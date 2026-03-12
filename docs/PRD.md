# OathKeeper PRD v1.1

**OathKeeper: B2B AI 개발 사업 Deal Go/No-Go 의사결정 지원 에이전트**

---

| 항목 | 내용 |
|---|---|
| 문서 버전 | v1.1 |
| 작성일 | 2026년 3월 10일 |
| 대상 독자 | 개발자, 경영진, 세일즈 팀 |

---

## 1. 프로젝트 개요

### 1.1 프로젝트 이름 및 한줄 설명

**OathKeeper** — 세일즈가 가져오는 B2B AI 개발 Deal을 AI 에이전트가 자동 분석하여 Go/No-Go 의사결정을 지원하는 서비스

### 1.2 해결하려는 문제

| 문제 | 현재 상황 | 결과 |
|---|---|---|
| 비일관적 판단 기준 | 구두 보고 기반, 사람마다 다른 기준 | 구성원 간 의견 충돌 |
| 리스크 분석 부재 | Deal 수락 후 수행 중 이슈 발생 | 추가 리소스 투입, 납기 지연 |
| 느린 의사결정 | 회의 조율 포함 3~5일 소요 | 영업 기회 손실 |

### 1.3 핵심 가치 제안

- **속도:** Deal 입력 후 24시간 이내 초기 분석 결과 제공
- **일관성:** 7개 표준 평가 기준으로 모든 Deal을 동일한 방식으로 평가
- **리스크 선제 대응:** 수행 전 잠재 리스크를 카테고리별로 식별·경고

---

## 2. 사용자 정의

### 2.1 주요 사용자

| 역할 | 설명 | 주요 니즈 |
|---|---|---|
| **경영진 / 의사결정권자** | OathKeeper를 통해 분석 결과를 보고 최종 판단 | 빠른 요약, 명확한 권고, 리스크 파악 |
| **관리자** | 회사 정보·평가 기준·인건비 단가 등 시스템 설정 | 평가 가중치 조정, 사례 DB 관리 |
| **세일즈 담당** | Notion에 Deal 정보 입력 | 입력 부담 최소화, 빠른 피드백 |

### 2.2 사용자별 접근 방식

- **경영진:** 대시보드에서 스코어카드 확인 → 상세 분석 리포트 열람 → 저장/공유
- **관리자:** 관리자 페이지에서 회사 정보, 평가 기준 가중치, 인력 단가 설정
- **세일즈 담당:** Notion DB에 Deal 정보 입력 (구조화 폼 또는 자유 텍스트/문서 업로드)

---

## 3. 핵심 기능 (MVP 범위)

### Must Have 기능 목록 및 우선순위

| 우선순위 | 기능 | 의존성 |
|:---:|---|---|
| 1 | Deal 정보 파싱 및 구조화 | Notion API 연동 |
| 2 | 자동 스코어링 및 Go/No-Go 판단 | Deal 구조화 완료 |
| 3 | 소요 인력·기간·예산 자동 산출 | 회사 규정 데이터 (Vector DB) |
| 4 | 리스크 요인 분석 및 경고 | Deal 구조화 완료 |
| 5 | 유사 프로젝트 검색 및 비교 | 프로젝트 수행 이력 Vector DB |
| 6 | 종합 판단 및 분석 리포트 생성 | 2~5번 기능 완료 |
| 7 | Notion 저장 | Notion API 연동 |
| 8 | 관리자 설정 페이지 | RDB (설정 저장) |

---

### 3.1 Deal 정보 파싱 및 구조화

세일즈가 다양한 형태로 입력한 Deal 정보를 파싱하여 구조화된 형태로 정리한다.

**입력 방식**

- Notion DB에 기록된 회의록, 메모 등 비구조화 텍스트
- 사용자가 OathKeeper UI에서 추가로 업로드하는 Word/PDF 문서
- OathKeeper UI의 자유 텍스트 입력창

**구조화 출력 항목**

