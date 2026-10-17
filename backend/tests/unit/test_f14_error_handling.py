"""F-14 regression tests: no failure hiding and no raw exception disclosure.

Verifies (Phase 2, Priority 6 — F-14):
1. An unexpected agent error surfaces as a **generic reason code** with a correlation id, sets
   ``human_review_required``, and never embeds the raw exception text in the model output.
2. The raw exception text/`full traceback` is still recorded **server-side** (logged), so the
   failure is not hidden — only not disclosed.
3. The recency-weight fallback for an unparseable ``sale_date`` is logged, not silent.
4. An unparseable ``sale_date`` is reason-coded during normalization (already non-silent).
5. A static guard: the in-scope property modules contain no bare/``except Exception`` swallows
   except the single documented last-resort handler in the agent.
"""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from app.agents.property_agent import UNEXPECTED_AGENT_ERROR, PropertyAgent
from app.property.comps import ComparableSalesAnalyzer
from app.property.jurisdictions import get_jurisdiction
from app.property.normalize import clean_raw_record
from app.property.provider import CompProvider
from app.property.schemas import (
    ComparableRecord,
    SharedCaseState,
    SubjectProperty,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"

SECRET = "SECRET-/etc/passwd-token-abc123"


@pytest.fixture
def subject_up() -> SubjectProperty:
    """Subject property in Gomti Nagar, Lucknow (UP pilot)."""
    return SubjectProperty(
        original_address="Flat 402, Shalimar Grand, Gomti Nagar, Lucknow",
        address_norm="Flat 402, Shalimar Grand, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        pincode="226010",
        property_type="apartment",
        living_area_sqft=1250.0,
        area_basis="carpet",
        lat=26.8530,
        lon=80.9980,
    )


class _ExplodingProvider(CompProvider):
    """Provider stub that fails with a non-ProviderUnavailable error carrying sensitive text."""

    def fetch_comps(
        self,
        subject: SubjectProperty,
        radius_km: float = 3.0,
        months: int = 12,
        filters: dict[str, Any] | None = None,
    ) -> list[ComparableRecord]:
        raise RuntimeError(f"boom at {SECRET}")


# ---------------------------------------------------------------------------
# 1 & 2. Agent last-resort handler: generic output, detailed log
# ---------------------------------------------------------------------------

def test_unexpected_error_yields_generic_reason_code_without_leaking(subject_up):
    agent = PropertyAgent(provider=_ExplodingProvider())
    state = SharedCaseState(case_id="case_f14_leak", subject_property=subject_up)

    result = agent.evaluate(state)

    assert result.model_output is not None
    assert result.model_output.abstain_reason == UNEXPECTED_AGENT_ERROR
    assert result.model_output.estimate is None
    assert result.human_review_required is True
    assert result.status == "needs_review"
    assert result.market_facts == []

    # The raw exception text must appear nowhere in the model output or the audit trail.
    serialized_output = json.dumps(result.model_output.model_dump(), default=str)
    serialized_audit = json.dumps([event.model_dump() for event in result.audit_trail], default=str)
    assert SECRET not in serialized_output
    assert SECRET not in serialized_audit
    assert "RuntimeError" not in serialized_output
    assert "RuntimeError" not in serialized_audit

    # A short, non-sensitive correlation id is recorded for log cross-referencing.
    event = result.audit_trail[-1]
    correlation_id = event.details.get("correlation_id")
    assert isinstance(correlation_id, str) and len(correlation_id) == 12
    assert all(ch in "0123456789abcdef" for ch in correlation_id)
    assert correlation_id in event.details["note"]


def test_unexpected_error_is_logged_server_side_with_traceback(subject_up, caplog):
    agent = PropertyAgent(provider=_ExplodingProvider())
    state = SharedCaseState(case_id="case_f14_log", subject_property=subject_up)

    with caplog.at_level(logging.ERROR, logger="app.agents.property_agent"):
        agent.evaluate(state)

    records = [r for r in caplog.records if r.name == "app.agents.property_agent"]
    assert records, "the failure must be logged, not silently swallowed"
    record = records[-1]
    assert "Unexpected error in PropertyAgent" in record.getMessage()
    assert "correlation_id=" in record.getMessage()
    assert "case_f14_log" in record.getMessage()
    # Full detail (traceback) is preserved server-side for diagnosis.
    assert record.exc_info is not None


# ---------------------------------------------------------------------------
# 3. Recency-weight fallback is observable
# ---------------------------------------------------------------------------

def test_unparseable_sale_date_warns_and_keeps_weight_finite(subject_up, caplog):
    comp = ComparableRecord(
        comp_id="BAD-DATE",
        source_name="test-fixture",
        provider_record_id="r1",
        address="Somewhere",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        property_type="apartment",
        sale_price=5_000_000.0,
        sale_date="not-a-date",
        living_area_sqft=1000.0,
        price_per_sqft=5000.0,
        price_type="registered_deed",
        license_scope="test",
        distance_km=1.0,
    )
    analyzer = ComparableSalesAnalyzer()

    with caplog.at_level(logging.WARNING, logger="app.property.comps"):
        weights = analyzer.compute_similarity_weights(subject_up, [comp])

    assert weights == [1.0]
    assert any("Unparseable sale_date" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# 4. Normalization reason code for an unparseable date
# ---------------------------------------------------------------------------

def test_unparseable_sale_date_is_reason_coded():
    jurisdiction = get_jurisdiction("UP")
    row = {
        "price_raw": "50 Lac",
        "area_raw": "1000 sqft",
        "date_raw": "not-a-date",
        "lat": 26.85,
        "lon": 80.99,
    }

    cleaned, reasons = clean_raw_record(row, jurisdiction)

    assert cleaned is None
    assert any(reason.startswith("unparseable_sale_date") for reason in reasons)


# ---------------------------------------------------------------------------
# 5. Static guard against new broad/bare excepts creeping back in
# ---------------------------------------------------------------------------

def _handler_type_names(handler: ast.ExceptHandler) -> set[str] | None:
    """Return the caught exception names, or ``None`` for a bare ``except:``."""
    if handler.type is None:
        return None
    node: Any = handler.type
    parts = node.elts if isinstance(node, ast.Tuple) else [node]
    names: set[str] = set()
    for part in parts:
        if isinstance(part, ast.Name):
            names.add(part.id)
        elif isinstance(part, ast.Attribute):
            names.add(part.attr)
    return names


def _handler_types(rel_path: str) -> list[set[str] | None]:
    tree = ast.parse((BACKEND / rel_path).read_text(encoding="utf-8"))
    return [
        _handler_type_names(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
    ]


@pytest.mark.parametrize(
    "rel_path",
    [
        "app/property/comps.py",
        "app/property/normalize.py",
        "app/property/valuation.py",
    ],
)
def test_property_modules_have_no_bare_or_broad_except(rel_path: str):
    handlers = _handler_types(rel_path)
    assert None not in handlers, f"bare `except:` found in {rel_path}"
    broad = [h for h in handlers if h and (h & {"Exception", "BaseException"})]
    assert not broad, f"`except Exception` found in {rel_path}: {broad}"


def test_agent_has_exactly_one_documented_last_resort_handler():
    handlers = _handler_types("app/agents/property_agent.py")
    assert None not in handlers, "bare `except:` found in property_agent.py"
    broad = [h for h in handlers if h and (h & {"Exception", "BaseException"})]
    assert len(broad) == 1, f"expected exactly one last-resort handler, found {len(broad)}"
