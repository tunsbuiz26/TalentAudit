"""Validate and parse all ten synthetic development CVs without network."""

import socket
from pathlib import Path

import pytest

from talentaudit.config import Settings
from talentaudit.schemas.document import DocumentUpload
from talentaudit.services.document_parser import DocumentParser
from talentaudit.services.document_validator import DocumentValidator

FIXTURES = Path(__file__).parents[1] / "fixtures" / "documents"
CASES = [(language, number) for language in ("vi", "en") for number in range(1, 6)]


@pytest.mark.parametrize(("language", "number"), CASES)
def test_synthetic_cv(
    language: str, number: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("Network access is forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    path = FIXTURES / f"{language}_{number}.txt"
    content = path.read_bytes()
    settings = Settings(environment="test")
    validated = DocumentValidator(settings).validate(
        DocumentUpload(
            filename=path.name, declared_mime_type="text/plain", content=content
        )
    )
    parser = DocumentParser(settings)
    parsed = parser.parse(validated)
    assert parsed.document_language == language
    assert parsed.text == content.decode("utf-8")
    assert parsed.sha256 == validated.sha256
    assert parsed.document_id == validated.document_id
    assert parsed.page_count is None
    assert parser.parse(validated) == parsed