| 필드명 | 설명 | 추출 방식 |
|---|---|---|
| `customer_name` | 고객사명 | LLM 추출 |
| `customer_size` | 고객사 규모 (대/중/소) | LLM 추출 |
| `customer_industry` | 산업군 | LLM 추출 |
| `project_summary` | 요청 배경, 목적, 기대 효과 | LLM 요약 |
| `tech_requirements` | 필요 기술 스택, 모델, 데이터 환경 | LLM 추출 |
| `expected_amount` | 예상 계약 금액 (원) | LLM 추출 |
| `deadline` | 요구 납기 | LLM 추출 |
| `payment_terms` | 결제 조건 | LLM 추출 |
| `special_notes` | 보안 요건, 특별 요구, 제약 조건 | LLM 추출 |
| `missing_fields` | 미입력/불명확 항목 목록 | LLM 판단 |

---

### 3.2 자동 스코어링 및 Go/No-Go 판단

7개 표준 평가 기준에 따라 Deal을 0~100점으로 자동 스코어링하고 종합 판단을 제시한다. 평가 시 회사의 사업 방향·전략 문서(Business Context)를 함께 참조한다.

**평가 기준 및 기본 가중치**

| # | 평가 기준 | 가중치 | 평가 항목 |
|:---:|---|:---:|---|
| 1 | 기술 적합성 | 20% | 자사 기술 스택으로 구현 가능한가? 추가 기술 학습 필요성은? |
| 2 | 리소스 가용성 | 15% | 현재 투입 가능한 인력/장비가 있는가? 타 프로젝트와 충돌은? |
| 3 | 수익성 | 20% | 예상 매출 대비 투입 비용이 적절한가? 목표 마진을 충족하는가? |
| 4 | 납기 리스크 | 15% | 고객 요구 일정이 현실적인가? 버퍼 기간이 충분한가? |
| 5 | 요구사항 명확성 | 10% | 고객의 요구사항이 구체적인가? 범위 변경 리스크는? |
| 6 | 전략적 가치 | 10% | 레퍼런스 확보, 신규 산업 진출, 기술 축적 등 장기적 가치 |
| 7 | 고객 리스크 | 10% | 고객사 지불 능력, 의사결정 구조, 과거 협업 이력 |

> 가중치 합계: 100%. 관리자 설정 페이지에서 조정 가능.

**각 기준별 점수 산출 방식**

각 항목을 LLM이 0~100점으로 평가한다. 종합 점수 = Σ(항목 점수 × 가중치).

```python
# 종합 점수 산출 예시
score = sum(criterion.score * criterion.weight for criterion in criteria)
```

**종합 판단 로직**

| 판단 | 조건 | 설명 |
|---|---|---|
| ✅ **Go** | 종합 70점 이상 | 수행 권고. 주요 리스크 요인 함께 제시 |
| ⚠️ **조건부 Go** | 종합 40~69점 | 조건 충족 시 수행. 해소 필요 항목 명시 |
| ❌ **No-Go** | 종합 40점 미만 | 수행 비권고. 주요 사유 및 대안 제시 |
| ℹ️ **보류** | 필수 평가 항목 중 미입력 존재 | 판단 보류. 추가 확인 필요 항목 안내 |

---

### 3.3 소요 인력·기간·예산 자동 산출

Deal의 기술 요구사항과 규모를 바탕으로 예상 투입 인력 구성, 기간, 소요 예산을 자동 계산한다. 회사 사업 방향·전략, 인건비 단가, 현재 인력 현황을 함께 참조한다.

**산출 항목**

| 항목 | 예시 출력 |
|---|---|
| 인력 구성 | PM 1명, Backend 2명, MLE 1명, Frontend 1명 |
| 예상 기간 | 3개월 (개발 2.5개월 + 버퍼 0.5개월) |
| 소요 예산 | 인건비 5,000만원, SW 라이센스 500만원, 총 5,500만원 |
| 예상 마진 | 계약금 7,000만원 기준 마진율 21.4% |

**산출 근거 표시:** 각 수치에 대해 "유사 프로젝트 평균 3개월 소요" 등 근거 문장 포함.

