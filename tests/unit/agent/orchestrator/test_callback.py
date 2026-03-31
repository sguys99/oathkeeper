"""Tests for OrchestratorLogCallback."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.log_types import StepType
from backend.app.agent.orchestrator.callback import OrchestratorLogCallback

pytestmark = pytest.mark.unit


def _mock_db_context():
    """Return patched AsyncSessionLocal and agent_log_repo.create."""
    mock_sl = patch("backend.app.db.session.AsyncSessionLocal")
    mock_create = patch(
        "backend.app.db.repositories.agent_log_repo.create",
        new_callable=AsyncMock,
    )
    mock_update = patch(
        "backend.app.db.repositories.agent_log_repo.update_log",
        new_callable=AsyncMock,
    )
    return mock_sl, mock_create, mock_update


class TestOrchestratorLogCallback:
    @pytest.mark.asyncio
    async def test_on_llm_end_creates_orchestrator_reasoning_log(self):
        deal_id = uuid.uuid4()
        callback = OrchestratorLogCallback(deal_id=deal_id)

        await callback.on_llm_start({}, ["test"])

        mock_response = MagicMock()
        mock_gen = MagicMock()
        mock_gen.text = "I'll start with deal structuring"
        mock_response.generations = [[mock_gen]]

        mock_log = MagicMock()
        mock_log.id = uuid.uuid4()

        with (
            patch("backend.app.db.session.AsyncSessionLocal") as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
                return_value=mock_log,
            ) as mock_create,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_llm_end(mock_response)

            mock_create.assert_called_once()
            kw = mock_create.call_args.kwargs
            assert kw["deal_id"] == deal_id
            assert kw["node_name"] == "orchestrator"
            assert kw["step_type"] == StepType.ORCHESTRATOR_REASONING
            assert kw["raw_output"] == "I'll start with deal structuring"

    @pytest.mark.asyncio
    async def test_on_tool_start_creates_log_and_sets_last_id(self):
        deal_id = uuid.uuid4()
        callback = OrchestratorLogCallback(deal_id=deal_id)
        log_id = uuid.uuid4()

        mock_log = MagicMock()
        mock_log.id = log_id

        with (
            patch("backend.app.db.session.AsyncSessionLocal") as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
                return_value=mock_log,
            ) as mock_create,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_tool_start({"name": "run_scoring_analysis"}, '{"deal_id": "abc"}')

            assert callback.last_tool_call_log_id == log_id
            kw = mock_create.call_args.kwargs
            assert kw["step_type"] == StepType.ORCHESTRATOR_TOOL_CALL
            assert kw["tool_name"] == "run_scoring_analysis"

    @pytest.mark.asyncio
    async def test_on_tool_end_updates_existing_log(self):
        deal_id = uuid.uuid4()
        callback = OrchestratorLogCallback(deal_id=deal_id)
        log_id = uuid.uuid4()
        callback._last_tool_call_log_id = log_id
        callback._tool_start = MagicMock()

        with (
            patch("backend.app.db.session.AsyncSessionLocal") as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.update_log",
                new_callable=AsyncMock,
            ) as mock_update,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_tool_end("Scoring complete. Total: 72.5")

            mock_update.assert_called_once()
            kw = mock_update.call_args.kwargs
            assert kw["raw_output"] == "Scoring complete. Total: 72.5"

    def test_initial_last_tool_call_log_id_is_none(self):
        callback = OrchestratorLogCallback(deal_id=uuid.uuid4())
        assert callback.last_tool_call_log_id is None

    @pytest.mark.asyncio
    async def test_step_index_increments(self):
        deal_id = uuid.uuid4()
        callback = OrchestratorLogCallback(deal_id=deal_id)
        assert callback._step_index == 0

        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="test")]]
        mock_log = MagicMock()
        mock_log.id = uuid.uuid4()

        with (
            patch("backend.app.db.session.AsyncSessionLocal") as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
                return_value=mock_log,
            ),
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_llm_start({}, ["test"])
            await callback.on_llm_end(mock_response)
            assert callback._step_index == 1

    @pytest.mark.asyncio
    async def test_db_error_handled_gracefully(self):
        callback = OrchestratorLogCallback(deal_id=uuid.uuid4())

        with patch(
            "backend.app.db.session.AsyncSessionLocal",
            side_effect=RuntimeError("DB down"),
        ):
            # Should not raise
            result = await callback._create_log(
                step_type=StepType.ORCHESTRATOR_REASONING,
                raw_output="test",
            )
            assert result is None
