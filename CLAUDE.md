# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OathKeeper is a B2B AI development deal Go/No-Go decision support agent. It automatically analyzes deal information, scores opportunities against a 7-criterion framework, assesses risks, and provides strategic recommendations via Notion integration.

**Evaluation criteria:** Technical fit (20%), Profitability (20%), Resource availability (15%), Timeline risk (15%), Customer risk (10%), Requirement clarity (10%), Strategic value (10%)

**Implementation status:** Most code is still stubs/planning phase. Only `backend/app/utils/path.py` and `backend/app/utils/settings.py` have non-trivial content. Use `docs/task-plan.md` (9-phase roadmap) and `docs/PRD.md` as authoritative references.

## Commands

```bash
# Environment setup
make init          # Initialize production environment (Python 3.12.12)
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

**Stack:** Python 3.12.12, FastAPI, LangChain/LangGraph agents, OpenAI GPT-4o or Claude Sonnet (via LiteLLM router), Pinecone (vector DB), PostgreSQL, Next.js 15 frontend

**Backend layout:**
- `backend/app/api/` — FastAPI routers and Pydantic schemas
- `backend/app/agent/` — LangGraph nodes, graph orchestration, LLM client
- `backend/app/db/` — SQLAlchemy ORM models, CRUD repositories, Pinecone client
- `backend/app/integrations/` — Notion API client, Slack webhook
- `backend/app/utils/path.py` — Project path constants (`REPO_ROOT`, `CONFIG_PATH`, etc.)
- `backend/app/utils/settings.py` — App config (loads from `.env`)
- `configs/prompts/` — YAML prompt templates (rendered with Jinja2 at runtime)
- `main.py` — Entry point (uvicorn)

**Key integrations:** Notion API (deal input + result save), Slack Webhook (completion notifications), Pinecone (similar project search)

## LangGraph Agent Flow

The core analysis pipeline is a LangGraph graph in `backend/app/agent/graph.py`:

```
deal_structuring_node
        ↓
[scoring_node, resource_estimation_node, risk_analysis_node, similar_project_node]  ← parallel
        ↓
final_verdict_node
```

Each node is a separate class in `backend/app/agent/nodes/`. The shared `AgentState` (TypedDict in `backend/app/agent/state.py`) holds:
- `deal_input` → `structured_deal` → `scores`, `resource_estimate`, `risks`, `similar_projects` → `final_report`
- `status` and `errors` for tracking

Conditional branching: if `structured_deal.missing_fields` exceeds threshold → short-circuit to Hold verdict.

**Verdict thresholds:** Go ≥ 70, Conditional Go 40–69, No-Go < 40, Hold (missing critical fields)

## Prompt Template System

Prompts live in `configs/prompts/` as YAML files (`deal_structuring.yaml`, `scoring.yaml`, etc.) loaded by `backend/app/agent/prompt_loader.py` using Jinja2. Variables injected at runtime include `company_context`, `company_rates`, `team_members`, and `past_projects` from the DB.

## Data Persistence

- **PostgreSQL** for structured data: deals, analysis results (scores/risks/estimates stored as JSONB), users, scoring criteria config, team member rates
- **Pinecone** vector store: company context embeddings + past project embeddings (Top-3 similarity search for `similar_project_node`)
- **Alembic** for schema migrations (`migrations/`)

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
