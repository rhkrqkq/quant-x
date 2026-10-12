"""LangGraph 노드 5종.
각 노드는 State에서 필요한 것만 읽고, 자기가 채울 키만 dict로 돌려준다.
Agent 실행 자체는 6장 SingleAgent가 그대로 담당한다.
"""
from __future__ import annotations
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..agents import prompts
from ..agents.definitions import MARKET_ANALYST, RESEARCH_AGENT, RISK_REVIEWER
from ..config import settings
from ..llm.factory import get_llm_client
from ..schemas.agent import AgentResult
from ..tools.gateway import gateway
from .execution_store import finish_execution, start_execution
from .state import ResearchState

logger = logging.getLogger(__name__)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """LLM 답변에서 JSON 한 덩어리를 꺼낸다. 실패하면 None."""
    m = _JSON_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def _run_worker(state: ResearchState, *, agent, step_order: int, query: str) -> AgentResult:
    """Worker 하나를 실행하고 시작·종료를 agent_execution에 남긴다."""
    exec_id = start_execution(
        job_id=state["job_id"], request_id=state["request_id"],
        agent_id=agent.agent_id, step_order=step_order, input_text=query,
    )
    started = time.time()
    try:
        result = await agent.run(query, user_id=state["user_id"], scope=state["scope"])
    except Exception as e:
        finish_execution(exec_id, status="FAILED",
                         duration_ms=int((time.time() - started) * 1000),
                         error_message=f"{type(e).__name__}: {e}")
        raise
    finish_execution(
        exec_id,
        status="COMPLETED" if result.ok else "FAILED",
        output_text=result.answer,
        duration_ms=result.elapsedMs,
        error_message=result.stoppedReason,
    )
    return result


# ------------------------------------------------------------------ PLAN
async def plan_node(state: ResearchState) -> Dict[str, Any]:
    """질의를 보고 어떤 Worker가 필요한지 고르고, 각자 맡을 부분을 나눈다."""
    known = ["research", "market"]
    plan: List[str] = []
    tasks: Dict[str, str] = {}
    try:
        answer = await get_llm_client().chat(
            [{"role": "user", "content": prompts.MANAGER_PLAN_PROMPT + state["query"]}]
        )
        parsed = _extract_json(answer) or {}
        plan = [w for w in parsed.get("plan", []) if w in known]
        raw = parsed.get("tasks") or {}
        tasks = {k: str(v) for k, v in raw.items() if k in known and v}
    except Exception:
        logger.exception("계획 수립 실패 — 전체 실행으로 진행한다")

    if not plan:                          # 파싱이 안 됐거나 빈 계획이면 전부 돌린다
        plan = known
    logger.info("plan=%s job=%s", plan, state["job_id"])
    return {"plan": plan, "tasks": tasks}


# -------------------------------------------------------------- RESEARCH
async def research_node(state: ResearchState) -> Dict[str, Any]:
    task = (state.get("tasks") or {}).get("research") or state["query"]
    result = await _run_worker(state, agent=RESEARCH_AGENT, step_order=1, query=task)
    return {
        "research": result,
        "citations": result.citations,
        "tool_calls": [t.model_dump() for t in result.toolCalls],
    }


# --------------------------------------------------------------- ANALYZE
async def market_node(state: ResearchState) -> Dict[str, Any]:
    task = (state.get("tasks") or {}).get("market") or state["query"]
    result = await _run_worker(state, agent=MARKET_ANALYST, step_order=2, query=task)
    return {
        "market": result,
        "citations": result.citations,
        "tool_calls": [t.model_dump() for t in result.toolCalls],
    }


# ---------------------------------------------------------------- REVIEW
def _draft_text(state: ResearchState) -> str:
    parts: List[str] = []
    if state.get("research"):
        parts.append("[문서 근거]\n" + state["research"].answer)
    if state.get("market"):
        parts.append("[시장 데이터]\n" + state["market"].answer)
    return "\n\n".join(parts)


