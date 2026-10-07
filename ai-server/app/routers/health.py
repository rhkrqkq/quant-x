from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["health"])


@router.get("/ai/health")
def health() -> dict:
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.version,
        "llmProvider": settings.llm_provider,
        "killSwitchActive": settings.kill_switch_enabled,
    }