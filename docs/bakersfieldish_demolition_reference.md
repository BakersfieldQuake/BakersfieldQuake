# Bakersfield-ish — Real-World Demolition Visual Reference & Quantitative Critic Benchmarks

> **Purpose:** Authoritative visual, kinematic, and perceptual benchmark specification for **Bakersfield-ish** (`maps/bakersfieldish.bsp`) destructible landmarks — **The Padre Hotel**, **Historic Fox Theater**, **The Bakersfield Sign**, and **Shatterable Glass Bays**.  
> **Audience:** Fresh-context Demolition Critics evaluating captured 720p MP4s & keyframe contact sheets from `source/mm_tools/bakersfieldish_capture.py`, plus QC/map tuning passes.  
> **Coordinate Scale:** `12 Quake units (u) = 1 real-world foot (ft)` (`~39.37 u/m`), matching `bakersfieldish.bsp`.

---

## 1. Real-World Reference Footage Analysis

Our destruction targets map directly onto three distinct real-world structural demolition regimes. Real footage establishes the non-negotiable physical signatures that separate believable weight from "video-game sliding boxes."

### 1.1 Controlled High-Rise Implosions → **The Padre Hotel** (`8 stories, 122.3 ft / 1,468 u`)

| Real Demolition Case | Structure & Charges | Total Collapse Duration | Signature Visual Mechanics |
|---|---|---|---|
| **Tropicana Las Vegas** *(Oct 9, 2024)* | Twin concrete/steel hotel towers (Paradise & Club Towers), ~2,200 lbs explosives across 220 cut-points | **~22 s** (twin staggered sequence; ~11–13 s per tower) | Crisp rhythmic lower-column charge pops → brief "hang/hesitation" → staggered vertical pancake with lateral V-fold → rolling ground-hugging base-surge dust sweeping outward across the Strip footprint. |
| **Trump Plaza, Atlantic City** *(Feb 17, 2021, CDI)* | 34–39 story reinforced concrete hotel/casino, ~1,900 lbs / 3,000–3,800 sticks across 14 lower floors (>700 micro-delays) | **~19.5 s** structural pacification (initial drop acceleration visibly ramps over first 2.5–3.5 s) | Sequential rhythmic `"pop-pop-pop"` blasts marching across lower bays with bright flash-puffs → upper stories fold **inward** toward the core (preventing timber-fall into neighbors) → heavy grey floor-seam dust jets followed by an expansive boardwalk base surge. |
| **The Landmark Hotel, Las Vegas** *(Nov 7, 1995, CDI)* | 31-story reinforced concrete tower, <100 lbs focused in lower 4 structural floors | **~17 s** total concrete descent | Lower core shears first, pulling the upper mass slightly inward/forward into its target drop zone → violent concrete-on-concrete crushing launches a **~150 ft high** dense plume and a rapid radial base surge across Paradise Rd. |

**Scaling Physics to an 8-Story Concrete/Masonry Hotel (Padre Hotel, `H = 122.3 ft / 37.3 m`):**
- Pure vacuum free-fall for `H = 37.3 m` is $t_{\text{ff}} = \sqrt{2H/g} \approx 2.76\text{ s}$.
- Real progressive structural collapse incurs continuous crushing resistance, buckling delay, and staggered floor-by-floor initiation, stretching fall duration by **3.2×–4.5×** free-fall (`~9–12.5 s` including `~2.0–2.2 s` pre-collapse charge pops and initial buckling hesitation).
- **Critical visual signature:** A high-rise NEVER moves downward at constant linear speed (`z(t) = z_0 - v t`). It **hesitates**, shudders as lower floors pop, begins sinking slowly while upper wings tilt slightly inward (V-collapse), then **accelerates** (`u^2.0 .. u^2.4`) as lower resistance gives way, culminating in massive ground impact, billowing radial base surge, and ejecting street boulders.

