"""Tests for base_worker module — factory, invocation, callback, and result extraction."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from backend.app.agent.workers.base_worker import (
    DEFAULT_MAX_ITERATIONS,
    WorkerLogCallback,
    extract_worker_result,
    invoke_worker,
    make_react_worker,
)

pytestmark = pytest.mark.unit


# ── extract_worker_result ─────────────────────────────────────────────


class TestExtractWorkerResult:
    def test_extracts_last_message_content(self):
        output = {
            "messages": [
                HumanMessage(content="analyze this"),
                AIMessage(content='{"scores": []}'),
            ],
        }
        assert extract_worker_result(output) == '{"scores": []}'

    def test_empty_messages_returns_empty_string(self):
        assert extract_worker_result({"messages": []}) == ""

    def test_missing_messages_key_returns_empty_string(self):
        assert extract_worker_result({}) == ""

    def test_multiple_messages_returns_last(self):
        output = {
            "messages": [
                HumanMessage(content="first"),
                AIMessage(content="middle"),
                AIMessage(content="final answer"),
            ],
        }
        assert extract_worker_result(output) == "final answer"


# ── make_react_worker ─────────────────────────────────────────────────


class TestMakeReactWorker:
    @patch("backend.app.agent.workers.base_worker.create_react_agent")
    def test_returns_compiled_graph(self, mock_create):
        mock_graph = MagicMock()
        mock_create.return_value = mock_graph
        mock_llm = MagicMock()
        tools = [MagicMock()]

        result = make_react_worker(
            name="test_worker",
            llm=mock_llm,
            tools=tools,
            system_prompt="You are a test worker.",
        )

        assert result is mock_graph
        mock_create.assert_called_once_with(
            model=mock_llm,
            tools=tools,
            prompt="You are a test worker.",
            name="test_worker",
        )


# ── invoke_worker ─────────────────────────────────────────────────────


class TestInvokeWorker:
    @pytest.mark.asyncio
    async def test_passes_recursion_limit_and_callback(self):
        mock_worker = AsyncMock()
        mock_worker.ainvoke.return_value = {
            "messages": [AIMessage(content="result")],
        }

        result = await invoke_worker(
            mock_worker,
            "analyze this deal",
            deal_id=uuid.uuid4(),
            worker_name="test_worker",
            max_iterations=5,
        )

        assert result == "result"
        call_args = mock_worker.ainvoke.call_args
        config = call_args.kwargs.get("config")
        assert config["recursion_limit"] == 2 * 5 + 1
        assert len(config["callbacks"]) == 1
        assert isinstance(config["callbacks"][0], WorkerLogCallback)

    @pytest.mark.asyncio
    async def test_uses_default_max_iterations(self):
        mock_worker = AsyncMock()
        mock_worker.ainvoke.return_value = {"messages": [AIMessage(content="ok")]}

        await invoke_worker(
            mock_worker,
            "test",
            deal_id=uuid.uuid4(),
            worker_name="test",
        )

        call_args = mock_worker.ainvoke.call_args
        config = call_args.kwargs.get("config") or call_args[0][1]
        assert config["recursion_limit"] == 2 * DEFAULT_MAX_ITERATIONS + 1

    @pytest.mark.asyncio
    async def test_sends_human_message(self):
        mock_worker = AsyncMock()
        mock_worker.ainvoke.return_value = {"messages": [AIMessage(content="ok")]}

        await invoke_worker(
            mock_worker,
            "my prompt",
            deal_id=uuid.uuid4(),
            worker_name="test",
        )

        input_state = mock_worker.ainvoke.call_args[0][0]
        assert len(input_state["messages"]) == 1
        assert isinstance(input_state["messages"][0], HumanMessage)
        assert input_state["messages"][0].content == "my prompt"


# ── WorkerLogCallback ─────────────────────────────────────────────────


class TestWorkerLogCallback:
    @pytest.mark.asyncio
    async def test_on_llm_end_creates_reasoning_log(self):
        deal_id = uuid.uuid4()
        callback = WorkerLogCallback(deal_id=deal_id, worker_name="scoring")

        await callback.on_llm_start({}, ["test prompt"])

        mock_response = MagicMock()
        mock_generation = MagicMock()
        mock_generation.text = "I should call the scoring tool"
        mock_response.generations = [[mock_generation]]

        with (
            patch(
                "backend.app.db.session.AsyncSessionLocal",
            ) as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_llm_end(mock_response)

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["deal_id"] == deal_id
            assert call_kwargs["node_name"] == "scoring:reasoning"
            assert call_kwargs["raw_output"] == "I should call the scoring tool"
            assert call_kwargs["error"] is None

    @pytest.mark.asyncio
    async def test_on_tool_end_creates_tool_call_log(self):
        deal_id = uuid.uuid4()
        callback = WorkerLogCallback(deal_id=deal_id, worker_name="scoring")

        await callback.on_tool_start({"name": "calculate_weighted_score"}, '{"score": 72.5}')

        with (
            patch(
                "backend.app.db.session.AsyncSessionLocal",
            ) as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_tool_end('{"total": 72.5}')

            assert mock_create.await_count == 2

            tool_call_kwargs = mock_create.await_args_list[0].kwargs
            assert tool_call_kwargs["node_name"] == "scoring:tool_call"
            assert tool_call_kwargs["user_prompt"] == '{"score": 72.5}'
            assert tool_call_kwargs["raw_output"] is None

            observation_kwargs = mock_create.await_args_list[1].kwargs
            assert observation_kwargs["node_name"] == "scoring:observation"
            assert '{"total": 72.5}' in observation_kwargs["raw_output"]

    @pytest.mark.asyncio
    async def test_on_tool_error_logs_error(self):
        deal_id = uuid.uuid4()
        callback = WorkerLogCallback(deal_id=deal_id, worker_name="risk_analysis")

        await callback.on_tool_start({"name": "web_search"}, "query")

        with (
            patch(
                "backend.app.db.session.AsyncSessionLocal",
            ) as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_tool_error(RuntimeError("API timeout"))

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["node_name"] == "risk_analysis:tool_call"
            assert "API timeout" in call_kwargs["error"]

    def test_step_index_increments(self):
        callback = WorkerLogCallback(deal_id=uuid.uuid4(), worker_name="test")
        assert callback._step_index == 0

    @pytest.mark.asyncio
    async def test_observation_step_advances_index(self):
        deal_id = uuid.uuid4()
        callback = WorkerLogCallback(deal_id=deal_id, worker_name="scoring")

        await callback.on_tool_start({"name": "calculate_weighted_score"}, "{}")

        with (
            patch("backend.app.db.session.AsyncSessionLocal") as mock_sl,
            patch(
                "backend.app.db.repositories.agent_log_repo.create",
                new_callable=AsyncMock,
            ),
        ):
            mock_session = AsyncMock()
            mock_sl.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sl.return_value.__aexit__ = AsyncMock(return_value=False)

            await callback.on_tool_end('{"total": 72.5}')

        assert callback._step_index == 2

    @pytest.mark.asyncio
    async def test_persist_log_handles_db_error_gracefully(self):
        callback = WorkerLogCallback(deal_id=uuid.uuid4(), worker_name="test")
        callback._current_start = datetime.now(UTC)

        with patch(
            "backend.app.db.session.AsyncSessionLocal",
            side_effect=RuntimeError("DB down"),
        ):
            # Should not raise
            await callback._persist_log(step_type="reasoning", raw_output="test")
