"""Builds the hilarious Evil Scissor-Running Guy sprite with flying money everywhere.

Outputs:
  1. G:/Quake/Combat/BakersfieldQuake/scissor_sprite/
       - scissor_00.png .. scissor_11.png   (12-frame seamless transparent RGBA sprite sequence)
       - scissor_sheet_4x3.png              (4x3 transparent sprite sheet)
       - scissor_run.gif                    (animated preview GIF)
       - index.html                         (interactive sprite viewer with FPS/scrub/bg controls)
  2. G:/Quake/Combat/BakersfieldQuake/progs/fr_scissors.spr32
       - Quake / DarkPlaces 32-bit RGBA upright sprite (IDSP v32, SPR_VP_PARALLEL_UPRIGHT),
         anchored at his feet so he can be spawned directly in-game!
"""

import math
import os
import shutil
import struct
from collections import deque
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
BRAIN = r"C:\Users\qxdc\.gemini\antigravity\brain\b00e11cf-659c-419a-a605-23ec106f1bc8"
RAW_DIR = os.path.join(ROOT, "source", "mm_tools", "out", "scissor_guy")
OUT_DIR = os.path.join(ROOT, "scissor_sprite")
PROGS_DIR = os.path.join(ROOT, "progs")

SRC_OPEN = os.path.join(BRAIN, "raw_pose_open_1793429598089.jpg")
SRC_HALF = os.path.join(BRAIN, "raw_pose_snip_v3_1793429678583.jpg")
SRC_SHUT = os.path.join(BRAIN, "raw_pose_snip_v2_1793429651256.jpg")
SRC_SHEET = os.path.join(BRAIN, "scissor_guy_sheet_2x2_v3_1793429648005.jpg")

WAIST_MID_X = 460
N_FRAMES = 12


def key_magenta_rgba(im_rgb):
    """Studio chroma-key + magenta despill against #FF00FF with interior feature preservation."""
    im = im_rgb.convert("RGB")
    w, h = im.size
    px = im.load()

    # Step 1: Identify definite #FF00FF background pixels (including narrow slits in scissor rings/blades)
    bg = [[False] * w for _ in range(h)]
    m_grid = [[0] * w for _ in range(h)]
    for y in range(h):
        row_bg = bg[y]
        row_m = m_grid[y]
        for x in range(w):
            r, g, b = px[x, y]
            m = (r if r < b else b) - g
            row_m[x] = m
            if m > 68 and r > 95 and b > 95:
                row_bg[x] = True

    # Step 2: Distance transform (up to 8 px) from definite background so interior mouth/ears stay 100% untouched
    dist = [[99] * w for _ in range(h)]
    q = deque()
    for y in range(h):
        for x in range(w):
            if bg[y][x]:
                dist[y][x] = 0
                q.append((x, y))

    while q:
        cx, cy = q.popleft()
        nd = dist[cy][cx] + 1
        if nd > 8:
            continue
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h and dist[ny][nx] > nd:
                dist[ny][nx] = nd
                q.append((nx, ny))

    # Step 3: Un-premultiply #FF00FF spill on edge pixels & build clean RGBA
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            d = dist[y][x]
            if d == 0:
                continue
            r, g, b = px[x, y]
            if d <= 8:
                m = m_grid[y][x]
                if m > 68:
                    continue
                if m > 8:
                    a_f = 1.0 - (m - 8.0) / 62.0
                    if a_f <= 0.04:
                        continue
                    inv = 1.0 - a_f
                    rf = max(0.0, (r - inv * 255.0) / a_f)
                    gf = max(0.0, g / a_f)
                    bf = max(0.0, (b - inv * 255.0) / a_f)
                    # Aggressive magenta despill on all boundary pixels
                    if min(rf, bf) > gf + 4.0:
                        excess = min(rf, bf) - (gf + 4.0)
                        rf = max(0.0, rf - excess)
                        bf = max(0.0, bf - excess)
                    r = max(0, min(255, int(round(rf))))
                    g = max(0, min(255, int(round(gf))))
                    b = max(0, min(255, int(round(bf))))
                    a = max(0, min(255, int(round(a_f * 255.0))))
                else:
                    if d <= 4 and min(r, b) > g + 6:
                        excess = min(r, b) - (g + 6)
                        r = max(0, r - excess)
                        b = max(0, b - excess)
                    a = 255
                opx[x, y] = (r, g, b, a)
            else:
                opx[x, y] = (r, g, b, 255)
    return out


