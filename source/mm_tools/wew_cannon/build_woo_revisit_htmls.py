"""Builds two self-contained WebGL2 HTML tools for revisiting the Woo / Wew / Wheelman Cannon:
  1. docs/woo_cannon_models.html        — Inspector for all 3 Woo Cannon models we built:
       - Chrome-Rod Contraption Bazooka (v_rodcannon 48f, p_rodcannon 259f 3P vwep + Ranger, g_rodcannon pickup)
       - WEW Cannon v1: Cartoon +58° Bendy-Barrel (v_wcannon 48f bend1..10, g_wewcannon v1 pickup)
       - WEW Cannon v2: XM-98 Military (Current In-Game progs/v_wewcannon.md3 48f, g_wewcannon v2 pickup)
  2. docs/woo_cannon_pose_adjuster.html — Interactive 1st-Person Pose Adjuster (defaulting to current in-game
       progs/v_wewcannon.md3, with switcher for v1 & rod_cannon), matching apply_viewmodel_edits.py & DarkPlaces FOV.
"""
import base64
import gzip
import hashlib
import io
import json
import os
import re
import sys
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
DOCS_DIR = os.path.join(MOD_ROOT, "docs")
PK3_PATH = os.path.join(MOD_ROOT, "bakersfield.pk3")
DEV_DIR = os.path.abspath(os.path.join(MOD_ROOT, "..", "_bakersfield_dev"))
ROD_HTML = os.path.join(DEV_DIR, "mod_root_archive", "rod_cannon.html")
WEW_V1_HTML = os.path.join(DEV_DIR, "wew_cannon.html")

OUT_INSPECTOR = os.path.join(DOCS_DIR, "woo_cannon_models.html")
OUT_ADJUSTER = os.path.join(DOCS_DIR, "woo_cannon_pose_adjuster.html")

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


def add_bytes(arena: bytearray, b: bytes):
    while len(arena) & 3:
        arena.append(0)
    off = len(arena)
    arena.extend(b)
    return [off, len(b)]


class TextureRegistry:
    """Deduplicates base64 PNG textures by content hash while preserving nearest-neighbor flags."""
    def __init__(self):
        self.items = []
        self.by_key = {}

    def add(self, name: str, uri: str, nearest: bool = False) -> int:
        h = hashlib.sha256(uri.encode("ascii")).hexdigest()
        key = (h, bool(nearest))
        if key in self.by_key:
            return self.by_key[key]
        idx = len(self.items)
        entry = {"name": name, "uri": uri}
        if nearest:
            entry["nearest"] = True
        self.items.append(entry)
        self.by_key[key] = idx
        return idx


