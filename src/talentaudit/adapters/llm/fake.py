"""Programmable offline adapter using the same Pydantic boundary as a provider."""

from collections import deque
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError

from talentaudit.domain.extraction_errors import LLMFailure, LLMSchemaFailure
from talentaudit.schemas.llm import PromptTemplate, UntrustedDocument


class FakeLLMClient:
    """Consume one JSON response or typed failure per request, without network."""

    def __init__(self, responses: Iterable[str | LLMFailure]) -> None:
        self._responses = deque(responses)
        # Record routing information, not document text or model output.
        self.calls: list[tuple[str, str, str]] = []

    def generate_structured[T: BaseModel](
        self,
        *,
        prompt: PromptTemplate,
        document: UntrustedDocument,
        output_model: type[T],
    ) -> T:
        """Validate scripted JSON; exhaustion is a test programming error."""

        self.calls.append((prompt.name, prompt.version, output_model.__name__))
        if not self._responses:
            raise AssertionError("FakeLLMClient response queue exhausted")
        response = self._responses.popleft()
        if isinstance(response, LLMFailure):
            raise response
        try:
            return output_model.model_validate_json(response)
        except ValidationError:
            raise LLMSchemaFailure() from None
