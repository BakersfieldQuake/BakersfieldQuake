# Prompt: "WHERE'S THE DISK?" gun - two Quake models

You are adding a new fun gun to BakersfieldQuake, a DarkPlaces/Quake mod in `G:\Quake\Combat\BakersfieldQuake`. Read `CLAUDE.md` first (how to test, where games open). Your job in this task is the **two 3D models and their shaders/textures**. Gun logic (QC) comes after the models are approved, unless I say otherwise.

## The joke (so the models get the tone right)

In the early 2000s, in high school, I was accused of putting a batch file on a school computer that sent `net send` pop-up messages to every machine on the network. I was hauled into the principal's office and interrogated: "David, where's the disk? WHERE'S THE DISK?" They were sure a floppy with the batch file existed. It has been an inside joke for years. The gun is that story: a hand holds a floppy disk labelled `LOL.BAT`; you throw it at the floor, it sticks, and a beige early-90s PC grows out of it and starts blasting `net send` messages at everybody. Make it funny, a bit cartoonish, readable at a glance in a fast deathmatch.

## Model 1: the viewmodel (first-person gun) - `progs/v_netsend.md3`

A hand holding a 3.5" floppy disk, drawn in the lower-right of the screen like every other gun in this mod.

- **The disk:** black/dark-grey 3.5" floppy with metal shutter, and a white paper label reading **`LOL.BAT`** in handwriting-ish or dot-matrix lettering. Label must be legible in first person (put it on the face turned toward the player in the idle hold). Slight cartoon exaggeration is fine; make it about the size of a playing card in the player's view so the label reads.
- **The hand:** match the style of the other hand-held fun guns (look at `v_pickle.md3` / the pickle viewmodel, built by `source/mm_tools/build_pickle_assets.py` and `build_fungun_viewmodels.py`, and the Mega-Slinger work in `build_megaman_weapon.py`). Same scale and screen position so the gun doesn't hide the crosshair.
- **Animation (vertex frames in one MD3):**
  - Frames 0-39: **idle loop**, seamless. He holds the disk up, spins it between his fingers, flips it over once (the back shows the metal shutter), tilts it to inspect the label, nods at it. Smooth, a bit smug.
  - Frames 40-47: **wind-up and throw**: arm draws back, then throws the disk hard down and forward at the floor. The disk leaves the hand at around frame 44 (the game will spawn the world disk at that moment, so the hand must be empty from then on).
  - Frames 48-53: follow-through, empty hand.
  - Frames 54-59: empty hand, shaking out, **a new disk slides into view** (this is the reload; the idle loop starts again after).
  - Write down the frame map in the file header / a text file next to the build script so QC can use it.

## Model 2: the world model (what the thrown disk becomes) - `progs/netsend_pc.md3`

A tall, standing, early-90s beige PC that appears where the disk sticks into the floor. It is a deployable, like the sentry gun (see `Sentry_Build` and `progs/` sentry assets): it stands in the map, other players see it, and I walk up to it and read its screen.

- **Look:** beige/grey-plastic desktop or mini-tower with a **CRT monitor** on top (deep, rounded back, bezel, little brand-less badge), a chunky keyboard and a **big beige "computer stand"/desk base** under it, a **3.5" floppy slot** in the case front (the disk can be seen half-inserted), a power LED and a drive-activity LED. Cables trailing to the floor. Overall height about 56-64 Quake units, footprint about 32x32, so it stands a little taller than a crouching player and reads from across a room.
- **The screen is the star.** It must be readable when I walk right up to it, so give it its **own surface and its own high-resolution texture** (at least 256x128 mapped to the screen face only, text on it large and crisp, green or white phosphor on black, a touch of scanline). The text sequence, in order:
  1. Black screen, then a flicker of white noise (power on, CRT warm-up).
  2. `INITIALIZING BATCH FILE...`
  3. `C:\> LOL.BAT`
  4. `NET SEND * LOL`
  5. A looping hacking screen: scrolling lines of fake hex and `NET SEND * LOL`, `NET SEND * WHERE'S THE DISK?`, `MESSAGE SENT [OK]` with a blinking cursor, typed out as if live.
  The final loop should feel like constant typing.
- **Animation (vertex frames):**
  - Frames 0-9: **materialize**: the disk sticks into the floor, the case rises/pops up out of it with a little squash-and-stretch overshoot.
  - Frames 10-19: **boot**: power LED on, monitor shakes slightly and turns on, floppy drive LED flickers.
  - Frames 20-39: **active loop**: keys visibly depress as if typed by ghosts, the monitor hums/jitters, antennas twitch. Seamless loop.
  - Frames 40-49: **shutdown**: the screen collapses to a white dot, case slumps (used when the timer ends or it is destroyed).
