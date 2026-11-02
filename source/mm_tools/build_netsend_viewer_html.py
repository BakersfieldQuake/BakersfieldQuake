"""Builds a standalone, zero-dependency WebGL2 3D Model & Animation Inspector for
the "WHERE'S THE DISK?" (LOL.BAT / NET SEND) weapon and deployable 90s school-lab PC:
  G:\\Quake\\Combat\\BakersfieldQuake\\netsend_viewer.html

Embeds the actual compiled MD3 binaries (`v_netsend.md3`, `netsend_pc.md3`,
`netsend_arc.md3`, `netsend_disk.md3`) and all 32 procedural PNG textures directly
as base64 so it opens instantaneously offline in any browser with zero server needed.
"""
import base64
import glob
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(ROOT, "progs")
OUT_HTML = os.path.join(ROOT, "netsend_viewer.html")

MD3_FILES = {
    "v_netsend": "v_netsend.md3",
    "netsend_pc": "netsend_pc.md3",
    "netsend_arc": "netsend_arc.md3",
    "netsend_disk": "netsend_disk.md3",
}


def b64_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WHERE'S THE DISK? (LOL.BAT / NET SEND) — 3D Model & Animation Inspector</title>
<style>
:root {
  --bg: #0f1115;
  --panel: #171a21;
  --panel2: #1f242d;
  --panel3: #282f3b;
  --line: #323b4a;
  --fg: #eef2f7;
  --dim: #9aa5b5;
  --accent: #39e58c;
  --accent-dim: rgba(57, 229, 140, 0.16);
  --cyan: #5ce1ff;
  --amber: #ffb84d;
  --danger: #ff6b6b;
  --mono: ui-monospace, "Cascadia Mono", "IBM Plex Mono", Consolas, monospace;
  --sans: "Segoe UI", system-ui, -apple-system, sans-serif;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; background: var(--bg); color: var(--fg); font: 13px/1.4 var(--sans); overflow: hidden; }
body { display: flex; flex-direction: column; }

header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 9px 14px; background: var(--panel); border-bottom: 1px solid var(--line); flex-wrap: wrap;
}
.brand { display: flex; align-items: baseline; gap: 10px; }
.brand h1 { margin: 0; font: 800 16px var(--mono); letter-spacing: 0.03em; color: var(--accent); }
.brand span { font: 12px var(--mono); color: var(--dim); }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.tab {
  font: 600 12px var(--mono); color: var(--fg); background: var(--panel2);
  border: 1px solid var(--line); border-radius: 6px; padding: 6px 11px; cursor: pointer;
  transition: border-color .12s, background .12s;
}
.tab:hover { border-color: var(--accent); }
.tab.active { background: var(--accent); color: #081a10; border-color: var(--accent); font-weight: 800; }

main {
  flex: 1; min-height: 0; display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
}
#viewport-wrap {
  position: relative; display: flex; flex-direction: column; min-height: 0; background: #090b0e;
}
#stage {
  flex: 1; min-height: 0; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden;
}
#canvas-box {
  position: relative; width: 100%; height: 100%; cursor: grab; touch-action: none;
}
#canvas-box.fp-aspect {
  width: auto; height: auto; max-width: 100%; max-height: 100%; aspect-ratio: 16 / 9;
  box-shadow: 0 0 0 1px var(--line), 0 16px 48px rgba(0,0,0,0.65);
}
#canvas-box.dragging { cursor: grabbing; }
canvas { display: block; width: 100%; height: 100%; }

#crosshair {
  position: absolute; left: 50%; top: 50%; width: 16px; height: 16px; margin: -8px 0 0 -8px;
  pointer-events: none; display: none;
}
#crosshair::before, #crosshair::after { content: ""; position: absolute; background: #3cff5e; box-shadow: 0 0 4px #000; }
#crosshair::before { left: 7px; top: 0; width: 2px; height: 16px; }
#crosshair::after { top: 7px; left: 0; width: 16px; height: 2px; }

#quake-hud {
  position: absolute; left: 0; right: 0; bottom: 0; height: 12%;
  background: repeating-linear-gradient(135deg, rgba(16,14,10,0.72) 0 10px, rgba(28,23,16,0.58) 10px 20px);
  border-top: 1px dashed rgba(255,215,130,0.4);
  color: rgba(255,232,185,0.82); font: 600 11px var(--mono);
  display: none; align-items: center; justify-content: center; pointer-events: none;
}

#hud-overlay {
  position: absolute; left: 12px; top: 12px; display: flex; flex-direction: column; gap: 6px; pointer-events: none;
}
.badge {
  background: rgba(12, 15, 20, 0.82); border: 1px solid rgba(90, 110, 140, 0.4);
  backdrop-filter: blur(4px); border-radius: 6px; padding: 6px 10px; font: 11.5px/1.45 var(--mono); color: var(--fg);
}
.badge b { color: var(--accent); }
.badge .sub { color: var(--dim); }
#event-pill {
  display: none; background: rgba(255, 184, 77, 0.18); border: 1px solid var(--amber);
  color: var(--amber); font: 700 12px var(--mono); padding: 5px 10px; border-radius: 6px;
}

#help-overlay {
  position: absolute; right: 12px; top: 12px; background: rgba(12,15,20,0.76);
  border: 1px solid rgba(90,110,140,0.35); border-radius: 6px; padding: 5px 9px;
  font: 11px var(--mono); color: var(--dim); pointer-events: none;
}

/* Bottom transport bar */
#transport {
  background: var(--panel); border-top: 1px solid var(--line); padding: 10px 14px;
  display: flex; flex-direction: column; gap: 8px;
}
.transport-row {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
button, select {
  font: 12px var(--mono); color: var(--fg); background: var(--panel2);
  border: 1px solid var(--line); border-radius: 5px; padding: 5px 9px; cursor: pointer;
}
button:hover, select:hover { border-color: var(--accent); }
button.active, button.primary {
  background: var(--accent-dim); border-color: var(--accent); color: var(--accent); font-weight: 700;
}
#scrubber { flex: 1; min-width: 180px; accent-color: var(--accent); cursor: pointer; }
#frame-readout { font: 700 12px var(--mono); min-width: 175px; text-align: right; color: var(--cyan); }

/* Right inspector sidebar */
aside {
  background: var(--panel); border-left: 1px solid var(--line); padding: 12px;
  overflow-y: auto; display: flex; flex-direction: column; gap: 11px;
}
section {
  background: var(--panel2); border: 1px solid var(--line); border-radius: 7px; padding: 9px 11px;
}
section h2 {
  margin: 0 0 7px 0; font: 700 11px var(--mono); text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--dim); display: flex; justify-content: space-between;
}
.clip-list, .cam-grid { display: flex; flex-wrap: wrap; gap: 5px; }
.clip-btn { flex: 1 1 calc(50% - 5px); text-align: left; padding: 6px 8px; font-size: 11.5px; }
.clip-btn small { display: block; color: var(--dim); font-size: 10px; margin-top: 1px; }
.clip-btn.active small { color: var(--accent); }
.cam-btn { font-size: 11px; padding: 4px 8px; }

.ctrl-row {
  display: grid; grid-template-columns: 92px 1fr 48px; align-items: center; gap: 7px; margin-top: 6px;
}
.ctrl-row label { font: 11.5px var(--mono); color: var(--dim); }
.ctrl-row input[type=range] { width: 100%; accent-color: var(--accent); }
.ctrl-row .val { font: 11.5px var(--mono); text-align: right; color: var(--fg); }

.chk-list { display: flex; flex-direction: column; gap: 5px; }
.chk { display: flex; align-items: center; gap: 7px; font: 12px var(--mono); color: var(--fg); cursor: pointer; }
.chk input { accent-color: var(--accent); margin: 0; }
.chk small { color: var(--dim); }

