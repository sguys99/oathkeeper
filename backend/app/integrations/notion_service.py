"""Notion business logic — deal listing, content parsing, analysis save."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.api.schemas.notion import NotionDeal, NotionSaveResponse
from backend.app.api.schemas.project_history import NotionProjectHistory
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


async def list_project_history() -> list[NotionProjectHistory]:
    """Fetch all projects from the Notion project history DB."""
    settings = get_settings()
    pages = await notion_client.query_database(settings.notion_project_history_db_id)
    return [_parse_project_history_page(page) for page in pages]


async def get_deal_content(page_id: str) -> str:
    """Extract plain text from a Notion deal page's properties and body blocks."""
    properties, blocks = await asyncio.gather(
        notion_client.get_page_properties(page_id),
        notion_client.get_page_content(page_id),
    )

    sections: list[str] = []

    prop_text = _properties_to_text(properties)
    if prop_text:
        sections.append(f"[딜 기본 정보]\n{prop_text}")

    body_text = _blocks_to_text(blocks)
    if body_text:
        sections.append(f"[상세 내용]\n{body_text}")

    return "\n\n".join(sections)


async def archive_decision_pages(deal_page_id: str) -> bool:
    """Archive ai decision pages linked to the deal page in Notion."""
    try:
        settings = get_settings()
        pages = await notion_client.query_database(
            settings.notion_decision_db_id,
            filter={
                "property": "deal",
                "relation": {"contains": deal_page_id},
            },
        )
        for page in pages:
            await notion_client.archive_page(page["id"])
        return True
    except Exception:
        logger.warning("Failed to archive decision pages for deal %s", deal_page_id, exc_info=True)
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


def _find_title_value(props: dict[str, Any]) -> str:
    """Find the title property by type and extract its plain text.

    Every Notion database has exactly one property with type ``"title"``.
    This helper locates it regardless of the property name, making the
    code resilient to Notion column renames.
    """
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return _extract_title(prop)
    return ""


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


def _extract_multi_select(prop: dict[str, Any]) -> list[str]:
    """Extract names from a Multi-select property."""
    items = prop.get("multi_select") or []
    return [item["name"] for item in items if "name" in item]


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


def _parse_project_history_page(page: dict[str, Any]) -> NotionProjectHistory:
    """Map a Notion page object to a NotionProjectHistory schema."""
    props = page.get("properties", {})
    return NotionProjectHistory(
        page_id=page["id"],
        project_name=_extract_rich_text(props.get("project_name", {})) or "",
        summary=_extract_title(props.get("summary", {})),
        industry=_extract_select(props.get("industry", {})),
        tech_stack=_extract_multi_select(props.get("tech_stack", {})),
        duration_months=_extract_number(props.get("duration_months", {})),
        planned_headcount=_extract_number(props.get("planned_headcount", {})),
        actual_headcount=_extract_number(props.get("actual_headcount", {})),
        contract_amount=_extract_number(props.get("contract_amount", {})),
        last_edited_time=page.get("last_edited_time"),
    )


def _properties_to_text(props: dict[str, Any]) -> str:
    """Format Notion page properties as labeled text for LLM consumption."""
    parts: list[str] = []

    title = _extract_title(props.get("deal_info", {}))
    if title:
        parts.append(f"딜 정보: {title}")

    customer = _extract_rich_text(props.get("customer_name", {}))
    if customer:
        parts.append(f"고객명: {customer}")

    amount = _extract_number(props.get("expected_amount", {}))
    if amount is not None:
        parts.append(f"예상 금액: {amount:,}")

    deadline = _extract_date(props.get("deadline", {}))
    if deadline:
        parts.append(f"납기: {deadline}")

    date = _extract_date(props.get("date", {}))
    if date:
        parts.append(f"등록일: {date}")

    author = _extract_person(props.get("author", {}))
    if author:
        parts.append(f"작성자: {author}")

    return "\n".join(parts)


def _blocks_to_text(blocks: list[dict[str, Any]], depth: int = 0) -> str:
    """Convert Notion blocks to plain text, recursively processing children."""
    lines: list[str] = []
    indent = "  " * depth
    for block in blocks:
        block_type = block.get("type", "")
        data = block.get(block_type, {})
        rich_texts = data.get("rich_text") or []
        text = "".join(rt.get("plain_text", "") for rt in rich_texts)
        if text.strip():
            lines.append(f"{indent}{text}")
        children = block.get("children", [])
        if children:
            child_text = _blocks_to_text(children, depth + 1)
            if child_text:
                lines.append(child_text)
    return "\n".join(lines)


def _rich_texts_to_markdown(rich_texts: list[dict[str, Any]]) -> str:
    """Convert Notion rich_text array to Markdown, preserving annotations."""
    parts: list[str] = []
    for rt in rich_texts:
        text = rt.get("plain_text", "")
        if not text:
            continue
        annotations = rt.get("annotations", {})
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        parts.append(text)
    return "".join(parts)


def _blocks_to_markdown(blocks: list[dict[str, Any]], depth: int = 0) -> str:
    """Convert Notion blocks to Markdown, preserving structure and annotations."""
    _LIST_TYPES = {"bulleted_list_item", "numbered_list_item", "to_do"}
    lines: list[str] = []
    indent = "  " * depth
    numbered_counter = 0
    prev_type = ""

    for block in blocks:
        block_type = block.get("type", "")
        data = block.get(block_type, {})
        rich_texts = data.get("rich_text") or []
        text = _rich_texts_to_markdown(rich_texts)

        # Insert blank line between different block groups for CommonMark separation
        if lines and not (prev_type in _LIST_TYPES and block_type in _LIST_TYPES):
            lines.append("")

        if block_type == "numbered_list_item":
            numbered_counter += 1
        else:
            numbered_counter = 0

        if block_type in ("heading_1", "heading_2", "heading_3"):
            level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[block_type]
            if text.strip():
                lines.append(f"{level} {text}")
        elif block_type == "bulleted_list_item":
            if text.strip():
                lines.append(f"{indent}- {text}")
        elif block_type == "numbered_list_item":
            if text.strip():
                lines.append(f"{indent}{numbered_counter}. {text}")
        elif block_type == "to_do":
            checked = data.get("checked", False)
            marker = "[x]" if checked else "[ ]"
            if text.strip():
                lines.append(f"{indent}- {marker} {text}")
        elif block_type == "quote":
            if text.strip():
                lines.append(f"{indent}> {text}")
        elif block_type == "code":
            language = data.get("language", "")
            lines.append(f"{indent}```{language}")
            if text:
                lines.append(f"{indent}{text}")
            lines.append(f"{indent}```")
        elif block_type == "divider":
            lines.append("---")
        elif block_type == "toggle":
            if text.strip():
                lines.append(f"{indent}**{text}**")
        else:
            if text.strip():
                lines.append(f"{indent}{text}")

        children = block.get("children", [])
        if children:
            child_text = _blocks_to_markdown(children, depth + 1)
            if child_text:
                lines.append(child_text)

        prev_type = block_type

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
