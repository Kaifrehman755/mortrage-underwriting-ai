"""Immutable raw-document storage with SHA-256 provenance.

Playbook sections 2, 4, and 16 SOP-3 require the original regulatory file to be
kept so every chunk can be traced back to a hashed source. MinIO/S3 is the
production target; a local filesystem store exists for offline development and
tests. Neither store writes unverified bytes under an assumed hash: the hash is
computed from the bytes before the object is written.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import Settings, get_settings


class RawDocumentStoreError(RuntimeError):
    """Raised when raw evidence cannot be stored or verified."""


@dataclass(frozen=True)
class StoredDocument:
    """A stored object's locator and content hash."""

    key: str
    sha256: str
    size_bytes: int


class RawDocumentStore(Protocol):
    """Minimal object-store interface used by the ingestion pipeline."""

    def put_document(self, raw_bytes: bytes, content_type: str = "application/octet-stream") -> StoredDocument:
        """Store bytes and return their immutable locator and SHA-256."""

    def get_document(self, key: str) -> bytes:
        """Read bytes back by key."""


class LocalRawDocumentStore:
    """Filesystem store for tests and explicitly offline development."""

    def __init__(self, base_path: Path | str):
        self.base_path = Path(base_path)

    def put_document(
        self, raw_bytes: bytes, content_type: str = "application/octet-stream"
    ) -> StoredDocument:
        del content_type  # Filesystem store records bytes only.
        digest = hashlib.sha256(raw_bytes).hexdigest()
        key = f"regulatory/{digest[:2]}/{digest}"
        target = self.base_path / key
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise RawDocumentStoreError(
                    f"existing object {key} does not match its content hash"
                )
            return StoredDocument(key=key, sha256=digest, size_bytes=len(raw_bytes))
        target.write_bytes(raw_bytes)
        return StoredDocument(key=key, sha256=digest, size_bytes=len(raw_bytes))

    def get_document(self, key: str) -> bytes:
        target = self.base_path / key
        if not target.is_file():
            raise RawDocumentStoreError(f"raw document {key} not found")
        raw = target.read_bytes()
        expected = key.rsplit("/", 1)[-1]
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise RawDocumentStoreError(
                f"raw document {key} failed SHA-256 verification"
            )
        return raw


class MinioRawDocumentStore:
    """MinIO/S3-compatible immutable document store.

    The ``minio`` dependency is imported lazily so test environments that do not
    run MinIO can still import the RAG package and use the local store. Empty
    credentials fail closed.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        if not access_key or not secret_key:
            raise RawDocumentStoreError(
                "MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when "
                "RAW_DOCUMENT_STORE=minio"
            )
        from minio import Minio

        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def put_document(
        self, raw_bytes: bytes, content_type: str = "application/octet-stream"
    ) -> StoredDocument:
        import io

        digest = hashlib.sha256(raw_bytes).hexdigest()
        key = f"regulatory/{digest[:2]}/{digest}"
        existing = self._stat_object(key)
        if existing is not None:
            if existing != len(raw_bytes):
                raise RawDocumentStoreError(
                    f"existing object {key} has unexpected size"
                )
            return StoredDocument(key=key, sha256=digest, size_bytes=len(raw_bytes))

        self._client.put_object(
            self.bucket,
            key,
            io.BytesIO(raw_bytes),
            length=len(raw_bytes),
            content_type=content_type,
        )
        return StoredDocument(key=key, sha256=digest, size_bytes=len(raw_bytes))

    def get_document(self, key: str) -> bytes:
        response = None
        try:
            response = self._client.get_object(self.bucket, key)
            raw = response.read()
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise RawDocumentStoreError(f"could not read {key}: {exc}") from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

        expected = key.rsplit("/", 1)[-1]
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise RawDocumentStoreError(
                f"raw document {key} failed SHA-256 verification"
            )
        return raw

    def _stat_object(self, key: str) -> int | None:
        try:
            stat = self._client.stat_object(self.bucket, key)
            return int(stat.size or 0)
        except Exception:  # noqa: BLE001 - missing object is a normal miss
            return None


def build_raw_document_store(
    settings: Settings | None = None,
    *,
    local_path: Path | str | None = None,
) -> RawDocumentStore:
    """Build the configured raw-document store, failing closed on misuse."""
    config = settings or get_settings()
    store_type = config.RAW_DOCUMENT_STORE.strip().lower()
    if store_type == "local":
        path = local_path or (Path(config.STORAGE_BASE_PATH) / "raw_regulatory")
        return LocalRawDocumentStore(path)
    if store_type == "minio":
        return MinioRawDocumentStore(
            endpoint=config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            bucket=config.MINIO_BUCKET,
            secure=config.MINIO_SECURE,
        )
    raise RawDocumentStoreError(
        f"unsupported RAW_DOCUMENT_STORE={config.RAW_DOCUMENT_STORE!r}; "
        "use 'minio' or 'local'"
    )
