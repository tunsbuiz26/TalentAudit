"""SQLAlchemy implementation of the safe document metadata repository."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from talentaudit.adapters.db.models import DocumentModel
from talentaudit.ports.repositories import DocumentRepository
from talentaudit.schemas.document import DocumentMetadata


class SqlAlchemyDocumentRepository(DocumentRepository):
    """Store document metadata without ever accepting raw document bytes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Insert metadata for a document already saved by a storage adapter."""

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
            }
        )
