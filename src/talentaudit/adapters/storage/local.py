"""Local filesystem adapter for validated document bytes."""

from pathlib import Path, PurePosixPath
from uuid import uuid4

from talentaudit.schemas.document import DocumentMimeType, ValidatedDocument

_MIME_TYPE_SUFFIXES: dict[DocumentMimeType, str] = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
}


class LocalDocumentStorage:
    """Store validated files under one configured root directory.

    Storage keys are generated rather than derived from untrusted filenames.
    Every read/delete operation validates its key again, which prevents a
    caller from escaping the configured root with a traversal path.
    """

    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path.resolve()
        self._root_path.mkdir(parents=True, exist_ok=True)

    def put(self, document: ValidatedDocument) -> str:
        """Write validated bytes and return a new opaque storage key."""

        suffix = _MIME_TYPE_SUFFIXES[document.mime_type]
        for _ in range(3):
            storage_key = f"documents/{uuid4().hex}{suffix}"
            destination = self._path_for_key(storage_key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with destination.open("xb") as file_handle:
                    file_handle.write(document.content)
            except FileExistsError:
                continue
            return storage_key
        raise RuntimeError("could not allocate a unique document storage key")

    def get(self, storage_key: str) -> bytes:
        """Read bytes only from a path contained by the configured root."""

        return self._path_for_key(storage_key).read_bytes()

    def delete(self, storage_key: str) -> None:
        """Delete a file only after checking its path is safe."""

        self._path_for_key(storage_key).unlink()

    def _path_for_key(self, storage_key: str) -> Path:
        """Resolve a storage key and reject absolute or traversal paths."""

        key_path = PurePosixPath(storage_key)
        if (
            not storage_key
            or "\\" in storage_key
            or key_path.is_absolute()
            or any(part in {".", ".."} for part in key_path.parts)
        ):
            raise ValueError("storage key must be a safe relative path")

        candidate = (self._root_path / Path(*key_path.parts)).resolve()
        try:
            candidate.relative_to(self._root_path)
        except ValueError as error:
            raise ValueError("storage key must be a safe relative path") from error
        return candidate
