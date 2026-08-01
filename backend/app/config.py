from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "conversational-bi"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://bi_user:bi_password@localhost:5432/conversational_bi"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-32-byte-key-for-fernet!!"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    llm_provider: str = "google"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"

    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "conversational-bi"

    query_timeout_seconds: int = 30
    query_max_rows: int = 10000

    rate_limit_per_user: int = 60
    rate_limit_per_org: int = 1000

    oidc_enabled: bool = False
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_discovery_url: str = ""


settings = Settings()
