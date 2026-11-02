"""Procedural supersampled RGBA MR. D.I.Y. props, hardware particles, starburst badges,
and realistic 2D-rigged lower-body leg completion for the MR. D.I.Y. Friend Sprite Pack."""

import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def make_screw_rgba(size=128):
    """Renders a supersampled gleaming steel Phillips-head screw (matching the MR. D.I.Y. logo screw!)."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = S // 2

    # Dark crisp comic/logo outline + metallic gradients
    outline = (28, 30, 35, 255)

    # Threaded shaft
    top_y = int(S * 0.34)
    bot_y = int(S * 0.88)
    sh_w = int(S * 0.13)
    # Tapered tip
    shaft_poly = [
        (cx - sh_w, top_y),
        (cx + sh_w, top_y),
        (cx + int(sh_w * 0.82), int(S * 0.78)),
        (cx, bot_y),
        (cx - int(sh_w * 0.82), int(S * 0.78)),
    ]
    d.polygon(shaft_poly, fill=(138, 146, 156, 255), outline=outline, width=max(3, S // 42))

    # Specular highlight strip down left-center of shaft
    hi_poly = [
        (cx - int(sh_w * 0.55), top_y + 4),
        (cx - int(sh_w * 0.10), top_y + 4),
        (cx - int(sh_w * 0.08), int(S * 0.80)),
        (cx - int(sh_w * 0.42), int(S * 0.77)),
    ]
    d.polygon(hi_poly, fill=(216, 224, 234, 220))

    # Diagonal helical screw threads!
    n_threads = 5
    for k in range(n_threads):
        ty = top_y + int((k + 0.55) * (bot_y - top_y - S * 0.08) / n_threads)
        tw = int(sh_w * (1.28 - 0.18 * (k / float(n_threads))))
        th = max(5, int(S * 0.032))
        pts = [
            (cx - tw, ty + th),
            (cx + tw, ty - th),
            (cx + tw, ty + th),
            (cx - tw, ty + th * 3),
        ]
        d.polygon(pts, fill=(102, 110, 120, 255), outline=outline, width=max(2, S // 64))
        d.line([(cx - tw + 3, ty + th + 2), (cx + tw - 3, ty - th + 2)], fill=(225, 232, 240, 210), width=max(2, S // 70))

    # Domed / pan Phillips screw head at top
    hw = int(S * 0.28)
    hh = int(S * 0.12)
    hy = int(S * 0.27)
    # Underside rim
    d.ellipse((cx - hw, hy - hh + 8, cx + hw, hy + hh + 10), fill=(95, 102, 112, 255), outline=outline, width=max(3, S // 42))
    # Top pan face
    d.ellipse((cx - hw, hy - hh, cx + hw, hy + hh), fill=(168, 176, 188, 255), outline=outline, width=max(3, S // 42))
    # Bright chrome crescent on upper-left of screw head
    d.arc((cx - hw + 8, hy - hh + 6, cx + hw - 8, hy + hh - 6), start=190, end=330, fill=(238, 244, 252, 235), width=max(3, S // 48))

    # Crisp Phillips '+' slot on top of head
    arm_x = int(hw * 0.56)
    arm_y = int(hh * 0.50)
    w_slot = max(4, S // 34)
    d.line([(cx - arm_x, hy), (cx + arm_x, hy)], fill=(42, 46, 54, 255), width=w_slot)
    d.line([(cx, hy - arm_y), (cx, hy + arm_y)], fill=(42, 46, 54, 255), width=w_slot)

    return im.resize((size, size), Image.Resampling.LANCZOS)


def make_mrdiy_bag_rgba(size=148):
    """Renders an iconic bright yellow MR. D.I.Y. shopping bag ('MR.D.I.Y. Always Low Prices')."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = S // 2
    outline = (35, 24, 10, 255)
    lw = max(3, S // 48)

    # Die-cut shopping bag body with slight perspective flair
    bx0, bx1 = int(S * 0.20), int(S * 0.80)
    by0, by1 = int(S * 0.22), int(S * 0.88)
    bag_pts = [
        (bx0 + 6, by0),
        (bx1 - 6, by0),
        (bx1 + 6, by1),
        (bx0 - 6, by1),
    ]
    d.polygon(bag_pts, fill=(255, 208, 12, 255), outline=outline, width=lw)

    # Vertical bag side gusset fold shading on right edge
    gusset = [
        (bx1 - 24, by0 + lw),
        (bx1 - 6, by0 + lw),
        (bx1 + 4, by1 - lw),
        (bx1 - 18, by1 - lw),
    ]
    d.polygon(gusset, fill=(230, 176, 6, 255))

    # Punch-out handle hole near top center
    hw, hh = int(S * 0.11), int(S * 0.036)
    hy = by0 + int(S * 0.075)
    d.rounded_rectangle((cx - hw, hy - hh, cx + hw, hy + hh), radius=hh, fill=(0, 0, 0, 0), outline=outline, width=lw)
    # Clear alpha inside handle cutout!
    arr = np.array(im)
    yy, xx = np.mgrid[0:S, 0:S]
    hole = (np.abs(xx - cx) < hw - lw) & (np.abs(yy - hy) < hh - lw // 2)
    arr[hole] = 0
    im = Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im)

    # Red & yellow MR.D.I.Y. banner across center of bag
    ry0, ry1 = int(S * 0.45), int(S * 0.63)
    d.rounded_rectangle((bx0 + 12, ry0, bx1 - 14, ry1), radius=10, fill=(224, 20, 28, 255), outline=(255, 238, 55, 255), width=lw)

    try:
        font_big = ImageFont.truetype("arialbd.ttf", int(S * 0.105))
        font_sm = ImageFont.truetype("arialbd.ttf", int(S * 0.055))
    except Exception:
        font_big = ImageFont.load_default()
        font_sm = font_big

    txt = "MR.D.I.Y."
    bb = d.textbbox((0, 0), txt, font=font_big)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = cx - tw // 2 - 2
    ty = (ry0 + ry1) // 2 - th // 2 - bb[1]
    d.text((tx, ty), txt, font=font_big, fill=(255, 232, 20, 255), stroke_width=max(2, lw // 2), stroke_fill=(30, 10, 10, 255))

    sub = "LOW PRICES"
    bb2 = d.textbbox((0, 0), sub, font=font_sm)
    sw = bb2[2] - bb2[0]
    d.text((cx - sw // 2, ry1 + int(S * 0.045)), sub, font=font_sm, fill=(32, 24, 12, 255))

    return im.resize((size, size), Image.Resampling.LANCZOS)


def make_price_burst_rgba(text="LOW PRICES!", size=150):
    """Renders a punchy retail yellow/red starburst bargain sticker!"""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = S // 2
    spikes = 14
    pts = []
    for i in range(spikes * 2):
        ang = i * math.pi / spikes
        r = S * (0.45 if i % 2 == 0 else 0.33)
        # Flatten slightly into oval burst
        pts.append((cx + r * math.cos(ang), cy + r * 0.76 * math.sin(ang)))
    d.polygon(pts, fill=(255, 218, 10, 255), outline=(215, 18, 24, 255), width=max(4, S // 42))

    try:
        font = ImageFont.truetype("arialbd.ttf", int(S * 0.095))
    except Exception:
        font = ImageFont.load_default()

    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(
        (cx - tw // 2, cy - th // 2 - bb[1]),
        text,
        font=font,
        fill=(218, 16, 22, 255),
        stroke_width=max(2, S // 80),
        stroke_fill=(255, 250, 210, 255),
    )
    return im.resize((size, size), Image.Resampling.LANCZOS)


def draw_pump_glint(canvas, cx, cy, radius=38, angle_deg=15.0):
    """Draws a golden-yellow MR. D.I.Y. impact sparkle/starburst."""
    sz = radius * 2 + 12
    star = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    mid = sz // 2
    glow = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((mid - radius // 2, mid - radius // 2, mid + radius // 2, mid + radius // 2), fill=(255, 220, 40, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    star = Image.alpha_composite(star, glow)
    d = ImageDraw.Draw(star)
    pts_main = [
        (mid, mid - radius),
        (mid + 6, mid - 6),
        (mid + radius, mid),
        (mid + 6, mid + 6),
        (mid, mid + radius),
        (mid - 6, mid + 6),
        (mid - radius, mid),
        (mid - 6, mid - 6),
    ]
    d.polygon(pts_main, fill=(255, 248, 190, 245), outline=(255, 190, 10, 220))
    r2 = int(radius * 0.50)
    pts_diag = [
        (mid - r2, mid - r2),
        (mid, mid - 3),
        (mid + r2, mid - r2),
        (mid + 3, mid),
        (mid + r2, mid + r2),
        (mid, mid + 3),
        (mid - r2, mid + r2),
        (mid - 3, mid),
    ]
    d.polygon(pts_diag, fill=(255, 212, 28, 225))
    star = star.rotate(angle_deg, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(star, (int(round(cx - mid)), int(round(cy - mid))))


def render_jogging_legs_rgba(
    canvas_w,
    canvas_h,
    hip_cx,
    hip_y,
    hip_span,
    leg_len,
    phase_rad,
    facing_cos=1.0,
    facing_sin=0.0,
    pant_rgb=(24, 25, 29),
):
    """Synthesizes shaded dark-denim jeans + casual dark sneakers w/ crisp white soles
    matching his real black jeans in frames 69..95, animated in a lively jogging/bouncing cycle!
    `facing_cos` = +1 front, 0 side, -1 back; `facing_sin` = +1 facing right, -1 facing left.
    """
    S = 2  # 2x supersampling for crisp anti-aliased legs & sneakers
    W, H = canvas_w * S, canvas_h * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    hcx = hip_cx * S
    hy = hip_y * S
    span = hip_span * S
    L = leg_len * S

    # Pelvis / upper jeans yoke tucked up under his untucked yellow-smiley shirt hem so zero gap ever appears!
    pelvis_w = max(int(L * 0.34), int(abs(span) + L * 0.24))
    pelvis_top = int(hy - L * 0.22)
    pelvis_bot = int(hy + L * 0.14)
    d.rounded_rectangle(
        (int(hcx - pelvis_w * 0.52), pelvis_top, int(hcx + pelvis_w * 0.52), pelvis_bot),
        radius=int(L * 0.12),
        fill=(pant_rgb[0], pant_rgb[1], pant_rgb[2], 255),
    )

    # Two legs: idx 0 = left leg, idx 1 = right leg
    legs = []
    for leg_i in (0, 1):
        p = phase_rad + (0.0 if leg_i == 0 else math.pi)
        side_sign = -1.0 if leg_i == 0 else 1.0

        # Lateral hip offset foreshortened by facing_cos
        hx = hcx + side_sign * span * 0.46 * facing_cos
        # Depth order so far leg draws first and near leg draws on top!
        stride_s = math.sin(p)
        lift = max(0.0, -math.cos(p))  # 0..1 knee lift

        # Depth z (>0 closer to camera)
        z_depth = side_sign * facing_sin * (-0.5) + stride_s * facing_cos * 0.7

        # Side-profile swing vs front/back foreshortened lift
        swing_x = stride_s * L * 0.30 * facing_sin + side_sign * L * 0.03 * facing_cos
        knee_x = hx + swing_x * 0.62 + facing_sin * lift * L * 0.16
        knee_y = hy + L * (0.48 - 0.16 * lift - 0.05 * max(0.0, stride_s * abs(facing_cos)))

        ankle_x = hx + swing_x * 0.95 - facing_sin * lift * L * 0.14
        ankle_y = knee_y + L * (0.46 - 0.14 * lift)

        legs.append((z_depth, leg_i, hx, hy, knee_x, knee_y, ankle_x, ankle_y, lift, stride_s))

    legs.sort(key=lambda item: item[0])

    for z_depth, leg_i, hx, hy_l, kx, ky, ax, ay, lift, stride_s in legs:
        shade = 0.88 if z_depth < 0 else 1.04
        pr = max(10, min(255, int(round(pant_rgb[0] * shade))))
        pg = max(10, min(255, int(round(pant_rgb[1] * shade))))
        pb = max(12, min(255, int(round(pant_rgb[2] * shade))))
        hi_col = (min(255, pr + 18), min(255, pg + 19), min(255, pb + 23), 255)
        sh_col = (max(6, pr - 10), max(6, pg - 10), max(8, pb - 10), 255)

        thigh_r0 = L * 0.155
        knee_r = L * 0.118
        ankle_r = L * 0.088

        def capsule_poly(x0, y0, r0, x1, y1, r1, col, hi=None):
            dx, dy = x1 - x0, y1 - y0
            ln = max(1.0, math.hypot(dx, dy))
            nx, ny = -dy / ln, dx / ln
            pts = [
                (x0 + nx * r0, y0 + ny * r0),
                (x1 + nx * r1, y1 + ny * r1),
                (x1 - nx * r1, y1 - ny * r1),
                (x0 - nx * r0, y0 - ny * r0),
            ]
            d.polygon(pts, fill=col, outline=sh_col, width=3)
            d.ellipse((x0 - r0, y0 - r0, x0 + r0, y0 + r0), fill=col)
            d.ellipse((x1 - r1, y1 - r1, x1 + r1, y1 + r1), fill=col)
            if hi is not None:
                # Subtle denim highlight ridge along front-center of leg
                hx0, hy0 = x0 + nx * r0 * 0.25, y0 + ny * r0 * 0.25
                hx1, hy1 = x1 + nx * r1 * 0.25, y1 + ny * r1 * 0.25
                d.line([(hx0, hy0), (hx1, hy1)], fill=hi, width=max(4, int(r1 * 0.42)))

        # Thigh + Shin
        capsule_poly(hx, hy_l, thigh_r0, kx, ky, knee_r, (pr, pg, pb, 255), hi=hi_col)
        capsule_poly(kx, ky, knee_r * 0.96, ax, ay, ankle_r, (pr, pg, pb, 255), hi=hi_col)

        # Sneaker w/ crisp white rubber midsole!
        shoe_w = L * (0.20 + 0.09 * abs(facing_sin))
        shoe_h = L * 0.115
        toe_dir = facing_sin if abs(facing_sin) > 0.25 else ((-0.25 if leg_i == 0 else 0.25) * facing_cos)
        sx0 = ax - shoe_w * (0.42 - 0.26 * toe_dir)
        sx1 = ax + shoe_w * (0.42 + 0.26 * toe_dir)
        sy0 = ay - shoe_h * 0.22
        sy1 = ay + shoe_h * 0.78

        # White rubber sneaker sole
        sole_h = max(6.0, shoe_h * 0.28)
        d.rounded_rectangle(
            (sx0 - 2, sy1 - sole_h, sx1 + 2, sy1 + 2),
            radius=int(sole_h * 0.45),
            fill=(232, 234, 238, 255),
            outline=(40, 42, 48, 255),
            width=3,
        )
        # Black canvas sneaker upper
        d.rounded_rectangle(
            (sx0, sy0, sx1, sy1 - sole_h * 0.55),
            radius=int(shoe_h * 0.42),
            fill=(30, 32, 38, 255),
            outline=(16, 18, 22, 255),
            width=3,
        )
        # Pant cuff overlapping top of sneaker
        d.rounded_rectangle(
            (ax - ankle_r * 1.12, ay - ankle_r * 0.65, ax + ankle_r * 1.12, ay + ankle_r * 0.35),
            radius=int(ankle_r * 0.35),
            fill=(pr, pg, pb, 255),
            outline=sh_col,
            width=2,
        )

    return im.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
