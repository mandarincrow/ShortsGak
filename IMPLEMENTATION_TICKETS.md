# Implementation Tickets (Agent Queue)

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
