"""Builds both:
  1. The 100% self-contained single-file <canvas> 360° HTML inspector:
       G:\\Quake\\Combat\\BakersfieldQuake\\robeguy_monster_sprite.html
  2. The Antigravity Generative UI interactive HTML artifact (using semantic theme tokens
     and https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js).
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from robeguy_keying import STAGE_GY, STAGE_H, resize_rgba_premul

FW, FH = 320, 360
GY = round(float(STAGE_GY) * FH / float(STAGE_H))  # 327 px

ANIM_MODES_META = [
    {
        "id": "monster_idle",
        "num": 1,
        "tab": "1. 🦩😈 Unhinged Whisperer Idle (360°)",
        "short": "1. Whisperer Idle",
        "title": "Anim 1 — Unhinged 3 AM Flamingo Whisperer (8 Angles × 8f)",
        "desc": "Heavy feral crouch-breathing, glowing red eyes over Clubmaster sunglasses, and two fanged pocket-flamingos snapping across 360°.",
        "dirs": 8,
        "frames": 8,
        "fps": 10,
        "gy": GY,
        "snd": "monster_idle",
        "spr_range": "Frames 0..7 (key) & 56..119 (full 8×8)",
    },
    {
        "id": "berserker_charge",
        "num": 2,
        "tab": "2. 🏃‍♂️💨 Barefoot Berserker Charge (360°)",
        "short": "2. Berserker Charge",
        "title": "Anim 2 — 'STAY OFF MY LAWN!' Barefoot Bathrobe Berserker (8 Angles × 8f)",
        "desc": "High-cadence barefoot sprint, arms flung wide & pumping, roaring monster jaw, billowing pink flamingo robe skirt, dust puffs & trailing hot-pink feathers.",
        "dirs": 8,
        "frames": 8,
        "fps": 15,
        "gy": GY,
        "snd": "berserker_charge",
        "spr_range": "Frames 8..55 (mbox.qc 8×6 run)",
    },
    {
        "id": "robe_flash_laser",
        "num": 3,
        "tab": "3. ⚡🩲 Heart-Boxers Chest-Laser (360°)",
        "short": "3. Chest-Hair Laser",
        "title": "Anim 3 — The 'MY EYES!!' Heart-Boxers Chest-Hair Mega-Laser (8 Angles × 12f)",
        "desc": "Whips his pink flamingo bathrobe wide open like giant bat-wings revealing yellow red-heart boxer shorts while firing a volumetric hot-pink Chest-Hair Mega-Laser!",
        "dirs": 8,
        "frames": 12,
        "fps": 12,
        "gy": GY,
        "snd": "robe_flash_laser",
        "spr_range": "Frames 120..215 (8×12)",
    },
    {
        "id": "flamingo_attack",
        "num": 4,
        "tab": "4. ☕🦩 Lawn-Flamingo & Coffee Attack (360°)",
        "short": "4. Flamingo Rampage",
        "title": "Anim 4 — Dual Fanged Lawn-Flamingo & Hot-Coffee Rampage (8 Angles × 12f)",
        "desc": "Sloshes a spilling '#1 MONSTER' hot coffee mug in one hand while swinging a fanged plastic lawn-flamingo club & launching a laser-eyed torpedo flamingo missile!",
        "dirs": 8,
        "frames": 12,
        "fps": 13,
        "gy": GY,
        "snd": "flamingo_attack",
        "spr_range": "Frames 216..311 (8×12)",
    },
    {
        "id": "flamingo_gib_death",
        "num": 5,
        "tab": "5. 💥💀 Feather & Gib Explosion (24f)",
        "short": "5. Gib Explosion",
        "title": "Anim 5 — Catastrophic 4-Act Flamingo Feather & Quake Gib Explosion (24f)",
        "desc": "Crooked-sunglasses shock 'O' bloat -> Quake fireball + 48 fluttering pink feathers + 14 meaty gibs + panicked flying flamingos -> double-bouncing severed head -> smoking robe heap!",
        "dirs": 1,
        "frames": 24,
        "fps": 14,
        "gy": GY,
        "snd": "flamingo_gib_death",
        "spr_range": "Frames 312..335 (24f 4-Act Death)",
    },
]


def _encode_file_b64(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _encode_jpg_b64(path: Path, max_w: int = 1440, quality: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = int(round(im.height * (max_w / float(im.width))))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def pack_webp_atlases_b64(anims: dict, fw: int = FW, fh: int = FH, quality: int = 90) -> dict[str, str]:
    """Packs each animation in `anims` into a crisp premultiplied RGBA WebP data URI."""
    def _pack_one(meta: dict) -> tuple[str, str]:
        mid = meta["id"]
        nd = meta["dirs"]
        nf = meta["frames"]
        atlas = Image.new("RGBA", (fw * nf, fh * nd), (0, 0, 0, 0))
        data = anims[mid]
        for d in range(nd):
            row = data[d] if nd > 1 else data
            for f in range(nf):
                cell = resize_rgba_premul(row[f], fw, fh)
                atlas.paste(Image.fromarray(cell, "RGBA"), (f * fw, d * fh))
        buf = io.BytesIO()
        atlas.save(buf, format="WEBP", quality=quality, method=4)
        return mid, "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    with ThreadPoolExecutor(max_workers=min(5, os.cpu_count() or 4)) as ex:
        pairs = list(ex.map(_pack_one, ANIM_MODES_META))
    return dict(pairs)


def build_self_contained_robeguy_html(
    atlases_b64: dict[str, str],
    sound_paths: dict[str, Path],
    gif_paths: dict[str, Path],
    sheet_paths: dict[str, Path],
    out_html_path: Path,
) -> int:
    """Writes the 100% self-contained workspace showcase HTML (`robeguy_monster_sprite.html`)."""
    sounds_b64 = {k: _encode_file_b64(p, "audio/wav") for k, p in sound_paths.items()}
    gifs_b64 = {k: _encode_file_b64(p, "image/gif") for k, p in gif_paths.items()}
    sheets_b64 = {k: _encode_jpg_b64(p, max_w=1480, quality=90) for k, p in sheet_paths.items()}

    tools_dir = Path(__file__).resolve().parent.parent
    ref_front_b64 = _encode_jpg_b64(tools_dir / "out" / "chars" / "ref" / "robe_front.jpg", max_w=460, quality=85)
    ref_back_b64 = _encode_jpg_b64(tools_dir / "out" / "chars" / "ref" / "robe_back.jpg", max_w=380, quality=85)
    ref_heads_b64 = _encode_jpg_b64(tools_dir / "ref" / "robeguy" / "robe_monster_heads_2x2.jpg", max_w=540, quality=85)
    ref_props_b64 = _encode_jpg_b64(tools_dir / "ref" / "robeguy" / "flamingo_monster_props_2x2.jpg", max_w=540, quality=85)

    modes_json = json.dumps(ANIM_MODES_META, separators=(",", ":"))
    atlases_json = json.dumps(atlases_b64, separators=(",", ":"))
    sounds_json = json.dumps(sounds_b64, separators=(",", ":"))
    gpct = round(100.0 * GY / float(FH), 2)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pink Flamingo Bathrobe Monster ('Flamingo Fiend') — 360° Quake Sprite Inspector</title>
<style>
  :root {{
    --bg:#0d0b14; --panel:#171424; --panel2:#221d35; --ink:#f8fafc; --dim:#a39eb8;
    --pink:#ff3b9a; --pink2:#ff85c2; --gold:#fbbf24; --cyan:#38bdf8;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:18px 14px 56px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1080px; }}
  h1 {{ font-size:24px; margin:0 0 6px; font-weight:900; letter-spacing:-0.02em; color:#fff; }}
  h1 span {{ color:var(--pink); }}
  .sub {{ color:var(--dim); font-size:13.5px; margin:0; }}
  .sub code {{ color:#fbcfe8; background:#36152b; padding:2px 7px; border-radius:5px; font-weight:700; }}

  .tabs {{
    display:grid; grid-template-columns:repeat(auto-fit, minmax(195px, 1fr)); gap:8px;
    width:min(100%, 1080px); background:var(--panel); border:1px solid #332a4d;
    border-radius:14px; padding:10px;
  }}
  .tab {{
    padding:10px 12px; border-radius:10px; border:1.5px solid #352c52;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:750; font-size:13px;
    cursor:pointer; transition:all 0.14s ease; text-align:left;
  }}
  .tab:hover {{ border-color:#68529e; transform:translateY(-1px); }}
  .tab.on {{
    background:linear-gradient(135deg, #431234 0%, #2a133d 100%);
    border-color:var(--pink); color:#ffd6eb;
    box-shadow:0 0 18px rgba(255,59,154,0.28);
  }}

  .descbar {{
    width:min(100%, 1080px); background:var(--panel); border:1px solid #332a4d;
    border-radius:12px; padding:10px 16px; display:flex; flex-wrap:wrap;
    align-items:center; justify-content:space-between; gap:10px;
  }}
  .descbar b {{ color:var(--pink2); font-size:14.5px; }}
  .descbar span {{ color:var(--dim); font-size:13px; }}
  .sprpill {{
    background:#2a173b; border:1px solid #7e3af2; color:#e9d5ff;
    padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; white-space:nowrap;
  }}

  #stage {{
    width:min(100%, 1080px); height:min(64vh, 540px); min-height:380px;
    border-radius:16px; border:1.5px solid #3a2f59; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker {{ background:repeating-conic-gradient(#241f36 0% 25%, #191528 0% 50%) 0 0/24px 24px; }}
  #stage.quake   {{ background:radial-gradient(circle at 50% 72%, #442b21 0%, #1f1310 68%, #0c0807 100%); }}
  #stage.miami   {{ background:radial-gradient(circle at 50% 62%, #4c1438 0%, #1c1033 65%, #090714 100%); }}
  #stage.light   {{ background:#dce4f0; }}

  #wrap {{
    position:relative; height:94%; aspect-ratio:{FW}/{FH};
    display:flex; align-items:center; justify-content:center;
  }}
  canvas#cv {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  canvas#cv.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:5%; right:5%; top:{gpct}%; border-top:1.5px dashed rgba(251,191,36,0.88); }}
  .aline {{ position:absolute; top:4%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.7); }}
  .odot  {{ position:absolute; left:50%; top:{gpct}%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--gold); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(13,11,20,0.9);
    border:1px solid #4c3b73; border-radius:9px; padding:6px 12px;
    font-size:13px; font-weight:800; color:var(--pink2); pointer-events:none;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(13,11,20,0.88);
    border:1px solid #4c3b73; border-radius:9px; padding:6px 12px;
    font-size:12.5px; color:#cbd5e1; pointer-events:none; font-variant-numeric:tabular-nums;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(13,11,20,0.85);
    border:1px solid #382d54; border-radius:7px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none;
  }}

  .controls {{
    display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center;
    width:min(100%, 1080px); background:var(--panel); border:1px solid #332a4d;
    border-radius:12px; padding:10px 14px;
  }}
  button.ctrl {{
    background:var(--pink); color:#fff; border:0; border-radius:8px;
    padding:7px 14px; font:inherit; font-weight:750; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--cyan); color:#082f49; }}
  button.ctrl.alt  {{ background:#2c2545; color:var(--ink); border:1px solid #473b6b; font-weight:650; }}
  button.ctrl.snd  {{ background:#fbbf24; color:#1e1303; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; font-variant-numeric:tabular-nums; }}
  input[type=range] {{ accent-color:var(--pink); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:7px; width:min(100%, 1080px);
  }}
  @media (max-width:740px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:6px 4px; background:var(--panel); border:2px solid #2d2546;
    border-radius:10px; display:flex; flex-direction:column; align-items:center; gap:3px;
    color:var(--dim); font-size:12px; font-weight:750; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--pink); color:#fff; background:#2b1a38; }}
  #strip canvas {{ width:100%; aspect-ratio:{FW}/{FH}; display:block; }}

  .section {{
    width:min(100%, 1080px); background:var(--panel); border:1px solid #332a4d;
    border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:12px;
  }}
  .section h2 {{ margin:0; font-size:17px; color:#fff; }}
  .sndgrid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:8px; }}
  .gifgrid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(290px, 1fr)); gap:12px; }}
  .gifcard {{
    background:var(--panel2); border:1px solid #382e57; border-radius:10px;
    padding:10px; display:flex; flex-direction:column; gap:6px; align-items:center;
  }}
  .gifcard img {{ width:100%; border-radius:8px; display:block; }}
  .gifcard span {{ font-size:12.5px; font-weight:700; color:#f1f5f9; text-align:center; }}
  .sheetimg {{ width:100%; border-radius:10px; border:1px solid #382e57; display:block; }}
  .ba-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:12px; align-items:stretch; }}
  .ba-card {{
    background:var(--panel2); border:1px solid #382e57; border-radius:10px;
    padding:10px; display:flex; flex-direction:column; gap:6px; align-items:center; justify-content:space-between;
  }}
  .ba-card img {{ width:100%; max-height:280px; object-fit:contain; border-radius:8px; background:#120f1d; }}
  .ba-card span {{ font-size:12px; font-weight:700; color:#e2e8f0; text-align:center; }}
  table.spec {{ width:100%; border-collapse:collapse; font-size:13px; }}
  table.spec th, table.spec td {{ padding:8px 10px; border-bottom:1px solid #2f274a; text-align:left; }}
  table.spec th {{ color:var(--pink2); font-weight:800; background:#1e1830; }}
  table.spec code {{ color:#fde68a; background:#2e2312; padding:2px 6px; border-radius:4px; }}
</style>
</head>
<body>
  <header>
    <h1>🦩😈 <span>THE FLAMINGO FIEND</span> — 360° Quake Monster Sprite</h1>
    <p class="sub">Digitized Pink Flamingo Bathrobe Monster &bull; <code>progs/robeguy.spr32</code> (336 HDR Pre-Toned Tight-Cropped Frames) &bull; 5 Hilarious Animations + Custom Monster Soundboard</p>
  </header>

  <div class="tabs" id="tabs"></div>

  <div class="descbar">
    <div>
      <b id="dtitle"></b><br>
      <span id="ddesc"></span>
    </div>
    <div class="sprpill" id="dspr"></div>
  </div>

  <div id="stage" class="checker">
    <div id="badge">0° Front</div>
    <div id="meta">Frame 0/7</div>
    <div id="wrap">
      <canvas id="cv" width="{FW}" height="{FH}"></canvas>
      <div id="reticle">
        <div class="gline"></div>
        <div class="aline"></div>
        <div class="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag stage horizontally to orbit 360° &bull; Keys 1-5 switch animation</div>
  </div>

  <div class="controls">
    <button class="ctrl" id="playBtn">Pause</button>
    <button class="ctrl alt" id="prevBtn">◀ Step</button>
    <button class="ctrl alt" id="nextBtn">Step ▶</button>
    <button class="ctrl spin" id="spinBtn">Auto-Spin 360°: ON</button>
    <button class="ctrl snd" id="sfxBtn">🔊 Play Monster SFX</button>
    <label>Angle <input id="angSlider" type="range" min="0" max="7" value="0" style="width:105px"></label>
    <label>FPS <span id="fpsVal">12</span> <input id="fpsSlider" type="range" min="4" max="24" value="12" style="width:90px"></label>
    <button class="ctrl alt" id="pixBtn">Filter: Smooth</button>
    <button class="ctrl alt" id="origBtn">Origin: OFF</button>
    <button class="ctrl alt" id="bgBtn">BG: Checker</button>
  </div>

  <div id="strip"></div>

  <div class="section">
    <h2>🔊 Custom Monster Soundboard (5 Synthesized WAVs in <code>sound/robeguy/</code>)</h2>
    <div class="sndgrid" id="sndgrid"></div>
  </div>

  <div class="section">
    <h2>🎞️ Animated Showcase GIFs</h2>
    <div class="gifgrid">
      <div class="gifcard"><img src="{gifs_b64['showcase']}" alt="All 5 Showcase"><span>All 5 Monster Animations Reel</span></div>
      <div class="gifcard"><img src="{gifs_b64['berserker_charge']}" alt="Berserker Charge"><span>Anim 2: 360° Barefoot Berserker Charge</span></div>
      <div class="gifcard"><img src="{gifs_b64['robe_flash_laser']}" alt="Chest Laser"><span>Anim 3: Heart-Boxers Chest-Hair Mega-Laser</span></div>
      <div class="gifcard"><img src="{gifs_b64['flamingo_attack']}" alt="Flamingo Attack"><span>Anim 4: Lawn-Flamingo &amp; Hot-Coffee Rampage</span></div>
      <div class="gifcard"><img src="{gifs_b64['flamingo_gib_death']}" alt="Gib Death"><span>Anim 5: 4-Act Feather &amp; Gib Explosion</span></div>
      <div class="gifcard"><img src="{gifs_b64['monster_idle']}" alt="Monster Idle"><span>Anim 1: 360° Unhinged Flamingo Whisperer</span></div>
    </div>
  </div>

  <div class="section">
    <h2>📸 Source DSLR Photos → Monster Transformation Studio Plates</h2>
    <div class="ba-grid">
      <div class="ba-card"><img src="{ref_front_b64}" alt="Original Front Photo"><span>Input Photo 1: Front Bathrobe DSLR</span></div>
      <div class="ba-card"><img src="{ref_back_b64}" alt="Original Back Photo"><span>Input Photo 2: Back Hooded DSLR</span></div>
      <div class="ba-card"><img src="{ref_heads_b64}" alt="Monster Portraits"><span>Synthesized Monster Expressions (2×2)</span></div>
      <div class="ba-card"><img src="{ref_props_b64}" alt="Monster Props"><span>Fanged Flamingos, Coffee Mug &amp; Robe Pile</span></div>
    </div>
  </div>

  <div class="section">
    <h2>🖼️ Master 5-Animation Contact Sheet &amp; 360° Turnaround Sheet</h2>
    <img class="sheetimg" src="{sheets_b64['five_anims']}" alt="5 Animations Sheet">
    <img class="sheetimg" src="{sheets_b64['turnaround']}" alt="360 Turnaround Sheet">
  </div>

  <div class="section">
    <h2>🕹️ DarkPlaces Quake <code>progs/robeguy.spr32</code> Frame Bank Map (336 Tight-Cropped Frames)</h2>
    <table class="spec">
      <thead><tr><th>Frame Range</th><th>Formula</th><th>Frames</th><th>Monster Animation &amp; Synthesized Audio</th></tr></thead>
      <tbody>
        <tr><td><code>0..7</code></td><td><code>d</code> (0..7)</td><td>8</td><td>8-Direction Standing Monster Idle Keyposes (<code>mbox.qc</code> compatible)</td></tr>
        <tr><td><code>8..55</code></td><td><code>8 + d*6 + k</code></td><td>48</td><td><b>Anim 2</b>: 8-Dir × 6f Barefoot Bathrobe Berserker Charge &bull; <code>berserker_yell.wav</code></td></tr>
        <tr><td><code>56..119</code></td><td><code>56 + d*8 + k</code></td><td>64</td><td><b>Anim 1</b>: 8-Dir × 8f Unhinged 3 AM Flamingo Whisperer Idle &bull; <code>idle_honk_growl.wav</code></td></tr>
        <tr><td><code>120..215</code></td><td><code>120 + d*12 + k</code></td><td>96</td><td><b>Anim 3</b>: 8-Dir × 12f Heart-Boxers Chest-Hair Mega-Laser &bull; <code>chest_laser_flash.wav</code></td></tr>
        <tr><td><code>216..311</code></td><td><code>216 + d*12 + k</code></td><td>96</td><td><b>Anim 4</b>: 8-Dir × 12f Dual Lawn-Flamingo Club &amp; Hot-Coffee Rampage &bull; <code>flamingo_whack.wav</code></td></tr>
        <tr><td><code>312..335</code></td><td><code>312 + s</code> (0..23)</td><td>24</td><td><b>Anim 5</b>: 4-Act Catastrophic Flamingo Feather &amp; Quake Gib Explosion &bull; <code>feather_gib_boom.wav</code></td></tr>
      </tbody>
    </table>
  </div>

<script>
const FW = {FW}, FH = {FH};
const MODES = {modes_json};
const ATLAS_URI = {atlases_json};
const SOUNDS_URI = {sounds_json};
const DIR_LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];

const atlasImgs = {{}};
let loadedCount = 0;
MODES.forEach(m => {{
  const im = new Image();
  im.onload = () => {{ loadedCount++; render(); updateStrip(); }};
  im.src = ATLAS_URI[m.id];
  atlasImgs[m.id] = im;
}});

const audioBank = {{}};
Object.keys(SOUNDS_URI).forEach(k => {{
  audioBank[k] = new Audio(SOUNDS_URI[k]);
}});
function playSfx(key) {{
  const a = audioBank[key];
  if (!a) return;
  a.currentTime = 0;
  a.play().catch(() => {{}});
}}

let curIdx = 0, curDir = 0, curFrame = 0, playing = true, autoSpin = true;
let pixelMode = false, showOrigin = false, bgIdx = 0;
const bgs = ["checker", "miami", "quake", "light"];
const bgNames = ["Checker", "Neon Miami", "Quake Dungeon", "Light"];

const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const tabsEl = document.getElementById("tabs"), stripEl = document.getElementById("strip");
const badgeEl = document.getElementById("badge"), metaEl = document.getElementById("meta");
const dtitleEl = document.getElementById("dtitle"), ddescEl = document.getElementById("ddesc"), dsprEl = document.getElementById("dspr");
const stageEl = document.getElementById("stage"), reticleEl = document.getElementById("reticle");
const playBtn = document.getElementById("playBtn"), spinBtn = document.getElementById("spinBtn");
const angSlider = document.getElementById("angSlider"), fpsSlider = document.getElementById("fpsSlider"), fpsVal = document.getElementById("fpsVal");

const tabBtns = MODES.map((m, i) => {{
  const b = document.createElement("button");
  b.className = "tab" + (i === 0 ? " on" : "");
  b.textContent = m.tab;
  b.onclick = () => selectMode(i, true);
  tabsEl.appendChild(b);
  return b;
}});

const sndGrid = document.getElementById("sndgrid");
MODES.forEach(m => {{
  const b = document.createElement("button");
  b.className = "ctrl alt";
  b.textContent = "🔊 " + m.short;
  b.onclick = () => playSfx(m.snd);
  sndGrid.appendChild(b);
}});

const stripBtns = [], stripCtxs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  const scv = document.createElement("canvas");
  scv.width = FW; scv.height = FH;
  const sp = document.createElement("span");
  sp.textContent = DIR_LABELS[d];
  b.appendChild(scv); b.appendChild(sp);
  b.onclick = () => {{ curDir = d; autoSpin = false; syncUI(); render(); }};
  stripEl.appendChild(b);
  stripBtns.push(b);
  stripCtxs.push(scv.getContext("2d"));
}}

function selectMode(idx, triggerAudio) {{
  curIdx = idx;
  curFrame = 0;
  const m = MODES[curIdx];
  fpsSlider.value = m.fps;
  fpsVal.textContent = m.fps;
  if (m.dirs === 1) curDir = 0;
  syncUI();
  updateStrip();
  render();
  if (triggerAudio) playSfx(m.snd);
}}

function syncUI() {{
  const m = MODES[curIdx];
  tabBtns.forEach((b, i) => b.classList.toggle("on", i === curIdx));
  dtitleEl.textContent = m.title;
  ddescEl.textContent = m.desc;
  dsprEl.textContent = "robeguy.spr32 · " + m.spr_range;
  playBtn.textContent = playing ? "Pause" : "Play";
  spinBtn.textContent = m.dirs > 1 ? `Auto-Spin 360°: ${{autoSpin ? "ON" : "OFF"}}` : "Fixed Camera (24f Death)";
  angSlider.disabled = (m.dirs === 1);
  angSlider.value = curDir;
  stripEl.style.display = m.dirs > 1 ? "grid" : "none";
  stripBtns.forEach((b, d) => b.classList.toggle("on", d === curDir));
}}

function updateStrip() {{
  const m = MODES[curIdx];
  const im = atlasImgs[m.id];
  if (!im || !im.complete || m.dirs === 1) return;
  const sampleF = Math.min(m.frames - 1, m.id === "robe_flash_laser" || m.id === "flamingo_attack" ? 5 : 1);
  for (let d = 0; d < 8; d++) {{
    const sctx = stripCtxs[d];
    sctx.clearRect(0, 0, FW, FH);
    sctx.drawImage(im, sampleF * FW, d * FH, FW, FH, 0, 0, FW, FH);
  }}
}}

function render() {{
  const m = MODES[curIdx];
  const im = atlasImgs[m.id];
  ctx.clearRect(0, 0, FW, FH);
  const dUse = m.dirs > 1 ? curDir : 0;
  const fUse = curFrame % m.frames;
  if (im && im.complete) {{
    ctx.imageSmoothingEnabled = !pixelMode;
    ctx.drawImage(im, fUse * FW, dUse * FH, FW, FH, 0, 0, FW, FH);
  }}
  badgeEl.textContent = m.dirs > 1 ? DIR_LABELS[dUse] : `Act ${{fUse < 5 ? 1 : (fUse < 12 ? 2 : (fUse < 19 ? 3 : 4))}} / 4 — Explosion Spectacle`;
  metaEl.textContent = `Frame ${{fUse + 1}}/${{m.frames}} · ${{fpsSlider.value}} FPS`;
}}

playBtn.onclick = () => {{ playing = !playing; syncUI(); }};
document.getElementById("prevBtn").onclick = () => {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame - 1 + m.frames) % m.frames; syncUI(); render(); }};
document.getElementById("nextBtn").onclick = () => {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame + 1) % m.frames; syncUI(); render(); }};
spinBtn.onclick = () => {{ if (MODES[curIdx].dirs > 1) {{ autoSpin = !autoSpin; syncUI(); }} }};
document.getElementById("sfxBtn").onclick = () => playSfx(MODES[curIdx].snd);
angSlider.oninput = () => {{ curDir = +angSlider.value; autoSpin = false; syncUI(); render(); }};
fpsSlider.oninput = () => {{ fpsVal.textContent = fpsSlider.value; render(); }};
document.getElementById("pixBtn").onclick = (e) => {{
  pixelMode = !pixelMode;
  cv.classList.toggle("pixel", pixelMode);
  e.target.textContent = `Filter: ${{pixelMode ? "Nearest" : "Smooth"}}`;
  render();
}};
document.getElementById("origBtn").onclick = (e) => {{
  showOrigin = !showOrigin;
  reticleEl.classList.toggle("on", showOrigin);
  e.target.textContent = `Origin: ${{showOrigin ? "ON" : "OFF"}}`;
}};
document.getElementById("bgBtn").onclick = (e) => {{
  stageEl.classList.remove(bgs[bgIdx]);
  bgIdx = (bgIdx + 1) % bgs.length;
  stageEl.classList.add(bgs[bgIdx]);
  e.target.textContent = `BG: ${{bgNames[bgIdx]}}`;
}};

// Drag horizontally to spin 360°
let dragX = null, dragStartDir = 0;
stageEl.addEventListener("pointerdown", e => {{
  dragX = e.clientX; dragStartDir = curDir;
  stageEl.classList.add("drag"); stageEl.setPointerCapture(e.pointerId);
}});
stageEl.addEventListener("pointermove", e => {{
  if (dragX === null || MODES[curIdx].dirs === 1) return;
  const steps = Math.round((e.clientX - dragX) / 42);
  const nd = ((dragStartDir - steps) % 8 + 8) % 8;
  if (nd !== curDir) {{ curDir = nd; autoSpin = false; syncUI(); render(); }}
}});
stageEl.addEventListener("pointerup", () => {{ dragX = null; stageEl.classList.remove("drag"); }});

window.addEventListener("keydown", e => {{
  if (e.key >= "1" && e.key <= "5") selectMode(+e.key - 1, true);
  else if (e.key === " ") {{ e.preventDefault(); playing = !playing; syncUI(); }}
  else if (e.key === "ArrowLeft" && MODES[curIdx].dirs > 1) {{ curDir = (curDir + 7) % 8; autoSpin = false; syncUI(); render(); }}
  else if (e.key === "ArrowRight" && MODES[curIdx].dirs > 1) {{ curDir = (curDir + 1) % 8; autoSpin = false; syncUI(); render(); }}
  else if (e.key === "ArrowUp") {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame + 1) % m.frames; syncUI(); render(); }}
  else if (e.key === "ArrowDown") {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame - 1 + m.frames) % m.frames; syncUI(); render(); }}
}});

let lastTick = 0, spinAccum = 0;
function loop(ts) {{
  const fps = +fpsSlider.value || 12;
  if (playing && ts - lastTick >= 1000 / fps) {{
    lastTick = ts;
    const m = MODES[curIdx];
    curFrame = (curFrame + 1) % m.frames;
    if (autoSpin && m.dirs > 1) {{
      spinAccum++;
      const holdFrames = Math.max(4, Math.round(m.frames * 0.5));
      if (spinAccum >= holdFrames) {{
        spinAccum = 0;
        curDir = (curDir + 1) % 8;
        syncUI();
      }}
    }}
    render();
  }}
  requestAnimationFrame(loop);
}}
selectMode(0, false);
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
    out_html_path.parent.mkdir(parents=True, exist_ok=True)
    out_html_path.write_text(html, encoding="utf-8")
    return out_html_path.stat().st_size


def build_antigravity_artifact_html(
    atlases_b64: dict[str, str],
    sound_paths: dict[str, Path],
) -> str:
    """Returns a clean Antigravity Generative UI interactive HTML document adhering strictly
    to semantic CSS variables (`--background`, `--card`, `--foreground`, `--border`, etc.)
    and `https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js`."""
    sounds_b64 = {k: _encode_file_b64(p, "audio/wav") for k, p in sound_paths.items()}
    modes_json = json.dumps(ANIM_MODES_META, separators=(",", ":"))
    atlases_json = json.dumps(atlases_b64, separators=(",", ":"))
    sounds_json = json.dumps(sounds_b64, separators=(",", ":"))
    gpct = round(100.0 * GY / float(FH), 2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Flamingo Fiend — Interactive 360° Monster Sprite Studio</title>
<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
<style>
  .stage-checker {{
    background: repeating-conic-gradient(rgba(128,128,145,0.16) 0% 25%, rgba(64,64,78,0.06) 0% 50%) 0 0 / 24px 24px;
  }}
  .stage-dungeon {{
    background: radial-gradient(circle at 50% 72%, #442b21 0%, #1e1310 70%, #0d0807 100%);
  }}
  .stage-miami {{
    background: radial-gradient(circle at 50% 62%, #52153d 0%, #1d1036 68%, #0a0715 100%);
  }}
  .pixelated {{ image-rendering: pixelated; }}
</style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-4 sm:p-6 select-none">
  <div class="max-w-5xl mx-auto flex flex-col gap-4">
    <!-- Header -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-lg sm:text-xl font-bold tracking-tight">🦩😈 The Flamingo Fiend — 360° Quake Monster Sprite</h1>
        <p class="text-xs sm:text-sm text-[var(--muted-foreground)] mt-0.5">
          5 Hilarious Monster Animations &bull; <code class="font-mono text-[var(--primary)]">progs/robeguy.spr32</code> (336 HDR Pre-Toned Frames)
        </p>
      </div>
      <button id="sfxMainBtn" class="px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold bg-pink-600 hover:bg-pink-500 text-white transition cursor-pointer">
        🔊 Play Animation SFX
      </button>
    </div>

    <!-- 5 Animation Selector Cards -->
    <div id="modeTabs" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2"></div>

    <!-- Active Animation Description Banner -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-2">
      <div class="min-w-0">
        <div id="animTitle" class="text-sm font-bold text-[var(--foreground)]"></div>
        <div id="animDesc" class="text-xs text-[var(--muted-foreground)] mt-0.5"></div>
      </div>
      <span id="sprRange" class="text-xs font-mono font-semibold px-2.5 py-1 rounded-md bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] shrink-0"></span>
    </div>

    <!-- Interactive 360° Stage -->
    <div id="stage" class="relative w-full h-[420px] sm:h-[470px] rounded-xl border border-[var(--border)] stage-checker flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing touch-none">
      <div id="angleBadge" class="absolute top-3 left-3 px-3 py-1.5 rounded-lg bg-[var(--card)]/90 border border-[var(--border)] text-xs font-bold tabular-nums">
        0° Front
      </div>
      <div id="frameBadge" class="absolute top-3 right-3 px-3 py-1.5 rounded-lg bg-[var(--card)]/90 border border-[var(--border)] text-xs text-[var(--muted-foreground)] font-mono tabular-nums">
        Frame 1/8
      </div>
      <div class="relative h-[93%]" style="aspect-ratio:{FW}/{FH};">
        <canvas id="cv" width="{FW}" height="{FH}" class="w-full h-full object-contain pointer-events-none"></canvas>
        <div id="reticle" class="hidden absolute inset-0 pointer-events-none">
          <div style="top:{gpct}%;" class="absolute left-3 right-3 border-t border-dashed border-amber-400"></div>
          <div class="absolute top-3 bottom-2 left-1/2 border-l border-dashed border-sky-400"></div>
          <div style="top:{gpct}%;" class="absolute left-1/2 w-2.5 h-2.5 -ml-1.5 -mt-1.5 rounded-full bg-amber-400 ring-2 ring-black"></div>
        </div>
      </div>
      <div class="absolute bottom-2.5 right-3 px-2.5 py-1 rounded-md bg-[var(--card)]/85 border border-[var(--border)] text-xs text-[var(--muted-foreground)] pointer-events-none">
        ↔ Drag stage to spin 360° &bull; Keys 1–5 switch anim
      </div>
    </div>

    <!-- Playback & Camera Toolbar -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 flex flex-wrap items-center justify-center gap-2.5 text-xs">
      <button id="playBtn" class="px-3.5 py-1.5 rounded-lg font-semibold bg-pink-600 hover:bg-pink-500 text-white cursor-pointer">Pause</button>
      <button id="prevBtn" class="px-3 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">◀ Step</button>
      <button id="nextBtn" class="px-3 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">Step ▶</button>
      <button id="spinBtn" class="px-3.5 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">Auto-Spin 360°: ON</button>
      <label class="flex items-center gap-2 text-[var(--muted-foreground)] font-medium px-2">
        Angle
        <input id="angSlider" type="range" min="0" max="7" value="0" class="w-24 accent-pink-500 cursor-pointer">
      </label>
      <label class="flex items-center gap-2 text-[var(--muted-foreground)] font-medium px-2 tabular-nums">
        FPS <span id="fpsVal" class="text-[var(--foreground)] font-semibold">10</span>
        <input id="fpsSlider" type="range" min="4" max="24" value="10" class="w-20 accent-pink-500 cursor-pointer">
      </label>
      <button id="origBtn" class="px-3 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">Origin: OFF</button>
      <button id="pixBtn" class="px-3 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">Filter: Smooth</button>
      <button id="bgBtn" class="px-3 py-1.5 rounded-lg font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] cursor-pointer">BG: Checker</button>
    </div>

    <!-- 8-Direction Quick Orbit Strip -->
    <div id="strip" class="grid grid-cols-4 sm:grid-cols-8 gap-2"></div>
  </div>

<script>
const FW = {FW}, FH = {FH};
const MODES = {modes_json};
const ATLAS_URI = {atlases_json};
const SOUNDS_URI = {sounds_json};
const DIR_LABELS = ["0° Front", "45° FL", "90° Left", "135° BL", "180° Back", "225° BR", "270° Right", "315° FR"];

const atlasImgs = {{}};
MODES.forEach(m => {{
  const im = new Image();
  im.onload = () => {{ render(); updateStrip(); }};
  im.src = ATLAS_URI[m.id];
  atlasImgs[m.id] = im;
}});

const audioBank = {{}};
Object.keys(SOUNDS_URI).forEach(k => {{ audioBank[k] = new Audio(SOUNDS_URI[k]); }});
function playSfx(k) {{
  const a = audioBank[k];
  if (!a) return;
  a.currentTime = 0;
  a.play().catch(() => {{}});
}}

let curIdx = 0, curDir = 0, curFrame = 0, playing = true, autoSpin = true;
let showOrigin = false, pixelMode = false, bgIdx = 0;
const bgClasses = ["stage-checker", "stage-miami", "stage-dungeon"];
const bgNames = ["Checker", "Neon Miami", "Quake Dungeon"];

const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const modeTabs = document.getElementById("modeTabs"), stripEl = document.getElementById("strip");
const stageEl = document.getElementById("stage"), reticleEl = document.getElementById("reticle");
const angleBadge = document.getElementById("angleBadge"), frameBadge = document.getElementById("frameBadge");
const animTitle = document.getElementById("animTitle"), animDesc = document.getElementById("animDesc"), sprRange = document.getElementById("sprRange");
const playBtn = document.getElementById("playBtn"), spinBtn = document.getElementById("spinBtn");
const angSlider = document.getElementById("angSlider"), fpsSlider = document.getElementById("fpsSlider"), fpsVal = document.getElementById("fpsVal");

const tabBtns = MODES.map((m, i) => {{
  const b = document.createElement("button");
  b.className = "px-3 py-2.5 rounded-xl border text-left text-xs font-bold transition cursor-pointer";
  b.textContent = m.short;
  b.onclick = () => selectMode(i, true);
  modeTabs.appendChild(b);
  return b;
}});

const stripBtns = [], stripCtxs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  b.className = "p-1.5 rounded-lg border bg-[var(--card)] flex flex-col items-center gap-1 text-xs font-semibold cursor-pointer transition";
  const scv = document.createElement("canvas");
  scv.width = FW; scv.height = FH;
  scv.className = "w-full h-auto block";
  const sp = document.createElement("span");
  sp.textContent = DIR_LABELS[d];
  b.appendChild(scv); b.appendChild(sp);
  b.onclick = () => {{ curDir = d; autoSpin = false; syncUI(); render(); }};
  stripEl.appendChild(b);
  stripBtns.push(b);
  stripCtxs.push(scv.getContext("2d"));
}}

function selectMode(idx, withAudio) {{
  curIdx = idx; curFrame = 0;
  const m = MODES[curIdx];
  fpsSlider.value = m.fps; fpsVal.textContent = m.fps;
  if (m.dirs === 1) curDir = 0;
  syncUI(); updateStrip(); render();
  if (withAudio) playSfx(m.snd);
}}

function syncUI() {{
  const m = MODES[curIdx];
  tabBtns.forEach((b, i) => {{
    if (i === curIdx) {{
      b.className = "px-3 py-2.5 rounded-xl border-2 border-pink-500 bg-pink-500/15 text-[var(--foreground)] text-left text-xs font-bold transition cursor-pointer";
    }} else {{
      b.className = "px-3 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] text-left text-xs font-semibold transition cursor-pointer";
    }}
  }});
  animTitle.textContent = m.title;
  animDesc.textContent = m.desc;
  sprRange.textContent = m.spr_range;
  playBtn.textContent = playing ? "Pause" : "Play";
  spinBtn.textContent = m.dirs > 1 ? `Auto-Spin 360°: ${{autoSpin ? "ON" : "OFF"}}` : "Fixed Camera (24f)";
  angSlider.disabled = (m.dirs === 1);
  angSlider.value = curDir;
  stripEl.style.display = m.dirs > 1 ? "grid" : "none";
  stripBtns.forEach((b, d) => {{
    b.style.borderColor = (d === curDir) ? "#ec4899" : "var(--border)";
  }});
}}

function updateStrip() {{
  const m = MODES[curIdx];
  const im = atlasImgs[m.id];
  if (!im || !im.complete || m.dirs === 1) return;
  const sf = Math.min(m.frames - 1, (m.id === "robe_flash_laser" || m.id === "flamingo_attack") ? 5 : 1);
  for (let d = 0; d < 8; d++) {{
    stripCtxs[d].clearRect(0, 0, FW, FH);
    stripCtxs[d].drawImage(im, sf * FW, d * FH, FW, FH, 0, 0, FW, FH);
  }}
}}

function render() {{
  const m = MODES[curIdx];
  const im = atlasImgs[m.id];
  ctx.clearRect(0, 0, FW, FH);
  const dUse = m.dirs > 1 ? curDir : 0;
  const fUse = curFrame % m.frames;
  if (im && im.complete) {{
    ctx.imageSmoothingEnabled = !pixelMode;
    ctx.drawImage(im, fUse * FW, dUse * FH, FW, FH, 0, 0, FW, FH);
  }}
  angleBadge.textContent = m.dirs > 1 ? DIR_LABELS[dUse] : `Act ${{fUse < 5 ? 1 : (fUse < 12 ? 2 : (fUse < 19 ? 3 : 4))}}/4`;
  frameBadge.textContent = `Frame ${{fUse + 1}}/${{m.frames}} · ${{fpsSlider.value}} FPS`;
}}

playBtn.onclick = () => {{ playing = !playing; syncUI(); }};
document.getElementById("prevBtn").onclick = () => {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame - 1 + m.frames) % m.frames; syncUI(); render(); }};
document.getElementById("nextBtn").onclick = () => {{ playing = false; const m = MODES[curIdx]; curFrame = (curFrame + 1) % m.frames; syncUI(); render(); }};
spinBtn.onclick = () => {{ if (MODES[curIdx].dirs > 1) {{ autoSpin = !autoSpin; syncUI(); }} }};
document.getElementById("sfxMainBtn").onclick = () => playSfx(MODES[curIdx].snd);
angSlider.oninput = () => {{ curDir = +angSlider.value; autoSpin = false; syncUI(); render(); }};
fpsSlider.oninput = () => {{ fpsVal.textContent = fpsSlider.value; render(); }};
document.getElementById("origBtn").onclick = e => {{
  showOrigin = !showOrigin;
  reticleEl.classList.toggle("hidden", !showOrigin);
  e.target.textContent = `Origin: ${{showOrigin ? "ON" : "OFF"}}`;
}};
document.getElementById("pixBtn").onclick = e => {{
  pixelMode = !pixelMode;
  cv.classList.toggle("pixelated", pixelMode);
  e.target.textContent = `Filter: ${{pixelMode ? "Nearest" : "Smooth"}}`;
  render();
}};
document.getElementById("bgBtn").onclick = e => {{
  stageEl.classList.remove(bgClasses[bgIdx]);
  bgIdx = (bgIdx + 1) % bgClasses.length;
  stageEl.classList.add(bgClasses[bgIdx]);
  e.target.textContent = `BG: ${{bgNames[bgIdx]}}`;
}};

let dragX = null, startDir = 0;
stageEl.addEventListener("pointerdown", e => {{ dragX = e.clientX; startDir = curDir; stageEl.setPointerCapture(e.pointerId); }});
stageEl.addEventListener("pointermove", e => {{
  if (dragX === null || MODES[curIdx].dirs === 1) return;
  const steps = Math.round((e.clientX - dragX) / 40);
  const nd = ((startDir - steps) % 8 + 8) % 8;
  if (nd !== curDir) {{ curDir = nd; autoSpin = false; syncUI(); render(); }}
}});
stageEl.addEventListener("pointerup", () => {{ dragX = null; }});

window.addEventListener("keydown", e => {{
  if (e.key >= "1" && e.key <= "5") selectMode(+e.key - 1, true);
  else if (e.key === " ") {{ e.preventDefault(); playing = !playing; syncUI(); }}
  else if (e.key === "ArrowLeft" && MODES[curIdx].dirs > 1) {{ curDir = (curDir + 7) % 8; autoSpin = false; syncUI(); render(); }}
  else if (e.key === "ArrowRight" && MODES[curIdx].dirs > 1) {{ curDir = (curDir + 1) % 8; autoSpin = false; syncUI(); render(); }}
}});

let lastTick = 0, spinAcc = 0;
function loop(ts) {{
  const fps = +fpsSlider.value || 10;
  if (playing && ts - lastTick >= 1000 / fps) {{
    lastTick = ts;
    const m = MODES[curIdx];
    curFrame = (curFrame + 1) % m.frames;
    if (autoSpin && m.dirs > 1) {{
      spinAcc++;
      if (spinAcc >= Math.max(4, Math.round(m.frames * 0.5))) {{
        spinAcc = 0;
        curDir = (curDir + 1) % 8;
        syncUI();
      }}
    }}
    render();
  }}
  requestAnimationFrame(loop);
}}
selectMode(0, false);
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
