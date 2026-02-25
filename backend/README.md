# Backend (FastAPI)

# Backend (FastAPI)

## 1) 설치
프로젝트 루트 기준:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## 2) 실행
프로젝트 루트 기준:

```bash
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

## 3) 주요 API
- `GET /health`
- `POST /api/analyze`
- `POST /api/export`

자세한 스키마는 루트의 `API_CONTRACT.md` 참고.

## 4) 로그/데이터 경로
- 실행 로그: `backend/logs/app.log`
- 채팅 캐시: `backend/data/chatlogs/`

## 5) 동작 메모
- `vod_id` 기준 로그를 우선 캐시에서 찾고, 없으면 자동 수집 시도
- 하이라이트 점수는 채팅량/키워드 z-score 혼합으로 계산
- 키워드 정규화 옵션 활성화 시 감탄사 변형(`허어어억` 등)을 동일 키워드로 집계

## 6) 장애 확인
1. `GET /health`가 200인지 확인
2. `backend/logs/app.log` 마지막 스택트레이스 확인
3. 입력 payload가 계약(`API_CONTRACT.md`)과 일치하는지 확인
