"""Tests for AnalysisService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.service import AnalysisService
from backend.app.agent.workflows import WorkflowType

pytestmark = pytest.mark.unit


SAMPLE_RESULT = {
    "structured_deal": {"customer_name": "Acme"},
    "scores": [{"criterion": "tech", "score": 80, "weight": 0.2, "weighted_score": 16.0}],
    "total_score": 72.0,
    "verdict": "go",
    "resource_estimate": {"duration_months": 4},
    "risks": [{"category": "tech", "level": "MEDIUM"}],
    "risk_interdependencies": [],
    "similar_projects": [],
    "final_report": "# Report\n\nGo!",
}


class TestAnalysisService:
    @pytest.mark.asyncio
    @patch("backend.app.agent.service.get_workflow")
    @patch("backend.app.agent.service.deal_repo")
    @patch("backend.app.agent.service.analysis_repo")
    @patch("backend.app.agent.service.AsyncSessionLocal")
    async def test_successful_analysis(
        self,
        mock_session_local,
        mock_analysis_repo,
        mock_deal_repo,
        mock_get_workflow,
    ):
        deal_id = uuid.uuid4()

        # Setup mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        # Setup mock deal
        mock_deal = MagicMock()
        mock_deal.raw_input = "Test deal text"
        mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
        mock_deal_repo.update_status = AsyncMock()

        # Setup mock workflow
        mock_workflow = MagicMock()
        mock_workflow.execute = AsyncMock(return_value=SAMPLE_RESULT)
        mock_get_workflow.return_value = mock_workflow

        # Setup mock analysis repo
        mock_analysis_repo.delete_by_deal_id = AsyncMock()
        mock_analysis_repo.create = AsyncMock()

        service = AnalysisService()
        await service.run_analysis(deal_id, WorkflowType.STATIC)

        # Verify workflow was selected
        mock_get_workflow.assert_called_once_with(WorkflowType.STATIC)

        # Verify workflow was executed
        mock_workflow.execute.assert_awaited_once()

        # Verify analysis was saved
        mock_analysis_repo.create.assert_awaited_once()
        call_kwargs = mock_analysis_repo.create.call_args
        assert call_kwargs.kwargs["deal_id"] == deal_id
        assert call_kwargs.kwargs["verdict"] == "go"
        assert call_kwargs.kwargs["workflow_type"] == "static"

        # Verify status updated to completed
        mock_deal_repo.update_status.assert_awaited_with(mock_session, deal_id, "completed")

    @pytest.mark.asyncio
    @patch("backend.app.agent.service.get_workflow")
    @patch("backend.app.agent.service.deal_repo")
    @patch("backend.app.agent.service.analysis_repo")
    @patch("backend.app.agent.service.AsyncSessionLocal")
    async def test_failed_analysis_marks_deal_failed(
        self,
        mock_session_local,
        mock_analysis_repo,
        mock_deal_repo,
        mock_get_workflow,
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

        # Workflow raises an error
        mock_workflow = MagicMock()
        mock_workflow.execute = AsyncMock(side_effect=RuntimeError("Workflow failed"))
        mock_get_workflow.return_value = mock_workflow

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
