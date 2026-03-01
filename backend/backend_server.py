"""backend_server.py

Electron(또는 테스트 스크립트)이 --port 인자로 직접 실행하는 최소 FastAPI 서버 진입점.

실행 예시:
    # frozen (backend.exe로 패키징된 경우)
    backend.exe --port 18765

    # 개발 환경
    python backend/backend_server.py --port 18765
    python backend/backend_server.py           # 랜덤 포트 사용 (stdout에 포트 번호 출력)

참고:
    - 호스트는 항상 127.0.0.1로 고정된다 (외부 네트워크 노출 방지).
    - 서버 시작 직전에 "LISTENING_PORT=<N>" 을 stdout에 출력한다.
      Electron은 이 값을 파싱해 loadURL 포트를 확인할 수 있다.
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

_HOST = "127.0.0.1"


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
    """OS가 할당하는 빈 포트를 반환한다.

    소켓을 닫은 뒤 uvicorn이 바인딩하기 전까지 짧은 race window가 존재한다.
    로컬 전용 앱에서는 실질적 문제가 없으나, Electron은 항상 --port를 직접
    지정하여 이 함수를 거치지 않도록 설계한다 (개발 편의 fallback 용도).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((_HOST, 0))
        return int(s.getsockname()[1])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ShortsGak backend server")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Listening port (default: random free port)",
    )
    return parser.parse_args()


def main() -> None:
    _setup_sys_path()

    args = _parse_args()
    port = args.port if args.port is not None else _find_free_port()

    # Electron 및 개발자가 실제 포트를 인지할 수 있도록 stdout에 출력한다.
    # uvicorn 로그가 억제(log_config=None)되어 있어도 이 줄은 항상 출력된다.
    print(f"LISTENING_PORT={port}", flush=True)

    # uvicorn import는 sys.path 설정 이후에 해야 한다
    import uvicorn  # noqa: PLC0415

    try:
        uvicorn.run(
            "app.main:app",
            host=_HOST,
            port=port,
            log_level="error",
            # sys.stderr=None 환경(PyInstaller console=False)에서 isatty() crash 방지.
            # 이 서버는 console=True로 빌드되므로 방어적 설정으로 유지한다.
            log_config=None,
        )
    except OSError as exc:
        # 포트 충돌 등 바인딩 실패 — Electron이 stderr를 파싱할 수 있도록 명시적 출력
        print(f"ERROR: Failed to bind {_HOST}:{port} — {exc}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
