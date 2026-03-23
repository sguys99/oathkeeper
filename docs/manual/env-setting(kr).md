# 환경 설정 가이드

> [English Version →](env-setting(en).md) · [← README로 돌아가기](../README(kr).md) · [사용 매뉴얼 →](manual(kr).md)

---

## 목차

1. [사전 준비](#1-사전-준비)
2. [Notion 설정](#2-notion-설정)
3. [설치](#3-설치)
4. [환경 변수](#4-환경-변수)
5. [데이터베이스 설정](#5-데이터베이스-설정)
6. [애플리케이션 실행](#6-애플리케이션-실행)
7. [프로덕션 배포](#7-프로덕션-배포)

---

## 1. 사전 준비

다음 도구들이 설치되어 있어야 합니다:

| 도구 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.12.12+ | 백엔드 런타임 |
| **uv** | 최신 | Python 패키지 매니저 |
| **Node.js** | 18+ | 프론트엔드 런타임 |
| **Docker & Docker Compose** | 최신 | PostgreSQL 및 프로덕션 배포 |

---

## 2. Notion 설정

OathKeeper는 Notion과 연동하여 딜 정보를 읽고 분석 결과를 저장합니다. **Notion Integration**과 **3개의 데이터베이스**를 생성해야 합니다.

### 2.1 Notion Integration 생성

1. [Notion Developers](https://www.notion.so/profile/integrations)에 접속하여 **"새 통합"**을 클릭합니다
2. 이름을 입력합니다 (예: `OathKeeper`)
3. 데이터베이스가 위치할 워크스페이스를 선택합니다
4. **Internal integration** 유형을 선택합니다
5. **기능(Capabilities)** 탭에서 **콘텐츠 읽기**, **콘텐츠 업데이트**, **콘텐츠 삽입**이 활성화되어 있는지 확인합니다
6. **저장**을 클릭하고 **Internal Integration Secret** (`ntn_`으로 시작)을 복사합니다
7. `.env` 파일의 `NOTION_API_KEY`에 붙여넣습니다

### 2.2 데이터베이스 생성

Notion 워크스페이스에 전용 페이지(예: "OathKeeper")를 만들고 그 아래에 3개의 데이터베이스 테이블을 추가합니다:

- **deal information** — 수주 딜 정보 (영업팀이 수동 입력)
- **ai descision** — 분석 결과 (OathKeeper가 자동 생성)
- **project history** — 과거 프로젝트 기록 (유사 프로젝트 매칭에 활용)

![OathKeeper Notion 데이터베이스 개요](imgs/0-1.notiondb-overview.png)

> **중요:** 각 데이터베이스 생성 후, 우측 상단의 **공유** 버튼을 클릭하여 생성한 Integration을 초대해야 OathKeeper가 접근할 수 있습니다.

### 2.3 데이터베이스 스키마 — Deal Information

이 데이터베이스는 수주 딜 항목을 저장합니다. 영업팀이 수동으로 딜을 등록하면, OathKeeper가 이를 읽어 분석합니다.

![Deal Information 데이터베이스](imgs/0-2.notiondb-dealinfo.png)

다음 프로퍼티를 생성합니다:

| 프로퍼티 | 타입 | 설명 |
|----------|------|------|
| `deal_info` | **제목(Title)** | 딜 이름 (고객사 + 프로젝트명) |
| `customer_name` | **텍스트(Rich Text)** | 고객사명 |
| `expected_amount` | **숫자(Number)** | 예상 계약 금액 (원) |
| `duration_months` | **숫자(Number)** | 예상 프로젝트 기간 (개월) |
| `date` | **날짜(Date)** | 딜 등록일 |
| `author` | **사람(Person)** | 딜을 등록한 팀원 |
| `status` | **선택(Select)** | 딜 상태 — 3개 옵션 생성: `미분석`, `분석중`, `완료` |
| `ai descision` | **관계형(Relation)** | AI Decision 데이터베이스와 연결 (분석 완료 후 자동 생성) |

### 2.4 데이터베이스 스키마 — AI Decision

분석이 완료되면 OathKeeper가 이 데이터베이스에 자동으로 페이지를 생성합니다. 스키마만 설정하면 되며, 데이터는 시스템이 자동으로 채웁니다.

![AI Decision 데이터베이스](imgs/0-3.notiondb-aidecision.png)

다음 프로퍼티를 생성합니다:

| 프로퍼티 | 타입 | 설명 |
|----------|------|------|
| `report` | **제목(Title)** | 자동 생성: `"분석 결과 — [판정]"` (예: "분석 결과 — Conditional Go") |
| `decision` | **선택(Select)** | 판정 결과 — 4개 옵션 생성: `Go`, `Conditional Go`, `No-Go`, `Hold` |
| `deal` | **관계형(Relation)** | Deal Information 데이터베이스와 역방향 연결 |
| `total_score` | **숫자(Number)** | 종합 분석 점수 (0–100) |
| `analysis_date` | **날짜(Date)** | 분석 완료 시점 |

### 2.5 데이터베이스 스키마 — Project History

이 데이터베이스는 과거 완료된 프로젝트 기록을 저장합니다. OathKeeper는 딜 분석 시 이 데이터를 벡터 임베딩하여 유사 프로젝트 매칭에 활용합니다.

![Project History 데이터베이스](imgs/0-4.notiondb-projecthistory.png)

다음 프로퍼티를 생성합니다:

| 프로퍼티 | 타입 | 설명 |
|----------|------|------|
| `project_name` | **제목(Title)** | 프로젝트명 |
| `summary` | **텍스트(Rich Text)** | 프로젝트 설명 (벡터 임베딩에 사용) |
| `industry` | **선택(Select)** | 산업 분류 (예: 조선해양, 에너지) |
| `tech_stack` | **다중 선택(Multi-select)** | 사용 기술 (예: video analytics, IoT) |
| `duration_months` | **숫자(Number)** | 실제 프로젝트 기간 (개월) |
| `planned_headcount` | **숫자(Number)** | 계획 투입 인원 |
| `actual_headcount` | **숫자(Number)** | 실제 투입 인원 |
| `contract_amount` | **숫자(Number)** | 계약 금액 (원) |

### 2.6 Database ID 확인

각 데이터베이스의 URL에 고유 ID가 포함되어 있습니다. `.env` 설정에 이 ID가 필요합니다.

1. 각 데이터베이스를 Notion에서 **전체 페이지**로 엽니다
2. 브라우저의 URL을 복사합니다 — 다음과 같은 형식입니다:
   ```
   https://www.notion.so/{워크스페이스명}/{database_id}?v={view_id}
   ```
3. `?v=` 앞의 32자리 16진수 문자열이 `{database_id}`입니다
4. `.env` 파일에 ID를 추가합니다:
   ```
   NOTION_DEAL_DB_ID=your_deal_database_id_here
   NOTION_DECISION_DB_ID=your_decision_database_id_here
   NOTION_PROJECT_HISTORY_DB_ID=your_history_database_id_here
   ```

> **팁:** Notion API를 통해서도 Database ID를 찾을 수 있습니다 — Integration 토큰으로 `POST https://api.notion.com/v1/search`를 호출하세요.

### 2.7 Pinecone 설정

OathKeeper는 유사 프로젝트 매칭을 위해 [Pinecone](https://www.pinecone.io/)을 벡터 데이터베이스로 사용합니다. **1개의 인덱스**(`project-history`)를 생성해야 합니다.

1. [Pinecone](https://www.pinecone.io/)에 가입하고 프로젝트를 생성합니다
2. 사이드바의 **API Keys**에서 API 키를 복사하여 `.env`의 `PINECONE_API_KEY`에 붙여넣습니다
3. `project-history`라는 이름으로 새 인덱스를 생성합니다 — 임베딩 모델로 **text-embedding-3-small** (OpenAI)을 선택하고 다음 설정값을 사용합니다:

![Pinecone 인덱스 설정](imgs/0-5.pinecone-setting.png)

| 설정 | 값 |
|------|-----|
| **임베딩 모델** | text-embedding-3-small (OpenAI) |
| **모달리티** | Text |
| **벡터 타입** | Dense |
| **차원(Dimension)** | 1536 |
| **메트릭** | cosine |

> **참고:** 차원(1536)과 메트릭(cosine)은 정확히 일치해야 합니다 — 이 값들은 OpenAI의 `text-embedding-3-small` 모델 출력에 대응합니다.

---

## 3. 설치

### 백엔드

```bash
# 저장소 클론
git clone https://github.com/your-org/oathkeeper.git
cd oathkeeper

# 프로덕션 환경
make init

# 개발 환경 (ruff 포매팅을 위한 pre-commit 훅 포함)
make init-dev
```

`make init` / `make init-dev` 실행 시:
- `uv`를 통해 Python 3.12.12 설치
- 가상 환경 생성
- 모든 Python 의존성 설치
- (개발 환경만) pre-commit 훅 설정

### 프론트엔드

```bash
cd frontend
npm install
```

---

## 4. 환경 변수

예제 파일을 복사하고 값을 입력합니다:

```bash
cp .env.example .env
```

### 애플리케이션

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `APP_NAME` | `"Oath Keeper"` | 애플리케이션 표시 이름 |
| `APP_VERSION` | `"0.1.0"` | 애플리케이션 버전 |
| `DEBUG` | `True` | 디버그 모드 활성화 |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |

### 데이터베이스

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://oathkeeper:oathkeeper@localhost:5432/oathkeeper` | PostgreSQL 비동기 연결 문자열 |

### LLM 프로바이더

OpenAI 또는 Anthropic Claude 중 하나를 선택합니다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LLM_PROVIDER` | `openai` | LLM 프로바이더: `openai` 또는 `claude` |
| `OPENAI_API_KEY` | — | `LLM_PROVIDER=openai`일 때 **필수** |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 모델명 |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | 임베딩 모델 (프로바이더와 무관하게 항상 OpenAI 사용) |
| `ANTHROPIC_API_KEY` | — | `LLM_PROVIDER=claude`일 때 **필수** |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Anthropic 모델명 |

> **참고:** Claude를 LLM 프로바이더로 사용하더라도, 임베딩 모델(`text-embedding-3-small`)을 위해 `OPENAI_API_KEY`는 여전히 필요합니다.

### Pinecone (벡터 데이터베이스)

인덱스 생성 방법은 [2.7 Pinecone 설정](#27-pinecone-설정)을 참고하세요.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PINECONE_API_KEY` | — | Pinecone API 키 |
| `PINECONE_ENVIRONMENT` | — | Pinecone 환경 리전 |
| `PINECONE_COMPANY_CONTEXT_INDEX` | `company-context` | 회사 컨텍스트 임베딩 인덱스명 |
| `PINECONE_PROJECT_HISTORY_INDEX` | `project-history` | 프로젝트 히스토리 임베딩 인덱스명 |

### Notion

값을 얻는 방법은 [2. Notion 설정](#2-notion-설정)을 참고하세요.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NOTION_API_KEY` | — | Notion Integration 토큰 (`ntn_`으로 시작) |
| `NOTION_DEAL_DB_ID` | — | Deal Information 데이터베이스 ID |
| `NOTION_DECISION_DB_ID` | — | AI Decision 데이터베이스 ID |
| `NOTION_PROJECT_HISTORY_DB_ID` | — | Project History 데이터베이스 ID |

### 연동 (선택 사항)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SLACK_WEBHOOK_URL` | — | Slack 수신 웹훅 URL (분석 결과 알림용) |
| `SENTRY_DSN` | — | Sentry 에러 트래킹 DSN |
| `LOG_LEVEL` | `INFO` | 로깅 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | 허용된 CORS 출처 (JSON 배열) |

### 프론트엔드

`frontend/.env.local` 파일을 생성합니다:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | 백엔드 API 기본 URL |

---

## 5. 데이터베이스 설정

### PostgreSQL 시작

```bash
make docker-up
```

다음 설정으로 **PostgreSQL 16** 컨테이너가 실행됩니다:
- 사용자: `oathkeeper`
- 비밀번호: `oathkeeper`
- 데이터베이스: `oathkeeper`
- 포트: `5432`

### 마이그레이션 실행

```bash
make migrate
```

모든 Alembic 마이그레이션을 적용하여 데이터베이스 스키마를 생성합니다 (users, deals, analysis_results, scoring_criteria, company_settings, team_members, agent_logs, cost_items).

### 기본 데이터 시딩

```bash
make seed
```

기본 설정 데이터를 삽입합니다:

| 데이터 | 설명 |
|--------|------|
| **평가 기준** | 7개 평가 기준 및 가중치 (기술 적합성 20%, 수익성 20%, 리소스 가용성 15%, 납기 리스크 15%, 요구사항 명확성 10%, 전략적 가치 10%, 고객 리스크 10%) |
| **회사 설정** | 사업 방향, 딜 판단 기준, 단기/중기/장기 전략 |
| **팀원 정보** | 팀원 목록, 역할 및 월 단가 |
| **비용 항목** | 인프라 및 하드웨어 비용 기본값 |

> 이 기본값들은 나중에 관리자 UI(`/admin`)에서 수정할 수 있습니다.

### PostgreSQL 중지

```bash
make docker-down
```

---

## 6. 애플리케이션 실행

백엔드와 프론트엔드를 각각 별도의 터미널에서 실행합니다:

```bash
# 터미널 1 — 백엔드 (FastAPI)
make run
# → http://localhost:8000 에서 실행

# 터미널 2 — 프론트엔드 (Next.js)
cd frontend
npm run dev
# → http://localhost:3000 에서 실행
```

백엔드가 정상적으로 실행되고 있는지 확인합니다:

```bash
curl http://localhost:8000/health
```

브라우저에서 `http://localhost:3000`을 열어 애플리케이션에 접속합니다.

---

## 7. 프로덕션 배포

OathKeeper는 4개 서비스로 구성된 Docker Compose 프로덕션 설정을 제공합니다:

| 서비스 | 설명 |
|--------|------|
| **PostgreSQL 16** | 데이터베이스 |
| **Backend** | FastAPI + uvicorn |
| **Frontend** | Next.js 프로덕션 빌드 |
| **Nginx** | 리버스 프록시 (포트 80) |

### 빌드 및 실행

```bash
# 프로덕션 Docker 이미지 빌드
make docker-build

# 모든 서비스 시작
make docker-prod-up
```

애플리케이션은 `http://localhost` (포트 80)에서 접속할 수 있습니다.

### 중지

```bash
make docker-prod-down
```

---

> [English Version →](env-setting(en).md) · [← README로 돌아가기](../README(kr).md) · [사용 매뉴얼 →](manual(kr).md)
