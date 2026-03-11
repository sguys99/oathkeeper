"""LangGraph StateGraph — deal-analysis orchestrator.

Graph topology::

    deal_structuring
          ↓
    [should_continue_or_hold]
          ├── hold → hold_verdict_node → END
          └── continue → scoring, resource_estimation,
                         risk_analysis, similar_project  (parallel)
                                ↓  (all complete)
                         final_verdict → END
"""

import logging

from langgraph.graph import END, StateGraph
from langgraph.types import Send
from sqlalchemy.ext.asyncio import AsyncSession

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


# ── Static nodes ────────────────────────────────────────────────────────


def hold_verdict_node(state: AgentState) -> dict:
    """Short-circuit when too many critical fields are missing."""
    missing = state.get("structured_deal", {}).get("missing_fields", [])
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
    """Conditional edge: hold if too many missing fields, else fan-out."""
    structured = state.get("structured_deal", {})
    missing = structured.get("missing_fields", [])

    if not structured or len(missing) >= MISSING_FIELDS_THRESHOLD:
        return [Send("hold_verdict", state)]

    return [
        Send("scoring", state),
        Send("resource_estimation", state),
        Send("risk_analysis", state),
        Send("similar_project", state),
    ]


# ── Graph builder ───────────────────────────────────────────────────────


def build_graph(db: AsyncSession):
    """Construct and compile the analysis LangGraph.

    Parameters
    ----------
    db:
        An async database session shared by nodes that need DB access.

    Returns
    -------
    CompiledGraph
        Ready to ``await graph.ainvoke({"deal_input": ...})``.
    """
    context_store = CompanyContextStore()
    project_store = ProjectHistoryStore()

    graph = StateGraph(AgentState)

    # ── Register nodes ──────────────────────────────────────────────
    graph.add_node("deal_structuring", make_deal_structuring_node(db, context_store))
    graph.add_node("scoring", make_scoring_node(db, context_store))
    graph.add_node("resource_estimation", make_resource_estimation_node(db, project_store))
    graph.add_node("risk_analysis", make_risk_analysis_node(context_store))
    graph.add_node("similar_project", make_similar_project_node(project_store))
    graph.add_node("final_verdict", make_final_verdict_node())
    graph.add_node("hold_verdict", hold_verdict_node)

    # ── Edges ───────────────────────────────────────────────────────
    graph.set_entry_point("deal_structuring")

    # Conditional fan-out via Send
    graph.add_conditional_edges("deal_structuring", _route_after_structuring)

    # Fan-in: all 4 parallel nodes converge to final_verdict
    graph.add_edge("scoring", "final_verdict")
    graph.add_edge("resource_estimation", "final_verdict")
    graph.add_edge("risk_analysis", "final_verdict")
    graph.add_edge("similar_project", "final_verdict")

    # Terminal edges
    graph.add_edge("final_verdict", END)
    graph.add_edge("hold_verdict", END)

    return graph.compile()
