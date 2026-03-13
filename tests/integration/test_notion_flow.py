"""Integration: Notion fetch → Analysis → Notion save → Slack notification."""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestNotionDealListing:
    """Test Notion deal listing through the API."""

    async def test_list_notion_deals(
        self,
        integration_client: AsyncClient,
        mock_notion_service,
    ):
        resp = await integration_client.get("/api/notion/deals")
        assert resp.status_code == 200
        data = resp.json()
        assert "deals" in data
        assert len(data["deals"]) == 1
        assert data["deals"][0]["page_id"] == "notion-page-001"
        assert data["deals"][0]["customer_name"] == "xx철강"
        mock_notion_service.list_deals.assert_awaited_once()


class TestNotionSaveFlow:
    """Test the full Notion → Analysis → Save → Slack notification flow."""

    async def test_full_notion_save_flow(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_llm,
        mock_vector_stores,
        mock_notion_service,
        mock_slack_client,
        seeded_db,
    ):
        """Create deal → analyze → save to Notion → Slack notification."""
        # 1. Create deal with a Notion page ID
        resp = await integration_client.post(
            "/api/deals/",
            json={
                "title": "Notion 연동 딜",
                "raw_input": "xx철강 AI 비전 검사 프로젝트",
                "notion_page_id": "notion-page-001",
            },
        )
        assert resp.status_code == 201
        deal_id = resp.json()["id"]

        # 2. Run analysis
        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        # 3. Verify analysis completed
        resp = await integration_client.get(f"/api/deals/{deal_id}/analysis")
        assert resp.status_code == 200
        analysis = resp.json()
        assert analysis["verdict"] is not None

        # 4. Save to Notion
        resp = await integration_client.post(f"/api/deals/{deal_id}/save-to-notion")
        assert resp.status_code == 200
        save_result = resp.json()
        assert save_result["success"] is True
        assert save_result["decision_page_id"] == "decision-page-001"

        # 5. Verify notion_service.save_analysis_to_notion was called
        mock_notion_service.save_analysis_to_notion.assert_awaited_once()

        # 6. Verify Slack notification was sent
        mock_slack_client.send_analysis_notification.assert_awaited_once()
        call_kwargs = mock_slack_client.send_analysis_notification.call_args
        assert call_kwargs.kwargs["deal_name"] == "Notion 연동 딜"

    async def test_save_without_analysis_fails(
        self,
        integration_client: AsyncClient,
        mock_notion_service,
        mock_slack_client,
    ):
        """Saving to Notion without a completed analysis should fail."""
        # Create deal without running analysis
        resp = await integration_client.post(
            "/api/deals/",
            json={"title": "미분석 딜", "raw_input": "테스트"},
        )
        deal_id = resp.json()["id"]

        resp = await integration_client.post(f"/api/deals/{deal_id}/save-to-notion")
        assert resp.status_code == 404

    async def test_notion_api_error_handling(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_llm,
        mock_vector_stores,
        mock_slack_client,
        seeded_db,
    ):
        """When Notion API fails, return appropriate error response."""
        from unittest.mock import AsyncMock, patch

        # Create and analyze deal
        resp = await integration_client.post(
            "/api/deals/",
            json={
                "title": "Notion 에러 딜",
                "raw_input": "테스트 데이터",
                "notion_page_id": "notion-page-err",
            },
        )
        deal_id = resp.json()["id"]

        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        # Mock Notion to raise
        with patch("backend.app.api.routers.notion.notion_service") as ns:
            ns.save_analysis_to_notion = AsyncMock(
                side_effect=RuntimeError("Notion API 503"),
            )
            resp = await integration_client.post(
                f"/api/deals/{deal_id}/save-to-notion",
            )
            assert resp.status_code == 502
