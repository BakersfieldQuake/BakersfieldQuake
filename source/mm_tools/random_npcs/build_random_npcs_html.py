"""Builds `G:\\Quake\\Combat\\BakersfieldQuake\\random_people_npcs.html`:
A 100% self-contained, zero-CDN WebGL2 3D Interactive Showcase for the 4 BakersfieldQuake Random People NPCs:
  1. npc_randguy.md3   — Random Guy (with live switcher for all 6 Random Comedy Shirts!)
  2. npc_afroguy.md3   — Black Guy with Volumetric 70s Afro, Gold Pick & Chrome Boombox
  3. npc_randlady.md3  — Random Lady (with live switcher for all 3 Tops!)
  4. npc_fatguy.md3    — Really Big Fat Guy with Stretched Shirt, Bare Jiggling Belly & XXL Burrito

Features:
  - All-4 Side-by-Side Lineup Mode + Solo Character Close-Up Mode
  - Live Animation Clip Switcher: Walk, Run, Idle, Funny Emote (+ embedded WAV audio!), Pain, Collapse Death
  - Live Random-Shirt / Outfit Skin Selector (including "Randomize Shirt!" button)
  - Toggleable Quake Player Hull ('-16 -16 -24' to '16 16 32', 54u standing reference) & Floor Grid
"""
from __future__ import annotations

import base64
import gzip
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "random_npcs")
SRGB_DIR = os.path.join(OUT_ROOT, "tex_srgb")
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SND_DIR = os.path.join(MOD_ROOT, "sound", "random_npcs")
HTML_OUT = os.path.join(MOD_ROOT, "random_people_npcs.html")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
import md3lib


def build_edges(tris):
    s = set()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u != v:
                s.add((min(int(u), int(v)), max(int(u), int(v))))
    return np.array(sorted(s), dtype=np.uint16)


def encode_tex(path: str, size: int = 512) -> dict:
    im = Image.open(path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    im.save(bio, "PNG", optimize=True)
    return dict(
        name=os.path.basename(path),
        uri="data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii"),
    )


def encode_wav(path: str) -> str:
    with open(path, "rb") as fp:
        raw = fp.read()
    return "data:audio/wav;base64," + base64.b64encode(raw).decode("ascii")