def encode_png_bytes(raw_bytes: bytes, name: str) -> str:
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
    bio = io.BytesIO()
    im.save(bio, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def extract_html_payload(html_path: str):
    txt = open(html_path, "r", encoding="utf-8").read()
    m = re.search(r"const\s+PAYLOAD\s*=\s*(\{.*?\});", txt)
    if not m:
        raise RuntimeError(f"Could not locate PAYLOAD JSON in {html_path}")
    d = json.loads(m.group(1))
    arena = gzip.decompress(base64.b64decode(d["binGz"]))
    return d, arena


def copy_packed_model(model_dict, src_arena: bytes, src_textures, dst_arena: bytearray, tex_reg: TextureRegistry,
                      remap_tex_fn=None):
    """Copies an already-packed WebGL2 model dict from a source archive HTML into dst_arena."""
    new_surfs = []
    for s in model_dict["surfaces"]:
        src_t = src_textures[s["tex"]]
        t_idx = tex_reg.add(src_t["name"], src_t["uri"], bool(src_t.get("nearest", False)))
        ns = {
            "name": s["name"],
            "nv": s["nv"],
            "nt": s["nt"],
            "ne": s["ne"],
            "tex": t_idx,
            "metallic": s["metallic"],
            "rough": s["rough"],
            "unlit": s["unlit"],
            "additive": s["additive"],
            "tris": add_bytes(dst_arena, src_arena[s["tris"][0]:s["tris"][0] + s["tris"][1]]),
            "edges": add_bytes(dst_arena, src_arena[s["edges"][0]:s["edges"][0] + s["edges"][1]]),
            "uv": add_bytes(dst_arena, src_arena[s["uv"][0]:s["uv"][0] + s["uv"][1]]),
            "pos": add_bytes(dst_arena, src_arena[s["pos"][0]:s["pos"][0] + s["pos"][1]]),
            "nrm": add_bytes(dst_arena, src_arena[s["nrm"][0]:s["nrm"][0] + s["nrm"][1]]),
        }
        if remap_tex_fn:
            remap_tex_fn(s, ns)
        new_surfs.append(ns)
    return {
        "nf": model_dict["nf"],
        "nv": model_dict["nv"],
        "nt": model_dict["nt"],
        "surfaces": new_surfs,
    }


def compute_pivot_from_packed(model_dict, arena: bytearray):
    """Computes exact frame-0 bounding-box center (matching apply_viewmodel_edits.py pivot_of)."""
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for s in model_dict["surfaces"]:
        off = s["pos"][0]
        nv = s["nv"]
        arr = np.frombuffer(arena, dtype=np.int16, count=nv * 3, offset=off).reshape(nv, 3).astype(np.float64) / 64.0
        mn = arr.min(axis=0)
        mx = arr.max(axis=0)
        for k in range(3):
            lo[k] = min(lo[k], float(mn[k]))
            hi[k] = max(hi[k], float(mx[k]))
    return [round((lo[k] + hi[k]) * 0.5, 6) for k in range(3)], [round(lo[k], 3) for k in range(3)], [round(hi[k], 3) for k in range(3)]


def pack_md3_bytes(md3_bytes: bytes, dst_arena: bytearray, surf_tex_map, surf_style):
    """Packs raw .md3 bytes (from bakersfield.pk3) into dst_arena with compacted vertices & exact pivot."""
    tmp_path = os.path.join(HERE, "_tmp_read.md3")
    with open(tmp_path, "wb") as f:
        f.write(md3_bytes)
    try:
        m = md3lib.read(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    nf = m["nframes"]
    # Exact apply_viewmodel_edits.py pivot over all surfaces frame 0
    all_pts = [v for s in m["surfaces"] for v in s["frames"][0][0]]
    exact_pivot = [
        round((min(v[k] for v in all_pts) + max(v[k] for v in all_pts)) * 0.5, 6)
        for k in range(3)
    ]

    surfs_out = []
    tot_v, tot_t = 0, 0
    for s in m["surfaces"]:
        sname = s["name"]
        nt = len(s["tris"])
        used = sorted({int(idx) for tri in s["tris"] for idx in tri})
        remap = {old_i: new_i for new_i, old_i in enumerate(used)}
        used_arr = np.array(used, dtype=np.int32)
        nv = len(used)
        tot_v += nv
        tot_t += nt
        tris_ccw = np.array([(remap[a], remap[c], remap[b]) for a, b, c in s["tris"]], dtype=np.uint16)
        edges = build_edges(tris_ccw)
        uv = np.array(s["st"], dtype=np.float32)[used_arr]

        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            vv_u = np.array(vv, dtype=np.float32)[used_arr]
            nn_u = np.array(nn, dtype=np.float32)[used_arr]
            pos_q[fi] = np.clip(np.round(vv_u * 64.0), -32768, 32767).astype(np.int16)
            nrm_q[fi] = np.clip(np.round(nn_u * 127.0), -127, 127).astype(np.int8)

        st = surf_style[sname]
        surfs_out.append({
            "name": sname,
            "nv": nv,
            "nt": nt,
            "ne": len(edges),
            "tex": surf_tex_map[sname],
            "metallic": st["metallic"],
            "rough": st["rough"],
            "unlit": st["unlit"],
            "additive": st["additive"],
            "tris": add_bytes(dst_arena, tris_ccw.tobytes()),
            "edges": add_bytes(dst_arena, edges.tobytes()),
            "uv": add_bytes(dst_arena, uv.tobytes()),
            "pos": add_bytes(dst_arena, pos_q.tobytes()),
            "nrm": add_bytes(dst_arena, nrm_q.tobytes()),
        })
    return {"nf": nf, "nv": tot_v, "nt": tot_t, "surfaces": surfs_out}, exact_pivot


def build_shared_data(include_pickups_and_3p=True):
    """Collects all 3 Woo Cannon models & textures into one arena + metadata."""
    arena = bytearray()
    tex_reg = TextureRegistry()

    # 1. Chrome-Rod Contraption (v_rodcannon, p_rodcannon, g_rodcannon)
    rod_d, rod_arena = extract_html_payload(ROD_HTML)
    rod_vm = copy_packed_model(rod_d["models"][0], rod_arena, rod_d["textures"], arena, tex_reg)
    rod_pivot, rod_lo, rod_hi = compute_pivot_from_packed(rod_vm, arena)
    rod_3p = copy_packed_model(rod_d["models"][1], rod_arena, rod_d["textures"], arena, tex_reg) if include_pickups_and_3p else None
    rod_pk = copy_packed_model(rod_d["models"][2], rod_arena, rod_d["textures"], arena, tex_reg) if include_pickups_and_3p else None

    # 2. WEW Cannon v1 (Cartoon +58 deg Bendy Barrel)
    wew1_d, wew1_arena = extract_html_payload(WEW_V1_HTML)
    wew1_crt_indices = []
    for t in wew1_d["textures"]:
        if t["name"].startswith("wew_crt_"):
            wew1_crt_indices.append(tex_reg.add(t["name"], t["uri"], False))
    wew1_vm = copy_packed_model(wew1_d["models"][0], wew1_arena, wew1_d["textures"], arena, tex_reg)
    wew1_pivot, wew1_lo, wew1_hi = compute_pivot_from_packed(wew1_vm, arena)
    wew1_pk = copy_packed_model(wew1_d["models"][1], wew1_arena, wew1_d["textures"], arena, tex_reg) if include_pickups_and_3p else None

    # 3. WEW Cannon v2 — Current In-Game XM-98 Military (from bakersfield.pk3)
    with zipfile.ZipFile(PK3_PATH, "r") as z:
        wew2_tex_names = ["wew_silver.png", "wew_hand.png", "wew_core.png", "wew_fx.png"] + [
            f"wew_crt_{i:02d}.png" for i in range(16)
        ]
        wew2_tmap = {}
        for fn in wew2_tex_names:
            uri = encode_png_bytes(z.read("progs/" + fn), fn)
            wew2_tmap[fn] = tex_reg.add(fn, uri, False)

        surf_tex_2 = {
            "cannon_silver": wew2_tmap["wew_silver.png"],
            "ranger_hands":  wew2_tmap["wew_hand.png"],
            "cannon_core":   wew2_tmap["wew_core.png"],
            "crt_screen":    wew2_tmap["wew_crt_00.png"],
            "cannon_fx":     wew2_tmap["wew_fx.png"],
        }
        surf_style_2 = {
            "cannon_silver": {"metallic": 0.92, "rough": 0.18, "unlit": False, "additive": False},
            "ranger_hands":  {"metallic": 0.22, "rough": 0.52, "unlit": False, "additive": False},
            "cannon_core":   {"metallic": 0.10, "rough": 0.30, "unlit": True,  "additive": False},
            "crt_screen":    {"metallic": 0.05, "rough": 0.20, "unlit": True,  "additive": False},
            "cannon_fx":     {"metallic": 0.00, "rough": 0.50, "unlit": True,  "additive": True},
        }
        wew2_vm, wew2_pivot = pack_md3_bytes(z.read("progs/v_wewcannon.md3"), arena, surf_tex_2, surf_style_2)
        _, wew2_lo, wew2_hi = compute_pivot_from_packed(wew2_vm, arena)
        wew2_pk = None
        if include_pickups_and_3p:
            wew2_pk, _ = pack_md3_bytes(z.read("progs/g_wewcannon.md3"), arena, surf_tex_2, surf_style_2)

    wew2_crt_indices = [wew2_tmap[f"wew_crt_{i:02d}.png"] for i in range(16)]

    return {
        "arena": arena,
        "textures": tex_reg.items,
        "rod": {
            "vm": rod_vm, "p3": rod_3p, "pk": rod_pk,
            "fn_vm": rod_d["frameNames"][0],
            "fn_p3": rod_d["frameNames"][1] if len(rod_d["frameNames"]) > 1 else [],
            "pivot": rod_pivot, "lo": rod_lo, "hi": rod_hi,
        },
        "wew1": {
            "vm": wew1_vm, "pk": wew1_pk,
            "fn_vm": wew1_d["frameNames"][0],
            "crt": wew1_crt_indices,
            "pivot": wew1_pivot, "lo": wew1_lo, "hi": wew1_hi,
        },
        "wew2": {
            "vm": wew2_vm, "pk": wew2_pk,
            "fn_vm": [
                *(f"idle{i+1}" for i in range(16)),
                *(f"charge{i+1}" for i in range(10)),
                *(f"blast{i+1}" for i in range(4)),
                *(f"recoil{i+1}" for i in range(10)),
                *(f"reload{i+1}" for i in range(8)),
            ],
            "crt": wew2_crt_indices,
            "pivot": wew2_pivot, "lo": wew2_lo, "hi": wew2_hi,
        },
    }


INSPECTOR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Woo Cannon · All Models Inspector</title>
<style>
  :root { --bg:#090d16; --panel:#111827; --panel2:#182235; --border:#24324d; --acc:#38bdf8; --gold:#fbbf24; --silver:#e2e8f0; --dim:#94a3b8; --hot:#fb923c; --ok:#4ade80; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--silver); font-family:'Segoe UI',system-ui,sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
  header { padding:10px 16px; background:#0d1322; border-bottom:1px solid var(--border); display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; }
  .brand { display:flex; align-items:center; gap:10px; }
  .badge { background:linear-gradient(135deg,#fbbf24,#f97316); color:#160b00; font-weight:900; font-size:11px; padding:3px 8px; border-radius:4px; letter-spacing:0.08em; }
  h1 { font-size:17px; font-weight:900; letter-spacing:0.04em; color:#f8fafc; }
  .variant-tabs { display:flex; flex-wrap:wrap; gap:6px; }
  button { background:var(--panel2); color:#dbeafe; border:1px solid var(--border); border-radius:6px; padding:7px 12px; font-size:12.5px; font-weight:700; cursor:pointer; transition:0.12s; }
  button:hover { border-color:var(--acc); background:#1e2d47; }
  button.active { background:var(--acc); color:#06101e; border-color:var(--acc); }
  button.active-gold { background:var(--gold); color:#1a1000; border-color:var(--gold); }
  button.fire-btn { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-size:13px; padding:8px 15px; box-shadow:0 0 18px rgba(249,115,22,0.35); }
  button.fire-btn.charging { background:linear-gradient(135deg,#38bdf8,#ffffff); color:#06101e; box-shadow:0 0 24px rgba(56,189,248,0.85); }
  main { flex:1; display:grid; grid-template-columns:1fr 350px; min-height:0; }
  #vp-wrap { position:relative; background:radial-gradient(circle at 50% 42%,#17223b 0%,#070a12 78%); overflow:hidden; }
  canvas { width:100%; height:100%; display:block; cursor:grab; }
  canvas:active { cursor:grabbing; }
  #top-bar { position:absolute; left:12px; top:12px; right:12px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px; pointer-events:none; }
  #top-bar > * { pointer-events:auto; }
  .subtabs { display:flex; flex-wrap:wrap; gap:6px; background:rgba(13,19,34,0.86); padding:5px; border-radius:8px; border:1px solid var(--border); }
  .pill-tag { background:rgba(13,19,34,0.86); border:1px solid var(--border); border-radius:8px; padding:6px 11px; font-size:12px; color:var(--dim); font-family:Consolas,monospace; }
  #crosshair { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); pointer-events:none; color:var(--ok); font-weight:900; font-size:20px; text-shadow:0 0 6px #000; display:none; }
  #hud-strip { position:absolute; left:0; right:0; bottom:0; height:14%; background:repeating-linear-gradient(135deg, rgba(0,0,0,.45) 0 8px, rgba(0,0,0,.22) 8px 16px); border-top:1px dashed rgba(255,255,255,.32); color:rgba(255,255,255,.65); font:11px Consolas,monospace; display:none; align-items:center; justify-content:center; pointer-events:none; }
  #charge-hud { position:absolute; left:50%; bottom:64px; transform:translateX(-50%); background:rgba(9,13,22,0.85); border:1px solid var(--border); border-radius:8px; padding:7px 14px; text-align:center; pointer-events:none; min-width:280px; }
  #charge-bar { height:8px; background:#1e293b; border-radius:4px; overflow:hidden; margin-top:5px; }
  #charge-fill { height:100%; width:0%; background:linear-gradient(90deg,#38bdf8,#facc15,#ef4444); transition:width 0.04s linear; }
  #scrubber-bar { position:absolute; left:14px; right:14px; bottom:12px; background:rgba(13,19,34,0.90); border:1px solid var(--border); border-radius:8px; padding:8px 12px; display:flex; align-items:center; gap:9px; z-index:2; }
  input[type=range] { flex:1; accent-color:var(--acc); }
  aside { background:var(--panel); border-left:1px solid var(--border); padding:13px; overflow-y:auto; display:flex; flex-direction:column; gap:11px; font-size:12.5px; line-height:1.45; }
  .card { background:#0c1220; border:1px solid var(--border); border-radius:8px; padding:11px; }
  .card h3 { font-size:11.5px; text-transform:uppercase; letter-spacing:0.08em; color:var(--acc); margin-bottom:7px; }
  .kv { display:flex; justify-content:space-between; gap:8px; padding:3px 0; border-bottom:1px solid #162036; }
  .kv:last-child { border-bottom:none; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  code { color:#93c5fd; font-family:Consolas,monospace; font-size:11.5px; }
  .desc { color:#cbd5e1; font-size:12.5px; }
  @media (max-width: 920px) { main { grid-template-columns: 1fr; } aside { max-height: 44vh; } }
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">ALL WOO CANNONS · 3 VARIANTS</span>
    <h1>WOO / WHEELMAN CANNON MODEL INSPECTOR</h1>
  </div>
  <div class="variant-tabs">
    <button id="vtab-rod" onclick="setVariant('rod')">1 · Chrome-Rod Contraption (rodcannon)</button>
    <button id="vtab-wew1" onclick="setVariant('wew1')">2 · WEW v1 (+58° Bendy Barrel)</button>
    <button id="vtab-wew2" class="active" onclick="setVariant('wew2')">3 · WEW v2 XM-98 (Current In-Game)</button>
  </div>
  <button id="btn-charge" class="fire-btn">HOLD TO CHARGE &amp; FIRE (Space)</button>
</header>
<main>
  <div id="vp-wrap">
    <canvas id="gl"></canvas>
    <div id="top-bar">
      <div class="subtabs" id="subtabs"></div>
      <div class="pill-tag" id="geo-stat">loading...</div>
    </div>
    <div id="crosshair">+</div>
    <div id="hud-strip">status bar strip (14%)</div>
    <div id="charge-hud">
      <div id="hud-label" style="font-weight:800;font-size:11.5px;letter-spacing:0.05em;">READY · HOLD SPACE OR FIRE BUTTON</div>
      <div id="charge-bar"><div id="charge-fill"></div></div>
    </div>
    <div id="scrubber-bar">
      <button id="btn-play" onclick="togglePlay()">Pause</button>
      <button onclick="triggerFullCycle()">Play Full Cycle</button>
      <input id="scrub" type="range" min="0" max="47" step="0.05" value="0">
      <span id="frame-lbl" style="min-width:138px;font-family:Consolas,monospace;font-size:12px;">f00 · idle1</span>
    </div>
  </div>
  <aside>
    <div class="card">
      <h3 id="card-title">Model Notes</h3>
      <p class="desc" id="card-desc"></p>
      <div id="card-kvs" style="margin-top:8px;"></div>
    </div>
    <div class="card">
      <h3>Camera &amp; Inspection</h3>
      <div class="row" style="margin-bottom:8px;">
        <button id="btn-orbit" class="active" onclick="setOrbit()">Free 3D Orbit</button>
        <button id="btn-pov111" onclick="setPov(111)">Game POV 111°</button>
        <button id="btn-pov90" onclick="setPov(90)">Quake POV 90°</button>
      </div>
      <div class="row">
        <button id="btn-wire" onclick="toggleWire()">Wireframe: OFF</button>
        <button id="btn-ranger" onclick="toggleRanger()" style="display:none;">Ranger Body: ON</button>
        <button id="btn-hud" onclick="toggleHud()">Crosshair/HUD: OFF</button>
      </div>
      <div style="margin-top:7px;color:var(--dim);font-size:11.5px;">Drag to orbit, scroll wheel to zoom. Switch to <b>Game POV 111°</b> to see exact in-game framing.</div>
    </div>
    <div class="card" id="p3-card" style="display:none;">
      <h3>3rd-Person vwep Clip (259f)</h3>
      <div class="row">
        <button id="p3-stand" class="active" onclick="set3PClip('stand',12,16,7)">Stand (12-16)</button>
        <button id="p3-run" onclick="set3PClip('run',6,11,11)">Run (6-11)</button>
        <button id="p3-blast" onclick="set3PClip('blast',107,112,11)">Blast (107-112)</button>
        <button id="p3-nail" onclick="set3PClip('nail',103,104,10)">Recoil (103-104)</button>
      </div>
    </div>
    <div class="card" id="crt-card">
      <h3>WEW-TAC 98 CRT Screen</h3>
      <div class="row">
        <button id="crt-auto" class="active" onclick="setCrtSite(-1)">Auto-Browse</button>
        <button id="crt-0" onclick="setCrtSite(0)">goodwebsites.html</button>
        <button id="crt-1" onclick="setCrtSite(1)">zxc.cc</button>
        <button id="crt-2" onclick="setCrtSite(2)">biblefirst.com</button>
        <button id="crt-3" onclick="setCrtSite(3)">wxcs.com/rob</button>
      </div>
    </div>
    <div class="card">
      <h3>Adjust Position</h3>
      <p class="desc">Want to tweak the awkward 1st-person position? Open <a href="woo_cannon_pose_adjuster.html" style="color:#38bdf8;font-weight:700;">woo_cannon_pose_adjuster.html</a> to drag, rotate, scale, and export exact pose JSON.</p>
    </div>
  </aside>
</main>
<script>
const PAYLOAD = /*__PAYLOAD__*/null;

async function DecompressB64Gz(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const w = ds.writable.getWriter();
  w.write(bin); w.close();
  return await new Response(ds.readable).arrayBuffer();
}

let gl, prog, arenaBuf;
let gpuTextures = [], gpuData = {};
let curVariant = 'wew2', curSub = 'vm';
let povMode = false, fovDeg = 111, showWire = false, showRanger = true, showHud = false;
let playing = true, animMode = 'idle', animFrame = 0.0;
let charging = false, chargeVal = 0.0, spinTurntable = 0.0;
let orbitAz = 2.42, orbitEl = 0.24, orbitDist = 38.0, dragging = false, lx = 0, ly = 0;
let crtPinSite = -1, crtClock = 0.0;
let p3Clip = { id: 'stand', start: 12, end: 16, fps: 7 };

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
function mat4RotZ(rad) {
  const c = Math.cos(rad), s = Math.sin(rad);
  return new Float32Array([c,s,0,0, -s,c,0,0, 0,0,1,0, 0,0,0,1]);
}
function mat4Ident() {
  return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
}

function uploadModel(m) {
  if (!m) return null;
  const surfs = m.surfaces.map(s => {
    const mk = (slice, target) => {
      const b = gl.createBuffer();
      gl.bindBuffer(target, b);
      gl.bufferData(target, new Uint8Array(arenaBuf, slice[0], slice[1]), gl.STATIC_DRAW);
      return b;
    };
    return { ...s, bPos: mk(s.pos, gl.ARRAY_BUFFER), bNrm: mk(s.nrm, gl.ARRAY_BUFFER), bUV: mk(s.uv, gl.ARRAY_BUFFER), bTri: mk(s.tris, gl.ELEMENT_ARRAY_BUFFER), bEdg: mk(s.edges, gl.ELEMENT_ARRAY_BUFFER) };
  });
  return { ...m, surfs };
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
    if (t.nearest) {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    } else {
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    }
    gpuTextures.push(tex);
  }

  for (const k of ['rod', 'wew1', 'wew2']) {
    const src = PAYLOAD.variants[k];
    gpuData[k] = {
      ...src,
      models: {
        vm: uploadModel(src.models.vm),
        p3: uploadModel(src.models.p3),
        pk: uploadModel(src.models.pk),
      }
    };
  }

  setupControls(canvas);
  setVariant('wew2');
  requestAnimationFrame(loop);
}

function setupControls(canvas) {
  const btnC = document.getElementById('btn-charge');
  const startCharge = () => {
    if (curSub !== 'vm') setSub('vm');
    if (!charging && animMode !== 'blast') {
      charging = true; chargeVal = 0.0; playing = true;
      btnC.classList.add('charging');
    }
  };
  const endCharge = () => {
    if (charging) {
      charging = false; btnC.classList.remove('charging');
      animMode = 'blast'; animFrame = 26.0;
    }
  };
  btnC.addEventListener('mousedown', startCharge);
  window.addEventListener('mouseup', endCharge);
  window.addEventListener('keydown', e => { if (e.code === 'Space' && !e.repeat) { e.preventDefault(); startCharge(); } });
  window.addEventListener('keyup', e => { if (e.code === 'Space') { e.preventDefault(); endCharge(); } });

  document.getElementById('scrub').addEventListener('input', e => {
    playing = false; document.getElementById('btn-play').textContent = 'Play';
    animFrame = parseFloat(e.target.value);
  });

  canvas.addEventListener('mousedown', e => { if (!povMode || curSub !== 'vm') { dragging = true; lx = e.clientX; ly = e.clientY; } });
  window.addEventListener('mousemove', e => {
    if (!dragging) return;
    orbitAz -= (e.clientX - lx) * 0.008;
    orbitEl = Math.max(-1.25, Math.min(1.25, orbitEl + (e.clientY - ly) * 0.008));
    lx = e.clientX; ly = e.clientY;
  });
  window.addEventListener('mouseup', () => dragging = false);
  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    orbitDist = Math.max(12, Math.min(140, orbitDist + e.deltaY * 0.035));
  }, { passive: false });
}

function setVariant(v) {
  curVariant = v;
  ['rod', 'wew1', 'wew2'].forEach(k => document.getElementById('vtab-' + k).classList.toggle('active', k === v));
  const info = gpuData[v];
  const st = document.getElementById('subtabs');
  st.innerHTML = '';
  const subs = [['vm', '1st-Person Viewmodel (48f)']];
  if (info.models.p3) subs.push(['p3', '3rd-Person vwep + Ranger (259f)']);
  if (info.models.pk) subs.push(['pk', 'World Pickup']);
  for (const [sid, lbl] of subs) {
    const b = document.createElement('button');
    b.id = 'sub-' + sid; b.textContent = lbl;
    b.onclick = () => setSub(sid);
    st.appendChild(b);
  }
  document.getElementById('card-title').textContent = info.title;
  document.getElementById('card-desc').textContent = info.desc;
  document.getElementById('card-kvs').innerHTML = info.kvs.map(([k, val]) => `<div class="kv"><span>${k}</span><code>${val}</code></div>`).join('');
  document.getElementById('crt-card').style.display = (info.crt && info.crt.length) ? 'block' : 'none';
  setSub('vm');
}

function setSub(sid) {
  curSub = sid;
  playing = true; charging = false; animMode = 'idle';
  document.getElementById('btn-charge').classList.remove('charging');
  document.querySelectorAll('#subtabs button').forEach(b => b.classList.toggle('active-gold', b.id === 'sub-' + sid));
  const info = gpuData[curVariant];
  const m = info.models[sid];
  document.getElementById('scrub').max = Math.max(0, m.nf - 1);
  document.getElementById('geo-stat').textContent = `${m.nf} frames · ${m.nv} verts · ${m.nt} tris`;
  document.getElementById('btn-play').textContent = 'Pause';
  document.getElementById('p3-card').style.display = (sid === 'p3') ? 'block' : 'none';
  document.getElementById('btn-ranger').style.display = (sid === 'p3') ? 'inline-block' : 'none';
  document.getElementById('charge-hud').style.display = (sid === 'vm') ? 'block' : 'none';

  if (sid === 'vm') {
    animFrame = 0;
    orbitDist = (curVariant === 'rod') ? 48.0 : 38.0;
    orbitAz = 2.42; orbitEl = 0.24;
  } else if (sid === 'p3') {
    animFrame = p3Clip.start;
    povMode = false;
    orbitDist = 74.0; orbitAz = -0.68; orbitEl = 0.28;
  } else {
    animFrame = 0;
    povMode = false;
    orbitDist = (curVariant === 'rod') ? 54.0 : 42.0;
    orbitAz = -0.95; orbitEl = 0.28;
  }
  syncCamButtons();
}

function syncCamButtons() {
  const inPov = (curSub === 'vm' && povMode);
  document.getElementById('btn-orbit').classList.toggle('active', !inPov);
  document.getElementById('btn-pov111').classList.toggle('active', inPov && fovDeg === 111);
  document.getElementById('btn-pov90').classList.toggle('active', inPov && fovDeg === 90);
  document.getElementById('crosshair').style.display = (inPov || showHud) ? 'block' : 'none';
  document.getElementById('hud-strip').style.display = (inPov || showHud) ? 'flex' : 'none';
}

function setPov(deg) {
  if (curSub !== 'vm') setSub('vm');
  povMode = true; fovDeg = deg;
  syncCamButtons();
}
function setOrbit() {
  povMode = false;
  syncCamButtons();
}
function toggleWire() {
  showWire = !showWire;
  document.getElementById('btn-wire').textContent = 'Wireframe: ' + (showWire ? 'ON' : 'OFF');
}
function toggleRanger() {
  showRanger = !showRanger;
  document.getElementById('btn-ranger').textContent = 'Ranger Body: ' + (showRanger ? 'ON' : 'OFF');
}
function toggleHud() {
  showHud = !showHud;
  document.getElementById('btn-hud').textContent = 'Crosshair/HUD: ' + (showHud ? 'ON' : 'OFF');
  syncCamButtons();
}
function togglePlay() {
  playing = !playing;
  document.getElementById('btn-play').textContent = playing ? 'Pause' : 'Play';
}
function triggerFullCycle() {
  if (curSub !== 'vm') setSub('vm');
  playing = true; charging = false; animMode = 'full'; animFrame = 16.0;
  document.getElementById('btn-play').textContent = 'Pause';
}
function set3PClip(id, s, e, fps) {
  p3Clip = { id, start: s, end: e, fps };
  ['stand', 'run', 'blast', 'nail'].forEach(k => document.getElementById('p3-' + k).classList.toggle('active', k === id));
  if (curSub !== 'p3') setSub('p3');
  animFrame = s; playing = true;
}
function setCrtSite(idx) {
  crtPinSite = idx;
  document.getElementById('crt-auto').classList.toggle('active', idx === -1);
  for (let k = 0; k < 4; k++) document.getElementById('crt-' + k).classList.toggle('active', idx === k);
}

function drawModel(m, f0, f1, lerp, modelMat, vpMat, camPos, crtList) {
  const mvp = mat4Mul(vpMat, modelMat);
  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mvp);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uModel'), false, modelMat);
  gl.uniform3fv(gl.getUniformLocation(prog, 'uCamPos'), camPos);
  gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);

  for (const s of m.surfs) {
    if (s.name === 'ranger_body' && !showRanger) continue;
    if (s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE); gl.depthMask(false);
    } else {
      gl.disable(gl.BLEND); gl.depthMask(true);
    }
    let texIdx = s.tex;
    if (s.name === 'crt_screen' && crtList && crtList.length === 16) {
      const subStep = Math.floor(crtClock * 1.2) % 4;
      const crtFrame = (crtPinSite >= 0) ? (crtPinSite * 4 + subStep) : (Math.floor(crtClock * 1.1) % 16);
      texIdx = crtList[crtFrame];
    }
    gl.activeTexture(gl.TEXTURE0);
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

let lastT = performance.now(), jitterPh = 0.0;
function loop(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000.0);
  lastT = now;
  crtClock += dt;
  jitterPh += dt * 28.0;

  const canvas = document.getElementById('gl');
  const dpr = window.devicePixelRatio || 1;
  const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.036, 0.05, 0.085, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const info = gpuData[curVariant];
  const m = info.models[curSub];
  let f0 = 0, f1 = 0, lerp = 0.0;

  if (curSub === 'vm') {
    if (charging) {
      chargeVal = Math.min(1.0, chargeVal + dt / 1.25);
      animFrame = (curVariant === 'rod' && chargeVal >= 0.999)
        ? (24.4 + 0.55 * (0.5 + 0.5 * Math.sin(jitterPh)))
        : (16.0 + chargeVal * 9.0);
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      document.getElementById('hud-label').textContent = chargeVal >= 0.99
        ? 'AT MAX CHARGE! RELEASE TO FIRE!'
        : `CHARGING... ${(chargeVal*100)|0}%`;
    } else if (playing) {
      if (animMode === 'blast') {
        animFrame += dt * 20.0;
        if (animFrame >= 47.95) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else if (animMode === 'full') {
        animFrame += dt * (animFrame < 26.0 ? 9.5 : 20.0);
        chargeVal = animFrame < 26.0 ? (animFrame - 16.0) / 10.0 : Math.max(0, 1.0 - (animFrame - 26.0) * 0.18);
        if (animFrame >= 47.95) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else {
        animFrame = (animFrame + dt * 10.0) % 16.0;
        chargeVal = Math.max(0.0, chargeVal - dt * 2.5);
      }
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      document.getElementById('hud-label').textContent = (animMode === 'idle')
        ? 'READY · HOLD SPACE OR FIRE BUTTON'
        : (animFrame < 30 ? 'FIRING BLAST!' : (animFrame < 40 ? 'RECOIL RECOVERY' : 'RELOAD / BREECH LOCK'));
    }
    f0 = Math.max(0, Math.min(m.nf - 1, Math.floor(animFrame)));
    if (animMode === 'idle' && !charging && f0 === 15) f1 = 0;
    else f1 = (f0 + 1 < m.nf) ? f0 + 1 : 0;
    const noLerp = (curVariant !== 'rod' && (f0 === 15 || f0 === 29 || f0 === 30));
    lerp = noLerp ? 0.0 : (animFrame - Math.floor(animFrame));
  } else if (curSub === 'p3') {
    const span = (p3Clip.end - p3Clip.start + 1);
    if (playing) animFrame = p3Clip.start + ((animFrame - p3Clip.start + dt * p3Clip.fps) % span);
    f0 = Math.max(0, Math.min(m.nf - 1, Math.floor(animFrame)));
    f1 = (f0 >= p3Clip.start && f0 <= p3Clip.end) ? (p3Clip.start + ((f0 - p3Clip.start + 1) % span)) : ((f0 + 1) % m.nf);
    lerp = animFrame - Math.floor(animFrame);
  } else {
    if (playing && !dragging) spinTurntable += dt * 1.1;
  }

  document.getElementById('scrub').value = animFrame;
  const fnames = (curSub === 'vm') ? info.fn_vm : (curSub === 'p3' ? info.fn_p3 : ['pickup1']);
  const fname = fnames[f0] || ('f' + f0);
  document.getElementById('frame-lbl').textContent = `f${String(f0).padStart(2,'0')} · ${fname}`;

  const asp = w / Math.max(1, h);
  let camPos, viewMat, projMat, modelMat = mat4Ident();
  if (curSub === 'vm' && povMode) {
    // DarkPlaces / Zircon 4:3-normalized FOV
    const ty = Math.tan(fovDeg * Math.PI / 360.0) * 0.75;
    const fovY = 2.0 * Math.atan(ty);
    projMat = mat4Persp(fovY, asp, 0.5, 900.0);
    camPos = [0, 0, 0];
    viewMat = mat4LookAt(camPos, [20, 0, 0], [0, 0, 1]);
  } else {
    projMat = mat4Persp(48.0 * Math.PI / 180.0, asp, 0.5, 900.0);
    const ctr = (curSub === 'vm') ? info.orbitCtr : (curSub === 'p3' ? [2, 0, 8] : info.pkCtr);
    camPos = [
      ctr[0] + orbitDist * Math.cos(orbitEl) * Math.cos(orbitAz),
      ctr[1] + orbitDist * Math.cos(orbitEl) * Math.sin(orbitAz),
      ctr[2] + orbitDist * Math.sin(orbitEl)
    ];
    viewMat = mat4LookAt(camPos, ctr, [0, 0, 1]);
    if (curSub === 'pk') modelMat = mat4RotZ(spinTurntable);
  }
  const vpMat = mat4Mul(projMat, viewMat);
  drawModel(m, f0, f1, lerp, modelMat, vpMat, camPos, info.crt);
  requestAnimationFrame(loop);
}
init();
</script>
</body>
</html>
"""


ADJUSTER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Woo Cannon · 1st-Person Pose Adjuster</title>
<style>
  :root {
    --bg:#12100e; --panel:#1b1815; --panel2:#24201c; --line:#3a332c; --fg:#efe8dc; --dim:#a39a8d;
    --accent:#ffb13b; --accent-ink:#1c1100; --ok:#7fd18b; --warn:#ff7a5c; --acc2:#38bdf8;
    --mono:ui-monospace,"IBM Plex Mono",Consolas,monospace; --sans:"Segoe UI",system-ui,sans-serif;
    color-scheme:dark;
  }
  * { box-sizing:border-box; }
  html, body { height:100%; }
  body { margin:0; background:var(--bg); color:var(--fg); font:13.5px/1.4 var(--sans); padding:10px 14px; display:flex; flex-direction:column; gap:9px; }
  header { display:flex; flex-wrap:wrap; gap:8px 12px; align-items:center; }
  h1 { margin:0; font:800 18px var(--sans); letter-spacing:.02em; }
  h1 small { font:400 12px var(--mono); color:var(--dim); margin-left:8px; }
  select, input[type=number], button, textarea { font:12.5px var(--mono); color:var(--fg); background:var(--panel2); border:1px solid var(--line); border-radius:5px; padding:5px 8px; }
  button { cursor:pointer; }
  button:hover { border-color:var(--accent); }
  button.primary { background:var(--accent); color:var(--accent-ink); border-color:var(--accent); font-weight:700; }
  button.fire { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-weight:700; }
  button.fire.charging { background:linear-gradient(135deg,#38bdf8,#ffffff); color:#06101e; }
  button.on { background:var(--acc2); color:#06101e; border-color:var(--acc2); font-weight:700; }
  main { flex:1; min-height:0; display:grid; grid-template-columns:minmax(0,1fr) 370px; gap:12px; }
  #stage { background:#080706; border:1px solid var(--line); border-radius:8px; display:flex; align-items:center; justify-content:center; min-height:360px; overflow:hidden; position:relative; }
  #frame { position:relative; max-width:100%; max-height:100%; width:100%; aspect-ratio:16/9; cursor:grab; touch-action:none; }
  #frame.drag { cursor:grabbing; }
  canvas { display:block; width:100%; height:100%; }
  #hud { position:absolute; left:0; right:0; bottom:0; height:14%; background:repeating-linear-gradient(135deg, rgba(0,0,0,.48) 0 8px, rgba(0,0,0,.26) 8px 16px); border-top:1px dashed rgba(255,255,255,.35); color:rgba(255,255,255,.72); font:11px var(--mono); display:flex; align-items:center; justify-content:center; pointer-events:none; }
  #cross { position:absolute; left:50%; top:50%; width:16px; height:16px; margin:-8px 0 0 -8px; pointer-events:none; }
  #cross::before, #cross::after { content:""; position:absolute; background:#4ade80; box-shadow:0 0 4px #000; }
  #cross::before { left:7px; top:0; width:2px; height:16px; } #cross::after { top:7px; left:0; height:2px; width:16px; }
  #tip { position:absolute; left:8px; top:8px; font:11px/1.45 var(--mono); color:rgba(255,255,255,.82); background:rgba(0,0,0,.58); padding:5px 9px; border-radius:5px; pointer-events:none; max-width:calc(100% - 16px); }
  #diag { position:absolute; right:8px; bottom:15%; font:11px/1.45 var(--mono); color:#e2e8f0; background:rgba(10,14,23,.82); border:1px solid #334155; padding:6px 9px; border-radius:6px; pointer-events:none; }
  aside { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:11px; overflow:auto; display:flex; flex-direction:column; gap:10px; }
  fieldset { border:1px solid var(--line); border-radius:6px; margin:0; padding:7px 10px 9px; }
  legend { color:var(--dim); font:600 11px var(--mono); letter-spacing:.08em; text-transform:uppercase; padding:0 6px; }
  .row { display:grid; grid-template-columns:56px 1fr 72px; gap:7px; align-items:center; margin-top:5px; }
  .row label { color:var(--dim); font:12px var(--mono); }
  .row input[type=range] { width:100%; accent-color:var(--accent); }
  .row input[type=number] { width:72px; padding:4px 5px; }
  .nudge { display:grid; grid-template-columns:repeat(4,1fr); gap:5px; margin-top:7px; }
  .nudge button { padding:5px 2px; font-size:11.5px; }
  .btns { display:flex; flex-wrap:wrap; gap:6px; margin-top:7px; }
  .chk { display:flex; align-items:center; gap:6px; color:var(--dim); font:12px var(--mono); margin-top:4px; }
  .chk input { accent-color:var(--accent); }
  #out { width:100%; height:96px; background:var(--panel2); color:var(--fg); border:1px solid var(--line); border-radius:5px; font:11px var(--mono); padding:6px; resize:vertical; margin-top:6px; }
  .note { color:var(--dim); font:11.5px/1.45 var(--mono); }
  .warn-txt { color:var(--warn); }
  .ok-txt { color:var(--ok); }
  @media (max-width: 920px) { main { grid-template-columns:1fr; } aside { max-height:none; } }
</style>
</head>
<body>
<header>
  <h1>Woo Cannon Pose Adjuster<small>100% offline WebGL2 · exact game FOV &amp; pivot math</small></h1>
  <select id="model" aria-label="Woo Cannon variant"></select>
  <select id="aspect" aria-label="Screen aspect">
    <option value="1.7778">16:9</option>
    <option value="1.6">16:10</option>
    <option value="1.3333">4:3</option>
    <option value="2.3333">21:9</option>
  </select>
  <label class="chk" style="margin:0">game fov <input id="fov" type="number" min="60" max="135" step="1" value="111" style="width:60px"></label>
  <span id="fovinfo" class="note"></span>
  <button id="btn-cam" title="Switch between 1st-person game camera and Peek 3D Orbit">Cam: 1st-Person POV</button>
  <button id="btn-fire" class="fire">Hold Space / Fire Test</button>
</header>
<main>
  <div id="stage">
    <div id="frame">
      <canvas id="gl"></canvas>
      <div id="cross"></div>
      <div id="hud">status bar strip (bottom 14%)</div>
      <div id="tip">drag = move left/right/up/down · wheel = closer/farther · shift-drag / right-drag = yaw &amp; pitch · ctrl-drag = roll · alt-wheel = scale · arrows/PgUp/PgDn = nudge</div>
      <div id="diag"></div>
    </div>
  </div>
  <aside>
    <fieldset><legend>Position (Quake eye units)</legend>
      <div class="row"><label>forward</label><input type="range" id="r_px" min="-25" max="45" step="0.1"><input type="number" id="n_px" step="0.1"></div>
      <div class="row"><label>left</label><input type="range" id="r_py" min="-35" max="35" step="0.1"><input type="number" id="n_py" step="0.1"></div>
      <div class="row"><label>up</label><input type="range" id="r_pz" min="-35" max="35" step="0.1"><input type="number" id="n_pz" step="0.1"></div>
      <div class="nudge">
        <button data-n="py" data-d="1">← left</button><button data-n="py" data-d="-1">right →</button>
        <button data-n="pz" data-d="1">↑ up</button><button data-n="pz" data-d="-1">↓ down</button>
        <button data-n="px" data-d="-1">closer</button><button data-n="px" data-d="1">farther</button>
        <label class="chk" style="margin:0 0 0 4px;grid-column:span 2">step <input id="step" type="number" min="0.1" max="10" step="0.1" value="1" style="width:52px;padding:3px 4px"></label>
      </div>
    </fieldset>
    <fieldset><legend>Rotation (degrees around pivot)</legend>
      <div class="row"><label>roll</label><input type="range" id="r_rr" min="-180" max="180" step="0.5"><input type="number" id="n_rr" step="0.5"></div>
      <div class="row"><label>pitch</label><input type="range" id="r_rp" min="-180" max="180" step="0.5"><input type="number" id="n_rp" step="0.5"></div>
      <div class="row"><label>yaw</label><input type="range" id="r_ry" min="-180" max="180" step="0.5"><input type="number" id="n_ry" step="0.5"></div>
      <div class="note" style="margin-top:4px">pitch + = nose up · yaw + = turn left · roll + = top rolls left</div>
    </fieldset>
    <fieldset><legend>Size</legend>
      <div class="row"><label>scale</label><input type="range" id="r_s" min="0.25" max="2.5" step="0.01"><input type="number" id="n_s" step="0.01"></div>
    </fieldset>
    <fieldset><legend>Animation</legend>
      <div class="row" style="grid-template-columns:56px 1fr"><label>clip</label>
        <select id="clip">
          <option value="idle">Idle Sway (0–15)</option>
          <option value="charge">Charge / Flex (16–25)</option>
          <option value="blast">Blast &amp; Recoil (26–47)</option>
          <option value="all">All Frames (0–47)</option>
        </select>
      </div>
      <div class="row"><label>frame</label><input type="range" id="r_f" min="0" max="15" step="1"><input type="number" id="n_f" step="1" min="0"></div>
      <div class="btns"><button id="play">▶ play</button><button id="prev">◀</button><button id="next">▶</button></div>
    </fieldset>
    <fieldset><legend>View &amp; Guides</legend>
      <label class="chk"><input type="checkbox" id="c_hud" checked> status bar strip + crosshair</label>
      <label class="chk"><input type="checkbox" id="c_ghost" checked> cyan ghost of unedited game pose</label>
      <label class="chk"><input type="checkbox" id="c_dummy" checked> player-sized target dummy at 200u</label>
      <label class="chk"><input type="checkbox" id="c_wire"> wireframe overlay</label>
      <div class="note" style="margin-top:4px"><a href="woo_cannon_models.html" style="color:#38bdf8;">Open All Woo Cannon Models Inspector →</a></div>
    </fieldset>
    <fieldset><legend>Export Pose JSON</legend>
      <div class="btns">
        <button id="reset">reset model</button>
        <button id="dl" class="primary">download JSON</button>
        <button id="copy">copy JSON</button>
      </div>
      <textarea id="out" readonly spellcheck="false" aria-label="pose JSON"></textarea>
      <div class="note" id="save-status" style="margin-top:4px">Saved automatically in browser. Paste JSON in chat or download when happy.</div>
    </fieldset>
  </aside>
</main>
<script>
const PAYLOAD = /*__PAYLOAD__*/null;

async function DecompressB64Gz(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const w = ds.writable.getWriter();
  w.write(bin); w.close();
  return await new Response(ds.readable).arrayBuffer();
}

const $ = id => document.getElementById(id);
const ID_POSE = () => ({ pos:[0,0,0], rot:[0,0,0], scale:1 });
const clonePose = p => ({ pos:p.pos.slice(), rot:p.rot.slice(), scale:p.scale });
const samePose = (a,b) => a.scale===b.scale && a.pos.every((v,i)=>v===b.pos[i]) && a.rot.every((v,i)=>v===b.rot[i]);
const r2 = v => Math.round(v * 100) / 100;

let gl, prog, flatProg, arenaBuf;
let gpuTextures = [], models = {}, worldGeo = {};
let cur = 'wew2';
const edits = {};
let peekOrbit = false, orbitAz = 2.4, orbitEl = 0.25, orbitDist = 42.0;
let playing = false, charging = false, chargeVal = 0.0, animMode = 'idle', frameF = 0.0;
let crtClock = 0.0;

const STORAGE_KEY = 'woo_pose_adj_v1';
for (const k of Object.keys(PAYLOAD.models)) edits[k] = ID_POSE();
try {
  const sv = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  if (sv.cur && PAYLOAD.models[sv.cur]) cur = sv.cur;
  if (sv.edits) for (const k of Object.keys(edits)) if (sv.edits[k]) edits[k] = clonePose(sv.edits[k]);
} catch (e) {}
function persist() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ cur, edits })); } catch (e) {} }

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
uniform float uMetallic, uRough, uUnlit, uPassMode; // 0=normal, 1=wire, 2=ghost
out vec4 fragColor;
void main() {
  if (uPassMode > 1.5) { fragColor = vec4(0.22, 0.82, 1.0, 0.28); return; }
  if (uPassMode > 0.5) { fragColor = vec4(0.98, 0.72, 0.22, 0.55); return; }
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
  vec3 R = reflect(-V, N);
  float env = 0.55 + 0.45 * sin(R.z * 3.8 + 0.4);
  vec3 lit = tx.rgb * (0.36 + 0.72 * d1 + 0.28 * d2) + tx.rgb * uMetallic * 0.28 * env + vec3(0.92, 0.96, 1.0) * spec;
  fragColor = vec4(lit, tx.a);
}`;

const FLAT_VS = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;
uniform mat4 uMVP;
out vec3 vNrm, vPos;
out vec2 vUV;
void main() {
  vPos = aPos; vNrm = aNrm; vUV = aUV;
  gl_Position = uMVP * vec4(aPos, 1.0);
}`;

const FLAT_FS = `#version 300 es
precision highp float;
in vec3 vNrm, vPos;
in vec2 vUV;
uniform vec4 uColor;
uniform float uCheck;
out vec4 fragColor;
void main() {
  vec3 col = uColor.rgb;
  if (uCheck > 0.5) {
    float cx = floor(vPos.x / 32.0);
    float cy = floor(vPos.y / 32.0);
    float ch = mod(cx + cy, 2.0);
    col = mix(vec3(0.17,0.17,0.19), vec3(0.29,0.29,0.31), ch);
  }
  vec3 N = normalize(vNrm);
  float d = 0.55 + 0.45 * max(dot(N, normalize(vec3(-0.4, 0.3, 0.8))), 0.0);
  float fog = clamp((length(vPos) - 180.0) / 1400.0, 0.0, 1.0);
  vec3 bg = vec3(0.35, 0.41, 0.49);
  fragColor = vec4(mix(col * d, bg, fog), uColor.a);
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

// Exact match to apply_viewmodel_edits.py make_xform:
// q = pivot + pos + R_z(yaw) * R_y_up(pitch) * R_x(roll) * scale * (p - pivot)
function buildPoseMatrix(pivot, e) {
  const [r, p, y] = e.rot.map(a => a * Math.PI / 180.0);
  const cr = Math.cos(r), sr = Math.sin(r);
  const cp = Math.cos(p), sp = Math.sin(p);
  const cy = Math.cos(y), sy = Math.sin(y);

  const rotVec = (vx, vy, vz) => {
    let a = vy * cr - vz * sr, b = vy * sr + vz * cr; vy = a; vz = b;
    a = vx * cp - vz * sp; b = vx * sp + vz * cp; vx = a; vz = b;
    a = vx * cy - vy * sy; b = vx * sy + vy * cy; vx = a; vy = b;
    return [vx, vy, vz];
  };
  const s = e.scale;
  const c0 = rotVec(s, 0, 0), c1 = rotVec(0, s, 0), c2 = rotVec(0, 0, s);
  const t0 = rotVec(-pivot[0] * s, -pivot[1] * s, -pivot[2] * s);
  const tx = pivot[0] + e.pos[0] + t0[0];
  const ty = pivot[1] + e.pos[1] + t0[1];
  const tz = pivot[2] + e.pos[2] + t0[2];
  return new Float32Array([
    c0[0], c0[1], c0[2], 0,
    c1[0], c1[1], c1[2], 0,
    c2[0], c2[1], c2[2], 0,
    tx,    ty,    tz,    1
  ]);
}

function transformPoint(pivot, e, pt) {
  const [r, p, y] = e.rot.map(a => a * Math.PI / 180.0);
  const cr = Math.cos(r), sr = Math.sin(r);
  const cp = Math.cos(p), sp = Math.sin(p);
  const cy = Math.cos(y), sy = Math.sin(y);
  let vx = (pt[0] - pivot[0]) * e.scale;
  let vy = (pt[1] - pivot[1]) * e.scale;
  let vz = (pt[2] - pivot[2]) * e.scale;
  let a = vy * cr - vz * sr, b = vy * sr + vz * cr; vy = a; vz = b;
  a = vx * cp - vz * sp; b = vx * sp + vz * cp; vx = a; vz = b;
  a = vx * cy - vy * sy; b = vx * sy + vy * cy; vx = a; vy = b;
  return [pivot[0] + vx + e.pos[0], pivot[1] + vy + e.pos[1], pivot[2] + vz + e.pos[2]];
}

function makeWorldGeo() {
  const makeBuf = (arr, target) => { const b = gl.createBuffer(); gl.bindBuffer(target, b); gl.bufferData(target, arr, gl.STATIC_DRAW); return b; };
  // Floor at z = -22
  const fv = new Float32Array([
    -1500,-1500,-22, 0,0,1, 0,0,
     1500,-1500,-22, 0,0,1, 1,0,
     1500, 1500,-22, 0,0,1, 1,1,
    -1500, 1500,-22, 0,0,1, 0,1
  ]);
  const fi = new Uint16Array([0,1,2, 0,2,3]);
  worldGeo.floor = { v: makeBuf(fv, gl.ARRAY_BUFFER), i: makeBuf(fi, gl.ELEMENT_ARRAY_BUFFER), n: 6 };

  // Box helper for dummy at x=200, y=0, z=-22..+34 (32x32x56 Quake player size)
  function boxGeo(x0,x1, y0,y1, z0,z1) {
    const faces = [
      [[x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1],[-1,0,0]],
      [[x1,y1,z0],[x1,y0,z0],[x1,y0,z1],[x1,y1,z1],[1,0,0]],
      [[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1],[0,1,0]],
      [[x1,y0,z0],[x0,y0,z0],[x0,y0,z1],[x1,y0,z1],[0,-1,0]],
      [[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],[0,0,1]],
      [[x0,y1,z0],[x1,y1,z0],[x1,y0,z0],[x0,y0,z0],[0,0,-1]],
    ];
    const v = [], idx = [];
    faces.forEach((f, fi) => {
      const base = fi * 4;
      for (let k = 0; k < 4; k++) v.push(f[k][0], f[k][1], f[k][2], f[4][0], f[4][1], f[4][2], 0, 0);
      idx.push(base, base+1, base+2, base, base+2, base+3);
    });
    return { v: makeBuf(new Float32Array(v), gl.ARRAY_BUFFER), i: makeBuf(new Uint16Array(idx), gl.ELEMENT_ARRAY_BUFFER), n: idx.length };
  }
  worldGeo.dummy = boxGeo(184, 216, -16, 16, -22, 34);
  worldGeo.eyeBox = boxGeo(-0.7, 0.7, -0.7, 0.7, -0.7, 0.7);
}

async function init() {
  const canvas = $('gl');
  gl = canvas.getContext('webgl2', { antialias: true });
  prog = compile(VS, FS);
  flatProg = compile(FLAT_VS, FLAT_FS);
  arenaBuf = await DecompressB64Gz(PAYLOAD.binGz);
  makeWorldGeo();

  for (const t of PAYLOAD.textures) {
    const img = new Image(); img.src = t.uri; await img.decode();
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gpuTextures.push(tex);
  }

  for (const [k, info] of Object.entries(PAYLOAD.models)) {
    const surfs = info.md3.surfaces.map(s => {
      const mk = (slice, target) => {
        const b = gl.createBuffer(); gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(arenaBuf, slice[0], slice[1]), gl.STATIC_DRAW);
        return b;
      };
      return { ...s, bPos: mk(s.pos, gl.ARRAY_BUFFER), bNrm: mk(s.nrm, gl.ARRAY_BUFFER), bUV: mk(s.uv, gl.ARRAY_BUFFER), bTri: mk(s.tris, gl.ELEMENT_ARRAY_BUFFER), bEdg: mk(s.edges, gl.ELEMENT_ARRAY_BUFFER) };
    });
    models[k] = { ...info, surfs };
    const opt = new Option(info.label, k);
    $('model').add(opt);
  }
  $('model').value = cur;

  setupUI();
  fovAspect();
  refreshUI();
  requestAnimationFrame(loop);
}

const FIELDS = [["px", e => e.pos, 0], ["py", e => e.pos, 1], ["pz", e => e.pos, 2], ["rr", e => e.rot, 0], ["rp", e => e.rot, 1], ["ry", e => e.rot, 2]];

function updateDiag() {
  const info = models[cur], e = edits[cur];
  const corners = [];
  for (const x of [info.lo[0], info.hi[0]])
    for (const y of [info.lo[1], info.hi[1]])
      for (const z of [info.lo[2], info.hi[2]])
        corners.push(transformPoint(info.pivot, e, [x, y, z]));
  const xs = corners.map(c => c[0]), ys = corners.map(c => c[1]), zs = corners.map(c => c[2]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys), z0 = Math.min(...zs), z1 = Math.max(...zs);
  const flags = [];
  if (x0 < 2.5) flags.push(`<span class="warn-txt">near camera (minX=${x0.toFixed(1)}u)</span>`);
  if (y0 < 0 && y1 > 0 && z1 > -2.5) flags.push(`<span class="warn-txt">crosses center sightline (Y=[${y0.toFixed(1)},${y1.toFixed(1)}])</span>`);
  if (flags.length === 0) flags.push(`<span class="ok-txt">sightline clear</span>`);
  $('diag').innerHTML = `bounds X:[${x0.toFixed(1)},${x1.toFixed(1)}] Y:[${y0.toFixed(1)},${y1.toFixed(1)}] Z:[${z0.toFixed(1)},${z1.toFixed(1)}]<br>${flags.join(' · ')}`;
}

function refreshUI() {
  const e = edits[cur];
  for (const [id, get, i] of FIELDS) {
    $('r_' + id).value = get(e)[i];
    $('n_' + id).value = r2(get(e)[i]);
  }
  $('r_s').value = e.scale; $('n_s').value = r2(e.scale);

  const json = {};
  for (const k of Object.keys(models)) {
    if (!samePose(edits[k], ID_POSE()) || k === cur) {
      json[models[k].exportKey] = {
        pos: edits[k].pos.map(r2),
        rot: edits[k].rot.map(r2),
        scale: r2(edits[k].scale),
      };
    }
  }
  $('out').value = JSON.stringify(json, null, 1);
  updateDiag();
  persist();
}

function fovAspect() {
  const asp = +$('aspect').value, f = (+$('fov').value || 111) * Math.PI / 180;
  const ty = Math.tan(f / 2) * 0.75, vfov = 2 * Math.atan(ty) * 180 / Math.PI, hfov = 2 * Math.atan(ty * asp) * 180 / Math.PI;
  $('fovinfo').textContent = `= ${hfov.toFixed(1)}°W / ${vfov.toFixed(1)}°H`;
  $('frame').style.aspectRatio = asp;
}

function clipRange() {
  const v = $('clip').value;
  if (v === 'idle') return [0, 15, 10, true];
  if (v === 'charge') return [16, 25, 10, false];
  if (v === 'blast') return [26, 47, 20, false];
  return [0, 47, 14, true];
}

function setupUI() {
  for (const [id, get, i] of FIELDS) {
    const fn = ev => { const v = parseFloat(ev.target.value); if (!isNaN(v)) { get(edits[cur])[i] = v; refreshUI(); } };
    $('r_' + id).addEventListener('input', fn);
    $('n_' + id).addEventListener('change', fn);
  }
  const sFn = ev => { const v = parseFloat(ev.target.value); if (v > 0) { edits[cur].scale = v; refreshUI(); } };
  $('r_s').addEventListener('input', sFn); $('n_s').addEventListener('change', sFn);

  document.querySelectorAll('.nudge button').forEach(b => {
    b.addEventListener('click', () => {
      const k = b.dataset.n, d = +b.dataset.d, step = +$('step').value || 1;
      const idx = k === 'px' ? 0 : k === 'py' ? 1 : 2;
      edits[cur].pos[idx] += d * step;
      refreshUI();
    });
  });

  $('model').addEventListener('change', () => { cur = $('model').value; refreshUI(); });
  $('aspect').addEventListener('change', fovAspect);
  $('fov').addEventListener('change', fovAspect);
  $('c_hud').addEventListener('change', () => {
    const show = $('c_hud').checked && !peekOrbit;
    $('hud').style.display = show ? 'flex' : 'none';
    $('cross').style.display = show ? 'block' : 'none';
  });

  $('btn-cam').addEventListener('click', () => {
    peekOrbit = !peekOrbit;
    $('btn-cam').textContent = peekOrbit ? 'Cam: Peek 3D Orbit' : 'Cam: 1st-Person POV';
    $('btn-cam').classList.toggle('on', peekOrbit);
    const show = $('c_hud').checked && !peekOrbit;
    $('hud').style.display = show ? 'flex' : 'none';
    $('cross').style.display = show ? 'block' : 'none';
  });

  const btnF = $('btn-fire');
  const startFire = () => { if (!charging && animMode !== 'blast') { charging = true; chargeVal = 0; playing = true; btnF.classList.add('charging'); } };
  const endFire = () => { if (charging) { charging = false; btnF.classList.remove('charging'); animMode = 'blast'; frameF = 26.0; } };
  btnF.addEventListener('mousedown', startFire);
  window.addEventListener('mouseup', endFire);

  $('clip').addEventListener('change', () => {
    const [a, b] = clipRange();
    $('r_f').min = $('n_f').min = a; $('r_f').max = $('n_f').max = b;
    frameF = a; $('r_f').value = $('n_f').value = a;
  });
  $('r_f').addEventListener('input', e => { playing = false; $('play').textContent = '▶ play'; frameF = +e.target.value; $('n_f').value = frameF; });
  $('n_f').addEventListener('change', e => { playing = false; $('play').textContent = '▶ play'; frameF = +e.target.value; $('r_f').value = frameF; });
  $('play').addEventListener('click', () => { playing = !playing; animMode = 'clip'; $('play').textContent = playing ? '❚❚ pause' : '▶ play'; });
  $('prev').addEventListener('click', () => { const [a,b] = clipRange(); playing = false; $('play').textContent = '▶ play'; frameF = Math.max(a, Math.min(b, Math.round(frameF)-1)); $('r_f').value = $('n_f').value = frameF; });
  $('next').addEventListener('click', () => { const [a,b] = clipRange(); playing = false; $('play').textContent = '▶ play'; frameF = Math.max(a, Math.min(b, Math.round(frameF)+1)); $('r_f').value = $('n_f').value = frameF; });

  $('reset').addEventListener('click', () => { edits[cur] = ID_POSE(); refreshUI(); });
  $('copy').addEventListener('click', () => {
    $('out').select();
    navigator.clipboard && navigator.clipboard.writeText($('out').value).catch(() => document.execCommand('copy'));
    $('save-status').textContent = 'Copied pose JSON to clipboard!';
  });
  $('dl').addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([$('out').value], { type: 'application/json' }));
    a.download = 'woo_cannon_pose.json'; a.click();
    $('save-status').textContent = 'Downloaded woo_cannon_pose.json!';
  });

  // Direct mouse drag & wheel in the viewport
  const frameEl = $('frame');
  let drag = null;
  frameEl.addEventListener('contextmenu', e => e.preventDefault());
  frameEl.addEventListener('pointerdown', e => {
    frameEl.setPointerCapture(e.pointerId);
    drag = {
      x: e.clientX, y: e.clientY,
      mode: peekOrbit ? 'orbit' : (e.ctrlKey ? 'roll' : (e.shiftKey || e.button === 2) ? 'turn' : 'move')
    };
    frameEl.classList.add('drag');
  });
  frameEl.addEventListener('pointerup', () => { drag = null; frameEl.classList.remove('drag'); });
  frameEl.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.mode === 'orbit') {
      orbitAz -= dx * 0.008;
      orbitEl = Math.max(-1.25, Math.min(1.25, orbitEl + dy * 0.008));
      return;
    }
    const E = edits[cur];
    if (drag.mode === 'move') {
      const f = (+$('fov').value || 111) * Math.PI / 180;
      const vfov = 2 * Math.atan(Math.tan(f / 2) * 0.75);
      const depth = Math.max(6, models[cur].pivot[0] + E.pos[0]);
      const perPx = 2 * Math.tan(vfov / 2) * depth / Math.max(1, frameEl.clientHeight);
      E.pos[1] -= dx * perPx;
      E.pos[2] -= dy * perPx;
    } else if (drag.mode === 'turn') {
      E.rot[2] -= dx * 0.35;
      E.rot[1] -= dy * 0.35;
    } else {
      E.rot[0] += dx * 0.35;
    }
    refreshUI();
  });
  frameEl.addEventListener('wheel', e => {
    e.preventDefault();
    if (peekOrbit) {
      orbitDist = Math.max(12, Math.min(120, orbitDist + e.deltaY * 0.035));
      return;
    }
    const E = edits[cur], d = Math.sign(-e.deltaY);
    if (e.altKey) E.scale = Math.max(0.2, E.scale * (1 + 0.03 * d));
    else E.pos[0] += d * (e.shiftKey ? 0.25 : 1.0);
    refreshUI();
  }, { passive: false });

  window.addEventListener('keydown', e => {
    if (e.code === 'Space' && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
      if (!e.repeat) { e.preventDefault(); startFire(); }
      return;
    }
    if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName) && document.activeElement.type !== 'range') return;
    const E = edits[cur], s = e.shiftKey ? 0.1 : 0.5;
    let hit = true;
    if (e.key === 'ArrowLeft') E.pos[1] += s;
    else if (e.key === 'ArrowRight') E.pos[1] -= s;
    else if (e.key === 'ArrowUp') E.pos[2] += s;
    else if (e.key === 'ArrowDown') E.pos[2] -= s;
    else if (e.key === 'PageUp') E.pos[0] += s;
    else if (e.key === 'PageDown') E.pos[0] -= s;
    else hit = false;
    if (hit) { e.preventDefault(); refreshUI(); }
  });
  window.addEventListener('keyup', e => { if (e.code === 'Space') endFire(); });
}

function drawFlatObj(obj, vpMat, color, check) {
  gl.useProgram(flatProg);
  gl.uniformMatrix4fv(gl.getUniformLocation(flatProg, 'uMVP'), false, vpMat);
  gl.uniform4fv(gl.getUniformLocation(flatProg, 'uColor'), color);
  gl.uniform1f(gl.getUniformLocation(flatProg, 'uCheck'), check ? 1.0 : 0.0);
  gl.bindBuffer(gl.ARRAY_BUFFER, obj.v);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, obj.i);
  gl.drawElements(gl.TRIANGLES, obj.n, gl.UNSIGNED_SHORT, 0);
}

function drawWeapon(info, f0, f1, lerp, modelMat, vpMat, camPos, passMode) {
  const mvp = mat4Mul(vpMat, modelMat);
  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mvp);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uModel'), false, modelMat);
  gl.uniform3fv(gl.getUniformLocation(prog, 'uCamPos'), camPos);
  gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);

  for (const s of info.surfs) {
    if (passMode === 2 && s.additive) continue;
    if (passMode === 2) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
    } else if (s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE); gl.depthMask(false);
    } else {
      gl.disable(gl.BLEND); gl.depthMask(true);
    }
    let texIdx = s.tex;
    if (s.name === 'crt_screen' && info.crt && info.crt.length === 16) {
      texIdx = info.crt[Math.floor(crtClock * 1.2) % 16];
    }
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, gpuTextures[texIdx]);
    gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uMetallic'), s.metallic);
    gl.uniform1f(gl.getUniformLocation(prog, 'uRough'), s.rough);
    gl.uniform1f(gl.getUniformLocation(prog, 'uUnlit'), s.unlit ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uPassMode'), passMode);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bPos);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.SHORT, false, 0, f0 * s.nv * 6);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 3, gl.SHORT, false, 0, f1 * s.nv * 6);
    gl.bindBuffer(gl.ARRAY_BUFFER, s.bNrm);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.BYTE, false, 0, f0 * s.nv * 3);
    gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.BYTE, false, 0, f1 * s.nv * 3);
    gl.bindBuffer(gl.ARRAY_BUFFER, s.bUV);
    gl.enableVertexAttribArray(4); gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);

    if (passMode === 1 || passMode === 2) {
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bEdg);
      gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
    } else {
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bTri);
      gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
    }
  }
  gl.depthMask(true); gl.disable(gl.BLEND);
}

let lastT = performance.now();
function loop(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000.0);
  lastT = now;
  crtClock += dt;

  const canvas = $('gl');
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.35, 0.41, 0.49, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  if (charging) {
    chargeVal = Math.min(1.0, chargeVal + dt / 1.25);
    frameF = 16.0 + chargeVal * 9.0;
  } else if (playing) {
    if (animMode === 'blast') {
      frameF += dt * 20.0;
      if (frameF >= 47.95) { animMode = 'clip'; frameF = 0.0; playing = false; $('play').textContent = '▶ play'; }
    } else {
      const [a, b, fps, lp] = clipRange();
      frameF += dt * fps;
      if (frameF > b) frameF = lp ? a + (frameF - a) % Math.max(1, b - a + 1) : a;
    }
    $('r_f').value = Math.floor(frameF); $('n_f').value = Math.floor(frameF);
  }

  const info = models[cur];
  const nf = info.md3.nf;
  const f0 = Math.max(0, Math.min(nf - 1, Math.floor(frameF)));
  const f1 = (f0 + 1 < nf) ? f0 + 1 : 0;
  const lerp = frameF - Math.floor(frameF);

  const asp = w / Math.max(1, h);
  let camPos, viewMat, projMat;
  if (!peekOrbit) {
    const f = (+$('fov').value || 111) * Math.PI / 180;
    const vfov = 2 * Math.atan(Math.tan(f / 2) * 0.75);
    projMat = mat4Persp(vfov, asp, 0.5, 4000.0);
    camPos = [0, 0, 0];
    viewMat = mat4LookAt(camPos, [20, 0, 0], [0, 0, 1]);
  } else {
    projMat = mat4Persp(48 * Math.PI / 180, asp, 0.5, 4000.0);
    const ctr = info.pivot;
    camPos = [
      ctr[0] + orbitDist * Math.cos(orbitEl) * Math.cos(orbitAz),
      ctr[1] + orbitDist * Math.cos(orbitEl) * Math.sin(orbitAz),
      ctr[2] + orbitDist * Math.sin(orbitEl)
    ];
    viewMat = mat4LookAt(camPos, ctr, [0, 0, 1]);
  }
  const vpMat = mat4Mul(projMat, viewMat);

  drawFlatObj(worldGeo.floor, vpMat, [0.3,0.3,0.3,1], true);
  if ($('c_dummy').checked) drawFlatObj(worldGeo.dummy, vpMat, [0.71,0.38,0.29,1], false);
  if (peekOrbit) drawFlatObj(worldGeo.eyeBox, vpMat, [0.25,0.95,0.45,1], false);

  if ($('c_ghost').checked && !samePose(edits[cur], ID_POSE())) {
    const ghostMat = buildPoseMatrix(info.pivot, ID_POSE());
    drawWeapon(info, f0, f1, lerp, ghostMat, vpMat, camPos, 2);
  }
  const modelMat = buildPoseMatrix(info.pivot, edits[cur]);
  drawWeapon(info, f0, f1, lerp, modelMat, vpMat, camPos, 0);
  if ($('c_wire').checked) drawWeapon(info, f0, f1, lerp, modelMat, vpMat, camPos, 1);

  requestAnimationFrame(loop);
}
init();
</script>
</body>
</html>
"""


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    data = build_shared_data(include_pickups_and_3p=True)
    gz = gzip.compress(bytes(data["arena"]), compresslevel=9, mtime=0)
    bin_b64 = base64.b64encode(gz).decode("ascii")

    # 1. Build Inspector HTML
    inspector_payload = {
        "binGz": bin_b64,
        "textures": data["textures"],
        "variants": {
            "rod": {
                "title": "1 · Chrome-Rod Contraption Bazooka (v_rodcannon / p_rodcannon / g_rodcannon)",
                "desc": "Built from the two-wheel stainless-steel contraption concept: wide pneumatic hand-truck tires on a barbell axle, mirror-chrome bullet-dome breech, +56% peristaltic swell & 3000-RPM wheel burnout.",
                "kvs": [
                    ["1st-Person", "progs/v_rodcannon.md3 (48f)"],
                    ["3rd-Person vwep", "progs/p_rodcannon.md3 (259f)"],
                    ["World Pickup", "progs/g_rodcannon.md3 (35° tilt)"],
                    ["Status", "Unused / parked (textures/skins in pk3)"],
                ],
                "models": {"vm": data["rod"]["vm"], "p3": data["rod"]["p3"], "pk": data["rod"]["pk"]},
                "fn_vm": data["rod"]["fn_vm"],
                "fn_p3": data["rod"]["fn_p3"],
                "crt": [],
                "orbitCtr": [26, -3, -5],
                "pkCtr": [0, 0, 15],
            },
            "wew1": {
                "title": "2 · WEW Cannon v1 — Cartoon +58° Bendy-Barrel (v_wcannon / pre_gunpose)",
                "desc": "First brushed-silver WEW Cannon iteration with WEW-TAC 98 CRT monitor, extreme +58° upward barrel bend & +58% peristaltic bulge during charge, whip-snap blast, and springy S-bend recoil.",
                "kvs": [
                    ["Archive File", "_bakersfield_dev/progs/v_wcannon.md3"],
                    ["Charge Anim", "bend1..10 (+58° Bend & +58% Bulge)"],
                    ["Geometry", f"{data['wew1']['vm']['nv']} verts / {data['wew1']['vm']['nt']} tris"],
                    ["Status", "Superseded by XM-98 Military v2"],
                ],
                "models": {"vm": data["wew1"]["vm"], "p3": None, "pk": data["wew1"]["pk"]},
                "fn_vm": data["wew1"]["fn_vm"],
                "fn_p3": [],
                "crt": data["wew1"]["crt"],
                "orbitCtr": [20, -5, -3],
                "pkCtr": [0, 0, 11],
            },
            "wew2": {
                "title": "3 · WEW Cannon v2 — XM-98 Military (Current In-Game progs/v_wewcannon.md3)",
                "desc": "Currently shipped in bakersfield.pk3. Tighter military artillery chassis with sear cocking (+5.5° steel flex), twin muzzle-brake side jets, hydropneumatic return-to-battery, and WEW-TAC 98 CRT.",
                "kvs": [
                    ["Shipped File", "progs/v_wewcannon.md3 (in bakersfield.pk3)"],
                    ["Charge Anim", "charge1..10 (Sear Cock & +5.5° Flex)"],
                    ["Geometry", f"{data['wew2']['vm']['nv']} verts / {data['wew2']['vm']['nt']} tris"],
                    ["Frame-0 Pivot", f"X={data['wew2']['pivot'][0]:.2f}, Y={data['wew2']['pivot'][1]:.2f}, Z={data['wew2']['pivot'][2]:.2f}"],
                ],
                "models": {"vm": data["wew2"]["vm"], "p3": None, "pk": data["wew2"]["pk"]},
                "fn_vm": data["wew2"]["fn_vm"],
                "fn_p3": [],
                "crt": data["wew2"]["crt"],
                "orbitCtr": [20, -5, -3],
                "pkCtr": [0, 0, 11],
            },
        },
    }
    html1 = INSPECTOR_TEMPLATE.replace("/*__PAYLOAD__*/null", json.dumps(inspector_payload, separators=(",", ":")))
    open(OUT_INSPECTOR, "w", encoding="utf-8").write(html1)
    print(f"[OK] Wrote {OUT_INSPECTOR} ({os.path.getsize(OUT_INSPECTOR) / 1e6:.2f} MB)")

    # 2. Build Pose Adjuster HTML (packs only the 3 1st-person viewmodels so it's extra lean!)
    adj_data = build_shared_data(include_pickups_and_3p=False)
    adj_gz = gzip.compress(bytes(adj_data["arena"]), compresslevel=9, mtime=0)
    adj_payload = {
        "binGz": base64.b64encode(adj_gz).decode("ascii"),
        "textures": adj_data["textures"],
        "models": {
            "wew2": {
                "label": "XM-98 WEW Cannon (Current In-Game · v_wewcannon)",
                "exportKey": "v_wewcannon",
                "md3": adj_data["wew2"]["vm"],
                "pivot": adj_data["wew2"]["pivot"],
                "lo": adj_data["wew2"]["lo"],
                "hi": adj_data["wew2"]["hi"],
                "crt": adj_data["wew2"]["crt"],
            },
            "wew1": {
                "label": "WEW Cannon v1 (Cartoon +58° Bendy Barrel)",
                "exportKey": "v_wewcannon_v1",
                "md3": adj_data["wew1"]["vm"],
                "pivot": adj_data["wew1"]["pivot"],
                "lo": adj_data["wew1"]["lo"],
                "hi": adj_data["wew1"]["hi"],
                "crt": adj_data["wew1"]["crt"],
            },
            "rod": {
                "label": "Chrome-Rod Contraption (v_rodcannon)",
                "exportKey": "v_rodcannon",
                "md3": adj_data["rod"]["vm"],
                "pivot": adj_data["rod"]["pivot"],
                "lo": adj_data["rod"]["lo"],
                "hi": adj_data["rod"]["hi"],
                "crt": [],
            },
        },
    }
    html2 = ADJUSTER_TEMPLATE.replace("/*__PAYLOAD__*/null", json.dumps(adj_payload, separators=(",", ":")))
    open(OUT_ADJUSTER, "w", encoding="utf-8").write(html2)
    print(f"[OK] Wrote {OUT_ADJUSTER} ({os.path.getsize(OUT_ADJUSTER) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
