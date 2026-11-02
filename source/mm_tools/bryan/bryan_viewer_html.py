"""Generates the interactive 360° HTML Sprite Showcase & Soundboard for Tinfoil-Hat Bryan & His Demons:
  - G:\\Quake\\Combat\\BakersfieldQuake\\bryan_sprite\\index.html
  - G:\\Quake\\Combat\\BakersfieldQuake\\bryan_demons.html
"""
import os

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
WEB_DIR = os.path.join(MOD_DIR, "bryan_sprite")


def build_html(img_prefix="", snd_prefix="../sound/bryan/"):
    ground_pct = round(100.0 * 296.0 / 324.0, 3)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tinfoil-Hat Bryan &amp; His Demons — 360° Quake Sprite Showcase</title>
<style>
  :root {{
    --bg:#0f1117; --panel:#1a1d27; --panel2:#232836; --ink:#f8fafc; --dim:#94a3b8;
    --accent:#ef4444; --accent2:#38bdf8; --neon:#4ade80; --warn:#fbbf24;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:18px 16px 44px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:960px; }}
  h1 {{ font-size:23px; margin:0 0 4px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13.5px; margin:0; }}
  .sub code {{ color:#fca5a5; background:#29181d; padding:1px 6px; border-radius:4px; }}

  .tabs {{
    display:flex; flex-wrap:wrap; gap:7px; justify-content:center;
    width:min(100%, 960px); background:var(--panel); border:1px solid #2d3446;
    border-radius:12px; padding:8px;
  }}
  .tab {{
    flex:1 1 145px; padding:9px 10px; border-radius:8px; border:1.5px solid #323a4e;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12.5px;
    cursor:pointer; transition:all 0.12s ease; text-align:center;
  }}
  .tab:hover {{ border-color:#5a6684; }}
  .tab.on {{ background:#35161c; border-color:var(--accent); color:#fecaca; box-shadow:0 0 14px rgba(239,68,68,0.24); }}

  #stage {{
    width:min(100%, 960px); height:min(62vh, 520px); min-height:360px;
    border-radius:14px; border:1px solid #363e52; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker  {{ background:repeating-conic-gradient(#262a35 0% 25%, #1b1f28 0% 50%) 0 0/24px 24px; }}
  #stage.quake    {{ background:radial-gradient(circle at 50% 70%, #432d1f 0%, #1d140f 68%, #0b0807 100%); }}
  #stage.hellfire {{ background:radial-gradient(circle at 50% 78%, #6d1814 0%, #2a0b10 62%, #09060a 100%); }}
  #stage.slate    {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0f172a 85%); }}

  #wrap {{
    position:relative; height:94%; aspect-ratio:360/324;
    display:flex; align-items:center; justify-content:center;
  }}
  #view {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  #view.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:4%; right:4%; top:{ground_pct}%; border-top:1.5px dashed rgba(251,191,36,0.88); }}
  .aline {{ position:absolute; top:4%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.68); }}
  .odot  {{ position:absolute; left:50%; top:{ground_pct}%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--warn); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(12,15,22,0.88);
    border:1px solid #443846; border-radius:8px; padding:6px 12px;
    font-size:13px; font-weight:800; color:#fca5a5; pointer-events:none; z-index:5;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(12,15,22,0.85);
    border:1px solid #3c4458; border-radius:8px; padding:5px 11px;
    font-size:12px; color:var(--dim); pointer-events:none; font-variant-numeric:tabular-nums; z-index:5;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(12,15,22,0.82);
    border:1px solid #2e3545; border-radius:6px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none; z-index:5;
  }}

  .row {{
    display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center;
    width:min(100%, 960px); background:var(--panel); border:1px solid #2e3444;
    border-radius:10px; padding:10px 14px;
  }}
  button.ctrl {{
    background:var(--accent); color:#fff; border:0; border-radius:6px;
    padding:7px 13px; font:inherit; font-weight:700; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--accent2); color:#082f49; }}
  button.ctrl.alt  {{ background:#333a4b; color:var(--ink); font-weight:600; }}
  button.snd {{
    background:#262d3f; color:#e2e8f0; border:1px solid #3d4863; border-radius:7px;
    padding:7px 11px; font:inherit; font-size:12.5px; font-weight:700; cursor:pointer;
    transition:all 0.12s;
  }}
  button.snd:hover {{ border-color:var(--neon); color:#bbf7d0; background:#1c3128; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 960px);
  }}
  @media (max-width:720px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid transparent;
    border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px;
    color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--accent); color:var(--ink); background:#2c2229; }}
  #strip img {{ width:100%; aspect-ratio:360/324; object-fit:contain; display:block; }}

  .sheets {{
    width:min(100%, 960px); display:flex; flex-direction:column; gap:14px; margin-top:8px;
  }}
  .card {{
    background:var(--panel); border:1px solid #2e3444; border-radius:12px; padding:14px;
  }}
  .card h2 {{ font-size:15px; margin:0 0 8px; color:#f1f5f9; }}
  .card img {{ width:100%; border-radius:8px; display:block; border:1px solid #2d3446; }}
  .gif-row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  @media (max-width:680px) {{ .gif-row {{ grid-template-columns:1fr; }} }}
  p.hint {{ color:var(--dim); margin:0; font-size:12.5px; text-align:center; }}
</style>
</head>
<body>
  <header>
    <h1>🛸 Tinfoil-Hat Bryan &amp; His Demons — 360° Quake Sprite</h1>
    <p class="sub">
      <code>progs/bryan.spr32</code> (264 frames &bull; 320&times;288 &bull; origin -160, 263) &bull;
      Summon in-game with <code>impulse 19</code> or Mystery Box <code>mb_force 17</code>
    </p>
  </header>

  <div class="tabs">
    <button class="tab on" data-mode="run">🏃 360° Bryan Run — Solo (8&times;6f)</button>
    <button class="tab" data-mode="scan">📡 360° Detector Scan — Solo (8&times;6f)</button>
    <button class="tab" data-mode="whirl">🌪️ 360° "NO WAY!" Demon-Whirl (8&times;8f)</button>
    <button class="tab" data-mode="surge">⚡ 360° Demon-Trio Surge (8&times;8f)</button>
    <button class="tab" data-mode="death">🔥 Hell Portal Death (32f)</button>
    <button class="tab" data-mode="spr32">🕹️ DarkPlaces .SPR32 (264f)</button>
  </div>

  <div id="stage" class="checker">
    <div id="badge">0° Front · Bryan Run (Solo)</div>
    <div id="meta">Frame 0/5</div>
    <div id="wrap">
      <img id="view" alt="Bryan & Demons sprite frame">
      <div id="reticle">
        <div class="gline"></div>
        <div class="aline"></div>
        <div class="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag horizontally to orbit 360°</div>
  </div>

  <div class="row">
    <button class="ctrl" id="play">Pause</button>
    <button class="ctrl spin" id="orbit">Auto-Spin 360°: ON</button>
    <label>Angle <input id="ang" type="range" min="0" max="7" value="0" style="width:120px"></label>
    <label>FPS <input id="fps" type="range" min="4" max="20" value="11" style="width:90px"></label>
    <button class="ctrl alt" id="origbtn">Origin: OFF</button>
    <button class="ctrl alt" id="bgbtn">BG: Checker</button>
  </div>

  <div class="row">
    <strong style="font-size:12.5px;color:#fca5a5;">🔊 Bryan Audio Soundboard:</strong>
    <button class="snd" data-wav="sense.wav">📡 "Demons in here, I can sense it"</button>
    <button class="snd" data-wav="detector.wav">🎛️ "My Demon Detector"</button>
    <button class="snd" data-wav="noway.wav">😱 "A DEMON! NO WAY!"</button>
    <button class="snd" data-wav="whirl.wav">🌪️ 360° Demon Swing Brawl</button>
    <button class="snd" data-wav="slash.wav">⚡ Demon-Trio Surge</button>
    <button class="snd" data-wav="portal_die.wav">🔥 Hell Portal Death</button>
  </div>

  <p class="hint">Drag left/right on stage or press <b>Left/Right Arrows</b> to orbit 360° &bull; <b>Up/Down Arrows</b> step frames &bull; <b>Space</b> pauses</p>
  <div id="strip"></div>

  <div class="sheets">
    <div class="gif-row">
      <div class="card">
        <h2>🌀 360° Sprint Chase Turnaround GIF</h2>
        <img src="{img_prefix}bryan_360_spin.gif" alt="Bryan 360 Spin GIF">
      </div>
      <div class="card">
        <h2>🌪️ "A DEMON! NO WAY!" Giant-Swing &amp; Demon-Trio Surge GIF</h2>
        <img src="{img_prefix}bryan_demon_whirl.gif" alt="Bryan Demon Whirl GIF">
      </div>
    </div>
    <div class="card">
      <h2>📐 Full 360° 8-Angle Turnaround Matrix (Scan &bull; Sprint Chase &bull; Giant-Swing Whirl &bull; 3-Demon Trio Surge)</h2>
      <img src="{img_prefix}bryan_360_turnaround_sheet.png" alt="Bryan 360 Turnaround Sheet">
    </div>
    <div class="card">
      <h2>🔥 32-Frame 4-Act Hell Portal Drag-Down &amp; Smoking Tinfoil Hat Death Sequence (Frames 232..263)</h2>
      <img src="{img_prefix}bryan_death_contact_sheet.jpg" alt="Bryan Hell Portal Death Sheet">
    </div>
    <div class="card">
      <h2>🕹️ Live In-Game DarkPlaces Verification (<code>map start</code> &bull; <code>impulse 19</code>)</h2>
      <div class="gif-row">
        <img src="{img_prefix}ingame_scan.jpg" alt="In-game Paranoid Detector Scan">
        <img src="{img_prefix}ingame_sprint.jpg" alt="In-game 360 Sprint Chase">
        <img src="{img_prefix}ingame_whirl.jpg" alt="In-game Giant-Swing Demon Whirl">
        <img src="{img_prefix}ingame_trio_surge.jpg" alt="In-game 3-Demon Trio EMF Surge">
      </div>
    </div>
  </div>

<script>
const PFX = "{img_prefix}", SND = "{snd_prefix}";
const LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];

const srcFor = (m, d, f) => {{
  if (m === "scan")  return `${{PFX}}bryan_scan_d${{d}}_f${{f}}.png`;
  if (m === "whirl") return `${{PFX}}bryan_whirl_d${{d}}_f${{f}}.png`;
  if (m === "surge") return `${{PFX}}bryan_surge_d${{d}}_f${{f}}.png`;
  if (m === "death") return `${{PFX}}bryan_death_${{String(f).padStart(2, "0")}}.png`;
  if (m === "spr32") return `${{PFX}}spr32/f_${{String(8 + d * 6 + f).padStart(3, "0")}}.png`;
  return `${{PFX}}bryan_run_d${{d}}_f${{f}}.png`;
}};

let mode = "run", curDir = 0, curFrame = 0, playing = true, autoSpin = true;
let showOrigin = false, bgi = 0;
const bgs = ["checker", "quake", "hellfire", "slate"], bgNames = ["Checker", "Quake Dungeon", "Hellfire", "Dark Slate"];
let lastFrameT = 0, lastSpinT = 0;

const view = document.getElementById("view"), badge = document.getElementById("badge"),
      meta = document.getElementById("meta"), stage = document.getElementById("stage"),
      playBtn = document.getElementById("play"), orbitBtn = document.getElementById("orbit"),
      angEl = document.getElementById("ang"), fpsEl = document.getElementById("fps"),
      origBtn = document.getElementById("origbtn"), bgBtn = document.getElementById("bgbtn"),
      reticle = document.getElementById("reticle"), strip = document.getElementById("strip");

const thumbs = [], thumbImgs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  const im = document.createElement("img");
  im.src = `${{PFX}}bryan_run_d${{d}}_f0.png`;
  const sp = document.createElement("span");
  sp.textContent = (d * 45) + "°";
  b.appendChild(im); b.appendChild(sp);
  b.onclick = () => {{ autoSpin = false; syncControls(); render(d, curFrame); }};
  strip.appendChild(b);
  thumbs.push(b); thumbImgs.push(im);
}}

function frameCount() {{
  if (mode === "whirl" || mode === "surge") return 8;
  if (mode === "death") return 32;
  return 6;
}}

function modeTitle() {{
  if (mode === "scan")  return "Solo Detector Scan";
  if (mode === "whirl") return "Giant-Swing Demon-Whirl";
  if (mode === "surge") return "3-Demon Trio EMF Surge";
  if (mode === "death") return "4-Act Hell Portal Death";
  if (mode === "spr32") return "DarkPlaces Toned .SPR32 (Solo Run)";
  return "Bryan Run (Solo)";
}}

function render(d, f) {{
  curDir = ((d % 8) + 8) % 8;
  const nf = frameCount();
  curFrame = ((f % nf) + nf) % nf;
  angEl.value = curDir;
  view.classList.toggle("pixel", mode === "spr32");
  view.src = srcFor(mode, curDir, curFrame);

  if (mode === "death") {{
    badge.textContent = modeTitle();
    meta.textContent = `SPR32 #${{232 + curFrame}} · Frame ${{curFrame}}/31`;
  }} else if (mode === "spr32") {{
    const sidx = 8 + curDir * 6 + curFrame;
    badge.textContent = `${{LABELS[curDir]}} · ${{modeTitle()}}`;
    meta.textContent = `progs/bryan.spr32 #${{sidx}} (toned)`;
  }} else {{
    badge.textContent = `${{LABELS[curDir]}} · ${{modeTitle()}}`;
    meta.textContent = `Frame ${{curFrame}}/${{nf - 1}}`;
  }}

  const stripMode = (mode === "death") ? "scan" : mode;
  const stripF = curFrame % ((stripMode === "whirl" || stripMode === "surge") ? 8 : 6);
  thumbImgs.forEach((im, k) => {{ im.src = srcFor(stripMode, k, stripF); }});
  thumbs.forEach((b, k) => b.classList.toggle("on", k === curDir));
}}

function syncControls() {{
  playBtn.textContent = playing ? "Pause" : "Play";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  origBtn.textContent = "Origin: " + (showOrigin ? "ON" : "OFF");
  reticle.classList.toggle("on", showOrigin);
  stage.className = bgs[bgi];
  bgBtn.textContent = "BG: " + bgNames[bgi];
}}

document.querySelectorAll(".tab").forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("on"));
    btn.classList.add("on");
    mode = btn.dataset.mode;
    curFrame = 0;
    render(curDir, 0);
  }};
}});

playBtn.onclick = () => {{ playing = !playing; syncControls(); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncControls(); }};
angEl.oninput = () => {{ autoSpin = false; syncControls(); render(+angEl.value, curFrame); }};
origBtn.onclick = () => {{ showOrigin = !showOrigin; syncControls(); }};
bgBtn.onclick = () => {{ bgi = (bgi + 1) % bgs.length; syncControls(); }};

let curAudio = null;
document.querySelectorAll("button.snd").forEach(btn => {{
  btn.onclick = () => {{
    if (curAudio) {{ curAudio.pause(); curAudio.currentTime = 0; }}
    curAudio = new Audio(SND + btn.dataset.wav);
    curAudio.play();
  }};
}});

// Drag-to-orbit on stage
let dragStartX = null, dragStartDir = 0;
stage.addEventListener("pointerdown", e => {{
  dragStartX = e.clientX; dragStartDir = curDir;
  stage.classList.add("drag"); stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener("pointermove", e => {{
  if (dragStartX === null) return;
  const step = Math.round((e.clientX - dragStartX) / 42);
  if (step !== 0) {{ autoSpin = false; syncControls(); render(dragStartDir + step, curFrame); }}
}});
stage.addEventListener("pointerup", () => {{ dragStartX = null; stage.classList.remove("drag"); }});

window.addEventListener("keydown", e => {{
  if (e.key === "ArrowLeft")  {{ autoSpin = false; syncControls(); render(curDir - 1, curFrame); }}
  if (e.key === "ArrowRight") {{ autoSpin = false; syncControls(); render(curDir + 1, curFrame); }}
  if (e.key === "ArrowUp")    {{ playing = false; syncControls(); render(curDir, curFrame + 1); }}
  if (e.key === "ArrowDown")  {{ playing = false; syncControls(); render(curDir, curFrame - 1); }}
  if (e.key === " ")          {{ e.preventDefault(); playing = !playing; syncControls(); }}
}});

function tick(ts) {{
  const fps = +fpsEl.value || 11;
  if (playing && ts - lastFrameT >= 1000 / fps) {{
    lastFrameT = ts;
    render(curDir, curFrame + 1);
  }}
  if (autoSpin && mode !== "death" && ts - lastSpinT >= 680) {{
    lastSpinT = ts;
    render(curDir + 1, curFrame);
  }}
  requestAnimationFrame(tick);
}}
syncControls();
render(0, 0);
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def main():
    os.makedirs(WEB_DIR, exist_ok=True)
    p1 = os.path.join(WEB_DIR, "index.html")
    with open(p1, "w", encoding="utf-8") as fp:
        fp.write(build_html(img_prefix="", snd_prefix="../sound/bryan/"))
    print("Wrote folder HTML viewer:", p1)


if __name__ == "__main__":
    main()
