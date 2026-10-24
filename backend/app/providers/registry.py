"""State Provider Registry and Router.

Enforces GEMINI.md Section 3 and Section 10 Step 5:
- Router managing multi-state provider instances (UP, MH, KA, TS).
- Unsupported states return an explicit data-unavailable error rather than fabricated records.
"""

from __future__ import annotations

from typing import Any

from app.providers.base import BaseStateProvider, UnsupportedStateError
from app.providers.karnataka.provider import KarnatakaProvider
from app.providers.maharashtra.provider import MaharashtraProvider
from app.providers.telangana.provider import TelanganaProvider
from app.providers.up.provider import UttarPradeshProvider


class StateProviderRegistry:
    """Registry routing operations to verified state data providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseStateProvider] = {
            "UP": UttarPradeshProvider(),
            "MH": MaharashtraProvider(),
            "KA": KarnatakaProvider(),
            "TS": TelanganaProvider(),
        }

    def is_state_supported(self, state_code: str) -> bool:
        """Check whether state provider is officially configured and approved."""
        return state_code.strip().upper() in self._providers

    def get_provider(self, state_code: str) -> BaseStateProvider:
        """Retrieve state provider adapter or raise UnsupportedStateError."""
        norm_code = state_code.strip().upper()
        if norm_code not in self._providers:
            raise UnsupportedStateError(
                f"State '{state_code}' is unsupported. No approved provider or permitted data source exists. "
                f"Currently supported candidate states: {self.list_supported_states()}."
            )
        return self._providers[norm_code]

    def list_supported_states(self) -> list[str]:
        """List state codes for all registered state providers."""
        return sorted(self._providers.keys())

    def get_all_state_statuses(self) -> dict[str, dict[str, Any]]:
        """Return readiness and access metadata across all registered state providers."""
        statuses: dict[str, dict[str, Any]] = {}
        for state_code, provider in self._providers.items():
            meta = provider.metadata
            statuses[state_code] = {
                "state_code": state_code,
                "state_name": meta.state_name,
                "reference_rate_name": meta.reference_rate_local_name,
                "native_unit": meta.native_area_unit,
                "reference_rate_approved": meta.reference_rate_approved,
                "transaction_data_approved": meta.transaction_data_approved,
                "transaction_restriction": meta.transaction_restriction_reason,
                "supported_districts": meta.supported_districts,
            }
        return statuses


# Default singleton instance
state_provider_registry = StateProviderRegistry()
