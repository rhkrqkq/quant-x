"""단일 Agent 공통 구현.
시스템 프롬프트와 Tool 세트만 바꾸면 다른 역할의 Agent가 된다.
7장에서는 이 클래스가 LangGraph 노드 안의 실행 단위가 된다.
"""
from __future__ import annotations
import logging
import re
import time
from typing import Any, Dict, List

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..config import settings
from ..llm.call_log import LLMCallLogger
from ..llm.factory import get_llm_client
from ..rag.citations import extract_citations                # 4장 유틸 재사용
from ..schemas.agent import AgentResult, ToolCallTrace
from .tool_adapter import build_langchain_tools

logger = logging.getLogger(__name__)

_MARKET_CITATION_RE = re.compile(r"\[market-data:[\w.]+\]")


def _collect_citations(answer: str, steps: List[Any]) -> List[str]:
    """문서 인용은 Tool이 실제 돌려준 값에서, 시장 인용은 답변 본문에서 모은다.

    [감사] 문서 인용을 답변 본문에서 긁지 않는 이유: 모델이 형식을 어기면
    (예: 긴 ID를 [1], [2] 같은 번호 각주로 바꾸면) 실제로 근거를 조회했는데도
    기록이 통째로 비어 버린다. 관찰 결과에는 Tool이 돌려준 citation 값이 그대로 있다.
    """
    docs: List[str] = []
    for _, observation in steps:
        for c in extract_citations(str(observation)):
            if c not in docs:                               # 순서 보존 중복 제거
                docs.append(c)

    market: List[str] = []                                  # 시장 인용은 짧아 본문 추출이 안정적이다
    for c in _MARKET_CITATION_RE.findall(answer):
        cid = c.strip("[]")
        if cid not in market:
            market.append(cid)
    return docs + market


class SingleAgent:
    def __init__(
        self,
        agent_id: str,
        system_prompt: str,
        tool_names: List[str],
        description: str = "",) -> None:
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.tool_names = tool_names
        self.description = description

    async def run(self, query: str, *, user_id: str, scope: List[str]) -> AgentResult:
        started = time.time()

        # [보안] 권한 정보는 여기서 한 번만 주입된다. 이후 LLM은 손대지 못한다.
        tools = build_langchain_tools(
            self.tool_names, agent_id=self.agent_id, user_id=user_id, scope=scope,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        # Agent 실행기 
        executor = AgentExecutor(
            agent=create_tool_calling_agent(get_llm_client().as_chat_model(), tools, prompt),
            tools=tools,
            max_iterations=settings.agent_max_iterations,        # [통제] 반복 상한
            max_execution_time=settings.agent_timeout_seconds,   # [통제] 시간 상한
            return_intermediate_steps=True,                      # 감사용 — 호출 내역 보존
            handle_parsing_errors=True,
        )

        # [감사] Agent 루프 안의 모든 LLM 호출을 기록한다.
        # LangChain이 chat model을 직접 부르므로 콜백으로 붙여야 잡힌다 (Step 1).
        call_logger = LLMCallLogger(
            provider=settings.llm_provider,
            model=settings.llm_model,
            agent_id=self.agent_id,
        )

        try:
		        # 비동기로 Agent 실제 실행 
            raw: Dict[str, Any] = await executor.ainvoke(
                {"input": query}, config={"callbacks": [call_logger]},
            )
        except Exception as e:
            logger.exception("agent failed: %s", self.agent_id)
            return AgentResult(
                agentId=self.agent_id, ok=False, answer="",
                stoppedReason=f"{type(e).__name__}: {e}",
                elapsedMs=int((time.time() - started) * 1000),
            )

        steps = raw.get("intermediate_steps", [])
        answer = str(raw.get("output", ""))
        # 실행결과 조립
        return AgentResult(
            agentId=self.agent_id,
            ok=True,
            answer=answer,
            citations=_collect_citations(answer, steps),
            toolCalls=[
                ToolCallTrace(
                    tool=action.tool,
                    args=action.tool_input if isinstance(action.tool_input, dict)
                         else {"input": action.tool_input},
                    resultSummary=str(observation)[:200],
                )
                for action, observation in steps
            ],
            # 상한에 걸렸으면 빈 결과가 아니라 중단 사유를 함께 남긴다 (§3.7)
            stoppedReason="MAX_ITERATIONS" if len(steps) >= settings.agent_max_iterations else None,
            elapsedMs=int((time.time() - started) * 1000),
        )