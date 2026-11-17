"""compile_gw.py — Compile Golden West Casino & S Union Ave (.map -> .bsp + .lit + .spots.json)
using ericw-tools (qbsp -bsp2 -leaktest -subdivide 512, full portal vis,
light -extra4 -bounce 1 -bouncescale 0.90), matching the soi6/compile_soi6.py pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

GW_DIR = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(GW_DIR)
MOD_DIR = os.path.dirname(os.path.dirname(MM_TOOLS_DIR))

if GW_DIR not in sys.path:
    sys.path.insert(0, GW_DIR)

from gw_lib import (  # noqa: E402
    DEFAULT_WAD_PATHS,
    SPECIAL_TEXTURES,
    is_forbidden_tex,
)

GW_OUT_DIR = os.path.join(GW_DIR, "out")
LEGACY_OUT_MAPS_DIR = os.path.join(MM_TOOLS_DIR, "out", "maps")
MOD_MAPS_DIR = os.path.join(MOD_DIR, "maps")

DEFAULT_ERICW_CANDIDATES: Tuple[str, ...] = (
    os.environ.get("ERICW_DIR", ""),
    r"G:\Quake\Combat\tools\ericw",
    r"G:\Quake\TRUEDM3\tools\ericw",
    r"D:\vibe\quake1opensource\tools\ericw",
    "/d/vibe/quake1opensource/tools/ericw",
)

MISSING_TEX_RE = re.compile(
    r"(?:Couldn't locate texture|Unable to find texture|Missing texture)\s+['\"]?([^\s'\"]+)",
    re.IGNORECASE,
)


def _exe_name(tool: str) -> str:
    return f"{tool}.exe" if os.name == "nt" else tool


def find_ericw_dir() -> str:
    """Locate ericw-tools directory containing qbsp, vis, and light executables."""
    for cand in DEFAULT_ERICW_CANDIDATES:
        if not cand or not os.path.isdir(cand):
            continue
        if all(os.path.isfile(os.path.join(cand, _exe_name(t))) for t in ("qbsp", "vis", "light")):
            return os.path.abspath(cand)
    qbsp_path = shutil.which("qbsp")
    if qbsp_path:
        d = os.path.dirname(os.path.abspath(qbsp_path))
        if all(os.path.isfile(os.path.join(d, _exe_name(t))) for t in ("qbsp", "vis", "light")):
            return d
    raise FileNotFoundError(
        "Could not locate ericw-tools (qbsp/vis/light). Checked ERICW_DIR and "
        + ", ".join(c for c in DEFAULT_ERICW_CANDIDATES if c)
    )


def find_wad_file(explicit_wad: Optional[str] = None) -> Optional[str]:
    """Return path to gw2.wad if present on disk."""
    if explicit_wad:
        if os.path.isfile(explicit_wad):
            return os.path.abspath(explicit_wad)
        cand = os.path.join(explicit_wad, "gw2.wad")
        if os.path.isfile(cand):
            return os.path.abspath(cand)
        return os.path.abspath(explicit_wad)
    for p in DEFAULT_WAD_PATHS:
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    return None


def default_map_path() -> str:
    """Resolve the default goldenwest.map input path cleanly across legacy and new layout."""
    candidates = (
        os.path.join(GW_OUT_DIR, "goldenwest.map"),
        os.path.join(LEGACY_OUT_MAPS_DIR, "goldenwest.map"),
    )
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]


def inspect_bsp(bsp_path: str) -> Dict[str, object]:
    """Inspect compiled Quake/BSP2 header lumps, texture list, and forbidden-texture absence."""
    if not os.path.isfile(bsp_path):
        raise FileNotFoundError(f"BSP not found: {bsp_path}")
    size = os.path.getsize(bsp_path)
    with open(bsp_path, "rb") as f:
        hdr = f.read(4 + 15 * 8)
        if len(hdr) < 4 + 15 * 8:
            raise ValueError(f"Truncated BSP header in {bsp_path}")
        magic = hdr[:4]
        is_bsp2 = magic == b"BSP2"
        lumps = [struct.unpack_from("<II", hdr, 4 + i * 8) for i in range(15)]

        # LUMP_ENTITIES = 0, LUMP_PLANES = 1, LUMP_TEXTURES = 2, LUMP_FACES = 7,
        # LUMP_LIGHTING = 8, LUMP_LEAFS = 10, LUMP_MODELS = 14
        tex_ofs, tex_len = lumps[2]
        textures: List[Dict[str, object]] = []
        forbidden: List[str] = []
        if tex_len >= 4 and tex_ofs + tex_len <= size:
            f.seek(tex_ofs)
            tblob = f.read(tex_len)
            num_tex = struct.unpack_from("<i", tblob, 0)[0]
            if 0 < num_tex < 65536 and 4 + num_tex * 4 <= len(tblob):
                offsets = struct.unpack_from(f"<{num_tex}i", tblob, 4)
                for mofs in offsets:
                    if mofs < 0 or mofs + 40 > len(tblob):
                        continue
                    raw_n, w, h, m0, _m1, _m2, _m3 = struct.unpack_from("<16s6I", tblob, mofs)
                    tname = raw_n.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()
                    if not tname:
                        continue
                    textures.append({"name": tname, "w": int(w), "h": int(h), "has_mips": m0 > 0})
                    if is_forbidden_tex(tname):
                        forbidden.append(tname)

    return {
        "bsp_path": os.path.abspath(bsp_path),
        "format": "BSP2" if is_bsp2 else magic.decode("latin1", errors="replace"),
        "size_bytes": size,
        "entities_bytes": lumps[0][1],
        "faces_bytes": lumps[7][1],
        "lighting_bytes": lumps[8][1],
        "vis_bytes": lumps[4][1],
        "texture_count": len(textures),
        "textures": textures,
        "forbidden_textures": sorted(set(forbidden)),
    }


def _run_tool(cmd: List[str], cwd: str, label: str) -> Tuple[int, str, float]:
    t0 = time.time()
    print(f"[{label}] {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    dt = time.time() - t0
    out = proc.stdout or ""
    if out.strip():
        for line in out.splitlines()[-25:]:
            print(f"  {line}")
    return proc.returncode, out, dt


def compile_map(
    map_path: str,
    fast: bool = False,
    threads: Optional[int] = None,
    no_copy: bool = False,
    onlyents: bool = False,
    allow_missing_tex: bool = False,
    wad_override: Optional[str] = None,
    stats_out_path: Optional[str] = None,
    subdivide: int = 512,
    visdist: int = 8400,
) -> Dict[str, object]:
    """Run qbsp -> vis -> light on goldenwest.map and deploy compiled outputs."""
    map_abs = os.path.abspath(map_path)
    if not os.path.isfile(map_abs):
        raise FileNotFoundError(f"Map file not found: {map_abs}")

    ericw_dir = find_ericw_dir()
    qbsp_exe = os.path.join(ericw_dir, _exe_name("qbsp"))
    vis_exe = os.path.join(ericw_dir, _exe_name("vis"))
    light_exe = os.path.join(ericw_dir, _exe_name("light"))

    nthreads = int(threads or os.cpu_count() or 4)
    work_dir = os.path.dirname(map_abs)
    stem = os.path.splitext(os.path.basename(map_abs))[0]
    bsp_path = os.path.join(work_dir, f"{stem}.bsp")
    lit_path = os.path.join(work_dir, f"{stem}.lit")
    pts_path = os.path.join(work_dir, f"{stem}.pts")
    spots_candidates = (
        os.path.join(work_dir, f"{stem}.spots.json"),
        os.path.join(GW_OUT_DIR, f"{stem}.spots.json"),
        os.path.join(LEGACY_OUT_MAPS_DIR, f"{stem}.spots.json"),
    )
    spots_src = next((p for p in spots_candidates if os.path.isfile(p)), None)

    wad_file = find_wad_file(wad_override)
    wad_dir = os.path.dirname(wad_file) if wad_file else LEGACY_OUT_MAPS_DIR

    # Clear stale leak points file before qbsp
    if os.path.isfile(pts_path):
        try:
            os.remove(pts_path)
        except OSError:
            pass

    timings: Dict[str, float] = {}
    missing_textures: List[str] = []

    if onlyents:
        rc, q_out, dt = _run_tool([qbsp_exe, "-onlyents", map_abs, bsp_path], work_dir, "qbsp -onlyents")
        timings["qbsp"] = round(dt, 2)
        if rc != 0:
            raise RuntimeError(f"qbsp -onlyents failed with exit code {rc}")
        rc, _l_out, dt = _run_tool([light_exe, "-onlyents", bsp_path], work_dir, "light -onlyents")
        timings["light"] = round(dt, 2)
        if rc != 0:
            raise RuntimeError(f"light -onlyents failed with exit code {rc}")
    else:
        qbsp_cmd = [
            qbsp_exe,
            "-bsp2",
            "-leaktest",
            "-threads",
            str(nthreads),
            "-wadpath",
            wad_dir,
        ]
        if subdivide and int(subdivide) > 0:
            qbsp_cmd.extend(["-subdivide", str(int(subdivide))])
        qbsp_cmd.extend([map_abs, bsp_path])
        rc, q_out, dt = _run_tool(qbsp_cmd, work_dir, "qbsp")
        timings["qbsp"] = round(dt, 2)
        leaked = ("leak" in q_out.lower() and "leaked" in q_out.lower()) or os.path.isfile(pts_path)
        if rc != 0 or leaked:
            raise RuntimeError(
                f"qbsp failed (rc={rc}, leaked={leaked}). "
                + (f"Leak pointfile written at {pts_path}" if os.path.isfile(pts_path) else "")
            )

        for m in MISSING_TEX_RE.finditer(q_out):
            tname = m.group(1).strip()
            if tname.lower() not in SPECIAL_TEXTURES and not tname.lower().startswith("sky"):
                missing_textures.append(tname)
        missing_textures = sorted(set(missing_textures))
        if missing_textures and not allow_missing_tex:
            raise RuntimeError(
                f"qbsp reported {len(missing_textures)} missing texture(s): {', '.join(missing_textures[:15])}"
            )

        vis_cmd = [vis_exe, "-threads", str(nthreads)]
        if visdist and int(visdist) > 0:
            vis_cmd.extend(["-visdist", str(int(visdist))])
        vis_cmd.append(bsp_path)
        rc, _v_out, dt = _run_tool(vis_cmd, work_dir, "vis")
        timings["vis"] = round(dt, 2)
        if rc != 0:
            raise RuntimeError(f"vis failed with exit code {rc}")

        light_cmd = [light_exe, "-threads", str(nthreads)]
        if fast:
            light_cmd.append("-extra")
        else:
            light_cmd.extend(["-extra4", "-bounce", "1", "-bouncescale", "0.65"])
        light_cmd.append(bsp_path)
        rc, _l_out, dt = _run_tool(light_cmd, work_dir, "light")
        timings["light"] = round(dt, 2)
        if rc != 0:
            raise RuntimeError(f"light failed with exit code {rc}")

        if MM_TOOLS_DIR not in sys.path:
            sys.path.insert(0, MM_TOOLS_DIR)
        import fog_vis_tools as fvt  # noqa: E402
        if visdist and int(visdist) > 0:
            fvt.prune_pvs(bsp_path, visdist=int(visdist), keep_sky=True, backup=False)
        else:
            fvt.keep_sky_pvs(bsp_path, backup=False)

    bsp_info = inspect_bsp(bsp_path)
    if bsp_info["forbidden_textures"]:
        raise RuntimeError(
            "Compiled BSP contains forbidden legacy textures: "
            + ", ".join(bsp_info["forbidden_textures"])
        )

    copied_paths: List[str] = []
    if not no_copy:
        dest_dirs = [MOD_MAPS_DIR, LEGACY_OUT_MAPS_DIR]
        for ddir in dest_dirs:
            os.makedirs(ddir, exist_ok=True)
            for src_file in (bsp_path, lit_path, spots_src):
                if src_file and os.path.isfile(src_file):
                    dst_file = os.path.join(ddir, os.path.basename(src_file))
                    if os.path.abspath(src_file) != os.path.abspath(dst_file):
                        shutil.copy2(src_file, dst_file)
                    copied_paths.append(dst_file)

    stats = {
        "map_path": map_abs,
        "bsp_path": bsp_path,
        "lit_path": lit_path if os.path.isfile(lit_path) else None,
        "spots_path": spots_src,
        "wad_used": wad_file,
        "wad_dir": wad_dir,
        "ericw_dir": ericw_dir,
        "fast": bool(fast),
        "onlyents": bool(onlyents),
        "subdivide": int(subdivide) if subdivide and int(subdivide) > 0 else 240,
        "threads": nthreads,
        "timings_sec": timings,
        "total_sec": round(sum(timings.values()), 2),
        "missing_textures": missing_textures,
        "bsp": {
            "format": bsp_info["format"],
            "size_bytes": bsp_info["size_bytes"],
            "entities_bytes": bsp_info["entities_bytes"],
            "faces_bytes": bsp_info["faces_bytes"],
            "lighting_bytes": bsp_info["lighting_bytes"],
            "vis_bytes": bsp_info["vis_bytes"],
            "texture_count": bsp_info["texture_count"],
            "forbidden_textures": bsp_info["forbidden_textures"],
        },
        "copied_outputs": copied_paths,
    }

    stats_path = os.path.abspath(stats_out_path or os.path.join(GW_OUT_DIR, "compile_stats.json"))
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    stats["stats_path"] = stats_path
    return stats


def _run_helper_script(script_path: str, label: str) -> None:
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Expected script not found for {label}: {script_path}")
    print(f"[{label}] Running {script_path}")
    proc = subprocess.run([sys.executable, script_path], cwd=MOD_DIR)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} exited with status {proc.returncode}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile Golden West Casino & S Union Ave Quake map (qbsp + vis + light)."
    )
    parser.add_argument("--map", default=None, help="Input .map file (defaults to goldenwest/out/goldenwest.map)")
    parser.add_argument("--build", action="store_true", help="Run make_goldenwest.py to emit .map before compiling")
    parser.add_argument("--sky", action="store_true", help="Run build_sky.py before compiling")
    parser.add_argument("--fast", action="store_true", help="Use light -extra instead of -extra4 -bounce 1 (always runs full portal VIS)")
    parser.add_argument("--subdivide", type=int, default=512, help="qbsp face subdivision threshold (default: 512; 0 uses qbsp default 240)")
    parser.add_argument("--visdist", type=int, default=8400, help="vis -visdist / PVS prune distance in units (default: 8400; 0 disables)")
    parser.add_argument("--threads", type=int, default=0, help="Worker thread count (0 = auto)")
    parser.add_argument("--no-copy", action="store_true", help="Do not copy outputs to maps/ and out/maps/")
    parser.add_argument("--onlyents", action="store_true", help="Re-embed entities and relight only")
    parser.add_argument("--allow-missing-tex", action="store_true", help="Allow missing WAD textures (debug only)")
    parser.add_argument("--wadpath", default=None, help="Explicit path to gw2.wad or its directory")
    parser.add_argument("--stats-out", default=None, help="Override path for compile_stats.json")
    args = parser.parse_args(argv)

    if args.sky:
        _run_helper_script(os.path.join(GW_DIR, "build_sky.py"), "build_sky")

    if args.build:
        build_script = os.path.join(GW_DIR, "make_goldenwest.py")
        if not os.path.isfile(build_script):
            build_script = os.path.join(MM_TOOLS_DIR, "make_goldenwest.py")
        _run_helper_script(build_script, "make_goldenwest")

    map_path = args.map or default_map_path()
    stats = compile_map(
        map_path=map_path,
        fast=args.fast,
        threads=args.threads or None,
        no_copy=args.no_copy,
        onlyents=args.onlyents,
        allow_missing_tex=args.allow_missing_tex,
        wad_override=args.wadpath,
        stats_out_path=args.stats_out,
        subdivide=args.subdivide,
        visdist=args.visdist,
    )
    print(
        f"[compile_gw] DONE in {stats['total_sec']}s: "
        f"{stats['bsp']['format']} {stats['bsp']['size_bytes']} bytes, "
        f"{stats['bsp']['texture_count']} textures, stats -> {stats['stats_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
