@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Display & Graphics Settings.
rem Reopens the pre-launch Display & Graphics Setup picker (monitor, display mode, resolution, graphics preset)
rem even if "Remember my settings" was previously enabled.

set "BQ_SETUP=1"
set "PLAY=%~dp0Play.cmd"
if not exist "%PLAY%" if exist "%~dp0..\Play.cmd" set "PLAY=%~dp0..\Play.cmd"
if not exist "%PLAY%" if exist "%~dp0..\launchers\Play.cmd" set "PLAY=%~dp0..\launchers\Play.cmd"
if not exist "%PLAY%" (
    echo Could not find Play.cmd next to Display Settings.cmd.
    echo Unzip the whole BAKOQUAKE folder and run "Display Settings.cmd" from inside it.
    pause
    exit /b 1
)
call "%PLAY%" %*
exit /b %ERRORLEVEL%
