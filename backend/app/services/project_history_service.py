"""Project history service — Notion sync and Pinecone embedding."""

from __future__ import annotations

import logging

from backend.app.api.schemas.project_history import (
    EmbedResponse,
    NotionProjectHistory,
    ProjectHistoryListResponse,
)
from backend.app.db.vector_store import ProjectHistoryStore
from backend.app.integrations import notion_service

logger = logging.getLogger(__name__)


async def list_projects_with_status() -> ProjectHistoryListResponse:
    """List all projects from Notion with embedding status from Pinecone."""
    projects = await notion_service.list_project_history()

    if not projects:
        return ProjectHistoryListResponse(projects=[], total=0, embedded_count=0)

    store = ProjectHistoryStore()
    page_ids = [p.page_id for p in projects]
    existing = store.fetch_existing(page_ids)

    enriched: list[NotionProjectHistory] = []
    embedded_count = 0

    for project in projects:
        vec_id = f"project-{project.page_id}"
        meta = existing.get(vec_id)

        if meta:
            embedded_count += 1
            project.is_embedded = True
            stored_edited = meta.get("notion_last_edited", "")
            project.needs_update = (
                project.last_edited_time is not None and stored_edited != project.last_edited_time
            )
        else:
            project.is_embedded = False
            project.needs_update = False

        enriched.append(project)

    return ProjectHistoryListResponse(
        projects=enriched,
        total=len(enriched),
        embedded_count=embedded_count,
    )


async def get_page_content(page_id: str) -> str:
    """Fetch the body content of a Notion project history page as plain text."""
    from backend.app.integrations import notion_client
    from backend.app.integrations.notion_service import _blocks_to_text

    blocks = await notion_client.get_page_content(page_id)
    return _blocks_to_text(blocks)


async def delete_embedding(page_id: str) -> None:
    """Delete a project embedding from Pinecone."""
    store = ProjectHistoryStore()
    await store.delete(page_id)


async def embed_projects(project_ids: list[str] | None = None) -> EmbedResponse:
    """Embed project history into Pinecone with incremental logic."""
    projects = await notion_service.list_project_history()

    if project_ids is not None:
        id_set = set(project_ids)
        projects = [p for p in projects if p.page_id in id_set]

    if not projects:
        return EmbedResponse(total=0, embedded=0, skipped=0, failed=0)

    store = ProjectHistoryStore()
    page_ids = [p.page_id for p in projects]
    existing = store.fetch_existing(page_ids)

    embedded = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for project in projects:
        vec_id = f"project-{project.page_id}"
        meta = existing.get(vec_id)

        # Skip if already embedded and not updated in Notion
        if meta:
            stored_edited = meta.get("notion_last_edited", "")
            if stored_edited == project.last_edited_time:
                skipped += 1
                continue

        if not project.summary:
            skipped += 1
            continue

        try:
            page_content = await get_page_content(project.page_id)
            embed_text = project.summary
            if page_content:
                embed_text = f"{project.summary}\n\n{page_content}"

            metadata = {
                "project_name": project.project_name or "",
                "industry": project.industry or "",
                "tech_stack": project.tech_stack,
                "duration_months": project.duration_months or 0,
                "planned_headcount": project.planned_headcount or 0,
                "actual_headcount": project.actual_headcount or 0,
                "contract_amount": project.contract_amount or 0,
            }
            await store.upsert(
                project_id=project.page_id,
                summary=embed_text,
                metadata=metadata,
                notion_last_edited=project.last_edited_time,
            )
            embedded += 1
        except Exception as exc:
            failed += 1
            msg = f"{project.project_name}: {exc}"
            errors.append(msg)
            logger.warning("Failed to embed project %s: %s", project.page_id, exc)

    return EmbedResponse(
        total=len(projects),
        embedded=embedded,
        skipped=skipped,
        failed=failed,
        errors=errors,
    )
