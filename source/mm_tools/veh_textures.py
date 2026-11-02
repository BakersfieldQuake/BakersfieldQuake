"""High-detail 1024x1024 Automotive UV Texture, Burn Variant & Glow Map Generator
for BakersfieldQuake's 4 Unique 3D Vehicles.

Uses exact world-to-pixel coordinate projection from veh_specs.py so every door shutline,
handle, window pillar, wheel arch, grille, headlight, taillight, bumper, license plate,
and rim lip lands on the exact corresponding 3D geometry on all 4 vehicles.
"""
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs

W = vs.W_ATLAS
H = vs.H_ATLAS

PALETTES = {
    "truck": {
        "sky":   (92, 148, 232),
        "hi":    (56, 108, 198),
        "mid":   (30, 68, 142),
        "lo":    (16, 38, 86),
        "two_tone": (190, 198, 208),
        "plate": "4TRK901",
    },
    "sedan": {
        "sky":   (94, 184, 144),
        "hi":    (52, 142, 104),
        "mid":   (26, 96, 68),
        "lo":    (14, 54, 38),
        "two_tone": None,
        "plate": "4LAN299",
    },
    "van": {
        "sky":   (252, 253, 255),
        "hi":    (240, 243, 248),
        "mid":   (216, 221, 228),
        "lo":    (176, 182, 190),
        "two_tone": None,
        "plate": "6WHT418",
    },
    "coupe": {
        "sky":   (255, 96, 88),
        "hi":    (234, 42, 42),
        "mid":   (186, 18, 24),
        "lo":    (112, 10, 14),
        "two_tone": None,
        "plate": "4SPD882",
    },
}


def _add_flake(arr_patch, rng, amp=3.5):
    h, w, _ = arr_patch.shape
    n = rng.normal(0.0, amp, (h, w, 1)).astype(np.float32)
    return np.clip(arr_patch.astype(np.float32) + n, 0, 255).astype(np.uint8)


_GLYPHS = {
    "0": [(0,0,1,0),(1,0,1,1),(1,1,0,1),(0,1,0,0)],
    "1": [(0.5,0,0.5,1),(0.2,0.2,0.5,0),(0.2,1,0.8,1)],
    "2": [(0,0,1,0),(1,0,1,0.5),(1,0.5,0,0.5),(0,0.5,0,1),(0,1,1,1)],
    "3": [(0,0,1,0),(1,0,1,1),(0,1,1,1),(0.1,0.5,1,0.5)],
    "4": [(0,0,0,0.55),(0,0.55,1,0.55),(0.8,0,0.8,1)],
    "6": [(1,0,0,0),(0,0,0,1),(0,1,1,1),(1,1,1,0.5),(1,0.5,0,0.5)],
    "8": [(0,0,1,0),(1,0,1,1),(1,1,0,1),(0,1,0,0),(0,0.5,1,0.5)],
    "9": [(0,0.5,1,0.5),(1,0,0,0),(0,0,0,0.5),(1,0,1,1),(0,1,1,1)],
    "A": [(0,1,0,0.2),(0,0.2,0.5,0),(0.5,0,1,0.2),(1,0.2,1,1),(0,0.55,1,0.55)],
    "D": [(0,0,0,1),(0,0,0.7,0),(0.7,0,1,0.25),(1,0.25,1,0.75),(1,0.75,0.7,1),(0.7,1,0,1)],
    "H": [(0,0,0,1),(1,0,1,1),(0,0.5,1,0.5)],
    "K": [(0,0,0,1),(1,0,0,0.5),(0,0.5,1,1)],
    "L": [(0,0,0,1),(0,1,1,1)],
    "N": [(0,1,0,0),(0,0,1,1),(1,1,1,0)],
    "P": [(0,1,0,0),(0,0,1,0),(1,0,1,0.5),(1,0.5,0,0.5)],
    "R": [(0,1,0,0),(0,0,1,0),(1,0,1,0.5),(1,0.5,0,0.5),(0.4,0.5,1,1)],
    "S": [(1,0,0,0),(0,0,0,0.5),(0,0.5,1,0.5),(1,0.5,1,1),(1,1,0,1)],
    "T": [(0,0,1,0),(0.5,0,0.5,1)],
    "W": [(0,0,0.2,1),(0.2,1,0.5,0.45),(0.5,0.45,0.8,1),(0.8,1,1,0)],
}


def _draw_plate(draw, cx, cy, pw, ph, text):
    x0, y0 = int(cx - pw * 0.5), int(cy - ph * 0.5)
    x1, y1 = int(cx + pw * 0.5), int(cy + ph * 0.5)
    draw.rounded_rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], radius=4, fill=(22, 24, 28), outline=(58, 62, 70), width=1)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=3, fill=(238, 241, 246))
    # California red script bar at top + registration tab
    draw.line([(x0 + 10, y0 + 5), (x1 - 16, y0 + 5)], fill=(198, 32, 36), width=3)
    draw.rectangle([x1 - 12, y0 + 3, x1 - 5, y0 + 7], fill=(232, 168, 24))
    step = (pw - 12) / max(1, len(text))
    for i, ch in enumerate(text):
        bx = x0 + 6 + i * step
        by = y0 + 10
        cw = max(4.0, step * 0.62)
        ch_h = max(8.0, ph - 14.0)
        for ax, ay, ex, ey in _GLYPHS.get(ch, _GLYPHS["0"]):
            draw.line([(bx + ax * cw, by + ay * ch_h), (bx + ex * cw, by + ey * ch_h)], fill=(24, 52, 126), width=2)


def _draw_headlight_unit(draw, glow_draw, x0, y0, x1, y1, projector=False):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x1 <= x0 + 6 or y1 <= y0 + 6:
        return
    draw.rounded_rectangle([x0, y0, x1, y1], radius=5, fill=(26, 30, 36), outline=(14, 16, 20), width=3)
    if projector:
        # Smoked JDM twin-projector housing
        w = x1 - x0
        ym = (y0 + y1) // 2
        r1 = max(6, int(min(w * 0.21, (y1 - y0) * 0.38)))
        for cx in (int(x0 + w * 0.30), int(x0 + w * 0.70)):
            draw.ellipse([cx - r1 - 2, ym - r1 - 2, cx + r1 + 2, ym + r1 + 2], fill=(148, 162, 182))
            draw.ellipse([cx - r1, ym - r1, cx + r1, ym + r1], fill=(224, 238, 255), outline=(92, 112, 142), width=2)
            draw.ellipse([cx - r1 // 2, ym - r1 // 2, cx + r1 // 2, ym + r1 // 2], fill=(252, 254, 255))
            glow_draw.ellipse([cx - r1, ym - r1, cx + r1, ym + r1], fill=(175, 205, 245))
    else:
        # Multi-surface chrome reflector bowl + vertical fluted glass lens ribs
        draw.rounded_rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], radius=4, fill=(196, 208, 224), outline=(128, 138, 152), width=2)
        draw.rounded_rectangle([x0 + 7, y0 + 6, x1 - 7, y1 - 6], radius=4, fill=(238, 245, 255))
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        draw.ellipse([cx - 7, cy - 6, cx + 7, cy + 6], fill=(255, 252, 236), outline=(168, 180, 198), width=2)
        for fx in range(x0 + 8, x1 - 6, 6):
            draw.line([(fx, y0 + 5), (fx, y1 - 5)], fill=(182, 198, 218), width=1)
        # Top glass specular streak
        draw.line([(x0 + 6, y0 + 6), (x1 - 6, y0 + 6)], fill=(255, 255, 255), width=2)
        glow_draw.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=3, fill=(180, 192, 212))


