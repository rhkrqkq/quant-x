"""Mock Core Service 진입점.

가상 원장이지만 프로세스를 따로 띄운다. 같은 코드 안에서 함수로 부르면 Core Zone 격리가
말로만 남는다. 별도 프로세스여야 네트워크 호출·인증 키·지연·실패가 전부 실제로 일어난다.
"""
import logging

from fastapi import FastAPI

from .config import settings
from .db import init_db
from .middleware import (AuditMiddleware, FailureSimulationMiddleware,
                         LatencySimulationMiddleware)
from .routers import accounts, health, orders

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Mock Core Service", version=settings.version)

# add_middleware는 나중에 넣은 것이 바깥이다.
# 감사를 가장 바깥에 둬야 시뮬레이션 503도 기록에 남는다
app.add_middleware(LatencySimulationMiddleware)
app.add_middleware(FailureSimulationMiddleware)
app.add_middleware(AuditMiddleware)

app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(orders.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()