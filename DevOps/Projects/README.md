# 프로젝트·기능별 문서 (DevOps 밖)

`plan.docs/DevOps/` 는 **여러 개발에 공통**인 기본 지침만 둡니다.  
특정 제품의 Phase STEP, OpenAPI 서비스 번호, 화면 mock 규칙은 **이 폴더 밖** `plan.docs/` 에 둡니다.

---

## 현재 등록된 프로젝트 문서

| 프로젝트 | 경로 | 내용 |
|----------|------|------|
| HACCP Monitor AI | `plan.docs/HACCP 개발/` | Phase 1·2 Cursor STEP, API·화면 명세 |

---

## 새 프로젝트 추가 절차

1. `plan.docs/Projects/{이름}/README.md` 또는 `plan.docs/{이름}/` 생성  
2. STEP·스펙·env 표를 **프로젝트 MD에만** 작성 (DevOps에 복사하지 않음)  
3. 위 표에 링크 한 줄 추가  
4. Cursor 작업 시: `@plan.docs/DevOps/...` + `@plan.docs/Projects/{이름}/...` 함께 첨부  

---

## DevOps와의 관계

```
plan.docs/DevOps/          →  항상 적용 (레이어, state, 캐시 원칙)
plan.docs/HACCP 개발/      →  HACCP 작업할 때만 추가
plan.docs/Projects/foo/    →  다른 제품 작업할 때만 추가
```

---

*프로젝트 문서가 늘어나도 DevOps FOUNDATIONS는 자주 바꾸지 않습니다.*
