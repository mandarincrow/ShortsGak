"""conftest.py

pytest 전역 설정. backend/ 를 sys.path 에 추가해
tests 에서 `import backend_server`, `import app.*` 가 가능하도록 한다.
"""
import sys
from pathlib import Path

# 프로젝트 루트 (tests/ 의 상위)
ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
