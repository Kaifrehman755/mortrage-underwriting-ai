"""FAIR-001: protected-class proxies in case notes and model features."""

from __future__ import annotations

from typing import Any

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    cannot_verify,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity
from app.property.normalize import check_protected_class_proxies


class FairLendingRule:
    rule_id = "FAIR-001"
    requirement = (
        "Case notes and valuation features do not contain protected-class proxies "
        "or discriminatory terms"
    )
    required_inputs: tuple[str, ...] = ()
    evidence_query = (
        "Article 15 Constitution of India non-discrimination RBI fair lending "
        "protected attributes valuation features"
    )
    requires_config = True

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        raw_notes = ctx.resolve("notes")
        raw_features = ctx.resolve("features")

        if raw_notes is None and raw_features is None:
            return cannot_verify(
                "neither case notes nor valuation features were supplied.",
                ["case notes or valuation feature names"],
            )
        if raw_notes is not None and not isinstance(raw_notes, str):
            return cannot_verify(
                "case notes are not text and cannot be screened.",
                ["text case notes"],
            )

        feature_names = _feature_names(raw_features)
        if feature_names is None:
            return cannot_verify(
                "valuation feature names are not a list or mapping and cannot be "
                "screened.",
                ["list or mapping of valuation feature names"],
            )

        if not (raw_notes or feature_names):
            return cannot_verify(
                "case notes are empty and no valuation feature names were supplied.",
                ["non-empty case notes or valuation feature names"],
            )

        allowed_features = settings.values.get("allowed_features")
        if (
            not settings.verified
            or not isinstance(allowed_features, list)
            or not allowed_features
        ):
            return cannot_verify(
                "no reviewed feature allow-list is configured for FAIR-001.",
                [
                    "verified valuation feature allow-list "
                    f"({settings.source_ref})"
                ],
            )
        allowed = {str(name) for name in allowed_features}

        note_proxies = check_protected_class_proxies(raw_notes or "")
        feature_proxies: list[str] = []
        for feature in feature_names:
            feature_proxies.extend(check_protected_class_proxies(feature))
        feature_proxies = sorted(set(feature_proxies))
        unknown_features = sorted(
            name for name in feature_names if name not in allowed
        )

        parts: list[str] = []
        if note_proxies:
            parts.append(
                "case notes contain protected-class proxy term(s): "
                + ", ".join(sorted(set(note_proxies)))
            )
        if feature_proxies:
            parts.append(
                "valuation feature names contain protected-class proxy term(s): "
                + ", ".join(feature_proxies)
            )
        if unknown_features:
            parts.append(
                "valuation feature names are not on the reviewed allow-list: "
                + ", ".join(unknown_features)
            )

        if parts:
            severity = Severity.HIGH if (note_proxies or feature_proxies) else Severity.MEDIUM
            return potential_issue("; ".join(parts) + ".", severity)

        return no_issue(
            "No protected-class proxy term was found and every valuation feature "
            "is on the reviewed allow-list."
        )


def _feature_names(raw: Any) -> list[str] | None:
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [str(name) for name in raw]
    if isinstance(raw, (list, tuple, set)):
        return [str(name) for name in raw]
    return None
