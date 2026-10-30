"""SQLAlchemy ORM models for regulatory documents and evidence chunks.

Playbook section 4 stores approved regulatory documents and their 384-dimension
embeddings in Postgres/pgvector. Approval is fail-closed: a document created by
default is not trusted for retrieval until an owner records the approval fields.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class RegDocument(Base, TimestampMixin):
    """An approved (or candidate) regulatory source document."""

    __tablename__ = "reg_document"

    doc_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="general", server_default="general"
    )
    version_or_date: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    terms_snapshot_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    license_scope: Mapped[str] = mapped_column(
        Text, nullable=False, default="unverified", server_default="unverified"
    )
    scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default="national", server_default="national", index=True
    )
    state_code: Mapped[str | None] = mapped_column(
        String(2), ForeignKey("jurisdiction.state_code"), nullable=True, index=True
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "scope IN ('national','state')", name="ck_reg_document_scope"
        ),
        CheckConstraint(
            "(scope = 'national' AND state_code IS NULL) OR "
            "(scope = 'state' AND state_code IS NOT NULL)",
            name="ck_reg_document_scope_state",
        ),
        CheckConstraint(
            "sha256 ~ '^[a-f0-9]{64}$'", name="ck_reg_document_sha256"
        ),
        CheckConstraint(
            "terms_snapshot_sha256 IS NULL OR "
            "terms_snapshot_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_reg_document_terms_sha256",
        ),
        CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR effective_from <= effective_to",
            name="ck_reg_document_effective_dates",
        ),
        CheckConstraint(
            "NOT approved OR (approved_by IS NOT NULL AND approved_at IS NOT NULL "
            "AND review_due IS NOT NULL AND terms_snapshot_sha256 IS NOT NULL)",
            name="ck_reg_document_approved_needs_record",
        ),
    )


class RegChunk(Base):
    """A retrievable chunk of one regulatory document with its embedding."""

    __tablename__ = "reg_chunk"

    chunk_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    doc_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reg_document.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[str] = mapped_column(Text, nullable=False)
    section_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    tsv: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', text)", persisted=True),
        nullable=True,
    )
    scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default="national", server_default="national", index=True
    )
    state_code: Mapped[str | None] = mapped_column(
        String(2), ForeignKey("jurisdiction.state_code"), nullable=True, index=True
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    version_or_date: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    license_scope: Mapped[str] = mapped_column(
        Text, nullable=False, default="unverified", server_default="unverified"
    )
    index_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint(
            "doc_id", "section_ref", "index_version", name="uq_reg_chunk_doc_section_version"
        ),
        CheckConstraint(
            "scope IN ('national','state')", name="ck_reg_chunk_scope"
        ),
        CheckConstraint(
            "(scope = 'national' AND state_code IS NULL) OR "
            "(scope = 'state' AND state_code IS NOT NULL)",
            name="ck_reg_chunk_scope_state",
        ),
        CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR effective_from <= effective_to",
            name="ck_reg_chunk_effective_dates",
        ),
        Index(
            "idx_reg_chunk_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("idx_reg_chunk_tsv_gin", "tsv", postgresql_using="gin"),
    )
