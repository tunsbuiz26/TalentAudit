"""Typed contracts for untrusted documents and their safe metadata."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from talentaudit.domain.exceptions import DocumentParseErrorCode

DocumentMimeType = Literal["application/pdf", "text/plain"]
DocumentLanguage = Literal["vi", "en", "mixed"]


class DocumentUpload(BaseModel):
    """Untrusted file data received at the application boundary.

    The validator service will inspect filename, MIME information, magic bytes,
    and byte size. This model does not make the input trusted by itself.
    """

    filename: str = Field(min_length=1, max_length=255)
    declared_mime_type: str | None = Field(default=None, max_length=100)
    content: bytes = Field(min_length=1, repr=False, exclude=True)


class ValidatedDocument(BaseModel):
    """Document bytes that have passed the deterministic validation boundary."""

    document_id: str = Field(min_length=1, max_length=100)
    mime_type: DocumentMimeType
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content: bytes = Field(min_length=1, repr=False, exclude=True)


class ParsedDocument(BaseModel):
    """Text extracted from a validated document with stable provenance."""

    document_id: str = Field(min_length=1, max_length=100)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text: str = Field(min_length=1, repr=False)
    # Parser enriches successful results before returning them to callers.
    document_language: DocumentLanguage
    page_count: int | None = Field(default=None, ge=1)


class ParseState(BaseModel):
    """Only a completed parse has language/pages; failed parses carry a safe code."""

    parser_status: Literal["PENDING", "PARSED", "FAILED"] = "PENDING"
    document_language: DocumentLanguage | None = None
    page_count: int | None = Field(default=None, ge=1)
    parse_error_code: DocumentParseErrorCode | None = None

    @model_validator(mode="after")
    def validate_state(self) -> "ParseState":
        if self.parser_status == "PARSED":
            if self.document_language is None or self.parse_error_code is not None:
                raise ValueError("parsed metadata requires language and no error")
        else:
            if self.document_language is not None or self.page_count is not None:
                raise ValueError("unparsed document cannot have language or pages")
            if (self.parser_status == "FAILED") != (self.parse_error_code is not None):
                raise ValueError("only failed parse requires an error code")
        return self


class DocumentParseMetadata(ParseState):
    """Hash-bound update that cannot transport raw document text or bytes."""

    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1, max_length=100)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DocumentMetadata(ParseState):
    """Persistable document metadata; it deliberately contains no raw bytes."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(min_length=1, max_length=100)
    storage_key: str = Field(min_length=1, max_length=500)
    mime_type: DocumentMimeType
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("storage_key")
    @classmethod
    def validate_storage_key(cls, value: str) -> str:
        """Require a relative POSIX key without traversal segments."""

        path = PurePosixPath(value)
        if (
            "\\" in value
            or path.is_absolute()
            or any(part in {".", ".."} for part in path.parts)
        ):
            raise ValueError("storage key must be a safe relative path")
        return value
