"""Tests for Slack webhook client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.integrations import slack_client

pytestmark = pytest.mark.unit


class TestSendAnalysisNotification:
    @patch("backend.app.integrations.slack_client.httpx.AsyncClient")
    @patch("backend.app.integrations.slack_client.get_settings")
    @pytest.mark.asyncio
    async def test_success(self, mock_settings, mock_client_cls):
        mock_settings.return_value.slack_webhook_url = "https://hooks.slack.com/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await slack_client.send_analysis_notification(
            deal_name="테스트 프로젝트",
            verdict="Go",
            total_score=85.0,
            notion_page_url="https://notion.so/page",
        )

        assert result is True
        mock_client.post.assert_awaited_once()
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert "테스트 프로젝트" in payload["text"]
        assert "85.0" in payload["text"]
        assert "notion.so/page" in payload["text"]

    @patch("backend.app.integrations.slack_client.get_settings")
    @pytest.mark.asyncio
    async def test_no_webhook_url_returns_false(self, mock_settings):
        mock_settings.return_value.slack_webhook_url = ""

        result = await slack_client.send_analysis_notification(
            deal_name="테스트",
            verdict="Go",
            total_score=80.0,
        )

        assert result is False

    @patch("backend.app.integrations.slack_client.httpx.AsyncClient")
    @patch("backend.app.integrations.slack_client.get_settings")
    @pytest.mark.asyncio
    async def test_http_error_returns_false(self, mock_settings, mock_client_cls):
        mock_settings.return_value.slack_webhook_url = "https://hooks.slack.com/test"
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500",
                request=httpx.Request("POST", "https://hooks.slack.com/test"),
                response=httpx.Response(500),
            ),
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await slack_client.send_analysis_notification(
            deal_name="테스트",
            verdict="Go",
            total_score=80.0,
        )

        assert result is False

    @patch("backend.app.integrations.slack_client.httpx.AsyncClient")
    @patch("backend.app.integrations.slack_client.get_settings")
    @pytest.mark.asyncio
    async def test_message_contains_verdict_emoji(self, mock_settings, mock_client_cls):
        mock_settings.return_value.slack_webhook_url = "https://hooks.slack.com/test"
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await slack_client.send_analysis_notification(
            deal_name="Deal",
            verdict="no_go",
            total_score=30.0,
        )

        payload = mock_client.post.call_args.kwargs["json"]
        assert ":red_circle:" in payload["text"]
