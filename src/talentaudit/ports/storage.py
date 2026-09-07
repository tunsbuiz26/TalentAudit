"""Application-facing interfaces for validated document byte storage."""

from typing import Protocol

from talentaudit.schemas.document import ValidatedDocument


class DocumentStorage(Protocol):
    """Store only bytes that passed the document validation trust boundary."""

    def put(self, document: ValidatedDocument) -> str:
        """Store a validated document and return its generated storage key."""

        ...

    def get(self, storage_key: str) -> bytes:
        """Return document bytes for a safe, generated storage key."""

        ...

    def delete(self, storage_key: str) -> None:
        """Remove a document identified by a safe, generated storage key."""

        ...
