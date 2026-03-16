# OathKeeper 상세 개발 계획서

## Context

OathKeeper는 B2B AI 개발 Deal의 Go/No-Go 의사결정을 지원하는 에이전트 서비스이다. 현재 PRD 문서(696줄)와 디렉토리 스켈레톤만 존재하며, 실제 비즈니스 로직은 구현되지 않은 상태이다. 이 계획은 PRD v1.1 기반으로 MVP 전체 기능(3.1~3.8)을 단계적으로 구현하기 위한 로드맵이다.

**현재 구현 상태:** `utils/path.py`(경로 상수), `utils/settings.py`(비어있음), `main.py`(placeholder) — 이 외 모든 코드 미구현

---

## Phase 0: 인프라 및 개발 환경 구성

**목표:** 로컬 환경에서 서비스를 실행할 수 있는 기반 인프라 완성

### 0-1. Docker 및 데이터베이스 인프라
- [x] `docker-compose.yaml` — PostgreSQL 서비스 정의 (포트 5432, 볼륨, 환경변수)
- [x] `.env.example`에 `DATABASE_URL`, `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `NOTION_API_KEY`, `SLACK_WEBHOOK_URL` 추가

### 0-2. 앱 설정 및 부트스트랩
- [x] `backend/app/utils/settings.py` — Pydantic `BaseSettings` 구현 (`.env` 로드, 전체 설정 항목 정의)
- [x] `backend/app/api/main.py` — FastAPI 앱 인스턴스 생성 (CORS, lifespan, 기본 health check)
- [x] `main.py` — uvicorn 서버 구동으로 교체
- [x] `pyproject.toml` — 누락 의존성 추가: `sqlalchemy`, `asyncpg`, `alembic`, `pinecone-client`, `notion-client`, `httpx`, `python-multipart`, `jinja2`
- [x] `Makefile` — `run`, `docker-up`, `docker-down`, `migrate`, `seed`, `test` 타겟 추가

### 0-3. 데이터베이스 마이그레이션 설정
- [x] Alembic 초기화 (`backend/app/db/migrations/`)
- [x] `backend/app/db/base.py` — SQLAlchemy `DeclarativeBase` 정의
- [x] `backend/app/db/session.py` — async `SessionLocal`, `get_db` 의존성 함수

---

## Phase 1: 데이터 모델 및 DB 계층

**목표:** PRD 6.1의 전체 RDB 테이블을 ORM 모델로 구현
**의존성:** Phase 0

### 1-1. SQLAlchemy ORM 모델
- [x] `backend/app/db/models/user.py` — `users` (id, email, name, role, created_at)
- [x] `backend/app/db/models/deal.py` — `deals` (id, notion_page_id, title, raw_input, structured_data JSONB, status, created_by FK, timestamps)
- [x] `backend/app/db/models/analysis_result.py` — `analysis_results` (id, deal_id FK, total_score, verdict, scores/resource_estimate/risks/similar_projects JSONB, report_markdown, notion_saved_at, created_at)
- [x] `backend/app/db/models/scoring_criteria.py` — `scoring_criteria` (id, name, weight, description, is_active, display_order, updated_at)
- [x] `backend/app/db/models/company_setting.py` — `company_settings` (key PK, value, description, updated_at)
- [x] `backend/app/db/models/team_member.py` — `team_members` (id, name, role, monthly_rate, is_available, current_project, available_from)

### 1-2. 마이그레이션 및 시드 데이터
- [x] Alembic 초기 마이그레이션 생성/적용
- [x] `backend/app/db/seed.py` — 7개 평가 기준 기본값, 샘플 company_settings 삽입

### 1-3. CRUD 레포지토리
- [x] `backend/app/db/repositories/deal_repo.py` — create, get_by_id, list_with_filters, update_status
- [x] `backend/app/db/repositories/analysis_repo.py` — create, get_by_deal_id, update_notion_saved
- [x] `backend/app/db/repositories/settings_repo.py` — ScoringCriteria, CompanySettings, TeamMember CRUD
- [x] `backend/app/db/repositories/user_repo.py` — User CRUD

### 1-4. 테스트
- [x] `tests/conftest.py` — 테스트 DB 세션 픽스처 (SQLite in-memory)
- [x] `tests/unit/db/test_models.py` — 모델 인스턴스 생성 테스트
- [x] `tests/unit/db/test_deal_repo.py` — Deal 레포지토리 테스트
- [x] `tests/unit/db/test_settings_repo.py` — 설정 레포지토리 테스트

---

## Phase 2: Pydantic 스키마 및 API 엔드포인트

**목표:** 프론트엔드와 에이전트가 사용할 REST API 구현
**의존성:** Phase 1

### 2-1. Pydantic 스키마
- [x] `backend/app/api/schemas/deal.py` — DealCreate, DealResponse, DealListResponse, DealStatus(Enum)
- [x] `backend/app/api/schemas/analysis.py` — AnalysisResponse, ScoreDetail, ResourceEstimate, RiskItem, SimilarProject, VerdictEnum
- [x] `backend/app/api/schemas/settings.py` — ScoringCriteriaSchema, CompanySettingSchema, TeamMemberSchema, WeightUpdateRequest (합계 100% validator)
- [x] `backend/app/api/schemas/user.py` — UserCreate, UserResponse
- [x] `backend/app/api/schemas/notion.py` — NotionDealListResponse, NotionSaveRequest/Response

### 2-2. API 라우터
- [x] `backend/app/api/routers/deals.py` — `POST /api/deals`, `GET /api/deals`, `GET /api/deals/{id}`
- [x] `backend/app/api/routers/analysis.py` — `POST /api/deals/{id}/analyze`, `GET /api/deals/{id}/analysis`, `GET /api/deals/{id}/status` (SSE)
- [x] `backend/app/api/routers/settings.py` — 평가 기준, 회사 설정, 팀원, 비용 CRUD 엔드포인트
- [x] `backend/app/api/routers/notion.py` — `GET /api/notion/deals`, `POST /api/deals/{id}/save-to-notion`
- [x] `backend/app/api/routers/users.py` — `POST /api/users`, `GET /api/users/me`
- [x] `backend/app/api/main.py`에 전체 라우터 등록

### 2-3. 에러 핸들링
- [x] `backend/app/api/exceptions.py` — 커스텀 예외 (DealNotFound, AnalysisInProgress, NotionAPIError)
- [x] 전역 예외 핸들러 등록

### 2-4. 테스트
- [x] `tests/unit/api/test_deals_router.py` — Deal 엔드포인트 테스트
- [x] `tests/unit/api/test_settings_router.py` — 설정 엔드포인트 테스트
- [x] `tests/unit/api/test_schemas.py` — 스키마 validation 테스트 (가중치 합계 등)

---

## Phase 3: LLM 연동 및 프롬프트 관리

**목표:** LiteLLM 라우터 기반 LLM 호출 인프라와 Jinja2 프롬프트 템플릿 시스템 구축
**의존성:** Phase 0 (settings), Phase 1과 병렬 가능

### 3-1. LLM 클라이언트
- [x] `backend/app/agent/llm.py` — LiteLLM 라우터 설정, `get_llm()` 팩토리 (LangChain ChatModel 래핑)
- [x] `backend/app/agent/embeddings.py` — OpenAI text-embedding-3-small 임베딩 클라이언트

### 3-2. 프롬프트 템플릿
- [x] `configs/prompts/system.yaml` — 공통 시스템 프롬프트 (역할 정의, Business Context Jinja2 변수)
- [x] `configs/prompts/deal_structuring.yaml` — 구조화 필드 추출, JSON 출력 스키마
- [x] `configs/prompts/scoring.yaml` — 7개 기준별 평가, JSON 출력
- [x] `configs/prompts/resource_estimation.yaml` — 소요 산출
- [x] `configs/prompts/risk_analysis.yaml` — 5개 카테고리, 3단계 심각도
- [x] `configs/prompts/similar_project.yaml` — 유사 프로젝트 정리
- [x] `configs/prompts/final_verdict.yaml` — 마크다운 리포트 생성
- [x] `backend/app/agent/prompt_loader.py` — YAML 로더 + Jinja2 렌더링

### 3-3. 테스트
- [x] `tests/unit/agent/test_prompt_loader.py` — 프롬프트 로딩/렌더링 테스트
- [x] `tests/unit/agent/test_llm.py` — LLM 클라이언트 초기화 테스트

---

## Phase 4: Vector DB (Pinecone) 연동

**목표:** 회사 컨텍스트 및 프로젝트 이력 저장/검색 기능 구현
**의존성:** Phase 3 (임베딩 클라이언트), Phase 1과 병렬 가능

### 4-1. Pinecone 클라이언트
- [x] `backend/app/db/pinecone_client.py` — Pinecone 연결 관리 (init, get_index)

### 4-2. Vector Store 서비스
- [x] `backend/app/db/vector_store.py` — `CompanyContextStore`: upsert(텍스트→임베딩→Pinecone), query(Top K)
- [x] `backend/app/db/vector_store.py` — `ProjectHistoryStore`: upsert(프로젝트 메타데이터), search_similar(코사인 유사도 Top 3)

### 4-3. 테스트
- [x] `tests/unit/db/test_vector_store.py` — mock 기반 단위 테스트
- [x] `tests/integration/test_pinecone.py` — 실제 Pinecone 통합 테스트 (`@pytest.mark.integration`)

---

## Phase 5: 에이전트 구현 (핵심 비즈니스 로직)

**목표:** LangGraph 기반 7개 에이전트 구현 및 오케스트레이션 워크플로우 완성
**의존성:** Phase 3 (LLM) + Phase 4 (Vector DB) + Phase 1 (DB)

### 5-1. 공통 구조
- [x] `backend/app/agent/state.py` — LangGraph State TypedDict (deal_input, structured_deal, scores, resource_estimate, risks, similar_projects, final_report, status, errors)
- [x] `backend/app/agent/base.py` — 에이전트 베이스 (공통 프롬프트 로딩, LLM 호출, 출력 파싱, 에러 핸들링)

### 5-2. 개별 에이전트
- [x] `backend/app/agent/nodes/deal_structuring.py` — 비구조화 텍스트 → 구조화 JSON, missing_fields 식별
- [x] `backend/app/agent/nodes/scoring.py` — 7개 기준 0-100점, 가중 합산, Go/No-Go 판단
- [x] `backend/app/agent/nodes/resource_estimation.py` — 인력/기간/예산 계산 (Vector DB 회사 단가 참조)
- [x] `backend/app/agent/nodes/risk_analysis.py` — 5개 카테고리 리스크, HIGH/MEDIUM/LOW, 완화 방안
- [x] `backend/app/agent/nodes/similar_project.py` — Pinecone Top 3 유사 프로젝트, 비교 정보
- [x] `backend/app/agent/nodes/final_verdict.py` — 전체 결과 종합, 마크다운 리포트, 권고사항

### 5-3. 오케스트레이터 (LangGraph)
- [x] `backend/app/agent/graph.py` — StateGraph 정의
  - deal_structuring → (scoring, resource_estimation, risk_analysis, similar_project) 병렬 → final_verdict
  - 조건부 분기: missing_fields 과다 시 보류 처리
  - 각 노드 완료 시 DB status 업데이트 콜백

### 5-4. 분석 서비스
- [x] `backend/app/agent/service.py` — `AnalysisService`: graph 실행, 결과 DB 저장, 에러 핸들링
- [x] `backend/app/api/routers/analysis.py`에서 `AnalysisService` 호출 연동 (BackgroundTasks)

### 5-5. 테스트
- [x] `tests/unit/agent/test_deal_structuring.py` — mock LLM 응답 기반 테스트
- [x] `tests/unit/agent/test_scoring.py` — 가중치 계산 정확성, 판단 로직 테스트
- [x] `tests/unit/agent/test_resource_estimation.py`
- [x] `tests/unit/agent/test_risk_analysis.py`
- [x] `tests/unit/agent/test_graph.py` — 전체 그래프 흐름 테스트 (모든 에이전트 mock)
- [x] `tests/integration/test_analysis_e2e.py` — 실제 LLM 호출 통합 테스트 (`@pytest.mark.integration`)

---

## Phase 6: 외부 연동 (Notion, Slack)

**목표:** Notion API Deal 읽기/저장, Slack 알림, 파일 업로드 기능 구현
**의존성:** Phase 2 (API) + Phase 5 (분석 결과)

### 6-1. Notion 연동
- [x] `backend/app/integrations/notion_client.py` — Notion API 클라이언트 래퍼 (DB 조회, 페이지 읽기, 하위 페이지 생성)
- [x] `backend/app/integrations/notion_service.py` — `list_deals()`: PRD 6.3 필드 매핑 적용
- [x] `backend/app/integrations/notion_service.py` — `get_deal_content(page_id)`: 콘텐츠 파싱
- [x] `backend/app/integrations/notion_service.py` — `save_analysis_to_notion()`: 분석 결과 하위 페이지 저장

### 6-2. Slack 연동
- [x] `backend/app/integrations/slack_client.py` — Webhook 알림 (분석 완료 요약, Notion 저장 완료)

### 6-3. 파일 업로드
- [x] `backend/app/api/routers/deals.py` — `POST /api/deals/{id}/upload` (Word/PDF)
- [x] `backend/app/utils/file_parser.py` — Word(python-docx)/PDF(PyPDF2) 텍스트 추출

### 6-4. 테스트
- [x] `tests/unit/integrations/test_notion_service.py` — Notion 서비스 mock 테스트
- [x] `tests/unit/integrations/test_slack_client.py`
- [x] `tests/integration/test_notion.py` — 실제 API 통합 테스트 (`@pytest.mark.integration`)

---

## Phase 7: 프론트엔드 구현

**목표:** Next.js 기반 4개 페이지 UI 구현 및 백엔드 연동
**의존성:** Phase 2 (API 스키마 확정 후 병렬 착수 가능)

### 7-1. 프로젝트 초기화
- [x] Next.js 15 App Router 프로젝트 생성
- [x] TailwindCSS v4 설정
- [x] shadcn/ui 설치 (Button, Input, Card, Table, Tabs, Dialog, Badge, Slider, Select, Textarea)
- [x] `frontend/lib/api.ts` — API 클라이언트 (fetch 래퍼, 타입 정의)

### 7-2. 공통 컴포넌트
- [x] `frontend/app/layout.tsx` — 전체 레이아웃 (헤더, 네비게이션)
- [x] `frontend/components/VerdictBadge.tsx` — Go/No-Go/조건부/보류 배지
- [x] `frontend/components/ScoreBar.tsx` — 점수 프로그레스 바
- [x] `frontend/components/RiskIndicator.tsx` — 리스크 레벨 (HIGH/MEDIUM/LOW 색상)
- [x] `frontend/components/RadarChart.tsx` — 7개 평가 기준 레이더 차트

### 7-3. 페이지 1 — Deal 분석 요청 (`/`)
- [x] Notion Deal 드롭다운 선택
- [x] 추가 정보 텍스트 입력 + 파일 업로드 (drag & drop)
- [x] 분석 시작 + 진행 상태 표시 (SSE/polling)
- [x] 완료 시 상세 결과 페이지 자동 이동

### 7-4. 페이지 2 — Deal 현황 대시보드 (`/deals`)
- [x] Deal 목록 테이블 (고객사, 판단, 점수, 생성일, 담당자)
- [x] 검색 + 필터 (판단 결과, 기간) + 페이지네이션

### 7-5. 페이지 3 — 상세 분석 결과 (`/deals/[id]`)
- [x] 종합 점수 + 레이더 차트 + Deal 개요
- [x] 평가 기준별 점수 (프로그레스 바 + 근거)
- [x] 소요 인력/기간/예산 카드
- [x] 리스크 분석 목록 (카테고리별, 심각도 색상)
- [x] 유사 프로젝트 Top 3
- [x] 권고사항 + "Notion에 저장" 버튼

### 7-6. 페이지 4 — 관리자 설정 (`/admin`)
- [x] 탭 1: 회사 정보 (사업 방향, 전략, Deal 기준)
- [x] 탭 2: 평가 기준 가중치 (슬라이더, 합계 100% 실시간 검증)
- [x] 탭 3: 인력 관리 (팀원 CRUD, 월 단가, 가용 상태)
- [x] 탭 4: 비용 설정 (HW/SW/라이선스 항목 CRUD)
- [x] 탭 5: 프로젝트 이력 (등록 폼 + 목록)

### 7-7. 반응형
- [x] 1280px 이상 데스크탑 레이아웃
- [x] 768px 이하 모바일 간소화 (메인 입력 + Deal 현황만)

---

## Phase 8: 통합 테스트 및 E2E 테스트

**목표:** 전체 시스템 엔드투엔드 동작 검증
**의존성:** Phase 5, 6, 7 완료

### 8-1. 백엔드 통합 테스트
- [x] `tests/integration/test_deal_flow.py` — Deal 생성 → 분석 → 결과 조회 전체 플로우
- [x] `tests/integration/test_notion_flow.py` — Notion 조회 → 분석 → Notion 저장 → Slack 알림
- [x] `tests/integration/test_settings_flow.py` — 설정 변경 → 분석 반영 검증

### 8-2. E2E 테스트
- [x] 실제 Deal 5건 분석 완료 시나리오 (`@pytest.mark.e2e`)
- [x] 응답 시간 3분 이내 검증
- [x] 분석 실패율 5% 이하 검증

### 8-3. 프론트엔드 E2E
- [x] Playwright 설정
- [x] 메인 입력 → 분석 → 결과 확인 시나리오
- [x] 관리자 설정 변경 시나리오

---

## Phase 9: 배포 및 운영 준비

**목표:** 프로덕션 배포 환경 구성 및 운영 모니터링 설정
**의존성:** Phase 8

- [x] `Dockerfile` (backend) — Python 멀티스테이지 빌드
- [x] `frontend/Dockerfile` — Next.js 프로덕션 빌드
- [x] `docker-compose.prod.yaml` 프로덕션 설정 (backend, frontend, PostgreSQL, nginx)
- [x] 로깅 설정 (structlog, JSON 포맷)
- [x] 에러 트래킹 (Sentry 연동)
- [x] `README.md` 배포 가이드 완성

---

## Phase 의존성 다이어그램

```
Phase 0 (인프라)
    │
    ├── Phase 1 (DB 모델) ──────────────────┐
    │       │                               │
    │       └── Phase 2 (API) ──────────┐   │
    │                                   │   │
    ├── Phase 3 (LLM/프롬프트) ─────────┤   │
    │                                   │   │
    ├── Phase 4 (Vector DB) ────────────┤   │
    │                                   │   │
    │                    Phase 5 (에이전트) ←┘
    │                           │
    │                    Phase 6 (Notion/Slack)
    │                           │
    │    Phase 7 (프론트엔드) ←── Phase 2 이후 병렬 가능
    │                           │
    │                    Phase 8 (통합/E2E 테스트)
    │                           │
    │                    Phase 9 (배포)
    └───────────────────────────┘
```

**병렬 가능 구간:**
- Phase 3/4는 Phase 1과 병렬 진행 가능
- Phase 7은 Phase 2 API 스키마 확정 후 백엔드와 병렬 진행 가능

---

## 검증 지표 (MVP 성공 기준)

| 항목 | 목표 |
|---|---|
| 분석 완료 시간 | 3분 이내 |
| 분석 실패율 | 5% 이하 |
| Go/No-Go 판단 일치율 | 전문가 대비 80% 이상 |
| 7개 평가 기준 커버율 | 100% |
| 유사 프로젝트 검색 | Top 3 항상 반환 |

## 주요 파일 참조

- [docs/PRD.md](PRD.md) — 전체 요구사항 원천 문서
- [backend/app/utils/settings.py](../backend/app/utils/settings.py) — 앱 설정 (Phase 0에서 최초 구현)
- [backend/app/api/main.py](../backend/app/api/main.py) — FastAPI 진입점
- [backend/app/agent/graph.py](../backend/app/agent/graph.py) — LangGraph 오케스트레이터 (Phase 5 핵심)
- [pyproject.toml](../pyproject.toml) — 의존성 관리
- [docker-compose.yaml](../docker-compose.yaml) — 인프라 서비스
