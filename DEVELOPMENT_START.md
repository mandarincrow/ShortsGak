# Development Handoff (AI Agent)

> 이 문서 하나로 현재 상태를 파악하고 작업을 바로 이어갈 수 있도록 기술합니다.

---

## 1. 현재 제품 상태

- **최신 빌드**: v0.1.1
- **동작 확인**: VOD ID `11933431` 기준 채팅 2784건, 하이라이트 03:08:30 탐지 정상
- **배포 산출물**: `dist/ShortsGak/ShortsGak.exe`

---

## 2. 디렉터리 구조

```
shorts-gak/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 앱 + 라우터
│   │   ├── analyzer.py        # 버킷 집계 + 하이라이트 스코어링
│   │   ├── chatlog_fetcher.py # Chzzk API 수집 (playerMessageTime 기준)
│   │   ├── chatlog_cache.py   # LRU 캐시 관리 (최대 5개)
│   │   ├── parser.py          # 로그 파싱 + 캐시/수집 오케스트레이션
│   │   ├── schemas.py         # Pydantic 모델 (API 계약)
│   │   └── logging_config.py  # 로깅 설정
│   └── data/chatlogs/         # 캐시 파일 (.log) 저장 위치
├── frontend/
│   └── src/
│       ├── App.tsx            # 메인 UI + 공유 state (chartWindowSize, chartPanCenter)
│       ├── LineChart.tsx      # 자체 SVG 차트 (zoom / pan / minimap)
│       ├── api.ts             # POST /api/analyze 호출
│       ├── types.ts           # TypeScript 타입 (API 응답 형태)
│       └── styles.css         # CSS 변수 기반 팔레트
├── desktop_launcher/
│   └── run_desktop.py         # PyWebView 런처 – 동적 포트, uvicorn 백그라운드 스레드
├── scripts/
│   ├── build.bat              # 전체 빌드 자동화 (컬러 출력, logs/ 로그 분리)
│   └── package_release.bat    # 기존 dist/ 를 ZIP으로만 묶기 (빌드 없음)
├── main.py                    # PyInstaller 엔트리포인트
└── ShortsGak.spec             # PyInstaller 스펙 (onedir)
```

---

## 3. 개발 환경 실행

### 사전 조건
- Python 3.12 (`py -3.12` 사용 가능)
- Node.js LTS + npm

### 백엔드

```powershell
cd f:\shorts-gak
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 프론트엔드 (별도 터미널)

```powershell
cd frontend
npm install
npm run dev
# localhost:5173 — /api/* 는 localhost:8000 으로 프록시됨 (vite.config.ts)
```

---

## 4. Windows exe 빌드

```powershell
cd f:\shorts-gak
scripts\build.bat v0.1.2
```

단계: 프론트 빌드 → pip 설치 → PyInstaller → ZIP 패키징

상세 출력: `logs/build_windows.log`
산출물: `dist/ShortsGak/ShortsGak.exe`, `release/ShortsGak-win64-v0.1.2.zip`

> **주의**: `package_release.bat` 단독 실행은 기존 `dist/` 를 그대로 ZIP으로 묶을 뿐입니다.
> 코드 변경 후에는 반드시 `build.bat` 을 사용하세요.

---

## 5. 로그 위치

| 상황 | 경로 |
|------|------|
| 빌드 로그 | `logs/build_windows.log` |
| 앱 실행 로그 (개발) | `backend/logs/app.log` |
| 앱 실행 로그 (배포 exe) | `dist/ShortsGak/_internal/backend/logs/app.log` |

---

## 6. 해결된 주요 이슈 (재현 방지용)

| 이슈 | 원인 | 해결 |
|------|------|------|
| 채팅 반응이 ~38초 이른 위치에 표시 | `messageTime` (벽시계 KST) 사용 | `playerMessageTime` (VOD 오프셋 ms) 으로 변경 |
| Windows `OSError` (1970년 datetime) | `datetime.timestamp()` Windows 미지원 | timedelta 산술 (`ts - _VOD_RELATIVE_BASE`) 사용 |
| 15초 버킷인데 30초 구간 표시 | 인접 버킷 무한 병합 | `max_merge_buckets=2` 제한 도입 |
| exe 재빌드 후에도 이전 코드 동작 | `package_release.bat` 만 실행 (dist 미갱신) | `build.bat` 전체 실행 필수 |
| PyWebView 환경 파일 다운로드 불가 | WebView 샌드박스 제한 | CSV/JSON 다운로드 버튼 제거 |
| PowerShell `Set-Content` 한국어 손상 | UTF-8 인코딩 문제 | Python `Path.write_text(encoding='utf-8')` 사용 |

---

## 7. 알려진 리스크

- PyWebView는 **WebView2 런타임** 필요 → 배포 대상 PC 사전 확인 요망
- 캐시/로그 경로가 현재 `backend/data/`, `backend/logs/` (실행 파일 내부) → N-01 참조
