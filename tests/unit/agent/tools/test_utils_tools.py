"""Unit tests for utility tools."""

import re
from datetime import UTC, datetime

import pytest

from backend.app.agent.tools.utils_tools import _format_currency, current_date

pytestmark = pytest.mark.unit


class TestFormatCurrency:
    def test_eok_and_man(self):
        assert _format_currency(15000) == "1억 5,000만원"

    def test_eok_only(self):
        assert _format_currency(50000) == "5억원"

    def test_man_only(self):
        assert _format_currency(3000) == "3,000만원"

    def test_small_amount(self):
        assert _format_currency(500) == "500만원"

    def test_zero(self):
        assert _format_currency(0) == "0원"

    def test_negative_man(self):
        assert _format_currency(-5000) == "-5,000만원"

    def test_negative_eok(self):
        assert _format_currency(-25000) == "-2억 5,000만원"

    def test_negative_eok_only(self):
        assert _format_currency(-30000) == "-3억원"

    def test_one_man(self):
        assert _format_currency(1) == "1만원"

    def test_large_amount(self):
        assert _format_currency(1000000) == "100억원"


class TestCurrentDate:
    @pytest.mark.asyncio
    async def test_returns_iso_date(self):
        result = await current_date.ainvoke({})
        assert re.match(r"\d{4}-\d{2}-\d{2}", result)

    @pytest.mark.asyncio
    async def test_returns_today(self):
        result = await current_date.ainvoke({})
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        assert result == today
