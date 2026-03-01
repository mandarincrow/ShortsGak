"""tests/test_backend_server.py

backend_server.py 의 동작을 검증하는 테스트.
T02 (backend.spec) 에서 번들할 진입점이 올바르게 동작함을 보장한다.

TDD 절차:
1. [Red]   이 파일 작성 → 구현 없을 때 실패 확인
2. [Green] backend_server.py / backend.spec 구현 → 전체 통과 확인
3. [Refactor] 필요 시 정리
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SERVER = ROOT / "backend" / "backend_server.py"
PYTHON = sys.executable

# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_http(url: str, timeout: float = 10.0, interval: float = 0.2) -> bool:
    """url 이 200 을 반환할 때까지 폴링, 타임아웃이면 False."""
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(interval)
    return False


# ---------------------------------------------------------------------------
# Unit tests — _find_free_port, _parse_args
# ---------------------------------------------------------------------------

class TestFindFreePort:
    def test_returns_integer(self):
        import backend_server
        port = backend_server._find_free_port()
        assert isinstance(port, int)

    def test_port_in_valid_range(self):
        import backend_server
        port = backend_server._find_free_port()
        assert 1024 <= port <= 65535

    def test_port_is_free(self):
        """반환된 포트에 즉시 바인딩 가능해야 한다."""
        import backend_server
        port = backend_server._find_free_port()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))  # OSError 없으면 성공


class TestParseArgs:
    def test_port_flag(self, monkeypatch):
        import backend_server
        monkeypatch.setattr(sys, "argv", ["backend_server.py", "--port", "12345"])
        args = backend_server._parse_args()
        assert args.port == 12345

    def test_port_default_is_none(self, monkeypatch):
        import backend_server
        monkeypatch.setattr(sys, "argv", ["backend_server.py"])
        args = backend_server._parse_args()
        assert args.port is None

    def test_no_host_arg(self, monkeypatch):
        """--host 플래그는 존재하지 않아야 한다 (보안 원칙)."""
        import backend_server
        monkeypatch.setattr(sys, "argv", ["backend_server.py", "--host", "0.0.0.0"])
        with pytest.raises(SystemExit):
            backend_server._parse_args()


# ---------------------------------------------------------------------------
# Integration tests — 실제 서버 subprocess
# ---------------------------------------------------------------------------

class TestBackendServerProcess:
    """backend_server.py 를 subprocess 로 실행해 동작을 검증한다."""

    @pytest.fixture()
    def server(self):
        """지정 포트로 서버를 시작하고, 테스트 종료 시 종료한다."""
        port = _free_port()
        proc = subprocess.Popen(
            [PYTHON, str(BACKEND_SERVER), "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(ROOT),
        )
        yield proc, port
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    def test_emits_listening_port_to_stdout(self, server):
        """서버 시작 시 stdout 첫 줄에 LISTENING_PORT=<N> 이 출력된다."""
        proc, port = server
        # 최대 5초 대기
        proc.stdout._sock.settimeout(5) if hasattr(proc.stdout, '_sock') else None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if line.startswith("LISTENING_PORT="):
                emitted_port = int(line.strip().split("=")[1])
                assert emitted_port == port
                return
        pytest.fail("LISTENING_PORT= 가 5초 내에 stdout에 출력되지 않았습니다.")

    def test_health_endpoint_returns_200(self, server):
        """서버 시작 후 /health 가 200 을 반환해야 한다."""
        proc, port = server
        url = f"http://127.0.0.1:{port}/health"
        assert _wait_http(url, timeout=15), f"{url} 이 15초 내에 응답하지 않았습니다."

    def test_port_conflict_exits_with_code_1(self):
        """이미 사용 중인 포트로 서버를 실행하면 exit code 1 로 종료된다."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
            blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            blocker.bind(("127.0.0.1", 0))
            blocker.listen(1)
            used_port = blocker.getsockname()[1]

            proc = subprocess.run(
                [PYTHON, str(BACKEND_SERVER), "--port", str(used_port)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(ROOT),
            )
            assert proc.returncode == 1, (
                f"반환 코드가 1이어야 하는데 {proc.returncode}입니다.\n"
                f"stderr: {proc.stderr}"
            )
            assert "ERROR" in proc.stderr, "stderr에 ERROR 메시지가 없습니다."
