"""Job policy CRUD endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from talentaudit.api.dependencies import get_job_repository
from talentaudit.application.services.job_service import JobService
from talentaudit.ports.repositories import JobRepository
from talentaudit.schemas.job import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])
JobRepositoryDependency = Annotated[JobRepository, Depends(get_job_repository)]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    repository: JobRepositoryDependency,
) -> JobResponse:
    """Create a draft job policy."""

    return JobService(repository).create_job(payload)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    repository: JobRepositoryDependency,
) -> JobResponse:
    """Return a job policy or HTTP 404 when it does not exist."""

    job = JobService(repository).get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return job
