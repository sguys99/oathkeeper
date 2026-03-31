"""Utility tools — formatting and date helpers."""

from datetime import UTC, datetime

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# format_currency
# ---------------------------------------------------------------------------


class FormatCurrencyInput(BaseModel):
    """Format a number as Korean currency."""

    amount: int = Field(description="Amount in 만원")


def _format_currency(amount: int) -> str:
    if amount == 0:
        return "0원"

    negative = amount < 0
    abs_amount = abs(amount)
    prefix = "-" if negative else ""

    eok = abs_amount // 10000
    man = abs_amount % 10000

    if eok > 0 and man > 0:
        return f"{prefix}{eok}억 {man:,}만원"
    elif eok > 0:
        return f"{prefix}{eok}억원"
    else:
        return f"{prefix}{man:,}만원"


@tool(args_schema=FormatCurrencyInput)
async def format_currency(amount: int) -> str:
    """Convert amount in 만원 to human-readable Korean currency (e.g., 15000 -> 1억 5,000만원)."""
    return _format_currency(amount)


# ---------------------------------------------------------------------------
# current_date
# ---------------------------------------------------------------------------


@tool
async def current_date() -> str:
    """Return the current date in YYYY-MM-DD format."""
    return datetime.now(UTC).strftime("%Y-%m-%d")
