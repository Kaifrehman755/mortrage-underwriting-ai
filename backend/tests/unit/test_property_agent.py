"""Unit and acceptance tests for Property Valuation Agent.

Validates all 8 design invariants from Playbook Section 1 and Section 10:
- Invariant 1: Never fabricate data; provider failure sets human review and abstains.
- Invariant 2: Market facts and model estimates live in separate fields.
- Invariant 4: Low confidence or failure sets human_review_required.
- Invariant 5: Protected-class proxies rejected.
- Invariant 6: Explainer cannot change estimate or flags.
- Invariant 8: State isolation preserved (UP never gets MH comps).
"""

from datetime import date, datetime, timedelta

import pytest

from app.agents.property_agent import PropertyAgent
from app.property.commands import LoanOfficerCommandHandler
from app.property.comps import ComparableSalesAnalyzer
from app.property.gate import GuardrailGate
from app.property.jurisdictions import get_jurisdiction
from app.property.normalize import (
    clean_raw_record,
    flag_outliers_mad,
    haversine_km,
    parse_area_sqft,
    parse_bhk,
    parse_pincode,
    parse_price_inr,
)
from app.property.providers.synthetic import SyntheticProvider
from app.property.schemas import (
    ComparableRecord,
    SharedCaseState,
    SubjectProperty,
)
from app.property.valuation import PropertyValuationEngine, calculate_weighted_median


@pytest.fixture
def subject_up():
    """Standard subject property in Gomti Nagar, Lucknow (UP pilot)."""
    return SubjectProperty(
        original_address="Flat 402, Shalimar Grand, Gomti Nagar, Lucknow",
        address_norm="Flat 402, Shalimar Grand, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        pincode="226010",
        property_type="apartment",
        living_area_sqft=1250.0,
        area_basis="carpet",
        lat=26.8530,
        lon=80.9980,
    )


# =========================================================================
# 1. Normalization & Cleaning Tests (Section 14.3 & 14.5)
# =========================================================================

def test_parse_price_inr():
    assert parse_price_inr("85 Lac") == 8500000.0
    assert parse_price_inr("1.2 Cr") == 12000000.0
    assert parse_price_inr("₹75,50,000") == 7550000.0
    assert parse_price_inr("8500000") == 8500000.0
    assert parse_price_inr("50 K") == 50000.0
    assert parse_price_inr("-5000") is None
    assert parse_price_inr("0") is None
    assert parse_price_inr("not a price") is None


def test_parse_area_sqft():
    assert parse_area_sqft("1200 sq ft") == 1200.0
    assert parse_area_sqft("100 sqm") == pytest.approx(1076.39, 0.1)
    assert parse_area_sqft("100 sqyd") == 900.0
    assert parse_area_sqft("100 gaj") == 900.0
    assert parse_area_sqft("-100") is None
    assert parse_area_sqft("invalid") is None


def test_parse_bhk_and_pincode():
    assert parse_bhk("3 BHK Luxury Flat") == 3
    assert parse_bhk("2bhk in Gomti Nagar") == 2
    assert parse_bhk("Villa without bhk tag") is None
    assert parse_pincode("Gomti Nagar, Lucknow 226010") == "226010"
    assert parse_pincode("No pincode here") is None


def test_haversine_distance():
    # Distance between Gomti Nagar (26.853, 80.998) and Hazratganj (26.8467, 80.9461)
    dist = haversine_km(26.8530, 80.9980, 26.8467, 80.9461)
    assert 4.5 <= dist <= 6.0


def test_clean_raw_record_rejects_and_logs():
    jurisdiction = get_jurisdiction("UP")

    # 1. Invalid price rejection
    bad_price_row = {"price_raw": "-100", "area_raw": "1000 sqft", "date_raw": "2026-01-01", "lat": 26.85, "lon": 80.99}
    cleaned, reasons = clean_raw_record(bad_price_row, jurisdiction)
    assert cleaned is None
    assert "invalid_or_missing_price" in reasons

    # 2. Outside bounding box rejection
    out_of_bounds_row = {"price_raw": "50 Lac", "area_raw": "1000 sqft", "date_raw": "2026-01-01", "lat": 19.05, "lon": 72.83}
    cleaned, reasons = clean_raw_record(out_of_bounds_row, jurisdiction)
    assert cleaned is None
    assert any("outside_boundary_box" in r for r in reasons)


