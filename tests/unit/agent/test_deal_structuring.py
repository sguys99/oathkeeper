"""Tests for deal_structuring node."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.nodes.deal_structuring import make_deal_structuring_node

pytestmark = pytest.mark.unit

SAMPLE_STRUCTURED = {
    "customer_name": "Acme Corp",
    "customer_size": "대",
    "customer_industry": "제조",
    "project_summary": "AI 기반 품질 검사 시스템",
    "tech_requirements": ["Python", "TensorFlow"],
    "expected_amount": 500000000,
    "deadline": "2026-06-30",
    "payment_terms": "3/3/4",
    "special_notes": None,
    "missing_fields": [],
}


@pytest.fixture
def mock_context_store():
    store = AsyncMock()
    store.query.return_value = [
        {"type": "strategy", "content": "AI 사업 확대"},
    ]
    return store


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestDealStructuringNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.call_llm")
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_happy_path(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_call_llm,
        mock_db,
        mock_context_store,
    ):
        # Setup mocks
        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_call_llm.return_value = json.dumps(SAMPLE_STRUCTURED)

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system prompt", "user prompt")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_db, mock_context_store)
        result = await node({"deal_input": "Acme Corp wants AI system"})

        assert result["structured_deal"]["customer_name"] == "Acme Corp"
        assert result["status"] == "deal_structured"
        assert "errors" not in result

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.call_llm")
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_json_parse_failure(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_call_llm,
        mock_db,
        mock_context_store,
    ):
        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_call_llm.return_value = "not valid json"

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_db, mock_context_store)
        result = await node({"deal_input": "bad input"})

        assert result["structured_deal"] == {}
        assert len(result["errors"]) == 1
        assert "deal_structuring" in result["errors"][0]

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.call_llm")
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_llm_exception(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_call_llm,
        mock_db,
        mock_context_store,
    ):
        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_call_llm.side_effect = RuntimeError("LLM down")

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_db, mock_context_store)
        result = await node({"deal_input": "test"})

        assert result["structured_deal"] == {}
        assert result["status"] == "failed"
