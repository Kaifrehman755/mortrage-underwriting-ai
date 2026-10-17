"""Jurisdiction configuration packs for multi-state property underwriting.

Adheres to Playbook Section 14 (Lucknow pilot), Section 15 (Multi-state design),
and Section 18.5 (State recon).
"""

from pydantic import BaseModel, Field


class AreaUnitsConfig(BaseModel):
    """Conversion multipliers from unit to square feet."""
    sq_ft: float = 1.0
    sq_m: float = 10.7639
    sq_yd: float = 9.0
    gaj: float = 9.0


class GuidelineValueConfig(BaseModel):
    local_name: str
    unit: str


class JurisdictionPack(BaseModel):
    state_code: str
    name: str
    status: str = Field(..., pattern=r"^(planned|pilot|live|paused)$")
    config_version: str = "2026-10-01"
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    guideline_value: GuidelineValueConfig
    area_units: AreaUnitsConfig = Field(default_factory=AreaUnitsConfig)
    min_comps_estimate: int = 3
    min_comps_interval: int = 5
    max_dispersion_cv: float = 0.35
    supported_property_types: list[str] = ["apartment", "residential_flat"]
    hpi_base_year: str = "2022-23"


# Official registry of jurisdiction packs
JURISDICTIONS: dict[str, JurisdictionPack] = {
    # Uttar Pradesh (Pilot State - Lucknow Pilot Box 26.6-27.1 N, 80.7-81.2 E)
    "UP": JurisdictionPack(
        state_code="UP",
        name="Uttar Pradesh",
        status="pilot",
        config_version="2026-10-01",
        lat_min=26.6,
        lat_max=27.1,
        lon_min=80.7,
        lon_max=81.2,
        guideline_value=GuidelineValueConfig(local_name="Circle rate", unit="per_sq_m"),
        area_units=AreaUnitsConfig(sq_ft=1.0, sq_m=10.7639, sq_yd=9.0, gaj=9.0),
        min_comps_estimate=3,
        min_comps_interval=5,
        max_dispersion_cv=0.35,
        supported_property_types=["apartment", "residential_flat"],
    ),
    # Maharashtra (Planned State - Mumbai / Pune)
    "MH": JurisdictionPack(
        state_code="MH",
        name="Maharashtra",
        status="planned",
        config_version="2026-10-01",
        lat_min=18.5,
        lat_max=19.5,
        lon_min=72.7,
        lon_max=73.9,
        guideline_value=GuidelineValueConfig(local_name="Ready Reckoner rate", unit="per_sq_m"),
        area_units=AreaUnitsConfig(sq_ft=1.0, sq_m=10.7639, sq_yd=9.0, gaj=9.0),
        min_comps_estimate=5,
        min_comps_interval=5,
        max_dispersion_cv=0.35,
        supported_property_types=["apartment", "residential_flat"],
    ),
    # Karnataka (Planned State - Bengaluru)
    "KA": JurisdictionPack(
        state_code="KA",
        name="Karnataka",
        status="planned",
        config_version="2026-10-01",
        lat_min=12.7,
        lat_max=13.3,
        lon_min=77.3,
        lon_max=77.9,
        guideline_value=GuidelineValueConfig(local_name="Guidance value", unit="per_sq_ft"),
        area_units=AreaUnitsConfig(sq_ft=1.0, sq_m=10.7639, sq_yd=9.0, gaj=9.0),
        min_comps_estimate=5,
        min_comps_interval=5,
        max_dispersion_cv=0.35,
        supported_property_types=["apartment", "residential_flat"],
    ),
    # Telangana (Planned State - Hyderabad)
    "TS": JurisdictionPack(
        state_code="TS",
        name="Telangana",
        status="planned",
        config_version="2026-10-01",
        lat_min=17.2,
        lat_max=17.6,
        lon_min=78.2,
        lon_max=78.6,
        guideline_value=GuidelineValueConfig(local_name="Basic market value", unit="per_sq_yd"),
        area_units=AreaUnitsConfig(sq_ft=1.0, sq_m=10.7639, sq_yd=9.0, gaj=9.0),
        min_comps_estimate=5,
        min_comps_interval=5,
        max_dispersion_cv=0.35,
        supported_property_types=["apartment", "residential_flat"],
    ),
}


def get_jurisdiction(state_code: str) -> JurisdictionPack:
    """Retrieve verified jurisdiction pack or raise KeyError."""
    state_norm = state_code.strip().upper()
    if state_norm not in JURISDICTIONS:
        raise ValueError(f"State '{state_code}' is unsupported. No jurisdiction pack found.")
    return JURISDICTIONS[state_norm]
