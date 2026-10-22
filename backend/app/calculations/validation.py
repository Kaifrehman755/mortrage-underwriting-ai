
"""Shared validation helpers for financial calculations."""

from decimal import Decimal, InvalidOperation
from typing import Any


def to_finite_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a numeric value to Decimal and reject invalid numbers."""

    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a valid number.")

    if not isinstance(value, (Decimal, int, float, str)):
        raise ValueError(f"{field_name} must be a valid number.")

    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.") from None

    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return number
    