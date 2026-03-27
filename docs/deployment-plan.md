# OathKeeper Vercel 배포 계획

## Context

OathKeeper는 **Next.js 프론트엔드 + FastAPI 백엔드 + PostgreSQL** 구조입니다. Vercel은 Next.js에 최적화된 플랫폼이지만, **Python FastAPI 백엔드는 Vercel에서 직접 운영하기 어렵습니다** (async SQLAlchemy, LangGraph, SSE 스트리밍, 파일 업로드 등 서버풀 기능 필요).

따라서 현실적인 배포 전략은 **프론트엔드만 Vercel**, **백엔드는 별도 클라우드 서비스**에 배포하는 것입니다.

---

## 배포 아키텍처

```
[Vercel] ← 프론트엔드 (Next.js)
    ↓ API 호출
[Railway/Render/Fly.io] ← 백엔드 (FastAPI + LangGraph)
    ↓
[Supabase/Neon/Railway] ← PostgreSQL
[Pinecone] ← 벡터 DB (기존 유지)
```

---

## 단계별 배포 절차

### 1단계: 백엔드 배포 (Railway 권장)

Vercel에 프론트엔드를 올리기 전에, 백엔드가 먼저 외부에서 접근 가능해야 합니다.

**옵션 비교:**
| 서비스 | 장점 | 단점 |
|---------|------|------|
| **Railway** | Docker 지원, PostgreSQL 내장, 간편 | 무료 플랜 제한적 |
| **Render** | 무료 티어 있음, Docker 지원 | 콜드 스타트 느림 |
| **Fly.io** | 글로벌 엣지, Docker 네이티브 | 설정 복잡 |

**Railway 배포 순서:**
1. [railway.app](https://railway.app) 가입 및 프로젝트 생성
2. GitHub 레포 연결
3. PostgreSQL 서비스 추가 (Add Plugin → PostgreSQL)
4. 백엔드 서비스 추가 — Root Directory: `/` (기존 Dockerfile 활용)
5. 환경변수 설정:
   - `DATABASE_URL` — Railway PostgreSQL 연결 문자열 (`postgresql+asyncpg://...`)
   - `OPENAI_API_KEY` 또는 `ANTHROPIC_API_KEY`
   - `LLM_PROVIDER`
   - `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`
   - `NOTION_API_KEY`, `NOTION_DEAL_DB_ID`, `NOTION_DECISION_DB_ID`
   - `CORS_ORIGINS` — Vercel 도메인 포함 (예: `["https://your-app.vercel.app"]`)
   - `ENVIRONMENT=production`, `DEBUG=false`
6. 배포 후 헬스체크 확인: `https://<backend-url>/health`
7. DB 마이그레이션 실행: Railway CLI 또는 콘솔에서 `alembic upgrade head`
8. 시드 데이터 입력: `python -m backend.app.db.seed`

### 2단계: 프론트엔드 코드 수정

현재 프론트엔드는 Docker 환경(Nginx 프록시)에 맞춰져 있으므로, Vercel 배포를 위해 일부 수정이 필요합니다.

#### 2-1. `next.config.ts` 수정
- `output: "standalone"` 제거 (Vercel은 자체 빌드 시스템 사용)
- 백엔드 API로의 rewrites 추가 (CORS 이슈 방지용, 선택사항)

```ts
// frontend/next.config.ts
const nextConfig = {
  // output: "standalone" 제거
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
};
```

#### 2-2. 환경변수 확인
- `NEXT_PUBLIC_API_URL` — 백엔드 URL (예: `https://oathkeeper-backend.up.railway.app`)

### 3단계: Vercel 프론트엔드 배포

1. [vercel.com](https://vercel.com) 가입 및 GitHub 레포 연결
2. 프로젝트 Import 시 설정:
   - **Framework Preset:** Next.js (자동 감지)
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (기본값)
   - **Output Directory:** `.next` (기본값)
3. 환경변수 설정:
   - `NEXT_PUBLIC_API_URL` = `https://<backend-url>` (1단계에서 배포한 백엔드 주소)
4. Deploy 클릭

### 4단계: CORS 및 연동 설정

1. **백엔드 CORS 업데이트:** `CORS_ORIGINS`에 Vercel 도메인 추가
   - 예: `["https://your-app.vercel.app", "https://custom-domain.com"]`
2. **Notion Webhook URL 업데이트** (필요시)
3. **Slack Webhook** 동작 확인

### 5단계: 커스텀 도메인 (선택)

1. Vercel 대시보드 → Settings → Domains에서 커스텀 도메인 추가
2. DNS 레코드 설정 (CNAME → `cname.vercel-dns.com`)
3. 백엔드 `CORS_ORIGINS`에 커스텀 도메인 추가

---

## 수정 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/next.config.ts` | `output: "standalone"` 제거, rewrites 추가 (선택) |
| `frontend/.env.production` | 새로 생성 — `NEXT_PUBLIC_API_URL` 설정 |

---

## 주의사항

- **SSE (Server-Sent Events):** 분석 진행 상태 스트리밍(`/deals/{id}/status`)이 Vercel의 Serverless Functions를 거치면 타임아웃 될 수 있음. 프론트엔드에서 백엔드로 직접 SSE 연결하는 방식 유지 권장
- **파일 업로드:** 20MB 제한이 있으므로 Vercel의 body size limit(4.5MB for serverless)과 충돌 가능 → 프론트엔드에서 백엔드로 직접 업로드하면 문제 없음
- **환경변수:** `NEXT_PUBLIC_` 접두사가 있는 변수만 클라이언트에 노출됨. API 키는 절대 `NEXT_PUBLIC_`으로 시작하면 안 됨
- **비용:** Vercel 무료 플랜은 Hobby 용도. 상용 배포 시 Pro 플랜($20/월) 권장

---

## 검증 방법

1. Vercel 배포 후 `https://your-app.vercel.app` 접속 확인
2. 딜 목록 조회 (`/deals` 페이지) → 백엔드 API 연동 확인
3. 새 딜 생성 및 분석 실행 → SSE 스트리밍 동작 확인
4. 파일 업로드 테스트
5. Notion 연동 테스트
