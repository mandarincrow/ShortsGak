# Implementation Tickets (Agent Queue)

> 완료 항목은 재현/회귀 방지를 위해 보존합니다.
> 다음 에이전트는 **Next** 섹션부터 읽으세요.

---

## 완료 (Done)

### D-01 Windows exe 빌드 파이프라인
- `scripts/build.bat`: 프론트 빌드 → pip 설치 → PyInstaller → ZIP 자동화
- PowerShell 컬러 출력, 진행률 표시, 상세 로그는 `logs/build_windows.log` 분리

### D-02 데스크톱 실행 안정화
- `run_desktop.py`: uvicorn 백그라운드 스레드, 동적 포트 할당
- same-origin API 호출, Vite 개발 프록시 설정 (`vite.config.ts`)

### D-03 playerMessageTime 기반 타임스탬프
- Chzzk API `playerMessageTime` (VOD 오프셋 ms) 우선 사용, `messageTime` fallback
- `_VOD_RELATIVE_BASE = datetime(1970,1,1)` 상수 도입
- Windows `datetime.timestamp()` OSError → timedelta 산술로 대체
- `year == 1970` 감지로 base_time 자동 선택

### D-04 max_merge_buckets 병합 제한
- `AnalyzeOptions.max_merge_buckets` (기본 2, 1~20) 추가
- 병합 루프에서 초과 시 새 범위로 분리 → 15초 버킷이 30초로 보이던 버그 해결

### D-05 키워드 정규화
- `ㅋ`, `ㅎ`, `ㅠ`, `ㅜ` 반복 축약, 감탄사 변형 (`허어어억` 등) → `헉` 통합
- 정규화 후 중복 키워드 dedup

### D-06 차트 줌 / 패닝 / 미니맵
- `ZOOM_STEPS = [10,20,40,80,160,320,640,1280,∞]` 단계별 줌
- 패닝: ◀◀ ◀ ▶ ▶▶ 버튼, SVG 클릭 재센터, 미니맵 클릭/드래그
- 하이라이트 클릭 시 windowSize=40 자동 줌 + panCenter 이동
- `windowSize` / `panCenter` 를 `App.tsx` 로 lift → 두 차트 완전 연동

### D-07 UI 색상 팔레트 (애쉬핑크)
- CSS 변수 기반 팔레트 도입
- WCAG AA(4.5:1) 대비비 전수 검토 및 수정 (`h2` → `#935260`, 헤더 텍스트 → charcoal)

### D-08 다운로드 기능 제거
- PyWebView 환경 파일 다운로드 불가 확인
- JSON/CSV 다운로드 버튼 및 관련 코드 (`handleExport`, `exporting` state, import) 제거

---

## 다음 우선순위 (Next)

### N-01 사용자 데이터 경로 분리
- **목표**: 실행 파일 내부에 사용자 데이터(캐시/로그)가 섞이는 문제 해결
- **현재 경로**: `backend/data/chatlogs/`, `backend/logs/`
- **목표 경로**: `%LOCALAPPDATA%/ShortsGak/chatlogs/`, `%LOCALAPPDATA%/ShortsGak/logs/`
- **영향 파일**: `backend/app/chatlog_cache.py`, `backend/app/logging_config.py`
- **추가 작업**: 기존 경로에 캐시가 있으면 새 경로로 마이그레이션

### N-02 장애 대응 UX
- **목표**: 사용자가 오류 원인을 스스로 파악하거나 개발자에게 전달 가능
- **작업**:
  - UI 오류 메시지에 로그 파일 경로 표시
  - "로그 폴더 열기" 버튼 (PyWebView → Python `os.startfile` 연동)

### N-03 설치형 배포
- **목표**: 비개발자 배포 가능 상태
- **작업**:
  - Inno Setup 또는 MSIX 스크립트 작성
  - WebView2 런타임 번들 or 설치 유도 처리
  - 코드서명 전략 수립 (백신 오탐 방지)

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
