"""Repository for Valuation Runs and Comparables traceability.

Enforces GEMINI.md Section 4.7:
- Every valuation estimate is traceable to the eligible comparable evidence used.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.valuation import ValuationComparable, ValuationRun
from app.schemas.valuation import ValuationRunCreate


class ValuationRepository:
    """Async repository for ValuationRun and ValuationComparable audit trail."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_valuation_run(
        self,
        run_data: ValuationRunCreate,
        comparables: list[dict[str, Any]] | None = None,
    ) -> ValuationRun:
        """Persist a valuation estimate and all linked comparables."""
        entity = ValuationRun(
            subject_property_input=run_data.subject_property_input,
            estimate_inr=run_data.estimate_inr,
            lower_bound_inr=run_data.lower_bound_inr,
            upper_bound_inr=run_data.upper_bound_inr,
            status=run_data.status.value if hasattr(run_data.status, "value") else str(run_data.status),
            reason_codes=run_data.reason_codes,
            method_version=run_data.method_version,
            dataset_cutoff=run_data.dataset_cutoff,
        )
        self.session.add(entity)
        await self.session.flush()

        if comparables:
            for comp in comparables:
                comp_entity = ValuationComparable(
                    valuation_id=entity.valuation_id,
                    transaction_id=comp["transaction_id"],
                    distance_m=comp["distance_m"],
                    similarity_score=comp.get("similarity_score"),
                    adjusted_price_per_sqft=comp["adjusted_price_per_sqft"],
                    selection_reason=comp.get("selection_reason", "eligible_recent_proximity"),
                )
                self.session.add(comp_entity)
            await self.session.flush()

        return entity

    async def get_valuation(self, valuation_id: UUID) -> tuple[ValuationRun | None, list[ValuationComparable]]:
        """Retrieve valuation run and linked comparables."""
        stmt = select(ValuationRun).where(ValuationRun.valuation_id == valuation_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            return None, []

        comps_stmt = select(ValuationComparable).where(ValuationComparable.valuation_id == valuation_id)
        comps_res = await self.session.execute(comps_stmt)
        comps = list(comps_res.scalars().all())

        return run, comps
