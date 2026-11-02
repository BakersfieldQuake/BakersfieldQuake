r"""Builds the standalone offline WebGL2 3D Explosion Studio viewer:
  g:\Quake\Combat\BakersfieldQuake\megaman_explode.html

Embeds all 31 fractured 3D rigid bodies (2 intact wheels, stainless steel central bar,
rear Delrin cap, 2 snapped cross-axles, 24 Voronoi shrapnel pieces, and 3D core starburst),
271-frame 60 FPS physics TRS tracks, procedural floor rolling trails, impact sparks,
camera tracking presets (Overview, Blast Close-Up, Track Left Wheel, Track Right Wheel,
Track Steel Bar), slow-motion speed controls, and frame-by-frame scrubber.
"""
import base64
import io
import json
import os
import zlib
import numpy as np
from PIL import Image

from mm_explode_sim import build_fracture_atlas, build_blast_starburst_mesh, part_world_aligned_mesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
PARTS_JSON = os.path.join(SCRIPT_DIR, "out", "mm_fractured_parts.json")
SIM_NPZ = os.path.join(SCRIPT_DIR, "out", "mm_explode_sim_cache.npz")
SRC_GLB = r"g:\Downloads\Telegram Desktop\megaman1.glb"
OUT_HTML = os.path.join(MOD_DIR, "megaman_explode.html")


def b64_f32(arr):
    return base64.b64encode(np.asarray(arr, dtype=np.float32).tobytes()).decode("ascii")


def b64_u16(arr):
    return base64.b64encode(np.asarray(arr, dtype=np.uint16).tobytes()).decode("ascii")


def main():
    with open(PARTS_JSON, "r", encoding="utf-8") as f:
        parts = json.load(f)
    sim = np.load(SIM_NPZ, allow_pickle=True)
    fps = int(np.asarray(sim["fps"]).reshape(-1)[0])
    n_frames = int(np.asarray(sim["n_frames"]).reshape(-1)[0])
    boom_frame = int(np.asarray(sim["boom_frame"]).reshape(-1)[0])
    sparks = json.loads(str(np.asarray(sim["sparks_json"]).reshape(-1)[0]))

    # Encode 1024x1024 crisp JPEG/PNG atlas for fast inline load (~180 KB JPEG q=90)
    atlas_im = build_fracture_atlas(SRC_GLB).resize((1024, 1024), Image.Resampling.LANCZOS)
    tex_buf = io.BytesIO()
    atlas_im.save(tex_buf, format="JPEG", quality=91, optimize=True)
    tex_uri = "data:image/jpeg;base64," + base64.b64encode(tex_buf.getvalue()).decode("ascii")

    # Pack meshes + animation tracks (convert Quake X_fwd, Y_left, Z_up -> Viewer X_right=-Y_q, Y_up=Z_q, Z_fwd=X_q in meters)
    # Wait: even cyclic permutation (X_v, Y_v, Z_v) = (Y_q, Z_q, X_q) / 22.0 has det = +1 (matches megaman_explode.glb 1:1!)
    S = 1.0 / 22.0
    blast_mesh = build_blast_starburst_mesh()

    ordered_names = (
        ["wheel_left", "wheel_right", "main_bar", "rear_cap", "axle_left", "axle_right"]
        + [k for k in sorted(parts.keys()) if k.startswith("frag_")]
        + ["blast_flash"]
    )

    js_parts = []
    for name in ordered_names:
        if name == "blast_flash":
            vw = np.array(blast_mesh["verts"], dtype=np.float64)
            nw = np.array(blast_mesh["norms"], dtype=np.float64)
            uvs = np.array(blast_mesh["uvs"], dtype=np.float32)
            tris = np.array(blast_mesh["tris"], dtype=np.uint16).reshape(-1)
            cat = "flash"
            pmat = "flash"
        else:
            p = parts[name]
            vw, nw = part_world_aligned_mesh(p)
            uvs = np.array(p["uvs"], dtype=np.float32)
            tris = np.array(p["tris"], dtype=np.uint16).reshape(-1)
            pmat = p.get("phys_mat", "metal")
            if name in ("wheel_left", "wheel_right"):
                cat = "wheel"
            elif name == "main_bar":
                cat = "bar"
            elif name in ("rear_cap", "axle_left", "axle_right"):
                cat = "hardware"
            else:
                cat = "frag"

        pos_g = np.column_stack([vw[:, 1], vw[:, 2], vw[:, 0]]).astype(np.float32) * S
        nrm_g = np.column_stack([nw[:, 1], nw[:, 2], nw[:, 0]]).astype(np.float32)
        nrm_g /= np.maximum(np.linalg.norm(nrm_g, axis=1, keepdims=True), 1e-8)

        # Interleave pos(3) + nrm(3) + uv(2) = 8 floats/vert
        interleaved = np.hstack([pos_g, nrm_g, uvs]).astype(np.float32)

        tr_p = sim[f"pos_{name}"]
        tr_r = sim[f"rot_{name}"]
        tr_s = sim[f"scl_{name}"]

        ap = np.column_stack([tr_p[:, 1], tr_p[:, 2], tr_p[:, 0]]).astype(np.float32) * S
        ar = np.column_stack([tr_r[:, 1], tr_r[:, 2], tr_r[:, 0], tr_r[:, 3]]).astype(np.float32)
        ar /= np.maximum(np.linalg.norm(ar, axis=1, keepdims=True), 1e-8)
        asc = np.column_stack([tr_s[:, 1], tr_s[:, 2], tr_s[:, 0]]).astype(np.float32)

        # Interleave TRS per frame: pos(3) + quat(4) + scl(3) = 10 floats/frame
        trs = np.hstack([ap, ar, asc]).astype(np.float32)

        js_parts.append({
            "name": name,
            "cat": cat,
            "mat": pmat,
            "nv": int(len(pos_g)),
            "ni": int(len(tris)),
            "vb": b64_f32(interleaved),
            "ib": b64_u16(tris),
            "trs": b64_f32(trs),
        })

    # Convert spark positions to viewer coords (Y_q, Z_q, X_q) * S
    js_sparks = []
    for sp in sparks:
        px, py, pz = sp["pos"]
        js_sparks.append({
            "t": sp["t"],
            "p": [round(py * S, 3), round(pz * S, 3), round(px * S, 3)],
            "i": round(float(sp["intensity"]), 2),
            "k": sp["kind"],
        })

    scene_payload = json.dumps({
        "fps": fps,
        "nFrames": n_frames,
        "boomFrame": boom_frame,
        "tex": tex_uri,
        "parts": js_parts,
        "sparks": js_sparks,
    }, separators=(",", ":"))

    html = HTML_TEMPLATE.replace("__SCENE_DATA_JSON__", scene_payload)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote standalone WebGL2 viewer: {OUT_HTML} ({os.path.getsize(OUT_HTML) / 1e6:.2f} MB)")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mega Man · 3D Explosion & Rolling Wreckage Studio (BakersfieldQuake)</title>
