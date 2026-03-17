# OathKeeper

> B2B AI 개발 사업 Deal Go/No-Go 의사결정 지원 에이전트

세일즈가 가져오는 B2B AI 개발 Deal을 AI 에이전트가 자동 분석하여 **24시간 이내** 에 Go/No-Go 의사결정을 지원합니다.

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| **Deal 파싱** | Notion, 자유 텍스트, Word/PDF 문서에서 Deal 정보를 자동 구조화 |
| **자동 스코어링** | 7개 표준 평가 기준으로 0~100점 산출 및 Go/No-Go 판단 |
| **소요 산출** | 투입 인력·기간·예산 자동 계산 (회사 인건비 단가 기반) |
| **리스크 분석** | 기술·일정·재무·고객·범위 리스크를 카테고리별로 식별·경고 |
| **유사 사례 검색** | 과거 프로젝트 이력(Vector DB)에서 유사 사례 Top 3 검색 |
| **분석 리포트** | 경영진 보고용 종합 리포트 생성 및 Notion 저장 |

### 평가 기준 (7개 항목)

| 기준 | 가중치 |
|---|:---:|
| 기술 적합성 | 20% |
| 수익성 | 20% |
| 리소스 가용성 | 15% |
| 납기 리스크 | 15% |
| 고객 리스크 | 10% |
| 요구사항 명확성 | 10% |
| 전략적 가치 | 10% |

### 종합 판단 로직

| 판단 | 조건 |
|---|---|
| ✅ Go | 종합 70점 이상 |
| ⚠️ 조건부 Go | 종합 40~69점 |
| ❌ No-Go | 종합 40점 미만 |
| ℹ️ 보류 | 필수 항목 미입력 존재 |

---

## 시스템 아키텍처

```
[세일즈] → Notion DB 입력
              │
              ▼ Notion API
[Backend: Input Parser] ← 문서 업로드 / 추가 텍스트
              │
              ▼
      [Orchestrator Agent]
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
[Deal 구조화] [스코어링] [리스크 분석]
   ▼          ▼          ▼
[소요 산출] [유사사례 검색] [종합 판단]
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
[Frontend] [Notion 저장] [Slack 알림]
```

### LangGraph Agent Flow

LangGraph 기반 분석 파이프라인 (`backend/app/agent/graph.py`):

```
deal_structuring_node
        ↓
[scoring_node, resource_estimation_node, risk_analysis_node, similar_project_node]  ← 병렬 실행
        ↓
final_verdict_node
```

각 노드는 `backend/app/agent/nodes/` 아래 개별 클래스로 구현되며, `AgentState` (TypedDict)를 통해 상태를 공유합니다.

조건부 분기: `structured_deal.missing_fields`가 임계값을 초과하면 즉시 보류(Hold) 판정으로 단락됩니다.

### 에이전트 구성

| 에이전트 | 역할 |
|---|---|
| Orchestrator | 전체 분석 흐름 조율 |
| Deal 구조화 | 비구조화 텍스트에서 필드 추출 |
| 스코어링 | 7개 기준으로 점수 산출 및 Go/No-Go 판단 |
| 소요 산출 | 인력·기간·예산 계산 |
| 리스크 분석 | 카테고리별 리스크 식별 및 심각도 분류 |
| 유사사례 검색 | Vector DB에서 유사 프로젝트 Top 3 검색 |
| 종합 판단 | 전체 결과 종합 및 리포트 생성 |

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| **Backend** | Python 3.12, FastAPI, Pydantic v2 |
| **AI Agent** | LangChain, LangGraph, LiteLLM |
| **LLM** | OpenAI GPT-4o / Claude Sonnet (LiteLLM 라우터) |
| **Vector DB** | Pinecone |
| **RDB** | PostgreSQL 16 (SQLAlchemy 2.0 + asyncpg) |
| **Migrations** | Alembic |
| **Frontend** | Next.js 16, React 19, TypeScript 5, Tailwind CSS v4, shadcn/ui |
| **차트** | Recharts |
| **상태 관리** | TanStack React Query 5 |
| **Input** | Notion API |
| **알림** | Slack Webhook |
| **로깅** | Structlog |
| **에러 추적** | Sentry |
| **배포** | Docker Compose, Nginx |

---

## 프로젝트 구조

```
oathkeeper/
├── backend/
│   └── app/
│       ├── api/               # FastAPI 라우터, Pydantic 스키마
│       │   ├── routers/       # deals, analysis, users, settings, notion, agent_logs, prompts, project_history
│       │   └── schemas/       # 요청/응답 스키마
│       ├── agent/             # LangGraph 에이전트
│       │   ├── graph.py       # 메인 그래프 정의
│       │   ├── state.py       # AgentState (공유 상태)
│       │   ├── llm.py         # LLM 클라이언트 (LiteLLM)
│       │   ├── prompt_loader.py # YAML 프롬프트 로더 (Jinja2)
│       │   └── nodes/         # 개별 에이전트 노드
│       ├── db/                # 데이터베이스 레이어
│       │   ├── models/        # SQLAlchemy ORM 모델
│       │   ├── repositories/  # CRUD 리포지토리
│       │   ├── migrations/    # Alembic 마이그레이션
│       │   ├── vector_store.py # Pinecone Vector Store 래퍼
│       │   ├── pinecone_client.py
│       │   └── seed.py        # 시드 데이터
│       ├── services/          # 비즈니스 로직 서비스
│       │   └── project_history_service.py
│       ├── integrations/      # 외부 서비스 연동
│       │   ├── notion_client.py
│       │   ├── notion_service.py
│       │   └── slack_client.py
│       └── utils/
│           ├── settings.py    # 앱 설정 (환경변수 로드)
│           ├── path.py        # 프로젝트 경로 상수
│           ├── logging.py     # Structlog 설정
│           └── file_parser.py # 문서 파싱 (Word/PDF)
├── configs/
│   └── prompts/               # 에이전트 프롬프트 YAML 템플릿
├── frontend/
│   └── src/
│       ├── app/               # Next.js App Router 페이지
│       │   ├── _components/   # 홈 페이지 (Deal 분석 요청)
│       │   ├── deals/         # Deal 현황 대시보드
│       │   │   └── [id]/      # Deal 상세 분석 결과 + 로그
│       │   ├── admin/         # 관리자 설정 페이지
│       │   ├── agent-logs/    # 에이전트 실행 로그
│       │   └── agent-settings/ # 에이전트 설정 및 프롬프트 관리
│       ├── components/
│       │   ├── ui/            # shadcn/ui 컴포넌트
│       │   ├── common/        # 공통 컴포넌트 (차트, 배지 등)
│       │   └── layout/        # 레이아웃 (헤더)
│       ├── hooks/             # 커스텀 React Hooks
│       ├── lib/api/           # API 클라이언트
│       └── providers/         # React Context (Query, User)
├── tests/
│   ├── unit/                  # 유닛 테스트
│   ├── integration/           # 인테그레이션 테스트
│   ├── e2e/                   # E2E 테스트
│   └── fixtures/              # 테스트 픽스처
├── docs/                      # PRD, 태스크 플랜
├── nginx/                     # Nginx 리버스 프록시 설정
├── main.py                    # 엔트리포인트 (uvicorn)
├── Makefile
├── Dockerfile                 # Backend Docker
├── docker-compose.yaml        # 개발 환경 (PostgreSQL)
├── docker-compose.prod.yaml   # 프로덕션 환경 (전체 서비스)
└── pyproject.toml
```

### 페이지 라우팅

| 경로 | 설명 |
|---|---|
| `/` | Deal 분석 요청 페이지 |
| `/deals` | Deal 현황 대시보드 |
| `/deals/:id` | Deal 상세 분석 결과 |
| `/deals/:id/logs` | Deal별 에이전트 실행 로그 |
| `/admin` | 관리자 설정 페이지 |
| `/agent-logs` | 에이전트 실행 로그 |
| `/agent-settings` | 에이전트 설정 및 프롬프트 관리 |

---

## 시작하기

### 사전 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Node.js 18+ (프론트엔드)
- Docker & Docker Compose (데이터베이스)

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-org/oathkeeper.git
cd oathkeeper

# 프로덕션 환경 초기화
make init

# 개발 환경 초기화 (pre-commit hooks 포함)
make init-dev

# 가상환경 활성화
source .venv/bin/activate

# 프론트엔드 설치
cd frontend && npm install && cd ..
```

### 환경 설정

```bash
cp .env.example .env
```

`.env` 파일에 필요한 값을 입력합니다:

```env
# 애플리케이션
APP_NAME="Oath Keeper"
APP_VERSION="0.1.0"
DEBUG=True
ENVIRONMENT=development

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://oathkeeper:oathkeeper@localhost:5432/oathkeeper

# LLM 설정 (openai 또는 claude)
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic Claude
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Pinecone Vector DB
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_COMPANY_CONTEXT_INDEX=company-context
PINECONE_PROJECT_HISTORY_INDEX=project-history

# Notion 연동
NOTION_API_KEY=
NOTION_DEAL_DB_ID=
NOTION_DECISION_DB_ID=
NOTION_PROJECT_HISTORY_DB_ID=

# Slack 알림
SLACK_WEBHOOK_URL=

# 모니터링
SENTRY_DSN=
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 실행

```bash
# 데이터베이스 시작
make docker-up

# DB 마이그레이션
make migrate

# 시드 데이터 삽입 (최초 1회)
make seed

# 백엔드 서버 실행
make run

# 프론트엔드 개발 서버 (별도 터미널)
cd frontend && npm run dev
```

---

## 개발

### 주요 Make 명령어

```bash
make help              # 사용 가능한 명령어 목록
make init-dev          # 개발 환경 초기화
make format            # 코드 포맷팅 (ruff check --fix && ruff format)
make run               # FastAPI 개발 서버 실행
make docker-up         # PostgreSQL 시작
make docker-down       # PostgreSQL 중지
make migrate           # Alembic 마이그레이션 실행
make seed              # 시드 데이터 삽입
```

### 테스트

```bash
# 유닛 테스트 (기본)
make test

# 인테그레이션 테스트
make test-integration

# E2E 테스트 (서비스 실행 필요)
make test-e2e

# 특정 파일 실행
uv run pytest tests/path/test_file.py

# 특정 테스트 함수 실행
uv run pytest -k "test_function_name"

# 프론트엔드 E2E 테스트 (Playwright)
cd frontend && npm run test:e2e
```

### 코드 스타일

- Line length: 105 chars
- Ruff rules: E, W, F, I, B, C4, UP
- Pre-commit hooks: ruff 포맷팅 + trailing comma 자동 적용
- 테스트 마커: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`

---

## 배포 (Production Deployment)

### 사전 요구사항

- Docker 및 Docker Compose

### 설정

```bash
cp .env.example .env
```

`.env` 파일에서 프로덕션 값을 설정합니다:

```env
DEBUG=False
ENVIRONMENT=production
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-domain.com"]
```

### 빌드 및 실행

```bash
# Docker 이미지 빌드
make docker-build

# 데이터베이스 마이그레이션
docker compose -f docker-compose.prod.yaml run --rm backend alembic upgrade head

# 시드 데이터 삽입 (최초 1회)
docker compose -f docker-compose.prod.yaml run --rm backend python -m backend.app.db.seed

# 서비스 시작
make docker-prod-up

# 서비스 중지
make docker-prod-down
```

### 프로덕션 구성

| 서비스 | 설명 |
|---|---|
| **PostgreSQL** | 데이터베이스 |
| **Backend** | FastAPI 애플리케이션 |
| **Frontend** | Next.js 정적 빌드 |
| **Nginx** | 리버스 프록시 (포트 80) |

### 접속

- 웹 UI: `http://localhost` (nginx 포트 80)
- API Health Check: `http://localhost/api/health`

### 로그 확인

```bash
docker compose -f docker-compose.prod.yaml logs -f backend
docker compose -f docker-compose.prod.yaml logs -f frontend
```

---

## 라이선스

Private — All rights reserved.
