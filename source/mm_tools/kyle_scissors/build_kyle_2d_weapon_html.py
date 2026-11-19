"""Build self-contained 2D FPS Weapon Viewmodel Prototype Showcase HTML for Kyle Tillet's
3 high-detail finalists (#1 Pocket Kyle, #3 Scissor-Slingshot Ballista, #4 Redesigned
Forward-Aiming Executive Audit Briefcase), modeled on v_milky / v_pickle / v_dookie.

Packs all 3 multi-keyframe optical-flow animated 2D weapon sprite sheets (WebP atlases) +
Kyle voice clips & scissor/cash SFX into docs/kyle_weapon_showcase.html.
"""

import base64
import io
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ARTIFACT_ROOT = r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
WEAPONS_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_2d_weapons_v2")
CLIPS_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_clips")
SFX_DIR = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_stage", "sfx")
OUT_HTML = os.path.join(REPO, "docs", "kyle_weapon_showcase.html")

SPECS = [
    {
        "id": "v1_pocket_kyle",
        "num": 1,
        "title": "The Pocket Kyle (Upgraded)",
        "style": "Milky / Pickle Photorealistic Style · 78 Frames",
        "tagline": "Funnier bobblehead-proportioned Kyle ('KYLE - 50%' nametag + $100 bills bursting from both pockets). His ENTIRE ARMS & giant barber scissors swing open & slam shut overhead while his eyes dart around and loafers kick — then releases to a true empty open palm!",
        "anchor": "right",
        "scale": 0.96,
        "offset_x": 18,
        "offset_y": 8,
        "fps_idle": 20,
        "fps_lock": 26,
        "fps_fire": 24,
    },
    {
        "id": "v3_scissor_ballista",
        "num": 3,
        "title": "The Scissor-Slingshot Ballista (Upgraded)",
        "style": "Dead-Center Forward Comic-Quake · 84 Frames",
        "tagline": "Way more animation: 4 camera-locked keyframes with Kyle kicking his legs, glancing maniacally back at you, pumping & slamming his scissors shut, brass winch crank turning, giant chrome scissor limbs flexing under draw tension, and an explosive empty-rail red-bungee whip launch!",
        "anchor": "center",
        "scale": 1.05,
        "offset_x": 0,
        "offset_y": 14,
        "fps_idle": 20,
        "fps_lock": 26,
        "fps_fire": 24,
    },
    {
        "id": "v4_audit_briefcase",
        "num": 4,
        "title": "The Executive Audit Briefcase (Redesigned Forward Aim)",
        "style": "Forward-Aiming Suited Quake Launcher · 76 Frames",
        "tagline": "Completely redesigned in true forward-aiming FPS perspective pointing straight into the crosshair! Rear brass combination lock, fiery 'MY CUT' pressure gauge, crackling green scissor-jaw lightning on Lock-On, crazed Kyle peeking out, and smoke + $100-bill empty bay blast on Fire!",
        "anchor": "center-right",
        "scale": 1.04,
        "offset_x": 60,
        "offset_y": 14,
        "fps_idle": 20,
        "fps_lock": 26,
        "fps_fire": 24,
    },
]


