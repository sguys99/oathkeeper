# Ollama 기반 SLM 연계 확장 계획

## 배경

현재 OathKeeper는 OpenAI GPT-4o / Claude Sonnet을 API 방식으로만 연계한다.
Ollama 기반 로컬 SLM(Small Language Model) 지원을 위해 6단계로 점진적 확장한다.

**최소 로컬 운영 목표:** Phase 1~3 완료 시 LLM + 임베딩 완전 로컬화 (Pinecone 유지)
**완전 오프라인 목표:** Phase 1~4 완료 시 인터넷 연결 없이 운영 가능

---

## Phase 1: Ollama LLM 기본 연계

> 목표: 최소 변경으로 Ollama를 LLM 백엔드로 사용

### 작업 항목

- [x] `backend/pyproject.toml` — `langchain-ollama>=0.3.0` 의존성 추가
- [x] `backend/app/utils/settings.py` — `llm_provider` Literal에 `"ollama"` 추가
- [x] `backend/app/utils/settings.py` — Ollama 설정 필드 추가
  - `ollama_base_url: str = "http://localhost:11434"`
  - `ollama_model: str = "qwen3:14b"`
- [x] `backend/app/agent/llm.py` — `ChatOllama` import 및 라우팅 분기 추가
  - `num_predict=max_tokens` (Ollama는 `max_tokens` 대신 `num_predict` 사용)
- [x] `.env.example` — Ollama 관련 환경변수 항목 추가
- [ ] 동작 검증
  - [ ] `ollama pull qwen3:14b` 후 서버 기동
  - [ ] `LLM_PROVIDER=ollama make run` 실행
  - [ ] 딜 분석 요청 후 `agent_logs`에서 LLM 호출 결과 확인

### 변경 불필요 (provider-agnostic 구조)
- `base.py` (call_llm, logged_call_llm)
- 모든 노드 팩토리 6개
- 프롬프트 YAML 파일

### 권장 모델 (한국어 기준)
| 모델 | 파라미터 | 컨텍스트 | 비고 |
|------|----------|----------|------|
| `qwen3:14b` | 14B | 128K | 권장 (품질 우수) |
| `qwen3:8b` | 8B | 128K | 경량 옵션 |
| `gemma3:12b` | 12B | 128K | 대안 |
| `llama3.2:3b` | 3B | 4K | Phase 2 필수 |

---

## Phase 2: SLM용 프롬프트 최적화

> 목표: SLM 컨텍스트 윈도우에 맞게 프롬프트 압축

### 배경
현재 노드별 토큰 추정치:
- `final_verdict`: system ~3,000 + data 2,000+ 토큰
- `resource_estimation`: ~2,200 토큰
- `scoring`: ~2,000 토큰

### 작업 항목

- [x] `backend/app/utils/settings.py` — `prompt_profile: Literal["full", "compact"] = "full"` 추가
- [x] `backend/app/agent/prompt_loader.py` — `load_prompt()` 함수에 profile 파라미터 지원
- [x] `configs/prompts/final_verdict.yaml` — compact 섹션 추가 (목표: 50% 토큰 절약)
- [x] `configs/prompts/resource_estimation.yaml` — compact 섹션 추가
- [x] `configs/prompts/scoring.yaml` — compact 섹션 추가
- [x] `configs/prompts/risk_analysis.yaml` — compact 섹션 추가
- [x] `configs/prompts/deal_structuring.yaml` — compact 섹션 추가
- [ ] 동작 검증
  - [ ] `PROMPT_PROFILE=compact LLM_PROVIDER=ollama` 로 딜 분석 실행
  - [ ] JSON schema 통과율 확인
  - [ ] `llama3.2:3b` (4K ctx) 모델로 compact 프로파일 동작 확인

---

## Phase 3: 로컬 임베딩 지원 (Ollama Embeddings)

> 목표: OpenAI 임베딩 의존성 제거, Ollama 임베딩 모델 지원

### 배경
- 현재: `text-embedding-3-small` (OpenAI, 1536-dim) 하드코딩
- Pinecone 인덱스 차원 1536 고정 가정

### 작업 항목

- [x] `backend/app/utils/settings.py` — 임베딩 설정 필드 추가
  - `embedding_provider: Literal["openai", "ollama"] = "openai"`
  - `ollama_embedding_model: str = "nomic-embed-text"`
  - `embedding_dimensions: int = 1536`
- [x] `backend/app/agent/embeddings.py` — `OllamaEmbeddings` 라우팅 추가
- [x] `backend/app/db/vector_store.py` — 차원 설정값 참조로 변경 (하드코딩 제거)
- [x] `.env.example` — 임베딩 관련 환경변수 항목 추가
- [ ] 동작 검증
  - [ ] `ollama pull nomic-embed-text` 실행
  - [ ] `EMBEDDING_PROVIDER=ollama EMBEDDING_DIMENSIONS=768` 환경으로 서버 기동
  - [ ] 프로젝트 히스토리 업서트 후 유사 프로젝트 검색 동작 확인

