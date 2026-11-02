"""Builds the standalone studio-grade WebGL2 3D interactive viewer for the
X290 Fiat Ducato / Ram ProMaster L2H2 High-Roof Walk-In Cargo Van:
  G:\\Quake\\Combat\\BakersfieldQuake\\van_3d_viewer.html

Features:
  - Full 2048x2048 lossless studio texture atlas + 512x512 RGBA cab glass & wire-mesh bulkhead
    + 2048x2048 emissive headlight/taillight glow map embedded as base64 (zero server needed).
  - Studio Photography Cyclorama infinity cove (matching reference video frames 001..020)
    with analytical soft underbody, 4-tire contact-patch, and dynamic barn-door floor shadows,
    plus toggleable Quake Dark Grid showroom theme.
  - 8 Reference & Interior Camera Presets (exact 50mm studio focal length matching reference video).
  - Live Articulation Controls: Rear Barn Doors (0..180 deg, default 126 deg), Cab Doors (0..65 deg),
    Front Hood (0..42 deg), and Front Wheel Steer (-32..+32 deg with synced 3D steering wheel!).
  - True Quake First-Person Walk-In Mode (32x32x56 hull, <=18u step-up onto 16.5u rear step bumper
    -> 19.5u corrugated cargo floor -> 58u wheel-arch aisle -> 35u bulkhead aisle -> cockpit).
  - Interactive Test-Drive Mode ([E] from cockpit or button) with rolling wheels, steering,
    body suspension pitch/roll, chase/cockpit camera toggle, and WebAudio diesel engine & horn.
  - Synced 13-box Quake SOLID_BBOX + SOLID_TRIGGER collision hull overlay & Dollhouse Cutaway mode.
"""
import base64
import json
import math
import os
import struct
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PARTS_JSON = os.path.join(HERE, "out", "vehicles_parts.json")
ATLAS_PNG = os.path.join(HERE, "out", "vehicles", "veh_van_atlas_2k.png")
GLASS_PNG = os.path.join(HERE, "out", "vehicles", "veh_van_glass.png")
GLOW_PNG = os.path.join(ROOT, "progs", "veh_van_tex_glow.png")
OUT_HTML = os.path.join(ROOT, "van_3d_viewer.html")

SCALE = 0.025  # 1 Quake unit = 0.025 m (227u -> 5.675 m length, 103.5u -> 2.59 m height)


def q2gl_pos(pt):
    return [float(pt[1]) * SCALE, float(pt[2]) * SCALE, float(pt[0]) * SCALE]


def q2gl_dir(vec):
    return [float(vec[1]), float(vec[2]), float(vec[0])]


def _pack_mesh_buffers(verts_q_world, norms_q, uvs, tris):
    """Packs world-space Quake vertices/normals/UVs/tris into interleaved WebGL2
    Float32 [x_gl, y_gl, z_gl, nx_gl, ny_gl, nz_gl, u, v] (32 bytes/vert) + Uint16 indices."""
    va = np.asarray(verts_q_world, dtype=np.float32)
    na = np.asarray(norms_q, dtype=np.float32)
    ua = np.asarray(uvs, dtype=np.float32)

    # Even cyclic permutation (X_q, Y_q, Z_q) -> (Y_q, Z_q, X_q) preserves right-handedness & CCW winding!
    pos_gl = np.stack([va[:, 1], va[:, 2], va[:, 0]], axis=1) * SCALE
    nrm_gl = np.stack([na[:, 1], na[:, 2], na[:, 0]], axis=1)
    nlen = np.linalg.norm(nrm_gl, axis=1, keepdims=True)
    nrm_gl = nrm_gl / np.maximum(nlen, 1e-8)

    interleaved = np.hstack([pos_gl, nrm_gl, ua]).astype("<f4")
    idx_arr = np.asarray(tris, dtype="<u2").reshape(-1)
    centroid_gl = pos_gl.mean(axis=0).tolist() if len(pos_gl) else [0.0, 0.0, 0.0]

    return {
        "v_b64": base64.b64encode(interleaved.tobytes()).decode("ascii"),
        "i_b64": base64.b64encode(idx_arr.tobytes()).decode("ascii"),
        "n_verts": int(len(va)),
        "n_idx": int(len(idx_arr)),
        "centroid": [round(c, 4) for c in centroid_gl],
    }


def _filter_subpart(part, pred_fn):
    """Extracts a subset of triangles from a part dictionary based on pred_fn(c_q, fn_q)."""
    ox, oy, oz = part["origin"]
    verts_w = [[v[0] + ox, v[1] + oy, v[2] + oz] for v in part["verts"]]
    norms = part["norms"]
    uvs = part["uvs"]

    remap = {}
    out_v, out_n, out_u, out_t = [], [], [], []
    for a, b, c in part["tris"]:
        p0, p1, p2 = verts_w[a], verts_w[b], verts_w[c]
        cq = ((p0[0] + p1[0] + p2[0]) / 3.0, (p0[1] + p1[1] + p2[1]) / 3.0, (p0[2] + p1[2] + p2[2]) / 3.0)
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = math.sqrt(nx * nx + ny * ny + nz * nz)
        fn = (nx / ln, ny / ln, nz / ln) if ln > 1e-9 else (0.0, 0.0, 1.0)
        if not pred_fn(cq, fn, (p0, p1, p2)):
            continue
        tri_new = []
        for idx in (a, b, c):
            if idx not in remap:
                remap[idx] = len(out_v)
                out_v.append(verts_w[idx])
                out_n.append(norms[idx])
                out_u.append(uvs[idx])
            tri_new.append(remap[idx])
        out_t.append(tri_new)

    if not out_t:
        return None
    return _pack_mesh_buffers(out_v, out_n, out_u, out_t)


def _whole_part(part):
    ox, oy, oz = part["origin"]
    verts_w = [[v[0] + ox, v[1] + oy, v[2] + oz] for v in part["verts"]]
    return _pack_mesh_buffers(verts_w, part["norms"], part["uvs"], part["tris"])


