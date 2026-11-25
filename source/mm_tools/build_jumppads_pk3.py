#!/usr/bin/env python3
"""Build zz_jumppads.pk3: a Quake 3 Arena style jump pad for Bakersfield Downtown (playtest 1.76 found the old
chevron slabs "ghetto").

progs/q3pad.md3, 74 units across (q3pad.qc scales it to each pad), four surfaces:
  base   square gunmetal plate with a recessed round pad, bolts and hazard edge; covers the old slab top
  ring   glowing amber ring, pulsing                   (additive, rgbGen wave)
  core   glowing centre with concentric rings, turning (additive, tcMod rotate)
  beam   soft light column rising out of the pad       (additive, pulsing, both sides)
plus the textures and scripts/q3pad.shader.

Playtest follow-up ("not all of the jump pads have been replaced"): also
progs/q3skypad.md3          the same pad in blue, for the SkyPads
progs/q3kart60/66/72.md3    the kart boost pads: a metal deck, lead-in ramp and lit rails that cover the old
                            chevron faces exactly (half-widths 60, 66 and 72 units), with the ring and core on top

Reproducible: no clock, no randomness, fixed zip dates/attributes, pinned Pillow/numpy in CI.

Usage:
  python -I build_jumppads_pk3.py <out zz_jumppads.pk3> [--preview-dir <dir>] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import math
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md3lib  # noqa: E402

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
HALF = 37.0          # half of the plate (74 units, the size of the Downtown pad triggers)
SEG = 40             # circle segments

SHADER = """// written by source/mm_tools/build_jumppads_pk3.py
// Quake 3 style jump pad for Bakersfield Downtown (progs/q3pad.md3, placed by q3pad.qc)

progs/q3pad_base
{
	{
		map progs/q3pad_base
		rgbGen lightingDiffuse
	}
	{
		map progs/q3pad_base_glow
		blendfunc add
		rgbGen wave sin 0.8 0.2 0 1.1
	}
}

progs/q3pad_ring
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3pad_ring
		blendfunc add
		rgbGen wave sin 0.75 0.25 0 1.1
	}
}

progs/q3pad_core
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3pad_core
		blendfunc add
		tcMod rotate 70
	}
	{
		map progs/q3pad_core
		blendfunc add
		tcMod rotate -40
		rgbGen wave sin 0.5 0.3 0.25 1.1
	}
}

progs/q3pad_beam
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3pad_beam
		blendfunc add
		rgbGen wave sin 0.75 0.25 0 1.1
	}
}

progs/q3sky_base
{
	{
		map progs/q3pad_base
		rgbGen lightingDiffuse
	}
	{
		map progs/q3sky_base_glow
		blendfunc add
		rgbGen wave sin 0.8 0.2 0 1.1
	}
}

progs/q3sky_ring
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3sky_ring
		blendfunc add
		rgbGen wave sin 0.75 0.25 0 1.1
	}
}

progs/q3sky_core
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3sky_core
		blendfunc add
		tcMod rotate 70
	}
	{
		map progs/q3sky_core
		blendfunc add
		tcMod rotate -40
		rgbGen wave sin 0.5 0.3 0.25 1.1
	}
}

progs/q3sky_beam
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3sky_beam
		blendfunc add
		rgbGen wave sin 0.75 0.25 0 1.1
	}
}

progs/q3kart_deck
{
	{
		map progs/q3kart_deck
		rgbGen lightingDiffuse
	}
}

progs/q3kart_rail
{
	cull none
	{
		map progs/q3kart_rail
		rgbGen identity
	}
}

