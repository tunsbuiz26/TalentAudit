"""Run a disposable PDF worker with a deadline and no secret environment."""

import os
import subprocess
import sys
from base64 import b64encode

from pydantic import ValidationError

from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode
from talentaudit.schemas.pdf_worker import PDFWorkerRequest, PDFWorkerResult


def run_worker(command: list[str], request: bytes, timeout: float) -> bytes:
    """subprocess.run kills and waits for its child when communicate times out."""

    worker_environment = {
        name: value
        for name, value in os.environ.items()
        if name.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}
    }
    try:
        completed = subprocess.run(
            command,
            input=request,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=True,
            env=worker_environment,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        raise DocumentParseError(DocumentParseErrorCode.PARSE_TIMEOUT) from None
    except (OSError, subprocess.CalledProcessError):
        raise DocumentParseError(DocumentParseErrorCode.PARSER_ERROR) from None
    return completed.stdout


def extract_pdf_in_worker(request: PDFWorkerRequest, timeout: float) -> tuple[str, int]:
    """Read only typed text/error from a fresh worker, never stderr diagnostics."""

    output = run_worker(
        [sys.executable, "-m", "talentaudit.adapters.parsing.pdf_worker"],
        request.model_dump_json().encode("utf-8"),
        timeout,
    )
    try:
        result = PDFWorkerResult.model_validate_json(output)
    except ValidationError:
        raise DocumentParseError(DocumentParseErrorCode.PARSER_ERROR) from None
    if result.error is not None:
        raise DocumentParseError(result.error)
    if result.text is None or result.page_count is None:
        raise DocumentParseError(DocumentParseErrorCode.PARSER_ERROR)
    return result.text, result.page_count


def pdf_request(
    content: bytes, max_pages: int, max_characters: int
) -> PDFWorkerRequest:
    """Encode bytes for JSON IPC; no raw content is put on the command line."""

    return PDFWorkerRequest(
        content_base64=b64encode(content).decode("ascii"),
        max_pages=max_pages,
        max_characters=max_characters,
    )
