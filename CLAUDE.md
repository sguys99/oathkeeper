# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OathKeeper is a B2B AI development deal Go/No-Go decision support agent. It automatically analyzes deal information, scores opportunities against a 7-criterion framework, assesses risks, and provides strategic recommendations via Notion integration.

**Evaluation criteria:** Technical fit (20%), Profitability (20%), Resource availability (15%), Timeline risk (15%), Customer risk (10%), Requirement clarity (10%), Strategic value (10%)

## Commands

```bash
# Environment setup
make init          # Initialize production environment (Python 3.12.9)
make init-dev      # Initialize dev environment + pre-commit hooks

# Code quality
make format        # ruff check . --fix && ruff format .

# Testing
uv run pytest                          # Run unit tests (default)
uv run pytest -m integration           # Run integration tests
uv run pytest tests/path/test_file.py  # Run a single test file
uv run pytest -k "test_function_name"  # Run a specific test
```

## Architecture

**Stack:** Python 3.12.12, FastAPI, LangChain/LangGraph agents, OpenAI GPT-4o or Claude Sonnet (via LiteLLM router), Pinecone (vector DB), PostgreSQL, Next.js frontend

**Backend layout:**
- `backend/app/api/` — FastAPI routers and Pydantic schemas
- `backend/app/db/` — Database layer
- `backend/app/utils/path.py` — Project path constants (`REPO_ROOT`, `CONFIG_PATH`, etc.)
- `backend/app/utils/settings.py` — App config (loads from `.env`)
- `configs/prompts/` — Prompt templates
- `main.py` — Entry point

**Key integrations:** Notion API (deal input), Slack Webhook (notifications), Pinecone (similar project search)

## Configuration

Copy `.env.example` to `.env`. Key settings:
- `LLM_PROVIDER`: `openai` or `claude`
- `OPENAI_MODEL`: `gpt-4o`
- `ANTHROPIC_MODEL`: `claude-sonnet-4-5-20250929`

## Code Style

- Line length: 105 chars (ruff)
- Ruff rules: E, W, F, I, B, C4, UP (B008 ignored for FastAPI)
- Pre-commit hooks run ruff + trailing comma enforcement automatically
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
