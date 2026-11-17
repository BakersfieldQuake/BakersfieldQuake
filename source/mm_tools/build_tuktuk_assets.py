"""build_tuktuk_assets.py — Textures, 960 Hz wild 3-wheel explosion physics, MD3s, skins & shader
for the Bangkok Tuk-Tuk (`veh_tuktuk` / VEH_TUKTUK = 9).

Prerequisites:
  Run `blender.exe --background --python source/mm_tools/blender_build_tuktuk.py` first
  (or pass `--blender` to invoke Blender automatically).

Usage:
  python source/mm_tools/build_tuktuk_assets.py
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
import veh_specs as vs

STAGED_ROOT = r"G:\Quake\Combat\_bakersfield_dev\staged_assets"
OUT_PROGS = os.path.join(STAGED_ROOT, "progs")
SHADER_PATH = os.path.join(STAGED_ROOT, "scripts", "vehicles.shader")
GEOM_JSON = r"C:\Users\qxdc\.gemini\antigravity\brain\2e8d87c6-94bd-47b0-991f-695f3579ece4\scratch\tuktuk_geom.json"
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
BLENDER_SCRIPT = os.path.join(HERE, "blender_build_tuktuk.py")

TT_RECTS = {
    "blue_body":   (16, 812, 168, 904),
    "stripe_seat": (176, 812, 336, 904),
    "canopy_dark": (344, 812, 496, 904),
    "roof_glow":   (16, 916, 168, 1012),
    "wire_mesh":   (176, 916, 336, 1012),
    "battery_box": (344, 916, 496, 1012),
}


# ---------------------------------------------------------------------------
# Pure Quaternion & Rotation Utilities [x, y, z, w]
# ---------------------------------------------------------------------------
def q_from_axis_angle(axis, angle: float) -> np.ndarray:
    a = np.asarray(axis, dtype=np.float64)
    n = float(np.linalg.norm(a))
    if n < 1e-9:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    a /= n
    s = math.sin(0.5 * angle)
    return np.array([a[0] * s, a[1] * s, a[2] * s, math.cos(0.5 * angle)], dtype=np.float64)


def q_mul(q1, q2) -> np.ndarray:
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ], dtype=np.float64)


def q_to_mat3(q) -> np.ndarray:
    x, y, z, w = q
    n = x * x + y * y + z * z + w * w
    if n < 1e-12:
        return np.eye(3, dtype=np.float64)
    s = 2.0 / n
    return np.array([
        [1.0 - s * (y * y + z * z), s * (x * y - w * z),       s * (x * z + w * y)],
        [s * (x * y + w * z),       1.0 - s * (x * x + z * z), s * (y * z - w * x)],
        [s * (x * z - w * y),       s * (y * z + w * x),       1.0 - s * (x * x + y * y)],
    ], dtype=np.float64)


def mat3_to_q(R: np.ndarray) -> np.ndarray:
    tr = float(R[0, 0] + R[1, 1] + R[2, 2])
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w], dtype=np.float64)
    return q / max(1e-12, float(np.linalg.norm(q)))


def integrate_q(q, omega, dt: float) -> np.ndarray:
    ang = float(np.linalg.norm(omega)) * dt
    if ang < 1e-9:
        return q
    dq = q_from_axis_angle(omega, ang)
    qn = q_mul(dq, q)
    return qn / max(1e-12, float(np.linalg.norm(qn)))


def build_blast_starburst_mesh() -> dict:
    """Multi-fin glowing plasma starburst mesh centered at origin, scaled by blast_flash track."""
    verts, norms, uvs, tris = [], [], [], []
    uc, vc = (710 + 1004) * 0.5 / vs.W_ATLAS, (808 + 1004) * 0.5 / vs.H_ATLAS
    r_tip = 24.0
    r_root = 5.5
    for k in range(6):
        th = 2.0 * math.pi * k / 6.0
        ct, st = math.cos(th), math.sin(th)
        p0 = [0.0, 0.0, 0.0]
        p1 = [ct * r_tip, st * r_tip, 0.0]
        p2 = [-st * r_root, ct * r_root, r_root * 0.85]
        p3 = [st * r_root, -ct * r_root, -r_root * 0.85]
        b = len(verts)
        verts.extend([p0, p1, p2, p3])
        norms.extend([[0.0, 0.0, 1.0], [ct, st, 0.0], [-st, ct, 0.6], [st, -ct, -0.6]])
        uvs.extend([[uc, vc]] * 4)
        tris.extend([[b, b + 1, b + 2], [b, b + 2, b + 1], [b, b + 1, b + 3], [b, b + 3, b + 1]])
    return {"name": "blast_flash", "origin": [0.0, 0.0, 32.0], "verts": verts, "norms": norms, "uvs": uvs, "tris": tris}


# ---------------------------------------------------------------------------
# 1024x1024 Atlas Texture Painting (Matched to Reference Bangkok Tuk-Tuk)
# ---------------------------------------------------------------------------
def _load_font(size: int):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def generate_tuktuk_textures() -> tuple[Image.Image, Image.Image, Image.Image, Image.Image]:
    W, H = vs.W_ATLAS, vs.H_ATLAS
    rng = np.random.default_rng(777)

    tex = Image.new("RGBA", (W, H), (22, 48, 128, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dr = ImageDraw.Draw(tex)
    dg = ImageDraw.Draw(glow)

    def paint_royal_blue(rect, diamond_plate=False):
        x0, y0, x1, y1 = rect
        h = y1 - y0
        for row in range(h):
            t = row / max(1, h - 1)
            # Clear-coat sky reflection near top, rich deep cobalt lower
            spec = 28.0 * math.exp(-((t - 0.25) / 0.14) ** 2)
            r = int(min(255, 16 + 18 * (1.0 - t) + spec))
            g = int(min(255, 68 + 46 * (1.0 - t) + spec * 1.1))
            b = int(min(255, 182 + 48 * (1.0 - t) + spec * 0.9))
            dr.line([(x0, y0 + row), (x1, y0 + row)], fill=(r, g, b, 255))
        if diamond_plate:
            for py in range(y0 + 4, y1 - 2, 10):
                off = ((py - y0) // 10) % 2 * 5
                for px in range(x0 + 4 + off, x1 - 4, 10):
                    dr.line([(px - 2, py), (px + 2, py)], fill=(90, 155, 245, 255), width=2)
                    dr.line([(px, py - 2), (px, py + 2)], fill=(12, 40, 115, 255), width=1)

    # 1. RECT_SIDE (world x=-56..58 -> u, z=8..72.5 -> v)
    paint_royal_blue(vs.RECT_SIDE, diamond_plate=False)
    sx0, sy0, sx1, sy1 = vs.RECT_SIDE
    # Lower side sill royal diamond plate + tri-color Bangkok racing stripes!
    # In RECT_SIDE, z=72.5 is top (sy0), z=8 is bottom (sy1)
    def sz(z):
        t = (z - 8.0) / (72.5 - 8.0)
        return int(sy1 - (sy1 - sy0) * max(0.0, min(1.0, t)))

    dr.rectangle([sx0, sz(26.5), sx1, sz(22.5)], fill=(228, 28, 36, 255))   # bold red stripe
    dr.rectangle([sx0, sz(22.5), sx1, sz(19.8)], fill=(246, 246, 252, 255)) # crisp white stripe
    dr.rectangle([sx0, sz(19.8), sx1, sz(17.6)], fill=(248, 200, 24, 255))  # golden yellow accent
    dr.rectangle([sx0, sz(36.0), sx1, sz(33.5)], fill=(242, 242, 248, 255)) # upper white pin
    dr.rectangle([sx0, sz(38.0), sx1, sz(36.0)], fill=(225, 25, 35, 255))   # upper red pin

    # 2. RECT_FRONT (y=-28..28 -> u, z=8..42.5 -> v)
    paint_royal_blue(vs.RECT_FRONT, diamond_plate=False)
    fx0, fy0, fx1, fy1 = vs.RECT_FRONT
    def fz(z):
        t = (z - 8.0) / (42.5 - 8.0)
        return int(fy1 - (fy1 - fy0) * max(0.0, min(1.0, t)))

    # Crisp red/white/yellow front apron racing pinstripes & radiator grille slats
    dr.rectangle([fx0, fz(39.0), fx1, fz(36.8)], fill=(228, 26, 36, 255))
    dr.rectangle([fx0, fz(36.8), fx1, fz(35.0)], fill=(248, 248, 255, 255))
    dr.rectangle([fx0, fz(26.2), fx1, fz(23.5)], fill=(248, 200, 26, 255))
    dr.rectangle([fx0, fz(23.5), fx1, fz(21.2)], fill=(246, 246, 252, 255))
    # Horizontal chrome cooling vents at nose center (above front wheel)
    cx_f = (fx0 + fx1) // 2
    for gi in range(3):
        yy = fz(28.5 - gi * 1.4)
        dr.rectangle([cx_f - 42, yy - 3, cx_f + 42, yy + 3], fill=(215, 225, 240, 255))

    # 3. RECT_REAR (y=28..-28 -> u, z=8..43 -> v)
    paint_royal_blue(vs.RECT_REAR, diamond_plate=False)
    rx0, ry0, rx1, ry1 = vs.RECT_REAR
    def rz(z):
        t = (z - 8.0) / (43.0 - 8.0)
        return int(ry1 - (ry1 - ry0) * max(0.0, min(1.0, t)))

    dr.rectangle([rx0, rz(33.5), rx1, rz(30.5)], fill=(230, 30, 38, 255))
    dr.rectangle([rx0, rz(30.5), rx1, rz(28.2)], fill=(248, 248, 252, 255))
    dr.rectangle([rx0, rz(28.2), rx1, rz(26.5)], fill=(248, 200, 24, 255))
    # Rear Thai taxi yellow plate badge center
    rcx = (rx0 + rx1) // 2
    dr.rectangle([rcx - 68, rz(23.5), rcx + 68, rz(15.0)], fill=(248, 208, 36, 255), outline=(25, 25, 30, 255), width=3)
    f_sm = _load_font(24)
    dr.text((rcx - 52, rz(22.5) + 4), "BKK 889", fill=(20, 20, 25, 255), font=f_sm)

    # 4. RECT_TOP
    paint_royal_blue(vs.RECT_TOP, diamond_plate=True)

    # 5. RECT_WHEEL (Golden-Yellow Alloy Rim + Bright Red Center Hubcap!)
    wx0, wy0, wx1, wy1 = vs.RECT_WHEEL
    dr.rectangle([wx0, wy0, wx1, wy1], fill=(24, 26, 30, 255))
    wc_x, wc_y = 128, 672
    r_tire, r_rim, r_dish, r_hub = 116, 65, 52, 24
    dr.ellipse([wc_x - r_tire, wc_y - r_tire, wc_x + r_tire, wc_y + r_tire], fill=(26, 28, 32, 255))
    dr.ellipse([wc_x - 98, wc_y - 98, wc_x + 98, wc_y + 98], outline=(42, 45, 52, 255), width=4)
    # Bright golden-yellow Tuk-Tuk wheel rim (from photo!)
    dr.ellipse([wc_x - r_rim, wc_y - r_rim, wc_x + r_rim, wc_y + r_rim], fill=(238, 178, 16, 255), outline=(170, 120, 10, 255), width=4)
    dr.ellipse([wc_x - r_dish, wc_y - r_dish, wc_x + r_dish, wc_y + r_dish], fill=(205, 148, 12, 255))
    for k in range(6):
        th = 2.0 * math.pi * k / 6.0
        px, py = int(wc_x + math.cos(th) * 38), int(wc_y + math.sin(th) * 38)
        dr.ellipse([px - 6, py - 6, px + 6, py + 6], fill=(115, 78, 8, 255))
    # Bright Red Center Hubcap (from photo!)
    dr.ellipse([wc_x - r_hub, wc_y - r_hub, wc_x + r_hub, wc_y + r_hub], fill=(224, 26, 34, 255), outline=(140, 12, 18, 255), width=3)
    dr.ellipse([wc_x - 8, wc_y - 8, wc_x + 8, wc_y + 8], fill=(245, 95, 95, 255))

    # 6. RECT_TREAD
    tx0, ty0, tx1, ty1 = vs.RECT_TREAD
    dr.rectangle([tx0, ty0, tx1, ty1], fill=(28, 30, 34, 255))
    for yy in range(ty0, ty1, 14):
        dr.rectangle([tx0 + 8, yy, tx1 - 8, yy + 6], fill=(18, 19, 22, 255))
        dr.line([(tx0 + 18, yy + 2), (tx1 - 18, yy + 10)], fill=(12, 13, 15, 255), width=3)

    # 7. RECT_GLASS (Clear tinted sky-reflective windshield)
    gx0, gy0, gx1, gy1 = vs.RECT_GLASS
    for row in range(gy1 - gy0):
        t = row / max(1, gy1 - gy0 - 1)
        shade = int(175 + 45 * math.sin(t * math.pi))
        dr.line([(gx0, gy0 + row), (gx1, gy0 + row)], fill=(shade - 20, shade, min(255, shade + 24), 255))
    dr.line([(gx0 + 25, gy1 - 30), (gx1 - 25, gy0 + 30)], fill=(240, 248, 255, 255), width=14)
    dr.line([(gx0 + 55, gy1 - 20), (gx1 - 10, gy0 + 60)], fill=(230, 242, 255, 255), width=6)

    # 8. RECT_CHROME (Shiny polished stainless/chrome bars & torpedo housings)
    cx0, cy0, cx1, cy1 = vs.RECT_CHROME
    for row in range(cy1 - cy0):
        t = row / max(1, cy1 - cy0 - 1)
        band = int(165 + 85 * math.sin(t * math.pi * 2.5))
        band = max(95, min(252, band))
        dr.line([(cx0, cy0 + row), (cx1, cy0 + row)], fill=(band - 6, band, min(255, band + 8), 255))

    # 8b. RECT_TRIM (Matte dark charcoal rubber, mirrors, fork gaiters & mudflaps)
    trx0, try0, trx1, try1 = vs.RECT_TRIM
    dr.rectangle([trx0, try0, trx1, try1], fill=(28, 30, 35, 255))
    for _ in range(90):
        px = int(rng.integers(trx0 + 4, trx1 - 4))
        py = int(rng.integers(try0 + 4, try1 - 4))
        dr.point((px, py), fill=(44, 46, 52, 255))

    # 9. Custom Sub-Rectangles
    # blue_body (diamond-plate + cobalt metallic)
    paint_royal_blue(TT_RECTS["blue_body"], diamond_plate=True)

    # stripe_seat (crisp vertical RED & WHITE vinyl stripes!)
    stx0, sty0, stx1, sty1 = TT_RECTS["stripe_seat"]
    n_stripes = 6
    sw = (stx1 - stx0) / n_stripes
    for i in range(n_stripes):
        col = (224, 24, 42, 255) if (i % 2 == 0) else (246, 240, 232, 255)
        dr.rectangle([int(stx0 + i * sw), sty0, int(stx0 + (i + 1) * sw), sty1], fill=col)
    # piping trim along bottom/top of upholstery swatch
    dr.rectangle([stx0, sty0, stx1, sty0 + 5], fill=(22, 68, 175, 255))
    dr.rectangle([stx0, sty1 - 5, stx1, sty1], fill=(22, 68, 175, 255))

    # canopy_dark (charcoal canvas fabric w/ subtle stitched hoop ribs)
    cdx0, cdy0, cdx1, cdy1 = TT_RECTS["canopy_dark"]
    dr.rectangle([cdx0, cdy0, cdx1, cdy1], fill=(40, 44, 52, 255))
    for rx in range(cdx0 + 24, cdx1 - 12, 32):
        dr.line([(rx, cdy0), (rx, cdy1)], fill=(26, 28, 34, 255), width=3)

    # roof_glow (amber glowing roof taxi sign pod + Bangkok badge plate!)
    rgx0, rgy0, rgx1, rgy1 = TT_RECTS["roof_glow"]
    dr.rectangle([rgx0, rgy0, rgx1, rgy1], fill=(252, 212, 74, 255))
    dg.rectangle([rgx0, rgy0, rgx1, rgy1], fill=(245, 195, 55, 255))
    f_tx = _load_font(28)
    dr.text((rgx0 + 40, rgy0 + 30), "TAXI", fill=(165, 42, 18, 255), font=f_tx)

    # wire_mesh (diamond safety cage behind driver — drawn clipped inside rect so TAXI stays clean!)
    wmx0, wmy0, wmx1, wmy1 = TT_RECTS["wire_mesh"]
    wm_im = Image.new("RGBA", (wmx1 - wmx0, wmy1 - wmy0), (26, 28, 32, 255))
    wm_dr = ImageDraw.Draw(wm_im)
    for k in range(-120, 220, 14):
        wm_dr.line([(k, 0), (k + 90, wmy1 - wmy0)], fill=(130, 138, 150, 255), width=2)
        wm_dr.line([(k + 90, 0), (k, wmy1 - wmy0)], fill=(130, 138, 150, 255), width=2)
    tex.paste(wm_im, (wmx0, wmy0))

    # battery_box (silver/grey metal box w/ black clasp)
    bbx0, bby0, bbx1, bby1 = TT_RECTS["battery_box"]
    dr.rectangle([bbx0, bby0, bbx1, bby1], fill=(182, 190, 198, 255), outline=(85, 92, 100, 255), width=4)
    dr.rectangle([bbx0 + 18, bby0 + 22, bbx1 - 18, bby0 + 52], fill=(224, 228, 232, 255))
    dr.text((bbx0 + 42, bby0 + 25), "12V", fill=(195, 28, 32, 255), font=_load_font(22))

    # RECT_WRECK (512, 800, 768, 1024) charred dark steel & ash
    wrx0, wry0, wrx1, wry1 = vs.RECT_WRECK
    dr.rectangle([wrx0, wry0, wrx1, wry1], fill=(44, 42, 46, 255))
    for _ in range(180):
        px = int(rng.integers(wrx0 + 4, wrx1 - 4))
        py = int(rng.integers(wry0 + 4, wry1 - 4))
        sh = int(rng.integers(25, 72))
        dr.ellipse([px - 5, py - 3, px + 5, py + 3], fill=(sh, sh - 2, sh + 2, 255))

    # RECT_EMBER (710, 808, 1004, 1004) -> bright xenon headlight + amber marker + red tail glow!
    ex0, ey0, ex1, ey1 = vs.RECT_EMBER
    dr.rectangle([ex0, ey0, ex1, ey1], fill=(255, 228, 145, 255))
    dg.rectangle([ex0, ey0, ex1, ey1], fill=(255, 205, 95, 255))
    ecx, ecy = (ex0 + ex1) // 2, (ey0 + ey1) // 2
    dr.ellipse([ecx - 80, ecy - 80, ecx + 80, ecy + 80], fill=(255, 250, 220, 255))
    dg.ellipse([ecx - 80, ecy - 80, ecx + 80, ecy + 80], fill=(255, 245, 190, 255))

    # Slight smoothing on painted sheetmetal regions? Crisp lines look sharper in Quake!
    # Build CHARRED BURN textures (`veh_tuktuk_burn.png` + `veh_tuktuk_burn_glow.png`)
    arr = np.array(tex, dtype=np.float32)
    burn_arr = arr.copy()
    # Darken & desaturate everything heavily into soot + scorched blue
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    burn_arr[:, :, 0] = lum * 0.22 + arr[:, :, 0] * 0.12
    burn_arr[:, :, 1] = lum * 0.19 + arr[:, :, 1] * 0.10
    burn_arr[:, :, 2] = lum * 0.18 + arr[:, :, 2] * 0.10
    burn_arr = np.clip(burn_arr, 0, 255).astype(np.uint8)
    burn = Image.fromarray(burn_arr, "RGBA")
    burn_glow = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dbg = ImageDraw.Draw(burn_glow)
    dbn = ImageDraw.Draw(burn)
    # Blistering orange-red molten embers on burn atlas
    for _ in range(95):
        px = int(rng.integers(24, W - 24))
        py = int(rng.integers(24, H - 24))
        rad = int(rng.integers(6, 26))
        dbn.ellipse([px - rad, py - rad // 2, px + rad, py + rad // 2], fill=(255, 110, 22, 255))
        dbg.ellipse([px - rad, py - rad // 2, px + rad, py + rad // 2], fill=(255, 90, 12, 255))
    # Bright glowing RECT_EMBER on burn too
    dbg.rectangle([ex0, ey0, ex1, ey1], fill=(255, 125, 20, 255))
    burn_glow = burn_glow.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Calibrate intact diffuse & glow to match HDR-toned vehicles (sedan/gtcar max ~155)
    t_arr = np.array(tex, dtype=np.float32)
    t_arr[..., :3] = np.clip(np.round(t_arr[..., :3] * 0.58), 0, 255)
    tex = Image.fromarray(t_arr.astype(np.uint8), "RGBA")
    g_arr = np.array(glow, dtype=np.float32)
    g_arr[..., :3] = np.clip(np.round(g_arr[..., :3] * 0.50), 0, 255)
    glow = Image.fromarray(g_arr.astype(np.uint8), "RGBA")

    return tex, glow, burn, burn_glow


# ---------------------------------------------------------------------------
# Intact Animations (Idle 24f + Flinch 6f + Fire 6f = 36f) & Wild 3-Wheel Explosion (40f)
# ---------------------------------------------------------------------------
def compute_tuktuk_pose(veh_data: dict, u: float, mode: str = "idle") -> dict:
    parts = veh_data["parts"]
    pose = {}
    for nm, p in parts.items():
        if nm in ("wreck_chassis", "blast_flash") or nm.startswith("shrap_"):
            pose[nm] = (np.array(p["origin"], dtype=np.float64), np.array([0.0, 0.0, 0.0, 1.0]), np.array([1.0, 1.0, 1.0]))
        else:
            pose[nm] = (np.array(p["origin"], dtype=np.float64), np.array([0.0, 0.0, 0.0, 1.0]), np.array([1.0, 1.0, 1.0]))

    if mode == "idle":
        # Buzzy high-RPM 2-stroke putt-putt vibration!
        s1 = math.sin(2.0 * math.pi * u)
        s2 = math.sin(4.0 * math.pi * u)
        pitch = 0.0055 * s1 + 0.002 * s2
        roll = 0.004 * math.cos(4.0 * math.pi * u)
        heave = 0.35 * s2
        qb = q_mul(q_from_axis_angle((0, 1, 0), pitch), q_from_axis_angle((1, 0, 0), roll))
        for nm in ("chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r"):
            op = np.array(parts[nm]["origin"], dtype=np.float64)
            rot_op = q_to_mat3(qb) @ op
            pose[nm] = (rot_op + np.array([0.0, 0.0, heave]), qb, np.array([1.0, 1.0, 1.0]))
        op_dv = np.array(parts["detail_vib"]["origin"], dtype=np.float64)
        qv = q_mul(qb, q_from_axis_angle((1, 0, 0), 0.024 * math.sin(6.0 * math.pi * u)))
        pose["detail_vib"] = (q_to_mat3(qb) @ op_dv + np.array([0.0, 0.0, heave + 0.45 * s2]), qv, np.array([1.0, 1.0, 1.0]))

    elif mode == "flinch":
        env = math.sin(math.pi * min(1.0, u))
        roll = 0.14 * env
        pitch = -0.07 * env
        qb = q_mul(q_from_axis_angle((1, 0, 0), roll), q_from_axis_angle((0, 1, 0), pitch))
        for nm in ("chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"):
            op = np.array(parts[nm]["origin"], dtype=np.float64)
            pose[nm] = (q_to_mat3(qb) @ op + np.array([0.0, 0.0, 2.2 * env]), qb, np.array([1.0, 1.0, 1.0]))

    elif mode == "fire":
        # Rapid desperate shuddering + rattling canopy & hood before detonation!
        s1 = math.sin(2.0 * math.pi * u)
        s3 = math.sin(6.0 * math.pi * u)
        qb = q_mul(q_from_axis_angle((1, 0, 0), 0.05 * s1), q_from_axis_angle((0, 1, 0), 0.04 * s3))
        for nm in ("chassis", "bumper_f", "bumper_r", "detail_vib"):
            op = np.array(parts[nm]["origin"], dtype=np.float64)
            pose[nm] = (q_to_mat3(qb) @ op + np.array([0.0, 0.0, 0.8 * s3]), qb, np.array([1.0, 1.0, 1.0]))
        # Canopy rattles wildly on poles!
        ex_op = np.array(parts["extra_part"]["origin"], dtype=np.float64)
        qe = q_mul(qb, q_from_axis_angle((1, 0.3, 0), 0.08 * s3))
        pose["extra_part"] = (q_to_mat3(qb) @ ex_op + np.array([0.0, 0.0, 1.4 * abs(s1)]), qe, np.array([1.0, 1.0, 1.0]))
        # Hood / windshield pops slightly
        h_op = np.array(parts["hood"]["origin"], dtype=np.float64)
        qh = q_mul(qb, q_from_axis_angle((0, 1, 0), -0.10 * (0.5 + 0.5 * s1)))
        pose["hood"] = (q_to_mat3(qb) @ h_op + np.array([0.0, 0.0, 0.9 * abs(s3)]), qh, np.array([1.0, 1.0, 1.0]))
        for dnm, dsgn in (("door_l", 1.0), ("door_r", -1.0)):
            d_op = np.array(parts[dnm]["origin"], dtype=np.float64)
            qd = q_mul(qb, q_from_axis_angle((0, 0, 1), dsgn * 0.06 * s1))
            pose[dnm] = (q_to_mat3(qb) @ d_op, qd, np.array([1.0, 1.0, 1.0]))

    pose["blast_flash"] = (np.array([0.0, 0.0, 32.0]), np.array([0.0, 0.0, 0.0, 1.0]), np.array([0.0001, 0.0001, 0.0001]))
    pose["wreck_chassis"] = (np.array(parts["wreck_chassis"]["origin"], dtype=np.float64), np.array([0.0, 0.0, 0.0, 1.0]), np.array([0.0001, 0.0001, 0.0001]))
    for k in range(10):
        snm = f"shrap_{k}"
        pose[snm] = (np.array(parts[snm]["origin"], dtype=np.float64), np.array([0.0, 0.0, 0.0, 1.0]), np.array([0.0001, 0.0001, 0.0001]))
    return pose


def simulate_tuktuk_explosion(veh_data: dict) -> dict:
    """960 Hz 40-frame wild airborne-flip explosion tailored for the 3-wheeled Tuk-Tuk!"""
    fps = 12
    n_frames = 40
    substeps = 80
    dt_frame = 1.0 / fps
    dt = dt_frame / substeps
    g_acc = np.array([0.0, 0.0, -800.0], dtype=np.float64)
    parts = veh_data["parts"]
    all_names = list(parts.keys()) + ["blast_flash"]

    tracks = {
        nm: {
            "pos": np.zeros((n_frames, 3), dtype=np.float32),
            "rot": np.zeros((n_frames, 4), dtype=np.float32),
            "scl": np.ones((n_frames, 3), dtype=np.float32),
        }
        for nm in all_names
    }

    boom_frame = 2
    sec_boom_frame = 7

    # Frames 0..1: violent pre-blast swell
    for fi in range(boom_frame):
        p = compute_tuktuk_pose(veh_data, (fi * 0.45) % 1.0, mode="flinch" if fi == 0 else "fire")
        for nm, (pos, rot, scl) in p.items():
            tracks[nm]["pos"][fi] = pos
            tracks[nm]["rot"][fi] = rot
            tracks[nm]["scl"][fi] = scl

    # Active flying rigid bodies (Tuk-Tuk leaps sky-high & barrel-rolls!)
    rb_cfgs = {
        "wreck_chassis": {"vel": [95.0, -28.0, 540.0], "omega": [12.5, 9.2, 5.4],  "e": 0.56, "mu": 0.62, "ld": 0.06, "ad": 0.10},
        "extra_part":    {"vel": [-25.0, 22.0, 460.0], "omega": [7.5, -10.5, 6.2],"e": 0.42, "mu": 0.48, "ld": 0.14, "ad": 0.12},
        "hood":          {"vel": [145.0, -32.0, 375.0],"omega": [5.5, -13.0, 4.8],"e": 0.50, "mu": 0.52, "ld": 0.10, "ad": 0.15},
        "door_l":        {"vel": [40.0, 240.0, 285.0], "omega": [12.0, 4.5, 9.0], "e": 0.46, "mu": 0.50, "ld": 0.12, "ad": 0.14},
        "door_r":        {"vel": [35.0, -245.0, 275.0],"omega": [-12.0, 4.0, -9.5],"e": 0.46, "mu": 0.50, "ld": 0.12, "ad": 0.14},
        "bumper_f":      {"vel": [265.0, 28.0, 220.0], "omega": [6.0, 14.0, 7.5], "e": 0.52, "mu": 0.55, "ld": 0.11, "ad": 0.16},
        "bumper_r":      {"vel": [-240.0, -24.0, 210.0],"omega": [-6.0, -12.0, 5.0],"e": 0.50, "mu": 0.55, "ld": 0.11, "ad": 0.16},
        "detail_vib":    {"vel": [-15.0, 65.0, 320.0], "omega": [14.0, 9.0, 11.0],"e": 0.48, "mu": 0.52, "ld": 0.10, "ad": 0.15},
    }
    rng = random.Random(909)
    for si in range(10):
        th = 2.0 * math.pi * si / 10.0 + 0.31
        spd = rng.uniform(210.0, 355.0)
        rb_cfgs[f"shrap_{si}"] = {
            "vel": [math.cos(th) * spd, math.sin(th) * spd, rng.uniform(250.0, 440.0)],
            "omega": [rng.uniform(-16, 16), rng.uniform(-16, 16), rng.uniform(-16, 16)],
            "e": 0.46, "mu": 0.50, "ld": 0.12, "ad": 0.12,
        }

    # Build convex/extremal vertex hulls for ground contact manifolds
    rb_states = {}
    for nm, cfg in rb_cfgs.items():
        v = np.array(parts[nm]["verts"], dtype=np.float64)
        if len(v) > 48:
            # Sample boundary extremal points so physics stays fast & exact
            idx = np.linspace(0, len(v) - 1, 48, dtype=int)
            v = v[idx]
        p0 = np.array(parts[nm]["origin"], dtype=np.float64)
        rb_states[nm] = {
            "pos": p0.copy(),
            "q": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64),
            "vel": np.array(cfg["vel"], dtype=np.float64),
            "omega": np.array(cfg["omega"], dtype=np.float64),
            "hull": v,
            "inv_I": np.diag([1.0 / 320.0, 1.0 / 480.0, 1.0 / 520.0]),
            "e": cfg["e"],
            "mu": cfg["mu"],
            "ld": cfg["ld"],
            "ad": cfg["ad"],
            "max_z": float(p0[2]),
            "cum_rot": 0.0,
        }

    # 3 Flying & Rolling Wheels! (wheel_f, wheel_rl, wheel_rr)
    wheel_states = {}
    w_cfgs = {
        "wheel_f":  {"vel": [210.0, 95.0, 185.0],   "side":  1.0, "r": 11.5, "hw": 2.5},
        "wheel_rl": {"vel": [-65.0, 235.0, 165.0],  "side":  1.0, "r": 11.8, "hw": 2.9},
        "wheel_rr": {"vel": [-55.0, -240.0, 160.0], "side": -1.0, "r": 11.8, "hw": 2.9},
    }
    for wn, wc in w_cfgs.items():
        p0 = np.array(parts[wn]["origin"], dtype=np.float64)
        hv = wc["vel"]
        yaw0 = math.atan2(hv[1], hv[0])
        wheel_states[wn] = {
            "pos": p0.copy(),
            "vel": np.array(hv, dtype=np.float64),
            "r": wc["r"],
            "hw": wc["hw"],
            "side": wc["side"],
            "yaw": yaw0,
            "lean": wc["side"] * 0.14,
            "spin": 0.0,
            "roll_spd": float(math.hypot(hv[0], hv[1])),
            "precess": 0.0,
            "on_ground": False,
        }

    for fi in range(boom_frame, n_frames):
        age = (fi - boom_frame) * dt_frame
        sec_age = (fi - sec_boom_frame) * dt_frame

        if fi == sec_boom_frame:
            wst = rb_states["wreck_chassis"]
            wst["vel"] += np.array([85.0, 45.0, 310.0], dtype=np.float64)
            wst["omega"] += np.array([10.0, -12.5, 6.5], dtype=np.float64)

        tracks["chassis"]["pos"][fi] = tracks["chassis"]["pos"][boom_frame - 1]
        tracks["chassis"]["rot"][fi] = tracks["chassis"]["rot"][boom_frame - 1]
        tracks["chassis"]["scl"][fi] = [0.0001, 0.0001, 0.0001]

        if age < 0.45:
            fl_s = (0.55 + 3.2 * math.sin(math.pi * min(1.0, age / 0.14))) * max(0.001, 1.0 - age / 0.45)
            tracks["blast_flash"]["pos"][fi] = [0.0, 0.0, 30.0 + age * 60.0]
            tracks["blast_flash"]["rot"][fi] = q_from_axis_angle((0, 0, 1), age * 9.5)
            tracks["blast_flash"]["scl"][fi] = [fl_s, fl_s, fl_s]
        elif 0.0 <= sec_age < 0.34:
            fl_s = (0.45 + 2.2 * math.sin(math.pi * min(1.0, sec_age / 0.11))) * max(0.001, 1.0 - sec_age / 0.34)
            tracks["blast_flash"]["pos"][fi] = rb_states["wreck_chassis"]["pos"]
            tracks["blast_flash"]["rot"][fi] = q_from_axis_angle((1, 0.5, 0.3), sec_age * 11.0)
            tracks["blast_flash"]["scl"][fi] = [fl_s, fl_s, fl_s]
        else:
            tracks["blast_flash"]["pos"][fi] = [0.0, 0.0, 30.0]
            tracks["blast_flash"]["rot"][fi] = [0.0, 0.0, 0.0, 1.0]
            tracks["blast_flash"]["scl"][fi] = [0.0001, 0.0001, 0.0001]

        for nm, st in rb_states.items():
            tracks[nm]["pos"][fi] = st["pos"]
            tracks[nm]["rot"][fi] = st["q"]
            tracks[nm]["scl"][fi] = [1.0, 1.0, 1.0]

        for wn, ws in wheel_states.items():
            cy, sy = math.cos(ws["yaw"]), math.sin(ws["yaw"])
            cl, sl = math.cos(ws["lean"]), math.sin(ws["lean"])
            cs, ss = math.cos(ws["spin"]), math.sin(ws["spin"])
            Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
            Rx = np.array([[1.0, 0.0, 0.0], [0.0, cl, -sl], [0.0, sl, cl]])
            Ry = np.array([[cs, 0.0, ss], [0.0, 1.0, 0.0], [-ss, 0.0, cs]])
            tracks[wn]["pos"][fi] = ws["pos"]
            tracks[wn]["rot"][fi] = mat3_to_q(Rz @ Rx @ Ry)
            tracks[wn]["scl"][fi] = [1.0, 1.0, 1.0]

        if fi == n_frames - 1:
            break

        for _ in range(substeps):
            for nm, st in rb_states.items():
                st["vel"] += g_acc * dt
                st["vel"] *= max(0.0, 1.0 - st["ld"] * dt)
                st["omega"] *= max(0.0, 1.0 - st["ad"] * dt)
                st["pos"] += st["vel"] * dt
                w_mag = float(np.linalg.norm(st["omega"]))
                st["cum_rot"] += w_mag * dt
                st["q"] = integrate_q(st["q"], st["omega"], dt)
                if st["pos"][2] > st["max_z"]:
                    st["max_z"] = float(st["pos"][2])

                Rm = q_to_mat3(st["q"])
                pts_w = st["hull"] @ Rm.T + st["pos"]
                pen_mask = pts_w[:, 2] < 0.0
                if np.any(pen_mask):
                    pens = -pts_w[pen_mask, 2]
                    st["pos"][2] += float(np.max(pens))
                    w_c = pens / max(1e-9, float(np.sum(pens)))
                    pt_c = np.sum(pts_w[pen_mask] * w_c[:, None], axis=0)
                    pt_c[2] = 0.0
                    r_vec = pt_c - st["pos"]
                    v_pt = st["vel"] + np.cross(st["omega"], r_vec)
                    vn = float(v_pt[2])
                    if vn < 0.0:
                        rxn = np.cross(r_vec, np.array([0.0, 0.0, 1.0]))
                        jn = (-(1.0 + st["e"]) * vn) / (1.0 + float(rxn @ st["inv_I"] @ rxn))
                        J = np.array([0.0, 0.0, jn])
                        v_tan = np.array([v_pt[0], v_pt[1], 0.0])
                        vt = float(np.linalg.norm(v_tan))
                        if vt > 1.0:
                            jt = -min(st["mu"] * jn, vt * 0.45)
                            J += (v_tan / vt) * jt
                        st["vel"] += J
                        st["omega"] += st["inv_I"] @ np.cross(r_vec, J)
                        if abs(vn) < 28.0:
                            st["vel"][2] = max(0.0, st["vel"][2])
                            st["vel"][0] *= max(0.0, 1.0 - 4.2 * dt)
                            st["vel"][1] *= max(0.0, 1.0 - 4.2 * dt)
                            st["omega"] *= max(0.0, 1.0 - 5.0 * dt)

            for wn, ws in wheel_states.items():
                if not ws["on_ground"]:
                    ws["vel"] += g_acc * dt
                    ws["pos"] += ws["vel"] * dt
                    ws["spin"] -= 18.0 * dt
                    ws["lean"] += ws["side"] * 0.55 * dt
                    al = abs(ws["lean"])
                    h_bot = ws["r"] * abs(math.cos(al)) + ws["hw"] * abs(math.sin(al))
                    if ws["pos"][2] <= h_bot:
                        ws["pos"][2] = h_bot
                        if ws["vel"][2] < -40.0:
                            ws["vel"][2] = -ws["vel"][2] * 0.62
                            ws["vel"][0] *= 0.90
                            ws["vel"][1] *= 0.90
                        else:
                            ws["vel"][2] = 0.0
                            ws["on_ground"] = True
                            ws["roll_spd"] = float(math.hypot(ws["vel"][0], ws["vel"][1]))
                            if ws["roll_spd"] > 5.0:
                                ws["yaw"] = math.atan2(ws["vel"][1], ws["vel"][0])
                else:
                    spd = ws["roll_spd"]
                    if spd > 10.0:
                        step = spd * dt
                        ws["pos"][0] += math.cos(ws["yaw"]) * step
                        ws["pos"][1] += math.sin(ws["yaw"]) * step
                        ws["spin"] -= step / max(4.0, ws["r"])
                        ws["yaw"] -= math.sin(ws["lean"]) * (1.8 / max(18.0, spd * 0.13)) * step
                        ws["roll_spd"] = max(0.0, spd * (1.0 - 0.42 * dt) - 10.0 * dt)
                        sf = min(1.0, ws["roll_spd"] / 230.0)
                        target_lean = math.radians(18.0 + ((1.0 - sf) ** 1.8) * 69.5)
                        ws["precess"] += (12.0 + (1.0 - sf) * 16.0) * dt
                        ws["lean"] = ws["side"] * target_lean + math.sin(ws["precess"]) * math.radians(8.5) * sf
                    else:
                        ws["lean"] = ws["side"] * math.radians(87.5)
                    al2 = abs(ws["lean"])
                    ws["pos"][2] = ws["r"] * math.cos(al2) + ws["hw"] * math.sin(al2)

    wst = rb_states["wreck_chassis"]
    print(f"  [sim tuktuk] max_z={wst['max_z']:.1f}u ({wst['max_z']/39.37:.1f}m) | spin={math.degrees(wst['cum_rot']):.0f} deg")
    return {"fps": fps, "n_frames": n_frames, "tracks": tracks}


# ---------------------------------------------------------------------------
# MD3 Surface Assembly (Respects MD3 [-505, +505] Coord Bounds & <4096 Verts/Surface)
# ---------------------------------------------------------------------------
def _slice_part(part: dict, max_tris: int = 900) -> list[tuple[str, dict]]:
    """Splits a large part into chunks so each MD3 surface stays well under 4096 vertices."""
    tris = part["tris"]
    if len(part["verts"]) <= 2400:
        return [(part["name"], part)]
    chunks = []
    for ci, start in enumerate(range(0, len(tris), max_tris)):
        sub_tris = tris[start:start + max_tris]
        v_map = {}
        nv, nn, nuv, ntr = [], [], [], []
        for t in sub_tris:
            tri_new = []
            for vi in t:
                if vi not in v_map:
                    v_map[vi] = len(nv)
                    nv.append(part["verts"][vi])
                    nn.append(part["norms"][vi])
                    nuv.append(part["uvs"][vi])
                tri_new.append(v_map[vi])
            ntr.append(tri_new)
        chunks.append((f"{part['name']}_{ci}", {
            "name": f"{part['name']}_{ci}",
            "origin": part["origin"],
            "verts": nv,
            "norms": nn,
            "uvs": nuv,
            "tris": ntr,
        }))
    return chunks


def _bake_surfaces(part_list: list[tuple[str, dict, str]], frame_poses: list[dict], scale_xyz: float = 1.0) -> list[dict]:
    """Combines/splits parts into MD3 surfaces, keeping each surface <= 2400 vertices."""
    expanded: list[tuple[str, dict, dict, str]] = []
    for orig_nm, p, sh in part_list:
        for sub_nm, sub_p in _slice_part(p):
            expanded.append((orig_nm, sub_nm, sub_p, sh))

    buckets: list[tuple[str, list[tuple[str, dict]], str]] = []
    cur_sh = None
    cur_items = []
    cur_v = 0
    for orig_nm, sub_nm, sub_p, sh in expanded:
        nv = len(sub_p["verts"])
        if cur_sh != sh or (cur_v + nv > 2400 and cur_items):
            if cur_items:
                buckets.append((f"s_{len(buckets)}", cur_items, cur_sh))
            cur_sh = sh
            cur_items = [(orig_nm, sub_p)]
            cur_v = nv
        else:
            cur_items.append((orig_nm, sub_p))
            cur_v += nv
    if cur_items:
        buckets.append((f"s_{len(buckets)}", cur_items, cur_sh))

    surfaces = []
    for sname, items, shader in buckets:
        st_all = []
        tris_all = []
        v_off = 0
        for orig_nm, p in items:
            st_all.extend([(float(u), float(v)) for (u, v) in p["uvs"]])
            tris_all.extend([[t[0] + v_off, t[1] + v_off, t[2] + v_off] for t in p["tris"]])
            v_off += len(p["verts"])

        frames = []
        for pose in frame_poses:
            vv_all, nn_all = [], []
            for orig_nm, p in items:
                pos, quat, scl = pose[orig_nm]
                R = q_to_mat3(quat)
                v = np.array(p["verts"], dtype=np.float64) * scl[None, :]
                n = np.array(p["norms"], dtype=np.float64)
                vw = (v @ R.T + pos[None, :]) * scale_xyz
                nw = n @ R.T
                nmags = np.maximum(1e-8, np.linalg.norm(nw, axis=1, keepdims=True))
                nw /= nmags
                vw = np.clip(vw, -504.0, 504.0)
                vv_all.extend(vw.tolist())
                nn_all.extend(nw.tolist())
            frames.append((vv_all, nn_all))
        surfaces.append({"name": sname, "shader": shader, "tris": tris_all, "st": st_all, "frames": frames})
    return surfaces


def update_tuktuk_shader():
    with open(SHADER_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    block = """
