r"""Builds the 100% Self-Contained Single-File HTML Showcase for Green-Suit Wheelman:
  - Local output: G:\Quake\Combat\BakersfieldQuake\greensuit_wheelman.html
  - VPS copy:     G:\Quake\Combat\BakersfieldQuake\greensuit_wheelman_sprite\index.html

Embeds:
  1. All 12 x 8-Direction 360° RGBA WebP Sprite Atlases (1,200 3D sprite frames!)
  2. Full Posed 3D Mesh + PBR Stainless Wheel Contraption (.GLB embedded for BOTH live WebGL2 3D
     orbit inspection AND 1-click .glb file download!)
  3. Playable 2.5D Driving & Stunt Arena (WASD / Arrows / Mouse + Stunt Hotkeys 1-6 + Space!)
  4. Real Photo vs. 3D Sprite Comparison Strip, 8-Angle Turnaround Sheet, & 12-Animation Poster
  5. Procedural WebAudio Sound Effects (tire rumble, grinding sparks, chrome clank, whoosh, Quake boom)
Zero external CDN or network dependencies!
"""
from __future__ import annotations

import base64
import io
import json
import os
import struct
from typing import Dict, List

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SPR_DIR = os.path.join(MOD_DIR, "greensuit_wheelman_sprite")
ATLAS_DIR = os.path.join(SPR_DIR, "atlases")
GLB_PATH = os.path.join(HERE, "greensuit_wheelman_3d.glb")
OUT_HTML_ROOT = os.path.join(MOD_DIR, "greensuit_wheelman.html")
OUT_HTML_SPR = os.path.join(SPR_DIR, "index.html")


def b64_file(path: str, mime: str) -> str:
    with open(path, "rb") as fp:
        return f"data:{mime};base64," + base64.b64encode(fp.read()).decode("ascii")


def b64_jpg_resized(path: str, max_w: int = 1320, quality: int = 89) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = int(round(im.height * (max_w / float(im.width))))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