def extract_components(im_rgba, min_pixels=200):
    """Returns list of (pixel_count, bbox, component_rgba_cropped) sorted largest-first."""
    w, h = im_rgba.size
    px = im_rgba.load()
    vis = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 20 and not vis[y][x]:
                q = deque([(x, y)])
                vis[y][x] = True
                pts = []
                x0 = x1 = x
                y0 = y1 = y
                while q:
                    cx, cy = q.popleft()
                    pts.append((cx, cy))
                    if cx < x0:
                        x0 = cx
                    if cx > x1:
                        x1 = cx
                    if cy < y0:
                        y0 = cy
                    if cy > y1:
                        y1 = cy
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 20 and not vis[ny][nx]:
                            vis[ny][nx] = True
                            q.append((nx, ny))
                if len(pts) >= min_pixels:
                    # Expand bbox by 1px to include soft AA alpha=1..20 border
                    bx0, by0 = max(0, x0 - 1), max(0, y0 - 1)
                    bx1, by1 = min(w - 1, x1 + 1), min(h - 1, y1 + 1)
                    cw, ch = bx1 - bx0 + 1, by1 - by0 + 1
                    sub = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                    spx = sub.load()
                    pt_set = set(pts)
                    for py in range(by0, by1 + 1):
                        for px_i in range(bx0, bx1 + 1):
                            if (px_i, py) in pt_set or (
                                px[px_i, py][3] > 0
                                and any(
                                    (px_i + dx, py + dy) in pt_set
                                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                                )
                            ):
                                spx[px_i - bx0, py - by0] = px[px_i, py]
                    comps.append((len(pts), (bx0, by0, bx1 + 1, by1 + 1), sub))
    comps.sort(key=lambda item: item[0], reverse=True)
    return comps


def place_on_full_canvas(comp_tuple, size):
    _, (bx0, by0, _, _), sub = comp_tuple
    full = Image.new("RGBA", size, (0, 0, 0, 0))
    full.paste(sub, (bx0, by0))
    return full


def split_upper_and_lower(char_open, char_half, char_shut):
    """Splits full-canvas character cutouts into:
       - upper_open, upper_half, upper_shut (head + blue polo + arms + giant scissors)
       - lower_left, lower_right (belt + pocket bills + khakis + legs + shoes, with a belt tuck band)
    """
    w, h = char_open.size

    def is_blue_polo(r, g, b, a):
        return a > 15 and (b - r > 26) and (b - g > 10)

    def make_upper(char_im):
        up = char_im.copy()
        upx = up.load()
        for y in range(600, h):
            for x in range(268, 652):
                r, g, b, a = upx[x, y]
                if a == 0:
                    continue
                if not is_blue_polo(r, g, b, a):
                    upx[x, y] = (0, 0, 0, 0)
        return up

    upper_open = make_upper(char_open)
    upper_half = make_upper(char_half)
    upper_shut = make_upper(char_shut)

    # Build lower_left from char_open (100% clean pants + pocket cash)
    lower_left = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = char_open.load()
    lpx = lower_left.load()
    for y in range(600, h):
        for x in range(268, 652):
            r, g, b, a = opx[x, y]
            if a > 0 and not is_blue_polo(r, g, b, a):
                lpx[x, y] = (r, g, b, a)

    # Extend top of belt/pants upward by 14px behind the blue polo hem so hip tilt/bounce never shows a gap
    for x in range(350, 570):
        # Find topmost opaque lower pixel in this column
        top_y = None
        for y in range(605, 705):
            if lpx[x, y][3] > 180:
                top_y = y
                break
        if top_y is not None:
            sample = lpx[x, min(h - 1, top_y + 2)]
            for y in range(max(605, top_y - 16), top_y):
                if lpx[x, y][3] == 0:
                    lpx[x, y] = sample

    # Mirror lower_left horizontally around WAIST_MID_X to get lower_right (opposite leg raised!)
    lower_right = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rpx = lower_right.load()
    for y in range(600, h):
        for x in range(240, 680):
            mx = 2 * WAIST_MID_X - x
            if 0 <= mx < w:
                rpx[mx, y] = lpx[x, y]

    return upper_open, upper_half, upper_shut, lower_left, lower_right


