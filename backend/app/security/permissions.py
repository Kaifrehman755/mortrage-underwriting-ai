"""Role-Based Access Control (RBAC) and permissions (Reserved for Phase 1+)."""

from enum import StrEnum


class UserRole(StrEnum):
    """User roles for mortgage underwriting system."""

    BORROWER = "borrower"
    LOAN_OFFICER = "loan_officer"
    UNDERWRITER = "underwriter"
    COMPLIANCE_AUDITOR = "compliance_auditor"
    ADMIN = "admin"
