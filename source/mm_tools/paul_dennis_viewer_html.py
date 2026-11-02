"""HTML viewer generators for Paul ('Screaming Paul') and Dennis ('Reading for 30 Years')
character sprite packs in BakersfieldQuake."""


def build_character_viewer_html(
    char_key: str,
    title: str,
    subtitle: str,
    action_tab_label: str,
    action_prefix: str,
    n_dirs: int,
    n_run: int,
    n_action: int,
    canvas_w: int,
    canvas_h: int,
    ground_y: int,
    spr_w: int,
    spr_h: int,
    accent: str = "#4ade80",
) -> str:
    ground_pct = round(100.0 * ground_y / max(1, canvas_h), 3)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — 360° Quake Character Sprite</title>
<style>
  :root {{
    --bg:#12141a; --panel:#1d212b; --panel2:#262b38; --ink:#f1f5f9; --dim:#94a3b8;
    --accent:{accent}; --accent2:#38bdf8; --warn:#fbbf24;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:16px 16px 36px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:900px; }}
  h1 {{ font-size:21px; margin:0 0 4px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13px; margin:0; }}
  .tabs {{
    display:flex; flex-wrap:wrap; gap:8px; justify-content:center;
    width:min(100%, 880px); background:var(--panel); border:1px solid #2e3444;
    border-radius:12px; padding:8px;
  }}
  .tab {{
    flex:1 1 180px; padding:9px 12px; border-radius:8px; border:1.5px solid #32394a;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:13px;
    cursor:pointer; transition:all 0.12s ease; text-align:center;
  }}
  .tab:hover {{ border-color:#525d78; }}
  .tab.on {{ background:#16352a; border-color:var(--accent); color:#bbf7d0; box-shadow:0 0 14px rgba(74,222,128,0.18); }}

  #stage {{
    width:min(100%, 880px); height:min(62vh, 520px); min-height:360px;
    border-radius:14px; border:1px solid #343b4d; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker {{ background:repeating-conic-gradient(#282c36 0% 25%, #1e222b 0% 50%) 0 0/24px 24px; }}
  #stage.quake   {{ background:radial-gradient(circle at 50% 68%, #3f2e21 0%, #1d1510 70%, #0d0a08 100%); }}
  #stage.slate   {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0f172a 85%); }}
  #stage.light   {{ background:#cbd5e1; }}

  #wrap {{
    position:relative; height:92%; aspect-ratio:{canvas_w}/{canvas_h};
    display:flex; align-items:center; justify-content:center;
  }}
  #view {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  #view.pixel {{ image-rendering:pixelated; }}

  #reticle {{ position:absolute; inset:0; pointer-events:none; display:none; }}
  #reticle.on {{ display:block; }}
  .gline {{ position:absolute; left:4%; right:4%; top:{ground_pct}%; border-top:1.5px dashed rgba(251,191,36,0.85); }}
  .aline {{ position:absolute; top:4%; bottom:2%; left:50%; border-left:1.5px dashed rgba(56,189,248,0.65); }}
  .odot  {{ position:absolute; left:50%; top:{ground_pct}%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--warn); box-shadow:0 0 0 2px #0f172a; }}

  #badge {{
    position:absolute; top:12px; left:14px; background:rgba(12,15,22,0.88);
    border:1px solid #3c4458; border-radius:8px; padding:6px 12px;
    font-size:13px; font-weight:800; color:var(--accent); pointer-events:none; z-index:5;
  }}
  #meta {{
    position:absolute; top:12px; right:14px; background:rgba(12,15,22,0.84);
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
    width:min(100%, 880px); background:var(--panel); border:1px solid #2e3444;
    border-radius:10px; padding:10px 14px;
  }}
  button.ctrl {{
    background:var(--accent); color:#0f172a; border:0; border-radius:6px;
    padding:7px 13px; font:inherit; font-weight:700; cursor:pointer;
  }}
  button.ctrl.spin {{ background:var(--accent2); color:#082f49; }}
  button.ctrl.alt  {{ background:#333a4b; color:var(--ink); font-weight:600; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  #strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 880px);
  }}
  @media (max-width:700px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{
    padding:4px 4px 3px; background:var(--panel); border:2px solid transparent;
    border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px;
    color:var(--dim); font-size:11px; font-weight:700; cursor:pointer;
  }}
  #strip button.on {{ border-color:var(--accent); color:var(--ink); background:#272d3b; }}
  #strip img {{ width:100%; aspect-ratio:{canvas_w}/{canvas_h}; object-fit:contain; display:block; }}
  p.hint {{ color:var(--dim); margin:0; font-size:12.5px; text-align:center; }}
</style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p class="sub">{subtitle}</p>
  </header>

  <div class="tabs">
    <button class="tab on" data-mode="run">🏃 360° Run Cycle (8×{n_run}f)</button>
    <button class="tab" data-mode="idle">🧍 360° Standing Idle (8 Angles)</button>
    <button class="tab" data-mode="action">{action_tab_label}</button>
    <button class="tab" data-mode="spr32">🕹️ Quake .SPR32 ({spr_w}×{spr_h} · 56f)</button>
  </div>

  <div id="stage" class="checker">
    <div id="badge">0° Front</div>
    <div id="meta">Frame 0/{n_run - 1}</div>
    <div id="wrap">
      <img id="view" alt="sprite frame">
      <div id="reticle">
        <div class="gline"></div>
        <div class="aline"></div>
        <div class="odot"></div>
      </div>
    </div>
    <div id="draghint">↔ Drag horizontally to spin 360°</div>
  </div>

  <div class="row">
    <button class="ctrl" id="play">Pause</button>
    <button class="ctrl spin" id="orbit">Auto-Spin 360°: ON</button>
    <label>Angle <input id="ang" type="range" min="0" max="{n_dirs - 1}" value="0" style="width:120px"></label>
    <label>FPS <input id="fps" type="range" min="4" max="20" value="11" style="width:90px"></label>
    <button class="ctrl alt" id="origbtn">Origin: OFF</button>
    <button class="ctrl alt" id="bgbtn">BG: Checker</button>
  </div>

  <p class="hint">Drag left/right on stage or press <b>Left/Right Arrows</b> to orbit 360° &bull; <b>Up/Down Arrows</b> step frames &bull; <b>Space</b> pauses</p>
  <div id="strip"></div>

<script>
const DIRS = {n_dirs}, N_RUN = {n_run}, N_ACT = {n_action};
const LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];
const KEY = "{char_key}", ACT_PREFIX = "{action_prefix}";

const runSrc  = (d, f) => `${{KEY}}_d${{d}}_f${{f}}.png`;
const idleSrc = (d)    => `${{KEY}}_idle_d${{d}}.png`;
const actSrc  = (f)    => `${{ACT_PREFIX}}_${{String(f).padStart(2, "0")}}.png`;
const sprSrc  = (idx)  => `spr32/f_${{String(idx).padStart(2, "0")}}.png`;

let mode = "run", curDir = 0, curFrame = 0, playing = true, autoSpin = true;
let showOrigin = false, bgi = 0;
const bgs = ["checker", "quake", "slate", "light"], bgNames = ["Checker", "Quake Dungeon", "Dark Slate", "Light"];
let lastFrameT = 0, lastSpinT = 0;

const view = document.getElementById("view"), badge = document.getElementById("badge"),
      meta = document.getElementById("meta"), stage = document.getElementById("stage"),
      playBtn = document.getElementById("play"), orbitBtn = document.getElementById("orbit"),
      angEl = document.getElementById("ang"), fpsEl = document.getElementById("fps"),
      origBtn = document.getElementById("origbtn"), bgBtn = document.getElementById("bgbtn"),
      reticle = document.getElementById("reticle"), strip = document.getElementById("strip");

// Preload images
for (let d = 0; d < DIRS; d++) {{
  new Image().src = idleSrc(d);
  for (let f = 0; f < N_RUN; f++) new Image().src = runSrc(d, f);
}}
for (let f = 0; f < N_ACT; f++) new Image().src = actSrc(f);

const thumbs = [], thumbImgs = [];
for (let d = 0; d < DIRS; d++) {{
  const b = document.createElement("button");
  const im = document.createElement("img");
  im.src = runSrc(d, 0);
  const sp = document.createElement("span");
  sp.textContent = (d * 45) + "°";
  b.appendChild(im); b.appendChild(sp);
  b.onclick = () => {{ autoSpin = false; syncControls(); render(d, curFrame); }};
  strip.appendChild(b);
  thumbs.push(b); thumbImgs.push(im);
}}

function frameCount() {{
  if (mode === "idle") return 1;
  if (mode === "action") return N_ACT;
  if (mode === "spr32") return 6;
  return N_RUN;
}}

function render(d, f) {{
  curDir = ((d % DIRS) + DIRS) % DIRS;
  const nf = frameCount();
  curFrame = ((f % nf) + nf) % nf;
  angEl.value = curDir;

  view.classList.toggle("pixel", mode === "spr32");
  if (mode === "idle") {{
    view.src = idleSrc(curDir);
    badge.textContent = LABELS[curDir] + " · Idle";
    meta.textContent = "progs/fr_" + KEY + ".spr32 [frame " + curDir + "]";
    thumbImgs.forEach((im, k) => {{ im.src = idleSrc(k); }});
  }} else if (mode === "action") {{
    view.src = actSrc(curFrame);
    badge.textContent = "Signature Expression Sequence";
    meta.textContent = "Frame " + curFrame + "/" + (N_ACT - 1);
    thumbImgs.forEach((im, k) => {{ im.src = idleSrc(k); }});
  }} else if (mode === "spr32") {{
    const sidx = 8 + curDir * 6 + curFrame;
    view.src = sprSrc(sidx);
    badge.textContent = LABELS[curDir] + " · In-Game SPR32";
    meta.textContent = "SPR32 #" + sidx + " (run " + curFrame + "/5)";
    thumbImgs.forEach((im, k) => {{ im.src = sprSrc(8 + k * 6 + curFrame); }});
  }} else {{
    view.src = runSrc(curDir, curFrame);
    badge.textContent = LABELS[curDir] + " · Running";
    meta.textContent = "Frame " + curFrame + "/" + (N_RUN - 1);
    thumbImgs.forEach((im, k) => {{ im.src = runSrc(k, curFrame); }});
  }}
  thumbs.forEach((t, k) => t.classList.toggle("on", k === curDir));
}}

function syncControls() {{
  playBtn.textContent = playing ? "Pause" : "Play";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  orbitBtn.className = "ctrl " + (autoSpin ? "spin" : "alt");
  origBtn.textContent = "Origin: " + (showOrigin ? "ON" : "OFF");
  reticle.classList.toggle("on", showOrigin);
}}

document.querySelectorAll(".tab").forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("on"));
    btn.classList.add("on");
    mode = btn.dataset.mode;
    curFrame = 0;
    render(curDir, 0);
  }};
}});

