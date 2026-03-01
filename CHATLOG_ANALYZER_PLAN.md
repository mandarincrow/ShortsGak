# ShortsGak – 프로젝트 개요 (Agent Reference)

> 추후 AI 에이전트가 맥락 없이 이 파일 하나만 읽고 작업을 바로 이어갈 수 있도록 기술합니다.

---

## 1. 제품 목적

Chzzk VOD의 채팅 로그에서 **편집 후보 구간(하이라이트)** 을 자동 탐지하고 시각화하는 데스크톱 도구입니다.

- 핵심 신호: 버킷별 채팅량 급증 × 키워드 빈도 급증
- 최종 사용자: 스트리머 편집자 (비개발자)
- 배포 형태: Windows 단일 `.exe` (더블클릭 실행)

---

## 2. 아키텍처

```
[PyWebView 창]
    │  same-origin HTTP
    ▼
[FastAPI (uvicorn, 동적 포트, 백그라운드 스레드)]
    │
    ├─ GET  /health
    └─ POST /api/analyze
           ├─ parser.py          → 로그 탐색 / 캐시 / 자동 수집
           ├─ chatlog_fetcher.py → Chzzk API 수집 (playerMessageTime 기준)
           ├─ chatlog_cache.py   → 캐시 관리 (최대 5개 LRU)
           └─ analyzer.py        → 버킷 집계 + 하이라이트 스코어링
```

- **개발 모드**: Vite dev(`localhost:5173`) + FastAPI(`localhost:8000`), Vite proxy로 `/api` 경유
- **배포 모드**: Vite 빌드 결과물을 FastAPI가 정적 파일로 서빙, 단일 origin

---

## 3. 분석 알고리즘

### 3-1. 타임스탬프 처리

채팅 로그는 Chzzk API의 `playerMessageTime` (VOD 재생 오프셋, ms) 기준으로 저장됩니다.

```
playerMessageTime (ms)
  └─ datetime.utcfromtimestamp(ms / 1000)
       └─ 1970-01-01 기반 epoch datetime  (year == 1970)
```

- `year == 1970` → `_VOD_RELATIVE_BASE = datetime(1970,1,1,0,0,0)` 를 기준점으로 offset 계산
- 레거시 로그(`messageTime` 벽시계 KST) → 첫 채팅을 기준점으로 사용 (하위 호환)
- **Windows 주의**: `datetime.timestamp()` 가 1970년 datetime 에서 OSError 발생 → timedelta 산술 사용

```python
# analyzer.py
_VOD_RELATIVE_BASE = datetime(1970, 1, 1, 0, 0, 0)

def _bucket_start(ts, bucket_size_seconds):
    offset_sec = int((ts - _VOD_RELATIVE_BASE).total_seconds())
    bucket_offset = offset_sec // bucket_size_seconds * bucket_size_seconds
    return _VOD_RELATIVE_BASE + timedelta(seconds=bucket_offset)
```

### 3-2. 스코어링

```
score[i] = 0.6 × volume_z[i]  +  0.4 × keyword_z[i]
```

z-score는 버킷 전체 벡터 기준. `score ≥ min_highlight_score` 인 버킷이 후보.

### 3-3. 버킷 병합

- 인접 후보 버킷을 병합해 연속 구간으로 확장
- `max_merge_buckets` (기본 2) 초과 시 병합 차단 → 새 독립 하이라이트로 분리
- 스코어 내림차순 정렬 후 `max_highlights` 개 반환

### 3-4. 키워드 정규화

- `ㅋ`, `ㅎ`, `ㅠ`, `ㅜ` 2개 이상 반복 → 2개로 축약
- `허어어억` 등 감탄사 변형 → `헉` 통합
- 정규화 후 중복 키워드 dedup (이중 카운트 방지)

---

## 4. UI / 차트 UX

`frontend/src/LineChart.tsx` — 외부 라이브러리 없이 SVG 직접 렌더링.

### 두 차트 공유 State (`App.tsx` 에서 관리)

| state | 타입 | 설명 |
|-------|------|------|
| `chartWindowSize` | `number \| null` | null = 전체보기, number = 표시할 버킷 수 |
| `chartPanCenter` | `number \| null` | null = 자동(focusedX 중심), number = 명시적 중심 인덱스 |

두 state 를 두 차트에 props로 전달 → 어느 차트에서 조작해도 동기화됨.

### 기능 목록

| 기능 | 동작 |
|------|------|
| 줌 + / − | `ZOOM_STEPS = [10,20,40,80,160,320,640,1280,∞]` 단계별 |
| 패닝 버튼 | ◀◀ ◀ ▶ ▶▶ (전체보기 시 숨김) |
| SVG 클릭 재센터 | 클릭 위치 기준 panCenter 이동 |
| 미니맵 | 전체 데이터 축소판 + 뷰포트 rect, 클릭/드래그 패닝 |
| 하이라이트 클릭 | windowSize=40 자동 줌 + panCenter 이동 |
| 전체 버튼 | windowSize=null, panCenter=null, focusedX=null 리셋 |

---

## 5. 색상 팔레트

| CSS 변수 | 값 | 용도 |
|----------|----|------|
| `--c-main` | `#d49fac` | 애쉬핑크 – 패널 좌측 보더, 페이지 헤더 |
| `--c-light` | `#eecace` | 서브 버튼/칩 배경 |
| `--c-dark` | `#272d2d` | 전체 텍스트, VOD이동 버튼 |
| `--c-lime` | `#8dad18` | 주 액션 버튼, 포커스 input 보더 |
| `--c-yellow` | `#e0e843` | 활성 하이라이트, Reset 버튼 |
| `#935260` | — | `h2`, 차트 포커스 마커 (대비비 5.8:1 확보) |

> WCAG AA 기준(4.5:1) 충족 확인 완료.

---

## 6. 비범위 (현재 미구현)

- 실시간 라이브 스트림 분석
- 자동 클립 생성
- 분석 결과 영속 저장 (DB)
- 파일 다운로드 — PyWebView 환경에서 동작 불가 확인됨, UI에서 제거됨
