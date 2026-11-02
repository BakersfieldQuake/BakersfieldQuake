"""Make ~320x320 transparent thumbnails for the Mystery Box monster vote page.
Run: python -I make_vote_thumbs.py [ids...]   (needs numpy + PIL)
Output: source/mm_tools/out/mystery_box/vote_thumbs/<id>_<name>.png
"""
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM = os.path.dirname(HERE)
MOD = os.path.dirname(os.path.dirname(MM))
sys.path.insert(0, MM)
import md3lib  # noqa: E402

OUT = os.path.join(MM, "out", "mystery_box", "vote_thumbs")
os.makedirs(OUT, exist_ok=True)
SIZE = 320
TARGET_H = round(SIZE * 0.85)      # every monster fills ~85% of the card height ...
TARGET_W = SIZE - 20               # ... unless that would be wider than the card
BASELINE = SIZE - 24               # common baseline (bottom of the figure), so top margin = 24 at full height


def mod(*p):
    return os.path.join(MOD, *p)


# ---------------------------------------------------------------- sprites
def read_spr32(path):
    d = open(path, "rb").read()
    magic, ver, typ = struct.unpack("<4sii", d[:12])
    assert magic == b"IDSP" and ver == 32, (magic, ver)
    radius, w, h, nf, beam, sync = struct.unpack("<fiiifi", d[12:36])
    o = 36
    frames = []
    for _ in range(nf):
        grp, ox, oy, fw, fh = struct.unpack("<5i", d[o:o + 20])
        assert grp == 0
        o += 20
        px = np.frombuffer(d, np.uint8, fw * fh * 4, o).reshape(fh, fw, 4).copy()
        o += fw * fh * 4
        frames.append(px)
    return frames


