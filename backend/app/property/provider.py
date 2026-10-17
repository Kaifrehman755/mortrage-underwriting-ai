"""Abstract CompProvider interface.

Adheres to Playbook Section 3a, 5, and Section 14.2:
- Providers must be authorized and verifiable.
- Never invent rows on provider error (raises ProviderUnavailable).
"""

from abc import ABC, abstractmethod
from typing import Any

from app.property.schemas import ComparableRecord, SubjectProperty


class ProviderUnavailable(Exception):
    """Raised when an authorized data provider is down, timed out, or returns an error.

    Invariant 1: A provider error must raise ProviderUnavailable, never return invented rows.
    """

    def __init__(self, provider_name: str, message: str, status_code: int = 503):
        super().__init__(f"Provider '{provider_name}' unavailable: {message}")
        self.provider_name = provider_name
        self.message = message
        self.status_code = status_code


class CompProvider(ABC):
    """Abstract base class for comparable property data providers."""

    @abstractmethod
    def fetch_comps(
        self,
        subject: SubjectProperty,
        radius_km: float = 3.0,
        months: int = 12,
        filters: dict[str, Any] | None = None,
    ) -> list[ComparableRecord]:
        """Retrieve comparable sales matching subject constraints.

        Args:
            subject: The normalized subject property.
            radius_km: Search radius around the subject location.
            months: Maximum age of comparable transactions in months.
            filters: Optional filters (property_type, area_basis, price_type).

        Returns:
            List of ComparableRecord market facts.

        Raises:
            ProviderUnavailable: If external service fails or encounters a connection issue.
        """
        pass