def _paint_side_profile(im, draw, glow_draw, sp, pal, rng):
    """Paints RECT_SIDE using exact world (x, z) -> pixel coordinates."""
    kind = sp["kind"]
    rx0, ry0, rx1, ry1 = vs.RECT_SIDE
    # Fill generous bleed padding around RECT_SIDE (0..640, 0..288)
    bw, bh = 640, 288
    arr = np.array(im)

    sky = np.array(pal["sky"], dtype=np.float32)
    hi = np.array(pal["hi"], dtype=np.float32)
    mid = np.array(pal["mid"], dtype=np.float32)
    lo = np.array(pal["lo"], dtype=np.float32)

    _, py_belt = vs.side_world_to_px(sp, 0.0, sp["z_belt"])
    _, py_bot = vs.side_world_to_px(sp, 0.0, sp["z_bot"])

    ys = np.arange(bh, dtype=np.float32)[:, None]
    # Realistic automotive studio reflection profile across Z:
    # Above beltline (pillars/roof rail): bright sky reflection; just below beltline: crisp horizon highlight;
    # mid-door: rich body colour; lower door: darker ground reflection + rocker shadow!
    band = np.zeros((bh, bw, 3), dtype=np.float32)
    for y_i in range(bh):
        if y_i < py_belt:
            t = max(0.0, min(1.0, y_i / max(1.0, py_belt)))
            c = sky * (1.0 - t * 0.45) + hi * (t * 0.45)
        else:
            t = max(0.0, min(1.0, (y_i - py_belt) / max(1.0, py_bot - py_belt)))
            if t < 0.14:
                # Upper shoulder horizon highlight!
                u = t / 0.14
                c = hi * (1.0 - u) + sky * u
            elif t < 0.58:
                u = (t - 0.14) / 0.44
                c = sky * (1.0 - u) * 0.25 + hi * (1.0 - u) * 0.75 + mid * u
            else:
                u = (t - 0.58) / 0.42
                c = mid * (1.0 - u) + lo * u
            # Subtle ground horizon bounce line at t=0.62
            c += np.exp(-((t - 0.62) / 0.05) ** 2) * 24.0
        band[y_i, :, :] = np.clip(c, 0, 255)

    # Truck two-tone lower silver paint band (z <= z_bot + 10.5)
    if pal["two_tone"] is not None:
        _, py_tt = vs.side_world_to_px(sp, 0.0, sp["z_bot"] + 10.5)
        y_cut = int(round(py_tt))
        tt = np.array(pal["two_tone"], dtype=np.float32)
        for y_i in range(y_cut, bh):
            u = min(1.0, (y_i - y_cut) / max(1.0, py_bot - y_cut))
            band[y_i, :, :] = tt * (1.05 - 0.28 * u)

    arr[0:bh, 0:bw] = _add_flake(band, rng, amp=3.5 if kind != "van" else 2.0)
    im.paste(Image.fromarray(arr[0:bh, 0:bw]), (0, 0))
    draw = ImageDraw.Draw(im)

    def P(wx, wz):
        return vs.side_world_to_px(sp, wx, wz)

    zb = sp["z_belt"]
    zbot = sp["z_bot"]
    zroof = sp["z_roof"]

    # Dark lower rocker pinch-weld / side-skirt shadow strip along bottom (z_bot .. z_bot + 2.8)
    _, py_rk0 = P(0, zbot + 2.8)
    draw.rectangle([0, int(py_rk0), bw, bh], fill=(24, 26, 30))

    # Recessed door & panel shutlines (dark 2px seam + 1px specular highlight!)
    def shutline_v(wx, za, zb_top):
        x_p, ya_p = P(wx, za)
        _, yb_p = P(wx, zb_top)
        y_lo, y_hi = min(ya_p, yb_p), max(ya_p, yb_p)
        draw.line([(x_p, y_lo), (x_p, y_hi)], fill=(12, 16, 22), width=3)
        draw.line([(x_p + 2, y_lo), (x_p + 2, y_hi)], fill=pal["sky"], width=1)

    def draw_door_handle(wx_center, wz_center, chrome_bar=False):
        x0_p, y0_p = P(wx_center - 5.2, wz_center + 2.0)
        x1_p, y1_p = P(wx_center + 5.2, wz_center - 2.0)
        draw.rounded_rectangle([x0_p, y0_p, x1_p, y1_p], radius=4, fill=(16, 20, 26), outline=pal["lo"], width=2)
        bar_col = (212, 218, 228) if chrome_bar else pal["hi"]
        ym = 0.5 * (y0_p + y1_p)
        draw.rounded_rectangle([x0_p + 2, ym - 2.5, x1_p - 2, ym + 2.5], radius=2, fill=bar_col)
        # Silver keyhole cylinder behind handle
        kx, ky = P(wx_center - 7.2, wz_center)
        draw.ellipse([kx - 2.2, ky - 2.2, kx + 2.2, ky + 2.2], fill=(205, 212, 222), outline=(24, 28, 34))

    # Vehicle-specific authentic side trim, shutlines, handles & wheel-arch moldings!
    if kind == "truck":
        _, py_tt = P(0, zbot + 10.5)
        draw.line([(4, py_tt), (bw - 4, py_tt)], fill=(238, 242, 250), width=3)
        draw.line([(4, py_tt - 3), (bw - 4, py_tt - 3)], fill=(18, 30, 58), width=2)
        # Cab-to-bed physical gap + extended-cab & front door seams (cleanly stopping at beltline zb!)
        xg0, yg0 = P(-21.0, zbot + 3.0)
        _, yg1 = P(-21.0, zb)
        draw.rectangle([xg0 - 3, yg1, xg0 + 3, yg0], fill=(10, 12, 16))
        shutline_v(sp["x_door0"], zbot + 3.0, zb)
        shutline_v(sp["x_door1"], zbot + 3.0, zb)
        shutline_v(-19.5, zbot + 3.0, zb)
        draw_door_handle(6.5, zb - 6.5, chrome_bar=True)
        # Fuel filler door on bedside
        fx0, fy0 = P(-44.0, zb - 9.0)
        fx1, fy1 = P(-37.0, zb - 14.5)
        draw.rounded_rectangle([fx0, fy0, fx1, fy1], radius=3, outline=(16, 28, 56), width=2)
        # Bold 4x4 OFF-ROAD decal on rear bedside
        dx0, dy0 = P(-104.0, zb - 4.5)
        dx1, dy1 = P(-80.0, zb - 11.0)
        draw.rounded_rectangle([dx0, dy0, dx1, dy1], radius=3, fill=(214, 44, 34), outline=(248, 222, 128), width=2)
        draw.line([(dx0 + 5, (dy0 + dy1) * 0.5), (dx1 - 5, (dy0 + dy1) * 0.5)], fill=(252, 248, 236), width=2)
        # Chrome side bumper caps at nose & tail
        bx0, by0 = P(sp["x1"] - 7.0, zbot + 10.5)
        bx1, by1 = P(sp["x1"], zbot + 1.0)
        draw.rectangle([bx0, by0, bw, by1], fill=(204, 212, 224), outline=(102, 110, 122), width=2)
        rx_b0, ry_b0 = P(sp["x0"], zbot + 10.0)
        rx_b1, ry_b1 = P(sp["x0"] + 7.0, zbot + 1.0)
        draw.rectangle([0, ry_b0, rx_b1, ry_b1], fill=(204, 212, 224), outline=(102, 110, 122), width=2)

    elif kind == "sedan":
        # 90s black protective side rub-molding strip + thin chrome spear!
        _, ym0 = P(0, zbot + 11.2)
        _, ym1 = P(0, zbot + 8.6)
        draw.rectangle([6, ym0, bw - 6, ym1], fill=(26, 29, 32))
        draw.line([(6, ym0 - 1), (bw - 6, ym0 - 1)], fill=(206, 216, 214), width=2)
        # 4-door shutlines (front door, B-pillar seam, rear door) cleanly stopping at beltline zb!
        shutline_v(sp["x_door1"], zbot + 3.0, zb)
        shutline_v(sp["x_door0"], zbot + 3.0, zb)
        shutline_v(-36.0, zbot + 8.0, zb)
        draw_door_handle(5.5, zb - 5.2, chrome_bar=False)
        draw_door_handle(-27.0, zb - 5.2, chrome_bar=False)
        # Chrome beltline window weatherstrip molding
        wx0, wy0 = P(-48.0, zb - 0.6)
        wx1, _ = P(34.0, zb - 0.6)
        draw.line([(wx0, wy0), (wx1, wy0)], fill=(204, 214, 218), width=3)
        draw.line([(wx0, wy0 + 2), (wx1, wy0 + 2)], fill=(20, 24, 26), width=2)
        # Front fender amber repeater lamp
        ax0, ay0 = P(39.0, zb - 7.5)
        ax1, ay1 = P(44.5, zb - 9.8)
        draw.rounded_rectangle([ax0, ay0, ax1, ay1], radius=2, fill=(248, 154, 22), outline=(28, 32, 30))

    elif kind == "van":
        # Accurate Ram ProMaster High-Roof Cargo Van (matched to reference video frames)
        # 1. Thick satin-black lower protective body cladding along rocker panels
        _, yrk = P(0, zbot + 12.0)
        draw.rectangle([0, yrk, bw, bh], fill=(36, 40, 46))
        draw.line([(0, yrk), (bw, yrk)], fill=(22, 24, 28), width=2)
        # Rounded black wheel arch flare moldings
        for wx in (sp["wheel_x_f"], sp["wheel_x_r"]):
            wc_px, _ = P(wx, zbot)
            draw.arc([wc_px - 44, yrk - 26, wc_px + 44, yrk + 46], start=180, end=360, fill=(34, 38, 44), width=10)
        # Amber rectangular side marker reflectors set in black cladding
        for mx in (-82.0, -12.0):
            mx0, my0 = P(mx, zbot + 6.0)
            draw.rectangle([mx0 - 9, my0 - 3, mx0 + 9, my0 + 3], fill=(245, 142, 18), outline=(68, 38, 10))
        # 2. Stepped High-Roof Line (aerodynamic rise from windshield header z=68 to standing high-roof z=89)
        rx_cowl, ry_cowl = P(sp["x_cowl"], zroof - 18.0)
        rx_step, ry_step = P(sp["x_roof1"], zroof - 2.0)
        draw.polygon([(rx_cowl, ry_cowl), (rx_step, ry_step), (0, ry_step), (0, ry_cowl)], fill=pal["hi"])
        draw.line([(rx_cowl, ry_cowl), (rx_step, ry_step)], fill=(188, 194, 204), width=3)
        # 3. Passenger Side Sliding Door Rail & Vertical Handles (frame 005)
        # Horizontal silver guide rail with black end caps
        sx0, sy0 = P(-48.0, zb + 2.5)
        sx1, sy1 = P(8.0, zb + 2.5)
        draw.rectangle([sx0, sy0 - 2, sx1, sy0 + 2], fill=(188, 194, 204), outline=(48, 52, 58))
        draw.rectangle([sx0 - 3, sy0 - 3, sx0 + 2, sy0 + 3], fill=(24, 26, 30))
        draw.rectangle([sx1 - 2, sy0 - 3, sx1 + 3, sy0 + 3], fill=(24, 26, 30))
        # Sliding door shutlines
        shutline_v(-48.0, zbot + 12.0, zroof - 4.0)
        shutline_v(8.0, zbot + 12.0, zroof - 4.0)
        # Vertical black commercial handles (front cab door & sliding door)
        for hx, hz in ((22.0, zb - 2.0), (4.0, zb - 2.0)):
            hx_px, hz_px = P(hx, hz)
            draw.rounded_rectangle([hx_px - 3, hz_px - 10, hx_px + 3, hz_px + 10], radius=2, fill=(24, 26, 30), outline=(58, 64, 72))
            draw.rectangle([hx_px - 2, hz_px - 5, hx_px + 2, hz_px + 5], fill=(12, 14, 16))
        # Cab door shutlines
        shutline_v(sp["x_door0"], zbot + 12.0, zb)
        shutline_v(sp["x_door1"], zbot + 12.0, zb)
        # Driver side fuel filler door
        fx0, fy0 = P(-2.0, zbot + 16.0)
        draw.rounded_rectangle([fx0 - 6, fy0 - 8, fx0 + 6, fy0 + 8], radius=2, outline=(160, 166, 176), width=1)

    elif kind == "coupe":
        # Sculpted sport character crease + aggressive carbon side skirt + long coupe door seam
        cx0, cy0 = P(-64.0, zb - 6.0)
        cx1, cy1 = P(36.0, zb - 8.5)
        draw.line([(cx0, cy0), (cx1, cy1)], fill=(252, 118, 108), width=2)
        draw.line([(cx0, cy0 + 2), (cx1, cy1 + 2)], fill=(96, 8, 12), width=3)
        _, ysk = P(0, zbot + 5.2)
        draw.rectangle([0, ysk, bw, bh], fill=(28, 30, 35))
        shutline_v(sp["x_door0"], zbot + 4.0, zb)
        shutline_v(sp["x_door1"], zbot + 4.0, zb)
        draw_door_handle(-8.0, zb - 5.0, chrome_bar=False)
        # Subtle DOHC VTEC / tuner quarter decal above skirt
        gx0, gy0 = P(-38.0, zbot + 9.2)
        gx1, gy1 = P(-18.0, zbot + 6.8)
        draw.line([(gx0, gy0), (gx1, gy0)], fill=(242, 214, 78), width=2)
        draw.line([(gx0 + 3, gy1), (gx1 - 2, gy1)], fill=(238, 240, 246), width=2)

    # Crisp wheel-arch fender lip molding hugging the exact 3D arch_lift curve (0.88 * sqrt(ar^2 - dx^2))!
    for wx_c in (sp["wheel_x_f"], sp["wheel_x_r"]):
        ar = sp["arch_r"]
        pts_hi, pts_lip = [], []
        for k in range(25):
            dx = -ar + 2.0 * ar * k / 24.0
            hz = math.sqrt(max(0.0, ar * ar - dx * dx)) * 0.88
            pts_lip.append(P(wx_c + dx, zbot + hz))
            pts_hi.append(P(wx_c + dx, zbot + hz + 1.4))
        draw.line(pts_hi, fill=pal["sky"], width=2)
        draw.line(pts_lip, fill=(22, 24, 28), width=4)

    # Wrap-around front amber corner marker & rear red taillight wrap at exact nose/tail heights!
    fx0, fy0 = P(sp["x1"] - 7.5, sp["z_nose_top"] - 2.5)
    fx1, fy1 = P(sp["x1"], sp["z_nose_top"] - 9.5)
    draw.rounded_rectangle([fx0, fy0, bw, fy1], radius=3, fill=(248, 156, 24), outline=(36, 26, 12), width=2)
    glow_draw.rectangle([fx0 + 2, fy0 + 2, bw - 2, fy1 - 2], fill=(135, 82, 12))

    rx_t0, ry_t0 = P(sp["x0"], min(sp["z_belt"] - 2.0, sp["z_rear_top"] - 3.0))
    rx_t1, ry_t1 = P(sp["x0"] + 7.5, sp["z_bot"] + 12.5)
    if ry_t1 > ry_t0 + 4:
        draw.rounded_rectangle([0, ry_t0, rx_t1, ry_t1], radius=3, fill=(208, 24, 32), outline=(38, 12, 16), width=2)
        glow_draw.rectangle([2, ry_t0 + 2, rx_t1 - 2, ry_t1 - 2], fill=(140, 16, 22))


