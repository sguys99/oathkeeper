"""LangGraph StateGraph — deal-analysis orchestrator.

Graph topology::

    deal_structuring
          ↓
    [should_continue_or_hold]
          ├── hold → hold_verdict_node → END
          └── continue:
                Phase 1 [parallel]: resource_estimation, similar_project
                         ↓
                   phase1_sync  (no-op sync point)
                         ↓
                Phase 2 [parallel]: scoring, risk_analysis
                         ↓  (all complete)
                   final_verdict → END

Phase 2 nodes receive Phase 1 results (resource_estimate, similar_projects)
so that scoring can incorporate actual cost/margin data for accurate evaluation.
"""

import logging

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from backend.app.agent.base import MISSING_FIELDS_THRESHOLD
from backend.app.agent.nodes import (
    make_deal_structuring_node,
    make_final_verdict_node,
    make_resource_estimation_node,
    make_risk_analysis_node,
    make_scoring_node,
    make_similar_project_node,
)
from backend.app.agent.state import AgentState
from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

logger = logging.getLogger(__name__)


# ── Constants ──────────────────────────────────────────────────────────

_CRITICAL_FIELDS = {
    "customer_name",
    "customer_industry",
    "project_overview",
    "tech_requirements",
    "expected_amount",
    "duration_months",
}


# ── Static nodes ────────────────────────────────────────────────────────


def phase1_sync(state: AgentState) -> dict:
    """No-op synchronization node — Phase 1 results are now in state."""
    return {}


def hold_verdict_node(state: AgentState) -> dict:
    """Short-circuit when too many critical fields are missing."""
    raw_missing = state.get("structured_deal", {}).get("missing_fields", [])
    missing = [f for f in raw_missing if f in _CRITICAL_FIELDS]
    return {
        "verdict": "pending",
        "total_score": 0.0,
        "scores": [],
        "resource_estimate": {},
        "risks": [],
        "similar_projects": [],
        "final_report": (
            "# 분석 보류\n\n"
            f"필수 항목이 충분하지 않아 분석을 보류합니다.\n\n"
            f"**미입력 항목:** {', '.join(missing) if missing else '(없음)'}"
        ),
        "status": "completed",
    }


# ── Routing ─────────────────────────────────────────────────────────────


def _route_after_structuring(state: AgentState) -> list[Send]:
    """Conditional edge: hold if too many missing fields, else fan-out to Phase 1."""
    structured = state.get("structured_deal", {})
    missing = structured.get("missing_fields", [])
    # Filter to critical fields only — LLM may include non-critical fields
    missing = [f for f in missing if f in _CRITICAL_FIELDS]

    if not structured or len(missing) >= MISSING_FIELDS_THRESHOLD:
        return [Send("hold_verdict", state)]

    # Phase 1: resource_estimation and similar_project run first
    return [
        Send("resource_estimation", state),
        Send("similar_project", state),
    ]


def _route_to_phase2(state: AgentState) -> list[Send]:
    """Fan-out to Phase 2 nodes (scoring, risk_analysis) with Phase 1 results in state."""
    return [
        Send("scoring", state),
        Send("risk_analysis", state),
    ]


# ── Graph builder ───────────────────────────────────────────────────────


def build_graph():
    """Construct and compile the analysis LangGraph.

    Returns
    -------
    CompiledGraph
        Ready to ``await graph.ainvoke({"deal_input": ...})``.
    """
    context_store = CompanyContextStore()
    project_store = ProjectHistoryStore()

    graph = StateGraph(AgentState)

    # ── Register nodes ──────────────────────────────────────────────
    graph.add_node("deal_structuring", make_deal_structuring_node(context_store))
    graph.add_node("resource_estimation", make_resource_estimation_node(project_store, context_store))
    graph.add_node("similar_project", make_similar_project_node(project_store, context_store))
    graph.add_node("phase1_sync", phase1_sync)
    graph.add_node("scoring", make_scoring_node(context_store))
    graph.add_node("risk_analysis", make_risk_analysis_node(context_store))
    graph.add_node("final_verdict", make_final_verdict_node(context_store))
    graph.add_node("hold_verdict", hold_verdict_node)

    # ── Edges ───────────────────────────────────────────────────────
    graph.set_entry_point("deal_structuring")

    # Phase 1: conditional fan-out to resource_estimation + similar_project
    graph.add_conditional_edges("deal_structuring", _route_after_structuring)

    # Phase 1 → sync point
    graph.add_edge("resource_estimation", "phase1_sync")
    graph.add_edge("similar_project", "phase1_sync")

    # Phase 2: fan-out to scoring + risk_analysis (with Phase 1 results in state)
    graph.add_conditional_edges("phase1_sync", _route_to_phase2)

    # Phase 2 → final_verdict
    graph.add_edge("scoring", "final_verdict")
    graph.add_edge("risk_analysis", "final_verdict")

    # Terminal edges
    graph.add_edge("final_verdict", END)
    graph.add_edge("hold_verdict", END)

    return graph.compile()
