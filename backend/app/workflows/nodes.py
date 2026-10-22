
"""LangGraph node execution functions for mortgage underwriting."""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.calculations.cltv import calculate_cltv
from app.agents.credit_agent import CreditAgent
from app.calculations.dscr import calculate_dscr
from app.calculations.dti import calculate_dti
from app.calculations.ltv import calculate_ltv
from app.calculations.risk_score import compute_composite_risk_score
from app.workflows.state import UnderwritingState
from app.agents.decision_agent import DecisionAgent
from app.calculations.fico import determine_qualifying_fico


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a numeric input to Decimal and reject invalid values."""

    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a valid number.")

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.") from None

    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return number


async def document_ingestion_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Placeholder for document ingestion and classification."""
    return {}


async def financial_calculation_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Calculate financial ratios and borrower credit risk."""

    data = state.get("extracted_data")

    if not isinstance(data, dict):
        return {
            "human_review_required": True,
            "financial_calculation_status": "invalid",
            "financial_calculation_warnings": [
                "Extracted application data is missing or invalid."
            ],
        }

    required_fields = [
        "gross_monthly_income",
        "total_monthly_debt",
        "loan_amount",
        "property_value",
        "primary_loan",
        "additional_secured_loans",
        "net_operating_income",
        "annual_debt_service",
        "reserves_months",
    ]

    missing = [
        field for field in required_fields
        if field not in data or data[field] is None
    ]

    if missing:
        return {
            "human_review_required": True,
            "financial_calculation_status": "incomplete",
            "financial_calculation_warnings": [
                f"Missing required financial data: {', '.join(missing)}."
            ],
        }
    has_single_fico = (
        "fico_score" in data and data["fico_score"] is not None
    )
    has_multiple_fico = (
        "fico_scores" in data and data["fico_scores"] is not None
    )

    if not has_single_fico and not has_multiple_fico:
        return {
            "human_review_required": True,
            "financial_calculation_status": "incomplete",
            "financial_calculation_warnings": [
                "Missing FICO data: provide fico_score or fico_scores."
            ],
        }

    try:
        # Convert monetary and ratio inputs before calculations.
        gross_income = _to_decimal(
            data["gross_monthly_income"], "gross_monthly_income"
        )
        monthly_debt = _to_decimal(
            data["total_monthly_debt"], "total_monthly_debt"
        )
        loan_amount = _to_decimal(data["loan_amount"], "loan_amount")
        property_value = _to_decimal(
            data["property_value"], "property_value"
        )
        primary_loan = _to_decimal(data["primary_loan"], "primary_loan")
        additional_loans = _to_decimal(
            data["additional_secured_loans"],
            "additional_secured_loans",
        )
        noi = _to_decimal(
            data["net_operating_income"], "net_operating_income"
        )
        annual_debt_service = _to_decimal(
            data["annual_debt_service"], "annual_debt_service"
        )

        if has_multiple_fico:
            fico_score = determine_qualifying_fico(data["fico_scores"])
        else:
            fico_score = data["fico_score"]

            if isinstance(fico_score, bool) or not isinstance(
                fico_score, int
            ):
                raise ValueError("fico_score must be an integer.")

        reserves = data["reserves_months"]
        if isinstance(reserves, bool) or not isinstance(
            reserves, (int, float)
        ):
            raise ValueError("reserves_months must be numeric.")

        dti_result = calculate_dti(gross_income, monthly_debt)

        # DTI reports invalid input in its result rather than raising.
        if dti_result["status"] != "calculated":
            raise ValueError("; ".join(dti_result["warnings"]))

        ltv_result = calculate_ltv(loan_amount, property_value)
        cltv_result = calculate_cltv(
            primary_loan, additional_loans, property_value
        )
        dscr_result = calculate_dscr(noi, annual_debt_service)
        credit_agent_result = CreditAgent().analyze(fico_score)

        if (
            not isinstance(credit_agent_result, dict)
            or credit_agent_result.get("status") != "completed"
            or not isinstance(credit_agent_result.get("credit_analysis"), dict)
            ):
                raise ValueError("CreditAgent returned an invalid result.")

        credit_result = credit_agent_result["credit_analysis"]
        # The risk engine accepts int/float, not Decimal.
        risk_score = compute_composite_risk_score(
            dti=float(dti_result["dti_percentage"]),
            ltv=float(ltv_result["ltv"]),
            fico=fico_score,
            reserves_months=reserves,
        )

        calculations = {
            "dti": dti_result,
            "ltv": ltv_result,
            "cltv": cltv_result,
            "dscr": dscr_result,
            "credit_analysis": credit_result,
            "risk_score": risk_score,
        }

        warnings = []
        for result in (
            dti_result, ltv_result, cltv_result, dscr_result, credit_result
        ):
            warnings.extend(result.get("warnings", []))

        return {
            "calculations": calculations,
            "human_review_required": state.get("human_review_required") is True,
            "financial_calculation_status": "completed",
            "financial_calculation_warnings": warnings,
        }

    except (ValueError, TypeError, InvalidOperation) as exc:
        return {
            "human_review_required": True,
            "financial_calculation_status": "invalid",
            "financial_calculation_warnings": [
                f"Financial calculations could not be completed: {exc}"
            ],
        }



async def compliance_check_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Validate a compliance result and route unresolved cases to review."""

    assessment = state.get("compliance_assessment")

    # Without an assessment, compliance cannot be considered cleared.
    if not isinstance(assessment, dict):
        return {
            "compliance_status": "review",
            "compliance_clear": False,
            "compliance_flags": [
                {
                    "status": "unresolved",
                    "reason": "No compliance assessment was provided.",
                }
            ],
            "human_review_required": True,
        }

    status = assessment.get("status")
    clear = assessment.get("clear")
    flags = assessment.get("flags")

    # Validate the result contract before trusting its contents.
    if (
        status != "completed"
        or not isinstance(clear, bool)
        or not isinstance(flags, list)
    ):
        return {
            "compliance_status": "review",
            "compliance_clear": False,
            "compliance_flags": [
                {
                    "status": "unresolved",
                    "reason": "The compliance assessment is incomplete or invalid.",
                }
            ],
            "human_review_required": True,
        }

    # Any unresolved flag or uncleared result blocks automatic finalization.
    unresolved_flags = [
        flag for flag in flags
        if not isinstance(flag, dict) or flag.get("status") != "cleared"
    ]

    is_clear = clear and not unresolved_flags
    existing_review = state.get("human_review_required") is True

    return {
        "compliance_status": "completed",
        "compliance_clear": is_clear,
        "compliance_flags": flags,
        "human_review_required": existing_review or not is_clear,
    }



