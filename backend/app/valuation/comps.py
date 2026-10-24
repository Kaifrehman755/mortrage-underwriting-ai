"""Comparable Selection and Filtering Engine.

Enforces GEMINI.md Section 8:
- A record is not eligible merely because it contains a price.
- Filters by:
  * State isolation (no cross-state comp contamination).
  * Compatible area basis (carpet to carpet only; never equate carpet with built-up).
  * Eligible price type (sale_consideration only; excludes asking prices and circle rates).
  * Temporal cutoff (no future transactions relative to dataset_cutoff).
  * Stepwise proximity search (1.5km -> 3.0km -> 5.0km) with logged expansion reasons.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.database.repositories.property_repo import haversine_distance_meters
from app.ingestion.normalize import calculate_price_per_sqft
from app.schemas.property import AreaType, PropertyType


def coerce_to_uuid(raw_id: Any) -> UUID:
    """Safely coerce any ID to a UUID, using deterministic URL namespace if needed."""
    if isinstance(raw_id, UUID):
        return raw_id
    try:
        return UUID(str(raw_id))
    except (ValueError, TypeError):
        return uuid5(NAMESPACE_URL, f"trans:{raw_id}")



@dataclass(frozen=True)
class SubjectPropertyInput:
    """Subject property input parameters for valuation."""

    state_code: str
    district: str
    locality: str
    latitude: float | None
    longitude: float | None
    area_sqft: float
    area_type: AreaType
    property_type: PropertyType = PropertyType.APARTMENT
    pincode: str | None = None


@dataclass(frozen=True)
class EligibleComparable:
    """An eligible transaction evidence record linked to a physical property."""

    transaction_id: UUID
    property_id: UUID | None
    distance_m: float
    transaction_date: date
    price_inr: float
    area_sqft: float
    area_type: AreaType
    price_per_sqft: float
    selection_reason: str
    is_outlier: bool = False
    robust_z: float | None = None


class ComparableSelector:
    """Identifies and filters eligible comparable transactions."""

    def __init__(
        self,
        min_comps: int = 3,
        initial_radius_km: float = 1.5,
        max_radius_km: float = 5.0,
        max_age_months: int = 18,
    ) -> None:
        self.min_comps = min_comps
        self.initial_radius_km = initial_radius_km
        self.max_radius_km = max_radius_km
        self.max_age_months = max_age_months

    def filter_candidate_pool(
        self,
        subject: SubjectPropertyInput,
        candidates: list[dict[str, Any]],
        dataset_cutoff: date,
    ) -> tuple[list[EligibleComparable], list[str]]:
        """Filter a pool of raw transaction candidates against eligibility rules.

        Returns (eligible_comps, filter_expansion_logs).
        """
        logs: list[str] = []

        # Coordinate check
        if subject.latitude is None or subject.longitude is None:
            logs.append("Subject property lacks geographic coordinates; proximity filtering impossible.")
            return [], logs

        # Area type check
        if subject.area_type == AreaType.UNKNOWN:
            logs.append("Subject area type is unknown; area-basis compatibility check cannot pass.")
            return [], logs

        min_tx_date = dataset_cutoff - timedelta(days=self.max_age_months * 30)
        state_norm = subject.state_code.strip().upper()

        # Step 1: Pre-filter by state isolation, property type, price type, and date
        valid_candidates: list[dict[str, Any]] = []
        for cand in candidates:
            # Rule 1: State Isolation
            if str(cand.get("state_code", "")).upper() != state_norm:
                continue

            # Rule 2: Property Type
            cand_prop_type = cand.get("property_type")
            expected_prop_type = subject.property_type.value if hasattr(subject.property_type, "value") else str(subject.property_type)
            if cand_prop_type != expected_prop_type:
                continue

            # Rule 3: Temporal boundary
            tx_date_raw = cand.get("transaction_date")
            if not tx_date_raw:
                continue
            tx_date = tx_date_raw if isinstance(tx_date_raw, date) else date.fromisoformat(str(tx_date_raw)[:10])
            if tx_date > dataset_cutoff or tx_date < min_tx_date:
                continue

            # Rule 4: Eligible Price Type (must be actual sale consideration)
            price_type = str(cand.get("price_type", "")).lower()
            if price_type not in ("sale_consideration", "reported_sale_price"):
                continue

            # Rule 5: Area type compatibility
            cand_area_type_str = str(cand.get("area_type", "unknown")).lower()
            try:
                cand_area_type = AreaType(cand_area_type_str)
            except ValueError:
                continue

            # Enforce strict compatibility: carpet to carpet, plot to plot
            if cand_area_type != subject.area_type:
                continue

            # Rule 6: Validate price and area
            price_inr = float(cand.get("transaction_price_inr") or cand.get("price_inr") or 0)
            area_sqft = float(cand.get("area_sqft") or cand.get("living_area_sqft") or 0)
            pps = calculate_price_per_sqft(
                price_inr=price_inr,
                area_sqft=area_sqft,
                subject_area_type=subject.area_type,
                comp_area_type=cand_area_type,
            )
            if pps is None or pps <= 0:
                continue

            # Distance calculation
            c_lat = cand.get("latitude") or cand.get("lat")
            c_lon = cand.get("longitude") or cand.get("lon")
            if c_lat is None or c_lon is None:
                continue

            dist_m = haversine_distance_meters(
                subject.latitude, subject.longitude, float(c_lat), float(c_lon)
            )

            valid_candidates.append({
                **cand,
                "tx_date": tx_date,
                "price_inr": price_inr,
                "area_sqft": area_sqft,
                "area_type": cand_area_type,
                "price_per_sqft": pps,
                "distance_m": dist_m,
            })

        # Sort all candidates by distance
        valid_candidates.sort(key=lambda x: x["distance_m"])

        # Step 2: Stepwise proximity expansion (1.5km -> 3.0km -> 5.0km)
        active_radius_km = self.initial_radius_km
        selected_raw: list[dict[str, Any]] = [
            c for c in valid_candidates if c["distance_m"] <= active_radius_km * 1000.0
        ]
        logs.append(f"Initial radius {active_radius_km} km found {len(selected_raw)} comps.")

        if len(selected_raw) < self.min_comps and active_radius_km < 3.0:
            active_radius_km = 3.0
            selected_raw = [
                c for c in valid_candidates if c["distance_m"] <= active_radius_km * 1000.0
            ]
            logs.append(f"Expanded search radius to {active_radius_km} km (found {len(selected_raw)} comps).")

        if len(selected_raw) < self.min_comps and active_radius_km < self.max_radius_km:
            active_radius_km = self.max_radius_km
            selected_raw = [
                c for c in valid_candidates if c["distance_m"] <= active_radius_km * 1000.0
            ]
            logs.append(f"Expanded search radius to max allowable {active_radius_km} km (found {len(selected_raw)} comps).")

        eligible_comps: list[EligibleComparable] = []
        for c in selected_raw:
            raw_comp_id = c.get("transaction_id") or c.get("comp_id")
            comp_id = coerce_to_uuid(raw_comp_id) if raw_comp_id is not None else coerce_to_uuid("TX_ANON")
            raw_prop_id = c.get("property_id")
            prop_id = coerce_to_uuid(raw_prop_id) if raw_prop_id is not None else None
            eligible_comps.append(
                EligibleComparable(
                    transaction_id=comp_id,
                    property_id=prop_id,
                    distance_m=round(c["distance_m"], 1),
                    transaction_date=c["tx_date"],
                    price_inr=c["price_inr"],
                    area_sqft=c["area_sqft"],
                    area_type=c["area_type"],
                    price_per_sqft=c["price_per_sqft"],
                    selection_reason=f"Proximity {round(c['distance_m']/1000.0, 2)}km, age {(dataset_cutoff - c['tx_date']).days}d",
                )
            )

        return eligible_comps, logs
