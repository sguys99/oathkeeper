# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OathKeeper is a B2B AI development deal Go/No-Go decision support agent. It analyzes deal information, scores opportunities against a 7-criterion framework, assesses risks, and provides strategic recommendations via Notion integration.

**Evaluation criteria:** Technical fit (20%), Profitability (20%), Resource availability (15%), Timeline risk (15%), Customer risk (10%), Requirement clarity (10%), Strategic value (10%)

**Verdict thresholds:** Go ≥ 70, Conditional Go 40–69, No-Go < 40, Hold (≥3 critical fields missing)

**Deal status flow:** pending → analyzing → completed (or failed)

## Commands

```bash
# Environment setup
make init          # Initialize production environment (Python 3.12.12)
make init-dev      # Initialize dev environment (Python 3.12.12) + pre-commit hooks

# Development
make run           # Start FastAPI server (uvicorn via main.py)
make format        # ruff check . --fix && ruff format . (requires venv activated)
make docker-up     # Start PostgreSQL container
make docker-down   # Stop PostgreSQL container
make migrate       # Run Alembic migrations (alembic upgrade head)
make seed          # Insert seed data (scoring criteria, company settings, team members)

# Testing (default runs unit tests only)
make test                              # Unit tests (default via -m unit)
make test-integration                  # Integration tests (require API keys)
make test-e2e                          # E2E tests (require running services, --timeout=200)
uv run pytest tests/path/test_file.py  # Single test file
uv run pytest -k "test_function_name"  # Single test function

# Production deployment
make docker-build     # Build production Docker images
make docker-prod-up   # Start all production services
make docker-prod-down # Stop all production services

# Frontend (run from frontend/)
npm run dev            # Start Next.js dev server (port 3000)
npm run build          # Production build
npm run test:e2e       # Run Playwright E2E tests
npm run test:e2e:ui    # Run Playwright E2E tests with UI
```

## Architecture

**Stack:** Python 3.12.12, FastAPI, LangGraph, LiteLLM (OpenAI GPT-4o / Claude Sonnet routing), Pinecone, PostgreSQL (async via SQLAlchemy + asyncpg), Next.js 16 + shadcn/ui frontend

### Backend (`backend/app/`)

- `api/main.py` — FastAPI app factory with CORS, exception handlers, structlog middleware
- `api/routers/` — 8 routers: `deals`, `analysis`, `settings`, `users`, `notion`, `agent_logs`, `prompts`, `project_history`
- `api/schemas/` — Pydantic request/response models
- `api/exceptions.py` — Custom exceptions (`DealNotFound`, `AnalysisInProgress`, etc.)
- `agent/graph.py` — LangGraph StateGraph orchestration (see flow below)
- `agent/nodes/` — 6 node factories (factory function → async node) + inline `hold_verdict_node` in `graph.py`
- `agent/base.py` — Shared utilities (`call_llm`, `logged_call_llm`, `parse_json_response`, `MISSING_FIELDS_THRESHOLD`)
- `agent/state.py` — `AgentState` TypedDict shared across nodes
- `agent/llm.py` — LiteLLM-backed LLM factory (routes to `openai/gpt-4o` or `anthropic/claude-sonnet`)
- `agent/embeddings.py` — Embedding client for vector operations
- `agent/prompt_loader.py` — Jinja2-based YAML prompt renderer
- `agent/service.py` — High-level service tying graph execution to DB persistence
- `db/models/` — 9 SQLAlchemy models: `Deal`, `AnalysisResult`, `ScoringCriteria`, `CompanySetting`, `TeamMember`, `User`, `AgentLog`, `CostItem`
- `db/repositories/` — Async CRUD repos: `deal_repo`, `analysis_repo`, `settings_repo`, `user_repo`, `agent_log_repo`
- `db/vector_store.py` — `CompanyContextStore` and `ProjectHistoryStore` (Pinecone wrappers)
- `db/seed.py` — Default scoring criteria, company settings, team member data
- `db/defaults_loader.py` — YAML-based defaults loading from `configs/defaults/`
- `db/pinecone_client.py` — Pinecone client initialization
- `services/project_history_service.py` — Project history business logic
- `integrations/notion_client.py` — Low-level Notion API operations
- `integrations/notion_service.py` — High-level Notion deal sync and result saving
- `integrations/slack_client.py` — Slack webhook notifications
- `utils/settings.py` — Pydantic BaseSettings (loads `.env`)
- `utils/path.py` — Path constants (`REPO_ROOT`, `CONFIG_PATH`, etc.)
- `utils/logging.py` — structlog + Sentry setup
- `utils/file_parser.py` — Word/PDF text extraction (20MB limit)

