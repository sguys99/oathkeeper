"""Tests for Notion service — deal listing, content parsing, analysis save."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.app.api.schemas.notion import NotionDeal, NotionSaveResponse
from backend.app.integrations import notion_service

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_notion_page(
    page_id: str = "page-001",
    deal_info: str = "xx철강 AI 비전 프로젝트",
    customer_name: str | None = "xx철강",
    expected_amount: int | None = 100_000_000,
    deadline: str | None = "2026-06-01",
    date: str | None = "2026-03-01",
    author_name: str | None = "홍길동",
    status: str | None = "미분석",
) -> dict:
    """Build a fake Notion page dict matching the API response structure."""
    props: dict = {
        "deal_info": {"title": [{"plain_text": deal_info}] if deal_info else []},
        "customer_name": {"rich_text": [{"plain_text": customer_name}] if customer_name else []},
        "expected_amount": {"number": expected_amount},
        "deadline": {"date": {"start": deadline} if deadline else None},
        "date": {"date": {"start": date} if date else None},
        "author": {"people": [{"name": author_name}] if author_name else []},
        "status": {"select": {"name": status} if status else None},
    }
    return {"id": page_id, "properties": props}


def _make_notion_blocks(texts: list[str]) -> list[dict]:
    """Build fake Notion block dicts (paragraphs)."""
    return [
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"plain_text": t}]},
        }
        for t in texts
    ]


def _make_analysis_result(**overrides):
    """Build a mock AnalysisResult."""
    mock = MagicMock()
    mock.id = overrides.get("id", uuid4())
    mock.deal_id = overrides.get("deal_id", uuid4())
    mock.total_score = overrides.get("total_score", 75.0)
    mock.verdict = overrides.get("verdict", "go")
    mock.scores = overrides.get("scores", {})
    mock.resource_estimate = overrides.get("resource_estimate", {})
    mock.risks = overrides.get("risks", {})
    mock.similar_projects = overrides.get("similar_projects", {})
    mock.report_markdown = overrides.get("report_markdown", "# Report\n\nAnalysis complete.")
    mock.notion_saved_at = overrides.get("notion_saved_at", None)
    return mock


# ---------------------------------------------------------------------------
# list_deals
# ---------------------------------------------------------------------------


class TestListDeals:
    @patch("backend.app.integrations.notion_service.notion_client")
    @patch("backend.app.integrations.notion_service.get_settings")
    @pytest.mark.asyncio
    async def test_parses_pages(self, mock_settings, mock_nc):
        mock_settings.return_value.notion_deal_db_id = "db-deal-123"
        mock_nc.query_database = AsyncMock(
            return_value=[
                _make_notion_page(page_id="p1", deal_info="프로젝트A", customer_name="고객사A"),
                _make_notion_page(page_id="p2", deal_info="프로젝트B", customer_name="고객사B"),
            ],
        )

        result = await notion_service.list_deals()

        assert len(result) == 2
        assert isinstance(result[0], NotionDeal)
        assert result[0].page_id == "p1"
        assert result[0].deal_info == "프로젝트A"
        assert result[0].customer_name == "고객사A"
        assert result[1].page_id == "p2"
        mock_nc.query_database.assert_awaited_once_with("db-deal-123")

    @patch("backend.app.integrations.notion_service.notion_client")
    @patch("backend.app.integrations.notion_service.get_settings")
    @pytest.mark.asyncio
    async def test_handles_empty_properties(self, mock_settings, mock_nc):
        mock_settings.return_value.notion_deal_db_id = "db-deal-123"
        mock_nc.query_database = AsyncMock(
            return_value=[
                _make_notion_page(
                    page_id="p-empty",
                    deal_info="",
                    customer_name=None,
                    expected_amount=None,
                    deadline=None,
                    date=None,
                    author_name=None,
                    status=None,
                ),
            ],
        )

        result = await notion_service.list_deals()

        assert len(result) == 1
        deal = result[0]
        assert deal.page_id == "p-empty"
        assert deal.deal_info == ""
        assert deal.customer_name is None
        assert deal.expected_amount is None
        assert deal.deadline is None
        assert deal.date is None
        assert deal.author is None
        assert deal.status is None


# ---------------------------------------------------------------------------
# get_deal_content
# ---------------------------------------------------------------------------


class TestGetDealContent:
    @patch("backend.app.integrations.notion_service.notion_client")
    @pytest.mark.asyncio
    async def test_extracts_text(self, mock_nc):
        mock_nc.get_page_content = AsyncMock(
            return_value=_make_notion_blocks(["프로젝트 개요입니다.", "기술 요구사항: AI 비전"]),
        )

        result = await notion_service.get_deal_content("page-abc")

        assert "프로젝트 개요입니다." in result
        assert "기술 요구사항: AI 비전" in result
        mock_nc.get_page_content.assert_awaited_once_with("page-abc")

    @patch("backend.app.integrations.notion_service.notion_client")
    @pytest.mark.asyncio
    async def test_empty_blocks_returns_empty_string(self, mock_nc):
        mock_nc.get_page_content = AsyncMock(return_value=[])

        result = await notion_service.get_deal_content("page-xyz")

        assert result == ""


# ---------------------------------------------------------------------------
# save_analysis_to_notion
# ---------------------------------------------------------------------------


class TestSaveAnalysisToNotion:
    @patch("backend.app.integrations.notion_service.notion_client")
    @patch("backend.app.integrations.notion_service.get_settings")
    @pytest.mark.asyncio
    async def test_creates_page(self, mock_settings, mock_nc):
        mock_settings.return_value.notion_decision_db_id = "db-decision-123"
        mock_nc.create_page = AsyncMock(
            return_value={"id": "new-page-id", "url": "https://notion.so/new-page"},
        )
        mock_nc.update_page_property = AsyncMock()

        analysis = _make_analysis_result(verdict="go", total_score=85.0)
        result = await notion_service.save_analysis_to_notion(analysis)

        assert isinstance(result, NotionSaveResponse)
        assert result.success is True
        assert result.decision_page_id == "new-page-id"
        assert result.notion_page_url == "https://notion.so/new-page"
        assert result.saved_at is not None

        # Verify create_page was called with correct DB ID
        call_kwargs = mock_nc.create_page.call_args.kwargs
        assert call_kwargs["parent_database_id"] == "db-decision-123"

        # Verify properties mapping
        props = call_kwargs["properties"]
        assert props["decision"]["select"]["name"] == "Go"
        assert props["total_score"]["number"] == 85.0

        # No deal_page_id → no update call
        mock_nc.update_page_property.assert_not_awaited()

    @patch("backend.app.integrations.notion_service.notion_client")
    @patch("backend.app.integrations.notion_service.get_settings")
    @pytest.mark.asyncio
    async def test_updates_deal_status_when_page_id_provided(self, mock_settings, mock_nc):
        mock_settings.return_value.notion_decision_db_id = "db-decision-123"
        mock_nc.create_page = AsyncMock(
            return_value={"id": "new-page-id", "url": "https://notion.so/new-page"},
        )
        mock_nc.update_page_property = AsyncMock()

        analysis = _make_analysis_result(verdict="conditional_go", total_score=60.0)
        await notion_service.save_analysis_to_notion(analysis, deal_page_id="deal-page-abc")

        # Verify deal status updated to "완료"
        mock_nc.update_page_property.assert_awaited_once_with(
            "deal-page-abc",
            {"status": {"select": {"name": "완료"}}},
        )

        # Verify relation property was set
        props = mock_nc.create_page.call_args.kwargs["properties"]
        assert props["deal"]["relation"] == [{"id": "deal-page-abc"}]

    @patch("backend.app.integrations.notion_service.notion_client")
    @patch("backend.app.integrations.notion_service.get_settings")
    @pytest.mark.asyncio
    async def test_verdict_mapping(self, mock_settings, mock_nc):
        mock_settings.return_value.notion_decision_db_id = "db-decision-123"
        mock_nc.create_page = AsyncMock(
            return_value={"id": "p", "url": "https://notion.so/p"},
        )

        for db_val, expected in [
            ("go", "Go"),
            ("conditional_go", "Conditional Go"),
            ("no_go", "No-Go"),
            ("pending", "Hold"),
        ]:
            analysis = _make_analysis_result(verdict=db_val)
            await notion_service.save_analysis_to_notion(analysis)
            props = mock_nc.create_page.call_args.kwargs["properties"]
            assert props["decision"]["select"]["name"] == expected


# ---------------------------------------------------------------------------
# Markdown → Notion blocks
# ---------------------------------------------------------------------------


class TestMarkdownToNotionBlocks:
    def test_heading_detection(self):
        blocks = notion_service._markdown_to_notion_blocks(
            "# Heading 1\n## Heading 2\n### Heading 3\nParagraph",
        )
        assert blocks[0]["type"] == "heading_1"
        assert blocks[1]["type"] == "heading_2"
        assert blocks[2]["type"] == "heading_3"
        assert blocks[3]["type"] == "paragraph"

    def test_empty_lines_skipped(self):
        blocks = notion_service._markdown_to_notion_blocks("Line1\n\n\nLine2")
        assert len(blocks) == 2

    def test_long_text_chunked(self):
        long_text = "x" * 5000
        blocks = notion_service._markdown_to_notion_blocks(long_text)
        rich_texts = blocks[0]["paragraph"]["rich_text"]
        assert len(rich_texts) == 3  # 2000 + 2000 + 1000
        assert len(rich_texts[0]["text"]["content"]) == 2000
