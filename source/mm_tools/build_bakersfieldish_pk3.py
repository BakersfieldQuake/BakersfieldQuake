"""Builds zz_bakersfieldish.pk3: reproducible overlay PK3 for Bakersfield-ish destructible debris.

Usage:
  python -I source/mm_tools/build_bakersfieldish_pk3.py [output_pk3] [--verify-repro]

Generates 4 chiseled, weathered 3D concrete/brick/stucco/rebar boulder & slab MD3 models
(progs/bako_boulder1..4.md3) plus crisp 256x256 procedural textures (progs/bako_boulder1..4.png,
progs/bako_rebar.png) inside a temporary directory and writes a deterministic, reproducible PK3
at BakersfieldQuake/zz_bakersfieldish.pk3 (zero loose asset files left in the mod folder).
"""
import argparse
import hashlib
import math
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_OUT = REPO_ROOT / "zz_bakersfieldish.pk3"
ASSETS_DIR = HERE / "bakersfieldish_assets"

MINIMAP_BOUNDS_TXT = b"-6360.00 -330.00 8796.80\n"
MINIMAP_SHADER_TXT = (
    b"gfx/minimap/bakersfieldish\n"
    b"{\n"
    b"\tnomipmaps\n"
    b"\tnopicmip\n"
    b"\tcull none\n"
    b"\t{\n"
    b"\t\tclampmap gfx/minimap/bakersfieldish.png\n"
    b"\t\tblendfunc blend\n"
    b"\t\trgbGen vertex\n"
    b"\t\talphaGen vertex\n"
    b"\t}\n"
    b"}\n"
)

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import md3lib  # noqa: E402

STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
FIXED_EXT_ATTR = 0o644 << 16


# ---------------------------------------------------------------------------
# Deterministic Procedural Textures (256x256 RGB PNG)
# ---------------------------------------------------------------------------

def _value_noise(h: int, w: int, grid: int, rng: np.random.Generator) -> np.ndarray:
    small = rng.random((grid, grid), dtype=np.float32)
    ys = np.linspace(0, grid, h, endpoint=False, dtype=np.float32)
    xs = np.linspace(0, grid, w, endpoint=False, dtype=np.float32)
    y0 = np.floor(ys).astype(np.int32) % grid
    x0 = np.floor(xs).astype(np.int32) % grid
    y1 = (y0 + 1) % grid
    x1 = (x0 + 1) % grid
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    fy = fy * fy * (3.0 - 2.0 * fy)
    fx = fx * fx * (3.0 - 2.0 * fx)
    v00 = small[np.ix_(y0, x0)]
    v10 = small[np.ix_(y1, x0)]
    v01 = small[np.ix_(y0, x1)]
    v11 = small[np.ix_(y1, x1)]
    return (v00 * (1.0 - fx) + v01 * fx) * (1.0 - fy) + (v10 * (1.0 - fx) + v11 * fx) * fy


def _fbm(size: int, rng: np.random.Generator, octaves=(4, 8, 16, 32, 64)) -> np.ndarray:
    acc = np.zeros((size, size), dtype=np.float32)
    w_sum = 0.0
    amp = 1.0
    for g in octaves:
        acc += amp * _value_noise(size, size, g, rng)
        w_sum += amp
        amp *= 0.52
    return acc / w_sum


def _add_cracks(img: np.ndarray, rng: np.random.Generator, n_cracks: int = 10, dark: float = 0.42) -> None:
    h, w, _ = img.shape
    for _ in range(n_cracks):
        x = float(rng.uniform(0, w))
        y = float(rng.uniform(0, h))
        ang = float(rng.uniform(0, 2.0 * math.pi))
        steps = int(rng.integers(24, 64))
        for _s in range(steps):
            ang += float(rng.uniform(-0.35, 0.35))
            x = (x + math.cos(ang) * 2.2) % w
            y = (y + math.sin(ang) * 2.2) % h
            ix, iy = int(x), int(y)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    d2 = dx * dx + dy * dy
                    if d2 <= 1:
                        k = dark if d2 == 0 else (0.72 + dark * 0.28)
                        img[(iy + dy) % h, (ix + dx) % w] *= k


