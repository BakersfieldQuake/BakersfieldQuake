"""Builds `G:\\Quake\\Combat\\BakersfieldQuake\\wew_cannon.html`:
A 100% self-contained, zero-dependency WebGL2 3D Weapon Studio & Live Charge-Bend-Blast Simulator
for the Quake 'WEW CANNON' (`v_wewcannon.md3` / `.mdl`, `g_wewcannon` — projectile excluded as separate entity model).
"""
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
OUT_ROOT = os.path.join(MM_TOOLS, "out", "wew_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")
HTML_OUT = os.path.join(MOD_ROOT, "wew_cannon.html")

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


def encode_tex(path):
    im = Image.open(path).convert("RGBA")
    bio = io.BytesIO()
    im.save(bio, "PNG", optimize=True)
    return dict(
        name=os.path.basename(path),
        uri="data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii"),
    )


def pack_md3(md3_path, arena, surf_tex_map, surf_style):
    m = md3lib.read(md3_path)
    nf = m["nframes"]

    def add_bytes(b):
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
        tot_v += len({int(idx) for tri in s["tris"] for idx in tri})
        tot_t += nt
        # Flip MD3 CW-outward -> WebGL CCW-outward!
        tris_ccw = np.array([(a, c, b) for a, b, c in s["tris"]], dtype=np.uint16)
        edges = build_edges(tris_ccw)
        uv = np.array(s["st"], dtype=np.float32)

        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            pos_q[fi] = np.clip(np.round(np.array(vv, dtype=np.float32) * 64.0), -32768, 32767).astype(np.int16)
            nrm_q[fi] = np.clip(np.round(np.array(nn, dtype=np.float32) * 127.0), -127, 127).astype(np.int8)

        st = surf_style[sname]
        surfs_out.append(dict(
            name=sname,
            nv=nv, nt=nt, ne=len(edges),
            tex=surf_tex_map[sname],
            metallic=st["metallic"],
            rough=st["rough"],
            unlit=st["unlit"],
            additive=st["additive"],
            tris=add_bytes(tris_ccw.tobytes()),
            edges=add_bytes(edges.tobytes()),
            uv=add_bytes(uv.tobytes()),
            pos=add_bytes(pos_q.tobytes()),
            nrm=add_bytes(nrm_q.tobytes()),
        ))
    return dict(nf=nf, nv=tot_v, nt=tot_t, surfaces=surfs_out)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>WEW CANNON · Quake 3D Weapon Studio</title>
