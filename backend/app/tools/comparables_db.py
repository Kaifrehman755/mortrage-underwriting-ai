"""Sync comparables lookup for property valuation agent."""

from sqlalchemy import select
from app.property_data.database.connection import AsyncSessionLocal
from app.property_data.database.models import PropertyListingDB


async def get_comparables(
    locality: str | None = None,
    city: str | None = None,
    property_type: str | None = None,
    bhk: int | None = None,
    area_sqft: int | None = None,
    max_results: int = 10,
) -> list[dict]:
    """Return comparable property listings from PostgreSQL."""
    try:
        async with AsyncSessionLocal() as session:
            query = select(PropertyListingDB).where(
                PropertyListingDB.transaction_type == "Sale"
            )
            if city:
                query = query.where(PropertyListingDB.city == city)
            if locality:
                query = query.where(PropertyListingDB.locality == locality)
            if property_type:
                query = query.where(PropertyListingDB.property_type == property_type)
            if bhk is not None:
                query = query.where(PropertyListingDB.bedrooms == bhk)
            if area_sqft is not None:
                query = query.where(
                    PropertyListingDB.area_sqft >= area_sqft * 0.8,
                    PropertyListingDB.area_sqft <= area_sqft * 1.2,
                )
            query = query.limit(max_results)
            result = await session.execute(query)
            rows = result.scalars().all()
            return [
                {
                    "id": row.id,
                    "bhk": row.bedrooms,
                    "area_sqft": row.area_sqft,
                    "price_inr": row.price,
                    "price_per_sqft": row.price_per_sqft,
                    "city": row.city,
                    "locality": row.locality,
                    "property_type": row.property_type,
                    "data_quality_score": row.data_quality_score,
                    "quality_label": getattr(row, "quality_label", None),
                }
                for row in rows
            ]
    except Exception:
        return []
