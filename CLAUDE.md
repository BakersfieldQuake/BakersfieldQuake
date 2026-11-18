@AGENTS.md

# BakersfieldQuake

## Engine

- **We are NOT using DarkPlaces anymore — we are using Zircon Engine** (`G:\Quake\Combat\engine\zircon_beta_gcc.exe`, launched for players by `G:\Quake\Combat\Play BakersfieldQuake.exe`).
- `darkplaces.exe` is gone; do not try to launch or check for `darkplaces.exe`.

## Testing in game

- **Never test on dm6.** Many of its spawns are in a tiny box with no room to try anything.
- **Test on the map `start`**: `+map start` (with `+deathmatch 1` when the LAN rules matter).
- Launch tests using `G:\Quake\Combat\engine\zircon_beta_gcc.exe` (working directory `G:\Quake\Combat\engine`, with `-basedir G:\Quake\Combat`) and an isolated `-userdir` and test `-port` (e.g. `26098`) so `-window -width 1280 -height 720` / `freelook 0` / `vid_mouse 0` test runs NEVER overwrite the user's `G:\Quake\Combat\BakersfieldQuake\config.cfg`:
  `zircon_beta_gcc.exe -basedir G:\Quake\Combat -userdir <temp_dir> -port 26098 -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake ... +map start`.
  Run scripted test configs with `+defer <seconds> "exec <cfg>"`, not straight from the command line. A `wait` chain run straight from the command line blocks the client's sign-on, so the game never finishes loading.
- Read results from a log, not `condump`: the HUD spams the console every frame, so a dump only holds the last few seconds. Launch with `-condebug +log_file zz_x.log` and grep that file in the mod folder.
- Bots need player slots: put `+maxplayers 4` before `+map` or `bm_botfill` reports the server is full.

## Where test games open

- Test games open on the user's **right (primary) monitor**: run `G:\Quake\Combat\engine\zircon_beta_gcc.exe` (with working directory `G:\Quake\Combat\engine`, `-basedir G:\Quake\Combat`, and `-userdir <temp_dir> -port 26098` so it never writes to `BakersfieldQuake\config.cfg`). Do not use `source\mm_tools\launch_left.ps1` (it targets the old `darkplaces.exe`):
  `zircon_beta_gcc.exe -basedir G:\Quake\Combat -userdir <temp_dir> -port 26098 -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake +deathmatch 1 +map start +defer 12 "exec <cfg>"`
- (The user went back and forth on this. The latest, from them directly on 2026-10-30, is the right monitor. On the left monitor the old engine spun the view whenever the mouse was on.)
- Keep test runs short and unattended (the cfg ends with `quit`). The user may be playing on the same machine: do not leave a game window open waiting, and close it as soon as the screenshots are written.
- Several Claude sessions test this game on the same machine. Before a test, check that no other `zircon_beta_gcc.exe` is running (another session's test, or the user's game) and wait if one is. When cleaning up, stop only the process your own launch started (by its id), never every Zircon process.

## HUD & Screen Overlay Rule

- **No ugly, dark, annoying menus or boxes slapped across the screen.** Never draw opaque/dark `drawfill` panels (`JBH_Box`, `HUD_Box`, `RH_Box`, or raw `drawfill` rectangles) over the middle/center of the viewport or behind status/debuff/toast/control overlays.
- **Corner text overlays only:** Place status text, debuffs, prompts, vehicle telemetry, and centerprint toasts as clean drop-shadowed text (`BM_DrawColorShadow`, `BM_ShadowColorRight`, `JBH_ShadowLeft`, `JBH_ShadowRight`) in one of the four screen corners — **top-left**, **top-right**, **bottom-left**, or **bottom-right** — keeping the center of the screen completely clear for 1st- and 3rd-person gameplay/vehicles.
- **Respect corner anchors & stack cleanly:**
  - Top-left: clear `con_notify` lines (`y >= 34`, or `y >= 62` in `bm_hud_style 2`, `y >= 24` in `bm_hud_style 3`).
  - Top-right: stack via `bm_topright_y` (`BM_DrawHUD` / `HUD_DrawTopRightToys` -> `JBH_DrawStatusFeedback` / 1P telemetry) so alerts never overlap `BOTS:` or `[N] FLYING BLUE SHELL READY!`.
  - Bottom-left: anchor above `BM_CornerBottomY(h)` (`h - 56`, or `h - 72` in styles 2/3) and shift `x` to `36` when `JP_IsVisible()` is true so it clears the jetpack fuel tank.
  - Bottom-right: anchor above `BM_CornerBottomY(h)` (clearing `showfps` and styles 2/3 cards).
