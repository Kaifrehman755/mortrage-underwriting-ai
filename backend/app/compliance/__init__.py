"""Compliance package initialization."""

from app.compliance.config import ComplianceConfig, RuleSettings
from app.compliance.engine import (
    ComplianceEngine,
    EvidenceRetriever,
    NullEvidenceRetriever,
)
from app.compliance.fair_lending import FairLendingAuditor
from app.compliance.fnma_fhlmc import ConformingLoanGuidelines
from app.compliance.hmda import HMDARules
from app.compliance.respa import RESPARules
from app.compliance.rules import default_rules
from app.compliance.schemas import (
    ComplianceOutput,
    ComplianceRun,
    ComplianceStatus,
    Severity,
)
from app.compliance.tila import TILARules

# Backwards-compatible name for the old placeholder class.
ComplianceRuleEngine = ComplianceEngine

__all__ = [
    "ComplianceConfig",
    "ComplianceEngine",
    "ComplianceOutput",
    "ComplianceRuleEngine",
    "ComplianceRun",
    "ComplianceStatus",
    "ConformingLoanGuidelines",
    "EvidenceRetriever",
    "NullEvidenceRetriever",
    "RESPARules",
    "RuleSettings",
    "Severity",
    "TILARules",
    "HMDARules",
    "FairLendingAuditor",
    "default_rules",
]
