"""Builds 3D MD3 prop models and HDR-calibrated Quake wall posters for the Daniel meme pack:
  - progs/daniel_table.md3 + progs/daniel_table.png       (4-legged honey-oak 4 AM wooden table)
  - progs/daniel_webcam.md3 + progs/daniel_webcam.png     (Logitech QuickCam 'Justin Berry' eyeball webcam)
  - progs/daniel_poster.md3 + .md3_0..3.skin + progs/dan_poster_0..3.png
  - textures/dan_4am.png, textures/dan_shaaa.png, textures/dan_webcam.png, textures/dan_ccc.png
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "daniel"
PROGS_DIR = MOD_DIR / "progs"
TEX_DIR = MOD_DIR / "textures"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
import md3lib


def _font(size: int, bold: bool = True):
    names = ("impact.ttf", "arialbd.ttf", "tahomabd.ttf", "arial.ttf") if bold else ("tahoma.ttf", "arial.ttf")
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", n), size)
        except OSError:
            pass
    return ImageFont.load_default()


def _add_box(
    verts: list,
    norms: list,
    st: list,
    tris: list,
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    uv_rect: tuple[float, float, float, float] = (0.05, 0.05, 0.95, 0.95),
) -> None:
    u0, v0, u1, v1 = uv_rect
    faces = [
        # +Z top
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0.0, 0.0, 1.0)),
        # -Z bottom
        ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0.0, 0.0, -1.0)),
        # +X front
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1.0, 0.0, 0.0)),
        # -X back
        ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1.0, 0.0, 0.0)),
        # +Y left
        ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0.0, 1.0, 0.0)),
        # -Y right
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0.0, -1.0, 0.0)),
    ]
    uvs = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    for pts, nrm in faces:
        base = len(verts)
        for p, uv in zip(pts, uvs):
            verts.append(p)
            norms.append(nrm)
            st.append(uv)
        tris.append((base, base + 2, base + 1))
        tris.append((base, base + 3, base + 2))
        # Double-sided insurance for tumbling gibs
        tris.append((base, base + 1, base + 2))
        tris.append((base, base + 2, base + 3))


def build_table_md3() -> None:
    """Builds progs/daniel_table.md3 + progs/daniel_table.png (honey-oak 4 AM wooden side table)."""
    PROGS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(404)

    # Procedural warm honey-oak woodgrain texture (pre-toned for DarkPlaces HDR)
    tw, th = 128, 128
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
    grain = (
        np.sin(xx * 0.22 + np.sin(yy * 0.07) * 2.2) * 11.0
        + np.sin(xx * 0.65 + yy * 0.03) * 5.0
        + rng.normal(0.0, 2.8, (th, tw))
    )
    r = np.clip((188.0 + grain) * 0.62, 0, 255)
    g = np.clip((138.0 + grain * 0.78) * 0.62, 0, 255)
    b = np.clip((76.0 + grain * 0.45) * 0.62, 0, 255)
    tex = np.dstack([r, g, b]).astype(np.uint8)
    # Darker underside/apron strip in bottom quarter of UV
    tex[96:, :, :] = (tex[96:, :, :].astype(np.float32) * 0.78).astype(np.uint8)
    Image.fromarray(tex, "RGB").save(PROGS_DIR / "daniel_table.png")

    verts, norms, st, tris = [], [], [], []
    # Table centered around Z = -14..+14 so origin sits near center of mass for smooth bounce/tumble
    # Tabletop slab: 38 x 26 x 2.6
    _add_box(verts, norms, st, tris, -19.0, -13.0, 11.4, 19.0, 13.0, 14.0, (0.04, 0.04, 0.96, 0.70))
    # Under-apron rails
    _add_box(verts, norms, st, tris, -16.5, -11.0, 8.2, 16.5, -9.4, 11.4, (0.05, 0.76, 0.95, 0.96))
    _add_box(verts, norms, st, tris, -16.5, 9.4, 8.2, 16.5, 11.0, 11.4, (0.05, 0.76, 0.95, 0.96))
    _add_box(verts, norms, st, tris, -16.5, -9.4, 8.2, -14.9, 9.4, 11.4, (0.05, 0.76, 0.95, 0.96))
    _add_box(verts, norms, st, tris, 14.9, -9.4, 8.2, 16.5, 9.4, 11.4, (0.05, 0.76, 0.95, 0.96))
    # 4 sturdy square wooden legs
    for lx in (-16.5, 14.3):
        for ly in (-11.0, 8.8):
            _add_box(verts, norms, st, tris, lx, ly, -14.0, lx + 2.2, ly + 2.2, 11.4, (0.08, 0.08, 0.45, 0.72))

    surf = dict(
        name="daniel_table",
        shader="progs/daniel_table",
        tris=tris,
        st=st,
        frames=[(verts, norms)],
    )
    md3lib.write(str(PROGS_DIR / "daniel_table.md3"), dict(name="daniel_table", surfaces=[surf], nframes=1))
    print("Wrote progs/daniel_table.md3 + daniel_table.png")


def build_webcam_md3() -> None:
    """Builds progs/daniel_webcam.md3 + progs/daniel_webcam.png (Logitech QuickCam eyeball USB webcam)."""
    tw, th = 128, 128
    im = Image.new("RGB", (tw, th), (122, 125, 130))
    d = ImageDraw.Draw(im)
    # Left half (u=0..0.5): white/grey QuickCam sphere with front lens bullseye centered at (32, 64)
    d.rectangle([0, 0, 64, 128], fill=(128, 132, 136))
    d.ellipse([6, 38, 58, 90], fill=(148, 148, 142))     # beige lens bezel ring
    d.ellipse([14, 46, 50, 82], fill=(28, 30, 34))       # dark recessed lens barrel
    d.ellipse([22, 54, 42, 74], fill=(12, 18, 28))       # glass optic
    d.ellipse([26, 57, 33, 64], fill=(135, 175, 215))    # lens glint
    d.ellipse([29, 31, 35, 37], fill=(225, 38, 32))      # red recording LED!
    # Right half (u=0.5..1.0): dark charcoal rubber desk stand
    d.rectangle([64, 0, 128, 128], fill=(34, 36, 40))
    im.save(PROGS_DIR / "daniel_webcam.png")

    verts, norms, st, tris = [], [], [], []
    # UV sphere for eyeball body (radius 5.5, centered at z=+1.5, facing +X)
    r_sph, cz = 5.5, 1.5
    n_lat, n_lon = 10, 16
    ring_idx = []
    for i in range(n_lat + 1):
        phi = math.pi * i / n_lat  # 0 (top +Z) .. pi (bottom -Z)
        row = []
        for j in range(n_lon + 1):
            th_a = -math.pi + 2.0 * math.pi * j / n_lon  # th_a = 0 => +X (front lens!)
            nx = math.sin(phi) * math.cos(th_a)
            ny = math.sin(phi) * math.sin(th_a)
            nz = math.cos(phi)
            # Map front hemisphere near +X onto bullseye at (u=0.25, v=0.5)
            u = 0.25 + 0.22 * ny if nx > 0.15 else 0.04
            v = 0.50 - 0.22 * nz if nx > 0.15 else 0.10
            row.append(len(verts))
            verts.append((nx * r_sph, ny * r_sph, cz + nz * r_sph))
            norms.append((nx, ny, nz))
            st.append((u, v))
        ring_idx.append(row)

    for i in range(n_lat):
        for j in range(n_lon):
            a, b = ring_idx[i][j], ring_idx[i][j + 1]
            c, d_ = ring_idx[i + 1][j + 1], ring_idx[i + 1][j]
            tris.extend([(a, c, b), (a, d_, c), (a, b, c), (a, c, d_)])

    # Triangular dark desk base under sphere (z = -6.5 .. -3.2)
    _add_box(verts, norms, st, tris, -4.8, -5.2, -6.5, 5.2, 5.2, -3.5, (0.58, 0.15, 0.92, 0.85))
    _add_box(verts, norms, st, tris, -1.6, -1.6, -3.8, 1.6, 1.6, -2.5, (0.58, 0.15, 0.92, 0.85))

    surf = dict(
        name="daniel_webcam",
        shader="progs/daniel_webcam",
        tris=tris,
        st=st,
        frames=[(verts, norms)],
    )
    md3lib.write(str(PROGS_DIR / "daniel_webcam.md3"), dict(name="daniel_webcam", surfaces=[surf], nframes=1))
    print("Wrote progs/daniel_webcam.md3 + daniel_webcam.png")


def build_posters() -> None:
    """Builds 4 meme wall posters in textures/dan_*.png and progs/daniel_poster.md3 (+4 skins)."""
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    fdir = REF_DIR / "frames"

    specs = [
        ("dan_4am",    "v1_table4am_019.png", "IT'S 4 AM DANIEL!", "SORRY! MOVING THE TABLE!"),
        ("dan_shaaa",  "v2_shaaa_016.png",    "B-LAN 4:00 AM",     "SHAAAAAAAAAAAAAA!!"),
        ("dan_webcam", "v3_webcam_015.png",   "CAN'T SEE!",        "JUSTIN BERRY'S WEBCAM?!"),
        ("dan_ccc",    "v4_ccc_012.png",      "CCC! CCC! CCC!",    "C-C-C-C-C-C-C-C!!"),
    ]

    f_top = _font(24, bold=True)
    f_bot = _font(21, bold=True)

    for idx, (tex_name, src_fn, top_txt, bot_txt) in enumerate(specs):
        src = Image.open(fdir / src_fn).convert("RGB")
        # Center-crop to 4:3 or 1:1 square 256x256 framed poster
        w, h = src.size
        side = min(w, h)
        cx, cy = w // 2, int(h * 0.44)
        x0 = max(0, min(w - side, cx - side // 2))
        y0 = max(0, min(h - side, cy - side // 2))
        crop = src.crop((x0, y0, x0 + side, y0 + side)).resize((236, 236), Image.Resampling.LANCZOS)
        crop = ImageEnhance.Contrast(crop).enhance(1.14)

        poster = Image.new("RGB", (256, 256), (26, 22, 18))
        d = ImageDraw.Draw(poster)
        # Classic dark wood/metal LAN poster frame
        d.rectangle([2, 2, 253, 253], outline=(96, 74, 44), width=4)
        poster.paste(crop, (10, 10))

        # Meme Impact caption stroke top & bottom
        for txt, y_pos, fnt in ((top_txt, 14, f_top), (bot_txt, 214, f_bot)):
            bbox = d.textbbox((0, 0), txt, font=fnt)
            tw_t = bbox[2] - bbox[0]
            tx = (256 - tw_t) // 2
            for ox in (-2, -1, 0, 1, 2):
                for oy in (-2, -1, 0, 1, 2):
                    if ox or oy:
                        d.text((tx + ox, y_pos + oy), txt, font=fnt, fill=(0, 0, 0))
            d.text((tx, y_pos), txt, font=fnt, fill=(255, 245, 90) if y_pos > 100 else (255, 255, 255))

        # Save full-brightness map texture (diffuse lit by map lightmaps) + HDR-toned entity skin
        poster.save(TEX_DIR / f"{tex_name}.png")
        toned = Image.fromarray((np.asarray(poster, dtype=np.float32) * 0.62).astype(np.uint8), "RGB")
        toned.save(PROGS_DIR / f"dan_poster_{idx}.png")

    # Framed 3D poster quad MD3 (36 x 36 units facing +X)
    hw, hh = 18.0, 18.0
    vs = [(0.5, -hw, hh), (0.5, hw, hh), (0.5, hw, -hh), (0.5, -hw, -hh)]
    ns = [(1.0, 0.0, 0.0)] * 4
    st = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
    surf = dict(name="dan_poster", shader="progs/dan_poster_0", tris=tris, st=st, frames=[(vs, ns)])
    md3lib.write(str(PROGS_DIR / "daniel_poster.md3"), dict(name="daniel_poster", surfaces=[surf], nframes=1))
    for k in range(4):
        (PROGS_DIR / f"daniel_poster.md3_{k}.skin").write_text(f"dan_poster,progs/dan_poster_{k}\n", encoding="utf-8")
    print("Wrote 4 textures/dan_*.png + progs/daniel_poster.md3 (4 skins)")


def main() -> None:
    build_table_md3()
    build_webcam_md3()
    build_posters()


if __name__ == "__main__":
    main()
