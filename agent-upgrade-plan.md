# OathKeeper Agent System 고도화 계획

## Hybrid Orchestrator + ReAct Workers 아키텍처

### Context

OathKeeper의 현재 에이전트 시스템은 정적 LangGraph DAG 워크플로우로 구현되어 있다. 각 노드는 1회 LLM 호출(text-in/text-out)만 수행하며, Tool calling, ReAct 패턴, 동적 라우팅이 없다. 이로 인해:
- LLM이 자율적으로 추가 정보를 수집하거나 판단을 재검토할 수 없음
- 모든 분석 노드가 항상 고정 순서로 실행됨 (불필요한 분석 스킵 불가)
- 경계값 결과에 대한 심층 분석 재시도 불가

**목표:** LangGraph를 유지하면서 ReAct + Tool calling을 도입하여 분석 품질과 워크플로우 유연성을 동시에 향상

**접근:** Hybrid 아키텍처 — Orchestrator Agent가 분석 전략을 수립/조정하고, ReAct Worker 서브그래프가 도메인별 깊이 있는 분석을 수행

---

## Phase 1: Tool 시스템 구축 (`agent/tools/`)

### 1.1 내부 데이터 Tools (`data_tools.py`)

- [x] `search_similar_projects` — Pinecone 벡터 검색 (`ProjectHistoryStore.query()` 재활용)
- [x] `search_company_context` — 회사 컨텍스트 벡터 검색 (`CompanyContextStore.query()` 재활용)
- [x] `get_team_members` — 팀원 정보 조회 (`settings_repo` 재활용)
- [x] `get_scoring_criteria` — 평가 기준/가중치 조회 (`settings_repo` 재활용)
- [x] `get_company_settings` — 회사 설정 조회 (`settings_repo` 재활용)
- [x] `get_past_deal_analysis` — 과거 딜 분석 결과 조회 (`analysis_repo` 재활용)

### 1.2 외부 API Tools (`external_tools.py`)

- [x] `web_search` — 시장/기술 동향, 경쟁사 정보 검색
- [x] `fetch_notion_deal` — Notion에서 딜 상세 정보 조회

### 1.3 계산/추론 Tools (`calculation_tools.py`)

- [x] `calculate_roi` — ROI, 손익분기점, 수익성 계산
- [x] `calculate_weighted_score` — 가중 점수 계산 (LLM 산술 신뢰 방지)
- [x] `estimate_timeline` — 일정 시뮬레이션 (리소스 대비 기간 추정)
- [x] `assess_risk_matrix` — 리스크 확률×영향도 매트릭스 계산

### 1.4 유틸리티 Tools (`utils_tools.py`)

- [x] `format_currency` — 금액 단위 변환 (만원/억원)
- [x] `current_date` — 현재 날짜 반환

### 1.5 Tool 단위 테스트

- [x] 각 Tool의 Pydantic 스키마 및 반환값 검증 테스트 작성

**구현 방식:** LangChain `@tool` 데코레이터 + Pydantic 스키마. 기존 `base.py` 헬퍼와 repository 계층 내부 재활용.

---

## Phase 2: ReAct Worker 서브그래프 (`agent/workers/`)

### 2.1 공통 Worker 빌더

- [x] `base_worker.py` — `make_react_worker(name, tools, system_prompt, max_iterations)` 팩토리 함수 구현
  - LangGraph `create_react_agent()` 또는 커스텀 reason→act→observe 루프
  - `WorkerState` (messages + context + result) 사용
  - max_iterations 안전장치 (기본 5~8회)
  - 각 ReAct step을 AgentLog에 기록하는 로깅 통합

### 2.2 Worker별 구현

| Worker | 전용 Tools | ReAct 시나리오 |
|--------|-----------|---------------|
| deal_structuring | search_company_context, fetch_notion_deal, format_currency | 부족한 정보 자율 보완 |
| scoring | get_scoring_criteria, search_company_context, calculate_weighted_score, search_similar_projects | 유사 프로젝트 비교 기반 점수 산정 |
| resource_estimation | get_team_members, get_company_settings, search_similar_projects, estimate_timeline, calculate_roi | ROI 계산 후 구성 재조정 |
| risk_analysis | search_company_context, web_search, assess_risk_matrix, search_similar_projects | 외부 정보 기반 리스크 재평가 |
| similar_project | search_similar_projects, get_past_deal_analysis, search_company_context | 과거 성공/실패 요인 추출 |
| final_verdict | calculate_weighted_score, calculate_roi | 최종 점수 검증 + 전략적 권고 |

- [x] `deal_structuring.py` — deal structuring worker 구현
- [x] `scoring.py` — scoring worker 구현
- [x] `resource_estimation.py` — resource estimation worker 구현
- [x] `risk_analysis.py` — risk analysis worker 구현
- [x] `similar_project.py` — similar project worker 구현
- [x] `final_verdict.py` — final verdict worker 구현

### 2.3 기존 노드 마이그레이션

