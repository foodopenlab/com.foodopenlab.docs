# Cursor Harness — Backend (`com.auditor`)

> **SSOT:** [`plan.docs/com.auditor/cursor-rules.md`](cursor-rules.md) · 코드 [`com.auditor/cursor-rules.md`](../../com.auditor/cursor-rules.md) 는 **심볼릭 링크**.

Parent: [`../../cursor-rules.md`](../../cursor-rules.md) · Full spec: [`CLAUDE.md`](CLAUDE.md) · Wiki: `plan.docs/DevOps/Backend/BACKEND_RULES.md`

**Scope:** `com.auditor/` — FastAPI, `apps/*`, `core/`, Alembic, Docker `fastapi_backend`.

---

## PKS workflow (backend)

1. Read **this file** + [`CLAUDE.md`](CLAUDE.md)
2. Read `plan.docs/com.auditor/*.md` (app, db, auth, entity, scaffold, mfds-erd)
3. App 작업 시 `apps/{domain}/_docs/cursor-rules.md` + `CLAUDE.md`
4. Plan → implement → verify (test/lint/API)

---

## Architecture (summary)

| Layer | Role |
|-------|------|
| Inbound | router, schema, inbound mapper |
| Application | use case port, interactor, dto |
| Domain | entity, value_object |
| Outbound | orm, pg repository, outbound mapper |
| dependencies | `get_*_repository` + `get_*_use_case` only |

**Flow:** `Router → UseCase → Interactor → Repository → PgRepository` · `Schema ↔ DTO ↔ ORM`

**금지:** Router→PgRepository · Interactor→`Depends` · Interactor→inbound Schema · Domain→FastAPI/SQLAlchemy

**Apps:** `titanic`, `mfds_user`, `mfds_admin` (+ sibling `apps/{domain}/_docs/`)

---

## Path notation

- Docs: `com.auditor/titanic/...` (= `apps/titanic/...`)
- Imports: `titanic.*`, `mfds_user.*`, `matrix.*`

---

## Stack summary

- Pydantic inbound schemas; meaningful HTTP status codes
- `.env` / Keymaker; no secrets in commits
- External API: cache-first + background sync (`mfds_user`)
- Alembic for schema; `db_init` = table check only
- Docker: `build backend` on `requirements.txt` change; `restart backend` for code-only

---

## ML / 데이터 분석 (측정 척도)

피처·전처리 전 **척도 구분** — 상세: [`CLAUDE.md`](CLAUDE.md) § 머신러닝 데이터 분석 원칙

| 구분 | 척도 | 핵심 |
|------|------|------|
| **Categorical** | nominal (명목) | 순서 없음 — 팀명 등 |
| | ordinal (서열) | 순서 있음 — 만족도·등급 |
| **Quantitative** | interval (등간) | 원점 없음 — 온도, pH, 시간 구간 |
| | ratio (비율) | 원점(0) 있음 — 나이, 금액, 무게 |

nominal에 순서 부여·ratio에 interval 연산 혼용 금지.

---

## Verification

- API: `/docs`, curl, integration scripts
- `docker logs fastapi_backend`
- `pytest apps/{domain}/tests -m "not integration"` when present
- Alembic when ORM changes

## Acknowledgment

`plan.docs acknowledged: FOUNDATIONS + Backend_RULES (+ plan.docs/com.auditor + app _docs if applicable)`