---

### 3.4 리스크 요인 분석 및 경고

Deal의 잠재적 리스크를 카테고리별로 식별하고 심각도에 따라 경고를 표시한다.

**리스크 카테고리**

- **기술 리스크:** 미경험 기술, 높은 구현 복잡도, 데이터 품질 이슈 등
- **일정 리스크:** 촉박한 납기, 불명확한 마일스톤, 병렬 작업 불가 등
- **재무 리스크:** 낮은 마진, 불명확한 결제 조건, 추가 비용 발생 가능성 등
- **고객 리스크:** 의사결정 지연 가능성, 요구사항 변경 빈도, 지불 안정성 등
- **범위 리스크:** Scope creep 가능성, 모호한 성공 기준, 암묵적 추가 요구 등

**경고 레벨**

| 레벨 | 기준 | 표시 |
|---|---|---|
| 높음 | 미해결 시 프로젝트 실패 가능성 | 🔴 |
| 중간 | 추가 비용 또는 일정 지연 가능성 | 🟡 |
| 낮음 | 관리 가능한 수준 | 🟢 |

**출력 예시**

```json
{
  "risks": [
    {
      "category": "기술 리스크",
      "item": "LLM fine-tuning 경험 부재",
      "level": "HIGH",
      "description": "요구사항에 커스텀 모델 학습이 포함되어 있으나 자사 MLE팀의 fine-tuning 경험 없음",
      "mitigation": "외부 전문가 서브컨트랙 또는 pre-trained 모델 활용 방안 검토 필요"
    }
  ]
}
```

---

### 3.5 유사 프로젝트 검색 및 비교

과거 수행 프로젝트 이력(Vector DB)을 기반으로 유사 사례를 검색하고, 결과와 교훈을 함께 제공한다.

**유사도 산출 기준:** 산업군, 기술 스택, 프로젝트 규모, 고객 유형을 임베딩하여 코사인 유사도로 Top 3 추출

**비교 제공 정보**

| 항목 | 내용 |
|---|---|
| 유사도 점수 | 0~100% |
| 실제 투입 리소스 | 계획 대비 실제 인력·기간 |
| 최종 결과 | 성공 / 부분 성공 / 실패 / 초과 |
| Lessons Learned | 발생한 이슈와 해결 방법 |

---

### 3.6 종합 판단 및 분석 리포트 생성

3.1~3.5의 분석 결과를 종합하여 화면에 표시하고, 경영진 보고용 완결 문서를 생성한다.

**리포트 포함 항목**

1. Deal 개요 요약
2. 종합 점수 및 Go/No-Go 판단
3. 평가 기준별 점수 및 근거
4. 소요 인력·기간·예산 산출 결과
5. 리스크 요인 목록 (카테고리별)
6. 유사 프로젝트 Top 3 비교
7. 권고 사항 (조건부 Go의 경우 해소 조건 명시)

---

### 3.7 Notion 저장

사용자가 분석 결과를 확인한 후 저장 요청 시, Notion의 해당 Deal 페이지에 분석 결과를 기록한다.

- 기존 Deal 페이지에 분석 결과 섹션 추가
- 저장 전 사용자 확인(미리보기) 제공
- 저장 완료 시 Slack Webhook으로 알림 전송

---

### 3.8 관리자 설정

관리자가 의사결정에 필요한 기준 데이터를 등록·수정한다.

**설정 가능 항목**

| 설정 항목 | 설명 |
|---|---|
| 회사 사업 방향 | 사업 영역, 범위, 단기/중기/장기 전략 |
| Deal 선정 기준 | 최소 마진율, 선호 산업군, 기술 스택 등 |
| 인건비 단가 | 직군별 월 단가 (PM, FE, BE, MLE 등) |
| HW/SW/라이선스 비용 | 자주 사용하는 비용 항목 등록 |
| 인력 현황 | 현재 가용 인력 및 각 인력의 프로젝트 할당 현황 |
| 평가 기준 가중치 | 7개 항목의 가중치 (합계 100% 검증) |
| 과거 프로젝트 수행 사례 | 프로젝트 이력 등록 (Vector DB 업데이트) |

