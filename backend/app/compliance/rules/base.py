"""Shared rule contracts and helpers for the India starter rule pack."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, ClassVar, Protocol

from app.compliance.config import RuleSettings
from app.compliance.schemas import ComplianceStatus, Severity
from app.property.schemas import ComparableRecord, ValuationOutput


@dataclass(frozen=True)
class CheckResult:
    """A rule's result before evidence is attached by the engine."""

    status: ComplianceStatus
    explanation: str
    severity: Severity | None = None
    missing_information: list[str] = field(default_factory=list)


def cannot_verify(explanation: str, missing_information: list[str]) -> CheckResult:
    """Build a fail-closed result. Missing information is mandatory."""
    if not missing_information:
        missing_information = ["Unspecified missing information"]
    return CheckResult(
        status=ComplianceStatus.CANNOT_VERIFY,
        explanation=f"Cannot verify: {explanation} Human review required.",
        missing_information=missing_information,
    )


def potential_issue(explanation: str, severity: Severity = Severity.MEDIUM) -> CheckResult:
    """Build a review flag. The engine still requires attached evidence."""
    return CheckResult(
        status=ComplianceStatus.POTENTIAL_ISSUE,
        explanation=f"Potential issue for review: {explanation}",
        severity=severity,
    )


def no_issue(explanation: str) -> CheckResult:
    """Build a no-issue result with neutral, non-legal wording."""
    return CheckResult(
        status=ComplianceStatus.NO_ISSUE_DETECTED,
        explanation=f"No issue detected by this rule. {explanation}".strip(),
    )


@dataclass
class ComplianceContext:
    """Case data visible to deterministic compliance rules.

    The context intentionally exposes statuses and booleans rather than raw KYC
    identifiers. Rules must never receive or persist PAN/Aadhaar values.
    """

    case_id: str
    state_code: str
    loan_date: str | None
    loan_data: dict[str, Any]
    valuation: ValuationOutput | None = None
    market_facts: list[ComparableRecord] = field(default_factory=list)
    notes: str = ""
    features: list[str] = field(default_factory=list)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def resolve(self, name: str) -> Any:
        """Resolve a rule input from the context without implicit defaults."""
        if name == "loan_date":
            return self.loan_date
        if name == "notes":
            return self.loan_data.get("notes", self.notes)
        if name == "features":
            return self.loan_data.get("features", self.features)
        if name == "model_estimate":
            return self.valuation.estimate if self.valuation else None
        if name == "model_interval_low":
            return self.valuation.interval_low if self.valuation else None
        if name == "model_interval_high":
            return self.valuation.interval_high if self.valuation else None
        if name == "model_confidence":
            return self.valuation.confidence_label if self.valuation else None
        if name == "subject_property_type":
            return self.loan_data.get("property_type")
        if name in self.loan_data:
            return self.loan_data[name]
        return self.source_metadata.get(name)

    def missing(self, names: tuple[str, ...]) -> list[str]:
        """Return required input names whose resolved value is absent."""
        return [name for name in names if _is_missing(self.resolve(name))]

    def as_of_date(self) -> date | None:
        """Parse the loan date used for as-of retrieval and rule checks."""
        return _parse_date(self.loan_date)

    def source_json(self) -> str:
        """Stable JSON representation of source metadata for system evidence."""
        return json.dumps(self.source_metadata, sort_keys=True, default=str)


class ComplianceRule(Protocol):
    """Protocol implemented by every starter rule."""

    rule_id: ClassVar[str]
    requirement: ClassVar[str]
    required_inputs: ClassVar[tuple[str, ...]]
    evidence_query: ClassVar[str | None]
    requires_config: ClassVar[bool]

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        """Evaluate the rule's deterministic checks."""
        ...


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
        return True
    return False


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def as_number(value: Any) -> float | None:
    """Parse a finite number without accepting booleans or magic strings."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def as_int(value: Any) -> int | None:
    number = as_number(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def as_bool(value: Any) -> bool | None:
    """Accept only explicit booleans; do not impute truth from arbitrary values."""
    return value if isinstance(value, bool) else None


def format_names(names: list[str]) -> str:
    return ", ".join(names)
