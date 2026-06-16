# Harness SSOT — 심볼릭 링크

`plan.docs` 아래 harness 파일이 **단일 원본(SSOT)** 입니다. 코드 폴더의 동명 파일은 **심볼릭 링크**로 연결합니다. (하드 링크 사용 금지.)

| SSOT (편집 위치) | 코드 트리 심볼릭 링크 |
|------------------|----------------------|
| `plan.docs/com.auditor/CLAUDE.md` | `com.auditor/CLAUDE.md` |
| `plan.docs/com.auditor/cursor-rules.md` | `com.auditor/cursor-rules.md` |
| `plan.docs/watcher.www/CLAUDE.md` | `watcher.www/CLAUDE.md` |
| `plan.docs/watcher.www/cursor-rules.md` | `watcher.www/cursor-rules.md` |

**루트** `CLAUDE.md` · `cursor-rules.md` — repo 루트에만 두고 `plan.docs` 링크 없음.

**앱** `apps/{domain}/_docs/cursor-rules.md` — 코드 트리 로컬 (심볼릭 링크 없음). 백엔드 SSOT [`plan.docs/com.auditor/cursor-rules.md`](com.auditor/cursor-rules.md) 경유.

> 구 파일명 `.cursorrules` → `cursor-rules.md` 로 통일. Cursor는 루트·하위 `cursor-rules.md`를 harness로 읽을 수 있음.

## Windows

```powershell
cd C:\Users\hi\Documents\com.foodopenlab

Remove-Item com.auditor\CLAUDE.md, com.auditor\cursor-rules.md -Force -ErrorAction SilentlyContinue
Remove-Item watcher.www\CLAUDE.md, watcher.www\cursor-rules.md -Force -ErrorAction SilentlyContinue

cd com.auditor
cmd /c mklink CLAUDE.md "..\plan.docs\com.auditor\CLAUDE.md"
cmd /c mklink cursor-rules.md "..\plan.docs\com.auditor\cursor-rules.md"

cd ..\watcher.www
cmd /c mklink CLAUDE.md "..\plan.docs\watcher.www\CLAUDE.md"
cmd /c mklink cursor-rules.md "..\plan.docs\watcher.www\cursor-rules.md"
```

검증:

```powershell
(Get-Item com.auditor\cursor-rules.md).LinkType   # SymbolicLink
(Get-Item com.auditor\cursor-rules.md).Target     # ..\plan.docs\com.auditor\cursor-rules.md
```

## Linux / macOS

```bash
ln -sf ../../plan.docs/com.auditor/CLAUDE.md com.auditor/CLAUDE.md
ln -sf ../../plan.docs/com.auditor/cursor-rules.md com.auditor/cursor-rules.md
ln -sf ../../plan.docs/watcher.www/CLAUDE.md watcher.www/CLAUDE.md
ln -sf ../../plan.docs/watcher.www/cursor-rules.md watcher.www/cursor-rules.md
```

## SSOT 편집

문서 수정은 **`plan.docs/{stack}/`** 를 기준으로 합니다.  
코드 트리의 `com.auditor/cursor-rules.md` 등은 심볼릭 링크이므로 열면 동일 SSOT를 편집합니다.