def pack_webp_strip(paths, quality=90):
    ims = [Image.open(p).convert("RGBA") for p in paths]
    fw, fh = ims[0].size
    max_cols = max(1, min(len(ims), 3800 // fw))
    cols = max_cols
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sheet.paste(im, (c * fw, r * fh))
    buf = io.BytesIO()
    sheet.save(buf, format="WEBP", quality=quality, method=4)
    return {
        "fw": fw,
        "fh": fh,
        "cols": cols,
        "rows": rows,
        "count": len(ims),
        "url": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
    }


def wav_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("ascii")


def main():
    with open(os.path.join(WEAPONS_DIR, "manifest.json"), "r", encoding="utf-8") as fh:
        raw_manifest = json.load(fh)
    by_id = {w["id"]: w for w in raw_manifest["weapons"]}

    weapons_data = []
    for sp in SPECS:
        wid = sp["id"]
        wmeta = by_id[wid]
        wdir = os.path.join(WEAPONS_DIR, wid)
        idle_strip = pack_webp_strip([os.path.join(wdir, f) for f in wmeta["idle"]], quality=88)
        lock_strip = pack_webp_strip([os.path.join(wdir, f) for f in wmeta["lock"]], quality=88)
        fire_strip = pack_webp_strip([os.path.join(wdir, f) for f in wmeta["fire"]], quality=88)
        with open(os.path.join(wdir, wmeta["idle"][0]), "rb") as tf:
            thumb_b64 = "data:image/png;base64," + base64.b64encode(tf.read()).decode("ascii")
        weapons_data.append({
            **sp,
            "thumb": thumb_b64,
            "idle": idle_strip,
            "lock": lock_strip,
            "fire": fire_strip,
        })

    audio_map = {
        "snip_fast": wav_b64(os.path.join(SFX_DIR, "snip_fast.wav")),
        "lock_ready": wav_b64(os.path.join(SFX_DIR, "lock_ready.wav")),
        "plane_whoosh": wav_b64(os.path.join(SFX_DIR, "plane_whoosh.wav")),
        "cash_register": wav_b64(os.path.join(SFX_DIR, "cash_register.wav")),
        "kyle_hey": wav_b64(os.path.join(CLIPS_DIR, "kyle_02_hey_bright.wav")),
        "kyle_cut": wav_b64(os.path.join(CLIPS_DIR, "cut_02_give_me_a_cut.wav")),
        "kyle_wheres": wav_b64(os.path.join(CLIPS_DIR, "cut_01_wheres_my_cut.wav")),
        "kyle_whoa": wav_b64(os.path.join(CLIPS_DIR, "whoa_04_punch.wav")),
        "kyle_clients": wav_b64(os.path.join(CLIPS_DIR, "clients_02_will_scream.wav")),
    }

    payload_json = json.dumps({"weapons": weapons_data, "audio": audio_map})

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kyle Tillet — Top 3 Upgraded 2D FPS Weapon Prototypes (#1, #3, #4)</title>
<style>
  :root {{
    --bg: #0f0d0b;
    --panel: #191512;
    --panel2: #221c17;
    --border: #3b3127;
    --text: #f3efe9;
    --muted: #a69a8c;
    --accent: #f59e0b;
    --green: #22c55e;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top, #1f1914 0%, var(--bg) 60%);
    color: var(--text); line-height: 1.45;
  }}
  header.top {{
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;
    padding: 12px 20px; background: #15120f; border-bottom: 1px solid var(--border);
  }}
  .brand h1 {{ margin: 0; font-size: 1.25rem; letter-spacing: 0.01em; }}
  .brand small {{ color: var(--muted); font-size: 0.84rem; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .tab {{
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 14px; font-size: 0.88rem; font-weight: 700; cursor: pointer;
  }}
  .tab:hover {{ border-color: #7c6752; }}
  .tab.active {{ background: #3f2b12; border-color: var(--accent); color: #fde68a; }}
  .wrap {{ max-width: 1380px; margin: 0 auto; padding: 16px 18px 48px; }}

  .stage-grid {{
    display: grid; grid-template-columns: minmax(0, 1fr) 350px; gap: 16px; align-items: start;
  }}
  @media (max-width: 1020px) {{ .stage-grid {{ grid-template-columns: 1fr; }} }}

  .fps-box {{
    background: #080706; border: 2px solid var(--border); border-radius: 12px; overflow: hidden;
  }}
  .fps-bar {{
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;
    padding: 10px 14px; background: #16120e; border-bottom: 1px solid var(--border);
  }}
  .btn {{
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 7px; padding: 7px 12px; font-size: 0.83rem; font-weight: 700; cursor: pointer;
  }}
  .btn:hover {{ border-color: #856e57; }}
  .btn.active {{ background: #3f2b12; border-color: var(--accent); color: #fde68a; }}
  .btn.fire {{ background: linear-gradient(180deg, #dc2626, #991b1b); border-color: #ef4444; color: #fff; }}
  .btn.pick {{ background: linear-gradient(180deg, #16a34a, #15803d); border-color: #22c55e; color: #fff; }}
  canvas#fps {{
    display: block; width: 100%; aspect-ratio: 16 / 9; cursor: crosshair; user-select: none;
  }}
  .fps-hint {{
    padding: 8px 14px; font-size: 0.82rem; color: var(--muted); background: #13100d;
    border-top: 1px solid var(--border); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  }}

  .side-panel {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px;
    display: flex; flex-direction: column; gap: 12px;
  }}
  .style-badge {{
    display: inline-block; font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 3px 9px; border-radius: 6px;
    background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.35);
    align-self: flex-start;
  }}
  .side-panel h2 {{ margin: 0; font-size: 1.28rem; }}
  .side-panel p {{ margin: 0; font-size: 0.9rem; color: var(--muted); }}
  .kv {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .kv-box {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px;
  }}
  .kv-box small {{ display: block; color: var(--muted); font-size: 0.72rem; text-transform: uppercase; }}
  .kv-box b {{ font-size: 0.92rem; }}

  .gallery-head {{ margin: 24px 0 12px; display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
  .gallery-head h3 {{ margin: 0; font-size: 1.15rem; }}
  .gallery {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px;
  }}
  .gcard {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px;
    cursor: pointer; display: flex; flex-direction: column; gap: 8px; transition: border-color 0.15s, transform 0.12s;
  }}
  .gcard:hover {{ border-color: #8b745d; transform: translateY(-2px); }}
  .gcard.active {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
  .gcard.winner {{ border-color: var(--green); box-shadow: 0 0 0 2px var(--green); }}
  .gthumb {{
    height: 220px; border-radius: 8px; background: radial-gradient(circle at 50% 60%, #2a313f, #11151d);
    display: flex; align-items: flex-end; justify-content: center; overflow: hidden; padding-top: 8px;
  }}
  .gthumb img {{ max-width: 94%; max-height: 96%; object-fit: contain; }}
  .gtitle {{ font-weight: 800; font-size: 1.02rem; }}
  .gsub {{ font-size: 0.78rem; color: var(--accent); font-weight: 700; }}
  .gdesc {{ font-size: 0.83rem; color: var(--muted); }}
</style>
</head>
<body>
<header class="top">
  <div class="brand">
    <h1>Kyle Tillet &mdash; Upgraded Top 3 2D FPS Weapon Prototypes (#1, #3, #4)</h1>
    <small>Zero-ghost multi-keyframe cel animation · Scissoring arms &amp; darting eyes (#1) · Heavy multi-pose animation (#3) · Redesigned forward-aiming Briefcase (#4)</small>
  </div>
  <div class="tabs" id="top-tabs"></div>
</header>

<div class="wrap">
  <div class="stage-grid">
    <div class="fps-box">
      <div class="fps-bar">
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn active" id="st-idle" onclick="setAnim('idle')">Idle</button>
          <button class="btn" id="st-lock" onclick="setAnim('lock')">Hold-to-Lock (Fast!)</button>
          <button class="btn fire" id="st-fire" onclick="triggerFire()">&#128293; Fire / Launch Kyle</button>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
          <button class="btn" id="btn-spd" onclick="cycleSpeed()">Speed: 1.0&times;</button>
          <label style="font-size:0.82rem;color:var(--muted);display:flex;align-items:center;gap:5px;cursor:pointer;">
            <input type="checkbox" id="chk-sound" checked> SFX
          </label>
          <button class="btn" id="btn-bg" onclick="cycleBg()">Arena: Bakersfield</button>
        </div>
      </div>
      <canvas id="fps" width="1280" height="720"></canvas>
      <div class="fps-hint">
        <span><b>Interactive FPS Test:</b> Hold Left Mouse on the viewport to <b>Lock-On</b> (fast chomp + reticle); release to <b>Launch Kyle</b>!</span>
        <span id="hud-readout">State: IDLE</span>
      </div>
    </div>

    <aside class="side-panel">
      <span class="style-badge" id="p-style">Style</span>
      <h2 id="p-title">Title</h2>
      <p id="p-tagline">Tagline</p>
      <div class="kv">
        <div class="kv-box"><small>Pipeline</small><b>2D Card + .SKIN</b></div>
        <div class="kv-box"><small>Animation</small><b>Crisp Multi-Keyframe Cel</b></div>
        <div class="kv-box"><small>Empty Launch</small><b>True Empty Frame</b></div>
        <div class="kv-box"><small>Slot</small><b>Fun Gun #8 (imp 68)</b></div>
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;margin-top:4px;">
        <button class="btn pick" id="btn-pick" onclick="pickWinner()">&#10004; Pick This Design as Winner</button>
        <button class="btn" onclick="copyWinner()">Copy Choice for Next Step</button>
        <div id="pick-status" style="font-size:0.82rem;color:#6ee7b7;min-height:1.2em;"></div>
      </div>
    </aside>
  </div>

  <div class="gallery-head">
    <h3>3 Finalists Side-by-Side (Click Any Card to Preview Live in FPS)</h3>
    <span style="font-size:0.84rem;color:var(--muted);">Try Speed 0.5&times; to inspect #1's darting eyes &amp; scissoring arms, #3's kicking legs &amp; flexing bow, and #4's forward briefcase aim!</span>
  </div>
  <div class="gallery" id="gallery"></div>
</div>

<script>
const DATA = {payload_json};
const WEAPONS = DATA.weapons;
const AUDIO = DATA.audio;

const canvas = document.getElementById("fps");
const ctx = canvas.getContext("2d");

let curIdx = 0;
let animMode = "idle";
let fireStartMs = 0;
let holdingMouse = false;
let holdStartMs = 0;
let bgMode = 0;
let winnerId = null;
let loadedSheets = {{}};
let mouseX = 640, mouseY = 360;
let lastSnipSound = 0;
let speedMult = 1.0;
const SPEEDS = [1.0, 0.5, 1.4];
let speedIdx = 0;

WEAPONS.forEach(w => {{
  loadedSheets[w.id] = {{}};
  ["idle", "lock", "fire"].forEach(k => {{
    const img = new Image();
    img.src = w[k].url;
    loadedSheets[w.id][k] = img;
  }});
}});

function playSound(key, vol = 0.82) {{
  if (!document.getElementById("chk-sound").checked) return;
  const src = AUDIO[key];
  if (!src) return;
  const a = new Audio(src);
  a.volume = vol;
  a.play().catch(() => {{}});
}}

function buildUI() {{
  const tabs = document.getElementById("top-tabs");
  const gal = document.getElementById("gallery");
  tabs.innerHTML = "";
  gal.innerHTML = "";
  WEAPONS.forEach((w, i) => {{
    const b = document.createElement("button");
    b.className = "tab" + (i === curIdx ? " active" : "");
    b.textContent = `#${{w.num}} ${{w.title.replace(" (Upgraded)", "").replace(" (Redesigned Forward Aim)", "")}}`;
    b.onclick = () => selectWeapon(i);
    tabs.appendChild(b);

    const c = document.createElement("div");
    c.className = "gcard" + (i === curIdx ? " active" : "") + (winnerId === w.id ? " winner" : "");
    c.onclick = () => selectWeapon(i);
    c.innerHTML = `
      <div class="gthumb"><img src="${{w.thumb}}" alt="${{w.title}}"></div>
      <div class="gsub">#${{w.num}} &middot; ${{w.style}}</div>
      <div class="gtitle">${{w.title}}</div>
      <div class="gdesc">${{w.tagline}}</div>
    `;
    gal.appendChild(c);
  }});

  const w = WEAPONS[curIdx];
  document.getElementById("p-style").textContent = `#${{w.num}} · ${{w.style}}`;
  document.getElementById("p-title").textContent = w.title;
  document.getElementById("p-tagline").textContent = w.tagline;
  document.getElementById("pick-status").textContent = winnerId
    ? `Selected winner: #${{WEAPONS.find(x => x.id === winnerId).num}} ${{WEAPONS.find(x => x.id === winnerId).title}}`
    : "";
}}

function selectWeapon(idx) {{
  curIdx = idx;
  animMode = "idle";
  updateAnimButtons();
  buildUI();
}}

function setAnim(mode) {{
  animMode = mode;
  if (mode === "fire") fireStartMs = performance.now();
  updateAnimButtons();
}}

function triggerFire() {{
  animMode = "fire";
  fireStartMs = performance.now();
  playSound(WEAPONS[curIdx].id === "v4_audit_briefcase" ? "cash_register" : "plane_whoosh", 0.65);
  const voiceKeys = ["kyle_cut", "kyle_hey", "kyle_wheres", "kyle_whoa", "kyle_clients"];
  playSound(voiceKeys[Math.floor(Math.random() * voiceKeys.length)], 0.9);
  updateAnimButtons();
}}

function updateAnimButtons() {{
  document.getElementById("st-idle").classList.toggle("active", animMode === "idle");
  document.getElementById("st-lock").classList.toggle("active", animMode === "lock");
}}

function cycleSpeed() {{
  speedIdx = (speedIdx + 1) % SPEEDS.length;
  speedMult = SPEEDS[speedIdx];
  document.getElementById("btn-spd").textContent = `Speed: ${{speedMult.toFixed(1)}}×`;
}}

function cycleBg() {{
  bgMode = (bgMode + 1) % 3;
  const names = ["Arena: Bakersfield", "Arena: Night Soi 6", "Arena: Dark Studio"];
  document.getElementById("btn-bg").textContent = names[bgMode];
}}

function pickWinner() {{
  winnerId = WEAPONS[curIdx].id;
  playSound("lock_ready", 0.8);
  buildUI();
}}

function copyWinner() {{
  const w = WEAPONS.find(x => x.id === (winnerId || WEAPONS[curIdx].id));
  const msg = `Let's lock in Design #${{w.num}}: ${{w.title}} (${{w.id}})`;
  navigator.clipboard?.writeText(msg).then(() => {{
    document.getElementById("pick-status").textContent = `Copied: "${{msg}}"`;
  }}).catch(() => alert(msg));
}}

canvas.addEventListener("mousemove", e => {{
  const r = canvas.getBoundingClientRect();
  mouseX = ((e.clientX - r.left) / r.width) * 1280;
  mouseY = ((e.clientY - r.top) / r.height) * 720;
}});
canvas.addEventListener("mousedown", () => {{
  holdingMouse = true;
  holdStartMs = performance.now();
  animMode = "lock";
  updateAnimButtons();
}});
window.addEventListener("mouseup", () => {{
  if (!holdingMouse) return;
  holdingMouse = false;
  triggerFire();
}});

function drawBackdrop(t) {{
  const W = 1280, H = 720;
  if (bgMode === 2) {{
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#1c222e");
    g.addColorStop(1, "#0d1118");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    for (let x = 0; x < W; x += 64) {{ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }}
    for (let y = 0; y < H; y += 64) {{ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }}
    return;
  }}
  const sky = ctx.createLinearGradient(0, 0, 0, 390);
  if (bgMode === 0) {{
    sky.addColorStop(0, "#3b6fa6");
    sky.addColorStop(1, "#d9b98c");
  }} else {{
    sky.addColorStop(0, "#0b1026");
    sky.addColorStop(1, "#3b1742");
  }}
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, 390);

  const gnd = ctx.createLinearGradient(0, 390, 0, H);
  gnd.addColorStop(0, bgMode === 0 ? "#4a433c" : "#1c1926");
  gnd.addColorStop(1, bgMode === 0 ? "#24201c" : "#0b0a10");
  ctx.fillStyle = gnd;
  ctx.fillRect(0, 390, W, H - 390);

  ctx.fillStyle = bgMode === 0 ? "#3c322b" : "#171422";
  ctx.fillRect(40, 210, 260, 180);
  ctx.fillRect(920, 180, 320, 210);
  ctx.fillStyle = bgMode === 0 ? "#5c4a3c" : "#251e36";
  ctx.fillRect(360, 270, 220, 120);

  // Flying John Bird target silhouette
  const bx = 640 + Math.sin(t * 1.4) * 210;
  const by = 210 + Math.cos(t * 2.1) * 40;
  ctx.save();
  ctx.translate(bx, by);
  ctx.fillStyle = "rgba(15, 23, 42, 0.78)";
  ctx.beginPath();
  ctx.ellipse(0, 0, 38, 18, 0, 0, Math.PI * 2);
  ctx.fill();
  const flap = Math.sin(t * 11) * 24;
  ctx.strokeStyle = "#94a3b8";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(-12, -4); ctx.quadraticCurveTo(-55, -35 + flap, -88, -10 + flap);
  ctx.moveTo(12, -4); ctx.quadraticCurveTo(55, -35 + flap, 88, -10 + flap);
  ctx.stroke();
  ctx.fillStyle = "#fde047";
  ctx.font = "bold 12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("JOHN BIRD TARGET", 0, -28);
  ctx.restore();
}}

function drawCrosshair(now) {{
  const cx = 640, cy = 360;
  ctx.save();
  if (animMode === "lock") {{
    const prog = holdingMouse ? Math.min(1, (now - holdStartMs) / 600) : 0.75 + 0.25 * Math.sin(now * 0.01);
    const rad = 46 - prog * 24;
    ctx.strokeStyle = prog >= 0.98 ? "#22c55e" : "#f59e0b";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(cx, cy, rad, 0, Math.PI * 2 * prog);
    ctx.stroke();
    ctx.font = "bold 13px system-ui";
    ctx.fillStyle = prog >= 0.98 ? "#4ade80" : "#fcd34d";
    ctx.textAlign = "center";
    ctx.fillText(prog >= 0.98 ? "CLIENT LOCKED! RELEASE TO FIRE" : "LOCKING ON...", cx, cy - rad - 10);
  }}
  ctx.strokeStyle = "rgba(255,255,255,0.88)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - 12, cy); ctx.lineTo(cx - 4, cy);
  ctx.moveTo(cx + 4, cy); ctx.lineTo(cx + 12, cy);
  ctx.moveTo(cx, cy - 12); ctx.lineTo(cx, cy - 4);
  ctx.moveTo(cx, cy + 4); ctx.lineTo(cx, cy + 12);
  ctx.stroke();
  ctx.restore();
}}

function loop(now) {{
  const t = (now * 0.001) * speedMult;
  drawBackdrop(now * 0.001);

  const w = WEAPONS[curIdx];
  let mode = animMode;
  let frameIdx = 0;
  if (mode === "idle") {{
    frameIdx = Math.floor(t * w.fps_idle) % w.idle.count;
  }} else if (mode === "lock") {{
    frameIdx = Math.floor(t * w.fps_lock) % w.lock.count;
    if (holdingMouse && now - lastSnipSound > 160) {{
      lastSnipSound = now;
      playSound("snip_fast", 0.35);
    }}
  }} else {{
    const el = ((now - fireStartMs) / 1000) * speedMult;
    const f = Math.floor(el * w.fps_fire);
    if (f >= w.fire.count) {{
      animMode = "idle";
      mode = "idle";
      updateAnimButtons();
      frameIdx = 0;
    }} else {{
      frameIdx = f;
    }}
  }}

  const strip = w[mode];
  const img = loadedSheets[w.id][mode];
  if (img && img.complete && img.naturalWidth > 0) {{
    const col = frameIdx % strip.cols;
    const row = Math.floor(frameIdx / strip.cols);
    const sx = col * strip.fw;
    const sy = row * strip.fh;

    const targetH = Math.min(620, strip.fh * 1.15 * w.scale);
    const targetW = targetH * (strip.fw / strip.fh);
    const swayX = ((mouseX - 640) / 640) * 16;
    const swayY = ((mouseY - 360) / 360) * 10;

    let dx;
    if (w.anchor === "center") {{
      dx = (1280 - targetW) * 0.5 + w.offset_x;
    }} else if (w.anchor === "right") {{
      dx = 1280 - targetW + w.offset_x;
    }} else {{
      dx = (1280 - targetW) * 0.62 + w.offset_x;
    }}
    dx += swayX;
    const dy = 720 - targetH + w.offset_y + swayY;

    ctx.drawImage(img, sx, sy, strip.fw, strip.fh, dx, dy, targetW, targetH);
  }}

  drawCrosshair(now);
  document.getElementById("hud-readout").textContent = `Design #${{w.num}} · State: ${{mode.toUpperCase()}} · Frame ${{frameIdx + 1}}/${{strip.count}} · ${{speedMult.toFixed(1)}}×`;
  requestAnimationFrame(loop);
}}

buildUI();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print(f"Wrote upgraded 3-finalist 2D Weapon Showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
