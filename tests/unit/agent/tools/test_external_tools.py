"""Unit tests for external tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.tools.external_tools import fetch_notion_deal, web_search

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# web_search
# ---------------------------------------------------------------------------


class TestWebSearch:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.external_tools.get_settings")
    async def test_no_api_key(self, mock_settings):
        mock_settings.return_value = MagicMock(tavily_api_key="")

        result = await web_search.ainvoke({"query": "AI market trends"})
        parsed = json.loads(result)

        assert "error" in parsed
        assert "not configured" in parsed["error"]

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.external_tools.get_settings")
    async def test_successful_search(self, mock_settings):
        mock_settings.return_value = MagicMock(tavily_api_key="test-key")

        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "AI Market Report",
                    "url": "https://example.com/ai",
                    "content": "AI market is growing...",
                },
            ],
        }

        mock_tavily_module = MagicMock()
        mock_tavily_module.AsyncTavilyClient.return_value = mock_client

        import sys

        with patch.dict(sys.modules, {"tavily": mock_tavily_module}):
            result = await web_search.ainvoke({"query": "AI market trends", "max_results": 3})

        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "AI Market Report"
        mock_client.search.assert_called_once_with(query="AI market trends", max_results=3)

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.external_tools.get_settings")
    async def test_api_error(self, mock_settings):
        mock_settings.return_value = MagicMock(tavily_api_key="test-key")

        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("API rate limit")

        mock_tavily_module = MagicMock()
        mock_tavily_module.AsyncTavilyClient.return_value = mock_client

        import sys

        with patch.dict(sys.modules, {"tavily": mock_tavily_module}):
            result = await web_search.ainvoke({"query": "test"})

        parsed = json.loads(result)
        assert "error" in parsed
        assert "API rate limit" in parsed["error"]


# ---------------------------------------------------------------------------
# fetch_notion_deal
# ---------------------------------------------------------------------------


class TestFetchNotionDeal:
    @pytest.mark.asyncio
    @patch(
        "backend.app.integrations.notion_service.get_deal_content",
        new_callable=AsyncMock,
    )
    async def test_successful_fetch(self, mock_get_content):
        mock_get_content.return_value = "# Deal Title\n\nProject overview..."

        result = await fetch_notion_deal.ainvoke({"page_id": "abc-123"})

        assert "Deal Title" in result
        mock_get_content.assert_called_once_with("abc-123")

    @pytest.mark.asyncio
    @patch(
        "backend.app.integrations.notion_service.get_deal_content",
        new_callable=AsyncMock,
    )
    async def test_page_not_found(self, mock_get_content):
        mock_get_content.side_effect = RuntimeError("Page not found")

        result = await fetch_notion_deal.ainvoke({"page_id": "nonexistent"})
        parsed = json.loads(result)

        assert "error" in parsed
        assert "Page not found" in parsed["error"]
