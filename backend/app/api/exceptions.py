import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response for OpenAPI docs."""

    detail: str


class OathKeeperError(Exception):
    """Base exception for OathKeeper."""

    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class DealNotFound(OathKeeperError):
    def __init__(self, deal_id: uuid.UUID):
        super().__init__(f"Deal {deal_id} not found", status_code=404)


class AnalysisNotFound(OathKeeperError):
    def __init__(self, deal_id: uuid.UUID):
        super().__init__(f"Analysis for deal {deal_id} not found", status_code=404)


class AnalysisInProgress(OathKeeperError):
    def __init__(self, deal_id: uuid.UUID):
        super().__init__(
            f"Analysis for deal {deal_id} is already in progress",
            status_code=409,
        )


class NotionAPIError(OathKeeperError):
    def __init__(self, detail: str = "Notion API error"):
        super().__init__(detail, status_code=502)


async def oathkeeper_exception_handler(
    request: Request,
    exc: OathKeeperError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
