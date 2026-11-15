"""100% procedural PIL + NumPy texture & WAD2 generator for Golden West Casino & S Union Ave.

Strict engineering guarantees:
  - 0 photographic crops, 0 generic repeating window-grid facade sheets
  - 0 legacy bklan* / bk_* / {bk3_* / {chain / sky_bk names
  - Every texture matches ``^\\{?gwc_`` (plus WAD2-only compiler specials sky/clip/skip/trigger)
  - Every texture name length <= 15 chars
  - Every texture resolution is a power of 2 >= 64 (WAD2 lumps kept power-of-2 >= 64)
  - Diffuse albedo capped at RGB <= 205 (MAX_ALBEDO = 205) so sunny daylight + bounce never clips
  - Emissive textures pair with crisp ``<name>_glow.png`` fullbright maps
  - Purges Stones green felt (#157): all 4 casino table felts use burgundy-red felt + gold crest

Outputs:
  - ``BakersfieldQuake/textures/gwc_*.png``, ``{gwc_*.png``, ``*_glow.png``
  - ``source/mm_tools/out/maps/gw2.wad``
  - ``source/mm_tools/goldenwest/out/texture_sheet.jpg`` (labeled visual QA contact sheet)
  - ``source/mm_tools/goldenwest/out/texture_manifest.json`` (measured dimensions & max RGB stats)
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_THIS_DIR = Path(__file__).resolve().parent
_MM_TOOLS = _THIS_DIR.parent
ROOT = _MM_TOOLS.parent.parent

for _p in (str(_THIS_DIR), str(_MM_TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wad2  # noqa: E402

TEX_DIR = ROOT / "textures"
WAD_PATH = _MM_TOOLS / "out" / "maps" / "gw2.wad"
OUT_DIR = _THIS_DIR / "out"
SHEET_PATH = OUT_DIR / "texture_sheet.jpg"
MANIFEST_PATH = OUT_DIR / "texture_manifest.json"

MAX_ALBEDO = 205
MAX_NAME_LEN = 15
SPECIAL_WAD_ONLY = ("sky", "clip", "skip", "trigger")

# ==============================================================================
# 1. PROCEDURAL NOISE, COLOR & TYPOGRAPHY PRIMITIVES
# ==============================================================================

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
_FONT_CANDIDATES: Dict[str, Tuple[str, ...]] = {
    "bold": ("arialbd.ttf", "segoeuib.ttf", "calibrib.ttf", "tahomabd.ttf"),
    "black": ("ariblk.ttf", "impact.ttf", "arialbd.ttf"),
    "impact": ("impact.ttf", "ariblk.ttf", "arialbd.ttf"),
    "serif": ("georgiaz.ttf", "georgiab.ttf", "timesbd.ttf", "georgia.ttf"),
    "serif_bold": ("georgiab.ttf", "timesbd.ttf", "arialbd.ttf"),
    "script": ("segoesc.ttf", "brushsci.ttf", "lucida calligraphy.ttf", "georgiai.ttf", "arialbi.ttf"),
    "mono": ("consolab.ttf", "lucon.ttf", "courbd.ttf", "arialbd.ttf"),
    "reg": ("arial.ttf", "segoeui.ttf", "calibri.ttf"),
}


def font(style: str, size: int) -> ImageFont.FreeTypeFont:
    key = (style, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    fonts_dir = Path("C:/Windows/Fonts")
    for fname in _FONT_CANDIDATES.get(style, _FONT_CANDIDATES["bold"]):
        p = fonts_dir / fname
        if p.exists():
            try:
                f = ImageFont.truetype(str(p), size)
                _FONT_CACHE[key] = f
                return f
            except OSError:
                continue
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    style: str,
    max_w: float,
    max_h: float,
    start_size: int = 80,
    min_size: int = 10,
) -> ImageFont.FreeTypeFont:
    """Binary/linear shrink font until ``text`` fits cleanly within ``max_w x max_h``."""
    sz = start_size
    while sz > min_size:
        f = font(style, sz)
        l, t, r, b = draw.textbbox((0, 0), text, font=f)
        if (r - l) <= max_w and (b - t) <= max_h:
            return f
        sz -= max(1, (sz - min_size) // 10)
    return font(style, min_size)


def draw_centered(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    text: str,
    fnt: ImageFont.ImageFont,
    fill: Tuple[int, ...],
    outline: Optional[Tuple[int, ...]] = None,
    outline_w: int = 2,
) -> None:
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    tw, th = r - l, b - t
    x = cx - tw * 0.5 - l
    y = cy - th * 0.5 - t
    if outline is not None and outline_w > 0:
        draw.text((x, y), text, font=fnt, fill=fill, stroke_width=outline_w, stroke_fill=outline)
    else:
        draw.text((x, y), text, font=fnt, fill=fill)


def tile_value_noise(h: int, w: int, gy: int, gx: int, seed: int) -> np.ndarray:
    """Seamless periodic 2D smoothstep value noise tiled over ``h x w``."""
    rng = np.random.default_rng(seed)
    grid = rng.random((gy, gx), dtype=np.float32)
    yy = (np.arange(h, dtype=np.float32) / h) * gy
    xx = (np.arange(w, dtype=np.float32) / w) * gx
    iy0 = np.floor(yy).astype(np.int32) % gy
    ix0 = np.floor(xx).astype(np.int32) % gx
    iy1 = (iy0 + 1) % gy
    ix1 = (ix0 + 1) % gx
    fy = yy - np.floor(yy)
    fx = xx - np.floor(xx)
    fy = (fy * fy * (3.0 - 2.0 * fy))[:, None]
    fx = (fx * fx * (3.0 - 2.0 * fx))[None, :]
    c00 = grid[np.ix_(iy0, ix0)]
    c10 = grid[np.ix_(iy0, ix1)]
    c01 = grid[np.ix_(iy1, ix0)]
    c11 = grid[np.ix_(iy1, ix1)]
    return (c00 * (1.0 - fx) + c10 * fx) * (1.0 - fy) + (c01 * (1.0 - fx) + c11 * fx) * fy


def tile_fbm(h: int, w: int, base: int = 4, octaves: int = 4, seed: int = 1) -> np.ndarray:
    """Periodic multi-octave FBM in [0, 1]."""
    acc = np.zeros((h, w), dtype=np.float32)
    amp = 0.5
    norm = 0.0
    freq = base
    for i in range(octaves):
        gy = max(2, min(h // 2, freq))
        gx = max(2, min(w // 2, max(2, int(round(freq * (w / max(h, 1)))))))
        acc += amp * tile_value_noise(h, w, gy, gx, seed + i * 73)
        norm += amp
        amp *= 0.5
        freq *= 2
    return acc / max(norm, 1e-6)


def clamp_albedo(im: Image.Image, cap: int = MAX_ALBEDO) -> Image.Image:
    """Clamp RGB channels <= cap while leaving alpha intact."""
    if im.mode == "RGBA":
        arr = np.array(im, dtype=np.uint8)
        arr[..., :3] = np.minimum(arr[..., :3], cap)
        return Image.fromarray(arr, mode="RGBA")
    arr = np.array(im.convert("RGB"), dtype=np.uint8)
    arr = np.minimum(arr, cap)
    return Image.fromarray(arr, mode="RGB")


def enforce_transparent_border(
    im: Image.Image, pad_xy: int = 6, pad_top: int = 12, pad_bot: int = 4
) -> Image.Image:
    """Clear outer transparent margin so linear filtering / mipmaps under Fit() never wrap edges."""
    arr = np.array(im.convert("RGBA"), dtype=np.uint8)
    h, w, _ = arr.shape
    if pad_top > 0:
        arr[:pad_top, :, :] = 0
    if pad_bot > 0:
        arr[h - pad_bot :, :, :] = 0
    if pad_xy > 0:
        arr[:, :pad_xy, :] = 0
        arr[:, w - pad_xy :, :] = 0
    return Image.fromarray(arr, mode="RGBA")


def make_rgb_tex(
    w: int,
    h: int,
    base_rgb: Tuple[int, int, int],
    amp: float = 16.0,
    base_freq: int = 8,
    octaves: int = 4,
    seed: int = 10,
    speckle: float = 0.0,
    cap: int = MAX_ALBEDO,
) -> Image.Image:
    n = tile_fbm(h, w, base=base_freq, octaves=octaves, seed=seed) - 0.5
    arr = np.empty((h, w, 3), dtype=np.float32)
    arr[..., 0] = base_rgb[0] + n * amp
    arr[..., 1] = base_rgb[1] + n * amp
    arr[..., 2] = base_rgb[2] + n * (amp * 0.92)
    if speckle > 0.0:
        rng = np.random.default_rng(seed + 999)
        sp = (rng.random((h, w), dtype=np.float32) - 0.5) * speckle
        arr += sp[..., None]
    arr = np.clip(arr, 0, cap).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def mask_glow(im: Image.Image, threshold: int = 85, gain: float = 1.0) -> Image.Image:
    """Create crisp black-masked _glow image from bright inked graphics."""
    arr = np.array(im.convert("RGB"), dtype=np.float32)
    lum = np.max(arr, axis=-1)
    m = np.clip((lum - threshold) / 40.0, 0.0, 1.0)[..., None]
    out = np.clip(arr * gain * m, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="RGB")


def neon_sign_pair(
    w: int,
    h: int,
    bg_rgb: Tuple[int, int, int],
    lines: List[Tuple[str, str, int, Tuple[int, int, int], float]],
    border_rgb: Optional[Tuple[int, int, int]] = None,
    alpha_cutout: bool = False,
    cap: int = MAX_ALBEDO,
) -> Tuple[Image.Image, Image.Image]:
    """Render a neon / illuminated cabinet face + radiant fullbright _glow pair.

    ``lines`` entries: ``(text, font_style, font_size, rgb, y_frac)``
    """
    diff = Image.new("RGBA" if alpha_cutout else "RGB", (w, h), (0, 0, 0, 0) if alpha_cutout else bg_rgb)
    glow_bg = (0, 0, 0)
    glow = Image.new("RGB", (w, h), glow_bg)

    if not alpha_cutout:
        # Subtle panel texture on opaque sign backing
        tex = make_rgb_tex(w, h, bg_rgb, amp=10.0, base_freq=8, seed=hash(str(lines)) & 0xFFFF, cap=cap)
        diff.paste(tex)

    if border_rgb is not None and not alpha_cutout:
        d = ImageDraw.Draw(diff)
        g = ImageDraw.Draw(glow)
        d.rectangle([4, 4, w - 5, h - 5], outline=tuple(min(c, cap) for c in border_rgb), width=4)
        g.rectangle([4, 4, w - 5, h - 5], outline=border_rgb, width=4)

    # Halation pass on glow
    halo = Image.new("RGB", (w, h), (0, 0, 0))
    dh = ImageDraw.Draw(halo)
    dd = ImageDraw.Draw(diff)
    dg = ImageDraw.Draw(glow)

    for text, style, sz, col, yf in lines:
        f = fit_font(dd, text, style, w * 0.88, h * 0.65, start_size=sz, min_size=12)
        cy = h * yf
        # Outer colored drop/casing on diffuse
        casing = tuple(max(8, int(c * 0.30)) for c in col) + ((255,) if alpha_cutout else ())
        dcol = tuple(min(cap, int(c * 0.92)) for c in col) + ((255,) if alpha_cutout else ())
        draw_centered(dd, w * 0.5, cy, text, f, dcol, outline=casing, outline_w=3)
        draw_centered(dh, w * 0.5, cy, text, f, tuple(int(c * 0.62) for c in col), outline=tuple(int(c * 0.35) for c in col), outline_w=5)
        bright_core = tuple(min(255, int(c * 0.72 + 72)) for c in col)
        draw_centered(dg, w * 0.5, cy, text, f, bright_core, outline=col, outline_w=2)

    halo = halo.filter(ImageFilter.GaussianBlur(radius=max(3, min(w, h) // 28)))
    glow_arr = np.clip(np.array(glow, np.float32) + np.array(halo, np.float32) * 0.95, 0, 255).astype(np.uint8)
    return clamp_albedo(diff, cap=cap), Image.fromarray(glow_arr, mode="RGB")


def draw_starburst_suit(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, suit: str, fill: Tuple[int, int, int]) -> None:
    """Vector-draw a crisp poker suit watermark (spade, heart, diamond, club)."""
    if suit == "diamond":
        pts = [(cx, cy - r), (cx + r * 0.72, cy), (cx, cy + r), (cx - r * 0.72, cy)]
        draw.polygon(pts, fill=fill)
    elif suit == "heart":
        rr = r * 0.44
        draw.ellipse([cx - r * 0.85, cy - r * 0.65, cx - r * 0.85 + 2 * rr, cy - r * 0.65 + 2 * rr], fill=fill)
        draw.ellipse([cx + r * 0.85 - 2 * rr, cy - r * 0.65, cx + r * 0.85, cy - r * 0.65 + 2 * rr], fill=fill)
        draw.polygon([(cx - r * 0.86, cy - r * 0.1), (cx + r * 0.86, cy - r * 0.1), (cx, cy + r * 0.92)], fill=fill)
    elif suit == "club":
        rr = r * 0.38
        draw.ellipse([cx - rr, cy - r * 0.82, cx + rr, cy - r * 0.82 + 2 * rr], fill=fill)
        draw.ellipse([cx - r * 0.78, cy - rr * 0.6, cx - r * 0.78 + 2 * rr, cy + rr * 1.4], fill=fill)
        draw.ellipse([cx + r * 0.78 - 2 * rr, cy - rr * 0.6, cx + r * 0.78, cy + rr * 1.4], fill=fill)
        draw.polygon([(cx, cy + rr * 0.2), (cx - r * 0.26, cy + r * 0.88), (cx + r * 0.26, cy + r * 0.88)], fill=fill)
    else:  # spade
        rr = r * 0.42
        draw.polygon([(cx, cy - r * 0.92), (cx - r * 0.82, cy + r * 0.14), (cx + r * 0.82, cy + r * 0.14)], fill=fill)
        draw.ellipse([cx - r * 0.84, cy - rr * 0.5, cx - r * 0.84 + 2 * rr, cy + rr * 1.5], fill=fill)
        draw.ellipse([cx + r * 0.84 - 2 * rr, cy - rr * 0.5, cx + r * 0.84, cy + rr * 1.5], fill=fill)
        draw.polygon([(cx, cy + rr * 0.3), (cx - r * 0.26, cy + r * 0.92), (cx + r * 0.26, cy + r * 0.92)], fill=fill)


# ==============================================================================
# 2. REGISTRY
# ==============================================================================

FULL_TEX: Dict[str, Image.Image] = {}
GLOW_TEX: Dict[str, Image.Image] = {}
WAD_TEX: Dict[str, Image.Image] = {}
CATALOG_ROWS: List[Dict[str, object]] = []


def reg(
    name: str,
    im: Image.Image,
    purpose: str,
    glow: Optional[Image.Image] = None,
    wad_div: int = 2,
    cap_albedo: bool = True,
) -> None:
    """Validate naming, dimensions, albedo cap, and enqueue texture for disk + WAD2 output."""
    assert re.match(r"^\{?gwc_", name), f"Invalid Golden West texture prefix: {name!r}"
    assert len(name) <= MAX_NAME_LEN, f"Texture name exceeds {MAX_NAME_LEN} chars: {name!r} ({len(name)})"
    w, h = im.size
    assert (w & (w - 1)) == 0 and (h & (h - 1)) == 0, f"{name}: non-power-of-2 size {w}x{h}"
    assert w >= 64 and h >= 64, f"{name}: size < 64 ({w}x{h})"

    if cap_albedo:
        im = clamp_albedo(im, MAX_ALBEDO)

    arr = np.array(im.convert("RGBA" if im.mode == "RGBA" else "RGB"), dtype=np.uint8)
    max_rgb = int(arr[..., :3].max())
    assert not cap_albedo or max_rgb <= MAX_ALBEDO, f"{name}: albedo {max_rgb} > {MAX_ALBEDO}"

    FULL_TEX[name] = im
    if glow is not None:
        assert glow.size == im.size, f"{name}: glow size {glow.size} != diffuse {im.size}"
        GLOW_TEX[name] = glow.convert("RGB")

    # Keep WAD2 mip dimensions powers of 2 >= 64
    eff_div = wad_div
    while eff_div > 1 and (w // eff_div < 64 or h // eff_div < 64):
        eff_div //= 2
    ww, hh = w // eff_div, h // eff_div
    if eff_div > 1:
        resample = Image.Resampling.NEAREST if name.startswith("{") else Image.Resampling.LANCZOS
        w_im = im.resize((ww, hh), resample)
    else:
        w_im = im
    if name.startswith("{") and w_im.mode != "RGBA":
        w_im = w_im.convert("RGBA")
    WAD_TEX[name] = w_im

    CATALOG_ROWS.append(
        {
            "name": name,
            "width": w,
            "height": h,
            "wad_width": ww,
            "wad_height": hh,
            "alpha": bool(name.startswith("{")),
            "glow": bool(glow is not None),
            "max_rgb": max_rgb,
            "purpose": purpose,
        }
    )


# ==============================================================================
# 3. CATEGORY BUILDERS
# ==============================================================================


def build_streets_and_site() -> None:
    """Roads, sidewalks, S Union concrete slab & brick median, markings, dirt & landscape."""
    # S Union cracked sun-bleached asphalt
    n1 = tile_fbm(256, 256, base=8, octaves=4, seed=101) - 0.5
    rng = np.random.default_rng(101)
    agg = (rng.random((256, 256), dtype=np.float32) - 0.5) * 14.0
    asph = np.empty((256, 256, 3), dtype=np.float32)
    asph[..., 0] = 66 + n1 * 18 + agg
    asph[..., 1] = 67 + n1 * 18 + agg
    asph[..., 2] = 69 + n1 * 17 + agg
    im = Image.fromarray(np.clip(asph, 0, MAX_ALBEDO).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    # Hairline asphalt tarred stress cracks
    for pts in [
        [(18, 0), (34, 48), (28, 102), (44, 178), (38, 256)],
        [(142, 0), (132, 62), (156, 138), (144, 212), (150, 256)],
        [(0, 124), (74, 132), (168, 118), (256, 128)],
    ]:
        d.line(pts, fill=(44, 44, 46), width=2)
    reg("gwc_asph", im, "Weathered cracked Bakersfield asphalt roadway")

    # S Union middle-lane light grey poured concrete slab w/ expansion joints (#016, #044, #046)
    conc_s = make_rgb_tex(256, 256, (152, 149, 143), amp=14.0, base_freq=8, seed=102, speckle=7.0)
    arr_cs = np.array(conc_s, dtype=np.float32)
    # Subtle tire-track darkening in central bands
    x_pos = np.linspace(0, 1, 256, dtype=np.float32)[None, :]
    track = np.exp(-((x_pos - 0.28) / 0.11) ** 2) + np.exp(-((x_pos - 0.72) / 0.11) ** 2)
    arr_cs -= (track[..., None] * 10.0)
    im = Image.fromarray(np.clip(arr_cs, 0, MAX_ALBEDO).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for y in (0, 128):
        d.rectangle([0, y, 255, y + 3], fill=(92, 90, 86))
    d.rectangle([0, 0, 2, 255], fill=(98, 96, 92))
    reg("gwc_concslab", im, "S Union Ave poured grey concrete middle-lane slab w/ joints")

    # Broom-finish sidewalk concrete
    im = make_rgb_tex(256, 256, (176, 171, 162), amp=12.0, base_freq=8, seed=103, speckle=6.0)
    d = ImageDraw.Draw(im)
    for g in (0, 128):
        d.line([(0, g), (255, g)], fill=(122, 118, 110), width=3)
        d.line([(g, 0), (g, 255)], fill=(128, 124, 116), width=2)
    reg("gwc_conc", im, "Broom-finish concrete sidewalk & apron slab")

    # Curbs
    im = make_rgb_tex(128, 128, (162, 158, 150), amp=14.0, base_freq=6, seed=104, speckle=6.0)
    ImageDraw.Draw(im).line([(0, 64), (127, 64)], fill=(116, 112, 104), width=2)
    reg("gwc_curb", im, "Weathered poured concrete curb")

    im = make_rgb_tex(128, 128, (168, 42, 38), amp=16.0, base_freq=6, seed=105, speckle=8.0)
    reg("gwc_curbred", im, "Painted red fire-lane concrete curb")

    # Red/pink herringbone brick median pavers (#021, #046)
    im = Image.new("RGB", (256, 256), (92, 86, 82))
    d = ImageDraw.Draw(im)
    rng_b = np.random.default_rng(106)
    pal_b = [(164, 78, 70), (178, 92, 82), (150, 68, 62), (186, 108, 96), (172, 86, 76)]
    step = 32
    for gy in range(-2, 10):
        for gx in range(-2, 10):
            x0, y0 = gx * step, gy * step
            c1 = pal_b[int(rng_b.integers(0, len(pal_b)))]
            c2 = pal_b[int(rng_b.integers(0, len(pal_b)))]
            if (gx + gy) % 2 == 0:
                d.rectangle([x0 + 2, y0 + 2, x0 + step - 3, y0 + step // 2 - 2], fill=c1)
                d.rectangle([x0 + 2, y0 + step // 2 + 1, x0 + step - 3, y0 + step - 3], fill=c2)
            else:
                d.rectangle([x0 + 2, y0 + 2, x0 + step // 2 - 2, y0 + step - 3], fill=c1)
                d.rectangle([x0 + step // 2 + 1, y0 + 2, x0 + step - 3, y0 + step - 3], fill=c2)
    arr_b = np.array(im, dtype=np.float32) + (tile_fbm(256, 256, 16, 3, 106) - 0.5)[..., None] * 14.0
    reg("gwc_brick", Image.fromarray(np.clip(arr_b, 0, MAX_ALBEDO).astype(np.uint8)), "Red/pink herringbone brick median pavers")

    # Crisp thermoplastic line markings (replaces bk_wline / bk_yline)
    im = make_rgb_tex(128, 128, (64, 65, 67), amp=10.0, base_freq=6, seed=107, speckle=8.0)
    ImageDraw.Draw(im).rectangle([40, 0, 88, 127], fill=(198, 198, 194))
    reg("gwc_wline", im, "White thermoplastic traffic lane divider stripe", wad_div=1)

    im = make_rgb_tex(128, 128, (64, 65, 67), amp=10.0, base_freq=6, seed=108, speckle=8.0)
    d = ImageDraw.Draw(im)
    d.rectangle([24, 0, 54, 127], fill=(196, 152, 34))
    d.rectangle([74, 0, 104, 127], fill=(196, 152, 34))
    reg("gwc_yline", im, "Double yellow centerline traffic stripe", wad_div=1)

    im = make_rgb_tex(256, 256, (66, 67, 69), amp=12.0, base_freq=8, seed=109, speckle=8.0)
    d = ImageDraw.Draw(im)
    for x in range(16, 256, 64):
        d.rectangle([x, 12, x + 36, 243], fill=(196, 196, 192))
    reg("gwc_xwalk", im, "Continental white pedestrian crosswalk bars on asphalt")

    im = make_rgb_tex(128, 256, (66, 67, 69), amp=12.0, base_freq=6, seed=110, speckle=8.0)
    d = ImageDraw.Draw(im)
    # White straight + left turn arrow stencil on asphalt (#044)
    d.rectangle([56, 86, 72, 236], fill=(196, 196, 192))
    d.polygon([(64, 24), (32, 92), (96, 92)], fill=(196, 196, 192))
    reg("gwc_turnarr", im, "Painted white lane directional arrow on asphalt")

    # CA-99 BUS shield on green Caltrans sign background
    im = make_rgb_tex(128, 128, (24, 90, 48), amp=8.0, base_freq=4, seed=111)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, 114, 114], radius=16, fill=(196, 196, 194), outline=(28, 96, 52), width=3)
    d.rounded_rectangle([18, 18, 110, 110], radius=13, fill=(24, 90, 48))
    draw_centered(d, 64, 34, "BUSINESS", font("bold", 13), (198, 198, 194))
    draw_centered(d, 64, 66, "99", font("black", 42), (198, 198, 194))
    draw_centered(d, 64, 96, "UNION AVE", font("bold", 12), (198, 198, 194))
    reg("gwc_ca99", im, "CA-99 Business S Union Ave guide shield", wad_div=1)

    # Dry San Joaquin Valley dirt, dry grass, irrigated lawn, bark mulch
    reg("gwc_dirt", make_rgb_tex(256, 256, (152, 130, 102), amp=24.0, base_freq=8, seed=112, speckle=14.0), "Dry San Joaquin Valley dirt & gravel")
    n_dg = tile_fbm(256, 256, base=12, octaves=4, seed=113) - 0.5
    rng_dg = np.random.default_rng(113)
    straw = (rng_dg.random((256, 256), dtype=np.float32) - 0.5) * 26.0
    dg_arr = np.stack(
        [154 + n_dg * 26 + straw, 136 + n_dg * 22 + straw * 0.9, 92 + n_dg * 16 + straw * 0.6],
        axis=-1,
    )
    reg("gwc_drygrs", Image.fromarray(np.clip(dg_arr, 0, MAX_ALBEDO).astype(np.uint8)), "Sun-dried San Joaquin yellow-tan scrub grass")

    im = make_rgb_tex(256, 256, (68, 114, 48), amp=20.0, base_freq=10, seed=114, speckle=16.0)
    reg("gwc_lawn", im, "Irrigated green turf lawn")

    im = make_rgb_tex(128, 128, (86, 52, 34), amp=26.0, base_freq=12, seed=115, speckle=18.0)
    reg("gwc_mulch", im, "Dark redwood bark planter mulch")


def build_foliage_and_fences() -> None:
    """Alpha cutout trees, palm fronds/bark/skirt, chain-link, green mesh, wrought iron, breeze block."""
    # Bark (palm ring scars + brown fissure grain)
    im = make_rgb_tex(128, 256, (108, 92, 76), amp=24.0, base_freq=8, seed=201, speckle=12.0)
    d = ImageDraw.Draw(im)
    for y in range(8, 256, 14):
        d.line([(0, y), (127, y + 3)], fill=(72, 60, 48), width=2)
    reg("gwc_bark", im, "Ring-scarred palm & oak tree bark")

    # Shaggy tan palm skirt petticoat (for Mexican Fan Palms along S Union)
    im = make_rgb_tex(128, 128, (146, 124, 92), amp=26.0, base_freq=10, seed=202, speckle=16.0)
    d = ImageDraw.Draw(im)
    for y in range(0, 128, 8):
        for x in range(0, 128, 6):
            d.line([(x, y), (x + (x % 5) - 2, min(127, y + 10))], fill=(96, 80, 56), width=1)
    reg("gwc_palmhat", im, "Dry shaggy palm petticoat skirt")

    # Solid hedge & canopy leaf textures
    reg("gwc_hedge", make_rgb_tex(128, 128, (46, 86, 38), amp=28.0, base_freq=14, seed=203, speckle=24.0), "Clipped dark boxwood hedge foliage")
    reg("gwc_leaf", make_rgb_tex(128, 128, (64, 114, 48), amp=32.0, base_freq=12, seed=204, speckle=26.0), "Sunlit green broadleaf tree foliage")

    # {gwc_palmfr: alpha-cutout lush radial palm frond cluster (inset cleanly inside transparent margin)
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 128, 240
    for ang_deg in range(-74, 76, 7):
        rad = math.radians(ang_deg - 90)
        ex = cx + math.cos(rad) * 106.0
        ey = cy + math.sin(rad) * 200.0
        col = (52 + (abs(ang_deg) % 24), 104 + (abs(ang_deg) % 22), 38, 255)
        d.polygon([(cx - 5, cy), (cx + 5, cy), (ex, ey)], fill=col)
        for frac in np.linspace(0.24, 0.96, 14):
            px = cx + (ex - cx) * frac
            py = cy + (ey - cy) * frac
            flen = 20.0 * (1.0 - 0.35 * abs(frac - 0.65))
            d.polygon([(px, py), (px + math.cos(rad + 0.55) * flen, py + math.sin(rad + 0.55) * flen), (px + math.cos(rad) * 7, py + math.sin(rad) * 7)], fill=(66, 122, 46, 255))
            d.polygon([(px, py), (px + math.cos(rad - 0.55) * flen, py + math.sin(rad - 0.55) * flen), (px + math.cos(rad) * 7, py + math.sin(rad) * 7)], fill=(48, 94, 34, 255))
    im = enforce_transparent_border(im, pad_xy=6, pad_top=12, pad_bot=5)
    reg("{gwc_palmfr", im, "Alpha-cutout radial Mexican Fan Palm frond fan")

    # {gwc_tree1: Mexican Fan Palm silhouette (sturdy trunk + dry skirt + lush weeping frond crown)
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(118, 250), (138, 250), (133, 72), (123, 72)], fill=(104, 88, 72, 255))
    d.polygon([(118, 80), (138, 80), (144, 114), (112, 114)], fill=(142, 120, 88, 255))
    for i in range(36):
        ang = (i / 36.0) * math.tau
        length = 56.0 + (i % 3) * 12.0
        mx = 128 + math.cos(ang) * (length * 0.55)
        my = 68 + math.sin(ang) * (length * 0.38) - 6
        ex = 128 + math.cos(ang) * length
        ey = 72 + math.sin(ang) * (length * 0.66) + 10
        col = (52 + (i % 3) * 12, 102 + (i % 4) * 10, 38, 255)
        d.line([(128, 68), (mx, my), (ex, ey)], fill=col, width=7)
        for t in (0.4, 0.7, 0.9):
            px = (1 - t) * mx + t * ex
            py = (1 - t) * my + t * ey
            d.line([(px, py), (px + math.cos(ang + 0.6) * 13, py + math.sin(ang + 0.6) * 13 + 5)], fill=col, width=4)
            d.line([(px, py), (px + math.cos(ang - 0.6) * 13, py + math.sin(ang - 0.6) * 13 + 5)], fill=(44, 88, 32, 255), width=4)
    im = enforce_transparent_border(im, pad_xy=6, pad_top=12, pad_bot=4)
    reg("{gwc_tree1", im, "Alpha-cutout Washingtonia Mexican Fan Palm silhouette")

    # {gwc_tree2: Valley Oak / Bradford Pear rich solid broadleaf silhouette
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(114, 250), (142, 250), (134, 150), (122, 150)], fill=(84, 66, 50, 255))
    d.line([(128, 182), (94, 134)], fill=(84, 66, 50, 255), width=8)
    d.line([(128, 174), (164, 132)], fill=(84, 66, 50, 255), width=8)
    # Dense core dark shadow foliage so canopy reads solid from distance (clear of top margin)
    d.ellipse([48, 36, 208, 172], fill=(38, 76, 30, 255))
    rng_t = np.random.default_rng(207)
    for _ in range(160):
        a = rng_t.uniform(0, math.tau)
        rr = rng_t.uniform(0, 76)
        bx = 128 + math.cos(a) * rr * 1.02
        by = 104 + math.sin(a) * rr * 0.72
        rad = rng_t.uniform(13, 22)
        tint = int(rng_t.integers(-14, 24))
        col = (max(26, 58 + tint), min(168, 108 + tint), max(22, 42 + tint // 2), 255)
        d.ellipse([bx - rad, by - rad, bx + rad, by + rad], fill=col)
    im = enforce_transparent_border(im, pad_xy=6, pad_top=12, pad_bot=4)
    reg("{gwc_tree2", im, "Alpha-cutout California Valley Oak broadleaf tree silhouette")

    # {gwc_tree3: Mediterranean Cypress lush columnar tree
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([118, 220, 138, 250], fill=(80, 62, 46, 255))
    rng_c = np.random.default_rng(208)
    for y in range(28, 226, 3):
        frac = (y - 28) / 198.0
        half_w = 8 + 38 * math.sin(frac * math.pi * 0.88)
        d.ellipse([128 - half_w * 0.72, y - 6, 128 + half_w * 0.72, y + 6], fill=(34, 72, 32, 255))
        for _ in range(6):
            px = 128 + rng_c.uniform(-half_w * 0.74, half_w * 0.74)
            rad = rng_c.uniform(7, 13)
            sh = int(rng_c.integers(-10, 18))
            col = (max(22, 44 + sh), min(148, 88 + sh), max(20, 40 + sh // 2), 255)
            d.ellipse([px - rad, y - rad * 0.75, px + rad, y + rad * 0.75], fill=col)
    im = enforce_transparent_border(im, pad_xy=6, pad_top=12, pad_bot=4)
    reg("{gwc_tree3", im, "Alpha-cutout columnar Mediterranean Cypress tree silhouette")

    # {gwc_canopy: seamless edge-to-edge tileable tree canopy foliage (safe with Tile() on canopy cubes)
    im_can = make_rgb_tex(256, 256, (44, 86, 36), amp=24.0, base_freq=10, seed=209, speckle=18.0).convert("RGBA")
    d_can = ImageDraw.Draw(im_can)
    rng_can = np.random.default_rng(209)
    for _ in range(240):
        lx, ly = rng_can.integers(0, 256), rng_can.integers(0, 256)
        rad = int(rng_can.integers(10, 22))
        tint = int(rng_can.integers(-16, 26))
        col = (max(26, 56 + tint), min(168, 108 + tint), max(22, 42 + tint // 2), 255)
        for ox in (-256, 0, 256):
            for oy in (-256, 0, 256):
                if -24 <= lx + ox <= 280 and -24 <= ly + oy <= 280:
                    d_can.ellipse([lx + ox - rad, ly + oy - rad, lx + ox + rad, ly + oy + rad], fill=col)
    # Subtle dappled airy edge openings (~14% transparent gaps, dense >85% foliage core)
    arr_can = np.array(im_can, dtype=np.uint8)
    dapple = tile_fbm(256, 256, base=12, octaves=3, seed=219)
    arr_can[dapple < 0.28, 3] = 0
    reg("{gwc_canopy", Image.fromarray(arr_can, mode="RGBA"), "Seamless tileable broadleaf tree canopy foliage")

    # {gwc_chain: galvanized diamond chain-link cutout
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wire = (156, 160, 166, 255)
    for off in range(-128, 256, 24):
        d.line([(off, 0), (off + 128, 128)], fill=wire, width=3)
        d.line([(off, 128), (off + 128, 0)], fill=(138, 142, 148, 255), width=3)
    d.rectangle([0, 0, 127, 5], fill=(144, 148, 152, 255))
    reg("{gwc_chain", im, "Alpha-cutout galvanized diamond chain-link fence")

    # {gwc_greenmesh: 891 S Union dark-green privacy mesh over chain-link
    im = make_rgb_tex(128, 128, (30, 74, 42), amp=12.0, base_freq=10, seed=210, speckle=10.0).convert("RGBA")
    arr_gm = np.array(im, dtype=np.uint8)
    # Fine woven breathable pores (opaque > 82% privacy screen with subtle chain-link shadow)
    yy, xx = np.mgrid[0:128, 0:128]
    pore = ((yy % 4 == 0) & (xx % 4 == 0))
    arr_gm[pore, 3] = 40
    im_gm = Image.fromarray(arr_gm, mode="RGBA")
    d = ImageDraw.Draw(im_gm)
    for off in range(-128, 256, 32):
        d.line([(off, 0), (off + 128, 128)], fill=(44, 92, 56, 255), width=1)
    d.rectangle([0, 0, 127, 5], fill=(124, 128, 132, 255))
    reg("{gwc_greenmesh", im_gm, "891 S Union Ave dark-green privacy mesh chain-link fence", wad_div=1)

    # {gwc_ironfence: Spear-top dark wrought-iron perimeter fence
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    iron = (32, 38, 36, 255)
    hi = (60, 68, 66, 255)
    # Top & bottom horizontal rails
    d.rectangle([0, 38, 255, 48], fill=iron)
    d.rectangle([0, 228, 255, 240], fill=iron)
    # Vertical spear-top pickets every 32px
    for x in range(16, 256, 32):
        d.rectangle([x - 4, 24, x + 4, 255], fill=iron)
        d.line([(x - 2, 26), (x - 2, 255)], fill=hi, width=1)
        # Spear finial
        d.polygon([(x, 4), (x + 8, 22), (x + 3, 28), (x - 3, 28), (x - 8, 22)], fill=iron)
    reg("{gwc_ironfence", im, "Alpha-cutout dark spear-top wrought iron perimeter fence")

    # {gwc_slat: Dark balcony / railing balustrade
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 8], fill=(38, 40, 44, 255))
    d.rectangle([0, 118, 127, 127], fill=(38, 40, 44, 255))
    for x in range(8, 128, 16):
        d.rectangle([x - 2, 8, x + 2, 118], fill=(42, 44, 48, 255))
    reg("{gwc_slat", im, "Alpha-cutout wrought-iron vertical picket railing", wad_div=1)

    # {gwc_breezeblk: Sunland Motel white diamond perforated breeze-block wall
    im = Image.new("RGBA", (128, 128), (196, 193, 186, 255))
    # Subtle stone speckle on concrete ribs
    sp_b = make_rgb_tex(128, 128, (192, 189, 182), amp=12.0, base_freq=8, seed=213, speckle=8.0).convert("RGBA")
    im.paste(sp_b)
    d = ImageDraw.Draw(im)
    # Outer mortar seams (2x2 blocks per 128px tile)
    for bx in (0, 64):
        for by in (0, 64):
            cx, cy = bx + 32, by + 32
            d.rectangle([bx, by, bx + 63, by + 63], outline=(148, 145, 138, 255), width=2)
            # Diamond cutout center + corner triangle openings (transparent alpha=0)
            d.polygon([(cx, cy - 18), (cx + 18, cy), (cx, cy + 18), (cx - 18, cy)], fill=(0, 0, 0, 0))
            d.polygon([(bx + 7, by + 7), (bx + 22, by + 7), (bx + 7, by + 22)], fill=(0, 0, 0, 0))
            d.polygon([(bx + 56, by + 7), (bx + 41, by + 7), (bx + 56, by + 22)], fill=(0, 0, 0, 0))
            d.polygon([(bx + 7, by + 56), (bx + 22, by + 56), (bx + 7, by + 41)], fill=(0, 0, 0, 0))
            d.polygon([(bx + 56, by + 56), (bx + 41, by + 56), (bx + 56, by + 41)], fill=(0, 0, 0, 0))
    reg("{gwc_breezeblk", im, "Sunland Motel off-white perforated diamond breeze-block screen", wad_div=1)


def build_metals_trims_and_props() -> None:
    """Metals, ducts, swamp cooler, roll-up door, lift, tires, cars, solid trims."""
    reg("gwc_steel", make_rgb_tex(128, 128, (64, 68, 74), amp=10.0, base_freq=6, seed=301, speckle=6.0), "Charcoal painted structural steel poles & frames")

    # Galvanized spangled steel
    im = make_rgb_tex(128, 128, (158, 162, 168), amp=22.0, base_freq=14, seed=302, speckle=12.0)
    reg("gwc_galv", im, "Galvanized spangled sheet metal")

    # HVAC cross-broken duct
    im = make_rgb_tex(128, 128, (148, 152, 156), amp=14.0, base_freq=8, seed=303, speckle=8.0)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 127], outline=(94, 98, 102), width=3)
    d.line([(4, 4), (123, 123)], fill=(122, 126, 130), width=2)
    d.line([(123, 4), (4, 123)], fill=(172, 176, 180), width=2)
    reg("gwc_duct", im, "Galvanized rooftop cross-broken HVAC ductwork", wad_div=1)

    # Galvanized swamp cooler louver panel (#076, #080)
    im = make_rgb_tex(128, 128, (144, 148, 152), amp=14.0, base_freq=8, seed=304)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 127], outline=(98, 102, 106), width=8)
    for y in range(14, 114, 10):
        d.rectangle([12, y, 115, y + 4], fill=(64, 68, 72))
        d.line([(12, y + 5), (115, y + 5)], fill=(176, 180, 184), width=1)
    reg("gwc_swamp", im, "Residential galvanized rooftop swamp-cooler louver grille", wad_div=1)

    # Beige commercial HVAC housing
    im = make_rgb_tex(128, 128, (172, 162, 142), amp=12.0, base_freq=6, seed=305, speckle=6.0)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 12, 119, 115], outline=(126, 118, 102), width=2)
    for y in range(28, 96, 8):
        d.line([(20, y), (74, y)], fill=(96, 88, 76), width=3)
    reg("gwc_hvac", im, "Sun-faded beige commercial rooftop HVAC cabinet", wad_div=1)

    # Corrugated commercial roll-up garage door
    im = make_rgb_tex(256, 256, (176, 178, 178), amp=8.0, base_freq=6, seed=306)
    d = ImageDraw.Draw(im)
    for y in range(0, 256, 16):
        d.rectangle([0, y, 255, y + 4], fill=(134, 136, 138))
        d.rectangle([0, y + 5, 255, y + 8], fill=(192, 194, 194))
    d.rectangle([96, 224, 160, 240], fill=(72, 74, 78))
    reg("gwc_rollup", im, "Ribbed horizontal roll-up service bay garage door")

    # Hydraulic 2-post car lift column (Ramos Tires interior)
    im = make_rgb_tex(128, 256, (148, 36, 36), amp=10.0, base_freq=6, seed=307)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 255], outline=(92, 22, 22), width=4)
    d.rectangle([40, 16, 88, 240], fill=(54, 58, 62))
    # Yellow/black safety stripes at carriage base
    for i in range(6):
        c = (194, 152, 28) if i % 2 == 0 else (34, 34, 36)
        d.rectangle([8, 196 + i * 8, 119, 203 + i * 8], fill=c)
    reg("gwc_carlift", im, "Hydraulic 2-post red/charcoal car lift column")

    # Black radial rubber tires
    im = make_rgb_tex(128, 128, (36, 36, 38), amp=8.0, base_freq=10, seed=308, speckle=6.0)
    d = ImageDraw.Draw(im)
    for y in range(0, 128, 32):
        d.rectangle([0, y, 127, y + 3], fill=(20, 20, 22))
        for x in range(4, 128, 12):
            d.line([(x, y + 6), (x + 6, y + 26)], fill=(24, 24, 26), width=2)
    reg("gwc_tire", im, "Molded black rubber automotive tire tread & stack", wad_div=1)

    # Solid utility / vehicle materials (capped <= 205)
    reg("gwc_white", make_rgb_tex(128, 128, (196, 194, 188), amp=6.0, base_freq=4, seed=309), "Clean off-white architectural fascia & trim")
    reg("gwc_dark", make_rgb_tex(128, 128, (38, 40, 44), amp=8.0, base_freq=6, seed=310), "Charcoal dark structural trim & mullions")
    reg("gwc_red", make_rgb_tex(128, 128, (158, 34, 36), amp=10.0, base_freq=6, seed=311), "Deep crimson painted architectural trim")
    # Rich brushed warm brass-gold urn material
    gu_arr = np.array(make_rgb_tex(128, 128, (188, 142, 48), amp=12.0, base_freq=6, seed=312, speckle=6.0), dtype=np.float32)
    sheen = (0.5 + 0.5 * np.sin(np.linspace(0, math.pi * 2.0, 128, dtype=np.float32)))[None, :, None]
    gu_arr += sheen * np.array([16.0, 14.0, 6.0], dtype=np.float32)
    reg("gwc_goldurn", Image.fromarray(np.clip(gu_arr, 0, MAX_ALBEDO).astype(np.uint8)), "Brushed warm brass-gold urn & trim accent")
    reg("gwc_carred", make_rgb_tex(128, 128, (152, 28, 34), amp=8.0, base_freq=4, seed=313), "Gloss burgundy-red painted vehicle body")
    reg("gwc_carwht", make_rgb_tex(128, 128, (194, 194, 190), amp=6.0, base_freq=4, seed=314), "Clean pearl-white painted vehicle body")
    reg("gwc_carblu", make_rgb_tex(128, 128, (36, 68, 126), amp=8.0, base_freq=4, seed=315), "Metallic navy-blue painted vehicle body")
    reg("gwc_carsil", make_rgb_tex(128, 128, (154, 158, 164), amp=10.0, base_freq=4, seed=316), "Metallic silver painted vehicle body")
    reg("gwc_carwin", make_rgb_tex(128, 128, (36, 46, 56), amp=12.0, base_freq=4, seed=317), "Tinted automotive windshield & window glass")

    # Utility transformer cabinet & dumpster
    im = make_rgb_tex(128, 128, (68, 92, 74), amp=10.0, base_freq=6, seed=318)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 117, 117], outline=(44, 62, 48), width=3)
    d.rectangle([72, 24, 104, 46], fill=(192, 148, 36), outline=(28, 28, 28), width=2)
    for y in range(62, 102, 7):
        d.line([(20, y), (62, y)], fill=(42, 58, 46), width=2)
    reg("gwc_utilbox", im, "Green steel utility transformer cabinet w/ warning placard", wad_div=1)

    im = make_rgb_tex(128, 128, (46, 84, 58), amp=12.0, base_freq=6, seed=319)
    d = ImageDraw.Draw(im)
    for x in range(16, 120, 24):
        d.rectangle([x, 12, x + 6, 115], fill=(32, 62, 42))
    d.rectangle([0, 0, 127, 14], fill=(32, 34, 36))
    reg("gwc_dumpstr", im, "Ribbed green steel commercial waste dumpster", wad_div=1)


def build_traffic_and_street_signs() -> None:
    """7 Bakersfield street name blades, Stop sign, One Way, Pedestrian & Traffic signals."""
    street_blades = [
        ("gwc_sbelle", "E BELLE TERRACE", "E Belle Terrace street blade"),
        ("gwc_sunion", "S UNION AVE", "S Union Ave street blade"),
        ("gwc_sadams", "ADAMS ST", "Adams St street blade"),
        ("gwc_strin", "TRINITY AVE", "Trinity Ave street blade"),
        ("gwc_sdel", "DELAWARE ST", "Delaware St street blade"),
        ("gwc_smari", "MARIPOSA AVE", "Mariposa Ave street blade"),
        ("gwc_samad", "AMADOR AVE", "Amador Ave street blade"),
    ]
    for name, label, desc in street_blades:
        im = make_rgb_tex(512, 128, (22, 92, 50), amp=8.0, base_freq=6, seed=hash(name) & 0xFFFF)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, 505, 121], radius=14, outline=(196, 198, 194), width=5)
        f = fit_font(d, label, "bold", 450, 82, start_size=56, min_size=24)
        draw_centered(d, 256, 64, label, f, (200, 200, 196))
        reg(name, im, desc)

    # {gwc_stopsign: octagonal red STOP cutout
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = 128.0, 122.0
    oct_pts = [
        (c + r * math.cos(math.radians(22.5 + 45 * i)), c + r * math.sin(math.radians(22.5 + 45 * i)))
        for i in range(8)
    ]
    d.polygon(oct_pts, fill=(196, 196, 192, 255))
    r2 = 112.0
    oct_in = [
        (c + r2 * math.cos(math.radians(22.5 + 45 * i)), c + r2 * math.sin(math.radians(22.5 + 45 * i)))
        for i in range(8)
    ]
    d.polygon(oct_in, fill=(166, 26, 30, 255))
    draw_centered(d, 128, 128, "STOP", font("impact", 72), (200, 200, 196, 255))
    reg("{gwc_stopsign", im, "Alpha-cutout MUTCD octagonal red STOP sign")

    # ONE WAY directional sign
    im = make_rgb_tex(256, 128, (196, 196, 192), amp=4.0, base_freq=4, seed=402)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, 251, 123], radius=8, outline=(26, 26, 28), width=4)
    d.polygon([(20, 64), (74, 24), (74, 40), (232, 40), (232, 88), (74, 88), (74, 104)], fill=(24, 24, 26))
    draw_centered(d, 144, 64, "ONE WAY", font("impact", 34), (198, 198, 194))
    reg("gwc_oneway", im, "MUTCD black-and-white ONE WAY directional arrow sign")

    # Traffic signal lenses + glow + pedestrian signal + speed limit 45
    for suf, col_d, col_g, desc in [
        ("gwc_tsig_g", (28, 154, 78), (40, 245, 130), "Traffic signal green circular lens"),
        ("gwc_tsig_y", (184, 134, 24), (252, 196, 32), "Traffic signal amber circular lens"),
        ("gwc_tsig_r", (176, 34, 28), (255, 58, 40), "Traffic signal red circular lens"),
    ]:
        diff = Image.new("RGB", (128, 128), (28, 30, 32))
        glow = Image.new("RGB", (128, 128), (0, 0, 0))
        ImageDraw.Draw(diff).ellipse([16, 16, 112, 112], fill=col_d, outline=(18, 18, 20), width=4)
        ImageDraw.Draw(glow).ellipse([20, 20, 108, 108], fill=col_g)
        glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
        reg(suf, diff, desc, glow=glow, wad_div=1)

    diff = Image.new("RGB", (128, 128), (22, 22, 24))
    glow = Image.new("RGB", (128, 128), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    draw_centered(dd, 64, 42, "WALK", font("bold", 26), (192, 196, 198))
    draw_centered(dd, 64, 86, "WAIT", font("bold", 24), (186, 84, 34))
    draw_centered(dg, 64, 42, "WALK", font("bold", 26), (235, 245, 255))
    draw_centered(dg, 64, 86, "WAIT", font("bold", 24), (255, 124, 42))
    reg("gwc_pedx", diff, "Crosswalk pedestrian WALK/WAIT illuminated signal", glow=glow, wad_div=1)

    im = make_rgb_tex(128, 128, (196, 196, 192), amp=4.0, base_freq=4, seed=410)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 4, 121, 123], radius=8, outline=(26, 26, 28), width=4)
    draw_centered(d, 64, 26, "SPEED", font("bold", 20), (24, 24, 26))
    draw_centered(d, 64, 48, "LIMIT", font("bold", 20), (24, 24, 26))
    draw_centered(d, 64, 88, "45", font("impact", 52), (24, 24, 26))
    reg("gwc_spd45", im, "Speed Limit 45 regulatory sign", wad_div=1)


def _draw_rubble_stone(
    w: int,
    h: int,
    base_colors: List[Tuple[int, int, int]],
    mortar: Tuple[int, int, int],
    seed: int,
) -> Image.Image:
    im = Image.new("RGB", (w, h), mortar)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    row_h = 32
    for row_i, y0 in enumerate(range(0, h, row_h)):
        x = -int((row_i * 41) % 64)
        while x < w:
            bw = int(rng.choice([44, 56, 68, 84]))
            col = base_colors[int(rng.integers(0, len(base_colors)))]
            col = tuple(int(np.clip(c + rng.integers(-8, 9), 20, MAX_ALBEDO)) for c in col)
            d.rectangle([x + 2, y0 + 2, x + bw - 2, y0 + row_h - 2], fill=col)
            # Crisp stone bevel highlight + shadow
            d.line([(x + 2, y0 + 2), (x + bw - 2, y0 + 2)], fill=tuple(min(MAX_ALBEDO, c + 14) for c in col), width=2)
            d.line([(x + 2, y0 + row_h - 3), (x + bw - 2, y0 + row_h - 3)], fill=tuple(max(20, c - 18) for c in col), width=2)
            x += bw
    arr = np.array(im, dtype=np.float32)
    tex_n = (tile_fbm(h, w, 14, 4, seed + 50) - 0.5) * 18.0
    rng_s = np.random.default_rng(seed + 51)
    sp = (rng_s.random((h, w), dtype=np.float32) - 0.5) * 10.0
    arr += tex_n[..., None] + sp[..., None]
    return Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8), "RGB")


def build_casino_architecture_and_interiors() -> None:
    """Golden West Casino stone, board-and-batten gable, roof shingles, ceilings, carpet, granite, signs."""
    # Courtyard stamped flagstone pavers (#113)
    im = _draw_rubble_stone(
        256, 256,
        [(176, 152, 118), (168, 144, 110), (184, 160, 126), (160, 138, 106)],
        mortar=(116, 100, 80), seed=501,
    )
    reg("gwc_flag", im, "Stamped sandstone courtyard flagstone pavers")

    # Cream exterior & warm buff interior split-face rubble stone
    reg(
        "gwc_stone",
        _draw_rubble_stone(
            256, 256,
            [(184, 174, 152), (176, 164, 142), (192, 182, 162), (168, 156, 134)],
            mortar=(124, 114, 96), seed=502,
        ),
        "Golden West exterior cream split-face rubble stone masonry",
    )
    reg(
        "gwc_istone",
        _draw_rubble_stone(
            256, 256,
            [(174, 150, 114), (166, 142, 108), (182, 158, 122), (156, 134, 102)],
            mortar=(108, 92, 72), seed=503,
        ),
        "Interior warm golden-buff split-face rubble stone feature wall",
    )

    # Dark espresso vertical board-and-batten gable siding (#113)
    im = make_rgb_tex(256, 256, (68, 48, 36), amp=12.0, base_freq=10, seed=504, speckle=6.0)
    d = ImageDraw.Draw(im)
    for x in range(0, 256, 32):
        d.rectangle([x, 0, x + 7, 255], fill=(82, 58, 44))
        d.line([(x + 8, 0), (x + 8, 255)], fill=(42, 28, 20), width=2)
    reg("gwc_batten", im, "Dark espresso vertical wood board-and-batten gable siding")

    # Dark structural wood beam
    im = make_rgb_tex(128, 256, (58, 40, 30), amp=14.0, base_freq=6, seed=505)
    d = ImageDraw.Draw(im)
    for x in range(12, 128, 22):
        d.line([(x, 0), (x, 255)], fill=(44, 30, 22), width=2)
    reg("gwc_beam", im, "Dark stained espresso structural timber beam", wad_div=1)

    # Terracotta barrel / architectural roof shingles (#113)
    im = Image.new("RGB", (256, 256), (112, 52, 38))
    d = ImageDraw.Draw(im)
    rng_sh = np.random.default_rng(506)
    for r_i, y in enumerate(range(0, 256, 24)):
        x_off = (r_i % 2) * 16
        for x in range(-16, 256, 32):
            c = (
                int(np.clip(144 + rng_sh.integers(-14, 15), 80, 175)),
                int(np.clip(72 + rng_sh.integers(-10, 11), 40, 100)),
                int(np.clip(52 + rng_sh.integers(-8, 9), 30, 75)),
            )
            d.rectangle([x + x_off + 1, y + 1, x + x_off + 30, y + 22], fill=c)
        d.line([(0, y + 23), (255, y + 23)], fill=(68, 30, 22), width=2)
    arr_sh = np.array(im, dtype=np.float32) + (tile_fbm(256, 256, 12, 3, 506) - 0.5)[..., None] * 14.0
    reg("gwc_shingle", Image.fromarray(np.clip(arr_sh, 0, MAX_ALBEDO).astype(np.uint8)), "Terracotta architectural/barrel casino roof shingles")

    # Flat TPO/gravel roof
    reg("gwc_tpo", make_rgb_tex(256, 256, (148, 146, 140), amp=16.0, base_freq=8, seed=507, speckle=10.0), "Weathered light-grey commercial flat TPO roof")

    # Warm Golden West exterior stucco & fluted purple pylon trim
    reg("gwc_stucco", make_rgb_tex(256, 256, (186, 168, 138), amp=12.0, base_freq=10, seed=508, speckle=8.0), "Golden West warm sandstone-tan exterior stucco")

    im = make_rgb_tex(128, 128, (64, 34, 96), amp=8.0, base_freq=6, seed=509)
    d = ImageDraw.Draw(im)
    for x in range(0, 128, 16):
        d.rectangle([x, 0, x + 5, 127], fill=(48, 24, 74))
        d.rectangle([x + 6, 0, x + 10, 127], fill=(86, 48, 122))
    reg("gwc_purple", im, "Fluted royal-purple steel pylon & accent cladding", wad_div=1)

    # Guard booth siding & bronze storefront glass
    im = make_rgb_tex(256, 256, (176, 172, 162), amp=10.0, base_freq=8, seed=510)
    d = ImageDraw.Draw(im)
    d.rectangle([28, 36, 228, 146], fill=(42, 54, 62), outline=(64, 60, 56), width=6)
    d.line([(128, 36), (128, 146)], fill=(64, 60, 56), width=4)
    d.rectangle([16, 146, 240, 158], fill=(124, 118, 108))
    reg("gwc_booth", im, "Security guard kiosk wall & sliding service window")

    im = make_rgb_tex(128, 128, (48, 66, 76), amp=14.0, base_freq=4, seed=511)
    d = ImageDraw.Draw(im)
    d.line([(12, 110), (112, 12)], fill=(78, 98, 112), width=10)
    d.line([(28, 118), (118, 28)], fill=(66, 86, 98), width=5)
    reg("gwc_glass", im, "Tinted bronze-teal commercial storefront glass", wad_div=1)

    # Acoustic 2x4 & 2x2 drop-tile ceilings + LED troffer
    im = make_rgb_tex(256, 256, (178, 176, 168), amp=8.0, base_freq=18, seed=512, speckle=12.0)
    d = ImageDraw.Draw(im)
    for y in (0, 128):
        d.rectangle([0, y, 255, y + 4], fill=(128, 126, 120))
    for x in (0, 255):
        d.rectangle([x, 0, min(255, x + 3), 255], fill=(128, 126, 120))
    reg("gwc_ceil2x4", im, "Acoustic 2x4 suspended drop-tile casino ceiling")

    im = make_rgb_tex(256, 256, (176, 174, 166), amp=8.0, base_freq=18, seed=513, speckle=12.0)
    d = ImageDraw.Draw(im)
    for g in (0, 128):
        d.rectangle([0, g, 255, g + 4], fill=(126, 124, 118))
        d.rectangle([g, 0, g + 4, 255], fill=(126, 124, 118))
    reg("gwc_ceil2x2", im, "Acoustic 2x2 tegular drop-tile lounge ceiling")

    diff = Image.new("RGB", (256, 128), (192, 190, 184))
    glow = Image.new("RGB", (256, 128), (0, 0, 0))
    ImageDraw.Draw(diff).rectangle([0, 0, 255, 127], outline=(112, 112, 110), width=6)
    for y in range(18, 112, 18):
        ImageDraw.Draw(diff).line([(8, y), (247, y)], fill=(154, 154, 148), width=2)
    ImageDraw.Draw(glow).rectangle([10, 10, 245, 117], fill=(246, 240, 224))
    reg("gwc_troffer", diff, "2x4 recessed warm-white LED troffer luminaire", glow=glow)

    # Casino burgundy/charcoal/gold medallion swirl carpet (#167)
    im = make_rgb_tex(256, 256, (94, 24, 30), amp=12.0, base_freq=10, seed=515, speckle=8.0)
    d = ImageDraw.Draw(im)
    gold_w = (158, 124, 54)
    dark_w = (46, 14, 18)
    for cx, cy in [(64, 64), (192, 64), (64, 192), (192, 192), (128, 128)]:
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], outline=gold_w, width=3)
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], outline=dark_w, width=4)
        d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(134, 96, 40))
    for i in range(0, 256, 64):
        d.arc([i - 32, 0, i + 32, 64], 0, 180, fill=gold_w, width=2)
        d.arc([i - 32, 128, i + 32, 192], 180, 360, fill=gold_w, width=2)
    reg("gwc_carpet", im, "Burgundy, charcoal & gold floral scroll casino carpet")

    # Lobby taupe/travertine floor tile (#167)
    im = make_rgb_tex(256, 256, (166, 154, 134), amp=14.0, base_freq=8, seed=516)
    d = ImageDraw.Draw(im)
    for g in (0, 128):
        d.rectangle([0, g, 255, g + 3], fill=(116, 108, 94))
        d.rectangle([g, 0, g + 3, 255], fill=(116, 108, 94))
    reg("gwc_tile", im, "Travertine warm-taupe lobby & aisle ceramic floor tile")

    # Tan bar counter ceramic apron tile (#127, #160)
    im = Image.new("RGB", (256, 256), (112, 96, 78))
    d = ImageDraw.Draw(im)
    rng_bt = np.random.default_rng(517)
    for r_i, y in enumerate(range(0, 256, 32)):
        xo = (r_i % 2) * 32
        for x in range(-32, 256, 64):
            sh = int(rng_bt.integers(-10, 11))
            col = (168 + sh, 136 + sh, 102 + sh)
            d.rectangle([x + xo + 2, y + 2, x + xo + 61, y + 29], fill=col)
    arr_bt = np.array(im, dtype=np.float32) + (tile_fbm(256, 256, 10, 3, 517) - 0.5)[..., None] * 10.0
    reg("gwc_bartile", Image.fromarray(np.clip(arr_bt, 0, MAX_ALBEDO).astype(np.uint8)), "Tan glazed ceramic bar counter apron tile")

    # Mottled dark granite bar top (#112) & speckled cream cage ledge (#152)
    im_g = make_rgb_tex(256, 256, (38, 42, 48), amp=18.0, base_freq=14, seed=518, speckle=22.0)
    arr_g = np.array(im_g, dtype=np.uint8)
    rng_g = np.random.default_rng(518)
    fleck = rng_g.random((256, 256)) > 0.94
    arr_g[fleck] = [96, 114, 134]
    reg("gwc_granite", Image.fromarray(arr_g, "RGB"), "Mottled dark charcoal/blue-flecked polished bar granite")

    im_cl = make_rgb_tex(256, 256, (174, 168, 158), amp=14.0, base_freq=14, seed=519, speckle=18.0)
    arr_cl = np.array(im_cl, dtype=np.uint8)
    rng_cl = np.random.default_rng(519)
    arr_cl[rng_cl.random((256, 256)) > 0.92] = [88, 84, 80]
    reg("gwc_cledge", Image.fromarray(arr_cl, "RGB"), "Speckled cream granite Cashier cage counter ledge")

    # Hardwood & padded leather & interior wainscot
    im = make_rgb_tex(256, 256, (82, 46, 28), amp=14.0, base_freq=6, seed=520)
    d = ImageDraw.Draw(im)
    for x in range(8, 256, 16):
        d.line([(x, 0), (x, 255)], fill=(62, 34, 20), width=2)
    reg("gwc_wood", im, "Dark mahogany hardwood rail & interior cabinet trim")

    im = make_rgb_tex(128, 128, (34, 34, 38), amp=8.0, base_freq=16, seed=521, speckle=6.0)
    reg("gwc_leather", im, "Matte black vinyl/leather table bolster rail", wad_div=1)

    im = make_rgb_tex(256, 256, (178, 164, 140), amp=10.0, base_freq=8, seed=522)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 148, 255, 255], fill=(74, 42, 26))
    d.rectangle([0, 140, 255, 148], fill=(96, 56, 36))
    for x in range(16, 256, 64):
        d.rectangle([x, 162, x + 48, 240], outline=(54, 30, 18), width=3)
    reg("gwc_wainscot", im, "Warm cream drywall over raised mahogany wainscot")

    # Corrugated Cashier cage shutter & illuminated CASHIER window (#167, #171)
    im = make_rgb_tex(256, 256, (158, 160, 164), amp=8.0, base_freq=6, seed=523)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, 255], outline=(98, 100, 104), width=8)
    for y in range(12, 244, 12):
        d.rectangle([8, y, 247, y + 4], fill=(116, 118, 122))
        d.line([(8, y + 5), (247, y + 5)], fill=(182, 184, 188), width=1)
    reg("gwc_cageshut", im, "Corrugated metal Cashier cage security roll shutter")

    diff = Image.new("RGB", (512, 128), (38, 28, 22))
    glow = Image.new("RGB", (512, 128), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    # Overhead burgundy & brass CASHIER marquee plaque with generous border padding
    dd.rounded_rectangle([12, 12, 499, 115], radius=10, fill=(64, 20, 28), outline=(176, 140, 48), width=4)
    dd.rounded_rectangle([20, 20, 491, 107], radius=6, outline=(128, 98, 32), width=2)
    dg.rounded_rectangle([12, 12, 499, 115], radius=10, outline=(196, 152, 54), width=3)
    for dx in (48, 463):
        pts = [(dx, 56), (dx + 8, 64), (dx, 72), (dx - 8, 64)]
        dd.polygon(pts, fill=(186, 150, 54))
        dg.polygon(pts, fill=(224, 180, 68))
    f_cash = fit_font(dd, "CASHIER", "serif_bold", 356, 70, start_size=62)
    draw_centered(dd, 256, 62, "CASHIER", f_cash, (198, 166, 68), outline=(36, 12, 16), outline_w=2)
    draw_centered(dg, 256, 62, "CASHIER", f_cash, (255, 214, 86))
    reg("gwc_cashier", diff, "Illuminated Golden West Cashier overhead cage banner", glow=glow)


def build_casino_felts_and_signage() -> None:
    """Pylon sign, LED sign, Blackjack Lounge neon, Security/Employees/PushToOpen, GWC chips & 4 burgundy felts."""
    # Pylon crown (#109): fluted purple cabinet, "Golden West" gold script, lit gold/red "CASINO"
    diff = make_rgb_tex(512, 256, (66, 30, 96), amp=10.0, base_freq=8, seed=601)
    glow = Image.new("RGB", (512, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    # Pylon arch border
    dd.rounded_rectangle([12, 12, 499, 243], radius=36, outline=(186, 44, 74), width=8)
    dg.rounded_rectangle([12, 12, 499, 243], radius=36, outline=(255, 58, 92), width=6)
    # "Golden West" cursive + "CASINO"
    f_gw = fit_font(dd, "Golden West", "script", 440, 95, start_size=70)
    draw_centered(dd, 256, 86, "Golden West", f_gw, (198, 168, 66), outline=(120, 32, 48), outline_w=3)
    draw_centered(dg, 256, 86, "Golden West", f_gw, (255, 224, 102), outline=(210, 48, 72), outline_w=2)
    f_cas = fit_font(dd, "CASINO", "impact", 420, 88, start_size=72)
    draw_centered(dd, 256, 178, "CASINO", f_cas, (198, 172, 82), outline=(168, 32, 54), outline_w=4)
    draw_centered(dg, 256, 178, "CASINO", f_cas, (255, 232, 128), outline=(255, 42, 68), outline_w=4)
    glow = Image.fromarray(
        np.clip(
            np.array(glow, np.float32) + np.array(glow.filter(ImageFilter.GaussianBlur(4)), np.float32) * 0.65,
            0, 255,
        ).astype(np.uint8)
    )
    reg("gwc_pyltop", diff, "Golden West Casino fluted purple & gold/neon pylon crown", glow=glow)

    # Programmable LED sign (#109 / Prompt): "POKER · BLACKJACK · BACCARAT"
    diff, glow = neon_sign_pair(
        512, 256, (20, 14, 34),
        [
            ("POKER  •  BLACKJACK", "black", 40, (255, 198, 52), 0.30),
            ("BACCARAT", "black", 46, (88, 224, 255), 0.62),
            ("OPEN 24 HOURS  •  JACKPOTS", "bold", 24, (255, 92, 118), 0.85),
        ],
        border_rgb=(176, 48, 210),
    )
    reg("gwc_pylled", diff, "Programmable LED marquee: POKER BLACKJACK BACCARAT", glow=glow)

    # Blackjack Lounge blue neon (both opaque soffit + alpha cutout)
    bj_d, bj_g = neon_sign_pair(512, 128, (30, 32, 38), [("Blackjack", "script", 74, (74, 216, 255), 0.50)])
    reg("gwc_bjneon", bj_d, "Blackjack bright cyan-blue neon script sign on soffit", glow=bj_g)
    bja_d, bja_g = neon_sign_pair(512, 128, (0, 0, 0), [("Blackjack", "script", 74, (74, 216, 255), 0.50)], alpha_cutout=True)
    reg("{gwc_bjneon", bja_d, "Alpha-cutout Blackjack cyan-blue neon tube sign", glow=bja_g)

    lg_d, lg_g = neon_sign_pair(512, 128, (30, 32, 38), [("Lounge", "script", 74, (74, 216, 255), 0.50)])
    reg("gwc_lgneon", lg_d, "Lounge bright cyan-blue neon script sign on soffit", glow=lg_g)
    lga_d, lga_g = neon_sign_pair(512, 128, (0, 0, 0), [("Lounge", "script", 74, (74, 216, 255), 0.50)], alpha_cutout=True)
    reg("{gwc_lgneon", lga_d, "Alpha-cutout Lounge cyan-blue neon tube sign", glow=lga_g)

    # SECURITY backlit plaque (#124)
    diff = make_rgb_tex(256, 128, (194, 186, 164), amp=6.0, base_freq=4, seed=605)
    glow = Image.new("RGB", (256, 128), (225, 212, 178))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    dd.rectangle([0, 0, 255, 127], outline=(42, 34, 28), width=8)
    dg.rectangle([0, 0, 255, 127], outline=(0, 0, 0), width=10)
    draw_centered(dd, 128, 64, "SECURITY", font("impact", 48), (36, 32, 28))
    draw_centered(dg, 128, 64, "SECURITY", font("impact", 48), (18, 16, 14))
    reg("gwc_security", diff, "Backlit cream box plaque reading SECURITY", glow=glow)

    # EMPLOYEES ONLY door sign (#160)
    im = make_rgb_tex(256, 512, (62, 38, 26), amp=12.0, base_freq=8, seed=606)
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, 243, 499], outline=(40, 24, 16), width=8)
    d.rounded_rectangle([32, 128, 224, 206], radius=8, fill=(28, 24, 22), outline=(176, 142, 54), width=4)
    draw_centered(d, 128, 152, "EMPLOYEES", font("bold", 26), (196, 166, 68))
    draw_centered(d, 128, 184, "ONLY", font("bold", 26), (196, 166, 68))
    d.ellipse([202, 268, 224, 290], fill=(176, 144, 58))
    reg("gwc_emponly", im, "Dark walnut door with gold EMPLOYEES ONLY plaque")

    # PUSH TO OPEN door decal (#154)
    im = make_rgb_tex(256, 128, (46, 42, 40), amp=6.0, base_freq=4, seed=607)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 22, 247, 105], fill=(166, 26, 32), outline=(196, 194, 190), width=3)
    draw_centered(d, 128, 64, "PUSH TO OPEN", font("impact", 34), (198, 198, 194))
    reg("gwc_pushtoop", im, "Red storefront door bar decal: PUSH TO OPEN")

    # GWC chip rack (#151, #152)
    im = Image.new("RGB", (256, 128), (38, 36, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 249, 121], outline=(146, 152, 158), width=4)
    stack_cols = [
        (194, 164, 42),   # $5 yellow
        (194, 164, 42),
        (114, 34, 42),    # $25 burgundy
        (46, 98, 164),    # $2 blue
        (30, 32, 36),     # $100 black
        (188, 186, 182),  # $1 white
    ]
    for si, col in enumerate(stack_cols):
        x0 = 16 + si * 38
        for y in range(14, 114, 6):
            d.rectangle([x0, y, x0 + 30, y + 4], fill=col, outline=(20, 20, 22), width=1)
        draw_centered(d, x0 + 15, 64, "GWC", font("bold", 10), (200, 198, 190))
    reg("gwc_chiprack", im, "Acrylic casino dealer chip rack w/ GWC chip stacks")

    # Hanging casino table number sign [11] (#169)
    im = Image.new("RGB", (128, 128), (34, 24, 22))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, 119, 119], radius=12, outline=(178, 144, 56), width=5)
    draw_centered(d, 64, 28, "TABLE", font("bold", 18), (196, 164, 64))
    draw_centered(d, 64, 72, "11", font("impact", 58), (198, 194, 184))
    reg("gwc_tblnum", im, "Dark bronze & gold casino table placard [11]", wad_div=1)

    # Sports TV screen + banners + billboard + US flag
    diff = Image.new("RGB", (256, 128), (24, 26, 30))
    glow = Image.new("RGB", (256, 128), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    for dr, g_scale in ((dd, 0.78), (dg, 1.0)):
        dr.rectangle([8, 8, 247, 100], fill=(int(48 * g_scale), int(124 * g_scale), int(56 * g_scale)))
        for x in range(28, 236, 28):
            dr.line([(x, 8), (x, 100)], fill=(int(180 * g_scale), int(196 * g_scale), int(180 * g_scale)), width=2)
        dr.rectangle([8, 100, 247, 120], fill=(int(24 * g_scale), int(48 * g_scale), int(112 * g_scale)))
        draw_centered(dr, 128, 110, "LIVE SPORTS  •  BAKERSFIELD", font("bold", 14), (int(240 * g_scale), int(224 * g_scale), int(120 * g_scale)))
    dd.rectangle([0, 0, 255, 127], outline=(24, 24, 26), width=6)
    reg("gwc_tvscr", diff, "Casino sports lounge flat-screen live broadcast display", glow=glow)

    im = make_rgb_tex(512, 128, (98, 24, 34), amp=8.0, base_freq=6, seed=610)
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 505, 121], outline=(186, 148, 54), width=5)
    f_n1 = fit_font(d, "GOLDEN WEST CASINO", "serif", 456, 48, start_size=34)
    f_n2 = fit_font(d, "LIVE ACTION SPORTS LOUNGE  •  24 HOURS", "bold", 464, 34, start_size=22)
    draw_centered(d, 256, 44, "GOLDEN WEST CASINO", f_n1, (198, 174, 76))
    draw_centered(d, 256, 88, "LIVE ACTION SPORTS LOUNGE  •  24 HOURS", f_n2, (198, 196, 190))
    reg("gwc_nflban", im, "Golden West Casino live action sports banner")

    im = make_rgb_tex(256, 256, (104, 24, 34), amp=8.0, base_freq=6, seed=611)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 12, 243, 243], radius=16, outline=(186, 152, 56), width=6)
    draw_centered(d, 128, 66, "PLAY", font("impact", 52), (198, 172, 68))
    draw_centered(d, 128, 126, "EAT", font("impact", 52), (198, 196, 190))
    draw_centered(d, 128, 186, "WIN!", font("impact", 56), (198, 172, 68))
    reg("gwc_goldwin", im, "Golden West promo graphic: PLAY EAT WIN")

    diff = Image.new("RGB", (256, 256), (34, 24, 22))
    glow = Image.new("RGB", (256, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    for dr, sc in ((dd, 0.8), (dg, 1.0)):
        dr.rectangle([8, 8, 247, 56], fill=(int(142 * sc), int(32 * sc), int(38 * sc)))
        draw_centered(dr, 128, 32, "CAFE & GRILL", font("impact", 32), (int(244 * sc), int(212 * sc), int(96 * sc)))
        items = ["BURGERS & FRIES   $11", "CARNITAS TACOS    $10", "STEAK & EGGS      $15", "COLD DRAFT BEER   $6"]
        for i, it in enumerate(items):
            draw_centered(dr, 128, 88 + i * 40, it, font("mono", 18), (int(238 * sc), int(234 * sc), int(224 * sc)))
    reg("gwc_menu", diff, "Backlit Golden West Cafe & Grill kitchen menu board", glow=glow)

    im = make_rgb_tex(512, 256, (74, 22, 68), amp=8.0, base_freq=6, seed=613)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, 503, 247], outline=(192, 156, 52), width=6)
    f_b1 = fit_font(d, "GOLDEN WEST CASINO", "serif", 452, 64, start_size=44)
    f_b2 = fit_font(d, "POKER  •  BLACKJACK  •  BACCARAT", "black", 456, 46, start_size=28)
    f_b3 = fit_font(d, "1001 S UNION AVE  •  OPEN 24 HOURS", "bold", 456, 42, start_size=26)
    draw_centered(d, 256, 66, "GOLDEN WEST CASINO", f_b1, (200, 176, 72))
    draw_centered(d, 256, 132, "POKER  •  BLACKJACK  •  BACCARAT", f_b2, (200, 198, 194))
    draw_centered(d, 256, 198, "1001 S UNION AVE  •  OPEN 24 HOURS", f_b3, (194, 162, 66))
    reg("gwc_bboard", im, "Golden West Casino highway billboard")

    # {gwc_usflag: 50-star US & California flag cutout
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 13 stripes on left-anchored billowing flag silhouette inside top 180px
    sh = 13
    for i in range(13):
        col = (158, 34, 42, 255) if i % 2 == 0 else (196, 196, 192, 255)
        d.rectangle([8, 16 + i * sh, 246, 16 + (i + 1) * sh - 1], fill=col)
    d.rectangle([8, 16, 108, 16 + 7 * sh], fill=(28, 48, 96, 255))
    for ry in range(24, 16 + 7 * sh - 4, 14):
        for rx in range(18, 102, 16):
            d.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=(198, 198, 196, 255))
    reg("{gwc_usflag", im, "Alpha-cutout US flag banner")

    # BURGUNDY-RED CASINO GAMING FELTS (ZERO #157 green Stones felt!)
    def make_burgundy_felt(title: str, subtitle: str, mode: str) -> Image.Image:
        w, h = 512, 256
        im = make_rgb_tex(w, h, (118, 22, 32), amp=10.0, base_freq=18, seed=700 + len(mode), speckle=10.0)
        d = ImageDraw.Draw(im)
        wm_col = (94, 18, 26)
        suits = ("spade", "heart", "diamond", "club")
        for r_i, y in enumerate(range(24, h, 44)):
            for c_i, x in enumerate(range(28, w, 48)):
                draw_starburst_suit(d, x + (r_i % 2) * 20, y, 10, suits[(r_i + c_i) % 4], wm_col)
        gold = (190, 156, 62)
        gold_dim = (146, 116, 44)
        # Outer mahogany wood & black leather border hint along bottom edge + gold betting rail
        d.arc([24, 18, w - 24, h * 2 - 28], 185, 355, fill=gold, width=4)
        d.arc([44, 38, w - 44, h * 2 - 48], 188, 352, fill=gold_dim, width=2)
        # Center Golden West Casino spade-chip crest
        draw_starburst_suit(d, w * 0.5, 62, 20, "spade", (64, 12, 18))
        d.ellipse([w * 0.5 - 26, 36, w * 0.5 + 26, 88], outline=gold, width=3)
        draw_centered(d, w * 0.5, 62, "GWC", font("serif", 16), gold)
        draw_centered(d, w * 0.5, 104, "GOLDEN WEST CASINO", font("serif", 22), gold)
        draw_centered(d, w * 0.5, 130, title, font("black", 24), (198, 186, 140))
        draw_centered(d, w * 0.5, 154, subtitle, font("bold", 14), gold)

        if mode == "bj":
            for bx in range(96, 420, 64):
                d.ellipse([bx - 16, 186, bx + 16, 218], outline=gold, width=3)
                d.ellipse([bx - 8, 224, bx + 8, 240], fill=(182, 148, 42), outline=(40, 14, 18), width=2)
        elif mode == "bacc":
            d.arc([88, 168, 424, 248], 0, 360, fill=gold, width=3)
            for lbl, px in [("PLAYER", 136), ("BANKER", 256), ("DRAGON 7", 376)]:
                d.rounded_rectangle([px - 46, 188, px + 46, 222], radius=8, outline=gold, width=2)
                f_bl = fit_font(d, lbl, "bold", 78, 24, start_size=13)
                draw_centered(d, px, 205, lbl, f_bl, (198, 192, 164))
        elif mode == "uth":
            for py, tag in [(182, "TRIPS"), (208, "ANTE"), (234, "PLAY")]:
                draw_centered(d, 56, py, tag, font("bold", 10), gold)
            for px in range(106, 412, 64):
                for py in (182, 208, 234):
                    d.ellipse([px - 10, py - 9, px + 10, py + 9], outline=gold, width=2)
        else:  # poker
            d.rounded_rectangle([196, 184, 316, 228], radius=10, outline=gold_dim, width=2)
            draw_centered(d, 256, 206, "HOLD'EM POT", font("bold", 15), gold)
        return im

    reg("gwc_fpoker", make_burgundy_felt("TEXAS HOLD'EM POKER", "DROP BOX  •  NO LIMIT / LIMIT", "poker"), "Burgundy-red Texas Hold'em poker felt w/ gold GWC crest")
    reg("gwc_fbj", make_burgundy_felt("BLACKJACK PAYS 3 TO 2", "DEALER MUST STAND ON ALL 17s", "bj"), "Burgundy-red Blackjack felt w/ player boxes & Buster circles")
    reg("gwc_fbacc", make_burgundy_felt("EZ BACCARAT", "PLAYER  •  BANKER  •  TIE 8 TO 1  •  PANDA 8", "bacc"), "Burgundy-red EZ Baccarat felt w/ Dragon 7 / Panda 8")
    reg("gwc_futh", make_burgundy_felt("ULTIMATE TEXAS HOLD'EM", "TRIPS  •  ANTE  •  BLIND  •  PLAY", "uth"), "Burgundy-red Ultimate Texas Hold'em felt w/ betting circles")


def build_neighborhood_surfaces_and_signs() -> None:
    """S Union Ave stucco/siding variants, motel/business signage, Playfair mural & Century Glass."""
    # Stucco / siding / shingles / CMU / blinds
    reg("gwc_wstucco", make_rgb_tex(256, 256, (192, 188, 178), amp=12.0, base_freq=10, seed=801, speckle=7.0), "California off-white troweled exterior stucco")
    reg("gwc_bstucco", make_rgb_tex(256, 256, (182, 166, 138), amp=14.0, base_freq=10, seed=802, speckle=8.0), "Warm cream-buff commercial exterior stucco")
    reg("gwc_rstucco", make_rgb_tex(256, 256, (166, 108, 86), amp=14.0, base_freq=10, seed=803, speckle=8.0), "Warm adobe-terracotta exterior stucco")
    reg("gwc_slatstuc", make_rgb_tex(256, 256, (88, 104, 122), amp=12.0, base_freq=10, seed=804, speckle=7.0), "Compas Auto slate blue-grey painted stucco")
    reg("gwc_crmstuc", make_rgb_tex(256, 256, (194, 186, 164), amp=10.0, base_freq=10, seed=805, speckle=6.0), "Sunlit cream-ivory residential/senior living stucco")

    # Residential composition asphalt roof shingles (#076, #080)
    im = make_rgb_tex(256, 256, (86, 78, 72), amp=14.0, base_freq=14, seed=806, speckle=18.0)
    d = ImageDraw.Draw(im)
    for r_i, y in enumerate(range(0, 256, 32)):
        xo = (r_i % 2) * 32
        d.line([(0, y), (255, y)], fill=(48, 44, 40), width=3)
        for x in range(-32, 256, 64):
            d.line([(x + xo, y), (x + xo, y + 31)], fill=(54, 50, 46), width=2)
    reg("gwc_resshing", im, "Weathered charcoal-brown residential asphalt composition shingles")

    # CMU cinderblock (#029)
    im = make_rgb_tex(256, 256, (176, 174, 168), amp=10.0, base_freq=12, seed=807, speckle=8.0)
    d = ImageDraw.Draw(im)
    for r_i, y in enumerate(range(0, 256, 32)):
        xo = (r_i % 2) * 32
        d.line([(0, y), (255, y)], fill=(122, 120, 114), width=2)
        for x in range(-32, 256, 64):
            d.line([(x + xo, y), (x + xo, y + 31)], fill=(122, 120, 114), width=2)
    reg("gwc_cinder", im, "Off-white painted CMU cinderblock commercial wall")

    # Star-Liter Motel barn-red horizontal wood siding (#086)
    im = make_rgb_tex(256, 256, (132, 42, 38), amp=12.0, base_freq=8, seed=808)
    d = ImageDraw.Draw(im)
    for y in range(0, 256, 24):
        d.line([(0, y), (255, y)], fill=(78, 22, 20), width=3)
        d.line([(0, y + 2), (255, y + 2)], fill=(154, 56, 48), width=2)
    reg("gwc_redsid", im, "Star-Liter Motel barn-red horizontal wood lap siding")

    # Corrugated metal siding
    im = make_rgb_tex(256, 256, (150, 152, 156), amp=10.0, base_freq=6, seed=809)
    d = ImageDraw.Draw(im)
    for x in range(0, 256, 16):
        d.rectangle([x, 0, x + 5, 255], fill=(108, 110, 114))
        d.rectangle([x + 6, 0, x + 11, 255], fill=(176, 178, 182))
    reg("gwc_corrug", im, "Vertical corrugated galvanized steel warehouse siding")

    # Window with horizontal vinyl venetian blinds (#086)
    im = Image.new("RGB", (128, 128), (38, 44, 48))
    d = ImageDraw.Draw(im)
    for y in range(6, 120, 8):
        d.rectangle([6, y, 121, y + 4], fill=(176, 172, 162))
    d.rectangle([0, 0, 127, 127], outline=(58, 54, 50), width=6)
    reg("gwc_blind", im, "Recessed glass window w/ horizontal cream vinyl blinds", wad_div=1)

    # Motel/residential exterior door
    im = make_rgb_tex(128, 256, (156, 148, 134), amp=10.0, base_freq=6, seed=811)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 117, 245], outline=(98, 92, 82), width=6)
    d.rectangle([26, 26, 101, 108], outline=(112, 104, 94), width=3)
    d.rectangle([26, 126, 101, 224], outline=(112, 104, 94), width=3)
    d.ellipse([94, 114, 106, 126], fill=(172, 140, 56))
    reg("gwc_wooddoor", im, "Paneled painted motel & residential exterior door")

    # --- NEIGHBORHOOD BUSINESS SIGNAGE ---
    # 1. Carnitas Birria Menudo (#033, #035)
    im = make_rgb_tex(512, 128, (194, 192, 186), amp=6.0, base_freq=4, seed=820)
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 505, 121], outline=(164, 24, 28), width=6)
    f_c1 = fit_font(d, "CARNITAS BIRRIA MENUDO", "impact", 464, 54, start_size=40)
    f_c2 = fit_font(d, "FRESH AUTHENTIC MEXICAN FOOD  •  TACOS  •  CHILORIO", "bold", 464, 28, start_size=16)
    draw_centered(d, 256, 50, "CARNITAS BIRRIA MENUDO", f_c1, (168, 22, 26))
    draw_centered(d, 256, 98, "FRESH AUTHENTIC MEXICAN FOOD  •  TACOS  •  CHILORIO", f_c2, (34, 96, 46))
    reg("gwc_carnit", im, "Carnitas Birria Menudo red/white roadside banner")

    # Menudo feather flag (alpha cutout + opaque blade)
    im_fa = Image.new("RGBA", (128, 512), (0, 0, 0, 0))
    da = ImageDraw.Draw(im_fa)
    da.polygon([(14, 18), (94, 48), (112, 220), (104, 480), (14, 496)], fill=(168, 24, 28, 255))
    da.polygon([(22, 42), (86, 66), (98, 210), (92, 460), (22, 474)], fill=(196, 158, 26, 255))
    for i, ch in enumerate("MENUDO"):
        draw_centered(da, 60, 102 + i * 62, ch, font("impact", 52), (164, 22, 24, 255), outline=(200, 198, 192, 255), outline_w=2)
    reg("{gwc_menudof", im_fa, "Alpha-cutout tall red & yellow MENUDO feather flag")

    im_fb = Image.new("RGB", (128, 512), (168, 24, 28))
    db = ImageDraw.Draw(im_fb)
    db.rectangle([10, 10, 117, 501], fill=(196, 158, 26), outline=(168, 24, 28), width=6)
    for i, ch in enumerate("MENUDO"):
        draw_centered(db, 64, 86 + i * 66, ch, font("impact", 56), (164, 22, 24), outline=(200, 198, 192), outline_w=2)
    reg("gwc_menudof", im_fb, "Red & yellow MENUDO street flag banner")

    # 2. Star-Liter Motel (#086)
    diff = make_rgb_tex(512, 256, (190, 186, 174), amp=8.0, base_freq=6, seed=822)
    glow = Image.new("RGB", (512, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    dd.rounded_rectangle([12, 12, 499, 156], radius=22, fill=(40, 116, 124), outline=(172, 34, 34), width=8)
    dg.rounded_rectangle([12, 12, 499, 156], radius=22, outline=(255, 72, 64), width=6)
    draw_centered(dd, 256, 62, "Star-Liter", font("script", 54), (198, 196, 190), outline=(160, 32, 32), outline_w=3)
    draw_centered(dg, 256, 62, "Star-Liter", font("script", 54), (255, 244, 210), outline=(255, 64, 56), outline_w=2)
    draw_centered(dd, 256, 124, "MOTEL", font("impact", 40), (196, 166, 48))
    draw_centered(dg, 256, 124, "MOTEL", font("impact", 40), (255, 212, 64))
    dd.rectangle([32, 172, 244, 236], fill=(154, 28, 30), outline=(44, 44, 48), width=4)
    dd.rectangle([268, 172, 480, 236], fill=(32, 38, 44), outline=(44, 44, 48), width=4)
    draw_centered(dd, 138, 204, "VACANCY", font("impact", 32), (198, 196, 190))
    draw_centered(dg, 138, 204, "VACANCY", font("impact", 32), (255, 74, 72))
    draw_centered(dd, 374, 204, "TV • REFRIG", font("bold", 26), (196, 176, 64))
    draw_centered(dg, 374, 204, "TV • REFRIG", font("bold", 26), (255, 224, 96))
    reg("gwc_starlt", diff, "Star-Liter Motel Googie illuminated VACANCY / REFRIG sign", glow=glow)

    # 3. Ramos Tire & Service + Ramos Now Open (#067)
    im = make_rgb_tex(512, 128, (24, 58, 132), amp=8.0, base_freq=6, seed=823)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 96, 511, 127], fill=(162, 28, 32))
    draw_centered(d, 256, 48, "RAMOS TIRE & SERVICE", font("impact", 46), (200, 200, 194))
    draw_centered(d, 256, 111, "NEW & USED TIRES  •  ALIGNMENT  •  BRAKES", font("bold", 16), (200, 198, 192))
    reg("gwc_ramos", im, "Ramos Tire & Service royal-blue fascia sign")

    im = make_rgb_tex(512, 128, (194, 192, 188), amp=6.0, base_freq=4, seed=824)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, 503, 119], outline=(24, 58, 132), width=6)
    draw_centered(d, 256, 44, "RAMOS", font("impact", 42), (164, 24, 28))
    draw_centered(d, 256, 94, "NOW OPEN", font("impact", 38), (24, 58, 132))
    reg("gwc_ramosop", im, "Ramos Tire & Service white vinyl banner: RAMOS NOW OPEN")

    # 4. Best DEALS / Compas Auto (#021, #044)
    im = make_rgb_tex(512, 256, (26, 62, 134), amp=8.0, base_freq=6, seed=825)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 501, 245], outline=(194, 158, 34), width=8)
    draw_centered(d, 256, 74, "Best DEALS", font("impact", 64), (198, 168, 38), outline=(14, 28, 66), outline_w=4)
    d.rectangle([28, 138, 484, 224], fill=(194, 192, 186))
    draw_centered(d, 256, 181, "Compas Auto", font("serif", 48), (24, 54, 122))
    reg("gwc_bdeal", im, "Best DEALS / Compas Auto lot billboard & fascia")

    # 5. Super 8 diamond yellow/red crest (#025, #027, #049)
    diff = Image.new("RGB", (256, 256), (174, 28, 32))
    glow = Image.new("RGB", (256, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    for dr, sc in ((dd, 0.78), (dg, 1.0)):
        dr.polygon([(128, 14), (242, 128), (128, 242), (14, 128)], fill=(int(244 * sc), int(202 * sc), int(34 * sc)), outline=(int(180 * sc), int(26 * sc), int(30 * sc)))
        draw_centered(dr, 128, 88, "Super", font("impact", 40), (int(196 * sc), int(26 * sc), int(30 * sc)))
        draw_centered(dr, 128, 152, "8", font("impact", 76), (int(196 * sc), int(26 * sc), int(30 * sc)))
        dr.rectangle([42, 206, 214, 242], fill=(int(28 * sc), int(28 * sc), int(32 * sc)))
        draw_centered(dr, 128, 224, "MOTEL", font("bold", 22), (int(244 * sc), int(242 * sc), int(236 * sc)))
    reg("gwc_super8", diff, "Super 8 Motel iconic yellow/red diamond crest sign", glow=glow)

    # 6. Sunland MOTEL (#063)
    diff, glow = neon_sign_pair(
        512, 256, (28, 92, 98),
        [
            ("Sunland", "script", 72, (255, 218, 68), 0.34),
            ("MOTEL", "impact", 52, (255, 244, 226), 0.68),
            ("COLOR TV  •  AIR COND  •  POOL", "bold", 18, (255, 118, 86), 0.88),
        ],
        border_rgb=(245, 198, 54),
    )
    reg("gwc_sunlnd", diff, "Sunland Motel teal & gold retro neon marquee", glow=glow)

    # 7. Country Inn MOTEL (#063)
    diff = make_rgb_tex(512, 256, (30, 86, 152), amp=8.0, base_freq=6, seed=828)
    glow = Image.new("RGB", (512, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    # Googie sweeping yellow fin border
    dd.polygon([(12, 18), (498, 18), (476, 174), (36, 174)], fill=(30, 86, 152), outline=(192, 158, 36), width=8)
    dg.polygon([(12, 18), (498, 18), (476, 174), (36, 174)], outline=(255, 214, 48), width=6)
    draw_centered(dd, 256, 94, "Country Inn", font("script", 64), (198, 196, 190))
    draw_centered(dg, 256, 94, "Country Inn", font("script", 64), (245, 248, 255))
    dd.rectangle([72, 182, 440, 242], fill=(166, 28, 32), outline=(194, 192, 186), width=4)
    draw_centered(dd, 256, 212, "MOTEL", font("impact", 42), (198, 196, 190))
    draw_centered(dg, 256, 212, "MOTEL", font("impact", 42), (255, 246, 232))
    reg("gwc_cntry", diff, "Country Inn Motel Googie blue/yellow/red pole sign", glow=glow)

    # 8. El Don MOTEL (#039 SE Belle Terrace brownfield corner sign)
    im = make_rgb_tex(512, 256, (192, 158, 34), amp=12.0, base_freq=8, seed=829, speckle=8.0)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 501, 245], outline=(24, 24, 26), width=10)
    draw_centered(d, 256, 86, "El Don", font("script", 74), (24, 24, 26))
    d.rectangle([38, 154, 474, 224], fill=(24, 24, 26))
    draw_centered(d, 256, 189, "MOTEL", font("impact", 48), (192, 158, 34))
    reg("gwc_eldon", im, "Weathered yellow & black El Don Motel corner sign")

    # 9. Play Fair Liquor & Beer / Market / Bakersfield Union Ave Mural (#046)
    im = make_rgb_tex(512, 128, (164, 28, 34), amp=8.0, base_freq=6, seed=830)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 74, 511, 127], fill=(24, 56, 126))
    draw_centered(d, 256, 38, "Play Fair", font("script", 54), (200, 198, 192))
    draw_centered(d, 256, 100, "LIQUOR  &  BEER", font("impact", 32), (200, 198, 192))
    reg("gwc_playfr", im, "Play Fair Liquor & Beer storefront fascia")

    im = make_rgb_tex(512, 128, (194, 192, 186), amp=6.0, base_freq=4, seed=831)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 511, 66], fill=(24, 56, 126))
    f_pf = fit_font(d, "GROCERIES  •  ICE COLD SODAS", "impact", 466, 42, start_size=30)
    draw_centered(d, 256, 33, "MARKET", font("impact", 46), (200, 198, 192))
    draw_centered(d, 256, 97, "GROCERIES  •  ICE COLD SODAS", f_pf, (164, 26, 30))
    reg("gwc_pfmarket", im, "Playfair Market Groceries Ice Cold Sodas fascia")

    # Colorful BAKERSFIELD UNION AVE wall mural (#046)
    im = make_rgb_tex(512, 256, (184, 124, 62), amp=12.0, base_freq=8, seed=832)
    d = ImageDraw.Draw(im)
    # Warm Central Valley sunset bands & silhouette hills/palms
    d.rectangle([0, 0, 511, 90], fill=(176, 98, 48))
    d.rectangle([0, 174, 511, 255], fill=(64, 42, 34))
    d.ellipse([364, 24, 464, 124], fill=(196, 162, 48))
    d.rectangle([404, 84, 412, 200], fill=(42, 30, 24))
    draw_centered(d, 236, 78, "BAKERSFIELD", font("impact", 58), (200, 194, 178), outline=(42, 26, 22), outline_w=5)
    draw_centered(d, 236, 148, "UNION AVE", font("black", 46), (198, 168, 48), outline=(42, 26, 22), outline_w=4)
    draw_centered(d, 256, 214, "WELCOME TO SOUTH UNION", font("bold", 22), (196, 190, 176))
    reg("gwc_pfmural", im, "Playfair Market painted BAKERSFIELD UNION AVE wall mural")

    # 10. Century Glass WINDOWS & DOORS + royal blue door (#029)
    im = make_rgb_tex(512, 128, (32, 34, 38), amp=6.0, base_freq=4, seed=833)
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 505, 121], outline=(28, 76, 152), width=5)
    draw_centered(d, 256, 46, "WINDOWS & DOORS", font("impact", 44), (200, 198, 194))
    draw_centered(d, 256, 96, "CENTURY GLASS  •  COMMERCIAL & AUTO", font("bold", 19), (86, 148, 200))
    reg("gwc_windoor", im, "Century Glass WINDOWS & DOORS storefront fascia")

    im = make_rgb_tex(128, 256, (26, 72, 148), amp=8.0, base_freq=4, seed=834)
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 121, 249], outline=(18, 48, 102), width=6)
    d.rectangle([22, 22, 105, 154], fill=(42, 62, 82), outline=(180, 184, 188), width=3)
    d.rectangle([16, 154, 111, 170], fill=(166, 170, 174))
    reg("gwc_royaldoor", im, "Century Glass royal-blue commercial aluminum entry door")

    # 11. U-Haul, U-Haul box livery, and Truck Sales (#035)
    im = make_rgb_tex(512, 128, (192, 84, 24), amp=8.0, base_freq=6, seed=835)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 74, 511, 127], fill=(194, 192, 186))
    draw_centered(d, 256, 38, "U-HAUL", font("impact", 58), (200, 200, 196), outline=(42, 24, 16), outline_w=3)
    draw_centered(d, 256, 101, "TRUCKS & TRAILERS FOR RENT", font("bold", 24), (28, 28, 30))
    reg("gwc_uhaul", im, "U-Haul orange & white storefront/yard fascia")

    im = make_rgb_tex(256, 128, (194, 192, 186), amp=6.0, base_freq=4, seed=836)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 92, 255, 127], fill=(192, 84, 24))
    d.rectangle([0, 0, 255, 14], fill=(192, 84, 24))
    draw_centered(d, 128, 44, "U-HAUL", font("impact", 40), (192, 84, 24))
    draw_centered(d, 128, 76, "IN-TOWN  •  ONE WAY", font("bold", 14), (28, 28, 30))
    reg("gwc_uhaulbox", im, "U-Haul box truck side livery")

    im = make_rgb_tex(512, 256, (194, 166, 34), amp=8.0, base_freq=6, seed=837)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 501, 245], outline=(24, 24, 26), width=8)
    draw_centered(d, 256, 86, "TRUCK SALES", font("impact", 68), (24, 24, 26))
    d.rectangle([42, 152, 470, 224], fill=(24, 24, 26))
    draw_centered(d, 256, 188, "BOX TRUCKS  •  PICKUPS  •  VANS", font("bold", 26), (194, 166, 34))
    reg("gwc_trksale", im, "Yellow & black TRUCK SALES lot billboard")

    # 12. Redwood Senior Living monument sign
    im = make_rgb_tex(512, 256, (186, 174, 150), amp=12.0, base_freq=8, seed=838)
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, 499, 243], outline=(104, 48, 36), width=10)
    draw_centered(d, 256, 84, "REDWOOD", font("serif", 64), (112, 42, 32))
    d.line([(68, 134), (444, 134)], fill=(66, 92, 54), width=4)
    draw_centered(d, 256, 178, "SENIOR LIVING", font("bold", 38), (52, 74, 44))
    draw_centered(d, 256, 220, "BAKERSFIELD, CALIFORNIA", font("bold", 16), (82, 74, 62))
    reg("gwc_redwood", im, "Redwood Senior Living monument plaque")

    # 13. Convenience Market & Residential / Motel Interior Textures (#43)
    # gwc_cooler: Backlit glass beverage cooler doors w/ soda/beer rows
    diff = Image.new("RGB", (256, 256), (34, 42, 52))
    glow = Image.new("RGB", (256, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    # Header lightbox strip
    dd.rectangle([0, 0, 255, 34], fill=(24, 58, 128), outline=(146, 150, 156), width=3)
    dg.rectangle([4, 4, 251, 30], fill=(38, 92, 198))
    draw_centered(dd, 128, 17, "COLD BEER  •  SODAS", font("impact", 20), (200, 198, 192))
    draw_centered(dg, 128, 17, "COLD BEER  •  SODAS", font("impact", 20), (248, 246, 224))
    # Two aluminum glass doors packed with colorful bottles & cans on 4 shelves
    rng_cl = np.random.default_rng(840)
    shelf_pal = [
        (178, 34, 38), (34, 96, 176), (36, 146, 68),
        (192, 134, 28), (192, 186, 172), (146, 52, 146),
    ]
    for dx0, dx1 in ((10, 123), (133, 245)):
        dd.rectangle([dx0, 42, dx1, 247], fill=(168, 194, 204), outline=(112, 118, 124), width=5)
        dg.rectangle([dx0 + 5, 47, dx1 - 5, 242], fill=(148, 178, 192))
        for sy in (86, 134, 182, 230):
            # Beverage cans/bottles standing on each shelf
            for bx in range(dx0 + 10, dx1 - 14, 14):
                col = shelf_pal[int(rng_cl.integers(0, len(shelf_pal)))]
                bh = int(rng_cl.integers(24, 34))
                dd.rectangle([bx, sy - bh, bx + 10, sy - 2], fill=col, outline=(28, 30, 34), width=1)
                dd.rectangle([bx + 2, sy - bh + 5, bx + 8, sy - bh + 12], fill=(198, 198, 194))
                dg.rectangle([bx + 1, sy - bh + 2, bx + 9, sy - 3], fill=tuple(min(220, int(c * 0.85)) for c in col))
            dd.rectangle([dx0 + 5, sy, dx1 - 5, sy + 5], fill=(122, 128, 134))
        # Subtle glass reflection + vertical chrome door handle
        dd.line([(dx0 + 14, 52), (dx1 - 16, 232)], fill=(198, 205, 205), width=2)
    dd.rectangle([114, 108, 120, 182], fill=(186, 190, 196))
    dd.rectangle([136, 108, 142, 182], fill=(186, 190, 196))
    reg("gwc_cooler", diff, "Backlit Playfair Market glass beverage cooler doors w/ soda/beer", glow=glow)

    # gwc_grocery: Stocked convenience store grocery & liquor shelving
    im = make_rgb_tex(256, 256, (168, 162, 150), amp=8.0, base_freq=6, seed=841)
    d = ImageDraw.Draw(im)
    rng_gr = np.random.default_rng(841)
    item_pal = [
        (174, 36, 38), (192, 152, 34), (36, 86, 158), (44, 132, 66),
        (194, 190, 182), (168, 86, 32), (98, 44, 118), (42, 46, 52),
    ]
    for sy in (52, 104, 156, 208, 250):
        bx = 6
        while bx < 246:
            bw = int(rng_gr.integers(12, 26))
            bh = int(rng_gr.integers(24, 42))
            col = item_pal[int(rng_gr.integers(0, len(item_pal)))]
            d.rectangle([bx, sy - bh, min(250, bx + bw - 2), sy - 2], fill=col, outline=(36, 34, 32), width=1)
            d.rectangle([bx + 2, sy - bh + 5, min(248, bx + bw - 4), sy - bh + 13], fill=(196, 194, 188))
            bx += bw
        d.rectangle([0, sy - 2, 255, sy + 6], fill=(122, 118, 112))
        d.rectangle([0, sy + 4, 255, sy + 7], fill=(182, 144, 42))
    reg("gwc_grocery", im, "Stocked convenience store grocery, snacks & liquor gondola shelves")

    # gwc_drywall: Warm sunlit residential interior plaster/drywall w/ baseboard
    im = make_rgb_tex(256, 256, (192, 186, 174), amp=8.0, base_freq=14, seed=842, speckle=5.0)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 232, 255, 255], fill=(176, 172, 162))
    d.line([(0, 232), (255, 232)], fill=(138, 134, 126), width=2)
    reg("gwc_drywall", im, "Warm off-white textured residential & motel interior drywall")

    # gwc_bed: Quilted motel/residential bedspread w/ pillows & headboard
    im = make_rgb_tex(256, 256, (118, 48, 52), amp=10.0, base_freq=10, seed=843, speckle=6.0)
    d = ImageDraw.Draw(im)
    # Walnut headboard along top
    d.rectangle([0, 0, 255, 28], fill=(74, 44, 28), outline=(48, 28, 18), width=3)
    # Crisp white top sheet & twin pillows
    d.rectangle([0, 28, 255, 102], fill=(192, 190, 184))
    d.rounded_rectangle([18, 34, 120, 82], radius=12, fill=(198, 196, 190), outline=(146, 144, 138), width=3)
    d.rounded_rectangle([136, 34, 238, 82], radius=12, fill=(198, 196, 190), outline=(146, 144, 138), width=3)
    # Quilted diamond stitch pattern on blanket
    d.rectangle([0, 96, 255, 114], fill=(172, 152, 118))
    for off in range(-256, 384, 32):
        d.line([(off, 114), (off + 142, 255)], fill=(92, 34, 38), width=2)
        d.line([(off + 142, 114), (off, 255)], fill=(92, 34, 38), width=2)
    reg("gwc_bed", im, "Quilted motel & bedroom bedspread with pillows and wood headboard")

    # gwc_motelcpt: Neutral warm tan/taupe-olive speckled motel room loop carpet
    im = make_rgb_tex(256, 256, (134, 124, 104), amp=16.0, base_freq=16, seed=844, speckle=22.0)
    reg("gwc_motelcpt", im, "Neutral tan/taupe speckled motel & residential carpet")

    # gwc_carnmenu: Carnitas Birria Menudo backlit diner menu board (512x256)
    diff = Image.new("RGB", (512, 256), (40, 24, 20))
    glow = Image.new("RGB", (512, 256), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    dd.rectangle([10, 10, 501, 245], fill=(192, 188, 174), outline=(154, 24, 28), width=4)
    dg.rectangle([10, 10, 501, 245], fill=(142, 138, 126))
    dd.rectangle([14, 14, 497, 56], fill=(154, 24, 28))
    dg.rectangle([14, 14, 497, 56], fill=(182, 28, 32))
    f_cm1 = fit_font(dd, "CARNITAS  •  BIRRIA  •  MENUDO", "impact", 456, 32, start_size=30)
    draw_centered(dd, 256, 35, "CARNITAS  •  BIRRIA  •  MENUDO", f_cm1, (200, 196, 186))
    draw_centered(dg, 256, 35, "CARNITAS  •  BIRRIA  •  MENUDO", f_cm1, (242, 238, 224))
    dd.rectangle([14, 58, 497, 86], fill=(28, 92, 42))
    dg.rectangle([14, 58, 497, 86], fill=(34, 114, 52))
    f_cm2 = fit_font(dd, "TACOS   •   TORTAS   •   BURRITOS", "bold", 456, 20, start_size=19)
    draw_centered(dd, 256, 72, "TACOS   •   TORTAS   •   BURRITOS", f_cm2, (200, 184, 92))
    draw_centered(dg, 256, 72, "TACOS   •   TORTAS   •   BURRITOS", f_cm2, (244, 222, 108))
    dd.line([(256, 94), (256, 206)], fill=(120, 106, 92), width=2)
    left_items = [
        ("CARNITAS PLATE", "$13"),
        ("BIRRIA TACOS", "$11"),
        ("MENUDO BOWL", "$12"),
    ]
    right_items = [
        ("TORTA CUBANA", "$12"),
        ("SUPER BURRITO", "$11"),
        ("QUESABIRRIA", "$13"),
    ]
    f_item = font("bold", 16)
    for col_idx, items in enumerate((left_items, right_items)):
        x0 = 28 if col_idx == 0 else 270
        xr = 242 if col_idx == 0 else 484
        for row_idx, (label, price) in enumerate(items):
            yy = 104 + row_idx * 34
            dd.text((x0, yy), label, font=f_item, fill=(32, 26, 24))
            dg.text((x0, yy), label, font=f_item, fill=(18, 14, 12))
            pb = dd.textbbox((0, 0), price, font=f_item)
            pw = pb[2] - pb[0]
            dd.text((xr - pw, yy), price, font=f_item, fill=(158, 24, 28))
            dg.text((xr - pw, yy), price, font=f_item, fill=(192, 24, 28))
            if row_idx < 2:
                dd.line([(x0, yy + 24), (xr, yy + 24)], fill=(160, 152, 138), width=1)
    dd.rectangle([14, 212, 497, 241], fill=(154, 24, 28))
    dg.rectangle([14, 212, 497, 241], fill=(182, 28, 32))
    f_cm3 = fit_font(dd, "FRESH DAILY  •  AGUAS FRESCAS  •  SALSA BAR", "bold", 456, 18, start_size=16)
    draw_centered(dd, 256, 226, "FRESH DAILY  •  AGUAS FRESCAS  •  SALSA BAR", f_cm3, (200, 196, 186))
    draw_centered(dg, 256, 226, "FRESH DAILY  •  AGUAS FRESCAS  •  SALSA BAR", f_cm3, (240, 236, 224))
    reg("gwc_carnmenu", diff, "Backlit Carnitas Birria Menudo tacos/tortas/burritos menu board", glow=glow)

    # gwc_keyrack: Motel office check-in key pegboard & daily/weekly rate sign (512x256)
    im = Image.new("RGB", (512, 256), (72, 42, 24))
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, 499, 243], fill=(192, 188, 174), outline=(44, 26, 16), width=3)
    d.rectangle([18, 18, 493, 60], fill=(28, 56, 86))
    d.line([(18, 60), (493, 60)], fill=(182, 146, 52), width=2)
    f_k1 = fit_font(d, "OFFICE  CHECK-IN", "impact", 448, 32, start_size=30)
    draw_centered(d, 256, 39, "OFFICE  CHECK-IN", f_k1, (200, 196, 184))
    d.rectangle([18, 62, 493, 88], fill=(128, 30, 36))
    f_k2 = fit_font(d, "ROOM KEYS  &  RATES", "bold", 440, 18, start_size=18)
    draw_centered(d, 256, 75, "ROOM KEYS  &  RATES", f_k2, (200, 184, 112))
    # Left section: wood key pegboard with numbered diamond room fobs
    d.rectangle([24, 96, 268, 236], fill=(158, 134, 102), outline=(64, 40, 22), width=2)
    d.text((34, 101), "ROOM KEYS", font=font("bold", 13), fill=(44, 28, 18))
    tag_cols = [(32, 92, 108), (132, 34, 38), (44, 102, 54), (156, 114, 28)]
    f_num = font("bold", 11)
    for row_idx, ry in enumerate((124, 180)):
        d.rectangle([32, ry - 4, 260, ry + 2], fill=(74, 44, 26))
        for col_idx in range(4):
            kx = 58 + col_idx * 56
            d.ellipse([kx - 3, ry - 3, kx + 3, ry + 3], fill=(192, 162, 62))
            tcol = tag_cols[(row_idx + col_idx) % len(tag_cols)]
            d.polygon([(kx, ry + 4), (kx + 18, ry + 20), (kx, ry + 42), (kx - 18, ry + 20)], fill=tcol, outline=(36, 24, 18))
            draw_centered(d, kx, ry + 22, f"{(row_idx + 1) * 100 + col_idx + 1}", f_num, (200, 198, 190))
    # Right section: clean framed daily/weekly room rates card
    d.rectangle([278, 96, 487, 236], fill=(198, 194, 184), outline=(28, 56, 86), width=2)
    d.rectangle([278, 96, 487, 122], fill=(28, 56, 86))
    draw_centered(d, 382, 109, "DAILY / WEEKLY", font("bold", 14), (200, 184, 112))
    rate_rows = [("SINGLE", "$69"), ("DOUBLE", "$79"), ("WEEKLY", "$349"), ("CHECK-OUT", "11 AM")]
    f_r = font("bold", 15)
    for idx, (rk, rv) in enumerate(rate_rows):
        ry = 130 + idx * 25
        d.text((290, ry), rk, font=f_r, fill=(32, 36, 44))
        rb = d.textbbox((0, 0), rv, font=f_r)
        d.text((476 - (rb[2] - rb[0]), ry), rv, font=f_r, fill=(132, 26, 30))
        if idx < 3:
            d.line([(290, ry + 20), (476, ry + 20)], fill=(166, 162, 152), width=1)
    reg("gwc_keyrack", im, "Motel office check-in wall board with room keys and rates")


# ==============================================================================
# 3B. GREAT CASTLE (410 UNION AVE) & NORTH S UNION CORRIDOR (PHASE 2)
# ==============================================================================


_CJK_FONT_CANDIDATES: Dict[str, List[str]] = {
    "jheng_bold": [r"C:\Windows\Fonts\msjhbd.ttc", r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simsun.ttc"],
    "yahei_bold": [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msjhbd.ttc", r"C:\Windows\Fonts\simsun.ttc"],
    "song_serif": [r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\msjhbd.ttc", r"C:\Windows\Fonts\msyhbd.ttc"],
}


def cjk_font(size: int, style: str = "jheng_bold") -> ImageFont.FreeTypeFont:
    """Load a verified Windows Traditional/Simplified CJK font (zero tofu boxes)."""
    key = (f"cjk_{style}", size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    for path in _CJK_FONT_CANDIDATES.get(style, _CJK_FONT_CANDIDATES["jheng_bold"]):
        if os.path.exists(path):
            fnt = ImageFont.truetype(path, size)
            _FONT_CACHE[key] = fnt
            return fnt
    fnt = font("bold", size)
    _FONT_CACHE[key] = fnt
    return fnt


def _periodic_fbm(w: int, h: int, freqs: Tuple[int, ...] = (2, 4, 8, 16), seed: int = 101) -> np.ndarray:
    """Generate seamlessly tileable periodic fBM heightfield in [-1, 1] for textures."""
    rng = np.random.default_rng(seed)
    uy = np.linspace(0.0, 2.0 * math.pi, h, endpoint=False)[:, None]
    ux = np.linspace(0.0, 2.0 * math.pi, w, endpoint=False)[None, :]
    acc = np.zeros((h, w), dtype=np.float32)
    amp = 1.0
    norm = 0.0
    for f in freqs:
        layer = np.zeros((h, w), dtype=np.float32)
        for _ in range(3):
            kx = int(rng.integers(1, f + 1))
            ky = int(rng.integers(1, f + 1))
            sx = 1 if rng.random() < 0.5 else -1
            ph = float(rng.uniform(0.0, 2.0 * math.pi))
            layer += np.sin(ux * (kx * sx) + uy * ky + ph).astype(np.float32)
        acc += (layer / 3.0) * amp
        norm += amp
        amp *= 0.55
    return np.clip(acc / max(norm, 1e-6), -1.0, 1.0)


def build_great_castle_architecture() -> None:
    """Build procedural exterior, interior & corridor architectural textures for Phase 2."""
    # 1. Great Castle painted white running-bond CMU masonry wall (#161, #162, #149)
    im = make_rgb_tex(256, 256, (186, 183, 176), amp=9.0, base_freq=8, octaves=4, seed=201, speckle=2.0)
    arr = np.array(im, dtype=np.float32)
    # Subtle horizontal stucco roller + vertical/horizontal CMU block mortar grooves (64x32 cells)
    for row in range(8):
        y0 = row * 32
        arr[y0 : y0 + 2, :, :] -= 18.0
        arr[y0 + 2 : y0 + 4, :, :] += 6.0
        offset = 32 if (row % 2) else 0
        for col in range(4):
            x0 = (col * 64 + offset) % 256
            arr[y0 : y0 + 32, x0 : min(256, x0 + 2), :] -= 15.0
            if x0 + 2 < 256:
                arr[y0 : y0 + 32, x0 + 2 : min(256, x0 + 4), :] += 5.0
    reg("gwc_gccmu", Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8)), "Painted off-white CMU block exterior wall (Great Castle & E 5th)")

    # 2. Great Castle white painted masonry merlon with dark embrasure slot (#161, #162)
    im = make_rgb_tex(128, 128, (188, 185, 178), amp=8.0, base_freq=4, octaves=4, seed=202, speckle=1.8)
    arr = np.array(im, dtype=np.float32)
    for y0 in (0, 32, 64, 96):
        arr[y0 : y0 + 2, :, :] -= 14.0
        offset = 32 if (y0 // 32) % 2 else 0
        for x0 in (offset % 128, (offset + 64) % 128):
            arr[y0 : y0 + 32, x0 : min(128, x0 + 2), :] -= 12.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Top parapet stone coping cap & cast drip line
    d.rectangle([0, 0, 127, 8], fill=(196, 193, 186))
    d.line([(0, 9), (127, 9)], fill=(138, 134, 126), width=2)
    # Recessed rectangular castle loophole embrasure slot (#161, #162)
    d.rectangle([45, 24, 83, 66], fill=(142, 138, 130))
    d.polygon([(45, 24), (83, 24), (77, 30), (51, 30)], fill=(96, 94, 88))
    d.polygon([(45, 24), (51, 30), (51, 60), (45, 66)], fill=(116, 112, 106))
    d.polygon([(83, 24), (83, 66), (77, 60), (77, 30)], fill=(154, 150, 142))
    d.rectangle([51, 30, 77, 60], fill=(32, 34, 38))
    reg("gwc_gcmerlon", im, "White masonry parapet merlon with dark embrasure slot (#161, #162)")

    # 3. Great Castle crimson barrel-vault awning with cream stripe & scalloped trim (#161)
    im = Image.new("RGB", (256, 128), (138, 24, 34))
    weave = _periodic_fbm(256, 128, (8, 16, 32), seed=203)
    arr = np.array(im, dtype=np.float32) + weave[:, :, None] * 6.5
    # Subtle woven canvas horizontal threads + darker barrel cuff
    yy = np.arange(128, dtype=np.float32)[:, None]
    arr += ((yy % 2) * 2.5 - 1.2)[:, :, None]
    arr[92:114, :, :] *= 0.86
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for sx in range(0, 256, 64):
        d.line([(sx, 0), (sx, 114)], fill=(98, 16, 24), width=2)
        d.line([(sx + 2, 0), (sx + 2, 114)], fill=(154, 34, 44), width=1)
    # Crisp cream accent stripe near bottom + deep shadow strip behind scalloped lace trim
    d.rectangle([0, 94, 255, 101], fill=(192, 186, 172))
    d.rectangle([0, 114, 255, 127], fill=(34, 12, 16))
    for lx in range(0, 256, 32):
        d.pieslice([lx, 102, lx + 31, 125], 0, 180, fill=(138, 24, 34))
        d.arc([lx, 102, lx + 31, 125], 0, 180, fill=(194, 188, 174), width=3)
    reg("gwc_gcawn", im, "Crimson canvas barrel awning with cream band and scalloped valance (#161)")

    # 4. Granite monolith boulder & riverbed cobble rock-garden stone (#161)
    f_macro = _periodic_fbm(256, 256, (2, 4, 8), seed=204)
    f_grain = _periodic_fbm(256, 256, (16, 32, 64), seed=205)
    rng = np.random.default_rng(206)
    speck = rng.normal(0.0, 7.5, (256, 256))
    stone = np.zeros((256, 256, 3), dtype=np.float32)
    stone[:, :, 0] = 108.0 + f_macro * 22.0 + f_grain * 11.0 + speck
    stone[:, :, 1] = 106.0 + f_macro * 21.0 + f_grain * 10.5 + speck
    stone[:, :, 2] = 100.0 + f_macro * 19.0 + f_grain * 10.0 + speck
    # Fissure veins & warm mineral patches
    fissure = np.abs(f_macro + 0.35 * f_grain) < 0.08
    stone[fissure] -= 26.0
    moss = (f_macro < -0.32) & (f_grain > 0.1)
    stone[moss, 1] += 10.0
    stone[moss, 0] -= 6.0
    reg("gwc_gcstone", Image.fromarray(np.clip(stone, 0, MAX_ALBEDO).astype(np.uint8)), "Grey granite monolith boulder and riverbed rock-garden stone (#161)")

    # 5. Dark forest-green textured entry ramp mat (#161)
    im = make_rgb_tex(128, 128, (36, 72, 52), amp=6.0, base_freq=8, octaves=3, seed=207, speckle=3.0)
    arr = np.array(im, dtype=np.float32)
    yy, xx = np.mgrid[0:128, 0:128]
    rib = np.sin(yy * (math.pi / 2.0)) * 6.0 + np.sin((xx + yy) * (math.pi / 4.0)) * 3.0
    arr += rib[:, :, None]
    reg("gwc_gcramp", Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8)), "Dark green ribbed outdoor rubber entry ramp mat (#161)")

    # 6. Tall columnar Italian Cypress cutout sprite (#149)
    im = Image.new("RGBA", (128, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(208)
    # Short woody base trunk centered inside safe bottom margin
    d.rectangle([58, 466, 70, 502], fill=(64, 48, 34, 255))
    # Solid inner conifer core silhouette so zero pinholes show through the crown
    d.polygon(
        [(64, 24), (48, 128), (42, 260), (42, 430), (50, 474), (78, 474), (86, 430), (86, 260), (80, 128)],
        fill=(28, 48, 22, 255),
    )
    # Dense tapering columnar flame silhouette from y=482 up to spire at y=24
    for i in range(420):
        t = rng.random()
        y = int(32 + t * 442)
        if t < 0.25:
            half_w = 5.0 + (t / 0.25) * 19.0
        elif t < 0.88:
            half_w = 24.0 + 7.0 * math.sin(((t - 0.25) / 0.63) * math.pi)
        else:
            half_w = 24.0 * (1.0 - (t - 0.88) * 2.2)
        dx = int(rng.uniform(-half_w, half_w))
        cx = 64 + dx
        shade = (dx / max(half_w, 1.0)) * 0.5 + (1.0 - t) * 0.25 + rng.uniform(-0.2, 0.2)
        r = int(np.clip(38 + shade * 24, 20, 78))
        g = int(np.clip(64 + shade * 34, 34, 114))
        b = int(np.clip(30 + shade * 18, 16, 60))
        tw = int(rng.integers(5, 11))
        th = int(rng.integers(10, 20))
        d.ellipse([cx - tw, y - th, cx + tw, y + th // 2], fill=(r, g, b, 255))
    # Pointed top spire tuft
    d.polygon([(64, 19), (56, 56), (72, 56)], fill=(48, 78, 38, 255))
    im = enforce_transparent_border(im, pad_xy=10, pad_top=18, pad_bot=6)
    reg("{gwc_cypress", im, "Tall narrow Italian Cypress tree sprite along north wall (#149)")

    # 7. Charcoal scissor-lattice steel accordion security gate (#161)
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Top & bottom steel channel guide tracks
    d.rectangle([0, 0, 127, 6], fill=(42, 44, 48, 255))
    d.rectangle([0, 121, 127, 127], fill=(42, 44, 48, 255))
    d.line([(0, 2), (127, 2)], fill=(76, 80, 86, 255), width=1)
    # Vertical steel pickets every 32px
    for px in range(0, 128, 32):
        d.rectangle([px + 13, 6, px + 18, 121], fill=(38, 40, 44, 255))
        d.line([(px + 14, 6), (px + 14, 121)], fill=(70, 74, 80, 255), width=1)
    # Diagonal X scissor slats (wrapping cleanly across 128px width)
    for k in range(-2, 4):
        x0 = k * 32
        d.line([(x0, 6), (x0 + 64, 121)], fill=(48, 50, 56, 255), width=4)
        d.line([(x0 + 64, 6), (x0, 121)], fill=(42, 44, 48, 255), width=4)
    # Center rivet dots
    for px in range(15, 128, 32):
        for py in (35, 64, 93):
            d.ellipse([px - 2, py - 2, px + 3, py + 3], fill=(96, 100, 108, 255))
    reg("{gwc_gcgate", im, "Charcoal steel scissor-lattice entry security gate (#161)")

    # 8. Deep crimson-burgundy swirl/floral dining room carpet (#163, #165)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    ux = xx * (2.0 * math.pi / 256.0)
    uy = yy * (2.0 * math.pi / 256.0)
    warp_x = 0.72 * np.sin(ux * 2.0 + np.cos(uy * 2.0)) + 0.35 * np.cos(uy * 3.0 - ux)
    warp_y = 0.72 * np.cos(uy * 2.0 - np.sin(ux * 2.0)) + 0.35 * np.sin(ux * 3.0 + uy)
    phase = ux * 3.0 + uy * 2.0 + warp_x * 2.8 + warp_y * 2.4
    band = np.sin(phase)
    rib_fine = np.sin(phase * 3.0)
    rib2 = np.cos(ux * 4.0 - uy * 3.0 + warp_y * 2.6)
    loop = _periodic_fbm(256, 256, (16, 32, 64), seed=209)
    scroll = 0.55 * band + 0.30 * rib_fine + 0.15 * rib2
    carp = np.zeros((256, 256, 3), dtype=np.float32)
    # Rich maroon-burgundy ground with crisp dark-wine triple swirl linework (#163)
    hi = np.clip(scroll, 0.0, 1.0)
    sh = np.clip(-scroll, 0.0, 1.0)
    carp[:, :, 0] = 94.0 + hi * 52.0 - sh * 48.0 + loop * 7.0
    carp[:, :, 1] = 16.0 + hi * 12.0 - sh * 8.0 + loop * 2.5
    carp[:, :, 2] = 22.0 + hi * 13.0 - sh * 10.0 + loop * 3.0
    reg("gwc_gccarp", Image.fromarray(np.clip(carp, 0, MAX_ALBEDO).astype(np.uint8)), "Deep crimson-burgundy swirl pattern restaurant carpet (#163, #165)")

    # 9. Dining room cream plaster bay framed in dark espresso wood rails & wainscot (#163, #165)
    im = Image.new("RGB", (256, 256), (182, 170, 144))
    plaster = _periodic_fbm(256, 256, (4, 8, 16), seed=210)
    arr = np.array(im, dtype=np.float32) + plaster[:, :, None] * 6.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Dark espresso wood header rail, side vertical stiles, chair rail & lower wood wainscot
    espresso = (40, 26, 18)
    wood_hi = (66, 44, 30)
    wood_sh = (22, 14, 10)
    d.rectangle([0, 0, 255, 14], fill=espresso)
    d.line([(0, 14), (255, 14)], fill=wood_sh, width=2)
    d.rectangle([0, 0, 11, 255], fill=espresso)
    d.rectangle([244, 0, 255, 255], fill=espresso)
    d.line([(12, 14), (12, 169)], fill=wood_hi, width=1)
    d.line([(243, 14), (243, 169)], fill=wood_sh, width=1)
    # Molded chair rail & dark wood wainscot dado below y=170
    d.rectangle([0, 170, 255, 182], fill=(54, 36, 24))
    d.line([(0, 170), (255, 170)], fill=wood_hi, width=2)
    d.line([(0, 182), (255, 182)], fill=wood_sh, width=2)
    d.rectangle([0, 183, 255, 255], fill=espresso)
    # Twin recessed wood wainscot panels in lower dado
    for px0, px1 in ((22, 118), (138, 234)):
        d.rectangle([px0, 194, px1, 244], fill=(48, 32, 22), outline=wood_sh, width=2)
        d.line([(px0 + 2, 195), (px1 - 2, 195)], fill=wood_hi, width=1)
    reg("gwc_gcwall", im, "Cream plaster wall panels in dark espresso wood rails and dado wainscot (#163, #165)")

    # 10. Warm golden-amber stippled main dining ceiling (#163, #165)
    im = make_rgb_tex(128, 128, (134, 106, 64), amp=8.5, base_freq=8, octaves=4, seed=211, speckle=2.8)
    reg("gwc_gcceil", im, "Warm golden-amber textured main dining ceiling (#163, #165)")

    # 11. Dark bronze stamped tin coffered vestibule ceiling tiles (#166)
    im = Image.new("RGB", (256, 256), (44, 34, 26))
    metal = _periodic_fbm(256, 256, (8, 16, 32), seed=212)
    arr = np.array(im, dtype=np.float32) + metal[:, :, None] * 4.5
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for ty in (0, 128):
        for tx in (0, 128):
            d.rectangle([tx, ty, tx + 127, ty + 127], outline=(24, 18, 14), width=3)
            d.rectangle([tx + 5, ty + 5, tx + 122, ty + 122], outline=(76, 60, 44), width=2)
            d.rectangle([tx + 14, ty + 14, tx + 113, ty + 113], fill=(34, 26, 20), outline=(88, 68, 48), width=2)
            d.rectangle([tx + 22, ty + 22, tx + 105, ty + 105], outline=(62, 48, 34), width=1)
            cx, cy = tx + 64, ty + 64
            # Central stamped octagonal rosette & petal relief
            d.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=(48, 38, 28), outline=(92, 72, 50), width=2)
            for a_idx in range(8):
                ang = a_idx * (math.pi / 4.0)
                px = int(cx + math.cos(ang) * 16)
                py = int(cy + math.sin(ang) * 16)
                d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=(68, 52, 36), outline=(28, 20, 16))
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(96, 76, 52), outline=(36, 26, 18))
    reg("gwc_gccoff", im, "Stamped antique dark bronze coffered vestibule ceiling tiles (#166)")

    # 12. Gold-and-charcoal Chinese dragon-scroll & Greek-key cornice frieze (#166)
    im = Image.new("RGB", (512, 128), (34, 28, 24))
    d = ImageDraw.Draw(im)
    gold = (156, 128, 76)
    gold_dim = (104, 82, 48)
    rust = (116, 62, 42)
    cream = (176, 166, 144)
    # Top & bottom border molding bands
    d.rectangle([0, 0, 511, 10], fill=(46, 36, 28))
    d.rectangle([0, 11, 511, 15], fill=gold)
    d.rectangle([0, 112, 511, 116], fill=gold)
    d.rectangle([0, 117, 511, 127], fill=(46, 36, 28))
    # Two horizontal frieze units per 512px: Greek-key square meander block + dragon cartouche panel
    for bx in (0, 256):
        # Greek-key meander block (bx .. bx+95)
        for mx in (bx + 6, bx + 52):
            for my in (22, 68):
                d.rectangle([mx, my, mx + 38, my + 38], outline=gold, width=3)
                d.line([(mx + 38, my + 12), (mx + 12, my + 12), (mx + 12, my + 26), (mx + 26, my + 26), (mx + 26, my + 19)], fill=gold, width=3)
        # Elongated hexagonal dragon/cloud cartouche (bx+98 .. bx+250)
        poly = [(bx + 102, 64), (bx + 118, 24), (bx + 232, 24), (bx + 248, 64), (bx + 232, 104), (bx + 118, 104)]
        d.polygon(poly, fill=(44, 34, 28), outline=cream, width=2)
        d.line([(bx + 110, 64), (bx + 124, 32), (bx + 226, 32), (bx + 240, 64), (bx + 226, 96), (bx + 124, 96), (bx + 110, 64)], fill=gold_dim, width=2)
        # Stylized sinuous dragon/cloud curve inside cartouche
        pts = [(bx + 124 + i * 7, int(64 + 14 * math.sin(i * 0.65))) for i in range(16)]
        d.line(pts, fill=gold, width=4)
        d.line([(x, y + 3) for x, y in pts], fill=rust, width=2)
        for cx in (bx + 142, bx + 175, bx + 208):
            d.arc([cx - 12, 42, cx + 12, 66], 0, 250, fill=cream, width=2)
    reg("gwc_gccorn", im, "Chinese dragon-scroll and Greek-key meander vestibule frieze (#166)")

    # 13. Carved oxblood-crimson wood open Chinese fretwork partition (#166)
    im = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    red_wood = (102, 20, 24, 255)
    red_hi = (138, 38, 40, 255)
    # Outer wood frame rails & inner Chinese stepped perimeter border
    d.rectangle([0, 0, 255, 11], fill=red_wood)
    d.rectangle([0, 116, 255, 127], fill=red_wood)
    d.rectangle([0, 0, 11, 127], fill=red_wood)
    d.rectangle([244, 0, 255, 127], fill=red_wood)
    # Sweeping Chinese arch spanning upper opening down into lower sill
    d.arc([12, 14, 243, 218], 180, 360, fill=red_wood, width=9)
    d.arc([14, 16, 241, 216], 180, 360, fill=red_hi, width=2)
    # Continuous intersecting bamboo/vine arches & corner key-fret struts attached to frame
    d.arc([12, 16, 148, 224], 235, 360, fill=red_wood, width=6)
    d.arc([108, 16, 243, 224], 180, 305, fill=red_wood, width=6)
    d.arc([38, 34, 128, 124], 270, 90, fill=red_wood, width=5)
    d.arc([128, 34, 218, 124], 90, 270, fill=red_wood, width=5)
    for k in range(3):
        xL = 26 + k * 22
        xR = 229 - k * 22
        d.line([(xL, 11), (xL, 38), (xL + 14, 38), (xL + 14, 11)], fill=red_wood, width=4)
        d.line([(xR, 11), (xR, 38), (xR - 14, 38), (xR - 14, 11)], fill=red_wood, width=4)
    # Horizontal mid tie rail & center lotus-ring medallion
    d.line([(11, 82), (244, 82)], fill=red_wood, width=6)
    d.line([(128, 15), (128, 116)], fill=red_wood, width=6)
    d.ellipse([106, 42, 150, 86], outline=red_wood, width=6)
    d.ellipse([110, 46, 146, 82], outline=red_hi, width=2)
    reg("{gwc_gcfret", im, "Carved oxblood-crimson wood open lattice vestibule partition (#166)")

    # 14. Honey-teak 4x4 square-coffered booth privacy screen (#163, #165)
    im = Image.new("RGB", (256, 256), (114, 64, 30))
    grain = _periodic_fbm(256, 256, (2, 16, 32), seed=213)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    # Fine vertical wood grain streaks
    vg = np.sin(xx * 0.45 + grain * 4.5) * 7.5
    arr = np.array(im, dtype=np.float32)
    arr[:, :, 0] += vg * 1.1 + grain * 5.0
    arr[:, :, 1] += vg * 0.7 + grain * 3.5
    arr[:, :, 2] += vg * 0.35 + grain * 2.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for gy in range(4):
        for gx in range(4):
            x0, y0 = gx * 64, gy * 64
            x1, y1 = x0 + 63, y0 + 63
            d.rectangle([x0, y0, x1, y1], outline=(46, 24, 12), width=3)
            # Top/Left sunlit chamfer bevels & Bottom/Right shaded bevels
            d.polygon([(x0 + 3, y0 + 3), (x1 - 3, y0 + 3), (x1 - 15, y0 + 15), (x0 + 15, y0 + 15)], fill=(148, 88, 44))
            d.polygon([(x0 + 3, y0 + 3), (x0 + 15, y0 + 15), (x0 + 15, y1 - 15), (x0 + 3, y1 - 3)], fill=(134, 78, 38))
            d.polygon([(x1 - 3, y0 + 3), (x1 - 3, y1 - 3), (x1 - 15, y1 - 15), (x1 - 15, y0 + 15)], fill=(80, 42, 18))
            d.polygon([(x0 + 3, y1 - 3), (x0 + 15, y1 - 15), (x1 - 15, y1 - 15), (x1 - 3, y1 - 3)], fill=(68, 36, 16))
            d.rectangle([x0 + 15, y0 + 15, x1 - 15, y1 - 15], fill=(122, 70, 34), outline=(58, 30, 16))
    reg("gwc_gcscrn", im, "Honey-teak square-coffered booth privacy partition screen (#163, #165)")

    # 15. Framed Guilin karst mountain & river celadon landscape mural (#165)
    yy_m, xx_m = np.mgrid[0:256, 0:512].astype(np.float32)
    mist = _periodic_fbm(512, 256, (2, 4, 8), seed=214)
    paper = _periodic_fbm(512, 256, (16, 32), seed=216)
    # Soft misty celadon silk sky base transitioning into lower river mist
    sky_grad = np.clip(182.0 - 10.0 * (yy_m / 255.0) + mist * 8.0 + paper * 3.0, 0, MAX_ALBEDO)
    mural = np.stack([sky_grad - 2.0, sky_grad + 4.0, sky_grad - 6.0], axis=-1)
    # Rounded organic Guilin karst limestone dome profiles (smooth harmonic peaks + mist fade at bases)
    p1 = 152.0 - 78.0 * np.exp(-((xx_m - 122.0) / 56.0) ** 2) - 96.0 * np.exp(-((xx_m - 252.0) / 62.0) ** 2) - 82.0 * np.exp(-((xx_m - 388.0) / 58.0) ** 2) + mist * 9.0
    p2 = 172.0 - 66.0 * np.exp(-((xx_m - 86.0) / 48.0) ** 2) - 86.0 * np.exp(-((xx_m - 208.0) / 54.0) ** 2) - 74.0 * np.exp(-((xx_m - 332.0) / 52.0) ** 2) - 62.0 * np.exp(-((xx_m - 442.0) / 46.0) ** 2) + mist * 7.0
    mask_far = (yy_m > p1) & (yy_m < 178.0)
    fade_far = np.clip((178.0 - yy_m) / 58.0, 0.25, 1.0)
    for ch_i, col_v in enumerate((118.0, 146.0, 132.0)):
        mural[mask_far, ch_i] = mural[mask_far, ch_i] * (1.0 - 0.72 * fade_far[mask_far]) + col_v * (0.72 * fade_far[mask_far])
    mask_mid = (yy_m > p2) & (yy_m < 188.0)
    fade_mid = np.clip((188.0 - yy_m) / 52.0, 0.28, 1.0)
    for ch_i, col_v in enumerate((76.0, 114.0, 94.0)):
        mural[mask_mid, ch_i] = mural[mask_mid, ch_i] * (1.0 - 0.80 * fade_mid[mask_mid]) + col_v * (0.80 * fade_mid[mask_mid])
    im = Image.fromarray(np.clip(mural, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Tranquil jade river basin & forested rocky banks
    d.polygon([(18, 236), (18, 182), (96, 184), (168, 206), (226, 236)], fill=(60, 92, 74))
    d.polygon([(294, 236), (344, 204), (424, 184), (494, 178), (494, 236)], fill=(54, 84, 68))
    for ry in range(186, 232, 9):
        d.line([(168 + (ry % 28), ry), (326 - (ry % 18), ry)], fill=(138, 154, 142), width=1)
    # Ink-painted riverside pine boughs & tiny river sampan boat silhouette
    for tx, ty in ((62, 174), (88, 182), (434, 170), (460, 178)):
        d.line([(tx, ty + 24), (tx + 3, ty)], fill=(36, 42, 34), width=3)
        d.ellipse([tx - 16, ty - 8, tx + 16, ty + 4], fill=(42, 72, 52))
        d.ellipse([tx - 10, ty - 14, tx + 12, ty - 3], fill=(48, 82, 58))
    d.polygon([(224, 212), (254, 212), (248, 217), (230, 217)], fill=(48, 44, 38))
    # Red vermilion artist seal chops & ink title column top-left
    f_chop = cjk_font(14, "song_serif")
    d.text((38, 30), "桂", font=f_chop, fill=(42, 46, 44))
    d.text((38, 46), "林", font=f_chop, fill=(42, 46, 44))
    d.rectangle([38, 66, 52, 80], fill=(154, 42, 34))
    d.rectangle([456, 206, 472, 222], fill=(154, 42, 34))
    # Cream silk mat & dark espresso carved outer wood frame
    d.rectangle([12, 12, 499, 243], outline=(186, 178, 158), width=10)
    d.rectangle([21, 21, 490, 234], outline=(84, 72, 56), width=1)
    d.rectangle([0, 0, 511, 255], outline=(36, 24, 16), width=12)
    reg("gwc_gcmural", im, "Framed misty jade Guilin karst mountain landscape mural (#165)")

    # 16. Split navy-blue plum-blossom restroom noren doorway curtain (#163)
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    navy = (28, 42, 74, 255)
    navy_sh = (20, 30, 56, 255)
    navy_hi = (38, 56, 94, 255)
    # Left & right split panels hanging down to y=178 with clean center walk-through gap
    for x0, x1 in ((4, 118), (138, 251)):
        d.rectangle([x0, 0, x1, 178], fill=navy)
        for fx in range(x0 + 18, x1 - 10, 28):
            d.line([(fx, 14), (fx, 176)], fill=navy_sh, width=3)
            d.line([(fx + 4, 14), (fx + 4, 176)], fill=navy_hi, width=2)
        d.line([(x0, 177), (x1, 177)], fill=(44, 62, 102, 255), width=2)
    # Top rod sleeve linking across doorway top
    d.rectangle([4, 0, 251, 13], fill=(22, 32, 58, 255))
    # Crisp white plum blossoms & sumi-e brushstroke arcs across both panels
    wh = (188, 190, 186, 255)
    d.arc([24, 34, 108, 148], 310, 120, fill=wh, width=5)
    d.arc([148, 28, 232, 144], 60, 230, fill=wh, width=5)
    for bx, by, r in ((58, 66, 13), (88, 118, 10), (176, 56, 11), (206, 108, 14), (168, 136, 8)):
        for p in range(5):
            a = p * (2.0 * math.pi / 5.0)
            px = int(bx + math.cos(a) * (r * 0.58))
            py = int(by + math.sin(a) * (r * 0.58))
            d.ellipse([px - r // 2, py - r // 2, px + r // 2, py + r // 2], fill=wh)
        d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=navy)
    reg("{gwc_gcnoren", im, "Split navy-blue plum-blossom doorway noren curtain (#163)")

    # 17. High-visibility emerald green bike-lane conflict pavement paint (#114, #150)
    im = make_rgb_tex(256, 256, (68, 140, 74), amp=9.0, base_freq=8, octaves=4, seed=215, speckle=4.5)
    arr = np.array(im, dtype=np.float32)
    # Subtle weathered tire-track asphalt wear peeking down middle-left/right
    xx = np.arange(256, dtype=np.float32)[None, :]
    wear = np.exp(-((xx - 84.0) / 28.0) ** 2) + np.exp(-((xx - 172.0) / 28.0) ** 2)
    arr = arr * (1.0 - 0.14 * wear[:, :, None]) + np.array([76.0, 80.0, 82.0]) * (0.14 * wear[:, :, None])
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Crisp dashed white edge borders along left and right sides
    for dy in range(8, 256, 64):
        d.rectangle([8, dy, 20, min(255, dy + 40)], fill=(192, 192, 188))
        d.rectangle([235, dy, 247, min(255, dy + 40)], fill=(192, 192, 188))
    # Centered crisp white bicycle stencil + forward directional arrow
    wh_road = (194, 194, 190)
    d.polygon([(128, 36), (106, 66), (120, 66), (120, 92), (136, 92), (136, 66), (150, 66)], fill=wh_road)
    d.ellipse([76, 152, 112, 188], outline=wh_road, width=5)
    d.ellipse([144, 152, 180, 188], outline=wh_road, width=5)
    d.line([(94, 170), (118, 134), (150, 134), (162, 170), (126, 170), (118, 134)], fill=wh_road, width=5)
    d.line([(114, 128), (126, 128)], fill=wh_road, width=5)
    d.line([(146, 124), (156, 124), (150, 134)], fill=wh_road, width=4)
    reg("gwc_bikelane", im, "Green thermoplastic intersection bike lane conflict pavement (#114, #150)")

    # 18. Painted desert-sunset & canyon mesas mural on traffic utility box (#114, #115)
    yy_u, xx_u = np.mgrid[0:256, 0:256].astype(np.float32)
    sky_t = np.clip(yy_u / 130.0, 0.0, 1.0)
    paint_grain = _periodic_fbm(256, 256, (8, 16, 32), seed=217) * 4.5
    box = np.zeros((256, 256, 3), dtype=np.float32)
    box[:, :, 0] = 44.0 + sky_t * 36.0 + paint_grain
    box[:, :, 1] = 158.0 + sky_t * 14.0 + paint_grain
    box[:, :, 2] = 172.0 - sky_t * 28.0 + paint_grain
    im = Image.fromarray(np.clip(box, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Warm sunset sun glow & layered cloud wisps
    d.ellipse([148, 22, 198, 72], fill=(202, 162, 74))
    d.polygon([(14, 48), (44, 34), (92, 36), (124, 48), (94, 54), (40, 54)], fill=(176, 194, 188))
    d.polygon([(144, 62), (178, 52), (230, 54), (248, 64), (214, 68), (160, 68)], fill=(192, 188, 174))
    # Distant plum-violet stepped mesa canyon silhouettes
    d.polygon([(0, 146), (26, 94), (62, 82), (96, 86), (126, 118), (168, 76), (206, 74), (236, 98), (255, 116), (255, 166), (0, 166)], fill=(122, 74, 112))
    # Sunlit marigold-amber sandstone bluff bands
    d.polygon([(0, 188), (20, 134), (58, 122), (88, 124), (118, 152), (156, 112), (198, 114), (232, 138), (255, 148), (255, 200), (0, 200)], fill=(196, 126, 46))
    # Warm terracotta valley ridges & foreground chaparral shrubs
    d.polygon([(0, 224), (44, 172), (108, 186), (174, 160), (232, 184), (255, 176), (255, 255), (0, 255)], fill=(164, 82, 52))
    for bx, by, rx, ry in ((26, 226, 24, 14), (88, 232, 28, 16), (162, 228, 26, 15), (224, 232, 28, 16)):
        d.ellipse([bx - rx, by - ry, bx + rx, by + ry], fill=(78, 118, 66))
        d.ellipse([bx - rx // 2, by - ry - 4, bx + rx // 2, by + ry // 2], fill=(96, 136, 78))
    d.rectangle([0, 240, 255, 255], fill=(60, 78, 56))
    # Subtle cabinet door center seam, steel latch handle & lower louver vents
    d.line([(128, 8), (128, 248)], fill=(34, 48, 52), width=2)
    d.rectangle([114, 122, 122, 146], fill=(166, 168, 170), outline=(42, 46, 50))
    for vy in range(202, 232, 6):
        d.line([(204, vy), (242, vy)], fill=(48, 60, 46), width=2)
    reg("gwc_utilart", im, "Painted desert-sunset canyon mural on NE Union/E 4th utility box (#114, #115)")


def build_great_castle_signage() -> None:
    """Build verified Great Castle (410 Union Ave) & corridor signage decals (Phase 2A)."""
    # 1. Great Castle West Wall crimson 3D channel letters + 4th bleached empty housing (#130, #162)
    im = make_rgb_tex(1024, 128, (186, 183, 176), amp=7.0, base_freq=8, octaves=3, seed=218, speckle=1.6)
    arr = np.array(im, dtype=np.float32)
    for y0 in (0, 32, 64, 96):
        arr[y0 : y0 + 2, :, :] -= 13.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    eng_txt = "GREAT CASTLE RESTAURANT"
    f_eng = fit_font(d, eng_txt, "impact", 690, 86, start_size=74)
    eb = d.textbbox((0, 0), eng_txt, font=f_eng)
    ex = 22
    ey = (128 - (eb[3] - eb[1])) // 2 - eb[1]
    for dx, dy in ((4, 4), (3, 3), (2, 2)):
        d.text((ex + dx, ey + dy), eng_txt, font=f_eng, fill=(40, 22, 22))
    d.text((ex, ey), eng_txt, font=f_eng, fill=(164, 24, 30))
    # Three crisp red 3D Traditional Chinese characters (長城飯) + 4th weathered bleached empty channel box
    f_cn = cjk_font(56, "jheng_bold")
    for idx, ch in enumerate("長城飯"):
        cx = 746 + idx * 62
        cy = 64
        draw_centered(d, cx + 3, cy + 3, ch, f_cn, (38, 22, 22))
        draw_centered(d, cx, cy, ch, f_cn, (164, 24, 30))
    # 4th empty sun-bleached aluminum channel can trace (missing red acrylic face #130)
    d.rectangle([938, 34, 994, 94], fill=(172, 166, 150), outline=(92, 86, 76), width=3)
    d.rectangle([944, 40, 988, 88], fill=(178, 173, 158), outline=(128, 122, 110), width=1)
    reg("gwc_gcwest", im, "West wall red 3D channel sign GREAT CASTLE RESTAURANT + 長城飯 & bleached 4th box (#130, #162)")

    # 2. Union curb 2-post white pylon face (#129, #130, #149, #150)
    im = Image.new("RGB", (512, 256), (192, 190, 184))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 511, 255], outline=(42, 46, 52), width=8)
    d.rectangle([10, 10, 501, 245], outline=(146, 144, 138), width=2)
    f_p1 = fit_font(d, "GREAT CASTLE", "impact", 456, 84, start_size=76)
    draw_centered(d, 256, 62, "GREAT CASTLE", f_p1, (162, 24, 28))
    f_p2 = fit_font(d, "R E S T A U R A N T", "bold", 424, 44, start_size=40)
    draw_centered(d, 256, 134, "R E S T A U R A N T", f_p2, (162, 24, 28))
    d.line([(24, 174), (487, 174)], fill=(48, 50, 56), width=3)
    # Sun-faded lower red/pink accent band (illegible in SV, kept clean without invented copy #130)
    d.rectangle([24, 184, 487, 232], fill=(182, 138, 134), outline=(144, 128, 122), width=1)
    d.rectangle([32, 192, 479, 224], fill=(176, 146, 142))
    reg("gwc_gcpylon", im, "White Union curb pylon cabinet GREAT CASTLE / RESTAURANT (#130, #149)")

    # 3. SW watchtower illuminated mustard-yellow plaque (城堡, #130, #161)
    diff = Image.new("RGB", (256, 128), (192, 154, 46))
    glow = Image.new("RGB", (256, 128), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    dg.rectangle([8, 8, 247, 119], fill=(154, 122, 34))
    dd.rectangle([0, 0, 255, 127], outline=(44, 34, 24), width=8)
    dd.rectangle([8, 8, 247, 119], outline=(128, 98, 30), width=2)
    f_pl = cjk_font(74, "song_serif")
    draw_centered(dd, 128, 62, "城 堡", f_pl, (76, 46, 22))
    draw_centered(dg, 128, 62, "城 堡", f_pl, (34, 20, 10))
    reg("gwc_gcplaque", diff, "SW watchtower illuminated yellow plaque reading 城堡 (#130, #161)", glow=glow)

    # 4. SW watchtower west corner black address numbers 410 (#130, #161, matched to gwc_gccmu)
    im = make_rgb_tex(128, 64, (186, 185, 180), amp=8.5, base_freq=4, octaves=4, seed=219, speckle=1.8)
    arr = np.array(im, dtype=np.float32)
    arr[31:33, :, :] -= 16.0
    arr[33:35, :, :] += 5.0
    arr[0:31, 63:65, :] -= 13.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f_410 = fit_font(d, "410", "bold", 96, 46, start_size=40)
    draw_centered(d, 64, 32, "410", f_410, (28, 30, 34))
    reg("gwc_gc410", im, "SW watchtower west wall black address numbers 410 (#130, #161)")

    # 5. Illuminated entrance OPEN sign (#130, #161, #164)
    diff = Image.new("RGB", (128, 64), (194, 194, 190))
    glow = Image.new("RGB", (128, 64), (0, 0, 0))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    dg.rectangle([5, 5, 122, 58], fill=(138, 138, 132))
    dd.rectangle([0, 0, 127, 63], outline=(32, 34, 38), width=5)
    f_op = fit_font(dd, "OPEN", "impact", 104, 44, start_size=42)
    draw_centered(dd, 64, 32, "OPEN", f_op, (168, 24, 28))
    draw_centered(dg, 64, 32, "OPEN", f_op, (220, 34, 38))
    reg("gwc_gcopen", diff, "Backlit entrance white hanging sign OPEN (#130, #161)", glow=glow)

    # 6. Crimson Tsingtao paper sphere lantern skin w/ backlit glow (#130, #163, #165)
    diff = Image.new("RGB", (256, 256), (154, 24, 28))
    glow = Image.new("RGB", (256, 256), (144, 24, 18))
    dd, dg = ImageDraw.Draw(diff), ImageDraw.Draw(glow)
    # Horizontal bamboo frame ribs + antique gold top/bottom collars
    for ry in range(28, 228, 16):
        dd.line([(0, ry), (255, ry)], fill=(122, 16, 20), width=2)
        dg.line([(0, ry), (255, ry)], fill=(112, 18, 14), width=1)
    for gy0, gy1 in ((0, 20), (236, 255)):
        dd.rectangle([0, gy0, 255, gy1], fill=(166, 132, 48))
        dg.rectangle([0, gy0, 255, gy1], fill=(0, 0, 0))
    dd.line([(0, 21), (255, 21)], fill=(96, 68, 24), width=2)
    dd.line([(0, 235), (255, 235)], fill=(96, 68, 24), width=2)
    # Front half (u=0..0.5, cx=68): Tsingtao crest, curved band + 青島啤酒
    dd.ellipse([48, 52, 88, 86], fill=(196, 196, 190), outline=(176, 142, 56), width=2)
    dg.ellipse([48, 52, 88, 86], fill=(224, 224, 212))
    dd.ellipse([58, 58, 78, 78], fill=(38, 108, 62))
    dd.rectangle([16, 94, 120, 128], fill=(196, 196, 190), outline=(176, 142, 56), width=2)
    dg.rectangle([16, 94, 120, 128], fill=(228, 226, 214))
    f_ts = fit_font(dd, "TSINGTAO", "bold", 96, 26, start_size=22)
    draw_centered(dd, 68, 110, "TSINGTAO", f_ts, (148, 24, 28))
    draw_centered(dg, 68, 110, "TSINGTAO", f_ts, (162, 24, 28))
    dd.line([(26, 136), (110, 136)], fill=(196, 196, 190), width=3)
    dg.line([(26, 136), (110, 136)], fill=(220, 218, 206), width=3)
    f_qp = cjk_font(22, "jheng_bold")
    draw_centered(dd, 68, 158, "青島啤酒", f_qp, (196, 196, 190))
    draw_centered(dg, 68, 158, "青島啤酒", f_qp, (226, 224, 210))
    # Opposite UV side (u=0.5..1.0, cx=192): vertical gold-on-red Chinese character strip (#130)
    dd.rectangle([170, 44, 214, 212], fill=(132, 18, 22), outline=(182, 148, 58), width=2)
    dg.rectangle([170, 44, 214, 212], fill=(120, 16, 18))
    f_vert = cjk_font(28, "song_serif")
    for idx, ch in enumerate("萬事如意"):
        draw_centered(dd, 192, 66 + idx * 38, ch, f_vert, (192, 164, 72))
        draw_centered(dg, 192, 66 + idx * 38, ch, f_vert, (214, 184, 86))
    reg("gwc_gclant", diff, "Crimson Tsingtao / vertical gold-char hanging paper lantern skin (#130, #163)", glow=glow)

    # 7. Crisp framed cream REST ROOMS transom plaque (#130, #163)
    im = Image.new("RGB", (256, 64), (194, 190, 178))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, 63], outline=(40, 28, 20), width=5)
    d.rectangle([6, 6, 249, 57], outline=(116, 108, 94), width=1)
    f_rr = fit_font(d, "REST ROOMS", "bold", 216, 40, start_size=34)
    draw_centered(d, 128, 32, "REST ROOMS", f_rr, (30, 32, 36))
    reg("gwc_gcrest", im, "Cream plaque reading REST ROOMS above split noren (#130, #163)")

    # 8. Vestibule crimson/gold 5-flap brocade banner reading R-to-L 萬事如意 (#130, #166)
    im = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 6, 503, 24], fill=(166, 134, 52, 255), outline=(92, 68, 24, 255), width=2)
    flap_w = 96
    cloth_chars = ["意", "如", "事", "萬"]  # R-to-L order left-to-right on cloth (#130, #166)
    f_ban = cjk_font(54, "song_serif")
    for idx in range(5):
        fx0 = 10 + idx * 99
        fx1 = fx0 + flap_w - 4
        d.rectangle([fx0, 22, fx1, 106], fill=(138, 20, 26, 255), outline=(182, 148, 58, 255), width=3)
        # Fringed gold bullion hem tufts along bottom edge of each flap
        for tx in range(fx0 + 4, fx1 - 3, 6):
            d.line([(tx, 107), (tx, 118)], fill=(182, 148, 58, 255), width=2)
        if 1 <= idx <= 4:
            draw_centered(d, (fx0 + fx1) // 2 + 2, 65, cloth_chars[idx - 1], f_ban, (82, 12, 16, 255))
            draw_centered(d, (fx0 + fx1) // 2, 63, cloth_chars[idx - 1], f_ban, (198, 170, 74, 255))
        else:
            cx, cy = (fx0 + fx1) // 2, 63
            d.ellipse([cx - 24, cy - 26, cx + 24, cy + 26], fill=(168, 132, 48, 255), outline=(96, 68, 24, 255), width=2)
            d.ellipse([cx - 12, cy - 16, cx + 12, cy + 8], fill=(194, 166, 132, 255))
    im = enforce_transparent_border(im, pad_xy=4, pad_top=4, pad_bot=6)
    reg("{gwc_gcbann", im, "Vestibule crimson/gold 5-flap brocade valance 意如事萬 (#130, #166)")

    # 9. Vestibule pleated semi-circular red/gold 福 fan above doorway (#130, #166)
    im = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 128, 118
    r_out = 104
    d.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out], 198, 342, fill=(144, 22, 28, 255), outline=(188, 156, 62, 255), width=4)
    for k in range(13):
        ang = math.radians(198 + k * (144.0 / 12.0))
        x2 = int(cx + math.cos(ang) * (r_out - 4))
        y2 = int(cy + math.sin(ang) * (r_out - 4))
        d.line([(cx, cy), (x2, y2)], fill=(176, 140, 52, 255), width=2)
    d.pieslice([cx - 44, cy - 44, cx + 44, cy + 44], 198, 342, fill=(168, 134, 48, 255), outline=(96, 68, 22, 255), width=2)
    f_fan = cjk_font(40, "song_serif")
    draw_centered(d, cx, cy - 42, "福", f_fan, (198, 172, 76, 255), outline=(96, 24, 24, 255), outline_w=2)
    im = enforce_transparent_border(im, pad_xy=6, pad_top=6, pad_bot=4)
    reg("{gwc_gcfan", im, "Vestibule pleated crimson-and-gold 福 wall fan (#130, #166)")

    # 10. Red diamond 福 wall plaque for dining cream plaster panels (#130, #163, #165)
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(64, 10), (118, 64), (64, 118), (10, 64)], fill=(154, 22, 28, 255), outline=(192, 160, 64, 255))
    d.polygon([(64, 18), (110, 64), (64, 110), (18, 64)], outline=(192, 160, 64, 255), width=3)
    d.polygon([(64, 26), (102, 64), (64, 102), (26, 64)], outline=(104, 16, 20, 255), width=2)
    draw_centered(d, 64, 62, "福", cjk_font(54, "song_serif"), (198, 170, 74, 255))
    im = enforce_transparent_border(im, pad_xy=6, pad_top=6, pad_bot=6)
    reg("{gwc_gcfu", im, "Red/gold diamond 福 wall hanging for dining plaster bays (#130, #163)")

    # 11. Framed Tang poem Maple Bridge Night Mooring calligraphy scroll (#130, #163)
    im = Image.new("RGB", (256, 256), (186, 176, 148))
    paper = _periodic_fbm(256, 256, (4, 8, 16), seed=220)
    arr = np.array(im, dtype=np.float32) + paper[:, :, None] * 6.0
    im = Image.fromarray(np.clip(arr, 0, MAX_ALBEDO).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Vertical R-to-L columns matching Zhang Ji's poem photographed in #163
    cols = [
        "月落烏啼霜滿",
        "天江楓漁火",
        "對愁眠姑蘇",
        "城外寒山寺",
        "夜半鐘聲",
        "到客船。",
    ]
    f_po = cjk_font(22, "song_serif")
    for c_idx, col_txt in enumerate(cols):
        cx = 216 - c_idx * 34
        for r_idx, ch in enumerate(col_txt):
            cy = 34 + r_idx * 32
            draw_centered(d, cx, cy, ch, f_po, (32, 30, 28))
    d.rectangle([28, 198, 44, 222], fill=(154, 40, 32))
    d.rectangle([10, 10, 245, 245], outline=(168, 158, 134), width=5)
    d.rectangle([0, 0, 255, 255], outline=(38, 26, 18), width=10)
    reg("gwc_gccallig", im, "Framed aged parchment Maple Bridge Night Mooring calligraphy scroll (#130, #163)")

    # 12 & 13. Bakersfield green reflective cross-street blades E 4th St & E 5th St
    for blade_name, label in (("gwc_e4st", "E 4th St"), ("gwc_e5st", "E 5th St")):
        im = Image.new("RGB", (256, 64), (32, 106, 60))
        d = ImageDraw.Draw(im)
        d.rectangle([3, 3, 252, 60], outline=(192, 194, 190), width=3)
        f_st = fit_font(d, label, "bold", 220, 42, start_size=36)
        draw_centered(d, 128, 32, label, f_st, (196, 196, 192))
        reg(blade_name, im, f"Bakersfield green reflective street name blade {label}")

    # 14. Deal Time Auto Sales SE Union/E 4th dark-charcoal cutout signage on white stucco (#141, #147)
    im = make_rgb_tex(512, 128, (191, 187, 177), amp=9.0, base_freq=8, octaves=4, seed=221, speckle=2.0)
    d = ImageDraw.Draw(im)
    f_dt1 = fit_font(d, "DEAL TIME", "impact", 456, 62, start_size=54)
    draw_centered(d, 259, 47, "DEAL TIME", f_dt1, (118, 114, 108))
    draw_centered(d, 256, 44, "DEAL TIME", f_dt1, (36, 38, 42))
    d.line([(56, 80), (455, 80)], fill=(154, 32, 34), width=2)
    f_dt2 = fit_font(d, "A U T O   S A L E S", "bold", 420, 26, start_size=22)
    draw_centered(d, 258, 99, "A U T O   S A L E S", f_dt2, (124, 120, 114))
    draw_centered(d, 256, 97, "A U T O   S A L E S", f_dt2, (42, 44, 48))
    reg("gwc_dealtime", im, "Deal Time Auto Sales charcoal cutout letters on white stucco (SE Union/E 4th, #141)")

    # 15. Reyes Tire Shop wide horizontal service fascia banner (#049, #130)
    im = Image.new("RGB", (512, 64), (192, 190, 184))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 511, 63], outline=(126, 116, 102), width=3)
    d.line([(8, 10), (503, 10)], fill=(154, 34, 34), width=2)
    d.line([(8, 53), (503, 53)], fill=(154, 34, 34), width=2)
    parts = ["A/C", "ALIGNMENT", "BRAKES", "TUNE-UP", "MUFFLERS"]
    gap_w = 16
    f_ry = font("bold", 17)
    for sz in (18, 17, 16, 15):
        f_try = font("bold", sz)
        tot = sum(d.textbbox((0, 0), p, font=f_try)[2] - d.textbbox((0, 0), p, font=f_try)[0] for p in parts) + 4 * gap_w
        if tot <= 472:
            f_ry = f_try
            break
    total_w = sum(d.textbbox((0, 0), p, font=f_ry)[2] - d.textbbox((0, 0), p, font=f_ry)[0] for p in parts) + 4 * gap_w
    cx = (512 - total_w) // 2
    for idx, p in enumerate(parts):
        bb = d.textbbox((0, 0), p, font=f_ry)
        pw = bb[2] - bb[0]
        ph = bb[3] - bb[1]
        d.text((cx - bb[0], 32 - ph // 2 - bb[1]), p, font=f_ry, fill=(28, 30, 34))
        cx += pw
        if idx < len(parts) - 1:
            d.ellipse([cx + 4, 28, cx + 12, 36], fill=(162, 26, 30))
            cx += gap_w
    reg("gwc_reyes", im, "Reyes Tire Shop horizontal white service fascia banner (#049, #130)")

    # 16. Reyes Tire Shop two-sided pole sign cabinet (#049, #130)
    im = Image.new("RGB", (256, 256), (192, 190, 184))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, 255], outline=(48, 52, 58), width=8)
    d.rectangle([14, 16, 241, 76], fill=(166, 170, 174), outline=(92, 96, 104), width=2)
    f_rp1 = fit_font(d, "REYES TIRE SHOP", "bold", 210, 40, start_size=26)
    draw_centered(d, 128, 46, "REYES TIRE SHOP", f_rp1, (48, 52, 58))
    d.line([(16, 86), (239, 86)], fill=(154, 30, 34), width=3)
    f_rp2 = fit_font(d, "Y MOFLES", "impact", 212, 68, start_size=54)
    draw_centered(d, 128, 128, "Y MOFLES", f_rp2, (30, 34, 40))
    d.line([(16, 170), (239, 170)], fill=(38, 72, 118), width=3)
    # Clean weathered lower blue/red accent rules without invented illegible text (#130)
    d.rectangle([22, 184, 233, 208], fill=(176, 174, 168))
    d.rectangle([22, 218, 233, 234], fill=(164, 168, 174))
    reg("gwc_reyespole", im, "Reyes Tire Shop white pole sign reading Y MOFLES (#049, #130)")

    # 17. DG market fascia sign across Union Ave (#130, #149, #150)
    im = Image.new("RGB", (256, 128), (34, 38, 42))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 10, 108, 117], fill=(198, 174, 34))
    f_dg = fit_font(d, "DG", "impact", 84, 88, start_size=78)
    draw_centered(d, 58, 63, "DG", f_dg, (24, 26, 28))
    d.rectangle([114, 10, 247, 117], fill=(34, 126, 54))
    f_mk = fit_font(d, "market", "bold", 118, 56, start_size=40)
    draw_centered(d, 180, 63, "market", f_mk, (198, 198, 194))
    reg("gwc_dgmrkt", im, "DG market yellow-and-green grocery fascia sign (west Union, #130, #149)")

    # 18. Diamond Shamrock SW Union/E 4th canopy fascia + 3-leaf shamrock (#113, #130)
    im = Image.new("RGB", (256, 128), (194, 194, 190))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, 16], fill=(28, 62, 114))
    d.rectangle([0, 17, 255, 24], fill=(164, 28, 32))
    d.rectangle([0, 104, 255, 111], fill=(164, 28, 32))
    d.rectangle([0, 112, 255, 127], fill=(34, 124, 54))
    # Crisp 3-leaf green shamrock emblem
    sx, sy = 44, 66
    for ox, oy in ((0, -14), (-12, 6), (12, 6)):
        d.ellipse([sx + ox - 11, sy + oy - 11, sx + ox + 11, sy + oy + 11], fill=(34, 128, 54))
    d.line([(sx, sy + 6), (sx, sy + 24)], fill=(34, 128, 54), width=5)
    f_sh = fit_font(d, "Shamrock", "bold", 168, 48, start_size=34)
    draw_centered(d, 158, 64, "Shamrock", f_sh, (28, 62, 114))
    reg("gwc_shamrock", im, "Diamond Shamrock SW Union/E 4th gas canopy & green 3-leaf emblem (#113, #130)")

    # 19. Warm emissive frosted alabaster dome bowl light for Dining Hall fans (#147, #165)
    yy_d, xx_d = np.mgrid[0:128, 0:128].astype(np.float32)
    rad = np.sqrt(((xx_d - 63.5) / 64.0) ** 2 + ((yy_d - 63.5) / 64.0) ** 2)
    swirl = _periodic_fbm(128, 128, (4, 8, 16), seed=222)
    rib = np.cos(xx_d * (2.0 * math.pi / 16.0)) * 4.5
    glow_band = np.clip(1.0 - 0.35 * rad, 0.45, 1.0)
    diff_d = np.zeros((128, 128, 3), dtype=np.float32)
    diff_d[:, :, 0] = 192.0 + glow_band * 11.0 + swirl * 6.0 + rib
    diff_d[:, :, 1] = 166.0 + glow_band * 22.0 + swirl * 5.0 + rib * 0.8
    diff_d[:, :, 2] = 104.0 + glow_band * 36.0 + swirl * 4.0 + rib * 0.4
    glow_d = np.zeros((128, 128, 3), dtype=np.float32)
    glow_d[:, :, 0] = 210.0 + glow_band * 42.0 + swirl * 7.0 + rib
    glow_d[:, :, 1] = 168.0 + glow_band * 56.0 + swirl * 6.0 + rib * 0.8
    glow_d[:, :, 2] = 84.0 + glow_band * 64.0 + swirl * 4.0
    # Top antique-bronze rim band on bowl lip; uniform warm alabaster below for 360-deg side + bottom UV
    diff_d[0:8, :, :] = np.array([56.0, 42.0, 28.0])
    glow_d[0:8, :, :] = 0.0
    reg(
        "gwc_gcdome",
        Image.fromarray(np.clip(diff_d, 0, MAX_ALBEDO).astype(np.uint8)),
        "Warm frosted alabaster ceiling fan dome light bowl (#147, #165)",
        glow=Image.fromarray(np.clip(glow_d, 0, 255).astype(np.uint8)),
    )


# ==============================================================================
# 4. OUTPUT ASSEMBLY & VISUAL CONTACT SHEET
# ==============================================================================


def write_contact_sheet() -> None:
    """Create a labeled QA thumbnail contact sheet for visual verification."""
    items = sorted(FULL_TEX.items(), key=lambda kv: kv[0].lstrip("{"))
    cols = 10
    cell_w, cell_h = 160, 132
    thumb_w, thumb_h = 148, 96
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * cell_w + 16, rows * cell_h + 44), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    d.text((14, 10), f"Golden West Procedural Textures ({len(items)} total, Albedo <= {MAX_ALBEDO})", fill=(235, 220, 165), font=font("bold", 18))

    for idx, (name, im) in enumerate(items):
        r, c = divmod(idx, cols)
        x0 = 8 + c * cell_w
        y0 = 40 + r * cell_h
        d.rectangle([x0 + 2, y0 + 2, x0 + cell_w - 4, y0 + cell_h - 4], fill=(38, 40, 46), outline=(66, 70, 78))
        # Checkerboard behind RGBA cutouts
        bg = Image.new("RGB", (thumb_w, thumb_h), (72, 78, 86))
        if im.mode == "RGBA":
            bd = ImageDraw.Draw(bg)
            for cy in range(0, thumb_h, 12):
                for cx in range(0, thumb_w, 12):
                    if ((cx // 12) + (cy // 12)) % 2 == 0:
                        bd.rectangle([cx, cy, cx + 11, cy + 11], fill=(108, 114, 124))
            th = im.copy()
            th.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            bg.paste(th, ((thumb_w - th.width) // 2, (thumb_h - th.height) // 2), th)
        else:
            th = im.convert("RGB").copy()
            th.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            bg.paste(th, ((thumb_w - th.width) // 2, (thumb_h - th.height) // 2))
        sheet.paste(bg, (x0 + 6, y0 + 6))
        glow_tag = " [G]" if name in GLOW_TEX else ""
        d.text((x0 + 6, y0 + 106), f"{name}{glow_tag}", fill=(224, 224, 224), font=font("mono", 11))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET_PATH, format="JPEG", quality=90)


def main() -> None:
    build_streets_and_site()
    build_foliage_and_fences()
    build_metals_trims_and_props()
    build_traffic_and_street_signs()
    build_casino_architecture_and_interiors()
    build_casino_felts_and_signage()
    build_neighborhood_surfaces_and_signs()
    build_great_castle_architecture()
    build_great_castle_signage()

    TEX_DIR.mkdir(parents=True, exist_ok=True)
    WAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove ONLY stale Golden West textures/glows in textures/ before writing
    expected_files = {f"{n}.png" for n in FULL_TEX} | {f"{n}_glow.png" for n in GLOW_TEX}
    removed = 0
    for fn in os.listdir(TEX_DIR):
        if re.match(r"^\{?gwc_", fn, re.I) and fn not in expected_files:
            (TEX_DIR / fn).unlink()
            removed += 1

    for name, im in FULL_TEX.items():
        im.save(TEX_DIR / f"{name}.png", format="PNG")
    for name, glow in GLOW_TEX.items():
        glow.save(TEX_DIR / f"{name}_glow.png", format="PNG")

    # Add compiler utility lumps to WAD2 ONLY (never textures/)
    wad_lumps = dict(WAD_TEX)
    special_cols = {
        "sky": (72, 128, 210),
        "clip": (150, 74, 34),
        "skip": (154, 150, 42),
        "trigger": (146, 38, 146),
    }
    for sp in SPECIAL_WAD_ONLY:
        im_sp = Image.new("RGB", (64, 64), special_cols[sp])
        draw_centered(ImageDraw.Draw(im_sp), 32, 32, sp.upper(), font("bold", 14), (200, 200, 198))
        wad_lumps[sp] = im_sp

    wad2.write_wad(str(WAD_PATH), wad_lumps)
    write_contact_sheet()

    manifest = {
        "count_textures": len(FULL_TEX),
        "count_glow": len(GLOW_TEX),
        "count_wad_lumps": len(wad_lumps),
        "max_albedo_cap": MAX_ALBEDO,
        "wad_path": str(WAD_PATH),
        "tex_dir": str(TEX_DIR),
        "removed_stale": removed,
        "textures": sorted(CATALOG_ROWS, key=lambda r: str(r["name"])),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"[build_textures] Wrote {len(FULL_TEX)} textures + {len(GLOW_TEX)} glow maps -> {TEX_DIR} "
        f"| {len(wad_lumps)} lumps -> {WAD_PATH} (removed {removed} stale)"
    )


if __name__ == "__main__":
    main()