def build_viewer():
    with open(PARTS_JSON, "r", encoding="utf-8") as f:
        van = json.load(f)["van"]

    parts = van["parts"]
    rig = van["viewer_rig"]

    # Steering wheel geometry filter inside chassis:
    # sw_c = (62.2, 20.6, 49.8), sw_n = (-cos 28 deg, 0, sin 28 deg)
    sw_c = (62.2, 20.6, 49.8)
    tilt = math.radians(28.0)
    sw_n = (-math.cos(tilt), 0.0, math.sin(tilt))

    def is_steering_wheel(cq, _fn, _pts):
        if cq[1] < 12.5:
            return False
        dx, dy, dz = cq[0] - sw_c[0], cq[1] - sw_c[1], cq[2] - sw_c[2]
        if dx * dx + dy * dy + dz * dz > 8.2 * 8.2:
            return False
        axial = dx * sw_n[0] + dy * sw_n[1] + dz * sw_n[2]
        return axial > -1.45

    def is_cutaway_shell(cq, _fn, pts):
        if is_steering_wheel(cq, _fn, pts):
            return False
        zmin = min(pts[0][2], pts[1][2], pts[2][2])
        zmax = max(pts[0][2], pts[1][2], pts[2][2])
        ymin = min(pts[0][1], pts[1][1], pts[2][1])
        # Clean quad-aligned CAD cutaway: roof/ceiling (zmin >= 94.0) + left (+Y) wall, liner & cant-rail!
        if zmin >= 94.0:
            return True
        if ymin > 31.8 and -107.2 < cq[0] < 84.5:
            # Preserve white rounded interior wheel arch (zmax <= 38.6) & lower exterior rub-strip/fender (zmax <= 33.8)
            if zmin >= 33.2 and not (-85.8 < cq[0] < -50.2 and zmax <= 38.8):
                return True
            # Also cleanly remove the lower dark inner cargo liner card (z = 19.5..46.8 -> zmax > 45.0)
            if zmin >= 19.0 and zmax > 45.0 and cq[0] < 32.0:
                return True
        return False

    def is_chassis_core(cq, fn, pts):
        return (not is_steering_wheel(cq, fn, pts)) and (not is_cutaway_shell(cq, fn, pts))

    meshes = []

    def add_mesh(mid, buf, pass_id, anim_kind, pivot_q=(0.0, 0.0, 0.0), axis_q=(0.0, 0.0, 1.0), hide_cutaway=False):
        if buf is None:
            return
        meshes.append({
            "id": mid,
            "pass": pass_id,          # 0 = opaque 2K atlas, 1 = alpha-blended RGBA glass/mesh
            "anim": anim_kind,        # static | steer_sw | hood | door_l | door_r | barn_l | barn_r | wheel_fl | wheel_fr | wheel_rl | wheel_rr
            "pivot": [round(x, 5) for x in q2gl_pos(pivot_q)],
            "axis": [round(x, 5) for x in q2gl_dir(axis_q)],
            "hideCut": bool(hide_cutaway),
            **buf,
        })

    # 1. Opaque sculpted parts
    ch = parts["chassis"]
    add_mesh("chassis_core",    _filter_subpart(ch, is_chassis_core),   0, "static")
    add_mesh("chassis_cutaway", _filter_subpart(ch, is_cutaway_shell),  0, "static", hide_cutaway=True)
    add_mesh("steering_wheel",  _filter_subpart(ch, is_steering_wheel), 0, "steer_sw", pivot_q=sw_c, axis_q=sw_n)

    add_mesh("bumper_f",   _whole_part(parts["bumper_f"]),   0, "static")
    add_mesh("bumper_r",   _whole_part(parts["bumper_r"]),   0, "static")
    add_mesh("detail_vib", _whole_part(parts["detail_vib"]), 0, "static")

    add_mesh("hood",   _whole_part(parts["hood"]),   0, "hood",   pivot_q=parts["hood"]["hinge"],   axis_q=(0.0, 1.0, 0.0))
    add_mesh("door_l", _whole_part(parts["door_l"]), 0, "door_l", pivot_q=parts["door_l"]["hinge"], axis_q=(0.0, 0.0, 1.0), hide_cutaway=True)
    add_mesh("door_r", _whole_part(parts["door_r"]), 0, "door_r", pivot_q=parts["door_r"]["hinge"], axis_q=(0.0, 0.0, 1.0))

    bd_l = rig["barn_door_l_closed"]
    bd_r = rig["barn_door_r_closed"]
    add_mesh("barn_l", _whole_part(bd_l), 0, "barn_l", pivot_q=bd_l["hinge"], axis_q=(0.0, 0.0, 1.0))
    add_mesh("barn_r", _whole_part(bd_r), 0, "barn_r", pivot_q=bd_r["hinge"], axis_q=(0.0, 0.0, 1.0))

    for wk in ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"):
        wp = parts[wk]
        add_mesh(wk, _whole_part(wp), 0, wk, pivot_q=wp["origin"], axis_q=(0.0, 1.0, 0.0))

    # 2. Translucent RGBA Cab Glass & Square Steel Wire-Mesh Bulkhead (sorted back-to-front per frame!)
    gc = parts["glass_cab"]
    add_mesh("bulkhead_mesh",    _filter_subpart(gc, lambda c, _f, _p: c[0] < 33.5),                       1, "static", hide_cutaway=False)
    add_mesh("glass_windshield", _filter_subpart(gc, lambda c, _f, _p: c[0] >= 33.5 and abs(c[1]) <= 37.2), 1, "static", hide_cutaway=True)
    add_mesh("glass_door_l",     _filter_subpart(gc, lambda c, _f, _p: c[0] >= 33.5 and c[1] > 37.2),      1, "door_l", pivot_q=parts["door_l"]["hinge"], axis_q=(0.0, 0.0, 1.0), hide_cutaway=True)
    add_mesh("glass_door_r",     _filter_subpart(gc, lambda c, _f, _p: c[0] >= 33.5 and c[1] < -37.2),     1, "door_r", pivot_q=parts["door_r"]["hinge"], axis_q=(0.0, 0.0, 1.0), hide_cutaway=False)

    tot_verts = sum(m["n_verts"] for m in meshes)
    tot_tris = sum(m["n_idx"] // 3 for m in meshes)

    with open(ATLAS_PNG, "rb") as f:
        atlas_b64 = base64.b64encode(f.read()).decode("ascii")
    with open(GLASS_PNG, "rb") as f:
        glass_b64 = base64.b64encode(f.read()).decode("ascii")
    with open(GLOW_PNG, "rb") as f:
        glow_b64 = base64.b64encode(f.read()).decode("ascii")

    # Synced 1:1 with Veh_Van_InitCollision in source/mm_tools/vehicles.qc!
    collision_boxes_q = [
        {"name": "1. Rear Walk-In Step (16.5u)", "b": [-114, -108, -33, 33, 0, 16.5], "kind": "step"},
        {"name": "2. Cargo & Cab Floor (19.5u)", "b": [-108, 68, -39, 39, 0, 19.5],   "kind": "floor"},
        {"name": "3. Left Cargo/Cab Wall",       "b": [-108, 68, 38, 43, 19.5, 101],  "kind": "wall"},
        {"name": "4. Right Cargo/Cab Wall",      "b": [-108, 68, -43, -38, 19.5, 101],"kind": "wall"},
        {"name": "5. Open 126° Left Barn Door",  "b": [-128, -108, 34, 56, 19.5, 97], "kind": "door"},
        {"name": "6. Open 126° Right Barn Door", "b": [-128, -108, -56, -34, 19.5, 97],"kind": "door"},
        {"name": "7. H2 High-Roof Ceiling",      "b": [-108, 48, -40, 40, 96.5, 103.5],"kind": "roof"},
        {"name": "8. Front Dash & Nose",         "b": [68, 113, -43, 43, 0, 52],      "kind": "wall"},
        {"name": "9. Left Wheel Arch",           "b": [-85, -51, 29, 39, 19.5, 38.5], "kind": "arch"},
        {"name": "10. Right Wheel Arch",         "b": [-85, -51, -39, -29, 19.5, 38.5],"kind": "arch"},
        {"name": "11. Left Bulkhead & Seat",     "b": [30, 36, 17.5, 39, 19.5, 82],   "kind": "bulk"},
        {"name": "12. Right Bulkhead & Seat",    "b": [30, 36, -39, -17.5, 19.5, 82], "kind": "bulk"},
        {"name": "13. Driver Cockpit Trigger",   "b": [36, 66, -16, 34, 19.5, 76],    "kind": "trig"},
    ]

    # Exact studio camera presets matched 1:1 to reference video frames 001, 005, 009, 010, 015, 020 + 2 interior views
    raw_presets = [
        ("1. Rear 3/4 (Video Start)", (-345.0, -238.0, 66.0), (-12.0,  0.0, 51.5), 27.5, True),
        ("2. Right Side (Sliding)",   ( -76.0, -460.0, 56.0), ( -6.0,  0.0, 52.5), 26.8, True),
        ("3. Front 3/4 (X290 Nose)",  ( 345.0, -228.0, 66.0), ( -2.0,  0.0, 51.5), 27.5, True),
        ("4. Front Straight",         ( 405.0,  -48.0, 61.0), (  0.0,  0.0, 52.0), 26.8, True),
        ("5. Left Side (Driver)",     (  32.0,  465.0, 56.0), ( -8.0,  0.0, 52.5), 26.8, True),
        ("6. Rear Cargo Straight",    (-405.0,  -45.0, 60.0), (  0.0,  0.0, 53.0), 26.8, True),
        ("7. Inside Cargo Bay",       ( -96.0,    0.0, 60.0), ( 42.0,  0.0, 50.0), 56.0, False),
        ("8. Driver's Cockpit",       (  39.8,   19.8, 65.8), ( 84.0, 17.5, 49.0), 60.0, False),
    ]
    presets_gl = []
    for label, eye_q, tgt_q, fov_deg, pan_for_ui in raw_presets:
        eg = q2gl_pos(eye_q)
        tg = q2gl_pos(tgt_q)
        if pan_for_ui:
            # Shift look-at target slightly along camera +Right so the van centers in the open canvas left of #sidePanel!
            fx_c, fz_c = tg[0] - eg[0], tg[2] - eg[2]
            fl_c = math.hypot(fx_c, fz_c) or 1.0
            rx_c, rz_c = -fz_c / fl_c, fx_c / fl_c
            d_full = math.sqrt((eg[0] - tg[0]) ** 2 + (eg[1] - tg[1]) ** 2 + (eg[2] - tg[2]) ** 2)
            shift = d_full * 0.048
            eg = [eg[0] + rx_c * shift, eg[1], eg[2] + rz_c * shift]
            tg = [tg[0] + rx_c * shift, tg[1], tg[2] + rz_c * shift]
        dx, dy, dz = eg[0] - tg[0], eg[1] - tg[1], eg[2] - tg[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        pitch = math.asin(max(-0.999, min(0.999, dy / dist)))
        yaw = math.atan2(dx, dz)
        presets_gl.append({
            "label": label,
            "yaw": round(yaw, 5),
            "pitch": round(pitch, 5),
            "dist": round(dist, 4),
            "target": [round(t, 4) for t in tg],
            "fov": fov_deg,
        })

    payload = {
        "scale": SCALE,
        "defaultBarnDeg": float(rig["default_barn_deg"]),
        "stats": {"verts": tot_verts, "tris": tot_tris, "parts": len(meshes)},
        "meshes": meshes,
        "presets": presets_gl,
        "collisionBoxes": collision_boxes_q,
    }

    html = _HTML_TEMPLATE
    html = html.replace("__VAN_PAYLOAD_JSON__", json.dumps(payload, separators=(",", ":")))
    html = html.replace("__ATLAS_B64__", atlas_b64)
    html = html.replace("__GLASS_B64__", glass_b64)
    html = html.replace("__GLOW_B64__", glow_b64)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    sz_mb = os.path.getsize(OUT_HTML) / (1024 * 1024)
    print(f"Built {OUT_HTML} ({sz_mb:.2f} MB) | {tot_verts} verts, {tot_tris} tris across {len(meshes)} sub-meshes.")


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ProMaster / Ducato L2H2 Walk-In Van — Quake 3D Studio Viewer</title>
<style>
  :root {
    --panel-bg: rgba(18, 20, 24, 0.84);
    --panel-border: rgba(255, 255, 255, 0.13);
    --accent: #38bdf8;
    --accent-warm: #f59e0b;
    --accent-ok: #34d399;
    --text: #f3f4f6;
    --muted: #9ca3af;
  }
  * { box-sizing: border-box; user-select: none; -webkit-user-select: none; }
  html, body {
    margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden;
    background: #a9a9a6;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: var(--text);
  }
  #glCanvas {
    display: block; width: 100vw; height: 100vh; cursor: grab;
  }
  #glCanvas:active { cursor: grabbing; }

  /* Sleek Top Header Pill */
  #topBar {
    position: fixed; top: 14px; left: 16px; right: 16px;
    display: flex; align-items: center; justify-content: space-between;
    pointer-events: none; z-index: 20; gap: 12px;
  }
  .brandCard {
    pointer-events: auto;
    background: var(--panel-bg);
    backdrop-filter: blur(14px);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 9px 15px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.22);
    display: flex; align-items: center; gap: 14px;
  }
  .brandTitle { font-size: 14px; font-weight: 700; letter-spacing: 0.2px; color: #fff; }
  .brandSub { font-size: 11.5px; color: var(--muted); margin-top: 1px; }
  .statPill {
    font-size: 11px; font-weight: 600; color: #dbeafe;
    background: rgba(56, 189, 248, 0.16);
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 4px 9px; border-radius: 999px; white-space: nowrap;
  }

  .modeBar {
    pointer-events: auto;
    display: flex; gap: 7px; flex-wrap: wrap;
    background: var(--panel-bg);
    backdrop-filter: blur(14px);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 6px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.22);
  }
  button {
    font-family: inherit;
    font-size: 11.5px; font-weight: 600;
    color: #e5e7eb;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 11px;
    cursor: pointer;
    transition: all 0.14s ease;
  }
  button:hover { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.26); color: #fff; }
  button.active {
    background: rgba(56, 189, 248, 0.24);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.28);
  }
  button.activeWarm {
    background: rgba(245, 158, 11, 0.26);
    border-color: var(--accent-warm);
    color: #fff;
  }
  button.activeOk {
    background: rgba(52, 211, 153, 0.25);
    border-color: var(--accent-ok);
    color: #fff;
  }

  /* Collapsible Right Studio Inspector */
  #sidePanel {
    position: fixed; top: 72px; right: 16px; width: 286px;
    max-height: calc(100vh - 140px); overflow-y: auto;
    background: var(--panel-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--panel-border);
    border-radius: 14px;
    padding: 13px 14px;
    box-shadow: 0 12px 36px rgba(0,0,0,0.26);
    z-index: 20;
    transition: opacity 0.2s ease, transform 0.2s ease;
  }
  #sidePanel.hidden { opacity: 0; pointer-events: none; transform: translateX(20px); }
  .secTitle {
    font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.9px; color: var(--muted);
    margin: 11px 0 7px 0;
    display: flex; justify-content: space-between; align-items: center;
  }
  .secTitle:first-child { margin-top: 0; }

  .presetGrid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 5px;
  }
  .presetGrid button {
    text-align: left; padding: 6px 8px; font-size: 11px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  .sliderRow { margin-bottom: 8px; }
  .sliderHdr {
    display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 3px;
  }
  .sliderVal { color: var(--accent); font-weight: 700; font-variant-numeric: tabular-nums; }
  input[type=range] {
    width: 100%; height: 5px; border-radius: 4px;
    appearance: none; -webkit-appearance: none;
    background: rgba(255,255,255,0.16); outline: none; cursor: pointer;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
    background: var(--accent); border: 2px solid #fff; cursor: pointer;
  }

  .toggleGrid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

  .swatchRow { display: flex; gap: 7px; margin-top: 4px; }
  .swatch {
    width: 24px; height: 24px; border-radius: 50%; cursor: pointer;
    border: 2px solid rgba(255,255,255,0.3); transition: transform 0.12s;
  }
  .swatch:hover { transform: scale(1.12); }
  .swatch.active { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(56,189,248,0.45); }

  /* Bottom Status / FPS Walk-In & Drive HUD */
  #bottomHud {
    position: fixed; bottom: 14px; left: 16px;
    background: var(--panel-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--panel-border);
    border-radius: 11px;
    padding: 8px 14px;
    font-size: 12px; color: #e5e7eb;
    box-shadow: 0 8px 24px rgba(0,0,0,0.22);
    z-index: 20;
    display: flex; align-items: center; gap: 14px;
  }
  .kbd {
    display: inline-block; padding: 1px 6px; border-radius: 4px;
    background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
    font-size: 11px; font-weight: 700; color: #fff; margin: 0 2px;
  }

  #centerBanner {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -135%);
    background: rgba(16, 24, 32, 0.88);
    border: 1px solid var(--accent-ok);
    color: #ecfdf5;
    padding: 10px 18px; border-radius: 10px;
    font-size: 13px; font-weight: 700; text-align: center;
    pointer-events: none; opacity: 0; transition: opacity 0.18s ease;
    box-shadow: 0 10px 30px rgba(0,0,0,0.38); z-index: 25;
  }
  #centerBanner.show { opacity: 1; }

  #crosshair {
    position: fixed; top: 50%; left: 50%; width: 14px; height: 14px;
    transform: translate(-50%, -50%); pointer-events: none; display: none; z-index: 22;
  }
  #crosshair::before, #crosshair::after {
    content: ''; position: absolute; background: rgba(255,255,255,0.85);
    box-shadow: 0 0 3px rgba(0,0,0,0.7);
  }
  #crosshair::before { top: 6px; left: 0; width: 14px; height: 2px; }
  #crosshair::after  { left: 6px; top: 0; width: 2px; height: 14px; }
