"""Unit tests for Ingestion Pipeline (GEMINI.md Phase 3 / Step 3 Definition of Done).

Verifies:
1. Source approval gate enforcement (unapproved sources raise SourceApprovalError).
2. Deterministic snapshot SHA-256 hash generation and provenance tracking.
3. Successful ingestion of approved real reference rate sample (Lucknow 2024).
4. Strict quarantine routing and reason code categorization (MISSING_PRICE, INVALID_UNIT, INVALID_DATE, PROVENANCE_MISSING).
5. Idempotent repeat imports: 2nd import creates 0 duplicates and marks rows as duplicate.
6. Exact row accounting invariant: rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected.
"""

from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from app.ingestion.deduplicate import DeduplicationIndex, generate_reference_rate_key
from app.ingestion.provider import ReferenceRateFileProvider, compute_sha256
from app.ingestion.quarantine import QuarantineReason
from app.ingestion.registry import SourceApprovalError, SourceRegistry
from app.ingestion.validate import validate_reference_rate_row, validate_transaction_row
from app.schemas.source import ApprovalStatus, DataSourceRead, SourceType
from app.schemas.transaction import ReferenceRateCreate


@pytest.fixture
def sample_csv_path() -> Path:
    p = Path(__file__).resolve().parents[3] / "data" / "reference_rates" / "up_lucknow_circle_rates_2024.csv"
    assert p.exists(), f"Sample CSV not found at {p}"
    return p


@pytest.fixture
def approved_source() -> DataSourceRead:
    return DataSourceRead(
        source_id=uuid4(),
        source_name="IGRSUP Circle Rate Services",
        state_code="UP",
        source_type=SourceType.GOVERNMENT,
        official_url="https://igrsup.gov.in/",
        access_method="downloadable file",
        license_scope="Category: reference_rate; Commercial allowed: false",
        approval_status=ApprovalStatus.APPROVED,
    )


@pytest.fixture
def unapproved_source() -> DataSourceRead:
    return DataSourceRead(
        source_id=uuid4(),
        source_name="IGRSUP Deed Search & Property Search",
        state_code="UP",
        source_type=SourceType.GOVERNMENT,
        official_url="https://igrsup.gov.in/",
        access_method="unknown",
        license_scope="Restricted",
        approval_status=ApprovalStatus.REJECTED,
    )


def test_source_approval_gate_blocks_unapproved_source(
    unapproved_source: DataSourceRead, sample_csv_path: Path
) -> None:
    provider = ReferenceRateFileProvider(source=unapproved_source)
    with pytest.raises(SourceApprovalError, match="is not approved"):
        provider.ingest_file(sample_csv_path)


def test_sha256_snapshot_hash_generation() -> None:
    content_a = "state_code,district,locality\nUP,Lucknow,Gomti Nagar"
    content_b = "state_code,district,locality\nUP,Lucknow,Indira Nagar"

    hash_a1 = compute_sha256(content_a)
    hash_a2 = compute_sha256(content_a.encode("utf-8"))
    hash_b = compute_sha256(content_b)

    assert hash_a1 == hash_a2
    assert len(hash_a1) == 64
    assert hash_a1 != hash_b


def test_successful_permitted_reference_rate_import(
    approved_source: DataSourceRead, sample_csv_path: Path
) -> None:
    with TemporaryDirectory() as tmp_dir:
        provider = ReferenceRateFileProvider(source=approved_source, quarantine_dir=tmp_dir)
        accepted, accounting, quarantined = provider.ingest_file(sample_csv_path)

        assert len(accepted) == 12
        assert accounting.rows_received == 12
        assert accounting.rows_accepted == 12
        assert accounting.rows_quarantined == 0
        assert accounting.rows_duplicate == 0
        assert accounting.rows_rejected == 0
        assert len(quarantined) == 0

        # Check normalization: Gomti Nagar rate_raw=54000 per_sqm -> ~5016.76 per sqft
        gomti = next(r for r in accepted if r.locality == "Gomti Nagar" and r.property_category == "residential_flat")
        assert gomti.rate_raw == 54000.0
        assert gomti.rate_unit_raw == "per_sqm"
        assert gomti.rate_inr_per_sqft == round(54000.0 / 10.7639104167, 2)
        assert gomti.state_code == "UP"
        assert gomti.district == "Lucknow"


def test_repeat_import_idempotency_zero_duplicates(
    approved_source: DataSourceRead, sample_csv_path: Path
) -> None:
    with TemporaryDirectory() as tmp_dir:
        dedup_index = DeduplicationIndex()
        provider = ReferenceRateFileProvider(
            source=approved_source, dedup_index=dedup_index, quarantine_dir=tmp_dir
        )

        # Pass 1: Fresh import
        accepted_1, acc_1, _ = provider.ingest_file(sample_csv_path)
        assert len(accepted_1) == 12
        assert acc_1.rows_accepted == 12
        assert acc_1.rows_duplicate == 0

        # Pass 2: Repeat import of the exact same snapshot
        accepted_2, acc_2, _ = provider.ingest_file(sample_csv_path)
        assert len(accepted_2) == 0  # Zero new records accepted!
        assert acc_2.rows_received == 12
        assert acc_2.rows_accepted == 0
        assert acc_2.rows_duplicate == 12  # All recognized as duplicates!
        assert acc_2.rows_quarantined == 0


