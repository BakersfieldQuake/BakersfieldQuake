#!/usr/bin/env python3
"""Build Cyrax Green Net textures and 3D MD3 models (cyrax_net.md3 + cyrax_wrap.md3).

Uses the uploaded classic MK3 Cyrax green net sprite as source:
  1. source/mm_tools/cyrax/assets/tex/cyrax_net.png
     Cleanly keyed, neon-green enhanced, RGB edge-bled flying net texture.
  2. source/mm_tools/cyrax/assets/tex/cyrax_wrap.png
     Seamless tiled MK3 neon-green net cage texture matching the exact MK3
     strand thickness, bright knot highlights, and crisp transparent holes.
  3. progs/cyrax_net.md3 (8 animated pulsing/spinning frames)
     3D billowing scoop + crossed energy-web projectile mesh.
  4. progs/cyrax_wrap.md3 (8 animated pulsing/constricting/rotating frames)
     3D barrel-shaped cylindrical net cage sized to wrap a player/bot hull
     (radius ~22u, z=-24..+34) and scale cleanly onto Winged John Bird / Milky Grenade.

Uses only Python stdlib + numpy + Pillow + md3lib.
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
TEX_DIR = HERE / "assets" / "tex"

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib  # noqa: E402

DEFAULT_SRC_NET = Path(
    "/home/computer/.gemini/antigravity/brain/c7c79a0e-f4b1-42bb-8730-fe3878e1c7bd/"
    ".user_uploaded/media_1795676941626_746d7ad8.png"
)


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vnorm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def _rot_x(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def _rot_z(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def _bleed_green_edges(rgba: np.ndarray, passes: int = 4) -> np.ndarray:
    """Propagate foreground RGB into alpha==0 neighbors to eliminate filter seams."""
    out = rgba.copy()
    mask = out[..., 3] >= 128
    if not np.any(mask):
        return out
    rgb = out[..., :3].astype(np.float32)
    valid = mask.astype(np.float32)

    def _box(arr):
        p = np.pad(arr, ((1, 1), (1, 1)), mode="edge")
        h, w = arr.shape
        return (
            p[0:h, 0:w] + p[0:h, 1:w + 1] + p[0:h, 2:w + 2]
            + p[1:h + 1, 0:w] + p[1:h + 1, 1:w + 1] + p[1:h + 1, 2:w + 2]
            + p[2:h + 2, 0:w] + p[2:h + 2, 1:w + 1] + p[2:h + 2, 2:w + 2]
        )

    for _ in range(passes):
        ws = _box(valid)
        need = (valid < 0.5) & (ws > 0.5)
        if not np.any(need):
            break
        for c in range(3):
            cs = _box(rgb[..., c] * valid)
            rgb[..., c][need] = cs[need] / ws[need]
        valid[need] = 1.0
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    return out


def key_and_enhance_net(src_path: Path) -> np.ndarray:
    """Key any white/pale pixels if present, keep crisp MK3 pixel grid, boost neon-green highlights."""
    raw = np.asarray(Image.open(src_path).convert("RGBA"))
    rgb = raw[..., :3].astype(np.float32)
    a = raw[..., 3].astype(np.float32)

    # Key out any near-white background if source had white instead of alpha
    lo = rgb.min(axis=2)
    hi = rgb.max(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    is_white = (lo > 215.0) & (sat < 0.14)
    a[is_white] = 0.0

    # Boost MK3 neon green contrast so strands pop against dark & bright maps
    g = rgb[..., 1]
    fg = a > 128
    g_boost = np.clip((g / 255.0) ** 0.78 * 255.0 + 18.0, 0.0, 255.0)
    hot = np.clip((g_boost - 195.0) / 60.0, 0.0, 1.0)
    out = np.zeros_like(raw)
    out[..., 0] = np.where(fg, np.round(hot * 110.0), 0).astype(np.uint8)
    out[..., 1] = np.where(fg, np.round(g_boost), 0).astype(np.uint8)
    out[..., 2] = np.where(fg, np.round(hot * 90.0), 0).astype(np.uint8)
    out[..., 3] = np.where(fg, 255, 0).astype(np.uint8)

    # Upscale 2x nearest-neighbor onto square-friendly 146x318 -> 256x256 padded or crisp 146x318
    im = Image.fromarray(out, "RGBA").resize((out.shape[1] * 2, out.shape[0] * 2), Image.Resampling.NEAREST)
    return _bleed_green_edges(np.asarray(im, dtype=np.uint8), passes=3)


def make_seamless_wrap_net(size: int = 256) -> np.ndarray:
    """Synthesize a crisp, seamless 256x256 MK3-style green net texture for cylindrical wrapping."""
    rng = np.random.default_rng(31337)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    # Draw tiled diagonal/diamond-curved MK3 net strands (4x4 cells per 256px)
    cells = 4
    step = size // cells
    for i in range(-1, cells + 2):
        # Horizontal-ish wavy cords
        y_base = i * step
        pts_h = []
        for x in range(0, size + 8, 8):
            ang = 2.0 * math.pi * (x / float(size)) * cells
            y = y_base + 5.0 * math.sin(ang + i * 0.7)
            pts_h.append((x, y))
        drw.line(pts_h, fill=(0, 120, 0, 255), width=11)
        drw.line(pts_h, fill=(25, 225, 35, 255), width=6)
        drw.line(pts_h, fill=(130, 255, 120, 255), width=2)

        # Vertical-ish cords
        x_base = i * step
        pts_v = []
        for y in range(0, size + 8, 8):
            ang = 2.0 * math.pi * (y / float(size)) * cells
            x = x_base + 5.0 * math.sin(ang + i * 0.9)
            pts_v.append((x, y))
        drw.line(pts_v, fill=(0, 120, 0, 255), width=11)
        drw.line(pts_v, fill=(25, 225, 35, 255), width=6)
        drw.line(pts_v, fill=(130, 255, 120, 255), width=2)

    # Bright glowing MK3 energy knots at intersections
    for iy in range(cells + 1):
        for ix in range(cells + 1):
            kx = (ix * step) % size
            ky = (iy * step) % size
            for ox in (-size, 0, size):
                for oy in (-size, 0, size):
                    cx, cy = kx + ox, ky + oy
                    if -16 <= cx <= size + 16 and -16 <= cy <= size + 16:
                        drw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(40, 245, 65, 255))
                        drw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(195, 255, 185, 255))

    # Quantize slightly to crisp 2x2 pixel blocks + subtle scanline shimmer for authentic MK3 feel
    arr = np.asarray(im, dtype=np.uint8)
    small = Image.fromarray(arr, "RGBA").resize((size // 2, size // 2), Image.Resampling.NEAREST)
    arr = np.array(small.resize((size, size), Image.Resampling.NEAREST), dtype=np.uint8)

    fg = arr[..., 3] > 128
    noise = rng.integers(-18, 22, size=(size, size))
    g = np.clip(arr[..., 1].astype(np.int16) + noise, 45, 255)
    arr[..., 1] = np.where(fg, g, 0).astype(np.uint8)
    arr[..., 3] = np.where(fg, 255, 0).astype(np.uint8)
    return _bleed_green_edges(arr, passes=3)


def generate_net_textures(src_net: Path = DEFAULT_SRC_NET, out_dir: Path = TEX_DIR) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    net_rgba = key_and_enhance_net(src_net)
    wrap_rgba = make_seamless_wrap_net(256)

    p_net = out_dir / "cyrax_net.png"
    p_wrap = out_dir / "cyrax_wrap.png"
    Image.fromarray(net_rgba, "RGBA").save(p_net, format="PNG", compress_level=9, optimize=False)
    Image.fromarray(wrap_rgba, "RGBA").save(p_wrap, format="PNG", compress_level=9, optimize=False)
    return p_net, p_wrap


def _build_grid_patch_tris(nx: int, nz: int) -> list[tuple[int, int, int]]:
    tris = []
    stride = nx + 1
    for iz in range(nz):
        for ix in range(nx):
            i0 = iz * stride + ix
            i1 = i0 + 1
            i2 = i0 + stride + 1
            i3 = i0 + stride
            tris.append((i0, i1, i2))
            tris.append((i0, i2, i3))
    return tris


def build_cyrax_net_md3_bytes() -> bytes:
    """Build 8-frame flying projectile MD3 (progs/cyrax_net.md3).

    ONE single huge, upright, non-spinning 3D parabolic elliptical MK3 green net
    dome oriented perpendicular to +X (in the Y-Z plane!):
      - Width across Y: ~72u (-36..+36)
      - Height across Z: ~92u (-46..+46)
      - Depth along X: ~30u (billowing forward along +X away from the shooter)
    Uses seamless MK3 grid UVs (progs/cyrax_wrap) and gently billows/pulses
    across 8 frames with ZERO spin.
    """
    n_rings = 8
    n_seg = 24
    half_w = 36.0   # 72u wide across Y
    half_h = 46.0   # 92u tall across Z
    depth = 30.0    # 30u deep along X

    # Vertex layout: 1 center apex + n_rings * (n_seg + 1) ring verts (seamless UV seam)
    verts_uv: list[tuple[float, float]] = [(0.75, 0.90)]
    for ir in range(1, n_rings + 1):
        rf = ir / float(n_rings)
        for iseg in range(n_seg + 1):
            ang = (iseg / float(n_seg)) * 2.0 * math.pi
            # Elliptical planar UVs mapped onto seamless 256x256 MK3 grid (1.5x1.8 tiles)
            u = 0.75 + 0.75 * rf * math.cos(ang)
            v = 0.90 + 0.90 * rf * math.sin(ang)
            verts_uv.append((u, v))

    tris: list[tuple[int, int, int]] = []
    stride = n_seg + 1
    # Inner fan around center apex (index 0)
    for iseg in range(n_seg):
        i1 = 1 + iseg
        i2 = 1 + iseg + 1
        tris.append((0, i2, i1))
    # Concentric quad rings
    for ir in range(1, n_rings):
        r0 = 1 + (ir - 1) * stride
        r1 = 1 + ir * stride
        for iseg in range(n_seg):
            a0 = r0 + iseg
            a1 = a0 + 1
            b0 = r1 + iseg
            b1 = b0 + 1
            tris.append((a0, a1, b1))
            tris.append((a0, b1, b0))

    frames = []
    for fi in range(8):
        t = fi / 8.0
        pulse = 1.0 + 0.05 * math.sin(2.0 * math.pi * t)
        verts: list[tuple[float, float, float]] = []
        norms: list[tuple[float, float, float]] = []

        # Center apex: billows forward (+X) away from the shooter
        apex_x = 18.0 + 2.5 * math.sin(2.0 * math.pi * t)
        verts.append((apex_x, 0.0, 0.0))
        norms.append((1.0, 0.0, 0.0))

        for ir in range(1, n_rings + 1):
            rf = ir / float(n_rings)
            for iseg in range(n_seg + 1):
                ang = (iseg / float(n_seg)) * 2.0 * math.pi
                ca, sa = math.cos(ang), math.sin(ang)
                y = rf * half_w * pulse * ca
                z = rf * half_h * pulse * sa
                # Parabolic dome: forward (+X) at center, sweeping back 30u to trailing rim (-X)
                shimmer = 2.0 * math.sin(2.0 * math.pi * (t + 0.65 * rf) + 2.0 * ang) * rf
                x = apex_x - depth * (rf ** 1.75) + shimmer
                verts.append((x, y, z))
                norms.append(_vnorm((1.0, 0.55 * rf * ca, 0.45 * rf * sa)))

        frames.append((verts, norms))

    surf = dict(
        name="net_sheet",
        shader="progs/cyrax_wrap",
        tris=tris,
        st=verts_uv,
        frames=frames,
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cyrax_net.md3"
        md3lib.write(str(p), dict(name="cyrax_net", surfaces=[surf], nframes=8))
        return p.read_bytes()


def build_cyrax_wrap_md3_bytes() -> bytes:
    """Build 8-frame 3D cylindrical/barrel wrapped net cage (progs/cyrax_wrap.md3).

    Sized to wrap cleanly around a player/bot (-24..+34 Z, radius ~22u) with
    pulsing constriction and slow helical rotation across 8 frames.
    """
    n_seg = 16
    n_rings = 6
    z_min, z_max = -24.0, 34.0
    r_mid = 22.5
    r_end = 15.0

    st = []
    for ir in range(n_rings + 1):
        v = ir / float(n_rings) * 1.5
        for iseg in range(n_seg + 1):
            u = iseg / float(n_seg) * 2.0
            st.append((u, v))

    tris = []
    stride = n_seg + 1
    for ir in range(n_rings):
        for iseg in range(n_seg):
            i0 = ir * stride + iseg
            i1 = i0 + 1
            i2 = i0 + stride + 1
            i3 = i0 + stride
            tris.append((i0, i1, i2))
            tris.append((i0, i2, i3))

    frames = []
    for fi in range(8):
        t = fi / 8.0
        pulse = 1.0 + 0.08 * math.sin(2.0 * math.pi * t)
        twist_base = fi * (45.0 / 8.0)  # continuous 45 deg rotation across loop (tiles every 22.5 deg * 2)
        verts = []
        norms = []
        for ir in range(n_rings + 1):
            vf = ir / float(n_rings)
            z = z_min + (z_max - z_min) * vf
            # Barrel curve: wider at torso/midsection, cinched at feet and head
            arch = math.sin(vf * math.pi)
            ring_r = (r_end + (r_mid - r_end) * (arch ** 0.72)) * pulse
            ring_r += 0.9 * math.sin(2.0 * math.pi * (t + vf * 1.5))
            helical = twist_base + 10.0 * math.sin(vf * math.pi + 2.0 * math.pi * t)
            for iseg in range(n_seg + 1):
                ang = math.radians(helical) + (iseg / float(n_seg)) * 2.0 * math.pi
                cx, cy = math.cos(ang), math.sin(ang)
                verts.append((cx * ring_r, cy * ring_r, z))
                norms.append(_vnorm((cx, cy, (0.5 - vf) * 0.35)))
        frames.append((verts, norms))

    surf = dict(
        name="wrap_cage",
        shader="progs/cyrax_wrap",
        tris=tris,
        st=st,
        frames=frames,
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cyrax_wrap.md3"
        md3lib.write(str(p), dict(name="cyrax_wrap", surfaces=[surf], nframes=8))
        return p.read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC_NET, help="Source MK3 net PNG")
    ap.add_argument("--out-dir", type=Path, default=TEX_DIR, help="Output texture directory")
    args = ap.parse_args()
    p_net, p_wrap = generate_net_textures(args.src, args.out_dir)
    net_b = build_cyrax_net_md3_bytes()
    wrap_b = build_cyrax_wrap_md3_bytes()
    print(f"Generated {p_net.name} & {p_wrap.name}; net.md3={len(net_b)}B, wrap.md3={len(wrap_b)}B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
