"""Build the interactive Kyle Tillet Projectile & Cash FX Showcase HTML
(docs/kyle_projectile_showcase.html).

Embeds all 139 staged RGBA sprites (4 states x 8 directions + $100 bills & spinning coins)
as compact WebP/PNG data URIs plus clean Kyle voice clips (ZERO 'clients' clips) and
scissor/cash SFX, with:
  1. Interactive 360-degree 8-dir Turntable & Frame-by-Frame Inspector for all 4 states
  2. Live 8-Direction Animated Grid (watch all 8 angles animate simultaneously)
  3. 4-Mode In-Game Behavior Simulator:
       - Paper-Plane Homing Flight (vs John Bird)
       - Ground Runner & Idle Wander
       - Victim Peripheral Vision Latch POV (Kyle frantically scissoring in your face!)
       - Business Register Raid (chopping a shop counter for cash showers)
  4. Animated Cash FX ($100 bills + spinning gold coins) burst tester
"""

import base64
import io
import json
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ARTIFACT_ROOT = r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
SPRITES_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_stage", "sprites")
SFX_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_stage", "sfx")
CLIPS_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_clips")
OUT_HTML = os.path.join(REPO, "docs", "kyle_projectile_showcase.html")


def img_to_webp_b64(path, quality=90):
    im = Image.open(path).convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def pack_state_atlas(manifest_state, base_dir, quality=90):
    """Pack all 8 directions x num_frames into one tidy horizontal-per-dir sprite sheet."""
    num_dirs = manifest_state["num_dirs"]
    num_frames = manifest_state["num_frames"]
    fw, fh = manifest_state["frame_size"]
    sheet = Image.new("RGBA", (num_frames * fw, num_dirs * fh), (0, 0, 0, 0))
    for d in range(num_dirs):
        files = manifest_state["directions"][str(d)]
        for f, rel in enumerate(files):
            im = Image.open(os.path.join(base_dir, rel)).convert("RGBA")
            if im.size != (fw, fh):
                im = im.resize((fw, fh), Image.LANCZOS)
            sheet.paste(im, (f * fw, d * fh))
    buf = io.BytesIO()
    sheet.save(buf, format="WEBP", quality=quality, method=4)
    return {
        "title": manifest_state["title"],
        "fps": manifest_state["fps"],
        "num_dirs": num_dirs,
        "num_frames": num_frames,
        "fw": fw,
        "fh": fh,
        "url": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
    }


def wav_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("ascii")