<style>
:root {
  --bg: #0d1016;
  --panel: rgba(18, 22, 31, 0.86);
  --panel-2: rgba(26, 31, 44, 0.92);
  --line: rgba(255, 255, 255, 0.11);
  --line-hi: rgba(255, 180, 84, 0.6);
  --text: #eef1f7;
  --muted: #98a2b8;
  --accent: #ffb454;
  --accent-2: #ff6b35;
  --cyan: #38bdf8;
  --green: #4ade80;
  color-scheme: dark;
}
* { box-sizing: border-box; user-select: none; }
html, body {
  margin: 0; padding: 0; width: 100%; height: 100%;
  overflow: hidden; background: var(--bg); color: var(--text);
  font: 13.5px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
canvas#gl {
  position: fixed; inset: 0; width: 100%; height: 100%; display: block; cursor: grab;
}
canvas#gl:active { cursor: grabbing; }

.hud-top {
  position: fixed; top: 14px; left: 16px; right: 16px;
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 12px; pointer-events: none; z-index: 10;
}
.title-card, .stats-card, .ctrl-dock {
  pointer-events: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 10px 32px rgba(0,0,0,0.45);
}
.title-card { padding: 12px 16px; max-width: 540px; }
.kicker {
  color: var(--accent); font-size: 11px; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase; margin-bottom: 2px;
}
h1 { margin: 0; font-size: 19px; font-weight: 700; letter-spacing: -0.01em; }
.sub { margin: 4px 0 0; color: var(--muted); font-size: 12.5px; }

.stats-card {
  padding: 10px 14px; font-size: 12px; color: var(--muted);
  display: flex; flex-direction: column; gap: 4px; align-items: flex-end;
}
.stats-card b { color: var(--text); font-family: ui-monospace, Consolas, monospace; }
.badge-row { display: flex; gap: 6px; margin-top: 2px; flex-wrap: wrap; justify-content: flex-end; }
.pill-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 999px;
  border: 1px solid var(--line); background: rgba(255,255,255,0.05); color: var(--text);
}
.pill-badge.live { border-color: rgba(74,222,128,0.45); color: var(--green); background: rgba(74,222,128,0.1); }

.ctrl-dock {
  position: fixed; left: 16px; right: 16px; bottom: 14px;
  max-width: 1180px; margin: 0 auto; padding: 12px 16px;
  display: flex; flex-direction: column; gap: 10px; z-index: 10;
}
.scrub-row { display: flex; align-items: center; gap: 10px; }
button.btn {
  background: rgba(255,255,255,0.06); color: var(--text);
  border: 1px solid var(--line); border-radius: 8px;
  padding: 6px 11px; font: inherit; font-size: 12.5px; font-weight: 600;
  cursor: pointer; transition: all 0.14s ease; white-space: nowrap;
}
button.btn:hover { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.24); }
button.btn.primary {
  background: var(--accent); color: #1b1104; border-color: var(--accent); min-width: 78px;
}
button.btn.primary:hover { filter: brightness(1.08); }
button.btn.active {
  background: rgba(255, 180, 84, 0.18); color: var(--accent); border-color: var(--line-hi);
}

input[type=range]#timeline {
  flex: 1; accent-color: var(--accent); height: 6px; cursor: pointer;
}
.time-readout {
  font-family: ui-monospace, Consolas, monospace; font-size: 12.5px;
  min-width: 152px; text-align: right; color: var(--text);
}
.bar-groups {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px 14px;
}
.grp { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.grp-label {
  color: var(--muted); font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em; margin-right: 2px;
}
.legend-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px;
}
@media (max-width: 780px) {
  .stats-card { display: none; }
  .time-readout { min-width: 110px; font-size: 11.5px; }
}
</style>
</head>
<body>
<canvas id="gl"></canvas>

