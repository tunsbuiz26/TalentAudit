"""Private subprocess entrypoint. Stdout is reserved for the typed result."""

import sys
from base64 import b64decode

from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode
from talentaudit.schemas.pdf_worker import PDFWorkerRequest, PDFWorkerResult
from talentaudit.services.pdf_text import PDFTextParser


def main() -> None:
    """Run the bounded text-only parser; never expose unexpected error details."""

    try:
        request = PDFWorkerRequest.model_validate_json(sys.stdin.buffer.read())
        text, pages = PDFTextParser(request).parse(
            b64decode(request.content_base64, validate=True)
        )
        result = PDFWorkerResult(text=text, page_count=pages)
    except DocumentParseError as error:
        result = PDFWorkerResult(error=error.code)
    except Exception:
        result = PDFWorkerResult(error=DocumentParseErrorCode.PARSER_ERROR)
    sys.stdout.buffer.write(result.model_dump_json().encode("utf-8"))


if __name__ == "__main__":
    main()
