"""Tests for scoring node."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.nodes.scoring import (
    _determine_verdict,
    _recalculate_scores,
    make_scoring_node,
)

pytestmark = pytest.mark.unit

SAMPLE_SCORES = [
    {
        "criterion": "Technical Fit",
        "score": 85,
        "weight": 0.20,
        "weighted_score": 17.0,
        "rationale": "Good",
    },
    {
        "criterion": "Profitability",
        "score": 70,
        "weight": 0.20,
        "weighted_score": 14.0,
        "rationale": "OK",
    },
    {
        "criterion": "Resource Availability",
        "score": 60,
        "weight": 0.15,
        "weighted_score": 9.0,
        "rationale": "Tight",
    },
    {
        "criterion": "Timeline Risk",
        "score": 50,
        "weight": 0.15,
        "weighted_score": 7.5,
        "rationale": "Risky",
    },
    {
        "criterion": "Customer Risk",
        "score": 80,
        "weight": 0.10,
        "weighted_score": 8.0,
        "rationale": "Stable",
    },
    {
        "criterion": "Requirement Clarity",
        "score": 75,
        "weight": 0.10,
        "weighted_score": 7.5,
        "rationale": "Clear",
    },
    {
        "criterion": "Strategic Value",
        "score": 90,
        "weight": 0.10,
        "weighted_score": 9.0,
        "rationale": "High",
    },
]

EMPTY_COMPANY_SETTINGS = {
    "business_direction": "",
    "deal_criteria": "",
    "short_term_strategy": "",
}


class TestDetermineVerdict:
    def test_go(self):
        assert _determine_verdict(70.0) == "go"
        assert _determine_verdict(85.0) == "go"

    def test_conditional_go(self):
        assert _determine_verdict(40.0) == "conditional_go"
        assert _determine_verdict(69.9) == "conditional_go"

    def test_no_go(self):
        assert _determine_verdict(39.9) == "no_go"
        assert _determine_verdict(0.0) == "no_go"


class TestRecalculateScores:
    def test_recalculates_weighted_scores(self):
        scores = [
            {"criterion": "A", "score": 80, "weight": 0.5, "weighted_score": 999, "rationale": "x"},
            {"criterion": "B", "score": 60, "weight": 0.5, "weighted_score": 999, "rationale": "y"},
        ]
        recalculated, total = _recalculate_scores(scores)

        assert recalculated[0]["weighted_score"] == 40.0
        assert recalculated[1]["weighted_score"] == 30.0
        assert total == 70.0

    def test_empty_scores(self):
        recalculated, total = _recalculate_scores([])
        assert recalculated == []
        assert total == 0.0


class TestScoringNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.scoring.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.scoring.update_log_parsed_output", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.scoring.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.scoring.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.scoring.settings_repo")
    @patch("backend.app.agent.nodes.scoring.load_prompt")
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

        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_fetch_settings.return_value = EMPTY_COMPANY_SETTINGS
        mock_logged_call.return_value = (
            json.dumps(
                {
                    "scores": SAMPLE_SCORES,
                    "total_score": 72.0,
                    "verdict": "go",
                },
            ),
            uuid.uuid4(),
        )

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        context_store = AsyncMock()
        context_store.query.return_value = []

        node = make_scoring_node(context_store)
        result = await node(
            {
                "structured_deal": {"project_summary": "test"},
                "deal_id": str(uuid.uuid4()),
                "resource_estimate": {
                    "profitability": {
                        "deal_amount": 10000,
                        "estimated_cost": 31000,
                        "expected_margin": -2.15,
                        "margin_assessment": "적자",
                    },
                    "team_composition": [
                        {"role": "PM", "count": 1, "duration_months": 3},
                    ],
                    "duration_months": 3,
                    "duration_with_buffer": 3.6,
                },
            },
        )

        assert len(result["scores"]) == 7
        assert isinstance(result["total_score"], float)
        assert result["verdict"] in ("go", "conditional_go", "no_go")

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.scoring.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.scoring.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.scoring.settings_repo")
    @patch("backend.app.agent.nodes.scoring.load_prompt")
    async def test_error_returns_defaults(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_fetch_settings,
        mock_session_local,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_active_criteria = AsyncMock(side_effect=RuntimeError("DB error"))

        node = make_scoring_node(AsyncMock())
        result = await node({"structured_deal": {}, "deal_id": str(uuid.uuid4())})

        assert result["scores"] == []
        assert result["verdict"] == "pending"
        assert "scoring" in result["errors"][0]
