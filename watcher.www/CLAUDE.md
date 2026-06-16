# Frontend Harness & Architecture (`watcher.www`)

> **SSOT:** [`plan.docs/watcher.www/CLAUDE.md`](CLAUDE.md)  
> 코드 [`watcher.www/CLAUDE.md`](../../watcher.www/CLAUDE.md) 는 **심볼릭 링크**로 이 파일을 가리킵니다.

Parent: [`../../CLAUDE.md`](../../CLAUDE.md) · Cursor summary: [`cursor-rules.md`](cursor-rules.md) · Wiki: `plan.docs/DevOps/Frontend/REACT_RULES.md`

**Physical root:** `com.foodopenlab/watcher.www/` · **Framework:** Next.js App Router

**API origin:** FastAPI `http://localhost:8000` (Docker: `BACKEND_URL=http://backend:8000`) — BFF·응답 계약은 아래 *Backend integration* 참고. 풀스택·백엔드 harness는 **루트** [`../../CLAUDE.md`](../../CLAUDE.md)에서 스코프 라우팅.

---

## Repository layout

| Path | Role |
|------|------|
| `app/**/page.tsx` | Route UI |
| `app/api/**/route.ts` | BFF — proxy, secrets, Vercel-only APIs |
| `components/` | Reusable UI |
| `lib/api-path.ts` | Same-origin `/api/*` — `apiPath()` |
| `lib/backend-origin.ts` | FastAPI origin for Route Handlers |
| `next.config.mjs` | `resolveBackendOrigin()` rewrites (local/Docker) |

**주요 라우트 (예):** `login`, `signup`, `mypage`, `dashboard`, `recalls`, `enforcement`, `supplier`, `lesson/titanic/...`, `chat`, `agent`

---

## Frontend architecture

| Layer | Responsibility |
|-------|----------------|
| **Pages** | Composition, minimal logic |
| **Components** | Reusable UI; avoid per-field `useState` sprawl |
| **Lib** | API paths, backend origin, shared utils |
| **Route Handlers** | BFF — proxy to FastAPI, hide secrets |

**Browser API calls:** same-origin **`/api/*` only** — never call `127.0.0.1:8000` from the client bundle.

**Vercel:** `NEXT_PUBLIC_API_URL`에 사설 IP·로컬호스트 금지. 공개 `BACKEND_URL` + Route Handler proxy.

---

## Backend integration

| Mode | When | Config |
|------|------|--------|
| **Rewrite** | Local / Docker | `next.config.mjs` + `BACKEND_URL` |
| **Route Handler** | Vercel, Gemini, food-safety | `app/api/**/route.ts` |
| **Catch-all proxy** | auth, mypage | `app/api/auth/[...path]`, `app/api/mypage/[...path]` |

**Response contracts:** UI 기대 필드와 FastAPI 응답 일치 (예: Smith chat → `{ text }`, enforcement list → `{ total, page, items, list_max }`).

Deploy: `watcher.www/docs/VERCEL_DEPLOY.md` (있을 때).

---

## State & forms

- One page → one state object + `patchState(partial)`
- Form submit → `FormData` + `Object.fromEntries`
- Detail: `REACT_RULES.md`

---

## Docker (frontend)

| Change | Command |
|--------|---------|
| `package.json` | `docker compose up -d --build frontend` |
| `.tsx` / `.ts` only | HMR (보통 자동); 필요 시 `restart frontend` |
| `.env.local` | `docker compose restart frontend` |

Service: `nextjs_frontend` :3000

---

## Non-Negotiable

- Minimal diff; match existing patterns
- No secrets in client bundles or committed `.env.local`
- Reuse `formatApiClientError` (`lib/api-path.ts`)
- Verify: `npm run dev` / `npm run build`

## Acknowledgment

`plan.docs acknowledged: FOUNDATIONS + Frontend_REACT_RULES`
