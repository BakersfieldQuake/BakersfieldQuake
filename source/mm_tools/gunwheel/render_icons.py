"""Make the 18 Gun Wheel icons from each gun's own art. Run once by hand when a gun's look changes:

    python3 -I source/mm_tools/gunwheel/render_icons.py <installed game folder> [names...]

Needs numpy and Pillow. Reads the models and textures from the installed game's pk3s (and the palette from
id1/pak0.pak for the .mdl skins) and writes assets/<name>.png, which are committed; CI only zips them
(build_gunwheel_pk3.py). The lightning icon is drawn here from scratch, not rendered from id's model.
"""
import glob
import io
import math
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
SIZE = 192
MARGIN = 8
HANDS = ("hand", "glove", "finger", "sleeve", "arm")

PACKS = {}
PALETTE = None


def open_game(root):
    global PALETTE
    paths = [os.path.join(root, "quake15", "q15.pk3"), os.path.join(root, "BakersfieldQuake", "bakersfield.pk3")]
    paths += sorted(glob.glob(os.path.join(root, "BakersfieldQuake", "zz_*.pk3")))
    import zipfile
    for p in paths:
        z = zipfile.ZipFile(p)
        for n in z.namelist():
            PACKS[n.lower()] = (z, n)
    with open(os.path.join(root, "id1", "pak0.pak"), "rb") as f:
        _, ofs, length = struct.unpack("<4sii", f.read(12))
        f.seek(ofs)
        table = f.read(length)
        for i in range(0, length, 64):
            name, pos, size = struct.unpack("<56sii", table[i:i + 64])
            if name.split(b"\0")[0] == b"gfx/palette.lmp":
                f.seek(pos)
                PALETTE = np.frombuffer(f.read(size), np.uint8).reshape(256, 3)


def read(name):
    z, real = PACKS[name.lower()]
    return z.read(real)


def image(name):
    return Image.open(io.BytesIO(read(name))).convert("RGBA")


def texture(shader):
    for ext in ("", ".png", ".tga", ".jpg"):
        if (shader + ext).lower() in PACKS:
            return np.asarray(image(shader + ext), np.float32) / 255.0
    return np.array([[[0.6, 0.6, 0.65, 1.0]]], np.float32)


# ---------------------------------------------------------------- model readers
def load_md3(name, frame):
    d = read(name)
    nsurf = struct.unpack_from("<i", d, 84)[0]
    ofs = struct.unpack_from("<i", d, 100)[0]
    out = []
    for _ in range(nsurf):
        sname = d[ofs + 4:ofs + 68].split(b"\0")[0].decode()
        _, nframes, _, nv, nt, otri, osh, ost, overt, oend = struct.unpack_from("<10i", d, ofs + 68)
        shader = d[ofs + osh:ofs + osh + 64].split(b"\0")[0].decode()
        tris = np.frombuffer(d, "<i4", nt * 3, ofs + otri).reshape(nt, 3)
        st = np.frombuffer(d, "<f4", nv * 2, ofs + ost).reshape(nv, 2)
        f = min(frame, nframes - 1)
        raw = np.frombuffer(d, "<i2", nv * 4, ofs + overt + f * nv * 8).reshape(nv, 4)
        verts = raw[:, :3] / 64.0
        out.append((sname, verts[tris], st[tris], texture(shader)))
        ofs += oend
    return out


def load_mdl(name, frame):
    d = read(name)
    scale = np.array(struct.unpack_from("<3f", d, 8))
    origin = np.array(struct.unpack_from("<3f", d, 20))
    nskins, sw, sh, nv, nt, nframes = struct.unpack_from("<6i", d, 48)
    o = 84
    skin = None
    for _ in range(nskins):
        group = struct.unpack_from("<i", d, o)[0]
        o += 4
        count = 1
        if group:
            count = struct.unpack_from("<i", d, o)[0]
            o += 4 + 4 * count
        if skin is None:
            idx = np.frombuffer(d, np.uint8, sw * sh, o).reshape(sh, sw)
            rgb = PALETTE[idx]
            skin = np.dstack([rgb, np.full((sh, sw), 255, np.uint8)]).astype(np.float32) / 255.0
        o += sw * sh * count
    stv = np.frombuffer(d, "<i4", nv * 3, o).reshape(nv, 3)
    o += nv * 12
    tris = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16
    pose = None
    for i in range(nframes):
        group = struct.unpack_from("<i", d, o)[0]
        o += 4
        count = 1
        if group:
            count = struct.unpack_from("<i", d, o)[0]
            o += 4 + 8 + 4 * count
        for _ in range(count):
            o += 24
            if pose is None or i == frame:
                pose = np.frombuffer(d, np.uint8, nv * 4, o).reshape(nv, 4)
            o += nv * 4
        if i >= frame:
            break
    verts = pose[:, :3] * scale + origin
    corners = verts[tris[:, 1:]]
    st = stv[tris[:, 1:]][..., 1:3].astype(np.float64)
    onseam = stv[tris[:, 1:]][..., 0] != 0
    back = (tris[:, 0] == 0)[:, None]
    st[..., 0] += np.where(onseam & back, sw / 2.0, 0.0)
    st = (st + 0.5) / np.array([sw, sh])
    return [("body", corners, st, skin)]


