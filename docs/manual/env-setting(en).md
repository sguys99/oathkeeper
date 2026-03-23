# Environment Setup Guide

> [한글 버전 →](env-setting(kr).md) · [← Back to README](../../README.md) · [User Manual →](manual(en).md)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Notion Setup](#2-notion-setup)
3. [Installation](#3-installation)
4. [Environment Variables](#4-environment-variables)
5. [Database Setup](#5-database-setup)
6. [Running the Application](#6-running-the-application)
7. [Production Deployment](#7-production-deployment)

---

## 1. Prerequisites

Ensure the following tools are installed before proceeding:

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12.12+ | Backend runtime |
| **uv** | latest | Python package manager |
| **Node.js** | 18+ | Frontend runtime |
| **Docker & Docker Compose** | latest | PostgreSQL & production deployment |
| **Git** | latest | Version control |

---

## 2. Notion Setup

OathKeeper integrates with Notion to read deal information and write analysis results. You need to create a **Notion Integration** and **three databases**.

### 2.1 Create a Notion Integration

1. Go to [Notion Developers](https://www.notion.so/profile/integrations) and click **"New integration"**
2. Enter a name (e.g., `OathKeeper`)
3. Select the workspace where your databases will live
4. Choose **Internal integration** type
5. Under **Capabilities**, ensure **Read content**, **Update content**, and **Insert content** are enabled
6. Click **Save** and copy the **Internal Integration Secret** (starts with `ntn_`)
7. Paste it into your `.env` file as `NOTION_API_KEY`

### 2.2 Create Databases

Create a dedicated page in your Notion workspace (e.g., "OathKeeper") and add three database tables under it:

- **deal information** — Source of incoming deals (populated by the sales team)
- **ai descision** — Analysis results (auto-populated by OathKeeper)
- **project history** — Past project records (used for similarity matching)

![OathKeeper Notion Database Overview](imgs/0-1.notiondb-overview.png)

> **Important:** After creating each database, click **Share** (top-right) → invite your integration so OathKeeper can access it.

### 2.3 Database Schema — Deal Information

This database stores incoming deal entries. The sales team manually adds deals here, and OathKeeper reads them for analysis.

![Deal Information Database](imgs/0-2.notiondb-dealinfo.png)

Create the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `deal_info` | **Title** | Deal name (typically customer + project name) |
| `customer_name` | **Rich Text** | Customer organization name |
| `expected_amount` | **Number** | Expected contract value (KRW) |
| `duration_months` | **Number** | Estimated project duration in months |
| `date` | **Date** | Deal registration date |
| `author` | **Person** | Team member who submitted the deal |
| `status` | **Select** | Deal status — create three options: `미분석` (Not Analyzed), `분석중` (Analyzing), `완료` (Completed) |
| `ai descision` | **Relation** | Links to the AI Decision database (auto-populated after analysis) |

### 2.4 Database Schema — AI Decision

OathKeeper automatically creates pages in this database when an analysis completes. You only need to set up the schema — the data is populated by the system.

![AI Decision Database](imgs/0-3.notiondb-aidecision.png)

Create the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `report` | **Title** | Auto-generated as `"분석 결과 — [Verdict]"` (e.g., "분석 결과 — Conditional Go") |
| `decision` | **Select** | Verdict — create four options: `Go`, `Conditional Go`, `No-Go`, `Hold` |
| `deal` | **Relation** | Links back to the Deal Information database |
| `total_score` | **Number** | Overall analysis score (0–100) |
| `analysis_date` | **Date** | Timestamp when the analysis completed |

### 2.5 Database Schema — Project History

This database stores records of past completed projects. OathKeeper uses these for similarity matching (vector embedding) during deal analysis.

![Project History Database](imgs/0-4.notiondb-projecthistory.png)

Create the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `project_name` | **Title** | Name of the completed project |
| `summary` | **Rich Text** | Project description (used for vector embedding) |
| `industry` | **Select** | Industry classification (e.g., 조선해양, 에너지) |
| `tech_stack` | **Multi-select** | Technologies used (e.g., video analytics, IoT) |
| `duration_months` | **Number** | Actual project duration in months |
| `planned_headcount` | **Number** | Initially planned team size |
| `actual_headcount` | **Number** | Actual team size deployed |
| `contract_amount` | **Number** | Contract value (KRW) |

### 2.6 Get Database IDs

Each database has a unique ID embedded in its URL. You need these IDs for the `.env` configuration.

1. Open each database as a **full page** in Notion
2. Copy the URL from your browser — it will look like:
   ```
   https://www.notion.so/{workspace_name}/{database_id}?v={view_id}
   ```
3. The `{database_id}` is the 32-character hexadecimal string before the `?v=` parameter
4. Add the IDs to your `.env` file:
   ```
   NOTION_DEAL_DB_ID=your_deal_database_id_here
   NOTION_DECISION_DB_ID=your_decision_database_id_here
   NOTION_PROJECT_HISTORY_DB_ID=your_history_database_id_here
   ```

> **Tip:** You can also find Database IDs via the Notion API — use `POST https://api.notion.com/v1/search` with your integration token.

---

## 3. Installation

### Backend

```bash
# Clone the repository
git clone https://github.com/your-org/oathkeeper.git
cd oathkeeper

# Production environment
make init

# Development environment (includes pre-commit hooks for ruff formatting)
make init-dev
```

`make init` / `make init-dev` will:
- Install Python 3.12.12 via `uv`
- Create a virtual environment
- Install all Python dependencies
- (dev only) Set up pre-commit hooks

### Frontend

```bash
cd frontend
npm install
```

---

## 4. Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `"Oath Keeper"` | Application display name |
| `APP_VERSION` | `"0.1.0"` | Application version |
| `DEBUG` | `True` | Enable debug mode |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://oathkeeper:oathkeeper@localhost:5432/oathkeeper` | PostgreSQL async connection string |

### LLM Provider

Choose one provider — either OpenAI or Anthropic Claude.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai` or `claude` |
| `OPENAI_API_KEY` | — | **Required** if `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model (always OpenAI, regardless of provider) |
| `ANTHROPIC_API_KEY` | — | **Required** if `LLM_PROVIDER=claude` |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Anthropic model name |

> **Note:** Even when using Claude as the LLM provider, `OPENAI_API_KEY` is still required for the embedding model (`text-embedding-3-small`).

### Pinecone (Vector Database)

| Variable | Default | Description |
|----------|---------|-------------|
| `PINECONE_API_KEY` | — | Pinecone API key |
| `PINECONE_ENVIRONMENT` | — | Pinecone environment region |
| `PINECONE_COMPANY_CONTEXT_INDEX` | `company-context` | Index name for company context embeddings |
| `PINECONE_PROJECT_HISTORY_INDEX` | `project-history` | Index name for project history embeddings |

### Notion

See [Section 2: Notion Setup](#2-notion-setup) for how to obtain these values.

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTION_API_KEY` | — | Notion integration token (starts with `ntn_`) |
| `NOTION_DEAL_DB_ID` | — | Deal Information database ID |
| `NOTION_DECISION_DB_ID` | — | AI Decision database ID |
| `NOTION_PROJECT_HISTORY_DB_ID` | — | Project History database ID |

### Integrations (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | — | Slack incoming webhook URL for analysis notifications |
| `SENTRY_DSN` | — | Sentry DSN for error tracking |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (JSON array) |

### Frontend

Create `frontend/.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## 5. Database Setup

### Start PostgreSQL

```bash
make docker-up
```

This starts a **PostgreSQL 16** container with:
- User: `oathkeeper`
- Password: `oathkeeper`
- Database: `oathkeeper`
- Port: `5432`

### Run Migrations

```bash
make migrate
```

Applies all Alembic migrations to create the database schema (users, deals, analysis_results, scoring_criteria, company_settings, team_members, agent_logs, cost_items).

### Seed Default Data

```bash
make seed
```

Inserts default configuration data:

| Data | Description |
|------|-------------|
| **Scoring Criteria** | 7 evaluation criteria with weights (Technical Fit 20%, Profitability 20%, Resource Availability 15%, Timeline Risk 15%, Requirement Clarity 10%, Strategic Value 10%, Customer Risk 10%) |
| **Company Settings** | Business direction, deal qualification criteria, short/mid/long-term strategies |
| **Team Members** | Team roster with roles and monthly rates |
| **Cost Items** | Infrastructure and hardware cost defaults |

> These defaults can be modified later through the Admin UI (`/admin`).

### Stop PostgreSQL

```bash
make docker-down
```

---

## 6. Running the Application

Start both the backend and frontend in separate terminals:

```bash
# Terminal 1 — Backend (FastAPI)
make run
# → Running on http://localhost:8000

# Terminal 2 — Frontend (Next.js)
cd frontend
npm run dev
# → Running on http://localhost:3000
```

Verify the backend is running:

```bash
curl http://localhost:8000/health
```

Open `http://localhost:3000` in your browser to access the application.

---

## 7. Production Deployment

OathKeeper provides a Docker Compose production configuration with four services:

| Service | Description |
|---------|-------------|
| **PostgreSQL 16** | Database |
| **Backend** | FastAPI + uvicorn |
| **Frontend** | Next.js production build |
| **Nginx** | Reverse proxy (port 80) |

### Build & Start

```bash
# Build production Docker images
make docker-build

# Start all services
make docker-prod-up
```

The application will be available at `http://localhost` (port 80).

### Stop

```bash
make docker-prod-down
```

---

> [한글 버전 →](env-setting(kr).md) · [← Back to README](../../README.md) · [User Manual →](manual(en).md)
