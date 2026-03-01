# Implementation Tickets (Agent Queue)

---

## 진행 예정 (Epic)

### EPIC-01 pywebview → Electron 데스크탑 재작성

**배경**
pywebview의 Windows 백엔드는 WebView2(Edge) 외에 pythonnet/CLR(.NET 런타임)에 의존한다.  
CLR 로딩 실패(`Python.Runtime.dll`) 상황에서 앱이 crash하는 사례가 보고됐다.  
Electron으로 대체하면 Chromium을 직접 번들하므로 시스템 의존성이 사라진다.

**목표**
- 외부 런타임 설치 없이 `.exe` 더블클릭만으로 실행
- 기존 FastAPI + React 구조는 그대로 유지
- 배포 형태 유지: zip 압축 폴더 (설치 불필요)

**최종 아키텍처**

```
ShortsGak-win64-<DATE>/
└─ ShortsGak/
     ├─ ShortsGak.exe          ← Electron 진입점
     └─ resources/
          ├─ backend.exe        ← PyInstaller headless FastAPI 서버
          └─ (backend 내부에 frontend/dist 번들됨)
```

Electron main process → `backend.exe --port {N}` spawn → health poll → `BrowserWindow.loadURL` → 창 닫힘 → backend.exe kill

---

### EPIC-01-T01 `backend/backend_server.py` 신규 작성
- **목표**: Electron이 `--port` 인자로 실행할 수 있는 최소 FastAPI 서버 진입점
- **작업**:
  - `sys.argv` 파싱 (`--port` 없으면 랜덤 포트)
  - `uvicorn.run("app.main:app", ...)` 호출
  - frozen 환경(`sys._MEIPASS`) / dev 환경 양쪽 경로 처리
- **영향 파일**: `backend/backend_server.py` (신규)
- **의존성**: 없음 (선행 가능)

---

### EPIC-01-T02 `backend.spec` 신규 작성 (PyInstaller headless 전용)
- **목표**: `backend.exe` 단독 실행 가능 headless 서버 번들
- **작업**:
  - entry point: `backend/backend_server.py`
  - `console=True` (GUI 없음)
  - `datas`: `backend/app/`, `frontend/dist/` 포함 (FastAPI가 서빙)
  - `hiddenimports`: uvicorn/fastapi/starlette/app.* 유지, webview·clr·tkinter 전부 제거
  - 출력 경로: `dist/backend/`
- **영향 파일**: `backend.spec` (신규), 기존 `ShortsGak.spec` 은 백업 후 대체
- **의존**: EPIC-01-T01

---

### EPIC-01-T03 `electron/` 디렉터리 및 Electron 앱 작성
- **목표**: pywebview를 대체하는 Electron main process
- **작업**:
  - `electron/package.json`: `electron`, `electron-builder` 의존성
  - `electron/main.js`:
    - 빈 포트 탐색 (`net.createServer`)
    - `resources/backend.exe --port {N}` spawn (dev: `dist/backend/backend.exe`)
    - health poll (30초, 250ms 간격)
    - `BrowserWindow` 생성 (`width:1100, height:760`, `nodeIntegration:false`)
    - `loadURL("http://127.0.0.1:{N}")`
    - 창 닫힘 → backend 프로세스 kill → `app.quit()`
    - 비정상 종료 시 에러 다이얼로그 표시
  - `electron/electron-builder.yml`:
    - `extraResources`: `../dist/backend/**` → `resources/`
    - `win.target`: `portable` (zip 배포 호환)
    - `productName`: `ShortsGak`
- **영향 파일**: `electron/` (신규 디렉터리)
- **의존**: EPIC-01-T01

---

### EPIC-01-T04 빌드 스크립트 수정
- **목표**: 기존 `build.bat` / `build.sh` 를 Electron 빌드 파이프라인으로 교체
- **작업**:
  - Step 1 (frontend npm build) — **유지**
  - Step 2 (Python venv): pywebview, pythonnet 의존성 제거
  - Step 3 변경: `pyinstaller ShortsGak.spec` → `pyinstaller backend.spec`
  - Step 4 변경: `package_release.bat` 호출 전에 `cd electron && npm install && npx electron-builder` 추가
  - Step 5 (package_release.bat): 출력 경로 조정 (`electron/dist/` → zip)
- **영향 파일**: `scripts/build.bat`, `scripts/build.sh`, `scripts/package_release.bat`
- **의존**: EPIC-01-T02, EPIC-01-T03

---

### EPIC-01-T05 `desktop_launcher/` 제거
- **목표**: 더 이상 필요없는 pywebview 런처 코드 및 의존성 정리
- **작업**:
  - `desktop_launcher/run_desktop.py` 삭제
  - `desktop_launcher/requirements.txt` 삭제 (pywebview, pythonnet 제거)
  - `desktop_launcher/README.md` 내용 갱신 또는 삭제
  - `ShortsGak.spec` (기존) 아카이브 또는 삭제
- **영향 파일**: `desktop_launcher/` 전체, 기존 `ShortsGak.spec`
- **의존**: EPIC-01-T04

---

### EPIC-01-T06 README 및 개발자 가이드 갱신
- **목표**: 실행/빌드 방법 최신화
- **작업**:
  - `README.md`: 실행 환경 변경사항 반영 (WebView2 필요 없음)
  - `README_DEVELOPER.md`: Electron 추가, pywebview 관련 항목 제거, 빌드 절차 갱신
- **영향 파일**: `README.md`, `README_DEVELOPER.md`
- **의존**: EPIC-01-T04

---

## 다음 우선순위 (Next)

### N-02 장애 대응 UX
- **목표**: 사용자가 오류 원인을 스스로 파악하거나 개발자에게 전달 가능
- **작업**:
  - UI 오류 메시지에 로그 파일 경로 표시
  - "로그 폴더 열기" 버튼 (PyWebView → Python `os.startfile` 연동)

### N-04 Smoke Test 자동화
- **목표**: 빌드 후 핵심 플로우 깨짐 즉시 탐지
- **작업**:
  - `scripts/build.bat` 완료 후 `/health` → `POST /api/analyze` 자동 실행
  - `highlights` 비어있지 않으면 성공 판정

---

## Backlog

- 키워드 정규화 사전 확장 (`헐`, `허얼`, `ㄷㄷ` 등)
- 분석 파라미터 프리셋 저장/불러오기 (localStorage)
- 대용량 로그 (10만 건 이상) 성능 프로파일링
- 다국어 지원 (일본어 스트리머 대상)

---

## 작업 원칙

1. **API 계약 유지** — `POST /api/analyze` 요청/응답 shape 변경 시 `API_CONTRACT.md` 동기화 필수
2. **Windows 우선** — `os.getuid()` 등 Unix 전용 API 사용 금지
3. **빌드 검증** — 코드 수정 후 `npm run build` (프론트) 또는 `scripts/build.bat` (전체) 확인 필수
4. **타임스탬프** — `playerMessageTime` 기준 유지. `messageTime` 벽시계 기준 로직 추가 금지
5. **한국어 파일 쓰기** — PowerShell `Set-Content` 인코딩 이슈 → `python Path.write_text(encoding='utf-8')` 사용
