
"""Loan-to-Value (LTV) calculation."""

from decimal import Decimal
from typing import Any

from app.calculations.validation import to_finite_decimal


def calculate_ltv(
    loan_amount: Decimal,
    property_value: Decimal,
) -> dict[str, Any]:
    """
    Calculate the Loan-to-Value ratio.

    Formula:
        LTV = (Loan Amount / Property Value) * 100
    """
    loan_amount = to_finite_decimal(loan_amount, "Loan amount")
    property_value = to_finite_decimal(property_value, "Property value")

    if loan_amount < 0:
        raise ValueError("Loan amount cannot be negative.")

    if property_value <= 0:
        raise ValueError("Property value must be greater than zero.")

    ltv = (loan_amount / property_value) * Decimal("100")

    warnings: list[str] = []
    if ltv > Decimal("80"):
        warnings.append("LTV exceeds 80%.")

    return {
        "loan_amount": loan_amount,
        "property_value": property_value,
        "ltv": ltv.quantize(Decimal("0.01")),
        "warnings": warnings,
    }
