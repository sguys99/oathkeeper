"""Integration tests for Pinecone vector stores.

Requires PINECONE_API_KEY in environment and existing indexes.
Run with: uv run pytest -m integration tests/integration/test_pinecone.py -v
"""

import asyncio
import uuid

import pytest

from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

# Unique namespace suffix to isolate test data
_TEST_SUFFIX = uuid.uuid4().hex[:8]


@pytest.fixture
def company_store():
    return CompanyContextStore()


@pytest.fixture
def project_store():
    return ProjectHistoryStore()


class TestCompanyContextIntegration:
    async def test_roundtrip(self, company_store):
        """Upsert a document, query it back, then delete."""
        content = f"[test-{_TEST_SUFFIX}] 개발자 월 단가 1,200만원, 시니어 1,800만원"

        # Upsert
        vec_id = await company_store.upsert(content, "cost_table")
        assert vec_id.startswith("company-context-")

        # Query
        results = await company_store.query("개발자 단가", top_k=3, context_type="cost_table")
        assert any(r["id"] == vec_id for r in results)
        matched = next(r for r in results if r["id"] == vec_id)
        assert "1,200만원" in matched["content"]

        # Cleanup
        await company_store.delete(vec_id)


class TestProjectHistoryIntegration:
    async def test_roundtrip(self, project_store):
        """Upsert a project, search for it, then delete."""
        project_id = f"test-{_TEST_SUFFIX}"
        summary = "금융권 AI 챗봇 개발 프로젝트, FastAPI + LangChain 기반"
        metadata = {
            "project_name": f"Test Project {_TEST_SUFFIX}",
            "industry": "금융",
            "tech_stack": ["FastAPI", "LangChain", "GPT-4o"],
            "scale": "medium",
            "duration_months": 4,
            "planned_headcount": 3,
            "actual_headcount": 4,
            "result": "success",
            "lessons_learned": "스코프 관리가 핵심",
            "contract_amount": 80_000_000,
        }

        # Upsert
        vec_id = await project_store.upsert(project_id, summary, metadata)
        assert vec_id == f"project-{project_id}"

        # Search
        results = await project_store.search_similar("금융 AI 챗봇 프로젝트", top_k=3)
        assert len(results) > 0
        assert any(r["project_name"] == metadata["project_name"] for r in results)

        # Cleanup
        await project_store.delete(project_id)

    async def test_similarity_relevance(self, project_store):
        """Verify that a matching project scores higher than unrelated ones."""
        ids = []
        try:
            # Upsert related project
            related_id = f"related-{_TEST_SUFFIX}"
            await project_store.upsert(
                related_id,
                "금융 보험사 AI 상담 시스템 개발",
                {"project_name": "Insurance AI", "industry": "금융", "result": "success"},
            )
            ids.append(related_id)

            # Upsert unrelated project
            unrelated_id = f"unrelated-{_TEST_SUFFIX}"
            await project_store.upsert(
                unrelated_id,
                "제조 공장 MES 시스템 구축, PLC 연동",
                {"project_name": "Factory MES", "industry": "제조", "result": "success"},
            )
            ids.append(unrelated_id)

            # Wait for Pinecone to index the vectors (eventual consistency)
            await asyncio.sleep(2)

            # Search for finance-related deal
            results = await project_store.search_similar("금융권 AI 고객 상담 자동화", top_k=5)
            names = [r["project_name"] for r in results]

            if "Insurance AI" in names and "Factory MES" in names:
                ins_idx = names.index("Insurance AI")
                fac_idx = names.index("Factory MES")
                assert ins_idx < fac_idx, "Related project should rank higher"
        finally:
            for pid in ids:
                await project_store.delete(pid)
