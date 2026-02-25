# -*- mode: python ; coding: utf-8 -*-
#
# ShortsGak.spec
# PyInstaller 빌드 명세 파일
#
# 빌드 방법:
#   pip install pyinstaller
#   pyinstaller ShortsGak.spec
#
# 출력: dist/ShortsGak/ 폴더 → ShortsGak.exe 포함
#
# 주의사항:
# - 빌드 전에 반드시 프론트엔드를 먼저 빌드해 frontend/dist/를 생성해야 합니다.
#   (cd frontend && npm run build)
# - Windows 타깃 배포 시 WebView2 런타임 설치 필요
#   (Microsoft Edge WebView2 Runtime)

from pathlib import Path

block_cipher = None

# ---------------------------------------------------------------------------
# 리소스 경로 정의
# ---------------------------------------------------------------------------
ROOT = Path(SPECPATH)  # ShortsGak.spec이 위치한 프로젝트 루트

# 번들에 포함할 데이터 (src, dest_inside_bundle)
added_datas = [
    # 프론트엔드 정적 파일: frontend/dist/** → _MEIPASS/frontend/dist/
    (str(ROOT / "frontend" / "dist"), "frontend/dist"),
    # 백엔드 패키지: backend/app/ → _MEIPASS/backend/app/
    # run_desktop.py가 _MEIPASS/backend 를 sys.path에 추가하므로
    # `import app.main` 이 동작합니다
    (str(ROOT / "backend" / "app"), "backend/app"),
]

# ---------------------------------------------------------------------------
# uvicorn 및 fastapi의 동적 로더는 PyInstaller가 자동 탐지하지 못하는 경우가 있음
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
    # pywebview
    "webview",
    "webview.platforms.winforms",  # Windows 기본
    "webview.platforms.gtk",       # Linux GTK
    "webview.platforms.qt",        # Linux Qt
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "desktop_launcher" / "run_desktop.py")],
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
    excludes=["tkinter", "matplotlib", "numpy", "scipy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ShortsGak",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # Windows에서 터미널 창 숨김
    icon=None,       # TODO: icon을 추가하려면 ico 파일 경로 지정
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ShortsGak",
)
