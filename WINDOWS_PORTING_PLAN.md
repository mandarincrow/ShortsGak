# Windows Build & Release Guide (Agent)

## 1) 목적
- Windows 사용자에게 `ShortsGak.exe` 단일 실행 경험 제공
- 개발 도구 없이 더블클릭 실행 가능 상태 유지

## 2) 현재 전략
- 런처: PyWebView
- 서버: 내부 FastAPI(동적 포트)
- 패키징: PyInstaller (`ShortsGak.spec`)
- 자동화: `scripts/build.bat`, `scripts/package_release.bat`

## 3) 빌드 절차 (현재 표준)
1. 프론트 `npm install && npm run build`
2. 루트 `.venv` 생성/의존성 설치
3. `pyinstaller ShortsGak.spec --clean --noconfirm`
4. 릴리즈 ZIP 패키징
5. 산출물 확인:
  - `dist/ShortsGak/ShortsGak.exe`
  - `release/ShortsGak-win64-<version>.zip`

위 단계는 `scripts/build.bat`에서 자동 수행된다.

버전 지정 예시:
- `scripts\\build.bat v0.1.0`
- `scripts\\package_release.bat v0.1.0`

## 4) 빌드 전제 조건
- Python 3.12 권장 (`py -3.12` 사용 가능 상태)
- Node.js LTS + npm 설치
- 대상 PC에서 WebView2 런타임 사용 가능

## 5) 운영 로그 위치
- 빌드 로그(프로젝트): `logs/build_windows.log`
- 빌드 로그(임시): `%TEMP%/shortsgak_build_windows.log`
- 실행 로그(배포본): `dist/ShortsGak/_internal/backend/logs/app.log`

## 6) 자주 발생한 이슈와 해결 이력
- `Failed to fetch`
  - 원인: API URL 하드코딩(`localhost:8000`)
  - 해결: same-origin 호출 + dev proxy
- `module 'os' has no attribute 'getuid'`
  - 원인: Windows 비호환 API 사용
  - 해결: `hasattr(os, "getuid")` 가드

## 7) 다음 릴리즈 전 체크리스트
- [ ] `scripts/build.bat` 성공
- [ ] `dist/ShortsGak/ShortsGak.exe` 기동 확인
- [ ] `release/ShortsGak-win64-<version>.zip` 생성 확인
- [ ] VOD 분석 1회 성공 확인
- [ ] 내보내기(JSON/CSV) 확인
- [ ] 실행 로그에 치명 예외 없음

## 8) 남은 개선 과제
1. 로그/캐시 경로를 `%LOCALAPPDATA%/ShortsGak`로 이동
2. 설치형 배포(Inno Setup/MSIX) 도입
3. 코드서명 및 백신 오탐 대응
