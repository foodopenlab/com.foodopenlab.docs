# 프론트엔드 공통 규칙 (React / Next.js)

> `@docs/DevOps/Frontend/REACT_RULES.md`  
> 전제: [FOUNDATIONS.md](../FOUNDATIONS.md) · 화면 STEP: `docs/{프로젝트}/`

---

## 1. 적용 범위

- **React** + **Next.js App Router** (`app/`, `page.tsx`)
- 클라이언트 API: 프로젝트가 정한 방식 (`fetch('/api/...')` + rewrite 등) — **상세 URL은 프로젝트 docs**
- 이 문서는 **state·폼·컴포넌트 구조** 등 공통 패턴만 다룸

---

## 2. `useState` — 남용하지 않는다

### 원칙

- 필드·UI 플래그마다 `useState`를 나열하지 않음  
- **한 페이지(또는 한 폼) = 하나의 상태 타입 + 하나의 `useState`**  
- 부분 갱신: `patchState(patch: Partial<PageState>)`  
- 폼 제출: **`FormData` + `Object.fromEntries(formData.entries())`**

### 권장 구조 (제네릭 예)

```tsx
type FormPageState = {
  // 폼 필드
  email: string
  password: string
  displayName: string
  // UI
  isSubmitting: boolean
  formError: string | null
  successMessage: string | null
}

const initialState: FormPageState = {
  email: "",
  password: "",
  displayName: "",
  isSubmitting: false,
  formError: null,
  successMessage: null,
}

export function ExampleFormPage() {
  const [state, setState] = useState<FormPageState>(initialState)

  const patchState = (patch: Partial<FormPageState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const formProps = Object.fromEntries(formData.entries())
    // formProps 파싱 → 검증 → fetch
  }

  const { email, isSubmitting, formError } = state
  // ...
}
```

### `name` · hidden

- 텍스트 input: `name="email"` 등 **HTML name** 필수  
- Radix `RadioGroup` / `Checkbox` 등 FormData에 안 들어가는 컨트롤: **hidden** 으로 값 동기화  

```tsx
<input type="hidden" name="role" value={state.role} readOnly />
```

### 예외

- 서로 완전히 독립이고 **2~3개 이하**일 때만 분리 `useState` 허용  
- 프로젝트에 **React Hook Form** 등이 도입되어 있으면 그 컨벤션 우선

---

## 3. 폼 Alert · 입력 시 에러 제거

### 원칙

- 검증/API 실패 메시지는 **`<Alert variant="destructive">`** (또는 동등 UI)로만 표시한다.  
- **브라우저 기본 검증 팝업**은 쓰지 않는다 → `<form noValidate>` + JS 검증.  
- 사용자가 **입력을 수정하기 시작하면** 에러 Alert만 제거한다. **성공 Alert는 입력으로 지우지 않는다.**

### 상태

```tsx
type FormPageState = {
  // ...
  formError: string | null      // 제출·검증 실패 — 입력 시 null
  successMessage: string | null // 제출 성공 — 새 제출 시에만 null
}
```

### 공통 헬퍼 (`frontend/lib/form-feedback.ts`)

```tsx
import { mergeFieldAndClearFormError } from "@/lib/form-feedback"

// controlled input
onChange={(e) => patchState(mergeFieldAndClearFormError("email", e.target.value))}

// 에러만 지울 때
patchState({ formError: null })
// 또는 patchState(formErrorClearPatch())
```

### 하지 않을 것

- `onChange`마다 `clearFeedback()`으로 **성공 메시지까지** 지우기  
- `required`만 두고 `noValidate` 없이 제출 → 브라우저 네이티브 alert/tooltip  
- 입력할 때마다 성공·실패 Alert를 한꺼번에 제거

---

## 4. API 호출

- 클라이언트 컴포넌트: `'use client'`  
- `fetch` URL·rewrite 규칙은 **프로젝트 `next.config` + 프로젝트 docs** 가 SSOT  
- 로딩 / 에러 / 빈 상태를 UI에 표시 (무한 스피너만 두지 않음)

---

## 5. UI·파일 위치 (일반)

| 종류 | 권장 위치 |
|------|-----------|
| 라우트 페이지 | `{app_root}/app/{route}/page.tsx` |
| 공통 컴포넌트 | `{app_root}/components/{domain}/` |
| mock (백엔드 전) | `{app_root}/lib/mocks/` — 프로젝트 정책 따름 |

기존 저장소의 `components/ui/`, Tailwind·shadcn 패턴을 **읽고 맞춤**.

---

## 6. 체크리스트 (리뷰·PR)

- [ ] FOUNDATIONS + 본 문서 읽음  
- [ ] 필드별 `useState` 4개 이상 → 단일 객체로 합칠 수 있는지  
- [ ] `handleSubmit`이 `FormData` / `e.currentTarget` 사용하는지  
- [ ] controlled input에 `name` 있는지  
- [ ] `noValidate` + 입력 시 `formError`만 제거하는지  
- [ ] 프로젝트 docs의 API 경로·응답 타입과 일치하는지  

---

## 7. Cursor 프롬프트 (복사용)

```text
@docs/DevOps/FOUNDATIONS.md @docs/DevOps/Frontend/REACT_RULES.md

공통 프론트 지침을 인지한 뒤 [작업]을 구현하세요.

useState가 필드마다 여러 개면 단일 객체 + patchState로 압축하고,
제출은 FormData + Object.fromEntries 패턴을 사용하세요.

- input name 유지, Radix는 hidden 동기화
- 기존 UI·동작 유지, 요청 파일만 수정
```

### 짧은 버전

```text
@docs/DevOps/Frontend/REACT_RULES.md — useState 객체 압축 + FormData 제출 패턴으로 리팩터링해 주세요.
```

---

## 부록: 현재 저장소(com.ragwatson) 참고

| 항목 | 위치 |
|------|------|
| 폼 state 예 | `frontend/app/signup/page.tsx` |
| 입력 시 에러 Alert 제거 | `frontend/lib/form-feedback.ts` |
| HACCP UI STEP | `docs/HACCP 개발/haccp_monitor_cursor_prompt.md` |

---

*최종 수정: 2026-05-20*
