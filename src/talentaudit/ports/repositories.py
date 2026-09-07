"""Application-facing repository interfaces."""

from typing import Protocol

from talentaudit.schemas.document import DocumentMetadata
from talentaudit.schemas.job import JobCreate, JobResponse


class JobRepository(Protocol):
    """Persistence port for recruiter job policies."""

    def create(self, payload: JobCreate) -> JobResponse:
        """Persist and return a job."""

        ...

    def get(self, job_id: str) -> JobResponse | None:
        """Return a job by identifier, if it exists."""

        ...


class DocumentRepository(Protocol):
    """Persistence port for safe document metadata only."""

    def create(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Persist and return document metadata without raw document bytes."""

        ...

    def get(self, document_id: str) -> DocumentMetadata | None:
        """Return document metadata by identifier, if it exists."""

        ...
