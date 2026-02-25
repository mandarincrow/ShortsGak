# Desktop Launcher

## 목적
- FastAPI + 프론트를 내부에서 자동 기동해 데스크톱 앱처럼 실행

## 개발 실행 (Windows)
프로젝트 루트 기준:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r backend\requirements.txt -r desktop_launcher\requirements.txt
cd frontend && npm install && npm run build
cd ..
.venv\Scripts\python desktop_launcher\run_desktop.py
```

## 배포 빌드
루트에서 아래 명령 1회:

```bat
scripts\build.bat
```

결과: `dist/ShortsGak/ShortsGak.exe`

## 런타임 동작
- 앱 시작 시 내부 서버를 `127.0.0.1` 동적 포트로 기동
- WebView 창에서 same-origin으로 API 호출
- 창 종료 시 프로세스 종료

## 장애 확인 포인트
- 실행 로그: `dist/ShortsGak/_internal/backend/logs/app.log`
- 빌드 로그: `logs/build_windows.log`
- 흔한 이슈:
  - `Failed to fetch`: 프론트-백엔드 origin 불일치
  - WebView2 미설치: 창 초기화 실패 가능
