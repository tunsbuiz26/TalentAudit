"""Deterministic parsing for validated TXT and text-based PDF bytes."""

from hashlib import sha256

from talentaudit.adapters.parsing.pdf_process import extract_pdf_in_worker, pdf_request
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
        """Give potentially expensive PDF decoding a disposable process."""

        request = pdf_request(
            content,
            self._settings.max_pdf_pages,
            self._settings.max_extracted_text_chars,
        )
        return extract_pdf_in_worker(
            request, self._settings.document_parse_timeout_seconds
        )

    @staticmethod
    def _verify_hash(document: ValidatedDocument) -> None:
        """Ensure parser provenance still matches the validated bytes."""

        if sha256(document.content).hexdigest() != document.sha256:
            raise DocumentParseError(DocumentParseErrorCode.HASH_MISMATCH)
