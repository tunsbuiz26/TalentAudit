"""Domain enums shared by schemas and services."""

from enum import StrEnum


class JobStatus(StrEnum):
    """Lifecycle states for a recruiter-created job."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class RequirementKind(StrEnum):
    """Whether a job requirement is mandatory or preferred."""

    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"


class MatchStatus(StrEnum):
    """Result for one deterministic requirement check."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class PolicyRecommendation(StrEnum):
    """Recommendation produced by deterministic policy evaluation."""

    MEETS = "MEETS"
    DOES_NOT_MEET = "DOES_NOT_MEET"
    NEEDS_REVIEW = "NEEDS_REVIEW"
