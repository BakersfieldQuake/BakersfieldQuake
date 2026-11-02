"""End-to-End 360° Sprite, Contact Sheet, Animated GIF, & Interactive HTML Showcase Builder
for Daniel ("Moving the Table at 4 AM" / "CCC!" / "SHAAAAA!" / "Justin Berry's Webcam")
and Angry 4 AM Dad (BakersfieldQuake).

Outputs:
  1. progs/daniel.spr32            (344 frames, 256x288, origin (-128, 262), HDR pre-toned)
       0..7     idle[0..7]
       8..55    fast_run[d][k]        (8 dirs x 6 frames — mbox.qc compatible)
       56..103  table_move[d][k]      (8 dirs x 6 frames — 4 AM Moving the Table)
       104..151 ccc_barrage[d][k]     (8 dirs x 6 frames — "CCC! C-C-C-C!" Grin Barrage)
       152..199 shaaa_rage[d][k]      (8 dirs x 6 frames — "SHAAAAAAAA!" Neon LAN Rage)
       200..247 webcam_squint[d][k]   (8 dirs x 6 frames — "Justin Berry's Webcam" Squint)
       248..295 sorry_panic[d][k]     (8 dirs x 6 frames — Hands-Up "Sorry!" Panic Sprint)
       296..343 lan_station[d][k]     (8 dirs x 6 frames — 360° Bakersfield LAN Station)
  2. progs/daniel_dad.spr32        (56 frames, 160x192, origin (-80, 175), HDR pre-toned)
       0..7     idle[0..7]
       8..55    run[d][k]             (8 dirs x 6 frames — mbox.qc compatible)
  3. daniel_sprite/*.png           (high-res 480x540 RGBA frames + contact sheets + GIFs)
  4. daniel_sprites.html           (interactive 360° viewer + 7-clip soundboard)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import math
import os
import struct
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent

for p in (str(CUR_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from daniel_rig import (
    STAGE_GY,
    STAGE_H,
    STAGE_W,
    build_all_daniel_animations,
    load_all_daniel_assets,
    resize_rgba_premul,
)

DN_SPR_W, DN_SPR_H = 256, 288
DN_SPR_OX = -(DN_SPR_W // 2)
DN_SPR_OY = round(STAGE_GY * DN_SPR_H / STAGE_H)  # 262

DD_SPR_W, DD_SPR_H = 160, 192
DD_SPR_OX = -(DD_SPR_W // 2)
DD_SPR_OY = round(STAGE_GY * DD_SPR_H / STAGE_H)  # 175

RUN_6_INDICES = [0, 1, 2, 4, 5, 6]
DIR_LABELS = [
    "0° Front", "45° Front-L", "90° Left", "135° Back-L",
    "180° Back", "225° Back-R", "270° Right", "315° Front-R",
]
MODES_7 = (
    "fast_run",
    "table_move",
    "ccc_barrage",
    "shaaa_rage",
    "webcam_squint",
    "sorry_panic",
    "lan_station",
)


def pretone_for_darkplaces_hdr(frames_rgba: list[np.ndarray], target_mean_lum: float = 62.0) -> list[np.ndarray]:
    """Pre-tones SPR32 RGB for DarkPlaces r_hdr_scenebrightness ~2.5 so sprites never blow out white."""
    boosted: list[np.ndarray] = []
    lums: list[float] = []
    for fr in frames_rgba:
        rgb_im = Image.fromarray(fr[..., :3], "RGB")
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(1.15)
        rgb_im = ImageEnhance.Color(rgb_im).enhance(1.06)
        rgb = np.asarray(rgb_im, dtype=np.float32)
        mask = fr[..., 3] > 128
        if np.any(mask):
            lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
            lums.append(float(lum[mask].mean()))
        boosted.append(np.dstack([np.clip(np.round(rgb), 0, 255).astype(np.uint8), fr[..., 3]]))

    cur_mean = float(np.mean(lums)) if lums else 100.0
    gain = float(np.clip(target_mean_lum / max(1.0, cur_mean), 0.38, 0.92))
    out: list[np.ndarray] = []
    for fr in boosted:
        toned = fr.copy()
        toned[..., :3] = np.clip(np.round(toned[..., :3].astype(np.float32) * gain), 0, 255).astype(np.uint8)
        out.append(toned)
    return out


def write_spr32(path: Path, frames_rgba: list[np.ndarray], ox: int, oy: int) -> tuple[int, float]:
    """Writes an IDSP v32 SPR_VP_PARALLEL_UPRIGHT (stype=0) 32-bit RGBA DarkPlaces sprite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    maxw = max(f.shape[1] for f in frames_rgba)
    maxh = max(f.shape[0] for f in frames_rgba)
    rad = math.sqrt((maxw / 2.0) ** 2 + float(maxh) ** 2)

    buf = bytearray()
    buf += b"IDSP"
    buf += struct.pack("<iifiiifi", 32, 0, rad, maxw, maxh, len(frames_rgba), 0.0, 0)

    lums: list[float] = []
    for fr in frames_rgba:
        h, w = fr.shape[:2]
        buf += struct.pack("<i", 0)
        buf += struct.pack("<iiii", ox, oy, w, h)
        buf += fr.tobytes()
        m = fr[..., 3] > 128
        if np.any(m):
            rgb = fr[..., :3].astype(np.float32)
            lums.append(float((0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[m].mean()))

    path.write_bytes(bytes(buf))
    return len(buf), (float(np.mean(lums)) if lums else 0.0)


def _save_png(task: tuple[Path, np.ndarray]) -> None:
    p, arr = task
    Image.fromarray(arr, "RGBA").save(p, compress_level=3)


def make_daniel_master_sheet(dn: dict, out_path: Path) -> None:
    rows = [
        ("Standing Idle 360°", [dn["idle"][d] for d in range(8)]),
        ("Fast Run 360°", [dn["fast_run"][d][1] for d in range(8)]),
        ("4 AM Moving Table 360°", [dn["table_move"][d][1] for d in range(8)]),
        ("CCC! C-C-C-C Grin 360°", [dn["ccc_barrage"][d][0] for d in range(8)]),
        ("SHAAAAAAAA! Rage 360°", [dn["shaaa_rage"][d][1] for d in range(8)]),
        ("Justin's Webcam 360°", [dn["webcam_squint"][d][0] for d in range(8)]),
        ("Hands-Up 'Sorry!' 360°", [dn["sorry_panic"][d][1] for d in range(8)]),
        ("360° LAN Station", [dn["lan_station"][d][2] for d in range(8)]),
    ]
    cw, ch = 200, 225
    hdr_h = 34
    sheet = Image.new("RGB", (cw * 8, hdr_h + ch * len(rows)), (18, 22, 30))
    dr = ImageDraw.Draw(sheet)
    for d in range(8):
        dr.text((d * cw + 52, 10), DIR_LABELS[d], fill=(253, 230, 138))

    for r_i, (lbl, imgs) in enumerate(rows):
        oy = hdr_h + r_i * ch
        for d in range(8):
            ox = d * cw
            bg_c = (27, 32, 43) if (r_i + d) % 2 == 0 else (22, 26, 36)
            dr.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], fill=bg_c, outline=(42, 49, 64))
            cell = Image.fromarray(resize_rgba_premul(imgs[d], cw, ch), "RGBA")
            sheet.paste(cell, (ox, oy), cell)
        dr.rectangle([6, oy + 6, 188, oy + 24], fill=(12, 15, 22))
        dr.text((11, oy + 9), lbl, fill=(248, 250, 252))

    sheet.save(out_path, optimize=True)