def _paint_top_plan(im, sp, pal, rng):
    """Paints RECT_TOP (hood, cowl wipers, roof, sunroof/ribs, trunk/bedliner) at exact world (x, y)."""
    kind = sp["kind"]
    arr = np.array(im)
    hi = np.array(pal["hi"], dtype=np.float32)
    mid = np.array(pal["mid"], dtype=np.float32)
    sky = np.array(pal["sky"], dtype=np.float32)

    y0_b, y1_b = 288, 544
    bh = y1_b - y0_b
    bw = 640
    yy = np.abs(np.linspace(-1.0, 1.0, bh))[:, None]
    crown = sky * (0.28 * (1.0 - yy ** 1.5)) + hi * (0.72 * (1.0 - 0.55 * yy ** 1.6)) + mid * (0.55 * yy ** 1.6)
    patch = np.repeat(crown[:, None, :], bw, axis=1)
    arr[y0_b:y1_b, 0:bw] = _add_flake(patch, rng, amp=3.0 if kind != "van" else 1.8)
    im.paste(Image.fromarray(arr[y0_b:y1_b, 0:bw]), (0, y0_b))
    draw = ImageDraw.Draw(im)

    def T(wx, wy):
        return vs.top_world_to_px(sp, wx, wy)

    hw = sp["hw"]
    xc = sp["x_cowl"]

    # Black windshield-base cowl vent + wiper blades right behind hood hinge!
    cx0, cy0 = T(xc - 4.5, -hw * 0.80)
    cx1, cy1 = T(xc + 0.5, hw * 0.80)
    draw.rectangle([cx0, cy0, cx1, cy1], fill=(24, 27, 32))
    # Hood shutlines & power-dome / louver creases
    hx0, hy0 = T(xc + 1.0, -hw * 0.82)
    hx1, hy1 = T(sp["x1"] - 3.0, hw * 0.82)
    draw.rounded_rectangle([hx0, hy0, hx1, hy1], radius=6, outline=pal["lo"], width=3)
    # Subtle sculpted hood character lines
    p_a0, p_a1 = T(xc + 4.0, -hw * 0.44), T(sp["x1"] - 6.0, -hw * 0.34)
    p_b0, p_b1 = T(xc + 4.0, hw * 0.44), T(sp["x1"] - 6.0, hw * 0.34)
    draw.line([p_a0, p_a1], fill=pal["sky"], width=2)
    draw.line([p_b0, p_b1], fill=pal["sky"], width=2)

    # Roof side rain-drip moldings
    rf0, rfy0 = T(sp["x_roof0"], -sp["y_roof"] + 1.5)
    rf1, rfy1 = T(sp["x_roof1"], sp["y_roof"] - 1.5)
    draw.line([(rf0, rfy0), (rf1, rfy0)], fill=(26, 30, 34), width=3)
    draw.line([(rf0, rfy1), (rf1, rfy1)], fill=(26, 30, 34), width=3)

    if kind == "truck":
        # Sprayed dark Rhino bedliner ribs in open cargo bed + aluminum diamond-plate toolbox!
        bx0, by0 = T(sp["x_bed_r"], -hw * 0.78)
        bx1, by1 = T(sp["x_bed_f"], hw * 0.78)
        draw.rectangle([bx0, by0, bx1, by1], fill=(32, 35, 40), outline=(18, 20, 24), width=3)
        for wy in np.linspace(-hw * 0.72, hw * 0.72, 13):
            pa = T(sp["x_bed_r"] + 4.0, wy)
            pb = T(-44.0, wy)
            draw.line([pa, pb], fill=(50, 54, 62), width=3)
            draw.line([(pa[0], pa[1] + 2), (pb[0], pb[1] + 2)], fill=(20, 22, 26), width=2)
        # Diamond-plate aluminum toolbox behind cab (-42 .. -23)
        tx0, ty0 = T(-42.5, -hw * 0.80)
        tx1, ty1 = T(-23.0, hw * 0.80)
        draw.rectangle([tx0, ty0, tx1, ty1], fill=(192, 200, 212), outline=(92, 98, 110), width=3)
        for ix in range(int(tx0) + 5, int(tx1) - 4, 8):
            for iy in range(int(ty0) + 5, int(ty1) - 4, 9):
                draw.line([(ix, iy), (ix + 3, iy + 3)], fill=(238, 243, 250), width=2)

    elif kind == "sedan":
        # Tinted glass sunroof with matte-black rubber perimeter seal + trunk shutlines
        sx0, sy0 = T(-12.0, -hw * 0.50)
        sx1, sy1 = T(6.0, hw * 0.50)
        draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=6, fill=(24, 34, 44), outline=(18, 20, 24), width=4)
        draw.line([(sx0 + 8, sy0 + 8), (sx1 - 12, sy1 - 8)], fill=(68, 94, 118), width=4)
        kx0, ky0 = T(sp["x_trunk_r"] + 2.0, -hw * 0.80)
        kx1, ky1 = T(sp["x_trunk_f"], hw * 0.80)
        draw.rounded_rectangle([kx0, ky0, kx1, ky1], radius=5, outline=pal["lo"], width=3)

    elif kind == "van":
        # 7 longitudinal stamped Econoline roof anti-drum ribs!
        for wy in np.linspace(-sp["y_roof"] * 0.78, sp["y_roof"] * 0.78, 7):
            p0 = T(sp["x_roof0"] + 6.0, wy - 1.5)
            p1 = T(sp["x_roof1"] - 6.0, wy + 1.5)
            draw.rounded_rectangle([p0[0], p0[1], p1[0], p1[1]], radius=3, fill=(196, 202, 210), outline=(248, 250, 254), width=1)

    elif kind == "coupe":
        # Aggressive twin carbon-mesh hood louvers!
        for sgn in (-1.0, 1.0):
            vx0, vy0 = T(xc + 16.0, sgn * hw * 0.22)
            vx1, vy1 = T(xc + 40.0, sgn * hw * 0.50)
            xa, xb = min(vx0, vx1), max(vx0, vx1)
            ya, yb = min(vy0, vy1), max(vy0, vy1)
            draw.rounded_rectangle([xa, ya, xb, yb], radius=4, fill=(24, 26, 30), outline=(88, 10, 14), width=2)
            for lx in range(int(xa) + 5, int(xb) - 4, 7):
                draw.line([(lx, ya + 3), (lx, yb - 3)], fill=(58, 62, 70), width=2)


