from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


# ---------------------------------------------------------------------------
# PyInstaller frozen 환경 vs 개발 환경 경로 감지
# frozen 시 sys._MEIPASS가 임시 추출 디렉터리가 됩니다
# ---------------------------------------------------------------------------
def _base_dir() -> Path:
    """실행 파일 기준 루트 디렉터리 반환 (frozen/dev 공용)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


BASE_DIR = _base_dir()
BACKEND_DIR = BASE_DIR / "backend"  # dev: backend/  frozen: _MEIPASS/ 하위에 패키지가 위치

SERVER_HOST = "127.0.0.1"
SERVER_START_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Frozen 환경에서는 backend 패키지를 sys.path에 추가해 import 가능하게 합니다
# ---------------------------------------------------------------------------
def _setup_sys_path() -> None:
    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((SERVER_HOST, 0))
        return int(sock.getsockname()[1])


def wait_until_server_ready(base_url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    health_url = f"{base_url}/health"
    while time.time() < deadline:
        try:
            with urlopen(health_url, timeout=1.5) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(0.25)
    raise TimeoutError(
        f"Server did not become ready within {timeout_seconds}s: {health_url}"
    )


def start_server_thread(port: int) -> threading.Thread:
    """uvicorn을 동일 프로세스의 백그라운드 스레드로 실행합니다.

    subprocess 방식과 달리 PyInstaller로 단일 exe 빌드 시에도 동작합니다.
    """
    import uvicorn  # noqa: PLC0415 – 경로 설정 후 import

    config = uvicorn.Config(
        "app.main:app",
        host=SERVER_HOST,
        port=port,
        log_level="error",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True, name="uvicorn-server")
    thread.start()
    return thread


def main() -> None:
    _setup_sys_path()

    import webview  # noqa: PLC0415 – 플랫폼 구분 시 지연 import 허용

    # ---------------------------------------------------------------------------
    # 번들된 WebView2 Fixed Version 런타임 적용
    # 배포 exe에는 vendor/webview2/ 가 _MEIPASS/webview2/ 로 포함됩니다
    # 없으면 시스템 설치 WebView2 로 fallback (개발 환경 포함)
    # ---------------------------------------------------------------------------
    if hasattr(sys, "_MEIPASS"):
        _bundled_wv2 = Path(sys._MEIPASS) / "webview2"
        if _bundled_wv2.exists():
            webview.settings["WEBVIEW2_RUNTIME_PATH"] = str(_bundled_wv2)

    port = find_free_port()
    base_url = f"http://{SERVER_HOST}:{port}"

    start_server_thread(port)
    wait_until_server_ready(base_url, SERVER_START_TIMEOUT_SECONDS)

    webview.create_window(
        title="ShortsGak Analyzer",
        url=base_url,
        min_size=(1100, 760),
    )
    # webview.start()는 blocking – 창이 닫히면 반환됩니다
    # daemon 스레드인 uvicorn은 프로세스 종료 시 자동으로 정리됩니다
    webview.start()


if __name__ == "__main__":
    import os
    import traceback

    try:
        main()
    except Exception:
        # console=False 빌드에서는 예외가 화면에 안 뜨므로 파일에 기록
        if hasattr(sys, "_MEIPASS"):
            crash_log_dir = Path(sys.executable).parent / "logs"
        else:
            crash_log_dir = BASE_DIR / "backend" / "logs"

        try:
            crash_log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            crash_log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ShortsGak" / "logs"
            crash_log_dir.mkdir(parents=True, exist_ok=True)

        crash_log = crash_log_dir / "crash.log"
        with open(crash_log, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise


if __name__ == "__main__":
    main()
