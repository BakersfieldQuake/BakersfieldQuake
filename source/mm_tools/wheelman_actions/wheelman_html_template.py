r"""Self-Contained Interactive 360° HTML Inspector Generator for Wheelman's 5 Quake Animations.

Packs each animation's (8 directions x N frames) into an embedded high-resolution RGBA WebP/PNG
atlas so the single standalone HTML file loads instantaneously with zero frame-swap flicker.
"""
import base64
import io
import json
import os
from PIL import Image


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WHEELMAN — 1700 Painting Character • 360° Quake Animation Suite</title>
<style>
  :root {
    --bg: #111318;
    --panel: #1b1f28;
    --panel2: #242936;
    --border: #32394a;
    --ink: #f1f4f9;
    --dim: #9aa3b5;
    --accent: #4ade80;
    --accent2: #38bdf8;
    --gold: #fbbf24;
    --crimson: #f87171;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: radial-gradient(circle at 50% 0%, #1d2230 0%, var(--bg) 65%);
    color: var(--ink);
    font: 14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    padding: 18px 16px 48px;
    min-height: 100vh;
  }
  header {
    width: min(100%, 1120px);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }
  .eyebrow {
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--gold);
    font-weight: 700;
  }
  h1 {
    font-size: clamp(20px, 2.6vw, 28px);
    margin: 0;
    font-weight: 800;
    letter-spacing: -0.02em;
  }
  .sub {
    color: var(--dim);
    font-size: 13px;
    margin: 0;
  }
  .url-box {
    margin-top: 4px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #0d1016;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 5px 10px;
    max-width: 100%;
    cursor: pointer;
    transition: border-color 0.15s;
  }
  .url-box:hover { border-color: var(--accent2); }
  .url-box code {
    color: var(--accent2);
    font-size: 12px;
    user-select: all;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .url-box span.cp {
    font-size: 11px;
    font-weight: 700;
    background: var(--panel2);
    color: var(--ink);
    padding: 2px 7px;
    border-radius: 5px;
    flex-shrink: 0;
  }

  /* Animation Selector Tabs */
  #anim-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    width: min(100%, 1120px);
  }
  .anim-tab {
    background: var(--panel);
    color: var(--ink);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 9px 14px;
    cursor: pointer;
    font: inherit;
    font-weight: 700;
    font-size: 13px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    transition: all 0.14s ease;
    min-width: 162px;
    flex: 1 1 162px;
  }
  .anim-tab:hover { border-color: var(--accent2); background: var(--panel2); }
  .anim-tab.active {
    border-color: var(--accent);
    background: linear-gradient(180deg, rgba(74,222,128,0.16), rgba(36,41,54,0.95));
    box-shadow: 0 0 0 1px rgba(74,222,128,0.35), 0 8px 22px rgba(0,0,0,0.35);
  }
  .anim-tab .t-num { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); }
  .anim-tab .t-title { font-size: 13.5px; color: var(--ink); }
  .anim-tab .t-sub { font-size: 11px; font-weight: 500; color: var(--dim); }

  /* Main Stage + Controls Layout */
  .main-grid {
    width: min(100%, 1120px);
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 14px;
    align-items: stretch;
  }
  @media (max-width: 900px) {
    .main-grid { grid-template-columns: 1fr; }
  }

  #stage {
    aspect-ratio: 1 / 1;
    max-height: 600px;
    width: 100%;
    border-radius: 14px;
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: grab;
    touch-action: none;
    user-select: none;
    box-shadow: 0 14px 36px rgba(0,0,0,0.45);
  }
  #stage.drag { cursor: grabbing; }
  #stage.quake {
    background:
      radial-gradient(ellipse at 50% 88%, rgba(92,62,38,0.55) 0%, rgba(28,20,14,0.0) 58%),
      radial-gradient(circle at 50% 42%, #3a2a1d 0%, #1b140f 68%, #0d0a08 100%);
  }
  #stage.gallery1700 {
    background:
      radial-gradient(ellipse at 50% 35%, #5c4630 0%, #2e2217 65%, #17110b 100%);
    box-shadow: inset 0 0 0 6px #785a32, inset 0 0 42px rgba(0,0,0,0.75);
  }
  #stage.checker {
    background: repeating-conic-gradient(#2a2e39 0% 25%, #1f232c 0% 50%) 0 0 / 24px 24px;
  }
  #stage.slate { background: #0f172a; }

  #hero-canvas {
    width: 100%;
    height: 100%;
    object-fit: contain;
    pointer-events: none;
  }

  .hud-pill {
    position: absolute;
    background: rgba(13, 16, 22, 0.86);
    border: 1px solid #363e50;
    border-radius: 8px;
    padding: 5px 11px;
    font-size: 12.5px;
    pointer-events: none;
    backdrop-filter: blur(6px);
  }
  #badge-tl { top: 12px; left: 12px; font-weight: 700; color: var(--accent); }
  #badge-tr { top: 12px; right: 12px; color: var(--dim); font-variant-numeric: tabular-nums; }
  #badge-bl { bottom: 12px; left: 12px; color: var(--gold); font-weight: 600; font-size: 12px; }
  #badge-br { bottom: 12px; right: 12px; color: var(--dim); font-size: 12px; }

  /* Side Panel: Simultaneous 5-Animation Live Preview Cards */
  .side-col {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .panel-box {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
  }
  .panel-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--accent2);
    margin: 0 0 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  #live-5-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
  }
  .mini-card {
    background: repeating-conic-gradient(#252934 0% 25%, #1c1f28 0% 50%) 0 0 / 16px 16px;
    border: 1.5px solid var(--border);
    border-radius: 9px;
    padding: 3px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: border-color 0.14s;
  }
  .mini-card:hover { border-color: var(--accent2); }
  .mini-card.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
  .mini-card canvas {
    width: 100%;
    max-width: 122px;
    aspect-ratio: 1 / 1;
    display: block;
  }
  .mini-card .mc-lbl {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--ink);
    text-align: center;
    padding: 2px 3px;
    line-height: 1.2;
  }
  .mini-card .mc-desc {
    font-size: 11px;
    color: var(--dim);
  }

  /* Controls Bar */
  .controls-bar {
    width: min(100%, 1120px);
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    justify-content: center;
  }
  button.ctrl {
    background: var(--accent);
    color: #0b1320;
    border: 0;
    border-radius: 7px;
    padding: 7px 13px;
    font: inherit;
    font-weight: 700;
    font-size: 13px;
    cursor: pointer;
  }
  button.ctrl.spin { background: var(--accent2); color: #062235; }
  button.ctrl.alt { background: var(--panel2); color: var(--ink); border: 1px solid var(--border); font-weight: 600; }
  button.ctrl.alt.on { border-color: var(--gold); color: var(--gold); }
  label.sl {
    color: var(--dim);
    font-size: 12.5px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-variant-numeric: tabular-nums;
  }
  input[type=range] { accent-color: var(--accent); cursor: pointer; }

  /* 8-Angle 360 Strip */
  #dir-strip {
    width: min(100%, 1120px);
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 7px;
  }
  @media (max-width: 720px) {
    #dir-strip { grid-template-columns: repeat(4, 1fr); }
  }
  .dir-btn {
    background: var(--panel);
    border: 2px solid var(--border);
    border-radius: 9px;
    padding: 4px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    color: var(--dim);
    font-size: 11px;
    font-weight: 700;
  }
  .dir-btn.on { border-color: var(--accent); color: var(--ink); background: var(--panel2); }
  .dir-btn canvas {
    width: 100%;
    aspect-ratio: 1 / 1;
    display: block;
    background: radial-gradient(circle at 50% 60%, #2a241e, #151318);
    border-radius: 5px;
  }

  /* Frame Sheet Matrix */
  details {
    width: min(100%, 1120px);
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 16px;
  }
  summary {
    cursor: pointer;
    font-weight: 700;
    color: var(--accent2);
    user-select: none;
  }
  #matrix-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 5px;
    margin-top: 12px;
  }
  .mat-cell {
    background: repeating-conic-gradient(#262a35 0% 25%, #1c1f28 0% 50%) 0 0 / 14px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px;
    text-align: center;
    cursor: pointer;
  }
  .mat-cell:hover { border-color: var(--accent); }
  .mat-cell canvas { width: 100%; aspect-ratio: 1 / 1; display: block; }
  .mat-cell span { font-size: 10px; color: var(--dim); font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
  <header>
    <div class="eyebrow">BakersfieldQuake &bull; 1700 Baroque Grotesque Painting Character &bull; DarkPlaces SPR32</div>
    <h1>WHEELMAN &mdash; Complete 360&deg; Realistic Animation Inspector</h1>
    <p class="sub">9 Full 360&deg; Animations (8 Directions Each &bull; 832 Total RGBA Frames) &bull; Full Bare Nudity &bull; <code>progs/wheelman_actions.spr32</code></p>
    <div class="url-box" id="copy-url" title="Click to copy full file URL">
      <code id="url-text">file:///G:/Quake/Combat/BakersfieldQuake/wheelman_animations.html</code>
      <span class="cp" id="cp-tag">Click to Copy URL</span>
    </div>
  </header>

  <div id="anim-tabs"></div>

  <div class="main-grid">
    <div id="stage" class="quake">
      <canvas id="hero-canvas" width="720" height="720"></canvas>
      <div class="hud-pill" id="badge-tl">1. Running w/ Stuck Bar &amp; Wheels</div>
      <div class="hud-pill" id="badge-tr">0&deg; Front &bull; Frame 0</div>
      <div class="hud-pill" id="badge-bl">SPR32 #0 &bull; Origin (-180, 332)</div>
      <div class="hud-pill" id="badge-br">&harr; Drag to Rotate 360&deg;</div>
    </div>

    <div class="side-col">
      <div class="panel-box">
        <div class="panel-title">
          <span>All 9 Animations Live @ <span id="sync-ang-lbl">0&deg; Front</span></span>
          <span style="color:var(--dim);font-weight:500;text-transform:none">Click any card</span>
        </div>
        <div id="live-5-grid"></div>
      </div>
      <div class="panel-box" style="font-size:12.5px;color:var(--dim);line-height:1.5">
        <strong style="color:var(--ink)" id="info-title">Animation Notes</strong>
        <div id="info-desc" style="margin-top:4px"></div>
      </div>
    </div>
  </div>

  <div class="controls-bar">
    <button class="ctrl" id="btn-play">Pause</button>
    <button class="ctrl spin" id="btn-orbit">Auto-Orbit 360&deg;: ON</button>
    <label class="sl">Angle <input id="sl-ang" type="range" min="0" max="7" value="0" style="width:105px"> <b id="lbl-ang">0&deg;</b></label>
    <label class="sl">Speed <input id="sl-fps" type="range" min="4" max="22" value="12" style="width:90px"> <b id="lbl-fps">12 FPS</b></label>
    <label class="sl">Zoom <input id="sl-zoom" type="range" min="85" max="200" value="105" style="width:85px"></label>
    <button class="ctrl alt" id="btn-origin">Origin Guide</button>
    <button class="ctrl alt" id="btn-bg">BG: Quake Dungeon</button>
  </div>

  <div id="dir-strip"></div>

  <details id="sheet-details">
    <summary>Inspect All Frames in Active Animation (8 Directions &times; Frame Cycle) &mdash; Click Any Frame to Freeze &amp; Inspect</summary>
    <div id="matrix-grid"></div>
  </details>

<script>
const ANIMS = __ANIMS_META_JSON__;
const ATLAS_URIS = __ATLAS_URIS_JSON__;
const CELL_W = __CELL_W__, CELL_H = __CELL_H__, GROUND_Y = __GROUND_Y__;
const DIRS = 8;
const DIR_LABELS = [
  "0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left",
  "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"
];
const BGS = ["quake", "gallery1700", "checker", "slate"];
const BG_NAMES = ["Quake Dungeon", "1700 Oil Gallery", "Alpha Checker", "Dark Slate"];

const atlasImgs = {};
let loadedCount = 0;

let curAnim = 0, curDir = 0, curTick = 0;
let playing = true, autoOrbit = true, showOrigin = false, bgIdx = 0;
let lastFrameTime = 0, lastOrbitTime = 0;

const heroCanvas = document.getElementById("hero-canvas");
const heroCtx = heroCanvas.getContext("2d");
const stage = document.getElementById("stage");
const tabsWrap = document.getElementById("anim-tabs");
const live5Grid = document.getElementById("live-5-grid");
const dirStrip = document.getElementById("dir-strip");
const matrixGrid = document.getElementById("matrix-grid");

// URL copy helper
document.getElementById("copy-url").onclick = () => {
  const txt = document.getElementById("url-text").textContent;
  navigator.clipboard?.writeText(txt);
  const tag = document.getElementById("cp-tag");
  tag.textContent = "Copied!";
  tag.style.background = "#4ade80";
  tag.style.color = "#08121e";
  setTimeout(() => { tag.textContent = "Click to Copy URL"; tag.style.background = ""; tag.style.color = ""; }, 1600);
};

// Build Tabs
const tabBtns = ANIMS.map((a, idx) => {
  const b = document.createElement("button");
  b.className = "anim-tab";
  b.innerHTML = `<span class="t-num">Anim ${idx + 1} &bull; 360&deg; (${a.n_frames}f &times; 8)</span>
                 <span class="t-title">${a.short_title}</span>
                 <span class="t-sub">${a.subtitle}</span>`;
  b.onclick = () => selectAnim(idx);
  tabsWrap.appendChild(b);
  return b;
});

// Build Live 9-Animation Simultaneous 3x3 Cards
const miniCards = ANIMS.map((a, idx) => {
  const card = document.createElement("div");
  card.className = "mini-card";
  const cv = document.createElement("canvas");
  cv.width = CELL_W; cv.height = CELL_H;
  const lblWrap = document.createElement("div");
  lblWrap.innerHTML = `<div class="mc-lbl">${idx + 1}. ${a.short_title}</div>`;
  card.appendChild(cv);
  card.appendChild(lblWrap);
  card.onclick = () => selectAnim(idx);
  live5Grid.appendChild(card);
  return { card, cv, ctx: cv.getContext("2d") };
});

// Build 8-Direction Strip
const dirThumbs = [];
for (let d = 0; d < DIRS; d++) {
  const btn = document.createElement("button");
  btn.className = "dir-btn";
  const cv = document.createElement("canvas");
  cv.width = 180; cv.height = 180;
  const sp = document.createElement("span");
  sp.textContent = DIR_LABELS[d];
  btn.appendChild(cv);
  btn.appendChild(sp);
  btn.onclick = () => { autoOrbit = false; curDir = d; syncUI(); renderAll(); };
  dirStrip.appendChild(btn);
  dirThumbs.push({ btn, cv, ctx: cv.getContext("2d") });
}

function drawFrameToCanvas(ctx, cw, ch, animIdx, dirIdx, frameIdx, zoom, withShadow, withOrigin) {
  ctx.clearRect(0, 0, cw, ch);
  const im = atlasImgs[ANIMS[animIdx].key];
  if (!im || !im.complete) return;

  const nf = ANIMS[animIdx].n_frames;
  const f = ((frameIdx % nf) + nf) % nf;
  const d = ((dirIdx % DIRS) + DIRS) % DIRS;

  const sx = f * CELL_W;
  const sy = d * CELL_H;

  const gyNorm = GROUND_Y / CELL_H;
  if (withShadow) {
    ctx.save();
    const shY = ch * (0.5 + (gyNorm - 0.5) * zoom);
    const grad = ctx.createRadialGradient(cw * 0.5, shY, cw * 0.02, cw * 0.5, shY, cw * 0.28 * zoom);
    grad.addColorStop(0, "rgba(0,0,0,0.52)");
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.scale(1, 0.24);
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cw * 0.5, shY / 0.24, cw * 0.28 * zoom, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // Scale around ground anchor (0.5, gyNorm)
  const dw = cw * zoom;
  const dh = ch * zoom;
  const ox = cw * 0.5 - dw * 0.5;
  const oy = ch * gyNorm - dh * gyNorm;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(im, sx, sy, CELL_W, CELL_H, ox, oy, dw, dh);

  if (withOrigin) {
    const gyPx = oy + dh * gyNorm;
    ctx.save();
    ctx.strokeStyle = "rgba(251,191,36,0.88)";
    ctx.lineWidth = 2;
    ctx.setLineDash([7, 5]);
    ctx.beginPath(); ctx.moveTo(cw * 0.06, gyPx); ctx.lineTo(cw * 0.94, gyPx); ctx.stroke();
    ctx.strokeStyle = "rgba(56,189,248,0.75)";
    ctx.beginPath(); ctx.moveTo(cw * 0.5, ch * 0.05); ctx.lineTo(cw * 0.5, ch * 0.96); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#fbbf24";
    ctx.beginPath(); ctx.arc(cw * 0.5, gyPx, 6, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
}

function rebuildMatrix() {
  matrixGrid.innerHTML = "";
  const a = ANIMS[curAnim];
  const im = atlasImgs[a.key];
  if (!im || !im.complete) return;
  for (let f = 0; f < a.n_frames; f++) {
    for (let d = 0; d < DIRS; d++) {
      const cell = document.createElement("div");
      cell.className = "mat-cell";
      const cv = document.createElement("canvas");
      cv.width = 140; cv.height = 140;
      drawFrameToCanvas(cv.getContext("2d"), 140, 140, curAnim, d, f, 1.0, false, false);
      const sp = document.createElement("span");
      const sprIdx = a.spr_base + d * a.n_frames + f;
      sp.textContent = `d${d}:f${f} (#${sprIdx})`;
      cell.appendChild(cv);
      cell.appendChild(sp);
      cell.onclick = () => {
        playing = false; autoOrbit = false; curDir = d; curTick = f;
        syncUI(); renderAll();
        window.scrollTo({ top: 0, behavior: "smooth" });
      };
      matrixGrid.appendChild(cell);
    }
  }
}

function selectAnim(idx) {
  curAnim = idx;
  curTick = 0;
  syncUI();
  rebuildMatrix();
  renderAll();
}

function syncUI() {
  const a = ANIMS[curAnim];
  tabBtns.forEach((b, i) => b.classList.toggle("active", i === curAnim));
  miniCards.forEach((m, i) => m.card.classList.toggle("active", i === curAnim));
  dirThumbs.forEach((t, d) => t.btn.classList.toggle("on", d === curDir));

  document.getElementById("btn-play").textContent = playing ? "Pause" : "Play";
  const ob = document.getElementById("btn-orbit");
  ob.textContent = "Auto-Orbit 360°: " + (autoOrbit ? "ON" : "OFF");
  ob.className = "ctrl " + (autoOrbit ? "spin" : "alt");
  document.getElementById("btn-origin").classList.toggle("on", showOrigin);
  document.getElementById("sl-ang").value = curDir;
  document.getElementById("lbl-ang").textContent = (curDir * 45) + "°";
  document.getElementById("sync-ang-lbl").textContent = DIR_LABELS[curDir];
  document.getElementById("info-title").textContent = `${curAnim + 1}. ${a.title}`;
  document.getElementById("info-desc").textContent = a.description;
}

function renderAll() {
  const a = ANIMS[curAnim];
  const f = curTick % a.n_frames;
  const zoom = (+document.getElementById("sl-zoom").value) / 100.0;
  drawFrameToCanvas(heroCtx, heroCanvas.width, heroCanvas.height, curAnim, curDir, f, zoom, bgIdx <= 1, showOrigin);

  const sprIdx = a.spr_base + curDir * a.n_frames + f;
  document.getElementById("badge-tl").textContent = `${curAnim + 1}. ${a.short_title}`;
  document.getElementById("badge-tr").textContent = `${DIR_LABELS[curDir]} • Frame ${f + 1}/${a.n_frames}`;
  document.getElementById("badge-bl").textContent = `SPR32 #${sprIdx} • ${CELL_W}×${CELL_H} • Origin (-${CELL_W/2}, ${GROUND_Y})`;

  miniCards.forEach((m, idx) => {
    const mf = curTick % ANIMS[idx].n_frames;
    drawFrameToCanvas(m.ctx, m.cv.width, m.cv.height, idx, curDir, mf, 1.02, false, false);
  });

  dirThumbs.forEach((t, d) => {
    drawFrameToCanvas(t.ctx, t.cv.width, t.cv.height, curAnim, d, f, 1.02, false, false);
  });
}

// Controls
document.getElementById("btn-play").onclick = () => { playing = !playing; syncUI(); };
document.getElementById("btn-orbit").onclick = () => { autoOrbit = !autoOrbit; syncUI(); };
document.getElementById("btn-origin").onclick = () => { showOrigin = !showOrigin; syncUI(); renderAll(); };
document.getElementById("btn-bg").onclick = () => {
  stage.classList.remove(BGS[bgIdx]);
  bgIdx = (bgIdx + 1) % BGS.length;
  stage.classList.add(BGS[bgIdx]);
  document.getElementById("btn-bg").textContent = "BG: " + BG_NAMES[bgIdx];
  renderAll();
};
document.getElementById("sl-ang").oninput = e => {
  autoOrbit = false; curDir = +e.target.value; syncUI(); renderAll();
};
document.getElementById("sl-fps").oninput = e => {
  document.getElementById("lbl-fps").textContent = e.target.value + " FPS";
};
document.getElementById("sl-zoom").oninput = () => renderAll();

// Drag to rotate 360°
let dragStartX = null, dragStartDir = 0;
stage.addEventListener("pointerdown", e => {
  dragStartX = e.clientX;
  dragStartDir = curDir;
  autoOrbit = false;
  stage.classList.add("drag");
  stage.setPointerCapture(e.pointerId);
  syncUI();
});
stage.addEventListener("pointermove", e => {
  if (dragStartX === null) return;
  const steps = Math.round((e.clientX - dragStartX) / 36);
  const nextD = (((dragStartDir - steps) % DIRS) + DIRS) % DIRS;
  if (nextD !== curDir) {
    curDir = nextD;
    syncUI();
    renderAll();
  }
});
const endDrag = () => { dragStartX = null; stage.classList.remove("drag"); };
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

// Keyboard shortcuts
addEventListener("keydown", e => {
  if (e.code === "Space") { e.preventDefault(); playing = !playing; syncUI(); }
  else if (e.code === "ArrowRight") { e.preventDefault(); autoOrbit = false; curDir = (curDir + 1) % DIRS; syncUI(); renderAll(); }
  else if (e.code === "ArrowLeft")  { e.preventDefault(); autoOrbit = false; curDir = (curDir + 7) % DIRS; syncUI(); renderAll(); }
  else if (e.code === "ArrowUp")    { e.preventDefault(); playing = false; curTick++; syncUI(); renderAll(); }
  else if (e.code === "ArrowDown")  { e.preventDefault(); playing = false; curTick = Math.max(0, curTick - 1); syncUI(); renderAll(); }
  else if (e.key >= "1" && e.key <= "9" && (+e.key - 1) < ANIMS.length) { selectAnim(+e.key - 1); }
});

// Load Atlases
ANIMS.forEach(a => {
  const img = new Image();
  img.onload = () => {
    loadedCount++;
    if (loadedCount === ANIMS.length) {
      syncUI();
      rebuildMatrix();
      renderAll();
    }
  };
  img.src = ATLAS_URIS[a.key];
  atlasImgs[a.key] = img;
});

function loop(now) {
  const fps = +document.getElementById("sl-fps").value;
  const interval = 1000 / fps;
  let dirty = false;
  if (playing && now - lastFrameTime >= interval) {
    lastFrameTime = now;
    curTick++;
    dirty = true;
  }
  if (autoOrbit && now - lastOrbitTime >= interval * 5.0) {
    lastOrbitTime = now;
    curDir = (curDir + 1) % DIRS;
    syncUI();
    dirty = true;
  }
  if (dirty) renderAll();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
</body>
</html>
"""


def build_self_contained_html(out_html_path, anims_list, cell_wh, ground_y):
    """anims_list: list of dicts:
         key, short_title, subtitle, title, description, frames_by_dir (list of 8 lists of RGBA PIL Images)
    """
    cw, ch = cell_wh
    meta = []
    atlas_uris = {}
    spr_cursor = 0

    for a in anims_list:
        frames_by_dir = a["frames_by_dir"]
        n_frames = len(frames_by_dir[0])
        atlas = Image.new("RGBA", (cw * n_frames, ch * 8), (0, 0, 0, 0))
        for d in range(8):
            for f in range(n_frames):
                fr = frames_by_dir[d][f]
                if fr.size != (cw, ch):
                    fr = fr.resize((cw, ch), Image.LANCZOS)
                atlas.paste(fr, (f * cw, d * ch))

        buf = io.BytesIO()
        # High-quality RGBA WebP keeps crisp alpha & photographic skin detail in ~1/6th the size of PNG!
        atlas.save(buf, format="WEBP", lossless=False, quality=90, alpha_quality=96, method=4)
        uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        atlas_uris[a["key"]] = uri

        meta.append(dict(
            key=a["key"],
            short_title=a["short_title"],
            subtitle=a["subtitle"],
            title=a["title"],
            description=a["description"],
            n_frames=n_frames,
            spr_base=spr_cursor,
        ))
        spr_cursor += 8 * n_frames

    html = (
        HTML_TEMPLATE
        .replace("__ANIMS_META_JSON__", json.dumps(meta))
        .replace("__ATLAS_URIS_JSON__", json.dumps(atlas_uris))
        .replace("__CELL_W__", str(cw))
        .replace("__CELL_H__", str(ch))
        .replace("__GROUND_Y__", str(ground_y))
    )
    os.makedirs(os.path.dirname(out_html_path), exist_ok=True)
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained HTML inspector: {out_html_path} ({len(html)/1e6:.2f} MB, {spr_cursor} total RGBA frames)")