### LangGraph Agent Flow (`agent/graph.py`)

```
deal_structuring_node
        ↓
should_continue_or_hold (conditional)
    ├── Hold (≥3 missing fields) → hold_verdict_node → END
    └── Continue:
           ↓
        [parallel execution]
        ├── scoring_node
        ├── resource_estimation_node
        ├── risk_analysis_node
        └── similar_project_node
           ↓
        final_verdict_node → END
```

`AgentState` flows: `deal_input` → `structured_deal` → `scores`, `resource_estimate`, `risks`, `similar_projects` → `final_report`

### Prompt Templates (`configs/prompts/`)

7 YAML files (`system.yaml`, `deal_structuring.yaml`, `scoring.yaml`, `resource_estimation.yaml`, `risk_analysis.yaml`, `similar_project.yaml`, `final_verdict.yaml`) loaded by `prompt_loader.py` with Jinja2. Runtime variables include `company_context`, `company_rates`, `team_members`, `past_projects`.

### Frontend (`frontend/src/`)

- **Next.js 16 App Router** with TailwindCSS v4, shadcn/ui, React Query
- `/` — Deal input page (Notion selector, text input, file upload, SSE progress)
- `/deals` — Dashboard with search, filters, pagination
- `/deals/[id]` — Analysis results (radar chart, scores, resources, risks, similar projects, recommendations)
- `/deals/[id]/logs` — Agent execution log viewer per deal
- `/admin` — 5-tab settings (company info, scoring weights, team management, cost settings, project history)
- `/agent-settings` — Agent configuration and prompt management
- `/agent-logs` — Agent execution log viewer (all deals)
- `lib/api/` — Typed fetch-based API client (email-based auth via `X-User-Email` header, no JWT)
- `hooks/` — React Query hooks (`use-deals`, `use-analysis`, `use-settings`, `use-notion`, `use-agent-logs`, `use-prompts`)

### Data Persistence

- **PostgreSQL:** Deals, analysis results (JSONB for scores/risks/estimates), users, scoring criteria, company settings, team members
- **Pinecone:** Company context embeddings + past project embeddings (Top-3 cosine similarity)
- **Alembic:** Schema migrations in `backend/app/db/migrations/`

### Key DB Relationships

- `Deal` ← FK → `User` (created_by)
- `Deal` → 1:1 → `AnalysisResult`
- `Deal` → 1:many → `AgentLog` (cascade delete)

## API Endpoints

- `POST /api/deals/` — Create deal
- `GET /api/deals/` — List deals (filters: status, created_by, pagination)
- `GET /api/deals/{id}` — Get deal
- `POST /api/deals/{id}/upload` — Upload Word/PDF document
- `POST /api/deals/{id}/analyze` — Trigger analysis (returns 202, runs in background)
- `GET /api/deals/{id}/analysis` — Get analysis result
- `GET /api/deals/{id}/status` — SSE stream for analysis progress
- `GET /api/notion/deals` — List deals from Notion
- `POST /api/notion/{deal_id}/save-to-notion` — Save analysis to Notion
- `/api/settings/` — CRUD for scoring criteria, company settings, team members, costs
- `/api/users/` — User CRUD
- `GET /api/agent-logs/{deal_id}` — Agent execution logs for a deal
- `GET /api/prompts/` — List prompt templates
- `PUT /api/prompts/{name}` — Update a prompt template
- `GET /health` — Health check

## Configuration

Copy `.env.example` to `.env`. Key settings: `LLM_PROVIDER` (`openai`/`claude`), API keys for OpenAI/Anthropic/Pinecone/Notion, `SLACK_WEBHOOK_URL`, `DATABASE_URL`, `SENTRY_DSN`.

## Code Style

- Line length: 105 chars (ruff)
- Ruff rules: E, W, F, I, B, C4, UP (B008 ignored for FastAPI)
- isort: first-party = `app`
- Pre-commit hooks: ruff + trailing comma enforcement
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
- Unit tests use SQLite in-memory; integration tests require real services
- README and docs are in Korean
