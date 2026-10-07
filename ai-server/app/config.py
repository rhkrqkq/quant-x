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

settings = Settings()