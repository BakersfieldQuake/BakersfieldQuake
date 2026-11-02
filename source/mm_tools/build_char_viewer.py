"""Builds one self-contained HTML page (no internet, no other files) that shows the suit guy, the stock Quake
Ranger, the robe guy and the wife animated in a small WebGL viewer.

python -E -P build_char_viewer.py [out.html]      (default: G:\\Quake\\Combat\\Bakersfield Player Models.html)

Reads progs/suitguy.mdl, robeguy.mdl and wifeguy.mdl (all 143 vertex-animated frames, straight from the files the game
uses) and the original progs/player.mdl from id1/pak0.pak, and rebuilds the full-colour skins from the photos at
full brightness (the in-game skins are darkened for Darkplaces' overbright lighting).  char_viewer.template.html is the page; __MODELS_JSON__ is replaced by the data.
"""
import base64
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_char_models as B

OUT = sys.argv[1] if len(sys.argv) > 1 else r"G:\Quake\Combat\Bakersfield Player Models.html"
TEMPLATE = os.path.join(HERE, "char_viewer.template.html")
TEX_MUL = 2                       # page texture = this many times the 8-bit skin size


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def raw_mdl(d):
    """parse an IDPO v6 model (bytes).  Vertices on the skin seam that belong to back-facing triangles get their own
    copy with s + skinwidth/2 (Quake's onseam rule), so the page needs no special case."""
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale, trans = h[2:5], h[5:8]
    nsk, sw, sh, nv, nt, nf = h[12:18]
    o = 84
    skin = None
    for _ in range(nsk):
        assert struct.unpack_from("<i", d, o)[0] == 0
        if skin is None:
            skin = np.frombuffer(d, np.uint8, sw * sh, o + 4).reshape(sh, sw)
        o += 4 + sw * sh
    st = np.frombuffer(d, "<i4", nv * 3, o).reshape(nv, 3)
    o += nv * 12
    tri = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16
    names, pos, nrm = [], [], []
    for _ in range(nf):
        assert struct.unpack_from("<i", d, o)[0] == 0
        o += 4 + 8
        names.append(d[o:o + 16].split(b"\0")[0].decode())
        o += 16
        v = np.frombuffer(d, np.uint8, nv * 4, o).reshape(nv, 4)
        o += nv * 4
        pos.append(v[:, :3])
        nrm.append(v[:, 3])
    assert o == len(d)
    key, src, uv, tris = {}, [], [], []
    for front, *vs in tri:
        t = []
        for v in vs:
            back = int(st[v, 0] != 0 and not front)
            if (v, back) not in key:
                key[(v, back)] = len(src)
                src.append(v)
                uv.append((st[v, 1] + back * sw // 2, st[v, 2]))
            t.append(key[(v, back)])
        tris.append(t)
    pos = np.array(pos, np.uint8)[:, src]
    nrm = np.array(nrm, np.uint8)[:, src]
    return dict(scale=scale, trans=trans, sw=sw, sh=sh, nv=len(src), nt=nt, st=np.array(uv), tri=np.array(tris),
                names=names, pos=pos, nrm=nrm, skin=skin)


def pack(r, mid, label, detail, tex_url, **extra):
    return dict(id=mid, label=label, detail=detail, nv=r["nv"], nt=r["nt"], sw=r["sw"], sh=r["sh"],
                scale=list(r["scale"]), trans=list(r["trans"]), names=r["names"],
                tris=b64(r["tri"].astype("<u2")), st=b64(r["st"].astype("<u2")),
                pos=b64(r["pos"]), nrm=b64(r["nrm"]), tex=tex_url, **extra)


def main():
    B.SKIN_GAIN = 1.0
    built = {}
    for ch, label in ((B.SUIT, "Suit guy"), (B.ROBE, "Robe guy"), (B.WIFE, "Wife")):
        with open(os.path.join(B.PROGS, ch["name"] + ".mdl"), "rb") as f:
            r = raw_mdl(f.read())
        m = B.build(ch)
        _, big, _, _, SW = B.make_skin(m, ch)
        assert SW == r["sw"], (SW, r["sw"])
        img = Image.fromarray(big).resize((r["sw"] * TEX_MUL, r["sh"] * TEX_MUL), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88, subsampling=0, optimize=True)
        built[ch["name"]] = pack(r, ch["name"], label, "{:,} tris".format(r["nt"]),
                                 "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii"))
        print("%s: %d verts, %d tris, %d frames, texture %dx%d (%d KB)" % (
            label, r["nv"], r["nt"], len(r["names"]), img.width, img.height, len(buf.getvalue()) // 1024))

    # the stock Ranger, straight out of id's pak0 (not the mod's copy)
    r = raw_mdl(B.read_pak_file(B.PAK, "progs/player.mdl"))
    rgb = B.PALETTE[r["skin"]].astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, "PNG", optimize=True)
    built["ranger"] = pack(r, "ranger", "Ranger", "stock · {:,} tris".format(r["nt"]),
                           "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
                           nearest=True, gain=1.7)
    print("Ranger: %d verts (seam-expanded), %d tris, %d frames, skin %dx%d" % (
        r["nv"], r["nt"], len(r["names"]), r["sw"], r["sh"]))

    models = [built["suitguy"], built["ranger"], built["robeguy"], built["wifeguy"]]   # the Ranger is second
    assert all(m["names"] == models[0]["names"] for m in models), "frame order differs"
    data = dict(anorm=[round(float(x), 4) for x in B.ANORM.reshape(-1)], models=models)
    page = open(TEMPLATE, encoding="utf-8").read()
    assert page.count("__MODELS_JSON__") == 1
    page = page.replace("__MODELS_JSON__", json.dumps(data, separators=(",", ":")))
    open(OUT, "w", encoding="utf-8").write(page)
    print("wrote", OUT, "%.2f MB" % (os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