- [x] `nodes/*.py`의 프롬프트 렌더링, JSON 파싱, 에러 핸들링 로직을 `workers/*.py`로 이전
- [x] `configs/prompts/*.yaml`을 Worker 시스템 프롬프트의 도메인 컨텍스트로 재활용

### 2.4 Worker 단위 테스트

- [x] 각 Worker가 mock Tool로 ReAct 루프를 정상 수행하는지 검증
- [x] max_iterations 안전장치 동작 검증

---

## Phase 3: Orchestrator 에이전트 (`agent/orchestrator/`)

### 3.1 Orchestrator Agent (`agent.py`)

- [x] LangGraph `create_react_agent()` 기반 최상위 에이전트 구현
- [x] `OrchestratorState` 사용 (messages 기반 ReAct 이력 관리)
- [x] max_iterations = 10~15
- [x] 시스템 프롬프트 설계: OathKeeper 평가 프레임워크, 판정 기준, 분석 전략 가이드라인

### 3.2 Meta-Tools (`tools.py`)

- [x] `run_deal_structuring` — deal_structuring_worker 실행
- [x] `run_scoring_analysis` — scoring_worker 실행
- [x] `run_risk_analysis` — risk_worker 실행
- [x] `run_resource_estimation` — resource_worker 실행
- [x] `run_similar_project_search` — similar_project_worker 실행
- [x] `run_final_verdict` — final_verdict_worker 실행
- [x] `search_company_context` — 빠른 컨텍스트 조회 (직접 호출)

### 3.3 동작 흐름

```
1. [PLAN] 딜 입력 분석 → 분석 전략 수립
2. [EXECUTE Phase 1] run_deal_structuring → 구조화 데이터 수신, Hold 판단
3. [EXECUTE Phase 2] 병렬/선택적 워커 호출 (필요한 분석만 실행)
4. [REFLECT] 중간 결과 검토 → 동적 판단
   - 경계값 점수 → 심층 재분석
   - 높은 리스크 → 실패 사례 중심 재조사
   - 비현실적 추정 → 재추정 요청
5. [SYNTHESIZE] run_final_verdict → 최종 보고서
```

### 3.4 Orchestrator 테스트

- [ ] Orchestrator → Worker → Tool 전체 파이프라인 통합 테스트 (유닛 테스트 완료, 통합 테스트 미완)
- [ ] 실제 LLM API를 사용한 Tool calling 정상 동작 확인

---

## Phase 4: State 설계 및 기존 코드 수정

### 4.1 State 변경 (`state.py`)

- [x] `OrchestratorState` 정의 추가 (`AnalysisContext` dataclass로 대체 구현)

```python
class OrchestratorState(TypedDict, total=False):
    deal_id: str
    deal_input: str
    messages: Annotated[list[BaseMessage], add_messages]
    structured_deal: dict
    scores: list[dict]
    total_score: float
    verdict: str
    resource_estimate: dict
    risks: list[dict]
    risk_interdependencies: list[dict]
    similar_projects: list[dict]
    final_report: str
    status: str
    errors: Annotated[list[str], operator.add]
    analysis_plan: str
    iteration_count: int
```

- [x] `WorkerState` 정의 추가 (Phase 2에서 `workers/base_worker.py`에 구현 완료)

```python
class WorkerState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict
    result: dict
```

### 4.2 기존 파일 수정

- [x] `llm.py` — bind_tools 지원 (`create_react_agent`가 내부 처리, 별도 수정 불필요)
- [x] `base.py` — ReAct step별 로깅 유틸리티 추가 (Phase 2 `WorkerLogCallback`으로 구현)
- [x] `graph.py` — 오케스트레이터 그래프 빌드로 재구성
- [x] `service.py` — 오케스트레이터 실행 흐름 적용, 확장 로깅/스트리밍

---

## Phase 5: 백엔드 AgentLog 모델 확장

### 5.1 AgentLog 모델 필드 추가 (`backend/app/db/models/agent_log.py`)

- [x] `parent_log_id` (UUID, nullable, self FK) — Orchestrator→Worker→Step 계층 구조
- [x] `step_type` (String/Enum) — `orchestrator_decision`, `worker_start`, `reasoning`, `tool_call`, `observation`, `worker_result`
- [x] `step_index` (Integer, nullable) — Worker 내 ReAct 루프 순서
- [x] `tool_name` (String, nullable) — Tool call step에서 사용된 도구명
- [x] `worker_name` (String, nullable) — Worker 식별자

### 5.2 스키마 및 API 수정

- [x] `AgentLogResponse` 스키마에 신규 필드 추가 (`backend/app/api/schemas/`)
- [x] `agent_logs` 라우터에서 계층적 응답 지원 (선택적 tree 구조 반환)
- [x] Alembic 마이그레이션 파일 생성

---

## Phase 6: 프론트엔드 수정

### 6.1 타입 업데이트 (`frontend/src/lib/api/types.ts`)

- [x] `AgentLogResponse`에 신규 필드 추가: `parent_log_id`, `step_type`, `step_index`, `tool_name`, `worker_name`, `children`

