import pytest

from backend.app.calculations.risk_score import (
    compute_composite_risk_score,
)


def test_low_risk_profile():
    score = compute_composite_risk_score(
        dti=20,
        ltv=60,
        fico=800,
        reserves_months=12,
    )

    assert score == 0.0


def test_high_risk_profile():
    score = compute_composite_risk_score(
        dti=55,
        ltv=100,
        fico=550,
        reserves_months=0,
    )

    assert score == 100.0


def test_moderate_risk_profile():
    score = compute_composite_risk_score(
        dti=40,
        ltv=85,
        fico=700,
        reserves_months=4,
    )

    assert score == 58.0


def test_score_is_deterministic():
    inputs = {
        "dti": 35,
        "ltv": 75,
        "fico": 750,
        "reserves_months": 8,
    }

    first = compute_composite_risk_score(**inputs)
    second = compute_composite_risk_score(**inputs)

    assert first == second


@pytest.mark.parametrize("dti", [-1, float("nan"), float("inf")])
def test_invalid_dti(dti):
    with pytest.raises(ValueError):
        compute_composite_risk_score(dti, 80, 700, 6)


@pytest.mark.parametrize("ltv", [-1, float("nan"), float("inf")])
def test_invalid_ltv(ltv):
    with pytest.raises(ValueError):
        compute_composite_risk_score(35, ltv, 700, 6)


@pytest.mark.parametrize("fico", [299, 851, 700.5, True])
def test_invalid_fico(fico):
    with pytest.raises(ValueError):
        compute_composite_risk_score(35, 80, fico, 6)


@pytest.mark.parametrize("reserves", [-1, float("nan"), float("inf")])
def test_invalid_reserves(reserves):
    with pytest.raises(ValueError):
        compute_composite_risk_score(35, 80, 700, reserves)