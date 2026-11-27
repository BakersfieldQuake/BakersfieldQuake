#!/usr/bin/env python3
"""Strip `item_powerup_foreloco` powerups from Bakersfield maps cleanly.

Strips any prior `item_powerup_foreloco` entities while preserving all brush
geometry, lightmaps (.lit), and other entities.

Usage:
  python -I source/mm_tools/foreloco/patch_foreloco_maps.py [path/to/bakersfielddowntown.bsp]
"""
from __future__ import annotations

import argparse
import os
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent.parent
DEFAULT_BSP = MOD / "maps" / "bakersfielddowntown.bsp"

CLASSNAME = "item_powerup_foreloco"


def patch_bsp(bsp_path: Path) -> bool:
    raw = bsp_path.read_bytes()
    magic = raw[:4]
    if magic not in (b"BSP2", b"2PSB") and struct.unpack("<i", magic)[0] != 29:
        raise ValueError(f"Unexpected BSP header in {bsp_path}: {magic!r}")

    lumps = [struct.unpack("<2i", raw[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    lump_blobs = [raw[o : o + n] for (o, n) in lumps]

    ent_raw = lump_blobs[0].rstrip(b"\x00").decode("latin1")

    # Remove any existing item_powerup_foreloco blocks
    blocks = re.findall(r"\{[^}]*\}", ent_raw)
    kept = [
        b for b in blocks
        if f'"classname" "{CLASSNAME}"' not in b and f'"classname"\t"{CLASSNAME}"' not in b
    ]
    removed = len(blocks) - len(kept)

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
    for idx, (ofs, n) in enumerate(new_dir):
        struct.pack_into("<2i", out, 4 + 8 * idx, ofs, n)

    tmp = bsp_path.with_suffix(".bsp.tmp")
    tmp.write_bytes(bytes(out))
    os.replace(tmp, bsp_path)
    print(f"Stripped {bsp_path.name}: removed {removed} {CLASSNAME} spawns")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bsp", nargs="?", default=str(DEFAULT_BSP))
    args = ap.parse_args()

    p = Path(args.bsp)
    if p.is_file():
        patch_bsp(p)
    fox = MOD / "maps" / "fox.bsp"
    if fox.is_file() and fox.resolve() != p.resolve():
        patch_bsp(fox)


if __name__ == "__main__":
    main()
