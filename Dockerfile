# ---- Stage 1: Builder ----
FROM python:3.12.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY backend/ backend/
COPY configs/ configs/
COPY main.py alembic.ini ./

# ---- Stage 2: Runtime ----
FROM python:3.12.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/backend backend/
COPY --from=builder /app/configs configs/
COPY --from=builder /app/main.py /app/alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "backend.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
