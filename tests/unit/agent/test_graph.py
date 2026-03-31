"""Tests for orchestrator graph builder."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class TestBuildGraph:
    @patch("backend.app.agent.graph.build_orchestrator")
    @patch("backend.app.agent.graph.ProjectHistoryStore")
    @patch("backend.app.agent.graph.CompanyContextStore")
    @patch("backend.app.agent.graph.init_tool_context")
    def test_graph_compiles(self, mock_init, mock_ctx, mock_proj, mock_build_orch):
        from backend.app.agent.graph import build_graph

        mock_ctx.return_value = MagicMock()
        mock_proj.return_value = MagicMock()
        mock_build_orch.return_value = MagicMock()

        graph = build_graph(deal_id="test-deal")

        assert graph is not None
        mock_init.assert_called_once()
        mock_build_orch.assert_called_once_with(deal_id="test-deal")

    @patch("backend.app.agent.graph.build_orchestrator")
    @patch("backend.app.agent.graph.ProjectHistoryStore")
    @patch("backend.app.agent.graph.CompanyContextStore")
    @patch("backend.app.agent.graph.init_tool_context")
    def test_init_tool_context_called_with_stores(
        self,
        mock_init,
        mock_ctx,
        mock_proj,
        mock_build_orch,
    ):
        from backend.app.agent.graph import build_graph

        ctx_instance = MagicMock()
        proj_instance = MagicMock()
        mock_ctx.return_value = ctx_instance
        mock_proj.return_value = proj_instance
        mock_build_orch.return_value = MagicMock()

        build_graph(deal_id="test-deal-2")

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["company_context_store"] is ctx_instance
        assert call_kwargs["project_history_store"] is proj_instance
