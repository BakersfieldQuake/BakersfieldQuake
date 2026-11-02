r"""Builds the 100% self-contained single-file HTML showcase page specifically highlighting
the updated LAN party areas in Larry's Warehouse (118/120 & Unit 130A) and ORCOM Connect:
  G:\Quake\Combat\BakersfieldQuake\lan_areas_showcase.html

Zero external dependencies: embeds all 28 MD3 models (17 LAN props + 11 explosion shrapnel gibs)
in a gzipped binary arena, full-range sRGB diffuse & UV glow atlases, all 49 CRT screen frames,
all 5 synthesized explosion WAVs, and 11 high-res venue & DarkPlaces explosion screenshots.
"""
import base64
import gzip
import io
import json
import os
import re
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGED_PROGS = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\progs"
PROGS_BKLAN = os.path.join(MOD, "progs", "bklan")
SOUND_LAN = os.path.join(MOD, "sound", "lan")
SHOTS_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\2a50ab99-03ff-45b6-a492-9f0490f21586\scratch\lan_shots"
NEW_LAN_SHOTS_DIR = os.path.join(HERE, "out", "lan_area_shots")
OUT_HTML = os.path.join(MOD, "lan_areas_showcase.html")

sys.path.insert(0, HERE)
import build_lan_showcase_html as base  # noqa: E402
import lan_models  # noqa: E402
import lan_screens  # noqa: E402


def parse_bsp_zones(bsp_path: str):
    d = open(bsp_path, "rb").read()
    eo, en = struct.unpack("<2i", d[4:12])
    ents = d[eo:eo + en].decode("latin1")
    zones = {
        "wh_se": {"monitor": 0, "pc": 0, "chair": 0, "table": 0, "total": 0},
        "wh_north": {"monitor": 0, "pc": 0, "chair": 0, "table": 0, "total": 0},
        "u130a": {"monitor": 0, "pc": 0, "chair": 0, "table": 0, "total": 0},
        "u120a": {"monitor": 0, "pc": 0, "chair": 0, "table": 0, "total": 0},
        "orcom": {"monitor": 0, "pc": 0, "chair": 0, "table": 0, "total": 0},
    }
    by_model = {}
    for m in re.finditer(r"\{([^}]*)\}", ents):
        kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1)))
        cn = kv.get("classname", "")
        if not cn.startswith("misc_lan_"):
            continue
        cat = cn.replace("misc_lan_", "")
        ox, oy, _ = [float(v) for v in kv.get("origin", "0 0 0").split()]
        fx, fy = ox / 12.0 - 110.0, oy / 12.0 + 225.0
        if fx < -120 and fy < 110:
            zk = "wh_se"
        elif fx < -120 and fy >= 110:
            zk = "wh_north"
        elif -120 <= fx < -20 and fy > 110:
            zk = "u130a"
        elif fx > 250 and fy > 200:
            zk = "orcom"
        else:
            zk = "u120a"
        zones[zk][cat] = zones[zk].get(cat, 0) + 1
        zones[zk]["total"] += 1

        try:
            var_id = int(float(kv.get("cnt", "1")))
        except ValueError:
            var_id = 1
        if cat == "monitor":
            key = f"lan_mon{max(1, min(4, var_id))}"
        elif cat == "pc":
            key = f"lan_pc{max(1, min(4, var_id))}"
        elif cat == "chair":
            key = f"lan_chair{max(1, min(4, var_id))}"
        else:
            key = "lan_table4s" if var_id == 5 else f"lan_table{max(1, min(4, var_id))}"
        by_model[key] = by_model.get(key, 0) + 1
    return zones, by_model


VENUE_SHOT_SPECS = [
    ("lan_wh_se_bay.jpg", "warehouse", "Larry's Warehouse (118/120) — SE",
     "SE LAN Party Bay: 16-ft Tournament Island, South Row & Admin Desk",
     "Newly built LAN party zone in the SE bay of Larry's Warehouse (118/120 E 21st St): 4 back-to-back 8-ft tables (10 CRT+PC+chair rigs), South Wall 2-table row flanking the Daniel TV, NE compact server desk (lan_table4s), tabletop Bawls/sodas, and 360° Daniel LAN Station.",
     "warehouse5/?spot=Larry%27s%20Warehouse%3A%20SE%20LAN%20Party%20Bay", "wh_se"),
    ("lan_wh_north_pod.jpg", "warehouse", "Larry's Warehouse (118/120) — North",
     "North Warehouse TV LAN Pod: 8-Player Back-to-Back Island",
     "New 16-ft 4-table tournament island beneath the North Warehouse Daniel TV & CCC! poster, outfitted with 8 mixed ProView/Trinitron/SyncMaster/fishbowl CRTs, Chieftec UV & Bondi towers, and rolling/banquet chairs.",
     "warehouse5/?spot=Larry%27s%20Warehouse%3A%20North%20TV%20LAN%20Pod", "wh_north"),
    ("lan_130a_main.jpg", "u130a", "Larry's Warehouse — Unit 130A",
     "Unit 130A B-LAN 2001 Main Hall & Upgraded Office Rig",
     "Flagship Unit 130A warehouse LAN hall featuring twin 24-ft folding table rows, upgraded office Chieftec UV + Sony Trinitron GameSpy rig, added south-row clan station, refreshment table, QuickCam podium, and Daniel CCC! TV.",
     "warehouse5/?spot=LAN%20hall", "u130a_office"),
    ("lan_130a_back.jpg", "u130a", "Unit 130A — Sky-Mural Back Room",
     "Unit 130A Back Room: Compact 5.8-ft Honey-Oak Corner Desks",
     "Two compact 5.8-ft Honey-Oak computer desks (lan_table4s.md3) tucked against the painted sky mural wall, upgraded with a brushed-silver Lian-Li LCD full-tower, SyncMaster CS 1.5 CRT, classic ATX rig & swivel chairs.",
     "warehouse5/?spot=LAN%20hall", "u130a_back"),
    ("lan_orcom_rows.jpg", "orcom", "ORCOM Connect — Main Banquet Hall",
     "ORCOM Connect Banquet Hall: 394 Destructible 3D LAN Props",
     "Four convention rows lined with authentic burgundy stacking banquet chairs (lan_chair1.md3), 8-ft folding banquet/granite/shop tables, 90+ live animated Quake III / CS 1.5 / Win98 CRTs, Computer Renaissance banner & Daniel TV.",
     "warehouse5/?spot=ORCOM%20CONNECT%20LAN%20PARTY", "orcom_island"),
    ("lan_orcom_counter.jpg", "orcom", "ORCOM Connect — East Check-In",
     "ORCOM Honey-Oak Check-In L-Counter & Tournament Bracket",
     "Replaced the static brush slabs on the East Honey-Oak Check-In L-Counter with 2 explodable 3D tournament registration stations (Sony Trinitron GameSpy + Silver LCD tower, SyncMaster Q3A + UV Chieftec), rolling chairs, and spare banquet chairs.",
     "warehouse5/?spot=ORCOM%3A%20Counter%20and%20whiteboard", "orcom_checkin"),
    ("lan_orcom_server.jpg", "orcom", "ORCOM Connect — West Server Desk",
     "ORCOM West Head-of-Aisle Dedicated Server Station",
     "Added a compact 5.8-ft Honey-Oak server desk (lan_table4s.md3) overlooking the main center aisle with dual GameSpy 3D & Q3A Campgrounds CRTs, UV Chieftec & Silver LCD towers, and cobalt task chair.",
     "warehouse5/?spot=ORCOM%3A%20Dedicated%20Server%20Desk", "orcom_server"),
    ("01_showcase_all.jpg", "dp", "DarkPlaces Engine (impulse 95)",
     "Complete 4×4 Explodable LAN Party Roster in DarkPlaces",
     "All 4 CRT monitors (playing Q3A, CS 1.5, Win98+Winamp, and GameSpy), 4 PC towers, 4 chairs, and 4 banquet/shop tables spawned side-by-side in DarkPlaces.",
     "", "wh_se"),
    ("02_showcase_closeup.jpg", "dp", "DarkPlaces Engine (Close-Up)",
     "Close-Up: Phosphor Bloom, Bawls/Q3A Stickers & UV Chieftec Window",
     "Close-up of q3dm17 Railgun, de_dust2 M4A1 + radar, the matte-black Chieftec Dragon's self-lit UV acrylic window & red top cathode, and BSOD fishbowl CRT.",
     "", "u130a_office"),
    ("03_showcase_explosion.jpg", "dp", "DarkPlaces Engine (impulse 96)",
     "Mid-Detonation: Bouncing 3D Shrapnel & <20 HP Cracked CRT Glass",
     "Live explosion hurling spinning dual-fan brackets, copper CRT deflection yokes, smoked glass shards & keyboard gibs while neighboring CRTs fracture to their cracked tube skin.",
     "", "wh_north"),
    ("07_orcom_chain_blast.jpg", "dp", "DarkPlaces — ORCOM Chain Blast",
     "Rocket Splash Chain-Reaction Across ORCOM Banquet Row",
     "Single rocket setting off adjacent monitors, towers, chairs & banquet tables beneath the Computer Renaissance banner with real-time wall shadows.",
     "warehouse5/?spot=ORCOM%20CONNECT%20LAN%20PARTY", "orcom_island"),
]


