"""OpenAI 구현체. 본 과정 개발 단계의 기본 provider."""
from __future__ import annotations
from typing import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ..config import settings
from .base import LLMClient


class OpenAIAdapter(LLMClient):
    def __init__(self, model: str | None = None, temperature: float = 0.0) -> None:
        # [보안] 폐쇄망 모드에서는 외부 LLM 호출을 아예 막는다 (10장에서 본격 구현)
        if not settings.allow_external_llm:
            raise RuntimeError("ALLOW_EXTERNAL_LLM=false — 외부 LLM 호출이 차단되어 있다.")
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY가 비어 있다. LLM_PROVIDER=mock 으로 전환하거나 키를 설정한다.")

        self._model = ChatOpenAI(
            model=model or settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=temperature,                      # 감사 재현성을 위해 0으로 고정
            timeout=settings.agent_timeout_seconds,
        )

    async def chat(self, messages: list[dict], **kwargs) -> str:
        resp = await self._model.ainvoke(messages, **kwargs)
        return str(resp.content)

    # 비동기 제너레이터이므로 async def로 구현한다 (반환형은 AsyncIterator[str])
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        async for chunk in self._model.astream(messages, **kwargs):
            if chunk.content:
                yield str(chunk.content)

    def as_chat_model(self) -> BaseChatModel:
        return self._model