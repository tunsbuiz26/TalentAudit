"""Database connectivity adapter used by the readiness endpoint."""

from typing import Protocol

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class DatabaseHealthChecker(Protocol):
    """Port used by the API to check database readiness."""

    def check(self) -> bool:
        """Return whether the database accepts a trivial query."""

        ...


class SqlAlchemyDatabaseHealthChecker:
    """PostgreSQL readiness check backed by a SQLAlchemy engine."""

    def __init__(self, database_url: str, connect_timeout_seconds: int) -> None:
        self._database_url = database_url
        self._connect_timeout_seconds = connect_timeout_seconds
        self._engine: Engine | None = None

    def check(self) -> bool:
        """Run a minimal query without exposing connection details."""

        try:
            if self._engine is None:
                self._engine = create_engine(
                    self._database_url,
                    connect_args={
                        "connect_timeout": self._connect_timeout_seconds,
                    },
                    pool_pre_ping=True,
                )
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except (ImportError, SQLAlchemyError, OSError):
            return False
        return True
