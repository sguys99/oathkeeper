"""Tests for risk_analysis node."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.nodes.risk_analysis import make_risk_analysis_node

pytestmark = pytest.mark.unit

SAMPLE_RISKS = {
    "risks": [
        {
            "category": "technology",
            "item": "Unfamiliar ML framework",
            "level": "HIGH",
            "description": "Team lacks experience with requested framework",
            "mitigation": "Hire consultant or allocate training time",
        },
        {
            "category": "timeline",
            "item": "Tight deadline",
            "level": "MEDIUM",
            "description": "4 month deadline for complex project",
            "mitigation": "Increase team size or reduce scope",
        },
    ],
}

EMPTY_COMPANY_SETTINGS = {
    "business_direction": "",
    "deal_criteria": "",
    "short_term_strategy": "",
}


class TestRiskAnalysisNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.risk_analysis.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.risk_analysis.update_log_parsed_output", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.risk_analysis.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.risk_analysis.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.risk_analysis.load_prompt")
    async def test_happy_path(
        self,
        mock_load_prompt,
        mock_fetch_settings,
        mock_logged_call,
        mock_update_log,
        mock_session_local,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_fetch_settings.return_value = EMPTY_COMPANY_SETTINGS
        mock_logged_call.return_value = (json.dumps(SAMPLE_RISKS), uuid.uuid4())

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_risk_analysis_node(context_store)
        result = await node(
            {"structured_deal": {"project_summary": "test"}, "deal_id": str(uuid.uuid4())},
        )

        assert len(result["risks"]) == 2
        assert result["risks"][0]["level"] == "HIGH"

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.risk_analysis.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.risk_analysis.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.risk_analysis.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.risk_analysis.load_prompt")
    async def test_error_returns_empty(
        self,
        mock_load_prompt,
        mock_fetch_settings,
        mock_logged_call,
        mock_session_local,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_fetch_settings.side_effect = RuntimeError("DB error")

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_risk_analysis_node(context_store)
        result = await node({"structured_deal": {}, "deal_id": str(uuid.uuid4())})

        assert result["risks"] == []
        assert "risk_analysis" in result["errors"][0]