### 1.2 Masonry Theater & Slender Clock Tower Topples → **Historic Fox Theater** (`116.5 ft / 1,398 u` tower + auditorium)

Real-world demolitions of historic unreinforced masonry (URM) theaters, brick bell towers, and tall chimneys show two distinct mechanics:
1. **Base Plastic-Hinge Cantilever Topple:** Unlike steel-framed skyscrapers imploded vertically, brick/stucco towers fail in eccentric compression once a basal wedge is blown out. The tower acts as a rigid lever rotating around a base hinge with angular acceleration governed by a falling rod:
   $$\alpha(\theta) = \frac{3g}{2L}\sin(\theta)$$
   - At small initial angles (`0°–12°`), $\sin\theta$ is tiny → **agonizingly slow, suspenseful initial lean** (`~2.0–2.5 s` just to tilt the first `15°`).
   - Past `25°–30°`, angular velocity snowballs dramatically → the last `50°` of rotation slams down in `< 1.8 s`!
2. **Mid-Span Tensile Fracture (The Masonry Topple Paradox):** Because masonry has near-zero tensile strength, a slender 116-ft tower rotating past `~25°–35°` snaps horizontally near mid-height (`tower_upper` shears ahead/steeper than `tower_lower`). Secondary attached volumes (wrap-around **marquee**, **east/south facades**, **auditorium roof**, **stagehouse**) peel and collapse in a staggered cascade `0.8–2.5 s` behind the clock tower as roof trusses lose support.

### 1.3 Steel Truss / Stucco Street Arch Falls → **The Bakersfield Sign** (`31 ft / 372 u` tall × `80–97 ft` span)

Real collapses of steel-truss highway sign gantries, arched street gateways, and bridge portals show:
1. **Pier Shear & Hinge Acceleration:** Severing the slender lower corner piers (`Plane A`, `Z ≈ 5 ft`) leaves ruined masonry stumps on both curbs while the `26 ft` (`312 u`) tall upper arch & twin tower crowns tip forward/south along H Street around the street-parallel base axis (`roll: 0° → ±88°`).
2. **High-Elasticity Ground Bounce / Recoil:** Unlike friable concrete, a steel-clad truss arch converts impact kinetic energy into elastic strain energy upon hitting asphalt, producing a distinct **visible structural bounce** (`88° → ~80°–82° → 88°` over `0.45–0.65 s`) accompanied by a shower of **neon/electrical sparks**, shattering bulb glass, and a localized street-hugging dust puff.
3. **Final Resting Silhouette:** The fallen arch lies across H Street as a recognizable, low-profile, **go-kart-rampable & climbable** wreckage (`bako_sign_rubble`) with the yellow `BAKERSFIELD` lettering still legible in the ruins.

---

## 2. Quantitative Collapse Pacing Curves

All demolition sequences must follow **non-linear gravitational acceleration curves** — never constant-velocity linear tweens. Let $u \in [0, 1]$ be normalized time within a piece's active fall window (`bako_delay` to `bako_delay + bako_dur`):

- **Recommended Gravity Drop Curve:** $f_{\text{drop}}(u) = 0.15 u + 0.85 u^{2.3}$ (or $u^{2.2}$ after an initial $0.12$ shudder offset)
- **Recommended Hinge Topple Curve:** $f_{\text{hinge}}(u) = u^{2.4}$ (slow ominous lean in first 40% of duration, whipping acceleration into impact)
- **Recommended Elastic Bounce Tail (Sign / Steel):** For $u \in [0.84, 1.0]$ after primary slam at $u = 0.84$:
  $$\theta(u) = \theta_{\max} - A_{\text{bounce}} \left|\sin\!\left(\pi \frac{u - 0.84}{0.16}\right)\right| e^{-2.2 (u - 0.84)/0.16}, \quad A_{\text{bounce}} \approx 6^\circ\text{–}9^\circ$$

### 2.1 Padre Hotel — Target Timeline (`11.0–13.0 s` Controlled Inward Implosion)

