"""SQLAlchemy ORM model for compliance findings.

The database mirrors invariant 3: a finding cannot be flagged unless it carries
at least one evidence reference. Only the three playbook statuses are allowed,
and the wording rule is enforced by the Pydantic output contract.
"""

from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ComplianceFinding(Base, TimestampMixin):
    """One rule result with evidence references and missing-information metadata."""

    __tablename__ = "compliance_finding"

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    state_code: Mapped[str | None] = mapped_column(
        String(2), ForeignKey("jurisdiction.state_code"), nullable=True, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rule_set_version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    affected_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        default=list,
        server_default="{}",
    )
    missing_information: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="'[]'::jsonb"
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    human_review_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('no_issue_detected','potential_issue','cannot_verify')",
            name="ck_compliance_finding_status",
        ),
        CheckConstraint(
            "severity IS NULL OR severity IN ('low','medium','high')",
            name="ck_compliance_finding_severity",
        ),
        CheckConstraint(
            "status = 'cannot_verify' OR cardinality(evidence_refs) > 0",
            name="ck_compliance_finding_evidence_required",
        ),
        CheckConstraint(
            "status <> 'cannot_verify' OR human_review_required",
            name="ck_compliance_finding_cannot_verify_review",
        ),
    )
