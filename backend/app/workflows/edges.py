
"""Conditional edge routing for mortgage underwriting workflows."""

from typing import Literal

from app.workflows.state import UnderwritingState


def should_route_to_human_review(
    state: UnderwritingState,
) -> Literal["human_review", "finalize_decision"]:
    """Route uncertain or incomplete cases to human review."""

    if state.get("human_review_required") is False:
        return "finalize_decision"

    return "human_review"
