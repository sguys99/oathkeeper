# Repository Guidelines

## Project Structure & Module Organization
`backend/app` contains the FastAPI service, LangGraph agent, database models/repositories, and external integrations. Prompt templates live in `configs/prompts`, defaults in `configs/defaults`, and Alembic migrations in `backend/app/db/migrations`. The Next.js app lives in `frontend/src`, with route files under `src/app`, shared UI in `src/components`, hooks in `src/hooks`, and API clients in `src/lib/api`. Tests are organized by scope in `tests/unit`, `tests/integration`, `tests/e2e`, plus frontend Playwright specs in `frontend/e2e`.

## Build, Test, and Development Commands
Backend setup uses `uv` and the root `Makefile`.

- `make init-dev`: create `.venv`, install dev dependencies, and register `pre-commit`.
- `make docker-up`: start local infrastructure from `docker-compose.yaml`.
- `make migrate` / `make seed`: apply Alembic migrations and load seed data.
- `make run`: start the FastAPI app through `main.py`.
- `make test`: run the default pytest suite (`-m unit` from `pyproject.toml`).
- `make test-integration` and `make test-e2e`: run broader backend suites.
- `cd frontend && npm run dev|build|test:e2e`: run the Next.js app, production build, or Playwright tests.

## Coding Style & Naming Conventions
Python targets 3.12 and uses Ruff for linting and formatting: run `make format` before submitting backend changes. Follow 4-space indentation, double quotes, and the configured 105-character line limit. Keep Python modules `snake_case`; classes, Pydantic schemas, and SQLAlchemy models use `PascalCase`.

TypeScript/React files in `frontend/src` follow the existing pattern: components and providers use `kebab-case` filenames exporting `PascalCase` symbols, hooks are `use-*.ts`, and route-local helpers belong in `_components`.

## Testing Guidelines
Name tests `test_*.py` and place them in the matching scope directory. Unit tests should stay isolated from external services; integration and e2e tests may require database containers, API keys, or running servers. Use pytest markers explicitly when needed, for example `uv run pytest -m integration -v`.

## Commit & Pull Request Guidelines
Recent history uses short, imperative subjects, often prefixed with `:sparkles:` (for example, `:sparkles: Complete phase 6: Modify frontend`). Keep commits focused and descriptive. PRs should summarize user-visible changes, list any migration or env updates, link the related issue or planning doc, and include screenshots for frontend changes or logs for agent-flow changes.

## Security & Configuration Tips
Keep secrets in `.env`, not in source or notebooks. Review the environment setup guides in `docs/manual/` before touching Notion, Pinecone, LLM, or Slack integrations.
