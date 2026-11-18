# Task: make the `bklan` Quake map more accurate, with the ORCOM CONNECT LAN PARTY as a room inside it

You are improving the Quake map `bklan` in the BakersfieldQuake mod (DarkPlaces, ericw-tools), and merging the separate
`orcom` map into it. They are recreations of real places. Your job is an accuracy audit: compare the maps against every real-world source below, find what is wrong
or missing, fix it, and show proof with side-by-side screenshots.

## The maps
- `bklan`: the 2001 "B-LAN" LAN party in unit 130A, 118 E 21st St, Bakersfield CA, plus the surrounding block (E 21st St,
  Sacramento St, Sumner St, Union Ave overpass, the rail line), the Bakersfield Sign over Sillect Ave, Buck Owens' Crystal
  Palace, the house at 1608 Manning St (with the white van), and Amberton Park. The last three are transplanted
  next to Larry's block, not at their real location.
- `orcom`: the OrCom Connect LAN party hall (Dec 2002), today a standalone map. See "Merge orcom into bklan" below:
  it must become a room inside `bklan`, not a second map.
- Generators (Python writes a .map): `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\make_bklan.py`,
  `make_bklan_v2.py` (sign, palace, Manning, park), `bklan_sign.py`, `make_orcom.py`. Textures:
  `build_bklan_textures.py` (+ `sunny_pass.py`). Read `memory\project-bklan-map.md` and `project-orcom-map.md` (in
  `C:\Users\qxdc\.claude\projects\G--Quake-Combat-BakersfieldQuake\memory\`) first; they explain the frame, units
  (12 units per foot) and what was measured versus guessed.

## Merge orcom into bklan (required)
The ORCOM CONNECT LAN PARTY must be a room (a building) inside `bklan`, not a separate map. One map, one BSP.
- Move the hall's geometry, textures (`oc_*`), props, lights and spawns from `make_orcom.py` into the `bklan` generator
  (a module like `make_bklan_v2.py`, using the same frame, 12 units per foot, `box`/`face` helpers and groups). Give it a
  real building shell on the block with a door (the entrance is on the east wall of the hall, with its vestibule), so a
  player can walk in from the street and out again. Pick a spot on the block that does not collide with the existing
  buildings, streets, the sign, or the Manning / park areas, and say why you chose it.
- Keep the hall's interior accurate to `Orcom 2.mpg` (kitchen west, entrance east, BAWLS banner and exit door south,
  "Computer" banner north, rows of tables with CRTs and burgundy chairs). Interior lighting stays indoor (troffers at
  about 165, `_minlight` is per map so check it does not wash the room out or darken the outdoors).
- Add "ORCOM CONNECT LAN PARTY" entries to the spots list (and so to the viewer's "Jump to" menu) and give it deathmatch
  spawns and items inside the hall.
- Once the merged map works: stop shipping `orcom` as its own map. Remove `orcom.bsp` and `.lit` from `maps\`, drop
  `view_orcom.sh` / `deploy_orcom_viewer.sh` from use, and make `https://bakersfield.larrywew.fun/orcom/` redirect to
  the warehouse viewer (or serve a page that links to the spot inside it). Keep `make_orcom.py` only if the new module
  imports from it, otherwise note it as retired.
- Watch the cost: bklan is already BSP2 with 77,000 faces and a one-hour vis. Use `func_detail` for furniture and props
  so vis does not get slower, and check there are no leaks.

## Sources of truth (compare against ALL of these)
1. Home videos (pull frames with ffmpeg, e.g. fps=1 plus scene-change frames; run faster-whisper for any spoken clues):
   - `D:\Local\Video\Capture Homevids\bklan.wmv` (the LAN in unit 130A, 2001, 320x240)
   - `D:\Local\Video\Capture Homevids\Orcom 2.mpg` (the OrCom hall)
2. The owner's review videos, where they point at mistakes and say what to fix (watch every one, transcribe the audio):
   - `C:\Users\qxdc\Videos\2026-10-30 17-40-08.mp4` (mistakes in the first map)
   - `C:\Users\qxdc\Videos\2026-10-30 22-56-37.mp4` (the Bakersfield Sign, Crystal Palace, Manning St, park)
3. Google Maps / Street View photos: `C:\Users\qxdc\Videos\larry-warehouse-gallery-self-contained.html` and
   `...gallery-self-contained (1).html` (about 100 Street View photos of 118 E 21st St and the block). Unpack the images.
   Also use Google Maps satellite and Street View live in the browser pane for the other locations, with the scale bar,
   and OpenStreetMap (api.openstreetmap.org bbox export) for footprints.
4. Reference frames already extracted: `source\mm_tools\ref_v2\` and `ref_orcom\`.

## Where the images are
Everything is already extracted for you under `G:\Quake\Combat\BakersfieldQuake\source\mm_tools\ref_sources\` (read its
`README.txt`). Start from the contact sheets, then open individual frames. Re-extract from the original videos with
ffmpeg when you need a higher resolution or a different moment.
- `bklan_wmv_frames\`: one frame per second of bklan.wmv (file number = second + 1, 3175 frames, 320x240) and
  `bklan_contact_sheets\` (53 numbered sheets with timestamps).
- `orcom_mpg_frames\` and `orcom_contact_sheets\`: the same for Orcom 2.mpg.
- `streetview_gallery1\` and `streetview_gallery2\`: the Google Street View and satellite images unpacked from the two
  gallery HTML files (about 180 images), including `aerial-z16-wide-sat.jpg`, `aerial-z17-sat.jpg`, `aerial-z17-hybrid.jpg`.
- `review_2026-10-30_17-40-08_frames\` and `review_2026-10-30_22-56-37_frames\`: frames of the owner's two review
  videos. Watch the videos themselves (and transcribe the audio) too; the frames do not carry what the owner says.
- `osm\`: OpenStreetMap exports for the palace and Manning sites.
- Originals, if you need them: `D:\Local\Video\Capture Homevids\bklan.wmv`, `Orcom 2.mpg`,
  `C:\Users\qxdc\Videos\2026-10-30 17-40-08.mp4`, `C:\Users\qxdc\Videos\2026-10-30 22-56-37.mp4`, and the two
  `larry-warehouse-gallery-self-contained*.html` files in `C:\Users\qxdc\Videos\`.
- Street View and Maps for places not in the gallery (the Bakersfield Sign, Crystal Palace, 1608 Manning St, Amberton
  Park) are live in the browser pane: use satellite view with the scale bar, and Street View photos.
- `G:\Quake\Combat\BakersfieldQuake\making_of_larrys_warehouse.html` lists the images used to build the first version.

## Method
1. Build an inventory of what each source shows: every wall, door, window, sign, vehicle, prop, pole, fence, tree, road
   marking, and its position and size. Read contact sheets rather than single frames. Note which source and timestamp or
   photo each fact comes from.
2. Take matching screenshots of the map from the same viewpoint (start from the camera positions in the spots lists,
   `view_bklan.sh`), put each beside the real photo or video frame, and list every difference
   (proportions, positions, colours, missing or invented objects, signage text, textures, orientation, scale).
3. Rank the differences by how visible they are and how sure you are, then fix them in the generators (not by editing the
   .map by hand). Use real measurements where possible (doors about 80 in, standard signs, vehicles, the scale bar).
4. Re-test and show before and after pictures in a report page.

## Facts already established (do not undo these)
- The front of 118 E 21st St faces south-west. The only legible street signage is "BATERIAS $55" and 120A / 120B. Grove
  St is not the rear of 118. The LAN room is at the north end of the building along Sacramento St, facing the lot.
- No image backdrops for streets: the streets and the blocks around are real geometry.
- The Bakersfield Sign dimensions were measured: towers 97 ft apart, 62 ft road, 31 ft at the roof peak, letters about
  4.7 ft tall.
- Orcom layout: kitchen at the west, entrance at the east, BAWLS banner and exit door on the south wall, "Computer"
  banner on the north wall; 76 x 52 x 10 ft estimated from scale cues. The venue name and address never appear on the tape.
- The map is now a sunny day (warm sun, blue sky, boosted colours). Keep it bright; do not push sun above about 150 or
  the game blows out.

## Rules: honesty first
- Only change something when a source supports it. If you guess, label it as a guess in the report. Never invent text,
  signs, or objects that are not visible in a photo or video. If a source is too blurry, say so.
- Keep a changelog of every change: what, which source and timestamp or photo, before and after screenshots.

## Rules for working in this project (from CLAUDE.md)
- Never test on dm6. Test on the map `start` for gameplay; for these maps use the view scripts.
- Launch tests from `G:\Quake\Combat` running `darkplaces.exe` directly (it opens on the right monitor). Do not use
  `launch_left.ps1`. Keep tests short and unattended and close the window when the screenshots are written.
- Before a test, check that no other `darkplaces.exe` is running (another agent, or the user's game) and wait if so.
  When cleaning up, stop only the process you started, by its id.
- Read results from a log (`-condebug +log_file zz_x.log`), not `condump`. Bots need `+maxplayers 4`.
- Tests must not change the user's saved cvars (DarkPlaces writes config.cfg on quit; restore it if it changes).
- Python with PIL: `/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe` (run PIL scripts without `-I`).
  Compilers: `D:\vibe\quake1opensource\tools\ericw` (qbsp, vis, light -extra).
- A full `bklan` rebuild takes about an hour because of `vis` (the map is BSP2, 77,000 faces). Iterate with the no-vis test
  builds in `view_bklan.sh`, batch your fixes, and do one full `sh build_bklan.sh` at the end. Light-only changes can be
  re-lit with `light.exe -extra` on the existing bsp without re-running vis.
- Other Claude agents may be working in the same folders; do not touch the gun, sound, or gameplay files.

## Deliverables
1. The updated single map, installed into `BakersfieldQuake\maps\` (bklan.bsp and .lit, with the ORCOM hall inside it),
   compiling without leaks or missing-texture warnings and loading in DarkPlaces. No separate orcom map any more.
2. The browser viewer redeployed: `sh deploy_web_viewer.sh` (https://bakersfield.larrywew.fun/warehouse/), with an
   ORCOM spot in the "Jump to" menu, and `/orcom/` redirecting to it.
3. An accuracy report (HTML page) with, for each fix: real photo or frame next to the map screenshot before and after,
   and the source. Also a list of what is still a guess and what no source covers.
4. Update the memory notes (`project-bklan-map.md`, `project-orcom-map.md`) with what changed, including that orcom is
   now a room inside bklan.
