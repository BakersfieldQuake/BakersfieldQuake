@echo off
setlocal EnableExtensions
rem BAKOQUAKE - Play.
rem Opens into the BakersfieldQuake Main Menu.
rem Use Join Game in the Main Menu (or press F3 in-game to run lan_server.cfg, which tools\lanscan.ps1 keeps updated).
rem Extra engine args (e.g. -window) can be passed with:  set COMBAT_ARGS=-window
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
    exit /b 1
)

rem Update: fetch only the files that changed in the newest release (set BQ_NO_UPDATE=1 to skip, e.g. offline at a LAN).
rem All on one line: cmd reads a running script from disk, so exit 3 restarts the updated launcher; exit 4 cancels cleanly;
rem any other non-zero exit code (or negative crash code) blocks launch so a half-updated install is never started.
if exist "%ROOT%\Update.exe" ( "%ROOT%\Update.exe" --launch --root "%ROOT%" & (if errorlevel 5 (popd & exit /b 1) else if errorlevel 4 (popd & exit /b 0) else if errorlevel 3 (popd & "%~f0" %*) else if errorlevel 1 (popd & exit /b 1) else if not errorlevel 0 (popd & exit /b 1)) ) else if exist "%ROOT%\tools\bq-update.exe" ( "%ROOT%\tools\bq-update.exe" --launch --root "%ROOT%" & (if errorlevel 5 (popd & exit /b 1) else if errorlevel 4 (popd & exit /b 0) else if errorlevel 3 (popd & "%~f0" %*) else if errorlevel 1 (popd & exit /b 1) else if not errorlevel 0 (popd & exit /b 1)) )

rem Start Menu and Desktop shortcuts (tools\install-shortcuts.ps1). The folder they point at is kept in shortcut-root.txt,
rem so PowerShell only runs on first launch or after the package moved (or after v2 shortcut migration). A failure never stops the launch.
set "BQMARK=%LOCALAPPDATA%\BAKOQUAKE\shortcut-root.txt"
set "BQOLD="
if exist "%BQMARK%" set /p BQOLD=<"%BQMARK%"
if /i not "%BQOLD%"=="v2|%ROOT%" if exist "%ROOT%\tools\install-shortcuts.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1" -Root "%ROOT%" >nul 2>&1 && <nul set /p "=v2|%ROOT%">"%BQMARK%"
)

rem Display & Graphics Picker (monitor, display mode, resolution, graphics preset).
rem Runs Update.exe --picker (or tools\bq_update.py --picker in dev trees); writes bq_launch_video.cfg and env vars.
set "BQPICKENV=%TEMP%\bq-pick-%RANDOM%-%RANDOM%.cmd"
set "PICKFLAGS="
if "%BQ_SETUP%"=="1" set "PICKFLAGS=--setup"
if not "%BQ_SETUP%"=="1" if "%BQ_NO_PROMPT%"=="1" set "PICKFLAGS=--no-gui"
set "BQ_PICK_CANCEL=0"
set "BQ_PICK_PRESET="
set "BQ_PICK_MODE="
set "BQ_PICK_WIDTH="
set "BQ_PICK_HEIGHT="
set "BQ_PICK_HZ="
set "BQ_PICK_MON_X="
set "BQ_PICK_MON_Y="
set "BQ_PICK_MON_W="
set "BQ_PICK_MON_H="
set "BQ_PICK_MON_PRIMARY="
set "BQ_PICK_CFG="
set "PICKPY=%ROOT%\tools\bq_update.py"
if not exist "%PICKPY%" set "PICKPY=%ROOT%\BakersfieldQuake\tools\bq_update.py"

if exist "%ROOT%\Update.exe" goto :pick_exe
if exist "%ROOT%\tools\bq-update.exe" goto :pick_legacy_exe
if not exist "%PICKPY%" goto :pickerdone
where python >nul 2>&1
if not errorlevel 1 goto :pick_py
where py >nul 2>&1
if not errorlevel 1 goto :pick_py3
goto :pickerdone

:pick_exe
"%ROOT%\Update.exe" --picker --root "%ROOT%" --userdir "%ROOT%" --out-env "%BQPICKENV%" --env-format cmd %PICKFLAGS%
goto :afterpicker

:pick_legacy_exe
"%ROOT%\tools\bq-update.exe" --picker --root "%ROOT%" --userdir "%ROOT%" --out-env "%BQPICKENV%" --env-format cmd %PICKFLAGS%
goto :afterpicker

:pick_py
python "%PICKPY%" --picker --root "%ROOT%" --userdir "%ROOT%" --out-env "%BQPICKENV%" --env-format cmd %PICKFLAGS%
goto :afterpicker

:pick_py3
py -3 "%PICKPY%" --picker --root "%ROOT%" --userdir "%ROOT%" --out-env "%BQPICKENV%" --env-format cmd %PICKFLAGS%
goto :afterpicker

:afterpicker
set "PICKRC=%ERRORLEVEL%"
if exist "%BQPICKENV%" (
    call "%BQPICKENV%"
    del /q "%BQPICKENV%" >nul 2>&1
)
if "%PICKRC%"=="4" (
    popd
    exit /b 0
)
if "%BQ_PICK_CANCEL%"=="1" (
    popd
    exit /b 0
)
:pickerdone

set "SCAN=%~dp0tools\lanscan.ps1"
if not exist "%SCAN%" set "SCAN=%~dp0lanscan.ps1"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden"

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

