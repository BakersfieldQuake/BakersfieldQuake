r"""Builds the 100% Self-Contained Offline WebGL2 Interactive 3D Wild Vehicle Explosion Studio:
  G:\Quake\Combat\BakersfieldQuake\wild_vehicles_explosion.html

Features the 3 NEW Realistic Shootable / Wild-Exploding 3D Vehicles:
  1. Heavy-Duty Crew-Cab Diesel Dually Rig Truck (hdtruck, 6 Flying Wheels!)
  2. Type-C Conventional Yellow School Bus (schoolbus, 6 Flying Wheels + STOP Sign!)
  3. V8 Street Muscle Fastback Car (gtcar, 4 Wide Twin-Spoke Wheels + Corkscrew Multi-Roll!)

Includes:
  - Top 1-click Copyable URL Bar for file:///G:/Quake/Combat/BakersfieldQuake/wild_vehicles_explosion.html
  - Pre-baked 960 Hz Catastrophic Airborne-Launch, Mid-Air Secondary Fuel Rupture & Multi-Turn
    Ground Barrel-Roll Simulation (451 frames @ 60 FPS = 7.50s)
  - Live In-Browser 480 Hz 3D Rigid-Body + 6-Wheel Gyroscopic Physics Re-Simulator for Intensity
    Presets (1.0x Intense Realistic, 1.45x Extreme Stunt, 2.0x Insane Mega-Blast) & Random Re-Rolls!
  - Full Volumetric Fireball, Mid-Air Fuel Burst, Streaming Wreck Flames/Smoke, Scraping Contact
    Sparks, Shockwave Ring, Scorch Crater Decals, Dynamic Shadows & Procedural WebAudio!
"""
import base64
import io
import json
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_physics_sim as vps
import wild_vehicles_specs_tex as wvs
import wild_vehicles_physics_build as wvpb

PARTS_JSON = os.path.join(HERE, "out", "wild_vehicles_parts.json")
SIM_CACHE_NPZ = os.path.join(HERE, "out", "wild_vehicles_sim_cache.npz")
TEX_DIR = os.path.join(HERE, "out", "vehicles")
OUT_HTML = os.path.join(MOD_DIR, "wild_vehicles_explosion.html")
WILD_KINDS = wvs.WILD_KINDS
SCALE = 1.0 / 39.37  # Quake units -> meters


def b64_f32(arr):
    return base64.b64encode(np.asarray(arr, dtype=np.float32).tobytes()).decode("ascii")


def b64_u16(arr):
    return base64.b64encode(np.asarray(arr, dtype=np.uint16).tobytes()).decode("ascii")


def img_to_jpeg_uri(path, size=768, quality=90):
    im = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def convert_trs_to_viewer(pos_q, rot_q, scl_q):
    pg = np.column_stack([pos_q[:, 1], pos_q[:, 2], pos_q[:, 0]]).astype(np.float32) * SCALE
    rg = np.column_stack([rot_q[:, 1], rot_q[:, 2], rot_q[:, 0], rot_q[:, 3]]).astype(np.float32)
    rg /= np.maximum(np.linalg.norm(rg, axis=1, keepdims=True), 1e-8)
    sg = np.column_stack([scl_q[:, 1], scl_q[:, 2], scl_q[:, 0]]).astype(np.float32)
    return np.hstack([pg, rg, sg]).astype(np.float32)


