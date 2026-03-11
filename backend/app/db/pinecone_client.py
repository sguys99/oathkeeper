"""Pinecone client — singleton connection management."""

from functools import lru_cache

from pinecone import Pinecone

from backend.app.utils.settings import get_settings


@lru_cache
def get_pinecone_client() -> Pinecone:
    """Return a singleton Pinecone client instance."""
    settings = get_settings()
    return Pinecone(api_key=settings.pinecone_api_key)


def get_index(index_name: str):
    """Return a Pinecone Index handle by name."""
    client = get_pinecone_client()
    return client.Index(index_name)
