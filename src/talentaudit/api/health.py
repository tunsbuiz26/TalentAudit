"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from talentaudit.adapters.db.health import DatabaseHealthChecker
from talentaudit.config import Settings


class HealthResponse(BaseModel):
    """Response returned when the process is alive."""

    status: Literal["ok"]
    service: str


class ReadinessResponse(BaseModel):
    """Response returned when required dependencies are ready."""

    status: Literal["ready"]
    database: Literal["up"]


def create_health_router(
    settings: Settings,
    database_health_checker: DatabaseHealthChecker,
) -> APIRouter:
    """Build health routes with explicitly injected runtime dependencies."""

    router = APIRouter(tags=["system"])

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.app_name)

    @router.get("/ready", response_model=ReadinessResponse)
    def readiness() -> ReadinessResponse | JSONResponse:
        if not database_health_checker.check():
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "database": "down"},
            )
        return ReadinessResponse(status="ready", database="up")

    return router

