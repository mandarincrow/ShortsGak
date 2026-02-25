from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt
import re

from .schemas import (
    AnalyzeOptions,
    ChatMessage,
    HighlightRange,
    KeywordSeriesPoint,
    SummaryStats,
    TimeBucketPoint,
)


def _bucket_start(ts: datetime, bucket_size_seconds: int) -> datetime:
    bucket_epoch = int(ts.timestamp()) // bucket_size_seconds * bucket_size_seconds
    return datetime.fromtimestamp(bucket_epoch)


def _format_offset(seconds: int) -> str:
    safe_seconds = max(seconds, 0)
    hours = safe_seconds // 3600
    minutes = (safe_seconds % 3600) // 60
    remain_seconds = safe_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remain_seconds:02d}"


def _count_keyword(content: str, keyword: str, mode: str) -> int:
    if not keyword:
        return 0
    if mode == "exact":
        return int(content == keyword)
    return content.count(keyword)


def _normalize_repeated_reactions(text: str) -> str:
    normalized = re.sub(r"ㅋ{2,}", "ㅋㅋ", text)
    normalized = re.sub(r"ㅎ{2,}", "ㅎㅎ", normalized)
    normalized = re.sub(r"ㅠ{2,}", "ㅠㅠ", normalized)
    normalized = re.sub(r"ㅜ{2,}", "ㅜㅜ", normalized)
    normalized = re.sub(r"허+어+억+", "헉", normalized)
    normalized = re.sub(r"허+억+", "헉", normalized)
    return normalized


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def build_analysis(
    messages: list[ChatMessage], keywords: list[str], options: AnalyzeOptions
) -> tuple[SummaryStats, list[TimeBucketPoint], list[KeywordSeriesPoint], list[HighlightRange]]:
    if not messages:
        return (
            SummaryStats(
                total_messages=0,
                unique_users=0,
                start_time=None,
                end_time=None,
                vod_duration_sec=0,
                vod_duration_label="00:00:00",
                avg_messages_per_minute=0.0,
            ),
            [],
            [],
            [],
        )

    normalized_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not options.keyword_options.case_sensitive:
        normalized_keywords = [keyword.lower() for keyword in normalized_keywords]
    if options.normalize_repeated_reactions:
        normalized_keywords = [_normalize_repeated_reactions(keyword) for keyword in normalized_keywords]
    normalized_keywords = _dedupe_preserve_order(normalized_keywords)

    by_bucket_total: dict[datetime, int] = defaultdict(int)
    by_bucket_users: dict[datetime, set[str]] = defaultdict(set)
    by_bucket_keyword: dict[tuple[datetime, str], int] = defaultdict(int)

    for message in messages:
        bucket = _bucket_start(message.timestamp, options.bucket_size_seconds)
        by_bucket_total[bucket] += 1
        by_bucket_users[bucket].add(message.user_id_hash)

        content = message.content
        if not options.keyword_options.case_sensitive:
            content = content.lower()
        if options.normalize_repeated_reactions:
            content = _normalize_repeated_reactions(content)

        for keyword in normalized_keywords:
            count = _count_keyword(content, keyword, options.keyword_options.mode)
            if count > 0:
                by_bucket_keyword[(bucket, keyword)] += count

    buckets = sorted(by_bucket_total.keys())
    base_time = messages[0].timestamp
    volume_series = [
        TimeBucketPoint(
            bucket_start=bucket,
            bucket_start_offset_sec=max(int((bucket - base_time).total_seconds()), 0),
            bucket_start_offset_label=_format_offset(max(int((bucket - base_time).total_seconds()), 0)),
            total_messages=by_bucket_total[bucket],
            unique_users=len(by_bucket_users[bucket]),
        )
        for bucket in buckets
    ]

    keyword_series: list[KeywordSeriesPoint] = []
    for bucket in buckets:
        for keyword in normalized_keywords:
            keyword_series.append(
                KeywordSeriesPoint(
                    bucket_start=bucket,
                    bucket_start_offset_sec=max(int((bucket - base_time).total_seconds()), 0),
                    bucket_start_offset_label=_format_offset(max(int((bucket - base_time).total_seconds()), 0)),
                    keyword=keyword,
                    count=by_bucket_keyword.get((bucket, keyword), 0),
                )
            )

    total_messages = len(messages)
    unique_users = len({message.user_id_hash for message in messages})
    start_time = messages[0].timestamp
    end_time = messages[-1].timestamp
    duration_minutes = max((end_time - start_time).total_seconds() / 60.0, 1 / 60)

    summary = SummaryStats(
        total_messages=total_messages,
        unique_users=unique_users,
        start_time=start_time,
        end_time=end_time,
        vod_duration_sec=max(int((end_time - start_time).total_seconds()), 0),
        vod_duration_label=_format_offset(max(int((end_time - start_time).total_seconds()), 0)),
        avg_messages_per_minute=round(total_messages / duration_minutes, 2),
    )

    highlights = _detect_highlights(
        buckets=buckets,
        base_time=base_time,
        by_bucket_total=by_bucket_total,
        by_bucket_keyword=by_bucket_keyword,
        normalized_keywords=normalized_keywords,
        options=options,
    )

    return summary, volume_series, keyword_series, highlights