def make_dad_master_sheet(dd: dict, out_path: Path) -> None:
    rows = [
        ("4 AM Dad - Furious Yell Idle 360°", [dd["idle"][d] for d in range(8)]),
        ("4 AM Dad - Charge Stride A 360°", [dd["run"][d][0] for d in range(8)]),
        ("4 AM Dad - Charge Stride B 360°", [dd["run"][d][2] for d in range(8)]),
        ("4 AM Dad - Charge Stride C 360°", [dd["run"][d][4] for d in range(8)]),
    ]
    cw, ch = 200, 225
    hdr_h = 34
    sheet = Image.new("RGB", (cw * 8, hdr_h + ch * len(rows)), (24, 18, 22))
    dr = ImageDraw.Draw(sheet)
    for d in range(8):
        dr.text((d * cw + 52, 10), DIR_LABELS[d], fill=(252, 165, 165))

    for r_i, (lbl, imgs) in enumerate(rows):
        oy = hdr_h + r_i * ch
        for d in range(8):
            ox = d * cw
            bg_c = (34, 24, 29) if (r_i + d) % 2 == 0 else (28, 20, 24)
            dr.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], fill=bg_c, outline=(56, 38, 44))
            cell = Image.fromarray(resize_rgba_premul(imgs[d], cw, ch), "RGBA")
            sheet.paste(cell, (ox, oy), cell)
        dr.rectangle([6, oy + 6, 226, oy + 24], fill=(16, 11, 14))
        dr.text((11, oy + 9), lbl, fill=(254, 242, 242))

    sheet.save(out_path, optimize=True)


