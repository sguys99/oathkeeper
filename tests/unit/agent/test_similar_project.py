"""Tests for similar_project node."""

import json
import uuid
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
    @patch("backend.app.agent.nodes.similar_project.update_log_parsed_output", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.similar_project.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.similar_project.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_logged_call, mock_update_log):
        mock_logged_call.return_value = (json.dumps(SAMPLE_SIMILAR), uuid.uuid4())

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
                "deal_id": str(uuid.uuid4()),
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
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["similar_projects"] == []

    @pytest.mark.asyncio
    async def test_empty_structured_deal_skips(self):
        project_store = AsyncMock()

        node = make_similar_project_node(project_store)
        result = await node({"structured_deal": {}, "deal_id": str(uuid.uuid4())})

        assert result["similar_projects"] == []
        project_store.search_similar.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("backend.app.agent.nodes.similar_project.logged_call_llm", new_callable=AsyncMock)
    @patch("backend.app.agent.nodes.similar_project.load_prompt")
    async def test_error_returns_empty(self, mock_load_prompt, mock_logged_call):
        mock_logged_call.side_effect = RuntimeError("LLM error")

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
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["similar_projects"] == []
        assert "similar_project" in result["errors"][0]