async def review_node(state: ResearchState) -> Dict[str, Any]:
    draft = _draft_text(state)
    citations = state.get("citations", [])

    # ① 규칙 검사 — Gateway 경유. LLM을 안 부르므로 결과가 고정이다
    try:
        rule = gateway.invoke(
            "check_compliance_rules",
            {"text": draft, "citation_count": len(citations)},
            agent_id="risk_reviewer", user_id=state["user_id"], scope=state["scope"],
        )
    except PermissionError as e:
        rule = {"passed": True, "issues": [{"message": f"규정 검사 권한이 없다: {e}"}]}
    except Exception as e:
        # Tool 미등록·DB 오류 등. 검사 실패는 초안의 문제가 아니므로 반려하지 않되,
        # 검사를 못 했다는 사실은 보고서에 남긴다
        logger.exception("규정 검사 실패")
        rule = {"passed": True, "issues": [{"message": f"규정 검사를 하지 못했다: {type(e).__name__}"}]}

    # ② LLM 검토 — 규칙이 못 잡는 것 (계획 대비 누락, 근거 부실)
    review_query = (
        f"다음은 보고서 초안이다. 계획은 {state.get('plan')} 였다.\n"
        f"규칙 검사가 찾은 문제: {[i['message'] for i in rule['issues']] or '없음'}\n\n"
        f"{draft}"
    )
    result = await _run_worker(state, agent=RISK_REVIEWER, step_order=3, query=review_query)
    verdict = _extract_json(result.answer) or {"passed": True, "issues": []}

    issues = [i["message"] for i in rule["issues"]] + [str(x) for x in verdict.get("issues", [])]
    passed = bool(rule["passed"]) and bool(verdict.get("passed", True))

    revision = state.get("revision", 0)
    if not passed and revision < settings.agent_max_revisions:
        revision += 1
        next_step = "revise"              # 앞 단계로 되돌아간다
    else:
        next_step = "write"               # 통과했거나 상한에 걸렸다

    return {
        "review": {"passed": passed, "issues": issues, "nextStep": next_step},
        "revision": revision,
    }


def route_after_review(state: ResearchState) -> str:
    """조건부 엣지. 판단은 review_node가 이미 끝냈고 여기서는 읽기만 한다."""
    return (state.get("review") or {}).get("nextStep", "write")


# ----------------------------------------------------------------- WRITE
def _title(query: str) -> str:
    short = query if len(query) <= 40 else query[:40].rstrip() + "…"
    return f"{short} 분석 보고서"


async def write_node(state: ResearchState) -> Dict[str, Any]:
    review = state.get("review") or {}
    citations = state.get("citations", [])
    writer_input = (
        f"질문: {state['query']}\n\n"
        f"{_draft_text(state)}\n\n"
        f"사용할 수 있는 인용: {citations}\n"
        f"검토자 지적: {review.get('issues') or '없음'}"
    )
    exec_id = start_execution(
        job_id=state["job_id"], request_id=state["request_id"],
        agent_id="report_writer", step_order=4, input_text=writer_input,
    )
    started = time.time()
    try:
        # Report Writer는 Tool이 없으므로 Agent 루프 없이 한 번만 부른다
        body = await get_llm_client().chat([
            {"role": "system", "content": prompts.REPORT_WRITER_SYSTEM},
            {"role": "user", "content": writer_input},
        ])
        status, error = "COMPLETED", None
    except Exception as e:
        body, status, error = "", "FAILED", f"{type(e).__name__}: {e}"
        logger.exception("보고서 작성 실패: job=%s", state["job_id"])

    finish_execution(exec_id, status=status, output_text=body,
                     duration_ms=int((time.time() - started) * 1000), error_message=error)

    report = {
        "title": _title(state["query"]),
        "body": body,
        "citations": state.get("citations", []),
        "toolCalls": state.get("tool_calls", []),
        "reviewPassed": review.get("passed", True),
        "reviewIssues": review.get("issues", []),
        "disclaimer": "본 보고서는 AI 생성 결과이므로 담당자 확인이 필수입니다.",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return {"report": report}