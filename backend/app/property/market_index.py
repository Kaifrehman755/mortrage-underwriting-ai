"""Versioned market-index provenance (security audit finding F-02).

Hard-coded, unprovenanced index values must never be used to time-adjust comparable
sales. This module loads a market index series from a versioned JSON file that
carries the source, publication date, units, base year and an explicit verification
status.

A series is only usable for a *production* time adjustment when
``verification_status == "verified"`` and the identifying provenance fields are
filled in. Otherwise the valuation engine abstains from the time adjustment instead
of inventing a value. A clearly-labelled synthetic dev fixture may be used when the
caller explicitly opts in (``allow_synthetic=True``), mirroring the F-01 gate.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MARKET_INDEX_FILE = (
    REPO_ROOT / "data" / "market_indices" / "rbi_hpi_urban_lucknow.json"
)


class MarketIndexSnapshot(BaseModel):
    """A versioned market index series plus its provenance metadata."""

    series_id: str
    title: str = ""
    index_basis: str = "city"
    base_year: str = "TODO-VERIFY"
    units: str = ""
    source_name: str = "TODO-VERIFY"
    source_url: str = "TODO-VERIFY"
    publication_date: str = "TODO-VERIFY"
    retrieved_at: str = "TODO-VERIFY"
    verification_status: str = "unverified"
    provenance_note: str = ""
    series: dict[str, float] = Field(default_factory=dict)

    @property
    def is_verified(self) -> bool:
        """True only when the series is explicitly verified with real provenance."""
        if self.verification_status.strip().lower() != "verified":
            return False
        return not any(
            _is_unset(value)
            for value in (self.source_url, self.publication_date, self.retrieved_at)
        )

    @property
    def latest_period(self) -> str | None:
        """Most recent period key (keys sort lexicographically as YYYY-Qn)."""
        return max(self.series) if self.series else None

    def value_for_period(self, period: str | None) -> float | None:
        """Return the index level for a period, or None when it is not covered."""
        if not period:
            return None
        return self.series.get(period)


def _is_unset(value: str) -> bool:
    stripped = str(value).strip().lower()
    return not stripped or stripped.startswith("todo") or stripped in {"unknown", "n/a"}


def period_for_date(date_str: str) -> str | None:
    """Map an ISO date to a calendar-quarter key (``YYYY-Qn``), or None if unparsable."""
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    quarter = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{quarter}"


def prior_year_period(period: str) -> str | None:
    """Return the same quarter one year earlier (``2026-Q3`` -> ``2025-Q3``)."""
    try:
        year_str, quarter = period.split("-Q", 1)
        return f"{int(year_str) - 1}-Q{quarter}"
    except (AttributeError, ValueError):
        return None


def load_market_index(path: str | Path | None = None) -> MarketIndexSnapshot | None:
    """Load the versioned market index.

    Returns ``None`` (never a fabricated default) when the file is absent or cannot
    be parsed, so callers must handle the "index unavailable" case explicitly.
    """
    if path is None:
        candidate = Path(os.environ.get("MARKET_INDEX_PATH", DEFAULT_MARKET_INDEX_FILE))
    else:
        candidate = Path(path)

    if not candidate.exists():
        return None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return MarketIndexSnapshot(**payload)
    except ValidationError:
        return None