progs/q3kart_arrows
{
	cull none
	surfaceparm nolightmap
	{
		map progs/q3kart_arrows
		blendfunc add
		tcMod scroll 0 0.9
		rgbGen wave sin 0.8 0.2 0 1.6
	}
}
"""

KART_HALF_WIDTHS = (60, 66, 72)     # half widths of the Downtown kart pad decks


# ---------------------------------------------------------------- textures

def _radial(n: int):
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    c = (n - 1) / 2.0
    return np.hypot(x - c, y - c) / c, np.arctan2(y - c, x - c)


def tex_base(n: int = 256) -> tuple[Image.Image, Image.Image]:
    r, ang = _radial(n)
    y, x = np.mgrid[0:n, 0:n].astype(np.float64) / (n - 1)
    # gunmetal plate with a faint brushed grain (deterministic sine noise)
    grain = 0.5 + 0.5 * np.sin(y * 900.0 + np.sin(x * 37.0) * 3.0)
    base = 58 + 10 * grain
    img = np.stack([base, base + 2, base + 6], axis=-1)
    # bevelled outer frame
    edge = np.minimum.reduce([x, y, 1 - x, 1 - y])
    frame = edge < 0.05
    img[frame] = img[frame] * 1.35
    # hazard stripes on the frame
    stripes = ((np.floor((x + y) * 22) % 2) == 0) & (edge < 0.035) & (edge > 0.012)
    img[stripes] = [196, 150, 28]
    # recessed round pad: darker well with a lit lip
    well = r < 0.86
    img[well] = img[well] * 0.55
    lip = (r > 0.86) & (r < 0.91)
    img[lip] = [150, 156, 166]
    # radial vents in the well
    vents = well & (r > 0.70) & (r < 0.80) & ((np.floor((ang + math.pi) / (2 * math.pi) * 24) % 2) == 0)
    img[vents] = [24, 24, 28]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for bx, by in ((0.12, 0.12), (0.88, 0.12), (0.12, 0.88), (0.88, 0.88)):
        cx, cy = bx * n, by * n
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(120, 124, 132), outline=(30, 30, 34), width=2)
        d.line((cx - 4, cy, cx + 4, cy), fill=(40, 40, 44), width=2)
    # glow map: the lit lip and the vents' inner edge glow amber
    g = np.zeros((n, n, 3))
    glow_lip = np.exp(-((r - 0.885) / 0.02) ** 2)
    g += glow_lip[..., None] * np.array([255, 150, 40]) * 0.55
    glow = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGB")
    return im, glow


def tex_ring(w: int = 512, h: int = 64) -> Image.Image:
    v = np.linspace(0, 1, h)[:, None]
    u = np.linspace(0, 1, w)[None, :]
    core = np.exp(-((v - 0.5) / 0.18) ** 2)
    halo = np.exp(-((v - 0.5) / 0.42) ** 2) * 0.45
    ticks = 0.82 + 0.18 * (np.cos(u * 2 * math.pi * 16) > 0.6)
    val = (core + halo) * ticks
    img = np.stack([val * 255, val * 170 + core * 60, val * 50 + core * 40], axis=-1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def tex_core(n: int = 256) -> Image.Image:
    r, ang = _radial(n)
    rings = 0.5 + 0.5 * np.cos(r * 2 * math.pi * 5.0)
    spokes = 0.6 + 0.4 * np.cos(ang * 6) ** 8
    hot = np.exp(-(r / 0.28) ** 2)
    val = (rings * 0.55 * spokes + hot) * np.clip(1.05 - r, 0, 1)
    val[r > 1.0] = 0
    img = np.stack([val * 255, val * 180 + hot * 50, val * 60 + hot * 70], axis=-1)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    return im.filter(ImageFilter.GaussianBlur(1.2))


def tex_beam(w: int = 64, h: int = 256) -> Image.Image:
    v = np.linspace(0, 1, h)[:, None]          # 0 = bottom of the column
    u = np.linspace(0, 1, w)[None, :]
    fade = (1 - v) ** 2.2
    fade[-3:] = 0                              # nothing at the very top edge
    streak = 0.8 + 0.2 * np.cos(u * 2 * math.pi * 3)
    val = fade * streak * 0.6
    img = np.stack([val * 255, val * 175, val * 60], axis=-1)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    return im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)   # image row 0 = top of the column


def blue(im: Image.Image) -> Image.Image:
    """The amber glow textures recoloured for the SkyPads (red and blue swapped, a touch more green)."""
    a = np.asarray(im, dtype=np.float64)
    out = np.stack([a[..., 2] * 0.9, np.clip(a[..., 1] * 1.08, 0, 255), a[..., 0]], axis=-1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def tex_kart_deck(n: int = 256) -> Image.Image:
    y, x = np.mgrid[0:n, 0:n].astype(np.float64) / (n - 1)
    grain = 0.5 + 0.5 * np.sin(y * 900.0 + np.sin(x * 37.0) * 3.0)
    base = 52 + 10 * grain
    img = np.stack([base, base + 2, base + 6], axis=-1)
    edge = np.minimum.reduce([x, y, 1 - x, 1 - y])
    img[edge < 0.045] = img[edge < 0.045] * 1.35
    stripes = ((np.floor((x + y) * 22) % 2) == 0) & (edge < 0.032) & (edge > 0.010)
    img[stripes] = [196, 150, 28]
    tread = (edge > 0.07) & ((np.floor(y * 18) % 3) == 0) & (np.abs(x - 0.5) > 0.40)
    img[tread] = [26, 26, 30]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for bx, by in ((0.10, 0.10), (0.90, 0.10), (0.10, 0.90), (0.90, 0.90)):
        cx, cy = bx * n, by * n
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(120, 124, 132), outline=(30, 30, 34), width=2)
    return im


def tex_kart_rail(w: int = 256, h: int = 32) -> Image.Image:
    v = np.linspace(0, 1, h)[:, None]
    u = np.linspace(0, 1, w)[None, :]
    lamp = np.exp(-((v - 0.5) / 0.22) ** 2) * (0.55 + 0.45 * (np.cos(u * 2 * math.pi * 6) > -0.4))
    img = np.stack([45 + lamp * 210, 46 + lamp * 130, 52 + lamp * 20], axis=-1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def tex_kart_arrows(n: int = 128) -> Image.Image:
    """One arrow per tile pointing to the top of the image (the travel direction), black elsewhere (additive)."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float64) / (n - 1)
    d = np.abs((y - 0.30) - np.abs(x - 0.5) * 0.85)
    val = np.exp(-(d / 0.07) ** 2) * (np.abs(x - 0.5) < 0.38)
    img = np.stack([val * 255, val * 170, val * 45], axis=-1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def png(im: Image.Image) -> bytes:
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue()


# ---------------------------------------------------------------- model

def surf(name, shader, verts, norms, st, tris):
    return {"name": name, "shader": shader, "tris": tris, "st": st, "frames": [(verts, norms)]}


def write_md3(name: str, surfaces: list) -> bytes:
    mdl = {"name": name, "frame_names": ["pad"], "surfaces": surfaces}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / (name + ".md3")
        md3lib.write(str(p), mdl)
        return p.read_bytes()


def annulus(name, shader, r0, r1, z, repeat=4.0):
    up = (0.0, 0.0, 1.0)
    verts, norms, st, tris = [], [], [], []
    for i in range(SEG + 1):
        a = 2 * math.pi * i / SEG
        c, s = math.cos(a), math.sin(a)
        verts += [(c * r0, s * r0, z), (c * r1, s * r1, z)]
        norms += [up, up]
        st += [(i / SEG * repeat, 1.0), (i / SEG * repeat, 0.0)]
    for i in range(SEG):
        k = i * 2
        tris += [(k, k + 3, k + 1), (k, k + 2, k + 3)]
    return surf(name, shader, verts, norms, st, tris)


def disc(name, shader, rc, z):
    up = (0.0, 0.0, 1.0)
    verts, norms, st, tris = [(0.0, 0.0, z)], [up], [(0.5, 0.5)], []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        verts.append((math.cos(a) * rc, math.sin(a) * rc, z))
        norms.append(up)
        st.append((0.5 + 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a)))
    for i in range(SEG):
        tris.append((0, 1 + (i + 1) % SEG, 1 + i))
    return surf(name, shader, verts, norms, st, tris)


