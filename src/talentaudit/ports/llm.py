"""The application depends on this port, never a provider SDK."""

from typing import Protocol

from pydantic import BaseModel

from talentaudit.schemas.llm import PromptTemplate, UntrustedDocument


class LLMClient(Protocol):
    """Return a validated model or a safe, typed LLM failure."""

    def generate_structured[T: BaseModel](
        self,
        *,
        prompt: PromptTemplate,
        document: UntrustedDocument,
        output_model: type[T],
    ) -> T: ...
