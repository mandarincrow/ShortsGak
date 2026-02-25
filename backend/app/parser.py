import re
import os
import json
import shutil
import platform
from datetime import datetime
from pathlib import Path

from .chatlog_cache import get_chatlog_cache_path, mark_recent, prune_cache
from .chatlog_fetcher import fetch_chatlog_to_file
from .logging_config import get_logger
from .schemas import ChatMessage, ParseErrorItem, SourceConfig


LOG_LINE_PATTERN = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s(?P<nickname>.*?):\s(?P<content>.*)\s\((?P<user_id_hash>[^()]*)\)$"
)
logger = get_logger(__name__)


def _build_file_lookup_diagnostics(vod_id: str, candidates: list[Path]) -> dict:
    cwd = Path.cwd()
    parent = (cwd / "..").resolve()

    candidate_details = []
    for candidate in candidates:
        candidate_details.append(
            {
                "raw": str(candidate),
                "absolute": str(candidate.resolve()),
                "exists": candidate.exists(),
            }
        )

    cwd_matches = sorted([path.name for path in cwd.glob("chatLog-*.log")])[:50]
    parent_matches = sorted([path.name for path in parent.glob("chatLog-*.log")])[:50]

    return {
        "vod_id": vod_id,
        "cwd": str(cwd),
        "cwd_absolute": str(cwd.resolve()),
        "parent_absolute": str(parent),
        "cwd_entries_count": len(list(cwd.iterdir())),
        "cwd_chatlog_files": cwd_matches,
        "parent_chatlog_files": parent_matches,
        "candidates": candidate_details,
        "process_uid": os.getuid() if hasattr(os, "getuid") else None,
        "process_pid": os.getpid(),
        "platform": platform.platform(),
    }


def resolve_source_files(source: SourceConfig) -> list[Path]:
    cache_path = get_chatlog_cache_path(source.vod_id)
    if cache_path.exists():
        mark_recent(cache_path)
        prune_cache()
        logger.info("Using cached chat log for vod_id=%s -> %s", source.vod_id, cache_path)
        return [cache_path]

    filename = f"chatLog-{source.vod_id}.log"
    legacy_candidates = [
        Path(filename),
        Path("..") / filename,
    ]

    for candidate in legacy_candidates:
        if candidate.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, cache_path)
            mark_recent(cache_path)
            prune_cache()
            logger.info(
                "Migrated legacy chat log to cache for vod_id=%s: %s -> %s",
                source.vod_id,
                candidate,
                cache_path,
            )
            return [cache_path]

    diagnostics = _build_file_lookup_diagnostics(source.vod_id, legacy_candidates)
    logger.warning(
        "No local chat log file found for vod_id=%s. diagnostics=%s",
        source.vod_id,
        json.dumps(diagnostics, ensure_ascii=False),
    )

    try:
        written_count, page_count = fetch_chatlog_to_file(source.vod_id, cache_path)
        mark_recent(cache_path)
        prune_cache()
        logger.info(
            "Auto-fetched chat log for vod_id=%s: messages=%s pages=%s path=%s",
            source.vod_id,
            written_count,
            page_count,
            cache_path,
        )
        return [cache_path]
    except Exception as exc:
        logger.exception("Failed to auto-fetch chat log for vod_id=%s", source.vod_id)
        raise RuntimeError(f"auto_fetch_failed: {exc}") from exc


def parse_chat_logs(source: SourceConfig) -> tuple[list[ChatMessage], list[ParseErrorItem]]:
    messages: list[ChatMessage] = []
    parse_errors: list[ParseErrorItem] = []

    try:
        resolved_paths = resolve_source_files(source)
    except Exception as exc:
        parse_errors.append(
            ParseErrorItem(
                file_path=f"chatLog-{source.vod_id}.log",
                line_number=0,
                reason="auto_fetch_failed",
                raw_line=str(exc),
            )
        )
        logger.error("Cannot resolve chat log for vod_id=%s: %s", source.vod_id, exc)
        return messages, parse_errors

    for path in resolved_paths:
        if not path.exists():
            logger.error(
                "Chat log file not found: raw=%s absolute=%s",
                path,
                path.resolve(),
            )
            parse_errors.append(
                ParseErrorItem(
                    file_path=str(path),
                    line_number=0,
                    reason="file_not_found",
                    raw_line="",
                )
            )
            continue

        logger.info("Start parsing chat log: %s", path)
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                match = LOG_LINE_PATTERN.match(line)
                if not match:
                    parse_errors.append(
                        ParseErrorItem(
                            file_path=str(path),
                            line_number=line_number,
                            reason="invalid_format",
                            raw_line=line,
                        )
                    )
                    continue

                groups = match.groupdict()
                try:
                    timestamp = datetime.strptime(groups["timestamp"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    parse_errors.append(
                        ParseErrorItem(
                            file_path=str(path),
                            line_number=line_number,
                            reason="invalid_timestamp",
                            raw_line=line,
                        )
                    )
                    continue

                messages.append(
                    ChatMessage(
                        timestamp=timestamp,
                        nickname=groups["nickname"].strip() or "Unknown",
                        content=groups["content"],
                        user_id_hash=groups["user_id_hash"],
                    )
                )

    messages.sort(key=lambda item: item.timestamp)
    logger.info(
        "Finished parsing: vod_id=%s, messages=%s, parse_errors=%s",
        source.vod_id,
        len(messages),
        len(parse_errors),
    )
    return messages, parse_errors