---

## 4. 기술 스택

| 구분 | 기술 | 비고 |
|---|---|---|
| LLM | OpenAI GPT-4o / Claude Sonnet | 용도별 최적 모델 선택 (A/B 테스트) |
| Backend | Python (FastAPI) | LLM 연동 및 Agent 오케스트레이션 |
| Agent | Langchain, Langgraph | RAG, Agent 워크플로우 설계 |
| Vector DB | Pinecone | 과거 프로젝트 유사도 검색용 |
| RDB | PostgreSQL | 평가 결과, 설정, 사용자 데이터 저장 |
| Frontend | Nextjs, TailwindCSS v4 + shadcn/ui | 사용자 입출력, 분석 결과, 관리화면 등 |
| Input 연동 | Notion API | MVP 기준. 향후 HubSpot API 추가 |

---

## 5. 시스템 아키텍처

### 5.1 데이터 흐름

```
[세일즈 담당]
    │  Notion DB에 Deal 정보 입력
    ▼
[Notion DB] ──Notion API──► [Backend: Input Parser]
                                    │
[경영진/사용자]                      │ 문서 업로드 / 추가 텍스트
    │                               │
    ▼                               ▼
[Frontend: 사용자 입력] ────────► [Orchestrator Agent]
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                      ▼
    [Deal 구조화 Agent]   [스코어링 Agent]    [리스크 분석 Agent]
              │                     │                      │
              ▼                     ▼                      ▼
    [소요 산출 Agent]     [유사사례 검색 Agent]  [종합 판단 Agent]
              │                     │                      │
              └─────────────────────┴──────────────────────┘
                                    │
                              [결과 종합]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             [Frontend         [Notion API     [Slack
              Dashboard]        저장]           Webhook]
```

### 5.2 에이전트 구성 및 역할

| 에이전트 | 역할 | 입력 | 출력 |
|---|---|---|---|
| **Orchestrator** | 전체 분석 흐름 조율, 하위 에이전트 호출 | Deal 원문, 사용자 추가 입력 | 분석 완료 신호 |
| **Deal 구조화 Agent** | Notion/문서/텍스트에서 구조화 필드 추출 | 비구조화 텍스트 | 구조화 JSON |
| **스코어링 Agent** | 7개 기준으로 점수 산출 및 Go/No-Go 판단 | 구조화 Deal + Business Context | 점수 JSON, 판단 결과 |
| **소요 산출 Agent** | 인력·기간·예산 계산 | 구조화 Deal + 회사 규정 | 산출 결과 JSON |
| **리스크 분석 Agent** | 카테고리별 리스크 식별 및 경고 레벨 분류 | 구조화 Deal | 리스크 목록 JSON |
| **유사사례 검색 Agent** | Vector DB에서 유사 프로젝트 Top 3 검색 | Deal 임베딩 벡터 | 유사 사례 목록 |
| **종합 판단 Agent** | 전체 결과 종합, 리포트 텍스트 생성 | 모든 에이전트 출력 | 최종 리포트 마크다운 |

### 5.3 Business Context 구성

에이전트가 분석 시 참조하는 회사 맥락 정보:

- **System Prompt:** 회사 사업 방향, 전략, Deal 선정 기준 (관리자 설정 → RDB 저장 → 매 분석 시 System Prompt에 삽입)
- **Vector DB (회사 정보):** 인건비 단가, HW/SW 비용, 인력 현황 등 정량 데이터
- **Vector DB (프로젝트 수행 실적):** 과거 프로젝트 이력 (유사 사례 검색용)

### 5.4 페이지 라우팅 구조

```
/                   → 사용자 입력 페이지 (Deal 분석 요청)
/deals              → Deal 현황 페이지 (분석 이력 목록)
/deals/:id          → Deal 상세 분석 결과 페이지
/admin              → 관리자 설정 페이지
```

---

## 6. 데이터 모델

