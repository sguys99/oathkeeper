"""Tests for final_verdict ReAct worker."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.final_verdict import make_final_verdict_worker_node

pytestmark = pytest.mark.unit


def _make_mocks():
    mock_tpl = MagicMock()
    mock_tpl.render_system.return_value = "system"
    mock_tpl.render_user.return_value = "user"
    return mock_tpl


def _full_state():
    return {
        "structured_deal": {"customer_name": "테스트"},
        "scores": [{"criterion": "Tech Fit", "score": 80}],
        "total_score": 72.5,
        "verdict": "go",
        "resource_estimate": {"total_cost": 30000},
        "risks": [{"category": "technical"}],
        "risk_interdependencies": [],
        "similar_projects": [],
        "deal_id": str(uuid.uuid4()),
    }


class TestFinalVerdictWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.final_verdict.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.final_verdict.make_react_worker")
    @patch("backend.app.agent.workers.final_verdict.get_llm")
    @patch("backend.app.agent.workers.final_verdict.load_prompt")
    async def test_happy_path_returns_markdown(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        markdown_report = "# 최종 판정\n\n## Go 판정\n\n전체 점수: 72.5점"
        mock_invoke.return_value = markdown_report

        node = make_final_verdict_worker_node()
        result = await node(_full_state())

        assert result["final_report"] == markdown_report
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.final_verdict.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.final_verdict.make_react_worker")
    @patch("backend.app.agent.workers.final_verdict.get_llm")
    @patch("backend.app.agent.workers.final_verdict.load_prompt")
    async def test_error_returns_defaults(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()
        mock_invoke.side_effect = RuntimeError("LLM error")

        node = make_final_verdict_worker_node()
        result = await node(_full_state())

        assert result["final_report"] == ""
        assert result["status"] == "failed"
        assert "final_verdict" in result["errors"][0]
