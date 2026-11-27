#!/usr/bin/env python3
"""Build a 100% self-contained HTML showcase page for B. Triple Wheeled.

Embeds:
  - Interactive 3D wireframe/shaded turntable extracted from progs/triple_wheeled.md3
  - Interactive 4-gun sequential firing & HUD simulator (with WebAudio synth)
  - Real in-game Zircon screenshots as base64 data URIs (zero external assets)
  - Complete technical reference, 7 big-map spawns (28 spots), and commit changelog

Usage:
  python -I source/mm_tools/triple_wheeled/build_showcase_html.py \
      --pk3 build/zz_triple_wheeled.pk3 \
      --shots-dir <dir_with_screenshots> \
      --out build/triple_wheeled_showcase.html
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
import struct
import zipfile
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import md3lib  # noqa: E402


SHOT_SPECS = [
    (
        "pickup",
        "World Pickup: 4 Spinning & Glowing Rocket Launchers",
        "Spawned via <code>impulse 158</code> (or auto-placed in all 7 big maps). Four Quake rocket launchers bundled in a 2&times;2 ring formation, wrapped in twin plasma halos and a 16-frame pulsing glow shell.",
    ),
    (
        "halo",
        "Third-Person Overhead Halo (<code>chase_active 1</code>)",
        "Other players and third-person chasecam see a scaled, tilted spinning 4-Rocket-Launcher halo orbiting above your head while B. Triple Wheeled is active.",
    ),
    (
        "random_quad",
        "Random 4-Gun Quad-Wield Layout",
        "Bottom-Right stays synced to your held weapon while Bottom-Left, Top-Right (<code>angles_z = 180</code> upside down — here Cyrax Net), and Top-Left (upside down — M4A1 Carbine) roll from the 16-weapon pool.",
    ),
    (
        "quad_rl",
        "4&times; Rocket Launcher Mode (<code>impulse 160</code>)",
        "Forces all four corners to Rocket Launchers — two upright along the bottom and two upside-down hanging from the top corners of the screen.",
    ),
    (
        "quad_fire",
        "Sequential Cascade Firing + Live CSQC HUD",
        "One trigger pull fires Slot 0 immediately, then Slot 1 &rarr; Slot 2 &rarr; Slot 3 spaced by <code>bm_triple_delay</code> (default <code>0.25s</code>). The top 2&times;2 HUD grid flashes orange on the firing corner and green on the next queued corner.",
    ),
]

BIG_MAPS = [
    ("bakersfielddowntown", "24.2 MB", "4 spots", "(-8420 2180 56), (-7940 -5960 56), (-12320 5220 56), (-3559 218 -32)"),
    ("bakersfieldish", "41.6 MB", "4 spots", "(-8676 -5964 56), (-4524 -5844 56), (-2004 3180 60), (-12756 5892 56)"),
    ("spruce", "24.3 MB", "4 spots", "(-1224 -2920 56), (1104 -340 56), (1944 500 56), (-6750 -120 56)"),
    ("soi6", "23.8 MB", "4 spots", "(-200 472 60), (1780 0 56), (6063 200 60), (10236 1750 56)"),
    ("bklan6", "19.9 MB", "4 spots", "(11580 -2736 56), (-4200 -10380 56), (5304 -15228 58), (564 -571 56)"),
    ("soicowboy_bkk", "10.4 MB", "4 spots", "(118 -1141 56), (4252 -1417 56), (7716 -1417 56), (10098 -1417 60)"),
    ("morrorock", "6.6 MB", "4 spots", "(-1102 3020 140), (-787 -8300 140), (-3600 3980 130), (-5500 -11480 130)"),
]

WEAPONS = [
    (1, "Rocket Launcher", "TW_RL", "progs/v_rock2.mdl"),
    (2, "Grenade Launcher", "TW_GL", "progs/v_rock.mdl"),
    (3, "DN3D Shotgun", "TW_SSG", "progs/v_shot2.mdl"),
    (4, "Laser Cannon", "TW_LASER", "progs/v_laserg.mdl"),
    (5, "Thunderbolt", "TW_LG", "progs/v_light.mdl"),
    (6, "Mega Man", "TW_MEGAMAN", "progs/v_megaman.md3"),
    (7, "Milky Gun", "TW_MILKY", "progs/v_milky.md3"),
    (8, "M4A1 Carbine", "TW_M4", "progs/v_m4.md3"),
    (9, "M1 Garand", "TW_GARAND", "progs/v_garand.md3"),
    (10, "Wheelman Cannon", "TW_WCANNON", "progs/v_wewcannon.md3"),
    (11, "Dookie Bazooka", "TW_DOOKIE", "progs/v_dookie.md3"),
    (12, "Pickle Surprise", "TW_PICKLE", "progs/v_pickle.md3"),
    (13, "Green Jar", "TW_GREENJAR", "progs/v_greenjar.md3"),
    (14, "NetSend Floppy", "TW_NETSEND", "progs/v_netsend.md3"),
    (15, "Pocket Kyle", "TW_KYLE", "progs/v_kyle.md3"),
    (16, "Cyrax Net", "TW_CYRAX", "progs/v_cyrax.md3"),
]

CHANGELOG = [
    ("NEW", "source/mm_tools/triple_wheeled/build_triple_wheeled_pk3.py", "Reproducible pk3 builder: aligns 4 q15 p_rock2 rocket launchers (top pair rolled 180 deg) + twin torus rings + octa core + 16-frame glow shell, shaders, pickup & wearoff WAVs."),
    ("NEW", "source/qc_combat_decomp/triple_wheeled_defs.qc", "Cvars (bm_triple_dur=15, bm_triple_delay=0.25, bm_triple_spawn=1), 16-weapon enum, player fields, clientstats 152..157 prototypes."),
    ("NEW", "source/qc_combat_decomp/triple_wheeled.qc", "Pickup entity, 1st-person 3 extra viewmodels (BL upright, TR/TL upside down), 3rd-person halo, 16-weapon sequential firing, 28 big-map spawns, impulses 158/159/160."),
    ("MOD", "source/qc_combat_decomp/progs.src", "Compiled triple_wheeled_defs.qc and triple_wheeled.qc into progs.dat."),
    ("MOD", "source/qc_combat_decomp/world.qc & bm_match.qc", "Precache models/sounds on map load, register clientstats 152..157, trigger TW_MapSpawn() at match start, reset stats in observer mode."),
    ("MOD", "source/qc_combat_decomp/weapons.qc & client.qc", "Hooked TW_Frame(), TW_Impulse(), TW_Reset() on death/intermission/disconnect, and TW_TriggerSequence() on W_Attack paths."),
    ("MOD", "source/qc_combat_decomp/{megaman,milky,m4,garand,wcannon,dookie,greenjar,pickle,netsend,kyle,cyrax,robhead}.qc", "Connected custom FunGun and charge/throw weapon release points to TW_TriggerSequence()."),
    ("MOD", "source/qc_combat_decomp/csqc/bm_hud.qc & csqc.main.qc", "Added TW_DrawHUD(w, h) rendering the countdown banner and live 2x2 weapon status grid."),
    ("MOD", ".github/workflows/build-zip.yml & source/mm_tools/assemble_local_package.sh", "Added cached CI and local overlay build + package verification for zz_triple_wheeled.pk3."),
]


def extract_mesh_payload(pk3_path: Path, tmp_dir: Path) -> dict:
    with zipfile.ZipFile(pk3_path) as z:
        md3_bytes = z.read("progs/triple_wheeled.md3")
    tmp_md3 = tmp_dir / "triple_wheeled_tmp.md3"
    tmp_md3.write_bytes(md3_bytes)
    model = md3lib.read(tmp_md3)
    tmp_md3.unlink(missing_ok=True)

    surfs = []
    for s in model["surfaces"]:
        verts0, _ = s["frames"][0]
        flat_xyz = []
        for v in verts0:
            flat_xyz.extend([round(v[0], 2), round(v[1], 2), round(v[2], 2)])
        flat_tris = []
        for a, b, c in s["tris"]:
            flat_tris.extend([int(a), int(b), int(c)])
        surfs.append({
            "name": s["name"],
            "n_verts": len(verts0),
            "n_tris": len(s["tris"]),
            "xyz": flat_xyz,
            "tris": flat_tris,
        })
    return {"frames": model["nframes"], "surfaces": surfs}


def img_to_data_uri(path: Path, max_w: int = 1280, quality: int = 88) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = int(round(im.height * (max_w / im.width)))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pk3", required=True)
    ap.add_argument("--pickup-shot", required=True)
    ap.add_argument("--halo-shot", required=True)
    ap.add_argument("--random-shot", required=True)
    ap.add_argument("--quad-shot", required=True)
    ap.add_argument("--fire-shot", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    mesh_json = json.dumps(extract_mesh_payload(Path(args.pk3), out_path.parent), separators=(",", ":"))
    shot_paths = {
        "pickup": Path(args.pickup_shot),
        "halo": Path(args.halo_shot),
        "random_quad": Path(args.random_shot),
        "quad_rl": Path(args.quad_shot),
        "quad_fire": Path(args.fire_shot),
    }

    gallery_cards = []
    for key, title, desc in SHOT_SPECS:
        uri = img_to_data_uri(shot_paths[key])
        gallery_cards.append(
            f'<article class="shot-card" onclick="openModal(this)">'
            f'<img src="{uri}" alt="{html.escape(title)}" loading="lazy" />'
            f'<div class="shot-meta"><h3>{title}</h3><p>{desc}</p></div>'
            f'</article>'
        )

    map_rows = "\n".join(
        f"<tr><td><code>{html.escape(m)}</code></td><td>{html.escape(sz)}</td><td>{html.escape(cnt)}</td><td><code>{html.escape(coords)}</code></td></tr>"
        for m, sz, cnt, coords in BIG_MAPS
    )
    wep_chips = "\n".join(
        f'<div class="wep-chip"><span class="wid">#{wid}</span><strong>{html.escape(name)}</strong><code>{html.escape(sym)}</code><small>{html.escape(mdl)}</small></div>'
        for wid, name, sym, mdl in WEAPONS
    )
    changelog_rows = "\n".join(
        f'<tr><td><span class="badge {tag.lower()}">{tag}</span></td><td><code>{html.escape(fpath)}</code></td><td>{html.escape(notes)}</td></tr>'
        for tag, fpath, notes in CHANGELOG
    )
    weapons_js = json.dumps([name.upper() for _, name, _, _ in WEAPONS])

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>B. Triple Wheeled — BakersfieldQuake Power-Up Showcase</title>
<style>
  :root {{
    --bg: #0c0e14;
    --panel: #141823;
    --panel2: #1a2030;
    --border: #2a334a;
    --gold: #ffaa2b;
    --cyan: #4cd4ff;
    --green: #45e07d;
    --red: #ff584d;
    --text: #e8ecf5;
    --muted: #98a4be;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: radial-gradient(circle at top center, #1b2136 0%, var(--bg) 55%);
    color: var(--text);
    line-height: 1.5;
  }}
  a {{ color: var(--cyan); }}
  code {{
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    background: rgba(255,255,255,0.07);
    padding: 0.12em 0.38em;
    border-radius: 4px;
    font-size: 0.9em;
    color: #ffd37a;
  }}
  .wrap {{ max-width: 1240px; margin: 0 auto; padding: 28px 18px 64px; }}
  header.hero {{
    background: linear-gradient(135deg, rgba(255,170,43,0.14), rgba(76,212,255,0.08));
    border: 1px solid rgba(255,170,43,0.38);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 24px;
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 24px;
    align-items: center;
  }}
  @media (max-width: 860px) {{ header.hero {{ grid-template-columns: 1fr; }} }}
  .eyebrow {{
    display: inline-block;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
    background: rgba(255,170,43,0.12);
    border: 1px solid rgba(255,170,43,0.35);
    padding: 4px 10px;
    border-radius: 999px;
    margin-bottom: 10px;
  }}
  h1 {{ margin: 0 0 10px; font-size: clamp(28px, 4vw, 44px); line-height: 1.1; }}
  .lead {{ color: var(--muted); font-size: 16px; margin: 0 0 18px; }}
  .stats-row {{ display: flex; flex-wrap: wrap; gap: 10px; }}
  .stat-pill {{
    background: rgba(12,14,20,0.75);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
  }}
  .stat-pill b {{ color: var(--gold); font-size: 15px; display: block; }}
  .viewer-box {{
    background: #080a0f;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px;
  }}
  #md3Canvas {{ width: 100%; height: 290px; display: block; border-radius: 8px; cursor: grab; }}
  #md3Canvas:active {{ cursor: grabbing; }}
  .viewer-ctrls {{
    display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center;
    padding-top: 8px; font-size: 12px; color: var(--muted);
  }}
  button {{
    background: var(--panel2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }}
  button:hover {{ border-color: var(--gold); color: var(--gold); }}
  button.primary {{ background: linear-gradient(135deg, #ff9914, #ff5e14); color: #120c05; border-color: #ffb84d; }}
  button.primary:hover {{ filter: brightness(1.08); color: #000; }}

  section {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 22px;
  }}
  section h2 {{ margin: 0 0 14px; font-size: 22px; color: var(--gold); }}

  /* Interactive 4-gun HUD simulator */
  .sim-wrap {{ display: grid; grid-template-columns: 1fr 340px; gap: 20px; align-items: center; }}
  @media (max-width: 900px) {{ .sim-wrap {{ grid-template-columns: 1fr; }} }}
  .hud-stage {{
    background: linear-gradient(180deg, #1b2842 0%, #24334d 45%, #2b2722 46%, #3f3830 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    min-height: 290px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .hud-grid-banner {{
    max-width: 480px;
    width: 100%;
    margin: 0 auto;
    background: rgba(10,11,16,0.86);
    border-top: 2px solid var(--gold);
    border-bottom: 2px solid var(--gold);
    padding: 8px;
    font-family: ui-monospace, Consolas, monospace;
  }}
  .hud-hdr {{ text-align: center; font-weight: 700; font-size: 14px; color: var(--gold); margin-bottom: 8px; }}
  .hud-2x2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
  .hud-cell {{
    background: rgba(24,28,40,0.85);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 7px 9px;
    border-radius: 5px;
    font-size: 12px;
    transition: background 0.08s, transform 0.08s;
  }}
  .hud-cell.firing {{ background: rgba(255,118,16,0.72); border-color: #ffd084; transform: scale(1.02); }}
  .hud-cell.queued {{ background: rgba(54,120,64,0.65); border-color: var(--green); }}
  .corner-stage {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 18px;
  }}
  .corner-gun {{
    background: rgba(8,10,15,0.68);
    border: 1px dashed rgba(255,255,255,0.16);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 13px;
    display: flex; justify-content: space-between; align-items: center;
    transition: transform 0.12s, border-color 0.12s;
  }}
  .corner-gun.inv {{ transform: rotate(180deg); }}
  .corner-gun.inv span {{ transform: rotate(180deg); display: inline-block; }}
  .corner-gun.kick {{ border-color: var(--gold); box-shadow: 0 0 18px rgba(255,155,30,0.45); }}
  .sim-ctrls {{ display: flex; flex-direction: column; gap: 12px; }}
  .sim-ctrls label {{ font-size: 13px; color: var(--muted); display: flex; justify-content: space-between; }}

  /* Gallery */
  .shot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; }}
  .shot-card {{
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    cursor: zoom-in;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .shot-card:hover {{ transform: translateY(-2px); border-color: var(--cyan); }}
  .shot-card img {{ width: 100%; height: auto; display: block; }}
  .shot-meta {{ padding: 14px; }}
  .shot-meta h3 {{ margin: 0 0 6px; font-size: 16px; }}
  .shot-meta p {{ margin: 0; font-size: 13px; color: var(--muted); }}

  /* Weapon grid & tables */
  .wep-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 10px; }}
  .wep-chip {{
    background: var(--panel2); border: 1px solid var(--border); border-radius: 9px; padding: 10px;
    display: flex; flex-direction: column; gap: 3px;
  }}
  .wep-chip .wid {{ font-size: 11px; color: var(--cyan); font-weight: 700; }}
  .wep-chip small {{ color: var(--muted); font-size: 11px; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ color: var(--cyan); font-weight: 700; background: rgba(255,255,255,0.03); }}
  .badge {{ font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px; }}
  .badge.new {{ background: rgba(69,224,125,0.16); color: var(--green); border: 1px solid rgba(69,224,125,0.4); }}
  .badge.mod {{ background: rgba(76,212,255,0.14); color: var(--cyan); border: 1px solid rgba(76,224,255,0.35); }}

  #modal {{
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.88); z-index: 999;
    align-items: center; justify-content: center; padding: 24px; cursor: zoom-out;
  }}
  #modal.open {{ display: flex; }}
  #modal img {{ max-width: 96vw; max-height: 92vh; border-radius: 10px; border: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div>
      <span class="eyebrow">BakersfieldQuake Power-Up &bull; Commit a29e809a</span>
      <h1>B. Triple Wheeled</h1>
      <p class="lead">
        Pick up the spinning, glowing 4-Rocket-Launcher bundle to simultaneously hold <b>4 weapons</b> across all four corners of your screen &mdash; your main weapon bottom-right, a random gun bottom-left, and two <b>upside-down</b> random weapons hanging from the top corners &mdash; firing all four in rapid succession on every trigger pull.
      </p>
      <div class="stats-row">
        <div class="stat-pill"><b>4 Guns</b>Simultaneous quad-wield</div>
        <div class="stat-pill"><b>0.25s</b>Sequential fire delay</div>
        <div class="stat-pill"><b>15s</b>Power-up duration</div>
        <div class="stat-pill"><b>28 Spawns</b>4&times; on 7 big maps</div>
      </div>
    </div>
    <div class="viewer-box">
      <canvas id="md3Canvas" width="540" height="320"></canvas>
      <div class="viewer-ctrls">
        <span id="meshStats">Loading <code>progs/triple_wheeled.md3</code>...</span>
        <div>
          <button type="button" onclick="toggleSpin()">Spin</button>
          <button type="button" onclick="toggleRings()">Rings</button>
        </div>
      </div>
    </div>
  </header>

  <section>
    <h2>Interactive Quad-Wield Cascade Simulator</h2>
    <div class="sim-wrap">
      <div class="hud-stage">
        <div class="hud-grid-banner">
          <div class="hud-hdr" id="simHdr">B. TRIPLE WHEELED &nbsp; [15.0s] &nbsp; <span style="color:var(--green)">(4 GUNS!)</span></div>
          <div class="hud-2x2">
            <div class="hud-cell" id="cell3"><span style="color:var(--cyan)">[TL INV]</span> <b id="lbl3">M4A1 CARBINE</b></div>
            <div class="hud-cell" id="cell2"><span style="color:var(--cyan)">[TR INV]</span> <b id="lbl2">CYRAX NET</b></div>
            <div class="hud-cell" id="cell1"><span style="color:var(--cyan)">[BL]</span> <b id="lbl1">PICKLE SURPRISE</b></div>
            <div class="hud-cell" id="cell0"><span style="color:var(--cyan)">[MAIN]</span> <b id="lbl0">ROCKET LAUNCHER</b></div>
          </div>
        </div>
        <div class="corner-stage">
          <div class="corner-gun inv" id="cg3"><span>Top-Left (180&deg;): <b id="cg3t">M4A1 CARBINE</b></span></div>
          <div class="corner-gun inv" id="cg2"><span>Top-Right (180&deg;): <b id="cg2t">CYRAX NET</b></span></div>
          <div class="corner-gun" id="cg1"><span>Bot-Left: <b id="cg1t">PICKLE SURPRISE</b></span></div>
          <div class="corner-gun" id="cg0"><span>Bot-Right (Main): <b id="cg0t">ROCKET LAUNCHER</b></span></div>
        </div>
      </div>
      <div class="sim-ctrls">
        <button class="primary" type="button" onclick="triggerCascade()">FIRE ALL 4 IN SEQUENCE!</button>
        <button type="button" onclick="rollRandom()">Roll Random 4 Guns (impulse 159)</button>
        <button type="button" onclick="setQuadRL()">4&times; Rocket Launcher Mode (impulse 160)</button>
        <label><span>Sequence Delay (<code>bm_triple_delay</code>)</span><b id="delayVal">0.25s</b></label>
        <input id="delaySlider" type="range" min="0.15" max="1.0" step="0.05" value="0.25" oninput="delayVal.textContent=Number(this.value).toFixed(2)+'s'" />
        <p style="font-size:12px;color:var(--muted);margin:0;">
          In game: hold any weapon and pull M1. Slot 0 fires immediately, then Slots 1 &rarr; 2 &rarr; 3 fire sequentially every <code>bm_triple_delay</code> seconds.
        </p>
      </div>
    </div>
  </section>

  <section>
    <h2>In-Game Zircon Screenshots</h2>
    <div class="shot-grid">
      {"".join(gallery_cards)}
    </div>
  </section>

  <section>
    <h2>16-Weapon Random Roll Pool</h2>
    <p style="color:var(--muted);margin-top:0;">Slots 1, 2, and 3 roll independently from all 16 precached core &amp; FunGun weapons (always available regardless of map placement):</p>
    <div class="wep-grid">
      {wep_chips}
    </div>
  </section>

  <section>
    <h2>Big-Map Placements (28 Auto-Spawned Pickups)</h2>
    <p style="color:var(--muted);margin-top:0;">Placed via <code>TW_MapSpawn()</code> at street/plaza floor coordinates verified in dedicated Zircon across all 7 shipped maps:</p>
    <table>
      <thead><tr><th>Map</th><th>BSP Size</th><th>Count</th><th>World Coordinates (<code>x y z</code>)</th></tr></thead>
      <tbody>{map_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>What Changed &mdash; Commit <code>a29e809a</code> (24 Files)</h2>
    <table>
      <thead><tr><th>Type</th><th>File</th><th>Summary</th></tr></thead>
      <tbody>{changelog_rows}</tbody>
    </table>
  </section>
</div>

<div id="modal" onclick="this.classList.remove('open')"><img id="modalImg" src="" alt="" /></div>

<script>
// ---- Modal lightbox ----
function openModal(card) {{
  const img = card.querySelector("img");
  document.getElementById("modalImg").src = img.src;
  document.getElementById("modal").classList.add("open");
}}

// ---- Embedded progs/triple_wheeled.md3 3D turntable ----
const MD3 = {mesh_json};
(function() {{
  const cv = document.getElementById("md3Canvas");
  const ctx = cv.getContext("2d");
  let yaw = 0.65, pitch = 0.35, spinning = true, showRings = true, dragging = false, lx = 0, ly = 0;

  let totalV = 0, totalT = 0;
  for (const s of MD3.surfaces) {{ totalV += s.n_verts; totalT += s.n_tris; }}
  document.getElementById("meshStats").textContent =
    MD3.surfaces.length + " surfaces • " + totalV + " verts • " + totalT + " tris • " + MD3.frames + " glow frames";

  cv.addEventListener("pointerdown", e => {{ dragging = true; lx = e.clientX; ly = e.clientY; cv.setPointerCapture(e.pointerId); }});
  cv.addEventListener("pointerup", () => dragging = false);
  cv.addEventListener("pointermove", e => {{
    if (!dragging) return;
    yaw += (e.clientX - lx) * 0.012;
    pitch = Math.max(-1.2, Math.min(1.2, pitch + (e.clientY - ly) * 0.012));
    lx = e.clientX; ly = e.clientY;
  }});

  window.toggleSpin = () => spinning = !spinning;
  window.toggleRings = () => showRings = !showRings;

  const palette = {{
    "rockets_quad": [205, 165, 110],
    "halo_rings": [85, 225, 255],
    "glow_core": [255, 215, 70],
    "glow_shell": [255, 130, 40],
  }};

  function frame(ts) {{
    if (spinning && !dragging) yaw += 0.018;
    const w = cv.width, h = cv.height;
    ctx.fillStyle = "#080a0f";
    ctx.fillRect(0, 0, w, h);

    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    const pulse = 0.65 + 0.35 * Math.sin(ts * 0.008);
    const drawList = [];

    for (const s of MD3.surfaces) {{
      if (!showRings && (s.name === "halo_rings" || s.name === "glow_shell")) continue;
      if (s.name === "glow_shell") continue;
      const pts = [];
      const xyz = s.xyz;
      for (let i = 0; i < xyz.length; i += 3) {{
        const x0 = xyz[i], y0 = xyz[i+1], z0 = xyz[i+2];
        const x1 = x0 * cy - y0 * sy;
        const y1 = x0 * sy + y0 * cy;
        const z2 = z0 * cp - x1 * sp;
        const d = x1 * cp + z0 * sp + 88;
        const sc = 430 / Math.max(20, d);
        pts.push([w * 0.5 + y1 * sc, h * 0.5 - z2 * sc, d]);
      }}
      const rgb = palette[s.name] || [200, 200, 200];
      const tris = s.tris;
      const stride = s.n_tris > 1200 ? 6 : 3;
      for (let i = 0; i < tris.length; i += stride) {{
        const a = pts[tris[i]], b = pts[tris[i+1]], c = pts[tris[i+2]];
        const depth = (a[2] + b[2] + c[2]) / 3;
        const shade = s.name === "rockets_quad" ? Math.max(0.35, Math.min(1.0, 1.15 - depth * 0.006)) : pulse;
        drawList.push([depth, a[0], a[1], b[0], b[1], c[0], c[1], rgb, shade, s.name]);
      }}
    }}
    drawList.sort((u, v) => v[0] - u[0]);
    for (const t of drawList) {{
      const r = Math.round(t[7][0] * t[8]), g = Math.round(t[7][1] * t[8]), b = Math.round(t[7][2] * t[8]);
      ctx.beginPath();
      ctx.moveTo(t[1], t[2]); ctx.lineTo(t[3], t[4]); ctx.lineTo(t[5], t[6]);
      ctx.closePath();
      ctx.fillStyle = `rgb(${{r}},${{g}},${{b}})`;
      ctx.fill();
      if (t[9] === "halo_rings") {{
        ctx.strokeStyle = "rgba(180,245,255,0.45)";
        ctx.stroke();
      }}
    }}
    requestAnimationFrame(frame);
  }}
  requestAnimationFrame(frame);
}})();

// ---- Quad-Wield Cascade Simulator ----
const WEPS = {weapons_js};
let slots = ["ROCKET LAUNCHER", "PICKLE SURPRISE", "CYRAX NET", "M4A1 CARBINE"];
let audioCtx = null;

function beep(freq) {{
  try {{
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = "sawtooth"; o.frequency.value = freq;
    g.gain.setValueAtTime(0.08, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.14);
    o.connect(g); g.connect(audioCtx.destination);
    o.start(); o.stop(audioCtx.currentTime + 0.15);
  }} catch (e) {{}}
}}

function renderSlots(activeIdx, queuedIdx) {{
  for (let i = 0; i < 4; i++) {{
    document.getElementById("lbl" + i).textContent = slots[i];
    document.getElementById("cg" + i + "t").textContent = slots[i];
    const cell = document.getElementById("cell" + i);
    const cg = document.getElementById("cg" + i);
    cell.classList.toggle("firing", i === activeIdx);
    cell.classList.toggle("queued", i === queuedIdx);
    cg.classList.toggle("kick", i === activeIdx);
  }}
}}

function rollRandom() {{
  slots = [
    WEPS[Math.floor(Math.random() * WEPS.length)],
    WEPS[Math.floor(Math.random() * WEPS.length)],
    WEPS[Math.floor(Math.random() * WEPS.length)],
    WEPS[Math.floor(Math.random() * WEPS.length)],
  ];
  renderSlots(-1, -1);
}}

function setQuadRL() {{
  slots = ["ROCKET LAUNCHER", "ROCKET LAUNCHER", "ROCKET LAUNCHER", "ROCKET LAUNCHER"];
  renderSlots(-1, -1);
}}

let simTimers = [];
function triggerCascade() {{
  simTimers.forEach(clearTimeout);
  simTimers = [];
  const d = Number(document.getElementById("delaySlider").value) * 1000;
  const freqs = [240, 310, 390, 480];
  [0, 1, 2, 3].forEach(s => {{
    simTimers.push(setTimeout(() => {{
      renderSlots(s, s < 3 ? s + 1 : -1);
      beep(freqs[s]);
    }}, s * d));
  }});
  simTimers.push(setTimeout(() => renderSlots(-1, -1), 4 * d + 120));
}}
renderSlots(-1, -1);
</script>
</body>
</html>
"""
    out_path.write_text(page, encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
