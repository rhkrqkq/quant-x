from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 인증
    ai_server_api_key: str = "changeme-internal-key"

    # LLM (3장에서는 미사용, 6장부터)
    llm_provider: str = "mock"
    llm_model: str = "mock-model"
    openai_api_key: str = ""

    # 보안
    allow_external_llm: bool = True
    kill_switch_enabled: bool = False

    # 서비스
    service_name: str = "quantx-ai-server"
    version: str = "0.1.0"

    mariadb_url: str = "mysql+pymysql://root:root@localhost:3306/quantx?charset=utf8mb4"

    agent_max_iterations: int = 1
    agent_timeout_seconds: int = 60

    mock_core_base_url: str = "http://localhost:9000"
    mock_core_api_key: str = "changeme-core-key"

    # 가드레일·거버넌스 (9장)
    # Moderation은 기본 off. 외부 호출이라 10장 폐쇄망 모드에서는 나갈 수 없다
    enable_moderation: bool = False
    rate_limit_per_min: int = 60        # 사용자별 분당 Tool 호출 상한. 0이면 제한 없음

    # [보안] 감사 기록 전용 커넥션. INSERT·SELECT만 가진 계정이라 이 커넥션으로는
    #        감사 로그를 고칠 수 없다. 8장의 조회 키/시스템 키 분리와 같은 사상이다
    mariadb_audit_url: str = (
        "mysql+pymysql://quantx_audit:audit-only-pass@localhost:3306/quantx?charset=utf8mb4")

settings = Settings()