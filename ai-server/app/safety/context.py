"""요청 하나를 관통하는 값들. 인자로 넘기지 않고 contextvars로 들고 다닌다.

[감사] request_uid는 Spring Boot가 만들어 X-Request-ID 헤더로 넘겨 준다.
       Tool Gateway·가드레일·Core Zone 호출이 모두 같은 값을 기록해야
       "이 조회는 누가 왜 했는가"에 답할 수 있다 (8장에서 9장으로 넘어온 숙제).

인자로 넘기지 않는 이유가 있다. 기록용 값을 함수 시그니처에 끼워 넣기 시작하면
Tool 함수 하나하나까지 전부 고쳐야 하고, LLM이 채우는 인자 스키마에도 새어 들어간다.
"""
from __future__ import annotations
import logging
import uuid
from contextvars import ContextVar
from typing import Optional

_request_uid: ContextVar[Optional[str]] = ContextVar("request_uid", default=None)
_execution_id: ContextVar[Optional[int]] = ContextVar("execution_id", default=None)
_caller_user_id: ContextVar[Optional[str]] = ContextVar("caller_user_id", default=None)


def set_request_uid(value: Optional[str]) -> str:
    """헤더로 받은 값을 심는다. 없으면 여기서 만든다 (FastAPI를 직접 부른 경우)."""
    uid = value or f"req-{uuid.uuid4()}"
    _request_uid.set(uid)
    return uid


def get_request_uid() -> Optional[str]:
    return _request_uid.get()


def set_execution_id(value: Optional[int]) -> None:
    """Worker 실행이 시작될 때 agent_execution.id를 심는다."""
    _execution_id.set(value)


def get_execution_id() -> Optional[int]:
    return _execution_id.get()


def set_caller_user_id(value: Optional[str]) -> None:
    """Tool Gateway가 호출 직전에 심는다.

    Tool 함수의 인자로 넣지 않는 이유가 있다. 인자에 넣으면 LangChain이 LLM에게
    보여 주는 스키마에도 들어가고, 그러면 **LLM이 user_id를 지어낼 수 있게 된다.**
    5장에서 agent_id·user_id·scope를 클로저로 주입한 것과 같은 판단이다.
    """
    _caller_user_id.set(value)


def get_caller_user_id() -> Optional[str]:
    return _caller_user_id.get()


class RequestUidLogFilter(logging.Filter):
    """모든 로그 줄에 request_uid를 끼워 넣는다.

    자바의 MDC(Mapped Diagnostic Context)와 같은 일을 한다. 로그 패턴에 `%X{requestUid}`를
    넣어 두고 요청 시작 때 심어 두면 그 요청 동안 찍히는 모든 줄에 자동으로 붙는 것 —
    운영에서 장애가 나면 그 값 하나로 Kibana에서 요청 전 구간을 따라가는 방식이다.

    파이썬 표준 logging에는 MDC가 없어서 Filter로 흉내낸다. Filter는 원래 '거르는' 용도지만
    레코드에 속성을 붙이는 자리로도 쓴다 — 포매터가 읽을 값을 여기서 채워 준다.

    [주의] 값이 없어도 반드시 채워야 한다. 포맷 문자열에 `%(request_uid)s`가 있는데
           속성이 없으면 그 로그 줄이 통째로 사라진다(로깅 자체가 예외를 낸다).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_uid = get_request_uid() or "-"
        return True          # 거르지 않는다. 값만 채우고 통과시킨다