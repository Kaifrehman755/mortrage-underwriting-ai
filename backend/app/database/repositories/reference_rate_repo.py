"""Repository for Administrative Reference Rates.

Enforces GEMINI.md Section 4.5:
- Multi-state lookup by state, district, locality, property category.
- Administrative benchmarks for circle rates, ready-reckoners, guidance values.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.reference_rate import ReferenceRate
from app.schemas.transaction import ReferenceRateCreate


class ReferenceRateRepository:
    """Async repository for ReferenceRate administrative benchmarks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_update(self, record: ReferenceRateCreate) -> ReferenceRate:
        """Upsert a reference rate keyed by unique constraint.

        F-17: the contract field is ``rate_inr_per_sqft``; the ORM attribute / physical column
        keeps the historical name ``rate_inr_normalized`` (basis: INR per square foot).
        """
        insert_stmt = pg_insert(ReferenceRate).values(
            source_id=record.source_id,
            state_code=record.state_code.upper(),
            district=record.district,
            locality=record.locality,
            property_category=record.property_category,
            rate_raw=record.rate_raw,
            rate_unit_raw=record.rate_unit_raw,
            rate_inr_normalized=record.rate_inr_per_sqft,
            effective_from=record.effective_from,
            effective_to=record.effective_to,
            published_at=record.published_at,
            source_url=record.source_url,
            source_record_hash=record.source_record_hash,
        )
        # `excluded` is an attribute of the *statement*, not of the `pg_insert` callable.
        stmt = insert_stmt.on_conflict_do_update(
            constraint="uq_reference_rate_state_dist_loc_cat_date",
            set_={
                "rate_raw": insert_stmt.excluded.rate_raw,
                "rate_inr_normalized": insert_stmt.excluded.rate_inr_normalized,
                "source_url": insert_stmt.excluded.source_url,
                "source_record_hash": insert_stmt.excluded.source_record_hash,
            },
        ).returning(ReferenceRate)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def lookup_benchmark(
        self,
        state_code: str,
        district: str,
        locality: str,
        property_category: str = "residential_flat",
        as_of_date: date | None = None,
    ) -> ReferenceRate | None:
        """Find the official reference rate benchmark for a locality."""
        state_norm = state_code.strip().upper()
        stmt = (
            select(ReferenceRate)
            .where(
                ReferenceRate.state_code == state_norm,
                ReferenceRate.district.ilike(district.strip()),
                ReferenceRate.locality.ilike(locality.strip()),
                ReferenceRate.property_category.ilike(property_category.strip()),
            )
        )
        if as_of_date:
            stmt = stmt.where(ReferenceRate.effective_from <= as_of_date)

        stmt = stmt.order_by(ReferenceRate.effective_from.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
