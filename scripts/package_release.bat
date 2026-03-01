@echo off
::
:: package_release.bat — ShortsGak 릴리즈 ZIP 패키저
::
::   사용법:
::     scripts\package_release.bat [version]
::
::   예시:
::     scripts\package_release.bat v1.0.0
::     scripts\package_release.bat              (VERSION 파일 또는 날짜 사용)
::
::   산출물:
::     release\ShortsGak-win64-<version>.zip
::

setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0.."
set "RELEASE_VERSION=%~1"

:: ── 콘솔 헤더 ───────────────────────────────────────────────────────────────
powershell -NoProfile -Command ^
  "Write-Host ''; Write-Host '  +-----------------------------------------+' -ForegroundColor Cyan; Write-Host '  |     ShortsGak  Release  Packager       |' -ForegroundColor Cyan; Write-Host '  +-----------------------------------------+' -ForegroundColor Cyan; Write-Host ''"

:: ── 버전 결정 ────────────────────────────────────────────────────────────────
:: 우선순위: 1) 인자  2) VERSION 파일  3) 날짜 스탬프
if defined RELEASE_VERSION goto :ver_done

if exist "%ROOT%\VERSION" (
    set /p RELEASE_VERSION=<"%ROOT%\VERSION"
    :: 앞뒤 공백/개행 제거
    for /f "tokens=* delims= " %%V in ("!RELEASE_VERSION!") do set "RELEASE_VERSION=%%V"
)

if not defined RELEASE_VERSION (
    for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set "RELEASE_VERSION=%%D"
)

:ver_done
set "RELEASE_NAME=ShortsGak-win64-!RELEASE_VERSION!"

powershell -NoProfile -Command "Write-Host '  Version  : !RELEASE_VERSION!' -ForegroundColor White"

:: ── 경로 설정 ────────────────────────────────────────────────────────────────
set "SOURCE=%ROOT%\electron\dist\electron\win-unpacked"
set "STAGING=%ROOT%\release\!RELEASE_NAME!"
set "ZIP_OUT=%ROOT%\release\!RELEASE_NAME!.zip"
set "SRC_README=%ROOT%\release\README.txt"

powershell -NoProfile -Command "Write-Host '  Source   : !SOURCE!' -ForegroundColor DarkGray"
powershell -NoProfile -Command "Write-Host '  Output   : !ZIP_OUT!' -ForegroundColor DarkGray; Write-Host ''"

:: ── 소스 검증 ────────────────────────────────────────────────────────────────
if not exist "!SOURCE!\ShortsGak.exe" (
    powershell -NoProfile -Command "Write-Host '  [ERROR] win-unpacked not found or ShortsGak.exe missing:' -ForegroundColor Red"
    powershell -NoProfile -Command "Write-Host '          !SOURCE!' -ForegroundColor Red"
    echo [ERROR] Build first with scripts\build.bat before packaging.
    exit /b 1
)

:: ── 스테이징 디렉터리 준비 ──────────────────────────────────────────────────
powershell -NoProfile -Command "Write-Host '  [1/3] Staging app files ...' -ForegroundColor Yellow"

if exist "!STAGING!" (
    echo  Removing existing staging dir: !STAGING!
    rmdir /s /q "!STAGING!"
)
mkdir "!STAGING!" >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Write-Host '  [ERROR] Cannot create staging dir: !STAGING!' -ForegroundColor Red"
    exit /b 1
)

:: electron/dist/win-unpacked → staging/ShortsGak/
xcopy /E /I /H /Y /Q "!SOURCE!" "!STAGING!\ShortsGak\" >nul
if errorlevel 1 (
    powershell -NoProfile -Command "Write-Host '  [ERROR] xcopy failed. Source: !SOURCE!' -ForegroundColor Red"
    exit /b 1
)

:: README.txt
if exist "!SRC_README!" (
    copy /Y "!SRC_README!" "!STAGING!\README.txt" >nul
) else (
    powershell -NoProfile -Command "Write-Host '  [WARN ] release\README.txt not found — skipped.' -ForegroundColor DarkYellow"
)

powershell -NoProfile -Command "Write-Host '      done' -ForegroundColor Green"

:: ── 기존 ZIP 제거 ────────────────────────────────────────────────────────────
if exist "!ZIP_OUT!" (
    powershell -NoProfile -Command "Write-Host '  Removing old ZIP ...' -ForegroundColor DarkGray"
    del /f /q "!ZIP_OUT!" >nul 2>&1
)

:: ── ZIP 생성 ─────────────────────────────────────────────────────────────────
:: Compress-Archive 는 .zip 확장자 파일(base_library.zip 등) 포함 시 IOException 발생
:: Windows 내장 tar(bsdtar) 로 대체 — -a 옵션이 .zip 확장자를 자동 감지
powershell -NoProfile -Command "Write-Host '  [2/3] Creating ZIP ...' -ForegroundColor Yellow"

tar -a -c -f "!ZIP_OUT!" -C "%ROOT%\release" "!RELEASE_NAME!"
if errorlevel 1 (
    powershell -NoProfile -Command "Write-Host '  [ERROR] ZIP creation failed.' -ForegroundColor Red"
    exit /b 1
)

powershell -NoProfile -Command "Write-Host '      done' -ForegroundColor Green"

:: ── 스테이징 정리 ────────────────────────────────────────────────────────────
powershell -NoProfile -Command "Write-Host '  [3/3] Cleaning staging dir ...' -ForegroundColor Yellow"
rmdir /s /q "!STAGING!" >nul 2>&1
powershell -NoProfile -Command "Write-Host '      done' -ForegroundColor Green"

:: ── 결과 출력 ────────────────────────────────────────────────────────────────
for %%F in ("!ZIP_OUT!") do (
    set "ZIP_SIZE=%%~zF"
)
set /a ZIP_MB=!ZIP_SIZE! / 1048576

powershell -NoProfile -Command ^
  "Write-Host ''; Write-Host '  [OK] Package ready' -ForegroundColor Green; Write-Host '       !ZIP_OUT!' -ForegroundColor White; Write-Host '       Size : !ZIP_MB! MB' -ForegroundColor DarkGray; Write-Host ''"

exit /b 0
