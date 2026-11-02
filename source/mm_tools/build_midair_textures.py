"""build_midair_textures.py — Procedural high-res nocturnal colosseum textures + emissive `_glow.png` maps
for `maps/midair.bsp`.

Writes:
  - `BakersfieldQuake/textures/ma_*.png` (+ `ma_*_glow.png` additive fullbright maps for DarkPlaces)
  - `source/mm_tools/out/maps/midair.wad` (WAD2 miptex archive for ericw qbsp/light)
"""
import math
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wad2 import write_wad  # noqa: E402

MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
TEX_DIR = os.path.join(MOD, "textures")
WAD_PATH = os.path.join(HERE, "out", "maps", "midair.wad")


def _tile_noise(h, w, seed, scale_y=8, scale_x=8):
    """Seamless tileable smooth 2D noise in [0, 1]."""
    rng = np.random.RandomState(seed)
    grid = rng.rand(scale_y, scale_x)
    yy = np.linspace(0, scale_y, h, endpoint=False)
    xx = np.linspace(0, scale_x, w, endpoint=False)
    iy = np.floor(yy).astype(int)
    ix = np.floor(xx).astype(int)
    fy = (yy - iy)[:, None]
    fx = (xx - ix)[None, :]
    fy = fy * fy * (3.0 - 2.0 * fy)
    fx = fx * fx * (3.0 - 2.0 * fx)
    g00 = grid[iy[:, None] % scale_y, ix[None, :] % scale_x]
    g10 = grid[iy[:, None] % scale_y, (ix[None, :] + 1) % scale_x]
    g01 = grid[(iy[:, None] + 1) % scale_y, ix[None, :] % scale_x]
    g11 = grid[(iy[:, None] + 1) % scale_y, (ix[None, :] + 1) % scale_x]
    return (g00 * (1 - fx) + g10 * fx) * (1 - fy) + (g01 * (1 - fx) + g11 * fx) * fy


def _fbm_tile(h, w, seed):
    n = 0.50 * _tile_noise(h, w, seed, 8, 8)
    n += 0.28 * _tile_noise(h, w, seed + 1, 16, 16)
    n += 0.14 * _tile_noise(h, w, seed + 2, 32, 32)
    n += 0.08 * _tile_noise(h, w, seed + 3, 64, 64)
    return n


def _to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def make_floor():
    """512x512 dark brushed carbon-slate arena tile with crisp subtle nocturnal grid & corner micro-dots."""
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    grain = _fbm_tile(N, N, 101)
    fine = _tile_noise(N, N, 109, 128, 128)

    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 28.0 + 14.0 * grain + 5.0 * fine
    base[..., 1] = 34.0 + 16.0 * grain + 6.0 * fine
    base[..., 2] = 48.0 + 20.0 * grain + 7.0 * fine

    # 4x4 sub-tiles (128px each) + major border seam
    gx_maj = np.minimum(x % 256.0, 256.0 - (x % 256.0))
    gy_maj = np.minimum(y % 256.0, 256.0 - (y % 256.0))
    d_maj = np.minimum(gx_maj, gy_maj)

    gx_min = np.minimum(x % 128.0, 128.0 - (x % 128.0))
    gy_min = np.minimum(y % 128.0, 128.0 - (y % 128.0))
    d_min = np.minimum(gx_min, gy_min)

    groove_maj = np.exp(-(d_maj / 2.4) ** 2)
    bevel_maj = np.exp(-((d_maj - 4.5) / 2.2) ** 2)
    groove_min = np.exp(-(d_min / 1.6) ** 2)

    base = base * (1.0 - 0.52 * groove_maj[..., None] - 0.28 * groove_min[..., None])
    base = base + np.array([14.0, 20.0, 30.0]) * bevel_maj[..., None]

    # Subtle glowing intersection pips at major 256px corners (tiny nocturnal reference dots, never distracting)
    corner_d = np.hypot(gx_maj, gy_maj)
    pip = np.exp(-(corner_d / 4.2) ** 2)
    line_glow = np.exp(-(d_maj / 1.6) ** 2) * 0.22
    glow = np.zeros_like(base)
    glow += np.array([32.0, 145.0, 210.0]) * line_glow[..., None]
    glow += np.array([85.0, 225.0, 255.0]) * (pip * 0.85)[..., None]
    base += glow * 0.55
    return _to_img(base), _to_img(glow)


