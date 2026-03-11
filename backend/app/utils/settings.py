from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Oath Keeper"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = "postgresql+asyncpg://oathkeeper:oathkeeper@localhost:5432/oathkeeper"

    # LLM Configuration
    llm_provider: Literal["openai", "claude"] = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic Claude
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_company_context_index: str = "company-context"
    pinecone_project_history_index: str = "project-history"

    # Notion
    notion_api_key: str = ""
    notion_database_id: str = ""

    # Slack
    slack_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