def test_quarantine_routing_and_reason_codes(approved_source: DataSourceRead) -> None:
    # Build a test CSV with deliberate data defects
    bad_csv_content = (
        "state_code,district,locality,property_category,rate_raw,rate_unit_raw,effective_from,source_url\n"
        "UP,Lucknow,Valid Nagar,residential_flat,50000.0,per_sqm,2024-04-01,https://example.gov\n"  # Valid
        "UP,Lucknow,Missing Price Nagar,residential_flat,,per_sqm,2024-04-01,https://example.gov\n"  # MISSING_PRICE
        "UP,Lucknow,Negative Rate Nagar,residential_flat,-5000,per_sqm,2024-04-01,https://example.gov\n"  # MISSING_PRICE
        "UP,Lucknow,Invalid Unit Nagar,residential_flat,40000,per_acre,2024-04-01,https://example.gov\n"  # INVALID_UNIT
        "UP,Lucknow,Invalid Date Nagar,residential_flat,40000,per_sqm,not-a-date,https://example.gov\n"  # INVALID_DATE
        ",,No Locality Nagar,residential_flat,40000,per_sqm,2024-04-01,https://example.gov\n"  # PROVENANCE_MISSING
    )

    with TemporaryDirectory() as tmp_dir:
        tmp_csv = Path(tmp_dir) / "test_defects.csv"
        tmp_csv.write_text(bad_csv_content, encoding="utf-8")

        provider = ReferenceRateFileProvider(source=approved_source, quarantine_dir=tmp_dir)
        accepted, accounting, quarantined = provider.ingest_file(tmp_csv)

        assert len(accepted) == 1
        assert accepted[0].locality == "Valid Nagar"
        assert len(quarantined) == 5

        # Check reason codes
        reason_codes = [qr.reason_code for qr in quarantined]
        assert QuarantineReason.MISSING_PRICE in reason_codes
        assert QuarantineReason.INVALID_UNIT in reason_codes
        assert QuarantineReason.INVALID_DATE in reason_codes
        assert QuarantineReason.PROVENANCE_MISSING in reason_codes

        # Invariant check: 6 received == 1 accepted + 5 quarantined + 0 duplicate + 0 rejected
        assert accounting.rows_received == 6
        assert accounting.rows_accepted == 1
        assert accounting.rows_quarantined == 5
        assert accounting.rows_duplicate == 0
        assert accounting.rows_rejected == 0

        # Check that quarantine log file was created
        quarantine_files = list(Path(tmp_dir).glob("quarantine_*.jsonl"))
        assert len(quarantine_files) == 1
        assert len(quarantine_files[0].read_text(encoding="utf-8").strip().splitlines()) == 5


def test_transaction_validation_blocks_asking_price() -> None:
    source_id = uuid4()
    run_id = uuid4()

    # Asking price submitted to transaction validator -> must be quarantined with PRICE_TYPE_NOT_ELIGIBLE
    raw_tx = {
        "source_transaction_id": "TX-101",
        "transaction_date": "2025-05-10",
        "transaction_price_raw": 6500000.0,
        "transaction_price_unit_raw": "INR",
        "price_type": "asking",  # Ineligible price type!
        "source_url": "https://example.com/listing/1",
    }
    model, quarantine_rec = validate_transaction_row(
        raw_row=raw_tx,
        source_id=source_id,
        run_id=run_id,
        source_snapshot_hash="f" * 32,
    )
    assert model is None
    assert quarantine_rec is not None
    assert quarantine_rec.reason_code == QuarantineReason.PRICE_TYPE_NOT_ELIGIBLE


def test_transaction_validation_requires_source_url() -> None:
    """F-16: a missing source_url must be quarantined, never defaulted to a fake URL."""
    source_id = uuid4()
    run_id = uuid4()

    base_tx = {
        "source_transaction_id": "TX-202",
        "transaction_date": "2025-05-10",
        "transaction_price_raw": 6500000.0,
        "transaction_price_unit_raw": "INR",
        "price_type": "sale_consideration",
    }

    # Missing source_url -> PROVENANCE_MISSING (no fabricated fallback).
    model, quarantine_rec = validate_transaction_row(
        raw_row=dict(base_tx),
        source_id=source_id,
        run_id=run_id,
        source_snapshot_hash="f" * 32,
    )
    assert model is None
    assert quarantine_rec is not None
    assert quarantine_rec.reason_code == QuarantineReason.PROVENANCE_MISSING

    # A real source_url still validates and is preserved verbatim.
    model_ok, quarantine_ok = validate_transaction_row(
        raw_row={**base_tx, "source_url": "https://example.gov/tx/202"},
        source_id=source_id,
        run_id=run_id,
        source_snapshot_hash="f" * 32,
    )
    assert quarantine_ok is None
    assert model_ok is not None
    assert model_ok.source_url == "https://example.gov/tx/202"