def main():
    lan_screens.BRIGHT = 1.0
    packer = base.ArenaPacker()
    shader_to_tex = {}

    for k in range(1, 5):
        shader_to_tex[f"progs/bklan/t_mon{k}"] = packer.add_pil_tex(lan_models._make_monitor_atlas(k), quality=92)
    for k in range(1, 5):
        shader_to_tex[f"progs/bklan/t_pc{k}"] = packer.add_pil_tex(lan_models._make_pc_atlas(k), quality=92)
    shader_to_tex["progs/bklan/scr_pc2uv"] = packer.add_pil_tex(lan_models._make_pc2_glow_tex(), quality=93)
    for k in range(1, 5):
        shader_to_tex[f"progs/bklan/t_chair{k}"] = packer.add_pil_tex(lan_models._make_chair_atlas(k), quality=92)
    for k in range(1, 5):
        shader_to_tex[f"progs/bklan/t_table{k}"] = packer.add_pil_tex(lan_models._make_table_atlas(k), quality=92)

    deb_disk = Image.open(os.path.join(PROGS_BKLAN, "t_lan_deb.png")).convert("RGB")
    deb_arr = np.clip(np.asarray(deb_disk, dtype=np.float32) * (1.0 / 0.48), 0, 255).astype(np.uint8)
    shader_to_tex["progs/bklan/t_lan_deb"] = packer.add_pil_tex(Image.fromarray(deb_arr), quality=92)

    for g_id, _ in base.EXTRA_GIBS:
        stem = g_id.replace("hd_", "")
        for side in ("top", "side"):
            sh = f"progs/hd_{stem}_{side}"
            p = os.path.join(MOD, "progs", f"hd_{stem}_{side}.png")
            if not os.path.isfile(p):
                p = os.path.join(STAGED_PROGS, f"hd_{stem}_{side}.png")
            shader_to_tex[sh] = packer.add_pil_tex(Image.open(p).convert("RGB"), as_png=True)

    seq_generators = {
        "scr_q3a1": lan_screens.make_q3a1_frames,
        "scr_cs1": lan_screens.make_cs1_frames,
        "scr_win98a": lan_screens.make_win98a_frames,
        "scr_q3a2": lan_screens.make_q3a2_frames,
        "scr_cs2": lan_screens.make_cs2_frames,
        "scr_win98b": lan_screens.make_win98b_frames,
    }
    screens_out = []
    for code, skin_idx, fps, title, desc in base.SCREEN_SPECS:
        frames_pil = seq_generators[code]()
        frame_tex_ids = [packer.add_pil_tex(fr, as_png=True, quantize_colors=256) for fr in frames_pil]
        if code == "scr_q3a1":
            shader_to_tex["progs/bklan/scr_q3a1"] = frame_tex_ids[0]
        screens_out.append({
            "code": code, "skin": skin_idx, "fps": fps, "title": title, "desc": desc, "frames": frame_tex_ids,
        })
    dead_tex_id = packer.add_pil_tex(lan_screens.make_dead_screen(), as_png=True, quantize_colors=128)
    screens_out.append({
        "code": "scr_dead", "skin": 6, "fps": 0,
        "title": "Cracked / Imploded CRT Tube (< 20 HP Damaged State)",
        "desc": "Spiderweb fracture lines over dark phosphor glass & exposed copper electron-gun neck when HP < 20.",
        "frames": [dead_tex_id],
    })

    zones5, cnt_bklan5 = parse_bsp_zones(os.path.join(MOD, "maps", "bklan5.bsp"))
    _, cat_bklan = base.count_bsp_lan_entities(os.path.join(MOD, "maps", "bklan.bsp"))
    _, cat_orcom = base.count_bsp_lan_entities(os.path.join(MOD, "maps", "orcom.bsp"))

    models_out = []
    for key, title, cat, hp, dmg, desc in base.PROP_SPECS:
        info = base.load_md3_into_packer(os.path.join(PROGS_BKLAN, key + ".md3"), packer, shader_to_tex)
        info.update({
            "id": key, "path": f"progs/bklan/{key}.md3", "title": title, "cat": cat,
            "hp": hp, "dmg": dmg, "desc": desc, "cnt4": cnt_bklan5.get(key, 0),
        })
        models_out.append(info)

    gibs_out = []
    for key, title in base.EXTRA_GIBS:
        md3_p = os.path.join(MOD, "progs", key + ".md3")
        if not os.path.isfile(md3_p):
            md3_p = os.path.join(STAGED_PROGS, key + ".md3")
        info = base.load_md3_into_packer(md3_p, packer, shader_to_tex)
        info.update({
            "id": key, "path": f"progs/{key}.md3", "title": title, "cat": "debris", "hp": 0, "dmg": 0,
            "desc": "Secondary hardware shrapnel gib launched alongside custom LAN debris during explosions.",
            "cnt4": 0,
        })
        gibs_out.append(info)

    gz_arena = gzip.compress(bytes(packer.buf), compresslevel=9)

    sounds_out = []
    for sid, rel_p, title, desc in base.SOUND_SPECS:
        wav_p = os.path.join(SOUND_LAN, sid + ".wav")
        sounds_out.append({
            "id": sid, "path": rel_p, "title": title, "desc": desc,
            "kb": round(os.path.getsize(wav_p) / 1024.0, 1), "uri": base.wav_to_uri(wav_p),
        })

    shots_out = []
    for fn, ztag, loc, title, desc, walk_url, rig_preset in VENUE_SHOT_SPECS:
        sp = os.path.join(NEW_LAN_SHOTS_DIR, fn)
        if not os.path.isfile(sp):
            sp = os.path.join(SHOTS_DIR, fn)
        assert os.path.isfile(sp), f"Missing screenshot: {sp}"
        shots_out.append({
            "zone": ztag, "loc": loc, "title": title, "desc": desc,
            "walkUrl": walk_url, "preset": rig_preset,
            "uri": base.file_to_jpeg_uri(sp, max_w=1240, max_h=720, quality=86),
        })

    payload = {
        "textures": packer.textures,
        "models": models_out,
        "extraGibs": gibs_out,
        "screens": screens_out,
        "sounds": sounds_out,
        "shots": shots_out,
        "zones5": zones5,
        "totals": {
            "bklan5": sum(z["total"] for z in zones5.values()),
            "bklan": sum(cat_bklan.values()),
            "orcom": sum(cat_orcom.values()),
        },
        "binGz": base64.b64encode(gz_arena).decode("ascii"),
    }

    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", json.dumps(payload, separators=(",", ":")))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024 * 1024):.2f} MB) | "
          f"bklan5={payload['totals']['bklan5']} bklan={payload['totals']['bklan']} orcom={payload['totals']['orcom']}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>Bakersfield Quake — Updated LAN Party Areas: Larry's Warehouse &amp; ORCOM Connect</title>
<style>
:root {
  --bg: #070a12;
  --bg2: #0d1322;
  --card: #11192c;
  --card2: #17223b;
  --line: #26365c;
  --fg: #eef3ff;
  --muted: #95a6cc;
  --cyan: #38e8ff;
  --amber: #ffb638;
  --red: #ff4d5e;
  --green: #49f28a;
  --purple: #9d7bff;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  background: radial-gradient(circle at 18% 0%, #14203d 0%, var(--bg) 52%);
  color: var(--fg);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.5;
  overflow-x: hidden;
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
a { color: var(--cyan); text-decoration: none; }
button, select { font: inherit; color: inherit; cursor: pointer; }
.wrap { max-width: 1440px; margin: 0 auto; }

.hero {
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(180deg, rgba(18,29,56,0.94), rgba(8,12,22,0.97)),
    repeating-linear-gradient(0deg, rgba(56,232,255,0.04) 0 1px, transparent 1px 4px);
  padding: 28px 24px 24px;
}
.eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--cyan); background: rgba(56,232,255,0.1);
  border: 1px solid rgba(56,232,255,0.32);
  padding: 4px 12px; border-radius: 999px; margin-bottom: 12px;
}
.hero-grid { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 18px; }
.hero h1 { font-size: clamp(26px, 3.2vw, 42px); line-height: 1.12; letter-spacing: -0.02em; max-width: 910px; }
.hero h1 span { color: var(--amber); }
.hero p.lead { color: var(--muted); max-width: 860px; margin-top: 8px; font-size: 15px; }
.connect-box {
  background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 12px 16px; display: flex; flex-direction: column; gap: 6px;
}
.connect-lbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
.connect-row { display: flex; align-items: center; gap: 8px; }
.connect-cmd {
  background: #060911; border: 1px solid #223257; padding: 6px 10px;
  border-radius: 7px; color: var(--green); font-size: 13px;
}

