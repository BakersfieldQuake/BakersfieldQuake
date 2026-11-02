r"""Builds TWO interactive 3D WebGL2 Viewers for the Pink Exotic Supercar ('It's not pink') + Roof Webcam:
  1. G:\Quake\Combat\BakersfieldQuake\pink_supercar.html
     Full-featured standalone offline WebGL2 Studio Showroom, Articulation Rig,
     Live Roof-Webcam Streamer POV, & Interactive WASD V12 Test-Drive!
  2. Optional artifact HTML path (passed via CLI argv[1]) styled with Antigravity
     Generative UI semantic theme variables & Tailwind CSS for side-pane inspection!
"""
import base64
import io
import json
import math
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out", "pink_supercar")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pink_supercar_tex as ptex

SCALE = 0.025  # 1 Quake unit = 0.025 m


def img_to_data_uri(path, max_dim=2048, fmt="JPEG", quality=91):
    im = Image.open(path)
    w0, h0 = im.size
    if max_dim and max(w0, h0) > max_dim:
        sc = max_dim / float(max(w0, h0))
        im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    if fmt == "PNG":
        im.save(bio, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.convert("RGB").save(bio, "JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def pack_parts_for_webgl(npz_path):
    data = np.load(npz_path)
    part_names = [
        "chassis", "hood", "door_l", "door_r",
        "webcam_base", "webcam_head",
        "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr",
        "glass", "door_l_glass", "door_r_glass",
    ]
    glass_set = {"glass", "door_l_glass", "door_r_glass"}
    out = {}
    tot_v, tot_t = 0, 0
    for nm in part_names:
        oq = data[f"{nm}_origin"].astype(np.float32)
        vq = data[f"{nm}_verts"].astype(np.float32)
        nq = data[f"{nm}_norms"].astype(np.float32)
        uv = data[f"{nm}_uvs"].astype(np.float32)
        tr = data[f"{nm}_tris"].astype(np.uint16).reshape(-1)

        tot_v += len(vq)
        tot_t += len(tr) // 3

        # (X_q, Y_q, Z_q) -> (Y_q, Z_q, X_q) * SCALE
        vg = np.column_stack([vq[:, 1], vq[:, 2], vq[:, 0]]) * SCALE
        ng = np.column_stack([nq[:, 1], nq[:, 2], nq[:, 0]])
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-8)
        inter = np.hstack([vg, ng, uv]).astype("<f4")

        out[nm] = {
            "pivot": [round(float(oq[1] * SCALE), 5), round(float(oq[2] * SCALE), 5), round(float(oq[0] * SCALE), 5)],
            "glass": 1 if nm in glass_set else 0,
            "nv": int(len(vq)),
            "ni": int(len(tr)),
            "vb64": base64.b64encode(inter.tobytes()).decode("ascii"),
            "ib64": base64.b64encode(tr.tobytes()).decode("ascii"),
        }
    return out, tot_v, tot_t


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>"It's Not Pink" Exotic Supercar + Roof Webcam — Interactive 3D Studio</title>
__TAILWIND_TAG__
<style>
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden;
    background: var(--background, #090b12);
    color: var(--foreground, #f1f5f9);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    user-select: none;
  }
  canvas#gl { position: fixed; inset: 0; width: 100%; height: 100%; display: block; cursor: grab; }
  canvas#gl:active { cursor: grabbing; }

  .hud-top {
    position: fixed; top: 14px; left: 14px; right: 14px; z-index: 10;
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 10px;
    pointer-events: none;
  }
  .card-glass {
    pointer-events: auto;
    background: rgba(13, 17, 28, 0.84);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 105, 180, 0.32);
    border-radius: 14px;
    padding: 12px 16px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
  }
  .badge-pink {
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    background: rgba(255, 79, 163, 0.2); border: 1px solid rgba(255, 105, 180, 0.55);
    color: #ff7cc3; font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  }
  h1 { margin: 5px 0 2px; font-size: 20px; font-weight: 800; color: #fff; letter-spacing: -0.01em; }
  .sub { margin: 0; font-size: 12.5px; color: #cbd5e1; }

  .cam-bar {
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px;
  }
  button.btn {
    cursor: pointer; border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(30, 38, 58, 0.85); color: #f1f5f9;
    padding: 6px 11px; border-radius: 8px; font-size: 12px; font-weight: 600;
    transition: all 0.14s ease;
  }
  button.btn:hover { border-color: #ff66b5; background: rgba(255, 79, 163, 0.22); }
  button.btn.active {
    background: linear-gradient(135deg, #ff4fa3, #d9267a);
    border-color: #ffc2e2; color: #fff; box-shadow: 0 0 14px rgba(255, 79, 163, 0.45);
  }

  .hud-right {
    position: fixed; bottom: 14px; right: 14px; z-index: 10; width: 310px;
    max-height: calc(100vh - 150px); overflow-y: auto;
  }
  .ctrl-row { margin-top: 9px; }
  .ctrl-label {
    display: flex; justify-content: space-between; font-size: 12px; color: #e2e8f0; margin-bottom: 3px; font-weight: 600;
  }
  input[type=range] {
    width: 100%; accent-color: #ff4fa3; cursor: pointer; height: 6px;
  }

  /* Authentic 2000s Roof USB Webcam OSD Overlay! */
  #webcam-osd {
    display: none; position: fixed; inset: 18px; z-index: 5; pointer-events: none;
    border: 2px solid rgba(74, 255, 148, 0.65); border-radius: 10px;
    box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.55);
    font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
  }
  #webcam-osd.visible { display: block; }
  .osd-rec {
    position: absolute; top: 14px; left: 18px; display: flex; align-items: center; gap: 8px;
    background: rgba(0, 0, 0, 0.68); padding: 5px 12px; border-radius: 6px;
    color: #4aff94; font-size: 13px; font-weight: 700;
  }
  .rec-dot {
    width: 10px; height: 10px; border-radius: 50%; background: #ff3355;
    box-shadow: 0 0 10px #ff3355; animation: blink 1s infinite;
  }
  .osd-meta {
    position: absolute; bottom: 14px; left: 18px;
    background: rgba(0, 0, 0, 0.68); padding: 5px 12px; border-radius: 6px;
    color: #e2e8f0; font-size: 12px;
  }
  @keyframes blink { 0%, 55% { opacity: 1; } 56%, 100% { opacity: 0.18; } }

  .drive-hint {
    position: fixed; bottom: 14px; left: 14px; z-index: 10; font-size: 12px; color: #cbd5e1;
  }
</style>
</head>
<body>
<canvas id="gl"></canvas>

<div id="webcam-osd">
  <div class="osd-rec"><span class="rec-dot"></span> REC · USB 2.0 ROOF_WEBCAM_01 · 640×480 30FPS</div>
  <div class="osd-meta">HOOD VIEW: "Say no to drugs." · VEHICLE COLOR: DEFINITELY NOT PINK (SALMON)</div>
</div>

<div class="hud-top">
  <div class="card-glass" style="max-width: 720px;">
    <span class="badge-pink">Exotic V12 Supercar · __STATS__</span>
    <h1>"It's Not Pink" Supercar + Roof USB Webcam</h1>
    <p class="sub">Painted hood mural (<i>"Say no to drugs."</i>) · Dual-side <b>"It's not pink"</b> scissor doors · Articulated 1080p roof webcam</p>
    <div class="cam-bar" id="preset-bar">
      <button class="btn active" data-cam="hero">1 · Hero 3/4</button>
      <button class="btn" data-cam="hood">2 · Hood Painting</button>
      <button class="btn" data-cam="left">3 · Left ("It's not pink")</button>
      <button class="btn" data-cam="right">4 · Right ("It's not pink")</button>
      <button class="btn" data-cam="webcam">5 · Roof Webcam Macro</button>
      <button class="btn" data-cam="rear">6 · Rear V12 &amp; Plate</button>
      <button class="btn" data-cam="webcam_pov">7 · 📹 Live Webcam POV</button>
    </div>
  </div>
</div>

<div class="hud-right card-glass">
  <div style="font-size:13px;font-weight:800;color:#ff85c8;margin-bottom:6px;">Animation &amp; Articulation Rig</div>
  <div class="cam-bar" id="anim-bar" style="margin-top:4px;margin-bottom:8px;">
    <button class="btn active" data-anim="idle">Idle Scan</button>
    <button class="btn" data-anim="cruise">Cruise</button>
    <button class="btn" data-anim="scissor">Scissor Doors</button>
    <button class="btn" data-anim="boost">V12 Boost</button>
    <button class="btn" data-anim="drive">🎮 Drive (WASD)</button>
  </div>

  <div class="ctrl-row">
    <div class="ctrl-label"><span>Scissor Doors</span><span id="val-door">0°</span></div>
    <input type="range" id="sl-door" min="0" max="60" step="1" value="0">
  </div>
  <div class="ctrl-row">
    <div class="ctrl-label"><span>Front Hood Pop</span><span id="val-hood">0°</span></div>
    <input type="range" id="sl-hood" min="0" max="34" step="1" value="0">
  </div>
  <div class="ctrl-row">
    <div class="ctrl-label"><span>Webcam Pan (Left/Right)</span><span id="val-cpan">0°</span></div>
    <input type="range" id="sl-cpan" min="-75" max="75" step="1" value="0">
  </div>
  <div class="ctrl-row">
    <div class="ctrl-label"><span>Webcam Tilt (Up/Down)</span><span id="val-ctilt">0°</span></div>
    <input type="range" id="sl-ctilt" min="-25" max="25" step="1" value="0">
  </div>
  <div class="ctrl-row">
    <div class="ctrl-label"><span>Front Wheel Steer</span><span id="val-steer">0°</span></div>
    <input type="range" id="sl-steer" min="-30" max="30" step="1" value="0">
  </div>
</div>

<div class="drive-hint card-glass">
  <b>Orbit:</b> Left-drag · <b>Pan:</b> Right-drag · <b>Zoom:</b> Scroll · <b>Drive Mode:</b> W/A/S/D + Space Brake
</div>

<script>
const PARTS_DATA = __PARTS_JSON__;
const TEX_URIS = __TEX_JSON__;

const canvas = document.getElementById('gl');
const gl = canvas.getContext('webgl2', { antialias: true, alpha: false });

function compileShader(type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}
function createProg(vs, fs) {
  const p = gl.createProgram();
  gl.attachShader(p, compileShader(gl.VERTEX_SHADER, vs));
  gl.attachShader(p, compileShader(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
}

const VS_CAR = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;
uniform mat4 uVP;
uniform mat4 uModel;
out vec3 vWorldPos;
out vec3 vNrm;
out vec2 vUV;
void main() {
  vec4 wp = uModel * vec4(aPos, 1.0);
  vWorldPos = wp.xyz;
  vNrm = mat3(uModel) * aNrm;
  vUV = aUV;
  gl_Position = uVP * wp;
}`;

const FS_CAR = `#version 300 es
precision highp float;
in vec3 vWorldPos;
in vec3 vNrm;
in vec2 vUV;
uniform sampler2D uBase;
uniform sampler2D uORM;
uniform sampler2D uGlow;
uniform sampler2D uGlass;
uniform vec3 uCamPos;
uniform int uIsGlass;
out vec4 fragColor;

void main() {
  vec3 N = normalize(vNrm);
  vec3 V = normalize(uCamPos - vWorldPos);
  if (dot(N, V) < 0.0) N = -N;

  if (uIsGlass == 1) {
    vec4 gc = texture(uGlass, vUV);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 3.2);
    vec3 sky = mix(vec3(0.18, 0.20, 0.30), vec3(1.0, 0.55, 0.82), fres);
    vec3 H = normalize(normalize(vec3(0.45, 0.85, 0.35)) + V);
    float spec = pow(max(dot(N, H), 0.0), 96.0);
    vec3 col = mix(gc.rgb, sky, 0.45 * fres) + vec3(1.0, 0.95, 0.98) * spec * 0.9;
    fragColor = vec4(col, clamp(gc.a + fres * 0.35, 0.25, 0.96));
    return;
  }

  vec3 base = pow(texture(uBase, vUV).rgb, vec3(2.2));
  vec3 orm  = texture(uORM, vUV).rgb;
  vec3 glow = texture(uGlow, vUV).rgb;
  float rough = clamp(orm.g, 0.06, 1.0);
  float metal = orm.b;

  vec3 L1 = normalize(vec3(0.52, 0.78, 0.34));
  vec3 L2 = normalize(vec3(-0.62, 0.55, -0.55));
  float ndl1 = max(dot(N, L1), 0.0);
  float ndl2 = max(dot(N, L2), 0.0);

  vec3 H1 = normalize(L1 + V);
  vec3 H2 = normalize(L2 + V);
  float shininess = mix(180.0, 10.0, rough);
  float sp1 = pow(max(dot(N, H1), 0.0), shininess) * mix(1.25, 0.15, rough);
  float sp2 = pow(max(dot(N, H2), 0.0), shininess * 0.7) * 0.45;

  // Automotive clearcoat reflection + studio horizon band
  vec3 R = reflect(-V, N);
  float envBand = smoothstep(-0.15, 0.55, R.y);
  vec3 envCol = mix(vec3(0.05, 0.05, 0.09), vec3(0.62, 0.54, 0.66), envBand);
  float clearcoat = pow(1.0 - max(dot(N, V), 0.0), 3.6) * (1.0 - rough * 0.7);

  vec3 diffCol = base * (1.0 - metal * 0.75);
  vec3 specCol = mix(vec3(0.055), base, metal);
  vec3 hemi = mix(vec3(0.11, 0.10, 0.15), vec3(0.52, 0.50, 0.58), N.y * 0.5 + 0.5);

  vec3 lit = diffCol * (hemi + vec3(1.05, 0.99, 0.97) * ndl1 + vec3(0.42, 0.48, 0.62) * ndl2)
           + (specCol + clearcoat * 0.45) * (sp1 + sp2)
           + envCol * (clearcoat * 0.55 + metal * 0.28)
           + glow * 1.65;

  lit = lit / (lit + vec3(0.88));
  fragColor = vec4(pow(clamp(lit * 1.38, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}`;

const VS_FLOOR = `#version 300 es
layout(location=0) in vec2 aXZ;
uniform mat4 uVP;
out vec2 vXZ;
void main() {
  vXZ = aXZ;
  gl_Position = uVP * vec4(aXZ.x, -0.002, aXZ.y, 1.0);
}`;

const FS_FLOOR = `#version 300 es
precision highp float;
in vec2 vXZ;
uniform vec3 uCarPos;
uniform float uCarYaw;
out vec4 fragColor;
void main() {
  vec2 d = vXZ - uCarPos.xz;
  float c = cos(-uCarYaw), s = sin(-uCarYaw);
  vec2 loc = vec2(d.x * c - d.y * s, d.x * s + d.y * c);
  // Soft analytical supercar underbody & 4-tire contact shadow
  vec2 q = abs(loc) - vec2(0.88, 2.15);
  float boxDist = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
  float shadow = 1.0 - 0.78 * (1.0 - smoothstep(-0.15, 0.65, boxDist));

  // Showroom neon grid
  vec2 gv = abs(fract(vXZ * 0.5 - 0.5) - 0.5) / fwidth(vXZ * 0.5);
  float line = 1.0 - min(min(gv.x, gv.y), 1.0);
  float distFade = exp(-length(d) * 0.065);
  vec3 base = mix(vec3(0.045, 0.050, 0.078), vec3(0.085, 0.092, 0.138), distFade);
  vec3 gridCol = mix(base, vec3(0.95, 0.32, 0.68), line * 0.32 * distFade);
  fragColor = vec4(gridCol * shadow, 1.0);
}`;

const progCar = createProg(VS_CAR, FS_CAR);
const progFloor = createProg(VS_FLOOR, FS_FLOOR);

function b64ToBytes(b64) {
  const bin = atob(b64);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return u8;
}

const gpuParts = {};
for (const [nm, p] of Object.entries(PARTS_DATA)) {
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const vbo = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
  gl.bufferData(gl.ARRAY_BUFFER, b64ToBytes(p.vb64), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);
  const ibo = gl.createBuffer();
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, b64ToBytes(p.ib64), gl.STATIC_DRAW);
  gpuParts[nm] = { ...p, vao };
}

// Floor quad VAO
const floorVAO = gl.createVertexArray();
gl.bindVertexArray(floorVAO);
const floorVBO = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, floorVBO);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-80,-80, 80,-80, 80,80, -80,-80, 80,80, -80,80]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 8, 0);

function loadTex(uri, isRGBA=false) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([235, 80, 160, 255]));
  const img = new Image();
  img.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, isRGBA ? gl.RGBA : gl.RGB, isRGBA ? gl.RGBA : gl.RGB, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  };
  img.src = uri;
  return tex;
}

const tBase  = loadTex(TEX_URIS.atlas, false);
const tORM   = loadTex(TEX_URIS.orm, false);
const tGlow  = loadTex(TEX_URIS.glow, false);
const tGlass = loadTex(TEX_URIS.glass, true);

// Minimal Matrix4 helpers (column-major)
function m4Identity() { const m = new Float32Array(16); m[0]=m[5]=m[10]=m[15]=1; return m; }
function m4Mul(a, b) {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let r = 0; r < 4; r++) {
      o[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1] + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
    }
  }
  return o;
}
function m4Translate(x, y, z) { const m = m4Identity(); m[12]=x; m[13]=y; m[14]=z; return m; }
function m4RotX(rad) { const m=m4Identity(), c=Math.cos(rad), s=Math.sin(rad); m[5]=c; m[6]=s; m[9]=-s; m[10]=c; return m; }
function m4RotY(rad) { const m=m4Identity(), c=Math.cos(rad), s=Math.sin(rad); m[0]=c; m[2]=-s; m[8]=s; m[10]=c; return m; }
function m4RotZ(rad) { const m=m4Identity(), c=Math.cos(rad), s=Math.sin(rad); m[0]=c; m[1]=s; m[4]=-s; m[5]=c; return m; }
function m4Persp(fovY, asp, zn, zf) {
  const f = 1.0 / Math.tan(fovY * 0.5), nf = 1.0 / (zn - zf);
  const m = new Float32Array(16);
  m[0] = f / asp; m[5] = f; m[10] = (zf + zn) * nf; m[11] = -1; m[14] = 2 * zf * zn * nf;
  return m;
}
function m4LookAt(eye, tgt, up=[0,1,0]) {
  let zx = eye[0]-tgt[0], zy = eye[1]-tgt[1], zz = eye[2]-tgt[2];
  let zl = Math.hypot(zx,zy,zz)||1; zx/=zl; zy/=zl; zz/=zl;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  let xl = Math.hypot(xx,xy,xz)||1; xx/=xl; xy/=xl; xz/=xl;
  let yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  const m = m4Identity();
  m[0]=xx; m[4]=xy; m[8]=xz;  m[12]=-(xx*eye[0]+xy*eye[1]+xz*eye[2]);
  m[1]=yx; m[5]=yy; m[9]=yz;  m[13]=-(yx*eye[0]+yy*eye[1]+yz*eye[2]);
  m[2]=zx; m[6]=zy; m[10]=zz; m[14]=-(zx*eye[0]+zy*eye[1]+zz*eye[2]);
  return m;
}

// Orbit & Preset State (glTF meters: +Y up, +Z forward, +X left!)
let camYaw = 0.68, camPitch = 0.30, camDist = 5.35;
let camTarget = [0.0, 0.58, 0.15];
let camMode = 'orbit';
let animMode = 'idle';
let manualOverride = false;

const PRESETS = {
  hero:       { yaw:  0.68, pitch: 0.30, dist: 5.35, tgt: [0.0, 0.58, 0.15], mode: 'orbit' },
  hood:       { yaw:  0.00, pitch: 0.62, dist: 2.65, tgt: [0.0, 0.56, 1.48], mode: 'orbit' },
  left:       { yaw:  1.57, pitch: 0.12, dist: 4.85, tgt: [0.0, 0.58, 0.05], mode: 'orbit' },
  right:      { yaw: -1.57, pitch: 0.12, dist: 4.85, tgt: [0.0, 0.58, 0.05], mode: 'orbit' },
  webcam:     { yaw:  0.55, pitch: 0.24, dist: 1.55, tgt: [0.0, 1.38, -0.04], mode: 'orbit' },
  rear:       { yaw: -2.55, pitch: 0.26, dist: 5.10, tgt: [0.0, 0.64, -0.25], mode: 'orbit' },
  webcam_pov: { yaw:  0.00, pitch: 0.00, dist: 2.00, tgt: [0.0, 1.40, 0.0], mode: 'webcam_pov' },
};

document.querySelectorAll('#preset-bar .btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#preset-bar .btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const p = PRESETS[btn.dataset.cam];
    camMode = p.mode;
    document.getElementById('webcam-osd').classList.toggle('visible', camMode === 'webcam_pov');
    if (p.mode === 'orbit') {
      camYaw = p.yaw; camPitch = p.pitch; camDist = p.dist;
      camTarget = [...p.tgt];
    }
  });
});

document.querySelectorAll('#anim-bar .btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#anim-bar .btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    animMode = btn.dataset.anim;
    manualOverride = false;
  });
});

const slDoor  = document.getElementById('sl-door');
const slHood  = document.getElementById('sl-hood');
const slCPan  = document.getElementById('sl-cpan');
const slCTilt = document.getElementById('sl-ctilt');
const slSteer = document.getElementById('sl-steer');
[slDoor, slHood, slCPan, slCTilt, slSteer].forEach(sl => {
  sl.addEventListener('input', () => { manualOverride = true; });
});

// Mouse / Touch Orbit
let dragging = false, rightDrag = false, lx = 0, ly = 0;
canvas.addEventListener('pointerdown', e => {
  dragging = true; rightDrag = (e.button === 2); lx = e.clientX; ly = e.clientY;
  canvas.setPointerCapture(e.pointerId);
});
window.addEventListener('pointerup', () => { dragging = false; });
window.addEventListener('pointermove', e => {
  if (!dragging || camMode === 'webcam_pov') return;
  const dx = e.clientX - lx, dy = e.clientY - ly;
  lx = e.clientX; ly = e.clientY;
  if (rightDrag) {
    camTarget[0] -= dx * 0.005;
    camTarget[1] += dy * 0.005;
  } else {
    camYaw -= dx * 0.007;
    camPitch = Math.max(0.03, Math.min(1.42, camPitch + dy * 0.007));
  }
});
canvas.addEventListener('contextmenu', e => e.preventDefault());
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  camDist = Math.max(1.1, Math.min(14.0, camDist * (1 + e.deltaY * 0.001)));
}, { passive: false });

// WASD Test Drive Physics State
const keys = {};
window.addEventListener('keydown', e => { keys[e.code] = true; });
window.addEventListener('keyup', e => { keys[e.code] = false; });
let carX = 0, carZ = 0, carHeading = 0, carSpeed = 0, wheelAngle = 0, driveSteer = 0;

let lastT = performance.now() * 0.001;
function frame(nowMs) {
  requestAnimationFrame(frame);
  const t = nowMs * 0.001;
  const dt = Math.min(0.05, Math.max(0.001, t - lastT));
  lastT = t;

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.floor(window.innerWidth * dpr), h = Math.floor(window.innerHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.045, 0.050, 0.082, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  // Articulation Parameters (degrees)
  let doorDeg = +slDoor.value, hoodDeg = +slHood.value;
  let cPanDeg = +slCPan.value, cTiltDeg = +slCTilt.value, steerDeg = +slSteer.value;
  let bodyPitchDeg = 0, bodyRollDeg = 0, bodyBobM = 0;

  if (animMode === 'drive') {
    const thr = (keys['KeyW'] || keys['ArrowUp'] ? 1 : 0) - (keys['KeyS'] || keys['ArrowDown'] ? 1 : 0);
    const stIn = (keys['KeyA'] || keys['ArrowLeft'] ? 1 : 0) - (keys['KeyD'] || keys['ArrowRight'] ? 1 : 0);
    driveSteer += (stIn * 28.0 - driveSteer) * Math.min(1, dt * 8.0);
    if (keys['Space']) carSpeed *= Math.pow(0.04, dt);
    else carSpeed += thr * 9.5 * dt - carSpeed * 0.65 * dt;
    carHeading += (driveSteer * Math.PI / 180) * (carSpeed * 0.24) * dt;
    carX += Math.sin(carHeading) * carSpeed * dt;
    carZ += Math.cos(carHeading) * carSpeed * dt;
    wheelAngle += (carSpeed / 0.34) * (180 / Math.PI) * dt;
    steerDeg = driveSteer;
    bodyPitchDeg = -thr * 1.4;
    bodyRollDeg = driveSteer * carSpeed * 0.035;
    cPanDeg = driveSteer * 1.1;
  } else {
    carX = 0; carZ = 0; carHeading = 0;
    if (!manualOverride) {
      if (animMode === 'idle') {
        doorDeg = 0; hoodDeg = 0; steerDeg = 0;
        cPanDeg = 28 * Math.sin(t * 1.3);
        cTiltDeg = -4 + 7 * Math.sin(t * 2.6);
        bodyBobM = 0.004 * Math.sin(t * 9.0);
      } else if (animMode === 'cruise') {
        doorDeg = 0; hoodDeg = 0;
        steerDeg = 6 * Math.sin(t * 1.5);
        wheelAngle = (t * 540) % 360;
        cPanDeg = 16 * Math.sin(t * 1.5);
        cTiltDeg = -3 + 4 * Math.cos(t * 3.0);
        bodyBobM = 0.009 * Math.sin(t * 5.0);
      } else if (animMode === 'scissor') {
        const s = 0.5 - 0.5 * Math.cos(t * 1.6);
        const sh = Math.min(1, s * 1.3);
        doorDeg = 58 * (sh * sh * (3 - 2 * sh));
        hoodDeg = 18 * (sh * sh * (3 - 2 * sh));
        cPanDeg = 36 * Math.sin(t * 1.6) * sh;
        cTiltDeg = 7 * sh;
      } else if (animMode === 'boost') {
        doorDeg = 0; hoodDeg = 0;
        wheelAngle = (t * 1180) % 360;
        bodyPitchDeg = -2.2 * (0.6 + 0.4 * Math.sin(t * 8.0));
        cPanDeg = 7 * Math.sin(t * 7.0);
        cTiltDeg = -13;
      }
      slDoor.value = Math.round(doorDeg);
      slHood.value = Math.round(hoodDeg);
      slCPan.value = Math.round(cPanDeg);
      slCTilt.value = Math.round(cTiltDeg);
      slSteer.value = Math.round(steerDeg);
    }
  }

  document.getElementById('val-door').textContent  = `${Math.round(doorDeg)}°`;
  document.getElementById('val-hood').textContent  = `${Math.round(hoodDeg)}°`;
  document.getElementById('val-cpan').textContent  = `${Math.round(cPanDeg)}°`;
  document.getElementById('val-ctilt').textContent = `${Math.round(cTiltDeg)}°`;
  document.getElementById('val-steer').textContent = `${Math.round(steerDeg)}°`;

  // World root transform of car (glTF space: X=left, Y=up, Z=forward)
  const mCarRoot = m4Mul(m4Translate(carX, 0, carZ), m4RotY(carHeading));
  const mBody = m4Mul(mCarRoot, m4Mul(m4Translate(0, bodyBobM, 0),
                m4Mul(m4RotX(bodyPitchDeg * Math.PI / 180), m4RotZ(bodyRollDeg * Math.PI / 180))));

  function childAtPivot(parentM, piv, localR) {
    return m4Mul(parentM, m4Mul(m4Translate(piv[0], piv[1], piv[2]), localR));
  }

  const flareRad = (11.0 * (doorDeg / 58.0)) * Math.PI / 180;
  const doorRad  = doorDeg * Math.PI / 180;
  const partMats = {
    chassis:      mBody,
    glass:        mBody,
    webcam_base:  mBody,
    hood:         childAtPivot(mBody, gpuParts.hood.pivot, m4RotX(-hoodDeg * Math.PI / 180)),
    door_l:       childAtPivot(mBody, gpuParts.door_l.pivot, m4Mul(m4RotY(flareRad), m4RotX(doorRad))),
    door_r:       childAtPivot(mBody, gpuParts.door_r.pivot, m4Mul(m4RotY(-flareRad), m4RotX(doorRad))),
    webcam_head:  childAtPivot(mBody, gpuParts.webcam_head.pivot,
                    m4Mul(m4RotY(cPanDeg * Math.PI / 180), m4RotX(-cTiltDeg * Math.PI / 180))),
  };
  partMats.door_l_glass = partMats.door_l;
  partMats.door_r_glass = partMats.door_r;

  for (const wnm of ['wheel_fl', 'wheel_fr', 'wheel_rl', 'wheel_rr']) {
    const st = (wnm === 'wheel_fl' || wnm === 'wheel_fr') ? (steerDeg * Math.PI / 180) : 0;
    const sp = wheelAngle * Math.PI / 180;
    partMats[wnm] = childAtPivot(mCarRoot, gpuParts[wnm].pivot, m4Mul(m4RotY(st), m4RotX(sp)));
  }

  // Camera Matrix (Orbit, Chase, or LIVE ROOF WEBCAM POV!)
  let eye, viewM, fovRad = 42 * Math.PI / 180;
  if (camMode === 'webcam_pov') {
    fovRad = 64 * Math.PI / 180; // Wide 640x480 webcam lens!
    const mw = partMats.webcam_head;
    const lx = 0.0, ly = 0.11, lz = 0.20; // Local offset from webcam_head pivot to front tip of optical lens!
    eye = [
      mw[0]*lx + mw[4]*ly + mw[8]*lz + mw[12],
      mw[1]*lx + mw[5]*ly + mw[9]*lz + mw[13],
      mw[2]*lx + mw[6]*ly + mw[10]*lz + mw[14],
    ];
    // Look forward & slightly down over the painted "Say no to drugs." hood!
    const tx = 0.0, ty = -0.42, tz = 2.35;
    const tgt = [
      mw[0]*tx + mw[4]*ty + mw[8]*tz + mw[12],
      mw[1]*tx + mw[5]*ty + mw[9]*tz + mw[13],
      mw[2]*tx + mw[6]*ty + mw[10]*tz + mw[14],
    ];
    viewM = m4LookAt(eye, tgt, [0, 1, 0]);
  } else if (animMode === 'drive') {
    const chaseDist = 5.4;
    eye = [carX - Math.sin(carHeading) * chaseDist, 1.85, carZ - Math.cos(carHeading) * chaseDist];
    viewM = m4LookAt(eye, [carX, 0.72, carZ], [0, 1, 0]);
  } else {
    eye = [
      camTarget[0] + camDist * Math.cos(camPitch) * Math.sin(camYaw),
      camTarget[1] + camDist * Math.sin(camPitch),
      camTarget[2] + camDist * Math.cos(camPitch) * Math.cos(camYaw),
    ];
    viewM = m4LookAt(eye, camTarget, [0, 1, 0]);
  }
  const vpM = m4Mul(m4Persp(fovRad, w / Math.max(1, h), 0.08, 160.0), viewM);

  // 1. Draw Showroom Floor + Analytical Contact Shadow
  gl.disable(gl.BLEND);
  gl.depthMask(true);
  gl.useProgram(progFloor);
  gl.uniformMatrix4fv(gl.getUniformLocation(progFloor, 'uVP'), false, vpM);
  gl.uniform3f(gl.getUniformLocation(progFloor, 'uCarPos'), carX, 0, carZ);
  gl.uniform1f(gl.getUniformLocation(progFloor, 'uCarYaw'), carHeading);
  gl.bindVertexArray(floorVAO);
  gl.drawArrays(gl.TRIANGLES, 0, 6);

  // 2. Draw Opaque Supercar + Roof Webcam Parts, then Translucent Glass Parts
  gl.useProgram(progCar);
  gl.uniformMatrix4fv(gl.getUniformLocation(progCar, 'uVP'), false, vpM);
  gl.uniform3f(gl.getUniformLocation(progCar, 'uCamPos'), eye[0], eye[1], eye[2]);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tBase);  gl.uniform1i(gl.getUniformLocation(progCar, 'uBase'), 0);
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tORM);   gl.uniform1i(gl.getUniformLocation(progCar, 'uORM'), 1);
  gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, tGlow);  gl.uniform1i(gl.getUniformLocation(progCar, 'uGlow'), 2);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tGlass); gl.uniform1i(gl.getUniformLocation(progCar, 'uGlass'), 3);

  const locModel = gl.getUniformLocation(progCar, 'uModel');
  const locGlass = gl.getUniformLocation(progCar, 'uIsGlass');

  for (const pass of [0, 1]) {
    if (pass === 1) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
    }
    for (const [nm, gp] of Object.entries(gpuParts)) {
      if (gp.glass !== pass) continue;
      if (camMode === 'webcam_pov' && nm === 'webcam_head') continue;
      gl.uniform1i(locGlass, pass);
      gl.uniformMatrix4fv(locModel, false, partMats[nm]);
      gl.bindVertexArray(gp.vao);
      gl.drawElements(gl.TRIANGLES, gp.ni, gl.UNSIGNED_SHORT, 0);
    }
  }
  gl.depthMask(true);
  gl.disable(gl.BLEND);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def build_viewers(artifact_html_path=None):
    npz_path = os.path.join(OUT_DIR, "pink_supercar_parts.npz")
    parts_json, tot_v, tot_t = pack_parts_for_webgl(npz_path)

    tex_uris = {
        "atlas": img_to_data_uri(os.path.join(OUT_DIR, "pink_supercar_atlas_2k.png"), max_dim=2048, fmt="JPEG", quality=92),
        "orm":   img_to_data_uri(os.path.join(OUT_DIR, "pink_supercar_orm_2k.png"),   max_dim=1024, fmt="JPEG", quality=85),
        "glow":  img_to_data_uri(os.path.join(OUT_DIR, "pink_supercar_glow_2k.png"),  max_dim=1024, fmt="JPEG", quality=88),
        "glass": img_to_data_uri(os.path.join(OUT_DIR, "pink_supercar_glass.png"),    max_dim=512,  fmt="PNG"),
    }

    stats_str = f"{tot_v:,} Verts · {tot_t:,} Tris · GLB + Quake MD3"
    base_html = (
        HTML_TEMPLATE
        .replace("__STATS__", stats_str)
        .replace("__PARTS_JSON__", json.dumps(parts_json, separators=(",", ":")))
        .replace("__TEX_JSON__", json.dumps(tex_uris, separators=(",", ":")))
    )

    out_root_html = os.path.join(MOD_DIR, "pink_supercar.html")
    with open(out_root_html, "w", encoding="utf-8") as f:
        f.write(base_html.replace("__TAILWIND_TAG__", ""))
    print(f"Wrote standalone WebGL2 viewer: {out_root_html} ({os.path.getsize(out_root_html) / 1e6:.2f} MB)")

    if artifact_html_path:
        tw_tag = '<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>'
        with open(artifact_html_path, "w", encoding="utf-8") as af:
            af.write(base_html.replace("__TAILWIND_TAG__", tw_tag))
        print(f"Wrote artifact WebGL2 viewer: {artifact_html_path}")


if __name__ == "__main__":
    art_p = sys.argv[1] if len(sys.argv) > 1 else None
    build_viewers(art_p)
