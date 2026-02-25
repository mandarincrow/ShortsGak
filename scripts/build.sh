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
echo "[1/4] 프론트엔드 빌드 중..."
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
echo "[2/4] Python 가상환경 준비 중..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

pip install -U pip --quiet
pip install -r backend/requirements.txt -r desktop_launcher/requirements.txt --quiet
echo "[OK] 가상환경 및 의존성 준비 완료"
echo

# ─────────────────────────────────────────────
# 3. PyInstaller 설치 및 빌드
# ─────────────────────────────────────────────
echo "[3/4] PyInstaller 빌드 중..."
pip install pyinstaller --quiet
pyinstaller ShortsGak.spec --clean --noconfirm
echo "[OK] 빌드 성공"
echo

# ─────────────────────────────────────────────
# 4. 결과 요약
# ─────────────────────────────────────────────
echo "[4/4] 빌드 결과"
echo "----------------------------------------"
echo "  실행 파일: $ROOT/dist/ShortsGak/ShortsGak"
echo "  배포 폴더: $ROOT/dist/ShortsGak/"
echo "----------------------------------------"
echo "  Linux/macOS에서 pywebview GUI 확인 시 GTK 또는 Qt 런타임이 필요합니다."
echo "  Windows exe 배포는 Windows 환경에서 build.bat 을 사용하세요."
echo "============================================================"