playBtn.onclick = () => {{ playing = !playing; syncControls(); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncControls(); }};
origBtn.onclick = () => {{ showOrigin = !showOrigin; syncControls(); }};
angEl.oninput = () => {{ autoSpin = false; syncControls(); render(+angEl.value, curFrame); }};
bgBtn.onclick = () => {{
  stage.classList.remove(bgs[bgi]);
  bgi = (bgi + 1) % bgs.length;
  stage.classList.add(bgs[bgi]);
  bgBtn.textContent = "BG: " + bgNames[bgi];
}};

addEventListener("keydown", e => {{
  if (e.code === "Space") {{ e.preventDefault(); playing = !playing; syncControls(); }}
  else if (e.code === "ArrowRight") {{ e.preventDefault(); autoSpin = false; syncControls(); render(curDir + 1, curFrame); }}
  else if (e.code === "ArrowLeft")  {{ e.preventDefault(); autoSpin = false; syncControls(); render(curDir - 1, curFrame); }}
  else if (e.code === "ArrowUp")    {{ e.preventDefault(); playing = false; syncControls(); render(curDir, curFrame + 1); }}
  else if (e.code === "ArrowDown")  {{ e.preventDefault(); playing = false; syncControls(); render(curDir, curFrame - 1); }}
}});

