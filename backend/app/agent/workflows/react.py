"""React workflow — ReAct orchestrator with dynamic worker invocation."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from langchain_core.messages import HumanMessage

from backend.app.agent.orchestrator.agent import ORCHESTRATOR_MAX_ITERATIONS, build_orchestrator
from backend.app.agent.orchestrator.callback import OrchestratorLogCallback
from backend.app.agent.orchestrator.context import (
    cleanup_analysis_context,
    init_analysis_context,
)
from backend.app.agent.tools import init_tool_context
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

logger = logging.getLogger(__name__)


class ReactWorkflow:
    """Execute the ReAct orchestrator pipeline with worker subgraphs."""

    async def execute(
        self,
        deal_id: uuid.UUID,
        deal_input: str,
        on_progress: Callable[[str], Awaitable[None]],
    ) -> dict:
        deal_id_str = str(deal_id)

        # Initialize shared tool context
        context_store = CompanyContextStore()
        project_store = ProjectHistoryStore()
        init_tool_context(
            session_factory=AsyncSessionLocal,
            company_context_store=context_store,
            project_history_store=project_store,
        )

        # Initialize per-deal analysis context
        ctx = init_analysis_context(
            deal_id=deal_id_str,
            deal_input=deal_input,
            on_progress=on_progress,
        )

        # Create orchestrator callback for hierarchical logging
        orch_callback = OrchestratorLogCallback(deal_id=deal_id)
        ctx.orchestrator_callback = orch_callback

        # Build and invoke orchestrator graph
        logger.info("Building orchestrator for deal %s", deal_id)
        graph = build_orchestrator(deal_id=deal_id_str)

        user_message = (
            f"Analyze the following deal for a Go/No-Go decision.\n\n"
            f"Deal ID: {deal_id_str}\n\n"
            f"Deal Input:\n{deal_input}"
        )

        logger.info("Starting orchestrator execution for deal %s", deal_id)
        try:
            await graph.ainvoke(
                {"messages": [HumanMessage(content=user_message)]},
                config={
                    "recursion_limit": 2 * ORCHESTRATOR_MAX_ITERATIONS + 1,
                    "callbacks": [orch_callback],
                },
            )

            # Extract accumulated results from context
            result = cleanup_analysis_context(deal_id_str)
            if result is None:
                raise RuntimeError("AnalysisContext was not found after orchestrator completion")

            return result
        except Exception:
            # Ensure context is cleaned up even on failure
            cleanup_analysis_context(deal_id_str)
            raise
