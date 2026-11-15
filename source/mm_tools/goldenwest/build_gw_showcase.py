"""build_gw_showcase.py — Generate self-contained Golden West Casino & Great Castle HTML Showcase.

Modeled on source/mm_tools/soi6/build_soi6_showcase.py + build_goldenwest_showcase_html.py.
Reads real build, export, audit, reference, and texture artifacts dynamically (never
hardcoding unverified results; shows PENDING badges for any audit not yet run):
  - goldenwest/out/compile_stats.json
  - goldenwest/out/web_export_stats.json
  - goldenwest.spots.json (maps/, goldenwest/out/, or out/maps/)
  - out/gw_ref_audit/ (sheets_html_190, REF_INVENTORY.md)
  - out/gc_ref_audit/ (sheets, images, GC_REF_INVENTORY.md)
  - goldenwest/out/audit1_refs.json + audit1_shots/*.png + audit1/*.png
  - goldenwest/out/audit2_*.json
  - goldenwest/out/audit3_nav_report.json + audit3_nav_map.png
  - goldenwest/out/audit4_perf_report.json (+ optional audit4_*.png)
  - goldenwest/out/audit5_report.json + audit5_*.png
  - goldenwest/out/AUDITS_LOG.md
  - BakersfieldQuake/textures/{gwc_*,{gwc_*}.png + progs/gw_*.png

Writes:
  - source/mm_tools/goldenwest/out/goldenwest_showcase.html (always; --local-only stops here)
  - G:/Quake/Combat/BakersfieldQuake/goldenwest_showcase.html
  - source/mm_tools/out/web/goldenwest/showcase.html
  - source/mm_tools/out/web/goldenwest_showcase.html
"""
from __future__ import annotations

import argparse
import base64
import html as htmllib
import io
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PIL import Image

GW_DIR = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(GW_DIR)
MOD_DIR = os.path.dirname(os.path.dirname(MM_TOOLS))
OUT_DIR = os.path.join(GW_DIR, "out")
WEB_OUT = os.path.join(MM_TOOLS, "out", "web", "goldenwest")
REF_AUDIT_DIR = os.path.join(MM_TOOLS, "out", "gw_ref_audit")
GC_REF_AUDIT_DIR = os.path.join(MM_TOOLS, "out", "gc_ref_audit")

LOCAL_HTML = os.path.join(OUT_DIR, "goldenwest_showcase.html")
ROOT_HTML = os.path.join(MOD_DIR, "goldenwest_showcase.html")
WEB_SHOWCASE = os.path.join(WEB_OUT, "showcase.html")
WEB_OUT_ROOT_SHOWCASE = os.path.join(MM_TOOLS, "out", "web", "goldenwest_showcase.html")

if GW_DIR not in sys.path:
    sys.path.insert(0, GW_DIR)

from gw_lib import (  # noqa: E402
    ADAMS_ST_Y,
    AMADOR_AVE_Y,
    BELLE_TERRACE_Y,
    CASINO_BOUNDS_FT,
    CASINO_LOT_FT,
    DELAWARE_ST_X,
    E_4TH_ST_Y,
    E_5TH_ST_Y,
    FOX_OFFSET_FT,
    GC_ALLEY_X,
    GC_BLDG_BOUNDS_FT,
    GC_LOT_FT,
    HY0,
    HY1,
    MARIPOSA_AVE_Y,
    ORIGIN_LATLON,
    PARCELS,
    SOUTH_ZONE_HY1,
    TRINITY_AVE_Y,
    UNION_MEDIAN_X,
    U_FT,
    U_M,
    WORLD_BOUNDS_FT,
    ZONE_BOUNDS_FT,
)

LIVE_VIEWER_URL = "https://bakersfield.larrywew.fun/goldenwest/"


def _read_json(path: str) -> Optional[dict]:
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"items": data}
    except Exception:
        return None


def _read_first_json(candidates: List[str]) -> Optional[dict]:
    for c in candidates:
        res = _read_json(c)
        if res is not None:
            return res
    return None


