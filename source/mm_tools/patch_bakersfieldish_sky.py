#!/usr/bin/env python3
"""Idempotently give maps/bakersfieldish.bsp a sunny blue sky.

The map's worldspawn "fog" was a warm tan (0.56 0.49 0.41) at full opacity, and DarkPlaces/Zircon paints the sky with
the fog colour toward the horizon, so most of the visible sky came out brown. This swaps only the fog colour for a
clear blue (tested in game 2026-11-26) and keeps density, distances and height fade.

The new value has the same length as the old one, so the entity lump is rewritten in place: no other lump moves and
the .lit lightmap stays valid. Running it on an already patched map changes nothing.

Usage: python -I source/mm_tools/patch_bakersfieldish_sky.py [path/to/bakersfieldish.bsp]
"""
import os
import struct
import sys
from pathlib import Path

OLD_FOG = b'"fog" "0.22 0.56 0.49 0.41 1 4200 7600 2200 750"'
NEW_FOG = b'"fog" "0.22 0.26 0.36 0.52 1 4200 7600 2200 750"'
assert len(OLD_FOG) == len(NEW_FOG)

DEFAULT = Path(__file__).resolve().parents[2] / "maps" / "bakersfieldish.bsp"


def patch(path):
    data = bytearray(Path(path).read_bytes())
    if data[:4] not in (b"BSP2", b"2PSB", b"\x1d\x00\x00\x00"):
        raise SystemExit(f"{path}: not a Quake BSP")
    off, length = struct.unpack_from("<ii", data, 4)
    ents = bytes(data[off:off + length])
    world_end = ents.find(b"}")
    if NEW_FOG in ents[:world_end]:
        print(f"{path}: sky already patched")
        return False
    at = ents.find(OLD_FOG, 0, world_end)
    if at < 0:
        raise SystemExit(f"{path}: worldspawn fog is neither the old nor the new value; refusing to guess")
    data[off + at:off + at + len(NEW_FOG)] = NEW_FOG
    tmp = str(path) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    print(f"{path}: fog set to sunny blue")
    return True


if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
