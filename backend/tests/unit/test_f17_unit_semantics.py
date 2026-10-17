"""F-17 regression tests: rate fields must name (and document) their unit basis.

Verifies (Phase 2, Priority 3 — F-17):
1. The canonical reference-rate contract field is named ``rate_inr_per_sqft`` (not the
   ambiguous ``rate_inr_normalized``) and documents the square-foot basis.
2. The circle-rate lookup field ``rate_per_sqm`` documents the square-metre basis.
3. A known fixture's normalized value matches its field name (per sq ft != per sq m).
4. The circle-rate ingestion default property type matches the API default
   (``residential_flat``), fixing the ``residential`` vs ``residential_flat`` mismatch.
5. The physical/ORM column keeps its historical name (no migration required) but is
   documented with the square-foot basis.
6. Generated processed fixtures use the new field name.
"""

from __future__ import annotations

import inspect
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from app.api.circle_rates import lookup_circle_rate
from app.database.models.reference_rate import ReferenceRate
from app.ingestion.circle_rates import DEFAULT_PROPERTY_TYPE, _normalize_row
from app.ingestion.normalize import SQM_TO_SQFT
from app.schemas.circle_rate import CircleRateLookup
from app.schemas.transaction import ReferenceRateCreate, ReferenceRateRead

REPO_ROOT = Path(__file__).resolve().parents[3]


# =========================================================================
# 1 & 2. Field names and documented units
# =========================================================================


def test_reference_rate_contract_field_names_its_basis() -> None:
    fields = ReferenceRateCreate.model_fields
    assert "rate_inr_per_sqft" in fields
    assert "rate_inr_normalized" not in fields
    # The basis is documented explicitly (square foot, not square metre).
    description = fields["rate_inr_per_sqft"].description or ""
    assert "square foot" in description.lower()
    assert "square metre" in description.lower()  # states what it is NOT
    assert "rate_inr_per_sqft" in ReferenceRateRead.model_fields


def test_circle_rate_lookup_field_documents_per_sqm() -> None:
    field = CircleRateLookup.model_fields["rate_per_sqm"]
    description = (field.description or "").lower()
    assert "square metre" in description


# =========================================================================
# 3. A known fixture's normalized unit matches its field name
# =========================================================================


def test_served_unit_matches_field_name_for_known_fixture() -> None:
    # Known fixture: UP / Lucknow / Gomti Nagar notified at 54,000 INR per sq m.
    rate_per_sqm_raw = 54000.0
    expected_per_sqft = round(rate_per_sqm_raw / SQM_TO_SQFT, 2)

    record = ReferenceRateCreate(
        source_id=uuid4(),
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        property_category="residential_flat",
        rate_raw=rate_per_sqm_raw,
        rate_unit_raw="per_sqm",
        rate_inr_per_sqft=expected_per_sqft,
        effective_from=date(2024, 4, 1),
        source_url="local://synthetic/reference_rates/up_lucknow_circle_rates_2024.csv",
        source_record_hash="a" * 32,
    )

    # The value carried by `rate_inr_per_sqft` must equal the per-square-foot figure and
    # must NOT equal the per-square-metre input (i.e. the unit matches the field name).
    assert record.rate_inr_per_sqft == expected_per_sqft
    assert record.rate_inr_per_sqft != rate_per_sqm_raw
    assert record.rate_raw == rate_per_sqm_raw
    assert record.rate_unit_raw == "per_sqm"


# =========================================================================
# 4. Ingestion and API defaults agree on the canonical property type
# =========================================================================


def test_circle_rate_ingestion_default_property_type_is_canonical() -> None:
    row = {
        "district": "Lucknow",
        "tehsil": "Lucknow Sadar",
        "locality": "Gomti Nagar",
        "circle rate per sqm": "54,000",
        "effective year": "2024",
    }
    normalized = _normalize_row(row, "UP", "Lucknow", "https://igrsup.gov.in/rates")
    assert normalized is not None
    assert normalized["property_type"] == DEFAULT_PROPERTY_TYPE == "residential_flat"


def test_api_lookup_default_property_type_is_canonical() -> None:
    param = inspect.signature(lookup_circle_rate).parameters["property_type"]
    assert param.default.default == "residential_flat"


# =========================================================================
# 5. ORM/DB column is documented (historical name retained, no migration needed)
# =========================================================================


def test_orm_column_retains_name_with_documented_foot_basis() -> None:
    assert "rate_inr_normalized" in ReferenceRate.__table__.c
    column = ReferenceRate.__table__.c["rate_inr_normalized"]
    assert "square foot" in (column.comment or "").lower()


# =========================================================================
# 6. Generated processed fixtures use the new contract name
# =========================================================================


def test_processed_reference_rate_fixtures_use_new_field_name() -> None:
    fixture = (
        REPO_ROOT
        / "data"
        / "processed"
        / "reference_rates"
        / "up_lucknow_circle_rates_2024.jsonl"
    )
    assert fixture.exists(), f"missing fixture: {fixture}"
    first = json.loads(fixture.read_text(encoding="utf-8").splitlines()[0])
    assert "rate_inr_per_sqft" in first
    assert "rate_inr_normalized" not in first
