"""Application service for safe document ingestion."""

from talentaudit.ports.repositories import DocumentRepository
from talentaudit.ports.storage import DocumentStorage
from talentaudit.schemas.document import DocumentMetadata, DocumentUpload
from talentaudit.services.document_validator import DocumentValidator


class DocumentIngestionService:
    """Coordinate the document trust boundary before any future parsing step.

    Only validated bytes are passed to storage. The repository receives a
    metadata-only DTO, so raw document content cannot enter the database via
    this use case.
    """

    def __init__(
        self,
        validator: DocumentValidator,
        storage: DocumentStorage,
        repository: DocumentRepository,
    ) -> None:
        self._validator = validator
        self._storage = storage
        self._repository = repository

    def ingest(self, upload: DocumentUpload) -> DocumentMetadata:
        """Validate, store, and persist one document's safe metadata.

        If persistence fails after storage succeeds, the just-created file is
        deleted before the persistence error is re-raised. This avoids leaving
        an orphaned local file for a document absent from the database.
        """

        validated_document = self._validator.validate(upload)
        storage_key = self._storage.put(validated_document)
        metadata = DocumentMetadata(
            document_id=validated_document.document_id,
            storage_key=storage_key,
            mime_type=validated_document.mime_type,
            size_bytes=validated_document.size_bytes,
            sha256=validated_document.sha256,
        )

        try:
            return self._repository.create(metadata)
        except Exception:
            self._storage.delete(storage_key)
            raise
