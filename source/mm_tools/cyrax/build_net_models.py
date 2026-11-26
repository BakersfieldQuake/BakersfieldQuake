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

    Two intersecting, softly billowing 3D curved net sheets oriented along +X
    (forward flight direction) using progs/cyrax_net.png, spinning & pulsing across 8 frames.
    """
    nx, nz = 6, 8
    tris = _build_grid_patch_tris(nx, nz)
    st = []
    for iz in range(nz + 1):
        v = 1.0 - iz / float(nz)
        for ix in range(nx + 1):
            u = ix / float(nx)
            st.append((u, v))

    def make_patch_frames(roll_offset: float) -> list[tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]]:
        frames = []
        for fi in range(8):
            t = fi / 8.0
            pulse = 1.0 + 0.14 * math.sin(2.0 * math.pi * t)
            spin_deg = roll_offset + fi * (360.0 / 8.0) * 0.5
            verts = []
            norms = []
            for iz in range(nz + 1):
                vz = (iz / float(nz) - 0.5) * 34.0 * pulse
                for ix in range(nx + 1):
                    ux = (ix / float(nx) - 0.5) * 20.0 * pulse
                    # Parabolic scoop: leading edge forward (+X), trailing skirt behind (-X)
                    # Note the MK3 net image curves toward +u (right edge of PNG)
                    scoop = (1.0 - (vz / (18.5 * pulse)) ** 2) * 8.0 + (ux + 10.0) * 0.75
                    p = (scoop * 0.65, ux * 0.65, vz)
                    p = _rot_x(p, spin_deg)
                    # Ripple wave
                    ripple = 1.4 * math.sin(2.0 * math.pi * (t + iz / float(nz)))
                    p = (p[0] + ripple, p[1], p[2])
                    verts.append(p)
                    norms.append(_vnorm(_rot_x((1.0, 0.1, 0.0), spin_deg)))
            frames.append((verts, norms))
        return frames

    surf_a = dict(
        name="net_sheet_a",
        shader="progs/cyrax_net",
        tris=tris,
        st=st,
        frames=make_patch_frames(0.0),
    )
    surf_b = dict(
        name="net_sheet_b",
        shader="progs/cyrax_net",
        tris=tris,
        st=st,
        frames=make_patch_frames(90.0),
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cyrax_net.md3"
        md3lib.write(str(p), dict(name="cyrax_net", surfaces=[surf_a, surf_b], nframes=8))
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
