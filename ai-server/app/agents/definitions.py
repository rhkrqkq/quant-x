"""본 장에서 만드는 Agent 2종. 같은 클래스에 프롬프트와 Tool 세트만 다르다."""
from __future__ import annotations
from typing import Dict, Optional

from . import prompts
from .base import SingleAgent

RESEARCH_AGENT = SingleAgent(
    agent_id="research_agent",
    system_prompt=prompts.RESEARCH_AGENT_SYSTEM,
    tool_names=["search_documents"],
    description="사내 리서치 문서에서 근거를 수집한다",
)

MARKET_ANALYST = SingleAgent(
    agent_id="market_analyst",
    system_prompt=prompts.MARKET_ANALYST_SYSTEM,
    tool_names=[
        "search_stock", "get_stock_price",
        "get_financial_metrics", "get_market_summary",
    ],
    description="시세·재무 지표를 조회해 해석한다",
)

AGENTS: Dict[str, SingleAgent] = {a.agent_id: a for a in (RESEARCH_AGENT, MARKET_ANALYST)}


def get_agent(agent_id: str) -> Optional[SingleAgent]:
    return AGENTS.get(agent_id)