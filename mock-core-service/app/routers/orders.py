"""주문. 조회만 Read 키로 열려 있고 접수·결재는 System 키를 받는다.

같은 자원(주문)인데 Read와 Write의 통제 수준이 다르다"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from ..db import get_engine
from ..deps import require_internal_key, require_system_key
from ..order_service import approve as approve_order
from ..order_service import create_order, list_orders
from ..order_service import reject as reject_order
from ..schemas import DecisionIn, OrderCreate, OrderListOut, OrderOut

router = APIRouter(prefix="/core/orders", tags=["orders"])


@router.get("", response_model=OrderListOut,
            dependencies=[Depends(require_internal_key)])
def read_orders(account_id: Optional[str] = None,
                order_status: Optional[str] = Query(default=None, alias="status"),
                limit: int = 50) -> OrderListOut:
    with get_engine().begin() as conn:          # 만료 처리가 있어 쓰기 트랜잭션이다
        items, total = list_orders(conn, account_id, order_status, limit)
    return OrderListOut(items=items, total=total)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_system_key)])
def submit_order(req: OrderCreate, response: Response,
                 idempotency_key: str = Header(alias="X-Idempotency-Key")) -> OrderOut:
    if not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="X-Idempotency-Key is required")

    with get_engine().begin() as conn:
        order, duplicate = create_order(conn, req, idempotency_key)

    # 같은 키로 다시 들어온 요청은 새로 만든 게 아니므로 201이 아니라 200이다
    if duplicate:
        response.status_code = status.HTTP_200_OK
    return order


@router.post("/{order_id}/approve", response_model=OrderOut,
             dependencies=[Depends(require_system_key)])
def approve(order_id: str, req: DecisionIn) -> OrderOut:
    with get_engine().begin() as conn:
        return approve_order(conn, order_id, req.decidedBy)


@router.post("/{order_id}/reject", response_model=OrderOut,
             dependencies=[Depends(require_system_key)])
def reject(order_id: str, req: DecisionIn) -> OrderOut:
    with get_engine().begin() as conn:
        return reject_order(conn, order_id, req.decidedBy, req.reason)