| Phase | Time Window (`t`) | Structural Motion | FX, Debris & Audio | Critic Visual Benchmark |
|---|---|---|---|---|
| **Damage Milestones** *(Pre-Collapse Gameplay)* | `75%`, `50%`, `25%` HP (`2600 HP` pool) | Structure remains intact & solid | Dust puffs at impact, cracking masonry SFX, window glass bursts, escalating floor smoke vents, subtle top-right corner text status | Clear progressive wear — players immediately see/hear the hotel weakening under rockets, gunfire, or Eric Cannon hits. |
| **P0: Pre-Collapse Charge Pops** | `0.0 – 2.2 s` | Base shudder (`±2–4 u` micro-jitter); zero major sink yet | 6–9 rhythmic `"pop-pop-pop"` lower-floor charges (`bako_charge_pop` bright flash + smoke puff marching around 1F–3F), glass shattering | Distinct sequential detonation cadence visible along lower floors before gravity takes over — mirrors Trump Plaza / Tropicana. |
| **P1: Initial Sink & Inward Buckling** | `2.2 – 4.5 s` | `tier1` (1–2F) begins slow downward crush (`0 → 18%` drop); `west_wing` & `east_wing` begin subtle **inward tilt** (`3°–8°` toward core) | Continuous vertical dust curtains pouring from floor seams (`bako_collapse_plume`); early brick/plaster chunks (`bako_masonry_burst`) | Unmistakable "breath/hang" of enormous mass beginning to fail inward — NOT instant teleporting drop. |
| **P2: Accelerating Multi-Tier V-Collapse** | `4.5 – 9.0 s` | Staggered pancaking: `tier1 → tier2 → tier3 → tier4 → crown` accelerate downward (`u^2.2`), upper tiers pitching/rolling inward `10°–22°` | Dense layered piston dust jets shooting out every floor seam; 3 waves of `MOVETYPE_BOUNCE` tumbling boulders (`20–24` total) erupting radially onto H St, 18th St, and toward Parking Garage; staggered `DN3FX_OnExplode` bursts | Every tier clearly descends in staggered succession (not as a single monolithic cube); upper roof sign/crown stays readable as it rides the collapse down! |
| **P3: Primary Impact & Base Surge** | `9.0 – 11.5 s` | Final upper mass & `crown` slam into rubble footprint; intact submodels hide *inside* the dense dust cover as `bako_padre_rubble` rises (`0.6 s` sweep) | Massive ground-hugging **`bako_demolition_dust_surge`** billowing outward across H St & 18th St; peak clamped earthquake pulse; rolling boulders bouncing down both streets | **Zero naked "pop-swap"** — swap from falling tiers to `bako_padre_rubble` is veiled cleanly inside the surge; sky & surrounding Garage remain legible. |
| **P4: Secondary Settling & Aftermath** | `11.5 – 19.0 s` *(Rubble stays `120 s`)* | `bako_padre_rubble` solid (`SOLID_BSP`), overlapping players safely lifted on top | Dust slowly rises thermally and thins out over `7–10 s`; final boulders tumble to a stop (`12–16 s`); climbable 2-story rubble silhouette revealed | Players can immediately walk/drive up onto the 2-story concrete mountain; zero pitch-black baked shadow holes; zero map void leaks. |

### 2.2 Historic Fox Theater — Target Timeline (`8.0–9.0 s` Collapse + `~25 s` Staged Rebuild)

