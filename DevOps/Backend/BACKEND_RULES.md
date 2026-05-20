# 백엔드 공통 규칙 (FastAPI / Python)

> `@docs/DevOps/Backend/BACKEND_RULES.md`  
> 전제: [FOUNDATIONS.md](../FOUNDATIONS.md) · 제품 스펙: `docs/{프로젝트}/`

---

## 1. 적용 범위

- Python **FastAPI** 기반 API 서버
- 모노레포에서 `backend/` 또는 `apps/` 하위가 일반적이나, **폴더명은 저장소 README를 따름**
- 이 문서는 **패턴·원칙**만 다룸. OpenAPI 서비스 코드·엔드포인트 목록은 **프로젝트 docs**에 둠

---

## 2. 디렉터리·레이어 (C · S · R)

새 도메인 추가 시 권장 구조:

```
{app_root}/{domain}/
├── controller.py    # HTTP / 라우트 핸들러 진입
├── service.py       # 비즈니스 로직
└── repository.py    # DB · 외부 API · 파일
```

| 규칙 | 설명 |
|------|------|
| Controller → Service → Repository | 호출 방향 고정. Repository끼리 직접 호출 지양 |
| 진입 `main.py` | 라우트·`Depends`·미들웨어만. 유스케이스 로직 금지 |
| 기존 모듈 참고 | 같은 저장소의 **이미 있는** 도메인 폴더 네이밍·import 스타일 복제 |
| 레거시 | `main.py`에 로직이 남아 있으면 **신규 코드는 레이어로**, 기존은 요청 시만 이전 |

---

## 3. HTTP·에러

- 요청/응답: **Pydantic** 모델로 스키마 고정. 프론트와 맞출 때는 프로젝트 docs 또는 OpenAPI(`/docs`) 기준  
- `IntegrityError` → 409 등 **의미 있는 상태 코드**  
- `ProgrammingError`(스키마 불일치) → 503 + 재시작 안내 등  
- `OperationalError`(DB 연결) → 503 + 재시도 안내 (스택 트레이스를 그대로 노출하지 않음)  
- 외부 API 실패 → 502 + 짧은 `detail` (키·URL 원문 노출 금지)

---

## 4. 환경 변수

- `os.getenv` / 프로젝트 Keymaker 등 **저장소가 정한 방식** 사용  
- **이름은 프로젝트 `.env.example` 또는 프로젝트 docs가 SSOT** — DevOps에 제품별 키 표를 넣지 않음  
- 원칙: 하드코딩 금지, 문서와 코드의 키 이름 일치

---

## 5. 데이터베이스 (SQLAlchemy 비동기 등)

- 비동기 세션 + 의존성 주입 패턴 유지  
- 풀: `pool_pre_ping=True`, 필요 시 `pool_recycle` (서버리스·유휴 끊김 대비)  
- DB **필수** 엔드포인트와 **선택** 엔드포인트를 구분 (`get_db` vs `get_db_optional` 등)  
- 트랜잭션: 실패 시 `rollback` 후 HTTPException

---

## 6. 외부 API·캐시

- [FOUNDATIONS.md §4](../FOUNDATIONS.md#4-외부-api느린-io) 준수  
- 구현 패턴: `services/*_cache.py` + JSON 캐시 파일 + (선택) 일일 스케줄러  
- HTTP 핸들러: **캐시 hit → 즉시 응답**; stale 허용 시 백그라운드 `refresh`  
- 동일 워커에서 **여러 무거운 refresh가 lock으로 줄서지 않게** lock 범위·종류 분리 검토
- **일일 소프트 한도(옵션):** `EXTERNAL_API_DAILY_UNIT_LIMIT`이 0보다 크면, UTC 일자 기준으로 외부 호출 1회당 1유닛이 누적되고 `EXTERNAL_API_SOFT_STOP_PERCENT`(기본 80)에 해당하는 유닛 수에 도달하면 신규 호출이 429로 차단된다. `0` 또는 미설정이면 비활성. 카운터는 **프로세스 단위**이므로 멀티 워커·재시작 시 리셋된다. 구현·라벨은 `apps/matrix/app/external_api_budget.py` 참고.

---

## 7. 로깅·보안

- 비밀번호·API 키는 로그에 **마스킹** (`***`, length만)  
- 회원가입·인증 payload는 구조만 로그

---

## 8. 구현 전 체크리스트

- [ ] FOUNDATIONS + 본 문서 읽음  
- [ ] 해당 **프로젝트 docs** (API·env) 읽음  
- [ ] C-S-R 위치·`main.py` 등록 방식이 기존 코드와 일치  
- [ ] env 키 이름을 프로젝트 문서와 대조  
- [ ] 느린 외부 호출이 요청 경로를 막지 않음  

---

## 9. Cursor 프롬프트 (복사용)

```text
@docs/DevOps/FOUNDATIONS.md @docs/DevOps/Backend/BACKEND_RULES.md

공통 백엔드 지침을 인지한 뒤 [작업]을 구현하세요.
- Controller → Service → Repository
- main.py는 라우트·DI만
- env/제품 스펙은 docs/{프로젝트}/ 및 .env.example 참고
- 요청 범위 밖 수정 금지
```

---

## 부록: 현재 저장소(com.ragwatson) 참고 링크

> **제품 전용** — 다른 프로젝트에 그대로 적용하지 말고, “문서를 어디에 두는지” 참고용.

| 항목 | 위치 |
|------|------|
| HACCP Phase STEP | `docs/HACCP 개발/` |
| 앱 진입 | `backend/apps/main.py` |
| 회원 C-S-R 예 | `backend/apps/mfds/` |
| 식안나 캐시 예 | `backend/apps/services/food_safety_*_cache.py` |

env 키 예시는 해당 프로젝트 `.env` / HACCP 프롬프트 MD를 보며, **이 DevOps 문서에는 고정하지 않음**.

---

*최종 수정: 2026-05-20*
