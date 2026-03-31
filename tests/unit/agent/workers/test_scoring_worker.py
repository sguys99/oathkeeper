"""Tests for scoring ReAct worker."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.scoring import make_scoring_worker_node

pytestmark = pytest.mark.unit

_SAMPLE_SCORES = [
    {"criterion": "Technical Fit", "score": 85, "weight": 0.20, "rationale": "Good match"},
    {"criterion": "Profitability", "score": 70, "weight": 0.20, "rationale": "OK margin"},
    {"criterion": "Resource Availability", "score": 60, "weight": 0.15, "rationale": "Tight"},
    {"criterion": "Timeline Risk", "score": 75, "weight": 0.15, "rationale": "Manageable"},
    {"criterion": "Customer Risk", "score": 80, "weight": 0.10, "rationale": "Low risk"},
    {"criterion": "Requirement Clarity", "score": 65, "weight": 0.10, "rationale": "Partial"},
    {"criterion": "Strategic Value", "score": 90, "weight": 0.10, "rationale": "High"},
]


def _make_mocks():
    """Create common mocks for scoring worker tests."""
    mock_tpl = MagicMock()
    mock_tpl.render_system.return_value = "system"
    mock_tpl.render_user.return_value = "user"
    return mock_tpl


class TestScoringWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.scoring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.scoring.make_react_worker")
    @patch("backend.app.agent.workers.scoring.get_llm")
    @patch("backend.app.agent.workers.scoring.load_prompt")
    async def test_happy_path_with_recalculation(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        # LLM returns scores with intentionally wrong total
        mock_invoke.return_value = json.dumps(
            {
                "scores": _SAMPLE_SCORES,
                "total_score": 999.0,  # Wrong — should be overridden
                "verdict": "no_go",  # Wrong — should be overridden
            },
        )

        node = make_scoring_worker_node()
        result = await node(
            {
                "structured_deal": {"project_overview": {"objective": "test"}},
                "deal_id": str(uuid.uuid4()),
            },
        )

        # Server-side recalculation should override LLM values
        assert result["total_score"] != 999.0
        expected_total = sum(s["score"] * s["weight"] for s in _SAMPLE_SCORES)
        assert result["total_score"] == round(expected_total, 2)

        # Verify verdict matches score thresholds
        if result["total_score"] >= 70:
            assert result["verdict"] == "go"
        elif result["total_score"] >= 40:
            assert result["verdict"] == "conditional_go"
        else:
            assert result["verdict"] == "no_go"

        # All scores should have weighted_score field
        assert all("weighted_score" in s for s in result["scores"])

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.scoring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.scoring.make_react_worker")
    @patch("backend.app.agent.workers.scoring.get_llm")
    @patch("backend.app.agent.workers.scoring.load_prompt")
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
        mock_invoke.side_effect = RuntimeError("LLM timeout")

        node = make_scoring_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["scores"] == []
        assert result["total_score"] == 0.0
        assert result["verdict"] == "pending"
        assert "scoring" in result["errors"][0]

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.scoring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.scoring.make_react_worker")
    @patch("backend.app.agent.workers.scoring.get_llm")
    @patch("backend.app.agent.workers.scoring.load_prompt")
    async def test_json_parse_failure(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()
        mock_invoke.return_value = "invalid json response"

        node = make_scoring_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["scores"] == []
        assert result["verdict"] == "pending"

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.scoring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.scoring.make_react_worker")
    @patch("backend.app.agent.workers.scoring.get_llm")
    @patch("backend.app.agent.workers.scoring.load_prompt")
    async def test_empty_scores_from_llm(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()
        mock_invoke.return_value = json.dumps({"scores": [], "total_score": 0})

        node = make_scoring_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["scores"] == []
        assert result["total_score"] == 0.0
        assert result["verdict"] == "no_go"
