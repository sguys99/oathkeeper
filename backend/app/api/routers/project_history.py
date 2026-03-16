"""Project history router — list projects and trigger embedding."""

from fastapi import APIRouter

from backend.app.api.schemas.project_history import (
    EmbedRequest,
    EmbedResponse,
    ProjectHistoryListResponse,
)
from backend.app.services import project_history_service

router = APIRouter(prefix="/api/project-history", tags=["project-history"])


@router.get("/", response_model=ProjectHistoryListResponse)
async def list_project_history():
    """List all project history from Notion with embedding status."""
    return await project_history_service.list_projects_with_status()


@router.post("/embed", response_model=EmbedResponse)
async def embed_project_history(body: EmbedRequest | None = None):
    """Run incremental embedding for project history."""
    project_ids = body.project_ids if body else None
    return await project_history_service.embed_projects(project_ids)
