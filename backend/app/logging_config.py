from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _get_log_dir() -> Path:
    """로그 디렉터리 반환.

    우선순위:
    1. frozen(exe) 환경 → exe 옆 `logs/` 폴더 (쓰기 가능한 배포 위치)
    2. 개발 환경 → 프로젝트 루트 `backend/logs/`
    3. 1번에 쓰기 권한이 없으면 → %LOCALAPPDATA%/ShortsGak/logs/
    """
    if hasattr(sys, "_MEIPASS"):
        # onedir: ShortsGak.exe 와 같은 폴더의 logs/
        exe_dir = Path(sys.executable).parent
        candidate = exe_dir / "logs"
    else:
        candidate = Path(__file__).resolve().parents[2] / "backend" / "logs"

    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # 실제 쓰기 가능 여부 확인
        test_file = candidate / ".write_test"
        test_file.touch()
        test_file.unlink()
        return candidate
    except OSError:
        # 쓰기 권한 없을 때 → %LOCALAPPDATA% 폴백
        fallback = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ShortsGak" / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_chatlog_logging_configured", False):
        return

    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    root_logger._chatlog_logging_configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