def quads(name, shader, quad_list):
    """Flat quads. Each is ((x0, y0, z0), (x1, y1, z1), u_repeat, v_repeat): rear/right corner to front/left corner,
    the height changing along x only. Texture top points forward (+x)."""
    verts, norms, st, tris = [], [], [], []
    for (x0, y0, z0), (x1, y1, z1), ur, vr in quad_list:
        base = len(verts)
        verts += [(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)]
        slope = (z1 - z0) / (x1 - x0)
        ln = math.hypot(slope, 1.0)
        norms += [(-slope / ln, 0.0, 1.0 / ln)] * 4
        st += [(ur, vr), (ur, 0.0), (0.0, 0.0), (0.0, vr)]
        tris += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    return surf(name, shader, verts, norms, st, tris)


def kart_model_bytes(half_w: int) -> bytes:
    w = half_w + 0.5
    deck = quads("deck", "progs/q3kart_deck", [((-60.5, -w, 4.4), (60.5, w, 4.4), 1.0, 1.0),
                                                ((-102.0, -w, 0.4), (-60.5, w, 4.4), 1.0, 0.4)])
    rails = quads("rails", "progs/q3kart_rail",
                  [((-60.5, half_w + 0.8, 6.4), (60.5, half_w + 6.2, 6.4), 1.0, 1.0),
                   ((-60.5, -half_w - 6.2, 6.4), (60.5, -half_w - 0.8, 6.4), 1.0, 1.0)])
    arrows = quads("arrows", "progs/q3kart_arrows", [((-101.0, -24.0, 0.75), (-61.0, 24.0, 4.65), 1.0, 1.0)])
    ring = annulus("ring", "progs/q3pad_ring", 44.0, 55.0, 4.8)
    core = disc("core", "progs/q3pad_core", 40.0, 4.65)
    return write_md3(f"q3kart{half_w}", [deck, rails, arrows, ring, core])