<div class="hud-top">
  <div class="title-card">
    <div class="kicker">BakersfieldQuake · 3D Rigid-Body &amp; Gyroscopic Fracture Asset</div>
    <h1>Mega Man Contraption — Detonation &amp; Rolling Wreckage</h1>
    <p class="sub">
      31 watertight meshes carved from <code>megaman1.glb</code> · 480 Hz physics · Banked gyroscopic wheel curves + Euler's-disk wobble · Tumbling &amp; cylinder-rolling stainless steel bar · 24 Voronoi shrapnel pieces.
    </p>
  </div>
  <div class="stats-card">
    <div>Asset: <b>megaman_explode.glb</b> + <b>progs/mm_*.md3</b></div>
    <div>Phase: <b id="phaseLabel">Pre-Detonation Overdrive</b></div>
    <div class="badge-row">
      <span class="pill-badge live">31 Rigid Bodies</span>
      <span class="pill-badge">271 Frames @ 60 FPS</span>
      <span class="pill-badge">Drag: Orbit · Right-Drag: Pan · Wheel: Zoom</span>
    </div>
  </div>
</div>

<div class="ctrl-dock">
  <div class="scrub-row">
    <button class="btn primary" id="btnPlay">Pause</button>
    <button class="btn" id="btnRestart" title="Restart (R)">&#8634; Replay</button>
    <button class="btn" id="btnPrev" title="Previous Frame">&lsaquo;</button>
    <input type="range" id="timeline" min="0" max="270" step="0.1" value="0">
    <button class="btn" id="btnNext" title="Next Frame">&rsaquo;</button>
    <div class="time-readout" id="timeReadout">0.00s · F000/270</div>
  </div>

  <div class="bar-groups">
    <div class="grp" id="camGroup">
      <span class="grp-label">Camera:</span>
      <button class="btn active" data-cam="overview">Arena Overview</button>
      <button class="btn" data-cam="blast">Blast Close-Up</button>
      <button class="btn" data-cam="wheel_left"><span class="legend-dot" style="background:#38bdf8"></span>Left Wheel</button>
      <button class="btn" data-cam="wheel_right"><span class="legend-dot" style="background:#fb7185"></span>Right Wheel</button>
      <button class="btn" data-cam="main_bar"><span class="legend-dot" style="background:#fbbf24"></span>Steel Bar</button>
    </div>

    <div class="grp" id="speedGroup">
      <span class="grp-label">Speed:</span>
      <button class="btn" data-spd="0.1">0.1&times;</button>
      <button class="btn" data-spd="0.25">0.25&times;</button>
      <button class="btn" data-spd="0.5">0.5&times;</button>
      <button class="btn active" data-spd="1.0">1.0&times;</button>
    </div>

    <div class="grp">
      <span class="grp-label">Inspect:</span>
      <button class="btn active" id="btnTrails">Floor Trails</button>
      <button class="btn" id="btnHighlightHero">Spotlight Wheels &amp; Bar</button>
      <button class="btn" id="btnSparks">FX Sparks: ON</button>
    </div>
  </div>
</div>

<script>
const SCENE = __SCENE_DATA_JSON__;

function b64ToF32(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Float32Array(bytes.buffer);
}
function b64ToU16(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Uint16Array(bytes.buffer);
}

