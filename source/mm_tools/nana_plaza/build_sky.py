"""build_sky.py — Photo-calibrated Bangkok clear daytime skybox for Nana Plaza (`gfx/env/nanaplaza_{rt,bk,lf,ft,up,dn}.png`).
Calibrated directly against `ref_029.jpg`, `ref_045.jpg`, and `ref_049.jpg` (Dec 2025 Soi 4 Street View):
- Clear blue upper sky (`ref_045.jpg` top-left) grading into pale warm tropical horizon haze (`ref_045.jpg` centre-top)
- Sun in the SE sky (`+0.52, -0.45, +0.725`, matching the shadows cast across Soi 4 by East-side shophouses in `ref_029`/`ref_045` and the solar glare looking South in `ref_049`).
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ENV = os.path.join(MOD, "gfx", "env")
N = 512

# Sun hangs in SE sky (+X East, -Y South, +Z Up); light travels toward (-0.52, +0.45, -0.725) -> _sunlight_mangle "139 -47 0"
SUN = np.array([0.52, -0.45, 0.725])
SUN = SUN / np.linalg.norm(SUN)

# Sampled from ref_045.jpg sky & tuned for DarkPlaces default gamma so horizon is crisp pale blue, never blown out
ZENITH = np.array([54.0, 96.0, 168.0])
MID = np.array([88.0, 134.0, 194.0])
HORIZON = np.array([156.0, 178.0, 204.0])
GROUND = np.array([104.0, 102.0, 98.0])

# DarkPlaces cubemap file convention verified in build_bklan_sky.py
FILE = {"ft": "rt", "rt": "ft", "bk": "lf", "lf": "bk"}


def faces():
    u, v = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    one = np.ones_like(u)
    d = {
        "ft": (one, -u, -v),
        "bk": (-one, u, -v),
        "lf": (u, one, -v),
        "rt": (-u, -one, -v),
        "up": (-v, -u, one),
        "dn": (v, -u, -one),
    }
    out = {}
    for k, (x, y, z) in d.items():
        a = np.stack([x, y, z], -1)
        out[k] = a / np.linalg.norm(a, axis=-1, keepdims=True)
    return out


_rng = np.random.RandomState(42)
_PERM = _rng.randint(0, 256, 512)
_VAL = _rng.rand(256)


def _hash(ix, iy, iz):
    return _VAL[_PERM[(_PERM[(_PERM[ix & 255] + iy) & 255] + iz) & 255]]


def noise3(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    ix, iy, iz = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    r = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                r = r + w * _hash(ix + dx, iy + dy, iz + dz)
    return r


def fbm(p, octaves=4):
    s, a, f = 0.0, 0.5, 1.0
    for _ in range(octaves):
        s = s + a * noise3(p * f)
        a *= 0.5
        f *= 2.03
    return s


def sky(d):
    z = d[..., 2]
    t = np.clip(z, 0.0, 1.0)
    col = HORIZON + (MID - HORIZON) * np.clip(t * 2.8, 0.0, 1.0)[..., None]
    col = col + (ZENITH - MID) * np.clip((t - 0.28) / 0.72, 0.0, 1.0)[..., None]
    below = np.clip(-z * 2.8, 0.0, 1.0)[..., None]
    col = col * (1.0 - below) + GROUND * below

    # Very light high wisps (Dec 2025 Bangkok dry season in ref_045.jpg is mostly clear pale blue with soft tropical haze)
    p = np.stack([d[..., 0] * 3.0, d[..., 1] * 3.0, d[..., 2] * 6.5], -1) + 11.0
    n = fbm(p)
    cover = np.clip((n - 0.62) * 2.4, 0.0, 1.0) * np.clip(z * 4.5, 0.0, 1.0)
    ccol = np.array([204.0, 208.0, 214.0])
    col = col * (1.0 - cover[..., None] * 0.35) + ccol * (cover[..., None] * 0.35)

    # Warm Bangkok solar aureole in SE sky (matching ref_049.jpg looking South)
    cs = np.clip(d @ SUN, -1.0, 1.0)
    haze = np.clip((cs - 0.55) / 0.45, 0.0, 1.0) ** 2 * np.clip(1.0 - abs(z - 0.35) * 1.1, 0.2, 1.0)
    col = col + (np.array([216.0, 212.0, 198.0]) - col) * (haze * 0.36)[..., None]
    glow = np.clip((cs - 0.92) / 0.08, 0.0, 1.0) ** 3
    col = col + (np.array([238.0, 224.0, 186.0]) - col) * (glow * 0.48)[..., None]
    disc = np.clip((cs - 0.9982) / 0.0012, 0.0, 1.0)
    col = col * (1.0 - disc[..., None]) + np.array([250.0, 244.0, 222.0]) * disc[..., None]
    return np.clip(col, 0, 255).astype(np.uint8)


def main():
    os.makedirs(ENV, exist_ok=True)
    for k, d in faces().items():
        f = FILE.get(k, k)
        im = Image.fromarray(sky(d), "RGB")
        if k == "up":
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        out_p = os.path.join(ENV, f"nanaplaza_{f}.png")
        out_tga = os.path.join(ENV, f"nanaplaza_{f}.tga")
        im.save(out_p)
        im.save(out_tga)
        print(f"Wrote {out_p} & {out_tga}")


if __name__ == "__main__":
    main()