def model_bytes(name: str = "q3pad", skin: str = "q3pad") -> bytes:
    up = (0.0, 0.0, 1.0)
    # base: square plate 74x74, top at z 1.0, with 1-unit sides
    h = HALF
    top = [(-h, -h, 1.0), (h, -h, 1.0), (h, h, 1.0), (-h, h, 1.0)]
    bot = [(x, y, -0.5) for x, y, _ in top]
    verts = top + bot
    norms = [up] * 4 + [(0.0, 0.0, -1.0)] * 4
    st = [(0, 1), (1, 1), (1, 0), (0, 0)] + [(0, 1), (1, 1), (1, 0), (0, 0)]
    tris = [(0, 2, 1), (0, 3, 2)]
    for i in range(4):                       # sides
        a, b = i, (i + 1) % 4
        base = len(verts)
        verts += [top[a], top[b], bot[b], bot[a]]
        nx, ny = (top[a][0] + top[b][0]) / 2, (top[a][1] + top[b][1]) / 2
        ln = math.hypot(nx, ny)
        norms += [(nx / ln, ny / ln, 0.0)] * 4
        st += [(0.02, 0.02), (0.98, 0.02), (0.98, 0.05), (0.02, 0.05)]
        tris += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    base_s = surf("base", f"progs/{skin}_base", verts, norms, st, tris)

    # ring: annulus r 25..31 at z 1.3
    r0, r1, z = 25.0, 31.0, 1.3
    verts, norms, st, tris = [], [], [], []
    for i in range(SEG + 1):
        a = 2 * math.pi * i / SEG
        c, s = math.cos(a), math.sin(a)
        verts += [(c * r0, s * r0, z), (c * r1, s * r1, z)]
        norms += [up, up]
        st += [(i / SEG * 4, 1.0), (i / SEG * 4, 0.0)]
    for i in range(SEG):
        k = i * 2
        tris += [(k, k + 3, k + 1), (k, k + 2, k + 3)]
    ring_s = surf("ring", f"progs/{skin}_ring", verts, norms, st, tris)

    # core: disc r 23 at z 1.2, planar UVs centred so tcMod rotate spins it in place
    rc, z = 23.0, 1.2
    verts, norms, st, tris = [(0.0, 0.0, z)], [up], [(0.5, 0.5)], []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        verts.append((math.cos(a) * rc, math.sin(a) * rc, z))
        norms.append(up)
        st.append((0.5 + 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a)))
    for i in range(SEG):
        tris.append((0, 1 + (i + 1) % SEG, 1 + i))
    core_s = surf("core", f"progs/{skin}_core", verts, norms, st, tris)

    # beam: open cylinder r 24 from z 1.5 to 72 (texture row 0 = top)
    rb, z0, z1 = 24.0, 1.5, 72.0
    verts, norms, st, tris = [], [], [], []
    for i in range(SEG + 1):
        a = 2 * math.pi * i / SEG
        c, s = math.cos(a), math.sin(a)
        verts += [(c * rb, s * rb, z0), (c * rb * 0.92, s * rb * 0.92, z1)]
        norms += [(c, s, 0.0), (c, s, 0.0)]
        st += [(i / SEG * 2, 1.0), (i / SEG * 2, 0.0)]
    for i in range(SEG):
        k = i * 2
        tris += [(k, k + 1, k + 3), (k, k + 3, k + 2)]
    beam_s = surf("beam", f"progs/{skin}_beam", verts, norms, st, tris)
    return write_md3(name, [base_s, ring_s, core_s, beam_s])


