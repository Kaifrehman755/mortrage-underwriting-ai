"""SQLAlchemy ORM model for Data Sources and Provenance.

Enforces GEMINI.md Section 4.1 and Playbook sections 18.2/19.3:
- Provider identity, licensing scope, and approval gate status.
- An approval record (who/when/terms hash/review due) is required before a source
  can be marked approved.
- Capability flags start as unknown (NULL) rather than being assumed.
- Freshness fields support the DATA-001 stale-source check.
"""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DataSource(Base, TimestampMixin):
    """Stores data provider identity, access method, approval, and freshness."""

    __tablename__ = "data_sources"

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    access_method: Mapped[str] = mapped_column(String(50), nullable=False)
    license_scope: Mapped[str] = mapped_column(Text, nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    terms_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Playbook 19.3: capabilities start unknown; NULL means not verified.
    access_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="access_pending",
        server_default="access_pending",
        index=True,
    )
    supports_transactions: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supports_guideline_values: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supports_land_records: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    refresh_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Playbook 18.2: approval is a record, not a boolean alone.
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terms_snapshot_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "access_mode IN ('access_pending','official_api','official_download',"
            "'portal_manual','licensed_feed','not_permitted')",
            name="ck_data_source_access_mode",
        ),
        CheckConstraint(
            "terms_snapshot_sha256 IS NULL OR "
            "terms_snapshot_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_data_source_terms_sha256",
        ),
        CheckConstraint(
            "approval_status <> 'approved' OR (approved_by IS NOT NULL "
            "AND approved_at IS NOT NULL AND terms_snapshot_sha256 IS NOT NULL "
            "AND review_due IS NOT NULL AND access_mode NOT IN "
            "('access_pending','not_permitted'))",
            name="ck_data_source_approved_needs_record",
        ),
    )