.stat-table { width: 100%; border-collapse: collapse; font: 11.5px var(--mono); }
.stat-table td { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.stat-table td:last-child { text-align: right; color: var(--cyan); }

@media (max-width: 980px) {
  html, body { overflow: auto; }
  main { grid-template-columns: 1fr; }
  #stage { min-height: 440px; }
  aside { border-left: none; border-top: 1px solid var(--line); }
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>WHERE'S THE DISK? // LOL.BAT</h1>
    <span>MD3 + Q3 Shader + Skin Inspector (DarkPlaces Quake 1.5)</span>
  </div>
  <div class="tabs" id="mode-tabs">
    <button class="tab active" data-mode="story">★ Full Story Sequence</button>
    <button class="tab" data-mode="netsend_pc">Deployable 486 PC</button>
    <button class="tab" data-mode="v_netsend">First-Person Viewmodel</button>
    <button class="tab" data-mode="netsend_arc">3D Lightning Cage</button>
    <button class="tab" data-mode="netsend_disk">World Floppy Disk</button>
  </div>
</header>

<main>
  <div id="viewport-wrap">
    <div id="stage">
      <div id="canvas-box">
        <canvas id="gl"></canvas>
        <div id="crosshair"></div>
        <div id="quake-hud">QUAKE STATUS BAR STRIP (12% HEIGHT) — FOV 111 (125.7° H × 94.8° V)</div>
      </div>

      <div id="hud-overlay">
        <div class="badge" id="model-badge">Loading MD3 assets…</div>
        <div id="event-pill"></div>
      </div>

      <div id="help-overlay" id="mouse-tip">Left-drag: Orbit · Right/Shift-drag: Pan · Wheel: Zoom · Space: Play/Pause · ←/→: Step</div>
    </div>

    <div id="transport">
      <div class="transport-row">
        <button id="btn-play" class="primary" style="min-width:84px">⏸ Pause</button>
        <button id="btn-prev" title="Previous frame (Left Arrow)">◀ -1</button>
        <button id="btn-next" title="Next frame (Right Arrow)">+1 ▶</button>
        <input type="range" id="scrubber" min="0" max="49" step="0.01" value="0">
        <span id="frame-readout">Frame 0 / 49</span>
      </div>
      <div class="transport-row" style="justify-content:space-between">
        <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap">
          <span style="font:11px var(--mono); color:var(--dim)">Speed:</span>
          <button class="spd-btn" data-spd="0.1">0.1×</button>
          <button class="spd-btn" data-spd="0.25">0.25×</button>
          <button class="spd-btn" data-spd="0.5">0.5×</button>
          <button class="spd-btn active" data-spd="1">1×</button>
          <button class="spd-btn" data-spd="1.5">1.5×</button>
          <button class="spd-btn" data-spd="2">2×</button>
        </div>
        <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap">
          <label class="chk"><input type="checkbox" id="chk-lerp" checked> Smooth Frame Lerp</label>
          <label class="chk"><input type="checkbox" id="chk-loop" checked> Loop Clip</label>
        </div>
      </div>
    </div>
  </div>

  <aside>
    <section id="sec-clips">
      <h2>Animation Clips <span id="clip-fps-label">10 fps</span></h2>
      <div class="clip-list" id="clip-list"></div>
    </section>

    <section id="sec-cam">
      <h2>Camera Presets</h2>
      <div class="cam-grid" id="cam-list"></div>
    </section>

    <section id="sec-pc-opts">
      <h2>CRT Skin & Turret Controls</h2>
      <div style="display:flex; flex-direction:column; gap:7px">
        <label style="font:11.5px var(--mono); color:var(--dim)">CRT Screen Skin (`self.skin` / `.skin` file):</label>
        <select id="sel-skin">
          <option value="auto">Auto-Sync with Frame (Boot → Active → Dot)</option>
          <option value="0">skin 0 — Active Live-Typing Loop (16-frame animmap)</option>
          <option value="1">skin 1 — CRT Off (Dark Glass)</option>
          <option value="2">skin 2 — Power-On Static Noise (14 Hz)</option>
          <option value="3">skin 3 — INITIALIZING BATCH FILE...</option>
          <option value="4">skin 4 — C:\&gt; LOL.BAT</option>
          <option value="5">skin 5 — NET SEND * LOL</option>
          <option value="6">skin 6 — Shutdown Phosphor Collapse Dot</option>
        </select>
        <label class="chk"><input type="checkbox" id="chk-arc" checked> Show 3D Lightning Cage (`netsend_arc.md3`)</label>
        <label class="chk"><input type="checkbox" id="chk-spin"> Spin PC Around Base (`self.angles_y`)</label>
        <label class="chk"><input type="checkbox" id="chk-hull"> Show Quake Collision Hull (`32×32×60`) &amp; Antenna Tips</label>
      </div>
    </section>

    <section id="sec-vm-opts" style="display:none">
      <h2>Viewmodel Camera Mode</h2>
      <div class="chk-list">
        <label class="chk"><input type="checkbox" id="chk-fpcam" checked> Lock to Game First-Person Camera (`fov 111`)</label>
        <label class="chk"><input type="checkbox" id="chk-fphud" checked> Show Crosshair &amp; Quake Status Bar Strip</label>
      </div>
    </section>

    <section>
      <h2>Display &amp; Surfaces</h2>
      <div class="chk-list" style="margin-bottom:8px">
        <label class="chk"><input type="checkbox" id="chk-wire"> Wireframe Overlay</label>
        <label class="chk"><input type="checkbox" id="chk-floor" checked> Quake Reference Grid Floor (`z = 0`)</label>
      </div>
      <div class="ctrl-row">
        <label>DP Exposure</label>
        <input type="range" id="rng-exp" min="0.8" max="3.5" step="0.05" value="2.30">
        <span class="val" id="val-exp">2.30×</span>
      </div>
      <div style="margin-top:9px; font:11px var(--mono); color:var(--dim)">Active MD3 Surfaces:</div>
      <div class="chk-list" id="surf-toggles" style="margin-top:5px"></div>
    </section>

    <section>
      <h2>Model &amp; Frame Specs</h2>
      <table class="stat-table" id="stat-table"></table>
    </section>
  </aside>
</main>

<script id="embedded-data" type="application/json">__PAYLOAD__</script>
<script>
(() => {
"use strict";

const PAYLOAD = JSON.parse(document.getElementById("embedded-data").textContent);
const $ = id => document.getElementById(id);

// ============================================================================
// 1. Binary MD3 Parser (Quake coords (x,y,z) -> WebGL (-y, z, -x))
// ============================================================================
function b64ToArrayBuffer(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}

function decodeMD3Normal(code) {
  if (code === 0) return [0, 1, 0];
  const lat = ((code >> 8) & 255) * (2 * Math.PI / 255);
  const lng = (code & 255) * (2 * Math.PI / 255);
  // Quake normal: x = cos(lat)*sin(lng)? Wait: MD3 standard:
  // byte0 (high, code>>8) = lat (zenith from +Z), byte1 (low, code&255) = lng (azimuth in XY)
  const qx = Math.cos(lng) * Math.sin(lat);
  const qy = Math.sin(lng) * Math.sin(lat);
  const qz = Math.cos(lat);
  return [-qy, qz, -qx];
}

function parseMD3(buf) {
  const dv = new DataView(buf);
  const i32 = o => dv.getInt32(o, true);
  const readStr = (o, maxLen) => {
    let s = "";
    for (let i = 0; i < maxLen; i++) {
      const c = dv.getUint8(o + i);
      if (!c) break;
      s += String.fromCharCode(c);
    }
    return s;
  };

  const nFrames = i32(76);
  const nSurfs = i32(84);
  let surfOfs = i32(100);
  const surfaces = [];
  let totalTris = 0, totalVerts = 0;

  for (let s = 0; s < nSurfs; s++) {
    const name = readStr(surfOfs + 4, 64);
    const nf = i32(surfOfs + 72);
    const nv = i32(surfOfs + 80);
    const nt = i32(surfOfs + 84);
    const ofsTris = i32(surfOfs + 88);
    const ofsShaders = i32(surfOfs + 92);
    const ofsSt = i32(surfOfs + 96);
    const ofsXyz = i32(surfOfs + 100);
    const ofsEnd = i32(surfOfs + 104);

    const shader = readStr(surfOfs + ofsShaders, 64);
    const indices = new Uint16Array(nt * 3);
    for (let i = 0; i < nt * 3; i++) {
      indices[i] = i32(surfOfs + ofsTris + i * 4);
    }

    // Build deduplicated wireframe edge index buffer
    const edgeSet = new Set();
    const edgeList = [];
    for (let t = 0; t < nt; t++) {
      const a = indices[t * 3], b = indices[t * 3 + 1], c = indices[t * 3 + 2];
      const pairs = [[a, b], [b, c], [c, a]];
      for (const [u, v] of pairs) {
        const lo = u < v ? u : v, hi = u < v ? v : u;
        const key = (lo << 16) | hi;
        if (!edgeSet.has(key)) {
          edgeSet.add(key);
          edgeList.push(lo, hi);
        }
      }
    }
    const wireIndices = new Uint16Array(edgeList);

    const uvs = new Float32Array(nv * 2);
    for (let i = 0; i < nv; i++) {
      uvs[i * 2]     = dv.getFloat32(surfOfs + ofsSt + i * 8, true);
      uvs[i * 2 + 1] = dv.getFloat32(surfOfs + ofsSt + i * 8 + 4, true);
    }

    const frames = [];
    for (let f = 0; f < nf; f++) {
      const pos = new Float32Array(nv * 3);
      const nrm = new Float32Array(nv * 3);
      const base = surfOfs + ofsXyz + f * nv * 8;
      for (let i = 0; i < nv; i++) {
        const qx = dv.getInt16(base + i * 8, true) / 64.0;
        const qy = dv.getInt16(base + i * 8 + 2, true) / 64.0;
        const qz = dv.getInt16(base + i * 8 + 4, true) / 64.0;
        pos[i * 3]     = -qy;
        pos[i * 3 + 1] =  qz;
        pos[i * 3 + 2] = -qx;
        const dn = decodeMD3Normal(dv.getUint16(base + i * 8 + 6, true));
        nrm[i * 3]     = dn[0];
        nrm[i * 3 + 1] = dn[1];
        nrm[i * 3 + 2] = dn[2];
      }
      frames.push({ pos, nrm });
    }

    surfaces.push({ name, shader, nv, nt, indices, wireIndices, uvs, frames, visible: true });
    totalTris += nt;
    totalVerts += nv;
    surfOfs += ofsEnd;
  }

  return { nFrames, surfaces, totalTris, totalVerts };
}

// ============================================================================
// 2. WebGL2 Setup, Shaders & GPU Buffers
// ============================================================================
const canvas = $("gl");
const canvasBox = $("canvas-box");
const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, preserveDrawingBuffer: true });
if (!gl) {
  $("model-badge").innerHTML = "<b style='color:#ff6b6b'>WebGL2 not available in this browser</b>";
  throw new Error("WebGL2 unavailable");
}
const extAniso = gl.getExtension("EXT_texture_filter_anisotropic");

const VS_MESH = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;

uniform mat4 uMVP;
uniform mat4 uModel;

out vec3 vNrm;
out vec2 vUV;

void main() {
  gl_Position = uMVP * vec4(aPos, 1.0);
  vNrm = mat3(uModel) * aNrm;
  vUV = aUV;
}`;

const FS_MESH = `#version 300 es
precision highp float;

in vec3 vNrm;
in vec2 vUV;

uniform sampler2D uTex;
uniform int uMode;       // 0=lit diffuse, 1=unlit identity (CRT/LEDs), 2=additive arc, 3=solid color
uniform float uExposure;
uniform vec4 uSolidColor;

out vec4 outColor;

void main() {
  if (uMode == 3) {
    outColor = uSolidColor;
    return;
  }
  vec4 texel = texture(uTex, vUV);
  if (uMode == 2) {
    outColor = vec4(texel.rgb * 1.45, 1.0);
    return;
  }
  if (uMode == 1) {
    outColor = vec4(texel.rgb * uExposure, 1.0);
    return;
  }
  vec3 N = normalize(vNrm);
  if (!gl_FrontFacing) N = -N;
  vec3 L1 = normalize(vec3(0.42, 0.78, -0.46));
  vec3 L2 = normalize(vec3(-0.65, 0.35, 0.66));
  float diff = 0.56 + 0.46 * max(dot(N, L1), 0.0) + 0.16 * max(dot(N, L2), 0.0);
  outColor = vec4(texel.rgb * diff * uExposure, 1.0);
}`;

function compileProgram(vsSrc, fsSrc) {
  const mk = (type, src) => {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  };
  const p = gl.createProgram();
  gl.attachShader(p, mk(gl.VERTEX_SHADER, vsSrc));
  gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fsSrc));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
}

const prog = compileProgram(VS_MESH, FS_MESH);
const U = {
  uMVP: gl.getUniformLocation(prog, "uMVP"),
  uModel: gl.getUniformLocation(prog, "uModel"),
  uTex: gl.getUniformLocation(prog, "uTex"),
  uMode: gl.getUniformLocation(prog, "uMode"),
  uExposure: gl.getUniformLocation(prog, "uExposure"),
  uSolidColor: gl.getUniformLocation(prog, "uSolidColor"),
};

// Load textures (UNPACK_FLIP_Y_WEBGL = false matches MD3 top-left UV origin directly)
gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
const textures = {};
const whiteTex = gl.createTexture();
gl.bindTexture(gl.TEXTURE_2D, whiteTex);
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([255,255,255,255]));

for (const [key, dataUri] of Object.entries(PAYLOAD.textures)) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([32,36,42,255]));
  const img = new Image();
  img.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    const clamp = key.includes("netsend_s_");
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, clamp ? gl.CLAMP_TO_EDGE : gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, clamp ? gl.CLAMP_TO_EDGE : gl.REPEAT);
    if (extAniso) {
      const maxA = gl.getParameter(extAniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT);
      gl.texParameterf(gl.TEXTURE_2D, extAniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, maxA));
    }
  };
  img.src = dataUri;
  textures[key] = tex;
}

// Parse all 4 MD3 models & allocate dynamic vertex buffers
const models = {};
for (const [key, b64] of Object.entries(PAYLOAD.md3)) {
  const parsed = parseMD3(b64ToArrayBuffer(b64));
  for (const s of parsed.surfaces) {
    s.vao = gl.createVertexArray();
    gl.bindVertexArray(s.vao);

    s.posBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, s.posBuf);
    gl.bufferData(gl.ARRAY_BUFFER, s.nv * 3 * 4, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);

    s.nrmBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, s.nrmBuf);
    gl.bufferData(gl.ARRAY_BUFFER, s.nv * 3 * 4, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 0, 0);

    s.uvBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, s.uvBuf);
    gl.bufferData(gl.ARRAY_BUFFER, s.uvs, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(2);
    gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 0, 0);

    s.idxBuf = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.idxBuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, s.indices, gl.STATIC_DRAW);

    s.wireVao = gl.createVertexArray();
    gl.bindVertexArray(s.wireVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, s.posBuf);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    s.wireIdxBuf = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.wireIdxBuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, s.wireIndices, gl.STATIC_DRAW);

    s.scratchPos = new Float32Array(s.nv * 3);
    s.scratchNrm = new Float32Array(s.nv * 3);
  }
  gl.bindVertexArray(null);
  models[key] = parsed;
}

// Helper line geometry: Floor grid + Collision hull (-16..16, -16..16, 0..60) + 4 Antenna tip crosses
function createLineVAO(verts) {
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(verts), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
  gl.bindVertexArray(null);
  return { vao, count: verts.length / 3 };
}

const gridLines = (() => {
  const v = [];
  const half = 96, step = 8;
  for (let i = -half; i <= half; i += step) {
    v.push(i, 0, -half, i, 0, half);
    v.push(-half, 0, i, half, 0, i);
  }
  return createLineVAO(v);
})();

const axesLines = createLineVAO([
  // Front (+X_q -> -Z_gl) arrow on floor
  0, 0.08, 0,   0, 0.08, -26,
  0, 0.08, -26, -2.5, 0.08, -22,
  0, 0.08, -26,  2.5, 0.08, -22,
]);

const hullLines = (() => {
  const v = [];
  const x0 = -16, x1 = 16, y0 = 0, y1 = 60, z0 = -16, z1 = 16;
  const corners = [
    [x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1],
    [x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]
  ];
  const edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  for (const [a, b] of edges) v.push(...corners[a], ...corners[b]);
  // 4 Antenna tip local markers in Quake coords -> (-y, z, -x)
  const tipsQ = [[2.6, 10.4, 62.8], [2.6, -10.4, 62.8], [0.6, 14.8, 50.2], [0.6, -14.8, 50.2]];
  for (const [qx, qy, qz] of tipsQ) {
    const gx = -qy, gy = qz, gz = -qx, r = 1.6;
    v.push(gx-r,gy,gz, gx+r,gy,gz, gx,gy-r,gz, gx,gy+r,gz, gx,gy,gz-r, gx,gy,gz+r);
  }
  return createLineVAO(v);
})();

// ============================================================================
// 3. Q3 Shader & CRT Skin `animmap` Resolver (exact match to scripts/netsend.shader)
// ============================================================================
const SKIN_SHADERS = {
  0: { fps: 6,  frames: Array.from({length: 16}, (_, i) => `progs/netsend_s_l${String(i).padStart(2, "0")}`) },
  1: { fps: 1,  frames: ["progs/netsend_s_off"] },
  2: { fps: 14, frames: ["progs/netsend_s_n0", "progs/netsend_s_n1", "progs/netsend_s_n2"] },
  3: { fps: 4,  frames: ["progs/netsend_s_init0", "progs/netsend_s_init1"] },
  4: { fps: 4,  frames: ["progs/netsend_s_lol0", "progs/netsend_s_lol1"] },
  5: { fps: 3,  frames: ["progs/netsend_s_fst0", "progs/netsend_s_fst1"] },
  6: { fps: 3,  frames: ["progs/netsend_s_dot0", "progs/netsend_s_dot1"] },
};

function autoSkinForPcFrame(f) {
  const fi = Math.floor(f);
  if (fi <= 9) return 1;
  if (fi <= 11) return 2;
  if (fi <= 14) return 3;
  if (fi <= 16) return 4;
  if (fi <= 19) return 5;
  if (fi <= 39) return 0;
  if (fi <= 48) return 6;
  return 1;
}

function resolveSurfaceMaterial(surf, skinIdx, wallClockSec) {
  if (surf.name === "netsend_screen") {
    const spec = SKIN_SHADERS[skinIdx] || SKIN_SHADERS[0];
    const idx = Math.floor(wallClockSec * spec.fps) % spec.frames.length;
    return { tex: textures[spec.frames[idx]] || whiteTex, mode: 1 };
  }
  if (surf.shader === "progs/netsend_leds") {
    return { tex: textures["progs/netsend_leds"] || whiteTex, mode: 1 };
  }
  if (surf.shader === "progs/netsend_arc") {
    return { tex: textures["progs/netsend_arc"] || whiteTex, mode: 2 };
  }
  return { tex: textures[surf.shader] || whiteTex, mode: 0 };
}

// ============================================================================
// 4. Matrix Math & Orbit / First-Person Camera
// ============================================================================
function mat4Identity() {
  const m = new Float32Array(16);
  m[0] = m[5] = m[10] = m[15] = 1;
  return m;
}
function mat4Mul(a, b) {
  const out = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let r = 0; r < 4; r++) {
      out[c * 4 + r] =
        a[0 * 4 + r] * b[c * 4 + 0] +
        a[1 * 4 + r] * b[c * 4 + 1] +
        a[2 * 4 + r] * b[c * 4 + 2] +
        a[3 * 4 + r] * b[c * 4 + 3];
    }
  }
  return out;
}
function mat4Perspective(vfovRad, aspect, near, far) {
  const f = 1.0 / Math.tan(vfovRad * 0.5);
  const nf = 1.0 / (near - far);
  const out = new Float32Array(16);
  out[0] = f / aspect;
  out[5] = f;
  out[10] = (far + near) * nf;
  out[11] = -1;
  out[14] = (2 * far * near) * nf;
  return out;
}
function mat4LookAt(eye, center, up) {
  let zx = eye[0] - center[0], zy = eye[1] - center[1], zz = eye[2] - center[2];
  let len = Math.hypot(zx, zy, zz) || 1;
  zx /= len; zy /= len; zz /= len;
  let xx = up[1] * zz - up[2] * zy;
  let xy = up[2] * zx - up[0] * zz;
  let xz = up[0] * zy - up[1] * zx;
  len = Math.hypot(xx, xy, xz) || 1;
  xx /= len; xy /= len; xz /= len;
  const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
  const out = new Float32Array(16);
  out[0] = xx; out[4] = xy; out[8]  = xz; out[12] = -(xx * eye[0] + xy * eye[1] + xz * eye[2]);
  out[1] = yx; out[5] = yy; out[9]  = yz; out[13] = -(yx * eye[0] + yy * eye[1] + yz * eye[2]);
  out[2] = zx; out[6] = zy; out[10] = zz; out[14] = -(zx * eye[0] + zy * eye[1] + zz * eye[2]);
  out[15] = 1;
  return out;
}
function mat4TranslateRotateY(tx, ty, tz, yawRad) {
  const c = Math.cos(yawRad), s = Math.sin(yawRad);
  const out = mat4Identity();
  out[0] = c;  out[8] = s;
  out[2] = -s; out[10] = c;
  out[12] = tx; out[13] = ty; out[14] = tz;
  return out;
}

const cam = {
  target: [0, 28, 0],
  az: Math.PI * 0.84,
  el: 0.20,
  dist: 78,
  vfovDeg: 46,
};

function setCamPreset(p) {
  cam.target = p.target.slice();
  cam.az = p.az;
  cam.el = p.el;
  cam.dist = p.dist;
}

// Mouse / Pointer Orbit + Pan + Zoom
let dragBtn = -1, lastX = 0, lastY = 0;
canvasBox.addEventListener("contextmenu", e => e.preventDefault());
canvasBox.addEventListener("pointerdown", e => {
  if (state.mode === "v_netsend" && $("chk-fpcam").checked) return;
  dragBtn = (e.button === 2 || e.shiftKey) ? 2 : 0;
  lastX = e.clientX; lastY = e.clientY;
  canvasBox.classList.add("dragging");
  canvasBox.setPointerCapture(e.pointerId);
});
canvasBox.addEventListener("pointermove", e => {
  if (dragBtn < 0) return;
  const dx = e.clientX - lastX, dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  if (dragBtn === 0) {
    cam.az -= dx * 0.0075;
    cam.el = Math.max(-1.42, Math.min(1.48, cam.el + dy * 0.0075));
  } else {
    const scale = cam.dist * 0.0016;
    const rx = Math.cos(cam.az), rz = -Math.sin(cam.az);
    cam.target[0] -= dx * rx * scale;
    cam.target[2] -= dx * rz * scale;
    cam.target[1] += dy * scale;
  }
});
window.addEventListener("pointerup", () => { dragBtn = -1; canvasBox.classList.remove("dragging"); });
canvasBox.addEventListener("wheel", e => {
  e.preventDefault();
  if (state.mode === "v_netsend" && $("chk-fpcam").checked) return;
  cam.dist = Math.max(8, Math.min(360, cam.dist * Math.exp(e.deltaY * 0.0011)));
}, { passive: false });

// ============================================================================
// 5. Modes, Animation Clips & Camera Presets
// ============================================================================
const MODES = {
  story: {
    title: "Full Story Sequence (Disk → Pop-Up → Boot → Active Zap → Shutdown)",
    fps: 10,
    clips: [
      { label: "Full Choreographed Story", sub: "0–149 (15.0s)", start: 0, end: 149, fps: 10, loop: true },
      { label: "1. Thrown & Floor Stick", sub: "0–14 (disk)", start: 0, end: 14, fps: 10, loop: true },
      { label: "2. Materialize Pop-Up", sub: "15–24 (stretch/squash)", start: 15, end: 24, fps: 10, loop: true },
      { label: "3. Boot & LOL.BAT", sub: "25–44 (skins 2→5)", start: 25, end: 44, fps: 10, loop: true },
      { label: "4. Active + 3D Lightning", sub: "45–129 (spin + skin 0)", start: 45, end: 129, fps: 10, loop: true },
      { label: "5. CRT Collapse Shutdown", sub: "130–149 (skin 6→1)", start: 130, end: 149, fps: 10, loop: true },
    ],
    cams: [
      { label: "3/4 Showcase", target: [0, 27, 0], az: Math.PI * 0.84, el: 0.20, dist: 82 },
      { label: "Front Straight", target: [0, 29, 0], az: Math.PI, el: 0.08, dist: 74 },
      { label: "40u Screen Check", target: [0, 39, -2], az: Math.PI, el: 0.03, dist: 46 },
      { label: "CRT Close-Up", target: [0, 42, -5], az: Math.PI, el: 0.02, dist: 25 },
      { label: "Floor Disk & Base", target: [0, 12, 0], az: Math.PI * 0.80, el: 0.28, dist: 44 },
      { label: "180° Rear Sticker", target: [0, 34, 0], az: 0.0, el: 0.08, dist: 62 },
    ],
  },
  netsend_pc: {
    title: "progs/netsend_pc.md3 — Deployable 90s School-Lab 486DX PC",
    fps: 10,
    clips: [
      { label: "Active Ghost-Typing Loop", sub: "frames 20–39 (10 fps)", start: 20, end: 39, fps: 10, loop: true },
      { label: "All 50 Vertex Frames", sub: "frames 0–49 (full MD3)", start: 0, end: 49, fps: 10, loop: true },
      { label: "Materialize Pop-Up", sub: "frames 0–9 (from disk)", start: 0, end: 9, fps: 10, loop: true },
      { label: "Boot + Degauss + LEDs", sub: "frames 10–19 (skins 2–5)", start: 10, end: 19, fps: 7, loop: true },
      { label: "Shutdown Slump & Droop", sub: "frames 40–49 (skin 6)", start: 40, end: 49, fps: 8, loop: true },
    ],
    cams: [
      { label: "3/4 Hero", target: [0, 28, 0], az: Math.PI * 0.83, el: 0.19, dist: 78 },
      { label: "Front Straight", target: [0, 29, 0], az: Math.PI, el: 0.06, dist: 72 },
      { label: "40u Readability", target: [0, 41, -3], az: Math.PI, el: 0.02, dist: 45 },
      { label: "CRT Close-Up", target: [0, 42.5, -6], az: Math.PI, el: 0.0, dist: 24 },
      { label: "Ghost Keyboard + A:", target: [0, 25.5, -8], az: Math.PI * 0.94, el: 0.45, dist: 26 },
      { label: "90° Side Profile", target: [0, 29, 0], az: Math.PI * 0.5, el: 0.08, dist: 76 },
      { label: "180° Rear Sticker", target: [0, 35, 3], az: 0.0, el: 0.06, dist: 48 },
    ],
  },
  v_netsend: {
    title: "progs/v_netsend.md3 — First-Person Ranger Hand + LOL.BAT Disk",
    fps: 10,
    clips: [
      { label: "Full Idle Loop", sub: "frames 0–39 (seamless)", start: 0, end: 39, fps: 10, loop: true },
      { label: "Fire + Follow + Reload", sub: "frames 40–59 (release @ 44)", start: 40, end: 59, fps: 11, loop: true },
      { label: "All 60 Vertex Frames", sub: "frames 0–59 (full MD3)", start: 0, end: 59, fps: 10, loop: true },
      { label: "Smug Idle Hold", sub: "frames 0–7", start: 0, end: 7, fps: 10, loop: true },
      { label: "Twirl & 180° Shutter Flip", sub: "frames 8–22 (back @ 14–16)", start: 8, end: 22, fps: 9, loop: true },
      { label: "Back Shutter Hold", sub: "frames 14–16 (metal hub)", start: 14, end: 16, fps: 4, loop: true },
      { label: "Inspect Label & Nod", sub: "frames 23–33", start: 23, end: 33, fps: 10, loop: true },
      { label: "Wind-Up & Throw", sub: "frames 40–47 (release @ 44)", start: 40, end: 47, fps: 9, loop: true },
      { label: "Reload Slide-In", sub: "frames 54–59", start: 54, end: 59, fps: 9, loop: true },
    ],
    cams: [
      { label: "Game FP View (FOV 111)", fp: true },
      { label: "3D Orbit — Front Label", fp: false, target: [6.5, -5.5, -13.5], az: 0.25, el: 0.12, dist: 22 },
      { label: "3D Orbit — Back Shutter", fp: false, target: [6.5, -5.5, -13.5], az: Math.PI + 0.2, el: 0.10, dist: 22 },
      { label: "3D Orbit — Ranger Bracer", fp: false, target: [8.5, -9.0, -11.5], az: -Math.PI * 0.42, el: 0.28, dist: 28 },
    ],
  },
  netsend_arc: {
    title: "progs/netsend_arc.md3 — 8-Frame Additive 3D Antenna Lightning Cage",
    fps: 18,
    clips: [
      { label: "Live Arc Crackle Loop", sub: "frames 0–7 (18 fps)", start: 0, end: 7, fps: 18, loop: true },
      { label: "Slow-Mo Bolt Study", sub: "frames 0–7 (4 fps)", start: 0, end: 7, fps: 4, loop: true },
    ],
    cams: [
      { label: "3/4 Cage + Ghost PC", target: [0, 30, 0], az: Math.PI * 0.80, el: 0.20, dist: 82 },
      { label: "Top Antenna Bridge", target: [0, 52, 0], az: Math.PI * 0.90, el: 0.34, dist: 44 },
      { label: "Floor Grounding Legs", target: [0, 12, 0], az: Math.PI * 0.75, el: 0.22, dist: 46 },
    ],
  },
  netsend_disk: {
    title: "progs/netsend_disk.md3 — Thrown & Floor-Stuck 3.5\" Floppy Disk",
    fps: 12,
    clips: [
      { label: "All 8 Vertex Frames", sub: "frames 0–7", start: 0, end: 7, fps: 8, loop: true },
      { label: "Frame 0: Flat Flying Disk", sub: "frame 0 (spinning)", start: 0, end: 0, fps: 10, loop: true, spinDisk: true },
      { label: "Frame 1: Stuck 68° in Floor", sub: "frame 1", start: 1, end: 1, fps: 10, loop: true },
      { label: "Frames 2–7: Pre-Pop Tremor", sub: "frames 2–7 (16 fps)", start: 2, end: 7, fps: 16, loop: true },
    ],
    cams: [
      { label: "Close-Up Front Label", target: [0, 4, 0], az: Math.PI * 0.86, el: 0.28, dist: 20 },
      { label: "Close-Up Back Shutter", target: [0, 4, 0], az: 0.18, el: 0.28, dist: 20 },
      { label: "Top-Down Flat View", target: [0, 2, 0], az: Math.PI, el: 1.25, dist: 22 },
    ],
  },
};

const state = {
  mode: "story",
  clipIdx: 0,
  frame: 0,
  playing: true,
  speed: 1.0,
  wallSec: 0,
};

// ============================================================================
// 6. Dynamic Vertex Interpolation & Draw Calls
// ============================================================================
function uploadInterpolatedSurface(surf, frameFloat, allowLerp) {
  const nf = surf.frames.length;
  const fClamped = Math.max(0, Math.min(nf - 1, frameFloat));
  const f0 = Math.floor(fClamped);
  const f1 = Math.min(nf - 1, f0 + 1);
  const t = allowLerp ? (fClamped - f0) : 0.0;

  const A = surf.frames[f0], B = surf.frames[f1];
  if (t <= 1e-5 || f0 === f1) {
    gl.bindBuffer(gl.ARRAY_BUFFER, surf.posBuf);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, A.pos);
    gl.bindBuffer(gl.ARRAY_BUFFER, surf.nrmBuf);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, A.nrm);
    return;
  }
  const pOut = surf.scratchPos, nOut = surf.scratchNrm;
  const n3 = surf.nv * 3;
  for (let i = 0; i < n3; i++) {
    pOut[i] = A.pos[i] + (B.pos[i] - A.pos[i]) * t;
    nOut[i] = A.nrm[i] + (B.nrm[i] - A.nrm[i]) * t;
  }
  gl.bindBuffer(gl.ARRAY_BUFFER, surf.posBuf);
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, pOut);
  gl.bindBuffer(gl.ARRAY_BUFFER, surf.nrmBuf);
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, nOut);
}

function drawMD3Model(md3, frameFloat, modelMat, vpMat, opts = {}) {
  const mvp = mat4Mul(vpMat, modelMat);
  const allowLerp = $("chk-lerp").checked && !opts.noLerp;
  const exposure = parseFloat($("rng-exp").value);
  const skinIdx = opts.skinIdx !== undefined ? opts.skinIdx : 0;

  gl.useProgram(prog);
  gl.uniformMatrix4fv(U.uMVP, false, mvp);
  gl.uniformMatrix4fv(U.uModel, false, modelMat);
  gl.uniform1f(U.uExposure, exposure);
  gl.uniform1i(U.uTex, 0);

  const additiveQueue = [];

  for (const s of md3.surfaces) {
    if (!opts.ignoreVisibility && !s.visible) continue;
    uploadInterpolatedSurface(s, frameFloat, allowLerp);

    if (opts.ghostWireOnly) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform1i(U.uMode, 3);
      gl.uniform4f(U.uSolidColor, 0.32, 0.55, 0.72, 0.22);
      gl.bindVertexArray(s.wireVao);
      gl.drawElements(gl.LINES, s.wireIndices.length, gl.UNSIGNED_SHORT, 0);
      gl.disable(gl.BLEND);
      continue;
    }

    const mat = resolveSurfaceMaterial(s, skinIdx, state.wallSec);
    if (mat.mode === 2) {
      additiveQueue.push({ s, mat });
      continue;
    }

    gl.disable(gl.BLEND);
    gl.depthMask(true);
    gl.enable(gl.POLYGON_OFFSET_FILL);
    gl.polygonOffset(1.0, 1.0);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, mat.tex);
    gl.uniform1i(U.uMode, mat.mode);
    gl.bindVertexArray(s.vao);
    gl.drawElements(gl.TRIANGLES, s.indices.length, gl.UNSIGNED_SHORT, 0);
    gl.disable(gl.POLYGON_OFFSET_FILL);

    if ($("chk-wire").checked) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform1i(U.uMode, 3);
      gl.uniform4f(U.uSolidColor, 0.22, 0.95, 0.62, 0.42);
      gl.bindVertexArray(s.wireVao);
      gl.drawElements(gl.LINES, s.wireIndices.length, gl.UNSIGNED_SHORT, 0);
      gl.disable(gl.BLEND);
    }
  }

  // Render additive glow surfaces last (depth-tested, depth-write off)
  if (additiveQueue.length) {
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.depthMask(false);
    for (const { s, mat } of additiveQueue) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, mat.tex);
      gl.uniform1i(U.uMode, 2);
      gl.bindVertexArray(s.vao);
      gl.drawElements(gl.TRIANGLES, s.indices.length, gl.UNSIGNED_SHORT, 0);

      if ($("chk-wire").checked) {
        gl.uniform1i(U.uMode, 3);
        gl.uniform4f(U.uSolidColor, 0.4, 0.9, 1.0, 0.55);
        gl.bindVertexArray(s.wireVao);
        gl.drawElements(gl.LINES, s.wireIndices.length, gl.UNSIGNED_SHORT, 0);
      }
    }
    gl.depthMask(true);
    gl.disable(gl.BLEND);
  }
  gl.bindVertexArray(null);
}

function drawHelperLines(lineObj, modelMat, vpMat, rgba) {
  gl.useProgram(prog);
  gl.uniformMatrix4fv(U.uMVP, false, mat4Mul(vpMat, modelMat));
  gl.uniformMatrix4fv(U.uModel, false, modelMat);
  gl.uniform1i(U.uMode, 3);
  gl.uniform4f(U.uSolidColor, rgba[0], rgba[1], rgba[2], rgba[3]);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.bindVertexArray(lineObj.vao);
  gl.drawArrays(gl.LINES, 0, lineObj.count);
  gl.bindVertexArray(null);
  gl.disable(gl.BLEND);
}

// ============================================================================
// 7. UI Synchronization & Controls
// ============================================================================
function activeClip() {
  return MODES[state.mode].clips[state.clipIdx];
}

function rebuildSurfaceToggles() {
  const box = $("surf-toggles");
  box.innerHTML = "";
  const mKey = state.mode === "story" ? "netsend_pc" : state.mode;
  const md3 = models[mKey];
  for (const s of md3.surfaces) {
    const lbl = document.createElement("label");
    lbl.className = "chk";
    const inp = document.createElement("input");
    inp.type = "checkbox";
    inp.checked = s.visible;
    inp.addEventListener("change", () => { s.visible = inp.checked; });
    lbl.appendChild(inp);
    const txt = document.createElement("span");
    txt.innerHTML = `${s.name} <small>(${s.nt} tris)</small>`;
    lbl.appendChild(txt);
    box.appendChild(lbl);
  }
}

function rebuildStats() {
  const mKey = state.mode === "story" ? "netsend_pc" : state.mode;
  const md3 = models[mKey];
  const rows = [
    ["MD3 File", `progs/${mKey}.md3`],
    ["Triangles", md3.totalTris.toLocaleString()],
    ["Vertices", md3.totalVerts.toLocaleString()],
    ["Vertex Frames", md3.nFrames],
    ["Surfaces", md3.surfaces.length],
  ];
  if (mKey === "netsend_pc") {
    rows.push(["CRT Skins", "7 (.skin 0..6)"]);
    rows.push(["Quake Hull", "'-16 -16 0' .. '16 16 60'"]);
  } else if (mKey === "v_netsend") {
    rows.push(["Throw Release", "Frame 44"]);
    rows.push(["DarkPlaces FOV", "111 (4:3 base)"]);
  }
  $("stat-table").innerHTML = rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
}

function selectClip(idx) {
  state.clipIdx = idx;
  const clip = activeClip();
  state.frame = clip.start;
  $("scrubber").min = clip.start;
  $("scrubber").max = clip.end;
  $("scrubber").value = state.frame;
  $("chk-loop").checked = clip.loop;
  $("clip-fps-label").textContent = `${clip.fps} fps`;
  document.querySelectorAll(".clip-btn").forEach((b, i) => b.classList.toggle("active", i === idx));
}

function selectMode(mode) {
  state.mode = mode;
  document.querySelectorAll("#mode-tabs .tab").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));

  const spec = MODES[mode];
  const clipBox = $("clip-list");
  clipBox.innerHTML = "";
  spec.clips.forEach((c, idx) => {
    const btn = document.createElement("button");
    btn.className = "clip-btn" + (idx === 0 ? " active" : "");
    btn.innerHTML = `${c.label}<small>${c.sub}</small>`;
    btn.addEventListener("click", () => selectClip(idx));
    clipBox.appendChild(btn);
  });

  const camBox = $("cam-list");
  camBox.innerHTML = "";
  spec.cams.forEach((p, idx) => {
    const btn = document.createElement("button");
    btn.className = "cam-btn";
    btn.textContent = p.label;
    btn.addEventListener("click", () => {
      if (mode === "v_netsend") {
        $("chk-fpcam").checked = !!p.fp;
        syncFpOverlay();
        if (!p.fp) setCamPreset(p);
      } else {
        setCamPreset(p);
      }
    });
    camBox.appendChild(btn);
    if (idx === 0 && !p.fp) setCamPreset(p);
  });

  $("sec-pc-opts").style.display = (mode === "netsend_pc" || mode === "story") ? "" : "none";
  $("sec-vm-opts").style.display = (mode === "v_netsend") ? "" : "none";
  if (mode === "v_netsend") {
    $("chk-fpcam").checked = true;
  }
  syncFpOverlay();
  rebuildSurfaceToggles();
  rebuildStats();
  selectClip(0);
}

function syncFpOverlay() {
  const isFP = state.mode === "v_netsend" && $("chk-fpcam").checked;
  canvasBox.classList.toggle("fp-aspect", isFP);
  const showHud = isFP && $("chk-fphud").checked;
  $("crosshair").style.display = showHud ? "block" : "none";
  $("quake-hud").style.display = showHud ? "flex" : "none";
}

document.querySelectorAll("#mode-tabs .tab").forEach(btn => {
  btn.addEventListener("click", () => selectMode(btn.dataset.mode));
});

$("btn-play").addEventListener("click", () => {
  state.playing = !state.playing;
  $("btn-play").textContent = state.playing ? "⏸ Pause" : "▶ Play";
  $("btn-play").classList.toggle("primary", state.playing);
});

function stepFrame(delta) {
  state.playing = false;
  $("btn-play").textContent = "▶ Play";
  $("btn-play").classList.remove("primary");
  const clip = activeClip();
  const span = Math.max(1, clip.end - clip.start + 1);
  let f = Math.round(state.frame) + delta;
  if (f > clip.end) f = clip.start;
  if (f < clip.start) f = clip.end;
  state.frame = f;
  $("scrubber").value = f;
}
$("btn-prev").addEventListener("click", () => stepFrame(-1));
$("btn-next").addEventListener("click", () => stepFrame(1));

$("scrubber").addEventListener("input", e => {
  state.frame = parseFloat(e.target.value);
});

document.querySelectorAll(".spd-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    state.speed = parseFloat(btn.dataset.spd);
    document.querySelectorAll(".spd-btn").forEach(b => b.classList.toggle("active", b === btn));
  });
});

$("chk-fpcam").addEventListener("change", () => {
  syncFpOverlay();
  if (!$("chk-fpcam").checked) {
    setCamPreset(MODES.v_netsend.cams[1]);
  }
});
$("chk-fphud").addEventListener("change", syncFpOverlay);
$("rng-exp").addEventListener("input", e => {
  $("val-exp").textContent = parseFloat(e.target.value).toFixed(2) + "×";
});

window.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.code === "Space") { e.preventDefault(); $("btn-play").click(); }
  else if (e.code === "ArrowLeft") { e.preventDefault(); stepFrame(-1); }
  else if (e.code === "ArrowRight") { e.preventDefault(); stepFrame(1); }
});

// ============================================================================
// 8. Main Render Loop
// ============================================================================
let prevNow = performance.now();

function render(now) {
  const dt = Math.min(0.1, (now - prevNow) / 1000);
  prevNow = now;
  state.wallSec += dt * state.speed;

  // Resize backing store cleanly
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.max(2, Math.floor(canvasBox.clientWidth * dpr));
  const h = Math.max(2, Math.floor(canvasBox.clientHeight * dpr));
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w; canvas.height = h;
  }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.065, 0.075, 0.095, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);
  gl.disable(gl.CULL_FACE);

  // Advance timeline
  const clip = activeClip();
  if (state.playing) {
    const span = clip.end - clip.start + 1;
    if (span <= 1) {
      state.frame = clip.start;
    } else {
      let next = state.frame + dt * clip.fps * state.speed;
      if ($("chk-loop").checked) {
        if (next >= clip.end + 0.999) next = clip.start + ((next - clip.start) % span);
      } else {
        if (next >= clip.end) {
          next = clip.end;
          state.playing = false;
          $("btn-play").textContent = "▶ Play";
          $("btn-play").classList.remove("primary");
        }
      }
      state.frame = next;
      $("scrubber").value = state.frame;
    }
  }

  // Camera View-Projection Matrix
  const aspect = w / h;
  const isFP = state.mode === "v_netsend" && $("chk-fpcam").checked;
  let vpMat;
  if (isFP) {
    // Exact DarkPlaces fov 111 on 4:3 base -> vfov = 2 * atan(tan(111°/2) * 0.75) = 94.8°
    const vfov = 2 * Math.atan(Math.tan(111 * Math.PI / 360) * 0.75);
    const proj = mat4Perspective(vfov, aspect, 0.5, 2000);
    const view = mat4LookAt([0, 0, 0], [0, 0, -1], [0, 1, 0]);
    vpMat = mat4Mul(proj, view);
  } else {
    const proj = mat4Perspective(cam.vfovDeg * Math.PI / 180, aspect, 0.5, 2000);
    const ex = cam.target[0] + cam.dist * Math.cos(cam.el) * Math.sin(cam.az);
    const ey = cam.target[1] + cam.dist * Math.sin(cam.el);
    const ez = cam.target[2] + cam.dist * Math.cos(cam.el) * Math.cos(cam.az);
    const view = mat4LookAt([ex, ey, ez], cam.target, [0, 1, 0]);
    vpMat = mat4Mul(proj, view);
  }

  const idMat = mat4Identity();

  // Floor grid (hide in locked FP camera so viewmodel reads like eye-space, or draw at y=-22 in FP)
  if ($("chk-floor").checked) {
    const floorMat = isFP ? mat4TranslateRotateY(0, -22, 0, 0) : idMat;
    drawHelperLines(gridLines, floorMat, vpMat, [0.24, 0.29, 0.36, 0.45]);
    if (!isFP) drawHelperLines(axesLines, idMat, vpMat, [0.22, 0.89, 0.55, 0.75]);
  }

  const skinSel = $("sel-skin").value;
  let badgeHTML = "";
  let pillText = "";

  if (state.mode === "story") {
    const sf = state.frame;
    if (sf < 15) {
      // Phase 1: Thrown & floor-stuck disk
      let dFrame = 1, yaw = 0, yLift = 0;
      if (sf < 5) {
        const u = sf / 5;
        dFrame = 0;
        yLift = (1 - u) * 26;
        yaw = (1 - u) * Math.PI * 4;
        pillText = "PHASE 1: Thrown LOL.BAT Disk Flying";
      } else if (sf < 8) {
        dFrame = 1;
        pillText = "PHASE 1: Disk Sticks 68° in Stone Floor";
      } else {
        dFrame = 2 + ((sf - 8) / 7) * 5;
        pillText = "PHASE 1: Disk Tremors Before Materializing...";
      }
      const m = mat4TranslateRotateY(0, yLift, 0, yaw);
      drawMD3Model(models.netsend_disk, dFrame, m, vpMat, { noLerp: sf < 8 });
      badgeHTML = `<b>STORY [1/5]</b> · progs/netsend_disk.md3 · frame ${Math.floor(dFrame)}`;
    } else {
      let pcFrame = 0, autoSkin = 1, showArc = false, yaw = 0;
      if (sf < 25) {
        pcFrame = ((sf - 15) / 10) * 9.0;
        autoSkin = 1;
        pillText = "PHASE 2: 486DX School-Lab PC Pops Up Out of Floor Disk!";
      } else if (sf < 45) {
        pcFrame = 10 + ((sf - 25) / 20) * 9.9;
        autoSkin = autoSkinForPcFrame(pcFrame);
        const skinNames = {2: "CRT Static Warm-Up", 3: "INITIALIZING BATCH FILE...", 4: "C:\\> LOL.BAT", 5: "NET SEND * LOL"};
        pillText = `PHASE 3: Boot & Degauss — ${skinNames[autoSkin] || ""}`;
      } else if (sf < 130) {
        const u = (sf - 45);
        pcFrame = 20 + (u % 20);
        autoSkin = 0;
        showArc = $("chk-arc").checked;
        yaw = (u / 85) * Math.PI * 2;
        pillText = "PHASE 4: Active Ghost-Typing + 360° Turret Scan + NET SEND Lightning!";
      } else {
        pcFrame = 40 + ((sf - 130) / 20) * 9.9;
        autoSkin = pcFrame < 48.5 ? 6 : 1;
        yaw = Math.PI * 2;
        pillText = "PHASE 5: CRT Phosphor Collapse Dot & Antenna Droop";
      }
      const skinUse = skinSel === "auto" ? autoSkin : parseInt(skinSel, 10);
      if ($("chk-spin").checked) yaw = state.wallSec * 0.9;
      const m = mat4TranslateRotateY(0, 0, 0, yaw);
      drawMD3Model(models.netsend_pc, pcFrame, m, vpMat, { skinIdx: skinUse });
      if (showArc) {
        const arcFrame = (state.wallSec * 18) % 8;
        drawMD3Model(models.netsend_arc, arcFrame, m, vpMat, { ignoreVisibility: true });
      }
      if ($("chk-hull").checked) drawHelperLines(hullLines, m, vpMat, [0.36, 0.88, 1.0, 0.55]);
      badgeHTML = `<b>STORY</b> · PC frame <b>${Math.floor(pcFrame)}</b>/49 · CRT <b>skin ${skinUse}</b>`;
    }
    $("frame-readout").textContent = `Timeline ${state.frame.toFixed(1)} / 149`;
  } else if (state.mode === "netsend_pc") {
    const skinUse = skinSel === "auto" ? autoSkinForPcFrame(state.frame) : parseInt(skinSel, 10);
    const yaw = $("chk-spin").checked ? state.wallSec * 0.85 : 0;
    const m = mat4TranslateRotateY(0, 0, 0, yaw);
    drawMD3Model(models.netsend_pc, state.frame, m, vpMat, { skinIdx: skinUse });
    if ($("chk-arc").checked) {
      const arcFrame = (state.wallSec * 18) % 8;
      drawMD3Model(models.netsend_arc, arcFrame, m, vpMat, { ignoreVisibility: true });
    }
    if ($("chk-hull").checked) drawHelperLines(hullLines, m, vpMat, [0.36, 0.88, 1.0, 0.55]);
    badgeHTML = `<b>progs/netsend_pc.md3</b> · Frame <b>${Math.floor(state.frame)}</b> / 49 · CRT <b>skin ${skinUse}</b>`;
    $("frame-readout").textContent = `Frame ${state.frame.toFixed(2)} / 49`;
  } else if (state.mode === "v_netsend") {
    drawMD3Model(models.v_netsend, state.frame, idMat, vpMat, {});
    const fi = Math.floor(state.frame);
    if (fi === 44) pillText = "★ FRAME 44: THROW RELEASE (Spawn progs/netsend_disk.md3)";
    else if (fi >= 14 && fi <= 16) pillText = "180° FLIP: Brushed Steel Sliding Shutter & Spindle Hub";
    badgeHTML = `<b>progs/v_netsend.md3</b> · Frame <b>${fi}</b> / 59 <span class="sub">(${isFP ? "Game FP FOV 111" : "Free 3D Orbit"})</span>`;
    $("frame-readout").textContent = `Frame ${state.frame.toFixed(2)} / 59`;
  } else if (state.mode === "netsend_arc") {
    drawMD3Model(models.netsend_pc, 25, idMat, vpMat, { ghostWireOnly: true, ignoreVisibility: true });
    drawMD3Model(models.netsend_arc, state.frame, idMat, vpMat, {});
    badgeHTML = `<b>progs/netsend_arc.md3</b> · Frame <b>${Math.floor(state.frame)}</b> / 7 <span class="sub">(Additive 3D Cage + Ghost PC)</span>`;
    $("frame-readout").textContent = `Frame ${state.frame.toFixed(2)} / 7`;
  } else if (state.mode === "netsend_disk") {
    const yaw = clip.spinDisk ? state.wallSec * 6.0 : 0;
    const yLift = clip.spinDisk ? 6.0 : 0.0;
    const m = mat4TranslateRotateY(0, yLift, 0, yaw);
    drawMD3Model(models.netsend_disk, state.frame, m, vpMat, {});
    badgeHTML = `<b>progs/netsend_disk.md3</b> · Frame <b>${Math.floor(state.frame)}</b> / 7`;
    $("frame-readout").textContent = `Frame ${state.frame.toFixed(2)} / 7`;
  }

  $("model-badge").innerHTML = badgeHTML;
  const pill = $("event-pill");
  if (pillText) {
    pill.style.display = "inline-block";
    pill.textContent = pillText;
  } else {
    pill.style.display = "none";
  }

  requestAnimationFrame(render);
}

selectMode("story");
requestAnimationFrame(render);
})();
</script>
</body>
</html>
"""


def main():
    md3_payload = {}
    for key, fname in MD3_FILES.items():
        path = os.path.join(PROGS, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing MD3 file: {path}")
        md3_payload[key] = b64_file(path)

    tex_payload = {}
    for png_path in sorted(glob.glob(os.path.join(PROGS, "netsend_*.png"))):
        stem = os.path.splitext(os.path.basename(png_path))[0]
        if stem in ("netsend_scr_black", "netsend_scr_glow"):
            continue
        shader_key = f"progs/{stem}"
        tex_payload[shader_key] = "data:image/png;base64," + b64_file(png_path)

    payload = {
        "built_at": int(time.time()),
        "md3": md3_payload,
        "textures": tex_payload,
    }
    js_str = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__PAYLOAD__", js_str)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    kb = os.path.getsize(OUT_HTML) / 1024.0
    print(f"Wrote {OUT_HTML} ({kb:.1f} KB, {len(md3_payload)} MD3 models, {len(tex_payload)} textures)")


if __name__ == "__main__":
    main()
