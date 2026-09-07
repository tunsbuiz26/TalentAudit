"""Deterministic job-policy matching."""

from talentaudit.domain.enums import (
    MatchStatus,
    PolicyRecommendation,
    RequirementKind,
)
from talentaudit.schemas.candidate import CandidateProfile
from talentaudit.schemas.job import JobCreate, RequirementCreate
from talentaudit.schemas.policy import PolicyResult, RequirementMatch


def _match_requirement(
    requirement: RequirementCreate,
    candidate: CandidateProfile,
    candidate_skills: set[str],
) -> RequirementMatch:
    """Evaluate one requirement using only validated candidate data."""

    candidate_years = candidate.experience_years.get(requirement.skill)
    if requirement.skill not in candidate_skills:
        return RequirementMatch(
            skill=requirement.skill,
            kind=requirement.kind,
            min_years=requirement.min_years,
            candidate_years=candidate_years,
            status=MatchStatus.FAIL,
            reason=f"skill '{requirement.skill}' is not present in profile",
        )

    if requirement.min_years == 0:
        return RequirementMatch(
            skill=requirement.skill,
            kind=requirement.kind,
            min_years=requirement.min_years,
            candidate_years=candidate_years,
            status=MatchStatus.PASS,
            reason="skill is present and no minimum experience is required",
        )

    if candidate_years is None:
        return RequirementMatch(
            skill=requirement.skill,
            kind=requirement.kind,
            min_years=requirement.min_years,
            candidate_years=None,
            status=MatchStatus.UNKNOWN,
            reason="skill is present but experience years are missing",
        )

    if candidate_years >= requirement.min_years:
        return RequirementMatch(
            skill=requirement.skill,
            kind=requirement.kind,
            min_years=requirement.min_years,
            candidate_years=candidate_years,
            status=MatchStatus.PASS,
            reason="candidate experience meets the minimum",
        )

    return RequirementMatch(
        skill=requirement.skill,
        kind=requirement.kind,
        min_years=requirement.min_years,
        candidate_years=candidate_years,
        status=MatchStatus.FAIL,
        reason="candidate experience is below the minimum",
    )


def match_policy(job: JobCreate, candidate: CandidateProfile) -> PolicyResult:
    """Return a deterministic recommendation for a job and candidate profile."""

    candidate_skills = set(candidate.skills)
    matches = [
        _match_requirement(requirement, candidate, candidate_skills)
        for requirement in job.requirements
    ]
    required_results = [
        result for result in matches if result.kind is RequirementKind.REQUIRED
    ]
    preferred_results = [
        result for result in matches if result.kind is RequirementKind.PREFERRED
    ]

    if any(result.status is MatchStatus.FAIL for result in required_results):
        recommendation = PolicyRecommendation.DOES_NOT_MEET
    elif any(result.status is MatchStatus.UNKNOWN for result in required_results):
        recommendation = PolicyRecommendation.NEEDS_REVIEW
    else:
        recommendation = PolicyRecommendation.MEETS

    return PolicyResult(
        recommendation=recommendation,
        required_results=required_results,
        preferred_results=preferred_results,
        required_passed=sum(
            result.status is MatchStatus.PASS for result in required_results
        ),
        required_total=len(required_results),
        preferred_passed=sum(
            result.status is MatchStatus.PASS for result in preferred_results
        ),
        preferred_total=len(preferred_results),
    )
