"""LangGraph 실행 전체가 공유하는 상태.
노드는 State 전체를 돌려주지 않고 자기가 채울 키만 dict로 반환한다.
"""
from __future__ import annotations
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from ..schemas.agent import AgentResult

def _merge_unique(left: List[str], right: List[str]) -> List[str]:
    """인용은 근거 목록이므로 중복을 지운다. 반려로 재실행돼도 한 번만 담긴다."""
    out = list(left)
    for x in right:
        if x not in out:
            out.append(x)
    return out

class ResearchState(TypedDict, total=False):
    # ---- 입력: 실행 내내 바뀌지 않는다 ----
    job_id: str
    request_id: int
    query: str
    user_id: str
    scope: List[str]

    # ---- Manager가 세운 계획 ----
    plan: List[str]                                  # 실행할 Worker id 목록
    tasks: Dict[str, str]                            # Worker별로 쪼갠 지시

    # ---- Worker 산출물: 나중 노드가 덮어쓴다 ----
    research: Optional[AgentResult]
    market: Optional[AgentResult]
    review: Optional[Dict[str, Any]]                 # {"passed": bool, "issues": [...]}
    report: Optional[Dict[str, Any]]

    # ---- 누적: 각 노드가 더한다 ----
    # [감사] reducer를 빼면 마지막 Worker의 것만 남아 기록이 사라진다
    citations: Annotated[List[str], _merge_unique]
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]

    # ---- 반려 루프 통제 ----
    revision: int
    stopped_reason: Optional[str]