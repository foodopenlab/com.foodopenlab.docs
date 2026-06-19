# Backend Harness & Architecture (`com.auditor`)

> **SSOT:** 이 파일은 [`plan.docs/com.auditor/CLAUDE.md`](CLAUDE.md) 입니다.  
> 코드 트리 [`com.auditor/CLAUDE.md`](../../com.auditor/CLAUDE.md) 는 **심볼릭 링크**로 이 파일을 가리킵니다. 여기만 수정하면 AI·개발자가 동일 문서를 봅니다.

Parent: [`../../CLAUDE.md`](../../CLAUDE.md) · Cursor summary: [`cursor-rules.md`](cursor-rules.md) · Wiki: `plan.docs/DevOps/Backend/BACKEND_RULES.md` (있을 때)

**Physical root:** `com.foodopenlab/com.auditor/` · **PYTHONPATH:** `apps/` + `core/` (`main.py`가 주입)

---

## Monorepo 위치

| Item | Path |
|------|------|
| FastAPI entry | `com.auditor/main.py` |
| Domain apps | `com.auditor/apps/{domain}/` |
| Shared core | `com.auditor/core/matrix/` |
| Alembic | `com.auditor/alembic/` |
| Docker backend | `docker-compose.yaml` → `fastapi_backend` :8000 |
| Env | `com.auditor/.env` |

**등록된 주요 라우터 (`main.py`):**

| Import prefix | App | Mount |
|---------------|-----|-------|
| `mfds_user.*` | MFDS 사용자 API | `user_router` |
| `mfds_admin.*` | MFDS 관리자 API | `admin_router` |
| `titanic.*` | Titanic 학습/데모 | `titanic_router` → `/api/titanic/...` |
| `siliconvalley.*` | Piper 크루 (실리콘밸리) | `piper_router` → `/api/piper/...` |

기타 `apps/` 형제: `imitation_game`, `inception`, `social_network` 등 — 동일 프랙탈 패턴으로 `_docs/` 추가.

---

## App-level specs (sibling apps)

```
com.auditor/apps/{domain}/_docs/CLAUDE.md
```

| App | Spec |
|-----|------|
| titanic | [`apps/titanic/_docs/CLAUDE.md`](../../com.auditor/apps/titanic/_docs/CLAUDE.md) |
| siliconvalley | [`apps/siliconvalley/_docs/CLAUDE.md`](../../com.auditor/apps/siliconvalley/_docs/CLAUDE.md) |
| mfds_user | [`apps/mfds_user/_docs/CLAUDE.md`](../../com.auditor/apps/mfds_user/_docs/CLAUDE.md) |
| mfds_admin | [`apps/mfds_admin/_docs/CLAUDE.md`](../../com.auditor/apps/mfds_admin/_docs/CLAUDE.md) |

앱 작업 시: **this file + 해당 앱 `_docs/CLAUDE.md` + `cursor-rules.md`**.

**PKS (이 폴더 하위 위키):** [`app-rules.md`](app-rules.md) · [`db-rules.md`](db-rules.md) · [`auth-rules.md`](auth-rules.md) · [`entity-rules.md`](entity-rules.md) · [`scaffold-rules.md`](scaffold-rules.md) · [`mfds-erd.md`](mfds-erd.md)

---

## Architecture — SOLID + Hexagonal + Clean + DDD

All backend feature work **must** comply with:

- **SOLID** (especially DIP: depend on ports, not concrete adapters)
- **Hexagonal** (inbound vs outbound; adapters at edges)
- **Clean** (dependency rule: domain has no framework imports)
- **DDD** (entities/VOs; application orchestrates use cases)

