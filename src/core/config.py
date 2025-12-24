from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STOCK_", env_file=".env", extra="ignore")

    runs_dir: str = "runs"
    model_registry_path: str = "services/mcp_server/models.yaml"
    default_model_id: str = "public:gpt-x"
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
