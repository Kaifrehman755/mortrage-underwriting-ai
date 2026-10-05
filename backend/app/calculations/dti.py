"""Deterministic Debt-to-Income (DTI) calculations (Reserved for Phase 1+)."""

from decimal import Decimal
from typing import Any


def calculate_dti(
    gross_monthly_income: Decimal,
    total_monthly_debt: Decimal,
) -> dict[str, Any]:
    
    warnings: list[str] = []

    # Validate gross monthly income
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

    # Validate total monthly debt
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

    # Calculate DTI
    dti = (total_monthly_debt / gross_monthly_income) * Decimal("100")

    return {
        "gross_monthly_income": gross_monthly_income,
        "total_monthly_debt": total_monthly_debt,
        "dti_percentage": dti,
        "status": "calculated",
        "warnings": warnings,
    }
