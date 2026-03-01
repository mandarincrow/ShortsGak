# AGENT_CONTEXT -- EPIC-01 Electron 재작성

> context가 초기화된 새 agent 세션이 작업을 이어받기 위한 참조 문서.
> 기준 브랜치: `feature/epic-01-electron` | repo: `mandarincrow/ShortsGak`

---

## 1. 배경 및 목표

**문제**: `pywebview`의 Windows 백엔드가 WebView2 외에 **pythonnet/CLR(.NET 런타임)** 에 의존.
CLR 로딩 실패(`Python.Runtime.dll`)로 일부 사용자 PC에서 앱이 crash.

**해결**: Electron으로 교체 → Chromium 직접 번들 → 시스템 의존성 제로 (~250 MB).

**배포 형태**: zip 압축 폴더 (설치 불필요), `ShortsGak-win64-<DATE>.zip`

---

## 2. 최종 아키텍처

```
ShortsGak-win64-<DATE>/
└─ ShortsGak/
     ├─ ShortsGak.exe          <- Electron 진입점 (Chromium 번들)
     └─ resources/
          └─ backend/
               └─ backend.exe  <- PyInstaller headless FastAPI 서버
                                   (내부에 frontend/dist + backend/app 번들됨)
```

**런타임 흐름**:
1. `ShortsGak.exe` 시작
2. `findFreePort()` (`net.createServer`) 로 빈 포트(N) 확보
3. `resources/backend/backend.exe --port N` spawn
4. stdout readline으로 `LISTENING_PORT=N` 파싱
5. `GET http://127.0.0.1:N/health` 폴링 (30초, 250ms 간격)
6. 성공 → `BrowserWindow.loadURL("http://127.0.0.1:N")`
7. 창 닫힘 → `backend.exe` kill → `app.quit()`

---

## 3. 티켓 현황

| 티켓 | 내용 | PR | 상태 |
|------|------|----|------|
| T01 | `backend/backend_server.py` | #8 | 머지됨 |
| T02 | `backend.spec` + pytest | #9 | 머지됨 |
| T03 | `electron/` 앱 신규 작성 | #10 | 머지됨 |
| T04 | 빌드 스크립트 수정 | #11 | 머지됨 |
| T05 | `desktop_launcher/` 제거 | #12 | 머지됨 |
| T06 | README 갱신 | #13 | 머지됨 |

---

## 4. 완료된 작업 상세

### T01: `backend/backend_server.py`
- `--port N` 인자 파싱, 없으면 랜덤 포트 (개발 fallback)
- 바인딩 직전 `LISTENING_PORT=<N>` stdout 출력 (flush=True)
- 포트 충돌 → stderr `ERROR: ...` 후 `sys.exit(1)`
- 호스트 `127.0.0.1` 고정, `log_config=None` (isatty() crash 방지)

### T02: `backend.spec` + pytest 환경
- PyInstaller headless 번들: entry `backend/backend_server.py`, `console=True`
- pywebview / clr / tkinter 완전 제거, 출력: `dist/backend/backend.exe`
- datas: `frontend/dist` + `backend/app`
- `pytest.ini`, `tests/conftest.py`, `tests/test_backend_server.py` (9개 테스트)

### T03: `electron/` 앱 (셀프 리뷰 수정 포함)
- `electron/utils.js`: `findFreePort()`, `parseListeningPort()` 분리 (단위테스트 가능)
- `electron/main.js`: 전체 Electron main process
  - `error` / `exit` / timeout → 내부 `fail()` 헬퍼로 단일 rejection 경로 수렴
    → `dialog.showErrorBox` / `app.quit()` 이중 호출 버그 제거 (셀프 리뷰 픽스)
  - 모든 코드 경로에서 `rl.close()` 호출 (readline 누수 제거, 셀프 리뷰 픽스)
- `electron/package.json`: `"electron": "latest"`, `"electron-builder": "latest"`
- `electron/electron-builder.yml`: `dir` 타겟 → `electron/dist/win-unpacked/`
  - `extraResources`: `dist/backend/**` → `resources/backend`
- `electron/.gitignore`: `node_modules/`, `dist/` 제외
- `electron/tests/utils.test.js`: 9개 순수 Node.js 단위 테스트 (전부 통과)

### T04: 빌드 스크립트 (셀프 리뷰 수정 포함)
- `build.bat` / `build.sh`: 5단계 파이프라인
  - Step 2: `desktop_launcher/requirements.txt` 제거
  - Step 3: `pyinstaller backend.spec`
  - Step 4 (신규): `cd electron && npm install && npx electron-builder`
  - Step 4: `CSC_IDENTITY_AUTO_DISCOVERY=false` 설정 — winCodeSign symlink 오류 방지 (코드사이닝 비활성화)
  - Step 5: `package_release.bat`
