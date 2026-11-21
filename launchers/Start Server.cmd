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
set "HAVEPAKS=1"
if not exist "%ROOT%\id1\pak0.pak" set "HAVEPAKS="
if not exist "%ROOT%\id1\pak1.pak" set "HAVEPAKS="
if not defined HAVEPAKS if exist "%ROOT%\tools\find-quake-paks.ps1" powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\find-quake-paks.ps1" -Root "%ROOT%"
set "HAVEPAKS=1"
if not exist "%ROOT%\id1\pak0.pak" set "HAVEPAKS="
if not exist "%ROOT%\id1\pak1.pak" set "HAVEPAKS="
if not defined HAVEPAKS (
    echo id1\pak0.pak or id1\pak1.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into "%ROOT%\id1\".
    popd
    pause
    exit /b 1
)

rem Update: fetch only the files that changed in the newest release (set BQ_NO_UPDATE=1 to skip, e.g. offline at a LAN).
rem All on one line: cmd reads a running script from disk, so when files changed (exit 3) the updated launcher restarts; exit 4 cancels launch.
if exist "%ROOT%\tools\bq-update.exe" ( "%ROOT%\tools\bq-update.exe" --launch --root "%ROOT%" & (if errorlevel 4 (if not errorlevel 5 (popd & exit /b 0)) else if errorlevel 3 (popd & "%~f0" %*)) )

rem Start Menu and Desktop shortcuts (tools\install-shortcuts.ps1). The folder they point at is kept in shortcut-root.txt,
rem so PowerShell only runs on first launch or after the package moved (or after v2 shortcut migration). A failure never stops the launch.
set "BQMARK=%LOCALAPPDATA%\BAKOQUAKE\shortcut-root.txt"
set "BQOLD="
if exist "%BQMARK%" set /p BQOLD=<"%BQMARK%"
if /i not "%BQOLD%"=="v2|%ROOT%" if exist "%ROOT%\tools\install-shortcuts.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1" -Root "%ROOT%" >nul 2>&1 && <nul set /p "=v2|%ROOT%">"%BQMARK%"
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
    rem Server log, kept like the game log below: bq_server.log, and the one before as bq_server_prev.log.
    if exist "%ROOT%\BakersfieldQuake\bq_server.log" move /y "%ROOT%\BakersfieldQuake\bq_server.log" "%ROOT%\BakersfieldQuake\bq_server_prev.log" >nul 2>&1
    start "Combat+ LAN Server" /D "%ROOT%\engine" "%ENGINE%" -dedicated 16 -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_server.log +exec server.cfg
    echo  Starting the server...
    rem Wait until the dedicated server finishes loading the map and answers LAN queries (up to ~12 s)
    for /L %%i in (1,1,20) do (
        for /f "tokens=1" %%a in ('%PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -Once -TimeoutMs 600 2^>nul') do if "%%a"=="FOUND" goto :serverready
    )
)
:serverready

rem Low-memory mode. With the normal settings the game needs about 4 GB of memory of its own, and on a PC with 8 GB the
rem map load can end in "Mem_Alloc: out of memory". Under 10 GB of RAM the game therefore starts with lowmem.cfg (model
rem textures at half size, about 2.5 GB). The RAM size is read once and kept in ram-gb.txt (delete it after a RAM upgrade).
rem   set BQ_LOWMEM=1  forces it on,  set BQ_LOWMEM=0  off.
set "BQRAMF=%LOCALAPPDATA%\BAKOQUAKE\ram-gb.txt"
set "BQRAM="
if exist "%BQRAMF%" set /p BQRAM=<"%BQRAMF%"
if defined BQRAM echo %BQRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQRAM="
if not defined BQRAM call :readram
set "LOWMEM="
rem (the leading 1 keeps the line valid when BQRAM is empty: 8 becomes 18, 16 becomes 116)
if defined BQRAM if 1%BQRAM% LSS 110 set "LOWMEM=+exec lowmem.cfg"

