"""Tests for deterministic document trust-boundary validation."""

from hashlib import sha256

import pytest

from talentaudit.config import Settings
from talentaudit.domain.exceptions import (
    DocumentValidationError,
    DocumentValidationErrorCode,
)
from talentaudit.schemas.document import DocumentUpload
from talentaudit.services.document_validator import DocumentValidator


@pytest.fixture
def validator() -> DocumentValidator:
    return DocumentValidator(Settings(environment="test", max_upload_bytes=64))


@pytest.mark.parametrize(
    ("upload", "expected_mime_type"),
    [
        (
            DocumentUpload(
                filename="synthetic-cv.pdf",
                declared_mime_type="application/pdf",
                content=b"%PDF-1.7\nsynthetic document",
            ),
            "application/pdf",
        ),
        (
            DocumentUpload(
                filename="synthetic-cv.txt",
                declared_mime_type="text/plain",
                content=b"Synthetic candidate profile for testing only.",
            ),
            "text/plain",
        ),
    ],
)
def test_validator_accepts_supported_pdf_and_text_documents(
    validator: DocumentValidator,
    upload: DocumentUpload,
    expected_mime_type: str,
) -> None:
    validated = validator.validate(upload)

    assert validated.mime_type == expected_mime_type
    assert validated.size_bytes == len(upload.content)
    assert validated.sha256 == sha256(upload.content).hexdigest()
    assert validated.content == upload.content


@pytest.mark.parametrize(
    ("upload", "expected_code"),
    [
        (
            DocumentUpload(
                filename="synthetic-cv.pdf",
                declared_mime_type="application/pdf",
                content=b"This is text, not a PDF.",
            ),
            DocumentValidationErrorCode.MIME_MISMATCH,
        ),
        (
            DocumentUpload(
                filename="synthetic-cv.txt",
                declared_mime_type="text/plain",
                content=b"%PDF-1.7\nsynthetic document",
            ),
            DocumentValidationErrorCode.MIME_MISMATCH,
        ),
        (
            DocumentUpload(
                filename="synthetic-cv.pdf",
                declared_mime_type="text/plain",
                content=b"%PDF-1.7\nsynthetic document",
            ),
            DocumentValidationErrorCode.MIME_MISMATCH,
        ),
    ],
)
def test_validator_rejects_extension_mime_or_magic_mismatches(
    validator: DocumentValidator,
    upload: DocumentUpload,
    expected_code: DocumentValidationErrorCode,
) -> None:
    with pytest.raises(DocumentValidationError) as error:
        validator.validate(upload)

    assert error.value.code is expected_code


def test_validator_rejects_an_oversized_document(validator: DocumentValidator) -> None:
    upload = DocumentUpload(
        filename="synthetic-cv.txt",
        declared_mime_type="text/plain",
        content=b"x" * 65,
    )

    with pytest.raises(DocumentValidationError) as error:
        validator.validate(upload)

    assert error.value.code is DocumentValidationErrorCode.FILE_TOO_LARGE


@pytest.mark.parametrize("filename", ["../synthetic-cv.txt", "folder\\cv.txt"])
def test_validator_rejects_filename_path_separators(
    validator: DocumentValidator,
    filename: str,
) -> None:
    upload = DocumentUpload(
        filename=filename,
        declared_mime_type="text/plain",
        content=b"Synthetic text.",
    )

    with pytest.raises(DocumentValidationError) as error:
        validator.validate(upload)

    assert error.value.code is DocumentValidationErrorCode.INVALID_FILENAME


def test_validator_rejects_binary_bytes_disguised_as_text(
    validator: DocumentValidator,
) -> None:
    upload = DocumentUpload(
        filename="synthetic-cv.txt",
        declared_mime_type="text/plain",
        content=b"\x00\xff\x01",
    )

    with pytest.raises(DocumentValidationError) as error:
        validator.validate(upload)

    assert error.value.code is DocumentValidationErrorCode.INVALID_MAGIC_BYTES
