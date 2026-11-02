"""Shared Exact Dimensions, UV Projection Math & 1024x1024 Studio Texture / Burn / Glow
Generator for BakersfieldQuake's 3 NEW Wild-Explosion Realistic Vehicles:
  1. hdtruck   : Heavy-Duty Crew-Cab Diesel Dually Rig Truck (Flame-Crimson & Gunmetal, 6 Wheels)
  2. schoolbus : Full-Size Type-C Conventional Yellow School Bus (Chrome Yellow, 6 Wheels, STOP Sign)
  3. gtcar     : V8 Street Muscle Fastback Car (Liquid Gunmetal Metallic w/ Twin Racing Stripes)

Atlas Discipline:
  - vs.RECT_TRIM (800..1024, 672..800) is kept 100% pure satin-black/carbon trim (zero bleed!).
  - Dedicated isolated sub-rectangles inside (0..256, 800..1024) hold engine detail, the School Bus
    octagonal STOP sign / fender emblems, and right-reading side signage strips.
"""
import math
import os
import sys
import numpy as np
try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
except ImportError:
    Image = ImageDraw = ImageEnhance = ImageFilter = ImageFont = None

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs

W = vs.W_ATLAS
H = vs.H_ATLAS

WILD_KINDS = ("hdtruck", "schoolbus", "gtcar")

# Non-overlapping isolated sub-rects inside (0..256, 800..1024) with generous mipmap guard gutters!
RECT_WILD_ENGINE = (4, 804, 142, 954)    # 138x150 under-hood turbo-diesel / V8 engine block
RECT_BADGE_A     = (150, 804, 252, 906)  # 102x102 STOP sign (schoolbus) or front fender badge
RECT_STOP_SIGN   = RECT_BADGE_A
RECT_DECAL_STRIP = (4, 962, 252, 1020)   # 248x58 right-reading side lettering / bedside graphic


def get_wild_spec(kind):
    if kind == "hdtruck":
        # Realistic Heavy-Duty Crew-Cab Diesel Dually Work/Off-Road Rig Truck
        return dict(
            kind="hdtruck",
            x0=-126.0, x1=122.0, hw=44.5,
            z_bot=12.5, z_bmp=24.0, z_belt=48.5, z_roof=81.5,
            z_nose_top=46.0, z_rear_top=48.5,
            wheel_x_f=78.0, wheel_x_r=-70.0, wheel_y=39.5, wheel_r=18.0, wheel_w=12.2,
            dual_rear=True, wheel_y_inner=29.0,
            dish=3.4, rim_ratio=0.58, arch_r=22.8, flare=4.2,
            x_cowl=44.0, x_cab_rear=-28.0,
            x_door0=4.0, x_door1=41.0,
            x_roof0=-25.0, x_roof1=22.0, y_roof=34.5,
            x_bed_f=-30.0, x_bed_r=-121.0,
        )
    elif kind == "schoolbus":
        # Full-Size Type-C Conventional Nose American Yellow School Bus
        return dict(
            kind="schoolbus",
            x0=-176.0, x1=154.0, hw=46.5,
            z_bot=13.0, z_bmp=24.5, z_belt=54.0, z_roof=102.0,
            z_nose_top=49.5, z_rear_top=100.0,
            wheel_x_f=110.0, wheel_x_r=-92.0, wheel_y=40.5, wheel_r=17.5, wheel_w=11.0,
            dual_rear=True, wheel_y_inner=30.5,
            dish=2.6, rim_ratio=0.57, arch_r=22.0, flare=2.2,
            x_cowl=100.0, x_cab_rear=-172.0,
            x_door0=66.0, x_door1=96.0,
            x_roof0=-170.0, x_roof1=84.0, y_roof=41.5,
        )
    elif kind == "gtcar":
        # Realistic Modern-Classic V8 Street Muscle Fastback Car
        return dict(
            kind="gtcar",
            x0=-99.0, x1=99.0, hw=38.0,
            z_bot=6.8, z_bmp=16.2, z_belt=33.0, z_roof=52.0,
            z_nose_top=28.5, z_rear_top=35.5,
            wheel_x_f=58.5, wheel_x_r=-56.5, wheel_y=34.2, wheel_r=13.8, wheel_w=10.2,
            dual_rear=False, wheel_y_inner=24.0,
            dish=2.8, rim_ratio=0.67, arch_r=17.2, flare=2.4,
            x_cowl=30.0, x_cab_rear=-62.0,
            x_door0=-14.0, x_door1=27.0,
            x_roof0=-28.0, x_roof1=6.0, y_roof=28.2,
            x_trunk_f=-62.0, x_trunk_r=-96.0,
        )
    raise ValueError(f"Unknown wild vehicle kind: {kind}")


PALETTES = {
    "hdtruck": {
        "sky": (248, 92, 72),
        "hi": (214, 38, 28),
        "mid": (158, 20, 16),
        "lo": (88, 10, 11),
        "two_tone": (62, 68, 78),
        "plate": "7RIG550",
    },
    "schoolbus": {
        "sky": (255, 214, 62),
        "hi": (248, 180, 14),
        "mid": (224, 148, 6),
        "lo": (168, 104, 4),
        "two_tone": None,
        "plate": "SCHL042",
    },
    "gtcar": {
        "sky": (214, 224, 238),
        "hi": (156, 168, 186),
        "mid": (96, 108, 126),
        "lo": (46, 54, 66),
        "two_tone": None,
        "plate": "8V8GT99",
    },
}

_GLYPHS = {
    "0": [(0,0,1,0),(1,0,1,1),(1,1,0,1),(0,1,0,0)],
    "1": [(0.5,0,0.5,1),(0.2,0.2,0.5,0),(0.2,1,0.8,1)],
    "2": [(0,0,1,0),(1,0,1,0.5),(1,0.5,0,0.5),(0,0.5,0,1),(0,1,1,1)],
    "3": [(0,0,1,0),(1,0,1,1),(0,1,1,1),(0.1,0.5,1,0.5)],
    "4": [(0,0,0,0.55),(0,0.55,1,0.55),(0.8,0,0.8,1)],
    "5": [(1,0,0,0),(0,0,0,0.5),(0,0.5,1,0.5),(1,0.5,1,1),(1,1,0,1)],
    "6": [(1,0,0,0),(0,0,0,1),(0,1,1,1),(1,1,1,0.5),(1,0.5,0,0.5)],
    "7": [(0,0,1,0),(1,0,0.35,1)],
    "8": [(0,0,1,0),(1,0,1,1),(1,1,0,1),(0,1,0,0),(0,0.5,1,0.5)],
    "9": [(0,0.5,1,0.5),(1,0,0,0),(0,0,0,0.5),(1,0,1,1),(0,1,1,1)],
    "A": [(0,1,0,0.2),(0,0.2,0.5,0),(0.5,0,1,0.2),(1,0.2,1,1),(0,0.55,1,0.55)],
    "B": [(0,0,0,1),(0,0,0.8,0),(0.8,0,1,0.25),(1,0.25,0.8,0.5),(0,0.5,0.85,0.5),(0.85,0.5,1,0.75),(1,0.75,0.8,1),(0.8,1,0,1)],
    "C": [(1,0.15,0.8,0),(0.8,0,0.2,0),(0.2,0,0,0.2),(0,0.2,0,0.8),(0,0.8,0.2,1),(0.2,1,0.8,1),(0.8,1,1,0.85)],
    "D": [(0,0,0,1),(0,0,0.7,0),(0.7,0,1,0.25),(1,0.25,1,0.75),(1,0.75,0.7,1),(0.7,1,0,1)],
    "E": [(1,0,0,0),(0,0,0,1),(0,1,1,1),(0,0.5,0.8,0.5)],
    "F": [(1,0,0,0),(0,0,0,1),(0,0.5,0.8,0.5)],
    "G": [(1,0.15,0.8,0),(0.8,0,0.15,0),(0.15,0,0,0.2),(0,0.2,0,0.8),(0,0.8,0.15,1),(0.15,1,0.9,1),(0.9,1,1,0.55),(1,0.55,0.55,0.55)],
    "H": [(0,0,0,1),(1,0,1,1),(0,0.5,1,0.5)],
    "I": [(0.2,0,0.8,0),(0.5,0,0.5,1),(0.2,1,0.8,1)],
    "K": [(0,0,0,1),(1,0,0,0.5),(0,0.5,1,1)],
    "L": [(0,0,0,1),(0,1,1,1)],
    "M": [(0,1,0,0),(0,0,0.5,0.55),(0.5,0.55,1,0),(1,0,1,1)],
    "N": [(0,1,0,0),(0,0,1,1),(1,1,1,0)],
    "O": [(0.2,0,0.8,0),(0.8,0,1,0.2),(1,0.2,1,0.8),(1,0.8,0.8,1),(0.8,1,0.2,1),(0.2,1,0,0.8),(0,0.8,0,0.2),(0,0.2,0.2,0)],
    "P": [(0,1,0,0),(0,0,0.85,0),(0.85,0,1,0.25),(1,0.25,0.85,0.5),(0.85,0.5,0,0.5)],
    "R": [(0,1,0,0),(0,0,0.85,0),(0.85,0,1,0.25),(1,0.25,0.85,0.5),(0.85,0.5,0,0.5),(0.45,0.5,1,1)],
    "S": [(1,0.1,0.15,0),(0.15,0,0,0.25),(0,0.25,0.15,0.5),(0.15,0.5,0.85,0.5),(0.85,0.5,1,0.75),(1,0.75,0.85,1),(0.85,1,0,0.9)],
    "T": [(0,0,1,0),(0.5,0,0.5,1)],
    "U": [(0,0,0,0.8),(0,0.8,0.2,1),(0.2,1,0.8,1),(0.8,1,1,0.8),(1,0.8,1,0)],
    "V": [(0,0,0.5,1),(0.5,1,1,0)],
    "X": [(0,0,1,1),(1,0,0,1)],
    "Y": [(0,0,0.5,0.5),(1,0,0.5,0.5),(0.5,0.5,0.5,1)],
    " ": [],
    "-": [(0.15,0.5,0.85,0.5)],
    ".": [(0.4,0.85,0.6,1.0)],
}

_FONT_CACHE = {}


