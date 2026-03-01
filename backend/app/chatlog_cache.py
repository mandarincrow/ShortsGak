from __future__ import annotations

import os
import sys
from pathlib import Path

from .logging_config import get_logger


logger = get_logger(__name__)
CACHE_MAX_FILES = 5


def get_chatlog_cache_dir() -> Path:
    """캐시 디렉터리 반환.

    우선순위:
    1. frozen(exe) 환경 → exe 옆 `data/chatlogs/`
    2. 개발 환경 → 프로젝트 루트 `backend/data/chatlogs/`
    3. 1번에 쓰기 권한이 없으면 → %LOCALAPPDATA%/ShortsGak/chatlogs/
    """
    if hasattr(sys, "_MEIPASS"):
        exe_dir = Path(sys.executable).parent
        candidate = exe_dir / "data" / "chatlogs"
    else:
        candidate = Path(__file__).resolve().parents[1] / "data" / "chatlogs"

    try:
        candidate.mkdir(parents=True, exist_ok=True)
        test_file = candidate / ".write_test"
        test_file.touch()
        test_file.unlink()
        return candidate
    except OSError:
        fallback = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ShortsGak" / "chatlogs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_chatlog_cache_path(vod_id: str) -> Path:
    return get_chatlog_cache_dir() / f"chatLog-{vod_id}.log"


def mark_recent(path: Path) -> None:
    if not path.exists():
        return
    os.utime(path, None)


def prune_cache(max_files: int = CACHE_MAX_FILES) -> None:
    cache_dir = get_chatlog_cache_dir()
    files = [path for path in cache_dir.glob("chatLog-*.log") if path.is_file()]
    before_count = len(files)
    if len(files) <= max_files:
        logger.info(
            "Cache prune skipped: before_count=%s max_files=%s",
            before_count,
            max_files,
        )
        return

    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    to_delete = files[max_files:]
    deleted_names: list[str] = []
    for path in to_delete:
        try:
            path.unlink(missing_ok=True)
            deleted_names.append(path.name)
        except Exception:
            logger.exception("Failed to prune cached chat log: %s", path)

    remaining_count = len([path for path in cache_dir.glob("chatLog-*.log") if path.is_file()])
    logger.info(
        "Cache prune completed: before_count=%s after_count=%s pruned_count=%s max_files=%s deleted=%s",
        before_count,
        remaining_count,
        len(deleted_names),
        max_files,
        deleted_names,
    )
