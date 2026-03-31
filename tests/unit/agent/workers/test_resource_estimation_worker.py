"""Tests for resource_estimation ReAct worker."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.resource_estimation import make_resource_estimation_worker_node

pytestmark = pytest.mark.unit


def _make_mocks():
    mock_tpl = MagicMock()
    mock_tpl.render_system.return_value = "system"
    mock_tpl.render_user.return_value = "user"
    return mock_tpl


class TestResourceEstimationWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.resource_estimation.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.resource_estimation.make_react_worker")
    @patch("backend.app.agent.workers.resource_estimation.get_llm")
    @patch("backend.app.agent.workers.resource_estimation.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_get_llm, mock_make_worker, mock_invoke):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        estimate = {
            "total_cost": 25000,
            "duration_months": 6,
            "team_composition": [{"role": "Backend", "count": 2}],
            "profitability": {"expected_margin": 0.35},
        }
        mock_invoke.return_value = json.dumps(estimate)

        node = make_resource_estimation_worker_node()
        result = await node(
            {
                "structured_deal": {"project_overview": {"objective": "AI"}},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["resource_estimate"]["total_cost"] == 25000
        assert result["resource_estimate"]["duration_months"] == 6

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.resource_estimation.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.resource_estimation.make_react_worker")
    @patch("backend.app.agent.workers.resource_estimation.get_llm")
    @patch("backend.app.agent.workers.resource_estimation.load_prompt")
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
        mock_invoke.side_effect = RuntimeError("timeout")

        node = make_resource_estimation_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["resource_estimate"] == {}
        assert "resource_estimation" in result["errors"][0]
