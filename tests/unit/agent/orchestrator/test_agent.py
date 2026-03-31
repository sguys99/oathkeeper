"""Tests for orchestrator agent builder."""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.agent.orchestrator.agent import (
    ORCHESTRATOR_MAX_ITERATIONS,
    build_orchestrator,
)

pytestmark = pytest.mark.unit


class TestBuildOrchestrator:
    @patch("backend.app.agent.orchestrator.agent.create_react_agent")
    @patch("backend.app.agent.orchestrator.agent.get_llm_uncached")
    def test_returns_compiled_graph(self, mock_llm, mock_create):
        mock_llm.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        agent = build_orchestrator("deal-123")

        assert agent is not None
        mock_llm.assert_called_once_with(temperature=0.0, max_tokens=4096)
        mock_create.assert_called_once()

    @patch("backend.app.agent.orchestrator.agent.create_react_agent")
    @patch("backend.app.agent.orchestrator.agent.get_llm_uncached")
    def test_passes_meta_tools(self, mock_llm, mock_create):
        mock_llm.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        build_orchestrator("deal-456")

        call_kwargs = mock_create.call_args
        tools = call_kwargs.kwargs.get("tools") or call_kwargs[1].get("tools")
        assert len(tools) == 7

    @patch("backend.app.agent.orchestrator.agent.create_react_agent")
    @patch("backend.app.agent.orchestrator.agent.get_llm_uncached")
    def test_deal_id_in_prompt(self, mock_llm, mock_create):
        mock_llm.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        build_orchestrator("deal-789")

        call_kwargs = mock_create.call_args
        prompt = call_kwargs.kwargs.get("prompt") or call_kwargs[1].get("prompt")
        assert "deal-789" in prompt

    def test_max_iterations_constant(self):
        assert ORCHESTRATOR_MAX_ITERATIONS == 12
