"""SQLAlchemy session factory and FastAPI database dependency."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from talentaudit.config import get_settings


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Create one process-local SQLAlchemy session factory lazily."""

    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    """Yield a database session for one API request."""

    with get_session_factory()() as session:
        yield session
