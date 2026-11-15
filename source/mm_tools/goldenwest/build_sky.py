"""Procedural sunny San Joaquin Valley / Bakersfield skybox for Golden West Casino & S Union Ave.

Generates:
  - DarkPlaces cube faces: ``gfx/env/gwsky_{bk,dn,ft,lf,rt,up}.png``
  - Three.js WebGL cube faces via ``build_web_sky(out_sky_dir, size=512)``

Sun direction aligns cleanly with worldspawn ``_sunlight_mangle`` (default ``212 -58 0`` ->
sun rays travel SW-down at yaw 212 deg, pitch -58 deg, so the solar disc sits high ENE at
azimuth +32 deg, elevation +58 deg).
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_THIS_DIR = Path(__file__).resolve().parent
_MM_TOOLS = _THIS_DIR.parent
ROOT = _MM_TOOLS.parent.parent

for _p in (str(_THIS_DIR), str(_MM_TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from gw_lib import SUN_AZIMUTH_DEG, SUN_ELEVATION_DEG  # type: ignore
except Exception:
    # Matches _sunlight_mangle "212 -58 0": sun opposite ray vector -> az=32 deg (ENE), el=58 deg
    SUN_AZIMUTH_DEG = 32.0
    SUN_ELEVATION_DEG = 58.0

SKY_PREFIX = "gwsky_"


def _value_noise_3d(x: np.ndarray, y: np.ndarray, z: np.ndarray, seed: int) -> np.ndarray:
    """Smooth trilinear value noise on an arbitrary 3D coordinate array."""
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    iz = np.floor(z).astype(np.int64)
    fx = x - ix
    fy = y - iy
    fz = z - iz
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    uz = fz * fz * (3.0 - 2.0 * fz)

    def h(ox: int, oy: int, oz: int) -> np.ndarray:
        n = (
            (ix + ox).astype(np.uint64) * np.uint64(374761393)
            + (iy + oy).astype(np.uint64) * np.uint64(668265263)
            + (iz + oz).astype(np.uint64) * np.uint64(1274126177)
            + np.uint64(seed) * np.uint64(1442695041)
        ) & np.uint64(0xFFFFFFFF)
        n = ((n ^ (n >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xFFFFFFFF)
        n = n ^ (n >> np.uint64(16))
        return (n & np.uint64(0xFFFF)).astype(np.float32) / 65535.0

    c000 = h(0, 0, 0)
    c100 = h(1, 0, 0)
    c010 = h(0, 1, 0)
    c110 = h(1, 1, 0)
    c001 = h(0, 0, 1)
    c101 = h(1, 0, 1)
    c011 = h(0, 1, 1)
    c111 = h(1, 1, 1)

    c00 = c000 * (1.0 - ux) + c100 * ux
    c10 = c010 * (1.0 - ux) + c110 * ux
    c01 = c001 * (1.0 - ux) + c101 * ux
    c11 = c011 * (1.0 - ux) + c111 * ux
    c0 = c00 * (1.0 - uy) + c10 * uy
    c1 = c01 * (1.0 - uy) + c11 * uy
    return c0 * (1.0 - uz) + c1 * uz


def _fbm_3d(x: np.ndarray, y: np.ndarray, z: np.ndarray, octaves: int = 5, seed: int = 109) -> np.ndarray:
    """Multi-octave 3D fractional Brownian motion."""
    total = np.zeros_like(x, dtype=np.float32)
    amp = 0.5
    freq = 1.0
    norm = 0.0
    for oct_i in range(octaves):
        total += amp * _value_noise_3d(x * freq, y * freq, z * freq, seed + oct_i * 41)
        norm += amp
        amp *= 0.5
        freq *= 2.07
    return total / max(norm, 1e-6)


def _sun_vector() -> tuple[float, float, float]:
    az = math.radians(SUN_AZIMUTH_DEG)
    el = math.radians(SUN_ELEVATION_DEG)
    return (
        math.cos(el) * math.cos(az),
        math.cos(el) * math.sin(az),
        math.sin(el),
    )


def render_sky_dirs(dirs: np.ndarray) -> np.ndarray:
    """Evaluate sunny Bakersfield sky radiance (H, W, 3) float32 in [0, 255].

    ``dirs`` has world axes (East +X, North +Y, Up +Z).
    """
    norm = np.linalg.norm(dirs, axis=-1, keepdims=True)
    d = dirs / np.maximum(norm, 1e-6)
    dx = d[..., 0]
    dy = d[..., 1]
    dz = d[..., 2]

    sx, sy, sz = _sun_vector()
    sun_dot = np.clip(dx * sx + dy * sy + dz * sz, -1.0, 1.0)

    # Azimuthal proximity to sun for Mie horizon warmth
    az = np.arctan2(dy, dx)
    sun_az = math.radians(SUN_AZIMUTH_DEG)
    az_sun_prox = np.clip(0.5 + 0.5 * np.cos(az - sun_az), 0.0, 1.0)

    z_up = np.clip(dz, 0.0, 1.0)

    # Clear San Joaquin Valley blue gradient: crisp cobalt zenith -> sunlit pale blue -> warm valley haze
    col_zenith = np.array([56.0, 126.0, 214.0], dtype=np.float32)
    col_mid = np.array([118.0, 180.0, 236.0], dtype=np.float32)
    col_low = np.array([184.0, 214.0, 234.0], dtype=np.float32)
    col_haze = np.array([224.0, 212.0, 194.0], dtype=np.float32)

    t_mid = np.clip(z_up / 0.42, 0.0, 1.0)[..., None] ** 0.72
    t_zen = np.clip((z_up - 0.30) / 0.70, 0.0, 1.0)[..., None] ** 0.90
    sky_col = col_low * (1.0 - t_mid) + col_mid * t_mid
    sky_col = sky_col * (1.0 - t_zen) + col_zenith * t_zen

    # Subtle warm Valley inversion/dust haze hugging z < 0.17, slightly warmer toward sun
    haze_t = np.exp(-z_up / 0.075) * (0.48 + 0.34 * az_sun_prox)
    warm_haze = col_haze + np.array([14.0, 6.0, -8.0], dtype=np.float32) * az_sun_prox[..., None]
    sky_col = sky_col * (1.0 - haze_t[..., None]) + warm_haze * haze_t[..., None]

    # Broad solar Rayleigh/Mie scattering halo + tight golden aureole + crisp solar disc.
    # Blend toward warm white/gold instead of pure additive so Blue never clips into cyan first.
    halo_wide = np.clip(sun_dot, 0.0, 1.0) ** 4.5
    halo_aureole = np.clip(sun_dot, 0.0, 1.0) ** 34.0
    halo_core = np.clip(sun_dot, 0.0, 1.0) ** 240.0
    sun_disc = np.clip((sun_dot - 0.99945) / (0.99975 - 0.99945), 0.0, 1.0)
    sun_vis = np.clip((dz + 0.02) / 0.06, 0.0, 1.0)

    warm_glow_col = np.array([242.0, 226.0, 198.0], dtype=np.float32)
    aureole_col = np.array([255.0, 244.0, 222.0], dtype=np.float32)
    disc_col = np.array([255.0, 253.0, 246.0], dtype=np.float32)

    w_wide = (0.34 * halo_wide * sun_vis)[..., None]
    w_aur = np.clip(0.85 * halo_aureole * sun_vis, 0.0, 1.0)[..., None]
    w_core = np.clip((0.92 * halo_core + sun_disc) * sun_vis, 0.0, 1.0)[..., None]

    sky_col = sky_col * (1.0 - w_wide) + warm_glow_col * w_wide
    sky_col = sky_col * (1.0 - w_aur) + aureole_col * w_aur
    sky_col = sky_col * (1.0 - w_core) + disc_col * w_core

    # Very delicate distant Sierra Nevada / Tehachapi ridge silhouette in the eastern & southern horizon
    ridge_east = np.clip(dx * 0.85 - dy * 0.52, 0.0, 1.0)
    ridge_south = np.clip(-dy * 0.90 + dx * 0.25, 0.0, 1.0)
    ridge_weight = np.maximum(ridge_east * 0.95, ridge_south * 0.72)
    ridge_n1 = 0.5 + 0.5 * np.sin(az * 7.0 + 0.9) * np.cos(az * 13.0 - 0.4)
    ridge_n2 = 0.5 + 0.5 * np.sin(az * 23.0 - 1.3)
    ridge_top = (0.006 + 0.019 * ridge_weight * (0.45 * ridge_n1 + 0.55 * ridge_n2))
    ridge_mask = np.clip((ridge_top - dz) / 0.0045, 0.0, 1.0) * np.clip((dz + 0.004) / 0.006, 0.0, 1.0)
    ridge_col = np.array([162.0, 174.0, 196.0], dtype=np.float32)
    sky_col = sky_col * (1.0 - 0.55 * ridge_mask[..., None]) + ridge_col * (0.55 * ridge_mask[..., None])

    # Delicate sparse high-altitude San Joaquin cirrus wisps (kept airy so sky stays clearly sunny blue)
    above = np.clip((dz - 0.05) / 0.14, 0.0, 1.0)
    sx_p = dx * 2.6 + dy * 1.4
    sy_p = -dy * 1.8 + dz * 4.0
    sz_p = dz * 2.8 - dx * 0.9
    n_broad = _fbm_3d(sx_p * 0.9 + 3.1, sy_p * 0.9 + 7.4, sz_p * 0.9, octaves=4, seed=211)
    n_streak = _fbm_3d(sx_p * 3.1 + n_broad * 1.6, sy_p * 1.5, sz_p * 2.6, octaves=4, seed=509)
    cirrus = np.clip((n_broad * 0.58 + n_streak * 0.42 - 0.62) / 0.22, 0.0, 1.0)
    cirrus *= above * (1.0 - 0.45 * z_up)
    # Keep solar disc unobstructed
    cirrus *= 1.0 - 0.85 * np.clip((sun_dot - 0.985) / 0.015, 0.0, 1.0)
    cirrus_col = np.array([236.0, 238.0, 240.0], dtype=np.float32) + np.array([12.0, 8.0, 2.0], dtype=np.float32) * halo_wide[..., None]
    sky_col = sky_col * (1.0 - 0.34 * cirrus[..., None]) + cirrus_col * (0.34 * cirrus[..., None])

    # Below-horizon ground apron (warm Central Valley earth so bottom reflections never turn cold black)
    gnd_t = np.clip(-dz / 0.55, 0.0, 1.0)[..., None]
    gnd_hor = np.array([188.0, 174.0, 152.0], dtype=np.float32)
    gnd_nadir = np.array([134.0, 120.0, 102.0], dtype=np.float32)
    gnd_col = gnd_hor * (1.0 - gnd_t) + gnd_nadir * gnd_t
    horiz_blend = np.clip((dz + 0.014) / 0.028, 0.0, 1.0)[..., None]
    rgb = gnd_col * (1.0 - horiz_blend) + sky_col * horiz_blend

    return np.clip(rgb, 0.0, 255.0)


def build_dp_sky(size: int = 512, write_tga: bool = False) -> list[Path]:
    """Generate DarkPlaces skybox cube faces ``gfx/env/gwsky_{rt,lf,ft,bk,up,dn}.png``."""
    out_dir = ROOT / "gfx" / "env"
    out_dir.mkdir(parents=True, exist_ok=True)

    lin = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    u, v = np.meshgrid(lin, -lin)  # u left->right, v top->bottom (+1 to -1)
    one = np.ones_like(u)

    dp_faces = {
        "rt": np.stack([one, -u, v], axis=-1),
        "ft": np.stack([-u, -one, v], axis=-1),
        "lf": np.stack([-one, u, v], axis=-1),
        "bk": np.stack([u, one, v], axis=-1),
        "up": np.flipud(np.stack([v, -u, one], axis=-1)),
        "dn": np.stack([-v, -u, -one], axis=-1),
    }

    written: list[Path] = []
    for suffix, dirs in dp_faces.items():
        # Slight headroom scale (0.94) prevents DP bright daylight clipping
        rgb = np.clip(render_sky_dirs(dirs) * 0.94, 0.0, 255.0).astype(np.uint8)
        im = Image.fromarray(rgb, mode="RGB")
        png_path = out_dir / f"{SKY_PREFIX}{suffix}.png"
        im.save(png_path, format="PNG", optimize=True)
        written.append(png_path)
        tga_path = out_dir / f"{SKY_PREFIX}{suffix}.tga"
        if write_tga:
            im.save(tga_path, format="TGA")
            written.append(tga_path)
        elif tga_path.exists():
            tga_path.unlink()

    print(
        f"[build_sky] Wrote {len(written)} DarkPlaces sky files ({SKY_PREFIX}*) "
        f"az={SUN_AZIMUTH_DEG:.1f} el={SUN_ELEVATION_DEG:.1f} -> {out_dir}"
    )
    return written


def build_web_sky(out_sky_dir: str | Path, size: int = 512) -> list[Path]:
    """Generate WebGL Three.js CubeTexture faces ``{rt,lf,up,dn,bk,ft}.jpg``."""
    out_dir = Path(out_sky_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lin = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    u, v = np.meshgrid(lin, lin)
    one = np.ones_like(u)

    gl_faces = {
        "rt": (one, -v, -u),
        "lf": (-one, -v, u),
        "up": (u, one, v),
        "dn": (u, -one, -v),
        "bk": (u, -v, one),
        "ft": (-u, -v, -one),
    }

    written: list[Path] = []
    for name, (rx, ry, rz) in gl_faces.items():
        # Match web viewer -90 deg X rotation: world = (-rx, -rz, ry)
        dirs = np.stack([-rx, -rz, ry], axis=-1)
        rgb = np.clip(render_sky_dirs(dirs), 0.0, 255.0).astype(np.uint8)
        out_path = out_dir / f"{name}.jpg"
        Image.fromarray(rgb, mode="RGB").save(out_path, format="JPEG", quality=92)
        written.append(out_path)

    print(f"[build_sky] Wrote 6 Three.js web skybox faces -> {out_dir}")
    return written


def main() -> None:
    build_dp_sky(size=512, write_tga=False)


if __name__ == "__main__":
    main()
