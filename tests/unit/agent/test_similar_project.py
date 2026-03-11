"""Tests for similar_project node."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.nodes.similar_project import make_similar_project_node

pytestmark = pytest.mark.unit

SAMPLE_SIMILAR = {
    "similar_projects": [
        {
            "project_name": "Project Alpha",
            "similarity_score": 0.92,
            "industry": "제조",
            "tech_stack": ["Python", "TensorFlow"],
            "duration_months": 6,
            "result": "성공",
            "lessons_learned": "초기 데이터 품질이 중요",
        },
    ],
}


class TestSimilarProjectNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.similar_project.call_llm")
    @patch("backend.app.agent.nodes.similar_project.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_call_llm):
        mock_call_llm.return_value = json.dumps(SAMPLE_SIMILAR)

        mock_tpl = MagicMock()
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        project_store = AsyncMock()
        project_store.search_similar.return_value = [
            {"project_name": "Alpha", "similarity_score": 0.92},
        ]

        node = make_similar_project_node(project_store)
        result = await node(
            {
                "structured_deal": {
                    "project_summary": "AI 품질 검사",
                    "tech_requirements": ["Python"],
                    "customer_industry": "제조",
                },
            },
        )

        assert len(result["similar_projects"]) == 1

    @pytest.mark.asyncio
    async def test_no_pinecone_results_skips_llm(self):
        project_store = AsyncMock()
        project_store.search_similar.return_value = []

        node = make_similar_project_node(project_store)
        result = await node(
            {
                "structured_deal": {
                    "project_summary": "test",
                    "tech_requirements": [],
                    "customer_industry": "IT",
                },
            },
        )

        assert result["similar_projects"] == []

    @pytest.mark.asyncio
    async def test_empty_structured_deal_skips(self):
        project_store = AsyncMock()

        node = make_similar_project_node(project_store)
        result = await node({"structured_deal": {}})

        assert result["similar_projects"] == []
        project_store.search_similar.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.similar_project.call_llm")
    @patch("backend.app.agent.nodes.similar_project.load_prompt")
    async def test_error_returns_empty(self, mock_load_prompt, mock_call_llm):
        mock_call_llm.side_effect = RuntimeError("LLM error")

        mock_tpl = MagicMock()
        mock_tpl.render.return_value = ("system", "user")
        mock_load_prompt.return_value = mock_tpl

        project_store = AsyncMock()
        project_store.search_similar.return_value = [{"project_name": "X"}]

        node = make_similar_project_node(project_store)
        result = await node(
            {
                "structured_deal": {
                    "project_summary": "test",
                    "tech_requirements": [],
                    "customer_industry": "IT",
                },
            },
        )

        assert result["similar_projects"] == []
        assert "similar_project" in result["errors"][0]
