"""Idempotently updates Lump 0 of compiled bklan5.bsp (plus all 5 lighting_presets/*/bklan5.bsp) and bklan4.bsp
with the updated misc_lan_* and tabletop drink misc_model entities from out/maps/bklan5.map across:
  - Larry's Warehouse (118/120 E 21st St): SE LAN Party Bay & North TV LAN Pod
  - Unit 130A B-LAN 2001 Main Hall, Office Box & Back Room
  - ORCOM Connect LAN Party Banquet Hall, Check-In L-Counter & Dedicated Server Desk

Preserves 100% of world/brush models (*1..*N), baked .lit lightmaps, lighting presets, and custom vehicles/NPCs.
"""
import os
import re
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
MAP_SRC = os.path.join(HERE, "out", "maps", "bklan5.map")


def parse_map_point_ents(map_path: str):
    """Extract all misc_lan_* entity blocks and new tabletop drink misc_model blocks from bklan5.map."""
    txt = open(map_path, encoding="latin1").read()
    # Point entities at the end of .map have no nested brush '{' blocks
    lan_blocks = []
    drink_blocks = []
    for m in re.finditer(r"\{\n([^{}]+?)\}", txt):
        body = m.group(1)
        kv = dict(re.findall(r'"([^"]+)"\s+"([^"]*)"', body))
        cls = kv.get("classname", "")
        if cls.startswith("misc_lan_"):
            lan_blocks.append("{\n" + body.strip() + "\n}")
        elif cls == "misc_model" and kv.get("mdl", "") in (
            "progs/bklan/soda_can.md3",
            "progs/bklan/soda_bottle.md3",
            "progs/bklan/cup.md3",
        ):
            drink_blocks.append((kv.get("origin", ""), "{\n" + body.strip() + "\n}"))
    return lan_blocks, drink_blocks


def patch_bsp(bsp_path: str, lan_blocks: list, drink_blocks: list):
    raw = open(bsp_path, "rb").read()
    magic = raw[:4]
    assert magic == b"BSP2" or struct.unpack("<i", raw[:4])[0] == 29, f"Bad BSP header in {bsp_path}"
    lumps = [struct.unpack("<2i", raw[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    lump_blobs = [raw[o : o + n] for (o, n) in lumps]

    ent_txt = lump_blobs[0].rstrip(b"\x00").decode("latin1")
    kept = []
    existing_drink_origins = set()
    removed_lan = 0
    for m in re.finditer(r"\{([^}]*)\}", ent_txt):
        blk = m.group(0)
        kv = dict(re.findall(r'"([^"]+)"\s+"([^"]*)"', m.group(1)))
        cls = kv.get("classname", "")
        if cls.startswith("misc_lan_"):
            removed_lan += 1
            continue
        if cls == "misc_model" and kv.get("mdl", "") in (
            "progs/bklan/soda_can.md3",
            "progs/bklan/soda_bottle.md3",
            "progs/bklan/cup.md3",
        ):
            existing_drink_origins.add(kv.get("origin", ""))
        kept.append(blk)

    added_drinks = 0
    for orig, dblk in drink_blocks:
        if orig not in existing_drink_origins:
            kept.append(dblk)
            existing_drink_origins.add(orig)
            added_drinks += 1

    kept.extend(lan_blocks)
    new_ent_bytes = ("\n".join(kept) + "\n\x00").encode("latin1")
    lump_blobs[0] = new_ent_bytes

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

    with open(bsp_path, "wb") as fp:
        fp.write(out)
    print(f"Patched {os.path.relpath(bsp_path, MOD)}: {removed_lan} old misc_lan_* -> {len(lan_blocks)} misc_lan_* (+{added_drinks} new drinks)")


def main():
    lan_blocks, drink_blocks = parse_map_point_ents(MAP_SRC)
    targets = [
        os.path.join(MOD, "maps", "bklan5.bsp"),
        os.path.join(MOD, "maps", "bklan4.bsp"),
        os.path.join(HERE, "out", "maps", "bklan4.bsp"),
    ]
    preset_root = os.path.join(HERE, "out", "lighting_presets")
    if os.path.isdir(preset_root):
        for d in sorted(os.listdir(preset_root)):
            p = os.path.join(preset_root, d, "bklan5.bsp")
            if os.path.isfile(p):
                targets.append(p)
    for t in targets:
        if os.path.isfile(t):
            patch_bsp(t, lan_blocks, drink_blocks)


if __name__ == "__main__":
    main()
