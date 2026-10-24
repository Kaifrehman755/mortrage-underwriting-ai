"""SQLAlchemy ORM models for Ingestion Runs and Quarantine Audit.

Enforces GEMINI.md Section 4.6 and Section 6:
- Every ingestion run accounts for all received rows.
- Rejected/quarantined records stored with reason codes.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionRun(Base):
    """Tracks metadata and row accounting metrics for an ingestion run."""

    __tablename__ = "ingestion_runs"

    run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    build_version: Mapped[str] = mapped_column(String(50), nullable=False)
    source_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    rows_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_quarantined: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_duplicate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class QuarantineRecordModel(Base):
    """Stores rejected/quarantined rows with audit reason codes."""

    __tablename__ = "quarantine_records"

    quarantine_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ingestion_runs.run_id"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    source_record_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reason_detail: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_record_ref: Mapped[str] = mapped_column(Text, nullable=False)
