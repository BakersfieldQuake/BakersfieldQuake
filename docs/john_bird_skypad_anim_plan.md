# Winged Breezy-Hair John — Expanded Animation & SkyPad Integration Spec

**Status:** Engineering specification (pre-vote; **no `.qc`, `progs.dat`, or `.pk3` files modified yet**)  
**Target files (post-vote):**
- `source/mm_tools/build_john_bird_head.py` (+ reproducible `zz_johnbird.pk3` packager)
- `source/qc_combat_decomp/john_bird_defs.qc`
- `source/qc_combat_decomp/john_bird.qc`
- `source/qc_combat_decomp/skypad.qc`

---

## 1. Frame Table: Current (`0..99`) vs. Proposed (`0..147`)

Existing clips (`0..99`) keep their exact frame indices so existing `progs/john_bird_head.md3` call sites remain backward-compatible. After the vote, the 3 winning 16-frame clips (`fast_fly`, `hit_flail`, `skypad_hyper`) are appended as frames `100..147` (148 frames total).

### Current Frame Table (`0..99` — 7 clips, 100 frames)

| Frames | Count | Clip Name | Purpose / Trigger |
|---|---:|---|---|
| `0..15` | 16 | `fly_breezy` | Normal cruising wingbeat (`780 u/s` base) + breezy hair |
| `16..31` | 16 | `windy_soar` | Outstretched thermal glide (`thr_in <= 0.05 && climb_in <= 0 && hspd > 340`) |
| `32..47` | 16 | `hover_flutter` | Hover scull / vigorous climb (`climb_in > 0.2 || hspd < 230`) |
| `48..59` | 12 | `swoop_dive` | Peregrine swoop / steep dive (`jb.velocity_z < -420` or boost/carve) |
| `60..71` | 12 | `perch_breeze` | Folded wings perched idle (`JB_IdleThink`) |
| `72..87` | 16 | `combat_fly` | Giant waving bangs combat flight (defined in model; `100..147` extend past it) |
| `88..99` | 12 | `combat_whip` | Mega-bangs pompadour whip-slap (`time < jb.jb_whip_until`, 0.50s) |

### Proposed Additions (`100..147` — 3 new 16-frame clips, 148 frames total)

| Frames | Count | Clip Name | Vote Category | Runtime Trigger Summary |
|---|---:|---|---|---|
| `100..115` | 16 | `fast_fly` | F1..F4 winner | High-speed flight (`hspd >= 950 u/s` via Shift boost or mouse-carve, when not in steep downward dive) |
| `116..131` | 16 | `hit_flail` | H1..H4 winner | Damage reaction (`JB_Pain` sets `jb_hurt_until = time + 0.65`) |
| `132..147` | 16 | `skypad_hyper` | S1..S4 winner | SkyPad supersonic arc (`jb_skypad_until > time || hspd >= 1500 u/s`) |

**Model Skins (`progs/john_bird_head.md3_*.skin`):**
- `skin 0`: `progs/john_bird_wings` (intact hawk plumage)
- `skin 1`: `progs/john_bird_wings_hurt` + `progs/john_bird_wings_hurt_glow` (scorched/ember wings; currently active at `health <= JB_LOW_HP` = 60, and used for brief hit-flash)
- `skin 2`: `progs/john_bird_wings_white`

---

## 2. Exact QuakeC Changes

Compile order in `source/qc_combat_decomp/progs.src`:
- `john_bird_defs.qc` (line 29)
- `john_bird.qc` (line 124)
- `skypad.qc` (line 139)

Because `skypad.qc` compiles **after** `john_bird.qc`, any `SkyPad_*` helper called from `john_bird.qc` must be forward-declared in `john_bird_defs.qc` (matching `mm_tank_defs.qc` lines 176–178). All `JB_*` / `JohnBird_*` symbols are already visible to `skypad.qc`.

### 2.1 `source/qc_combat_decomp/john_bird_defs.qc`

1. **Add speed, duration, and threshold constants:**
   ```qc
   float JB_SPEED_FAST_ANIM   = 950;   // u/s threshold for fast_fly (cruise=780, carve max=1220, swoop=1280)
   float JB_SPEED_HYPER_ANIM  = 1500;  // u/s threshold keeping skypad_hyper active
   float JB_HURT_ANIM_DUR     = 0.65;  // hit_flail override duration on JB_Pain
   float JB_HURT_SKIN_FLASH   = 0.18;  // brief skin=1 flash duration when health > JB_LOW_HP
   ```

