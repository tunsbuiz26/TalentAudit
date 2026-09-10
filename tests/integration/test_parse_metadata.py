"""Metadata updates are tied to the stored document's hash."""

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from talentaudit.adapters.db.base import Base
from talentaudit.adapters.db.document_repository import SqlAlchemyDocumentRepository
from talentaudit.schemas.document import DocumentMetadata, DocumentParseMetadata


@pytest.mark.parametrize(
    "fields",
    [
        {"parser_status": "PARSED"},
        {"parser_status": "FAILED"},
        {"parser_status": "PENDING", "page_count": 1},
        {"parser_status": "PARSED", "document_language": "fr"},
        {"parser_status": "PARSED", "document_language": "en", "page_count": 0},
        {
            "parser_status": "PARSED",
            "document_language": "en",
            "parse_error_code": "PARSER_ERROR",
        },
        {"text": "raw synthetic CV"},
    ],
)
def test_inconsistent_parse_metadata_rejected(fields) -> None:
    with pytest.raises(ValidationError):
        DocumentParseMetadata(document_id="synthetic", sha256="a" * 64, **fields)


def test_parsing_service_persists_success_and_failure() -> None:
    from talentaudit.application.services.document_parsing_service import (
        DocumentParsingService,
    )
    from talentaudit.config import Settings
    from talentaudit.domain.exceptions import DocumentParseError
    from talentaudit.schemas.document import DocumentUpload
    from talentaudit.services.document_parser import DocumentParser
    from talentaudit.services.document_validator import DocumentValidator

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None)
    with Session(engine) as session:
        repository = SqlAlchemyDocumentRepository(session)
        service = DocumentParsingService(DocumentParser(settings), repository)
        for content, expected in [(b"Skills: Python", "PARSED"), (b"  \n", "FAILED")]:
            document = DocumentValidator(settings).validate(
                DocumentUpload(
                    filename="synthetic.txt",
                    declared_mime_type="text/plain",
                    content=content,
                )
            )
            repository.create(
                DocumentMetadata(
                    document_id=document.document_id,
                    storage_key=document.document_id + ".txt",
                    mime_type=document.mime_type,
                    size_bytes=document.size_bytes,
                    sha256=document.sha256,
                )
            )
            if expected == "FAILED":
                with pytest.raises(DocumentParseError):
                    service.parse_and_persist(document)
            else:
                assert service.parse_and_persist(document).text == content.decode()
            stored = repository.get(document.document_id)
            assert stored.parser_status == expected
            assert stored.page_count is None
            assert "text" not in stored.model_dump()
    engine.dispose()


def test_parse_metadata_roundtrip_and_stale_hash_rejected() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = SqlAlchemyDocumentRepository(session)
        repository.create(
            DocumentMetadata(
                document_id="synthetic",
                storage_key="generated.pdf",
                mime_type="application/pdf",
                size_bytes=42,
                sha256="a" * 64,
            )
        )
        success = DocumentParseMetadata(
            document_id="synthetic",
            sha256="a" * 64,
            parser_status="PARSED",
            document_language="vi",
            page_count=2,
        )
        repository.update_parse_metadata(success)
        assert repository.get("synthetic").parser_status == "PARSED"
        assert repository.get("synthetic").page_count == 2
        with pytest.raises(ValueError):
            repository.update_parse_metadata(
                success.model_copy(update={"sha256": "b" * 64})
            )
        failure = DocumentParseMetadata(
            document_id="synthetic",
            sha256="a" * 64,
            parser_status="FAILED",
            parse_error_code="PARSE_TIMEOUT",
        )
        repository.update_parse_metadata(failure)
        fetched = repository.get("synthetic")
        assert fetched.parser_status == "FAILED"
        assert fetched.document_language is None
        assert fetched.page_count is None
        assert fetched.parse_error_code == "PARSE_TIMEOUT"
        with pytest.raises(LookupError):
            repository.update_parse_metadata(
                failure.model_copy(update={"document_id": "absent"})
            )
    engine.dispose()
