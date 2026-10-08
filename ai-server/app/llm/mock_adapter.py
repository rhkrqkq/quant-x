"""API 키 없이 Agent 전 구간을 재현하기 위한 Mock LLM.
답변만 흉내는 게 아니라 tool_calls를 생성해 실제로 Tool Gateway를 거치게 한다.
동작이 결정적이므로 자동 테스트에도 그대로 쓴다.
"""
from __future__ import annotations
import re
import uuid
from typing import Any, AsyncIterator, List, Optional, Sequence

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from .base import LLMClient

_TICKER_RE = re.compile(r"\d{6}")


class MockChatModel(BaseChatModel):
    """규칙 기반 가짜 chat model.
    - 대화에 ToolMessage가 없으면: 질의에 맞는 Tool을 하나 호출하는 tool_calls 반환
    - ToolMessage가 있으면: 관찰 결과를 정리한 최종 답변 반환
    """

    bound_tools: List[BaseTool] = []

    @property
    def _llm_type(self) -> str:
        return "mock-chat"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "MockChatModel":
        return MockChatModel(bound_tools=list(tools))

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,) -> ChatResult:
        observations = [m for m in messages if isinstance(m, ToolMessage)]

        if self.bound_tools and not observations:
            tool = self._pick_tool(messages)
            message = AIMessage(content="", tool_calls=[{
                "name": tool.name,
                "args": self._build_args(tool, messages),
                "id": f"call_{uuid.uuid4().hex[:8]}",
            }])
        else:
            joined = "\n".join(str(m.content) for m in observations)
            message = AIMessage(content=(
                "[mock 응답] 조회한 자료를 정리하면 다음과 같다.\n"
                + (joined or "조회된 자료가 없다.")
            ))
        return ChatResult(generations=[ChatGeneration(message=message)])

    # ---------- 규칙 ----------
    @staticmethod
    def _user_text(messages: List[BaseMessage]) -> str:
        for m in reversed(messages):
            if m.type == "human":
                return str(m.content)
        return ""

    def _pick_tool(self, messages: List[BaseMessage]) -> BaseTool:
        text = self._user_text(messages)
        by_name = {t.name: t for t in self.bound_tools}
        if "PER" in text or "PBR" in text or "재무" in text:
            if "get_financial_metrics" in by_name:
                return by_name["get_financial_metrics"]
        if "get_stock_price" in by_name and (_TICKER_RE.search(text) or "주가" in text or "종가" in text):
            return by_name["get_stock_price"]
        return self.bound_tools[0]

    def _build_args(self, tool: BaseTool, messages: List[BaseMessage]) -> dict:
        text = self._user_text(messages)
        found = _TICKER_RE.search(text)
        fields = tool.args_schema.model_fields if tool.args_schema else {}
        args: dict[str, Any] = {}
        if "ticker_or_name" in fields:
            args["ticker_or_name"] = found.group(0) if found else "005930"
        if "query" in fields:
            args["query"] = (text[:100] or "삼성전자")
        return args


class MockAdapter(LLMClient):
    def __init__(self) -> None:
        self._model = MockChatModel()

    async def chat(self, messages: list[dict], **kwargs) -> str:
        return "[mock 응답] LLM_PROVIDER=mock 상태다. 외부 모델 호출은 일어나지 않았다."

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        yield await self.chat(messages, **kwargs)

    def as_chat_model(self) -> BaseChatModel:
        return self._model