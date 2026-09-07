"""SQLAlchemy implementation of the job repository port."""

from sqlalchemy.orm import Session, selectinload

from talentaudit.adapters.db.models import JobModel, RequirementModel
from talentaudit.domain.enums import JobStatus, RequirementKind
from talentaudit.ports.repositories import JobRepository
from talentaudit.schemas.job import JobCreate, JobResponse, RequirementResponse


class SqlAlchemyJobRepository(JobRepository):
    """Store job policies using SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, payload: JobCreate) -> JobResponse:
        """Insert a job and its requirements in one transaction."""

        job = JobModel(
            title=payload.title,
            description=payload.description,
            rubric_version=payload.rubric_version,
            status=JobStatus.DRAFT.value,
            requirements=[
                RequirementModel(
                    position=position,
                    skill=requirement.skill,
                    kind=requirement.kind.value,
                    min_years=requirement.min_years,
                    weight=requirement.weight,
                )
                for position, requirement in enumerate(payload.requirements)
            ],
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return self._to_response(job)

    def get(self, job_id: str) -> JobResponse | None:
        """Fetch a job and eagerly load its requirements."""

        job = self._session.get(
            JobModel,
            job_id,
            options=[selectinload(JobModel.requirements)],
        )
        if job is None:
            return None
        return self._to_response(job)

    @staticmethod
    def _to_response(job: JobModel) -> JobResponse:
        """Map an ORM object to the public Pydantic response model."""

        requirements = [
            RequirementResponse(
                id=requirement.id,
                skill=requirement.skill,
                kind=RequirementKind(requirement.kind),
                min_years=requirement.min_years,
                weight=requirement.weight,
            )
            for requirement in job.requirements
        ]
        return JobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            rubric_version=job.rubric_version,
            status=JobStatus(job.status),
            requirements=requirements,
        )
