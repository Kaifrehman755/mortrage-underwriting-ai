"""Circle rate lookup API endpoints.

Adheres to the Phase 1 trust rule: every rate is served with its source URL
and fetch timestamp so users can verify it against the official portal.

Access policy (F-05, see ``docs/security/access_policy.md``): this endpoint is deliberately
**public reference data** — it returns government-notified circle rates only, never personal or
confidential information. It therefore carries input validation, safe error handling and a
best-effort rate limiter rather than authentication.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models.circle_rate import CircleRate
from app.schemas.circle_rate import CircleRateLookup
from app.security.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/circle-rates", tags=["Circle Rates"])


@router.get(
    "/lookup",
    response_model=CircleRateLookup,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Look up the official circle rate for a locality",
    description=(
        "Returns the government-notified circle rate (guideline value) in INR "
        "per SQUARE METRE (`rate_per_sqm`) for a locality, with the source URL "
        "and fetch date so the figure can be verified against the official "
        "portal. Note: the canonical reference-rate pipeline normalises to INR "
        "per SQUARE FOOT (`rate_inr_per_sqft`), so the two bases are not "
        "interchangeable (F-17). Public reference-data endpoint (F-05); no "
        "personal or confidential data is returned."
    ),
)
async def lookup_circle_rate(
    session: Annotated[AsyncSession, Depends(get_db)],
    state: str = Query(
        default="UP",
        min_length=2,
        max_length=10,
        pattern=r"^[A-Za-z]{2,10}$",
        description="State code, e.g. UP",
    ),
    district: str = Query(default="Lucknow", min_length=1, max_length=100, description="District name"),
    locality: str = Query(..., min_length=1, max_length=100, description="Locality / area name"),
    property_type: str = Query(
        default="residential_flat",
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$",
        description="Property type; defaults to the canonical residential_flat",
    ),
) -> CircleRateLookup:
    """Look up the latest circle rate for a locality."""
    stmt = (
        select(CircleRate)
        .where(
            CircleRate.state == state.strip().upper(),
            CircleRate.district.ilike(district.strip()),
            CircleRate.locality.ilike(locality.strip()),
            CircleRate.property_type.ilike(property_type.strip()),
        )
        .order_by(CircleRate.effective_year.desc(), CircleRate.fetched_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()

    if row is None:
        # Generic message: do not reflect raw user input back in the response.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No circle rate found for the requested locality. Run ingestion first.",
        )

    return CircleRateLookup.model_validate(row, from_attributes=True)
