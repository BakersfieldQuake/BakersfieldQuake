"""Packs all 16 full-body Hero Dance RGBA frames, all 48 360-degree Turnaround RGBA frames,
and Rob's real laugh MP3 into a single 100% self-contained standalone HTML inspector file
with zero external dependencies."""

import base64
import io
import json
import os
from PIL import Image

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
SPRITE_DIR = os.path.join(ROOT, "mrdiy_sprite")
OUT_HTML = os.path.join(SPRITE_DIR, "rob_mrdiy_standalone.html")
INDEX_HTML = os.path.join(SPRITE_DIR, "index.html")


def png_to_webp_data_uri(png_path: str, quality: int = 92) -> str:
    im = Image.open(png_path).convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, alpha_quality=96, method=4)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def build_self_contained_html():
    hero_uris = [
        png_to_webp_data_uri(os.path.join(SPRITE_DIR, f"mrdiy_{k:02d}.png"), quality=93)
        for k in range(16)
    ]

    dir_uris = []
    for d in range(8):
        row = [
            png_to_webp_data_uri(os.path.join(SPRITE_DIR, f"mrdiy_d{d}_f{f}.png"), quality=90)
            for f in range(6)
        ]
        dir_uris.append(row)

    mp3_path = os.path.join(SPRITE_DIR, "mrdiy_laugh.mp3")
    with open(mp3_path, "rb") as f:
        mp3_b64 = base64.b64encode(f.read()).decode("ascii")
    audio_uri = f"data:audio/mpeg;base64,{mp3_b64}"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rob's MR. D.I.Y. Full-Body Sprite Inspector (Self-Contained)</title>
