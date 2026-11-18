"""Builds zz_bakovan.pk3: the stock ProMaster van with Rob's van front (van_front_bako.png) and no old chrome emblem.

python -I build_van_bako_pk3.py <path to bakersfield.pk3> [output pk3]

Reads the stock progs/veh_van_tex.png and progs/veh_van_tex_glow.png out of bakersfield.pk3, scales
van_front_bako.png into the front-fascia panel (x 1024-1521, y 43-497 of the 2048x2048 atlas), matches its white
paint to the atlas white (about 147, the atlas is dimmed for DarkPlaces), and moves the two headlight glow blobs
onto the new headlights. It also removes the old 3D chrome ring emblem (promaster_van_mesh.py, "Hollow Chrome Ring
Emblem") from progs/veh_van.md3 (surface "interior") and progs/veh_van_bumper.md3, because it sits in front of the
drawn Ram logo: its triangles are collapsed (all three corners on one vertex), so vertices and frames are unchanged.
Writes the PNGs and the two models into a small pk3 (default: zz_bakovan.pk3 next to bakersfield.pk3).
The zz_ name sorts after bakersfield.pk3, so DarkPlaces loads it later and its files win; delete it to undo.
"""
import io
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin

HERE = Path(__file__).resolve().parent
FRONT_ART = HERE / "van_front_bako.png"
X0, Y0, W, H = 1024, 43, 497, 454              # front panel in veh_van_tex.png
ATLAS_WHITE = 147.0                            # mean of the stock white paint
HEADLIGHTS_UV = ((160 / 1312, 300 / 1199), (1180 / 1312, 300 / 1199))  # headlight centres in van_front_bako.png
GLOW_BLOB = (1075, 150, 1115, 190)             # one stock headlight glow blob, reused for both lights
CHROME_UV = (1296, 1456, 1520, 1760)           # R_CHROME in promaster_van_tex.py (atlas pixels), the emblem's UVs
EMBLEM_MODELS = (("progs/veh_van.md3", "interior", 60), ("progs/veh_van_bumper.md3", "bumper_f", 60))
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
ZIP_EXTERNAL_ATTR = 0o644 << 16
ZIP_COMPRESS_LEVEL = 6
STORED_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}


def remove_emblem(data, surface, expect):
    """Collapses the emblem triangles of one MD3 surface: front-most 1.2 units, |y| < 3.6, chrome UVs."""
    b = bytearray(data)
    assert b[:4] == b"IDP3", "not an MD3"
    nsurf, = struct.unpack_from("<i", b, 84)
    o, = struct.unpack_from("<i", b, 100)
    for _ in range(nsurf):
        name = bytes(b[o + 4:o + 68]).split(b"\0")[0].decode()
        _, _, _, nv, ntri, ot, _, ost, oxyz, oend = struct.unpack_from("<10i", b, o + 68)
        if name == surface:
            xyz = np.frombuffer(b, "<i2", nv * 4, o + oxyz).reshape(-1, 4)[:, :3] / 64.0  # frame 0
            st = np.frombuffer(b, "<f4", nv * 2, o + ost).reshape(-1, 2) * 2048
            tri = np.frombuffer(b, "<i4", ntri * 3, o + ot).reshape(-1, 3).copy()
            u0, v0, u1, v1 = CHROME_UV
            hit = ((xyz[:, 0] > xyz[:, 0].max() - 1.2) & (abs(xyz[:, 1]) < 3.6)
                   & (st[:, 0] >= u0) & (st[:, 0] <= u1) & (st[:, 1] >= v0) & (st[:, 1] <= v1))
            sel = hit[tri].all(1)
            if sel.sum() != expect:
                sys.exit(f"{surface}: found {sel.sum()} emblem triangles, expected {expect}; model changed? not patching")
            tri[sel] = tri[sel][:, :1]
            b[o + ot:o + ot + ntri * 12] = tri.astype("<i4").tobytes()
            return bytes(b), int(sel.sum())
        o += oend
    sys.exit(f"surface {surface} not found")


def encode_png(im):
    """Serializes an RGB image as a deterministic PNG without metadata or timestamps."""
    clean = im.copy()
    clean.info.clear()
    buf = io.BytesIO()
    clean.save(buf, "PNG", compress_level=ZIP_COMPRESS_LEVEL, optimize=False, pnginfo=PngImagePlugin.PngInfo())
    return buf.getvalue()


def write_reproducible_pk3(out_pk3, entries):
    """Writes entries in sorted path order with fixed ZipInfo timestamps, mode, and per-entry compression."""
    with zipfile.ZipFile(out_pk3, "w") as z:
        for name in sorted(entries):
            data = entries[name]
            zi = zipfile.ZipInfo(name, date_time=ZIP_DATE_TIME)
            zi.create_system = 3
            zi.external_attr = ZIP_EXTERNAL_ATTR
            if Path(name).suffix.lower() in STORED_EXTS:
                z.writestr(zi, data, compress_type=zipfile.ZIP_STORED)
            else:
                z.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=ZIP_COMPRESS_LEVEL)
            print(f"wrote {name} -> {out_pk3}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src_pk3 = Path(sys.argv[1])
    out_pk3 = Path(sys.argv[2]) if len(sys.argv) > 2 else src_pk3.with_name("zz_bakovan.pk3")
    with zipfile.ZipFile(src_pk3) as z:
        tex = Image.open(io.BytesIO(z.read("progs/veh_van_tex.png"))).convert("RGB")
        glow = Image.open(io.BytesIO(z.read("progs/veh_van_tex_glow.png"))).convert("RGB")
        entries = {}
        for path, surface, expect in EMBLEM_MODELS:
            entries[path], n = remove_emblem(z.read(path), surface, expect)
            print(f"{path}: collapsed {n} emblem triangles in {surface}")

    front = np.asarray(Image.open(FRONT_ART).convert("RGB").resize((W, H), Image.LANCZOS)).astype(float)
    hood = front[int(H * 0.05):int(H * 0.15), int(W * 0.3):int(W * 0.7)].reshape(-1, 3).mean()
    front = np.clip(front * (ATLAS_WHITE / hood), 0, 255).astype(np.uint8)
    tex.paste(Image.fromarray(front), (X0, Y0))

    blob = glow.crop(GLOW_BLOB)
    glow.paste((0, 0, 0), (X0, Y0, X0 + W, Y0 + H))
    for u, v in HEADLIGHTS_UV:
        glow.paste(blob, (X0 + int(u * W) - blob.width // 2, Y0 + int(v * H) - blob.height // 2))

    entries["progs/veh_van_tex.png"] = encode_png(tex)
    entries["progs/veh_van_tex_glow.png"] = encode_png(glow)
    write_reproducible_pk3(out_pk3, entries)


if __name__ == "__main__":
    main()