if exist "%PREFLIGHT%" (
    if defined BQ_PICK_PRESET (
        powershell -NoProfile -ExecutionPolicy Bypass -File "%PREFLIGHT%" -Root "%ROOT%" -OutEnvFile "%BQENV%" -UserPreset "%BQ_PICK_PRESET%" >nul 2>&1
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -File "%PREFLIGHT%" -Root "%ROOT%" -OutEnvFile "%BQENV%" >nul 2>&1
    )
)
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
set "LOWMEM="
set "LOWGPU="
set "WEAKGPU="
if defined BQ_PICK_PRESET goto :fallback_overrides
set "BQRAMF=%LOCALAPPDATA%\BAKOQUAKE\ram-gb.txt"
set "BQRAM="
if exist "%BQRAMF%" set /p BQRAM=<"%BQRAMF%"
if defined BQRAM echo %BQRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQRAM="
if not defined BQRAM call :readram
if defined BQRAM if 1%BQRAM% LSS 110 set "LOWMEM=+exec lowmem.cfg"

set "BQVRAMF=%LOCALAPPDATA%\BAKOQUAKE\vram-mb.txt"
set "BQGPUDONE=%LOCALAPPDATA%\BAKOQUAKE\lowgpu-applied.txt"
set "BQVRAM="
if exist "%BQVRAMF%" set /p BQVRAM=<"%BQVRAMF%"
if defined BQVRAM echo %BQVRAM%| findstr /r "^[0-9][0-9]*$" >nul || set "BQVRAM="
if not defined BQVRAM call :readvram
if "%BQVRAM%"=="0" set "BQVRAM="
if defined BQVRAM if 1%BQVRAM% LSS 13000 set "WEAKGPU=1"
if defined WEAKGPU set "LOWMEM=+exec lowmem.cfg"
if defined WEAKGPU if not exist "%BQGPUDONE%" set "LOWGPU=+exec lowgpu.cfg"
:fallback_overrides
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

set "PICKARGS="
if defined BQ_PICK_CFG set "PICKARGS=+exec %BQ_PICK_CFG%"

rem First run (no saved config yet, or only the placeholder from the zip): use the Windows user name and a random colour.
set "FIRST="
set "NEWPLAYER="
if not exist "%ROOT%\BakersfieldQuake\config.cfg" set "NEWPLAYER=1"
findstr /m /c:"BAKERSFIELD_SEED" "%ROOT%\BakersfieldQuake\config.cfg" >nul 2>&1 && set "NEWPLAYER=1"
if not defined NEWPLAYER goto :haveconfig
set /a COLOR=%RANDOM% %% 14 * 17
set FIRST=+_cl_name "%USERNAME%" +_cl_color %COLOR%
:haveconfig

rem Game log rotation fallback (if preflight did not already rotate it). Preserve copy if target is locked.
if not "%BQ_PRE_LOG_ROTATED%"=="1" if exist "%ROOT%\BakersfieldQuake\bq_game.log" (
    move /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1 || copy /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1
)

rem Keys (F1 = add bot, F2 = remove bot, F3 = LAN) are defaults in default.cfg/bm_binds.cfg, not forced here.
rem PICKARGS (+exec bq_launch_video.cfg) runs before TIERARGS so crash-recovery safemode.cfg cleanly overrides it.
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_game.log %FIRST% %PICKARGS% %TIERARGS% %COMBAT_ARGS%

rem Background watchdog: places window on chosen monitor on startup, clears session-active.flag and writes
rem lowgpu-applied.txt ONLY after clean exit, restores config.cfg after temporary Safe Mode/Ultra-Low sessions,
rem preserves bq_game_crash.log on crash/hang, and offers Safe Mode / Report a Problem if frozen >60s.
set "WATCHMARK="
if "%BQ_PRE_MARK_LOWGPU%"=="1" set "WATCHMARK=-WatchMarkLowGpu"
set "WATCHRESTORE="
if "%BQ_PRE_RESTORE_CONFIG%"=="1" set "WATCHRESTORE=-WatchRestoreConfig"
set "WATCHMON="
if defined BQ_PICK_MON_W if defined BQ_PICK_MON_H if defined BQ_PICK_MON_X if defined BQ_PICK_MON_Y set "WATCHMON=-TargetMonitorRect "%BQ_PICK_MON_X%,%BQ_PICK_MON_Y%,%BQ_PICK_MON_W%,%BQ_PICK_MON_H%""
set "WATCHMODE="
if defined BQ_PICK_MODE set "WATCHMODE=-TargetDisplayMode "%BQ_PICK_MODE%""
set "WATCHSIZE="
if defined BQ_PICK_WIDTH if defined BQ_PICK_HEIGHT set "WATCHSIZE=-TargetSize "%BQ_PICK_WIDTH%,%BQ_PICK_HEIGHT%""
set "WATCHPRIM="
if defined BQ_PICK_MON_PRIMARY set "WATCHPRIM=-TargetMonitorPrimary "%BQ_PICK_MON_PRIMARY%""
if defined USED_PREFLIGHT (
    if not "%BQ_WATCHDOG%"=="0" start "" /min %PS% -File "%PREFLIGHT%" -Root "%ROOT%" -WatchExe "%ENGINE%" -WatchTier "%BQ_PRE_TIER%" %WATCHMARK% %WATCHRESTORE% %WATCHMON% %WATCHMODE% %WATCHSIZE% %WATCHPRIM%
) else (
    if defined LOWGPU if defined WEAKGPU <nul set /p "=1">"%BQGPUDONE%"
)

rem Keep lan_server.cfg fresh in the background for optional F3 LAN fallback until the game exits.
if exist "%SCAN%" start "" /min %PS% -File "%SCAN%" -GameDir "%ROOT%\BakersfieldQuake" -WatchExe "%ENGINE%"
popd
exit /b 0

:nogame
echo Could not find engine\zircon_beta_gcc.exe next to Play.cmd.
echo Unzip the whole BAKOQUAKE folder and run Play.cmd from inside it.
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