def fit_image(img):
    """crop RGBA PIL image to its alpha bbox and fit it into a SIZE x SIZE canvas."""
    bb = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bb:
        img = img.crop(bb)
    s = min(TARGET_W / img.width, TARGET_H / img.height)     # every monster the same height unless too wide
    nw, nh = max(1, round(img.width * s)), max(1, round(img.height * s))
    a = np.asarray(img, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]  # premultiply so resizing leaves no fringes
    pm = Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")
    pm = pm.resize((nw, nh), Image.LANCZOS if s < 1 else Image.NEAREST)
    b = np.asarray(pm, np.float32) / 255.0
    al = b[..., 3:4]
    b[..., :3] = np.where(al > 0, b[..., :3] / np.maximum(al, 1e-4), 0)
    out = Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(out, ((SIZE - nw) // 2, BASELINE - nh), out)
    return canvas


def sprite_thumb(path, frame):
    fr = read_spr32(path)
    return fit_image(Image.fromarray(fr[frame], "RGBA"))


def png_thumb(path):
    return fit_image(Image.open(path).convert("RGBA"))


# ---------------------------------------------------------------- textures
_tex_cache = {}


def load_tex(shader):
    if shader in _tex_cache:
        return _tex_cache[shader]
    res = None
    for ext in (".png", ".tga", ".jpg"):
        p = mod(shader + ext)
        if os.path.exists(p):
            res = np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255.0
            break
    _tex_cache[shader] = res
    return res


def sample(tex, u, v, flip):
    h, w = tex.shape[:2]
    u = u - np.floor(u)
    v = v - np.floor(v)
    if flip:
        v = 1 - v
    x = np.clip((u * w).astype(int), 0, w - 1)
    y = np.clip((v * h).astype(int), 0, h - 1)
    return tex[y, x]


# ---------------------------------------------------------------- rasteriser
def render_md3(path, frame=0, skin=None, az=38, el=20, flipv=False, extra_fallback=None,
               skip=(), glass=("glass",), R=2, gain=1.0):
    model = md3lib.read(path)
    skinmap = {}
    if skin:
        for line in open(skin).read().splitlines():
            if "," in line:
                a, b = line.split(",", 1)
                skinmap[a.strip()] = b.strip()
    azr, elr = math.radians(az), math.radians(el)
    cam = np.array([math.cos(elr) * math.cos(azr), math.cos(elr) * math.sin(azr), math.sin(elr)])
    fwd = -cam
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    light = cam + right * -0.6 + up * 0.9
    light /= np.linalg.norm(light)

    surfs = []
    allv = []
    for s in model["surfaces"]:
        if any(k in s["name"] for k in skip):
            continue
        fi = min(frame, len(s["frames"]) - 1)
        v, n = s["frames"][fi]
        v = np.array(v, np.float64)
        n = np.array(n, np.float64)
        surfs.append((s, v, n))
        allv.append(v)
    allv = np.concatenate(allv)
    px = allv @ right
    py = allv @ up
    cx, cy = (px.min() + px.max()) / 2, (py.min() + py.max()) / 2
    span = max(px.max() - px.min(), py.max() - py.min())
    N = SIZE * R
    scale = (N - 28 * R) / span

    color = np.zeros((N, N, 3), np.float32)
    alpha = np.zeros((N, N), np.float32)
    zbuf = np.full((N, N), -1e18, np.float64)

    order = sorted(range(len(surfs)), key=lambda i: any(g in surfs[i][0]["name"] for g in glass))
    for i in order:
        s, v, n = surfs[i]
        name = s["name"]
        is_glass = any(g in name for g in glass)
        sh = skinmap.get(name, s["shader"])
        tex = load_tex(sh)
        if tex is None:
            if extra_fallback and name in extra_fallback:
                c = extra_fallback[name]
            elif sh.startswith("progs/bklan/t_flat_"):
                hx = sh[-6:]
                c = tuple(int(hx[k:k + 2], 16) / 255 for k in (0, 2, 4))
            else:
                c = (0.55, 0.55, 0.6)
            tex = np.array([[[c[0], c[1], c[2], 1.0]]], np.float32)
        st = np.array(s["st"], np.float64)
        sx = (v @ right - cx) * scale + N / 2
        sy = N / 2 - ((v @ up - cy) * scale)
        sz = -(v @ fwd)  # larger = nearer
        for (a, b, c) in s["tris"]:
            xs = (sx[a], sx[b], sx[c])
            ys = (sy[a], sy[b], sy[c])
            x0 = max(int(math.floor(min(xs))), 0)
            x1 = min(int(math.ceil(max(xs))), N - 1)
            y0 = max(int(math.floor(min(ys))), 0)
            y1 = min(int(math.ceil(max(ys))), N - 1)
            if x1 < x0 or y1 < y0:
                continue
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not m.any():
                continue
            z = w0 * sz[a] + w1 * sz[b] + w2 * sz[c]
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            if not is_glass:
                m &= z > zb
            if not m.any():
                continue
            u = w0 * st[a, 0] + w1 * st[b, 0] + w2 * st[c, 0]
            vv = w0 * st[a, 1] + w1 * st[b, 1] + w2 * st[c, 1]
            t = sample(tex, u, vv, flipv)
            nn = w0[..., None] * n[a] + w1[..., None] * n[b] + w2[..., None] * n[c]
            nn /= np.maximum(np.linalg.norm(nn, axis=-1, keepdims=True), 1e-6)
            facing = nn @ cam
            nn = np.where((facing < 0)[..., None], -nn, nn)
            lam = np.clip(nn @ light, 0, 1)
            shade = 0.50 + 0.55 * lam
            ta = t[..., 3]
            col = np.clip(t[..., :3] * shade[..., None] * gain, 0, 1)
            dst = color[y0:y1 + 1, x0:x1 + 1]
            al0 = alpha[y0:y1 + 1, x0:x1 + 1]
            if is_glass:
                a_eff = np.minimum(ta, 0.40)
                m &= a_eff > 0.02
                if not m.any():
                    continue
                dst[m] = dst[m] * (1 - a_eff[m][:, None]) + col[m] * a_eff[m][:, None]
                al0[m] = np.maximum(al0[m], a_eff[m])
                continue
            m &= ta > 0.5
            if not m.any():
                continue
            dst[m] = col[m]
            al0[m] = 1.0
            zb[m] = z[m]
    pm = color * alpha[..., None]
    pm = pm.reshape(SIZE, R, SIZE, R, 3).mean(axis=(1, 3))
    al = alpha.reshape(SIZE, R, SIZE, R).mean(axis=(1, 3))
    rgb = np.where(al[..., None] > 0, pm / np.maximum(al[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), al])
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")


SPEC = [
    (1, "megaman_contraption", lambda: render_md3(mod("progs/megaman.md3"), 0)),
    (2, "suit_rider", lambda: render_md3(mod("progs/mm_suit_rider.md3"), 0, mod("progs/mm_suit_rider.md3_0.skin"), skip=("spark_fx",))),
    (3, "pink_supercar", lambda: render_md3(mod("progs/pink_supercar.md3"), 0, mod("progs/pink_supercar.md3_0.skin"))),
    (4, "squat_rider", lambda: render_md3(mod("progs/mm_squat_rider.md3"), 0, mod("progs/mm_squat_rider.md3_0.skin"), skip=("spark_fx",))),
    (5, "netsend_pc", lambda: render_md3(mod("progs/netsend_pc.md3"), 20, mod("progs/netsend_pc.md3_0.skin"),
                                         extra_fallback={"netsend_screen": (0.1, 0.25, 0.8)})),
    (6, "gw_horse", lambda: render_md3(mod("progs/gw_horse.md3"), 0, mod("progs/gw_horse.md3_0.skin"))),
    (7, "bigears_head", lambda: render_md3(mod("progs/bigears.md3"), 0)),
    (8, "forklift", lambda: render_md3(mod("progs/bklan/sr_vehicle_forklift_orange_a01.md3"), 0, flipv=True, gain=2.2)),
    (9, "wheelman", lambda: sprite_thumb(mod("progs/wheelman.spr32"), 0)),
    (10, "jesskart", lambda: sprite_thumb(mod("progs/jesskart.spr32"), 0)),
    (11, "kyle_scissors", lambda: sprite_thumb(mod("progs/fr_scissors.spr32"), 0)),
    (12, "earhead", lambda: png_thumb(mod("earhead_sprite", "earhead_00.png"))),
    (13, "pickle_surprise", lambda: png_thumb(mod("progs", "pickle_00.png"))),
    (14, "friend_rob", lambda: sprite_thumb(mod("progs/fr_rob.spr32"), 0)),
    (15, "john_wave_hand", lambda: sprite_thumb(mod("progs/fr_johnhand.spr32"), 0)),
    (16, "wheelman_rolling", lambda: sprite_thumb(mod("progs/wheelman.spr32"), 8 + 2 * 6 + 1)),
    # sprites added 2026-10-31 (frame 0 = idle, facing the viewer)
    (17, "bryan_demons", lambda: sprite_thumb(mod("progs/bryan.spr32"), 0)),
    (18, "dennis", lambda: sprite_thumb(mod("progs/fr_dennis.spr32"), 0)),
    (19, "paul", lambda: sprite_thumb(mod("progs/fr_paul.spr32"), 0)),
    (20, "quakeguy", lambda: sprite_thumb(mod("progs/fr_quakeguy.spr32"), 0)),
    (21, "mr_diy", lambda: sprite_thumb(mod("progs/fr_mrdiy.spr32"), 0)),
    (22, "rubber_finger", lambda: sprite_thumb(mod("progs/fr_finger.spr32"), 0)),
]

def reframe(im):
    """Crop to the visible content and fit it to the same height / baseline as the sprites (used for the 3D renders)."""
    bb = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bb:
        return im
    c = im.crop(bb)
    s = min(TARGET_W / c.width, TARGET_H / c.height)
    if abs(s - 1) < 0.01 and bb[3] == BASELINE:
        return im
    a = np.asarray(c, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    pm = Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")
    nw, nh = max(1, round(c.width * s)), max(1, round(c.height * s))
    pm = pm.resize((nw, nh), Image.LANCZOS if s < 1 else Image.BICUBIC)
    b = np.asarray(pm, np.float32) / 255.0
    al = b[..., 3:4]
    b[..., :3] = np.where(al > 0, b[..., :3] / np.maximum(al, 1e-4), 0)
    out = Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(out, ((SIZE - nw) // 2, BASELINE - nh), out)
    return canvas


if __name__ == "__main__":
    import time
    import normalise_vote_thumbs as nv
    only = {int(a) for a in sys.argv[1:]}
    os.makedirs(nv.RAW, exist_ok=True)
    for i, name, fn in SPEC:
        if only and i not in only:
            continue
        t0 = time.time()
        im = reframe(fn())
        im.save(os.path.join(nv.RAW, "%02d_%s.png" % (i, name)), optimize=True)    # un-toned frames
        print(i, name, "%.1fs" % (time.time() - t0), flush=True)
    nv.run()                                                                       # brightness/contrast match -> OUT