| Layer | Responsibility | Must NOT |
|-------|----------------|----------|
| **Inbound adapter** (router, schema, inbound mapper) | HTTP 검증, Schema↔DTO 변환 | SQL, ORM, 비즈니스 규칙 |
| **Application** (use case port, interactor, dto) | 유스케이스 오케스트레이션 | FastAPI `Depends`, ORM |
| **Domain** (entity, value object) | 도메인 규칙·타입 | FastAPI, SQLAlchemy, HTTP |
| **Outbound adapter** (repositories/memory/orm, outbound mapper) | 영속성·외부 I/O | `HTTPException` (라우터 책임) |
| **dependencies/** | Composition root — `get_*_repository` → `get_*_use_case` | 비즈니스 로직 |

**표준 호출 흐름:**

```
Router → Schema → (inbound mapper) → Query/Command DTO
      → UseCase (abstract) → Interactor → Output port (abstract) → Repository
      → Response DTO → Router → Response Schema
```

**DIP 금지:**

- Router → `*Repository` (adapter) 직접 import
- Interactor → `Depends`, inbound `*Schema` (DTO/Command 사용)
- Domain → framework import

**Fractal naming:** 동일 capability 접두·접미 (`crew_smith_captain_router`, `_schema`, `_dto`, `_interactor`, `_port`, `_repository`, `_provider`).

### Use case · interactor — `async` 붙일까?

**같은 use case 클래스 안에서도 메서드마다 다를 수 있다.** `async`는 “클래스가 async라서”가 아니라 **안에서 `await`할 I/O가 있을 때만** 붙인다.

| 메서드 성격 | 예 | use case / interactor |
|-------------|-----|------------------------|
| **CPU-bound** — 동기 연산만, DB·네트워크·파일 없음 | Kiwi `tokenize()`, dict 점수 계산 (`analyze_intent`) | `def` |
| **I/O-bound** — DB·LLM·HTTP·파일 등 `await` 필요 | `repository.introduce_myself(...)`, 외부 API | `async def` |

**금지:** CPU만 하는 메서드에 `async def`만 달고 내부에 `await` 없음 → 코루틴만 생기고 **이벤트 루프는 그대로 블로킹**. 비동기인 것처럼 보이지만 실제로는 더 헷갈리는 동기 코드가 된다.

**CPU가 무거워 이벤트 루프 블로킹이 문제일 때** — port를 `async def`로 바꾸기보다 **호출 측(router 등)** 에서 스레드풀 위임:

```python
result = await asyncio.to_thread(use_case.analyze_intent, question)
```

참고 예 (`titanic`): `analyze_intent` → `def` · `introduce_myself` → `async def` (repository I/O `await`).

**에이전트:** 오류 수정 시 use case/interactor의 **동기·비동기 시그니처를 임의로 바꾸지 않는다.** 레이어·책임(예: interactor ↔ repository)도 사용자 요청 없이 옮기지 않는다.

---

## Path & Import Conventions

| Kind | Documentation path | Physical path |
|------|-------------------|---------------|
| App/domain | `com.auditor/{domain}/...` | `com.auditor/apps/{domain}/...` |
| Core | `com.auditor.core.*` | `com.auditor/core/matrix/...` |

**Python imports:** `titanic.*`, `mfds_user.*`, `mfds_admin.*`, `matrix.*` (저장소 관례 유지).

---

## Stack & operations

| Topic | Rule |
|-------|------|
| HTTP | Pydantic schema; 400/404/409/502/503 + 짧은 `detail` |
| Env | `.env` / Keymaker; 비밀 커밋 금지 |
| External API | cache-first; background enrich (`mfds_user` lifecycle) |
| DB schema | **Alembic SSOT**; `db_init` = 존재 확인·dev helper |
| Docker | deps 변경 → `docker compose up -d --build backend`; `.py`만 → `restart backend` |
| LLM (titanic 등) | blocking I/O → `asyncio.to_thread`; Docker → `OLLAMA_HOST=host.docker.internal:11434` |

---

## 머신러닝 데이터 분석 원칙

피처·스키마·전처리 설계 시 **측정 척도**를 먼저 구분한다.

### Categorical (범주형)

데이터가 카테고리로 묶일 때 사용한다.

| 척도 | 설명 | 예 |
|------|------|-----|
| **nominal** (명목) | 이름을 바탕으로 하는 척도. 순서와 무관하게 셀 수 있는 데이터 | 청팀, 홍팀, 백팀 |
| **ordinal** (서열) | 순서를 바탕으로 하는 척도. 자료 사이에 순서(서열)가 있는 경우 | 청팀이 이길 가능성: 1. 매우 낮음 · 2. 낮음 · 3. 보통 · 4. 높음 · 5. 매우 높음 |

### Quantitative (양적)

숫자로 셀 수 있을 때 사용한다.

| 척도 | 설명 | 예 |
|------|------|-----|
| **interval** (등간) | 간격을 바탕으로 하는 척도. 임의의 원점 없이 일정한 측정 구간을 갖는 데이터 | 11:00~11:05, 15:55~16:00, 온도, pH — 「10배 덥다」「10배 시다」는 불가 |
| **ratio** (비율) | 비율을 바탕으로 하는 척도. 임의의 원점(0)을 기준으로 두는 데이터 | 나이, 돈, 몸무게 — 「10배 많다」가 가능 |

**적용:** nominal → one-hot·label encoding(순서 없음) · ordinal → 순서 보존 인코딩·순위 처리 · interval/ratio → 산술 연산·스케일링(원점 의미에 주의).

---

## Verification (backend)

1. `/docs` 또는 `curl` / reproducible API check  
2. `uvicorn` / `docker logs fastapi_backend`  
3. Lint/typecheck on touched modules  
4. `pytest apps/{domain}/tests` when applicable  
5. `alembic upgrade head` when ORM changes  

## Acknowledgment (one line)

`plan.docs acknowledged: FOUNDATIONS + Backend_RULES (+ plan.docs/com.auditor/*.md + app _docs/CLAUDE.md if applicable)`