def _get_font(px_size, style="bold"):
    key = (px_size, style)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if ImageFont is None:
        return None
    candidates = {
        "impact": ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf"],
        "cond": ["C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/arialbd.ttf"],
        "bold": ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    }.get(style, ["C:/Windows/Fonts/arialbd.ttf"])
    for fp in candidates:
        if os.path.exists(fp):
            try:
                fnt = ImageFont.truetype(fp, px_size)
                _FONT_CACHE[key] = fnt
                return fnt
            except Exception:
                pass
    _FONT_CACHE[key] = None
    return None


def _draw_vector_text_fallback(draw, cx, cy, total_w, h, text, color=(18, 20, 24), width=2):
    if not text:
        return
    step = total_w / max(1, len(text))
    x_start = cx - total_w * 0.5
    y_top = cy - h * 0.5
    cw = step * 0.68
    for i, ch in enumerate(text.upper()):
        bx = x_start + i * step + (step - cw) * 0.5
        for ax, ay, ex, ey in _GLYPHS.get(ch, []):
            draw.line([(bx + ax * cw, y_top + ay * h), (bx + ex * cw, y_top + ey * h)], fill=color, width=width)


def _draw_crisp_text(im, cx, cy, max_w, target_h, text, color=(18, 20, 24), style="bold", outline=None, outline_w=0):
    """Renders supersampled anti-aliased TrueType automotive/DOT lettering fit cleanly inside (max_w, target_h)."""
    if not text:
        return
    fnt = _get_font(max(24, int(round(target_h * 2.6))), style=style)
    if fnt is None:
        _draw_vector_text_fallback(ImageDraw.Draw(im), cx, cy, max_w, target_h, text, color=color, width=2)
        return

    tmp_measure = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(tmp_measure)
    pad = max(4, outline_w * 3 + 4)
    bb = mdraw.textbbox((0, 0), text, font=fnt, stroke_width=outline_w * 2)
    tw = max(4, bb[2] - bb[0])
    th = max(4, bb[3] - bb[1])

    canvas = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(canvas)
    fill_rgba = (color[0], color[1], color[2], 255)
    if outline is not None and outline_w > 0:
        out_rgba = (outline[0], outline[1], outline[2], 255)
        cdraw.text((pad - bb[0], pad - bb[1]), text, font=fnt, fill=fill_rgba, stroke_width=outline_w * 2, stroke_fill=out_rgba)
    else:
        cdraw.text((pad - bb[0], pad - bb[1]), text, font=fnt, fill=fill_rgba)

    # Crop tight alpha bounds and scale smoothly to fit (max_w, target_h)
    abb = canvas.getbbox()
    if not abb:
        return
    cropped = canvas.crop(abb)
    cw, ch = cropped.size
    scale_y = target_h / max(1.0, float(ch))
    new_h = max(4, int(round(target_h)))
    new_w = max(4, int(round(min(max_w, cw * scale_y))))
    scaled = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    px = int(round(cx - new_w * 0.5))
    py = int(round(cy - new_h * 0.5))
    im.paste(scaled, (px, py), scaled)


def _draw_plate(im, draw, cx, cy, pw, ph, text):
    x0, y0 = int(round(cx - pw * 0.5)), int(round(cy - ph * 0.5))
    x1, y1 = int(round(cx + pw * 0.5)), int(round(cy + ph * 0.5))
    draw.rounded_rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], radius=4, fill=(18, 20, 24), outline=(72, 78, 88), width=1)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=3, fill=(242, 245, 250))
    # California red header script + registration sticker
    draw.line([(x0 + 9, y0 + 5), (x1 - 15, y0 + 5)], fill=(198, 30, 34), width=3)
    draw.rectangle([x1 - 12, y0 + 3, x1 - 5, y0 + 7], fill=(238, 174, 20))
    _draw_crisp_text(im, cx, cy + 3.5, pw - 8, max(10.0, ph - 12.0), text, color=(20, 48, 124), style="cond")


def _add_flake(arr_patch, rng, amp=2.8):
    h, w, _ = arr_patch.shape
    n = rng.normal(0.0, amp, (h, w, 1)).astype(np.float32)
    return np.clip(arr_patch.astype(np.float32) + n, 0, 255).astype(np.uint8)


def _side_row_color(y_i, py_belt, py_bot, sky, hi, mid, lo):
    """Smooth C1-continuous automotive clearcoat vertical reflection profile (no jump at py_belt!)."""
    if y_i <= py_belt:
        t = max(0.0, min(1.0, y_i / max(1.0, py_belt)))
        # Smooth sky -> upper shoulder highlight right down to beltline
        s = t * t * (3.0 - 2.0 * t)
        return sky * (0.88 - 0.16 * s) + hi * (0.12 + 0.16 * s)
    else:
        t = max(0.0, min(1.0, (y_i - py_belt) / max(1.0, py_bot - py_belt)))
        # At t=0: matches sky*0.72 + hi*0.28 seamlessly!
        c_top = sky * 0.72 + hi * 0.28
        if t < 0.18:
            u = t / 0.18
            s = u * u * (3.0 - 2.0 * u)
            c = c_top * (1.0 - s) + (sky * 0.42 + hi * 0.58) * s
        elif t < 0.60:
            u = (t - 0.18) / 0.42
            s = u * u * (3.0 - 2.0 * u)
            c = (sky * 0.42 + hi * 0.58) * (1.0 - s) + mid * s
        else:
            u = (t - 0.60) / 0.40
            s = u * u * (3.0 - 2.0 * u)
            c = mid * (1.0 - s) + lo * s
        # Subtle studio floor bounce highlight
        c = c + np.exp(-((t - 0.64) / 0.06) ** 2) * 16.0
        return np.clip(c, 0, 255)


