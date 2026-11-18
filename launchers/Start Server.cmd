@echo off
setlocal EnableExtensions
title Combat+ LAN - Start Server
rem Combat+ LAN party - host PC only.
rem Starts the dedicated server (BakersfieldQuake\server.cfg) and then joins it on this PC.

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
    pause
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

echo.
echo  Combat+ LAN server
echo  ------------------
echo  Windows Firewall may ask about zircon_beta_gcc.exe: tick "Private networks" and click Allow,
echo  otherwise the other PCs can't see or join this server.
echo  The server runs in its own window titled "Combat+ LAN Server" - close that window to stop it.
echo.

rem Don't start a second server if one is already running on this PC.
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter 'Name=''zircon_beta_gcc.exe''' | Where-Object { $_.CommandLine -match '-dedicated' }) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo  A server is already running on this PC - just joining it.
) else (
    start "Combat+ LAN Server" /D "%ROOT%\engine" "%ENGINE%" -dedicated 16 -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +exec server.cfg
    echo  Starting the server...
    rem Wait until the dedicated server finishes loading the map and answers LAN queries (up to ~12 s)
    for /L %%i in (1,1,20) do (
        for /f "tokens=1" %%a in ('%PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -Once -TimeoutMs 600 2^>nul') do if "%%a"=="FOUND" goto :serverready
    )
)
:serverready

rem First run (no saved config yet, or only the placeholder from the zip): use the Windows user name and a random colour.
set "FIRST="
set "NEWPLAYER="
if not exist "%ROOT%\BakersfieldQuake\config.cfg" set "NEWPLAYER=1"
findstr /m /c:"BAKERSFIELD_SEED" "%ROOT%\BakersfieldQuake\config.cfg" >nul 2>&1 && set "NEWPLAYER=1"
if not defined NEWPLAYER goto :haveconfig
set /a COLOR=%RANDOM% %% 14 * 17
set FIRST=+_cl_name "%USERNAME%" +_cl_color %COLOR%
:haveconfig

echo  Joining the game...
rem Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake %FIRST% %COMBAT_ARGS% +connect 127.0.0.1

rem Keep lan_server.cfg fresh so F2 rejoins after a disconnect.
start "" /min %PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -WatchExe "%ENGINE%"
popd
echo.
echo  Friends: double-click Play on their PCs. This window closes by itself.
timeout /t 20 >nul 2>&1
exit /b 0

:nogame
echo Could not find engine\zircon_beta_gcc.exe next to Start Server.cmd.
echo Unzip the whole BAKOQUAKE folder and run Start Server.cmd from inside it.
pause
exit /b 1
