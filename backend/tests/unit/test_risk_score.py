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

@pytest.mark.parametrize(
    ("dti", "expected"),
    [
        (20, 0.0),
        (21, 8.0),
        (36, 8.0),
        (37, 18.0),
        (43, 18.0),
        (44, 25.0),
        (50, 25.0),
        (51, 30.0),
    ],
)
def test_dti_risk_boundaries(dti, expected):
    score = compute_composite_risk_score(dti, 60, 800, 12)
    assert score == expected


@pytest.mark.parametrize(
    ("ltv", "expected"),
    [
        (60, 0.0),
        (61, 8.0),
        (80, 8.0),
        (81, 16.0),
        (90, 16.0),
        (91, 22.0),
        (97, 22.0),
        (98, 25.0),
    ],
)
def test_ltv_risk_boundaries(ltv, expected):
    score = compute_composite_risk_score(20, ltv, 800, 12)
    assert score == expected


@pytest.mark.parametrize(
    ("fico", "expected"),
    [
        (300, 30.0),
        (579, 30.0),
        (580, 24.0),
        (669, 24.0),
        (670, 15.0),
        (739, 15.0),
        (740, 6.0),
        (799, 6.0),
        (800, 0.0),
        (850, 0.0),
    ],
)
def test_fico_risk_boundaries(fico, expected):
    score = compute_composite_risk_score(20, 60, fico, 12)
    assert score == expected


@pytest.mark.parametrize(
    ("reserves", "expected"),
    [
        (0, 15.0),
        (0.99, 15.0),
        (1, 12.0),
        (2.99, 12.0),
        (3, 9.0),
        (5.99, 9.0),
        (6, 4.0),
        (11.99, 4.0),
        (12, 0.0),
    ],
)
def test_reserve_risk_boundaries(reserves, expected):
    score = compute_composite_risk_score(20, 60, 800, reserves)
    assert score == expected


@pytest.mark.parametrize(
    ("field", "invalid_value", "message"),
    [
        ("dti", "30", "DTI must be a numeric percentage."),
        ("ltv", "80", "LTV must be a numeric percentage."),
        ("reserves_months", "6", "Reserves must be numeric."),
    ],
)
def test_risk_score_rejects_non_numeric_input_types(
    field, invalid_value, message
):
    """Risk scoring must reject numeric strings instead of silently coercing."""
    inputs = {
        "dti": 30.0,
        "ltv": 80.0,
        "fico": 740,
        "reserves_months": 6.0,
    }
    inputs[field] = invalid_value

    with pytest.raises(ValueError, match=message):
        compute_composite_risk_score(**inputs)
def test_extremely_large_integer_inputs_raise_value_error():
    huge = 10**10000

    with pytest.raises(ValueError):
        compute_composite_risk_score(huge, 80, 700, 6)

    with pytest.raises(ValueError):
        compute_composite_risk_score(35, huge, 700, 6)

    with pytest.raises(ValueError):
        compute_composite_risk_score(35, 80, 700, huge)