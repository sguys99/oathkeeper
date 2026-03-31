"""Tests for deal_structuring ReAct worker."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.deal_structuring import make_deal_structuring_worker_node

pytestmark = pytest.mark.unit


class TestDealStructuringWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.deal_structuring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.deal_structuring.make_react_worker")
    @patch("backend.app.agent.workers.deal_structuring.get_llm")
    @patch("backend.app.agent.workers.deal_structuring.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_get_llm, mock_make_worker, mock_invoke):
        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system prompt"
        mock_tpl.render_user.return_value = "user prompt"
        mock_load_prompt.return_value = mock_tpl

        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        structured_data = {
            "customer_name": "테스트 고객",
            "customer_industry": "IT",
            "expected_amount": 50000,
            "amount_unit": "만원",
            "project_overview": {"objective": "AI 솔루션 구축"},
            "missing_fields": [],
        }
        mock_invoke.return_value = json.dumps(structured_data)

        node = make_deal_structuring_worker_node()
        result = await node(
            {
                "deal_input": "테스트 딜 텍스트",
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["status"] == "deal_structured"
        assert result["structured_deal"]["customer_name"] == "테스트 고객"
        assert result["structured_deal"]["expected_amount"] == 50000
        assert result["structured_deal"]["amount_unit"] == "만원"

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.deal_structuring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.deal_structuring.make_react_worker")
    @patch("backend.app.agent.workers.deal_structuring.get_llm")
    @patch("backend.app.agent.workers.deal_structuring.load_prompt")
    async def test_amount_normalization(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system"
        mock_tpl.render_user.return_value = "user"
        mock_load_prompt.return_value = mock_tpl
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        mock_invoke.return_value = json.dumps(
            {
                "expected_amount": 5,
                "amount_unit": "억원",
            },
        )

        node = make_deal_structuring_worker_node()
        result = await node(
            {
                "deal_input": "test",
                "deal_id": str(uuid.uuid4()),
            },
        )

        # 5억원 = 50000만원
        assert result["structured_deal"]["expected_amount"] == 50000
        assert result["structured_deal"]["amount_unit"] == "만원"

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.deal_structuring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.deal_structuring.make_react_worker")
    @patch("backend.app.agent.workers.deal_structuring.get_llm")
    @patch("backend.app.agent.workers.deal_structuring.load_prompt")
    async def test_error_returns_defaults(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system"
        mock_tpl.render_user.return_value = "user"
        mock_load_prompt.return_value = mock_tpl
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        mock_invoke.side_effect = RuntimeError("LLM timeout")

        node = make_deal_structuring_worker_node()
        result = await node(
            {
                "deal_input": "test",
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["structured_deal"] == {}
        assert result["status"] == "failed"
        assert "deal_structuring" in result["errors"][0]

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.deal_structuring.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.deal_structuring.make_react_worker")
    @patch("backend.app.agent.workers.deal_structuring.get_llm")
    @patch("backend.app.agent.workers.deal_structuring.load_prompt")
    async def test_json_parse_failure(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
    ):
        mock_tpl = MagicMock()
        mock_tpl.render_system.return_value = "system"
        mock_tpl.render_user.return_value = "user"
        mock_load_prompt.return_value = mock_tpl
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        mock_invoke.return_value = "not valid json at all"

        node = make_deal_structuring_worker_node()
        result = await node(
            {
                "deal_input": "test",
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["structured_deal"] == {}
        assert result["status"] == "failed"
