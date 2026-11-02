"""build_midair_sky.py — Seamless 3D-projected nighttime cubemap for `maps/midair.bsp`.
Writes `gfx/env/midair_{rt,bk,lf,ft,up,dn}.png` and `.tga` (1024x1024 per face):
- Deep cosmic midnight-indigo zenith grading to nocturnal cobalt and subtle Bakersfield night-horizon glow
- Seamless 3D cell-hashed multi-temperature starfield (zero cubemap edge seams)
- Soft 3D FBM Milky Way / violet-cyan nebula band overhead for clear visual reference when aiming straight up
- Crisp silver-white full moon with 3D mare detail and atmospheric lunar corona aligned with worldspawn moonlight
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ENV = os.path.join(MOD, "gfx", "env")
N = 1024

# Moon sits in NW sky (-X, +Y, +Z) at ~31 deg elevation so it frames dramatically above the arena rim!
# Moonlight travels toward (+0.52, -0.64, -0.50) -> _sunlight_mangle "309 -31 0"
MOON = np.array([-0.52, 0.64, 0.50], dtype=np.float64)
MOON = MOON / np.linalg.norm(MOON)

ZENITH = np.array([6.0, 10.0, 26.0])
MID = np.array([12.0, 21.0, 48.0])
HORIZON = np.array([24.0, 36.0, 70.0])
ABYSS = np.array([4.0, 6.0, 15.0])

# Verified DarkPlaces cubemap face mapping (see build_bklan_sky.py)
FILE = {"ft": "rt", "rt": "ft", "bk": "lf", "lf": "bk"}


def faces():
    u, v = np.meshgrid(np.linspace(-1.0, 1.0, N), np.linspace(-1.0, 1.0, N))
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


_rng = np.random.RandomState(2026)
_PERM = _rng.randint(0, 256, 512)
_VAL = _rng.rand(256)


def _hash(ix, iy, iz):
    return _VAL[_PERM[(_PERM[(_PERM[ix & 255] + iy) & 255] + iz) & 255]]


def noise3(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    ix, iy, iz = np.floor(x).astype(int), np.floor(y).astype(int), np.floor(z).astype(int)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3.0 - 2.0 * fx), fy * fy * (3.0 - 2.0 * fy), fz * fz * (3.0 - 2.0 * fz)
    r = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1.0 - fx) * (fy if dy else 1.0 - fy) * (fz if dz else 1.0 - fz)
                r = r + w * _hash(ix + dx, iy + dy, iz + dz)
    return r


def fbm(p, octaves=5):
    s, a, f = 0.0, 0.5, 1.0
    for _ in range(octaves):
        s = s + a * noise3(p * f)
        a *= 0.5
        f *= 2.07
    return s


def star_layer(d, scale, density, size_sharpness, brightness):
    """3D Worley/cell-center stars on the unit direction vector so cube edges are 100% seamless."""
    p = d * scale
    base = np.floor(p).astype(int)
    best_dist2 = np.full(d.shape[:-1], 99.0, dtype=np.float64)
    best_c1 = np.zeros(d.shape[:-1], dtype=np.float64)
    best_c2 = np.zeros(d.shape[:-1], dtype=np.float64)

    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            for oz in (-1, 0, 1):
                cx = base[..., 0] + ox
                cy = base[..., 1] + oy
                cz = base[..., 2] + oz
                h0 = _hash(cx * 3 + 1, cy * 5 + 7, cz * 7 + 13)
                active = h0 > (1.0 - density)
                if not np.any(active):
                    continue
                jx = _hash(cx + 17, cy + 31, cz + 47)
                jy = _hash(cx + 59, cy + 83, cz + 101)
                jz = _hash(cx + 131, cy + 167, cz + 199)
                sx = cx + 0.15 + 0.70 * jx
                sy = cy + 0.15 + 0.70 * jy
                sz = cz + 0.15 + 0.70 * jz
                dx = p[..., 0] - sx
                dy = p[..., 1] - sy
                dz = p[..., 2] - sz
                dist2 = np.where(active, dx * dx + dy * dy + dz * dz, 99.0)
                closer = dist2 < best_dist2
                best_dist2 = np.where(closer, dist2, best_dist2)
                best_c1 = np.where(closer, _hash(cx + 211, cy + 11, cz + 73), best_c1)
                best_c2 = np.where(closer, _hash(cx + 37, cy + 149, cz + 233), best_c2)

    intensity = np.exp(-best_dist2 * size_sharpness) * (0.45 + 0.55 * best_c1) * brightness
    # Star temperature tint: cool ice-blue <-> pure white <-> warm gold
    warm = np.array([255.0, 214.0, 168.0])
    white = np.array([236.0, 244.0, 255.0])
    ice = np.array([162.0, 206.0, 255.0])
    t = best_c2[..., None]
    tint = np.where(t < 0.5, ice + (white - ice) * (t * 2.0), white + (warm - white) * ((t - 0.5) * 2.0))
    return tint * intensity[..., None]


def sky(d):
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    t = np.clip(z, 0.0, 1.0)

    # Base nocturnal sky gradient
    col = HORIZON + (MID - HORIZON) * np.clip(t * 2.6, 0.0, 1.0)[..., None]
    col = col + (ZENITH - MID) * np.clip((t - 0.28) / 0.72, 0.0, 1.0)[..., None]

    # Below horizon: smooth fade into dark midnight valley abyss
    below = np.clip(-z * 3.4, 0.0, 1.0)[..., None]
    col = col * (1.0 - below) + ABYSS * below

    # Subtle distant night-city horizon glow (warm amber + neon cyan haze right along the horizon)
    az_var = noise3(np.stack([x * 4.5 + 3.0, y * 4.5 - 2.0, z * 2.0], -1))
    hband = np.exp(-((z - 0.015) / 0.085) ** 2) * (0.55 + 0.65 * az_var)
    city_warm = np.array([92.0, 56.0, 84.0])
    city_cyan = np.array([32.0, 82.0, 118.0])
    mix_c = np.clip(noise3(np.stack([x * 2.8 - 9.0, y * 2.8 + 5.0, z * 2.0], -1)) * 1.4 - 0.2, 0.0, 1.0)[..., None]
    city_col = city_warm * (1.0 - mix_c) + city_cyan * mix_c
    col = col + city_col * (hband * 0.42)[..., None]

    # Faint distant valley street-light pinpoints below the horizon (-0.42 < z < -0.03)
    valley_mask = np.clip((-z - 0.02) / 0.06, 0.0, 1.0) * np.clip((0.45 + z) / 0.30, 0.0, 1.0)
    if np.any(valley_mask > 0.01):
        vstars = star_layer(d, scale=95.0, density=0.14, size_sharpness=110.0, brightness=0.42)
        amber_tint = np.array([1.0, 0.72, 0.38])
        col = col + vstars * amber_tint * valley_mask[..., None]

    # Overhead Milky Way / cosmic violet-cyan nebula band (tilted great circle across the zenith)
    band_coord = 0.58 * x + 0.42 * y - 0.22 * (1.0 - z)
    band_env = np.exp(-(band_coord / 0.34) ** 2) * np.clip((z - 0.04) / 0.25, 0.0, 1.0)
    neb1 = fbm(d * 4.2 + 7.3, octaves=5)
    neb2 = fbm(d * 8.5 - 3.1, octaves=4)
    neb_strength = band_env * np.clip((neb1 - 0.36) * 2.1, 0.0, 1.0)
    dust_lane = np.clip((neb2 - 0.56) * 3.2, 0.0, 1.0)
    neb_col = np.array([34.0, 48.0, 96.0]) * (1.0 - 0.45 * dust_lane[..., None]) + np.array([58.0, 28.0, 88.0]) * (neb2[..., None] * 0.55)
    col = col + neb_col * (neb_strength * 0.72)[..., None]

    # Thin nocturnal silver-lit clouds low-to-mid sky
    cp = np.stack([x * 3.4, y * 3.4, z * 7.5], -1) + 14.0
    cn = fbm(cp, octaves=5)
    clouds = np.clip((cn - 0.60) * 2.5, 0.0, 1.0) * np.clip(z * 5.0, 0.0, 1.0) * np.clip(1.25 - z * 0.7, 0.35, 1.0)
    cm = np.clip(d @ MOON, -1.0, 1.0)
    moon_rim = np.clip((cm - 0.35) / 0.65, 0.0, 1.0) ** 2
    cloud_col = np.array([22.0, 32.0, 58.0]) + np.array([58.0, 74.0, 108.0]) * moon_rim[..., None]
    col = col * (1.0 - clouds[..., None] * 0.55) + cloud_col * (clouds[..., None] * 0.55)

    # Multi-tier seamless 3D starfield (fades near horizon haze, behind thick clouds, and inside moon glare)
    star_vis = np.clip((z - 0.02) / 0.14, 0.0, 1.0) * (1.0 - clouds * 0.80) * np.clip(1.0 - np.clip((cm - 0.96) / 0.04, 0.0, 1.0), 0.0, 1.0)
    if np.any(star_vis > 0.005):
        s_fine = star_layer(d, scale=88.0, density=0.22, size_sharpness=95.0, brightness=0.72)
        s_mid = star_layer(d + 0.37, scale=46.0, density=0.14, size_sharpness=85.0, brightness=1.05)
        s_bright = star_layer(d - 0.61, scale=22.0, density=0.07, size_sharpness=75.0, brightness=1.45)
        col = col + (s_fine + s_mid + s_bright) * star_vis[..., None]

    # Luminous Moon + silver-blue atmospheric corona
    halo_wide = np.clip((cm - 0.82) / 0.18, 0.0, 1.0) ** 2.6
    halo_tight = np.clip((cm - 0.965) / 0.035, 0.0, 1.0) ** 2.2
    col = col + np.array([42.0, 62.0, 105.0]) * halo_wide[..., None]
    col = col + np.array([95.0, 118.0, 160.0]) * halo_tight[..., None]

    # Crisp lunar disc (~4.2 deg apparent diameter -> dramatic nighttime arena moon!)
    disc = np.clip((cm - 0.9972) / 0.00045, 0.0, 1.0)
    if np.any(disc > 0.0):
        mare = fbm(d * 120.0 + 5.0, octaves=4)
        limb = np.clip((cm - 0.9972) / (1.0 - 0.9972), 0.0, 1.0) ** 0.35
        moon_surface = (np.array([226.0, 235.0, 252.0]) - np.array([54.0, 50.0, 42.0]) * np.clip((mare - 0.43) * 2.5, 0.0, 1.0)[..., None])
        moon_surface = moon_surface * (0.78 + 0.22 * limb[..., None])
        col = col * (1.0 - disc[..., None]) + moon_surface * disc[..., None]

    return np.clip(col, 0, 255).astype(np.uint8)


def main():
    os.makedirs(ENV, exist_ok=True)
    for k, d in faces().items():
        f = FILE.get(k, k)
        im = Image.fromarray(sky(d), "RGB")
        if k == "up":
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        png_path = os.path.join(ENV, f"midair_{f}.png")
        tga_path = os.path.join(ENV, f"midair_{f}.tga")
        im.save(png_path)
        im.save(tga_path)
        print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
