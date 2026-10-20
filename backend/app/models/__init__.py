"""Legacy database models package — DEPRECATED (F-10).

.. deprecated::
    This tree models the out-of-scope US-mortgage placeholder layer. The **canonical** ORM for
    the India property-valuation backend is ``app.database.models``. These modules are retained
    only until their references and compatibility implications are understood (Phase-2
    Priority 5, F-10) and MUST NOT be used by new code.

    See ``docs/architecture/canonical_pipeline.md``.

Importing this package emits a :class:`DeprecationWarning`.
"""

import warnings

from app.models.applicant import Applicant
from app.models.application import Application
from app.models.audit import AuditLog
from app.models.credit import CreditProfile
from app.models.decision import UnderwritingDecision
from app.models.document import Document
from app.models.property import Property
from app.models.risk import RiskAssessment

warnings.warn(
    "app.models is a legacy US-mortgage model tree; use app.database.models instead "
    "(see docs/architecture/canonical_pipeline.md).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "Application",
    "Applicant",
    "Document",
    "Property",
    "CreditProfile",
    "RiskAssessment",
    "UnderwritingDecision",
    "AuditLog",
]