| Phase | Time Window (`t`) | Structural Motion | FX, Debris & Audio | Critic Visual Benchmark |
|---|---|---|---|---|
| **P0: Clock Trigger & Crown Blast** | `0.0 – 1.2 s` | `bako_fox_clock` (`200 HP`) shatters on weapon hit; `tower_upper` shudders and leans `0° → 8°` | Clock face explosion, glass & bronze sparks, chime/boom SFX, masonry chips (`bako_masonry_burst`) | Shooting the clock face directly triggers the chain reaction cleanly with immediate visual/audio payoff. |
| **P1: Slow Tower Lean & Mid-Height Shear** | `1.2 – 4.0 s` | `tower_upper` tilts `8° → 42°` (`u^2.4`), shearing ahead of `tower_lower` (`0° → 24°`); `marquee` begins peeling & dropping (`t ≈ 2.2 s`) | Plumes pouring from tower joints (`bako_collapse_plume`), flying brick/stucco chunks & sparks | Classic brittle masonry topple: slow menacing tilt transitioning into visible mid-shaft separation. |
| **P2: Tower Crash & Auditorium Collapse** | `4.0 – 7.2 s` | `tower_upper` + `tower_lower` whip down to `~78°–86°` impact onto H St/20th corner; `facade_e`, `facade_s`, `auditorium_roof`, `stagehouse` drop staggered (`t = 3.2–7.2 s`) | Peak impact blast (`DN3FX_OnExplode`), outward flying `MOVETYPE_BOUNCE` debris chunks, radial **`bako_demolition_dust_surge`**, clamped earthquake | Multi-stage cascade reads clearly from street or Parking Garage; marquee & tower feel distinct from the auditorium hall. |
| **P3: Rubble Reveal & Lingering Dust** | `7.2 – 14.0 s` *(Rubble stays `150 s`)* | `bako_fox_rubble` swaps cleanly under dust veil (`SOLID_BSP`, safe player lift) | Translucent dust curls rise and clear over `6–9 s` | Climbable broken-marquee/masonry mound with static floor underneath (zero void holes!). |
| **P4: Slow Staged Rebuild** *(after `150 s` or `bako_cmd fast_rebuild_fox`)* | `0.0 – 25.0 s` *(rebuild clock)* | `0–3.5 s`: rubble sinks smoothly underground. `3.5–11 s`: `stagehouse` & `auditorium_roof` rise. `11–18 s`: `facade_s`, `facade_e`, `marquee` ascend & lock. `18–25 s`: `tower_lower → tower_upper → clock` rise & right themselves (`Bako_NudgePlayersClear` keeps players safe) | Golden welding sparks (`bako_rebuild_weld`), steel clanks, gentle rising dust puffs, completion chime | Smooth, magical-industrial reconstruction — every tier locks seamlessly back into its exact original intact alignment & becomes shootable again! |

### 2.3 The Bakersfield Sign — Target Timeline (`4.0–4.8 s` Arch Topple + Bounce)

| Phase | Time Window (`t`) | Structural Motion | FX, Debris & Audio | Critic Visual Benchmark |
|---|---|---|---|---|
| **P0: Pier Fracture & Neon Short** | `0.0 – 0.7 s` | Ruined pier stumps (`Z ≤ 5 ft`) remain static on both sidewalks; upper sign shudders & cracks free (`0° → 5°`) | Base pylon charge/blast bursts + bright blue-gold **`bako_sign_sparks`** + glass bulb shatter | Clear fracture at Plane A (`Z ≈ 5 ft`); neon arc sparks sell an electrified landmark sign. |
| **P1: Hinge Topple Acceleration** | `0.7 – 3.3 s` | `bako_sign_piece` pivots around street-parallel base axis (`roll: 5° → 88°` with `u^2.4` acceleration) down H St's unobstructed `>120 ft` runway | Trailing electrical sparks & loose stucco/trim chunks shedding along the arc | Smooth pivot around the base hinge (zero floating detachment or wall clipping into adjacent blocks). |
| **P2: Street Slam & Elastic Bounce** | `3.3 – 4.5 s` | Impacts H St asphalt at `~3.4 s`, visibly **rebounds** (`88° → 81° → 88°` damped bounce), then settles; swaps cleanly to `bako_sign_rubble` | Street-level dust surge (`bako_demolition_dust_surge`), bright spark spray, crisp clamped earthquake, metallic crash SFX | Unmistakable elastic bounce sells heavy steel truss weight; fallen arch becomes a **climbable / go-kart-rampable** roadway obstacle for `120 s`. |

