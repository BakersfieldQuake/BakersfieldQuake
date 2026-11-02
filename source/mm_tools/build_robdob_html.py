"""Builds G:\\Quake\\Combat\\BakersfieldQuake\\robdob_head.html:
A 100% self-contained, zero-CDN interactive WebGL 3D inspector for the upgraded RobDob Floating Head
(`progs/floathead.mdl`) & 1st-Person Held Viewmodel (`progs/v_robdob.mdl`) with his Crimson "M'LADY" Fedora,
plus live side-by-side / toggle comparison against the original `.pre_fedora` model, real Quake `.wav` audio,
frame-by-frame scrubber, part isolation (Head + Fedora / Fedora Only / Head Only), and 1152x1152 skin atlas viewer.

Usage:
    python3 -E -P source/mm_tools/build_robdob_html.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SOUND = os.path.join(MOD, "sound")
OUT_HTML = os.path.join(MOD, "robdob_head.html")


def pil_to_webp_uri(im: Image.Image, quality: int = 90, max_dim: int = 1152) -> str:
    if max(im.size) > max_dim:
        sc = max_dim / float(max(im.size))
        im = im.resize((int(round(im.width * sc)), int(round(im.height * sc))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def file_to_data_uri(path: str, mime: str) -> str | None:
    if not os.path.isfile(path):
        return None
    raw = open(path, "rb").read()
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def pack_f32_b64(arr: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<f4").tobytes()).decode("ascii")


def pack_u16_b64(arr: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<u2").tobytes()).decode("ascii")


def load_mdl_webgl(mdl_path: str, head_uv_rows: int = 256) -> dict:
    """Loads a Quake IDPO v6 .mdl into smooth-normal float32 WebGL buffers, sorting head vs hat triangles."""
    d = open(mdl_path, "rb").read()
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6, f"Bad MDL header: {mdl_path}"
    scale = np.array(h[2:5], dtype=np.float64)
    tr = np.array(h[5:8], dtype=np.float64)
    nsk, sw, sh, nv, nt, nf = h[12:18]

    o = 84
    for _ in range(nsk):
        kind = struct.unpack_from("<i", d, o)[0]
        assert kind == 0
        o += 4 + sw * sh

    st_raw = np.frombuffer(d, "<i4", nv * 3, o).reshape(nv, 3)
    o += nv * 12
    tri_raw = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16

    frame_names: list[str] = []
    raw_verts = []
    for _ in range(nf):
        kind = struct.unpack_from("<i", d, o)[0]
        assert kind == 0
        name = d[o + 12:o + 28].split(b"\0", 1)[0].decode("ascii", "replace")
        v = np.frombuffer(d, np.uint8, nv * 4, o + 28).reshape(nv, 4)
        pts = v[:, :3].astype(np.float64) * scale + tr
        frame_names.append(name)
        raw_verts.append(pts)
        o += 28 + nv * 4

    raw_verts_arr = np.asarray(raw_verts, dtype=np.float32)  # (nf, nv, 3)

    # Expand any back-facing onseam vertices cleanly if present, and flip CW -> CCW for standard WebGL outward winding
    onseam = st_raw[:, 0]
    s_px = st_raw[:, 1].astype(np.float64)
    t_px = st_raw[:, 2].astype(np.float64)

    vert_map: dict[tuple[int, int], int] = {}
    out_orig_idx: list[int] = []
    out_uv: list[tuple[float, float]] = []
    head_tris: list[tuple[int, int, int]] = []
    hat_tris: list[tuple[int, int, int]] = []

    def get_v(vi: int, back_seam: int) -> int:
        key = (vi, back_seam)
        got = vert_map.get(key)
        if got is not None:
            return got
        s = s_px[vi] + (sw * 0.5 if back_seam else 0.0)
        t = t_px[vi]
        idx = len(out_orig_idx)
        vert_map[key] = idx
        out_orig_idx.append(vi)
        out_uv.append(((s + 0.5) / sw, (t + 0.5) / sh))
        return idx

    for facesfront, a, b, c in tri_raw:
        bs_a = 1 if (not facesfront and onseam[a]) else 0
        bs_b = 1 if (not facesfront and onseam[b]) else 0
        bs_c = 1 if (not facesfront and onseam[c]) else 0
        ia = get_v(int(a), bs_a)
        ib = get_v(int(b), bs_b)
        ic = get_v(int(c), bs_c)
        # Quake .mdl triangles (a, b, c) are clockwise from outside; (ia, ic, ib) is CCW outward in right-handed XYZ!
        tri_ccw = (ia, ic, ib)
        if max(t_px[a], t_px[b], t_px[c]) < head_uv_rows:
            head_tris.append(tri_ccw)
        else:
            hat_tris.append(tri_ccw)

    all_tris = np.asarray(head_tris + hat_tris, dtype=np.uint16)
    orig_idx_arr = np.asarray(out_orig_idx, dtype=np.int32)
    verts_exp = raw_verts_arr[:, orig_idx_arr, :]  # (nf, nv_exp, 3)
    uv_arr = np.asarray(out_uv, dtype=np.float32)

    # Compute smooth area-weighted per-frame vertex normals (welds shared UV islands, keeps sharp creases at UV splits)
    nv_exp = verts_exp.shape[1]
    norms_exp = np.zeros_like(verts_exp, dtype=np.float32)
    ta, tb, tc = all_tris[:, 0], all_tris[:, 1], all_tris[:, 2]
    for fi in range(nf):
        P = verts_exp[fi]
        fn = np.cross(P[tb] - P[ta], P[tc] - P[ta])  # outward normal for CCW (ia, ic, ib)
        vn = np.zeros((nv_exp, 3), dtype=np.float32)
        np.add.at(vn, ta, fn)
        np.add.at(vn, tb, fn)
        np.add.at(vn, tc, fn)
        nlen = np.linalg.norm(vn, axis=1, keepdims=True)
        norms_exp[fi] = np.where(nlen > 1e-8, vn / np.maximum(nlen, 1e-8), np.array([0.0, 0.0, 1.0], dtype=np.float32))

    # Wireframe unique edges (head + hat)
    edges_head = set()
    for a, b, c in head_tris:
        for u, v in ((a, b), (b, c), (c, a)):
            edges_head.add((min(u, v), max(u, v)))
    edges_hat = set()
    for a, b, c in hat_tris:
        for u, v in ((a, b), (b, c), (c, a)):
            edges_hat.add((min(u, v), max(u, v)))
    eh_list = sorted(edges_head)
    ef_list = sorted(edges_hat)
    all_edges = np.asarray(eh_list + ef_list, dtype=np.uint16).reshape(-1)

    return dict(
        nf=int(nf),
        nv=int(nv_exp),
        nt=int(len(all_tris)),
        headIdxCount=int(len(head_tris) * 3),
        hatIdxCount=int(len(hat_tris) * 3),
        headEdgeCount=int(len(eh_list) * 2),
        hatEdgeCount=int(len(ef_list) * 2),
        frameNames=frame_names,
        vertsB64=pack_f32_b64(verts_exp),
        normsB64=pack_f32_b64(norms_exp),
        uvsB64=pack_f32_b64(uv_arr),
        trisB64=pack_u16_b64(all_tris.reshape(-1)),
        edgesB64=pack_u16_b64(all_edges),
        bboxMin=[round(float(x), 2) for x in verts_exp.min(axis=(0, 1))],
        bboxMax=[round(float(x), 2) for x in verts_exp.max(axis=(0, 1))],
        sw=int(sw),
        sh=int(sh),
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rob Dob — Crimson "M'LADY" Fedora 3D Model &amp; Animation Inspector</title>
<style>
:root {
  --bg: #100c0b;
  --bg2: #171210;
  --panel: #1d1614;
  --panel2: #261d1a;
  --line: #3c2d28;
  --crimson: #e02438;
  --crimson-hi: #ff4757;
  --gold: #f4c55c;
  --mint: #6ef2a6;
  --cyan: #5ce1e6;
  --ink: #f5ede4;
  --dim: #a8988c;
  --mono: ui-monospace, "Cascadia Mono", "IBM Plex Mono", Consolas, monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: radial-gradient(circle at 22% 0%, #2a1316 0%, var(--bg) 56%); color: var(--ink); font: 13.5px/1.45 var(--sans); }
header {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 10px 18px; padding: 12px 18px; border-bottom: 1px solid var(--line);
  background: rgba(20, 14, 13, 0.92); backdrop-filter: blur(8px); position: sticky; top: 0; z-index: 30;
}
.brand { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.brand h1 {
  margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 0.03em; text-transform: uppercase;
  display: flex; align-items: center; gap: 8px;
}
.badge-pill {
  display: inline-block; padding: 2px 8px; border-radius: 999px; font: 700 11px/1.4 var(--mono);
  background: linear-gradient(135deg, var(--crimson), #9e1122); color: #fff; letter-spacing: 0.06em;
}
.brand small { color: var(--dim); font-family: var(--mono); font-size: 12px; }
.seg {
  display: inline-flex; flex-wrap: wrap; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: var(--panel);
}
.seg button {
  background: transparent; color: var(--dim); border: 0; padding: 7px 13px;
  font: 600 12.5px var(--sans); cursor: pointer; transition: background 0.14s, color 0.14s;
}
.seg button + button { border-left: 1px solid var(--line); }
.seg button:hover { color: var(--ink); background: rgba(255,255,255,0.04); }
.seg button.act { background: var(--crimson); color: #fff; }

.workspace {
  display: grid; grid-template-columns: minmax(0, 1fr) 370px; gap: 14px;
  padding: 14px 18px; max-width: 1760px; margin: 0 auto;
}
@media (max-width: 1020px) {
  .workspace { grid-template-columns: 1fr; }
}

.stage-wrap {
  display: flex; flex-direction: column; gap: 10px;
}
#stage {
  position: relative; height: min(70vh, 690px); min-height: 460px;
  background: radial-gradient(circle at 50% 42%, #291d1a 0%, #0d0908 78%);
  border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
  user-select: none; touch-action: none; cursor: grab;
  box-shadow: 0 18px 46px rgba(0, 0, 0, 0.55);
}
#stage.dragging { cursor: grabbing; }
#glCanvas { width: 100%; height: 100%; display: block; }

.hud-top {
  position: absolute; top: 12px; left: 12px; right: 12px;
  display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; pointer-events: none;
}
.hud-card {
  background: rgba(15, 11, 10, 0.82); border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 8px; padding: 7px 11px; font: 12px/1.4 var(--mono); color: var(--ink);
  backdrop-filter: blur(6px);
}
.hud-card .sub { color: var(--dim); font-size: 11px; }
.hud-split-labels {
  position: absolute; top: 58px; left: 0; right: 0; display: none;
  justify-content: space-around; pointer-events: none; font: 700 12px var(--mono);
}
.hud-split-labels span {
  background: rgba(12, 9, 8, 0.82); border: 1px solid var(--line); padding: 4px 10px; border-radius: 999px;
}

#quakeCrosshair {
  position: absolute; left: 50%; top: 50%; width: 22px; height: 22px; margin: -11px 0 0 -11px;
  pointer-events: none; display: none;
}
#quakeCrosshair::before, #quakeCrosshair::after {
  content: ""; position: absolute; background: #7dff7d; box-shadow: 0 0 4px #000;
}
#quakeCrosshair::before { left: 10px; top: 0; width: 2px; height: 22px; }
#quakeCrosshair::after { top: 10px; left: 0; width: 22px; height: 2px; }

#quakeHudBar {
  position: absolute; left: 0; right: 0; bottom: 38px; display: none;
  justify-content: center; gap: 44px; pointer-events: none;
  font: 800 22px var(--mono); letter-spacing: 0.08em; color: #e23b2e;
  text-shadow: 0 2px 0 #000, 0 0 12px rgba(0,0,0,0.8);
}
#quakeHudBar .num { color: var(--gold); }

.stage-overlay-actions {
  position: absolute; bottom: 12px; left: 12px; right: 12px;
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px;
  pointer-events: none;
}
.stage-overlay-actions > * { pointer-events: auto; }
.cam-snaps {
  display: flex; flex-wrap: wrap; gap: 5px;
}
.snap-btn {
  background: rgba(24, 18, 16, 0.86); color: var(--ink); border: 1px solid var(--line);
  border-radius: 6px; padding: 5px 9px; font: 600 11.5px var(--mono); cursor: pointer;
}
.snap-btn:hover { border-color: var(--crimson-hi); color: #fff; background: rgba(224, 36, 56, 0.22); }
.action-triggers { display: flex; gap: 7px; flex-wrap: wrap; }
.big-act {
  background: linear-gradient(135deg, var(--crimson-hi), #b81426); color: #fff; border: 0;
  border-radius: 7px; padding: 7px 14px; font: 700 12.5px var(--mono); cursor: pointer;
  box-shadow: 0 4px 14px rgba(224, 36, 56, 0.4);
}
.big-act:hover { filter: brightness(1.1); }
.big-act.gold {
  background: linear-gradient(135deg, #f5b942, #c67d15); color: #1a0f04;
  box-shadow: 0 4px 14px rgba(245, 185, 66, 0.32);
}

.scrubber-bar {
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 10px 14px; display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px;
}
.scrubber-bar button {
  background: var(--panel2); color: var(--ink); border: 1px solid var(--line);
  border-radius: 6px; padding: 5px 10px; font: 600 12px var(--mono); cursor: pointer;
}
.scrubber-bar button.act { background: var(--crimson); border-color: var(--crimson-hi); color: #fff; }
#frameSlider { flex: 1; min-width: 160px; accent-color: var(--crimson-hi); cursor: pointer; }
#frameReadout { font: 600 12px var(--mono); color: var(--gold); min-width: 145px; text-align: right; }

aside {
  display: flex; flex-direction: column; gap: 11px;
}
.card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 12px 13px;
}
.card h2 {
  margin: 0 0 9px; font: 700 12px var(--mono); letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--gold); display: flex; justify-content: space-between; align-items: center;
}
.clip-list { display: flex; flex-direction: column; gap: 5px; }
.clip-btn {
  text-align: left; background: var(--panel2); color: var(--ink); border: 1px solid var(--line);
  border-radius: 7px; padding: 7px 10px; font: 600 12.5px var(--sans); cursor: pointer;
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
}
.clip-btn:hover { border-color: #5c433b; }
.clip-btn.act {
  background: rgba(224, 36, 56, 0.2); border-color: var(--crimson-hi); color: #fff;
}
.clip-btn small { font: 500 11px var(--mono); color: var(--dim); }
.clip-btn.act small { color: var(--gold); }

.ctrl-row {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px;
}
.ctrl-row:last-child { margin-bottom: 0; }
.ctrl-row label { color: var(--dim); font-size: 12.5px; }
.ctrl-row input[type="range"] { flex: 1; max-width: 175px; accent-color: var(--crimson-hi); }
.ctrl-row select {
  background: var(--panel2); color: var(--ink); border: 1px solid var(--line);
  border-radius: 6px; padding: 4px 8px; font: 12px var(--mono);
}
.checks { display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 6px; }
.checks label { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--ink); cursor: pointer; }
.checks input { accent-color: var(--crimson-hi); }

.sfx-grid {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px;
}
.sfx-btn {
  background: var(--panel2); color: var(--ink); border: 1px solid var(--line);
  border-radius: 6px; padding: 6px 8px; font: 600 11.5px var(--mono); cursor: pointer; text-align: left;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sfx-btn:hover { border-color: var(--gold); color: var(--gold); }

.below-fold {
  max-width: 1760px; margin: 4px auto 34px; padding: 0 18px;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px;
}
.atlas-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 13px;
}
.atlas-card h3 {
  margin: 0 0 6px; font: 700 13px var(--mono); text-transform: uppercase; letter-spacing: 0.07em; color: var(--gold);
}
.atlas-card p { margin: 0 0 10px; color: var(--dim); font-size: 12.5px; }
.atlas-img-wrap {
  background: #0b0807; border: 1px solid var(--line); border-radius: 8px; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.atlas-img-wrap img { width: 100%; height: auto; display: block; cursor: zoom-in; }
.spec-list {
  margin: 8px 0 0; padding-left: 18px; color: var(--ink); font-size: 12.5px;
}
.spec-list li { margin-bottom: 5px; }
.spec-list code { font-family: var(--mono); color: var(--gold); background: rgba(255,255,255,0.06); padding: 1px 5px; border-radius: 4px; }

#lightbox {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.88); z-index: 100;
  display: none; align-items: center; justify-content: center; padding: 24px; cursor: zoom-out;
}
#lightbox img { max-width: 95vw; max-height: 92vh; border: 1px solid var(--line); border-radius: 8px; }
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1><span>🎩</span> Rob Dob Fedora Inspector <span class="badge-pill">M'LADY EDITION</span></h1>
    <small>progs/floathead.mdl (4,237v · 7,788t) &amp; progs/v_robdob.mdl · 100% Self-Contained WebGL</small>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
    <div class="seg" id="camModeSeg" title="Switch camera &amp; gameplay viewpoint">
      <button data-mode="orbit" class="act">1 · 360° Studio Orbit</button>
      <button data-mode="pilot">2 · Pilot Chase-Cam (Flight)</button>
      <button data-mode="vm">3 · 1st-Person Held (FOV 90)</button>
    </div>
    <div class="seg" id="compareSeg" title="Compare upgraded Crimson Fedora vs original pre-fedora model">
      <button data-cmp="new" class="act">🎩 Fedora Upgrade</button>
      <button data-cmp="split">⚖️ Side-by-Side</button>
      <button data-cmp="old">🧔 Original (.pre_fedora)</button>
    </div>
  </div>
</header>

<div class="workspace">
  <div class="stage-wrap">
    <div id="stage">
      <canvas id="glCanvas"></canvas>

      <div class="hud-top">
        <div class="hud-card" id="hudLeft">
          <div id="hudTitle" style="font-weight:700; color:var(--gold);">floathead.mdl — IDLE + "M'LADY" SALUTE</div>
          <div class="sub" id="hudStats">4,237 verts · 7,788 tris · Skin 0 (1152×1152)</div>
        </div>
        <div class="hud-card" style="text-align:right;">
          <div>Drag = Orbit · Right-Drag = Pan · Wheel = Zoom</div>
          <div class="sub">Keys: <b>Space</b> = Dash / Throw · <b>P</b> = Pain Hit · <b>1-3</b> = View Mode</div>
        </div>
      </div>

      <div class="hud-split-labels" id="splitLabels">
        <span style="color:var(--dim);">ORIGINAL (.pre_fedora · 2,896v / Static Rush Jaw)</span>
        <span style="color:var(--gold);">UPGRADED (Crimson "M'LADY" Fedora · 4,237v / Chomping Jaw)</span>
      </div>

      <div id="quakeCrosshair"></div>
      <div id="quakeHudBar">
        <span>ARMOR <span class="num">0</span></span>
        <span>HEALTH <span class="num">100</span></span>
        <span>ROB DOB <span class="num" id="hudAmmo">1</span></span>
      </div>

      <div class="stage-overlay-actions">
        <div class="cam-snaps" id="orbitSnaps">
          <button class="snap-btn" data-snap="3q">3/4 "M'LADY" Card</button>
          <button class="snap-btn" data-snap="front">Front Face</button>
          <button class="snap-btn" data-snap="right">Right Profile (Feather)</button>
          <button class="snap-btn" data-snap="rear">Pilot Rear (180°)</button>
          <button class="snap-btn" data-snap="under">Under-Brim &amp; Sweatband</button>
          <button class="snap-btn" data-snap="top">Top Teardrop Crease</button>
        </div>
        <div class="action-triggers">
          <button class="big-act" id="btnDash" title="Trigger floathead.qc open1-4 -> rush1-4 dash sequence + charge.wav!">⚡ DASH! (Space)</button>
          <button class="big-act gold" id="btnPain" title="Trigger floathead.qc pain1-4 crooked fedora knockback + pain.wav!">💥 PAIN HIT (P)</button>
        </div>
      </div>
    </div>

    <div class="scrubber-bar">
      <button id="btnPlay" class="act">⏸ Playing</button>
      <button id="btnPrev" title="Previous frame">◀</button>
      <button id="btnNext" title="Next frame">▶</button>
      <input type="range" id="frameSlider" min="0" max="19" step="0.01" value="0">
      <div id="frameReadout">idle1 (0 / 20)</div>
      <div class="seg" id="speedSeg">
        <button data-spd="0.2">0.2×</button>
        <button data-spd="0.5">0.5×</button>
        <button data-spd="1" class="act">1.0×</button>
      </div>
    </div>
  </div>

  <aside>
    <div class="card">
      <h2><span>Animation Clips</span> <small style="color:var(--dim);font-weight:400;">floathead.qc</small></h2>
      <div class="clip-list" id="clipList"></div>
    </div>

    <div class="card">
      <h2>Mesh Parts &amp; Shading</h2>
      <div class="ctrl-row">
        <label>Isolate Part</label>
        <div class="seg" id="partSeg">
          <button data-part="both" class="act">Head + Hat</button>
          <button data-part="hat">🎩 Hat Only</button>
          <button data-part="head">🧔 Head Only</button>
        </div>
      </div>
      <div class="ctrl-row">
        <label>Skin Override</label>
        <select id="skinSel">
          <option value="auto" selected>Auto (Per Clip)</option>
          <option value="0">Skin 0 — Closed Smirk</option>
          <option value="1">Skin 1 — Screaming Mouth</option>
        </select>
      </div>
      <div class="ctrl-row">
        <label>Lighting</label>
        <select id="litSel">
          <option value="hybrid" selected>Quake Fullbright + Subtle Relief</option>
          <option value="fullbright">Pure EF_FULLBRIGHT (Unlit Skin)</option>
          <option value="studio">3D Studio Key + Rim Shaded</option>
        </select>
      </div>
      <div class="ctrl-row">
        <label>Exposure (<span id="expVal">1.42</span>×)</label>
        <input type="range" id="expRange" min="0.6" max="2.4" step="0.02" value="1.42">
      </div>
      <div class="checks">
        <label><input type="checkbox" id="chkSpin"> Auto-Turntable</label>
        <label><input type="checkbox" id="chkWire"> Wireframe Overlay</label>
        <label><input type="checkbox" id="chkRoom" checked> Quake Brick Room (Pilot/1P)</label>
        <label><input type="checkbox" id="chkSound" checked> Play Sound FX</label>
      </div>
    </div>

    <div class="card">
      <h2><span>In-Game Soundboard</span> <small style="color:var(--dim);font-weight:400;">sound/floathead</small></h2>
      <div class="sfx-grid" id="sfxGrid"></div>
    </div>

    <div class="card">
      <h2>Upgrade Highlights</h2>
      <ul class="spec-list">
        <li><b>Crimson Wool-Felt Fedora</b>: Pinched teardrop crown, curled snap-brim, calfskin sweatband + gold piping, satin diamond crest, brass buckle, double-sided <code>M'LADY</code> press-card &amp; plume feather.</li>
        <li><b>1st-Person Crosshair Placement</b>: Card, buckle &amp; feather sit on his right temple (<code>-Y</code>, <code>-6.5°</code> cock) facing inward toward the crosshair in <code>v_robdob.mdl</code>.</li>
        <li><b>Cartoon Dash &amp; Chomping Jaw</b>: Clicking Fire blasts the fedora into the slipstream (<code>open1-4</code>) and chomps his jaw at <code>20 fps</code> (<code>rush1-4</code>).</li>
      </ul>
    </div>
  </aside>
</div>

<section class="below-fold">
  <div class="atlas-card">
    <h3>Skin 0 Atlas — Closed Smirk + Fedora Strip (1152×1152)</h3>
    <p>Top <code>1152×768</code> preserves 100% of the head unwrap; bottom <code>1152×384</code> packs the monotonic polar outer felt, leather sweatband &amp; satin crest, black grosgrain silk band, brass buckle, <code>VIP · PRESS / M'LADY</code> card, and plume feather. Click to zoom.</p>
    <div class="atlas-img-wrap"><img id="imgSkin0" alt="Skin 0 Atlas"></div>
  </div>
  <div class="atlas-card">
    <h3>Skin 1 Atlas — Screaming Dash Mouth + Fedora Strip</h3>
    <p>Activated automatically during <code>open1-4</code>, <code>rush1-4</code>, and <code>pain1-4</code> in <code>floathead.qc</code> while his jaw chomps and the crimson fedora hovers &amp; flutters overhead in the slipstream.</p>
    <div class="atlas-img-wrap"><img id="imgSkin1" alt="Skin 1 Atlas"></div>
  </div>
  <div class="atlas-card">
    <h3>Canonical Reference &amp; Multi-Angle Sheet</h3>
    <p>Inspired directly by Rob's Mystery Box card (<code>14_friend_rob.png</code> — red fedora + black band + red <code>M'LADY</code> tee) alongside orthographic turnaround previews.</p>
    <div style="display:grid; grid-template-columns: 1fr 1.35fr; gap:8px; align-items:start;">
      <div class="atlas-img-wrap"><img id="imgRefRob" alt="14_friend_rob reference"></div>
      <div class="atlas-img-wrap"><img id="imgViews" alt="Orthographic multi-angle views"></div>
    </div>
  </div>
</section>

<div id="lightbox"><img id="lightboxImg" alt="Zoomed view"></div>

<script id="payloadData" type="application/json">/*PAYLOAD_JSON*/</script>
<script>
(() => {
  "use strict";
  const DATA = JSON.parse(document.getElementById("payloadData").textContent);

  // Populate reference images + click-to-zoom lightbox
  document.getElementById("imgSkin0").src = DATA.textures.fh0;
  document.getElementById("imgSkin1").src = DATA.textures.fh1;
  document.getElementById("imgRefRob").src = DATA.textures.refRob;
  document.getElementById("imgViews").src = DATA.textures.viewsSheet;

  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightboxImg");
  document.querySelectorAll(".atlas-img-wrap img").forEach(im => {
    im.addEventListener("click", () => {
      lightboxImg.src = im.src;
      lightbox.style.display = "flex";
    });
  });
  lightbox.addEventListener("click", () => { lightbox.style.display = "none"; });

  // Soundboard setup
  const audioCache = {};
  function playSfx(key, force = false) {
    if (!force && !document.getElementById("chkSound").checked) return;
    const item = DATA.sounds.find(s => s.key === key);
    if (!item || !item.uri) return;
    try {
      if (!audioCache[key]) audioCache[key] = new Audio(item.uri);
      const a = audioCache[key];
      a.currentTime = 0;
      a.volume = 0.75;
      a.play().catch(() => {});
    } catch (_) {}
  }
  const sfxGrid = document.getElementById("sfxGrid");
  DATA.sounds.forEach(s => {
    const b = document.createElement("button");
    b.className = "sfx-btn";
    b.textContent = s.label;
    b.addEventListener("click", () => playSfx(s.key, true));
    sfxGrid.appendChild(b);
  });

  // Base64 typed-array decoders
  function b64ToF32(b64) {
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return new Float32Array(u8.buffer);
  }
  function b64ToU16(b64) {
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return new Uint16Array(u8.buffer);
  }
  function loadImg(uri) {
    return new Promise((resolve, reject) => {
      const im = new Image();
      im.onload = () => resolve(im);
      im.onerror = reject;
      im.src = uri;
    });
  }

  // Clips definition (matches floathead.qc & v_robdob.mdl)
  const CLIPS = [
    { id: "idle",      label: "🎩 Idle + \"M'Lady\" Fedora Tip", tag: "idle1-8 · 10 fps", model: "fh", start: 0,  count: 8, fps: 10, skin: 0 },
    { id: "dash_seq",  label: "⚡ Full Dash: Blast-Off → Rush!", tag: "open1-4 → rush1-4", model: "fh", special: "dash", fps: 20, skin: 1 },
    { id: "rush",      label: "🦷 Chomping Rush + Slipstream Hat", tag: "rush1-4 · 20 fps", model: "fh", start: 12, count: 4, fps: 16, skin: 1 },
    { id: "open",      label: "😱 Jaw Drop & Hat Launch", tag: "open1-4 · loop", model: "fh", start: 8,  count: 4, fps: 8,  skin: 1 },
    { id: "pain",      label: "💥 Knocked Crooked Pain", tag: "pain1-4 · 10 fps", model: "fh", start: 16, count: 4, fps: 8,  skin: 1 },
    { id: "vm_bob",    label: "🤚 1st-Person Held Salute", tag: "v_robdob bob1-8", model: "vm", start: 0,  count: 8, fps: 10, skin: 0 },
    { id: "all20",     label: "🎞 All 20 World Frames", tag: "frame 0..19", model: "fh", start: 0,  count: 20, fps: 8, skin: 0 },
  ];

  // State
  const state = {
    camMode: "orbit",     // "orbit" | "pilot" | "vm"
    compare: "new",       // "new" | "split" | "old"
    clipIdx: 0,
    part: "both",         // "both" | "hat" | "head"
    skinMode: "auto",     // "auto" | "0" | "1"
    litMode: "hybrid",    // "hybrid" | "fullbright" | "studio"
    exposure: 1.42,
    playing: true,
    speed: 1.0,
    spin: false,
    wire: false,
    showRoom: true,
    manualFrame: 0.0,
    // Orbit camera in Quake Z-up spherical coordinates around target
    az: -0.56,            // -32 deg -> faces his front-right (-Y) "M'LADY" press-card & feather!
    el: 0.14,
    dist: 76.0,
    panX: 0.0,
    panY: 0.0,
    panZ: 4.5,
    // Action state for live Dash / Pain / VM Launch simulation
    dashStartT: -999,
    dashing: false,
    painStartT: -999,
    vmGoneStartT: -999,
    hallScroll: 0.0,
  };

  // Build clip buttons
  const clipList = document.getElementById("clipList");
  function renderClipList() {
    clipList.innerHTML = "";
    CLIPS.forEach((c, idx) => {
      const b = document.createElement("button");
      b.className = "clip-btn" + (idx === state.clipIdx ? " act" : "");
      b.innerHTML = `<span>${c.label}</span><small>${c.tag}</small>`;
      b.addEventListener("click", () => {
        state.clipIdx = idx;
        state.dashing = (c.id === "dash_seq");
        if (c.id === "dash_seq") {
          state.dashStartT = performance.now() / 1000;
          playSfx("charge");
        } else if (c.id === "pain") {
          playSfx("pain");
        } else if (c.id === "vm_bob" && state.camMode !== "vm") {
          setCamMode("vm");
        } else if (c.model === "fh" && state.camMode === "vm") {
          setCamMode("orbit");
        }
        renderClipList();
      });
      clipList.appendChild(b);
    });
  }

  // Camera Mode switching
  function setCamMode(mode) {
    state.camMode = mode;
    document.querySelectorAll("#camModeSeg button").forEach(b => b.classList.toggle("act", b.dataset.mode === mode));
    document.getElementById("orbitSnaps").style.display = (mode === "orbit") ? "flex" : "none";
    document.getElementById("quakeCrosshair").style.display = (mode === "vm" || mode === "pilot") ? "block" : "none";
    document.getElementById("quakeHudBar").style.display = (mode === "vm") ? "flex" : "none";
    if (mode === "vm") {
      state.compare = "new";
      document.querySelectorAll("#compareSeg button").forEach(b => b.classList.toggle("act", b.dataset.cmp === "new"));
      document.getElementById("splitLabels").style.display = "none";
      const vmIdx = CLIPS.findIndex(c => c.id === "vm_bob");
      if (vmIdx >= 0) state.clipIdx = vmIdx;
      document.getElementById("btnDash").textContent = "🚀 LAUNCH HEAD (Space)";
    } else {
      if (CLIPS[state.clipIdx].model === "vm") state.clipIdx = 0;
      document.getElementById("btnDash").textContent = "⚡ DASH! (Space)";
    }
    renderClipList();
  }

  document.querySelectorAll("#camModeSeg button").forEach(b => {
    b.addEventListener("click", () => setCamMode(b.dataset.mode));
  });

  document.querySelectorAll("#compareSeg button").forEach(b => {
    b.addEventListener("click", () => {
      if (state.camMode === "vm" && b.dataset.cmp !== "new") setCamMode("orbit");
      state.compare = b.dataset.cmp;
      document.querySelectorAll("#compareSeg button").forEach(x => x.classList.toggle("act", x === b));
      document.getElementById("splitLabels").style.display = (state.compare === "split") ? "flex" : "none";
    });
  });

  document.querySelectorAll("#partSeg button").forEach(b => {
    b.addEventListener("click", () => {
      state.part = b.dataset.part;
      document.querySelectorAll("#partSeg button").forEach(x => x.classList.toggle("act", x === b));
    });
  });

  document.querySelectorAll("#speedSeg button").forEach(b => {
    b.addEventListener("click", () => {
      state.speed = parseFloat(b.dataset.spd);
      document.querySelectorAll("#speedSeg button").forEach(x => x.classList.toggle("act", x === b));
    });
  });

  // Snap camera presets (Quake Z-up: az=0 looks from +X at front face; az=-pi/2 looks from -Y at right ear/M'LADY side; az=pi looks from -X behind)
  const SNAPS = {
    "3q":    { az: -0.56, el: 0.14, dist: 74, pz: 4.5 },
    "front": { az:  0.00, el: 0.08, dist: 74, pz: 4.5 },
    "right": { az: -1.32, el: 0.10, dist: 74, pz: 5.0 },
    "rear":  { az:  3.1416, el: 0.20, dist: 82, pz: 5.0 },
    "under": { az: -0.52, el: -0.58, dist: 68, pz: 8.5 },
    "top":   { az: -0.35, el: 1.08, dist: 72, pz: 8.0 },
  };
  document.querySelectorAll(".snap-btn").forEach(b => {
    b.addEventListener("click", () => {
      const s = SNAPS[b.dataset.snap];
      if (!s) return;
      state.az = s.az; state.el = s.el; state.dist = s.dist;
      state.panX = 0; state.panY = 0; state.panZ = s.pz;
      state.spin = false;
      document.getElementById("chkSpin").checked = false;
    });
  });

  // Action buttons (Dash / Pain / Launch)
  function triggerDashOrLaunch() {
    const now = performance.now() / 1000;
    if (state.camMode === "vm") {
      state.vmGoneStartT = now;
      playSfx("sight1");
      return;
    }
    state.playing = true;
    updatePlayBtn();
    const dashIdx = CLIPS.findIndex(c => c.id === "dash_seq");
    state.clipIdx = dashIdx;
    state.dashStartT = now;
    state.dashing = true;
    playSfx("charge");
    renderClipList();
  }
  function triggerPain() {
    const now = performance.now() / 1000;
    if (state.camMode === "vm") setCamMode("orbit");
    state.playing = true;
    updatePlayBtn();
    state.painStartT = now;
    state.dashing = false;
    const painIdx = CLIPS.findIndex(c => c.id === "pain");
    state.clipIdx = painIdx;
    playSfx("pain");
    renderClipList();
  }
  document.getElementById("btnDash").addEventListener("click", triggerDashOrLaunch);
  document.getElementById("btnPain").addEventListener("click", triggerPain);

  // Scrubber & Play/Pause controls
  const btnPlay = document.getElementById("btnPlay");
  const frameSlider = document.getElementById("frameSlider");
  const frameReadout = document.getElementById("frameReadout");
  function updatePlayBtn() {
    btnPlay.textContent = state.playing ? "⏸ Playing" : "▶ Paused";
    btnPlay.classList.toggle("act", state.playing);
  }
  btnPlay.addEventListener("click", () => {
    state.playing = !state.playing;
    updatePlayBtn();
  });
  frameSlider.addEventListener("input", () => {
    state.playing = false;
    updatePlayBtn();
    state.manualFrame = parseFloat(frameSlider.value);
  });
  function stepFrame(delta) {
    state.playing = false;
    updatePlayBtn();
    const total = (state.camMode === "vm") ? 9 : 20;
    state.manualFrame = (Math.round(state.manualFrame) + delta + total) % total;
    frameSlider.value = state.manualFrame;
  }
  document.getElementById("btnPrev").addEventListener("click", () => stepFrame(-1));
  document.getElementById("btnNext").addEventListener("click", () => stepFrame(1));

  // Sidebar inputs
  document.getElementById("skinSel").addEventListener("change", e => { state.skinMode = e.target.value; });
  document.getElementById("litSel").addEventListener("change", e => { state.litMode = e.target.value; });
  const expRange = document.getElementById("expRange");
  const expVal = document.getElementById("expVal");
  expRange.addEventListener("input", () => {
    state.exposure = parseFloat(expRange.value);
    expVal.textContent = state.exposure.toFixed(2);
  });
  document.getElementById("chkSpin").addEventListener("change", e => { state.spin = e.target.checked; });
  document.getElementById("chkWire").addEventListener("change", e => { state.wire = e.target.checked; });
  document.getElementById("chkRoom").addEventListener("change", e => { state.showRoom = e.target.checked; });

  window.addEventListener("keydown", e => {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "SELECT")) return;
    if (e.code === "Space") { e.preventDefault(); triggerDashOrLaunch(); }
    else if (e.key === "p" || e.key === "P") { triggerPain(); }
    else if (e.key === "1") setCamMode("orbit");
    else if (e.key === "2") setCamMode("pilot");
    else if (e.key === "3") setCamMode("vm");
    else if (e.key === "ArrowLeft") stepFrame(-1);
    else if (e.key === "ArrowRight") stepFrame(1);
  });

  renderClipList();

  // ======================== Pure Zero-CDN WebGL Engine ========================
  const stage = document.getElementById("stage");
  const canvas = document.getElementById("glCanvas");
  const gl = canvas.getContext("webgl", { antialias: true, alpha: false });
  if (!gl) {
    document.getElementById("hudTitle").textContent = "WebGL unavailable in this browser";
    return;
  }

  // Pointer orbit / pan / zoom on stage
  let dragBtn = -1, lx = 0, ly = 0;
  stage.addEventListener("contextmenu", e => e.preventDefault());
  stage.addEventListener("pointerdown", e => {
    if (e.target.closest("button")) return;
    dragBtn = e.button;
    lx = e.clientX; ly = e.clientY;
    stage.classList.add("dragging");
    stage.setPointerCapture(e.pointerId);
  });
  stage.addEventListener("pointermove", e => {
    if (dragBtn < 0) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    if (state.camMode !== "orbit") return;
    if (dragBtn === 2 || e.shiftKey) {
      const k = state.dist * 0.0016;
      const rightX = -Math.sin(state.az), rightY = Math.cos(state.az);
      state.panX -= rightX * dx * k;
      state.panY -= rightY * dx * k;
      state.panZ += dy * k;
    } else {
      state.az -= dx * 0.0085;
      state.el = Math.max(-1.42, Math.min(1.42, state.el + dy * 0.0085));
    }
  });
  const endDrag = () => { dragBtn = -1; stage.classList.remove("dragging"); };
  stage.addEventListener("pointerup", endDrag);
  stage.addEventListener("pointercancel", endDrag);
  stage.addEventListener("wheel", e => {
    e.preventDefault();
    if (state.camMode !== "orbit") return;
    state.dist = Math.max(22.0, Math.min(220.0, state.dist * (e.deltaY > 0 ? 1.085 : 0.92)));
  }, { passive: false });

  // Shaders: Morphing Model Shader + Procedural Quake Brick Room Shader
  const vsModel = `
    attribute vec3 aPos0, aPos1;
    attribute vec3 aNrm0, aNrm1;
    attribute vec2 aUv;
    uniform float uLerp;
    uniform mat4 uMVP;
    uniform mat3 uNMat;
    varying vec2 vUv;
    varying vec3 vNrm;
    void main() {
      vec3 p = mix(aPos0, aPos1, uLerp);
      vec3 n = normalize(mix(aNrm0, aNrm1, uLerp));
      vUv = aUv;
      vNrm = normalize(uNMat * n);
      gl_Position = uMVP * vec4(p, 1.0);
    }
  `;
  const fsModel = `
    precision mediump float;
    varying vec2 vUv;
    varying vec3 vNrm;
    uniform sampler2D uTex;
    uniform float uExposure;
    uniform int uLitMode;
    uniform int uWirePass;
    void main() {
      if (uWirePass == 1) {
        gl_FragColor = vec4(0.45, 0.95, 1.0, 0.55);
        return;
      }
      vec3 n = normalize(vNrm);
      if (!gl_FrontFacing) n = -n;
      vec4 texel = texture2D(uTex, vUv);
      vec3 col = texel.rgb * uExposure;
      if (uLitMode == 0) {
        // Hybrid: Quake EF_FULLBRIGHT skin fidelity + gentle 3D contour relief so pinched crown & brim read crisply
        vec3 l1 = normalize(vec3(0.38, 0.28, 0.88));
        float shade = 0.84 + 0.24 * max(dot(n, l1), 0.0) + 0.08 * max(n.z, 0.0);
        col *= shade;
      } else if (uLitMode == 2) {
        vec3 l1 = normalize(vec3(0.45, 0.35, 0.82));
        vec3 l2 = normalize(vec3(-0.65, -0.35, 0.45));
        float diff = 0.42 + 0.62 * max(dot(n, l1), 0.0) + 0.24 * max(dot(n, l2), 0.0);
        vec3 h = normalize(l1 + vec3(0.0, 0.0, 1.0));
        float spec = pow(max(dot(n, h), 0.0), 26.0) * 0.18;
        col = col * diff + vec3(spec);
      }
      gl_FragColor = vec4(col, 1.0);
    }
  `;

  const vsRoom = `
    attribute vec3 aPos;
    attribute vec2 aUv;
    uniform mat4 uMVP;
    uniform vec2 uScroll;
    varying vec2 vUv;
    varying float vDist;
    void main() {
      vUv = aUv + uScroll;
      vec4 cp = uMVP * vec4(aPos, 1.0);
      vDist = cp.w;
      gl_Position = cp;
    }
  `;
  const fsRoom = `
    precision mediump float;
    varying vec2 vUv;
    varying float vDist;
    uniform sampler2D uTex;
    void main() {
      vec3 c = texture2D(uTex, vUv).rgb;
      float fog = clamp((vDist - 120.0) / 760.0, 0.0, 1.0);
      vec3 fogCol = vec3(0.065, 0.048, 0.044);
      gl_FragColor = vec4(mix(c, fogCol, fog), 1.0);
    }
  `;

  function compileProgram(vs, fs) {
    const mk = (t, s) => {
      const sh = gl.createShader(t);
      gl.shaderSource(sh, s);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(sh));
      return sh;
    };
    const p = gl.createProgram();
    gl.attachShader(p, mk(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    return p;
  }

  const progModel = compileProgram(vsModel, fsModel);
  const locM = {
    p0: gl.getAttribLocation(progModel, "aPos0"),
    p1: gl.getAttribLocation(progModel, "aPos1"),
    n0: gl.getAttribLocation(progModel, "aNrm0"),
    n1: gl.getAttribLocation(progModel, "aNrm1"),
    uv: gl.getAttribLocation(progModel, "aUv"),
    lerp: gl.getUniformLocation(progModel, "uLerp"),
    mvp: gl.getUniformLocation(progModel, "uMVP"),
    nmat: gl.getUniformLocation(progModel, "uNMat"),
    tex: gl.getUniformLocation(progModel, "uTex"),
    exp: gl.getUniformLocation(progModel, "uExposure"),
    lit: gl.getUniformLocation(progModel, "uLitMode"),
    wire: gl.getUniformLocation(progModel, "uWirePass"),
  };

  const progRoom = compileProgram(vsRoom, fsRoom);
  const locR = {
    pos: gl.getAttribLocation(progRoom, "aPos"),
    uv: gl.getAttribLocation(progRoom, "aUv"),
    mvp: gl.getUniformLocation(progRoom, "uMVP"),
    scroll: gl.getUniformLocation(progRoom, "uScroll"),
    tex: gl.getUniformLocation(progRoom, "uTex"),
  };

  // Procedural Quake brown runic brick texture for Pilot / 1st-Person corridor
  function makeBrickTexture() {
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d");
    g.fillStyle = "#483428";
    g.fillRect(0, 0, 256, 256);
    let seed = 42;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < 1200; i++) {
      g.fillStyle = rnd() < 0.5 ? `rgba(0,0,0,${rnd() * 0.16})` : `rgba(235,195,150,${rnd() * 0.08})`;
      g.fillRect(rnd() * 256, rnd() * 256, 2 + rnd() * 10, 2 + rnd() * 6);
    }
    g.strokeStyle = "#221711";
    g.lineWidth = 4;
    const rows = 4, step = 256 / rows;
    for (let r = 0; r <= rows; r++) {
      g.beginPath(); g.moveTo(0, r * step); g.lineTo(256, r * step); g.stroke();
    }
    for (let r = 0; r < rows; r++) {
      for (let k = 0; k <= 2; k++) {
        const x = ((r % 2) * 0.5 + k) * 128;
        g.beginPath(); g.moveTo(x, r * step); g.lineTo(x, (r + 1) * step); g.stroke();
      }
    }
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    gl.generateMipmap(gl.TEXTURE_2D);
    return t;
  }
  const texBrick = makeBrickTexture();

  // Build Quake corridor box around origin along +X/-X: x in [-400, +1100], y in [-220, +220], z in [-52, +190]
  function makeCorridorBuffers() {
    const x0 = -420, x1 = 1100, y0 = -220, y1 = 220, z0 = -52, z1 = 190;
    const uLen = (x1 - x0) / 96.0, vWall = (z1 - z0) / 96.0, vFlr = (y1 - y0) / 96.0;
    // Pos (x,y,z) + UV (u along X so scrolling u moves along corridor!)
    const quads = [
      // Floor
      [[x0,y0,z0, 0,0], [x1,y0,z0, uLen,0], [x1,y1,z0, uLen,vFlr], [x0,y1,z0, 0,vFlr]],
      // Ceiling
      [[x0,y1,z1, 0,0], [x1,y1,z1, uLen,0], [x1,y0,z1, uLen,vFlr], [x0,y0,z1, 0,vFlr]],
      // Left wall (+Y)
      [[x0,y1,z0, 0,0], [x1,y1,z0, uLen,0], [x1,y1,z1, uLen,vWall], [x0,y1,z1, 0,vWall]],
      // Right wall (-Y)
      [[x0,y0,z1, 0,vWall], [x1,y0,z1, uLen,vWall], [x1,y0,z0, uLen,0], [x0,y0,z0, 0,0]],
      // Far end wall (+X, stationary cap)
      [[x1,y0,z0, 0,0], [x1,y1,z0, vFlr,0], [x1,y1,z1, vFlr,vWall], [x1,y0,z1, 0,vWall]],
    ];
    const pos = [], uv = [], idx = [];
    let base = 0;
    quads.forEach(q => {
      q.forEach(v => { pos.push(v[0], v[1], v[2]); uv.push(v[3], v[4]); });
      idx.push(base, base+1, base+2, base, base+2, base+3);
      base += 4;
    });
    const pb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(pos), gl.STATIC_DRAW);
    const tb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, tb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(uv), gl.STATIC_DRAW);
    const ib = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(idx), gl.STATIC_DRAW);
    return { pb, tb, ib, count: idx.length };
  }
  const corridor = makeCorridorBuffers();

  // Matrix helpers (Right-handed Quake Z-up: X forward, Y left, Z up)
  function mat4Mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++)
      for (let r = 0; r < 4; r++)
        o[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1] + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
    return o;
  }
  function perspVFov(vfovRad, aspect, zn, zf) {
    const f = 1.0 / Math.tan(vfovRad * 0.5);
    const o = new Float32Array(16);
    o[0] = f / aspect; o[5] = f;
    o[10] = (zf + zn) / (zn - zf); o[11] = -1.0;
    o[14] = (2.0 * zf * zn) / (zn - zf);
    return o;
  }
  function lookAtZUp(ex, ey, ez, tx, ty, tz) {
    let fx = tx - ex, fy = ty - ey, fz = tz - ez;
    const fl = Math.hypot(fx, fy, fz) || 1.0;
    fx /= fl; fy /= fl; fz /= fl;
    // right = normalize(cross(fwd, (0, 0, 1))) = (fy, -fx, 0)
    let sx = fy, sy = -fx, sz = 0.0;
    const sl = Math.hypot(sx, sy, sz);
    if (sl < 1e-5) { sx = 0.0; sy = 1.0; sz = 0.0; }
    else { sx /= sl; sy /= sl; }
    // up = cross(right, fwd)
    const ux = sy * fz - sz * fy;
    const uy = sz * fx - sx * fz;
    const uz = sx * fy - sy * fx;
    const o = new Float32Array(16);
    o[0] = sx;  o[4] = sy;  o[8]  = sz;  o[12] = -(sx*ex + sy*ey + sz*ez);
    o[1] = ux;  o[5] = uy;  o[9]  = uz;  o[13] = -(ux*ex + uy*ey + uz*ez);
    o[2] = -fx; o[6] = -fy; o[10] = -fz; o[14] =  (fx*ex + fy*ey + fz*ez);
    o[15] = 1.0;
    return o;
  }

  async function uploadImageTex(uri) {
    const im = await loadImg(uri);
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  }

  function buildGLModel(m) {
    const verts = b64ToF32(m.vertsB64);
    const norms = b64ToF32(m.normsB64);
    const uvs = b64ToF32(m.uvsB64);
    const tris = b64ToU16(m.trisB64);
    const edges = b64ToU16(m.edgesB64);
    const stride = m.nv * 3;
    const frames = [];
    for (let f = 0; f < m.nf; f++) {
      const vb = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, vb);
      gl.bufferData(gl.ARRAY_BUFFER, verts.subarray(f * stride, (f + 1) * stride), gl.STATIC_DRAW);
      const nb = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, nb);
      gl.bufferData(gl.ARRAY_BUFFER, norms.subarray(f * stride, (f + 1) * stride), gl.STATIC_DRAW);
      frames.push({ vb, nb });
    }
    const uvb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, uvb);
    gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
    const ib = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tris, gl.STATIC_DRAW);
    const eb = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, eb);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edges, gl.STATIC_DRAW);
    return { ...m, frames, uvb, ib, eb };
  }

  // Boot async texture uploads & start render loop
  Promise.all([
    uploadImageTex(DATA.textures.fh0),
    uploadImageTex(DATA.textures.fh1),
    uploadImageTex(DATA.textures.vm0),
    uploadImageTex(DATA.textures.old0),
    uploadImageTex(DATA.textures.old1),
  ]).then(([texFh0, texFh1, texVm0, texOld0, texOld1]) => {
    const mdlFh = buildGLModel(DATA.models.floathead);
    const mdlVm = buildGLModel(DATA.models.v_robdob);
    const mdlOld = buildGLModel(DATA.models.floatheadOld);

    let lastT = performance.now() / 1000;

    function resolvePose(now, isVm) {
      if (isVm) {
        frameSlider.max = "8";
        if (!state.playing) {
          const fi = Math.max(0, Math.min(8, Math.floor(state.manualFrame)));
          const fNext = (fi < 8) ? ((fi + 1) % 8) : 8;
          return { f0: fi, f1: fNext, lerp: state.manualFrame - Math.floor(state.manualFrame), skin: 0, name: mdlVm.frameNames[fi] };
        }
        const dtGone = now - state.vmGoneStartT;
        if (dtGone >= 0 && dtGone < 1.15) {
          document.getElementById("hudAmmo").textContent = "0 (FLYING!)";
          return { f0: 8, f1: 8, lerp: 0, skin: 0, name: "gone (launched!)" };
        }
        document.getElementById("hudAmmo").textContent = "1";
        const pos = (now * 10.0 * state.speed) % 8.0;
        const i0 = Math.floor(pos);
        return { f0: i0, f1: (i0 + 1) % 8, lerp: pos - i0, skin: 0, name: mdlVm.frameNames[i0] };
      }

      frameSlider.max = "19";
      if (!state.playing) {
        const fi = Math.max(0, Math.min(19, Math.floor(state.manualFrame)));
        const fNext = (fi + 1) % 20;
        const autoSk = fi >= 8 ? 1 : 0;
        return { f0: fi, f1: fNext, lerp: state.manualFrame - Math.floor(state.manualFrame), skin: autoSk, name: mdlFh.frameNames[fi] };
      }

      // Temporary pain override when Pain button pressed in Pilot mode
      const dtPain = (now - state.painStartT) * state.speed;
      const clip = CLIPS[state.clipIdx];
      if (clip.id === "dash_seq" || state.dashing) {
        const dt = Math.max(0, (now - state.dashStartT) * state.speed);
        // Repeat dash blast-off every 3.2s in Studio/Dash clip so you see the launch repeatedly, or hold rush in Pilot
        const cyc = (state.camMode === "pilot") ? dt : (dt % 3.2);
        if (state.camMode === "pilot" && dt > 4.0) {
          state.dashing = false;
          state.clipIdx = 0;
          renderClipList();
        } else if (cyc < 0.16) {
          const p = cyc * 25.0;
          const i0 = Math.min(3, Math.floor(p));
          const i1 = (i0 < 3) ? (i0 + 1) : 12; // seamless handoff open4 -> rush1!
          return { f0: 8 + i0, f1: (i0 < 3 ? 8 + i1 : 12), lerp: p - Math.floor(p), skin: 1, name: mdlFh.frameNames[8 + i0] };
        } else {
          const p = ((cyc - 0.16) * 18.0) % 4.0;
          const i0 = Math.floor(p);
          return { f0: 12 + i0, f1: 12 + ((i0 + 1) % 4), lerp: p - i0, skin: 1, name: mdlFh.frameNames[12 + i0] };
        }
      }

      if (dtPain >= 0 && dtPain < 0.5 && clip.id === "pain") {
        const p = Math.min(3.99, dtPain * 8.0);
        const i0 = Math.floor(p);
        return { f0: 16 + i0, f1: (i0 < 3 ? 16 + i0 + 1 : 0), lerp: p - i0, skin: 1, name: mdlFh.frameNames[16 + i0] };
      }

      const pos = (now * clip.fps * state.speed) % clip.count;
      const i0 = Math.floor(pos);
      const f0 = clip.start + i0;
      const f1 = clip.start + ((i0 + 1) % clip.count);
      const autoSkin = (clip.id === "all20") ? (f0 >= 8 ? 1 : 0) : clip.skin;
      return { f0, f1, lerp: pos - i0, skin: autoSkin, name: mdlFh.frameNames[f0] };
    }

    function drawCorridor(MVP, scrollX) {
      gl.useProgram(progRoom);
      gl.uniformMatrix4fv(locR.mvp, false, MVP);
      gl.uniform2f(locR.scroll, scrollX, 0.0);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, texBrick);
      gl.uniform1i(locR.tex, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, corridor.pb);
      gl.enableVertexAttribArray(locR.pos);
      gl.vertexAttribPointer(locR.pos, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, corridor.tb);
      gl.enableVertexAttribArray(locR.uv);
      gl.vertexAttribPointer(locR.uv, 2, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, corridor.ib);
      gl.drawElements(gl.TRIANGLES, corridor.count, gl.UNSIGNED_SHORT, 0);

      gl.disableVertexAttribArray(locR.pos);
      gl.disableVertexAttribArray(locR.uv);
    }

    function drawModel(m, tex, MVP, V, f0, f1, lerp, allowPartFilter) {
      gl.useProgram(progModel);
      gl.uniform1f(locM.lerp, lerp);
      gl.uniformMatrix4fv(locM.mvp, false, MVP);
      const nmat = new Float32Array([V[0], V[1], V[2], V[4], V[5], V[6], V[8], V[9], V[10]]);
      gl.uniformMatrix3fv(locM.nmat, false, nmat);
      gl.uniform1f(locM.exp, state.exposure);
      const litInt = state.litMode === "hybrid" ? 0 : (state.litMode === "fullbright" ? 1 : 2);
      gl.uniform1i(locM.lit, litInt);
      gl.uniform1i(locM.wire, 0);

      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.uniform1i(locM.tex, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frames[f0].vb);
      gl.enableVertexAttribArray(locM.p0);
      gl.vertexAttribPointer(locM.p0, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frames[f1].vb);
      gl.enableVertexAttribArray(locM.p1);
      gl.vertexAttribPointer(locM.p1, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frames[f0].nb);
      gl.enableVertexAttribArray(locM.n0);
      gl.vertexAttribPointer(locM.n0, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.frames[f1].nb);
      gl.enableVertexAttribArray(locM.n1);
      gl.vertexAttribPointer(locM.n1, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, m.uvb);
      gl.enableVertexAttribArray(locM.uv);
      gl.vertexAttribPointer(locM.uv, 2, gl.FLOAT, false, 0, 0);

      let triOffsetBytes = 0;
      let triIdxCount = m.headIdxCount + m.hatIdxCount;
      let edgeOffsetBytes = 0;
      let edgeIdxCount = m.headEdgeCount + m.hatEdgeCount;
      if (allowPartFilter && m.hatIdxCount > 0) {
        if (state.part === "head") {
          triIdxCount = m.headIdxCount;
          edgeIdxCount = m.headEdgeCount;
        } else if (state.part === "hat") {
          triOffsetBytes = m.headIdxCount * 2;
          triIdxCount = m.hatIdxCount;
          edgeOffsetBytes = m.headEdgeCount * 2;
          edgeIdxCount = m.hatEdgeCount;
        }
      }

      if (triIdxCount > 0) {
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ib);
        gl.drawElements(gl.TRIANGLES, triIdxCount, gl.UNSIGNED_SHORT, triOffsetBytes);
      }

      if (state.wire && edgeIdxCount > 0) {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.uniform1i(locM.wire, 1);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.eb);
        gl.drawElements(gl.LINES, edgeIdxCount, gl.UNSIGNED_SHORT, edgeOffsetBytes);
        gl.disable(gl.BLEND);
      }
    }

    function renderViewport(vx, vy, vw, vh, m, tex, pose, now, allowPartFilter) {
      gl.viewport(vx, vy, vw, vh);
      const aspect = Math.max(0.2, vw / Math.max(1, vh));
      let V, P;
      if (state.camMode === "vm") {
        // True Quake 90-deg 4:3 FOV -> vfov = 2 * atan(tan(45deg) * 3/4) = 73.74 deg (gives 106.26 deg HFOV at 16:9!)
        const vfov = 2.0 * Math.atan(0.75);
        P = perspVFov(vfov, aspect, 1.5, 1600.0);
        V = lookAtZUp(0, 0, 0, 20, 0, 0);
        if (state.showRoom) drawCorridor(mat4Mul(P, V), 0.0);
        // Clear depth so viewmodel never clips into world walls (just like Quake r_drawviewmodel!)
        gl.clear(gl.DEPTH_BUFFER_BIT);
      } else if (state.camMode === "pilot") {
        // FD_Camera sits 92u behind (-X) and 16u above (+Z) the flying head! Zoom slightly closer (-76u) during dash for drama
        const isRush = (pose.f0 >= 8 && pose.f0 <= 15);
        const camX = isRush ? -82.0 : -88.0;
        const camZ = isRush ? 18.0 : 16.0;
        const vfov = isRush ? 1.12 : 0.98;
        P = perspVFov(vfov, aspect, 2.0, 1800.0);
        V = lookAtZUp(camX, 0.0, camZ, 0.0, 0.0, isRush ? 9.0 : 4.0);
        if (state.showRoom) drawCorridor(mat4Mul(P, V), state.hallScroll);
      } else {
        P = perspVFov(0.74, aspect, 2.0, 1500.0);
        const ex = state.panX + state.dist * Math.cos(state.el) * Math.cos(state.az);
        const ey = state.panY + state.dist * Math.cos(state.el) * Math.sin(state.az);
        const ez = state.panZ + state.dist * Math.sin(state.el);
        V = lookAtZUp(ex, ey, ez, state.panX, state.panY, state.panZ);
      }
      const MVP = mat4Mul(P, V);
      drawModel(m, tex, MVP, V, pose.f0, pose.f1, pose.lerp, allowPartFilter);
    }

    gl.enable(gl.DEPTH_TEST);

    function frame(ms) {
      const now = ms / 1000.0;
      const dt = Math.min(0.1, now - lastT);
      lastT = now;

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const cw = Math.max(2, Math.floor(canvas.clientWidth * dpr));
      const ch = Math.max(2, Math.floor(canvas.clientHeight * dpr));
      if (canvas.width !== cw || canvas.height !== ch) {
        canvas.width = cw;
        canvas.height = ch;
      }

      if (state.spin && state.camMode === "orbit" && dragBtn < 0) {
        state.az -= dt * 0.65;
      }

      const isVm = (state.camMode === "vm");
      const pose = resolvePose(now, isVm);

      // Corridor scroll speed in Pilot Chase-Cam (2000 u/s dash vs 320 u/s cruise!)
      if (state.playing && state.camMode === "pilot") {
        const spd = (pose.f0 >= 8 && pose.f0 <= 15) ? 20.8 : 3.3;
        state.hallScroll = (state.hallScroll + dt * spd * state.speed) % 1000.0;
      }

      const useSkin = state.skinMode === "auto" ? pose.skin : parseInt(state.skinMode, 10);

      gl.viewport(0, 0, cw, ch);
      gl.clearColor(0.065, 0.048, 0.044, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      if (isVm) {
        renderViewport(0, 0, cw, ch, mdlVm, texVm0, pose, now, true);
        document.getElementById("hudTitle").textContent = `v_robdob.mdl — 1ST-PERSON HELD VIEW (${pose.name.toUpperCase()})`;
        document.getElementById("hudStats").textContent = `${mdlVm.nv.toLocaleString()} verts · ${(mdlVm.nt).toLocaleString()} tris · Lower-Right Eye Space (18.8, -18.9, -9.3)`;
      } else if (state.compare === "split") {
        const half = Math.floor(cw / 2);
        const texOld = useSkin === 1 ? texOld1 : texOld0;
        const texNew = useSkin === 1 ? texFh1 : texFh0;
        renderViewport(0, 0, half - 1, ch, mdlOld, texOld, pose, now, false);
        renderViewport(half + 1, 0, cw - half - 1, ch, mdlFh, texNew, pose, now, true);
        document.getElementById("hudTitle").textContent = `SIDE-BY-SIDE — ORIGINAL vs CRIMSON "M'LADY" FEDORA (${pose.name})`;
        document.getElementById("hudStats").textContent = `Left: 2,896v / 5,376t (384×256)  |  Right: 4,237v / 7,788t (384×384, TGA 1152²)`;
      } else if (state.compare === "old") {
        const texOld = useSkin === 1 ? texOld1 : texOld0;
        renderViewport(0, 0, cw, ch, mdlOld, texOld, pose, now, false);
        document.getElementById("hudTitle").textContent = `floathead.mdl.pre_fedora — ORIGINAL (${pose.name})`;
        document.getElementById("hudStats").textContent = `${mdlOld.nv.toLocaleString()} verts · ${mdlOld.nt.toLocaleString()} tris · Skin ${useSkin} (1152×768)`;
      } else {
        const texNew = useSkin === 1 ? texFh1 : texFh0;
        renderViewport(0, 0, cw, ch, mdlFh, texNew, pose, now, true);
        const modeTag = state.camMode === "pilot" ? "PILOT CHASE-CAM" : CLIPS[state.clipIdx].label;
        document.getElementById("hudTitle").textContent = `floathead.mdl — ${modeTag} (${pose.name})`;
        document.getElementById("hudStats").textContent = `${mdlFh.nv.toLocaleString()} verts · ${mdlFh.nt.toLocaleString()} tris · Skin ${useSkin} (1152×1152 TGA)`;
      }

      // Update scrubber readout
      const totalF = isVm ? 9 : 20;
      const curFloat = pose.f0 + pose.lerp;
      if (state.playing) {
        state.manualFrame = curFloat;
        frameSlider.value = curFloat.toFixed(2);
      }
      frameReadout.textContent = `${pose.name} (${pose.f0 + 1} / ${totalF})`;

      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  });
})();
</script>
</body>
</html>
"""