def _paint_front_and_rear(im, glow_draw, sp, pal):
    """Paints RECT_FRONT and RECT_REAR using exact world (y, z) -> pixel coordinates so
    the bumper (z_bot .. z_bumper_top) and upper fascia (z_bumper_top .. z_top) meet seamlessly!"""
    kind = sp["kind"]
    draw = ImageDraw.Draw(im)
    hw = sp["hw"]
    zbot = sp["z_bot"]
    zbmp = sp["z_bmp"]

    # Bleed base body paint across front (640..1024, 0..272) & rear (640..1024, 272..544)
    draw.rectangle([640, 0, 1024, 272], fill=pal["mid"])
    draw.rectangle([640, 272, 1024, 544], fill=pal["mid"])

    def F(wy, wz):
        return vs.front_world_to_px(sp, wy, wz)

    def R(wy, wz):
        return vs.rear_world_to_px(sp, wy, wz)

    def box_F(wy_left, wz_top, wy_right, wz_bot):
        x0, y0 = F(wy_left, wz_top)
        x1, y1 = F(wy_right, wz_bot)
        return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]

    def box_R(wy_left, wz_top, wy_right, wz_bot):
        x0, y0 = R(wy_left, wz_top)
        x1, y1 = R(wy_right, wz_bot)
        return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]

    zn = sp["z_nose_top"]
    zr = sp["z_rear_top"]

    if kind == "truck":
        # FRONT: Chrome grille shell + dark mesh + twin chrome bars + blue oval + stacked quad lights + chrome bumper!
        gr = box_F(hw * 0.56, zn - 3.0, -hw * 0.56, zbmp + 2.0)
        draw.rounded_rectangle(gr, radius=8, fill=(24, 28, 34), outline=(218, 226, 238), width=7)
        for gx in range(int(gr[0]) + 10, int(gr[2]) - 8, 12):
            draw.line([(gx, gr[1] + 6), (gx, gr[3] - 6)], fill=(46, 52, 60), width=2)
        ym = 0.5 * (gr[1] + gr[3])
        draw.rectangle([gr[0] + 6, ym - 9, gr[2] - 6, ym - 2], fill=(210, 218, 230))
        draw.rectangle([gr[0] + 6, ym + 2, gr[2] - 6, ym + 9], fill=(210, 218, 230))
        cx = 0.5 * (gr[0] + gr[2])
        draw.ellipse([cx - 18, ym - 10, cx + 18, ym + 10], fill=(26, 66, 152), outline=(238, 244, 252), width=3)

        for sgn in (1.0, -1.0):
            hl = box_F(sgn * hw * 0.94, zn - 3.5, sgn * hw * 0.60, zbmp + 8.5)
            _draw_headlight_unit(draw, glow_draw, *hl, projector=False)
            am = box_F(sgn * hw * 0.94, zbmp + 7.2, sgn * hw * 0.60, zbmp + 2.2)
            draw.rounded_rectangle(am, radius=3, fill=(248, 154, 22), outline=(72, 44, 12), width=2)
            glow_draw.rectangle([am[0] + 3, am[1] + 3, am[2] - 3, am[3] - 3], fill=(135, 80, 10))

        # Chrome bumper + black impact strip + lower air dam + tow hooks + plate
        bm_chr = box_F(hw, zbmp, -hw, zbot + 3.2)
        bm_dam = box_F(hw, zbot + 3.2, -hw, zbot)
        draw.rectangle([640, bm_chr[1], 1024, bm_chr[3]], fill=(210, 218, 230), outline=(112, 120, 134), width=2)
        draw.rectangle([640, bm_dam[1], 1024, 272], fill=(24, 27, 32))
        px_c, py_c = F(0.0, zbot + 5.2)
        _draw_plate(draw, px_c, py_c, 84, 36, pal["plate"])

        # REAR: Stamped tailgate + brushed aluminum applique + latch + vertical taillights + chrome step bumper
        tg = box_R(-hw * 0.80, zr - 2.0, hw * 0.80, zbmp + 1.5)
        draw.rectangle(tg, fill=pal["mid"], outline=pal["lo"], width=3)
        ap = box_R(-hw * 0.78, zr - 14.0, hw * 0.78, zbmp + 6.0)
        draw.rectangle(ap, fill=(196, 204, 216), outline=(92, 100, 112), width=2)
        hd = box_R(-5.5, zr - 5.0, 5.5, zr - 9.5)
        draw.rounded_rectangle(hd, radius=2, fill=(22, 26, 32))
        for sgn in (-1.0, 1.0):
            tl = box_R(sgn * hw * 0.83, zr - 3.5, sgn * hw * 0.96, zbmp + 2.5)
            draw.rounded_rectangle(tl, radius=4, fill=(210, 24, 30), outline=(36, 12, 16), width=2)
            rv_y = tl[1] + (tl[3] - tl[1]) * 0.68
            draw.rectangle([tl[0] + 3, rv_y, tl[2] - 3, tl[3] - 5], fill=(236, 240, 248))
            glow_draw.rectangle([tl[0] + 3, tl[1] + 4, tl[2] - 3, rv_y - 2], fill=(155, 18, 22))
        rb = box_R(-hw, zbmp, hw, zbot)
        draw.rectangle([640, rb[1], 1024, 544], fill=(204, 212, 224), outline=(102, 110, 122), width=2)
        draw.rectangle([640, rb[1], 1024, rb[1] + 9], fill=(32, 36, 42))
        rcx, rcy = R(0.0, zbot + 4.8)
        _draw_plate(draw, rcx, rcy, 84, 34, pal["plate"])

    elif kind == "sedan":
        # FRONT: Slatted 90s grille + wide fluted headlights + corner ambers + rub-strip bumper + lower intake!
        gr = box_F(hw * 0.44, zn - 2.2, -hw * 0.44, zbmp + 2.2)
        draw.rounded_rectangle(gr, radius=6, fill=(20, 24, 26), outline=(198, 210, 212), width=4)
        for gy in np.linspace(gr[1] + 8, gr[3] - 8, 3):
            draw.line([(gr[0] + 6, gy), (gr[2] - 6, gy)], fill=(148, 160, 164), width=2)
        cx, cy = 0.5 * (gr[0] + gr[2]), 0.5 * (gr[1] + gr[3])
        draw.ellipse([cx - 12, cy - 10, cx + 12, cy + 10], outline=(224, 232, 236), width=3)

        for sgn in (1.0, -1.0):
            hl = box_F(sgn * hw * 0.82, zn - 2.0, sgn * hw * 0.47, zbmp + 2.2)
            _draw_headlight_unit(draw, glow_draw, *hl, projector=False)
            am = box_F(sgn * hw * 0.96, zn - 2.4, sgn * hw * 0.82, zbmp + 2.4)
            draw.rounded_rectangle(am, radius=4, fill=(248, 152, 22), outline=(68, 42, 12), width=2)

        # Bumper rub strip + lower black grille + fog pockets + plate
        rs = box_F(hw, zbmp - 0.5, -hw, zbmp - 2.6)
        draw.rectangle([640, rs[1], 1024, rs[3]], fill=(24, 28, 30))
        li = box_F(hw * 0.68, zbot + 3.6, -hw * 0.68, zbot + 0.8)
        draw.rounded_rectangle(li, radius=5, fill=(18, 22, 24))
        for fy in range(int(li[1]) + 5, int(li[3]) - 3, 6):
            draw.line([(li[0] + 6, fy), (li[2] - 6, fy)], fill=(52, 58, 62), width=2)
        px_c, py_c = F(0.0, zbot + 5.7)
        _draw_plate(draw, px_c, py_c, 80, 30, pal["plate"])

        # REAR: Wide 90s ruby/amber/reverse taillight clusters + recessed trunk plate pocket + rub-strip bumper
        for sgn in (-1.0, 1.0):
            tl = box_R(sgn * hw * 0.36, zr - 3.5, sgn * hw * 0.96, zbmp + 3.0)
            draw.rounded_rectangle(tl, radius=5, fill=(208, 24, 34), outline=(38, 12, 16), width=3)
            ym = tl[1] + (tl[3] - tl[1]) * 0.42
            draw.rectangle([tl[0] + 4, tl[1] + 4, tl[2] - 4, ym], fill=(244, 148, 22))
            if sgn > 0:
                draw.rectangle([tl[2] - 38, tl[1] + 4, tl[2] - 4, ym], fill=(238, 242, 248))
            else:
                draw.rectangle([tl[0] + 4, tl[1] + 4, tl[0] + 38, ym], fill=(238, 242, 248))
            glow_draw.rectangle([tl[0] + 4, ym + 3, tl[2] - 4, tl[3] - 4], fill=(155, 18, 24))
        pk = box_R(-hw * 0.32, zr - 4.5, hw * 0.32, zbmp + 2.5)
        draw.rounded_rectangle(pk, radius=5, fill=pal["lo"], outline=(14, 34, 24), width=2)
        rcx, rcy = R(0.0, 0.5 * (zr - 4.5 + zbmp + 2.5))
        _draw_plate(draw, rcx, rcy, 80, 34, pal["plate"])
        rrs = box_R(-hw, zbmp - 0.8, hw, zbmp - 3.2)
        draw.rectangle([640, rrs[1], 1024, rrs[3]], fill=(24, 28, 30))

    elif kind == "van":
        # FRONT: Modern Ram ProMaster multi-slat commercial grille, high swept headlights, multi-piece bumper
        gr = box_F(hw * 0.62, zn - 2.0, -hw * 0.62, zbmp + 3.0)
        draw.rounded_rectangle(gr, radius=6, fill=(28, 30, 36), outline=(52, 56, 64), width=3)
        # Deep horizontal black commercial grille bars
        for gy in np.linspace(gr[1] + 10, gr[3] - 10, 6):
            draw.line([(gr[0] + 8, gy), (gr[2] - 8, gy)], fill=(44, 48, 56), width=3)
            draw.line([(gr[0] + 8, gy + 2), (gr[2] - 8, gy + 2)], fill=(18, 20, 24), width=2)
        # Prominent central chrome/silver emblem badge (frame 010)
        cx, cy = 0.5 * (gr[0] + gr[2]), 0.5 * (gr[1] + gr[3])
        draw.ellipse([cx - 20, cy - 12, cx + 20, cy + 12], fill=(210, 216, 226), outline=(130, 136, 148), width=3)
        draw.ellipse([cx - 14, cy - 8, cx + 14, cy + 8], fill=(32, 35, 42), outline=(178, 184, 194), width=2)

        # Swept modern high-mounted headlights extending up into fenders
        for sgn in (1.0, -1.0):
            bz = box_F(sgn * hw * 0.96, zn - 1.0, sgn * hw * 0.62, zbmp + 2.0)
            draw.rounded_rectangle(bz, radius=4, fill=(48, 52, 58), outline=(26, 28, 32), width=2)
            hl = box_F(sgn * hw * 0.94, zn - 2.5, sgn * hw * 0.64, zbmp + 7.5)
            _draw_headlight_unit(draw, glow_draw, *hl, projector=True)
            am = box_F(sgn * hw * 0.94, zbmp + 6.8, sgn * hw * 0.64, zbmp + 2.5)
            draw.rectangle(am, fill=(245, 142, 18), outline=(78, 44, 12), width=2)

        # Multi-piece black commercial bumper with lower air intake & license plate
        fb = box_F(hw, zbmp + 2.0, -hw, zbot)
        draw.rectangle([640, fb[1], 1024, 272], fill=(36, 40, 46), outline=(22, 24, 28), width=2)
        # Lower central radiator cooling intake
        lower_intake = box_F(hw * 0.44, zbmp - 2.0, -hw * 0.44, zbot + 3.0)
        draw.rounded_rectangle(lower_intake, radius=3, fill=(18, 20, 24), outline=(52, 56, 64))
        for lgy in np.linspace(lower_intake[1] + 6, lower_intake[3] - 6, 3):
            draw.line([(lower_intake[0] + 4, lgy), (lower_intake[2] - 4, lgy)], fill=(38, 42, 48), width=2)
        # Side fog light / tow scoop recesses
        for sgn in (1.0, -1.0):
            fog_sc = box_F(sgn * hw * 0.88, zbmp - 2.0, sgn * hw * 0.58, zbot + 3.0)
            draw.rounded_rectangle(fog_sc, radius=4, fill=(22, 24, 28), outline=(48, 52, 60))
        px_c, py_c = F(0.0, zbot + 6.0)
        _draw_plate(draw, px_c, py_c, 84, 35, pal["plate"])

        # REAR: Wide walk-in cargo door opening, vertical D-pillar taillights, high 3rd brake light, open barn doors
        # Outer rear door opening frame with dark rubber gasket lining
        bd = box_R(-hw * 0.78, zr - 4.0, hw * 0.78, zbmp + 1.5)
        draw.rectangle(bd, fill=(242, 245, 250), outline=(28, 30, 36), width=5)
        # Vertical ProMaster D-pillar taillight columns (frame 001, 015, 020)
        for sgn in (-1.0, 1.0):
            tl = box_R(sgn * hw * 0.82, zr - 36.0, sgn * hw * 0.96, zbmp + 3.0)
            draw.rounded_rectangle(tl, radius=4, fill=(198, 20, 26), outline=(32, 10, 14), width=2)
            # Amber turn signal segment
            am_y = tl[1] + (tl[3] - tl[1]) * 0.45
            draw.rectangle([tl[0] + 3, am_y, tl[2] - 3, am_y + 14], fill=(245, 142, 18), outline=(68, 38, 10))
            # White reverse light segment
            rv_y = tl[1] + (tl[3] - tl[1]) * 0.72
            draw.rectangle([tl[0] + 3, rv_y, tl[2] - 3, tl[3] - 4], fill=(238, 242, 248), outline=(54, 58, 66))
            glow_draw.rectangle([tl[0] + 3, tl[1] + 4, tl[2] - 3, am_y - 2], fill=(160, 18, 22))

        # Center High-Mount 3rd Brake Light above rear door header (frame 001, 020)
        c_third = box_R(-hw * 0.14, zr - 0.5, hw * 0.14, zr - 3.8)
        draw.rounded_rectangle(c_third, radius=2, fill=(218, 24, 28), outline=(42, 12, 16))
        glow_draw.rectangle([c_third[0] + 2, c_third[1] + 1, c_third[2] - 2, c_third[3] - 1], fill=(180, 20, 24))

        # Open Barn Doors inner cards texture (stamped upper metal, dark lower kick panel, latch handle)
        door_l_card = box_R(-hw * 0.74, zr - 6.0, -hw * 0.04, zbmp + 3.0)
        door_r_card = box_R(hw * 0.04, zr - 6.0, hw * 0.74, zbmp + 3.0)
        for dc, is_right in ((door_l_card, False), (door_r_card, True)):
            d_mid = dc[1] + (dc[3] - dc[1]) * 0.52
            # Upper stamped sheet metal
            draw.rectangle([dc[0], dc[1], dc[2], d_mid], fill=(236, 240, 246), outline=(158, 164, 174), width=2)
            # Two horizontal stamped inset bays in upper door (frame 001, 020)
            bay_h = (d_mid - dc[1]) * 0.38
            for by_i in (dc[1] + 6, dc[1] + bay_h + 10):
                draw.rounded_rectangle([dc[0] + 6, by_i, dc[2] - 6, by_i + bay_h - 4], radius=4,
                                       fill=(218, 222, 230), outline=(172, 178, 188), width=2)
            # Lower dark protective kick panel
            draw.rectangle([dc[0], d_mid, dc[2], dc[3]], fill=(38, 42, 48), outline=(22, 24, 28), width=2)
            # Interior release latch handle on right door (frame 001, 020)
            if is_right:
                lh = [dc[0] + 10, d_mid + 8, dc[0] + 34, d_mid + 24]
                draw.rounded_rectangle(lh, radius=3, fill=(18, 20, 24), outline=(58, 64, 72))
                draw.rectangle([lh[0] + 6, lh[1] + 5, lh[2] - 6, lh[3] - 5], fill=(34, 38, 44))

        # Black rear commercial step bumper with non-slip center tread
        rb = box_R(-hw, zbmp + 2.0, hw, zbot)
        draw.rectangle([640, rb[1], 1024, 544], fill=(36, 40, 46), outline=(22, 24, 28), width=2)
        # Center step recess
        step_rc = box_R(-hw * 0.55, zbmp + 1.0, hw * 0.55, zbot + 3.0)
        draw.rectangle(step_rc, fill=(24, 26, 30), outline=(52, 56, 64))
        for sx in range(int(step_rc[0]) + 6, int(step_rc[2]) - 4, 8):
            draw.line([(sx, step_rc[1] + 2), (sx, step_rc[3] - 2)], fill=(44, 48, 56), width=2)

    elif kind == "coupe":
        # FRONT: Smoked twin-projector headlights + sport mesh grille + aluminum intercooler + yellow JDM fogs!
        gr = box_F(hw * 0.36, zn - 3.5, -hw * 0.36, zbmp + 2.0)
        draw.polygon([(gr[0], gr[1]), (gr[2], gr[1]), (gr[2] - 10, gr[3]), (gr[0] + 10, gr[3])], fill=(20, 22, 26))
        cx, cy = 0.5 * (gr[0] + gr[2]), 0.5 * (gr[1] + gr[3])
        draw.rounded_rectangle([cx - 8, cy - 6, cx + 8, cy + 6], radius=2, fill=(224, 24, 28), outline=(235, 240, 246), width=2)

        for sgn in (1.0, -1.0):
            hl = box_F(sgn * hw * 0.94, zn - 1.8, sgn * hw * 0.40, zbmp + 1.5)
            _draw_headlight_unit(draw, glow_draw, *hl, projector=True)

        # Wide aluminum front-mount intercooler in bumper mouth + yellow fogs + carbon lip splitter!
        ic_o = box_F(hw * 0.50, zbmp - 1.0, -hw * 0.50, zbot + 1.6)
        draw.rounded_rectangle(ic_o, radius=5, fill=(18, 20, 24), outline=(96, 10, 14), width=2)
        ic_c = [ic_o[0] + 12, ic_o[1] + 5, ic_o[2] - 12, ic_o[3] - 5]
        draw.rectangle(ic_c, fill=(172, 182, 194))
        for iy in range(int(ic_c[1]) + 4, int(ic_c[3]) - 2, 6):
            draw.line([(ic_c[0] + 2, iy), (ic_c[2] - 2, iy)], fill=(88, 96, 108), width=2)
        for sgn in (1.0, -1.0):
            fg = box_F(sgn * hw * 0.90, zbmp - 1.2, sgn * hw * 0.68, zbot + 1.8)
            draw.rounded_rectangle(fg, radius=5, fill=(22, 24, 28))
            fcx, fcy = 0.5 * (fg[0] + fg[2]), 0.5 * (fg[1] + fg[3])
            fr = min(fg[2] - fg[0], fg[3] - fg[1]) * 0.38
            draw.ellipse([fcx - fr, fcy - fr, fcx + fr, fcy + fr], fill=(250, 214, 34), outline=(140, 118, 18), width=2)
            glow_draw.ellipse([fcx - fr + 2, fcy - fr + 2, fcx + fr - 2, fcy + fr - 2], fill=(165, 138, 16))
        sp_lip = box_F(hw, zbot + 1.4, -hw, zbot)
        draw.rectangle([640, sp_lip[1], 1024, 272], fill=(22, 24, 28))
        px_c, py_c = F(hw * 0.55, zbot + 5.0)
        _draw_plate(draw, px_c, py_c, 62, 24, pal["plate"])

        # REAR: Smoked JDM quad-ring ruby taillights + center garnish + matte black rear aero diffuser!
        for sgn in (-1.0, 1.0):
            tl = box_R(sgn * hw * 0.36, zr - 3.5, sgn * hw * 0.95, zbmp + 4.5)
            draw.rounded_rectangle(tl, radius=7, fill=(58, 12, 18), outline=(24, 8, 10), width=3)
            ym = 0.5 * (tl[1] + tl[3])
            w_tl = tl[2] - tl[0]
            rr = min(w_tl * 0.19, (tl[3] - tl[1]) * 0.38)
            for cx_r in (tl[0] + w_tl * 0.30, tl[0] + w_tl * 0.70):
                draw.ellipse([cx_r - rr, ym - rr, cx_r + rr, ym + rr], fill=(236, 24, 34), outline=(255, 138, 128), width=3)
                draw.ellipse([cx_r - rr * 0.42, ym - rr * 0.42, cx_r + rr * 0.42, ym + rr * 0.42], fill=(246, 214, 198))
                glow_draw.ellipse([cx_r - rr + 2, ym - rr + 2, cx_r + rr - 2, ym + rr - 2], fill=(180, 20, 28))
        rcx, rcy = R(0.0, 0.5 * (zr - 4.0 + zbmp + 3.0))
        _draw_plate(draw, rcx, rcy, 80, 34, pal["plate"])
        df = box_R(-hw * 0.86, zbot + 5.2, hw * 0.86, zbot)
        draw.rounded_rectangle([df[0], df[1], df[2], 544], radius=6, fill=(24, 26, 32), outline=(14, 16, 20), width=2)
        for dx in np.linspace(df[0] + 24, df[2] - 24, 5):
            draw.line([(dx, df[1] + 4), (dx, 540)], fill=(48, 52, 60), width=3)