def _save_png(arr: np.ndarray, path: Path) -> None:
    u8 = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    Image.fromarray(u8, mode="RGB").save(path, format="PNG", compress_level=9)


def build_textures(out_dir: Path) -> None:
    sz = 256

    # 1. bako_boulder1.png - Heavy weathered dark-grey fractured Bakersfield concrete with soot & aggregate
    #    (kept deliberately darker than raw plaster so daylight ~2x exposure renders rich heavy concrete, not pale pebbles!)
    rng = np.random.default_rng(20261101)
    n1 = _fbm(sz, rng)
    n2 = _fbm(sz, rng, (8, 16, 32, 64))
    speck = rng.random((sz, sz), dtype=np.float32)
    base = np.zeros((sz, sz, 3), dtype=np.float32)
    base[:, :, 0] = 84.0 + (n1 - 0.5) * 48.0 + (n2 - 0.5) * 24.0
    base[:, :, 1] = 79.0 + (n1 - 0.5) * 45.0 + (n2 - 0.5) * 22.0
    base[:, :, 2] = 72.0 + (n1 - 0.5) * 40.0 + (n2 - 0.5) * 18.0
    base[speck > 0.94] += 22.0
    base[speck < 0.08] -= 26.0
    scorch = np.clip((n2 - 0.54) * 2.5, 0.0, 0.62)
    base *= (1.0 - scorch[:, :, None])
    _add_cracks(base, rng, n_cracks=18, dark=0.28)
    _save_png(base, out_dir / "bako_boulder1.png")

    # 2. bako_boulder2.png - Heavy weathered dark-grey/umber concrete masonry blocks (ZERO salmon/pink!)
    rng = np.random.default_rng(20261102)
    n1 = _fbm(sz, rng)
    grain = _fbm(sz, rng, (16, 32, 64))
    brick = np.zeros((sz, sz, 3), dtype=np.float32)
    row_h = 26
    col_w = 56
    for y in range(sz):
        row = y // row_h
        ry = y % row_h
        x_off = (col_w // 2) if (row & 1) else 0
        for x in range(sz):
            cx = (x + x_off) % col_w
            col = ((x + x_off) // col_w) % 8
            is_mortar = (ry < 3) or (cx < 3)
            if is_mortar:
                brick[y, x] = (58.0, 55.0, 50.0)
            else:
                hv = ((row * 37 + col * 19) % 11) / 10.0 - 0.5
                brick[y, x, 0] = 76.0 + hv * 20.0
                brick[y, x, 1] = 71.0 + hv * 18.0
                brick[y, x, 2] = 64.0 + hv * 16.0
    brick += (grain[:, :, None] - 0.5) * 26.0
    dust = np.clip((n1 - 0.50) * 1.6, 0.0, 0.48)[:, :, None]
    dust_col = np.array([92.0, 86.0, 76.0], dtype=np.float32)
    brick = brick * (1.0 - dust) + dust_col * dust
    _add_cracks(brick, rng, n_cracks=16, dark=0.28)
    _save_png(brick, out_dir / "bako_boulder2.png")

    # 3. bako_boulder3.png - Dark sheared reinforced concrete floor slab with scorch & fracture veins
    rng = np.random.default_rng(20261103)
    n1 = _fbm(sz, rng)
    n2 = _fbm(sz, rng, (8, 16, 32, 64))
    slab = np.zeros((sz, sz, 3), dtype=np.float32)
    slab[:, :, 0] = 88.0 + (n1 - 0.5) * 42.0 + (n2 - 0.5) * 22.0
    slab[:, :, 1] = 84.0 + (n1 - 0.5) * 40.0 + (n2 - 0.5) * 20.0
    slab[:, :, 2] = 79.0 + (n1 - 0.5) * 38.0 + (n2 - 0.5) * 18.0
    speck = rng.random((sz, sz), dtype=np.float32)
    slab[speck > 0.92] += 20.0
    slab[speck < 0.10] -= 28.0
    soot = np.clip((n2 - 0.56) * 2.2, 0.0, 0.54)
    slab *= (1.0 - soot[:, :, None])
    _add_cracks(slab, rng, n_cracks=20, dark=0.28)
    _save_png(slab, out_dir / "bako_boulder3.png")

    # 4. bako_boulder4.png - Weathered warm-umber/grey-tan concrete & charred stucco chunk
    rng = np.random.default_rng(20261104)
    n1 = _fbm(sz, rng)
    n2 = _fbm(sz, rng, (16, 32, 64))
    stucco = np.zeros((sz, sz, 3), dtype=np.float32)
    stucco[:, :, 0] = 98.0 + (n1 - 0.5) * 38.0 + (n2 - 0.5) * 20.0
    stucco[:, :, 1] = 88.0 + (n1 - 0.5) * 34.0 + (n2 - 0.5) * 18.0
    stucco[:, :, 2] = 74.0 + (n1 - 0.5) * 30.0 + (n2 - 0.5) * 16.0
    char = np.clip((n1 - 0.54) * 2.1, 0.0, 0.50)
    stucco *= (1.0 - char[:, :, None])
    _add_cracks(stucco, rng, n_cracks=16, dark=0.30)
    _save_png(stucco, out_dir / "bako_boulder4.png")

    # 5. bako_rebar.png - Oxidized rust & dark steel rebar texture
    rng = np.random.default_rng(20261105)
    n1 = _fbm(sz, rng, (8, 16, 32, 64))
    rebar = np.zeros((sz, sz, 3), dtype=np.float32)
    rebar[:, :, 0] = 86.0 + (n1 - 0.5) * 58.0
    rebar[:, :, 1] = 48.0 + (n1 - 0.5) * 30.0
    rebar[:, :, 2] = 34.0 + (n1 - 0.5) * 22.0
    yy = np.arange(sz, dtype=np.float32)[:, None]
    ribs = (0.86 + 0.16 * np.sin(yy * (2.0 * math.pi / 12.0)))[:, :, None]
    rebar *= ribs
    _save_png(rebar, out_dir / "bako_rebar.png")

    # 6. bako_glass_shard.png - Deep faceted cool ice-blue/silver-slate crystalline glass texture
    #    (deliberately darker base + crisp dark/bright bevel edges so ~2x daylight exposure + alpha=0.56
    #     renders rich translucent glinting glass instead of flat #FFFFFF paper cards!)
    rng = np.random.default_rng(20261106)
    n1 = _fbm(sz, rng, (4, 8, 16, 32))
    yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32) / float(sz)
    # Sharp faceted planar reflection bands across cool slate-cyan glass
    diag = (xx * 0.76 + yy * 0.65) % 1.0
    glint1 = np.exp(-((diag - 0.30) ** 2) / 0.0022)
    glint2 = np.exp(-((diag - 0.72) ** 2) / 0.0014)
    # Dark outer refraction frame + razor-bright inner bevel glint around perimeter
    rad_e = np.maximum(np.abs(xx - 0.5), np.abs(yy - 0.5)) * 2.0
    dark_rim = np.clip((rad_e - 0.86) / 0.14, 0.0, 1.0)
    bright_bevel = np.exp(-((rad_e - 0.82) ** 2) / 0.0018)
    # Faceted triangular shade variation across diagonals
    facet_shade = np.where((xx - 0.5) * 0.65 + (yy - 0.5) * 0.75 > 0.0, 1.12, 0.76)
    glass = np.zeros((sz, sz, 3), dtype=np.float32)
    glass[:, :, 0] = (38.0 + (n1 - 0.5) * 22.0) * facet_shade + glint1 * 112.0 + glint2 * 82.0 + bright_bevel * 78.0
    glass[:, :, 1] = (64.0 + (n1 - 0.5) * 26.0) * facet_shade + glint1 * 124.0 + glint2 * 94.0 + bright_bevel * 96.0
    glass[:, :, 2] = (86.0 + (n1 - 0.5) * 28.0) * facet_shade + glint1 * 130.0 + glint2 * 102.0 + bright_bevel * 108.0
    glass *= (1.0 - 0.55 * dark_rim[:, :, None])
    _add_cracks(glass, rng, n_cracks=10, dark=0.52)
    _save_png(glass, out_dir / "bako_glass_shard.png")


# ---------------------------------------------------------------------------
# Procedural Faceted 3D Boulder & Slab Geometry
# ---------------------------------------------------------------------------

def _norm3(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def _sub3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross3(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _icosphere(subdiv: int = 1):
    phi = (1.0 + math.sqrt(5.0)) * 0.5
    verts = [
        _norm3((-1, phi, 0)), _norm3((1, phi, 0)), _norm3((-1, -phi, 0)), _norm3((1, -phi, 0)),
        _norm3((0, -1, phi)), _norm3((0, 1, phi)), _norm3((0, -1, -phi)), _norm3((0, 1, -phi)),
        _norm3((phi, 0, -1)), _norm3((phi, 0, 1)), _norm3((-phi, 0, -1)), _norm3((-phi, 0, 1)),
    ]
    tris = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    for _ in range(subdiv):
        mid_cache = {}
        new_tris = []

        def mid(i, j):
            key = (i, j) if i < j else (j, i)
            if key not in mid_cache:
                a, b = verts[i], verts[j]
                verts.append(_norm3((a[0] + b[0], a[1] + b[1], a[2] + b[2])))
                mid_cache[key] = len(verts) - 1
            return mid_cache[key]

        for a, b, c in tris:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new_tris.extend([(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)])
        tris = new_tris
    return verts, tris


def _triplanar_uv(p, n, uv_scale: float = 0.032):
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if az >= ax and az >= ay:
        return (p[0] * uv_scale + 0.5, p[1] * uv_scale + 0.5)
    if ax >= ay:
        return (p[1] * uv_scale + 0.5, p[2] * uv_scale + 0.5)
    return (p[0] * uv_scale + 0.5, p[2] * uv_scale + 0.5)


def _build_faceted_surface(name: str, shader: str, base_verts, base_tris, uv_scale: float = 0.032):
    """Emits crisp flat-shaded triangles with verified outward CCW winding ((v1-v0)x(v2-v0) outward)."""
    # Compute mesh centroid for winding sanity check
    cx = sum(v[0] for v in base_verts) / len(base_verts)
    cy = sum(v[1] for v in base_verts) / len(base_verts)
    cz = sum(v[2] for v in base_verts) / len(base_verts)
    # Re-center mesh on (0,0,0) so tumbling spins cleanly around visual center
    centered = [(v[0] - cx, v[1] - cy, v[2] - cz) for v in base_verts]

    out_v = []
    out_n = []
    out_st = []
    out_t = []
    for a, b, c in base_tris:
        va, vb, vc = centered[a], centered[b], centered[c]
        cr = _cross3(_sub3(vb, va), _sub3(vc, va))
        mid = ((va[0] + vb[0] + vc[0]) / 3.0, (va[1] + vb[1] + vc[1]) / 3.0, (va[2] + vb[2] + vc[2]) / 3.0)
        if _dot3(cr, mid) < 0.0:
            vb, vc = vc, vb
            cr = _cross3(_sub3(vb, va), _sub3(vc, va))
        n = _norm3(cr)
        idx = len(out_v)
        for p in (va, vb, vc):
            out_v.append(p)
            out_n.append(n)
            out_st.append(_triplanar_uv(p, n, uv_scale))
        out_t.append((idx, idx + 1, idx + 2))

    return dict(name=name, shader=shader, tris=out_t, st=out_st, frames=[(out_v, out_n)])


def _fracture_rock(scale_xyz, seed: int, subdiv: int = 1, n_planes: int = 10, jitter: float = 0.22):
    rng = np.random.default_rng(seed)
    verts, tris = _icosphere(subdiv)
    # Random cleavage planes chip sharp faces off the rock
    planes = []
    for _ in range(n_planes):
        pn = _norm3(tuple(float(x) for x in rng.normal(0.0, 1.0, 3)))
        pd = float(rng.uniform(0.66, 0.94))
        planes.append((pn, pd))

    # Multi-frequency harmonic bumps + plane slicing for natural jagged concrete/rock fracture
    freqs = [(float(rng.uniform(1.6, 3.6)), _norm3(tuple(float(x) for x in rng.normal(0, 1, 3))),
              float(rng.uniform(0, 6.28)), float(rng.uniform(0.05, jitter))) for _ in range(7)]

    deformed = []
    for v in verts:
        r = 1.0
        for f, axis, ph, amp in freqs:
            r += amp * math.sin(f * _dot3(v, axis) + ph)
        p = [v[0] * r, v[1] * r, v[2] * r]
        for pn, pd in planes:
            d = _dot3(p, pn)
            if d > pd:
                excess = d - pd
                p[0] -= pn[0] * excess * 0.85
                p[1] -= pn[1] * excess * 0.85
                p[2] -= pn[2] * excess * 0.85
        deformed.append((p[0] * scale_xyz[0], p[1] * scale_xyz[1], p[2] * scale_xyz[2]))
    return deformed, tris


def _box_chunk(half_xyz, seed: int, n_slices: int = 7):
    """Chunky sheared masonry block (subdivided box with fractured edges & cleavage planes)."""
    rng = np.random.default_rng(seed)
    hx, hy, hz = half_xyz
    # Start from subdivided icosphere mapped onto superellipsoid box so topology is clean & closed
    verts, tris = _icosphere(subdiv=1)
    planes = []
    for _ in range(n_slices):
        pn = _norm3(tuple(float(x) for x in rng.normal(0.0, 1.0, 3)))
        pd = float(rng.uniform(0.72, 0.96))
        planes.append((pn, pd))

    out = []
    for v in verts:
        # Project unit sphere toward cube corners (squircle) for masonry block silhouette
        m = max(abs(v[0]), abs(v[1]), abs(v[2])) or 1.0
        bx = v[0] / m
        by = v[1] / m
        bz = v[2] / m
        # Blend 72% boxy + 28% rounded + jagged fracture noise
        p = [
            0.74 * bx + 0.26 * v[0] + float(rng.uniform(-0.10, 0.10)),
            0.74 * by + 0.26 * v[1] + float(rng.uniform(-0.10, 0.10)),
            0.74 * bz + 0.26 * v[2] + float(rng.uniform(-0.10, 0.10)),
        ]
        for pn, pd in planes:
            d = _dot3(p, pn)
            if d > pd:
                ex = d - pd
                p[0] -= pn[0] * ex * 0.82
                p[1] -= pn[1] * ex * 0.82
                p[2] -= pn[2] * ex * 0.82
        out.append((p[0] * hx, p[1] * hy, p[2] * hz))
    return out, tris


def _rebar_rods_surface(shader: str):
    """4 bent rusty iron rebar stubs protruding from the broken edges of bako_boulder3 slab."""
    rods = [
        ((-12.0, -5.0, 0.5), (-25.5, -7.5, 3.2)),
        ((-11.0, 6.5, -0.8), (-24.0, 9.0, -3.0)),
        ((13.0, -4.0, 0.6), (26.0, -6.5, 2.8)),
        ((12.0, 5.5, -0.4), (24.5, 8.0, -1.8)),
    ]
    out_v, out_n, out_st, out_t = [], [], [], []
    rad = 0.85
    segs = 6
    for p0, p1 in rods:
        axis = _norm3(_sub3(p1, p0))
        ref = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm3(_cross3(axis, ref))
        w = _norm3(_cross3(axis, u))
        ring0, ring1, rnorms = [], [], []
        for k in range(segs):
            th = 2.0 * math.pi * k / segs
            cs, sn = math.cos(th), math.sin(th)
            n = (u[0] * cs + w[0] * sn, u[1] * cs + w[1] * sn, u[2] * cs + w[2] * sn)
            rnorms.append(n)
            ring0.append((p0[0] + n[0] * rad, p0[1] + n[1] * rad, p0[2] + n[2] * rad))
            ring1.append((p1[0] + n[0] * rad, p1[1] + n[1] * rad, p1[2] + n[2] * rad))
        for k in range(segs):
            kn = (k + 1) % segs
            i0 = len(out_v)
            va, vb, vc, vd = ring0[k], ring1[k], ring1[kn], ring0[kn]
            na, nb = rnorms[k], rnorms[kn]
            # Check outward winding on quad (va, vb, vc, vd)
            cr = _cross3(_sub3(vb, va), _sub3(vc, va))
            if _dot3(cr, na) < 0.0:
                va, vb, vc, vd = ring0[kn], ring1[kn], ring1[k], ring0[k]
                na, nb = rnorms[kn], rnorms[k]
            out_v.extend([va, vb, vc, vd])
            out_n.extend([na, na, nb, nb])
            u0, u1 = k / segs, (k + 1) / segs
            out_st.extend([(u0, 0.0), (u0, 1.0), (u1, 1.0), (u1, 0.0)])
            out_t.append((i0, i0 + 1, i0 + 2))
            out_t.append((i0, i0 + 2, i0 + 3))
    return dict(name="rebar", shader=shader, tris=out_t, st=out_st, frames=[(out_v, out_n)])


def _extruded_glass_shard(poly_xy: list[tuple[float, float]], half_thick: float, shader: str, name: str):
    """Build a sharp, beveled 3D polygon glass shard with verified outward CCW winding."""
    n_pts = len(poly_xy)
    cx = sum(p[0] for p in poly_xy) / n_pts
    cy = sum(p[1] for p in poly_xy) / n_pts
    pts = [(p[0] - cx, p[1] - cy) for p in poly_xy]
    # Ensure 2D polygon is CCW so front (+Z) and back (-Z) fans wind cleanly outward
    area2 = sum(pts[i][0] * pts[(i + 1) % n_pts][1] - pts[(i + 1) % n_pts][0] * pts[i][1] for i in range(n_pts))
    if area2 < 0:
        pts.reverse()

    # Slight ridge along centroid on top & bottom for realistic fractured-glass bevel sparkle!
    top_ctr = (0.0, 0.0, half_thick * 1.18)
    bot_ctr = (0.0, 0.0, -half_thick * 1.18)
    top_ring = [(p[0], p[1], half_thick) for p in pts]
    bot_ring = [(p[0], p[1], -half_thick) for p in pts]

    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    span_x = max(1e-3, max_x - min_x)
    span_y = max(1e-3, max_y - min_y)

    def uv2(p):
        return ((p[0] - min_x) / span_x, (p[1] - min_y) / span_y)

    out_v, out_n, out_st, out_t = [], [], [], []

    def add_tri(a, b, c, want_out):
        cr = _cross3(_sub3(b, a), _sub3(c, a))
        if _dot3(cr, want_out) < 0.0:
            b, c = c, b
            cr = _cross3(_sub3(b, a), _sub3(c, a))
        n = _norm3(cr)
        idx = len(out_v)
        for p in (a, b, c):
            out_v.append(p)
            out_n.append(n)
            out_st.append(uv2(p))
        out_t.append((idx, idx + 1, idx + 2))

    # Top & bottom beveled faces
    for i in range(n_pts):
        j = (i + 1) % n_pts
        add_tri(top_ctr, top_ring[i], top_ring[j], (0.0, 0.0, 1.0))
        add_tri(bot_ctr, bot_ring[j], bot_ring[i], (0.0, 0.0, -1.0))
        # Sharp sheared perimeter edges
        p0, p1 = pts[i], pts[j]
        ex, ey = p1[0] - p0[0], p1[1] - p0[1]
        en = _norm3((ey, -ex, 0.0))
        add_tri(bot_ring[i], bot_ring[j], top_ring[j], en)
        add_tri(bot_ring[i], top_ring[j], top_ring[i], en)

    return dict(name=name, shader=shader, tris=out_t, st=out_st, frames=[(out_v, out_n)])


def build_models(out_dir: Path) -> None:
    # 1. bako_boulder1.md3 - Heavy angular fractured concrete masonry block (~36x28x24u, NOT round pebble!)
    v1, t1 = _box_chunk((18.5, 14.5, 12.2), seed=101, n_slices=9)
    s1 = _build_faceted_surface("boulder1", "progs/bako_boulder1", v1, t1, uv_scale=0.036)
    md3lib.write(str(out_dir / "bako_boulder1.md3"), dict(name="progs/bako_boulder1.md3", surfaces=[s1]))

    # 2. bako_boulder2.md3 - Padre red-brick & mortar sheared masonry chunk (~38x26x24u)
    v2, t2 = _box_chunk((19.0, 13.0, 11.8), seed=202, n_slices=8)
    s2 = _build_faceted_surface("boulder2", "progs/bako_boulder2", v2, t2, uv_scale=0.030)
    md3lib.write(str(out_dir / "bako_boulder2.md3"), dict(name="progs/bako_boulder2.md3", surfaces=[s2]))

    # 3. bako_boulder3.md3 - Reinforced concrete floor slab with exposed rusty rebar (~40x30x13u)
    v3, t3 = _box_chunk((20.0, 14.8, 6.6), seed=303, n_slices=7)
    s3_slab = _build_faceted_surface("slab", "progs/bako_boulder3", v3, t3, uv_scale=0.032)
    s3_rebar = _rebar_rods_surface("progs/bako_rebar")
    md3lib.write(str(out_dir / "bako_boulder3.md3"), dict(name="progs/bako_boulder3.md3", surfaces=[s3_slab, s3_rebar]))

    # 4. bako_boulder4.md3 - Angular sheared Bakersfield concrete/stucco corner chunk (~30x24x20u)
    v4, t4 = _box_chunk((15.2, 12.0, 10.2), seed=404, n_slices=10)
    s4 = _build_faceted_surface("boulder4", "progs/bako_boulder4", v4, t4, uv_scale=0.040)
    md3lib.write(str(out_dir / "bako_boulder4.md3"), dict(name="progs/bako_boulder4.md3", surfaces=[s4]))

    # 5..7. bako_glass_shard1..3.md3 - Large jagged glinting window glass shards (~16..23u wide, ~2x+ bigger!)
    shard1_poly = [(-10.5, -4.2), (9.8, -1.8), (4.2, 6.8), (-6.8, 4.6)]
    gs1 = _extruded_glass_shard(shard1_poly, half_thick=0.85, shader="progs/bako_glass_shard", name="glass1")
    md3lib.write(str(out_dir / "bako_glass_shard1.md3"), dict(name="progs/bako_glass_shard1.md3", surfaces=[gs1]))

    shard2_poly = [(-8.6, -6.2), (6.4, -5.0), (10.2, 1.5), (1.8, 7.6), (-7.8, 3.8)]
    gs2 = _extruded_glass_shard(shard2_poly, half_thick=0.85, shader="progs/bako_glass_shard", name="glass2")
    md3lib.write(str(out_dir / "bako_glass_shard2.md3"), dict(name="progs/bako_glass_shard2.md3", surfaces=[gs2]))

    shard3_poly = [(-12.0, -3.2), (11.6, -0.6), (3.6, 4.4), (-8.4, 3.4)]
    gs3 = _extruded_glass_shard(shard3_poly, half_thick=0.78, shader="progs/bako_glass_shard", name="glass3")
    md3lib.write(str(out_dir / "bako_glass_shard3.md3"), dict(name="progs/bako_glass_shard3.md3", surfaces=[gs3]))


def write_reproducible_pk3(out_pk3: Path, entries: dict[str, bytes]) -> str:
    out_pk3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_pk3, "w") as zf:
        for arcname in sorted(entries):
            data = entries[arcname]
            ext = Path(arcname).suffix.lower()
            comp = zipfile.ZIP_STORED if ext in STORE_EXTS else zipfile.ZIP_DEFLATED
            zi = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_TIME)
            zi.compress_type = comp
            zi.external_attr = FIXED_EXT_ATTR
            if comp == zipfile.ZIP_DEFLATED:
                zf.writestr(zi, data, compress_type=comp, compresslevel=9)
            else:
                zf.writestr(zi, data, compress_type=comp)
    h = hashlib.sha256(out_pk3.read_bytes()).hexdigest()
    return h


def build_pk3(out_pk3: Path, levelshot: Path | None = None) -> tuple[str, int, list[str]]:
    with tempfile.TemporaryDirectory(prefix="bako_pk3_") as td:
        tmp = Path(td)
        build_textures(tmp)
        build_models(tmp)
        entries: dict[str, bytes] = {}
        for p in sorted(tmp.iterdir()):
            if p.is_file():
                entries[f"progs/{p.name}"] = p.read_bytes()

        ls_src = levelshot if (levelshot and levelshot.is_file()) else (ASSETS_DIR / "levelshot_bakersfieldish.jpg")
        if ls_src.is_file():
            entries["levelshots/bakersfieldish.jpg"] = ls_src.read_bytes()

        mm_src = ASSETS_DIR / "minimap_bakersfieldish.png"
        if mm_src.is_file():
            entries["gfx/minimap/bakersfieldish.png"] = mm_src.read_bytes()
            entries["gfx/minimap/bakersfieldish.txt"] = MINIMAP_BOUNDS_TXT
            entries["scripts/bakersfieldish_minimap.shader"] = MINIMAP_SHADER_TXT

        sha = write_reproducible_pk3(out_pk3, entries)
        return sha, out_pk3.stat().st_size, sorted(entries)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build reproducible zz_bakersfieldish.pk3")
    ap.add_argument("out_pk3", nargs="?", default=str(DEFAULT_OUT), help="Output PK3 path")
    ap.add_argument("--levelshot", default=None, help="Optional levelshots/bakersfieldish.jpg to include")
    ap.add_argument("--verify-repro", action="store_true", help="Build twice and assert identical SHA-256")
    args = ap.parse_args()

    out_path = Path(args.out_pk3)
    ls_path = Path(args.levelshot) if args.levelshot else None
    sha1, sz1, names = build_pk3(out_path, ls_path)
    print(f"Built {out_path} ({sz1:,} bytes, {len(names)} entries, sha256={sha1})")
    for n in names:
        print(f"  {n}")

    if args.verify_repro:
        with tempfile.TemporaryDirectory(prefix="bako_pk3_check_") as td:
            p2 = Path(td) / "repro.pk3"
            sha2, sz2, _ = build_pk3(p2, ls_path)
            assert sha1 == sha2 and sz1 == sz2, f"Non-reproducible build! {sha1} != {sha2}"
            print(f"Reproducibility verified: byte-identical SHA-256 ({sha2})")


if __name__ == "__main__":
    main()
