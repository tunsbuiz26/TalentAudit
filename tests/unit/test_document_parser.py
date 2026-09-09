"""Tests for the first Day 07 UTF-8 TXT parsing increment."""

from hashlib import sha256
from io import BytesIO

import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from talentaudit.config import Settings
from talentaudit.domain.exceptions import DocumentParseError, DocumentParseErrorCode
from talentaudit.schemas.document import ParsedDocument, ValidatedDocument
from talentaudit.services.document_parser import DocumentParser


def make_text_document(content: bytes) -> ValidatedDocument:
    """Create synthetic validated TXT input without any candidate PII."""

    return ValidatedDocument(
        document_id="document-001",
        mime_type="text/plain",
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        content=content,
    )


def make_pdf_document(page_texts: list[str]) -> ValidatedDocument:
    """Create a real text-based synthetic PDF entirely in memory."""

    buffer = BytesIO()
    canvas = Canvas(buffer)
    for page_text in page_texts:
        canvas.drawString(72, 720, page_text)
        canvas.showPage()
    canvas.save()
    content = buffer.getvalue()
    return ValidatedDocument(
        document_id="document-pdf-001",
        mime_type="application/pdf",
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        content=content,
    )


def test_parser_creates_parsed_document_for_valid_utf8_text() -> None:
    document = make_text_document(b"Synthetic profile: Python and SQL.")
    parser = DocumentParser(Settings(environment="test"))

    parsed = parser.parse(document)

    assert parsed.document_id == document.document_id
    assert parsed.sha256 == document.sha256
    assert parsed.text == "Synthetic profile: Python and SQL."
    assert parsed.page_count is None
    assert parsed.document_language == "en"


def test_parser_creates_parsed_document_for_text_based_pdf_with_page_count() -> None:
    document = make_pdf_document(["Synthetic page one.", "Synthetic page two."])
    parser = DocumentParser(Settings(environment="test"))

    parsed = parser.parse(document)

    assert parsed.document_id == document.document_id
    assert parsed.sha256 == document.sha256
    assert "Synthetic page one." in parsed.text
    assert "Synthetic page two." in parsed.text
    assert parsed.page_count == 2
    assert parsed.document_language == "en"


def test_parser_rejects_pdf_above_the_configured_page_limit() -> None:
    document = make_pdf_document(["Page one.", "Page two."])
    parser = DocumentParser(Settings(environment="test", max_pdf_pages=1))

    with pytest.raises(DocumentParseError) as error:
        parser.parse(document)

    assert error.value.code is DocumentParseErrorCode.PAGE_LIMIT_EXCEEDED


def test_parser_maps_malformed_pdf_to_a_typed_error() -> None:
    content = b"%PDF-this-is-not-a-valid-pdf"
    document = ValidatedDocument(
        document_id="document-bad-pdf",
        mime_type="application/pdf",
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        content=content,
    )
    parser = DocumentParser(Settings(environment="test"))

    with pytest.raises(DocumentParseError) as error:
        parser.parse(document)

    assert error.value.code is DocumentParseErrorCode.MALFORMED_PDF


def test_parser_rejects_empty_text() -> None:
    parser = DocumentParser(Settings(environment="test"))

    with pytest.raises(DocumentParseError) as error:
        parser.parse(make_text_document(b" \n\t"))

    assert error.value.code is DocumentParseErrorCode.EMPTY_TEXT


def test_parser_rejects_text_above_the_configured_character_limit() -> None:
    parser = DocumentParser(Settings(environment="test", max_extracted_text_chars=3))

    with pytest.raises(DocumentParseError) as error:
        parser.parse(make_text_document(b"four"))

    assert error.value.code is DocumentParseErrorCode.TEXT_LIMIT_EXCEEDED


def test_source_offsets_and_repeatability() -> None:
    text = "  Kỹ năng: Python\r\n\tDự án dữ liệu.  "
    document = make_text_document(text.encode("utf-8"))
    parser = DocumentParser(Settings(environment="test"))
    parsed = parser.parse(document)
    assert parsed == parser.parse(document)
    assert parsed.text == text
    start = text.index("Python")
    assert parsed.text[start : start + 6] == "Python"
    assert parsed.sha256 == sha256(document.content).hexdigest()
    assert parsed.document_id == document.document_id
    assert parsed.document_language == "vi"


def test_hash_mismatch_rejected() -> None:
    document = make_text_document(b"Skills: Python")
    document.sha256 = "0" * 64
    with pytest.raises(DocumentParseError) as error:
        DocumentParser(Settings(environment="test")).parse(document)
    assert error.value.code is DocumentParseErrorCode.HASH_MISMATCH


def test_pdf_blank_and_encrypted() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    for encrypted, expected in [
        (False, DocumentParseErrorCode.EMPTY_TEXT),
        (True, DocumentParseErrorCode.PASSWORD_PROTECTED_PDF),
    ]:
        if encrypted:
            writer.encrypt("synthetic-test-only")
        stream = BytesIO()
        writer.write(stream)
        document = make_text_document(stream.getvalue())
        document.mime_type = "application/pdf"
        with pytest.raises(DocumentParseError) as error:
            DocumentParser(Settings(environment="test")).parse(document)
        assert error.value.code is expected


def test_unexpected_parser_error_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("synthetic internal details")

    monkeypatch.setattr("talentaudit.services.document_parser.PdfReader", fail)
    with pytest.raises(DocumentParseError) as error:
        DocumentParser(Settings(environment="test")).parse(make_pdf_document(["Text"]))
    assert error.value.code is DocumentParseErrorCode.PARSER_ERROR
    assert "internal details" not in str(error.value)
    assert error.value.__suppress_context__


def test_pdf_limits_include_page_separator_and_preserve_text() -> None:
    document = make_pdf_document(["Skills: Python", "Experience: SQL"])
    parser = DocumentParser(Settings(environment="test", max_pdf_pages=2))
    parsed = parser.parse(document)
    assert parsed.text == "Skills: Python\n\nExperience: SQL\n"
    assert parsed == parser.parse(document)
    for limit, succeeds in [(len(parsed.text), True), (len(parsed.text) - 1, False)]:
        limited = DocumentParser(
            Settings(environment="test", max_extracted_text_chars=limit)
        )
        if succeeds:
            assert limited.parse(document).text == parsed.text
        else:
            with pytest.raises(DocumentParseError) as error:
                limited.parse(document)
            assert error.value.code is DocumentParseErrorCode.TEXT_LIMIT_EXCEEDED


def test_text_limit_counts_unicode_characters_not_bytes() -> None:
    document = make_text_document("Kỹ năng".encode())
    assert (
        DocumentParser(Settings(environment="test", max_extracted_text_chars=7))
        .parse(document)
        .text
        == "Kỹ năng"
    )


def test_invalid_encoding_is_typed() -> None:
    with pytest.raises(DocumentParseError) as error:
        DocumentParser(Settings(environment="test")).parse(make_text_document(b"\xff"))
    assert error.value.code is DocumentParseErrorCode.INVALID_TEXT_ENCODING


def test_parsed_schema_roundtrip_and_invalid_metadata() -> None:
    parsed = DocumentParser(Settings(environment="test")).parse(
        make_text_document(b"Skills")
    )
    assert ParsedDocument.model_validate_json(parsed.model_dump_json()) == parsed
    assert "Skills" not in repr(parsed)
    for field, value in [
        ("page_count", 0),
        ("document_language", "fr"),
        ("sha256", "bad"),
    ]:
        with pytest.raises(ValidationError):
            ParsedDocument.model_validate({**parsed.model_dump(), field: value})