### 2.4 Shatterable Glass Bays (`func_breakable`, `style 3`, `health 15`)

- **Trigger:** Any weapon shot, nearby splash/building collapse, OR player/go-kart high-speed smash-through (`> 260 u/s`).
- **Timing:** Instant fracture (`< 0.05 s`) → crisp `glass_impact.wav` + `glass_break` sparkle burst + tumbling shard props (`0.8–1.8 s` scatter) → clean empty window frame (passable immediately!) → silent respawn at `120 s` (deferred if player occupies frame).

---

## 3. Dust Cloud Morphology & Non-Blinding Visibility Budget

Real building demolitions produce clouds that look **colossal and weighty**, yet in an active Quake multiplayer arena they must **NEVER blind players or wash out the frame into solid grey/white fog**.

### 3.1 Three-Layer Morphology Checklist
1. **Floor-Seam Piston Plumes (`bako_collapse_plume`):**
   - Tightly emitted along horizontal tier seams (`originjitter` wide in XY, thin in Z) with brisk outward horizontal burst (`180–300 u/s`) mimicking trapped air compressed between pancaking slabs.
2. **Ground-Hugging Pyroclastic Base Surge (`bako_demolition_dust_surge`):**
   - Radial density current hugging `Z = 6..96 u` expanding outward at `280–420 u/s` (`~16–24 mph` effective game scale) down H Street and 18th Street.
   - High `airfriction (1.5–1.9)` slows the advancing front rapidly so puffs pile up into **rolling, mushrooming vortex curls** rather than streaking off like bullets.
   - Particle `sizeincrease` (`+45..+65 u/s`) creates billowing volumetric expansion over `7–10 s`.
3. **Thermal Buoyant Rising Curl (`bako_collapse_dust`):**
   - Slight upward buoyancy (`velocityoffset_z = +65..+105 u/s`, `gravity = -0.03..-0.05`) lifts the central column upward while outer edges curl outward and dissipate smoothly.

### 3.2 Color Palette & Non-Blinding Opacity Caps (Hard Technical Limits)

| Parameter | Benchmark Target | Hard Fail Threshold |
|---|---|---|
| **Palette (Concrete / Stucco / Plaster)** | Warm dusty beige-tan (`#C8B69E` – `#8E7C68`) over darker warm rubble-charcoal core (`#706458` – `#4C443C`); **NOT** pure cartoon white or neon orange | Pure white (`#FFFFFF`) or flat uniform solid-grey wall |
| **Per-Particle Max Alpha (`effectinfo.txt`)** | **`alpha 70..125`** (decaying to `0` smoothly over `6.5–10 s`) | `alpha > 150` (causes opaque white-out blindness when overlapping) |
| **Linger Duration** | **`7.0–12.0 s`** active presence (3–4 s staggered emission + 6–9 s particle fade) | Vanishes in `< 3 s` (feels tiny/puff-like) OR hangs opaque `> 20 s` |
| **Readability Through Cloud (Critic Check)** | High-contrast player silhouettes, streetlights, and neighboring buildings retain **`>= 40%` visual legibility** even standing near the base surge | Full-viewport white/grey occlusion (`> 85%` of screen pixels clipped to flat fog luminance) |
| **Low-GPU Compatibility (`lowgpu.cfg`, `cl_particles_quality 0.5`)** | Cloud still reads massive and cohesive at `50%` particle density (large `size 64–112`, layered with zero-edict CSQC `DN3FX` sprites) | Looks sparse or invisible at `0.5` quality |

---

## 4. Debris Physics, Rolling Boulders & Rubble Silhouette Benchmarks

### 4.1 Three-Tier Debris Hierarchy