def transform_around_pivot(im, pivot, scale_x=1.0, scale_y=1.0, angle_deg=0.0, dx=0.0, dy=0.0):
    """Applies scale (sx, sy) and rotation around pivot=(px, py), then translates by (dx, dy)."""
    w, h = im.size
    px0, py0 = pivot
    rad = math.radians(angle_deg)
    ca, sa = math.cos(rad), math.sin(rad)

    # Forward map:
    # u = (x - px0) * sx, v = (y - py0) * sy
    # x' = px0 + dx + ca * u - sa * v
    # y' = py0 + dy + sa * u + ca * v
    # Inverse map for PIL AFFINE (maps output x', y' -> input x, y):
    # [u] = [ ca  sa] [x' - px0 - dx]
    # [v]   [-sa  ca] [y' - py0 - dy]
    # x = px0 + u / sx, y = py0 + v / sy
    tx = px0 + dx
    ty = py0 + dy
    a = ca / scale_x
    b = sa / scale_x
    c = px0 - a * tx - b * ty
    d = -sa / scale_y
    e = ca / scale_y
    f = py0 - d * tx - e * ty
    return im.transform((w, h), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


def split_bill_halves(bill_im):
    """Splits a dollar bill cleanly along a jagged/diagonal scissor-cut line into two halves!"""
    w, h = bill_im.size
    left_h = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    right_h = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = bill_im.load()
    lpx = left_h.load()
    rpx = right_h.load()
    for y in range(h):
        cut_x = int(w * 0.5 + (y - h * 0.5) * 0.18)
        for x in range(w):
            c = px[x, y]
            if c[3] == 0:
                continue
            if x < cut_x:
                lpx[x, y] = c
            elif x == cut_x:
                # Crisp bright cut paper edge!
                lpx[x, y] = (235, 242, 225, c[3])
                rpx[x, y] = (235, 242, 225, c[3])
            else:
                rpx[x, y] = c
    return left_h, right_h


def draw_snip_glint(canvas, cx, cy, radius=38, angle_deg=18.0):
    """Draws a crisp gleaming metallic 4-point scissor-snip flash."""
    sz = radius * 2 + 8
    star = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(star)
    mid = sz // 2
    # Soft outer glow
    glow = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((mid - radius // 2, mid - radius // 2, mid + radius // 2, mid + radius // 2), fill=(255, 252, 210, 125))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    star = Image.alpha_composite(star, glow)
    d = ImageDraw.Draw(star)
    # 4-point sharp metallic star spikes + diagonal mini spikes
    pts_main = [
        (mid, mid - radius),
        (mid + 5, mid - 5),
        (mid + radius, mid),
        (mid + 5, mid + 5),
        (mid, mid + radius),
        (mid - 5, mid + 5),
        (mid - radius, mid),
        (mid - 5, mid - 5),
    ]
    d.polygon(pts_main, fill=(255, 255, 245, 240))
    r2 = int(radius * 0.48)
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
    d.polygon(pts_diag, fill=(255, 248, 200, 200))
    star = star.rotate(angle_deg, resample=Image.BICUBIC)
    canvas.alpha_composite(star, (int(cx - mid), int(cy - mid)))


def warp_bill(bill_im, scale, flutter_phase, spin_deg, alpha_mult=1.0):
    """Applies pseudo-3D tumble squeeze + rotation + optional alpha fade to a real $100 bill cutout."""
    bw, bh = bill_im.size
    # Pseudo-3D flip/tumble foreshortening (never completely edge-on 0px so bills always read clearly)
    squeeze = 0.44 + 0.56 * abs(math.cos(flutter_phase))
    nw = max(8, int(round(bw * scale)))
    nh = max(6, int(round(bh * scale * squeeze)))
    resized = bill_im.resize((nw, nh), Image.LANCZOS)
    # Subtle brightness shift as bill tilts toward/away from light
    shade = 0.90 + 0.18 * math.sin(flutter_phase)
    rgb = ImageEnhance.Brightness(resized.convert("RGB")).enhance(shade)
    r, g, b = rgb.split()
    a = resized.getchannel("A")
    if alpha_mult < 0.999:
        a = a.point(lambda v: int(round(v * alpha_mult)))
    out = Image.merge("RGBA", (r, g, b, a))
    return out.rotate(spin_deg, resample=Image.BICUBIC, expand=True)


def build_money_specs(num_bills=34):
    """Deterministic, Golden-Angle distributed 360-degree radial + trailing cash fountain specs."""
    specs = []
    golden = 2.399963229728653  # golden angle in radians
    for i in range(num_bills):
        # Spread bills all around him: sides, upper corners, shoulders, waist, legs!
        ang = (i * golden) % (2.0 * math.pi)
        # Bias slightly away from dead-top-center of his face (ang near -pi/2)
        # In screen coords: +x right, +y down, so straight up is -pi/2
        if -1.95 < ang - 2 * math.pi < -1.19 or (1.19 < (2 * math.pi - ang) < 1.95):
            pass
        # Map angle cleanly to burst outward from his pockets / torso / shoulders
        vx = math.cos(ang)
        vy = math.sin(ang)
        # Keep bills flying out wide left/right, up past ears/scissors, and down around legs
        if vy < -0.55 and abs(vx) < 0.55:
            # Push top-center bills outward to flank his giant head & scissors instead of covering nose/eyes
            vx = -0.78 if (i % 2 == 0) else 0.78
            vy = -0.62

        layer = "front" if (i % 4 == 0 and vy > 0.22) else "back"
        # Emitter origins around waist pockets & torso sides
        emit_x = WAIST_MID_X + vx * (90.0 + (i % 3) * 28.0)
        emit_y = 615.0 + vy * 50.0 + ((i % 5) - 2) * 24.0
        travel = 215.0 + (i % 6) * 38.0
        gravity = 68.0 + (i % 4) * 20.0
        phase0 = (i * 0.61803398875) % 1.0
        speed_cycles = 1 if (i % 3 != 0) else 2  # integer cycles per 12 frames = 100% seamless loop!
        spin_dir = 1 if (i % 2 == 0) else -1
        spin0 = (i * 47.0) % 360.0
        scale0 = 0.68 + (i % 5) * 0.13
        if layer == "front":
            scale0 += 0.16
        bill_idx = i
        specs.append(
            {
                "layer": layer,
                "emit_x": emit_x,
                "emit_y": emit_y,
                "vx": vx,
                "vy": vy,
                "travel": travel,
                "gravity": gravity,
                "phase0": phase0,
                "cycles": speed_cycles,
                "spin0": spin0,
                "spin_dir": spin_dir,
                "scale0": scale0,
                "bill_idx": bill_idx,
            }
        )
    return specs


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)

    # Save raw references in workspace tool folder
    for src, dst in (
        (SRC_OPEN, "raw_pose_open.jpg"),
        (SRC_HALF, "raw_pose_half.jpg"),
        (SRC_SHUT, "raw_pose_shut.jpg"),
        (SRC_SHEET, "raw_sheet_2x2.jpg"),
    ):
        if os.path.exists(src):
            shutil.copy(src, os.path.join(RAW_DIR, dst))

    print("Keying magenta backgrounds...")
    rgba_open = key_magenta_rgba(Image.open(SRC_OPEN))
    rgba_half = key_magenta_rgba(Image.open(SRC_HALF))
    rgba_shut = key_magenta_rgba(Image.open(SRC_SHUT))

    comps_open = extract_components(rgba_open, min_pixels=200)
    comps_half = extract_components(rgba_half, min_pixels=200)
    comps_shut = extract_components(rgba_shut, min_pixels=200)

    canvas_size = rgba_open.size  # (896, 1200)
    char_open = place_on_full_canvas(comps_open[0], canvas_size)
    char_half = place_on_full_canvas(comps_half[0], canvas_size)
    char_shut = place_on_full_canvas(comps_shut[0], canvas_size)

    # Collect all real photorealistic $100 bills from open + shut poses!
    bills = [c[2] for c in comps_open[1:]]
    # Also grab the big crisp foreground $100 bill from bottom-left of shut pose
    for cnt, bbox, sub in comps_shut[1:]:
        if cnt > 6000:
            bills.insert(0, sub)
            break
    print(f"Extracted character + {len(bills)} photorealistic $100 bill sprites!")

    # Create a pair of snipped half-bills from our crispest bill!
    half_bill_l, half_bill_r = split_bill_halves(bills[0])

    upper_open, upper_half, upper_shut, lower_left, lower_right = split_upper_and_lower(
        char_open, char_half, char_shut
    )

    money_specs = build_money_specs(num_bills=36)

    # Render 12-frame seamless run + giant-scissor snip + flying money tornado!
    # Generous simulation canvas (1260 x 1320) so flying bills NEVER clip against canvas borders!
    OUT_W, OUT_H = 1260, 1320
    PAD_X = (OUT_W - canvas_size[0]) // 2
    PAD_Y = 36

    # Per-half-stride (s = 0..5) choreography:
    #   s=0: Drive start   | scissors WIDE OPEN  | leg rising
    #   s=1: High knee peak| scissors HALF-SNIP  | airborne bounce up
    #   s=2: CHOP IMPACT!  | scissors SLAM SHUT! | lunging forward/down + *SNIP!* glint + bill sliced!
    #   s=3: Snip hold     | scissors SHUT       | push-off recoil, sliced bill halves flying apart
    #   s=4: Passing air   | scissors HALF-OPEN  | legs scissoring mid-air
    #   s=5: Reach prep    | scissors WIDE OPEN  | opposite leg starting lift
    upper_states = [upper_open, upper_half, upper_shut, upper_shut, upper_half, upper_open]
    upper_scales = [0.99, 1.02, 1.055, 1.025, 1.00, 0.992]
    upper_tilts = [-3.0, -1.6, 0.8, 1.8, 1.2, -1.4]  # multiplied by stride side (-1 or +1)
    body_dys = [2.0, -12.0, 9.0, 4.0, -8.0, -4.0]
    body_dxs = [-6.0, -9.0, -4.0, 0.0, 2.0, 4.0]  # multiplied by stride side

    lower_sy = [0.95, 1.00, 0.97, 0.93, 0.87, 0.91]
    lower_sx = [1.00, 1.03, 1.02, 0.99, 0.96, 0.98]
    lower_tilts = [2.0, 3.4, 2.2, 1.0, 0.0, -1.4]

    raw_frames = []
    for f in range(N_FRAMES):
        t_norm = f / float(N_FRAMES)
        side = 1.0 if f < 6 else -1.0
        s = f % 6

        frame = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))

        # 1. Background flying money tornado!
        for sp in money_specs:
            if sp["layer"] != "back":
                continue
            p = (t_norm * sp["cycles"] + sp["phase0"]) % 1.0
            # Smooth fade-in (0..0.10) and fade-out (0.82..1.0) so loop is 100% invisible
            if p < 0.10:
                alpha_m = p / 0.10
            elif p > 0.82:
                alpha_m = (1.0 - p) / 0.18
            else:
                alpha_m = 1.0
            dist = sp["travel"] * (0.12 + 0.88 * (1.0 - (1.0 - p) ** 1.6))
            sway = 22.0 * math.sin(2.0 * math.pi * p + sp["phase0"] * 6.0)
            bx = PAD_X + sp["emit_x"] + sp["vx"] * dist - sp["vy"] * sway
            by = PAD_Y + sp["emit_y"] + sp["vy"] * dist + sp["gravity"] * (p * p) + sp["vx"] * sway * 0.5
            flutter = 2.0 * math.pi * (p * 2.0 + sp["phase0"])
            spin = sp["spin0"] + sp["spin_dir"] * p * 360.0
            sc = sp["scale0"] * (0.75 + 0.35 * p)
            b_src = bills[sp["bill_idx"] % len(bills)]
            wb = warp_bill(b_src, sc, flutter, spin, alpha_m)
            frame.alpha_composite(wb, (int(round(bx - wb.width / 2)), int(round(by - wb.height / 2))))

        # 2. Lower Body (Pumping Khaki Legs & Pocket Bills)
        if s <= 4:
            low_src = lower_left if f < 6 else lower_right
            ltilt = lower_tilts[s] * side
        else:
            # s == 5: opposite leg already driving up for smooth transition into next half-stride!
            low_src = lower_right if f < 6 else lower_left
            ltilt = lower_tilts[s] * side

        dx = body_dxs[s] * side
        dy = body_dys[s]
        warped_low = transform_around_pivot(
            low_src,
            pivot=(WAIST_MID_X, 645.0),
            scale_x=lower_sx[s],
            scale_y=lower_sy[s],
            angle_deg=ltilt,
            dx=dx,
            dy=dy,
        )
        frame.alpha_composite(warped_low, (PAD_X, PAD_Y))

        # 3. Upper Body (Evil Grinning Big Head + Royal Blue Polo + Dual Giant Scissors)
        up_src = upper_states[s]
        warped_up = transform_around_pivot(
            up_src,
            pivot=(WAIST_MID_X, 625.0),
            scale_x=upper_scales[s],
            scale_y=upper_scales[s],
            angle_deg=upper_tilts[s] * side,
            dx=dx,
            dy=dy,
        )
        frame.alpha_composite(warped_up, (PAD_X, PAD_Y))

        # 4. Snipped-in-Half Dollar Bills + Metallic Scissor Flash on CHOP beats (s == 2, 3, 4)!
        # Exact closed scissor blade edges in source space: Left ~(168, 295), Right ~(750, 295)
        if s in (2, 3, 4):
            snip_age = (s - 2) / 3.0  # 0.0, 0.33, 0.67
            fade = 1.0 - snip_age * 0.85
            usc = upper_scales[s]
            for raw_bx, raw_by, dir_sign in ((168.0, 292.0, -1), (750.0, 292.0, 1)):
                blade_cx = PAD_X + WAIST_MID_X + (raw_bx - WAIST_MID_X) * usc + dx
                blade_cy = PAD_Y + 625.0 + (raw_by - 625.0) * usc + dy
                spread = 16.0 + 92.0 * snip_age
                drop = 42.0 * (snip_age ** 1.5)
                hl = warp_bill(half_bill_l, 0.60, snip_age * 2.5, -30.0 - 75.0 * snip_age, fade)
                hr = warp_bill(half_bill_r, 0.60, snip_age * 2.5 + 0.6, 26.0 + 75.0 * snip_age, fade)
                frame.alpha_composite(hl, (int(blade_cx - spread - hl.width // 2), int(blade_cy + drop - hl.height // 2)))
                frame.alpha_composite(hr, (int(blade_cx + spread - hr.width // 2), int(blade_cy + drop + 8 - hr.height // 2)))
                if s == 2:
                    draw_snip_glint(frame, blade_cx, blade_cy - 34, radius=40, angle_deg=18.0 * dir_sign)

        # 5. Foreground Flying Dollar Bills (whipping past waist & legs for 3D depth, never covering face or scissors!)
        for sp in money_specs:
            if sp["layer"] != "front":
                continue
            p = (t_norm * sp["cycles"] + sp["phase0"]) % 1.0
            if p < 0.14:
                alpha_m = p / 0.14
            elif p > 0.78:
                alpha_m = (1.0 - p) / 0.22
            else:
                alpha_m = 1.0
            dist = (sp["travel"] + 45.0) * (0.18 + 0.82 * p)
            bx = PAD_X + sp["emit_x"] + sp["vx"] * dist
            by = max(PAD_Y + 610.0, PAD_Y + sp["emit_y"] + sp["vy"] * dist + sp["gravity"] * (p * p))
            flutter = 2.0 * math.pi * (p * 2.0 + sp["phase0"])
            spin = sp["spin0"] + sp["spin_dir"] * p * 360.0
            sc = sp["scale0"] * (0.80 + 0.35 * p)
            b_src = bills[sp["bill_idx"] % len(bills)]
            wb = warp_bill(b_src, sc, flutter, spin, alpha_m)
            frame.alpha_composite(wb, (int(round(bx - wb.width / 2)), int(round(by - wb.height / 2))))

        raw_frames.append(frame)

    # Compute common tight bounding box across all 12 frames with clean padding
    union_box = None
    for fr in raw_frames:
        bb = fr.getbbox()
        if bb:
            if union_box is None:
                union_box = list(bb)
            else:
                union_box[0] = min(union_box[0], bb[0])
                union_box[1] = min(union_box[1], bb[1])
                union_box[2] = max(union_box[2], bb[2])
                union_box[3] = max(union_box[3], bb[3])

    margin = 16
    cx0 = max(0, union_box[0] - margin)
    cy0 = max(0, union_box[1] - margin)
    cx1 = min(OUT_W, union_box[2] + margin)
    cy1 = min(OUT_H, union_box[3] + margin)
    # Make dimensions even
    if (cx1 - cx0) % 2:
        cx1 += 1
    if (cy1 - cy0) % 2:
        cy1 += 1

    # Target crisp sprite frame size (~720px tall, matching earhead_sprite scale)
    crop_w, crop_h = cx1 - cx0, cy1 - cy0
    target_h = 720
    target_w = int(round(crop_w * (target_h / float(crop_h))))
    if target_w % 2:
        target_w += 1

    final_frames = []
    for i, fr in enumerate(raw_frames):
        cropped = fr.crop((cx0, cy0, cx1, cy1)).resize((target_w, target_h), Image.LANCZOS)
        final_frames.append(cropped)
        out_png = os.path.join(OUT_DIR, f"scissor_{i:02d}.png")
        cropped.save(out_png, optimize=True)

    print(f"Saved 12 transparent PNG frames ({target_w}x{target_h}) to {OUT_DIR}")

    # Save 4x3 transparent sprite sheet
    cols, rows = 4, 3
    sheet = Image.new("RGBA", (target_w * cols, target_h * rows), (0, 0, 0, 0))
    for i, fr in enumerate(final_frames):
        c, r = i % cols, i // cols
        sheet.paste(fr, (c * target_w, r * target_h))
    sheet_path = os.path.join(OUT_DIR, "scissor_sheet_4x3.png")
    sheet.save(sheet_path, optimize=True)
    print(f"Saved sprite sheet ({sheet.width}x{sheet.height}) -> {sheet_path}")

    # Save animated GIF (both in scissor_sprite/ and brain artifact dir for inline preview!)
    gif_frames_dark = []
    gif_w = int(round(target_w * 0.65))
    gif_h = int(round(target_h * 0.65))
    for fr in final_frames:
        small = fr.resize((gif_w, gif_h), Image.LANCZOS)
        # Render on a subtle dark checkerboard-free slate card OR clean transparent GIF:
        # Let's make TWO GIFs:
        # 1) scissor_run.gif (transparent disposal=2 GIF for universal sprite embedding!)
        # 2) scissor_preview_card.gif (anti-aliased over rich dark Quake dungeon slate so zero 1-bit GIF dither!)
        alpha = small.getchannel("A")
        rgb = small.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
        mask = Image.eval(alpha, lambda a: 255 if a <= 96 else 0)
        rgb.paste(255, mask)
        rgb.info["transparency"] = 255
        gif_frames_dark.append(rgb)

    gif_path = os.path.join(OUT_DIR, "scissor_run.gif")
    gif_frames_dark[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames_dark[1:],
        duration=85,
        loop=0,
        disposal=2,
        transparency=255,
    )

    # Smooth full-AA showcase GIF over subtle dark checkerboard for crisp artifact display
    showcase_frames = []
    tile = 20
    bg_check = Image.new("RGBA", (gif_w, gif_h), (34, 37, 43, 255))
    bd = ImageDraw.Draw(bg_check)
    for yy in range(0, gif_h, tile):
        for xx in range(0, gif_w, tile):
            if ((xx // tile) + (yy // tile)) % 2 == 0:
                bd.rectangle((xx, yy, xx + tile - 1, yy + tile - 1), fill=(44, 48, 56, 255))
    for fr in final_frames:
        small = fr.resize((gif_w, gif_h), Image.LANCZOS)
        comp = bg_check.copy()
        comp.alpha_composite(small)
        showcase_frames.append(comp.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG))

    showcase_gif_brain = os.path.join(BRAIN, "scissor_guy_animated.gif")
    showcase_frames[0].save(
        showcase_gif_brain,
        save_all=True,
        append_images=showcase_frames[1:],
        duration=85,
        loop=0,
    )
    shutil.copy(showcase_gif_brain, os.path.join(OUT_DIR, "scissor_showcase.gif"))
    shutil.copy(os.path.join(OUT_DIR, "scissor_02.png"), os.path.join(BRAIN, "scissor_hero_snip.png"))

    # Also build a compact preview contact sheet for quick visual inspection
    preview_sheet = Image.new("RGB", ( (target_w // 2) * cols, (target_h // 2) * rows ), (36, 39, 46))
    for i, fr in enumerate(final_frames):
        c, r = i % cols, i // cols
        cell = Image.new("RGBA", (target_w // 2, target_h // 2), (36, 39, 46, 255))
        cell.alpha_composite(fr.resize((target_w // 2, target_h // 2), Image.LANCZOS))
        preview_sheet.paste(cell.convert("RGB"), (c * (target_w // 2), r * (target_h // 2)))
    preview_sheet_brain = os.path.join(BRAIN, "scissor_sheet_preview.png")
    preview_sheet.save(preview_sheet_brain)

    # Bake Quake / DarkPlaces SPR32 sprite (progs/fr_scissors.spr32)!
    # Height 160 px (drawn at .scale 0.5 in Quake = crisp 80-unit tall enemy/friend with flying cash!)
    spr_h = 160
    spr_w = max(2, int(round(target_w * (spr_h / float(target_h)))))
    if spr_w % 2:
        spr_w += 1
    # Foot baseline is near bottom of frame (~94% down)
    foot_oy = int(round(spr_h * 0.94))
    rad = math.hypot(spr_w / 2.0, spr_h)
    # Write single-frame list (frames 0..11, matching fr_rob.spr32 / jw_splash.spr32 convention)
    spr_bytes = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, spr_w, spr_h, len(final_frames), 0.0, 0))
    for fr in final_frames:
        s_im = fr.resize((spr_w, spr_h), Image.LANCZOS)
        spr_bytes += struct.pack("<i", 0) + struct.pack("<iiii", -spr_w // 2, foot_oy, spr_w, spr_h) + s_im.tobytes()
    spr_path = os.path.join(PROGS_DIR, "fr_scissors.spr32")
    with open(spr_path, "wb") as fp:
        fp.write(spr_bytes)
    print(f"Wrote Quake SPR32 sprite -> {spr_path} ({spr_w}x{spr_h}, {len(final_frames)} frames, {len(spr_bytes)/1e6:.2f} MB)")

    # Write interactive HTML sprite viewer in scissor_sprite/index.html
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evil Scissor Runner Sprite</title>
<style>
  :root {{ --bg:#181a1f; --panel:#252830; --ink:#eef0f4; --dim:#9aa0ac; --accent:#4ade80; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif; display:flex; flex-direction:column; align-items:center; gap:14px; padding:18px; min-height:100vh; }}
  h1 {{ font-size:20px; margin:2px 0 0; font-weight:700; letter-spacing:-0.01em; }}
  #stage {{ width:min(100%, 760px); aspect-ratio:{target_w}/{target_h}; max-height:68vh; border-radius:12px; display:flex; align-items:center; justify-content:center; overflow:hidden; border:1px solid #343844; position:relative; }}
  #stage.checker {{ background:repeating-conic-gradient(#2c303a 0% 25%, #22252d 0% 50%) 0 0/24px 24px; }}
  #stage.quake {{ background:radial-gradient(circle at 50% 62%, #3d2e22 0%, #1c1510 72%, #0e0b09 100%); }}
  #stage.green {{ background:#0f172a; }}
  #stage img {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  .row {{ display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:center; width:min(100%,760px); background:var(--panel); border-radius:10px; padding:12px 14px; }}
  input[type=range] {{ flex:1 1 200px; accent-color:var(--accent); }}
  button {{ background:var(--accent); color:#0f172a; border:0; border-radius:6px; padding:8px 14px; font:inherit; font-weight:700; cursor:pointer; }}
  button.alt {{ background:#3a3f4b; color:var(--ink); font-weight:600; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; }}
  #info {{ color:var(--dim); min-width:10ch; text-align:right; font-variant-numeric:tabular-nums; }}
  #strip {{ display:grid; grid-template-columns:repeat(6, 1fr); gap:6px; width:min(100%,760px); }}
  #strip button {{ padding:4px; background:var(--panel); border:2px solid transparent; border-radius:8px; aspect-ratio:{target_w}/{target_h}; overflow:hidden; }}
  #strip button.on {{ border-color:var(--accent); }}
  #strip img {{ width:100%; height:100%; object-fit:contain; display:block; }}
  p.hint {{ color:var(--dim); margin:0; font-size:13px; text-align:center; }}
</style>
</head>
<body>
  <h1>Evil Scissor Runner &mdash; 12-Frame Cash-Storm Sprite</h1>
  <div id="stage" class="checker"><img id="view" alt="sprite frame"></div>
  <div class="row">
    <button id="play">Pause</button>
    <input id="seek" type="range" min="0" max="{N_FRAMES - 1}" value="0" aria-label="frame">
    <span id="info">0 / {N_FRAMES - 1}</span>
    <label>FPS <input id="fps" type="range" min="4" max="24" value="12" style="flex:0 0 96px"></label>
    <button class="alt" id="bgbtn">BG: Checker</button>
  </div>
  <p class="hint">Space plays/pauses &bull; Left/Right arrows step frame-by-frame &bull; Transparent PNGs + <code>progs/fr_scissors.spr32</code></p>
  <div id="strip"></div>
<script>
const N = {N_FRAMES}, pad = n => String(n).padStart(2, "0");
const src = i => "scissor_" + pad(i) + ".png";
const view = document.getElementById("view"), seek = document.getElementById("seek"),
      info = document.getElementById("info"), play = document.getElementById("play"),
      fpsEl = document.getElementById("fps"), stage = document.getElementById("stage"),
      strip = document.getElementById("strip"), bgbtn = document.getElementById("bgbtn");
let cur = 0, playing = true, last = 0;
const bgs = ["checker", "quake", "green"], bgNames = ["Checker", "Quake Dungeon", "Dark Slate"];
let bgi = 0;
for (let i = 0; i < N; i++) {{ const im = new Image(); im.src = src(i); }}
const thumbs = [];
for (let i = 0; i < N; i++) {{
  const b = document.createElement("button"); b.title = "Frame " + i;
  const im = document.createElement("img"); im.src = src(i); b.appendChild(im);
  b.onclick = () => {{ playing = false; sync(); show(i); }};
  strip.appendChild(b); thumbs.push(b);
}}
function show(i) {{
  cur = ((i % N) + N) % N;
  view.src = src(cur); seek.value = cur;
  info.textContent = "Frame " + cur + " / " + (N - 1);
  thumbs.forEach((t, k) => t.classList.toggle("on", k === cur));
}}
function sync() {{ play.textContent = playing ? "Pause" : "Play"; }}
play.onclick = () => {{ playing = !playing; sync(); }};
seek.oninput = () => {{ playing = false; sync(); show(+seek.value); }};
bgbtn.onclick = () => {{
  stage.classList.remove(bgs[bgi]);
  bgi = (bgi + 1) % bgs.length;
  stage.classList.add(bgs[bgi]);
  bgbtn.textContent = "BG: " + bgNames[bgi];
}};
addEventListener("keydown", e => {{
  if (e.code === "Space") {{ e.preventDefault(); playing = !playing; sync(); }}
  else if (e.code === "ArrowRight") {{ playing = false; sync(); show(cur + 1); }}
  else if (e.code === "ArrowLeft") {{ playing = false; sync(); show(cur - 1); }}
}});
function tick(t) {{
  if (playing && t - last > 1000 / fpsEl.value) {{ last = t; show(cur + 1); }}
  requestAnimationFrame(tick);
}}
show(0); requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fp:
        fp.write(html)
    print("Wrote interactive HTML viewer ->", os.path.join(OUT_DIR, "index.html"))


if __name__ == "__main__":
    main()