def test_clean_raw_record_date_validation():
    jurisdiction = get_jurisdiction("UP")
    base_row = {
        "price_raw": "50 Lac",
        "area_raw": "1000 sqft",
        "lat": 26.85,
        "lon": 80.99,
    }

    # 1. Accepts datetime object (must not fail with TypeError: '>' not supported between datetime and date)
    dt_row = {**base_row, "sale_date": datetime(2025, 6, 15, 14, 30)}
    cleaned, reasons = clean_raw_record(dt_row, jurisdiction)
    assert cleaned is not None
    assert cleaned["sale_date"] == "2025-06-15"
    assert reasons == []

    # 2. Accepts date object
    date_row = {**base_row, "sale_date": date(2025, 6, 15)}
    cleaned, reasons = clean_raw_record(date_row, jurisdiction)
    assert cleaned is not None
    assert cleaned["sale_date"] == "2025-06-15"

    # 3. Accepts day-first string (dd/mm/yyyy)
    slash_row = {**base_row, "date_raw": "15/06/2025"}
    cleaned, reasons = clean_raw_record(slash_row, jurisdiction)
    assert cleaned is not None
    assert cleaned["sale_date"] == "2025-06-15"

    # 4. Rejects future date (using date and datetime in the future)
    future_date = date.today() + timedelta(days=30)
    future_row = {**base_row, "sale_date": future_date}
    cleaned, reasons = clean_raw_record(future_row, jurisdiction)
    assert cleaned is None
    assert any("future_sale_date" in r for r in reasons)

    future_dt = datetime.now() + timedelta(days=30)
    future_dt_row = {**base_row, "sale_date": future_dt}
    cleaned, reasons = clean_raw_record(future_dt_row, jurisdiction)
    assert cleaned is None
    assert any("future_sale_date" in r for r in reasons)


def test_flag_outliers_mad():
    records = [
        {"price_per_sqft": 5000.0},
        {"price_per_sqft": 5100.0},
        {"price_per_sqft": 4900.0},
        {"price_per_sqft": 5050.0},
        {"price_per_sqft": 5200.0},
        {"price_per_sqft": 4800.0},
        {"price_per_sqft": 25000.0},  # Extreme outlier
    ]
    flagged = flag_outliers_mad(records, threshold=3.5)
    outliers = [r for r in flagged if "outlier" in r.get("clean_flags", [])]
    assert len(outliers) == 1
    assert outliers[0]["price_per_sqft"] == 25000.0


# =========================================================================
# 2. Invariant Acceptance Tests
# =========================================================================

def test_invariant_1_never_fabricate_provider_failure_sets_human_review(subject_up):
    """Invariant 1 & 4: Provider outage raises exception; never returns invented data."""
    provider = SyntheticProvider(simulate_outage=True)
    agent = PropertyAgent(provider=provider, allow_synthetic=True)

    state = SharedCaseState(
        case_id="case_outage_001",
        subject_property=subject_up,
    )
    result = agent.evaluate(state)

    assert result.model_output is not None
    assert result.model_output.estimate is None
    assert result.model_output.abstain_reason == "provider_unavailable"
    assert result.human_review_required is True
    assert result.status == "needs_review"
    assert len(result.market_facts) == 0


