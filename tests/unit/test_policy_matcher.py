import pytest
from pydantic import ValidationError

from talentaudit.domain.enums import MatchStatus, PolicyRecommendation
from talentaudit.domain.policies.matcher import match_policy
from talentaudit.schemas.candidate import CandidateProfile
from talentaudit.schemas.job import JobCreate


def make_job() -> JobCreate:
    return JobCreate(
        title="AI/ML Engineer",
        description="Build machine learning services.",
        requirements=[
            {"skill": "Python", "kind": "REQUIRED", "min_years": 2},
            {"skill": "SQL", "kind": "REQUIRED"},
            {"skill": "Kubernetes", "kind": "PREFERRED"},
        ],
    )


def test_required_and_preferred_skills_are_evaluated_separately() -> None:
    result = match_policy(
        make_job(),
        CandidateProfile(
            skills=["python", "sql"],
            experience_years={"python": 3},
        ),
    )

    assert result.recommendation is PolicyRecommendation.MEETS
    assert result.required_passed == 2
    assert result.required_total == 2
    assert result.preferred_passed == 0
    assert result.preferred_total == 1
    assert result.preferred_results[0].status is MatchStatus.FAIL


def test_required_min_years_failure_does_not_become_unknown() -> None:
    result = match_policy(
        make_job(),
        CandidateProfile(
            skills=["python", "sql"],
            experience_years={"python": 1},
        ),
    )

    assert result.recommendation is PolicyRecommendation.DOES_NOT_MEET
    assert result.required_results[0].status is MatchStatus.FAIL


def test_missing_experience_is_needs_review_not_a_guess() -> None:
    result = match_policy(
        make_job(),
        CandidateProfile(skills=["python", "sql"]),
    )

    assert result.recommendation is PolicyRecommendation.NEEDS_REVIEW
    assert result.required_results[0].status is MatchStatus.UNKNOWN
    assert result.required_results[0].candidate_years is None


def test_same_input_produces_identical_output() -> None:
    candidate = CandidateProfile(
        skills=["Python", "SQL"],
        experience_years={"Python": 2},
    )

    first = match_policy(make_job(), candidate).model_dump(mode="json")
    second = match_policy(make_job(), candidate).model_dump(mode="json")

    assert first == second


def test_negative_experience_is_rejected_before_matching() -> None:
    with pytest.raises(ValidationError):
        CandidateProfile(skills=["Python"], experience_years={"Python": -1})