def _paint_wheel_and_tread(im, sp):
    """Paints RECT_WHEEL (0..256, 544..800, center=(128, 672), R_tire=116) synced 1:1 with sp['rim_ratio']!"""
    kind = sp["kind"]
    draw = ImageDraw.Draw(im)
    wx0, wy0, wx1, wy1 = vs.RECT_WHEEL
    cx, cy = (wx0 + wx1) // 2, (wy0 + wy1) // 2
    r_tire = 116
    r_rim = int(round(r_tire * sp["rim_ratio"]))  # Exact match to 3D wheel rim vertex ring!

    draw.rectangle([wx0, wy0, wx1, wy1], fill=(22, 24, 27))
    # Pneumatic rubber tire sidewall with molded concentric ribs (strictly outside r_rim!)
    draw.ellipse([cx - r_tire, cy - r_tire, cx + r_tire, cy + r_tire], fill=(30, 32, 36), outline=(18, 20, 22), width=3)
    r_mid_sw = (r_tire + r_rim) // 2
    draw.ellipse([cx - r_mid_sw - 5, cy - r_mid_sw - 5, cx + r_mid_sw + 5, cy + r_mid_sw + 5], outline=(44, 47, 52), width=2)
    draw.ellipse([cx - r_mid_sw + 6, cy - r_mid_sw + 6, cx + r_mid_sw - 6, cy + r_mid_sw - 6], outline=(20, 22, 25), width=2)

    if kind == "truck":
        # Subtle white-letter sidewall ticks inside rubber band + 6-spoke machined off-road rim
        for k in range(20):
            a = 2 * math.pi * k / 20
            if k % 5 != 0:
                draw.line([(cx + math.cos(a) * (r_mid_sw - 2), cy + math.sin(a) * (r_mid_sw - 2)),
                           (cx + math.cos(a) * (r_mid_sw + 3), cy + math.sin(a) * (r_mid_sw + 3))], fill=(182, 188, 196), width=2)
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(22, 24, 28), outline=(212, 220, 232), width=6)
        draw.ellipse([cx - int(r_rim * 0.72), cy - int(r_rim * 0.72), cx + int(r_rim * 0.72), cy + int(r_rim * 0.72)], fill=(76, 82, 90))
        for k in range(6):
            a = 2 * math.pi * k / 6
            ca, sa = math.cos(a), math.sin(a)
            pa, qa = -sa, ca
            pts = [
                (cx + ca * 15 + pa * 9, cy + sa * 15 + qa * 9),
                (cx + ca * (r_rim - 5) + pa * 8, cy + sa * (r_rim - 5) + qa * 8),
                (cx + ca * (r_rim - 5) - pa * 8, cy + sa * (r_rim - 5) - qa * 8),
                (cx + ca * 15 - pa * 9, cy + sa * 15 - qa * 9),
            ]
            draw.polygon(pts, fill=(202, 210, 222), outline=(108, 114, 126))
            lx, ly = cx + ca * 22, cy + sa * 22
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(232, 238, 246), outline=(36, 40, 46))
        draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(34, 38, 44), outline=(214, 62, 38), width=3)

    elif kind == "sedan":
        # Clean 90s 5-spoke silver alloy rim
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(26, 30, 34), outline=(210, 218, 226), width=6)
        draw.ellipse([cx - int(r_rim * 0.72), cy - int(r_rim * 0.72), cx + int(r_rim * 0.72), cy + int(r_rim * 0.72)], fill=(88, 94, 102))
        for k in range(5):
            a = 2 * math.pi * k / 5 - math.pi / 2
            ca, sa = math.cos(a), math.sin(a)
            pa, qa = -sa, ca
            pts = [
                (cx + ca * 14 + pa * 11, cy + sa * 14 + qa * 11),
                (cx + ca * (r_rim - 4) + pa * 8, cy + sa * (r_rim - 4) + qa * 8),
                (cx + ca * (r_rim - 4) - pa * 8, cy + sa * (r_rim - 4) - qa * 8),
                (cx + ca * 14 - pa * 11, cy + sa * 14 - qa * 11),
            ]
            draw.polygon(pts, fill=(212, 218, 226), outline=(132, 138, 148))
            lx, ly = cx + ca * 21, cy + sa * 21
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(56, 60, 68))
        draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(192, 200, 210), outline=(88, 94, 102), width=2)

    elif kind == "van":
        # Heavy-duty 8-vent painted steel commercial wheel + black center hubcap
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(172, 178, 186), outline=(116, 122, 132), width=6)
        draw.ellipse([cx - int(r_rim * 0.76), cy - int(r_rim * 0.76), cx + int(r_rim * 0.76), cy + int(r_rim * 0.76)], outline=(92, 98, 108), width=3)
        for k in range(8):
            a = 2 * math.pi * k / 8
            vx, vy = cx + math.cos(a) * (r_rim * 0.68), cy + math.sin(a) * (r_rim * 0.68)
            draw.ellipse([vx - 6, vy - 6, vx + 6, vy + 6], fill=(24, 26, 30))
            lx, ly = cx + math.cos(a + 0.39) * 30, cy + math.sin(a + 0.39) * 30
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(54, 58, 64))
        draw.ellipse([cx - 23, cy - 23, cx + 23, cy + 23], fill=(28, 31, 36), outline=(92, 98, 108), width=2)

    elif kind == "coupe":
        # 6-spoke anodized bronze deep-dish tuner wheel + slotted rotor + red caliper strictly inside barrel!
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(22, 24, 28), outline=(218, 224, 232), width=6)
        rb = int(r_rim * 0.70)
        draw.ellipse([cx - rb, cy - rb, cx + rb, cy + rb], fill=(112, 118, 128))
        draw.pieslice([cx - rb, cy - rb, cx + rb, cy + rb], start=-30, end=30, fill=(208, 28, 32))
        for k in range(6):
            a = 2 * math.pi * k / 6
            ca, sa = math.cos(a), math.sin(a)
            pa, qa = -sa, ca
            pts = [
                (cx + ca * 15 + pa * 8, cy + sa * 15 + qa * 8),
                (cx + ca * (r_rim - 5) + pa * 7, cy + sa * (r_rim - 5) + qa * 7),
                (cx + ca * (r_rim - 5) - pa * 7, cy + sa * (r_rim - 5) - qa * 7),
                (cx + ca * 15 - pa * 8, cy + sa * 15 - qa * 8),
            ]
            draw.polygon(pts, fill=(172, 130, 72), outline=(94, 68, 34))
            lx, ly = cx + ca * 21, cy + sa * 21
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(42, 88, 198))
        draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(30, 32, 36), outline=(178, 136, 76), width=2)

    # Tire Tread Strip (RECT_TREAD: 256..512, 544..800)
    tx0, ty0, tx1, ty1 = vs.RECT_TREAD
    draw.rectangle([tx0, ty0, tx1, ty1], fill=(28, 30, 34))
    if kind == "truck":
        for ty in range(ty0 + 4, ty1 - 8, 22):
            draw.polygon([(tx0 + 8, ty), (tx0 + 118, ty + 6), (tx0 + 118, ty + 16), (tx0 + 8, ty + 12)], fill=(46, 49, 55))
            draw.polygon([(tx0 + 138, ty + 8), (tx1 - 8, ty + 2), (tx1 - 8, ty + 14), (tx0 + 138, ty + 18)], fill=(46, 49, 55))
    elif kind == "coupe":
        for gx in (tx0 + 56, tx0 + 128, tx0 + 200):
            draw.line([(gx, ty0), (gx, ty1)], fill=(15, 17, 20), width=6)
        for ty in range(ty0 + 8, ty1 - 12, 20):
            draw.line([(tx0 + 128, ty), (tx0 + 14, ty + 15)], fill=(18, 20, 23), width=4)
            draw.line([(tx0 + 128, ty), (tx1 - 14, ty + 15)], fill=(18, 20, 23), width=4)
    else:
        for gx in (tx0 + 48, tx0 + 100, tx0 + 156, tx0 + 208):
            draw.line([(gx, ty0), (gx, ty1)], fill=(15, 17, 20), width=6)
        for ty in range(ty0 + 6, ty1 - 6, 16):
            draw.line([(tx0 + 8, ty), (tx1 - 8, ty + 4)], fill=(21, 23, 27), width=2)