def main() -> None:
    print("[1/3] Extracting WebGL geometry & smooth normals from floathead.mdl, v_robdob.mdl, and .pre_fedora...")
    fh_new = load_mdl_webgl(os.path.join(PROGS, "floathead.mdl"), head_uv_rows=256)
    vm_new = load_mdl_webgl(os.path.join(PROGS, "v_robdob.mdl"), head_uv_rows=256)
    pre_path = os.path.join(PROGS, "floathead.mdl.pre_fedora")
    fh_old = load_mdl_webgl(pre_path, head_uv_rows=256) if os.path.isfile(pre_path) else fh_new

    print("[2/3] Encoding 1152x1152 TGA skins, reference art & Quake WAV soundboard...")
    t_fh0 = pil_to_webp_uri(Image.open(os.path.join(PROGS, "floathead.mdl_0.tga")).convert("RGB"), quality=92, max_dim=1152)
    t_fh1 = pil_to_webp_uri(Image.open(os.path.join(PROGS, "floathead.mdl_1.tga")).convert("RGB"), quality=92, max_dim=1152)
    t_vm0 = pil_to_webp_uri(Image.open(os.path.join(PROGS, "v_robdob.mdl_0.tga")).convert("RGB"), quality=92, max_dim=1152)

    old0_p = os.path.join(PROGS, "floathead.mdl_0.tga.pre_fedora")
    old1_p = os.path.join(PROGS, "floathead.mdl_1.tga.pre_fedora")
    t_old0 = pil_to_webp_uri(Image.open(old0_p).convert("RGB"), quality=90, max_dim=1152) if os.path.isfile(old0_p) else t_fh0
    t_old1 = pil_to_webp_uri(Image.open(old1_p).convert("RGB"), quality=90, max_dim=1152) if os.path.isfile(old1_p) else t_fh1

    ref_rob_p = os.path.join(HERE, "out", "mystery_box", "vote_thumbs", "14_friend_rob.png")
    views_p = os.path.join(HERE, "preview", "floathead", "floathead_views.png")
    t_ref = pil_to_webp_uri(Image.open(ref_rob_p).convert("RGB"), quality=88, max_dim=720) if os.path.isfile(ref_rob_p) else t_fh0
    t_views = pil_to_webp_uri(Image.open(views_p).convert("RGB"), quality=88, max_dim=1200) if os.path.isfile(views_p) else t_fh0

    sound_specs = [
        ("charge", "⚡ Dash Scream (charge.wav)", os.path.join(SOUND, "floathead", "charge.wav")),
        ("sight1", "🎩 Sight 1 (sight1.wav)",     os.path.join(SOUND, "floathead", "sight1.wav")),
        ("sight2", "😏 Sight 2 (sight2.wav)",     os.path.join(SOUND, "floathead", "sight2.wav")),
        ("pain",   "💥 Pain Hit (pain.wav)",      os.path.join(SOUND, "floathead", "pain.wav")),
        ("idle",   "🌀 Drone Hum (idle.wav)",     os.path.join(SOUND, "floathead", "idle.wav")),
        ("boing",  "🪀 Bounce (boing.wav)",       os.path.join(SOUND, "floathead", "boing.wav")),
        ("pop",    "🎈 Head Pop (pop.wav)",       os.path.join(SOUND, "floathead", "pop.wav")),
        ("heh",    "😂 Blast \"Heh\" (heh.wav)",  os.path.join(SOUND, "funny", "heh.wav")),
    ]
    sounds = []
    for key, label, sp in sound_specs:
        uri = file_to_data_uri(sp, "audio/wav")
        if uri:
            sounds.append(dict(key=key, label=label, uri=uri))

    payload = dict(
        models=dict(floathead=fh_new, v_robdob=vm_new, floatheadOld=fh_old),
        textures=dict(fh0=t_fh0, fh1=t_fh1, vm0=t_vm0, old0=t_old0, old1=t_old1, refRob=t_ref, viewsSheet=t_views),
        sounds=sounds,
    )

    print("[3/3] Writing self-contained HTML inspector...")
    html_out = HTML_TEMPLATE.replace("/*PAYLOAD_JSON*/", json.dumps(payload, separators=(",", ":")))
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_out)
    sz_mb = os.path.getsize(OUT_HTML) / (1024.0 * 1024.0)
    print(f"Wrote {OUT_HTML} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
