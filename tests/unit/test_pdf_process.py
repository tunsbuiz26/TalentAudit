"""Timeout must stop the subprocess, not just stop waiting for a thread."""

import subprocess
import sys

import pytest

from talentaudit.adapters.parsing.pdf_process import run_worker
from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode


def test_hanging_worker_is_killed_and_reaped(monkeypatch: pytest.MonkeyPatch) -> None:
    children = []
    original = subprocess.Popen

    def record_child(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(subprocess, "Popen", record_child)
    with pytest.raises(DocumentParseError) as caught:
        run_worker([sys.executable, "-c", "import time; time.sleep(30)"], b"{}", 0.2)
    assert caught.value.code == DocumentParseErrorCode.PARSE_TIMEOUT
    assert len(children) == 1
    assert children[0].poll() is not None


def test_crashed_worker_returns_safe_failure() -> None:
    with pytest.raises(DocumentParseError) as caught:
        run_worker(
            [sys.executable, "-c", "raise RuntimeError('private-marker')"], b"{}", 5
        )
    assert caught.value.code == DocumentParseErrorCode.PARSER_ERROR
    assert "private-marker" not in str(caught.value)


def test_parser_uses_configured_deadline_without_forwarding_secrets(
    monkeypatch,
) -> None:
    import json

    from talentaudit.adapters.parsing import pdf_process
    from talentaudit.config import Settings
    from talentaudit.services.document_parser import DocumentParser

    def fake_run(command, request, timeout):
        assert timeout == 0.75
        assert set(json.loads(request)) == {
            "content_base64",
            "max_pages",
            "max_characters",
        }
        return b'{"text":"Python","page_count":1,"error":null}'

    monkeypatch.setattr(pdf_process, "run_worker", fake_run)
    settings = Settings(_env_file=None, document_parse_timeout_seconds=0.75)
    assert DocumentParser(settings)._parse_pdf(b"%PDF-synthetic") == ("Python", 1)
