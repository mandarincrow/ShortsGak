"""backend_server.py

Electron(또는 테스트 스크립트)이 --port 인자로 직접 실행하는 최소 FastAPI 서버 진입점.

실행 예시:
    # frozen (backend.exe로 패키징된 경우)
    backend.exe --port 18765

    # 개발 환경
    python backend/backend_server.py --port 18765
    python backend/backend_server.py           # 랜덤 포트 사용
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# sys.path 설정 — frozen / 개발 환경 공용
# ---------------------------------------------------------------------------
def _setup_sys_path() -> None:
    """app 패키지를 import할 수 있도록 sys.path를 설정한다.

    frozen (PyInstaller) 환경에서는 _MEIPASS 하위에 backend/app 이 위치하므로
    _MEIPASS/backend 를 경로에 추가한다.
    개발 환경에서는 이 파일(backend/backend_server.py)의 부모 디렉터리(backend/)를 추가한다.
    """
    if hasattr(sys, "_MEIPASS"):
        # frozen: sys._MEIPASS/backend/app/...
        backend_path = str(Path(sys._MEIPASS) / "backend")  # type: ignore[attr-defined]
    else:
        # dev: backend/backend_server.py → 부모 = backend/
        backend_path = str(Path(__file__).resolve().parent)

    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _find_free_port() -> int:
    """OS가 할당하는 빈 포트를 반환한다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ShortsGak backend server")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Listening port (default: random free port)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Listening host (default: 127.0.0.1)",
    )
    return parser.parse_args()


def main() -> None:
    _setup_sys_path()

    args = _parse_args()
    port = args.port if args.port is not None else _find_free_port()
    host = args.host

    # uvicorn import는 sys.path 설정 이후에 해야 한다
    import uvicorn  # noqa: PLC0415

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="error",
        # console=False 빌드에서 sys.stderr=None → isatty() crash 방지
        log_config=None,
    )


if __name__ == "__main__":
    main()
