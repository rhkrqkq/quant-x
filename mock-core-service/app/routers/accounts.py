"""계좌 조회. Read 전용이라 Tool Gateway가 부를 수 있다."""
from fastapi import APIRouter, Depends

from ..db import get_engine
from ..deps import require_internal_key
from ..order_service import get_account, now_iso
from ..schemas import AccountOut, BalanceOut

router = APIRouter(prefix="/core/accounts", tags=["accounts"],
                   dependencies=[Depends(require_internal_key)])


@router.get("/{account_id}", response_model=AccountOut)
def read_account(account_id: str) -> AccountOut:
    with get_engine().connect() as conn:
        row = get_account(conn, account_id)
    # 계좌번호와 이름은 DB에 이미 마스킹된 채로 들어 있다. 여기서 제거할 방법은 없다
    return AccountOut(
        accountId=row.account_id,
        accountNumberMasked=row.account_number_masked,
        holderNameMasked=row.holder_name_masked,
        type=row.type,
        openedAt=row.opened_at,
        active=bool(row.active),
    )


@router.get("/{account_id}/balance", response_model=BalanceOut)
def read_balance(account_id: str) -> BalanceOut:
    with get_engine().connect() as conn:
        row = get_account(conn, account_id)
    return BalanceOut(
        accountId=row.account_id,
        balanceKrw=row.balance_krw,
        availableKrw=row.available_krw,
        asOf=now_iso(),
    )