"""bklan sky: a bright sunny-day skybox (owner 2026-11-01: "too dark and boring, it should be on a bright sunny day").
Writes gfx/env/bklan_{rt,bk,lf,ft,up,dn}.png (512 px). Blue gradient (pale at the horizon, deep blue overhead), soft white
cumulus from 3D noise (so the clouds run across the cube edges), a sun disc with a glow where the map's _sunlight comes from
(worldspawn "_sunlight_mangle" "60 -52 0": the light travels toward +x +y, so the sun hangs in the -x -y sky, 52 degrees up),
a hazy horizon and a pale ground colour below.
The old faces are kept in gfx/env/bklan_old/ the first time this runs.
usage: python build_bklan_sky.py   (WindowsApps python3.13: PIL + numpy)"""
import os
import shutil

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ENV = os.path.join(MOD, "gfx", "env")
N = 512
SUN = np.array([-0.31, -0.53, 0.79])
SUN = SUN / np.linalg.norm(SUN)

ZENITH = np.array([20.0, 56.0, 134.0])
MID = np.array([40.0, 86.0, 158.0])
HORIZON = np.array([110.0, 132.0, 158.0])
GROUND = np.array([96.0, 90.0, 78.0])


# which file DarkPlaces draws on each side (read off a labelled test sky in game, 2026-11-01): facing +x it shows "rt",
# then turning right (-y) "ft", then -x "lf", then +y "bk"; the faces below are named by the direction they look at
FILE = {"ft": "rt", "rt": "ft", "bk": "lf", "lf": "bk"}


def faces():
    """direction of every pixel on each face, keyed by the direction it covers: ft = +x, bk = -x, lf = +y, rt = -y, up = +z, dn = -z
    (written to the file FILE says; the up face is flipped top to bottom when saved)"""
    u, v = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))      # v grows downward in the image
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


_rng = np.random.RandomState(7)
_PERM = _rng.randint(0, 256, 512)
_VAL = _rng.rand(256)


def _hash(ix, iy, iz):
    return _VAL[_PERM[(_PERM[(_PERM[ix & 255] + iy) & 255] + iz) & 255]]


def noise3(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    ix, iy, iz = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    r = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                r = r + w * _hash(ix + dx, iy + dy, iz + dz)
    return r


def fbm(p, octaves=5):
    s, a, f = 0, 0.5, 1.0
    for _ in range(octaves):
        s = s + a * noise3(p * f)
        a *= 0.5
        f *= 2.05
    return s


def sky(d):
    z = d[..., 2]
    # base gradient by height above the horizon
    t = np.clip(z, 0, 1)
    col = HORIZON + (MID - HORIZON) * np.clip(t * 3.2, 0, 1)[..., None]
    col = col + (ZENITH - MID) * np.clip((t - 0.3) / 0.7, 0, 1)[..., None]
    # below the horizon: pale haze fading to the ground colour
    below = np.clip(-z * 2.5, 0, 1)[..., None]
    col = col * (1 - below) + GROUND * below
    # clouds: 3D noise on the direction itself, squashed in z so they lie in flat banks (a flat-layer projection made
    # straight radial streaks that showed as bright diagonal bands where the cube faces meet)
    p = np.stack([d[..., 0] * 3.2, d[..., 1] * 3.2, d[..., 2] * 7.0], -1) + 20
    n = fbm(p)
    cover = np.clip((n - 0.54) * 2.8, 0, 1)
    cover = cover * np.clip(z * 5.0, 0, 1)                         # thin out into the haze at the horizon
    lit = np.clip(0.75 + 0.25 * (d @ SUN), 0, 1)
    ccol = (np.array([168.0, 164.0, 156.0]) * lit[..., None] + np.array([98.0, 114.0, 140.0]) * (1 - lit[..., None]))
    shade = np.clip(1.0 - (cover - 0.4) * 0.28, 0.82, 1.0)[..., None]       # thick middles a little grey
    col = col * (1 - cover[..., None] * 0.65) + ccol * shade * cover[..., None] * 0.65
    # sun: warm golden glow and a compact warm disc (tuned for v_gamma 1.75 so the sky never washes out white)
    cs = np.clip(d @ SUN, -1, 1)
    glow = np.clip((cs - 0.91) / 0.09, 0, 1) ** 3
    col = col + (np.array([218.0, 188.0, 128.0]) - col) * (glow * 0.38)[..., None]
    disc = np.clip((cs - 0.9985) / 0.0010, 0, 1)
    col = col * (1 - disc[..., None]) + np.array([238.0, 226.0, 192.0]) * disc[..., None]
    return np.clip(col, 0, 255).astype(np.uint8)


def web_faces(out_dir, gain=1.15):
    """The same sky for the browser viewer (export_web_viewer.py): six jpgs in the order its CubeTextureLoader takes them
    (rt lf up dn bk ft = three's +x -x +y -y +z -z faces). three draws a cube background with the OpenGL face layout and the
    x axis mirrored; the viewer's world is Quake (x, y, z) -> three (x, z, -y)."""
    from PIL import ImageEnhance
    u, v = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    one = np.ones_like(u)
    gl = {"rt": (one, -v, -u), "lf": (-one, -v, u), "up": (u, one, v), "dn": (u, -one, -v), "bk": (u, -v, one), "ft": (-u, -v, -one)}
    os.makedirs(out_dir, exist_ok=True)
    for name, (rx, ry, rz) in gl.items():
        x3, y3, z3 = -rx, ry, rz                                   # three's world direction (the background flips x)
        d = np.stack([x3, -z3, y3], -1)                            # the Quake direction
        d = d / np.linalg.norm(d, axis=-1, keepdims=True)
        im = ImageEnhance.Brightness(Image.fromarray(sky(d), "RGB")).enhance(gain)
        im.save(os.path.join(out_dir, "%s.jpg" % name), quality=88)


def main():
    os.makedirs(ENV, exist_ok=True)
    old = os.path.join(ENV, "bklan_old")
    if not os.path.isdir(old):
        os.makedirs(old)
        for k in ("rt", "bk", "lf", "ft", "up", "dn"):
            src = os.path.join(ENV, "bklan_%s.png" % k)
            if os.path.exists(src):
                shutil.copy(src, old)
    for k, d in faces().items():
        f = FILE.get(k, k)
        im = Image.fromarray(sky(d), "RGB")
        if k == "up":
            im = im.transpose(Image.FLIP_TOP_BOTTOM)           # in game the up face is drawn flipped vertically (found by trying the 8 orientations)
        im.save(os.path.join(ENV, "bklan_%s.png" % f))
        print("bklan_%s.png" % f)


if __name__ == "__main__":
    main()
