"""Property Valuation and Appraisal module — **canonical live AVM engine (F-10)**.

Designated canonical for the India property-valuation backend: it is the path wired into a live
entry point (``PropertyAgent``) and it carries the F-01 synthetic-exclusion gate and the F-02
market-index gating/abstention. The stricter GEMINI engine under ``app.valuation`` is the
migration target, not the current canon — see ``docs/architecture/canonical_pipeline.md``.
"""

from app.property.comps import ComparableSalesAnalyzer
from app.property.gate import GuardrailGate, GuardrailGateViolation
from app.property.jurisdictions import JurisdictionPack, get_jurisdiction
from app.property.normalize import (
    clean_raw_record,
    flag_outliers_mad,
    haversine_km,
    parse_area_sqft,
    parse_bhk,
    parse_pincode,
    parse_price_inr,
)
from app.property.provider import CompProvider, ProviderUnavailable
from app.property.providers.assessor_csv import AssessorCsvProvider
from app.property.providers.synthetic import SyntheticProvider
from app.property.schemas import (
    AuditEvent,
    ComparableRecord,
    MarketIndicator,
    SharedCaseState,
    SubjectProperty,
    ValuationOutput,
)
from app.property.valuation import PropertyValuationEngine

__all__ = [
    "ComparableSalesAnalyzer",
    "GuardrailGate",
    "GuardrailGateViolation",
    "JurisdictionPack",
    "get_jurisdiction",
    "clean_raw_record",
    "flag_outliers_mad",
    "haversine_km",
    "parse_price_inr",
    "parse_area_sqft",
    "parse_bhk",
    "parse_pincode",
    "CompProvider",
    "ProviderUnavailable",
    "SyntheticProvider",
    "AssessorCsvProvider",
    "SubjectProperty",
    "ComparableRecord",
    "ValuationOutput",
    "MarketIndicator",
    "SharedCaseState",
    "AuditEvent",
    "PropertyValuationEngine",
]
