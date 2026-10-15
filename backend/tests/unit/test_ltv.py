from decimal import Decimal

import pytest

from backend.app.calculations.ltv import calculate_ltv


def test_calculate_ltv_normal_case():
    result = calculate_ltv(
        Decimal("240000"),
        Decimal("300000"),
    )

    assert result["ltv"] == Decimal("80.00")
    assert result["warnings"] == []


def test_calculate_ltv_above_80_percent():
    result = calculate_ltv(
        Decimal("270000"),
        Decimal("300000"),
    )

    assert result["ltv"] == Decimal("90.00")
    assert "LTV exceeds 80%." in result["warnings"]


def test_calculate_ltv_below_80_percent():
    result = calculate_ltv(
        Decimal("150000"),
        Decimal("300000"),
    )

    assert result["ltv"] == Decimal("50.00")
    assert result["warnings"] == []


def test_calculate_ltv_zero_property_value():
    with pytest.raises(ValueError, match="Property value must be greater than zero."):
        calculate_ltv(
            Decimal("200000"),
            Decimal("0"),
        )


def test_calculate_ltv_negative_loan_amount():
    with pytest.raises(ValueError, match="Loan amount cannot be negative."):
        calculate_ltv(
            Decimal("-1000"),
            Decimal("300000"),
        )


def test_calculate_ltv_negative_property_value():
    with pytest.raises(ValueError, match="Property value must be greater than zero."):
        calculate_ltv(
            Decimal("100000"),
            Decimal("-300000"),
        )