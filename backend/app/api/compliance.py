"""Regulatory compliance API endpoints.

The endpoint is stateless: the caller supplies the case, subject property and
already-retrieved valuation/market facts. The compliance agent runs the
deterministic rule pack and returns evidence references. No LLM is used to set
a status, and a case with no approved evidence abstains.

Protected by default (F-05): every route added here inherits the
``require_api_key`` dependency. See ``docs/security/access_policy.md``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.agents.compliance_agent import ComplianceAgent
from app.compliance.schemas import ComplianceOutput
from app.property.schemas import SharedCaseState
from app.rag.schemas import EvidenceItem
from app.schemas.compliance import ComplianceCheckRequest, ComplianceCheckResponse
from app.security.auth import require_api_key

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"],
    dependencies=[Depends(require_api_key)],
)


def get_compliance_agent() -> ComplianceAgent:
    """Default agent uses a null retriever, so unevidenced rules abstain."""
    return ComplianceAgent()


@router.post("/check", response_model=ComplianceCheckResponse)
def check_compliance(
    payload: ComplianceCheckRequest,
    agent: Annotated[ComplianceAgent, Depends(get_compliance_agent)],
) -> ComplianceCheckResponse:
    """Run the compliance rule pack for one case snapshot."""
    state = SharedCaseState(
        case_id=payload.case_id,
        subject_property=payload.subject,
        loan_data=payload.loan_data,
        market_facts=payload.market_facts,
        model_output=payload.valuation,
        market_indicators=payload.market_indicators,
        status="valued" if payload.valuation is not None else "intake_done",
    )
    updated = agent.evaluate(state)

    return ComplianceCheckResponse(
        case_id=updated.case_id,
        status=updated.status,
        rule_set_version=agent.engine.config.rule_set_version,
        findings=[
            ComplianceOutput.model_validate(finding)
            for finding in updated.compliance
        ],
        evidence=[
            EvidenceItem.model_validate(item) for item in updated.evidence
        ],
        missing_information=updated.missing_information,
        human_review_required=updated.human_review_required,
    )
