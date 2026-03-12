"""Integration tests for Notion API.

Requires NOTION_API_KEY, NOTION_DEAL_DB_ID, NOTION_DECISION_DB_ID in environment.
Run with: uv run pytest -m integration tests/integration/test_notion.py -v
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.integrations import notion_client, notion_service

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="module")]


class TestNotionDealRead:
    async def test_list_deals_from_notion(self):
        """Fetch deals from the real Notion deal information DB."""
        deals = await notion_service.list_deals()
        assert isinstance(deals, list)
        # The test DB should have at least one deal
        assert len(deals) > 0
        deal = deals[0]
        assert deal.page_id
        assert isinstance(deal.deal_info, str)

    async def test_get_deal_content(self):
        """Fetch page content from the first available deal."""
        deals = await notion_service.list_deals()
        assert len(deals) > 0

        content = await notion_service.get_deal_content(deals[0].page_id)
        assert isinstance(content, str)


class TestNotionDecisionWrite:
    async def test_create_and_cleanup_decision_page(self):
        """Create an analysis result page, then archive it to clean up."""
        analysis = MagicMock()
        analysis.id = uuid4()
        analysis.deal_id = uuid4()
        analysis.total_score = 72.5
        analysis.verdict = "go"
        analysis.report_markdown = "# 테스트 분석 결과\n\n통합 테스트용 리포트입니다."
        analysis.notion_saved_at = None

        page_id = None
        try:
            result = await notion_service.save_analysis_to_notion(analysis)
            assert result.success is True
            assert result.decision_page_id is not None
            assert result.saved_at is not None
            page_id = result.decision_page_id
        finally:
            # Clean up: archive the created page
            if page_id:
                client = notion_client.get_notion_client()
                await client.pages.update(page_id=page_id, archived=True)
