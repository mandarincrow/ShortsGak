from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceConfig(BaseModel):
    vod_id: str = Field(..., min_length=1, description="Chzzk VOD ID")


class KeywordOptions(BaseModel):
    mode: Literal["contains", "exact"] = "contains"
    case_sensitive: bool = False


class AnalyzeOptions(BaseModel):
    bucket_size_seconds: int = Field(default=30, ge=5, le=300)
    keyword_options: KeywordOptions = Field(default_factory=KeywordOptions)
    normalize_repeated_reactions: bool = True
    normalize_repeated_laugh: bool | None = Field(
        default=None,
        description="deprecated alias of normalize_repeated_reactions",
    )
    min_highlight_score: float = 1.2
    max_highlights: int = Field(default=20, ge=1, le=200)

    @model_validator(mode="before")
    @classmethod
    def apply_legacy_alias(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        if "normalize_repeated_reactions" not in data and "normalize_repeated_laugh" in data:
            data["normalize_repeated_reactions"] = data["normalize_repeated_laugh"]
        return data


class AnalyzeRequest(BaseModel):
    source: SourceConfig
    keywords: list[str] = Field(default_factory=list)
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


class ExportRequest(BaseModel):
    analysis: AnalyzeRequest
    format: Literal["json", "csv"] = "json"
    dataset: Literal["summary", "highlights", "volume", "keywords", "parse_errors", "all"] = "all"


class ParseErrorItem(BaseModel):
    file_path: str
    line_number: int
    reason: str
    raw_line: str


class ChatMessage(BaseModel):
    timestamp: datetime
    nickname: str
    content: str
    user_id_hash: str


class TimeBucketPoint(BaseModel):
    bucket_start: datetime
    bucket_start_offset_sec: int
    bucket_start_offset_label: str
    total_messages: int
    unique_users: int


class KeywordSeriesPoint(BaseModel):
    bucket_start: datetime
    bucket_start_offset_sec: int
    bucket_start_offset_label: str
    keyword: str
    count: int


class HighlightRange(BaseModel):
    start: datetime
    start_offset_sec: int
    start_offset_label: str
    end: datetime
    end_offset_sec: int
    end_offset_label: str
    score: float
    peak_bucket: datetime
    peak_offset_sec: int
    peak_offset_label: str
    peak_total_messages: int
    representative_keyword: str | None = None


class SummaryStats(BaseModel):
    total_messages: int
    unique_users: int
    start_time: datetime | None
    end_time: datetime | None
    vod_duration_sec: int
    vod_duration_label: str
    avg_messages_per_minute: float


class AnalyzeResponse(BaseModel):
    summary: SummaryStats
    volume_series: list[TimeBucketPoint]
    keyword_series: list[KeywordSeriesPoint]
    highlights: list[HighlightRange]
    parse_errors: list[ParseErrorItem]
    message: str = "ok"
