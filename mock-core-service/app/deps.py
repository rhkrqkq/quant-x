"""인증 의존성. Read와 Write가 서로 다른 키를 본다.

[보안] 이 파일이 8장의 핵심이다. AI 서버는 Read 키만 갖고 있으므로
Write 엔드포인트에 아무리 요청을 보내도 403에서 끝난다.
"""
from fastapi import Header, HTTPException, status

from .config import settings


def require_internal_key(x_internal_api_key: str = Header(default="")) -> None:
    """Tool Gateway(AI 서버)가 Read를 부를 때 쓰는 키."""
    if x_internal_api_key != settings.mock_core_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid or missing X-Internal-API-Key",
        )


def require_system_key(x_system_key: str = Header(default="")) -> None:
    """Spring Boot가 결재를 마치고 Write를 부를 때 쓰는 키.
    Read 키로는 통과할 수 없다. 두 값이 같아지지 않도록 .env에서 다르게 둔다.
    """
    if x_system_key != settings.mock_core_system_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid or missing X-System-Key",
        )