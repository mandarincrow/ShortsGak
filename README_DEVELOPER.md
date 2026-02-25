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

## 로그 위치
- 개발 실행 로그: `backend/logs/app.log`
- 실행파일 로그: `dist/ShortsGak/_internal/backend/logs/app.log`
- 빌드 로그: `logs/build_windows.log`
- 임시 빌드 로그: `%TEMP%/shortsgak_build_windows.log`

## 최근 주요 반영
- 프론트 API same-origin 호출 전환 (`Failed to fetch` 이슈 대응)
- Windows `os.getuid` 호환 처리
- 키워드 정규화 강화 (`헉` 계열 변형 통합)

## 참고 문서
- API 계약: `API_CONTRACT.md`
- 상태 요약: `DEVELOPMENT_START.md`
- 작업 큐: `IMPLEMENTATION_TICKETS.md`
- Windows 배포: `WINDOWS_PORTING_PLAN.md`
