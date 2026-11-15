"""Build self-contained 60-FPS HTML5 interactive Poop Gun All-Versions Simulator.

Packs all 8 weapon concept & forward sprite sheets (`work/c1_cannon/`..`work/c4_tuba/`
and `work/dookie_mk1/`..`work/dookie_mk4/`), shared mud/mist FX (`work/fx/`), and WAV
audio clips (`work/audio/`) into `G:\\Quake\\Combat\\BakersfieldQuake\\poop_gun_concepts.html`.

Usage:
    py -3.13 source/mm_tools/poop_gun/build_poop_concepts_html.py
"""
from __future__ import annotations

import argparse
import base64
import glob
import io
import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(HERE, "work")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_OUT_HTML = os.path.join(REPO_ROOT, "poop_gun_concepts.html")

MAX_ATLAS_DIM = 4096

CONCEPTS: List[Dict[str, Any]] = [
    {
        "id": "c1_cannon",
        "num": 1,
        "title": "THE DOOKIE BAZOOKA",
        "subtitle": "Original Concept 1 • Brass Plunger Cannon + 4 Arguing Heads + 14 Flies",
        "accent": "#d97706",
        "tagline": "Original brass & copper poop plunger cannon with 4 arguing heads, dual tricolor flags, PSI gauge & 14 orbiting flies.",
        "proj_style": "cannonball",
        "muzzle_norm": [0.19, 0.60],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "c2_throwguy",
        "num": 2,
        "title": "HUMAN BELLY-SLING",
        "subtitle": "Original Concept 2 • Hoist & Yeet a Squirming Bloke",
        "accent": "#ea580c",
        "tagline": "Original bare-handed concept: hoist an entire squirming bloke, squeeze his belly for a fart boost, and YEET him!",
        "proj_style": "yeet",
        "muzzle_norm": [0.50, 0.36],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "c3_paintball",
        "num": 3,
        "title": "POOP PAINTBALL HOPPER",
        "subtitle": "Original Concept 3 • 7-Head Gravity-Feed Face-Tube Marker",
        "accent": "#84cc16",
        "tagline": "Clear acrylic gravity-feed hopper packed with 7 squished rattling faces, tricolor flags, shivering PSI gauge & rapid-spin mud-face paintball orbs.",
        "proj_style": "paintball",
        "muzzle_norm": [0.36, 0.45],
        "tp_muzzle_norm": [0.28, 0.48],
    },
    {
        "id": "c4_tuba",
        "num": 4,
        "title": "The Porcelain Poop-Tuba",
        "subtitle": "Original Concept 4 • Toilet Mortar & Strangelove Torpedo",
        "accent": "#a855f7",
        "tagline": "Shoulder-mounted porcelain toilet-tuba mortar launching a Strangelove torpedo!",
        "proj_style": "torpedo",
        "muzzle_norm": [0.31, 0.51],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "dookie_mk1",
        "num": 5,
        "title": "MK-I: DOOKIE BAZOOKA",
        "subtitle": "Forward Tactical Plunger • 4-Head Glass Tube",
        "accent": "#f59e0b",
        "tagline": "Re-angled forward FPS aim with a giant crystal head chamber, 4 calmly arguing blokes, dual tricolor flags, PSI gauge & 4 tank-orbiting flies.",
        "proj_style": "sprint",
        "muzzle_norm": [0.29, 0.30],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "dookie_mk2",
        "num": 6,
        "title": "MK-II: TURBO FLUSHER",
        "subtitle": "Twin Plungers • 4-Head Poop-Soup Aquarium",
        "accent": "#22c55e",
        "tagline": "Doubled over-under plunger muzzles + dripping toilet-brush bayonet + MEGA STINK gauge + 4 calmly bobbing heads in sloshing poop soup!",
        "proj_style": "sprint",
        "muzzle_norm": [0.26, 0.26],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "dookie_mk3",
        "num": 7,
        "title": "MK-III: PORCELAIN THRONE",
        "subtitle": "Crowned Toilet Bazooka • 5 Dome Heads + Bowl Stowaway",
        "accent": "#38bdf8",
        "tagline": "Royally gilded porcelain toilet cannon! 5 readable heads in the crowned dome + stowaway bloke peeking out of the toilet bowl + 3 flags!",
        "proj_style": "sprint",
        "muzzle_norm": [0.26, 0.26],
        "tp_muzzle_norm": [0.46, 0.44],
    },
    {
        "id": "dookie_mk4",
        "num": 8,
        "title": "MK-IV: OMEGA BFG-9000",
        "subtitle": "Winning Design • 5 Reactor Heads + Slow Tank Flies + Hand-Waving Runner",
        "accent": "#ef4444",
        "tagline": "CHOSEN WINNER! Caged toxic reactor with 5 calm bobbing heads, Chakra turbine wheel, 4 flags, 7 slow flies orbiting the tank & ONE hand-waving bloke projectile!",
        "proj_style": "sprint",
        "muzzle_norm": [0.35, 0.26],
        "tp_muzzle_norm": [0.46, 0.44],
    },
]


def _natural_key(path: str) -> List[Any]:
    name = os.path.basename(path)
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", name)]


def _resolve_files(concept_dir: str, entries: List[str]) -> List[str]:
    out: List[str] = []
    for rel in entries:
        p = rel if os.path.isabs(rel) else os.path.join(concept_dir, rel)
        if os.path.isfile(p):
            out.append(p)
    return out


def _glob_sorted(concept_dir: str, patterns: List[str]) -> List[str]:
    found: List[str] = []
    seen = set()
    for pat in patterns:
        for p in sorted(glob.glob(os.path.join(concept_dir, pat)), key=_natural_key):
            bn = os.path.basename(p).lower()
            if bn.startswith("_") or "contact" in bn or "verify" in bn or "sheet" in bn:
                continue
            if os.path.isfile(p) and p not in seen:
                seen.add(p)
                found.append(p)
    return found


