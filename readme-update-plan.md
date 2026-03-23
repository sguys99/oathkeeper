# README 개편 계획

## Context

현재 `README.md`가 한글 단일 파일로 모든 내용(프로젝트 소개, 환경 설정, 실행 방법, 배포)을 포함하고 있음. 이를 영문 중심으로 재구성하고, 한글 버전/환경 설정 가이드/사용 매뉴얼을 별도 문서로 분리하여 가독성과 접근성을 개선한다.

## 대상 파일

| 파일 | 역할 |
|---|---|
| `README.md` | 영문 메인 README (한글 버전 링크 포함) |
| `docs/README(kr).md` | 한글 메인 README |
| `docs/manual/env-setting(en).md` | 영문 환경 설정 가이드 |
| `docs/manual/env-setting(kr).md` | 한글 환경 설정 가이드 |
| `docs/manual/manual(en).md` | 영문 사용 매뉴얼 (스크린샷 포함) |
| `docs/manual/manual(kr).md` | 한글 사용 매뉴얼 (스크린샷 포함) |

## 활용 가능한 스크린샷 (docs/manual/imgs/)

| 파일 | 화면 |
|---|---|
| `1.request-analysis.png` | Deal 분석 요청 페이지 (Notion Deal 선택, 추가 정보, 문서 첨부) |
| `2-1.deal-info-overview.png` | Deal 현황 대시보드 (목록, 검색, 필터) |
| `2-2.deal-info-detail.png` | Deal 상세 분석 결과 (종합 점수, 레이더 차트, 기준별 점수) |
| `3-1.agent-log-overview.png` | 에이전트 로그 목록 |
| `3-2.agent-log-logs.png` | 에이전트 로그 상세 (단계별 프롬프트/출력) |
| `4.agent-settings.png` | 에이전트 설정 (프롬프트 관리 + 플로우 다이어그램) |
| `5.admin.png` | 관리자 설정 (평가 기준 가중치 슬라이더) |

---

## 단계별 작업 계획

### Step 1: `README.md` — 영문 메인 README 작성

현재 한글 README를 영문으로 재작성. 핵심 정보만 유지하고, 상세 환경 설정/매뉴얼은 링크로 대체.

- [ ] Title + 한줄 설명 + 한글 버전 링크 (`docs/README(kr).md`)
- [ ] **Key Features** — 6개 기능 테이블 (Deal 파싱, 스코어링, 소요 산출, 리스크 분석, 유사사례, 리포트)
- [ ] **Scoring Criteria** — 7개 항목 + 가중치 테이블
- [ ] **Verdict Logic** — Go/Conditional Go/No-Go/Hold 조건 테이블
- [ ] **System Architecture** — 아키텍처 다이어그램 (텍스트)
- [ ] **LangGraph Agent Flow** — 파이프라인 다이어그램 + 노드 설명
- [ ] **Tech Stack** — 기술 스택 테이블
- [ ] **Project Structure** — 디렉토리 트리
- [ ] **Quick Start** — 간략한 설치/실행 명령어 (상세는 env-setting 링크)
- [ ] **Documentation** — 하위 문서 링크 테이블
- [ ] **License**

### Step 2: `docs/README(kr).md` — 한글 메인 README 작성

- [ ] Step 1의 한글 번역 버전 작성
- [ ] 영문 버전 링크 포함

### Step 3: `docs/manual/env-setting(en).md` — 영문 환경 설정 가이드

- [ ] **Prerequisites** — Python 3.12+, uv, Node.js 18+, Docker
- [ ] **Installation** — 저장소 클론, `make init` / `make init-dev`, 프론트엔드 설치
- [ ] **Notion Setup** — Integration 생성, DB 생성 및 ID 확인, 필수 프로퍼티 설명
- [ ] **Environment Variables (`.env`)** — `.env.example` 기반 전체 변수 설명 테이블
- [ ] **Database Setup** — Docker PostgreSQL, 마이그레이션, 시드 데이터
- [ ] **Running the Application** — 백엔드 + 프론트엔드 실행
- [ ] **Production Deployment** — Docker Compose 프로덕션 빌드/실행

### Step 4: `docs/manual/env-setting(kr).md` — 한글 환경 설정 가이드

- [ ] Step 3의 한글 번역 버전 작성

### Step 5: `docs/manual/manual(en).md` — 영문 사용 매뉴얼

스크린샷 중심의 화면별 사용 가이드.

- [ ] **Overview** — 페이지 라우팅 테이블
- [ ] **1. Request Analysis** (`/`) — `1.request-analysis.png` 활용
- [ ] **2. Deal Dashboard** (`/deals`) — `2-1.deal-info-overview.png` 활용
- [ ] **3. Deal Detail** (`/deals/:id`) — `2-2.deal-info-detail.png` 활용
- [ ] **4. Agent Logs** (`/agent-logs`, `/deals/:id/logs`) — `3-1`, `3-2` 활용
- [ ] **5. Agent Settings** (`/agent-settings`) — `4.agent-settings.png` 활용
- [ ] **6. Admin Settings** (`/admin`) — `5.admin.png` 활용

### Step 6: `docs/manual/manual(kr).md` — 한글 사용 매뉴얼

- [ ] Step 5의 한글 번역 버전 작성 (동일 스크린샷 사용)

---

## 작업 순서 요약

| 순서 | 파일 | 설명 | 상태 |
|:---:|---|---|:---:|
| 1 | `README.md` | 영문 메인 README 재작성 | ⬜ |
| 2 | `docs/README(kr).md` | 한글 메인 README | ⬜ |
| 3 | `docs/manual/env-setting(en).md` | 영문 환경 설정 | ⬜ |
| 4 | `docs/manual/env-setting(kr).md` | 한글 환경 설정 | ⬜ |
| 5 | `docs/manual/manual(en).md` | 영문 사용 매뉴얼 | ⬜ |
| 6 | `docs/manual/manual(kr).md` | 한글 사용 매뉴얼 | ⬜ |

## Verification

- [ ] 모든 문서 간 상호 링크가 정상 동작하는지 확인
- [ ] 스크린샷 경로(`imgs/`)가 각 매뉴얼 파일 위치 기준 상대경로로 올바른지 확인
- [ ] `.env.example` 변수와 env-setting 문서의 변수 목록 일치 여부 확인
- [ ] README의 Quick Start 명령어가 실제 Makefile 타겟과 일치하는지 확인