async def decision_synthesis_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Build an assessment and obtain a recommendation from DecisionAgent."""

    # Never make a final decision when calculations did not complete.
    if state.get("financial_calculation_status") != "completed":
        return {
            "human_review_required": True,
            "decision_recommendation": {
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": [
                    "Financial calculations are missing or incomplete."
                ],
            },
        }

    calculations = state.get("calculations")

    if not isinstance(calculations, dict):
        return {
            "human_review_required": True,
            "decision_recommendation": {
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": ["Financial calculation results are missing."],
            },
        }

    try:
        dti = calculations["dti"]["dti_percentage"]
        ltv = calculations["ltv"]["ltv"]
        cltv = calculations["cltv"]["cltv"]
        dscr = calculations["dscr"]["dscr"]
        credit = calculations["credit_analysis"]
        risk_score = calculations["risk_score"]

        # Map calculation outputs to the DecisionAgent's input contract.
        assessment = {
            "dti_percentage": float(dti),
            "ltv": float(ltv),
            "cltv": float(cltv),
            "dscr": float(dscr),
            "fico_score": credit["fico_score"],
            "risk_score": risk_score,
            "documents_complete": state.get("documents_complete"),
            "compliance_clear": state.get("compliance_clear"),
            "data_conflicts": state.get("data_conflicts"),
            "confidence": state.get("confidence"),
            "policy_outcome": state.get("policy_outcome"),
        }

        decision = DecisionAgent().evaluate(assessment)

    except (KeyError, TypeError, ValueError) as exc:
        return {
            "human_review_required": True,
            "decision_recommendation": {
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": [
                    f"Decision assessment could not be completed: {exc}"
                ],
            },
        }

    # Preserve a review requirement raised by any earlier workflow node.
    existing_review = state.get("human_review_required") is True
    requires_review = (
        existing_review
        or decision["requires_human_review"] is True
    )

    # An existing review requirement overrides an automatic recommendation.
    recommendation = decision["recommendation"]
    reasons = list(decision["reasons"])

    if existing_review:
        recommendation = "SUSPEND"
        reasons.append(
            "An earlier workflow stage requires human review."
        )

    return {
        "human_review_required": requires_review,
        "decision_recommendation": {
            "recommendation": recommendation,
            "requires_human_review": requires_review,
            "reasons": reasons,
        },
    }




async def human_review_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Mark the case as requiring human review."""

    existing_warnings = state.get("financial_calculation_warnings", [])

    return {
        "human_review_required": True,
        "decision_recommendation": {
            "recommendation": "SUSPEND",
            "requires_human_review": True,
            "reasons": (
                existing_warnings
                or ["The case requires human review before a final decision."]
            ),
        },
    }


async def finalize_decision_node(
    state: UnderwritingState,
) -> dict[str, Any]:
    """Validate the recommendation before finalization."""

    recommendation = state.get("decision_recommendation")

    if (
        state.get("human_review_required") is not False
        or not isinstance(recommendation, dict)
        or recommendation.get("recommendation") not in {"APPROVE", "DENY"}
        or recommendation.get("requires_human_review") is not False
    ):
        return {
            "human_review_required": True,
            "decision_recommendation": {
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": [
                    "Finalization requirements were not satisfied."
                ],
            },
        }

    return {
        "human_review_required": state.get("human_review_required") is True,
        "decision_recommendation": recommendation,
    }
