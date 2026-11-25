#!/usr/bin/env python3
"""Build a 100% self-contained single-file HTML showcase & changelog for Bakersfield-ish.

Outputs:
  - docs/bakersfieldish_deliverables/bakersfieldish_showcase.html
  - docs/bakersfieldish_showcase.html

Zero external CDN/font/script/fetch/ES-module dependencies: every hero image is
compressed as inline WebP/JPEG base64 data URIs so the page works identically via
file:// offline and when hosted on the VPS alongside ./bakersfieldish_interactive.html.

Usage:
  python source/mm_tools/build_bakersfieldish_showcase_html.py
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image

HERE = Path(__file__).resolve().parent
MOD_DIR = HERE.parents[1]
FINAL_CAP = MOD_DIR / "docs" / "bakersfieldish_captures" / "final"
DELIV_DIR = MOD_DIR / "docs" / "bakersfieldish_deliverables"
OUT_MAIN = DELIV_DIR / "bakersfieldish_showcase.html"
OUT_DOCS = MOD_DIR / "docs" / "bakersfieldish_showcase.html"


def encode_img(path: Path, max_w: int = 960, quality: int = 80) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing showcase image: {path}")
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        nh = max(1, int(round(im.height * (max_w / im.width))))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_showcase_data() -> Dict[str, Any]:
    hero_uri = encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "01_hst_hero_spine.png", max_w=1280, quality=84)

    landmarks = [
        {
            "title": "H Street Core Spine (Padre ↔ Sign ↔ Fox)",
            "tag": "SACRED ANCHORS · 569–582 FT VISTA",
            "desc": "Preserves real downtown Bakersfield scale & sightlines from original bakersfielddowntown.bsp: Padre Hotel, 6-level 18th & Eye Parking Garage, Fox Theater, Nile, Dagny's, Sandrini's, Jerry's & Guthrie's.",
            "img": encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "12_downtown_panorama.png", 860, 80),
        },
        {
            "title": "Golden West Casino + Flat-Roof SkyPad",
            "tag": "MERGED LANDMARK #1 · 12 HOLLOW GLASS BAYS",
            "desc": "Full exterior rotunda, purple neon pylon, courtyard & interior integrated east of Eye St with a verified open-sky north flat-roof SkyPad hub + paired Go-Kart (zero floating 21st St awnings).",
            "img": encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "08_golden_west_skypad.png", 860, 80),
        },
        {
            "title": "The Great Castle",
            "tag": "MERGED LANDMARK #2 · WATCHTOWER JETPACK",
            "desc": "Integrated seamlessly onto the Eye St plaza block with a spacious red-carpet foyer, merloned roof SkyPad + paired Go-Kart, walkable watchtower jetpack perch, and hollow breakable windows.",
            "img": encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "10_great_castle.png", 860, 80),
        },
        {
            "title": "Larry's Warehouse & LAN Courtyard",
            "tag": "MERGED LANDMARK #3 · SKY-BRIDGE TO DAGNY'S",
            "desc": "1:1 B76 warehouse + Unit 130A LAN hall + open-aisle forklifts, 4 newly carved hollow glass windows, walkable Sky-Bridge to Dagny's, and purple-sign Courtyard SkyPad.",
            "img": encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "07_larrys_warehouse.png", 860, 80),
        },
        {
            "title": "The Bakersfield Sign (3-Stage Rampable Arch)",
            "tag": "MERGED LANDMARK #4 · 864 U SPAN OVER H ST",
            "desc": "Iconic yellow Bakersfield arch spanning H St between Padre & Fox. Split into 3 progressive breakable submodels (west cap, east cap, main arch) that topple -90° into a smooth Go-Kart ramp.",
            "img": encode_img(FINAL_CAP / "orbit_sign_intact_keyframes" / "07_270_S.png", 860, 80),
        },
        {
            "title": "600-ft High Skybox & Chained SkyPad Loop",
            "tag": "7,200 U CEILING (2.14×) · 11 SKYPADS",
            "desc": "Skybox raised from 3,360 u to 7,200 u so 6 closed-loop rooftop SkyPads + 5 street feeders launch players continuously across every district without ceiling bonks.",
            "img": encode_img(FINAL_CAP / "flythrough_bakersfieldish_keyframes" / "11_skypad_skyline.png", 860, 80),
        },
    ]

    def kf(folder: str, name: str, label: str, note: str) -> Dict[str, str]:
        return {
            "label": label,
            "note": note,
            "img": encode_img(FINAL_CAP / folder / name, 960, 80),
        }

    sequences = {
        "padre": {
            "title": "The Padre Hotel — 3-Stage Controlled Demolition (91/100 Critic PASS)",
            "meta": "2,600 HP (13× Fox) · 1.75× Eric Cannon Bonus · 20–24 Explosions · 24 Player/Kart-Bouncing Boulders · 115s Rubble",
            "frames": [
                kf("destruct_padre_keyframes", "01_intact.png", "01 · Intact", "Iconic 8-story Padre Hotel anchoring 18th & H St across from the 6-level Parking Garage."),
                kf("destruct_padre_keyframes", "02_stage1_east_wing.png", "02 · Stage 1 (66%)", "Hit-localized Stage 1 blasts off the shot East Wing with explosions & tumbling concrete boulders while the main tower & crown stand."),
                kf("destruct_padre_keyframes", "03_stage2_crown.png", "03 · Stage 2 (33%)", "Stage 2 shears off the rooftop PADRE crown sign & hides roof props safely while lower floors vent smoke."),
                kf("destruct_padre_keyframes", "04_stage3_trigger.png", "04 · Stage 3 Blasts", "Final Stage 3 triggers 10 rhythmic lower charge pops + multi-point facade blasts (zero blinding whiteout or screen flash)."),
                kf("destruct_padre_keyframes", "07_mid_pancake.png", "05 · Inward Implosion", "Multi-tier inward V-collapse with unified warm matte tan dust & rolling street boulders visibly bouncing targets across 18th St."),
                kf("destruct_padre_keyframes", "12_rubble_aftermath.png", "06 · Climbable Ruin", "Organic 2-story climbable concrete rubble mound persisting 115s with zero floating sky pads or void leaks."),
            ],
        },
        "fox": {
            "title": "Historic Fox Theater — 3-Stage Collapse & 25s Slow Rebuild (90/100 Critic PASS)",
            "meta": "450 HP (Clock + Structure) · 12–15 Explosions · 115s Climbable Ruin · 25s Bottom-Up Upright Rebuild + Welding Sparks",
            "frames": [
                kf("destruct_fox_keyframes", "01_intact.png", "01 · Intact", "Historic Bakersfield Fox Theater on 20th & H St with intact wrap-around marquee, red FOX shaft, clock & blue dome."),
                kf("destruct_fox_keyframes", "02_stage1_marquee.png", "02 · Stage 1 (66%)", "Hit-localized Stage 1 blasts off the shot corner marquee while the clock tower & auditorium stay standing."),
                kf("destruct_fox_keyframes", "03_stage2_belfry.png", "03 · Stage 2 (33%)", "Stage 2 explodes the clock & blue-domed upper belfry off the collar while the red FOX shaft remains intact."),
                kf("destruct_fox_keyframes", "04_stage3_trigger.png", "04 · Stage 3 Crash", "Final Stage 3 collapses the remaining FOX tower, hall & stagehouse into a warm matte tan dust surge clear of the 20th St signal."),
                kf("destruct_fox_keyframes", "09_rubble_clean_b.png", "05 · Climbable Ruin", "Multi-tiered climbable ruin with crashed blue dome & fallen marquee slab, persisting 115s before slow rebuild."),
                kf("destruct_fox_keyframes", "15_rebuild_twr_hi.png", "06 · 25s Rebuild", "Staged upright bottom-to-top reconstruction wrapped in golden welding sparks, restoring rooftop SkyPad trigger bounds cleanly."),
                kf("destruct_fox_keyframes", "16_restored_intact.png", "07 · Restored", "100% exact restoration ready to be demolished all over again."),
            ],
        },
        "sign": {
            "title": "The Bakersfield Sign — 3-Stage Break & Go-Kart Rampable Topple (86/100 Critic PASS)",
            "meta": "540 HP · Split sign_west / sign_east / sign_span · 7–9 Explosions · -90° Topple · 16.3° Smooth Go-Kart Ramp",
            "frames": [
                kf("destruct_sign_keyframes", "01_intact_hst.png", "01 · Intact Arch", "864-unit BAKERSFIELD arch spanning H St with clean vehicle & pedestrian clearance."),
                kf("destruct_sign_keyframes", "02_stage1_west_cap.png", "02 · Stage 1 West Cap", "Shooting the West pier/crown blasts off sign_west's terracotta eaves & pyramid cap while East cap & arch stand."),
                kf("destruct_sign_keyframes", "03_stage2_east_cap.png", "03 · Stage 2 East Cap", "Shooting the East pier/crown blasts off sign_east's cap in charcoal smoke & debris."),
                kf("destruct_sign_keyframes", "04_stage3_piers.png", "04 · Stage 3 Piers", "Final pier blasts shear both shafts, igniting blue-gold neon sparks as the arch accelerates North."),
                kf("destruct_sign_keyframes", "07_street_impact.png", "05 · Impact & Surge", "Triple street-impact explosions, damped elastic street bounce, and full-width warm matte tan dust surge."),
                kf("orbit_sign_collapsed_keyframes", "06_225_SW.png", "06 · Rampable Arch", "Exact-pose -90° fallen wreckage with 16.3° double-sided clip ramp + Veh_GroundSample BSP fix — Go-Karts launch straight over it!"),
            ],
        },
        "glass": {
            "title": "Shatterable Architectural Glass — 56 Hollow Bays Across 6+ Buildings (87/100 Critic PASS)",
            "meta": "56 Real Cut-Out func_breakable Bays · 1-Hit Shatter · Translucent Beveled Ice-Blue 3D Shards · Walk-Through Openings",
            "frames": [
                kf("destruct_glass_keyframes", "01_intact_panes.png", "01 · Intact Bays", "Recessed storefront windows across Padre, Nile, Dagny's, Golden West Casino, Great Castle & Larry's Warehouse."),
                kf("destruct_glass_keyframes", "02_blast1_shatter.png", "02 · 1st-Hit Shatter", "Instant 1-hit shatter with cool crystalline burst & zero blood/soot/orange fireball artifacts."),
                kf("destruct_glass_keyframes", "03_pane1_shards.png", "03 · 3D Ice Shards", "Genuinely translucent beveled ice-blue/silver 3D glass shards tumbling & bouncing across the sidewalk."),
                kf("destruct_glass_keyframes", "05_both_open_frames.png", "04 · Hollow Bays", "Clean hollow openings revealed straight into real lit interiors."),
                kf("destruct_glass_keyframes", "06_entering_frame.png", "05 · Walk-Through", "Players walk or jump smoothly straight through shattered storefront bays."),
                kf("destruct_glass_keyframes", "08_looking_out_frame.png", "06 · Interior Contrast", "Looking back out onto H St contrasting shattered open bays right beside intact glazed panes."),
            ],
        },
    }

    return {
        "hero": hero_uri,
        "landmarks": landmarks,
        "sequences": sequences,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bakersfield-ish — Map Showcase &amp; Engineering Changelog</title>
<style>
  :root {
    --bg: #0c0e13;
    --bg2: #131722;
    --card: #171c28;
    --card2: #1d2434;
    --border: rgba(242, 198, 114, 0.22);
    --gold: #f2c672;
    --amber: #e89b48;
    --cyan: #6ec6ff;
    --green: #69d18b;
    --coral: #ff7a6b;
    --text: #eef1f7;
    --muted: #9ea8bc;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: radial-gradient(circle at 20% -10%, rgba(232,155,72,0.12), transparent 45%),
                radial-gradient(circle at 85% 10%, rgba(110,198,255,0.09), transparent 42%),
                var(--bg);
    color: var(--text);
    font: 15px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    min-height: 100vh;
  }
  a { color: var(--gold); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .wrap { max-width: 1220px; margin: 0 auto; padding: 0 22px; }

  /* Sticky Nav */
  nav {
    position: sticky; top: 0; z-index: 40;
    background: rgba(12, 14, 19, 0.88);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }
  .nav-in {
    max-width: 1220px; margin: 0 auto; padding: 12px 22px;
    display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;
  }
  .brand { font-weight: 800; letter-spacing: 0.06em; color: var(--gold); font-size: 15px; }
  .nav-links { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; font-size: 13px; }
  .nav-links a { color: #d6dce8; font-weight: 600; }
  .nav-links a:hover { color: var(--gold); text-decoration: none; }
  .btn-cta {
    display: inline-flex; align-items: center; gap: 8px;
    background: linear-gradient(135deg, #f2c672, #e08d3c);
    color: #14100a !important; font-weight: 800; font-size: 13.5px;
    padding: 9px 16px; border-radius: 9px; border: 0; cursor: pointer;
    box-shadow: 0 6px 22px rgba(242, 198, 114, 0.25);
    transition: transform .12s, box-shadow .15s;
  }
  .btn-cta:hover { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(242,198,114,0.36); text-decoration: none; }
  .btn-ghost {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.18);
    color: var(--text) !important; font-weight: 700; font-size: 13.5px;
    padding: 9px 16px; border-radius: 9px;
  }
  .btn-ghost:hover { background: rgba(242,198,114,0.14); border-color: var(--gold); text-decoration: none; }

  /* Hero */
  .hero {
    position: relative; overflow: hidden;
    border-bottom: 1px solid var(--border);
    padding: 54px 0 48px;
  }
  .hero-grid {
    display: grid; grid-template-columns: 1.05fr 1fr; gap: 30px; align-items: center;
  }
  @media (max-width: 920px) { .hero-grid { grid-template-columns: 1fr; } }
  .eyebrow {
    display: inline-block; font-size: 11px; font-weight: 800; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--gold);
    background: rgba(242,198,114,0.12); border: 1px solid rgba(242,198,114,0.35);
    padding: 4px 10px; border-radius: 99px; margin-bottom: 14px;
  }
  .hero h1 {
    font-size: clamp(30px, 4.4vw, 48px); line-height: 1.08; font-weight: 900;
    letter-spacing: -0.02em; margin-bottom: 14px;
  }
  .hero h1 span { color: var(--gold); }
  .hero p.lead { color: #cfd6e6; font-size: 16px; margin-bottom: 22px; max-width: 58ch; }
  .hero-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
  .hero-img-card {
    border-radius: 14px; overflow: hidden; border: 1px solid var(--border);
    background: var(--card); box-shadow: 0 22px 60px rgba(0,0,0,0.6);
    cursor: zoom-in;
  }
  .hero-img-card img { display: block; width: 100%; height: auto; }
  .hero-img-cap {
    padding: 10px 14px; font-size: 12px; color: var(--muted);
    display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap;
    background: rgba(10,12,17,0.85);
  }

  .kpi-strip {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px;
    margin-top: 26px;
  }
  .kpi {
    background: var(--card); border: 1px solid rgba(255,255,255,0.09); border-radius: 10px;
    padding: 12px 14px;
  }
  .kpi .val { font-size: 21px; font-weight: 900; color: var(--gold); line-height: 1.15; }
  .kpi .lbl { font-size: 11.5px; color: var(--muted); margin-top: 3px; }

  /* Sections */
  section { padding: 52px 0; border-bottom: 1px solid rgba(255,255,255,0.07); }
  .sec-head { margin-bottom: 24px; }
  .sec-head h2 { font-size: 26px; font-weight: 850; letter-spacing: -0.015em; margin-bottom: 6px; }
  .sec-head p { color: var(--muted); max-width: 72ch; }

  /* Landmark Grid */
  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 18px; }
  .lm-card {
    background: var(--card); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; overflow: hidden; display: flex; flex-direction: column;
    transition: border-color .15s, transform .15s;
  }
  .lm-card:hover { border-color: rgba(242,198,114,0.45); transform: translateY(-2px); }
  .lm-card img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; cursor: zoom-in; }
  .lm-body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 6px; }
  .lm-tag { font-size: 10.5px; font-weight: 800; letter-spacing: 0.08em; color: var(--cyan); }
  .lm-card h3 { font-size: 16.5px; font-weight: 800; }
  .lm-card p { font-size: 13.5px; color: #c4ccdc; }

  /* Interactive Stage Gallery */
  .tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
  .tab-btn {
    background: var(--card); border: 1px solid rgba(255,255,255,0.14);
    color: var(--text); font-weight: 700; font-size: 13px; padding: 9px 14px;
    border-radius: 9px; cursor: pointer; transition: .12s;
  }
  .tab-btn:hover { border-color: var(--gold); }
  .tab-btn.active { background: rgba(242,198,114,0.18); border-color: var(--gold); color: var(--gold); }

  .stage-box {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px;
  }
  .stage-hdr { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .stage-hdr h3 { font-size: 18px; font-weight: 800; color: var(--gold); }
  .stage-meta { font-size: 12px; color: var(--muted); font-family: ui-monospace, Consolas, monospace; }
  .stage-main { position: relative; border-radius: 10px; overflow: hidden; background: #07090d; border: 1px solid rgba(255,255,255,0.08); }
  .stage-main img { width: 100%; max-height: 540px; object-fit: contain; display: block; margin: 0 auto; cursor: zoom-in; }
  .stage-caption {
    padding: 12px 15px; background: rgba(11,14,20,0.92);
    display: flex; justify-content: space-between; align-items: center; gap: 14px; flex-wrap: wrap;
    border-top: 1px solid rgba(255,255,255,0.08);
  }
  .stage-caption strong { color: var(--gold); margin-right: 8px; }
  .stage-nav { display: flex; gap: 8px; }
  .stage-nav button {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.16);
    color: var(--text); font-weight: 700; padding: 6px 12px; border-radius: 7px; cursor: pointer;
  }
  .stage-nav button:hover { border-color: var(--gold); color: var(--gold); }
  .thumbs {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 8px; margin-top: 12px;
  }
  .thumb {
    background: var(--bg2); border: 2px solid transparent; border-radius: 8px;
    overflow: hidden; cursor: pointer; text-align: left; padding: 0; color: var(--text);
  }
  .thumb.active { border-color: var(--gold); }
  .thumb img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
  .thumb span { display: block; font-size: 11px; font-weight: 700; padding: 5px 7px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Changelog Cards */
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px; }
  @media (max-width: 520px) { .grid-2 { grid-template-columns: 1fr; } }
  .chg-card {
    background: var(--card); border: 1px solid rgba(255,255,255,0.09); border-radius: 12px; padding: 18px 20px;
  }
  .chg-card h3 { font-size: 16px; font-weight: 800; color: var(--gold); margin-bottom: 10px; }
  .chg-card ul { padding-left: 18px; display: flex; flex-direction: column; gap: 7px; color: #d1d8e6; font-size: 13.8px; }
  .chg-card li strong { color: #fff; }
  code {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px; padding: 1px 5px; font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; color: #ffe2a8;
  }

  /* Critic Score Bars */
  .score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .score-card {
    background: var(--card); border: 1px solid rgba(105,209,139,0.3); border-radius: 12px; padding: 16px;
  }
  .score-top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
  .score-name { font-weight: 800; font-size: 15px; }
  .score-num { font-weight: 900; font-size: 20px; color: var(--green); }
  .bar-bg { height: 8px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; margin-bottom: 8px; }
  .bar-fill { height: 100%; background: linear-gradient(90deg, var(--amber), var(--green)); border-radius: 99px; }
  .score-sub { font-size: 12px; color: var(--muted); }

  /* Tables */
  .tbl-wrap { overflow-x: auto; background: var(--card); border: 1px solid rgba(255,255,255,0.09); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.07); }
  th { font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--gold); background: rgba(255,255,255,0.03); }
  tr:last-child td { border-bottom: 0; }
  .pill-ok {
    display: inline-block; background: rgba(105,209,139,0.16); color: var(--green);
    border: 1px solid rgba(105,209,139,0.4); border-radius: 99px; font-size: 11px; font-weight: 800; padding: 2px 8px;
  }

  /* Lightbox */
  #lb {
    position: fixed; inset: 0; z-index: 99; background: rgba(5,7,11,0.93);
    display: none; align-items: center; justify-content: center; flex-direction: column; padding: 20px; gap: 12px;
  }
  #lb.open { display: flex; }
  #lb img { max-width: 96vw; max-height: 84vh; border-radius: 10px; border: 1px solid var(--border); }
  #lb-cap { color: #e2e8f5; font-size: 13.5px; max-width: 900px; text-align: center; }

  footer { padding: 34px 0 48px; color: var(--muted); font-size: 13px; text-align: center; }
</style>
</head>
<body>

<nav>
  <div class="nav-in">
    <div class="brand">BAKERSFIELD-ISH · QUAKE 1 MAP SHOWCASE</div>
    <div class="nav-links">
      <a href="#landmarks">Landmarks</a>
      <a href="#destructibles">3-Stage Destruction</a>
      <a href="#changelog">What Changed</a>
      <a href="#audits">Critics &amp; Audits</a>
      <a href="#play">Play &amp; Files</a>
      <a class="btn-cta" href="./bakersfieldish_interactive.html">Launch 3D Interactive Viewer →</a>
    </div>
  </div>
</nav>

<header class="hero">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <div class="eyebrow">BakersfieldQuake · maps/bakersfieldish.bsp</div>
        <h1>Remastered <span>Bakersfield-ish</span></h1>
        <p class="lead">
          A cohesive, light-handed post-apocalyptic remix of downtown Bakersfield preserving the iconic
          <strong>Padre Hotel</strong>, <strong>Fox Theater</strong>, <strong>569–582 ft H Street spine</strong>,
          6-level Parking Garage, and enterable downtown venues—while merging <strong>Golden West Casino</strong>,
          <strong>The Great Castle</strong>, <strong>Larry's Warehouse</strong>, and <strong>The Bakersfield Sign</strong>
          with <strong>3-stage hit-localized destructible landmarks</strong>, <strong>56 hollow shatterable glass bays</strong>,
          and a <strong>600-ft high chained Super Jump Pad skybox</strong>.
        </p>
        <div class="hero-actions">
          <a class="btn-cta" href="./bakersfieldish_interactive.html">Explore in 3D Offline WebGL2 Viewer →</a>
          <a class="btn-ghost" href="#destructibles">Inspect 3-Stage Demolitions</a>
          <a class="btn-ghost" href="#changelog">Read Engineering Notes</a>
        </div>
      </div>
      <div class="hero-img-card" id="hero-card">
        <img id="hero-img" alt="H Street spine in Bakersfield-ish">
        <div class="hero-img-cap">
          <span><strong>H Street Vista:</strong> Padre Hotel, Bakersfield Sign &amp; 18th St Plaza</span>
          <span>Click any image to zoom</span>
        </div>
      </div>
    </div>

    <div class="kpi-strip">
      <div class="kpi"><div class="val">7,200 u</div><div class="lbl">600-ft High Skybox (2.14× baseline)</div></div>
      <div class="kpi"><div class="val">3-Stage</div><div class="lbl">Hit-Localized Breaks + Multi-Blasts</div></div>
      <div class="kpi"><div class="val">56 Bays</div><div class="lbl">Hollow 3D-Shard Glass (6+ Buildings)</div></div>
      <div class="kpi"><div class="val">11 SkyPads</div><div class="lbl">6-Roof Closed Loop + 5 Street Feeders</div></div>
      <div class="kpi"><div class="val">36 / 36</div><div class="lbl">Spawns Paired with Walkable Go-Karts</div></div>
      <div class="kpi"><div class="val">86–91/100</div><div class="lbl">4/4 Fresh Demolition Critics Passed</div></div>
    </div>
  </div>
</header>

<section id="landmarks">
  <div class="wrap">
    <div class="sec-head">
      <h2>What We Made — Cohesive Merged Downtown</h2>
      <p>
        Built directly on top of the real-scale downtown Bakersfield footprint (1 ft = 12 u, 0.00 ft delta on Padre,
        Fox, 6-level Parking Garage, Dagny's, Nile, Sandrini's, Jerry's &amp; Guthrie's) with all four signature
        landmarks integrated cleanly into replaceable city blocks—not glued on.
      </p>
    </div>
    <div class="grid-3" id="landmark-grid"></div>
  </div>
</section>

<section id="destructibles">
  <div class="wrap">
    <div class="sec-head">
      <h2>Interactive 3-Stage Destruction &amp; Rebuild Gallery</h2>
      <p>
        Every major destructible breaks in <strong>at least 3 real structural parts</strong>—the specific area you shoot
        explodes and breaks off first (~66% HP), a second major section breaks next (~33% HP), and the final crash (0% HP)
        brings down the remaining structure in multi-point explosions, warm non-blinding matte dust, rolling boulders, and
        climbable rubble. Select a landmark and step through real in-game captures:
      </p>
    </div>

    <div class="tabs" id="seq-tabs">
      <button type="button" class="tab-btn active" data-seq="padre">Padre Hotel (3-Stage + Boulders)</button>
      <button type="button" class="tab-btn" data-seq="fox">Fox Theater (3-Stage + 25s Rebuild)</button>
      <button type="button" class="tab-btn" data-seq="sign">Bakersfield Sign (3-Stage + Ramp)</button>
      <button type="button" class="tab-btn" data-seq="glass">Shatterable Glass (56 Bays)</button>
    </div>

    <div class="stage-box">
      <div class="stage-hdr">
        <h3 id="stage-title"></h3>
        <div class="stage-meta" id="stage-meta"></div>
      </div>
      <div class="stage-main">
        <img id="stage-img" alt="Destruction stage frame">
        <div class="stage-caption">
          <div><strong id="stage-lbl"></strong><span id="stage-note"></span></div>
          <div class="stage-nav">
            <button type="button" id="btn-prev">← Prev</button>
            <button type="button" id="btn-next">Next →</button>
          </div>
        </div>
      </div>
      <div class="thumbs" id="stage-thumbs"></div>
    </div>
  </div>
</section>

<section id="changelog">
  <div class="wrap">
    <div class="sec-head">
      <h2>What We Changed — Architecture &amp; Engineering Notes</h2>
      <p>Summary of map, QuakeC physics, visual effects, traversal, and packaging changes shipped in this release.</p>
    </div>

    <div class="grid-2">
      <div class="chg-card">
        <h3>1. 3-Part Hit-Localized Progressive Breaks &amp; Multi-Point Explosions</h3>
        <ul>
          <li><strong>Area-Shot Structural Breaks:</strong> Shooting Fox Theater (<code>450 HP</code>), Padre Hotel (<code>2,600 HP</code>), or Bakersfield Sign (<code>540 HP</code>) breaks the specific shot submodel at <strong>~66% HP</strong> (Stage 1), a second section at <strong>~33% HP</strong> (Stage 2), and triggers the full catastrophic collapse at <strong>0% HP</strong> (Stage 3).</li>
          <li><strong>More Big-Building Explosions (Strictly Non-Blinding):</strong> Added custom <code>bako_big_boom</code> effect (vivid fireball + sparks + matte charcoal smoke, alpha <code>78–112</code>, zero <code>bf</code> / <code>v_cshift</code> whiteout): <strong>20–24 blasts</strong> on Padre, <strong>12–15</strong> on Fox, and <strong>7–9</strong> on the Bakersfield Sign.</li>
          <li><strong>Solid Fracture Caps:</strong> Remaining standing cores on Padre, Fox, and Bakersfield Sign carry solid interior walls/caps so early Stage 1/2 breaks leave scarred architecture—never hollow void holes.</li>
        </ul>
      </div>

      <div class="chg-card">
        <h3>2. Fox Theater, Padre Hotel, Sign &amp; 56 Glass Bays</h3>
        <ul>
          <li><strong>Fox Theater:</strong> Shoot the clock or walls/marquee → coupled tower collapse clear of 20th St signal arm → whole-map damped shake (<code>24,000 u</code> radius, clamped pitch/roll) → <code>115s</code> climbable ruin → <code>~25s</code> upright bottom-up slow rebuild with golden welding sparks &amp; intact rooftop SkyPad bbox restoration.</li>
          <li><strong>Padre Hotel:</strong> 13× tougher than Fox + Eric Cannon <code>1.75×</code> structural blast bonus (fixed splash dedup race) → inward V-collapse → unified warm matte tan dust surge → <strong>24 rolling concrete boulders</strong> that actively bounce players, bots &amp; parked/driven vehicles (with <code>veh_coast_until</code>) → <code>115s</code> 2-story climbable rubble.</li>
          <li><strong>Bakersfield Sign &amp; Glass:</strong> Split into <code>sign_west</code>, <code>sign_east</code>, and <code>sign_span</code> toppling <code>-90°</code> onto H St with a <code>16.3°</code> double-sided <code>clip</code> ramp; <strong>56 real hollow cut-out <code>func_breakable</code> glass windows</strong> across Padre, Nile, Dagny's, Golden West, Great Castle &amp; Larry's shatter on 1 hit into translucent beveled ice-blue 3D shards.</li>
        </ul>
      </div>

      <div class="chg-card">
        <h3>3. Traversal, Vehicles &amp; SkyPad Overhaul</h3>
        <ul>
          <li><strong>Go-Kart BSP &amp; Rubble Grounding Fix:</strong> Upgraded <code>vehicle_drive.qc:Veh_GroundSample</code> from <code>MOVE_WORLDONLY</code> to <code>tracebox(..., 1, v)</code> accepting <code>SOLID_BSP</code> (plus <code>gokart.qc</code> curb-climb), enabling Go-Karts to ramp smoothly over the fallen Bakersfield Sign arch and drive cleanly across Fox/Padre roofs &amp; rubble.</li>
          <li><strong>11 Chained Super Jump Pads (<code>info_skypad</code>):</strong> Verified open-sky 6-rooftop closed loop (Padre → Fox → Larry's → Golden West flat north roof → Great Castle → Parking Garage L6 → Padre) plus 5 street/courtyard feeders (including the Purple Launch Pad in Larry's Courtyard).</li>
          <li><strong>36/36 Spawns + Go-Karts &amp; 12/12 Jump Pads:</strong> Every deathmatch spawn has a walkable same-floor Go-Kart within 125–192 u, zero spawns inside SkyPad triggers or collapse footprints, <code>12/12</code> regular <code>trigger_push</code> pads pass <code>25/25</code> wide-hull checks, <code>13</code> jetpacks, stunt ramps &amp; unobstructed Dagny's↔Larry's Sky-Bridge.</li>
        </ul>
      </div>

      <div class="chg-card">
        <h3>4. Reproducible Packaging &amp; Map Hygiene</h3>
        <ul>
          <li><strong>Zero Base-PK3 Edits:</strong> Base <code>bakersfield.pk3</code> (442 MB) and <code>q15.pk3</code> (477 MB) remain 100% untouched for differential updaters.</li>
          <li><strong>Reproducible Overlay <code>zz_bakersfieldish.pk3</code> (423 KB):</strong> Deterministic <code>1980-01-01</code> timestamps, sorted entries, byte-identical SHA-256 verified, bundling custom rubble/boulder/glass shaders, refreshed top-down <code>gfx/minimap/bakersfieldish.png</code>, and <code>levelshots/bakersfieldish.jpg</code> + wired into CI <code>.github/workflows/build-zip.yml</code>.</li>
          <li><strong>Clean Engine Runtime:</strong> Zero missing textures across 1,037 BSP miptexes, zero missing models/sounds, zero QC/CSQC errors, zero blood/gibs when shooting or axing masonry/metal/glass, and triple-layer telefrag immunity on all destructibles.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section id="audits">
  <div class="wrap">
    <div class="sec-head">
      <h2>Fresh-Context Demolition Critics &amp; 4-Audit Verification</h2>
      <p>
        Every destructible was judged on real 720p30 + stereo audio gameplay captures by fresh-context critics against real
        demolition footage benchmarks (Tropicana Las Vegas, Trump Plaza, masonry clock towers &amp; steel arches), followed by
        4 independent accuracy audits (Quantitative BSP2/Hull-1, Visual/OSM/StreetView, Mechanics/QC Physics, and Live Zircon).
      </p>
    </div>

    <div class="score-grid">
      <div class="score-card">
        <div class="score-top"><span class="score-name">Padre Hotel</span><span class="score-num">91 / 100</span></div>
        <div class="bar-bg"><div class="bar-fill" style="width:91%"></div></div>
        <div class="score-sub">R1: 34 → R3: 79 → R4: <strong>91 PASS</strong> · 0/6 Red Flags + 3-stage &amp; 20+ blasts added</div>
      </div>
      <div class="score-card">
        <div class="score-top"><span class="score-name">Fox Theater</span><span class="score-num">90 / 100</span></div>
        <div class="bar-bg"><div class="bar-fill" style="width:90%"></div></div>
        <div class="score-sub">R1: 35 → R4: 82 → R5: <strong>90 PASS</strong> · 0/6 Red Flags + 3-stage &amp; 25s rebuild</div>
      </div>
      <div class="score-card">
        <div class="score-top"><span class="score-name">Shatterable Glass</span><span class="score-num">87 / 100</span></div>
        <div class="bar-bg"><div class="bar-fill" style="width:87%"></div></div>
        <div class="score-sub">R1: 14 → R3: <strong>87 PASS</strong> · 0/6 Red Flags · 56 hollow bays across 6+ buildings</div>
      </div>
      <div class="score-card">
        <div class="score-top"><span class="score-name">Bakersfield Sign</span><span class="score-num">86 / 100</span></div>
        <div class="bar-bg"><div class="bar-fill" style="width:86%"></div></div>
        <div class="score-sub">R1: 47 → R3: <strong>86 PASS</strong> · 0/6 Red Flags + 3-stage &amp; Go-Kart ramp fix</div>
      </div>
    </div>

    <div class="tbl-wrap">
      <table>
        <thead>
          <tr><th>Audit / Defect Class</th><th>Root Cause Caught</th><th>Verified Fix Landed</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td>Padre Frame-1 Telefrag</td><td><code>spawn_tdeath</code> dealt 50,000 dmg to Padre on DM spawn</td><td>Triple-layer telefrag immunity in <code>triggers.qc</code>, <code>combat.qc</code>, <code>bako_destruct.qc</code></td><td><span class="pill-ok">FIXED</span></td></tr>
          <tr><td>Golden West Roof SkyPad</td><td>Initial anchor sat inside 30.8-ft gable attic + 3 floating 21st St awnings</td><td>Moved onto verified open-sky north flat roof (<code>Z=16.2 ft</code>); expanded <code>gw_a</code> strip filter</td><td><span class="pill-ok">FIXED</span></td></tr>
          <tr><td>Go-Kart Fallen Sign Ramp</td><td><code>Veh_GroundSample</code> used <code>MOVE_WORLDONLY</code> (ignored <code>SOLID_BSP</code> &amp; <code>clip</code>)</td><td>Switched to <code>tracebox(..., 1, v)</code> + <code>SOLID_BSP</code> curb-climb + <code>-90°</code> 16.3° double-sided clip ramp</td><td><span class="pill-ok">FIXED</span></td></tr>
          <tr><td>Padre Rolling Boulder Bounces</td><td>Proximity scan omitted players/bots and parked <code>MOVETYPE_NONE</code> karts</td><td>Full <code>bm_player_head</code> + <code>findradius</code> sweep + <code>veh_coast_until</code> for parked/all vehicles</td><td><span class="pill-ok">FIXED</span></td></tr>
          <tr><td>Rebuilt Rooftop SkyPad BBox</td><td><code>setmodel(e,"")</code> cleared <code>mins</code>/<code>maxs</code> on hide without restoring <code>setsize</code></td><td>Saved/restored full <code>mins</code>/<code>maxs</code>/<code>solid</code>/<code>model</code> on every roof prop &amp; SkyPad</td><td><span class="pill-ok">FIXED</span></td></tr>
          <tr><td>Traversal &amp; Roof Footing</td><td>Dagny's Sky-Bridge clip wall, Great Castle hovering roof props, Pad #04 lamp pole</td><td>Removed blocking clip wall; verified flat Great Castle anchors; <code>12/12</code> pads pass <code>25/25</code> wide-hull</td><td><span class="pill-ok">FIXED</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section id="play">
  <div class="wrap">
    <div class="sec-head">
      <h2>Play In-Game &amp; Deliverables Inventory</h2>
      <p>
        Load the map directly on the BakersfieldQuake server or locally in Zircon with <code>map bakersfieldish</code>,
        or fly through the compiled BSP right in your browser using the standalone offline 3D viewer.
      </p>
    </div>

    <div class="grid-2" style="margin-bottom:20px;">
      <div class="chg-card">
        <h3>Quick Console &amp; Testing Commands</h3>
        <ul>
          <li><code>map bakersfieldish</code> — Launch Bakersfield-ish locally or vote/switch on the VPS.</li>
          <li><code>bako_cmd status</code> — Inspect live Fox / Padre / Sign stage, HP, boulder &amp; glass shard counts.</li>
          <li><code>bako_cmd fast_rebuild_fox</code> — Fast-forward Fox Theater into its 25-second upright staged rebuild.</li>
          <li><code>bako_cmd reset_all</code> — Restore Fox, Padre, Bakersfield Sign &amp; all 56 glass windows intact.</li>
        </ul>
      </div>
      <div class="chg-card">
        <h3>Interactive 3D Viewer (Zero Dependencies)</h3>
        <ul>
          <li><strong>File:</strong> <a href="./bakersfieldish_interactive.html"><code>bakersfieldish_interactive.html</code></a> (<code>13.54 MB</code>, inline WebGL2 + gzipped BSP2 + 1,019 WebP textures + colored <code>.lit</code> lightmaps).</li>
          <li><strong>Controls:</strong> <code>WASD</code> + mouse drag (or <code>F</code> PointerLock) free-fly, keys <code>1–8</code> landmark quick-teleports.</li>
          <li><strong>Live Destructibles:</strong> Click Fox, Padre, or Bakersfield Sign buttons to step through all <strong>3 progressive break stages</strong> + rolling boulders + dust + glass shatter right in-browser!</li>
        </ul>
      </div>
    </div>

    <div class="tbl-wrap">
      <table>
        <thead>
          <tr><th>Deliverable File</th><th>Type</th><th>Length</th><th>Size</th><th>Format / Verification</th></tr>
        </thead>
        <tbody>
          <tr><td><code>fox_destruct.mp4</code></td><td>3-Stage Destruction + Rebuild</td><td>55.5s</td><td>22.10 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>padre_destruct.mp4</code></td><td>3-Stage Implosion + Boulders</td><td>39.5s</td><td>17.71 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>sign_destruct.mp4</code></td><td>3-Stage Arch Break &amp; Topple</td><td>22.0s</td><td>9.77 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>glass_destruct.mp4</code></td><td>Shatterable Glass Showcase</td><td>12.4s</td><td>5.77 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>fox_orbit_{intact,collapsed}.mp4</code></td><td>360° Orbits (Fox)</td><td>15.6s / 16.4s</td><td>7.42 / 8.51 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>padre_orbit_{intact,collapsed}.mp4</code></td><td>360° Orbits (Padre)</td><td>15.6s / 16.5s</td><td>11.19 / 10.46 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>sign_orbit_{intact,collapsed}.mp4</code></td><td>360° Orbits (Sign)</td><td>15.6s / 16.4s</td><td>9.79 / 10.35 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><code>bakersfieldish_flythrough.mp4</code></td><td>Full Downtown Fly-Through</td><td>46.0s</td><td>30.78 MB</td><td>720p H.264 + AAC (<code>streams=2</code>)</td></tr>
          <tr><td><a href="./bakersfieldish_interactive.html"><code>bakersfieldish_interactive.html</code></a></td><td>Offline 3D WebGL2 Viewer</td><td>Interactive</td><td>13.54 MB</td><td>Single-file, 0 external deps (<code>file://</code> ready)</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    Bakersfield-ish · Remastered Post-Apocalyptic Downtown for BakersfieldQuake ·
    <a href="./bakersfieldish_interactive.html">Open Interactive 3D Map Viewer</a>
  </div>
</footer>

<div id="lb" role="dialog" aria-modal="true">
  <img id="lb-img" alt="Zoomed preview">
  <div id="lb-cap"></div>
</div>

<script>
const DATA = __SHOWCASE_JSON__;
const $ = (id) => document.getElementById(id);

// Lightbox
function openLb(src, cap) {
  $("lb-img").src = src;
  $("lb-cap").textContent = cap || "";
  $("lb").classList.add("open");
}
$("lb").onclick = () => $("lb").classList.remove("open");
addEventListener("keydown", (e) => { if (e.key === "Escape") $("lb").classList.remove("open"); });

// Hero
$("hero-img").src = DATA.hero;
$("hero-card").onclick = () => openLb(DATA.hero, "Bakersfield-ish — H Street Core Spine (Padre Hotel, Bakersfield Sign & 18th St Plaza)");

// Landmarks
const lmGrid = $("landmark-grid");
DATA.landmarks.forEach((lm) => {
  const card = document.createElement("article");
  card.className = "lm-card";
  card.innerHTML = `<img alt=""><div class="lm-body"><div class="lm-tag"></div><h3></h3><p></p></div>`;
  const img = card.querySelector("img");
  img.src = lm.img;
  img.alt = lm.title;
  img.onclick = () => openLb(lm.img, lm.title + " — " + lm.desc);
  card.querySelector(".lm-tag").textContent = lm.tag;
  card.querySelector("h3").textContent = lm.title;
  card.querySelector("p").textContent = lm.desc;
  lmGrid.appendChild(card);
});

// Interactive 3-Stage Gallery
let curSeq = "padre";
let curIdx = 0;

function renderSeq() {
  const seq = DATA.sequences[curSeq];
  if (curIdx < 0) curIdx = seq.frames.length - 1;
  if (curIdx >= seq.frames.length) curIdx = 0;
  const f = seq.frames[curIdx];
  $("stage-title").textContent = seq.title;
  $("stage-meta").textContent = seq.meta;
  $("stage-img").src = f.img;
  $("stage-img").onclick = () => openLb(f.img, `${seq.title} · ${f.label}: ${f.note}`);
  $("stage-lbl").textContent = f.label + ":";
  $("stage-note").textContent = f.note;

  const thEl = $("stage-thumbs");
  thEl.innerHTML = "";
  seq.frames.forEach((fr, idx) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "thumb" + (idx === curIdx ? " active" : "");
    b.innerHTML = `<img alt=""><span></span>`;
    b.querySelector("img").src = fr.img;
    b.querySelector("span").textContent = fr.label;
    b.onclick = () => { curIdx = idx; renderSeq(); };
    thEl.appendChild(b);
  });
}

document.querySelectorAll("#seq-tabs .tab-btn").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll("#seq-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    curSeq = btn.dataset.seq;
    curIdx = 0;
    renderSeq();
  };
});
$("btn-prev").onclick = () => { curIdx--; renderSeq(); };
$("btn-next").onclick = () => { curIdx++; renderSeq(); };
renderSeq();
</script>
</body>
</html>
"""


