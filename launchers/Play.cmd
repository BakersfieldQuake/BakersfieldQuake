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

rem Game log. The engine appends to its log, so the previous one is moved aside first: BakersfieldQuake\bq_game.log is
rem this session, bq_game_prev.log the one before. "Report a Problem.cmd" reads both after a crash or a bad session.
if exist "%ROOT%\BakersfieldQuake\bq_game.log" move /y "%ROOT%\BakersfieldQuake\bq_game.log" "%ROOT%\BakersfieldQuake\bq_game_prev.log" >nul 2>&1
rem Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
start "" /D "%ROOT%\engine" "%ENGINE%" -basedir "%ROOT%" -userdir "%ROOT%" -game quake15 -game BakersfieldQuake +log_file bq_game.log %FIRST% %LOWMEM% %LOWGPU% %COMBAT_ARGS%
if defined LOWGPU if defined WEAKGPU <nul set /p "=1">"%BQGPUDONE%"

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
