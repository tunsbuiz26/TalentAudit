"""Deterministic provenance validation; this does not prove semantic correctness."""

import re

from talentaudit.domain.extraction_errors import EvidenceValidationFailure
from talentaudit.domain.policies.normalization import normalize_skill
from talentaudit.schemas.document import ParsedDocument
from talentaudit.schemas.evidence import EvidenceRef


def validate_evidence(references: list[EvidenceRef], document: ParsedDocument) -> None:
    """Require at least one exact, in-bounds source quote for each known claim."""

    if not references:
        raise EvidenceValidationFailure()
    for reference in references:
        if (
            reference.document_id != document.document_id
            or not 0 <= reference.start < reference.end <= len(document.text)
            or document.text[reference.start : reference.end] != reference.text
        ):
            raise EvidenceValidationFailure()


def validate_skill_evidence(skill: str, references: list[EvidenceRef]) -> None:
    """Conservatively require the named skill in at least one verified quote.

    No alias inference: ambiguous aliases go to review until taxonomy exists.
    This lexical guard does not resolve negation or prove a duration claim.
    """

    pattern = r"(?<!\w)" + re.escape(normalize_skill(skill)) + r"(?!\w)"
    if not any(re.search(pattern, normalize_skill(ref.text)) for ref in references):
        raise EvidenceValidationFailure()