def pack_md3(md3_path: str, arena: bytearray, head_tex_idx: int, body_tex_indices: list[int], meta: dict) -> dict:
    m = md3lib.read(md3_path)
    nf = m["nframes"]

    def add_bytes(b: bytes):
        while len(arena) & 3:
            arena.append(0)
        off = len(arena)
        arena.extend(b)
        return [off, len(b)]

    surfs_out = []
    tot_v, tot_t = 0, 0
    for s in m["surfaces"]:
        sname = s["name"]
        nv, nt = len(s["st"]), len(s["tris"])
        tot_v += nv
        tot_t += nt
        tris_arr = np.array(s["tris"], dtype=np.uint16)
        edges = build_edges(s["tris"])
        uv = np.array(s["st"], dtype=np.float32)

        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            pos_q[fi] = np.clip(np.round(np.array(vv, dtype=np.float32) * 64.0), -32768, 32767).astype(np.int16)
            nrm_q[fi] = np.clip(np.round(np.array(nn, dtype=np.float32) * 127.0), -127, 127).astype(np.int8)

        surfs_out.append(
            dict(
                name=sname,
                nv=nv,
                nt=nt,
                ne=len(edges),
                skinTex=[head_tex_idx] if sname == "head" else body_tex_indices,
                tris=add_bytes(tris_arr.tobytes()),
                edges=add_bytes(edges.tobytes()),
                uv=add_bytes(uv.tobytes()),
                pos=add_bytes(pos_q.tobytes()),
                nrm=add_bytes(nrm_q.tobytes()),
            )
        )
    frame_names = (
        [f"idle{i+1}" for i in range(8)]
        + [f"walk{i+1}" for i in range(12)]
        + [f"run{i+1}" for i in range(10)]
        + [f"funny{i+1}" for i in range(10)]
        + [f"pain{i+1}" for i in range(4)]
        + [f"death{i+1}" for i in range(6)]
    )
    return dict(
        **meta,
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        frameNames=frame_names,
        surfaces=surfs_out,
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BakersfieldQuake · 4 Random People 3D NPCs Showcase</title>
<style>
  :root { --bg:#090d16; --panel:#111827; --border:#24324d; --acc:#38bdf8; --silver:#e2e8f0; --hot:#fb923c; --ok:#34d399; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--silver); font-family:'Segoe UI',system-ui,sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
  header { padding:10px 18px; background:#0d1322; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .brand { display:flex; align-items:center; gap:12px; }
  .badge { background:linear-gradient(135deg,#34d399,#38bdf8); color:#06101e; font-weight:900; font-size:11px; padding:3px 9px; border-radius:4px; letter-spacing:0.08em; }
  h1 { font-size:17px; font-weight:900; letter-spacing:0.04em; color:#f8fafc; }
  .tabs { display:flex; gap:6px; flex-wrap:wrap; }
  button { background:#182235; color:#dbeafe; border:1px solid var(--border); border-radius:6px; padding:7px 12px; font-size:12px; font-weight:700; cursor:pointer; transition:0.15s; }
  button:hover { border-color:var(--acc); background:#1e2d47; }
  button.active { background:var(--acc); color:#06101e; border-color:var(--acc); }
  button.funny-btn { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-size:12.5px; padding:7px 15px; box-shadow:0 0 14px rgba(249,115,22,0.35); }
  button.rand-btn { background:linear-gradient(135deg,#a855f7,#ec4899); color:#fff; border-color:#f9a8d4; }
  main { flex:1; display:grid; grid-template-columns:1fr 350px; min-height:0; }
  #vp-wrap { position:relative; background:radial-gradient(circle at 50% 42%,#1a2744 0%,#080c15 80%); overflow:hidden; }
  canvas { width:100%; height:100%; display:block; }
  #scrubber-bar { position:absolute; left:14px; right:14px; bottom:12px; background:rgba(13,19,34,0.90); border:1px solid var(--border); border-radius:8px; padding:8px 14px; display:flex; align-items:center; gap:10px; }
  input[type=range] { flex:1; accent-color:var(--acc); }
  aside { background:var(--panel); border-left:1px solid var(--border); padding:14px; overflow-y:auto; display:flex; flex-direction:column; gap:11px; font-size:12.5px; line-height:1.45; }
  .card { background:#0c1220; border:1px solid var(--border); border-radius:8px; padding:11px; }
  .card h3 { font-size:11.5px; text-transform:uppercase; letter-spacing:0.08em; color:var(--acc); margin-bottom:7px; }
  .kv { display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #162036; gap:8px; }
  .kv:last-child { border-bottom:none; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  code { color:#93c5fd; font-family:Consolas,monospace; font-size:11.5px; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">PLAYER-SIZED 54u MD3 NPCs</span>
    <h1>BAKERSFIELD "RANDOM PEOPLE" 3D NPC LINEUP</h1>
  </div>
  <div class="tabs">
    <button id="tab-all" class="active" onclick="setView(-1)">All 4 Side-by-Side</button>
    <button id="tab-0" onclick="setView(0)">1 · Random Shirt Guy</button>
    <button id="tab-1" onclick="setView(1)">2 · Afro Guy</button>
    <button id="tab-2" onclick="setView(2)">3 · Random Lady</button>
    <button id="tab-3" onclick="setView(3)">4 · Really Big Fat Guy</button>
  </div>
  <div class="row">
    <button class="rand-btn" onclick="randomizeOutfits()">🎲 Randomize Shirt!</button>
    <button class="funny-btn" onclick="playFunnyWithVoice()">😂 Funny Emote + Voice!</button>
  </div>
</header>
<main>
  <div id="vp-wrap">
    <canvas id="gl"></canvas>
    <div id="scrubber-bar">
      <button id="btn-play" onclick="togglePlay()">Pause</button>
      <input id="scrub" type="range" min="0" max="49" step="0.05" value="8">
      <span id="frame-lbl" style="min-width:135px;font-family:Consolas,monospace;font-size:12px;">f08 · walk1</span>
    </div>
  </div>
  <aside>
    <div class="card">
      <h3>50-Frame Animation Clips</h3>
      <div class="row">
        <button id="clip-walk" class="active" onclick="setClip('walk')">Walk (8–19)</button>
        <button id="clip-run" onclick="setClip('run')">Run / Panic (20–29)</button>
        <button id="clip-idle" onclick="setClip('idle')">Idle (0–7)</button>
        <button id="clip-funny" onclick="setClip('funny')">Funny Emote (30–39)</button>
        <button id="clip-pain" onclick="setClip('pain')">Pain (40–43)</button>
        <button id="clip-death" onclick="setClip('death')">Death (44–49)</button>
      </div>
    </div>

    <div class="card">
      <h3>Random Guy · 6 Comedy Shirts (<code>.skin</code>)</h3>
      <div class="row" id="rg-skins"></div>
    </div>

    <div class="card">
      <h3>Random Lady · 3 Tops (<code>.skin</code>)</h3>
      <div class="row" id="ld-skins"></div>
    </div>

    <div class="card">
      <h3>Scale &amp; Viewport Helpers</h3>
      <div class="row">
        <button id="btn-hull" class="active" onclick="toggleHull()">54u Player Hull Gauge: ON</button>
        <button id="btn-wire" onclick="toggleWire()">Wireframe: OFF</button>
        <button onclick="resetCamera()">Reset Camera</button>
      </div>
      <div style="margin-top:6px;color:#94a3b8;font-size:11.5px;">Left-drag to orbit 360° · Scroll wheel to zoom · Right-drag to pan. Green box = exact Quake <code>player.mdl</code> hull (<code>-16 -16 -24</code> to <code>16 16 32</code>).</div>
    </div>

    <div class="card">
      <h3>QuakeC Entities &amp; Cheat Impulses</h3>
      <div class="kv"><span>Random Shirt Guy</span><code>npc_random_guy (imp 51)</code></div>
      <div class="kv"><span>Black Guy w/ Afro</span><code>npc_afro_guy (imp 52)</code></div>
      <div class="kv"><span>Random Lady</span><code>npc_random_lady (imp 53)</code></div>
      <div class="kv"><span>Really Big Fat Guy</span><code>npc_fat_guy (imp 54)</code></div>
      <div class="kv"><span>Spawn Random 1 of 4</span><code>npc_random_person</code></div>
      <div class="kv"><span>Summon All 4 Lineup</span><code>impulse 55</code></div>
    </div>
  </aside>
</main>
<script>
const PAYLOAD = /*__RNPC_DATA__*/null;

const CLIPS = {
  idle:  { a: 0,  b: 7,  fps: 8.5,  loop: true },
  walk:  { a: 8,  b: 19, fps: 11.5, loop: true },
  run:   { a: 20, b: 29, fps: 15.0, loop: true },
  funny: { a: 30, b: 39, fps: 10.0, loop: true },
  pain:  { a: 40, b: 43, fps: 9.0,  loop: true },
  death: { a: 44, b: 49, fps: 7.5,  loop: false },
};

async function DecompressB64Gz(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const w = ds.writable.getWriter();
  w.write(bin); w.close();
  return await new Response(ds.readable).arrayBuffer();
}

let gl, prog, lineProg, arenaBuf, lineVbo;
let gpuModels = [], gpuTextures = [], voiceAudio = [];
let viewIdx = -1; // -1 = all 4 lineup, 0..3 = solo
let curClip = 'walk', playing = true, animT = 0.0, lastTs = 0.0;
let showHull = true, showWire = false;
let skinChoice = [0, 0, 0, 0];
let camAz = 0.0, camEl = 0.14, camDist = 175.0, camPanY = 0.0, camPanZ = 3.0;
let dragBtn = -1, lx = 0, ly = 0;

const VS = `#version 300 es
layout(location=0) in vec3 aPos0;
layout(location=1) in vec3 aNrm0;
layout(location=2) in vec3 aPos1;
layout(location=3) in vec3 aNrm1;
layout(location=4) in vec2 aUV;
uniform mat4 uMVP, uModel;
uniform float uLerp;
out vec3 vNrm, vPos;
out vec2 vUV;
void main() {
  vec3 p = mix(aPos0, aPos1, uLerp) / 64.0;
  vec3 n = normalize(mix(aNrm0, aNrm1, uLerp) / 127.0);
  vec4 wp = uModel * vec4(p, 1.0);
  vPos = wp.xyz;
  vNrm = normalize(mat3(uModel) * n);
  vUV = aUV;
  gl_Position = uMVP * wp;
}`;

const FS = `#version 300 es
precision highp float;
in vec3 vNrm, vPos;
in vec2 vUV;
uniform sampler2D uTex;
uniform vec3 uCamPos;
uniform float uWirePass;
out vec4 fragColor;
void main() {
  if (uWirePass > 0.5) { fragColor = vec4(0.22, 0.82, 1.0, 0.65); return; }
  vec4 tx = texture(uTex, vUV);
  vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
  vec3 V = normalize(uCamPos - vPos);
  vec3 L1 = normalize(vec3(0.78, -0.36, 0.52));
  vec3 L2 = normalize(vec3(0.45, 0.72, 0.35));
  vec3 L3 = normalize(vec3(-0.75, 0.0, 0.55));
  float d1 = max(dot(N, L1), 0.0);
  float d2 = max(dot(N, L2), 0.0);
  float rim = pow(max(dot(N, L3), 0.0), 2.0) * 0.22;
  vec3 H1 = normalize(L1 + V);
  float spec = pow(max(dot(N, H1), 0.0), 28.0) * 0.14;
  vec3 lit = tx.rgb * (0.42 + 0.52 * d1 + 0.24 * d2 + rim) + vec3(1.0) * spec;
  fragColor = vec4(lit, 1.0);
}`;

const LVS = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aCol;
uniform mat4 uMVP;
out vec3 vCol;
void main() { vCol = aCol; gl_Position = uMVP * vec4(aPos, 1.0); }`;

const LFS = `#version 300 es
precision highp float;
in vec3 vCol;
out vec4 fragColor;
void main() { fragColor = vec4(vCol, 1.0); }`;

function compile(vs, fs) {
  const s = (t, src) => { const sh = gl.createShader(t); gl.shaderSource(sh, src); gl.compileShader(sh); return sh; };
  const p = gl.createProgram();
  gl.attachShader(p, s(gl.VERTEX_SHADER, vs));
  gl.attachShader(p, s(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p);
  return p;
}

function mat4Mul(a, b) {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++)
    o[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1] + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
  return o;
}
function mat4Persp(fovYRad, asp, zn, zf) {
  const f = 1.0 / Math.tan(fovYRad * 0.5), nf = 1.0 / (zn - zf);
  return new Float32Array([f/asp,0,0,0, 0,f,0,0, 0,0,(zf+zn)*nf,-1, 0,0,2*zf*zn*nf,0]);
}
function mat4LookAt(eye, tgt, up) {
  const z0=eye[0]-tgt[0], z1=eye[1]-tgt[1], z2=eye[2]-tgt[2];
  let zl = Math.hypot(z0,z1,z2)||1; const zx=z0/zl, zy=z1/zl, zz=z2/zl;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  let xl = Math.hypot(xx,xy,xz)||1; xx/=xl; xy/=xl; xz/=xl;
  const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  return new Float32Array([
    xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]),
    -(yx*eye[0]+yy*eye[1]+yz*eye[2]),
    -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}
function mat4Trans(tx, ty, tz) {
  return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, tx,ty,tz,1]);
}

function buildStageLines() {
  const pts = [];
  const pushSeg = (x0,y0,z0, x1,y1,z1, r,g,b) => { pts.push(x0,y0,z0,r,g,b, x1,y1,z1,r,g,b); };
  // Floor grid at Z = -24.0
  for (let g = -100; g <= 100; g += 16) {
    pushSeg(-60, g, -24, 60, g, -24, 0.16, 0.22, 0.34);
  }
  for (let x = -60; x <= 60; x += 15) {
    pushSeg(x, -100, -24, x, 100, -24, 0.16, 0.22, 0.34);
  }
  return new Float32Array(pts);
}

function buildHullBoxVerts(yc) {
  const pts = [];
  const pushSeg = (x0,y0,z0, x1,y1,z1, r,g,b) => { pts.push(x0,y0,z0,r,g,b, x1,y1,z1,r,g,b); };
  const x0=-16, x1=16, y0=yc-16, y1=yc+16, z0=-24, z1=30; // 54u standing player height!
  const c = [0.20, 0.90, 0.52];
  pushSeg(x0,y0,z0, x1,y0,z0, ...c); pushSeg(x1,y0,z0, x1,y1,z0, ...c);
  pushSeg(x1,y1,z0, x0,y1,z0, ...c); pushSeg(x0,y1,z0, x0,y0,z0, ...c);
  pushSeg(x0,y0,z1, x1,y0,z1, ...c); pushSeg(x1,y0,z1, x1,y1,z1, ...c);
  pushSeg(x1,y1,z1, x0,y1,z1, ...c); pushSeg(x0,y1,z1, x0,y0,z1, ...c);
  pushSeg(x0,y0,z0, x0,y0,z1, ...c); pushSeg(x1,y0,z0, x1,y0,z1, ...c);
  pushSeg(x1,y1,z0, x1,y1,z1, ...c); pushSeg(x0,y1,z0, x0,y1,z1, ...c);
  return pts;
}

const RG_LABELS = ['0: Oildale', '1: Hawaiian', '2: Forklift', '3: Okayest', '4: Tie-Dye', '5: Flames'];
const LD_LABELS = ['0: Live Laugh Frag', '1: Leopard', '2: HOA Enforcer'];

function buildSkinButtons() {
  const rg = document.getElementById('rg-skins');
  RG_LABELS.forEach((lbl, i) => {
    const b = document.createElement('button');
    b.id = 'rg-sk-' + i;
    b.textContent = lbl;
    if (i === 0) b.className = 'active';
    b.onclick = () => { skinChoice[0] = i; syncSkinButtons(); };
    rg.appendChild(b);
  });
  const ld = document.getElementById('ld-skins');
  LD_LABELS.forEach((lbl, i) => {
    const b = document.createElement('button');
    b.id = 'ld-sk-' + i;
    b.textContent = lbl;
    if (i === 0) b.className = 'active';
    b.onclick = () => { skinChoice[2] = i; syncSkinButtons(); };
    ld.appendChild(b);
  });
}

function syncSkinButtons() {
  for (let i = 0; i < 6; i++) document.getElementById('rg-sk-' + i).classList.toggle('active', skinChoice[0] === i);
  for (let i = 0; i < 3; i++) document.getElementById('ld-sk-' + i).classList.toggle('active', skinChoice[2] === i);
}

function randomizeOutfits() {
  skinChoice[0] = (skinChoice[0] + 1 + Math.floor(Math.random() * 5)) % 6;
  skinChoice[2] = (skinChoice[2] + 1 + Math.floor(Math.random() * 2)) % 3;
  syncSkinButtons();
}

function setView(idx) {
  viewIdx = idx;
  document.getElementById('tab-all').classList.toggle('active', idx === -1);
  for (let i = 0; i < 4; i++) document.getElementById('tab-' + i).classList.toggle('active', idx === i);
  resetCamera();
}

function resetCamera() {
  camAz = 0.22; camEl = 0.14; camPanY = 0.0; camPanZ = 3.0;
  camDist = (viewIdx === -1) ? 172.0 : 88.0;
}

function setClip(name) {
  curClip = name;
  animT = 0.0;
  playing = true;
  document.getElementById('btn-play').textContent = 'Pause';
  for (const k of Object.keys(CLIPS)) document.getElementById('clip-' + k).classList.toggle('active', k === name);
}

function playFunnyWithVoice() {
  setClip('funny');
  const who = (viewIdx >= 0) ? viewIdx : Math.floor(Math.random() * 4);
  if (voiceAudio[who]) {
    voiceAudio[who].currentTime = 0;
    voiceAudio[who].play().catch(() => {});
  }
}

function togglePlay() {
  playing = !playing;
  document.getElementById('btn-play').textContent = playing ? 'Pause' : 'Play';
}
function toggleHull() {
  showHull = !showHull;
  const b = document.getElementById('btn-hull');
  b.textContent = '54u Player Hull Gauge: ' + (showHull ? 'ON' : 'OFF');
  b.classList.toggle('active', showHull);
}
function toggleWire() {
  showWire = !showWire;
  const b = document.getElementById('btn-wire');
  b.textContent = 'Wireframe: ' + (showWire ? 'ON' : 'OFF');
  b.classList.toggle('active', showWire);
}

async function init() {
  buildSkinButtons();
  const canvas = document.getElementById('gl');
  gl = canvas.getContext('webgl2', { antialias: true });
  prog = compile(VS, FS);
  lineProg = compile(LVS, LFS);
  lineVbo = gl.createBuffer();
  arenaBuf = await DecompressB64Gz(PAYLOAD.binGz);

  for (const t of PAYLOAD.textures) {
    const img = new Image();
    img.src = t.uri;
    await img.decode();
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gpuTextures.push(tex);
  }

  voiceAudio = PAYLOAD.voices.map(u => { const a = new Audio(u); a.volume = 0.85; return a; });

  for (const m of PAYLOAD.models) {
    const surfs = m.surfaces.map(s => {
      const mk = (sl, tgt) => {
        const b = gl.createBuffer();
        gl.bindBuffer(tgt, b);
        gl.bufferData(tgt, new Uint8Array(arenaBuf, sl[0], sl[1]), gl.STATIC_DRAW);
        return b;
      };
      return { ...s, bPos: mk(s.pos, gl.ARRAY_BUFFER), bNrm: mk(s.nrm, gl.ARRAY_BUFFER), bUV: mk(s.uv, gl.ARRAY_BUFFER), bTri: mk(s.tris, gl.ELEMENT_ARRAY_BUFFER), bEdg: mk(s.edges, gl.ELEMENT_ARRAY_BUFFER) };
    });
    gpuModels.push({ ...m, surfs });
  }

  canvas.addEventListener('contextmenu', e => e.preventDefault());
  canvas.addEventListener('pointerdown', e => { dragBtn = e.button; lx = e.clientX; ly = e.clientY; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointerup', () => { dragBtn = -1; });
  canvas.addEventListener('pointermove', e => {
    if (dragBtn < 0) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    if (dragBtn === 0) {
      camAz -= dx * 0.008;
      camEl = Math.max(-0.45, Math.min(1.25, camEl + dy * 0.007));
    } else {
      camPanY -= dx * 0.14;
      camPanZ += dy * 0.14;
    }
  });
  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    camDist = Math.max(38.0, Math.min(340.0, camDist * (1.0 + e.deltaY * 0.001)));
  }, { passive: false });

  document.getElementById('scrub').addEventListener('input', e => {
    playing = false;
    document.getElementById('btn-play').textContent = 'Play';
    animT = parseFloat(e.target.value);
    curClip = 'manual';
    for (const k of Object.keys(CLIPS)) document.getElementById('clip-' + k).classList.remove('active');
  });

  resetCamera();
  requestAnimationFrame(loop);
}

function drawModelAt(mIdx, yOffset, fFloat, mvp, eye) {
  const m = gpuModels[mIdx];
  const f0 = Math.max(0, Math.min(m.nf - 1, Math.floor(fFloat)));
  let f1 = f0 + 1;
  if (curClip !== 'manual') {
    const cl = CLIPS[curClip];
    if (f1 > cl.b) f1 = cl.loop ? cl.a : cl.b;
  } else {
    f1 = Math.min(m.nf - 1, f1);
  }
  const lerp = fFloat - Math.floor(fFloat);
  const M = mat4Trans(0.0, yOffset, 0.0);
  const MVP = mat4Mul(mvp, M);

  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, MVP);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uModel'), false, M);
  gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);
  gl.uniform3fv(gl.getUniformLocation(prog, 'uCamPos'), eye);

  for (const s of m.surfs) {
    const strideP = s.nv * 3 * 2;
    const strideN = s.nv * 3 * 1;
    gl.bindBuffer(gl.ARRAY_BUFFER, s.bPos);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.SHORT, false, 0, f0 * strideP);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 3, gl.SHORT, false, 0, f1 * strideP);
    gl.bindBuffer(gl.ARRAY_BUFFER, s.bNrm);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.BYTE, false, 0, f0 * strideN);
    gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.BYTE, false, 0, f1 * strideN);
    gl.bindBuffer(gl.ARRAY_BUFFER, s.bUV);
    gl.enableVertexAttribArray(4); gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);

    const sk = skinChoice[mIdx] % s.skinTex.length;
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, gpuTextures[s.skinTex[sk]]);
    gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);

    gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 0.0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bTri);
    gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);

    if (showWire) {
      gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 1.0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bEdg);
      gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
    }
  }
}

function loop(ts) {
  const dt = Math.min(0.05, (ts - lastTs) * 0.001 || 0.016);
  lastTs = ts;

  let curF = animT;
  if (curClip !== 'manual') {
    const cl = CLIPS[curClip];
    const span = cl.b - cl.a + 1;
    if (playing) animT += dt * cl.fps;
    if (cl.loop) curF = cl.a + (animT % span);
    else curF = Math.min(cl.b, cl.a + animT);
    document.getElementById('scrub').value = curF.toFixed(2);
  }
  const fiDisp = Math.max(0, Math.min(49, Math.floor(curF)));
  document.getElementById('frame-lbl').textContent = 'f' + String(fiDisp).padStart(2, '0') + ' · ' + gpuModels[0].frameNames[fiDisp];

  const canvas = document.getElementById('gl');
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }

  gl.viewport(0, 0, w, h);
  gl.clearColor(0.045, 0.065, 0.11, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const eye = [
    Math.cos(camEl) * Math.cos(camAz) * camDist,
    camPanY + Math.cos(camEl) * Math.sin(camAz) * camDist,
    camPanZ + Math.sin(camEl) * camDist,
  ];
  const tgt = [0.0, camPanY, camPanZ];
  const P = mat4Persp(44.0 * Math.PI / 180.0, w / Math.max(1, h), 2.0, 900.0);
  const V = mat4LookAt(eye, tgt, [0, 0, 1]);
  const VP = mat4Mul(P, V);

  // Draw floor grid + optional 54u player hull box!
  let lVerts = Array.from(buildStageLines());
  if (showHull) {
    if (viewIdx === -1) lVerts = lVerts.concat(buildHullBoxVerts(-84.0));
    else lVerts = lVerts.concat(buildHullBoxVerts(0.0));
  }
  const lArr = new Float32Array(lVerts);
  gl.useProgram(lineProg);
  gl.uniformMatrix4fv(gl.getUniformLocation(lineProg, 'uMVP'), false, VP);
  gl.bindBuffer(gl.ARRAY_BUFFER, lineVbo);
  gl.bufferData(gl.ARRAY_BUFFER, lArr, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
  for (let a = 2; a <= 4; a++) gl.disableVertexAttribArray(a);
  gl.drawArrays(gl.LINES, 0, lArr.length / 6);

  if (viewIdx === -1) {
    const slots = [-50.0, -17.0, 17.0, 54.0];
    for (let i = 0; i < 4; i++) {
      // Stagger walk/run phase slightly across the 4 NPCs so lineup looks alive!
      let fChar = curF;
      if (playing && (curClip === 'walk' || curClip === 'run' || curClip === 'idle')) {
        const cl = CLIPS[curClip];
        const span = cl.b - cl.a + 1;
        fChar = cl.a + ((animT + i * 2.1) % span);
      }
      drawModelAt(i, slots[i], fChar, VP, eye);
    }
  } else {
    drawModelAt(viewIdx, 0.0, curF, VP, eye);
  }

  requestAnimationFrame(loop);
}

init();
</script>
</body>
</html>
"""


def main() -> None:
    tex_list: list[dict] = []

    def add_tex(fname: str) -> int:
        idx = len(tex_list)
        tex_list.append(encode_tex(os.path.join(SRGB_DIR, fname), size=512))
        return idx

    rg_h = add_tex("npc_randguy_head.png")
    rg_b = [add_tex(f"npc_randguy_body_{i}.png") for i in range(6)]

    af_h = add_tex("npc_afroguy_head.png")
    af_b = [add_tex("npc_afroguy_body.png")]

    ld_h = add_tex("npc_randlady_head.png")
    ld_b = [add_tex(f"npc_randlady_body_{i}.png") for i in range(3)]

    fg_h = add_tex("npc_fatguy_head.png")
    fg_b = [add_tex("npc_fatguy_body.png")]

    arena = bytearray()
    models = [
        pack_md3(os.path.join(PROGS_DIR, "npc_randguy.md3"), arena, rg_h, rg_b, dict(title="Random Shirt Guy")),
        pack_md3(os.path.join(PROGS_DIR, "npc_afroguy.md3"), arena, af_h, af_b, dict(title="Afro Guy")),
        pack_md3(os.path.join(PROGS_DIR, "npc_randlady.md3"), arena, ld_h, ld_b, dict(title="Random Lady")),
        pack_md3(os.path.join(PROGS_DIR, "npc_fatguy.md3"), arena, fg_h, fg_b, dict(title="Really Big Fat Guy")),
    ]

    voices = [
        encode_wav(os.path.join(SND_DIR, "randguy_funny.wav")),
        encode_wav(os.path.join(SND_DIR, "afroguy_funny.wav")),
        encode_wav(os.path.join(SND_DIR, "lady_funny.wav")),
        encode_wav(os.path.join(SND_DIR, "fatguy_funny.wav")),
    ]

    gz_bytes = gzip.compress(bytes(arena), compresslevel=9)
    payload = dict(
        textures=tex_list,
        models=models,
        voices=voices,
        binGz=base64.b64encode(gz_bytes).decode("ascii"),
    )

    html = HTML_TEMPLATE.replace("/*__RNPC_DATA__*/null", json.dumps(payload, separators=(",", ":")))
    with open(HTML_OUT, "w", encoding="utf-8") as fp:
        fp.write(html)

    sz_mb = os.path.getsize(HTML_OUT) / (1024 * 1024)
    print(f"WROTE {HTML_OUT} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