def _paint_shared_swatches(im, glow_draw, rng):
    """Paints clean smoked automotive glass, brushed chrome, matte black trim, engine bay,
    quilted cabin interior, charred wreck metal, and hot embers."""
    arr = np.array(im)

    # 1. Clean Smoked Automotive Safety Glass (RECT_GLASS: 512..800, 544..800)
    # Top (row 0) = upper roof edge (dark tint -> sky reflection band -> dark charcoal cabin depth at bottom)
    gx0, gy0, gx1, gy1 = vs.RECT_GLASS
    gh, gw = gy1 - gy0, gx1 - gx0
    gy, gx = np.mgrid[0:gh, 0:gw]
    v_norm = gy / float(gh)
    sky_grad = np.exp(-((v_norm - 0.30) / 0.22) ** 2) * 0.72
    diag_gloss = np.exp(-(((gx * 0.55 + gy) - 165.0) / 26.0) ** 2) * 0.55
    glass = np.zeros((gh, gw, 3), dtype=np.float32)
    glass[:, :, 0] = 18.0 + sky_grad * 36.0 + diag_gloss * 58.0
    glass[:, :, 1] = 26.0 + sky_grad * 52.0 + diag_gloss * 72.0
    glass[:, :, 2] = 34.0 + sky_grad * 68.0 + diag_gloss * 86.0
    arr[gy0:gy1, gx0:gx1] = np.clip(glass, 0, 255).astype(np.uint8)

    # 2. Chrome (RECT_CHROME: 800..1024, 544..670)
    cx0, cy0, cx1, cy1 = vs.RECT_CHROME
    ch_h, ch_w = cy1 - cy0, cx1 - cx0
    cg = np.linspace(0.0, 1.0, ch_h)[:, None]
    cv = np.where(cg < 0.48, 238.0 - cg * 115.0, 82.0 + (cg - 0.48) * 250.0)
    chr_arr = np.zeros((ch_h, ch_w, 3), dtype=np.float32)
    chr_arr[:, :, 0] = cv * 0.96
    chr_arr[:, :, 1] = cv * 0.99
    chr_arr[:, :, 2] = np.clip(cv * 1.04, 0, 255)
    arr[cy0:cy1, cx0:cx1] = np.clip(chr_arr[:, None, :] if chr_arr.ndim == 2 else chr_arr, 0, 255).astype(np.uint8)

    # 3. Matte Black Rubber / Plastic Trim (RECT_TRIM: 800..1024, 672..800)
    tx0, ty0, tx1, ty1 = vs.RECT_TRIM
    th, tw = ty1 - ty0, tx1 - tx0
    ty_g, tx_g = np.mgrid[0:th, 0:tw]
    trim = 28.0 + 4.0 * ((tx_g // 4 + ty_g // 4) % 2) + rng.normal(0.0, 2.0, (th, tw))
    arr[ty0:ty1, tx0:tx1] = np.clip(trim[:, :, None], 16, 48).astype(np.uint8)

    # 4. Charred Wreck Metal (RECT_WRECK: 512..768, 800..1024)
    wx0, wy0, wx1, wy1 = vs.RECT_WRECK
    wh, ww = wy1 - wy0, wx1 - wx0
    wy_g, wx_g = np.mgrid[0:wh, 0:ww]
    rust = np.maximum(0.0, np.sin(wx_g * 0.06 + wy_g * 0.04) * np.cos(wy_g * 0.08 - wx_g * 0.03))
    soot = 26.0 + rng.normal(0.0, 7.5, (wh, ww))
    wreck = np.zeros((wh, ww, 3), dtype=np.float32)
    wreck[:, :, 0] = np.clip(soot + rust * 52.0, 12, 126)
    wreck[:, :, 1] = np.clip(soot + rust * 22.0, 12, 88)
    wreck[:, :, 2] = np.clip(soot + rust * 10.0, 14, 72)
    arr[wy0:wy1, wx0:wx1] = wreck.astype(np.uint8)

    # 5. Hot Embers (RECT_EMBER: 768..1024, 800..1024)
    ex0, ey0, ex1, ey1 = vs.RECT_EMBER
    eh, ew = ey1 - ey0, ex1 - ex0
    ey_g, ex_g = np.mgrid[0:eh, 0:ew]
    vein = (0.5 + 0.5 * np.sin(ex_g * 0.08 + np.cos(ey_g * 0.07) * 2.5)) ** 2
    emb = np.zeros((eh, ew, 3), dtype=np.float32)
    emb[:, :, 0] = np.clip(72.0 + vein * 182.0, 0, 255)
    emb[:, :, 1] = np.clip(20.0 + (vein ** 1.6) * 160.0, 0, 255)
    emb[:, :, 2] = np.clip(8.0 + (vein ** 2.8) * 70.0, 0, 255)
    arr[ey0:ey1, ex0:ex1] = emb.astype(np.uint8)

    im.paste(Image.fromarray(arr[544:1024, 0:1024]), (0, 544))
    draw = ImageDraw.Draw(im)

    # Black ceramic frit border around glass swatch
    draw.rectangle([gx0 + 2, gy0 + 2, gx1 - 3, gy1 - 3], outline=(14, 18, 22), width=7)

    # 6. Detailed 3D Engine Bay Swatch (RECT_ENGINE: 0..256, 800..1024)
    en0, eny0, en1, eny1 = vs.RECT_ENGINE
    draw.rectangle([en0, eny0, en1, eny1], fill=(24, 26, 30))
    draw.rectangle([22, eny0 + 12, 234, eny0 + 36], fill=(46, 50, 56), outline=(92, 98, 108), width=2)
    draw.rounded_rectangle([66, eny0 + 52, 190, eny1 - 54], radius=7, fill=(138, 144, 154), outline=(68, 74, 82), width=3)
    for ry in range(eny0 + 66, eny1 - 62, 14):
        draw.line([(76, ry), (180, ry)], fill=(64, 68, 76), width=3)
    draw.rectangle([28, eny0 + 60, 60, eny1 - 58], fill=(54, 60, 68), outline=(112, 118, 128), width=2)
    draw.rectangle([196, eny0 + 60, 228, eny1 - 58], fill=(54, 60, 68), outline=(112, 118, 128), width=2)
    draw.rectangle([22, eny1 - 46, 78, eny1 - 10], fill=(20, 22, 26), outline=(72, 76, 84), width=2)
    draw.rectangle([62, eny1 - 40, 72, eny1 - 30], fill=(214, 34, 34))
    draw.ellipse([188, eny1 - 46, 226, eny1 - 10], fill=(218, 188, 56), outline=(96, 84, 28), width=2)

    # 7. Rich Walk-in Cargo Van & Vehicle Cabin Interior (RECT_INTERIOR: 256..512, 800..1024)
    # Sub-region A: Ribbed Galvanized/White Metal Cargo Floor (RECT_INT_FLOOR: 256..384, 800..912)
    fx0, fy0, fx1, fy1 = vs.RECT_INT_FLOOR
    draw.rectangle([fx0, fy0, fx1, fy1], fill=(222, 226, 232))
    # Longitudinal stamped anti-skid ribs running the length
    for rx in range(fx0 + 8, fx1 - 6, 12):
        draw.line([(rx, fy0 + 2), (rx, fy1 - 2)], fill=(250, 252, 255), width=2)
        draw.line([(rx + 2, fy0 + 2), (rx + 2, fy1 - 2)], fill=(168, 174, 184), width=2)
    # Stamped circular dimples & D-ring tie down brackets
    for dy in range(fy0 + 16, fy1 - 10, 28):
        for dx in (fx0 + 12, fx0 + 64, fx1 - 14):
            draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=(188, 194, 202), outline=(130, 136, 146), width=1)
            draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(120, 126, 136))

    # Sub-region B: Full Dashboard Console, Gauges, Stereo & A/C (RECT_INT_DASH: 384..512, 800..912)
    dx0, dy0, dx1, dy1 = vs.RECT_INT_DASH
    draw.rectangle([dx0, dy0, dx1, dy1], fill=(36, 39, 44))
    # Instrument cluster binnacle
    draw.rounded_rectangle([dx0 + 6, dy0 + 8, dx0 + 58, dy0 + 52], radius=4, fill=(20, 22, 26), outline=(62, 66, 74), width=2)
    # Speedometer gauge
    draw.ellipse([dx0 + 10, dy0 + 12, dx0 + 32, dy0 + 34], fill=(16, 18, 22), outline=(190, 196, 206), width=1)
    draw.line([(dx0 + 21, dy0 + 23), (dx0 + 27, dy0 + 17)], fill=(238, 48, 48), width=2) # red needle
    # Tachometer gauge
    draw.ellipse([dx0 + 34, dy0 + 12, dx0 + 54, dy0 + 32], fill=(16, 18, 22), outline=(190, 196, 206), width=1)
    draw.line([(dx0 + 44, dy0 + 22), (dx0 + 49, dy0 + 17)], fill=(238, 48, 48), width=2)
    # Odometer LCD
    draw.rectangle([dx0 + 18, dy0 + 38, dx0 + 44, dy0 + 46], fill=(42, 68, 56), outline=(24, 38, 30))
    # Center stack: A/C vents, Stereo & Climate controls
    draw.rounded_rectangle([dx0 + 64, dy0 + 6, dx1 - 8, dy0 + 80], radius=3, fill=(28, 30, 34), outline=(52, 56, 62), width=1)
    # Dual rectangular A/C vents
    for vx in (dx0 + 68, dx0 + 94):
        draw.rectangle([vx, dy0 + 10, vx + 22, dy0 + 24], fill=(18, 20, 24), outline=(48, 52, 58))
        for vy in range(dy0 + 13, dy0 + 23, 3):
            draw.line([(vx + 2, vy), (vx + 20, vy)], fill=(44, 48, 54), width=1)
    # Stereo head unit
    draw.rectangle([dx0 + 68, dy0 + 28, dx1 - 12, dy0 + 48], fill=(16, 17, 20), outline=(68, 72, 80))
    draw.rectangle([dx0 + 72, dy0 + 32, dx0 + 102, dy0 + 40], fill=(22, 44, 58)) # LCD screen
    draw.ellipse([dx1 - 22, dy0 + 33, dx1 - 14, dy0 + 41], fill=(50, 54, 60), outline=(90, 96, 104)) # volume knob
    # Climate control dials
    for cx in (dx0 + 74, dx0 + 94, dx1 - 20):
        draw.ellipse([cx - 5, dy0 + 54, cx + 5, dy0 + 64], fill=(36, 40, 46), outline=(96, 102, 112))
        draw.line([(cx, dy0 + 55), (cx, dy0 + 59)], fill=(220, 224, 230), width=1)
    # Hazard triangle button
    draw.polygon([(dx0 + 89, dy0 + 68), (dx0 + 85, dy0 + 75), (dx0 + 93, dy0 + 75)], fill=(210, 36, 36))
    # Glove box door on passenger side
    draw.rounded_rectangle([dx0 + 8, dy0 + 58, dx0 + 58, dy1 - 8], radius=3, fill=(32, 35, 40), outline=(48, 52, 58))
    draw.rectangle([dx0 + 28, dy0 + 62, dx0 + 38, dy0 + 66], fill=(58, 62, 70)) # handle

    # Sub-region C: High-Back Bucket Seat Upholstery (RECT_INT_SEAT: 256..384, 912..1024)
    sx0, sy0, sx1, sy1 = vs.RECT_INT_SEAT
    draw.rectangle([sx0, sy0, sx1, sy1], fill=(42, 46, 54))
    # Vertical fluted double-stitch seam lines
    for st_x in range(sx0 + 12, sx1 - 10, 16):
        draw.line([(st_x, sy0 + 6), (st_x, sy1 - 6)], fill=(28, 30, 36), width=3)
        draw.line([(st_x + 1, sy0 + 6), (st_x + 1, sy1 - 6)], fill=(68, 74, 84), width=1)
    # Bolster outer edges
    draw.rounded_rectangle([sx0 + 4, sy0 + 4, sx1 - 4, sy1 - 4], radius=6, outline=(24, 26, 32), width=3)

    # Sub-region D: Two-Tone Cargo Walls, Stamped Ribs & Inner Doors (RECT_INT_WALL: 384..512, 912..1024)
    wx0, wy0, wx1, wy1 = vs.RECT_INT_WALL
    w_mid_y = wy0 + 48
    # Lower dark protective kick panel
    draw.rectangle([wx0, w_mid_y, wx1, wy1], fill=(40, 44, 50))
    for fy in range(w_mid_y + 12, wy1 - 8, 20):
        for fx in range(wx0 + 16, wx1 - 10, 24):
            draw.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(22, 24, 28)) # fastener plugs
    # Upper stamped sheet metal
    draw.rectangle([wx0, wy0, wx1, w_mid_y], fill=(228, 232, 238))
    # Vertical structural hat channels / upright ribs
    for hx in range(wx0 + 14, wx1 - 10, 24):
        draw.line([(hx, wy0 + 4), (hx, w_mid_y - 4)], fill=(252, 254, 255), width=2)
        draw.line([(hx + 2, wy0 + 4), (hx + 2, w_mid_y - 4)], fill=(172, 178, 188), width=2)
        draw.rounded_rectangle([hx - 4, wy0 + 10, hx + 6, wy0 + 38], radius=2, outline=(186, 192, 202))
    # Horizontal tie-down track
    draw.rectangle([wx0 + 4, w_mid_y - 8, wx1 - 4, w_mid_y + 4], fill=(160, 166, 176), outline=(98, 104, 114))

    glow_draw.rectangle([ex0 + 4, ey0 + 4, ex1 - 4, ey1 - 4], fill=(210, 92, 20))


