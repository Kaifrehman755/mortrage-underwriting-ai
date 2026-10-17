"""Property data provider adapter interface.

Maintains backward-compatibility while exposing the core CompProvider abstractions.
"""

from app.property.provider import CompProvider, ProviderUnavailable
from app.property.providers.assessor_csv import AssessorCsvProvider
from app.property.providers.synthetic import SyntheticProvider

# Backward compatible alias
PropertyDataProvider = CompProvider

__all__ = [
    "PropertyDataProvider",
    "CompProvider",
    "ProviderUnavailable",
    "SyntheticProvider",
    "AssessorCsvProvider",
]
