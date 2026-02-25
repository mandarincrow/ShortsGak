# Windows Build & Release Guide

---

## 1. 빌드 단일 명령

```powershell
cd f:\shorts-gak
scripts\build.bat v0.1.2
```

내부 실행 순서:
1. `npm install && npm run build` (frontend/)
2. `.venv` 생성 + `pip install -r backend/requirements.txt`
3. `pyinstaller ShortsGak.spec --clean --noconfirm`
4. `release/ShortsGak-win64-<version>.zip` 패키징

터미널에는 단계별 컬러 요약만 출력, 상세 로그는 `logs/build_windows.log` 에 기록.

---

## 2. 빌드 사전 조건

| 항목 | 요건 |
|------|------|
| Python | 3.12 권장 (`py -3.12` 사용 가능) |
| Node.js | LTS + npm |
| 대상 PC | WebView2 런타임 설치됨 |
| 빌드 중 | `ShortsGak.exe` 프로세스 종료 상태 (파일 잠금 방지) |

---

## 3. 산출물

| 파일 | 설명 |
|------|------|
| `dist/ShortsGak/ShortsGak.exe` | 실행 파일 |
| `release/ShortsGak-win64-<version>.zip` | 배포용 ZIP |
| `logs/build_windows.log` | 빌드 상세 로그 |

---

## 4. PyInstaller 구조 (`ShortsGak.spec`)

- `onedir` 방식 → `dist/ShortsGak/` 폴더 전체가 배포 단위
- `sys._MEIPASS` 하위에 `frontend/dist/`, `backend/` 패키지 포함
- `run_desktop.py` 실행 흐름:
  1. frozen 환경 감지 (`hasattr(sys, '_MEIPASS')`)
  2. `sys.path` 에 backend 경로 추가
  3. 동적 포트 할당 (`socket.bind('', 0)`)
  4. uvicorn 백그라운드 스레드 기동
  5. `/health` 폴링으로 준비 완료 확인 (최대 30초)
  6. PyWebView 창 열기

---

## 5. 로그 위치

| 상황 | 경로 |
|------|------|
| 빌드 로그 | `logs/build_windows.log` |
| 앱 로그 (개발) | `backend/logs/app.log` |
| 앱 로그 (배포 exe) | `dist/ShortsGak/_internal/backend/logs/app.log` |

---

## 6. 릴리즈 전 체크리스트

- [ ] `scripts/build.bat` exit code 0
- [ ] `dist/ShortsGak/ShortsGak.exe` 더블클릭 기동 확인
- [ ] VOD 분석 1회 성공 (하이라이트 ≥ 1개)
- [ ] `release/ShortsGak-win64-<version>.zip` 생성 확인
- [ ] `dist/ShortsGak/_internal/backend/logs/app.log` 에 치명 예외 없음

---

## 7. 해결된 이슈 이력

| 이슈 | 원인 | 해결 |
|------|------|------|
| `Failed to fetch` | API URL 하드코딩 (`localhost:8000`) | same-origin 호출 + Vite 개발 프록시 |
| `module 'os' has no attribute 'getuid'` | Unix 전용 API | `hasattr(os, "getuid")` 가드 |
| `OSError` (year=1970 datetime) | `datetime.timestamp()` Windows 미지원 | timedelta 산술로 대체 |
| exe 재빌드 후에도 구버전 동작 | `package_release.bat` 만 실행 | `build.bat` 전체 실행 필수 |

---

## 8. 다음 과제

- **N-01**: 사용자 데이터 경로 → `%LOCALAPPDATA%/ShortsGak/` (현재 exe 내부 혼재)
- **N-03**: 설치형 배포 (Inno Setup/MSIX) + 코드서명
