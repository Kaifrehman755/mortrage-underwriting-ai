from decimal import Decimal

import pytest

from backend.app.calculations.dscr import calculate_dscr


def test_calculate_dscr_above_benchmark():
    result = calculate_dscr(
        Decimal("150000"),
        Decimal("100000"),
    )

    assert result["dscr"] == Decimal("1.50")
    assert result["warnings"] == []


def test_calculate_dscr_exactly_one():
    result = calculate_dscr(
        Decimal("100000"),
        Decimal("100000"),
    )

    assert result["dscr"] == Decimal("1.00")
    assert any("1.25" in warning for warning in result["warnings"])
    assert not any("below 1.0" in warning for warning in result["warnings"])

def test_calculate_dscr_below_one():
    result = calculate_dscr(
        Decimal("80000"),
        Decimal("100000"),
    )

    assert result["dscr"] == Decimal("0.80")
    assert any("below 1.0" in warning for warning in result["warnings"])


def test_calculate_dscr_below_125():
    result = calculate_dscr(
        Decimal("110000"),
        Decimal("100000"),
    )

    assert result["dscr"] == Decimal("1.10")
    assert any("1.25" in warning for warning in result["warnings"])


def test_calculate_dscr_zero_debt_service():
    with pytest.raises(
        ValueError,
        match="Annual debt service must be greater than zero.",
    ):
        calculate_dscr(
            Decimal("100000"),
            Decimal("0"),
        )


def test_calculate_dscr_negative_income():
    with pytest.raises(
        ValueError,
        match="Net operating income cannot be negative.",
    ):
        calculate_dscr(
            Decimal("-1000"),
            Decimal("100000"),
        )


def test_calculate_dscr_negative_debt_service():
    with pytest.raises(
        ValueError,
        match="Annual debt service cannot be negative.",
    ):
        calculate_dscr(
            Decimal("100000"),
            Decimal("-1000"),
        )