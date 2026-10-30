"""SQLAlchemy ORM model for retrieved market indicators.

Market facts are retrieved, never modelled. They live in their own table and are
never folded into a valuation estimate (playbook invariants 1 and 2).
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    PrimaryKeyConstraint,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MarketIndicator(Base):
    """One observation such as median PPSF or HPI for a geo/period/metric."""

    __tablename__ = "market_indicator"

    geo_key: Mapped[str] = mapped_column(String(200), nullable=False)
    period: Mapped[date] = mapped_column(Date, nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_sources.source_id"),
        nullable=False,
    )
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "geo_key", "period", "metric", "source_id", name="pk_market_indicator"
        ),
        CheckConstraint("value = value", name="ck_market_indicator_value_not_nan"),
    )
