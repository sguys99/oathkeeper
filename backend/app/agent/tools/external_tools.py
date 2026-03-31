"""External tools — web search and Notion integration."""

import json
import logging

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.app.utils.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# web_search
# ---------------------------------------------------------------------------


class WebSearchInput(BaseModel):
    """Search the web for market, technology, or competitor information."""

    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Maximum results to return", ge=1, le=10)


@tool(args_schema=WebSearchInput)
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for market trends, technology information, competitor data,
    or industry analysis relevant to deal evaluation."""
    settings = get_settings()
    if not settings.tavily_api_key:
        return json.dumps({"error": "Web search not configured (no API key)"})

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        response = await client.search(query=query, max_results=max_results)
        results = [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in response.get("results", [])
        ]
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.exception("web_search failed")
        return json.dumps({"error": f"Web search failed: {e}"})


# ---------------------------------------------------------------------------
# fetch_notion_deal
# ---------------------------------------------------------------------------


class FetchNotionDealInput(BaseModel):
    """Fetch deal details from a Notion page."""

    page_id: str = Field(description="Notion page ID")


@tool(args_schema=FetchNotionDealInput)
async def fetch_notion_deal(page_id: str) -> str:
    """Fetch the full content of a deal from Notion, including properties and body text."""
    try:
        from backend.app.integrations.notion_service import get_deal_content

        content = await get_deal_content(page_id)
        return content
    except Exception as e:
        logger.exception("fetch_notion_deal failed")
        return json.dumps({"error": f"Notion fetch failed: {e}"})
