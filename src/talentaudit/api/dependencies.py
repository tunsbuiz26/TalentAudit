"""FastAPI dependency wiring for infrastructure ports."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from talentaudit.adapters.db.job_repository import SqlAlchemyJobRepository
from talentaudit.adapters.db.session import get_db_session
from talentaudit.ports.repositories import JobRepository

DatabaseSession = Annotated[Session, Depends(get_db_session)]


def get_job_repository(session: DatabaseSession) -> JobRepository:
    """Build a job repository for the current request."""

    return SqlAlchemyJobRepository(session)