def save_orbit_gif(seq_rgba: list[np.ndarray], labels: list[str], out_path: Path, w: int = 280, h: int = 315, duration_ms: int = 75) -> None:
    pil_frames: list[Image.Image] = []
    for arr, lbl in zip(seq_rgba, labels):
        bg = Image.new("RGB", (w, h), (22, 25, 34))
        dr = ImageDraw.Draw(bg)
        dr.ellipse([24, h - 52, w - 24, h - 14], fill=(34, 39, 52))
        scaled = Image.fromarray(resize_rgba_premul(arr, w, h), "RGBA")
        bg.paste(scaled, (0, 0), scaled)
        dr.rectangle([8, 8, min(w - 8, 14 + len(lbl) * 6), 26], fill=(12, 14, 20))
        dr.text((13, 11), lbl, fill=(253, 230, 138))
        pil_frames.append(bg.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    pil_frames[0].save(
        out_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def write_daniel_showcase_html(mod_dir: Path) -> None:
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Daniel &amp; 4 AM Dad — BakersfieldQuake 360° Sprite &amp; Meme Asset Showcase</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: #0e1118; color: #e2e8f0; }
  header { padding: 20px 28px; background: linear-gradient(135deg, #172033, #0f172a); border-bottom: 1px solid #263248; }
  h1 { margin: 0 0 6px; font-size: 22px; color: #fde68a; }
  p.sub { margin: 0; color: #94a3b8; font-size: 14px; }
  main { max-width: 1280px; margin: 0 auto; padding: 22px 24px 60px; display: grid; gap: 22px; }
  .grid2 { display: grid; grid-template-columns: 440px 1fr; gap: 22px; align-items: start; }
  .card { background: #151b26; border: 1px solid #263248; border-radius: 12px; padding: 18px; }
  .stage { width: 384px; height: 432px; margin: 0 auto; background: radial-gradient(circle at 50% 82%, #243047 0%, #111622 72%); border-radius: 10px; display: flex; align-items: center; justify-content: center; cursor: grab; user-select: none; border: 1px solid #2c3a52; }
  .stage img { width: 360px; height: 405px; image-rendering: auto; pointer-events: none; }
  .btns { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
  button { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 7px; padding: 7px 11px; font-size: 12.5px; cursor: pointer; }
  button:hover { background: #29384f; }
  button.active { background: #f59e0b; color: #0f172a; border-color: #fbbf24; font-weight: 700; }
  .snd-btn { background: #14332b; border-color: #10b981; color: #a7f3d0; }
  .snd-btn:hover { background: #1b463b; }
  .gifs { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
  .gifs img, .sheet img { width: 100%; border-radius: 8px; border: 1px solid #2a364d; }
  code { background: #0b0f17; padding: 2px 6px; border-radius: 4px; color: #fde68a; }
</style>
</head>
<body>
<header>
  <h1>Daniel ("4 AM Table" / "CCC!" / "SHAAAAA!" / "Justin Berry's Webcam") &amp; Angry 4 AM Dad</h1>
  <p class="sub">BakersfieldQuake 360° 8-Direction DarkPlaces SPR32 Rig · MD3 Props · Wall Posters · BKTV Channels 8–11 · Mystery Box #27–28</p>
</header>
<main>
  <div class="grid2">
    <div class="card">
      <div class="stage" id="stage" title="Drag left/right to orbit 360°">
        <img id="spriteImg" src="daniel_sprite/daniel_table_move_d0_f0.png" alt="Daniel 360 sprite">
      </div>
      <div style="text-align:center;margin-top:8px;font-size:13px;color:#cbd5e1;" id="statusLbl"> Angle: 0° Front · Frame 0 </div>
      <div class="btns" id="dirBtns"></div>
    </div>
    <div class="card">
      <h3 style="margin:0 0 8px;color:#fde68a;">Animation Mode (Drag Viewer to Orbit 360°)</h3>
      <div class="btns" id="modeBtns"></div>
      <div class="btns" style="margin-top:10px;">
        <button id="orbitToggle" class="active">Auto-Orbit 360°: ON</button>
      </div>
      <h3 style="margin:18px 0 8px;color:#6ee7b7;">Mastered 22050 Hz In-Game Soundboard (sound/daniel/*.wav)</h3>
      <div class="btns">
        <button class="snd-btn" onclick="playWav('sound/daniel/dad_4am.wav')">🔊 "It's 4 in the morning, Daniel!"</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/sorry_table.wav')">🔊 "Sorry! Moving the table!"</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/table_drag.wav')">🔊 4 AM Table Scrape</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/ccc_chant.wav')">🔊 "CCC! C-C-C-C-C!"</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/ccc_burst.wav')">🔊 CCC Rapid Burst</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/shaaa_scream.wav')">🔊 "SHAAAAAAAAAAAA!"</button>
        <button class="snd-btn" onclick="playWav('sound/daniel/cant_see_webcam.wav')">🔊 "Justin Berry's Webcam!"</button>
      </div>
      <h3 style="margin:18px 0 8px;color:#93c5fd;">In-Game Quake Console Commands</h3>
      <ul style="margin:0;padding-left:18px;font-size:13.5px;line-height:1.65;color:#cbd5e1;">
        <li><code>impulse 26</code> — Summon 4 AM Daniel (dragging wooden table) + Furious 4 AM Dad chasing him + Framed Meme Poster!</li>
        <li><code>impulse 27</code> — Summon Solo Autonomous Daniel (cycles Table Ram, <code>ccc.md3</code> Yellow-C Barrage, SHAAA Sonic Blast, &amp; Webcam Toss)</li>
        <li><code>impulse 28</code> — Summon 360° Bakersfield LAN Station Daniel (Oak Table + <code>19990</code> Quake CRT + RGB Keyboard + QuickCam)</li>
        <li><code>impulse 29</code> — Summon Angry 4 AM Dad</li>
        <li><code>impulse 91</code> — Spawn Bakersfield LAN TV (<code>bk_tv</code> channels 8–11 play all 4 Daniel videos with audio!)</li>
        <li>Mystery Box (<code>mbox.qc</code>) — Slots <code>#27 Daniel (CCC)</code> &amp; <code>#28 4 AM Dad</code></li>
      </ul>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 12px;color:#fde68a;">360° Turntable Animated GIFs</h3>
    <div class="gifs">
      <img src="daniel_sprite/daniel_4am_table_360.gif" alt="4AM Table & Panic">
      <img src="daniel_sprite/daniel_ccc_shaaa_360.gif" alt="CCC & SHAAA">
      <img src="daniel_sprite/daniel_lan_station_360.gif" alt="LAN Station & Webcam">
      <img src="daniel_sprite/dad_4am_chase_360.gif" alt="4AM Dad Chase">
    </div>
  </div>

  <div class="card sheet">
    <h3 style="margin:0 0 12px;color:#fde68a;">Master 360° 8-Direction Turnaround Sheets</h3>
    <img src="daniel_sprite/daniel_360_turnaround_sheet.png" alt="Daniel Master Sheet" style="margin-bottom:14px;">
    <img src="daniel_sprite/dad_360_turnaround_sheet.png" alt="4AM Dad Master Sheet">
  </div>
</main>
<script>
const DIRS = ["0° Front","45° Front-L","90° Left","135° Back-L","180° Back","225° Back-R","270° Right","315° Front-R"];
const MODES = [
  {id:"daniel_table_move", label:"4 AM Moving Table", frames:8},
  {id:"daniel_sorry_panic", label:"Hands-Up 'Sorry!' Sprint", frames:8},
  {id:"daniel_ccc_barrage", label:"CCC! C-C-C-C Grin", frames:8},
  {id:"daniel_shaaa_rage", label:"SHAAAAAAAA! LAN Rage", frames:8},
  {id:"daniel_webcam_squint", label:"Justin Berry's Webcam", frames:8},
  {id:"daniel_lan_station", label:"360° LAN Station", frames:8},
  {id:"daniel_fast_run", label:"Daniel Fast Run", frames:8},
  {id:"daniel_idle", label:"Daniel Idle", frames:1},
  {id:"dad_run", label:"4 AM Dad Charge", frames:8},
  {id:"dad_idle", label:"4 AM Dad Idle", frames:1}
];
let curMode = MODES[0], curDir = 0, curFrame = 0, autoOrbit = true, tick = 0;
const imgEl = document.getElementById("spriteImg"), lblEl = document.getElementById("statusLbl");
const modeWrap = document.getElementById("modeBtns"), dirWrap = document.getElementById("dirBtns");

MODES.forEach((m, idx) => {
  const b = document.createElement("button");
  b.textContent = m.label;
  if (idx === 0) b.classList.add("active");
  b.onclick = () => {
    curMode = m;
    [...modeWrap.children].forEach(c => c.classList.remove("active"));
    b.classList.add("active");
    renderNow();
  };
  modeWrap.appendChild(b);
});

DIRS.forEach((dl, d) => {
  const b = document.createElement("button");
  b.textContent = dl;
  if (d === 0) b.classList.add("active");
  b.onclick = () => { autoOrbit = false; updateOrbitBtn(); setDir(d); };
  dirWrap.appendChild(b);
});

function setDir(d) {
  curDir = ((d % 8) + 8) % 8;
  [...dirWrap.children].forEach((c, i) => c.classList.toggle("active", i === curDir));
  renderNow();
}
function updateOrbitBtn() {
  const ob = document.getElementById("orbitToggle");
  ob.textContent = "Auto-Orbit 360°: " + (autoOrbit ? "ON" : "OFF");
  ob.classList.toggle("active", autoOrbit);
}
document.getElementById("orbitToggle").onclick = () => { autoOrbit = !autoOrbit; updateOrbitBtn(); };

function renderNow() {
  const f = curFrame % curMode.frames;
  imgEl.src = curMode.frames === 1
    ? `daniel_sprite/${curMode.id}_d${curDir}.png`
    : `daniel_sprite/${curMode.id}_d${curDir}_f${f}.png`;
  lblEl.textContent = `${curMode.label} · ${DIRS[curDir]} · Frame ${f}`;
}
setInterval(() => {
  curFrame = (curFrame + 1) % 8;
  tick++;
  if (autoOrbit && tick % 4 === 0) setDir(curDir + 1);
  else renderNow();
}, 85);

let dragX = null;
const st = document.getElementById("stage");
st.onpointerdown = e => { dragX = e.clientX; autoOrbit = false; updateOrbitBtn(); st.setPointerCapture(e.pointerId); };
st.onpointermove = e => { if (dragX !== null && Math.abs(e.clientX - dragX) > 26) { setDir(curDir + (e.clientX > dragX ? 1 : -1)); dragX = e.clientX; } };
st.onpointerup = () => { dragX = null; };

let curAudio = null;
function playWav(p) { if (curAudio) curAudio.pause(); curAudio = new Audio(p); curAudio.play(); }
</script>
</body>
</html>
"""
    (mod_dir / "daniel_sprites.html").write_text(html, encoding="utf-8")


def main() -> None:
    t0 = time.time()
    print("[1/5] Loading Daniel, 4 AM Dad, real-video expressions, & LAN studio props...")
    assets = load_all_daniel_assets()

    print("[2/5] Synthesizing full 8-direction x 8-frame 360° animations...")
    anims = build_all_daniel_animations(assets, n_frames=8)
    dn = anims["daniel"]
    dd = anims["dad"]

    web_dir = MOD_DIR / "daniel_sprite"
    progs_dir = MOD_DIR / "progs"
    web_dir.mkdir(parents=True, exist_ok=True)
    progs_dir.mkdir(parents=True, exist_ok=True)

    print("[3/5] Saving high-res 480x540 RGBA PNG frames to daniel_sprite/...")
    png_tasks: list[tuple[Path, np.ndarray]] = []
    for d in range(8):
        png_tasks.append((web_dir / f"daniel_idle_d{d}.png", dn["idle"][d]))
        for mode in MODES_7:
            for f in range(8):
                png_tasks.append((web_dir / f"daniel_{mode}_d{d}_f{f}.png", dn[mode][d][f]))
        png_tasks.append((web_dir / f"dad_idle_d{d}.png", dd["idle"][d]))
        for f in range(8):
            png_tasks.append((web_dir / f"dad_run_d{d}_f{f}.png", dd["run"][d][f]))

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        list(ex.map(_save_png, png_tasks))
    print(f"      Saved {len(png_tasks)} PNGs.")

    print("[4/5] Building HDR-pretoned DarkPlaces SPR32 sprites in progs/...")
    dn_raw_list: list[np.ndarray] = [dn["idle"][d] for d in range(8)]
    for mode in MODES_7:
        for d in range(8):
            for k in RUN_6_INDICES:
                dn_raw_list.append(dn[mode][d][k])
    assert len(dn_raw_list) == 344, f"Expected 344 Daniel frames, got {len(dn_raw_list)}"

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        dn_scaled = list(ex.map(lambda a: resize_rgba_premul(a, DN_SPR_W, DN_SPR_H), dn_raw_list))
    dn_toned = pretone_for_darkplaces_hdr(dn_scaled, target_mean_lum=62.0)
    dn_bytes, dn_lum = write_spr32(progs_dir / "daniel.spr32", dn_toned, DN_SPR_OX, DN_SPR_OY)
    print(f"      progs/daniel.spr32: {len(dn_toned)} frames ({DN_SPR_W}x{DN_SPR_H}, origin=({DN_SPR_OX},{DN_SPR_OY})), {dn_bytes / 1048576:.2f} MB, lum={dn_lum:.1f}")

    dd_raw_list: list[np.ndarray] = [dd["idle"][d] for d in range(8)]
    for d in range(8):
        for k in RUN_6_INDICES:
            dd_raw_list.append(dd["run"][d][k])
    assert len(dd_raw_list) == 56
    dd_scaled = [resize_rgba_premul(a, DD_SPR_W, DD_SPR_H) for a in dd_raw_list]
    dd_toned = pretone_for_darkplaces_hdr(dd_scaled, target_mean_lum=62.0)
    dd_bytes, dd_lum = write_spr32(progs_dir / "daniel_dad.spr32", dd_toned, DD_SPR_OX, DD_SPR_OY)
    print(f"      progs/daniel_dad.spr32: {len(dd_toned)} frames ({DD_SPR_W}x{DD_SPR_H}, origin=({DD_SPR_OX},{DD_SPR_OY})), {dd_bytes / 1048576:.2f} MB, lum={dd_lum:.1f}")

    print("[5/5] Exporting master 360° contact sheets, animated GIFs, & HTML showcase...")
    make_daniel_master_sheet(dn, web_dir / "daniel_360_turnaround_sheet.png")
    make_dad_master_sheet(dd, web_dir / "dad_360_turnaround_sheet.png")

    # GIF 1: 4 AM Moving Table -> Hands-Up Sorry Panic
    s1, l1 = [], []
    for step in range(32):
        d = (step // 2) % 8
        m = "table_move" if step < 16 else "sorry_panic"
        s1.append(dn[m][d][step % 8])
        l1.append(f"{'4 AM Moving Table' if step < 16 else 'Sorry! Hands-Up'} · {DIR_LABELS[d]}")
    save_orbit_gif(s1, l1, web_dir / "daniel_4am_table_360.gif")

    # GIF 2: CCC Grin Barrage -> SHAAA Neon LAN Scream
    s2, l2 = [], []
    for step in range(32):
        d = (step // 2) % 8
        m = "ccc_barrage" if step < 16 else "shaaa_rage"
        s2.append(dn[m][d][step % 8])
        l2.append(f"{'CCC! C-C-C-C!' if step < 16 else 'SHAAAAAAAA!'} · {DIR_LABELS[d]}")
    save_orbit_gif(s2, l2, web_dir / "daniel_ccc_shaaa_360.gif")

    # GIF 3: 360° LAN Station -> Justin Berry's Webcam
    s3, l3 = [], []
    for step in range(32):
        d = (step // 2) % 8
        m = "lan_station" if step < 16 else "webcam_squint"
        s3.append(dn[m][d][step % 8])
        l3.append(f"{'360 LAN Station' if step < 16 else 'Justin Webcam'} · {DIR_LABELS[d]}")
    save_orbit_gif(s3, l3, web_dir / "daniel_lan_station_360.gif")

    # GIF 4: Angry 4 AM Dad 360° Charge
    s4, l4 = [], []
    for step in range(24):
        d = (step // 3) % 8
        s4.append(dd["run"][d][step % 8])
        l4.append(f"4 AM Dad · {DIR_LABELS[d]}")
    save_orbit_gif(s4, l4, web_dir / "dad_4am_chase_360.gif")

    write_daniel_showcase_html(MOD_DIR)
    print(f"ALL DONE in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