def make_ring_inlay(rgb_main, rgb_core, seed):
    """256x256 recessed luminous neon floor inlay texture."""
    N = 256
    grain = _fbm_tile(N, N, seed)
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    # Subtle pulse pattern along both axes so it looks rich from any radial angle
    grid_d = np.minimum(np.minimum(x % 64.0, 64.0 - (x % 64.0)), np.minimum(y % 64.0, 64.0 - (y % 64.0)))
    rib = 1.0 - 0.28 * np.exp(-(grid_d / 2.2) ** 2)

    c_main = np.array(rgb_main, dtype=np.float64)
    c_core = np.array(rgb_core, dtype=np.float64)
    mix = (0.55 + 0.45 * grain)[..., None] * rib[..., None]
    base = c_main * 0.48 + c_core * 0.42 * mix
    glow = (c_main * 0.55 + c_core * 0.45 * mix) * 0.88
    return _to_img(base), _to_img(glow)


def make_collar():
    """512x512 centered radial Launch Collar around the central hole (maps -272..+272 around origin).
    Hole is R = 192 -> normalized r_hole = 192 / 272 = 0.7059; outer collar edge r = 1.0.
    """
    N = 512
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
    nx = (xx + 0.5 - N / 2.0) / (N / 2.0)
    ny = (yy + 0.5 - N / 2.0) / (N / 2.0)
    r = np.hypot(nx, ny)
    ang = np.arctan2(ny, nx)
    grain = _fbm_tile(N, N, 205)

    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 34.0 + 14.0 * grain
    base[..., 1] = 40.0 + 16.0 * grain
    base[..., 2] = 56.0 + 20.0 * grain

    glow = np.zeros_like(base)

    # Inner blazing cyan rim right at the lip of the hole (r ~ 0.706 .. 0.755)
    lip = np.exp(-((r - 0.728) / 0.024) ** 2)
    glow += np.array([65.0, 235.0, 255.0]) * lip[..., None]

    # Mid collar: angled dark gunmetal & amber/gold caution ticks (r = 0.77 .. 0.92)
    in_band = np.clip((r - 0.765) / 0.015, 0.0, 1.0) * np.clip((0.925 - r) / 0.015, 0.0, 1.0)
    # 48 crisp radial tick / chevron segments matching N_SEG = 48
    spiral_phase = (ang / (2.0 * math.pi) * 24.0 + (r - 0.76) * 3.2) % 1.0
    stripe = np.clip((spiral_phase - 0.58) * 14.0, 0.0, 1.0) * np.clip((0.88 - spiral_phase) * 14.0, 0.0, 1.0)
    amber = np.array([255.0, 176.0, 52.0])
    base = base * (1.0 - 0.35 * in_band[..., None]) + amber * (in_band * stripe * 0.65)[..., None]
    glow += amber * (in_band * stripe * 0.78)[..., None]

    # Outer collar ring border (r ~ 0.965)
    outer_rim = np.exp(-((r - 0.965) / 0.018) ** 2)
    glow += np.array([45.0, 185.0, 255.0]) * (outer_rim * 0.75)[..., None]

    base += glow * 0.65
    return _to_img(base), _to_img(glow)


def make_pad():
    """512x512 centered radial Hyper-Jump Pad at the bottom of the central hole (-192..+192)."""
    N = 512
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
    nx = (xx + 0.5 - N / 2.0) / (N / 2.0)
    ny = (yy + 0.5 - N / 2.0) / (N / 2.0)
    r = np.hypot(nx, ny)
    ang = np.arctan2(ny, nx)
    grain = _fbm_tile(N, N, 307)

    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 18.0 + 10.0 * grain
    base[..., 1] = 26.0 + 14.0 * grain
    base[..., 2] = 44.0 + 18.0 * grain

    glow = np.zeros_like(base)

    # Radial turbine vanes (16 sleek curved plasma blades)
    vane_phase = (ang / (2.0 * math.pi) * 16.0 - r * 1.35) % 1.0
    vane = np.exp(-((vane_phase - 0.5) / 0.14) ** 2) * np.clip((r - 0.16) / 0.08, 0.0, 1.0) * np.clip((0.92 - r) / 0.08, 0.0, 1.0)
    glow += np.array([40.0, 185.0, 255.0]) * (vane * 0.62)[..., None]

    # Concentric high-energy accelerator rings
    for r0, w, col in (
        (0.24, 0.028, (255.0, 235.0, 150.0)),
        (0.46, 0.026, (70.0, 240.0, 255.0)),
        (0.68, 0.026, (185.0, 115.0, 255.0)),
        (0.88, 0.030, (65.0, 230.0, 255.0)),
    ):
        ring = np.exp(-((r - r0) / w) ** 2)
        glow += np.array(col) * ring[..., None]

    # Blazing white-cyan reactor core at (0, 0)
    core = np.exp(-(r / 0.19) ** 2)
    glow += np.array([210.0, 250.0, 255.0]) * (core * 1.15)[..., None]

    base = base + glow * 0.85
    return _to_img(base), _to_img(glow)


