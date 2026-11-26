@echo off
setlocal EnableExtensions
title Combat+ LAN - Start Server
rem Combat+ LAN party - host PC only.
rem Starts the dedicated server (BakersfieldQuake\server.cfg) and then joins it on this PC.
rem Tier overrides: set BQ_TIER=normal|lowmem|ultralow|safemode  (or BQ_SAFEMODE=1, BQ_ULTRALOW=1, BQ_LOWMEM=1|0, BQ_LOWGPU=1|0)

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
rem All on one line: exit 3 restarts the updated launcher; exit 4 cancels cleanly; any other non-zero exit blocks launch.
if exist "%ROOT%\Update.exe" ( "%ROOT%\Update.exe" --launch --root "%ROOT%" & (if errorlevel 5 (popd & exit /b 1) else if errorlevel 4 (popd & exit /b 0) else if errorlevel 3 (popd & "%~f0" %*) else if errorlevel 1 (popd & exit /b 1) else if not errorlevel 0 (popd & exit /b 1)) ) else if exist "%ROOT%\tools\bq-update.exe" ( "%ROOT%\tools\bq-update.exe" --launch --root "%ROOT%" & (if errorlevel 5 (popd & exit /b 1) else if errorlevel 4 (popd & exit /b 0) else if errorlevel 3 (popd & "%~f0" %*) else if errorlevel 1 (popd & exit /b 1) else if not errorlevel 0 (popd & exit /b 1)) )

rem Quake's own lightning gun back, from your id1\pak0.pak: the mod's pk3s replace it, a loose copy beats them.
rem PowerShell only runs while that copy is missing or broken. A failure never stops the launch.
set "LGMDL=%ROOT%\BakersfieldQuake\progs\v_light.mdl"
set "LGOK="
if exist "%LGMDL%" for %%F in ("%LGMDL%") do if %%~zF GEQ 20000 set "LGOK=1"
if defined LGOK findstr /b /m /c:"IDPO" "%LGMDL%" >nul 2>&1
if defined LGOK if errorlevel 1 set "LGOK="
if not defined LGOK if exist "%ROOT%\tools\find-quake-paks.ps1" powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\find-quake-paks.ps1" -Root "%ROOT%"

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
    if exist "%ROOT%\BakersfieldQuake\bq_server.log" (
        move /y "%ROOT%\BakersfieldQuake\bq_server.log" "%ROOT%\BakersfieldQuake\bq_server_prev.log" >nul 2>&1 || copy /y "%ROOT%\BakersfieldQuake\bq_server.log" "%ROOT%\BakersfieldQuake\bq_server_prev.log" >nul 2>&1
    )
    start "Combat+ LAN Server" /D "%ROOT%\engine" "%ENGINE%" -dedicated 16 -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_server.log +exec server.cfg
    echo  Starting the server...
    rem Wait until the dedicated server finishes loading the map and answers LAN queries (up to ~12 s)
    for /L %%i in (1,1,20) do (
        for /f "tokens=1" %%a in ('%PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -Once -TimeoutMs 600 2^>nul') do if "%%a"=="FOUND" goto :serverready
    )
)
:serverready

rem Pre-flight hardware/live-RAM auto-tiering, crash/safe-mode recovery, and safe log rotation (tools\bq-preflight.ps1).
set "PREFLIGHT=%ROOT%\tools\bq-preflight.ps1"
if not exist "%PREFLIGHT%" set "PREFLIGHT=%ROOT%\BakersfieldQuake\tools\bq-preflight.ps1"
set "BQ_PRE_TIER="
set "BQ_PRE_ARGS="
set "BQ_PRE_CANCEL=0"
set "BQ_PRE_MARK_LOWGPU=0"
set "BQ_PRE_RESTORE_CONFIG=0"
set "BQ_PRE_LOG_ROTATED=0"
set "USED_PREFLIGHT="
set "TIERARGS="
set "BQENV=%TEMP%\bq-pre-%RANDOM%-%RANDOM%.cmd"

if exist "%PREFLIGHT%" powershell -NoProfile -ExecutionPolicy Bypass -File "%PREFLIGHT%" -Root "%ROOT%" -ServerMode -OutEnvFile "%BQENV%" >nul 2>&1
if exist "%BQENV%" (
    call "%BQENV%"
    del /q "%BQENV%" >nul 2>&1
    set "USED_PREFLIGHT=1"
)
if "%BQ_PRE_CANCEL%"=="1" (
    popd
    exit /b 0
)
if defined USED_PREFLIGHT (
    set "TIERARGS=%BQ_PRE_ARGS%"
    goto :tierdone
)

