@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Play.
rem Joins the LAN server if one is up. Otherwise it starts the game on its own, and quake.rc then plays the
rem BAKOQUAKE intro demo (intro.dem). In the intro, F1 joins the online server and F2 the LAN game.
rem In game, F2 joins the LAN server once it is up (F2 runs lan_server.cfg, which the
rem background scanner tools\lanscan.ps1 keeps up to date).
rem Extra engine args (e.g. -window) can be passed with:  set COMBAT_ARGS=-window

rem Package root is this folder; in the dev tree (Combat\lan\) it is one folder up.
set "ROOT=%~dp0"
if not exist "%ROOT%darkplaces.exe" if exist "%~dp0..\darkplaces.exe" set "ROOT=%~dp0..\"
pushd "%ROOT%" || goto :nogame
set "ROOT=%CD%"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
if not exist "%ROOT%\darkplaces.exe" goto :nogame

rem First run: find Quake's pak0/pak1 (Steam, GOG, the usual folders, Downloads) and copy them into id1\.
if not exist "%ROOT%\id1\pak0.pak" if exist "%ROOT%\tools\find-quake-paks.ps1" powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\find-quake-paks.ps1" -Root "%ROOT%"
if not exist "%ROOT%\id1\pak0.pak" (
    echo id1\pak0.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into "%ROOT%\id1\".
    popd
    exit /b 1
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

rem Quick scan (~1.5 s). This also hides this console window.
set "SERVER="
for /f "tokens=1,2" %%a in ('%PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -Once -TimeoutMs 1500 2^>nul') do if "%%a"=="FOUND" set "SERVER=%%b"

set "JOIN="
if defined SERVER set "JOIN=+connect %SERVER%"

rem Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
start "" "%ROOT%\darkplaces.exe" -game quake15 -game BakersfieldQuake %FIRST% %COMBAT_ARGS% %JOIN%

rem Keep lan_server.cfg fresh until the game exits.
start "" /min %PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -WatchExe "%ROOT%\darkplaces.exe"
popd
exit /b 0

:nogame
echo Could not find darkplaces.exe next to Play.cmd.
echo Unzip the whole BAKOQUAKE folder and run Play.cmd from inside it.
pause
exit /b 1
