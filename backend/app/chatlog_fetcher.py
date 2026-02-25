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
PAGE_REQUEST_DELAY_SECONDS = 0.2


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
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
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
                # playerMessageTime: VOD 재생 위치 (ms). messageTime 은 벽시계 시각이므로
                # playerMessageTime 을 기준으로 저장해야 VOD 링크 offset 이 정확합니다.
                if player_message_time is None:
                    # fallback: messageTime 벽시계 KST 사용 (레거시)
                    message_time = chat.get("messageTime")
                    if message_time is None:
                        continue
                    vod_time = datetime.fromtimestamp(message_time / 1000.0, KST).replace(tzinfo=None)
                else:
                    # epoch-relative UTC datetime (year=1970) = VOD 재생 오프셋
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

            time.sleep(PAGE_REQUEST_DELAY_SECONDS)

    logger.info(
        "Finished fetching chat log: vod_id=%s pages=%s messages=%s path=%s",
        vod_id,
        page_count,
        written_count,
        destination,
    )
    return written_count, page_count
