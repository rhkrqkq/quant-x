"""LLM_PROVIDER 환경변수 하나로 provider를 고른다.
Agent 코드는 이 함수만 보며 구현체를 알지 못한다.
"""
from __future__ import annotations
from functools import lru_cache

from ..config import settings
from .base import LLMClient


@lru_cache(maxsize=None)
def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        from .openai_adapter import OpenAIAdapter
        return OpenAIAdapter()
    if provider == "mock":
        from .mock_adapter import MockAdapter
        return MockAdapter()
    # 10장에서 ollama · vllm 분기가 이 자리에 추가된다.
    raise ValueError(f"지원하지 않는 LLM_PROVIDER: {settings.llm_provider}")