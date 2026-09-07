"""FastAPI application entry point."""

from fastapi import FastAPI

from talentaudit.adapters.db.health import (
    DatabaseHealthChecker,
    SqlAlchemyDatabaseHealthChecker,
)
from talentaudit.api.health import create_health_router
from talentaudit.api.v1.router import router as api_v1_router
from talentaudit.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    database_health_checker: DatabaseHealthChecker | None = None,
) -> FastAPI:
    """Create the FastAPI application with injectable dependencies."""

    resolved_settings = settings or get_settings()
    resolved_checker = database_health_checker or SqlAlchemyDatabaseHealthChecker(
        resolved_settings.database_url,
        resolved_settings.db_connect_timeout_seconds,
    )
    application = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
    )
    application.include_router(
        create_health_router(resolved_settings, resolved_checker),
    )
    application.include_router(api_v1_router, prefix="/api/v1")
    return application


app = create_app()
