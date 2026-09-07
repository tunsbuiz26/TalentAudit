import pytest
from pydantic import ValidationError

from talentaudit.domain.enums import RequirementKind
from talentaudit.schemas.candidate import CandidateProfile
from talentaudit.schemas.evidence import EvidenceRef
from talentaudit.schemas.job import JobCreate


def test_job_schema_normalizes_skills_and_keeps_required_preferred_kind() -> None:
    job = JobCreate(
        title="AI/ML Engineer",
        description="Build and maintain machine learning services.",
        requirements=[
            {"skill": " Python ", "kind": "REQUIRED", "min_years": 2},
            {"skill": "machine learning", "kind": "PREFERRED"},
        ],
    )

    assert job.requirements[0].skill == "python"
    assert job.requirements[0].kind is RequirementKind.REQUIRED
    assert job.requirements[1].kind is RequirementKind.PREFERRED


def test_job_schema_rejects_duplicate_skills() -> None:
    with pytest.raises(ValidationError, match="unique skills"):
        JobCreate(
            title="AI/ML Engineer",
            description="Build services.",
            requirements=[
                {"skill": "Python"},
                {"skill": " python "},
            ],
        )


def test_schema_rejects_invalid_requirement_and_evidence_values() -> None:
    with pytest.raises(ValidationError):
        JobCreate(
            title="AI/ML Engineer",
            description="Build services.",
            requirements=[{"skill": "Python", "min_years": -1}],
        )

    with pytest.raises(ValidationError, match="end must be greater"):
        EvidenceRef(
            document_id="synthetic-cv-001",
            section="skills",
            start=20,
            end=20,
            text="Python",
        )


def test_candidate_profile_normalizes_experience_and_rejects_invalid_values() -> None:
    profile = CandidateProfile(
        skills=["Python", "Machine Learning"],
        experience_years={" Python ": 3.0},
    )

    assert profile.skills == ["python", "machine learning"]
    assert profile.experience_years == {"python": 3.0}

    with pytest.raises(ValidationError, match="non-negative"):
        CandidateProfile(experience_years={"Python": -0.5})
