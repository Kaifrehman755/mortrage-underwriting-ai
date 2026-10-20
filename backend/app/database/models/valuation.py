"""SQLAlchemy ORM models for Valuation Runs and Comparables.

Enforces GEMINI.md Section 4.7:
- Every estimate is traceable to the eligible comparable evidence used.
- Stores estimate, uncertainty bounds, abstention status, and reason codes.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ValuationRun(Base):
    """Stores property valuation execution result, bounds, and abstention status."""

    __tablename__ = "valuation_runs"

    valuation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    subject_property_input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    estimate_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_bound_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound_inr: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="completed", index=True
    )
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    method_version: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_cutoff: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ValuationComparable(Base):
    """Stores individual eligible comps used to derive a valuation estimate."""

    __tablename__ = "valuation_comparables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    valuation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("valuation_runs.valuation_id"), nullable=False, index=True
    )
    transaction_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("property_transactions.transaction_id"), nullable=False, index=True
    )
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    adjusted_price_per_sqft: Mapped[float] = mapped_column(Float, nullable=False)
    selection_reason: Mapped[str] = mapped_column(String(200), nullable=False)
