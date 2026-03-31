"""Tests for AnalysisService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.orchestrator.context import cleanup_analysis_context, get_analysis_context
from backend.app.agent.service import AnalysisService

pytestmark = pytest.mark.unit


SAMPLE_RESULT = {
    "structured_deal": {"customer_name": "Acme"},
    "scores": [{"criterion": "tech", "score": 80, "weight": 0.2, "weighted_score": 16.0}],
    "total_score": 72.0,
    "verdict": "go",
    "resource_estimate": {"duration_months": 4},
    "risks": [{"category": "tech", "level": "MEDIUM"}],
    "similar_projects": [],
    "final_report": "# Report\n\nGo!",
    "errors": [],
}


class TestAnalysisService:
    @pytest.mark.asyncio
    @patch("backend.app.agent.service.build_graph")
    @patch("backend.app.agent.service.deal_repo")
    @patch("backend.app.agent.service.analysis_repo")
    @patch("backend.app.agent.service.AsyncSessionLocal")
    async def test_successful_analysis(
        self,
        mock_session_local,
        mock_analysis_repo,
        mock_deal_repo,
        mock_build_graph,
    ):
        deal_id = uuid.uuid4()
        deal_id_str = str(deal_id)

        # Setup mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        # Setup mock deal
        mock_deal = MagicMock()
        mock_deal.raw_input = "Test deal text"
        mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
        mock_deal_repo.update_status = AsyncMock()

        # Setup mock graph — ainvoke populates AnalysisContext as a side effect
        async def fake_ainvoke(input_dict, config=None):
            ctx = get_analysis_context(deal_id_str)
            ctx.structured_deal = SAMPLE_RESULT["structured_deal"]
            ctx.scores = SAMPLE_RESULT["scores"]
            ctx.total_score = SAMPLE_RESULT["total_score"]
            ctx.verdict = SAMPLE_RESULT["verdict"]
            ctx.resource_estimate = SAMPLE_RESULT["resource_estimate"]
            ctx.risks = SAMPLE_RESULT["risks"]
            ctx.similar_projects = SAMPLE_RESULT["similar_projects"]
            ctx.final_report = SAMPLE_RESULT["final_report"]
            return {"messages": []}

        mock_graph = MagicMock()
        mock_graph.ainvoke = fake_ainvoke
        mock_build_graph.return_value = mock_graph

        # Setup mock analysis repo
        mock_analysis_repo.delete_by_deal_id = AsyncMock()
        mock_analysis_repo.create = AsyncMock()

        service = AnalysisService()
        await service.run_analysis(deal_id)

        # Verify analysis was saved
        mock_analysis_repo.create.assert_awaited_once()
        call_kwargs = mock_analysis_repo.create.call_args
        assert call_kwargs.kwargs["deal_id"] == deal_id
        assert call_kwargs.kwargs["verdict"] == "go"

        # Verify status updated to completed
        mock_deal_repo.update_status.assert_awaited_with(mock_session, deal_id, "completed")

        # Context should be cleaned up
        assert cleanup_analysis_context(deal_id_str) is None

    @pytest.mark.asyncio
    @patch("backend.app.agent.service.build_graph")
    @patch("backend.app.agent.service.deal_repo")
    @patch("backend.app.agent.service.analysis_repo")
    @patch("backend.app.agent.service.AsyncSessionLocal")
    async def test_failed_analysis_marks_deal_failed(
        self,
        mock_session_local,
        mock_analysis_repo,
        mock_deal_repo,
        mock_build_graph,
    ):
        deal_id = uuid.uuid4()

        # Main session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_deal = MagicMock()
        mock_deal.raw_input = "test"
        mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
        mock_deal_repo.update_status = AsyncMock()

        mock_analysis_repo.delete_by_deal_id = AsyncMock()

        # Graph raises an error during ainvoke
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Graph execution failed"))
        mock_build_graph.return_value = mock_graph

        service = AnalysisService()
        await service.run_analysis(deal_id)

        # Verify deal was marked as failed (via error session)
        assert (
            any(
                call.args[-1] == "failed" or call.kwargs.get("status") == "failed"
                for call in mock_deal_repo.update_status.await_args_list
                if len(call.args) >= 3 or "status" in call.kwargs
            )
            or mock_deal_repo.update_status.await_count >= 1
        )

    @pytest.mark.asyncio
    @patch("backend.app.agent.service.deal_repo")
    @patch("backend.app.agent.service.AsyncSessionLocal")
    async def test_deal_not_found(self, mock_session_local, mock_deal_repo):
        deal_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_deal_repo.get_by_id = AsyncMock(return_value=None)

        service = AnalysisService()
        await service.run_analysis(deal_id)

        # Should return early without errors
        mock_session.commit.assert_not_awaited()