### 6.1 RDB 스키마 (PostgreSQL)

```sql
-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'executive', 'sales')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deal 분석 요청
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notion_page_id VARCHAR(255),          -- Notion 연동 ID (없으면 NULL)
    title VARCHAR(500) NOT NULL,
    raw_input TEXT,                       -- 원문 입력 (자유 텍스트)
    structured_data JSONB,                -- 구조화 결과 JSON
    status VARCHAR(20) DEFAULT 'pending'  -- pending | analyzing | completed | failed
        CHECK (status IN ('pending', 'analyzing', 'completed', 'failed')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 분석 결과
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    total_score NUMERIC(5,2),             -- 0.00 ~ 100.00
    verdict VARCHAR(20)                   -- go | conditional_go | no_go | pending
        CHECK (verdict IN ('go', 'conditional_go', 'no_go', 'pending')),
    scores JSONB,                         -- 항목별 점수 {criterion: score, ...}
    resource_estimate JSONB,              -- 인력·기간·예산 산출 결과
    risks JSONB,                          -- 리스크 목록 [{category, item, level, ...}]
    similar_projects JSONB,               -- 유사 사례 Top 3
    report_markdown TEXT,                 -- 최종 리포트 원문
    notion_saved_at TIMESTAMPTZ,          -- Notion 저장 완료 시각 (NULL이면 미저장)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 평가 기준 설정 (관리자 설정)
CREATE TABLE scoring_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,           -- 예: '기술 적합성'
    weight NUMERIC(4,3) NOT NULL,         -- 0.000 ~ 1.000 (합계 = 1.000)
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 회사 설정 (Business Context)
CREATE TABLE company_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- 예시 key: 'business_direction', 'deal_criteria', 'short_term_strategy', etc.

-- 인력 현황
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,            -- PM | FE | BE | MLE | DevOps
    monthly_rate INT NOT NULL,            -- 월 단가 (원)
    is_available BOOLEAN DEFAULT TRUE,
    current_project VARCHAR(255),         -- 현재 투입 프로젝트 (없으면 NULL)
    available_from DATE                   -- 가용 시작일
);
```

### 6.2 Vector DB 스키마 (Pinecone)

**인덱스 1: `company-context`** (회사 정보 - 단가, 전략, 규정 문서)

```python
# Vector 메타데이터 구조
{
    "id": "company-context-{hash}",
    "values": [...],  # 임베딩 벡터 (1536-dim, text-embedding-3-small)
    "metadata": {
        "type": "cost_table | strategy | regulation | tech_stack",
        "content": "...",     # 원문 텍스트 (검색 결과 반환용)
        "updated_at": "2026-03-10"
    }
}
```

**인덱스 2: `project-history`** (과거 프로젝트 수행 실적)

```python
{
    "id": "project-{uuid}",
    "values": [...],  # 임베딩 벡터
    "metadata": {
        "project_name": "...",
        "industry": "금융 | 제조 | 유통 | ...",
        "tech_stack": ["FastAPI", "LangChain", "GPT-4o"],
        "scale": "small | medium | large",        # 계약금 기준
        "duration_months": 3,
        "planned_headcount": 4,
        "actual_headcount": 5,
        "result": "success | partial | failed | overrun",
        "lessons_learned": "...",
        "contract_amount": 70000000,
        "summary": "..."                          # 검색 결과 표시용 요약
    }
}
```

### 6.3 Notion 데이터베이스 구조

OathKeeper는 2개의 Notion DB를 사용한다.

**DB 1: deal information** (세일즈 담당 입력 — OathKeeper가 읽기)

| Notion 속성명 | 타입 | OathKeeper 매핑 | 비고 |
|---|---|---|---|
| `deal_info` | Title | 고객사 + 프로젝트명 | 예: "xx 철강 AI 비전 프로젝트" |
| `customer_name` | Text | `customer_name` | API 필터/검색용 |
| `expected_amount` | Number | `expected_amount` | 예상 계약 금액 (원) |
| `deadline` | Date | `deadline` | 요구 납기 |
| `date` | Date | 입력일 | |
| `author` | Person | `created_by` (담당 세일즈) | |
| `status` | Select | 분석 상태 | `미분석` / `분석중` / `완료` |

