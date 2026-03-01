#!/usr/bin/env bash
# ShortsGak 빌드 스크립트 (Linux / macOS)
# NOTE: PyInstaller는 현재 OS 용 바이너리만 생성합니다.
#       Windows exe 를 만들려면 Windows 환경에서 scripts/build.bat 을 실행하세요.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "============================================================"
echo " ShortsGak 빌드 스크립트 (Linux/macOS)"
echo "============================================================"
echo

# ─────────────────────────────────────────────
# 1. 프론트엔드 빌드
# ─────────────────────────────────────────────
echo "[clean] 이전 빌드 아티팩트 정리 중..."
rm -rf "$ROOT/dist/backend" "$ROOT/build/backend" "$ROOT/electron/dist"
echo "[clean] 완료"
echo

echo "[1/5] 프론트엔드 빌드 중..."
if ! command -v npm &>/dev/null; then
    echo "[ERROR] npm 을 찾을 수 없습니다. Node.js 를 설치하세요."
    exit 1
fi

cd frontend
npm install
npm run build
cd "$ROOT"
echo "[OK] 프론트엔드 빌드 완료"
echo

# ─────────────────────────────────────────────
# 2. Python 가상환경 준비
# ─────────────────────────────────────────────
echo "[2/5] Python 가상환경 준비 중..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

pip install -U pip --quiet
pip install -r backend/requirements.txt --quiet
echo "[OK] 가상환경 및 의존성 준비 완료"
echo

# ─────────────────────────────────────────────
# 3. PyInstaller 빌드
# ─────────────────────────────────────────────
echo "[3/5] PyInstaller 빌드 중..."
pip install pyinstaller --quiet
pyinstaller backend.spec --clean --noconfirm
echo "[OK] backend.exe 빌드 성공"
echo

# ─────────────────────────────────────────────
# 4. Electron 빌드
# ─────────────────────────────────────────────
echo "[4/5] Electron 빌드 중..."
if ! command -v npm &>/dev/null; then
    echo "[ERROR] npm 을 찾을 수 없습니다. Node.js 를 설치하세요."
    exit 1
fi

cd electron
npm install
# 코드사이닝 인증서 없이 빌드 -- winCodeSign symlink 오류 방지
export CSC_IDENTITY_AUTO_DISCOVERY=false
npx electron-builder
cd "$ROOT"
echo "[OK] Electron 빌드 성공"
echo

# ─────────────────────────────────────────────
# 5. 결과 요약
# ─────────────────────────────────────────────
echo "[5/5] 빌드 결과"
echo "----------------------------------------"
echo "  backend.exe : $ROOT/dist/backend/backend.exe"
echo "  Electron 앱 : $ROOT/electron/dist/win-unpacked/ (Windows 빌드 시)"
echo "----------------------------------------"
echo "  NOTE: Windows exe 배포는 Windows 환경에서 build.bat 을 사용하세요."
echo "============================================================"
