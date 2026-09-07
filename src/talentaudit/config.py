"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TALENTAUDIT_",
        extra="ignore",
    )

    app_name: str = "TalentAudit"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://talentaudit:talentaudit@db:5432/talentaudit"
    )
    db_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Accept only PostgreSQL URLs for the MVP runtime."""

        if not value.startswith(("postgresql://", "postgresql+")):
            raise ValueError("DATABASE_URL must use a PostgreSQL scheme")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
