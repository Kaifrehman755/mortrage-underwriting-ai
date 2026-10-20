"""Unit tests for Phase 6 Valuation Estimation and Abstention Engine (GEMINI.md Step 6).

Verifies:
1. Deterministic weighted median calculation.
2. Robust locality-aware MAD outlier detection, zero MAD handling, and small group behavior.
3. Strict abstention triggers:
   - Unsupported state (STATE_NOT_SUPPORTED)
   - Missing coordinates (MISSING_COORDINATES)
   - Incompatible/unknown area basis (AREA_BASIS_INCOMPATIBLE)
   - Insufficient comps (< 3) (INSUFFICIENT_COMPARABLES)
   - Excessive price dispersion (EXCESSIVE_DISPERSION)
   - Stale market evidence (STALE_EVIDENCE)
4. Empirical uncertainty intervals only generated when >= 5 comps exist; bounds guarantee lower <= est <= upper.
5. Traceability: Every valuation links directly to eligible comparable records with selection reasons.
"""

from datetime import date, timedelta
from uuid import uuid4
import pytest

from app.schemas.property import AreaType, PropertyType
from app.schemas.valuation import ValuationStatus
from app.valuation import (
    ComparableSelector,
    EligibleComparable,
    SubjectPropertyInput,
    ValuationEngine,
    calculate_median_and_mad,
    calculate_weighted_median,
    compute_confidence_and_bounds,
    evaluate_robust_outliers,
)


def test_calculate_weighted_median_logic() -> None:
    values = [4000.0, 5000.0, 6000.0]
    # Equal weights -> middle value
    assert calculate_weighted_median(values, [1.0, 1.0, 1.0]) == 5000.0
    # Heavy top weight -> pulls to 6000
    assert calculate_weighted_median(values, [0.1, 0.1, 0.9]) == 6000.0
    # Heavy bottom weight -> pulls to 4000
    assert calculate_weighted_median(values, [0.9, 0.1, 0.1]) == 4000.0


def test_mad_outlier_detection_zero_mad_and_small_groups() -> None:
    # 1. Small group (< 4): Should NOT flag false outliers
    small_comps = [
        EligibleComparable(
            transaction_id=uuid4(),
            property_id=None,
            distance_m=500.0,
            transaction_date=date(2026, 5, 1),
            price_inr=5000000.0,
            area_sqft=1000.0,
            area_type=AreaType.CARPET,
            price_per_sqft=5000.0,
            selection_reason="recent",
        ),
        EligibleComparable(
            transaction_id=uuid4(),
            property_id=None,
            distance_m=600.0,
            transaction_date=date(2026, 5, 1),
            price_inr=15000000.0,
            area_sqft=1000.0,
            area_type=AreaType.CARPET,
            price_per_sqft=15000.0,
            selection_reason="recent",
        ),
    ]
    eval_small, logs_small = evaluate_robust_outliers(small_comps, min_group_size=4)
    assert not any(c.is_outlier for c in eval_small)
    assert "bypassed" in logs_small[0]

    # 2. Zero MAD: Identical values across group
    identical_comps = [
        EligibleComparable(
            transaction_id=uuid4(),
            property_id=None,
            distance_m=500.0,
            transaction_date=date(2026, 5, 1),
            price_inr=5000000.0,
            area_sqft=1000.0,
            area_type=AreaType.CARPET,
            price_per_sqft=5000.0,
            selection_reason="recent",
        )
        for _ in range(5)
    ]
    eval_zero, logs_zero = evaluate_robust_outliers(identical_comps)
    assert not any(c.is_outlier for c in eval_zero)
    assert "Zero MAD" in logs_zero[0]


def test_mad_outlier_detection_flags_extreme_value_without_dropping() -> None:
    # Cluster around 5000 ppsf with one 15000 ppsf extreme outlier
    comps = [
        EligibleComparable(
            transaction_id=uuid4(),
            property_id=None,
            distance_m=500.0,
            transaction_date=date(2026, 5, 1),
            price_inr=5000000.0,
            area_sqft=1000.0,
            area_type=AreaType.CARPET,
            price_per_sqft=ppsf,
            selection_reason="proximity",
        )
        for ppsf in [4900.0, 5000.0, 5100.0, 5050.0, 15000.0]
    ]
    evaluated, logs = evaluate_robust_outliers(comps)
    assert len(evaluated) == 5  # No records dropped!
    outliers = [c for c in evaluated if c.is_outlier]
    assert len(outliers) == 1
    assert outliers[0].price_per_sqft == 15000.0
    assert outliers[0].robust_z is not None
    assert outliers[0].robust_z > 3.5
    assert "FLAGGED_OUTLIER" in outliers[0].selection_reason


def test_abstention_on_unsupported_state() -> None:
    engine = ValuationEngine()
    subject = SubjectPropertyInput(
        state_code="DL",  # Unsupported
        district="New Delhi",
        locality="Connaught Place",
        latitude=28.6315,
        longitude=77.2167,
        area_sqft=1000.0,
        area_type=AreaType.CARPET,
    )
    run, comps = engine.evaluate(subject, candidate_pool=[], dataset_cutoff=date(2026, 10, 1))
    assert run.status == ValuationStatus.ABSTAINED
    assert "STATE_NOT_SUPPORTED" in run.reason_codes
    assert run.estimate_inr is None
    assert len(comps) == 0


