"""Provider-independent failures; never carry raw document or provider output."""

from enum import StrEnum


class ExtractionFailureCode(StrEnum):
    SCHEMA_INVALID = "SCHEMA_INVALID"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    UNKNOWN = "UNKNOWN"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    REFUSED = "REFUSED"
    INCOMPLETE = "INCOMPLETE"


class LLMFailure(Exception):
    """Transport/refusal failure, not eligible for schema retry."""

    def __init__(self, code: ExtractionFailureCode) -> None:
        self.code = code
        super().__init__(code.value)


class LLMSchemaFailure(LLMFailure):
    """Output did not conform to the requested model."""

    def __init__(self) -> None:
        super().__init__(ExtractionFailureCode.SCHEMA_INVALID)


class EvidenceValidationFailure(Exception):
    """A claim cannot be grounded in the supplied document."""

    def __init__(self) -> None:
        super().__init__(ExtractionFailureCode.EVIDENCE_INVALID.value)
