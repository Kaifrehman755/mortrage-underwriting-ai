
"""Combined Loan-to-Value (CLTV) calculation."""

from decimal import Decimal
from typing import Any

from app.calculations.validation import to_finite_decimal


def calculate_cltv(
    primary_loan: Decimal,
    additional_secured_loans: Decimal,
    property_value: Decimal,
) -> dict[str, Any]:
    """
    Calculate the Combined Loan-to-Value ratio.

    Formula:
        CLTV = ((Primary Loan + Additional Secured Loans)
                / Property Value) * 100
    """
    primary_loan = to_finite_decimal(primary_loan, "Primary loan")
    additional_secured_loans = to_finite_decimal(
        additional_secured_loans, "Additional secured loans"
    )
    property_value = to_finite_decimal(property_value, "Property value")

    if primary_loan < 0:
        raise ValueError("Primary loan cannot be negative.")

    if additional_secured_loans < 0:
        raise ValueError("Additional secured loans cannot be negative.")

    if property_value <= 0:
        raise ValueError("Property value must be greater than zero.")

    total_secured_debt = primary_loan + additional_secured_loans
    cltv = (total_secured_debt / property_value) * Decimal("100")

    warnings: list[str] = []
    if cltv > Decimal("80"):
        warnings.append("CLTV exceeds 80%.")

    return {
        "primary_loan": primary_loan,
        "additional_secured_loans": additional_secured_loans,
        "total_secured_debt": total_secured_debt,
        "property_value": property_value,
        "cltv": cltv.quantize(Decimal("0.01")),
        "warnings": warnings,
    }