</style>
</head>
<body>

<canvas id="glCanvas"></canvas>
<div id="crosshair"></div>
<div id="centerBanner">Driver Cockpit Reached — Press <span class="kbd">E</span> to Drive Van!</div>

<div id="topBar">
  <div class="brandCard">
    <div>
      <div class="brandTitle">X290 ProMaster / Ducato L2H2 High-Roof Cargo Van</div>
      <div class="brandSub">Quake DarkPlaces Walk-In Drivable Vehicle • 2K Studio Atlas + RGBA Glass/Mesh</div>
    </div>
    <div class="statPill" id="meshStatsPill">Loading…</div>
  </div>

  <div class="modeBar">
    <button id="btnModeOrbit" class="active" title="Studio Orbit Camera [1-8]">Studio Orbit</button>
    <button id="btnModeWalk" title="Walk Inside with Quake 32x32x56 Player Hull [F]">Walk Inside (FPS)</button>
    <button id="btnModeDrive" title="Sit in Driver's Seat & Test Drive [E]">Test Drive</button>
    <button id="btnTogglePanel" title="Show/Hide Controls [H]">Hide UI</button>
  </div>
</div>

<div id="sidePanel">
  <div class="secTitle">
    <span>Reference & Interior Views</span>
    <span style="font-size:10px;color:#60a5fa">[1–8]</span>
  </div>
  <div class="presetGrid" id="presetGrid"></div>

  <div class="secTitle">Live Articulation Rig</div>

  <div class="sliderRow">
    <div class="sliderHdr">
      <span>Rear Barn Doors (50/50)</span>
      <span class="sliderVal" id="valBarn">126°</span>
    </div>
    <input type="range" id="slBarn" min="0" max="180" step="1" value="126">
  </div>

  <div class="sliderRow">
    <div class="sliderHdr">
      <span>Cab Doors & Mirrors</span>
      <span class="sliderVal" id="valCab">0°</span>
    </div>
    <input type="range" id="slCab" min="0" max="65" step="1" value="0">
  </div>

  <div class="sliderRow">
    <div class="sliderHdr">
      <span>Front Service Hood</span>
      <span class="sliderVal" id="valHood">0°</span>
    </div>
    <input type="range" id="slHood" min="0" max="42" step="1" value="0">
  </div>

  <div class="sliderRow">
    <div class="sliderHdr">
      <span>Steering Wheel & Axle</span>
      <span class="sliderVal" id="valSteer">0°</span>
    </div>
    <input type="range" id="slSteer" min="-32" max="32" step="1" value="0">
  </div>

  <div class="secTitle">Studio & Quake Overlays</div>
  <div class="toggleGrid">
    <button id="btnBgTheme" class="active" title="Toggle Studio Cyclorama vs Quake Dark Grid [B]">Studio Cove</button>
    <button id="btnSpin" title="360° Turntable Showcase [T]">Turntable</button>
    <button id="btnCutaway" title="Dollhouse Cutaway to Inspect Walk-In Interior [X]">Cutaway</button>
    <button id="btnHulls" title="Show 13 Quake SOLID_BBOX + Cockpit Trigger Hulls [C]">Quake Hulls</button>
    <button id="btnLights" title="Toggle Headlights, Amber Markers & Taillights [L]">Lights Off</button>
    <button id="btnWire" title="Triangle Mesh Wireframe Overlay [M]">Wireframe</button>
  </div>

  <div class="secTitle">Factory Fleet Paint</div>
  <div class="swatchRow" id="swatchRow">
    <div class="swatch active" data-tint="1.00,1.00,1.00" style="background:#f4f5f7" title="Alpine Fleet White (Reference)"></div>
    <div class="swatch" data-tint="0.83,0.86,0.90" style="background:#cbd4de" title=" Silver Metallic"></div>
    <div class="swatch" data-tint="0.96,0.75,0.18" style="background:#f5be2e" title="DHL / Highway Amber"></div>
    <div class="swatch" data-tint="0.86,0.22,0.20" style="background:#dc3833" title="Fire / Rescue Red"></div>
    <div class="swatch" data-tint="0.24,0.44,0.74" style="background:#3d70bd" title=" Municipal Blue"></div>
    <div class="swatch" data-tint="0.34,0.37,0.40" style="background:#575e66" title="Tactical Slate Grey"></div>
  </div>
</div>

<div id="bottomHud">
  <span id="hudText">
    <b>Orbit:</b> Left-Drag • <b>Pan:</b> Right-Drag • <b>Zoom:</b> Wheel •
    Press <span class="kbd">F</span> to Walk Inside Cargo Bay • <span class="kbd">1–8</span> Views
  </span>
</div>