def test_validators_never_return_none_none() -> None:
    """F-15: every validator outcome is either (model, None) or (None, quarantine) — never both None."""
    source_id = uuid4()
    run_id = uuid4()
    snapshot_hash = "f" * 32

    reference_rate_rows = [
        {  # valid
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "Valid Nagar",
            "property_category": "residential_flat",
            "rate_raw": 50000.0,
            "rate_unit_raw": "per_sqm",
            "effective_from": "2024-04-01",
            "source_url": "https://example.gov",
        },
        {},  # everything missing
        {  # bad unit
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "X",
            "rate_raw": 40000.0,
            "rate_unit_raw": "per_acre",
            "effective_from": "2024-04-01",
            "source_url": "https://example.gov",
        },
        {  # bad date
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "X",
            "rate_raw": 40000.0,
            "rate_unit_raw": "per_sqm",
            "effective_from": "not-a-date",
            "source_url": "https://example.gov",
        },
        {  # missing source_url
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "X",
            "rate_raw": 40000.0,
            "rate_unit_raw": "per_sqm",
            "effective_from": "2024-04-01",
        },
    ]

    transaction_rows = [
        {  # valid
            "source_transaction_id": "TX-1",
            "transaction_date": "2025-05-10",
            "transaction_price_raw": 6500000.0,
            "transaction_price_unit_raw": "INR",
            "price_type": "sale_consideration",
            "source_url": "https://example.gov/tx/1",
        },
        {},  # everything missing
        {  # asking price
            "source_transaction_id": "TX-2",
            "transaction_date": "2025-05-10",
            "transaction_price_raw": 6500000.0,
            "transaction_price_unit_raw": "INR",
            "price_type": "asking",
            "source_url": "https://example.gov/tx/2",
        },
    ]

    for row in reference_rate_rows:
        model, quarantine = validate_reference_rate_row(row, source_id, run_id, snapshot_hash)
        assert (model is None) != (quarantine is None), f"reference-rate row not accounted: {row}"

    for row in transaction_rows:
        model, quarantine = validate_transaction_row(row, source_id, run_id, snapshot_hash)
        assert (model is None) != (quarantine is None), f"transaction row not accounted: {row}"


def test_multi_state_reference_rate_ingestion_all_four_states() -> None:
    """F-03: the four reference-rate sources are unverified (pending_review) and must be blocked.

    Fixture content remains ingestible through an explicitly approved synthetic test source so that
    row-accounting and normalisation coverage is preserved.
    """
    from app.ingestion.registry import default_registry

    ref_dir = Path(__file__).resolve().parents[3] / "data" / "reference_rates"
    states_to_test = [
        ("UP", "IGRSUP Circle Rate Services", "up_lucknow_circle_rates_2024.csv", 12),
        ("MH", "IGR Maharashtra eASR (Ready Reckoner Rates)", "mh_mumbai_ready_reckoner_2024.csv", 7),
        ("KA", "Kaveri 2.0 Guidance Value Services", "ka_bengaluru_guidance_values_2024.csv", 7),
        ("TS", "IGRS Telangana Market Value & Unit Rates", "ts_hyderabad_market_values_2024.csv", 7),
    ]

    synthetic_source = DataSourceRead(
        source_id=uuid4(),
        source_name="Synthetic Multi-State Reference Rate Fixture",
        state_code="ALL",
        source_type=SourceType.SYNTHETIC_TEST,
        official_url="local://synthetic/reference_rates",
        access_method="manual authorized export",
        license_scope="Synthetic dev fixture; not real market evidence",
        approval_status=ApprovalStatus.APPROVED,
    )

    with TemporaryDirectory() as tmp_dir:
        for state_code, source_name, filename, expected_rows in states_to_test:
            # F-03: unverified reference-rate sources must not be approved nor ingestible.
            with pytest.raises(SourceApprovalError):
                default_registry.verify_approval(state_code, source_name)

            csv_file = ref_dir / filename
            assert csv_file.exists(), f"Missing file: {csv_file}"

            dedup = DeduplicationIndex()
            provider = ReferenceRateFileProvider(
                source=synthetic_source, dedup_index=dedup, quarantine_dir=tmp_dir
            )
            accepted, accounting, quarantined = provider.ingest_file(csv_file)

            assert len(accepted) == expected_rows
            assert accounting.rows_received == expected_rows
            assert accounting.rows_accepted == expected_rows
            assert accounting.rows_quarantined == 0
            assert accounting.rows_duplicate == 0

            # Verify that normalized INR rate is present and greater than 0
            for r in accepted:
                assert r.state_code == state_code
                assert r.rate_inr_per_sqft is not None
                assert r.rate_inr_per_sqft > 0

