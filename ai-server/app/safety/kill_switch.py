"""Kill Switch. 상태는 Spring Boot가 DB에 쓰고 여기서는 읽기만 한다.

왜 FastAPI가 자기 상태를 안 들고 있는가. 비상 정지를 누르는 사람은 관리자이고
관리자 화면은 Spring Boot에 있다. 두 서버가 각자 상태를 들면 한쪽만 꺼진 채로
"껐는데 왜 도나"가 된다. 정지 상태는 한 곳에만 있어야 한다.

[주의] 매 요청마다 DB를 보면 정상 트래픽에 조회가 한 번씩 더 붙는다.
       짧은 TTL 캐시를 두는 대신, **켜는 것은 즉시가 아니다**. 실습에서 껐다 켜고
       바로 눌러 보면 몇 초 동안 이전 상태가 남아 있는 걸 보게 된다.
       비상 정지에서 이 몇 초를 받아들일 수 있는지가 실제 설계 판단이다.
"""
from __future__ import annotations
import logging
import time
from typing import Optional, Tuple

import sqlalchemy as sa

from ..config import settings
from ..tools.db import get_engine

logger = logging.getLogger(__name__)

_TTL_SEC = 3.0 # ttl 3초
_cache: Tuple[float, bool, Optional[str]] = (0.0, False, None)


def _read_db() -> Tuple[bool, Optional[str]]:
    """최신 한 줄이 현재 상태다. 토글할 때마다 행이 쌓인다."""
    with get_engine().connect() as conn:
        row = conn.execute(sa.text("""
            SELECT active, reason FROM kill_switch_status
             ORDER BY id DESC LIMIT 1
        """)).first()
    if row is None:
        return False, None
    return bool(row.active), row.reason


def is_active(*, force_refresh: bool = False) -> bool:
    return status(force_refresh=force_refresh)[0]


def status(*, force_refresh: bool = False) -> Tuple[bool, Optional[str]]:
    """(활성 여부, 사유). env의 KILL_SWITCH_ENABLED와 OR로 묶는다.

    env 값은 '부팅할 때부터 막고 시작한다'는 뜻이라 DB로 끌 수 없다.
    사고가 났을 때 DB까지 손이 닿지 않는 상황을 위한 마지막 수단이다.
    """
    global _cache

    if settings.kill_switch_enabled:
        return True, "환경변수 KILL_SWITCH_ENABLED"

    now = time.time()
    cached_at, active, reason = _cache
    if not force_refresh and now - cached_at < _TTL_SEC:
        return active, reason

    try:
        active, reason = _read_db()
    except Exception as e:
        # [주의] 상태를 못 읽었다고 서비스를 세우지 않는다. DB 장애가 곧 전면 중단이 되면
        #        Kill Switch가 오히려 장애 원인이 된다. 직전 값을 그대로 쓴다.
        #        매 요청마다 도는 자리라 트레이스백은 남기지 않는다 — MariaDB를 안 띄운 상태에서
        #        실습하면 로그가 스택으로 가득 차 정작 볼 것을 못 본다
        logger.warning("kill_switch_status 조회 실패(%s). 직전 값을 유지한다",
                       type(e).__name__)
        return active, reason

    _cache = (now, active, reason)
    return active, reason