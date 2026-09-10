"""SQLAlchemy implementation of the safe document metadata repository."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from talentaudit.adapters.db.models import DocumentModel
from talentaudit.ports.repositories import DocumentRepository
from talentaudit.schemas.document import DocumentMetadata, DocumentParseMetadata


class SqlAlchemyDocumentRepository(DocumentRepository):
    """Store document metadata without ever accepting raw document bytes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Insert metadata for a document already saved by a storage adapter."""

        if metadata.parser_status != "PENDING":
            raise ValueError("new document must have pending parse metadata")
        document = DocumentModel(
            id=metadata.document_id,
            storage_key=metadata.storage_key,
            sha256=metadata.sha256,
            mime_type=metadata.mime_type,
            size_bytes=metadata.size_bytes,
        )
        self._session.add(document)
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise
        self._session.refresh(document)
        return self._to_metadata(document)

    def get(self, document_id: str) -> DocumentMetadata | None:
        """Fetch safe metadata by identifier."""

        document = self._session.get(DocumentModel, document_id)
        if document is None:
            return None
        return self._to_metadata(document)

    def update_parse_metadata(self, metadata: DocumentParseMetadata) -> None:
        """Update safe metadata atomically; reject unknown IDs or stale provenance."""

        metadata = DocumentParseMetadata.model_validate(metadata.model_dump())
        document = self._session.get(DocumentModel, metadata.document_id)
        if document is None:
            raise LookupError("document not found")
        if document.sha256 != metadata.sha256:
            raise ValueError("document hash mismatch")
        if metadata.parser_status == "PARSED":
            is_pdf = document.mime_type == "application/pdf"
            if is_pdf != (metadata.page_count is not None):
                raise ValueError("page count does not match document MIME")
        document.parser_status = metadata.parser_status
        document.document_language = metadata.document_language
        document.page_count = metadata.page_count
        document.parse_error_code = metadata.parse_error_code
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    @staticmethod
    def _to_metadata(document: DocumentModel) -> DocumentMetadata:
        """Map an ORM record to the metadata-only application contract."""

        return DocumentMetadata.model_validate(
            {
                "document_id": document.id,
                "storage_key": document.storage_key,
                "mime_type": document.mime_type,
                "size_bytes": document.size_bytes,
                "sha256": document.sha256,
                "parser_status": document.parser_status,
                "document_language": document.document_language,
                "page_count": document.page_count,
                "parse_error_code": document.parse_error_code,
            }
        )