def test_invariant_2_market_facts_and_model_estimates_separated(subject_up):
    """Invariant 2: Market facts and model estimates live in separate objects."""
    provider = SyntheticProvider(seed=42)
    agent = PropertyAgent(provider=provider, allow_synthetic=True)

    state = SharedCaseState(
        case_id="case_inv2_001",
        subject_property=subject_up,
    )
    result = agent.evaluate(state)

    assert result.model_output is not None
    assert result.model_output.is_estimate is True
    # Market facts are separate list of ComparableRecord
    assert isinstance(result.market_facts, list)
    assert len(result.market_facts) > 0
    for fact in result.market_facts:
        assert isinstance(fact, ComparableRecord)
        assert fact.price_per_sqft > 0
        assert fact.is_synthetic is True  # Labelled synthetic


def test_invariant_4_low_confidence_and_thin_data_sets_human_review(subject_up):
    """Invariant 4: Fewer than 3 comps abstains and sets human_review_required=True."""
    # Custom provider with only 2 comps
    comps = [
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id="REC-1",
            address="Comp 1",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=5000000.0,
            sale_date="2026-05-01",
            living_area_sqft=1000.0,
            price_per_sqft=5000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=0.8,
        ),
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id="REC-2",
            address="Comp 2",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=5200000.0,
            sale_date="2026-06-01",
            living_area_sqft=1040.0,
            price_per_sqft=5000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.1,
        ),
    ]

    engine = PropertyValuationEngine()
    vo = engine.valuate(case_id="case_thin_001", subject=subject_up, available_comps=comps)

    assert vo.estimate is None
    assert vo.abstain_reason == "insufficient_comparables"
    assert vo.human_review_required is True
    assert vo.confidence_label == "low"


def test_invariant_5_protected_class_proxies_rejected(subject_up):
    """Invariant 5: Reject protected-class proxies in subject notes or comp features."""
    jurisdiction = get_jurisdiction("UP")
    row_with_proxy = {
        "price_raw": "60 Lac",
        "area_raw": "1100 sqft",
        "date_raw": "2026-03-01",
        "lat": 26.85,
        "lon": 80.99,
        "description": "Located in exclusive Brahmin colony near temple",
    }
    cleaned, reasons = clean_raw_record(row_with_proxy, jurisdiction)
    assert cleaned is None
    assert any("contains_protected_class_proxy" in r for r in reasons)


def test_invariant_6_explainer_cannot_alter_estimate_or_flags(subject_up):
    """Invariant 6: LLM explainer returns formatted text and cannot alter stored estimates."""
    provider = SyntheticProvider(seed=42)
    agent = PropertyAgent(provider=provider, allow_synthetic=True)
    handler = LoanOfficerCommandHandler(agent=agent)

    # 1. Intake
    handler.intake(
        case_id="case_exp_001",
        address="Flat 201, 3 BHK, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_raw="1250 sqft",
    )

    # 2. Valuate
    val_res = handler.valuate("case_exp_001")
    original_estimate = val_res["estimate"]
    assert original_estimate is not None

    # 3. Explain
    exp_res = handler.explain("case_exp_001")
    assert "RETRIEVED MARKET FACTS" in exp_res["plain_language_summary"]
    assert "MODEL ESTIMATE" in exp_res["plain_language_summary"]
    assert "is_estimate=True" in exp_res["plain_language_summary"]

    # Verify state estimate remains identical
    state_after = handler.cases["case_exp_001"]
    assert state_after.model_output is not None
    assert state_after.model_output.estimate == original_estimate


def test_invariant_8_state_isolation_up_never_receives_mh_comps(subject_up):
    """Invariant 8: Comps from Maharashtra must never cross into an Uttar Pradesh case."""
    provider = SyntheticProvider(seed=42)
    all_comps = provider.fetch_comps(subject_up, radius_km=50.0, months=24)

    # Verify all returned comps are strictly UP
    for comp in all_comps:
        assert comp.state_code == "UP"
        assert comp.state_code != "MH"
        assert comp.state_code != "KA"


# =========================================================================
# 3. Comps Selection & Step Widening Tests
# =========================================================================

