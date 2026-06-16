# Cursor Harness — Frontend (`watcher.www`)

> **SSOT:** [`plan.docs/watcher.www/cursor-rules.md`](cursor-rules.md) · 코드 [`watcher.www/cursor-rules.md`](../../watcher.www/cursor-rules.md) 는 **심볼릭 링크**.

Parent: [`../../cursor-rules.md`](../../cursor-rules.md) · Full spec: [`CLAUDE.md`](CLAUDE.md) · Wiki: `plan.docs/DevOps/Frontend/REACT_RULES.md`

**Scope:** `watcher.www/` — Next.js App Router, BFF `app/api/*`. 풀스택·백엔드 작업은 루트 [`../../cursor-rules.md`](../../cursor-rules.md)에서 스코프 라우팅.

---

## PKS workflow (frontend)

1. Read **this file** + [`CLAUDE.md`](CLAUDE.md)
2. `plan.docs/DevOps/Frontend/REACT_RULES.md` + product docs when applicable
3. API 계약 변경 시 → 이 파일의 proxy·JSON 계약 절 + 제품 위키; 백엔드 쪽은 루트 harness로 스코프 전환
4. Plan → implement → `npm run build` when routing/config changes

---

## Stack summary

- **Framework:** Next.js App Router (`app/`, `page.tsx`, Route Handlers)
- **API:** browser → same-origin `/api/*` via `lib/api-path.ts` `apiPath()`
- **BFF:** `app/api/**/route.ts` → FastAPI (`lib/backend-origin.ts`)
- **Rewrite:** `next.config.mjs` — local/Docker only; Vercel uses public `BACKEND_URL`
- **State:** one page state object; `FormData` + `patchState` — see `REACT_RULES.md`

---

## Backend proxy patterns

| Pattern | Use |
|---------|-----|
| Route Handler | Gemini, recalls, weather, Vercel-only |
| `next.config` rewrite | Local `BACKEND_URL` → FastAPI |
| Catch-all | `app/api/auth/[...path]`, `app/api/mypage/[...path]` |

JSON 계약(`text`, `detail`, `items`, …)을 백엔드 응답과 맞출 것.

---

## Docker

- `package.json` change → `docker compose up -d --build frontend`
- Code-only → HMR or `docker compose restart frontend`
- Container: `nextjs_frontend` :3000

---

## Non-Negotiable

- Minimal diff; no unrelated UI refactors
- No secrets in client bundles
- `formatApiClientError` 등 기존 UX 패턴 재사용
- TypeScript: match existing style

## Verification

- `npm run dev` / Docker frontend logs
- Browser network tab
- `npm run build` on config/routing changes

## Acknowledgment

`plan.docs acknowledged: FOUNDATIONS + Frontend_REACT_RULES`
