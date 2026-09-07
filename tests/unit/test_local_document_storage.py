"""Tests for the local document storage adapter."""

from pathlib import Path

import pytest

from talentaudit.adapters.storage.local import LocalDocumentStorage
from talentaudit.schemas.document import ValidatedDocument


def test_local_storage_generates_a_key_and_round_trips_validated_bytes(
    tmp_path: Path,
) -> None:
    storage = LocalDocumentStorage(tmp_path)
    document = ValidatedDocument(
        document_id="document-001",
        mime_type="text/plain",
        size_bytes=16,
        sha256="a" * 64,
        content=b"Synthetic notes.",
    )

    storage_key = storage.put(document)

    assert storage_key.startswith("documents/")
    assert storage_key.endswith(".txt")
    assert "document-001" not in storage_key
    assert storage.get(storage_key) == document.content

    storage.delete(storage_key)
    assert not (tmp_path / Path(storage_key)).exists()


@pytest.mark.parametrize("storage_key", ["../outside.txt", "/outside.txt", "a\\b.txt"])
def test_local_storage_rejects_path_traversal_keys(
    tmp_path: Path,
    storage_key: str,
) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(ValueError, match="safe relative path"):
        storage.get(storage_key)