<script>
(() => {
  "use strict";

  const DATA = __VAN_PAYLOAD_JSON__;
  const ATLAS_URI = "data:image/png;base64,__ATLAS_B64__";
  const GLASS_URI = "data:image/png;base64,__GLASS_B64__";
  const GLOW_URI  = "data:image/png;base64,__GLOW_B64__";
  const S = DATA.scale; // 0.025 m per Quake unit

  document.getElementById("meshStatsPill").textContent =
    `${DATA.stats.verts.toLocaleString()} verts • ${DATA.stats.tris.toLocaleString()} tris`;

  const canvas = document.getElementById("glCanvas");
  const gl = canvas.getContext("webgl2", {
    antialias: true,
    alpha: false,
    depth: true,
    powerPreference: "high-performance",
    preserveDrawingBuffer: true
  });
  if (!gl) {
    alert("WebGL2 is required to view this 3D model.");
    return;
  }
  const extAniso = gl.getExtension("EXT_texture_filter_anisotropic") ||
                   gl.getExtension("WEBKIT_EXT_texture_filter_anisotropic");

  // =========================================================================
  // 1. Matrix & Vector Math Helpers (Column-Major Float32Array(16))
  // =========================================================================
  function mat4Identity() {
    const m = new Float32Array(16);
    m[0] = m[5] = m[10] = m[15] = 1;
    return m;
  }
  function mat4Mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++) {
      const b0 = b[c*4], b1 = b[c*4+1], b2 = b[c*4+2], b3 = b[c*4+3];
      o[c*4]   = a[0]*b0 + a[4]*b1 + a[8]*b2  + a[12]*b3;
      o[c*4+1] = a[1]*b0 + a[5]*b1 + a[9]*b2  + a[13]*b3;
      o[c*4+2] = a[2]*b0 + a[6]*b1 + a[10]*b2 + a[14]*b3;
      o[c*4+3] = a[3]*b0 + a[7]*b1 + a[11]*b2 + a[15]*b3;
    }
    return o;
  }
  function mat4Perspective(fovYRad, aspect, near, far) {
    const f = 1.0 / Math.tan(fovYRad * 0.5);
    const nf = 1.0 / (near - far);
    const m = new Float32Array(16);
    m[0] = f / aspect;
    m[5] = f;
    m[10] = (far + near) * nf;
    m[11] = -1.0;
    m[14] = 2.0 * far * near * nf;
    return m;
  }
  function mat4LookAt(eye, ctr, up) {
    let zx = eye[0] - ctr[0], zy = eye[1] - ctr[1], zz = eye[2] - ctr[2];
    let zl = Math.hypot(zx, zy, zz) || 1;
    zx /= zl; zy /= zl; zz /= zl;
    let xx = up[1]*zz - up[2]*zy;
    let xy = up[2]*zx - up[0]*zz;
    let xz = up[0]*zy - up[1]*zx;
    let xl = Math.hypot(xx, xy, xz) || 1;
    xx /= xl; xy /= xl; xz /= xl;
    const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
    const m = new Float32Array(16);
    m[0]=xx; m[4]=xy; m[8]=xz;  m[12]=-(xx*eye[0]+xy*eye[1]+xz*eye[2]);
    m[1]=yx; m[5]=yy; m[9]=yz;  m[13]=-(yx*eye[0]+yy*eye[1]+yz*eye[2]);
    m[2]=zx; m[6]=zy; m[10]=zz; m[14]=-(zx*eye[0]+zy*eye[1]+zz*eye[2]);
    m[3]=0;  m[7]=0;  m[11]=0;  m[15]=1;
    return m;
  }
  function mat4Translate(tx, ty, tz) {
    const m = mat4Identity();
    m[12] = tx; m[13] = ty; m[14] = tz;
    return m;
  }
  function mat4AxisAngle(axis, rad) {
    let [x, y, z] = axis;
    const l = Math.hypot(x, y, z) || 1;
    x /= l; y /= l; z /= l;
    const s = Math.sin(rad), c = Math.cos(rad), t = 1.0 - c;
    const m = mat4Identity();
    m[0] = t*x*x + c;   m[4] = t*x*y - s*z; m[8]  = t*x*z + s*y;
    m[1] = t*x*y + s*z; m[5] = t*y*y + c;   m[9]  = t*y*z - s*x;
    m[2] = t*x*z - s*y; m[6] = t*y*z + s*x; m[10] = t*z*z + c;
    return m;
  }
  function mat4PivotAxisAngle(pivot, axis, rad) {
    if (Math.abs(rad) < 1e-6) return mat4Identity();
    return mat4Mul(mat4Translate(pivot[0], pivot[1], pivot[2]),
           mat4Mul(mat4AxisAngle(axis, rad), mat4Translate(-pivot[0], -pivot[1], -pivot[2])));
  }
  function transformPoint(m, p) {
    return [
      m[0]*p[0] + m[4]*p[1] + m[8]*p[2]  + m[12],
      m[1]*p[0] + m[5]*p[1] + m[9]*p[2]  + m[13],
      m[2]*p[0] + m[6]*p[1] + m[10]*p[2] + m[14]
    ];
  }

  // =========================================================================
  // 2. Shaders: Automotive Studio Multi-Softbox PBR + Seamless Cyclorama Floor
  // =========================================================================
  function compileProgram(vsSrc, fsSrc) {
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

  // ---- A. Background & Infinity Cyclorama Floor + Analytical Soft AO Shadow ----
  const BG_VS = `#version 300 es
  precision highp float;
  out vec2 vNDC;
  void main() {
    vec2 pos = vec2((gl_VertexID == 1) ? 3.0 : -1.0, (gl_VertexID == 2) ? 3.0 : -1.0);
    vNDC = pos;
    gl_Position = vec4(pos, 0.9999, 1.0);
  }`;

  const BG_FS = `#version 300 es
  precision highp float;
  in vec2 vNDC;
  out vec4 fragColor;

  uniform vec3 uCamEye;
  uniform vec3 uCamFwd;
  uniform vec3 uCamRight;
  uniform vec3 uCamUp;
  uniform float uTanHalfFov;
  uniform float uAspect;
  uniform int uStudioMode;
  uniform vec3 uVanPos;
  uniform float uVanYaw;
  uniform float uBarnRad;

  float sdRoundBox2D(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
  }

  float distSeg2D(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-5), 0.0, 1.0);
    return length(pa - ba * h);
  }

  void main() {
    vec3 rd = normalize(uCamFwd + vNDC.x * uAspect * uTanHalfFov * uCamRight + vNDC.y * uTanHalfFov * uCamUp);

    if (uStudioMode == 1) {
      // Seamless Photography Studio Cyclorama Backdrop (matched to reference frames 001..020)
      float h = clamp(rd.y, -1.0, 1.0);
      vec3 zenith  = vec3(0.635, 0.635, 0.624);
      vec3 horizon = vec3(0.752, 0.752, 0.740);
      vec3 col = mix(horizon, zenith, smoothstep(0.0, 0.42, max(0.0, h)));

      if (rd.y < -0.0004 && uCamEye.y > 0.01) {
        float t = -uCamEye.y / rd.y;
        vec3 hit = uCamEye + rd * t;
        float distCam = length(hit.xz - uCamEye.xz);
        float fog = 1.0 - exp(-distCam * 0.042);

        // Floor base studio neutral warm grey + subtle overhead softbox pool
        float pool = exp(-dot(hit.xz - uVanPos.xz, hit.xz - uVanPos.xz) * 0.012);
        vec3 floorCol = mix(vec3(0.705, 0.705, 0.693), vec3(0.738, 0.738, 0.726), pool);

        // Transform floor point into Van local Quake units (x_q forward, y_q left)
        vec2 dW = hit.xz - uVanPos.xz;
        float cy = cos(-uVanYaw), sy = sin(-uVanYaw);
        vec2 localGL = vec2(dW.x * cy + dW.y * sy, -dW.x * sy + dW.y * cy);
        vec2 pq = vec2(localGL.y, localGL.x) / 0.025; // (x_q, y_q)

        // 1. Soft chassis underbody ambient occlusion
        float dBody = sdRoundBox2D(pq, vec2(106.5, 41.2), 10.0);
        float aoWide = 1.0 - 0.44 * (1.0 - smoothstep(-14.0, 30.0, dBody));
        float aoCore = 1.0 - 0.25 * (1.0 - smoothstep(-28.0, 5.0, dBody));

        // 2. 4 Crisp Tire Contact-Patch AO Ellipses
        float aoTire = 1.0;
        vec2 tires[4] = vec2[4](
          vec2( 80.0,  38.5), vec2( 80.0, -38.5),
          vec2(-68.0,  38.5), vec2(-68.0, -38.5)
        );
        for (int i = 0; i < 4; i++) {
          vec2 dt = (pq - tires[i]) / vec2(16.0, 7.2);
          float r2 = dot(dt, dt);
          aoTire *= (1.0 - 0.66 * exp(-r2 * 1.45));
        }

        // 3. Dynamic Rear Barn Door Shadows (follows Barn Door slider!)
        vec2 hL = vec2(-108.6, 34.8);
        vec2 eL = hL + vec2(-34.2 * sin(uBarnRad), -34.2 * cos(uBarnRad));
        vec2 hR = vec2(-108.6, -34.8);
        vec2 eR = hR + vec2(-34.2 * sin(uBarnRad),  34.2 * cos(uBarnRad));
        float dDoor = min(distSeg2D(pq, hL, eL), distSeg2D(pq, hR, eR));
        float aoDoor = 1.0 - 0.14 * exp(-(dDoor * dDoor) / 170.0);

        floorCol *= (aoWide * aoCore * aoTire * aoDoor);
        col = mix(floorCol, horizon, clamp(fog, 0.0, 1.0));
      }
      fragColor = vec4(col, 1.0);
    } else {
      // Quake Dark Engineering Grid Showroom
      vec3 skyTop = vec3(0.055, 0.070, 0.095);
      vec3 skyHor = vec3(0.115, 0.140, 0.180);
      vec3 col = mix(skyHor, skyTop, smoothstep(0.0, 0.5, max(0.0, rd.y)));
      if (rd.y < -0.0004 && uCamEye.y > 0.01) {
        float t = -uCamEye.y / rd.y;
        vec3 hit = uCamEye + rd * t;
        float distCam = length(hit.xz - uCamEye.xz);
        float fog = 1.0 - exp(-distCam * 0.055);

        vec2 qu = hit.xz / 0.025;
        vec2 g32 = abs(fract(qu / 32.0 - 0.5) - 0.5) / fwidth(qu / 32.0);
        float l32 = 1.0 - min(min(g32.x, g32.y), 1.0);
        vec2 g128 = abs(fract(qu / 128.0 - 0.5) - 0.5) / fwidth(qu / 128.0);
        float l128 = 1.0 - min(min(g128.x, g128.y), 1.0);

        vec3 flr = vec3(0.085, 0.100, 0.125);
        flr = mix(flr, vec3(0.16, 0.24, 0.34), l32 * 0.45);
        flr = mix(flr, vec3(0.24, 0.56, 0.82), l128 * 0.75);

        // Underbody shadow on grid
        vec2 dW = hit.xz - uVanPos.xz;
        float cy = cos(-uVanYaw), sy = sin(-uVanYaw);
        vec2 localGL = vec2(dW.x * cy + dW.y * sy, -dW.x * sy + dW.y * cy);
        vec2 pq = vec2(localGL.y, localGL.x) / 0.025;
        float dBody = sdRoundBox2D(pq, vec2(106.5, 41.2), 10.0);
        flr *= (1.0 - 0.62 * (1.0 - smoothstep(-10.0, 26.0, dBody)));

        col = mix(flr, skyHor, clamp(fog, 0.0, 1.0));
      }
      fragColor = vec4(col, 1.0);
    }
  }`;

  // ---- B. Main Vehicle Shader (Opaque 2K Atlas + Translucent RGBA Cab Glass & Wire-Mesh) ----
  const VAN_VS = `#version 300 es
  precision highp float;
  layout(location = 0) in vec3 aPos;
  layout(location = 1) in vec3 aNorm;
  layout(location = 2) in vec2 aUV;

  uniform mat4 uViewProj;
  uniform mat4 uModel;
  uniform mat4 uInvVan;

  out vec3 vWorldPos;
  out vec3 vLocalVanPos;
  out vec3 vNorm;
  out vec2 vUV;

  void main() {
    vec4 wp = uModel * vec4(aPos, 1.0);
    vWorldPos = wp.xyz;
    vLocalVanPos = (uInvVan * wp).xyz;
    vNorm = normalize(mat3(uModel) * aNorm);
    vUV = aUV;
    gl_Position = uViewProj * wp;
  }`;

  const VAN_FS = `#version 300 es
  precision highp float;
  in vec3 vWorldPos;
  in vec3 vLocalVanPos;
  in vec3 vNorm;
  in vec2 vUV;
  out vec4 fragColor;

  uniform sampler2D uAtlasTex;
  uniform sampler2D uGlowTex;
  uniform sampler2D uGlassTex;
  uniform vec3 uCamEye;
  uniform vec3 uPaintTint;
  uniform float uGlowGain;
  uniform float uBarnOpenFactor;
  uniform int uPass;       // 0 = Opaque Body/Interior/Wheels, 1 = RGBA Glass & Wire-Mesh, 2 = Wireframe
  uniform int uStudioMode;

  vec3 acesFilm(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
  }

  void main() {
    if (uPass == 2) {
      fragColor = vec4(0.15, 0.78, 1.0, 0.55);
      return;
    }

    vec3 N = normalize(vNorm);
    if (!gl_FrontFacing) N = -N;
    vec3 V = normalize(uCamEye - vWorldPos);

    if (uPass == 1) {
      // Pass 1: 512x512 RGBA Laminated Green-Tint Cab Glass (u<0.5) & Steel Wire-Mesh Screen (u>=0.5)
      vec4 gSample = texture(uGlassTex, vUV);
      if (vUV.x >= 0.5) {
        // Square steel wire-mesh bulkhead screen
        if (gSample.a < 0.06) discard;
        vec3 wireLin = pow(gSample.rgb, vec3(2.2));
        vec3 L1 = normalize(vec3(0.20, 0.85, -0.48));
        float rim = 0.45 + 0.55 * abs(dot(N, L1));
        vec3 litWire = wireLin * (0.65 + 0.65 * rim);
        fragColor = vec4(pow(clamp(litWire, 0.0, 1.0), vec3(1.0 / 2.2)), gSample.a);
        return;
      } else {
        // Factory green-tinted laminated automotive cab glass + sky/softbox Fresnel reflection
        vec3 baseGlass = pow(gSample.rgb, vec3(2.2));
        float ndv = abs(dot(N, V));
        float fresnel = 0.05 + 0.48 * pow(1.0 - ndv, 4.0);
        vec3 R = reflect(-V, N);
        float softbox = smoothstep(0.62, 0.94, R.y) * (0.55 + 0.45 * smoothstep(-0.4, 0.4, R.z));
        vec3 envRefl = (uStudioMode == 1)
          ? mix(vec3(0.45, 0.47, 0.48), vec3(0.95, 0.97, 1.0), 0.45 + 0.55 * clamp(R.y, 0.0, 1.0))
          : mix(vec3(0.08, 0.12, 0.18), vec3(0.42, 0.60, 0.85), clamp(R.y, 0.0, 1.0));
        vec3 glassCol = baseGlass * 0.72 + envRefl * (fresnel + 0.26 * softbox);
        float outAlpha = clamp(gSample.a + fresnel * 0.55 + softbox * 0.16, 0.18, 0.88);
        fragColor = vec4(pow(acesFilm(glassCol), vec3(1.0 / 2.2)), outAlpha);
        return;
      }
    }

    // Pass 0: 2048x2048 Studio Atlas
    vec4 texSrgb = texture(uAtlasTex, vUV);
    vec3 albedo = pow(texSrgb.rgb, vec3(2.2));

    // Apply optional fleet paint tint ONLY to high-value neutral white exterior body panels
    // (preserves white interior cargo walls/floor/ceiling, red taillights, amber markers, EU blue band, and black trim!)
    float lum = dot(texSrgb.rgb, vec3(0.299, 0.587, 0.114));
    float sat = max(texSrgb.r, max(texSrgb.g, texSrgb.b)) - min(texSrgb.r, min(texSrgb.g, texSrgb.b));
    vec3 lq = vLocalVanPos / 0.025; // (y_q, z_q, x_q)
    bool isInterior = (abs(lq.x) < 38.4 && lq.y > 19.0 && lq.y < 99.3 && lq.z > -106.5 && lq.z < 68.0);
    if (!isInterior && lum > 0.62 && sat < 0.08) {
      albedo *= pow(uPaintTint, vec3(2.2));
    }

    // Detect material finish (gloss clearcoat white/paint vs chrome vs matte black rub-strip/rubber)
    float isGlossPaint = smoothstep(0.42, 0.70, lum) * (1.0 - smoothstep(0.12, 0.35, sat));
    if (isInterior) isGlossPaint *= 0.35; // semi-gloss commercial interior liner

    // 3-Softbox Studio Lighting Rig (matched to Blender Cycles verification rig!)
    vec3 L_top   = normalize(vec3( 0.06, 0.96,  0.27));
    vec3 L_front = normalize(vec3(-0.44, 0.42,  0.79));
    vec3 L_rear  = normalize(vec3(-0.38, 0.40, -0.83));
    vec3 L_left  = normalize(vec3( 0.84, 0.36, -0.40));

    // Wrapped studio softbox diffuse (soft shadow terminator like large rectangular area lights)
    float dTop   = clamp((dot(N, L_top)   + 0.35) / 1.35, 0.0, 1.0);
    float dFront = clamp((dot(N, L_front) + 0.30) / 1.30, 0.0, 1.0);
    float dRear  = clamp((dot(N, L_rear)  + 0.30) / 1.30, 0.0, 1.0);
    float dLeft  = clamp((dot(N, L_left)  + 0.25) / 1.25, 0.0, 1.0);

    vec3 hemiSky = (uStudioMode == 1) ? vec3(0.46, 0.46, 0.455) : vec3(0.20, 0.24, 0.32);
    vec3 hemiGnd = (uStudioMode == 1) ? vec3(0.27, 0.27, 0.265) : vec3(0.08, 0.09, 0.12);
    vec3 ambient = mix(hemiGnd, hemiSky, 0.5 + 0.5 * N.y);

    vec3 directLight =
        vec3(0.56, 0.56, 0.555) * dTop +
        vec3(0.26, 0.26, 0.265) * dFront +
        vec3(0.28, 0.28, 0.275) * dRear * (isInterior ? (0.30 + 0.70 * uBarnOpenFactor) : 1.0) +
        vec3(0.20, 0.20, 0.205) * dLeft;

    // Gentle interior cavity enclosure shading so ribbed cargo floor & wheel arches have crisp 3D depth!
    if (isInterior) {
      float rearOpenBoost = smoothstep(32.0, -106.0, lq.z) * (0.28 * uBarnOpenFactor);
      float cabWindowBoost = smoothstep(10.0, 62.0, lq.z) * 0.22;
      float cavityFactor = 0.62 + rearOpenBoost + cabWindowBoost;
      ambient *= cavityFactor;
      directLight *= (0.72 + 0.28 * cavityFactor);
    }

    // Subtle lower-body ground proximity AO
    float underAO = mix(0.68, 1.0, smoothstep(6.0, 26.0, lq.y));
    if (N.y < -0.35 && lq.y < 22.0) underAO *= 0.65;

    // Clearcoat & Matte Specular Highlights
    vec3 R = reflect(-V, N);
    float ndv = max(dot(N, V), 0.0);
    float fres = 0.035 + 0.22 * pow(1.0 - ndv, 4.0);

    vec3 H_top = normalize(L_top + V);
    vec3 H_fr  = normalize(L_front + V);
    vec3 H_rr  = normalize(L_rear + V);
    float specPow = mix(22.0, 96.0, isGlossPaint);
    float specStrength = mix(0.045, 0.16, isGlossPaint) * (isInterior ? 0.35 : 1.0);
    float spec = (
      pow(max(dot(N, H_top), 0.0), specPow) * 1.0 +
      pow(max(dot(N, H_fr),  0.0), specPow * 0.7) * 0.55 +
      pow(max(dot(N, H_rr),  0.0), specPow * 0.7) * 0.50
    ) * specStrength;

    // Subtle studio horizon clearcoat sheen on exterior panels
    float envBand = smoothstep(0.35, 0.88, R.y) * fres * isGlossPaint * (isInterior ? 0.0 : 0.22);

    vec3 color = albedo * (ambient + directLight) * underAO + vec3(spec + envBand);

    // Optional Headlight / Amber Marker / Ruby Taillight Emissive Glow ([L] toggle)
    if (uGlowGain > 0.01) {
      vec3 glow = pow(texture(uGlowTex, vUV).rgb, vec3(1.8)) * uGlowGain;
      color += glow;
    }

    // Tone map softly while preserving crisp Alpine White studio brightness
    vec3 mapped = (uStudioMode == 1)
      ? clamp(color / (1.0 + 0.16 * color), 0.0, 1.0)
      : acesFilm(color * 1.15);

    fragColor = vec4(pow(mapped, vec3(1.0 / 2.2)), 1.0);
  }`;

  // ---- C. 3D Line / Translucent Box Overlay Shader (Quake Collision Hulls & Player 32x32x56 Box) ----
  const LINE_VS = `#version 300 es
  precision highp float;
  layout(location = 0) in vec3 aPos;
  uniform mat4 uViewProj;
  uniform mat4 uModel;
  void main() {
    gl_Position = uViewProj * uModel * vec4(aPos, 1.0);
  }`;
  const LINE_FS = `#version 300 es
  precision highp float;
  uniform vec4 uColor;
  out vec4 fragColor;
  void main() { fragColor = uColor; }`;

  const bgProg   = compileProgram(BG_VS, BG_FS);
  const vanProg  = compileProgram(VAN_VS, VAN_FS);
  const lineProg = compileProgram(LINE_VS, LINE_FS);

  const bgUni = {
    uCamEye:     gl.getUniformLocation(bgProg, "uCamEye"),
    uCamFwd:     gl.getUniformLocation(bgProg, "uCamFwd"),
    uCamRight:   gl.getUniformLocation(bgProg, "uCamRight"),
    uCamUp:      gl.getUniformLocation(bgProg, "uCamUp"),
    uTanHalfFov: gl.getUniformLocation(bgProg, "uTanHalfFov"),
    uAspect:     gl.getUniformLocation(bgProg, "uAspect"),
    uStudioMode: gl.getUniformLocation(bgProg, "uStudioMode"),
    uVanPos:     gl.getUniformLocation(bgProg, "uVanPos"),
    uVanYaw:     gl.getUniformLocation(bgProg, "uVanYaw"),
    uBarnRad:    gl.getUniformLocation(bgProg, "uBarnRad"),
  };

  const vanUni = {
    uViewProj:       gl.getUniformLocation(vanProg, "uViewProj"),
    uModel:          gl.getUniformLocation(vanProg, "uModel"),
    uInvVan:         gl.getUniformLocation(vanProg, "uInvVan"),
    uAtlasTex:       gl.getUniformLocation(vanProg, "uAtlasTex"),
    uGlowTex:        gl.getUniformLocation(vanProg, "uGlowTex"),
    uGlassTex:       gl.getUniformLocation(vanProg, "uGlassTex"),
    uCamEye:         gl.getUniformLocation(vanProg, "uCamEye"),
    uPaintTint:      gl.getUniformLocation(vanProg, "uPaintTint"),
    uGlowGain:       gl.getUniformLocation(vanProg, "uGlowGain"),
    uBarnOpenFactor: gl.getUniformLocation(vanProg, "uBarnOpenFactor"),
    uPass:           gl.getUniformLocation(vanProg, "uPass"),
    uStudioMode:     gl.getUniformLocation(vanProg, "uStudioMode"),
  };

  const lineUni = {
    uViewProj: gl.getUniformLocation(lineProg, "uViewProj"),
    uModel:    gl.getUniformLocation(lineProg, "uModel"),
    uColor:    gl.getUniformLocation(lineProg, "uColor"),
  };

  const emptyVAO = gl.createVertexArray();

  // =========================================================================
  // 3. Decode Embedded Binary Meshes & Upload VBOs/IBOs (Exact 32B Stride!)
  // =========================================================================
  function b64ToBytes(b64) {
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return u8;
  }

  const gpuMeshes = DATA.meshes.map(m => {
    const vBytes = b64ToBytes(m.v_b64);
    const iBytes = b64ToBytes(m.i_b64);

    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);

    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, vBytes, gl.STATIC_DRAW);

    // 8 floats * 4 bytes = 32 bytes stride: aPos(3), aNorm(3), aUV(2)
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
    gl.enableVertexAttribArray(2);
    gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);

    const ibo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, iBytes, gl.STATIC_DRAW);

    // Build wireframe edge index buffer
    const idx16 = new Uint16Array(iBytes.buffer);
    const edgeLines = new Uint16Array(idx16.length * 2);
    let ei = 0;
    for (let t = 0; t < idx16.length; t += 3) {
      const a = idx16[t], b = idx16[t+1], c = idx16[t+2];
      edgeLines[ei++] = a; edgeLines[ei++] = b;
      edgeLines[ei++] = b; edgeLines[ei++] = c;
      edgeLines[ei++] = c; edgeLines[ei++] = a;
    }
    const wVao = gl.createVertexArray();
    gl.bindVertexArray(wVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
    const wIbo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, wIbo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edgeLines, gl.STATIC_DRAW);

    gl.bindVertexArray(null);
    return { ...m, vao, wVao, nWireIdx: edgeLines.length, modelMat: mat4Identity() };
  });

  // Build Quake Collision Hull Wireframe & Translucent Fill Buffers
  function buildBoxVAO(x0, x1, y0, y1, z0, z1) {
    // Convert Quake (x,y,z) box to WebGL (y*S, z*S, x*S)
    const X0 = y0*S, X1 = y1*S, Y0 = z0*S, Y1 = z1*S, Z0 = x0*S, Z1 = x1*S;
    const v = new Float32Array([
      X0,Y0,Z0,  X1,Y0,Z0,  X1,Y1,Z0,  X0,Y1,Z0,
      X0,Y0,Z1,  X1,Y0,Z1,  X1,Y1,Z1,  X0,Y1,Z1
    ]);
    const lines = new Uint16Array([
      0,1, 1,2, 2,3, 3,0,  4,5, 5,6, 6,7, 7,4,  0,4, 1,5, 2,6, 3,7
    ]);
    const tris = new Uint16Array([
      0,1,2, 0,2,3,  4,6,5, 4,7,6,  0,4,5, 0,5,1,
      2,6,7, 2,7,3,  0,3,7, 0,7,4,  1,5,6, 1,6,2
    ]);
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 12, 0);
    const iboL = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, iboL);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, lines, gl.STATIC_DRAW);

    const vaoT = gl.createVertexArray();
    gl.bindVertexArray(vaoT);
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 12, 0);
    const iboT = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, iboT);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tris, gl.STATIC_DRAW);
    gl.bindVertexArray(null);
    return { vaoL: vao, vaoT };
  }

  const hullColors = {
    step:  [0.20, 0.90, 0.55],
    floor: [0.22, 0.72, 0.98],
    wall:  [0.98, 0.62, 0.18],
    door:  [0.95, 0.42, 0.68],
    roof:  [0.68, 0.55, 0.98],
    arch:  [0.98, 0.84, 0.22],
    bulk:  [0.96, 0.40, 0.34],
    trig:  [0.15, 0.98, 0.45],
  };
  const gpuHulls = DATA.collisionBoxes.map(h => ({
    ...h,
    color: hullColors[h.kind] || [0.3, 0.8, 1.0],
    ...buildBoxVAO(...h.b)
  }));
  // Reference 32x32x56 Quake Player Hull standing inside cargo bay (x_q=-24, y_q=0, z_q=19.5..75.5)
  const playerRefHull = buildBoxVAO(-40, -8, -16, 16, 19.5, 75.5);

  // =========================================================================
  // 4. Load 2K Atlas, RGBA Glass & Glow Textures (with 16x Anisotropic Mips!)
  // =========================================================================
  let texturesReady = 0;
  function loadGLTexture(uri, rgbaMode) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
                  new Uint8Array(rgbaMode ? [150, 184, 176, 80] : [236, 238, 240, 255]));
    const img = new Image();
    img.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); // UVs authored with v=0 at PNG top!
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      if (extAniso) {
        const maxAniso = gl.getParameter(extAniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT);
        gl.texParameterf(gl.TEXTURE_2D, extAniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(16, maxAniso));
      }
      texturesReady++;
      if (texturesReady === 3) window.__VAN_VIEWER_READY = true;
    };
    img.src = uri;
    return tex;
  }

  const texAtlas = loadGLTexture(ATLAS_URI, false);
  const texGlass = loadGLTexture(GLASS_URI, true);
  const texGlow  = loadGLTexture(GLOW_URI,  false);

  // =========================================================================
  // 5. Viewer State, Articulation, Walk-In Quake Physics & Test-Drive Physics
  // =========================================================================
  const p0 = DATA.presets[0];
  const state = {
    mode: "orbit",         // "orbit" | "walk" | "drive"
    driveChaseCam: false,  // [V] toggle between 1st-person driver seat & 3rd-person chase cam in Drive mode
    studioMode: 1,         // 1 = Studio Cyclorama (matches reference video), 0 = Quake Dark Grid
    turntable: false,
    cutaway: false,
    showHulls: false,
    lightsOn: false,
    wireframe: false,
    paintTint: [1.0, 1.0, 1.0],

    // Articulation sliders
    barnDeg: DATA.defaultBarnDeg, // 126 deg matching reference video!
    cabDeg: 0,
    hoodDeg: 0,
    steerDeg: 0,
    wheelSpinRad: 0,

    // Smooth Orbit Camera
    yaw: p0.yaw,     goalYaw: p0.yaw,
    pitch: p0.pitch, goalPitch: p0.pitch,
    dist: p0.dist,   goalDist: p0.dist,
    target: [...p0.target], goalTarget: [...p0.target],
    fovDeg: p0.fov,  goalFovDeg: p0.fov,

    // First-Person Quake Walk-In Player (in van-local Quake units: feet at z_q, 32x32x56 hull)
    plQ: [-168.0, 0.0, 0.0], // behind open rear barn doors!
    plVz: 0.0,
    plOnGround: true,
    plYaw: 0.0,    // 0 = looking +X_q (straight into open cargo bay!)
    plPitch: 0.02,
    inCockpitTrigger: false,

    // Drivable Van State (WebGL meters)
    vanPos: [0.0, 0.0, 0.0],
    vanYaw: 0.0,
    vanSpeed: 0.0,
    vanPitch: 0.0,
    vanRoll: 0.0,
  };

  // Optional synthesized WebAudio Diesel Idle & Horn (activates cleanly on user interaction)
  let audioCtx = null, engineOsc = null, engineGain = null;
  function ensureAudio() {
    if (audioCtx) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      audioCtx = new AC();
      engineOsc = audioCtx.createOscillator();
      engineOsc.type = "sawtooth";
      engineOsc.frequency.value = 46;
      const filt = audioCtx.createBiquadFilter();
      filt.type = "lowpass";
      filt.frequency.value = 155;
      engineGain = audioCtx.createGain();
      engineGain.gain.value = 0.0;
      engineOsc.connect(filt);
      filt.connect(engineGain);
      engineGain.connect(audioCtx.destination);
      engineOsc.start();
    } catch (_) {}
  }
  function playHorn() {
    ensureAudio();
    if (!audioCtx) return;
    const now = audioCtx.currentTime;
    [340, 425].forEach(freq => {
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = "sawtooth"; o.frequency.value = freq;
      g.gain.setValueAtTime(0.08, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.34);
      o.connect(g); g.connect(audioCtx.destination);
      o.start(now); o.stop(now + 0.35);
    });
  }

  // =========================================================================
  // 6. UI Controls & Keyboard/Mouse Input
  // =========================================================================
  const presetGrid = document.getElementById("presetGrid");
  const presetBtns = DATA.presets.map((pr, idx) => {
    const b = document.createElement("button");
    b.textContent = pr.label;
    if (idx === 0) b.classList.add("active");
    b.addEventListener("click", () => applyPreset(idx));
    presetGrid.appendChild(b);
    return b;
  });

  function applyPreset(idx, instant = false) {
    const pr = DATA.presets[idx];
    if (!pr) return;
    setMode("orbit");
    state.turntable = false;
    document.getElementById("btnSpin").classList.remove("active");
    // Unwrap yaw delta for shortest smooth turn
    let dy = pr.yaw - state.yaw;
    while (dy >  Math.PI) dy -= Math.PI * 2;
    while (dy < -Math.PI) dy += Math.PI * 2;
    state.goalYaw = state.yaw + dy;
    state.goalPitch = pr.pitch;
    state.goalDist = pr.dist;
    state.goalTarget = [
      state.vanPos[0] + pr.target[0] * Math.cos(state.vanYaw) + pr.target[2] * Math.sin(state.vanYaw),
      pr.target[1],
      state.vanPos[2] - pr.target[0] * Math.sin(state.vanYaw) + pr.target[2] * Math.cos(state.vanYaw)
    ];
    state.goalFovDeg = pr.fov;
    if (instant) {
      state.yaw = state.goalYaw;
      state.pitch = state.goalPitch;
      state.dist = state.goalDist;
      state.target = [...state.goalTarget];
      state.fovDeg = state.goalFovDeg;
    }
    presetBtns.forEach((btn, i) => btn.classList.toggle("active", i === idx));
  }
  window.applyVanPreset = applyPreset;

  const hudText = document.getElementById("hudText");
  const crosshair = document.getElementById("crosshair");
  const centerBanner = document.getElementById("centerBanner");

  function setMode(newMode) {
    if (state.mode === newMode) return;
    const prevMode = state.mode;
    state.mode = newMode;

    document.getElementById("btnModeOrbit").classList.toggle("active", newMode === "orbit");
    document.getElementById("btnModeWalk").classList.toggle("activeOk", newMode === "walk");
    document.getElementById("btnModeDrive").classList.toggle("activeWarm", newMode === "drive");
    crosshair.style.display = (newMode === "walk") ? "block" : "none";

    if (newMode === "walk") {
      if (prevMode === "drive") {
        // Step out from driver seat into central bulkhead aisle!
        state.plQ = [28.0, 0.0, 19.5];
        state.plYaw = Math.PI; // facing rear cargo doorway
        state.plPitch = -0.05;
      } else {
        state.plQ = [-164.0, 0.0, 0.0];
        state.plYaw = 0.0;
        state.plPitch = 0.03;
      }
      state.plVz = 0;
      hudText.innerHTML =
        `<b>Quake Walk-In (32×32×56 Hull):</b> <span class="kbd">WASD</span> Walk • ` +
        `Drag/Mouse Look • <span class="kbd">Space</span> Jump • Walk up rear step into cockpit & press <span class="kbd">E</span> to Drive!`;
    } else if (newMode === "drive") {
      ensureAudio();
      state.cutaway = false;
      document.getElementById("btnCutaway").classList.remove("active");
      centerBanner.classList.remove("show");
      hudText.innerHTML =
        `<b>Drivable ProMaster Van:</b> <span class="kbd">W/S</span> Throttle/Reverse • ` +
        `<span class="kbd">A/D</span> Steer • <span class="kbd">V</span> Cockpit / Chase Cam • ` +
        `<span class="kbd">Space</span> Horn • <span class="kbd">E</span> Park & Walk Out`;
    } else {
      centerBanner.classList.remove("show");
      if (document.pointerLockElement === canvas) document.exitPointerLock();
      hudText.innerHTML =
        `<b>Orbit:</b> Left-Drag • <b>Pan:</b> Right-Drag • <b>Zoom:</b> Wheel • ` +
        `Press <span class="kbd">F</span> to Walk Inside Cargo Bay • <span class="kbd">1–8</span> Views`;
    }
    if (engineGain && audioCtx) {
      engineGain.gain.setTargetAtTime(newMode === "drive" ? 0.035 : 0.0, audioCtx.currentTime, 0.12);
    }
  }

  document.getElementById("btnModeOrbit").onclick = () => setMode("orbit");
  document.getElementById("btnModeWalk").onclick  = () => setMode("walk");
  document.getElementById("btnModeDrive").onclick = () => setMode("drive");

  const sidePanel = document.getElementById("sidePanel");
  const btnTogglePanel = document.getElementById("btnTogglePanel");
  btnTogglePanel.onclick = () => {
    const hidden = sidePanel.classList.toggle("hidden");
    btnTogglePanel.textContent = hidden ? "Show UI" : "Hide UI";
  };

  function bindSlider(id, valId, key) {
    const sl = document.getElementById(id);
    const vl = document.getElementById(valId);
    sl.addEventListener("input", () => {
      state[key] = parseFloat(sl.value);
      vl.textContent = `${state[key]}°`;
    });
  }
  bindSlider("slBarn",  "valBarn",  "barnDeg");
  bindSlider("slCab",   "valCab",   "cabDeg");
  bindSlider("slHood",  "valHood",  "hoodDeg");
  bindSlider("slSteer", "valSteer", "steerDeg");

  document.getElementById("btnBgTheme").onclick = function () {
    state.studioMode = state.studioMode ? 0 : 1;
    this.classList.toggle("active", state.studioMode === 1);
    this.textContent = state.studioMode ? "Studio Cove" : "Quake Grid";
  };
  document.getElementById("btnSpin").onclick = function () {
    state.turntable = !state.turntable;
    this.classList.toggle("active", state.turntable);
  };
  document.getElementById("btnCutaway").onclick = function () {
    state.cutaway = !state.cutaway;
    this.classList.toggle("active", state.cutaway);
  };
  document.getElementById("btnHulls").onclick = function () {
    state.showHulls = !state.showHulls;
    this.classList.toggle("active", state.showHulls);
  };
  document.getElementById("btnLights").onclick = function () {
    state.lightsOn = !state.lightsOn;
    this.classList.toggle("activeWarm", state.lightsOn);
    this.textContent = state.lightsOn ? "Lights On" : "Lights Off";
  };
  document.getElementById("btnWire").onclick = function () {
    state.wireframe = !state.wireframe;
    this.classList.toggle("active", state.wireframe);
  };

  document.querySelectorAll(".swatch").forEach(sw => {
    sw.addEventListener("click", () => {
      document.querySelectorAll(".swatch").forEach(s => s.classList.remove("active"));
      sw.classList.add("active");
      state.paintTint = sw.dataset.tint.split(",").map(Number);
    });
  });

  // Mouse & Pointer Lock Controls
  let dragBtn = -1, lastX = 0, lastY = 0;
  canvas.addEventListener("contextmenu", e => e.preventDefault());
  canvas.addEventListener("mousedown", e => {
    dragBtn = e.button; lastX = e.clientX; lastY = e.clientY;
    if (state.mode === "walk" && e.button === 0 && canvas.requestPointerLock) {
      canvas.requestPointerLock();
    }
  });
  window.addEventListener("mouseup", () => { dragBtn = -1; });
  window.addEventListener("mousemove", e => {
    const locked = (document.pointerLockElement === canvas);
    if (state.mode === "walk" && (locked || dragBtn === 0)) {
      const dx = locked ? e.movementX : (e.clientX - lastX);
      const dy = locked ? e.movementY : (e.clientY - lastY);
      lastX = e.clientX; lastY = e.clientY;
      state.plYaw   -= dx * 0.0032; // Quake +Y_q is left -> dragging mouse right turns right (-yaw)!
      state.plPitch  = Math.max(-1.35, Math.min(1.35, state.plPitch - dy * 0.0030));
      return;
    }
    if (state.mode === "orbit" && dragBtn >= 0) {
      const dx = e.clientX - lastX, dy = e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      state.turntable = false;
      document.getElementById("btnSpin").classList.remove("active");
      presetBtns.forEach(b => b.classList.remove("active"));
      if (dragBtn === 0) {
        state.goalYaw   -= dx * 0.0055;
        state.goalPitch  = Math.max(-0.08, Math.min(1.46, state.goalPitch + dy * 0.0055));
      } else {
        const panScale = state.dist * 0.0011;
        const cy = Math.cos(state.yaw), sy = Math.sin(state.yaw);
        state.goalTarget[0] -= cy * dx * panScale;
        state.goalTarget[2] += sy * dx * panScale;
        state.goalTarget[1] = Math.max(0.15, state.goalTarget[1] + dy * panScale);
      }
    }
  });
  canvas.addEventListener("wheel", e => {
    e.preventDefault();
    if (state.mode === "orbit") {
      state.goalDist = Math.max(1.2, Math.min(26.0, state.goalDist * Math.exp(e.deltaY * 0.0010)));
    }
  }, { passive: false });

  // Keyboard Controls
  const keys = {};
  window.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") return;
    const k = e.key.toLowerCase();
    keys[k] = true;
    if (k >= "1" && k <= "8") applyPreset(parseInt(k, 10) - 1);
    else if (k === "f") setMode(state.mode === "walk" ? "orbit" : "walk");
    else if (k === "e") {
      if (state.mode === "drive") setMode("walk");
      else if (state.mode === "walk") setMode("drive");
      else setMode("drive");
    }
    else if (k === "v" && state.mode === "drive") state.driveChaseCam = !state.driveChaseCam;
    else if (k === "h") btnTogglePanel.click();
    else if (k === "b") document.getElementById("btnBgTheme").click();
    else if (k === "t") document.getElementById("btnSpin").click();
    else if (k === "x") document.getElementById("btnCutaway").click();
    else if (k === "c") document.getElementById("btnHulls").click();
    else if (k === "l") document.getElementById("btnLights").click();
    else if (k === "m") document.getElementById("btnWire").click();
    else if (k === " " && state.mode === "drive") { e.preventDefault(); playHorn(); }
  });
  window.addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });

  // =========================================================================
  // 7. Quake 32x32x56 Walk-In Collision & Step-Up Physics (18u STEPSIZE!)
  // =========================================================================
  function getActiveSolidBoxesQ() {
    // Exact 12 SOLID_BBOX hulls from Veh_Van_InitCollision + closed barn door blocker when barnDeg < 58 deg!
    const boxes = [];
    for (const h of DATA.collisionBoxes) {
      if (h.kind === "trig") continue;
      if (h.kind === "door") {
        if (state.barnDeg >= 58) boxes.push(h.b);
      } else {
        boxes.push(h.b);
      }
    }
    if (state.barnDeg < 58) {
      // Closed rear barn doors block the rear aperture (-110..-106, -38..38, 19.5..97)
      boxes.push([-110, -106, -38, 38, 19.5, 97.0]);
    }
    return boxes;
  }

  function playerOverlapsBox(px, py, pz, b) {
    // Quake player hull: 32x32 wide (-16..+16), 56u tall (feet at pz .. pz+56)
    const H = 15.0; // slight 1u skin tolerance so 35u bulkhead aisle feels silky smooth
    return (px + H > b[0] && px - H < b[1] &&
            py + H > b[2] && py - H < b[3] &&
            pz + 55.5 > b[4] && pz + 0.1 < b[5]);
  }

  function floorHeightAt(px, py, pzFeet, boxes) {
    let maxZ = 0.0;
    const H = 14.5;
    for (const b of boxes) {
      if (px + H > b[0] && px - H < b[1] && py + H > b[2] && py - H < b[3]) {
        // Quake STEPSIZE = 18u: can step onto any surface whose top b[5] <= pzFeet + 18.0!
        if (b[5] <= pzFeet + 18.0 && b[5] > maxZ) {
          // Verify 56u headroom above b[5]
          let headroomBlocked = false;
          for (const c of boxes) {
            if (c !== b && px + H > c[0] && px - H < c[1] && py + H > c[2] && py - H < c[3]) {
              if (c[4] > b[5] && c[4] < b[5] + 56.0) { headroomBlocked = true; break; }
            }
          }
          if (!headroomBlocked) maxZ = b[5];
        }
      }
    }
    return maxZ;
  }

  function updateWalkMode(dt) {
    const boxes = getActiveSolidBoxesQ();
    let fwd = (keys["w"] || keys["arrowup"] ? 1 : 0) - (keys["s"] || keys["arrowdown"] ? 1 : 0);
    let str = (keys["a"] || keys["arrowleft"] ? 1 : 0) - (keys["d"] || keys["arrowright"] ? 1 : 0); // +Y_q is Left!
    const len = Math.hypot(fwd, str);
    if (len > 0) { fwd /= len; str /= len; }

    const speed = 135.0; // Quake units/sec comfortable walk-in inspection speed
    const cy = Math.cos(state.plYaw), sy = Math.sin(state.plYaw);
    const vx = (fwd * cy - str * sy) * speed;
    const vy = (fwd * sy + str * cy) * speed;

    // Axis-separated slide + 18u Quake step-up
    for (const [dx, dy] of [[vx * dt, 0], [0, vy * dt]]) {
      const nx = state.plQ[0] + dx;
      const ny = state.plQ[1] + dy;
      const stepFloor = floorHeightAt(nx, ny, state.plQ[2], boxes);
      const tryZ = Math.max(state.plQ[2], stepFloor);
      let hit = false;
      for (const b of boxes) {
        if (playerOverlapsBox(nx, ny, tryZ, b)) { hit = true; break; }
      }
      if (!hit) {
        state.plQ[0] = Math.max(-360, Math.min(360, nx));
        state.plQ[1] = Math.max(-360, Math.min(360, ny));
        if (tryZ > state.plQ[2]) state.plQ[2] = tryZ;
      }
    }

    // Jump & Gravity
    if (keys[" "] && state.plOnGround) {
      state.plVz = 185.0;
      state.plOnGround = false;
    }
    state.plVz -= 560.0 * dt;
    state.plQ[2] += state.plVz * dt;
    const groundZ = floorHeightAt(state.plQ[0], state.plQ[1], state.plQ[2] + 2.0, boxes);
    if (state.plQ[2] <= groundZ) {
      state.plQ[2] = groundZ;
      state.plVz = 0;
      state.plOnGround = true;
    }

    // Check Box 13: Cockpit Driver Interaction Trigger (x: 36..66, y: -16..34, z: 19.5..76)
    const inTrig = (state.plQ[0] > 32 && state.plQ[0] < 67 &&
                    state.plQ[1] > -18 && state.plQ[1] < 35 &&
                    state.plQ[2] >= 18.5);
    if (inTrig !== state.inCockpitTrigger) {
      state.inCockpitTrigger = inTrig;
      centerBanner.classList.toggle("show", inTrig);
    }
  }

  function updateDriveMode(dt) {
    const thr = (keys["w"] || keys["arrowup"] ? 1 : 0) - (keys["s"] || keys["arrowdown"] ? 1 : 0);
    const str = (keys["a"] || keys["arrowleft"] ? 1 : 0) - (keys["d"] || keys["arrowright"] ? 1 : 0);

    // Smooth steering wheel return & input
    const targetSteer = str * 30.0;
    state.steerDeg += (targetSteer - state.steerDeg) * Math.min(1.0, dt * 7.5);
    document.getElementById("slSteer").value = Math.round(state.steerDeg);
    document.getElementById("valSteer").textContent = `${Math.round(state.steerDeg)}°`;

    const accel = thr * 7.5;
    state.vanSpeed += accel * dt;
    state.vanSpeed *= Math.exp(-1.6 * dt);
    if (Math.abs(state.vanSpeed) < 0.02 && thr === 0) state.vanSpeed = 0;
    state.vanSpeed = Math.max(-6.5, Math.min(14.5, state.vanSpeed));

    // Bicycle model turning (wheelbase = (80 - -68)*0.025 = 3.70 m)
    const steerRad = state.steerDeg * Math.PI / 180.0;
    const angularVel = (state.vanSpeed / 3.70) * Math.tan(steerRad);
    state.vanYaw += angularVel * dt;

    // Move van along forward (+Z_gl rotated by vanYaw -> (sin(vanYaw), 0, cos(vanYaw)))
    state.vanPos[0] += Math.sin(state.vanYaw) * state.vanSpeed * dt;
    state.vanPos[2] += Math.cos(state.vanYaw) * state.vanSpeed * dt;

    // Roll 4 16" steelie wheels (wheel radius = 15.2 * 0.025 = 0.38 m)
    state.wheelSpinRad += (state.vanSpeed * dt) / 0.38;

    // Subtle commercial suspension pitch & body roll
    const targetPitch = -accel * 0.0038;
    const targetRoll  = -state.vanSpeed * angularVel * 0.0055;
    state.vanPitch += (targetPitch - state.vanPitch) * Math.min(1, dt * 8);
    state.vanRoll  += (targetRoll  - state.vanRoll)  * Math.min(1, dt * 8);

    if (engineOsc && audioCtx) {
      const rpmFreq = 46 + Math.abs(state.vanSpeed) * 6.8 + Math.abs(thr) * 14;
      engineOsc.frequency.setTargetAtTime(rpmFreq, audioCtx.currentTime, 0.08);
    }
  }

  // =========================================================================
  // 8. Main Render Loop
  // =========================================================================
  let prevTime = performance.now();

  function renderFrame(now) {
    const dt = Math.min(0.05, Math.max(0.001, (now - prevTime) * 0.001));
    prevTime = now;

    // Resize canvas cleanly for crisp HiDPI
    const dpr = Math.min(window.devicePixelRatio || 1, 2.0);
    const cw = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    const ch = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== cw || canvas.height !== ch) {
      canvas.width = cw; canvas.height = ch;
    }
    gl.viewport(0, 0, cw, ch);
    const aspect = cw / ch;

    if (state.mode === "walk") updateWalkMode(dt);
    else if (state.mode === "drive") updateDriveMode(dt);
    else {
      state.vanPitch *= Math.exp(-8 * dt);
      state.vanRoll  *= Math.exp(-8 * dt);
      if (state.turntable) state.goalYaw += dt * 0.38;
    }

    // Root Van World Matrix & Exact Inverse
    const mVanTrans = mat4Translate(state.vanPos[0], state.vanPos[1], state.vanPos[2]);
    const mVanYaw   = mat4AxisAngle([0, 1, 0], state.vanYaw);
    const mVanSusp  = mat4Mul(mat4AxisAngle([1, 0, 0], state.vanPitch), mat4AxisAngle([0, 0, 1], state.vanRoll));
    const mVan      = mat4Mul(mVanTrans, mat4Mul(mVanYaw, mVanSusp));
    const mInvVan   = mat4Mul(
      mat4Mul(mat4AxisAngle([0, 0, 1], -state.vanRoll), mat4AxisAngle([1, 0, 0], -state.vanPitch)),
      mat4Mul(mat4AxisAngle([0, 1, 0], -state.vanYaw), mat4Translate(-state.vanPos[0], -state.vanPos[1], -state.vanPos[2]))
    );

    // Compute Camera Eye, Target & FOV
    let camEye, camCtr, fovRad;
    if (state.mode === "walk") {
      // Quake eye height = feet_z + 44u (63.5u on 19.5u cargo floor -> clear of 96.5u ceiling & matches cab windows!)
      const eyeLocalGL = [state.plQ[1] * S, (state.plQ[2] + 44.0) * S, state.plQ[0] * S];
      const lookLocalGL = [
        eyeLocalGL[0] + Math.cos(state.plPitch) * Math.sin(state.plYaw),
        eyeLocalGL[1] + Math.sin(state.plPitch),
        eyeLocalGL[2] + Math.cos(state.plPitch) * Math.cos(state.plYaw)
      ];
      camEye = transformPoint(mVan, eyeLocalGL);
      camCtr = transformPoint(mVan, lookLocalGL);
      fovRad = 68.0 * Math.PI / 180.0;
    } else if (state.mode === "drive") {
      if (!state.driveChaseCam) {
        // 1st-Person Left-Hand Driver's Seat (x_q=44.5, y_q=19.8, z_q=62.5)
        const eyeLocal = [19.8 * S, 62.5 * S, 44.5 * S];
        const lookLocal = [(19.8 + state.steerDeg * 0.25) * S, 55.5 * S, 145.0 * S];
        camEye = transformPoint(mVan, eyeLocal);
        camCtr = transformPoint(mVan, lookLocal);
        fovRad = 64.0 * Math.PI / 180.0;
      } else {
        // 3rd-Person Chase Camera
        camEye = transformPoint(mVan, [0.0, 3.35, -8.8]);
        camCtr = transformPoint(mVan, [0.0, 1.35,  1.8]);
        fovRad = 38.0 * Math.PI / 180.0;
      }
    } else {
      const kLerp = Math.min(1.0, dt * 11.0);
      state.yaw    += (state.goalYaw    - state.yaw)    * kLerp;
      state.pitch  += (state.goalPitch  - state.pitch)  * kLerp;
      state.dist   += (state.goalDist   - state.dist)   * kLerp;
      state.fovDeg += (state.goalFovDeg - state.fovDeg) * kLerp;
      for (let i = 0; i < 3; i++) state.target[i] += (state.goalTarget[i] - state.target[i]) * kLerp;

      camCtr = state.target;
      camEye = [
        camCtr[0] + state.dist * Math.cos(state.pitch) * Math.sin(state.yaw),
        Math.max(0.08, camCtr[1] + state.dist * Math.sin(state.pitch)),
        camCtr[2] + state.dist * Math.cos(state.pitch) * Math.cos(state.yaw)
      ];
      fovRad = state.fovDeg * Math.PI / 180.0;
    }

    const mProj = mat4Perspective(fovRad, aspect, 0.06, 180.0);
    const mView = mat4LookAt(camEye, camCtr, [0, 1, 0]);
    const mVP   = mat4Mul(mProj, mView);

    // Camera basis vectors for ray-traced cyclorama floor & soft AO shadows
    let fx = camCtr[0]-camEye[0], fy = camCtr[1]-camEye[1], fz = camCtr[2]-camEye[2];
    const fl = Math.hypot(fx, fy, fz) || 1; fx/=fl; fy/=fl; fz/=fl;
    let rx = fy*0 - fz*1, ry = fz*0 - fx*0, rz = fx*1 - fy*0; // cross(fwd, up=(0,1,0)) = (-fz, 0, fx)... wait:
    // Right = normalize(cross(fwd, [0,1,0])) = [ -fz, 0, fx ]? Let's compute exact cross(fwd, [0,1,0]):
    // fwd x up = (fy*0 - fz*1, fz*0 - fx*0, fx*1 - fy*0) = (-fz, 0, fx)!
    rx = -fz; ry = 0.0; rz = fx;
    const rl = Math.hypot(rx, ry, rz) || 1; rx/=rl; ry/=rl; rz/=rl;
    const ux = ry*fz - rz*fy, uy = rz*fx - rx*fz, uz = rx*fy - ry*fx;

    const barnRad  = state.barnDeg  * Math.PI / 180.0;
    const cabRad   = state.cabDeg   * Math.PI / 180.0;
    const hoodRad  = state.hoodDeg  * Math.PI / 180.0;
    const steerRad = state.steerDeg * Math.PI / 180.0;

    // Update per-part articulated world matrices
    for (const m of gpuMeshes) {
      let localM = mat4Identity();
      switch (m.anim) {
        case "barn_l":   localM = mat4PivotAxisAngle(m.pivot, m.axis, -barnRad); break;
        case "barn_r":   localM = mat4PivotAxisAngle(m.pivot, m.axis, +barnRad); break;
        case "door_l":   localM = mat4PivotAxisAngle(m.pivot, m.axis, -cabRad);  break;
        case "door_r":   localM = mat4PivotAxisAngle(m.pivot, m.axis, +cabRad);  break;
        case "hood":     localM = mat4PivotAxisAngle(m.pivot, m.axis, -hoodRad); break;
        case "steer_sw": localM = mat4PivotAxisAngle(m.pivot, m.axis, -steerRad * 4.5); break;
        case "wheel_fl":
        case "wheel_fr": {
          const p = m.pivot;
          localM = mat4Mul(
            mat4Translate(p[0], p[1], p[2]),
            mat4Mul(mat4AxisAngle([0, 1, 0], steerRad),
            mat4Mul(mat4AxisAngle([1, 0, 0], state.wheelSpinRad), mat4Translate(-p[0], -p[1], -p[2])))
          );
          break;
        }
        case "wheel_rl":
        case "wheel_rr":
          localM = mat4PivotAxisAngle(m.pivot, [1, 0, 0], state.wheelSpinRad);
          break;
      }
      m.modelMat = mat4Mul(mVan, localM);
    }

    // ---- 1. Draw Studio Cyclorama / Quake Grid Sky & Floor ----
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);
    gl.depthMask(false);
    gl.useProgram(bgProg);
    gl.uniform3fv(bgUni.uCamEye, camEye);
    gl.uniform3f(bgUni.uCamFwd, fx, fy, fz);
    gl.uniform3f(bgUni.uCamRight, rx, ry, rz);
    gl.uniform3f(bgUni.uCamUp, ux, uy, uz);
    gl.uniform1f(bgUni.uTanHalfFov, Math.tan(fovRad * 0.5));
    gl.uniform1f(bgUni.uAspect, aspect);
    gl.uniform1i(bgUni.uStudioMode, state.studioMode);
    gl.uniform3fv(bgUni.uVanPos, state.vanPos);
    gl.uniform1f(bgUni.uVanYaw, state.vanYaw);
    gl.uniform1f(bgUni.uBarnRad, barnRad);
    gl.bindVertexArray(emptyVAO);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    // ---- 2. Draw Opaque 2K Sculpted Van Parts ----
    gl.depthMask(true);
    gl.clear(gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    gl.disable(gl.CULL_FACE); // double-sided geometry already authored with exact outward/inward split normals

    gl.useProgram(vanProg);
    gl.uniformMatrix4fv(vanUni.uViewProj, false, mVP);
    gl.uniformMatrix4fv(vanUni.uInvVan, false, mInvVan);
    gl.uniform3fv(vanUni.uCamEye, camEye);
    gl.uniform3fv(vanUni.uPaintTint, state.paintTint);
    gl.uniform1f(vanUni.uGlowGain, state.lightsOn ? 2.1 : 0.0);
    gl.uniform1f(vanUni.uBarnOpenFactor, Math.min(1.0, state.barnDeg / 90.0));
    gl.uniform1i(vanUni.uStudioMode, state.studioMode);

    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, texAtlas); gl.uniform1i(vanUni.uAtlasTex, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, texGlow);  gl.uniform1i(vanUni.uGlowTex, 1);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, texGlass); gl.uniform1i(vanUni.uGlassTex, 2);

    gl.uniform1i(vanUni.uPass, 0);
    for (const m of gpuMeshes) {
      if (m.pass !== 0) continue;
      if (state.cutaway && m.hideCut) continue;
      gl.uniformMatrix4fv(vanUni.uModel, false, m.modelMat);
      gl.bindVertexArray(m.vao);
      gl.drawElements(gl.TRIANGLES, m.n_idx, gl.UNSIGNED_SHORT, 0);
    }

    // ---- 3. Draw Back-to-Front Sorted Translucent Cab Glass & Wire-Mesh Bulkhead ----
    const glassList = gpuMeshes.filter(m => m.pass === 1 && !(state.cutaway && m.hideCut));
    glassList.sort((a, b) => {
      const ca = transformPoint(a.modelMat, a.centroid);
      const cb = transformPoint(b.modelMat, b.centroid);
      const da = (ca[0]-camEye[0])**2 + (ca[1]-camEye[1])**2 + (ca[2]-camEye[2])**2;
      const db = (cb[0]-camEye[0])**2 + (cb[1]-camEye[1])**2 + (cb[2]-camEye[2])**2;
      return db - da; // farthest first!
    });

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.depthMask(false);
    gl.uniform1i(vanUni.uPass, 1);
    for (const m of glassList) {
      gl.uniformMatrix4fv(vanUni.uModel, false, m.modelMat);
      gl.bindVertexArray(m.vao);
      gl.drawElements(gl.TRIANGLES, m.n_idx, gl.UNSIGNED_SHORT, 0);
    }

    // ---- 4. Optional Triangle Wireframe Overlay ----
    if (state.wireframe) {
      gl.useProgram(lineProg);
      gl.uniformMatrix4fv(lineUni.uViewProj, false, mVP);
      gl.uniform4f(lineUni.uColor, 0.12, 0.82, 1.0, 0.42);
      for (const m of gpuMeshes) {
        if (state.cutaway && m.hideCut) continue;
        gl.uniformMatrix4fv(lineUni.uModel, false, m.modelMat);
        gl.bindVertexArray(m.wVao);
        gl.drawElements(gl.LINES, m.nWireIdx, gl.UNSIGNED_SHORT, 0);
      }
    }

    // ---- 5. Optional 13 Quake Collision Hulls + 32x32x56 Player Hull Overlay ----
    if (state.showHulls) {
      gl.useProgram(lineProg);
      gl.uniformMatrix4fv(lineUni.uViewProj, false, mVP);
      gl.uniformMatrix4fv(lineUni.uModel, false, mVan);

      for (const h of gpuHulls) {
        if (h.kind === "door" && state.barnDeg < 58) continue;
        gl.uniform4f(lineUni.uColor, h.color[0], h.color[1], h.color[2], 0.14);
        gl.bindVertexArray(h.vaoT);
        gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);

        gl.uniform4f(lineUni.uColor, h.color[0], h.color[1], h.color[2], 0.88);
        gl.bindVertexArray(h.vaoL);
        gl.drawElements(gl.LINES, 24, gl.UNSIGNED_SHORT, 0);
      }
      // 32x32x56 Quake Player Reference Box standing inside cargo bay
      gl.uniform4f(lineUni.uColor, 0.25, 1.0, 0.95, 0.22);
      gl.bindVertexArray(playerRefHull.vaoT);
      gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);
      gl.uniform4f(lineUni.uColor, 0.45, 1.0, 1.0, 0.95);
      gl.bindVertexArray(playerRefHull.vaoL);
      gl.drawElements(gl.LINES, 24, gl.UNSIGNED_SHORT, 0);
    }

    gl.depthMask(true);
    gl.disable(gl.BLEND);
    requestAnimationFrame(renderFrame);
  }

  requestAnimationFrame(renderFrame);
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build_viewer()