.btn {
  background: var(--card2); border: 1px solid var(--line); padding: 7px 12px;
  border-radius: 8px; font-size: 13px; font-weight: 600; transition: 0.15s ease;
  display: inline-flex; align-items: center; gap: 5px;
}
.btn:hover { border-color: var(--cyan); background: #1e2d4f; color: #fff; }
.btn[aria-pressed="true"], .btn.active {
  background: rgba(56,232,255,0.16); border-color: var(--cyan); color: #fff;
}
.btn-boom {
  background: linear-gradient(180deg, #ff5436, #c81d25); border-color: #ff8c66;
  color: #fff; font-weight: 700; box-shadow: 0 0 18px rgba(255,77,62,0.38);
}
.btn-hit { background: linear-gradient(180deg, #ffb02e, #c97308); border-color: #ffd37a; color: #150d00; font-weight: 700; }
.btn-respawn { background: rgba(73,242,138,0.15); border-color: var(--green); color: var(--green); }

.teleport-bar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  margin-top: 16px; padding: 10px 14px;
  background: rgba(13, 21, 39, 0.85); border: 1px solid var(--line); border-radius: 11px;
}
.teleport-bar .lbl { font-size: 12px; font-weight: 700; color: var(--amber); text-transform: uppercase; letter-spacing: 0.06em; margin-right: 4px; }

.stat-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 10px; margin-top: 16px;
}
.stat { background: rgba(17,25,44,0.88); border: 1px solid var(--line); border-radius: 10px; padding: 10px 14px; }
.stat .k { font-size: 22px; font-weight: 800; color: var(--fg); }
.stat .k em { font-style: normal; color: var(--cyan); font-size: 14px; font-weight: 600; }
.stat .l { font-size: 12px; color: var(--muted); }

section { padding: 28px 24px; border-bottom: 1px solid rgba(38,54,92,0.6); }
.sec-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 12px; margin-bottom: 16px; }
.sec-head h2 { font-size: 22px; letter-spacing: -0.01em; }
.sec-head p { color: var(--muted); font-size: 14px; max-width: 820px; }

.filter-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.tab {
  background: #0c1324; border: 1px solid var(--line); border-radius: 999px;
  padding: 5px 12px; font-size: 12.5px; color: var(--muted);
}
.tab.active { background: rgba(56,232,255,0.18); border-color: var(--cyan); color: #fff; font-weight: 650; }

/* Venue Tour Cards */
.shot-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(390px, 1fr)); gap: 16px; }
.shot-card {
  background: var(--card); border: 1px solid var(--line); border-radius: 13px;
  overflow: hidden; display: flex; flex-direction: column; transition: transform 0.16s ease, border-color 0.16s ease;
}
.shot-card:hover { transform: translateY(-2px); border-color: var(--cyan); }
.shot-img { aspect-ratio: 16 / 9; background: #05070c; overflow: hidden; position: relative; cursor: zoom-in; }
.shot-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
.shot-badge {
  position: absolute; top: 9px; left: 9px;
  background: rgba(7,10,18,0.86); border: 1px solid rgba(56,232,255,0.38);
  color: var(--cyan); font-size: 11px; padding: 2px 8px; border-radius: 6px;
}
.shot-body { padding: 13px 15px 15px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.shot-title { font-weight: 700; font-size: 15.5px; }
.shot-desc { font-size: 13px; color: var(--muted); flex: 1; }
.shot-actions { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 6px; }

/* Zone Census Table */
.zone-tbl-wrap { margin-top: 20px; overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
table.zone-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
table.zone-tbl th, table.zone-tbl td { padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(38,54,92,0.55); }
table.zone-tbl th { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--cyan); background: #0c1324; }
table.zone-tbl tr:last-child td { border-bottom: none; font-weight: 700; background: rgba(56,232,255,0.06); }

/* 3D Studio */
.studio { display: grid; grid-template-columns: 350px 1fr; gap: 16px; min-height: 660px; }
@media (max-width: 1024px) { .studio { grid-template-columns: 1fr; } }
.sidebar {
  background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  display: flex; flex-direction: column; overflow: hidden; max-height: 700px;
}
.mode-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 10px; background: #0b101d; border-bottom: 1px solid var(--line); }
.tabs { display: flex; flex-wrap: wrap; gap: 5px; padding: 9px 10px; border-bottom: 1px solid var(--line); }
.prop-list { overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.pcard {
  text-align: left; background: #0d1527; border: 1px solid #1e2d4d;
  border-radius: 10px; padding: 9px 11px; transition: 0.14s ease;
}
.pcard:hover { border-color: #3f5d9c; background: #131e36; }
.pcard.active {
  border-color: var(--cyan); background: linear-gradient(90deg, rgba(56,232,255,0.14), rgba(19,30,54,0.95));
  box-shadow: inset 3px 0 0 var(--cyan);
}
.ptop { display: flex; justify-content: space-between; align-items: center; font-size: 11px; margin-bottom: 3px; }
.ctag { text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em; padding: 1px 6px; border-radius: 4px; font-size: 10px; }
.ctag.monitor { background: rgba(56,232,255,0.16); color: var(--cyan); }
.ctag.pc      { background: rgba(157,123,255,0.2); color: #bfa8ff; }
.ctag.chair   { background: rgba(255,182,56,0.18); color: var(--amber); }
.ctag.table   { background: rgba(73,242,138,0.16); color: var(--green); }
.ctag.debris  { background: rgba(255,77,94,0.18);  color: #ff8590; }
.pname { font-weight: 650; font-size: 13.5px; color: var(--fg); }
.pmeta { font-size: 11.5px; color: var(--muted); margin-top: 2px; }

.rig-panel { padding: 12px; display: none; flex-direction: column; gap: 10px; overflow-y: auto; }
.rig-panel.show { display: flex; }
.rig-field { display: flex; flex-direction: column; gap: 4px; }
.rig-field label { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.rig-field select { background: #0a101e; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; font-size: 13px; color: var(--fg); }

.stage {
  position: relative; background: #060912; border: 1px solid var(--line);
  border-radius: 14px; overflow: hidden; min-height: 700px; display: flex; flex-direction: column; user-select: none;
}
.stage.fullscreen { position: fixed; inset: 12px; z-index: 999; min-height: 0; }
.stage canvas { width: 100%; height: 100%; flex: 1; display: block; cursor: grab; }
.stage.drag canvas { cursor: grabbing; }

.hud-top {
  position: absolute; top: 12px; left: 12px; right: 12px;
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 10px; pointer-events: none;
}
.hud-card {
  background: rgba(8,13,25,0.86); border: 1px solid rgba(56,232,255,0.28);
  border-radius: 11px; padding: 10px 14px; max-width: 530px; pointer-events: auto;
}
.hud-title { font-size: 16px; font-weight: 700; }
.hud-sub { font-size: 12px; color: var(--cyan); margin-top: 1px; }
.hud-desc { font-size: 12.5px; color: var(--muted); margin-top: 5px; line-height: 1.4; }
.hp-wrap { margin-top: 8px; display: flex; align-items: center; gap: 8px; }
.hp-bar { flex: 1; height: 9px; background: #141c2e; border-radius: 999px; overflow: hidden; border: 1px solid #27375a; }
.hp-fill { height: 100%; width: 100%; background: linear-gradient(90deg, var(--green), #88ff66); transition: width 0.16s ease; }
.hud-controls { display: flex; flex-wrap: wrap; gap: 6px; pointer-events: auto; }
.hud-bottom {
  position: absolute; bottom: 12px; left: 12px; right: 12px;
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 10px; pointer-events: none;
}
.chan-bar, .act-bar {
  background: rgba(8,13,25,0.9); border: 1px solid var(--line); border-radius: 10px;
  padding: 6px 8px; display: flex; flex-wrap: wrap; align-items: center; gap: 5px; pointer-events: auto;
}
.chan-lbl { font-size: 10.5px; font-weight: 700; color: var(--muted); text-transform: uppercase; margin-right: 2px; }
.ch-btn { background: #111b31; border: 1px solid #283c68; border-radius: 6px; padding: 4px 7px; font-size: 11px; color: var(--muted); }
.ch-btn.active { background: rgba(56,232,255,0.2); border-color: var(--cyan); color: #fff; font-weight: 700; }

.scr-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.scard { background: var(--card); border: 1px solid var(--line); border-radius: 13px; overflow: hidden; display: flex; flex-direction: column; }
.scard-bezel { background: linear-gradient(180deg, #272d3d, #151924); padding: 14px 16px 10px; border-bottom: 1px solid var(--line); display: flex; flex-direction: column; align-items: center; }
.scard canvas { width: 100%; max-width: 340px; aspect-ratio: 4 / 3; border-radius: 10px; border: 4px solid #0a0c12; image-rendering: pixelated; background: #05070c; }
.scard-led { width: 100%; max-width: 340px; display: flex; justify-content: space-between; align-items: center; margin-top: 7px; font-size: 11px; color: var(--muted); }
.led-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); margin-right: 5px; }
.scard-body { padding: 13px 15px 15px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.scard-title { font-weight: 700; font-size: 15px; }
.scard-desc { font-size: 13px; color: var(--muted); flex: 1; }

.snd-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.snd-card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 13px 15px; display: flex; flex-direction: column; gap: 8px; }
.snd-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.cat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.ccard { background: var(--card); border: 1px solid var(--line); border-radius: 11px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; cursor: pointer; transition: 0.14s ease; }
.ccard:hover { border-color: var(--cyan); background: var(--card2); }

.lightbox { position: fixed; inset: 0; background: rgba(4,7,14,0.92); z-index: 2000; display: none; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }
.lightbox.open { display: flex; }
.lightbox img { max-width: 95vw; max-height: 82vh; border-radius: 10px; border: 1px solid var(--line); }
.lightbox-cap { margin-top: 12px; color: var(--fg); font-size: 14px; text-align: center; max-width: 880px; }
footer { padding: 24px; text-align: center; color: var(--muted); font-size: 13px; }
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <div class="eyebrow mono">● BAKERSFIELD QUAKE · LARRY'S WAREHOUSE (118/120 &amp; 130A) &amp; ORCOM CONNECT LAN UPDATE</div>
    <div class="hero-grid">
      <div>
        <h1>Updated 3D LAN Party Areas — <span>Larry's Warehouse</span> &amp; <span>ORCOM Connect</span></h1>
        <p class="lead">
          Populated Larry's Warehouse SE LAN Bay, North TV LAN Pod, Unit 130A B-LAN 2001 Hall, and ORCOM Connect's Check-In L-Counter &amp; Dedicated Server Desk with
          <strong>569 explodable 3D LAN party models</strong> (4 CRTs playing live Q3A / CS 1.5 / Win98, 4 PC towers, 4 chairs, 5 tables &amp; 11 shrapnel gibs).
        </p>
      </div>
      <div class="connect-box">
        <span class="connect-lbl">Live Dedicated DarkPlaces Server</span>
        <div class="connect-row">
          <code class="connect-cmd mono" id="srv-cmd">connect 72.62.241.93:26000</code>
          <button class="btn" id="btn-copy" type="button">Copy</button>
        </div>
      </div>
    </div>

    <div class="teleport-bar">
      <span class="lbl mono">▶ Live 3D Walk-Around Teleports:</span>
      <a class="btn" href="warehouse5/?spot=Larry%27s%20Warehouse%3A%20SE%20LAN%20Party%20Bay">Larry's SE LAN Bay</a>
      <a class="btn" href="warehouse5/?spot=Larry%27s%20Warehouse%3A%20North%20TV%20LAN%20Pod">North TV LAN Pod</a>
      <a class="btn" href="warehouse5/?spot=LAN%20hall">Unit 130A Hall</a>
      <a class="btn" href="warehouse5/?spot=ORCOM%20CONNECT%20LAN%20PARTY">ORCOM Banquet Hall</a>
      <a class="btn" href="warehouse5/?spot=ORCOM%3A%20Counter%20and%20whiteboard">ORCOM Check-In Counter</a>
      <a class="btn" href="warehouse5/?spot=ORCOM%3A%20Dedicated%20Server%20Desk">ORCOM Server Desk</a>
    </div>

    <div class="stat-strip">
      <div class="stat"><div class="k"><span id="st-total5">569</span> <em>in bklan5</em></div><div class="l">Destructible 3D LAN Props (<span id="st-bklan">495</span> in <span class="mono">bklan</span> · <span id="st-orcom">394</span> in <span class="mono">orcom</span>)</div></div>
      <div class="stat"><div class="k" id="st-wh">79</div><div class="l">Larry's Warehouse 118/120 (SE Bay + North TV Pod)</div></div>
      <div class="stat"><div class="k" id="st-130a">92</div><div class="l">Unit 130A B-LAN Hall &amp; Sky-Mural Back Room</div></div>
      <div class="stat"><div class="k" id="st-orc">394</div><div class="l">ORCOM Banquet Rows, Check-In Counter &amp; Server Desk</div></div>
      <div class="stat"><div class="k">17 <em>+11 MD3s</em></div><div class="l">Unique 3D Furniture/Rig Models + Bouncing Gibs</div></div>
    </div>
  </div>
</header>

<!-- ==================== 1. UPDATED VENUE TOUR & CENSUS ==================== -->
<section id="sec-venues">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>Updated LAN Party Venues Tour &amp; Compiled BSP Census</h2>
        <p>Click any screenshot to zoom, jump directly to that room in the live 3D WebGL map viewer, or load that zone's exact workstation setup into the interactive explosion simulator below.</p>
      </div>
      <div class="filter-tabs" id="venue-tabs">
        <button type="button" class="tab active" data-zone="all">All Views (11)</button>
        <button type="button" class="tab" data-zone="warehouse">Larry's 118/120 (2)</button>
        <button type="button" class="tab" data-zone="u130a">Unit 130A (2)</button>
        <button type="button" class="tab" data-zone="orcom">ORCOM Connect (3)</button>
        <button type="button" class="tab" data-zone="dp">DarkPlaces Blast &amp; Lineup (4)</button>
      </div>
    </div>

    <div class="shot-grid" id="shot-grid"></div>

    <div class="zone-tbl-wrap">
      <table class="zone-tbl">
        <thead>
          <tr>
            <th>LAN Party Area</th>
            <th>CRTs</th>
            <th>PC Towers</th>
            <th>Chairs</th>
            <th>Tables</th>
            <th>Total Props</th>
            <th>Key Additions &amp; Upgrades</th>
          </tr>
        </thead>
        <tbody id="zone-tbody"></tbody>
      </table>
    </div>
  </div>
</section>

<!-- ==================== 2. INTERACTIVE WEBGL2 3D STUDIO ==================== -->
<section id="sec-3d">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>Interactive WebGL2 3D Venue Workstation &amp; Chain-Reaction Simulator</h2>
        <p>Load any venue workstation preset from Larry's Warehouse or ORCOM, flip live 8-frame CRT channels, shoot props to crack the glass (<span class="mono">&lt;20 HP</span>), and press <strong>💥 DETONATE!</strong></p>
      </div>
      <div style="font-size:12.5px;color:var(--muted)" class="mono">Drag: Orbit · Right-Drag/Shift: Pan · Wheel: Zoom · Space: Detonate</div>
    </div>

    <div class="studio">
      <aside class="sidebar">
        <div class="mode-switch">
          <button type="button" class="btn active" id="mode-rig">🖥️ Venue LAN Rig</button>
          <button type="button" class="btn" id="mode-single">🔍 Single MD3 (28)</button>
        </div>

        <div class="rig-panel show" id="rig-pane">
          <div class="rig-field">
            <label>Map Venue Preset</label>
            <select id="rig-preset">
              <option value="wh_se">Larry's 118/120 — SE Bay Tournament Island</option>
              <option value="wh_north">Larry's 118/120 — North Warehouse TV Pod</option>
              <option value="u130a_office">Unit 130A — Office UV Chieftec &amp; Trinitron</option>
              <option value="u130a_back">Unit 130A Back Room — 5.8-ft Honey-Oak Desk</option>
              <option value="orcom_checkin">ORCOM — East Honey-Oak Check-In Counter</option>
              <option value="orcom_server">ORCOM — West Head-of-Aisle Server Desk</option>
              <option value="orcom_island">ORCOM — Banquet Row (Burgundy Chairs)</option>
            </select>
          </div>
          <div class="rig-field">
            <label>Station Layout</label>
            <select id="rig-layout">
              <option value="dual">👥 Dual 2-Player Station (Chain-Reaction!)</option>
              <option value="single">👤 Single 1-Player Workstation</option>
            </select>
          </div>
          <div class="rig-field"><label>LAN Table</label><select id="rig-table"></select></div>
          <div class="rig-field"><label>Seat A — CRT Monitor</label><select id="rig-mon1"></select></div>
          <div class="rig-field"><label>Seat A — PC Tower</label><select id="rig-pc1"></select></div>
          <div class="rig-field"><label>Seat A — Chair</label><select id="rig-chair1"></select></div>
          <div class="rig-field" id="rig-b-wrap1"><label>Seat B — CRT Monitor</label><select id="rig-mon2"></select></div>
          <div class="rig-field" id="rig-b-wrap2"><label>Seat B — Chair</label><select id="rig-chair2"></select></div>
          <button type="button" class="btn" id="btn-randomize">🎲 Randomize Tournament Table</button>
        </div>

        <div id="single-pane" style="display:none;flex-direction:column;flex:1;min-height:0">
          <div class="tabs" id="cat-tabs">
            <button type="button" class="tab active" data-cat="all">All (28)</button>
            <button type="button" class="tab" data-cat="monitor">CRTs (4)</button>
            <button type="button" class="tab" data-cat="pc">PCs (4)</button>
            <button type="button" class="tab" data-cat="chair">Chairs (4)</button>
            <button type="button" class="tab" data-cat="table">Tables (5)</button>
            <button type="button" class="tab" data-cat="debris">Debris (11)</button>
          </div>
          <div class="prop-list" id="prop-list"></div>
        </div>
      </aside>

      <div class="stage" id="stage">
        <canvas id="gl"></canvas>
        <div class="hud-top">
          <div class="hud-card">
            <div class="hud-title" id="hud-title">Loading WebGL2 Arena…</div>
            <div class="hud-sub mono" id="hud-meta"></div>
            <div class="hud-desc" id="hud-desc"></div>
            <div class="hp-wrap" id="hp-wrap">
              <span class="mono" style="font-size:12px;font-weight:700" id="hp-txt">HP 355 / 355</span>
              <div class="hp-bar"><div class="hp-fill" id="hp-fill"></div></div>
            </div>
          </div>
          <div class="hud-controls">
            <button type="button" class="btn" id="btn-prev" title="Previous model ([)">◀</button>
            <button type="button" class="btn" id="btn-next" title="Next model (])">▶</button>
            <button type="button" class="btn" id="btn-spin" aria-pressed="true">⟳ Spin</button>
            <button type="button" class="btn" id="btn-lit">🌙 Dark LAN Hall</button>
            <button type="button" class="btn" id="btn-wire" aria-pressed="false">△ Wire</button>
            <button type="button" class="btn" id="btn-full">⛶ Full</button>
          </div>
        </div>
        <div class="hud-bottom">
          <div class="chan-bar" id="chan-bar">
            <span class="chan-lbl">📺 CRT Screen:</span>
            <button type="button" class="ch-btn active" data-ch="0">Q3A: q3dm17</button>
            <button type="button" class="ch-btn" data-ch="1">CS 1.5: dust2</button>
            <button type="button" class="ch-btn" data-ch="2">Win98 + Winamp</button>
            <button type="button" class="ch-btn" data-ch="3">Q3A: q3dm6</button>
            <button type="button" class="ch-btn" data-ch="4">CS 1.5: AWP</button>
            <button type="button" class="ch-btn" data-ch="5">GameSpy / BSOD</button>
            <button type="button" class="ch-btn" data-ch="6">Cracked</button>
          </div>
          <div class="act-bar">
            <button type="button" class="btn btn-hit" id="btn-hit">🔫 Shoot (-18 HP)</button>
            <button type="button" class="btn btn-boom" id="btn-boom">💥 DETONATE!</button>
            <button type="button" class="btn btn-respawn" id="btn-respawn">♻ Respawn</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ==================== 3. ANIMATED CRT SCREENS ==================== -->
<section id="sec-screens">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>Live Animated CRT Monitor Screens (256×192 · 8-Frame Quake Shaders)</h2>
        <p>Every placed <span class="mono">misc_lan_monitor</span> across Larry's Warehouse and ORCOM cycles one of 6 animated 8-frame skins (<span class="mono">scr_q3a1..scr_win98b</span>) and swaps to <span class="mono">scr_dead</span> below 20 HP.</p>
      </div>
    </div>
    <div class="scr-grid" id="scr-grid"></div>
  </div>
</section>

<!-- ==================== 4. AUDIO & COMPLETE 28-MD3 CATALOG ==================== -->
<section id="sec-audio">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>Synthesized LAN Destruction SFX (<span class="mono">sound/lan/*.wav</span>)</h2>
        <p>Five custom 22.05 kHz PCM WAV effects embedded offline and triggered live when monitors implode, PSUs pop, and banquet tables collapse.</p>
      </div>
    </div>
    <div class="snd-grid" id="snd-grid"></div>
  </div>
</section>

<section id="sec-catalog">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <h2>Complete 28-Model 3D LAN Furniture, Rig &amp; Shrapnel Catalog</h2>
        <p>Click any card to inspect or detonate that individual MD3 mesh in the WebGL2 studio above.</p>
      </div>
    </div>
    <div class="cat-grid" id="cat-grid"></div>
  </div>
</section>

<div class="lightbox" id="lightbox">
  <img id="lb-img" alt="">
  <div class="lightbox-cap" id="lb-cap"></div>
</div>

<footer>
  Bakersfield Quake · Updated LAN Party Areas Showcase · Zero External Dependencies · <span class="mono">connect 72.62.241.93:26000</span>
</footer>

<script>
const DATA = __PAYLOAD_JSON__;
const $ = (id) => document.getElementById(id);

$("st-total5").textContent = DATA.totals.bklan5;
$("st-bklan").textContent = DATA.totals.bklan;
$("st-orcom").textContent = DATA.totals.orcom;
$("st-wh").textContent = DATA.zones5.wh_se.total + DATA.zones5.wh_north.total;
$("st-130a").textContent = DATA.zones5.u130a.total;
$("st-orc").textContent = DATA.zones5.orcom.total;

$("btn-copy").onclick = () => {
  navigator.clipboard?.writeText($("srv-cmd").textContent);
  $("btn-copy").textContent = "Copied!";
  setTimeout(() => ($("btn-copy").textContent = "Copy"), 1600);
};

function openLightbox(uri, cap) {
  $("lb-img").src = uri;
  $("lb-cap").textContent = cap;
  $("lightbox").classList.add("open");
}
$("lightbox").onclick = () => $("lightbox").classList.remove("open");
addEventListener("keydown", (e) => { if (e.key === "Escape") $("lightbox").classList.remove("open"); });

// Populate Zone Census Table
const ZONE_ROWS = [
  ["wh_se", "Larry's Warehouse (118/120) — SE LAN Party Bay", "16-ft 4-table island + South Wall row + NE lan_table4s admin desk beneath Daniel TV"],
  ["wh_north", "Larry's Warehouse (118/120) — North TV LAN Pod", "8-player back-to-back tournament island directly beneath North Warehouse TV"],
  ["u130a", "Larry's Warehouse — Unit 130A Hall & Sky-Mural Back Room", "Twin 24-ft rows + upgraded UV Chieftec office rig + sky-mural lan_table4s corner desks"],
  ["orcom", "ORCOM Connect — Banquet Hall, Check-In & Server Desk", "4 banquet rows + 3D Check-In L-Counter rigs + West Head-of-Aisle lan_table4s server desk"],
  ["u120a", "Unit 120A Shop & Residential Rig", "Shop counter rig + bedroom compact Honey-Oak LAN station"],
];
const zTbody = $("zone-tbody");
let sumM = 0, sumP = 0, sumC = 0, sumT = 0, sumAll = 0;
for (const [zk, label, notes] of ZONE_ROWS) {
  const z = DATA.zones5[zk];
  sumM += z.monitor; sumP += z.pc; sumC += z.chair; sumT += z.table; sumAll += z.total;
  const tr = document.createElement("tr");
  tr.innerHTML = `<td><strong>${label}</strong></td><td class="mono">${z.monitor}</td><td class="mono">${z.pc}</td><td class="mono">${z.chair}</td><td class="mono">${z.table}</td><td class="mono" style="color:var(--cyan);font-weight:700">${z.total}</td><td style="color:var(--muted)">${notes}</td>`;
  zTbody.appendChild(tr);
}
const trTot = document.createElement("tr");
trTot.innerHTML = `<td>Total in <span class="mono">bklan5.bsp</span></td><td class="mono">${sumM}</td><td class="mono">${sumP}</td><td class="mono">${sumC}</td><td class="mono">${sumT}</td><td class="mono" style="color:var(--amber)">${sumAll}</td><td>All destructible with 15s DM respawn &amp; chain-reaction splash</td>`;
zTbody.appendChild(trTot);

// Audio helper
const soundMap = {};
for (const s of DATA.sounds) soundMap[s.id] = s.uri;
function playSfx(id, vol = 0.75) {
  const uri = soundMap[id];
  if (!uri) return;
  try {
    const a = new Audio(uri);
    a.volume = Math.max(0, Math.min(1, vol));
    a.play().catch(() => {});
  } catch (_) {}
}

// Render Venue Tour Cards with Zone Filtering
const shotGrid = $("shot-grid");
let activeZone = "all";
function renderShots() {
  shotGrid.innerHTML = "";
  for (const sh of DATA.shots) {
    if (activeZone !== "all" && sh.zone !== activeZone) continue;
    const el = document.createElement("div");
    el.className = "shot-card";
    el.innerHTML = `
      <div class="shot-img">
        <img src="${sh.uri}" alt="${sh.title}" loading="lazy">
        <span class="shot-badge mono">${sh.loc}</span>
      </div>
      <div class="shot-body">
        <div class="shot-title">${sh.title}</div>
        <div class="shot-desc">${sh.desc}</div>
        <div class="shot-actions">
          ${sh.walkUrl ? `<a class="btn" href="${sh.walkUrl}">▶ Walk Here in 3D</a>` : ""}
          <button type="button" class="btn btn-rig-load">🖥️ Load Rig in 3D Studio</button>
        </div>
      </div>`;
    el.querySelector(".shot-img").onclick = () => openLightbox(sh.uri, `${sh.title} [${sh.loc}] — ${sh.desc}`);
    el.querySelector(".btn-rig-load").onclick = () => {
      window.__applyVenuePreset?.(sh.preset);
      $("sec-3d").scrollIntoView({ behavior: "smooth" });
    };
    shotGrid.appendChild(el);
  }
}
renderShots();
$("venue-tabs").querySelectorAll(".tab").forEach((b) => {
  b.onclick = () => {
    activeZone = b.dataset.zone;
    $("venue-tabs").querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b));
    renderShots();
  };
});

// Soundboard
const sndGrid = $("snd-grid");
for (const s of DATA.sounds) {
  const el = document.createElement("div");
  el.className = "snd-card";
  el.innerHTML = `
    <div class="snd-top">
      <span class="mono" style="font-size:12px;color:var(--cyan)">${s.path}</span>
      <span class="mono" style="font-size:11px;color:var(--muted)">${s.kb} KB</span>
    </div>
    <div style="font-weight:700;font-size:14px">${s.title}</div>
    <div style="font-size:12.5px;color:var(--muted);flex:1">${s.desc}</div>
    <button type="button" class="btn" style="align-self:flex-start">▶ Play WAV</button>`;
  el.querySelector("button").onclick = () => playSfx(s.id, 0.9);
  sndGrid.appendChild(el);
}

// Preload textures
const loadedImages = DATA.textures.map((t) => {
  const im = new Image();
  im.src = t.uri;
  return im;
});

// Animated CRT Screen Cards
const scrGrid = $("scr-grid");
const scrCanvases = [];
DATA.screens.forEach((sc, idx) => {
  const el = document.createElement("div");
  el.className = "scard";
  el.innerHTML = `
    <div class="scard-bezel">
      <canvas width="256" height="192"></canvas>
      <div class="scard-led mono">
        <span><i class="led-dot" style="${sc.skin === 6 ? 'background:#ff4d5e;box-shadow:0 0 6px #ff4d5e' : ''}"></i>skin ${sc.skin} · ${sc.code}</span>
        <span>${sc.fps > 0 ? sc.fps + ' fps · 8 frames' : 'damaged <20 HP'}</span>
      </div>
    </div>
    <div class="scard-body">
      <div class="scard-title">${sc.title}</div>
      <div class="scard-desc">${sc.desc}</div>
      <button type="button" class="btn" style="align-self:flex-start;margin-top:4px">📺 Preview on 3D CRT</button>
    </div>`;
  scrCanvases.push({ ctx: el.querySelector("canvas").getContext("2d"), sc });
  el.querySelector("button").onclick = () => {
    window.__setChannelFromGallery?.(idx);
    $("sec-3d").scrollIntoView({ behavior: "smooth" });
  };
  scrGrid.appendChild(el);
});

function tickScreenCanvases(nowSec) {
  for (const item of scrCanvases) {
    const fids = item.sc.frames;
    const fi = item.sc.fps > 0 ? Math.floor(nowSec * item.sc.fps) % fids.length : 0;
    const im = loadedImages[fids[fi]];
    if (im && im.complete && im.naturalWidth > 0) item.ctx.drawImage(im, 0, 0, 256, 192);
  }
}

const ALL_MODELS = [...DATA.models, ...DATA.extraGibs];
const MODEL_BY_ID = {};
ALL_MODELS.forEach((m, i) => { m.index = i; MODEL_BY_ID[m.id] = m; });

const catGrid = $("cat-grid");
ALL_MODELS.forEach((m, idx) => {
  const dx = m.bmax[0] - m.bmin[0], dy = m.bmax[1] - m.bmin[1], dz = m.bmax[2] - m.bmin[2];
  const el = document.createElement("div");
  el.className = "ccard";
  el.innerHTML = `
    <div class="ptop">
      <span class="ctag ${m.cat}">${m.cat}</span>
      <span class="mono" style="font-size:11px;color:var(--muted)">${m.cnt4 > 0 ? '×' + m.cnt4 + ' in bklan5' : 'dynamic gib'}</span>
    </div>
    <div style="font-weight:700;font-size:14.5px">${m.title}</div>
    <div class="mono" style="font-size:11.5px;color:var(--cyan)">${m.path} · ${m.nt} tris · ${dx.toFixed(0)}×${dy.toFixed(0)}×${dz.toFixed(0)}u</div>
    <div style="font-size:12.5px;color:var(--muted);flex:1">${m.desc}</div>
    <div class="mono" style="font-size:11px;color:var(--amber)">${m.hp > 0 ? `HP: ${m.hp} · Blast: ${m.dmg} dmg · 15s DM respawn` : 'Ballistic bounce shrapnel'}</div>`;
  el.onclick = () => {
    window.__selectSingleProp?.(idx);
    $("sec-3d").scrollIntoView({ behavior: "smooth" });
  };
  catGrid.appendChild(el);
});

async function gunzip(b64) {
  const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const ds = new DecompressionStream("gzip");
  const w = ds.writable.getWriter();
  w.write(bin);
  w.close();
  return await new Response(ds.readable).arrayBuffer();
}

function mat4Persp(out, fovy, aspect, near, far) {
  const f = 1.0 / Math.tan(fovy * 0.5), nf = 1.0 / (near - far);
  out.fill(0);
  out[0] = f / aspect; out[5] = f; out[10] = (far + near) * nf; out[11] = -1; out[14] = 2 * far * near * nf;
  return out;
}
function mat4LookAt(out, eye, ctr, up) {
  let zx = eye[0]-ctr[0], zy = eye[1]-ctr[1], zz = eye[2]-ctr[2];
  let l = Math.hypot(zx, zy, zz) || 1; zx/=l; zy/=l; zz/=l;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  l = Math.hypot(xx, xy, xz) || 1; xx/=l; xy/=l; xz/=l;
  const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
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
  for (let c = 0; c < 4; c++)
    for (let rw = 0; rw < 4; rw++)
      r[c*4+rw] = a[0*4+rw]*b[c*4+0] + a[1*4+rw]*b[c*4+1] + a[2*4+rw]*b[c*4+2] + a[3*4+rw]*b[c*4+3];
  out.set(r);
  return out;
}
function mat3Euler(out, yaw, pitch, roll) {
  const cz = Math.cos(yaw), sz = Math.sin(yaw), cy = Math.cos(pitch), sy = Math.sin(pitch), cx = Math.cos(roll), sx = Math.sin(roll);
  out[0] = cz*cy; out[1] = sz*cy; out[2] = -sy;
  out[3] = cz*sy*sx - sz*cx; out[4] = sz*sy*sx + cz*cx; out[5] = cy*sx;
  out[6] = cz*sy*cx + sz*sx; out[7] = sz*sy*cx - cz*sx; out[8] = cy*cx;
  return out;
}

(async function boot3D() {
  const AB = await gunzip(DATA.binGz);
  const canvas = $("gl");
  canvas.addEventListener("webglcontextlost", (e) => e.preventDefault());
  const gl = canvas.getContext("webgl2", { antialias: true, alpha: false });
  if (!gl || gl.isContextLost()) {
    $("hud-title").textContent = "WebGL2 Unavailable in Browser";
    return;
  }

  function mkProg(vs, fs) {
    const p = gl.createProgram();
    for (const [tp, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(tp);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  const pSky = mkProg(`#version 300 es
    precision highp float; precision highp int;
    layout(location=0) in vec2 aQ; out vec2 vUv;
    void main() { vUv = aQ * 0.5 + 0.5; gl_Position = vec4(aQ, 0.9999, 1.0); }`,
    `#version 300 es
    precision highp float; precision highp int;
    in vec2 vUv; uniform int uLit; uniform float uBlast; out vec4 fragColor;
    void main() {
      vec3 top = uLit == 0 ? vec3(0.04, 0.06, 0.13) : vec3(0.14, 0.19, 0.28);
      vec3 bot = uLit == 0 ? vec3(0.10, 0.12, 0.22) : vec3(0.24, 0.28, 0.36);
      vec3 c = mix(bot, top, smoothstep(0.0, 1.0, vUv.y));
      c += vec3(0.32, 0.14, 0.03) * uBlast * (1.0 - vUv.y * 0.6);
      fragColor = vec4(c, 1.0);
    }`);

  const pGrid = mkProg(`#version 300 es
    precision highp float; precision highp int;
    layout(location=0) in vec2 aQ; uniform mat4 uVP; uniform float uZ; uniform float uRad; out vec2 vP;
    void main() { vP = aQ * uRad; gl_Position = uVP * vec4(vP, uZ, 1.0); }`,
    `#version 300 es
    precision highp float; precision highp int;
    in vec2 vP; uniform float uRad; uniform vec3 uBlastPos; uniform float uBlast; out vec4 fragColor;
    void main() {
      vec2 q = vP / 16.0;
      float chk = mod(floor(q.x) + floor(q.y), 2.0);
      vec2 g = abs(fract(q - 0.5) - 0.5) / fwidth(q);
      float ln = 1.0 - min(min(g.x, g.y), 1.0);
      float fade = 1.0 - smoothstep(uRad * 0.30, uRad * 0.96, length(vP));
      vec3 col = mix(vec3(0.08, 0.11, 0.18), vec3(0.11, 0.15, 0.24), chk) + vec3(0.14, 0.55, 0.72) * ln * 0.22;
      float bd = length(vP - uBlastPos.xy);
      col += vec3(1.0, 0.52, 0.14) * uBlast * exp(-bd * 0.028);
      fragColor = vec4(col, fade * 0.88);
    }`);

  const pMesh = mkProg(`#version 300 es
    precision highp float; precision highp int;
    layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec2 aUv;
    uniform mat4 uVP; uniform mat3 uRot; uniform vec3 uTrans; uniform int uShadow; uniform float uFloorZ;
    out vec3 vPos; out vec3 vNrm; out vec2 vUv;
    void main() {
      vec3 p = uRot * aPos + uTrans; vec3 n = uRot * aNrm;
      if (uShadow == 1) {
        float h = max(0.0, p.z - uFloorZ);
        vec3 sp = vec3(p.x - 0.25 * h, p.y + 0.20 * h, uFloorZ + 0.06);
        vPos = sp; vNrm = vec3(0.0, 0.0, 1.0); vUv = aUv; gl_Position = uVP * vec4(sp, 1.0);
      } else {
        vPos = p; vNrm = n; vUv = aUv; gl_Position = uVP * vec4(p, 1.0);
      }
    }`,
    `#version 300 es
    precision highp float; precision highp int;
    in vec3 vPos; in vec3 vNrm; in vec2 vUv;
    uniform sampler2D uTex; uniform vec3 uEye; uniform int uLit; uniform int uEmissive; uniform int uShadow;
    uniform vec3 uBlastPos; uniform float uBlast; out vec4 fragColor;
    void main() {
      if (uShadow == 1) { fragColor = vec4(0.01, 0.02, 0.05, 0.38); return; }
      vec3 base = texture(uTex, vUv).rgb;
      if (uLit == 2) { fragColor = vec4(base, 1.0); return; }
      if (uEmissive == 1) {
        vec3 c = base * 1.12;
        c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14);
        fragColor = vec4(c, 1.0); return;
      }
      vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
      vec3 V = normalize(uEye - vPos);
      vec3 L1 = normalize(vec3(0.54, -0.42, 0.73));
      vec3 L2 = normalize(vec3(-0.62, 0.55, 0.56));
      vec3 c1 = uLit == 0 ? vec3(0.88, 0.92, 1.12) : vec3(1.18, 1.14, 1.06);
      vec3 c2 = uLit == 0 ? vec3(0.28, 0.52, 0.85) : vec3(0.55, 0.65, 0.82);
      vec3 hemi = uLit == 0
        ? mix(vec3(0.16, 0.18, 0.28), vec3(0.36, 0.42, 0.58), 0.5 + 0.5 * N.z)
        : mix(vec3(0.28, 0.30, 0.36), vec3(0.56, 0.58, 0.64), 0.5 + 0.5 * N.z);
      vec3 diff = hemi + c1 * max(dot(N, L1), 0.0) * 0.82 + c2 * max(dot(N, L2), 0.0) * 0.36;
      if (uBlast > 0.001) {
        vec3 B = uBlastPos - vPos; float bd = length(B) + 1e-3;
        diff += vec3(2.2, 1.05, 0.32) * uBlast * max(dot(N, B / bd), 0.15) * exp(-bd * 0.018);
      }
      float sp = pow(max(dot(N, normalize(L1 + V)), 0.0), 32.0) * 0.22;
      vec3 col = base * diff + c1 * sp;
      col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
      fragColor = vec4(col, 1.0);
    }`);

  const pWire = mkProg(`#version 300 es
    precision highp float; layout(location=0) in vec3 aPos;
    uniform mat4 uVP; uniform mat3 uRot; uniform vec3 uTrans;
    void main() { gl_Position = uVP * vec4(uRot * aPos + uTrans, 1.0); }`,
    `#version 300 es
    precision highp float; out vec4 fragColor;
    void main() { fragColor = vec4(0.22, 0.91, 1.0, 0.72); }`);

  const pSpark = mkProg(`#version 300 es
    precision highp float; layout(location=0) in vec3 aPos; layout(location=1) in vec4 aCol;
    uniform mat4 uVP; out vec4 vCol;
    void main() { vCol = aCol; gl_Position = uVP * vec4(aPos, 1.0); }`,
    `#version 300 es
    precision highp float; in vec4 vCol; out vec4 fragColor;
    void main() { fragColor = vCol; }`);

  function mkBuf(target, arr, usage = gl.STATIC_DRAW) {
    const b = gl.createBuffer(); gl.bindBuffer(target, b); gl.bufferData(target, arr, usage); return b;
  }

  const quadVao = gl.createVertexArray();
  gl.bindVertexArray(quadVao);
  mkBuf(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]));
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

  const sparkVao = gl.createVertexArray();
  gl.bindVertexArray(sparkVao);
  const sparkBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, sparkBuf);
  gl.bufferData(gl.ARRAY_BUFFER, 4096 * 7 * 4, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 28, 12);

  const glTex = DATA.textures.map((t, idx) => {
    const tx = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tx);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([40,55,80,255]));
    const upload = () => {
      gl.bindTexture(gl.TEXTURE_2D, tx);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, loadedImages[idx]);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    };
    if (loadedImages[idx].complete && loadedImages[idx].naturalWidth > 0) upload();
    else loadedImages[idx].addEventListener("load", upload);
    return tx;
  });

  for (const m of ALL_MODELS) {
    for (const s of m.surfaces) {
      s.vao = gl.createVertexArray();
      gl.bindVertexArray(s.vao);
      mkBuf(gl.ARRAY_BUFFER, new Float32Array(AB, s.pos[0], s.pos[1] >> 2));
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
      mkBuf(gl.ARRAY_BUFFER, new Int8Array(AB, s.nrm[0], s.nrm[1]));
      gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.BYTE, true, 4, 0);
      mkBuf(gl.ARRAY_BUFFER, new Float32Array(AB, s.uv[0], s.uv[1] >> 2));
      gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 0, 0);
      s.ibTris = mkBuf(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(AB, s.tris[0], s.tris[1] >> 1));
      s.ibEdges = mkBuf(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(AB, s.edges[0], s.edges[1] >> 1));
    }
  }

  const state = {
    mode: "rig", singleIdx: 0, channel: 0, spin: true, wire: false, lit: 0,
    turntableYaw: 0, entities: [], debris: [], sparks: [], timers: [], blastPos: [0,0,20], blastInt: 0,
    presetLabel: "Larry's 118/120 — SE Bay Tournament Island",
  };
  const cam = { az: -0.52, el: 0.30, dist: 132, panX: 4, panY: 0, panZ: 24, radius: 88, floorZ: 0 };

  function clearTimers() { while (state.timers.length) clearTimeout(state.timers.pop()); }
  function makeEntity(model, pos, yawDeg, channel = 0) {
    return { model, pos: [...pos], yaw: yawDeg * Math.PI / 180, hp: model.hp || 35, maxHp: model.hp || 35, alive: true, cracked: false, channel };
  }

  function updateHpHud() {
    const aliveProps = state.entities.filter((e) => e.alive && e.model.hp > 0);
    const totHp = aliveProps.reduce((a, e) => a + Math.max(0, e.hp), 0);
    const totMax = state.entities.reduce((a, e) => a + (e.model.hp || 0), 0);
    if (totMax <= 0) { $("hp-wrap").style.display = "none"; return; }
    $("hp-wrap").style.display = "flex";
    const pct = Math.max(0, Math.min(100, (totHp / totMax) * 100));
    $("hp-txt").textContent = totHp > 0 ? `HP ${totHp} / ${totMax}` : `DESTROYED (0 / ${totMax})`;
    $("hp-fill").style.width = pct + "%";
  }

  const fillSel = (id, cat, defIdx) => {
    const sel = $(id); sel.innerHTML = "";
    ALL_MODELS.filter((m) => m.cat === cat).forEach((m, i) => {
      const o = document.createElement("option"); o.value = m.id; o.textContent = m.title;
      if (i === defIdx) o.selected = true;
      sel.appendChild(o);
    });
  };
  fillSel("rig-table", "table", 2);
  fillSel("rig-mon1", "monitor", 1);
  fillSel("rig-pc1", "pc", 1);
  fillSel("rig-chair1", "chair", 1);
  fillSel("rig-mon2", "monitor", 2);
  fillSel("rig-chair2", "chair", 3);

  const VENUE_PRESETS = {
    wh_se:        { layout: "dual",   table: "lan_table3", mon1: "lan_mon2", pc1: "lan_pc2", chair1: "lan_chair2", mon2: "lan_mon3", chair2: "lan_chair4", ch: 0, label: "Larry's 118/120 — SE Bay Tournament Island" },
    wh_north:     { layout: "dual",   table: "lan_table1", mon1: "lan_mon3", pc1: "lan_pc3", chair1: "lan_chair4", mon2: "lan_mon1", chair2: "lan_chair1", ch: 1, label: "Larry's 118/120 — North Warehouse TV Pod" },
    u130a_office: { layout: "single", table: "lan_table4", mon1: "lan_mon2", pc1: "lan_pc2", chair1: "lan_chair2", mon2: "lan_mon1", chair2: "lan_chair2", ch: 5, label: "Unit 130A — Office UV Chieftec & Trinitron Rig" },
    u130a_back:   { layout: "single", table: "lan_table4s",mon1: "lan_mon3", pc1: "lan_pc4", chair1: "lan_chair4", mon2: "lan_mon1", chair2: "lan_chair2", ch: 4, label: "Unit 130A Back Room — 5.8-ft Honey-Oak Corner Desk" },
    orcom_checkin:{ layout: "dual",   table: "lan_table4", mon1: "lan_mon2", pc1: "lan_pc4", chair1: "lan_chair2", mon2: "lan_mon3", chair2: "lan_chair2", ch: 5, label: "ORCOM Connect — East Honey-Oak Check-In Counter" },
    orcom_server: { layout: "single", table: "lan_table4s",mon1: "lan_mon2", pc1: "lan_pc2", chair1: "lan_chair4", mon2: "lan_mon3", chair2: "lan_chair4", ch: 3, label: "ORCOM Connect — West Dedicated Server Desk" },
    orcom_island: { layout: "dual",   table: "lan_table1", mon1: "lan_mon1", pc1: "lan_pc1", chair1: "lan_chair1", mon2: "lan_mon4", chair2: "lan_chair1", ch: 2, label: "ORCOM Connect — Main Hall Banquet Row" },
  };

  function applyVenuePreset(pk) {
    const pr = VENUE_PRESETS[pk] || VENUE_PRESETS.wh_se;
    $("rig-preset").value = pk in VENUE_PRESETS ? pk : "wh_se";
    $("rig-layout").value = pr.layout;
    $("rig-table").value = pr.table;
    $("rig-mon1").value = pr.mon1;
    $("rig-pc1").value = pr.pc1;
    $("rig-chair1").value = pr.chair1;
    $("rig-mon2").value = pr.mon2;
    $("rig-chair2").value = pr.chair2;
    state.presetLabel = pr.label;
    setChannel(pr.ch);
    if (state.mode !== "rig") setMode("rig");
    else buildRigScene();
  }
  window.__applyVenuePreset = applyVenuePreset;
  $("rig-preset").onchange = () => applyVenuePreset($("rig-preset").value);

  function buildSingleScene() {
    clearTimers(); state.debris = []; state.sparks = [];
    const m = ALL_MODELS[state.singleIdx];
    state.entities = [makeEntity(m, [0, 0, 0], 0, state.channel)];
    const cx = 0.5*(m.bmin[0]+m.bmax[0]), cy = 0.5*(m.bmin[1]+m.bmax[1]), cz = 0.5*(m.bmin[2]+m.bmax[2]);
    const dx = m.bmax[0]-m.bmin[0], dy = m.bmax[1]-m.bmin[1], dz = m.bmax[2]-m.bmin[2];
    const span = Math.max(dx, dy, dz, 14);
    cam.panX = cx; cam.panY = cy; cam.panZ = cz - dz * 0.05;
    cam.radius = span; cam.dist = span * 2.15; cam.az = -0.52; cam.el = 0.28; cam.floorZ = Math.min(0, m.bmin[2]);
    state.turntableYaw = 0;
    $("hud-title").textContent = m.title;
    $("hud-meta").textContent = `${m.path} · ${m.nv} verts · ${m.nt} tris` + (m.cnt4 > 0 ? ` · ×${m.cnt4} in bklan5.bsp` : "");
    $("hud-desc").textContent = m.desc;
    updateHpHud();
  }

  function buildRigScene() {
    clearTimers(); state.debris = []; state.sparks = [];
    const tbl = MODEL_BY_ID[$("rig-table").value];
    const isCompact = tbl.id === "lan_table4s";
    const dual = $("rig-layout").value === "dual" && !isCompact;
    $("rig-b-wrap1").style.display = dual ? "flex" : "none";
    $("rig-b-wrap2").style.display = dual ? "flex" : "none";

    const ents = [makeEntity(tbl, [0, 0, 0], -90, 0)];
    const monA = MODEL_BY_ID[$("rig-mon1").value];
    const pcA = MODEL_BY_ID[$("rig-pc1").value];
    const chA = MODEL_BY_ID[$("rig-chair1").value];

    if (dual) {
      ents.push(makeEntity(monA, [2, -26, 30], 0, state.channel));
      ents.push(makeEntity(pcA,  [0, -10, 30], 0, 0));
      ents.push(makeEntity(chA,  [27, -26, 0], 180, 0));
      const monB = MODEL_BY_ID[$("rig-mon2").value];
      const pcBId = pcA.id === "lan_pc2" ? "lan_pc4" : "lan_pc2";
      const chB = MODEL_BY_ID[$("rig-chair2").value];
      ents.push(makeEntity(monB, [2, 18, 30], 0, (state.channel + 1) % 6));
      ents.push(makeEntity(MODEL_BY_ID[pcBId], [0, 35, 30], 0, 0));
      ents.push(makeEntity(chB,  [27, 18, 0], 180, 0));
    } else {
      ents.push(makeEntity(monA, [2, -7, 30], 0, state.channel));
      ents.push(makeEntity(pcA,  [0, 13, 30], 0, 0));
      ents.push(makeEntity(chA,  [27, -7, 0], 180, 0));
    }

    state.entities = ents;
    const totTris = ents.reduce((a, e) => a + e.model.nt, 0);
    cam.panX = 4; cam.panY = 0; cam.panZ = 24;
    cam.radius = dual ? 88 : 68; cam.dist = dual ? 132 : 104; cam.az = -0.52; cam.el = 0.30; cam.floorZ = 0;
    state.turntableYaw = 0;
    $("hud-title").textContent = state.presetLabel;
    $("hud-meta").textContent = `${ents.length} destructible entities · ${totTris} total tris · Chain-Reaction Ready`;
    $("hud-desc").textContent = "Choose any Larry's Warehouse or ORCOM venue preset on the left, flip live CRT channels below, or press 💥 DETONATE!";
    updateHpHud();
  }

  ["rig-layout", "rig-table", "rig-mon1", "rig-pc1", "rig-chair1", "rig-mon2", "rig-chair2"].forEach((id) => {
    $(id).onchange = () => { state.presetLabel = "Custom LAN Party Workstation"; if (state.mode === "rig") buildRigScene(); };
  });
  $("btn-randomize").onclick = () => {
    ["rig-table", "rig-mon1", "rig-pc1", "rig-chair1", "rig-mon2", "rig-chair2"].forEach((id) => {
      const s = $(id); s.selectedIndex = Math.floor(Math.random() * s.options.length);
    });
    state.presetLabel = "Randomized B-LAN Tournament Rig";
    setChannel(Math.floor(Math.random() * 6));
    buildRigScene();
  };

  function spawnSparks(origin, count, coolBlue = false) {
    for (let i = 0; i < count; i++) {
      const ang = Math.random() * Math.PI * 2, spd = 65 + Math.random() * 210, vz = 80 + Math.random() * 230;
      const col = coolBlue && Math.random() < 0.55 ? [0.30, 0.92, 1.0] : [1.0, 0.55 + Math.random() * 0.4, 0.15];
      state.sparks.push({ x: origin[0]+(Math.random()-0.5)*8, y: origin[1]+(Math.random()-0.5)*8, z: origin[2]+Math.random()*10,
        vx: Math.cos(ang)*spd, vy: Math.sin(ang)*spd, vz, col, life: 0.45+Math.random()*0.55, maxLife: 0.9 });
    }
  }
  function worldPosOfEntity(ent) {
    const c = Math.cos(state.turntableYaw), s = Math.sin(state.turntableYaw), cz = 0.5*(ent.model.bmin[2]+ent.model.bmax[2]);
    return [c*ent.pos[0] - s*ent.pos[1], s*ent.pos[0] + c*ent.pos[1], ent.pos[2] + cz];
  }

  function explodeEntity(ent, playAudio = true) {
    if (!ent.alive) return;
    ent.alive = false; ent.hp = 0;
    const wp = worldPosOfEntity(ent);
    state.blastPos = wp; state.blastInt = 1.65;
    const cat = ent.model.cat;
    let gibIds = [];
    if (cat === "monitor") { if (playAudio) playSfx("crt_implode", 0.85); gibIds = ["lan_deb_yoke","lan_deb_glass","lan_deb_glass","lan_deb_glass","hd_kbd","hd_mouse","hd_board"]; spawnSparks(wp, 42, true); }
    else if (cat === "pc") { if (playAudio) playSfx("pc_boom", 0.85); gibIds = ["lan_deb_panel","lan_deb_panel","lan_deb_fan","hd_board","hd_cd","hd_floppy","lan_deb_glass"]; spawnSparks(wp, 46, true); }
    else if (cat === "chair") { if (playAudio) playSfx("chair_break", 0.85); gibIds = ["lan_deb_wheel","lan_deb_wheel","lan_deb_wheel","lan_deb_plank"]; spawnSparks(wp, 22, false); }
    else if (cat === "table") { if (playAudio) playSfx("table_smash", 0.9); gibIds = ["lan_deb_plank","lan_deb_plank","lan_deb_plank","lan_deb_plank","lan_deb_panel"]; spawnSparks(wp, 32, false); }
    else { if (playAudio) playSfx("glass_tink", 0.8); gibIds = [ent.model.id,"lan_deb_glass"]; spawnSparks(wp, 20, false); }

    for (const gid of gibIds) {
      const gm = MODEL_BY_ID[gid]; if (!gm) continue;
      const ang = Math.random() * Math.PI * 2, spd = 55 + Math.random() * 165;
      state.debris.push({ model: gm, x: wp[0]+(Math.random()-0.5)*12, y: wp[1]+(Math.random()-0.5)*12, z: Math.max(cam.floorZ+4, wp[2]+(Math.random()-0.3)*8),
        vx: Math.cos(ang)*spd, vy: Math.sin(ang)*spd, vz: 135+Math.random()*195,
        yaw: Math.random()*6.28, pitch: Math.random()*6.28, roll: Math.random()*6.28,
        vyaw: (Math.random()-0.5)*11, vpitch: (Math.random()-0.5)*11, vroll: (Math.random()-0.5)*11, bounces: 0, isGlass: gid === "lan_deb_glass" });
    }
    updateHpHud();
  }

  function triggerDetonateAll() {
    const alive = state.entities.filter((e) => e.alive);
    if (!alive.length) { respawnCurrent(); return; }
    const order = { monitor: 0, pc: 1, chair: 2, table: 3, debris: 0 };
    alive.sort((a, b) => (order[a.model.cat] ?? 1) - (order[b.model.cat] ?? 1));
    alive.forEach((ent, idx) => {
      if (idx === 0) explodeEntity(ent, true);
      else state.timers.push(setTimeout(() => explodeEntity(ent, true), idx * 145));
    });
  }
  function triggerShootHit() {
    const target = state.entities.find((e) => e.alive && e.model.cat === "monitor") || state.entities.find((e) => e.alive);
    if (!target) { respawnCurrent(); return; }
    target.hp -= 18;
    spawnSparks(worldPosOfEntity(target), 14, true);
    if (target.hp <= 0) explodeEntity(target, true);
    else { playSfx("glass_tink", 0.7); if (target.model.cat === "monitor" && target.hp < 20) target.cracked = true; updateHpHud(); }
  }
  function respawnCurrent() { if (state.mode === "rig") buildRigScene(); else buildSingleScene(); }
  $("btn-hit").onclick = triggerShootHit;
  $("btn-boom").onclick = triggerDetonateAll;
  $("btn-respawn").onclick = respawnCurrent;

  function setChannel(ch) {
    state.channel = ch;
    $("chan-bar").querySelectorAll(".ch-btn").forEach((b) => b.classList.toggle("active", +b.dataset.ch === ch));
    state.entities.forEach((e, idx) => {
      if (e.model.cat === "monitor") { e.channel = idx <= 1 ? ch : (ch === 6 ? 6 : (ch + 1) % 6); e.cracked = ch === 6; }
    });
  }
  $("chan-bar").querySelectorAll(".ch-btn").forEach((b) => { b.onclick = () => setChannel(+b.dataset.ch); });
  window.__setChannelFromGallery = (ch) => {
    if (state.mode === "single" && ALL_MODELS[state.singleIdx].cat !== "monitor") selectSingleModel(0);
    setChannel(ch);
  };

  const listEl = $("prop-list");
  let activeCat = "all";
  function renderRoster() {
    listEl.innerHTML = "";
    ALL_MODELS.forEach((m, i) => {
      if (activeCat !== "all" && m.cat !== activeCat) return;
      const b = document.createElement("button");
      b.type = "button"; b.className = "pcard" + (i === state.singleIdx ? " active" : ""); b.dataset.idx = i;
      b.innerHTML = `<div class="ptop"><span class="ctag ${m.cat}">${m.cat}</span><span class="mono" style="color:var(--muted)">${m.cnt4 > 0 ? '×' + m.cnt4 + ' placed' : 'gib'}</span></div><div class="pname">${m.title}</div><div class="pmeta mono">${m.id}.md3 · ${m.nt} tris</div>`;
      b.onclick = () => selectSingleModel(i);
      listEl.appendChild(b);
    });
  }
  function setMode(mode) {
    state.mode = mode;
    $("mode-single").classList.toggle("active", mode === "single");
    $("mode-rig").classList.toggle("active", mode === "rig");
    $("single-pane").style.display = mode === "single" ? "flex" : "none";
    $("rig-pane").classList.toggle("show", mode === "rig");
    if (mode === "rig") buildRigScene(); else buildSingleScene();
  }
  $("mode-single").onclick = () => setMode("single");
  $("mode-rig").onclick = () => setMode("rig");

  function selectSingleModel(i) {
    state.singleIdx = (i + ALL_MODELS.length) % ALL_MODELS.length;
    if (state.mode !== "single") setMode("single"); else buildSingleScene();
    listEl.querySelectorAll(".pcard").forEach((b) => b.classList.toggle("active", +b.dataset.idx === state.singleIdx));
  }
  window.__selectSingleProp = selectSingleModel;
  $("cat-tabs").querySelectorAll(".tab").forEach((b) => {
    b.onclick = () => { activeCat = b.dataset.cat; $("cat-tabs").querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === b)); renderRoster(); };
  });
  $("btn-prev").onclick = () => selectSingleModel(state.singleIdx - 1);
  $("btn-next").onclick = () => selectSingleModel(state.singleIdx + 1);
  $("btn-spin").onclick = () => { state.spin = !state.spin; $("btn-spin").setAttribute("aria-pressed", state.spin); };
  $("btn-wire").onclick = () => { state.wire = !state.wire; $("btn-wire").setAttribute("aria-pressed", state.wire); };
  const litNames = ["🌙 Dark LAN Hall", "💡 Fluorescent Hall", "🎨 Unlit Atlas"];
  $("btn-lit").onclick = () => { state.lit = (state.lit + 1) % 3; $("btn-lit").textContent = litNames[state.lit]; };
  $("btn-full").onclick = () => $("stage").classList.toggle("fullscreen");

  const stage = $("stage");
  stage.addEventListener("contextmenu", (e) => e.preventDefault());
  let drag = null;
  stage.addEventListener("pointerdown", (e) => {
    if (e.target.closest("button, select, .hud-card, .chan-bar, .act-bar")) return;
    stage.setPointerCapture(e.pointerId); stage.classList.add("drag");
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
  });
  stage.addEventListener("pointermove", (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.pan) {
      const s = cam.dist * 0.0016;
      cam.panX -= (-Math.sin(cam.az) * dx) * s; cam.panY -= (Math.cos(cam.az) * dx) * s; cam.panZ += dy * s;
    } else {
      cam.az -= dx * 0.0085; cam.el = Math.max(-1.42, Math.min(1.42, cam.el + dy * 0.0085));
    }
  });
  const endDrag = () => { drag = null; stage.classList.remove("drag"); };
  stage.addEventListener("pointerup", endDrag);
  stage.addEventListener("pointercancel", endDrag);
  stage.addEventListener("wheel", (e) => {
    e.preventDefault();
    cam.dist = Math.max(cam.radius * 0.42, Math.min(cam.radius * 5.0, cam.dist * Math.exp(e.deltaY * 0.0012)));
  }, { passive: false });

  renderRoster();
  applyVenuePreset("wh_se");

  const mP = new Float32Array(16), mV = new Float32Array(16), mVP = new Float32Array(16), mRot = new Float32Array(9), sparkArr = new Float32Array(4096 * 7);
  let lastT = performance.now();

  function stepPhysics(dt) {
    state.blastInt = Math.max(0, state.blastInt - dt * 3.4);
    for (const g of state.debris) {
      if (g.settled) continue;
      g.vz -= 680 * dt; g.x += g.vx * dt; g.y += g.vy * dt; g.z += g.vz * dt;
      g.yaw += g.vyaw * dt; g.pitch += g.vpitch * dt; g.roll += g.vroll * dt;
      const fz = cam.floorZ + 1.8;
      if (g.z < fz) {
        g.z = fz;
        if (Math.abs(g.vz) > 48 && g.bounces < 4) {
          g.vz = -g.vz * 0.44; g.vx *= 0.68; g.vy *= 0.68; g.bounces++;
          if (g.isGlass && g.bounces === 1 && Math.random() < 0.35) playSfx("glass_tink", 0.35);
        } else { g.vz = 0; g.vx = 0; g.vy = 0; g.settled = true; }
      }
    }
    for (let i = state.sparks.length - 1; i >= 0; i--) {
      const p = state.sparks[i]; p.life -= dt;
      if (p.life <= 0) { state.sparks.splice(i, 1); continue; }
      p.vz -= 560 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
      if (p.z < cam.floorZ + 0.5) { p.z = cam.floorZ + 0.5; p.vz = -p.vz * 0.45; }
    }
  }

  function screenTexForChannel(ch, nowSec) {
    const sc = DATA.screens[Math.max(0, Math.min(DATA.screens.length - 1, ch))];
    const fi = sc.fps > 0 ? Math.floor(nowSec * sc.fps) % sc.frames.length : 0;
    return sc.frames[fi];
  }

  function drawItem(model, worldPos, rotMat3, screenCh, isCracked, nowSec, shadowPass) {
    gl.uniformMatrix3fv(gl.getUniformLocation(pMesh, "uRot"), false, rotMat3);
    gl.uniform3fv(gl.getUniformLocation(pMesh, "uTrans"), worldPos);
    for (const s of model.surfaces) {
      if (!shadowPass) {
        let tid = s.tex, em = s.isEmissive;
        if (s.isScreen) { const effCh = isCracked ? 6 : screenCh; tid = screenTexForChannel(effCh, nowSec); em = effCh === 6 ? 0 : 1; }
        gl.uniform1i(gl.getUniformLocation(pMesh, "uEmissive"), em);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, glTex[tid]);
      }
      gl.bindVertexArray(s.vao); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibTris);
      gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);
    }
  }

  function frame(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now; const nowSec = now * 0.001;
    tickScreenCanvases(nowSec);
    if (state.spin && !drag) state.turntableYaw += dt * 0.38;
    stepPhysics(dt);

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(2, Math.floor(canvas.clientWidth * dpr)), h = Math.max(2, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    gl.disable(gl.DEPTH_TEST); gl.useProgram(pSky);
    gl.uniform1i(gl.getUniformLocation(pSky, "uLit"), state.lit);
    gl.uniform1f(gl.getUniformLocation(pSky, "uBlast"), state.blastInt * 0.35);
    gl.bindVertexArray(quadVao); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    const ce = Math.cos(cam.el), se = Math.sin(cam.el);
    const eye = [cam.panX + cam.dist*ce*Math.cos(cam.az), cam.panY + cam.dist*ce*Math.sin(cam.az), cam.panZ + cam.dist*se];
    mat4Persp(mP, 44 * Math.PI / 180, w / h, Math.max(0.5, cam.radius * 0.03), cam.radius * 20.0);
    mat4LookAt(mV, eye, [cam.panX, cam.panY, cam.panZ], [0, 0, 1]);
    mat4Mul(mVP, mP, mV);

    gl.enable(gl.DEPTH_TEST); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.depthMask(false); gl.useProgram(pGrid);
    gl.uniformMatrix4fv(gl.getUniformLocation(pGrid, "uVP"), false, mVP);
    gl.uniform1f(gl.getUniformLocation(pGrid, "uZ"), cam.floorZ);
    gl.uniform1f(gl.getUniformLocation(pGrid, "uRad"), Math.max(120, cam.radius * 2.5));
    gl.uniform3fv(gl.getUniformLocation(pGrid, "uBlastPos"), state.blastPos);
    gl.uniform1f(gl.getUniformLocation(pGrid, "uBlast"), state.blastInt);
    gl.bindVertexArray(quadVao); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    const ct = Math.cos(state.turntableYaw), st = Math.sin(state.turntableYaw);
    gl.useProgram(pMesh); gl.uniformMatrix4fv(gl.getUniformLocation(pMesh, "uVP"), false, mVP);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uShadow"), 1); gl.uniform1f(gl.getUniformLocation(pMesh, "uFloorZ"), cam.floorZ);
    for (const ent of state.entities) {
      if (!ent.alive) continue;
      mat3Euler(mRot, state.turntableYaw + ent.yaw, 0, 0);
      drawItem(ent.model, [ct*ent.pos[0] - st*ent.pos[1], st*ent.pos[0] + ct*ent.pos[1], ent.pos[2]], mRot, ent.channel, ent.cracked, nowSec, true);
    }
    for (const g of state.debris) { mat3Euler(mRot, g.yaw, g.pitch, g.roll); drawItem(g.model, [g.x, g.y, g.z], mRot, 0, true, nowSec, true); }

    gl.depthMask(true); gl.disable(gl.BLEND);
    gl.useProgram(pMesh); gl.uniformMatrix4fv(gl.getUniformLocation(pMesh, "uVP"), false, mVP);
    gl.uniform3fv(gl.getUniformLocation(pMesh, "uEye"), eye); gl.uniform1i(gl.getUniformLocation(pMesh, "uLit"), state.lit);
    gl.uniform1i(gl.getUniformLocation(pMesh, "uShadow"), 0); gl.uniform1i(gl.getUniformLocation(pMesh, "uTex"), 0);
    gl.uniform3fv(gl.getUniformLocation(pMesh, "uBlastPos"), state.blastPos); gl.uniform1f(gl.getUniformLocation(pMesh, "uBlast"), state.blastInt);
    for (const ent of state.entities) {
      if (!ent.alive) continue;
      mat3Euler(mRot, state.turntableYaw + ent.yaw, 0, 0);
      drawItem(ent.model, [ct*ent.pos[0] - st*ent.pos[1], st*ent.pos[0] + ct*ent.pos[1], ent.pos[2]], mRot, ent.channel, ent.cracked, nowSec, false);
    }
    for (const g of state.debris) { mat3Euler(mRot, g.yaw, g.pitch, g.roll); drawItem(g.model, [g.x, g.y, g.z], mRot, 0, true, nowSec, false); }

    if (state.wire) {
      gl.enable(gl.BLEND); gl.useProgram(pWire); gl.uniformMatrix4fv(gl.getUniformLocation(pWire, "uVP"), false, mVP);
      for (const ent of state.entities) {
        if (!ent.alive) continue;
        mat3Euler(mRot, state.turntableYaw + ent.yaw, 0, 0);
        gl.uniformMatrix3fv(gl.getUniformLocation(pWire, "uRot"), false, mRot);
        gl.uniform3fv(gl.getUniformLocation(pWire, "uTrans"), [ct*ent.pos[0] - st*ent.pos[1], st*ent.pos[0] + ct*ent.pos[1], ent.pos[2]]);
        for (const s of ent.model.surfaces) { gl.bindVertexArray(s.vao); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.ibEdges); gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0); }
      }
      gl.disable(gl.BLEND);
    }

    if (state.sparks.length > 0) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
      const n = Math.min(state.sparks.length, 2048); let o = 0;
      for (let i = 0; i < n; i++) {
        const p = state.sparks[i], a = Math.max(0, p.life / p.maxLife);
        sparkArr[o++]=p.x; sparkArr[o++]=p.y; sparkArr[o++]=p.z; sparkArr[o++]=p.col[0]; sparkArr[o++]=p.col[1]; sparkArr[o++]=p.col[2]; sparkArr[o++]=a;
        sparkArr[o++]=p.x-p.vx*0.032; sparkArr[o++]=p.y-p.vy*0.032; sparkArr[o++]=p.z-p.vz*0.032; sparkArr[o++]=p.col[0]; sparkArr[o++]=p.col[1]; sparkArr[o++]=p.col[2]; sparkArr[o++]=0.0;
      }
      gl.useProgram(pSpark); gl.uniformMatrix4fv(gl.getUniformLocation(pSpark, "uVP"), false, mVP);
      gl.bindVertexArray(sparkVao); gl.bindBuffer(gl.ARRAY_BUFFER, sparkBuf);
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, sparkArr.subarray(0, o));
      gl.drawArrays(gl.LINES, 0, n * 2);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.disable(gl.BLEND);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