rem Fallback batch tiering if PowerShell / bq-preflight.ps1 is unavailable.
set "BQRAMF=%LOCALAPPDATA%\BAKOQUAKE\ram-gb.txt"
set "BQRAM="
if exist "%BQRAMF%" set /p BQRAM=<"%BQRAMF%"
if defined BQRAM echo %BQRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQRAM="
if not defined BQRAM call :readram
set "LOWMEM="
if defined BQRAM if 1%BQRAM% LSS 110 set "LOWMEM=+exec lowmem.cfg"

set "BQVRAMF=%LOCALAPPDATA%\BAKOQUAKE\vram-mb.txt"
set "BQGPUDONE=%LOCALAPPDATA%\BAKOQUAKE\lowgpu-applied.txt"
set "BQVRAM="
if exist "%BQVRAMF%" set /p BQVRAM=<"%BQVRAMF%"
if defined BQVRAM echo %BQVRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQVRAM="
if not defined BQVRAM call :readvram
if "%BQVRAM%"=="0" set "BQVRAM="
set "WEAKGPU="
if defined BQVRAM if 1%BQVRAM% LSS 13000 set "WEAKGPU=1"
if defined WEAKGPU set "LOWMEM=+exec lowmem.cfg"
set "LOWGPU="
if defined WEAKGPU if not exist "%BQGPUDONE%" set "LOWGPU=+exec lowgpu.cfg"
if "%BQ_LOWGPU%"=="1" set "LOWGPU=+exec lowgpu.cfg"
if "%BQ_LOWGPU%"=="0" set "LOWGPU="
if "%BQ_LOWMEM%"=="1" set "LOWMEM=+exec lowmem.cfg"
if "%BQ_LOWMEM%"=="0" set "LOWMEM="
set "TIERARGS=%LOWMEM% %LOWGPU%"
if /i "%BQ_TIER%"=="ultralow" set "TIERARGS=+exec ultralow.cfg"
if "%BQ_ULTRALOW%"=="1" set "TIERARGS=+exec ultralow.cfg"
if /i "%BQ_TIER%"=="safemode" set "TIERARGS=+exec safemode.cfg"
if "%BQ_SAFEMODE%"=="1" set "TIERARGS=+exec safemode.cfg"
if /i "%BQ_TIER%"=="normal" set "TIERARGS="

:tierdone

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
if not "%BQ_PRE_LOG_ROTATED%"=="1" if exist "%ROOT%\BakersfieldQuake\bq_game.log" (
    move /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1 || copy /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1
)
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_game.log %FIRST% %TIERARGS% %COMBAT_ARGS% +connect 127.0.0.1

set "WATCHMARK="
if "%BQ_PRE_MARK_LOWGPU%"=="1" set "WATCHMARK=-WatchMarkLowGpu"
set "WATCHRESTORE="
if "%BQ_PRE_RESTORE_CONFIG%"=="1" set "WATCHRESTORE=-WatchRestoreConfig"
if defined USED_PREFLIGHT (
    if not "%BQ_WATCHDOG%"=="0" start "" /min %PS% -File "%PREFLIGHT%" -Root "%ROOT%" -WatchExe "%ENGINE%" -WatchTier "%BQ_PRE_TIER%" %WATCHMARK% %WATCHRESTORE%
) else (
    if defined LOWGPU if defined WEAKGPU <nul set /p "=1">"%BQGPUDONE%"
)

rem Keep lan_server.cfg fresh so F3 rejoins after a disconnect.
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
rem Fallback: whole GB of RAM into BQRAM and ram-gb.txt.
for /f %%r in ('powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)" 2^>nul') do set "BQRAM=%%r"
if defined BQRAM echo %BQRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQRAM="
if not defined BQRAM exit /b 0
if not exist "%LOCALAPPDATA%\BAKOQUAKE" mkdir "%LOCALAPPDATA%\BAKOQUAKE" 2>nul
<nul set /p "=%BQRAM%">"%BQRAMF%"
exit /b 0

:readvram
rem Fallback: largest video memory of any graphics adapter, in MB, into BQVRAM and vram-mb.txt.
for /f %%r in ('powershell -NoProfile -Command "[math]::Round(((Get-CimInstance Win32_VideoController | Measure-Object -Property AdapterRAM -Maximum).Maximum)/1MB)" 2^>nul') do set "BQVRAM=%%r"
if defined BQVRAM echo %BQVRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQVRAM="
if not defined BQVRAM set "BQVRAM=0"
if not exist "%LOCALAPPDATA%\BAKOQUAKE" mkdir "%LOCALAPPDATA%\BAKOQUAKE" 2>nul
<nul set /p "=%BQVRAM%">"%BQVRAMF%"
exit /b 0
