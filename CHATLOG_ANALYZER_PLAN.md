# ShortsGak 프로젝트 개요 (Agent Reference)

## 1) 제품 목적
- VOD 채팅 로그에서 편집 후보 구간(하이라이트)을 자동 탐지한다.
- 핵심 신호:
  - 버킷별 전체 채팅량 급증
  - 키워드 빈도 급증
- 결과를 UI로 시각화하고 JSON/CSV로 내보낸다.

## 2) 현재 구현 범위
- 입력: `vod_id`, 키워드 배열, 버킷/점수 옵션
- 처리:
  - 채팅 로그 파싱
  - 버킷 집계
  - 하이라이트 스코어 계산 (`0.6 * volume_z + 0.4 * keyword_z`)
  - 연속 버킷 병합
- 출력:
  - summary
  - volume_series
  - keyword_series
  - highlights
  - parse_errors
- 내보내기: `/api/export`로 JSON/CSV 다운로드

## 3) 기술 스택(실사용 기준)
- Backend: FastAPI, Pydantic, Uvicorn, Requests
- Frontend: React + TypeScript + Vite
- Desktop: PyWebView + PyInstaller

## 4) 아키텍처
1. UI에서 분석 요청
2. 백엔드가 로그 파일 탐색/캐시/자동 수집 수행
3. 분석 엔진이 시계열/하이라이트 계산
4. API 응답을 UI가 차트/리스트로 렌더링
5. 데스크톱 모드에서는 같은 API를 내장 서버로 호출

## 5) 키워드 처리 정책(중요)
- 기본: `contains`, `case_sensitive=false`
- 반복 반응 정규화:
  - `ㅋ`, `ㅎ`, `ㅠ`, `ㅜ` 반복 축약
  - 감탄사 변형 통합: `허어어억`/`허어어어어어억` 등 → `헉`
- 정규화 후 키워드 dedupe로 이중 집계 방지

## 6) 비범위(아직 미구현)
- 실시간 라이브 스트림 분석
- 자동 클립 생성
- 분석 결과 영속 저장소(DB)

## 7) 다음 작업 가이드
1. 로그/캐시 루트를 `%LOCALAPPDATA%/ShortsGak`로 이관
2. 오류 UX 개선(로그 열기/진단 번들)
3. 설치형 배포(Inno Setup/MSIX) 자동화
4. 회귀 테스트 셋 정리(대표 VOD ID + 기대 지표)