> `project_summary`, `tech_requirements`, `special_notes` 등 상세 정보는 **페이지 본문(content)**에 자유 텍스트/회의록으로 작성. LLM이 본문을 파싱하여 구조화 필드를 추출한다.

**DB 2: ai decision** (OathKeeper가 분석 결과 저장)

| Notion 속성명 | 타입 | OathKeeper 매핑 | 비고 |
|---|---|---|---|
| `report` | Title | 분석 리포트 제목 | 예: "xx 철강 분석 결과" |
| `decision` | Select | `verdict` | `Go` / `Conditional Go` / `No-Go` / `Hold` |
| `deal` | Relation | deal information 연결 | page_id 기반, 1:N 관계 |
| `total_score` | Number | `total_score` | 종합 점수 (0~100) |
| `analysis_date` | Date | 분석 완료 시각 | 자동 기록 |

> 상세 분석 내용(항목별 점수, 리스크 목록, 소요 산출, 권고사항, 마크다운 리포트)은 **페이지 본문(content)**에 작성한다.

**두 DB 간 관계:**
- `ai decision.deal` → `deal information` Relation (양방향)
- 하나의 Deal에 대해 재분석 시 ai decision에 새 레코드 생성 (1:N)
- deal information에 Rollup 속성 추가로 최신 판단 결과 자동 표시 가능

---

## 7. UI/UX 요구사항

총 4개 페이지로 구성. React + TailwindCSS v4 + shadcn/ui.

### 7.1 페이지 1: 사용자 입력 페이지 (`/`)

**목적:** 경영진/사용자가 분석할 Deal을 선택하고 분석을 요청하는 메인 페이지.

**레이아웃 구성**

