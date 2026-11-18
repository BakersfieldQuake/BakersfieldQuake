@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Play.
rem Opens into the BakersfieldQuake Main Menu (with a slow scenic background map when menu_background is 1).
rem Use Join Game in the Main Menu (or press F3 in-game to run lan_server.cfg, which tools\lanscan.ps1 keeps updated).
rem Extra engine args (e.g. -window) can be passed with:  set COMBAT_ARGS=-window

rem Package root is this folder; in the dev tree it is one folder up (Combat\lan\) or two (Combat\BakersfieldQuake\launchers\).
set "ROOT=%~dp0"
if not exist "%ROOT%engine\zircon_beta_gcc.exe" if exist "%~dp0..\engine\zircon_beta_gcc.exe" set "ROOT=%~dp0..\"
if not exist "%ROOT%engine\zircon_beta_gcc.exe" if exist "%~dp0..\..\engine\zircon_beta_gcc.exe" set "ROOT=%~dp0..\..\"
pushd "%ROOT%" || goto :nogame
set "ROOT=%CD%"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "ENGINE=%ROOT%\engine\zircon_beta_gcc.exe"
if not exist "%ENGINE%" goto :nogame

rem First run: the package ships no id Software data, so find the player's own Quake pak0/pak1 (Steam, GOG, the usual
rem folders, Downloads) and copy them into id1\. find-quake-paks.ps1 shows a message box when it can't find them.
if not exist "%ROOT%\id1\pak0.pak" if exist "%ROOT%\tools\find-quake-paks.ps1" powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\find-quake-paks.ps1" -Root "%ROOT%"
if not exist "%ROOT%\id1\pak0.pak" (
    echo id1\pak0.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into "%ROOT%\id1\".
    popd
    exit /b 1
)

rem Update: fetch only the files that changed in the newest release (set BQ_NO_UPDATE=1 to skip, e.g. offline at a LAN).
rem All on one line: cmd reads a running script from disk, so when files changed (exit 3) the updated launcher restarts.
if exist "%ROOT%\tools\bq-update.exe" ( "%ROOT%\tools\bq-update.exe" --launch --root "%ROOT%" & if errorlevel 3 if not errorlevel 4 ( popd & "%~f0" %* ) )

rem Start Menu and Desktop shortcuts (tools\install-shortcuts.ps1). The folder they point at is kept in shortcut-root.txt,
rem so PowerShell only runs on first launch or after the package moved. A failure never stops the launch.
set "BQMARK=%LOCALAPPDATA%\BAKOQUAKE\shortcut-root.txt"
set "BQOLD="
if exist "%BQMARK%" set /p BQOLD=<"%BQMARK%"
if /i not "%BQOLD%"=="%ROOT%" if exist "%ROOT%\tools\install-shortcuts.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1" -Root "%ROOT%" >nul 2>&1 && <nul set /p "=%ROOT%">"%BQMARK%"
)

set "SCAN=%~dp0tools\lanscan.ps1"
if not exist "%SCAN%" set "SCAN=%~dp0lanscan.ps1"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden"

rem First run (no saved config yet, or only the placeholder from the zip): use the Windows user name and a random colour.
set "FIRST="
set "NEWPLAYER="
if not exist "%ROOT%\BakersfieldQuake\config.cfg" set "NEWPLAYER=1"
findstr /m /c:"BAKERSFIELD_SEED" "%ROOT%\BakersfieldQuake\config.cfg" >nul 2>&1 && set "NEWPLAYER=1"
if not defined NEWPLAYER goto :haveconfig
set /a COLOR=%RANDOM% %% 14 * 17
set FIRST=+_cl_name "%USERNAME%" +_cl_color %COLOR%
:haveconfig

rem Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake %FIRST% %COMBAT_ARGS%

rem Keep lan_server.cfg fresh in the background for optional F3 LAN fallback until the game exits.
if exist "%SCAN%" start "" /min %PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -WatchExe "%ENGINE%"
popd
exit /b 0

:nogame
echo Could not find engine\zircon_beta_gcc.exe next to Play.cmd.
echo Unzip the whole BAKOQUAKE folder and run Play.cmd from inside it.
pause
exit /b 1
