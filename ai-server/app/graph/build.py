"""노드와 엣지를 StateGraph로 묶는다.
그래프 모양이 곧 실행 흐름이라 코드만 보고도 순서를 알 수 있다.
"""
from __future__ import annotations
from functools import lru_cache

from langgraph.graph import END, StateGraph

from .nodes import (market_node, plan_node, research_node,
                    review_node, route_after_review, write_node)
from .state import ResearchState


def _route_after_plan(state: ResearchState) -> str:
    """계획에 없는 Worker는 건너뛴다."""
    plan = state.get("plan") or []
    if "research" in plan:
        return "research"
    if "market" in plan:
        return "market"
    return "review"


def _route_after_research(state: ResearchState) -> str:
    return "market" if "market" in (state.get("plan") or []) else "review"


def _route_after_review_node(state: ResearchState) -> str:
    """review_node가 정한 다음 단계를 실제 노드 이름으로 바꿔 준다."""
    if route_after_review(state) == "write":
        return "write"
    # 반려된 경우 계획에 있는 첫 노드로 돌아간다
    plan = state.get("plan") or []
    return "research" if "research" in plan else "market"


@lru_cache(maxsize=1)
def get_research_graph():
    """컴파일된 그래프. 프로세스당 한 번만 만든다."""
    g = StateGraph(ResearchState)

    g.add_node("plan", plan_node)
    g.add_node("research", research_node)
    g.add_node("market", market_node)
    g.add_node("review", review_node)
    g.add_node("write", write_node)

    g.set_entry_point("plan")

    g.add_conditional_edges("plan", _route_after_plan, {
        "research": "research", "market": "market", "review": "review",
    })
    g.add_conditional_edges("research", _route_after_research, {
        "market": "market", "review": "review",
    })
    g.add_edge("market", "review")

    # [통제] 반려되면 앞 노드로 되돌아간다. 상한은 review_node가 이미 보았다
    g.add_conditional_edges("review", _route_after_review_node, {
        "research": "research", "market": "market", "write": "write",
    })
    g.add_edge("write", END)

    return g.compile()