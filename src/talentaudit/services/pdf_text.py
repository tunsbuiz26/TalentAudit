"""Text-only PDF decoding, invoked by the disposable parser process."""

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode
from talentaudit.schemas.pdf_worker import PDFParseLimits


class PDFTextParser:
    """Keep PDF decoding separate from process lifecycle and language detection."""

    def __init__(self, limits: PDFParseLimits) -> None:
        self._limits = limits

    def parse(self, content: bytes) -> tuple[str, int]:
        """Extract text from a PDF without rendering or executing embedded data."""

        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise DocumentParseError(DocumentParseErrorCode.PASSWORD_PROTECTED_PDF)
            page_count = len(reader.pages)
            if page_count > self._limits.max_pages:
                raise DocumentParseError(DocumentParseErrorCode.PAGE_LIMIT_EXCEEDED)

            page_texts: list[str] = []
            extracted_char_count = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
                extracted_char_count += len(page_text)
                if len(page_texts) > 1:
                    extracted_char_count += 1
                if extracted_char_count > self._limits.max_characters:
                    raise DocumentParseError(DocumentParseErrorCode.TEXT_LIMIT_EXCEEDED)
            text = "\n".join(page_texts)
        except DocumentParseError:
            raise
        except PdfReadError:
            raise DocumentParseError(DocumentParseErrorCode.MALFORMED_PDF) from None
        except Exception:
            raise DocumentParseError(DocumentParseErrorCode.PARSER_ERROR) from None

        if not text.strip():
            raise DocumentParseError(DocumentParseErrorCode.EMPTY_TEXT)
        return text, page_count
