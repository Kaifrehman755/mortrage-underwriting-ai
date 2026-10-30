"""Compliance output contracts.

Enforces the playbook's compliance invariants:

* Status is only ``no_issue_detected``, ``potential_issue`` or ``cannot_verify``;
  the word "compliant" is never a status.
* A finding that is not ``cannot_verify`` must carry at least one evidence reference.
  This mirrors the database check required by the playbook.
* ``potential_issue`` must carry a severity and use the wording
  "potential issue for review"; legal conclusions are rejected.
* ``cannot_verify`` always sets ``human_review_required``.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.rag.schemas import EvidenceItem


class ComplianceStatus(StrEnum):
    """The only permitted compliance statuses."""

    NO_ISSUE_DETECTED = "no_issue_detected"
    POTENTIAL_ISSUE = "potential_issue"
    CANNOT_VERIFY = "cannot_verify"


class Severity(StrEnum):
    """Finding severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_LEGAL_CONCLUSION_PATTERN = re.compile(
    r"\b(violation|violates|violated|compliant|illegal|legally liable)\b",
    re.IGNORECASE,
)


class ComplianceOutput(BaseModel):
    """A single rule result plus its evidence references.

    This is the contract the playbook requires. It deliberately does not contain a
    free-form ``compliant`` flag: a reviewer reads the status and the evidence.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    finding_id: UUID = Field(default_factory=uuid4)
    case_id: str = Field(..., min_length=1)
    rule_id: str = Field(..., min_length=1)
    rule_set_version: str = Field(..., min_length=1)
    status: ComplianceStatus
    severity: Severity | None = None
    affected_requirement: str = Field(..., min_length=1)
    evidence_refs: list[UUID] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)
    human_review_required: bool = False

    @model_validator(mode="after")
    def validate_contract(self) -> ComplianceOutput:
        """Enforce invariant 3, invariant 7 and the human-review rule."""
        if self.status is not ComplianceStatus.CANNOT_VERIFY and not self.evidence_refs:
            raise ValueError(
                "A compliance finding requires at least one evidence reference unless "
                "status is cannot_verify"
            )

        if self.status is ComplianceStatus.CANNOT_VERIFY:
            if not self.missing_information:
                raise ValueError(
                    "cannot_verify findings must state the missing information"
                )
            if self.severity is not None:
                raise ValueError("cannot_verify findings must not carry a severity")
            self.human_review_required = True

        if self.status is ComplianceStatus.NO_ISSUE_DETECTED:
            if self.severity is not None:
                raise ValueError("no_issue_detected findings must not carry a severity")
            if "potential issue for review" in self.explanation.lower():
                raise ValueError(
                    "no_issue_detected findings must not use potential-issue wording"
                )
            self.human_review_required = False

        if self.status is ComplianceStatus.POTENTIAL_ISSUE:
            if "potential issue for review" not in self.explanation.lower():
                raise ValueError(
                    "potential_issue findings must use the wording "
                    "'potential issue for review'"
                )
            if self.severity is None:
                raise ValueError("potential_issue findings must carry a severity")
            self.human_review_required = True

        if _LEGAL_CONCLUSION_PATTERN.search(self.explanation):
            raise ValueError(
                "Compliance explanations must not state or imply a legal conclusion"
            )

        return self


class ComplianceRun(BaseModel):
    """The full result of running a rule pack for one case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    rule_set_version: str
    findings: list[ComplianceOutput] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    human_review_required: bool = False

    @property
    def status(self) -> str:
        """Aggregate case status for the shared case state."""
        return "needs_review" if self.human_review_required else "compliance_checked"

    def summary(self) -> dict[str, Any]:
        """Return a small, non-sensitive summary suitable for commands or reports."""
        counts = {status.value: 0 for status in ComplianceStatus}
        for finding in self.findings:
            counts[finding.status.value] += 1
        return {
            "case_id": self.case_id,
            "rule_set_version": self.rule_set_version,
            "finding_count": len(self.findings),
            "status_counts": counts,
            "human_review_required": self.human_review_required,
            "evidence_count": len(self.evidence),
        }
