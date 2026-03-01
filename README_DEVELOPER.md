# ShortsGak Developer Guide

개발/빌드/문서 정합성 관점의 안내 문서입니다.

## 기술 스택
- Backend: FastAPI, Pydantic, Uvicorn, Requests
- Frontend: React, TypeScript, Vite
- Desktop: PyWebView, PyInstaller

## 프로젝트 구조
- `backend/` : API, 파서, 분석 엔진
- `frontend/` : 사용자 UI
- `desktop_launcher/` : 데스크톱 앱 엔트리
- `scripts/build.bat` : Windows 빌드 자동화
- `ShortsGak.spec` : PyInstaller 스펙

## 로컬 개발 실행

### 1) 의존성 설치
프로젝트 루트에서:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r backend\requirements.txt -r desktop_launcher\requirements.txt
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

산출물:
- `dist/ShortsGak/ShortsGak.exe`

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
| 대상 PC | WebView2 런타임 설치됨 |
| 빌드 중 | `ShortsGak.exe` 프로세스 종료 상태 (파일 잠금 방지) |

## PyInstaller 구조 (`ShortsGak.spec`)

- `onedir` 방식 → `dist/ShortsGak/` 폴더 전체가 배포 단위
- `sys._MEIPASS` 하위에 `frontend/dist/`, `backend/` 패키지 포함
- `run_desktop.py` 실행 흐름:
  1. frozen 환경 감지 (`hasattr(sys, '_MEIPASS')`)
  2. `sys.path` 에 backend 경로 추가
  3. 동적 포트 할당 (`socket.bind('', 0)`)
  4. uvicorn 백그라운드 스레드 기동
  5. `/health` 폴링으로 준비 완료 확인 (최대 30초)
  6. PyWebView 창 열기

## 릴리즈 전 체크리스트

- [ ] `scripts/build.bat` exit code 0
- [ ] `dist/ShortsGak/ShortsGak.exe` 더블클릭 기동 확인
- [ ] VOD 분석 1회 성공 (하이라이트 ≥ 1개)
- [ ] `release/ShortsGak-win64-<version>.zip` 생성 확인
- [ ] `dist/ShortsGak/_internal/backend/logs/app.log` 에 치명 예외 없음

## 권장 릴리즈 절차
1. `scripts\\build.bat vX.Y.Z` 실행
2. 산출물 확인
	- `dist/ShortsGak/ShortsGak.exe`
	- `release/ShortsGak-win64-vX.Y.Z.zip`
3. ZIP 압축 해제 후 exe 스모크 테스트
4. 이상 없으면 릴리즈 업로드

## 로그 위치
- 개발 실행 로그: `backend/logs/app.log`
- 실행파일 로그: `dist/ShortsGak/_internal/backend/logs/app.log`
- 빌드 로그: `logs/build_windows.log`
- 임시 빌드 로그: `%TEMP%/shortsgak_build_windows.log`

## 해결된 이슈 이력

| 이슈 | 원인 | 해결 |
|------|------|------|
| `Failed to fetch` | API URL 하드코딩 (`localhost:8000`) | same-origin 호출 + Vite 개발 프록시 |
| `module 'os' has no attribute 'getuid'` | Unix 전용 API | `hasattr(os, "getuid")` 가드 |
| `OSError` (year=1970 datetime) | `datetime.timestamp()` Windows 미지원 | timedelta 산술로 대체 |
| exe 재빌드 후에도 구버전 동작 | `package_release.bat` 만 실행 | `build.bat` 전체 실행 필수 |

## 참고 문서
- API 계약: `API_CONTRACT.md`
- 프로젝트 개요 & 알고리즘: `CHATLOG_ANALYZER_PLAN.md`
- 작업 큐: `IMPLEMENTATION_TICKETS.md`
- 사용자 문서: `README.md`
