from pydantic import BaseModel


class NotionProjectHistory(BaseModel):
    """project history DB의 한 레코드."""

    page_id: str
    project_name: str  # Title (Aa)
    summary: str | None = None  # Rich text — 임베딩 텍스트
    industry: str | None = None
    tech_stack: list[str] = []
    duration_months: int | None = None
    planned_headcount: int | None = None
    actual_headcount: int | None = None
    contract_amount: int | None = None
    is_embedded: bool = False
    needs_update: bool = False
    last_edited_time: str | None = None


class ProjectHistoryListResponse(BaseModel):
    projects: list[NotionProjectHistory]
    total: int
    embedded_count: int


class EmbedRequest(BaseModel):
    project_ids: list[str] | None = None  # None이면 미임베딩 전체 대상


class EmbedResponse(BaseModel):
    total: int
    embedded: int
    skipped: int
    failed: int
    errors: list[str] = []
