"""LLM client factory — LiteLLM router wrapping LangChain ChatModel."""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from backend.app.utils.settings import get_settings


@lru_cache
def get_llm(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Return a LangChain ChatModel backed by LiteLLM.

    LiteLLM accepts ``openai/<model>`` and ``anthropic/<model>`` prefixes,
    so we route through ``ChatOpenAI`` pointed at the LiteLLM-compatible
    interface (same OpenAI SDK shape).
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        model_name = f"openai/{settings.openai_model}"
        api_key = settings.openai_api_key
    else:
        model_name = f"anthropic/{settings.anthropic_model}"
        api_key = settings.anthropic_api_key

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        # LiteLLM acts as a drop-in proxy; we use its router via the
        # standard OpenAI SDK shape provided by langchain_openai.
    )


def get_llm_uncached(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Non-cached variant — useful when per-call params differ."""
    settings = get_settings()

    if settings.llm_provider == "openai":
        model_name = f"openai/{settings.openai_model}"
        api_key = settings.openai_api_key
    else:
        model_name = f"anthropic/{settings.anthropic_model}"
        api_key = settings.anthropic_api_key

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
