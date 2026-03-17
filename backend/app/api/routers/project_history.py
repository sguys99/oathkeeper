"""Project history router — list projects and trigger embedding."""

from fastapi import APIRouter

from backend.app.api.schemas.project_history import (
    EmbedRequest,
    EmbedResponse,
    PageContentResponse,
    ProjectHistoryListResponse,
)
from backend.app.services import project_history_service

router = APIRouter(prefix="/api/project-history", tags=["project-history"])


@router.get("/", response_model=ProjectHistoryListResponse)
async def list_project_history():
    """List all project history from Notion with embedding status."""
    return await project_history_service.list_projects_with_status()


@router.get("/{page_id}/content", response_model=PageContentResponse)
async def get_page_content(page_id: str):
    """Get the body content of a Notion project history page."""
    content = await project_history_service.get_page_content(page_id)
    return PageContentResponse(content=content)


@router.delete("/{page_id}/embedding", status_code=204)
async def delete_embedding(page_id: str):
    """Delete embedding for a project from Pinecone."""
    await project_history_service.delete_embedding(page_id)


@router.post("/embed", response_model=EmbedResponse)
async def embed_project_history(body: EmbedRequest | None = None):
    """Run incremental embedding for project history."""
    project_ids = body.project_ids if body else None
    return await project_history_service.embed_projects(project_ids)