def test_step_widening_logic(subject_up):
    """Analyzer widens radius and area tolerance when comps are thin."""
    # Comp far away (3.2 km) and with 28% area gap
    wide_comp = ComparableRecord(
        source_id=1,
        source_name="synthetic",
        provider_record_id="REC-WIDE-1",
        address="Wide Comp 1",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        property_type="apartment",
        sale_price=4500000.0,
        sale_date="2026-04-01",
        living_area_sqft=900.0,  # 28% gap from 1250 sqft
        price_per_sqft=5000.0,
        price_type="registered_deed",
        license_scope="synthetic_internal",
        distance_km=3.2,
    )
    # Plus two normal comps
    normal_comps = [
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id=f"REC-NORM-{i}",
            address=f"Norm Comp {i}",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=6000000.0,
            sale_date="2026-05-01",
            living_area_sqft=1200.0,
            price_per_sqft=5000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.2,
        )
        for i in range(2)
    ]

    analyzer = ComparableSalesAnalyzer()
    selected, meta = analyzer.select_comps(subject_up, [wide_comp] + normal_comps)

    # Initial step had only 2 comps; ladder widened to step 2 (3.5 km, 30% area) to find 3 comps
    assert len(selected) == 3
    assert meta["final_radius_km"] == 3.5


def test_asking_prices_excluded_from_valuation_comps(subject_up):
    """Asking prices are excluded from valuation estimate comps (used only for indicators)."""
    asking_comp = ComparableRecord(
        source_id=1,
        source_name="synthetic",
        provider_record_id="REC-ASKING",
        address="Asking Property",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        property_type="apartment",
        sale_price=8000000.0,
        sale_date="2026-06-01",
        living_area_sqft=1250.0,
        price_per_sqft=6400.0,
        price_type="asking",  # Asking price!
        license_scope="synthetic_internal",
        distance_km=0.5,
    )
    analyzer = ComparableSalesAnalyzer()
    selected, _ = analyzer.select_comps(subject_up, [asking_comp])
    assert len(selected) == 0


# =========================================================================
# 4. Valuation Math & Bootstrap Tests
# =========================================================================

def test_weighted_median_math():
    values = [4000.0, 5000.0, 6000.0]
    # Heavy weight on 5000.0
    weights = [0.1, 0.8, 0.1]
    med = calculate_weighted_median(values, weights)
    assert med == 5000.0


def test_bootstrap_interval_with_5_comps(subject_up):
    """When n_comps >= 5, computes bootstrap 80% confidence interval."""
    provider = SyntheticProvider(seed=101)
    all_comps = provider.fetch_comps(subject_up, radius_km=5.0, months=12)

    engine = PropertyValuationEngine(allow_synthetic=True)
    vo = engine.valuate("case_boot_001", subject_up, all_comps)

    assert vo.estimate is not None
    assert vo.n_comps >= 5
    assert vo.interval_low is not None
    assert vo.interval_high is not None
    assert vo.interval_low < vo.estimate < vo.interval_high


def test_interval_abstains_when_n_comps_between_3_and_4(subject_up):
    """When 3 <= n_comps < 5, estimate is returned but interval is None."""
    comps_4 = [
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id=f"REC-4-{i}",
            address=f"Comp {i}",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=6000000.0 + i * 100000,
            sale_date="2026-04-01",
            living_area_sqft=1200.0,
            price_per_sqft=5000.0 + i * 80,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.0 + i * 0.1,
        )
        for i in range(4)
    ]
    engine = PropertyValuationEngine()
    vo = engine.valuate("case_4_comps", subject_up, comps_4)

    assert vo.estimate is not None
    assert vo.interval_low is None
    assert vo.interval_high is None


