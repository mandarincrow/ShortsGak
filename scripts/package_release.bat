@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "DIST_DIR=%ROOT%\dist\ShortsGak"
set "RELEASE_DIR=%ROOT%\release"
set "RELEASE_README=%RELEASE_DIR%\README.txt"
set "VERSION=%~1"

if not exist "%DIST_DIR%" (
    echo [ERROR] Dist directory not found: "%DIST_DIR%"
    echo [HINT] Run scripts\build.bat first.
    exit /b 1
)

if not defined VERSION (
    for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set "VERSION=%%i"
)

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%" >nul 2>&1

(
echo ShortsGak Release Notes
echo ======================
echo.
echo [Quick Start]
echo 1^) Extract all files from this zip.
echo 2^) Run ShortsGak\ShortsGak.exe.
echo 3^) Enter VOD ID and keywords, then start analysis.
echo.
echo [Recommended Environment]
echo - Windows 10/11
echo - Internet connection ^(required for auto chatlog fetch^)
echo - WebView2 Runtime
echo.
echo [Troubleshooting]
echo - If you see "Failed to fetch", close the app completely and run it again.
echo - If the issue continues, check this log file:
echo   ShortsGak\_internal\backend\logs\app.log
echo.
echo [Project]
echo https://github.com/mandarincrow/ShortsGak
) > "%RELEASE_README%"

set "ZIP_NAME=ShortsGak-win64-%VERSION%.zip"
set "ZIP_PATH=%RELEASE_DIR%\%ZIP_NAME%"

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%" >nul 2>&1

powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%','%RELEASE_README%' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 (
    echo [ERROR] Failed to create release zip.
    exit /b 1
)

echo [OK] Release zip created: "%ZIP_PATH%"
exit /b 0