def _read_spots() -> List[dict]:
    candidates = [
        os.path.join(MOD_DIR, "maps", "goldenwest.spots.json"),
        os.path.join(OUT_DIR, "goldenwest.spots.json"),
        os.path.join(MM_TOOLS, "out", "maps", "goldenwest.spots.json"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    if not existing:
        return []
    newest = max(existing, key=os.path.getmtime)
    with open(newest, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("spots", [])
    return data if isinstance(data, list) else []


def _b64_image(path: str, max_w: int = 960, quality: int = 84) -> Optional[str]:
    """Encode image as compact data URI (JPEG for photos/renders, PNG for small sprites/maps)."""
    if not path or not os.path.isfile(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png" and os.path.getsize(path) <= 180 * 1024:
        with open(path, "rb") as f:
            raw = f.read()
        return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            if max_w and im.width > max_w:
                nh = max(1, int(round(im.height * (max_w / float(im.width)))))
                im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def _b64_png_swatch(path: str, max_px: int = 256) -> Optional[str]:
    if not path or not os.path.isfile(path):
        return None
    try:
        with Image.open(path) as im:
            if max(im.width, im.height) > max_px:
                im.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def _resolve_rel_path(rel_or_abs: str) -> str:
    if not rel_or_abs:
        return ""
    if os.path.isfile(rel_or_abs):
        return rel_or_abs
    for base in (OUT_DIR, MM_TOOLS, MOD_DIR, REF_AUDIT_DIR, GC_REF_AUDIT_DIR):
        cand = os.path.join(base, rel_or_abs)
        if os.path.isfile(cand):
            return cand
    return rel_or_abs


def _report_pass_state(report: Optional[dict]) -> Optional[bool]:
    """Infer PASS (True), FAIL (False), or indeterminate (None) across audit1..5 schemas."""
    if not report:
        return None
    for k in ("overall_pass", "passed", "pass"):
        if k in report and isinstance(report[k], bool):
            return report[k]
    status = str(report.get("status", "")).upper()
    if status == "PASS":
        return True
    if status == "FAIL":
        return False
    if "tarjan_sink_sccs" in report and isinstance(report.get("errors"), list):
        return len(report["errors"]) == 0 and report.get("tarjan_sink_sccs", 1) == 0
    if "wasm_pack" in report and "bsp_and_map" in report:
        wasm_ok = (report.get("wasm_pack") or {}).get("within_budget") is True
        web = report.get("browser_webgl") or {}
        dp = report.get("darkplaces") or {}
        web_ok = bool(web.get("skipped")) or (web.get("ran") is True and not web.get("bad_responses"))
        dp_ok = bool(dp.get("skipped")) or (dp.get("ran") is True)
        return wasm_ok and web_ok and dp_ok
    return None


def _audit_badge(report: Optional[dict]) -> str:
    if not report:
        return '<span class="badge pending">PENDING</span>'
    state = _report_pass_state(report)
    if state is True:
        return '<span class="badge pass">PASS</span>'
    if state is False:
        return '<span class="badge fail">FAIL</span>'
    return '<span class="badge info">LOGGED</span>'


def _format_audit_bullets(report: Optional[dict], fallback_msg: str) -> str:
    if not report:
        return f"<li>{htmllib.escape(fallback_msg)}</li>"
    items: List[str] = []
    for key in ("highlights", "bullets", "findings", "summary_lines"):
        vals = report.get(key)
        if isinstance(vals, list):
            items.extend(str(v) for v in vals if v)
    if isinstance(report.get("summary"), str) and report["summary"]:
        items.insert(0, report["summary"])

    # Audit 3 schema
    if "reachable_cells" in report:
        items.append(
            f"<b>Hull-1 Walk Grid:</b> {report.get('reachable_cells', 0):,} cells | "
            f"Strongly connected: {report.get('strongly_connected_cells', 0):,} | "
            f"Tarjan SCCs: {report.get('tarjan_scc_count', '?')} (sink SCCs: {report.get('tarjan_sink_sccs', '?')})"
        )
        items.append(
            f"<b>Zones &amp; Parity:</b> {report.get('zones_reached', '?')}/{report.get('zones_total', '?')} zones | "
            f"Web Hull-1 parity={report.get('web_hull1_parity')} | "
            f"Errors={len(report.get('errors') or [])}"
        )

    # Audit 4 schema
    if "wasm_pack" in report and "bsp_and_map" in report:
        wasm = report.get("wasm_pack") or {}
        web = report.get("browser_webgl") or {}
        dp = report.get("darkplaces") or {}
        items.append(
            f"<b>WASM Pack Budget:</b> {wasm.get('total_goldenwest_mb', '?')} / {wasm.get('wasm_budget_mb', '?')} MB "
            f"(within_budget={wasm.get('within_budget')}, in_server_cfg={wasm.get('goldenwest_in_server_cfg')})"
        )
        if web.get("ran"):
            items.append(
                f"<b>WebGL Bench:</b> cold load {web.get('cold_load_s', '?')}s | "
                f"transfer {web.get('total_transfer_mb', '?')} MB | "
                f"walk/jump FPS={(web.get('live_fps') or {}).get('walk_jump', {}).get('fps', '?')} | "
                f"fly FPS={(web.get('live_fps') or {}).get('fly', {}).get('fps', '?')}"
            )
        if dp.get("ran"):
            dp_fps = [s.get("fps") for s in (dp.get("spots") or []) if isinstance(s, dict) and "fps" in s]
            fps_rng = f"{min(dp_fps)}–{max(dp_fps)} FPS" if dp_fps else "ran"
            items.append(f"<b>Desktop DarkPlaces:</b> {fps_rng} across {len(dp.get('spots') or [])} viewpoints")

    # Audit 5 schema
    if "textures" in report and "lighting_lit" in report and "standalone_and_wasm" in report:
        for sec in ("textures", "lighting_lit", "webgl_interiors", "darkplaces_webcfg", "scale_and_signage", "standalone_and_wasm"):
            sub = report.get(sec)
            if isinstance(sub, dict):
                flag = sub.get("pass") if "pass" in sub else sub.get("ran")
                items.append(f"<b>{htmllib.escape(sec)}:</b> pass/ran={htmllib.escape(str(flag))}")

    if isinstance(report.get("checks"), dict):
        for ck, cv in list(report["checks"].items())[:8]:
            if isinstance(cv, dict) and "pass" in cv:
                items.append(f"<b>{htmllib.escape(str(ck))}:</b> {'PASS' if cv['pass'] else 'FAIL'}")
            else:
                items.append(f"<b>{htmllib.escape(str(ck))}:</b> {htmllib.escape(json.dumps(cv) if isinstance(cv, (dict, list)) else str(cv))}")
    if not items:
        compact = {k: v for k, v in report.items() if not isinstance(v, (dict, list)) or len(str(v)) < 120}
        for k, v in list(compact.items())[:8]:
            items.append(f"<b>{htmllib.escape(str(k))}:</b> {htmllib.escape(str(v))}")
    if not items:
        items.append("Report file found on disk (no summary lines recorded).")
    return "\n".join(
        f"<li>{item if '<b>' in item else htmllib.escape(item)}</li>"
        for item in items
    )


def _categorize_texture(stem: str, has_glow: bool, is_prop: bool) -> Tuple[str, str]:
    low = stem.lower()
    if is_prop:
        return "props", "3D Prop Skin"
    if low.startswith("{"):
        return "alpha", "Alpha Cutout"
    if any(k in low for k in ("asph", "road", "curb", "sdwk", "sidewalk", "median", "line", "cross", "dirt", "lot", "park", "bikelane", "utilart", "e4st", "e5st")):
        return "streets", "Streets & Curbs"
    if low.startswith("gwc_gc") or "great_castle" in low:
        return "greatcastle", "Great Castle"
    if any(k in low for k in ("sl_", "sun_", "ci_", "s8_", "pf_", "motel", "ramos", "compas", "carnitas", "redwood", "brick", "stucco", "metal", "dealtime", "bdeal", "reyes", "dgmrkt", "shamrock", "cledge", "hedge")):
        return "neighbors", "Neighbors & Motels"
    return "casino", "Casino & Neon"


def _collect_textures() -> List[dict]:
    items: List[dict] = []
    tex_dir = os.path.join(MOD_DIR, "textures")
    if os.path.isdir(tex_dir):
        files = sorted(os.listdir(tex_dir))
        file_set = set(files)
        for fn in files:
            low = fn.lower()
            if not low.endswith(".png") or low.endswith("_glow.png"):
                continue
            if not (low.startswith("gwc_") or low.startswith("{gwc_")):
                continue
            stem = fn[:-4]
            glow_fn = stem + "_glow.png"
            has_glow = glow_fn in file_set
            cat_id, cat_label = _categorize_texture(stem, has_glow, is_prop=False)
            full_path = os.path.join(tex_dir, fn)
            uri = _b64_png_swatch(full_path, max_px=220)
            if not uri:
                continue
            with Image.open(full_path) as im:
                dims = f"{im.width}x{im.height}"
            items.append({
                "name": stem,
                "dims": dims,
                "has_glow": has_glow,
                "cat": cat_id,
                "cat_label": cat_label,
                "uri": uri,
            })

    progs_dir = os.path.join(MOD_DIR, "progs")
    if os.path.isdir(progs_dir):
        for fn in sorted(os.listdir(progs_dir)):
            low = fn.lower()
            if low.endswith(".png") and low.startswith("gw_"):
                stem = fn[:-4]
                full_path = os.path.join(progs_dir, fn)
                uri = _b64_png_swatch(full_path, max_px=220)
                if not uri:
                    continue
                with Image.open(full_path) as im:
                    dims = f"{im.width}x{im.height}"
                items.append({
                    "name": f"progs/{stem}",
                    "dims": dims,
                    "has_glow": False,
                    "cat": "props",
                    "cat_label": "3D Prop Skin",
                    "uri": uri,
                })
    return items


def _collect_audit1_visuals(a1: Optional[dict]) -> Tuple[List[str], List[str]]:
    """Build side-by-side comparison cards and standalone capture cards."""
    pair_cards: List[str] = []
    extra_cards: List[str] = []
    used_shots = set()

    if a1:
        pairs = a1.get("pairs") or a1.get("comparisons") or a1.get("matches") or []
        for idx, p in enumerate(pairs, 1):
            if not isinstance(p, dict):
                continue
            title = str(p.get("title") or p.get("spot") or p.get("name") or f"Viewpoint {idx}")
            notes = str(p.get("notes") or p.get("caption") or p.get("desc") or "")
            ref_p = _resolve_rel_path(str(p.get("ref") or p.get("ref_path") or p.get("photo") or ""))
            shot_p = _resolve_rel_path(str(p.get("shot") or p.get("shot_path") or p.get("render") or ""))
            dp_p = _resolve_rel_path(str(p.get("dp_shot") or ""))
            if shot_p:
                used_shots.add(os.path.abspath(shot_p))
            ref_uri = _b64_image(ref_p, max_w=720)
            shot_uri = _b64_image(shot_p, max_w=720)
            dp_uri = _b64_image(dp_p, max_w=720) if dp_p and os.path.abspath(dp_p) != os.path.abspath(shot_p or "") else None
            if not (ref_uri or shot_uri or dp_uri):
                continue
            spot_q = urllib.parse.quote(str(p.get("spot_query") or p.get("spot") or ""))
            jump = (
                f'<a class="mini-btn" href="__VIEWER_URL__?spot={spot_q}&fly=1" target="_blank">Open Spot</a>'
                if spot_q else ""
            )
            dp_fig = (
                f'<figure><img src="{dp_uri}" alt="DarkPlaces"><figcaption>DarkPlaces Engine Render</figcaption></figure>'
                if dp_uri else ""
            )
            pair_cards.append(
                f"""<div class="pair-card">
  <div class="pair-head"><strong>{htmllib.escape(title)}</strong>{jump}</div>
  {f'<p class="pair-note">{htmllib.escape(notes)}</p>' if notes else ''}
  <div class="pair-imgs">
    <figure>{f'<img src="{ref_uri}" alt="Reference"><figcaption>Reference Photo</figcaption>' if ref_uri else '<div class="empty-img">No reference photo</div>'}</figure>
    <figure>{f'<img src="{shot_uri}" alt="Quake Render"><figcaption>1:1 Quake WebGL Render</figcaption>' if shot_uri else '<div class="empty-img">No capture yet</div>'}</figure>
    {dp_fig}
  </div>
</div>"""
            )

    for shot_dir in (os.path.join(OUT_DIR, "audit1_shots"), os.path.join(OUT_DIR, "audit1")):
        if not os.path.isdir(shot_dir):
            continue
        for fn in sorted(os.listdir(shot_dir)):
            if not fn.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            if os.path.basename(shot_dir) == "audit1" and not fn.lower().startswith("sheet_"):
                continue
            fp = os.path.join(shot_dir, fn)
            if os.path.abspath(fp) in used_shots:
                continue
            uri = _b64_image(fp, max_w=900)
            if not uri:
                continue
            label = os.path.splitext(fn)[0].replace("_", " ")
            extra_cards.append(
                f'<figure class="extra-card"><img src="{uri}" alt="{htmllib.escape(label)}">'
                f"<figcaption>{htmllib.escape(label)}</figcaption></figure>"
            )

    return pair_cards, extra_cards


def _collect_reference_sheets() -> Tuple[List[str], List[str]]:
    """Collect curated Great Castle (410 Union) and Golden West (1001 S Union) ref sheets."""
    gc_cards: List[str] = []
    gw_cards: List[str] = []

    gc_specs = [
        ("sheets/hero_maps_web.jpg", "Great Castle Hero Plates (#161–#166): Union Facade, Watchtower & Lantern Interior"),
        ("sheets/aerials.jpg", "Great Castle 410 Union Ave Aerial & Satellite Views (#167–#177)"),
        ("sheets/sv_sheet_01.jpg", "Great Castle Street View Sheet 01 (Rear Alley & E 5th)"),
        ("sheets/sv_sheet_05.jpg", "Great Castle Street View Sheet 05 (Union Ave & E 4th Signal)"),
        ("sheets/sv_sheet_08.jpg", "Great Castle Street View Sheet 08 (Pylon, West Facade & Annex)"),
        ("sheets/sv_sheet_10.jpg", "Great Castle Street View Sheet 10 (Reyes Tires, Deal Time & E 4th/5th)"),
    ]
    for rel, caption in gc_specs:
        fp = os.path.join(GC_REF_AUDIT_DIR, rel.replace("/", os.sep))
        uri = _b64_image(fp, max_w=780, quality=76)
        if uri:
            gc_cards.append(
                f'<figure class="extra-card"><img src="{uri}" alt="{htmllib.escape(caption)}">'
                f"<figcaption>{htmllib.escape(caption)}</figcaption></figure>"
            )

    gw_specs = [
        ("sheets_html_190/gwc_sheet_01.jpg", "Golden West Ref Sheet 01 (1001 S Union Casino Exterior)"),
        ("sheets_html_190/gwc_sheet_04.jpg", "Golden West Ref Sheet 04 (Rotunda & NE Portico)"),
        ("sheets_html_190/gwc_sheet_07.jpg", "Golden West Ref Sheet 07 (S Union Median & Neighbors)"),
        ("sheets_html_190/gwc_sheet_10.jpg", "Golden West Ref Sheet 10 (Interior Hall & Props)"),
    ]
    for rel, caption in gw_specs:
        fp = os.path.join(REF_AUDIT_DIR, rel.replace("/", os.sep))
        uri = _b64_image(fp, max_w=780, quality=76)
        if uri:
            gw_cards.append(
                f'<figure class="extra-card"><img src="{uri}" alt="{htmllib.escape(caption)}">'
                f"<figcaption>{htmllib.escape(caption)}</figcaption></figure>"
            )

    return gc_cards, gw_cards


def _render_html(
    compile_stats: Optional[dict],
    web_stats: Optional[dict],
    spots: List[dict],
    a1: Optional[dict],
    a2: Optional[dict],
    a3: Optional[dict],
    a4: Optional[dict],
    a5: Optional[dict],
    audits_log_md: str,
    textures: List[dict],
    pair_cards: List[str],
    extra_cards: List[str],
    gc_ref_cards: List[str],
    gw_ref_cards: List[str],
) -> str:
    bsp_info = (compile_stats or {}).get("bsp", {})
    bsp_mb = f"{bsp_info['size_bytes'] / (1024 * 1024):.2f} MB" if bsp_info.get("size_bytes") else "Pending compile"
    bsp_tex = str(bsp_info.get("texture_count", "Pending"))
    world_tris = f"{web_stats['world_triangles']:,}" if web_stats and "world_triangles" in web_stats else "Pending export"
    bundle_mb = (
        f"{web_stats['sizes_kb']['total_bundle_mb']} MB"
        if web_stats and isinstance(web_stats.get("sizes_kb"), dict) and "total_bundle_mb" in web_stats["sizes_kb"]
        else "Pending export"
    )
    draw_groups = str(web_stats.get("draw_groups", "Pending")) if web_stats else "Pending"
    hull_trees = str(web_stats.get("hull_trees", "Pending")) if web_stats else "Pending"
    prop_instances = str(web_stats.get("prop_instances", "0")) if web_stats else "Pending"
    tex_png_cnt = str(len(textures))

    north_spot_links: List[str] = []
    south_spot_links: List[str] = []
    north_y_u = SOUTH_ZONE_HY1 * U_FT
    north_tokens = ("gc_", "castle", "reyes", "deal_time", "dealtime", "e4th", "e5th", "e_4th", "e_5th", "shamrock", "onestop", "manila", "dg_")
    for sp in spots:
        name = str(sp.get("name", "Spot"))
        desc = str(sp.get("desc", ""))
        org = sp.get("origin") or sp.get("pos") or [0, 0, 0]
        q = urllib.parse.quote(name)
        org_txt = f"({org[0]:.0f}, {org[1]:.0f}, {org[2]:.0f}) u" if isinstance(org, list) and len(org) >= 3 else ""
        card = (
            f'<a class="spot-btn" href="__VIEWER_URL__?spot={q}" target="_blank">'
            f"<strong>{htmllib.escape(name)}</strong>"
            f"<span>{htmllib.escape(desc or org_txt)}</span></a>"
        )
        is_north = (
            (isinstance(org, list) and len(org) >= 2 and float(org[1]) >= north_y_u)
            or any(tok in name.lower() for tok in north_tokens)
        )
        (north_spot_links if is_north else south_spot_links).append(card)
    if not south_spot_links:
        south_spot_links.append('<p class="muted">Pending: compile goldenwest.spots.json to populate Golden West viewpoints.</p>')
    if not north_spot_links:
        north_spot_links.append('<p class="muted">Pending: compile goldenwest.spots.json with Great Castle northern spots.</p>')

    # Nav & Audit 5 figures
    nav_fig = ""
    nav_img_p = os.path.join(OUT_DIR, "audit3_nav_map.png")
    nav_uri = _b64_image(nav_img_p, max_w=960)
    if nav_uri:
        nav_fig = (
            f'<figure class="diag-fig"><img src="{nav_uri}" alt="Hull-1 Navigation Map">'
            f"<figcaption>Audit 3 Hull-1 (32&times;32&times;56 u) Navigation Connectivity Map</figcaption></figure>"
        )

    a4_figs: List[str] = []
    for fn in sorted(os.listdir(OUT_DIR)) if os.path.isdir(OUT_DIR) else []:
        if fn.lower().startswith("audit4_") and fn.lower().endswith((".png", ".jpg")):
            uri = _b64_image(os.path.join(OUT_DIR, fn), max_w=800)
            if uri:
                a4_figs.append(
                    f'<figure class="diag-fig"><img src="{uri}" alt="{htmllib.escape(fn)}">'
                    f"<figcaption>{htmllib.escape(fn)}</figcaption></figure>"
                )

    a5_figs: List[str] = []
    for fn in sorted(os.listdir(OUT_DIR)) if os.path.isdir(OUT_DIR) else []:
        if fn.lower().startswith("audit5_") and fn.lower().endswith((".png", ".jpg")):
            uri = _b64_image(os.path.join(OUT_DIR, fn), max_w=800)
            if uri:
                a5_figs.append(
                    f'<figure class="diag-fig"><img src="{uri}" alt="{htmllib.escape(fn)}">'
                    f"<figcaption>{htmllib.escape(fn)}</figcaption></figure>"
                )

    tex_cards: List[str] = []
    for t in textures:
        glow_badge = '<span class="tag glow">+Glow</span>' if t["has_glow"] else ""
        tex_cards.append(
            f'<div class="tex-card" data-cat="{htmllib.escape(t["cat"])}" '
            f'data-glow="{"1" if t["has_glow"] else "0"}" data-name="{htmllib.escape(t["name"].lower())}">'
            f'<img src="{t["uri"]}" alt="{htmllib.escape(t["name"])}">'
            f'<div class="tex-meta"><code>{htmllib.escape(t["name"])}</code>'
            f'<div class="tex-sub"><span>{htmllib.escape(t["dims"])}</span>'
            f'<span class="tag">{htmllib.escape(t["cat_label"])}</span>{glow_badge}</div></div></div>'
        )
    if not tex_cards:
        tex_cards.append('<p class="muted">Pending: run goldenwest/build_textures.py to stage textures/gwc_*.png.</p>')

    gis_rows = [
        ("Corridor World Bounds", f"{WORLD_BOUNDS_FT[0]:.0f}..{WORLD_BOUNDS_FT[2]:.0f}", f"{HY0:.0f}..{HY1:.0f}", f"South Golden West y&le;{SOUTH_ZONE_HY1:.0f} ft + North Great Castle extension {SOUTH_ZONE_HY1:.0f}..{HY1:.0f} ft"),
        ("Golden West Casino Parcel", f"{CASINO_LOT_FT[0]:.1f}..{CASINO_LOT_FT[2]:.1f}", f"{CASINO_LOT_FT[1]:.1f}..{CASINO_LOT_FT[3]:.1f}", "1001 S Union Ave compound & parking lot"),
        ("Casino Building Footprint", f"{CASINO_BOUNDS_FT[0]:.1f}..{CASINO_BOUNDS_FT[2]:.1f}", f"{CASINO_BOUNDS_FT[1]:.1f}..{CASINO_BOUNDS_FT[3]:.1f}", "26-vertex perimeter, rotunda, 45&deg; NE portico, enterable pit"),
        ("Great Castle Lot (410 Union)", f"{GC_LOT_FT[0]:.1f}..{GC_LOT_FT[2]:.1f}", f"{GC_LOT_FT[1]:.1f}..{GC_LOT_FT[3]:.1f}", "East side of S Union Ave between E 4th St & E 5th St, SE Annex & rear alley"),
        ("Great Castle Building", f"{GC_BLDG_BOUNDS_FT[0]:.1f}..{GC_BLDG_BOUNDS_FT[2]:.1f}", f"{GC_BLDG_BOUNDS_FT[1]:.1f}..{GC_BLDG_BOUNDS_FT[3]:.1f}", "Crenellated SW Watchtower, barrel-vault awning, carved vestibule, lantern dining, restrooms & BOH"),
        ("E 4th St / E 5th St / Alley", f"Alley X={GC_ALLEY_X[0]:.1f}..{GC_ALLEY_X[1]:.1f}", f"E4={E_4TH_ST_Y:.1f}, E5={E_5TH_ST_Y:.1f}", "Signalized E 4th St (4-way + sunset utilart), E 5th T-junction & rear service alley"),
        ("Deal Time / Reyes Tires / Alley E", f"{PARCELS['gc_deal_time'][0]:.1f}..{PARCELS['gc_alley_east'][2]:.1f}", f"{PARCELS['gc_deal_time'][1]:.1f}..{PARCELS['gc_reyes_tires'][3]:.1f}", "Deal Time Auto (SE E 4th), Reyes Tires / Y Mofles bay (NE E 5th) & East Alley warehouse/cottages"),
        ("Shamrock / One Stop / Manila / DG", f"{PARCELS['gc_west_4th_onestop'][0]:.1f}..{PARCELS['gc_west_manila_dg'][2]:.1f}", f"{PARCELS['gc_west_4th_onestop'][1]:.1f}..{PARCELS['gc_west_manila_dg'][3]:.1f}", "West Union northern blocks: Diamond Shamrock, One Stop, Manila Inn & DG market"),
        ("S Union Ave Brick Median", f"{UNION_MEDIAN_X[0]:.1f}..{UNION_MEDIAN_X[1]:.1f}", f"{WORLD_BOUNDS_FT[1]:.0f}..{WORLD_BOUNDS_FT[3]:.0f}", "3+3 divided CA-99 BUS with herringbone brick median & GIS palms"),
        ("E Belle Terrace Signal", f"{WORLD_BOUNDS_FT[0]:.0f}..{WORLD_BOUNDS_FT[2]:.0f}", f"{BELLE_TERRACE_Y:.1f}", "4-way mast-arm traffic signal & cross street"),
        ("Star-Liter Motor Motel", f"{PARCELS['star_liter_motel'][0]:.1f}..{PARCELS['star_liter_motel'][2]:.1f}", f"{PARCELS['star_liter_motel'][1]:.1f}..{PARCELS['star_liter_motel'][3]:.1f}", "East side of S Union opposite Casino"),
        ("Ramos Tires / Super 8", f"{PARCELS['ramos_tires'][0]:.1f}..{PARCELS['super8_motel'][2]:.1f}", f"{PARCELS['super8_motel'][1]:.1f}..{PARCELS['ramos_tires'][3]:.1f}", "West side south of Casino along S Union & Delaware"),
        ("Trinity / Mariposa / Adams / Amador", f"Delaware X={DELAWARE_ST_X:.1f}", f"T={TRINITY_AVE_Y:.1f}, M={MARIPOSA_AVE_Y:.1f}, Ad={ADAMS_ST_Y:.1f}, Am={AMADOR_AVE_Y:.1f}", "Surveyed Bakersfield residential & commercial cross streets"),
    ]
    gis_rows_html = "\n".join(
        f"<tr><td>{name}</td><td><code>{xr}</code></td><td><code>{yr}</code></td><td>{desc}</td></tr>"
        for name, xr, yr, desc in gis_rows
    )

    mod_file_map = {
        "streets": "gw_streets.py",
        "casino_ext": "gw_casino_ext.py",
        "casino_int": "gw_casino_int.py",
        "east_union": "gw_east_union.py",
        "west_union": "gw_west_union.py",
        "gc_ext": "gw_gc_ext.py",
        "gc_int": "gw_gc_int.py",
        "north_union": "gw_east_union.py + gw_west_union.py (y&ge;750)",
    }
    mod_rows_html_list: List[str] = []
    for zname, zinfo in ZONE_BOUNDS_FT.items():
        if not isinstance(zinfo, dict):
            continue
        if "bbox" in zinfo and isinstance(zinfo["bbox"], (list, tuple)) and len(zinfo["bbox"]) == 4:
            bx = zinfo["bbox"]
            span_txt = f"X {bx[0]:.0f}..{bx[2]:.0f}, Y {bx[1]:.0f}..{bx[3]:.0f} ft"
        elif "corridors" in zinfo and isinstance(zinfo["corridors"], (list, tuple)):
            span_txt = f"{len(zinfo['corridors'])} corridors (Y {HY0:.0f}..{HY1:.0f} ft)"
        else:
            span_txt = "corridor-wide"
        plist = zinfo.get("parcels") or []
        ptxt = f"{len(plist)} parcel(s): {', '.join(str(p) for p in plist[:4])}" + ("…" if len(plist) > 4 else "") if plist else "street corridors"
        mod_rows_html_list.append(
            f"<tr><td><code>{htmllib.escape(zname)}</code></td>"
            f"<td><code>{mod_file_map.get(zname, 'make_gw.py')}</code></td>"
            f"<td><code>{htmllib.escape(span_txt)}</code></td>"
            f"<td>{htmllib.escape(ptxt)}</td>"
            f"<td>{htmllib.escape(str(zinfo.get('summary', '')))}</td></tr>"
        )
    mod_rows_html = "\n".join(mod_rows_html_list)

    log_html = ""
    if audits_log_md.strip():
        log_html = (
            "<h2>Sequential Audit Log (<code>AUDITS_LOG.md</code>)</h2>\n"
            f'<pre class="audit-log">{htmllib.escape(audits_log_md)}</pre>'
        )

    built_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Golden West Casino &amp; Great Castle &middot; 1:1 Bakersfield Quake Showcase</title>
<style>
  :root {{
    --bg: #0f1216; --panel: #171c22; --panel2: #1f262e; --border: #2c3540;
    --ink: #eef2f7; --muted: #98a4b3; --gold: #f5b841; --teal: #38bdf8;
    --pass: #22c55e; --fail: #ef4444; --pend: #f59e0b;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, sans-serif; }}
  .wrap {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 64px; }}
  header.hero {{
    background: linear-gradient(135deg, #1b222c 0%, #12171e 100%);
    border: 1px solid var(--border); border-radius: 14px; padding: 28px; margin-bottom: 24px;
  }}
  .eyebrow {{ color: var(--gold); font-size: 12px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }}
  h1 {{ margin: 6px 0 10px; font-size: 32px; line-height: 1.15; }}
  h2 {{ margin: 34px 0 14px; font-size: 22px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  h3 {{ margin: 0 0 8px; font-size: 17px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  p.lead {{ color: var(--muted); max-width: 860px; margin: 0 0 18px; }}
  .cta-row {{ display: flex; flex-wrap: wrap; gap: 10px; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 8px;
    font-weight: 700; text-decoration: none; border: 1px solid var(--border); color: var(--ink); background: var(--panel2);
  }}
  .btn.primary {{ background: var(--gold); color: #111; border-color: var(--gold); }}
  .btn.secondary {{ background: #223042; border-color: #355070; color: #dbeafe; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(175px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .kpi {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }}
  .kpi strong {{ display: block; font-size: 20px; color: var(--gold); }}
  .kpi span {{ color: var(--muted); font-size: 12px; }}
  .audit-box {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; margin-bottom: 14px; }}
  .audit-box ul {{ margin: 8px 0 0; padding-left: 20px; color: #d5dde7; }}
  .badge {{ font-size: 11px; font-weight: 800; padding: 2px 9px; border-radius: 999px; letter-spacing: .05em; }}
  .badge.pass {{ background: rgba(34,197,94,.18); color: #86efac; border: 1px solid rgba(34,197,94,.45); }}
  .badge.fail {{ background: rgba(239,68,68,.18); color: #fca5a5; border: 1px solid rgba(239,68,68,.45); }}
  .badge.pending {{ background: rgba(245,158,11,.18); color: #fde68a; border: 1px solid rgba(245,158,11,.45); }}
  .badge.info {{ background: rgba(56,189,248,.18); color: #bae6fd; border: 1px solid rgba(56,189,248,.45); }}
  .spots-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(225px, 1fr)); gap: 10px; }}
  .spot-btn {{
    display: block; background: var(--panel); border: 1px solid var(--border); border-radius: 9px;
    padding: 11px 13px; text-decoration: none; color: var(--ink); transition: border-color .15s;
  }}
  .spot-btn:hover {{ border-color: var(--gold); }}
  .spot-btn strong {{ display: block; font-size: 14px; color: var(--gold); }}
  .spot-btn span {{ display: block; font-size: 12px; color: var(--muted); margin-top: 2px; }}
  .pair-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
  .pair-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 6px; }}
  .pair-note {{ color: var(--muted); font-size: 13px; margin: 0 0 10px; }}
  .pair-imgs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
  figure {{ margin: 0; background: #0c0e12; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  figure img {{ display: block; width: 100%; height: auto; }}
  figcaption {{ padding: 7px 10px; font-size: 12px; color: var(--muted); border-top: 1px solid var(--border); }}
  .mini-btn {{ font-size: 12px; font-weight: 700; color: var(--teal); text-decoration: none; border: 1px solid #355070; padding: 4px 10px; border-radius: 6px; }}
  .extra-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }}
  .diag-fig {{ margin-top: 12px; max-width: 820px; }}
  .filter-bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 14px; }}
  .fbtn {{
    background: var(--panel); color: var(--ink); border: 1px solid var(--border);
    border-radius: 999px; padding: 6px 13px; cursor: pointer; font-size: 13px; font-weight: 600;
  }}
  .fbtn.active {{ background: var(--gold); color: #111; border-color: var(--gold); }}
  #tex-search {{
    margin-left: auto; background: var(--panel); color: var(--ink); border: 1px solid var(--border);
    border-radius: 8px; padding: 6px 12px; min-width: 210px;
  }}
  .tex-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr)); gap: 11px; }}
  .tex-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 9px; overflow: hidden; display: flex; flex-direction: column; }}
  .tex-card img {{ width: 100%; height: 124px; object-fit: contain; background: repeating-conic-gradient(#1f262e 0% 25%, #161b21 0% 50%) 50% / 16px 16px; }}
  .tex-meta {{ padding: 8px 10px; font-size: 12px; border-top: 1px solid var(--border); }}
  .tex-meta code {{ display: block; color: var(--ink); font-size: 12px; word-break: break-all; margin-bottom: 4px; }}
  .tex-sub {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; color: var(--muted); font-size: 11px; }}
  .tag {{ background: #26303c; padding: 1px 6px; border-radius: 4px; color: #cbd5e1; }}
  .tag.glow {{ background: rgba(245,184,65,.2); color: var(--gold); }}
  table.gis {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; font-size: 13px; }}
  table.gis th, table.gis td {{ padding: 9px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
  table.gis th {{ background: var(--panel2); color: var(--gold); }}
  pre.audit-log {{ background: #0c0f13; border: 1px solid var(--border); border-radius: 10px; padding: 16px; overflow-x: auto; font-size: 12px; color: #cbd5e1; max-height: 440px; }}
  .muted {{ color: var(--muted); }}
  .empty-img {{ padding: 48px 16px; text-align: center; color: var(--muted); }}
  .spots-sub {{ margin: 18px 0 10px; font-size: 16px; color: var(--teal); }}
  details.ref-details {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; margin-bottom: 14px; }}
  details.ref-details summary {{ cursor: pointer; font-weight: 700; color: var(--gold); list-style: none; }}
  details.ref-details .extra-grid {{ margin-top: 12px; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="eyebrow">1:1 Bakersfield Quake Map &middot; {U_FT:.0f} u/ft ({U_M:.2f} u/m) &middot; Origin {ORIGIN_LATLON[0]:.6f}&deg;N, {ORIGIN_LATLON[1]:.6f}&deg;W</div>
    <h1>Golden West Casino &amp; Great Castle &middot; S Union Ave (<code>goldenwest.bsp</code>)</h1>
    <p class="lead">1:1 scale reconstruction of <b>Golden West Casino</b> (1001 S Union Ave: rotunda, NE portico &amp; enterable gaming floor) and <b>Great Castle Restaurant</b> (410 Union Ave: crenellated SW watchtower, barrel-vault awning, carved vestibule &amp; lantern dining hall), connected along S Union Ave (3+3 brick median, Amador Ave to E 5th St) with Deal Time Auto, Reyes Tires, DG market, Diamond Shamrock, Manila Inn, Star-Liter &amp; Country Inn motels, Super 8, Ramos Tires, and Carnitas Birria. Generated {built_str}.</p>
    <div class="cta-row">
      <a class="btn primary" href="__VIEWER_URL__" target="_blank">Play in Browser (WASD + Space + F)</a>
      <a class="btn secondary" href="__VIEWER_URL__?fly=1" target="_blank">Launch in Free-Fly Mode</a>
      <a class="btn" href="__PACK_URL__" download>Download Self-Contained Pack (<code>goldenwest_map_pack.zip</code>)</a>
      <a class="btn" href="{LIVE_VIEWER_URL}" target="_blank">Live VPS Mirror</a>
    </div>
  </header>

  <div class="kpis">
    <div class="kpi"><strong>{bsp_mb}</strong><span>Compiled BSP2 (<code>{bsp_tex}</code> textures)</span></div>
    <div class="kpi"><strong>{world_tris} tris</strong><span>WebGL World ({draw_groups} draw groups)</span></div>
    <div class="kpi"><strong>{hull_trees} Hull-1</strong><span>Exact Quake Clipnode Trees</span></div>
    <div class="kpi"><strong>{len(spots)} Spots</strong><span>Deep-Linked Viewpoints</span></div>
    <div class="kpi"><strong>{prop_instances} Props</strong><span>3D MD3 Prop Instances</span></div>
    <div class="kpi"><strong>{tex_png_cnt} Textures</strong><span>Staged <code>gwc_*</code> / <code>gw_*</code> PNGs</span></div>
    <div class="kpi"><strong>{bundle_mb}</strong><span>Total Three.js Bundle (<code>bright=1.00</code>)</span></div>
  </div>

  <h2>Sequential 5-Audit QA Verification</h2>

  <div class="audit-box">
    <h3>Audit 1: Side-by-Side Visual Comparison {_audit_badge(a1)}</h3>
    <ul>{_format_audit_bullets(a1, "Pending: run audit1_capture.py to generate side-by-side reference comparisons.")}</ul>
  </div>

  <div class="audit-box">
    <h3>Audit 2: Final Accuracy Audit (Real-World Layout &amp; Proportions) {_audit_badge(a2)}</h3>
    <ul>{_format_audit_bullets(a2, "Pending: run audit2_accuracy.py to verify street widths, parcel footprints, and signage accuracy.")}</ul>
  </div>

  <div class="audit-box">
    <h3>Audit 3: Collision &amp; Navigation Audit (Quake Hull-1 32&times;32&times;56 u) {_audit_badge(a3)}</h3>
    <ul>{_format_audit_bullets(a3, "Pending: run audit3_nav.py to verify doorways, stairs, interior reachability, and void containment.")}</ul>
    {nav_fig}
  </div>

  <div class="audit-box">
    <h3>Audit 4: Performance &amp; Browser Optimization Audit {_audit_badge(a4)}</h3>
    <ul>{_format_audit_bullets(a4, "Pending: run audit4_perf.py to benchmark clipnodes, VIS, WebGL draw calls, and FPS.")}</ul>
    {"".join(a4_figs)}
  </div>

  <div class="audit-box">
    <h3>Audit 5: Lighting, Materials &amp; Live Parity Compliance Audit {_audit_badge(a5)}</h3>
    <ul>{_format_audit_bullets(a5, "Pending: run audit5_lighting_materials.py to verify sunny luminance, emissives, WebGL bright=1.00 parity, and zero legacy bk_* textures.")}</ul>
    {"".join(a5_figs)}
  </div>

  <h2>Teleport Viewpoints ({len(spots)} Spots)</h2>
  <h3 class="spots-sub">Great Castle &amp; North Union ({len(north_spot_links)} Spots &middot; 410 Union Ave, E 4th &ndash; E 5th St)</h3>
  <div class="spots-grid">
    {"".join(north_spot_links)}
  </div>
  <h3 class="spots-sub">Golden West Casino &amp; South Union ({len(south_spot_links)} Spots &middot; 1001 S Union Ave, Belle Terrace &ndash; Amador Ave)</h3>
  <div class="spots-grid">
    {"".join(south_spot_links)}
  </div>

  <h2>Visual Comparisons &amp; Captures</h2>
  {"".join(pair_cards) if pair_cards else '<p class="muted">No side-by-side Audit 1 pairs recorded yet; showing available captures below.</p>'}
  <div class="extra-grid">
    {"".join(extra_cards) if extra_cards else '<p class="muted">No additional Audit 1 captures on disk yet.</p>'}
  </div>

  <h2>Reference Sheets &amp; Hero Plates (Great Castle &amp; Golden West)</h2>
  <details class="ref-details" open>
    <summary>Great Castle Restaurant (410 Union Ave) Reference Plates &amp; Street View Sheets ({len(gc_ref_cards)})</summary>
    <div class="extra-grid">
      {"".join(gc_ref_cards) if gc_ref_cards else '<p class="muted">No Great Castle reference sheets found in out/gc_ref_audit/sheets/.</p>'}
    </div>
  </details>
  <details class="ref-details">
    <summary>Golden West Casino (1001 S Union Ave) Reference Contact Sheets ({len(gw_ref_cards)})</summary>
    <div class="extra-grid">
      {"".join(gw_ref_cards) if gw_ref_cards else '<p class="muted">No Golden West reference sheets found in out/gw_ref_audit/sheets_html_190/.</p>'}
    </div>
  </details>

  <h2>Map Builder Modules &amp; Ownership Zones ({len(mod_rows_html_list)} Modules)</h2>
  <table class="gis">
    <thead><tr><th>Zone</th><th>Module</th><th>Bounds (ft)</th><th>Parcels</th><th>Ownership Summary</th></tr></thead>
    <tbody>{mod_rows_html}</tbody>
  </table>

  <h2>Bakersfield Surveyed GIS Anchors (12 u/ft, Fox Offset <code>{FOX_OFFSET_FT[0]:.1f}, {FOX_OFFSET_FT[1]:.1f} ft</code>)</h2>
  <table class="gis">
    <thead><tr><th>Anchor</th><th>X Range (ft)</th><th>Y Range (ft)</th><th>Notes</th></tr></thead>
    <tbody>{gis_rows_html}</tbody>
  </table>

  <h2>Staged Golden West &amp; Great Castle Textures &amp; 3D Prop Skins ({len(textures)})</h2>
  <div class="filter-bar">
    <button class="fbtn active" data-filter="all">All ({len(textures)})</button>
    <button class="fbtn" data-filter="casino">Casino &amp; Neon</button>
    <button class="fbtn" data-filter="greatcastle">Great Castle</button>
    <button class="fbtn" data-filter="streets">Streets &amp; Curbs</button>
    <button class="fbtn" data-filter="neighbors">Neighbors &amp; Motels</button>
    <button class="fbtn" data-filter="alpha">Alpha Cutouts</button>
    <button class="fbtn" data-filter="glow">Emissive Glow</button>
    <button class="fbtn" data-filter="props">3D Props</button>
    <input id="tex-search" type="search" placeholder="Filter textures by name...">
  </div>
  <div class="tex-grid" id="tex-grid">
    {"".join(tex_cards)}
  </div>

  {log_html}
</div>
<script>
const fbtns = Array.from(document.querySelectorAll(".fbtn"));
const cards = Array.from(document.querySelectorAll(".tex-card"));
const searchBox = document.getElementById("tex-search");
let activeCat = "all";
function applyTexFilter() {{
  const q = (searchBox.value || "").trim().toLowerCase();
  for (const c of cards) {{
    const catOk = activeCat === "all" || (activeCat === "glow" ? c.dataset.glow === "1" : c.dataset.cat === activeCat);
    const qOk = !q || (c.dataset.name || "").includes(q);
    c.style.display = (catOk && qOk) ? "" : "none";
  }}
}}
for (const b of fbtns) {{
  b.addEventListener("click", () => {{
    for (const x of fbtns) x.classList.remove("active");
    b.classList.add("active");
    activeCat = b.dataset.filter;
    applyTexFilter();
  }});
}}
if (searchBox) searchBox.addEventListener("input", applyTexFilter);
</script>
</body>
</html>
"""


def build_showcase(local_only: bool = False) -> List[str]:
    compile_stats = _read_json(os.path.join(OUT_DIR, "compile_stats.json"))
    web_stats = _read_json(os.path.join(OUT_DIR, "web_export_stats.json"))
    spots = _read_spots()

    a1 = _read_first_json([
        os.path.join(OUT_DIR, "audit1_manifest.json"),
        os.path.join(OUT_DIR, "audit1_report.json"),
        os.path.join(OUT_DIR, "audit1_refs.json"),
    ])
    a2 = _read_first_json([os.path.join(OUT_DIR, "audit2_accuracy_report.json"), os.path.join(OUT_DIR, "audit2_report.json")])
    a3 = _read_first_json([os.path.join(OUT_DIR, "audit3_nav_report.json"), os.path.join(OUT_DIR, "audit3_report.json")])
    a4 = _read_first_json([os.path.join(OUT_DIR, "audit4_perf_report.json"), os.path.join(OUT_DIR, "audit4_report.json")])
    a5 = _read_first_json([os.path.join(OUT_DIR, "audit5_report.json"), os.path.join(OUT_DIR, "audit5_lighting_report.json")])

    audits_log_md = ""
    for lp in (
        os.path.join(OUT_DIR, "AUDITS_LOG.md"),
        os.path.join(MOD_DIR, "AUDITS_LOG.md"),
    ):
        if os.path.isfile(lp):
            with open(lp, "r", encoding="utf-8") as f:
                audits_log_md = f.read()
            break

    textures = _collect_textures()
    pair_cards, extra_cards = _collect_audit1_visuals(a1)
    gc_ref_cards, gw_ref_cards = _collect_reference_sheets()
    template_html = _render_html(
        compile_stats=compile_stats,
        web_stats=web_stats,
        spots=spots,
        a1=a1,
        a2=a2,
        a3=a3,
        a4=a4,
        a5=a5,
        audits_log_md=audits_log_md,
        textures=textures,
        pair_cards=pair_cards,
        extra_cards=extra_cards,
        gc_ref_cards=gc_ref_cards,
        gw_ref_cards=gw_ref_cards,
    )

    # Map each destination path to viewer/pack URLs that resolve correctly in that context
    targets: List[Tuple[str, str, str]] = [
        (LOCAL_HTML, "../../out/web/goldenwest/index.html", "../../out/web/goldenwest/goldenwest_map_pack.zip"),
    ]
    if not local_only:
        targets.extend([
            (ROOT_HTML, "goldenwest/", "goldenwest/goldenwest_map_pack.zip"),
            (WEB_SHOWCASE, "index.html", "goldenwest_map_pack.zip"),
            (WEB_OUT_ROOT_SHOWCASE, "goldenwest/", "goldenwest/goldenwest_map_pack.zip"),
        ])

    written: List[str] = []
    for path, viewer_url, pack_url in targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out_html = template_html.replace("__VIEWER_URL__", viewer_url).replace("__PACK_URL__", pack_url)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out_html)
        sz_mb = os.path.getsize(path) / (1024.0 * 1024.0)
        print(f"[build_gw_showcase] Wrote showcase -> {path} ({sz_mb:.2f} MB)")
        written.append(path)
    return written


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build self-contained goldenwest_showcase.html")
    ap.add_argument(
        "--local-only",
        action="store_true",
        help="Write only to source/mm_tools/goldenwest/out/goldenwest_showcase.html",
    )
    args = ap.parse_args(argv)
    build_showcase(local_only=args.local_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
