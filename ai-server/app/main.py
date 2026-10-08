from fastapi import FastAPI
from .config import settings
from .routers import health, research, rag, tools as tools_router
from .routers import agents as agents_router
from .tools.registry import register_default_tools

app = FastAPI(title=settings.service_name, version=settings.version)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(rag.router)
app.include_router(tools_router.router)
app.include_router(agents_router.router)

@app.on_event("startup")
def on_startup() -> None:
    register_default_tools()

@app.get("/")
def root() -> dict:
    return {"service": settings.service_name, "version": settings.version}