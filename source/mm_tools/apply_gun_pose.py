"""Bakes the placements from the gun placement vote page (gun_pose_votes.json) into the first-person models.

python -I apply_gun_pose.py <gun_pose_votes.json> [--dry-run]

Only guns whose vote is not "fine as it is"/"undecided" AND that were adjusted (vote "my placement") are touched.
The pose is {pos [fwd,left,up], rot [roll,pitch,yaw], scale}, turned/scaled about the centre of the frame-0 bounding box,
exactly the maths of apply_viewmodel_edits.py, and is measured against the model as it was before this script ran, which is
kept as progs/<name>.pre_gunpose (made once) - so applying again gives the same result.  Written: source/gun_pose_vote/applied.json.
Guns whose start pose has a stock slot tilt (goo gun, SSG, milky) are skipped here: their tilt cvars would need zeroing too.
md3 models are rewritten through md3lib; Quake .mdl models are decoded, transformed and re-quantised (a pure move only
changes the header origin).  Then run build_gun_pose_vote.py to refresh the page."""
import json
import os
import shutil
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib
from apply_viewmodel_edits import bake, make_xform

COMBAT = "G:/Quake/Combat/"
MOD = COMBAT + "BakersfieldQuake/"
PROGS = MOD + "progs/"
APPLIED = MOD + "source/gun_pose_vote/applied.json"
ANORM = json.load(open(COMBAT + "monster_page/anorm.json"))
ANORM = [ANORM[i:i + 3] for i in range(0, 162 * 3, 3)]


def stock_bytes(rel):
    """a stock game file (quake15 pk3, then id1 paks) for models the mod does not carry."""
    try:
        return zipfile.ZipFile(COMBAT + "quake15/q15.pk3").read(rel)
    except KeyError:
        pass
    for pak in ("pak1", "pak0"):
        f = open(COMBAT + "id1/%s.pak" % pak, "rb")
        _, ofs, ln = struct.unpack("<4sii", f.read(12))
        f.seek(ofs)
        raw = f.read(ln)
        for i in range(0, ln, 64):
            if raw[i:i + 56].split(b"\0")[0].decode("latin1").lower() == rel:
                pos, sz = struct.unpack("<ii", raw[i + 56:i + 64])
                f.seek(pos)
                return f.read(sz)
    raise SystemExit("no such stock file " + rel)


def nearest_normal(n):
    best, bi = -9, 0
    for i, a in enumerate(ANORM):
        d = a[0] * n[0] + a[1] * n[1] + a[2] * n[2]
        if d > best:
            best, bi = d, i
    return bi


def parse_mdl(raw):
    nskin, sw, sh, nv, nt, nf = struct.unpack("<6i", raw[48:72])
    sc = struct.unpack("<3f", raw[8:20])
    org = struct.unpack("<3f", raw[20:32])
    o = 84
    for _ in range(nskin):
        g = struct.unpack("<i", raw[o:o + 4])[0]
        o += 4
        if g == 0:
            o += sw * sh
        else:
            n = struct.unpack("<i", raw[o:o + 4])[0]
            o += 4 + 4 * n + n * sw * sh
    head_end = o + nv * 12 + nt * 16          # skins, texcoords, triangles are copied as they are
    o = head_end
    frames = []
    for _ in range(nf):
        t = struct.unpack("<i", raw[o:o + 4])[0]
        if t != 0:
            raise SystemExit("group frames are not supported")
        name = raw[o + 12:o + 28]
        verts = []
        for i in range(nv):
            b = o + 28 + i * 4
            x, y, z, n = raw[b:b + 4]
            verts.append(((x * sc[0] + org[0], y * sc[1] + org[1], z * sc[2] + org[2]), ANORM[n % 162], n))
        frames.append((name, verts))
        o += 28 + nv * 4
    return dict(head=bytearray(raw[:head_end]), frames=frames, nv=nv)


def write_mdl(m, point, rotate):
    new = [(name, [(point(p), rotate(n)) for p, n, _ in verts]) for name, verts in m["frames"]]
    allp = [p for _, vs in new for p, _ in vs]
    lo = [min(p[k] for p in allp) for k in range(3)]
    hi = [max(p[k] for p in allp) for k in range(3)]
    sc = [max((hi[k] - lo[k]) / 255.0, 1e-6) for k in range(3)]
    head = m["head"]
    head[8:20] = struct.pack("<3f", *sc)
    head[20:32] = struct.pack("<3f", *lo)
    head[32:36] = struct.pack("<f", max((p[0] ** 2 + p[1] ** 2 + p[2] ** 2) ** 0.5 for p in allp))
    out = bytearray(head)
    for name, vs in new:
        q = [tuple(max(0, min(255, round((p[k] - lo[k]) / sc[k]))) for k in range(3)) + (nearest_normal(n),) for p, n in vs]
        bmin = bytes([min(v[k] for v in q) for k in range(3)] + [0])
        bmax = bytes([max(v[k] for v in q) for k in range(3)] + [0])
        out += struct.pack("<i", 0) + bmin + bmax + name + b"".join(bytes(v) for v in q)
    return bytes(out)


def apply_mdl(base_raw, out_path, e):
    m = parse_mdl(base_raw)
    pts = [p for p, _, _ in m["frames"][0][1]]
    pivot = tuple((min(p[k] for p in pts) + max(p[k] for p in pts)) / 2 for k in range(3))
    point, rotate = make_xform(pivot, e["pos"], e["rot"], e["scale"])
    only_move = all(abs(a) < 1e-9 for a in e["rot"]) and abs(e["scale"] - 1) < 1e-9
    if only_move:
        out = bytearray(base_raw)
        org = struct.unpack("<3f", base_raw[20:32])
        out[20:32] = struct.pack("<3f", *(org[k] + e["pos"][k] for k in range(3)))
        out[32:36] = struct.pack("<f", struct.unpack("<f", base_raw[32:36])[0] + sum(abs(v) for v in e["pos"]))
        open(out_path, "wb").write(bytes(out))
        return
    open(out_path, "wb").write(write_mdl(m, point, rotate))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        sys.exit(__doc__)
    votes = json.load(open(args[0], encoding="utf-8"))["guns"]
    done = json.load(open(APPLIED)) if os.path.exists(APPLIED) else {}
    for gid, g in votes.items():
        if g["vote"] != "my placement" or not g["adjusted"]:
            continue
        if g["start"]["rot"] != [0, 0, 0]:
            print("skip", gid, "(stock tilt in its start pose)")
            continue
        e = dict(pos=g["pose"]["pos"], rot=g["pose"]["rot"], scale=g["pose"]["scale"])
        rel = g["model"]
        path = MOD + rel
        base = path + ".pre_gunpose"
        print(gid, rel, e, "(dry run)" if dry else "")
        if dry:
            continue
        if not os.path.exists(base):
            if os.path.exists(path):
                shutil.copy2(path, base)
            else:
                open(base, "wb").write(stock_bytes(rel))
        if rel.endswith(".md3"):
            bake(base, path, e)
        else:
            apply_mdl(open(base, "rb").read(), path, e)
        done[gid] = dict(model=rel, **e)
    if not dry:
        json.dump(done, open(APPLIED, "w"), indent=1)
        print("wrote", APPLIED, "- now run build_gun_pose_vote.py to refresh the page")


if __name__ == "__main__":
    main()
