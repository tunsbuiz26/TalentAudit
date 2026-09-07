"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
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

    # Document-processing limits belong in configuration so services never need
    # their own hard-coded byte, page, or text-length limits.
    document_storage_path: Path = Path("var/documents")
    allowed_document_mime_types: tuple[str, ...] = (
        "application/pdf",
        "text/plain",
    )
    max_upload_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    max_pdf_pages: int = Field(default=25, ge=1, le=1_000)
    max_extracted_text_chars: int = Field(default=1_000_000, ge=1)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Accept only PostgreSQL URLs for the MVP runtime."""

        if not value.startswith(("postgresql://", "postgresql+")):
            raise ValueError("DATABASE_URL must use a PostgreSQL scheme")
        return value

    @field_validator("allowed_document_mime_types")
    @classmethod
    def validate_allowed_document_mime_types(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Allow only file types implemented by the MVP document parser."""

        supported = {"application/pdf", "text/plain"}
        if not value:
            raise ValueError("at least one document MIME type must be allowed")
        if any(mime not in supported for mime in value):
            raise ValueError("unsupported document MIME type configured")
        if len(value) != len(set(value)):
            raise ValueError("document MIME types must be unique")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
