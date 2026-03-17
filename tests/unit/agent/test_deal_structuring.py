"""Tests for deal_structuring node."""

import json
import uuid
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
    "duration_months": 6,
    "payment_terms": "3/3/4",
    "special_notes": None,
    "missing_fields": [],
}

EMPTY_COMPANY_SETTINGS = {
    "business_direction": "",
    "deal_criteria": "",
    "short_term_strategy": "",
}


@pytest.fixture
def mock_context_store():
    store = AsyncMock()
    store.query.return_value = [
        {"type": "strategy", "content": "AI 사업 확대"},
    ]
    return store


class TestDealStructuringNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.deal_structuring.update_log_parsed_output", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_happy_path(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_fetch_settings,
        mock_logged_call,
        mock_update_log,
        mock_session_local,
        mock_context_store,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_fetch_settings.return_value = EMPTY_COMPANY_SETTINGS
        mock_logged_call.return_value = (json.dumps(SAMPLE_STRUCTURED), uuid.uuid4())

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system prompt", "user prompt")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_context_store)
        result = await node({"deal_input": "Acme Corp wants AI system", "deal_id": str(uuid.uuid4())})

        assert result["structured_deal"]["customer_name"] == "Acme Corp"
        assert result["status"] == "deal_structured"
        assert "errors" not in result

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.deal_structuring.update_log_parsed_output", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_json_parse_failure(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_fetch_settings,
        mock_logged_call,
        mock_update_log,
        mock_session_local,
        mock_context_store,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_fetch_settings.return_value = EMPTY_COMPANY_SETTINGS
        mock_logged_call.return_value = ("not valid json", uuid.uuid4())

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_context_store)
        result = await node({"deal_input": "bad input", "deal_id": str(uuid.uuid4())})

        assert result["structured_deal"] == {}
        assert len(result["errors"]) == 1
        assert "deal_structuring" in result["errors"][0]

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.deal_structuring.AsyncSessionLocal")
    @patch("backend.app.agent.nodes.deal_structuring.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.fetch_company_settings", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.deal_structuring.settings_repo")
    @patch("backend.app.agent.nodes.deal_structuring.load_prompt")
    async def test_llm_exception(
        self,
        mock_load_prompt,
        mock_settings_repo,
        mock_fetch_settings,
        mock_logged_call,
        mock_session_local,
        mock_context_store,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_settings_repo.list_active_criteria = AsyncMock(return_value=[])
        mock_fetch_settings.return_value = EMPTY_COMPANY_SETTINGS
        mock_logged_call.side_effect = RuntimeError("LLM down")

        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system base"
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        node = make_deal_structuring_node(mock_context_store)
        result = await node({"deal_input": "test", "deal_id": str(uuid.uuid4())})

        assert result["structured_deal"] == {}
        assert result["status"] == "failed"
