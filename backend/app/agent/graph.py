"""LangGraph orchestrator — deal-analysis coordinator.

Phase 3: ReAct orchestrator agent that dynamically invokes analysis workers
via meta-tools. Replaces the static two-phase fan-out graph.
"""

import logging

from backend.app.agent.orchestrator.agent import build_orchestrator
from backend.app.agent.tools import init_tool_context
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

logger = logging.getLogger(__name__)


def build_graph(deal_id: str):
    """Construct and compile the orchestrator agent.

    Parameters
    ----------
    deal_id : str
        The deal UUID. Passed to the orchestrator for tool invocations.

    Returns
    -------
    CompiledStateGraph
        Ready to ``await graph.ainvoke({"messages": [...]})``.
    """
    context_store = CompanyContextStore()
    project_store = ProjectHistoryStore()

    init_tool_context(
        session_factory=AsyncSessionLocal,
        company_context_store=context_store,
        project_history_store=project_store,
    )

    return build_orchestrator(deal_id=deal_id)
