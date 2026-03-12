"""Notion API client — singleton connection and low-level operations."""

from __future__ import annotations

import uuid as _uuid
from functools import lru_cache
from typing import Any

from notion_client import AsyncClient

from backend.app.utils.settings import get_settings


def _normalize_id(raw_id: str) -> str:
    """Ensure a Notion ID is in hyphenated UUID format."""
    try:
        return str(_uuid.UUID(raw_id))
    except ValueError:
        return raw_id


@lru_cache
def get_notion_client() -> AsyncClient:
    """Return a singleton async Notion client instance."""
    settings = get_settings()
    return AsyncClient(auth=settings.notion_api_key, notion_version="2022-06-28")


async def query_database(
    database_id: str,
    filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query a Notion database, handling pagination internally."""
    client = get_notion_client()
    db_id = _normalize_id(database_id)
    results: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        body: dict[str, Any] = {}
        if filter:
            body["filter"] = filter
        if cursor:
            body["start_cursor"] = cursor
        response = await client.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body=body,
        )
        results.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return results


async def get_page_content(page_id: str) -> list[dict[str, Any]]:
    """Retrieve all block children (page body) for a given page."""
    client = get_notion_client()
    normalized_page_id = _normalize_id(page_id)
    blocks: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        kwargs: dict[str, Any] = {"block_id": normalized_page_id}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = await client.blocks.children.list(**kwargs)
        blocks.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return blocks


async def create_page(
    parent_database_id: str,
    properties: dict[str, Any],
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a new page in a Notion database."""
    client = get_notion_client()
    payload: dict[str, Any] = {
        "parent": {"database_id": _normalize_id(parent_database_id)},
        "properties": properties,
    }
    if children:
        payload["children"] = children
    return await client.pages.create(**payload)


async def update_page_property(
    page_id: str,
    properties: dict[str, Any],
) -> dict[str, Any]:
    """Update properties on an existing Notion page."""
    client = get_notion_client()
    return await client.pages.update(page_id=_normalize_id(page_id), properties=properties)
