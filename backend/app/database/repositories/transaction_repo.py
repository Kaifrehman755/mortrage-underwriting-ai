"""Repository for Property Transactions and eligible comp queries.

Enforces GEMINI.md Section 4.3 and Section 8:
- Queries sale transactions linked to properties.
- Filters by transaction verification status and eligible price type.
- Enforces temporal cutoffs to prevent data leakage.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.transaction import PropertyTransaction
from app.schemas.transaction import PropertyTransactionCreate


class TransactionRepository:
    """Async repository for PropertyTransaction entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: PropertyTransactionCreate) -> PropertyTransaction:
        """Persist a new transaction record."""
        entity = PropertyTransaction(
            property_id=record.property_id,
            source_id=record.source_id,
            source_transaction_id=record.source_transaction_id,
            transaction_date=record.transaction_date,
            transaction_price_raw=record.transaction_price_raw,
            transaction_price_unit_raw=record.transaction_price_unit_raw,
            transaction_price_inr=record.transaction_price_inr,
            price_type=record.price_type.value if hasattr(record.price_type, "value") else str(record.price_type),
            transaction_verification_status=record.transaction_verification_status.value if hasattr(record.transaction_verification_status, "value") else str(record.transaction_verification_status),
            source_url=record.source_url,
            source_record_hash=record.source_record_hash,
            raw_payload=record.raw_payload,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_by_id(self, transaction_id: UUID) -> PropertyTransaction | None:
        stmt = select(PropertyTransaction).where(PropertyTransaction.transaction_id == transaction_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_eligible_comps(
        self,
        property_ids: list[UUID],
        cutoff_date: date,
        min_date: date | None = None,
        only_verified: bool = False,
    ) -> list[PropertyTransaction]:
        """Find eligible sales linked to candidate properties before cutoff_date."""
        if not property_ids:
            return []

        stmt = select(PropertyTransaction).where(
            PropertyTransaction.property_id.in_(property_ids),
            PropertyTransaction.transaction_date <= cutoff_date,
            PropertyTransaction.transaction_price_inr.isnot(None),
            PropertyTransaction.transaction_price_inr > 0,
            PropertyTransaction.price_type.in_(["sale_consideration", "reported_sale_price"]),
        )
        if min_date:
            stmt = stmt.where(PropertyTransaction.transaction_date >= min_date)
        if only_verified:
            stmt = stmt.where(PropertyTransaction.transaction_verification_status == "verified")

        stmt = stmt.order_by(PropertyTransaction.transaction_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
