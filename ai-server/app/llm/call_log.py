"""LLM 호출 기록. 5장 Tool Gateway의 호출 로그와 대칭 구조다.
[보안] 프롬프트 전문이 아니라 SHA-256 해시만 남긴다.
       감사 로그 자체가 PII 유출 경로가 되지 않도록 하기 위함이다 (부록 A §6).
9장에서 Audit DB로 영속화하고, 10장에서 llm_invocation_log 테이블로 확장한다.
"""
from __future__ import annotations
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


@dataclass
class LLMCallRecord:
    record_id: str
    provider: str
    model: str
    agent_id: str
    prompt_hash: str                                 # [보안] 전문 대신 해시
    prompt_chars: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    duration_ms: int = 0
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class LLMCallLog:
    """InMemory 누적. 9장에서 DB 영속화로 교체된다."""

    def __init__(self) -> None:
        self._records: List[LLMCallRecord] = []

    def add(self, record: LLMCallRecord) -> None:
        self._records.append(record)
        logger.info("llm_call %s/%s | agent=%s | %dms | err=%s",
                    record.provider, record.model, record.agent_id,
                    record.duration_ms, record.error)

    def recent(self, limit: int = 50) -> List[LLMCallRecord]:
        return self._records[-limit:]


llm_call_log = LLMCallLog()                          # 전역 인스턴스 (gateway와 같은 패턴)


class LLMCallLogger(BaseCallbackHandler):
    """AgentExecutor에 붙여 Agent 루프 안의 모든 LLM 호출을 기록한다.

    LangChain이 chat model을 직접 호출하므로 LLMClient.chat()에 로깅을 넣으면
    Agent 실행 중의 호출은 하나도 잡히지 않는다. 그래서 콜백으로 붙인다.
    """

    def __init__(self, *, provider: str, model: str, agent_id: str) -> None:
        self.provider = provider
        self.model = model
        self.agent_id = agent_id
        self._started: float = 0.0
        self._prompt_hash: str = ""
        self._prompt_chars: int = 0

    # chat model은 on_chat_model_start, 일반 LLM은 on_llm_start가 호출된다.
    # 본 과정은 chat model만 쓰지만 둘 다 받아 둔다.
    def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[Any]], **kwargs: Any) -> None:
        self._begin("\n".join(str(m.content) for batch in messages for m in batch))

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        self._begin("\n".join(prompts))

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = (response.llm_output or {}).get("token_usage", {})
        self._record(
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self._record(error=f"{type(error).__name__}: {error}")

    # ---------- 내부 ----------
    def _begin(self, text: str) -> None:
        self._started = time.time()
        self._prompt_chars = len(text)
        self._prompt_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _record(self, **extra: Any) -> None:
        llm_call_log.add(LLMCallRecord(
            record_id=str(uuid.uuid4()),
            provider=self.provider,
            model=self.model,
            agent_id=self.agent_id,
            prompt_hash=self._prompt_hash,
            prompt_chars=self._prompt_chars,
            duration_ms=int((time.time() - self._started) * 1000),
            **extra,
        ))