let dragX = null, dragStartDir = 0;
stage.addEventListener("pointerdown", e => {{
  dragX = e.clientX; dragStartDir = curDir; autoSpin = false; syncControls();
  stage.classList.add("drag"); stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener("pointermove", e => {{
  if (dragX === null) return;
  const steps = Math.round((e.clientX - dragX) / 36);
  render(dragStartDir - steps, curFrame);
}});
const endDrag = () => {{ dragX = null; stage.classList.remove("drag"); }};
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

function tick(t) {{
  const iv = 1000 / (+fpsEl.value);
  let nextD = curDir, nextF = curFrame, dirty = false;
  if (playing && frameCount() > 1 && t - lastFrameT > iv) {{
    lastFrameT = t; nextF = (curFrame + 1) % frameCount(); dirty = true;
  }}
  if (autoSpin && mode !== "action" && t - lastSpinT > iv * 3.2) {{
    lastSpinT = t; nextD = (curDir + 1) % DIRS; dirty = true;
  }}
  if (dirty) render(nextD, nextF);
  requestAnimationFrame(tick);
}}
syncControls();
render(0, 0);
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def build_combined_showcase_html(canvas_w: int, canvas_h: int) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Paul & Dennis — BakersfieldQuake Character Sprites</title>
<style>
  :root {{
    --bg:#0e1015; --panel:#191d26; --panel2:#232836; --ink:#f1f5f9; --dim:#94a3b8;
    --paul:#fb923c; --dennis:#38bdf8; --accent:#4ade80;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:14px;
    padding:18px 16px 44px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1080px; }}
  h1 {{ font-size:24px; margin:0 0 4px; font-weight:800; letter-spacing:-0.02em; }}
  .sub {{ color:var(--dim); font-size:13.5px; margin:0; }}

  .bar {{
    display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center;
    width:min(100%, 1080px); background:var(--panel); border:1px solid #2b3244;
    border-radius:12px; padding:10px 14px;
  }}
  button {{
    background:var(--panel2); color:var(--ink); border:1.5px solid #353e54;
    border-radius:8px; padding:7px 14px; font:inherit; font-weight:700; cursor:pointer;
  }}
  button.on {{ background:#163829; border-color:var(--accent); color:#bbf7d0; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:13px; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  .duo {{
    display:grid; grid-template-columns:1fr 1fr; gap:16px; width:min(100%, 1080px);
  }}
  @media (max-width:780px) {{ .duo {{ grid-template-columns:1fr; }} }}

  .card {{
    background:var(--panel); border:1px solid #2b3244; border-radius:14px;
    padding:14px; display:flex; flex-direction:column; gap:10px;
  }}
  .card-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px; }}
  .card-title {{ font-size:17px; font-weight:800; }}
  .card-title.paul {{ color:var(--paul); }}
  .card-title.dennis {{ color:var(--dennis); }}
  .card-file {{ font-family:ui-monospace, Consolas, monospace; font-size:12px; color:var(--dim); }}

  .stage {{
    width:100%; aspect-ratio:{canvas_w}/{canvas_h}; max-height:460px;
    border-radius:12px; border:1px solid #333b50; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    cursor:grab; user-select:none; touch-action:none;
  }}
  .stage.checker {{ background:repeating-conic-gradient(#272b35 0% 25%, #1d2029 0% 50%) 0 0/24px 24px; }}
  .stage.quake   {{ background:radial-gradient(circle at 50% 68%, #3f2e21 0%, #1d1510 70%, #0d0a08 100%); }}
  .stage.slate   {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0f172a 85%); }}
  .stage img {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  .stage img.pixel {{ image-rendering:pixelated; }}
  .pill {{
    position:absolute; top:10px; left:12px; background:rgba(12,15,22,0.86);
    border:1px solid #3c4458; border-radius:7px; padding:4px 10px;
    font-size:12px; font-weight:700; color:#e2e8f0; pointer-events:none;
  }}
  .links {{ display:flex; justify-content:space-between; font-size:12.5px; color:var(--dim); }}
  .links a {{ color:var(--accent); text-decoration:none; font-weight:700; }}
  .links a:hover {{ text-decoration:underline; }}

  .sheets {{
    width:min(100%, 1080px); display:grid; grid-template-columns:1fr 1fr; gap:16px;
  }}
  @media (max-width:780px) {{ .sheets {{ grid-template-columns:1fr; }} }}
  .sheet-box {{
    background:var(--panel); border:1px solid #2b3244; border-radius:14px; padding:12px;
  }}
  .sheet-box h3 {{ margin:0 0 8px; font-size:14px; color:var(--dim); }}
  .sheet-box img {{
    width:100%; height:auto; display:block; border-radius:8px;
    background:repeating-conic-gradient(#252932 0% 25%, #1b1e26 0% 50%) 0 0/18px 18px;
  }}
</style>
</head>
<body>
  <header>
    <h1>Paul &amp; Dennis — BakersfieldQuake Character Sprites</h1>
    <p class="sub">8-Direction 360° Idle &amp; Run Cycles &bull; Signature Video Expressions &bull; Ready-to-Spawn DarkPlaces <code>.SPR32</code> Assets</p>
  </header>

  <div class="bar">
    <button class="mode on" data-mode="run">🏃 360° Run Cycle</button>
    <button class="mode" data-mode="idle">🧍 360° Standing Idle</button>
    <button class="mode" data-mode="action">🎬 Signature Expression</button>
    <button class="mode" data-mode="spr32">🕹️ In-Game .SPR32 (56f)</button>
    <button id="play" class="on">Pause</button>
    <button id="spin" class="on">Auto-Spin: ON</button>
    <label>Angle <input id="ang" type="range" min="0" max="7" value="0" style="width:110px"></label>
    <label>FPS <input id="fps" type="range" min="4" max="20" value="11" style="width:85px"></label>
    <button id="bg">BG: Checker</button>
  </div>

  <div class="duo">
    <div class="card">
      <div class="card-head">
        <span class="card-title paul">PAUL — "PAAAAUUUUUL!"</span>
        <span class="card-file">progs/fr_paul.spr32</span>
      </div>
      <div class="stage checker" id="st-paul">
        <div class="pill" id="lbl-paul">0° Front</div>
        <img id="im-paul" alt="Paul sprite">
      </div>
      <div class="links">
        <span>8 Angles × 8 Run + 8 Idle + Scream</span>
        <a href="paul_sprite/index.html">Open Dedicated Paul Viewer →</a>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <span class="card-title dennis">DENNIS — "Reading For 30 Years"</span>
        <span class="card-file">progs/fr_dennis.spr32</span>
      </div>
      <div class="stage checker" id="st-dennis">
        <div class="pill" id="lbl-dennis">0° Front</div>
        <img id="im-dennis" alt="Dennis sprite">
      </div>
      <div class="links">
        <span>8 Angles × 8 Run + 8 Idle + Lecture</span>
        <a href="dennis_sprite/index.html">Open Dedicated Dennis Viewer →</a>
      </div>
    </div>
  </div>

  <div class="sheets">
    <div class="sheet-box">
      <h3>Paul 8×8 360° Run &amp; Scream Sheet (<code>paul_sprite/paul_360_sheet_8x8.png</code>)</h3>
      <img src="paul_sprite/paul_360_sheet_8x8.png" alt="Paul 8x8 Sprite Sheet">
    </div>
    <div class="sheet-box">
      <h3>Dennis 8×8 360° Suit Run Sheet (<code>dennis_sprite/dennis_360_sheet_8x8.png</code>)</h3>
      <img src="dennis_sprite/dennis_360_sheet_8x8.png" alt="Dennis 8x8 Sprite Sheet">
    </div>
  </div>

<script>
const LABELS = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"];
let mode = "run", dir = 0, frame = 0, playing = true, spin = true, bgi = 0;
const bgs = ["checker", "quake", "slate"], bgNames = ["Checker", "Quake Dungeon", "Dark Slate"];
let lastF = 0, lastS = 0;

const imP = document.getElementById("im-paul"), imD = document.getElementById("im-dennis");
const lbP = document.getElementById("lbl-paul"), lbD = document.getElementById("lbl-dennis");
const angEl = document.getElementById("ang"), fpsEl = document.getElementById("fps");
const playBtn = document.getElementById("play"), spinBtn = document.getElementById("spin"), bgBtn = document.getElementById("bg");

function nf() {{ return mode === "idle" ? 1 : (mode === "spr32" ? 6 : 8); }}

function update() {{
  dir = ((dir % 8) + 8) % 8;
  frame = ((frame % nf()) + nf()) % nf();
  angEl.value = dir;
  imP.classList.toggle("pixel", mode === "spr32");
  imD.classList.toggle("pixel", mode === "spr32");
  if (mode === "idle") {{
    imP.src = `paul_sprite/paul_idle_d${{dir}}.png`;
    imD.src = `dennis_sprite/dennis_idle_d${{dir}}.png`;
    lbP.textContent = lbD.textContent = LABELS[dir] + " · Idle";
  }} else if (mode === "action") {{
    const s = String(frame).padStart(2, "0");
    imP.src = `paul_sprite/paul_scream_${{s}}.png`;
    imD.src = `dennis_sprite/dennis_read_${{s}}.png`;
    lbP.textContent = `Scream ${{frame}}/7`;
    lbD.textContent = `Reading ${{frame}}/7`;
  }} else if (mode === "spr32") {{
    const idx = String(8 + dir * 6 + frame).padStart(2, "0");
    imP.src = `paul_sprite/spr32/f_${{idx}}.png`;
    imD.src = `dennis_sprite/spr32/f_${{idx}}.png`;
    lbP.textContent = lbD.textContent = LABELS[dir] + ` · SPR32 #${{8 + dir * 6 + frame}}`;
  }} else {{
    imP.src = `paul_sprite/paul_d${{dir}}_f${{frame}}.png`;
    imD.src = `dennis_sprite/dennis_d${{dir}}_f${{frame}}.png`;
    lbP.textContent = lbD.textContent = LABELS[dir] + ` · Frame ${{frame}}/7`;
  }}
}}

document.querySelectorAll(".mode").forEach(b => {{
  b.onclick = () => {{
    document.querySelectorAll(".mode").forEach(x => x.classList.remove("on"));
    b.classList.add("on"); mode = b.dataset.mode; frame = 0; update();
  }};
}});
playBtn.onclick = () => {{ playing = !playing; playBtn.classList.toggle("on", playing); playBtn.textContent = playing ? "Pause" : "Play"; }};
spinBtn.onclick = () => {{ spin = !spin; spinBtn.classList.toggle("on", spin); spinBtn.textContent = "Auto-Spin: " + (spin ? "ON" : "OFF"); }};
angEl.oninput = () => {{ spin = false; spinBtn.classList.remove("on"); spinBtn.textContent = "Auto-Spin: OFF"; dir = +angEl.value; update(); }};
bgBtn.onclick = () => {{
  document.querySelectorAll(".stage").forEach(s => s.classList.remove(bgs[bgi]));
  bgi = (bgi + 1) % bgs.length;
  document.querySelectorAll(".stage").forEach(s => s.classList.add(bgs[bgi]));
  bgBtn.textContent = "BG: " + bgNames[bgi];
}};

["st-paul", "st-dennis"].forEach(id => {{
  const el = document.getElementById(id);
  let dx = null, startD = 0;
  el.addEventListener("pointerdown", e => {{ dx = e.clientX; startD = dir; spin = false; spinBtn.classList.remove("on"); spinBtn.textContent = "Auto-Spin: OFF"; el.setPointerCapture(e.pointerId); }});
  el.addEventListener("pointermove", e => {{ if (dx === null) return; dir = startD - Math.round((e.clientX - dx) / 34); update(); }});
  const end = () => {{ dx = null; }};
  el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
}});

function tick(t) {{
  const iv = 1000 / (+fpsEl.value);
  let ch = false;
  if (playing && nf() > 1 && t - lastF > iv) {{ lastF = t; frame = (frame + 1) % nf(); ch = true; }}
  if (spin && mode !== "action" && t - lastS > iv * 3.2) {{ lastS = t; dir = (dir + 1) % 8; ch = true; }}
  if (ch) update();
  requestAnimationFrame(tick);
}}
update();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
