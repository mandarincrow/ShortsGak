# ShortsGak Developer Guide

개발/빌드/문서 정합성 관점의 안내 문서입니다.

## 기술 스택
- Backend: FastAPI, Pydantic, Uvicorn, Requests
- Frontend: React, TypeScript, Vite
- Desktop: Electron, PyInstaller

## 프로젝트 구조
- `backend/` : API, 파서, 분석 엔진
- `frontend/` : 사용자 UI
- `electron/` : Electron main process (데스크탑 앱 진입점)
- `scripts/build.bat` : Windows 빌드 자동화
- `backend.spec` : PyInstaller 스펙 (headless 서버 바이너리)

## 로컬 개발 실행

### 1) 의존성 설치
프로젝트 루트에서:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

### 2) 백엔드 실행

```bash
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

### 3) 프론트 실행

```bash
cd frontend
npm run dev
```

### 4) 접속
- UI: http://localhost:5173
- Health: http://localhost:8000/health

## Windows 빌드
루트에서:

```bat
scripts\build.bat
```

빌드 단계:
1. **Frontend** — `npm run build` → `frontend/dist/`
2. **Python 의존성** — `backend/requirements.txt` 설치
3. **backend.exe** — `pyinstaller backend.spec` → `dist/backend/backend.exe`
4. **Electron 앱** — `cd electron && npm install && npx electron-builder` → `electron/dist/electron/win-unpacked/`
5. **Release ZIP** — `package_release.bat` → `release/ShortsGak-win64-<DATE>.zip`

산출물:
- `electron/dist/electron/win-unpacked/ShortsGak.exe`

## Release ZIP 패키징

### 빌드와 함께 ZIP 생성
`scripts\build.bat` 실행 시 자동으로 `release/`에 ZIP이 생성됩니다.

### ZIP만 별도 생성
```bat
scripts\package_release.bat
```

버전을 직접 지정하려면:
```bat
scripts\package_release.bat v0.1.0
```

산출물 예시:
- `release/ShortsGak-win64-v0.1.0.zip`
- ZIP 내부에 사용자 안내용 `README.txt`가 함께 포함됩니다.

## 빌드 사전 조건

| 항목 | 요건 |
|------|------|
| Python | 3.12 (`py -3.12` 사용 가능) |
| Node.js | LTS + npm |
| 빌드 환경 | 불러오기 전 `ShortsGak.exe` 프로세스 종료 (파일 잠금 방지) |

## Electron 앱 구조 (`electron/`)

```
electron/
  main.js          ← Electron main process
  utils.js         ← findFreePort(), parseListeningPort() 유틸리티
  package.json
  electron-builder.yml
  tests/
    utils.test.js  ← 순수 Node.js 단위 테스트
```

Electron 실행 흐름:
1. `findFreePort()` → 가용 포트(N) 확보
2. `resources/backend/backend.exe --port N` spawn (frozen) / `dist/backend/backend.exe` (dev)
3. stdout readline — `LISTENING_PORT=N` 수신 (30초 타임아웃)
4. `GET http://127.0.0.1:N/health` 폴링 (250ms 간격)
5. `BrowserWindow(1100×760)` → `loadURL(http://127.0.0.1:N)`
6. 창 닫힐 시 `backendProc.kill()` → `app.quit()`

## backend.exe PyInstaller 구조 (`backend.spec`)

- headless `console=True` 실행파일
- 진입점: `backend/backend_server.py`
- `dist/backend/backend.exe` 산출
- 데이터 포함: `frontend/dist/`, `backend/app/`
- pywebview · clr · tkinter 완전 제거

## 릴리즈 전 체크리스트

- [ ] `scripts/build.bat` exit code 0
- [ ] `electron/dist/electron/win-unpacked/ShortsGak.exe` 더블클릭 기동 확인
- [ ] VOD 분석 1회 성공 (하이라이트 ≥ 1개)
- [ ] `release/ShortsGak-win64-<version>.zip` 생성 확인
- [ ] `ShortsGak/resources/backend/logs/app.log` 에 치명 예외 없음

## 권장 릴리즈 절차
1. `scripts\\build.bat vX.Y.Z` 실행
2. 산출물 확인
	- `electron/dist/electron/win-unpacked/ShortsGak.exe`
	- `release/ShortsGak-win64-vX.Y.Z.zip`
3. ZIP 압축 해제 후 exe 스모크 테스트
4. 이상 없으면 릴리즈 업로드

## 로그 위치
- 개발 실행 로그: `backend/logs/app.log`
- 실행파일 로그: `ShortsGak/resources/backend/logs/app.log`
- 빌드 로그: `logs/build_windows.log`

## 해결된 이슈 이력

| 이슈 | 원인 | 해결 |
|------|------|------|
| `Failed to fetch` | API URL 하드코딩 (`localhost:8000`) | same-origin 호출 + Vite 개발 프록시 |
| `module 'os' has no attribute 'getuid'` | Unix 전용 API | `hasattr(os, "getuid")` 가드 |
| `OSError` (year=1970 datetime) | `datetime.timestamp()` Windows 미지원 | timedelta 산술로 대체 |
| exe 재빌드 후에도 구버전 동작 | `package_release.bat` 만 실행 | `build.bat` 전체 실행 필수 |
| `Python.Runtime.dll` 로드 실패 (CLR crash) | pythonnet 의존 (PyWebView Windows 백엔드) | Electron 전환으로 **해결됨** (시스템 .NET 런타임 불필요) |

## 참고 문서
- API 계약: `API_CONTRACT.md`
- 프로젝트 개요 & 알고리즘: `CHATLOG_ANALYZER_PLAN.md`
- 사용자 문서: `README.md`
