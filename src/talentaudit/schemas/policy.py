"""Deterministic policy evaluation schemas."""

from pydantic import BaseModel, ConfigDict

from talentaudit.domain.enums import (
    MatchStatus,
    PolicyRecommendation,
    RequirementKind,
)


class RequirementMatch(BaseModel):
    """Outcome of checking one required or preferred skill."""

    model_config = ConfigDict(str_strip_whitespace=True)

    skill: str
    kind: RequirementKind
    min_years: float
    candidate_years: float | None
    status: MatchStatus
    reason: str


class PolicyResult(BaseModel):
    """Complete deterministic policy result."""

    recommendation: PolicyRecommendation
    required_results: list[RequirementMatch]
    preferred_results: list[RequirementMatch]
    required_passed: int
    required_total: int
    preferred_passed: int
    preferred_total: int