def pack_frames_to_webp_atlas(
    frame_paths: List[str],
    quality: int = 90,
    lossless: bool = False,
) -> Optional[Dict[str, Any]]:
    """Pack a list of RGBA image paths into one or more <=4096px WebP sprite sheets."""
    if not frame_paths:
        return None

    images: List[Image.Image] = []
    for p in frame_paths:
        with Image.open(p) as im:
            images.append(im.convert("RGBA"))

    fw, fh = images[0].size
    if fw <= 0 or fh <= 0:
        return None

    normalized: List[Image.Image] = []
    for im in images:
        if im.size != (fw, fh):
            im = im.resize((fw, fh), Image.Resampling.LANCZOS)
        normalized.append(im)

    max_cols = max(1, min(len(normalized), MAX_ATLAS_DIM // fw))
    max_rows = max(1, MAX_ATLAS_DIM // fh)
    per_page = max_cols * max_rows

    pages: List[Dict[str, Any]] = []
    for start in range(0, len(normalized), per_page):
        chunk = normalized[start : start + per_page]
        cols = min(max_cols, len(chunk))
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
        for idx, frame in enumerate(chunk):
            r = idx // cols
            c = idx % cols
            sheet.paste(frame, (c * fw, r * fh))

        buf = io.BytesIO()
        if lossless:
            sheet.save(buf, format="WEBP", lossless=True, method=4)
        else:
            sheet.save(buf, format="WEBP", quality=quality, method=4)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        pages.append(
            {
                "url": f"data:image/webp;base64,{b64}",
                "cols": cols,
                "rows": rows,
                "start": start,
                "count": len(chunk),
            }
        )

    return {
        "fw": fw,
        "fh": fh,
        "count": len(normalized),
        "pages": pages,
    }


def _discover_projectile(
    concept_dir: str,
    manifest: Dict[str, Any],
) -> Tuple[List[str], int, int]:
    """Return (flat_frame_paths, n_angles, frames_per_angle)."""
    proj_spec = manifest.get("proj")
    if isinstance(proj_spec, dict) and proj_spec.get("files"):
        raw_files = proj_spec["files"]
        flat: List[str] = []
        if raw_files and isinstance(raw_files[0], list):
            n_angles = len(raw_files)
            fpa = len(raw_files[0]) if n_angles else 1
            for row in raw_files:
                flat.extend(_resolve_files(concept_dir, row))
            return flat, max(1, n_angles), max(1, fpa)
        flat = _resolve_files(concept_dir, raw_files)
        n_angles = int(proj_spec.get("angles", 1))
        fpa = int(proj_spec.get("frames_per_angle", max(1, len(flat) // max(1, n_angles))))
        return flat, max(1, n_angles), max(1, fpa)
    if isinstance(proj_spec, list) and proj_spec:
        flat = _resolve_files(concept_dir, proj_spec)
        return flat, 1, max(1, len(flat))

    # Glob fallback: check proj_aXX_fYY.png first
    all_proj = _glob_sorted(concept_dir, ["proj_*.png", "proj_*.webp"])
    if not all_proj:
        return [], 1, 1

    grid_pat = re.compile(r"proj_a(\d+)_f(\d+)", re.IGNORECASE)
    grouped: Dict[int, List[Tuple[int, str]]] = {}
    for p in all_proj:
        m = grid_pat.search(os.path.basename(p))
        if m:
            ang = int(m.group(1))
            frm = int(m.group(2))
            grouped.setdefault(ang, []).append((frm, p))

    if grouped:
        angles_sorted = sorted(grouped.keys())
        fpa = max(len(v) for v in grouped.values())
        flat_grid: List[str] = []
        for ang in angles_sorted:
            row = [p for _, p in sorted(grouped[ang], key=lambda t: t[0])]
            while len(row) < fpa:
                row.append(row[-1])
            flat_grid.extend(row[:fpa])
        return flat_grid, len(angles_sorted), fpa

    # Check proj_00_00.png style
    pair_pat = re.compile(r"proj_(\d+)_(\d+)", re.IGNORECASE)
    grouped2: Dict[int, List[Tuple[int, str]]] = {}
    for p in all_proj:
        m = pair_pat.search(os.path.basename(p))
        if m:
            grouped2.setdefault(int(m.group(1)), []).append((int(m.group(2)), p))
    if len(grouped2) > 1:
        angles_sorted = sorted(grouped2.keys())
        fpa = max(len(v) for v in grouped2.values())
        flat_grid2: List[str] = []
        for ang in angles_sorted:
            row = [p for _, p in sorted(grouped2[ang], key=lambda t: t[0])]
            while len(row) < fpa:
                row.append(row[-1])
            flat_grid2.extend(row[:fpa])
        return flat_grid2, len(angles_sorted), fpa

    return all_proj, 1, len(all_proj)


def pack_concept(meta: Dict[str, Any], work_dir: str, quality: int = 90) -> Dict[str, Any]:
    """Load and pack all sequences for one weapon concept."""
    cid = meta["id"]
    cdir = os.path.join(work_dir, cid)
    manifest: Dict[str, Any] = {}
    manifest_path = os.path.join(cdir, "manifest.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            print(f"[warn] Failed to parse {manifest_path}: {exc}")

    def pick_seq(key: str, patterns: List[str]) -> List[str]:
        if isinstance(manifest.get(key), list) and manifest[key]:
            resolved = _resolve_files(cdir, manifest[key])
            if resolved:
                return resolved
        return _glob_sorted(cdir, patterns)

    vm_idle_paths = pick_seq("vm_idle", ["vm_idle_*.png", "vm_idle_*.webp"])
    vm_fire_paths = pick_seq("vm_fire", ["vm_fire_*.png", "vm_fire_*.webp"])
    vm_reload_paths = pick_seq("vm_reload", ["vm_reload_*.png", "vm_reload_*.webp"])

    # Fallback if worker emitted vm_000.png.. without split prefixes
    if not vm_idle_paths and os.path.isdir(cdir):
        generic_vm = _glob_sorted(cdir, ["vm_[0-9]*.png", "vm_[0-9]*.webp"])
        if generic_vm:
            vm_idle_paths = generic_vm

    tp_idle_paths = pick_seq("tp_idle", ["tp_idle_*.png", "tp_idle_*.webp"])
    tp_fire_paths = pick_seq("tp_fire", ["tp_fire_*.png", "tp_fire_*.webp"])
    tp_reload_paths = pick_seq("tp_reload", ["tp_reload_*.png", "tp_reload_*.webp"])
    if not tp_idle_paths and os.path.isdir(cdir):
        generic_tp = _glob_sorted(cdir, ["tp_[0-9]*.png", "tp_[0-9]*.webp"])
        if generic_tp:
            tp_idle_paths = generic_tp

    proj_paths, proj_angles, proj_fpa = _discover_projectile(cdir, manifest)

    sequences: Dict[str, Any] = {}
    seq_inputs = {
        "vm_idle": vm_idle_paths,
        "vm_fire": vm_fire_paths,
        "vm_reload": vm_reload_paths,
        "proj": proj_paths,
        "tp_idle": tp_idle_paths,
        "tp_fire": tp_fire_paths,
        "tp_reload": tp_reload_paths,
    }
    for sname, paths in seq_inputs.items():
        atlas = pack_frames_to_webp_atlas(paths, quality=quality)
        if atlas is not None and sname == "proj":
            atlas["angles"] = proj_angles
            atlas["fpa"] = proj_fpa
        sequences[sname] = atlas

    missing = [k for k in ("vm_idle", "vm_fire", "proj", "tp_idle", "tp_fire") if sequences[k] is None]
    ready = len(missing) == 0

    return {
        "id": cid,
        "num": meta["num"],
        "title": manifest.get("title", meta["title"]),
        "subtitle": manifest.get("subtitle", meta["subtitle"]),
        "accent": meta["accent"],
        "tagline": manifest.get("tagline", meta["tagline"]),
        "fps": int(manifest.get("fps", 60)),
        "proj_style": meta["proj_style"],
        "muzzle_norm": manifest.get("muzzle_norm", meta["muzzle_norm"]),
        "tp_muzzle_norm": manifest.get("tp_muzzle_norm", meta["tp_muzzle_norm"]),
        "ready": ready,
        "missing": missing,
        "sequences": sequences,
    }


def pack_shared_fx(work_dir: str, quality: int = 88) -> Dict[str, Any]:
    """Pack reusable mud splatter decals, mud globs, and stink mist puffs if present."""
    fx_candidates: List[str] = []
    for sub in ("fx", "mud_fx", "splats", "mist"):
        base = os.path.join(work_dir, sub)
        if os.path.isdir(base):
            fx_candidates.extend(glob.glob(os.path.join(base, "*.png")))

    splat_paths: List[str] = []
    glob_paths: List[str] = []
    mist_paths: List[str] = []
    seen = set()
    for p in sorted(fx_candidates, key=_natural_key):
        if p in seen:
            continue
        seen.add(p)
        bn = os.path.basename(p).lower()
        if bn.startswith("_") or "verify" in bn or "contact" in bn or "sheet" in bn or "enemy_shooter" in bn:
            continue
        if "mist" in bn or "cloud" in bn or "fume" in bn or "smoke" in bn:
            mist_paths.append(p)
        elif "glob" in bn or "mud" in bn:
            glob_paths.append(p)
        elif "splat" in bn or "poop" in bn:
            splat_paths.append(p)

    def _file_data_uri(path: str, mime: str) -> Optional[str]:
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as f:
            return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"

    return {
        "splats": pack_frames_to_webp_atlas(splat_paths, quality=quality),
        "globs": pack_frames_to_webp_atlas(glob_paths, quality=quality),
        "mist": pack_frames_to_webp_atlas(mist_paths, quality=quality),
        "bg_world": _file_data_uri(os.path.join(work_dir, "fx", "game_world_16x9.jpg"), "image/jpeg"),
        "bg_hud": _file_data_uri(os.path.join(work_dir, "fx", "game_hud_16x9.png"), "image/png"),
    }


def pack_audio(work_dir: str) -> Dict[str, str]:
    """Load WAV files from work/audio/ as base64 data URIs."""
    audio_dir = os.path.join(work_dir, "audio")
    clips: Dict[str, str] = {}
    if not os.path.isdir(audio_dir):
        return clips

    for p in sorted(glob.glob(os.path.join(audio_dir, "*.wav")), key=_natural_key):
        key = os.path.splitext(os.path.basename(p))[0]
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        clips[key] = f"data:audio/wav;base64,{b64}"
    return clips


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Bakersfield Quake — Poop Gun All 8 Versions 60-FPS Simulator</title>
<style>
  :root {
    --bg: #0f0d0b;
    --panel: #1a1612;
    --panel-2: #241e18;
    --border: #43372b;
    --text: #f3eadb;
    --muted: #a69884;
    --accent: #ff9933;
    --slime: #84cc16;
    --danger: #ef4444;
    --mud: #6b4423;
    --font-mono: ui-monospace, "Cascadia Mono", "Consolas", monospace;
    --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    background: radial-gradient(circle at 50% 0%, #241c15 0%, #0d0b09 70%);
    color: var(--text);
    font-family: var(--font-sans);
    min-height: 100vh;
  }
  .topbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 16px;
    background: linear-gradient(180deg, #241d17 0%, #16120e 100%);
    border-bottom: 2px solid var(--border);
    box-shadow: 0 4px 18px rgba(0,0,0,0.55);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .brand-badge {
    background: linear-gradient(135deg, #ff9933, #b45309);
    color: #120c06;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 0.08em;
    padding: 4px 8px;
    border-radius: 4px;
    text-transform: uppercase;
  }
  .brand h1 {
    margin: 0;
    font-size: 17px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 800;
  }
  .brand-sub {
    font-size: 11px;
    color: var(--muted);
    font-family: var(--font-mono);
  }
  .audio-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .tabs-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 10px 16px;
    background: #14110e;
    border-bottom: 1px solid var(--border);
  }
  .tab-btn {
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 13px;
    background: var(--panel);
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    font-weight: 700;
    font-size: 13px;
    transition: all 0.12s ease;
  }
  .tab-btn:hover { color: var(--text); border-color: #7c6751; background: var(--panel-2); }
  .tab-btn.active {
    color: #fff;
    background: linear-gradient(180deg, #33271c 0%, #211a13 100%);
    border-color: var(--tab-accent, var(--accent));
    box-shadow: 0 0 0 1px var(--tab-accent, var(--accent)), 0 4px 12px rgba(0,0,0,0.45);
  }
  .tab-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #666;
  }
  .tab-dot.ready { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
  .tab-dot.pending { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
  .tab-star {
    color: #fbbf24;
    font-size: 12px;
  }
  .winner-pill {
    background: #fbbf24;
    color: #181208;
    font-size: 10px;
    font-weight: 900;
    padding: 1px 5px;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .btn {
    background: #2b231b;
    color: var(--text);
    border: 1px solid #524334;
    border-radius: 5px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.1s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .btn:hover { background: #3a2f24; border-color: #826a52; }
  .btn:active { transform: translateY(1px); }
  .btn.primary {
    background: linear-gradient(180deg, #d97706 0%, #92400e 100%);
    border-color: #f59e0b;
    color: #fff;
  }
  .btn.primary:hover { filter: brightness(1.1); }
  .btn.active {
    background: #443322;
    border-color: var(--accent);
    color: #fff;
    box-shadow: inset 0 0 0 1px var(--accent);
  }
  .btn.danger {
    background: linear-gradient(180deg, #991b1b 0%, #7f1d1d 100%);
    border-color: #ef4444;
  }
  .btn.sm { padding: 4px 8px; font-size: 11px; }

  .main-wrap {
    max-width: 1440px;
    margin: 0 auto;
    padding: 14px 16px 28px;
  }

  /* Single Concept View */
  .concept-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 12px;
  }
  .concept-title-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }
  .concept-title-row h2 {
    margin: 0;
    font-size: 20px;
    letter-spacing: 0.03em;
  }
  .concept-sub {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
  }
  .concept-desc {
    margin: 4px 0 0;
    font-size: 13px;
    color: var(--muted);
  }

  .controls-strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 9px 14px;
    background: #17130f;
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 12px;
  }
  .ctrl-group {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .ctrl-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    font-weight: 800;
    margin-right: 4px;
  }
  .segmented {
    display: inline-flex;
    background: #0e0c0a;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px;
    gap: 2px;
  }
  .segmented .btn {
    border: none;
    background: transparent;
    border-radius: 4px;
  }
  .segmented .btn.active {
    background: #3b2d20;
    color: #fff;
    box-shadow: 0 0 0 1px var(--accent);
  }

  .arena-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 390px;
    gap: 14px;
    align-items: start;
  }
  @media (max-width: 1120px) {
    .arena-layout { grid-template-columns: 1fr; }
  }

  .viewport-card {
    background: #090807;
    border: 2px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    position: relative;
  }
  #arena-canvas {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 9;
    cursor: crosshair;
    background: #0b0907;
  }
  .arena-hud-bar {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #15110d;
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--muted);
  }
  .arena-hud-bar b { color: var(--text); }

  /* Inspector & Rating Sidebar */
  .side-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }
  .card h3 {
    margin: 0 0 10px;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .inspector-canvas-wrap {
    border: 1px solid #3c3126;
    border-radius: 6px;
    overflow: hidden;
    background: #111;
    margin-bottom: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .checkerboard {
    background-image:
      linear-gradient(45deg, #222 25%, transparent 25%),
      linear-gradient(-45deg, #222 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #222 75%),
      linear-gradient(-45deg, transparent 75%, #222 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0;
    background-color: #161616;
  }
  #inspector-canvas {
    display: block;
    width: 100%;
    max-height: 280px;
    object-fit: contain;
  }
  .scrubber-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 8px 0;
  }
  .scrubber-row input[type="range"] {
    flex: 1;
    accent-color: var(--accent);
  }
  .mono-meta {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
  }

  /* Rating widget */
  .stars {
    display: flex;
    gap: 4px;
    align-items: center;
  }
  .star-btn {
    background: #231c15;
    border: 1px solid #493b2d;
    color: #6b5e50;
    font-size: 18px;
    line-height: 1;
    padding: 4px 7px;
    border-radius: 4px;
    cursor: pointer;
  }
  .star-btn.lit { color: #fbbf24; border-color: #b45309; background: #2e2212; }
  .notes-box {
    width: 100%;
    margin-top: 8px;
    background: #100d0a;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 6px 8px;
    font-family: var(--font-sans);
    font-size: 12px;
    resize: vertical;
    min-height: 48px;
  }

  /* Compare All 4 Grid */
  .compare-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
  @media (max-width: 900px) {
    .compare-grid { grid-template-columns: 1fr; }
  }
  .compare-card {
    background: var(--panel);
    border: 2px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  .compare-card.is-winner {
    border-color: #fbbf24;
    box-shadow: 0 0 18px rgba(251, 191, 36, 0.2);
  }
  .compare-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 12px;
    background: #1d1712;
    border-bottom: 1px solid var(--border);
    gap: 8px;
  }
  .compare-canvas {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #0b0907;
    cursor: pointer;
  }
  .compare-foot {
    padding: 8px 12px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    border-top: 1px solid var(--border);
    font-size: 12px;
  }
  /* Weapon Model Position Adjuster */
  .adj-presets {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 8px;
  }
  .adj-grid {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .adj-row {
    display: grid;
    grid-template-columns: 78px 1fr 56px;
    align-items: center;
    gap: 6px;
    font-size: 11px;
  }
  .adj-row label {
    color: var(--muted);
    font-weight: 700;
    font-family: var(--font-mono);
  }
  .adj-row input[type="range"] {
    width: 100%;
    accent-color: var(--accent);
    margin: 0;
  }
  .adj-num {
    width: 100%;
    background: #100d0a;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 4px;
    font-family: var(--font-mono);
    font-size: 11px;
    text-align: right;
  }
  .adj-export {
    margin-top: 8px;
    background: #100d0a;
    border: 1px solid #3c3126;
    border-radius: 5px;
    padding: 6px 8px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: #cbd5e1;
    line-height: 1.4;
    word-break: break-word;
  }
  #arena-canvas.drag-mode { cursor: grab; }
  #arena-canvas.dragging { cursor: grabbing; }
  .arena-left-col {
    display: flex;
    flex-direction: column;
    gap: 14px;
    min-width: 0;
  }
  .audio-vote-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }
  .audio-vote-head h3 { margin: 0; }
  .audio-vote-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 10px;
  }
  .audio-pack-card {
    background: #17120d;
    border: 2px solid var(--border);
    border-radius: 7px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 7px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  .audio-pack-card.is-equipped {
    border-color: #22c55e;
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.18);
  }
  .audio-pack-card.is-winner {
    border-color: #fbbf24;
    box-shadow: 0 0 14px rgba(251, 191, 36, 0.24);
  }
  .audio-pack-title {
    font-size: 13px;
    font-weight: 800;
    color: var(--text);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
  }
  .audio-pack-sub {
    font-size: 11px;
    color: var(--muted);
    line-height: 1.35;
    min-height: 30px;
  }
  .audio-pack-btns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 5px;
  }
  .audio-pack-btns .btn.span2 {
    grid-column: span 2;
  }
  .audio-pack-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    padding-top: 6px;
    border-top: 1px solid #2e251d;
  }
  .audio-pack-foot .star-btn {
    padding: 3px 6px;
    font-size: 16px;
    cursor: pointer;
    position: relative;
    z-index: 2;
  }
  .audio-pack-btns .btn {
    justify-content: center;
    font-size: 11px;
    padding: 5px 6px;
  }
  .btn.voted-snd {
    background: #14532d;
    border-color: #22c55e;
    color: #bbf7d0;
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.28);
  }
  .btn.voted-win {
    background: linear-gradient(180deg, #b45309 0%, #78350f 100%);
    border-color: #fbbf24;
    color: #fef3c7;
    box-shadow: 0 0 10px rgba(251, 191, 36, 0.35);
  }
  .audio-toast {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(34, 197, 94, 0.22);
    border: 1px solid #4ade80;
    color: #86efac;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  .audio-toast.show { opacity: 1; }
  .audio-vote-summary {
    margin-top: 10px;
    padding: 8px 10px;
    background: #120e0a;
    border: 1px solid #352b21;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: #cbd5e1;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }
  .audio-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 999px;
    background: #272018;
    color: var(--muted);
    white-space: nowrap;
  }
  .audio-badge.eq { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(74,222,128,0.4); }
  .audio-badge.win { background: rgba(251,191,36,0.2); color: #fbbf24; border: 1px solid rgba(251,191,36,0.45); }
  .hidden { display: none !important; }
</style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <span class="brand-badge">Bakersfield Quake</span>
    <div>
      <h1>Poop Gun — All 8 Versions (Original 4 Concepts + MK-I to MK-IV)</h1>
      <div class="brand-sub" id="asset-summary">Initializing embedded sprite atlases & WAV audio...</div>
    </div>
  </div>
  <div class="audio-bar">
    <button class="btn" id="btn-test-fart" title="Preview Wew Cannon Windup, Fart Blast, Yell & Music">💨 Test Audio Mix</button>
    <button class="btn" id="btn-mute">🔊 Sound: ON</button>
    <button class="btn" id="btn-clean-walls">🧹 Clean Mud</button>
  </div>
</header>

<nav class="tabs-bar" id="tabs-bar"></nav>

<main class="main-wrap">
  <!-- SINGLE CONCEPT SIMULATOR VIEW -->
  <section id="single-view">
    <div class="concept-header">
      <div>
        <div class="concept-title-row">
          <h2 id="c-title">Design</h2>
          <span class="concept-sub" id="c-subtitle"></span>
          <span class="mono-meta" id="c-ready-badge"></span>
        </div>
        <p class="concept-desc" id="c-tagline"></p>
      </div>
      <div class="ctrl-group">
        <button class="btn primary" id="btn-pick-winner">🏆 Pick as Favorite</button>
      </div>
    </div>

    <div class="controls-strip">
      <div class="ctrl-group">
        <span class="ctrl-label">Perspective</span>
        <div class="segmented">
          <button class="btn active" id="mode-1p">🎯 1st-Person Arena</button>
          <button class="btn" id="mode-3p">💀 3rd-Person: Getting Shot At!</button>
        </div>
      </div>

      <div class="ctrl-group">
        <span class="ctrl-label">Speed</span>
        <div class="segmented" id="speed-group">
          <button class="btn" data-speed="0.25">0.25x</button>
          <button class="btn" data-speed="0.5">0.5x</button>
          <button class="btn active" data-speed="1">1.0x</button>
        </div>
      </div>

      <div class="ctrl-group">
        <button class="btn primary" id="btn-fire-now">⚡ HOLD / CLICK FIRE! (Space)</button>
        <button class="btn active" id="btn-bg-mode" title="Toggle between live Soi Cowboy + HUD, clean in-game world, or dark test corridor">🎮 Soi Cowboy + HUD</button>
        <button class="btn" id="btn-drag-vm" title="Drag weapon model directly on the arena canvas (or hold Alt+Drag anytime)">🖱️ Drag Weapon</button>
        <button class="btn" id="btn-vm-guides" title="Show sprite frame box, pivot & muzzle reticle">📐 Guides</button>
        <button class="btn hidden" id="btn-auto-fire">🔁 Enemy Auto-Fire: ON</button>
      </div>
    </div>

    <div class="arena-layout">
      <div class="arena-left-col">
        <div class="viewport-card">
          <canvas id="arena-canvas" width="960" height="540"></canvas>
          <div class="arena-hud-bar">
            <div>STATE: <b id="hud-state">IDLE</b> | SHOT COUNT: <b id="hud-shots">0</b> | WALL SPLATTERS: <b id="hud-splats">0</b></div>
            <div id="hud-hint">Move mouse to aim • Hold or Click / SPACE for windup & blast • A/D to strafe/dodge</div>
          </div>
        </div>

        <div id="audio-vote-mount-1p">
          <div class="card" id="audio-vote-card">
            <div class="audio-vote-head">
              <div>
                <h3>🥁💨 6 India / Fart / Poop Audio Packs — Play &amp; Vote <span class="audio-toast" id="audio-vote-toast">✓ Saved!</span></h3>
                <div class="mono-meta" id="audio-vote-status">Loading live sound mix...</div>
              </div>
              <div class="ctrl-group">
                <button type="button" class="btn sm primary" id="btn-test-live-mix" title="Test your currently mixed Windup + Fire on the gun">⚡ Test Live Mix</button>
                <button type="button" class="btn sm" id="btn-audio-orig" data-action="equip-orig" title="Equip Original Wew Windup + Classic Farts">🔊 Original Wew</button>
                <button type="button" class="btn sm" id="btn-clear-audio-vote" data-action="clear-votes" title="Reset sound votes">↺ Clear</button>
                <button type="button" class="btn sm primary" id="btn-copy-audio-vote" data-action="copy-votes">📋 Copy Votes</button>
              </div>
            </div>
            <div class="audio-vote-grid" id="audio-vote-grid"></div>
            <div class="audio-vote-summary" id="audio-vote-summary">Vote on any Windup, Fire sound, Stars, or Overall Best Pack above!</div>
          </div>
        </div>
      </div>

      <aside class="side-panel">
        <div class="card" id="vm-adjust-card">
          <h3>
            <span>🎛️ Weapon Model Adjuster</span>
            <span class="mono-meta" id="adj-summary">X:6% Y:2% S:78%</span>
          </h3>
          <div class="adj-presets">
            <button class="btn sm" data-vmpreset="quake-right">Quake Right</button>
            <button class="btn sm" data-vmpreset="center-low">Center Low</button>
            <button class="btn sm" data-vmpreset="hipfire">Hipfire</button>
            <button class="btn sm" data-vmpreset="reset">↺ Reset</button>
          </div>
          <div class="adj-grid">
            <div class="adj-row">
              <label for="adj-x">Pos X %</label>
              <input type="range" id="adj-x" min="-40" max="45" step="0.5" value="6">
              <input type="number" class="adj-num" id="adj-x-num" min="-40" max="45" step="0.5" value="6">
            </div>
            <div class="adj-row">
              <label for="adj-y">Pos Y %</label>
              <input type="range" id="adj-y" min="-25" max="45" step="0.5" value="2">
              <input type="number" class="adj-num" id="adj-y-num" min="-25" max="45" step="0.5" value="2">
            </div>
            <div class="adj-row">
              <label for="adj-scale">Scale %</label>
              <input type="range" id="adj-scale" min="35" max="135" step="1" value="78">
              <input type="number" class="adj-num" id="adj-scale-num" min="35" max="135" step="1" value="78">
            </div>
            <div class="adj-row">
              <label for="adj-rot">Rotate °</label>
              <input type="range" id="adj-rot" min="-35" max="35" step="0.5" value="0">
              <input type="number" class="adj-num" id="adj-rot-num" min="-35" max="35" step="0.5" value="0">
            </div>
            <div class="adj-row">
              <label for="adj-bob">Bob/Sway %</label>
              <input type="range" id="adj-bob" min="0" max="200" step="5" value="100">
              <input type="number" class="adj-num" id="adj-bob-num" min="0" max="200" step="5" value="100">
            </div>
            <div class="adj-row">
              <label for="adj-mx">Muzzle X</label>
              <input type="range" id="adj-mx" min="0.05" max="0.95" step="0.01" value="0.28">
              <input type="number" class="adj-num" id="adj-mx-num" min="0.05" max="0.95" step="0.01" value="0.28">
            </div>
            <div class="adj-row">
              <label for="adj-my">Muzzle Y</label>
              <input type="range" id="adj-my" min="0.05" max="0.95" step="0.01" value="0.26">
              <input type="number" class="adj-num" id="adj-my-num" min="0.05" max="0.95" step="0.01" value="0.26">
            </div>
            <div class="adj-row">
              <label for="adj-fov">Game FOV</label>
              <input type="range" id="adj-fov" min="75" max="125" step="1" value="111">
              <input type="number" class="adj-num" id="adj-fov-num" min="75" max="125" step="1" value="111">
            </div>
          </div>
          <div class="adj-presets" style="margin-top:6px;margin-bottom:4px;">
            <button class="btn sm" data-fovpreset="90">FOV 90</button>
            <button class="btn sm" data-fovpreset="100">FOV 100 (Def)</button>
            <button class="btn sm active" data-fovpreset="111">FOV 111 (Your Cfg)</button>
          </div>
          <div class="ctrl-group" style="margin-top:8px;justify-content:space-between;">
            <button class="btn sm" id="btn-adj-all" title="Apply these position & scale settings to all 8 weapon tabs">📌 Apply to All 8</button>
            <button class="btn sm primary" id="btn-adj-copy">📋 Copy Values</button>
          </div>
          <div class="adj-export" id="adj-export"></div>
        </div>

        <div class="card">
          <h3>
            <span>🔬 Frame Inspector</span>
            <span class="mono-meta" id="insp-dims">0×0</span>
          </h3>
          <div class="ctrl-group" style="margin-bottom: 8px;">
            <select id="insp-seq" class="btn" style="flex:1;"></select>
            <button class="btn sm active" id="insp-checker" title="Toggle alpha checkerboard">Checker</button>
            <button class="btn sm" id="insp-zoom" title="Cycle zoom">1x</button>
          </div>
          <div class="inspector-canvas-wrap checkerboard" id="insp-wrap">
            <canvas id="inspector-canvas" width="420" height="360"></canvas>
          </div>
          <div class="ctrl-group" style="justify-content: space-between;">
            <div class="ctrl-group">
              <button class="btn sm" id="insp-prev">◀</button>
              <button class="btn sm primary" id="insp-play">⏸ Pause</button>
              <button class="btn sm" id="insp-next">▶</button>
            </div>
            <div class="ctrl-group hidden" id="insp-angle-wrap">
              <span class="ctrl-label">Angle</span>
              <input type="range" id="insp-angle" min="0" max="15" value="0" style="width:80px;" />
              <span class="mono-meta" id="insp-angle-lbl">0°</span>
            </div>
          </div>
          <div class="scrubber-row">
            <input type="range" id="insp-scrub" min="0" max="0" value="0" />
          </div>
          <div class="mono-meta">
            <span id="insp-frame-lbl">Frame 0 / 0</span>
            <span id="insp-fps-lbl">60 FPS × 1.00</span>
          </div>
        </div>

        <div class="card">
          <h3>
            <span>⭐ Design Rating & Verdict</span>
            <span class="mono-meta" id="rating-lbl">Unrated</span>
          </h3>
          <div class="stars" id="rating-stars">
            <button class="star-btn" data-val="1">★</button>
            <button class="star-btn" data-val="2">★</button>
            <button class="star-btn" data-val="3">★</button>
            <button class="star-btn" data-val="4">★</button>
            <button class="star-btn" data-val="5">★</button>
          </div>
          <textarea class="notes-box" id="rating-notes" placeholder="Notes on silhouette, flags, flies, head comedy, projectile readability..."></textarea>
        </div>
      </aside>
    </div>
  </section>

  <!-- COMPARE ALL 8 SIDE-BY-SIDE VIEW -->
  <section id="compare-view" class="hidden">
    <div class="controls-strip">
      <div class="ctrl-group">
        <span class="ctrl-label">Compare Mode</span>
        <div class="segmented" id="cmp-mode-group">
          <button class="btn active" data-cmode="1p">🎯 1st-Person Viewmodels</button>
          <button class="btn" data-cmode="3p">💀 3rd-Person Getting Shot At</button>
          <button class="btn" data-cmode="proj">🚀 Projectile Spin</button>
        </div>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Speed</span>
        <div class="segmented" id="cmp-speed-group">
          <button class="btn" data-cspeed="0.25">0.25x</button>
          <button class="btn" data-cspeed="0.5">0.5x</button>
          <button class="btn active" data-cspeed="1">1.0x</button>
        </div>
      </div>
      <div class="ctrl-group">
        <button class="btn primary" id="btn-fire-all">💥 FIRE ALL 8 AT ONCE!</button>
      </div>
    </div>
    <div class="compare-grid" id="compare-grid"></div>
    <div id="audio-vote-mount-cmp" style="margin-top:14px;"></div>
  </section>
</main>

<!-- Embedded Audio Tags for zero-missing-asset DOM inspection + AudioContext decoding -->
<div id="embedded-audio-tags" class="hidden">
__AUDIO_TAGS__
</div>

<script>
const CONCEPTS = __CONCEPTS_JSON__;
const SHARED_FX = __FX_JSON__;

// ---------------------------------------------------------------------------
// 1. Sprite Atlas Loader & Blitter
// ---------------------------------------------------------------------------
const AtlasStore = {
  totalPages: 0,
  loadedPages: 0,
  init() {
    const loadPage = (page) => {
      this.totalPages++;
      const img = new Image();
      img.onload = () => { page._img = img; this.loadedPages++; };
      img.onerror = () => { this.loadedPages++; };
      img.src = page.url;
    };
    for (const c of CONCEPTS) {
      for (const seq of Object.values(c.sequences)) {
        if (!seq || !seq.pages) continue;
        for (const p of seq.pages) loadPage(p);
      }
    }
    for (const seq of Object.values(SHARED_FX)) {
      if (!seq || !seq.pages) continue;
      for (const p of seq.pages) loadPage(p);
    }
    const loadStandalone = (dataUri, propName) => {
      if (!dataUri) return;
      this.totalPages++;
      const img = new Image();
      img.onload = () => { SHARED_FX[propName] = img; this.loadedPages++; };
      img.onerror = () => { this.loadedPages++; };
      img.src = dataUri;
    };
    loadStandalone(SHARED_FX.bg_world, '_bgWorldImg');
    loadStandalone(SHARED_FX.bg_hud, '_bgHudImg');
  },
  drawFrame(ctx, atlas, frameIdx, dx, dy, dw, dh) {
    if (!atlas || !atlas.pages || atlas.count <= 0) return false;
    const idx = ((frameIdx % atlas.count) + atlas.count) % atlas.count;
    let targetPage = null;
    for (const p of atlas.pages) {
      if (idx >= p.start && idx < p.start + p.count) {
        targetPage = p;
        break;
      }
    }
    if (!targetPage || !targetPage._img) return false;
    const local = idx - targetPage.start;
    const col = local % targetPage.cols;
    const row = Math.floor(local / targetPage.cols);
    ctx.drawImage(
      targetPage._img,
      col * atlas.fw,
      row * atlas.fh,
      atlas.fw,
      atlas.fh,
      dx,
      dy,
      dw,
      dh
    );
    return true;
  },
  drawProj(ctx, atlas, angleIdx, frameIdx, dx, dy, dw, dh) {
    if (!atlas || atlas.count <= 0) return false;
    const angles = atlas.angles || 1;
    const fpa = atlas.fpa || atlas.count;
    const a = ((angleIdx % angles) + angles) % angles;
    const f = ((frameIdx % fpa) + fpa) % fpa;
    return this.drawFrame(ctx, atlas, a * fpa + f, dx, dy, dw, dh);
  }
};

// ---------------------------------------------------------------------------
// 2. Warm-Mastered Web Audio API SFX + Spatial Projectile Tracker Engine
// ---------------------------------------------------------------------------
const AudioFX = {
  ctx: null,
  masterGain: null,
  compressor: null,
  buffers: {},
  muted: false,
  decoded: false,
  decodePromise: null,
  activeHandles: new Set(),
  predecode() {
    if (this.decoded) return this.decodePromise;
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    const decCtx = OAC ? new OAC(1, 44100, 44100) : this.ctx;
    if (!decCtx) return null;
    this.decoded = true;
    this.decodePromise = this.decodeDomTags(decCtx);
    return this.decodePromise;
  },
  ensureCtx() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) {
        this.ctx = new AC();
        this.compressor = this.ctx.createDynamicsCompressor();
        this.compressor.threshold.value = -16;
        this.compressor.knee.value = 18;
        this.compressor.ratio.value = 4;
        this.compressor.attack.value = 0.008;
        this.compressor.release.value = 0.18;
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.value = 0.82;
        this.compressor.connect(this.masterGain);
        this.masterGain.connect(this.ctx.destination);
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    if (!this.decoded) {
      this.predecode();
    }
  },
  getOutNode() {
    return this.compressor || (this.ctx ? this.ctx.destination : null);
  },
  async decodeDomTags(decCtx) {
    const useCtx = decCtx || this.ctx;
    if (!useCtx) return;
    const tags = [...document.querySelectorAll('#embedded-audio-tags audio[data-sfx]')];
    // Decode active windup/fire variants first so first click responds immediately
    const priority = new Set([
      'windup_v1', 'fire_v1', 'windup_v2', 'fire_v2', 'windup_v3', 'fire_v3',
      'windup_v4', 'fire_v4', 'windup_v5', 'fire_v5', 'windup_v6', 'fire_v6', 'windup_wew'
    ]);
    tags.sort((a, b) => (priority.has(a.dataset.sfx) ? -1 : priority.has(b.dataset.sfx) ? 1 : 0));
    await Promise.all(tags.map(async (el) => {
      const key = el.dataset.sfx;
      const src = el.getAttribute('src') || '';
      if (!src.startsWith('data:audio') || this.buffers[key]) return;
      try {
        const b64 = src.split(',')[1];
        const bin = atob(b64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const buf = await useCtx.decodeAudioData(bytes.buffer);
        this.buffers[key] = buf;
      } catch (e) {}
    }));
  },
  stopAllActive() {
    for (const h of [...this.activeHandles]) {
      if (h && h.stop) h.stop(0.05);
    }
    this.activeHandles.clear();
  },
  playKey(key, { volume = 0.8, rate = 1.0, pan = 0.0, delay = 0 } = {}) {
    if (this.muted) return false;
    this.ensureCtx();
    const buf = this.buffers[key];
    const out = this.getOutNode();
    if (!this.ctx || !buf || !out) return false;
    const now = this.ctx.currentTime + delay;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = Math.max(0.4, Math.min(1.6, rate));
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(volume, now + 0.014);
    if (this.ctx.createStereoPanner) {
      const panner = this.ctx.createStereoPanner();
      panner.pan.value = Math.max(-0.95, Math.min(0.95, pan));
      src.connect(gain);
      gain.connect(panner);
      panner.connect(out);
    } else {
      src.connect(gain);
      gain.connect(out);
    }
    src.start(now);
    return true;
  },
  previewTimers: [],
  previewTrackerIv: null,
  stopPreview() {
    while (this.previewTimers.length) clearTimeout(this.previewTimers.pop());
    if (this.previewTrackerIv) {
      clearInterval(this.previewTrackerIv);
      this.previewTrackerIv = null;
    }
  },
  getActiveWindupPack() {
    return AUDIO_PACKS.find(p => p.id === (AudioVote.data.equippedWindup || AudioVote.data.equipped)) || AUDIO_PACKS[0];
  },
  getActiveFirePack() {
    return AUDIO_PACKS.find(p => p.id === (AudioVote.data.equippedFire || AudioVote.data.equipped)) || AUDIO_PACKS[0];
  },
  getActivePack() {
    return this.getActiveWindupPack();
  },
  startWindup(pan = 0, speed = 1.0, keyOverride = null) {
    if (this.muted) return null;
    this.ensureCtx();
    const pack = this.getActiveWindupPack();
    const wKey = keyOverride || pack.windup || 'windup_wew';
    const buf = this.buffers[wKey] || this.buffers['windup_wew'];
    const out = this.getOutNode();
    if (!this.ctx || !buf || !out) return null;
    const now = this.ctx.currentTime;
    const rate = speed < 1.0 ? Math.max(0.6, 0.72 + speed * 0.28) : 1.0;
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.loop = false;
    src.playbackRate.value = rate;
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(0.72, now + 0.045);
    const lpf = this.ctx.createBiquadFilter();
    lpf.type = 'lowpass';
    lpf.frequency.value = 3400;
    let panner = null;
    src.connect(lpf);
    lpf.connect(gain);
    if (this.ctx.createStereoPanner) {
      panner = this.ctx.createStereoPanner();
      panner.pan.value = Math.max(-0.95, Math.min(0.95, pan));
      gain.connect(panner);
      panner.connect(out);
    } else {
      gain.connect(out);
    }
    src.start(now);
    let stopped = false;
    const handle = {
      setPan: (p) => {
        if (panner && this.ctx && !stopped) {
          panner.pan.setTargetAtTime(Math.max(-0.95, Math.min(0.95, p)), this.ctx.currentTime, 0.03);
        }
      },
      stop: (fadeS = 0.035) => {
        if (stopped || !this.ctx) return;
        stopped = true;
        this.activeHandles.delete(handle);
        const t = this.ctx.currentTime;
        try {
          gain.gain.cancelScheduledValues(t);
          gain.gain.setValueAtTime(Math.max(0.0001, gain.gain.value), t);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + fadeS);
          src.stop(t + fadeS + 0.02);
        } catch (e) {}
      }
    };
    this.activeHandles.add(handle);
    return handle;
  },
  synthFart(pan = 0, rate = 1.0) {
    if (this.muted) return;
    this.ensureCtx();
    const out = this.getOutNode();
    if (!this.ctx || !out) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(105 * rate, now);
    osc.frequency.exponentialRampToValueAtTime(46 * rate, now + 0.38 / rate);
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.32, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.44 / rate);
    osc.connect(gain);
    gain.connect(out);
    osc.start(now);
    osc.stop(now + 0.48 / rate);
  },
  playFartBlast(pan = 0, speed = 1.0, keyOverride = null) {
    const rate = speed < 1.0 ? Math.max(0.55, speed + 0.30) : 1.0;
    let pick = null;
    if (typeof keyOverride === 'string' && this.buffers[keyOverride]) {
      pick = keyOverride;
    } else if (Array.isArray(keyOverride)) {
      const choices = keyOverride.filter(k => this.buffers[k]);
      if (choices.length) pick = choices[Math.floor(Math.random() * choices.length)];
    } else {
      const pack = this.getActiveFirePack();
      if (Array.isArray(pack.fire)) {
        const farts = pack.fire.filter(k => this.buffers[k]);
        if (farts.length) pick = farts[Math.floor(Math.random() * farts.length)];
      } else if (pack.fire && this.buffers[pack.fire]) {
        pick = pack.fire;
      }
      if (!pick) {
        const farts = ['fart_1', 'fart_2', 'fart_3', 'fart_4'].filter(k => this.buffers[k]);
        if (farts.length) pick = farts[Math.floor(Math.random() * farts.length)];
      }
    }
    if (pick) {
      this.playKey(pick, { volume: 0.90, rate: rate * (0.97 + Math.random() * 0.06), pan });
    } else {
      this.synthFart(pan, rate);
    }
  },
  startProjectileTracker(pan = 0, z = 1.0, dir = 'away', speed = 1.0) {
    if (this.muted) return null;
    this.ensureCtx();
    const out = this.getOutNode();
    if (!this.ctx || !out) return null;
    const now = this.ctx.currentTime;
    const rate = speed < 1.0 ? Math.max(0.62, speed + 0.32) : 1.0;

    const makeChannel = (bufKey, loop, delayS, initGain, initCutoff) => {
      const buf = this.buffers[bufKey];
      if (!buf) return null;
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = loop;
      src.playbackRate.value = loop ? 1.0 : rate * (0.97 + Math.random() * 0.06);
      const lpf = this.ctx.createBiquadFilter();
      lpf.type = 'lowpass';
      lpf.frequency.value = initCutoff;
      const gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.0001, now + delayS);
      gain.gain.linearRampToValueAtTime(initGain, now + delayS + 0.05);
      let panner = null;
      src.connect(lpf);
      lpf.connect(gain);
      if (this.ctx.createStereoPanner) {
        panner = this.ctx.createStereoPanner();
        panner.pan.setValueAtTime(Math.max(-0.95, Math.min(0.95, pan)), now);
        gain.connect(panner);
        panner.connect(out);
      } else {
        gain.connect(out);
      }
      src.start(now + delayS);
      return { src, lpf, gain, panner };
    };

    const sp = this._spatialParams(z, dir);
    const yellKeys = ['yell_1', 'yell_2', 'yell_3', 'wc_scream'].filter(k => this.buffers[k]);
    const yPick = yellKeys.length ? yellKeys[Math.floor(Math.random() * yellKeys.length)] : null;
    const yellCh = yPick ? makeChannel(yPick, true, 0.04, sp.yellGain, sp.cutoff) : null;
    const musicCh = this.buffers['proj_music']
      ? makeChannel('proj_music', true, 0.02, sp.musicGain, sp.cutoff)
      : null;

    let stopped = false;
    const handle = {
      update: (newPan, newZ) => {
        if (stopped || !this.ctx) return;
        const p = Math.max(-0.95, Math.min(0.95, newPan));
        const par = this._spatialParams(newZ, dir);
        const t = this.ctx.currentTime;
        if (yellCh) {
          yellCh.gain.gain.setTargetAtTime(par.yellGain, t, 0.045);
          yellCh.lpf.frequency.setTargetAtTime(par.cutoff, t, 0.05);
          if (yellCh.panner) yellCh.panner.pan.setTargetAtTime(p, t, 0.035);
        }
        if (musicCh) {
          musicCh.gain.gain.setTargetAtTime(par.musicGain, t, 0.045);
          musicCh.lpf.frequency.setTargetAtTime(par.cutoff, t, 0.05);
          if (musicCh.panner) musicCh.panner.pan.setTargetAtTime(p, t, 0.035);
        }
      },
      stop: (fadeS = 0.11) => {
        if (stopped || !this.ctx) return;
        stopped = true;
        this.activeHandles.delete(handle);
        const t = this.ctx.currentTime;
        for (const ch of [yellCh, musicCh]) {
          if (!ch) continue;
          try {
            ch.gain.gain.cancelScheduledValues(t);
            ch.gain.gain.setValueAtTime(Math.max(0.0001, ch.gain.gain.value), t);
            ch.gain.gain.exponentialRampToValueAtTime(0.0001, t + fadeS);
            ch.src.stop(t + fadeS + 0.02);
          } catch (e) {}
        }
      }
    };
    this.activeHandles.add(handle);
    return handle;
  },
  _spatialParams(z, dir) {
    // Smooth 3D distance attenuation & air low-pass filter so travelling music feels physical
    const dist = Math.max(0.4, Math.min(10.5, z));
    const nearness = dir === 'toward'
      ? Math.pow(Math.max(0.12, Math.min(1.0, 1.0 - (dist - 0.35) / 6.2)), 1.15)
      : Math.pow(Math.max(0.24, Math.min(1.0, 1.12 - dist / 11.2)), 1.05);
    return {
      yellGain: 0.24 + 0.56 * nearness,
      musicGain: 0.22 + 0.54 * nearness,
      cutoff: 1850 + 2750 * nearness
    };
  },
  previewPackCombo(windupPackId = null, withTracker = true, pan = 0, speed = 1.0, firePackId = null) {
    this.stopPreview();
    this.stopAllActive();
    const wPack = AUDIO_PACKS.find(p => p.id === (windupPackId || AudioVote.data.equippedWindup || AudioVote.data.equipped)) || this.getActiveWindupPack();
    const fPack = AUDIO_PACKS.find(p => p.id === (firePackId || windupPackId || AudioVote.data.equippedFire || AudioVote.data.equipped)) || this.getActiveFirePack();
    const w = this.startWindup(pan, speed, wPack.windup);
    const t1 = setTimeout(() => {
      if (w) w.stop(0.04);
      this.playFartBlast(pan, speed, fPack.fire);
      if (!withTracker) return;
      const tr = this.startProjectileTracker(pan, 1.4, 'away', speed);
      if (tr) {
        let step = 0;
        this.previewTrackerIv = setInterval(() => {
          step++;
          tr.update(-0.6 + step * 0.12, 1.4 + step * 0.7);
          if (step >= 12) {
            clearInterval(this.previewTrackerIv);
            this.previewTrackerIv = null;
            tr.stop(0.18);
          }
        }, 140);
      }
    }, 900);
    this.previewTimers.push(t1);
  },
  playFireCombo(pan = 0, speed = 1.0) {
    this.previewPackCombo(AudioVote.data.equippedWindup, true, pan, speed, AudioVote.data.equippedFire);
  },
  playImpact(pan = 0, speed = 1.0, heavy = false) {
    const rate = speed < 1.0 ? Math.max(0.6, speed + 0.25) : 1.0;
    if (this.buffers['mud_splat']) {
      this.playKey('mud_splat', { volume: heavy ? 0.88 : 0.72, rate, pan });
    }
    if (this.buffers['fly_buzz']) {
      this.playKey('fly_buzz', { volume: 0.24, rate: 1.0, pan, delay: 0.08 });
    }
  }
};

// ---------------------------------------------------------------------------
// 2b. Audio Pack Catalog & Voting (6 India/Fart/Poop packs + Original Wew)
// ---------------------------------------------------------------------------
const AUDIO_PACKS = [
  {
    id: 'pack1',
    num: 1,
    title: '1. Tumbi Bubble & Wet Ripper',
    subtitle: 'Bhangra Tumbi pitch-rise + stomach gurgles → Punjabi Dhol + mega wet fart + yell',
    windup: 'windup_v1',
    fire: 'fire_v1',
    orig: false
  },
  {
    id: 'pack2',
    num: 2,
    title: '2. Dhol Plunger & Tuk-Tuk Toot',
    subtitle: 'Accelerating Dhol roll + toilet plunger pops → Tuk-Tuk horn chirp + triple wet fart',
    windup: 'windup_v2',
    fire: 'fire_v2',
    orig: false
  },
  {
    id: 'pack3',
    num: 3,
    title: '3. Pungi Belly & Stutter Cannon',
    subtitle: 'Indian Pungi snake-charmer reed + burp churn → 3x rapid-fire stutter fart cannon',
    windup: 'windup_v3',
    fire: 'fire_v3',
    orig: false
  },
  {
    id: 'pack4',
    num: 4,
    title: '4. Rickshaw Sitar & Flush Bomb',
    subtitle: 'Indian sitar bend + bike bell + goostick → sub flush thud + low fart + bloop',
    windup: 'windup_v4',
    fire: 'fire_v4',
    orig: false
  },
  {
    id: 'pack5',
    num: 5,
    title: '5. Bhangra Strain & Fart Trombone',
    subtitle: 'Bhangra vocal hook strain + squeak leaks → dhol slam + sad fart trombone splat',
    windup: 'windup_v5',
    fire: 'fire_v5',
    orig: false
  },
  {
    id: 'pack6',
    num: 6,
    title: '6. Tabla Wobble & Rocket Shart',
    subtitle: 'Fast tabla hits + belly bubbles + wobble → double Tuk-Tuk horn + heh-fart cannon',
    windup: 'windup_v6',
    fire: 'fire_v6',
    orig: false
  },
  {
    id: 'orig',
    num: 0,
    title: 'Original Wew + Classic Farts',
    subtitle: 'Classic Wew Cannon rising whine + randomized fart',
    windup: 'windup_wew',
    fire: ['fart_1', 'fart_2', 'fart_3', 'fart_4'],
    orig: true
  }
];

const AUDIO_VOTE_STORAGE_KEY = 'bakersfield_poop_gun_audio_vote_v3';
const AudioVote = {
  data: {
    equipped: 'pack5',
    equippedWindup: 'pack6',
    equippedFire: 'pack5',
    winner: 'pack5',
    votedWindup: 'pack6',
    votedFire: 'pack5',
    windupVotes: { pack6: 1 },
    fireVotes: { pack5: 1 },
    stars: {}
  },
  _memRaw: '',
  _toastTimer: null,
  load() {
    try {
      const raw = (window.localStorage ? localStorage.getItem(AUDIO_VOTE_STORAGE_KEY) : null) || this._memRaw;
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
          this.data.equipped = parsed.equipped || 'pack5';
          this.data.equippedWindup = parsed.equippedWindup || 'pack6';
          this.data.equippedFire = parsed.equippedFire || 'pack5';
          this.data.winner = parsed.winner || 'pack5';
          this.data.votedWindup = parsed.votedWindup || 'pack6';
          this.data.votedFire = parsed.votedFire || 'pack5';
          this.data.windupVotes = parsed.windupVotes || { pack6: 1 };
          this.data.fireVotes = parsed.fireVotes || { pack5: 1 };
          this.data.stars = parsed.stars || {};
        }
      }
    } catch (e) {}
    if (!AUDIO_PACKS.some(p => p.id === this.data.equippedWindup)) this.data.equippedWindup = 'pack6';
    if (!AUDIO_PACKS.some(p => p.id === this.data.equippedFire)) this.data.equippedFire = 'pack5';
  },
  save() {
    const raw = JSON.stringify(this.data);
    this._memRaw = raw;
    try {
      if (window.localStorage) localStorage.setItem(AUDIO_VOTE_STORAGE_KEY, raw);
    } catch (e) {}
  },
  flashToast(msg) {
    const el = document.getElementById('audio-vote-toast');
    if (!el) return;
    el.textContent = '✓ ' + msg;
    el.classList.add('show');
    if (this._toastTimer) clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => el.classList.remove('show'), 1800);
  },
  setEquipped(packId) {
    if (!AUDIO_PACKS.some(p => p.id === packId)) return;
    this.data.equipped = packId;
    this.data.equippedWindup = packId;
    this.data.equippedFire = packId;
    this.save();
  },
  voteWindup(packId) {
    if (!AUDIO_PACKS.some(p => p.id === packId)) return;
    this.data.votedWindup = packId;
    this.data.equippedWindup = packId;
    this.data.windupVotes[packId] = (Number(this.data.windupVotes[packId]) || 0) + 1;
    this.save();
  },
  voteFire(packId) {
    if (!AUDIO_PACKS.some(p => p.id === packId)) return;
    this.data.votedFire = packId;
    this.data.equippedFire = packId;
    this.data.fireVotes[packId] = (Number(this.data.fireVotes[packId]) || 0) + 1;
    this.save();
  },
  setWinner(packId) {
    if (!AUDIO_PACKS.some(p => p.id === packId)) return;
    this.data.winner = packId;
    this.data.equipped = packId;
    this.data.equippedWindup = packId;
    this.data.equippedFire = packId;
    this.save();
  },
  setStars(packId, stars) {
    this.data.stars[packId] = stars;
    this.save();
  },
  getStars(packId) {
    return Number(this.data.stars[packId] || 0);
  },
  clearVotes() {
    this.data.winner = '';
    this.data.votedWindup = '';
    this.data.votedFire = '';
    this.data.windupVotes = {};
    this.data.fireVotes = {};
    this.data.stars = {};
    this.save();
  }
};

function _buildAudioPackCardDom(p) {
  const card = document.createElement('div');
  card.className = 'audio-pack-card';
  card.dataset.packCard = p.id;
  let starHtml = '';
  for (let s = 1; s <= 5; s++) {
    starHtml += `<button type="button" class="star-btn" data-action="star" data-pack="${p.id}" data-sval="${s}" title="Rate Pack ${p.num}: ${s}/5">☆</button>`;
  }
  card.innerHTML = `
    <div class="audio-pack-title">
      <span>${p.title}</span>
      <span class="audio-badge" data-role="badge"></span>
    </div>
    <div class="audio-pack-sub">${p.subtitle}</div>
    <div class="audio-pack-btns">
      <button type="button" class="btn sm" data-action="play-w" data-pack="${p.id}" title="Listen to Windup sound">🔊 Play Windup</button>
      <button type="button" class="btn sm" data-action="vote-w" data-pack="${p.id}" title="Vote for &amp; equip this Windup sound">👍 Vote Windup</button>
      <button type="button" class="btn sm" data-action="play-f" data-pack="${p.id}" title="Listen to Fire blast sound">💥 Play Fire</button>
      <button type="button" class="btn sm" data-action="vote-f" data-pack="${p.id}" title="Vote for &amp; equip this Fire sound">👍 Vote Fire</button>
      <button type="button" class="btn sm primary" data-action="play-c" data-pack="${p.id}" title="Preview Windup -> Fire + travelling yell &amp; music">⚡ Combo</button>
      <button type="button" class="btn sm" data-action="equip" data-pack="${p.id}" title="Equip this pack's Windup + Fire on the gun">🎯 Equip Pair</button>
    </div>
    <div class="audio-pack-foot">
      <div class="stars" aria-label="Rate audio pack">${starHtml}</div>
      <button type="button" class="btn sm" data-action="vote-win" data-pack="${p.id}">🏆 Vote Best</button>
    </div>
  `;
  return card;
}

function renderAudioVoteGrid() {
  const grid = document.getElementById('audio-vote-grid');
  if (!grid) return;
  if (!grid.children.length) {
    for (const p of AUDIO_PACKS.filter(x => !x.orig)) {
      grid.appendChild(_buildAudioPackCardDom(p));
    }
  }
  const wPack = AUDIO_PACKS.find(p => p.id === AudioVote.data.equippedWindup) || AUDIO_PACKS[0];
  const fPack = AUDIO_PACKS.find(p => p.id === AudioVote.data.equippedFire) || AUDIO_PACKS[0];
  const winPack = AUDIO_PACKS.find(p => p.id === AudioVote.data.winner);
  const vWPack = AUDIO_PACKS.find(p => p.id === AudioVote.data.votedWindup);
  const vFPack = AUDIO_PACKS.find(p => p.id === AudioVote.data.votedFire);

  const statusEl = document.getElementById('audio-vote-status');
  if (statusEl) {
    statusEl.textContent =
      `Live Gun Mix: Windup [${wPack.num ? '#' + wPack.num : 'Orig'}] + Fire [${fPack.num ? '#' + fPack.num : 'Orig'}]` +
      (winPack ? ` • 🏆 Winner: #${winPack.num} ${winPack.title.replace(/^\d+\.\s*/, '')}` : ' • Click Play or Vote on any Windup / Fire / Pack');
  }
  const summaryEl = document.getElementById('audio-vote-summary');
  if (summaryEl) {
    const rated = AUDIO_PACKS.filter(p => !p.orig && AudioVote.getStars(p.id) > 0)
      .map(p => `#${p.num}:${AudioVote.getStars(p.id)}★`).join(' ');
    summaryEl.textContent =
      `Votes — Best Windup: ${vWPack ? '#' + vWPack.num : 'None'} | Best Fire: ${vFPack ? '#' + vFPack.num : 'None'} | Pack Winner: ${winPack ? '#' + winPack.num : 'None'}` +
      (rated ? ` | Stars: ${rated}` : '');
  }
  const origBtn = document.getElementById('btn-audio-orig');
  if (origBtn) {
    const origEq = wPack.id === 'orig' && fPack.id === 'orig';
    origBtn.classList.toggle('active', origEq);
    origBtn.textContent = origEq ? '🔊 Original Wew (On Gun)' : '🔊 Original Wew';
  }

  for (const p of AUDIO_PACKS.filter(x => !x.orig)) {
    const card = grid.querySelector(`[data-pack-card="${p.id}"]`);
    if (!card) continue;
    const isWEq = AudioVote.data.equippedWindup === p.id;
    const isFEq = AudioVote.data.equippedFire === p.id;
    const isEq = isWEq && isFEq;
    const isWin = AudioVote.data.winner === p.id;
    const isWVoted = AudioVote.data.votedWindup === p.id;
    const isFVoted = AudioVote.data.votedFire === p.id;
    const wCount = Number(AudioVote.data.windupVotes[p.id] || 0);
    const fCount = Number(AudioVote.data.fireVotes[p.id] || 0);
    const stars = AudioVote.getStars(p.id);

    card.className = 'audio-pack-card' + ((isWEq || isFEq) ? ' is-equipped' : '') + (isWin ? ' is-winner' : '');
    const badge = card.querySelector('[data-role="badge"]');
    if (badge) {
      if (isWin) {
        badge.className = 'audio-badge win';
        badge.textContent = '🏆 WINNER';
      } else if (isEq) {
        badge.className = 'audio-badge eq';
        badge.textContent = 'ON GUN';
      } else if (isWEq) {
        badge.className = 'audio-badge eq';
        badge.textContent = 'WINDUP ON';
      } else if (isFEq) {
        badge.className = 'audio-badge eq';
        badge.textContent = 'FIRE ON';
      } else {
        badge.className = 'audio-badge';
        badge.textContent = `PACK #${p.num}`;
      }
    }

    const vwBtn = card.querySelector('[data-action="vote-w"]');
    if (vwBtn) {
      vwBtn.classList.toggle('voted-snd', isWVoted);
      vwBtn.textContent = (isWVoted ? '✓ Voted Windup' : '👍 Vote Windup') + (wCount ? ` (${wCount})` : '');
    }
    const vfBtn = card.querySelector('[data-action="vote-f"]');
    if (vfBtn) {
      vfBtn.classList.toggle('voted-snd', isFVoted);
      vfBtn.textContent = (isFVoted ? '✓ Voted Fire' : '👍 Vote Fire') + (fCount ? ` (${fCount})` : '');
    }
    const eqBtn = card.querySelector('[data-action="equip"]');
    if (eqBtn) {
      eqBtn.classList.toggle('active', isEq);
      eqBtn.textContent = isEq ? '✓ On Gun' : '🎯 Equip Pair';
    }
    const winBtn = card.querySelector('[data-action="vote-win"]');
    if (winBtn) {
      winBtn.classList.toggle('voted-win', isWin);
      winBtn.textContent = isWin ? '🏆 WINNER!' : '🏆 Vote Best';
    }
    card.querySelectorAll('[data-action="star"]').forEach(btn => {
      const sv = Number(btn.dataset.sval);
      const lit = sv <= stars;
      btn.classList.toggle('lit', lit);
      btn.textContent = lit ? '★' : '☆';
    });
  }
}

let _audioVotePanelWired = false;
function setupAudioVotePanel() {
  const card = document.getElementById('audio-vote-card');
  if (!card || _audioVotePanelWired) return;
  _audioVotePanelWired = true;
  card.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-action], #btn-test-live-mix');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    if (btn.id === 'btn-test-live-mix') {
      AudioFX.playFireCombo(0, appState.speed);
      return;
    }
    const action = btn.dataset.action;
    const pid = btn.dataset.pack;
    const p = AUDIO_PACKS.find(x => x.id === pid);
    if (action === 'play-w' && p) {
      AudioFX.stopPreview();
      AudioFX.stopAllActive();
      AudioFX.startWindup(0, appState.speed, p.windup);
    } else if (action === 'vote-w' && p) {
      AudioVote.voteWindup(p.id);
      renderAudioVoteGrid();
      AudioVote.flashToast(`Voted & equipped Windup #${p.num}!`);
      AudioFX.stopPreview();
      AudioFX.stopAllActive();
      AudioFX.startWindup(0, appState.speed, p.windup);
    } else if (action === 'play-f' && p) {
      AudioFX.stopPreview();
      AudioFX.stopAllActive();
      AudioFX.playFartBlast(0, appState.speed, p.fire);
    } else if (action === 'vote-f' && p) {
      AudioVote.voteFire(p.id);
      renderAudioVoteGrid();
      AudioVote.flashToast(`Voted & equipped Fire #${p.num}!`);
      AudioFX.stopPreview();
      AudioFX.stopAllActive();
      AudioFX.playFartBlast(0, appState.speed, p.fire);
    } else if (action === 'play-c' && p) {
      AudioVote.setEquipped(p.id);
      renderAudioVoteGrid();
      AudioFX.previewPackCombo(p.id, true, 0, appState.speed, p.id);
    } else if (action === 'equip' && p) {
      AudioVote.setEquipped(p.id);
      renderAudioVoteGrid();
      AudioVote.flashToast(`Equipped Pack #${p.num} on gun`);
      AudioFX.stopPreview();
      AudioFX.stopAllActive();
      AudioFX.startWindup(0, appState.speed, p.windup);
    } else if (action === 'star' && p) {
      const sv = Number(btn.dataset.sval);
      AudioVote.setStars(p.id, sv);
      renderAudioVoteGrid();
      AudioVote.flashToast(`Rated Pack #${p.num}: ${sv}/5 ★`);
    } else if (action === 'vote-win' && p) {
      AudioVote.setWinner(p.id);
      renderAudioVoteGrid();
      AudioVote.flashToast(`🏆 Pack #${p.num} picked as Winner!`);
    } else if (action === 'equip-orig') {
      AudioVote.setEquipped('orig');
      renderAudioVoteGrid();
      AudioVote.flashToast('Equipped Original Wew');
      AudioFX.previewPackCombo('orig', true, 0, appState.speed, 'orig');
    } else if (action === 'clear-votes') {
      AudioVote.clearVotes();
      renderAudioVoteGrid();
      AudioVote.flashToast('Cleared votes');
    } else if (action === 'copy-votes') {
      const payload = {
        equippedWindup: AudioVote.data.equippedWindup,
        equippedFire: AudioVote.data.equippedFire,
        votedWindup: AudioVote.data.votedWindup || null,
        votedFire: AudioVote.data.votedFire || null,
        winnerPack: AudioVote.data.winner || null,
        windupVotes: AudioVote.data.windupVotes,
        fireVotes: AudioVote.data.fireVotes,
        stars: AudioVote.data.stars
      };
      const text = JSON.stringify(payload, null, 2);
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          prompt('Copy Audio Pack Votes JSON:', text);
        }
      } catch (err) {
        try { prompt('Copy Audio Pack Votes JSON:', text); } catch (e2) {}
      }
      AudioVote.flashToast('Copied Votes JSON!');
    }
  });
}

// ---------------------------------------------------------------------------
// 3. Persistent User Ratings & Winner Selection
// ---------------------------------------------------------------------------
const STORAGE_KEY = 'bakersfield_poop_gun_ratings_v2';
const Ratings = {
  data: { winner: 'dookie_mk4', items: {} },
  load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) this.data = JSON.parse(raw);
    } catch (e) {}
    if (!this.data.winner) this.data.winner = 'dookie_mk4';
  },
  save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
    } catch (e) {}
  },
  get(cid) {
    return this.data.items[cid] || { stars: 0, notes: '' };
  },
  setStars(cid, stars) {
    const cur = this.get(cid);
    this.data.items[cid] = { ...cur, stars };
    this.save();
  },
  setNotes(cid, notes) {
    const cur = this.get(cid);
    this.data.items[cid] = { ...cur, notes };
    this.save();
  },
  setWinner(cid) {
    this.data.winner = this.data.winner === cid ? null : cid;
    this.save();
  }
};

