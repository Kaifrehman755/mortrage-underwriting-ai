"""F-02 regression tests: market-index provenance must never be invented.

Verifies (Phase 2, Priority 2):
1. The valuation engine no longer hard-codes an HPI series or an invented
   year-on-year growth figure.
2. The versioned market-index file carries source, publication date, units, base
   year and an explicit verification status.
3. An unverified or absent index abstains from the production time adjustment
   instead of inventing a value, and the output is flagged for human review.
4. A missing quarterly value is never replaced by a default constant.
5. A verified series (or an explicit synthetic opt-in) does enable the adjustment.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.property.market_index import (
    DEFAULT_MARKET_INDEX_FILE,
    load_market_index,
    period_for_date,
    prior_year_period,
)
from app.property.schemas import ComparableRecord, SubjectProperty
from app.property.valuation import PropertyValuationEngine, get_hpi_for_date

REPO_ROOT = Path(__file__).resolve().parents[3]
VALUATION_SRC = REPO_ROOT / "backend" / "app" / "property" / "valuation.py"

REQUIRED_PROVENANCE_FIELDS = (
    "source_name",
    "source_url",
    "publication_date",
    "units",
    "base_year",
    "verification_status",
    "series",
)


def _subject() -> SubjectProperty:
    return SubjectProperty(
        original_address="Flat 201, Gomti Nagar, Lucknow",
        address_norm="Flat 201 Gomti Nagar Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_sqft=1200.0,
        lat=26.85,
        lon=80.99,
    )


def _comp(
    rec_id: str,
    *,
    sale_date: str = "2026-05-01",
    ppsf: float = 5000.0,
    dist: float = 1.0,
) -> ComparableRecord:
    area = 1200.0
    return ComparableRecord(
        source_id=2,
        source_name="approved_provider",
        provider_record_id=rec_id,
        address=f"Real Comp {rec_id}",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        property_type="apartment",
        sale_price=ppsf * area,
        sale_date=sale_date,
        living_area_sqft=area,
        price_per_sqft=ppsf,
        price_type="registered_deed",
        license_scope="approved",
        distance_km=dist,
        is_synthetic=False,
    )


def _comps(n: int = 5, *, sale_date: str = "2026-05-01") -> list[ComparableRecord]:
    return [
        _comp(f"REAL-{i}", ppsf=5000.0 + i * 60, dist=0.9 + i * 0.1, sale_date=sale_date)
        for i in range(n)
    ]


def _write_index(path: Path, *, status: str, series: dict[str, float]) -> Path:
    payload = {
        "series_id": "test_index",
        "title": "test",
        "index_basis": "city",
        "base_year": "2022-23",
        "units": "index points",
        "source_name": "Reserve Bank of India HPI (test)",
        "source_url": "https://data.rbi.org.in/",
        "publication_date": "2026-08-24",
        "retrieved_at": "2026-10-17",
        "verification_status": status,
        "series": series,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# =========================================================================
# 1. Source-level guarantees against hard-coded / invented index data
# =========================================================================


def test_valuation_module_has_no_hardcoded_index_or_growth() -> None:
    """The engine must not carry an unprovenanced series or a magic YoY figure."""
    src = VALUATION_SRC.read_text(encoding="utf-8")
    assert "HPI_SERIES" not in src
    assert "CURRENT_HPI" not in src
    assert "8.2" not in src, "invented rbi_hpi_yoy_growth_percent constant still present"
    assert "118.2" not in src, "hard-coded HPI level still present"


def test_versioned_index_file_carries_provenance() -> None:
    assert DEFAULT_MARKET_INDEX_FILE.exists()
    payload = json.loads(DEFAULT_MARKET_INDEX_FILE.read_text(encoding="utf-8"))
    for field in REQUIRED_PROVENANCE_FIELDS:
        assert field in payload, f"market index missing required provenance field {field!r}"
    # The shipped fixture is unverified and must not masquerade as a verified series.
    assert payload["verification_status"] != "verified"


def test_loader_returns_none_for_missing_or_unparsable_file(tmp_path: Path) -> None:
    assert load_market_index(tmp_path / "does_not_exist.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_market_index(bad) is None


def test_shipped_index_is_not_production_usable() -> None:
    snapshot = load_market_index(DEFAULT_MARKET_INDEX_FILE)
    assert snapshot is not None
    assert snapshot.is_verified is False


# =========================================================================
# 2. Unverified / absent / partial index -> abstain, never invent
# =========================================================================


def test_unverified_index_abstains_from_time_adjustment_in_production() -> None:
    engine = PropertyValuationEngine(market_index_path=DEFAULT_MARKET_INDEX_FILE)
    vo = engine.valuate("case_f02_unverified", _subject(), _comps())

    assert vo.estimate is not None
    block = vo.market_indicators["market_index"]
    assert block["verification_status"] == "unverified"
    assert block["usable_for_time_adjustment"] is False
    assert block["time_adjustment_applied"] is False
    assert block["time_adjustment_abstained_reason"] == "market_index_unverified"
    assert vo.market_indicators["rbi_hpi_current"] is None
    assert vo.market_indicators["rbi_hpi_yoy_growth_percent"] is None
    assert vo.human_review_required is True


def test_absent_index_abstains_and_is_flagged(tmp_path: Path) -> None:
    engine = PropertyValuationEngine(market_index_path=tmp_path / "missing.json")
    vo = engine.valuate("case_f02_absent", _subject(), _comps())

    block = vo.market_indicators["market_index"]
    assert block["verification_status"] == "absent"
    assert block["time_adjustment_applied"] is False
    assert block["time_adjustment_abstained_reason"] == "market_index_unavailable"
    assert vo.market_indicators["rbi_hpi_current"] is None
    assert vo.human_review_required is True


def test_verified_index_enables_time_adjustment(tmp_path: Path) -> None:
    path = _write_index(
        tmp_path / "verified.json",
        status="verified",
        series={"2025-Q2": 100.0, "2026-Q2": 110.0},
    )
    engine = PropertyValuationEngine(market_index_path=path)
    vo = engine.valuate("case_f02_verified", _subject(), _comps(sale_date="2025-05-01"))

    block = vo.market_indicators["market_index"]
    assert block["usable_for_time_adjustment"] is True
    assert block["time_adjustment_applied"] is True
    assert vo.market_indicators["rbi_hpi_current"] == 110.0
    assert vo.market_indicators["rbi_hpi_yoy_growth_percent"] == 10.0


def test_missing_quarter_is_not_replaced_by_default_constant(tmp_path: Path) -> None:
    """A quarter absent from the series must not fall back to an invented level (e.g. 100.0)."""
    partial = _write_index(
        tmp_path / "partial.json",
        status="verified",
        series={"2025-Q4": 105.0},
    )
    engine_partial = PropertyValuationEngine(market_index_path=partial)
    vo_partial = engine_partial.valuate(
        "case_f02_partial", _subject(), _comps(sale_date="2026-05-01")
    )

    block = vo_partial.market_indicators["market_index"]
    assert block["time_adjustment_applied"] is False
    assert block["time_adjustment_abstained_reason"] == "incomplete_index_coverage"
    assert "2026-Q2" in block["missing_index_periods"]

    # With no index at all the estimate is identical: no invented default was used.
    engine_none = PropertyValuationEngine(market_index_path=tmp_path / "missing.json")
    vo_none = engine_none.valuate("case_f02_none", _subject(), _comps(sale_date="2026-05-01"))
    assert vo_partial.estimate == vo_none.estimate


def test_synthetic_optin_uses_dev_fixture(tmp_path: Path) -> None:
    engine = PropertyValuationEngine(allow_synthetic=True, market_index_path=DEFAULT_MARKET_INDEX_FILE)
    vo = engine.valuate("case_f02_optin", _subject(), _comps())

    block = vo.market_indicators["market_index"]
    assert block["usable_reason"] == "synthetic_dev_fixture"
    assert block["time_adjustment_applied"] is True


# =========================================================================
# 3. Helper guarantees
# =========================================================================


def test_get_hpi_for_date_never_invents_a_level() -> None:
    assert get_hpi_for_date("2026-05-01", None) is None

    snapshot = load_market_index(DEFAULT_MARKET_INDEX_FILE)
    assert snapshot is not None
    # Uncovered quarter -> None, never a fallback constant.
    assert get_hpi_for_date("2099-05-01", snapshot) is None
    assert get_hpi_for_date("2026-05-01", snapshot) == snapshot.series["2026-Q2"]


def test_period_helpers() -> None:
    assert period_for_date("2026-05-01") == "2026-Q2"
    assert period_for_date("not-a-date") is None
    assert prior_year_period("2026-Q2") == "2025-Q2"
    assert prior_year_period("garbage") is None
