from pathlib import Path

import pytest
from pydantic import ValidationError

from talentaudit.config import Settings


def test_settings_use_safe_local_defaults() -> None:
    settings = Settings(environment="test")

    assert settings.environment == "test"
    assert settings.database_url.startswith("postgresql+")
    assert settings.db_connect_timeout_seconds == 3


def test_settings_reject_non_postgresql_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", database_url="sqlite:///local.db")


def test_document_settings_have_safe_defaults() -> None:
    settings = Settings(environment="test")

    assert settings.document_storage_path == Path("var/documents")
    assert settings.allowed_document_mime_types == (
        "application/pdf",
        "text/plain",
    )
    assert settings.max_upload_bytes == 5 * 1024 * 1024
    assert settings.max_pdf_pages == 25
    assert settings.max_extracted_text_chars == 1_000_000


def test_document_settings_read_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TALENTAUDIT_DOCUMENT_STORAGE_PATH", "test-documents")
    monkeypatch.setenv(
        "TALENTAUDIT_ALLOWED_DOCUMENT_MIME_TYPES",
        '["text/plain"]',
    )
    monkeypatch.setenv("TALENTAUDIT_MAX_UPLOAD_BYTES", "1024")
    monkeypatch.setenv("TALENTAUDIT_MAX_PDF_PAGES", "2")
    monkeypatch.setenv("TALENTAUDIT_MAX_EXTRACTED_TEXT_CHARS", "500")

    settings = Settings(environment="test")

    assert settings.document_storage_path == Path("test-documents")
    assert settings.allowed_document_mime_types == ("text/plain",)
    assert settings.max_upload_bytes == 1024
    assert settings.max_pdf_pages == 2
    assert settings.max_extracted_text_chars == 500


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("max_upload_bytes", 0),
        ("max_pdf_pages", 0),
        ("max_extracted_text_chars", 0),
    ],
)
def test_document_limits_reject_non_positive_values(
    field_name: str,
    value: int,
) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"environment": "test", field_name: value})


@pytest.mark.parametrize(
    "mime_types",
    [
        (),
        ("application/pdf", "application/pdf"),
        ("image/png",),
    ],
)
def test_document_settings_reject_invalid_mime_configuration(
    mime_types: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", allowed_document_mime_types=mime_types)
