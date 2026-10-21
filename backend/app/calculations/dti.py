
"""Deterministic Debt-to-Income (DTI) calculations."""

from decimal import Decimal
from typing import Any

from app.calculations.validation import to_finite_decimal


def calculate_dti(
    gross_monthly_income: Decimal,
    total_monthly_debt: Decimal,
) -> dict[str, Any]:
    """Calculate DTI as a percentage of gross monthly income."""

    original_income = gross_monthly_income
    original_debt = total_monthly_debt

    try:
        gross_monthly_income = to_finite_decimal(
            gross_monthly_income, "Gross monthly income"
        )
        total_monthly_debt = to_finite_decimal(
            total_monthly_debt, "Total monthly debt"
        )
    except (ValueError, TypeError) as exc:
        return {
            "gross_monthly_income": original_income,
            "total_monthly_debt": original_debt,
            "dti_percentage": None,
            "status": "invalid",
            "warnings": [str(exc)],
        }

    if gross_monthly_income <= 0:
        return {
            "gross_monthly_income": gross_monthly_income,
            "total_monthly_debt": total_monthly_debt,
            "dti_percentage": None,
            "status": "invalid",
            "warnings": [
                "Gross monthly income must be greater than zero."
            ],
        }

    if total_monthly_debt < 0:
        return {
            "gross_monthly_income": gross_monthly_income,
            "total_monthly_debt": total_monthly_debt,
            "dti_percentage": None,
            "status": "invalid",
            "warnings": [
                "Total monthly debt cannot be negative."
            ],
        }

    dti = (
        total_monthly_debt / gross_monthly_income
    ) * Decimal("100")

    return {
        "gross_monthly_income": gross_monthly_income,
        "total_monthly_debt": total_monthly_debt,
        "dti_percentage": dti,
        "status": "calculated",
        "warnings": [],
    }


def calculate_back_end_dti(
    gross_monthly_income: Decimal,
    total_monthly_debt: Decimal,
) -> dict[str, Any]:
    """Calculate back-end DTI using total monthly debt."""
    return calculate_dti(gross_monthly_income, total_monthly_debt)


def calculate_front_end_dti(
    gross_monthly_income: Decimal,
    housing_expense: Decimal,
) -> dict[str, Any]:
    """Calculate front-end DTI using housing expenses."""
    return calculate_dti(gross_monthly_income, housing_expense)
