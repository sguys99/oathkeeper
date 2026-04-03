"""Orchestrator logging callback — logs orchestrator ReAct steps to AgentLog."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from langchain_core.callbacks import AsyncCallbackHandler

from backend.app.agent.log_types import StepType

logger = logging.getLogger(__name__)


class OrchestratorLogCallback(AsyncCallbackHandler):
    """Logs orchestrator reasoning and meta-tool calls to AgentLog.

    Key design: ``on_tool_start`` creates the log and sets
    ``last_tool_call_log_id`` *before* the meta-tool function runs,
    so the meta-tool can read it and pass it as ``parent_log_id``
    to ``invoke_worker()``.  ``on_tool_end`` then updates that log
    with the result and duration.
    """

    def __init__(self, deal_id: uuid.UUID) -> None:
        super().__init__()
        self.deal_id = deal_id
        self._step_index = 0
        self._current_start: datetime | None = None

        # Per-tool-call tracking for parallel safety
        self._tool_call_log_ids: dict[uuid.UUID, uuid.UUID] = {}  # run_id → log_id
        self._tool_call_log_ids_by_name: dict[str, uuid.UUID] = {}  # tool_name → log_id
        self._tool_starts: dict[uuid.UUID, datetime] = {}  # run_id → start time
        self._last_tool_call_log_id: uuid.UUID | None = None  # backward compat

    @property
    def last_tool_call_log_id(self) -> uuid.UUID | None:
        """The log ID of the most recent orchestrator tool call.

        Meta-tools read this to set ``parent_log_id`` on worker callbacks.
        """
        return self._last_tool_call_log_id

    def get_tool_call_log_id(self, tool_name: str) -> uuid.UUID | None:
        """Get the log_id for a specific tool call by name.

        Parallel-safe: each tool name maps to its own log entry.
        """
        return self._tool_call_log_ids_by_name.get(tool_name)

    # ── LLM reasoning ────────────────────────────────────────────────

    async def on_llm_start(self, serialized, prompts, **kwargs):
        self._current_start = datetime.now(UTC)

    async def on_llm_end(self, response, **kwargs):
        completed_at = datetime.now(UTC)
        started_at = self._current_start or completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        generation = response.generations[0][0] if response.generations else None
        raw_output = generation.text if generation else ""

        await self._create_log(
            step_type=StepType.ORCHESTRATOR_REASONING,
            raw_output=raw_output,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        self._step_index += 1

    # ── Tool calls (meta-tools) ──────────────────────────────────────

    async def on_tool_start(self, serialized, input_str, **kwargs):
        """Create orchestrator_tool_call log and expose its ID.

        Uses ``run_id`` from kwargs to correlate with ``on_tool_end`` so that
        parallel tool calls each track their own log entry.
        """
        run_id: uuid.UUID | None = kwargs.get("run_id")
        started_at = datetime.now(UTC)
        tool_name = serialized.get("name", "unknown")

        log_id = await self._create_log(
            step_type=StepType.ORCHESTRATOR_TOOL_CALL,
            tool_name=tool_name,
            started_at=started_at,
        )

        # Track per run_id and per tool_name for parallel safety
        if run_id and log_id:
            self._tool_call_log_ids[run_id] = log_id
            self._tool_starts[run_id] = started_at
        if log_id:
            self._tool_call_log_ids_by_name[tool_name] = log_id
            self._last_tool_call_log_id = log_id

    async def on_tool_end(self, output, **kwargs):
        """Update the tool_call log created in on_tool_start."""
        run_id: uuid.UUID | None = kwargs.get("run_id")
        completed_at = datetime.now(UTC)

        log_id = self._tool_call_log_ids.get(run_id) if run_id else self._last_tool_call_log_id
        started_at = self._tool_starts.get(run_id, completed_at) if run_id else completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        if log_id:
            await self._update_log(
                log_id=log_id,
                raw_output=str(output)[:5000],
                duration_ms=duration_ms,
                completed_at=completed_at,
            )
        self._step_index += 1

    async def on_tool_error(self, error, **kwargs):
        """Update the tool_call log with error info."""
        run_id: uuid.UUID | None = kwargs.get("run_id")
        completed_at = datetime.now(UTC)

        log_id = self._tool_call_log_ids.get(run_id) if run_id else self._last_tool_call_log_id
        started_at = self._tool_starts.get(run_id, completed_at) if run_id else completed_at
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        if log_id:
            await self._update_log(
                log_id=log_id,
                error=str(error),
                duration_ms=duration_ms,
                completed_at=completed_at,
            )
        self._step_index += 1

    # ── Persistence helpers ──────────────────────────────────────────

    async def _create_log(
        self,
        step_type: str,
        raw_output: str | None = None,
        error: str | None = None,
        tool_name: str | None = None,
        duration_ms: int = 0,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> uuid.UUID | None:
        """Create an AgentLog row and return its ID."""
        from backend.app.db.repositories import agent_log_repo
        from backend.app.db.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                log = await agent_log_repo.create(
                    session,
                    deal_id=self.deal_id,
                    node_name="orchestrator",
                    raw_output=raw_output,
                    error=error,
                    duration_ms=duration_ms,
                    started_at=started_at or datetime.now(UTC),
                    completed_at=completed_at,
                    step_type=step_type,
                    step_index=self._step_index,
                    tool_name=tool_name,
                )
                await session.commit()
                return log.id
        except Exception:
            logger.exception("Failed to create orchestrator log (step_type=%s)", step_type)
            return None

    async def _update_log(
        self,
        log_id: uuid.UUID,
        raw_output: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Update an existing log entry."""
        from backend.app.db.repositories import agent_log_repo
        from backend.app.db.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                await agent_log_repo.update_log(
                    session,
                    log_id,
                    raw_output=raw_output,
                    error=error,
                    duration_ms=duration_ms,
                    completed_at=completed_at,
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to update orchestrator log %s", log_id)
