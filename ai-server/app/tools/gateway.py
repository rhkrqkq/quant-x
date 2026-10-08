"""Tool Gateway 골격.
- Scope 검사
- 호출 로깅 (9장에서 DB 영속화로 교체)
6장에서 LangChain Tool로 래핑되고, 8장에서 Mock Core Service Read Tool 추가, 9장에서 Rate Limit/Audit DB 통합.
"""
from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolSpec:
    name: str
    func: Callable[..., Any]
    required_scopes: List[str]
    description: str = ""


@dataclass
class ToolCallRecord:
    record_id: str
    tool_name: str
    agent_id: str
    user_id: str
    scope_pass: bool
    duration_ms: int
    error: Optional[str] = None
    summary: str = ""
    timestamp: float = field(default_factory=time.time)


class ToolGateway:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}
        self._call_log: List[ToolCallRecord] = []

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def list_tools(self, scope: List[str]) -> List[ToolSpec]:
        return [s for s in self._tools.values()
                if all(req in scope for req in s.required_scopes)]

    def invoke(
        self,
        tool_name: str,
        params: Dict[str, Any],
        *,
        agent_id: str,
        user_id: str,
        scope: List[str],) -> Any:
        spec = self._tools.get(tool_name)
        if spec is None:
            raise KeyError(f"Tool not found: {tool_name}")

        # ① Scope 검사
        missing = [r for r in spec.required_scopes if r not in scope]
        if missing:
            self._record(ToolCallRecord(
                record_id=str(uuid.uuid4()), tool_name=tool_name,
                agent_id=agent_id, user_id=user_id, scope_pass=False,
                duration_ms=0, error=f"missing scope: {missing}",
            ))
            raise PermissionError(f"missing scope: {missing}")

        # ② 호출 + 시간 측정
        start = time.time()
        error: Optional[str] = None
        result: Any = None
        try:
            result = spec.func(**params)
            return result
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            logger.exception("tool failed: %s", tool_name)
            raise
        finally:
            self._record(ToolCallRecord(
                record_id=str(uuid.uuid4()), tool_name=tool_name,
                agent_id=agent_id, user_id=user_id, scope_pass=True,
                duration_ms=int((time.time() - start) * 1000),
                error=error,
                summary=_summarize(result) if result is not None else "",
            ))

    # ---------- 로깅 (인메모리) ----------
    def _record(self, record: ToolCallRecord) -> None:
        self._call_log.append(record)
        logger.info("tool_call %s | scope_pass=%s | duration=%dms | err=%s",
                    record.tool_name, record.scope_pass, record.duration_ms, record.error)

    def recent_calls(self, limit: int = 50) -> List[ToolCallRecord]:
        return self._call_log[-limit:]


def _summarize(value: Any, max_len: int = 200) -> str:
    s = str(value)
    return s if len(s) <= max_len else s[:max_len] + "..."


# 전역 인스턴스 (FastAPI 의존성 주입에서 사용)
gateway = ToolGateway()