2. **Add bird vehicle fields:**
   ```qc
   .float jb_hurt_until;         // hit_flail animation + erratic flap SFX expiry
   .float jb_hurt_skin_until;    // brief hurt-skin flash expiry (restores skin 0 if > JB_LOW_HP)
   .float jb_skypad_until;       // ballistic SkyPad arc expiry (preserves velocity without cruise/swoop clamp)
   .float jb_skypad_feather_t;   // continuous shedding john_bird_feather.md3 trail throttle
   .float jb_pad_scan_t;         // 20 Hz hull-overlap scan throttle for JB_CheckSkyPads
   ```
   *(Note: `.float skypad_cool_t` and `.float skypad_safe_t` are already declared in `bm_defs.qc` lines 310–311 and can be reused directly on both `jb` and `pilot`.)*

3. **Add SkyPad forward declarations (for `john_bird.qc` -> `skypad.qc`):**
   ```qc
   void() SkyPad_RaiseMaxVel;
   vector(vector org, vector dst, float apex_z) SkyPad_CalcVel;
   void(entity pad, entity jb) SkyPad_LaunchJohnBird;
   ```

4. **Update header frame table comment** to document `100..115` (`fast_fly`), `116..131` (`hit_flail`), and `132..147` (`skypad_hyper`).

---

### 2.2 Fast Flight (`fast_fly`, frames `100..115`) — `john_bird.qc`

**Speed Thresholds (existing vs. new):**
- Base cruise: `JB_SPEED_CRUISE = 780 u/s` (`fly_breezy`, `0..15`)
- Mouse-carve boost: up to `780 + 440 = 1220 u/s` (`JB_SPEED_CARVE_MAX = 440`)
- Shift (`+button4`) Peregrine boost: `JB_SPEED_SWOOP = 1280 u/s`
- **New `fast_fly` threshold:** `hspd >= JB_SPEED_FAST_ANIM` (`950 u/s`)

**Clip Selection & Interaction with `swoop_dive` (`john_bird.qc` `JB_UpdateAnimAndAudio`, lines 1660–1738):**
- Currently line 1677 triggers `swoop_dive` (`48..59`) whenever `swooping || jb.velocity_z < -420`, where line 1862 sets `swooping = (jb.jb_boosting || jb.jb_carve_spd >= 60 || vlen(jb.velocity) >= 1020)`.
- Update the clip branch so `fast_fly` handles high-speed level/climbing flight while `swoop_dive` remains reserved for steep downward dives (`jb.velocity_z < -420`):
  - If `jb.velocity_z < -420`: `swoop_dive` (`48..59`, 12 frames, `fps = 16`, `flap_gap = 0.52`, `flap_vol = 0.55`, `flap_pitch = 114`)
  - Else if `hspd >= JB_SPEED_FAST_ANIM` (`950 u/s`): `fast_fly` (`100..115`, 16 frames)
    - **Dynamic FPS:** `fps = 22 + bound(0, (hspd - 950) / 80, 10);` (`22..32` fps)
    - **Flap SFX cadence:** `flap_gap = bound(0.14, 0.24 - (hspd - 950) * 0.00018, 0.24);` (`0.14..0.24s`)
    - **Flap SFX volume / pitch:** `flap_vol = 0.92; flap_pitch = 108 + bound(0, (hspd - 950) * 0.025, 18);` (`108..126%`)

---

### 2.3 Hit / Disoriented (`hit_flail`, frames `116..131`) — `john_bird.qc`

**Trigger in `JB_Pain(entity attacker, float take)` (`john_bird.qc` lines 2278–2325):**
1. Set `self.jb_hurt_until = time + JB_HURT_ANIM_DUR;` (`time + 0.65`) unconditionally when `take > 0` (before the `jb_feather_t` early-return throttle at line 2284, so rapid multi-hit gunfire still refreshes the flail window).
2. **Brief hurt-skin flash:** Set `self.jb_hurt_skin_until = time + JB_HURT_SKIN_FLASH; self.skin = 1;` (`0.18s`). In `JB_UpdateAnimAndAudio` (and `JB_IdleThink`), keep `jb.skin = 1` while `jb.health <= JB_LOW_HP || time < jb.jb_hurt_skin_until`, restoring `jb.skin = 0` once expired and `jb.health > JB_LOW_HP`.
3. **Feather burst & SFX:** Existing `JB_SpawnFeathers(self.origin + '0 0 34', 8, 1.0)` (line 2293) and `sound(self, CHAN_AUTO, "john_bird/feather_hit.wav", 1, 0.55)` (line 2295) remain active.
4. **Optional light angular/velocity jolt & pilot punch:**
   ```qc
   self.angles_z = bound(-32, self.angles_z + crandom() * 24, 32);
   if (self.jb_pilot != world || self.jb_ai)
       self.velocity = self.velocity + '1 0 0' * (crandom() * 90) + '0 1 0' * (crandom() * 90) + '0 0 1' * (random() * 55);
   if (self.jb_pilot != world && self.jb_pilot.ishuman == 1)
   {
       self.jb_pilot.punchangle_x = crandom() * 4;
       self.jb_pilot.punchangle_z = crandom() * 6;
   }
   ```