<style>
  :root { --bg:#090d16; --panel:#111827; --border:#24324d; --acc:#38bdf8; --silver:#e2e8f0; --hot:#fb923c; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--silver); font-family:'Segoe UI',system-ui,sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
  header { padding:10px 18px; background:#0d1322; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .brand { display:flex; align-items:center; gap:12px; }
  .badge { background:linear-gradient(135deg,#cbd5e1,#64748b); color:#090d16; font-weight:900; font-size:11px; padding:3px 8px; border-radius:4px; letter-spacing:0.08em; }
  h1 { font-size:18px; font-weight:900; letter-spacing:0.06em; color:#f8fafc; }
  .tabs { display:flex; gap:6px; }
  button { background:#182235; color:#dbeafe; border:1px solid var(--border); border-radius:6px; padding:7px 13px; font-size:12.5px; font-weight:700; cursor:pointer; transition:0.15s; }
  button:hover { border-color:var(--acc); background:#1e2d47; }
  button.active { background:var(--acc); color:#06101e; border-color:var(--acc); }
  button.fire-btn { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-size:13.5px; padding:8px 18px; box-shadow:0 0 18px rgba(249,115,22,0.4); }
  button.fire-btn:active, button.fire-btn.charging { background:linear-gradient(135deg,#38bdf8,#ffffff); color:#06101e; box-shadow:0 0 26px rgba(56,189,248,0.85); }
  main { flex:1; display:grid; grid-template-columns:1fr 330px; min-height:0; }
  #vp-wrap { position:relative; background:radial-gradient(circle at 50% 42%,#17223b 0%,#070a12 78%); overflow:hidden; }
  canvas { width:100%; height:100%; display:block; }
  #crosshair { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); pointer-events:none; color:#4ade80; font-weight:900; font-size:20px; text-shadow:0 0 6px #000; }
  #charge-hud { position:absolute; left:50%; bottom:68px; transform:translateX(-50%); background:rgba(9,13,22,0.82); border:1px solid var(--border); border-radius:8px; padding:8px 16px; text-align:center; pointer-events:none; min-width:250px; }
  #charge-bar { height:9px; background:#1e293b; border-radius:5px; overflow:hidden; margin-top:5px; }
  #charge-fill { height:100%; width:0%; background:linear-gradient(90deg,#38bdf8,#facc15,#ef4444); transition:width 0.04s linear; }
  #scrubber-bar { position:absolute; left:14px; right:14px; bottom:12px; background:rgba(13,19,34,0.88); border:1px solid var(--border); border-radius:8px; padding:8px 14px; display:flex; align-items:center; gap:10px; }
  input[type=range] { flex:1; accent-color:var(--acc); }
  aside { background:var(--panel); border-left:1px solid var(--border); padding:14px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; font-size:12.5px; line-height:1.45; }
  .card { background:#0c1220; border:1px solid var(--border); border-radius:8px; padding:11px; }
  .card h3 { font-size:12px; text-transform:uppercase; letter-spacing:0.08em; color:var(--acc); margin-bottom:7px; }
  .kv { display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #162036; }
  .kv:last-child { border-bottom:none; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  code { color:#93c5fd; font-family:Consolas,monospace; font-size:11.5px; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">MIL-SPEC MD3 + STRICT MDL</span>
    <h1>XM-98 MILITARY "WEW CANNON"</h1>
  </div>
  <div class="tabs">
    <button id="tab-vm" class="active" onclick="setModel(0)">1 · 1st-Person WEW CANNON (48f)</button>
    <button id="tab-pk" onclick="setModel(1)">2 · World Pickup (`g_wewcannon`)</button>
  </div>
  <div class="row">
    <button id="btn-charge" class="fire-btn">HOLD TO CHARGE &amp; FIRE! (or Space)</button>
  </div>
</header>
<main>
  <div id="vp-wrap">
    <canvas id="gl"></canvas>
    <div id="crosshair">+</div>
    <div id="charge-hud">
      <div id="hud-label" style="font-weight:800;font-size:12px;letter-spacing:0.06em;">READY · HOLD SPACE OR FIRE BUTTON</div>
      <div id="charge-bar"><div id="charge-fill"></div></div>
    </div>
    <div id="scrubber-bar">
      <button id="btn-play" onclick="togglePlay()">Pause</button>
      <button onclick="triggerFullCycle()">Play Full Artillery Cycle</button>
      <input id="scrub" type="range" min="0" max="47" step="0.05" value="0">
      <span id="frame-lbl" style="min-width:125px;font-family:Consolas,monospace;font-size:12px;">f00 · idle1</span>
    </div>
  </div>
  <aside>
    <div class="card">
      <h3>Camera &amp; FOV Controls</h3>
      <div class="row" style="margin-bottom:8px;">
        <button id="btn-pov90" onclick="setPov(90)">Quake POV 90°</button>
        <button id="btn-pov111" class="active" onclick="setPov(111)">Bakersfield POV 111°</button>
        <button id="btn-orbit" onclick="setOrbit()">Free 3D Orbit</button>
      </div>
      <div class="row">
        <button id="btn-wire" onclick="toggleWire()">Wireframe: OFF</button>
      </div>
      <div style="margin-top:7px;color:#94a3b8;font-size:11.5px;">Drag mouse in Orbit mode to rotate; scroll wheel to zoom.</div>
    </div>
    <div class="card">
      <h3>WEW-TAC 98 CRT Websites</h3>
      <div class="row">
        <button id="crt-auto" class="active" onclick="setCrtSite(-1)">Auto-Browse</button>
        <button id="crt-0" onclick="setCrtSite(0)">goodwebsites.html</button>
        <button id="crt-1" onclick="setCrtSite(1)">zxc.cc</button>
        <button id="crt-2" onclick="setCrtSite(2)">biblefirst.com</button>
        <button id="crt-3" onclick="setCrtSite(3)">wxcs.com/rob</button>
      </div>
    </div>
    <div class="card">
      <h3>48-Frame Artillery Recoil Schedule</h3>
      <div class="kv"><span>Frames 0–15</span><code>idle1..16 (Disciplined Sway)</code></div>
      <div class="kv"><span>Frames 16–25</span><code>charge1..10 (Sear Cock &amp; +5.5° Flex)</code></div>
      <div class="kv"><span>Frames 26–29</span><code>blast1..4 (Side-Brake Jets &amp; -6.3u Stroke)</code></div>
      <div class="kv"><span>Frames 30–39</span><code>recoil1..10 (Hydropneumatic Return)</code></div>
      <div class="kv"><span>Frames 40–47</span><code>reload1..8 (Breech-Block Lock-In)</code></div>
    </div>
    <div class="card">
      <h3>100% Quake Engine Compatibility</h3>
      <div class="kv"><span>DarkPlaces / Q3</span><code>progs/v_wewcannon.md3</code></div>
      <div class="kv"><span>Wheelman Alias</span><code>progs/v_wcannon.md3</code></div>
      <div class="kv"><span>Vanilla 1996 MDL</span><code>progs/v_wewcannon.mdl</code></div>
      <div class="kv"><span>MDL Limits</span><code>&le;1024v / &le;2048t (IDPO v6)</code></div>
      <div class="kv"><span>MDL Skin</span><code>512&times;256 (&le;480) + _0.tga</code></div>
      <div class="kv"><span>Pickup / Proj</span><code>g_wewcannon (Proj Separate)</code></div>
    </div>
  </aside>
</main>
<script>
const PAYLOAD = /*__WEW_DATA__*/null;

async function DecompressB64Gz(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const w = ds.writable.getWriter();
  w.write(bin); w.close();
  const buf = await new Response(ds.readable).arrayBuffer();
  return buf;
}

let gl, prog, wireProg, arenaBuf;
let gpuModels = [], gpuTextures = [];
let curModelIdx = 0, povMode = true, fovDeg = 111, showWire = false;
let playing = true, animMode = 'idle', animFrame = 0.0;
let charging = false, chargeVal = 0.0;
let orbitAz = 2.35, orbitEl = 0.25, orbitDist = 36.0, dragging = false, lx = 0, ly = 0;
let crtPinSite = -1, crtClock = 0.0;

function setCrtSite(idx) {
  crtPinSite = idx;
  document.getElementById('crt-auto').classList.toggle('active', idx === -1);
  for (let k = 0; k < 4; k++) document.getElementById('crt-' + k).classList.toggle('active', idx === k);
}

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
uniform float uMetallic, uRough, uUnlit, uWirePass;
out vec4 fragColor;
void main() {
  if (uWirePass > 0.5) { fragColor = vec4(0.22, 0.78, 1.0, 0.55); return; }
  vec4 tx = texture(uTex, vUV);
  if (uUnlit > 0.5) { fragColor = tx; return; }
  vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
  vec3 V = normalize(uCamPos - vPos);
  vec3 L1 = normalize(vec3(-0.35, 0.55, 0.75));
  vec3 L2 = normalize(vec3(0.70, -0.45, 0.45));
  float d1 = max(dot(N, L1), 0.0);
  float d2 = max(dot(N, L2), 0.0);
  vec3 H1 = normalize(L1 + V);
  float spec = pow(max(dot(N, H1), 0.0), mix(18.0, 72.0, 1.0 - uRough)) * (0.35 + 0.95 * uMetallic);
  // Crisp studio horizon reflection boost for gleaming silver cannon!
  vec3 R = reflect(-V, N);
  float env = 0.55 + 0.45 * sin(R.z * 3.8 + 0.4);
  vec3 lit = tx.rgb * (0.34 + 0.72 * d1 + 0.28 * d2) + tx.rgb * uMetallic * 0.28 * env + vec3(0.92, 0.96, 1.0) * spec;
  fragColor = vec4(lit, tx.a);
}`;

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
    xx, yx, zx, 0,
    xy, yy, zy, 0,
    xz, yz, zz, 0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]),
    -(yx*eye[0]+yy*eye[1]+yz*eye[2]),
    -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}
function mat4TransScale(tx, ty, tz, sc) {
  return new Float32Array([sc,0,0,0, 0,sc,0,0, 0,0,sc,0, tx,ty,tz,1]);
}

async function init() {
  const canvas = document.getElementById('gl');
  gl = canvas.getContext('webgl2', { antialias: true });
  prog = compile(VS, FS);
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

  for (const m of PAYLOAD.models) {
    const surfs = m.surfaces.map(s => {
      const mkBuf = (slice, target) => {
        const b = gl.createBuffer();
        gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(arenaBuf, slice[0], slice[1]), gl.STATIC_DRAW);
        return b;
      };
      return {
        ...s,
        bPos: mkBuf(s.pos, gl.ARRAY_BUFFER),
        bNrm: mkBuf(s.nrm, gl.ARRAY_BUFFER),
        bUV:  mkBuf(s.uv,  gl.ARRAY_BUFFER),
        bTri: mkBuf(s.tris, gl.ELEMENT_ARRAY_BUFFER),
        bEdg: mkBuf(s.edges, gl.ELEMENT_ARRAY_BUFFER),
      };
    });
    gpuModels.push({ ...m, surfs });
  }

  setupControls(canvas);
  requestAnimationFrame(loop);
}

function setupControls(canvas) {
  const btnC = document.getElementById('btn-charge');
  const startCharge = () => {
    if (curModelIdx !== 0) setModel(0);
    if (!charging && animMode !== 'blast') {
      charging = true; chargeVal = 0.0; playing = true;
      btnC.classList.add('charging');
    }
  };
  const endCharge = () => {
    if (charging) {
      charging = false;
      btnC.classList.remove('charging');
      animMode = 'blast';
      animFrame = 26.0;
    }
  };
  btnC.addEventListener('mousedown', startCharge);
  window.addEventListener('mouseup', endCharge);
  window.addEventListener('keydown', e => { if (e.code === 'Space' && !e.repeat) { e.preventDefault(); startCharge(); } });
  window.addEventListener('keyup', e => { if (e.code === 'Space') { e.preventDefault(); endCharge(); } });

  document.getElementById('scrub').addEventListener('input', e => {
    playing = false;
    document.getElementById('btn-play').textContent = 'Play';
    animFrame = parseFloat(e.target.value);
  });

  canvas.addEventListener('mousedown', e => { if (!povMode || curModelIdx !== 0) { dragging = true; lx = e.clientX; ly = e.clientY; } });
  window.addEventListener('mousemove', e => {
    if (!dragging) return;
    orbitAz -= (e.clientX - lx) * 0.008;
    orbitEl = Math.max(-1.2, Math.min(1.2, orbitEl + (e.clientY - ly) * 0.008));
    lx = e.clientX; ly = e.clientY;
  });
  window.addEventListener('mouseup', () => dragging = false);
  canvas.addEventListener('wheel', e => { orbitDist = Math.max(12, Math.min(110, orbitDist + e.deltaY * 0.03)); });
}

function setModel(idx) {
  curModelIdx = idx;
  animFrame = 0; animMode = 'idle'; playing = true;
  ['tab-vm','tab-pk'].forEach((id, i) => document.getElementById(id).classList.toggle('active', i === idx));
  document.getElementById('scrub').max = Math.max(0, gpuModels[idx].nf - 1);
  document.getElementById('crosshair').style.display = (idx === 0 && povMode) ? 'block' : 'none';
}
function setPov(deg) {
  povMode = true; fovDeg = deg;
  document.getElementById('btn-pov90').classList.toggle('active', deg === 90);
  document.getElementById('btn-pov111').classList.toggle('active', deg === 111);
  document.getElementById('btn-orbit').classList.remove('active');
  document.getElementById('crosshair').style.display = (curModelIdx === 0) ? 'block' : 'none';
}
function setOrbit() {
  povMode = false;
  document.getElementById('btn-pov90').classList.remove('active');
  document.getElementById('btn-pov111').classList.remove('active');
  document.getElementById('btn-orbit').classList.add('active');
  document.getElementById('crosshair').style.display = 'none';
}
function toggleWire() {
  showWire = !showWire;
  document.getElementById('btn-wire').textContent = 'Wireframe: ' + (showWire ? 'ON' : 'OFF');
}
function togglePlay() {
  playing = !playing;
  document.getElementById('btn-play').textContent = playing ? 'Pause' : 'Play';
}
function triggerFullCycle() {
  if (curModelIdx !== 0) setModel(0);
  playing = true; charging = false; animMode = 'full'; animFrame = 16.0;
  document.getElementById('btn-play').textContent = 'Pause';
}

function drawModel(m, fFloat, modelMat, vpMat, camPos) {
  const nf = m.nf;
  const f0 = Math.max(0, Math.min(nf - 1, Math.floor(fFloat)));
  const f1 = (f0 + 1 < nf) ? f0 + 1 : 0;
  const noLerp = (m === gpuModels[0] && (f0 === 15 || f0 === 29 || f0 === 30));
  const lerp = noLerp ? 0.0 : (fFloat - f0);
  const mvp = mat4Mul(vpMat, modelMat);

  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mvp);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uModel'), false, modelMat);
  gl.uniform3fv(gl.getUniformLocation(prog, 'uCamPos'), camPos);
  gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);

  for (const s of m.surfs) {
    if (s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE); gl.depthMask(false);
    } else {
      gl.disable(gl.BLEND); gl.depthMask(true);
    }
    gl.activeTexture(gl.TEXTURE0);
    let texIdx = s.tex;
    if (s.name === 'crt_screen') {
      const subStep = Math.floor(crtClock * 1.2) % 4;
      const crtFrame = (crtPinSite >= 0) ? (crtPinSite * 4 + subStep) : (Math.floor(crtClock * 1.1) % 16);
      texIdx = PAYLOAD.crtTexBase + crtFrame;
    }
    gl.bindTexture(gl.TEXTURE_2D, gpuTextures[texIdx]);
    gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uMetallic'), s.metallic);
    gl.uniform1f(gl.getUniformLocation(prog, 'uRough'), s.rough);
    gl.uniform1f(gl.getUniformLocation(prog, 'uUnlit'), s.unlit ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 0.0);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bPos);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.SHORT, false, 0, f0 * s.nv * 6);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 3, gl.SHORT, false, 0, f1 * s.nv * 6);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bNrm);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.BYTE, false, 0, f0 * s.nv * 3);
    gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.BYTE, false, 0, f1 * s.nv * 3);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bUV);
    gl.enableVertexAttribArray(4); gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bTri);
    gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);

    if (showWire && !s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 1.0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bEdg);
      gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
      gl.disable(gl.BLEND);
    }
  }
  gl.depthMask(true); gl.disable(gl.BLEND);
}

let lastT = performance.now();
function loop(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000.0);
  lastT = now;
  crtClock += dt;

  const canvas = document.getElementById('gl');
  const dpr = window.devicePixelRatio || 1;
  const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.04, 0.06, 0.10, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const m = gpuModels[curModelIdx];
  const prevF = animFrame;

  if (curModelIdx === 0) {
    if (charging) {
      chargeVal = Math.min(1.0, chargeVal + dt / 1.4);
      animFrame = 16.0 + chargeVal * 9.0;
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      document.getElementById('hud-label').textContent = chargeVal >= 0.99 ? 'CHAMBER AT MAX PRESSURE! RELEASE TO FIRE!!' : `PRESSURIZING CHAMBER... ${(chargeVal*100)|0}%`;
    } else if (playing) {
      if (animMode === 'blast') {
        animFrame += dt * 22.0;
        if (animFrame >= 47.95) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else if (animMode === 'full') {
        animFrame += dt * (animFrame < 26.0 ? 9.5 : 22.0);
        chargeVal = animFrame < 26.0 ? (animFrame - 16.0) / 10.0 : Math.max(0, 1.0 - (animFrame - 26.0) * 0.2);
        if (animFrame >= 47.95) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else {
        animFrame = (animFrame + dt * 10.0) % 16.0;
        chargeVal = Math.max(0.0, chargeVal - dt * 2.5);
      }
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      if (animMode === 'idle') document.getElementById('hud-label').textContent = 'READY · HOLD SPACE OR FIRE BUTTON';
      else document.getElementById('hud-label').textContent = animFrame < 30 ? '155MM MUZZLE-BRAKE BLAST!!' : (animFrame < 40 ? 'HYDROPNEUMATIC RETURN-TO-BATTERY' : 'BREECH-BLOCK AUTO-LOCK');
    }
  } else if (playing) {
    animFrame = (animFrame + dt * 12.0) % Math.max(1, m.nf);
  }

  document.getElementById('scrub').value = animFrame;
  const fi = Math.floor(animFrame) % m.nf;
  const fname = PAYLOAD.frameNames[curModelIdx][fi] || ('f' + fi);
  document.getElementById('frame-lbl').textContent = `f${String(fi).padStart(2,'0')} · ${fname}`;

  const asp = w / Math.max(1, h);
  let camPos, viewMat, projMat;
  if (curModelIdx === 0 && povMode) {
    // Convert Quake horizontal FOV (at 4:3) to vertical FOV!
    const fovX = fovDeg * Math.PI / 180.0;
    const fovY = 2.0 * Math.atan(Math.tan(fovX * 0.5) / asp);
    projMat = mat4Persp(fovY, asp, 1.0, 900.0);
    camPos = [0, 0, 0];
    viewMat = mat4LookAt(camPos, [20, 0, 0], [0, 0, 1]);
  } else {
    projMat = mat4Persp(50.0 * Math.PI / 180.0, asp, 1.0, 900.0);
    const ctr = curModelIdx === 0 ? [20, -5, -3] : (curModelIdx === 1 ? [0, 0, 11] : [-2, 0, 0]);
    camPos = [
      ctr[0] + orbitDist * Math.cos(orbitEl) * Math.cos(orbitAz),
      ctr[1] + orbitDist * Math.cos(orbitEl) * Math.sin(orbitAz),
      ctr[2] + orbitDist * Math.sin(orbitEl)
    ];
    viewMat = mat4LookAt(camPos, ctr, [0, 0, 1]);
  }
  const vpMat = mat4Mul(projMat, viewMat);
  const ident = mat4TransScale(0, 0, 0, 1.0);
  drawModel(m, animFrame, ident, vpMat, camPos);

  requestAnimationFrame(loop);
}
init();
</script>
</body>
</html>
"""


def main():
    tex_files = ["wew_silver.png", "wew_hand.png", "wew_core.png", "wew_fx.png"] + [f"wew_crt_{i:02d}.png" for i in range(16)]
    tex_list = [encode_tex(os.path.join(TEX_DIR, fn)) for fn in tex_files]
    tmap = {fn: i for i, fn in enumerate(tex_files)}

    surf_tex = {
        "cannon_silver": tmap["wew_silver.png"],
        "ranger_hands":  tmap["wew_hand.png"],
        "cannon_core":   tmap["wew_core.png"],
        "crt_screen":    tmap["wew_crt_00.png"],
        "cannon_fx":     tmap["wew_fx.png"],
    }
    surf_style = {
        "cannon_silver": dict(metallic=0.92, rough=0.18, unlit=False, additive=False),
        "ranger_hands":  dict(metallic=0.22, rough=0.52, unlit=False, additive=False),
        "cannon_core":   dict(metallic=0.10, rough=0.30, unlit=True,  additive=False),
        "crt_screen":    dict(metallic=0.05, rough=0.20, unlit=True,  additive=False),
        "cannon_fx":     dict(metallic=0.00, rough=0.50, unlit=True,  additive=True),
    }

    arena = bytearray()
    m_vm = pack_md3(os.path.join(STAGE_DIR, "v_wewcannon.md3"), arena, surf_tex, surf_style)
    m_pk = pack_md3(os.path.join(STAGE_DIR, "g_wewcannon.md3"), arena, surf_tex, surf_style)

    meta = json.loads(open(os.path.join(OUT_ROOT, "wew_meta.json"), encoding="utf-8").read())
    gz = gzip.compress(bytes(arena), compresslevel=9)
    payload = dict(
        binGz=base64.b64encode(gz).decode("ascii"),
        textures=tex_list,
        crtTexBase=tmap["wew_crt_00.png"],
        models=[m_vm, m_pk],
        frameNames=[meta["frameNames"], ["pickup1"]],
    )
    html = HTML_TEMPLATE.replace("/*__WEW_DATA__*/null", json.dumps(payload, separators=(",", ":")))
    open(HTML_OUT, "w", encoding="utf-8").write(html)
    print(f"[HTML OK] Wrote {HTML_OUT} ({os.path.getsize(HTML_OUT) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
