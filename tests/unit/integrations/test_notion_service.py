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
    duration_months: int | None = 6,
    date: str | None = "2026-03-01",
    author_name: str | None = "홍길동",
    status: str | None = "미분석",
) -> dict:
    """Build a fake Notion page dict matching the API response structure."""
    props: dict = {
        "deal_info": {"title": [{"plain_text": deal_info}] if deal_info else []},
        "customer_name": {"rich_text": [{"plain_text": customer_name}] if customer_name else []},
        "expected_amount": {"number": expected_amount},
        "duration_months": {"number": duration_months},
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
                    duration_months=None,
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
        assert deal.duration_months is None
        assert deal.date is None
        assert deal.author is None
        assert deal.status is None


# ---------------------------------------------------------------------------
# get_deal_content
# ---------------------------------------------------------------------------


class TestGetDealContent:
    @patch("backend.app.integrations.notion_service.notion_client")
    @pytest.mark.asyncio
    async def test_includes_properties_and_body(self, mock_nc):
        props = _make_notion_page(
            customer_name="성대 보일러",
            expected_amount=50_000_000,
            duration_months=3,
        )["properties"]
        mock_nc.get_page_properties = AsyncMock(return_value=props)
        mock_nc.get_page_content = AsyncMock(
            return_value=_make_notion_blocks(["프로젝트 개요입니다.", "기술 요구사항: AI 비전"]),
        )

        result = await notion_service.get_deal_content("page-abc")

        assert "[딜 기본 정보]" in result
        assert "고객명: 성대 보일러" in result
        assert "예상 금액: 50,000,000" in result
        assert "수행 기간(개월): 3" in result
        assert "[상세 내용]" in result
        assert "프로젝트 개요입니다." in result
        assert "기술 요구사항: AI 비전" in result

    @patch("backend.app.integrations.notion_service.notion_client")
    @pytest.mark.asyncio
    async def test_empty_blocks_and_properties(self, mock_nc):
        mock_nc.get_page_properties = AsyncMock(return_value={})
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
# _properties_to_text
# ---------------------------------------------------------------------------


class TestPropertiesToText:
    def test_all_fields(self):
        props = _make_notion_page(
            deal_info="AI 비전 프로젝트",
            customer_name="성대 보일러",
            expected_amount=50_000_000,
            duration_months=3,
            date="2026-03-15",
            author_name="유광명",
        )["properties"]

        result = notion_service._properties_to_text(props)

        assert "딜 정보: AI 비전 프로젝트" in result
        assert "고객명: 성대 보일러" in result
        assert "예상 금액: 50,000,000" in result
        assert "수행 기간(개월): 3" in result
        assert "등록일: 2026-03-15" in result
        assert "작성자: 유광명" in result

    def test_empty_properties(self):
        result = notion_service._properties_to_text({})
        assert result == ""

    def test_partial_properties(self):
        props = _make_notion_page(
            customer_name="테스트",
            expected_amount=None,
            duration_months=None,
            author_name=None,
        )["properties"]

        result = notion_service._properties_to_text(props)

        assert "고객명: 테스트" in result
        assert "예상 금액" not in result
        assert "수행 기간" not in result
        assert "작성자" not in result


# ---------------------------------------------------------------------------
# _blocks_to_text (nested)
# ---------------------------------------------------------------------------


class TestBlocksToTextNested:
    def test_flat_blocks(self):
        blocks = _make_notion_blocks(["첫 번째", "두 번째"])
        result = notion_service._blocks_to_text(blocks)
        assert result == "첫 번째\n두 번째"

    def test_nested_children(self):
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": "현장 확인 결과"}]},
                "has_children": True,
                "children": [
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"plain_text": "바코드 인식용 로봇 비전 카메라 사용중"}],
                        },
                    },
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"plain_text": "현재 근접 촬영 이미지만 보유"}],
                        },
                    },
                ],
            },
        ]

        result = notion_service._blocks_to_text(blocks)

        assert "현장 확인 결과" in result
        assert "  바코드 인식용 로봇 비전 카메라 사용중" in result
        assert "  현재 근접 촬영 이미지만 보유" in result

    def test_deeply_nested(self):
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"plain_text": "레벨0"}]},
                "has_children": True,
                "children": [
                    {
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"plain_text": "레벨1"}]},
                        "has_children": True,
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {"rich_text": [{"plain_text": "레벨2"}]},
                            },
                        ],
                    },
                ],
            },
        ]

        result = notion_service._blocks_to_text(blocks)

        assert "레벨0" in result
        assert "  레벨1" in result
        assert "    레벨2" in result


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
