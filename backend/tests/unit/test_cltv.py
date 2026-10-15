from decimal import Decimal

import pytest

from backend.app.calculations.cltv import calculate_cltv


def test_calculate_cltv_normal_case():
    result = calculate_cltv(
        Decimal("240000"),
        Decimal("30000"),
        Decimal("300000"),
    )

    assert result["total_secured_debt"] == Decimal("270000")
    assert result["cltv"] == Decimal("90.00")
    assert "CLTV exceeds 80%." in result["warnings"]


def test_calculate_cltv_below_80_percent():
    result = calculate_cltv(
        Decimal("150000"),
        Decimal("30000"),
        Decimal("300000"),
    )

    assert result["cltv"] == Decimal("60.00")
    assert result["warnings"] == []


def test_calculate_cltv_exactly_80_percent():
    result = calculate_cltv(
        Decimal("240000"),
        Decimal("0"),
        Decimal("300000"),
    )

    assert result["cltv"] == Decimal("80.00")
    assert result["warnings"] == []


def test_calculate_cltv_zero_property_value():
    with pytest.raises(ValueError, match="Property value must be greater than zero."):
        calculate_cltv(
            Decimal("200000"),
            Decimal("10000"),
            Decimal("0"),
        )


def test_calculate_cltv_negative_primary_loan():
    with pytest.raises(ValueError, match="Primary loan cannot be negative."):
        calculate_cltv(
            Decimal("-1000"),
            Decimal("10000"),
            Decimal("300000"),
        )


def test_calculate_cltv_negative_additional_loan():
    with pytest.raises(
        ValueError,
        match="Additional secured loans cannot be negative.",
    ):
        calculate_cltv(
            Decimal("200000"),
            Decimal("-1000"),
            Decimal("300000"),
        )


def test_calculate_cltv_negative_property_value():
    with pytest.raises(ValueError, match="Property value must be greater than zero."):
        calculate_cltv(
            Decimal("200000"),
            Decimal("10000"),
            Decimal("-300000"),
        )