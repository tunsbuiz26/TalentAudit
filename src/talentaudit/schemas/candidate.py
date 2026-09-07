"""Candidate profile and evidence-bearing schemas."""

import math

from pydantic import BaseModel, ConfigDict, Field, model_validator

from talentaudit.domain.policies.normalization import normalize_skill
from talentaudit.schemas.evidence import EvidenceRef


class CandidateProfile(BaseModel):
    """Structured candidate data consumed by the deterministic matcher."""

    model_config = ConfigDict(str_strip_whitespace=True)

    skills: list[str] = Field(default_factory=list, max_length=500)
    experience_years: dict[str, float] = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list, max_length=1_000)

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "CandidateProfile":
        """Canonicalize skills and reject invalid experience values."""

        normalized_skills = [normalize_skill(skill) for skill in self.skills]
        if any(not skill for skill in normalized_skills):
            raise ValueError("skills must not contain blank values")
        if len(normalized_skills) != len(set(normalized_skills)):
            raise ValueError("skills must be unique")
        self.skills = normalized_skills

        normalized_experience: dict[str, float] = {}
        for skill, years in self.experience_years.items():
            normalized_skill = normalize_skill(skill)
            if not normalized_skill:
                raise ValueError("experience skill keys must not be blank")
            if not math.isfinite(years) or years < 0:
                raise ValueError("experience years must be finite and non-negative")
            normalized_experience[normalized_skill] = years
        self.experience_years = normalized_experience
        return self
