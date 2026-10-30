"""Playbook persistence, bronze fingerprint, and raw-store contracts."""

from __future__ import annotations

import hashlib
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.database.models import Base
from app.database.models.compliance_finding import ComplianceFinding
from app.database.models.regulatory import RegChunk as RegChunkModel
from app.database.models.regulatory import RegDocument as RegDocumentModel
from app.ingestion.bronze import build_record_fingerprint
from app.rag.embeddings import EmbeddingModelUnavailable, EmbeddingService
from app.rag.postgres_store import PostgresVectorStore
from app.rag.raw_store import (
    LocalRawDocumentStore,
    MinioRawDocumentStore,
    RawDocumentStoreError,
)
from app.rag.schemas import RegDocument


def test_playbook_tables_are_in_canonical_metadata() -> None:
    assert {
        "jurisdiction",
        "reg_document",
        "reg_chunk",
        "compliance_finding",
        "market_indicator",
        "raw_record",
    } <= set(Base.metadata.tables)


def test_evidence_and_approval_columns_exist() -> None:
    source_columns = set(Base.metadata.tables["data_sources"].columns.keys())
    assert {
        "access_mode",
        "approved_by",
        "approved_at",
        "terms_snapshot_sha256",
        "review_due",
        "last_attempt_at",
        "last_success_at",
        "last_error",
        "refresh_interval_days",
    } <= source_columns

    doc_columns = set(RegDocumentModel.__table__.columns.keys())
    assert {"scope", "state_code", "effective_from", "effective_to", "approved"} <= doc_columns
    assert {"embedding", "tsv", "index_version"} <= set(
        RegChunkModel.__table__.columns.keys()
    )


def test_database_enforces_evidence_on_non_abstain_findings() -> None:
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in ComplianceFinding.__table__.constraints
        if constraint.name
    }
    assert "cardinality(evidence_refs) > 0" in checks[
        "ck_compliance_finding_evidence_required"
    ]
    assert "status IN ('no_issue_detected','potential_issue','cannot_verify')" in checks[
        "ck_compliance_finding_status"
    ]


def test_approval_schema_requires_an_approval_record() -> None:
    with pytest.raises(ValidationError, match="approval record"):
        RegDocument(
            source_name="Example",
            authority="Example authority",
            version_or_date="2026-01-01",
            url="https://example.invalid/doc",
            sha256="a" * 64,
            approved=True,
        )

    approved = RegDocument(
        source_name="Example",
        authority="Example authority",
        version_or_date="2026-01-01",
        url="https://example.invalid/doc",
        sha256="a" * 64,
        approved=True,
        approved_by="Owner",
        approved_at="2026-01-01T00:00:00+00:00",
        review_due="2027-01-01",
        terms_snapshot_sha256="b" * 64,
    )
    assert approved.approved


def test_postgres_filters_include_approval_state_date_and_index() -> None:
    filters = PostgresVectorStore._base_filters(
        state_code="up",
        target_date=date(2026, 10, 25),
        require_approved=True,
        index_version="idx_v1",
    )
    rendered = " ".join(str(item) for item in filters).lower()
    assert "approved" in rendered
    assert "state" in rendered
    assert "effective_from" in rendered
    assert "index_version" in rendered


def test_postgres_store_rejects_wrong_embedding_dimension() -> None:
    store = PostgresVectorStore(session=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="384"):
        import asyncio

        asyncio.run(store.hybrid_search("query", [0.0, 1.0]))


def test_bronze_fingerprint_is_deterministic_and_pii_free() -> None:
    source_id = uuid4()
    kwargs = {
        "source_id": source_id,
        "record_type": "registered_transaction",
        "document_or_registration_number": "REG/2026/001",
        "sub_registrar_office": "Lucknow",
        "registration_date": date(2026, 5, 1),
        "recorded_consideration_inr": 8_500_000,
        "area_sqft": 1200,
    }
    first = build_record_fingerprint(**kwargs)
    second = build_record_fingerprint(**kwargs)
    assert first == second
    assert len(first) == 64
    assert set(first) <= set("0123456789abcdef")

    changed = build_record_fingerprint(**{**kwargs, "record_type": "listing"})
    assert changed != first


def test_bronze_fingerprint_refuses_empty_identifiers() -> None:
    with pytest.raises(ValueError, match="cannot fingerprint"):
        build_record_fingerprint(
            source_id=uuid4(),
            record_type="registered_transaction",
        )


def test_local_raw_store_is_content_addressed_and_verifies(tmp_path: Path) -> None:
    store = LocalRawDocumentStore(tmp_path)
    stored = store.put_document(b"official bytes", "text/plain")
    assert stored.sha256 == hashlib.sha256(b"official bytes").hexdigest()
    assert store.get_document(stored.key) == b"official bytes"
    assert store.put_document(b"official bytes").key == stored.key


def test_local_raw_store_detects_tampering(tmp_path: Path) -> None:
    store = LocalRawDocumentStore(tmp_path)
    stored = store.put_document(b"official bytes")
    path = tmp_path / stored.key
    path.write_bytes(b"tampered")
    with pytest.raises(RawDocumentStoreError, match="SHA-256"):
        store.get_document(stored.key)


def test_minio_store_fails_closed_without_credentials() -> None:
    with pytest.raises(RawDocumentStoreError, match="MINIO_ACCESS_KEY"):
        MinioRawDocumentStore("localhost:9000", "", "", "bucket")


def test_production_embedding_requires_the_real_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(EmbeddingModelUnavailable, match="real embedding model"):
        EmbeddingService(require_model=True)
