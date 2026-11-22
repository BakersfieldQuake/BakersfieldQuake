#!/usr/bin/env python3
"""Idempotently add the 1996 Quake 1 LAN Party Battlestations to Dagny's upstairs
office (James Building Floor 2 — Mesh Cowork) in maps/bakersfielddowntown.bsp Lump 0.

Preserves 100% of world/brush models, baked lightmaps (.lit), PVS, and all other
entities. Uses only the Python standard library and writes atomically so it is safe
for local patching, CI (`build-zip.yml`), and in-place VPS updates.

Note on `misc_lan_quakedesk` (`source/qc_combat_decomp/lan_props.qc`):
  Passing `"pos2" "0 0 0"` / `"0 0 1"` / `"0 0 2"` selects `qdesk_b.md3_0.skin`
  (E2M1 SSG), `_1.skin` (Start Hall SG), and `_2.skin` (DM3 RL) cleanly on one MD3,
  and `"classname" "misc_lan_quakedesk"` wires `SOLID_BBOX` + `DAMAGE_AIM` + sparks +
  flying CRT/PC/keyboard/oak debris + domino explosions + 45s DM respawn.

Usage:
  python -I source/mm_tools/patch_dagnys_lan_bsp.py [path/to/bakersfielddowntown.bsp] [--check-idempotent]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent
DEFAULT_BSP = MOD / "maps" / "bakersfielddowntown.bsp"

QDESK_CLASSNAME = "misc_lan_quakedesk"
QDESK_MDL = "progs/qdesk_b.md3"
QDESK_PREFIX = "progs/qdesk_"
FLOOR_Z = "174.2"  # +0.2 QU above Z=174 floor plane so DarkPlaces lightpoint samples cleanly above floor

# (label, x, y, yaw_deg, skin_id)
# Local +X = Ranger look direction & rear of desk/monitor; -X = chair back & glowing CRT screen face.
LAN_DESKS: list[tuple[str, int, int, int, int]] = [
    # --- Main Loft: 5-rig South 20th St Ribbon-Window Row (yaw=270, CRTs glow North into loft) ---
    ("S-1", -5730, 2440, 270, 0),
    ("S-2", -5630, 2440, 270, 1),
    ("S-3", -5530, 2440, 270, 2),
    ("S-4", -5430, 2440, 270, 0),
    ("S-5", -5330, 2440, 270, 1),
    # --- Main Loft: 1-rig Hero SE Curved-Corner Battlestation (yaw=315, CRT glows NW into loft) ---
    ("SE-1", -5165, 2505, 315, 2),
    # --- Main Loft: 4-rig East Eye St Ribbon-Window Row (yaw=0, CRTs glow West, clear of NE stairs) ---
    ("E-1", -5076, 2640, 0, 0),
    ("E-2", -5076, 2735, 0, 1),
    ("E-3", -5076, 2830, 0, 2),
    ("E-4", -5076, 2925, 0, 0),
    # --- Main Loft: 4-rig Center-East Back-to-Back LAN Island (cables inward, CRTs outward; >=47u aisles) ---
    ("CE-S1", -5330, 2771, 90, 0),
    ("CE-S2", -5262, 2771, 90, 1),
    ("CE-N1", -5330, 2842, 270, 2),
    ("CE-N2", -5262, 2842, 270, 0),
    # --- Main Loft: 2-rig Center-West Back-to-Back Mini Island ---
    ("CW-S1", -5690, 2755, 90, 1),
    ("CW-N1", -5690, 2826, 270, 2),
    # --- Room 13: 2-rig VIP Admin LAN Pair (clear of walnut desk, swung '13' door & item_health) ---
    ("R13-W", -6140, 2835, 180, 1),
    ("R13-E", -5955, 2845, 0, 2),
]


def build_lan_entities() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for _label, x, y, yaw, skin in LAN_DESKS:
        ent: dict[str, str] = {
            "classname": QDESK_CLASSNAME,
            "origin": f"{x} {y} {FLOOR_Z}",
            "angles": f"0 {yaw} 0",
            "mdl": QDESK_MDL,
        }
        if skin > 0:
            ent["pos2"] = f"0 0 {skin}"
        out.append(ent)
    return out


def _fmt_ent(kv: dict[str, str]) -> str:
    return "{\n" + "".join(f'"{k}" "{v}"\n' for k, v in kv.items()) + "}"


def patch_bsp(bsp_path: Path) -> tuple[str, int, int]:
    raw = bsp_path.read_bytes()
    magic = raw[:4]
    if magic != b"BSP2" and struct.unpack("<i", magic)[0] != 29:
        raise ValueError(f"Unexpected BSP header in {bsp_path}: {magic!r}")

    lumps = [struct.unpack("<2i", raw[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    lump_blobs = [raw[o : o + n] for (o, n) in lumps]

    ent_txt = lump_blobs[0].rstrip(b"\x00").decode("latin1")
    pat = re.compile(r'"([^"]+)"\s+"([^"]*)"')
    kept: list[str] = []
    removed = 0
    for m in re.finditer(r"\{([^}]*)\}", ent_txt):
        kv = dict(pat.findall(m.group(1)))
        if kv.get("classname") in ("misc_model", QDESK_CLASSNAME) and kv.get("mdl", "").startswith(QDESK_PREFIX):
            removed += 1
            continue
        kept.append(m.group(0))

    new_ents = build_lan_entities()
    for ent in new_ents:
        kept.append(_fmt_ent(ent))

    lump_blobs[0] = ("\n".join(kept) + "\n\x00").encode("latin1")

    order = sorted(range(15), key=lambda i: lumps[i][0])
    out = bytearray(4 + 15 * 8)
    out[:4] = magic
    new_dir = [(0, 0)] * 15
    for idx in order:
        while len(out) & 3:
            out.append(0)
        ofs = len(out)
        blob = lump_blobs[idx]
        out.extend(blob)
        new_dir[idx] = (ofs, len(blob))
    for i, (ofs, length) in enumerate(new_dir):
        struct.pack_into("<2i", out, 4 + 8 * i, ofs, length)

    out_bytes = bytes(out)
    tmp_path = bsp_path.with_suffix(bsp_path.suffix + ".tmp")
    tmp_path.write_bytes(out_bytes)
    os.replace(tmp_path, bsp_path)

    sha = hashlib.sha256(out_bytes).hexdigest()
    print(
        f"Patched {bsp_path}: removed {removed} old qdesk ents, "
        f"added {len(new_ents)} LAN desk ents ({len(out_bytes):,} B, sha256={sha})"
    )
    return sha, removed, len(new_ents)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Patch Dagny's upstairs LAN party desks into bakersfielddowntown.bsp")
    ap.add_argument("bsp_path", nargs="?", type=Path, default=DEFAULT_BSP, help="Target BSP path")
    ap.add_argument(
        "--check-idempotent",
        action="store_true",
        help="Run patch a second time and assert identical SHA-256.",
    )
    args = ap.parse_args(argv)

    bsp_path = args.bsp_path.resolve()
    if not bsp_path.is_file():
        raise FileNotFoundError(f"BSP not found: {bsp_path}")

    sha1, _, _ = patch_bsp(bsp_path)
    if args.check_idempotent:
        sha2, rem2, add2 = patch_bsp(bsp_path)
        if sha1 != sha2 or rem2 != add2:
            raise RuntimeError(f"Idempotency check FAILED: sha1={sha1} != sha2={sha2}, rem2={rem2}, add2={add2}")
        print(f"Idempotency PASSED: byte-identical sha256={sha2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
