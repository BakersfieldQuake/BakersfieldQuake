r"""Self-contained single-file HTML5 Playground & Spherical 360° + Above/Below +
Fire-Wheels + Super-Long Bar & Wheels + Jetpack Hover + High-FPS Driving/Flying Arena + Screaming +
4x Escalating 360° Explosions Inspector for the BakersfieldQuake Wheelman sprite."""

VIEWER_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wheelman — 360° + Above/Below • Fire-Wheels • Super-Long Bar • Jetpack • 4x Explosions</title>
<style>
  :root {
    --bg:#0f1116; --panel:#1a1e28; --panel2:#232936; --ink:#f1f5f9; --dim:#94a3b8;
    --accent:#4ade80; --accent2:#38bdf8; --warn:#fbbf24; --danger:#f43f5e; --orange:#fb923c; --cyan:#22d3ee; --nuke:#e879f9;
  }
  * { box-sizing:border-box; }
  body {
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:9px;
    padding:11px 14px 40px; min-height:100vh;
  }
  header { text-align:center; max-width:980px; }
  h1 { font-size:20px; margin:0 0 3px; font-weight:800; letter-spacing:-0.015em; }
  .sub { color:var(--dim); font-size:12.5px; margin:0; }

  .tabs {
    display:flex; flex-wrap:wrap; gap:6px; justify-content:center;
    width:min(100%, 960px); background:var(--panel); border:1px solid #2e3444;
    border-radius:12px; padding:7px;
  }
  .tab {
    flex:1 1 126px; padding:8px 9px; border-radius:8px; border:1.5px solid #32394a;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12.8px;
    cursor:pointer; transition:all 0.12s ease; text-align:center;
  }
  .tab:hover { border-color:#586584; transform:translateY(-1px); }
  .tab.on-sphere  { background:#143829; border-color:var(--accent); color:#86efac; box-shadow:0 0 14px rgba(74,222,128,0.22); }
  .tab.on-fire    { background:#461b0b; border-color:var(--orange); color:#fed7aa; box-shadow:0 0 16px rgba(251,146,60,0.34); }
  .tab.on-long    { background:#1e2948; border-color:#818cf8; color:#e0e7ff; box-shadow:0 0 15px rgba(129,140,248,0.30); }
  .tab.on-jetpack { background:#0c3442; border-color:var(--cyan); color:#a5f3fc; box-shadow:0 0 16px rgba(34,211,238,0.34); }
  .tab.on-drive   { background:#123047; border-color:var(--accent2); color:#7dd3fc; box-shadow:0 0 14px rgba(56,189,248,0.22); }
  .tab.on-scream  { background:#3b2514; border-color:var(--warn); color:#fde68a; box-shadow:0 0 14px rgba(251,191,36,0.22); }
  .tab.on-boom    { background:#461220; border-color:var(--danger); color:#fda4af; box-shadow:0 0 18px rgba(244,63,94,0.32); }

  /* 4 Escalating Explosion Tier Selector Bar */
  .tier-bar {
    display:flex; flex-wrap:wrap; gap:7px; justify-content:center;
    width:min(100%, 940px); background:#18141c; border:1.5px solid #452336;
    border-radius:11px; padding:7px 9px;
  }
  .tier-bar.hidden { display:none; }
  .t-btn {
    flex:1 1 155px; padding:8px 10px; border-radius:8px; border:1.5px solid #382c40;
    background:#241d29; color:#e2e8f0; font:inherit; font-weight:800; font-size:12.5px;
    cursor:pointer; transition:all 0.12s;
  }
  .t-btn:hover { transform:translateY(-1px); border-color:#7c5b8c; }
  .t-btn.t1.on { background:#451822; border-color:#f43f5e; color:#fecdd3; box-shadow:0 0 14px rgba(244,63,94,0.35); }
  .t-btn.t2.on { background:#47210c; border-color:#fb923c; color:#fed7aa; box-shadow:0 0 14px rgba(251,146,60,0.38); }
  .t-btn.t3.on { background:#0d3344; border-color:#22d3ee; color:#a5f3fc; box-shadow:0 0 16px rgba(34,211,238,0.42); }
  .t-btn.t4.on { background:#3e1047; border-color:#e879f9; color:#fae8ff; box-shadow:0 0 20px rgba(232,121,249,0.52); }
  .t-btn.chain.on { background:#1e3a29; border-color:var(--accent); color:#bbf7d0; }

  /* Stage */
  #stage-box {
    width:min(100%, 940px); height:min(63vh, 515px); min-height:370px;
    border-radius:14px; border:1px solid #343b4d; position:relative;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    user-select:none; touch-action:none; cursor:grab;
  }
  #stage-box.drag { cursor:grabbing; }
  #stage-box.checker { background:repeating-conic-gradient(#282c36 0% 25%, #1e222b 0% 50%) 0 0/24px 24px; }
  #stage-box.quake   { background:radial-gradient(circle at 50% 72%, #3f2e21 0%, #1d1510 70%, #0b0908 100%); }
  #stage-box.slate   { background:radial-gradient(circle at 50% 58%, #1e293b 0%, #0f172a 85%); }
  #stage-box.light   { background:#cbd5e1; }

  #sprite-wrap {
    position:relative; height:94%; aspect-ratio:320/304;
    display:flex; align-items:center; justify-content:center;
  }
  #sprite-img {
    width:100%; height:100%; object-fit:contain; pointer-events:none;
    transform-origin:50% 50%; will-change:transform;
  }
  #boom-canvas {
    width:min(100%, 820px); height:auto; max-height:98%; aspect-ratio:640/440;
    display:none; pointer-events:none; will-change:transform;
  }
  #arena-canvas {
    width:100%; height:100%; display:none; object-fit:cover;
  }

  #badge {
    position:absolute; top:11px; left:14px; background:rgba(10,13,20,0.88);
    border:1px solid #3c4458; border-radius:8px; padding:6px 12px;
    font-size:13.5px; font-weight:800; color:var(--accent); pointer-events:none; backdrop-filter:blur(6px); z-index:5;
  }
  #meta-badge {
    position:absolute; top:11px; right:14px; background:rgba(10,13,20,0.85);
    border:1px solid #3c4458; border-radius:8px; padding:5px 11px;
    font-size:12px; color:var(--dim); pointer-events:none; font-variant-numeric:tabular-nums; z-index:5;
  }
  #draghint {
    position:absolute; bottom:9px; right:14px; background:rgba(10,13,20,0.84);
    border:1px solid #2e3545; border-radius:6px; padding:4px 10px;
    font-size:12px; color:#cbd5e1; pointer-events:none; z-index:5;
  }

  .row {
    display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:center;
    width:min(100%, 940px); background:var(--panel); border:1px solid #2c3242;
    border-radius:10px; padding:8px 12px;
  }
  .row.hidden { display:none; }
  button.btn {
    background:var(--accent); color:#091510; border:0; border-radius:7px;
    padding:7px 11px; font:inherit; font-weight:700; font-size:12.5px; cursor:pointer;
  }
  button.btn.blue   { background:var(--accent2); color:#062235; }
  button.btn.orange { background:var(--orange); color:#271002; }
  button.btn.indigo { background:#818cf8; color:#11132e; }
  button.btn.cyan   { background:var(--cyan); color:#04242c; }
  button.btn.warn   { background:var(--warn); color:#241703; }
  button.btn.danger { background:var(--danger); color:#fff; box-shadow:0 0 12px rgba(244,63,94,0.35); }
  button.btn.alt    { background:#303748; color:var(--ink); font-weight:600; }
  button.btn.alt.on { background:#475569; outline:2px solid var(--accent); color:#fff; }
  label { color:var(--dim); display:flex; gap:5px; align-items:center; font-size:12.5px; font-weight:600; }
  input[type=range] { accent-color:var(--accent); cursor:pointer; }
  .val-pill {
    display:inline-block; min-width:46px; text-align:center; background:#12151c;
    border:1px solid #32394a; border-radius:5px; padding:1px 5px; color:var(--accent);
    font-variant-numeric:tabular-nums; font-size:12px;
  }

  .section-lbl { width:min(100%, 940px); font-size:11.5px; font-weight:700; color:var(--dim); text-transform:uppercase; letter-spacing:0.06em; margin:2px 0 -4px; padding-left:4px; }
  #pitch-strip { display:grid; grid-template-columns:repeat(5, 1fr); gap:7px; width:min(100%, 940px); }
  @media (max-width:700px) { #pitch-strip { grid-template-columns:repeat(3, 1fr); } }
  .p-card {
    background:var(--panel); border:2px solid #2d3444; border-radius:9px; padding:5px;
    display:flex; flex-direction:column; align-items:center; gap:3px; cursor:pointer;
    color:var(--dim); font-size:11.5px; font-weight:700; transition:border-color 0.12s;
  }
  .p-card:hover { border-color:#566380; }
  .p-card.on { border-color:var(--accent2); color:var(--ink); background:#232b3b; }
  .p-card img { width:100%; max-height:74px; aspect-ratio:320/304; object-fit:contain; display:block; }

  #yaw-strip { display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%, 940px); }
  @media (max-width:700px) { #yaw-strip { grid-template-columns:repeat(4, 1fr); } }
  .y-card {
    background:var(--panel); border:2px solid #2d3444; border-radius:8px; padding:4px;
    display:flex; flex-direction:column; align-items:center; gap:2px; cursor:pointer;
    color:var(--dim); font-size:11px; font-weight:700;
  }
  .y-card.on { border-color:var(--accent); color:var(--ink); background:#242c3a; }
  .y-card img { width:100%; aspect-ratio:320/304; object-fit:contain; display:block; }

  details {
    width:min(100%, 940px); background:var(--panel); border:1px solid #2c3242;
    border-radius:10px; padding:10px 14px;
  }
  summary { cursor:pointer; font-weight:700; color:var(--accent2); user-select:none; }
  #boom-grid { display:grid; grid-template-columns:repeat(7, 1fr); gap:5px; margin-top:10px; }
  @media (max-width:720px) { #boom-grid { grid-template-columns:repeat(4, 1fr); } }
  .b-cell {
    background:#151821; border:1px solid #2f3646; border-radius:6px; padding:3px;
    text-align:center; cursor:pointer;
  }
  .b-cell:hover { border-color:var(--danger); }
  .b-cell canvas { width:100%; aspect-ratio:640/440; display:block; border-radius:4px; }
  .b-cell span { font-size:10px; color:var(--dim); font-variant-numeric:tabular-nums; }
</style>
</head>
<body>
  <header>
    <h1>Wheelman &mdash; Spherical 360&deg; + Above/Below &bull; Fire-Wheels &bull; Super-Long Bar &amp; Wheels &bull; Jetpack Hover &bull; 4x Explosions</h1>
    <p class="sub">100% Self-Contained Single HTML &bull; Drag Left/Right (360&deg;) &amp; Up/Down (Above/Below) LIVE Inside Every Stunt &amp; Explosion! &bull; Synced with <code>progs/wheelman.spr32</code> (792 Frames)</p>
  </header>

  <!-- 7 Primary Interactive Modes -->
  <div class="tabs">
    <button class="tab on-sphere" id="tab-sphere">&#x1F310; 360&deg; + Above/Below</button>
    <button class="tab" id="tab-fire">&#x1F525; Fire-Wheels Burnout</button>
    <button class="tab" id="tab-long">&#x1F4CF; Super-Long Bar &amp; Wheels</button>
    <button class="tab" id="tab-jetpack">&#x1F680; Jetpack + Spinning Bar</button>
    <button class="tab" id="tab-drive">&#x1F3CE;&#xFE0F; Driving &amp; Jetpack Arena</button>
    <button class="tab" id="tab-scream">&#x1F631; Screaming (360&deg;)</button>
    <button class="tab" id="tab-boom">&#x1F4A5; 4x 360&deg; Explosions</button>
  </div>

  <!-- 4 Escalating 360° Explosion Selector Bar -->
  <div class="tier-bar hidden" id="tier-bar">
    <button class="t-btn t1 on" id="tbtn-1">&#x1F4A5; 1: Classic Overload (84f)</button>
    <button class="t-btn t2" id="tbtn-2">&#x1F525; 2: Napalm Cluster (108f)</button>
    <button class="t-btn t3" id="tbtn-3">&#x26A1; 3: Tesla X-Ray Tornado (132f)</button>
    <button class="t-btn t4" id="tbtn-4">&#x2622;&#xFE0F; 4: THERMONUCLEAR CATACLYSM (168f)</button>
    <button class="t-btn chain on" id="btn-escalate">&#x1F680; Auto-Escalate 1&rarr;2&rarr;3&rarr;4: ON</button>
  </div>

  <!-- Stage -->
  <div id="stage-box" class="quake">
    <div id="badge">0&deg; Front &bull; Eye-Level</div>
    <div id="meta-badge">24 FPS &bull; d=0 f=0/11</div>
    <div id="sprite-wrap">
      <img id="sprite-img" alt="Wheelman sprite frame">
    </div>
    <canvas id="boom-canvas" width="640" height="440"></canvas>
    <canvas id="arena-canvas" width="940" height="515"></canvas>
    <div id="draghint">&#x2194; Drag Left/Right: 360&deg; Yaw &nbsp;&bull;&nbsp; &#x2195; Drag Up/Down: Above &amp; Below!</div>
  </div>

  <!-- Spherical / Scream Controls -->
  <div class="row" id="ctrl-sphere">
    <button class="btn" id="btn-play">Pause</button>
    <button class="btn blue" id="btn-tour">3D Spherical Tour: ON</button>
    <button class="btn alt" id="btn-idle">Idle: OFF</button>
    <label>FPS <input id="rng-fps" type="range" min="8" max="60" value="24" style="width:82px"><span class="val-pill" id="lbl-fps">24 fps</span></label>
    <label>Zoom <input id="rng-zoom" type="range" min="85" max="200" value="100" style="width:70px"></label>
    <button class="btn orange" id="btn-quick-fire">&#x1F525; Fire-Wheels</button>
    <button class="btn indigo" id="btn-quick-long">&#x1F4CF; Long Bar</button>
    <button class="btn cyan" id="btn-quick-jet">&#x1F680; Jetpack</button>
    <button class="btn warn" id="btn-quick-scream">&#x1F631; Scream!</button>
    <button class="btn danger" id="btn-quick-boom">&#x1F4A5; 4x Explosions</button>
    <button class="btn alt" id="btn-bg">BG: Quake</button>
    <button class="btn alt" id="btn-sfx">&#x1F50A; SFX: ON</button>
  </div>

  <!-- 360° + Above/Below Stunt Controls (Fire-Wheels / Super-Long Bar & Wheels / Jetpack Hover + Spinning Bar) -->
  <div class="row hidden" id="ctrl-stunt">
    <button class="btn" id="btn-stunt-play">Pause</button>
    <button class="btn blue" id="btn-stunt-orbit">&#x1F504; 360&deg; Stunt Orbit: ON</button>

    <span id="grp-fire" style="display:inline-flex;gap:8px;align-items:center;flex-wrap:wrap">
      <label>Wheel Spin &amp; Heat <input id="rng-fire-spd" type="range" min="2" max="10" step="0.5" value="5.5" style="width:95px"><span class="val-pill" id="lbl-fire-spd">5.5x</span></label>
      <button class="btn orange" id="btn-nitrous">&#x1F525; 88-MPH NITROUS BURST!</button>
    </span>

    <span id="grp-long" style="display:none;gap:8px;align-items:center;flex-wrap:wrap">
      <button class="btn indigo" id="btn-long-auto">Auto-Telescope Wave: ON</button>
      <label>Bar &amp; Wheel Length <input id="rng-long-len" type="range" min="1.0" max="4.0" step="0.05" value="2.80" style="width:110px"><span class="val-pill" id="lbl-long-len">2.80x</span></label>
    </span>

    <span id="grp-jet" style="display:none;gap:8px;align-items:center;flex-wrap:wrap">
      <label>Hover Altitude <input id="rng-jp-alt" type="range" min="25" max="140" value="84" style="width:90px"><span class="val-pill" id="lbl-jp-alt">84 px</span></label>
      <label>Bar &amp; Wheel Spin <input id="rng-jp-spd" type="range" min="0.5" max="6.0" step="0.25" value="2.5" style="width:90px"><span class="val-pill" id="lbl-jp-spd">2.5x</span></label>
      <button class="btn cyan" id="btn-afterburn">&#x1F680; AFTERBURNER BOOST!</button>
    </span>

    <label>Zoom <input id="rng-stunt-zoom" type="range" min="80" max="175" value="100" style="width:70px"></label>
    <button class="btn alt" id="btn-stunt-bg">BG: Quake</button>
    <button class="btn alt" id="btn-sfx-stunt">&#x1F50A; SFX: ON</button>
  </div>

  <!-- Driving & Flying Arena Controls -->
  <div class="row hidden" id="ctrl-drive">
    <button class="btn blue" id="btn-autodrive">&#x1F916; Auto-Drive: ON</button>
    <button class="btn alt on" id="cam-track">&#x1F3A5; 3D Track</button>
    <button class="btn alt" id="cam-above">&#x1F681; Above (+90&deg;)</button>
    <button class="btn alt" id="cam-below">&#x1F573;&#xFE0F; Below (-90&deg;)</button>
    <button class="btn orange" id="btn-drv-fire">&#x1F525; Fire-Wheels (F)</button>
    <button class="btn indigo" id="btn-drv-long">&#x1F4CF; Long-Bar (L)</button>
    <button class="btn cyan" id="btn-drv-jet">&#x1F680; Jetpack (J)</button>
    <button class="btn warn" id="btn-drv-scream">&#x1F631; Scream (C)</button>
    <button class="btn danger" id="btn-drv-boom">&#x1F4A5; EXPLODE! (E)</button>
    <button class="btn alt on" id="btn-drv-cycle">Auto-Stunts &amp; Finale: ON</button>
    <button class="btn alt" id="btn-sfx2">&#x1F50A; SFX: ON</button>
  </div>

  <!-- 360° Multi-Tier Explosion Cinema Controls -->
  <div class="row hidden" id="ctrl-boom">
    <button class="btn danger" id="btn-boom-play">Pause</button>
    <button class="btn blue" id="btn-boom-orbit">&#x1F504; 360&deg; Bullet-Time Orbit: ON</button>
    <button class="btn alt" id="btn-boom-prev">&laquo; -1f</button>
    <button class="btn alt" id="btn-boom-next">+1f &raquo;</button>
    <label>Frame <input id="rng-boom" type="range" min="0" max="83" value="0" style="width:155px"><span class="val-pill" id="lbl-boom-f">0 / 83</span></label>
    <label>FPS <input id="rng-boom-fps" type="range" min="6" max="60" value="24" style="width:80px"><span class="val-pill" id="lbl-boom-fps">24 fps</span></label>
    <button class="btn alt" id="act1">Act 1: Scream</button>
    <button class="btn alt" id="act2">Act 2: Overload</button>
    <button class="btn alt" id="act3">Act 3: DETONATE</button>
    <button class="btn alt" id="act4">Act 4: Chaos</button>
    <button class="btn alt" id="act5">Act 5: Aftermath</button>
    <button class="btn alt" id="btn-sfx3">&#x1F50A; SFX: ON</button>
  </div>

  <!-- 5-Level Vertical Pitch Strip -->
  <div class="section-lbl">Vertical Camera Elevation (Above Him &bull; Eye-Level &bull; Below Him) &mdash; Works Live in 360&deg; &amp; All 4 Explosions!</div>
  <div id="pitch-strip"></div>

  <!-- 8-Angle Horizontal 360° Strip -->
  <div class="section-lbl">Horizontal 360&deg; Camera Angle (0&deg;..315&deg;) &mdash; Click Any Angle or Drag Left/Right on Stage</div>
  <div id="yaw-strip"></div>

  <details id="story-details">
    <summary id="story-summary">Inspect 360&deg; Explosion Keyframe Storyboard (Updates for Selected Explosion 1&ndash;4 &amp; Angle!)</summary>
    <div id="boom-grid"></div>
  </details>

<script>
const DIRS = 8, FRAMES = 12;
const DIR_LABELS = [
  "0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left",
  "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"
];
const PITCH_LABELS = [
  "+90° Directly Above Him",
  "+45° High-Angle Above",
  "0° Eye-Level (360°)",
  "-45° Worm's-Eye Below",
  "-90° Directly Below Him"
];

const TIER_INFO = {
  1: { name: "💥 Boom 1: Classic Core Overload", nFrames: 84,  detF: 30, act4F: 40, act5F: 62, nGibs: 24,  velM: 1.00 },
  2: { name: "🔥 Boom 2: Napalm Cluster Rampage", nFrames: 108, detF: 30, act4F: 44, act5F: 80, nGibs: 52,  velM: 1.32 },
  3: { name: "⚡ Boom 3: Tesla X-Ray Plasma Tornado", nFrames: 132, detF: 34, act4F: 42, act5F: 96, nGibs: 84,  velM: 1.48 },
  4: { name: "☢️ Boom 4: THERMONUCLEAR CATACLYSM", nFrames: 168, detF: 38, act4F: 50, act5F: 134, nGibs: 140, velM: 1.85 }
};

const IDLE_B64    = __IDLE_JSON__;
const ROLL_B64    = __ROLL_JSON__;
const SCREAM_B64  = __SCREAM_JSON__;
const ABOVE90_B64 = __ABOVE90_JSON__;
const ABOVE45_B64 = __ABOVE45_JSON__;
const BELOW45_B64 = __BELOW45_JSON__;
const BELOW90_B64 = __BELOW90_JSON__;
const PARTS_B64   = __PARTS360_JSON__;
const VFX_B64     = __VFX_JSON__;
const STUNTS_B64  = __STUNTS_JSON__;

function preloadImg(src) { const im = new Image(); im.src = src; return im; }
function preloadList(list) { return list.map(preloadImg); }

const IMG_ROLL      = ROLL_B64.map(preloadList);
const IMG_SCREAM    = SCREAM_B64.map(preloadList);
const IMG_ABOVE90   = preloadList(ABOVE90_B64.roll);
const IMG_ABOVE90_S = preloadList(ABOVE90_B64.scream);
const IMG_ABOVE45   = preloadList(ABOVE45_B64.roll);
const IMG_ABOVE45_S = preloadList(ABOVE45_B64.scream);
const IMG_BELOW45   = preloadList(BELOW45_B64.roll);
const IMG_BELOW45_S = preloadList(BELOW45_B64.scream);
const IMG_BELOW90   = preloadList(BELOW90_B64.roll);

const P360 = {
  heads:  preloadList(PARTS_B64.heads),
  wheels: preloadList(PARTS_B64.wheels),
  bars:   preloadList(PARTS_B64.bars),
  llegs:  preloadList(PARTS_B64.llegs),
  rlegs:  preloadList(PARTS_B64.rlegs),
  xrays:  preloadList(PARTS_B64.xrays),
  xrayAbove: preloadImg(PARTS_B64.xray_above90),
  gibs:   preloadList(PARTS_B64.gibs),
  cap:    preloadImg(PARTS_B64.shrap_cap),
  nut:    preloadImg(PARTS_B64.shrap_nut),
};
const VFX_IMGS = {
  fire:   preloadImg(VFX_B64.fire),
  napalm: preloadImg(VFX_B64.napalm),
  plasma: preloadImg(VFX_B64.plasma),
  nuke:   preloadImg(VFX_B64.nuke),
};
const STUNT_IMGS = {
  body:         preloadList(STUNTS_B64.body_only),
  bodyAbove90:  preloadImg(STUNTS_B64.body_above90),
  bodyBelow90:  preloadImg(STUNTS_B64.body_below90),
  jetpacks:     preloadList(STUNTS_B64.jetpacks),
  jetpackAbove: preloadImg(STUNTS_B64.jetpack_above),
  jetpackBelow: preloadImg(STUNTS_B64.jetpack_below),
  cSpecs:       STUNTS_B64.c_specs,
};

// =========================================================================
// Procedural WebAudio Sound Synthesizer (Escalating SFX per Tier 1..4!)
// =========================================================================
let audioCtx = null, sfxOn = true;
function ensureAudio() {
  if (!sfxOn) return null;
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
  return audioCtx;
}
window.addEventListener("pointerdown", ensureAudio, { passive:true });
window.addEventListener("keydown", ensureAudio, { passive:true });

function playScreamSfx(dur = 0.55, pitchMul = 1.0) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator(), osc2 = ctx.createOscillator(), lfo = ctx.createOscillator();
  const lfoGain = ctx.createGain(), g = ctx.createGain(), filt = ctx.createBiquadFilter();
  osc.type = "sawtooth"; osc2.type = "square";
  osc.frequency.setValueAtTime(520 * pitchMul, now);
  osc.frequency.exponentialRampToValueAtTime(820 * pitchMul, now + dur * 0.35);
  osc.frequency.exponentialRampToValueAtTime(420 * pitchMul, now + dur);
  osc2.frequency.setValueAtTime(529 * pitchMul, now);
  osc2.frequency.exponentialRampToValueAtTime(832 * pitchMul, now + dur * 0.35);
  lfo.frequency.value = 28; lfoGain.gain.value = 42;
  lfo.connect(lfoGain); lfoGain.connect(osc.frequency); lfoGain.connect(osc2.frequency);
  filt.type = "bandpass"; filt.frequency.value = 1400; filt.Q.value = 2.2;
  g.gain.setValueAtTime(0.001, now);
  g.gain.linearRampToValueAtTime(0.14, now + 0.04);
  g.gain.exponentialRampToValueAtTime(0.001, now + dur);
  osc.connect(filt); osc2.connect(filt); filt.connect(g); g.connect(ctx.destination);
  osc.start(now); osc2.start(now); lfo.start(now);
  osc.stop(now + dur + 0.02); osc2.stop(now + dur + 0.02); lfo.stop(now + dur + 0.02);
}

function playOverloadWhine(tier = 1) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime, dur = 0.55 + tier * 0.1;
  const osc = ctx.createOscillator(), g = ctx.createGain();
  osc.type = tier === 3 ? "square" : "sawtooth";
  osc.frequency.setValueAtTime(tier === 4 ? 440 : 190, now);
  osc.frequency.exponentialRampToValueAtTime(tier === 4 ? 1680 : 1180, now + dur);
  g.gain.setValueAtTime(0.01, now);
  g.gain.linearRampToValueAtTime(0.13, now + dur * 0.8);
  g.gain.exponentialRampToValueAtTime(0.001, now + dur + 0.05);
  osc.connect(g); g.connect(ctx.destination);
  osc.start(now); osc.stop(now + dur + 0.06);
}

function playExplosionBoom(scale = 1.0, isPlasma = false) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime, dur = Math.min(2.4, 0.85 * scale);
  const bufSz = Math.floor(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, bufSz, ctx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < bufSz; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufSz, 1.25);
  const noise = ctx.createBufferSource(); noise.buffer = buf;
  const filt = ctx.createBiquadFilter(); filt.type = isPlasma ? "bandpass" : "lowpass";
  filt.frequency.setValueAtTime(isPlasma ? 1650 : 1050, now);
  filt.frequency.exponentialRampToValueAtTime(75, now + dur);
  const g = ctx.createGain();
  g.gain.setValueAtTime(Math.min(0.55, 0.30 * scale), now);
  g.gain.exponentialRampToValueAtTime(0.001, now + dur);
  noise.connect(filt); filt.connect(g); g.connect(ctx.destination);
  noise.start(now);

  const sub = ctx.createOscillator(), sg = ctx.createGain();
  sub.type = "sine";
  sub.frequency.setValueAtTime(135, now);
  sub.frequency.exponentialRampToValueAtTime(24, now + 0.55 * scale);
  sg.gain.setValueAtTime(Math.min(0.5, 0.30 * scale), now);
  sg.gain.exponentialRampToValueAtTime(0.001, now + 0.58 * scale);
  sub.connect(sg); sg.connect(ctx.destination);
  sub.start(now); sub.stop(now + 0.6 * scale);
}

function playGibSplat() {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator(), g = ctx.createGain();
  osc.type = "triangle";
  osc.frequency.setValueAtTime(245, now);
  osc.frequency.exponentialRampToValueAtTime(55, now + 0.14);
  g.gain.setValueAtTime(0.16, now);
  g.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
  osc.connect(g); g.connect(ctx.destination);
  osc.start(now); osc.stop(now + 0.16);
}

function playBurnoutSfx(boost = 1.0) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime, dur = 0.55;
  // Screeching tire harmonic + roaring flame whoosh
  const osc = ctx.createOscillator(), g = ctx.createGain();
  osc.type = "sawtooth";
  osc.frequency.setValueAtTime(340 * boost, now);
  osc.frequency.exponentialRampToValueAtTime(920 * boost, now + dur * 0.55);
  osc.frequency.exponentialRampToValueAtTime(580 * boost, now + dur);
  g.gain.setValueAtTime(0.08, now);
  g.gain.exponentialRampToValueAtTime(0.001, now + dur);
  osc.connect(g); g.connect(ctx.destination);
  osc.start(now); osc.stop(now + dur + 0.02);

  const bSz = Math.floor(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, bSz, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < bSz; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bSz, 0.7);
  const ns = ctx.createBufferSource(); ns.buffer = buf;
  const fl = ctx.createBiquadFilter(); fl.type = "bandpass"; fl.frequency.value = 680 * boost; fl.Q.value = 1.1;
  const ng = ctx.createGain(); ng.gain.setValueAtTime(0.16, now); ng.gain.exponentialRampToValueAtTime(0.001, now + dur);
  ns.connect(fl); fl.connect(ng); ng.connect(ctx.destination);
  ns.start(now);
}

function playHydraulicSfx(expanding = true) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime, dur = 0.42;
  const osc = ctx.createOscillator(), osc2 = ctx.createOscillator(), g = ctx.createGain();
  osc.type = "triangle"; osc2.type = "sawtooth";
  osc.frequency.setValueAtTime(expanding ? 140 : 420, now);
  osc.frequency.exponentialRampToValueAtTime(expanding ? 460 : 135, now + dur);
  osc2.frequency.setValueAtTime(expanding ? 280 : 840, now);
  osc2.frequency.exponentialRampToValueAtTime(expanding ? 920 : 270, now + dur);
  g.gain.setValueAtTime(0.09, now);
  g.gain.exponentialRampToValueAtTime(0.001, now + dur);
  osc.connect(g); osc2.connect(g); g.connect(ctx.destination);
  osc.start(now); osc2.start(now); osc.stop(now + dur + 0.02); osc2.stop(now + dur + 0.02);
}

function playJetpackRoarSfx(boost = 1.0) {
  const ctx = ensureAudio(); if (!ctx) return;
  const now = ctx.currentTime, dur = 0.65;
  const bSz = Math.floor(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, bSz, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < bSz; i++) d[i] = (Math.random() * 2 - 1) * (0.65 + 0.35 * Math.sin(i * 0.02));
  const ns = ctx.createBufferSource(); ns.buffer = buf;
  const fl = ctx.createBiquadFilter(); fl.type = "lowpass";
  fl.frequency.setValueAtTime(480 * boost, now);
  fl.frequency.linearRampToValueAtTime(1150 * boost, now + dur * 0.4);
  fl.frequency.exponentialRampToValueAtTime(320, now + dur);
  const ng = ctx.createGain(); ng.gain.setValueAtTime(0.20, now); ng.gain.exponentialRampToValueAtTime(0.002, now + dur);
  ns.connect(fl); fl.connect(ng); ng.connect(ctx.destination);
  ns.start(now);
}

// =========================================================================
// Deterministic 3D (X, Y, Z) Physics Pre-Simulator for All 4 Escalating Tiers!
// Allows instant timeline scrubbing AND real-time 360° + Above/Below orbiting!
// =========================================================================
function mulberry32(a) {
  return function() {
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function precompute3DTier(tier) {
  const cfg = TIER_INFO[tier];
  const nF = cfg.nFrames, detF = cfg.detF, nGibs = cfg.nGibs, vm = cfg.velM;
  const rng = mulberry32(20261101 + tier * 777);
  const rand = (lo, hi) => lo + rng() * (hi - lo);
  const dt = 1 / 24, grav = tier === 4 ? 760 : 860;

  const bodies = [
    { kind:"wheel", side:-1, x:-84, y:54,  z:0,   vx:-178*vm, vy:295*vm, vz:58*vm,  ang:0,  omg:-720*vm, rad:46, bounce:0.65, fire:tier>=2, active:true },
    { kind:"wheel", side: 1, x: 86, y:54,  z:0,   vx: 184*vm, vy:318*vm, vz:-64*vm, ang:0,  omg: 760*vm, rad:46, bounce:0.66, fire:tier>=2, active:true },
    { kind:"bar",   side: 0, x:  4, y:58,  z:18,  vx:  68*vm, vy:380*vm, vz:130*vm, ang:-8, omg:1080*vm, rad:22, bounce:0.52, fire:tier>=2, active:true },
    { kind:"lleg",  side:-1, x:-78, y:142, z:14,  vx:-140*vm, vy:295*vm, vz:-88*vm, ang:0,  omg:-540*vm, rad:28, bounce:0.38, fire:tier>=4, active:true },
    { kind:"rleg",  side: 1, x: 80, y:142, z:14,  vx: 146*vm, vy:285*vm, vz: 94*vm, ang:0,  omg: 520*vm, rad:28, bounce:0.38, fire:tier>=4, active:true },
    { kind:"head",  side: 0, x:  0, y:194, z: 8,  vx:  16,    vy:[0,545,670,615,960][tier], vz:45, ang:0, omg:590, rad:25, bounce:0.52, fire:tier>=2, active:true },
    { kind:"cap",   side: 0, x:  0, y:  0, z: 0,  vx: 215,    vy:235,    vz:165,    ang:0,  omg:1450,    rad:11, bounce:0.58, fire:false,   active:false },
    { kind:"nut",   side:-1, x:  0, y:  0, z: 0,  vx:-240,    vy:195,    vz:-145,   ang:0,  omg:-1650,   rad: 8, bounce:0.62, fire:false,   active:false },
    { kind:"nut",   side: 1, x:  0, y:  0, z: 0,  vx: 170,    vy:275,    vz:-180,   ang:0,  omg:1600,    rad: 8, bounce:0.62, fire:false,   active:false }
  ];

  const gibs = [];
  for (let i = 0; i < nGibs; i++) {
    const az = rand(0, Math.PI * 2), el = rand(0.18, 1.38), sp = rand(165, 470) * vm;
    gibs.push({
      gidx: i % P360.gibs.length,
      x: rand(-22, 22), y: rand(75, 165), z: rand(-22, 22),
      vx: Math.cos(az) * Math.cos(el) * sp,
      vy: Math.sin(el) * sp + (tier === 4 ? 190 : 0),
      vz: Math.sin(az) * Math.cos(el) * sp,
      ang: rand(0, 360), omg: rand(-840, 840), rad: rand(9, 15), bounce: rand(0.28, 0.48),
      volatile: (tier === 2 && i < 5) || (tier === 4 && i < 10), popped: false
    });
  }

  const sparks = [];
  function addSparks(sx, sy, sz, cnt, spHi, col) {
    for (let i = 0; i < cnt; i++) {
      const az = rand(0, Math.PI*2), el = rand(-0.3, 1.3), sp = rand(80, spHi);
      sparks.push({ x:sx, y:sy, z:sz, vx:Math.cos(az)*Math.cos(el)*sp, vy:Math.sin(el)*sp + 80, vz:Math.sin(az)*Math.cos(el)*sp, life:1.0, dec:rand(1.3, 2.6), col });
    }
  }

  const blasts = [], craters = [], frames = [];
  const lim = tier < 3 ? 235 : 275;

  for (let f = 0; f < nF; f++) {
    if (f === detF) {
      if (tier === 1) {
        blasts.push({ f0:f, dur:26, x:0, y:98, z:10, maxR:285, style:"fire" });
        craters.push({ x:0, z:0, r:82, style:"blood", f0:f });
        addSparks(0, 90, 0, 55, 420, "#ffd166");
      } else if (tier === 2) {
        blasts.push({ f0:f,   dur:28, x:0,    y:108, z:12,  maxR:335, style:"napalm" });
        blasts.push({ f0:f+4, dur:26, x:-102, y:85,  z:48,  maxR:270, style:"fire" });
        blasts.push({ f0:f+8, dur:28, x: 106, y:96,  z:-44, maxR:290, style:"napalm" });
        craters.push({ x:0, z:0, r:118, style:"napalm", f0:f });
        addSparks(0, 95, 0, 90, 520, "#ff9f1c");
      } else if (tier === 3) {
        blasts.push({ f0:f, dur:34, x:0, y:138, z:0, maxR:385, style:"plasma" });
        craters.push({ x:0, z:0, r:138, style:"plasma", f0:f });
        addSparks(0, 120, 0, 110, 560, "#38bdf8");
      } else if (tier === 4) {
        blasts.push({ f0:f, dur:105, x:0, y:175, z:0, maxR:470, style:"nuke" });
        craters.push({ x:0, z:0, r:205, style:"magma", f0:f });
        addSparks(0, 130, 0, 150, 680, "#fef08a");
      }
    }

    if (f > detF) {
      const barB = bodies[2];
      // Tier 1 secondary mid-air chrome bar blast at f=44
      if (tier === 1 && f === 44) {
        blasts.push({ f0:f, dur:18, x:barB.x, y:barB.y, z:barB.z, maxR:178, style:"fire" });
        addSparks(barB.x, barB.y, barB.z, 36, 340, "#fde047");
        barB.vx = -130; barB.vy = 155; barB.omg = -1360;
        for (let s = 6; s < 9; s++) { bodies[s].active = true; bodies[s].x = barB.x; bodies[s].y = barB.y; bodies[s].z = barB.z; }
      }
      // Tier 2 rocket-missile chrome bar corkscrews around 3D stage & detonates at f=58!
      if (tier === 2 && f < 58) {
        const ar = f * 0.44;
        barB.vx += Math.cos(ar) * 34; barB.vz += Math.sin(ar) * 34; barB.vy += 26;
        if (f % 2 === 0) addSparks(barB.x, barB.y, barB.z, 4, 150, "#fb923c");
      } else if (tier === 2 && f === 58) {
        blasts.push({ f0:f, dur:24, x:barB.x, y:barB.y, z:barB.z, maxR:255, style:"napalm" });
        addSparks(barB.x, barB.y, barB.z, 55, 440, "#fb923c");
        for (let s = 6; s < 9; s++) { bodies[s].active = true; bodies[s].x = barB.x; bodies[s].y = barB.y; bodies[s].z = barB.z; }
      }

      // Tier 3 roaring 3D Helical Gib & Wheel Tornado (f=36..95) + 6 chain plasma blasts + Sky Thunderbolt Slam at f=96!
      const inTornado = (tier === 3 && f >= 36 && f < 96);
      if (tier === 3 && [46, 55, 64, 73, 82, 90].includes(f)) {
        const ap = f * 0.92;
        blasts.push({ f0:f, dur:16, x:Math.cos(ap)*105, y:100+(f-40)*1.9, z:Math.sin(ap)*105, maxR:195, style:"plasma" });
        addSparks(Math.cos(ap)*105, 110, Math.sin(ap)*105, 28, 380, "#67e8f9");
      }
      if (tier === 3 && f === 96) {
        blasts.push({ f0:f, dur:28, x:0, y:98, z:0, maxR:380, style:"plasma" });
        addSparks(0, 80, 0, 95, 580, "#e879f9");
        for (let s = 6; s < 9; s++) { bodies[s].active = true; bodies[s].x = 0; bodies[s].y = 145; bodies[s].z = 0; }
      }

      // Tier 4 12-Blast Rolling Carpet-Bombing Apocalypse across the 3D floor (f=48..114) + Final Head Mini-Nuke POP at f=152!
      if (tier === 4 && f >= 48 && f <= 114 && (f - 48) % 6 === 0) {
        const idx = (f - 48) / 6, az = idx * 2.15, rr = 70 + (idx % 4) * 58;
        const bx = Math.cos(az) * rr, bz = Math.sin(az) * rr;
        blasts.push({ f0:f, dur:22, x:bx, y:72, z:bz, maxR:235, style:idx % 2 ? "napalm" : "fire" });
        craters.push({ x:bx, z:bz, r:56, style:"magma", f0:f });
        addSparks(bx, 45, bz, 26, 420, "#fde047");
      }
      if (tier === 4 && f === 152) {
        const hb = bodies[5];
        blasts.push({ f0:f, dur:18, x:hb.x, y:hb.y + 24, z:hb.z, maxR:180, style:"fire" });
        addSparks(hb.x, hb.y + 20, hb.z, 40, 360, "#fef08a");
        hb.vy = 235; hb.omg = 980;
      }

      for (const bd of bodies) {
        if (!bd.active) continue;
        if (inTornado && bd.kind !== "head") {
          const swR = 72 + 0.56 * bd.y, curR = Math.max(8, Math.hypot(bd.x, bd.z));
          const tx = -bd.z / curR, tz = bd.x / curR;
          bd.vx = tx * 460 + (swR - curR) * (bd.x / curR) * 6;
          bd.vz = tz * 460 + (swR - curR) * (bd.z / curR) * 6;
          bd.vy = 95 * Math.sin(f * 0.25 + bd.side) + (170 - bd.y) * 2.5;
        } else if (tier === 3 && f === 96) {
          const ao = Math.atan2(bd.z, bd.x + 0.1);
          bd.vx = Math.cos(ao) * 360; bd.vz = Math.sin(ao) * 360; bd.vy = -270;
        } else {
          bd.vy -= grav * dt;
        }
        bd.x += bd.vx * dt; bd.y += bd.vy * dt; bd.z += bd.vz * dt; bd.ang += bd.omg * dt;
        if (bd.y <= bd.rad) {
          bd.y = bd.rad;
          if (Math.abs(bd.vy) > 48) {
            bd.vy = Math.abs(bd.vy) * bd.bounce; bd.vx *= 0.80; bd.vz *= 0.80; bd.omg *= 0.68;
            if (bd.kind === "wheel" && tier >= 2 && craters.length < 28) craters.push({ x:bd.x, z:bd.z, r:28, style:"napalm", f0:f });
          } else {
            bd.vy = 0; bd.vx *= 0.72; bd.vz *= 0.72;
            if (bd.kind === "head") { bd.omg = 0; bd.ang *= 0.45; } else bd.omg *= 0.55;
          }
        }
        if (Math.abs(bd.x) > lim) { bd.x = Math.sign(bd.x) * lim; bd.vx *= -0.68; }
        if (Math.abs(bd.z) > lim) { bd.z = Math.sign(bd.z) * lim; bd.vz *= -0.68; }
      }

      for (let gi = 0; gi < gibs.length; gi++) {
        const gb = gibs[gi];
        if (inTornado) {
          const ty = 35 + (gi / nGibs) * 245, swR = 34 + 0.54 * ty, ag = f * 0.29 + gi * 0.55;
          gb.x = Math.cos(ag) * swR; gb.z = Math.sin(ag) * swR; gb.y += (ty - gb.y) * 0.25; gb.ang += gb.omg * dt;
          continue;
        } else if (tier === 3 && f === 96) {
          const ao = Math.atan2(gb.z, gb.x + 0.01), sp = 150 + (gi % 9) * 36;
          gb.vx = Math.cos(ao) * sp; gb.vz = Math.sin(ao) * sp; gb.vy = -190 + (gi % 5) * 48;
        }
        gb.vy -= grav * dt;
        gb.x += gb.vx * dt; gb.y += gb.vy * dt; gb.z += gb.vz * dt; gb.ang += gb.omg * dt;
        if (gb.y <= gb.rad) {
          gb.y = gb.rad;
          if (gb.volatile && !gb.popped && f > detF + 14) {
            gb.popped = true; gb.vy = 295;
            blasts.push({ f0:f, dur:15, x:gb.x, y:28, z:gb.z, maxR:145, style:"fire" });
            if (craters.length < 32) craters.push({ x:gb.x, z:gb.z, r:34, style:"napalm", f0:f });
          } else if (Math.abs(gb.vy) > 52) {
            gb.vy = Math.abs(gb.vy) * gb.bounce; gb.vx *= 0.65; gb.vz *= 0.65; gb.omg *= 0.55;
            if (craters.length < 36 && gi % 5 === 0) craters.push({ x:gb.x, z:gb.z, r:16, style:"blood", f0:f });
          } else {
            gb.vy = 0; gb.vx *= 0.68; gb.vz *= 0.68; gb.omg *= 0.45;
          }
        }
        if (Math.abs(gb.x) > lim + 18) { gb.x = Math.sign(gb.x) * (lim + 18); gb.vx *= -0.55; }
        if (Math.abs(gb.z) > lim + 18) { gb.z = Math.sign(gb.z) * (lim + 18); gb.vz *= -0.55; }
      }

      for (const sp of sparks) {
        if (sp.life <= 0) continue;
        sp.vy -= grav * 0.55 * dt;
        sp.x += sp.vx * dt; sp.y += sp.vy * dt; sp.z += sp.vz * dt;
        if (sp.y <= 2) { sp.y = 2; sp.vy = Math.abs(sp.vy) * 0.45; }
        sp.life -= sp.dec * dt;
      }
    }

    frames.push({
      f,
      bodies: bodies.filter(b => b.active).map(b => ({...b})),
      gibs: gibs.map(g => ({...g})),
      blasts: blasts.filter(bl => f >= bl.f0 && f < bl.f0 + bl.dur).map(bl => ({...bl})),
      craters: craters.filter(cr => cr.f0 <= f).map(cr => ({...cr})),
      sparks: sparks.filter(sp => sp.life > 0.04).map(sp => ({...sp}))
    });
  }
  return frames;
}

const SIM_HIST = {
  1: precompute3DTier(1),
  2: precompute3DTier(2),
  3: precompute3DTier(3),
  4: precompute3DTier(4)
};

// Render any frame of Tier 1..4 from ANY continuous 360° Yaw + Vertical Pitch (+90° Above .. -90° Below)!
function renderExplosion3D(ctx, W, H, tier, f, yawDeg, pitchIdx) {
  ctx.clearRect(0, 0, W, H);
  const cfg = TIER_INFO[tier], detF = cfg.detF;
  const stFrame = SIM_HIST[tier][Math.min(cfg.nFrames - 1, Math.max(0, f))];
  const normYaw = ((yawDeg % 360) + 360) % 360;
  const camD = Math.round(normYaw / 45) % 8;
  const th = normYaw * Math.PI / 180;
  const ct = Math.cos(th), st = Math.sin(th);

  // Camera elevation angle: +90°, +45°, 0°, -45°, -90°
  const elDeg = [86, 42, 10, -38, -86][pitchIdx];
  const elRad = elDeg * Math.PI / 180;
  const sinEl = Math.sin(elRad), cosEl = Math.cos(elRad);
  const cxS = W * 0.5;
  const groundY = pitchIdx === 0 || pitchIdx === 4 ? H * 0.54 : H * 0.87;

  function proj3D(x, y, z) {
    const u = x * ct - z * st;
    const hz = x * st + z * ct; // horizontal depth toward viewer
    // Full 3D elevation rotation! Works smoothly from +90° Overhead -> 0° Eye-Level -> -90° Glass-Floor Below!
    const depth = hz * cosEl + (y - 70) * sinEl;
    const vScreen = -(y * cosEl - hz * sinEl);
    const persp = Math.max(0.62, Math.min(1.52, 820 / Math.max(280, 820 - depth)));
    return { sx: cxS + u * persp, sy: groundY + vScreen * persp, depth, persp };
  }

  // --- ACT 1 & ACT 2: PRE-DETONATION 360° SCREAM, BLOAT, X-RAY & SKY-BEAM ---
  if (f < detF) {
    const spinAdd = (tier === 2) ? Math.floor(f / 2) : 0;
    const effD = (camD + spinAdd) % 8;
    const effYaw = normYaw + spinAdd * 45;
    const phK = (f * 2) % FRAMES;
    const useXray = (tier === 3 && f >= 8 && (f % 3 !== 2)) || (tier === 4 && f >= 20 && (f % 3 === 0));

    let wmImg = IMG_SCREAM[effD][phK];
    if (pitchIdx === 0) wmImg = useXray ? P360.xrayAbove : IMG_ABOVE90_S[phK];
    else if (pitchIdx === 1) wmImg = useXray ? P360.xrays[effD] : IMG_ABOVE45_S[phK];
    else if (pitchIdx === 3) wmImg = useXray ? P360.xrays[effD] : IMG_BELOW45_S[phK];
    else if (pitchIdx === 4) wmImg = IMG_BELOW90[phK];
    else if (useXray) wmImg = P360.xrays[effD];

    const ovStart = tier >= 2 ? 12 : 17;
    let bloatX = 1, bloatY = 1, shakeX = 0, shakeY = 0, liftY = 0, ov = 0;
    if (tier === 3 && f >= 6) liftY = Math.min(1, (f - 6) / 18) * 34 + Math.sin(f * 0.9) * 5;
    if (f >= ovStart) {
      ov = (f - ovStart) / Math.max(1, detF - ovStart);
      if (tier === 3 && f >= detF - 5) {
        const imp = (f - (detF - 6)) / 5;
        bloatX = 1 - 0.42 * imp; bloatY = 1 - 0.36 * imp;
      } else {
        const maxB = [0, 0.22, 0.44, 0.24, 0.78][tier];
        bloatX = 1 + maxB * Math.pow(ov, 1.3) + 0.04 * Math.sin(f * 2.8);
        bloatY = 1 + maxB * 0.65 * Math.pow(ov, 1.3) - 0.03 * Math.sin(f * 2.8);
      }
      const sAmp = (2.5 + 7 * ov) * (tier >= 3 ? 1.4 : 1.0);
      shakeX = Math.sin(f * 4.2) * sAmp; shakeY = Math.cos(f * 5.3) * sAmp * 0.65;
    }

    // Tier 4 Spinning 3D Orbital Laser Target Reticle on Floor!
    if (tier === 4) {
      ctx.save();
      for (const rr of [135, 82, 38]) {
        ctx.strokeStyle = `rgba(255,45,70,${0.45 + 0.4 * Math.sin(f * 0.7)})`;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        for (let i = 0; i <= 48; i++) {
          const a = (i / 48) * Math.PI * 2 + f * 0.08;
          const p = proj3D(Math.cos(a) * rr, 0, Math.sin(a) * rr);
          if (i === 0) ctx.moveTo(p.sx, p.sy); else ctx.lineTo(p.sx, p.sy);
        }
        ctx.stroke();
      }
      ctx.restore();
    }

    // Draw screaming / bloating / X-ray Wheelman
    ctx.save();
    const anchor = proj3D(0, 0, 0);
    ctx.translate(anchor.sx + shakeX, anchor.sy + shakeY - liftY);
    if (pitchIdx === 0) ctx.rotate(effYaw * Math.PI / 180);
    else if (pitchIdx === 4) ctx.rotate(-effYaw * Math.PI / 180);
    const dw = 320 * bloatX, dh = 304 * bloatY;
    if (wmImg && wmImg.complete) {
      if (pitchIdx === 0 || pitchIdx === 4) ctx.drawImage(wmImg, -dw * 0.5, -dh * 0.5, dw, dh);
      else ctx.drawImage(wmImg, -dw * 0.5, -dh * 0.947, dw, dh);
    }
    // Core overload incandescent plasma/fire glow
    if (ov > 0.02) {
      const gx = 0, gy = (pitchIdx === 0 || pitchIdx === 4) ? 0 : -88;
      const gr = 55 + 95 * ov;
      const grad = ctx.createRadialGradient(gx, gy, 4, gx, gy, gr);
      if (tier === 3) {
        grad.addColorStop(0, `rgba(255,255,255,${0.85 * ov})`);
        grad.addColorStop(0.45, `rgba(34,211,238,${0.65 * ov})`);
        grad.addColorStop(1, "rgba(168,85,247,0)");
      } else {
        grad.addColorStop(0, `rgba(255,255,220,${0.88 * ov})`);
        grad.addColorStop(0.45, `rgba(255,115,20,${0.65 * ov})`);
        grad.addColorStop(1, "rgba(220,38,38,0)");
      }
      ctx.globalCompositeOperation = "lighter";
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(gx, gy, gr, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();

    // Tier 4 Orbital Antimatter Sky-Beam slamming down at f = detF-8 .. detF-1!
    if (tier === 4 && f >= detF - 8) {
      const kBeam = (f - (detF - 8)) / 8;
      const bw = 18 + kBeam * 68;
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      const bg = ctx.createLinearGradient(cxS - bw, 0, cxS + bw, 0);
      bg.addColorStop(0, "rgba(232,121,249,0)");
      bg.addColorStop(0.3, "rgba(251,146,60,0.85)");
      bg.addColorStop(0.5, "rgba(255,255,255,1)");
      bg.addColorStop(0.7, "rgba(251,146,60,0.85)");
      bg.addColorStop(1, "rgba(232,121,249,0)");
      ctx.fillStyle = bg;
      ctx.fillRect(cxS - bw, 0, bw * 2, groundY + 18);
      ctx.restore();
    }

    // Crackling overload lightning / burnout fire arcs
    if ((tier >= 2 && f >= 5) || ov > 0.15) {
      ctx.save();
      ctx.strokeStyle = tier === 3 ? "#67e8f9" : "#fbbf24";
      ctx.lineWidth = 2.6;
      const cP = proj3D(0, 75 + liftY, 0);
      for (let b = 0; b < 4 + tier * 2; b++) {
        let bx = cP.sx + shakeX, by = cP.sy + shakeY, a = (b * 1.3 + f * 0.7);
        ctx.beginPath(); ctx.moveTo(bx, by);
        for (let s = 0; s < 4; s++) {
          a += Math.sin(f * 1.9 + b * 3 + s) * 0.65;
          bx += Math.cos(a) * 24; by += Math.sin(a) * 22;
          ctx.lineTo(bx, by);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
    return;
  }

  // --- ACT 3, 4 & 5: TRUE 3D DEPTH-SORTED EXPLOSIONS, TORNADO, MUSHROOM CLOUD & GIBS! ---
  // 1) Soft Radial-Feathered 3D Floor Craters, Burning Napalm Pools & Magma Fissures
  for (const cr of stFrame.craters) {
    const p = proj3D(cr.x, 0, cr.z);
    const rx = Math.max(4, cr.r * p.persp);
    const aspect = Math.max(0.20, Math.abs(sinEl));
    ctx.save();
    ctx.translate(p.sx, p.sy);
    ctx.scale(1, aspect);
    const cg = ctx.createRadialGradient(0, 0, rx * 0.08, 0, 0, rx);
    if (cr.style === "blood") {
      cg.addColorStop(0, "rgba(155,14,20,0.88)");
      cg.addColorStop(0.55, "rgba(65,10,14,0.65)");
    } else if (cr.style === "plasma") {
      cg.addColorStop(0, "rgba(103,232,249,0.78)");
      cg.addColorStop(0.5, "rgba(30,64,95,0.55)");
    } else if (cr.style === "magma") {
      cg.addColorStop(0, "rgba(255,210,75,0.85)");
      cg.addColorStop(0.45, "rgba(234,88,12,0.72)");
    } else {
      cg.addColorStop(0, "rgba(251,146,60,0.80)");
      cg.addColorStop(0.5, "rgba(38,24,20,0.62)");
    }
    cg.addColorStop(1, "rgba(15,12,12,0)");
    ctx.fillStyle = cg;
    ctx.beginPath(); ctx.arc(0, 0, rx, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  // Tier 3 3D Plasma Funnel Core Glow during Tornado (f=36..95)
  if (tier === 3 && f >= 36 && f < 96) {
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (let h = 20; h <= 250; h += 26) {
      const swR = (34 + 0.54 * h), a0 = f * 0.32 + h * 0.04;
      const p0 = proj3D(Math.cos(a0) * swR, h, Math.sin(a0) * swR);
      const p1 = proj3D(Math.cos(a0 + 2.2) * swR, h + 18, Math.sin(a0 + 2.2) * swR);
      ctx.strokeStyle = "rgba(56,225,255,0.42)";
      ctx.lineWidth = 5 * p0.persp;
      ctx.beginPath(); ctx.moveTo(p0.sx, p0.sy); ctx.lineTo(p1.sx, p1.sy); ctx.stroke();
    }
    ctx.restore();
  }

  // 2) Build & Depth-Sort All 3D Renderables (VFX Blasts, Gibs, Hero Rigid Bodies, 3D Sparks)
  const queue = [];
  for (const bl of stFrame.blasts) {
    const p = proj3D(bl.x, bl.y, bl.z);
    queue.push({ depth: p.depth, type: "blast", bl, p, prog: (f - bl.f0) / bl.dur });
  }
  for (const gb of stFrame.gibs) {
    const p = proj3D(gb.x, gb.y, gb.z);
    queue.push({ depth: p.depth, type: "gib", gb, p });
  }
  for (const bd of stFrame.bodies) {
    const p = proj3D(bd.x, bd.y, bd.z);
    queue.push({ depth: p.depth, type: "body", bd, p });
  }
  queue.sort((a, b) => a.depth - b.depth);

  for (const item of queue) {
    if (item.type === "blast") {
      const { bl, p, prog } = item;
      const im = VFX_IMGS[bl.style] || VFX_IMGS.fire;
      if (!im || !im.complete) continue;
      ctx.save();
      if (bl.style === "nuke") {
        // Towering Photorealistic Thermonuclear Mushroom Cloud anchored to 3D ground!
        const gP = proj3D(0, 0, 0);
        const scN = 0.56 + 0.56 * Math.pow(prog, 0.38);
        const hN = Math.min(H * 1.03, bl.maxR * 0.94 * scN * gP.persp);
        const wN = hN * 1.02;
        ctx.globalAlpha = prog > 0.68 ? Math.max(0, 1 - (prog - 0.68) / 0.32) : 1.0;
        if (pitchIdx === 0 || pitchIdx === 4) {
          ctx.translate(gP.sx, gP.sy);
          ctx.rotate(th);
          ctx.drawImage(im, -wN * 0.5, -hN * 0.5, wN, hN);
        } else {
          ctx.translate(gP.sx, gP.sy + 12 - hN * 0.91 + hN * 0.5);
          if (camD === 2 || camD === 3 || camD === 6 || camD === 7) ctx.scale(-1, 1);
          ctx.drawImage(im, -wN * 0.5, -hN * 0.5, wN, hN);
        }
      } else {
        const diam = bl.maxR * (0.42 + 0.72 * Math.pow(prog, 0.52)) * p.persp;
        ctx.globalAlpha = prog < 0.48 ? 0.96 : Math.max(0, (1 - (prog - 0.48) / 0.52) * 0.92);
        if (prog < 0.24) ctx.globalCompositeOperation = "lighter";
        ctx.translate(p.sx, p.sy - prog * diam * 0.18);
        ctx.rotate(prog * 0.85);
        ctx.drawImage(im, -diam * 0.5, -diam * 0.5, diam, diam);
      }
      ctx.restore();
    } else if (item.type === "gib") {
      const { gb, p } = item;
      const im = P360.gibs[gb.gidx];
      if (!im || !im.complete) continue;
      ctx.save();
      ctx.translate(p.sx, p.sy);
      ctx.rotate(gb.ang * Math.PI / 180);
      ctx.scale(p.persp, p.persp);
      ctx.drawImage(im, -im.width * 0.5, -im.height * 0.5);
      ctx.restore();
    } else if (item.type === "body") {
      const { bd, p } = item;
      const spinStep = Math.round(bd.ang / 90);
      const effD = ((camD + spinStep) % 8 + 8) % 8;
      let im = P360.nut;
      if (bd.kind === "head") im = P360.heads[camD];
      else if (bd.kind === "wheel") im = P360.wheels[effD];
      else if (bd.kind === "bar") im = P360.bars[effD];
      else if (bd.kind === "lleg") im = P360.llegs[camD];
      else if (bd.kind === "rleg") im = P360.rlegs[camD];
      else if (bd.kind === "cap") im = P360.cap;
      if (!im || !im.complete) continue;

      if (bd.fire && f < cfg.nFrames - 16) {
        const fl = VFX_IMGS[tier === 3 ? "plasma" : "fire"];
        if (fl && fl.complete) {
          ctx.save();
          ctx.globalCompositeOperation = "lighter";
          ctx.globalAlpha = 0.72;
          const fd = 76 * p.persp;
          ctx.drawImage(fl, p.sx - fd * 0.5, p.sy - fd * 0.5, fd, fd);
          ctx.restore();
        }
      }
      ctx.save();
      ctx.translate(p.sx, p.sy);
      ctx.rotate(bd.ang * Math.PI / 180);
      ctx.scale(p.persp, p.persp);
      ctx.drawImage(im, -im.width * 0.5, -im.height * 0.5);
      ctx.restore();
    }
  }

  // 3) 3D Sparks, 3D Perspective Shockwave Rings, Thunderbolt Slam & Whiteout Flash!
  for (const sp of stFrame.sparks) {
    const p = proj3D(sp.x, sp.y, sp.z);
    ctx.fillStyle = sp.col;
    ctx.globalAlpha = Math.min(1, sp.life);
    ctx.beginPath(); ctx.arc(p.sx, p.sy, 2.4 * p.persp, 0, Math.PI * 2); ctx.fill();
  }
  ctx.globalAlpha = 1;

  if (f >= detF && f <= detF + 10) {
    const kS = (f - detF) / 10;
    const rSh = 35 + kS * (tier === 4 ? 340 : (tier === 3 ? 280 : 225));
    ctx.save();
    ctx.strokeStyle = tier === 3 ? `rgba(103,232,249,${1 - kS})` : `rgba(254,240,138,${1 - kS})`;
    ctx.lineWidth = Math.max(2, 8 * (1 - kS));
    ctx.beginPath();
    for (let i = 0; i <= 48; i++) {
      const a = (i / 48) * Math.PI * 2;
      const p = proj3D(Math.cos(a) * rSh, 55, Math.sin(a) * rSh);
      if (i === 0) ctx.moveTo(p.sx, p.sy); else ctx.lineTo(p.sx, p.sy);
    }
    ctx.stroke();
    ctx.restore();
  }

  // Tier 3 Giant Sky-to-Ground Thunderbolt Slam at f=95..101!
  if (tier === 3 && f >= 95 && f <= 101) {
    const gP = proj3D(0, 0, 0);
    ctx.save();
    ctx.strokeStyle = "#22d3ee"; ctx.lineWidth = 18;
    ctx.beginPath();
    ctx.moveTo(cxS - 18, 0); ctx.lineTo(cxS + 26, H*0.24); ctx.lineTo(cxS - 22, H*0.48); ctx.lineTo(cxS + 18, H*0.68); ctx.lineTo(gP.sx, gP.sy);
    ctx.stroke();
    ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 7; ctx.stroke();
    ctx.restore();
  }

  // Blinding Detonation Flash (full whiteout on Tier 4 Nuclear Detonation!)
  if (f >= detF && f <= detF + 3) {
    const kF = 1 - (f - detF) / 4;
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    if (tier === 4 && f <= detF + 1) {
      ctx.fillStyle = `rgba(255,252,235,${0.88 * kF})`;
      ctx.fillRect(0, 0, W, H);
    }
    const cP = proj3D(0, 95, 0);
    const rg = ctx.createRadialGradient(cP.sx, cP.sy, 5, cP.sx, cP.sy, 180 + tier * 65);
    rg.addColorStop(0, `rgba(255,255,255,${0.95 * kF})`);
    rg.addColorStop(0.4, tier === 3 ? `rgba(56,189,248,${0.65 * kF})` : `rgba(251,191,36,${0.65 * kF})`);
    rg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = rg;
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
  }
}

// =========================================================================
// 3 NEW 60-FPS SPHERICAL (360° + ABOVE/BELOW) STUNT RENDERERS!
//   1) 🔥 Fire-Wheels Burnout
//   2) 📏 Super-Long Metal Bar & Cylindrical Steamroller Wheels
//   3) 🚀 Jetpack Hover + Spinning Bar & Wheels
// =========================================================================
const JP_OFFSETS = [
  [80, 56], [146, 54], [205, 88], [122, 50],
  [80, 66], [38, 50],  [-45, 88], [14, 54]
];

function drawContinuousWheelInferno2D(ctx, wx, wy, rx, ry, angDeg, tSec, spinSpeed, wakeDx) {
  const rad = angDeg * Math.PI / 180;
  const ca = Math.cos(rad), sa = Math.sin(rad);

  // 1) Additive incandescent cherry-orange/yellow molten tire glow
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.translate(wx, wy);
  ctx.rotate(rad);
  ctx.scale(1, ry / Math.max(1, rx));
  const rg = ctx.createRadialGradient(0, 0, rx * 0.45, 0, 0, rx * 1.42);
  rg.addColorStop(0, "rgba(255,140,20,0)");
  rg.addColorStop(0.52, "rgba(255,95,12,0.72)");
  rg.addColorStop(0.76, "rgba(255,230,110,0.88)");
  rg.addColorStop(1, "rgba(255,60,0,0)");
  ctx.fillStyle = rg;
  ctx.beginPath(); ctx.arc(0, 0, rx * 1.42, 0, Math.PI * 2); ctx.fill();
  ctx.restore();

  // 2) 22 Continuous roaring centrifugal flame tongues licking upward & along wakeDx
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  const nT = 22;
  for (let i = 0; i < nT; i++) {
    const th = (i / nT) * Math.PI * 2 + tSec * spinSpeed * 3.2;
    const px = wx + (rx * Math.cos(th)) * ca - (ry * Math.sin(th)) * sa;
    const py = wy + (rx * Math.cos(th)) * sa + (ry * Math.sin(th)) * ca;
    const flk = 0.62 + 0.38 * Math.sin(th * 3 - tSec * 24 + i * 1.7);
    const tipX = px + Math.cos(th) * 11 + wakeDx * (0.16 + 0.22 * flk);
    const tipY = py + Math.sin(th) * 8 - (22 + 34 * flk * (0.75 + spinSpeed * 0.06));
    const wb = 8.5 + 4.8 * flk;
    ctx.fillStyle = `rgba(255,${Math.round(80 + 85 * flk)},14,0.62)`;
    ctx.beginPath(); ctx.moveTo(px - wb, py + 3); ctx.lineTo(px + wb, py + 3); ctx.lineTo(tipX, tipY); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "rgba(255,240,135,0.72)";
    ctx.beginPath(); ctx.moveTo(px - wb*0.48, py + 2); ctx.lineTo(px + wb*0.48, py + 2); ctx.lineTo(px*0.35 + tipX*0.65, py*0.35 + tipY*0.65); ctx.closePath(); ctx.fill();
  }

  // 3) Rising photographic pyrotechnic fire crests
  const fireIm = VFX_IMGS.fire;
  if (fireIm && fireIm.complete) {
    for (let k = 0; k < 2; k++) {
      const pr = (tSec * 2.2 + k * 0.5) % 1.0;
      const fd = Math.max(68, rx * 1.45 + 42) * (0.65 + 0.45 * pr);
      ctx.save();
      ctx.globalAlpha = (1 - pr) * 0.78;
      ctx.translate(wx + wakeDx * (0.15 + 0.45 * pr), wy - ry * 0.52 - pr * 38);
      ctx.rotate(tSec * 4 + k * 2.1);
      ctx.drawImage(fireIm, -fd * 0.5, -fd * 0.5, fd, fd);
      ctx.restore();
    }
  }

  // 4) Tangential white-hot friction spark shower!
  for (let s = 0; s < 16; s++) {
    const u = ((tSec * (3.4 + (s % 4) * 0.6) + s * 0.13) % 1.0);
    const thS = (s * 1.17) % 3.1 - 0.6;
    const sx0 = wx + (rx * Math.cos(thS)) * ca + wakeDx * u * 1.05 + Math.sin(s * 9 + tSec * 20) * 6;
    const sy0 = wy + (ry * Math.sin(thS)) * 0.65 - u * (22 + (s % 5) * 14);
    const dxS = wakeDx * 0.24 + Math.cos(s * 3) * 9;
    const dyS = -(8 + (s % 4) * 3.5);
    ctx.strokeStyle = `rgba(255,215,90,${(1 - u * 0.85).toFixed(2)})`;
    ctx.lineWidth = 2.6;
    ctx.beginPath(); ctx.moveTo(sx0, sy0); ctx.lineTo(sx0 + dxS, sy0 + dyS); ctx.stroke();
  }
  ctx.restore();
}

function renderFireWheels3D(ctx, W, H, tSec, yawDeg, pitchIdx, spinSpeed) {
  ctx.clearRect(0, 0, W, H);
  const normYaw = ((yawDeg % 360) + 360) % 360;
  const camD = Math.round(normYaw / 45) % 8;
  const cxS = W * 0.5;
  const fFast0 = Math.floor(tSec * 16 * spinSpeed) % FRAMES;
  const fFast1 = (fFast0 + 4) % FRAMES;
  const fFast2 = (fFast0 + 8) % FRAMES;

  // Overhead (+90°) or Glass-Floor Underneath (-90°) Fire-Wheels!
  if (pitchIdx === 0 || pitchIdx === 4) {
    ctx.save();
    ctx.translate(cxS, H * 0.52);
    ctx.rotate((pitchIdx === 0 ? normYaw : -normYaw) * Math.PI / 180);
    // Twin 88-MPH scorching flame tracks behind both tires!
    for (const sxW of [-78, 78]) {
      const tg = ctx.createLinearGradient(sxW, -25, sxW, 145);
      tg.addColorStop(0, "rgba(255,235,120,0.85)");
      tg.addColorStop(0.5, "rgba(255,90,14,0.65)");
      tg.addColorStop(1, "rgba(255,40,0,0)");
      ctx.fillStyle = tg;
      ctx.fillRect(sxW - 18, -10, 36, 155);
    }
    const listV = pitchIdx === 0 ? IMG_ABOVE90_S : IMG_BELOW90;
    for (const [fi, al] of [[fFast0, 1.0], [fFast1, 0.45], [fFast2, 0.32]]) {
      const im = listV[fi];
      if (im && im.complete) { ctx.globalAlpha = al; ctx.drawImage(im, -160, -152, 320, 304); }
    }
    ctx.globalAlpha = 1;
    drawContinuousWheelInferno2D(ctx, -78, 4, 24, 56, 0, tSec, spinSpeed, 0);
    drawContinuousWheelInferno2D(ctx,  78, 4, 24, 56, 0, tSec, spinSpeed, 0);
    ctx.restore();
    return;
  }

  const groundY = H * 0.86;
  const ox = cxS - 160, oy = groundY - 288;
  const vibX = Math.sin(tSec * 46) * 2.0, vibY = Math.cos(tSec * 58) * 1.5;
  const wakeDx = (camD >= 1 && camD <= 3) ? 84 : ((camD >= 5 && camD <= 7) ? -84 : 0);

  const wSpecs = (pitchIdx === 2)
    ? STUNT_IMGS.cSpecs[camD]
    : [{ cx: 64, cy: 226, rx: 32, ry: 58, ang: -4 }, { cx: 256, cy: 226, rx: 32, ry: 58, ang: 4 }];

  // 1) Twin 88-MPH Scorching Ground Fire Trails!
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (const ws of wSpecs) {
    const wx = ox + ws.cx + wakeDx * 0.48, wy = groundY + 2;
    const rxT = 56 + Math.abs(wakeDx) * 0.58;
    const fg = ctx.createRadialGradient(wx, wy, 4, wx, wy, rxT);
    fg.addColorStop(0, "rgba(255,248,160,0.92)");
    fg.addColorStop(0.45, "rgba(255,105,16,0.75)");
    fg.addColorStop(1, "rgba(220,38,10,0)");
    ctx.save(); ctx.translate(wx, wy); ctx.scale(1, 13 / rxT);
    ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(0, 0, rxT, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  ctx.restore();

  // 2) Motion-blurred hyper-spinning screaming Wheelman
  const frameBank = pitchIdx === 1 ? IMG_ABOVE45_S : (pitchIdx === 3 ? IMG_BELOW45_S : IMG_SCREAM[camD]);
  ctx.save();
  for (const [fi, al] of [[fFast0, 1.0], [fFast1, 0.45], [fFast2, 0.30]]) {
    const im = frameBank[fi];
    if (im && im.complete) { ctx.globalAlpha = al; ctx.drawImage(im, ox + vibX, oy + vibY, 320, 304); }
  }
  ctx.restore();

  // 3) Roaring centrifugal tire inferno around each spinning wheel!
  for (const ws of wSpecs) {
    drawContinuousWheelInferno2D(ctx, ox + ws.cx + vibX, oy + ws.cy + vibY, ws.rx, ws.ry, ws.ang, tSec, spinSpeed, wakeDx);
  }
}

function drawSteppedHydraulicRod(ctx, x0, y0, x1, y1, thick = 11, isChrome = false) {
  const dx = x1 - x0, dy = y1 - y0;
  if (Math.hypot(dx, dy) < 3) return;
  const xm1 = x0 + dx * 0.42, ym1 = y0 + dy * 0.42;
  const xm2 = x0 + dx * 0.74, ym2 = y0 + dy * 0.74;
  const segs = [
    [x0, y0, xm1, ym1, thick + 4],
    [xm1, ym1, xm2, ym2, thick + 1],
    [xm2, ym2, x1, y1, Math.max(5, thick - 2)]
  ];
  ctx.save();
  ctx.lineCap = "round";
  for (const [xa, ya, xb, yb, wt] of segs) {
    ctx.strokeStyle = "#22262f"; ctx.lineWidth = wt + 3.5;
    ctx.beginPath(); ctx.moveTo(xa, ya); ctx.lineTo(xb, yb); ctx.stroke();
    ctx.strokeStyle = isChrome ? "#bac8da" : "#8e9cb0"; ctx.lineWidth = wt;
    ctx.beginPath(); ctx.moveTo(xa, ya); ctx.lineTo(xb, yb); ctx.stroke();
    ctx.strokeStyle = "#f8fafc"; ctx.lineWidth = Math.max(1.8, wt * 0.28);
    ctx.beginPath(); ctx.moveTo(xa, ya - wt * 0.22); ctx.lineTo(xb, yb - wt * 0.22); ctx.stroke();
  }
  for (const [mx, my, col] of [[xm1, ym1, "#f59e0b"], [xm2, ym2, "#e2e8f0"]]) {
    const rc = thick * 0.56 + 2;
    ctx.fillStyle = col; ctx.strokeStyle = "#1e222a"; ctx.lineWidth = 1.8;
    ctx.beginPath(); ctx.ellipse(mx, my, rc * 0.65, rc, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  }
  ctx.restore();
}

function drawExtrudedCylindricalWheel(ctx, wIm, pIn, pOut, rotRad, baseSc, nSlices = 14) {
  if (!wIm || !wIm.complete) return;
  const slices = [];
  for (let i = 0; i < nSlices; i++) {
    const tv = i / (nSlices - 1);
    slices.push({
      tv,
      sx: pIn.sx + (pOut.sx - pIn.sx) * tv,
      sy: pIn.sy + (pOut.sy - pIn.sy) * tv,
      depth: pIn.depth + (pOut.depth - pIn.depth) * tv,
      persp: pIn.persp + (pOut.persp - pIn.persp) * tv
    });
  }
  slices.sort((a, b) => a.depth - b.depth);
  for (let i = 0; i < slices.length; i++) {
    const s = slices[i];
    const isCap = (s.tv < 0.05) || (s.tv > 0.95) || (i === slices.length - 1);
    ctx.save();
    ctx.translate(s.sx, s.sy);
    ctx.rotate(rotRad);
    const sc = baseSc * s.persp;
    ctx.scale(sc, sc);
    if (!isCap) ctx.filter = "brightness(0.64)";
    ctx.drawImage(wIm, -wIm.width * 0.5, -wIm.height * 0.5);
    ctx.restore();
  }
}

function renderSuperLongBar3D(ctx, W, H, tSec, yawDeg, pitchIdx, stretchMul) {
  ctx.clearRect(0, 0, W, H);
  const normYaw = ((yawDeg % 360) + 360) % 360;
  const camD = Math.round(normYaw / 45) % 8;
  const s01 = Math.max(0, (stretchMul - 1.0) / 3.0);
  const cxS = W * 0.5;

  // Overhead (+90°) or Glass-Floor Underneath (-90°) Super-Long Bar & Steamroller Wheels!
  if (pitchIdx === 0 || pitchIdx === 4) {
    ctx.save();
    ctx.translate(cxS, H * 0.52);
    ctx.rotate((pitchIdx === 0 ? normYaw : -normYaw) * Math.PI / 180);
    const inAx = 46 + 118 * s01, wLen = 16 + 56 * s01, outAx = inAx + wLen;
    const cylDir = pitchIdx === 0 ? 1 : -1;
    const cylTipY = cylDir * (56 + 115 * s01);
    const bodyV = pitchIdx === 0 ? STUNT_IMGS.bodyAbove90 : STUNT_IMGS.bodyBelow90;
    const wEdge = P360.wheels[0];

    drawSteppedHydraulicRod(ctx, -40, 4, -outAx, 4, 10, false);
    drawSteppedHydraulicRod(ctx,  40, 4,  outAx, 4, 10, false);
    if (pitchIdx === 0 && bodyV && bodyV.complete) ctx.drawImage(bodyV, -160, -152, 320, 304);
    drawSteppedHydraulicRod(ctx, 0, cylDir * 14, 0, cylTipY, 18, true);
    if (P360.cap && P360.cap.complete) {
      ctx.save(); ctx.translate(0, cylTipY); ctx.rotate(tSec * 6);
      ctx.drawImage(P360.cap, -P360.cap.width * 0.6, -P360.cap.height * 0.6, P360.cap.width * 1.2, P360.cap.height * 1.2);
      ctx.restore();
    }
    if (pitchIdx === 4 && bodyV && bodyV.complete) ctx.drawImage(bodyV, -160, -152, 320, 304);

    drawExtrudedCylindricalWheel(ctx, wEdge, { sx:-inAx, sy:4, depth:0, persp:0.88 }, { sx:-outAx, sy:4, depth:1, persp:0.88 }, 0, 1.0, 12);
    drawExtrudedCylindricalWheel(ctx, wEdge, { sx: inAx, sy:4, depth:0, persp:0.88 }, { sx: outAx, sy:4, depth:1, persp:0.88 }, 0, 1.0, 12);
    ctx.restore();
    return;
  }

  const th = normYaw * Math.PI / 180;
  const ct = Math.cos(th), st = Math.sin(th);
  const elDeg = [86, 34, 9, -28, -86][pitchIdx];
  const elRad = elDeg * Math.PI / 180;
  const sinEl = Math.sin(elRad), cosEl = Math.cos(elRad);
  const groundY = H * 0.85;
  const axleY = 54;

  function proj3D(x, y, z) {
    const u = x * ct - z * st;
    const hz = x * st + z * ct;
    const depth = hz * cosEl + (y - 60) * sinEl;
    const vScreen = -(y * cosEl - hz * sinEl);
    const persp = Math.max(0.72, Math.min(1.30, 920 / Math.max(380, 920 - depth)));
    return { sx: cxS + u * persp, sy: groundY + vScreen * persp, depth, persp };
  }

  const innerAx = 44 + 132 * s01;      // 44 .. 176
  const wheelLen = 14 + 62 * s01;      // 14 .. 76 (wheels stretch 5.4x super long!)
  const outerAx = innerAx + wheelLen;  // up to +-252 inside 640px!
  const cylLen = 42 + 158 * s01;       // Forward chrome bar stretches up to 200px!

  const pC = proj3D(0, axleY, 0);
  const pHandL = proj3D(-38, axleY, 0), pHandR = proj3D(38, axleY, 0);
  const pInL = proj3D(-innerAx, axleY, 0), pOutL = proj3D(-outerAx, axleY, 0);
  const pInR = proj3D(innerAx, axleY, 0),  pOutR = proj3D(outerAx, axleY, 0);
  const pCylBase = proj3D(0, axleY - 2, 16), pCylTip = proj3D(0, axleY - 8, cylLen);

  // Wide ground shadow under the super-long bar & roller drums
  ctx.save();
  ctx.strokeStyle = "rgba(8,10,15,0.52)"; ctx.lineWidth = 18; ctx.lineCap = "round";
  const shL = proj3D(-outerAx, 0, 0), shR = proj3D(outerAx, 0, 0);
  ctx.beginPath(); ctx.moveTo(shL.sx, shL.sy + 4); ctx.lineTo(shR.sx, shR.sy + 4); ctx.stroke();
  ctx.restore();

  const wIm = P360.wheels[camD];
  const baseSc = wIm ? Math.min(1.04, 108 / Math.max(1, wIm.height)) : 1.0;
  const rotW = (camD === 2 || camD === 6) ? ((camD === 2 ? -1 : 1) * tSec * 7.5) : 0;

  const sides = [
    { hand: pHandL, pIn: pInL, pOut: pOutL, depth: 0.5 * (pInL.depth + pOutL.depth) },
    { hand: pHandR, pIn: pInR, pOut: pOutR, depth: 0.5 * (pInR.depth + pOutR.depth) }
  ].sort((a, b) => a.depth - b.depth);

  function drawChromeCannon() {
    drawSteppedHydraulicRod(ctx, pCylBase.sx, pCylBase.sy, pCylTip.sx, pCylTip.sy, 18, true);
    if (P360.cap && P360.cap.complete) {
      ctx.save();
      ctx.translate(pCylTip.sx, pCylTip.sy);
      ctx.rotate(tSec * 6.5);
      const cs = 1.22 * pCylTip.persp;
      ctx.drawImage(P360.cap, -P360.cap.width * 0.5 * cs, -P360.cap.height * 0.5 * cs, P360.cap.width * cs, P360.cap.height * cs);
      ctx.restore();
    }
  }

  // 1) Far Super-Long Cylindrical Wheel & Far Telescoping Axle
  drawExtrudedCylindricalWheel(ctx, wIm, sides[0].pIn, sides[0].pOut, rotW, baseSc, 14);
  drawSteppedHydraulicRod(ctx, sides[0].hand.sx, sides[0].hand.sy, sides[0].pOut.sx, sides[0].pOut.sy, 9.5, false);

  // 2) Rear-pointing Chrome Cannon (occluded behind his back when viewing from rear)
  if (pCylTip.depth < pC.depth) drawChromeCannon();

  // 3) Central Un-Squashed Human Body!
  const bIm = STUNT_IMGS.body[camD];
  if (bIm && bIm.complete) {
    const bob = Math.sin(tSec * 6) * 2.0;
    ctx.drawImage(bIm, pC.sx - 160, pC.sy - 234 + bob, 320, 304);
  }

  // 4) Front/Profile Super-Long Chrome Cannon
  if (pCylTip.depth >= pC.depth) drawChromeCannon();

  // 5) Near Telescoping Axle & Near Super-Long Cylindrical Wheel!
  drawSteppedHydraulicRod(ctx, sides[1].hand.sx, sides[1].hand.sy, sides[1].pOut.sx, sides[1].pOut.sy, 10.5, false);
  drawExtrudedCylindricalWheel(ctx, wIm, sides[1].pIn, sides[1].pOut, rotW, baseSc, 14);
}

function renderJetpackHover3D(ctx, W, H, tSec, yawDeg, pitchIdx, hoverAlt, rotorSpd) {
  ctx.clearRect(0, 0, W, H);
  const normYaw = ((yawDeg % 360) + 360) % 360;
  const camD = Math.round(normYaw / 45) % 8;
  const cxS = W * 0.5;
  const hoverLift = hoverAlt + 15 * Math.sin(tSec * 3.1);
  const swayX = 14 * Math.cos(tSec * 2.0);

  // Overhead (+90°) or Glass-Floor Underneath (-90°) Jetpack Hover + Spinning Bar/Wheels!
  if (pitchIdx === 0 || pitchIdx === 4) {
    const cyS = H * 0.52;
    ctx.save();
    ctx.translate(cxS + swayX, cyS);
    ctx.rotate((pitchIdx === 0 ? normYaw : -normYaw) * Math.PI / 180);

    const spinAng = tSec * rotorSpd * Math.PI * 2;
    const drawSpinAssemblyTopBot = () => {
      ctx.save();
      ctx.rotate(spinAng);
      ctx.strokeStyle = "rgba(165,243,252,0.48)"; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.arc(0, 0, 92, 0, Math.PI * 2); ctx.stroke();
      drawSteppedHydraulicRod(ctx, -84, 0, 84, 0, 9, false);
      drawSteppedHydraulicRod(ctx, 0, 0, 0, pitchIdx === 0 ? 52 : -52, 15, true);
      const wE = P360.wheels[0];
      if (wE && wE.complete) {
        ctx.drawImage(wE, -88 - wE.width * 0.42, -wE.height * 0.42, wE.width * 0.84, wE.height * 0.84);
        ctx.drawImage(wE,  88 - wE.width * 0.42, -wE.height * 0.42, wE.width * 0.84, wE.height * 0.84);
      }
      ctx.restore();
    };

    if (pitchIdx === 0) {
      drawSpinAssemblyTopBot();
      if (STUNT_IMGS.bodyAbove90.complete) ctx.drawImage(STUNT_IMGS.bodyAbove90, -160, -152, 320, 304);
      if (STUNT_IMGS.jetpackAbove.complete) ctx.drawImage(STUNT_IMGS.jetpackAbove, -70, -112, 140, 140);
    } else {
      if (STUNT_IMGS.bodyBelow90.complete) ctx.drawImage(STUNT_IMGS.bodyBelow90, -160, -152, 320, 304);
      drawSpinAssemblyTopBot();
      if (STUNT_IMGS.jetpackBelow.complete) ctx.drawImage(STUNT_IMGS.jetpackBelow, -70, -12, 140, 140);
      // Blinding twin rocket nozzles blasting straight toward the glass floor!
      ctx.save(); ctx.globalCompositeOperation = "lighter";
      for (const nx of [-26, 26]) {
        const pr = 34 + 12 * Math.sin(tSec * 28 + nx);
        const rg = ctx.createRadialGradient(nx, 56, 3, nx, 56, pr);
        rg.addColorStop(0, "rgba(255,255,255,0.98)");
        rg.addColorStop(0.42, "rgba(103,232,249,0.85)");
        rg.addColorStop(0.75, "rgba(255,115,20,0.65)");
        rg.addColorStop(1, "rgba(255,40,0,0)");
        ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(nx, 56, pr, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    ctx.restore();
    return;
  }

  const groundY = H * 0.88;
  // 1) Shrinking Ground Shadow + Pulsing Orange Rocket Ground-Wash + Contrail Smoke Rings!
  const shRx = Math.max(24, 62 - hoverLift * 0.22);
  ctx.save();
  const sg = ctx.createRadialGradient(cxS + swayX, groundY, 4, cxS + swayX, groundY, shRx * 1.35);
  sg.addColorStop(0, "rgba(10,10,14,0.72)");
  sg.addColorStop(0.6, "rgba(255,120,20,0.38)");
  sg.addColorStop(1, "rgba(0,0,0,0)");
  ctx.translate(cxS + swayX, groundY); ctx.scale(1, 0.24);
  ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(0, 0, shRx * 1.35, 0, Math.PI * 2); ctx.fill();
  ctx.restore();

  for (let si = 0; si < 5; si++) {
    const spU = (tSec * 1.5 + si * 0.2) % 1.0;
    const sxSm = cxS + swayX + (si - 2) * 44 * spU;
    const sySm = groundY - 4 - (1 - spU) * 28;
    const rSm = 14 + spU * 28;
    ctx.fillStyle = `rgba(203,213,225,${((1 - spU) * 0.34).toFixed(2)})`;
    ctx.beginPath(); ctx.ellipse(sxSm, sySm, rSm, rSm * 0.42, 0, 0, Math.PI * 2); ctx.fill();
  }

  const bx = cxS + swayX - 160;
  const by = groundY - 288 - hoverLift;
  const [jox, joy] = JP_OFFSETS[camD];
  const jpIm = STUNT_IMGS.jetpacks[camD];
  const bodyIm = STUNT_IMGS.body[camD];

  function drawSupersonicThrusterPlumes() {
    let nozzles;
    if (camD === 2) nozzles = [[bx + jox + 60, by + joy + 114, -18]];
    else if (camD === 6) nozzles = [[bx + jox + 100, by + joy + 114, 18]];
    else if (camD === 0 || camD === 1 || camD === 7) nozzles = [[bx + jox + 36, by + joy + 122, 0], [bx + jox + 124, by + joy + 122, 0]];
    else nozzles = [[bx + jox + 48, by + joy + 124, 0], [bx + jox + 112, by + joy + 124, 0]];

    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (let ni = 0; ni < nozzles.length; ni++) {
      const [nxP, nyP, tiltDeg] = nozzles[ni];
      const flen = ((camD === 0 || camD === 1 || camD === 7) ? 112 : 84) + 24 * Math.sin(tSec * 34 + ni * 1.9);
      const radT = tiltDeg * Math.PI / 180;
      const txEnd = nxP + Math.sin(radT) * flen, tyEnd = nyP + Math.cos(radT) * flen;

      // Outer roaring orange-amber rocket plume
      ctx.fillStyle = "rgba(255,110,18,0.88)";
      ctx.beginPath(); ctx.moveTo(nxP - 14, nyP); ctx.lineTo(nxP + 14, nyP); ctx.lineTo(txEnd, tyEnd); ctx.closePath(); ctx.fill();
      // Blinding cyan-white supersonic inner core
      ctx.fillStyle = "rgba(165,245,255,0.95)";
      ctx.beginPath(); ctx.moveTo(nxP - 8, nyP); ctx.lineTo(nxP + 8, nyP);
      ctx.lineTo(nxP + Math.sin(radT) * flen * 0.72, nyP + Math.cos(radT) * flen * 0.72); ctx.closePath(); ctx.fill();
      // Crisp supersonic Mach shock diamonds!
      ctx.fillStyle = "#ffffff";
      for (let md = 0; md < 4; md++) {
        const fd = 0.16 + md * 0.16;
        const mxD = nxP + Math.sin(radT) * flen * fd, myD = nyP + Math.cos(radT) * flen * fd;
        ctx.beginPath(); ctx.moveTo(mxD, myD - 5); ctx.lineTo(mxD + 5, myD); ctx.lineTo(mxD, myD + 5); ctx.lineTo(mxD - 5, myD); ctx.closePath(); ctx.fill();
      }
      if (VFX_IMGS.fire && VFX_IMGS.fire.complete) {
        const pfd = 66;
        ctx.globalAlpha = 0.55;
        ctx.drawImage(VFX_IMGS.fire, nxP + Math.sin(radT)*flen*0.55 - pfd*0.5, nyP + Math.cos(radT)*flen*0.55 - pfd*0.5, pfd, pfd);
        ctx.globalAlpha = 1.0;
      }
    }
    ctx.restore();
  }

  function drawSpinningRotorBarAndWheels() {
    const thRotor = normYaw + tSec * rotorSpd * 360;
    const radR = thRotor * Math.PI / 180;
    const ctR = Math.cos(radR), stR = Math.sin(radR);
    const rotD = Math.round(((thRotor % 360) + 360) % 360 / 45) % 8;
    const hubX = cxS + swayX + (camD === 2 ? -18 : (camD === 6 ? 18 : 0));
    const hubY = by + 236;
    const tiltY = pitchIdx === 1 ? 0.34 : (pitchIdx === 3 ? -0.30 : 0.17);

    // High-speed silver-cyan motion-blur rotor disc!
    ctx.save();
    ctx.strokeStyle = "rgba(186,230,253,0.52)"; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.ellipse(hubX, hubY, 98, Math.max(14, Math.abs(98 * tiltY)), 0, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = "rgba(255,255,255,0.36)"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(hubX, hubY, 76, Math.max(10, Math.abs(76 * tiltY)), 0, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();

    const wPts = [
      { dx: -78 * ctR, dz: -78 * stR },
      { dx:  78 * ctR, dz:  78 * stR }
    ].sort((a, b) => a.dz - b.dz);

    const wSp = P360.wheels[rotD], barSp = P360.bars[rotD];
    const wSc = wSp ? Math.min(0.95, 102 / Math.max(1, wSp.height)) : 0.9;
    const selfSpin = (rotD === 2 || rotD === 6) ? tSec * rotorSpd * 18 : 0;

    if (wSp && wSp.complete) {
      ctx.save();
      ctx.translate(hubX + wPts[0].dx, hubY + wPts[0].dz * tiltY);
      ctx.rotate(selfSpin);
      ctx.scale(wSc * 0.90, wSc * 0.90);
      ctx.drawImage(wSp, -wSp.width * 0.5, -wSp.height * 0.5);
      ctx.restore();
    }
    if (barSp && barSp.complete) {
      ctx.save();
      ctx.translate(hubX, hubY);
      ctx.rotate(Math.sin(radR) * 0.16);
      ctx.drawImage(barSp, -barSp.width * 0.5, -barSp.height * 0.5);
      ctx.restore();
    }
    if (wSp && wSp.complete) {
      ctx.save();
      ctx.translate(hubX + wPts[1].dx, hubY + wPts[1].dz * tiltY);
      ctx.rotate(selfSpin);
      ctx.scale(wSc * 1.05, wSc * 1.05);
      ctx.drawImage(wSp, -wSp.width * 0.5, -wSp.height * 0.5);
      ctx.restore();
    }
  }

  const jpInFront = (camD === 3 || camD === 4 || camD === 5);
  if (!jpInFront) {
    drawSupersonicThrusterPlumes();
    if (jpIm && jpIm.complete) ctx.drawImage(jpIm, bx + jox, by + joy, 160, 160);
  }
  if (jpInFront) drawSpinningRotorBarAndWheels();

  if (bodyIm && bodyIm.complete) ctx.drawImage(bodyIm, bx, by, 320, 304);
  // Tactical shoulder harness straps on Front (0°) & Profile (90°/270°)
  if (camD === 0) {
    ctx.save(); ctx.strokeStyle = "#262a33"; ctx.lineWidth = 6;
    for (const sxSt of [bx + 128, bx + 174]) {
      ctx.beginPath(); ctx.moveTo(sxSt, by + 124); ctx.lineTo(sxSt, by + 166); ctx.stroke();
      ctx.fillStyle = "#dce4ee"; ctx.fillRect(sxSt - 4, by + 142, 8, 8);
    }
    ctx.restore();
  }

  if (!jpInFront) drawSpinningRotorBarAndWheels();
  if (jpInFront) {
    drawSupersonicThrusterPlumes();
    if (jpIm && jpIm.complete) ctx.drawImage(jpIm, bx + jox, by + joy, 160, 160);
  }
}

// =========================================================================
// UI State & Controls
// =========================================================================
let mode = "sphere"; // "sphere" | "fire" | "long" | "jetpack" | "drive" | "scream" | "boom"
let curTier = 1;     // 1..4
let autoEscalate = true, boomOrbit = true, stuntOrbit = true, longAutoWave = true;
let stuntTime = 0, sfxPulseAccum = 0, nitrousBoostT = 0, afterburnBoostT = 0;
let curPitch = 2;    // 0=+90 Above, 1=+45 Above, 2=0 Eye-Level, 3=-45 Below, 4=-90 Below
let curDir = 0;      // 0..7
let yawDegCont = 0;
let curFrame = 0;
let boomFrame = 0;
let playing = true, tourOn = true, idleMode = false, quickScreamTimer = 0;
let bgs = ["quake", "checker", "slate", "light"], bgNames = ["Quake", "Checker", "Slate", "Light"], bgi = 0;

const stageBox = document.getElementById("stage-box"), spriteWrap = document.getElementById("sprite-wrap"),
      spriteImg = document.getElementById("sprite-img"), boomCanvas = document.getElementById("boom-canvas"),
      bctx = boomCanvas.getContext("2d"), arenaCanvas = document.getElementById("arena-canvas"),
      badge = document.getElementById("badge"), metaBadge = document.getElementById("meta-badge"),
      dragHint = document.getElementById("draghint"), tierBar = document.getElementById("tier-bar"),
      ctrlSphere = document.getElementById("ctrl-sphere"), ctrlStunt = document.getElementById("ctrl-stunt"),
      ctrlDrive = document.getElementById("ctrl-drive"), ctrlBoom = document.getElementById("ctrl-boom"),
      pitchStrip = document.getElementById("pitch-strip"), yawStrip = document.getElementById("yaw-strip"),
      rngFps = document.getElementById("rng-fps"), lblFps = document.getElementById("lbl-fps"),
      rngZoom = document.getElementById("rng-zoom"), rngStuntZoom = document.getElementById("rng-stunt-zoom"),
      rngFireSpd = document.getElementById("rng-fire-spd"), lblFireSpd = document.getElementById("lbl-fire-spd"),
      rngLongLen = document.getElementById("rng-long-len"), lblLongLen = document.getElementById("lbl-long-len"),
      rngJpAlt = document.getElementById("rng-jp-alt"), lblJpAlt = document.getElementById("lbl-jp-alt"),
      rngJpSpd = document.getElementById("rng-jp-spd"), lblJpSpd = document.getElementById("lbl-jp-spd"),
      rngBoom = document.getElementById("rng-boom"), lblBoomF = document.getElementById("lbl-boom-f"),
      rngBoomFps = document.getElementById("rng-boom-fps"), lblBoomFps = document.getElementById("lbl-boom-fps");

function isStuntMode(m = mode) { return m === "fire" || m === "long" || m === "jetpack"; }

function getPitchFrameSrc(p, d, f, isScream) {
  if (p === 0) return isScream ? ABOVE90_B64.scream[f] : ABOVE90_B64.roll[f];
  if (p === 1) return isScream ? ABOVE45_B64.scream[f] : ABOVE45_B64.roll[f];
  if (p === 2) {
    if (idleMode && !isScream) return IDLE_B64[d];
    return isScream ? SCREAM_B64[d][f] : ROLL_B64[d][f];
  }
  if (p === 3) return isScream ? BELOW45_B64.scream[f] : BELOW45_B64.roll[f];
  return BELOW90_B64.roll[f];
}

// Build 5-card Vertical Pitch Strip (works in Sphere, Scream, All 3 Stunts, Drive AND all 4 360° Explosions!)
const pitchCards = [], pitchImgs = [];
for (let p = 0; p < 5; p++) {
  const c = document.createElement("div"); c.className = "p-card";
  const im = document.createElement("img"); im.src = getPitchFrameSrc(p, 0, 0, false);
  const sp = document.createElement("span");
  sp.textContent = ["+90° Above", "+45° Above", "0° Eye-Level", "-45° Below", "-90° Below"][p];
  c.appendChild(im); c.appendChild(sp);
  c.onclick = () => {
    if (mode === "drive") { setArenaCam(p <= 1 ? "above" : (p >= 3 ? "below" : "track")); return; }
    tourOn = false; curPitch = p; syncUI(); renderStage(); refreshStoryboardIfOpen();
  };
  pitchStrip.appendChild(c); pitchCards.push(c); pitchImgs.push(im);
}

// Build 8-card Horizontal 360° Yaw Strip (works in Sphere, Scream, All 3 Stunts AND all 4 360° Explosions!)
const yawCards = [], yawImgs = [];
for (let d = 0; d < DIRS; d++) {
  const c = document.createElement("div"); c.className = "y-card";
  const im = document.createElement("img"); im.src = ROLL_B64[d][0];
  const sp = document.createElement("span"); sp.textContent = (d * 45) + "°";
  c.appendChild(im); c.appendChild(sp);
  c.onclick = () => {
    if (mode === "drive") setMode("sphere");
    tourOn = false; boomOrbit = false; stuntOrbit = false; curDir = d; yawDegCont = d * 45;
    syncUI(); renderStage(); refreshStoryboardIfOpen();
  };
  yawStrip.appendChild(c); yawCards.push(c); yawImgs.push(im);
}

// 28-cell Dynamic 360° Explosion Storyboard
const boomGrid = document.getElementById("boom-grid");
const storyCells = [];
for (let i = 0; i < 28; i++) {
  const cell = document.createElement("div"); cell.className = "b-cell";
  const cv = document.createElement("canvas"); cv.width = 160; cv.height = 110;
  const sp = document.createElement("span");
  cell.appendChild(cv); cell.appendChild(sp);
  boomGrid.appendChild(cell);
  storyCells.push({ cell, cv, ctx: cv.getContext("2d"), sp, f: 0 });
}
function refreshStoryboard() {
  const cfg = TIER_INFO[curTier];
  for (let i = 0; i < 28; i++) {
    const bf = Math.min(cfg.nFrames - 1, Math.round(i * (cfg.nFrames - 1) / 27));
    const sc = storyCells[i]; sc.f = bf;
    sc.ctx.fillStyle = "#1a1412"; sc.ctx.fillRect(0, 0, 160, 110);
    sc.ctx.save(); sc.ctx.scale(160 / 640, 110 / 440);
    renderExplosion3D(sc.ctx, 640, 440, curTier, bf, yawDegCont, curPitch);
    sc.ctx.restore();
    sc.sp.textContent = `T${curTier} • f${bf} • ${Math.round(((yawDegCont%360)+360)%360)}°`;
    sc.cell.onclick = () => {
      setMode("boom", false); playing = false; boomFrame = bf; syncUI(); renderStage();
      window.scrollTo({ top: 0, behavior: "smooth" });
    };
  }
}
function refreshStoryboardIfOpen() {
  if (document.getElementById("story-details").open) refreshStoryboard();
}
document.getElementById("story-details").addEventListener("toggle", refreshStoryboardIfOpen);
window.addEventListener("load", () => setTimeout(refreshStoryboardIfOpen, 250));

function setTier(t) {
  curTier = t;
  boomFrame = 0;
  rngBoom.max = TIER_INFO[t].nFrames - 1;
  playScreamSfx(0.6, 0.9 + t * 0.08);
  syncUI();
  renderStage();
  refreshStoryboardIfOpen();
}
for (let t = 1; t <= 4; t++) document.getElementById("tbtn-" + t).onclick = () => { if (mode !== "boom") setMode("boom", false); setTier(t); playing = true; syncUI(); };
document.getElementById("btn-escalate").onclick = () => { autoEscalate = !autoEscalate; syncUI(); };

function setMode(m, resetBoom = true) {
  mode = m;
  playing = true;
  if (m === "boom" && resetBoom) { boomFrame = 0; playScreamSfx(0.6, 0.95 + curTier * 0.06); }
  if (m === "scream") playScreamSfx(0.5);
  if (m === "fire") { playBurnoutSfx(1.2); playScreamSfx(0.45, 1.08); }
  if (m === "long") playHydraulicSfx(true);
  if (m === "jetpack") playJetpackRoarSfx(1.15);
  syncUI();
  if (m !== "drive") renderStage();
}
document.getElementById("tab-sphere").onclick  = () => setMode("sphere");
document.getElementById("tab-fire").onclick    = () => setMode("fire");
document.getElementById("tab-long").onclick    = () => setMode("long");
document.getElementById("tab-jetpack").onclick = () => setMode("jetpack");
document.getElementById("tab-drive").onclick   = () => setMode("drive");
document.getElementById("tab-scream").onclick  = () => setMode("scream");
document.getElementById("tab-boom").onclick    = () => setMode("boom");

function syncUI() {
  document.getElementById("tab-sphere").className  = "tab" + (mode === "sphere"  ? " on-sphere"  : "");
  document.getElementById("tab-fire").className    = "tab" + (mode === "fire"    ? " on-fire"    : "");
  document.getElementById("tab-long").className    = "tab" + (mode === "long"    ? " on-long"    : "");
  document.getElementById("tab-jetpack").className = "tab" + (mode === "jetpack" ? " on-jetpack" : "");
  document.getElementById("tab-drive").className   = "tab" + (mode === "drive"   ? " on-drive"   : "");
  document.getElementById("tab-scream").className  = "tab" + (mode === "scream"  ? " on-scream"  : "");
  document.getElementById("tab-boom").className    = "tab" + (mode === "boom"    ? " on-boom"    : "");

  const isDrive = (mode === "drive"), isBoom = (mode === "boom"), isStunt = isStuntMode();
  tierBar.classList.toggle("hidden", !isBoom);
  for (let t = 1; t <= 4; t++) document.getElementById("tbtn-" + t).className = `t-btn t${t}` + (curTier === t ? " on" : "");
  document.getElementById("btn-escalate").className = "t-btn chain" + (autoEscalate ? " on" : "");
  document.getElementById("btn-escalate").textContent = "🚀 Auto-Escalate 1→2→3→4: " + (autoEscalate ? "ON" : "OFF");

  spriteWrap.style.display = (isDrive || isBoom || isStunt) ? "none" : "flex";
  boomCanvas.style.display = (isBoom || isStunt) ? "block" : "none";
  arenaCanvas.style.display = isDrive ? "block" : "none";

  ctrlSphere.classList.toggle("hidden", isDrive || isBoom || isStunt);
  ctrlStunt.classList.toggle("hidden", !isStunt);
  ctrlDrive.classList.toggle("hidden", !isDrive);
  ctrlBoom.classList.toggle("hidden", !isBoom);

  document.getElementById("grp-fire").style.display = (mode === "fire") ? "inline-flex" : "none";
  document.getElementById("grp-long").style.display = (mode === "long") ? "inline-flex" : "none";
  document.getElementById("grp-jet").style.display  = (mode === "jetpack") ? "inline-flex" : "none";

  document.getElementById("btn-play").textContent = playing ? "Pause" : "Play";
  document.getElementById("btn-stunt-play").textContent = playing ? "Pause" : "Play";
  document.getElementById("btn-boom-play").textContent = playing ? "Pause" : "Play / Replay";
  document.getElementById("btn-boom-orbit").textContent = "🔄 360° Bullet-Time Orbit: " + (boomOrbit ? "ON" : "OFF");
  document.getElementById("btn-boom-orbit").className = "btn " + (boomOrbit ? "blue" : "alt");
  document.getElementById("btn-stunt-orbit").textContent = "🔄 360° Stunt Orbit: " + (stuntOrbit ? "ON" : "OFF");
  document.getElementById("btn-stunt-orbit").className = "btn " + (stuntOrbit ? "blue" : "alt");
  document.getElementById("btn-long-auto").textContent = "Auto-Telescope Wave: " + (longAutoWave ? "ON" : "OFF");
  document.getElementById("btn-long-auto").className = "btn " + (longAutoWave ? "indigo" : "alt");
  document.getElementById("btn-tour").textContent = "3D Spherical Tour: " + (tourOn ? "ON" : "OFF");
  document.getElementById("btn-tour").className = "btn " + (tourOn ? "blue" : "alt");
  document.getElementById("btn-idle").textContent = "Idle: " + (idleMode ? "ON" : "OFF");

  const sfxTxt = sfxOn ? "🔊 SFX: ON" : "🔇 SFX: OFF";
  document.getElementById("btn-sfx").textContent = sfxTxt;
  document.getElementById("btn-sfx-stunt").textContent = sfxTxt;
  document.getElementById("btn-sfx2").textContent = sfxTxt;
  document.getElementById("btn-sfx3").textContent = sfxTxt;

  lblFps.textContent = rngFps.value + " fps";
  lblBoomFps.textContent = rngBoomFps.value + " fps";
  lblFireSpd.textContent = (+rngFireSpd.value).toFixed(1) + "x";
  lblLongLen.textContent = (+rngLongLen.value).toFixed(2) + "x";
  lblJpAlt.textContent = rngJpAlt.value + " px";
  lblJpSpd.textContent = (+rngJpSpd.value).toFixed(2) + "x";
  rngBoom.max = TIER_INFO[curTier].nFrames - 1;

  pitchCards.forEach((c, idx) => c.classList.toggle("on", idx === curPitch));
  yawCards.forEach((c, idx) => c.classList.toggle("on", idx === curDir));

  if (isDrive) dragHint.textContent = "WASD/Arrows: Steer • F: Fire-Wheels • L: Super-Long Bar • J: Jetpack Flight • C: Scream • E: 4x Explosion!";
  else if (isBoom) dragHint.textContent = "↔ Drag Left/Right: Orbit 360° LIVE Around Explosion!  •  ↕ Drag Up/Down: Above (+90°) & Below (-90°)!";
  else if (isStunt) dragHint.textContent = "↔ Drag Left/Right: Orbit 360° LIVE Around Stunt!  •  ↕ Drag Up/Down: View Stunt From Above (+90°) & Below (-90°)!";
  else dragHint.textContent = "↔ Drag Left/Right: 360° Yaw  •  ↕ Drag Up/Down: Above (+90°) & Below (-90°)!";
}

function renderStage() {
  if (mode === "drive") return;
  const normYaw = Math.round(((yawDegCont % 360) + 360) % 360);
  const pShort = ["+90° Above","+45° Above","Eye-Level","-45° Below","-90° Below"][curPitch];

  if (isStuntMode()) {
    const szoom = (+rngStuntZoom.value) / 100;
    boomCanvas.style.transform = `scale(${szoom})`;
    if (mode === "fire") {
      const spd = (+rngFireSpd.value) + (nitrousBoostT > 0 ? 4.5 : 0);
      renderFireWheels3D(bctx, boomCanvas.width, boomCanvas.height, stuntTime, yawDegCont, curPitch, spd);
      badge.textContent = `🔥 Fire-Wheels Hyper-Burnout • ${DIR_LABELS[curDir]} (${pShort})`;
      metaBadge.textContent = `60 FPS Live • Spin ${spd.toFixed(1)}x • Yaw ${normYaw}°`;
    } else if (mode === "long") {
      const stretch = longAutoWave ? (1.15 + 2.45 * (0.5 - 0.5 * Math.cos(stuntTime * 2.4))) : (+rngLongLen.value);
      if (longAutoWave) { rngLongLen.value = stretch.toFixed(2); lblLongLen.textContent = stretch.toFixed(2) + "x"; }
      renderSuperLongBar3D(bctx, boomCanvas.width, boomCanvas.height, stuntTime, yawDegCont, curPitch, stretch);
      badge.textContent = `📏 Super-Long Metal Bar & Wheels (${stretch.toFixed(2)}x) • ${DIR_LABELS[curDir]} (${pShort})`;
      metaBadge.textContent = `60 FPS 3D Extrusion • Span ${Math.round(stretch * 140)}px • Yaw ${normYaw}°`;
    } else if (mode === "jetpack") {
      const alt = (+rngJpAlt.value) + (afterburnBoostT > 0 ? 36 : 0);
      const rspd = (+rngJpSpd.value) + (afterburnBoostT > 0 ? 2.5 : 0);
      renderJetpackHover3D(bctx, boomCanvas.width, boomCanvas.height, stuntTime, yawDegCont, curPitch, alt, rspd);
      badge.textContent = `🚀 Jetpack Hover + Spinning Bar & Wheels • ${DIR_LABELS[curDir]} (${pShort})`;
      metaBadge.textContent = `60 FPS Live • Alt ${Math.round(alt)}px • Rotor ${rspd.toFixed(1)}x • Yaw ${normYaw}°`;
    }
    return;
  }

  const zoom = (+rngZoom.value) / 100;
  if (mode === "boom") {
    const cfg = TIER_INFO[curTier];
    renderExplosion3D(bctx, boomCanvas.width, boomCanvas.height, curTier, boomFrame, yawDegCont, curPitch);
    boomCanvas.style.transform = `scale(${zoom})`;
    badge.textContent = `${cfg.name} • ${DIR_LABELS[curDir]} (${pShort})`;
    metaBadge.textContent = `Frame ${boomFrame} / ${cfg.nFrames - 1} • Yaw ${normYaw}° • ${rngBoomFps.value} FPS`;
    rngBoom.value = boomFrame;
    lblBoomF.textContent = `${boomFrame} / ${cfg.nFrames - 1}`;
    return;
  }

  const isScream = (mode === "scream") || (quickScreamTimer > 0);
  spriteImg.src = getPitchFrameSrc(curPitch, curDir, curFrame, isScream);
  let rotDeg = 0;
  if (curPitch === 0) rotDeg = yawDegCont;
  else if (curPitch === 4) rotDeg = -yawDegCont;
  else if ((curPitch === 1 || curPitch === 3) && curDir !== 0) rotDeg = Math.sin(yawDegCont * Math.PI / 180) * -10;
  spriteImg.style.transform = `scale(${zoom}) rotate(${rotDeg.toFixed(1)}deg)`;

  badge.textContent = (isScream ? "😱 SCREAMING • " : "") + `${DIR_LABELS[curDir]} • ${PITCH_LABELS[curPitch]}`;
  metaBadge.textContent = `${rngFps.value} FPS • Pitch ${["+90°","+45°","0°","-45°","-90°"][curPitch]} • Yaw ${normYaw}° • f=${curFrame}/11`;

  for (let p = 0; p < 5; p++) {
    pitchImgs[p].src = getPitchFrameSrc(p, curDir, curFrame, isScream);
    pitchImgs[p].style.transform = p === 0 ? `rotate(${yawDegCont}deg)` : (p === 4 ? `rotate(${-yawDegCont}deg)` : "none");
  }
  for (let d = 0; d < DIRS; d++) yawImgs[d].src = isScream ? SCREAM_B64[d][curFrame] : ROLL_B64[d][curFrame];
}

// Button handlers
document.getElementById("btn-play").onclick = () => { playing = !playing; syncUI(); };
document.getElementById("btn-stunt-play").onclick = () => { playing = !playing; syncUI(); };
document.getElementById("btn-stunt-orbit").onclick = () => { stuntOrbit = !stuntOrbit; syncUI(); };
document.getElementById("btn-tour").onclick = () => { tourOn = !tourOn; syncUI(); };
document.getElementById("btn-idle").onclick = () => { idleMode = !idleMode; syncUI(); renderStage(); };
rngFps.oninput = syncUI;
rngZoom.oninput = renderStage;
rngStuntZoom.oninput = renderStage;
rngFireSpd.oninput = () => { syncUI(); renderStage(); };
rngLongLen.oninput = () => { longAutoWave = false; syncUI(); renderStage(); };
document.getElementById("btn-long-auto").onclick = () => { longAutoWave = !longAutoWave; playHydraulicSfx(true); syncUI(); };
rngJpAlt.oninput = () => { syncUI(); renderStage(); };
rngJpSpd.oninput = () => { syncUI(); renderStage(); };
document.getElementById("btn-nitrous").onclick = () => { nitrousBoostT = 1.6; playBurnoutSfx(1.55); playScreamSfx(0.6, 1.15); };
document.getElementById("btn-afterburn").onclick = () => { afterburnBoostT = 1.6; playJetpackRoarSfx(1.6); };

document.getElementById("btn-quick-fire").onclick   = () => setMode("fire");
document.getElementById("btn-quick-long").onclick   = () => setMode("long");
document.getElementById("btn-quick-jet").onclick    = () => setMode("jetpack");
document.getElementById("btn-quick-scream").onclick = () => { quickScreamTimer = 1.4; playScreamSfx(0.65); renderStage(); };
document.getElementById("btn-quick-boom").onclick   = () => setMode("boom");
const cycleBg = () => {
  stageBox.classList.remove(bgs[bgi]); bgi = (bgi + 1) % bgs.length; stageBox.classList.add(bgs[bgi]);
  document.getElementById("btn-bg").textContent = "BG: " + bgNames[bgi];
  document.getElementById("btn-stunt-bg").textContent = "BG: " + bgNames[bgi];
};
document.getElementById("btn-bg").onclick = cycleBg;
document.getElementById("btn-stunt-bg").onclick = cycleBg;
const toggleSfx = () => { sfxOn = !sfxOn; syncUI(); };
document.getElementById("btn-sfx").onclick = toggleSfx;
document.getElementById("btn-sfx-stunt").onclick = toggleSfx;
document.getElementById("btn-sfx2").onclick = toggleSfx;
document.getElementById("btn-sfx3").onclick = toggleSfx;

// Boom controls
document.getElementById("btn-boom-play").onclick = () => {
  if (!playing && boomFrame >= TIER_INFO[curTier].nFrames - 1) boomFrame = 0;
  playing = !playing; syncUI();
};
document.getElementById("btn-boom-orbit").onclick = () => { boomOrbit = !boomOrbit; syncUI(); };
document.getElementById("btn-boom-prev").onclick = () => { const n = TIER_INFO[curTier].nFrames; playing = false; boomFrame = (boomFrame - 1 + n) % n; syncUI(); renderStage(); };
document.getElementById("btn-boom-next").onclick = () => { const n = TIER_INFO[curTier].nFrames; playing = false; boomFrame = (boomFrame + 1) % n; syncUI(); renderStage(); };
rngBoom.oninput = () => { playing = false; boomFrame = +rngBoom.value; syncUI(); renderStage(); };
rngBoomFps.oninput = syncUI;
document.getElementById("act1").onclick = () => { boomFrame = 0; playing = true; playScreamSfx(0.6); syncUI(); };
document.getElementById("act2").onclick = () => { boomFrame = 14; playing = true; playOverloadWhine(curTier); syncUI(); };
document.getElementById("act3").onclick = () => { boomFrame = TIER_INFO[curTier].detF; playing = true; playExplosionBoom(0.9 + curTier * 0.32, curTier === 3); syncUI(); };
document.getElementById("act4").onclick = () => { boomFrame = TIER_INFO[curTier].act4F; playing = true; syncUI(); };
document.getElementById("act5").onclick = () => { boomFrame = TIER_INFO[curTier].act5F; playing = true; playGibSplat(); syncUI(); };

// 2D Spherical Pointer Drag — ACTIVE IN SPHERE, SCREAM, ALL 3 STUNTS & ALL 4 EXPLOSIONS!
let dragStart = null;
stageBox.addEventListener("pointerdown", e => {
  if (mode === "drive") return;
  dragStart = { x: e.clientX, y: e.clientY, yaw: yawDegCont, pitch: curPitch };
  tourOn = false; boomOrbit = false; stuntOrbit = false; syncUI();
  stageBox.classList.add("drag");
  stageBox.setPointerCapture(e.pointerId);
});
stageBox.addEventListener("pointermove", e => {
  if (!dragStart) return;
  const dx = e.clientX - dragStart.x, dy = e.clientY - dragStart.y;
  yawDegCont = dragStart.yaw - dx * 0.85;
  curDir = Math.round((((yawDegCont % 360) + 360) % 360) / 45) % DIRS;
  curPitch = Math.max(0, Math.min(4, dragStart.pitch + Math.round(dy / 52)));
  syncUI();
  renderStage();
});
const endDrag = () => { if (dragStart) refreshStoryboardIfOpen(); dragStart = null; stageBox.classList.remove("drag"); };
stageBox.addEventListener("pointerup", endDrag);
stageBox.addEventListener("pointercancel", endDrag);

// =========================================================================
// 60-FPS LIVE DRIVING & JETPACK ARENA (With Live F/L/J Stunts + 4x Explosions!)
// =========================================================================
const actx = arenaCanvas.getContext("2d");
const offBoom = document.createElement("canvas"); offBoom.width = 640; offBoom.height = 440;
const offCtx = offBoom.getContext("2d");

let autoDrive = true, autoFinale = true, arenaCam = "track", arenaNextTier = 1;
let arenaStunt = "none"; // "none" | "fire" | "long" | "jetpack"
function toggleArenaStunt(st) {
  arenaStunt = (arenaStunt === st) ? "none" : st;
  if (arenaStunt === "fire") playBurnoutSfx(1.25);
  else if (arenaStunt === "long") playHydraulicSfx(true);
  else if (arenaStunt === "jetpack") playJetpackRoarSfx(1.25);
  syncArenaStuntButtons();
}
function syncArenaStuntButtons() {
  document.getElementById("btn-drv-fire").style.outline = arenaStunt === "fire" ? "2.5px solid #fff" : "none";
  document.getElementById("btn-drv-long").style.outline = arenaStunt === "long" ? "2.5px solid #fff" : "none";
  document.getElementById("btn-drv-jet").style.outline  = arenaStunt === "jetpack" ? "2.5px solid #fff" : "none";
}
document.getElementById("btn-drv-fire").onclick = () => { autoFinale = false; syncArenaCycleBtn(); toggleArenaStunt("fire"); };
document.getElementById("btn-drv-long").onclick = () => { autoFinale = false; syncArenaCycleBtn(); toggleArenaStunt("long"); };
document.getElementById("btn-drv-jet").onclick  = () => { autoFinale = false; syncArenaCycleBtn(); toggleArenaStunt("jetpack"); };

const keys = {};
window.addEventListener("keydown", e => {
  keys[e.code] = true;
  if (mode === "drive") {
    if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight","KeyW","KeyA","KeyS","KeyD"].includes(e.code)) {
      if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(e.code)) e.preventDefault();
      autoDrive = false;
      document.getElementById("btn-autodrive").textContent = "🤖 Auto-Drive: OFF (WASD)";
      document.getElementById("btn-autodrive").className = "btn alt";
    }
    if (e.code === "KeyF") toggleArenaStunt("fire");
    if (e.code === "KeyL") toggleArenaStunt("long");
    if (e.code === "KeyJ") toggleArenaStunt("jetpack");
    if (e.code === "KeyC") triggerArenaScream();
    if (e.code === "KeyE" || e.code === "Space") { e.preventDefault(); triggerArenaExplosion(); }
  } else if (mode === "boom") {
    const n = TIER_INFO[curTier].nFrames;
    if (e.code === "ArrowRight") { e.preventDefault(); playing = false; boomFrame = (boomFrame + 1) % n; syncUI(); renderStage(); }
    if (e.code === "ArrowLeft")  { e.preventDefault(); playing = false; boomFrame = (boomFrame - 1 + n) % n; syncUI(); renderStage(); }
    if (e.code === "Space")      { e.preventDefault(); playing = !playing; syncUI(); }
    if (["Digit1","Digit2","Digit3","Digit4"].includes(e.code)) setTier(+e.code.slice(-1));
  }
});
window.addEventListener("keyup", e => { keys[e.code] = false; });

function setArenaCam(c) {
  arenaCam = c;
  document.getElementById("cam-track").classList.toggle("on", c === "track");
  document.getElementById("cam-above").classList.toggle("on", c === "above");
  document.getElementById("cam-below").classList.toggle("on", c === "below");
  curPitch = c === "above" ? 0 : (c === "below" ? 4 : 2);
  syncUI();
}
document.getElementById("cam-track").onclick = () => setArenaCam("track");
document.getElementById("cam-above").onclick = () => setArenaCam("above");
document.getElementById("cam-below").onclick = () => setArenaCam("below");
document.getElementById("btn-autodrive").onclick = () => {
  autoDrive = !autoDrive;
  document.getElementById("btn-autodrive").textContent = autoDrive ? "🤖 Auto-Drive: ON" : "🤖 Auto-Drive: OFF (WASD)";
  document.getElementById("btn-autodrive").className = autoDrive ? "btn blue" : "btn alt";
};
function syncArenaCycleBtn() {
  document.getElementById("btn-drv-cycle").textContent = "Auto-Stunts & Finale: " + (autoFinale ? "ON" : "OFF");
  document.getElementById("btn-drv-cycle").classList.toggle("on", autoFinale);
}
document.getElementById("btn-drv-cycle").onclick = () => { autoFinale = !autoFinale; syncArenaCycleBtn(); };

const car = {
  x: 470, y: 300, yaw: 0, speed: 220, wheelPhase: 0, screamT: 0,
  boomState: "alive", boomTier: 1, boomF: 0, boomTimer: 0,
  tourTime: 0, nextAutoBoom: 13.0, flashT: 0, shakeT: 0
};
const skids = [], craters = [];

function triggerArenaScream() { if (car.boomState === "alive") { car.screamT = 1.1; playScreamSfx(0.6); } }
function triggerArenaExplosion() {
  if (car.boomState !== "alive") return;
  car.boomState = "exploding";
  car.boomTier = arenaNextTier;
  arenaNextTier = (arenaNextTier % 4) + 1;
  car.boomF = 0; car.boomTimer = 0;
  playScreamSfx(0.65, 0.92 + car.boomTier * 0.07);
}
document.getElementById("btn-drv-scream").onclick = triggerArenaScream;
document.getElementById("btn-drv-boom").onclick   = triggerArenaExplosion;

function triggerBoomSfxEvents(tier, prevF, nextF) {
  const detF = TIER_INFO[tier].detF;
  if (nextF >= 14 && prevF < 14) playOverloadWhine(tier);
  if (nextF >= detF && prevF < detF) playExplosionBoom(0.9 + tier * 0.35, tier === 3);
  if (tier === 1 && nextF >= 44 && prevF < 44) playExplosionBoom(0.75, false);
  if (tier === 2 && (([34,38,58].some(k => nextF >= k && prevF < k)))) playExplosionBoom(0.95, false);
  if (tier === 3 && nextF >= 96 && prevF < 96) playExplosionBoom(1.45, true);
  if (tier === 4 && nextF >= 48 && nextF <= 114 && Math.floor((nextF-48)/12) !== Math.floor((prevF-48)/12)) playExplosionBoom(0.85, false);
  if (tier === 4 && nextF >= 152 && prevF < 152) playExplosionBoom(0.7, false);
  if (nextF >= TIER_INFO[tier].act5F + 2 && prevF < TIER_INFO[tier].act5F + 2) playGibSplat();
}

function stepAndDrawArena(dt) {
  const W = arenaCanvas.width, H = arenaCanvas.height;
  actx.save();
  if (car.shakeT > 0) {
    car.shakeT = Math.max(0, car.shakeT - dt);
    const amp = car.shakeT * (14 + car.boomTier * 6);
    actx.translate((Math.random() - 0.5) * amp, (Math.random() - 0.5) * amp);
  }

  if (arenaCam === "above") {
    actx.fillStyle = "#181c24"; actx.fillRect(0, 0, W, H);
    actx.strokeStyle = "rgba(148,163,184,0.10)"; actx.lineWidth = 1;
    for (let gx = 0; gx < W; gx += 48) { actx.beginPath(); actx.moveTo(gx, 0); actx.lineTo(gx, H); actx.stroke(); }
    for (let gy = 0; gy < H; gy += 48) { actx.beginPath(); actx.moveTo(0, gy); actx.lineTo(W, gy); actx.stroke(); }
  } else if (arenaCam === "below") {
    const grad = actx.createRadialGradient(W*0.5, H*0.5, 40, W*0.5, H*0.5, 520);
    grad.addColorStop(0, "#172536"); grad.addColorStop(1, "#090e17");
    actx.fillStyle = grad; actx.fillRect(0, 0, W, H);
    actx.strokeStyle = "rgba(56,189,248,0.16)"; actx.lineWidth = 2;
    for (let gx = 0; gx < W; gx += 64) { actx.beginPath(); actx.moveTo(gx, 0); actx.lineTo(gx, H); actx.stroke(); }
    for (let gy = 0; gy < H; gy += 64) { actx.beginPath(); actx.moveTo(0, gy); actx.lineTo(W, gy); actx.stroke(); }
  } else {
    const sky = actx.createLinearGradient(0, 0, 0, 150);
    sky.addColorStop(0, "#120c0a"); sky.addColorStop(1, "#2f1e16");
    actx.fillStyle = sky; actx.fillRect(0, 0, W, 150);
    const flr = actx.createLinearGradient(0, 150, 0, H);
    flr.addColorStop(0, "#241b16"); flr.addColorStop(1, "#15110f");
    actx.fillStyle = flr; actx.fillRect(0, 150, W, H - 150);
    actx.strokeStyle = "rgba(255,215,170,0.08)"; actx.lineWidth = 1;
    for (let i = -8; i <= 8; i++) { actx.beginPath(); actx.moveTo(W*0.5 + i * 28, 150); actx.lineTo(W*0.5 + i * 135, H); actx.stroke(); }
  }

  for (const cr of craters) {
    actx.fillStyle = "rgba(20,16,16,0.75)";
    actx.beginPath(); actx.ellipse(cr.x, cr.y, 44 + cr.tier*10, arenaCam === "track" ? 15 + cr.tier*3 : 38 + cr.tier*8, 0, 0, Math.PI*2); actx.fill();
    actx.fillStyle = cr.tier === 3 ? "rgba(34,211,238,0.55)" : (cr.tier === 4 ? "rgba(255,95,20,0.75)" : "rgba(145,14,20,0.72)");
    actx.beginPath(); actx.ellipse(cr.x, cr.y, 28 + cr.tier*7, arenaCam === "track" ? 10 + cr.tier*2 : 24 + cr.tier*5, 0, 0, Math.PI*2); actx.fill();
  }

  for (let i = skids.length - 1; i >= 0; i--) {
    const s = skids[i]; s.alpha -= dt * (s.fire ? 0.36 : 0.14);
    if (s.alpha <= 0) { skids.splice(i, 1); continue; }
    if (s.fire) {
      actx.save(); actx.globalCompositeOperation = "lighter";
      actx.strokeStyle = `rgba(255,115,18,${(s.alpha * 0.85).toFixed(2)})`; actx.lineWidth = 9;
      actx.beginPath(); actx.moveTo(s.x0, s.y0); actx.lineTo(s.x1, s.y1); actx.stroke();
      actx.strokeStyle = `rgba(255,245,150,${(s.alpha * 0.9).toFixed(2)})`; actx.lineWidth = 3.5;
      actx.beginPath(); actx.moveTo(s.x0, s.y0); actx.lineTo(s.x1, s.y1); actx.stroke();
      actx.restore();
    } else {
      actx.strokeStyle = arenaCam === "below" ? `rgba(180,220,255,${s.alpha*0.35})` : `rgba(15,15,18,${s.alpha*0.65})`;
      actx.lineWidth = 4; actx.beginPath(); actx.moveTo(s.x0, s.y0); actx.lineTo(s.x1, s.y1); actx.stroke();
    }
  }

  let prevX = car.x, prevY = car.y, prevYaw = car.yaw;
  const relDeg = ((Math.PI * 0.5 - car.yaw) * 180 / Math.PI % 360 + 360) % 360;
  const dIdx = Math.round(relDeg / 45) % DIRS;
  curDir = dIdx;

  if (car.boomState === "alive") {
    car.tourTime += dt;
    // Automatically cycle Normal -> Fire-Wheels -> Super-Long Bar -> Jetpack Flight -> Explosion when Auto-Stunts is ON!
    if (autoFinale) {
      const cyc = car.tourTime % 13.0;
      const wantSt = cyc < 3.0 ? "none" : (cyc < 6.4 ? "fire" : (cyc < 9.8 ? "long" : "jetpack"));
      if (wantSt !== arenaStunt) { arenaStunt = wantSt; syncArenaStuntButtons(); }
    }
    const spdMul = arenaStunt === "fire" ? 1.48 : (arenaStunt === "jetpack" ? 1.25 : 1.0);
    if (autoDrive) {
      const w = 1.05 * spdMul;
      const tx = W * 0.5 + Math.sin(car.tourTime * w) * 320;
      const ty = (arenaCam === "track" ? 335 : H * 0.5) + Math.sin(car.tourTime * w * 2) * (arenaCam === "track" ? 110 : 145);
      car.yaw = Math.atan2(ty - car.y, tx - car.x);
      car.x = tx; car.y = ty;
      if (autoFinale) {
        car.nextAutoBoom -= dt;
        if (car.nextAutoBoom <= 0) { car.nextAutoBoom = 13.0; triggerArenaExplosion(); }
      }
    } else {
      let turn = 0, throttle = 0;
      if (keys["ArrowLeft"]  || keys["KeyA"]) turn -= 1;
      if (keys["ArrowRight"] || keys["KeyD"]) turn += 1;
      if (keys["ArrowUp"]    || keys["KeyW"]) throttle += 1;
      if (keys["ArrowDown"]  || keys["KeyS"]) throttle -= 0.7;
      car.yaw += turn * 3.1 * dt;
      car.speed += (throttle * 290 * spdMul - car.speed) * Math.min(1, dt * 6.5);
      car.x = Math.max(65, Math.min(W - 65, car.x + Math.cos(car.yaw) * car.speed * dt));
      car.y = Math.max(arenaCam === "track" ? 185 : 55, Math.min(H - 42, car.y + Math.sin(car.yaw) * car.speed * dt));
    }
    const moved = Math.hypot(car.x - prevX, car.y - prevY);
    car.wheelPhase = (car.wheelPhase + moved * (arenaStunt === "fire" ? 0.08 : 0.022)) % 1.0;
    if (car.screamT > 0) car.screamT = Math.max(0, car.screamT - dt);
    if (car.flashT > 0) car.flashT = Math.max(0, car.flashT - dt);
    const nx = -Math.sin(car.yaw), ny = Math.cos(car.yaw);
    const ha = arenaStunt === "long" ? 68 : 28;
    if (moved > 0.8 && arenaStunt !== "jetpack") {
      skids.push({ x0: prevX + nx*ha, y0: prevY + ny*ha*0.55, x1: car.x + nx*ha, y1: car.y + ny*ha*0.55, alpha: 0.85, fire: arenaStunt === "fire" });
      skids.push({ x0: prevX - nx*ha, y0: prevY - ny*ha*0.55, x1: car.x - nx*ha, y1: car.y - ny*ha*0.55, alpha: 0.85, fire: arenaStunt === "fire" });
    }
  } else {
    const nMax = TIER_INFO[car.boomTier].nFrames;
    const detF = TIER_INFO[car.boomTier].detF;
    car.boomTimer += dt * 24.0;
    const nextF = Math.floor(car.boomTimer);
    if (nextF !== car.boomF) {
      triggerBoomSfxEvents(car.boomTier, car.boomF, nextF);
      if (nextF >= detF && car.boomF < detF) {
        car.shakeT = 0.45 + car.boomTier * 0.18;
        craters.push({ x: car.x, y: car.y + (arenaCam === "track" ? 12 : 0), tier: car.boomTier });
        if (craters.length > 7) craters.shift();
      }
      car.boomF = nextF;
    }
    if (car.boomF >= nMax - 1) {
      car.boomF = nMax - 1;
      if (car.boomTimer > nMax + 26) { car.boomState = "alive"; car.flashT = 0.45; }
    }
  }

  const fIdx = Math.floor(car.wheelPhase * FRAMES) % FRAMES;
  const pArena = arenaCam === "above" ? 0 : (arenaCam === "below" ? 4 : 2);
  if (car.boomState === "exploding") {
    renderExplosion3D(offCtx, 640, 440, car.boomTier, car.boomF, relDeg, pArena);
    const sc = arenaCam === "track" ? (0.58 + (car.y / H) * 0.45) : 0.85;
    const dw = 640 * sc, dh = 440 * sc;
    actx.drawImage(offBoom, car.x - dw * 0.5, arenaCam === "track" ? (car.y - dh * 0.87) : (car.y - dh * 0.54), dw, dh);
    badge.textContent = `${TIER_INFO[car.boomTier].name} • ${DIR_LABELS[dIdx]} (f=${car.boomF})`;
  } else if (arenaStunt !== "none") {
    if (arenaStunt === "fire") renderFireWheels3D(offCtx, 640, 440, car.tourTime, relDeg, pArena, 6.5);
    else if (arenaStunt === "long") renderSuperLongBar3D(offCtx, 640, 440, car.tourTime, relDeg, pArena, 2.35 + 0.95 * Math.sin(car.tourTime * 3.0));
    else renderJetpackHover3D(offCtx, 640, 440, car.tourTime, relDeg, pArena, 78, 2.8);
    const sc = arenaCam === "track" ? (0.48 + (car.y / H) * 0.42) : 0.72;
    const dw = 640 * sc, dh = 440 * sc;
    actx.drawImage(offBoom, car.x - dw * 0.5, arenaCam === "track" ? (car.y - dh * 0.86) : (car.y - dh * 0.52), dw, dh);
    const stNames = { fire: "🔥 FIRE-WHEELS BURNOUT", long: "📏 SUPER-LONG BAR & WHEELS", jetpack: "🚀 JETPACK FLIGHT + SPINNING BAR" };
    badge.textContent = `${stNames[arenaStunt]} • ${DIR_LABELS[dIdx]}`;
  } else if (arenaCam === "above") {
    actx.save(); actx.translate(car.x, car.y); actx.rotate(car.yaw - Math.PI * 0.5);
    actx.drawImage(IMG_ABOVE90[fIdx], -96, -91, 192, 182); actx.restore();
    badge.textContent = "🚁 Driving Around • Overhead Drone Cam (+90° Above Him)";
  } else if (arenaCam === "below") {
    actx.save(); actx.translate(car.x, car.y); actx.rotate(car.yaw + Math.PI * 0.5);
    actx.drawImage(IMG_BELOW90[fIdx], -96, -91, 192, 182); actx.restore();
    badge.textContent = "🕳️ Driving Around • Glass-Floor Cam (-90° Below Him)";
  } else {
    const sc = 0.46 + (car.y / H) * 0.44, dw = 320 * sc, dh = 304 * sc;
    actx.fillStyle = "rgba(0,0,0,0.45)";
    actx.beginPath(); actx.ellipse(car.x, car.y + 4, dw * 0.34, dh * 0.08, 0, 0, Math.PI*2); actx.fill();
    const im = car.screamT > 0 ? IMG_SCREAM[dIdx][fIdx] : IMG_ROLL[dIdx][fIdx];
    actx.save(); actx.translate(car.x, car.y); actx.rotate(Math.max(-0.14, Math.min(0.14, (car.yaw - prevYaw) * 4.5)));
    actx.drawImage(im, -dw * 0.5, -dh * 0.94, dw, dh); actx.restore();
    badge.textContent = (car.screamT > 0 ? "😱 SCREAMING! • " : "🏎️ Driving Around (60 FPS) • ") + DIR_LABELS[dIdx];
  }
  metaBadge.textContent = `60 FPS Live • F: Fire • L: Long-Bar • J: Jetpack • Next Boom: Tier ${arenaNextTier}/4`;
  actx.restore();
}

// =========================================================================
// Master Animation Loop
// =========================================================================
let lastTs = performance.now(), spriteAccum = 0, tourAccum = 0, tourPhase = 0;
const TOUR_PITCH_SEQ = [2, 2, 1, 0, 0, 2, 3, 4, 4];

function mainLoop(ts) {
  const dt = Math.min(0.05, (ts - lastTs) / 1000);
  lastTs = ts;
  if (quickScreamTimer > 0) quickScreamTimer = Math.max(0, quickScreamTimer - dt);
  if (nitrousBoostT > 0) nitrousBoostT = Math.max(0, nitrousBoostT - dt);
  if (afterburnBoostT > 0) afterburnBoostT = Math.max(0, afterburnBoostT - dt);

  if (mode === "drive") {
    stepAndDrawArena(dt);
  } else if (isStuntMode()) {
    if (playing) {
      stuntTime += dt;
      sfxPulseAccum += dt;
      if (sfxPulseAccum >= 1.35) {
        sfxPulseAccum = 0;
        if (mode === "fire") playBurnoutSfx(0.95);
        else if (mode === "long" && longAutoWave) playHydraulicSfx(Math.sin(stuntTime * 2.4) > 0);
        else if (mode === "jetpack") playJetpackRoarSfx(0.9);
      }
      if (stuntOrbit) {
        yawDegCont = (yawDegCont + dt * 42.0) % 360;
        curDir = Math.round(yawDegCont / 45) % DIRS;
        syncUI();
      }
    }
    renderStage();
  } else if (mode === "boom") {
    let dirty = false;
    if (boomOrbit) {
      yawDegCont = (yawDegCont + dt * 44.0) % 360;
      curDir = Math.round(yawDegCont / 45) % DIRS;
      syncUI();
      dirty = true;
    }
    const stepDur = 1.0 / (+rngBoomFps.value);
    if (playing) {
      spriteAccum += dt;
      if (spriteAccum >= stepDur) {
        spriteAccum %= stepDur;
        const prevB = boomFrame;
        const nMax = TIER_INFO[curTier].nFrames;
        if (boomFrame + 1 >= nMax) {
          if (autoEscalate) {
            curTier = (curTier % 4) + 1;
            boomFrame = 0;
            playScreamSfx(0.6, 0.92 + curTier * 0.07);
            syncUI();
            refreshStoryboardIfOpen();
          } else {
            boomFrame = 0;
            playScreamSfx(0.55);
          }
        } else {
          boomFrame++;
          triggerBoomSfxEvents(curTier, prevB, boomFrame);
        }
        dirty = true;
      }
    }
    if (dirty) renderStage();
  } else {
    const stepDur = 1.0 / (+rngFps.value);
    let dirty = false;
    if (playing) {
      spriteAccum += dt;
      if (spriteAccum >= stepDur) { spriteAccum %= stepDur; curFrame = (curFrame + 1) % FRAMES; dirty = true; }
    }
    if (tourOn) {
      yawDegCont = (yawDegCont + dt * 52.0) % 360;
      curDir = Math.round(yawDegCont / 45) % DIRS;
      tourAccum += dt;
      if (tourAccum > 3.2) {
        tourAccum = 0; tourPhase = (tourPhase + 1) % TOUR_PITCH_SEQ.length; curPitch = TOUR_PITCH_SEQ[tourPhase]; syncUI();
      }
      dirty = true;
    }
    if (dirty) renderStage();
  }
  requestAnimationFrame(mainLoop);
}

syncUI();
renderStage();
requestAnimationFrame(mainLoop);
</script>
</body>
</html>
"""