### 6.2 LogTimeline 재설계 (`frontend/src/app/deals/[id]/logs/_components/log-timeline.tsx`)

- [x] 하드코딩된 3-phase 레이아웃 제거 (`PARALLEL_NODES`, `NODE_LABELS` 등)
- [x] 동적 트리 기반 렌더러로 교체:
  - 1단계: Orchestrator 판단 (어떤 Worker를 왜 호출했는지)
  - 2단계: Worker 실행 (각각의 duration, status)
  - 3단계: Worker 내 ReAct step (reasoning → tool_call → observation 사이클)

### 6.3 LogNodeCard 확장 (`frontend/src/app/deals/[id]/logs/_components/log-node-card.tsx`)

- [x] `step_type` 기반 카드 변형 구현:
  - Orchestrator 판단 카드 (분석 전략, Worker 선택 이유)
  - Worker 카드 (접기/펼치기, 하위 ReAct step 포함)
  - Tool call 카드 (도구명, 입력 파라미터, 출력/관찰 결과)
  - Reasoning 카드 (LLM 사고 과정 표시)
- [x] 동적 라벨링 시스템 (하드코딩된 7개 → Worker/Tool 이름 기반)

### 6.4 AnalysisProgress 개선 (선택사항)

- [x] `current_step`에 Worker 진행 상황 표시 (예: "Scoring Worker: 3/5 - 계산 도구 호출 중")

---

## Phase 7: 통합 및 검증

### 7.1 통합 테스트

- [x] 기존 분석 결과와 품질 비교 (동일 딜 데이터로 테스트)
- [x] `@pytest.mark.integration` 패턴 따름

### 7.2 E2E 테스트

- [x] `POST /api/deals/{id}/analyze` → SSE 진행 상태 → 분석 결과 조회
- [x] AgentLog에 ReAct step별 로그 기록 확인
- [x] 프론트엔드 로그 뷰어에서 확장된 로그 표시 확인 (Playwright E2E: Hold/다중Worker/Legacy 포맷 포함)

### 7.3 수동 검증

자동화된 E2E 테스트 (`tests/e2e/test_deal_scenarios.py`, `tests/e2e/test_agent_logs.py`):

- [x] 명확한 Go 딜 시나리오 테스트 (자동화)
- [x] 경계값 딜 시나리오 테스트 + Orchestrator 로그 계층 검증 (자동화)
- [x] No-Go 딜 시나리오 테스트 (자동화)
- [x] Hold 딜 시나리오 테스트 (자동화)
- [x] Tool calling 로그 ReAct 순서 검증 (자동화)

UI 수동 QA 체크리스트 (자동화 범위 밖):

- [ ] Go 딜: 분석 결과 페이지에서 점수/리스크/리소스/유사 프로젝트 모두 표시
- [ ] 경계값 딜: 로그 뷰어에서 Orchestrator 재분석 판단 과정 확인
- [ ] No-Go 딜: verdict "no_go", 보고서에 근거 포함
- [ ] Hold 딜: 로그 뷰어에 Worker 없이 orchestrator만 표시
- [ ] Tool calling: 로그 뷰어에서 도구명, 입력/출력 확인 가능

### 7.4 레거시 정리

- [x] 기존 `nodes/` 디렉토리 삭제 완료 (프로덕션 코드에서 import 없음 확인)
- [x] 레거시 노드 단위 테스트 5개 삭제 완료

---

## 파일 구조 변경 요약

```
backend/app/agent/
├── graph.py                    # [수정] 오케스트레이터 그래프 빌드
├── state.py                    # [수정] OrchestratorState, WorkerState 추가
├── base.py                     # [수정] ReAct 로깅 유틸리티 추가
├── llm.py                      # [수정] bind_tools 지원 추가
├── service.py                  # [수정] 오케스트레이터 실행 흐름 적용
├── prompt_loader.py            # [유지]
├── tools/                      # [신규]
│   ├── __init__.py
│   ├── data_tools.py
│   ├── external_tools.py
│   ├── calculation_tools.py
│   └── utils_tools.py
├── workers/                    # [신규]
│   ├── __init__.py
│   ├── base_worker.py
│   ├── deal_structuring.py
│   ├── scoring.py
│   ├── resource_estimation.py
│   ├── risk_analysis.py
│   ├── similar_project.py
│   └── final_verdict.py
├── orchestrator/               # [신규]
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
└── nodes/                      # [단계적 폐기] 마이그레이션 완료 후 제거
```

### 기존 코드 재활용 매핑

| 기존 코드 | 재활용 위치 |
|-----------|-----------|
| `nodes/*.py` 비즈니스 로직 | `workers/*.py` |
| `base.py` `logged_call_llm` | `base.py` 확장 (ReAct step 로깅) |
| `base.py` formatting 헬퍼 | `tools/data_tools.py` 내부 |
| `configs/prompts/*.yaml` | Worker 시스템 프롬프트 컨텍스트 |
| `graph.py` `build_graph()` | `graph.py` 리팩토링 |
| `service.py` | `service.py` 확장 |
