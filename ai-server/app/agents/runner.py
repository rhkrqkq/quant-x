"""6장의 순차 호출을 LangGraph 실행으로 교체한다."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..graph.build import get_research_graph
from ..services.job_store import job_store

logger = logging.getLogger(__name__)

# 노드가 끝날 때마다 올려줄 진행률
_PROGRESS = {"plan": 0.1, "research": 0.35, "market": 0.6, "review": 0.8, "write": 0.95}


async def run_agent_research(job_id: str, query: str, user_id: str,
                             scope: List[str], request_id: int = 0) -> None:
    initial: Dict[str, Any] = {
        "job_id": job_id, "request_id": request_id, "query": query,
        "user_id": user_id, "scope": scope,
        "citations": [], "tool_calls": [], "revision": 0,
    }
    report: Optional[Dict[str, Any]] = None

    try:
        # astream은 노드가 끝날 때마다 {노드이름: 반환값}을 내보낸다
        async for chunk in get_research_graph().astream(initial):
            for node_name, node_out in chunk.items():
                job_store.update(
                    job_id,
                    progress=_PROGRESS.get(node_name, 0.5),
                    currentStep=node_name.upper(),
                )
                if node_name == "write":
                    report = (node_out or {}).get("report")
    except Exception as e:
        logger.exception("그래프 실행 실패: job=%s", job_id)
        job_store.update(job_id, status="FAILED", progress=1.0, currentStep="FAILED",
                         result={"error": f"{type(e).__name__}: {e}"})
        return

    if report is None:
        job_store.update(job_id, status="FAILED", progress=1.0, currentStep="FAILED",
                         result={"error": "보고서를 만들지 못했다"})
        return

    job_store.update(job_id, status="COMPLETED", progress=1.0,
                     currentStep="DONE", result={"report": report})