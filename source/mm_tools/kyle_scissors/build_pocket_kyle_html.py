"""Build the polished, high-FPS (48 FPS, 224 frames) interactive 2D FPS Viewmodel Showcase
+ Live Quake POV Adjuster for #1 — THE POCKET KYLE (docs/kyle_weapon_showcase.html).

Packs all 224 RGBA frames (96 Idle + 48 Lock + 56 Fire + 24 Draw) as high-quality WebP sprite sheets
plus synchronized scissor SNIP, lock-on SHING, whoosh, cash flutter, and Kyle voice WAVs
(with ZERO "Will stole my clients" clips, quiet chillin' Idle, and "Whoa man" Draw voices).
"""

import base64
import io
import json
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ARTIFACT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
IN_DIR = os.path.join(ARTIFACT_ROOT, "pocket_kyle_hd")
CLIPS_DIR = os.path.join(ARTIFACT_ROOT, "clips")
SFX_DIR = os.path.join(ARTIFACT_ROOT, "sfx")
OUT_HTML = os.path.join(REPO, "docs", "kyle_weapon_showcase.html")


def pack_webp_pages(paths, quality=88, max_dim=3840):
    ims = [Image.open(p).convert("RGBA") for p in paths]
    fw, fh = ims[0].size
    max_cols = max(1, min(len(ims), max_dim // fw))
    max_rows = max(1, max_dim // fh)
    per_page = max_cols * max_rows
    pages = []
    for start in range(0, len(ims), per_page):
        chunk = ims[start:start + per_page]
        cols = min(max_cols, len(chunk))
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
        for idx, im in enumerate(chunk):
            r, c = divmod(idx, cols)
            sheet.paste(im, (c * fw, r * fh))
        buf = io.BytesIO()
        sheet.save(buf, format="WEBP", quality=quality, method=4)
        pages.append({
            "start": start,
            "count": len(chunk),
            "cols": cols,
            "rows": rows,
            "url": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
        })
    return {"fw": fw, "fh": fh, "count": len(ims), "pages": pages}


def wav_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("ascii")


def main():
    with open(os.path.join(IN_DIR, "manifest.json"), "r", encoding="utf-8") as fh:
        m = json.load(fh)

    idle_atlas = pack_webp_pages([os.path.join(IN_DIR, f) for f in m["idle"]], quality=88)
    lock_atlas = pack_webp_pages([os.path.join(IN_DIR, f) for f in m["lock"]], quality=88)
    fire_atlas = pack_webp_pages([os.path.join(IN_DIR, f) for f in m["fire"]], quality=88)
    draw_atlas = pack_webp_pages([os.path.join(IN_DIR, f) for f in m["draw"]], quality=88)

    audio_map = {
        "snip_fast": wav_b64(os.path.join(SFX_DIR, "snip_fast.wav")),
        "snip_heavy": wav_b64(os.path.join(SFX_DIR, "snip_heavy.wav")),
        "lock_ready": wav_b64(os.path.join(SFX_DIR, "lock_ready.wav")),
        "plane_whoosh": wav_b64(os.path.join(SFX_DIR, "plane_whoosh.wav")),
        "cash_flutter": wav_b64(os.path.join(SFX_DIR, "cash_flutter.wav")),
        "whoa_man": wav_b64(os.path.join(CLIPS_DIR, "cut_01_wheres_my_cut.wav")),
        "whoa_1": wav_b64(os.path.join(CLIPS_DIR, "whoa_01_short.wav")),
        "whoa_2": wav_b64(os.path.join(CLIPS_DIR, "whoa_02_wobble.wav")),
        "whoa_3": wav_b64(os.path.join(CLIPS_DIR, "whoa_03_rise.wav")),
        "whoa_4": wav_b64(os.path.join(CLIPS_DIR, "whoa_04_punch.wav")),
        "kyle_hey": wav_b64(os.path.join(CLIPS_DIR, "kyle_02_hey_bright.wav")),
        "kyle_cut": wav_b64(os.path.join(CLIPS_DIR, "cut_02_give_me_a_cut.wav")),
        "kyle_hey_man": wav_b64(os.path.join(CLIPS_DIR, "edit_01_hey_man_tight.wav")),
    }

    payload = json.dumps({
        "fps": m["fps"],
        "idle": idle_atlas,
        "lock": lock_atlas,
        "fire": fire_atlas,
        "draw": draw_atlas,
        "audio": audio_map,
    })

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Pocket Kyle (#1) — 48-FPS HD Viewmodel &amp; POV Tuner</title>
<style>
  :root {{
    --bg: #0e0c0a;
    --panel: #181411;
    --panel2: #221c17;
    --border: #3a3026;
    --text: #f5f1eb;
    --muted: #a6998a;
    --accent: #f59e0b;
    --green: #22c55e;
    --blue: #38bdf8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top, #1f1914 0%, var(--bg) 60%);
    color: var(--text); line-height: 1.42;
  }}
  header.top {{
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;
    padding: 12px 20px; background: #14110e; border-bottom: 1px solid var(--border);
  }}
  .brand h1 {{ margin: 0; font-size: 1.25rem; }}
  .brand small {{ color: var(--muted); font-size: 0.83rem; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 7px; }}
  .pill {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 999px;
    padding: 4px 11px; font-size: 0.77rem; color: var(--muted); font-weight: 700;
  }}
  .pill b {{ color: #fde68a; }}
  .wrap {{ max-width: 1440px; margin: 0 auto; padding: 14px 16px 40px; }}
  .layout {{
    display: grid; grid-template-columns: minmax(0, 1fr) 370px; gap: 15px; align-items: start;
  }}
  @media (max-width: 1040px) {{ .layout {{ grid-template-columns: 1fr; }} }}

  .fps-card {{
    background: #080706; border: 2px solid var(--border); border-radius: 12px; overflow: hidden;
  }}
  .bar {{
    display: flex; flex-wrap: wrap; gap: 7px; align-items: center; justify-content: space-between;
    padding: 9px 12px; background: #16120e; border-bottom: 1px solid var(--border);
  }}
  .btn {{
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 7px; padding: 6px 11px; font-size: 0.81rem; font-weight: 700; cursor: pointer;
    transition: border-color .12s, background .12s;
  }}
  .btn:hover {{ border-color: #846d55; }}
  .btn.active {{ background: #3f2b12; border-color: var(--accent); color: #fde68a; }}
  .btn.drag-on {{ background: #0c3347; border-color: var(--blue); color: #bae6fd; }}
  .btn.fire {{ background: linear-gradient(180deg, #dc2626, #991b1b); border-color: #ef4444; color: #fff; }}
  .btn.copy {{ background: linear-gradient(180deg, #15803d, #166534); border-color: #22c55e; color: #fff; width: 100%; padding: 9px 12px; font-size: 0.86rem; }}
  .btn.sm {{ padding: 4px 8px; font-size: 0.74rem; }}
  canvas#fps {{ display: block; width: 100%; aspect-ratio: 16 / 9; cursor: crosshair; user-select: none; touch-action: none; }}
  canvas#fps.grabbing {{ cursor: grab; }}
  canvas#fps.grabbing:active {{ cursor: grabbing; }}
  .scrub-bar {{
    display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 8px 13px; background: #13100d;
    border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted);
  }}
  .scrub-bar input[type=range] {{ flex: 1; min-width: 140px; accent-color: var(--accent); }}

  .side {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px;
    display: flex; flex-direction: column; gap: 12px;
  }}
  .side h2 {{ margin: 0; font-size: 1.06rem; color: #fde68a; display: flex; align-items: center; justify-content: space-between; }}
  .preset-row {{ display: flex; flex-wrap: wrap; gap: 5px; }}

  .ctrl {{
    display: flex; flex-direction: column; gap: 3px;
  }}
  .ctrl-head {{
    display: flex; justify-content: space-between; align-items: center; font-size: 0.79rem;
  }}
  .ctrl-head label {{ color: var(--muted); font-weight: 600; }}
  .ctrl-head .val {{ color: #fde68a; font-variant-numeric: tabular-nums; font-weight: 700; font-family: ui-monospace, Consolas, monospace; }}
  .ctrl input[type=range] {{ width: 100%; margin: 0; accent-color: var(--accent); }}

  .chk-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding-top: 2px;
  }}
  .chk {{
    display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--muted);
    background: var(--panel2); border: 1px solid var(--border); border-radius: 7px; padding: 6px 8px; cursor: pointer;
  }}
  .chk input {{ accent-color: var(--accent); margin: 0; }}

  .codebox {{
    background: #0d0b09; border: 1px solid var(--border); border-radius: 8px; padding: 9px 10px;
    font-family: ui-monospace, Consolas, monospace; font-size: 0.74rem; color: #cbd5e1;
    white-space: pre; overflow-x: auto; line-height: 1.42; margin: 0;
  }}
  .note {{ font-size: 0.76rem; color: var(--muted); margin: 0; }}
  .divider {{ border: 0; border-top: 1px solid var(--border); margin: 2px 0; }}
  .toast {{
    display: none; text-align: center; font-size: 0.79rem; font-weight: 700; color: #4ade80;
    background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.35); border-radius: 7px; padding: 5px 8px;
  }}
</style>
</head>
<body>
<header class="top">
  <div class="brand">
    <h1>#1 &mdash; The Pocket Kyle &middot; 48-FPS HD Viewmodel &amp; Quake POV Tuner</h1>
    <small>Hair &amp; Blades Fixed &middot; Quiet Chillin&rsquo; Idle &middot; &ldquo;Whoa Man&rdquo; Draw &middot; 4-Beat Throw &middot; Live Quake <code>v_kyle.md3</code> POV Placement</small>
  </div>
  <div class="pills">
    <span class="pill">Rate: <b>48 FPS</b></span>
    <span class="pill">Frames: <b>224 RGBA (420&times;560)</b></span>
    <span class="pill">Slot: <b>Fun Gun #8 (imp 68)</b></span>
  </div>
</header>

<div class="wrap">
  <div class="layout">
    <div class="fps-card">
      <div class="bar">
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn" id="st-draw" onclick="triggerDraw()">&#128075; Pull Out (Draw)</button>
          <button class="btn active" id="st-idle" onclick="setMode('idle')">Idle (96f)</button>
          <button class="btn" id="st-lock" onclick="setMode('lock')">Lock (48f)</button>
          <button class="btn fire" id="st-fire" onclick="triggerFire()">&#128293; Yeet Kyle (56f)</button>
          <button class="btn" id="btn-pause" onclick="togglePause()">&#9208; Pause</button>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
          <button class="btn" id="btn-drag" onclick="toggleDragMode()" title="Switch Left-Click between Lock/Fire and dragging Kyle directly on screen">&#9995; Drag POV: OFF</button>
          <button class="btn" id="btn-spd" onclick="cycleSpeed()">1.0&times;</button>
          <label style="font-size:0.8rem;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;">
            <input type="checkbox" id="chk-sfx" checked> SFX
          </label>
          <button class="btn" id="btn-bg" onclick="cycleBg()">Bakersfield</button>
        </div>
      </div>
      <canvas id="fps" width="1280" height="720"></canvas>
      <div class="scrub-bar">
        <span id="frame-lbl" style="min-width:150px;font-variant-numeric:tabular-nums;">IDLE &middot; 1 / 96 (48 FPS)</span>
        <input type="range" id="scrubber" min="0" max="95" value="0" oninput="onScrub(this.value)">
        <span id="hint-lbl">LMB: Hold to Lock &amp; Yeet &middot; Right-Drag (or Drag Mode): Move POV</span>
      </div>
    </div>

    <aside class="side">
      <h2>
        <span>&#127919; Quake First-Person POV Tuner</span>
        <button class="btn sm" onclick="applyPreset('default')">Reset</button>
      </h2>

      <div class="preset-row">
        <button class="btn sm" onclick="applyPreset('default')">Default Right</button>
        <button class="btn sm" onclick="applyPreset('milky')">Milky Style</button>
        <button class="btn sm" onclick="applyPreset('compact')">Compact</button>
        <button class="btn sm" onclick="applyPreset('big')">Big &amp; Close</button>
        <button class="btn sm" onclick="applyPreset('center')">Doom Center</button>
      </div>

      <div class="ctrl">
        <div class="ctrl-head"><label for="pov-x">Horizontal Offset (Left &larr; &rarr; Right)</label><span class="val" id="val-x">+24 px</span></div>
        <input type="range" id="pov-x" min="-640" max="240" step="1" value="24" oninput="onPovInput()">
      </div>

      <div class="ctrl">
        <div class="ctrl-head"><label for="pov-y">Vertical Offset (Up &uarr; &darr; Down)</label><span class="val" id="val-y">+10 px</span></div>
        <input type="range" id="pov-y" min="-220" max="260" step="1" value="10" oninput="onPovInput()">
      </div>

      <div class="ctrl">
        <div class="ctrl-head"><label for="pov-scale">Weapon Scale</label><span class="val" id="val-scale">100%</span></div>
        <input type="range" id="pov-scale" min="45" max="155" step="1" value="100" oninput="onPovInput()">
      </div>

      <div class="ctrl">
        <div class="ctrl-head"><label for="pov-roll">Tilt / Roll Angle</label><span class="val" id="val-roll">0.0&deg;</span></div>
        <input type="range" id="pov-roll" min="-30" max="30" step="0.5" value="0" oninput="onPovInput()">
      </div>

      <div class="ctrl">
        <div class="ctrl-head"><label for="pov-sway">Mouse Look Sway</label><span class="val" id="val-sway">100%</span></div>
        <input type="range" id="pov-sway" min="0" max="200" step="5" value="100" oninput="onPovInput()">
      </div>

      <div class="chk-grid">
        <label class="chk"><input type="checkbox" id="pov-hud" checked onchange="onPovInput()"> Quake HUD Bar</label>
        <label class="chk"><input type="checkbox" id="pov-guides" onchange="onPovInput()"> 4:3 &amp; Card Guides</label>
        <label class="chk"><input type="checkbox" id="pov-flip" onchange="onPovInput()"> Mirror Left-Hand</label>
        <label class="chk"><input type="checkbox" id="pov-bob" checked onchange="onPovInput()"> Walk Bob Sim</label>
      </div>

      <hr class="divider">

      <div>
        <div class="ctrl-head" style="margin-bottom:5px;">
          <label>Live Quake <code>v_kyle.md3</code> Coordinates (16:9 FOV 90)</label>
        </div>
        <pre class="codebox" id="md3-readout"></pre>
      </div>

      <button class="btn copy" onclick="copyPovSettings()">&#128203; Copy POV Settings to Send Back</button>
      <div class="toast" id="copy-toast">Copied! Paste straight into chat to bake v_kyle.md3</div>
      <p class="note">Tip: Use <b>Arrow Keys</b> for 1px fine-nudging (<b>Shift+Arrows</b> = 10px), or turn on <b>Drag POV</b> / <b>Right-Click Drag</b> right on the arena. Settings auto-save in your browser.</p>
    </aside>
  </div>
</div>

<script>
const DATA = {payload};
const FPS = DATA.fps;
const AUDIO = DATA.audio;
const canvas = document.getElementById("fps");
const ctx = canvas.getContext("2d");

const BASE_H = 620;
const STORAGE_KEY = "bakoquake_pocket_kyle_pov_v1";

const PRESETS = {{
  default: {{ x: 24,   y: 10,  scale: 100, roll: 0,    sway: 100, flip: false }},
  milky:   {{ x: 28,   y: 78,  scale: 100, roll: 0,    sway: 100, flip: false }},
  compact: {{ x: 12,   y: 44,  scale: 78,  roll: -3.5, sway: 80,  flip: false }},
  big:     {{ x: 46,   y: 56,  scale: 122, roll: 2.0,  sway: 110, flip: false }},
  center:  {{ x: -408, y: 36,  scale: 94,  roll: 0,    sway: 75,  flip: false }},
}};

const pov = {{
  x: 24,
  y: 10,
  scale: 100,
  roll: 0,
  sway: 100,
  hud: true,
  guides: false,
  flip: false,
  bob: true,
}};

let mode = "idle";
let paused = false;
let manualFrame = 0;
let startMs = performance.now();
let holdingMouse = false;
let holdStartMs = 0;
let dragMode = false;
let draggingPov = false;
let dragStartMouse = {{ x: 0, y: 0 }};
let dragStartPov = {{ x: 0, y: 0 }};
let bgMode = 0;
let mouseX = 640, mouseY = 360;
const SPEEDS = [1.0, 0.5, 0.25, 1.35];
let speedIdx = 0;
let speedMult = 1.0;
let lastFramePlayed = -1;
let lockDinged = false;

// Preload all WebP atlas pages
const loaded = {{}};
["idle", "lock", "fire", "draw"].forEach(k => {{
  loaded[k] = DATA[k].pages.map(pg => {{
    const im = new Image();
    im.src = pg.url;
    return {{ ...pg, img: im }};
  }});
}});

function loadSavedPov() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {{
      const parsed = JSON.parse(raw);
      Object.assign(pov, parsed);
    }}
  }} catch (e) {{}}
  syncControlsFromPov();
}}

function savePov() {{
  try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(pov)); }} catch (e) {{}}
}}

function syncControlsFromPov() {{
  document.getElementById("pov-x").value = pov.x;
  document.getElementById("pov-y").value = pov.y;
  document.getElementById("pov-scale").value = pov.scale;
  document.getElementById("pov-roll").value = pov.roll;
  document.getElementById("pov-sway").value = pov.sway;
  document.getElementById("pov-hud").checked = !!pov.hud;
  document.getElementById("pov-guides").checked = !!pov.guides;
  document.getElementById("pov-flip").checked = !!pov.flip;
  document.getElementById("pov-bob").checked = !!pov.bob;
  updatePovReadout();
}}

function onPovInput() {{
  pov.x = parseFloat(document.getElementById("pov-x").value);
  pov.y = parseFloat(document.getElementById("pov-y").value);
  pov.scale = parseFloat(document.getElementById("pov-scale").value);
  pov.roll = parseFloat(document.getElementById("pov-roll").value);
  pov.sway = parseFloat(document.getElementById("pov-sway").value);
  pov.hud = document.getElementById("pov-hud").checked;
  pov.guides = document.getElementById("pov-guides").checked;
  pov.flip = document.getElementById("pov-flip").checked;
  pov.bob = document.getElementById("pov-bob").checked;
  savePov();
  updatePovReadout();
}}

function applyPreset(name) {{
  const p = PRESETS[name];
  if (!p) return;
  Object.assign(pov, p);
  savePov();
  syncControlsFromPov();
}}

function computeCardLayout(curSpec) {{
  const targetH = BASE_H * (pov.scale / 100);
  const targetW = targetH * (curSpec.fw / curSpec.fh);
  // Base anchor: bottom-right aligned, shifted by pov.x / pov.y
  const baseX = 1280 - targetW + pov.x;
  const baseY = 720 - targetH + pov.y;
  return {{ targetW, targetH, baseX, baseY }};
}}

function computeQuakeConstants() {{
  const spec = DATA.idle;
  const {{ targetW, targetH, baseX, baseY }} = computeCardLayout(spec);
  // Matches source/mm_tools/build_milky_view.py (16:9 FOV 90 at VIEW_X = 14.0 -> +/-27.8 W, +/-15.6 H)
  const VIEW_X = 14.0;
  const VIEW_H = (targetH / 720) * 31.2;
  const VIEW_TOP = (0.5 - baseY / 720) * 31.2;
  const pxRight = baseX + targetW;
  const VIEW_RIGHT = (0.5 - pxRight / 1280) * 55.6;
  return {{
    VIEW_X: +VIEW_X.toFixed(2),
    VIEW_H: +VIEW_H.toFixed(2),
    VIEW_RIGHT: +VIEW_RIGHT.toFixed(2),
    VIEW_TOP: +VIEW_TOP.toFixed(2),
    VIEW_ROLL: +pov.roll.toFixed(1),
    FLIP_X: !!pov.flip,
    px: {{ x: Math.round(pov.x), y: Math.round(pov.y), scale_pct: Math.round(pov.scale) }}
  }};
}}

function updatePovReadout() {{
  document.getElementById("val-x").textContent = `${{pov.x >= 0 ? "+" : ""}}${{Math.round(pov.x)}} px`;
  document.getElementById("val-y").textContent = `${{pov.y >= 0 ? "+" : ""}}${{Math.round(pov.y)}} px`;
  document.getElementById("val-scale").textContent = `${{Math.round(pov.scale)}}%`;
  document.getElementById("val-roll").textContent = `${{pov.roll >= 0 ? "+" : ""}}${{pov.roll.toFixed(1)}}°`;
  document.getElementById("val-sway").textContent = `${{Math.round(pov.sway)}}%`;

  const q = computeQuakeConstants();
  document.getElementById("md3-readout").textContent =
`VIEW_X     = ${{q.VIEW_X.toFixed(1)}}
VIEW_H     = ${{q.VIEW_H.toFixed(2)}}
VIEW_RIGHT = ${{q.VIEW_RIGHT.toFixed(2)}}
VIEW_TOP   = ${{q.VIEW_TOP.toFixed(2)}}
VIEW_ROLL  = ${{q.VIEW_ROLL.toFixed(1)}}   # deg
FLIP_X     = ${{q.FLIP_X ? "True" : "False"}}`;
}}

function copyPovSettings() {{
  const q = computeQuakeConstants();
  const txt = "Pocket Kyle POV Settings: " + JSON.stringify(q);
  const done = () => {{
    const el = document.getElementById("copy-toast");
    el.style.display = "block";
    clearTimeout(window._toastTid);
    window._toastTid = setTimeout(() => {{ el.style.display = "none"; }}, 2800);
  }};
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(txt).then(done).catch(() => {{ prompt("Copy POV Settings:", txt); }});
  }} else {{
    prompt("Copy POV Settings:", txt);
  }}
}}

function toggleDragMode() {{
  dragMode = !dragMode;
  const b = document.getElementById("btn-drag");
  b.classList.toggle("drag-on", dragMode);
  b.innerHTML = dragMode ? "&#9995; Drag POV: ON" : "&#9995; Drag POV: OFF";
  canvas.classList.toggle("grabbing", dragMode);
  document.getElementById("hint-lbl").textContent = dragMode
    ? "Drag Mode ON: Drag Kyle anywhere on screen (Mouse Wheel = Scale)"
    : "LMB: Hold to Lock & Yeet · Right-Drag (or Drag Mode): Move POV";
}}

function playSound(key, vol = 0.8) {{
  if (!document.getElementById("chk-sfx").checked) return;
  const src = AUDIO[key];
  if (!src) return;
  const a = new Audio(src);
  a.volume = vol;
  a.play().catch(() => {{}});
}}

function setMode(m) {{
  mode = m;
  paused = false;
  startMs = performance.now();
  manualFrame = 0;
  lastFramePlayed = -1;
  document.getElementById("scrubber").max = DATA[m].count - 1;
  document.getElementById("btn-pause").innerHTML = "&#9208; Pause";
  document.getElementById("st-draw").classList.toggle("active", m === "draw");
  document.getElementById("st-idle").classList.toggle("active", m === "idle");
  document.getElementById("st-lock").classList.toggle("active", m === "lock");
}}

function triggerDraw() {{
  setMode("draw");
  const drawWhoas = ["whoa_man", "whoa_1", "whoa_2", "whoa_3", "whoa_4"];
  playSound(drawWhoas[Math.floor(Math.random() * drawWhoas.length)], 0.9);
}}

function triggerFire() {{
  setMode("fire");
  playSound("plane_whoosh", 0.62);
  setTimeout(() => playSound("cash_flutter", 0.55), 220);
  const voices = ["kyle_cut", "whoa_man", "kyle_hey", "whoa_4", "whoa_2", "kyle_hey_man"];
  playSound(voices[Math.floor(Math.random() * voices.length)], 0.9);
}}

function togglePause() {{
  paused = !paused;
  document.getElementById("btn-pause").innerHTML = paused ? "&#9654; Resume" : "&#9208; Pause";
  if (!paused) {{
    startMs = performance.now() - (manualFrame / (FPS * speedMult)) * 1000;
  }}
}}

function onScrub(v) {{
  paused = true;
  manualFrame = parseInt(v, 10) || 0;
  document.getElementById("btn-pause").innerHTML = "&#9654; Resume";
}}

function cycleSpeed() {{
  speedIdx = (speedIdx + 1) % SPEEDS.length;
  speedMult = SPEEDS[speedIdx];
  document.getElementById("btn-spd").textContent = `${{speedMult}}×`;
  startMs = performance.now() - (manualFrame / (FPS * speedMult)) * 1000;
}}

function cycleBg() {{
  bgMode = (bgMode + 1) % 3;
  const names = ["Bakersfield", "Night Soi 6", "Dark Studio"];
  document.getElementById("btn-bg").textContent = names[bgMode];
}}

function canvasCoords(e) {{
  const r = canvas.getBoundingClientRect();
  return {{
    x: ((e.clientX - r.left) / r.width) * 1280,
    y: ((e.clientY - r.top) / r.height) * 720,
  }};
}}

canvas.addEventListener("contextmenu", e => e.preventDefault());

canvas.addEventListener("mousemove", e => {{
  const c = canvasCoords(e);
  mouseX = c.x;
  mouseY = c.y;
  if (draggingPov) {{
    pov.x = Math.max(-640, Math.min(240, Math.round(dragStartPov.x + (c.x - dragStartMouse.x))));
    pov.y = Math.max(-220, Math.min(260, Math.round(dragStartPov.y + (c.y - dragStartMouse.y))));
    savePov();
    syncControlsFromPov();
  }}
}});

canvas.addEventListener("mousedown", e => {{
  const c = canvasCoords(e);
  if (dragMode || e.button === 2) {{
    draggingPov = true;
    dragStartMouse = c;
    dragStartPov = {{ x: pov.x, y: pov.y }};
    return;
  }}
  if (e.button === 0) {{
    holdingMouse = true;
    holdStartMs = performance.now();
    lockDinged = false;
    setMode("lock");
  }}
}});

window.addEventListener("mouseup", () => {{
  if (draggingPov) {{
    draggingPov = false;
    return;
  }}
  if (!holdingMouse) return;
  holdingMouse = false;
  triggerFire();
}});

canvas.addEventListener("wheel", e => {{
  if (!dragMode) return;
  e.preventDefault();
  const delta = e.deltaY < 0 ? 3 : -3;
  pov.scale = Math.max(45, Math.min(155, pov.scale + delta));
  savePov();
  syncControlsFromPov();
}}, {{ passive: false }});

window.addEventListener("keydown", e => {{
  if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;
  const step = e.shiftKey ? 10 : 1;
  if (e.key === "ArrowLeft")  {{ pov.x = Math.max(-640, pov.x - step); e.preventDefault(); }}
  else if (e.key === "ArrowRight") {{ pov.x = Math.min(240, pov.x + step); e.preventDefault(); }}
  else if (e.key === "ArrowUp")    {{ pov.y = Math.max(-220, pov.y - step); e.preventDefault(); }}
  else if (e.key === "ArrowDown")  {{ pov.y = Math.min(260, pov.y + step); e.preventDefault(); }}
  else return;
  savePov();
  syncControlsFromPov();
}});

function drawBackdrop(t) {{
  const W = 1280, H = 720;
  if (bgMode === 2) {{
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#1c222e"); g.addColorStop(1, "#0d1118");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(255,255,255,0.045)";
    for (let x = 0; x < W; x += 64) {{ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }}
    for (let y = 0; y < H; y += 64) {{ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }}
    return;
  }}
  const sky = ctx.createLinearGradient(0, 0, 0, 390);
  if (bgMode === 0) {{ sky.addColorStop(0, "#3b6fa6"); sky.addColorStop(1, "#d9b98c"); }}
  else {{ sky.addColorStop(0, "#0b1026"); sky.addColorStop(1, "#3b1742"); }}
  ctx.fillStyle = sky; ctx.fillRect(0, 0, W, 390);

  const gnd = ctx.createLinearGradient(0, 390, 0, H);
  gnd.addColorStop(0, bgMode === 0 ? "#4a433c" : "#1c1926");
  gnd.addColorStop(1, bgMode === 0 ? "#24201c" : "#0b0a10");
  ctx.fillStyle = gnd; ctx.fillRect(0, 390, W, H - 390);

  ctx.fillStyle = bgMode === 0 ? "#3c322b" : "#171422";
  ctx.fillRect(40, 210, 260, 180); ctx.fillRect(920, 180, 320, 210);
  ctx.fillStyle = bgMode === 0 ? "#5c4a3c" : "#251e36";
  ctx.fillRect(360, 270, 220, 120);

  const bx = 640 + Math.sin(t * 1.4) * 210;
  const by = 205 + Math.cos(t * 2.1) * 40;
  ctx.save();
  ctx.translate(bx, by);
  ctx.fillStyle = "rgba(15, 23, 42, 0.78)";
  ctx.beginPath(); ctx.ellipse(0, 0, 38, 18, 0, 0, Math.PI * 2); ctx.fill();
  const flap = Math.sin(t * 11) * 24;
  ctx.strokeStyle = "#94a3b8"; ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(-12, -4); ctx.quadraticCurveTo(-55, -35 + flap, -88, -10 + flap);
  ctx.moveTo(12, -4); ctx.quadraticCurveTo(55, -35 + flap, 88, -10 + flap);
  ctx.stroke();
  ctx.fillStyle = "#fde047"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
  ctx.fillText("JOHN BIRD TARGET", 0, -28);
  ctx.restore();
}}

function drawQuakeHud() {{
  if (!pov.hud) return;
  const W = 1280, H = 720, barH = 68;
  ctx.save();
  // Classic Quake bottom status bar silhouette (centered 640px wide)
  const bx = (W - 640) / 2;
  ctx.fillStyle = "rgba(24, 18, 14, 0.82)";
  ctx.fillRect(bx, H - barH, 640, barH);
  ctx.strokeStyle = "rgba(168, 134, 96, 0.5)";
  ctx.lineWidth = 2;
  ctx.strokeRect(bx + 1, H - barH + 1, 638, barH - 2);
  ctx.font = "bold 24px ui-monospace, Consolas, monospace";
  ctx.fillStyle = "#f59e0b";
  ctx.textAlign = "left";
  ctx.fillText("ARMOR 100", bx + 22, H - 24);
  ctx.fillStyle = "#f8fafc";
  ctx.fillText("HP 100", bx + 235, H - 24);
  ctx.fillStyle = "#4ade80";
  ctx.fillText("KYLES 3", bx + 425, H - 24);
  ctx.font = "bold 11px system-ui";
  ctx.fillStyle = "rgba(245, 241, 235, 0.55)";
  ctx.textAlign = "center";
  ctx.fillText("QUAKE HUD STATUS BAR REFERENCE", W / 2, H - barH + 14);
  ctx.restore();
}}

function drawGuides(dx, dy, targetW, targetH) {{
  if (!pov.guides) return;
  const W = 1280, H = 720;
  ctx.save();
  // 4:3 Safe Frame (960x720 centered)
  ctx.strokeStyle = "rgba(56, 189, 248, 0.45)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([8, 6]);
  ctx.strokeRect(160, 0, 960, 720);
  ctx.fillStyle = "rgba(56, 189, 248, 0.75)";
  ctx.font = "bold 12px system-ui";
  ctx.fillText("4:3 SAFE EDGE", 168, 18);
  // Crosshair clearance ring (r=110px)
  ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
  ctx.beginPath(); ctx.arc(640, 360, 110, 0, Math.PI * 2); ctx.stroke();
  // Card bounding box
  ctx.strokeStyle = "rgba(74, 222, 128, 0.7)";
  ctx.setLineDash([5, 5]);
  ctx.strokeRect(dx, dy, targetW, targetH);
  ctx.fillStyle = "rgba(74, 222, 128, 0.9)";
  ctx.fillText("v_kyle.md3 CARD", dx + 8, Math.max(16, dy + 16));
  ctx.restore();
}}

function drawCrosshair(now) {{
  const cx = 640, cy = 360;
  ctx.save();
  if (mode === "lock") {{
    const prog = holdingMouse ? Math.min(1, (now - holdStartMs) / 600) : 0.78 + 0.22 * Math.sin(now * 0.01);
    if (holdingMouse && prog >= 0.99 && !lockDinged) {{
      lockDinged = true;
      playSound("lock_ready", 0.75);
    }}
    const rad = 48 - prog * 26;
    ctx.strokeStyle = prog >= 0.98 ? "#22c55e" : "#f59e0b";
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2 * prog); ctx.stroke();
    ctx.font = "bold 13px system-ui";
    ctx.fillStyle = prog >= 0.98 ? "#4ade80" : "#fcd34d";
    ctx.textAlign = "center";
    ctx.fillText(prog >= 0.98 ? "CLIENT LOCKED! RELEASE TO YEET" : "LOCKING ON...", cx, cy - rad - 10);
  }}
  ctx.strokeStyle = "rgba(255,255,255,0.88)"; ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - 12, cy); ctx.lineTo(cx - 4, cy);
  ctx.moveTo(cx + 4, cy); ctx.lineTo(cx + 12, cy);
  ctx.moveTo(cx, cy - 12); ctx.lineTo(cx, cy - 4);
  ctx.moveTo(cx, cy + 4); ctx.lineTo(cx, cy + 12);
  ctx.stroke();
  ctx.restore();
}}

function loop(now) {{
  const t = now * 0.001;
  drawBackdrop(t);

  const spec = DATA[mode];
  let fi = manualFrame;
  if (!paused) {{
    const el = ((now - startMs) / 1000) * FPS * speedMult;
    if (mode === "fire" || mode === "draw") {{
      const f = Math.floor(el);
      if (f >= spec.count) {{
        setMode("idle");
        fi = 0;
      }} else {{
        fi = f;
      }}
    }} else {{
      fi = Math.floor(el) % spec.count;
    }}
    manualFrame = fi;
    document.getElementById("scrubber").value = fi;
  }}

  // Frame-accurate metallic SNIP! SFX ONLY during Hold-to-Lock (quiet chillin' Idle!)
  if (!paused && fi !== lastFramePlayed) {{
    if (mode === "lock" && (fi % 12 === 5)) {{
      playSound("snip_fast", 0.42);
    }}
    lastFramePlayed = fi;
  }}

  const curSpec = DATA[mode];
  const pages = loaded[mode];
  const pg = pages.find(p => fi >= p.start && fi < p.start + p.count) || pages[0];
  const {{ targetW, targetH, baseX, baseY }} = computeCardLayout(curSpec);

  const swayMult = pov.sway / 100;
  const swayX = draggingPov ? 0 : ((mouseX - 640) / 640) * 16 * swayMult;
  const swayY = draggingPov ? 0 : ((mouseY - 360) / 360) * 10 * swayMult;
  const bobX = (pov.bob && !paused && !draggingPov) ? Math.sin(t * 2.6) * 4.0 : 0;
  const bobY = (pov.bob && !paused && !draggingPov) ? Math.abs(Math.cos(t * 2.6)) * 5.0 : 0;
  const dx = baseX + swayX + bobX;
  const dy = baseY + swayY + bobY;

  if (pg && pg.img.complete && pg.img.naturalWidth > 0) {{
    const localIdx = fi - pg.start;
    const col = localIdx % pg.cols;
    const row = Math.floor(localIdx / pg.cols);
    const sx = col * curSpec.fw;
    const sy = row * curSpec.fh;

    ctx.save();
    const cx = dx + targetW * 0.5;
    const cy = dy + targetH * 0.72;
    ctx.translate(cx, cy);
    if (pov.roll !== 0) ctx.rotate((pov.roll * Math.PI) / 180);
    if (pov.flip) ctx.scale(-1, 1);
    ctx.drawImage(pg.img, sx, sy, curSpec.fw, curSpec.fh, -targetW * 0.5, -targetH * 0.72, targetW, targetH);
    ctx.restore();
  }}

  drawGuides(dx, dy, targetW, targetH);
  drawQuakeHud();
  drawCrosshair(now);
  document.getElementById("frame-lbl").textContent = `${{mode.toUpperCase()}} · ${{fi + 1}} / ${{curSpec.count}} (${{Math.round(FPS * speedMult)}} FPS)`;
  requestAnimationFrame(loop);
}}

loadSavedPov();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print(f"Wrote Pocket Kyle 48-FPS HD Showcase + POV Tuner: {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
