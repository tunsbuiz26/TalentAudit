"""Deterministic parsing for validated TXT and text-based PDF bytes."""

from hashlib import sha256
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from talentaudit.config import Settings
from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode
from talentaudit.schemas.document import ParsedDocument, ValidatedDocument
from talentaudit.services.language_detector import LanguageDetector


class DocumentParser:
    """Parse document text without LLM, network, or filesystem side effects.

    PDF support is text-only. The parser does not execute links, macros,
    JavaScript, or embedded content.
    """

    def __init__(
        self, settings: Settings, detector: LanguageDetector | None = None
    ) -> None:
        self._settings = settings
        self._detector = detector or LanguageDetector()

    def parse(self, document: ValidatedDocument) -> ParsedDocument:
        """Extract stable text from one validated TXT or text-based PDF."""

        self._verify_hash(document)
        if document.mime_type == "text/plain":
            text, page_count = self._parse_text(document.content)
        elif document.mime_type == "application/pdf":
            text, page_count = self._parse_pdf(document.content)
        else:
            raise DocumentParseError(DocumentParseErrorCode.UNSUPPORTED_DOCUMENT_TYPE)

        return ParsedDocument(
            document_id=document.document_id,
            sha256=document.sha256,
            text=text,
            page_count=page_count,
            document_language=self._detector.detect(text),
        )

    def _parse_text(self, content: bytes) -> tuple[str, None]:
        """Decode UTF-8 text without normalizing its source content."""

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DocumentParseError(
                DocumentParseErrorCode.INVALID_TEXT_ENCODING
            ) from error
        if not text.strip():
            raise DocumentParseError(DocumentParseErrorCode.EMPTY_TEXT)
        if len(text) > self._settings.max_extracted_text_chars:
            raise DocumentParseError(DocumentParseErrorCode.TEXT_LIMIT_EXCEEDED)
        return text, None

    def _parse_pdf(self, content: bytes) -> tuple[str, int]:
        """Extract text from a PDF without rendering or executing embedded data."""

        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise DocumentParseError(DocumentParseErrorCode.PASSWORD_PROTECTED_PDF)
            page_count = len(reader.pages)
            if page_count > self._settings.max_pdf_pages:
                raise DocumentParseError(DocumentParseErrorCode.PAGE_LIMIT_EXCEEDED)

            page_texts: list[str] = []
            extracted_char_count = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
                extracted_char_count += len(page_text)
                if len(page_texts) > 1:
                    extracted_char_count += 1
                if extracted_char_count > self._settings.max_extracted_text_chars:
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

    @staticmethod
    def _verify_hash(document: ValidatedDocument) -> None:
        """Ensure parser provenance still matches the validated bytes."""

        if sha256(document.content).hexdigest() != document.sha256:
            raise DocumentParseError(DocumentParseErrorCode.HASH_MISMATCH)