def entries() -> dict[str, bytes]:
    base, base_glow = tex_base()
    karts = {f"progs/q3kart{w}.md3": kart_model_bytes(w) for w in KART_HALF_WIDTHS}
    return {
        **karts,
        "progs/q3skypad.md3": model_bytes("q3skypad", "q3sky"),
        "progs/q3sky_base_glow.png": png(blue(base_glow)),
        "progs/q3sky_ring.png": png(blue(tex_ring())),
        "progs/q3sky_core.png": png(blue(tex_core())),
        "progs/q3sky_beam.png": png(blue(tex_beam())),
        "progs/q3kart_deck.png": png(tex_kart_deck()),
        "progs/q3kart_rail.png": png(tex_kart_rail()),
        "progs/q3kart_arrows.png": png(tex_kart_arrows()),
        "progs/q3pad.md3": model_bytes(),
        "progs/q3pad_base.png": png(base),
        "progs/q3pad_base_glow.png": png(base_glow),
        "progs/q3pad_ring.png": png(tex_ring()),
        "progs/q3pad_core.png": png(tex_core()),
        "progs/q3pad_beam.png": png(tex_beam()),
        "scripts/q3pad.shader": SHADER.encode("ascii"),
    }


def build(out: Path, preview: Path | None) -> str:
    ent = entries()
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        for name, data in ent.items():
            if name.endswith(".png"):
                (preview / Path(name).name).write_bytes(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for name in sorted(ent):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.external_attr = FILE_ATTR
            if name.endswith(".png"):
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, ent[name])
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, ent[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out}: {len(ent)} files sha256 {digest}")
    return digest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--preview-dir", type=Path)
    ap.add_argument("--verify-repro", action="store_true")
    a = ap.parse_args()
    first = build(a.out, a.preview_dir)
    if a.verify_repro:
        tmp = a.out.with_suffix(".repro.pk3")
        second = build(tmp, None)
        tmp.unlink()
        if first != second:
            sys.exit("NOT REPRODUCIBLE: two builds differ")
        print("reproducible: OK")


if __name__ == "__main__":
    main()