# ---------------------------------------------------------------- rasteriser
def render(surfaces, az=-72, el=14, skip=(), res=768):
    azr, elr = math.radians(az), math.radians(el)
    cam = np.array([math.cos(elr) * math.cos(azr), math.cos(elr) * math.sin(azr), math.sin(elr)])
    fwd = -cam
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    light = cam + right * -0.5 + up * 0.9
    light /= np.linalg.norm(light)

    keep = [s for s in surfaces if not any(k in s[0].lower() for k in skip)]
    every = np.concatenate([s[1].reshape(-1, 3) for s in keep])
    px, py = every @ right, every @ up
    cx, cy = (px.min() + px.max()) / 2, (py.min() + py.max()) / 2
    scale = (res - 8) / max(px.max() - px.min(), py.max() - py.min())
    color = np.zeros((res, res, 4), np.float32)
    zbuf = np.full((res, res), -1e18)
    for _, tri, st, tex in keep:
        th, tw = tex.shape[:2]
        xs = (tri @ right - cx) * scale + res / 2
        ys = res / 2 - (tri @ up - cy) * scale
        zs = tri @ cam
        for t in range(len(tri)):
            x, y, z = xs[t], ys[t], zs[t]
            x0, x1 = max(int(x.min()), 0), min(int(math.ceil(x.max())), res - 1)
            y0, y1 = max(int(y.min()), 0), min(int(math.ceil(y.max())), res - 1)
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if x1 < x0 or y1 < y0 or abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            w2 = 1 - w0 - w1
            depth = w0 * z[0] + w1 * z[1] + w2 * z[2]
            window = zbuf[y0:y1 + 1, x0:x1 + 1]
            mask = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4) & (depth > window)
            if not mask.any():
                continue
            u = w0 * st[t, 0, 0] + w1 * st[t, 1, 0] + w2 * st[t, 2, 0]
            v = w0 * st[t, 0, 1] + w1 * st[t, 1, 1] + w2 * st[t, 2, 1]
            tx = (np.mod(u, 1.0) * tw).astype(int).clip(0, tw - 1)
            ty = (np.mod(v, 1.0) * th).astype(int).clip(0, th - 1)
            sample = tex[ty, tx]
            mask &= sample[..., 3] > 0.35
            normal = np.cross(tri[t, 1] - tri[t, 0], tri[t, 2] - tri[t, 0])
            normal /= max(np.linalg.norm(normal), 1e-9)
            if normal @ cam < 0:
                normal = -normal
            shade = 0.62 + 0.75 * max(float(normal @ light), 0.0)
            window[mask] = depth[mask]
            target = color[y0:y1 + 1, x0:x1 + 1]
            target[mask, :3] = np.clip(sample[mask][:, :3] * shade, 0, 1)
            target[mask, 3] = 1.0
    return Image.fromarray((color * 255 + 0.5).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- finishing
def finish(img, gamma=1.0, turn=0):
    """Crop to the drawing, fit it in the square and give it the same light outline as every other icon."""
    if turn:      # long thin guns fill the square better on a slant
        img = img.rotate(turn, resample=Image.BICUBIC, expand=True)
    box = img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    img = img.crop(box)
    room = SIZE - 2 * MARGIN
    scale = room / max(img.width, img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")
    if gamma != 1.0:
        lut = [round(255 * (i / 255) ** (1 / gamma)) for i in range(256)]
        r, g, b, a = img.split()
        img = Image.merge("RGBA", (r.point(lut), g.point(lut), b.point(lut), a))
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - size[0]) // 2, (SIZE - size[1]) // 2))
    alpha = canvas.getchannel("A")
    rim = alpha.filter(ImageFilter.MaxFilter(5))
    out = Image.new("RGBA", (SIZE, SIZE), (235, 240, 250, 0))
    out.putalpha(ImageChops.multiply(rim, Image.new("L", rim.size, 170)))
    out.alpha_composite(canvas)
    return out


def without_stray(surfaces, min_x):
    """Drop triangles parked behind the camera (the Garand's spare clip)."""
    out = []
    for name, tri, st, tex in surfaces:
        keep = tri[:, :, 0].mean(axis=1) > min_x
        out.append((name, tri[keep], st[keep], tex))
    return [s for s in out if len(s[1])]


def card(name, keep_top=1.0):
    img = image(name)
    img = img.crop(img.getchannel("A").getbbox())
    return img.crop((0, 0, img.width, round(img.height * keep_top)))


def lightning():
    """Original side view of a thunderbolt-style gun: coil emitter, twin rails, grip, and a bolt."""
    s = 4
    img = Image.new("RGBA", (192 * s, 192 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def poly(points, fill):
        d.polygon([(x * s, y * s) for x, y in points], fill=fill)

    metal, dark, trim, glow = (150, 156, 168, 255), (82, 86, 100, 255), (188, 140, 72, 255), (130, 200, 255, 255)
    poly([(10, 92), (30, 78), (92, 78), (104, 88), (104, 112), (30, 116), (10, 108)], metal)   # body
    poly([(30, 78), (44, 66), (82, 66), (92, 78)], dark)                                       # top housing
    poly([(40, 116), (58, 116), (50, 146), (32, 142)], dark)                                   # grip
    poly([(70, 114), (92, 112), (88, 128), (72, 130)], trim)                                   # cell
    poly([(104, 84), (158, 84), (162, 90), (104, 90)], dark)                                   # upper rail
    poly([(104, 108), (162, 108), (158, 114), (104, 114)], dark)                               # lower rail
    for x in (114, 130, 146):
        poly([(x, 80), (x + 7, 80), (x + 7, 118), (x, 118)], trim)                             # coils
    poly([(160, 94), (174, 88), (170, 99), (186, 96), (164, 112), (170, 101), (158, 104)], glow)
    d.line([(18 * s, 96 * s), (98 * s, 96 * s)], fill=glow, width=4 * s)
    return img


ICONS = {
    "hammer": lambda: (render(load_mdl("progs/v_hammer.mdl", 0), az=0, el=20), 1.5, -35),
    "pump": lambda: (image("gfx/dn3sg/hud_icon.png"), 1.5, 30),
    "milky": lambda: (card("progs/mvm_a_00.png"), 1.0),
    "grenade": lambda: (render(load_mdl("progs/v_rock.mdl", 0)), 1.35),
    "rocket": lambda: (render(load_mdl("progs/v_rock2.mdl", 0)), 1.35),
    "lightning": lambda: (lightning(), 1.0),
    "ccc": lambda: (render(load_mdl("progs/v_laserg.mdl", 0)), 1.35),
    "megaman": lambda: (render(load_md3("progs/v_megaman.md3", 0), az=-60, el=18, skip=HANDS + ("fx",)), 1.2),
    "m4": lambda: (render(load_md3("progs/v_m4.md3", 0), az=-90, el=0, skip=HANDS + ("view_skin",)), 1.6, 30),
    "robdob": lambda: (card("progs/rh_drone_head_000.png"), 1.0),
    "jar": lambda: (card("progs/gjvm_000.png"), 1.1),
    "pickle": lambda: (card("progs/pvm_000.png"), 1.1),
    "netsend": lambda: (card("progs/ndvm_000.png"), 1.15),
    "dookie": lambda: (card("progs/dvm_000.png"), 1.1),
    "wheelman": lambda: (render(load_md3("progs/v_wewcannon.md3", 0), az=-65, el=16, skip=HANDS + ("fx",)), 1.2),
    "kyle": lambda: (card("progs/kvm_000.png"), 1.15),
    "cyrax": lambda: (card("progs/cyrax_vm_00.png"), 1.2),
}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    open_game(sys.argv[1])
    os.makedirs(ASSETS, exist_ok=True)
    for name in sys.argv[2:] or ICONS:
        finish(*ICONS[name]()).save(os.path.join(ASSETS, name + ".png"), optimize=True)
        print(name)


if __name__ == "__main__":
    main()