def make_shaft():
    """512x512 inner vertical wall of the central launch hole:
    dark ribbed gunmetal panels + glowing vertical plasma conduits + upward launch chevrons!
    Note: in Quake world Z up, v_px = -z / yscale + yoff, so smaller row index y = higher Z (upward!).
    """
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    grain = _fbm_tile(N, N, 401)

    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 22.0 + 12.0 * grain
    base[..., 1] = 28.0 + 14.0 * grain
    base[..., 2] = 44.0 + 18.0 * grain

    # Vertical panel ribs every 128 px
    px = x % 128.0
    seam = np.exp(-(np.minimum(px, 128.0 - px) / 2.5) ** 2)
    base *= (1.0 - 0.45 * seam[..., None])

    glow = np.zeros_like(base)

    # Vertical glowing cyan plasma conduit along each 128px panel edge (px ~ 12 / 116)
    cond = np.exp(-((px - 64.0) / 4.0) ** 2) * 0.0 + np.exp(-(np.minimum(px, 128.0 - px) / 3.2) ** 2)
    glow += np.array([55.0, 220.0, 255.0]) * (cond * 0.82)[..., None]

    # Upward-pointing glowing chevrons centered in each 128px column!
    # Apex points UP (smaller y): at center dx=0, apex is at smallest y; as |dx| grows, chevron legs go DOWN (+y).
    dx = np.abs(px - 64.0)  # 0 at panel center, 64 at edges
    in_col = np.clip((46.0 - dx) / 4.0, 0.0, 1.0)
    chev_y = (y - dx * 0.72) % 128.0
    chev1 = np.exp(-((chev_y - 48.0) / 6.5) ** 2) * in_col
    chev2 = np.exp(-((chev_y - 82.0) / 5.0) ** 2) * in_col
    glow += np.array([80.0, 240.0, 255.0]) * (chev1 * 0.95)[..., None]
    glow += np.array([185.0, 115.0, 255.0]) * (chev2 * 0.85)[..., None]

    # Horizontal ring bands
    hy = np.minimum(y % 128.0, 128.0 - (y % 128.0))
    hring = np.exp(-(hy / 2.5) ** 2)
    glow += np.array([45.0, 150.0, 230.0]) * (hring * 0.35)[..., None]

    base += glow * 0.75
    return _to_img(base), _to_img(glow)


def make_step():
    """512x512 outer terrace step deck."""
    N = 512
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    grain = _fbm_tile(N, N, 503)
    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 34.0 + 14.0 * grain
    base[..., 1] = 40.0 + 16.0 * grain
    base[..., 2] = 58.0 + 20.0 * grain

    gx = np.minimum(x % 128.0, 128.0 - (x % 128.0))
    gy = np.minimum(y % 128.0, 128.0 - (y % 128.0))
    d = np.minimum(gx, gy)
    base *= (1.0 - 0.38 * np.exp(-(d / 2.0) ** 2)[..., None])

    glow = np.zeros_like(base)
    glow += np.array([48.0, 130.0, 210.0]) * (np.exp(-(d / 1.5) ** 2) * 0.16)[..., None]
    base += glow * 0.5
    return _to_img(base), _to_img(glow)


def make_riser():
    """512x128 step riser with crisp luminous horizontal accent strip."""
    W, H = 512, 128
    y, x = np.mgrid[0:H, 0:W].astype(np.float64)
    grain = _fbm_tile(H, W, 607)
    base = np.zeros((H, W, 3), dtype=np.float64)
    base[..., 0] = 24.0 + 10.0 * grain
    base[..., 1] = 30.0 + 12.0 * grain
    base[..., 2] = 46.0 + 16.0 * grain

    strip = np.exp(-((y - 36.0) / 5.5) ** 2)
    glow = np.array([75.0, 215.0, 255.0]) * (strip * 0.88)[..., None]
    base += glow * 0.75
    return _to_img(base), _to_img(glow)


