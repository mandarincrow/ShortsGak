from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .logging_config import get_logger


logger = get_logger(__name__)
KST = timezone(timedelta(hours=9))
REQUEST_TIMEOUT_SECONDS = 10
# 레이트 리밋(429) 발생 시에만 back-off. 정상 응답 시 최소 딜레이만 적용.
_MIN_PAGE_DELAY = 0.05        # 초, 정상 응답 시 최소 대기 (기존 0.2s의 1/4)
_RATE_LIMIT_BASE_DELAY = 1.0   # 초, 429 첫 번째 재시도
_RATE_LIMIT_MAX_RETRIES = 5    # 최대 재시도 횟수


def _get_page(session: requests.Session, url: str, headers: dict) -> requests.Response:
    """단일 페이지 요청. 429/타임아웃 시 exponential back-off 후 재시도."""
    for attempt in range(_RATE_LIMIT_MAX_RETRIES + 1):
        try:
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.exceptions.Timeout:
            if attempt >= _RATE_LIMIT_MAX_RETRIES:
                raise
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "Request timeout: url=%s attempt=%s/%s, retrying in %.1fs",
                url, attempt + 1, _RATE_LIMIT_MAX_RETRIES, delay,
            )
            time.sleep(delay)
            continue
        if response.status_code == 429:
            delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "Rate limited (429): url=%s attempt=%s/%s, retrying in %.1fs",
                url, attempt + 1, _RATE_LIMIT_MAX_RETRIES, delay,
            )
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response
    raise requests.exceptions.RetryError(f"Max retries exceeded: {url}")


def fetch_chatlog_to_file(vod_id: str, destination: Path) -> tuple[int, int]:
    next_player_message_time = "0"
    page_count = 0
    written_count = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Start fetching chat log: vod_id=%s -> %s", vod_id, destination)

    with requests.Session() as session, destination.open("w", encoding="utf-8") as file:
        while True:
            url = (
                f"https://api.chzzk.naver.com/service/v1/videos/{vod_id}/chats"
                f"?playerMessageTime={next_player_message_time}"
            )
            response = _get_page(session, url, headers)
            data = response.json()
            page_count += 1

            if data.get("code") != 200:
                logger.warning("Unexpected chzzk response code: vod_id=%s code=%s", vod_id, data.get("code"))
                break

            content = data.get("content", {})
            video_chats = content.get("videoChats") or []
            if not video_chats:
                logger.info("No more chats from API: vod_id=%s page=%s", vod_id, page_count)
                break

            log_messages: list[str] = []
            for chat in video_chats:
                player_message_time = chat.get("playerMessageTime")
                user_id_hash = chat.get("userIdHash", "")
                message = chat.get("content", "")
                if player_message_time is None:
                    message_time = chat.get("messageTime")
                    if message_time is None:
                        continue
                    vod_time = datetime.fromtimestamp(message_time / 1000.0, KST).replace(tzinfo=None)
                else:
                    vod_time = datetime.utcfromtimestamp(player_message_time / 1000.0)
                formatted_time = vod_time.strftime("%Y-%m-%d %H:%M:%S")

                nickname = "Unknown"
                profile_raw = chat.get("profile")
                if profile_raw and profile_raw != "null":
                    try:
                        profile = json.loads(profile_raw)
                        nickname = profile.get("nickname", "Unknown")
                    except json.JSONDecodeError:
                        nickname = "Unknown"

                log_messages.append(f"[{formatted_time}] {nickname}: {message} ({user_id_hash})\n")

            file.writelines(log_messages)
            written_count += len(log_messages)

            next_player_message_time = content.get("nextPlayerMessageTime")
            if next_player_message_time is None:
                logger.info("Reached last chat page: vod_id=%s page=%s", vod_id, page_count)
                break
            # 정상 응답 시 최소 딜레이 — 기존 0.2s 대비 1/4, 429 시 _get_page 내부에서 back-off
            time.sleep(_MIN_PAGE_DELAY)

    logger.info(
        "Finished fetching chat log: vod_id=%s pages=%s messages=%s path=%s",
        vod_id,
        page_count,
        written_count,
        destination,
    )
    return written_count, page_count