def main():
    with open(os.path.join(SPRITES_DIR, "manifest.json"), "r", encoding="utf-8") as fh:
        m = json.load(fh)

    states = {}
    for st_key in ("running_scissors", "overhead_scissors", "front_scissors", "no_scissors"):
        states[st_key] = pack_state_atlas(m["states"][st_key], SPRITES_DIR, quality=90)

    cash_fx = {
        "bills": [
            img_to_webp_b64(os.path.join(SPRITES_DIR, rel), quality=92)
            for rel in m["cash_fx"]["bills"]
        ],
        "quarters": [
            img_to_webp_b64(os.path.join(SPRITES_DIR, rel), quality=92)
            for rel in m["cash_fx"]["quarters"]
        ],
        "gold_dollars": [
            img_to_webp_b64(os.path.join(SPRITES_DIR, rel), quality=92)
            for rel in m["cash_fx"]["gold_dollars"]
        ],
    }

    audio = {
        "snip_fast": wav_b64(os.path.join(SFX_DIR, "snip_fast.wav")),
        "snip_heavy": wav_b64(os.path.join(SFX_DIR, "snip_heavy.wav")),
        "plane_whoosh": wav_b64(os.path.join(SFX_DIR, "plane_whoosh.wav")),
        "cash_register": wav_b64(os.path.join(SFX_DIR, "cash_register.wav")),
        "cash_flutter": wav_b64(os.path.join(SFX_DIR, "cash_flutter.wav")),
        "whoa_man": wav_b64(os.path.join(CLIPS_DIR, "cut_01_wheres_my_cut.wav")),
        "whoa_1": wav_b64(os.path.join(CLIPS_DIR, "whoa_01_short.wav")),
        "whoa_2": wav_b64(os.path.join(CLIPS_DIR, "whoa_02_wobble.wav")),
        "whoa_4": wav_b64(os.path.join(CLIPS_DIR, "whoa_04_punch.wav")),
        "kyle_hey": wav_b64(os.path.join(CLIPS_DIR, "kyle_02_hey_bright.wav")),
        "kyle_cut": wav_b64(os.path.join(CLIPS_DIR, "cut_02_give_me_a_cut.wav")),
        "kyle_hey_man": wav_b64(os.path.join(CLIPS_DIR, "edit_01_hey_man_tight.wav")),
    }

    payload = json.dumps({
        "directions": m["directions"],
        "states": states,
        "cash_fx": cash_fx,
        "audio": audio,
    })

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kyle Tillet — 4-State 8-Dir Projectile Sprites &amp; Cash FX Showcase</title>
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
    --red: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top, #1f1914 0%, var(--bg) 62%);
    color: var(--text); line-height: 1.44;
  }}
  header.top {{
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;
    padding: 13px 20px; background: #14110e; border-bottom: 1px solid var(--border);
  }}
  .brand h1 {{ margin: 0; font-size: 1.28rem; }}
  .brand small {{ color: var(--muted); font-size: 0.84rem; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 7px; align-items: center; }}
  .pill {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 999px;
    padding: 4px 11px; font-size: 0.77rem; color: var(--muted); font-weight: 700; text-decoration: none;
  }}
  .pill b {{ color: #fde68a; }}
  .pill.link {{ color: #fde68a; border-color: #6b4e22; }}
  .pill.link:hover {{ border-color: var(--accent); background: #2c2115; }}

  .wrap {{ max-width: 1400px; margin: 0 auto; padding: 16px 16px 48px; display: flex; flex-direction: column; gap: 18px; }}

  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
  }}
  .bar {{
    display: flex; flex-wrap: wrap; gap: 7px; align-items: center; justify-content: space-between;
    padding: 10px 14px; background: #16120e; border-bottom: 1px solid var(--border);
  }}
  .bar h2 {{ margin: 0; font-size: 1.04rem; color: #fde68a; }}
  .btn {{
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 7px; padding: 6px 11px; font-size: 0.81rem; font-weight: 700; cursor: pointer;
  }}
  .btn:hover {{ border-color: #846d55; }}
  .btn.active {{ background: #3f2b12; border-color: var(--accent); color: #fde68a; }}
  .btn.green {{ background: linear-gradient(180deg, #15803d, #166534); border-color: #22c55e; color: #fff; }}
  .btn.red {{ background: linear-gradient(180deg, #dc2626, #991b1b); border-color: #ef4444; color: #fff; }}

  .sim-grid {{
    display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 0;
  }}
  @media (max-width: 980px) {{ .sim-grid {{ grid-template-columns: 1fr; }} }}
  canvas#sim {{ display: block; width: 100%; aspect-ratio: 16 / 9; background: #080706; cursor: pointer; }}
  .sim-side {{
    padding: 14px; border-left: 1px solid var(--border); display: flex; flex-direction: column; gap: 11px;
    background: #14110e;
  }}
  @media (max-width: 980px) {{ .sim-side {{ border-left: 0; border-top: 1px solid var(--border); }} }}
  .sim-side h3 {{ margin: 0; font-size: 0.96rem; color: #fde68a; }}
  .sim-side p {{ margin: 0; font-size: 0.83rem; color: var(--muted); }}
  .stat-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }}
  .stat {{ background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 7px 9px; }}
  .stat small {{ display: block; font-size: 0.69rem; color: var(--muted); text-transform: uppercase; }}
  .stat b {{ font-size: 0.88rem; }}

  .turn-grid {{
    display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 0;
  }}
  @media (max-width: 960px) {{ .turn-grid {{ grid-template-columns: 1fr; }} }}
  .turn-left {{
    padding: 14px; border-right: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px;
    background: #13100d;
  }}
  @media (max-width: 960px) {{ .turn-left {{ border-right: 0; border-bottom: 1px solid var(--border); }} }}
  canvas#turntable {{
    width: 100%; aspect-ratio: 1 / 1; background: radial-gradient(circle, #2a241f 0%, #100d0b 75%);
    border: 1px solid var(--border); border-radius: 10px; cursor: ew-resize;
  }}
  .ctrl {{ display: flex; flex-direction: column; gap: 3px; font-size: 0.79rem; }}
  .ctrl-head {{ display: flex; justify-content: space-between; color: var(--muted); font-weight: 600; }}
  .ctrl-head b {{ color: #fde68a; font-family: ui-monospace, Consolas, monospace; }}
  .ctrl input[type=range] {{ width: 100%; accent-color: var(--accent); margin: 0; }}

  .turn-right {{ padding: 14px; display: flex; flex-direction: column; gap: 12px; }}
  .dir-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
  }}
  @media (max-width: 680px) {{ .dir-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  .dir-cell {{
    background: #120f0c; border: 1px solid var(--border); border-radius: 9px; padding: 8px;
    text-align: center; cursor: pointer; transition: border-color .12s;
  }}
  .dir-cell:hover {{ border-color: #7c654d; }}
  .dir-cell.selected {{ border-color: var(--accent); background: #211910; }}
  .dir-cell canvas {{ width: 100%; aspect-ratio: 1 / 1; display: block; }}
  .dir-cell span {{ display: block; margin-top: 4px; font-size: 0.75rem; color: var(--muted); font-weight: 700; }}
  .dir-cell.selected span {{ color: #fde68a; }}

  .cash-row {{
    display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 14px; padding: 14px; align-items: center;
  }}
  @media (max-width: 820px) {{ .cash-row {{ grid-template-columns: 1fr; }} }}
  canvas#cash {{
    width: 100%; height: 210px; background: radial-gradient(circle, #1f261c 0%, #0d100c 75%);
    border: 1px solid var(--border); border-radius: 10px; cursor: pointer; display: block;
  }}
</style>
</head>
<body>
<header class="top">
  <div class="brand">
    <h1>Kyle Tillet &mdash; Custom 24-FPS Photorealistic Projectile Animations &amp; Real US Currency FX</h1>
    <small>440 HD RGBA Sprites (300px Tall) &middot; Articulated 2-Leg Running + Chopping &middot; Overhead &amp; Front Lunge-Chops &middot; Real US $100 Bills, Silver Quarters &amp; Gold Dollars</small>
  </div>
  <div class="pills">
    <a class="pill link" href="kyle_weapon_showcase.html">&#8592; Viewmodel &amp; POV Tuner</a>
    <a class="pill link" href="kyle_scissors_sound_preview.html">&#128266; Voice Clips</a>
    <span class="pill">Sprites: <b>440 HD RGBA</b></span>
    <span class="pill">Rate: <b>24 FPS &times; 8 Dirs</b></span>
  </div>
</header>

<div class="wrap">
  <!-- 1. LIVE IN-GAME BEHAVIOR SIMULATOR -->
  <section class="card">
    <div class="bar">
      <h2>&#127918; Live In-Game Projectile Behavior Simulator</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
        <button class="btn active" id="sim-plane" onclick="setSim('plane')">&#9992; Homing vs John Bird</button>
        <button class="btn" id="sim-runner" onclick="setSim('runner')">&#127939; Ground Runner &amp; Wander</button>
        <button class="btn red" id="sim-latch" onclick="setSim('latch')">&#128561; Victim Peripheral Latch POV</button>
        <button class="btn green" id="sim-register" onclick="setSim('register')">&#128176; Business Register Raid</button>
        <label style="font-size:0.8rem;color:var(--muted);display:flex;align-items:center;gap:4px;margin-left:6px;cursor:pointer;">
          <input type="checkbox" id="chk-sfx" checked> SFX &amp; Voice
        </label>
      </div>
    </div>
    <div class="sim-grid">
      <canvas id="sim" width="1280" height="720"></canvas>
      <div class="sim-side">
        <h3 id="sim-title">Homing Paper-Plane Kyle vs John Bird</h3>
        <p id="sim-desc">When locked on (hold fire ~0.6s), Kyle launches into the sky spinning/gliding with overhead scissors open, trailing $100 bills &amp; coins, then latches right onto John Bird for 2&times; snip damage &amp; wing slow!</p>
        <div class="stat-row">
          <div class="stat"><small>Active Sprite</small><b id="sim-sprite">overhead_scissors</b></div>
          <div class="stat"><small>Projectile HP</small><b>35 HP (shootable)</b></div>
          <div class="stat"><small>Latch Damage</small><b>12 dmg / 0.45s</b></div>
          <div class="stat"><small>John Bird Bonus</small><b>2&times; dmg + slow</b></div>
        </div>
        <button class="btn green" onclick="burstSimCash()">&#128181; Trigger Snip + Cash Burst</button>
        <button class="btn" onclick="sayKyleLine()">&#128483; Play Random Kyle Line</button>
        <p style="font-size:0.75rem;">Click anywhere on the arena canvas to trigger a cash burst + snip right at that spot.</p>
      </div>
    </div>
  </section>

  <!-- 2. 360-DEGREE 8-DIRECTION SPRITE INSPECTOR -->
  <section class="card">
    <div class="bar">
      <h2>&#128260; 4-State &times; 8-Direction Audited Studio Photography Sprite Inspector</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="btn active" id="st-running_scissors" onclick="setState('running_scissors')">1. Running + Chopping (64f)</button>
        <button class="btn" id="st-overhead_scissors" onclick="setState('overhead_scissors')">2. Overhead Jump-Chop (64f)</button>
        <button class="btn" id="st-front_scissors" onclick="setState('front_scissors')">3. Front &amp; Side Lunge-Chop (64f)</button>
        <button class="btn" id="st-no_scissors" onclick="setState('no_scissors')">4. Funny Idle (No Scissors, 64f)</button>
      </div>
    </div>
    <div class="turn-grid">
      <div class="turn-left">
        <canvas id="turntable" width="420" height="420"></canvas>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn active" id="btn-spin" onclick="toggleSpin()">Auto-Spin 360&deg;: ON</button>
          <button class="btn" id="btn-tpause" onclick="toggleTurnPause()">&#9208; Pause Anim</button>
          <button class="btn" onclick="stepTurnFrame()">Step Frame +1</button>
        </div>
        <div class="ctrl">
          <div class="ctrl-head"><span>Direction Angle (drag canvas too)</span><b id="lbl-dir">0&deg; Front</b></div>
          <input type="range" id="rng-dir" min="0" max="7" step="1" value="0" oninput="onDirSlider(this.value)">
        </div>
        <div class="ctrl">
          <div class="ctrl-head"><span>Animation Speed</span><b id="lbl-spd">1.0&times;</b></div>
          <input type="range" id="rng-spd" min="0.25" max="2.5" step="0.25" value="1.0" oninput="onSpdSlider(this.value)">
        </div>
        <div class="ctrl">
          <div class="ctrl-head"><span>Preview Zoom</span><b id="lbl-zoom">1.15&times;</b></div>
          <input type="range" id="rng-zoom" min="0.6" max="1.8" step="0.05" value="1.15" oninput="onZoomSlider(this.value)">
        </div>
      </div>

      <div class="turn-right">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
          <strong style="color:#fde68a;font-size:0.93rem;" id="grid-title">All 8 Directions — Running w/ Chopping Scissors (16 frames/dir @ 24 FPS)</strong>
          <span style="font-size:0.78rem;color:var(--muted);">Click any angle card to lock the turntable onto it</span>
        </div>
        <div class="dir-grid" id="dir-grid"></div>
      </div>
    </div>
  </section>

  <!-- 3. CASH FX (REALISTIC US $100 BILLS, SILVER QUARTERS & SACAGAWEA GOLD DOLLARS) -->
  <section class="card">
    <div class="bar">
      <h2>&#128181; Realistic US Currency Particles &mdash; $100 Bills, 2024 Silver Quarters &amp; Sacagawea Gold Dollars</h2>
      <button class="btn green" onclick="spawnCashFountain(32)">&#128176; Make It Rain!</button>
    </div>
    <div class="cash-row">
      <canvas id="cash" width="900" height="210"></canvas>
      <div style="display:flex;flex-direction:column;gap:8px;font-size:0.83rem;color:var(--muted);">
        <strong style="color:#fde68a;">Authentic US Currency Spectacle</strong>
        <p style="margin:0;">Every scissor chop erupts fluttering sage-green engraved <b>$100 bills</b> (8 front/back/S-wave/folded frames), 3D spinning reeded <b>2024 Washington Silver Quarters</b> (8 frames), and gleaming <b>Sacagawea Gold Dollars</b> (8 frames) visible to everyone in third-person.</p>
        <p style="margin:0;">Click anywhere on the green cash tray or hit <b>Make It Rain!</b> to test the physics + register &amp; flutter SFX.</p>
      </div>
    </div>
  </section>
</div>

<script>
const DATA = {payload};
const AUDIO = DATA.audio;

// Load state sprite sheets
const stateImgs = {{}};
Object.keys(DATA.states).forEach(k => {{
  const im = new Image();
  im.src = DATA.states[k].url;
  stateImgs[k] = im;
}});
const billImgs = DATA.cash_fx.bills.map(u => {{ const im = new Image(); im.src = u; return im; }});
const quarterImgs = DATA.cash_fx.quarters.map(u => {{ const im = new Image(); im.src = u; return im; }});
const goldImgs = DATA.cash_fx.gold_dollars.map(u => {{ const im = new Image(); im.src = u; return im; }});

function playSound(key, vol = 0.75) {{
  if (!document.getElementById("chk-sfx").checked) return;
  const src = AUDIO[key];
  if (!src) return;
  const a = new Audio(src);
  a.volume = vol;
  a.play().catch(() => {{}});
}}

function sayKyleLine() {{
  const pool = ["kyle_cut", "whoa_man", "kyle_hey", "kyle_hey_man", "whoa_2", "whoa_4"];
  playSound(pool[Math.floor(Math.random() * pool.length)], 0.85);
}}

function drawStateSprite(ctx, stKey, dirIdx, frameIdx, cx, bottomY, scale, rotRad = 0) {{
  const st = DATA.states[stKey];
  const im = stateImgs[stKey];
  if (!im || !im.complete || im.naturalWidth === 0) return;
  const d = ((dirIdx % st.num_dirs) + st.num_dirs) % st.num_dirs;
  const f = ((frameIdx % st.num_frames) + st.num_frames) % st.num_frames;
  const sx = f * st.fw, sy = d * st.fh;
  const dw = st.fw * scale, dh = st.fh * scale;
  ctx.save();
  ctx.translate(cx, bottomY - dh * 0.5);
  if (rotRad !== 0) ctx.rotate(rotRad);
  ctx.drawImage(im, sx, sy, st.fw, st.fh, -dw * 0.5, -dh * 0.5, dw, dh);
  ctx.restore();
}}

// ---------- 1. TURNTABLE & 8-DIR GRID ----------
let activeState = "running_scissors";
let turnDir = 0;
let autoSpin = true;
let turnPaused = false;
let turnSpeed = 1.0;
let turnZoom = 1.15;
let manualTurnFrame = 0;
let lastSpinMs = performance.now();

const dirGridEl = document.getElementById("dir-grid");
const dirCanvases = [];
for (let d = 0; d < 8; d++) {{
  const cell = document.createElement("div");
  cell.className = "dir-cell" + (d === 0 ? " selected" : "");
  const c = document.createElement("canvas");
  c.width = 200; c.height = 200;
  const sp = document.createElement("span");
  sp.textContent = DATA.directions[d].label;
  cell.appendChild(c); cell.appendChild(sp);
  cell.onclick = () => {{
    autoSpin = false;
    updateSpinBtn();
    turnDir = d;
    document.getElementById("rng-dir").value = d;
    updateDirSelection();
  }};
  dirGridEl.appendChild(cell);
  dirCanvases.push({{ cell, ctx: c.getContext("2d") }});
}}

function updateDirSelection() {{
  document.getElementById("lbl-dir").textContent = DATA.directions[turnDir].label;
  dirCanvases.forEach((o, i) => o.cell.classList.toggle("selected", i === turnDir));
}}

function updateSpinBtn() {{
  const b = document.getElementById("btn-spin");
  b.classList.toggle("active", autoSpin);
  b.textContent = autoSpin ? "Auto-Spin 360°: ON" : "Auto-Spin 360°: OFF";
}}

function toggleSpin() {{ autoSpin = !autoSpin; updateSpinBtn(); }}
function toggleTurnPause() {{
  turnPaused = !turnPaused;
  document.getElementById("btn-tpause").innerHTML = turnPaused ? "&#9654; Resume Anim" : "&#9208; Pause Anim";
}}
function stepTurnFrame() {{
  turnPaused = true;
  document.getElementById("btn-tpause").innerHTML = "&#9654; Resume Anim";
  manualTurnFrame = (manualTurnFrame + 1) % DATA.states[activeState].num_frames;
}}
function onDirSlider(v) {{
  autoSpin = false; updateSpinBtn();
  turnDir = parseInt(v, 10) || 0;
  updateDirSelection();
}}
function onSpdSlider(v) {{
  turnSpeed = parseFloat(v) || 1.0;
  document.getElementById("lbl-spd").textContent = turnSpeed.toFixed(2).replace(/\\.00$/, ".0") + "×";
}}
function onZoomSlider(v) {{
  turnZoom = parseFloat(v) || 1.15;
  document.getElementById("lbl-zoom").textContent = turnZoom.toFixed(2).replace(/0$/, "") + "×";
}}

function setState(k) {{
  activeState = k;
  manualTurnFrame = 0;
  Object.keys(DATA.states).forEach(sk => {{
    document.getElementById("st-" + sk).classList.toggle("active", sk === k);
  }});
  const st = DATA.states[k];
  document.getElementById("grid-title").textContent =
    `All 8 Directions — ${{st.title}} (${{st.num_frames}} frames/dir @ ${{st.fps}} FPS)`;
}}

const turnCanvas = document.getElementById("turntable");
const turnCtx = turnCanvas.getContext("2d");
let draggingTurn = false, dragTurnX = 0, dragTurnDir0 = 0;
turnCanvas.addEventListener("mousedown", e => {{
  draggingTurn = true; autoSpin = false; updateSpinBtn();
  dragTurnX = e.clientX; dragTurnDir0 = turnDir;
}});
window.addEventListener("mousemove", e => {{
  if (!draggingTurn) return;
  const step = Math.round((e.clientX - dragTurnX) / 28);
  turnDir = ((dragTurnDir0 + step) % 8 + 8) % 8;
  document.getElementById("rng-dir").value = turnDir;
  updateDirSelection();
}});
window.addEventListener("mouseup", () => {{ draggingTurn = false; }});

// ---------- 2. LIVE SIMULATOR ----------
const simCanvas = document.getElementById("sim");
const simCtx = simCanvas.getContext("2d");
let simMode = "plane";
let simStartMs = performance.now();
let lastSimSnipMs = 0;
const simParticles = [];

const SIM_META = {{
  plane: {{
    title: "Homing Paper-Plane Kyle vs John Bird",
    desc: "When locked on (~0.6s hold), Kyle glides through the sky with overhead scissors snapping, trailing $100 bills & coins, hunting down John Bird for 2× snip damage + wing slow!",
    sprite: "overhead_scissors (gliding)"
  }},
  runner: {{
    title: "Ground Runner & Crowd Wander (No Lock)",
    desc: "Quick-firing without a lock sends Kyle sprinting along the ground with dual scissors. When no enemies are nearby, he slows down, waves his scissors, and yells his signature lines!",
    sprite: "running_scissors -> no_scissors"
  }},
  latch: {{
    title: "Victim First-Person Peripheral Latch POV",
    desc: "When Kyle catches you, he latches right in your forward-side peripheral (~30u ahead) for up to 5s, frantically scissoring in your face while cash erupts out of your pockets!",
    sprite: "front_scissors + overhead_scissors"
  }},
  register: {{
    title: "Business Cash Register Raid",
    desc: "Fired near a Bakersfield storefront with no enemies around, Kyle rushes straight for the front counter & cash register, chopping it open into a fountain of $100 bills & gold coins!",
    sprite: "running_scissors -> front_scissors"
  }}
}};

function setSim(m) {{
  simMode = m;
  simStartMs = performance.now();
  simParticles.length = 0;
  ["plane", "runner", "latch", "register"].forEach(k => {{
    document.getElementById("sim-" + k).classList.toggle("active", k === m);
  }});
  document.getElementById("sim-title").textContent = SIM_META[m].title;
  document.getElementById("sim-desc").textContent = SIM_META[m].desc;
  document.getElementById("sim-sprite").textContent = SIM_META[m].sprite;
  if (m === "plane") playSound("plane_whoosh", 0.55);
  else if (m === "register") playSound("cash_register", 0.65);
  else sayKyleLine();
}}

function spawnSimCash(x, y, count = 14) {{
  for (let i = 0; i < count; i++) {{
    const r = Math.random();
    const kind = r < 0.52 ? "bill" : (r < 0.78 ? "quarter" : "gold");
    const ang = -Math.PI * 0.5 + (Math.random() - 0.5) * 2.4;
    const spd = 160 + Math.random() * 340;
    simParticles.push({{
      kind,
      x, y,
      vx: Math.cos(ang) * spd,
      vy: Math.sin(ang) * spd - 60,
      rot: Math.random() * Math.PI * 2,
      vrot: (Math.random() - 0.5) * 8,
      phase: Math.random() * 10,
      life: 1.4 + Math.random() * 1.1,
      maxLife: 2.5,
      scale: kind === "bill" ? (0.42 + Math.random() * 0.22) : (0.34 + Math.random() * 0.16),
    }});
  }}
}}

function burstSimCash() {{
  spawnSimCash(640, 340, 24);
  playSound("snip_heavy", 0.6);
  playSound("cash_flutter", 0.55);
}}

simCanvas.addEventListener("mousedown", e => {{
  const r = simCanvas.getBoundingClientRect();
  const x = ((e.clientX - r.left) / r.width) * 1280;
  const y = ((e.clientY - r.top) / r.height) * 720;
  spawnSimCash(x, y, 18);
  playSound("snip_fast", 0.55);
  if (Math.random() < 0.45) playSound("cash_flutter", 0.5);
}});

function drawParticles(ctx, list, dt) {{
  for (let i = list.length - 1; i >= 0; i--) {{
    const p = list[i];
    p.life -= dt;
    if (p.life <= 0) {{ list.splice(i, 1); continue; }}
    const isCoin = p.kind !== "bill";
    p.vy += (isCoin ? 560 : 185) * dt;
    if (!isCoin) p.vx += Math.sin(p.phase + p.life * 8) * 125 * dt;
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.rot += p.vrot * dt;
    const alpha = Math.min(1, p.life * 1.4);
    const arr = p.kind === "bill" ? billImgs : (p.kind === "quarter" ? quarterImgs : goldImgs);
    const idx = Math.floor((p.phase + p.life * (isCoin ? 15 : 10)) % arr.length);
    const im = arr[(idx + arr.length) % arr.length];
    if (im && im.complete && im.naturalWidth > 0) {{
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      const w = im.naturalWidth * p.scale, h = im.naturalHeight * p.scale;
      ctx.drawImage(im, -w * 0.5, -h * 0.5, w, h);
      ctx.restore();
    }}
  }}
}}

function drawSim(now, dt) {{
  const t = (now - simStartMs) * 0.001;
  const W = 1280, H = 720;
  const ctx = simCtx;

  // Bakersfield daylight arena backdrop
  const sky = ctx.createLinearGradient(0, 0, 0, 410);
  sky.addColorStop(0, simMode === "latch" ? "#263c5e" : "#3a70a8");
  sky.addColorStop(1, simMode === "latch" ? "#7a5b48" : "#d9b98c");
  ctx.fillStyle = sky; ctx.fillRect(0, 0, W, 410);
  const gnd = ctx.createLinearGradient(0, 410, 0, H);
  gnd.addColorStop(0, "#4e463e"); gnd.addColorStop(1, "#221e1a");
  ctx.fillStyle = gnd; ctx.fillRect(0, 410, W, H - 410);

  // Subtle street horizon buildings
  ctx.fillStyle = "#3a3028";
  ctx.fillRect(30, 230, 220, 180);
  ctx.fillRect(1010, 195, 240, 215);
  ctx.fillStyle = "#544336";
  ctx.fillRect(280, 290, 190, 120);

  if (simMode === "plane") {{
    // John Bird flying figure-8
    const bx = 660 + Math.sin(t * 1.1) * 340;
    const by = 220 + Math.sin(t * 2.2) * 75;
    const bvx = Math.cos(t * 1.1) * 340;
    ctx.save();
    ctx.translate(bx, by);
    if (bvx < 0) ctx.scale(-1, 1);
    ctx.fillStyle = "rgba(15, 23, 42, 0.86)";
    ctx.beginPath(); ctx.ellipse(0, 0, 52, 24, 0, 0, Math.PI * 2); ctx.fill();
    const flap = Math.sin(t * 13) * 30;
    ctx.strokeStyle = "#cbd5e1"; ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(-14, -4); ctx.quadraticCurveTo(-65, -45 + flap, -110, -10 + flap);
    ctx.moveTo(14, -4); ctx.quadraticCurveTo(65, -45 + flap, 110, -10 + flap);
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = "#fde047"; ctx.font = "bold 13px system-ui"; ctx.textAlign = "center";
    ctx.fillText("JOHN BIRD (LOCKED — 2× SNIP DMG!)", bx, by - 42);

    // Homing Kyle gliding/banking right behind & onto John Bird
    const kx = 660 + Math.sin(t * 1.1 - 0.35) * 340;
    const ky = 220 + Math.sin((t - 0.32) * 2.2) * 75 + 24;
    const kvx = Math.cos(t * 1.1 - 0.35);
    const dir = kvx >= 0 ? 6 : 2;
    const f = Math.floor(t * 24) % DATA.states.overhead_scissors.num_frames;
    const bank = kvx >= 0 ? 0.95 : -0.95; // paper-plane horizontal dive angle!

    // Speed trail
    ctx.strokeStyle = "rgba(253, 224, 71, 0.35)"; ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(kx - kvx * 160, ky + 16); ctx.lineTo(kx, ky);
    ctx.stroke();

    drawStateSprite(ctx, "overhead_scissors", dir, f, kx, ky + 70, 0.62, bank);
    if (now - lastSimSnipMs > 420) {{
      lastSimSnipMs = now;
      spawnSimCash(bx, by, 5);
    }}
  }} else if (simMode === "runner") {{
    // Ground Runner cycle: 4s running across -> 2.5s wandering/taunting with no_scissors & front_scissors
    const cyc = t % 6.5;
    const isRunning = cyc < 4.0;
    const phase = isRunning ? (cyc / 4.0) : 1.0;
    const dirSign = Math.floor(t / 6.5) % 2 === 0 ? 1 : -1;
    const kx = isRunning
      ? (dirSign > 0 ? 180 + phase * 920 : 1100 - phase * 920)
      : (dirSign > 0 ? 1100 : 180);
    const ky = 595;

    // Ground shadow
    ctx.fillStyle = "rgba(0,0,0,0.42)";
    ctx.beginPath(); ctx.ellipse(kx, 594, 62, 16, 0, 0, Math.PI * 2); ctx.fill();

    if (isRunning) {{
      const d = dirSign > 0 ? 6 : 2;
      const f = Math.floor(t * 24) % DATA.states.running_scissors.num_frames;
      drawStateSprite(ctx, "running_scissors", d, f, kx, ky, 0.92);
      if (now - lastSimSnipMs > 360) {{
        lastSimSnipMs = now;
        spawnSimCash(kx - dirSign * 30, ky - 140, 2);
      }}
    }} else {{
      // No enemies nearby -> turns toward camera, swaps between front_scissors & no_scissors taunting!
      const showChop = (cyc - 4.0) > 1.1;
      const st = showChop ? "front_scissors" : "no_scissors";
      const f = Math.floor(t * DATA.states[st].fps) % DATA.states[st].num_frames;
      drawStateSprite(ctx, st, 0, f, kx, 595, 0.94);
      // Speech bubble
      ctx.save();
      ctx.fillStyle = "rgba(18,14,11,0.9)"; ctx.strokeStyle = "#f59e0b"; ctx.lineWidth = 2;
      const bx = Math.max(150, Math.min(1130, kx));
      ctx.beginPath(); ctx.roundRect(bx - 125, 250, 250, 44, 12); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fde68a"; ctx.font = "bold 16px system-ui"; ctx.textAlign = "center";
      ctx.fillText(showChop ? '"GIVE ME A CUT, MAN!"' : '"Hey, it\\\'s Kyle... nobody here?"', bx, 278);
      ctx.restore();
    }}
  }} else if (simMode === "latch") {{
    // VICTIM PERIPHERAL LATCH POV! Screen shake + red cash-cut vignette + huge Kyle scissoring in peripheral!
    const chopCycle = (t * 2.22) % 1.0; // every 0.45s!
    const hitPulse = Math.max(0, 1 - chopCycle * 4.0);
    const sx = (Math.random() - 0.5) * 14 * hitPulse;
    const sy = (Math.random() - 0.5) * 10 * hitPulse;

    ctx.save();
    ctx.translate(sx, sy);

    // Subtle enemy weapon silhouette at bottom-right to sell Victim POV
    ctx.fillStyle = "rgba(12,12,14,0.65)";
    ctx.fillRect(880, 560, 180, 190);
    ctx.fillStyle = "#94a3b8"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center";
    ctx.fillText("(YOUR VIEW — VICTIM POV)", 640, 46);

    // Kyle latched right in the left-forward peripheral vision (~30u ahead, bobbing & frantically scissoring!)
    const side = Math.floor(t / 4.5) % 2 === 0 ? -1 : 1;
    const kx = 640 + side * 355 + Math.sin(t * 9) * 28;
    const ky = 685 + Math.cos(t * 11) * 20;
    const dir = side < 0 ? 7 : 1; // angled right into victim's face!
    const st = Math.floor(t / 1.5) % 2 === 0 ? "front_scissors" : "overhead_scissors";
    const f = Math.floor(t * 28) % DATA.states[st].num_frames;
    drawStateSprite(ctx, st, dir, f, kx, ky, 1.65, side * -0.07 * Math.sin(t * 14));

    // Snip hit flash + cash bursting from victim
    if (now - lastSimSnipMs > 450) {{
      lastSimSnipMs = now;
      spawnSimCash(kx - side * 70, 390, 9);
      playSound("snip_fast", 0.35);
    }}

    // Warning banner
    ctx.fillStyle = `rgba(220, 38, 38, ${{0.14 + hitPulse * 0.22}})`;
    ctx.fillRect(0, 0, W, 16); ctx.fillRect(0, H - 16, W, 16);
    ctx.fillRect(0, 0, 16, H); ctx.fillRect(W - 16, 0, 16, H);

    ctx.fillStyle = "rgba(18,14,11,0.85)";
    ctx.beginPath(); ctx.roundRect(410, 62, 460, 42, 10); ctx.fill();
    ctx.fillStyle = "#fca5a5"; ctx.font = "bold 17px system-ui"; ctx.textAlign = "center";
    ctx.fillText('KYLE LATCHED! -12 HP  "WHOA MAN, GIVE ME A CUT!"', 640, 89);

    // Crosshair
    ctx.strokeStyle = "rgba(255,255,255,0.85)"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(628, 360); ctx.lineTo(636, 360); ctx.moveTo(644, 360); ctx.lineTo(652, 360);
    ctx.moveTo(640, 348); ctx.lineTo(640, 356); ctx.moveTo(640, 364); ctx.lineTo(640, 372);
    ctx.stroke();
    ctx.restore();
  }} else if (simMode === "register") {{
    // Shop counter & Bakersfield cash register on right side
    ctx.fillStyle = "#5c3d28"; ctx.fillRect(760, 415, 360, 185);
    ctx.strokeStyle = "#8c6142"; ctx.lineWidth = 4; ctx.strokeRect(760, 415, 360, 185);
    ctx.fillStyle = "#2b303a"; ctx.fillRect(865, 330, 130, 85);
    ctx.fillStyle = "#16a34a"; ctx.fillRect(885, 345, 90, 26);
    ctx.fillStyle = "#bbf7d0"; ctx.font = "bold 16px ui-monospace, monospace"; ctx.textAlign = "center";
    ctx.fillText("$999.50", 930, 364);
    ctx.fillStyle = "#fde68a"; ctx.font = "bold 14px system-ui";
    ctx.fillText("BAKERSFIELD SHOP REGISTER", 940, 315);

    const cyc = t % 5.5;
    if (cyc < 1.6) {{
      // Sprinting up to counter
      const u = cyc / 1.6;
      const kx = 180 + u * 540;
      const f = Math.floor(t * 24) % DATA.states.running_scissors.num_frames;
      drawStateSprite(ctx, "running_scissors", 6, f, kx, 598, 0.94);
    }} else {{
      // Frantically chopping the register!
      const f = Math.floor(t * 26) % DATA.states.front_scissors.num_frames;
      drawStateSprite(ctx, "front_scissors", 6, f, 735, 598, 0.96);
      if (now - lastSimSnipMs > 340) {{
        lastSimSnipMs = now;
        spawnSimCash(920, 355, 8);
        playSound("snip_fast", 0.34);
      }}
    }}
  }}

  drawParticles(ctx, simParticles, dt);
}}

// ---------- 3. CASH TRAY ----------
const cashCanvas = document.getElementById("cash");
const cashCtx = cashCanvas.getContext("2d");
const trayParticles = [];

function spawnCashFountain(n = 24, x = null, y = null) {{
  const sx = x !== null ? x : 160 + Math.random() * 580;
  const sy = y !== null ? y : 155;
  for (let i = 0; i < n; i++) {{
    const r = Math.random();
    const kind = r < 0.50 ? "bill" : (r < 0.75 ? "quarter" : "gold");
    const ang = -Math.PI * 0.5 + (Math.random() - 0.5) * 1.9;
    const spd = 110 + Math.random() * 240;
    trayParticles.push({{
      kind, x: sx, y: sy,
      vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd - 40,
      rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 7,
      phase: Math.random() * 10, life: 1.8 + Math.random() * 1.2, maxLife: 3.0,
      scale: kind === "bill" ? 0.46 : 0.38,
    }});
  }}
  playSound("cash_register", 0.55);
  playSound("cash_flutter", 0.5);
}}

cashCanvas.addEventListener("mousedown", e => {{
  const r = cashCanvas.getBoundingClientRect();
  spawnCashFountain(24, ((e.clientX - r.left) / r.width) * 900, ((e.clientY - r.top) / r.height) * 210);
}});

// ---------- MAIN ANIMATION LOOP ----------
let prevMs = performance.now();
function loop(now) {{
  const dt = Math.min(0.05, (now - prevMs) * 0.001);
  prevMs = now;

  // Auto-spin turntable every 550ms
  if (autoSpin && now - lastSpinMs > 550) {{
    lastSpinMs = now;
    turnDir = (turnDir + 1) % 8;
    document.getElementById("rng-dir").value = turnDir;
    updateDirSelection();
  }}

  const st = DATA.states[activeState];
  const fi = turnPaused ? manualTurnFrame : Math.floor((now * 0.001) * st.fps * turnSpeed) % st.num_frames;
  manualTurnFrame = fi;

  // Draw big turntable
  turnCtx.clearRect(0, 0, 420, 420);
  // Turntable floor ring
  turnCtx.fillStyle = "rgba(0,0,0,0.4)";
  turnCtx.beginPath(); turnCtx.ellipse(210, 368, 105, 22, 0, 0, Math.PI * 2); turnCtx.fill();
  turnCtx.strokeStyle = "rgba(245,158,11,0.35)"; turnCtx.lineWidth = 2;
  turnCtx.beginPath(); turnCtx.ellipse(210, 368, 125, 28, 0, 0, Math.PI * 2); turnCtx.stroke();
  drawStateSprite(turnCtx, activeState, turnDir, fi, 210, 372, turnZoom);

  turnCtx.fillStyle = "rgba(245,241,235,0.75)";
  turnCtx.font = "bold 13px ui-monospace, Consolas, monospace";
  turnCtx.fillText(`${{DATA.directions[turnDir].label}} · frame ${{fi + 1}}/${{st.num_frames}}`, 14, 24);

  // Draw 8-dir mini grid
  for (let d = 0; d < 8; d++) {{
    const gctx = dirCanvases[d].ctx;
    gctx.clearRect(0, 0, 200, 200);
    gctx.fillStyle = "rgba(0,0,0,0.32)";
    gctx.beginPath(); gctx.ellipse(100, 182, 46, 10, 0, 0, Math.PI * 2); gctx.fill();
    drawStateSprite(gctx, activeState, d, fi, 100, 184, 0.58);
  }}

  // Draw simulator
  drawSim(now, dt);

  // Draw cash tray: 4 fluttering $100 US bills + 2 spinning Silver Quarters + 2 spinning Sacagawea Gold Dollars
  cashCtx.clearRect(0, 0, 900, 210);
  const bf = Math.floor(now * 0.008) % billImgs.length;
  const cf = Math.floor(now * 0.011) % quarterImgs.length;
  for (let i = 0; i < 4; i++) {{
    const bi = billImgs[(bf + i * 2) % billImgs.length];
    if (bi && bi.complete) {{
      const x = 90 + i * 116, y = 105 + Math.sin(now * 0.004 + i) * 14;
      cashCtx.save(); cashCtx.translate(x, y); cashCtx.rotate(Math.sin(now * 0.003 + i) * 0.22);
      cashCtx.drawImage(bi, -54, -30, 108, 60); cashCtx.restore();
    }}
  }}
  for (let i = 0; i < 2; i++) {{
    const qi = quarterImgs[(cf + i * 2) % quarterImgs.length];
    if (qi && qi.complete) {{
      const x = 565 + i * 82, y = 105 + Math.cos(now * 0.005 + i) * 11;
      cashCtx.drawImage(qi, x - 34, y - 34, 68, 68);
    }}
    const gi = goldImgs[(cf + i * 2 + 1) % goldImgs.length];
    if (gi && gi.complete) {{
      const x = 735 + i * 82, y = 105 + Math.cos(now * 0.005 + i + 2) * 11;
      cashCtx.drawImage(gi, x - 34, y - 34, 68, 68);
    }}
  }}
  drawParticles(cashCtx, trayParticles, dt);

  requestAnimationFrame(loop);
}}

updateDirSelection();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print(f"Wrote Kyle Projectile Showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
