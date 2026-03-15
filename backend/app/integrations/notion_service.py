"""Notion business logic — deal listing, content parsing, analysis save."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.api.schemas.notion import NotionDeal, NotionSaveResponse
from backend.app.db.models.analysis_result import AnalysisResult
from backend.app.integrations import notion_client
from backend.app.utils.settings import get_settings

logger = logging.getLogger(__name__)

# Verdict mapping: DB value → Notion Select display name
_VERDICT_MAP: dict[str, str] = {
    "go": "Go",
    "conditional_go": "Conditional Go",
    "no_go": "No-Go",
    "pending": "Hold",
}

# Max characters per Notion rich_text element
_RICH_TEXT_LIMIT = 2000


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def list_deals() -> list[NotionDeal]:
    """Fetch all deals from the Notion deal information DB."""
    settings = get_settings()
    pages = await notion_client.query_database(settings.notion_deal_db_id)
    return [_parse_deal_page(page) for page in pages]


async def get_deal_content(page_id: str) -> str:
    """Extract plain text from a Notion deal page's body blocks."""
    blocks = await notion_client.get_page_content(page_id)
    return _blocks_to_text(blocks)


async def archive_deal_page(notion_page_id: str) -> bool:
    """Archive the source deal page in Notion. Returns True on success."""
    try:
        await notion_client.archive_page(notion_page_id)
        return True
    except Exception:
        logger.warning("Failed to archive Notion page %s", notion_page_id, exc_info=True)
        return False


async def save_analysis_to_notion(
    analysis: AnalysisResult,
    deal_page_id: str | None = None,
) -> NotionSaveResponse:
    """Create a page in the ai decision DB with the analysis results."""
    settings = get_settings()
    now = datetime.now(tz=UTC)

    properties = _build_decision_properties(analysis, deal_page_id, now)
    children = _markdown_to_notion_blocks(analysis.report_markdown or "")

    page = await notion_client.create_page(
        parent_database_id=settings.notion_decision_db_id,
        properties=properties,
        children=children[:100],  # Notion API limit: 100 blocks per create
    )

    # Append remaining blocks if report exceeds 100 blocks
    if len(children) > 100:
        client = notion_client.get_notion_client()
        for i in range(100, len(children), 100):
            await client.blocks.children.append(
                block_id=page["id"],
                children=children[i : i + 100],
            )

    # Update deal status to "완료" if we have the page ID
    if deal_page_id:
        await notion_client.update_page_property(
            deal_page_id,
            {"status": {"select": {"name": "완료"}}},
        )

    return NotionSaveResponse(
        success=True,
        decision_page_id=page["id"],
        notion_page_url=page.get("url"),
        saved_at=now,
    )


# ---------------------------------------------------------------------------
# Notion property extractors
# ---------------------------------------------------------------------------


def _extract_title(prop: dict[str, Any]) -> str:
    """Extract plain text from a Title property."""
    items = prop.get("title") or []
    return items[0]["plain_text"] if items else ""


def _extract_rich_text(prop: dict[str, Any]) -> str | None:
    """Extract plain text from a Rich Text property."""
    items = prop.get("rich_text") or []
    return items[0]["plain_text"] if items else None


def _extract_number(prop: dict[str, Any]) -> int | None:
    """Extract value from a Number property."""
    return prop.get("number")


def _extract_date(prop: dict[str, Any]) -> str | None:
    """Extract start date string from a Date property."""
    date_obj = prop.get("date")
    if date_obj is None:
        return None
    return date_obj.get("start")


def _extract_date_as_datetime(prop: dict[str, Any]) -> datetime | None:
    """Extract start date as datetime from a Date property."""
    date_str = _extract_date(prop)
    if date_str is None:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def _extract_person(prop: dict[str, Any]) -> str | None:
    """Extract first person's name from a People property."""
    people = prop.get("people") or []
    if not people:
        return None
    return people[0].get("name")


def _extract_select(prop: dict[str, Any]) -> str | None:
    """Extract name from a Select property."""
    select = prop.get("select")
    if select is None:
        return None
    return select.get("name")


# ---------------------------------------------------------------------------
# Page parsing
# ---------------------------------------------------------------------------


def _parse_deal_page(page: dict[str, Any]) -> NotionDeal:
    """Map a Notion page object to a NotionDeal schema."""
    props = page.get("properties", {})
    return NotionDeal(
        page_id=page["id"],
        deal_info=_extract_title(props.get("deal_info", {})),
        customer_name=_extract_rich_text(props.get("customer_name", {})),
        expected_amount=_extract_number(props.get("expected_amount", {})),
        deadline=_extract_date(props.get("deadline", {})),
        date=_extract_date_as_datetime(props.get("date", {})),
        author=_extract_person(props.get("author", {})),
        status=_extract_select(props.get("status", {})),
    )


def _blocks_to_text(blocks: list[dict[str, Any]]) -> str:
    """Convert Notion blocks to plain text."""
    lines: list[str] = []
    for block in blocks:
        block_type = block.get("type", "")
        data = block.get(block_type, {})
        rich_texts = data.get("rich_text") or []
        text = "".join(rt.get("plain_text", "") for rt in rich_texts)
        if text.strip():
            lines.append(text)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Decision page builders
# ---------------------------------------------------------------------------


def _build_decision_properties(
    analysis: AnalysisResult,
    deal_page_id: str | None,
    now: datetime,
) -> dict[str, Any]:
    """Build Notion properties dict for the ai decision DB page."""
    verdict_display = _VERDICT_MAP.get(analysis.verdict or "", analysis.verdict or "")

    properties: dict[str, Any] = {
        "report": {
            "title": [{"text": {"content": f"분석 결과 — {verdict_display}"}}],
        },
        "decision": {"select": {"name": verdict_display}},
        "total_score": {"number": float(analysis.total_score or 0)},
        "analysis_date": {"date": {"start": now.isoformat()}},
    }

    if deal_page_id:
        properties["deal"] = {"relation": [{"id": deal_page_id}]}

    return properties


def _markdown_to_notion_blocks(markdown: str) -> list[dict[str, Any]]:
    """Convert markdown text to a list of Notion block objects.

    Handles headings (h1–h3) and paragraphs. Long text is chunked to
    respect Notion's 2000-char rich_text limit.
    """
    blocks: list[dict[str, Any]] = []
    for line in markdown.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        block_type, text = _classify_line(stripped)
        rich_texts = _chunk_rich_text(text)
        blocks.append(
            {
                "object": "block",
                "type": block_type,
                block_type: {"rich_text": rich_texts},
            },
        )

    return blocks


def _classify_line(line: str) -> tuple[str, str]:
    """Determine Notion block type from a markdown line."""
    if line.startswith("### "):
        return "heading_3", line[4:]
    if line.startswith("## "):
        return "heading_2", line[3:]
    if line.startswith("# "):
        return "heading_1", line[2:]
    return "paragraph", line


def _chunk_rich_text(text: str) -> list[dict[str, Any]]:
    """Split text into rich_text elements respecting the 2000-char limit."""
    chunks: list[dict[str, Any]] = []
    for i in range(0, max(len(text), 1), _RICH_TEXT_LIMIT):
        chunks.append({"type": "text", "text": {"content": text[i : i + _RICH_TEXT_LIMIT]}})
    return chunks
