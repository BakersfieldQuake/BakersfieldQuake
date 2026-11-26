#!/usr/bin/env python3
"""Give a lit BSP2 map the collision hulls of another compile of the same map, without relighting it.

Used 2026-11-26 to clear the streets of bakersfieldish: the 75 parked cars there were misc_model props with a clip
brush each. The .map was recompiled with qbsp only (no vis, no light) without those clip brushes, and this script
copied that compile's player and large hulls (hulls 1 and 2) into the shipped, lit map:

  - the donor's planes are appended to the lit map's planes, and its clipnodes replace the lit map's clipnodes
    (plane numbers shifted past the lit map's own planes);
  - every model's hull 1..3 head nodes come from the donor; hull 0 (drawing, bullets, rockets), faces, lighting,
    visibility and the .lit file are untouched, so the map looks exactly the same;
  - with --drop-mdl, misc_model entities using those models are removed from the entity lump.

The two compiles must come from the same .map apart from clip brushes: the script checks the model count and each
model's bounds. Only the hulls of the brushes that were removed change.

Usage:
  python -I graft_bsp_hulls.py LIT.bsp DONOR.bsp OUT.bsp [--drop-mdl progs/veh_sedan.md3 ...]
"""
import re
import struct
import sys

LUMP_ENTITIES, LUMP_PLANES, LUMP_CLIPNODES, LUMP_MODELS = 0, 1, 9, 14
N_LUMPS = 15
MODEL_SIZE = 64          # mins 3f, maxs 3f, origin 3f, headnode 4i, visleafs i, firstface i, numfaces i


def read_bsp(path):
    data = open(path, "rb").read()
    if data[:4] != b"BSP2":
        raise SystemExit(f"{path}: not a BSP2 map")
    lumps = []
    for i in range(N_LUMPS):
        off, ln = struct.unpack_from("<ii", data, 4 + 8 * i)
        lumps.append(bytearray(data[off:off + ln]))
    return lumps


def write_bsp(path, lumps):
    head = bytearray(b"BSP2" + b"\0" * (8 * N_LUMPS))
    body = bytearray()
    pos = len(head)
    for i, lump in enumerate(lumps):
        struct.pack_into("<ii", head, 4 + 8 * i, pos + len(body), len(lump))
        body += lump
        while len(body) % 4:
            body += b"\0"
    with open(path, "wb") as f:
        f.write(head + body)


def models(lump):
    return [struct.unpack_from("<9f4i3i", lump, i * MODEL_SIZE) for i in range(len(lump) // MODEL_SIZE)]


def drop_models(ents, mdls):
    text = bytes(ents).rstrip(b"\0").decode("latin1")
    kept, dropped = [], 0
    for block in re.findall(r"\{[^{}]*\}", text):
        kv = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', block))
        if kv.get("classname") == "misc_model" and kv.get("mdl") in mdls:
            dropped += 1
            continue
        kept.append(block)
    return bytearray(("\n".join(kept) + "\n").encode("latin1") + b"\0"), dropped


def main():
    args = sys.argv[1:]
    drop = []
    if "--drop-mdl" in args:
        k = args.index("--drop-mdl")
        drop, args = args[k + 1:], args[:k]
    lit_path, donor_path, out_path = args
    lit, donor = read_bsp(lit_path), read_bsp(donor_path)

    lm, dm = models(lit[LUMP_MODELS]), models(donor[LUMP_MODELS])
    if len(lm) != len(dm):
        raise SystemExit(f"model count differs: {len(lm)} vs {len(dm)}")
    for i, (a, b) in enumerate(zip(lm, dm)):
        if i and any(abs(a[j] - b[j]) > 1.01 for j in range(6)):
            raise SystemExit(f"model {i} bounds differ: {a[:6]} vs {b[:6]}")

    n_planes = len(lit[LUMP_PLANES]) // 20
    lit[LUMP_PLANES] += donor[LUMP_PLANES]
    clip = donor[LUMP_CLIPNODES]
    for i in range(len(clip) // 12):
        pn, = struct.unpack_from("<i", clip, i * 12)
        struct.pack_into("<i", clip, i * 12, pn + n_planes)
    lit[LUMP_CLIPNODES] = clip
    for i, b in enumerate(dm):
        struct.pack_into("<3i", lit[LUMP_MODELS], i * MODEL_SIZE + 40, b[10], b[11], b[12])

    if drop:
        lit[LUMP_ENTITIES], n = drop_models(lit[LUMP_ENTITIES], set(drop))
        print(f"dropped {n} misc_model entities")
    write_bsp(out_path, lit)
    print(f"{out_path}: {len(lm)} models, {n_planes} + {len(donor[LUMP_PLANES]) // 20} planes, "
          f"{len(clip) // 12} clipnodes")


if __name__ == "__main__":
    main()
