@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0.."
set "LOG_DIR=%ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\build_windows.log"
set "RELEASE_VERSION=%~1"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

:: 콘솔에 컬러 헤더 출력 (로그 리디렉션 바깥)
powershell -NoProfile -Command "Write-Host ''; Write-Host '  +-------------------------------------+' -ForegroundColor Cyan; Write-Host '  |      ShortsGak  Windows  Build      |' -ForegroundColor Cyan; Write-Host '  +-------------------------------------+' -ForegroundColor Cyan; Write-Host ''"

if defined RELEASE_VERSION (
    powershell -NoProfile -Command "Write-Host '  Version : %RELEASE_VERSION%' -ForegroundColor White"
) else (
    powershell -NoProfile -Command "Write-Host '  Version : (auto)' -ForegroundColor DarkGray"
)
powershell -NoProfile -Command "Write-Host '  Log     : %LOG_FILE%' -ForegroundColor DarkGray; Write-Host ''"

:: :main 의 모든 출력은 로그 파일로, 콘솔 진행 상황은 > CON 으로 직접 출력
call :main >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% == 0 (
    powershell -NoProfile -Command "Write-Host ''; Write-Host '  [OK] BUILD SUCCESS' -ForegroundColor Green; Write-Host ''"
) else (
    powershell -NoProfile -Command "Write-Host ''; Write-Host '  [!!] BUILD FAILED' -ForegroundColor Red"
    powershell -NoProfile -Command "Write-Host '       log: %LOG_FILE%' -ForegroundColor DarkGray; Write-Host ''"
)
exit /b %EXIT_CODE%

:: ─────────────────────────────────────────────────────────
:main
:: ─────────────────────────────────────────────────────────

set "ROOT=%~dp0.."
cd /d "%ROOT%"
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"
set "PYTHON_CMD="
set "BUILD_STEP_OK=0"

echo ================================================
echo  Build started  %DATE% %TIME%
echo ================================================

:: ── Step 1 ──────────────────────────────────────
call :step_start 1 "Frontend  (npm install + build)"
cd frontend

where npm >nul 2>&1
if errorlevel 1 ( echo [ERROR] npm not found. Install Node.js. & exit /b 1 )

call npm install
if errorlevel 1 ( echo [ERROR] npm install failed & exit /b 1 )

call npm run build
if errorlevel 1 ( echo [ERROR] npm run build failed & exit /b 1 )

cd "%ROOT%"
call :step_done 1

:: ── Step 2 ──────────────────────────────────────
call :step_start 2 "Python env  (venv + pip)"

where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD ( echo [ERROR] Python not found in PATH. & exit /b 1 )

if not exist ".venv" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 ( echo [ERROR] venv creation failed & exit /b 1 )
)
if not exist "%VENV_PY%" ( echo [ERROR] venv python missing: %VENV_PY% & exit /b 1 )

"%VENV_PY%" -m pip install -U pip --quiet
"%VENV_PY%" -m pip install -r backend\requirements.txt -r desktop_launcher\requirements.txt --quiet
if errorlevel 1 ( echo [ERROR] dependency install failed & exit /b 1 )

call :step_done 2

:: ── Step 3 ──────────────────────────────────────
call :step_start 3 "PyInstaller  (exe bundle)"
taskkill /IM ShortsGak.exe /F >nul 2>&1

"%VENV_PY%" -m pip install pyinstaller --quiet
if errorlevel 1 ( echo [ERROR] pyinstaller install failed & exit /b 1 )

"%VENV_PY%" -m PyInstaller ShortsGak.spec --clean --noconfirm
if errorlevel 1 ( echo [ERROR] pyinstaller build failed & exit /b 1 )

call :step_done 3

:: ── Step 4 ──────────────────────────────────────
call :step_start 4 "Release ZIP  (package_release.bat)"
call "%ROOT%\scripts\package_release.bat" %RELEASE_VERSION%
if errorlevel 1 ( echo [ERROR] release zip packaging failed & exit /b 1 )
call :step_done 4

:: ── Summary ─────────────────────────────────────
echo.
echo ================================================
echo  Build summary  %DATE% %TIME%
echo ================================================

set "EXE=%ROOT%\dist\ShortsGak\ShortsGak.exe"
if exist "%EXE%" (
    for %%F in ("%EXE%") do echo  exe   : %%~fF  [%%~zF bytes]
) else (
    echo  exe   : NOT FOUND
)

for /f "delims=" %%Z in ('dir /b /o-d "%ROOT%\release\ShortsGak-win64-*.zip" 2^>nul') do (
    for %%F in ("%ROOT%\release\%%Z") do echo  zip   : %%~fF  [%%~zF bytes]
    goto :zip_done
)
echo  zip   : NOT FOUND
:zip_done

echo ================================================
echo  ALL STEPS OK
echo ================================================
exit /b 0

:: ─────────────────────────────────────────────────────────
:step_start
:: %1 = step number (1-5), %2 = label
echo.
echo +---------------------------------------------
echo ^|  Step %~1 / 4  :  %~2
echo ^|  %TIME%
echo +---------------------------------------------
powershell -NoProfile -Command "Write-Host ('  [%~1/4] ' + '%~2' + ' ...') -ForegroundColor Yellow" > CON
exit /b 0

:step_done
:: %1 = step number
echo.
echo  -- Step %~1 done --  %TIME%
powershell -NoProfile -Command "Write-Host ('      done') -ForegroundColor Green" > CON
exit /b 0
