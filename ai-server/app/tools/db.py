"""MariaDB SQLAlchemy 엔진 단일 진입점.
backfill.py와 market_tools.py가 모두 이 모듈에서 엔진을 가져온다.
yfinance와 같은 무거운 외부 의존성이 시세 조회 경로(market_tools)에 전이되지 않도록
backfill에서 분리해 둔다.
"""
from __future__ import annotations
import os

import sqlalchemy as sa
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    """프로세스 단일 엔진. 운영에서는 PoolClass·timeout 옵션을 따로 튜닝."""
    global _engine
    if _engine is None:
        url = os.getenv("MARIADB_URL")
        _engine = sa.create_engine(url, pool_pre_ping=True, future=True)
    return _engine