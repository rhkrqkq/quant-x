"""요청·응답 모델. 부록 B §4의 형태를 그대로 따른다."""
from __future__ import annotations
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AccountOut(BaseModel):
    accountId: str
    accountNumberMasked: str
    holderNameMasked: str
    type: str
    openedAt: str
    active: bool


class BalanceOut(BaseModel):
    accountId: str
    balanceKrw: int
    availableKrw: int
    asOf: str


class OrderCreate(BaseModel):
    accountId: str
    ticker: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    submittedBy: str                          # 결재 요청자. Spring Boot가 채운다
    researchReportId: Optional[int] = None    # 추적용


class DecisionIn(BaseModel):
    decidedBy: str
    comment: Optional[str] = None             # approve
    reason: Optional[str] = None              # reject


class OrderOut(BaseModel):
    orderId: str
    accountId: str
    ticker: str
    side: str
    quantity: int
    price: int
    estimatedAmountKrw: int
    status: str
    submittedBy: str
    researchReportId: Optional[int] = None
    decidedBy: Optional[str] = None
    decidedAt: Optional[str] = None
    executedAt: Optional[str] = None
    executionPriceKrw: Optional[int] = None
    actualAmountKrw: Optional[int] = None
    rejectReason: Optional[str] = None
    createdAt: str
    decisionRequiredBy: str
    duplicate: bool = False                   # 같은 멱등성 키로 다시 들어온 요청인가


class OrderListOut(BaseModel):
    items: List[OrderOut]
    total: int