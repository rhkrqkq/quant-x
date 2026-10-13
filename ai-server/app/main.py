"""AI 서버 진입점.

[9장] `logging.basicConfig`를 여기서 부른다. 없으면 root 로거에 핸들러가 없어서
      Tool Gateway가 남기는 `logger.info` 감사 줄이 통째로 버려진다. uvicorn은
      자기 로거(`uvicorn.*`)만 설정할 뿐 우리 모듈의 로거는 건드리지 않는다.
      8장까지 "감사는 log.info로 남긴다"고 해 놓고 실제로는 안 보이던 자리다.

      로그 패턴에 request_uid를 넣는다. 자바 MDC + `%X{requestUid}`와 같은 방식이고,
      감사 테이블과 로그를 같은 값으로 맞춰 둬야 장애가 났을 때 둘을 오가며 볼 수 있다.
"""
import logging

from fastapi import FastAPI

from .config import settings
from .routers import agents as agents_router
from .routers import guardrails, health, rag, research
from .routers import tools as tools_router
from .safety.context import RequestUidLogFilter
from .tools.registry import register_default_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(request_uid)s] %(name)s: %(message)s",
)

# 필터는 로거가 아니라 **핸들러**에 건다. 로거에 걸면 그 로거로 직접 찍은 것만 처리되고,
# 하위 로거에서 올라온 레코드는 속성이 빈 채로 포매터에 닿아 로그가 통째로 사라진다
for _handler in logging.getLogger().handlers:
    _handler.addFilter(RequestUidLogFilter())

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(rag.router)
app.include_router(tools_router.router)
app.include_router(agents_router.router)
app.include_router(guardrails.router)          # ← 9장 추가


@app.on_event("startup")
def on_startup() -> None:
    register_default_tools()


@app.get("/")
def root() -> dict:
    return {"service": settings.service_name, "version": settings.version}