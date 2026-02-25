@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0.."
set "LOG_DIR=%ROOT%\logs"
set "PROJECT_LOG_FILE=%LOG_DIR%\build_windows.log"
set "LOG_FILE=%TEMP%\shortsgak_build_windows.log"
set "RELEASE_VERSION=%~1"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :main > "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

if exist "%LOG_FILE%" copy /y "%LOG_FILE%" "%PROJECT_LOG_FILE%" >nul 2>&1

echo [INFO] Build log: "%LOG_FILE%"
if exist "%PROJECT_LOG_FILE%" echo [INFO] Project log: "%PROJECT_LOG_FILE%"
exit /b %EXIT_CODE%

:main

echo [INFO] Build started
echo ================================================
echo ShortsGak Windows build
echo ================================================

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "PYTHON_CMD="
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"

echo [1/5] Frontend build
cd frontend

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js.
    exit /b 1
)

call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed
    exit /b 1
)

call npm run build
if errorlevel 1 (
    echo [ERROR] npm run build failed
    exit /b 1
)

cd "%ROOT%"
echo [OK] Frontend build done

echo [2/5] Python environment setup

where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python not found in PATH.
    exit /b 1
)

if not exist ".venv" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] venv creation failed
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo [ERROR] venv python missing: %VENV_PY%
    exit /b 1
)

"%VENV_PY%" -m pip install -U pip --quiet
"%VENV_PY%" -m pip install -r backend\requirements.txt -r desktop_launcher\requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] dependency install failed
    exit /b 1
)

echo [OK] Python environment ready

echo [3/5] PyInstaller build
taskkill /IM ShortsGak.exe /F >nul 2>&1
"%VENV_PY%" -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] pyinstaller install failed
    exit /b 1
)

"%VENV_PY%" -m PyInstaller ShortsGak.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] pyinstaller build failed
    exit /b 1
)

echo [4/5] Release zip
call "%ROOT%\scripts\package_release.bat" %RELEASE_VERSION%
if errorlevel 1 (
    echo [ERROR] release zip packaging failed
    exit /b 1
)

echo [5/5] Build result
echo exe: %ROOT%\dist\ShortsGak\ShortsGak.exe
echo dir: %ROOT%\dist\ShortsGak\
echo release: %ROOT%\release\
echo [OK] Build success
exit /b 0