**Animation & Rapid Multi-Directional Flap SFX (`JB_UpdateAnimAndAudio` + `JB_IdleThink`):**
- When `time < jb.jb_hurt_until`:
  - `clip_start = 116; clip_len = 16;` (`hit_flail`)
  - `fps = 28;` (frantic ~1.75 loops/sec)
  - `flap_gap = 0.11;` (~6 rapid flaps during the `0.65s` window)
  - `flap_vol = 0.95;`
  - `flap_pitch = 118 + crandom() * 18;` (wide erratic `100..136%` pitch jitter)
- In `JB_IdleThink` (for perched birds that survive a hit): if `time < self.jb_hurt_until`, drive frames `116 + idx` at `28 fps` and restore `self.skin` after `jb_hurt_skin_until`, instead of locking to `perch_breeze` (`60..71`).
- Reset `jb_hurt_until = 0` and `jb_hurt_skin_until = 0` in `JB_InitEntity`, `JB_Park`, `JB_Enter`, `JB_Leave`, and `JB_Respawn`.

---

### 2.4 Super Launch Pad (`info_skypad` + `skypad_hyper`, frames `132..147`) — `skypad.qc` & `john_bird.qc`

#### Why Both `SkyPad_Touch` AND Hull-Overlap (`JB_CheckSkyPads`) Are Required
- `SkyPad_Touch` (`skypad.qc` lines 92–126) currently rejects any entity with `other.classname != "player"` or `Veh_Driving(other)`.
- Furthermore, when Winged John is piloted (`JB_Enter` line 1512) or AI-controlled (`john_bird.qc` line 2676), `jb.movetype = MOVETYPE_NONE` and `JB_SlideMove` moves `jb` via `setorigin()` + `tracebox()`, while the pilot has `movetype = MOVETYPE_NONE` and `solid = SOLID_NOT`. In Quake/DarkPlaces, `setorigin()` does **not** run trigger-touch links, which is why `gokart.qc` (`GK_CheckPads`) and `mm_tank.qc` (`MMT_CheckPads`) both perform a 20 Hz AABB overlap scan against `info_skypad`.
- Therefore, implement a shared `SkyPad_LaunchJohnBird(entity pad, entity jb)` in `skypad.qc`, call it from **both**:
  1. `SkyPad_Touch` (when `other.classname == "misc_vehicle_johnbird"` or `other.classname == "player" && JohnBird_Flying(other)`), and
  2. `JB_CheckSkyPads(entity jb, entity pilot)` in `john_bird.qc` (called from `JohnBird_Frame` and `JB_AutopilotThink`).

#### Changes in `source/qc_combat_decomp/skypad.qc`
1. **Add `SkyPad_LaunchJohnBird(entity pad, entity jb)`:**
   ```qc
   void(entity pad, entity jb) SkyPad_LaunchJohnBird =
   {
       local entity pilot;
       local vector v;
       local float g, top, vz, tf;

       if (jb == world || jb.health <= 0 || jb.jb_dying)
           return;
       if (time < jb.skypad_cool_t)
           return;

       SkyPad_RaiseMaxVel ();
       pilot = jb.jb_pilot;
       if (pilot != world && pilot.ishuman == 1 && !pilot.skypad_vel_sent)
       {
           pilot.skypad_vel_sent = TRUE;
           stuffcmd (pilot, "sv_maxvelocity 6500\n");
       }

       jb.skypad_cool_t = time + 0.65;
       jb.flags = jb.flags - (jb.flags & FL_ONGROUND);
       setorigin (jb, jb.origin + '0 0 4');

       v = SkyPad_CalcVel (jb.origin, pad.pos1, pad.height);
       jb.velocity = v;

       // Match SkyPad_CalcVel flight duration so ballistic arc persists across sky
       g = cvar ("sv_gravity");
       if (g <= 10) g = 800;
       top = max (pad.height, max (jb.origin_z + 256, pad.pos1_z + 256));
       vz = sqrt (2 * g * (top - jb.origin_z));
       tf = (vz / g) + sqrt (2 * (top - pad.pos1_z) / g);
       jb.jb_skypad_until = time + bound (1.2, tf * 0.90, 3.8);
       jb.jb_swoop_until = time + 0.5;
       jb.jb_flap_t = time + 0.14;

       if (pilot != world)
           pilot.skypad_safe_t = time + 10.0;   // fall-safe if pilot dismounts mid-arc

       sound7 (jb, CHAN_AUTO, "skypad/launch.wav", 0.90, ATTN_NORM, SNDSPD * (0.96 + random () * 0.08));
       pointparticles (particleeffectnum ("TE_TELEPORT"), pad.origin + '0 0 12', '0 0 0', 1);
       JB_SpawnFeathers (jb.origin + '0 0 28', 10, 1.35);

       if (pad.message != "" && pilot != world && pilot.ishuman == 1)
           sprint (pilot, strcat ("Sky Pad -> ", pad.message, "\n"));
   };
   ```