def _paint_side(im, glow_draw, sp, pal, rng):
    """Paints RECT_SIDE with 100% clean paint, shutlines, handles, rub-rails & lights (ZERO mirrored text!)."""
    kind = sp["kind"]
    bw, bh = 640, 288
    arr = np.array(im)

    sky = np.array(pal["sky"], dtype=np.float32)
    hi = np.array(pal["hi"], dtype=np.float32)
    mid = np.array(pal["mid"], dtype=np.float32)
    lo = np.array(pal["lo"], dtype=np.float32)

    _, py_belt = vs.side_world_to_px(sp, 0.0, sp["z_belt"])
    _, py_bot = vs.side_world_to_px(sp, 0.0, sp["z_bot"])

    band = np.zeros((bh, bw, 3), dtype=np.float32)
    for y_i in range(bh):
        band[y_i, :, :] = _side_row_color(y_i, py_belt, py_bot, sky, hi, mid, lo)

    if pal["two_tone"] is not None:
        _, py_tt = vs.side_world_to_px(sp, 0.0, sp["z_bot"] + 12.0)
        y_cut = int(round(py_tt))
        tt = np.array(pal["two_tone"], dtype=np.float32)
        for y_i in range(y_cut, bh):
            u = min(1.0, (y_i - y_cut) / max(1.0, py_bot - y_cut))
            band[y_i, :, :] = tt * (1.08 - 0.28 * u)

    arr[0:bh, 0:bw] = _add_flake(band, rng, amp=1.8 if kind == "schoolbus" else 3.0)
    im.paste(Image.fromarray(arr[0:bh, 0:bw]), (0, 0))
    draw = ImageDraw.Draw(im)

    def P(wx, wz):
        return vs.side_world_to_px(sp, wx, wz)

    zb = sp["z_belt"]
    zbot = sp["z_bot"]
    zroof = sp["z_roof"]

    _, py_rk = P(0, zbot + 2.6)
    draw.rectangle([0, int(py_rk), bw, bh], fill=(20, 22, 26))

    def shutline_v(wx, za, zb_top):
        x_p, ya_p = P(wx, za)
        _, yb_p = P(wx, zb_top)
        y_lo, y_hi = min(ya_p, yb_p), max(ya_p, yb_p)
        draw.line([(x_p, y_lo), (x_p, y_hi)], fill=(14, 16, 20), width=3)
        draw.line([(x_p + 2, y_lo), (x_p + 2, y_hi)], fill=pal["sky"], width=1)

    if kind == "hdtruck":
        _, py_tt = P(0, zbot + 12.0)
        draw.line([(4, py_tt), (bw - 4, py_tt)], fill=(228, 234, 244), width=3)
        draw.line([(4, py_tt - 3), (bw - 4, py_tt - 3)], fill=(45, 12, 12), width=2)
        # Cab-to-bed gap + Crew-Cab front & rear doors
        xg0, yg0 = P(-29.0, zbot + 3.0)
        _, yg1 = P(-29.0, zb)
        draw.rectangle([xg0 - 3, yg1, xg0 + 3, yg0], fill=(10, 12, 16))
        shutline_v(sp["x_door0"], zbot + 3.0, zb)
        shutline_v(sp["x_door1"], zbot + 3.0, zb)
        shutline_v(-26.0, zbot + 3.0, zb)
        # Chrome pull handles on both crew-cab doors + diesel fuel doors
        for hx in (12.0, -18.0):
            x0p, y0p = P(hx - 5.2, zb - 5.0)
            x1p, y1p = P(hx + 5.2, zb - 9.0)
            ylo, yhi = min(y0p, y1p), max(y0p, y1p)
            draw.rounded_rectangle([x0p, ylo, x1p, yhi], radius=3, fill=(18, 20, 26), outline=pal["lo"], width=1)
            ym = 0.5 * (ylo + yhi)
            draw.rounded_rectangle([x0p + 2, ym - 2.2, x1p - 2, ym + 2.2], radius=2, fill=(224, 230, 240))
        fx0, fy0 = P(-45.0, zb - 9.5)
        fx1, fy1 = P(-37.5, zb - 15.5)
        draw.rounded_rectangle([fx0, min(fy0, fy1), fx1, max(fy0, fy1)], radius=3, outline=(36, 12, 14), width=2)
        # Glowing amber dually fender clearance markers + front amber side marker
        for mx, mz, col_m in ((-50.0, zbot + 16.5, (255, 168, 24)), (-90.0, zbot + 16.5, (238, 34, 34)), (108.0, zbot + 18.0, (255, 168, 24))):
            mx0, my0 = P(mx, mz)
            draw.rounded_rectangle([mx0 - 5, my0 - 3, mx0 + 5, my0 + 3], radius=2, fill=col_m, outline=(24, 18, 14))
            glow_draw.rounded_rectangle([mx0 - 4, my0 - 2, mx0 + 4, my0 + 2], radius=2, fill=col_m)

    elif kind == "schoolbus":
        # 4 classic matte-black corrugated steel rub rails along the bus body!
        x_body_r, _ = P(-173.0, zb)
        x_body_f, _ = P(98.0, zb)
        for rz in (zb - 1.5, zb - 13.5, zb - 26.5, zbot + 4.5):
            _, ry = P(0.0, rz)
            draw.rectangle([x_body_r, ry - 3.5, x_body_f, ry + 3.5], fill=(20, 22, 26))
            draw.line([(x_body_r, ry - 1.5), (x_body_f, ry - 1.5)], fill=(70, 76, 86), width=1)
        # Upper letterboard rivet seam & yellow reflective DOT perimeter stripe
        _, py_hdr = P(0.0, zroof - 6.5)
        draw.line([(x_body_r, py_hdr), (x_body_f, py_hdr)], fill=(176, 114, 8), width=2)
        # Hood engine side louver vents placed cleanly ABOVE front wheel arch (z = 38..47)
        vx0, vy0 = P(114.0, 46.5)
        vx1, vy1 = P(138.0, 38.5)
        for lx in np.linspace(vx0, vx1, 7):
            draw.line([(lx, vy0), (lx - 2, vy1)], fill=(32, 26, 14), width=2)
            draw.line([(lx + 2, vy0), (lx, vy1)], fill=(255, 212, 68), width=1)
        # Side amber & red clearance / reflector lamps
        for mx, col_m in ((88.0, (255, 172, 24)), (-12.0, (255, 172, 24)), (-164.0, (235, 36, 36))):
            px_m, py_m = P(mx, zroof - 5.0)
            draw.ellipse([px_m - 4, py_m - 3, px_m + 4, py_m + 3], fill=col_m, outline=(22, 22, 24))
            glow_draw.ellipse([px_m - 3, py_m - 2, px_m + 3, py_m + 2], fill=col_m)
        # Side amber turn repeater behind front wheel
        tx_m, ty_m = P(93.0, zb - 19.5)
        draw.rounded_rectangle([tx_m - 5, ty_m - 3, tx_m + 5, ty_m + 3], radius=2, fill=(255, 168, 20), outline=(22, 22, 24))
        glow_draw.rounded_rectangle([tx_m - 4, ty_m - 2, tx_m + 4, ty_m + 2], radius=2, fill=(255, 164, 18))
        shutline_v(sp["x_door0"], zbot + 2.0, zroof - 10.0)
        shutline_v(sp["x_door1"], zbot + 2.0, zroof - 10.0)

    elif kind == "gtcar":
        # Sleek carbon lower side-skirt splitter + crimson accent spear
        _, ys0 = P(0.0, zbot + 4.8)
        draw.rectangle([12, int(ys0), bw - 12, bh], fill=(22, 25, 30))
        draw.line([(18, int(ys0)), (bw - 18, int(ys0))], fill=(224, 48, 38), width=2)
        # Sharp upper shoulder crease highlight
        _, yc0 = P(0.0, zb - 4.0)
        draw.line([(16, yc0), (bw - 16, yc0)], fill=(232, 240, 250), width=2)
        draw.line([(16, yc0 + 2), (bw - 16, yc0 + 2)], fill=(54, 62, 76), width=2)
        shutline_v(sp["x_door0"], zbot + 4.5, zb)
        shutline_v(sp["x_door1"], zbot + 4.5, zb)
        # Flush aero door handle + front fender shark-gill extractor vent (no mirrored text here!)
        hx0, hy0 = P(-5.0, zb - 6.0)
        hx1, hy1 = P(6.0, zb - 8.6)
        draw.rounded_rectangle([hx0, min(hy0, hy1), hx1, max(hy0, hy1)], radius=2, fill=(28, 32, 40), outline=(198, 208, 224), width=1)
        gx0, gy0 = P(31.0, zb - 7.5)
        gx1, gy1 = P(39.0, zb - 18.0)
        draw.polygon([(gx0, gy0), (gx1, gy0 + 2), (gx1 - 3, gy1), (gx0 - 3, gy1 - 2)], fill=(18, 22, 28), outline=(68, 76, 90))
        # Glowing LED side markers
        fx_m, fy_m = P(78.0, zbot + 8.5)
        rx_m, ry_m = P(-80.0, zbot + 9.5)
        draw.rectangle([fx_m - 6, fy_m - 2, fx_m + 6, fy_m + 2], fill=(255, 166, 24))
        glow_draw.rectangle([fx_m - 6, fy_m - 2, fx_m + 6, fy_m + 2], fill=(255, 166, 24))
        draw.rectangle([rx_m - 6, ry_m - 2, rx_m + 6, ry_m + 2], fill=(242, 34, 38))
        glow_draw.rectangle([rx_m - 6, ry_m - 2, rx_m + 6, ry_m + 2], fill=(242, 34, 38))

    # Wheel well arches in side atlas
    for wx in (sp["wheel_x_f"], sp["wheel_x_r"]):
        px_l, _ = P(wx - sp["arch_r"] * 1.03, zbot)
        px_r, _ = P(wx + sp["arch_r"] * 1.03, zbot)
        _, py_top = P(wx, zbot + sp["arch_r"] * 0.88)
        _, py_b = P(wx, zbot)
        x_lo, x_hi = min(px_l, px_r), max(px_l, px_r)
        dh = max(12.0, py_b - py_top)
        draw.pieslice([x_lo - 5, py_top - 5, x_hi + 5, py_top + dh * 2.0 + 5], 180, 360, fill=(28, 32, 38))
        draw.pieslice([x_lo, py_top, x_hi, py_top + dh * 2.0], 180, 360, fill=(10, 12, 15))


def _paint_top(im, glow_draw, sp, pal, rng):
    kind = sp["kind"]
    x0_b, y0_b, x1_b, y1_b = 0, 290, 640, 542
    bw, bh = x1_b - x0_b, y1_b - y0_b

    arr = np.array(im)
    ys = np.linspace(-1.0, 1.0, bh, dtype=np.float32)[:, None]
    crown = 1.0 - (ys ** 2) * 0.50
    hi = np.array(pal["sky"], dtype=np.float32)
    mid = np.array(pal["hi"], dtype=np.float32)
    patch = mid[None, None, :] * (1.0 - crown[:, :, None] * 0.45) + hi[None, None, :] * (crown[:, :, None] * 0.45)
    arr[y0_b:y1_b, x0_b:x1_b] = _add_flake(patch, rng, amp=2.4)
    im.paste(Image.fromarray(arr[y0_b:y1_b, x0_b:x1_b]), (x0_b, y0_b))
    draw = ImageDraw.Draw(im)

    def T(wx, wy):
        return vs.top_world_to_px(sp, wx, wy)

    hw = sp["hw"]

    if kind == "hdtruck":
        # Sprayed dark Rhino bedliner + ribs + diamond-plate auxiliary diesel tank
        bx0, by0 = T(sp["x_bed_r"], -hw * 0.80)
        bx1, by1 = T(sp["x_bed_f"], hw * 0.80)
        draw.rectangle([bx0, by0, bx1, by1], fill=(24, 27, 32), outline=(14, 16, 20), width=2)
        for ry in np.linspace(by0 + 7, by1 - 7, 13):
            draw.line([(bx0 + 4, ry), (bx1 - 4, ry)], fill=(40, 44, 52), width=2)
        tx0, ty0 = T(-48.0, -hw * 0.78)
        tx1, ty1 = T(-31.0, hw * 0.78)
        draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=3, fill=(198, 206, 218), outline=(92, 100, 112), width=2)
        for dx_d in range(int(tx0) + 6, int(tx1) - 4, 8):
            for dy_d in range(int(ty0) + 6, int(ty1) - 4, 8):
                draw.line([(dx_d - 2, dy_d), (dx_d + 2, dy_d)], fill=(232, 238, 246), width=1)
        # Power-dome diesel hood contours + matte-black heat louvers
        hx0, hy0 = T(sp["x_cowl"] + 6.0, -18.0)
        hx1, hy1 = T(sp["x1"] - 14.0, 18.0)
        draw.rounded_rectangle([hx0, hy0, hx1, hy1], radius=6, outline=pal["lo"], width=2)
        for vy_s in (-13.0, 13.0):
            vx0, vy_p = T(sp["x_cowl"] + 10.0, vy_s)
            vx1, _ = T(sp["x_cowl"] + 26.0, vy_s)
            draw.rounded_rectangle([vx0, vy_p - 5, vx1, vy_p + 5], radius=2, fill=(20, 22, 26), outline=(52, 56, 64))
        # 5 glowing amber cab roof clearance lights!
        for ly in (-22.0, -11.0, 0.0, 11.0, 22.0):
            lx_p, ly_p = T(sp["x_roof1"] - 3.5, ly)
            draw.rounded_rectangle([lx_p - 4, ly_p - 3, lx_p + 4, ly_p + 3], radius=2, fill=(255, 174, 24), outline=(30, 24, 12))
            glow_draw.rounded_rectangle([lx_p - 4, ly_p - 3, lx_p + 4, ly_p + 3], radius=2, fill=(255, 168, 20))

    elif kind == "schoolbus":
        # Authentic California white heat-reflective center roof sheet + ribs + 2 escape hatches!
        rx_a, ry_a = T(-164.0, -hw * 0.74)
        rx_b, ry_b = T(76.0, hw * 0.74)
        draw.rounded_rectangle([rx_a, ry_a, rx_b, ry_b], radius=6, fill=(240, 243, 248), outline=(182, 128, 10), width=2)
        for rib_x in np.linspace(rx_a + 14, rx_b - 14, 11):
            draw.line([(rib_x, ry_a + 3), (rib_x, ry_b - 3)], fill=(210, 216, 226), width=2)
        # 2 Roof Emergency Escape Hatches (crisp white cover + dark gasket + red latch bar)
        for hx_w in (-105.0, -15.0):
            ha0, hb0 = T(hx_w - 13.0, -13.0)
            ha1, hb1 = T(hx_w + 13.0, 13.0)
            draw.rounded_rectangle([ha0, hb0, ha1, hb1], radius=3, fill=(248, 250, 253), outline=(42, 46, 54), width=2)
            draw.rounded_rectangle([ha0 + 5, hb0 + 5, ha1 - 5, hb1 - 5], radius=2, outline=(176, 184, 196), width=1)
            mcx, mcy = 0.5 * (ha0 + ha1), 0.5 * (hb0 + hb1)
            draw.line([(mcx - 5, mcy), (mcx + 5, mcy)], fill=(208, 34, 32), width=3)
        # Matte-black anti-glare fiberglass hood center strip
        nh0, ny0 = T(103.0, -16.5)
        nh1, ny1 = T(148.0, 16.5)
        draw.rounded_rectangle([nh0, ny0, nh1, ny1], radius=4, fill=(28, 30, 35), outline=(52, 56, 64), width=1)

    elif kind == "gtcar":
        # Twin Wide Satin-Carbon Racing Stripes + Crisp Silver/Crimson Pin-Stripes Nose-to-Tail!
        sx0, _ = T(sp["x0"], 0.0)
        sx1, _ = T(sp["x1"], 0.0)
        for sgn in (-1.0, 1.0):
            _, sy_a = T(0.0, sgn * 3.0)
            _, sy_b = T(0.0, sgn * 12.2)
            ylo, yhi = min(sy_a, sy_b), max(sy_a, sy_b)
            draw.rectangle([sx0 - 6, ylo, sx1 + 6, yhi], fill=(22, 25, 31))
            draw.line([(sx0 - 6, ylo - 2), (sx1 + 6, ylo - 2)], fill=(214, 42, 36), width=2)
            draw.line([(sx0 - 6, yhi + 2), (sx1 + 6, yhi + 2)], fill=(214, 42, 36), width=2)
        # Twin Hood Honeycomb Heat-Extractor Scoops
        for sgn in (-1.0, 1.0):
            vx0, vy0 = T(52.0, sgn * 7.6 - 3.4)
            vx1, vy1 = T(76.0, sgn * 7.6 + 3.4)
            vylo, vyhi = min(vy0, vy1), max(vy0, vy1)
            draw.rounded_rectangle([vx0, vylo, vx1, vyhi], radius=2, fill=(12, 14, 18), outline=(74, 82, 96), width=1)
            for lx_v in np.linspace(vx0 + 4, vx1 - 4, 5):
                draw.line([(lx_v, vylo + 2), (lx_v, vyhi - 2)], fill=(38, 44, 52), width=1)