progs/veh_tuktuk_tex
{
    cull none
    {
        map progs/veh_tuktuk_tex.png
        rgbGen lightingDiffuse
    }
    {
        map progs/veh_tuktuk_tex_glow.png
        blendfunc add
        rgbGen identity
    }
}

progs/veh_tuktuk_burn
{
    cull none
    {
        map progs/veh_tuktuk_burn.png
        rgbGen lightingDiffuse
    }
    {
        map progs/veh_tuktuk_burn_glow.png
        blendfunc add
        rgbGen identity
    }
}
"""
    if "progs/veh_tuktuk_tex" not in text:
        text = text.rstrip() + "\n" + block
        with open(SHADER_PATH, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Added progs/veh_tuktuk_tex & veh_tuktuk_burn to {SHADER_PATH}")
    else:
        print(f"{SHADER_PATH} already contains progs/veh_tuktuk_tex")


def main():
    if "--blender" in sys.argv or not os.path.exists(GEOM_JSON):
        print("Running Blender 5.2 geometry builder...")
        subprocess.run([BLENDER_EXE, "--background", "--python", BLENDER_SCRIPT], check=True)

    with open(GEOM_JSON, "r", encoding="utf-8") as f:
        veh_data = json.load(f)

    parts = dict(veh_data["parts"])
    parts["blast_flash"] = build_blast_starburst_mesh()
    veh_data["parts"] = parts

    os.makedirs(OUT_PROGS, exist_ok=True)

    # 1. Generate 4 PNG textures
    tex, glow, burn, burn_glow = generate_tuktuk_textures()
    tex.save(os.path.join(OUT_PROGS, "veh_tuktuk_tex.png"))
    glow.save(os.path.join(OUT_PROGS, "veh_tuktuk_tex_glow.png"))
    burn.save(os.path.join(OUT_PROGS, "veh_tuktuk_burn.png"))
    burn_glow.save(os.path.join(OUT_PROGS, "veh_tuktuk_burn_glow.png"))
    print(f"Wrote 4 PNG textures in {OUT_PROGS}")

    # 2. Intact MD3 (36 frames: 0..23 idle, 24..29 flinch, 30..35 fire)
    intact_keys = ["chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib", "wheel_f", "wheel_rl", "wheel_rr"]
    intact_poses = []
    fnames_intact = []
    for i in range(24):
        intact_poses.append(compute_tuktuk_pose(veh_data, i / 24.0, "idle"))
        fnames_intact.append(f"idle{i}")
    for i in range(6):
        intact_poses.append(compute_tuktuk_pose(veh_data, i / 5.0, "flinch"))
        fnames_intact.append(f"flinch{i}")
    for i in range(6):
        intact_poses.append(compute_tuktuk_pose(veh_data, i / 6.0, "fire"))
        fnames_intact.append(f"fire{i}")

    intact_list = [(k, parts[k], "progs/veh_tuktuk_tex") for k in intact_keys]
    intact_surfaces = _bake_surfaces(intact_list, intact_poses)
    md3lib.write(os.path.join(OUT_PROGS, "veh_tuktuk.md3"), {"name": "veh_tuktuk", "surfaces": intact_surfaces, "frame_names": fnames_intact})
    print(f"Wrote veh_tuktuk.md3 ({len(intact_surfaces)} surfaces, 36 frames)")

    # 3. Skins (.skin files map all surface names -> intact or burn shader)
    for skin_idx, sh_name in ((0, "progs/veh_tuktuk_tex"), (1, "progs/veh_tuktuk_burn")):
        lines = [f"{s['name']},{sh_name}\n" for s in intact_surfaces]
        with open(os.path.join(OUT_PROGS, f"veh_tuktuk.md3_{skin_idx}.skin"), "w", encoding="ascii") as f:
            f.writelines(lines)

    # 4. Wild Explosion Wreck MD3 (40 frames of barrel-rolling charred wreck chassis!)
    sim = simulate_tuktuk_explosion(veh_data)
    tr = sim["tracks"]
    wreck_poses = []
    for fi in range(sim["n_frames"]):
        wreck_poses.append({
            "wreck_chassis": (tr["wreck_chassis"]["pos"][fi], tr["wreck_chassis"]["rot"][fi], np.ones(3)),
        })

    wreck_surfaces = _bake_surfaces([("wreck_chassis", parts["wreck_chassis"], "progs/veh_tuktuk_burn")], wreck_poses)
    md3lib.write(
        os.path.join(OUT_PROGS, "veh_tuktuk_wreck.md3"),
        {"name": "veh_tuktuk_wreck", "surfaces": wreck_surfaces, "frame_names": [f"ex{i}" for i in range(40)]},
    )
    print(f"Wrote veh_tuktuk_wreck.md3 ({len(wreck_surfaces)} surfaces, 40 frames)")

    # 5. Standalone 16-frame spinning wheel & flying debris sub-models
    wh_poses = []
    for i in range(16):
        ang = 2.0 * math.pi * i / 16.0
        wh_poses.append({"wheel": (np.zeros(3), q_from_axis_angle((0, 1, 0), ang), np.ones(3))})
    wh_surf = _bake_surfaces([("wheel", parts["wheel_rl"], "progs/veh_tuktuk_tex")], wh_poses)
    md3lib.write(os.path.join(OUT_PROGS, "veh_tuktuk_wheel.md3"), {"name": "veh_tuktuk_wheel", "surfaces": wh_surf, "frame_names": [f"w{i}" for i in range(16)]})

    zero_pose = lambda k: [{k: (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0]), np.ones(3))}]
    for sub_nm, p_key in (("hood", "hood"), ("door", "door_l"), ("extra", "extra_part"), ("bumper", "bumper_f")):
        s_surf = _bake_surfaces([(p_key, parts[p_key], "progs/veh_tuktuk_burn")], zero_pose(p_key))
        md3lib.write(os.path.join(OUT_PROGS, f"veh_tuktuk_{sub_nm}.md3"), {"name": f"veh_tuktuk_{sub_nm}", "surfaces": s_surf, "frame_names": ["f0"]})

    # 6. Shader update
    update_tuktuk_shader()


if __name__ == "__main__":
    main()
