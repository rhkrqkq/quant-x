"""가드레일 요청·응답 모델. 부록 B §3.4의 형태를 그대로 따른다.

응답 모델을 내부 함수의 반환형으로도 같이 쓴다. 내부용 dataclass를 따로 두면
API로 나갈 때 한 번 더 변환해야 하고, 그 사이에서 필드가 어긋나기 시작한다.
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["SAFE", "WARNING", "BLOCKED"]


class GuardrailCheckRequest(BaseModel):
    text: str = Field(..., max_length=20000)
    userId: Optional[str] = None
    context: str = "unknown"          # research_query, report_section, ...


class GuardrailResult(BaseModel):
    isSafe: bool
    riskLevel: RiskLevel
    detectedIssues: List[str] = Field(default_factory=list)
    filteredText: str
    shouldBlock: bool
    shouldRewrite: bool = False
    moderation: Optional[Dict[str, Any]] = None      # 꺼져 있으면 null