"""3장 run_dummy_research를 대체하는 실제 Agent 실행 진입점.
본 장은 두 Agent를 순차 호출한다. 7장에서는 Manager가 이 순서를 스스로 계획한다.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import List

from ..services.job_store import job_store
from .definitions import MARKET_ANALYST, RESEARCH_AGENT

logger = logging.getLogger(__name__)


async def run_agent_research(job_id: str, query: str, user_id: str, scope: List[str]) -> None:
    try:
        job_store.update(job_id, progress=0.2, currentStep="RESEARCH")
        research = await RESEARCH_AGENT.run(query, user_id=user_id, scope=scope)

        job_store.update(job_id, progress=0.6, currentStep="MARKET_ANALYSIS")
        market = await MARKET_ANALYST.run(query, user_id=user_id, scope=scope)

        job_store.update(job_id, progress=0.9, currentStep="REPORT_WRITING")

        # 한국어 질의가 어중간하게 잘리지 않도록 말줄임 처리
        short_query = query if len(query) <= 40 else query[:40].rstrip() + "…"
        report = {
            "title": f"{short_query} 분석 보고서",
            "sections": [
                {"title": "문서 근거", "content": research.answer, "citations": research.citations},
                {"title": "시장 데이터", "content": market.answer, "citations": market.citations},
            ],
            # 감사용 — 어떤 Tool을 어떤 인자로 불렀는지를 보고서에 함께 담는다
            "toolCalls": [t.model_dump() for t in (research.toolCalls + market.toolCalls)],
            "disclaimer": "본 보고서는 AI 생성 결과이므로 담당자 확인이 필수입니다.",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }

        if not research.ok and not market.ok:
            # 둘 다 실패한 경우에만 FAILED. 한쪽만 실패하면 부분 결과를 살린다.
            job_store.update(
                job_id, status="FAILED", progress=1.0, currentStep="FAILED",
                result={"report": report,
                        "error": research.stoppedReason or market.stoppedReason},
            )
            return

        job_store.update(job_id, status="COMPLETED", progress=1.0,
                         currentStep="DONE", result={"report": report})

    except Exception as e:
        logger.exception("agent research failed: job=%s", job_id)
        job_store.update(job_id, status="FAILED", progress=1.0, currentStep="FAILED",
                         result={"error": f"{type(e).__name__}: {e}"})