const VM_ADJ_STORAGE_KEY = 'bakersfield_poop_gun_vm_adjust_v3';
const VmAdjust = {
  items: {},
  defaultsFor(c) {
    const mn = (c && c.muzzle_norm) ? c.muzzle_norm : [0.35, 0.26];
    return {
      xPct: 26.5,
      yPct: 4.5,
      scalePct: 78,
      rotDeg: -2.0,
      bobPct: 90,
      fovRef: 111,
      muzzleX: Number(mn[0].toFixed(2)),
      muzzleY: Number(mn[1].toFixed(2))
    };
  },
  load() {
    try {
      const raw = localStorage.getItem(VM_ADJ_STORAGE_KEY);
      if (raw) this.items = JSON.parse(raw) || {};
    } catch (e) {
      this.items = {};
    }
  },
  save() {
    try {
      localStorage.setItem(VM_ADJ_STORAGE_KEY, JSON.stringify(this.items));
    } catch (e) {}
  },
  get(c) {
    const def = this.defaultsFor(c);
    const saved = c ? this.items[c.id] : null;
    return saved ? { ...def, ...saved } : def;
  },
  set(c, patch) {
    if (!c) return;
    this.items[c.id] = { ...this.get(c), ...patch };
    this.save();
  },
  reset(c) {
    if (!c) return;
    delete this.items[c.id];
    this.save();
  },
  applyToAll(patch) {
    for (const c of CONCEPTS) {
      const cur = this.get(c);
      this.items[c.id] = {
        ...cur,
        xPct: patch.xPct,
        yPct: patch.yPct,
        scalePct: patch.scalePct,
        rotDeg: patch.rotDeg,
        bobPct: patch.bobPct,
        fovRef: patch.fovRef
      };
    }
    this.save();
  }
};

