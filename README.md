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

**에이전트 구성**

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
| **Backend** | Python 3.12, FastAPI |
| **AI Agent** | LangChain, LangGraph |
| **LLM** | OpenAI GPT-4o / Claude Sonnet (LiteLLM 라우터) |
| **Vector DB** | Pinecone |
| **RDB** | PostgreSQL |
| **Frontend** | Next.js, TailwindCSS v4, shadcn/ui |
| **Input** | Notion API |
| **알림** | Slack Webhook |

---

## 시작하기

### 사전 요구사항

- Python 3.12.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

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
```

### 환경 설정

```bash
cp .env.example .env
```

`.env` 파일에 필요한 값을 입력합니다:

```env
# LLM 설정 (openai 또는 claude)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/oathkeeper

# Notion 연동
NOTION_API_KEY=secret_...
NOTION_DEAL_DB_ID=...
NOTION_DECISION_DB_ID=...

# Slack 알림
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Pinecone Vector DB
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
```

### 실행

```bash
uv run python main.py
```

---

## 개발

### 코드 포맷팅

```bash
make format
```

### 테스트

```bash
# 유닛 테스트 (기본)
uv run pytest

# 인테그레이션 테스트
uv run pytest -m integration

# 특정 파일 실행
uv run pytest tests/path/test_file.py

# 특정 테스트 함수 실행
uv run pytest -k "test_function_name"
```

### 프로젝트 구조

```
oathkeeper/
├── backend/
│   └── app/
│       ├── api/          # FastAPI 라우터 및 Pydantic 스키마
│       ├── db/           # 데이터베이스 레이어
│       └── utils/
│           ├── path.py   # 프로젝트 경로 상수
│           └── settings.py  # 앱 설정 (환경변수 로드)
├── configs/
│   └── prompts/          # 에이전트 프롬프트 YAML 템플릿
├── docs/
│   └── PRD.md            # 제품 요구사항 문서
├── frontend/             # Next.js 프론트엔드
├── tests/                # 테스트 코드
├── main.py               # 엔트리포인트
├── pyproject.toml
└── .env.example
```

### 페이지 라우팅

| 경로 | 설명 |
|---|---|
| `/` | Deal 분석 요청 페이지 |
| `/deals` | Deal 현황 대시보드 |
| `/deals/:id` | Deal 상세 분석 결과 |
| `/admin` | 관리자 설정 페이지 |

---

## 라이선스

Private — All rights reserved.
