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


class DocumentParseErrorCode(StrEnum):
    """Stable error codes emitted while parsing validated document bytes."""

    UNSUPPORTED_DOCUMENT_TYPE = "UNSUPPORTED_DOCUMENT_TYPE"
    INVALID_TEXT_ENCODING = "INVALID_TEXT_ENCODING"
    EMPTY_TEXT = "EMPTY_TEXT"
    TEXT_LIMIT_EXCEEDED = "TEXT_LIMIT_EXCEEDED"
    MALFORMED_PDF = "MALFORMED_PDF"
    PASSWORD_PROTECTED_PDF = "PASSWORD_PROTECTED_PDF"
    PAGE_LIMIT_EXCEEDED = "PAGE_LIMIT_EXCEEDED"
    HASH_MISMATCH = "HASH_MISMATCH"
    PARSER_ERROR = "PARSER_ERROR"
    PARSE_TIMEOUT = "PARSE_TIMEOUT"


_DOCUMENT_PARSE_MESSAGES: dict[DocumentParseErrorCode, str] = {
    DocumentParseErrorCode.UNSUPPORTED_DOCUMENT_TYPE: (
        "The document type is not supported by this parser."
    ),
    DocumentParseErrorCode.INVALID_TEXT_ENCODING: (
        "The document text is not valid UTF-8."
    ),
    DocumentParseErrorCode.EMPTY_TEXT: "The document does not contain text.",
    DocumentParseErrorCode.TEXT_LIMIT_EXCEEDED: (
        "The extracted document text exceeds the configured limit."
    ),
    DocumentParseErrorCode.MALFORMED_PDF: "The PDF document could not be parsed.",
    DocumentParseErrorCode.PASSWORD_PROTECTED_PDF: (
        "The PDF document is password protected."
    ),
    DocumentParseErrorCode.PAGE_LIMIT_EXCEEDED: (
        "The PDF document exceeds the configured page limit."
    ),
    DocumentParseErrorCode.HASH_MISMATCH: "The document integrity check failed.",
    DocumentParseErrorCode.PARSER_ERROR: "The document parser failed.",
    DocumentParseErrorCode.PARSE_TIMEOUT: "The document parser timed out.",
}


class DocumentParseError(ValueError):
    """Raised when validated document bytes cannot produce usable text."""

    def __init__(self, code: DocumentParseErrorCode) -> None:
        self.code = code
        self.public_message = _DOCUMENT_PARSE_MESSAGES[code]
        super().__init__(self.public_message)
