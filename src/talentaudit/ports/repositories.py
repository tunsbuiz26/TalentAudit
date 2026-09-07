"""Application-facing repository interfaces."""

from typing import Protocol

from talentaudit.schemas.job import JobCreate, JobResponse


class JobRepository(Protocol):
    """Persistence port for recruiter job policies."""

    def create(self, payload: JobCreate) -> JobResponse:
        """Persist and return a job."""

        ...

    def get(self, job_id: str) -> JobResponse | None:
        """Return a job by identifier, if it exists."""

        ...
