"""Validates all Mega-Man 3D Rider Quake assets and builds G:\\Quake\\Combat\\BakersfieldQuake\\mm_riders_3d.html:
A 100% self-contained, offline WebGL2 3D Inspector & Multi-Role Animation Studio for:
  - progs/mm_suit_rider.md3  (Screaming Tan-Blazer Suit Rider on Reclined Stainless Bucket-Seat Rig)
  - progs/mm_squat_rider.md3 (Squatting Plaid-Shirt Rider on Sparking Chrome Handlebar Chariot, Skin 0 & Skin 1)

Usage:
  python3.13 source/mm_tools/build_mm_riders_html.py
"""
import base64
import gzip
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
OUT_DIR = os.path.join(HERE, "out", "mm_riders")
OUT_HTML = os.path.join(MOD, "mm_riders_3d.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib


def validate_assets():
    print("1. Validating Quake MD3 / Skin / Shader / Texture integrity...", flush=True)
    req_pngs = [
        "mm_suit_human.png",
        "mm_suit_rig.png",
        "mm_squat_human.png",
        "mm_squat_human_grin.png",
        "mm_squat_rig.png",
        "mm_rider_fx.png",
    ]
    for fn in req_pngs:
        p = os.path.join(PROGS, fn)
        assert os.path.isfile(p), f"Missing DarkPlaces texture: {p}"

    shader_p = os.path.join(SCRIPTS, "mm_riders.shader")
    assert os.path.isfile(shader_p), f"Missing shader: {shader_p}"
    sh_txt = open(shader_p, "r", encoding="ascii").read()

    for mname, skins in (("mm_suit_rider", [0]), ("mm_squat_rider", [0, 1])):
        md3_p = os.path.join(PROGS, f"{mname}.md3")
        assert os.path.isfile(md3_p), f"Missing MD3: {md3_p}"
        for sk in skins:
            sk_p = os.path.join(PROGS, f"{mname}.md3_{sk}.skin")
            assert os.path.isfile(sk_p), f"Missing skin: {sk_p}"

        with open(md3_p, "rb") as f:
            hdr = f.read(108)
        ident, ver = struct.unpack("<4si", hdr[:8])
        assert ident == b"IDP3" and ver == 15, f"Invalid MD3 header in {md3_p}"

        m = md3lib.read(md3_p)
        assert m["nframes"] == 60, f"Expected 60 frames in {md3_p}, got {m['nframes']}"
        assert 1 <= len(m["surfaces"]) <= 32

        solid_z0 = []
        for s in m["surfaces"]:
            nv, nt = len(s["st"]), len(s["tris"])
            assert 0 < nv <= 4096, f"{mname}:{s['name']} nv={nv} > 4096!"
            assert 0 < nt <= 8192, f"{mname}:{s['name']} nt={nt} > 8192!"
            assert s["shader"] in sh_txt, f"Shader {s['shader']} missing from scripts/mm_riders.shader"
            all_v = np.asarray([fr[0] for fr in s["frames"]], dtype=np.float32)
            all_n = np.asarray([fr[1] for fr in s["frames"]], dtype=np.float32)
            assert np.isfinite(all_v).all() and np.isfinite(all_n).all()
            assert np.max(np.abs(all_v)) < 511.5
            if "fx" not in s["name"]:
                solid_z0.append(float(all_v[0, :, 2].min()))

        z_min = min(solid_z0)
        assert abs(z_min) < 0.25, f"{mname} frame 0 tire ground z_min={z_min:.3f} (expected ~0.0)"
        print(f"   [OK] {mname}.md3 : IDP3 v15, 60f, {len(m['surfaces'])} surfs, z_min={z_min:.3f}")


def img_to_data_uri(path, fmt="JPEG", quality=90, max_dim=1024):
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_dim:
        scale = max_dim / float(max(im.size))
        im = im.resize((int(im.size[0] * scale), int(im.size[1] * scale)), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    if fmt == "PNG":
        im.save(bio, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.save(bio, "JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def pack_md3_gzip_b64(md3_path):
    """Packs MD3 surfaces into compact binary + gzip + base64 for instant WebGL2 decoding."""
    m = md3lib.read(md3_path)
    nf = m["nframes"]
    meta = {"name": m["name"], "nframes": nf, "surfaces": []}
    chunks = []
    byte_off = 0

    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        tris = np.asarray(s["tris"], dtype=np.uint16).ravel().tobytes()
        st = np.asarray(s["st"], dtype=np.float32).ravel().tobytes()
        # Quantize pos to int16 (x64, exact MD3 precision!) and normals to int8 (x127)
        pos = np.clip(np.rint(np.asarray([fr[0] for fr in s["frames"]], dtype=np.float32) * 64.0), -32768, 32767).astype(np.int16).tobytes()
        nrm = np.clip(np.rint(np.asarray([fr[1] for fr in s["frames"]], dtype=np.float32) * 127.0), -127, 127).astype(np.int8).tobytes()

        # Pad each sub-buffer to 4-byte alignment
        def push_buf(b):
            nonlocal byte_off
            pad = (4 - (len(b) % 4)) % 4
            b_pad = b + (b"\0" * pad)
            off = byte_off
            chunks.append(b_pad)
            byte_off += len(b_pad)
            return off, len(b)

        o_tri, l_tri = push_buf(tris)
        o_st, l_st = push_buf(st)
        o_pos, l_pos = push_buf(pos)
        o_nrm, l_nrm = push_buf(nrm)

        meta["surfaces"].append({
            "name": s["name"],
            "shader": s["shader"],
            "nv": nv,
            "nt": nt,
            "o_tri": o_tri, "l_tri": l_tri,
            "o_st": o_st,   "l_st": l_st,
            "o_pos": o_pos, "l_pos": l_pos,
            "o_nrm": o_nrm, "l_nrm": l_nrm,
        })

    raw_bin = b"".join(chunks)
    gz = gzip.compress(raw_bin, compresslevel=9)
    meta["gz_b64"] = base64.b64encode(gz).decode("ascii")
    return meta


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BakersfieldQuake — 3D Mega-Man Riders Inspector (Vehicle / Projectile / Monster)</title>
<style>
  :root {
    --bg: #10131a; --panel: #181d27; --border: #2a3346;
    --accent: #ffb340; --accent2: #4ce0b3; --text: #e9eef7; --muted: #9aa6bd;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #sidebar { width: 350px; background: var(--panel); border-right: 1px solid var(--border); padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
  h1 { font-size: 16px; font-weight: 700; color: var(--accent); letter-spacing: 0.3px; }
  .sub { font-size: 12px; color: var(--muted); line-height: 1.4; }
  .group { background: rgba(0,0,0,0.22); border: 1px solid var(--border); border-radius: 8px; padding: 11px; display: flex; flex-direction: column; gap: 8px; }
  .group-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: var(--accent2); }
  .btn-row { display: flex; flex-wrap: wrap; gap: 6px; }
  button { background: #232b3a; color: var(--text); border: 1px solid #364258; border-radius: 6px; padding: 6px 10px; font-size: 12px; cursor: pointer; transition: 0.15s; flex: 1 1 auto; }
  button:hover { border-color: var(--accent); }
  button.active { background: var(--accent); color: #111; border-color: var(--accent); font-weight: 700; }
  label { font-size: 12px; display: flex; align-items: center; gap: 7px; cursor: pointer; color: var(--text); }
  .stat { font-family: ui-monospace, Consolas, monospace; font-size: 11px; color: var(--muted); line-height: 1.5; }
  #main { flex: 1; position: relative; display: flex; flex-direction: column; }
  #glcanvas { flex: 1; width: 100%; height: 100%; display: block; cursor: grab; background: radial-gradient(circle at 50% 42%, #eef1f6 0%, #c8d0dc 72%, #9aa5b5 100%); }
  #glcanvas.dark-bg { background: radial-gradient(circle at 50% 42%, #252c3d 0%, #121620 80%); }
  #glcanvas:active { cursor: grabbing; }
  #hud { position: absolute; top: 12px; left: 14px; background: rgba(16,19,26,0.80); border: 1px solid var(--border); padding: 8px 12px; border-radius: 8px; font-size: 12px; pointer-events: none; }
  .cmp-modal { display: none; position: fixed; inset: 24px; background: rgba(12,15,22,0.96); border: 1px solid var(--border); border-radius: 12px; z-index: 50; padding: 16px; overflow: auto; flex-direction: column; gap: 12px; }
  .cmp-modal.open { display: flex; }
  .cmp-imgs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .cmp-imgs img { width: 100%; border-radius: 8px; border: 1px solid var(--border); }
</style>
</head>
<body>
<div id="sidebar">
  <div>
    <h1>MEGA-MAN 3D QUAKE RIDERS</h1>
    <div class="sub">True 3D Quake MD3 replicas built for <b>Vehicle</b>, <b>Projectile</b> &amp; <b>Monster</b> gameplay in DarkPlaces.</div>
  </div>

  <div class="group">
    <div class="group-title">Model Selection</div>
    <div class="btn-row" id="modelBtns">
      <button data-model="both" class="active">Both Side-by-Side</button>
      <button data-model="suit">Suit Rider</button>
      <button data-model="squat">Squat Rider</button>
    </div>
  </div>

  <div class="group">
    <div class="group-title">Animation Clip (60 Frames)</div>
    <div class="btn-row" id="clipBtns">
      <button data-clip="drive" class="active">Drive Roll (12..27)</button>
      <button data-clip="idle">Idle Pose (0..11)</button>
      <button data-clip="proj">Projectile Boost (28..39)</button>
      <button data-clip="charge">Monster Charge (40..51)</button>
      <button data-clip="attack">Wheelie Slam (52..59)</button>
      <button data-clip="static0">Exact Frame 0</button>
    </div>
  </div>

  <div class="group">
    <div class="group-title">Squat Rider Skin (.skin)</div>
    <div class="btn-row" id="skinBtns">
      <button data-skin="0" class="active">Skin 0: Serious Stare</button>
      <button data-skin="1">Skin 1: Joyful Grin</button>
    </div>
  </div>

  <div class="group">
    <div class="group-title">Surface &amp; Studio Controls</div>
    <label><input type="checkbox" id="chkHuman" checked> 3D Human Rider Surface</label>
    <label><input type="checkbox" id="chkFrame" checked> Chrome Shaft / Seat / Bars</label>
    <label><input type="checkbox" id="chkWheels" checked> Spinning 5-Ribbed Tires &amp; Rims</label>
    <label><input type="checkbox" id="chkSparks" checked> 3D Additive Grinding Sparks</label>
    <label><input type="checkbox" id="chkSpin" checked> Auto-Turntable 360&deg; Orbit</label>
    <label><input type="checkbox" id="chkDarkBg"> Dark Arena Backdrop (Show Sparks)</label>
    <button id="btnCompare" style="margin-top:4px;">View Video vs MD3 Verification Sheets</button>
  </div>

  <div class="group">
    <div class="group-title">Quake Asset Specs</div>
    <div class="stat">
      <b>progs/mm_suit_rider.md3</b><br>
      &bull; 4 surfaces, 60 frames, z=0 ground<br>
      &bull; Bucket seat + twin spine ribs + V-legs<br><br>
      <b>progs/mm_squat_rider.md3</b><br>
      &bull; 4 surfaces, 60 frames, 2 skins<br>
      &bull; 5-lug grey rims + handlebars + sparks<br><br>
      <b>scripts/mm_riders.shader</b><br>
      <b>progs/mm_riders_frames.txt</b>
    </div>
  </div>
</div>

<div id="main">
  <canvas id="glcanvas"></canvas>
  <div id="hud">Drag to Orbit &bull; Scroll to Zoom &bull; Right-Drag to Pan &bull; <span id="frameInfo">Frame 12</span></div>
</div>

<div class="cmp-modal" id="cmpModal">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <h1 style="font-size:15px;">5-Angle Real Video Frame vs. Exported Quake MD3 Verification</h1>
    <button id="btnCloseCmp" style="flex:0 0 auto;padding:6px 16px;">Close</button>
  </div>
  <div class="cmp-imgs">
    <img id="cmpSuitImg" alt="Suit Rider Comparison">
    <img id="cmpSquatImg" alt="Squat Rider Comparison">
  </div>
</div>

<script>
const PAYLOAD = __PAYLOAD_JSON__;

const CLIPS = {
  static0: { start: 0,  count: 1,  fps: 0.0 },
  idle:    { start: 0,  count: 12, fps: 10.0 },
  drive:   { start: 12, count: 16, fps: 16.0 },
  proj:    { start: 28, count: 12, fps: 20.0 },
  charge:  { start: 40, count: 12, fps: 14.0 },
  attack:  { start: 52, count: 8,  fps: 12.0 },
};

let curModelMode = 'both';
let curClip = 'drive';
let curSquatSkin = 0;
let camYaw = 0.55, camPitch = 0.16, camDist = 92.0, panX = 0.0, panY = 22.0;

document.getElementById('cmpSuitImg').src = PAYLOAD.compare_suit;
document.getElementById('cmpSquatImg').src = PAYLOAD.compare_squat;
document.getElementById('btnCompare').onclick = () => document.getElementById('cmpModal').classList.add('open');
document.getElementById('btnCloseCmp').onclick = () => document.getElementById('cmpModal').classList.remove('open');

document.querySelectorAll('#modelBtns button').forEach(b => b.onclick = () => {
  document.querySelectorAll('#modelBtns button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  curModelMode = b.dataset.model;
  camDist = (curModelMode === 'both') ? 92.0 : 62.0;
});
document.querySelectorAll('#clipBtns button').forEach(b => b.onclick = () => {
  document.querySelectorAll('#clipBtns button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  curClip = b.dataset.clip;
});
document.querySelectorAll('#skinBtns button').forEach(b => b.onclick = () => {
  document.querySelectorAll('#skinBtns button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  curSquatSkin = parseInt(b.dataset.skin, 10);
});
document.getElementById('chkDarkBg').onchange = (e) => {
  document.getElementById('glcanvas').classList.toggle('dark-bg', e.target.checked);
};

async function gunzipB64(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const writer = ds.writable.getWriter();
  writer.write(bin);
  writer.close();
  const buf = await new Response(ds.readable).arrayBuffer();
  return buf;
}

const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl2', { antialias: true, alpha: true });

let dragging = false, btnMode = 0, lastX = 0, lastY = 0;
canvas.onmousedown = e => { dragging = true; btnMode = e.button; lastX = e.clientX; lastY = e.clientY; document.getElementById('chkSpin').checked = false; };
window.onmouseup = () => dragging = false;
canvas.oncontextmenu = e => e.preventDefault();
window.onmousemove = e => {
  if (!dragging) return;
  const dx = e.clientX - lastX, dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  if (btnMode === 0) {
    camYaw -= dx * 0.008;
    camPitch = Math.max(-1.2, Math.min(1.35, camPitch + dy * 0.008));
  } else {
    panX -= dx * 0.08;
    panY += dy * 0.08;
  }
};
canvas.onwheel = e => { e.preventDefault(); camDist = Math.max(24.0, Math.min(220.0, camDist * (1.0 + e.deltaY * 0.001))); };

const VS = `#version 300 es
layout(location=0) in vec3 aPos0;
layout(location=1) in vec3 aPos1;
layout(location=2) in vec3 aNrm0;
layout(location=3) in vec3 aNrm1;
layout(location=4) in vec2 aUV;
uniform mat4 uMVP;
uniform vec3 uOffset;
uniform float uLerp;
out vec2 vUV;
out vec3 vNrm;
out vec3 vPos;
void main() {
  vec3 p = mix(aPos0, aPos1, uLerp) + uOffset;
  vNrm = normalize(mix(aNrm0, aNrm1, uLerp));
  vUV = aUV;
  vPos = p;
  // Quake (+X fwd, +Y left, +Z up) -> WebGL (X=-Y_q, Y=+Z_q, Z=+X_q)
  vec3 glp = vec3(-p.y, p.z, p.x);
  gl_Position = uMVP * vec4(glp, 1.0);
}`;

const FS = `#version 300 es
precision highp float;
in vec2 vUV;
in vec3 vNrm;
in vec3 vPos;
uniform sampler2D uTex;
uniform int uMode; // 0=human, 1=rig, 2=additive_fx
uniform vec3 uCamQuake;
out vec4 fragColor;
void main() {
  vec4 tc = texture(uTex, vUV);
  if (uMode == 2) {
    fragColor = vec4(tc.rgb * 1.15, 1.0);
    return;
  }
  vec3 N = normalize(vNrm);
  vec3 L = normalize(vec3(0.42, 0.28, 0.86));
  float ndl = max(0.0, dot(N, L));
  vec3 col = tc.rgb * (0.86 + 0.18 * ndl);
  if (uMode == 1) {
    vec3 V = normalize(uCamQuake - vPos);
    vec3 H = normalize(L + V);
    float spec = pow(max(0.0, dot(N, H)), 24.0);
    col += vec3(0.18) * spec;
  }
  fragColor = vec4(col, 1.0);
}`;

function compileProg(vsSrc, fsSrc) {
  const vs = gl.createShader(gl.VERTEX_SHADER); gl.shaderSource(vs, vsSrc); gl.compileShader(vs);
  const fs = gl.createShader(gl.FRAGMENT_SHADER); gl.shaderSource(fs, fsSrc); gl.compileShader(fs);
  const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
  return p;
}
const prog = compileProg(VS, FS);

function loadTexture(uri) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([180,180,180,255]));
  const img = new Image();
  img.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  };
  img.src = uri;
  return tex;
}

const textures = {};
for (const [k, uri] of Object.entries(PAYLOAD.textures)) {
  textures[k] = loadTexture(uri);
}

async function decodeModel(mMeta) {
  const buf = await gunzipB64(mMeta.gz_b64);
  const surfs = mMeta.surfaces.map(s => {
    const tris = new Uint16Array(buf, s.o_tri, s.nt * 3);
    const st = new Float32Array(buf, s.o_st, s.nv * 2);
    const posI16 = new Int16Array(buf, s.o_pos, mMeta.nframes * s.nv * 3);
    const nrmI8 = new Int8Array(buf, s.o_nrm, mMeta.nframes * s.nv * 3);

    const framesPos = [], framesNrm = [];
    for (let f = 0; f < mMeta.nframes; f++) {
      const pArr = new Float32Array(s.nv * 3);
      const nArr = new Float32Array(s.nv * 3);
      const base = f * s.nv * 3;
      for (let i = 0; i < s.nv * 3; i++) {
        pArr[i] = posI16[base + i] / 64.0;
        nArr[i] = nrmI8[base + i] / 127.0;
      }
      framesPos.push(pArr);
      framesNrm.push(nArr);
    }

    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const bPos0 = gl.createBuffer();
    const bPos1 = gl.createBuffer();
    const bNrm0 = gl.createBuffer();
    const bNrm1 = gl.createBuffer();
    const bUV = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, bUV);
    gl.bufferData(gl.ARRAY_BUFFER, st, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(4);
    gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);

    const bIdx = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, bIdx);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tris, gl.STATIC_DRAW);

    return { ...s, vao, bPos0, bPos1, bNrm0, bNrm1, framesPos, framesNrm };
  });
  return { name: mMeta.name, nframes: mMeta.nframes, surfaces: surfs };
}

function mat4Perspective(fovy, aspect, near, far) {
  const f = 1.0 / Math.tan(fovy / 2), nf = 1 / (near - far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
}
function mat4LookAt(eye, ctr, up) {
  let zx = eye[0]-ctr[0], zy = eye[1]-ctr[1], zz = eye[2]-ctr[2];
  let zl = Math.hypot(zx,zy,zz); zx/=zl; zy/=zl; zz/=zl;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  let xl = Math.hypot(xx,xy,xz); xx/=xl; xy/=xl; xz/=xl;
  let yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  return new Float32Array([
    xx, yx, zx, 0,
    xy, yy, zy, 0,
    xz, yz, zz, 0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]), -(yx*eye[0]+yy*eye[1]+yz*eye[2]), -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}
function mat4Mul(a, b) {
  const o = new Float32Array(16);
  for (let c=0;c<4;c++) for (let r=0;r<4;r++) o[c*4+r] = a[0*4+r]*b[c*4+0]+a[1*4+r]*b[c*4+1]+a[2*4+r]*b[c*4+2]+a[3*4+r]*b[c*4+3];
  return o;
}

(async () => {
  const suitM = await decodeModel(PAYLOAD.suit);
  const squatM = await decodeModel(PAYLOAD.squat);

  let lastT = performance.now(), animClock = 0.0;
  function render(now) {
    const dt = Math.min(0.1, (now - lastT) * 0.001);
    lastT = now;
    if (document.getElementById('chkSpin').checked) camYaw += dt * 0.55;

    const dpr = window.devicePixelRatio || 1;
    const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);

    const clip = CLIPS[curClip];
    animClock += dt * clip.fps;
    const fRel = (clip.count > 1) ? (animClock % clip.count) : 0.0;
    const f0 = clip.start + Math.floor(fRel);
    const f1 = clip.start + ((Math.floor(fRel) + 1) % clip.count);
    const lerp = (clip.count > 1) ? (fRel - Math.floor(fRel)) : 0.0;
    document.getElementById('frameInfo').textContent = `Clip: ${curClip.toUpperCase()} | Frame ${f0} -> ${f1}`;

    const ex = panX + camDist * Math.cos(camPitch) * Math.sin(camYaw);
    const ey = panY + camDist * Math.sin(camPitch);
    const ez = camDist * Math.cos(camPitch) * Math.cos(camYaw);
    const mvp = mat4Mul(mat4Perspective(0.68, w / Math.max(1, h), 1.0, 600.0), mat4LookAt([ex, ey, ez], [panX, panY, 0], [0, 1, 0]));
    // Inverse map WebGL eye (X=-Y_q, Y=+Z_q, Z=+X_q) -> Quake (X_q=ez, Y_q=-ex, Z_q=ey)
    const camQuake = [ez, -ex, ey];

    gl.useProgram(prog);
    gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mvp);
    gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);
    gl.uniform3fv(gl.getUniformLocation(prog, 'uCamQuake'), camQuake);

    const showH = document.getElementById('chkHuman').checked;
    const showF = document.getElementById('chkFrame').checked;
    const showW = document.getElementById('chkWheels').checked;
    const showS = document.getElementById('chkSparks').checked;

    const draws = [];
    if (curModelMode === 'both') {
      draws.push({ m: suitM,  off: [0, +26, 0], isSquat: false });
      draws.push({ m: squatM, off: [0, -26, 0], isSquat: true });
    } else if (curModelMode === 'suit') {
      draws.push({ m: suitM,  off: [0, 0, 0], isSquat: false });
    } else {
      draws.push({ m: squatM, off: [0, 0, 0], isSquat: true });
    }

    for (const passFX of [false, true]) {
      if (passFX) {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.ONE, gl.ONE);
        gl.depthMask(false);
      } else {
        gl.disable(gl.BLEND);
        gl.depthMask(true);
      }
      for (const item of draws) {
        gl.uniform3fv(gl.getUniformLocation(prog, 'uOffset'), item.off);
        for (const s of item.m.surfaces) {
          const isFX = s.name.includes('fx');
          if (isFX !== passFX) continue;
          if (s.name === 'rider_human' && !showH) continue;
          if (s.name === 'rider_frame' && !showF) continue;
          if (s.name === 'rider_wheels' && !showW) continue;
          if (isFX && !showS) continue;

          gl.bindVertexArray(s.vao);
          const bindAttrib = (buf, loc, arr) => {
            gl.bindBuffer(gl.ARRAY_BUFFER, buf);
            gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STREAM_DRAW);
            gl.enableVertexAttribArray(loc);
            gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0);
          };
          bindAttrib(s.bPos0, 0, s.framesPos[f0]);
          bindAttrib(s.bPos1, 1, s.framesPos[f1]);
          bindAttrib(s.bNrm0, 2, s.framesNrm[f0]);
          bindAttrib(s.bNrm1, 3, s.framesNrm[f1]);

          let shKey = s.shader;
          if (item.isSquat && s.name === 'rider_human' && curSquatSkin === 1) {
            shKey = 'progs/mm_squat_human_grin';
          }
          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, textures[shKey]);
          gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
          gl.uniform1i(gl.getUniformLocation(prog, 'uMode'), isFX ? 2 : (s.name === 'rider_human' ? 0 : 1));
          gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
        }
      }
    }
    gl.depthMask(true);
    gl.disable(gl.BLEND);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
})();
</script>
</body>
</html>
"""


def main():
    validate_assets()
    print("2. Packing WebGL2 3D showcase HTML...", flush=True)
    payload = {
        "suit": pack_md3_gzip_b64(os.path.join(PROGS, "mm_suit_rider.md3")),
        "squat": pack_md3_gzip_b64(os.path.join(PROGS, "mm_squat_rider.md3")),
        "textures": {
            "progs/mm_suit_human": img_to_data_uri(os.path.join(OUT_DIR, "mm_suit_human_srgb.png"), "JPEG", 92),
            "progs/mm_suit_rig": img_to_data_uri(os.path.join(OUT_DIR, "mm_suit_rig_srgb.png"), "JPEG", 92),
            "progs/mm_squat_human": img_to_data_uri(os.path.join(OUT_DIR, "mm_squat_human_srgb.png"), "JPEG", 92),
            "progs/mm_squat_human_grin": img_to_data_uri(os.path.join(OUT_DIR, "mm_squat_human_grin_srgb.png"), "JPEG", 92),
            "progs/mm_squat_rig": img_to_data_uri(os.path.join(OUT_DIR, "mm_squat_rig_srgb.png"), "JPEG", 92),
            "progs/mm_rider_fx": img_to_data_uri(os.path.join(OUT_DIR, "mm_rider_fx_srgb.png"), "PNG"),
        },
        "compare_suit": img_to_data_uri(os.path.join(OUT_DIR, "compare_suit_md3.png"), "JPEG", 88, max_dim=1600),
        "compare_squat": img_to_data_uri(os.path.join(OUT_DIR, "compare_squat_md3.png"), "JPEG", 88, max_dim=1600),
    }

    html_out = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", json.dumps(payload, separators=(",", ":")))
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"Wrote {OUT_HTML} ({os.path.getsize(OUT_HTML):,} bytes)")


if __name__ == "__main__":
    main()
