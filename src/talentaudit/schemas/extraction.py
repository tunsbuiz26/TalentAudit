"""Strict provider DTOs and the safe service outcome (not a hiring decision)."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from talentaudit.domain.extraction_errors import ExtractionFailureCode
from talentaudit.domain.policies.normalization import normalize_skill
from talentaudit.schemas.candidate import CandidateProfile
from talentaudit.schemas.evidence import EvidenceRef


class SkillClaim(BaseModel):
    """Associate each skill and optional duration with its own source evidence."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    skill: str = Field(min_length=1, max_length=200)
    status: Literal["KNOWN", "UNKNOWN"]
    years: float | None = Field(ge=0, allow_inf_nan=False, strict=True)
    skill_evidence: list[EvidenceRef] = Field(max_length=20)
    experience_evidence: list[EvidenceRef] = Field(max_length=20)

    @model_validator(mode="after")
    def validate_claim(self) -> Self:
        """UNKNOWN is not a number; null years must not have duration claims."""

        if not normalize_skill(self.skill):
            raise ValueError("blank skill")
        if self.status == "UNKNOWN" and self.years is not None:
            raise ValueError("UNKNOWN claim cannot assert years")
        if self.years is None and self.experience_evidence:
            raise ValueError("duration evidence requires years")
        return self


class ExtractedProfile(BaseModel):
    """Wire schema uses lists, not dynamic dictionaries unsupported by strict JSON."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    claims: list[SkillClaim] = Field(max_length=500)

    @model_validator(mode="after")
    def unique_skills(self) -> Self:
        """Conflicting or duplicated normalized claims are a schema failure."""

        skills = [normalize_skill(claim.skill) for claim in self.claims]
        if len(skills) != len(set(skills)):
            raise ValueError("duplicate skill claims")
        return self


class ExtractionOutcome(BaseModel):
    """Only SUCCESS exposes a usable profile; downstream code must check status."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    status: Literal["SUCCESS", "NEEDS_REVIEW"]
    profile: CandidateProfile | None = Field(default=None, repr=False)
    failure_code: ExtractionFailureCode | None = None
    attempts: int = Field(ge=1, le=2)
    prompt_version: str
    document_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        """Make partial or failed results impossible to mistake for success."""

        if self.status == "SUCCESS":
            if self.profile is None or self.failure_code is not None:
                raise ValueError("success requires profile and no failure")
        elif self.profile is not None or self.failure_code is None:
            raise ValueError("review requires failure and no usable profile")
        return self
