"""Tests for LangGraph orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.graph import _route_after_structuring, hold_verdict_node

pytestmark = pytest.mark.unit


class TestRouteAfterStructuring:
    def test_hold_when_many_missing_fields(self):
        state = {
            "structured_deal": {
                "missing_fields": ["customer_name", "expected_amount", "deadline"],
            },
        }
        sends = _route_after_structuring(state)
        assert len(sends) == 1
        assert sends[0].node == "hold_verdict"

    def test_continue_when_few_missing_fields(self):
        state = {
            "structured_deal": {
                "missing_fields": ["payment_terms"],
            },
        }
        sends = _route_after_structuring(state)
        assert len(sends) == 4
        node_names = {s.node for s in sends}
        assert node_names == {"scoring", "resource_estimation", "risk_analysis", "similar_project"}

    def test_hold_when_structured_deal_empty(self):
        state = {"structured_deal": {}}
        sends = _route_after_structuring(state)
        assert len(sends) == 1
        assert sends[0].node == "hold_verdict"

    def test_hold_when_structured_deal_missing(self):
        state = {}
        sends = _route_after_structuring(state)
        assert len(sends) == 1
        assert sends[0].node == "hold_verdict"

    def test_continue_when_no_missing_fields(self):
        state = {
            "structured_deal": {
                "customer_name": "Acme",
                "missing_fields": [],
            },
        }
        sends = _route_after_structuring(state)
        assert len(sends) == 4


class TestHoldVerdictNode:
    def test_returns_hold_state(self):
        state = {
            "structured_deal": {
                "missing_fields": ["customer_name", "budget", "deadline"],
            },
        }
        result = hold_verdict_node(state)

        assert result["verdict"] == "pending"
        assert result["total_score"] == 0.0
        assert "보류" in result["final_report"]
        assert result["status"] == "completed"

    def test_empty_missing_fields(self):
        result = hold_verdict_node({"structured_deal": {}})
        assert result["verdict"] == "pending"


class TestBuildGraph:
    @patch("backend.app.agent.graph.CompanyContextStore")
    @patch("backend.app.agent.graph.ProjectHistoryStore")
    def test_graph_compiles(self, mock_project_store, mock_context_store):
        from backend.app.agent.graph import build_graph

        mock_context_store.return_value = MagicMock()
        mock_project_store.return_value = MagicMock()

        graph = build_graph(AsyncMock())
        assert graph is not None

    @pytest.mark.asyncio
    @patch("backend.app.agent.graph.CompanyContextStore")
    @patch("backend.app.agent.graph.ProjectHistoryStore")
    @patch("backend.app.agent.graph.make_deal_structuring_node")
    @patch("backend.app.agent.graph.make_scoring_node")
    @patch("backend.app.agent.graph.make_resource_estimation_node")
    @patch("backend.app.agent.graph.make_risk_analysis_node")
    @patch("backend.app.agent.graph.make_similar_project_node")
    @patch("backend.app.agent.graph.make_final_verdict_node")
    async def test_hold_path(
        self,
        mock_final,
        mock_similar,
        mock_risk,
        mock_resource,
        mock_scoring,
        mock_deal,
        mock_project_store,
        mock_context_store,
    ):
        """When deal_structuring returns many missing fields, graph takes hold path."""
        from backend.app.agent.graph import build_graph

        mock_context_store.return_value = MagicMock()
        mock_project_store.return_value = MagicMock()

        # deal_structuring returns many missing fields
        async def fake_deal_structuring(state):
            return {
                "structured_deal": {
                    "missing_fields": ["a", "b", "c", "d"],
                },
                "status": "deal_structured",
            }

        mock_deal.return_value = fake_deal_structuring

        graph = build_graph(AsyncMock())
        result = await graph.ainvoke({"deal_input": "vague deal"})

        assert result["verdict"] == "pending"
        assert result["status"] == "completed"
        # Parallel nodes should NOT have been called
        mock_scoring.return_value.assert_not_called()
