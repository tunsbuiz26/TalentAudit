"""Provider-independent request contracts; document text is never instructions."""

import json

from pydantic import BaseModel, ConfigDict, Field


class PromptTemplate(BaseModel):
    """Trusted, versioned instructions loaded from a packaged resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    instructions: str = Field(min_length=1)


class UntrustedDocument(BaseModel):
    """Only the minimum document data needed by the provider."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    document_id: str = Field(min_length=1)
    text: str = Field(min_length=1, repr=False)

    def delimited_data(self) -> str:
        """Escape delimiter characters without changing the decoded source text."""

        payload = json.dumps(self.model_dump(), ensure_ascii=True)
        payload = payload.replace("<", r"\u003c").replace(">", r"\u003e")
        return "<untrusted_document>\n" + payload + "\n</untrusted_document>"
