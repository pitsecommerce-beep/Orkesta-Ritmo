from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    redis_url: str = "redis://localhost:6379"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model_extraction: str = "gpt-4o-mini"
    llm_model_chat: str = "gpt-4o"

    efirma_master_key: str = ""
    feature_efirma: bool = False

    chat_messages_per_month_free: int = 20
    chat_messages_per_month_essential: int = 100
    chat_messages_per_month_complete: int = 500

    site_url: str = "http://localhost:3000"

    api_port: int = 8000
    next_public_api_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
