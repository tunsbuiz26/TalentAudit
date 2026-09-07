"""Deterministic validation at the untrusted document input boundary."""

from hashlib import sha256
from pathlib import PurePath
from uuid import uuid4

from talentaudit.config import Settings
from talentaudit.domain.exceptions import (
    DocumentValidationError,
    DocumentValidationErrorCode,
)
from talentaudit.schemas.document import (
    DocumentMimeType,
    DocumentUpload,
    ValidatedDocument,
)

_EXTENSION_MIME_TYPES: dict[str, DocumentMimeType] = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}


class DocumentValidator:
    """Verify filename, MIME declarations, magic bytes, and upload size.

    The validator contains no network or LLM calls. It must run before a
    document is handed to a parser or byte-storage adapter.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(self, upload: DocumentUpload) -> ValidatedDocument:
        """Return a typed trusted document or raise a stable validation error."""

        self._validate_filename(upload.filename)
        if not upload.content:
            raise DocumentValidationError(DocumentValidationErrorCode.EMPTY_FILE)
        if len(upload.content) > self._settings.max_upload_bytes:
            raise DocumentValidationError(DocumentValidationErrorCode.FILE_TOO_LARGE)

        expected_mime_type = self._mime_type_for_filename(upload.filename)
        self._ensure_allowed_mime_type(expected_mime_type)
        declared_mime_type = self._normalize_declared_mime_type(
            upload.declared_mime_type
        )
        self._ensure_allowed_mime_type(declared_mime_type)
        if declared_mime_type != expected_mime_type:
            raise DocumentValidationError(DocumentValidationErrorCode.MIME_MISMATCH)

        detected_mime_type = self._detect_mime_type(upload.content)
        if detected_mime_type is None:
            raise DocumentValidationError(
                DocumentValidationErrorCode.INVALID_MAGIC_BYTES
            )
        if detected_mime_type != expected_mime_type:
            raise DocumentValidationError(DocumentValidationErrorCode.MIME_MISMATCH)

        return ValidatedDocument(
            document_id=str(uuid4()),
            mime_type=detected_mime_type,
            size_bytes=len(upload.content),
            sha256=sha256(upload.content).hexdigest(),
            content=upload.content,
        )

    @staticmethod
    def _validate_filename(filename: str) -> None:
        if "/" in filename or "\\" in filename or PurePath(filename).name != filename:
            raise DocumentValidationError(DocumentValidationErrorCode.INVALID_FILENAME)

    @staticmethod
    def _mime_type_for_filename(filename: str) -> DocumentMimeType:
        mime_type = _EXTENSION_MIME_TYPES.get(PurePath(filename).suffix.lower())
        if mime_type is None:
            raise DocumentValidationError(
                DocumentValidationErrorCode.UNSUPPORTED_MEDIA_TYPE
            )
        return mime_type

    def _ensure_allowed_mime_type(self, mime_type: str) -> None:
        if mime_type not in self._settings.allowed_document_mime_types:
            raise DocumentValidationError(
                DocumentValidationErrorCode.UNSUPPORTED_MEDIA_TYPE
            )

    @staticmethod
    def _normalize_declared_mime_type(
        declared_mime_type: str | None,
    ) -> str:
        if declared_mime_type is None:
            raise DocumentValidationError(
                DocumentValidationErrorCode.UNSUPPORTED_MEDIA_TYPE
            )
        return declared_mime_type.strip().lower()

    @staticmethod
    def _detect_mime_type(content: bytes) -> DocumentMimeType | None:
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        try:
            decoded_content = content.decode("utf-8")
        except UnicodeDecodeError:
            return None
        if "\x00" in decoded_content:
            return None
        if any(
            ord(character) < 32 and character not in {"\n", "\r", "\t"}
            for character in decoded_content
        ):
            return None
        return "text/plain"
