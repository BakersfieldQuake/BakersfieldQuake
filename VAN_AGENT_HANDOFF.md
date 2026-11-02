# AI Agent Handoff — ProMaster / Ducato L2H2 Walk-In Cargo Van Assets

**Workspace Root:** `G:\Quake\Combat\BakersfieldQuake`  
**Engine / Target:** Quake / DarkPlaces (`Combat+` mod, compiled with `fteqcc64.exe`)  
**Vehicle Identity:** X290 Facelift Fiat Ducato / Ram ProMaster L2H2 High-Roof Cargo Van (`VEH_VAN = 3`, Left-Hand Drive, 50/50 split rear barn doors open `126°`, full walk-in cargo bay & cockpit).

---

## 1. Runtime Quake / DarkPlaces Assets (Installed & Ready)

### 3D Models & Skins (`progs/`)
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van.md3` — Main intact & burning animated van (`36` frames: `0..15` engine idle, `16..21` hit flinch, `22..35` hood-ajar fire rattle). Split into 5 MD3 surfaces to stay cleanly under the 4096-vertex MD3 surface limit:
  - `body_a`, `body_b` (chassis + full walk-in interior + cockpit)
  - `interior` (hood, cab doors, open 126° rear barn doors, front/rear bumpers, steering/detail)
  - `wheels` (4× commercial 16" steelie wheels)
  - `glass` (translucent laminated green-tint cab glass + square wire-mesh bulkhead screen)
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van.md3_0.skin` — Intact skin (`progs/veh_van_tex` + `progs/veh_van_glass`)
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van.md3_1.skin` — Scorched/fire skin (`progs/veh_van_burn` + `progs/veh_van_glass_burn`)
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_wreck.md3` — 20-frame post-explosion leaping/crumpled charred chassis hulk
- **Detached Physics Debris MD3s** (spawned on explosion or reusable as articulated sub-entities for driving):
  - `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_wheel.md3` (16-frame spinning 16" steelie tire/rim)
  - `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_door.md3` (cab door + twin-arm mirror)
  - `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_hood.md3` (front service hood)
  - `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_bumper.md3` (front bull-nose bumper)
  - `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_extra.md3` (50/50 rear barn doors)

### Textures, Shaders, Audio & Map
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_tex.png` — 2048×2048 intact texture atlas (0.60× DarkPlaces diffuse gain)
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_tex_glow.png` — 2048×2048 additive emissive headlight/marker/taillight glow map
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_burn.png` & `veh_van_burn_glow.png` — 2048×2048 scorched/ember maps
- `G:\Quake\Combat\BakersfieldQuake\progs\veh_van_glass.png` & `veh_van_glass_burn.png` — 512×512 RGBA cab glass (`u: 0..0.5`) & steel wire-mesh bulkhead (`u: 0.5..1.0`)
- `G:\Quake\Combat\BakersfieldQuake\scripts\vehicles.shader` — Defines `progs/veh_van_tex`, `progs/veh_van_burn`, `progs/veh_van_glass` (`blendfunc blend`), and `progs/veh_van_glass_burn`
- `G:\Quake\Combat\BakersfieldQuake\sound\vehicles\idle_van.wav` — Diesel idle audio loop
- `G:\Quake\Combat\BakersfieldQuake\progs.dat` — Compiled QuakeC bytecode with walk-in van & vehicle system installed
- `G:\Quake\Combat\BakersfieldQuake\maps\vehtest.bsp` — Test parking-lot map with vehicles spawned

### Standalone GLB & Interactive 3D Viewer
- `G:\Quake\Combat\BakersfieldQuake\veh_van.glb` — Rigged 25-node glTF 2.0 binary (`Idle`, `CatchFire`, and `Explode` clips + `BLEND` glass material)
- `G:\Quake\Combat\BakersfieldQuake\van_3d_viewer.html` — Self-contained WebGL2 studio viewer (includes reference camera presets, `0..180°` barn-door / cab-door / hood / steering rig, Quake `32×32×56` FPS walk-in mode, test-drive mode, CAD cutaway, and 13-hull Quake collision visualizer)

---

## 2. Source-of-Truth Generators (`source/mm_tools/`)

> **IMPORTANT — Authoritative vs. Deprecated Files:**  
> Always edit the files in `source/mm_tools/` listed below. **Ignore** legacy prototype files in `G:\Quake\Combat\BakersfieldQuake\source\van_walkin\*`, `progs\van_walkin.md3`, `maps\vanwalkin*.bsp`, and `source\mm_tools\build_promaster_van.py` (those were superseded early prototypes).

1. **Parametric 3D Sculpted Mesh & Articulation Rig:**  
   `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\promaster_van_mesh.py`
   - Entry point: `build_promaster_van_data(barn_open_deg=126.0)`
   - Produces `10,147` vertices / `7,114` triangles across 24 standard vehicle parts (`chassis`, `hood`, `door_l`, `door_r`, `bumper_f`, `bumper_r`, `detail_vib`, `extra_part`, `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr`, `wreck_chassis`, `shrap_0..9`), plus `"glass_cab"` and `"viewer_rig"` (`barn_door_l_closed`, `barn_door_r_closed` with exact hinge pivots).
2. **2048×2048 Studio Atlas & 512×512 RGBA Glass/Mesh Generator:**  
   `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\promaster_van_tex.py`
   - Entry point: `build_promaster_van_textures()`
   - Full-brightness 2K studio PNGs are also saved at `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\out\vehicles\veh_van_atlas_2k.png` and `veh_van_glass.png`.
3. **Vehicle JSON Assembler:**  
   `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\blender_build_vehicles.py`
   - `build_single_vehicle("van")` delegates directly to `promaster_van_mesh.build_promaster_van_data(barn_open_deg=126.0)` and writes `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\out\vehicles_parts.json`.
4. **MD3 / Skin / Shader / GLB / Physics Asset Builder:**  
   `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\build_vehicles_assets.py` (uses `veh_textures.py` and `veh_physics_sim.py`).
5. **Standalone WebGL2 HTML Viewer Builder:**  
   `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\build_van_viewer_html.py` -> outputs `van_3d_viewer.html`.

---

## 3. QuakeC Implementation & Drivable Vehicle Foundation

Edit QuakeC in `source/mm_tools/` (NOT `source/qc_combat_decomp/` directly, as `build_combat.py` copies from `source/mm_tools/` into `source/qc_combat_decomp/` before compiling):

- **Entity Fields & Constants:** `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\vehicles_defs.qc`
  - `VEH_VAN = 3`
  - `.entity veh_clip_head;` — linked list of the 13 child walk-in collision/trigger entities (`c.enemy` chain, `c.owner = v`)
  - `.entity veh_driver;` — player entity currently in the cockpit
  - `.float veh_drive_mode;` — reserved flag for active driving state
- **Spawning, Walk-In Collision & Damage Logic:** `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\vehicles.qc`
  - **Map / Dynamic Spawn:** `misc_vehicle_van` (line 1166), `Veh_SpawnDynamic(VEH_VAN, org, yaw_deg)` (line 1218), or in-game test **`impulse 83`** (spawns van ahead of player; `impulse 85` spawns all 4 vehicles).
  - **13-Box Composite Walk-In Architecture:** `Veh_Van_InitCollision(entity v)` (lines 360–415) & `Veh_Van_AddBox` (lines 302–358):
    1. Rear walk-in step bumper: `x: -114..-108, y: -33..33, z: 0..16.5` (`<= 18u` Quake step height)
    2. Main corrugated cargo & cab floor: `x: -108..68, y: -39..39, z: 0..19.5` (`+3.0u` step from bumper)
    3. Left outer wall: `x: -108..68, y: 38..43, z: 19.5..101`
    4. Right outer wall: `x: -108..68, y: -43..-38, z: 19.5..101` (`76u` interior width)
    5. Open 126° left barn door: `x: -128..-108, y: 34..56, z: 19.5..97`
    6. Open 126° right barn door: `x: -128..-108, y: -56..-34, z: 19.5..97` (`66u` clear rear doorway `y: -33..33`)
    7. Crowned H2 roof & ceiling bows: `x: -108..48, y: -40..40, z: 96.5..103.5` (`77u` standing headroom)
    8. Front dash, cowl, hood & nose: `x: 68..113, y: -43..43, z: 0..52`
    9. Left cargo wheel arch: `x: -85..-51, y: 29..39, z: 19.5..38.5`
    10. Right cargo wheel arch: `x: -85..-51, y: -39..-29, z: 19.5..38.5` (`58u` clear aisle between arches)
    11. Left bulkhead wing & driver seat base: `x: 30..36, y: 17.5..39, z: 19.5..82`
    12. Right bulkhead wing & passenger seat base: `x: 30..36, y: -39..-17.5, z: 19.5..82` (`35u` central walkthrough aisle `y: -17.5..17.5` for `32×32×56` player)
    13. Cockpit driver interaction trigger (`SOLID_TRIGGER`, `Veh_CockpitTouch`): `x: 36..66, y: -16..34, z: 19.5..76` — shows the "Press H to drive" prompt (the driver is set by `Veh_Enter` in `vehicle_drive.qc`, see section 3b).
    - **Root Entity BBox Note:** `v` uses `setsize(v, '-16 -16 0', '16 16 19.5')` so the root AABB stays underneath the `z = 19.5` cargo floor at any yaw angle and never blocks players inside the cargo bay.

---

## 3b. DRIVING THE VAN (implemented)

Walk into the cab (behind the bulkhead), you get **"Press H to drive"**; **H** (`impulse 86`) sits you in the seat. The mouse is
ignored while driving (the server owns the view); the keys are the normal move/jump/fire keys:

| Key | Does |
|---|---|
| W / S | throttle / brake, then reverse once stopped (W while rolling backward brakes first) |
| A / D | steer. Eased toward the key like a keyboard racer; less wheel lock the faster you go |
| SPACE | handbrake: locks the rears, tail swings out (steer + SPACE = a slide) |
| FIRE | horn |
| K (`impulse 87`) | cockpit view / chase view |
| H | get out (needs <= 140 u/s, or <= 260 while burning) |

Files (all edited in `source/mm_tools/`, built by `build_combat.py`):
- `vehicle_drive.qc` (new): the whole system. `Veh_DriveFrame` is called for the driver every client frame from `W_WeaponFrame`.
- `vehicles.qc`: cockpit trigger now only shows the prompt (`Veh_CockpitTouch`); explosion throws the driver out (`Veh_DriverBail`);
  `Veh_Think` calls `Veh_DriveWatch` (driver died/dropped); impulses 86..90; **child collision boxes now have `health 1000000` +
  `th_die = SUB_Null`** (they used to have health 0 and no `th_die`, so any rocket splash or ramming van reached `Killed()` and crashed the server).
- `vehicles_defs.qc`: fields, prototypes, `autocvar_veh_debug`.
- `patch_vehicle_drive_combat.py`: hooks in game code (`weapons.qc` W_WeaponFrame, `custom_effects.qc` gun helper hides the gun, `client.qc`
  run-over obituary + `ClientDisconnect`, `progs.src`, `build_combat.py`). Marker-guarded; run it after `patch_vehicles_combat.py`.
- `build_vehicles_assets.py`: also writes `progs/veh_van.md3_2.skin` / `_3.skin` + the `progs/veh_van_nodraw` shader (see gotchas).
- `make_vehicle_drive_sounds.py`: `engine_grain.wav`, `tire_squeal.wav`, `horn.wav`, `ignition.wav` (needs numpy).
- `default.cfg`: `bind h "impulse 86"`, `bind k "impulse 87"`.

Model of the physics (all constants at the top of `vehicle_drive.qc`, `VD_*`): speed kept as forward + sideways parts of the van's own
heading; tyres take out sideways speed up to `VD_GRIP` (less with the handbrake / hard braking); turn rate = bicycle model
`speed * tan(wheel angle) / wheelbase`, capped by the grip (so too fast into a corner = understeer). Collision = 20 small hulls swept round the
real rotated footprint (an entity box is axis aligned); a blocked hull slides along the wall and the lost speed is the crash (damage to van and
driver, sparks). Ramming people/monsters/vehicles hurts them by speed ("X was run over by Y's van"). Four wheel traces give pitch and let it
drop off ledges and jump. While driven the van is ONE box inscribed in its real footprint (so nobody is trapped beside it); parked within 7
degrees of square to the world it gets its walk-in interior back (`Veh_Park`), otherwise it stays a plain box.

**Not done / ideas:** the wheels and steering wheel are baked into the MD3 (no spin / steer animation; would need a `veh_van` variant without the
`wheels` surface plus 4 `veh_van_wheel.md3` sub-entities); no mouse look; no speedometer (no HUD hook); parked cars at odd yaws have big
axis-aligned boxes that block lanes.

**Testing:** `zz_drive_test.cfg` is a scripted smoke test (launch line in its header; follow `CLAUDE.md`). `set veh_debug 1` + `developer 1` logs
speed / heading / steering / revs / what blocked the van 4x a second. Test aids (need `sv_cheats 1`): `impulse 88` running van + you in it,
`impulse 89` into the nearest van's cab, `impulse 90` a sedan 700 ahead to ram. `setpos` does not exist in this engine build.

**Gotchas that cost hours (don't relearn them):**
1. The camera entity (`clientcamera`) must be networked, so it needs a model, and a sprite model at the eye fills the screen. It is the
   `progs/s_bubble.spr` sprite shrunk with `scale 0.01`. `EF_NODRAW` on it is WRONG: the client then looks out from the map origin.
2. From INSIDE the cab, `body_a` (the outer shell surface of `veh_van.md3`) paints the whole view flat grey (cause not found; isolated by hiding
   surfaces with skins). So the driver in cockpit view is sent skin 2/3 (`body_a` -> `progs/veh_van_nodraw`) by `customizeentityforclient`
   (`Veh_VanCustomize`); everyone else gets skin 0/1. **A `customizeentityforclient` function must be `float()` and `return TRUE`**, otherwise the
   engine does not send the entity at all.
3. The gun on screen is drawn by a helper entity (`custom_effects.qc` ~2440), not by `weaponmodel`: blanking `weaponmodel` does nothing. It hides
   itself on `FD_Flying(owner)`; it now also checks `Veh_Driving(owner)`. (Do NOT hide it with the client's `r_drawviewmodel`: it is saved in config.cfg.)
4. `fixangle` every frame is fine for a server-owned view, but reading `v_angle` back to add the van's turn to the view lags by the round trip.
5. `sin` / `cos` / `tan` / `atan2` / `sqrt` are untyped builtins: use them only through float locals (see `Veh_Sin`, `Veh_Cos`, `Veh_Tan`).
6. `screenshot <name>` needs an extension (`.png`); test lanes: the map is 2880 wide, parked cars' boxes are big.

---

## 4. Coordinate System & Key Mechanical Pivots (For Driving Rig)

All mesh coordinates in `VAN_SPEC` (`promaster_van_mesh.py`) are in **Quake units** (`+X` forward, `+Y` left/driver side, `+Z` up, `z = 0` ground contact):

- **Exterior Bounds:** `x: -114.0 .. +112.5` (`226.5u`), `y: -43.0 .. +43.0` (`86.0u`), `z: 0.0 .. +103.5`
- **Front Axle Wheels (`wheel_fl`, `wheel_fr`):** `(80.0, ±38.5, 15.2)`, tire radius `15.2u`, width `9.6u`
- **Rear Axle Wheels (`wheel_rl`, `wheel_rr`):** `(-68.0, ±38.5, 15.2)`, wheelbase `148.0u`
- **Driver Eye / Camera Seat Anchor (LHD):** `(40.0 .. 44.5, +19.8, 62.5 .. 65.8)`
- **3D Steering Wheel Center & Axis:** `sw_c = (62.2, +20.6, 49.8)`, axis `(-cos 28°, 0, sin 28°)`
- **Cab Door Hinges (`door_l`, `door_r`):** `(81.0, ±42.5, 34.0)` around `+Z`
- **Rear Barn Door Hinges:** `(-108.6, ±34.8, 55.0)` around `+Z`
- **Front Hood Hinge:** `(84.5, 0.0, 50.7)` around `+Y`

> **Note on Part Origins in `vehicles_parts.json`:** Each part stores `"verts"` relative to `part["origin"]`. World-space Quake vertex position is `v_world = vert + origin`.

---

## 5. Rebuild Commands

Run from `G:\Quake\Combat\BakersfieldQuake`:

```powershell
# 1. Regenerate van geometry in source/mm_tools/out/vehicles_parts.json (if promaster_van_mesh.py changed):
python3.13 -c "import sys, json; sys.path.insert(0, 'source/mm_tools'); import promaster_van_mesh; p='source/mm_tools/out/vehicles_parts.json'; d=json.load(open(p)); d['van']=promaster_van_mesh.build_promaster_van_data(126.0); json.dump(d, open(p,'w'))"

# 2. Rebuild DarkPlaces MD3s, 2K textures, skins, scripts/vehicles.shader, and veh_van.glb:
python3.13 "source/mm_tools/build_vehicles_assets.py"

# 3. Rebuild standalone WebGL2 studio viewer (van_3d_viewer.html):
python3.13 "source/mm_tools/build_van_viewer_html.py"

# 4. Compile QuakeC (copies source/mm_tools/*.qc -> source/qc_combat_decomp/ and installs progs.dat):
python3.13 "source/mm_tools/build_combat.py"
```

---

## 3c. Windshield removed (2026-10-31)

The front windshield glass is gone from `progs/veh_van.md3` (`source/mm_tools/van_windshield.py` drops the windshield triangles from the `glass`
surface; the side windows and the wire-mesh screen stay). `build_vehicles_assets.py` calls it after writing the van, so a rebuild keeps it out.
The un-stripped model is in `source/mm_tools/out/van_model_backup/veh_van.md3.with_windshield`. `promaster_van_mesh.py` still builds the
windshield (so the GLB / `van_3d_viewer.html` still show it).

Two more DarkPlaces facts learned doing this (they were the real cause of the cockpit haze, not the glass):
- `rgbGen const` and `alphaGen const` are ignored: the "nodraw" shader must be `blendfunc GL_ZERO GL_ONE` (draws nothing). The old one painted the shell
  round the cab over the whole view.
- A sprite as the camera entity washes the view with its colour whatever its `.scale`; the camera is now `progs/spike.mdl` at scale 0.01.
  The driver's body is also `EF_NODRAW` while he drives.
