#!/usr/bin/env python3
"""Build maps/practice.bsp and maps/practice.lit: dark space floating Practice Range.

Layout (6144 x 6144 floating space deck inside a 9216 x 9216 starry void):
  - Wide-open dark steel deck floating in deep starry space (pracspace_ skybox,
    no perimeter walls blocking the stars; trigger_hurt void kill below).
  - Central hole (-128..+128, depth 96 to z = -96) containing a jump pad
    (trigger_push launching straight up; dressed with progs/q3pad.md3 by q3pad.qc).
  - 1 Mega Man Tank (misc_mm_tank)
  - 1 Go-Kart (misc_gokart, cnt=1)
  - Custom powerup only:
      * item_powerup_triple_wheeled   (Dual Wield)
  - Paired with practice.qc which spawns 1 walking, non-shooting enemy player
    model (progs/player_id1.mdl) patrolling around the central arena.

Reproducible: fixed WAD2, sorted brushes/entities, single-threaded ericw-tools
compilation; --verify-repro builds twice into temp dirs and verifies identical SHA-256.

Usage:
  python -I source/mm_tools/build_practice_map.py [--ericw DIR] [--out-dir DIR] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

ARENA_HALF = 3072       # 6144 x 6144 wide-open floating platform
DECK_THICK = 96         # platform slab thickness (z = -96..0)
VOID_HALF = 4608        # outer skybox enclosure half-width
VOID_TOP = 2304         # sky ceiling height
VOID_BOT = -1024        # sky floor depth
HOLE_HALF = 128         # 256 x 256 center hole
HOLE_DEPTH = 96         # bottom at z = -96
PAD_HALF = 45           # 90 x 90 trigger_push -> dressed as ~97u q3pad.md3


def _wad_miptex(name: str, w: int = 64, h: int = 64, pal_index: int = 2) -> bytes:
    """Build a minimal valid 4-mip WAD2 miptex lump using Quake palette grey index."""
    data = b""
    ofs = []
    cur = 40
    for m in range(4):
        mw = max(1, w >> m)
        mh = max(1, h >> m)
        ofs.append(cur)
        cur += mw * mh
        data += bytes([pal_index]) * (mw * mh)
    return struct.pack("<16s2I4I", name.encode("ascii")[:15], w, h, *ofs) + data


def write_practice_wad(wad_path: Path) -> None:
    """Write a minimal deterministic WAD2 with the texture names used by practice.map.

    DarkPlaces/Zircon resolves prac_deck, prac_pit, and prac_trim to the textures in
    zz_practice.pk3; the WAD2 provides qbsp/light dimensions and dark albedo.
    """
    specs = [
        ("prac_deck", 2),
        ("prac_pit", 1),
        ("prac_trim", 3),
        ("sky", 0),
        ("trigger", 0),
    ]
    lumps = [(name, _wad_miptex(name, pal_index=idx)) for name, idx in specs]
    body = bytearray()
    dirs = bytearray()
    pos = 12
    for name, blob in lumps:
        dirs += struct.pack("<3i2bh16s", pos, len(blob), len(blob), 0x44, 0, 0, name.encode("ascii")[:15])
        body += blob
        pos += len(blob)
    wad_path.write_bytes(struct.pack("<4sii", b"WAD2", len(lumps), pos) + bytes(body) + bytes(dirs))


def brush_box(
    x0: int,
    y0: int,
    z0: int,
    x1: int,
    y1: int,
    z1: int,
    tex_top: str,
    tex_side: str | None = None,
    tex_bot: str | None = None,
) -> str:
    if tex_side is None:
        tex_side = tex_top
    if tex_bot is None:
        tex_bot = tex_side
    lines = [
        "{",
        f"( {x0} {y1} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y0} {z1} ) {tex_top} 0 0 0 1 1",
        f"( {x0} {y0} {z0} ) ( {x1} {y0} {z0} ) ( {x1} {y1} {z0} ) {tex_bot} 0 0 0 1 1",
        f"( {x0} {y1} {z1} ) ( {x0} {y0} {z1} ) ( {x0} {y0} {z0} ) {tex_side} 0 0 0 1 1",
        f"( {x1} {y0} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y1} {z0} ) {tex_side} 0 0 0 1 1",
        f"( {x1} {y1} {z1} ) ( {x0} {y1} {z1} ) ( {x0} {y1} {z0} ) {tex_side} 0 0 0 1 1",
        f"( {x0} {y0} {z1} ) ( {x1} {y0} {z1} ) ( {x1} {y0} {z0} ) {tex_side} 0 0 0 1 1",
        "}",
    ]
    return "\n".join(lines)


def fmt_ent(kv: dict[str, str], brushes: list[str] | None = None) -> str:
    out = ["{"]
    for k, v in kv.items():
        out.append(f'"{k}" "{v}"')
    if brushes:
        out.extend(brushes)
    out.append("}")
    return "\n".join(out)


def build_map_text(wad_path: Path) -> str:
    S = ARENA_HALF
    T = DECK_THICK
    V = VOID_HALF
    VT = VOID_TOP
    VB = VOID_BOT
    W = 64
    P = HOLE_HALF
    D = HOLE_DEPTH

    world_brushes = [
        # Floating dark space deck around the central hole (-P..+P)
        brush_box(-S, -S, -T, -P, S, 0, "prac_deck", "prac_trim", "prac_pit"),
        brush_box(P, -S, -T, S, S, 0, "prac_deck", "prac_trim", "prac_pit"),
        brush_box(-P, -S, -T, P, -P, 0, "prac_deck", "prac_pit", "prac_pit"),
        brush_box(-P, P, -T, P, S, 0, "prac_deck", "prac_pit", "prac_pit"),
        # Pit bottom closing the central hole at z = -96
        brush_box(-P - 64, -P - 64, -D - 64, P + 64, P + 64, -D, "prac_pit", "prac_pit"),
        # Open space skybox enclosure far outside the floating platform
        brush_box(-V - W, -V - W, VB - W, -V, V + W, VT + W, "sky", "sky"),
        brush_box(V, -V - W, VB - W, V + W, V + W, VT + W, "sky", "sky"),
        brush_box(-V, -V - W, VB - W, V, -V, VT + W, "sky", "sky"),
        brush_box(-V, V, VB - W, V, V + W, VT + W, "sky", "sky"),
        brush_box(-V, -V, VT, V, V, VT + W, "sky", "sky"),
        brush_box(-V, -V, VB - W, V, V, VB, "sky", "sky"),
    ]

    world_kv = {
        "classname": "worldspawn",
        "message": "Bakersfield Space Practice",
        "wad": wad_path.name,
        "skyname": "pracspace_",
        "_minlight": "16",
        "_minlight_color": "115 125 185",
        "_sunlight": "58",
        "_sunlight_mangle": "55 -48 0",
        "_sunlight_color": "0.75 0.82 1.0",
        "_sunlight2": "26",
        "_sunlight2_color": "0.55 0.42 0.85",
    }

    entities: list[str] = [fmt_ent(world_kv, world_brushes)]

    # Jump pad inside the central hole
    entities.append(
        fmt_ent(
            {
                "classname": "trigger_push",
                "angle": "-1",
                "speed": "95",
            },
            [brush_box(-PAD_HALF, -PAD_HALF, -D, PAD_HALF, PAD_HALF, -D + 64, "trigger")],
        )
    )

    # Space void fall kill trigger below the floating deck
    entities.append(
        fmt_ent(
            {
                "classname": "trigger_hurt",
                "dmg": "9999",
            },
            [brush_box(-V + 64, -V + 64, VB + 32, V - 64, V - 64, -480, "trigger")],
        )
    )

    # Singleplayer start & deathmatch spawns
    entities.append(
        fmt_ent(
            {
                "classname": "info_player_start",
                "origin": "0 -640 28",
                "angle": "90",
            }
        )
    )
    dm_spawns = [
        (0, -640, 90),
        (-360, -780, 75),
        (360, -780, 105),
        (-820, -320, 20),
        (820, -320, 160),
        (-820, 320, 340),
        (820, 320, 200),
        (0, 920, 270),
    ]
    for sx, sy, sang in dm_spawns:
        entities.append(
            fmt_ent(
                {
                    "classname": "info_player_deathmatch",
                    "origin": f"{sx} {sy} 28",
                    "angle": str(sang),
                }
            )
        )

    # 1 Mega Man Tank and 1 Go-Kart
    entities.append(
        fmt_ent(
            {
                "classname": "misc_mm_tank",
                "origin": "-560 -120 12",
                "angles": "0 330 0",
            }
        )
    )
    entities.append(
        fmt_ent(
            {
                "classname": "misc_gokart",
                "origin": "560 -120 12",
                "angles": "0 210 0",
                "cnt": "1",
            }
        )
    )

    # Custom powerup only, centered north of the arena hole
    powerups = [
        ("item_powerup_triple_wheeled", 0, 520),
    ]
    for cls, px, py in powerups:
        entities.append(
            fmt_ent(
                {
                    "classname": cls,
                    "origin": f"{px} {py} 24",
                }
            )
        )

    # Moody space accent lighting: warm gold center-hole glow, cool pools on assets, faint rim lights
    entities.append(fmt_ent({"classname": "light", "origin": "0 0 -16", "light": "320", "_color": "1 0.78 0.38"}))
    entities.append(fmt_ent({"classname": "light", "origin": "0 0 110", "light": "280", "_color": "1 0.82 0.48"}))
    entities.append(fmt_ent({"classname": "light", "origin": "-560 -120 220", "light": "260", "_color": "0.68 0.85 1"}))
    entities.append(fmt_ent({"classname": "light", "origin": "560 -120 220", "light": "260", "_color": "1 0.76 0.48"}))
    entities.append(fmt_ent({"classname": "light", "origin": "0 520 180", "light": "220", "_color": "0.55 1 0.75"}))
    entities.append(fmt_ent({"classname": "light", "origin": "0 -640 190", "light": "200", "_color": "0.72 0.82 1"}))
    for lx in (-2600, 0, 2600):
        for ly in (-2600, 0, 2600):
            if lx == 0 and ly == 0:
                continue
            entities.append(
                fmt_ent({"classname": "light", "origin": f"{lx} {ly} 900", "light": "340", "_color": "0.65 0.72 1"})
            )

    return "\n".join(entities) + "\n"


def find_ericw_dir(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.resolve())
    env_dir = os.environ.get("ERICW_DIR")
    if env_dir:
        candidates.append(Path(env_dir).resolve())
    candidates.append((REPO / "build" / "ericw").resolve())
    for cand in candidates:
        if (cand / "qbsp").is_file() and (cand / "vis").is_file() and (cand / "light").is_file():
            return cand
        if (cand / "qbsp.exe").is_file() and (cand / "vis.exe").is_file() and (cand / "light.exe").is_file():
            return cand
    qbsp = shutil.which("qbsp")
    if qbsp:
        return Path(qbsp).resolve().parent
    raise FileNotFoundError("Could not locate ericw-tools (qbsp, vis, light). Pass --ericw or set ERICW_DIR.")


def _tool_exe(ericw_dir: Path, name: str) -> str:
    p = (ericw_dir / name).resolve()
    if p.is_file():
        return str(p)
    p_exe = (ericw_dir / f"{name}.exe").resolve()
    if p_exe.is_file():
        return str(p_exe)
    raise FileNotFoundError(f"Missing {name} in {ericw_dir}")


def compile_once(ericw_dir: Path, out_dir: Path) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="practice_bsp_") as tmp:
        work = Path(tmp)
        wad_path = work / "practice.wad"
        map_path = work / "practice.map"
        bsp_path = work / "practice.bsp"
        lit_path = work / "practice.lit"

        write_practice_wad(wad_path)
        map_path.write_text(build_map_text(wad_path), encoding="ascii")

        qbsp = _tool_exe(ericw_dir, "qbsp")
        vis = _tool_exe(ericw_dir, "vis")
        light = _tool_exe(ericw_dir, "light")

        # Single-threaded for deterministic output across runs
        r_qbsp = subprocess.run(
            [qbsp, "-nolog", "-threads", "1", "-bsp2", "-leaktest", str(map_path), str(bsp_path)],
            cwd=str(work),
            capture_output=True,
            text=True,
        )
        if r_qbsp.returncode != 0:
            raise RuntimeError(f"qbsp failed ({r_qbsp.returncode}):\n{r_qbsp.stdout}\n{r_qbsp.stderr}")

        r_vis = subprocess.run(
            [vis, "-nolog", "-threads", "1", "-fast", str(bsp_path)],
            cwd=str(work),
            capture_output=True,
            text=True,
        )
        if r_vis.returncode != 0:
            raise RuntimeError(f"vis failed ({r_vis.returncode}):\n{r_vis.stdout}\n{r_vis.stderr}")

        r_light = subprocess.run(
            [light, "-nolog", "-threads", "1", str(bsp_path)],
            cwd=str(work),
            capture_output=True,
            text=True,
        )
        if r_light.returncode != 0:
            raise RuntimeError(f"light failed ({r_light.returncode}):\n{r_light.stdout}\n{r_light.stderr}")

        bsp_bytes = bsp_path.read_bytes()
        lit_bytes = lit_path.read_bytes() if lit_path.is_file() else b""

        out_dir.mkdir(parents=True, exist_ok=True)
        out_bsp = out_dir / "practice.bsp"
        out_lit = out_dir / "practice.lit"
        out_bsp.write_bytes(bsp_bytes)
        if lit_bytes:
            out_lit.write_bytes(lit_bytes)

        bsp_sha = hashlib.sha256(bsp_bytes).hexdigest()
        lit_sha = hashlib.sha256(lit_bytes).hexdigest() if lit_bytes else ""
        print(
            f"Built {out_bsp} ({len(bsp_bytes):,} B, sha256={bsp_sha}) "
            f"+ {out_lit.name} ({len(lit_bytes):,} B, sha256={lit_sha})"
        )
        return bsp_sha, lit_sha


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ericw", type=Path, default=None, help="Directory containing ericw-tools (qbsp, vis, light)")
    ap.add_argument("--out-dir", type=Path, default=REPO / "build" / "maps", help="Output directory for practice.bsp/.lit")
    ap.add_argument("--verify-repro", action="store_true", help="Compile twice and assert identical SHA-256")
    args = ap.parse_args(argv)

    ericw_dir = find_ericw_dir(args.ericw)
    bsp1, lit1 = compile_once(ericw_dir, args.out_dir)
    if args.verify_repro:
        with tempfile.TemporaryDirectory(prefix="practice_repro_") as tmp2:
            bsp2, lit2 = compile_once(ericw_dir, Path(tmp2))
        if bsp1 != bsp2 or lit1 != lit2:
            raise RuntimeError(f"NOT REPRODUCIBLE: bsp {bsp1} vs {bsp2}, lit {lit1} vs {lit2}")
        print("reproducible: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