def _paint_front_and_rear(im, glow_draw, sp, pal, rng):
    kind = sp["kind"]
    hw = sp["hw"]
    zbot = sp["z_bot"]
    zbmp = sp["z_bmp"]

    for (x0_b, y0_b, x1_b, y1_b) in ((642, 0, 1024, 272), (642, 274, 1024, 544)):
        bw, bh = x1_b - x0_b, y1_b - y0_b
        arr = np.array(im)
        t = np.linspace(0.0, 1.0, bh, dtype=np.float32)[:, None]
        hi = np.array(pal["hi"], dtype=np.float32)
        lo = np.array(pal["lo"], dtype=np.float32)
        patch = hi[None, None, :] * (1.0 - t[:, :, None] * 0.62) + lo[None, None, :] * (t[:, :, None] * 0.62)
        arr[y0_b:y1_b, x0_b:x1_b] = _add_flake(patch, rng, amp=2.6)
        im.paste(Image.fromarray(arr[y0_b:y1_b, x0_b:x1_b]), (x0_b, y0_b))

    draw = ImageDraw.Draw(im)

    def F(wy, wz):
        return vs.front_world_to_px(sp, wy, wz)

    def R(wy, wz):
        return vs.rear_world_to_px(sp, wy, wz)

    # ---------------- FRONT FASCIA ----------------
    _, fy_bmp = F(0, zbmp)
    if kind == "hdtruck":
        draw.rectangle([642, int(fy_bmp), 1024, 272], fill=(44, 48, 56))
        draw.line([(642, int(fy_bmp)), (1024, int(fy_bmp))], fill=(218, 226, 238), width=3)
        # Massive Chrome Billet Grille + dark mesh + bold center RIG badge
        gx0, gy0 = F(-hw * 0.55, sp["z_nose_top"] - 2.0)
        gx1, gy1 = F(hw * 0.55, zbmp + 2.5)
        draw.rounded_rectangle([gx0 - 6, gy0 - 4, gx1 + 6, gy1 + 4], radius=7, fill=(220, 228, 240), outline=(92, 102, 118), width=3)
        draw.rounded_rectangle([gx0, gy0, gx1, gy1], radius=5, fill=(16, 18, 24))
        for yb in np.linspace(gy0 + 9, gy1 - 9, 4):
            draw.rectangle([gx0 + 4, yb - 4, gx1 - 4, yb + 4], fill=(208, 216, 230), outline=(112, 120, 136), width=1)
        cx, cy = 0.5 * (gx0 + gx1), 0.5 * (gy0 + gy1)
        draw.rounded_rectangle([cx - 30, cy - 11, cx + 30, cy + 11], radius=4, fill=(184, 22, 20), outline=(238, 242, 248), width=2)
        _draw_crisp_text(im, cx, cy, 48, 15, "RIG", color=(252, 250, 246), style="impact")
        draw = ImageDraw.Draw(im)
        # Quad Stacked Heavy-Duty LED Headlights + Amber C-DRLs
        for sgn in (-1.0, 1.0):
            ya, yb_h = sorted([F(sgn * hw * 0.59, 0)[0], F(sgn * hw * 0.93, 0)[0]])
            _, hy0 = F(0, sp["z_nose_top"] - 2.5)
            _, hy1 = F(0, zbmp + 3.0)
            draw.rounded_rectangle([ya, hy0, yb_h, hy1], radius=5, fill=(22, 26, 32), outline=(184, 194, 210), width=2)
            ym = 0.5 * (hy0 + hy1)
            for (lya, lyb) in ((hy0 + 4, ym - 2), (ym + 2, hy1 - 4)):
                draw.rounded_rectangle([ya + 5, lya, yb_h - 5, lyb], radius=3, fill=(226, 238, 255), outline=(112, 132, 162), width=1)
                pcx, pcy = 0.5 * (ya + yb_h), 0.5 * (lya + lyb)
                draw.ellipse([pcx - 7, pcy - 6, pcx + 7, pcy + 6], fill=(252, 254, 255), outline=(140, 164, 196), width=1)
                glow_draw.rounded_rectangle([ya + 6, lya + 1, yb_h - 6, lyb - 1], radius=2, fill=(200, 222, 255))
            ax_bar = ya + 3 if sgn < 0 else yb_h - 3
            draw.line([(ax_bar, hy0 + 3), (ax_bar, hy1 - 3)], fill=(255, 168, 22), width=4)
            glow_draw.line([(ax_bar, hy0 + 3), (ax_bar, hy1 - 3)], fill=(255, 168, 22), width=4)
        # Tow hook pockets + front plate
        for sgn in (-1.0, 1.0):
            thx, thy = F(sgn * hw * 0.42, zbot + 6.5)
            draw.rounded_rectangle([thx - 14, thy - 7, thx + 14, thy + 7], radius=3, fill=(16, 18, 22), outline=(82, 88, 98), width=1)
        px_c, py_c = F(0, zbot + 6.8)
        _draw_plate(im, draw, px_c, py_c, 78, 36, pal["plate"])
        draw = ImageDraw.Draw(im)

    elif kind == "schoolbus":
        # Heavy black steel front bumper
        draw.rectangle([642, int(fy_bmp), 1024, 272], fill=(22, 24, 28))
        draw.line([(642, int(fy_bmp)), (1024, int(fy_bmp))], fill=(58, 64, 74), width=2)
        # Slatted yellow & black conventional school bus radiator grille
        gx0, gy0 = F(-hw * 0.48, sp["z_nose_top"] - 4.0)
        gx1, gy1 = F(hw * 0.48, zbmp + 3.5)
        draw.rounded_rectangle([gx0, gy0, gx1, gy1], radius=6, fill=(18, 20, 24), outline=(168, 108, 6), width=3)
        for xv in np.linspace(gx0 + 9, gx1 - 9, 11):
            draw.line([(xv, gy0 + 5), (xv, gy1 - 5)], fill=(242, 172, 14), width=3)
        # Round sealed-beam fluted headlights in black bezels + round amber turn signals!
        for sgn in (-1.0, 1.0):
            hx_c, hy_c = F(sgn * hw * 0.74, zbmp + 10.8)
            draw.rounded_rectangle([hx_c - 24, hy_c - 19, hx_c + 24, hy_c + 19], radius=5, fill=(24, 26, 30), outline=(52, 56, 64), width=2)
            draw.ellipse([hx_c - 15, hy_c - 15, hx_c + 15, hy_c + 15], fill=(244, 248, 255), outline=(176, 188, 206), width=2)
            for fx_l in range(int(hx_c) - 10, int(hx_c) + 11, 5):
                draw.line([(fx_l, hy_c - 11), (fx_l, hy_c + 11)], fill=(202, 214, 232), width=1)
            glow_draw.ellipse([hx_c - 13, hy_c - 13, hx_c + 13, hy_c + 13], fill=(238, 234, 202))
            ax_c, ay_c = F(sgn * hw * 0.74, sp["z_nose_top"] - 6.0)
            draw.ellipse([ax_c - 11, ay_c - 10, ax_c + 11, ay_c + 10], fill=(255, 168, 18), outline=(24, 22, 18), width=2)
            glow_draw.ellipse([ax_c - 9, ay_c - 8, ax_c + 9, ay_c + 8], fill=(255, 162, 16))
        px_c, py_c = F(0, zbot + 6.5)
        _draw_plate(im, draw, px_c, py_c, 78, 36, pal["plate"])
        draw = ImageDraw.Draw(im)

    elif kind == "gtcar":
        # Twin satin-black racing stripes down front nose!
        for sgn in (-1.0, 1.0):
            sx_a, _ = F(sgn * 3.0, zbmp)
            sx_b, _ = F(sgn * 12.2, zbmp)
            xlo, xhi = min(sx_a, sx_b), max(sx_a, sx_b)
            draw.rectangle([xlo, 0, xhi, int(fy_bmp)], fill=(22, 25, 31))
            draw.line([(xlo - 2, 0), (xlo - 2, int(fy_bmp))], fill=(214, 42, 36), width=2)
            draw.line([(xhi + 2, 0), (xhi + 2, int(fy_bmp))], fill=(214, 42, 36), width=2)
        draw.rectangle([642, int(fy_bmp), 1024, 272], fill=(24, 28, 34))
        # Deep recessed black honeycomb grille + red GT grille badge
        gx0, gy0 = F(-hw * 0.52, sp["z_nose_top"] - 3.0)
        gx1, gy1 = F(hw * 0.52, zbmp + 2.2)
        draw.polygon([(gx0 + 6, gy0), (gx1 - 6, gy0), (gx1, gy1), (gx0, gy1)], fill=(12, 14, 18), outline=(82, 92, 108))
        for hx_g in range(int(gx0) + 12, int(gx1) - 10, 10):
            draw.line([(hx_g, gy0 + 4), (hx_g - 4, gy1 - 4)], fill=(30, 35, 44), width=1)
            draw.line([(hx_g - 4, gy0 + 4), (hx_g, gy1 - 4)], fill=(30, 35, 44), width=1)
        _draw_crisp_text(im, gx1 - 28, 0.5 * (gy0 + gy1), 28, 14, "GT", color=(234, 44, 38), style="impact")
        draw = ImageDraw.Draw(im)
        # Menacing Quad Halo LED Projectors + DRL fangs
        for sgn in (-1.0, 1.0):
            ya, yb_h = sorted([F(sgn * hw * 0.55, 0)[0], F(sgn * hw * 0.94, 0)[0]])
            _, hy0 = F(0, sp["z_nose_top"] - 2.6)
            _, hy1 = F(0, zbmp + 3.2)
            draw.rounded_rectangle([ya, hy0, yb_h, hy1], radius=5, fill=(16, 18, 24), outline=(72, 82, 98), width=2)
            ym = 0.5 * (hy0 + hy1)
            r_p = max(7, int(min((yb_h - ya) * 0.20, (hy1 - hy0) * 0.36)))
            for cx_p in (ya + (yb_h - ya) * 0.32, ya + (yb_h - ya) * 0.70):
                draw.ellipse([cx_p - r_p - 2, ym - r_p - 2, cx_p + r_p + 2, ym + r_p + 2], outline=(215, 236, 255), width=2)
                draw.ellipse([cx_p - r_p + 2, ym - r_p + 2, cx_p + r_p - 2, ym + r_p - 2], fill=(238, 246, 255))
                glow_draw.ellipse([cx_p - r_p - 1, ym - r_p - 1, cx_p + r_p + 1, ym + r_p + 1], fill=(195, 225, 255))
            # Inner angled white LED DRL fang
            fx_in = yb_h - 4 if sgn < 0 else ya + 4
            fx_sl = fx_in + (6 if sgn < 0 else -6)
            draw.line([(fx_in, hy0 + 4), (fx_sl, hy1 - 4)], fill=(235, 245, 255), width=3)
            glow_draw.line([(fx_in, hy0 + 4), (fx_sl, hy1 - 4)], fill=(210, 232, 255), width=3)
        lx0, ly0 = F(-hw * 0.62, zbmp - 2.2)
        lx1, ly1 = F(hw * 0.62, zbot + 1.8)
        draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=4, fill=(12, 14, 18), outline=(48, 54, 64))
        px_c, py_c = F(0, zbot + 5.2)
        _draw_plate(im, draw, px_c, py_c, 74, 34, pal["plate"])
        draw = ImageDraw.Draw(im)

    # ---------------- REAR FASCIA ----------------
    _, ry_bmp = R(0, zbmp)
    if kind == "hdtruck":
        draw.rectangle([642, int(ry_bmp), 1024, 544], fill=(192, 200, 212))
        draw.rectangle([642, int(ry_bmp), 1024, int(ry_bmp) + 6], fill=(32, 36, 42))
        # Stamped DIESEL tailgate + vertical LED taillights + 3-dot dually ICC red marker bar
        tx0, ty0 = R(hw * 0.78, sp["z_rear_top"] - 5.5)
        tx1, ty1 = R(-hw * 0.78, zbmp + 6.5)
        tlo, thi = min(tx0, tx1), max(tx0, tx1)
        draw.rounded_rectangle([tlo, ty0, thi, ty1], radius=4, outline=pal["lo"], width=2)
        # Tailgate pull handle
        th_cx = 0.5 * (tlo + thi)
        draw.rounded_rectangle([th_cx - 22, ty0 + 8, th_cx + 22, ty0 + 20], radius=3, fill=(22, 24, 30), outline=(90, 96, 108))
        _draw_crisp_text(im, th_cx, ty1 - 24, 150, 24, "DIESEL", color=(68, 10, 12), style="impact", outline=(235, 86, 72), outline_w=1)
        draw = ImageDraw.Draw(im)
        for d_y in (-8.0, 0.0, 8.0):
            dx_p, dy_p = R(d_y, zbmp + 2.6)
            draw.ellipse([dx_p - 3, dy_p - 3, dx_p + 3, dy_p + 3], fill=(246, 34, 34), outline=(36, 12, 12))
            glow_draw.ellipse([dx_p - 3, dy_p - 3, dx_p + 3, dy_p + 3], fill=(246, 34, 34))
        for sgn in (-1.0, 1.0):
            xa, xb_t = sorted([R(sgn * hw * 0.82, 0)[0], R(sgn * hw * 0.96, 0)[0]])
            _, t_top = R(0, sp["z_rear_top"] - 2.5)
            _, t_bot = R(0, zbmp + 2.5)
            draw.rounded_rectangle([xa, t_top, xb_t, t_bot], radius=4, fill=(204, 22, 26), outline=(28, 12, 14), width=2)
            ym = t_top + (t_bot - t_top) * 0.70
            draw.rectangle([xa + 3, ym, xb_t - 3, ym + 10], fill=(244, 248, 254))
            glow_draw.rounded_rectangle([xa + 2, t_top + 2, xb_t - 2, ym - 2], radius=3, fill=(248, 36, 36))
        px_r, py_r = R(0, zbot + 6.0)
        _draw_plate(im, draw, px_r, py_r, 78, 36, pal["plate"])
        draw = ImageDraw.Draw(im)

    elif kind == "schoolbus":
        draw.rectangle([642, int(ry_bmp), 1024, 544], fill=(22, 24, 28))
        # Top header: crisp bold "SCHOOL BUS" + 4 round 8-way red & amber warning flashers!
        hx_c, hy_c = R(0.0, sp["z_rear_top"] - 6.8)
        draw.rounded_rectangle([hx_c - 76, hy_c - 11, hx_c + 76, hy_c + 11], radius=3, fill=(248, 184, 16), outline=(20, 22, 26), width=2)
        _draw_crisp_text(im, hx_c, hy_c, 138, 16, "SCHOOL BUS", color=(14, 16, 20), style="cond")
        draw = ImageDraw.Draw(im)
        for sgn in (-1.0, 1.0):
            rx_f, ry_f = R(sgn * hw * 0.80, sp["z_rear_top"] - 6.8)
            ax_f, ay_f = R(sgn * hw * 0.58, sp["z_rear_top"] - 6.8)
            draw.ellipse([rx_f - 11, ry_f - 10, rx_f + 11, ry_f + 10], fill=(238, 28, 32), outline=(18, 18, 22), width=2)
            glow_draw.ellipse([rx_f - 9, ry_f - 8, rx_f + 9, ry_f + 8], fill=(250, 36, 36))
            draw.ellipse([ax_f - 10, ay_f - 9, ax_f + 10, ay_f + 9], fill=(255, 172, 20), outline=(18, 18, 22), width=2)
            glow_draw.ellipse([ax_f - 8, ay_f - 7, ax_f + 8, ay_f + 7], fill=(255, 166, 18))
        # Central Emergency Exit Door outline + upper/lower dark glass + crisp "EMERGENCY EXIT"
        ex0, ey0 = R(17.5, 86.0)
        ex1, ey1 = R(-17.5, zbmp + 2.5)
        elo, ehi = min(ex0, ex1), max(ex0, ex1)
        draw.rounded_rectangle([elo, ey0, ehi, ey1], radius=4, outline=(22, 24, 28), width=3)
        ym_e = 0.5 * (ey0 + ey1)
        draw.rounded_rectangle([elo + 8, ey0 + 10, ehi - 8, ym_e - 10], radius=4, fill=(24, 34, 46), outline=(14, 16, 20), width=2)
        draw.rounded_rectangle([elo + 8, ym_e + 12, ehi - 8, ey1 - 10], radius=4, fill=(24, 34, 46), outline=(14, 16, 20), width=2)
        # White reflective background strip for EMERGENCY EXIT stencil + black latch handle
        draw.rounded_rectangle([elo + 5, ym_e - 6, ehi - 5, ym_e + 8], radius=2, fill=(246, 248, 250), outline=(196, 28, 28), width=1)
        _draw_crisp_text(im, 0.5 * (elo + ehi) - 6.0, ym_e + 1, (ehi - elo) - 28, 10, "EMERGENCY EXIT", color=(198, 22, 24), style="cond")
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle([ehi - 15, ym_e - 2, ehi - 7, ym_e + 4], radius=1, fill=(22, 24, 28))
        # Round rear brake/turn/reverse clusters on left & right
        for sgn in (-1.0, 1.0):
            bx_l, by_l = R(sgn * hw * 0.74, zbmp + 24.0)
            draw.ellipse([bx_l - 12, by_l - 11, bx_l + 12, by_l + 11], fill=(228, 26, 30), outline=(20, 20, 22), width=2)
            glow_draw.ellipse([bx_l - 10, by_l - 9, bx_l + 10, by_l + 9], fill=(248, 36, 36))
            tx_l, ty_l = R(sgn * hw * 0.74, zbmp + 11.0)
            draw.ellipse([tx_l - 9, ty_l - 8, tx_l + 9, ty_l + 8], fill=(255, 168, 20), outline=(20, 20, 22), width=2)
            rv_x, rv_y = R(sgn * hw * 0.54, zbmp + 11.0)
            draw.ellipse([rv_x - 6, rv_y - 6, rv_x + 6, rv_y + 6], fill=(238, 244, 252), outline=(24, 24, 28), width=1)
        px_r, py_r = R(-hw * 0.68, zbot + 6.2)
        _draw_plate(im, draw, px_r, py_r, 68, 32, pal["plate"])
        draw = ImageDraw.Draw(im)

    elif kind == "gtcar":
        # Twin stripes + Gloss-black tail panel + Iconic Triple-Bar Red LED Taillights!
        for sgn in (-1.0, 1.0):
            sx_a, _ = R(sgn * 3.0, zbmp)
            sx_b, _ = R(sgn * 12.2, zbmp)
            xlo, xhi = min(sx_a, sx_b), max(sx_a, sx_b)
            draw.rectangle([xlo, 274, xhi, int(ry_bmp)], fill=(22, 25, 31))
        draw.rectangle([642, int(ry_bmp), 1024, 544], fill=(20, 22, 28))
        bx0, by0 = R(hw * 0.92, sp["z_rear_top"] - 2.8)
        bx1, by1 = R(-hw * 0.92, zbmp + 4.2)
        blo, bhi = min(bx0, bx1), max(bx0, bx1)
        draw.rounded_rectangle([blo, by0, bhi, by1], radius=5, fill=(14, 16, 20), outline=(46, 52, 64), width=2)
        # 3 vertical glowing ruby-red bars per side!
        for sgn in (-1.0, 1.0):
            for frac in (0.52, 0.68, 0.84):
                lx_c, _ = R(sgn * hw * frac, 0)
                draw.rounded_rectangle([lx_c - 6, by0 + 5, lx_c + 6, by1 - 5], radius=2, fill=(238, 24, 34), outline=(92, 12, 18), width=1)
                glow_draw.rounded_rectangle([lx_c - 5, by0 + 6, lx_c + 5, by1 - 6], radius=2, fill=(255, 38, 46))
        # Center circular GT rear decklid medallion
        mcx, mcy = 0.5 * (blo + bhi), 0.5 * (by0 + by1)
        draw.ellipse([mcx - 16, mcy - 16, mcx + 16, mcy + 16], fill=(24, 28, 36), outline=(196, 206, 222), width=2)
        _draw_crisp_text(im, mcx, mcy, 24, 14, "GT", color=(238, 244, 252), style="impact")
        draw = ImageDraw.Draw(im)
        px_r, py_r = R(0, zbot + 5.2)
        _draw_plate(im, draw, px_r, py_r, 74, 34, pal["plate"])
        draw = ImageDraw.Draw(im)


