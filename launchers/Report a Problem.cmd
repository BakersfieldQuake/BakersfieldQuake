@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Report a Problem.
rem Writes BAKOQUAKE-report.txt to your Desktop and opens it: package version, PC and graphics details, what the launcher
rem decided, a few graphics settings, the end of the last game logs and the crashes Windows recorded for the game.
rem Nothing is sent anywhere. Send the file to whoever is helping you.

rem Package root is this folder; in the dev tree it is two folders up (Combat\BakersfieldQuake\launchers\).
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
powershell -NoProfile -ExecutionPolicy Bypass -File "%TOOL%" -Root "%ROOT%"
exit /b 0

:nogame
echo Could not find tools\bq-report.ps1 next to this file.
echo Unzip the whole BAKOQUAKE folder and run "Report a Problem.cmd" from inside it.
pause
exit /b 1