<style>
  :root {{
    --bg:#12141a; --panel:#1d212b; --panel2:#262b38; --ink:#f3f5f9;
    --dim:#9aa3b5; --diy:#ffd217; --red:#e11d24; --accent:#38bdf8;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:16px 16px 36px; min-height:100vh;
  }}
  header {{ display:flex; flex-direction:column; align-items:center; gap:8px; text-align:center; }}
  h1 {{ font-size:21px; margin:0; font-weight:800; display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:center; }}
  .diy-logo {{
    background:var(--diy); color:#1a1204; border:2px solid var(--red);
    border-radius:7px; padding:2px 10px; font-size:13px; font-weight:900; letter-spacing:0.03em;
  }}
  .tabs {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }}
  .tabs button {{
    background:var(--panel2); color:var(--dim); border:2px solid transparent;
    border-radius:8px; padding:8px 15px; font:inherit; font-weight:700; cursor:pointer; transition:0.15s;
  }}
  .tabs button.active {{ background:#2c2510; color:var(--diy); border-color:var(--diy); }}

  #stage {{
    width:min(100%, 840px); height:min(68vh, 690px);
    border-radius:14px; display:flex; align-items:center; justify-content:center;
    overflow:hidden; border:1px solid #353c4d; position:relative;
    cursor:grab; touch-action:none; user-select:none;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker-dark {{ background:repeating-conic-gradient(#2a2e39 0% 25%, #1e222b 0% 50%) 0 0/24px 24px; }}
  #stage.checker-light {{ background:repeating-conic-gradient(#e4e7ee 0% 25%, #cbd1dc 0% 50%) 0 0/24px 24px; }}
  #stage.white {{ background:#ffffff; }}
  #stage.store {{ background:radial-gradient(circle at 50% 42%, #4a3f28 0%, #231e16 68%, #12100d 100%); }}
  #stage.quake {{ background:radial-gradient(circle at 50% 62%, #3d2e22 0%, #1c1510 72%, #0e0b09 100%); }}
  #stage.green {{ background:#00b140; }}

  #view {{
    max-width:100%; max-height:100%; width:auto; height:94%;
    object-fit:contain; pointer-events:none; transform-origin:50% 55%;
    image-rendering:auto;
  }}
  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(15,18,24,0.86);
    border:1px solid #3d4455; border-radius:8px; padding:5px 11px;
    font-size:13px; font-weight:700; color:var(--diy); pointer-events:none; backdrop-filter:blur(6px);
  }}
  #resbadge {{
    position:absolute; top:12px; right:14px; background:rgba(15,18,24,0.80);
    border:1px solid #343a48; border-radius:8px; padding:4px 10px;
    font-size:12px; color:var(--dim); pointer-events:none; font-variant-numeric:tabular-nums;
  }}
  #draghint {{
    position:absolute; bottom:10px; right:14px; background:rgba(15,18,24,0.80);
    border-radius:6px; padding:4px 10px; font-size:12px; color:var(--dim); pointer-events:none;
  }}

  .row {{
    display:flex; flex-wrap:wrap; gap:9px; align-items:center; justify-content:center;
    width:min(100%, 840px); background:var(--panel); border:1px solid #2b3140;
    border-radius:11px; padding:10px 14px;
  }}
  input[type=range] {{ accent-color:var(--diy); cursor:pointer; }}
  button.ctrl {{
    background:var(--diy); color:#1a1204; border:0; border-radius:7px;
    padding:7px 12px; font:inherit; font-weight:800; cursor:pointer;
  }}
  button.step {{ background:var(--panel2); color:var(--ink); font-weight:700; padding:7px 10px; }}
  button.laugh {{ background:var(--red); color:#fff; border:2px solid var(--diy); }}
  button.spin {{ background:var(--accent); color:#072a42; }}
  button.alt {{ background:#343b4b; color:var(--ink); font-weight:600; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; font-weight:600; }}
  #info {{ color:var(--ink); min-width:14ch; text-align:right; font-variant-numeric:tabular-nums; font-weight:700; font-size:13px; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px;
    width:min(100%, 840px);
  }}
  @media (max-width:700px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid #2b3140;
    border-radius:8px; display:flex; flex-direction:column; align-items:center;
    gap:2px; overflow:hidden; color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--diy); color:var(--diy); background:#292618; }}
  #strip img {{ width:100%; aspect-ratio:720/780; object-fit:contain; display:block; background:repeating-conic-gradient(#262a34 0% 25%, #1d2028 0% 50%) 0 0/12px 12px; border-radius:4px; }}

  #gridInspector {{
    display:none; width:min(100%, 1120px); flex-direction:column; gap:16px;
  }}
  .gridTitle {{ font-size:16px; font-weight:800; color:var(--diy); margin:6px 0 2px; }}
  .sheetGrid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:8px;
  }}
  .cellCard {{
    background:repeating-conic-gradient(#2a2e39 0% 25%, #1e222b 0% 50%) 0 0/16px 16px;
    border:1px solid #343b4b; border-radius:9px; padding:6px;
    display:flex; flex-direction:column; align-items:center; cursor:pointer; transition:0.12s;
  }}
  .cellCard:hover {{ border-color:var(--diy); transform:translateY(-2px); }}
  .cellCard img {{ width:100%; aspect-ratio:720/780; object-fit:contain; }}
  .cellCard span {{
    margin-top:4px; font-size:11px; font-weight:700; color:var(--ink);
    background:rgba(15,18,24,0.82); padding:2px 8px; border-radius:4px;
  }}
  p.hint {{ color:var(--dim); margin:0; font-size:12.5px; text-align:center; }}
</style>
</head>
<body>
  <header>
    <h1><span class="diy-logo">MR. D.I.Y.</span> Rob's Full-Body Dancing Sprite Inspector</h1>
    <div class="tabs">
      <button id="tabHero" class="active">16-Frame Full-Body Dance</button>
      <button id="tab360">360&deg; 8-Angle Turnaround</button>
      <button id="tabGrid">Inspect All 64 Frames (Grid)</button>
    </div>
  </header>

  <div id="stage" class="checker-dark">
    <div id="badge">Hero MR. D.I.Y. Dance (Full Legs &amp; Shoes)</div>
    <div id="resbadge">720&times;780 RGBA &bull; Zoom 1.00&times;</div>
    <img id="view" alt="Rob MR. D.I.Y. sprite">
    <div id="draghint">&leftrightarrow; Drag to scrub &bull; Scroll wheel to zoom</div>
  </div>

  <div class="row" id="controlsRow">
    <button class="ctrl step" id="prevBtn" title="Previous frame">&larr;</button>
    <button class="ctrl" id="play">Pause</button>
    <button class="ctrl step" id="nextBtn" title="Next frame">&rarr;</button>
    <button class="ctrl laugh" id="laughBtn">&#x1F50A; Play Rob's Laugh</button>
    <button class="ctrl spin" id="orbit" style="display:none">Auto-Spin 360&deg;: ON</button>
    <label id="scrubWrap">Frame <input id="scrub" type="range" min="0" max="15" value="0" style="width:120px"></label>
    <label id="angWrap" style="display:none">Angle <input id="ang" type="range" min="0" max="7" value="0" style="width:110px"></label>
    <label>FPS <input id="fps" type="range" min="2" max="24" value="13" style="width:82px"><span id="fpsVal">13</span></label>
    <label>Zoom <input id="zoom" type="range" min="50" max="250" value="100" style="width:82px"></label>
    <button class="ctrl alt" id="resetZoom">1&times;</button>
    <button class="ctrl alt" id="bgbtn">BG: Dark Checker</button>
    <span id="info">Frame 0/15</span>
  </div>

  <p class="hint" id="hintText"><b>Space</b> play/pause &bull; <b>Left/Right</b> step frames (or rotate 360&deg;) &bull; <b>Scroll wheel</b> zoom in on legs/shoes/face &bull; 100% self-contained single HTML file</p>
  <div id="strip"></div>

  <div id="gridInspector">
    <div>
      <div class="gridTitle">16-Frame Full-Body Hero Dance (Click any frame to inspect zoomed)</div>
      <div class="sheetGrid" id="heroGrid"></div>
    </div>
    <div>
      <div class="gridTitle">8-Direction &times; 6-Frame 360&deg; Turnaround (48 Frames — Click any to inspect)</div>
      <div class="sheetGrid" id="dirGrid"></div>
    </div>
  </div>

  <audio id="laughAudio" src="{audio_uri}" preload="auto"></audio>

<script>
const HERO = {json.dumps(hero_uris)};
const DIRS_DATA = {json.dumps(dir_uris)};
const HERO_N = HERO.length, DIRS = 8, DIR_N = 6;
const LABELS = ["0° Front", "45° Front-Left", "90° Left Side", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Side", "315° Front-Right"];

const view = document.getElementById("view"), badge = document.getElementById("badge"),
      resbadge = document.getElementById("resbadge"), draghint = document.getElementById("draghint"),
      info = document.getElementById("info"), playBtn = document.getElementById("play"),
      prevBtn = document.getElementById("prevBtn"), nextBtn = document.getElementById("nextBtn"),
      laughBtn = document.getElementById("laughBtn"), orbitBtn = document.getElementById("orbit"),
      scrubEl = document.getElementById("scrub"), scrubWrap = document.getElementById("scrubWrap"),
      angEl = document.getElementById("ang"), angWrap = document.getElementById("angWrap"),
      fpsEl = document.getElementById("fps"), fpsVal = document.getElementById("fpsVal"),
      zoomEl = document.getElementById("zoom"), resetZoom = document.getElementById("resetZoom"),
      stage = document.getElementById("stage"), strip = document.getElementById("strip"),
      controlsRow = document.getElementById("controlsRow"), gridInspector = document.getElementById("gridInspector"),
      bgbtn = document.getElementById("bgbtn"), tabHero = document.getElementById("tabHero"),
      tab360 = document.getElementById("tab360"), tabGrid = document.getElementById("tabGrid"),
      audio = document.getElementById("laughAudio");

let mode = "hero", curHero = 0, curDir = 0, curDirF = 0, running = true, autoSpin = true;
let lastStep = 0, lastSpin = 0, laughPlaying = false;
let zoom = 1.0, panX = 0, panY = 0;

const bgs = ["checker-dark", "checker-light", "white", "store", "quake", "green"];
const bgNames = ["Dark Checker", "Light Checker", "Pure White", "Storefront Warm", "Quake Dungeon", "Chroma Green"];
let bgi = 0;

let thumbs = [], thumbImgs = [];
function rebuildStrip() {{
  strip.innerHTML = ""; thumbs = []; thumbImgs = [];
  if (mode === "hero") {{
    for (let f = 0; f < HERO_N; f++) {{
      const b = document.createElement("button");
      const im = document.createElement("img"); im.src = HERO[f];
      const sp = document.createElement("span"); sp.textContent = "#" + String(f).padStart(2, "0");
      b.appendChild(im); b.appendChild(sp);
      b.onclick = () => {{ running = false; curHero = f; syncUI(); render(); }};
      strip.appendChild(b); thumbs.push(b); thumbImgs.push(im);
    }}
  }} else if (mode === "360") {{
    for (let d = 0; d < DIRS; d++) {{
      const b = document.createElement("button");
      const im = document.createElement("img"); im.src = DIRS_DATA[d][curDirF];
      const sp = document.createElement("span"); sp.textContent = (d * 45) + "°";
      b.appendChild(im); b.appendChild(sp);
      b.onclick = () => {{ autoSpin = false; curDir = d; syncUI(); render(); }};
      strip.appendChild(b); thumbs.push(b); thumbImgs.push(im);
    }}
  }}
}}

function buildInspectorGrids() {{
  const hg = document.getElementById("heroGrid");
  HERO.forEach((uri, f) => {{
    const c = document.createElement("div"); c.className = "cellCard";
    c.innerHTML = `<img src="${{uri}}"><span>Hero #${{String(f).padStart(2, "0")}}</span>`;
    c.onclick = () => {{ mode = "hero"; running = false; curHero = f; rebuildStrip(); syncUI(); render(); window.scrollTo({{top:0, behavior:"smooth"}}); }};
    hg.appendChild(c);
  }});
  const dg = document.getElementById("dirGrid");
  for (let d = 0; d < DIRS; d++) {{
    for (let f = 0; f < DIR_N; f++) {{
      const c = document.createElement("div"); c.className = "cellCard";
      c.innerHTML = `<img src="${{DIRS_DATA[d][f]}}"><span>${{d * 45}}° • f${{f}}</span>`;
      c.onclick = () => {{ mode = "360"; running = false; autoSpin = false; curDir = d; curDirF = f; rebuildStrip(); syncUI(); render(); window.scrollTo({{top:0, behavior:"smooth"}}); }};
      dg.appendChild(c);
    }}
  }}
}}

function applyTransform() {{
  view.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`;
  resbadge.textContent = `720×780 RGBA • Zoom ${{zoom.toFixed(2)}}×`;
}}

function render() {{
  if (mode === "grid") return;
  if (mode === "hero") {{
    curHero = ((curHero % HERO_N) + HERO_N) % HERO_N;
    view.src = HERO[curHero];
    badge.textContent = "Hero MR. D.I.Y. Dance (Full Legs & Shoes)";
    draghint.textContent = zoom > 1.05 ? "↔ Drag to pan • Scroll to zoom" : "↔ Drag to scrub frames • Scroll to zoom";
    scrubEl.value = curHero;
    info.textContent = `Frame ${{curHero}}/${{HERO_N - 1}}`;
    thumbs.forEach((t, k) => t.classList.toggle("on", k === curHero));
  }} else {{
    curDir = ((curDir % DIRS) + DIRS) % DIRS;
    curDirF = ((curDirF % DIR_N) + DIR_N) % DIR_N;
    view.src = DIRS_DATA[curDir][curDirF];
    badge.textContent = LABELS[curDir];
    draghint.textContent = zoom > 1.05 ? "↔ Drag to pan • Scroll to zoom" : "↔ Drag anywhere to spin 360°";
    angEl.value = curDir;
    info.textContent = `${{curDir * 45}}° • Frame ${{curDirF}}/${{DIR_N - 1}}`;
    thumbs.forEach((t, k) => t.classList.toggle("on", k === curDir));
    thumbImgs.forEach((im, k) => {{ im.src = DIRS_DATA[k][curDirF]; }});
  }}
  applyTransform();
}}

function syncUI() {{
  tabHero.classList.toggle("active", mode === "hero");
  tab360.classList.toggle("active", mode === "360");
  tabGrid.classList.toggle("active", mode === "grid");
  const isGrid = mode === "grid";
  stage.style.display = isGrid ? "none" : "flex";
  controlsRow.style.display = isGrid ? "none" : "flex";
  strip.style.display = isGrid ? "none" : "grid";
  gridInspector.style.display = isGrid ? "flex" : "none";
  orbitBtn.style.display = mode === "360" ? "" : "none";
  angWrap.style.display = mode === "360" ? "" : "none";
  scrubWrap.style.display = mode === "hero" ? "" : "none";
  strip.style.gridTemplateColumns = mode === "hero" ? "repeat(8, 1fr)" : "repeat(8, 1fr)";
  playBtn.textContent = running ? "Pause" : "Play";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  orbitBtn.className = "ctrl " + (autoSpin ? "spin" : "alt");
}}

tabHero.onclick = () => {{ mode = "hero"; rebuildStrip(); syncUI(); render(); }};
tab360.onclick = () => {{ mode = "360"; rebuildStrip(); syncUI(); render(); }};
tabGrid.onclick = () => {{ mode = "grid"; syncUI(); }};
playBtn.onclick = () => {{ running = !running; syncUI(); }};
prevBtn.onclick = () => {{ running = false; if (mode === "hero") curHero--; else curDirF--; syncUI(); render(); }};
nextBtn.onclick = () => {{ running = false; if (mode === "hero") curHero++; else curDirF++; syncUI(); render(); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncUI(); }};
scrubEl.oninput = () => {{ running = false; curHero = +scrubEl.value; syncUI(); render(); }};
angEl.oninput = () => {{ autoSpin = false; curDir = +angEl.value; syncUI(); render(); }};
fpsEl.oninput = () => {{ fpsVal.textContent = fpsEl.value; }};
zoomEl.oninput = () => {{ zoom = (+zoomEl.value) / 100; if (zoom <= 1.02) {{ panX = 0; panY = 0; }} render(); }};
resetZoom.onclick = () => {{ zoom = 1.0; panX = 0; panY = 0; zoomEl.value = 100; render(); }};

bgbtn.onclick = () => {{
  stage.classList.remove(bgs[bgi]);
  bgi = (bgi + 1) % bgs.length;
  stage.classList.add(bgs[bgi]);
  bgbtn.textContent = "BG: " + bgNames[bgi];
}};

laughBtn.onclick = () => {{
  laughPlaying = !laughPlaying;
  audio.loop = laughPlaying;
  if (laughPlaying) {{ audio.currentTime = 0; audio.play(); laughBtn.textContent = "🔇 Stop Laugh"; }}
  else {{ audio.pause(); laughBtn.textContent = "🔊 Play Rob's Laugh"; }}
}};

stage.addEventListener("wheel", e => {{
  e.preventDefault();
  zoom = Math.min(2.5, Math.max(0.5, zoom * (e.deltaY < 0 ? 1.12 : 0.89)));
  if (zoom <= 1.02) {{ panX = 0; panY = 0; }}
  zoomEl.value = Math.round(zoom * 100);
  render();
}}, {{ passive:false }});

let dragX = null, dragY = null, startVal = 0, startPanX = 0, startPanY = 0;
stage.addEventListener("pointerdown", e => {{
  dragX = e.clientX; dragY = e.clientY;
  startPanX = panX; startPanY = panY;
  startVal = mode === "hero" ? curHero : curDir;
  if (zoom <= 1.05) {{
    if (mode === "360") autoSpin = false; else running = false;
    syncUI();
  }}
  stage.classList.add("drag");
  stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener("pointermove", e => {{
  if (dragX === null) return;
  if (zoom > 1.05) {{
    panX = startPanX + (e.clientX - dragX);
    panY = startPanY + (e.clientY - dragY);
    applyTransform();
  }} else {{
    const steps = Math.round((e.clientX - dragX) / 32);
    if (mode === "hero") curHero = startVal + steps;
    else curDir = startVal - steps;
    render();
  }}
}});
const endDrag = () => {{ dragX = null; stage.classList.remove("drag"); }};
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

addEventListener("keydown", e => {{
  if (mode === "grid") return;
  if (e.code === "Space") {{ e.preventDefault(); running = !running; syncUI(); }}
  else if (e.code === "ArrowRight") {{ e.preventDefault(); if (mode === "hero") {{ running = false; curHero++; }} else {{ autoSpin = false; curDir++; }} syncUI(); render(); }}
  else if (e.code === "ArrowLeft")  {{ e.preventDefault(); if (mode === "hero") {{ running = false; curHero--; }} else {{ autoSpin = false; curDir--; }} syncUI(); render(); }}
}});

function tick(t) {{
  const interval = 1000 / (+fpsEl.value);
  let dirty = false;
  if (running && mode !== "grid" && t - lastStep > interval) {{
    lastStep = t;
    if (mode === "hero") curHero = (curHero + 1) % HERO_N;
    else curDirF = (curDirF + 1) % DIR_N;
    dirty = true;
  }}
  if (mode === "360" && autoSpin && t - lastSpin > interval * 3.0) {{
    lastSpin = t;
    curDir = (curDir + 1) % DIRS;
    dirty = true;
  }}
  if (dirty) render();
  requestAnimationFrame(tick);
}}

buildInspectorGrids();
rebuildStrip();
syncUI();
render();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    sz_mb = os.path.getsize(OUT_HTML) / (1024 * 1024)
    print(f"Wrote self-contained HTML: {OUT_HTML} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    build_self_contained_html()