// ---------------------------------------------------------------------------
// 4. Quake-Style 3D Arena Simulation State & Renderer
// ---------------------------------------------------------------------------
function makeSimState(concept) {
  return {
    concept,
    mode: '1p', // '1p' | '3p'
    animState: 'idle', // 'idle' | 'charge' | 'fire' | 'reload'
    animFrame: 0,
    idleFrame: 0,
    charging: false,
    chargeTime: 0,
    holdDown: false,
    chargeAudio: null,
    playChargeAudio: true,
    tpState: 'idle', // 'idle' | 'charge' | 'fire' | 'reload'
    tpFrame: 0,
    tpAutoTimer: 1.2,
    tpChargeTimer: 0,
    tpChargeAudio: null,
    aimX: 0, // -1..1
    aimY: 0, // -1..1
    dodgeX: 0,
    bobPhase: 0,
    shake: 0,
    muzzleFlash: 0,
    shotsFired: 0,
    projectiles: [],
    wallDecals: [],
    mistClouds: [],
    flies: [],
    screenSplats: [],
    screenSplatAlpha: 0,
    hitmarkerTimer: 0,
    keys: { left: false, right: false }
  };
}

function stopSimAudio(sim) {
  if (sim.chargeAudio) {
    sim.chargeAudio.stop(0.03);
    sim.chargeAudio = null;
  }
  if (sim.tpChargeAudio) {
    sim.tpChargeAudio.stop(0.03);
    sim.tpChargeAudio = null;
  }
  sim.charging = false;
  sim.holdDown = false;
  sim.chargeTime = 0;
  for (const p of sim.projectiles) {
    if (p._audio) {
      p._audio.stop(0.08);
      p._audio = null;
    }
  }
}

function project3D(x, y, z, w, h, camYaw, camPitch) {
  const zz = Math.max(0.18, z);
  const scale = (h * 0.72) / zz;
  const rx = x - camYaw * zz * 0.25;
  const ry = y - camPitch * zz * 0.18;
  return {
    sx: w * 0.5 + rx * scale,
    sy: h * 0.48 + ry * scale,
    scale
  };
}

