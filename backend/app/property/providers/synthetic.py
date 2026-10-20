"""Synthetic comp provider generating seeded, reproducible property sales.

Implements Playbook Section 3a, 5, 14.2, and 18.4:
- Seeded, deterministic comps across Lucknow (UP), Mumbai (MH), and Bengaluru (KA).
- Every record explicitly tagged is_synthetic=True and license_scope='synthetic_internal'.
- Supports simulated provider outage to verify Invariant 1.
"""

import random
from datetime import date, timedelta
from typing import Any, TypedDict
from uuid import NAMESPACE_DNS, uuid5

from app.property.normalize import haversine_km
from app.property.provider import CompProvider, ProviderUnavailable
from app.property.schemas import ComparableRecord, SubjectProperty


class LocalityDict(TypedDict):
    locality: str
    city: str
    lat: float
    lon: float
    base_ppsf: float
    pin: str


# Realistic baseline coordinates and price ranges by locality
LOCALITY_CATALOG: dict[str, list[LocalityDict]] = {
    # Uttar Pradesh (Lucknow Pilot)
    "UP": [
        {"locality": "Gomti Nagar", "city": "Lucknow", "lat": 26.8530, "lon": 80.9980, "base_ppsf": 5200.0, "pin": "226010"},
        {"locality": "Indira Nagar", "city": "Lucknow", "lat": 26.8840, "lon": 80.9890, "base_ppsf": 4600.0, "pin": "226016"},
        {"locality": "Hazratganj", "city": "Lucknow", "lat": 26.8467, "lon": 80.9461, "base_ppsf": 6800.0, "pin": "226001"},
        {"locality": "Aliganj", "city": "Lucknow", "lat": 26.8920, "lon": 80.9410, "base_ppsf": 4800.0, "pin": "226024"},
    ],
    # Maharashtra (Mumbai)
    "MH": [
        {"locality": "Bandra West", "city": "Mumbai", "lat": 19.0596, "lon": 72.8295, "base_ppsf": 38000.0, "pin": "400050"},
        {"locality": "Andheri East", "city": "Mumbai", "lat": 19.1136, "lon": 72.8697, "base_ppsf": 18500.0, "pin": "400069"},
    ],
    # Karnataka (Bengaluru)
    "KA": [
        {"locality": "Indiranagar", "city": "Bengaluru", "lat": 12.9719, "lon": 77.6412, "base_ppsf": 11500.0, "pin": "560038"},
        {"locality": "Koramangala", "city": "Bengaluru", "lat": 12.9352, "lon": 77.6245, "base_ppsf": 12500.0, "pin": "560034"},
    ],
    # Telangana (Hyderabad)
    "TS": [
        {"locality": "Banjara Hills", "city": "Hyderabad", "lat": 17.4156, "lon": 78.4354, "base_ppsf": 9500.0, "pin": "500034"},
        {"locality": "Jubilee Hills", "city": "Hyderabad", "lat": 17.4319, "lon": 78.4073, "base_ppsf": 10500.0, "pin": "500033"},
        {"locality": "Gachibowli", "city": "Hyderabad", "lat": 17.4401, "lon": 78.3489, "base_ppsf": 7800.0, "pin": "500032"},
        {"locality": "Hitec City", "city": "Hyderabad", "lat": 17.4474, "lon": 78.3762, "base_ppsf": 8200.0, "pin": "500081"},
    ],
}


