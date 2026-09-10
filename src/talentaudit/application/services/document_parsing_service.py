"""Persist parser metadata without coupling text extraction to SQLAlchemy."""

from talentaudit.domain.exceptions import DocumentParseError
from talentaudit.ports.repositories import DocumentRepository
from talentaudit.schemas.document import (
    DocumentParseMetadata,
    ParsedDocument,
    ValidatedDocument,
)
from talentaudit.services.document_parser import DocumentParser


class DocumentParsingService:
    """The parser owns decoding; this use case owns the persistence side effect."""

    def __init__(self, parser: DocumentParser, repository: DocumentRepository) -> None:
        self._parser = parser
        self._repository = repository

    def parse_and_persist(self, document: ValidatedDocument) -> ParsedDocument:
        """Do not expose success unless its metadata was saved successfully."""

        stored = self._repository.get(document.document_id)
        if stored is None:
            raise LookupError("document not found")
        if stored.sha256 != document.sha256 or stored.mime_type != document.mime_type:
            raise ValueError("document provenance mismatch")
        try:
            parsed = self._parser.parse(document)
        except DocumentParseError as error:
            self._repository.update_parse_metadata(
                DocumentParseMetadata(
                    document_id=document.document_id,
                    sha256=document.sha256,
                    parser_status="FAILED",
                    parse_error_code=error.code,
                )
            )
            raise
        self._repository.update_parse_metadata(
            DocumentParseMetadata(
                document_id=parsed.document_id,
                sha256=parsed.sha256,
                parser_status="PARSED",
                document_language=parsed.document_language,
                page_count=parsed.page_count,
            )
        )
        return parsed
