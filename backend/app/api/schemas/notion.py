from datetime import datetime

from pydantic import BaseModel

# --- deal information DB (세일즈 입력, OathKeeper 읽기) ---


class NotionDeal(BaseModel):
    """deal information DB의 한 레코드."""

    page_id: str
    deal_info: str  # Title 속성 (고객사 + 프로젝트명)
    customer_name: str | None = None
    expected_amount: int | None = None
    duration_months: int | None = None
    date: datetime | None = None
    author: str | None = None  # Person 속성에서 이름 추출
    status: str | None = None  # 미분석 / 분석중 / 완료


class NotionDealListResponse(BaseModel):
    deals: list[NotionDeal]


# --- ai decision DB (OathKeeper 저장) ---


class NotionSaveRequest(BaseModel):
    include_report: bool = True


class NotionSaveResponse(BaseModel):
    success: bool
    decision_page_id: str | None = None  # ai decision DB에 생성된 페이지 ID
    notion_page_url: str | None = None
    saved_at: datetime | None = None
