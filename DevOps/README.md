# DevOps · 공통 개발 지침 (Cursor SSOT)

이 디렉터리는 **프로젝트·기능에 관계없이** 여러 개발을 진행할 때 공통으로 따르는 **기본 지침**입니다.  
특정 제품(HACCP Monitor 등)의 API 스펙·화면 STEP은 `docs/DevOps`가 아니라 **`docs/` 아래 프로젝트·기능 문서**에 둡니다.

---

## 문서 계층 (우선순위)

| 계층 | 위치 | 역할 |
|------|------|------|
| **1. 공통 DevOps** | `docs/DevOps/` | 레이어 패턴, state 관리, env·캐시·DB 원칙 — **항상 먼저** |
| **2. 스택별** | `docs/DevOps/Backend/`, `docs/DevOps/Frontend/` | FastAPI·React 등 기술 스택 규칙 |
| **3. 프로젝트·기능** | 예: `docs/HACCP 개발/`, `docs/Projects/` | 해당 제품의 STEP·API·화면 명세 |
| **4. 저장소 하네스** | `.cursorrules`, `CLAUDE.md`, `backend/CURSOR.md` | 에이전트 주입용 **요약** (상세는 docs) |

**충돌 시:** 더 구체적인 **3. 프로젝트·기능** > **2. 스택** > **1. 공통** > `.cursorrules` 요약.

---

## 파일 목록

| 문서 | 대상 |
|------|------|
| [FOUNDATIONS.md](./FOUNDATIONS.md) | 전 스택 공통 원칙·docs 운용·Cursor 워크플로 |
| [Backend/BACKEND_RULES.md](./Backend/BACKEND_RULES.md) | API·DB·서버 (FastAPI 기준) |
| [Frontend/REACT_RULES.md](./Frontend/REACT_RULES.md) | UI·폼·클라이언트 state (React/Next.js 기준) |
| [Projects/README.md](./Projects/README.md) | 제품별 문서를 두는 위치·추가 방법 |

---

## Cursor 사용법

### 구현 전 (에이전트·사람 공통)

1. `@docs/DevOps/README.md` 또는 `@docs/DevOps/FOUNDATIONS.md` 로 계층 확인  
2. 작업 스택에 맞는 `@docs/DevOps/Backend/...` 또는 `Frontend/...` 읽기  
3. 해당 제품 작업이면 `@docs/HACCP 개발/...` 등 **프로젝트 문서** 추가  
4. 구현 후: 요청 범위만 diff, 검증 방법 명시  

### 표준 프롬프트 (복사용)

```text
@docs/DevOps/FOUNDATIONS.md @docs/DevOps/[Backend|Frontend]/..._RULES.md

공통 DevOps 지침을 인지한 뒤 [작업 설명]을 구현하세요.
프로젝트 전용 스펙이 필요하면 docs/ 아래 해당 프로젝트 MD를 추가로 읽으세요.
요청 범위 밖 수정 금지.
```

### 인지 완료 (에이전트용, 한 줄)

`docs 인지: FOUNDATIONS + [Backend|Frontend]_RULES (+ 프로젝트 MD명)`

---

## 새 프로젝트·기능 문서 추가 시

1. `docs/Projects/{프로젝트명}/` 또는 `docs/{프로젝트명}/` 에 README·STEP MD 생성  
2. **DevOps MD는 범용 원칙만** 유지 — 제품 API 번호·화면 목록은 프로젝트 문서로  
3. [Projects/README.md](./Projects/README.md) 인덱스에 한 줄 링크 추가  
4. 필요 시 `.cursorrules`에 해당 프로젝트 경로만 **한 줄** 보강  

---

*역할: 여러 개발의 **초반·공통** 지침. 제품 상세는 `docs/DevOps` 밖에 둡니다.*
