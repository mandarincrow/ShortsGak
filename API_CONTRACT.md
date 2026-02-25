# Analyze API Contract (T01)

## Endpoint
- `POST /api/analyze`
- `POST /api/export`

## Request
```json
{
  # API Contract

  ## Base
  - Health: `GET /health`
  - Analyze: `POST /api/analyze`
  - Export: `POST /api/export`

  ## 1) Analyze

  ### Request
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
      "max_highlights": 20
    }
  }
  ```

  ### Response (shape)
  ```json
  {
    "summary": {
      "total_messages": 1200,
      "unique_users": 340,
      "start_time": "2026-02-25T20:00:00",
      "end_time": "2026-02-25T22:10:00",
      "vod_duration_sec": 7800,
      "vod_duration_label": "02:10:00",
      "avg_messages_per_minute": 9.23
    },
    "volume_series": [
      {
        "bucket_start": "2026-02-25T20:00:00",
        "bucket_start_offset_sec": 0,
        "bucket_start_offset_label": "00:00:00",
        "total_messages": 13,
        "unique_users": 11
      }
    ],
    "keyword_series": [
      {
        "bucket_start": "2026-02-25T20:00:00",
        "bucket_start_offset_sec": 0,
        "bucket_start_offset_label": "00:00:00",
        "keyword": "헉",
        "count": 4
      }
    ],
    "highlights": [
      {
        "start": "2026-02-25T20:41:00",
        "start_offset_sec": 2460,
        "start_offset_label": "00:41:00",
        "end": "2026-02-25T20:42:00",
        "end_offset_sec": 2520,
        "end_offset_label": "00:42:00",
        "score": 2.81,
        "peak_bucket": "2026-02-25T20:41:30",
        "peak_offset_sec": 2490,
        "peak_offset_label": "00:41:30",
        "peak_total_messages": 28,
        "representative_keyword": "헉"
      }
    ],
    "parse_errors": [],
    "message": "ok"
  }
  ```

  ### Validation
  - `source.vod_id`: required
  - `options.bucket_size_seconds`: `5..300`
  - `options.max_highlights`: `1..200`
  - `options.keyword_options.mode`: `contains | exact`
  - `options.normalize_repeated_reactions`: default `true`
  - `options.normalize_repeated_laugh`: deprecated alias (auto-mapped)

  ### Keyword normalization note
  `normalize_repeated_reactions=true`일 때:
  - `ㅋ/ㅎ/ㅠ/ㅜ` 반복이 축약된다.
  - `허어어억`, `허어어어어어억` 등은 `헉`으로 정규화되어 같은 키워드로 집계된다.

  ## 2) Export

  ### Request
  ```json
  {
    "analysis": {
      "source": { "vod_id": "11933431" },
      "keywords": ["헉", "ㅋㅋㅋㅋ"],
      "options": {
        "bucket_size_seconds": 30,
        "keyword_options": {
          "mode": "contains",
          "case_sensitive": false
        },
        "normalize_repeated_reactions": true,
        "min_highlight_score": 1.2,
        "max_highlights": 20
      }
    },
    "format": "json",
    "dataset": "all"
  }
  ```

  ### Params
  - `format`: `json | csv`
  - `dataset`: `summary | highlights | volume | keywords | parse_errors | all`

  ### Behavior
  - `format=json`: 지정 dataset JSON 반환
  - `format=csv`: 지정 dataset CSV 반환
  - `format=csv` + `dataset=all`: `400` 반환

  ## 3) Error semantics
  - `400`: 잘못된 입력/지원하지 않는 dataset
  - `500`: 파싱/분석 중 내부 오류
  - 분석 실패 시 `parse_errors` 또는 HTTP 오류 detail을 확인
