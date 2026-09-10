"""Tests for document boundary DTOs and validation exceptions."""

import pytest
from pydantic import ValidationError

from talentaudit.domain.exceptions import (
    DocumentValidationError,
    DocumentValidationErrorCode,
)
from talentaudit.schemas.document import (
    DocumentMetadata,
    DocumentUpload,
    ValidatedDocument,
)

SHA256 = "a" * 64


def test_document_contracts_keep_raw_bytes_out_of_serialized_results() -> None:
    upload = DocumentUpload(
        filename="synthetic-cv.pdf",
        declared_mime_type="application/pdf",
        content=b"%PDF-synthetic",
    )
    validated = ValidatedDocument(
        document_id="document-001",
        mime_type="application/pdf",
        size_bytes=len(upload.content),
        sha256=SHA256,
        content=upload.content,
    )
    metadata = DocumentMetadata(
        document_id=validated.document_id,
        storage_key="documents/document-001.pdf",
        mime_type=validated.mime_type,
        size_bytes=validated.size_bytes,
        sha256=validated.sha256,
    )

    assert upload.content == b"%PDF-synthetic"
    assert "content" not in validated.model_dump()
    assert metadata.model_dump() == {
        "parser_status": "PENDING",
        "document_language": None,
        "page_count": None,
        "parse_error_code": None,
        "document_id": "document-001",
        "storage_key": "documents/document-001.pdf",
        "mime_type": "application/pdf",
        "size_bytes": len(upload.content),
        "sha256": SHA256,
    }


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (DocumentUpload, {"filename": "empty.txt", "content": b""}),
        (
            ValidatedDocument,
            {
                "document_id": "document-001",
                "mime_type": "text/plain",
                "size_bytes": 1,
                "sha256": "not-a-hash",
                "content": b"x",
            },
        ),
        (
            DocumentMetadata,
            {
                "document_id": "document-001",
                "storage_key": "../outside.txt",
                "mime_type": "text/plain",
                "size_bytes": 1,
                "sha256": SHA256,
            },
        ),
    ],
)
def test_document_contracts_reject_invalid_boundary_data(
    model: type[DocumentUpload | ValidatedDocument | DocumentMetadata],
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_document_validation_error_exposes_only_a_safe_error_contract() -> None:
    error = DocumentValidationError(DocumentValidationErrorCode.INVALID_MAGIC_BYTES)

    assert error.code is DocumentValidationErrorCode.INVALID_MAGIC_BYTES
    assert error.public_message == (
        "The uploaded document content is not a supported file type."
    )
    assert str(error) == error.public_message
