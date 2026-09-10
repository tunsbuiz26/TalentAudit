"""The only application module that knows about the OpenAI SDK."""

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from talentaudit.config import Settings
from talentaudit.domain.extraction_errors import (
    ExtractionFailureCode,
    LLMFailure,
    LLMSchemaFailure,
)
from talentaudit.schemas.llm import PromptTemplate, UntrustedDocument


class _ResponseStatus(BaseModel):
    """Inspect completion before SDK attempts to parse potentially truncated JSON."""

    status: str


class OpenAILLMClient:
    """Lazy, explicitly configured live client; app startup needs no credentials."""

    def __init__(self, settings: Settings) -> None:
        key = settings.openai_api_key
        if key is None or not key.get_secret_value().strip():
            raise ValueError("OpenAI adapter requires configured API key")
        if not settings.openai_model.strip():
            raise ValueError("OpenAI adapter requires configured model")
        self._settings = settings.model_copy(deep=True)

    def generate_structured[T: BaseModel](
        self,
        *,
        prompt: PromptTemplate,
        document: UntrustedDocument,
        output_model: type[T],
    ) -> T:
        """Parse structured output; SDK retries disabled so service owns the budget."""

        settings = self._settings
        assert settings.openai_api_key is not None
        try:
            # Context manager closes HTTP resources on success and on failure.
            with OpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                max_retries=0,
                timeout=settings.openai_timeout_seconds,
            ) as client:
                raw = client.responses.with_raw_response.parse(
                    model=settings.openai_model,
                    temperature=settings.openai_temperature,
                    max_output_tokens=settings.openai_max_output_tokens,
                    store=False,
                    instructions=prompt.instructions,
                    metadata={
                        "prompt_name": prompt.name,
                        "prompt_version": prompt.version,
                    },
                    input=[{"role": "user", "content": document.delimited_data()}],
                    text_format=output_model,
                )
                envelope = _ResponseStatus.model_validate_json(raw.text)
                if envelope.status != "completed":
                    raise LLMFailure(ExtractionFailureCode.INCOMPLETE)
                response = raw.parse()
                for item in response.output:
                    if item.type == "message" and any(
                        part.type == "refusal" for part in item.content
                    ):
                        raise LLMFailure(ExtractionFailureCode.REFUSED)
                if response.output_parsed is None:
                    raise LLMSchemaFailure()
                return output_model.model_validate(response.output_parsed.model_dump())
        except ValidationError:
            raise LLMSchemaFailure() from None
        except OpenAIError:
            raise LLMFailure(ExtractionFailureCode.PROVIDER_UNAVAILABLE) from None
