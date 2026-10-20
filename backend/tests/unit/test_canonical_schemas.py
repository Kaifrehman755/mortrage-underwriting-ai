"""Unit tests for Canonical Pydantic v2 schemas and normalization rules.

Verifies Definition of Done for Step 2 in GEMINI.md:
- Strict schema validation & predictable failures on invalid inputs.
- Provenance and source approval gating.
- Lakh and crore conversions.
- Square metre (10.7639104167) and square yard (9.0) conversions.
- Area-basis compatibility checks (carpet vs built_up vs unknown).
- Ingestion accounting invariant verification.
- Valuation bounds and reason codes.
"""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.ingestion.normalize import (
    SQM_TO_SQFT,
    SQYD_TO_SQFT,
    calculate_price_per_sqft,
    normalize_area_sqft,
    normalize_inr_price,
)
from app.ingestion.quarantine import IngestionRunAccounting, QuarantineReason, QuarantineRecord
from app.schemas.property import (
    AreaType,
    PropertyRecordCreate,
    PropertyType,
    SourceAuthenticityStatus,
)
from app.schemas.source import ApprovalStatus, DataSourceCreate, SourceType
from app.schemas.transaction import (
    PriceType,
    PropertyListingCreate,
    PropertyTransactionCreate,
    ReferenceRateCreate,
    TransactionVerificationStatus,
)
from app.schemas.valuation import ValuationRunCreate, ValuationStatus


# =============================================================================
# 1. Unit Conversion Tests (GEMINI.md Section 5)
# =============================================================================


def test_normalize_inr_price_lakh_and_crore() -> None:
    # 1 Lakh = 100,000 INR
    assert normalize_inr_price("75 Lakh") == 7500000.0
    assert normalize_inr_price(75.0, raw_unit="lakh") == 7500000.0
    assert normalize_inr_price("85.5 lac") == 8550000.0

    # 1 Crore = 10,000,000 INR
    assert normalize_inr_price("1.25 Crore") == 12500000.0
    assert normalize_inr_price("2.5 cr") == 25000000.0
    assert normalize_inr_price(3, raw_unit="crore") == 30000000.0

    # Direct Indian formatted numbers
    assert normalize_inr_price("₹ 50,00,000") == 5000000.0
    assert normalize_inr_price("10000000") == 10000000.0


def test_normalize_inr_price_rejects_invalid() -> None:
    assert normalize_inr_price(None) is None
    assert normalize_inr_price(0) is None
    assert normalize_inr_price(-5000) is None
    assert normalize_inr_price("invalid text") is None
    assert normalize_inr_price("NaN") is None


def test_normalize_area_sqft_conversions() -> None:
    # Direct sqft
    assert normalize_area_sqft(1200, "sqft") == 1200.0

    # 1 sqm = 10.7639104167 sqft
    converted_sqm = normalize_area_sqft(100.0, "sqm")
    assert converted_sqm == round(100.0 * SQM_TO_SQFT, 4)

    # 1 sqyd = 9.0 sqft
    converted_sqyd = normalize_area_sqft(200.0, "sqyd")
    assert converted_sqyd == 1800.0

    # Gaj is equivalent to sqyd in Indian real estate
    assert normalize_area_sqft(150.0, "gaj") == 1350.0


def test_normalize_area_sqft_rejects_unknown_units_or_invalid_values() -> None:
    # Rule 1: Never infer an unknown unit from numeric value alone
    assert normalize_area_sqft(1200, None) is None
    assert normalize_area_sqft(1200, "furlongs") is None
    assert normalize_area_sqft(-100, "sqft") is None
    assert normalize_area_sqft(0, "sqm") is None


def test_calculate_price_per_sqft_enforces_area_compatibility() -> None:
    # Compatible areas (carpet to carpet)
    pps = calculate_price_per_sqft(
        price_inr=5000000.0,
        area_sqft=1000.0,
        subject_area_type=AreaType.CARPET,
        comp_area_type=AreaType.CARPET,
    )
    assert pps == 5000.0

    # Incompatible: Carpet vs Built-up must NOT compute
    incompatible = calculate_price_per_sqft(
        price_inr=5000000.0,
        area_sqft=1000.0,
        subject_area_type=AreaType.CARPET,
        comp_area_type=AreaType.BUILT_UP,
    )
    assert incompatible is None

    # Incompatible: Unknown area type must NOT compute
    assert (
        calculate_price_per_sqft(
            price_inr=5000000.0,
            area_sqft=1000.0,
            subject_area_type=AreaType.CARPET,
            comp_area_type=AreaType.UNKNOWN,
        )
        is None
    )


# =============================================================================
# 2. Canonical Schemas & Constraint Tests (GEMINI.md Section 4)
# =============================================================================


def test_data_source_schema_validation() -> None:
    ds = DataSourceCreate(
        source_name="IGRSUP Circle Rates",
        state_code="UP",
        source_type=SourceType.GOVERNMENT,
        official_url="https://igrsup.gov.in/",
        access_method="downloadable file",
        license_scope="Official public rate schedule; evaluation permitted",
        approval_status=ApprovalStatus.PENDING_REVIEW,
    )
    assert ds.source_name == "IGRSUP Circle Rates"
    assert ds.approval_status == ApprovalStatus.PENDING_REVIEW

    # Disallow extra fields
    with pytest.raises(ValidationError):
        DataSourceCreate(
            source_name="Extra",
            state_code="UP",
            source_type=SourceType.GOVERNMENT,
            official_url="https://igrsup.gov.in/",
            access_method="downloadable file",
            license_scope="scope",
            unexpected_field="disallowed",
        )


