"""export_gw_web.py — Export Golden West Casino & S Union Ave for Three.js WebGL viewer.

Modeled on source/mm_tools/soi6/export_soi6_web.py:
  1. Wipes stale source/mm_tools/out/web/goldenwest/tex/ (removes legacy Nov 3 bk_* pollution).
  2. Runs export_web_viewer.py on maps/goldenwest.bsp + .lit + spots.json (+ MD3 misc_model props).
  3. Overwrites sky/*.jpg with build_sky.build_web_sky(..., size=512) so WebGL uses gwsky
     rather than export_web_viewer.py's legacy bklan fallback.
  4. Patches Fox WebGL viewer template to calibrated bright=1.00 (matching WASM DarkPlaces
     web.cfg v_gamma 1 / v_contrast 1), WASD + Space + F controls, and ?fly=1 / ?nointro=1 params.
  5. Asserts 0 missing world/prop textures & glow maps, 0 legacy bk_*/{bk3_/{chain textures,
     all 6 gwsky_* DP + WebGL skybox faces present, and writes out/web_export_stats.json.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List

GW_DIR = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(GW_DIR)
MOD_DIR = os.path.dirname(os.path.dirname(MM_TOOLS))
OUT_DIR = os.path.join(GW_DIR, "out")
FOX_WEB = os.path.join(MM_TOOLS, "out", "web", "fox")
WEB_OUT = os.path.join(MM_TOOLS, "out", "web", "goldenwest")

for _p in (GW_DIR, MM_TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from build_sky import build_web_sky  # noqa: E402
from gw_lib import FORBIDDEN_TEX_PREFIXES, is_forbidden_tex  # noqa: E402

SKY_FACES = ("rt", "lf", "up", "dn", "ft", "bk")


def _dir_bytes(path: str) -> int:
    if not os.path.isdir(path):
        return 0
    return sum(
        os.path.getsize(os.path.join(dp, fn))
        for dp, _, fns in os.walk(path)
        for fn in fns
    )


def _sync_spots_json() -> str:
    """Ensure export_web_viewer.py can read the authoritative goldenwest.spots.json."""
    candidates = [
        os.path.join(MOD_DIR, "maps", "goldenwest.spots.json"),
        os.path.join(OUT_DIR, "goldenwest.spots.json"),
        os.path.join(MM_TOOLS, "out", "maps", "goldenwest.spots.json"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    if not existing:
        raise FileNotFoundError(
            "Missing goldenwest.spots.json in maps/, goldenwest/out/, or out/maps/"
        )
    newest = max(existing, key=os.path.getmtime)
    target = os.path.join(OUT_DIR, "goldenwest.spots.json")
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.abspath(newest) != os.path.abspath(target):
        shutil.copy2(newest, target)
    return newest


def _safe_to_tex(safe_name: str) -> str:
    if safe_name.startswith("fence_"):
        return "{" + safe_name[len("fence_"):]
    if safe_name.startswith("star_"):
        return "*" + safe_name[len("star_"):]
    return safe_name


def _patch_viewer_html(template_html: str) -> str:
    """Apply Golden West metadata, bright=1.00 calibration, and ?fly=1 / ?nointro=1 params."""
    html = template_html

    html = re.sub(
        r"<title>.*?</title>",
        "<title>Golden West Casino &amp; Great Castle &middot; S Union Ave, Bakersfield (1:1 Quake Replica)</title>",
        html,
        flags=re.S,
    )

    cam_old = "const camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 2, 40000);"
    cam_new = "const camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 2, 60000);"
    assert cam_old in html, "Expected PerspectiveCamera far=40000 in Fox template"
    html = html.replace(cam_old, cam_new, 1)

    assert 'value="1.35"' in html, "Expected default bright slider value=\"1.35\" in Fox template"
    assert "const bright = { value: 1.35 };" in html, "Expected bright uniform 1.35 in Fox template"
    html = html.replace('value="1.35"', 'value="1.00"')
    html = html.replace("const bright = { value: 1.35 };", "const bright = { value: 1.00 };")

    html = html.replace(
        "1:1 Scale Downtown Bakersfield &middot; fox.bsp",
        "1:1 Scale South Union Ave, Bakersfield (12 u/ft &middot; 39.37 u/m) &middot; goldenwest.bsp",
    )
    html = html.replace(
        "<h1>Fox Theater &amp; The Padre Hotel</h1>",
        "<h1>Golden West Casino &amp; Great Castle &middot; S Union Ave</h1>",
    )
    html, p_subs = re.subn(
        r"<h1>Golden West Casino &amp; Great Castle &middot; S Union Ave</h1>\s*<p>.*?</p>",
        "<h1>Golden West Casino &amp; Great Castle &middot; S Union Ave</h1>\n"
        "  <p>1:1 scale sunny-day Quake replica of <b>Golden West Casino</b> (1001 S Union Ave), "
        "<b>Great Castle Restaurant</b> (410 Union Ave) &amp; S Union Ave (Amador Ave to E 5th St): "
        "enterable gaming floor &amp; rotunda, bronze horse plaza, crenellated castle hall &amp; lantern dining room, "
        "Deal Time Auto, Reyes Tires, DG market, Star-Liter &amp; Country Inn motels, Super 8 &amp; "
        "6-lane S Union Blvd. Use <b>W A S D</b> to walk, <b>Space</b> to jump, and <b>F</b> to free-fly anywhere.</p>",
        html,
        flags=re.S,
    )
    assert p_subs == 1, "Failed to replace intro paragraph in Fox template"

    html = html.replace(">Asset &amp; Map Showcase</a>", ">Audit Report &amp; Map Showcase</a>")

    # Add ?fly=1 and ?nointro=1 URL query handling matching Golden West showcase deep links
    if 'get("fly")' not in html:
        spot_hook = 'const wantSpot = new URLSearchParams(location.search).get("spot");'
        assert spot_hook in html, "Expected wantSpot query parser in Fox template"
        html = html.replace(
            spot_hook,
            spot_hook + '\nconst wantFly = new URLSearchParams(location.search).get("fly");\n'
            'if (new URLSearchParams(location.search).get("nointro")) $("intro").style.display = "none";',
            1,
        )
    if "setFly(true);" not in html or 'wantFly === "1"' not in html:
        tp_hook = "teleport(meta.spots[initIdx]);"
        assert tp_hook in html, "Expected initial teleport(meta.spots[initIdx]) in Fox template"
        html = html.replace(
            tp_hook,
            tp_hook + '\nif (wantFly === "1" || wantFly === "true") setFly(true);',
            1,
        )

    # Enforce walk (WASD), jump (Space), free-fly (F), calibrated bright=1.00, and far=60000 bindings are intact
    for token in ("KeyW", "KeyA", "KeyS", "KeyD", "Space", "KeyF", "setFly", "bright = { value: 1.00 }", ", 2, 60000);"):
        assert token in html, f"Patched index.html missing required viewer contract token: {token}"

    return html


def main() -> int:
    bsp_path = os.path.join(MOD_DIR, "maps", "goldenwest.bsp")
    lit_path = os.path.join(MOD_DIR, "maps", "goldenwest.lit")
    if not os.path.isfile(bsp_path):
        raise FileNotFoundError(f"Compiled BSP not found: {bsp_path}")
    if not os.path.isfile(lit_path):
        raise FileNotFoundError(f"Compiled LIT not found: {lit_path}")

    spots_src = _sync_spots_json()
    print(f"[export_gw_web] Using spots from {spots_src}")

    os.makedirs(WEB_OUT, exist_ok=True)
    # Wipe stale exported textures & sky faces so removed/legacy bk_* PNGs never linger
    tex_out = os.path.join(WEB_OUT, "tex")
    if os.path.isdir(tex_out):
        shutil.rmtree(tex_out)
    sky_out = os.path.join(WEB_OUT, "sky")
    if os.path.isdir(sky_out):
        shutil.rmtree(sky_out)

    exporter = os.path.join(MM_TOOLS, "export_web_viewer.py")
    subprocess.run([sys.executable, exporter, WEB_OUT, "goldenwest"], cwd=MM_TOOLS, check=True)

    # Override export_web_viewer.py line 480 (which falls back to build_bklan_sky) with gwsky
    build_web_sky(sky_out, size=512)

    # Verify DarkPlaces gwsky_* files & WebGL sky/*.jpg faces
    missing_sky: List[str] = []
    for face in SKY_FACES:
        dp_png = os.path.join(MOD_DIR, "gfx", "env", f"gwsky_{face}.png")
        gl_jpg = os.path.join(sky_out, f"{face}.jpg")
        if not os.path.isfile(dp_png):
            missing_sky.append(f"gfx/env/gwsky_{face}.png")
        if not os.path.isfile(gl_jpg) or os.path.getsize(gl_jpg) < 100:
            missing_sky.append(f"out/web/goldenwest/sky/{face}.jpg")
    assert not missing_sky, f"Missing skybox assets: {missing_sky}"

    # Copy shared Three.js viewer runtime & dev overlay from Fox template
    lib_dir = os.path.join(WEB_OUT, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    shutil.copy2(os.path.join(FOX_WEB, "lib", "three.module.min.js"), os.path.join(lib_dir, "three.module.min.js"))
    shutil.copy2(os.path.join(FOX_WEB, "dev_overlay.js"), os.path.join(WEB_OUT, "dev_overlay.js"))

    with open(os.path.join(FOX_WEB, "index.html"), "r", encoding="utf-8") as f:
        html = _patch_viewer_html(f.read())
    with open(os.path.join(WEB_OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # Inspect exported map.json
    map_json_path = os.path.join(WEB_OUT, "map.json")
    with open(map_json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Normalize spots from authoritative .spots.json into flat Three.js schema [{name, pos, yaw, pitch}]
    with open(spots_src, "r", encoding="utf-8") as f:
        spots_raw = json.load(f)
    raw_list = spots_raw.get("spots", []) if isinstance(spots_raw, dict) else (spots_raw or [])
    norm_spots: List[Dict[str, object]] = []
    for sp in raw_list:
        if not isinstance(sp, dict):
            continue
        pos = sp.get("pos") or sp.get("origin") or [0.0, 0.0, 0.0]
        angles = sp.get("angles") or [0.0, 0.0, 0.0]
        pitch = float(sp["pitch"]) if "pitch" in sp else (float(angles[0]) if len(angles) > 0 else 0.0)
        yaw = float(sp["yaw"]) if "yaw" in sp else (float(angles[1]) if len(angles) > 1 else 0.0)
        entry: Dict[str, object] = {
            "name": str(sp.get("name", "Spot")),
            "pos": [float(pos[0]), float(pos[1]), float(pos[2])],
            "yaw": yaw,
            "pitch": pitch,
        }
        if sp.get("kind"):
            entry["kind"] = sp["kind"]
        if sp.get("desc"):
            entry["desc"] = sp["desc"]
        norm_spots.append(entry)

    if norm_spots:
        meta["spots"] = norm_spots
        with open(map_json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
    assert isinstance(meta.get("spots"), list) and len(meta["spots"]) >= 1, "map.json has 0 normalized spots"
    assert "pos" in meta["spots"][0] and "yaw" in meta["spots"][0], "Normalized spot missing pos/yaw"

    missing_tex: List[str] = []
    forbidden_world: List[str] = []

    for g in meta.get("world", []):
        tname = g["tex"]
        orig_name = _safe_to_tex(tname)
        if is_forbidden_tex(tname) or is_forbidden_tex(orig_name):
            forbidden_world.append(tname)
        tp = os.path.join(tex_out, tname + ".png")
        if not os.path.isfile(tp):
            missing_tex.append(tname + ".png")
        if g.get("glow"):
            gp = os.path.join(tex_out, tname + "_glow.png")
            if not os.path.isfile(gp):
                missing_tex.append(tname + "_glow.png")

    prop_names: List[str] = []
    prop_surfaces = 0
    for mdl in meta.get("models", []):
        mname = mdl.get("name") or mdl.get("mdl", "")
        prop_names.append(mname)
        for surf in mdl.get("surfaces", []):
            prop_surfaces += 1
            tname = surf["tex"]
            tp = os.path.join(tex_out, tname + ".png")
            if not os.path.isfile(tp):
                missing_tex.append(f"prop:{mname}:{tname}.png")
            if surf.get("glow"):
                gp = os.path.join(tex_out, tname + "_glow.png")
                if not os.path.isfile(gp):
                    missing_tex.append(f"prop:{mname}:{tname}_glow.png")

    # Verify zero stale bk_*/bklan*/fence_bk*/fence_chain/sky_bk PNGs landed in tex/
    stale_prefixes = ("bklan", "bk_", "fence_bk", "fence_chain", "sky_bk")
    stale_tex: List[str] = []
    if os.path.isdir(tex_out):
        for fn in os.listdir(tex_out):
            if fn.endswith(".png"):
                stem = fn[:-4]
                orig = _safe_to_tex(stem)
                if is_forbidden_tex(stem) or is_forbidden_tex(orig) or stem.lower().startswith(stale_prefixes):
                    stale_tex.append(fn)

    assert not forbidden_world, f"Forbidden legacy world textures exported: {sorted(set(forbidden_world))}"
    assert not stale_tex, f"Forbidden legacy PNGs present in tex/: {sorted(stale_tex)}"
    assert not missing_tex, f"Missing WebGL textures/glows: {sorted(set(missing_tex))}"

    map_bin_b = os.path.getsize(os.path.join(WEB_OUT, "map.bin"))
    map_json_b = os.path.getsize(map_json_path)
    lightmap_b = os.path.getsize(os.path.join(WEB_OUT, "lightmap.png"))
    tex_b = _dir_bytes(tex_out)
    sky_b = _dir_bytes(sky_out)
    core_b = map_bin_b + map_json_b + lightmap_b + tex_b + sky_b
    total_b = _dir_bytes(WEB_OUT)

    world_tris = sum(g["count"] for g in meta.get("world", [])) // 3
    tex_files = [fn for fn in os.listdir(tex_out) if fn.endswith(".png")]
    report: Dict[str, object] = {
        "web_out": WEB_OUT,
        "draw_groups": len(meta.get("world", [])),
        "world_triangles": world_tris,
        "hull_trees": len(meta.get("hulls", [])),
        "prop_models": len(meta.get("models", [])),
        "prop_model_paths": sorted(set(prop_names)),
        "prop_instances": len(meta.get("instances", [])),
        "prop_surfaces": prop_surfaces,
        "spots": len(meta.get("spots", [])),
        "tex_png_count": len(tex_files),
        "lightmap_px": meta.get("lightmap", []),
        "bright_default": 1.00,
        "skybox": "gwsky",
        "sizes_kb": {
            "map_bin": round(map_bin_b / 1024.0, 1),
            "map_json": round(map_json_b / 1024.0, 1),
            "lightmap_png": round(lightmap_b / 1024.0, 1),
            "tex_dir": round(tex_b / 1024.0, 1),
            "sky_dir": round(sky_b / 1024.0, 1),
            "core_assets_mb": round(core_b / (1024.0 * 1024.0), 2),
            "total_bundle_mb": round(total_b / (1024.0 * 1024.0), 2),
        },
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    stats_path = os.path.join(OUT_DIR, "web_export_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(
        f"[export_gw_web] Verified 0 missing textures/glows, 0 forbidden bk_* textures: "
        f"{report['draw_groups']} draw groups, {report['world_triangles']:,} tris, "
        f"{report['hull_trees']} Hull-1 trees, {report['prop_instances']} prop instances, "
        f"{report['spots']} spots."
    )
    print(
        f"[export_gw_web] Bundle: core={report['sizes_kb']['core_assets_mb']} MB, "
        f"total={report['sizes_kb']['total_bundle_mb']} MB -> {WEB_OUT}"
    )
    print(f"[export_gw_web] Stats -> {stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
