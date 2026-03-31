"""Tests for risk_analysis ReAct worker."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.risk_analysis import make_risk_analysis_worker_node

pytestmark = pytest.mark.unit


def _make_mocks():
    mock_tpl = MagicMock()
    mock_tpl.render_system.return_value = "system"
    mock_tpl.render_user.return_value = "user"
    return mock_tpl


class TestRiskAnalysisWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.risk_analysis.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.risk_analysis.make_react_worker")
    @patch("backend.app.agent.workers.risk_analysis.get_llm")
    @patch("backend.app.agent.workers.risk_analysis.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_get_llm, mock_make_worker, mock_invoke):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        mock_invoke.return_value = json.dumps(
            {
                "risks": [
                    {"category": "technical", "item": "AI 정확도", "probability": 0.3, "impact": 0.8},
                ],
                "risk_interdependencies": [
                    {
                        "risk_pair": ["AI 정확도", "일정 지연"],
                        "amplification": "기술적 실패 시 일정 영향",
                    },
                ],
            },
        )

        node = make_risk_analysis_worker_node()
        result = await node(
            {
                "structured_deal": {"project_overview": {"objective": "AI"}},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert len(result["risks"]) == 1
        assert result["risks"][0]["category"] == "technical"
        assert len(result["risk_interdependencies"]) == 1

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.risk_analysis.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.risk_analysis.make_react_worker")
    @patch("backend.app.agent.workers.risk_analysis.get_llm")
    @patch("backend.app.agent.workers.risk_analysis.load_prompt")
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
        mock_invoke.side_effect = RuntimeError("API error")

        node = make_risk_analysis_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["risks"] == []
        assert "risk_analysis" in result["errors"][0]
