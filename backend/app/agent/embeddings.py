"""Embedding client — OpenAI text-embedding-3-small via LangChain."""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from backend.app.utils.settings import get_settings


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    """Return a LangChain OpenAIEmbeddings instance.

    Used by Phase 4 (Pinecone vector store) for upsert and query operations.
    """
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )
