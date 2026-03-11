"""Tests for agent base utilities."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.base import (
    call_llm,
    format_company_context,
    format_scoring_criteria,
    format_team_members,
    parse_json_response,
)

pytestmark = pytest.mark.unit


class TestParseJsonResponse:
    def test_direct_json(self):
        raw = '{"key": "value", "num": 42}'
        assert parse_json_response(raw) == {"key": "value", "num": 42}

    def test_json_in_code_fence(self):
        raw = 'Some text\n```json\n{"key": "value"}\n```\nMore text'
        assert parse_json_response(raw) == {"key": "value"}

    def test_json_in_bare_code_fence(self):
        raw = '```\n{"key": "value"}\n```'
        assert parse_json_response(raw) == {"key": "value"}

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_json_response("not json at all")

    def test_whitespace_wrapped_json(self):
        raw = '  \n  {"a": 1}  \n  '
        assert parse_json_response(raw) == {"a": 1}

    def test_nested_json(self):
        data = {"scores": [{"criterion": "tech", "score": 80}], "total": 80}
        raw = f"```json\n{json.dumps(data)}\n```"
        assert parse_json_response(raw) == data


class TestCallLlm:
    @pytest.mark.asyncio
    async def test_calls_llm_with_messages(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="response text")

        result = await call_llm("system msg", "user msg", llm=mock_llm)

        assert result == "response text"
        mock_llm.ainvoke.assert_awaited_once()
        messages = mock_llm.ainvoke.call_args[0][0]
        assert len(messages) == 2
        assert messages[0].content == "system msg"
        assert messages[1].content == "user msg"

    @pytest.mark.asyncio
    @patch("backend.app.agent.base.get_llm")
    async def test_uses_default_llm(self, mock_get_llm):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="ok")
        mock_get_llm.return_value = mock_llm

        result = await call_llm("sys", "usr")

        assert result == "ok"
        mock_get_llm.assert_called_once()


class TestFormatScoringCriteria:
    def test_converts_orm_objects(self):
        criteria = [
            MagicMock(name="Technical Fit", weight=0.20, description="Tech match"),
            MagicMock(name="Profitability", weight=0.20, description="Margin"),
        ]
        # MagicMock overrides .name, need to set it explicitly
        criteria[0].name = "Technical Fit"
        criteria[1].name = "Profitability"

        result = format_scoring_criteria(criteria)

        assert len(result) == 2
        assert result[0] == {"name": "Technical Fit", "weight": 0.20, "description": "Tech match"}
        assert result[1]["weight"] == 0.20

    def test_empty_list(self):
        assert format_scoring_criteria([]) == []


class TestFormatTeamMembers:
    def test_converts_orm_objects(self):
        member = MagicMock(
            role="BE",
            monthly_rate=8000000,
            is_available=True,
            current_project=None,
            available_from=None,
        )
        member.name = "Kim"

        result = format_team_members([member])

        assert len(result) == 1
        assert result[0]["name"] == "Kim"
        assert result[0]["monthly_rate"] == 8000000
        assert result[0]["is_available"] is True


class TestFormatCompanyContext:
    def test_formats_results(self):
        results = [
            {"type": "strategy", "content": "AI focus"},
            {"type": "tech_stack", "content": "Python, React"},
        ]
        text = format_company_context(results)
        assert "[strategy] AI focus" in text
        assert "[tech_stack] Python, React" in text

    def test_empty_results(self):
        assert format_company_context([]) == ""
