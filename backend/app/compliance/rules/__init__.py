"""India starter rule pack registry."""

from __future__ import annotations

from typing import cast

from app.compliance.rules.base import ComplianceRule
from app.compliance.rules.data import DataSourceRule
from app.compliance.rules.fair import FairLendingRule
from app.compliance.rules.kfs import KFSRule
from app.compliance.rules.kyc import KYCRule
from app.compliance.rules.ltv import LTVRule
from app.compliance.rules.rera import RERARule
from app.compliance.rules.title import TitleRule
from app.compliance.rules.valuation_rule import ValuationRule


def default_rules() -> list[ComplianceRule]:
    """Return a fresh list of the eight starter rules."""
    return cast(
        list[ComplianceRule],
        [
            KFSRule(),
            LTVRule(),
            RERARule(),
            TitleRule(),
            ValuationRule(),
            KYCRule(),
            FairLendingRule(),
            DataSourceRule(),
        ],
    )


__all__ = [
    "ComplianceRule",
    "DataSourceRule",
    "FairLendingRule",
    "KFSRule",
    "KYCRule",
    "LTVRule",
    "RERARule",
    "TitleRule",
    "ValuationRule",
    "default_rules",
]