| Tier | Representation | Count Cap | Trajectory & Restitution | Visual & Gameplay Benchmark |
|---|---|---|---|---|
| **Tier 1: Rolling Concrete Boulders & Slabs** *(Padre Hotel hero feature)* | Custom weathered concrete/brick chunk `.md3`s (`progs/bako_boulder*.md3`, `MOVETYPE_BOUNCE`, `SOLID_TRIGGER`) | **20–24 active** | Launched in 3 radial waves (`360–820 u/s` outward, `240–560 u/s` upward arc); **low-to-moderate concrete restitution** (`bouncefactor 0.50–0.62`, first bounce `40–130 u` high — heavy thuds, NOT rubber superballs!); horizontal street roll across H St / 18th St (`300–950 u` reach) with spin axis (`avelocity`) perpendicular to travel + trailing `bako_rock_dust` puffs | Boulders visibly tumble end-over-end down the asphalt; hitting a player or go-kart delivers a dramatic physical **bounce upward & away** (`velocity += dir*420 + '0 0 360'`) + heavy rock thud SFX without snagging/trapping the player! |
| **Tier 2: Masonry Chunks, Bricks & Sparks** *(Fox, Padre, Sign)* | `MOVETYPE_BOUNCE` shrapnel `.md3`s + `bako_masonry_burst` + `bako_sign_sparks` | **<= 32 active** | Snappier initial ejection (`400–750 u/s`) during charge pops, tower shear, and sign short-circuit; fast tumbling `avelocity` (`180–480 deg/s`), settling within `3–5 s` | Sells brittle material fracture right at the break seams. |
| **Tier 3: Glass Shards & Aggregate Dust** | `maps/ad_brk/glass01..12.bsp` / `lan_deb_glass.md3` + `glass_break` particles | Per-window capped | High-velocity glittering fan away from impact normal; clears within `2 s` | Crisp sparkling glass breakup; **zero blood splatters or flesh sounds** on masonry, metal, or glass! |

### 4.2 Climbable Rubble Silhouette Standards (`bako_*_rubble`)
- **Profile:** Multi-tiered jagged/stepped masonry and tilted slab silhouette (Padre: dramatic **2-story / `~22–28 ft`** terraced concrete mountain; Fox: stepped brick & broken marquee frame; Sign: fallen `BAKERSFIELD` arch resting as a ramp across H St). Never a flat box or single pyramid.
- **Navigability:** Every flank provides walkable slopes (`<= 38°`) or climbable step ledges (`<= 18 u` vertical step) so players on foot AND go-karts can scale the ruins for mid-match high ground.
- **Lighting & Grounding:** `"_shadow" "0"` and `"_minlight" "20–24"` on all collapsible & rubble submodels so:
  1. Collapsing a building NEVER leaves an ugly pitch-black baked shadow rectangle burned onto the street.
  2. Rubble mounds rising out of the dust cloud are warmly, naturally lit — never silhouettes of pure `#000000`.
- **Player Safety:** When `bako_*_rubble` turns `SOLID_BSP`, any player/go-kart inside its XY bounds is smoothly lifted onto the top surface (`trace_endpos_z + 26`, gentle upward hop) — **zero stuck-in-solid incidents**.

---

## 5. Camera & Earthquake Feel Benchmarks (Crisp Impact, Zero Blindness)

Real demolition shockwaves hit viewers with a visceral **seismic thud** (`0.05–0.18 s` after distant visual impact), combining a heavy low-frequency ground-roll pulse with sharp impact snaps. In Quake/Zircon, this must feel epic across the entire map **without ever disorienting players, hijacking aim, or blinding the screen**.