- `package_release.bat`:
  - DIST_DIR: `electron\dist\win-unpacked`
  - 버그 수정 (셀프 리뷰): `win-unpacked\` 직접 압축 시 zip 내 폴더명 깨짐
    → `%TEMP%\shortsgak_staging_%RANDOM%\ShortsGak\` 에 복사 후 압축
    → zip 내부 구조: `ShortsGak\ShortsGak.exe` (기존과 동일)
  - README.txt 로그 경로: `ShortsGak\resources\backend\logs\app.log`

| T05: `desktop_launcher/` 제거 -- PR #12 (머지됨) |
- 삭제: `desktop_launcher/run_desktop.py`, `requirements.txt`, `README.md`
- `ShortsGak.spec` → `ShortsGak.spec.bak` 으로 아카이브
- `.gitignore`: `desktop_launcher/.venv/` 항목 제거

### T06: README 갱신 -- PR #13 (머지됨)
- `README.md`: 실행 환경 섹션 추가 (런타임 설치 불필요, ~250 MB), 로그 경로 갱신
- `README_DEVELOPER.md`: Electron 빌드 절차 5단계 반영, pywebview/WebView2 항목 전부 제거, Known Issues에 CLR crash 해결 항목 추가

---

## 5. 파일 트리 (feature/epic-01-electron 기준)

```
backend/
  backend_server.py     <- T01 (Electron 서버 진입점)
  app/
    main.py             <- FastAPI 앱 (GET /, GET /assets/*, POST /api/analyze 등)
    ...
backend.spec            <- T02 (headless PyInstaller, dist/backend/ 출력)
ShortsGak.spec.bak      <- T05에서 아카이브됨 (PR #12 머지됨)
electron/
  .gitignore
  main.js               <- T03 Electron main process
  utils.js              <- T03 findFreePort / parseListeningPort
  package.json
  electron-builder.yml  <- dir target, electron/dist/win-unpacked/
  tests/
    utils.test.js       <- 9개 단위 테스트
frontend/
  dist/                 <- npm run build 산출물 (빌드 전 없음)
tests/
  conftest.py
  test_backend_server.py
pytest.ini
scripts/
  build.bat             <- T04 수정됨 (5단계)
  build.sh              <- T04 수정됨 (5단계)
  package_release.bat   <- T04 수정됨 (staging 복사 후 zip)
```

---

## 6. 개발 원칙

### 6-1. TDD
- 구현 전 테스트 먼저 작성 (Red → Green)
- Python 테스트: `tests/` (pytest), Electron 테스트: `electron/tests/` (순수 Node.js)
- PR 오픈은 모든 테스트 통과 후

### 6-2. 셀프 리뷰 절차

PR 오픈 **전** 또는 오픈 **직후** 반드시 수행. 수정 사항이 있으면 추가 커밋 후 PR 코멘트에 요약 작성.

**검토 항목**:

| 분류 | 체크포인트 |
|------|-----------|
| 제어 흐름 | 에러 핸들러 중복 여부 -- 동일 이벤트에서 `app.quit()` / `dialog.showErrorBox` 가 두 번 발생하는 경로 없는지 |
| 리소스 정리 | `readline`, `net.createServer`, 파일 핸들 등 모든 IO가 resolve / reject / timeout 모든 경로에서 `close()` 되는지 |
| 에러 전파 | 모든 실패 경로가 사용자에게 노출되는지 (silent fail 없는지) |
| 보안 | 호스트 `127.0.0.1` 고정, `nodeIntegration:false`, `contextIsolation:true` |
| 버전 핀 | 존재하지 않는 버전을 고정하지 않았는지 (`^35.0.0` 등 미출시 major) |
| 경로 정확성 | zip 내부 폴더 구조가 의도한 대로인지 (`win-unpacked\` vs `ShortsGak\`) |
| 교차 참조 | 삭제/이동된 파일을 참조하는 다른 파일 (.gitignore, requirements.txt, README 등)이 없는지 |
| .gitignore | 새 디렉터리 추가 시 해당 `node_modules/`, `dist/` 규칙 포함 여부 |

**추가 커밋 메시지 형식**:
```
refactor(TX): self-review fixes -- <한 줄 요약>
fix(TX): <버그 설명>
```

**PR 코멘트**: 각 수정 항목마다 문제 / 수정 방법 서술. 머지 요청 전 기록.

### 6-3. PR 워크플로우
- 절대 자동 머지 금지. PR 오픈 후 사용자 리뷰 대기
- 브랜치 명: `feature/epic-01-t0N-<kebab-description>`
- base: 항상 `feature/epic-01-electron`

### 6-4. GitHub 이슈/PR 본문 작성
- 반드시 파일(`logs/_tmp.md`)로 작성 후 `--body-file` 로 전달 (PowerShell here-string 백틱 깨짐 방지)
- 사용 후 임시 파일 (`logs/_*.md`) 즉시 삭제
- **gh CLI 경로**: `C:\Program Files\GitHub CLI\gh.exe`

### 6-5. 기타
- **Windows 우선**: `os.getuid()` 등 Unix 전용 API 사용 금지
- **파일 쓰기**: PowerShell `Set-Content` 인코딩 이슈 → `python Path.write_text(encoding="utf-8")` 사용

---

## 7. 핵심 인터페이스 계약

### backend.exe <-> Electron 프로토콜
| 항목 | 내용 |
|------|------|
| 실행 | `backend.exe --port <N>` |
| 시작 신호 | stdout: `LISTENING_PORT=<N>\n` (flush=True) |
| 준비 확인 | `GET http://127.0.0.1:<N>/health` → `200 OK` |
| 실패 신호 | stderr: `ERROR: Failed to bind ...`, exit code 1 |
| 종료 | Electron이 `backendProc.kill()` 호출 |

### FastAPI 주요 라우트
| 경로 | 설명 |
|------|------|
| `GET /health` | 헬스체크 (200 OK) |
| `GET /` | `frontend/dist/index.html` 서빙 |
| `GET /assets/*` | 정적 파일 |
| `POST /api/analyze` | 채팅 로그 분석 |
| `POST /api/export` | CSV/JSON 내보내기 |
