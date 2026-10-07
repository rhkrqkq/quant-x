from fastapi import FastAPI
from .routers import health, research
from .config import settings
from .routers import health, research, rag

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(rag.router)

@app.get("/")
def root() -> dict:
    return {"service": settings.service_name, "version": settings.version}