"""Tests for Pinecone vector store services."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore, _truncate

pytestmark = pytest.mark.unit

FAKE_VECTOR = [0.1] * 1536


def _make_mock_match(id_: str, score: float, metadata: dict):
    """Create a mock Pinecone match object."""
    match = MagicMock()
    match.id = id_
    match.score = score
    match.metadata = metadata
    return match


def _mock_query_response(matches):
    """Create a mock Pinecone query response."""
    resp = MagicMock()
    resp.matches = matches
    return resp


@pytest.fixture
def mock_embeddings():
    emb = MagicMock()
    emb.aembed_query = AsyncMock(return_value=FAKE_VECTOR)
    return emb


@pytest.fixture
def mock_index():
    idx = MagicMock()
    idx.upsert = MagicMock()
    idx.query = MagicMock()
    idx.delete = MagicMock()
    return idx


# ---------------------------------------------------------------------------
# _truncate
# ---------------------------------------------------------------------------


class TestTruncate:
    def test_short_text_unchanged(self):
        assert _truncate("hello", 100) == "hello"

    def test_long_text_truncated(self):
        result = _truncate("a" * 200, 100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")


# ---------------------------------------------------------------------------
# CompanyContextStore
# ---------------------------------------------------------------------------


class TestCompanyContextStore:
    @patch("backend.app.db.vector_store.get_embeddings")
    @patch("backend.app.db.vector_store.get_index")
    @patch("backend.app.db.vector_store.get_settings")
    def _make_store(self, mock_settings, mock_get_index, mock_get_emb, mock_index, mock_embeddings):
        mock_settings.return_value.pinecone_company_context_index = "test-company-context"
        mock_get_index.return_value = mock_index
        mock_get_emb.return_value = mock_embeddings
        return CompanyContextStore()

    @pytest.mark.asyncio
    async def test_upsert_calls_embed_and_pinecone(self, mock_index, mock_embeddings):
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        vec_id = await store.upsert("test content", "cost_table")

        mock_embeddings.aembed_query.assert_awaited_once_with("test content")
        mock_index.upsert.assert_called_once()
        call_kwargs = mock_index.upsert.call_args
        vectors = call_kwargs.kwargs.get("vectors") or call_kwargs[1].get("vectors")
        if vectors is None:
            vectors = call_kwargs[0][0] if call_kwargs[0] else None
        assert vectors is not None
        assert vectors[0]["id"] == vec_id
        assert vectors[0]["values"] == FAKE_VECTOR
        assert vectors[0]["metadata"]["type"] == "cost_table"
        assert vectors[0]["metadata"]["content"] == "test content"

    @pytest.mark.asyncio
    async def test_upsert_deterministic_id(self, mock_index, mock_embeddings):
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        id1 = await store.upsert("same content", "strategy")
        id2 = await store.upsert("same content", "strategy")
        id3 = await store.upsert("different content", "strategy")

        assert id1 == id2
        assert id1 != id3

    @pytest.mark.asyncio
    async def test_query_returns_formatted_results(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response(
            [
                _make_mock_match("cc-1", 0.95, {"content": "cost info", "type": "cost_table"}),
                _make_mock_match("cc-2", 0.80, {"content": "strategy info", "type": "strategy"}),
            ],
        )
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        results = await store.query("company costs")

        assert len(results) == 2
        assert results[0] == {
            "id": "cc-1",
            "score": 0.95,
            "content": "cost info",
            "type": "cost_table",
        }
        mock_embeddings.aembed_query.assert_awaited_once_with("company costs")

    @pytest.mark.asyncio
    async def test_query_with_type_filter(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response([])
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        await store.query("test", context_type="regulation")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"] == {"type": "regulation"}

    @pytest.mark.asyncio
    async def test_query_without_filter(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response([])
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        await store.query("test")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"] is None

    @pytest.mark.asyncio
    async def test_delete(self, mock_index, mock_embeddings):
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        await store.delete("cc-123")

        mock_index.delete.assert_called_once_with(ids=["cc-123"])


# ---------------------------------------------------------------------------
# ProjectHistoryStore
# ---------------------------------------------------------------------------


class TestProjectHistoryStore:
    @patch("backend.app.db.vector_store.get_embeddings")
    @patch("backend.app.db.vector_store.get_index")
    @patch("backend.app.db.vector_store.get_settings")
    def _make_store(self, mock_settings, mock_get_index, mock_get_emb, mock_index, mock_embeddings):
        mock_settings.return_value.pinecone_project_history_index = "test-project-history"
        mock_get_index.return_value = mock_index
        mock_get_emb.return_value = mock_embeddings
        return ProjectHistoryStore()

    @pytest.mark.asyncio
    async def test_upsert_project(self, mock_index, mock_embeddings):
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)
        metadata = {
            "project_name": "AI Chatbot",
            "industry": "금융",
            "tech_stack": ["FastAPI", "LangChain"],
            "scale": "medium",
            "duration_months": 6,
            "result": "success",
        }

        vec_id = await store.upsert("proj-001", "AI chatbot for banking", metadata)

        assert vec_id == "project-proj-001"
        mock_embeddings.aembed_query.assert_awaited_once_with("AI chatbot for banking")
        call_args = mock_index.upsert.call_args
        vectors = call_args.kwargs.get("vectors") or call_args[1].get("vectors")
        if vectors is None:
            vectors = call_args[0][0] if call_args[0] else None
        assert vectors[0]["metadata"]["summary"] == "AI chatbot for banking"
        assert vectors[0]["metadata"]["project_name"] == "AI Chatbot"

    @pytest.mark.asyncio
    async def test_search_similar_returns_top_k(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response(
            [
                _make_mock_match(
                    "project-1",
                    0.92345678,
                    {
                        "project_name": "Project A",
                        "industry": "금융",
                        "tech_stack": ["FastAPI"],
                        "duration_months": 3,
                        "result": "success",
                        "lessons_learned": "Good scope",
                        "scale": "small",
                        "contract_amount": 50_000_000,
                        "summary": "Banking chatbot",
                    },
                ),
                _make_mock_match(
                    "project-2",
                    0.85123456,
                    {
                        "project_name": "Project B",
                        "industry": "제조",
                        "tech_stack": ["Django"],
                        "duration_months": 6,
                        "result": "partial",
                        "lessons_learned": "Scope creep",
                        "scale": "medium",
                        "contract_amount": 100_000_000,
                        "summary": "Manufacturing MES",
                    },
                ),
            ],
        )
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        results = await store.search_similar("AI banking project")

        assert len(results) == 2
        assert results[0]["project_name"] == "Project A"
        assert results[0]["similarity_score"] == 0.9235  # rounded to 4 decimals
        assert results[1]["similarity_score"] == 0.8512
        mock_index.query.assert_called_once()
        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["top_k"] == 3  # default

    @pytest.mark.asyncio
    async def test_search_similar_with_industry_filter(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response([])
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        await store.search_similar("test deal", industry="금융")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"] == {"industry": "금융"}

    @pytest.mark.asyncio
    async def test_search_similar_empty_results(self, mock_index, mock_embeddings):
        mock_index.query.return_value = _mock_query_response([])
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        results = await store.search_similar("completely novel deal")

        assert results == []

    @pytest.mark.asyncio
    async def test_delete_project(self, mock_index, mock_embeddings):
        store = self._make_store(mock_index=mock_index, mock_embeddings=mock_embeddings)

        await store.delete("proj-001")

        mock_index.delete.assert_called_once_with(ids=["project-proj-001"])
