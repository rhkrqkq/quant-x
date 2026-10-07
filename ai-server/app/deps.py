from fastapi import Header, HTTPException, status, Depends
from .config import settings


async def verify_internal_key(x_internal_api_key: str = Header(...)) -> None:
    if x_internal_api_key != settings.ai_server_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


async def require_user_id(x_user_id: str = Header(...)) -> str:
    return x_user_id