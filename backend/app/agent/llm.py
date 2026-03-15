"""LLM client factory — provider-aware LangChain ChatModel."""

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backend.app.utils.settings import get_settings


@lru_cache
def get_llm(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> BaseChatModel:
    """Return a LangChain ChatModel for the configured provider.

    - ``openai`` → ``ChatOpenAI`` (model name e.g. ``gpt-4o``)
    - ``claude`` → ``ChatAnthropic`` (model name e.g. ``claude-sonnet-4-5-20250929``)
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_llm_uncached(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> BaseChatModel:
    """Non-cached variant — useful when per-call params differ."""
    settings = get_settings()

    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
