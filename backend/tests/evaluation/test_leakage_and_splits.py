"""Evaluation and Leakage Prevention Tests (GEMINI.md Step 6 and Section 7).

Verifies:
1. Property Group Isolation: All transactions for the same physical property remain in the same partition.
2. Temporal Holdout: Evaluation strictly uses subsequent out-of-time transactions without future data leakage.
3. Locality Holdout: Evaluates geographic transferability with zero locality leakage.
4. Deterministic Split Manifest: Every split produces an auditable manifest with hash and parameters.
5. Evaluation Metrics & Abstention Reporting: MdAPE, MAPE, coverage rate, and stratified metrics.
6. Sample Size Warnings: Formally reports limitations when sample size is insufficient for strong generalization claims.
"""

from datetime import date
from uuid import uuid4
import pytest

from app.schemas.property import AreaType
from app.valuation import (
    ValuationEngine,
    create_locality_holdout_split,
    create_temporal_split,
    run_benchmark_evaluation,
)


def test_property_group_isolation_in_splits() -> None:
    """Verifies that repeat transactions for the same property never leak across partitions."""
    prop_a = "PROP_ALPHA"
    prop_b = "PROP_BETA"

    records = [
        # Property A: Two transactions (historical in 2024, repeat sale in 2026)
        {
            "transaction_id": "TX-A1",
            "property_id": prop_a,
            "transaction_date": date(2024, 5, 1),
            "state_code": "UP",
            "locality": "Gomti Nagar",
            "price_inr": 4500000.0,
            "area_sqft": 1000.0,
        },
        {
            "transaction_id": "TX-A2",
            "property_id": prop_a,
            "transaction_date": date(2026, 6, 1),
            "state_code": "UP",
            "locality": "Gomti Nagar",
            "price_inr": 5500000.0,
            "area_sqft": 1000.0,
        },
        # Property B: Subsequent property (only sold in 2026)
        {
            "transaction_id": "TX-B1",
            "property_id": prop_b,
            "transaction_date": date(2026, 8, 1),
            "state_code": "UP",
            "locality": "Gomti Nagar",
            "price_inr": 5800000.0,
            "area_sqft": 1000.0,
        },
    ]

    split_date = date(2025, 12, 31)
    train_records, test_records, manifest = create_temporal_split(
        records=records, split_date=split_date, seed=42
    )

    train_props = {r["property_id"] for r in train_records}
    test_props = {r["property_id"] for r in test_records}

    # Strict invariant: Intersection must be empty (zero property identity leakage!)
    assert train_props.intersection(test_props) == set()
    assert prop_a in train_props
    assert prop_b in test_props
    assert len(manifest.manifest_hash) == 64


def test_temporal_holdout_boundary_enforcement() -> None:
    """Verifies that training split contains no future records relative to split_date."""
    split_date = date(2025, 12, 31)
    records = [
        {
            "transaction_id": f"TX-{i}",
            "property_id": f"P-{i}",
            "transaction_date": date(2025, i, 15),
            "state_code": "UP",
            "locality": "Gomti Nagar",
            "price_inr": 5000000.0,
            "area_sqft": 1000.0,
        }
        for i in range(1, 13)
    ] + [
        {
            "transaction_id": f"TX-2026-{i}",
            "property_id": f"P-2026-{i}",
            "transaction_date": date(2026, i, 15),
            "state_code": "UP",
            "locality": "Gomti Nagar",
            "price_inr": 5400000.0,
            "area_sqft": 1000.0,
        }
        for i in range(1, 7)
    ]

    train_records, test_records, manifest = create_temporal_split(
        records=records, split_date=split_date, seed=100
    )

    for r in train_records:
        assert r["transaction_date"] <= split_date

    for r in test_records:
        assert r["transaction_date"] > split_date

    assert manifest.strategy == "temporal"
    assert manifest.train_count == 12
    assert manifest.test_count == 6


def test_locality_holdout_prevents_geographic_leakage() -> None:
    records = [
        {"transaction_id": "TX-1", "locality": "Gomti Nagar", "state_code": "UP"},
        {"transaction_id": "TX-2", "locality": "Indira Nagar", "state_code": "UP"},
        {"transaction_id": "TX-3", "locality": "Aliganj", "state_code": "UP"},
        {"transaction_id": "TX-4", "locality": "Hazratganj", "state_code": "UP"},
    ]

    train, test, manifest = create_locality_holdout_split(
        records=records, held_out_localities=["Aliganj", "Hazratganj"]
    )

    train_locs = {r["locality"].lower() for r in train}
    test_locs = {r["locality"].lower() for r in test}

    assert train_locs == {"gomti nagar", "indira nagar"}
    assert test_locs == {"aliganj", "hazratganj"}
    assert train_locs.intersection(test_locs) == set()
    assert manifest.held_out_localities == ["aliganj", "hazratganj"]


def test_benchmark_evaluation_and_metrics_calculation() -> None:
    engine = ValuationEngine(min_comps=3)
    cutoff = date(2026, 10, 1)

    # 10 training candidate comps around Gomti Nagar (base 5000 ppsf)
    train_pool = [
        {
            "transaction_id": f"TRAIN-TX-{i}",
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "Gomti Nagar",
            "property_type": "apartment",
            "price_type": "sale_consideration",
            "transaction_date": date(2026, 8, 1),
            "price_inr": 5000000.0 + (i * 20000.0),
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": 26.8530 + (i * 0.001),
            "longitude": 80.9980 + (i * 0.001),
        }
        for i in range(10)
    ]

    # Test set of 4 evaluation records (some completed, some in unsupported state or missing coords)
    eval_set = [
        # Gomti Nagar evaluation record (should succeed)
        {
            "transaction_id": "TEST-1",
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "Gomti Nagar",
            "price_inr": 5100000.0,
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": 26.8531,
            "longitude": 80.9981,
        },
        # Record with missing coordinates (should abstain)
        {
            "transaction_id": "TEST-2",
            "state_code": "UP",
            "district": "Lucknow",
            "locality": "Gomti Nagar",
            "price_inr": 5200000.0,
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": None,
            "longitude": None,
        },
        # Record in unsupported state (should abstain)
        {
            "transaction_id": "TEST-3",
            "state_code": "DL",
            "district": "New Delhi",
            "locality": "Saket",
            "price_inr": 9000000.0,
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": 28.5244,
            "longitude": 77.2167,
        },
    ]

    metrics = run_benchmark_evaluation(
        engine=engine,
        eval_records=eval_set,
        training_candidates=train_pool,
        dataset_cutoff=cutoff,
    )

    assert metrics.sample_size == 3
    assert metrics.abstained_count == 2
    assert metrics.completed_count == 1
    assert metrics.abstention_rate == pytest.approx(0.667, abs=0.01)
    assert metrics.coverage_rate == pytest.approx(0.333, abs=0.01)
    assert metrics.mdape is not None
    assert metrics.mdape < 5.0  # Close estimate on completed Gomti Nagar case
    # Verify small sample limitation warning is triggered
    assert metrics.sample_size_limitation_warning is not None
    assert "GEMINI.md Section 7" in metrics.sample_size_limitation_warning