def make_burn_variant(intact_im, intact_glow, sp, seed=101):
    """Creates skin 1 (Catching Fire): scorched/blistered hood & front fenders, spiderweb-cracked
    safety glass, and glowing engine-bay + narrow grille-slot flames!"""
    rng = np.random.default_rng(seed)
    arr = np.array(intact_im, dtype=np.float32)

    px_cowl, _ = vs.side_world_to_px(sp, sp["x_cowl"], 0.0)
    yy, xx = np.mgrid[0:H, 0:W]
    hood_side = np.clip((xx - (px_cowl - 20.0)) / max(40.0, 624.0 - px_cowl), 0.0, 1.0) * (yy < 288).astype(np.float32)
    hood_top = np.clip((xx - (px_cowl - 20.0)) / max(40.0, 624.0 - px_cowl), 0.0, 1.0) * ((yy >= 288) & (yy < 544)).astype(np.float32)
    front_scorch = ((xx >= 640) & (yy < 272)).astype(np.float32) * 0.58

    noise = 0.55 + 0.45 * np.sin(xx * 0.05 + rng.normal(0, 0.35, (H, W))) * np.cos(yy * 0.06)
    scorch = np.clip((hood_side * 0.85 + hood_top * 0.88 + front_scorch) * noise, 0.0, 0.90)
    char_rgb = np.array([24.0, 20.0, 18.0], dtype=np.float32)
    arr = arr * (1.0 - scorch[:, :, None]) + char_rgb[None, None, :] * scorch[:, :, None]

    body_mask = (yy < 544).astype(np.float32) * 0.18
    arr = arr * (1.0 - body_mask[:, :, None]) + np.array([32.0, 26.0, 22.0])[None, None, :] * body_mask[:, :, None]

    burn_im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    bdraw = ImageDraw.Draw(burn_im)
    burn_glow = intact_glow.copy()
    gdraw = ImageDraw.Draw(burn_glow)

    # Glowing fire bed inside recessed 3D engine bay (RECT_ENGINE)
    en0, eny0, en1, eny1 = vs.RECT_ENGINE
    for ey in range(eny0 + 18, eny1 - 18, 20):
        bdraw.rounded_rectangle([24, ey, 232, ey + 9], radius=4, fill=(238, 102, 20))
        gdraw.rounded_rectangle([28, ey + 2, 228, ey + 7], radius=3, fill=(185, 68, 12))
    bdraw.rounded_rectangle([66, eny0 + 52, 190, eny1 - 54], radius=7, fill=(42, 40, 44), outline=(180, 74, 18), width=2)
    gdraw.rounded_rectangle([66, eny0 + 52, 190, eny1 - 54], radius=7, fill=(22, 8, 4))

    # Narrow glowing orange radiator slots strictly inside front grille center!
    hw = sp["hw"]
    zbmp = sp["z_bot"] + (8.2 if sp["kind"] == "coupe" else 10.2)
    gx0, gy0 = vs.front_world_to_px(sp, hw * 0.34, sp["z_nose_top"] - 4.0)
    gx1, gy1 = vs.front_world_to_px(sp, -hw * 0.34, zbmp + 3.0)
    xa, xb = min(gx0, gx1), max(gx0, gx1)
    ya, yb = min(gy0, gy1), max(gy0, gy1)
    for gy in range(int(ya) + 6, int(yb) - 4, 14):
        bdraw.line([(xa, gy), (xb, gy)], fill=(215, 86, 18), width=2)
        gdraw.line([(xa + 4, gy), (xb - 4, gy)], fill=(140, 50, 10), width=2)
        bdraw.line([(xa - 2, gy + 3), (xb + 2, gy + 3)], fill=(22, 24, 28), width=3)

    # Spiderweb safety-glass cracks in RECT_GLASS
    gl0, gly0, gl1, gly1 = vs.RECT_GLASS
    for cx, cy in ((gl0 + 92, gly0 + 86), (gl0 + 198, gly0 + 128)):
        for k in range(14):
            a = 2 * math.pi * k / 14 + 0.17 * (k % 3)
            r = 52 + (k % 4) * 13
            bdraw.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=(192, 206, 220), width=2)
        for rr in (18, 36, 52):
            bdraw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(162, 178, 194), width=1)

    return burn_im, burn_glow


