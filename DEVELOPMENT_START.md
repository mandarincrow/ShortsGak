# Development Handoff (AI Agent)

이 문서는 "다음 에이전트가 바로 이어서 작업"하기 위한 현재 상태 요약입니다.

## 1) 현재 제품 상태
- 목표: VOD 채팅 로그 기반 하이라이트 후보 탐지 + 시각화 + 내보내기
- 실행 형태:
  - 개발 모드: FastAPI + Vite
  - 배포 모드: PyWebView + 내장 FastAPI + PyInstaller 실행파일
- 현재 빌드 산출물: `dist/ShortsGak/ShortsGak.exe`

## 2) 최근 반영된 핵심 변경
- `Failed to fetch` 해결
  - 원인: 프론트 API URL이 `http://localhost:8000` 고정
  - 조치: same-origin 기반 호출로 변경 (`frontend/src/api.ts`)
  - 개발 편의: Vite 프록시 추가 (`frontend/vite.config.ts`)
- Windows 호환성 버그 해결
  - 원인: `os.getuid()` 사용으로 Windows 런타임 오류
  - 조치: 가드 처리 (`backend/app/parser.py`)
- 키워드 정규화 고도화
  - `헉`, `허어어억`, `허어어어어어억`을 동일 키워드로 집계
  - 중복 키워드 입력 시 이중 카운트 방지
- 릴리즈 ZIP 자동화
  - `scripts/package_release.bat` 추가
  - `scripts/build.bat [version]` 실행 시 exe 빌드 + ZIP 생성까지 자동 수행
  - ZIP 내부에 사용자 안내 `README.txt` 포함
- 문서 체계 정리
  - 루트 `README.md`를 일반 사용자 중심으로 단순화
  - 개발자용 문서 분리: `README_DEVELOPER.md`
  - 라이선스 확정: `MIT` (`LICENSE` 추가)

## 3) 주요 디렉터리
- `backend/app`: API/파서/분석 엔진
- `frontend/src`: UI + API 호출
- `desktop_launcher`: 데스크톱 런처 엔트리
- `scripts/build.bat`: 윈도우 빌드 자동화
- `ShortsGak.spec`: PyInstaller 스펙

## 4) 실행/검증 빠른 경로

### 개발 실행
1. 루트에서 `.venv` 준비
2. 백엔드: `./.venv/Scripts/python -m uvicorn backend.app.main:app --reload --port 8000`
3. 프론트: `cd frontend && npm run dev`

### 윈도우 실행파일 빌드
1. 루트에서 `scripts\build.bat`
2. 결과물 확인: `dist\ShortsGak\ShortsGak.exe`

### 릴리즈 ZIP 생성
1. 빌드+패키징 동시: `scripts\build.bat v0.1.0`
2. ZIP만 생성: `scripts\package_release.bat v0.1.0`
3. 결과물 확인: `release\ShortsGak-win64-v0.1.0.zip`

## 5) 로그 위치(장애 분석 기준)
- 앱 실행 로그(개발): `backend/logs/app.log`
- 앱 실행 로그(배포 exe): `dist/ShortsGak/_internal/backend/logs/app.log`
- 빌드 로그: `logs/build_windows.log`
- 임시 빌드 로그: `%TEMP%/shortsgak_build_windows.log`

## 6) 현재 알려진 리스크
- `pywebview`는 WebView2 런타임 의존 (대상 PC 사전 확인 필요)
- `frontend` 의존성에 moderate 취약점 경고가 존재할 수 있음 (`npm audit` 확인 가능)

## 7) 다음 우선순위 제안
1. `%LOCALAPPDATA%/ShortsGak` 기반 로그/캐시 경로 정착
2. 에러 발생 시 UI에서 로그 열기/복사 UX 제공
3. 설치형 배포(Inno Setup/MSIX) 및 코드서명 체계 도입