def test_property_record_validates_pincode_and_coordinates() -> None:
    source_id = uuid4()
    # Valid record
    rec = PropertyRecordCreate(
        source_id=source_id,
        source_record_id="REC-001",
        state_code="UP",
        district="Lucknow",
        city="Lucknow",
        locality="Gomti Nagar",
        pincode="226010",
        property_type=PropertyType.APARTMENT,
        area_value_raw=1250.0,
        area_unit_raw="sqft",
        area_sqft=1250.0,
        area_type=AreaType.CARPET,
        latitude=26.8530,
        longitude=80.9980,
        source_url="https://example.gov/rec/1",
        source_record_hash="a" * 32,
    )
    assert rec.pincode == "226010"

    # Invalid Indian PIN code (not 6 digits)
    with pytest.raises(ValidationError, match="Indian PIN code must be exactly 6 digits"):
        PropertyRecordCreate(
            source_id=source_id,
            source_record_id="REC-002",
            state_code="UP",
            district="Lucknow",
            city="Lucknow",
            locality="Gomti Nagar",
            pincode="22601",  # 5 digits -> invalid
            area_value_raw=1000.0,
            area_unit_raw="sqft",
            source_url="https://example.gov/rec/2",
            source_record_hash="b" * 32,
        )


def test_separation_of_transactions_and_reference_rates() -> None:
    source_id = uuid4()

    # PropertyTransaction represents actual consideration
    tx = PropertyTransactionCreate(
        source_id=source_id,
        source_transaction_id="TX-999",
        transaction_date=date(2025, 6, 15),
        transaction_price_raw=7500000.0,
        transaction_price_unit_raw="INR",
        transaction_price_inr=7500000.0,
        price_type=PriceType.SALE_CONSIDERATION,
        transaction_verification_status=TransactionVerificationStatus.VERIFIED,
        source_url="https://example.gov/tx/999",
        source_record_hash="c" * 32,
    )
    assert tx.price_type == PriceType.SALE_CONSIDERATION

    # ReferenceRate stores circle rate / guidance value benchmark
    ref = ReferenceRateCreate(
        source_id=source_id,
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        property_category="residential_flat",
        rate_raw=54000.0,
        rate_unit_raw="per_sqm",
        rate_inr_per_sqft=round(54000.0 / SQM_TO_SQFT, 2),
        effective_from=date(2024, 4, 1),
        source_url="https://igrsup.gov.in/rates",
        source_record_hash="d" * 32,
    )
    assert ref.rate_raw == 54000.0


def test_valuation_run_bounds_and_abstention_invariants() -> None:
    # Completed valuation requires estimate within bounds
    vr = ValuationRunCreate(
        subject_property_input={"locality": "Gomti Nagar", "sqft": 1250},
        estimate_inr=7500000.0,
        lower_bound_inr=7000000.0,
        upper_bound_inr=8000000.0,
        status=ValuationStatus.COMPLETED,
        method_version="1.0.0",
        dataset_cutoff=date(2026, 1, 1),
    )
    assert vr.status == ValuationStatus.COMPLETED

    # Completed valuation with inverted bounds must fail
    with pytest.raises(ValidationError, match="lower_bound_inr .* cannot exceed upper_bound_inr"):
        ValuationRunCreate(
            subject_property_input={"locality": "Gomti Nagar"},
            estimate_inr=7500000.0,
            lower_bound_inr=8500000.0,
            upper_bound_inr=7000000.0,
            status=ValuationStatus.COMPLETED,
            method_version="1.0.0",
            dataset_cutoff=date(2026, 1, 1),
        )

    # Abstained valuation must provide reason codes
    with pytest.raises(ValidationError, match="must provide at least one reason code"):
        ValuationRunCreate(
            subject_property_input={"locality": "Unknown"},
            status=ValuationStatus.ABSTAINED,
            reason_codes=[],  # Empty reason codes -> invalid!
            method_version="1.0.0",
            dataset_cutoff=date(2026, 1, 1),
        )


def test_ingestion_accounting_invariant() -> None:
    run_id = uuid4()
    source_id = uuid4()

    # Valid accounting: received == accepted + quarantined + duplicate + rejected
    acc = IngestionRunAccounting(
        run_id=run_id,
        source_id=source_id,
        build_version="1.0.0",
        source_snapshot_hash="e" * 32,
        rows_received=100,
        rows_accepted=75,
        rows_quarantined=15,
        rows_duplicate=5,
        rows_rejected=5,
        finished_at=datetime.now(UTC),
    )
    assert acc.rows_received == 100

    # Invariant violation: 100 received != 70 + 15 + 5 + 5 = 95
    with pytest.raises(ValidationError, match="Row accounting invariant violated"):
        IngestionRunAccounting(
            run_id=run_id,
            source_id=source_id,
            build_version="1.0.0",
            source_snapshot_hash="e" * 32,
            rows_received=100,
            rows_accepted=70,
            rows_quarantined=15,
            rows_duplicate=5,
            rows_rejected=5,
            finished_at=datetime.now(UTC),
        )