def _paint_wheel_and_swatches(im, glow_draw, sp, pal, rng):
    kind = sp["kind"]
    draw = ImageDraw.Draw(im)

    # 1. Wheel face (0..256, 544..800), center = (128, 672), R_tire = 116
    draw.rectangle([0, 544, 256, 800], fill=(20, 22, 26))
    cx, cy = 128, 672
    r_tire = 118
    r_rim = int(round(116 * sp["rim_ratio"]))
    draw.ellipse([cx - r_tire, cy - r_tire, cx + r_tire, cy + r_tire], fill=(26, 28, 33), outline=(12, 14, 18), width=3)
    draw.ellipse([cx - 104, cy - 104, cx + 104, cy + 104], outline=(44, 48, 56), width=2)
    draw.ellipse([cx - 94, cy - 94, cx + 94, cy + 94], outline=(36, 40, 48), width=1)

    if kind == "hdtruck":
        # Forged 10-lug heavy-duty Alcoa dually machined rim
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(206, 214, 226), outline=(108, 116, 130), width=4)
        draw.ellipse([cx - r_rim + 9, cy - r_rim + 9, cx + r_rim - 9, cy + r_rim - 9], fill=(162, 172, 186), outline=(78, 86, 98), width=2)
        for k in range(8):
            ang = 2.0 * math.pi * k / 8.0
            hx = cx + math.cos(ang) * (r_rim * 0.64)
            hy = cy + math.sin(ang) * (r_rim * 0.64)
            draw.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=(20, 24, 30), outline=(228, 234, 244), width=1)
        for k in range(10):
            ang = 2.0 * math.pi * k / 10.0
            lx = cx + math.cos(ang) * 28.0
            ly = cy + math.sin(ang) * 28.0
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(240, 244, 250), outline=(36, 40, 48))
        draw.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], fill=(32, 36, 44), outline=(218, 226, 238), width=2)

    elif kind == "schoolbus":
        # Heavy black 10-lug steel commercial bus wheel with 5 hand-holes & hub cap
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(34, 38, 45), outline=(72, 78, 88), width=3)
        draw.ellipse([cx - r_rim + 9, cy - r_rim + 9, cx + r_rim - 9, cy + r_rim - 9], fill=(24, 27, 33), outline=(54, 60, 70), width=2)
        for k in range(5):
            ang = 2.0 * math.pi * k / 5.0
            hx = cx + math.cos(ang) * (r_rim * 0.63)
            hy = cy + math.sin(ang) * (r_rim * 0.63)
            draw.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=(10, 12, 15), outline=(48, 52, 60), width=1)
        for k in range(10):
            ang = 2.0 * math.pi * k / 10.0
            lx = cx + math.cos(ang) * 29.0
            ly = cy + math.sin(ang) * 29.0
            draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(220, 226, 236), outline=(20, 22, 26))
        draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(42, 46, 54), outline=(172, 180, 192), width=2)

    elif kind == "gtcar":
        # Deep-black barrel + compact cross-drilled dark rotor + compact Brembo caliper + bold 5-twin-spoke rim!
        draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=(216, 224, 236), outline=(118, 128, 144), width=4)
        draw.ellipse([cx - r_rim + 6, cy - r_rim + 6, cx + r_rim - 6, cy + r_rim - 6], fill=(12, 14, 18), outline=(58, 64, 76), width=2)
        # Recessed dark metallic cross-drilled rotor
        r_rot_out = int(round(r_rim * 0.56))
        r_rot_in = int(round(r_rim * 0.30))
        draw.ellipse([cx - r_rot_out, cy - r_rot_out, cx + r_rot_out, cy + r_rot_out], fill=(64, 70, 80), outline=(42, 46, 54), width=2)
        for k in range(18):
            ang = 2.0 * math.pi * k / 18.0
            for rr in (r_rot_out * 0.72, r_rot_out * 0.86):
                dx_h = cx + math.cos(ang) * rr
                dy_h = cy + math.sin(ang) * rr
                draw.ellipse([dx_h - 1.2, dy_h - 1.2, dx_h + 1.2, dy_h + 1.2], fill=(24, 28, 34))
        # Compact curved Brembo-red 6-piston caliper arc (only outer rotor ring, NOT center!)
        cal_pts = []
        for a_deg in range(-28, 29, 7):
            ar = math.radians(a_deg)
            cal_pts.append((cx + math.cos(ar) * (r_rot_out + 4), cy + math.sin(ar) * (r_rot_out + 4)))
        for a_deg in range(28, -29, -7):
            ar = math.radians(a_deg)
            cal_pts.append((cx + math.cos(ar) * (r_rot_in + 3), cy + math.sin(ar) * (r_rot_in + 3)))
        draw.polygon(cal_pts, fill=(214, 28, 30), outline=(120, 14, 16))
        draw.ellipse([cx - r_rot_in, cy - r_rot_in, cx + r_rot_in, cy + r_rot_in], fill=(16, 18, 22))
        # Bold 3D-shaded 5-twin-spoke forged alloy spokes
        for k in range(5):
            for da in (-0.155, 0.155):
                ang = 2.0 * math.pi * k / 5.0 + da - math.pi * 0.5
                nx, ny = -math.sin(ang), math.cos(ang)
                p0 = (cx + math.cos(ang) * 18 + nx * 5.8, cy + math.sin(ang) * 18 + ny * 5.8)
                p1 = (cx + math.cos(ang) * 18 - nx * 5.8, cy + math.sin(ang) * 18 - ny * 5.8)
                p2 = (cx + math.cos(ang) * (r_rim - 5) - nx * 4.2, cy + math.sin(ang) * (r_rim - 5) - ny * 4.2)
                p3 = (cx + math.cos(ang) * (r_rim - 5) + nx * 4.2, cy + math.sin(ang) * (r_rim - 5) + ny * 4.2)
                draw.polygon([p0, p1, p2, p3], fill=(192, 202, 218), outline=(58, 66, 78))
                # Inner bright machined highlight spine along each spoke
                draw.line(
                    [(cx + math.cos(ang) * 21, cy + math.sin(ang) * 21),
                     (cx + math.cos(ang) * (r_rim - 7), cy + math.sin(ang) * (r_rim - 7))],
                    fill=(238, 244, 252), width=2,
                )
        # Center hub + 5 chrome lug nuts + GT cap
        draw.ellipse([cx - 21, cy - 21, cx + 21, cy + 21], fill=(38, 42, 52), outline=(168, 178, 194), width=2)
        for k in range(5):
            ang = 2.0 * math.pi * k / 5.0 - math.pi * 0.5
            lx = cx + math.cos(ang) * 14.5
            ly = cy + math.sin(ang) * 14.5
            draw.ellipse([lx - 2.5, ly - 2.5, lx + 2.5, ly + 2.5], fill=(232, 238, 248))
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(20, 22, 28), outline=(218, 38, 36), width=2)

    # 2. Tire Tread (256..512, 544..800)
    tx0, ty0, tx1, ty1 = vs.RECT_TREAD
    draw.rectangle([tx0, ty0, tx1, ty1], fill=(24, 26, 30))
    for gx in (tx0 + 54, tx0 + 104, tx0 + 152, tx0 + 202):
        draw.rectangle([gx - 5, ty0, gx + 5, ty1], fill=(12, 13, 16))
    step_y = 16 if kind == "hdtruck" else 20
    for y_t in range(ty0, ty1, step_y):
        draw.line([(tx0 + 8, y_t), (tx0 + 96, y_t + 7)], fill=(40, 44, 50), width=4)
        draw.line([(tx1 - 8, y_t), (tx1 - 96, y_t + 7)], fill=(40, 44, 50), width=4)

    # 3. Smoked Glass (512..800, 544..800)
    gx0, gy0, gx1, gy1 = vs.RECT_GLASS
    arr = np.array(im)
    gw, gh = gx1 - gx0, gy1 - gy0
    yg = np.linspace(0.0, 1.0, gh, dtype=np.float32)[:, None]
    xg = np.linspace(0.0, 1.0, gw, dtype=np.float32)[None, :]
    sky_g = (1.0 - yg) ** 1.5
    streak = np.exp(-(((xg * 0.9 + yg * 0.55 - 0.50) / 0.08) ** 2)) * 0.50
    g_patch = np.zeros((gh, gw, 3), dtype=np.float32)
    g_patch[:, :, 0] = 16 + 50 * sky_g + 120 * streak
    g_patch[:, :, 1] = 24 + 66 * sky_g + 136 * streak
    g_patch[:, :, 2] = 34 + 84 * sky_g + 152 * streak
    arr[gy0:gy1, gx0:gx1] = np.clip(g_patch, 0, 255).astype(np.uint8)
    im.paste(Image.fromarray(arr[gy0:gy1, gx0:gx1]), (gx0, gy0))
    draw = ImageDraw.Draw(im)
    draw.rectangle([gx0, gy0, gx1 - 1, gy1 - 1], outline=(14, 16, 20), width=5)

    # 4. Brushed Chrome (800..1024, 544..670) & 100% CLEAN Satin Trim (800..1024, 672..800)!
    cx0, cy0, cx1, cy1 = vs.RECT_CHROME
    arr = np.array(im)
    yc = np.linspace(0.0, 1.0, cy1 - cy0, dtype=np.float32)[:, None]
    ch_band = 138.0 + 92.0 * np.sin(yc * math.pi) + 22.0 * np.cos(yc * 4.0 * math.pi)
    ch_rgb = np.dstack([ch_band * 0.96, ch_band * 0.99, ch_band * 1.03])
    arr[cy0:cy1, cx0:cx1] = np.clip(ch_rgb, 42, 255).astype(np.uint8)
    im.paste(Image.fromarray(arr[cy0:cy1, cx0:cx1]), (cx0, cy0))

    # PURE CLEAN SATIN-BLACK / MICRO-CARBON AUTOMOTIVE TRIM — ZERO RED OR TEXT!
    rx0, ry0, rx1, ry1 = vs.RECT_TRIM
    tw_r, th_r = rx1 - rx0, ry1 - ry0
    arr = np.array(im)
    yy_t, xx_t = np.mgrid[0:th_r, 0:tw_r]
    weave = (((xx_t // 2 + yy_t // 2) % 2) * 3.5 - 1.75).astype(np.float32)
    tr_base = np.zeros((th_r, tw_r, 3), dtype=np.float32)
    tr_base[:, :, 0] = 28.0 + weave
    tr_base[:, :, 1] = 31.0 + weave
    tr_base[:, :, 2] = 36.0 + weave
    arr[ry0:ry1, rx0:rx1] = _add_flake(tr_base, rng, amp=1.6)
    im.paste(Image.fromarray(arr[ry0:ry1, rx0:rx1]), (rx0, ry0))
    draw = ImageDraw.Draw(im)

    # 5. Isolated Vault (0..256, 800..1024):
    #    - RECT_WILD_ENGINE (4..142, 804..954)
    #    - RECT_BADGE_A / RECT_STOP_SIGN (150..252, 804..906)
    #    - RECT_DECAL_STRIP (4..252, 962..1020)
    draw.rectangle([0, 800, 256, 1024], fill=(22, 24, 28))

    # 5A. Detailed Engine Block inside RECT_WILD_ENGINE
    ex0, ey0, ex1, ey1 = RECT_WILD_ENGINE
    draw.rectangle([ex0, ey0, ex1, ey1], fill=(20, 22, 26))
    draw.rounded_rectangle([ex0 + 14, ey0 + 16, ex1 - 14, ey1 - 16], radius=6, fill=(66, 72, 82), outline=(132, 140, 154), width=2)
    for ry in range(ey0 + 28, ey1 - 24, 13):
        draw.line([(ex0 + 22, ry), (ex1 - 22, ry)], fill=(158, 166, 180), width=3)
    vc_col = (196, 28, 24) if kind == "hdtruck" else ((224, 162, 18) if kind == "schoolbus" else (38, 118, 214))
    draw.rounded_rectangle([ex0 + 20, ey0 + 24, ex0 + 44, ey1 - 24], radius=3, fill=vc_col, outline=(24, 26, 30))
    draw.rounded_rectangle([ex1 - 44, ey0 + 24, ex1 - 20, ey1 - 24], radius=3, fill=vc_col, outline=(24, 26, 30))
    draw.ellipse([ex1 - 38, ey0 + 28, ex1 - 24, ey0 + 42], fill=(242, 196, 28), outline=(28, 28, 30))

    # 5B. RECT_BADGE_A (150..252, 804..906): School Bus STOP Sign OR Fender Emblem!
    bx0, by0, bx1, by1 = RECT_BADGE_A
    scx, scy = 0.5 * (bx0 + bx1), 0.5 * (by0 + by1)
    if kind == "schoolbus":
        draw.rectangle([bx0 - 3, by0 - 3, bx1 + 3, by1 + 3], fill=(204, 22, 26))
        oct_outer = [
            (scx + math.cos(math.pi / 8 + k * math.pi / 4) * 48.0, scy + math.sin(math.pi / 8 + k * math.pi / 4) * 48.0)
            for k in range(8)
        ]
        oct_white = [
            (scx + math.cos(math.pi / 8 + k * math.pi / 4) * 45.0, scy + math.sin(math.pi / 8 + k * math.pi / 4) * 45.0)
            for k in range(8)
        ]
        oct_red = [
            (scx + math.cos(math.pi / 8 + k * math.pi / 4) * 40.5, scy + math.sin(math.pi / 8 + k * math.pi / 4) * 40.5)
            for k in range(8)
        ]
        draw.polygon(oct_outer, fill=(196, 18, 22))
        draw.polygon(oct_white, fill=(248, 250, 252))
        draw.polygon(oct_red, fill=(210, 20, 24))
        # Top & bottom red warning flasher lenses on the STOP sign
        for fy_s in (scy - 28.0, scy + 28.0):
            draw.ellipse([scx - 8, fy_s - 6, scx + 8, fy_s + 6], fill=(255, 58, 52), outline=(140, 12, 14), width=1)
            glow_draw.ellipse([scx - 7, fy_s - 5, scx + 7, fy_s + 5], fill=(255, 42, 42))
        _draw_crisp_text(im, scx, scy, 68, 26, "STOP", color=(252, 252, 255), style="impact")
        draw = ImageDraw.Draw(im)
    elif kind == "hdtruck":
        draw.rectangle([bx0 - 3, by0 - 3, bx1 + 3, by1 + 3], fill=(28, 32, 38))
        draw.rounded_rectangle([bx0 + 4, by0 + 18, bx1 - 4, by1 - 18], radius=6, fill=(218, 226, 238), outline=(52, 58, 68), width=3)
        draw.rounded_rectangle([bx0 + 9, by0 + 23, bx1 - 9, by1 - 23], radius=4, fill=(22, 26, 32))
        _draw_crisp_text(im, scx, scy - 9, 76, 20, "6.7TD", color=(238, 44, 36), style="impact")
        _draw_crisp_text(im, scx, scy + 11, 76, 12, "TURBO DIESEL", color=(224, 232, 244), style="cond")
        draw = ImageDraw.Draw(im)
    elif kind == "gtcar":
        draw.rectangle([bx0 - 3, by0 - 3, bx1 + 3, by1 + 3], fill=(32, 36, 44))
        draw.rounded_rectangle([bx0 + 4, by0 + 20, bx1 - 4, by1 - 20], radius=6, fill=(212, 220, 234), outline=(44, 50, 62), width=3)
        draw.rounded_rectangle([bx0 + 9, by0 + 25, bx1 - 9, by1 - 25], radius=4, fill=(18, 22, 28))
        _draw_crisp_text(im, scx, scy - 8, 76, 22, "5.0", color=(236, 44, 38), style="impact")
        _draw_crisp_text(im, scx, scy + 12, 74, 12, "SUPERCHARGED", color=(222, 230, 244), style="cond")
        draw = ImageDraw.Draw(im)

    # 5C. RECT_DECAL_STRIP (4..252, 962..1020): Right-Reading Side Signage Banner!
    dx0, dy0, dx1, dy1 = RECT_DECAL_STRIP
    dcx, dcy = 0.5 * (dx0 + dx1), 0.5 * (dy0 + dy1)
    if kind == "schoolbus":
        # Match exact chrome-yellow side paint at z = zb - 7.5 so flush letterboard blends 100% seamlessly!
        _, py_belt = vs.side_world_to_px(sp, 0.0, sp["z_belt"])
        _, py_bot = vs.side_world_to_px(sp, 0.0, sp["z_bot"])
        _, py_lbl = vs.side_world_to_px(sp, 0.0, sp["z_belt"] - 7.5)
        sky = np.array(pal["sky"], dtype=np.float32)
        hi = np.array(pal["hi"], dtype=np.float32)
        mid = np.array(pal["mid"], dtype=np.float32)
        lo = np.array(pal["lo"], dtype=np.float32)
        c_lbl = tuple(int(round(x)) for x in _side_row_color(py_lbl, py_belt, py_bot, sky, hi, mid, lo))
        draw.rectangle([0, dy0 - 4, 256, 1024], fill=c_lbl)
        _draw_crisp_text(im, dcx, dcy, (dx1 - dx0) - 14, 28, "BAKERSFIELD UNIFIED  •  BUS 42", color=(14, 16, 20), style="cond")
        draw = ImageDraw.Draw(im)
    elif kind == "hdtruck":
        draw.rectangle([0, dy0 - 4, 256, 1024], fill=(22, 25, 31))
        draw.rounded_rectangle([dx0 + 4, dy0 + 4, dx1 - 4, dy1 - 4], radius=5, fill=(24, 28, 36), outline=(246, 194, 58), width=2)
        _draw_crisp_text(im, dcx, dcy, (dx1 - dx0) - 22, 28, "4x4  HEAVY DUALLY", color=(252, 210, 74), style="impact", outline=(140, 24, 20), outline_w=1)
        draw = ImageDraw.Draw(im)
    elif kind == "gtcar":
        draw.rectangle([0, dy0 - 4, 256, 1024], fill=(20, 23, 29))
        draw.line([(dx0 + 6, dy0 + 7), (dx1 - 6, dy0 + 7)], fill=(224, 44, 38), width=3)
        draw.line([(dx0 + 6, dy1 - 7), (dx1 - 6, dy1 - 7)], fill=(224, 44, 38), width=3)
        _draw_crisp_text(im, dcx, dcy, (dx1 - dx0) - 22, 24, "GT  •  V8 PERFORMANCE", color=(228, 236, 248), style="cond")
        draw = ImageDraw.Draw(im)

    # 6. Interior (Floor / Dash / Seats / Wall) in (256..512, 800..1024)
    ix0, iy0, ix1, iy1 = vs.RECT_INTERIOR
    seat_col = (52, 74, 58) if kind == "schoolbus" else ((48, 42, 42) if kind == "hdtruck" else (32, 35, 44))
    draw.rectangle([ix0, iy0, ix1, iy1], fill=(38, 42, 48))
    # Floor (256..384, 800..912)
    draw.rectangle([256, 800, 384, 912], fill=(28, 31, 36))
    for fx in range(262, 380, 9):
        draw.line([(fx, 804), (fx, 908)], fill=(50, 54, 62), width=2)
    # Dash (384..512, 800..912)
    draw.rectangle([384, 800, 512, 912], fill=(22, 25, 30))
    for gcx in (408, 434):
        draw.ellipse([gcx - 10, 818, gcx + 10, 838], fill=(12, 16, 22), outline=(180, 192, 210), width=2)
        glow_draw.ellipse([gcx - 7, 821, gcx + 7, 835], fill=(64, 195, 135))
    draw.rectangle([456, 820, 498, 842], fill=(18, 48, 72), outline=(82, 128, 168), width=1)
    # Seat upholstery (256..384, 912..1024)
    draw.rectangle([256, 912, 384, 1024], fill=seat_col)
    for sy in range(922, 1018, 14):
        draw.line([(264, sy), (376, sy)], fill=(20, 24, 26), width=2)
    # Interior wall (384..512, 912..1024)
    draw.rectangle([384, 912, 512, 1024], fill=(142, 148, 156) if kind == "schoolbus" else (56, 60, 68))

    # 7. Scorched Wreck Metal (512..768, 800..1024) — Crisp Charred Soot & Blistered Gunmetal Steel!
    wx0, wy0, wx1, wy1 = vs.RECT_WRECK
    arr = np.array(im)
    ww, wh = wx1 - wx0, wy1 - wy0
    n_coarse = rng.uniform(18.0, 48.0, (wh // 8, ww // 8))
    nc_up = np.array(Image.fromarray(n_coarse.astype(np.uint8)).resize((ww, wh), Image.Resampling.BILINEAR), dtype=np.float32)
    n_fine = rng.normal(0.0, 6.5, (wh, ww)).astype(np.float32)
    base_ash = np.clip(nc_up + n_fine, 12.0, 68.0)
    # Subtle heat-oxidized rust & scorched paint remnants
    heat = np.clip((nc_up - 34.0) / 14.0, 0.0, 1.0)
    p_tint = np.array(pal["mid"], dtype=np.float32) * 0.14
    w_rgb = np.dstack([
        base_ash + heat * 26.0 + p_tint[0] * (1.0 - heat),
        base_ash * 0.95 + heat * 11.0 + p_tint[1] * (1.0 - heat),
        base_ash * 0.92 + heat * 3.0 + p_tint[2] * (1.0 - heat),
    ])
    arr[wy0:wy1, wx0:wx1] = np.clip(w_rgb, 10, 118).astype(np.uint8)
    im.paste(Image.fromarray(arr[wy0:wy1, wx0:wx1]), (wx0, wy0))
    draw = ImageDraw.Draw(im)
    # Fine metallic scrape striations across scorched wreck steel
    for _ in range(42):
        sx_a = int(rng.integers(wx0 + 6, wx1 - 28))
        sy_a = int(rng.integers(wy0 + 6, wy1 - 6))
        slen = int(rng.integers(12, 28))
        draw.line([(sx_a, sy_a), (sx_a + slen, sy_a + int(rng.integers(-3, 4)))], fill=(82, 86, 94), width=1)

    # 8. Glowing Cracked Ember Core (768..1024, 800..1024)
    emx0, emy0, emx1, emy1 = vs.RECT_EMBER
    arr = np.array(im)
    ew, eh = emx1 - emx0, emy1 - emy0
    em_n = rng.uniform(0.0, 1.0, (eh // 5, ew // 5))
    em_up = np.array(Image.fromarray((em_n * 255).astype(np.uint8)).resize((ew, eh), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    hot = np.clip((em_up - 0.52) * 2.8, 0.0, 1.0)
    em_rgb = np.dstack([22 + 225 * hot, 18 + 115 * (hot ** 1.5), 18 + 28 * (hot ** 2.4)])
    arr[emy0:emy1, emx0:emx1] = np.clip(em_rgb, 0, 255).astype(np.uint8)
    im.paste(Image.fromarray(arr[emy0:emy1, emx0:emx1]), (emx0, emy0))


def build_burn_variant(intact_im, sp, rng):
    arr = np.array(intact_im, dtype=np.float32)
    # Keep charred vehicle colors & panel lines recognizable while darkening with soot & heat blister!
    luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    arr = arr * 0.28 + luma[:, :, None] * 0.14
    coarse = rng.uniform(0.42, 1.12, (H // 16, W // 16))
    c_up = np.array(Image.fromarray((coarse * 128).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), dtype=np.float32) / 128.0
    arr *= c_up[:, :, None]

    rust = np.clip((c_up - 0.80) * 2.6, 0.0, 1.0)
    arr[:, :, 0] += rust * 54.0
    arr[:, :, 1] += rust * 22.0
    arr[:, :, 2] += rust * 6.0

    # Preserve crispRECT_WRECK & RECT_EMBER swatches in the burn atlas!
    intact_np = np.array(intact_im, dtype=np.float32)
    arr[800:1024, 512:1024] = intact_np[800:1024, 512:1024]

    burn_im = Image.fromarray(np.clip(arr, 8, 255).astype(np.uint8))
    bdraw = ImageDraw.Draw(burn_im)
    burn_glow = Image.new("RGB", (W, H), (0, 0, 0))
    bg_draw = ImageDraw.Draw(burn_glow)

    # Spiderwebbed shattered safety glass
    gx0, gy0, gx1, gy1 = vs.RECT_GLASS
    bdraw.rectangle([gx0 + 5, gy0 + 5, gx1 - 5, gy1 - 5], fill=(18, 20, 24))
    gcx, gcy = (gx0 + gx1) // 2, (gy0 + gy1) // 2
    for k in range(20):
        ang = 2.0 * math.pi * k / 20.0 + float(rng.uniform(-0.1, 0.1))
        bdraw.line([(gcx, gcy), (gcx + math.cos(ang) * 125, gcy + math.sin(ang) * 115)], fill=(118, 126, 140), width=2)
    for rr in (28, 58, 92):
        bdraw.ellipse([gcx - rr, gcy - rr, gcx + rr, gcy + rr], outline=(88, 96, 110), width=1)

    # Roaring engine fire glow along hood seams, wheel wells & ember core ONLY (never touching decals!)
    hx0, hy0 = vs.top_world_to_px(sp, sp["x_cowl"], -sp["hw"] * 0.68)
    hx1, hy1 = vs.top_world_to_px(sp, sp["x1"] - 6.0, sp["hw"] * 0.68)
    for (xa, ya, xb, yb) in ((hx0, hy0, hx1, hy0), (hx0, hy1, hx1, hy1), (hx0, hy0, hx0, hy1)):
        bdraw.line([(xa, ya), (xb, yb)], fill=(255, 148, 36), width=7)
        bg_draw.line([(xa, ya), (xb, yb)], fill=(255, 132, 26), width=10)

    sx_c, sy_c = vs.side_world_to_px(sp, sp["x_cowl"] + 10.0, sp["z_belt"] - 2.0)
    sx_n, sy_n = vs.side_world_to_px(sp, sp["x1"] - 8.0, sp["z_nose_top"] - 2.0)
    bdraw.line([(sx_c, sy_c), (sx_n, sy_n)], fill=(255, 136, 28), width=6)
    bg_draw.line([(sx_c, sy_c), (sx_n, sy_n)], fill=(255, 120, 20), width=9)

    emx0, emy0, emx1, emy1 = vs.RECT_EMBER
    # Mask ember glow to actual hot cracks in RECT_EMBER so it looks like glowing fissures, not a flat orange brick!
    ember_patch = intact_np[emy0:emy1, emx0:emx1]
    ember_glow_arr = np.zeros_like(ember_patch)
    hot_mask = np.clip((ember_patch[:, :, 0] - 60.0) / 195.0, 0.0, 1.0)
    ember_glow_arr[:, :, 0] = hot_mask * 235.0
    ember_glow_arr[:, :, 1] = (hot_mask ** 1.4) * 105.0
    ember_glow_arr[:, :, 2] = (hot_mask ** 2.2) * 22.0
    burn_glow.paste(Image.fromarray(ember_glow_arr.astype(np.uint8)), (emx0, emy0))

    ex0, ey0, ex1, ey1 = RECT_WILD_ENGINE
    bg_draw.rectangle([ex0 + 8, ey0 + 8, ex1 - 8, ey1 - 8], fill=(215, 78, 16))
    burn_glow = burn_glow.filter(ImageFilter.GaussianBlur(radius=3.0))
    return burn_im, burn_glow


def generate_wild_vehicle_atlases():
    out = {}
    seeds = {"hdtruck": 5101, "schoolbus": 6202, "gtcar": 7303}
    for kind in WILD_KINDS:
        rng = np.random.default_rng(seeds[kind])
        sp = get_wild_spec(kind)
        pal = PALETTES[kind]

        im = Image.new("RGB", (W, H), (24, 26, 30))
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)

        _paint_side(im, glow_draw, sp, pal, rng)
        _paint_top(im, glow_draw, sp, pal, rng)
        _paint_front_and_rear(im, glow_draw, sp, pal, rng)
        _paint_wheel_and_swatches(im, glow_draw, sp, pal, rng)

        glow = glow.filter(ImageFilter.GaussianBlur(radius=2.2))
        burn_im, burn_glow = build_burn_variant(im, sp, rng)
        out[kind] = {
            "intact": im,
            "intact_glow": glow,
            "burn": burn_im,
            "burn_glow": burn_glow,
        }
    return out


def save_wild_darkplaces_textures(progs_dir, preview_dir, dp_gain=0.60):
    os.makedirs(progs_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    atlases = generate_wild_vehicle_atlases()
    for kind, d in atlases.items():
        d["intact"].save(os.path.join(preview_dir, f"veh_{kind}_atlas.png"))
        d["burn"].save(os.path.join(preview_dir, f"veh_{kind}_burn_atlas.png"))

        dp_intact = ImageEnhance.Brightness(d["intact"]).enhance(dp_gain)
        dp_burn = ImageEnhance.Brightness(d["burn"]).enhance(dp_gain)
        dp_intact.save(os.path.join(progs_dir, f"veh_{kind}_tex.png"))
        d["intact_glow"].save(os.path.join(progs_dir, f"veh_{kind}_tex_glow.png"))
        dp_burn.save(os.path.join(progs_dir, f"veh_{kind}_burn.png"))
        d["burn_glow"].save(os.path.join(progs_dir, f"veh_{kind}_burn_glow.png"))
    return atlases


if __name__ == "__main__":
    p_dir = os.path.abspath(os.path.join(HERE, "..", "..", "progs"))
    prev_dir = os.path.join(HERE, "out", "vehicles")
    save_wild_darkplaces_textures(p_dir, prev_dir)
    print("Generated 3 wild vehicle texture sets successfully!")
