"""Job and requirement schemas."""

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, model_validator

from talentaudit.domain.enums import JobStatus, RequirementKind
from talentaudit.domain.policies.normalization import normalize_skill


class RequirementCreate(BaseModel):
    """Input contract for one job requirement."""

    model_config = ConfigDict(str_strip_whitespace=True)

    skill: str = Field(min_length=1, max_length=100)
    kind: RequirementKind = RequirementKind.REQUIRED
    min_years: float = Field(default=0, ge=0, le=100)
    weight: PositiveFloat = 1.0

    @model_validator(mode="after")
    def normalize(self) -> "RequirementCreate":
        """Canonicalize skill keys before policy evaluation and persistence."""

        normalized_skill = normalize_skill(self.skill)
        if not normalized_skill:
            raise ValueError("skill must not be blank")
        self.skill = normalized_skill
        return self


class JobCreate(BaseModel):
    """Input contract for creating a recruiter job policy."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=20_000)
    rubric_version: str = Field(default="v1", min_length=1, max_length=50)
    requirements: list[RequirementCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_requirements(self) -> "JobCreate":
        """Reject duplicate skills whose policy meaning would be ambiguous."""

        skills = [requirement.skill for requirement in self.requirements]
        if len(skills) != len(set(skills)):
            raise ValueError("requirements must contain unique skills")
        return self


class RequirementResponse(RequirementCreate):
    """Persisted requirement returned by the API."""

    id: str


class JobResponse(BaseModel):
    """Persisted job returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    rubric_version: str
    status: JobStatus
    requirements: list[RequirementResponse]
