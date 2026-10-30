"""SQLAlchemy ORM model for the bronze (raw) ingestion layer.

Playbook sections 14.5 and 19.3 require untouched source payloads, a record type,
and a documented fingerprint for de-duplication when a source has no stable ID.
The fingerprint deliberately excludes buyer/seller names and other personal data.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

RECORD_TYPES = (
    "registered_transaction",
    "guideline_value",
    "land_record",
    "listing",
    "survey",
)


class RawRecord(Base):
    """An untouched source record awaiting cleaning into a silver/gold table."""

    __tablename__ = "raw_record"

    raw_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_sources.source_id"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="new", server_default="new", index=True
    )
    record_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="registered_transaction",
        server_default="registered_transaction",
        index=True,
    )
    record_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "record_type",
            "record_fingerprint",
            name="raw_record_dedupe",
        ),
        CheckConstraint(
            "record_type IN ('registered_transaction','guideline_value',"
            "'land_record','listing','survey')",
            name="ck_raw_record_type",
        ),
        CheckConstraint(
            "record_fingerprint ~ '^[a-f0-9]{64}$'",
            name="ck_raw_record_fingerprint_sha256",
        ),
        CheckConstraint(
            "file_sha256 IS NULL OR file_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_raw_record_file_sha256",
        ),
    )
