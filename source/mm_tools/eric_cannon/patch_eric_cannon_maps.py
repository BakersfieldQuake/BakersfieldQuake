"""Idempotently patch `misc_eric_cannon` spawns into Lump 0 of `maps/downtownsmall.bsp`
and `maps/downtown.bsp` (Fox Theater Plaza & Padre Hotel Street) without touching `.lit` files.
"""
import os
import re
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def patch_eric_cannons_into_bsp(rel_path, placements):
    path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(path):
        print(f"SKIP (not found): {rel_path}")
        return
    raw = open(path, "rb").read()
    magic = raw[:4]
    assert magic in (b"\x1d\x00\x00\x00", b"BSP2"), f"Unexpected BSP magic {magic} in {path}"
    ofs, ln = struct.unpack_from("<2i", raw, 4)
    ent_txt = raw[ofs : ofs + ln].decode("latin1")
    blocks = [b for b in re.findall(r"\{[^}]*\}", ent_txt) if "misc_eric_cannon" not in b]
    for ox, oy, oz, ang in placements:
        blocks.append(
            '{\n"classname" "misc_eric_cannon"\n'
            f'"origin" "{ox} {oy} {oz}"\n'
            f'"angle" "{ang}"\n}}'
        )
    new_ent = ("\n".join(blocks) + "\n\x00").encode("latin1")
    if ofs + ln + 4 >= len(raw):
        base = raw[:ofs]
    else:
        base = raw
    pad = (4 - (len(base) % 4)) % 4
    new_ofs = len(base) + pad
    out = bytearray(base + (b"\x00" * pad) + new_ent)
    struct.pack_into("<2i", out, 4, new_ofs, len(new_ent))
    with open(path, "wb") as f:
        f.write(out)
    print(f"[BSP OK] {rel_path}: {len(placements)}x misc_eric_cannon patched (size={len(out)/1e6:.2f} MB)")


if __name__ == "__main__":
    # Verified obstacle-free, full-sky-clearance coordinates via `find_downtown_spots.py`:
    #   1) Fox Theater Marquee Plaza: (-9230, 2480, 6), angle 270 (facing South down H St toward Padre Hotel)
    #   2) Padre Hotel H St Entrance: (-8860, -5640, 0), angle 90 (facing North up H St toward Fox Theater)
    downtown_placements = [
        (-9230, 2480, 6, 270),
        (-8860, -5640, 0, 90),
    ]
    patch_eric_cannons_into_bsp("maps/bakersfielddowntown.bsp", downtown_placements)
    patch_eric_cannons_into_bsp("maps/downtownsmall.bsp", downtown_placements)
    patch_eric_cannons_into_bsp("maps/downtown.bsp", downtown_placements)
