"""사용자별 Tool 호출 상한. 슬라이딩 윈도우 1분.

막으려는 것은 과부하가 아니라 **패턴**이다. 부록 A §10.2가 알람 조건으로 든 것들 —
"하루 Tool Call 100건 이상", "동일 Tool 반복 호출" — 은 성능 문제가 아니라
인젝션에 걸린 Agent가 같은 호출을 무한히 반복하는 신호다.

[주의] 프로세스 안에만 있는 카운터다. AI 서버를 두 대로 늘리면 각자 세므로 상한이 두 배가 된다.
       운영에서는 Redis 같은 공용 저장소로 옮겨야 한다.
"""
from __future__ import annotations
import time
from collections import defaultdict, deque
from typing import Deque, Dict

_WINDOW_SEC = 60.0
_calls: Dict[str, Deque[float]] = defaultdict(deque)


class RateLimitExceeded(Exception):
    """Tool Gateway가 429로 바꿔 준다."""


def check(user_id: str, limit: int) -> None:
    """상한을 넘으면 예외. 넘지 않으면 이번 호출을 창에 기록한다."""
    if limit <= 0:                      # 0 이하면 제한을 걸지 않는다
        return

    now = time.time()
    window = _calls[user_id]
    while window and now - window[0] > _WINDOW_SEC:
        window.popleft()

    if len(window) >= limit:
        raise RateLimitExceeded(
            f"분당 Tool 호출 한도 초과: {len(window)}/{limit} (user={user_id})")

    window.append(now)


def reset() -> None:
    """실습에서 상한에 걸린 뒤 되돌릴 때 쓴다."""
    _calls.clear()