"""Version 1 API router."""

from fastapi import APIRouter

from talentaudit.api.v1.jobs import router as jobs_router

router = APIRouter()
router.include_router(jobs_router)
