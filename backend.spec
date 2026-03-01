# -*- mode: python ; coding: utf-8 -*-
#
# backend.spec
# PyInstaller 빌드 명세 — headless FastAPI 서버 전용
#
# 빌드 방법:
#   pip install pyinstaller
#   pyinstaller backend.spec --clean --noconfirm
#
# 출력: dist/backend/ 폴더 → backend.exe 포함
#
# 전제 조건:
#   - 프론트엔드를 먼저 빌드해 frontend/dist/ 를 생성해야 합니다.
#     (cd frontend && npm run build)
#   - 기존 ShortsGak.spec(pywebview 포함)과는 다른 파일입니다.
#     Electron이 backend.exe 를 자식 프로세스로 실행합니다.
#
# 주요 차이점 (vs ShortsGak.spec):
#   - entry point : backend/backend_server.py  (desktop_launcher/run_desktop.py 아님)
#   - console=True : GUI 없음, Electron 이 창을 담당
#   - pywebview / clr / clr_loader / tkinter 완전 제거 → 시스템 의존성 없음
#   - 출력 이름 : backend  (→ dist/backend/backend.exe)

from pathlib import Path

# ---------------------------------------------------------------------------
# 리소스 경로 정의
# ---------------------------------------------------------------------------
ROOT = Path(SPECPATH)  # backend.spec 이 위치한 프로젝트 루트

added_datas = [
    # 프론트엔드 정적 파일: FastAPI 가 직접 서빙
    (str(ROOT / "frontend" / "dist"), "frontend/dist"),
    # 백엔드 패키지: _MEIPASS/backend/app/ 에 배치
    # backend_server.py 가 _MEIPASS/backend 를 sys.path 에 추가하므로
    # `import app.main` 이 동작합니다
    (str(ROOT / "backend" / "app"), "backend/app"),
]

# ---------------------------------------------------------------------------
# Hidden imports
# uvicorn / fastapi 의 동적 로더는 PyInstaller 가 자동 탐지하지 못하는 경우가 있음
# pywebview · clr · tkinter 는 Electron 전환으로 완전 제거
# ---------------------------------------------------------------------------
hidden_imports = [
    # uvicorn internals
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.loops.uvloop",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.wsproto_impl",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.off",
    "uvicorn.lifespan.on",
    # fastapi / starlette
    "fastapi",
    "fastapi.middleware.cors",
    "starlette.staticfiles",
    "starlette.responses",
    # app 패키지 (backend/app/)
    "app.main",
    "app.schemas",
    "app.parser",
    "app.analyzer",
    "app.logging_config",
    "app.chatlog_cache",
    "app.chatlog_fetcher",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "backend" / "backend_server.py")],
    pathex=[
        str(ROOT),
        str(ROOT / "backend"),  # PyInstaller 빌드 시 `app` 패키지 탐색 경로
    ],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "scipy",
        # GUI / WebView 관련 — Electron 전환으로 불필요
        "webview", "clr", "clr_loader",
        "tkinter", "tkinter.font", "tkinter.ttk",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # headless 서버 — 터미널 출력 필요 (LISTENING_PORT= 등)
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="backend",  # 출력: dist/backend/
)
