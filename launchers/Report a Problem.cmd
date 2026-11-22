@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Report a Problem.
rem Creates BAKOQUAKE-report-YYYYMMDD-HHMMSS.zip on your Desktop containing summary.txt, full game/server logs,
rem config.cfg, updater logs/state, hardware + GPU details, Windows crash/hang/TDR/OOM events, and map/pk3 hashes.
rem Nothing is sent anywhere. Send the zip file to whoever is helping you.

rem Package root is this folder; in the dev tree it is one (Combat\lan\) or two (Combat\BakersfieldQuake\launchers\) folders up.
set "ROOT=%~dp0"
if not exist "%ROOT%engine\zircon_beta_gcc.exe" if exist "%~dp0..\engine\zircon_beta_gcc.exe" set "ROOT=%~dp0..\"
if not exist "%ROOT%engine\zircon_beta_gcc.exe" if exist "%~dp0..\..\engine\zircon_beta_gcc.exe" set "ROOT=%~dp0..\..\"
pushd "%ROOT%" || goto :nogame
set "ROOT=%CD%"
popd
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "TOOL=%ROOT%\tools\bq-report.ps1"
if not exist "%TOOL%" set "TOOL=%ROOT%\BakersfieldQuake\tools\bq-report.ps1"
if not exist "%TOOL%" goto :nogame

echo Collecting BAKOQUAKE diagnostic report (this may take a few seconds)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%TOOL%" -Root "%ROOT%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo ERROR: Could not create the problem report ^(PowerShell exited with code %RC%^).
    echo Make sure your Desktop is writable and try running this script again.
    if not defined BQ_REPORT_NO_OPEN pause
    exit /b %RC%
)
echo.
echo Send the highlighted zip file on your Desktop to whoever is helping you.
if not defined BQ_REPORT_NO_OPEN pause
exit /b 0

:nogame
echo Could not find tools\bq-report.ps1 next to this file.
echo Unzip the whole BAKOQUAKE folder and run "Report a Problem.cmd" from inside it.
if not defined BQ_REPORT_NO_OPEN pause
exit /b 1
