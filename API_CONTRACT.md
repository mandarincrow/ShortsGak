# API Contract

> Frontend ↔ Backend 계약.  
> Breaking change 금지. 변경 시 이 파일을 반드시 동기화하세요.

---

## 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 (`{"status":"ok"}`) |
| POST | `/api/analyze` | 분석 실행 |

> `/api/export` 는 백엔드에 남아있으나 **PyWebView 환경에서 파일 다운로드 불가** 확인으로 UI에서 제거됨.

---

## POST /api/analyze

### Request Body

```json
{
  "source": {
    "vod_id": "11933431"
  },
  "keywords": ["헉", "ㅋㅋㅋㅋ", "와"],
  "options": {
    "bucket_size_seconds": 30,
    "keyword_options": {
      "mode": "contains",
      "case_sensitive": false
    },
    "normalize_repeated_reactions": true,
    "min_highlight_score": 1.2,
    "max_highlights": 20,
    "max_merge_buckets": 2
  }
}
```

#### options 필드 상세

| 필드 | 타입 | 기본값 | 범위 | 설명 |
|------|------|--------|------|------|
| `bucket_size_seconds` | int | 30 | 5~300 | 버킷 크기 (초) |
| `keyword_options.mode` | `"contains"\|"exact"` | `"contains"` | — | 키워드 매칭 방식 |
| `keyword_options.case_sensitive` | bool | false | — | 대소문자 구분 |
| `normalize_repeated_reactions` | bool | true | — | 반복 반응 정규화 |
| `min_highlight_score` | float | 1.2 | — | 하이라이트 최소 z-score |
| `max_highlights` | int | 20 | 1~200 | 반환 최대 하이라이트 수 |
| `max_merge_buckets` | int | 2 | 1~20 | 인접 버킷 병합 최대 수 |

### Response Body

```json
{
  "summary": {
    "total_messages": 2784,
    "unique_users": 512,
    "start_time": "1970-01-01T00:00:10",
    "end_time": "1970-01-01T03:48:00",
    "vod_duration_sec": 13670,
    "vod_duration_label": "03:47:50",
    "avg_messages_per_minute": 12.24
  },
  "volume_series": [
    {
      "bucket_start": "1970-01-01T00:00:00",
      "bucket_start_offset_sec": 0,
      "bucket_start_offset_label": "00:00:00",
      "total_messages": 13,
      "unique_users": 11
    }
  ],
  "keyword_series": [
    {
      "bucket_start": "1970-01-01T00:00:00",
      "bucket_start_offset_sec": 0,
      "bucket_start_offset_label": "00:00:00",
      "keyword": "헉",
      "count": 4
    }
  ],
  "highlights": [
    {
      "start": "1970-01-01T03:08:30",
      "start_offset_sec": 11310,
      "start_offset_label": "03:08:30",
      "end": "1970-01-01T03:09:00",
      "end_offset_sec": 11340,
      "end_offset_label": "03:09:00",
      "score": 3.142,
      "peak_bucket": "1970-01-01T03:08:30",
      "peak_offset_sec": 11310,
      "peak_offset_label": "03:08:30",
      "peak_total_messages": 47,
      "representative_keyword": "ㅋㅋ"
    }
  ],
  "parse_errors": [],
  "message": "ok"
}
```

#### 타임스탬프 규칙

- `playerMessageTime` 기반 로그: `bucket_start` 가 `1970-01-01T...` 형태 (epoch-relative UTC)
- `offset_sec` / `offset_label` 이 VOD 플레이어의 실제 재생 위치와 직접 대응
- VOD 링크 생성: `https://chzzk.naver.com/video/{vod_id}?t={start_offset_sec}`

---

## 캐시 동작

- 동일 `vod_id` 재요청 → `backend/data/chatlogs/chatLog-{vod_id}.log` 재사용
- 캐시 최대 5개 유지 (LRU), 초과 시 가장 오래된 파일 삭제
- 강제 재수집: 해당 `.log` 파일 삭제 후 재요청