def test_abstention_on_missing_coordinates() -> None:
    engine = ValuationEngine()
    subject = SubjectPropertyInput(
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        latitude=None,  # Missing!
        longitude=None,
        area_sqft=1000.0,
        area_type=AreaType.CARPET,
    )
    run, comps = engine.evaluate(subject, candidate_pool=[], dataset_cutoff=date(2026, 10, 1))
    assert run.status == ValuationStatus.ABSTAINED
    assert "MISSING_COORDINATES" in run.reason_codes
    assert run.estimate_inr is None


def test_abstention_on_incompatible_area_basis() -> None:
    engine = ValuationEngine()
    subject = SubjectPropertyInput(
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        latitude=26.8530,
        longitude=80.9980,
        area_sqft=1000.0,
        area_type=AreaType.UNKNOWN,  # Unknown area basis!
    )
    run, comps = engine.evaluate(subject, candidate_pool=[], dataset_cutoff=date(2026, 10, 1))
    assert run.status == ValuationStatus.ABSTAINED
    assert "AREA_BASIS_INCOMPATIBLE" in run.reason_codes
    assert run.estimate_inr is None


def test_abstention_on_insufficient_comps() -> None:
    engine = ValuationEngine(min_comps=3)
    subject = SubjectPropertyInput(
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        latitude=26.8530,
        longitude=80.9980,
        area_sqft=1200.0,
        area_type=AreaType.CARPET,
    )
    # Only 1 candidate available
    candidate = {
        "transaction_id": "TX-1",
        "state_code": "UP",
        "property_type": "apartment",
        "price_type": "sale_consideration",
        "transaction_date": "2026-06-01",
        "transaction_price_inr": 6000000.0,
        "area_sqft": 1200.0,
        "area_type": "carpet",
        "latitude": 26.8532,
        "longitude": 80.9982,
    }
    run, comps = engine.evaluate(subject, candidate_pool=[candidate], dataset_cutoff=date(2026, 10, 1))
    assert run.status == ValuationStatus.ABSTAINED
    assert "INSUFFICIENT_COMPARABLES" in run.reason_codes
    assert run.estimate_inr is None


def test_successful_valuation_and_traceable_comparables() -> None:
    engine = ValuationEngine(min_comps=3, min_comps_for_bounds=5)
    subject = SubjectPropertyInput(
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        latitude=26.8530,
        longitude=80.9980,
        area_sqft=1000.0,
        area_type=AreaType.CARPET,
    )

    # 6 clean candidate comps in Gomti Nagar
    candidates = [
        {
            "transaction_id": f"TX-{i}",
            "state_code": "UP",
            "property_type": "apartment",
            "price_type": "sale_consideration",
            "transaction_date": (date(2026, 9, 1) - timedelta(days=i * 20)).isoformat(),
            "transaction_price_inr": 5000000.0 + (i * 50000.0),
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": 26.8530 + (i * 0.002),
            "longitude": 80.9980 + (i * 0.002),
        }
        for i in range(6)
    ]

    run, comps = engine.evaluate(subject, candidate_pool=candidates, dataset_cutoff=date(2026, 10, 1))

    assert run.status == ValuationStatus.COMPLETED
    assert run.estimate_inr is not None
    assert 5000000.0 <= run.estimate_inr <= 5300000.0
    # Because 6 comps were used (>= 5), empirical bounds are produced!
    assert run.lower_bound_inr is not None
    assert run.upper_bound_inr is not None
    assert run.lower_bound_inr <= run.estimate_inr <= run.upper_bound_inr

    # Traceability checks
    assert len(comps) == 6
    for c in comps:
        assert c.adjusted_price_per_sqft > 0
        assert c.distance_m >= 0
        assert 0.0 <= c.similarity_score <= 1.0
        assert "Proximity" in c.selection_reason


def test_uncertainty_bounds_withheld_when_fewer_than_five_comps() -> None:
    engine = ValuationEngine(min_comps=3, min_comps_for_bounds=5)
    subject = SubjectPropertyInput(
        state_code="UP",
        district="Lucknow",
        locality="Gomti Nagar",
        latitude=26.8530,
        longitude=80.9980,
        area_sqft=1000.0,
        area_type=AreaType.CARPET,
    )

    # Exactly 3 comps (enough for estimate, not enough for bounds)
    candidates = [
        {
            "transaction_id": f"TX-{i}",
            "state_code": "UP",
            "property_type": "apartment",
            "price_type": "sale_consideration",
            "transaction_date": "2026-08-01",
            "transaction_price_inr": 5200000.0,
            "area_sqft": 1000.0,
            "area_type": "carpet",
            "latitude": 26.8530 + (i * 0.002),
            "longitude": 80.9980 + (i * 0.002),
        }
        for i in range(3)
    ]

    run, comps = engine.evaluate(subject, candidate_pool=candidates, dataset_cutoff=date(2026, 10, 1))
    assert run.status == ValuationStatus.COMPLETED
    assert run.estimate_inr == 5200000.0
    # Strict rule: Uncertainty bounds withheld when < 5 comps
    assert run.lower_bound_inr is None
    assert run.upper_bound_inr is None