// Minimal fast Matrix4 / Quaternion math
function mat4Perspective(out, fovy, aspect, near, far) {
  const f = 1.0 / Math.tan(fovy * 0.5), nf = 1.0 / (near - far);
  out.fill(0);
  out[0] = f / aspect; out[5] = f; out[10] = (far + near) * nf; out[11] = -1;
  out[14] = 2 * far * near * nf;
  return out;
}
function mat4LookAt(out, eye, ctr, up) {
  let zx = eye[0] - ctr[0], zy = eye[1] - ctr[1], zz = eye[2] - ctr[2];
  let len = Math.hypot(zx, zy, zz) || 1; zx /= len; zy /= len; zz /= len;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  len = Math.hypot(xx, xy, xz) || 1; xx /= len; xy /= len; xz /= len;
  let yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  out[0]=xx; out[1]=yx; out[2]=zx; out[3]=0;
  out[4]=xy; out[5]=yy; out[6]=zy; out[7]=0;
  out[8]=xz; out[9]=yz; out[10]=zz; out[11]=0;
  out[12]=-(xx*eye[0]+xy*eye[1]+xz*eye[2]);
  out[13]=-(yx*eye[0]+yy*eye[1]+yz*eye[2]);
  out[14]=-(zx*eye[0]+zy*eye[1]+zz*eye[2]);
  out[15]=1;
  return out;
}
function mat4Mul(out, a, b) {
  const r = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let rw = 0; rw < 4; rw++) {
      r[c*4+rw] = a[0*4+rw]*b[c*4+0] + a[1*4+rw]*b[c*4+1] + a[2*4+rw]*b[c*4+2] + a[3*4+rw]*b[c*4+3];
    }
  }
  out.set(r);
  return out;
}
function mat4FromTRS(out, tx, ty, tz, qx, qy, qz, qw, sx, sy, sz) {
  const x2 = qx+qx, y2 = qy+qy, z2 = qz+qz;
  const xx = qx*x2, xy = qx*y2, xz = qx*z2;
  const yy = qy*y2, yz = qy*z2, zz = qz*z2;
  const wx = qw*x2, wy = qw*y2, wz = qw*z2;
  out[0] = (1 - (yy + zz)) * sx;
  out[1] = (xy + wz) * sx;
  out[2] = (xz - wy) * sx;
  out[3] = 0;
  out[4] = (xy - wz) * sy;
  out[5] = (1 - (xx + zz)) * sy;
  out[6] = (yz + wx) * sy;
  out[7] = 0;
  out[8] = (xz + wy) * sz;
  out[9] = (yz - wx) * sz;
  out[10] = (1 - (xx + yy)) * sz;
  out[11] = 0;
  out[12] = tx; out[13] = ty; out[14] = tz; out[15] = 1;
  return out;
}
function slerpQuat(out, a, b, t) {
  let ax=a[0], ay=a[1], az=a[2], aw=a[3];
  let bx=b[0], by=b[1], bz=b[2], bw=b[3];
  let cosom = ax*bx + ay*by + az*bz + aw*bw;
  if (cosom < 0) { cosom = -cosom; bx=-bx; by=-by; bz=-bz; bw=-bw; }
  let s0 = 1 - t, s1 = t;
  if (1 - cosom > 1e-5) {
    const om = Math.acos(Math.min(1, cosom)), sinom = Math.sin(om);
    s0 = Math.sin((1 - t) * om) / sinom;
    s1 = Math.sin(t * om) / sinom;
  }
  let rx = s0*ax + s1*bx, ry = s0*ay + s1*by, rz = s0*az + s1*bz, rw = s0*aw + s1*bw;
  const n = Math.hypot(rx, ry, rz, rw) || 1;
  out[0]=rx/n; out[1]=ry/n; out[2]=rz/n; out[3]=rw/n;
}

const canvas = document.getElementById("gl");
const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, preserveDrawingBuffer: true });
if (!gl) alert("WebGL2 is required to view this 3D scene.");

function compileProg(vsSrc, fsSrc) {
  const vs = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vs, vsSrc); gl.compileShader(vs);
  if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(vs));
  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fs, fsSrc); gl.compileShader(fs);
  if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(fs));
  const p = gl.createProgram();
  gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
}

