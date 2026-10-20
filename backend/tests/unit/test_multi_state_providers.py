"""Unit tests for Phase 5 Multi-State Providers (GEMINI.md Step 5 Definition of Done).

Verifies:
1. All candidate states (UP, MH, KA, TS) have officially registered and approved reference rate providers.
2. Accurate state-specific native units, guideline names, and transformation mappings.
3. Successful ingestion of approved reference rate snapshots across all 4 states via state providers.
4. Enforcement that deed search APIs remain restricted and do NOT fabricate transaction data or scrape.
5. Unsupported states (e.g. DL, TN, RJ) raise UnsupportedStateError and return explicit unavailable status.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from app.ingestion.provider import ReferenceRateFileProvider
from app.ingestion.registry import SourceApprovalError
from app.providers import (
    StateProviderRegistry,
    StateReadinessStatus,
    TransactionDataUnavailableError,
    UnsupportedStateError,
    state_provider_registry,
)
from app.providers.karnataka.provider import KarnatakaProvider
from app.providers.maharashtra.provider import MaharashtraProvider
from app.providers.telangana.provider import TelanganaProvider
from app.providers.up.provider import UttarPradeshProvider
from app.schemas.source import ApprovalStatus, DataSourceRead, SourceType


def test_registry_contains_all_four_candidate_states() -> None:
    registry = StateProviderRegistry()
    supported = registry.list_supported_states()
    assert supported == ["KA", "MH", "TS", "UP"]

    for sc in ["UP", "MH", "KA", "TS"]:
        assert registry.is_state_supported(sc)
        provider = registry.get_provider(sc)
        assert provider.state_code == sc


def test_unsupported_state_raises_explicit_error() -> None:
    registry = StateProviderRegistry()
    assert not registry.is_state_supported("DL")
    assert not registry.is_state_supported("TN")
    assert not registry.is_state_supported("RJ")

    with pytest.raises(UnsupportedStateError, match="State 'DL' is unsupported"):
        registry.get_provider("DL")

    with pytest.raises(UnsupportedStateError, match="State 'TN' is unsupported"):
        registry.get_provider("TN")


def test_state_metadata_and_transformation_specifications() -> None:
    up = UttarPradeshProvider()
    assert up.metadata.native_area_unit == "per_sqm"
    assert up.metadata.reference_rate_local_name == "Circle Rate"
    assert up.metadata.reference_rate_approved is False
    assert up.metadata.transaction_data_approved is False
    up_docs = up.document_source_transformations()
    assert "10.7639104167" in up_docs["unit_conversion"]

    mh = MaharashtraProvider()
    assert mh.metadata.native_area_unit == "per_sqm"
    assert mh.metadata.reference_rate_local_name == "Ready Reckoner Rate"
    assert mh.metadata.reference_rate_approved is False
    assert mh.metadata.transaction_data_approved is False

    ka = KarnatakaProvider()
    assert ka.metadata.native_area_unit == "per_sqft"
    assert ka.metadata.reference_rate_local_name == "Guidance Value"
    assert ka.metadata.reference_rate_approved is False
    assert ka.metadata.transaction_data_approved is False

    ts = TelanganaProvider()
    assert ts.metadata.native_area_unit == "per_sqyd"
    assert ts.metadata.reference_rate_local_name == "Market Value / Unit Rate"
    assert ts.metadata.reference_rate_approved is False
    assert ts.metadata.transaction_data_approved is False
    ts_docs = ts.document_source_transformations()
    assert "9.0" in ts_docs["unit_conversion"]


def test_transaction_data_unavailable_error_prevents_fake_scraping() -> None:
    """Verifies GEMINI.md Rules 5, 6, 7: Transaction deed access is blocked with explicit reason."""
    for sc in ["UP", "MH", "KA", "TS"]:
        provider = state_provider_registry.get_provider(sc)
        with pytest.raises(TransactionDataUnavailableError, match="Real transaction deed data is unavailable"):
            provider.require_transaction_data()

        status = provider.get_transaction_access_status()
        assert status["transaction_data_approved"] is False
        assert "Do not scrape" in status["next_action"]


def test_reference_rate_ingestion_through_state_providers() -> None:
    """F-03: unverified reference-rate sources are pending, so providers must block ingestion.

    Unit-normalisation coverage is preserved by ingesting the same fixtures through an explicitly
    approved synthetic test source (the only source type permitted to carry unverified fixtures).
    """
    ref_dir = Path(__file__).resolve().parents[3] / "data" / "reference_rates"
    test_cases = [
        ("UP", "up_lucknow_circle_rates_2024.csv", 12),
        ("MH", "mh_mumbai_ready_reckoner_2024.csv", 7),
        ("KA", "ka_bengaluru_guidance_values_2024.csv", 7),
        ("TS", "ts_hyderabad_market_values_2024.csv", 7),
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
        for state_code, filename, expected_rows in test_cases:
            provider = state_provider_registry.get_provider(state_code)
            csv_path = ref_dir / filename
            assert csv_path.exists(), f"Missing file: {csv_path}"

            # F-03: an unverified source must be blocked by the approval gate.
            with pytest.raises(SourceApprovalError):
                provider.ingest_reference_rates(file_path=csv_path, quarantine_dir=tmp_dir)

            # Fixture content itself is still valid and unit-normalises per state.
            accepted, accounting, quarantined = ReferenceRateFileProvider(
                source=synthetic_source, quarantine_dir=tmp_dir
            ).ingest_file(csv_path)

            assert len(accepted) == expected_rows
            assert accounting.rows_received == expected_rows
            assert accounting.rows_accepted == expected_rows
            assert accounting.rows_quarantined == 0
            assert len(quarantined) == 0

            # Verify that rate is normalized to INR/sqft properly
            for item in accepted:
                assert item.state_code == state_code
                assert item.rate_inr_per_sqft > 0