def build_vehicle_textures(kind):
    sp = vs.get_spec(kind)
    pal = PALETTES[kind]
    rng = np.random.default_rng({"truck": 11, "sedan": 22, "van": 33, "coupe": 44}[kind])

    im = Image.new("RGB", (W, H), (26, 28, 32))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    glow_draw = ImageDraw.Draw(glow)

    _paint_side_profile(im, draw, glow_draw, sp, pal, rng)
    _paint_top_plan(im, sp, pal, rng)
    _paint_front_and_rear(im, glow_draw, sp, pal)
    _paint_wheel_and_tread(im, sp)
    _paint_shared_swatches(im, glow_draw, rng)

    glow = glow.filter(ImageFilter.GaussianBlur(radius=2.0))
    burn_im, burn_glow = make_burn_variant(im, glow, sp, seed=100 + len(kind))
    burn_glow = burn_glow.filter(ImageFilter.GaussianBlur(radius=2.2))
    return im, glow, burn_im, burn_glow


def save_darkplaces_textures(out_progs_dir, preview_dir=None, dp_gain=0.60):
    os.makedirs(out_progs_dir, exist_ok=True)
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)

    atlases = {}
    for kind in ("truck", "sedan", "van", "coupe"):
        if kind == "van":
            import promaster_van_tex
            im, glow, burn_im, burn_glow, glass_rgba, glass_burn = promaster_van_tex.build_promaster_van_textures()
            atlases[kind] = {
                "intact": im,
                "glow": glow,
                "burn": burn_im,
                "burn_glow": burn_glow,
                "glass": glass_rgba,
                "glass_burn": glass_burn,
            }
            for g_im, g_name in ((glass_rgba, "veh_van_glass.png"), (glass_burn, "veh_van_glass_burn.png")):
                r, g, b, a = g_im.split()
                rgb_tm = ImageEnhance.Brightness(Image.merge("RGB", (r, g, b))).enhance(dp_gain)
                rt, gt, bt = rgb_tm.split()
                Image.merge("RGBA", (rt, gt, bt, a)).save(os.path.join(out_progs_dir, g_name), "PNG", optimize=True)
            if preview_dir:
                im.save(os.path.join(preview_dir, "veh_van_atlas_2k.png"), "PNG")
                glass_rgba.save(os.path.join(preview_dir, "veh_van_glass.png"), "PNG")
        else:
            im, glow, burn_im, burn_glow = build_vehicle_textures(kind)
            atlases[kind] = {"intact": im, "glow": glow, "burn": burn_im, "burn_glow": burn_glow}

        ImageEnhance.Brightness(im).enhance(dp_gain).save(
            os.path.join(out_progs_dir, f"veh_{kind}_tex.png"), "PNG", optimize=True
        )
        ImageEnhance.Brightness(glow).enhance(0.55).save(
            os.path.join(out_progs_dir, f"veh_{kind}_tex_glow.png"), "PNG", optimize=True
        )
        ImageEnhance.Brightness(burn_im).enhance(dp_gain).save(
            os.path.join(out_progs_dir, f"veh_{kind}_burn.png"), "PNG", optimize=True
        )
        ImageEnhance.Brightness(burn_glow).enhance(0.75).save(
            os.path.join(out_progs_dir, f"veh_{kind}_burn_glow.png"), "PNG", optimize=True
        )
        if preview_dir:
            im.save(os.path.join(preview_dir, f"veh_{kind}_atlas.png"), "PNG")
            burn_im.save(os.path.join(preview_dir, f"veh_{kind}_burn_atlas.png"), "PNG")

    flash = Image.new("RGB", (64, 64), (255, 186, 62))
    flash.save(os.path.join(out_progs_dir, "veh_blast_flash.png"), "PNG")
    return atlases


if __name__ == "__main__":
    progs = os.path.abspath(os.path.join(HERE, "..", "..", "progs"))
    prev = os.path.join(HERE, "out", "vehicles")
    save_darkplaces_textures(progs, prev)
    print("Generated all 4 aligned vehicle texture atlases + burn variants + glow maps.")