| Rule / Metric | Approved Quantitative Range | Strictly Forbidden (Instant Fail) |
|---|---|---|
| **Shake Mechanism** | Clamped, distance-attenuated `punchangle` pulses (`0.15–0.22 s` cadence across impact beats; respects `effects_explosion_shake`) | Any `fixangle`, `v_angle` hijack, or permanent view roll offset |
| **Pitch Clamp (`punchangle_x`)** | **`±5.5°` max** at epicenter, attenuating smoothly to `±1.2°` across map | `> 7.0°` vertical whip (breaks crosshair tracking) |
| **Roll Clamp (`punchangle_z`)** | **`±3.5°` max** on foot (**`±1.75°` max** inside go-karts/vehicles) | `> 5.0°` tilt (causes motion sickness / vehicle disorientation) |
| **Yaw Clamp (`punchangle_y`)** | **`±2.5°` max** subtle lateral jolt | `> 3.5°` horizontal twist |
| **Screen Flash / Color Wash** | **ZERO** (`0` `bf`, `0` `v_cshift`, `0` full-screen flash) | Any `bf`, `v_cshift` white/brown wash, or blinding bloom spike |
| **HUD Notifications** | Clean corner drop-shadowed text only (`CLAUDE.md`: top-right / top-left corner stack) | Any dark/opaque center-screen box or `drawfill` banner |

---

## 6. Fresh-Context Demolition Critic Scoring Rubric (100 Points)

Fresh-context Critics inspect both the **720p H.264 MP4** (for pacing, physics, earthquake feel, audio sync) and the **6×2 / 4×3 Keyframe Contact Sheets** (for dust opacity, rubble lighting, silhouette clarity, and zero visual glitches).

| Category | Max Pts | Pass Bar | Keyframe & Video Inspection Criteria |
|---|---:|---:|---|
| **1. Collapse Pacing & Gravity Weight** | **25** | `>= 20` | Visible pre-collapse pops/buckling hesitation; clear non-linear `u^2+` acceleration; staggered multi-piece/multi-tier motion (`Padre 11–13 s`, `Fox 8–9 s + 25 s rebuild`, `Sign 4.5 s + bounce`). Zero robotic constant-speed sliding. |
| **2. Dust Cloud Morphology & Readability** | **25** | `>= 20` | Distinct floor-seam plumes + rolling ground-hugging base surge + buoyant rising curl; warm stucco/concrete palette; lingers `7–12 s`; **zero white-out blindness** (`>= 40%` background contrast preserved). |
| **3. Debris Physics & Climbable Aftermath** | **25** | `>= 20` | Realistic concrete bounce heights (not rubber balls); tumbling rolling boulders across H St / 18th St that visibly bounce players/karts; veiled rubble swap (zero naked pop); natural `_minlight` rubble lighting; zero void leaks or baked street shadow holes; climbable/rampable profile. |
| **4. Camera/Earthquake Feel & Gameplay Polish** | **15** | `>= 12` | Crisp impact shake synced to major slams without blinding or aim-hijacking; zero `bf`/`v_cshift`/center HUD boxes; real weapon hits visibly register (no blood FX on stone/glass); Fox rebuild locks seamlessly back intact. |
| **5. Visual Composition & Framing Fidelity** | **10** | `>= 8` | Intact 360° orbit matches authentic Bakersfield landmark silhouettes (Padre, Fox, Sign); collapsed 360° orbit shows clean ruins from every side with zero floating scraps or Z-fighting. |

### Instant-Fail Red Flags (Automatic Revision Trigger)
1. **Instant / Too-Fast Collapse:** Padre `< 8 s`, Fox `< 5.5 s`, or Sign `< 2.8 s` — destroys sense of massive scale.
2. **Naked Pop-Swap:** Intact building vanishes into thin air before dust covers the swap, or rubble pops in over empty air.
3. **Blinding Fog / Flash:** White-out dust wall (`> 85%` viewport occluded) or `bf`/`v_cshift` screen flash.
4. **Baked Black Footprint / Void Leak:** Pitch-black shadow rectangle left on asphalt after collapse, or missing floor revealing sky/void underneath.
5. **Blood on Buildings / Unresponsive Weapons:** Blood splatters on masonry/sign/glass, or rockets/Eric Cannon failing to damage large walls.
6. **Stuck Players or Floating Clipped Debris:** Rubble trapping a standing player or falling sign clipping straight through an adjacent building wall.