// 1. Main Lit PBR-Style Part Shader + Planar Shadow Pass Support
const meshProg = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;
uniform mat4 uVP;
uniform mat4 uModel;
uniform int uShadowPass;
out vec3 vWorldPos;
out vec3 vNrm;
out vec2 vUV;
void main() {
  vec4 wp = uModel * vec4(aPos, 1.0);
  if (uShadowPass == 1) {
    vec3 L = normalize(vec3(0.42, 1.15, 0.35));
    float t = max(0.0, wp.y) / L.y;
    vec3 sp = vec3(wp.x - L.x * t, 0.003, wp.z - L.z * t);
    vWorldPos = sp;
    vNrm = vec3(0.0, 1.0, 0.0);
    vUV = aUV;
    gl_Position = uVP * vec4(sp, 1.0);
  } else {
    vWorldPos = wp.xyz;
    vNrm = mat3(uModel) * aNrm;
    vUV = aUV;
    gl_Position = uVP * wp;
  }
}`, `#version 300 es
precision highp float;
precision highp int;
in vec3 vWorldPos;
in vec3 vNrm;
in vec2 vUV;
uniform sampler2D uTex;
uniform vec3 uCamPos;
uniform float uBlastGlow;
uniform vec3 uBlastPos;
uniform int uIsFlash;
uniform int uShadowPass;
uniform float uDimAlpha;
uniform int uMatType; // 0=metal/chrome, 1=wheel/rubber, 2=rim
out vec4 fragColor;
void main() {
  if (uShadowPass == 1) {
    fragColor = vec4(0.02, 0.03, 0.05, 0.34 * uDimAlpha);
    return;
  }
  if (uIsFlash == 1) {
    float r = length(vWorldPos - uBlastPos);
    vec3 col = mix(vec3(1.0, 0.97, 0.82), vec3(1.0, 0.45, 0.08), clamp(r * 1.4, 0.0, 1.0));
    fragColor = vec4(col * 1.65, 0.92);
    return;
  }
  vec3 base = texture(uTex, vUV).rgb;
  vec3 N = normalize(vNrm);
  vec3 V = normalize(uCamPos - vWorldPos);
  vec3 L1 = normalize(vec3(0.45, 0.82, 0.38));
  vec3 L2 = normalize(vec3(-0.62, 0.45, -0.58));

  // Detect chrome/steel vs dark rubber directly from texel brightness & saturation for crisp reflections
  float lum = dot(base, vec3(0.299, 0.587, 0.114));
  float metalness = (uMatType == 0 && lum > 0.32) ? 0.72 : 0.08;
  float shininess = (metalness > 0.4) ? 72.0 : ((lum > 0.65) ? 42.0 : 16.0);
  float specStr   = (metalness > 0.4) ? 0.85 : ((lum > 0.65) ? 0.38 : 0.14);

  float ndl1 = max(dot(N, L1), 0.0);
  float ndl2 = max(dot(N, L2), 0.0);
  vec3 H1 = normalize(L1 + V);
  float spec = pow(max(dot(N, H1), 0.0), shininess) * specStr;

  // Hemisphere sky/ground ambient + rim Fresnel
  vec3 hemi = mix(vec3(0.16, 0.18, 0.23), vec3(0.44, 0.48, 0.56), N.y * 0.5 + 0.5);
  float rim = pow(1.0 - max(dot(N, V), 0.0), 3.2) * 0.22;

  // Dynamic orange point light from detonation flash
  vec3 dB = uBlastPos - vWorldPos;
  float distB = length(dB) + 0.15;
  vec3 blastLight = vec3(1.0, 0.58, 0.18) * (uBlastGlow * max(dot(N, dB / distB), 0.0) / (distB * distB));

  vec3 lit = base * (hemi + ndl1 * vec3(1.02, 0.98, 0.92) + ndl2 * vec3(0.32, 0.40, 0.55) + blastLight)
           + vec3(spec) + rim * vec3(0.65, 0.78, 1.0);

  if (uDimAlpha < 0.99) {
    lit *= 0.35;
  }
  fragColor = vec4(pow(max(lit, 0.0), vec3(0.95)), uDimAlpha);
}`);

// 2. Arena Line / Trail / Spark Shader
const lineProg = compileProg(`#version 300 es
precision highp float;
precision highp int;
layout(location=0) in vec3 aPos;
layout(location=1) in vec4 aCol;
uniform mat4 uVP;
out vec4 vCol;
void main() {
  vCol = aCol;
  gl_Position = uVP * vec4(aPos, 1.0);
  gl_PointSize = 5.0;
}`, `#version 300 es
precision highp float;
precision highp int;
in vec4 vCol;
out vec4 fragColor;
void main() {
  fragColor = vCol;
}`);

// Upload shared atlas texture
const glTex = gl.createTexture();
gl.bindTexture(gl.TEXTURE_2D, glTex);
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([180,180,190,255]));
const img = new Image();
img.onload = () => {
  gl.bindTexture(gl.TEXTURE_2D, glTex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
};
img.src = SCENE.tex;

// Upload part VAOs & decode TRS tracks
const partMap = {};
const partsGPU = SCENE.parts.map(p => {
  const vb = b64ToF32(p.vb);
  const ib = b64ToU16(p.ib);
  const trs = b64ToF32(p.trs);
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);

  const vbo = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
  gl.bufferData(gl.ARRAY_BUFFER, vb, gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);

  const ebo = gl.createBuffer();
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ebo);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, ib, gl.STATIC_DRAW);
  gl.bindVertexArray(null);

  const matCode = (p.cat === "wheel" || p.mat === "rubber") ? 1 : (p.mat === "rim" ? 2 : 0);
  const obj = { name: p.name, cat: p.cat, matCode, ni: p.ni, vao, trs };
  partMap[p.name] = obj;
  return obj;
});

function samplePartTRS(part, frameFloat, outPos, outQuat, outScl) {
  const maxF = SCENE.nFrames - 1;
  const f = Math.max(0, Math.min(maxF, frameFloat));
  const i0 = Math.floor(f), i1 = Math.min(maxF, i0 + 1);
  const t = f - i0;
  const trs = part.trs;
  const b0 = i0 * 10, b1 = i1 * 10;
  outPos[0] = trs[b0]   + (trs[b1]   - trs[b0])   * t;
  outPos[1] = trs[b0+1] + (trs[b1+1] - trs[b0+1]) * t;
  outPos[2] = trs[b0+2] + (trs[b1+2] - trs[b0+2]) * t;
  slerpQuat(outQuat, trs.subarray(b0+3, b0+7), trs.subarray(b1+3, b1+7), t);
  if (part.cat === "frag" && i0 < SCENE.boomFrame) {
    outScl[0] = trs[b0+7]; outScl[1] = trs[b0+8]; outScl[2] = trs[b0+9];
  } else {
    outScl[0] = trs[b0+7] + (trs[b1+7] - trs[b0+7]) * t;
    outScl[1] = trs[b0+8] + (trs[b1+8] - trs[b0+8]) * t;
    outScl[2] = trs[b0+9] + (trs[b1+9] - trs[b0+9]) * t;
  }
}

// Build static floor grid + 1m..5m radar circles
const gridVerts = [];
function pushLine(x0,y0,z0, x1,y1,z1, r,g,b,a) {
  gridVerts.push(x0,y0,z0, r,g,b,a, x1,y1,z1, r,g,b,a);
}
for (let i = -8; i <= 8; i++) {
  const al = (i === 0) ? 0.24 : 0.08;
  pushLine(i, 0, -8, i, 0, 8, 0.65, 0.72, 0.88, al);
  pushLine(-8, 0, i, 8, 0, i, 0.65, 0.72, 0.88, al);
}
for (const rad of [1.5, 3.0, 4.5, 6.0]) {
  const segs = 72;
  for (let s = 0; s < segs; s++) {
    const a0 = (s / segs) * Math.PI * 2, a1 = ((s + 1) / segs) * Math.PI * 2;
    const hi = (rad === 3.0) ? 0.16 : 0.08;
    pushLine(Math.cos(a0)*rad, 0.001, Math.sin(a0)*rad, Math.cos(a1)*rad, 0.001, Math.sin(a1)*rad, 1.0, 0.72, 0.35, hi);
  }
}
const gridVao = gl.createVertexArray();
gl.bindVertexArray(gridVao);
const gridVbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, gridVbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(gridVerts), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 28, 12);
const gridCount = gridVerts.length / 7;

// Dynamic VBO for trails + sparks
const dynVao = gl.createVertexArray();
gl.bindVertexArray(dynVao);
const dynVbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, dynVbo);
gl.bufferData(gl.ARRAY_BUFFER, 65536 * 4, gl.DYNAMIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 28, 12);
gl.bindVertexArray(null);

// Pre-generate deterministic ballistic spark streaks from SCENE.sparks
const sparkParticles = [];
let seed = 1337;
function rand01() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
for (const ev of SCENE.sparks) {
  const count = ev.k === "detonation" ? 68 : (ev.k === "sparks" ? 14 : 8);
  for (let k = 0; k < count; k++) {
    const az = rand01() * Math.PI * 2;
    const spd = (ev.k === "detonation" ? (2.5 + rand01() * 6.5) : (1.2 + rand01() * 3.4)) * Math.sqrt(ev.i);
    const vy = (ev.k === "detonation" ? (1.8 + rand01() * 5.2) : (0.9 + rand01() * 2.5));
    sparkParticles.push({
      t0: ev.t,
      life: ev.k === "rubber" ? (0.22 + rand01() * 0.2) : (0.32 + rand01() * 0.42),
      p0: ev.p,
      v: [Math.cos(az) * spd, vy, Math.sin(az) * spd],
      rubber: ev.k === "rubber",
    });
  }
}

// Playback & Camera State
let playing = true;
const urlT = parseFloat(new URLSearchParams(location.search).get("t"));
let curFrame = Number.isFinite(urlT) ? Math.max(0, Math.min(SCENE.nFrames - 1, urlT * SCENE.fps)) : 0.0;
let speed = 1.0;
let camMode = "overview";
let showTrails = true;
let spotlightHero = false;
let showSparks = true;

let camYaw = 0.72, camPitch = 0.48, camDist = 6.2;
let camTarget = [0.0, 0.35, 0.25];
let smoothTarget = [0.0, 0.35, 0.25];

let dragBtn = -1, lastX = 0, lastY = 0;
canvas.addEventListener("contextmenu", e => e.preventDefault());
canvas.addEventListener("pointerdown", e => {
  dragBtn = e.button; lastX = e.clientX; lastY = e.clientY;
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", e => {
  if (dragBtn < 0) return;
  const dx = e.clientX - lastX, dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  if (dragBtn === 0) {
    camYaw -= dx * 0.0065;
    camPitch = Math.max(0.06, Math.min(1.48, camPitch + dy * 0.0065));
  } else {
    const s = camDist * 0.0016;
    camTarget[0] -= Math.cos(camYaw) * dx * s;
    camTarget[2] += Math.sin(camYaw) * dx * s;
    camTarget[1] = Math.max(0.0, camTarget[1] + dy * s);
  }
});
canvas.addEventListener("pointerup", () => { dragBtn = -1; });
canvas.addEventListener("wheel", e => {
  e.preventDefault();
  camDist = Math.max(1.1, Math.min(16.0, camDist * Math.exp(e.deltaY * 0.001)));
}, { passive: false });

// UI wiring
const btnPlay = document.getElementById("btnPlay");
const timeline = document.getElementById("timeline");
const timeReadout = document.getElementById("timeReadout");
const phaseLabel = document.getElementById("phaseLabel");

function setPlaying(p) {
  playing = p;
  btnPlay.textContent = playing ? "Pause" : "Play";
}
btnPlay.onclick = () => setPlaying(!playing);
document.getElementById("btnRestart").onclick = () => { curFrame = 0; setPlaying(true); };
document.getElementById("btnPrev").onclick = () => { setPlaying(false); curFrame = Math.max(0, Math.floor(curFrame) - 1); };
document.getElementById("btnNext").onclick = () => { setPlaying(false); curFrame = Math.min(SCENE.nFrames - 1, Math.floor(curFrame) + 1); };
timeline.addEventListener("input", () => {
  setPlaying(false);
  curFrame = parseFloat(timeline.value);
});

document.querySelectorAll("#camGroup .btn").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll("#camGroup .btn").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    camMode = b.dataset.cam;
    if (camMode === "overview") { camDist = 6.2; camPitch = 0.48; camYaw = 0.72; camTarget = [0, 0.35, 0.25]; }
    else if (camMode === "blast") { camDist = 2.6; camPitch = 0.34; camYaw = 0.65; camTarget = [0, 0.52, 0.0]; }
    else { camDist = 2.5; camPitch = 0.40; }
  };
});

document.querySelectorAll("#speedGroup .btn").forEach(b => {
  b.onclick = () => {
    document.querySelectorAll("#speedGroup .btn").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    speed = parseFloat(b.dataset.spd);
  };
});

const btnTrails = document.getElementById("btnTrails");
btnTrails.onclick = () => { showTrails = !showTrails; btnTrails.classList.toggle("active", showTrails); };
const btnHighlightHero = document.getElementById("btnHighlightHero");
btnHighlightHero.onclick = () => { spotlightHero = !spotlightHero; btnHighlightHero.classList.toggle("active", spotlightHero); };
const btnSparks = document.getElementById("btnSparks");
btnSparks.onclick = () => {
  showSparks = !showSparks;
  btnSparks.classList.toggle("active", showSparks);
  btnSparks.textContent = showSparks ? "FX Sparks: ON" : "FX Sparks: OFF";
};

window.addEventListener("keydown", e => {
  if (e.code === "Space") { e.preventDefault(); setPlaying(!playing); }
  else if (e.code === "KeyR") { curFrame = 0; setPlaying(true); }
  else if (e.code === "ArrowLeft") { setPlaying(false); curFrame = Math.max(0, Math.round(curFrame) - 1); }
  else if (e.code === "ArrowRight") { setPlaying(false); curFrame = Math.min(SCENE.nFrames - 1, Math.round(curFrame) + 1); }
});

// Uniform locations
const uMesh = {
  uVP: gl.getUniformLocation(meshProg, "uVP"),
  uModel: gl.getUniformLocation(meshProg, "uModel"),
  uTex: gl.getUniformLocation(meshProg, "uTex"),
  uCamPos: gl.getUniformLocation(meshProg, "uCamPos"),
  uBlastGlow: gl.getUniformLocation(meshProg, "uBlastGlow"),
  uBlastPos: gl.getUniformLocation(meshProg, "uBlastPos"),
  uIsFlash: gl.getUniformLocation(meshProg, "uIsFlash"),
  uShadowPass: gl.getUniformLocation(meshProg, "uShadowPass"),
  uDimAlpha: gl.getUniformLocation(meshProg, "uDimAlpha"),
  uMatType: gl.getUniformLocation(meshProg, "uMatType"),
};
const uLineVP = gl.getUniformLocation(lineProg, "uVP");

const mProj = new Float32Array(16);
const mView = new Float32Array(16);
const mVP = new Float32Array(16);
const mModel = new Float32Array(16);
const tmpP = new Float32Array(3), tmpQ = new Float32Array(4), tmpS = new Float32Array(3);

let lastTime = performance.now();

function render(now) {
  const dt = Math.min(0.05, (now - lastTime) * 0.001);
  lastTime = now;

  if (playing) {
    curFrame += dt * SCENE.fps * speed;
    if (curFrame >= SCENE.nFrames - 1) curFrame = 0.0;
  }
  timeline.value = curFrame.toFixed(1);
  const sec = curFrame / SCENE.fps;
  timeReadout.textContent = `${sec.toFixed(2)}s · F${String(Math.floor(curFrame)).padStart(3,"0")}/${SCENE.nFrames - 1}`;

  if (curFrame < SCENE.boomFrame) phaseLabel.textContent = "1/4 · Wheel Rev-Up & Pressure Shudder";
  else if (sec < 0.95) phaseLabel.textContent = "2/4 · Core Rupture & 24-Piece Voronoi Burst";
  else if (sec < 2.85) phaseLabel.textContent = "3/4 · Banked Wheel Curves & Rolling Steel Bar";
  else phaseLabel.textContent = "4/4 · Coin-Wobble Precession & Wreckage Settle";

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.floor(innerWidth * dpr), h = Math.floor(innerHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.055, 0.066, 0.092, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  // Update camera target if tracking a rolling part
  if (camMode === "wheel_left" || camMode === "wheel_right" || camMode === "main_bar") {
    samplePartTRS(partMap[camMode], curFrame, tmpP, tmpQ, tmpS);
    camTarget[0] = tmpP[0];
    camTarget[1] = Math.max(0.18, tmpP[1] * 0.65);
    camTarget[2] = tmpP[2];
  }
  const lerpK = 1.0 - Math.exp(-10.0 * dt);
  smoothTarget[0] += (camTarget[0] - smoothTarget[0]) * lerpK;
  smoothTarget[1] += (camTarget[1] - smoothTarget[1]) * lerpK;
  smoothTarget[2] += (camTarget[2] - smoothTarget[2]) * lerpK;

  const eye = [
    smoothTarget[0] + Math.sin(camYaw) * Math.cos(camPitch) * camDist,
    smoothTarget[1] + Math.sin(camPitch) * camDist,
    smoothTarget[2] + Math.cos(camYaw) * Math.cos(camPitch) * camDist,
  ];
  mat4Perspective(mProj, 44 * Math.PI / 180, w / Math.max(1, h), 0.08, 60.0);
  mat4LookAt(mView, eye, smoothTarget, [0, 1, 0]);
  mat4Mul(mVP, mProj, mView);

  // 1. Draw floor grid
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.useProgram(lineProg);
  gl.uniformMatrix4fv(uLineVP, false, mVP);
  gl.bindVertexArray(gridVao);
  gl.drawArrays(gl.LINES, 0, gridCount);

  // 2. Draw floor trails for Left Wheel, Right Wheel, and Main Stainless Bar
  const dynFloats = [];
  if (showTrails && curFrame > SCENE.boomFrame) {
    const trailSpecs = [
      { name: "wheel_left",  col: [0.22, 0.74, 0.97] },
      { name: "wheel_right", col: [0.98, 0.44, 0.52] },
      { name: "main_bar",    col: [0.98, 0.75, 0.15] },
    ];
    const maxI = Math.floor(curFrame);
    for (const ts of trailSpecs) {
      const trs = partMap[ts.name].trs;
      for (let i = SCENE.boomFrame; i < maxI; i++) {
        const b0 = i * 10, b1 = (i + 1) * 10;
        const ageA = Math.max(0.12, 1.0 - (maxI - i) / 220.0) * 0.85;
        dynFloats.push(
          trs[b0], 0.008, trs[b0+2], ts.col[0], ts.col[1], ts.col[2], ageA,
          trs[b1], 0.008, trs[b1+2], ts.col[0], ts.col[1], ts.col[2], ageA
        );
      }
    }
  }

  // 3. Add active ballistic spark streaks
  if (showSparks) {
    for (const sp of sparkParticles) {
      const dtS = sec - sp.t0;
      if (dtS > 0 && dtS < sp.life) {
        const u = dtS / sp.life;
        const gAcc = sp.rubber ? 6.0 : 12.5;
        const x1 = sp.p0[0] + sp.v[0] * dtS;
        const y1 = Math.max(0.01, sp.p0[1] + sp.v[1] * dtS - 0.5 * gAcc * dtS * dtS);
        const z1 = sp.p0[2] + sp.v[2] * dtS;
        const dtPrev = Math.max(0, dtS - 0.028);
        const x0 = sp.p0[0] + sp.v[0] * dtPrev;
        const y0 = Math.max(0.01, sp.p0[1] + sp.v[1] * dtPrev - 0.5 * gAcc * dtPrev * dtPrev);
        const z0 = sp.p0[2] + sp.v[2] * dtPrev;
        const al = (1.0 - u) * 0.95;
        if (sp.rubber) {
          dynFloats.push(x0,y0,z0, 0.45,0.47,0.52,al*0.4, x1,y1,z1, 0.55,0.58,0.62,al*0.65);
        } else {
          dynFloats.push(x0,y0,z0, 1.0,0.42,0.08,al*0.35, x1,y1,z1, 1.0,0.92,0.55,al);
        }
      }
    }
  }
  if (dynFloats.length > 0) {
    gl.bindVertexArray(dynVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, dynVbo);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, new Float32Array(dynFloats));
    gl.drawArrays(gl.LINES, 0, dynFloats.length / 7);
  }

  // 4. Draw planar contact shadows + lit 3D rigid bodies
  gl.useProgram(meshProg);
  gl.uniformMatrix4fv(uMesh.uVP, false, mVP);
  gl.uniform3fv(uMesh.uCamPos, eye);
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, glTex);
  gl.uniform1i(uMesh.uTex, 0);

  const dtBoom = sec - (SCENE.boomFrame / SCENE.fps);
  const blastGlow = (dtBoom >= 0 && dtBoom < 0.35) ? Math.pow(1.0 - dtBoom / 0.35, 2.0) * 6.5 : 0.0;
  gl.uniform1f(uMesh.uBlastGlow, blastGlow);
  gl.uniform3f(uMesh.uBlastPos, 0.0, 0.54, -0.06);

  // Pass A: Planar shadows on floor (depth write off)
  gl.depthMask(false);
  gl.uniform1i(uMesh.uShadowPass, 1);
  gl.uniform1i(uMesh.uIsFlash, 0);
  for (const p of partsGPU) {
    if (p.cat === "flash") continue;
    samplePartTRS(p, curFrame, tmpP, tmpQ, tmpS);
    if (tmpS[0] < 0.01) continue;
    const dim = (spotlightHero && p.cat !== "wheel" && p.cat !== "bar") ? 0.18 : 1.0;
    gl.uniform1f(uMesh.uDimAlpha, dim);
    mat4FromTRS(mModel, tmpP[0], tmpP[1], tmpP[2], tmpQ[0], tmpQ[1], tmpQ[2], tmpQ[3], tmpS[0], tmpS[1], tmpS[2]);
    gl.uniformMatrix4fv(uMesh.uModel, false, mModel);
    gl.bindVertexArray(p.vao);
    gl.drawElements(gl.TRIANGLES, p.ni, gl.UNSIGNED_SHORT, 0);
  }

  // Pass B: Solid lit 3D meshes
  gl.depthMask(true);
  gl.uniform1i(uMesh.uShadowPass, 0);
  for (const p of partsGPU) {
    samplePartTRS(p, curFrame, tmpP, tmpQ, tmpS);
    if (tmpS[0] < 0.01) continue;
    const isFlash = (p.cat === "flash") ? 1 : 0;
    const dim = (!isFlash && spotlightHero && p.cat !== "wheel" && p.cat !== "bar") ? 0.22 : 1.0;
    gl.uniform1i(uMesh.uIsFlash, isFlash);
    gl.uniform1f(uMesh.uDimAlpha, dim);
    gl.uniform1i(uMesh.uMatType, p.matCode);
    mat4FromTRS(mModel, tmpP[0], tmpP[1], tmpP[2], tmpQ[0], tmpQ[1], tmpQ[2], tmpQ[3], tmpS[0], tmpS[1], tmpS[2]);
    gl.uniformMatrix4fv(uMesh.uModel, false, mModel);
    gl.bindVertexArray(p.vao);
    gl.drawElements(gl.TRIANGLES, p.ni, gl.UNSIGNED_SHORT, 0);
  }

  requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