def make_wall():
    """512x256 curved perimeter parapet wall: dark architectural paneling + twin horizontal neon trim bands."""
    W, H = 512, 256
    y, x = np.mgrid[0:H, 0:W].astype(np.float64)
    grain = _fbm_tile(H, W, 709)
    base = np.zeros((H, W, 3), dtype=np.float64)
    base[..., 0] = 26.0 + 14.0 * grain
    base[..., 1] = 32.0 + 16.0 * grain
    base[..., 2] = 48.0 + 20.0 * grain

    # Architectural vertical seams every 128px
    gx = np.minimum(x % 128.0, 128.0 - (x % 128.0))
    base *= (1.0 - 0.42 * np.exp(-(gx / 2.4) ** 2)[..., None])

    # Recessed dark band in middle
    mid_recess = np.clip((y - 52.0) / 6.0, 0.0, 1.0) * np.clip((204.0 - y) / 6.0, 0.0, 1.0)
    base *= (1.0 - 0.22 * mid_recess[..., None])

    glow = np.zeros_like(base)
    # Upper electric-cyan neon band + lower violet-magenta neon band
    band_top = np.exp(-((y - 44.0) / 4.8) ** 2)
    band_bot = np.exp(-((y - 208.0) / 4.8) ** 2)
    glow += np.array([65.0, 228.0, 255.0]) * (band_top * 0.92)[..., None]
    glow += np.array([195.0, 95.0, 255.0]) * (band_bot * 0.86)[..., None]

    base += glow * 0.72
    return _to_img(base), _to_img(glow)


def make_pylon():
    """256x256 perimeter beacon floodlight sconce."""
    N = 256
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    grain = _fbm_tile(N, N, 811)
    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 30.0 + 10.0 * grain
    base[..., 1] = 34.0 + 12.0 * grain
    base[..., 2] = 50.0 + 16.0 * grain

    # Glowing vertical light bar in center of sconce
    dx = np.abs(x - N / 2.0)
    dy = np.abs(y - N / 2.0)
    lamp = np.clip((48.0 - dx) / 8.0, 0.0, 1.0) * np.clip((92.0 - dy) / 10.0, 0.0, 1.0)
    core = np.exp(-(dx / 22.0) ** 2) * np.clip((84.0 - dy) / 12.0, 0.0, 1.0)

    glow = np.array([255.0, 195.0, 120.0]) * (lamp * 0.55)[..., None] + np.array([220.0, 242.0, 255.0]) * (core * 0.75)[..., None]
    base = base * (1.0 - 0.5 * lamp[..., None]) + glow * 0.85
    return _to_img(base), _to_img(glow)


def make_outer():
    """256x256 exterior floating-colosseum rim texture (seen when flying 2400 units up looking down!)."""
    N = 256
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    grain = _fbm_tile(N, N, 919)
    base = np.zeros((N, N, 3), dtype=np.float64)
    base[..., 0] = 20.0 + 10.0 * grain
    base[..., 1] = 26.0 + 12.0 * grain
    base[..., 2] = 42.0 + 16.0 * grain

    b1 = np.exp(-((y - 36.0) / 5.0) ** 2)
    b2 = np.exp(-((y - 128.0) / 4.5) ** 2)
    glow = np.array([65.0, 220.0, 255.0]) * (b1 * 0.85)[..., None] + np.array([185.0, 95.0, 255.0]) * (b2 * 0.75)[..., None]
    base += glow * 0.75
    return _to_img(base), _to_img(glow)


def make_utility_solid(rgb):
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :] = rgb
    return Image.fromarray(arr, "RGB")


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(WAD_PATH), exist_ok=True)

    builders = {
        "ma_floor": make_floor,
        "ma_ring_c": lambda: make_ring_inlay((45, 210, 255), (170, 248, 255), 131),
        "ma_ring_m": lambda: make_ring_inlay((190, 85, 255), (245, 185, 255), 149),
        "ma_collar": make_collar,
        "ma_pad": make_pad,
        "ma_shaft": make_shaft,
        "ma_step": make_step,
        "ma_riser": make_riser,
        "ma_wall": make_wall,
        "ma_pylon": make_pylon,
        "ma_outer": make_outer,
    }

    wad_tex = {}
    for name, fn in builders.items():
        assert len(name) <= 15, name
        im, glow = fn()
        im.save(os.path.join(TEX_DIR, f"{name}.png"))
        glow.save(os.path.join(TEX_DIR, f"{name}_glow.png"))
        # Downsampled 4x (multiple of 16) for WAD2 miptex lightmap bounce colors
        sw = max(16, (im.width // 2 // 16) * 16)
        sh = max(16, (im.height // 2 // 16) * 16)
        wad_tex[name] = im.resize((sw, sh), Image.LANCZOS)

    wad_tex["sky1"] = make_utility_solid((16, 28, 64))
    wad_tex["clip"] = make_utility_solid((160, 64, 64))

    write_wad(WAD_PATH, wad_tex)
    print(f"wrote {WAD_PATH} ({len(wad_tex)} WAD textures, {len(builders)} HD + _glow PNG pairs)")


if __name__ == "__main__":
    main()