rem Weak graphics. A map loads 1.4 to 2.2 GB of textures. A graphics chip with under 3 GB of its own memory (integrated
rem graphics, or an old 2 GB card) cannot hold them, so such a PC also starts with lowmem.cfg. The first time it starts
rem the game it also gets lowgpu.cfg (the menu's Simple Mode, no anti-aliasing): ordinary saved settings from then on,
rem which Options changes back. The size is read once and kept in vram-mb.txt (delete it after a graphics card change;
rem 0 = unknown = normal settings). Windows reports at most 4095 here, which is all this test needs.
rem   set BQ_LOWGPU=1  applies lowgpu.cfg at this start,  set BQ_LOWGPU=0  never.
set "BQVRAMF=%LOCALAPPDATA%\BAKOQUAKE\vram-mb.txt"
set "BQGPUDONE=%LOCALAPPDATA%\BAKOQUAKE\lowgpu-applied.txt"
set "BQVRAM="
if exist "%BQVRAMF%" set /p BQVRAM=<"%BQVRAMF%"
if defined BQVRAM echo %BQVRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQVRAM="
if not defined BQVRAM call :readvram
if "%BQVRAM%"=="0" set "BQVRAM="
set "WEAKGPU="
rem (leading 1 again: 512 becomes 1512, 2048 becomes 12048, 4095 becomes 14095)
if defined BQVRAM if 1%BQVRAM% LSS 13000 set "WEAKGPU=1"
if defined WEAKGPU set "LOWMEM=+exec lowmem.cfg"
set "LOWGPU="
if defined WEAKGPU if not exist "%BQGPUDONE%" set "LOWGPU=+exec lowgpu.cfg"
if "%BQ_LOWGPU%"=="1" set "LOWGPU=+exec lowgpu.cfg"
if "%BQ_LOWGPU%"=="0" set "LOWGPU="

if "%BQ_LOWMEM%"=="1" set "LOWMEM=+exec lowmem.cfg"
if "%BQ_LOWMEM%"=="0" set "LOWMEM="

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
rem Game log. The engine appends to its log, so the previous one is moved aside first: BakersfieldQuake\bq_game.log is
rem this session, bq_game_prev.log the one before. "Report a Problem.cmd" reads both after a crash or a bad session.
if exist "%ROOT%\BakersfieldQuake\bq_game.log" move /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_game.log %FIRST% %LOWMEM% %LOWGPU% %COMBAT_ARGS% +connect 127.0.0.1
if defined LOWGPU if defined WEAKGPU <nul set /p "=1">"%BQGPUDONE%"

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

:readram
rem Whole GB of RAM into BQRAM and ram-gb.txt. Leaves BQRAM empty (= normal settings) when PowerShell gives no number.
for /f %%r in ('powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)" 2^>nul') do set "BQRAM=%%r"
if defined BQRAM echo %BQRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQRAM="
if not defined BQRAM exit /b 0
if not exist "%LOCALAPPDATA%\BAKOQUAKE" mkdir "%LOCALAPPDATA%\BAKOQUAKE" 2>nul
<nul set /p "=%BQRAM%">"%BQRAMF%"
exit /b 0

:readvram
rem Largest video memory of any graphics adapter, in MB, into BQVRAM and vram-mb.txt (0 when PowerShell gives no number).
for /f %%r in ('powershell -NoProfile -Command "[math]::Round(((Get-CimInstance Win32_VideoController | Measure-Object -Property AdapterRAM -Maximum).Maximum)/1MB)" 2^>nul') do set "BQVRAM=%%r"
if defined BQVRAM echo %BQVRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQVRAM="
if not defined BQVRAM set "BQVRAM=0"
if not exist "%LOCALAPPDATA%\BAKOQUAKE" mkdir "%LOCALAPPDATA%\BAKOQUAKE" 2>nul
<nul set /p "=%BQVRAM%">"%BQVRAMF%"
exit /b 0