2. **Update `SkyPad_Touch` (`skypad.qc` lines 92–126):**
   - Before rejecting `other.classname != "player"` or `Veh_Driving(other)`:
     ```qc
     if (other.classname == "misc_vehicle_johnbird")
     {
         SkyPad_LaunchJohnBird (self, other);
         return;
     }
     if (other.classname == "player" && JohnBird_Flying (other))
     {
         SkyPad_LaunchJohnBird (self, other.jb_vehicle);
         return;
     }
     ```
   - Keep existing player/foot launch path intact below that check.

#### Changes in `source/qc_combat_decomp/john_bird.qc`
1. **Add `JB_CheckSkyPads(entity jb, entity pilot)`:**
   - Early out if `!skypad_present || time < jb.skypad_cool_t || time < jb.jb_pad_scan_t`.
   - Throttle to 20 Hz: `jb.jb_pad_scan_t = time + 0.05;`.
   - Test AABB overlap of `jb.origin + '-30 -38 -6'` .. `jb.origin + '30 38 58'` against `find(world, classname, "info_skypad")` (`pad.absmin`..`pad.absmax`) and call `SkyPad_LaunchJohnBird(pad, jb)`.
   - Call `JB_CheckSkyPads(jb, self)` in `JohnBird_Frame` before velocity update, and `JB_CheckSkyPads(self, world)` in `JB_AutopilotThink`.

2. **Preserve Ballistic Momentum in `JohnBird_Frame` (lines 1870–1915):**
   - Currently `JohnBird_Frame` lerps `jb.velocity` toward `wish` (`max_spd = 780..1280`) and clamps `vlen(jb.velocity) <= max_spd`, which would immediately strip a `~4,000 u/s` SkyPad launch down to `1280 u/s` on frame 1.
   - Replace the velocity integration block when `time < jb.jb_skypad_until`:
     - Integrate gravity matching `SkyPad_CalcVel`:
       ```qc
       local float g, maxv;
       g = cvar ("sv_gravity");
       if (g <= 10) g = 800;
       jb.velocity_z = jb.velocity_z - g * dt;
       ```
     - Apply **light air-steering** instead of full velocity overwrite:
       ```qc
       jb.velocity = jb.velocity + (v_forward * (fwd_in * 420) + v_right * (str_in * 460) + '0 0 1' * (up_in * 240)) * dt;
       ```
     - **Do not clamp** to `JB_SPEED_CRUISE` (`780`) or `JB_SPEED_SWOOP` (`1280`); clamp only to `sv_maxvelocity` (6500 u/s).
     - After `JB_SlideMove(jb, self, dt)`: if `trace_fraction < 1 && trace_plane_normal_z > 0.7 && jb.velocity_z <= 0`, clear `jb.jb_skypad_until = 0;` so landing cleanly restores normal flight control immediately.
     - Camera pullback: pull `jb.jb_cam_pull` target up to `34` while `time < jb.jb_skypad_until || vlen(jb.velocity) >= JB_SPEED_HYPER_ANIM`.
   - Apply the same ballistic preservation check in `JB_AutopilotThink` (line 2187) when `time < self.jb_skypad_until` so AI birds launched off a SkyPad arc cleanly too.

