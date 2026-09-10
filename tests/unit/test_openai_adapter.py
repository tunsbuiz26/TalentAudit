"""Exercise the real SDK over an in-memory HTTP transport, never the network."""

import json
import secrets
import socket
from contextlib import contextmanager

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from talentaudit.adapters.llm import openai as adapter_module
from talentaudit.config import Settings
from talentaudit.domain.extraction_errors import ExtractionFailureCode, LLMFailure
from talentaudit.prompts import load_profile_prompt
from talentaudit.schemas.extraction import ExtractedProfile
from talentaudit.schemas.llm import UntrustedDocument


@pytest.fixture(autouse=True)
def block_network(monkeypatch) -> None:
    def deny(*args, **kwargs):
        raise AssertionError("Network is forbidden: use the in-memory transport")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)


def settings() -> Settings:
    # Ephemeral random placeholder generated at runtime; no credential in fixtures.
    return Settings(
        _env_file=None,
        openai_api_key=SecretStr(secrets.token_urlsafe(24)),
        openai_model="synthetic-model",
        openai_temperature=0.25,
        openai_max_output_tokens=1234,
        openai_timeout_seconds=7,
    )


def response_body(kind: str) -> dict:
    content = [{"type": "output_text", "text": '{"claims": []}', "annotations": []}]
    if kind == "invalid":
        content[0]["text"] = '{"claims": "wrong type"}'
    elif kind == "refusal":
        content = [{"type": "refusal", "refusal": "Synthetic refusal"}]
    elif kind == "incomplete":
        content[0]["text"] = '{"claims": ['
    return {
        "id": "resp_synthetic",
        "object": "response",
        "created_at": 0,
        "model": "synthetic-model",
        "status": ("incomplete" if kind == "incomplete" else "completed"),
        "output": [
            {
                "id": "msg_synthetic",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": content,
            }
        ]
        if kind != "empty"
        else [],
        "parallel_tool_calls": False,
        "tool_choice": "auto",
        "tools": [],
    }


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("success", None),
        ("invalid", ExtractionFailureCode.SCHEMA_INVALID),
        ("empty", ExtractionFailureCode.SCHEMA_INVALID),
        ("refusal", ExtractionFailureCode.REFUSED),
        ("incomplete", ExtractionFailureCode.INCOMPLETE),
        ("server", ExtractionFailureCode.PROVIDER_UNAVAILABLE),
        ("timeout", ExtractionFailureCode.PROVIDER_UNAVAILABLE),
    ],
)
def test_sdk_request_and_failure_contract(monkeypatch, kind, expected) -> None:
    configured = settings()
    real_factory = adapter_module.OpenAI
    calls = []
    clients = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        if kind == "timeout":
            raise httpx.ReadTimeout("SYNTHETIC-PRIVATE-MARKER", request=request)
        if kind == "server":
            return httpx.Response(
                500,
                json={
                    "error": {
                        "message": "SYNTHETIC-PRIVATE-MARKER",
                        "type": "server_error",
                    }
                },
            )
        return httpx.Response(200, json=response_body(kind))

    @contextmanager
    def factory(**kwargs):
        assert kwargs["api_key"] == configured.openai_api_key.get_secret_value()
        assert kwargs["max_retries"] == 0
        assert kwargs["timeout"] == 7
        transport = httpx.Client(transport=httpx.MockTransport(handle))
        clients.append(transport)
        with real_factory(**kwargs, http_client=transport) as client:
            yield client

    monkeypatch.setattr(adapter_module, "OpenAI", factory)
    adapter = adapter_module.OpenAILLMClient(configured)
    prompt = load_profile_prompt()
    data = UntrustedDocument(document_id="synthetic", text="Python")
    if expected is None:
        result = adapter.generate_structured(
            prompt=prompt, document=data, output_model=ExtractedProfile
        )
        assert isinstance(result, ExtractedProfile)
    else:
        with pytest.raises(LLMFailure) as caught:
            adapter.generate_structured(
                prompt=prompt, document=data, output_model=ExtractedProfile
            )
        assert caught.value.code == expected
        assert "SYNTHETIC-PRIVATE-MARKER" not in str(caught.value)
    assert len(calls) == 1
    assert all(client.is_closed for client in clients)
    request = calls[0]
    assert request["model"] == configured.openai_model
    assert request["temperature"] == 0.25
    assert request["max_output_tokens"] == 1234
    assert request["store"] is False
    assert request["instructions"] == prompt.instructions
    assert request["input"] == [{"role": "user", "content": data.delimited_data()}]
    assert request["metadata"] == {"prompt_name": prompt.name, "prompt_version": "v1"}
    assert request["text"]["format"]["strict"] is True
    schema = request["text"]["format"]["schema"]
    assert schema["additionalProperties"] is False
    for definition in schema["$defs"].values():
        assert definition["additionalProperties"] is False
        assert set(definition["required"]) == set(definition["properties"])
    assert "tools" not in request


def test_live_adapter_requires_explicit_key_and_model() -> None:
    with pytest.raises(ValueError, match="API key"):
        adapter_module.OpenAILLMClient(Settings(_env_file=None, openai_api_key=None))
    configured = settings()
    configured.openai_model = ""
    with pytest.raises(ValueError, match="model"):
        adapter_module.OpenAILLMClient(configured)


def test_openai_settings_environment_and_secret_exclusion(monkeypatch) -> None:
    ephemeral = secrets.token_urlsafe(24)
    monkeypatch.setenv("TALENTAUDIT_OPENAI_API_KEY", ephemeral)
    monkeypatch.setenv("TALENTAUDIT_OPENAI_MODEL", "synthetic-model-env")
    monkeypatch.setenv("TALENTAUDIT_OPENAI_TEMPERATURE", "0.5")
    monkeypatch.setenv("TALENTAUDIT_OPENAI_MAX_OUTPUT_TOKENS", "100")
    monkeypatch.setenv("TALENTAUDIT_OPENAI_TIMEOUT_SECONDS", "9")
    configured = Settings(_env_file=None)
    assert configured.openai_api_key.get_secret_value() == ephemeral
    assert configured.openai_model == "synthetic-model-env"
    assert configured.openai_temperature == 0.5
    assert configured.openai_max_output_tokens == 100
    assert configured.openai_timeout_seconds == 9
    assert ephemeral not in repr(configured)
    assert "openai_api_key" not in configured.model_dump()
    assert ephemeral not in configured.model_dump_json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("openai_temperature", -1),
        ("openai_temperature", 3),
        ("openai_temperature", float("nan")),
        ("openai_max_output_tokens", 0),
        ("openai_timeout_seconds", 0),
    ],
)
def test_invalid_provider_limits_rejected(field, value) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})
