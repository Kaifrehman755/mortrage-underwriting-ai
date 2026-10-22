
"""LangGraph workflow assembly for mortgage underwriting."""

from langgraph.graph import END, START, StateGraph

from app.workflows.edges import should_route_to_human_review
from app.workflows.nodes import (
    compliance_check_node,
    decision_synthesis_node,
    document_ingestion_node,
    finalize_decision_node,
    financial_calculation_node,
    human_review_node,
)
from app.workflows.state import UnderwritingState


def build_underwriting_graph():
    """Construct and compile the mortgage underwriting workflow."""

    # Create a graph that uses UnderwritingState as shared state.
    workflow = StateGraph(UnderwritingState)

    # Register each processing stage as a node.
    workflow.add_node("document_ingestion", document_ingestion_node)
    workflow.add_node("financial_calculation", financial_calculation_node)
    workflow.add_node("compliance_check", compliance_check_node)
    workflow.add_node("decision_synthesis", decision_synthesis_node)

    # Register the two possible terminal paths.
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("finalize_decision", finalize_decision_node)

    # Define the normal processing sequence.
    workflow.add_edge(START, "document_ingestion")
    workflow.add_edge("document_ingestion", "financial_calculation")
    workflow.add_edge("financial_calculation", "compliance_check")
    workflow.add_edge("compliance_check", "decision_synthesis")

    # Choose the next node based on the review flag.
    workflow.add_conditional_edges(
        "decision_synthesis",
        should_route_to_human_review,
        {
            "human_review": "human_review",
            "finalize_decision": "finalize_decision",
        },
    )

    # Both paths terminate after their respective node runs.
    workflow.add_edge("human_review", END)
    workflow.add_edge("finalize_decision", END)

    # Compile the graph so it can be invoked.
    return workflow.compile()
