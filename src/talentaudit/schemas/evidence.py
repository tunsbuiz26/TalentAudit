"""Evidence reference schema."""

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator


class EvidenceRef(BaseModel):
    """A source span that can support a later recommendation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    document_id: str = Field(min_length=1, max_length=100)
    section: str = Field(min_length=1, max_length=100)
    start: NonNegativeInt
    end: NonNegativeInt
    text: str = Field(min_length=1, max_length=2_000)

    @model_validator(mode="after")
    def validate_span(self) -> "EvidenceRef":
        """Require a non-empty, forward source span."""

        if self.end <= self.start:
            raise ValueError("evidence end must be greater than start")
        return self
