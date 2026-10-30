from fastapi import APIRouter
from app.tools.comparables_db import get_comparables

router = APIRouter(prefix="/property-data")

@router.get("/comps")
async def lookup_comps(
    city: str = "Bengaluru",
    locality: str | None = None,
    property_type: str | None = None,
    bhk: int | None = None,
    area_sqft: int | None = None,
):
    comps = await get_comparables(
        locality=locality,
        city=city,
        property_type=property_type,
        bhk=bhk,
        area_sqft=area_sqft,
    )
    return {"count": len(comps), "comparables": comps}
