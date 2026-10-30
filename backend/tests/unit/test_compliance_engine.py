"""Compliance engine, rule and output-contract tests."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.compliance.config import ComplianceConfig, RuleSettings
from app.compliance.engine import ComplianceEngine
from app.compliance.rules.base import ComplianceContext
from app.compliance.schemas import (
    ComplianceOutput,
    ComplianceStatus,
    Severity,
)
from app.property.schemas import SharedCaseState, SubjectProperty, ValuationOutput


def _config() -> ComplianceConfig:
    return ComplianceConfig(
        rule_set_version="test-v1",
        rules={
            "KFS-001": RuleSettings(
                verified=True,
                source_ref="test KFS source",
                values={"min_cooling_off_days": 3},
            ),
            "LTV-001": RuleSettings(
                verified=True,
                source_ref="test LTV source",
                values={
                    "bands": [
                        {"max_loan_amount": 3_000_000, "max_ltv_percent": 90.0},
                        {"max_loan_amount": None, "max_ltv_percent": 75.0},
                    ]
                },
            ),
            "RERA-001": RuleSettings(
                verified=True,
                source_ref="test RERA source",
                values={"rera_id_pattern": r"^UP/RERA/[0-9]{4}/[0-9]{3}$"},
            ),
            "TITLE-001": RuleSettings(verified=True, source_ref="test title source"),
            "VAL-001": RuleSettings(
                verified=True,
                source_ref="test valuation source",
                values={
                    "max_model_gap_percent": 15.0,
                    "max_circle_rate_gap_percent": 20.0,
                },
            ),
            "KYC-001": RuleSettings(verified=True, source_ref="test KYC source"),
            "FAIR-001": RuleSettings(
                verified=True,
                source_ref="test fair-lending source",
                values={
                    "allowed_features": [
                        "locality",
                        "living_area_sqft",
                    ]
                },
            ),
            "DATA-001": RuleSettings(
                verified=True,
                source_ref="test source policy",
                values={"max_source_age_days": 365},
            ),
        },
    )


BASE_LOAN: dict[str, Any] = {
    "loan_date": "2026-01-15",
    "loan_amount": 2_000_000,
    "property_value": 3_000_000,
    "annual_interest_rate": 8.5,
    "apr": 9.0,
    "tenure_months": 240,
    "cooling_off_days": 5,
    "under_construction": False,
    "project_registered": True,
    "rera_id": "UP/RERA/2024/001",
    "title_document_present": True,
    "encumbrance_certificate_present": True,
    "cersai_check_present": True,
    "valuer_empanelled": True,
    "valuation_report_present": True,
    "valuation_amount": 3_000_000,
    "circle_rate_value": None,
    "kyc_completed": True,
    "customer_due_diligence_completed": True,
    "pan_verified": True,
    "notes": "Borrower requested a twenty-year term.",
    "features": ["locality", "living_area_sqft"],
    "source_metadata": {
        "source_name": "Test Source Registry",
        "authority": "Test Authority",
        "source_version_or_date": "2026-01-01",
        "source_last_success_at": "2026-01-01",
        "source_effective_to": "2026-12-31",
        "index_version": "idx_test",
        "active_index_version": "idx_test",
    },
}


class FakeRetriever:
    def __init__(self, items: list[Any] | None = None):
        self.items = items if items is not None else [_evidence()]

    def retrieve(
        self,
        query: str,
        state_code: str | None = None,
        loan_date: str | None = None,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[Any]:
        del query, loan_date, threshold
        return self.items[:top_k]


class RaisingRetriever:
    def retrieve(self, *args: Any, **kwargs: Any) -> list[Any]:
        del args, kwargs
        raise RuntimeError("retrieval down")


def _evidence(state_code: str | None = None) -> Any:
    from app.rag.schemas import EvidenceItem

    return EvidenceItem(
        retrieval_ref="chunk-test-1",
        source_name="Test Act",
        authority="Test Authority",
        version_or_date="2026-01-01",
        section_or_page="Section 1",
        scope="state" if state_code else "national",
        state_code=state_code,
        snippet="A verbatim test clause.",
        score=0.9,
        license_scope="test_fixture",
        index_version="idx_test",
    )


def _valuation(estimate: float | None = 3_000_000) -> ValuationOutput:
    return ValuationOutput(
        case_id="case-comp-001",
        subject_id="subject-001",
        estimate=estimate,
        interval_low=2_800_000 if estimate else None,
        interval_high=3_200_000 if estimate else None,
        confidence_level=0.8,
        confidence_label="high",
        n_comps=6,
    )


def _context(
    *,
    overrides: dict[str, Any] | None = None,
    estimate: float | None = 3_000_000,
    loan_date: str | None = "2026-01-15",
) -> ComplianceContext:
    loan_data = {**BASE_LOAN, **(overrides or {})}
    if loan_date is None:
        loan_data.pop("loan_date", None)
    else:
        loan_data["loan_date"] = loan_date
    return ComplianceContext(
        case_id="case-comp-001",
        state_code="UP",
        loan_date=loan_date,
        loan_data=loan_data,
        valuation=_valuation(estimate),
        notes=str(loan_data.get("notes", "")),
        features=loan_data.get("features", []),
        source_metadata=loan_data["source_metadata"],
    )


def _engine(
    *,
    retriever: Any | None = None,
    config: ComplianceConfig | None = None,
) -> ComplianceEngine:
    return ComplianceEngine(
        retriever=retriever if retriever is not None else FakeRetriever(),
        config=config or _config(),
    )


def _by_rule(run: Any, rule_id: str) -> ComplianceOutput:
    return next(finding for finding in run.findings if finding.rule_id == rule_id)


def test_happy_path_all_eight_rules_no_issue() -> None:
    run = _engine().run(_context())

    assert len(run.findings) == 8
    assert all(f.status is ComplianceStatus.NO_ISSUE_DETECTED for f in run.findings)
    assert all(not f.human_review_required for f in run.findings)
    assert run.human_review_required is False
    assert run.evidence
    assert all(f.evidence_refs for f in run.findings)


def test_missing_required_input_fails_closed() -> None:
    run = _engine().run(_context(overrides={"loan_amount": None}))

    for rule_id in ("KFS-001", "LTV-001"):
        finding = _by_rule(run, rule_id)
        assert finding.status is ComplianceStatus.CANNOT_VERIFY
        assert finding.human_review_required is True
        assert any("loan_amount" in item for item in finding.missing_information)


def test_missing_loan_date_fails_closed_for_every_rule() -> None:
    run = _engine().run(_context(loan_date=None))

    assert len(run.findings) == 8
    assert all(f.status is ComplianceStatus.CANNOT_VERIFY for f in run.findings)
    assert all(f.missing_information == ["loan_date"] for f in run.findings)
    assert run.human_review_required is True


def test_empty_retrieval_downgrades_potential_issue() -> None:
    run = _engine(retriever=FakeRetriever([])).run(
        _context(overrides={"cooling_off_days": 1})
    )
    finding = _by_rule(run, "KFS-001")

    assert finding.status is ComplianceStatus.CANNOT_VERIFY
    assert finding.evidence_refs == []
    assert any("approved evidence" in item for item in finding.missing_information)


def test_flagged_rule_has_evidence_and_review_wording() -> None:
    run = _engine().run(_context(overrides={"cooling_off_days": 1}))
    finding = _by_rule(run, "KFS-001")

    assert finding.status is ComplianceStatus.POTENTIAL_ISSUE
    assert finding.severity is Severity.MEDIUM
    assert finding.evidence_refs
    assert "potential issue for review" in finding.explanation.lower()
    assert finding.human_review_required is True


@pytest.mark.parametrize(
    ("rule_id", "overrides", "expected_severity"),
    [
        (
            "LTV-001",
            {"loan_amount": 2_900_000, "property_value": 3_000_000},
            Severity.HIGH,
        ),
        (
            "RERA-001",
            {"under_construction": True, "project_registered": False},
            Severity.HIGH,
        ),
        ("TITLE-001", {"encumbrance_certificate_present": False}, Severity.HIGH),
        ("VAL-001", {"valuation_amount": 3_600_000}, Severity.MEDIUM),
        ("KYC-001", {"pan_verified": False}, Severity.HIGH),
        (
            "FAIR-001",
            {"notes": "The community composition was considered."},
            Severity.HIGH,
        ),
    ],
)
def test_each_rule_can_flag_with_evidence(
    rule_id: str, overrides: dict[str, Any], expected_severity: Severity
) -> None:
    run = _engine().run(_context(overrides=overrides))
    finding = _by_rule(run, rule_id)

    assert finding.status is ComplianceStatus.POTENTIAL_ISSUE
    assert finding.severity is expected_severity
    assert finding.evidence_refs


@pytest.mark.parametrize(
    ("rule_id", "overrides"),
    [
        ("KFS-001", {"apr": None}),
        ("LTV-001", {"property_value": None}),
        ("RERA-001", {"under_construction": None}),
        ("TITLE-001", {"title_document_present": None}),
        ("VAL-001", {"valuation_amount": None}),
        ("KYC-001", {"pan_verified": None}),
        ("FAIR-001", {"notes": "", "features": []}),
        ("DATA-001", {"source_metadata": {}}),
    ],
)
def test_each_rule_missing_data_fails_closed(
    rule_id: str, overrides: dict[str, Any]
) -> None:
    run = _engine().run(_context(overrides=overrides))
    finding = _by_rule(run, rule_id)

    assert finding.status is ComplianceStatus.CANNOT_VERIFY
    assert finding.missing_information
    assert finding.evidence_refs == []
    assert finding.human_review_required is True


@pytest.mark.parametrize(
    "rule_id",
    ["KFS-001", "LTV-001", "RERA-001", "TITLE-001", "VAL-001", "KYC-001", "FAIR-001"],
)
def test_each_evidence_rule_abstains_on_empty_retrieval(rule_id: str) -> None:
    run = _engine(retriever=FakeRetriever([])).run(_context())
    finding = _by_rule(run, rule_id)

    assert finding.status is ComplianceStatus.CANNOT_VERIFY
    assert finding.evidence_refs == []
    assert any("approved evidence" in item for item in finding.missing_information)


def test_fair_rule_rejects_feature_outside_allow_list() -> None:
    run = _engine().run(
        _context(
            overrides={
                "notes": "No proxy terms in the notes.",
                "features": ["locality", "religion_code"],
            }
        )
    )
    finding = _by_rule(run, "FAIR-001")

    assert finding.status is ComplianceStatus.POTENTIAL_ISSUE
    assert finding.severity is Severity.MEDIUM
    assert "allow-list" in finding.explanation


def test_data_rule_stale_source_is_cannot_verify() -> None:
    run = _engine().run(
        _context(
            overrides={
                "source_metadata": {
                    **BASE_LOAN["source_metadata"],
                    "source_last_success_at": "2024-01-01",
                }
            }
        )
    )
    finding = _by_rule(run, "DATA-001")

    assert finding.status is ComplianceStatus.CANNOT_VERIFY
    assert finding.severity is None
    assert any("freshness" in item for item in finding.missing_information)
    assert finding.evidence_refs == []


def test_data_rule_uses_system_evidence_when_fresh() -> None:
    run = _engine().run(_context())
    finding = _by_rule(run, "DATA-001")

    assert finding.status is ComplianceStatus.NO_ISSUE_DETECTED
    assert finding.evidence_refs
    system_evidence = next(
        item for item in run.evidence if item.retrieval_ref == "source_registry"
    )
    assert "source_last_success_at" in system_evidence.snippet


def test_foreign_state_evidence_is_filtered_out() -> None:
    mh_evidence = _evidence(state_code="MH")
    run = _engine(retriever=FakeRetriever([mh_evidence])).run(_context())

    first_rule = _by_rule(run, "KFS-001")
    assert first_rule.status is ComplianceStatus.CANNOT_VERIFY
    assert first_rule.evidence_refs == []


def test_retrieval_failure_fails_closed() -> None:
    run = _engine(retriever=RaisingRetriever()).run(_context())

    # DATA-001 is a system check and does not call the evidence retriever.
    assert all(
        f.status is ComplianceStatus.CANNOT_VERIFY
        for f in run.findings
        if f.rule_id != "DATA-001"
    )
    assert _by_rule(run, "DATA-001").status is ComplianceStatus.NO_ISSUE_DETECTED
    assert run.human_review_required is True


def test_default_config_never_uses_unverified_thresholds() -> None:
    run = _engine(config=ComplianceConfig.load()).run(_context())

    for rule_id in ("KFS-001", "LTV-001", "VAL-001", "DATA-001"):
        finding = _by_rule(run, rule_id)
        assert finding.status is ComplianceStatus.CANNOT_VERIFY
        assert any(
            "verified" in item.lower() or "reviewed" in item.lower()
            for item in finding.missing_information
        )


def test_rule_set_version_is_recorded() -> None:
    run = _engine().run(_context())
    assert run.rule_set_version == "test-v1"
    assert all(f.rule_set_version == "test-v1" for f in run.findings)


def test_output_contract_rejects_evidence_less_flag() -> None:
    with pytest.raises(ValidationError):
        ComplianceOutput(
            case_id="case-comp-001",
            rule_id="KFS-001",
            rule_set_version="test-v1",
            status=ComplianceStatus.POTENTIAL_ISSUE,
            severity=Severity.HIGH,
            affected_requirement="KFS test",
            evidence_refs=[],
            explanation="Potential issue for review: test flag.",
        )


def test_output_contract_rejects_legal_conclusion() -> None:
    with pytest.raises(ValidationError):
        ComplianceOutput(
            case_id="case-comp-001",
            rule_id="KFS-001",
            rule_set_version="test-v1",
            status=ComplianceStatus.NO_ISSUE_DETECTED,
            affected_requirement="KFS test",
            evidence_refs=[uuid4()],
            explanation="The lender is compliant with the rule.",
        )


def test_output_contract_requires_review_wording_for_flag() -> None:
    with pytest.raises(ValidationError):
        ComplianceOutput(
            case_id="case-comp-001",
            rule_id="KFS-001",
            rule_set_version="test-v1",
            status=ComplianceStatus.POTENTIAL_ISSUE,
            severity=Severity.HIGH,
            affected_requirement="KFS test",
            evidence_refs=[uuid4()],
            explanation="This is a definite problem.",
        )


def test_output_contract_forces_human_review_on_cannot_verify() -> None:
    finding = ComplianceOutput(
        case_id="case-comp-001",
        rule_id="KFS-001",
        rule_set_version="test-v1",
        status=ComplianceStatus.CANNOT_VERIFY,
        affected_requirement="KFS test",
        missing_information=["KFS cooling-off threshold"],
        explanation="Cannot verify: threshold unavailable.",
    )

    assert finding.human_review_required is True


def test_output_contract_keeps_no_issue_out_of_human_review() -> None:
    finding = ComplianceOutput(
        case_id="case-comp-001",
        rule_id="KFS-001",
        rule_set_version="test-v1",
        status=ComplianceStatus.NO_ISSUE_DETECTED,
        affected_requirement="KFS test",
        evidence_refs=[uuid4()],
        explanation="No issue detected by this rule.",
    )

    assert finding.human_review_required is False


def _state(overrides: dict[str, Any] | None = None) -> SharedCaseState:
    subject = SubjectProperty(
        original_address="Flat 302, Gomti Nagar, Lucknow",
        address_norm="Flat 302, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_sqft=1100,
        lat=26.85,
        lon=80.99,
    )
    return SharedCaseState(
        case_id="case-comp-001",
        subject_property=subject,
        loan_data={**BASE_LOAN, **(overrides or {})},
        model_output=_valuation(),
        status="valued",
    )


def test_compliance_agent_updates_state_and_audit() -> None:
    from app.agents.compliance_agent import ComplianceAgent

    agent = ComplianceAgent(engine=_engine())
    updated = agent.evaluate(_state())

    assert len(updated.compliance) == 8
    assert updated.evidence
    assert updated.status == "compliance_checked"
    assert updated.human_review_required is False
    assert updated.audit_trail[-1].actor == "compliance_agent"
    assert updated.audit_trail[-1].node == "compliance_check"


def test_compliance_agent_escalates_on_open_finding() -> None:
    from app.agents.compliance_agent import ComplianceAgent

    agent = ComplianceAgent(engine=_engine())
    updated = agent.evaluate(_state({"pan_verified": False}))

    assert updated.status == "needs_review"
    assert updated.human_review_required is True
    assert any(
        finding["rule_id"] == "KYC-001"
        and finding["status"] == ComplianceStatus.POTENTIAL_ISSUE.value
        for finding in updated.compliance
    )


def test_compliance_agent_without_retriever_abstains() -> None:
    from app.agents.compliance_agent import ComplianceAgent

    agent = ComplianceAgent(engine=ComplianceEngine(config=_config()))
    updated = agent.evaluate(_state())

    assert updated.status == "needs_review"
    assert updated.human_review_required is True
    assert any(
        finding["status"] == ComplianceStatus.CANNOT_VERIFY.value
        for finding in updated.compliance
    )


def test_commands_run_compliance_evidence_review_and_approve() -> None:
    from app.agents.compliance_agent import ComplianceAgent
    from app.property.commands import LoanOfficerCommandHandler

    handler = LoanOfficerCommandHandler(
        allow_synthetic=True,
        compliance_agent=ComplianceAgent(engine=_engine()),
    )
    handler.intake(
        case_id="case-comp-cmd",
        address="Flat 302, 2 BHK, Gomti Nagar, Lucknow",
        locality="Gomti Nagar",
        city="Lucknow",
        state_code="UP",
        living_area_raw="1100 sqft",
        price_quoted_raw="60 Lac",
    )
    handler.valuate("case-comp-cmd")
    # Commands use their own state, so inject the compliance loan data directly.
    state = handler.cases["case-comp-cmd"]
    state.loan_data.update(BASE_LOAN)
    if state.model_output and state.model_output.estimate:
        state.loan_data["valuation_amount"] = state.model_output.estimate
        state.loan_data["property_value"] = state.model_output.estimate * 1.5

    result = handler.compliance("case-comp-cmd")
    assert result["finding_count"] == 8
    assert result["human_review_required"] is False

    finding_id = result["findings"][0]["finding_id"]
    evidence = handler.evidence("case-comp-cmd", finding_id)
    assert evidence["evidence_count"] >= 1

    reviewed = handler.review(
        "case-comp-cmd",
        decision="accept",
        note="Reviewed with evidence.",
        reviewer="reviewer-1",
    )
    assert reviewed["status"] == "reviewed"

    approved = handler.approve("case-comp-cmd")
    assert approved["status"] == "approved"
    assert approved["eligible"] is True


def test_commands_block_privileged_actions_for_loan_officer() -> None:
    from app.property.commands import LoanOfficerCommandHandler

    handler = LoanOfficerCommandHandler(allow_synthetic=True)

    with pytest.raises(PermissionError):
        handler.approve("missing", role="loan_officer")
    with pytest.raises(PermissionError):
        handler.sources(role="loan_officer")


def test_sources_command_reports_zero_approved_sources() -> None:
    from app.property.commands import LoanOfficerCommandHandler

    handler = LoanOfficerCommandHandler(allow_synthetic=True)
    result = handler.sources(role="admin")

    assert result["count"] >= 8
    assert result["approved_count"] == 0
    assert "approved" in result["warning"].lower()


def test_compliance_api_endpoint_runs_agent() -> None:
    from app.agents.compliance_agent import ComplianceAgent
    from app.api.compliance import check_compliance
    from app.schemas.compliance import ComplianceCheckRequest

    payload = ComplianceCheckRequest(
        case_id="case-comp-001",
        subject=_state().subject_property,
        loan_data=dict(BASE_LOAN),
        valuation=_valuation(),
    )
    response = check_compliance(payload, ComplianceAgent(engine=_engine()))

    assert response.rule_set_version == "test-v1"
    assert len(response.findings) == 8
    assert response.evidence
    assert response.human_review_required is False


def test_compliance_api_rejects_raw_kyc_identifiers() -> None:
    from app.schemas.compliance import ComplianceCheckRequest

    with pytest.raises(ValidationError):
        ComplianceCheckRequest(
            case_id="case-comp-001",
            subject=_state().subject_property,
            loan_data={**BASE_LOAN, "pan": "ABCDE1234F"},
        )


@pytest.mark.asyncio
async def test_compliance_api_returns_422_for_raw_pii() -> None:
    from httpx import ASGITransport, AsyncClient

    from app.main import app
    from app.security.auth import require_api_key

    app.dependency_overrides[require_api_key] = lambda: None
    try:
        payload = {
            "case_id": "case-comp-001",
            "subject": _state().subject_property.model_dump(mode="json"),
            "loan_data": {**BASE_LOAN, "pan": "ABCDE1234F"},
        }
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/compliance/check", json=payload)
    finally:
        app.dependency_overrides.pop(require_api_key, None)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert "Raw KYC identifiers are not accepted" in str(body)


def test_guardrail_gate_rejects_evidence_less_compliance_flag() -> None:
    from app.property.gate import GuardrailGate

    state = _state()
    state.human_review_required = True
    state.compliance = [
        {
            "rule_id": "KFS-001",
            "status": "potential_issue",
            "severity": "high",
            "evidence_refs": [],
            "missing_information": [],
            "explanation": "Potential issue for review: test.",
        }
    ]

    violations = GuardrailGate.verify(state)

    assert any("Invariant 3" in item for item in violations)


def test_guardrail_gate_rejects_legal_conclusion() -> None:
    from app.property.gate import GuardrailGate

    state = _state()
    state.human_review_required = True
    state.evidence = [{"evidence_id": "ev-1", "state_code": None}]
    state.compliance = [
        {
            "rule_id": "KFS-001",
            "status": "no_issue_detected",
            "severity": None,
            "evidence_refs": ["ev-1"],
            "missing_information": [],
            "explanation": "The lender is compliant.",
        }
    ]

    violations = GuardrailGate.verify(state)

    assert any("Invariant 7" in item for item in violations)