3. **`skypad_hyper` Animation & Continuous Feather Trail (`JB_UpdateAnimAndAudio`):**
   - Priority order in `JB_UpdateAnimAndAudio`:
     1. `time < jb.jb_hurt_until` -> `hit_flail` (`116..131`)
     2. `time < jb.jb_skypad_until || hspd >= JB_SPEED_HYPER_ANIM` (`1500 u/s`) -> `skypad_hyper` (`132..147`)
     3. `time < jb.jb_whip_until` -> `combat_whip` (`88..99`)
     4. `jb.velocity_z < -420` -> `swoop_dive` (`48..59`)
     5. `hspd >= JB_SPEED_FAST_ANIM` (`950 u/s`) -> `fast_fly` (`100..115`)
     6. `climb_in > 0.2 || hspd < 230` -> `hover_flutter` (`32..47`)
     7. `thr_in <= 0.05 && climb_in <= 0 && hspd > 340` -> `windy_soar` (`16..31`)
     8. Default -> `fly_breezy` (`0..15`)
   - **`skypad_hyper` parameters:**
     - `clip_start = 132; clip_len = 16;`
     - `fps = 30 + bound(0, (hspd - 1500) / 180, 12);` (`30..42` fps)
     - `flap_gap = 0.13; flap_vol = 0.90; flap_pitch = 122 + bound(0, (hspd - 1500) * 0.008, 16);`
   - **Continuous shedding feather trail:**
     ```qc
     if ((time < jb.jb_skypad_until || hspd >= JB_SPEED_HYPER_ANIM) && time >= jb.jb_skypad_feather_t)
     {
         jb.jb_skypad_feather_t = time + 0.06;   // ~16 bursts/sec behind bird
         JB_SpawnFeathers (jb.origin + '0 0 28' - normalize (jb.velocity) * 18, 2, 0.85);
     }
     ```
   - Reset `jb_skypad_until = 0` and `jb_skypad_feather_t = 0` in `JB_InitEntity`, `JB_Park`, `JB_Leave`, and `JB_Respawn`.

---

## 3. Asset Audit (`.pk3` Locations) & Post-Vote Packaging Rules

Verified contents of `bakersfield.pk3` and `zz_johnbird.pk3` (and confirmed no stray loose copies exist in `progs/` or `sound/`):

| Asset | Current Location | Notes |
|---|---|---|
| `sound/skypad/launch.wav` | `bakersfield.pk3` | Already precached by `SkyPad_Precache` (`skypad.qc:39`) |
| `progs/john_bird_feather.md3` | `bakersfield.pk3` | Already precached by `JohnBird_Precache` (`john_bird.qc:31`) |
| `progs/john_bird_wings_hurt.png` (+ `_glow.png`) | `bakersfield.pk3` | Used by `skin 1` (`progs/john_bird_head.md3_1.skin`) + `scripts/john_bird.shader` |
| `sound/john_bird/flap1..4.wav`, `feather_hit.wav`, `swoop.wav`, `takeoff.wav`, `shootdown.wav`, `jv_fly00..13.wav`, `jv_hurt.wav` | `bakersfield.pk3` | Base flight/hit/voice SFX; already precached in `john_bird.qc` |
| `sound/john_bird/jb_*.wav` (8 combat SFX) | `zz_johnbird.pk3` | Combat overlay SFX |
| `progs/john_bird_head.md3` | `zz_johnbird.pk3` (overrides `bakersfield.pk3`) | Overlay model; currently 100 frames, will be 148 frames post-vote |

### Post-Vote `AGENTS.md` Packaging Checklist
1. **Never edit `bakersfield.pk3` or `q15.pk3`** (forces ~450 MB re-download via the differential updater).
2. **Ship the updated 148-frame `progs/john_bird_head.md3` inside `zz_johnbird.pk3`** (sorted filename order means `zz_johnbird.pk3` cleanly overrides `bakersfield.pk3`). Do **not** leave a loose `progs/john_bird_head.md3` on disk.
3. **Keep `progs.dat` as a loose file** (diffs cleanly through the updater).
4. **Reproducible CI build:** Create a deterministic builder script under `source/mm_tools/` that builds `zz_johnbird.pk3` with `zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))`, fixed `external_attr`, sorted entries, `ZIP_STORED` for `.png`/`.wav` and `ZIP_DEFLATED` for `.md3`, no unseeded randomness, and add a cached step in `.github/workflows/build-zip.yml` (modeled on `zz_bakovan.pk3` / `zz_karts.pk3`) pinning `numpy`/`pillow`/`scipy` and hashing all read inputs. Verify determinism by building twice and comparing SHA-256.