### 참고: Ollama 임베딩 모델 차원
| 모델 | 차원 |
|------|------|
| `nomic-embed-text` | 768 |
| `mxbai-embed-large` | 1024 |
| `all-minilm` | 384 |

---

## Phase 4: 로컬 벡터 DB 지원 (선택)

> 목표: Pinecone 대신 로컬 벡터 DB를 지원하여 완전 오프라인 운영 가능

### 작업 항목

- [ ] `backend/app/utils/settings.py` — 벡터 스토어 설정 추가
  - `vector_store_provider: Literal["pinecone", "chroma", "qdrant"] = "pinecone"`
  - `chroma_persist_dir: str = "./data/chroma"`
  - `qdrant_url: str = "http://localhost:6333"`
- [ ] `backend/app/db/vector_store_factory.py` (신규) — 팩토리 함수 구현
- [ ] `backend/app/db/vector_store.py` — `CompanyContextStore`, `ProjectHistoryStore` 추상화
- [ ] `backend/pyproject.toml` — `chromadb` 또는 `qdrant-client` 의존성 추가
- [ ] `backend/app/api/routers/project_history.py` — 벡터 업서트 로직 팩토리 연동
- [ ] 동작 검증
  - [ ] `VECTOR_STORE_PROVIDER=chroma make run`
  - [ ] `make seed` 후 ChromaDB 저장 확인
  - [ ] 유사 프로젝트 검색 기능 동작 확인

---

## Phase 5: 노드별 모델 라우팅 (선택)

> 목표: 노드 복잡도에 따라 다른 모델 사용 → 비용/성능 최적화

### 작업 항목

- [ ] `backend/app/utils/settings.py` — `node_model_overrides: dict[str, str] = {}` 추가
- [ ] `backend/app/agent/llm.py` — `get_llm_for_node(node_name)` 함수 추가
- [ ] 각 노드 팩토리 (6개) — `logged_call_llm` 호출 시 `llm=get_llm_for_node(node_name)` 전달
  - `backend/app/agent/nodes/deal_structuring.py`
  - `backend/app/agent/nodes/scoring.py`
  - `backend/app/agent/nodes/resource_estimation.py`
  - `backend/app/agent/nodes/risk_analysis.py`
  - `backend/app/agent/nodes/similar_project.py`
  - `backend/app/agent/nodes/final_verdict.py`
- [ ] `.env.example` — 노드별 오버라이드 예시 추가
- [ ] 동작 검증
  - [ ] `NODE_MODEL_OVERRIDES='{"final_verdict": "qwen3:14b", "deal_structuring": "qwen3:8b"}'` 설정 후 분석 실행
  - [ ] `agent_logs`에서 노드별 모델명 확인

---

## Phase 6: 어드민 UI 확장 (선택)

> 목표: 프론트엔드에서 Ollama 설정 관리

### 작업 항목

#### 백엔드
- [ ] `backend/app/api/routers/settings.py` — Ollama API 엔드포인트 추가
  - `GET /api/settings/ollama/status` — 연결 상태 확인
  - `GET /api/settings/ollama/models` — 사용 가능한 모델 목록 조회

#### 프론트엔드
- [ ] `frontend/src/app/admin/page.tsx` — "AI 모델" 탭 추가
- [ ] `frontend/src/app/admin/_components/ai-model-tab.tsx` (신규) — 탭 컴포넌트
  - LLM 프로바이더 선택 (openai / claude / ollama)
  - Ollama 서버 URL 설정
  - 모델명 드롭다운 (Ollama API 동적 조회)
  - 연결 테스트 버튼
  - 임베딩 프로바이더 설정
- [ ] `frontend/src/hooks/use-settings.ts` — Ollama 설정 훅 확장
- [ ] 동작 검증
  - [ ] 어드민 UI에서 Ollama URL 변경 후 저장
  - [ ] 연결 테스트 버튼 동작 확인
  - [ ] 모델 목록 드롭다운 동적 로드 확인

---

## 진행 현황

| Phase | 상태 | 예상 소요 |
|-------|------|-----------|
| Phase 1: Ollama LLM 기본 연계 | 🔲 동작 검증 대기 | 1~2일 |
| Phase 2: SLM용 프롬프트 최적화 | 🔲 동작 검증 대기 | 1~2일 |
| Phase 3: 로컬 임베딩 지원 | ⬜ 미시작 | 1~2일 |
| Phase 4: 로컬 벡터 DB 지원 | ⬜ 미시작 (선택) | 2~3일 |
| Phase 5: 노드별 모델 라우팅 | ⬜ 미시작 (선택) | 1~2일 |
| Phase 6: 어드민 UI 확장 | ⬜ 미시작 (선택) | 1~2일 |