```
┌─────────────────────────────────────────────────┐
│  OathKeeper                          [관리자] [?] │
├─────────────────────────────────────────────────┤
│                                                 │
│  Deal 분석 요청                                   │
│                                                 │
│  [Notion Deal 선택 드롭다운 ▼]                    │
│  → Notion DB에서 최근 Deal 목록 불러오기           │
│                                                 │
│  추가 정보 (선택사항)                              │
│  ┌─────────────────────────────────────────┐   │
│  │ 보충 설명, 추가 요청사항 자유 입력...         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  문서 업로드 (선택사항)                            │
│  [📎 Word / PDF 파일 첨부]                        │
│                                                 │
│                    [분석 시작]                    │
│                                                 │
│  분석 중 상태 표시 (스피너 + 단계별 진행 메시지)     │
│  예: "Deal 정보 파싱 중..." → "스코어링 중..." 등   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**인터랙션**
- Notion Deal 선택 시 Deal 제목과 입력일 표시
- 분석 시작 클릭 → 진행 상태를 단계별로 실시간 표시 (SSE 또는 polling)
- 분석 완료 시 자동으로 상세 결과 페이지로 이동

---

### 7.2 페이지 2: Deal 현황 페이지 (`/deals`)

**목적:** 분석 완료된 Deal 이력 목록을 보여주는 대시보드.

**레이아웃 구성**

```
┌─────────────────────────────────────────────────┐
│  OathKeeper                  [+ 새 분석] [관리자] │
├─────────────────────────────────────────────────┤
│  [검색창]  [필터: 판단결과 ▼]  [필터: 기간 ▼]      │
├─────────────────────────────────────────────────┤
│  고객사        판단    점수  생성일     담당자       │
│  ─────────────────────────────────────────────  │
│  ABC Corp    ✅ Go    82점  2026-03-09  김세일   │
│  DEF Corp   ⚠️ 조건부  61점  2026-03-07  이세일   │
│  GHI Corp   ❌ No-Go  31점  2026-03-05  박세일   │
│  ...                                            │
└─────────────────────────────────────────────────┘
```

- 각 행 클릭 시 상세 결과 페이지(`/deals/:id`)로 이동

---

### 7.3 페이지 3: Deal 상세 분석 결과 페이지 (`/deals/:id`)

**목적:** 하나의 Deal에 대한 전체 분석 결과를 시각적으로 표시.

**레이아웃 구성 (상단 → 하단 순)**

```
┌─────────────────────────────────────────────────┐
│  ← 목록으로   ABC Corp — AI 추천 시스템 개발       │
├──────────────────────┬──────────────────────────┤
│ 종합 점수            │ Deal 개요                  │
│   82점               │ 고객사: ABC Corp (대기업)  │
│  ✅ GO               │ 계약금: 1.5억원             │
│                      │ 납기: 2026-06-30           │
│ [레이더 차트]         │ 기술: RAG, GPT-4o, FastAPI │
├──────────────────────┴──────────────────────────┤
│ 평가 기준별 점수                                   │
│ 기술 적합성  ████████░░  85점                     │
│ 수익성      ███████░░░  78점                     │
│ ...                                             │
├─────────────────────────────────────────────────┤
│ 소요 인력·기간·예산                                │
│ PM 1명 + BE 2명 + MLE 1명 | 3개월 | 총 5,500만원  │
├─────────────────────────────────────────────────┤
│ 리스크 분석                                       │
│ 🔴 기술 리스크: LLM fine-tuning 경험 부재          │
│ 🟡 일정 리스크: MVP 납기 촉박 (버퍼 2주)           │
│ 🟢 고객 리스크: 결제 조건 안정적                   │
├─────────────────────────────────────────────────┤
│ 유사 프로젝트                                     │
│ 1. XYZ Corp 챗봇 (유사도 89%) — 성공 / 3개월      │
│ 2. ...                                          │
├─────────────────────────────────────────────────┤
│ 권고 사항                                         │
│ "Go 권고. 단, MLE fine-tuning 리스크 대비책 필요." │
├─────────────────────────────────────────────────┤
│         [Notion에 저장]      [닫기]               │
└─────────────────────────────────────────────────┘
```

---

### 7.4 페이지 4: 관리자 설정 페이지 (`/admin`)

**목적:** 회사 정보, 평가 기준, 인력 현황 등 시스템 설정 관리.

**탭 구성**

| 탭 | 설정 항목 |
|---|---|
| 회사 정보 | 사업 방향, 단기/중기/장기 전략, Deal 선정 기준 |
| 평가 기준 | 7개 항목 가중치 조정 (슬라이더, 합계 100% 실시간 검증) |
| 인력 관리 | 팀원 등록/수정, 월 단가, 현재 투입 프로젝트 |
| 비용 설정 | HW/SW/라이선스 비용 항목 등록 |
| 프로젝트 이력 | 과거 수행 프로젝트 등록 (Vector DB 업데이트) |

### 7.5 반응형 디자인

- 기준 해상도: 1280px 이상 (경영진 데스크탑/노트북 환경 최적화)
- 모바일(768px 이하): 사용자 입력 페이지와 Deal 현황 페이지만 간소화 지원

---

## 8. 프롬프트 관리 / 구성

### 8.1 System Prompt 구조

모든 에이전트 호출 시 공통 System Prompt에 Business Context를 포함한다.

```
[System Prompt 구성]
1. 역할 정의: "당신은 B2B AI 개발 Deal 평가 전문가입니다."
2. 회사 사업 방향 및 전략 (company_settings에서 동적 삽입)
3. Deal 선정 기준 (company_settings에서 동적 삽입)
4. 평가 기준 및 가중치 (scoring_criteria에서 동적 삽입)
5. 출력 형식 지정 (JSON Schema)
```

### 8.2 에이전트별 프롬프트 역할

| 에이전트 | 프롬프트 핵심 지시 |
|---|---|
| Deal 구조화 | "아래 텍스트에서 지정된 필드를 추출하라. 없으면 null, 불명확하면 `missing_fields`에 추가하라." |
| 스코어링 | "각 평가 기준별로 0~100점을 부여하고, 판단 근거를 한 문장으로 기술하라. 반드시 JSON으로 반환하라." |
| 소요 산출 | "회사 인건비 단가와 과거 유사 프로젝트 기간을 참고하여 투입 인력과 예산을 산출하라." |
| 리스크 분석 | "각 리스크 항목의 심각도(HIGH/MEDIUM/LOW)와 구체적 사유, 완화 방안을 함께 제시하라." |
| 종합 판단 | "모든 분석 결과를 바탕으로 경영진이 바로 읽을 수 있는 분석 리포트를 마크다운으로 작성하라." |

### 8.3 프롬프트 버전 관리

- 프롬프트 텍스트는 코드베이스 내 `configs/prompts/` 디렉터리에 `.yaml` 파일로 관리
- RDB의 `company_settings`에서 동적으로 삽입되는 값은 Jinja2 템플릿으로 처리
- 프롬프트 변경 시 Git commit으로 이력 추적

---

## 9. MVP 제외 사항

### 9.1 향후 버전에서 고려할 기능

| 기능 | 제외 사유 | 예상 버전 |
|---|---|---|
| HubSpot API 연동 | Notion API만으로 MVP 충분 | v2.0 |
| PDF 리포트 자동 생성 (다운로드) | 마크다운 리포트로 대체 | v2.0 |
| 다국어 지원 | 초기 사용자 전원 한국어 | v2.0 |
| A/B 테스트 (GPT-4o vs Claude) | 단일 모델로 시작 | v1.5 |
| 이메일 알림 | Slack Webhook으로 대체 | v2.0 |
| Deal 협상 시나리오 시뮬레이션 | 분석만으로 MVP 충분 | v3.0 |
| 모바일 앱 | 웹 브라우저로 대체 | v3.0 |

### 9.2 의도적으로 제외한 기능

- **최종 의사결정 자동화:** OathKeeper는 의사결정 지원 도구이며, 최종 판단은 경영진이 내린다. 자동 승인/거절 기능은 범위 외.
- **고객사 직접 접근:** 내부 임직원 전용 서비스. 고객사 포털 기능 제외.
- **실시간 협업:** 동시 편집, 코멘트 등 협업 기능 제외. 분석 결과 공유는 Slack 알림과 Notion 저장으로 대체.

---

## 10. 성공 지표

### 10.1 MVP 완료 기준

| 항목 | 기준 |
|---|---|
| 기능 완성도 | 3.1~3.8 전체 기능 동작 확인 |
| 엔드투엔드 테스트 | 실제 Deal 5건 이상 분석 완료 |
| 응답 시간 | Deal 분석 전체 소요 시간 3분 이내 |
| 오류율 | 분석 실패율 5% 이하 |

### 10.2 측정 가능한 목표 (파일럿 1개월 기준)

| KPI | 현재 (As-Is) | MVP 목표 |
|---|---|---|
| Deal 초기 분석 소요 시간 | 3~5일 | 24시간 이내 |
| 실제 분석 Deal 수 | - | 월 5건 이상 |
| 사용자 만족도 (설문) | - | 4점 이상 / 5점 만점 |
| 분석 결과 활용률 | - | 경영진이 분석 리포트를 의사결정에 활용한 비율 80% 이상 |

---

## Appendix: 용어 정의

| 용어 | 정의 |
|---|---|
| Deal | 고객사로부터 받은 AI 개발 사업 요청 건 |
| Go/No-Go | Deal 수행 여부에 대한 의사결정 |
| Business Context | 회사 사업 방향, 전략, 규정 등 에이전트 분석 시 참조하는 내부 데이터 |
| Scorecard | 평가 기준별 점수와 종합 판단을 시각적으로 표시한 보고서 |
| Vector DB | 텍스트의 의미적 유사성으로 검색하는 데이터베이스 |
| Scope Creep | 프로젝트 진행 중 요구사항이 점진적으로 확대되는 현상 |
| Orchestrator | 여러 하위 에이전트를 조율하는 최상위 에이전트 |

---

*— End of Document —*
