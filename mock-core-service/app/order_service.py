"""주문 접수·결재 로직.

접수 순서는 멱등성 → 단일 한도 → 일일 누적 한도 → 잔고다.
비싼 검사를 뒤로 미루는 것도 있지만, 그보다 **거절 사유를 하나로 못박기 위해서**다.
한도와 잔고에 동시에 걸리는 주문이 실행할 때마다 다른 이유로 거절되면 감사에서 설명하기 어렵다.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.engine import Connection

from .config import settings
from .schemas import OrderCreate, OrderOut

# 상태 전이 규칙. 종료 상태에서는 아무 데로도 못 간다
ALLOWED_TRANSITIONS: Dict[str, set] = {
    "PENDING": {"EXECUTED", "REJECTED", "EXPIRED"},
    "EXECUTED": set(),
    "REJECTED": set(),
    "EXPIRED": set(),
    "FAILED": set(),
}

_ORDER_COLUMNS = """
    order_id, account_id, ticker, side, quantity, price, estimated_amount_krw,
    status, submitted_by, research_report_id, decided_by, decided_at,
    executed_at, execution_price_krw, actual_amount_krw, reject_reason,
    created_at, decision_required_by
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conflict(code: str, **extra: Any) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail={"error": code, **extra})


def _to_out(row: Any, *, duplicate: bool = False) -> OrderOut:
    return OrderOut(
        orderId=row.order_id, accountId=row.account_id, ticker=row.ticker,
        side=row.side, quantity=row.quantity, price=row.price,
        estimatedAmountKrw=row.estimated_amount_krw, status=row.status,
        submittedBy=row.submitted_by, researchReportId=row.research_report_id,
        decidedBy=row.decided_by, decidedAt=row.decided_at,
        executedAt=row.executed_at, executionPriceKrw=row.execution_price_krw,
        actualAmountKrw=row.actual_amount_krw, rejectReason=row.reject_reason,
        createdAt=row.created_at, decisionRequiredBy=row.decision_required_by,
        duplicate=duplicate,
    )


def _fetch_order(conn: Connection, order_id: str) -> Any:
    row = conn.execute(sa.text(
        f"SELECT {_ORDER_COLUMNS} FROM mock_orders WHERE order_id = :oid"
    ), {"oid": order_id}).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"order not found: {order_id}")
    return row


def expire_stale(conn: Connection) -> int:
    """결재 시한을 넘긴 PENDING을 EXPIRED로 넘긴다.

    백그라운드 스케줄러 대신 조회·결재 직전에 한 번 돌린다. 프로세스가 꺼져 있는 동안에도
    시간은 흐르므로, 만료는 '언제 검사했는가'가 아니라 '시한을 넘겼는가'로 정해져야 한다.
    """
    res = conn.execute(sa.text("""
        UPDATE mock_orders
           SET status = 'EXPIRED'
         WHERE status = 'PENDING' AND decision_required_by < :now
    """), {"now": now_iso()})
    return res.rowcount or 0


def get_account(conn: Connection, account_id: str) -> Any:
    row = conn.execute(sa.text("""
        SELECT account_id, account_number_masked, holder_name_masked, type,
               balance_krw, available_krw, opened_at, active
          FROM mock_accounts WHERE account_id = :aid
    """), {"aid": account_id}).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"account not found: {account_id}")
    return row


