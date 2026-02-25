# Implementation Tickets (Agent Queue)

이 문서는 다음 에이전트가 바로 집행할 수 있는 작업 목록입니다.

## 1) 완료 항목 (Done)

### D-01 Windows exe 빌드 파이프라인
- `scripts/build.bat`로 프론트 빌드 + Python 의존성 설치 + PyInstaller 빌드 자동화
- 산출물: `dist/ShortsGak/ShortsGak.exe`
- 실행 중 프로세스 잠금 대응(`ShortsGak.exe` 종료 후 빌드)

### D-02 데스크톱 실행 경로 안정화
- `run_desktop.py`에서 내부 FastAPI를 동적 포트로 기동
- WebView가 같은 origin으로 접근하도록 프론트 API 경로 수정

### D-03 API/파서 안정화
- VOD ID 기반 로그 탐색/캐시/자동수집 동작
- `os.getuid()` Windows 미지원 이슈 해결

### D-04 키워드 정규화 개선
- 반복 반응 정규화 + 감탄사(`헉` 변형) 통합
- 정규화 후 중복 키워드 제거

### D-05 UX 기본 요구 반영
- VOD ID 입력, 최근 VOD 캐시, 하이라이트 포커스, 차트 라벨/툴팁
- JSON/CSV 내보내기

### D-06 릴리즈 ZIP 패키징 자동화
- `scripts/package_release.bat` 추가
- `scripts/build.bat [version]`에서 ZIP 자동 생성 연동
- 산출물: `release/ShortsGak-win64-<version>.zip`
- ZIP 내부 사용자 안내 `README.txt` 포함

### D-07 문서/라이선스 정리
- 사용자/개발자 문서 분리 (`README.md`, `README_DEVELOPER.md`)
- MIT 라이선스 파일 추가 (`LICENSE`)

## 2) 다음 우선순위 (Next)

### N-01 로컬 데이터 경로 마이그레이션
- 목표: 실행 디렉터리 의존 제거
- 작업:
  - 로그/캐시를 `%LOCALAPPDATA%/ShortsGak` 기준으로 통일
  - 기존 경로에서 마이그레이션 처리

### N-02 장애 대응 UX
- 목표: "실패 원인 파악" 시간을 단축
- 작업:
  - UI 오류 메시지에 로그 파일 경로 노출
  - "로그 폴더 열기" 액션 제공

### N-03 릴리즈 패키징
- 목표: 비개발자 배포 가능 상태
- 작업:
  - 설치형 패키지(Inno Setup 또는 MSIX) 초안
  - 코드서명 적용 전략 수립

### N-04 회귀 검증 자동화(최소)
- 목표: 수정 후 핵심 플로우 깨짐 방지
- 작업:
  - 빌드 후 smoke test: 앱 기동, `/health`, 분석 1회, ZIP 생성 확인

### N-05 릴리즈 운영 메타데이터
- 목표: 배포 산출물 추적성 확보
- 작업:
  - 버전 규칙 확정(`vX.Y.Z`)
  - 릴리즈 노트 템플릿/체인지로그 템플릿 추가

## 3) 보류/아이디어 (Backlog)
- 진단 번들(zip) 내보내기
- 키워드 정규화 사전 확장 (`헐`, `허얼` 등)
- 대용량 로그 성능 최적화

## 4) 작업 원칙
- 기존 API 계약 유지 (breaking change 금지)
- 배포 안정성 우선 (빌드/실행/로그 확인 가능해야 함)
- 문서 변경 시 반드시 `API_CONTRACT.md`와 README 동기화
