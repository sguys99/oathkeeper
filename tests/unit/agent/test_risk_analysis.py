"""Tests for risk_analysis node."""

import json
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


class TestRiskAnalysisNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.risk_analysis.call_llm")
    @patch("backend.app.agent.nodes.risk_analysis.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_call_llm):
        mock_call_llm.return_value = json.dumps(SAMPLE_RISKS)

        mock_tpl = MagicMock()
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_risk_analysis_node(context_store)
        result = await node({"structured_deal": {"project_summary": "test"}})

        assert len(result["risks"]) == 2
        assert result["risks"][0]["level"] == "HIGH"

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.risk_analysis.call_llm")
    @patch("backend.app.agent.nodes.risk_analysis.load_prompt")
    async def test_error_returns_empty(self, mock_load_prompt, mock_call_llm):
        mock_call_llm.side_effect = RuntimeError("LLM error")

        mock_tpl = MagicMock()
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_risk_analysis_node(context_store)
        result = await node({"structured_deal": {}})

        assert result["risks"] == []
        assert "risk_analysis" in result["errors"][0]