def _zscore(values: list[int]) -> list[float]:
    if not values:
        return []
    float_values = [float(value) for value in values]
    mean = sum(float_values) / len(float_values)
    variance = sum((value - mean) ** 2 for value in float_values) / len(float_values)
    std = sqrt(variance)
    if std == 0:
        return [0.0 for _ in values]
    return [(value - mean) / std for value in float_values]


def _detect_highlights(
    buckets: list[datetime],
    base_time: datetime,
    by_bucket_total: dict[datetime, int],
    by_bucket_keyword: dict[tuple[datetime, str], int],
    normalized_keywords: list[str],
    options: AnalyzeOptions,
) -> list[HighlightRange]:
    if not buckets:
        return []

    volume_values = [by_bucket_total[bucket] for bucket in buckets]
    volume_z = _zscore(volume_values)

    keyword_peak_per_bucket: list[int] = []
    representative_keyword_per_bucket: list[str | None] = []

    for bucket in buckets:
        if not normalized_keywords:
            keyword_peak_per_bucket.append(0)
            representative_keyword_per_bucket.append(None)
            continue

        counts = {keyword: by_bucket_keyword.get((bucket, keyword), 0) for keyword in normalized_keywords}
        best_keyword, best_count = max(counts.items(), key=lambda item: item[1])
        keyword_peak_per_bucket.append(best_count)
        representative_keyword_per_bucket.append(best_keyword if best_count > 0 else None)

    keyword_z = _zscore(keyword_peak_per_bucket)
    scores = [0.6 * volume_z[idx] + 0.4 * keyword_z[idx] for idx in range(len(buckets))]

    candidate_indices = [
        idx for idx, score in enumerate(scores) if score >= options.min_highlight_score
    ]

    max_merge_buckets = options.max_merge_buckets
    merged_ranges: list[list[int]] = []
    for idx in candidate_indices:
        if (
            not merged_ranges
            or idx > merged_ranges[-1][-1] + 1
            or (merged_ranges[-1][1] - merged_ranges[-1][0] + 1) >= max_merge_buckets
        ):
            merged_ranges.append([idx, idx])
        else:
            merged_ranges[-1][1] = idx

    highlights: list[HighlightRange] = []
    bucket_delta = timedelta(seconds=options.bucket_size_seconds)

    for start_idx, end_idx in merged_ranges:
        peak_idx = max(range(start_idx, end_idx + 1), key=lambda idx: scores[idx])
        start_bucket = buckets[start_idx]
        end_bucket = buckets[end_idx] + bucket_delta
        peak_bucket = buckets[peak_idx]

        start_offset_sec = max(int((start_bucket - base_time).total_seconds()), 0)
        end_offset_sec = max(int((end_bucket - base_time).total_seconds()), 0)
        peak_offset_sec = max(int((peak_bucket - base_time).total_seconds()), 0)

        highlights.append(
            HighlightRange(
                start=start_bucket,
                start_offset_sec=start_offset_sec,
                start_offset_label=_format_offset(start_offset_sec),
                end=end_bucket,
                end_offset_sec=end_offset_sec,
                end_offset_label=_format_offset(end_offset_sec),
                score=round(scores[peak_idx], 3),
                peak_bucket=peak_bucket,
                peak_offset_sec=peak_offset_sec,
                peak_offset_label=_format_offset(peak_offset_sec),
                peak_total_messages=by_bucket_total[peak_bucket],
                representative_keyword=representative_keyword_per_bucket[peak_idx],
            )
        )

    highlights.sort(key=lambda item: item.score, reverse=True)
    return highlights[: options.max_highlights]
