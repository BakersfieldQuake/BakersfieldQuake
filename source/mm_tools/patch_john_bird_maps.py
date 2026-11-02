"""Idempotently patch perched 'misc_vehicle_johnbird' vehicle spawns into Lump 0
of maps/bklan5.bsp and maps/fox.bsp without disturbing prebaked .lit lightmaps.
"""
import os
import re
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def add_jbirds_to_bsp(rel_path, placements):
    path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(path):
        return
    raw = open(path, "rb").read()
    magic = raw[:4]
    assert magic in (b"\x1d\x00\x00\x00", b"BSP2"), f"Unexpected BSP magic {magic} in {path}"
    ofs, ln = struct.unpack_from("<2i", raw, 4)
    ent_txt = raw[ofs : ofs + ln].decode("latin1")
    blocks = [b for b in re.findall(r"\{[^}]*\}", ent_txt) if "misc_vehicle_johnbird" not in b]
    for ox, oy, oz, ang in placements:
        blocks.append(
            '{\n"classname" "misc_vehicle_johnbird"\n'
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
    print(f"Patched {rel_path}: {len(placements)}x misc_vehicle_johnbird (size={len(out)/1e6:.2f} MB)")


if __name__ == "__main__":
    add_jbirds_to_bsp(
        "maps/bklan5.bsp",
        [
            (1210, -11412, 12, 312),   # Fox Theater 20th & H Plaza
            (360, -18490, 1242, 90),   # Padre Hotel 8th-Floor Skyline Rooftop
            (-120, -1180, 12, 90),     # Larry's Warehouse / LAN Courtyard
        ],
    )
    add_jbirds_to_bsp(
        "maps/fox.bsp",
        [
            (-2220, 912, 12, 312),     # Fox Theater Plaza
            (-1480, -340, 1242, 90),   # Padre Hotel Rooftop
        ],
    )
