"""Integration tests for document metadata persistence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from talentaudit.adapters.db.base import Base
from talentaudit.adapters.db.document_repository import SqlAlchemyDocumentRepository
from talentaudit.adapters.db.models import DocumentModel
from talentaudit.schemas.document import DocumentMetadata


def test_document_repository_persists_metadata_without_raw_bytes() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    metadata = DocumentMetadata(
        document_id="document-001",
        storage_key="documents/generated-key.pdf",
        mime_type="application/pdf",
        size_bytes=42,
        sha256="a" * 64,
    )

    with session_factory() as session:
        repository = SqlAlchemyDocumentRepository(session)
        created = repository.create(metadata)
        fetched = repository.get(metadata.document_id)

    engine.dispose()

    assert created == metadata
    assert fetched == metadata
    assert "content" not in DocumentModel.__table__.columns
    assert {column.name for column in DocumentModel.__table__.columns} == {
        "id",
        "storage_key",
        "sha256",
        "mime_type",
        "size_bytes",
        "created_at",
        "parser_status",
        "document_language",
        "page_count",
        "parse_error_code",
    }


def test_document_repository_returns_none_for_an_unknown_document() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with session_factory() as session:
        repository = SqlAlchemyDocumentRepository(session)
        document = repository.get("unknown-document")

    engine.dispose()

    assert document is None


def test_document_repository_rolls_back_after_a_persistence_failure() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    first = DocumentMetadata(
        document_id="document-001",
        storage_key="documents/shared-key.pdf",
        mime_type="application/pdf",
        size_bytes=42,
        sha256="a" * 64,
    )
    duplicate_key = first.model_copy(update={"document_id": "document-002"})

    with session_factory() as session:
        repository = SqlAlchemyDocumentRepository(session)
        repository.create(first)
        with pytest.raises(IntegrityError):
            repository.create(duplicate_key)

        fetched = repository.get(first.document_id)

    engine.dispose()

    assert fetched == first