function drawBuzzingFly(ctx, sx, sy, size, wingPhase, angle = 0) {
  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(angle);
  const r = Math.max(1.8, size);
  const flap = Math.sin(wingPhase) * 0.65;

  // Translucent fluttering wings
  ctx.fillStyle = 'rgba(225, 240, 255, 0.55)';
  ctx.strokeStyle = 'rgba(180, 210, 235, 0.7)';
  ctx.lineWidth = Math.max(0.7, r * 0.12);
  ctx.beginPath();
  ctx.ellipse(-r * 0.55, -r * (0.4 + flap * 0.5), r * 0.85, r * 0.42, -0.5 + flap, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(r * 0.55, -r * (0.4 - flap * 0.5), r * 0.85, r * 0.42, 0.5 - flap, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Glossy iridescent body
  ctx.fillStyle = '#1b2b1e';
  ctx.beginPath();
  ctx.ellipse(0, 0, r * 0.62, r * 0.88, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = 'rgba(120, 230, 140, 0.35)';
  ctx.beginPath();
  ctx.ellipse(-r * 0.15, -r * 0.15, r * 0.22, r * 0.35, 0, 0, Math.PI * 2);
  ctx.fill();

  // Red compound eyes
  ctx.fillStyle = '#dc2626';
  ctx.beginPath();
  ctx.arc(-r * 0.26, -r * 0.62, r * 0.24, 0, Math.PI * 2);
  ctx.arc(r * 0.26, -r * 0.62, r * 0.24, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawMudBlob(ctx, sx, sy, r, seed, alpha = 1) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(sx, sy);
  ctx.rotate((seed * 2.37) % (Math.PI * 2));
  ctx.fillStyle = '#4f3016';
  ctx.beginPath();
  const lobes = 9;
  for (let i = 0; i <= lobes * 2; i++) {
    const a = (i / (lobes * 2)) * Math.PI * 2;
    const rad = r * (0.72 + 0.36 * Math.abs(Math.sin(seed * 7.1 + i * 1.9)));
    const px = Math.cos(a) * rad;
    const py = Math.sin(a) * rad;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fill();

  // Glossy highlight + darker core
  ctx.fillStyle = '#38200d';
  ctx.beginPath();
  ctx.arc(r * 0.08, r * 0.08, r * 0.45, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = 'rgba(176, 128, 72, 0.42)';
  ctx.beginPath();
  ctx.ellipse(-r * 0.22, -r * 0.22, r * 0.22, r * 0.12, -0.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawMistPuff(ctx, sx, sy, r, alpha) {
  const mistAtlas = SHARED_FX.mist;
  if (mistAtlas && mistAtlas.count > 0) {
    ctx.save();
    ctx.globalAlpha = alpha;
    const ok = AtlasStore.drawFrame(ctx, mistAtlas, Math.floor(r) % mistAtlas.count, sx - r, sy - r, r * 2, r * 2);
    ctx.restore();
    if (ok) return;
  }
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createRadialGradient(sx - r * 0.15, sy - r * 0.15, r * 0.1, sx, sy, r);
  grad.addColorStop(0, 'rgba(122, 92, 42, 0.85)');
  grad.addColorStop(0.55, 'rgba(92, 108, 44, 0.55)');
  grad.addColorStop(1, 'rgba(55, 42, 20, 0)');
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(sx, sy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawQuakeCorridor(ctx, w, h, camYaw, camPitch, timeSec, accent) {
  // Base dark stone background
  const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
  bgGrad.addColorStop(0, '#14110f');
  bgGrad.addColorStop(0.48, '#0c0907');
  bgGrad.addColorStop(1, '#1a1510');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, w, h);

  const wallW = 2.55;
  const ceilY = -1.35;
  const floorY = 1.35;
  const zFar = 10.5;
  const zSteps = [1.0, 1.9, 3.0, 4.3, 5.8, 7.5, 9.2, zFar];

  // Draw corridor slices back-to-front
  for (let i = zSteps.length - 1; i >= 1; i--) {
    const z1 = zSteps[i];
    const z0 = zSteps[i - 1];
    const fog = Math.min(0.68, z0 / 13.0);
    const tl1 = project3D(-wallW, ceilY, z1, w, h, camYaw, camPitch);
    const tr1 = project3D(wallW, ceilY, z1, w, h, camYaw, camPitch);
    const br1 = project3D(wallW, floorY, z1, w, h, camYaw, camPitch);
    const bl1 = project3D(-wallW, floorY, z1, w, h, camYaw, camPitch);

    const tl0 = project3D(-wallW, ceilY, z0, w, h, camYaw, camPitch);
    const tr0 = project3D(wallW, ceilY, z0, w, h, camYaw, camPitch);
    const br0 = project3D(wallW, floorY, z0, w, h, camYaw, camPitch);
    const bl0 = project3D(-wallW, floorY, z0, w, h, camYaw, camPitch);

    const shade = Math.round(52 * (1 - fog * 0.72));
    const brickWarm = Math.round(42 * (1 - fog * 0.75));
    const stoneBlue = Math.round(36 * (1 - fog * 0.75));

    // Floor slab with Quake stone grid
    ctx.fillStyle = i % 2 === 0
      ? `rgb(${shade + 6}, ${brickWarm + 2}, ${stoneBlue})`
      : `rgb(${shade - 2}, ${brickWarm - 3}, ${stoneBlue - 2})`;
    ctx.beginPath();
    ctx.moveTo(bl0.sx, bl0.sy); ctx.lineTo(br0.sx, br0.sy);
    ctx.lineTo(br1.sx, br1.sy); ctx.lineTo(bl1.sx, bl1.sy);
    ctx.closePath();
    ctx.fill();

    // Floor center tile strip
    for (let col = -2; col < 2; col++) {
      const fx0 = col * (wallW / 2);
      const fx1 = (col + 1) * (wallW / 2);
      const p00 = project3D(fx0, floorY, z0, w, h, camYaw, camPitch);
      const p10 = project3D(fx1, floorY, z0, w, h, camYaw, camPitch);
      const p11 = project3D(fx1, floorY, z1, w, h, camYaw, camPitch);
      const p01 = project3D(fx0, floorY, z1, w, h, camYaw, camPitch);
      if ((col + i) % 2 === 0) {
        ctx.fillStyle = `rgba(255, 220, 170, ${0.04 * (1 - fog)})`;
        ctx.beginPath();
        ctx.moveTo(p00.sx, p00.sy); ctx.lineTo(p10.sx, p10.sy);
        ctx.lineTo(p11.sx, p11.sy); ctx.lineTo(p01.sx, p01.sy);
        ctx.closePath();
        ctx.fill();
      }
      ctx.strokeStyle = `rgba(10, 8, 6, ${0.55 * (1 - fog * 0.5)})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Ceiling
    ctx.fillStyle = i % 2 === 0
      ? `rgb(${shade - 10}, ${brickWarm - 10}, ${stoneBlue - 8})`
      : `rgb(${shade - 14}, ${brickWarm - 13}, ${stoneBlue - 10})`;
    ctx.beginPath();
    ctx.moveTo(tl0.sx, tl0.sy); ctx.lineTo(tr0.sx, tr0.sy);
    ctx.lineTo(tr1.sx, tr1.sy); ctx.lineTo(tl1.sx, tl1.sy);
    ctx.closePath();
    ctx.fill();

    // Left & Right Stone Brick Walls
    const wallTone = i % 2 === 0
      ? `rgb(${shade + 12}, ${brickWarm + 2}, ${stoneBlue - 4})`
      : `rgb(${shade + 3}, ${brickWarm - 4}, ${stoneBlue - 6})`;
    ctx.fillStyle = wallTone;
    // Left
    ctx.beginPath();
    ctx.moveTo(tl0.sx, tl0.sy); ctx.lineTo(tl1.sx, tl1.sy);
    ctx.lineTo(bl1.sx, bl1.sy); ctx.lineTo(bl0.sx, bl0.sy);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = 'rgba(12, 9, 6, 0.7)';
    ctx.stroke();

    // Right
    ctx.beginPath();
    ctx.moveTo(tr0.sx, tr0.sy); ctx.lineTo(tr1.sx, tr1.sy);
    ctx.lineTo(br1.sx, br1.sy); ctx.lineTo(br0.sx, br0.sy);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Horizontal brick courses on side walls
    for (let row = 1; row <= 3; row++) {
      const wy = ceilY + (floorY - ceilY) * (row / 4);
      const lw0 = project3D(-wallW, wy, z0, w, h, camYaw, camPitch);
      const lw1 = project3D(-wallW, wy, z1, w, h, camYaw, camPitch);
      const rw0 = project3D(wallW, wy, z0, w, h, camYaw, camPitch);
      const rw1 = project3D(wallW, wy, z1, w, h, camYaw, camPitch);
      ctx.strokeStyle = `rgba(12, 9, 6, ${0.45 * (1 - fog)})`;
      ctx.beginPath();
      ctx.moveTo(lw0.sx, lw0.sy); ctx.lineTo(lw1.sx, lw1.sy);
      ctx.moveTo(rw0.sx, rw0.sy); ctx.lineTo(rw1.sx, rw1.sy);
      ctx.stroke();
    }

    // Wall torches on every other rib
    if (i === 2 || i === 5 || i === 7) {
      const zMid = (z0 + z1) * 0.5;
      const flicker = 0.86 + 0.14 * Math.sin(timeSec * 14.0 + i * 2.1);
      for (const side of [-1, 1]) {
        const tp = project3D(side * (wallW - 0.14), -0.35, zMid, w, h, camYaw, camPitch);
        const glowR = tp.scale * 0.55 * flicker;
        const tgrad = ctx.createRadialGradient(tp.sx, tp.sy, 1, tp.sx, tp.sy, glowR);
        tgrad.addColorStop(0, `rgba(255, 225, 130, ${0.85 * flicker})`);
        tgrad.addColorStop(0.3, `rgba(255, 130, 30, ${0.45 * flicker})`);
        tgrad.addColorStop(1, 'rgba(255, 80, 0, 0)');
        ctx.fillStyle = tgrad;
        ctx.beginPath();
        ctx.arc(tp.sx, tp.sy, glowR, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  // Far Back Wall + Target Bullseye
  const btl = project3D(-wallW, ceilY, zFar, w, h, camYaw, camPitch);
  const btr = project3D(wallW, ceilY, zFar, w, h, camYaw, camPitch);
  const bbr = project3D(wallW, floorY, zFar, w, h, camYaw, camPitch);
  const bbl = project3D(-wallW, floorY, zFar, w, h, camYaw, camPitch);
  ctx.fillStyle = '#261f18';
  ctx.beginPath();
  ctx.moveTo(btl.sx, btl.sy); ctx.lineTo(btr.sx, btr.sy);
  ctx.lineTo(bbr.sx, bbr.sy); ctx.lineTo(bbl.sx, bbl.sy);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#120e0a';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Painted Target Crest on Back Wall
  const targetCenter = project3D(0, 0.02, zFar - 0.05, w, h, camYaw, camPitch);
  const tr = targetCenter.scale * 0.85;
  const rings = ['#78350f', '#f5f5f4', '#b91c1c', '#f5f5f4', accent || '#ff9933'];
  rings.forEach((col, idx) => {
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(targetCenter.sx, targetCenter.sy, tr * (1 - idx * 0.19), 0, Math.PI * 2);
    ctx.fill();
  });
}

const WC_CHARGE_MAX = 1.45;
const WC_CHARGE_MIN_TAP = 0.58;

function beginCharge(sim, playAudio = true, isHold = true) {
  if (sim.mode === '1p') {
    if (sim.charging || sim.animState === 'fire') return;
    sim.charging = true;
    sim.holdDown = isHold;
    sim.chargeTime = 0;
    sim.playChargeAudio = playAudio;
    sim.animState = 'charge';
    if (playAudio) {
      if (sim.chargeAudio) sim.chargeAudio.stop(0.02);
      sim.chargeAudio = AudioFX.startWindup(sim.aimX * 0.6, appState.speed);
    }
  } else {
    if (sim.tpState === 'charge' || sim.tpState === 'fire') return;
    sim.tpState = 'charge';
    sim.tpChargeTimer = 0;
    if (playAudio) {
      if (sim.tpChargeAudio) sim.tpChargeAudio.stop(0.02);
      sim.tpChargeAudio = AudioFX.startWindup(sim.aimX * 0.4, appState.speed);
    }
  }
}

function releaseCharge(sim) {
  sim.holdDown = false;
  if (sim.mode === '1p' && sim.charging && sim.chargeTime >= WC_CHARGE_MIN_TAP) {
    launchShot(sim, sim.playChargeAudio, Math.min(1.0, sim.chargeTime / WC_CHARGE_MAX));
  }
}

function triggerShot(sim, playAudio = true, instant = false) {
  if (instant) {
    launchShot(sim, playAudio, 1.0);
  } else {
    beginCharge(sim, playAudio, false);
  }
}

function getVmTransform(w, h, sim, compact = false) {
  const c = sim.concept;
  const cfg = VmAdjust.get(c);
  const seq = (sim.animState === 'fire' && c.sequences.vm_fire)
    ? c.sequences.vm_fire
    : ((sim.animState === 'reload' && c.sequences.vm_reload) ? c.sequences.vm_reload : c.sequences.vm_idle);

  const bobScale = (cfg.bobPct || 0) / 100.0;
  const chargeFrac = sim.charging ? Math.min(1.0, sim.chargeTime / WC_CHARGE_MAX) : 0;
  const bobX = (Math.sin(sim.bobPhase) * (compact ? 4 : 7) + sim.aimX * (compact ? 14 : 26)) * bobScale + (sim.charging ? chargeFrac * 18 : 0);
  const bobY = (Math.abs(Math.cos(sim.bobPhase)) * (compact ? 3 : 6) + sim.aimY * (compact ? 8 : 14)) * bobScale + (sim.charging ? chargeFrac * 12 : 0);
  const recoilY = sim.animState === 'fire' ? Math.sin(Math.min(1, sim.animFrame / 8) * Math.PI) * 18 : 0;

  const refFov = Number(cfg.fovRef) || 111;
  const curFov = compact ? refFov : (Number(appState.previewFov) || refFov);
  const fovScale = Math.tan((refFov * Math.PI) / 360.0) / Math.tan((curFov * Math.PI) / 360.0);

  const vhRef = h * ((cfg.scalePct || 78) / 100.0);
  const vwRef = (seq && seq.fw && seq.fh) ? vhRef * (seq.fw / seq.fh) : vhRef * (420 / 360);
  const vxRef = w * (0.50 + (cfg.xPct || 0) / 100.0) - vwRef * 0.5;
  const vyRef = (h - vhRef) + ((cfg.yPct || 0) / 100.0) * h;

  const vw = vwRef * fovScale;
  const vh = vhRef * fovScale;
  const vx = w * 0.5 + (vxRef - w * 0.5) * fovScale + bobX;
  const vy = h * 0.5 + (vyRef - h * 0.5) * fovScale + bobY + recoilY;

  const rotRad = ((cfg.rotDeg || 0) * Math.PI) / 180.0;
  const pivX = vx + vw * 0.55;
  const pivY = vy + vh * 0.78;
  const localMx = vx + (cfg.muzzleX != null ? cfg.muzzleX : 0.35) * vw - pivX;
  const localMy = vy + (cfg.muzzleY != null ? cfg.muzzleY : 0.26) * vh - pivY;
  const cr = Math.cos(rotRad), sr = Math.sin(rotRad);
  const mx = pivX + localMx * cr - localMy * sr;
  const my = pivY + localMx * sr + localMy * cr;
  return { cfg, vx, vy, vw, vh, pivX, pivY, rotRad, mx, my, bobX, bobY, recoilY, chargeFrac, fovScale };
}

function launchShot(sim, playAudio = true, chargeFrac = 0.7) {
  if (sim.mode === '1p') {
    const tr = getVmTransform(960, 540, sim, false);
    sim.charging = false;
    sim.holdDown = false;
    sim.chargeTime = 0;
    if (sim.chargeAudio) {
      sim.chargeAudio.stop(0.03);
      sim.chargeAudio = null;
    }
    sim.animState = 'fire';
    sim.animFrame = 0;
    sim.muzzleFlash = 1.0;
    sim.shake = Math.max(sim.shake, 12 + chargeFrac * 6);
    sim.shotsFired++;

    const tx = sim.aimX * 2.15;
    const ty = Math.max(-1.05, Math.min(1.05, sim.aimY * 1.05));
    const startZ = 0.85;
    const scale0 = (540 * 0.72) / startZ;
    const camYaw0 = sim.aimX * 0.45;
    const camPitch0 = sim.aimY * 0.25;
    const startX = (tr.mx - 960 * 0.5) / scale0 + camYaw0 * startZ * 0.25;
    const startY = (tr.my - 540 * 0.48) / scale0 + camPitch0 * startZ * 0.18;
    // Slow enough to clearly watch him run/wave arms down the corridor + hear music follow him!
    const travelTime = 2.45 - 0.45 * chargeFrac;
    const grav = 0.75;

    const projAudio = playAudio
      ? AudioFX.startProjectileTracker((startX - sim.aimX * 0.45) * 0.55, startZ, 'away', appState.speed)
      : null;

    sim.projectiles.push({
      dir: 'away',
      x: startX,
      y: startY,
      z: startZ,
      vx: (tx - startX) / travelTime,
      vy: (ty - startY) / travelTime - 0.5 * grav * travelTime,
      vz: (10.35 - startZ) / travelTime,
      gravity: grav,
      age: 0,
      frame: 0,
      trailAccum: 0,
      style: 'sprint',
      _audio: projAudio
    });

    // Muzzle fart stink-mist puffs
    for (let i = 0; i < 6; i++) {
      sim.mistClouds.push({
        x: startX + (Math.random() - 0.5) * 0.28,
        y: startY + (Math.random() - 0.5) * 0.18,
        z: startZ + 0.15,
        vx: (Math.random() - 0.5) * 0.9,
        vy: -0.35 - Math.random() * 0.5,
        vz: 1.4 + Math.random() * 1.0,
        r: 0.18,
        maxR: 0.52 + Math.random() * 0.25,
        life: 0,
        maxLife: 0.75 + Math.random() * 0.35
      });
    }
    if (playAudio) AudioFX.playFartBlast(sim.aimX * 0.6, appState.speed);
  } else {
    // 3rd-Person: Enemy finishes Wew windup and blasts a slow, visible yelling+music bloke at YOUR camera!
    if (sim.tpChargeAudio) {
      sim.tpChargeAudio.stop(0.03);
      sim.tpChargeAudio = null;
    }
    sim.tpState = 'fire';
    sim.tpFrame = 0;
    sim.muzzleFlash = 0.9;
    sim.shake = Math.max(sim.shake, 7);
    sim.shotsFired++;

    const enemyX = sim.aimX * 1.1;
    const enemyZ = 5.3;
    const startY = 0.15;
    const targetX = sim.dodgeX * 0.7;
    const targetY = 0.04;
    // Slow enough to clearly watch him waving hands + flies trailing + dodge with A/D!
    const travelTime = 2.25;
    const grav = 0.85;

    const projAudio = playAudio
      ? AudioFX.startProjectileTracker((enemyX - sim.dodgeX * 0.35) * 0.55, enemyZ, 'toward', appState.speed)
      : null;

    sim.projectiles.push({
      dir: 'toward',
      x: enemyX,
      y: startY,
      z: enemyZ,
      vx: (targetX - enemyX) / travelTime,
      vy: (targetY - startY) / travelTime - 0.5 * grav * travelTime,
      vz: (0.28 - enemyZ) / travelTime,
      gravity: grav,
      age: 0,
      frame: 0,
      trailAccum: 0,
      style: 'sprint',
      _audio: projAudio
    });

    for (let i = 0; i < 6; i++) {
      sim.mistClouds.push({
        x: enemyX + (Math.random() - 0.5) * 0.35,
        y: startY + (Math.random() - 0.5) * 0.25,
        z: enemyZ - 0.3,
        vx: (Math.random() - 0.5) * 1.4,
        vy: -0.4 - Math.random() * 0.5,
        vz: -1.4,
        r: 0.24,
        maxR: 0.75 + Math.random() * 0.35,
        life: 0,
        maxLife: 0.85 + Math.random() * 0.35
      });
    }
    if (playAudio) AudioFX.playFartBlast(enemyX * 0.35, appState.speed);
  }
}

function stepSim(sim, dtRaw, speed, autoFire3p, playAudio) {
  const dt = dtRaw * speed;
  sim.bobPhase += dt * 4.2;
  sim.shake = Math.max(0, sim.shake - dtRaw * 32);
  sim.muzzleFlash = Math.max(0, sim.muzzleFlash - dt * 6.5);
  sim.hitmarkerTimer = Math.max(0, sim.hitmarkerTimer - dtRaw * 3.0);

  if (sim.keys.left) sim.dodgeX = Math.max(-1.2, sim.dodgeX - dt * 1.8);
  if (sim.keys.right) sim.dodgeX = Math.min(1.2, sim.dodgeX + dt * 1.8);

  const seqs = sim.concept.sequences;
  const fps = sim.concept.fps || 60;

  // Viewmodel state machine (Wew Cannon windup -> fart blast -> reload)
  if (sim.charging && sim.mode === '1p') {
    const cnt = seqs.vm_idle ? seqs.vm_idle.count : 60;
    sim.idleFrame = (sim.idleFrame + dt * fps * 0.65) % Math.max(1, cnt);
    sim.chargeTime += dtRaw * (speed >= 1 ? 1.0 : Math.max(0.5, speed));
    const cFrac = Math.min(1.0, sim.chargeTime / WC_CHARGE_MAX);
    sim.shake = Math.max(sim.shake, 1.5 + cFrac * 4.5);
    if (sim.chargeAudio) sim.chargeAudio.setPan(sim.aimX * 0.6);
    if ((!sim.holdDown && sim.chargeTime >= WC_CHARGE_MIN_TAP) || sim.chargeTime >= WC_CHARGE_MAX) {
      launchShot(sim, playAudio && sim.playChargeAudio, cFrac);
    }
  } else if (sim.animState === 'idle') {
    const cnt = seqs.vm_idle ? seqs.vm_idle.count : 60;
    sim.idleFrame = (sim.idleFrame + dt * fps) % Math.max(1, cnt);
  } else if (sim.animState === 'fire') {
    sim.animFrame += dt * fps;
    const cnt = seqs.vm_fire ? seqs.vm_fire.count : 20;
    if (sim.animFrame >= cnt) {
      if (seqs.vm_reload && seqs.vm_reload.count > 0) {
        sim.animState = 'reload';
        sim.animFrame = 0;
      } else {
        sim.animState = 'idle';
        sim.animFrame = 0;
      }
    }
  } else if (sim.animState === 'reload') {
    sim.animFrame += dt * fps;
    const cnt = seqs.vm_reload ? seqs.vm_reload.count : 18;
    if (sim.animFrame >= cnt) {
      sim.animState = 'idle';
      sim.animFrame = 0;
    }
  }

  // 3rd-Person shooter state machine (Wew Cannon windup warning before firing!)
  if (sim.tpState === 'idle') {
    const cnt = seqs.tp_idle ? seqs.tp_idle.count : 30;
    const tpFps = cnt <= 28 ? 24 : fps;
    sim.tpFrame = (sim.tpFrame + dt * tpFps) % Math.max(1, cnt);
    if (sim.mode === '3p' && autoFire3p) {
      sim.tpAutoTimer -= dt;
      if (sim.tpAutoTimer <= 0) {
        sim.tpAutoTimer = 3.2;
        beginCharge(sim, playAudio, true);
      }
    }
  } else if (sim.tpState === 'charge') {
    const cnt = seqs.tp_idle ? seqs.tp_idle.count : 30;
    sim.tpFrame = (sim.tpFrame + dt * fps * 0.65) % Math.max(1, cnt);
    sim.tpChargeTimer += dt;
    if (sim.tpChargeAudio) sim.tpChargeAudio.setPan(sim.aimX * 0.4);
    if (sim.tpChargeTimer >= 0.85) {
      launchShot(sim, playAudio, 0.85);
    }
  } else if (sim.tpState === 'fire') {
    const cnt = seqs.tp_fire ? seqs.tp_fire.count : 20;
    const tpFps = cnt <= 18 ? 30 : fps;
    sim.tpFrame += dt * tpFps;
    if (sim.tpFrame >= cnt) {
      if (seqs.tp_reload && seqs.tp_reload.count > 0) {
        sim.tpState = 'reload';
        sim.tpFrame = 0;
      } else {
        sim.tpState = 'idle';
        sim.tpFrame = 0;
      }
    }
  } else if (sim.tpState === 'reload') {
    const cnt = seqs.tp_reload ? seqs.tp_reload.count : 16;
    const tpFps = cnt <= 18 ? 30 : fps;
    sim.tpFrame += dt * tpFps;
    if (sim.tpFrame >= cnt) {
      sim.tpState = 'idle';
      sim.tpFrame = 0;
    }
  }

  // Projectiles (slow, readable waving runner + spatially-following yelling & Bhangra music)
  const camX = (sim.mode === '1p' ? sim.aimX * 0.45 : sim.dodgeX * 0.35);
  for (let i = sim.projectiles.length - 1; i >= 0; i--) {
    const p = sim.projectiles[i];
    p.age += dt;
    p.frame += dt * 16;
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += p.gravity * dt;
    p.z += p.vz * dt;
    p.trailAccum += dt;

    if (p._audio) {
      p._audio.update((p.x - camX * 1.4) / 2.2, p.z);
    }

    // Leave mud globs + calm flies tracking behind the flying bloke
    if (p.trailAccum >= 0.06) {
      p.trailAccum = 0;
      sim.mistClouds.push({
        x: p.x + (Math.random() - 0.5) * 0.16,
        y: p.y + (Math.random() - 0.5) * 0.16,
        z: p.z,
        vx: (Math.random() - 0.5) * 0.30,
        vy: -0.15 + (Math.random() - 0.5) * 0.16,
        vz: 0,
        r: 0.13,
        maxR: 0.34,
        life: 0,
        maxLife: 0.65,
        isTrail: true
      });
      if (sim.flies.length < 18) {
        sim.flies.push({
          cx: p.x + (Math.random() - 0.5) * 0.18,
          cy: p.y - 0.08 + (Math.random() - 0.5) * 0.18,
          cz: p.z - (p.dir === 'away' ? 0.18 : -0.18),
          phase: Math.random() * 12,
          speed: 3.4 + Math.random() * 2.4,
          rx: 0.12 + Math.random() * 0.12,
          ry: 0.09 + Math.random() * 0.10,
          rz: 0.06,
          life: 0,
          maxLife: 1.15
        });
      }
    }

    // Impact check
    if (p.dir === 'away' && (p.z >= 10.3 || Math.abs(p.x) > 2.45 || p.y > 1.28)) {
      const iz = Math.min(10.35, p.z);
      const ix = Math.max(-2.15, Math.min(2.15, p.x));
      const iy = Math.max(-1.05, Math.min(1.05, p.y));
      sim.wallDecals.push({
        x: ix,
        y: iy,
        z: iz,
        r: 1.85 + Math.random() * 0.45,
        seed: Math.random() * 100,
        spriteIdx: Math.floor(Math.random() * 16),
        age: 0
      });
      for (let sb = 0; sb < 5; sb++) {
        const ang = (sb / 5) * Math.PI * 2 + Math.random() * 0.7;
        const dist = 0.65 + Math.random() * 0.75;
        sim.wallDecals.push({
          x: Math.max(-2.3, Math.min(2.3, ix + Math.cos(ang) * dist)),
          y: Math.max(-1.15, Math.min(1.15, iy + Math.sin(ang) * dist * 0.7)),
          z: iz - 0.02,
          r: 0.80 + Math.random() * 0.45,
          seed: Math.random() * 100,
          spriteIdx: Math.floor(Math.random() * 16),
          age: 0
        });
      }
      while (sim.wallDecals.length > 40) sim.wallDecals.shift();

      // Big billowing brown stink-mist cloud at impact (kept translucent so wall mud pops clearly)
      for (let m = 0; m < 10; m++) {
        sim.mistClouds.push({
          x: ix + (Math.random() - 0.5) * 1.4,
          y: iy + (Math.random() - 0.5) * 1.0,
          z: iz - 0.15,
          vx: (Math.random() - 0.5) * 1.8,
          vy: -0.4 - Math.random() * 0.6,
          vz: -0.6 - Math.random() * 0.8,
          r: 0.30,
          maxR: 1.45 + Math.random() * 0.65,
          life: 0,
          maxLife: 1.05 + Math.random() * 0.45
        });
      }
      // Calm buzzing flies around wall splatter
      for (let f = 0; f < 6; f++) {
        sim.flies.push({
          cx: ix + (Math.random() - 0.5) * 0.45,
          cy: iy + (Math.random() - 0.5) * 0.45,
          cz: iz - 0.25,
          phase: Math.random() * 20,
          speed: 3.0 + Math.random() * 2.5,
          rx: 0.40 + Math.random() * 0.30,
          ry: 0.30 + Math.random() * 0.25,
          rz: 0.18,
          life: 0,
          maxLife: 5.5 + Math.random() * 2.5
        });
      }
      sim.shake = Math.max(sim.shake, 11);
      sim.hitmarkerTimer = 1.0;
      if (p._audio) {
        p._audio.stop(0.11);
        p._audio = null;
      }
      if (playAudio) AudioFX.playImpact(ix / 2.4, speed, false);
      sim.projectiles.splice(i, 1);
    } else if (p.dir === 'toward' && p.z <= 0.42) {
      // SLAMMED INTO PLAYER CAMERA!
      sim.shake = 26;
      sim.screenSplatAlpha = 1.0;
      sim.screenSplats = [];
      for (let s = 0; s < 14; s++) {
        sim.screenSplats.push({
          nx: 0.08 + Math.random() * 0.84,
          ny: 0.08 + Math.random() * 0.78,
          r: 0.06 + Math.random() * 0.13,
          dripSpeed: 0.025 + Math.random() * 0.055,
          dripLen: 0,
          seed: Math.random() * 100
        });
      }
      // Flies right in front of camera lens!
      for (let f = 0; f < 7; f++) {
        sim.flies.push({
          cx: (Math.random() - 0.5) * 0.75,
          cy: (Math.random() - 0.5) * 0.45,
          cz: 0.7 + Math.random() * 0.35,
          phase: Math.random() * 20,
          speed: 3.5 + Math.random() * 3.0,
          rx: 0.14 + Math.random() * 0.16,
          ry: 0.11 + Math.random() * 0.14,
          rz: 0.08,
          life: 0,
          maxLife: 3.6 + Math.random() * 1.4
        });
      }
      // Stink mist right at lens
      for (let m = 0; m < 10; m++) {
        sim.mistClouds.push({
          x: (Math.random() - 0.5) * 0.9,
          y: (Math.random() - 0.5) * 0.6,
          z: 0.9,
          vx: (Math.random() - 0.5) * 0.6,
          vy: -0.25 - Math.random() * 0.3,
          vz: 0.15,
          r: 0.25,
          maxR: 0.78,
          life: 0,
          maxLife: 1.5
        });
      }
      if (p._audio) {
        p._audio.stop(0.11);
        p._audio = null;
      }
      if (playAudio) AudioFX.playImpact(0, speed, true);
      sim.projectiles.splice(i, 1);
    }
  }

  // Mist clouds
  for (let i = sim.mistClouds.length - 1; i >= 0; i--) {
    const m = sim.mistClouds[i];
    m.life += dt;
    if (m.life >= m.maxLife) {
      sim.mistClouds.splice(i, 1);
      continue;
    }
    m.x += m.vx * dt;
    m.y += m.vy * dt;
    m.z += m.vz * dt;
    const t = m.life / m.maxLife;
    m.r = m.r + (m.maxR - m.r) * Math.min(1, dt * 4.0);
    m.alpha = (1 - t) * (m.isTrail ? 0.42 : 0.48);
  }

  // Flies
  for (let i = sim.flies.length - 1; i >= 0; i--) {
    const f = sim.flies[i];
    f.life += dt;
    if (f.life >= f.maxLife) {
      sim.flies.splice(i, 1);
      continue;
    }
    f.phase += dt * f.speed;
  }

  // Screen mud splat wipe decay
  if (sim.screenSplatAlpha > 0) {
    for (const sp of sim.screenSplats) {
      sp.dripLen += sp.dripSpeed * dt;
    }
    sim.screenSplatAlpha = Math.max(0, sim.screenSplatAlpha - dt * 0.34);
  }
}

function drawBakersfieldHudOverlay(ctx, w, h, compact) {
  // 1. Captured real Combat+ bottom status bar + ammo + >TRUE dock
  if (SHARED_FX._bgHudImg) {
    ctx.drawImage(SHARED_FX._bgHudImg, 0, 0, w, h);
  }
  const s = h / 540.0;

  // 2. Left-side Jetpack fuel gauge (matching JP_DrawHUD in bm_hud.qc)
  const jpX = 11 * s;
  const jpW = 28 * s;
  const jpH = 128 * s;
  const jpY = h - 115 * s - jpH;
  ctx.save();
  ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
  ctx.fillRect(jpX, jpY, jpW, jpH);
  ctx.fillStyle = 'rgba(235, 198, 52, 0.76)';
  ctx.fillRect(jpX + 1.5 * s, jpY + 1.5 * s, jpW - 3 * s, jpH - 3 * s);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.88)';
  ctx.lineWidth = Math.max(1, 1.5 * s);
  ctx.strokeRect(jpX, jpY, jpW, jpH);
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${Math.max(9, Math.round(13 * s))}px ui-monospace, monospace`;
  ctx.textAlign = 'center';
  ctx.fillText('40s', jpX + jpW * 0.5, jpY + jpH + 15 * s);
  ctx.restore();

  // 3. Top-right CSQC weapon/toy dock (F:Head I:Jar X:Pkl B:BC U:Dookie G:Wew P:Bird)
  const slots = [
    ['F:', 'Head'],
    ['I:', 'Jar'],
    ['X:', 'Pkl'],
    ['B:', 'BC'],
    ['U:', 'Dookie'],
    ['G:', 'Wew'],
    ['P:', 'Bird']
  ];
  ctx.save();
  const fontSize = Math.max(9, Math.round(12 * s));
  ctx.font = `bold ${fontSize}px ui-monospace, Consolas, monospace`;
  const padX = 7 * s;
  const gap = 8 * s;
  let totalW = padX * 2;
  const widths = slots.map(([k, v]) => ctx.measureText(k).width + ctx.measureText(v).width);
  for (let i = 0; i < widths.length; i++) totalW += widths[i] + (i > 0 ? gap : 0);
  const pillH = Math.round(20 * s);
  const pillX = w - totalW - 8 * s;
  const pillY = 6 * s;
  ctx.fillStyle = 'rgba(0, 0, 0, 0.42)';
  ctx.beginPath();
  ctx.roundRect(pillX, pillY, totalW, pillH, 3 * s);
  ctx.fill();

  let curX = pillX + padX;
  const textY = pillY + pillH * 0.72;
  for (let i = 0; i < slots.length; i++) {
    const [k, v] = slots[i];
    const kw = ctx.measureText(k).width;
    const vw = ctx.measureText(v).width;
    if (v === 'Dookie') {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.14)';
      ctx.fillRect(curX - 2 * s, pillY + 2 * s, kw + vw + 4 * s, pillH - 4 * s);
    }
    ctx.fillStyle = '#38e838';
    ctx.fillText(k, curX, textY);
    ctx.fillStyle = v === 'Dookie' ? '#fde047' : '#ffffff';
    ctx.fillText(v, curX + kw, textY);
    curX += kw + vw + gap;
  }
  ctx.restore();
}

function drawSimCanvas(ctx, w, h, sim, timeSec, compact = false) {
  ctx.clearRect(0, 0, w, h);

  const sxShake = (Math.random() - 0.5) * sim.shake * (compact ? 0.6 : 1.0);
  const syShake = (Math.random() - 0.5) * sim.shake * (compact ? 0.6 : 1.0);
  const camYaw = (sim.mode === '1p' ? sim.aimX * 0.45 : sim.dodgeX * 0.35);
  const camPitch = (sim.mode === '1p' ? sim.aimY * 0.25 : 0.0);

  ctx.save();
  ctx.translate(sxShake, syShake);

  // 1. Background: Real Soi Cowboy world capture or dark test corridor
  const useGameBg = appState.bgMode !== 'corridor' && SHARED_FX._bgWorldImg;
  if (useGameBg) {
    const padX = w * 0.025;
    const padY = h * 0.025;
    ctx.drawImage(
      SHARED_FX._bgWorldImg,
      -padX - camYaw * w * 0.032,
      -padY - camPitch * h * 0.032,
      w + padX * 2,
      h + padY * 2
    );
  } else {
    drawQuakeCorridor(ctx, w, h, camYaw, camPitch, timeSec, sim.concept.accent);
  }

  // 2. Wall Mud Splatter Decals
  const splatAtlas = SHARED_FX.splats;
  for (const d of sim.wallDecals) {
    const p = project3D(d.x, d.y, d.z, w, h, camYaw, camPitch);
    const pr = d.r * p.scale;
    if (splatAtlas && splatAtlas.count > 0) {
      AtlasStore.drawFrame(ctx, splatAtlas, d.spriteIdx, p.sx - pr, p.sy - pr, pr * 2, pr * 2);
    } else {
      drawMudBlob(ctx, p.sx, p.sy, pr, d.seed, 0.92);
    }
  }

  // 3. 3rd-Person Enemy Shooter standing downrange
  if (sim.mode === '3p') {
    const enemyX = sim.aimX * 1.1;
    const enemyZ = 5.3;
    const ep = project3D(enemyX, 0.2, enemyZ, w, h, camYaw, camPitch);
    const floorP = project3D(enemyX, 1.35, enemyZ, w, h, camYaw, camPitch);
    // Ground shadow
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.beginPath();
    ctx.ellipse(floorP.sx, floorP.sy, ep.scale * 0.62, ep.scale * 0.16, 0, 0, Math.PI * 2);
    ctx.fill();

    let tpSeq = sim.concept.sequences.tp_idle || sim.concept.sequences.tp_fire;
    if (sim.tpState === 'fire' && sim.concept.sequences.tp_fire) {
      tpSeq = sim.concept.sequences.tp_fire;
    } else if (sim.tpState === 'reload' && sim.concept.sequences.tp_reload) {
      tpSeq = sim.concept.sequences.tp_reload;
    }

    const spriteH = (floorP.sy - project3D(enemyX, -1.02, enemyZ, w, h, camYaw, camPitch).sy);
    if (tpSeq && tpSeq.count > 0) {
      const spriteW = spriteH * (tpSeq.fw / tpSeq.fh);
      const drawX = ep.sx - spriteW * 0.5;
      const drawY = floorP.sy - spriteH;
      const ok = AtlasStore.drawFrame(ctx, tpSeq, Math.floor(sim.tpFrame), drawX, drawY, spriteW, spriteH);
      if (!ok) drawFallbackEnemy(ctx, ep.sx, floorP.sy, spriteH, sim.concept);
    } else {
      drawFallbackEnemy(ctx, ep.sx, floorP.sy, spriteH, sim.concept);
    }

    // Muzzle blast ring on enemy
    if (sim.muzzleFlash > 0.05) {
      const mf = project3D(enemyX, 0.05, enemyZ - 0.5, w, h, camYaw, camPitch);
      const mr = mf.scale * 0.9 * (1.2 - sim.muzzleFlash * 0.5);
      const mg = ctx.createRadialGradient(mf.sx, mf.sy, 2, mf.sx, mf.sy, mr);
      mg.addColorStop(0, `rgba(180, 220, 70, ${sim.muzzleFlash * 0.9})`);
      mg.addColorStop(0.5, `rgba(110, 75, 25, ${sim.muzzleFlash * 0.6})`);
      mg.addColorStop(1, 'rgba(70, 45, 15, 0)');
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(mf.sx, mf.sy, mr, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // 4. Mist Clouds & Mud Trail Globs (sorted back-to-front)
  const globAtlas = SHARED_FX.globs || SHARED_FX.splats;
  const sortedMist = [...sim.mistClouds].sort((a, b) => b.z - a.z);
  for (const m of sortedMist) {
    const p = project3D(m.x, m.y, m.z, w, h, camYaw, camPitch);
    const pr = m.r * p.scale;
    if (m.isTrail && globAtlas && globAtlas.count > 0) {
      ctx.save();
      ctx.globalAlpha = m.alpha || 0.65;
      AtlasStore.drawFrame(ctx, globAtlas, Math.floor(m.r * 30), p.sx - pr, p.sy - pr, pr * 2, pr * 2);
      ctx.restore();
    } else {
      drawMistPuff(ctx, p.sx, p.sy, pr, m.alpha || 0.6);
    }
  }

  // 5. Flying Projectiles (sorted back-to-front, scaled larger so enemy players clearly see the hand-waving bloke!)
  const sortedProj = [...sim.projectiles].sort((a, b) => b.z - a.z);
  for (const prj of sortedProj) {
    const p = project3D(prj.x, prj.y, prj.z, w, h, camYaw, camPitch);
    const pAtlas = sim.concept.sequences.proj;
    const baseSize = p.scale * 1.15;
    let angIdx = 0;
    if (pAtlas && pAtlas.angles > 1) {
      angIdx = prj.dir === 'away' ? Math.floor(pAtlas.angles / 2) : 0;
    }
    if (pAtlas && pAtlas.count > 0) {
      const pw = baseSize * (pAtlas.fw / pAtlas.fh);
      const ph = baseSize;
      AtlasStore.drawProj(ctx, pAtlas, angIdx, Math.floor(prj.frame), p.sx - pw * 0.5, p.sy - ph * 0.5, pw, ph);
    } else {
      drawMudBlob(ctx, p.sx, p.sy, baseSize * 0.42, prj.age * 10, 0.95);
    }
  }

  // 6. Buzzing 3D Flies
  for (const f of sim.flies) {
    const fx = f.cx + Math.cos(f.phase) * f.rx;
    const fy = f.cy + Math.sin(f.phase * 1.4) * f.ry;
    const fz = f.cz + Math.sin(f.phase * 0.8) * f.rz;
    const p = project3D(fx, fy, fz, w, h, camYaw, camPitch);
    const flySize = Math.max(1.4, Math.min(8.5, p.scale * 0.022));
    drawBuzzingFly(ctx, p.sx, p.sy, flySize, f.phase * 5.0, Math.cos(f.phase) * 0.5);
  }

  // 7. 1st-Person Weapon Viewmodel + Wew Cannon Charge Coil + Muzzle Fart Blast
  if (sim.mode === '1p') {
    const vmIdle = sim.concept.sequences.vm_idle;
    const vmFire = sim.concept.sequences.vm_fire;
    const vmReload = sim.concept.sequences.vm_reload;

    let activeSeq = vmIdle;
    let activeFrame = Math.floor(sim.idleFrame);
    if (sim.animState === 'fire' && vmFire) {
      activeSeq = vmFire;
      activeFrame = Math.floor(sim.animFrame);
    } else if (sim.animState === 'reload' && vmReload) {
      activeSeq = vmReload;
      activeFrame = Math.floor(sim.animFrame);
    }

    const vt = getVmTransform(w, h, sim, compact);
    const { vx, vy, vw, vh, pivX, pivY, rotRad, mx, my, bobX, bobY, recoilY, chargeFrac } = vt;

    // Charging green-gold reactor glow on muzzle while winding up like Wew Cannon
    if (sim.charging && chargeFrac > 0.02) {
      const cr = h * (0.10 + 0.14 * chargeFrac);
      const cg = ctx.createRadialGradient(mx, my, 2, mx, my, cr);
      cg.addColorStop(0, `rgba(180, 255, 90, ${0.35 + 0.45 * chargeFrac})`);
      cg.addColorStop(0.55, `rgba(250, 190, 40, ${0.20 + 0.30 * chargeFrac})`);
      cg.addColorStop(1, 'rgba(120, 200, 30, 0)');
      ctx.fillStyle = cg;
      ctx.beginPath();
      ctx.arc(mx, my, cr, 0, Math.PI * 2);
      ctx.fill();
    }

    // Muzzle flash behind weapon barrel, anchored to adjusted muzzle
    if (sim.muzzleFlash > 0.05) {
      const mr = h * 0.28 * (1.2 - sim.muzzleFlash * 0.4);
      const mg = ctx.createRadialGradient(mx, my, 4, mx, my, mr);
      mg.addColorStop(0, `rgba(190, 230, 80, ${sim.muzzleFlash * 0.85})`);
      mg.addColorStop(0.45, `rgba(115, 78, 25, ${sim.muzzleFlash * 0.65})`);
      mg.addColorStop(1, 'rgba(60, 38, 12, 0)');
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(mx, my, mr, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.save();
    if (Math.abs(rotRad) > 0.0005) {
      ctx.translate(pivX, pivY);
      ctx.rotate(rotRad);
      ctx.translate(-pivX, -pivY);
    }
    if (activeSeq && activeSeq.count > 0) {
      const ok = AtlasStore.drawFrame(ctx, activeSeq, activeFrame, vx, vy, vw, vh);
      if (!ok) drawFallbackVM(ctx, w, h, bobX, bobY + recoilY, sim.concept);
    } else {
      drawFallbackVM(ctx, w, h, bobX, bobY + recoilY, sim.concept);
    }
    if (!compact && (appState.vmGuides || appState.vmDragMode)) {
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.82)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(vx, vy, vw, vh);
      ctx.setLineDash([]);
    }
    ctx.restore();

    if (!compact && (appState.vmGuides || appState.vmDragMode)) {
      ctx.save();
      // Pivot marker
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(pivX, pivY, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = 'bold 10px ui-monospace, monospace';
      ctx.fillText('PIVOT', pivX + 8, pivY + 3);
      // Muzzle reticle
      ctx.strokeStyle = '#ff9933';
      ctx.fillStyle = '#ff9933';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.arc(mx, my, 8, 0, Math.PI * 2);
      ctx.moveTo(mx - 13, my); ctx.lineTo(mx + 13, my);
      ctx.moveTo(mx, my - 13); ctx.lineTo(mx, my + 13);
      ctx.stroke();
      ctx.fillText('MUZZLE', mx + 11, my - 6);
      ctx.restore();
    }

    // Quake Crosshair + Wew Windup Charge Bar
    if (!compact) {
      const cx = w * 0.5 + sim.aimX * (w * 0.36);
      const cy = h * 0.48 + sim.aimY * (h * 0.34);
      if (appState.bgMode === 'game_hud') {
        // Real BakersfieldQuake green crosshair (crosshair 5 / Combat+)
        ctx.strokeStyle = sim.hitmarkerTimer > 0 ? '#ef4444' : (sim.charging ? '#bef264' : '#00e628');
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.arc(cx, cy, 4.2 + (sim.charging ? 2.5 * chargeFrac : 0), 0, Math.PI * 2);
        ctx.moveTo(cx - 10, cy); ctx.lineTo(cx - 3.5, cy);
        ctx.moveTo(cx + 3.5, cy); ctx.lineTo(cx + 10, cy);
        ctx.moveTo(cx, cy - 10); ctx.lineTo(cx, cy - 3.5);
        ctx.moveTo(cx, cy + 3.5); ctx.lineTo(cx, cy + 10);
        ctx.stroke();
      } else {
        ctx.strokeStyle = sim.hitmarkerTimer > 0 ? '#ef4444' : (sim.charging ? '#84cc16' : 'rgba(255, 210, 120, 0.85)');
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, 10 + (sim.charging ? 5 * chargeFrac : 0), 0, Math.PI * 2);
        ctx.moveTo(cx - 16, cy); ctx.lineTo(cx - 5, cy);
        ctx.moveTo(cx + 5, cy); ctx.lineTo(cx + 16, cy);
        ctx.moveTo(cx, cy - 16); ctx.lineTo(cx, cy - 5);
        ctx.moveTo(cx, cy + 5); ctx.lineTo(cx, cy + 16);
        ctx.stroke();
      }

      if (sim.charging) {
        const bw = 220, bh = 16;
        const bx = w * 0.5 - bw * 0.5, by = appState.bgMode === 'game_hud' ? h - 108 : h - 54;
        ctx.fillStyle = 'rgba(15, 13, 11, 0.82)';
        ctx.strokeStyle = '#ff9933';
        ctx.lineWidth = 2;
        ctx.fillRect(bx, by, bw, bh);
        ctx.strokeRect(bx, by, bw, bh);
        const fillG = ctx.createLinearGradient(bx, by, bx + bw, by);
        fillG.addColorStop(0, '#84cc16');
        fillG.addColorStop(0.65, '#f59e0b');
        fillG.addColorStop(1, '#ef4444');
        ctx.fillStyle = fillG;
        ctx.fillRect(bx + 2, by + 2, (bw - 4) * chargeFrac, bh - 4);
        ctx.fillStyle = '#f3eadb';
        ctx.font = 'bold 11px ui-monospace, monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`DOOKIE PRESSURE: ${Math.round(chargeFrac * 100)}%`, w * 0.5, by - 6);
        ctx.textAlign = 'left';
      }

      if (sim.hitmarkerTimer > 0) {
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(cx - 14, cy - 14); ctx.lineTo(cx - 6, cy - 6);
        ctx.moveTo(cx + 14, cy - 14); ctx.lineTo(cx + 6, cy - 6);
        ctx.moveTo(cx - 14, cy + 14); ctx.lineTo(cx - 6, cy + 6);
        ctx.moveTo(cx + 14, cy + 14); ctx.lineTo(cx + 6, cy + 6);
        ctx.stroke();
      }
    }
  } else if (!compact) {
    // Subtle 3rd-person "DODGE A/D" + Enemy Windup indicator
    ctx.fillStyle = sim.tpState === 'charge' ? '#fbbf24' : 'rgba(239, 68, 68, 0.85)';
    ctx.font = 'bold 12px ui-monospace, monospace';
    ctx.fillText(
      sim.tpState === 'charge'
        ? '⚡ ENEMY WINDING UP — GET READY TO DODGE WITH [A] / [D]!'
        : 'INCOMING FIRE ZONE — DODGE WITH [A] / [D] OR MOUSE',
      14,
      24
    );
  }

  // 7.5 Real BakersfieldQuake HUD Overlay (Combat+ bottom bar, Jetpack gauge, top-right Toy Dock)
  if (appState.bgMode === 'game_hud') {
    drawBakersfieldHudOverlay(ctx, w, h, compact);
  }

  // 8. 3rd-Person Full-Screen Mud Splatter Wipe!
  if (sim.screenSplatAlpha > 0.01) {
    ctx.save();
    // Stinky brown-green vignette
    const vig = ctx.createRadialGradient(w * 0.5, h * 0.5, h * 0.15, w * 0.5, h * 0.5, w * 0.72);
    vig.addColorStop(0, `rgba(92, 62, 24, ${sim.screenSplatAlpha * 0.18})`);
    vig.addColorStop(1, `rgba(66, 40, 14, ${sim.screenSplatAlpha * 0.72})`);
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, w, h);

    for (let idx = 0; idx < sim.screenSplats.length; idx++) {
      const sp = sim.screenSplats[idx];
      const px = sp.nx * w;
      const py = (sp.ny + sp.dripLen) * h;
      const pr = sp.r * h;
      // Drip streak above blob
      ctx.strokeStyle = `rgba(74, 44, 18, ${sim.screenSplatAlpha * 0.8})`;
      ctx.lineWidth = pr * 0.35;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(px, sp.ny * h);
      ctx.lineTo(px, py);
      ctx.stroke();
      if (splatAtlas && splatAtlas.count > 0) {
        ctx.save();
        ctx.globalAlpha = sim.screenSplatAlpha * 0.94;
        AtlasStore.drawFrame(ctx, splatAtlas, idx, px - pr * 1.4, py - pr * 1.4, pr * 2.8, pr * 2.8);
        ctx.restore();
      } else {
        drawMudBlob(ctx, px, py, pr, sp.seed, sim.screenSplatAlpha * 0.94);
      }
    }
    ctx.restore();
  }

  ctx.restore();
}

function drawFallbackVM(ctx, w, h, bx, by, concept) {
  ctx.save();
  ctx.translate(w * 0.5 + bx, h * 0.82 + by);
  ctx.fillStyle = '#2d231a';
  ctx.strokeStyle = concept.accent;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(-130, -90, 260, 140, 16);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#f3eadb';
  ctx.textAlign = 'center';
  ctx.font = 'bold 15px system-ui, sans-serif';
  ctx.fillText(`DESIGN ${concept.num}: ${concept.title}`, 0, -28);
  ctx.fillStyle = '#a69884';
  ctx.font = '12px ui-monospace, monospace';
  ctx.fillText('Awaiting baked vm_*.png sprites...', 0, -4);
  ctx.restore();
}

function drawFallbackEnemy(ctx, sx, floorY, spriteH, concept) {
  ctx.save();
  const bw = Math.max(40, spriteH * 0.55);
  ctx.fillStyle = '#31261d';
  ctx.strokeStyle = concept.accent;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(sx - bw * 0.5, floorY - spriteH, bw, spriteH, 10);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#f3eadb';
  ctx.textAlign = 'center';
  ctx.font = 'bold 11px ui-monospace, monospace';
  ctx.fillText(`ENEMY #${concept.num}`, sx, floorY - spriteH * 0.55);
  ctx.fillText('(Awaiting tp_*.png)', sx, floorY - spriteH * 0.42);
  ctx.restore();
}

// ---------------------------------------------------------------------------
// 5. Application Controller (Tabs, Inspector, Compare Grid, Input)
// ---------------------------------------------------------------------------
const appState = {
  activeTab: (CONCEPTS.find(c => c.id === 'dookie_mk4') || CONCEPTS[0]).id, // MK-IV winner pre-selected (or 'compare')
  speed: 1.0,
  autoFire3p: true,
  vmDragMode: false,
  vmGuides: false,
  bgMode: 'game_hud', // 'game_hud' | 'game_clean' | 'corridor'
  previewFov: 111,
  sims: {},
  compareMode: '1p',
  compareSpeed: 1.0,
  insp: {
    seqKey: 'vm_idle',
    playing: true,
    frame: 0,
    angle: 0,
    checker: true,
    zoom: 1.0
  }
};

for (const c of CONCEPTS) {
  appState.sims[c.id] = makeSimState(c);
}

function activeConcept() {
  return CONCEPTS.find(c => c.id === appState.activeTab) || CONCEPTS[0];
}
function activeSim() {
  return appState.sims[activeConcept().id];
}

function renderTabs() {
  const bar = document.getElementById('tabs-bar');
  bar.innerHTML = '';
  for (const c of CONCEPTS) {
    const r = Ratings.get(c.id);
    const btn = document.createElement('button');
    btn.className = 'tab-btn' + (appState.activeTab === c.id ? ' active' : '');
    btn.dataset.cid = c.id;
    btn.style.setProperty('--tab-accent', c.accent);
    const dotClass = c.ready ? 'ready' : 'pending';
    const starHtml = r.stars > 0 ? `<span class="tab-star">${'★'.repeat(r.stars)}</span>` : '';
    const winHtml = Ratings.data.winner === c.id ? `<span class="winner-pill">Winner</span>` : '';
    btn.innerHTML = `<span class="tab-dot ${dotClass}"></span><span>${c.num}. ${c.title}</span>${starHtml}${winHtml}`;
    btn.onclick = () => selectTab(c.id);
    bar.appendChild(btn);
  }
  const cmpBtn = document.createElement('button');
  cmpBtn.className = 'tab-btn' + (appState.activeTab === 'compare' ? ' active' : '');
  cmpBtn.style.setProperty('--tab-accent', '#22c55e');
  cmpBtn.innerHTML = `⚡ COMPARE ALL ${CONCEPTS.length} SIDE-BY-SIDE`;
  cmpBtn.onclick = () => selectTab('compare');
  bar.appendChild(cmpBtn);
}

function selectTab(tabId) {
  AudioFX.stopAllActive();
  for (const s of Object.values(appState.sims)) {
    stopSimAudio(s);
    s.charging = false;
  }
  appState.activeTab = tabId;
  renderTabs();
  const isCmp = tabId === 'compare';
  document.getElementById('single-view').classList.toggle('hidden', isCmp);
  document.getElementById('compare-view').classList.toggle('hidden', !isCmp);
  const voteCard = document.getElementById('audio-vote-card');
  const m1 = document.getElementById('audio-vote-mount-1p');
  const mc = document.getElementById('audio-vote-mount-cmp');
  if (voteCard && m1 && mc) {
    const dest = isCmp ? mc : m1;
    if (voteCard.parentElement !== dest) dest.appendChild(voteCard);
  }
  if (isCmp) {
    for (const c of CONCEPTS) {
      appState.sims[c.id].mode = appState.compareMode === '3p' ? '3p' : '1p';
      if (appState.compareMode !== '3p') {
        appState.sims[c.id].screenSplatAlpha = 0;
        appState.sims[c.id].screenSplats = [];
      }
    }
    renderCompareGrid();
  } else {
    syncSingleConceptUI();
  }
}

function syncSingleConceptUI() {
  const c = activeConcept();
  const sim = activeSim();
  document.getElementById('c-title').textContent = `${c.num}. ${c.title}`;
  document.getElementById('c-subtitle').textContent = c.subtitle;
  document.getElementById('c-subtitle').style.color = c.accent;
  document.getElementById('c-tagline').textContent = c.tagline;
  document.getElementById('c-ready-badge').textContent = c.ready
    ? '● ALL SPRITES PACKED'
    : `◐ MISSING: ${c.missing.join(', ')}`;
  document.getElementById('c-ready-badge').style.color = c.ready ? '#4ade80' : '#fbbf24';

  const winBtn = document.getElementById('btn-pick-winner');
  const isWin = Ratings.data.winner === c.id;
  winBtn.textContent = isWin ? '🏆 SELECTED AS FAVORITE!' : '🏆 Pick as Favorite';
  winBtn.classList.toggle('active', isWin);

  document.getElementById('mode-1p').classList.toggle('active', sim.mode === '1p');
  document.getElementById('mode-3p').classList.toggle('active', sim.mode === '3p');
  document.getElementById('btn-auto-fire').classList.toggle('hidden', sim.mode !== '3p');

  // Populate inspector sequence dropdown
  const sel = document.getElementById('insp-seq');
  const labels = {
    vm_idle: 'VM Idle (1st-Person)',
    vm_fire: 'VM Fire / Recoil',
    vm_reload: 'VM Reload',
    proj: 'Projectile Sprite',
    tp_idle: '3P Enemy Idle',
    tp_fire: '3P Enemy Fire',
    tp_reload: '3P Enemy Reload'
  };
  sel.innerHTML = '';
  for (const [k, lbl] of Object.entries(labels)) {
    const seq = c.sequences[k];
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = seq ? `${lbl} (${seq.count}f)` : `${lbl} (empty)`;
    sel.appendChild(opt);
  }
  if (!c.sequences[appState.insp.seqKey]) {
    appState.insp.seqKey = Object.keys(labels).find(k => c.sequences[k]) || 'vm_idle';
  }
  sel.value = appState.insp.seqKey;
  appState.insp.frame = 0;
  syncInspectorControls();
  syncRatingUI();
  syncAdjusterUI();
}

function formatAdjustPayload(c, cfg) {
  const refFov = Number(cfg.fovRef) || 111;
  const tanHalfY = Math.tan((refFov * Math.PI) / 360.0) * 0.75;
  const dx = 14.0;
  const halfH = dx * tanHalfY;
  const halfW = halfH * (16.0 / 9.0);
  const seq = (c && c.sequences && c.sequences.vm_idle) ? c.sequences.vm_idle : null;
  const aspect = (seq && seq.fw && seq.fh) ? (seq.fw / seq.fh) : (420.0 / 360.0);
  const vhFrac = (cfg.scalePct || 78) / 100.0;
  const vhScreenY = vhFrac * 2.0 * halfH;
  const vwScreenY = vhScreenY * aspect;
  const vxCenterNdc = 2.0 * (0.5 + (cfg.xPct || 0) / 100.0) - 1.0;
  const vyTopFrac = (1.0 - vhFrac) + (cfg.yPct || 0) / 100.0;
  const vyTopNdc = 1.0 - 2.0 * vyTopFrac;
  const vyBotNdc = vyTopNdc - 2.0 * vhFrac;
  const yCenter = -vxCenterNdc * halfW;
  const zTop = vyTopNdc * halfH;
  const zBot = vyBotNdc * halfH;
  return {
    id: c.id,
    xPct: Number(cfg.xPct.toFixed(1)),
    yPct: Number(cfg.yPct.toFixed(1)),
    scalePct: Math.round(cfg.scalePct),
    rotDeg: Number(cfg.rotDeg.toFixed(1)),
    bobPct: Math.round(cfg.bobPct),
    fovRef: refFov,
    previewFov: Number(appState.previewFov) || refFov,
    muzzle_norm: [Number(cfg.muzzleX.toFixed(2)), Number(cfg.muzzleY.toFixed(2))],
    md3_bounds: {
      dx,
      y_right: Number((yCenter - vwScreenY * 0.5).toFixed(2)),
      y_left: Number((yCenter + vwScreenY * 0.5).toFixed(2)),
      z_bot: Number(zBot.toFixed(2)),
      z_top: Number(zTop.toFixed(2))
    }
  };
}

function syncAdjusterUI() {
  const c = activeConcept();
  const cfg = VmAdjust.get(c);
  const pairs = [
    ['adj-x', 'xPct', 1],
    ['adj-y', 'yPct', 1],
    ['adj-scale', 'scalePct', 0],
    ['adj-rot', 'rotDeg', 1],
    ['adj-bob', 'bobPct', 0],
    ['adj-mx', 'muzzleX', 2],
    ['adj-my', 'muzzleY', 2]
  ];
  for (const [id, key, dec] of pairs) {
    const val = Number(cfg[key]).toFixed(dec);
    const rng = document.getElementById(id);
    const num = document.getElementById(id + '-num');
    if (rng) rng.value = val;
    if (num) num.value = val;
  }
  const fovVal = String(Math.round(Number(appState.previewFov) || 111));
  const fovRng = document.getElementById('adj-fov');
  const fovNum = document.getElementById('adj-fov-num');
  if (fovRng) fovRng.value = fovVal;
  if (fovNum) fovNum.value = fovVal;
  document.querySelectorAll('[data-fovpreset]').forEach((b) => {
    b.classList.toggle('active', Number(b.dataset.fovpreset) === Number(fovVal));
  });

  const bgBtn = document.getElementById('btn-bg-mode');
  if (bgBtn) {
    const labels = {
      game_hud: '🎮 Soi Cowboy + HUD',
      game_clean: '🎮 Soi Cowboy (Clean)',
      corridor: '🧱 Dark Corridor'
    };
    bgBtn.textContent = labels[appState.bgMode] || labels.game_hud;
    bgBtn.classList.toggle('active', appState.bgMode !== 'corridor');
  }

  const sum = document.getElementById('adj-summary');
  if (sum) sum.textContent = `X:${cfg.xPct.toFixed(1)}% Y:${cfg.yPct.toFixed(1)}% S:${Math.round(cfg.scalePct)}% FOV:${fovVal}`;
  const exp = document.getElementById('adj-export');
  if (exp) {
    const payload = formatAdjustPayload(c, cfg);
    exp.textContent = JSON.stringify(payload);
  }
  const dragBtn = document.getElementById('btn-drag-vm');
  if (dragBtn) {
    dragBtn.classList.toggle('active', appState.vmDragMode);
    dragBtn.textContent = appState.vmDragMode ? '🖱️ Dragging Weapon: ON' : '🖱️ Drag Weapon';
  }
  const guideBtn = document.getElementById('btn-vm-guides');
  if (guideBtn) {
    guideBtn.classList.toggle('active', appState.vmGuides);
  }
  const arena = document.getElementById('arena-canvas');
  if (arena) arena.classList.toggle('drag-mode', appState.vmDragMode);
  const hint = document.getElementById('hud-hint');
  if (hint) {
    hint.textContent = appState.vmDragMode
      ? 'Drag canvas to move weapon • Scroll: Scale • Shift+Scroll: Rotate • Arrows: Nudge'
      : 'Move mouse to aim • Hold or Click / SPACE for Dookie windup & blast • Alt+Drag moves weapon';
  }
}

function syncInspectorControls() {
  const c = activeConcept();
  const seq = c.sequences[appState.insp.seqKey];
  const isProj = appState.insp.seqKey === 'proj' && seq && seq.angles > 1;
  document.getElementById('insp-angle-wrap').classList.toggle('hidden', !isProj);
  const scrub = document.getElementById('insp-scrub');
  if (seq) {
    const maxF = isProj ? seq.fpa : seq.count;
    scrub.max = Math.max(0, maxF - 1);
    document.getElementById('insp-dims').textContent = `${seq.fw}×${seq.fh}`;
    if (isProj) {
      const angSlider = document.getElementById('insp-angle');
      angSlider.max = seq.angles - 1;
      angSlider.value = Math.min(appState.insp.angle, seq.angles - 1);
      const deg = Math.round((Number(angSlider.value) / seq.angles) * 360);
      document.getElementById('insp-angle-lbl').textContent = `${deg}°`;
    }
  } else {
    scrub.max = 0;
    document.getElementById('insp-dims').textContent = '0×0';
  }
  document.getElementById('insp-play').textContent = appState.insp.playing ? '⏸ Pause' : '▶ Play';
}

function syncRatingUI() {
  const c = activeConcept();
  const r = Ratings.get(c.id);
  document.getElementById('rating-lbl').textContent = r.stars ? `${r.stars} / 5 ★` : 'Unrated';
  document.querySelectorAll('#rating-stars .star-btn').forEach(btn => {
    btn.classList.toggle('lit', Number(btn.dataset.val) <= r.stars);
  });
  document.getElementById('rating-notes').value = r.notes || '';
}

function renderCompareGrid() {
  const grid = document.getElementById('compare-grid');
  grid.innerHTML = '';
  for (const c of CONCEPTS) {
    const r = Ratings.get(c.id);
    const isWin = Ratings.data.winner === c.id;
    const card = document.createElement('div');
    card.className = 'compare-card' + (isWin ? ' is-winner' : '');
    card.innerHTML = `
      <div class="compare-head">
        <div>
          <strong style="color:${c.accent}">${c.num}. ${c.title}</strong>
          <span class="mono-meta" style="display:inline;margin-left:6px;">${c.subtitle}</span>
        </div>
        <div class="ctrl-group">
          <button class="btn sm primary" data-fire="${c.id}">💥 Fire</button>
          <button class="btn sm" data-open="${c.id}">Inspect →</button>
        </div>
      </div>
      <canvas class="compare-canvas" id="cmp-canvas-${c.id}" width="640" height="360"></canvas>
      <div class="compare-foot">
        <span class="mono-meta">${c.ready ? '● Ready' : '◐ Missing: ' + c.missing.join(',')}</span>
        <div class="ctrl-group">
          <span class="tab-star">${r.stars ? '★'.repeat(r.stars) : 'No rating'}</span>
          <button class="btn sm ${isWin ? 'active' : ''}" data-win="${c.id}">${isWin ? '🏆 Winner' : '🏆 Pick'}</button>
        </div>
      </div>
    `;
    card.querySelector(`[data-fire="${c.id}"]`).onclick = () => {
      const s = appState.sims[c.id];
      s.mode = appState.compareMode === '3p' ? '3p' : '1p';
      triggerShot(s, true);
    };
    card.querySelector(`[data-open="${c.id}"]`).onclick = () => selectTab(c.id);
    card.querySelector(`[data-win="${c.id}"]`).onclick = () => {
      Ratings.setWinner(c.id);
      renderTabs();
      renderCompareGrid();
    };
    card.querySelector('canvas').onclick = () => {
      const s = appState.sims[c.id];
      s.mode = appState.compareMode === '3p' ? '3p' : '1p';
      triggerShot(s, true);
    };
    grid.appendChild(card);
  }
}

// ---------------------------------------------------------------------------
// 6. Wire Up UI Events
// ---------------------------------------------------------------------------
function bindEvents() {
  document.getElementById('btn-test-fart').onclick = () => AudioFX.playFireCombo(0, appState.speed);
  setupAudioVotePanel();
  document.getElementById('btn-mute').onclick = (e) => {
    AudioFX.muted = !AudioFX.muted;
    if (AudioFX.muted) {
      AudioFX.stopAllActive();
      for (const s of Object.values(appState.sims)) stopSimAudio(s);
    }
    e.target.textContent = AudioFX.muted ? '🔇 Sound: OFF' : '🔊 Sound: ON';
  };
  document.getElementById('btn-clean-walls').onclick = () => {
    for (const s of Object.values(appState.sims)) {
      s.wallDecals = [];
      s.screenSplats = [];
      s.screenSplatAlpha = 0;
    }
  };
  document.getElementById('btn-pick-winner').onclick = () => {
    Ratings.setWinner(activeConcept().id);
    renderTabs();
    syncSingleConceptUI();
  };

  document.getElementById('mode-1p').onclick = () => {
    const sim = activeSim();
    stopSimAudio(sim);
    sim.tpState = 'idle';
    sim.mode = '1p';
    syncSingleConceptUI();
  };
  document.getElementById('mode-3p').onclick = () => {
    const sim = activeSim();
    stopSimAudio(sim);
    sim.animState = 'idle';
    sim.mode = '3p';
    sim.tpAutoTimer = 0.7;
    syncSingleConceptUI();
  };
  document.getElementById('btn-auto-fire').onclick = (e) => {
    appState.autoFire3p = !appState.autoFire3p;
    e.target.textContent = appState.autoFire3p ? '🔁 Enemy Auto-Fire: ON' : '🔁 Enemy Auto-Fire: OFF';
  };
  const fireBtn = document.getElementById('btn-fire-now');
  fireBtn.onmousedown = () => beginCharge(activeSim(), true, true);
  fireBtn.onmouseup = () => releaseCharge(activeSim());
  fireBtn.onmouseleave = () => {
    const sim = activeSim();
    if (sim.holdDown) releaseCharge(sim);
  };
  document.getElementById('btn-bg-mode').onclick = () => {
    const order = ['game_hud', 'game_clean', 'corridor'];
    appState.bgMode = order[(order.indexOf(appState.bgMode) + 1) % order.length];
    syncAdjusterUI();
  };
  document.getElementById('btn-drag-vm').onclick = () => {
    appState.vmDragMode = !appState.vmDragMode;
    syncAdjusterUI();
  };
  document.getElementById('btn-vm-guides').onclick = () => {
    appState.vmGuides = !appState.vmGuides;
    syncAdjusterUI();
  };

  // Weapon Model Position Adjuster bindings
  const adjFields = [
    ['adj-x', 'xPct', -40, 45],
    ['adj-y', 'yPct', -25, 45],
    ['adj-scale', 'scalePct', 35, 135],
    ['adj-rot', 'rotDeg', -35, 35],
    ['adj-bob', 'bobPct', 0, 200],
    ['adj-mx', 'muzzleX', 0.05, 0.95],
    ['adj-my', 'muzzleY', 0.05, 0.95]
  ];
  for (const [id, key, minV, maxV] of adjFields) {
    const applyVal = (raw) => {
      const n = Number(raw);
      if (!Number.isFinite(n)) return;
      const clamped = Math.max(minV, Math.min(maxV, n));
      VmAdjust.set(activeConcept(), { [key]: clamped });
      syncAdjusterUI();
    };
    document.getElementById(id).oninput = (e) => applyVal(e.target.value);
    document.getElementById(id + '-num').onchange = (e) => applyVal(e.target.value);
    document.getElementById(id + '-num').oninput = (e) => applyVal(e.target.value);
  }
  const applyPreviewFov = (raw) => {
    const n = Number(raw);
    if (!Number.isFinite(n)) return;
    appState.previewFov = Math.max(75, Math.min(125, Math.round(n)));
    syncAdjusterUI();
  };
  document.getElementById('adj-fov').oninput = (e) => applyPreviewFov(e.target.value);
  document.getElementById('adj-fov-num').onchange = (e) => applyPreviewFov(e.target.value);
  document.getElementById('adj-fov-num').oninput = (e) => applyPreviewFov(e.target.value);
  document.querySelectorAll('[data-fovpreset]').forEach((b) => {
    b.onclick = () => applyPreviewFov(b.dataset.fovpreset);
  });

  document.querySelectorAll('[data-vmpreset]').forEach((b) => {
    b.onclick = () => {
      const preset = b.dataset.vmpreset;
      const c = activeConcept();
      if (preset === 'reset') {
        VmAdjust.reset(c);
        appState.previewFov = 111;
      } else if (preset === 'quake-right') {
        VmAdjust.set(c, { xPct: 26.5, yPct: 4.5, scalePct: 78, rotDeg: -2.0, bobPct: 90 });
      } else if (preset === 'center-low') {
        VmAdjust.set(c, { xPct: 2.0, yPct: 12.0, scalePct: 76, rotDeg: 0.0, bobPct: 75 });
      } else if (preset === 'hipfire') {
        VmAdjust.set(c, { xPct: 21.0, yPct: 2.0, scalePct: 84, rotDeg: 1.5, bobPct: 100 });
      }
      syncAdjusterUI();
    };
  });
  document.getElementById('btn-adj-all').onclick = (e) => {
    const cfg = VmAdjust.get(activeConcept());
    VmAdjust.applyToAll(cfg);
    const orig = e.target.textContent;
    e.target.textContent = `✓ Applied to All ${CONCEPTS.length}!`;
    setTimeout(() => { e.target.textContent = orig; }, 1200);
  };
  document.getElementById('btn-adj-copy').onclick = (e) => {
    const c = activeConcept();
    const text = JSON.stringify(formatAdjustPayload(c, VmAdjust.get(c)), null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    const orig = e.target.textContent;
    e.target.textContent = '✓ Copied!';
    setTimeout(() => { e.target.textContent = orig; }, 1200);
  };

  document.querySelectorAll('#speed-group .btn').forEach(b => {
    b.onclick = () => {
      appState.speed = Number(b.dataset.speed);
      document.querySelectorAll('#speed-group .btn').forEach(x => x.classList.toggle('active', x === b));
    };
  });

  // Arena mouse + hold/click windup fire + weapon drag positioning
  const arenaCanvas = document.getElementById('arena-canvas');
  let vmDrag = null;
  arenaCanvas.addEventListener('mousemove', (e) => {
    if (vmDrag) return;
    const rect = arenaCanvas.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    const sim = activeSim();
    sim.aimX = Math.max(-1, Math.min(1, nx));
    sim.aimY = Math.max(-1, Math.min(1, ny));
    if (sim.mode === '3p') sim.dodgeX = sim.aimX * 0.9;
  });
  arenaCanvas.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    const sim = activeSim();
    if (sim.mode === '1p' && (appState.vmDragMode || e.altKey)) {
      e.preventDefault();
      const rect = arenaCanvas.getBoundingClientRect();
      const cur = VmAdjust.get(activeConcept());
      vmDrag = {
        startX: e.clientX,
        startY: e.clientY,
        origX: cur.xPct,
        origY: cur.yPct,
        w: rect.width,
        h: rect.height
      };
      arenaCanvas.classList.add('dragging');
      return;
    }
    beginCharge(sim, true, true);
  });
  window.addEventListener('mousemove', (e) => {
    if (!vmDrag) return;
    const dxPct = ((e.clientX - vmDrag.startX) / Math.max(1, vmDrag.w)) * 100.0;
    const dyPct = ((e.clientY - vmDrag.startY) / Math.max(1, vmDrag.h)) * 100.0;
    const nx = Math.max(-40, Math.min(45, Math.round((vmDrag.origX + dxPct) * 2) / 2));
    const ny = Math.max(-25, Math.min(45, Math.round((vmDrag.origY + dyPct) * 2) / 2));
    VmAdjust.set(activeConcept(), { xPct: nx, yPct: ny });
    syncAdjusterUI();
  });
  window.addEventListener('mouseup', () => {
    if (vmDrag) {
      vmDrag = null;
      arenaCanvas.classList.remove('dragging');
    }
  });
  arenaCanvas.addEventListener('wheel', (e) => {
    const sim = activeSim();
    if (sim.mode !== '1p' || (!appState.vmDragMode && !e.altKey)) return;
    e.preventDefault();
    const cur = VmAdjust.get(activeConcept());
    if (e.shiftKey) {
      const nr = Math.max(-35, Math.min(35, cur.rotDeg + (e.deltaY < 0 ? 1 : -1)));
      VmAdjust.set(activeConcept(), { rotDeg: nr });
    } else {
      const ns = Math.max(35, Math.min(135, cur.scalePct + (e.deltaY < 0 ? 2 : -2)));
      VmAdjust.set(activeConcept(), { scalePct: ns });
    }
    syncAdjusterUI();
  }, { passive: false });
  arenaCanvas.addEventListener('mouseup', () => {
    if (!vmDrag) releaseCharge(activeSim());
  });
  arenaCanvas.addEventListener('mouseleave', () => {
    const sim = activeSim();
    if (sim.holdDown) releaseCharge(sim);
  });

  // Keyboard shortcuts
  window.addEventListener('keydown', (e) => {
    if (document.activeElement && (document.activeElement.tagName === 'TEXTAREA' || (document.activeElement.tagName === 'INPUT' && document.activeElement.type === 'number'))) return;
    const sim = activeSim();
    if (appState.vmDragMode && sim.mode === '1p' && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
      e.preventDefault();
      const cur = VmAdjust.get(activeConcept());
      const step = e.shiftKey ? 2.0 : 0.5;
      if (e.key === 'ArrowLeft') VmAdjust.set(activeConcept(), { xPct: Math.max(-40, cur.xPct - step) });
      if (e.key === 'ArrowRight') VmAdjust.set(activeConcept(), { xPct: Math.min(45, cur.xPct + step) });
      if (e.key === 'ArrowUp') VmAdjust.set(activeConcept(), { yPct: Math.max(-25, cur.yPct - step) });
      if (e.key === 'ArrowDown') VmAdjust.set(activeConcept(), { yPct: Math.min(45, cur.yPct + step) });
      syncAdjusterUI();
      return;
    }
    if (e.code === 'Space') {
      e.preventDefault();
      if (e.repeat) return;
      if (appState.activeTab === 'compare') {
        for (const c of CONCEPTS) triggerShot(appState.sims[c.id], c.id === 'dookie_mk4', false);
      } else {
        beginCharge(sim, true, true);
      }
    } else if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') {
      sim.keys.left = true;
    } else if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') {
      sim.keys.right = true;
    } else if (e.key === 'p' || e.key === 'P') {
      appState.insp.playing = !appState.insp.playing;
      syncInspectorControls();
    }
  });
  window.addEventListener('keyup', (e) => {
    const sim = activeSim();
    if (e.code === 'Space' && appState.activeTab !== 'compare') releaseCharge(sim);
    if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') sim.keys.left = false;
    if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') sim.keys.right = false;
  });

  // Inspector controls
  document.getElementById('insp-seq').onchange = (e) => {
    appState.insp.seqKey = e.target.value;
    appState.insp.frame = 0;
    syncInspectorControls();
  };
  document.getElementById('insp-play').onclick = () => {
    appState.insp.playing = !appState.insp.playing;
    syncInspectorControls();
  };
  document.getElementById('insp-prev').onclick = () => {
    appState.insp.playing = false;
    stepInspector(-1);
    syncInspectorControls();
  };
  document.getElementById('insp-next').onclick = () => {
    appState.insp.playing = false;
    stepInspector(1);
    syncInspectorControls();
  };
  document.getElementById('insp-scrub').oninput = (e) => {
    appState.insp.playing = false;
    appState.insp.frame = Number(e.target.value);
    syncInspectorControls();
  };
  document.getElementById('insp-angle').oninput = (e) => {
    appState.insp.angle = Number(e.target.value);
    syncInspectorControls();
  };
  document.getElementById('insp-checker').onclick = (e) => {
    appState.insp.checker = !appState.insp.checker;
    e.target.classList.toggle('active', appState.insp.checker);
    document.getElementById('insp-wrap').classList.toggle('checkerboard', appState.insp.checker);
  };
  document.getElementById('insp-zoom').onclick = (e) => {
    appState.insp.zoom = appState.insp.zoom === 1 ? 1.5 : (appState.insp.zoom === 1.5 ? 2 : 1);
    e.target.textContent = appState.insp.zoom + 'x';
  };

  // Ratings
  document.querySelectorAll('#rating-stars .star-btn').forEach(b => {
    b.onclick = () => {
      Ratings.setStars(activeConcept().id, Number(b.dataset.val));
      syncRatingUI();
      renderTabs();
    };
  });
  document.getElementById('rating-notes').oninput = (e) => {
    Ratings.setNotes(activeConcept().id, e.target.value);
  };

  // Compare mode controls
  document.querySelectorAll('#cmp-mode-group .btn').forEach(b => {
    b.onclick = () => {
      appState.compareMode = b.dataset.cmode;
      document.querySelectorAll('#cmp-mode-group .btn').forEach(x => x.classList.toggle('active', x === b));
      for (const c of CONCEPTS) {
        appState.sims[c.id].mode = appState.compareMode === '3p' ? '3p' : '1p';
        if (appState.compareMode !== '3p') {
          appState.sims[c.id].screenSplatAlpha = 0;
          appState.sims[c.id].screenSplats = [];
        }
      }
    };
  });
  document.querySelectorAll('#cmp-speed-group .btn').forEach(b => {
    b.onclick = () => {
      appState.compareSpeed = Number(b.dataset.cspeed);
      document.querySelectorAll('#cmp-speed-group .btn').forEach(x => x.classList.toggle('active', x === b));
    };
  });
  document.getElementById('btn-fire-all').onclick = () => {
    for (const c of CONCEPTS) {
      const s = appState.sims[c.id];
      s.mode = appState.compareMode === '3p' ? '3p' : '1p';
      triggerShot(s, c.id === 'dookie_mk4', false);
    }
  };
}

function stepInspector(delta) {
  const c = activeConcept();
  const seq = c.sequences[appState.insp.seqKey];
  if (!seq) return;
  const maxF = (appState.insp.seqKey === 'proj' && seq.angles > 1) ? seq.fpa : seq.count;
  if (maxF <= 0) return;
  appState.insp.frame = ((Math.floor(appState.insp.frame) + delta) % maxF + maxF) % maxF;
}

function drawInspector(dt) {
  const c = activeConcept();
  const seq = c.sequences[appState.insp.seqKey];
  const canvas = document.getElementById('inspector-canvas');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!seq || seq.count <= 0) {
    ctx.fillStyle = '#a69884';
    ctx.textAlign = 'center';
    ctx.font = '13px ui-monospace, monospace';
    ctx.fillText('No frames packed for this sequence yet', canvas.width * 0.5, canvas.height * 0.5);
    document.getElementById('insp-frame-lbl').textContent = 'Frame 0 / 0';
    return;
  }

  const isProj = appState.insp.seqKey === 'proj' && seq.angles > 1;
  const maxF = isProj ? seq.fpa : seq.count;
  const fps = c.fps || 60;
  if (appState.insp.playing) {
    appState.insp.frame = (appState.insp.frame + dt * fps * appState.speed) % maxF;
  }
  const fIdx = Math.floor(appState.insp.frame);
  document.getElementById('insp-scrub').value = fIdx;
  document.getElementById('insp-frame-lbl').textContent = `Frame ${fIdx + 1} / ${maxF}`;
  document.getElementById('insp-fps-lbl').textContent = `${fps} FPS × ${appState.speed.toFixed(2)}`;

  const fit = Math.min((canvas.width - 16) / seq.fw, (canvas.height - 16) / seq.fh) * appState.insp.zoom;
  const dw = seq.fw * fit;
  const dh = seq.fh * fit;
  const dx = (canvas.width - dw) * 0.5;
  const dy = (canvas.height - dh) * 0.5;

  if (isProj) {
    AtlasStore.drawProj(ctx, seq, appState.insp.angle, fIdx, dx, dy, dw, dh);
  } else {
    AtlasStore.drawFrame(ctx, seq, fIdx, dx, dy, dw, dh);
  }
}

// ---------------------------------------------------------------------------
// 7. Main 60-FPS Animation Loop
// ---------------------------------------------------------------------------
let lastTs = performance.now();
function loop(ts) {
  const dt = Math.min(0.05, Math.max(0.001, (ts - lastTs) / 1000));
  lastTs = ts;
  const timeSec = ts / 1000;

  // Update summary badge once loaded
  const readyCount = CONCEPTS.filter(c => c.ready).length;
  const sfxCount = document.querySelectorAll('#embedded-audio-tags audio').length;
  document.getElementById('asset-summary').textContent =
    `${readyCount}/${CONCEPTS.length} Versions Ready • ${AtlasStore.loadedPages}/${AtlasStore.totalPages} WebP Atlases • ${sfxCount} WAV Clips`;

  if (appState.activeTab === 'compare') {
    for (const c of CONCEPTS) {
      const sim = appState.sims[c.id];
      const cvs = document.getElementById(`cmp-canvas-${c.id}`);
      if (!cvs) continue;
      const ctx = cvs.getContext('2d');
      if (appState.compareMode === 'proj') {
        ctx.clearRect(0, 0, cvs.width, cvs.height);
        drawQuakeCorridor(ctx, cvs.width, cvs.height, 0, 0, timeSec, c.accent);
        const pAtlas = c.sequences.proj;
        if (pAtlas && pAtlas.count > 0) {
          const ang = Math.floor(timeSec * 4) % (pAtlas.angles || 1);
          const frm = Math.floor(timeSec * 24 * appState.compareSpeed);
          const sh = cvs.height * 0.72;
          const sw = sh * (pAtlas.fw / pAtlas.fh);
          AtlasStore.drawProj(ctx, pAtlas, ang, frm, (cvs.width - sw) * 0.5, (cvs.height - sh) * 0.5, sw, sh);
        } else {
          drawFallbackVM(ctx, cvs.width, cvs.height, 0, -40, c);
        }
      } else {
        stepSim(sim, dt, appState.compareSpeed, false, false);
        drawSimCanvas(ctx, cvs.width, cvs.height, sim, timeSec, true);
      }
    }
  } else {
    const sim = activeSim();
    stepSim(sim, dt, appState.speed, appState.autoFire3p, true);
    const arenaCanvas = document.getElementById('arena-canvas');
    drawSimCanvas(arenaCanvas.getContext('2d'), arenaCanvas.width, arenaCanvas.height, sim, timeSec, false);

    document.getElementById('hud-state').textContent =
      (sim.mode === '1p' ? sim.animState : sim.tpState).toUpperCase();
    document.getElementById('hud-shots').textContent = sim.shotsFired;
    document.getElementById('hud-splats').textContent = sim.wallDecals.length;

    drawInspector(dt);
  }

  requestAnimationFrame(loop);
}

// Boot
AtlasStore.init();
AudioVote.load();
AudioFX.predecode();
Ratings.load();
VmAdjust.load();
renderAudioVoteGrid();
bindEvents();
selectTab((CONCEPTS.find(c => c.id === 'dookie_mk4') || CONCEPTS[0]).id);
requestAnimationFrame(loop);
</script>
</body>
</html>
"""


def build_html(work_dir: str, out_html: str, quality: int = 90) -> Dict[str, Any]:
    """Pack all concept sprites, shared FX, and audio into `out_html`."""
    packed_concepts = [pack_concept(meta, work_dir, quality=quality) for meta in CONCEPTS]
    packed_fx = pack_shared_fx(work_dir, quality=quality)
    audio_map = pack_audio(work_dir)

    audio_tags = "\n".join(
        f'  <audio id="sfx-{key}" data-sfx="{key}" preload="auto" src="{uri}"></audio>'
        for key, uri in audio_map.items()
    )

    html = HTML_TEMPLATE
    html = html.replace("__AUDIO_TAGS__", audio_tags)
    html = html.replace("__CONCEPTS_JSON__", json.dumps(packed_concepts, separators=(",", ":")))
    html = html.replace("__FX_JSON__", json.dumps(packed_fx, separators=(",", ":")))

    out_dir = os.path.dirname(os.path.abspath(out_html))
    os.makedirs(out_dir, exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "out_html": out_html,
        "bytes": len(html.encode("utf-8")),
        "concepts": packed_concepts,
        "fx_splats": packed_fx["splats"]["count"] if packed_fx["splats"] else 0,
        "fx_globs": packed_fx["globs"]["count"] if packed_fx["globs"] else 0,
        "fx_mist": packed_fx["mist"]["count"] if packed_fx["mist"] else 0,
        "audio_clips": sorted(audio_map.keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Bakersfield Quake Poop Gun Concept Simulator HTML.")
    parser.add_argument("--work-dir", default=WORK_DIR, help="Path to poop_gun work/ directory")
    parser.add_argument("--out", default=DEFAULT_OUT_HTML, help="Output HTML path")
    parser.add_argument("--quality", type=int, default=90, help="WebP quality (1-100)")
    args = parser.parse_args()

    res = build_html(args.work_dir, args.out, quality=args.quality)
    mb = res["bytes"] / (1024.0 * 1024.0)
    print(f"[build_poop_concepts_html] Wrote {res['out_html']} ({mb:.2f} MB)")
    for c in res["concepts"]:
        counts = {k: (v["count"] if v else 0) for k, v in c["sequences"].items()}
        status = "READY" if c["ready"] else f"MISSING={c['missing']}"
        print(f"  - {c['id']} [{status}]: {counts}")
    print(f"  - shared FX: splats={res['fx_splats']}, globs={res['fx_globs']}, mist={res['fx_mist']}")
    print(f"  - audio ({len(res['audio_clips'])}): {res['audio_clips']}")


if __name__ == "__main__":
    main()
