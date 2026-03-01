# AGENT_CONTEXT — EPIC-01 Electron 재작성 (T03~T06 이어받기)

> 이 파일은 context가 초기화된 새 agent 세션이 EPIC-01 작업을 이어받기 위한 참조 문서입니다.  
> 브랜치: `feature/epic-01-electron` | 기준 repo: `mandarincrow/ShortsGak`

---

## 1. 배경 및 목표

**문제**: `pywebview`의 Windows 백엔드가 WebView2 외에 **pythonnet/CLR(.NET 런타임)** 에 의존.  
CLR 로딩 실패(`Python.Runtime.dll`)로 일부 사용자 PC에서 앱이 crash.

**해결**: Electron으로 교체 → Chromium 직접 번들 → 시스템 의존성 제로.

**배포 형태 유지**: zip 압축 폴더 (설치 불필요), `ShortsGak-win64-<DATE>.zip`

---

## 2. 최종 아키텍처

```
ShortsGak-win64-<DATE>/
└─ ShortsGak/
     ├─ ShortsGak.exe              ← Electron 진입점 (Chromium 번들)
     └─ resources/
          └─ backend.exe           ← PyInstaller headless FastAPI 서버
                                      (내부에 frontend/dist + backend/app 번들됨)
```

**런타임 흐름**:
1. `ShortsGak.exe` 시작
2. `net.createServer`로 빈 포트(N) 확보
3. `resources/backend.exe --port N` spawn
4. stdout에서 `LISTENING_PORT=N` 라인 확인 (파싱)
5. `GET http://127.0.0.1:N/health` 폴링 (30초, 250ms 간격)
6. 성공 → `BrowserWindow.loadURL("http://127.0.0.1:N")`
7. 창 닫힘 → `backend.exe` kill → `app.quit()`

---

## 3. 완료된 작업 (T01, T02) — PR 머지됨

### T01: `backend/backend_server.py`
- Electron이 `--port N`으로 실행하는 FastAPI 서버 진입점
- 핵심 계약:
  - `--port` 없으면 랜덤 포트 (개발용 fallback)
  - 바인딩 직전 **`LISTENING_PORT=<N>`** 을 stdout에 출력 (flush=True)
  - 포트 충돌 시 stderr에 `ERROR: ...` 출력 후 `sys.exit(1)`
  - 호스트는 `127.0.0.1` 고정 (--host 플래그 없음, 보안 원칙)
  - `log_config=None` (isatty() crash 방지)

### T02: `backend.spec` + pytest 환경
- `backend.spec`: PyInstaller headless 번들 명세
  - entry: `backend/backend_server.py`
  - `console=True`
  - pywebview/clr/tkinter **완전 제거**
  - 출력: `dist/backend/backend.exe`
  - datas: `frontend/dist` + `backend/app`
- `pytest.ini`, `tests/conftest.py`, `tests/test_backend_server.py` (9개 테스트)

---

## 4. 남은 작업

### T03: `electron/` 디렉터리 — GitHub Issue #4
**브랜치 명**: `feature/epic-01-t03-electron-app`  
**base**: `feature/epic-01-electron`

생성할 파일:

#### `electron/package.json`
```json
{
  "name": "shortsgak",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": { "start": "electron ." },
  "devDependencies": {
    "electron": "^latest",
    "electron-builder": "^latest"
  }
}
```

#### `electron/main.js` 구현 스펙
```js
const { app, BrowserWindow, dialog } = require('electron')
const { spawn } = require('child_process')
const net = require('net')
const path = require('path')

// 포트 탐색: net.createServer → listen(0) → server.address().port
// backend.exe 경로:
//   - 배포(frozen): path.join(process.resourcesPath, 'backend', 'backend.exe')
//   - 개발: path.join(__dirname, '..', 'dist', 'backend', 'backend.exe')
// spawn 후 stdout readline으로 'LISTENING_PORT=N' 파싱
// health poll: 30초, 250ms 간격, fetch('http://127.0.0.1:N/health')
// BrowserWindow: width:1100, height:760, nodeIntegration:false, contextIsolation:true
// 창 닫힘(window-all-closed): backendProc.kill() → app.quit()
// 실패 시: dialog.showErrorBox('ShortsGak', '서버 시작 실패...')
```

#### `electron/electron-builder.yml`
```yaml
appId: com.mandarincrow.shortsgak
productName: ShortsGak
directories:
  output: dist/electron
files:
  - main.js
  - package.json
extraResources:
  - from: ../dist/backend
    to: backend
    filter: ["**/*"]
win:
  target:
    - target: portable
      arch: [x64]
```

**TDD**: `electron/tests/` 에 Jest 또는 순수 Node.js 테스트 작성 먼저.  
포트 탐색 함수, LISTENING_PORT 파싱 함수를 `electron/utils.js`로 분리해 단위 테스트 가능하게.

---

