"""Mock Core Service 설정. ai-server/app/config.py와 같은 방식(pydantic-settings)을 쓴다."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 인증 — Read와 Write를 다른 키로 나눈다. 이 분리가 8장의 핵심이다
    mock_core_api_key: str = "changeme-core-key"        # Tool Gateway(AI 서버) → Read
    mock_core_system_key: str = "changeme-system-key"   # Spring Boot(결재 후) → Write

    # 시뮬레이션 — 기본은 꺼 둔다. 켜는 건 별도 Step에서
    mock_core_latency_ms_min: int = 0
    mock_core_latency_ms_max: int = 0
    mock_core_fail_rate: float = 0.0

    # 비즈니스 룰 (원 단위)
    order_single_limit_krw: int = 100_000_000     # 단일 주문 1억
    order_daily_limit_krw: int = 500_000_000      # 일일 누적 5억
    order_decision_timeout_sec: int = 900         # 결재 만료 15분

    # DB
    mock_core_db_path: str = "./data/core.db"

    service_name: str = "mock-core-service"
    version: str = "0.1.0"


settings = Settings()