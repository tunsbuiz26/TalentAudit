"""Extract through a port, check evidence, then expose a matcher-compatible profile."""

from pydantic import ValidationError

from talentaudit.domain.extraction_errors import (
    EvidenceValidationFailure,
    ExtractionFailureCode,
    LLMFailure,
    LLMSchemaFailure,
)
from talentaudit.domain.policies.normalization import normalize_skill
from talentaudit.ports.llm import LLMClient
from talentaudit.prompts import load_profile_prompt
from talentaudit.schemas.candidate import CandidateProfile
from talentaudit.schemas.document import ParsedDocument
from talentaudit.schemas.extraction import ExtractedProfile, ExtractionOutcome
from talentaudit.schemas.llm import UntrustedDocument
from talentaudit.services.evidence_validator import (
    validate_evidence,
    validate_skill_evidence,
)


def _validated_profile(
    extracted: ExtractedProfile, document: ParsedDocument
) -> CandidateProfile:
    """Map only fully supported claims; no guess or partial match on failed input."""

    profile = CandidateProfile()
    for claim in extracted.claims:
        validate_evidence(claim.skill_evidence, document)
        validate_skill_evidence(claim.skill, claim.skill_evidence)
        skill = normalize_skill(claim.skill)
        profile.skills.append(skill)
        profile.skill_evidence[skill] = claim.skill_evidence
        profile.evidence_refs.extend(claim.skill_evidence)
        if claim.years is not None:
            validate_evidence(claim.experience_evidence, document)
            validate_skill_evidence(claim.skill, claim.experience_evidence)
            profile.experience_years[skill] = claim.years
            profile.experience_evidence[skill] = claim.experience_evidence
            profile.evidence_refs.extend(claim.experience_evidence)
    # Revalidate after assembling mutable collections (Pydantic assignment is off).
    return CandidateProfile.model_validate(profile.model_dump())


class ProfileExtractor:
    """One schema retry at most. Provider and evidence failures never retry."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client
        self._prompt = load_profile_prompt()

    def extract(self, document: ParsedDocument) -> ExtractionOutcome:
        """Return a safe typed result; do not log raw provider or document data."""

        data = UntrustedDocument(document_id=document.document_id, text=document.text)
        failure = ExtractionFailureCode.SCHEMA_INVALID
        for attempt in (1, 2):
            try:
                response = self._client.generate_structured(
                    prompt=self._prompt, document=data, output_model=ExtractedProfile
                )
                # Defend against a custom adapter returning model_construct() output.
                extracted = ExtractedProfile.model_validate(response.model_dump())
            except (LLMSchemaFailure, ValidationError):
                continue
            except LLMFailure as error:
                failure = error.code
                break
            if not extracted.claims or any(
                claim.status == "UNKNOWN" for claim in extracted.claims
            ):
                failure = ExtractionFailureCode.UNKNOWN
                break
            try:
                profile = _validated_profile(extracted, document)
            except (EvidenceValidationFailure, ValidationError):
                failure = ExtractionFailureCode.EVIDENCE_INVALID
                break
            return ExtractionOutcome(
                status="SUCCESS",
                profile=profile,
                attempts=attempt,
                prompt_version=self._prompt.version,
                document_id=document.document_id,
                sha256=document.sha256,
            )
        return ExtractionOutcome(
            status="NEEDS_REVIEW",
            failure_code=failure,
            attempts=attempt,
            prompt_version=self._prompt.version,
            document_id=document.document_id,
            sha256=document.sha256,
        )
