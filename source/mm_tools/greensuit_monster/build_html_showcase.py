"""Generates the 100% Self-Contained Interactive HTML5 Showcase (`greensuit_wheelman_monster.html`)
embedding all 7 native 60 FPS x 16-Angle WebP sprite atlases, real reference comparison cards,
and 4 interactive modes:
  1. 360° Drag-Orbit Turntable Studio (16 Angles x 60 FPS)
  2. Playable 2.5D Drive-and-Jump Monster Sandbox (WASD + Shift Charge + Space Pipe-Vault Jump + Click Whirlwind)
  3. Playable 3D First-Person Quake Encounter (Fight AI Packs of Jumping Wheelman Monsters with Shotgun/Rocket!)
  4. 16-Angle Turnaround, Real Photo Accuracy & Full Atlas Inspector
"""
from __future__ import annotations

import base64
import json
import os
from typing import Dict, List


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Green-Suit Wheelman Monster — 16-Angle 360° @ 60 FPS Digitized Live-Action Sprite Suite</title>
<style>
  :root {
    --bg:#070a10; --panel:#101622; --panel2:#172032; --panel3:#1f2b42;
    --border:#2a3956; --ink:#f1f5f9; --dim:#94a3b8;
    --neon:#80f542; --neon2:#4ade80; --gold:#fbbf24; --danger:#f43f5e; --cyan:#38bdf8;
  }
  * { box-sizing:border-box; }
  body {
    margin:0; background:radial-gradient(circle at 50% 0%, #152236 0%, var(--bg) 58%);
    color:var(--ink); font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    min-height:100vh; display:flex; flex-direction:column; align-items:center;
    padding:14px 14px 42px; gap:11px;
  }
  header {
    width:min(100%, 1240px); display:flex; flex-wrap:wrap; align-items:center;
    justify-content:space-between; gap:12px; background:rgba(16,22,34,0.92);
    border:1px solid var(--border); border-radius:14px; padding:13px 18px;
    box-shadow:0 14px 36px rgba(0,0,0,0.42); backdrop-filter:blur(10px);
  }
  .brand h1 {
    margin:0; font-size:clamp(18px, 2.3vw, 24px); font-weight:900; letter-spacing:-0.02em;
    display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  }
  .pill {
    background:linear-gradient(135deg, #8cf854, #38d864); color:#061a0b;
    font-size:11px; font-weight:900; padding:3px 9px; border-radius:999px;
    letter-spacing:0.05em; text-transform:uppercase;
  }
  .pill.hot { background:linear-gradient(135deg, #fbbf24, #f97316); color:#1e0d02; }
  .sub { margin:3px 0 0; color:var(--dim); font-size:12.5px; }
  .hdr-btns { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  .btn {
    background:var(--panel2); color:var(--ink); border:1px solid var(--border);
    border-radius:9px; padding:7px 12px; font:inherit; font-size:12.5px; font-weight:700;
    cursor:pointer; display:inline-flex; align-items:center; gap:6px; transition:all 0.14s ease;
  }
  .btn:hover { border-color:var(--neon); color:var(--neon); transform:translateY(-1px); }
  .btn.active, .btn.primary {
    background:var(--neon); color:#061b0a; border-color:var(--neon); font-weight:900;
  }
  .btn.danger { border-color:#88263b; color:#fda4af; }
  .btn.danger:hover { background:var(--danger); color:#fff; border-color:var(--danger); }

  .mode-bar {
    width:min(100%, 1240px); display:grid; grid-template-columns:repeat(4, 1fr); gap:7px;
    background:var(--panel); border:1px solid var(--border); border-radius:13px; padding:6px;
  }
  @media (max-width:860px) { .mode-bar { grid-template-columns:repeat(2, 1fr); } }
  .mode-tab {
    background:var(--panel2); color:var(--dim); border:1.5px solid transparent;
    border-radius:9px; padding:10px 10px; font:inherit; font-weight:800; font-size:13px;
    cursor:pointer; transition:all 0.14s ease; text-align:center;
  }
  .mode-tab:hover { color:var(--ink); border-color:#41557a; }
  .mode-tab.active {
    background:linear-gradient(180deg, #1a3822 0%, #102317 100%);
    color:var(--neon); border-color:var(--neon);
    box-shadow:0 0 18px rgba(128,245,66,0.22);
  }

  .panel-view { width:min(100%, 1240px); }
  .hidden { display:none !important; }

  .studio-grid {
    display:grid; grid-template-columns:330px 1fr; gap:12px; align-items:start;
  }
  @media (max-width:920px) { .studio-grid { grid-template-columns:1fr; } }

  .anim-list {
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    padding:9px; display:flex; flex-direction:column; gap:7px;
  }
  .anim-card {
    display:flex; align-items:center; gap:10px; padding:10px 11px; border-radius:10px;
    background:var(--panel2); border:1.5px solid transparent; color:var(--ink);
    cursor:pointer; text-align:left; font:inherit; transition:all 0.12s ease; width:100%;
  }
  .anim-card:hover { border-color:#42567d; transform:translateX(2px); }
  .anim-card.active {
    background:#173220; border-color:var(--neon);
    box-shadow:inset 0 0 16px rgba(128,245,66,0.14);
  }
  .anim-ico { font-size:22px; flex:0 0 28px; text-align:center; }
  .anim-info { flex:1; min-width:0; }
  .anim-title { font-weight:800; font-size:13px; display:flex; justify-content:space-between; gap:6px; }
  .anim-meta { font-size:11px; color:var(--dim); display:flex; gap:5px; align-items:center; margin-top:3px; flex-wrap:wrap; }
  .badge {
    font-size:9.5px; font-weight:800; padding:1px 6px; border-radius:4px;
    background:#26344f; color:#cbd5e1;
  }
  .anim-card.active .badge { background:var(--neon); color:#071b0b; }

  .stage-col { display:flex; flex-direction:column; gap:10px; min-width:0; }
  .stage-wrap {
    width:100%; height:min(64vh, 540px); min-height:390px; border-radius:14px;
    border:1px solid var(--border); position:relative; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }
  .stage-wrap:active { cursor:grabbing; }
  .bg-quake   { background:radial-gradient(circle at 50% 68%, #3c291b 0%, #1c130d 70%, #090706 100%); }
  .bg-street  { background:linear-gradient(180deg, #0b1324 0%, #192844 58%, #222733 59%, #151821 100%); }
  .bg-wood    { background:linear-gradient(180deg, #3c2a1a 0%, #2a1c11 60%, #6b4423 60.5%, #462b14 100%); }
  .bg-checker { background:repeating-conic-gradient(#212838 0% 25%, #151a25 0% 50%) 0 0/26px 26px; }
  .bg-studio  { background:radial-gradient(circle at 50% 60%, #f1f5f9 0%, #cbd5e1 72%, #94a3b8 100%); }
  .bg-magenta { background:#ff00ff; }

  canvas.full-cv { width:100%; height:100%; display:block; }

  .hud-tl {
    position:absolute; top:12px; left:14px; background:rgba(9,13,21,0.86);
    border:1px solid #324466; border-radius:10px; padding:8px 13px;
    pointer-events:none; backdrop-filter:blur(6px); max-width:68%;
  }
  .hud-tl .h-title { font-weight:900; font-size:14.5px; color:var(--neon); }
  .hud-tl .h-desc { font-size:11.5px; color:#cbd5e1; margin-top:2px; }
  .hud-tr {
    position:absolute; top:12px; right:14px; background:rgba(9,13,21,0.86);
    border:1px solid #324466; border-radius:10px; padding:7px 11px;
    font-size:11.5px; font-weight:800; color:var(--gold); pointer-events:none;
  }
  .hud-bl {
    position:absolute; bottom:11px; left:14px; right:14px; display:flex;
    justify-content:space-between; align-items:center; pointer-events:none;
    font-size:11.5px; color:#cbd5e1; text-shadow:0 1px 4px #000;
  }

  .ctrl-card {
    background:var(--panel); border:1px solid var(--border); border-radius:13px;
    padding:11px 14px; display:flex; flex-direction:column; gap:10px;
  }
  .ctrl-row { display:flex; flex-wrap:wrap; align-items:center; gap:9px; justify-content:space-between; }
  .slider-grp { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--dim); font-weight:700; }
  input[type=range] { accent-color:var(--neon); cursor:pointer; }

  .angle-strip {
    display:grid; grid-template-columns:repeat(16, 1fr); gap:4px;
  }
  @media (max-width:760px) { .angle-strip { grid-template-columns:repeat(8, 1fr); } }
  .ang-btn {
    background:var(--panel2); color:var(--dim); border:1px solid var(--border);
    border-radius:6px; padding:5px 2px; font-size:10.5px; font-weight:800;
    cursor:pointer; text-align:center; transition:all 0.1s;
  }
  .ang-btn:hover { border-color:var(--neon); color:var(--ink); }
  .ang-btn.active { background:var(--neon); color:#061a0a; border-color:var(--neon); }

  .game-box {
    width:100%; height:min(72vh, 620px); min-height:440px; border-radius:14px;
    border:1px solid var(--border); position:relative; overflow:hidden; background:#0b0f17;
  }
  .game-bar {
    background:var(--panel); border:1px solid var(--border); border-radius:12px;
    padding:10px 15px; margin-top:10px; display:flex; flex-wrap:wrap; gap:12px;
    align-items:center; justify-content:space-between; font-size:12.5px;
  }
  kbd {
    background:#222e46; border:1px solid #41557c; border-radius:5px;
    padding:1px 6px; font-size:11px; font-weight:800; color:var(--neon);
  }

  .insp-grid { display:flex; flex-direction:column; gap:14px; }
  .insp-card {
    background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:15px;
  }
  .insp-card h3 { margin:0 0 8px; color:var(--neon); font-size:16px; }
  .insp-card img { width:100%; height:auto; border-radius:10px; border:1px solid var(--border); display:block; }
  .atlas-scroll {
    width:100%; max-height:560px; overflow:auto; border-radius:10px;
    border:1px solid var(--border); background:repeating-conic-gradient(#1d2433 0% 25%, #131824 0% 50%) 0 0/22px 22px;
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>
      <span>🛞 Green-Suit Wheelman Monster</span>
      <span class="pill">16 Angles · 360°</span>
      <span class="pill hot">Native 60 FPS Digitized</span>
    </h1>
    <p class="sub">100% Real Photo-Digitized Live-Action Stunt Monster — Seated Low-Rider Cruise, Ab-Roller Charge, Pipe-Vault Sky-Point Slam &amp; 3D Quake Gibs</p>
  </div>
  <div class="hdr-btns">
    <button class="btn primary" id="btn-choreo" title="Auto-plays all moves while orbiting 360°">🎬 Monster Demo Reel</button>
    <button class="btn" id="btn-autoturn">🔄 Auto-360° Spin: OFF</button>
    <button class="btn active" id="btn-sfx">🔊 SFX: ON</button>
  </div>
</header>

<nav class="mode-bar">
  <button class="mode-tab active" data-mode="studio">🎛️ 1. 360° Turntable Studio (60 FPS)</button>
  <button class="mode-tab" data-mode="sandbox">🛞 2. Drive &amp; Jump Him Yourself!</button>
  <button class="mode-tab" data-mode="fps">🔫 3. 3D Quake FPS Monster Fight</button>
  <button class="mode-tab" data-mode="inspect">🔍 4. Photo Accuracy &amp; Sprite Sheets</button>
</nav>

<!-- ==================== TAB 1: 360° TURNTABLE STUDIO ==================== -->
<section class="panel-view" id="view-studio">
  <div class="studio-grid">
    <div class="anim-list" id="anim-list"></div>

    <div class="stage-col">
      <div class="stage-wrap bg-quake" id="studio-stage">
        <canvas class="full-cv" id="studio-cv"></canvas>
        <div class="hud-tl">
          <div class="h-title" id="hud-anim-title">Loading 60 FPS Atlases...</div>
          <div class="h-desc" id="hud-anim-desc">Unpacking embedded 16-angle WebP sprite sheets...</div>
        </div>
        <div class="hud-tr" id="hud-angle-readout">0.0° (Front) · Frame 0/36 · 60 FPS</div>
        <div class="hud-bl">
          <span>🖱️ Drag left/right anywhere to orbit all 16 angles (every 22.5°) · Scroll to zoom</span>
          <span id="load-progress">Loading...</span>
        </div>
      </div>

      <div class="ctrl-card">
        <div class="ctrl-row">
          <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
            <button class="btn active" id="btn-play">⏸ Pause</button>
            <button class="btn" id="btn-prev">⏮</button>
            <button class="btn" id="btn-next">⏭</button>
            <button class="btn" id="btn-pivot">🎯 Pivot/Hitbox</button>
          </div>
          <div class="slider-grp" style="flex:1; min-width:190px;">
            <span>Frame</span>
            <input type="range" id="rng-frame" min="0" max="35" value="0" style="flex:1;">
          </div>
          <div class="slider-grp">
            <span>FPS: <strong id="lbl-fps" style="color:var(--neon)">60</strong></span>
            <input type="range" id="rng-fps" min="6" max="90" value="60" style="width:96px;">
          </div>
          <div class="slider-grp">
            <span>Zoom</span>
            <input type="range" id="rng-zoom" min="60" max="220" value="125" style="width:86px;">
          </div>
        </div>

        <div class="angle-strip" id="angle-strip"></div>

        <div class="ctrl-row" style="padding-top:2px;">
          <span style="font-size:12px; color:var(--dim); font-weight:700;">Stage Backdrop:</span>
          <div style="display:flex; gap:6px; flex-wrap:wrap;" id="bg-btns">
            <button class="btn active" data-bg="bg-quake">🏰 Quake Dungeon</button>
            <button class="btn" data-bg="bg-street">🌃 Bakersfield Street</button>
            <button class="btn" data-bg="bg-wood">🪵 Hardwood Room</button>
            <button class="btn" data-bg="bg-checker">🏁 Alpha Checker</button>
            <button class="btn" data-bg="bg-studio">💡 Bright Studio</button>
            <button class="btn" data-bg="bg-magenta">🟪 #FF00FF Key</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ==================== TAB 2: 2.5D DRIVE & JUMP SANDBOX ==================== -->
<section class="panel-view hidden" id="view-sandbox">
  <div class="game-box">
    <canvas class="full-cv" id="sandbox-cv"></canvas>
    <div class="hud-tl">
      <div class="h-title">🛞 Monster Rampage Stunt Arena (60 FPS · 16 Angles)</div>
      <div class="h-desc" id="sb-status">Ride around on your wheels, hit Shift for Ab-Roller Torpedo Charge, press SPACE to Pipe-Vault Sky-Point Jump &amp; Slam!</div>
    </div>
    <div class="hud-tr" id="sb-score">Crushed: 0 · Combo: x1</div>
  </div>
  <div class="game-bar">
    <div>
      <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> / Arrows: Ride &amp; Carve 360° &nbsp;·&nbsp;
      <kbd>Shift</kbd>: Ab-Roller Torpedo Charge &nbsp;·&nbsp;
      <kbd>Space</kbd>: Pipe-Vault Sky-Point Jump &amp; Shockwave Slam! &nbsp;·&nbsp;
      <kbd>Click</kbd> / <kbd>E</kbd>: 360° Whirlwind Melee &nbsp;·&nbsp;
      <kbd>Q</kbd>: Wheelie Burnout &nbsp;·&nbsp;
      <kbd>G</kbd>: Test Mega-Gib!
    </div>
    <button class="btn primary" id="btn-sb-reset">🔄 Respawn Dummies &amp; Barrels</button>
  </div>
</section>

<!-- ==================== TAB 3: 3D QUAKE FPS MONSTER ENCOUNTER ==================== -->
<section class="panel-view hidden" id="view-fps">
  <div class="game-box" id="fps-wrap" style="cursor:crosshair;">
    <canvas class="full-cv" id="fps-cv"></canvas>
    <div class="hud-tl">
      <div class="h-title">🔫 First-Person 3D Quake Arena — Survive the Jumping Wheelman Pack!</div>
      <div class="h-desc">Click arena to lock mouse (or drag to aim). Watch them prowl, charge, and pole-vault jump at your head across all 16 angles!</div>
    </div>
    <div class="hud-tr" id="fps-hud">HP: 100 · Frags: 0 · Wave: 1</div>
  </div>
  <div class="game-bar">
    <div>
      <kbd>Click Arena</kbd>: Mouse-Look &amp; Shoot &nbsp;·&nbsp;
      <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>: Move/Strafe &nbsp;·&nbsp;
      <kbd>1</kbd>: Super Shotgun &nbsp;·&nbsp;
      <kbd>2</kbd>: Rocket Launcher (Guaranteed Gibs!) &nbsp;·&nbsp;
      <kbd>Space</kbd>: Jump
    </div>
    <div style="display:flex; gap:8px;">
      <button class="btn" id="btn-fps-spawn">➕ Summon Another Monster</button>
      <button class="btn danger" id="btn-fps-nuke">💥 Gib All Monsters!</button>
    </div>
  </div>
</section>

<!-- ==================== TAB 4: PHOTO ACCURACY & ATLAS INSPECTOR ==================== -->
<section class="panel-view hidden" id="view-inspect">
  <div class="insp-grid">
    <div class="insp-card">
      <h3>📸 100% Real Photo-Digitized Fidelity &amp; Full 16-Angle (Every 22.5°) Turnaround</h3>
      <p style="margin:0 0 10px; color:var(--dim); font-size:13px;">Built directly from live-action photography with zero procedural 3D human meshes — preserving his exact real face, expressions, bright neon morphsuit wrinkles, white-rimmed pneumatic tires, and bullet-nosed stainless center pipe across all 16 compass angles.</p>
      <img id="img-turnaround-poster" alt="16-Angle Turnaround Sheet">
    </div>
    <div class="insp-card">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
        <h3 style="margin:0;">🎞️ Raw 60 FPS × 16-Row Baked Sprite Atlas Inspector</h3>
        <div style="display:flex; gap:8px; align-items:center;">
          <select id="sel-atlas-inspect" class="btn" style="padding:6px 10px;"></select>
          <span style="font-size:12px; color:var(--dim);" id="lbl-atlas-dims"></span>
        </div>
      </div>
      <div class="atlas-scroll">
        <img id="img-raw-atlas" style="width:auto; max-width:none; image-rendering:auto;" alt="Raw Sprite Sheet Atlas">
      </div>
    </div>
  </div>
</section>

<script>
const META = __META_JSON__;
const ATLAS_DATA = __ATLAS_JSON__;
const POSTER_URI = __POSTER_JSON__;

const CELL_W = META.cellW;
const CELL_H = META.cellH;
const GROUND_Y = META.groundY;
const N_DIRS = 16;
const DIR_NAMES = [
  "0.0° Front", "22.5° Fr-Left", "45.0° Fr-Left", "67.5° Stp-Left",
  "90.0° Left Side", "112.5° Rr-Left", "135.0° Bk-Left", "157.5° Stp-BackL",
  "180.0° Dead Back", "202.5° Stp-BackR", "225.0° Bk-Right", "247.5° Rr-Right",
  "270.0° Right Side", "292.5° Stp-Right", "315.0° Fr-Right", "337.5° Fr-Right"
];

// ---------------------------------------------------------------------------
// 1. WebAudio Procedural Monster & Quake SFX Synthesizer
// ---------------------------------------------------------------------------
let sfxEnabled = true;
let audioCtx = null;
function ensureAudio() {
  if (!sfxEnabled) return null;
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
  return audioCtx;
}

function playSfx(kind) {
  const ctx = ensureAudio();
  if (!ctx) return;
  const now = ctx.currentTime;
  if (kind === "vault") {
    // Metallic stainless-pipe pole-vault CLANG + upward spring whoosh!
    const o1 = ctx.createOscillator(), g1 = ctx.createGain();
    o1.type = "triangle";
    o1.frequency.setValueAtTime(520, now);
    o1.frequency.exponentialRampToValueAtTime(1280, now + 0.09);
    o1.frequency.exponentialRampToValueAtTime(290, now + 0.34);
    g1.gain.setValueAtTime(0.24, now);
    g1.gain.exponentialRampToValueAtTime(0.001, now + 0.36);
    o1.connect(g1).connect(ctx.destination);
    o1.start(now); o1.stop(now + 0.36);
  } else if (kind === "slam") {
    // Heavy tire + steel shockwave SLAM!
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sawtooth";
    o.frequency.setValueAtTime(135, now);
    o.frequency.exponentialRampToValueAtTime(32, now + 0.28);
    g.gain.setValueAtTime(0.32, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + 0.30);
    o.connect(g).connect(ctx.destination);
    o.start(now); o.stop(now + 0.30);
  } else if (kind === "roar") {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sawtooth";
    o.frequency.setValueAtTime(190, now);
    o.frequency.linearRampToValueAtTime(285, now + 0.12);
    o.frequency.exponentialRampToValueAtTime(115, now + 0.38);
    g.gain.setValueAtTime(0.16, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + 0.40);
    o.connect(g).connect(ctx.destination);
    o.start(now); o.stop(now + 0.40);
  } else if (kind === "whirl") {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(160, now);
    o.frequency.exponentialRampToValueAtTime(460, now + 0.16);
    o.frequency.exponentialRampToValueAtTime(140, now + 0.36);
    g.gain.setValueAtTime(0.20, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
    o.connect(g).connect(ctx.destination);
    o.start(now); o.stop(now + 0.38);
  } else if (kind === "shotgun" || kind === "rocket" || kind === "gib") {
    const dur = kind === "shotgun" ? 0.22 : 0.48;
    const buf = ctx.createBuffer(1, Math.floor(ctx.sampleRate * dur), ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) {
      const env = Math.pow(1 - i / data.length, kind === "gib" ? 1.4 : 2.1);
      data[i] = (Math.random() * 2 - 1) * env;
    }
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const flt = ctx.createBiquadFilter();
    flt.type = "lowpass";
    flt.frequency.setValueAtTime(kind === "gib" ? 950 : 1400, now);
    flt.frequency.exponentialRampToValueAtTime(160, now + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.36, now);
    g.gain.exponentialRampToValueAtTime(0.01, now + dur);
    src.connect(flt).connect(g).connect(ctx.destination);
    src.start(now);
  }
}

// ---------------------------------------------------------------------------
// 2. Load Embedded 60 FPS Atlases
// ---------------------------------------------------------------------------
const atlases = {};
let loadedCount = 0;
const animMap = {};
META.anims.forEach(a => { animMap[a.id] = a; });

META.anims.forEach(a => {
  const img = new Image();
  img.onload = () => {
    loadedCount++;
    const lp = document.getElementById("load-progress");
    if (loadedCount < META.anims.length) {
      lp.textContent = `Loaded ${loadedCount}/${META.anims.length} atlases...`;
    } else {
      lp.textContent = `All ${META.totalFrames.toLocaleString()} baked 60 FPS frames ready!`;
      updateInspectAtlas();
    }
  };
  img.src = ATLAS_DATA[a.id];
  atlases[a.id] = img;
});

document.getElementById("img-turnaround-poster").src = POSTER_URI;

// Helper to draw a single baked sprite cell
function drawSpriteFrame(ctx, animId, dIdx, fIdx, screenX, groundScreenY, scale, alpha = 1.0) {
  const img = atlases[animId];
  if (!img || !img.complete || !img.naturalWidth) return;
  const spec = animMap[animId];
  const d = ((Math.round(dIdx) % N_DIRS) + N_DIRS) % N_DIRS;
  const f = Math.max(0, Math.min(spec.frames - 1, Math.floor(fIdx)));
  const dw = CELL_W * scale;
  const dh = CELL_H * scale;
  const dx = screenX - dw * 0.5;
  const dy = groundScreenY - GROUND_Y * scale;
  if (alpha < 0.999) ctx.save();
  if (alpha < 0.999) ctx.globalAlpha = alpha;
  ctx.drawImage(img, f * CELL_W, d * CELL_H, CELL_W, CELL_H, dx, dy, dw, dh);
  if (alpha < 0.999) ctx.restore();
}

// ---------------------------------------------------------------------------
// 3. Tab Switching & Studio Controls
// ---------------------------------------------------------------------------
let activeMode = "studio";
document.querySelectorAll(".mode-tab").forEach(btn => {
  btn.addEventListener("click", () => {
    activeMode = btn.dataset.mode;
    document.querySelectorAll(".mode-tab").forEach(b => b.classList.toggle("active", b === btn));
    ["studio", "sandbox", "fps", "inspect"].forEach(m => {
      document.getElementById("view-" + m).classList.toggle("hidden", m !== activeMode);
    });
    if (activeMode !== "fps" && document.pointerLockElement) document.exitPointerLock();
  });
});

document.getElementById("btn-sfx").addEventListener("click", (e) => {
  sfxEnabled = !sfxEnabled;
  e.currentTarget.classList.toggle("active", sfxEnabled);
  e.currentTarget.textContent = sfxEnabled ? "🔊 SFX: ON" : "🔇 SFX: OFF";
});

// Studio state
let curAnimId = "cruise";
let curDirFloat = 0.0;
let curFrameFloat = 0.0;
let isPlaying = true;
let targetFps = 60;
let studioZoom = 1.25;
let showPivot = false;
let autoTurn = false;
let choreoActive = false;
let choreoStep = 0;

const CHOREO_SEQ = [
  { id: "cruise", loops: 2 },
  { id: "wheelie_taunt", loops: 1 },
  { id: "charge", loops: 2 },
  { id: "jump_slam", loops: 2 },
  { id: "whirlwind_melee", loops: 2 },
  { id: "pain", loops: 1 },
  { id: "gib_death", loops: 1 },
];
let choreoLoopsDone = 0;

// Build animation list cards
const animListEl = document.getElementById("anim-list");
const selInspect = document.getElementById("sel-atlas-inspect");
META.anims.forEach((a, idx) => {
  const btn = document.createElement("button");
  btn.className = "anim-card" + (a.id === curAnimId ? " active" : "");
  btn.dataset.id = a.id;
  btn.innerHTML = `
    <div class="anim-ico">${a.ico}</div>
    <div class="anim-info">
      <div class="anim-title"><span>${idx + 1}. ${a.title}</span></div>
      <div class="anim-meta">
        <span class="badge">${a.frames}f @ 60fps</span>
        <span class="badge">16 Angles</span>
        <span>${(a.frames * 16)} cells</span>
      </div>
    </div>`;
  btn.addEventListener("click", () => {
    choreoActive = false;
    document.getElementById("btn-choreo").classList.remove("active");
    selectAnim(a.id, true);
  });
  animListEl.appendChild(btn);

  const opt = document.createElement("option");
  opt.value = a.id;
  opt.textContent = `${a.ico} ${a.title} (16 × ${a.frames}f @ 60 FPS)`;
  selInspect.appendChild(opt);
});

function updateInspectAtlas() {
  const id = selInspect.value || "cruise";
  const spec = animMap[id];
  document.getElementById("img-raw-atlas").src = ATLAS_DATA[id];
  document.getElementById("lbl-atlas-dims").textContent =
    `${spec.frames * CELL_W} × ${16 * CELL_H} px (${spec.frames * 16} cells)`;
}
selInspect.addEventListener("change", updateInspectAtlas);

// Build 16-angle buttons
const angleStripEl = document.getElementById("angle-strip");
for (let d = 0; d < N_DIRS; d++) {
  const b = document.createElement("button");
  b.className = "ang-btn" + (d === 0 ? " active" : "");
  b.textContent = (d * 22.5) + "°";
  b.addEventListener("click", () => {
    curDirFloat = d;
    autoTurn = false;
    document.getElementById("btn-autoturn").classList.remove("active");
    document.getElementById("btn-autoturn").textContent = "🔄 Auto-360° Spin: OFF";
    syncAngleButtons();
  });
  angleStripEl.appendChild(b);
}

function syncAngleButtons() {
  const dActive = ((Math.round(curDirFloat) % N_DIRS) + N_DIRS) % N_DIRS;
  angleStripEl.querySelectorAll(".ang-btn").forEach((b, idx) => b.classList.toggle("active", idx === dActive));
}

function selectAnim(id, playSound = false) {
  curAnimId = id;
  curFrameFloat = 0.0;
  isPlaying = true;
  document.getElementById("btn-play").textContent = "⏸ Pause";
  document.getElementById("btn-play").classList.add("active");
  const spec = animMap[id];
  document.getElementById("rng-frame").max = spec.frames - 1;
  document.getElementById("hud-anim-title").textContent = `${spec.ico} ${spec.title}`;
  document.getElementById("hud-anim-desc").textContent = spec.desc;
  animListEl.querySelectorAll(".anim-card").forEach(c => c.classList.toggle("active", c.dataset.id === id));
  if (playSound) {
    if (id === "jump_slam") playSfx("vault");
    else if (id === "gib_death") playSfx("gib");
    else if (id === "whirlwind_melee") playSfx("whirl");
    else if (id === "charge" || id === "wheelie_taunt") playSfx("roar");
  }
}
selectAnim("cruise", false);

// Studio Drag-to-Orbit & Zoom
const studioStage = document.getElementById("studio-stage");
let draggingStage = false, dragLastX = 0;
studioStage.addEventListener("pointerdown", e => {
  draggingStage = true; dragLastX = e.clientX;
  studioStage.setPointerCapture(e.pointerId);
});
studioStage.addEventListener("pointermove", e => {
  if (!draggingStage) return;
  const dx = e.clientX - dragLastX;
  dragLastX = e.clientX;
  curDirFloat = ((curDirFloat + dx * 0.055) % N_DIRS + N_DIRS) % N_DIRS;
  syncAngleButtons();
});
studioStage.addEventListener("pointerup", () => { draggingStage = false; });
studioStage.addEventListener("wheel", e => {
  e.preventDefault();
  studioZoom = Math.max(0.6, Math.min(2.2, studioZoom - e.deltaY * 0.001));
  document.getElementById("rng-zoom").value = Math.round(studioZoom * 100);
}, { passive: false });

document.getElementById("btn-play").addEventListener("click", e => {
  isPlaying = !isPlaying;
  e.currentTarget.textContent = isPlaying ? "⏸ Pause" : "▶ Play";
  e.currentTarget.classList.toggle("active", isPlaying);
});
document.getElementById("btn-prev").addEventListener("click", () => {
  isPlaying = false;
  document.getElementById("btn-play").textContent = "▶ Play";
  const spec = animMap[curAnimId];
  curFrameFloat = (Math.floor(curFrameFloat) - 1 + spec.frames) % spec.frames;
});
document.getElementById("btn-next").addEventListener("click", () => {
  isPlaying = false;
  document.getElementById("btn-play").textContent = "▶ Play";
  const spec = animMap[curAnimId];
  curFrameFloat = (Math.floor(curFrameFloat) + 1) % spec.frames;
});
document.getElementById("btn-pivot").addEventListener("click", e => {
  showPivot = !showPivot;
  e.currentTarget.classList.toggle("active", showPivot);
});
document.getElementById("rng-frame").addEventListener("input", e => {
  isPlaying = false;
  document.getElementById("btn-play").textContent = "▶ Play";
  curFrameFloat = parseFloat(e.target.value);
});
document.getElementById("rng-fps").addEventListener("input", e => {
  targetFps = parseInt(e.target.value, 10);
  document.getElementById("lbl-fps").textContent = targetFps;
});
document.getElementById("rng-zoom").addEventListener("input", e => {
  studioZoom = parseInt(e.target.value, 10) / 100.0;
});
document.getElementById("btn-autoturn").addEventListener("click", e => {
  autoTurn = !autoTurn;
  e.currentTarget.classList.toggle("active", autoTurn);
  e.currentTarget.textContent = autoTurn ? "🔄 Auto-360° Spin: ON" : "🔄 Auto-360° Spin: OFF";
});
document.getElementById("btn-choreo").addEventListener("click", e => {
  choreoActive = !choreoActive;
  e.currentTarget.classList.toggle("active", choreoActive);
  if (choreoActive) {
    autoTurn = true;
    document.getElementById("btn-autoturn").classList.add("active");
    document.getElementById("btn-autoturn").textContent = "🔄 Auto-360° Spin: ON";
    choreoStep = 0; choreoLoopsDone = 0;
    selectAnim(CHOREO_SEQ[0].id, true);
  }
});

document.querySelectorAll("#bg-btns .btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#bg-btns .btn").forEach(b => b.classList.toggle("active", b === btn));
    studioStage.className = "stage-wrap " + btn.dataset.bg;
  });
});

window.addEventListener("keydown", e => {
  if (activeMode === "studio" && e.key >= "1" && e.key <= "7") {
    const idx = parseInt(e.key, 10) - 1;
    if (META.anims[idx]) selectAnim(META.anims[idx].id, true);
  }
});

function renderStudio(dt) {
  const cv = document.getElementById("studio-cv");
  const rect = cv.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (cv.width !== Math.floor(rect.width * dpr) || cv.height !== Math.floor(rect.height * dpr)) {
    cv.width = Math.floor(rect.width * dpr);
    cv.height = Math.floor(rect.height * dpr);
  }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = rect.width, H = rect.height;
  ctx.clearRect(0, 0, W, H);

  if (autoTurn && !draggingStage) {
    curDirFloat = (curDirFloat + dt * 2.6) % N_DIRS;
    syncAngleButtons();
  }

  const spec = animMap[curAnimId];
  if (isPlaying) {
    const prevF = Math.floor(curFrameFloat);
    curFrameFloat += dt * targetFps;
    if (curAnimId === "jump_slam" && prevF < 45 && Math.floor(curFrameFloat) >= 45) playSfx("slam");
    if (curFrameFloat >= spec.frames) {
      if (choreoActive) {
        choreoLoopsDone++;
        if (choreoLoopsDone >= CHOREO_SEQ[choreoStep].loops) {
          choreoStep = (choreoStep + 1) % CHOREO_SEQ.length;
          choreoLoopsDone = 0;
          selectAnim(CHOREO_SEQ[choreoStep].id, true);
        } else {
          curFrameFloat = curFrameFloat % spec.frames;
        }
      } else if (spec.loop) {
        curFrameFloat = curFrameFloat % spec.frames;
      } else {
        // Hold briefly on final frame of pain/gib_death then replay cleanly
        if (curFrameFloat >= spec.frames + targetFps * 0.45) {
          curFrameFloat = 0;
          if (curAnimId === "gib_death") playSfx("gib");
        }
      }
    }
  }

  const fDisp = Math.min(spec.frames - 1, Math.floor(curFrameFloat));
  document.getElementById("rng-frame").value = fDisp;
  const dIdx = ((Math.round(curDirFloat) % N_DIRS) + N_DIRS) % N_DIRS;
  document.getElementById("hud-angle-readout").textContent =
    `${DIR_NAMES[dIdx]} · Frame ${fDisp + 1}/${spec.frames} · ${targetFps} FPS`;

  // Subtle perspective floor ellipse grid
  const gx = W * 0.5, gy = H * 0.80;
  ctx.save();
  ctx.strokeStyle = "rgba(128,245,66,0.18)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.ellipse(gx, gy, 150 * studioZoom, 38 * studioZoom, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  const scale = (H / 320.0) * studioZoom;
  drawSpriteFrame(ctx, curAnimId, dIdx, fDisp, gx, gy, scale);

  if (showPivot) {
    ctx.save();
    const hbW = 92 * scale, hbH = 165 * scale;
    ctx.strokeStyle = "#38bdf8";
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.8;
    ctx.strokeRect(gx - hbW * 0.5, gy - hbH, hbW, hbH);
    ctx.setLineDash([]);
    ctx.strokeStyle = "#f43f5e";
    ctx.beginPath();
    ctx.moveTo(gx - 18, gy); ctx.lineTo(gx + 18, gy);
    ctx.moveTo(gx, gy - 18); ctx.lineTo(gx, gy + 18);
    ctx.stroke();
    ctx.restore();
  }
}

// ---------------------------------------------------------------------------
// 4. TAB 2: Playable 2.5D Drive & Jump Monster Sandbox!
// ---------------------------------------------------------------------------
const keys = {};
window.addEventListener("keydown", e => {
  keys[e.code] = true;
  if (activeMode === "sandbox" && ["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
    e.preventDefault();
  }
  if (activeMode === "sandbox") {
    if (e.code === "Space" && sbPlayer.state !== "jump_slam" && sbPlayer.state !== "gib_death") {
      sbPlayer.state = "jump_slam"; sbPlayer.animF = 0; sbPlayer.slamDone = false;
      playSfx("vault");
    } else if (e.code === "KeyE" && sbPlayer.state !== "jump_slam" && sbPlayer.state !== "gib_death") {
      sbPlayer.state = "whirlwind_melee"; sbPlayer.animF = 0;
      playSfx("whirl");
    } else if (e.code === "KeyQ" && sbPlayer.state !== "jump_slam") {
      sbPlayer.state = "wheelie_taunt"; sbPlayer.animF = 0;
      playSfx("roar");
    } else if (e.code === "KeyG") {
      sbPlayer.state = "gib_death"; sbPlayer.animF = 0;
      playSfx("gib");
    }
  }
});
window.addEventListener("keyup", e => { keys[e.code] = false; });

const sbPlayer = { x: 0, y: 0, yaw: 270, vx: 0, vy: 0, state: "cruise", animF: 0, slamDone: false, crushed: 0, combo: 1 };
let sbTargets = [];
let sbSkids = [];
let sbShockwaves = [];

function resetSandbox() {
  sbTargets = [];
  for (let i = 0; i < 16; i++) {
    const ang = (i / 16) * Math.PI * 2;
    const dist = 160 + (i % 3) * 115;
    sbTargets.push({
      x: Math.cos(ang) * dist,
      y: Math.sin(ang) * dist * 0.65,
      kind: i % 4 === 0 ? "barrel" : "grunt",
      alive: true,
      bloodR: 0,
      wanderPhase: Math.random() * 6.28,
    });
  }
  sbSkids = [];
  sbShockwaves = [];
}
resetSandbox();
document.getElementById("btn-sb-reset").addEventListener("click", resetSandbox);
document.getElementById("sandbox-cv").addEventListener("pointerdown", () => {
  if (sbPlayer.state !== "jump_slam" && sbPlayer.state !== "gib_death") {
    sbPlayer.state = "whirlwind_melee"; sbPlayer.animF = 0;
    playSfx("whirl");
  }
});

function smashNearbyTargets(cx, cy, radius, label) {
  let hits = 0;
  sbTargets.forEach(t => {
    if (!t.alive) return;
    const d = Math.hypot(t.x - cx, t.y - cy);
    if (d < radius) {
      t.alive = false;
      t.bloodR = t.kind === "barrel" ? 48 : 34;
      hits++;
      sbPlayer.crushed++;
      if (t.kind === "barrel") {
        sbShockwaves.push({ x: t.x, y: t.y, r: 10, maxR: 135, col: "#fb923c" });
        playSfx("rocket");
      }
    }
  });
  if (hits > 0) {
    sbPlayer.combo = Math.min(12, sbPlayer.combo + hits);
    playSfx("gib");
    document.getElementById("sb-status").textContent = `${label} SMASHED ${hits} target(s)!`;
    document.getElementById("sb-score").textContent = `Crushed: ${sbPlayer.crushed} · Combo: x${sbPlayer.combo}`;
  }
}

function renderSandbox(dt) {
  const cv = document.getElementById("sandbox-cv");
  const rect = cv.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (cv.width !== Math.floor(rect.width * dpr) || cv.height !== Math.floor(rect.height * dpr)) {
    cv.width = Math.floor(rect.width * dpr); cv.height = Math.floor(rect.height * dpr);
  }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = rect.width, H = rect.height;

  // Asphalt arena floor
  ctx.fillStyle = "#141923";
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = "rgba(148,163,184,0.08)";
  ctx.lineWidth = 1;
  for (let x = (W * 0.5) % 64; x < W; x += 64) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = (H * 0.5) % 64; y < H; y += 64) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

  // Input vector
  let ix = 0, iy = 0;
  if (keys["KeyA"] || keys["ArrowLeft"]) ix -= 1;
  if (keys["KeyD"] || keys["ArrowRight"]) ix += 1;
  if (keys["KeyW"] || keys["ArrowUp"]) iy -= 1;
  if (keys["KeyS"] || keys["ArrowDown"]) iy += 1;
  const moving = (ix !== 0 || iy !== 0);
  const turbo = keys["ShiftLeft"] || keys["ShiftRight"];

  if (sbPlayer.state === "gib_death") {
    sbPlayer.animF += dt * 60;
    if (sbPlayer.animF >= 72) { sbPlayer.state = "cruise"; sbPlayer.animF = 0; }
  } else if (sbPlayer.state === "jump_slam") {
    const spd = 290;
    const rad = sbPlayer.yaw * Math.PI / 180;
    sbPlayer.x += Math.cos(rad) * spd * dt;
    sbPlayer.y += Math.sin(rad) * spd * 0.72 * dt;
    sbPlayer.animF += dt * 60;
    if (!sbPlayer.slamDone && sbPlayer.animF >= 45) {
      sbPlayer.slamDone = true;
      playSfx("slam");
      sbShockwaves.push({ x: sbPlayer.x, y: sbPlayer.y, r: 16, maxR: 145, col: "#80f542" });
      smashNearbyTargets(sbPlayer.x, sbPlayer.y, 130, "🚀 PIPE-VAULT SKY-POINT SLAM");
    }
    if (sbPlayer.animF >= 54) { sbPlayer.state = "cruise"; sbPlayer.animF = 0; }
  } else if (sbPlayer.state === "whirlwind_melee") {
    sbPlayer.animF += dt * 60;
    if (Math.floor(sbPlayer.animF) === 16) smashNearbyTargets(sbPlayer.x, sbPlayer.y, 110, "🌪️ 360° WHIRLWIND");
    if (sbPlayer.animF >= 36) { sbPlayer.state = "cruise"; sbPlayer.animF = 0; }
  } else if (sbPlayer.state === "wheelie_taunt") {
    sbPlayer.animF += dt * 60;
    if (sbPlayer.animF >= 36) { sbPlayer.state = "cruise"; sbPlayer.animF = 0; }
  } else {
    if (moving) {
      const wantYaw = (Math.atan2(iy, ix) * 180 / Math.PI + 360) % 360;
      let diff = ((wantYaw - sbPlayer.yaw + 540) % 360) - 180;
      sbPlayer.yaw = (sbPlayer.yaw + diff * Math.min(1, dt * 10) + 360) % 360;
      const spd = turbo ? 365 : 210;
      sbPlayer.x += (ix / Math.hypot(ix, iy)) * spd * dt;
      sbPlayer.y += (iy / Math.hypot(ix, iy)) * spd * dt;
      sbPlayer.state = turbo ? "charge" : "cruise";
      sbPlayer.animF = (sbPlayer.animF + dt * 60) % animMap[sbPlayer.state].frames;
      if (Math.abs(diff) > 35 || turbo) {
        sbSkids.push({ x: sbPlayer.x, y: sbPlayer.y, a: 0.45 });
        if (sbSkids.length > 220) sbSkids.shift();
      }
      if (turbo) smashNearbyTargets(sbPlayer.x, sbPlayer.y, 58, "⚡ AB-ROLLER CHARGE");
    } else {
      sbPlayer.state = "cruise";
      sbPlayer.animF = (sbPlayer.animF + dt * 24) % animMap.cruise.frames;
    }
  }

  const limX = W * 0.45, limY = H * 0.42;
  sbPlayer.x = Math.max(-limX, Math.min(limX, sbPlayer.x));
  sbPlayer.y = Math.max(-limY, Math.min(limY, sbPlayer.y));

  // Draw tire skidmarks & blood pools
  sbSkids.forEach(s => {
    ctx.fillStyle = `rgba(10,12,16,${s.a})`;
    ctx.fillRect(W * 0.5 + s.x - 14, H * 0.52 + s.y - 3, 7, 4);
    ctx.fillRect(W * 0.5 + s.x + 8, H * 0.52 + s.y - 3, 7, 4);
  });
  sbTargets.forEach(t => {
    if (!t.alive && t.bloodR > 0) {
      ctx.fillStyle = t.kind === "barrel" ? "rgba(30,28,28,0.75)" : "rgba(138,10,16,0.82)";
      ctx.beginPath();
      ctx.ellipse(W * 0.5 + t.x, H * 0.52 + t.y, t.bloodR, t.bloodR * 0.36, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  });

  // Sort entities by Y for true 2.5D painter's depth
  const drawables = [];
  sbTargets.forEach(t => {
    if (!t.alive) return;
    if (t.kind === "grunt") {
      t.wanderPhase += dt * 2.2;
      t.x += Math.cos(t.wanderPhase) * 22 * dt;
      t.y += Math.sin(t.wanderPhase * 0.7) * 14 * dt;
    }
    drawables.push({ y: t.y, kind: t.kind, obj: t });
  });
  drawables.push({ y: sbPlayer.y, kind: "player" });
  drawables.sort((a, b) => a.y - b.y);

  // Camera sits at south (+Y = 90° in screen space): convert player yaw to 16-angle sprite index!
  // In screen space: yaw=90° (moving straight down toward viewer) -> d=0 (Front)!
  // yaw=180° (moving left) -> d=4 (90° Left Side)!
  // yaw=270° (moving straight up away from viewer) -> d=8 (180° Dead Back)!
  // yaw=0° (moving right) -> d=12 (270° Right Side)!
  const relDeg = ((sbPlayer.yaw - 90) % 360 + 360) % 360;
  const pDir16 = Math.round(relDeg / 22.5) % 16;

  drawables.forEach(item => {
    if (item.kind === "player") {
      drawSpriteFrame(ctx, sbPlayer.state, pDir16, sbPlayer.animF, W * 0.5 + sbPlayer.x, H * 0.52 + sbPlayer.y, 0.72);
    } else {
      const tx = W * 0.5 + item.obj.x, ty = H * 0.52 + item.obj.y;
      if (item.kind === "barrel") {
        ctx.fillStyle = "#b91c1c";
        ctx.fillRect(tx - 15, ty - 42, 30, 42);
        ctx.fillStyle = "#fbbf24";
        ctx.fillRect(tx - 15, ty - 27, 30, 7);
        ctx.strokeStyle = "#fca5a5";
        ctx.strokeRect(tx - 15, ty - 42, 30, 42);
      } else {
        // Target Quake Grunt dummy
        ctx.fillStyle = "rgba(0,0,0,0.35)";
        ctx.beginPath(); ctx.ellipse(tx, ty, 16, 6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#78553a";
        ctx.fillRect(tx - 11, ty - 44, 22, 30);
        ctx.fillStyle = "#d6a37c";
        ctx.beginPath(); ctx.arc(tx, ty - 52, 10, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#ef4444";
        ctx.fillRect(tx - 12, ty - 62, 24, 5);
      }
    }
  });

  // Shockwaves
  for (let i = sbShockwaves.length - 1; i >= 0; i--) {
    const sw = sbShockwaves[i];
    sw.r += dt * 420;
    const alpha = Math.max(0, 1 - sw.r / sw.maxR);
    ctx.strokeStyle = sw.col;
    ctx.globalAlpha = alpha;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.ellipse(W * 0.5 + sw.x, H * 0.52 + sw.y, sw.r, sw.r * 0.36, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.globalAlpha = 1;
    if (sw.r >= sw.maxR) sbShockwaves.splice(i, 1);
  }
}

// ---------------------------------------------------------------------------
// 5. TAB 3: Playable 3D First-Person Quake Encounter (True 16-Angle Billboards!)
// ---------------------------------------------------------------------------
const MAP_SIZE = 16;
const QMAP = [
  "1111111111111111",
  "1000000000000001",
  "1000000000000001",
  "1002200000022001",
  "1002000000002001",
  "1000000000000001",
  "1000000110000001",
  "1000000110000001",
  "1000000000000001",
  "1002000000002001",
  "1002200000022001",
  "1000000000000001",
  "1000000000000001",
  "1000000000000001",
  "1000000000000001",
  "1111111111111111"
];

function isWall(x, y) {
  const gx = Math.floor(x), gy = Math.floor(y);
  if (gx < 0 || gy < 0 || gx >= MAP_SIZE || gy >= MAP_SIZE) return true;
  return QMAP[gy][gx] !== "0";
}

const fpPlayer = { x: 8.0, y: 13.2, z: 0, vz: 0, yaw: -Math.PI / 2, hp: 100, frags: 0, weapon: 1, recoil: 0, muzzle: 0, hurtFlash: 0 };
let fpMonsters = [];
let fpRockets = [];
let fpWave = 1;

function spawnFpMonster(x, y) {
  fpMonsters.push({
    x, y, z: 0, vz: 0,
    yaw: Math.random() * Math.PI * 2,
    hp: 120,
    state: "cruise",
    animF: Math.random() * 30,
    aiTimer: 1.2 + Math.random() * 1.5,
    dead: false,
    removeTimer: 0
  });
}

function spawnWave() {
  const spots = [[3.5, 2.5], [12.5, 2.5], [8.0, 4.5], [2.5, 8.5], [13.5, 8.5]];
  const count = Math.min(5, 2 + fpWave);
  for (let i = 0; i < count; i++) {
    const s = spots[i % spots.length];
    spawnFpMonster(s[0] + (Math.random() - 0.5) * 0.6, s[1] + (Math.random() - 0.5) * 0.6);
  }
}
spawnWave();

const fpsWrap = document.getElementById("fps-wrap");
let fpDragging = false, fpLastX = 0;
fpsWrap.addEventListener("mousedown", e => {
  if (activeMode !== "fps") return;
  if (document.pointerLockElement === fpsWrap) {
    fireFpWeapon();
  } else {
    if (fpsWrap.requestPointerLock) fpsWrap.requestPointerLock();
    fpDragging = true; fpLastX = e.clientX;
    fireFpWeapon();
  }
});
window.addEventListener("mousemove", e => {
  if (activeMode !== "fps") return;
  if (document.pointerLockElement === fpsWrap) {
    fpPlayer.yaw += e.movementX * 0.0028;
  } else if (fpDragging) {
    fpPlayer.yaw += (e.clientX - fpLastX) * 0.005;
    fpLastX = e.clientX;
  }
});
window.addEventListener("mouseup", () => { fpDragging = false; });
window.addEventListener("keydown", e => {
  if (activeMode === "fps") {
    if (e.code === "Digit1") fpPlayer.weapon = 1;
    if (e.code === "Digit2") fpPlayer.weapon = 2;
    if (e.code === "Space" && fpPlayer.z <= 0.01) { fpPlayer.vz = 4.2; e.preventDefault(); }
  }
});

document.getElementById("btn-fps-spawn").addEventListener("click", () => {
  spawnFpMonster(8.0 + (Math.random() - 0.5) * 5, 4.0 + (Math.random() - 0.5) * 3);
  playSfx("roar");
});
document.getElementById("btn-fps-nuke").addEventListener("click", () => {
  fpMonsters.forEach(m => {
    if (!m.dead) { m.dead = true; m.state = "gib_death"; m.animF = 0; fpPlayer.frags++; }
  });
  playSfx("gib");
});

function damageMonster(m, dmg, forceGib) {
  if (m.dead) return;
  m.hp -= dmg;
  if (m.hp <= 0 || forceGib) {
    m.dead = true;
    m.state = "gib_death";
    m.animF = 0;
    fpPlayer.frags++;
    playSfx("gib");
  } else {
    m.state = "pain";
    m.animF = 0;
    m.aiTimer = 0.40;
  }
}

function fireFpWeapon() {
  if (fpPlayer.recoil > 0.08) return;
  fpPlayer.recoil = fpPlayer.weapon === 1 ? 0.34 : 0.48;
  fpPlayer.muzzle = 0.09;
  if (fpPlayer.weapon === 1) {
    playSfx("shotgun");
    // Hitscan cone against monsters
    let bestM = null, bestDist = 999;
    fpMonsters.forEach(m => {
      if (m.dead) return;
      const dx = m.x - fpPlayer.x, dy = m.y - fpPlayer.y;
      const dist = Math.hypot(dx, dy);
      const ang = Math.atan2(dy, dx);
      let diff = Math.atan2(Math.sin(ang - fpPlayer.yaw), Math.cos(ang - fpPlayer.yaw));
      if (Math.abs(diff) < 0.16 + 0.35 / Math.max(dist, 0.8) && dist < bestDist) {
        bestDist = dist; bestM = m;
      }
    });
    if (bestM) {
      const dmg = bestDist < 3.2 ? 125 : 65;
      damageMonster(bestM, dmg, dmg >= 120);
    }
  } else {
    playSfx("rocket");
    fpRockets.push({
      x: fpPlayer.x + Math.cos(fpPlayer.yaw) * 0.4,
      y: fpPlayer.y + Math.sin(fpPlayer.yaw) * 0.4,
      vx: Math.cos(fpPlayer.yaw) * 11.5,
      vy: Math.sin(fpPlayer.yaw) * 11.5,
      life: 2.5
    });
  }
}

function renderFps(dt) {
  const cv = document.getElementById("fps-cv");
  const rect = cv.parentElement.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  if (cv.width !== Math.floor(rect.width * dpr) || cv.height !== Math.floor(rect.height * dpr)) {
    cv.width = Math.floor(rect.width * dpr); cv.height = Math.floor(rect.height * dpr);
  }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = rect.width, H = rect.height;

  // Player movement
  const fwdX = Math.cos(fpPlayer.yaw), fwdY = Math.sin(fpPlayer.yaw);
  const rgtX = -fwdY, rgtY = fwdX;
  let mx = 0, my = 0;
  if (keys["KeyW"] || keys["ArrowUp"]) { mx += fwdX; my += fwdY; }
  if (keys["KeyS"] || keys["ArrowDown"]) { mx -= fwdX; my -= fwdY; }
  if (keys["KeyD"]) { mx += rgtX; my += rgtY; }
  if (keys["KeyA"]) { mx -= rgtX; my -= rgtY; }
  if (keys["ArrowLeft"]) fpPlayer.yaw -= dt * 2.2;
  if (keys["ArrowRight"]) fpPlayer.yaw += dt * 2.2;
  if (mx !== 0 || my !== 0) {
    const len = Math.hypot(mx, my);
    const spd = 4.6 * dt;
    const nx = fpPlayer.x + (mx / len) * spd;
    const ny = fpPlayer.y + (my / len) * spd;
    if (!isWall(nx, fpPlayer.y)) fpPlayer.x = nx;
    if (!isWall(fpPlayer.x, ny)) fpPlayer.y = ny;
  }
  fpPlayer.z += fpPlayer.vz * dt;
  if (fpPlayer.z > 0) fpPlayer.vz -= 11.5 * dt;
  else { fpPlayer.z = 0; fpPlayer.vz = 0; }
  fpPlayer.recoil = Math.max(0, fpPlayer.recoil - dt);
  fpPlayer.muzzle = Math.max(0, fpPlayer.muzzle - dt);
  fpPlayer.hurtFlash = Math.max(0, fpPlayer.hurtFlash - dt * 2.2);

  // Rockets update
  for (let i = fpRockets.length - 1; i >= 0; i--) {
    const r = fpRockets[i];
    r.x += r.vx * dt; r.y += r.vy * dt; r.life -= dt;
    let boom = isWall(r.x, r.y) || r.life <= 0;
    fpMonsters.forEach(m => {
      if (!m.dead && Math.hypot(m.x - r.x, m.y - r.y) < 0.75) boom = true;
    });
    if (boom) {
      fpMonsters.forEach(m => {
        const d = Math.hypot(m.x - r.x, m.y - r.y);
        if (!m.dead && d < 2.6) damageMonster(m, 160, true);
      });
      fpRockets.splice(i, 1);
    }
  }

  // Update AI Monsters
  let aliveCount = 0;
  for (let i = fpMonsters.length - 1; i >= 0; i--) {
    const m = fpMonsters[i];
    if (m.dead) {
      m.animF += dt * 60;
      if (m.animF >= 47) {
        m.animF = 47;
        m.removeTimer += dt;
        if (m.removeTimer > 3.5) fpMonsters.splice(i, 1);
      }
      continue;
    }
    aliveCount++;
    const dx = fpPlayer.x - m.x, dy = fpPlayer.y - m.y;
    const dist = Math.hypot(dx, dy);
    const toPlayerYaw = Math.atan2(dy, dx);

    m.aiTimer -= dt;
    if (m.state === "pain") {
      m.animF += dt * 60;
      if (m.animF >= 24) { m.state = "charge"; m.animF = 0; m.aiTimer = 1.6; }
    } else if (m.state === "jump_slam") {
      m.animF += dt * 60;
      const step = 5.4 * dt;
      const nx = m.x + Math.cos(m.yaw) * step, ny = m.y + Math.sin(m.yaw) * step;
      if (!isWall(nx, m.y)) m.x = nx;
      if (!isWall(m.x, ny)) m.y = ny;
      if (Math.floor(m.animF) === 45) {
        playSfx("slam");
        if (dist < 1.9) { fpPlayer.hp = Math.max(0, fpPlayer.hp - 18); fpPlayer.hurtFlash = 0.55; }
      }
      if (m.animF >= 54) { m.state = "cruise"; m.animF = 0; m.aiTimer = 1.2; }
    } else if (m.state === "whirlwind_melee") {
      m.animF += dt * 60;
      if (Math.floor(m.animF) === 18 && dist < 1.65) {
        fpPlayer.hp = Math.max(0, fpPlayer.hp - 14); fpPlayer.hurtFlash = 0.45;
      }
      if (m.animF >= 36) { m.state = "cruise"; m.animF = 0; m.aiTimer = 1.0; }
    } else if (m.state === "wheelie_taunt") {
      m.yaw = toPlayerYaw;
      m.animF += dt * 60;
      if (m.animF >= 36) { m.state = "charge"; m.animF = 0; m.aiTimer = 1.8; }
    } else {
      // Steer smoothly toward player with slight circle-strafe weave so viewer sees all 16 angles!
      const weave = Math.sin(performance.now() * 0.0018 + i * 2.1) * (m.state === "cruise" ? 0.55 : 0.18);
      const want = toPlayerYaw + weave;
      let diff = Math.atan2(Math.sin(want - m.yaw), Math.cos(want - m.yaw));
      m.yaw += diff * Math.min(1, dt * 5.0);
      const spd = (m.state === "charge" ? 3.8 : 2.2) * dt;
      const nx = m.x + Math.cos(m.yaw) * spd, ny = m.y + Math.sin(m.yaw) * spd;
      if (!isWall(nx, m.y)) m.x = nx; else m.yaw += 1.2;
      if (!isWall(m.x, ny)) m.y = ny;
      m.animF = (m.animF + dt * 60) % animMap[m.state].frames;

      if (dist < 1.35) {
        m.state = "whirlwind_melee"; m.animF = 0; playSfx("whirl");
      } else if (m.aiTimer <= 0) {
        if (dist > 2.2 && dist < 6.8 && Math.random() < 0.52) {
          m.yaw = toPlayerYaw;
          m.state = "jump_slam"; m.animF = 0; playSfx("vault");
        } else if (m.state === "cruise") {
          m.state = Math.random() < 0.4 ? "wheelie_taunt" : "charge";
          m.animF = 0; m.aiTimer = 1.8;
          playSfx("roar");
        } else {
          m.state = "cruise"; m.aiTimer = 1.5;
        }
      }
    }
  }
  if (aliveCount === 0 && fpMonsters.length === 0) {
    fpWave++;
    if (fpPlayer.hp <= 0) fpPlayer.hp = 100;
    spawnWave();
  }
  if (fpPlayer.hp <= 0) fpPlayer.hp = 100;

  // Raycast 3D Quake Dungeon Walls + Z-Buffer!
  const horizon = H * 0.5 + fpPlayer.z * 28;
  const ceilGrad = ctx.createLinearGradient(0, 0, 0, horizon);
  ceilGrad.addColorStop(0, "#090c12"); ceilGrad.addColorStop(1, "#1e1611");
  ctx.fillStyle = ceilGrad; ctx.fillRect(0, 0, W, horizon);

  const flrGrad = ctx.createLinearGradient(0, horizon, 0, H);
  flrGrad.addColorStop(0, "#1c1510"); flrGrad.addColorStop(1, "#3b2c20");
  ctx.fillStyle = flrGrad; ctx.fillRect(0, horizon, W, H - horizon);

  const nCols = Math.min(320, Math.floor(W / 2));
  const colW = W / nCols;
  const zBuf = new Float32Array(nCols);
  const fov = 1.08;

  for (let c = 0; c < nCols; c++) {
    const camX = (c / nCols) * 2 - 1;
    const rayAng = fpPlayer.yaw + Math.atan(camX * Math.tan(fov * 0.5));
    const rdx = Math.cos(rayAng), rdy = Math.sin(rayAng);
    let mapX = Math.floor(fpPlayer.x), mapY = Math.floor(fpPlayer.y);
    const ddx = Math.abs(1 / (rdx || 1e-6)), ddy = Math.abs(1 / (rdy || 1e-6));
    let stepX, sideDistX, stepY, sideDistY;
    if (rdx < 0) { stepX = -1; sideDistX = (fpPlayer.x - mapX) * ddx; }
    else { stepX = 1; sideDistX = (mapX + 1.0 - fpPlayer.x) * ddx; }
    if (rdy < 0) { stepY = -1; sideDistY = (fpPlayer.y - mapY) * ddy; }
    else { stepY = 1; sideDistY = (mapY + 1.0 - fpPlayer.y) * ddy; }

    let hit = "0", side = 0;
    for (let iter = 0; iter < 32; iter++) {
      if (sideDistX < sideDistY) { sideDistX += ddx; mapX += stepX; side = 0; }
      else { sideDistY += ddy; mapY += stepY; side = 1; }
      if (mapX < 0 || mapY < 0 || mapX >= MAP_SIZE || mapY >= MAP_SIZE) { hit = "1"; break; }
      hit = QMAP[mapY][mapX];
      if (hit !== "0") break;
    }
    const rawDist = side === 0 ? (sideDistX - ddx) : (sideDistY - ddy);
    const perpDist = Math.max(0.15, rawDist * Math.cos(rayAng - fpPlayer.yaw));
    zBuf[c] = perpDist;

    const wallH = (H * 0.88) / perpDist;
    const y0 = horizon - wallH * 0.5;
    const shade = Math.max(0.16, Math.min(1.0, 1.35 / (1 + perpDist * 0.22))) * (side === 1 ? 0.76 : 1.0);
    const wallX = side === 0 ? (fpPlayer.y + rawDist * rdy) : (fpPlayer.x + rawDist * rdx);
    const mortar = ((wallX % 1 + 1) % 1 < 0.06) ? 0.72 : 1.0;
    const s = shade * mortar;
    if (hit === "2") {
      ctx.fillStyle = `rgb(${Math.round(92 * s)},${Math.round(108 * s)},${Math.round(72 * s)})`;
    } else {
      ctx.fillStyle = `rgb(${Math.round(108 * s)},${Math.round(82 * s)},${Math.round(62 * s)})`;
    }
    ctx.fillRect(c * colW, y0, colW + 0.8, wallH);
  }

  // Project & Depth-Sort Monsters + Rockets!
  const sprites3d = [];
  fpMonsters.forEach(m => {
    const dx = m.x - fpPlayer.x, dy = m.y - fpPlayer.y;
    const depth = dx * fwdX + dy * fwdY;
    const sideX = dx * rgtX + dy * rgtY;
    if (depth > 0.25) sprites3d.push({ kind: "monster", depth, sideX, m });
  });
  fpRockets.forEach(r => {
    const dx = r.x - fpPlayer.x, dy = r.y - fpPlayer.y;
    const depth = dx * fwdX + dy * fwdY;
    const sideX = dx * rgtX + dy * rgtY;
    if (depth > 0.2) sprites3d.push({ kind: "rocket", depth, sideX, r });
  });
  sprites3d.sort((a, b) => b.depth - a.depth);

  const focal = (W * 0.5) / Math.tan(fov * 0.5);
  sprites3d.forEach(sp => {
    const sx = W * 0.5 + (sp.sideX / sp.depth) * focal;
    const floorY = horizon + (H * 0.44) / sp.depth;
    if (sp.kind === "rocket") {
      const colIdx = Math.floor((sx / W) * nCols);
      if (colIdx >= 0 && colIdx < nCols && zBuf[colIdx] > sp.depth) {
        const rad = Math.max(4, 24 / sp.depth);
        ctx.fillStyle = "#fbbf24";
        ctx.beginPath(); ctx.arc(sx, horizon, rad, 0, Math.PI * 2); ctx.fill();
      }
      return;
    }

    const m = sp.m;
    // Exact 16-angle billboard calculation matching QuakeC GreenSuit_Customize!
    const viewerAng = Math.atan2(fpPlayer.y - m.y, fpPlayer.x - m.x);
    const relDeg = (((m.yaw - viewerAng) * 180 / Math.PI) % 360 + 360) % 360;
    // When monster faces straight at player (`viewerAng == m.yaw`), relDeg=0 -> d=0 (Front)!
    const d16 = Math.round(relDeg / 22.5) % 16;

    const sprScale = (H * 0.92) / (sp.depth * CELL_H);
    const dw = CELL_W * sprScale;
    const xLeft = sx - dw * 0.5, xRight = sx + dw * 0.5;
    if (xRight < 0 || xLeft > W) return;

    // Clip sprite horizontally against raycast Z-buffer spans so walls occlude monsters cleanly!
    ctx.save();
    ctx.beginPath();
    const cStart = Math.max(0, Math.floor((xLeft / W) * nCols));
    const cEnd = Math.min(nCols - 1, Math.ceil((xRight / W) * nCols));
    let anyVis = false;
    for (let c = cStart; c <= cEnd; c++) {
      if (zBuf[c] > sp.depth - 0.15) {
        ctx.rect(c * colW, 0, colW + 1, H);
        anyVis = true;
      }
    }
    if (anyVis) {
      ctx.clip();
      drawSpriteFrame(ctx, m.state, d16, m.animF, sx, floorY, sprScale);
    }
    ctx.restore();
  });

  // Crosshair + Quake Weapon Viewmodel
  ctx.strokeStyle = "#80f542";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(W * 0.5 - 8, H * 0.5); ctx.lineTo(W * 0.5 + 8, H * 0.5);
  ctx.moveTo(W * 0.5, H * 0.5 - 8); ctx.lineTo(W * 0.5, H * 0.5 + 8);
  ctx.stroke();

  const kickY = fpPlayer.recoil * 68;
  const wx = W * 0.5, wy = H + kickY;
  if (fpPlayer.muzzle > 0) {
    ctx.fillStyle = "rgba(255,214,102,0.75)";
    ctx.beginPath(); ctx.arc(wx, wy - 115, 38, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = fpPlayer.weapon === 1 ? "#334155" : "#475569";
  if (fpPlayer.weapon === 1) {
    // Double-barreled Quake Super Shotgun
    ctx.fillRect(wx - 28, wy - 110, 24, 115);
    ctx.fillRect(wx + 4, wy - 110, 24, 115);
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(wx - 22, wy - 110, 12, 16);
    ctx.fillRect(wx + 10, wy - 110, 12, 16);
  } else {
    // Center Quake Brown/Steel Rocket Launcher
    ctx.fillStyle = "#78350f";
    ctx.fillRect(wx - 24, wy - 125, 48, 130);
    ctx.fillStyle = "#cbd5e1";
    ctx.fillRect(wx - 16, wy - 128, 32, 22);
  }

  if (fpPlayer.hurtFlash > 0) {
    ctx.fillStyle = `rgba(220,20,30,${fpPlayer.hurtFlash * 0.45})`;
    ctx.fillRect(0, 0, W, H);
  }
  document.getElementById("fps-hud").textContent =
    `HP: ${fpPlayer.hp} · Frags: ${fpPlayer.frags} · Wave: ${fpWave} · [${fpPlayer.weapon === 1 ? "Super Shotgun" : "Rocket Launcher"}]`;
}

// ---------------------------------------------------------------------------
// 6. Main 60+ Hz Animation Loop
// ---------------------------------------------------------------------------
let lastTs = performance.now();
function tick(now) {
  const dt = Math.min(0.05, Math.max(0.001, (now - lastTs) / 1000.0));
  lastTs = now;
  if (activeMode === "studio") renderStudio(dt);
  else if (activeMode === "sandbox") renderSandbox(dt);
  else if (activeMode === "fps") renderFps(dt);
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def write_self_contained_html(
    out_html_path: str,
    meta: Dict,
    atlas_paths: Dict[str, str],
    poster_jpg_path: str,
) -> float:
    """Embeds all WebP atlases and turnaround poster as data URIs into a single self-contained HTML."""
    atlas_uris: Dict[str, str] = {}
    for anim_id, p in atlas_paths.items():
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        atlas_uris[anim_id] = f"data:image/webp;base64,{b64}"

    with open(poster_jpg_path, "rb") as f:
        poster_uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")

    html = (
        HTML_TEMPLATE
        .replace("__META_JSON__", json.dumps(meta))
        .replace("__ATLAS_JSON__", json.dumps(atlas_uris))
        .replace("__POSTER_JSON__", json.dumps(poster_uri))
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_html_path)), exist_ok=True)
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return len(html) / (1024.0 * 1024.0)
