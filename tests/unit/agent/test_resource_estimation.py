"""Tests for resource_estimation node."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.nodes.resource_estimation import make_resource_estimation_node

pytestmark = pytest.mark.unit

SAMPLE_ESTIMATE = {
    "team_composition": [
        {"role": "PM", "count": 1, "monthly_rate": 10000000},
        {"role": "BE", "count": 2, "monthly_rate": 8000000},
    ],
    "duration_months": 4,
    "total_cost": 104000000,
    "expected_margin": 0.25,
    "rationale": "Based on similar projects",
}


class TestResourceEstimationNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.resource_estimation.AsyncSessionLocal")
    @patch(
        "backend.app.agent.nodes.resource_estimation.update_log_parsed_output",
        new_callable=AsyncMock,
    )
    @patch("backend.app.agent.nodes.resource_estimation.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.resource_estimation.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.resource_estimation.settings_repo")
    @patch("backend.app.agent.nodes.resource_estimation.load_prompt")
    async def test_happy_path(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_fetch_settings,
        mock_logged_call,
        mock_update_log,
        mock_session_local,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_team_members = AsyncMock(return_value=[])
        mock_settings_repo.get_setting = AsyncMock(return_value=None)
        mock_fetch_settings.return_value = {
            "business_direction": "",
            "deal_criteria": "",
            "short_term_strategy": "",
        }
        mock_logged_call.return_value = (json.dumps(SAMPLE_ESTIMATE), uuid.uuid4())

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        project_store = AsyncMock()
        project_store.search_similar.return_value = []

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_resource_estimation_node(project_store, context_store)
        result = await node(
            {"structured_deal": {"project_summary": "test"}, "deal_id": str(uuid.uuid4())},
        )

        assert result["resource_estimate"]["duration_months"] == 4
        assert len(result["resource_estimate"]["team_composition"]) == 2

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.resource_estimation.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.resource_estimation.settings_repo")
    @patch("backend.app.agent.nodes.resource_estimation.load_prompt")
    async def test_error_returns_empty(self, mock_load_prompt, mock_settings_repo, mock_session_local):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_team_members = AsyncMock(side_effect=RuntimeError("fail"))

        node = make_resource_estimation_node(AsyncMock(), AsyncMock())
        result = await node({"structured_deal": {}, "deal_id": str(uuid.uuid4())})

        assert result["resource_estimate"] == {}
        assert "resource_estimation" in result["errors"][0]