def test_high_dispersion_abstains(subject_up):
    """When dispersion CV > 0.35, engine abstains with high_dispersion."""
    # Very erratic prices per sqft: 2000 vs 12000
    erratic_comps = [
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id="REC-DISP-1",
            address="Low Price Comp",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=2400000.0,
            sale_date="2026-05-01",
            living_area_sqft=1200.0,
            price_per_sqft=2000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.0,
        ),
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id="REC-DISP-2",
            address="Mid Price Comp",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=6000000.0,
            sale_date="2026-05-01",
            living_area_sqft=1200.0,
            price_per_sqft=5000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.0,
        ),
        ComparableRecord(
            source_id=1,
            source_name="synthetic",
            provider_record_id="REC-DISP-3",
            address="High Price Comp",
            locality="Gomti Nagar",
            city="Lucknow",
            state_code="UP",
            property_type="apartment",
            sale_price=14400000.0,
            sale_date="2026-05-01",
            living_area_sqft=1200.0,
            price_per_sqft=12000.0,
            price_type="registered_deed",
            license_scope="synthetic_internal",
            distance_km=1.0,
        ),
    ]
    engine = PropertyValuationEngine()
    vo = engine.valuate("case_disp_001", subject_up, erratic_comps)

    assert vo.estimate is None
    assert vo.abstain_reason == "high_dispersion"
    assert vo.human_review_required is True


def test_valuation_backtest():
    """Run leave-one-out backtest and check MAPE is sensible."""
    provider = SyntheticProvider(seed=42)
    subject = SubjectProperty(
        original_address="Gomti Nagar",
        address_norm="Gomti Nagar",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_sqft=1250.0,
        lat=26.8530,
        lon=80.9980,
    )
    comps = provider.fetch_comps(subject, radius_km=5.0, months=18)
    engine = PropertyValuationEngine(allow_synthetic=True)
    results = engine.run_backtest(comps)

    assert "mape_percent" in results
    assert results["evaluated"] >= 5
    assert results["mape_percent"] < 15.0  # MAPE should be under 15% on synthetic model


# =========================================================================
# 5. Loan Officer Command Workflow & Audit Trail
# =========================================================================

def test_loan_officer_workflow_end_to_end():
    handler = LoanOfficerCommandHandler(allow_synthetic=True)

    # 1. /intake
    intake_res = handler.intake(
        case_id="case_lo_001",
        address="Flat 302, 2 BHK, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_raw="1100 sqft",
        price_quoted_raw="60 Lac",
    )
    assert intake_res["status"] == "intake_done"

    # 2. /valuate
    val_res = handler.valuate("case_lo_001")
    assert val_res["is_estimate"] is True
    assert val_res["estimate"] is not None

    # 3. /comps
    comps_res = handler.comps("case_lo_001")
    assert comps_res["count"] > 0

    # 4. /market
    mkt_res = handler.market("Gomti Nagar")
    assert mkt_res["locality"] == "Gomti Nagar"
    assert mkt_res["median_registered_ppsf"] > 0

    # 5. /explain
    exp_res = handler.explain("case_lo_001")
    assert "MODEL ESTIMATE" in exp_res["plain_language_summary"]

    # 6. /escalate
    esc_res = handler.escalate("case_lo_001", reason="Unusual circle rate discrepancy noted.")
    assert esc_res["status"] == "needs_review"
    assert esc_res["escalated"] is True

    # Guardrail check
    state = handler.cases["case_lo_001"]
    GuardrailGate.assert_valid(state)
    assert len(state.audit_trail) >= 1
    audit = state.audit_trail[0]
    assert audit.actor == "property_agent"
    assert len(audit.input_digest) == 64
    assert len(audit.output_digest) == 64


# =========================================================================
# 6. F-01 Regression: Synthetic Data Must Never Reach Production Valuation
# =========================================================================

def _real_comp(
    rec_id: str,
    *,
    ppsf: float = 5000.0,
    dist: float = 1.0,
    area: float = 1200.0,
) -> ComparableRecord:
    """An approved, non-synthetic registered-deed comparable."""
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
        sale_date="2026-05-01",
        living_area_sqft=area,
        price_per_sqft=ppsf,
        price_type="registered_deed",
        license_scope="approved",
        distance_km=dist,
        is_synthetic=False,
    )