### T04: 빌드 스크립트 수정 — GitHub Issue #5
**브랜치 명**: `feature/epic-01-t04-build-scripts`  
**base**: `feature/epic-01-electron`  
**의존**: T02, T03 머지 후

수정 파일: `scripts/build.bat`, `scripts/build.sh`, `scripts/package_release.bat`

현재 `build.bat` 구조 (수정 대상):
- Step 1: `cd frontend && npm install && npm run build` → **유지**
- Step 2: Python venv 생성 + 패키지 설치 → pywebview, pythonnet 제거
- Step 3: `pyinstaller ShortsGak.spec` → **`pyinstaller backend.spec --clean --noconfirm`** 로 변경, 출력 `dist/backend/`
- Step 4 (추가): `cd electron && npm install && npx electron-builder` → 출력 `dist/electron/`
- Step 5: `package_release.bat` 호출 → 출력 경로 `dist/electron/win-unpacked/` → zip

`package_release.bat` 수정:
- 현재 `dist/ShortsGak/` 패키징 → `dist/electron/win-unpacked/` 패키징으로 변경

---

### T05: `desktop_launcher/` 제거 — GitHub Issue #6
**브랜치 명**: `feature/epic-01-t05-remove-desktop-launcher`  
**base**: `feature/epic-01-electron`  
**의존**: T04 머지 후

삭제 대상:
- `desktop_launcher/run_desktop.py`
- `desktop_launcher/requirements.txt`
- `desktop_launcher/README.md`
- `ShortsGak.spec` (기존 pywebview 포함 spec)

---

### T06: README 갱신 — GitHub Issue #7
**브랜치 명**: `feature/epic-01-t06-readme`  
**base**: `feature/epic-01-electron`  
**의존**: T04 머지 후

- `README.md`: WebView2·.NET 요구사항 제거, 배포 사이즈 ~250MB로 갱신
- `README_DEVELOPER.md`: Electron 빌드 절차 추가, pywebview 항목 제거

---

## 5. 개발 원칙

1. **TDD** — 구현 전 테스트 먼저 작성. Red → Green 후 PR 오픈
2. **PR 워크플로우** — 절대 자동 머지 금지. PR 오픈 후 사용자 리뷰 대기
3. **셀프 리뷰** — PR 생성 전 코드를 직접 리뷰하고 개선사항이 있으면 반영 후 PR 코멘트에 변경 요약 작성
4. **브랜치 명**: `feature/epic-01-t0N-<kebab-description>`, base는 항상 `feature/epic-01-electron`
5. **GitHub 이슈 파일 방식**: PR/이슈 본문은 반드시 파일(`logs/_tmp.md`)로 작성 후 `--body-file`로 전달. PowerShell here-string 백틱 깨짐 방지
6. **임시 파일 정리**: `logs/_*.md` 사용 후 즉시 삭제
7. **Windows 우선**: `os.getuid()` 등 Unix 전용 API 사용 금지
8. **테스트 경로**: Python → `tests/`, Electron → `electron/tests/`

---

## 6. 현재 파일 트리 (epic 브랜치 기준)

```
backend/
  backend_server.py     ← T01 신규 (Electron 서버 진입점)
  app/
    main.py             ← FastAPI 앱 (GET /, GET /assets/*, POST /api/analyze 등)
    ...
backend.spec            ← T02 신규 (headless PyInstaller, dist/backend/ 출력)
ShortsGak.spec          ← 기존 (T05에서 삭제 예정)
desktop_launcher/       ← T05에서 전체 삭제 예정
  run_desktop.py
  requirements.txt
electron/               ← T03에서 신규 생성 예정
frontend/
  dist/                 ← npm run build 산출물 (빌드 전 없음)
tests/
  conftest.py
  test_backend_server.py
pytest.ini
scripts/
  build.bat             ← T04에서 수정 예정
  build.sh              ← T04에서 수정 예정
  package_release.bat   ← T04에서 수정 예정
```

---

## 7. 핵심 인터페이스 계약

### backend.exe ↔ Electron 프로토콜
| 항목 | 내용 |
|---|---|
| 실행 | `backend.exe --port <N>` |
| 시작 신호 | stdout 첫 줄: `LISTENING_PORT=<N>\n` |
| 준비 확인 | `GET http://127.0.0.1:<N>/health` → `200 OK` |
| 실패 신호 | stderr: `ERROR: Failed to bind ...`, exit code 1 |
| 종료 | Electron이 `backendProc.kill()` 호출 |

### FastAPI 주요 라우트
| 경로 | 설명 |
|---|---|
| `GET /health` | 헬스체크 (200 OK) |
| `GET /` | `frontend/dist/index.html` 서빙 |
| `GET /assets/*` | 정적 파일 |
| `POST /api/analyze` | 채팅 로그 분석 |
| `POST /api/export` | CSV/JSON 내보내기 |
