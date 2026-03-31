"""Common ReAct worker infrastructure — factory, callback logger, and helpers."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 8


# ── Worker State ──────────────────────────────────────────────────────


class WorkerState(dict):
    """State for ReAct worker subgraphs.

    Minimal messages-based schema compatible with ``create_react_agent``.
    """

    messages: Annotated[list[BaseMessage], add_messages]


# ── Worker Factory ────────────────────────────────────────────────────


def make_react_worker(
    name: str,
    llm,
    tools: list,
    system_prompt: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> CompiledStateGraph:
    """Create a compiled ReAct agent subgraph.

    Parameters
    ----------
    name:
        Worker identifier (e.g., ``"scoring_worker"``). Used for logging.
    llm:
        LLM instance (from ``get_llm()``). Must support tool calling.
    tools:
        List of ``@tool``-decorated functions for this worker.
    system_prompt:
        Rendered system prompt including domain instructions and output format.
    max_iterations:
        Safety limit. Not directly used here — passed at ``invoke_worker`` time
        via ``recursion_limit``.

    Returns
    -------
    CompiledStateGraph
        A compiled LangGraph that accepts ``WorkerState`` and returns ``WorkerState``.
    """
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name=name,
    )


# ── Worker Invocation ─────────────────────────────────────────────────


def extract_worker_result(worker_output: dict) -> str:
    """Extract the final text content from a ReAct worker's output.

    The last message in the worker's message list is the final AI response
    containing the structured analysis result.
    """
    messages = worker_output.get("messages", [])
    if not messages:
        return ""
    last_msg = messages[-1]
    return last_msg.content if hasattr(last_msg, "content") else str(last_msg)


async def invoke_worker(
    worker: CompiledStateGraph,
    user_prompt: str,
    *,
    deal_id: uuid.UUID,
    worker_name: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> str:
    """Invoke a ReAct worker with logging and safety limits.

    Returns the final text content from the worker.
    """
    callback = WorkerLogCallback(deal_id=deal_id, worker_name=worker_name)

    result = await worker.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={
            "recursion_limit": 2 * max_iterations + 1,
            "callbacks": [callback],
        },
    )

    return extract_worker_result(result)


# ── Logging Callback ──────────────────────────────────────────────────


class WorkerLogCallback(AsyncCallbackHandler):
    """Logs each ReAct step (reasoning, tool_call) to AgentLog.

    Instantiated per worker invocation with ``deal_id`` and ``worker_name``.
    Uses an independent DB session per log write for concurrency safety.
    """

    def __init__(
        self,
        deal_id: uuid.UUID,
        worker_name: str,
    ) -> None:
        super().__init__()
        self.deal_id = deal_id
        self.worker_name = worker_name
        self._step_index = 0
        self._current_start: datetime | None = None
        self._tool_start: datetime | None = None
        self._current_tool_name: str = "unknown"

    async def on_llm_start(self, serialized, prompts, **kwargs):
        """Record that a reasoning step started."""
        self._current_start = datetime.now(UTC)

    async def on_llm_end(self, response, **kwargs):
        """Log the reasoning step (LLM response)."""
        completed_at = datetime.now(UTC)
        started_at = self._current_start or completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        generation = response.generations[0][0] if response.generations else None
        raw_output = generation.text if generation else ""

        await self._persist_log(
            step_type="reasoning",
            raw_output=raw_output,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        self._step_index += 1

    async def on_tool_start(self, serialized, input_str, **kwargs):
        """Record tool invocation start."""
        self._tool_start = datetime.now(UTC)
        self._current_tool_name = serialized.get("name", "unknown")

    async def on_tool_end(self, output, **kwargs):
        """Log the tool call and its result."""
        completed_at = datetime.now(UTC)
        started_at = self._tool_start or completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        await self._persist_log(
            step_type="tool_call",
            tool_name=self._current_tool_name,
            raw_output=str(output)[:5000],
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        self._step_index += 1

    async def on_tool_error(self, error, **kwargs):
        """Log tool execution failure."""
        completed_at = datetime.now(UTC)
        started_at = self._tool_start or completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        await self._persist_log(
            step_type="tool_call",
            tool_name=self._current_tool_name,
            error=str(error),
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        self._step_index += 1

    async def _persist_log(
        self,
        step_type: str,
        raw_output: str | None = None,
        error: str | None = None,
        tool_name: str | None = None,
        duration_ms: int = 0,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Write a single AgentLog row using an independent session."""
        from backend.app.db.repositories import agent_log_repo
        from backend.app.db.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                await agent_log_repo.create(
                    session,
                    deal_id=self.deal_id,
                    node_name=f"{self.worker_name}:{step_type}",
                    raw_output=raw_output,
                    error=error,
                    duration_ms=duration_ms,
                    started_at=started_at or datetime.now(UTC),
                    completed_at=completed_at,
                )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist worker log step for %s (step_type=%s)",
                self.worker_name,
                step_type,
            )