def verify_offline(path: Path) -> None:
    txt = path.read_text(encoding="utf-8")
    ext = re.findall(r"(?:src|href)\s*=\s*[\"']https?://", txt, re.I)
    assert not ext, f"Found external URL refs: {ext[:3]}"
    assert not re.search(r"\bfetch\s*\(", txt), "Found fetch() call in offline showcase HTML"
    assert not re.search(r"<script[^>]+type\s*=\s*[\"']module[\"']", txt, re.I), "Found ES module script tag"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build standalone offline Bakersfield-ish showcase HTML.")
    ap.add_argument("--out", type=Path, default=OUT_MAIN, help="Primary output path")
    ap.add_argument("--copy", type=Path, default=OUT_DOCS, help="Secondary docs copy path")
    args = ap.parse_args()

    data = build_showcase_data()
    json_str = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html_out = HTML_TEMPLATE.replace("__SHOWCASE_JSON__", json_str)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_out, encoding="utf-8")
    verify_offline(args.out)

    if args.copy and args.copy.resolve() != args.out.resolve():
        args.copy.parent.mkdir(parents=True, exist_ok=True)
        args.copy.write_text(html_out, encoding="utf-8")

    sz_mb = args.out.stat().st_size / (1024 * 1024)
    print(f"[done] Built standalone showcase HTML: {args.out} ({sz_mb:.2f} MB, 0 external deps)", flush=True)
    if args.copy:
        print(f"[done] Copied showcase HTML: {args.copy}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