- **Antennas:** four **rabbit-ear TV antennas / satellite whip antennas** sticking out of the top of the monitor and sides of the case. They are what "shoots" the `net send` messages. Give them bright tips. Model them as separate vertices so they can wobble in the animation.
- **Electricity:** crackling lightning arcs between the antenna tips and from the case to the floor. Do this as a **separate small additive effect model** `progs/netsend_arc.md3` (a few crossed ribbons/quads, 6-8 frames of different jagged arc shapes cycled in the game, additive blue-white shader) and/or a DarkPlaces `effectinfo.txt` effect (see how `pk_boom` / `ltg_zap` are done between the marker comments). Keep a lightning-textured sprite option as fallback.
- **Spinning:** the PC rotates slowly in a circle while active. **Do not bake this into the frames**: the game will turn the entity's yaw, so the model's origin must be at the **centre of its base footprint on the floor**, and the whole thing must look correct when rotating about the vertical axis (no asymmetry that makes it wobble out of its footprint).
- Optional small third asset if it is easy: `progs/netsend_disk.md3`, the lone disk stuck at an angle in the floor for the moment before the PC pops out (it can reuse the viewmodel's disk). Skip if it costs a lot.

## Must be Quake / DarkPlaces compatible (this is the point)

The game is DarkPlaces on the Quake engine. Build everything so it loads in this mod without errors:

- **Format:** MD3 (vertex-animated, multi-frame) in `BakersfieldQuake/progs/`. MD3 limits: max 1024 frames, max 8192 triangles and 4096 vertices **per surface**, max 32 surfaces, names under 64 chars, vertex positions are signed 16-bit fixed-point (1/64 unit), so keep geometry within about +/-500 units of the origin. Every surface needs UVs and a shader name. All frames must have identical topology.
- **Budget:** viewmodel under about 3000 triangles; PC under about 4000 triangles (plus the arc model). Many players, many sentries: don't go crazy.
- **Scale:** Quake units. A player is 56 tall, 32 wide. MD3 origin conventions: viewmodel as in the existing fun guns (eye at origin, +X forward); the PC's origin on the floor at the centre of its base.
- **Textures:** PNG or TGA in `progs/` (power-of-two sizes where practical, e.g. 256x256, 256x128, 512x512), referenced by a **shader** in `scripts/netsend.shader` (new file; look at `scripts/pickle.shader`, `scripts/megaman_slinger.shader`, `scripts/ltgun.shader` for what works here). Use `cull none` on thin shells (the Mega-Slinger looked see-through until fixed), `blendfunc add` or `blendfunc blend` for the arcs and CRT glow.
- **Brightness:** this DarkPlaces setup renders about **2.5x brighter** than raw textures (see `reference-darkplaces-quirks` in my memory notes). Bake textures dim (roughly 0.35-0.5x) or they blow out white. The CRT screen should still glow, so give it its own glow stage.
- **Animated screen text:** a shader `animmap` runs on the **clock, not the model frame**, so it can't be synced to the model's frame number directly (the laptop gun hit exactly this and solved it with several rotated copies of the model, `ltg_type_0..7.md3`). Plan for that: either keep the screen on its own surface so it can play its own timeline from the moment the PC appears (rotated copies like the laptop gun if sync matters), or let the boot text be a short sequence of screen frames the QC switches by changing the skin/model variant. Tell me which you chose.
- **Tools:** Blender is connected through the Blender MCP; build and look at the models there. For writing MD3, **reuse the MD3 writer already used in `source/mm_tools/`** (see `build_pickle_assets.py`, `build_googun.py`, `build_fungun_viewmodels.py`, `build_megaman_weapon.py`, `build_laptop_gun.py`) instead of writing a new exporter. Put new scripts in `source/mm_tools/` with a `build_netsend_assets.py` entry point that regenerates everything and installs it into `BakersfieldQuake/progs`, `scripts` and (if needed) `effectinfo.txt` between its own begin/end markers. Keep names prefixed `netsend_` so nothing clashes with the other agents' files (another agent already made a `laptop` set; do not touch it).
- **Do not overwrite** any existing model or shader. Back up anything you must change with a `.pre_netsend` suffix.

## Check your work before you call it done

1. Render turntables (or Blender `look` shots) of both models, and a contact sheet of the key frames of each animation.
2. **Load them in the game** on the map `start` (never dm6) following `CLAUDE.md`: launch short and unattended, log with `-condebug`, no model-load errors in the log. A quick test cfg can use `setmodel`/`impulse` cheats or `viewmodel` hooks; for models alone it is enough to show each one in the world and to dump screenshots, with the CRT screen close up so I can read the text.
3. Check specifically: label reads `LOL.BAT` in first person; the hand/disk doesn't cover the crosshair; nothing see-through; textures not blown out; the PC's screen text is readable from about 40 units away; the spin looks right when rotated about the base.
4. Report: file list, triangle counts, frame maps for both models, anything you couldn't do, and screenshots.

Ask me before you change the plan; don't wait on small details, pick sensible defaults and say what you picked.