def create_order(conn: Connection, req: OrderCreate, idem_key: str) -> Tuple[OrderOut, bool]:
    # ① 멱등성 — 같은 키가 있으면 새로 만들지 않고 있던 걸 그대로 돌려준다
    existing = conn.execute(sa.text(
        f"SELECT {_ORDER_COLUMNS} FROM mock_orders WHERE idempotency_key = :k"
    ), {"k": idem_key}).first()
    if existing is not None:
        return _to_out(existing, duplicate=True), True

    account = get_account(conn, req.accountId)
    if not account.active:
        raise _conflict("ACCOUNT_INACTIVE", accountId=req.accountId)

    amount = req.quantity * req.price

    # ② 단일 주문 한도
    if amount > settings.order_single_limit_krw:
        raise _conflict("SINGLE_LIMIT_EXCEEDED",
                        limit=settings.order_single_limit_krw, requested=amount)

    # ③ 일일 누적 한도 — 계좌와 요청자를 함께 본다. 계좌를 바꿔 가며 쪼개는 것도 막아야 하지만,
    #    본 과정에서는 사용자·계좌 조합 기준까지만 다룬다
    daily = conn.execute(sa.text("""
        SELECT COALESCE(SUM(estimated_amount_krw), 0)
          FROM mock_orders
         WHERE account_id = :aid AND submitted_by = :uid
           AND substr(created_at, 1, 10) = :today
           AND status IN ('PENDING', 'EXECUTED')
    """), {"aid": req.accountId, "uid": req.submittedBy,
           "today": now_iso()[:10]}).scalar_one()
    if daily + amount > settings.order_daily_limit_krw:
        raise _conflict("DAILY_LIMIT_EXCEEDED",
                        limit=settings.order_daily_limit_krw,
                        alreadyUsed=daily, requested=amount)

    # ④ 잔고 — 매수만 본다. 매도는 보유 수량을 봐야 하는데 Mock에는 보유 종목이 없다
    if req.side == "BUY" and account.available_krw < amount:
        raise _conflict("INSUFFICIENT_BALANCE",
                        available=account.available_krw, requested=amount)

    created = datetime.now(timezone.utc)
    order_id = f"ord-{uuid.uuid4()}"
    conn.execute(sa.text("""
        INSERT INTO mock_orders
            (order_id, idempotency_key, account_id, ticker, side, quantity, price,
             estimated_amount_krw, status, submitted_by, research_report_id,
             created_at, decision_required_by)
        VALUES
            (:order_id, :idem, :account_id, :ticker, :side, :quantity, :price,
             :amount, 'PENDING', :submitted_by, :report_id,
             :created_at, :required_by)
    """), {
        "order_id": order_id, "idem": idem_key, "account_id": req.accountId,
        "ticker": req.ticker, "side": req.side, "quantity": req.quantity,
        "price": req.price, "amount": amount, "submitted_by": req.submittedBy,
        "report_id": req.researchReportId,
        "created_at": created.isoformat(),
        "required_by": (created + timedelta(
            seconds=settings.order_decision_timeout_sec)).isoformat(),
    })
    return _to_out(_fetch_order(conn, order_id)), False


def _transition(current: str, new: str) -> None:
    if new not in ALLOWED_TRANSITIONS.get(current, set()):
        raise _conflict("INVALID_TRANSITION", fromStatus=current, toStatus=new)


def approve(conn: Connection, order_id: str, decided_by: str) -> OrderOut:
    """결재 의견(comment)은 여기 남기지 않는다.
    Core Zone에는 체결에 필요한 사실만 두고, 누가 왜 승인했는지는
    Spring Boot의 order_approval_queue와 감사 로그가 갖는다.
    """
    expire_stale(conn)
    row = _fetch_order(conn, order_id)
    _transition(row.status, "EXECUTED")

    # 체결가는 주문가 그대로 둔다. 슬리피지를 흉내내면 실행할 때마다 금액이 달라져
    # 실습 결과를 대조할 수 없다. 실제 체결가가 다를 수 있다는 건 §7에서 짚는다
    now = now_iso()
    conn.execute(sa.text("""
        UPDATE mock_orders
           SET status = 'EXECUTED', decided_by = :by, decided_at = :now,
               executed_at = :now,
               execution_price_krw = price, actual_amount_krw = estimated_amount_krw
         WHERE order_id = :oid
    """), {"by": decided_by, "now": now, "oid": order_id})

    # 체결된 만큼 주문 가능 금액을 줄인다. PENDING 상태에서는 잡아 두지 않으므로,
    # 같은 계좌에 PENDING이 여러 건이면 합이 잔고를 넘길 수 있다 (부록 F §14 확장 항목)
    delta = -row.estimated_amount_krw if row.side == "BUY" else row.estimated_amount_krw
    conn.execute(sa.text("""
        UPDATE mock_accounts SET available_krw = available_krw + :delta
         WHERE account_id = :aid
    """), {"delta": delta, "aid": row.account_id})

    return _to_out(_fetch_order(conn, order_id))


def reject(conn: Connection, order_id: str, decided_by: str,
           reason: Optional[str]) -> OrderOut:
    expire_stale(conn)
    row = _fetch_order(conn, order_id)
    _transition(row.status, "REJECTED")

    conn.execute(sa.text("""
        UPDATE mock_orders
           SET status = 'REJECTED', decided_by = :by, decided_at = :now,
               reject_reason = :reason
         WHERE order_id = :oid
    """), {"by": decided_by, "now": now_iso(), "reason": reason, "oid": order_id})
    return _to_out(_fetch_order(conn, order_id))


def list_orders(conn: Connection, account_id: Optional[str],
                order_status: Optional[str], limit: int = 50) -> Tuple[List[OrderOut], int]:
    expire_stale(conn)

    where, params = [], {}
    if account_id:
        where.append("account_id = :aid")
        params["aid"] = account_id
    if order_status:
        where.append("status = :st")
        params["st"] = order_status
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    total = conn.execute(sa.text(
        f"SELECT COUNT(*) FROM mock_orders {clause}"), params).scalar_one()
    rows = conn.execute(sa.text(
        f"SELECT {_ORDER_COLUMNS} FROM mock_orders {clause} "
        f"ORDER BY created_at DESC LIMIT :limit"
    ), {**params, "limit": limit}).all()

    return [_to_out(r) for r in rows], total