"""Minimal subprocess protocol: no Settings object, credentials or filename."""

from pydantic import BaseModel, Field

from talentaudit.domain.exceptions import DocumentParseErrorCode


class PDFParseLimits(BaseModel):
    max_pages: int = Field(ge=1)
    max_characters: int = Field(ge=1)


class PDFWorkerRequest(PDFParseLimits):
    content_base64: str = Field(repr=False)


class PDFWorkerResult(BaseModel):
    text: str | None = Field(default=None, repr=False)
    page_count: int | None = Field(default=None, ge=1)
    error: DocumentParseErrorCode | None = None
