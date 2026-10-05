from decimal import Decimal

from app.calculations.dti import calculate_dti


def test_calculate_dti():
    result = calculate_dti(
        gross_monthly_income=Decimal("8000"),
        total_monthly_debt=Decimal("2400"),
    )

    assert result["dti_percentage"] == Decimal("30")
    assert result["status"] == "calculated"
    assert result["warnings"] == []


def test_dti_with_zero_debt():
    result = calculate_dti(
        gross_monthly_income=Decimal("8000"),
        total_monthly_debt=Decimal("0"),
    )

    assert result["dti_percentage"] == Decimal("0")
    assert result["status"] == "calculated"


def test_dti_with_zero_income():
    result = calculate_dti(
        gross_monthly_income=Decimal("0"),
        total_monthly_debt=Decimal("2400"),
    )

    assert result["dti_percentage"] is None
    assert result["status"] == "invalid"


def test_dti_with_negative_income():
    result = calculate_dti(
        gross_monthly_income=Decimal("-8000"),
        total_monthly_debt=Decimal("2400"),
    )

    assert result["dti_percentage"] is None
    assert result["status"] == "invalid"


def test_dti_with_negative_debt():
    result = calculate_dti(
        gross_monthly_income=Decimal("8000"),
        total_monthly_debt=Decimal("-2400"),
    )

    assert result["dti_percentage"] is None
    assert result["status"] == "invalid"