ANIMS_UI = [
    {"id": "seated_cruise",    "icon": "🛞", "badge": "POSE #1 • CLASSIC", "sfx": "roll",   "desc": "Iconic crouched Green-Suit Wheelman pose: hands gripping the stainless axle, green-socked feet perched by the white rims, cheeky studio grin, spinning ribbed pneumatic tires."},
    {"id": "scream_turbo",     "icon": "⚡", "badge": "POSE #2 • SPARKS",  "sfx": "sparks", "desc": "Maximum-effort straining battle-cry overdrive! Bullet-nose stainless cylinder scrapes a shower of 3D golden sparks across the floor at high RPM."},
    {"id": "plank_rollout",    "icon": "🏋️", "badge": "POSE #3 • PLANK",   "sfx": "whoosh", "desc": "Full-body living-room ab-roller rollout! Extends from a compact pike all the way into a hovering horizontal plank with wide-eyed 'OOOO!' shock."},
    {"id": "hero_crane_point", "icon": "☝️", "badge": "POSE #4 • CRANE",   "sfx": "fanfare","desc": "Balancing on one leg with left knee kicked high, cradling the heavy two-wheel stainless contraption diagonally across his chest while sky-pointing!"},
    {"id": "overhead_press",   "icon": "💪", "badge": "STRENGTH",          "sfx": "clang",  "desc": "Deep Olympic squat-clean grab followed by an explosive overhead barbell lockout press of the spinning two-wheel steel rig."},
    {"id": "cyclone_spin",     "icon": "🌪️", "badge": "TORNADO",           "sfx": "whirl",  "desc": "360° helicopter wheel-barbell cyclone spin wrapped in glowing neon-green & gold plasma rings."},
    {"id": "wheelie_backflip", "icon": "🤸", "badge": "ACROBATICS",        "sfx": "whoosh", "desc": "Yanks the axle into a steep wheelie, launches skyward into a full tucked 360° mid-air backflip, and sticks a cushioned landing."},
    {"id": "bazooka_ram",      "icon": "🚀", "badge": "CHARGE",            "sfx": "sparks", "desc": "Full-tilt sprint aiming the polished bullet-tip stainless cylinder horizontally forward like a rocket battering-ram lance!"},
    {"id": "throw_boomerang",  "icon": "🪃", "badge": "PROJECTILE",        "sfx": "whoosh", "desc": "Winds up deep, hurls the entire 3D stainless wheel contraption spinning forward through space like a boomerang, and snatches it back!"},
    {"id": "breakdance_flare", "icon": "🕺", "badge": "B-BOY",             "sfx": "roll",   "desc": "Inverted B-Boy handstand balanced directly on the rolling steel axle while flaring bright neon-green legs in a wide V-straddle."},
    {"id": "victory_groove",   "icon": "🎸", "badge": "SHRED",             "sfx": "guitar", "desc": "Strumming the polished central chrome cylinder like a heavy-metal double-wheel electric guitar with funky side-kicks!"},
    {"id": "gib_explosion",    "icon": "💥", "badge": "QUAKE FINALE",      "sfx": "boom",   "desc": "Overload tremor & swell followed by a fiery Quake detonation sending both tires, the stainless chrome rod, and green gibs flying & bouncing in 3D!"},
]


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Green-Suit Wheelman — 360° 3D Sprite, 12 Animations, Playable Arena &amp; WebGL 3D Model</title>
<style>
  :root {
    --bg:#0b0f17; --panel:#131926; --panel2:#1b2334; --panel3:#232e44;
    --ink:#f1f5f9; --dim:#94a3b8; --neon:#7ef442; --neon-dim:#244b18;
    --cyan:#38bdf8; --amber:#fbbf24; --danger:#f43f5e; --purple:#c084fc;
    --border:#2b364f;
  }
  * { box-sizing:border-box; }
  body {
    margin:0; background:radial-gradient(circle at 50% 0%, #162235 0%, var(--bg) 55%);
    color:var(--ink); font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    min-height:100vh; display:flex; flex-direction:column; align-items:center;
    padding:16px 14px 48px; gap:12px;
  }
  header {
    width:min(100%, 1140px); display:flex; flex-wrap:wrap; align-items:center;
    justify-content:space-between; gap:12px; background:rgba(19,25,38,0.88);
    border:1px solid var(--border); border-radius:14px; padding:14px 18px;
    box-shadow:0 12px 32px rgba(0,0,0,0.35); backdrop-filter:blur(10px);
  }
  .brand { display:flex; flex-direction:column; gap:3px; }
  h1 {
    margin:0; font-size:clamp(18px, 2.4vw, 24px); font-weight:900; letter-spacing:-0.02em;
    display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  }
  .pill {
    background:linear-gradient(135deg, #86efac, #4ade80); color:#071a0c;
    font-size:11.5px; font-weight:900; padding:3px 9px; border-radius:999px;
    letter-spacing:0.04em; text-transform:uppercase;
  }
  .sub { margin:0; color:var(--dim); font-size:13px; }
  .hdr-actions { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .dl-btn {
    background:var(--panel2); color:var(--ink); border:1px solid #384766;
    border-radius:9px; padding:8px 12px; font:inherit; font-size:12.5px; font-weight:700;
    cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:6px;
    transition:all 0.14s ease;
  }
  .dl-btn:hover { border-color:var(--neon); color:var(--neon); transform:translateY(-1px); }
  .dl-btn.primary { background:var(--neon); color:#071c0b; border-color:var(--neon); font-weight:800; }
  .dl-btn.primary:hover { background:#9ef86c; color:#071c0b; }

  /* Mode Switcher */
  .mode-bar {
    width:min(100%, 1140px); display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));
    gap:8px; background:var(--panel); border:1px solid var(--border); border-radius:13px; padding:7px;
  }
  .mode-tab {
    background:var(--panel2); color:var(--dim); border:1.5px solid transparent;
    border-radius:9px; padding:10px 12px; font:inherit; font-weight:800; font-size:13.5px;
    cursor:pointer; transition:all 0.14s ease; text-align:center;
  }
  .mode-tab:hover { color:var(--ink); border-color:#425275; }
  .mode-tab.active {
    background:linear-gradient(180deg, #1a3822 0%, #122619 100%);
    color:var(--neon); border-color:var(--neon);
    box-shadow:0 0 18px rgba(126,244,66,0.20);
  }

  /* Main Studio Layout */
  .workspace {
    width:min(100%, 1140px); display:grid; grid-template-columns:320px 1fr; gap:12px;
    align-items:start;
  }
  @media (max-width: 880px) { .workspace { grid-template-columns:1fr; } }
  .hidden { display:none !important; }

  .anim-list {
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    padding:9px; display:flex; flex-direction:column; gap:6px; max-height:660px; overflow-y:auto;
  }
  .anim-card {
    display:flex; align-items:center; gap:10px; padding:9px 11px; border-radius:10px;
    background:var(--panel2); border:1.5px solid transparent; color:var(--ink);
    cursor:pointer; text-align:left; font:inherit; transition:all 0.12s ease;
  }
  .anim-card:hover { border-color:#425378; transform:translateX(2px); }
  .anim-card.active {
    background:#193322; border-color:var(--neon);
    box-shadow:inset 0 0 14px rgba(126,244,66,0.12);
  }
  .anim-ico { font-size:21px; line-height:1; flex:0 0 28px; text-align:center; }
  .anim-info { flex:1; min-width:0; }
  .anim-title { font-weight:800; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .anim-meta { font-size:11px; color:var(--dim); display:flex; gap:6px; align-items:center; margin-top:2px; }
  .mini-badge {
    font-size:9.5px; font-weight:800; padding:1px 6px; border-radius:4px;
    background:#28354e; color:#cbd5e1; letter-spacing:0.03em;
  }
  .anim-card.active .mini-badge { background:var(--neon); color:#081c0c; }

  /* Stage Panel */
  .stage-col { display:flex; flex-direction:column; gap:10px; min-width:0; }
  .stage-box {
    width:100%; height:min(64vh, 520px); min-height:380px; border-radius:14px;
    border:1px solid var(--border); position:relative; overflow:hidden;
    display:flex; align-items:center; justify-content:center;
    user-select:none; touch-action:none; cursor:grab;
  }
  .stage-box:active { cursor:grabbing; }
  .stage-box.bg-checker { background:repeating-conic-gradient(#232938 0% 25%, #181d28 0% 50%) 0 0/26px 26px; }
  .stage-box.bg-studio  { background:radial-gradient(circle at 50% 62%, #eceff4 0%, #cfd6e0 68%, #aeb8c6 100%); }
  .stage-box.bg-room    {
    background:
      linear-gradient(180deg, rgba(84,54,30,0.92) 0%, rgba(62,38,20,0.95) 62%, rgba(112,72,34,0.98) 62.5%, rgba(74,45,19,1) 100%);
  }
  .stage-box.bg-quake   { background:radial-gradient(circle at 50% 68%, #3e2b1d 0%, #1c130d 72%, #0a0807 100%); }
  .stage-box.bg-magenta { background:#ff00ff; }
  .stage-box.bg-black   { background:#05070a; }

  #sprite-canvas { width:100%; height:100%; display:block; }

  .hud-tl {
    position:absolute; top:12px; left:14px; background:rgba(11,15,23,0.86);
    border:1px solid #364463; border-radius:9px; padding:7px 12px;
    pointer-events:none; backdrop-filter:blur(6px); max-width:65%;
  }
  .hud-tl .h-name { font-weight:900; font-size:14px; color:var(--neon); }
  .hud-tl .h-desc { font-size:11.5px; color:#cbd5e1; margin-top:2px; }
  .hud-tr {
    position:absolute; top:12px; right:14px; background:rgba(11,15,23,0.86);
    border:1px solid #364463; border-radius:9px; padding:6px 11px;
    font-size:12px; color:var(--dim); font-variant-numeric:tabular-nums; pointer-events:none;
  }
  .hud-br {
    position:absolute; bottom:11px; right:14px; background:rgba(11,15,23,0.84);
    border:1px solid #2d3953; border-radius:7px; padding:5px 10px;
    font-size:11.5px; color:#cbd5e1; pointer-events:none;
  }

  /* Compass 8-Angle Quick Selector */
  .angle-bar {
    display:grid; grid-template-columns:repeat(8, 1fr); gap:5px;
    background:var(--panel); border:1px solid var(--border); border-radius:11px; padding:6px;
  }
  .ang-btn {
    background:var(--panel2); color:var(--dim); border:1px solid #2d3850;
    border-radius:7px; padding:6px 4px; font:inherit; font-size:11.5px; font-weight:800;
    cursor:pointer; transition:0.12s;
  }
  .ang-btn:hover { color:var(--ink); border-color:#4d5f86; }
  .ang-btn.active { background:#1a3822; color:var(--neon); border-color:var(--neon); }

  .ctrl-row {
    display:flex; flex-wrap:wrap; gap:9px; align-items:center; justify-content:space-between;
    background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:10px 14px;
  }
  .ctrl-group { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
  .btn {
    background:var(--panel2); color:var(--ink); border:1px solid #384664;
    border-radius:8px; padding:7px 11px; font:inherit; font-size:12.5px; font-weight:700;
    cursor:pointer; transition:0.12s;
  }
  .btn:hover { border-color:var(--neon); }
  .btn.active, .btn.green { background:var(--neon); color:#071b0b; border-color:var(--neon); font-weight:800; }
  select.sel {
    background:var(--panel2); color:var(--ink); border:1px solid #384664;
    border-radius:8px; padding:6px 10px; font:inherit; font-size:12.5px; font-weight:700;
  }
  label.lbl { font-size:12px; color:var(--dim); display:flex; align-items:center; gap:6px; font-weight:600; }
  input[type=range] { accent-color:var(--neon); cursor:pointer; }

  /* Arena & WebGL3D Full-Width Panels */
  .full-panel {
    width:min(100%, 1140px); display:flex; flex-direction:column; gap:10px;
  }
  .arena-wrap, .gl-wrap {
    width:100%; height:min(68vh, 580px); min-height:400px; border-radius:14px;
    border:1px solid var(--border); background:#0c111b; position:relative; overflow:hidden;
  }
  #arena-canvas, #gl-canvas { width:100%; height:100%; display:block; touch-action:none; }

  /* Gallery Cards */
  .gallery-grid {
    width:min(100%, 1140px); display:flex; flex-direction:column; gap:16px;
  }
  .gal-card {
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    padding:14px; display:flex; flex-direction:column; gap:10px;
  }
  .gal-card h2 { margin:0; font-size:16px; color:var(--neon); }
  .gal-card p { margin:0; font-size:12.5px; color:var(--dim); }
  .gal-card img { width:100%; height:auto; border-radius:10px; border:1px solid #2b364e; display:block; }
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>
      <span>🟢🛞 Green-Suit Wheelman</span>
      <span class="pill">360° 3D Sprite • 12 Animations • WebGL 3D</span>
    </h1>
    <p class="sub">1,200 Studio-Lit 3D RGBA Sprite Frames (8 Angles × 12 Animations) + DarkPlaces <code>.SPR32</code> + Live 3D Contraption Model</p>
  </div>
  <div class="hdr-actions">
    <button class="dl-btn" id="btn-sfx-toggle">🔊 SFX: ON</button>
    <button class="dl-btn primary" id="btn-dl-glb">⬇ Download 3D Model (.GLB)</button>
    <a class="dl-btn" href="greensuit_wheelman.spr32" download="greensuit_wheelman.spr32">⬇ Quake .SPR32</a>
  </div>
</header>

<nav class="mode-bar">
  <button class="mode-tab active" data-mode="studio">🎡 360° 3D Sprite Studio (12 Anims)</button>
  <button class="mode-tab" data-mode="arena">🎮 Playable 2.5D Stunt Arena</button>
  <button class="mode-tab" data-mode="webgl3d">🧊 Live WebGL2 3D Mesh Viewer</button>
  <button class="mode-tab" data-mode="gallery">📸 Real Photo vs. 3D &amp; Sheets</button>
</nav>

<!-- ==================== MODE 1: 360° SPRITE STUDIO ==================== -->
<section class="workspace" id="sec-studio">
  <div class="anim-list" id="anim-list"></div>

  <div class="stage-col">
    <div class="stage-box bg-checker" id="stage-box">
      <canvas id="sprite-canvas"></canvas>
      <div class="hud-tl">
        <div class="h-name" id="hud-title">Seated Wheel-Cruise</div>
        <div class="h-desc" id="hud-desc"></div>
      </div>
      <div class="hud-tr" id="hud-meta">Angle 0° • Frame 1/12</div>
      <div class="hud-br">↔ Drag left/right to rotate 360° • Scroll to zoom • Keys 1–9 / Arrows</div>
    </div>

    <div class="angle-bar" id="angle-bar">
      <button class="ang-btn active" data-dir="0">0° Front</button>
      <button class="ang-btn" data-dir="1">45° Front-L</button>
      <button class="ang-btn" data-dir="2">90° Left</button>
      <button class="ang-btn" data-dir="3">135° Back-L</button>
      <button class="ang-btn" data-dir="4">180° Back</button>
      <button class="ang-btn" data-dir="5">225° Back-R</button>
      <button class="ang-btn" data-dir="6">270° Right</button>
      <button class="ang-btn" data-dir="7">315° Front-R</button>
    </div>

    <div class="ctrl-row">
      <div class="ctrl-group">
        <button class="btn green" id="btn-play">⏸ Pause</button>
        <button class="btn" id="btn-prev">◀</button>
        <button class="btn" id="btn-next">▶</button>
        <button class="btn" id="btn-turntable">🔄 Auto-Orbit 360°</button>
      </div>
      <div class="ctrl-group">
        <label class="lbl">Scrub <input type="range" id="rng-frame" min="0" max="11" value="0" style="width:95px"></label>
        <label class="lbl">FPS <input type="range" id="rng-fps" min="4" max="60" value="18" style="width:85px"><span id="lbl-fps">18</span></label>
        <label class="lbl">Zoom <input type="range" id="rng-zoom" min="60" max="185" value="108" style="width:80px"></label>
      </div>
      <div class="ctrl-group">
        <select class="sel" id="sel-bg">
          <option value="bg-checker">BG: Dark Checker</option>
          <option value="bg-studio">BG: Studio Grey (Photo 4)</option>
          <option value="bg-room">BG: Living Room Parquet</option>
          <option value="bg-quake">BG: Quake Arena</option>
          <option value="bg-magenta">BG: Chroma #FF00FF</option>
          <option value="bg-black">BG: Pure Black</option>
        </select>
        <button class="btn" id="btn-pixel">🔍 Pixel Mode: OFF</button>
      </div>
    </div>
  </div>
</section>

<!-- ==================== MODE 2: PLAYABLE 2.5D ARENA ==================== -->
<section class="full-panel hidden" id="sec-arena">
  <div class="arena-wrap">
    <canvas id="arena-canvas"></canvas>
    <div class="hud-tl">
      <div class="h-name">🎮 Green-Suit Wheelman Stunt Playground</div>
      <div class="h-desc">Drive with <b>WASD / Arrow Keys</b> or <b>Click/Touch</b> anywhere on the floor! Trigger stunts below or press <b>Space / 1–6</b>!</div>
    </div>
    <div class="hud-tr" id="arena-hud">Speed: 0 • Heading: 0°</div>
  </div>
  <div class="ctrl-row">
    <div class="ctrl-group">
      <button class="btn green" data-stunt="scream_turbo">⚡ [1] Turbo Sparks</button>
      <button class="btn" data-stunt="wheelie_backflip">🤸 [2] Wheelie Backflip</button>
      <button class="btn" data-stunt="plank_rollout">🏋️ [3] Plank Launch</button>
      <button class="btn" data-stunt="hero_crane_point">☝️ [4] Crane Sky-Point</button>
      <button class="btn" data-stunt="cyclone_spin">🌪️ [5] Cyclone Tornado</button>
      <button class="btn" data-stunt="throw_boomerang">🪃 [6] Throw Wheel Rig</button>
      <button class="btn" style="border-color:#f43f5e;color:#fda4af" data-stunt="gib_explosion">💥 [Space] GIB EXPLODE!</button>
    </div>
  </div>
</section>

<!-- ==================== MODE 3: LIVE WEBGL2 3D MODEL ==================== -->
<section class="full-panel hidden" id="sec-webgl3d">
  <div class="gl-wrap">
    <canvas id="gl-canvas"></canvas>
    <div class="hud-tl">
      <div class="h-name">🧊 Real-Time WebGL2 3D Mesh &amp; Stainless Contraption</div>
      <div class="h-desc">Full 3D geometry exported directly from Blender 5.2 (<code>greensuit_wheelman_3d.glb</code>). Drag in any direction (yaw + pitch above/below) &amp; scroll to zoom!</div>
    </div>
    <div class="hud-tr" id="gl-stats">Loading 3D Mesh...</div>
  </div>
  <div class="ctrl-row">
    <div class="ctrl-group">
      <button class="btn green active" id="btn-gl-spin">🔄 Auto-Turntable: ON</button>
      <button class="btn active" id="btn-gl-wheels">🛞 Spin 3D Tires: ON</button>
      <button class="btn" id="btn-gl-wire">🕸️ Wireframe: OFF</button>
      <button class="btn" id="btn-gl-reset">🎯 Reset Camera</button>
    </div>
  </div>
</section>

<!-- ==================== MODE 4: COMPARISON & GALLERY ==================== -->
<section class="gallery-grid hidden" id="sec-gallery">
  <div class="gal-card">
    <h2>📸 Real-Life Reference Photos vs. 3D Sprite Poses</h2>
    <p>Direct side-by-side comparison of the 4 reference poses against the sculpted &amp; rigged 3D character sprite.</p>
    <img id="img-ref-vs-3d" alt="Reference vs 3D Sprite Comparison">
  </div>
  <div class="gal-card">
    <h2>🧭 Full 8-Angle 360° Turnaround Sheet (0° → 315°)</h2>
    <p>Consistent 3D silhouette, sculpted nose/beard relief inside the stitched morphsuit hood opening, and mirror-stainless contraption across every angle.</p>
    <img id="img-turnaround" alt="360 Turnaround">
  </div>
  <div class="gal-card">
    <h2>🎬 All 12 360° 3D Animations Poster</h2>
    <p>1,200 rendered RGBA studio frames packed across 12 distinct animations.</p>
    <img id="img-poster" alt="12 Animations Poster">
  </div>
</section>

<script>
const PAYLOAD = __PAYLOAD_JSON__;

// ---------------------------------------------------------------------------
// 1. Procedural WebAudio Synthesizer (Zero External Audio Dependencies!)
// ---------------------------------------------------------------------------
let audioCtx = null;
let sfxEnabled = true;
function ensureAudio() {
  if (!sfxEnabled) return null;
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
  return audioCtx;
}

function playSFX(kind) {
  const ctx = ensureAudio();
  if (!ctx) return;
  const now = ctx.currentTime;
  if (kind === "sparks") {
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.22, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.08));
    const src = ctx.createBufferSource(); src.buffer = buf;
    const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 3400; bp.Q.value = 2.2;
    const g = ctx.createGain(); g.gain.setValueAtTime(0.18, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
    src.connect(bp).connect(g).connect(ctx.destination); src.start(now);
  } else if (kind === "boom") {
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.65, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.18));
    const src = ctx.createBufferSource(); src.buffer = buf;
    const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.setValueAtTime(420, now); lp.frequency.exponentialRampToValueAtTime(65, now + 0.6);
    const g = ctx.createGain(); g.gain.setValueAtTime(0.45, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.64);
    src.connect(lp).connect(g).connect(ctx.destination); src.start(now);
  } else if (kind === "whoosh" || kind === "whirl") {
    const osc = ctx.createOscillator(); osc.type = "sawtooth";
    osc.frequency.setValueAtTime(kind === "whirl" ? 190 : 140, now);
    osc.frequency.exponentialRampToValueAtTime(480, now + 0.14);
    osc.frequency.exponentialRampToValueAtTime(110, now + 0.30);
    const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 900;
    const g = ctx.createGain(); g.gain.setValueAtTime(0.12, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.31);
    osc.connect(lp).connect(g).connect(ctx.destination); osc.start(now); osc.stop(now + 0.32);
  } else if (kind === "fanfare" || kind === "guitar" || kind === "clang") {
    const notes = kind === "fanfare" ? [392, 523.25, 659.25] : (kind === "guitar" ? [164.8, 246.9, 329.6] : [580, 860]);
    notes.forEach((hz, idx) => {
      const o = ctx.createOscillator(); o.type = kind === "guitar" ? "sawtooth" : "triangle";
      o.frequency.setValueAtTime(hz, now + idx * 0.045);
      const g = ctx.createGain(); g.gain.setValueAtTime(0.10, now + idx * 0.045);
      g.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.045 + 0.28);
      o.connect(g).connect(ctx.destination); o.start(now + idx * 0.045); o.stop(now + idx * 0.045 + 0.30);
    });
  } else if (kind === "roll") {
    const o = ctx.createOscillator(); o.type = "sine";
    o.frequency.setValueAtTime(85, now); o.frequency.exponentialRampToValueAtTime(125, now + 0.12);
    const g = ctx.createGain(); g.gain.setValueAtTime(0.09, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
    o.connect(g).connect(ctx.destination); o.start(now); o.stop(now + 0.15);
  }
}

document.getElementById("btn-sfx-toggle").onclick = (e) => {
  sfxEnabled = !sfxEnabled;
  e.currentTarget.textContent = sfxEnabled ? "🔊 SFX: ON" : "🔇 SFX: OFF";
};

// Download embedded .GLB directly from base64
document.getElementById("btn-dl-glb").onclick = () => {
  const bin = atob(PAYLOAD.glbB64);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  const blob = new Blob([u8], { type: "model/gltf-binary" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "greensuit_wheelman_3d.glb";
  a.click();
};

// Populate Gallery Images
document.getElementById("img-ref-vs-3d").src = PAYLOAD.sheets.refVs3d;
document.getElementById("img-turnaround").src = PAYLOAD.sheets.turnaround;
document.getElementById("img-poster").src = PAYLOAD.sheets.poster;

// Preload all 12 Atlas Images
const ATLAS_IMGS = {};
let loadedCount = 0;
PAYLOAD.anims.forEach(a => {
  const im = new Image();
  im.onload = () => { loadedCount++; };
  im.src = PAYLOAD.atlases[a.id];
  ATLAS_IMGS[a.id] = im;
});

// ---------------------------------------------------------------------------
// 2. Mode Tab Switching
// ---------------------------------------------------------------------------
let activeMode = "studio";
document.querySelectorAll(".mode-tab").forEach(btn => {
  btn.onclick = () => {
    activeMode = btn.dataset.mode;
    document.querySelectorAll(".mode-tab").forEach(b => b.classList.toggle("active", b === btn));
    document.getElementById("sec-studio").classList.toggle("hidden", activeMode !== "studio");
    document.getElementById("sec-arena").classList.toggle("hidden", activeMode !== "arena");
    document.getElementById("sec-webgl3d").classList.toggle("hidden", activeMode !== "webgl3d");
    document.getElementById("sec-gallery").classList.toggle("hidden", activeMode !== "gallery");
    if (activeMode === "webgl3d") initWebGLViewer();
  };
});

// ---------------------------------------------------------------------------
// 3. Mode 1: 360° 3D Sprite Studio
// ---------------------------------------------------------------------------
const animListEl = document.getElementById("anim-list");
let curAnimIdx = 0;
let curDir = 0;
let curFrame = 0;
let playing = true;
let autoOrbit = false;
let pixelMode = false;
let fps = 18;
let zoom = 1.08;
let accumMs = 0;
let orbitAccum = 0;

function selectAnim(idx, triggerAudio = true) {
  curAnimIdx = (idx + PAYLOAD.anims.length) % PAYLOAD.anims.length;
  const a = PAYLOAD.anims[curAnimIdx];
  curFrame = 0;
  fps = a.fps;
  document.getElementById("rng-fps").value = fps;
  document.getElementById("lbl-fps").textContent = fps;
  document.getElementById("rng-frame").max = a.frames - 1;
  document.getElementById("rng-frame").value = 0;
  document.getElementById("hud-title").textContent = `${a.icon} ${a.title}`;
  document.getElementById("hud-desc").textContent = a.desc;
  document.querySelectorAll(".anim-card").forEach((el, i) => el.classList.toggle("active", i === curAnimIdx));
  if (triggerAudio) playSFX(a.sfx);
}

PAYLOAD.anims.forEach((a, i) => {
  const btn = document.createElement("button");
  btn.className = "anim-card" + (i === 0 ? " active" : "");
  btn.innerHTML = `
    <div class="anim-ico">${a.icon}</div>
    <div class="anim-info">
      <div class="anim-title">${i + 1}. ${a.title}</div>
      <div class="anim-meta"><span class="mini-badge">${a.badge}</span><span>8×${a.frames}f (${8 * a.frames}f)</span></div>
    </div>`;
  btn.onclick = () => selectAnim(i, true);
  animListEl.appendChild(btn);
});

function setDir(d) {
  curDir = ((d % 8) + 8) % 8;
  document.querySelectorAll(".ang-btn").forEach(b => b.classList.toggle("active", Number(b.dataset.dir) === curDir));
}
document.querySelectorAll(".ang-btn").forEach(b => {
  b.onclick = () => { autoOrbit = false; document.getElementById("btn-turntable").classList.remove("active"); setDir(Number(b.dataset.dir)); };
});

document.getElementById("btn-play").onclick = (e) => {
  playing = !playing;
  e.currentTarget.textContent = playing ? "⏸ Pause" : "▶ Play";
  e.currentTarget.classList.toggle("green", playing);
};
document.getElementById("btn-prev").onclick = () => {
  playing = false; document.getElementById("btn-play").textContent = "▶ Play"; document.getElementById("btn-play").classList.remove("green");
  const nf = PAYLOAD.anims[curAnimIdx].frames;
  curFrame = (curFrame - 1 + nf) % nf;
  document.getElementById("rng-frame").value = curFrame;
};
document.getElementById("btn-next").onclick = () => {
  playing = false; document.getElementById("btn-play").textContent = "▶ Play"; document.getElementById("btn-play").classList.remove("green");
  const nf = PAYLOAD.anims[curAnimIdx].frames;
  curFrame = (curFrame + 1) % nf;
  document.getElementById("rng-frame").value = curFrame;
};
document.getElementById("btn-turntable").onclick = (e) => {
  autoOrbit = !autoOrbit;
  e.currentTarget.classList.toggle("active", autoOrbit);
};
document.getElementById("rng-frame").oninput = (e) => { curFrame = Number(e.target.value); };
document.getElementById("rng-fps").oninput = (e) => { fps = Number(e.target.value); document.getElementById("lbl-fps").textContent = fps; };
document.getElementById("rng-zoom").oninput = (e) => { zoom = Number(e.target.value) / 100; };
document.getElementById("sel-bg").onchange = (e) => {
  const sb = document.getElementById("stage-box");
  sb.className = "stage-box " + e.target.value;
};
document.getElementById("btn-pixel").onclick = (e) => {
  pixelMode = !pixelMode;
  e.currentTarget.textContent = pixelMode ? "🔍 Pixel Mode: ON (Retro)" : "🔍 Pixel Mode: OFF";
  e.currentTarget.classList.toggle("active", pixelMode);
};

// Drag-to-orbit 360° on stageBox
const stageBox = document.getElementById("stage-box");
let dragging = false, dragStartX = 0, dragStartDir = 0;
stageBox.addEventListener("pointerdown", (e) => {
  dragging = true; dragStartX = e.clientX; dragStartDir = curDir;
  stageBox.setPointerCapture(e.pointerId);
});
stageBox.addEventListener("pointermove", (e) => {
  if (!dragging) return;
  const steps = Math.round((e.clientX - dragStartX) / 36);
  setDir(dragStartDir + steps);
});
stageBox.addEventListener("pointerup", () => { dragging = false; });
stageBox.addEventListener("wheel", (e) => {
  e.preventDefault();
  zoom = Math.max(0.6, Math.min(1.85, zoom - e.deltaY * 0.0008));
  document.getElementById("rng-zoom").value = Math.round(zoom * 100);
}, { passive: false });

const sprCanvas = document.getElementById("sprite-canvas");
const sprCtx = sprCanvas.getContext("2d");

function renderStudioSprite() {
  const dpr = window.devicePixelRatio || 1;
  const w = stageBox.clientWidth, h = stageBox.clientHeight;
  if (sprCanvas.width !== Math.round(w * dpr) || sprCanvas.height !== Math.round(h * dpr)) {
    sprCanvas.width = Math.round(w * dpr);
    sprCanvas.height = Math.round(h * dpr);
  }
  sprCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  sprCtx.clearRect(0, 0, w, h);

  const a = PAYLOAD.anims[curAnimIdx];
  const im = ATLAS_IMGS[a.id];
  if (!im || !im.complete) return;

  const cw = a.cellW, ch = a.cellH;
  const drawSz = Math.min(w, h) * 0.88 * zoom;
  const dx = (w - drawSz) * 0.5;
  const dy = (h - drawSz) * 0.52;

  if (pixelMode) {
    // Authentic chunky retro 140x140 nearest-neighbor Quake sprite preview!
    if (!window._pixCnv) { window._pixCnv = document.createElement("canvas"); window._pixCnv.width = 128; window._pixCnv.height = 128; }
    const pctx = window._pixCnv.getContext("2d");
    pctx.clearRect(0, 0, 128, 128);
    pctx.imageSmoothingEnabled = true;
    pctx.drawImage(im, curFrame * cw, curDir * ch, cw, ch, 0, 0, 128, 128);
    sprCtx.imageSmoothingEnabled = false;
    sprCtx.drawImage(window._pixCnv, dx, dy, drawSz, drawSz);
  } else {
    sprCtx.imageSmoothingEnabled = true;
    sprCtx.imageSmoothingQuality = "high";
    sprCtx.drawImage(im, curFrame * cw, curDir * ch, cw, ch, dx, dy, drawSz, drawSz);
  }

  document.getElementById("hud-meta").textContent =
    `Angle ${curDir * 45}° (d${curDir}) • Frame ${curFrame + 1}/${a.frames} • ${cw}×${ch} RGBA`;
}

// ---------------------------------------------------------------------------
// 4. Mode 2: Playable 2.5D Driving & Stunt Arena
// ---------------------------------------------------------------------------
const arenaCanvas = document.getElementById("arena-canvas");
const arenaCtx = arenaCanvas.getContext("2d");
const keys = {};
const player = {
  x: 0, y: 0, vx: 0, vy: 0, heading: Math.PI * 0.5, // facing toward camera (+Y screen)
  anim: "seated_cruise", frame: 0, animTimer: 0, stuntLock: 0,
  skids: [], sparks: [], target: null,
};

window.addEventListener("keydown", (e) => {
  keys[e.code] = true;
  if (activeMode === "studio") {
    if (e.code === "ArrowLeft") setDir(curDir - 1);
    else if (e.code === "ArrowRight") setDir(curDir + 1);
    else if (e.code === "ArrowUp") { e.preventDefault(); selectAnim(curAnimIdx - 1); }
    else if (e.code === "ArrowDown") { e.preventDefault(); selectAnim(curAnimIdx + 1); }
  } else if (activeMode === "arena") {
    const stuntMap = {
      Digit1: "scream_turbo", Digit2: "wheelie_backflip", Digit3: "plank_rollout",
      Digit4: "hero_crane_point", Digit5: "cyclone_spin", Digit6: "throw_boomerang",
      Space: "gib_explosion",
    };
    if (stuntMap[e.code]) { e.preventDefault(); triggerArenaStunt(stuntMap[e.code]); }
  }
});
window.addEventListener("keyup", (e) => { keys[e.code] = false; });

function triggerArenaStunt(stuntId) {
  player.anim = stuntId;
  player.frame = 0;
  player.animTimer = 0;
  const spec = PAYLOAD.anims.find(x => x.id === stuntId);
  player.stuntLock = spec ? (spec.frames / spec.fps) : 0.7;
  playSFX(spec ? spec.sfx : "whoosh");
  if (stuntId === "scream_turbo") {
    player.vx += Math.cos(player.heading) * 320;
    player.vy += Math.sin(player.heading) * 320;
  }
}
document.querySelectorAll("[data-stunt]").forEach(btn => {
  btn.onclick = () => triggerArenaStunt(btn.dataset.stunt);
});

arenaCanvas.addEventListener("pointerdown", (e) => {
  const r = arenaCanvas.getBoundingClientRect();
  player.target = { x: (e.clientX - r.left) - r.width * 0.5, y: (e.clientY - r.top) - r.height * 0.56 };
});

function updateAndRenderArena(dt) {
  const dpr = window.devicePixelRatio || 1;
  const w = arenaCanvas.clientWidth, h = arenaCanvas.clientHeight;
  if (arenaCanvas.width !== Math.round(w * dpr) || arenaCanvas.height !== Math.round(h * dpr)) {
    arenaCanvas.width = Math.round(w * dpr); arenaCanvas.height = Math.round(h * dpr);
  }
  arenaCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Input acceleration
  let ax = 0, ay = 0;
  if (keys.KeyW || keys.ArrowUp) ay -= 1;
  if (keys.KeyS || keys.ArrowDown) ay += 1;
  if (keys.KeyA || keys.ArrowLeft) ax -= 1;
  if (keys.KeyD || keys.ArrowRight) ax += 1;
  if (ax !== 0 || ay !== 0) player.target = null;
  if (player.target) {
    const dx = player.target.x - player.x, dy = player.target.y - player.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 14) { ax = dx / dist; ay = dy / dist; } else { player.target = null; }
  }

  const accel = (keys.ShiftLeft || player.anim === "scream_turbo") ? 920 : 620;
  if (ax !== 0 || ay !== 0) {
    const len = Math.hypot(ax, ay);
    player.vx += (ax / len) * accel * dt;
    player.vy += (ay / len) * accel * dt;
    player.heading = Math.atan2(ay, ax);
  }
  player.vx *= Math.pow(0.06, dt);
  player.vy *= Math.pow(0.06, dt);
  player.x = Math.max(-w * 0.44, Math.min(w * 0.44, player.x + player.vx * dt));
  player.y = Math.max(-h * 0.34, Math.min(h * 0.34, player.y + player.vy * dt));

  const spd = Math.hypot(player.vx, player.vy);
  if (spd > 45) {
    const perpX = -Math.sin(player.heading) * 24, perpY = Math.cos(player.heading) * 14;
    player.skids.push({ x: player.x + perpX, y: player.y + perpY, a: 0.45 });
    player.skids.push({ x: player.x - perpX, y: player.y - perpY, a: 0.45 });
    if (player.skids.length > 260) player.skids.splice(0, 2);
  }
  if (player.anim === "scream_turbo" || spd > 240) {
    for (let i = 0; i < 2; i++) {
      player.sparks.push({
        x: player.x, y: player.y + 8,
        vx: (Math.random() - 0.5) * 180 - player.vx * 0.35,
        vy: (Math.random() - 0.8) * 140 - player.vy * 0.35,
        life: 0.35,
      });
    }
  }
  player.sparks.forEach(s => { s.x += s.vx * dt; s.y += s.vy * dt; s.vy += 260 * dt; s.life -= dt; });
  player.sparks = player.sparks.filter(s => s.life > 0);

  if (player.stuntLock > 0) {
    player.stuntLock -= dt;
    if (player.stuntLock <= 0) player.anim = "seated_cruise";
  } else {
    player.anim = (keys.ShiftLeft && spd > 40) ? "scream_turbo" : "seated_cruise";
  }

  const spec = PAYLOAD.anims.find(x => x.id === player.anim) || PAYLOAD.anims[0];
  const rate = player.stuntLock > 0 ? spec.fps : Math.max(4, Math.min(30, spd * 0.08));
  player.animTimer += dt * rate;
  if (spd > 8 || player.stuntLock > 0) {
    player.frame = Math.floor(player.animTimer) % spec.frames;
  } else {
    player.frame = 0;
  }

  // Convert screen-plane heading (0=+X right, +90°=+Y toward viewer/front d=0!) to 8-angle sprite dir!
  // Recall in Blender: d=0 is Front (moving +Y toward camera = +90°),
  // d=2 is Left Profile (cam at +X -> char faces -X left = 180°? Let's verify:
  // At d=1 (+45° cam_rig Z rot), cam is at (+sin45, -cos45) = front-left of character (+X is char's left = viewer's right),
  // so character faces down-left on screen (+135°)!
  // Let's check: heading=+90° (down toward viewer) -> d=0; heading=+135° (down-left) -> d=7 or d=1!
  // Let's check 02_seated_045.png: at d=1, character faces viewer's LEFT (screen -X, heading=135°)!
  // Yes!! At d=0: +90° (down); d=1: +135° (down-left); d=2: 180° (left); d=3: -135° (up-left);
  // d=4: -90° (up/away); d=5: -45° (up-right); d=6: 0° (right); d=7: +45° (down-right)!
  const relDeg = ((player.heading * 180 / Math.PI) - 90 + 360) % 360;
  const dirIdx = Math.round(relDeg / 45) % 8;

  // Draw Arena Perspective Floor & Parquet Horizon
  const grad = arenaCtx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "#101726");
  grad.addColorStop(0.26, "#1c2840");
  grad.addColorStop(0.27, "#2a2017");
  grad.addColorStop(1, "#17110c");
  arenaCtx.fillStyle = grad;
  arenaCtx.fillRect(0, 0, w, h);

  // Perspective grid lines
  const horY = h * 0.27;
  arenaCtx.strokeStyle = "rgba(126,244,66,0.13)";
  arenaCtx.lineWidth = 1;
  for (let i = -10; i <= 10; i++) {
    arenaCtx.beginPath();
    arenaCtx.moveTo(w * 0.5 + i * 38, horY);
    arenaCtx.lineTo(w * 0.5 + i * 145, h);
    arenaCtx.stroke();
  }
  for (let r = 0; r <= 8; r++) {
    const t = Math.pow(r / 8, 1.55);
    const y = horY + (h - horY) * t;
    arenaCtx.beginPath(); arenaCtx.moveTo(0, y); arenaCtx.lineTo(w, y); arenaCtx.stroke();
  }

  const cx = w * 0.5, cy = h * 0.58;
  // Tire skid marks
  player.skids.forEach(s => {
    s.a *= 0.994;
    arenaCtx.fillStyle = `rgba(12,14,18,${s.a.toFixed(3)})`;
    arenaCtx.fillRect(cx + s.x - 3, cy + s.y + 42, 6, 4);
  });

  // Draw Sprite scaled by depth Y!
  const im = ATLAS_IMGS[spec.id];
  if (im && im.complete) {
    const depthScale = 0.78 + 0.44 * ((player.y + h * 0.34) / (h * 0.68));
    const sz = 215 * depthScale;
    arenaCtx.drawImage(im, player.frame * spec.cellW, dirIdx * spec.cellH, spec.cellW, spec.cellH, cx + player.x - sz * 0.5, cy + player.y - sz * 0.62, sz, sz);
  }

  // Sparks
  player.sparks.forEach(s => {
    arenaCtx.fillStyle = s.life > 0.18 ? "#fef08a" : "#fb923c";
    arenaCtx.fillRect(cx + s.x - 2, cy + s.y + 32, 4, 4);
  });

  document.getElementById("arena-hud").textContent =
    `Speed: ${Math.round(spd)} px/s • Sprite Angle: ${dirIdx * 45}° (d${dirIdx}) • Anim: ${spec.title}`;
}

// ---------------------------------------------------------------------------
// 5. Mode 3: Dependency-Free Vanilla WebGL2 PBR .GLB Viewer!
// ---------------------------------------------------------------------------
let glInited = false;
let glState = { yaw: 0.45, pitch: 0.25, dist: 1.55, autoSpin: true, spinWheels: true, wire: false, wheelAngle: 0, draws: [] };

async function initWebGLViewer() {
  if (glInited) return;
  glInited = true;
  const canvas = document.getElementById("gl-canvas");
  const gl = canvas.getContext("webgl2", { antialias: true, alpha: false });
  if (!gl) { document.getElementById("gl-stats").textContent = "WebGL2 unavailable"; return; }
  glState.gl = gl;

  // Parse embedded binary GLB!
  const binStr = atob(PAYLOAD.glbB64);
  const bytes = new Uint8Array(binStr.length);
  for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
  const dv = new DataView(bytes.buffer);
  const jsonLen = dv.getUint32(12, true);
  const gltf = JSON.parse(new TextDecoder().decode(bytes.subarray(20, 20 + jsonLen)));
  const binOffset = 20 + jsonLen + 8;

  // Decode embedded GLB images into WebGL textures
  const glTextures = [];
  if (gltf.images) {
    for (const imgDef of gltf.images) {
      const bv = gltf.bufferViews[imgDef.bufferView];
      const slice = bytes.subarray(binOffset + (bv.byteOffset || 0), binOffset + (bv.byteOffset || 0) + bv.byteLength);
      const blob = new Blob([slice], { type: imgDef.mimeType || "image/png" });
      const bmp = await createImageBitmap(blob);
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bmp);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      glTextures.push(tex);
    }
  }

  // Compile PBR Metallic-Roughness + Studio Environment Reflection Shader
  const vsSrc = `#version 300 es
  layout(location=0) in vec3 aPos;
  layout(location=1) in vec3 aNorm;
  layout(location=2) in vec2 aUV;
  uniform mat4 uMVP, uModel;
  out vec3 vNorm, vWorldPos;
  out vec2 vUV;
  void main() {
    vec4 wp = uModel * vec4(aPos, 1.0);
    vWorldPos = wp.xyz;
    vNorm = mat3(uModel) * aNorm;
    vUV = aUV;
    gl_Position = uMVP * vec4(aPos, 1.0);
  }`;

  const fsSrc = `#version 300 es
  precision highp float;
  in vec3 vNorm, vWorldPos;
  in vec2 vUV;
  uniform vec4 uBaseCol;
  uniform vec2 uMetRough;
  uniform int uHasTex;
  uniform sampler2D uTex;
  uniform vec3 uCamPos;
  out vec4 fragColor;
  void main() {
    vec3 N = normalize(vNorm);
    vec3 V = normalize(uCamPos - vWorldPos);
    vec3 base = uBaseCol.rgb;
    if (uHasTex == 1) {
      vec3 tc = texture(uTex, vUV).rgb;
      base *= pow(tc, vec3(2.2));
    }
    float metallic = uMetRough.x;
    float rough = clamp(uMetRough.y, 0.06, 1.0);

    vec3 L1 = normalize(vec3(0.55, 0.72, 0.62));
    vec3 L2 = normalize(vec3(-0.65, 0.42, 0.48));
    vec3 L3 = normalize(vec3(0.0, 0.55, -0.82));

    float ndl1 = max(dot(N, L1), 0.0);
    float ndl2 = max(dot(N, L2), 0.0);
    float ndl3 = max(dot(N, L3), 0.0);

    vec3 diff = base * (1.0 - metallic * 0.88) * (0.26 + 0.85 * ndl1 + 0.38 * ndl2 + 0.30 * ndl3);

    // Studio softbox environment reflection for mirror-polished stainless steel!
    vec3 R = reflect(-V, N);
    float skyBand = smoothstep(-0.15, 0.35, R.y);
    float strip = pow(max(0.0, 1.0 - abs(R.y - 0.18) * 3.5), 3.0);
    vec3 envCol = mix(vec3(0.10, 0.12, 0.15), vec3(0.88, 0.92, 0.98), skyBand) + vec3(0.85) * strip * (1.0 - rough);
    vec3 F0 = mix(vec3(0.04), base, metallic);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 4.0);
    vec3 specEnv = (F0 + (1.0 - F0) * fres * 0.55) * envCol * (1.0 - rough * 0.72);

    vec3 H1 = normalize(L1 + V);
    float shin = mix(128.0, 8.0, rough);
    vec3 specSun = F0 * pow(max(dot(N, H1), 0.0), shin) * (1.6 - rough);

    vec3 lin = diff + specEnv * (0.28 + 0.78 * metallic) + specSun;
    // Tone-map & gamma encode
    lin = lin / (lin + vec3(0.82)) * 1.38;
    fragColor = vec4(pow(clamp(lin, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
  }`;

  function compile(type, src) {
    const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, vsSrc));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fsSrc));
  gl.linkProgram(prog);
  glState.prog = prog;
  glState.locs = {
    uMVP: gl.getUniformLocation(prog, "uMVP"),
    uModel: gl.getUniformLocation(prog, "uModel"),
    uBaseCol: gl.getUniformLocation(prog, "uBaseCol"),
    uMetRough: gl.getUniformLocation(prog, "uMetRough"),
    uHasTex: gl.getUniformLocation(prog, "uHasTex"),
    uCamPos: gl.getUniformLocation(prog, "uCamPos"),
  };

  function getAcc(accIdx) {
    const acc = gltf.accessors[accIdx];
    const bv = gltf.bufferViews[acc.bufferView];
    const off = binOffset + (bv.byteOffset || 0) + (acc.byteOffset || 0);
    const comps = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[acc.type];
    const bpc = { 5126: 4, 5123: 2, 5125: 4, 5121: 1 }[acc.componentType] || 4;
    const len = acc.count * comps;
    const stride = bv.byteStride || (comps * bpc);
    if (stride === comps * bpc) {
      const aligned = bytes.slice(off, off + len * bpc).buffer;
      if (acc.componentType === 5126) return new Float32Array(aligned);
      if (acc.componentType === 5123) return new Uint16Array(aligned);
      if (acc.componentType === 5125) return new Uint32Array(aligned);
      if (acc.componentType === 5121) return new Uint16Array(new Uint8Array(aligned));
    } else {
      const dvAcc = new DataView(bytes.buffer, bytes.byteOffset);
      if (acc.componentType === 5126) {
        const out = new Float32Array(len);
        for (let i = 0; i < acc.count; i++)
          for (let c = 0; c < comps; c++) out[i * comps + c] = dvAcc.getFloat32(off + i * stride + c * 4, true);
        return out;
      }
    }
    return null;
  }

  function mat4Mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++)
      for (let r = 0; r < 4; r++)
        o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
    return o;
  }
  function nodeLocalMat(nd) {
    if (nd.matrix) return new Float32Array(nd.matrix);
    const t = nd.translation || [0, 0, 0], q = nd.rotation || [0, 0, 0, 1], s = nd.scale || [1, 1, 1];
    const [x, y, z, w] = q;
    const x2 = x + x, y2 = y + y, z2 = z + z;
    const xx = x * x2, xy = x * y2, xz = x * z2, yy = y * y2, yz = y * z2, zz = z * z2;
    const wx = w * x2, wy = w * y2, wz = w * z2;
    return new Float32Array([
      (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
      (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
      (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
      t[0], t[1], t[2], 1,
    ]);
  }

  let totVerts = 0, totTris = 0;
  function walkNode(nIdx, parentMat) {
    const nd = gltf.nodes[nIdx];
    const m = mat4Mul(parentMat, nodeLocalMat(nd));
    const isWheel = (nd.name || "").includes("Wheel");
    if (nd.mesh !== undefined) {
      const mesh = gltf.meshes[nd.mesh];
      for (const prim of mesh.primitives) {
        const pos = getAcc(prim.attributes.POSITION);
        const norm = prim.attributes.NORMAL !== undefined ? getAcc(prim.attributes.NORMAL) : new Float32Array(pos.length);
        const uv = prim.attributes.TEXCOORD_0 !== undefined ? getAcc(prim.attributes.TEXCOORD_0) : new Float32Array((pos.length / 3) * 2);
        const idx = getAcc(prim.indices);
        totVerts += pos.length / 3;
        totTris += idx.length / 3;

        const vao = gl.createVertexArray();
        gl.bindVertexArray(vao);
        const mkBuf = (loc, data, sz) => {
          const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
          gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
          gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, sz, gl.FLOAT, false, 0, 0);
        };
        mkBuf(0, pos, 3); mkBuf(1, norm, 3); mkBuf(2, uv, 2);
        const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);

        let baseCol = [0.85, 0.85, 0.85, 1], met = 0.0, rough = 0.5, texObj = null;
        if (prim.material !== undefined) {
          const mat = gltf.materials[prim.material];
          const pbr = mat.pbrMetallicRoughness || {};
          if (pbr.baseColorFactor) baseCol = pbr.baseColorFactor;
          if (pbr.metallicFactor !== undefined) met = pbr.metallicFactor;
          if (pbr.roughnessFactor !== undefined) rough = pbr.roughnessFactor;
          if (pbr.baseColorTexture !== undefined) {
            const tDef = gltf.textures[pbr.baseColorTexture.index];
            texObj = glTextures[tDef.source];
          }
        }
        glState.draws.push({
          vao, count: idx.length, indexType: idx instanceof Uint32Array ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT,
          baseMat: m, isWheel: isWheel || (mesh.name || "").includes("Wheel"), baseCol, met, rough, texObj,
        });
      }
    }
    if (nd.children) nd.children.forEach(ch => walkNode(ch, m));
  }
  const ident = new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
  gltf.scenes[gltf.scene || 0].nodes.forEach(n => walkNode(n, ident));
  glState.mat4Mul = mat4Mul;
  document.getElementById("gl-stats").textContent =
    `${totVerts.toLocaleString()} Verts • ${totTris.toLocaleString()} Tris • PBR GLB`;

  // Orbit drag & zoom on gl-canvas
  let gDrag = false, gx = 0, gy = 0;
  canvas.addEventListener("pointerdown", (e) => { gDrag = true; gx = e.clientX; gy = e.clientY; glState.autoSpin = false; document.getElementById("btn-gl-spin").classList.remove("active"); canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!gDrag) return;
    glState.yaw -= (e.clientX - gx) * 0.009;
    glState.pitch = Math.max(-0.7, Math.min(1.35, glState.pitch + (e.clientY - gy) * 0.008));
    gx = e.clientX; gy = e.clientY;
  });
  canvas.addEventListener("pointerup", () => { gDrag = false; });
  canvas.addEventListener("wheel", (e) => { e.preventDefault(); glState.dist = Math.max(0.75, Math.min(3.5, glState.dist + e.deltaY * 0.0012)); }, { passive: false });
}

document.getElementById("btn-gl-spin").onclick = (e) => { glState.autoSpin = !glState.autoSpin; e.currentTarget.classList.toggle("active", glState.autoSpin); e.currentTarget.textContent = glState.autoSpin ? "🔄 Auto-Turntable: ON" : "🔄 Auto-Turntable: OFF"; };
document.getElementById("btn-gl-wheels").onclick = (e) => { glState.spinWheels = !glState.spinWheels; e.currentTarget.classList.toggle("active", glState.spinWheels); e.currentTarget.textContent = glState.spinWheels ? "🛞 Spin 3D Tires: ON" : "🛞 Spin 3D Tires: OFF"; };
document.getElementById("btn-gl-wire").onclick = (e) => { glState.wire = !glState.wire; e.currentTarget.classList.toggle("active", glState.wire); e.currentTarget.textContent = glState.wire ? "🕸️ Wireframe: ON" : "🕸️ Wireframe: OFF"; };
document.getElementById("btn-gl-reset").onclick = () => { glState.yaw = 0.45; glState.pitch = 0.25; glState.dist = 1.55; };

function renderWebGL3D(dt) {
  const gl = glState.gl;
  if (!gl || !glState.prog) return;
  const canvas = gl.canvas;
  const dpr = window.devicePixelRatio || 1;
  const w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.06, 0.08, 0.12, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  if (glState.autoSpin) glState.yaw += dt * 0.65;
  if (glState.spinWheels) glState.wheelAngle -= dt * 4.5;

  const target = [0, 0.38, 0];
  const cx = target[0] + glState.dist * Math.cos(glState.pitch) * Math.sin(glState.yaw);
  const cy = target[1] + glState.dist * Math.sin(glState.pitch);
  const cz = target[2] + glState.dist * Math.cos(glState.pitch) * Math.cos(glState.yaw);

  // Perspective + LookAt
  const aspect = w / Math.max(1, h), f = 1.0 / Math.tan(42 * Math.PI / 360), nf = 1 / (0.05 - 25.0);
  const proj = new Float32Array([f / aspect,0,0,0, 0,f,0,0, 0,0,(25+0.05)*nf,-1, 0,0,2*25*0.05*nf,0]);
  let fx = target[0]-cx, fy = target[1]-cy, fz = target[2]-cz;
  let fl = Math.hypot(fx,fy,fz); fx/=fl; fy/=fl; fz/=fl;
  let sx = fy*0 - fz*1, sy = fz*0 - fx*0, sz = fx*1 - fy*0; // cross(f, [0,1,0]) -> [ -fz, 0, fx ]
  sx = -fz; sy = 0; sz = fx;
  let sl = Math.hypot(sx,sy,sz) || 1; sx/=sl; sz/=sl;
  const ux = sy*fz - sz*fy, uy = sz*fx - sx*fz, uz = sx*fy - sy*fx;
  const view = new Float32Array([
    sx, ux, -fx, 0,
    sy, uy, -fy, 0,
    sz, uz, -fz, 0,
    -(sx*cx+sy*cy+sz*cz), -(ux*cx+uy*cy+uz*cz), (fx*cx+fy*cy+fz*cz), 1,
  ]);
  const vp = glState.mat4Mul(proj, view);

  const ca = Math.cos(glState.wheelAngle), sa = Math.sin(glState.wheelAngle);
  const rotX = new Float32Array([1,0,0,0, 0,ca,sa,0, 0,-sa,ca,0, 0,0,0,1]);

  gl.useProgram(glState.prog);
  gl.uniform3f(glState.locs.uCamPos, cx, cy, cz);
  for (const d of glState.draws) {
    const m = d.isWheel ? glState.mat4Mul(d.baseMat, rotX) : d.baseMat;
    const mvp = glState.mat4Mul(vp, m);
    gl.uniformMatrix4fv(glState.locs.uModel, false, m);
    gl.uniformMatrix4fv(glState.locs.uMVP, false, mvp);
    gl.uniform4fv(glState.locs.uBaseCol, d.baseCol);
    gl.uniform2f(glState.locs.uMetRough, d.met, d.rough);
    if (d.texObj) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, d.texObj);
      gl.uniform1i(glState.locs.uHasTex, 1);
    } else {
      gl.uniform1i(glState.locs.uHasTex, 0);
    }
    gl.bindVertexArray(d.vao);
    gl.drawElements(glState.wire ? gl.LINES : gl.TRIANGLES, d.count, d.indexType, 0);
  }
}

// ---------------------------------------------------------------------------
// 6. Main 60Hz Animation Loop
// ---------------------------------------------------------------------------
selectAnim(0, false);
let lastT = performance.now();
function tick(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000);
  lastT = now;

  if (activeMode === "studio") {
    if (playing) {
      accumMs += dt * 1000;
      const stepMs = 1000 / Math.max(1, fps);
      while (accumMs >= stepMs) {
        accumMs -= stepMs;
        const nf = PAYLOAD.anims[curAnimIdx].frames;
        curFrame = (curFrame + 1) % nf;
        document.getElementById("rng-frame").value = curFrame;
      }
    }
    if (autoOrbit && !dragging) {
      orbitAccum += dt;
      if (orbitAccum >= 0.28) { orbitAccum = 0; setDir(curDir + 1); }
    }
    renderStudioSprite();
  } else if (activeMode === "arena") {
    updateAndRenderArena(dt);
  } else if (activeMode === "webgl3d") {
    renderWebGL3D(dt);
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def main() -> None:
    with open(os.path.join(SPR_DIR, "sprite_meta.json"), "r", encoding="utf-8") as fp:
        smeta = json.load(fp)
    meta_by_id = {m["id"]: m for m in smeta["anims"]}

    anims_payload: List[Dict] = []
    atlases_b64: Dict[str, str] = {}
    for ui in ANIMS_UI:
        aid = ui["id"]
        m = meta_by_id[aid]
        anims_payload.append({**m, **ui})
        atlases_b64[aid] = b64_file(os.path.join(ATLAS_DIR, f"{aid}.webp"), "image/webp")

    with open(GLB_PATH, "rb") as fp:
        glb_b64 = base64.b64encode(fp.read()).decode("ascii")

    sheets = {
        "refVs3d": b64_jpg_resized(os.path.join(SPR_DIR, "greensuit_ref_vs_3d.jpg"), max_w=1360, quality=90),
        "turnaround": b64_jpg_resized(os.path.join(SPR_DIR, "greensuit_360_turnaround.jpg"), max_w=1400, quality=90),
        "poster": b64_jpg_resized(os.path.join(SPR_DIR, "greensuit_12anims_poster.jpg"), max_w=1280, quality=89),
    }

    payload_json = json.dumps(
        {"anims": anims_payload, "atlases": atlases_b64, "glbB64": glb_b64, "sheets": sheets},
        separators=(",", ":"),
    )
    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_json)

    for p in (OUT_HTML_ROOT, OUT_HTML_SPR):
        with open(p, "w", encoding="utf-8") as fp:
            fp.write(html)
        print(f"Wrote self-contained HTML -> {p} ({os.path.getsize(p) / 1048576:.2f} MB)")


if __name__ == "__main__":
    main()
