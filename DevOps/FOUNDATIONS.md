# DevOps 공통 기반 (Foundations)

> `@plan.docs/DevOps/FOUNDATIONS.md` — 스택·제품을 가리지 않는 **기본 방향성**.  
> FastAPI·React 구체 문법은 [Backend](./Backend/BACKEND_RULES.md)·[Frontend](./Frontend/REACT_RULES.md) 를 따릅니다.

---

## 1. 문서가 코드보다 먼저다 (SSOT)

- 코딩 규칙·API 계약·env 키 이름은 **문서에 먼저** 정하고, 코드는 문서를 따른다.  
- 에이전트는 `.cursorrules` 요약만 보고 구현하지 않는다. **`plan.docs/` 해당 MD를 Read 또는 `@` 첨부** 후 진행.  
- 한 제품의 상세 STEP·OpenAPI 서비스 번호·화면 목록은 **DevOps가 아닌** `plan.docs/{프로젝트}/` 에 둔다.

---

## 2. 레이어 분리 (백엔드)

HTTP 진입 · 비즈니스 로직 · 저장·외부 I/O를 **한 파일에 섞지 않는다.**

| 레이어 | 책임 | 하지 않을 것 |
|--------|------|----------------|
| **Controller** (또는 Router handler) | 요청 검증, 응답 형식, HTTP 상태 | SQL, 외부 API 상세, 복잡한 분기 |
| **Service** | 유스케이스·트랜잭션 경계·오케스트레이션 | HTTP 객체에 직접 의존 (가능한 한) |
| **Repository** | DB·파일·외부 API 호출 | UI·HTTP 상태코드 결정 |

앱 진입점(`main.py` 등)은 **라우트 등록·의존성 주입** 위주. 새 기능은 도메인 모듈에 추가.

---

## 3. 환경 변수·비밀

- API 키·DB URL·시크릿은 **코드·저장소에 하드코딩 금지**.  
- 키 **이름**은 프로젝트 `.env.example` 또는 **프로젝트 docs**에 문서화. DevOps는 “이름을 바꾸지 말 것” 원칙만 고정.  
- 로컬: `.env` / 배포: 플랫폼 시크릿. 문서와 실제 키 이름이 다르면 **문서를 먼저 수정**.

---

## 4. 외부 API·느린 I/O

- 공공 API·대량 조회는 **요청 스레드에서 동기로 오래 붙잡지 않는다** (프록시 타임아웃·워커 정체 방지).  
- 권장: **디스크/메모리 캐시** → 있으면 **즉시 반환** → 갱신은 **백그라운드** (스케줄러·별도 스레드).  
- 캐시 없을 때만 동기 갱신을 허용하고, 실패 시 기존 캐시(stale) 제공을 검토.

---

## 5. 데이터베이스

- 커넥션 풀: 끊긴 연결 재사용 방지 (`pool_pre_ping` 등) — 서버리스 DB에 유리.  
- `OperationalError`(연결 끊김)는 500 스택 대신 **503 + 재시도 안내** 등 사용자 메시지.  
- “DB 없이도 동작”과 “DB 필수” 엔드포인트를 **의도적으로 구분** (`Depends(get_db)` vs optional).

---

## 6. 프론트엔드 state·폼

- 관련 state는 **필드마다 `useState` 남발하지 않음** → **단일 객체 + 부분 갱신** (`patchState`).  
- 폼 제출: **`FormData` + `Object.fromEntries(formData.entries())`** 우선.  
- `name` 속성·Radix 등 FormData 미포함 컨트롤은 **hidden** 동기화.  
- 상세: [Frontend/REACT_RULES.md](./Frontend/REACT_RULES.md)

---

## 7. 변경 범위·검증

- 요청과 **직접 연결된 diff**만. 인접 “정리” 리팩터링·무분별한 README 수정 금지.  
- 완료 기준: 테스트·빌드·린트·수동 확인 중 **하나 이상** 재현 가능하게.  
- 기존 저장소의 네이밍·폴더·import 스타일을 **읽고 맞춘다**.

---

## 8. Cursor 에이전트 워크플로

```
1. FOUNDATIONS + 스택 RULES 읽기
2. (해당 시) 프로젝트 docs 읽기
3. 계획·성공 기준 한두 문장
4. 구현 (레이어·캐시·state 원칙 준수)
5. 검증 명령·결과 보고
```

짧은 사용자 지시 예:

```text
@plan.docs/DevOps/FOUNDATIONS.md @plan.docs/DevOps/Backend/BACKEND_RULES.md
[작업]. 프로젝트 스펙은 plan.docs/HACCP 개발/ 해당 파일 참고.
```

---

*이 문서는 제품명·특정 env 키·특정 URL을 넣지 않습니다. 제품별 내용은 프로젝트 docs에 둡니다.*
