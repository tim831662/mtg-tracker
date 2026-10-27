"""Read local configuration without opening a database connection."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MTG Tracker"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://mtg:mtg_local@localhost:5432/mtg_tracker"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