def _synthetic_comp(rec_id: str, *, dist: float = 1.0, ppsf: float = 5200.0) -> ComparableRecord:
    """A fabricated, clearly-labelled synthetic comparable."""
    area = 1200.0
    return ComparableRecord(
        source_id=1,
        source_name="synthetic_provider",
        provider_record_id=rec_id,
        address=f"Synthetic Comp {rec_id}",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        property_type="apartment",
        sale_price=ppsf * area,
        sale_date="2026-05-01",
        living_area_sqft=area,
        price_per_sqft=ppsf,
        price_type="registered_deed",
        license_scope="synthetic_internal",
        distance_km=dist,
        is_synthetic=True,
    )


def test_f01_property_agent_requires_injected_provider():
    """F-01: default construction must not silently fall back to synthetic data."""
    with pytest.raises(ValueError):
        PropertyAgent()


def test_f01_synthetic_provider_requires_explicit_optin():
    """F-01: a synthetic provider is refused unless allow_synthetic=True (test-only)."""
    with pytest.raises(ValueError):
        PropertyAgent(provider=SyntheticProvider())

    agent = PropertyAgent(provider=SyntheticProvider(), allow_synthetic=True)
    assert agent.allow_synthetic is True


def test_f01_analyzer_meta_reports_excluded_synthetic(subject_up):
    """F-01: selection checks the is_synthetic discriminator and reports exclusions."""
    synthetic = [_synthetic_comp(f"SYN-{i}") for i in range(3)]
    analyzer = ComparableSalesAnalyzer()
    selected, meta = analyzer.select_comps(subject_up, synthetic)

    assert selected == []
    assert meta["synthetic_excluded"] == 3


def test_f01_synthetic_only_evidence_yields_no_production_estimate(subject_up):
    """F-01: synthetic-only evidence must abstain and produce NO estimate."""
    synthetic = [_synthetic_comp(f"SYN-{i}", dist=0.8 + i * 0.1) for i in range(5)]
    engine = PropertyValuationEngine()  # production default: allow_synthetic=False
    vo = engine.valuate("case_f01_synth_only", subject_up, synthetic)

    assert vo.estimate is None
    assert vo.abstain_reason == "synthetic_evidence_not_permitted"
    assert vo.human_review_required is True
    assert vo.confidence_label == "low"
    assert vo.evidence_is_synthetic is False


def test_f01_mixed_evidence_excludes_synthetic_comps(subject_up):
    """F-01: with mixed evidence, only approved real comps are eligible."""
    real = [_real_comp(f"REAL-{i}", ppsf=5000.0 + i * 100, dist=0.9 + i * 0.1) for i in range(4)]
    synthetic = [_synthetic_comp(f"SYN-{i}", dist=0.5) for i in range(3)]

    engine = PropertyValuationEngine()
    vo = engine.valuate("case_f01_mixed", subject_up, real + synthetic)

    assert vo.estimate is not None
    assert vo.evidence_is_synthetic is False
    assert vo.n_comps <= len(real)
    selected_ids = set(vo.comp_ids)
    selected = [c for c in (real + synthetic) if c.comp_id in selected_ids]
    assert selected, "expected at least one real comparable to be selected"
    assert all(not c.is_synthetic for c in selected)


def test_f01_approved_real_evidence_produces_estimate(subject_up):
    """F-01: approved real evidence still produces an estimate (no regression)."""
    real = [_real_comp(f"REAL-{i}", ppsf=5000.0 + i * 60, dist=1.0 + i * 0.1) for i in range(5)]
    engine = PropertyValuationEngine()
    vo = engine.valuate("case_f01_real", subject_up, real)

    assert vo.estimate is not None
    assert vo.evidence_is_synthetic is False
    assert vo.n_comps == 5


def test_f01_synthetic_optin_marks_output_discriminator(subject_up):
    """F-01: when explicitly opted in, synthetic evidence is flagged, never disguised."""
    synthetic = [_synthetic_comp(f"SYN-{i}", dist=0.8 + i * 0.1) for i in range(5)]
    engine = PropertyValuationEngine(allow_synthetic=True)
    vo = engine.valuate("case_f01_optin", subject_up, synthetic)

    assert vo.estimate is not None
    assert vo.evidence_is_synthetic is True
