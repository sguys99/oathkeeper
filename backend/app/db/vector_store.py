"""Vector store services — Pinecone-backed company context and project history."""

import hashlib
from datetime import UTC, datetime
from typing import Literal

from backend.app.agent.embeddings import get_embeddings
from backend.app.db.pinecone_client import get_index
from backend.app.utils.settings import get_settings

ContextType = Literal["cost_table", "strategy", "regulation", "tech_stack"]

MAX_METADATA_CHARS = 10_000


def _truncate(text: str, max_chars: int = MAX_METADATA_CHARS) -> str:
    """Truncate text to stay within Pinecone metadata size limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


class CompanyContextStore:
    """Store and retrieve company context documents via Pinecone.

    Index: company-context (dimension per settings.embedding_dimensions, cosine similarity)
    Metadata: type, content, updated_at
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._index = get_index(settings.pinecone_company_context_index)
        self._embeddings = get_embeddings()

    def _make_id(self, content: str) -> str:
        """Deterministic ID from content hash for natural deduplication."""
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"company-context-{h}"

    async def upsert(self, content: str, context_type: ContextType) -> str:
        """Embed and upsert a company context document. Returns the vector ID."""
        vector = await self._embeddings.aembed_query(content)
        vec_id = self._make_id(content)
        self._index.upsert(
            vectors=[
                {
                    "id": vec_id,
                    "values": vector,
                    "metadata": {
                        "type": context_type,
                        "content": _truncate(content),
                        "updated_at": datetime.now(UTC).isoformat(),
                    },
                },
            ],
        )
        return vec_id

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        context_type: ContextType | None = None,
    ) -> list[dict]:
        """Search for relevant company context.

        Returns list of {id, score, content, type}.
        """
        vector = await self._embeddings.aembed_query(query_text)
        filter_dict = {"type": context_type} if context_type else None
        results = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )
        return [
            {
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "type": match.metadata.get("type", ""),
            }
            for match in results.matches
        ]

    async def delete(self, vec_id: str) -> None:
        """Delete a vector by ID."""
        self._index.delete(ids=[vec_id])


class ProjectHistoryStore:
    """Store and search similar past projects via Pinecone.

    Index: project-history (dimension per settings.embedding_dimensions, cosine similarity)
    Metadata: project_name, industry, tech_stack, duration_months,
              planned_headcount, actual_headcount, contract_amount, summary,
              embedded_at, notion_last_edited
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._index = get_index(settings.pinecone_project_history_index)
        self._embeddings = get_embeddings()

    async def upsert(
        self,
        project_id: str,
        summary: str,
        metadata: dict,
        notion_last_edited: str | None = None,
    ) -> str:
        """Embed project summary and upsert with full metadata.

        Args:
            project_id: Unique project identifier.
            summary: Text summary used for embedding.
            metadata: Dict with project_name, industry, tech_stack,
                      duration_months, planned_headcount, actual_headcount,
                      contract_amount.
            notion_last_edited: Notion page last_edited_time for change tracking.

        Returns:
            The Pinecone vector ID.
        """
        vector = await self._embeddings.aembed_query(summary)
        vec_id = f"project-{project_id}"
        meta = {**metadata, "summary": _truncate(summary)}
        meta["embedded_at"] = datetime.now(UTC).isoformat()
        if notion_last_edited:
            meta["notion_last_edited"] = notion_last_edited
        self._index.upsert(vectors=[{"id": vec_id, "values": vector, "metadata": meta}])
        return vec_id

    def fetch_existing(self, project_ids: list[str]) -> dict[str, dict]:
        """Fetch existing vectors by project IDs.

        Returns:
            Dict mapping vector ID to its metadata.
        """
        vec_ids = [f"project-{pid}" for pid in project_ids]
        result = self._index.fetch(ids=vec_ids)
        return {vid: v.metadata for vid, v in result.vectors.items()}

    async def search_similar(
        self,
        deal_text: str,
        top_k: int = 3,
        industry: str | None = None,
    ) -> list[dict]:
        """Find similar past projects by cosine similarity.

        Args:
            deal_text: Concatenated deal description for embedding.
            top_k: Number of results (default 3 per PRD).
            industry: Optional filter to narrow by industry.

        Returns:
            List of dicts compatible with SimilarProject schema and
            similar_project.yaml prompt template.
        """
        vector = await self._embeddings.aembed_query(deal_text)
        filter_dict = {"industry": industry} if industry else None
        results = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )
        return [
            {
                "project_name": match.metadata.get("project_name", ""),
                "similarity_score": round(match.score, 4),
                "industry": match.metadata.get("industry", ""),
                "tech_stack": match.metadata.get("tech_stack", []),
                "duration_months": match.metadata.get("duration_months", 0),
                "planned_headcount": match.metadata.get("planned_headcount", 0),
                "actual_headcount": match.metadata.get("actual_headcount", 0),
                "contract_amount": match.metadata.get("contract_amount", 0),
                "summary": match.metadata.get("summary", ""),
            }
            for match in results.matches
        ]

    async def delete(self, project_id: str) -> None:
        """Delete a project vector by ID."""
        self._index.delete(ids=[f"project-{project_id}"])