class SyntheticProvider(CompProvider):
    """Generates synthetic, deterministic comparable sales with fixed seeding."""

    def __init__(self, seed: int = 42, simulate_outage: bool = False):
        self.seed = seed
        self.simulate_outage = simulate_outage

    def _generate_pool(self, state_code: str) -> list[dict[str, Any]]:
        """Generate a deterministic universe of 150 comps for the given state."""
        rng = random.Random(f"{self.seed}_{state_code}")
        state_norm = state_code.upper()
        localities = LOCALITY_CATALOG.get(state_norm, LOCALITY_CATALOG["UP"])

        pool: list[dict[str, Any]] = []
        today = date(2026, 10, 10)  # Reference date matching system metadata

        for i in range(150):
            loc_info = rng.choice(localities)
            # Add small geo jitter within ~1.5 km
            d_lat = rng.uniform(-0.015, 0.015)
            d_lon = rng.uniform(-0.015, 0.015)
            loc_lat = loc_info["lat"]
            loc_lon = loc_info["lon"]
            base_ppsf = loc_info["base_ppsf"]
            locality_name = loc_info["locality"]
            city_name = loc_info["city"]

            lat = round(loc_lat + d_lat, 5)
            lon = round(loc_lon + d_lon, 5)

            # Plausible area between 750 and 2200 sqft
            sqft = rng.choice([850, 950, 1100, 1250, 1400, 1650, 1800, 2100])
            area_jitter = rng.uniform(-40, 40)
            living_area = round(sqft + area_jitter, 1)

            # Noise on price per sqft (+/- 12%)
            ppsf_noise = rng.uniform(0.88, 1.12)
            ppsf = base_ppsf * ppsf_noise
            price = round(living_area * ppsf, -3)  # round to nearest thousand

            # Price types: mostly registered deeds & valuer reports; 15% asking prices
            price_type_val = rng.choices(
                ["registered_deed", "valuer_report", "survey", "asking"],
                weights=[0.55, 0.25, 0.05, 0.15],
                k=1,
            )[0]

            # Sale date within past 18 months
            days_ago = rng.randint(5, 540)
            sale_date_val = (today - timedelta(days=days_ago)).isoformat()

            # Record identifier
            rec_id = f"SYNTH-{state_norm}-{locality_name[:3].upper()}-{i:04d}"

            pool.append({
                "provider_record_id": rec_id,
                "address": f"Flat {rng.randint(101, 1404)}, Block {rng.choice(['A','B','C'])}, {locality_name}",
                "locality": locality_name,
                "city": city_name,
                "state_code": state_norm,
                "property_type": "apartment",
                "sale_price": price,
                "living_area_sqft": living_area,
                "sale_date": sale_date_val,
                "price_type": price_type_val,
                "area_basis": "carpet",
                "lat": lat,
                "lon": lon,
            })

        return pool

    def fetch_comps(
        self,
        subject: SubjectProperty,
        radius_km: float = 3.0,
        months: int = 12,
        filters: dict[str, Any] | None = None,
    ) -> list[ComparableRecord]:
        """Fetch matching comps.

        Invariant 1: Provider outage raises ProviderUnavailable; never fabricates data.
        Invariant 8: State isolation - only returns comps from the subject's own state.
        """
        if self.simulate_outage:
            raise ProviderUnavailable(
                provider_name="synthetic_provider",
                message="Simulated connection timeout to comps registry.",
            )

        pool = self._generate_pool(subject.state_code)
        cutoff_date = date(2026, 10, 10) - timedelta(days=months * 30)

        results: list[ComparableRecord] = []
        for item in pool:
            # Enforce state isolation
            if item["state_code"] != subject.state_code:
                continue

            # Date check
            d = date.fromisoformat(item["sale_date"])
            if d < cutoff_date:
                continue

            # Property type check
            if filters and "property_type" in filters:
                if item["property_type"] != filters["property_type"]:
                    continue

            # Calculate distance
            dist = haversine_km(subject.lat, subject.lon, item["lat"], item["lon"])
            if dist > radius_km:
                continue

            # Generate deterministic UUID based on provider_record_id
            comp_uuid = str(uuid5(NAMESPACE_DNS, item["provider_record_id"]))

            record = ComparableRecord(
                comp_id=comp_uuid,
                source_id=1,
                source_name="synthetic_provider",
                provider_record_id=item["provider_record_id"],
                address=item["address"],
                locality=item["locality"],
                city=item["city"],
                state_code=item["state_code"],
                property_type=item["property_type"],
                sale_price=item["sale_price"],
                currency="INR",
                sale_date=item["sale_date"],
                living_area_sqft=item["living_area_sqft"],
                price_per_sqft=round(item["sale_price"] / item["living_area_sqft"], 2),
                price_type=item["price_type"],
                area_basis=item["area_basis"],
                license_scope="synthetic_internal",
                clean_flags=[],
                distance_km=dist,
                is_synthetic=True,
                raw=item,
            )
            results.append(record)

        # Sort by distance
        results.sort(key=lambda c: (c.distance_km if c.distance_km is not None else 999.0))
        return results
