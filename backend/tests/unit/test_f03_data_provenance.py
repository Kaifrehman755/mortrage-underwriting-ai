"""F-03 regression tests: reference-rate provenance must never be fabricated or mislabelled.

Verifies (Phase 2, Priority 2):
1. Every reference-rate dataset in ``data/source_readiness.csv`` is NOT approved (pending review)
   and cannot pass the source approval gate.
2. Every reference-rate fixture row carries honest local/synthetic provenance instead of a
   fabricated official government URL.
3. Fixture SHA-256 hashes match the values recorded in ``data/DATA_CARD.md``.
4. ``DATA_CARD.md`` no longer describes the unverified fixtures as approved official snapshots.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from app.ingestion.registry import SourceApprovalError, SourceRegistry

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
READINESS_CSV = DATA_DIR / "source_readiness.csv"
DATA_CARD = DATA_DIR / "DATA_CARD.md"
FIXTURES_DIR = DATA_DIR / "reference_rates"

FIXTURES = [
    "up_lucknow_circle_rates_2024.csv",
    "mh_mumbai_ready_reckoner_2024.csv",
    "ka_bengaluru_guidance_values_2024.csv",
    "ts_hyderabad_market_values_2024.csv",
]


def _readiness_rows() -> list[dict[str, str]]:
    with READINESS_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _reference_rate_rows() -> list[dict[str, str]]:
    rows = [r for r in _readiness_rows() if r["data_category"] == "reference_rate"]
    assert rows, "Expected at least one reference_rate row in source_readiness.csv"
    return rows


def test_source_readiness_csv_is_well_formed() -> None:
    """Guards against unquoted commas silently shifting CSV columns (as seen during F-03)."""
    with READINESS_CSV.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        assert fieldnames, "source_readiness.csv has no header row"
        assert None not in fieldnames
        for row in reader:
            assert None not in row, (
                "Row has more fields than headers (unquoted comma inside a field?)"
            )
            assert all(value is not None for value in row.values())


def test_reference_rate_sources_are_not_approved() -> None:
    for row in _reference_rate_rows():
        assert row["decision"] == "pending_review", (
            f"{row['source_name']} must be marked pending_review"
        )
        assert row["license_review_status"] == "pending_review", (
            f"{row['source_name']} must not claim an approved license review"
        )


def test_approval_gate_blocks_unverified_reference_rate_sources() -> None:
    registry = SourceRegistry(READINESS_CSV)
    for row in _reference_rate_rows():
        with pytest.raises(SourceApprovalError):
            registry.verify_approval(row["state_code"], row["source_name"])


def test_fixture_rows_use_local_synthetic_provenance() -> None:
    fixture_dirs = [FIXTURES_DIR, DATA_DIR / "raw" / "reference_rates"]
    checked = 0
    for fixtures_dir in fixture_dirs:
        for path in sorted(fixtures_dir.glob("*.csv")):
            checked += 1
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    url = str(row.get("source_url", "")).strip()
                    assert url.startswith("local://synthetic/"), (
                        f"{path.name}: fabricated official provenance URL {url!r}"
                    )
                    assert "SYNTHETIC DEV FIXTURE" in str(row.get("notes", "")), (
                        f"{path.name}: missing synthetic provenance marker in notes"
                    )
    assert checked >= len(FIXTURES)


def test_fixture_hashes_match_data_card() -> None:
    card = DATA_CARD.read_text(encoding="utf-8")
    for name in FIXTURES:
        digest = hashlib.sha256((FIXTURES_DIR / name).read_bytes()).hexdigest()
        assert digest in card, f"{name}: SHA-256 {digest} not recorded in DATA_CARD.md"
        assert f"data/reference_rates/{name}" in card


def test_data_card_does_not_claim_approved_snapshots() -> None:
    card = DATA_CARD.read_text(encoding="utf-8")
    assert "Approved Multi-State Reference Rate Snapshots" not in card
    assert "UNVERIFIED" in card
