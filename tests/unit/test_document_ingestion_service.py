"""Tests for document ingestion orchestration at the trust boundary."""

import pytest

from talentaudit.application.services.document_ingestion_service import (
    DocumentIngestionService,
)
from talentaudit.config import Settings
from talentaudit.domain.exceptions import DocumentValidationError
from talentaudit.schemas.document import (
    DocumentMetadata,
    DocumentUpload,
    ValidatedDocument,
)
from talentaudit.services.document_validator import DocumentValidator


class RecordingStorage:
    """In-memory storage fake that records calls without writing candidate data."""

    def __init__(self) -> None:
        self.stored_documents: list[ValidatedDocument] = []
        self.deleted_keys: list[str] = []

    def put(self, document: ValidatedDocument) -> str:
        self.stored_documents.append(document)
        return "documents/generated-document.txt"

    def get(self, storage_key: str) -> bytes:
        raise AssertionError("get is not part of document ingestion")

    def delete(self, storage_key: str) -> None:
        self.deleted_keys.append(storage_key)


class RecordingRepository:
    """Metadata-only repository fake for application service tests."""

    def __init__(self) -> None:
        self.created_metadata: list[DocumentMetadata] = []

    def create(self, metadata: DocumentMetadata) -> DocumentMetadata:
        self.created_metadata.append(metadata)
        return metadata

    def get(self, document_id: str) -> DocumentMetadata | None:
        return None


class FailingRepository(RecordingRepository):
    """Repository fake that simulates a database persistence failure."""

    def create(self, metadata: DocumentMetadata) -> DocumentMetadata:
        self.created_metadata.append(metadata)
        raise RuntimeError("synthetic persistence failure")


@pytest.fixture
def validator() -> DocumentValidator:
    return DocumentValidator(Settings(environment="test"))


def test_ingest_validates_before_calling_storage_or_repository(
    validator: DocumentValidator,
) -> None:
    storage = RecordingStorage()
    repository = RecordingRepository()
    service = DocumentIngestionService(validator, storage, repository)
    upload = DocumentUpload(
        filename="../unsafe.txt",
        declared_mime_type="text/plain",
        content=b"Synthetic test content.",
    )

    with pytest.raises(DocumentValidationError):
        service.ingest(upload)

    assert storage.stored_documents == []
    assert repository.created_metadata == []


def test_ingest_stores_validated_bytes_and_persists_metadata_only(
    validator: DocumentValidator,
) -> None:
    storage = RecordingStorage()
    repository = RecordingRepository()
    service = DocumentIngestionService(validator, storage, repository)
    upload = DocumentUpload(
        filename="synthetic-cv.txt",
        declared_mime_type="text/plain",
        content=b"Synthetic test content.",
    )

    metadata = service.ingest(upload)

    assert storage.stored_documents[0].content == upload.content
    assert repository.created_metadata == [metadata]
    assert "content" not in metadata.model_dump()
    assert storage.deleted_keys == []


def test_ingest_deletes_file_when_metadata_persistence_fails(
    validator: DocumentValidator,
) -> None:
    storage = RecordingStorage()
    repository = FailingRepository()
    service = DocumentIngestionService(validator, storage, repository)
    upload = DocumentUpload(
        filename="synthetic-cv.txt",
        declared_mime_type="text/plain",
        content=b"Synthetic test content.",
    )

    with pytest.raises(RuntimeError, match="synthetic persistence failure"):
        service.ingest(upload)

    assert len(repository.created_metadata) == 1
    assert storage.deleted_keys == ["documents/generated-document.txt"]
