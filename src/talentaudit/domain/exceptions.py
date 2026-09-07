"""Business exceptions that are safe to map to public error responses."""

from enum import StrEnum


class DocumentValidationErrorCode(StrEnum):
    """Stable error codes emitted by the document trust boundary."""

    EMPTY_FILE = "EMPTY_FILE"
    INVALID_FILENAME = "INVALID_FILENAME"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    MIME_MISMATCH = "MIME_MISMATCH"
    INVALID_MAGIC_BYTES = "INVALID_MAGIC_BYTES"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


_DOCUMENT_VALIDATION_MESSAGES: dict[DocumentValidationErrorCode, str] = {
    DocumentValidationErrorCode.EMPTY_FILE: "The uploaded document is empty.",
    DocumentValidationErrorCode.INVALID_FILENAME: "The uploaded filename is invalid.",
    DocumentValidationErrorCode.UNSUPPORTED_MEDIA_TYPE: (
        "The uploaded document type is not supported."
    ),
    DocumentValidationErrorCode.MIME_MISMATCH: (
        "The declared document type does not match its content."
    ),
    DocumentValidationErrorCode.INVALID_MAGIC_BYTES: (
        "The uploaded document content is not a supported file type."
    ),
    DocumentValidationErrorCode.FILE_TOO_LARGE: "The uploaded document is too large.",
}


class DocumentValidationError(ValueError):
    """Raised when untrusted document input fails a validation rule.

    The exception intentionally stores only a stable code and a generic public
    message. Callers must not attach raw bytes, filenames, or other PII to it.
    """

    def __init__(self, code: DocumentValidationErrorCode) -> None:
        self.code = code
        self.public_message = _DOCUMENT_VALIDATION_MESSAGES[code]
        super().__init__(self.public_message)