def main():
    with open(PARTS_JSON, "r", encoding="utf-8") as f:
        all_veh = json.load(f)
    sim = np.load(SIM_CACHE_NPZ, allow_pickle=True)
    blast_mesh = vps.build_blast_starburst_mesh()

    labels = {
        "hdtruck": "Heavy-Duty Diesel Dually Truck",
        "schoolbus": "Type-C Yellow School Bus",
        "gtcar": "V8 Street Muscle Car",
    }
    subtitles = {
        "hdtruck": "6.7L Turbo-Diesel Crew-Cab Rig • 6 Flying Wheels • Twin Chrome Stacks",
        "schoolbus": "35-ft Bakersfield Unified Bus #42 • 6 Flying Wheels • STOP Sign & 8-Way Flashers",
        "gtcar": "Supercharged V8 Fastback • 4 Wide Twin-Spoke Alloys • Corkscrew Multi-Roll",
    }
    max_hps = {"hdtruck": 380, "schoolbus": 520, "gtcar": 250}
    hood_fire_viewer = {
        "hdtruck": [0.0, 47.0 * SCALE, 82.0 * SCALE],
        "schoolbus": [0.0, 48.0 * SCALE, 126.0 * SCALE],
        "gtcar": [0.0, 32.0 * SCALE, 64.0 * SCALE],
    }

    vehicles_payload = {}
    for kind in WILD_KINDS:
        vdata = all_veh[kind]
        parts = vdata["parts"]
        sp = vdata["spec"]
        fps_ex = int(sim[f"{kind}_fps"][0])
        nf_ex = int(sim[f"{kind}_n_frames"][0])
        boom_frame = int(sim[f"{kind}_boom_frame"][0])
        sec_boom_frame = int(sim[f"{kind}_sec_boom_frame"][0])
        sparks_raw = json.loads(str(sim[f"{kind}_sparks"][0]))

        wheel_names = sorted([nm for nm in parts if nm.startswith("wheel_")])
        shrap_names = sorted([nm for nm in parts if nm.startswith("shrap_")], key=lambda s: int(s.split("_")[1]))
        ordered_names = (
            ["chassis", "wreck_chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"]
            + wheel_names
            + shrap_names
            + ["blast_flash"]
        )

        # Idle (61 frames @ 30 FPS = 2.0s) & CatchFire (91 frames @ 30 FPS = 3.0s)
        nf_idle = 61
        idle_q = {nm: (np.zeros((nf_idle, 3)), np.zeros((nf_idle, 4)), np.ones((nf_idle, 3))) for nm in ordered_names}
        for fi in range(nf_idle):
            pose = wvpb.compute_wild_part_trs(vdata, kind, (fi / 60.0) % 1.0, mode="idle")
            for nm, (p, q, sc) in pose.items():
                idle_q[nm][0][fi], idle_q[nm][1][fi], idle_q[nm][2][fi] = p, q, sc

        nf_fire = 91
        fire_q = {nm: (np.zeros((nf_fire, 3)), np.zeros((nf_fire, 4)), np.ones((nf_fire, 3))) for nm in ordered_names}
        for fi in range(nf_fire):
            t = fi / 30.0
            if t < 0.85:
                pose = wvpb.compute_wild_part_trs(vdata, kind, (t % 0.28) / 0.28, mode="flinch")
            else:
                pose = wvpb.compute_wild_part_trs(vdata, kind, ((t - 0.85) * 1.45) % 1.0, mode="fire")
            for nm, (p, q, sc) in pose.items():
                fire_q[nm][0][fi], fire_q[nm][1][fi], fire_q[nm][2][fi] = p, q, sc

        pose_boom = wvpb.compute_wild_part_trs(vdata, kind, (boom_frame * 0.11) % 1.0, mode="fire")

        js_parts = []
        for nm in ordered_names:
            p = blast_mesh if nm == "blast_flash" else parts[nm]
            va = np.array(p["verts"], dtype=np.float32)
            na = np.array(p["norms"], dtype=np.float32)
            uv = np.array(p["uvs"], dtype=np.float32)
            tris = np.array(p["tris"], dtype=np.uint16).reshape(-1)

            pos_g = np.column_stack([va[:, 1], va[:, 2], va[:, 0]]) * SCALE
            nrm_g = np.column_stack([na[:, 1], na[:, 2], na[:, 0]])
            nrm_g /= np.maximum(np.linalg.norm(nrm_g, axis=1, keepdims=True), 1e-8)
            vb = np.hstack([pos_g, nrm_g, uv]).astype(np.float32)

            trs_idle = convert_trs_to_viewer(*idle_q[nm])
            trs_fire = convert_trs_to_viewer(*fire_q[nm])
            trs_ex = convert_trs_to_viewer(
                sim[f"{kind}_pos_{nm}"], sim[f"{kind}_rot_{nm}"], sim[f"{kind}_scl_{nm}"]
            )

            # Compact collision hull in Quake units for in-browser 480 Hz physics re-simulation!
            hull_q = []
            if nm != "blast_flash" and not nm.startswith("wheel_") and nm != "chassis":
                if nm == "wreck_chassis" and "roll_hull" in p:
                    hv = np.array(p["roll_hull"], dtype=np.float32)
                elif len(va) > 40:
                    step_i = max(1, len(va) // 36)
                    hv = np.vstack([va[::step_i], va[np.argsort(va[:, 2])[:10]]])
                else:
                    hv = va
                hull_q = np.round(hv, 2).tolist()

            p_org_q = [0.0, 0.0, 32.0] if nm == "blast_flash" else [round(float(x), 3) for x in p["origin"]]
            b_pos_q = [round(float(x), 3) for x in pose_boom[nm][0]]
            b_rot_q = [round(float(x), 4) for x in pose_boom[nm][1]]

            burn_only = nm in ("wreck_chassis", "hood") or nm.startswith("shrap_")
            js_parts.append({
                "name": nm,
                "burnOnly": bool(burn_only),
                "isFlash": nm == "blast_flash",
                "stepScale": bool(nm in ("chassis", "wreck_chassis") or nm.startswith("shrap_")),
                "nv": int(len(pos_g)),
                "ni": int(len(tris)),
                "vb": b64_f32(vb),
                "ib": b64_u16(tris),
                "idle": b64_f32(trs_idle),
                "fire": b64_f32(trs_fire),
                "explode": b64_f32(trs_ex),
                "orgQ": p_org_q,
                "boomPosQ": b_pos_q,
                "boomRotQ": b_rot_q,
                "hullQ": hull_q,
            })

        js_sparks = [
            {
                "t": spk["t"],
                "p": [round(spk["pos"][1] * SCALE, 3), round(spk["pos"][2] * SCALE, 3), round(spk["pos"][0] * SCALE, 3)],
                "i": round(float(spk["intensity"]), 2),
                "k": spk["kind"],
            }
            for spk in sparks_raw
        ]

        # Compute baseline telemetry for UI display
        w_pos_q = sim[f"{kind}_pos_wreck_chassis"]
        w_rot_q = sim[f"{kind}_rot_wreck_chassis"]
        max_z_m = round(float(np.max(w_pos_q[:, 2])) * SCALE, 1)
        roll_dist_m = round(float(np.hypot(w_pos_q[-1, 0], w_pos_q[-1, 1])) * SCALE, 1)
        cum_ang = 0.0
        for fi in range(boom_frame + 1, len(w_rot_q)):
            d = min(1.0, abs(float(np.dot(w_rot_q[fi - 1], w_rot_q[fi]))))
            cum_ang += 2.0 * np.arccos(d)
        revs = round(float(cum_ang / (2.0 * np.pi)), 1)
        max_wd_m = round(
            max(float(np.hypot(sim[f"{kind}_pos_{wn}"][-1, 0], sim[f"{kind}_pos_{wn}"][-1, 1])) for wn in wheel_names) * SCALE,
            1,
        )

        vehicles_payload[kind] = {
            "label": labels[kind],
            "subtitle": subtitles[kind],
            "maxHp": max_hps[kind],
            "nWheels": len(wheel_names),
            "wheelR": float(sp["wheel_r"]),
            "wheelW": float(sp["wheel_w"]),
            "halfLenM": round(float(max(abs(sp["x0"]), abs(sp["x1"]))) * SCALE, 2),
            "halfWidM": round(float(sp["hw"]) * SCALE, 2),
            "hoodOfs": hood_fire_viewer[kind],
            "stats": {
                "peakAltM": max_z_m,
                "barrelRevs": revs,
                "rollDistM": roll_dist_m,
                "wheelDistM": max_wd_m,
            },
            "texIntact": img_to_jpeg_uri(os.path.join(TEX_DIR, f"veh_{kind}_atlas.png"), size=1024, quality=92),
            "texBurn": img_to_jpeg_uri(os.path.join(TEX_DIR, f"veh_{kind}_burn_atlas.png"), size=1024, quality=90),
            "texGlow": img_to_jpeg_uri(os.path.join(MOD_DIR, "progs", f"veh_{kind}_tex_glow.png"), size=512, quality=88),
            "texBurnGlow": img_to_jpeg_uri(os.path.join(MOD_DIR, "progs", f"veh_{kind}_burn_glow.png"), size=512, quality=88),
            "fpsEx": fps_ex,
            "nFramesEx": nf_ex,
            "boomFrame": boom_frame,
            "secBoomFrame": sec_boom_frame,
            "nFramesIdle": nf_idle,
            "nFramesFire": nf_fire,
            "parts": js_parts,
            "sparks": js_sparks,
        }

    payload_json = json.dumps(
        {"scale": SCALE, "kinds": list(WILD_KINDS), "vehicles": vehicles_payload},
        separators=(",", ":"),
    )
    html = HTML_TEMPLATE.replace("__WILD_VEHICLES_JSON__", payload_json)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote standalone WebGL2 Wild Explosion Studio: {OUT_HTML} ({os.path.getsize(OUT_HTML) / 1e6:.2f} MB)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BakersfieldQuake — Wild Vehicle Explosions Studio (Truck • School Bus • Muscle Car)</title>
<style>
  :root {
    --bg: #080b11;
    --panel: rgba(13, 18, 28, 0.88);
    --panel-strong: rgba(10, 14, 22, 0.95);
    --border: rgba(255, 255, 255, 0.13);
    --accent: #ff6b1a;
    --accent2: #38bdf8;
    --gold: #facc15;
    --danger: #ef4444;
    --ok: #22c55e;
    --txt: #f1f5f9;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  html, body {
    width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--txt);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  canvas { width: 100%; height: 100%; display: block; cursor: grab; }
  canvas:active { cursor: grabbing; }

  /* Top 1-Click Copyable URL Bar */
  .url-bar {
    position: fixed; top: 8px; left: 12px; right: 12px; z-index: 20;
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    background: var(--panel-strong); border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 9px; padding: 5px 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.5);
  }
  .url-box {
    flex: 1; display: flex; align-items: center; gap: 8px; cursor: pointer;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 6px; padding: 4px 10px; overflow: hidden; transition: 0.15s;
  }
  .url-box:hover { background: rgba(56, 189, 248, 0.12); border-color: #7dd3fc; }
  .url-code {
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px;
    color: #bae6fd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; user-select: all;
  }
  .copy-pill {
    font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 5px;
    background: var(--accent2); color: #06131f; white-space: nowrap;
  }
  .copy-pill.copied { background: var(--ok); color: #041a0d; }

  .hud-top {
    position: fixed; top: 48px; left: 12px; right: 12px; z-index: 15;
    display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: stretch;
    pointer-events: none;
  }
  .card {
    background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px 12px; pointer-events: auto;
    display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    box-shadow: 0 8px 26px rgba(0,0,0,0.48);
  }
  .title { font-weight: 800; font-size: 13.5px; letter-spacing: 0.25px; color: #fff; }
  .sub { font-size: 11px; color: var(--muted); }

  button {
    background: rgba(255,255,255,0.07); color: var(--txt); border: 1px solid rgba(255,255,255,0.15);
    border-radius: 7px; padding: 5px 10px; font-size: 12px; font-weight: 600;
    cursor: pointer; transition: 0.14s; display: inline-flex; align-items: center; gap: 5px;
  }
  button:hover { background: rgba(255,255,255,0.16); border-color: rgba(255,255,255,0.34); }
  button.active { background: var(--accent); color: #120700; border-color: #fdba74; font-weight: 700; }
  button.veh-btn.active { background: var(--accent2); color: #051320; border-color: #bae6fd; font-weight: 700; }
  button.int-btn.active { background: var(--gold); color: #1a1200; border-color: #fef08a; font-weight: 700; }

  button.boom-btn {
    background: linear-gradient(135deg, #dc2626, #ea580c); color: #fff;
    border: 1px solid #fca5a5; padding: 6px 13px; font-size: 12.5px; font-weight: 800;
    box-shadow: 0 0 16px rgba(239, 68, 68, 0.45);
  }
  button.boom-btn:hover { filter: brightness(1.14); transform: translateY(-1px); }

  button.shoot-btn {
    background: linear-gradient(135deg, #f59e0b, #d97706); color: #140b00;
    border: 1px solid #fde68a; padding: 6px 11px; font-weight: 800;
  }
  button.shoot-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }

  .hp-wrap { display: flex; align-items: center; gap: 7px; min-width: 175px; }
  .hp-bar-bg {
    flex: 1; height: 10px; background: rgba(0,0,0,0.6); border-radius: 99px;
    overflow: hidden; border: 1px solid rgba(255,255,255,0.18);
  }
  .hp-bar-fill { height: 100%; width: 100%; background: var(--ok); transition: width 0.1s, background 0.18s; }
  .hp-label { font-size: 11.5px; font-variant-numeric: tabular-nums; font-weight: 700; min-width: 76px; }

  .badge {
    font-size: 10.5px; padding: 3px 8px; border-radius: 99px; font-weight: 800; letter-spacing: 0.3px;
    background: rgba(34,197,94,0.18); color: #86efac; border: 1px solid rgba(34,197,94,0.42);
  }
  .badge.fire { background: rgba(249,115,22,0.25); color: #fdba74; border-color: rgba(249,115,22,0.55); }
  .badge.wreck { background: rgba(239,68,68,0.28); color: #fca5a5; border-color: rgba(239,68,68,0.6); }

  /* Telemetry Pill Strip */
  .telemetry {
    position: fixed; left: 12px; bottom: 104px; z-index: 14; pointer-events: none;
    display: flex; gap: 8px; flex-wrap: wrap;
  }
  .stat-pill {
    background: rgba(10, 15, 24, 0.82); backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; padding: 5px 10px;
    font-size: 11px; color: #cbd5e1;
  }
  .stat-pill b { color: #38bdf8; font-variant-numeric: tabular-nums; }

  .hud-bottom {
    position: fixed; bottom: 10px; left: 12px; right: 12px; z-index: 15;
    display: flex; flex-direction: column; gap: 7px; pointer-events: none;
  }
  .scrubber-row { width: 100%; display: flex; align-items: center; gap: 10px; }
  input[type=range] { flex: 1; accent-color: var(--accent); cursor: pointer; height: 6px; }

  .modal-backdrop {
    position: fixed; inset: 0; z-index: 50; background: rgba(4, 7, 13, 0.82);
    backdrop-filter: blur(10px); display: none; align-items: center; justify-content: center; padding: 20px;
  }
  .modal-backdrop.open { display: flex; }
  .modal-box {
    background: #0d1320; border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px;
    max-width: 1060px; width: 100%; max-height: 88vh; overflow-y: auto; padding: 20px 24px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.75); user-select: text;
  }
  .modal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 14px; margin-top: 14px; }
  .veh-spec-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.11);
    border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px;
  }
  .veh-spec-card img { width: 100%; border-radius: 7px; border: 1px solid rgba(255,255,255,0.15); }
  .code-chip {
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 11.5px;
    background: rgba(56,189,248,0.12); color: #bae6fd; padding: 2px 6px; border-radius: 4px;
  }
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>

<!-- Single-Click Copyable Full URL Bar -->
<div class="url-bar">
  <span class="sub" id="urlBarLabel" style="font-weight:700; color:#7dd3fc;">STUDIO URL:</span>
  <div class="url-box" id="urlCopyBox" title="Single-click to copy full URL path">
    <span class="url-code" id="urlCodeText">file:///G:/Quake/Combat/BakersfieldQuake/wild_vehicles_explosion.html</span>
    <span class="copy-pill" id="copyPill">Click to Copy URL</span>
  </div>
  <button id="btnShowcaseInfo" style="border-color:rgba(56,189,248,0.45); color:#bae6fd;">&#9432; What We Made &amp; Atlases</button>
  <span class="sub">Drag: Orbit &bull; Right-Drag: Pan &bull; Wheel: Zoom &bull; <b>R</b>: Detonate &bull; <b>Space</b>: Shoot</span>
</div>

<!-- Showcase Summary & Fixed 1024x1024 Texture Atlas Inspector Modal -->
<div class="modal-backdrop" id="showcaseModal">
  <div class="modal-box">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; border-bottom:1px solid rgba(255,255,255,0.12); padding-bottom:12px;">
      <div>
        <div style="font-size:18px; font-weight:800; color:#fff;">BakersfieldQuake — 3 Wild-Exploding Realistic Vehicles Showcase</div>
        <div class="sub" style="margin-top:3px;">960 Hz Multi-Body Airborne-Flip &amp; Multi-Turn Ground Barrel-Roll Physics &bull; 4..6 Flying Gyroscopic Wheels &bull; Clean 1024&times;1024 Studio &amp; Burn UV Atlases &bull; DarkPlaces MD3 + Standalone glTF 2.0</div>
      </div>
      <button id="btnCloseModal" style="padding:6px 14px; font-weight:700;">&#10005; Close</button>
    </div>
    <div class="modal-grid" id="modalAtlasGrid"></div>
  </div>
</div>

<!-- Top Vehicle & Explosion Controls -->
<div class="hud-top">
  <div class="card">
    <div style="margin-right:4px;">
      <div class="title">Wild Explosions 3D Studio</div>
      <div class="sub" id="vehSubtitle">All 3 Vehicles • Domino Chain-Reaction Stunt Lot</div>
    </div>
    <button class="veh-btn active" data-veh="all">All 3 Stunt Lineup</button>
    <button class="veh-btn" data-veh="hdtruck">1. Heavy-Duty Truck (6W)</button>
    <button class="veh-btn" data-veh="schoolbus">2. Yellow School Bus (6W)</button>
    <button class="veh-btn" data-veh="gtcar">3. V8 Muscle Car (4W)</button>
  </div>

  <div class="card">
    <button class="boom-btn" id="btnDetonate">&#128165; DETONATE NOW! (R)</button>
    <button class="shoot-btn" id="btnShoot">&#128299; Shoot (Space)</button>
    <button id="btnReset">&#8634; Reset</button>
    <div class="hp-wrap">
      <div class="hp-bar-bg"><div class="hp-bar-fill" id="hpFill"></div></div>
      <div class="hp-label" id="hpText">380 / 380 HP</div>
    </div>
    <span class="badge" id="stateBadge">IDLE RUNNING</span>
  </div>
</div>

<!-- Live Physics Telemetry -->
<div class="telemetry" id="telemetryBar"></div>

<!-- Bottom Animation, Intensity, Camera & Scrubber Controls -->
<div class="hud-bottom">
  <div class="card" style="justify-content: space-between;">
    <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap;">
      <span class="sub">Mode:</span>
      <button class="clip-btn active" data-clip="interactive">Interactive</button>
      <button class="clip-btn" data-clip="explode">Explode Loop (7.5s)</button>
      <button class="clip-btn" data-clip="fire">Catch Fire</button>
      <button class="clip-btn" data-clip="idle">Idle</button>
      <span class="sub" style="margin-left:6px;">Wildness:</span>
      <button class="int-btn active" data-int="1.0">1.0x Realistic Wild</button>
      <button class="int-btn" data-int="1.45">1.45x Extreme Stunt</button>
      <button class="int-btn" data-int="2.0">2.0x Insane Launch</button>
      <button id="btnReroll" title="Run fresh 480 Hz 3D rigid-body & 6-tire gyroscopic physics simulation">&#127922; Re-Roll Physics</button>
    </div>

    <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap;">
      <span class="sub">Camera:</span>
      <button class="cam-btn active" data-cam="orbit">Free Orbit</button>
      <button class="cam-btn" data-cam="wreck">Follow Rolling Car</button>
      <button class="cam-btn" data-cam="stunt">Low Stunt Cam</button>
      <button class="cam-btn" data-cam="wheel">Track Flying Wheel</button>
      <button class="cam-btn" data-cam="hood">Track Blown Hood</button>
      <span class="sub" style="margin-left:6px;">Speed:</span>
      <button class="spd-btn" data-spd="0.1">0.1x</button>
      <button class="spd-btn" data-spd="0.25">0.25x</button>
      <button class="spd-btn" data-spd="0.5">0.5x</button>
      <button class="spd-btn active" data-spd="1.0">1.0x</button>
    </div>
  </div>

  <div class="card scrubber-row">
    <button id="btnPlayPause" style="min-width:64px; justify-content:center;">Pause</button>
    <input type="range" id="scrubber" min="0" max="1000" value="0">
    <span class="hp-label" id="timeLabel" style="min-width:125px; text-align:right;">LIVE INTERACTIVE</span>
  </div>
</div>

<script>
const DATA = __WILD_VEHICLES_JSON__;
const SCALE = DATA.scale;
const LOCAL_FILE_URL = "file:///G:/Quake/Combat/BakersfieldQuake/wild_vehicles_explosion.html";
const ACTIVE_URL = (typeof location !== "undefined" && /^https?:/i.test(location.protocol)) ? location.href : LOCAL_FILE_URL;

// --- 1-Click Copy URL Bar & Showcase Modal ---
const urlCopyBox = document.getElementById('urlCopyBox');
const urlCodeText = document.getElementById('urlCodeText');
const urlBarLabel = document.getElementById('urlBarLabel');
const copyPill = document.getElementById('copyPill');
if (urlCodeText) urlCodeText.textContent = ACTIVE_URL;
if (urlBarLabel && /^https?:/i.test(ACTIVE_URL)) urlBarLabel.textContent = "LIVE VPS URL:";

urlCopyBox.addEventListener('click', async () => {
  const txt = ACTIVE_URL;
  try {
    await navigator.clipboard.writeText(txt);
  } catch (_) {
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(urlCodeText);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('copy');
  }
  copyPill.textContent = '✓ Copied!';
  copyPill.classList.add('copied');
  setTimeout(() => {
    copyPill.textContent = 'Click to Copy URL';
    copyPill.classList.remove('copied');
  }, 1800);
});

const showcaseModal = document.getElementById('showcaseModal');
const btnShowcaseInfo = document.getElementById('btnShowcaseInfo');
const btnCloseModal = document.getElementById('btnCloseModal');
if (btnShowcaseInfo && showcaseModal) {
  const metaMap = {
    hdtruck: { ent: "misc_vehicle_hdtruck", imp: "impulse 91", glb: "veh_hdtruck.glb" },
    schoolbus: { ent: "misc_vehicle_schoolbus", imp: "impulse 92", glb: "veh_schoolbus.glb" },
    gtcar: { ent: "misc_vehicle_gtcar", imp: "impulse 93", glb: "veh_gtcar.glb" }
  };
  const gridEl = document.getElementById('modalAtlasGrid');
  if (gridEl) {
    gridEl.innerHTML = DATA.kinds.map(k => {
      const v = DATA.vehicles[k], m = metaMap[k];
      return `<div class="veh-spec-card">
        <div style="font-weight:800; font-size:14px; color:#fff;">${v.label}</div>
        <div class="sub">${v.subtitle}</div>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <span class="code-chip">${m.ent}</span>
          <span class="code-chip">${m.imp}</span>
          <span class="code-chip">${v.maxHp} HP &bull; ${v.nWheels} Flying Wheels</span>
        </div>
        <div class="sub" style="color:#cbd5e1;">Peak Launch: <b>${v.stats.peakAltM}m</b> &bull; Barrel Rolls: <b>${v.stats.barrelRevs} rev</b> &bull; Roll Dist: <b>${v.stats.rollDistM}m</b> &bull; Max Tire Flight: <b>${v.stats.wheelDistM}m</b></div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
          <div><div class="sub" style="margin-bottom:3px;">Intact 1024&times;1024 Atlas</div><img src="${v.texIntact}" alt="${k} intact atlas"></div>
          <div><div class="sub" style="margin-bottom:3px;">Scorched Burn / Wreck Atlas</div><img src="${v.texBurn}" alt="${k} burn atlas"></div>
        </div>
      </div>`;
    }).join('');
  }
  btnShowcaseInfo.addEventListener('click', () => showcaseModal.classList.add('open'));
  btnCloseModal.addEventListener('click', () => showcaseModal.classList.remove('open'));
  showcaseModal.addEventListener('click', (e) => { if (e.target === showcaseModal) showcaseModal.classList.remove('open'); });
}

function b64ToF32(s) {
  const bin = atob(s), len = bin.length, u8 = new Uint8Array(len);
  for (let i = 0; i < len; i++) u8[i] = bin.charCodeAt(i);
  return new Float32Array(u8.buffer);
}
function b64ToU16(s) {
  const bin = atob(s), len = bin.length, u8 = new Uint8Array(len);
  for (let i = 0; i < len; i++) u8[i] = bin.charCodeAt(i);
  return new Uint16Array(u8.buffer);
}

// --- Procedural WebAudio Sound Engine (Booms, Mid-Air Rupture, Roof Crunches, Tire Thuds, Clangs) ---
let audioCtx = null;
function ensureAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
}

function playBulletClang() {
  ensureAudio();
  const sr = audioCtx.sampleRate, dur = 0.22;
  const buf = audioCtx.createBuffer(1, Math.floor(sr * dur), sr);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) {
    const t = i / sr;
    d[i] = Math.exp(-t / 0.022) * (Math.random() * 2 - 1) * 0.65
         + Math.exp(-t / 0.075) * (0.45 * Math.sin(2 * Math.PI * 260 * t) + 0.32 * Math.sin(2 * Math.PI * 710 * t));
  }
  const src = audioCtx.createBufferSource(); src.buffer = buf;
  const g = audioCtx.createGain(); g.gain.value = 0.38;
  src.connect(g).connect(audioCtx.destination); src.start();
}

function playMassiveBoom(scale = 1.0) {
  ensureAudio();
  const sr = audioCtx.sampleRate, dur = 1.85;
  const buf = audioCtx.createBuffer(1, Math.floor(sr * dur), sr);
  const d = buf.getChannelData(0);
  let lp = 0, lp2 = 0, ph = 0;
  for (let i = 0; i < d.length; i++) {
    const t = i / sr;
    const nz = Math.random() * 2 - 1;
    lp += 0.045 * (nz - lp);
    lp2 += 0.18 * (nz - lp2);
    ph += 2 * Math.PI * (30 + 95 * Math.exp(-t / 0.11)) / sr;
    const sub = 1.55 * Math.sin(ph) * Math.exp(-t / 0.34);
    const roar = lp * 5.2 * Math.exp(-t / 0.62);
    const crack = lp2 * 1.4 * Math.exp(-t / 0.09);
    d[i] = Math.tanh((sub + roar + crack) * 0.85 * Math.min(1.35, scale));
  }
  const src = audioCtx.createBufferSource(); src.buffer = buf;
  const g = audioCtx.createGain(); g.gain.value = 0.68;
  src.connect(g).connect(audioCtx.destination); src.start();
}

function playRollCrunch(intensity = 0.8) {
  ensureAudio();
  const sr = audioCtx.sampleRate, dur = 0.32;
  const buf = audioCtx.createBuffer(1, Math.floor(sr * dur), sr);
  const d = buf.getChannelData(0);
  let lp = 0;
  const f1 = 145 + Math.random() * 75, f2 = 390 + Math.random() * 190;
  for (let i = 0; i < d.length; i++) {
    const t = i / sr;
    const nz = Math.random() * 2 - 1;
    lp += 0.22 * (nz - lp);
    d[i] = Math.tanh((
      lp * 1.9 * Math.exp(-t / 0.13) +
      0.55 * Math.sin(2 * Math.PI * f1 * t) * Math.exp(-t / 0.11) +
      0.32 * Math.sin(2 * Math.PI * f2 * t) * Math.exp(-t / 0.06)
    ) * intensity);
  }
  const src = audioCtx.createBufferSource(); src.buffer = buf;
  const g = audioCtx.createGain(); g.gain.value = 0.34 * Math.min(1.0, intensity);
  src.connect(g).connect(audioCtx.destination); src.start();
}

function playTireBounce(intensity = 0.7) {
  ensureAudio();
  const sr = audioCtx.sampleRate, dur = 0.16;
  const buf = audioCtx.createBuffer(1, Math.floor(sr * dur), sr);
  const d = buf.getChannelData(0);
  let ph = 0;
  for (let i = 0; i < d.length; i++) {
    const t = i / sr;
    ph += 2 * Math.PI * (72 + 115 * Math.exp(-t / 0.04)) / sr;
    d[i] = Math.sin(ph) * Math.exp(-t / 0.065) * 0.75 + (Math.random() * 2 - 1) * Math.exp(-t / 0.02) * 0.2;
  }
  const src = audioCtx.createBufferSource(); src.buffer = buf;
  const g = audioCtx.createGain(); g.gain.value = 0.24 * Math.min(1.0, intensity);
  src.connect(g).connect(audioCtx.destination); src.start();
}

// --- WebGL2 Shaders (Sky Dome, Expansive Stunt Lot w/ Scorch Marks & Shockwaves, Lit Vehicles, Soft Shadows, Particles) ---
const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl2', { antialias: true, alpha: false });

const VS_SKY = `#version 300 es
out vec2 vUV;
void main() {
  vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
  vUV = p;
  gl_Position = vec4(p * 2.0 - 1.0, 0.9999, 1.0);
}`;
const FS_SKY = `#version 300 es
precision highp float;
in vec2 vUV;
out vec4 fragColor;
void main() {
  float y = clamp(vUV.y, 0.0, 1.0);
  vec3 horizon = vec3(0.14, 0.17, 0.24);
  vec3 zenith  = vec3(0.035, 0.05, 0.095);
  vec3 col = mix(horizon, zenith, pow(y, 0.62));
  // Subtle warm sunset glow near horizon
  col += vec3(0.16, 0.065, 0.02) * exp(-y * 5.5) * (1.0 - abs(vUV.x - 0.5) * 0.9);
  fragColor = vec4(col, 1.0);
}`;

const VS_GRID = `#version 300 es
layout(location=0) in vec3 aPos;
uniform mat4 uVP;
out vec3 vPos;
void main() { vPos = aPos; gl_Position = uVP * vec4(aPos, 1.0); }`;

const FS_GRID = `#version 300 es
precision highp float;
in vec3 vPos;
uniform vec4 uScorch[3];   // xyz = world center, w = strength (0..1)
uniform vec4 uShock[3];    // xyz = world center, w = radius (>0 active)
uniform vec3 uFirePos;
uniform float uFireInt;
out vec4 fragColor;
void main() {
  vec2 g1 = abs(fract(vPos.xz * 0.5 - 0.5) - 0.5) / fwidth(vPos.xz * 0.5);
  float minorGrid = 1.0 - min(min(g1.x, g1.y), 1.0);
  vec2 g10 = abs(fract(vPos.xz * 0.1 - 0.5) - 0.5) / fwidth(vPos.xz * 0.1);
  float majorGrid = 1.0 - min(min(g10.x, g10.y), 1.0);

  // Stunt lot parking bay stripes at x = -11.25, -3.75, +3.75, +11.25
  float bayX = abs(fract((vPos.x + 3.75) / 7.5) - 0.5) * 7.5;
  float stripe = (bayX < 0.09 && abs(vPos.z) < 4.6) ? 1.0 : 0.0;

  // Concentric blast range rings at 15m, 35m, 65m
  float rOrigin = length(vPos.xz);
  float ring = smoothstep(0.14, 0.0, abs(rOrigin - 15.0))
             + smoothstep(0.16, 0.0, abs(rOrigin - 35.0)) * 0.7
             + smoothstep(0.20, 0.0, abs(rOrigin - 65.0)) * 0.5;

  float distFade = exp(-0.00042 * dot(vPos.xz, vPos.xz));
  vec3 asphalt = vec3(0.088, 0.10, 0.125);
  vec3 col = mix(asphalt, vec3(0.16, 0.19, 0.25), minorGrid * 0.35 * distFade);
  col = mix(col, vec3(0.24, 0.30, 0.39), majorGrid * 0.45 * distFade);
  col = mix(col, vec3(0.92, 0.72, 0.15), stripe * 0.72 * distFade);
  col += vec3(0.12, 0.22, 0.32) * ring * 0.35 * distFade;

  // Blast scorch craters & supersonic shockwave rings
  for (int i = 0; i < 3; i++) {
    if (uScorch[i].w > 0.01) {
      float d = length(vPos.xz - uScorch[i].xz);
      float soot = exp(-d * d * 0.085) * uScorch[i].w;
      float ember = exp(-d * d * 0.42) * uScorch[i].w;
      col = mix(col, vec3(0.018, 0.016, 0.016), clamp(soot * 0.92, 0.0, 0.92));
      col += vec3(0.95, 0.32, 0.04) * ember * 0.35;
    }
    if (uShock[i].w > 0.05) {
      float d = length(vPos.xz - uShock[i].xz);
      float sr = uShock[i].w;
      float band = exp(-pow((d - sr) * 1.45, 2.0)) * clamp(1.0 - sr / 36.0, 0.0, 1.0);
      col += vec3(1.0, 0.76, 0.38) * band * 0.85;
    }
  }

  if (uFireInt > 0.01) {
    vec3 df = uFirePos - vPos;
    float att = uFireInt / (dot(df, df) + 1.8);
    col += vec3(1.0, 0.46, 0.10) * att * 0.95;
  }
  fragColor = vec4(col, 1.0);
}`;

const VS_MESH = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;
uniform mat4 uVP;
uniform vec3 uWorldOffset;
uniform vec3 uTrsPos;
uniform vec4 uTrsRot;
uniform vec3 uTrsScl;
out vec3 vNrm;
out vec3 vWorldPos;
out vec2 vUV;
vec3 qrot(vec4 q, vec3 v) {
  return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
}
void main() {
  vec3 p = qrot(uTrsRot, aPos * uTrsScl) + uTrsPos + uWorldOffset;
  vWorldPos = p;
  vNrm = normalize(qrot(uTrsRot, aNrm));
  vUV = aUV;
  gl_Position = uVP * vec4(p, 1.0);
}`;

const FS_MESH = `#version 300 es
precision highp float;
in vec3 vNrm;
in vec3 vWorldPos;
in vec2 vUV;
uniform sampler2D uTex;
uniform sampler2D uGlow;
uniform vec3 uCamPos;
uniform float uIsFlash;
uniform vec3 uFireLightPos;
uniform float uFireLightInt;
out vec4 fragColor;
void main() {
  if (uIsFlash > 0.5) {
    fragColor = vec4(1.0, 0.78, 0.30, 0.94);
    return;
  }
  vec3 base = texture(uTex, vUV).rgb;
  vec3 glow = texture(uGlow, vUV).rgb;
  vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
  vec3 L1 = normalize(vec3(0.46, 0.84, 0.40));
  vec3 L2 = normalize(vec3(-0.55, 0.35, -0.62));
  vec3 V = normalize(uCamPos - vWorldPos);
  vec3 H = normalize(L1 + V);
  float diff1 = max(dot(N, L1), 0.0);
  float diff2 = max(dot(N, L2), 0.0) * 0.25;
  float hemi = 0.33 + 0.24 * (N.y * 0.5 + 0.5);
  float spec = pow(max(dot(N, H), 0.0), 42.0) * 0.34;
  float rim  = pow(1.0 - max(dot(N, V), 0.0), 3.2) * 0.10;
  vec3 col = base * (hemi + diff1 * 0.82 + diff2) + vec3(spec) + vec3(0.55, 0.72, 0.95) * rim;
  if (uFireLightInt > 0.01) {
    vec3 dF = uFireLightPos - vWorldPos;
    float dist2 = dot(dF, dF) + 0.75;
    float att = uFireLightInt / dist2;
    col += base * vec3(1.0, 0.50, 0.14) * att * max(dot(N, normalize(dF)), 0.18) * 3.6;
  }
  col += glow * 1.45;
  fragColor = vec4(col, 1.0);
}`;

const VS_SHADOW = `#version 300 es
layout(location=0) in vec2 aQuad;
uniform mat4 uVP;
uniform vec3 uCenter;
uniform vec2 uRadii;
uniform float uYaw;
out vec2 vLocal;
void main() {
  float c = cos(uYaw), s = sin(uYaw);
  vec2 p = aQuad * uRadii;
  vec2 r = vec2(p.x * c - p.y * s, p.x * s + p.y * c);
  vLocal = aQuad;
  gl_Position = uVP * vec4(uCenter.x + r.x, 0.015, uCenter.z + r.y, 1.0);
}`;
const FS_SHADOW = `#version 300 es
precision highp float;
in vec2 vLocal;
uniform float uAlpha;
out vec4 fragColor;
void main() {
  float r2 = dot(vLocal, vLocal);
  if (r2 > 1.0) discard;
  float a = pow(1.0 - r2, 1.7) * uAlpha;
  fragColor = vec4(0.0, 0.0, 0.0, a);
}`;

const VS_PARTICLE = `#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in float aSize;
layout(location=2) in vec4 aCol;
uniform mat4 uVP;
uniform float uViewportH;
out vec4 vCol;
void main() {
  vec4 clip = uVP * vec4(aPos, 1.0);
  gl_Position = clip;
  gl_PointSize = clamp(aSize * uViewportH / max(clip.w, 0.2), 1.5, 165.0);
  vCol = aCol;
}`;
const FS_PARTICLE = `#version 300 es
precision highp float;
in vec4 vCol;
out vec4 fragColor;
void main() {
  vec2 uv = gl_PointCoord * 2.0 - 1.0;
  float r2 = dot(uv, uv);
  if (r2 > 1.0) discard;
  float soft = pow(1.0 - r2, 1.55);
  fragColor = vec4(vCol.rgb, vCol.a * soft);
}`;

function compileProg(vsSrc, fsSrc) {
  const vs = gl.createShader(gl.VERTEX_SHADER); gl.shaderSource(vs, vsSrc); gl.compileShader(vs);
  if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(vs));
  const fs = gl.createShader(gl.FRAGMENT_SHADER); gl.shaderSource(fs, fsSrc); gl.compileShader(fs);
  if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(fs));
  const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
  return p;
}

const progSky  = compileProg(VS_SKY, FS_SKY);
const progGrid = compileProg(VS_GRID, FS_GRID);
const progMesh = compileProg(VS_MESH, FS_MESH);
const progShad = compileProg(VS_SHADOW, FS_SHADOW);
const progPart = compileProg(VS_PARTICLE, FS_PARTICLE);
const emptyVao = gl.createVertexArray();

function loadTexture(uri) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([40,40,45,255]));
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

// Expansive 560m x 560m stunt lot ground quad
const gridVao = gl.createVertexArray();
gl.bindVertexArray(gridVao);
const gridVb = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, gridVb);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-280,0,-280, 280,0,-280, 280,0,280, -280,0,-280, 280,0,280, -280,0,280]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);

// Soft shadow quad
const shadVao = gl.createVertexArray();
gl.bindVertexArray(shadVao);
const shadVb = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, shadVb);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, 1,1, -1,-1, 1,1, -1,1]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

// Volumetric Particle Buffer (4500 particles!)
const MAX_PARTS = 4500;
const partData = new Float32Array(MAX_PARTS * 8);
const partVao = gl.createVertexArray();
gl.bindVertexArray(partVao);
const partVb = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, partVb);
gl.bufferData(gl.ARRAY_BUFFER, partData.byteLength, gl.DYNAMIC_DRAW);
gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 32, 12);
gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 32, 16);

// Unpack all 3 wild vehicles onto GPU
const vehGPU = {};
for (const k of DATA.kinds) {
  const v = DATA.vehicles[k];
  const parts = v.parts.map(p => {
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const vb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vb);
    gl.bufferData(gl.ARRAY_BUFFER, b64ToF32(p.vb), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);
    const ib = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, b64ToU16(p.ib), gl.STATIC_DRAW);
    const exOrig = b64ToF32(p.explode);
    return {
      ...p, vao,
      idleArr: b64ToF32(p.idle),
      fireArr: b64ToF32(p.fire),
      exBaseArr: exOrig,
      exArr: new Float32Array(exOrig),
    };
  });
  vehGPU[k] = {
    ...v,
    parts,
    partMap: Object.fromEntries(parts.map(p => [p.name, p])),
    baseSparks: v.sparks.slice(),
    sparks: v.sparks.slice(),
    liveStats: { ...v.stats },
    tIntact: loadTexture(v.texIntact),
    tBurn: loadTexture(v.texBurn),
    gIntact: loadTexture(v.texGlow),
    gBurn: loadTexture(v.texBurnGlow),
  };
}

// ============================================================================
// IN-BROWSER 480 Hz 3D MULTI-CONTACT RIGID-BODY + 6-WHEEL GYROSCOPIC SIMULATOR
// Allows live Wildness Intensity presets (1.0x / 1.45x / 2.0x) & Random Re-Rolls
// with TRUE ground collision & barrel-rolling (zero floor clipping!).
// ============================================================================
function qMul(a, b) {
  return [
    a[3]*b[0] + a[0]*b[3] + a[1]*b[2] - a[2]*b[1],
    a[3]*b[1] - a[0]*b[2] + a[1]*b[3] + a[2]*b[0],
    a[3]*b[2] + a[0]*b[1] - a[1]*b[0] + a[2]*b[3],
    a[3]*b[3] - a[0]*b[0] - a[1]*b[1] - a[2]*b[2],
  ];
}
function qNorm(q) {
  const l = Math.hypot(q[0], q[1], q[2], q[3]) || 1;
  return [q[0]/l, q[1]/l, q[2]/l, q[3]/l];
}
function qFromAxisAngle(ax, ay, az, rad) {
  const l = Math.hypot(ax, ay, az) || 1;
  const s = Math.sin(rad * 0.5) / l;
  return [ax * s, ay * s, az * s, Math.cos(rad * 0.5)];
}
function qToMat3(q) {
  const [x, y, z, w] = q;
  const xx=x*x, yy=y*y, zz=z*z, xy=x*y, xz=x*z, yz=y*z, wx=w*x, wy=w*y, wz=w*z;
  return [
    1 - 2*(yy+zz), 2*(xy-wz),     2*(xz+wy),
    2*(xy+wz),     1 - 2*(xx+zz), 2*(yz-wx),
    2*(xz-wy),     2*(yz+wx),     1 - 2*(xx+yy),
  ];
}
function mat3ToQ(m) {
  const tr = m[0] + m[4] + m[8];
  let q;
  if (tr > 0) {
    const s = Math.sqrt(tr + 1.0) * 2;
    q = [(m[7]-m[5])/s, (m[2]-m[6])/s, (m[3]-m[1])/s, 0.25*s];
  } else if (m[0] > m[4] && m[0] > m[8]) {
    const s = Math.sqrt(1.0 + m[0] - m[4] - m[8]) * 2;
    q = [0.25*s, (m[1]+m[3])/s, (m[2]+m[6])/s, (m[7]-m[5])/s];
  } else if (m[4] > m[8]) {
    const s = Math.sqrt(1.0 + m[4] - m[0] - m[8]) * 2;
    q = [(m[1]+m[3])/s, 0.25*s, (m[5]+m[7])/s, (m[2]-m[6])/s];
  } else {
    const s = Math.sqrt(1.0 + m[8] - m[0] - m[4]) * 2;
    q = [(m[2]+m[6])/s, (m[5]+m[7])/s, 0.25*s, (m[3]-m[1])/s];
  }
  return qNorm(q);
}
function cross3(a, b) {
  return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]];
}
function mat3Vec(m, v) {
  return [
    m[0]*v[0] + m[1]*v[1] + m[2]*v[2],
    m[3]*v[0] + m[4]*v[1] + m[5]*v[2],
    m[6]*v[0] + m[7]*v[1] + m[8]*v[2],
  ];
}

function resimulateVehicleJS(kind, intensity, randJitter = 0.0) {
  const v = vehGPU[kind];
  if (intensity === 1.0 && randJitter === 0.0) {
    for (const p of v.parts) p.exArr.set(p.exBaseArr);
    v.sparks = v.baseSparks.slice();
    v.liveStats = { ...v.stats };
    return;
  }

  const fps = v.fpsEx, nFrames = v.nFramesEx, boomF = v.boomFrame, secBoomF = v.secBoomFrame;
  const substeps = 8; // 480 Hz live physics!
  const dtFrame = 1.0 / fps, dt = dtFrame / substeps;
  const rnd = (lo, hi) => lo + Math.random() * (hi - lo);
  const wRad = v.wheelR, wHalfW = v.wheelW * 0.5;
  const newSparks = [];

  // Copy pre-boom frames (0..boomF-1) directly from baked track
  for (const p of v.parts) {
    p.exArr.set(p.exBaseArr.subarray(0, boomF * 10), 0);
  }

  const sideFlip = (randJitter > 0 && Math.random() < 0.5) ? -1 : 1;
  const iz = Math.pow(intensity, 0.72); // Keeps peak apex <= ~3.6s so car gets 4+ full seconds of ground barrel-rolling!
  let wCfg;
  if (kind === 'gtcar') {
    const s = sideFlip;
    wCfg = {
      vel: [(175 + rnd(-35,45)*randJitter)*intensity, s*(255 + rnd(-35,45)*randJitter)*intensity, (695 + rnd(-25,55)*randJitter)*iz],
      omega: [-s*(9.6 + rnd(-1.2,1.6)*randJitter)*intensity, (3.5 + rnd(-0.8,0.8)*randJitter)*intensity, s*2.1*intensity],
      secDv: [35*intensity, s*75*intensity, 145*iz],
      secDw: [-s*2.8*intensity, 0.9*intensity, s*0.6*intensity],
      e: 0.45, mu: 0.52, linD: 0.14, angD: 0.22
    };
  } else if (kind === 'hdtruck') {
    const s = -sideFlip;
    wCfg = {
      vel: [(155 + rnd(-30,40)*randJitter)*intensity, s*(235 + rnd(-30,40)*randJitter)*intensity, (625 + rnd(-20,50)*randJitter)*iz],
      omega: [-s*(8.6 + rnd(-1.1,1.4)*randJitter)*intensity, (3.0 + rnd(-0.7,0.7)*randJitter)*intensity, s*1.8*intensity],
      secDv: [30*intensity, s*70*intensity, 135*iz],
      secDw: [-s*2.5*intensity, 0.8*intensity, s*0.5*intensity],
      e: 0.41, mu: 0.54, linD: 0.15, angD: 0.25
    };
  } else {
    const s = sideFlip;
    wCfg = {
      vel: [(130 + rnd(-25,35)*randJitter)*intensity, s*(225 + rnd(-25,35)*randJitter)*intensity, (585 + rnd(-20,45)*randJitter)*iz],
      omega: [-s*(7.8 + rnd(-1.0,1.3)*randJitter)*intensity, (2.1 + rnd(-0.6,0.6)*randJitter)*intensity, s*1.4*intensity],
      secDv: [25*intensity, s*68*intensity, 130*iz],
      secDw: [-s*2.3*intensity, 0.6*intensity, s*0.4*intensity],
      e: 0.39, mu: 0.55, linD: 0.16, angD: 0.26
    };
  }

  const baseWheelCfgs = {
    wheel_fl:  { vel:[275,  435, 845], spin:-54, lean:20,  side:1,  maxB:5 },
    wheel_fr:  { vel:[385, -515, 560], spin:-62, lean:-25, side:-1, maxB:4 },
    wheel_rl:  { vel:[-335, 475, 710], spin:48,  lean:-22, side:-1, maxB:4 },
    wheel_rr:  { vel:[-285,-445, 775], spin:-46, lean:26,  side:1,  maxB:5 },
    wheel_rl2: { vel:[-155, 555, 625], spin:-56, lean:19,  side:1,  maxB:4 },
    wheel_rr2: { vel:[145, -575, 650], spin:52,  lean:-23, side:-1, maxB:4 },
  };

  const wheelStates = {};
  const rbStates = {};

  for (const p of v.parts) {
    const nm = p.name;
    if (nm === 'chassis' || nm === 'blast_flash') continue;
    if (nm.startsWith('wheel_')) {
      const cfg = baseWheelCfgs[nm];
      const v0 = [
        (cfg.vel[0] + rnd(-45, 45)) * intensity,
        (cfg.vel[1] + rnd(-45, 45)) * intensity,
        (cfg.vel[2] + rnd(-35, 65)) * intensity,
      ];
      wheelStates[nm] = {
        pos: [p.boomPosQ[0], p.boomPosQ[1], p.boomPosQ[2] + 3.0],
        vel: v0, mode: 'air', bounces: 0, maxB: cfg.maxB,
        yaw: Math.atan2(v0[1], v0[0]), lean: cfg.lean * Math.PI / 180,
        leanVel: cfg.side * 1.45, side: cfg.side, spin: 0,
        spinRate: cfg.spin * intensity, rollSpd: 0, precess: 0,
      };
      continue;
    }

    let cfg;
    if (nm === 'wreck_chassis') cfg = wCfg;
    else if (nm === 'hood') cfg = { vel:[rnd(95,195)*intensity, rnd(-140,140)*intensity, rnd(820,940)*intensity], omega:[rnd(-12,12), -15.5+rnd(-3,3), rnd(-8,8)], e:0.44, mu:0.42, linD:0.14, angD:0.34 };
    else if (nm === 'door_l') cfg = { vel:[rnd(-95,95)*intensity, rnd(540,650)*intensity, rnd(460,560)*intensity], omega:[-12.5, rnd(-7,7), 8.8], e:0.40, mu:0.44, linD:0.16, angD:0.38 };
    else if (nm === 'door_r') cfg = { vel:[rnd(-95,95)*intensity, -rnd(540,650)*intensity, rnd(475,575)*intensity], omega:[13.0, rnd(-7,7), -9.2], e:0.40, mu:0.44, linD:0.16, angD:0.38 };
    else if (nm === 'extra_part') cfg = { vel:[-rnd(300,410)*intensity, rnd(-160,160)*intensity, rnd(700,820)*intensity], omega:[rnd(-10,10), 12.8, rnd(-8,8)], e:0.42, mu:0.44, linD:0.15, angD:0.36 };
    else if (nm === 'bumper_f') cfg = { vel:[rnd(520,630)*intensity, rnd(-130,130)*intensity, rnd(360,450)*intensity], omega:[rnd(-9,9), 11.2, rnd(-7,7)], e:0.40, mu:0.48, linD:0.18, angD:0.42 };
    else if (nm === 'bumper_r') cfg = { vel:[-rnd(510,620)*intensity, rnd(-130,130)*intensity, rnd(340,430)*intensity], omega:[rnd(-9,9), -11.4, rnd(-7,7)], e:0.40, mu:0.48, linD:0.18, angD:0.42 };
    else if (nm === 'detail_vib') cfg = { vel:[-395*intensity, -235*intensity, 540*intensity], omega:[14.5, -11.2, 12.0], e:0.46, mu:0.38, linD:0.15, angD:0.35 };
    else {
      const idx = parseInt(nm.split('_')[1] || '0', 10);
      const ang = (2 * Math.PI * idx / 12) + rnd(-0.22, 0.22);
      const sxy = rnd(380, 790) * intensity;
      cfg = { vel:[Math.cos(ang)*sxy, Math.sin(ang)*sxy, rnd(460, 880)*intensity], omega:[rnd(-20,20), rnd(-20,20), rnd(-20,20)], e:0.46, mu:0.42, linD:0.14, angD:0.34 };
    }

    const hull = p.hullQ;
    let minX=1e9, maxX=-1e9, minY=1e9, maxY=-1e9, minZ=1e9, maxZ=-1e9;
    for (let i=0; i<hull.length; i++) {
      const h = hull[i];
      if (h[0]<minX) minX=h[0]; if (h[0]>maxX) maxX=h[0];
      if (h[1]<minY) minY=h[1]; if (h[1]>maxY) maxY=h[1];
      if (h[2]<minZ) minZ=h[2]; if (h[2]>maxZ) maxZ=h[2];
    }
    const ex = Math.max(5, maxX-minX), ey = Math.max(5, maxY-minY), ez = Math.max(5, maxZ-minZ);
    const kR = nm === 'wreck_chassis' ? 0.78 : 1.0, kL = nm === 'wreck_chassis' ? 0.82 : 1.0;
    const invI = [
      12.0 / ((ey*kR)*(ey*kR) + (ez*kR)*(ez*kR)),
      12.0 / ((ex*kL)*(ex*kL) + ez*ez),
      12.0 / ((ex*kL)*(ex*kL) + ey*ey),
    ];

    rbStates[nm] = {
      pos: nm === 'wreck_chassis' ? [p.orgQ[0], p.orgQ[1], p.orgQ[2] + 6.0] : p.boomPosQ.slice(),
      vel: cfg.vel.slice(),
      q: nm.startsWith('shrap_') ? [0,0,0,1] : p.boomRotQ.slice(),
      omega: cfg.omega.slice(),
      hull, invI, e: cfg.e, mu: cfg.mu, linD: cfg.linD, angD: cfg.angD,
      sparkCd: 0, maxZ: 6.0, cumRot: 0,
    };
  }

  function writeViewerTRS(arr, fi, pq, rq, sq) {
    const o = fi * 10;
    arr[o]   = pq[1] * SCALE; arr[o+1] = pq[2] * SCALE; arr[o+2] = pq[0] * SCALE;
    arr[o+3] = rq[1];         arr[o+4] = rq[2];         arr[o+5] = rq[0];         arr[o+6] = rq[3];
    arr[o+7] = sq[1];         arr[o+8] = sq[2];         arr[o+9] = sq[0];
  }

  const pChassis = v.partMap['chassis'];
  const pFlash = v.partMap['blast_flash'];

  for (let fi = boomF; fi < nFrames; fi++) {
    const age = (fi - boomF) * dtFrame;
    const secAge = (fi - secBoomF) * dtFrame;

    if (fi === secBoomF) {
      const wst = rbStates['wreck_chassis'];
      wst.vel[0] += wCfg.secDv[0]; wst.vel[1] += wCfg.secDv[1]; wst.vel[2] += wCfg.secDv[2];
      wst.omega[0] += wCfg.secDw[0]; wst.omega[1] += wCfg.secDw[1]; wst.omega[2] += wCfg.secDw[2];
      newSparks.push({
        t: +(fi * dtFrame).toFixed(3),
        p: [+(wst.pos[1]*SCALE).toFixed(3), +(wst.pos[2]*SCALE).toFixed(3), +(wst.pos[0]*SCALE).toFixed(3)],
        i: 1.0, k: 'airburst'
      });
    }

    // Hide intact chassis
    const cPrev = (boomF - 1) * 10;
    pChassis.exArr.set(pChassis.exBaseArr.subarray(cPrev, cPrev + 7), fi * 10);
    pChassis.exArr[fi*10+7] = 0.0001; pChassis.exArr[fi*10+8] = 0.0001; pChassis.exArr[fi*10+9] = 0.0001;

    // Primary + mid-air secondary blast starburst flash
    if (age < 0.48) {
      const s = (0.55 + 3.45 * Math.sin(Math.PI * Math.min(1, age / 0.15))) * Math.max(0.001, 1 - age / 0.48) * Math.sqrt(intensity);
      writeViewerTRS(pFlash.exArr, fi, [0, 0, 32 + age * 65], qFromAxisAngle(0, 0, 1, age * 9.5), [s, s, s]);
    } else if (secAge >= 0 && secAge < 0.34) {
      const s = (0.45 + 2.35 * Math.sin(Math.PI * Math.min(1, secAge / 0.11))) * Math.max(0.001, 1 - secAge / 0.34) * Math.sqrt(intensity);
      writeViewerTRS(pFlash.exArr, fi, rbStates['wreck_chassis'].pos, qFromAxisAngle(1, 0.5, 0.3, secAge * 12), [s, s, s]);
    } else {
      writeViewerTRS(pFlash.exArr, fi, [0, 0, 32], [0,0,0,1], [0.0001, 0.0001, 0.0001]);
    }

    for (const nm in rbStates) {
      const st = rbStates[nm];
      writeViewerTRS(v.partMap[nm].exArr, fi, st.pos, st.q, [1,1,1]);
    }
    for (const wn in wheelStates) {
      const ws = wheelStates[wn];
      const cy = Math.cos(ws.yaw), sy = Math.sin(ws.yaw);
      const cl = Math.cos(ws.lean), sl = Math.sin(ws.lean);
      const cs = Math.cos(ws.spin), ss = Math.sin(ws.spin);
      // Rz * Rx * Ry
      const m = [
        cy*cs + sy*sl*ss, -sy*cl, cy*ss - sy*sl*cs,
        sy*cs - cy*sl*ss,  cy*cl, sy*ss + cy*sl*cs,
        -cl*ss,            sl,    cl*cs
      ];
      writeViewerTRS(v.partMap[wn].exArr, fi, ws.pos, mat3ToQ(m), [1,1,1]);
    }

    if (fi === nFrames - 1) break;

    for (let sub = 0; sub < substeps; sub++) {
      for (const nm in rbStates) {
        const st = rbStates[nm];
        st.sparkCd = Math.max(0, st.sparkCd - dt);
        st.vel[2] -= 560.0 * dt;
        const ld = Math.max(0, 1 - st.linD * dt), ad = Math.max(0, 1 - st.angD * dt);
        st.vel[0] *= ld; st.vel[1] *= ld; st.vel[2] *= ld;
        st.omega[0] *= ad; st.omega[1] *= ad; st.omega[2] *= ad;
        st.pos[0] += st.vel[0] * dt; st.pos[1] += st.vel[1] * dt; st.pos[2] += st.vel[2] * dt;
        if (st.pos[2] > st.maxZ) st.maxZ = st.pos[2];

        const wm = Math.hypot(st.omega[0], st.omega[1], st.omega[2]);
        st.cumRot += wm * dt;
        if (wm > 1e-7) st.q = qNorm(qMul(qFromAxisAngle(st.omega[0], st.omega[1], st.omega[2], wm * dt), st.q));

        const Rm = qToMat3(st.q);
        const hull = st.hull;
        let maxPen = 0, sumPen = 0, cx = 0, cy = 0;
        for (let i = 0; i < hull.length; i++) {
          const h = hull[i];
          const wz = Rm[6]*h[0] + Rm[7]*h[1] + Rm[8]*h[2] + st.pos[2];
          if (wz < 0) {
            const pen = -wz;
            if (pen > maxPen) maxPen = pen;
            sumPen += pen;
            cx += (Rm[0]*h[0] + Rm[1]*h[1] + Rm[2]*h[2] + st.pos[0]) * pen;
            cy += (Rm[3]*h[0] + Rm[4]*h[1] + Rm[5]*h[2] + st.pos[1]) * pen;
          }
        }

        if (sumPen > 0) {
          st.pos[2] += maxPen;
          cx /= sumPen; cy /= sumPen;
          const rx = cx - st.pos[0], ry = cy - st.pos[1], rz = -st.pos[2];
          const vpx = st.vel[0] + (st.omega[1]*rz - st.omega[2]*ry);
          const vpy = st.vel[1] + (st.omega[2]*rx - st.omega[0]*rz);
          const vpz = st.vel[2] + (st.omega[0]*ry - st.omega[1]*rx);

          if (vpz < 0) {
            // invI_world * v helper via Rm * diag(invI) * Rm^T
            const applyInvI = (vx, vy, vz) => {
              const bx = Rm[0]*vx + Rm[3]*vy + Rm[6]*vz;
              const by = Rm[1]*vx + Rm[4]*vy + Rm[7]*vz;
              const bz = Rm[2]*vx + Rm[5]*vy + Rm[8]*vz;
              const sx = bx * st.invI[0], sy = by * st.invI[1], sz = bz * st.invI[2];
              return [
                Rm[0]*sx + Rm[1]*sy + Rm[2]*sz,
                Rm[3]*sx + Rm[4]*sy + Rm[5]*sz,
                Rm[6]*sx + Rm[7]*sy + Rm[8]*sz,
              ];
            };

            const rnx = ry, rny = -rx, rnz = 0; // r x n where n=(0,0,1)
            const irn = applyInvI(rnx, rny, rnz);
            const cN = cross3(irn, [rx, ry, rz]);
            const denom = 1.0 + cN[2];
            const eEff = vpz < -60 ? st.e : (vpz < -22 ? st.e * ((-vpz - 22) / 38) : 0);
            const jn = -(1 + eEff) * vpz / Math.max(1e-6, denom);

            st.vel[2] += jn;
            const dwN = applyInvI(ry * jn, -rx * jn, 0);
            st.omega[0] += dwN[0]; st.omega[1] += dwN[1]; st.omega[2] += dwN[2];

            // Tangential rolling/scraping impulse
            const vtX = st.vel[0] + (st.omega[1]*rz - st.omega[2]*ry);
            const vtY = st.vel[1] + (st.omega[2]*rx - st.omega[0]*rz);
            const vtLen = Math.hypot(vtX, vtY);
            if (vtLen > 1e-4) {
              const tx = vtX / vtLen, ty = vtY / vtLen;
              const rt = cross3([rx, ry, rz], [tx, ty, 0]);
              const irt = applyInvI(rt[0], rt[1], rt[2]);
              const cT = cross3(irt, [rx, ry, rz]);
              const denomT = 1.0 + (cT[0]*tx + cT[1]*ty);
              const jt = Math.min(st.mu * jn, vtLen / Math.max(1e-6, denomT));
              const impTx = -jt * tx, impTy = -jt * ty;
              st.vel[0] += impTx; st.vel[1] += impTy;
              const rxt = cross3([rx, ry, rz], [impTx, impTy, 0]);
              const dwT = applyInvI(rxt[0], rxt[1], rxt[2]);
              st.omega[0] += dwT[0]; st.omega[1] += dwT[1]; st.omega[2] += dwT[2];
            }

            const impE = -vpz + 0.35 * vtLen;
            if (impE > 75 && st.sparkCd <= 0 && newSparks.length < 420) {
              newSparks.push({
                t: +(fi * dtFrame).toFixed(3),
                p: [+(cy * SCALE).toFixed(3), 0.04, +(cx * SCALE).toFixed(3)],
                i: +Math.min(1, impE / 320).toFixed(2),
                k: nm === 'wreck_chassis' ? 'wreck' : 'metal'
              });
              st.sparkCd = nm === 'wreck_chassis' ? 0.055 : 0.095;
            }
          }

          const spdTot = Math.hypot(st.vel[0], st.vel[1], st.vel[2]);
          if (age > 4.8 && spdTot < 48 && Math.abs(st.vel[2]) < 18) {
            const sd = Math.max(0, 1 - 4.5 * dt);
            st.vel[0] *= sd; st.vel[1] *= sd; st.vel[2] *= sd;
            st.omega[0] *= sd; st.omega[1] *= sd; st.omega[2] *= sd;
          }
        }
      }

      // Flying & gyroscopic rolling tires
      for (const wn in wheelStates) {
        const ws = wheelStates[wn];
        const al = Math.abs(ws.lean);
        const zc = wRad * Math.cos(al) + wHalfW * Math.sin(al);
        if (ws.mode === 'air') {
          ws.vel[2] -= 560.0 * dt;
          ws.pos[0] += ws.vel[0] * dt; ws.pos[1] += ws.vel[1] * dt; ws.pos[2] += ws.vel[2] * dt;
          ws.spin += ws.spinRate * dt;
          ws.lean = Math.max(-1.35, Math.min(1.35, ws.lean + ws.leanVel * dt * 0.42));
          if (Math.hypot(ws.vel[0], ws.vel[1]) > 25) ws.yaw = Math.atan2(ws.vel[1], ws.vel[0]);
          if (ws.pos[2] <= zc) {
            ws.pos[2] = zc;
            if (newSparks.length < 420) {
              newSparks.push({
                t: +(fi * dtFrame).toFixed(3),
                p: [+(ws.pos[1]*SCALE).toFixed(3), 0.03, +(ws.pos[0]*SCALE).toFixed(3)],
                i: +Math.min(1, Math.abs(ws.vel[2]) / 450).toFixed(2),
                k: 'tire'
              });
            }
            if (ws.vel[2] < -65 && ws.bounces < ws.maxB) {
              ws.vel[2] = -ws.vel[2] * 0.76;
              ws.vel[0] *= 0.91; ws.vel[1] *= 0.91;
              ws.bounces++;
              ws.leanVel = -ws.leanVel * 0.68 + rnd(-0.6, 0.6);
            } else {
              ws.mode = 'roll';
              ws.rollSpd = Math.max(210, Math.min(460, Math.hypot(ws.vel[0], ws.vel[1])));
              ws.vel = [0,0,0];
              ws.lean = ws.side * (18 + rnd(0, 12)) * Math.PI / 180;
            }
          }
        } else {
          if (ws.rollSpd > 1.5) {
            const step = ws.rollSpd * dt;
            ws.pos[0] += Math.cos(ws.yaw) * step;
            ws.pos[1] += Math.sin(ws.yaw) * step;
            ws.spin -= step / Math.max(4, wRad);
            ws.yaw -= Math.sin(ws.lean) * (1.95 / Math.max(18, ws.rollSpd * 0.13)) * step;
            ws.rollSpd = Math.max(0, ws.rollSpd * (1 - 0.44 * dt) - 12.0 * dt);
            const sf = Math.min(1, ws.rollSpd / 230);
            const tLean = (18 + Math.pow(1 - sf, 1.8) * 69.5) * Math.PI / 180;
            ws.precess += (12 + (1 - sf) * 16) * dt;
            ws.lean = ws.side * tLean + Math.sin(ws.precess) * (8.5 * Math.PI / 180) * sf;
            if (ws.rollSpd < 60) ws.yaw -= ws.side * 3.0 * dt;
          } else {
            ws.lean = ws.side * 87.5 * Math.PI / 180;
          }
          const al2 = Math.abs(ws.lean);
          ws.pos[2] = wRad * Math.cos(al2) + wHalfW * Math.sin(al2);
        }
      }
    }
  }

  v.sparks = newSparks;
  const wst = rbStates['wreck_chassis'];
  let maxWd = 0;
  for (const wn in wheelStates) {
    const d = Math.hypot(wheelStates[wn].pos[0], wheelStates[wn].pos[1]) * SCALE;
    if (d > maxWd) maxWd = d;
  }
  v.liveStats = {
    peakAltM: +(wst.maxZ * SCALE).toFixed(1),
    barrelRevs: +(wst.cumRot / (2 * Math.PI)).toFixed(1),
    rollDistM: +(Math.hypot(wst.pos[0], wst.pos[1]) * SCALE).toFixed(1),
    wheelDistM: +maxWd.toFixed(1),
  };
}

// --- Interactive Studio State ---
let selectedVeh = 'all';
let clipMode = 'interactive';
let camPreset = 'orbit';
let intensityMul = 1.0;
let speedMul = 1.0;
let playing = true;
let simTime = 0.0;
let camShake = 0.0;

const lineupX = { hdtruck: -7.5, schoolbus: 0.0, gtcar: 7.5 };
const instances = {};
const particles = [];

function spawnParticle(x, y, z, vx, vy, vz, size, r, g, b, a, life, additive, grav = 0, grow = 0.45) {
  if (particles.length >= MAX_PARTS) return;
  particles.push({ x, y, z, vx, vy, vz, size, r, g, b, a, age: 0, life, additive, grav, grow });
}

function updateTelemetryUI() {
  const bar = document.getElementById('telemetryBar');
  const sub = document.getElementById('vehSubtitle');
  if (selectedVeh === 'all') {
    sub.textContent = 'All 3 Wild Vehicles • Shoot or Detonate One for a Domino Chain-Reaction!';
    bar.innerHTML = DATA.kinds.map(k => {
      const v = vehGPU[k];
      return `<div class="stat-pill">${v.label}: <b>${v.liveStats.peakAltM}m</b> launch &bull; <b>${v.liveStats.barrelRevs}x</b> rolls &bull; <b>${v.nWheels}</b> wheels (<b>${v.liveStats.wheelDistM}m</b>)</div>`;
    }).join('');
  } else {
    const v = vehGPU[selectedVeh];
    sub.textContent = v.subtitle;
    bar.innerHTML = `
      <div class="stat-pill">Peak Airborne Altitude: <b>${v.liveStats.peakAltM} m</b></div>
      <div class="stat-pill">Air + Ground Spin: <b>${v.liveStats.barrelRevs} rev</b></div>
      <div class="stat-pill">Ground Roll Travel: <b>${v.liveStats.rollDistM} m</b></div>
      <div class="stat-pill">Flying Wheels (${v.nWheels}): <b>${v.liveStats.wheelDistM} m</b></div>
    `;
  }
}

function resetInstances() {
  for (const k of DATA.kinds) {
    instances[k] = {
      hp: DATA.vehicles[k].maxHp,
      maxHp: DATA.vehicles[k].maxHp,
      state: 'idle',
      stateT: Math.random() * 1.4,
      flinchT: 0,
      chainDelay: 0,
      boomSounded: false,
      lastEventT: -1,
      scorch: 0,
      shockR: 0,
    };
  }
  particles.length = 0;
  simTime = 0;
  camShake = 0;
  updateHud();
  updateTelemetryUI();
}

function updateHud() {
  const k = selectedVeh === 'all'
    ? (DATA.kinds.find(x => instances[x].state !== 'explode') || 'schoolbus')
    : selectedVeh;
  const inst = instances[k];
  const pct = Math.max(0, Math.min(100, (inst.hp / inst.maxHp) * 100));
  const fill = document.getElementById('hpFill');
  fill.style.width = pct + '%';
  fill.style.background = inst.state === 'explode' ? '#ef4444' : (inst.state === 'fire' ? '#f97316' : '#22c55e');
  document.getElementById('hpText').textContent = `${Math.ceil(inst.hp)} / ${inst.maxHp} HP`;
  const badge = document.getElementById('stateBadge');
  if (inst.state === 'explode') { badge.textContent = 'AIRBORNE / ROLLING WRECK!'; badge.className = 'badge wreck'; }
  else if (inst.state === 'fire') { badge.textContent = 'COOKING OFF!'; badge.className = 'badge fire'; }
  else { badge.textContent = 'IDLE RUNNING'; badge.className = 'badge'; }
}

function emitBigExplosionBurst(wx, wy, wz, scale = 1.0) {
  // Bright expanding fireball core
  for (let i = 0; i < 75; i++) {
    const a = Math.random() * 6.283, el = Math.random() * 1.45;
    const spd = (3.0 + Math.random() * 13.5) * scale;
    spawnParticle(
      wx + (Math.random()-0.5)*1.2, wy + 0.5 + Math.random()*0.8, wz + (Math.random()-0.5)*1.8,
      Math.cos(a)*Math.cos(el)*spd, Math.sin(el)*spd + 3.5*scale, Math.sin(a)*Math.cos(el)*spd,
      (0.95 + Math.random()*1.15)*scale, 1.0, 0.58 + Math.random()*0.3, 0.14, 0.96,
      0.75 + Math.random()*0.65, true, -1.5, 1.15
    );
  }
  // Thick dark billowing blast smoke column
  for (let i = 0; i < 50; i++) {
    const a = Math.random() * 6.283, spd = (1.5 + Math.random() * 6.5) * scale;
    const g = 0.10 + Math.random() * 0.08;
    spawnParticle(
      wx + (Math.random()-0.5)*1.6, wy + 0.8 + Math.random()*1.2, wz + (Math.random()-0.5)*2.0,
      Math.cos(a)*spd, 3.2 + Math.random()*6.5*scale, Math.sin(a)*spd,
      1.25 + Math.random()*1.35, g, g, g*1.06, 0.56,
      2.1 + Math.random()*1.5, false, -0.4, 0.95
    );
  }
  // High-speed ballistic ember sparks
  for (let i = 0; i < 65; i++) {
    const a = Math.random() * 6.283, spd = (7 + Math.random() * 22) * scale;
    spawnParticle(
      wx, wy + 0.8, wz,
      Math.cos(a)*spd, 5 + Math.random()*18*scale, Math.sin(a)*spd,
      0.11 + Math.random()*0.09, 1.0, 0.84, 0.36, 1.0,
      0.85 + Math.random()*0.75, true, 13.5, 0.0
    );
  }
}

function triggerVehicleExplode(k) {
  const inst = instances[k];
  if (inst.state === 'explode') return;
  inst.state = 'explode';
  inst.hp = 0;
  const v = vehGPU[k];
  inst.stateT = Math.max(0, (v.boomFrame - 2) / v.fpsEx);
  inst.lastEventT = inst.stateT;
  inst.boomSounded = false;

  if (selectedVeh === 'all') {
    const idx = DATA.kinds.indexOf(k);
    for (const nk of DATA.kinds) {
      if (nk !== k && instances[nk].state !== 'explode' && instances[nk].chainDelay <= 0) {
        const dist = Math.abs(DATA.kinds.indexOf(nk) - idx);
        if (instances[nk].state === 'idle') { instances[nk].state = 'fire'; instances[nk].stateT = 0.9; }
        instances[nk].chainDelay = 0.38 * dist;
      }
    }
  }
  updateHud();
}

function detonateNow() {
  if (clipMode !== 'interactive') {
    clipMode = 'interactive';
    document.querySelectorAll('.clip-btn').forEach(b => b.classList.toggle('active', b.dataset.clip === 'interactive'));
  }
  const targets = selectedVeh === 'all'
    ? DATA.kinds.filter(k => instances[k].state !== 'explode')
    : [selectedVeh];
  if (!targets.length) {
    resetInstances();
    triggerVehicleExplode(selectedVeh === 'all' ? 'schoolbus' : selectedVeh);
    return;
  }
  // In lineup mode, start with the center School Bus or first intact vehicle!
  const pick = targets.includes('schoolbus') ? 'schoolbus' : targets[0];
  triggerVehicleExplode(pick);
}

function shootTargetVehicle() {
  if (clipMode !== 'interactive') {
    clipMode = 'interactive';
    document.querySelectorAll('.clip-btn').forEach(b => b.classList.toggle('active', b.dataset.clip === 'interactive'));
  }
  const targets = selectedVeh === 'all'
    ? DATA.kinds.filter(k => instances[k].state !== 'explode')
    : [selectedVeh];
  if (!targets.length) { resetInstances(); return; }
  const k = targets[0];
  const inst = instances[k];

  playBulletClang();
  const wx = selectedVeh === 'all' ? lineupX[k] : 0;
  for (let i = 0; i < 18; i++) {
    spawnParticle(
      wx + (Math.random()-0.5)*1.2, 0.85 + Math.random()*0.7, (Math.random()-0.5)*2.4,
      (Math.random()-0.5)*7.5, 2.5 + Math.random()*5.5, (Math.random()-0.5)*7.5,
      0.09, 1.0, 0.85, 0.35, 1.0, 0.45, true, 12.0, 0.0
    );
  }
  inst.hp = Math.max(0, inst.hp - 62);
  inst.flinchT = 0.28;
  if (inst.hp <= 0) triggerVehicleExplode(k);
  else if (inst.hp <= inst.maxHp * 0.48 && inst.state === 'idle') {
    inst.state = 'fire';
    inst.stateT = 0.9;
  }
  updateHud();
}

resetInstances();

// --- Camera Orbit / Pan / Zoom & Presets ---
let camYaw = 0.64, camPitch = 0.28, camDist = 17.5;
let camTarget = [0, 1.35, 0];
let panOffset = [0, 0, 0];
let dragBtn = -1, lastX = 0, lastY = 0;

canvas.addEventListener('contextmenu', e => e.preventDefault());
canvas.addEventListener('mousedown', e => { dragBtn = e.button; lastX = e.clientX; lastY = e.clientY; ensureAudio(); });
window.addEventListener('mouseup', () => { dragBtn = -1; });
window.addEventListener('mousemove', e => {
  if (dragBtn < 0) return;
  const dx = e.clientX - lastX, dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  if (dragBtn === 0) {
    camYaw -= dx * 0.0068;
    camPitch = Math.max(0.04, Math.min(1.42, camPitch + dy * 0.0058));
  } else {
    const panScale = camDist * 0.0014;
    panOffset[0] -= Math.cos(camYaw) * dx * panScale;
    panOffset[2] += Math.sin(camYaw) * dx * panScale;
    panOffset[1] = Math.max(-1.0, Math.min(18.0, panOffset[1] + dy * panScale));
  }
});
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  camDist = Math.max(3.6, Math.min(68.0, camDist * (1 + e.deltaY * 0.001)));
}, { passive: false });

window.addEventListener('keydown', e => {
  if (e.code === 'Space') { e.preventDefault(); shootTargetVehicle(); }
  else if (e.code === 'KeyR') { e.preventDefault(); detonateNow(); }
  else if (e.code === 'Escape') { resetInstances(); }
});

document.getElementById('btnDetonate').onclick = detonateNow;
document.getElementById('btnShoot').onclick = shootTargetVehicle;
document.getElementById('btnReset').onclick = resetInstances;
document.getElementById('btnPlayPause').onclick = e => {
  playing = !playing;
  e.target.textContent = playing ? 'Pause' : 'Play';
};

document.querySelectorAll('.veh-btn').forEach(btn => btn.onclick = () => {
  selectedVeh = btn.dataset.veh;
  document.querySelectorAll('.veh-btn').forEach(b => b.classList.toggle('active', b === btn));
  panOffset = [0, 0, 0];
  camDist = selectedVeh === 'all' ? 17.5 : (selectedVeh === 'schoolbus' ? 11.8 : 9.6);
  updateHud();
  updateTelemetryUI();
});

document.querySelectorAll('.clip-btn').forEach(btn => btn.onclick = () => {
  clipMode = btn.dataset.clip;
  document.querySelectorAll('.clip-btn').forEach(b => b.classList.toggle('active', b === btn));
  simTime = 0;
  particles.length = 0;
  for (const k of DATA.kinds) { instances[k].lastEventT = -1; instances[k].scorch = 0; instances[k].shockR = 0; }
  if (clipMode === 'interactive') resetInstances();
});

document.querySelectorAll('.int-btn').forEach(btn => btn.onclick = () => {
  intensityMul = parseFloat(btn.dataset.int);
  document.querySelectorAll('.int-btn').forEach(b => b.classList.toggle('active', b === btn));
  for (const k of DATA.kinds) resimulateVehicleJS(k, intensityMul, intensityMul === 1.0 ? 0.0 : 0.25);
  updateTelemetryUI();
  resetInstances();
  detonateNow();
});

document.getElementById('btnReroll').onclick = () => {
  for (const k of DATA.kinds) resimulateVehicleJS(k, intensityMul, 1.0);
  updateTelemetryUI();
  resetInstances();
  detonateNow();
};

document.querySelectorAll('.cam-btn').forEach(btn => btn.onclick = () => {
  camPreset = btn.dataset.cam;
  panOffset = [0, 0, 0];
  document.querySelectorAll('.cam-btn').forEach(b => b.classList.toggle('active', b === btn));
});

document.querySelectorAll('.spd-btn').forEach(btn => btn.onclick = () => {
  speedMul = parseFloat(btn.dataset.spd);
  document.querySelectorAll('.spd-btn').forEach(b => b.classList.toggle('active', b === btn));
});

const scrubber = document.getElementById('scrubber');
scrubber.addEventListener('input', () => {
  if (clipMode === 'interactive') {
    clipMode = 'explode';
    document.querySelectorAll('.clip-btn').forEach(b => b.classList.toggle('active', b.dataset.clip === 'explode'));
  }
  const dur = clipMode === 'idle' ? 2.0 : (clipMode === 'fire' ? 3.0 : 7.5);
  simTime = (scrubber.value / 1000) * dur;
  for (const k of DATA.kinds) instances[k].lastEventT = simTime;
});

// --- Matrix & TRS Sampling Helpers ---
function mat4Persp(fov, aspect, near, far) {
  const f = 1.0 / Math.tan(fov * 0.5), nf = 1 / (near - far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
}
function mat4LookAt(eye, ctr, up) {
  let zx = eye[0]-ctr[0], zy = eye[1]-ctr[1], zz = eye[2]-ctr[2];
  let zl = Math.hypot(zx,zy,zz)||1; zx/=zl; zy/=zl; zz/=zl;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  let xl = Math.hypot(xx,xy,xz)||1; xx/=xl; xy/=xl; xz/=xl;
  let yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  return new Float32Array([
    xx, yx, zx, 0,  xy, yy, zy, 0,  xz, yz, zz, 0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]), -(yx*eye[0]+yy*eye[1]+yz*eye[2]), -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}
function mat4Mul(a, b) {
  const o = new Float32Array(16);
  for (let i=0;i<4;i++) for (let j=0;j<4;j++) o[j*4+i] = a[i]*b[j*4]+a[4+i]*b[j*4+1]+a[8+i]*b[j*4+2]+a[12+i]*b[j*4+3];
  return o;
}

const outPos = new Float32Array(3), outRot = new Float32Array(4), outScl = new Float32Array(3);
function sampleTRS(arr, nFrames, fps, tSec, loop, stepScale) {
  let f = tSec * fps;
  if (loop) f = ((f % (nFrames - 1)) + (nFrames - 1)) % (nFrames - 1);
  else f = Math.max(0, Math.min(nFrames - 1.0001, f));
  const i0 = Math.floor(f), i1 = Math.min(nFrames - 1, i0 + 1), a = f - i0;
  const b0 = i0 * 10, b1 = i1 * 10;
  for (let c=0;c<3;c++) outPos[c] = arr[b0+c] + (arr[b1+c] - arr[b0+c]) * a;
  let dot = 0;
  for (let c=0;c<4;c++) dot += arr[b0+3+c] * arr[b1+3+c];
  const sgn = dot < 0 ? -1 : 1;
  let ql = 0;
  for (let c=0;c<4;c++) { outRot[c] = arr[b0+3+c] + (arr[b1+3+c]*sgn - arr[b0+3+c]) * a; ql += outRot[c]*outRot[c]; }
  ql = 1.0 / (Math.sqrt(ql) || 1);
  for (let c=0;c<4;c++) outRot[c] *= ql;
  for (let c=0;c<3;c++) outScl[c] = stepScale ? arr[b0+7+c] : (arr[b0+7+c] + (arr[b1+7+c] - arr[b0+7+c]) * a);
}

function processExplosionEvents(k, wx, tPrev, tCurr) {
  if (tCurr <= tPrev) return;
  const v = vehGPU[k];
  for (let i = 0; i < v.sparks.length; i++) {
    const ev = v.sparks[i];
    if (ev.t > tPrev && ev.t <= tCurr) {
      const px = wx + ev.p[0], py = ev.p[1], pz = ev.p[2];
      if (ev.k === 'airburst') {
        playMassiveBoom(0.82 * intensityMul);
        camShake = Math.max(camShake, 0.32 * intensityMul);
        emitBigExplosionBurst(px, py, pz, 0.72 * Math.sqrt(intensityMul));
      } else if (ev.k === 'wreck') {
        playRollCrunch(ev.i);
        camShake = Math.max(camShake, 0.14 * ev.i);
        const nSpk = Math.floor(14 + 26 * ev.i);
        for (let s = 0; s < nSpk; s++) {
          const a = Math.random() * 6.283, spd = (3.5 + Math.random() * 11.5) * (0.6 + ev.i);
          spawnParticle(
            px + (Math.random()-0.5)*0.6, py + 0.08, pz + (Math.random()-0.5)*0.6,
            Math.cos(a)*spd, 1.8 + Math.random()*6.5, Math.sin(a)*spd,
            0.08 + Math.random()*0.07, 1.0, 0.78 + Math.random()*0.2, 0.28, 1.0,
            0.38 + Math.random()*0.42, true, 13.5, 0.0
          );
        }
        for (let d = 0; d < 6; d++) {
          const a = Math.random() * 6.283, spd = 1.0 + Math.random() * 3.2;
          spawnParticle(
            px, 0.12, pz, Math.cos(a)*spd, 0.8 + Math.random()*1.8, Math.sin(a)*spd,
            0.55 + Math.random()*0.5, 0.26, 0.24, 0.22, 0.34 * ev.i, 0.95, false, -0.2, 0.65
          );
        }
      } else if (ev.k === 'metal') {
        if (ev.i > 0.45 && Math.random() < 0.45) playRollCrunch(ev.i * 0.55);
        for (let s = 0; s < 8; s++) {
          const a = Math.random() * 6.283, spd = 2.5 + Math.random() * 7.5;
          spawnParticle(
            px, py + 0.05, pz, Math.cos(a)*spd, 1.4 + Math.random()*4.2, Math.sin(a)*spd,
            0.07, 1.0, 0.82, 0.34, 0.95, 0.32 + Math.random()*0.25, true, 13.5, 0.0
          );
        }
      } else if (ev.k === 'tire') {
        if (ev.i > 0.25) playTireBounce(ev.i);
        for (let d = 0; d < 5; d++) {
          const a = Math.random() * 6.283, spd = 0.8 + Math.random() * 2.4;
          spawnParticle(
            px, 0.08, pz, Math.cos(a)*spd, 0.5 + Math.random()*1.2, Math.sin(a)*spd,
            0.35 + Math.random()*0.25, 0.22, 0.22, 0.24, 0.32, 0.65, false, -0.1, 0.45
          );
        }
      }
    }
  }
}

// Auto-trigger a dramatic demonstration right after load? No — keep interactive ready, OR let's keep intact & responsive!
let lastNow = performance.now();
function frame(now) {
  requestAnimationFrame(frame);
  const rawDt = Math.min(0.05, (now - lastNow) * 0.001);
  lastNow = now;
  const dt = playing ? rawDt * speedMul : 0;

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.floor(canvas.clientWidth * dpr) || canvas.height !== Math.floor(canvas.clientHeight * dpr)) {
    canvas.width = Math.floor(canvas.clientWidth * dpr);
    canvas.height = Math.floor(canvas.clientHeight * dpr);
  }
  gl.viewport(0, 0, canvas.width, canvas.height);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  const activeKinds = selectedVeh === 'all' ? DATA.kinds : [selectedVeh];
  let fireLightPos = [0, 2, 0], fireLightInt = 0;

  if (clipMode !== 'interactive') {
    const dur = clipMode === 'idle' ? 2.0 : (clipMode === 'fire' ? 3.0 : 7.5);
    const prevT = simTime;
    simTime = (simTime + dt) % dur;
    if (simTime < prevT) {
      for (const k of DATA.kinds) { instances[k].lastEventT = -1; instances[k].shockR = 0; instances[k].scorch = 0; }
    }
    scrubber.value = Math.round((simTime / dur) * 1000);
    document.getElementById('timeLabel').textContent = `${simTime.toFixed(2)}s / ${dur.toFixed(1)}s`;
  } else {
    simTime += dt;
    const exInst = activeKinds.map(k => instances[k]).find(i => i.state === 'explode');
    if (exInst) {
      scrubber.value = Math.min(1000, Math.round((exInst.stateT / 7.5) * 1000));
      document.getElementById('timeLabel').textContent = `BLAST ${exInst.stateT.toFixed(2)}s / 7.5s`;
    } else {
      document.getElementById('timeLabel').textContent = `LIVE INTERACTIVE`;
    }
  }

  // Update vehicles, shockwaves, scorch decals & volumetric fire/smoke trails
  const scorchUniform = new Float32Array(12);
  const shockUniform = new Float32Array(12);

  activeKinds.forEach((k, idx) => {
    const v = vehGPU[k];
    const inst = instances[k];
    const wx = selectedVeh === 'all' ? lineupX[k] : 0;
    const h = v.hoodOfs;
    const boomT = v.boomFrame / v.fpsEx;
    let mode = clipMode, tLocal = simTime;

    if (clipMode === 'interactive') {
      const prevT = inst.stateT;
      inst.stateT += dt;
      if (inst.flinchT > 0) inst.flinchT = Math.max(0, inst.flinchT - dt);
      if (inst.chainDelay > 0) {
        inst.chainDelay -= dt;
        if (inst.chainDelay <= 0) triggerVehicleExplode(k);
      }
      if (inst.state === 'fire' && inst.chainDelay <= 0) {
        inst.hp = Math.max(0, inst.hp - 36 * dt);
        updateHud();
        if (inst.hp <= 0) triggerVehicleExplode(k);
      }
      mode = inst.state;
      tLocal = inst.stateT;

      if (mode === 'explode') {
        if (!inst.boomSounded && tLocal >= boomT) {
          inst.boomSounded = true;
          inst.scorch = 1.0;
          inst.shockR = 0.5;
          camShake = Math.max(camShake, 0.52 * intensityMul);
          playMassiveBoom(intensityMul);
          emitBigExplosionBurst(wx, 0.6, 0, Math.sqrt(intensityMul));
        }
        processExplosionEvents(k, wx, prevT, tLocal);
      }
    } else if (clipMode === 'explode') {
      if (inst.lastEventT < boomT && tLocal >= boomT && dt > 0) {
        inst.scorch = 1.0;
        inst.shockR = 0.5;
        camShake = Math.max(camShake, 0.48 * intensityMul);
        playMassiveBoom(intensityMul);
        emitBigExplosionBurst(wx, 0.6, 0, Math.sqrt(intensityMul));
      }
      if (dt > 0) processExplosionEvents(k, wx, Math.max(0, inst.lastEventT), tLocal);
      inst.lastEventT = tLocal;
    }

    if (inst.shockR > 0) {
      inst.shockR += 34.0 * dt;
      if (inst.shockR > 38.0) inst.shockR = 0;
    }
    scorchUniform[idx*4] = wx; scorchUniform[idx*4+1] = 0; scorchUniform[idx*4+2] = 0; scorchUniform[idx*4+3] = inst.scorch;
    shockUniform[idx*4] = wx;  shockUniform[idx*4+1] = 0;  shockUniform[idx*4+2] = 0;  shockUniform[idx*4+3] = inst.shockR;

    const preCook = (mode === 'fire' && (clipMode === 'interactive' || tLocal > 0.85))
                 || (mode === 'explode' && tLocal < boomT);

    if (preCook && dt > 0) {
      fireLightPos = [wx + h[0], h[1] + 0.5, h[2]];
      fireLightInt = Math.max(fireLightInt, 1.65 + 0.4 * Math.sin(now * 0.035));
      if (Math.random() < 0.92) {
        spawnParticle(wx + h[0] + (Math.random()-0.5)*0.55, h[1], h[2] + (Math.random()-0.5)*0.55,
          (Math.random()-0.5)*1.2, 2.2+Math.random()*2.5, (Math.random()-0.5)*1.2,
          0.42+Math.random()*0.32, 1.0, 0.56, 0.12, 0.90, 0.48, true, -0.8, 0.55);
      }
      if (Math.random() < 0.55) {
        spawnParticle(wx + h[0] + (Math.random()-0.5)*0.6, h[1]+0.3, h[2] + (Math.random()-0.5)*0.6,
          (Math.random()-0.5)*1.0, 2.5+Math.random()*1.8, (Math.random()-0.5)*1.0,
          0.62+Math.random()*0.45, 0.13, 0.13, 0.15, 0.46, 1.45, false, -0.3, 0.75);
      }
    } else if (mode === 'explode' && tLocal >= boomT && dt > 0) {
      // Stream roaring flames & black smoke directly off the airborne flipping & barrel-rolling wreck_chassis!
      const pWreck = v.partMap['wreck_chassis'];
      sampleTRS(pWreck.exArr, v.nFramesEx, v.fpsEx, tLocal, false, false);
      const rx = wx + outPos[0], ry = outPos[1], rz = outPos[2];
      const ageAfterBoom = tLocal - boomT;
      fireLightPos = [rx, ry + 0.8, rz];
      fireLightInt = Math.max(fireLightInt, ageAfterBoom < 1.2 ? (5.5 - ageAfterBoom * 3.0) : 1.55);

      if (Math.random() < (ageAfterBoom < 4.5 ? 0.95 : 0.55)) {
        spawnParticle(
          rx + (Math.random()-0.5)*1.1, ry + (Math.random()-0.3)*0.7, rz + (Math.random()-0.5)*1.4,
          (Math.random()-0.5)*1.8, 1.6 + Math.random()*2.8, (Math.random()-0.5)*1.8,
          0.48 + Math.random()*0.42, 1.0, 0.48 + Math.random()*0.25, 0.09, 0.86,
          0.42 + Math.random()*0.32, true, -1.2, 0.65
        );
      }
      if (Math.random() < (ageAfterBoom < 5.0 ? 0.72 : 0.35)) {
        const g = 0.11 + Math.random() * 0.06;
        spawnParticle(
          rx + (Math.random()-0.5)*1.2, ry + 0.3, rz + (Math.random()-0.5)*1.5,
          (Math.random()-0.5)*1.2, 1.8 + Math.random()*2.2, (Math.random()-0.5)*1.2,
          0.72 + Math.random()*0.55, g, g, g*1.05, 0.44,
          1.35 + Math.random()*0.85, false, -0.35, 0.78
        );
      }

      // Hot rubber smoke trails streaming off flying tires during first 2.8s!
      if (ageAfterBoom < 2.8 && Math.random() < 0.65) {
        const wPick = v.parts.filter(p => p.name.startsWith('wheel_'));
        const wp = wPick[Math.floor(Math.random() * wPick.length)];
        sampleTRS(wp.exArr, v.nFramesEx, v.fpsEx, tLocal, false, false);
        spawnParticle(
          wx + outPos[0], outPos[1], outPos[2],
          (Math.random()-0.5)*0.5, 0.5 + Math.random()*0.8, (Math.random()-0.5)*0.5,
          0.26 + Math.random()*0.18, 0.20, 0.20, 0.22, 0.34, 0.65, false, -0.1, 0.42
        );
      }
    }
  });

  // Camera Target & Preset Tracking
  const focusKind = selectedVeh === 'all'
    ? (DATA.kinds.find(k => instances[k].state === 'explode') || 'schoolbus')
    : selectedVeh;
  const focusWx = selectedVeh === 'all' ? lineupX[focusKind] : 0;
  const fv = vehGPU[focusKind];
  const tFocus = clipMode === 'interactive' ? instances[focusKind].stateT : simTime;
  const isExFocus = (clipMode === 'explode') || (clipMode === 'interactive' && instances[focusKind].state === 'explode');

  let desiredTarget = [panOffset[0], 1.25 + panOffset[1], panOffset[2]];
  if (camPreset === 'wreck' && isExFocus && tFocus >= fv.boomFrame / fv.fpsEx) {
    sampleTRS(fv.partMap['wreck_chassis'].exArr, fv.nFramesEx, fv.fpsEx, tFocus, false, false);
    desiredTarget = [focusWx + outPos[0], Math.max(0.75, outPos[1] * 0.85), outPos[2]];
  } else if (camPreset === 'stunt') {
    camPitch = 0.085;
    if (isExFocus && tFocus >= fv.boomFrame / fv.fpsEx) {
      sampleTRS(fv.partMap['wreck_chassis'].exArr, fv.nFramesEx, fv.fpsEx, tFocus, false, false);
      desiredTarget = [focusWx + outPos[0] * 0.75, Math.max(1.1, outPos[1] * 0.65), outPos[2] * 0.75];
    }
  } else if ((camPreset === 'wheel' || camPreset === 'hood') && isExFocus && tFocus >= fv.boomFrame / fv.fpsEx) {
    const pName = camPreset === 'wheel' ? 'wheel_fl' : 'hood';
    sampleTRS(fv.partMap[pName].exArr, fv.nFramesEx, fv.fpsEx, tFocus, false, false);
    desiredTarget = [focusWx + outPos[0], Math.max(0.4, outPos[1]), outPos[2]];
  }
  for (let c = 0; c < 3; c++) camTarget[c] += (desiredTarget[c] - camTarget[c]) * 0.14;

  camShake = Math.max(0, camShake - rawDt * 1.45);
  const shkX = (Math.random() - 0.5) * camShake;
  const shkY = (Math.random() - 0.5) * camShake;

  const eye = [
    camTarget[0] + camDist * Math.cos(camPitch) * Math.sin(camYaw) + shkX,
    Math.max(0.28, camTarget[1] + camDist * Math.sin(camPitch) + shkY),
    camTarget[2] + camDist * Math.cos(camPitch) * Math.cos(camYaw),
  ];
  const vp = mat4Mul(mat4Persp(0.80, canvas.width / Math.max(1, canvas.height), 0.18, 560.0), mat4LookAt(eye, camTarget, [0, 1, 0]));

  // 1. Draw Sky Dome
  gl.disable(gl.DEPTH_TEST);
  gl.useProgram(progSky);
  gl.bindVertexArray(emptyVao);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  gl.enable(gl.DEPTH_TEST);

  // 2. Draw Stunt Lot Ground, Scorch Craters & Shockwave Rings
  gl.useProgram(progGrid);
  gl.uniformMatrix4fv(gl.getUniformLocation(progGrid, 'uVP'), false, vp);
  gl.uniform4fv(gl.getUniformLocation(progGrid, 'uScorch'), scorchUniform);
  gl.uniform4fv(gl.getUniformLocation(progGrid, 'uShock'), shockUniform);
  gl.uniform3fv(gl.getUniformLocation(progGrid, 'uFirePos'), fireLightPos);
  gl.uniform1f(gl.getUniformLocation(progGrid, 'uFireInt'), fireLightInt);
  gl.bindVertexArray(gridVao);
  gl.drawArrays(gl.TRIANGLES, 0, 6);

  // 3. Draw Soft Ground Drop Shadows under Vehicles, Airborne/Rolling Wrecks & Flying Wheels
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.depthMask(false);
  gl.useProgram(progShad);
  gl.uniformMatrix4fv(gl.getUniformLocation(progShad, 'uVP'), false, vp);
  const locShCtr = gl.getUniformLocation(progShad, 'uCenter');
  const locShRad = gl.getUniformLocation(progShad, 'uRadii');
  const locShYaw = gl.getUniformLocation(progShad, 'uYaw');
  const locShAlp = gl.getUniformLocation(progShad, 'uAlpha');
  gl.bindVertexArray(shadVao);

  for (const k of activeKinds) {
    const v = vehGPU[k];
    const wx = selectedVeh === 'all' ? lineupX[k] : 0;
    let mode = clipMode, tLocal = simTime;
    if (clipMode === 'interactive') { mode = instances[k].state; tLocal = instances[k].stateT; }
    const isPostBoom = mode === 'explode' && tLocal >= v.boomFrame / v.fpsEx;

    if (!isPostBoom) {
      gl.uniform3f(locShCtr, wx, 0, 0);
      gl.uniform2f(locShRad, v.halfWidM * 1.28, v.halfLenM * 1.16);
      gl.uniform1f(locShYaw, 0.0);
      gl.uniform1f(locShAlp, 0.62);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    } else {
      sampleTRS(v.partMap['wreck_chassis'].exArr, v.nFramesEx, v.fpsEx, tLocal, false, false);
      const hFrac = Math.max(0.22, 1.0 / (1.0 + outPos[1] * 0.14));
      gl.uniform3f(locShCtr, wx + outPos[0], 0, outPos[2]);
      gl.uniform2f(locShRad, v.halfWidM * 1.35 / hFrac * 0.65, v.halfLenM * 1.1 / hFrac * 0.65);
      gl.uniform1f(locShYaw, Math.atan2(2*(outRot[3]*outRot[1]+outRot[0]*outRot[2]), 1 - 2*(outRot[1]*outRot[1]+outRot[2]*outRot[2])));
      gl.uniform1f(locShAlp, 0.56 * hFrac);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      for (const p of v.parts) {
        if (!p.name.startsWith('wheel_')) continue;
        sampleTRS(p.exArr, v.nFramesEx, v.fpsEx, tLocal, false, false);
        const wf = Math.max(0.18, 1.0 / (1.0 + outPos[1] * 0.18));
        gl.uniform3f(locShCtr, wx + outPos[0], 0, outPos[2]);
        gl.uniform2f(locShRad, 0.52, 0.52);
        gl.uniform1f(locShYaw, 0.0);
        gl.uniform1f(locShAlp, 0.45 * wf);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }
    }
  }
  gl.depthMask(true);
  gl.disable(gl.BLEND);

  // 4. Draw 3D Multi-Part Vehicles, Airborne Rolling Wrecks, Flying Wheels & Shrapnel
  gl.useProgram(progMesh);
  gl.uniformMatrix4fv(gl.getUniformLocation(progMesh, 'uVP'), false, vp);
  gl.uniform3fv(gl.getUniformLocation(progMesh, 'uCamPos'), eye);
  gl.uniform3fv(gl.getUniformLocation(progMesh, 'uFireLightPos'), fireLightPos);
  gl.uniform1f(gl.getUniformLocation(progMesh, 'uFireLightInt'), fireLightInt);
  gl.uniform1i(gl.getUniformLocation(progMesh, 'uTex'), 0);
  gl.uniform1i(gl.getUniformLocation(progMesh, 'uGlow'), 1);

  const locOfs = gl.getUniformLocation(progMesh, 'uWorldOffset');
  const locPos = gl.getUniformLocation(progMesh, 'uTrsPos');
  const locRot = gl.getUniformLocation(progMesh, 'uTrsRot');
  const locScl = gl.getUniformLocation(progMesh, 'uTrsScl');
  const locFlash = gl.getUniformLocation(progMesh, 'uIsFlash');

  for (const k of activeKinds) {
    const v = vehGPU[k];
    const wx = selectedVeh === 'all' ? lineupX[k] : 0;
    gl.uniform3f(locOfs, wx, 0, 0);

    let mode = clipMode, tLocal = simTime;
    if (clipMode === 'interactive') {
      const inst = instances[k];
      if (inst.state === 'idle' && inst.flinchT > 0) {
        mode = 'fire'; tLocal = (0.28 - inst.flinchT);
      } else {
        mode = inst.state; tLocal = inst.stateT;
      }
    }

    const useBurnSkin = (mode === 'fire' && (clipMode === 'interactive' ? instances[k].state === 'fire' : tLocal > 0.85))
                     || (mode === 'explode' && tLocal >= (v.boomFrame - 8) / v.fpsEx);

    for (const p of v.parts) {
      if (mode === 'idle') sampleTRS(p.idleArr, v.nFramesIdle, 30, tLocal, true, p.stepScale);
      else if (mode === 'fire') sampleTRS(p.fireArr, v.nFramesFire, 30, tLocal, clipMode === 'interactive' && instances[k].state === 'fire', p.stepScale);
      else sampleTRS(p.exArr, v.nFramesEx, v.fpsEx, tLocal, false, p.stepScale);

      if (outScl[0] < 0.005) continue;

      const burnThis = p.burnOnly || useBurnSkin;
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, burnThis ? v.tBurn : v.tIntact);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, burnThis ? v.gBurn : v.gIntact);

      gl.uniform3fv(locPos, outPos);
      gl.uniform4fv(locRot, outRot);
      gl.uniform3fv(locScl, outScl);
      gl.uniform1f(locFlash, p.isFlash ? 1.0 : 0.0);
      gl.bindVertexArray(p.vao);
      gl.drawElements(gl.TRIANGLES, p.ni, gl.UNSIGNED_SHORT, 0);
    }
  }

  // 5. Update & Render Volumetric Fireball, Smoke & Spark Particles
  for (let i = particles.length - 1; i >= 0; i--) {
    const pt = particles[i];
    pt.age += dt;
    if (pt.age >= pt.life) { particles.splice(i, 1); continue; }
    pt.vy -= pt.grav * dt;
    pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.z += pt.vz * dt;
    pt.size += pt.grow * dt;
    if (pt.y < 0.04) {
      pt.y = 0.04;
      pt.vy = Math.abs(pt.vy) * 0.42;
      pt.vx *= 0.72; pt.vz *= 0.72;
    }
  }

  if (particles.length > 0) {
    gl.enable(gl.BLEND);
    gl.depthMask(false);
    gl.useProgram(progPart);
    gl.uniformMatrix4fv(gl.getUniformLocation(progPart, 'uVP'), false, vp);
    gl.uniform1f(gl.getUniformLocation(progPart, 'uViewportH'), canvas.height);
    gl.bindVertexArray(partVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, partVb);

    for (const passAdd of [false, true]) {
      gl.blendFunc(gl.SRC_ALPHA, passAdd ? gl.ONE : gl.ONE_MINUS_SRC_ALPHA);
      let cnt = 0;
      for (const pt of particles) {
        if (pt.additive !== passAdd) continue;
        const fade = Math.pow(1.0 - (pt.age / pt.life), passAdd ? 1.15 : 0.85);
        const o = cnt * 8;
        partData[o]=pt.x; partData[o+1]=pt.y; partData[o+2]=pt.z; partData[o+3]=pt.size;
        partData[o+4]=pt.r; partData[o+5]=pt.g; partData[o+6]=pt.b; partData[o+7]=pt.a * fade;
        cnt++;
      }
      if (cnt > 0) {
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, partData.subarray(0, cnt * 8));
        gl.drawArrays(gl.POINTS, 0, cnt);
      }
    }
    gl.depthMask(true);
    gl.disable(gl.BLEND);
  }
}
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
