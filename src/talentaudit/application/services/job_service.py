"""Application service for job policy use cases."""

from talentaudit.ports.repositories import JobRepository
from talentaudit.schemas.job import JobCreate, JobResponse


class JobService:
    """Coordinate job use cases without knowing HTTP or SQLAlchemy details."""

    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def create_job(self, payload: JobCreate) -> JobResponse:
        """Create a draft job policy."""

        return self._repository.create(payload)

    def get_job(self, job_id: str) -> JobResponse | None:
        """Get a job policy by identifier."""

        return self._repository.get(job_id)
