from datetime import datetime

from pydantic import BaseModel


class NotionDeal(BaseModel):
    page_id: str
    title: str
    customer_name: str | None = None
    expected_amount: int | None = None
    deadline: str | None = None
    created_time: datetime | None = None


class NotionDealListResponse(BaseModel):
    deals: list[NotionDeal]


class NotionSaveRequest(BaseModel):
    include_report: bool = True


class NotionSaveResponse(BaseModel):
    success: bool
    notion_page_url: str | None = None
    saved_at: datetime | None = None
