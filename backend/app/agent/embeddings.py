"""Embedding client factory — provider-aware LangChain Embeddings."""

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from backend.app.utils.settings import get_settings


@lru_cache
def get_embeddings() -> Embeddings:
    """Return a LangChain Embeddings instance for the configured provider.

    - ``openai``  → ``OpenAIEmbeddings``
    - ``ollama``  → ``OllamaEmbeddings`` (local via Ollama)
    """
    settings = get_settings()

    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )
