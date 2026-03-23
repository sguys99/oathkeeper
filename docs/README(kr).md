# OathKeeper

> B2B AI 개발 딜 Go/No-Go 의사결정 지원 에이전트 — 24시간 내 판정 제공

### [English](../README.md) | 한국어



## 주요 기능

| 기능 | 설명 |
|---|---|
| **딜 파싱** | Notion, 자유 텍스트, Word/PDF 문서에서 딜 정보를 자동 구조화 |
| **자동 스코어링** | 7개 기준으로 딜을 0–100점 평가 후 Go/No-Go 판정 |
| **리소스 산출** | 자사 인건비 단가 기반 인력, 기간, 예산 산출 |
| **리스크 분석** | 기술, 일정, 재무, 고객, 범위 등 카테고리별 리스크 식별 및 분류 |
| **유사 사례 검색** | 벡터 DB에서 코사인 유사도 기반 Top-3 유사 과거 프로젝트 검색 |
| **분석 리포트** | 경영진 요약 리포트 생성 및 Notion 저장 |

### 판정 로직

| 판정 | 조건 |
|---|---|
| Go | 총점 >= 70 |
| Conditional Go | 총점 40–69 |
| No-Go | 총점 < 40 |
| Hold | 핵심 필드 3개 이상 누락 |

핵심 딜 필드가 3개 이상 누락되면 스코어링 없이 Hold로 단축 판정됩니다.

---

## 시스템 아키텍처

![Service Architecture](../img/service-architecture.png)

### LangGraph 에이전트 플로우

LangGraph 기반 분석 파이프라인 (`backend/app/agent/graph.py`):

![Agent Flow](../img/agent-flow.png)

| 노드 | 역할 |
|---|---|
| Deal Structuring | 비정형 딜 텍스트에서 구조화된 필드 추출 |
| Scoring | 7개 기준으로 딜 평가, Go/No-Go 권고안 생성 |
| Resource Estimation | 인력, 기간, 예산 산출 |
| Risk Analysis | 카테고리 및 심각도별 리스크 식별 |
| Similar Project | 벡터 DB에서 Top-3 유사 과거 프로젝트 검색 |
| Final Verdict | 모든 결과를 종합하여 경영진 리포트 생성 |
| Hold Verdict | 핵심 필드 누락 시 단축 판정 |

각 노드는 `backend/app/agent/nodes/` 아래 팩토리 함수로 구현되며, `AgentState`(TypedDict)를 통해 상태를 공유합니다. 조건 분기는 LangGraph의 `Send` API로 팬아웃됩니다.

---

## 기술 스택

| 분류 | 기술 |
|---|---|
| **백엔드** | Python 3.12, FastAPI, Pydantic v2 |
| **AI 에이전트** | LangGraph, LiteLLM, LangChain |
| **LLM** | OpenAI GPT-4o / Claude Sonnet (LiteLLM 라우터 경유) |
| **벡터 DB** | Pinecone |
| **데이터베이스** | PostgreSQL 16 (SQLAlchemy 2.0 + asyncpg) |
| **마이그레이션** | Alembic |
| **프론트엔드** | Next.js 16, React 19, TypeScript 5, TailwindCSS v4, shadcn/ui |
| **차트** | Recharts |
| **상태 관리** | TanStack React Query 5 |
| **연동** | Notion API |
| **알림** | Slack Webhook |
| **로깅** | structlog |
| **에러 추적** | Sentry |
| **배포** | Docker Compose, Nginx |

---

## 프로젝트 구조

```
oathkeeper/
├── backend/
│   └── app/
│       ├── api/                # FastAPI 라우터, Pydantic 스키마
│       │   ├── routers/        # deals, analysis, users, settings, notion, agent_logs, prompts, project_history
│       │   └── schemas/        # 요청/응답 스키마
│       ├── agent/              # LangGraph 에이전트
│       │   ├── graph.py        # 메인 그래프 정의
│       │   ├── state.py        # AgentState (공유 상태)
│       │   ├── llm.py          # LLM 클라이언트 (LiteLLM)
│       │   ├── prompt_loader.py # YAML 프롬프트 로더 (Jinja2)
│       │   └── nodes/          # 개별 에이전트 노드
│       ├── db/                 # 데이터베이스 레이어
│       │   ├── models/         # SQLAlchemy ORM 모델
│       │   ├── repositories/   # CRUD 레포지토리
│       │   ├── migrations/     # Alembic 마이그레이션
│       │   ├── vector_store.py # Pinecone 벡터 스토어 래퍼
│       │   ├── pinecone_client.py
│       │   └── seed.py         # 시드 데이터
│       ├── services/           # 비즈니스 로직 서비스
│       │   └── project_history_service.py
│       ├── integrations/       # 외부 서비스 클라이언트
│       │   ├── notion_client.py
│       │   ├── notion_service.py
│       │   └── slack_client.py
│       └── utils/
│           ├── settings.py     # 앱 설정 (환경 변수)
│           ├── path.py         # 프로젝트 경로 상수
│           ├── logging.py      # structlog 설정
│           └── file_parser.py  # 문서 파싱 (Word/PDF)
├── configs/
│   └── prompts/                # 에이전트 프롬프트 YAML 템플릿
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router 페이지
│       │   ├── _components/    # 홈 페이지 (딜 분석 요청)
│       │   ├── deals/          # 딜 대시보드
│       │   │   └── [id]/       # 딜 상세 + 로그
│       │   ├── admin/          # 관리자 설정
│       │   ├── agent-logs/     # 에이전트 실행 로그
│       │   └── agent-settings/ # 에이전트 설정 & 프롬프트 관리
│       ├── components/
│       │   ├── ui/             # shadcn/ui 컴포넌트
│       │   ├── common/         # 공통 컴포넌트 (차트, 뱃지 등)
│       │   └── layout/         # 레이아웃 (헤더)
│       ├── hooks/              # 커스텀 React 훅
│       ├── lib/api/            # API 클라이언트
│       └── providers/          # React 컨텍스트 (Query, User)
├── tests/
│   ├── unit/                   # 유닛 테스트
│   ├── integration/            # 통합 테스트
│   ├── e2e/                    # E2E 테스트
│   └── fixtures/               # 테스트 픽스처
├── docs/                       # 문서
├── nginx/                      # Nginx 리버스 프록시 설정
├── main.py                     # 엔트리포인트 (uvicorn)
├── Makefile
├── Dockerfile                  # 백엔드 Docker
├── docker-compose.yaml         # 개발 환경 (PostgreSQL)
├── docker-compose.prod.yaml    # 프로덕션 환경 (전체 서비스)
└── pyproject.toml
```

---

## 빠른 시작

### 사전 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Node.js 18+ (프론트엔드)
- Docker & Docker Compose (데이터베이스)

### 백엔드

```bash
# 저장소 클론
git clone https://github.com/your-org/oathkeeper.git
cd oathkeeper

# 환경 초기화
make init

# 환경 변수 설정
cp .env.example .env

# 데이터베이스 시작, 마이그레이션, 시드 데이터 삽입
make docker-up
make migrate
make seed

# 백엔드 서버 시작
make run
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

API 키 및 외부 서비스 설정을 포함한 상세 환경 설정은 [환경 설정 가이드](manual/env-setting(kr).md)를 참조하세요.

---

## 문서

| 문서 | 링크 |
|---|---|
| 환경 설정 (영문) | [manual/env-setting(en).md](manual/env-setting(en).md) |
| 환경 설정 (한글) | [manual/env-setting(kr).md](manual/env-setting(kr).md) |
| 사용 매뉴얼 (영문) | [manual/manual(en).md](manual/manual(en).md) |
| 사용 매뉴얼 (한글) | [manual/manual(kr).md](manual/manual(kr).md) |
| 영문 README | [README.md](../README.md) |

---

## 라이선스

Private — All rights reserved.
