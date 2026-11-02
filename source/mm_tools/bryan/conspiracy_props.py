"""3D Projection, Dynamic Tinfoil-Hat Bryan Rig Posing, and High-Detail Prop Builders
for Bryan's 12 Ultra-High-FPS 360° Conspiracy, Weapon & Nerd Animations.
"""
import math
import os
import random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import build_bryan_sprites as bbs

FW, FH = 320, 288
CX = FW // 2
GY = 256  # Generous 68px sky headroom above Bryan's tinfoil hat + 32px floor margin!
ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)


def project_3d(lx, ly, lz, d_idx, cx=CX, gy=GY):
    """Projects Bryan-local 3D point (lx=forward, ly=left, lz=up) to (sx, sy, dz, persp_scale)
    for camera angle index d_idx (0..7 => 0°..315°).
    Convention:
      dz < 0 => CLOSER to camera (drawn IN FRONT of Bryan)
      dz > 0 => FURTHER from camera (drawn BEHIND Bryan)
    """
    phi = math.radians(d_idx * 45.0)
    sx = cx + (-lx * math.sin(phi) + ly * math.cos(phi))
    dz = -lx * math.cos(phi) - ly * math.sin(phi)
    sy = gy - lz + dz * 0.17
    sc = float(np.clip(1.0 - 0.0016 * dz, 0.76, 1.24))
    return sx, sy, dz, sc


def paste_rgba_center(canvas, im, cx, cy, scale=1.0, rot_deg=0.0, alpha_mul=1.0, flip_x=False):
    """Pastes an RGBA PIL image centered at (cx, cy) with optional scale, rotation, and alpha."""
    if im is None:
        return
    work = im.transpose(Image.FLIP_LEFT_RIGHT) if flip_x else im
    if abs(scale - 1.0) > 0.015:
        nw = max(2, int(round(work.width * scale)))
        nh = max(2, int(round(work.height * scale)))
        work = work.resize((nw, nh), Image.BILINEAR)
    if abs(rot_deg) > 0.35:
        work = work.rotate(rot_deg, resample=Image.BICUBIC, expand=True)
    if alpha_mul < 0.995:
        arr = np.array(work)
        arr[..., 3] = np.clip(arr[..., 3].astype(np.float32) * alpha_mul, 0, 255).astype(np.uint8)
        work = Image.fromarray(arr, "RGBA")
    dx = int(round(cx - work.width * 0.5))
    dy = int(round(cy - work.height * 0.5))
    if dx >= canvas.width or dy >= canvas.height or dx + work.width <= 0 or dy + work.height <= 0:
        return
    canvas.alpha_composite(work, (dx, dy))


def draw_shadow(canvas, cx, gy=GY, rx=28, ry=7, alpha=90, color=(8, 6, 12)):
    """Fast elliptical soft ground shadow without full-canvas GaussianBlur overhead."""
    w = max(8, int(rx * 2 + 16))
    h = max(6, int(ry * 2 + 12))
    sub = np.zeros((h, w, 4), dtype=np.uint8)
    cv2.ellipse(sub, (w // 2, h // 2), (max(2, int(rx)), max(1, int(ry))), 0, 0, 360,
                (color[0], color[1], color[2], int(alpha)), -1, cv2.LINE_AA)
    sub = cv2.GaussianBlur(sub, (9, 9), 2.6)
    canvas.alpha_composite(Image.fromarray(sub, "RGBA"), (int(round(cx - w // 2)), int(round(gy - h // 2))))


def draw_glow_line(dr, p0, p1, core_col, glow_col, core_w=2, glow_w=7):
    dr.line([p0, p1], fill=glow_col, width=glow_w)
    dr.line([p0, p1], fill=core_col, width=core_w)


def load_compact_rigs():
    """Loads 8-dir Solo Bryan Idle, 6-frame Solo Run, Demons, and Tinfoil Hat normalized for 320x288 (height 186px)."""
    raw = bbs.load_normalized_assets()
    sc_fac = 186.0 / 212.0

    def resc(pair):
        im, piv = pair
        nw = max(2, int(round(im.width * sc_fac)))
        nh = max(2, int(round(im.height * sc_fac)))
        return im.resize((nw, nh), Image.LANCZOS), int(round(piv * sc_fac))

    idle = {d: resc(raw["bryan_idle"][d]) for d in range(8)}
    run6 = {d: [resc(p) for p in raw["bryan_run_6"][d]] for d in range(8)}
    crimson = {d: resc(raw["crimson"][d]) for d in range(8)}
    reaper = resc(raw["reaper"])
    ram = resc(raw["ram"])
    hat = raw["hat_crop"].resize(
        (max(2, int(round(raw["hat_crop"].width * sc_fac))), max(2, int(round(raw["hat_crop"].height * sc_fac)))),
        Image.LANCZOS,
    )
    return {
        "idle": idle,
        "run6": run6,
        "crimson": crimson,
        "reaper": reaper,
        "ram": ram,
        "hat": hat,
    }


def render_bryan_3d(
    canvas, rigs, d_idx, cx=CX, gy=GY, lz=0.0,
    run_frame=None, pitch_fwd_deg=0.0, roll_deg=0.0,
    squash_x=1.0, stretch_y=1.0, alpha_mul=1.0, tint=None,
    hat_mode="normal", hat_lift=0.0, hat_tilt=0.0,
    deal_shades=False, scouter=False,
):
    """Renders Tinfoil-Hat Bryan at angle d_idx with full 3D pitch/lean foreshortening and comical hat/face mods!
    pitch_fwd_deg > 0: leans forward in Bryan's facing direction (e.g. +38° Area-51 Naruto run!)
    pitch_fwd_deg < 0: leans backward (e.g. -58° Matrix Neo Bullet-Time dodge!)
    Returns (head_x, head_top_y, body_mid_x, body_mid_y) on canvas for attaching hats/FX.
    """
    im, piv = rigs["idle"][d_idx] if run_frame is None else rigs["run6"][d_idx][int(run_frame) % 6]
    arr = np.array(im).copy()

    # Optional hat modes that modify or lift Bryan's top tinfoil cone (top 33px of 186px rig):
    if hat_mode in ("lifted_backup", "bonked", "saiyan"):
        # Erase original top cone (y < 29) so we can draw the lifted/bonked/Super-Saiyan hat cleanly!
        # Leave y=25..31 silver base if backup hat!
        arr[:29, :, 3] = 0

    if tint is not None or alpha_mul < 0.995:
        af = arr.astype(np.float32)
        if tint is not None:
            af[..., 0] = np.clip(af[..., 0] * tint[0], 0, 255)
            af[..., 1] = np.clip(af[..., 1] * tint[1], 0, 255)
            af[..., 2] = np.clip(af[..., 2] * tint[2], 0, 255)
        if alpha_mul < 0.995:
            af[..., 3] *= alpha_mul
        arr = af.astype(np.uint8)

    work = Image.fromarray(arr, "RGBA")

    # Add pixel "DEAL WITH IT" shades or green DBZ Scouter directly onto Bryan's face before 3D tilt!
    if (deal_shades or scouter) and d_idx in (0, 1, 2, 6, 7):
        fd = ImageDraw.Draw(work)
        face_y = 40
        off_f = {0: 0, 1: -5, 2: -10, 6: 10, 7: 5}[d_idx]
        fx = piv + off_f
        if deal_shades:
            if d_idx in (0, 1, 7):
                fd.rectangle([fx - 12, face_y - 2, fx + 12, face_y + 3], fill=(10, 12, 16, 255))
                fd.rectangle([fx - 10, face_y - 1, fx - 3, face_y + 3], fill=(20, 24, 32, 255))
                fd.rectangle([fx + 3, face_y - 1, fx + 10, face_y + 3], fill=(20, 24, 32, 255))
                # White 8-bit pixel glint!
                fd.rectangle([fx - 9, face_y, fx - 6, face_y + 1], fill=(255, 255, 255, 255))
                fd.rectangle([fx + 4, face_y, fx + 7, face_y + 1], fill=(255, 255, 255, 255))
            else:
                sx0 = fx - 6 if d_idx == 2 else fx - 2
                fd.rectangle([sx0, face_y - 2, sx0 + 9, face_y + 3], fill=(12, 14, 18, 255))
                fd.rectangle([sx0 + 2, face_y, sx0 + 5, face_y + 1], fill=(255, 255, 255, 255))
        if scouter:
            sx_s = fx - 8 if d_idx != 6 else fx + 2
            fd.rectangle([sx_s, face_y - 3, sx_s + 9, face_y + 4], fill=(40, 255, 90, 195), outline=(180, 255, 200, 255))

    # Compute 3D screen rotation & foreshortening from pitch_fwd_deg!
    phi = math.radians(d_idx * 45.0)
    # At d=2 (90° facing left), sin(phi)=+1 => +pitch rotates CCW (head tilts left = forward!).
    # At d=6 (270° facing right), sin(phi)=-1 => +pitch rotates CW (head tilts right = forward!).
    screen_rot = pitch_fwd_deg * math.sin(phi) + roll_deg
    foreshort_y = 1.0 - 0.24 * abs(math.sin(math.radians(pitch_fwd_deg))) * abs(math.cos(phi))
    tot_sx = max(0.55, squash_x)
    tot_sy = max(0.55, stretch_y * foreshort_y)

    if abs(tot_sx - 1.0) > 0.015 or abs(tot_sy - 1.0) > 0.015:
        nw = max(4, int(round(work.width * tot_sx)))
        nh = max(4, int(round(work.height * tot_sy)))
        work = work.resize((nw, nh), Image.BILINEAR)
        piv = int(round(piv * tot_sx))

    foot_y = gy - lz
    # Pivot rotation around Bryan's ankles/feet (piv, work.height - 6) so his sneakers stay grounded during leans!
    if abs(screen_rot) > 0.4:
        pad = 96
        big = Image.new("RGBA", (work.width + pad * 2, work.height + pad * 2), (0, 0, 0, 0))
        big.paste(work, (pad, pad))
        ank_x = pad + piv
        ank_y = pad + work.height - 6
        big_r = big.rotate(screen_rot, resample=Image.BICUBIC, center=(ank_x, ank_y))
        dx = int(round(cx - ank_x))
        dy = int(round(foot_y - 6 - ank_y))
        canvas.alpha_composite(big_r, (dx, dy))
        rad_r = math.radians(screen_rot)
        head_len = work.height - 14
        head_x = cx - math.sin(rad_r) * head_len
        head_y = (foot_y - 6) - math.cos(rad_r) * head_len
    else:
        dx = int(round(cx - piv))
        dy = int(round(foot_y - work.height))
        canvas.alpha_composite(work, (dx, dy))
        head_x = float(cx)
        head_y = float(dy + 8)

    # Render special comical Tinfoil Hat states at (head_x, head_y)!
    hd = ImageDraw.Draw(canvas)
    hx_i, hy_i = int(round(head_x)), int(round(head_y))

    if hat_mode == "lifted_backup":
        # Draw TINY BACKUP TINFOIL CONE HAT right on Bryan's head while main hat levitates above!
        hd.polygon([(hx_i, hy_i + 4), (hx_i - 9, hy_i + 20), (hx_i + 9, hy_i + 20)],
                   fill=(210, 220, 232, 255), outline=(120, 130, 145, 255))
        hd.line([(hx_i, hy_i + 5), (hx_i - 3, hy_i + 19)], fill=(255, 255, 255, 255), width=1)
        # Main levitating tinfoil hat pulled up toward UFO!
        paste_rgba_center(canvas, rigs["hat"], hx_i, hy_i + 12 - hat_lift, scale=1.0, rot_deg=hat_tilt)

    elif hat_mode == "bonked":
        # Dented/tilted tinfoil hat popped slightly off head after nunchuck bonk!
        paste_rgba_center(canvas, rigs["hat"], hx_i + 4, hy_i + 10 - hat_lift, scale=1.05, rot_deg=hat_tilt)

    elif hat_mode == "triple_dish":
        # Two extra auxiliary tinfoil satellite dishes sprouting off the sides of his tinfoil hat!
        for sgn in (-1, 1):
            dx_s = hx_i + sgn * 16
            dy_s = hy_i + 11
            hd.pieslice([dx_s - 9, dy_s - 9, dx_s + 9, dy_s + 9],
                        start=190 if sgn < 0 else -70, end=350 if sgn < 0 else 90,
                        fill=(215, 225, 240, 255), outline=(110, 120, 138, 255))
            hd.line([(dx_s, dy_s), (dx_s + sgn * 10, dy_s - 8)], fill=(245, 250, 255, 255), width=2)
            hd.ellipse([dx_s + sgn * 10 - 2, dy_s - 10, dx_s + sgn * 10 + 2, dy_s - 6], fill=(80, 255, 220, 255))

    elif hat_mode == "wizard":
        # Arcane starry purple Wizard Brim + gold band around his silver tinfoil cone!
        hd.ellipse([hx_i - 22, hy_i + 15, hx_i + 22, hy_i + 23],
                   fill=(88, 36, 165, 255), outline=(250, 204, 52, 255), width=2)
        for sx_st in (-10, 0, 9):
            hd.ellipse([hx_i + sx_st - 1, hy_i + 17, hx_i + sx_st + 1, hy_i + 19], fill=(255, 230, 90, 255))

    elif hat_mode == "saiyan":
        # GOLDEN SUPER-SAIYAN SPIKY TINFOIL CROWN!
        spikes = [
            [(hx_i, hy_i - 18), (hx_i - 8, hy_i + 18), (hx_i + 8, hy_i + 18)],
            [(hx_i - 16, hy_i - 11), (hx_i - 15, hy_i + 19), (hx_i - 2, hy_i + 15)],
            [(hx_i + 16, hy_i - 11), (hx_i + 2, hy_i + 15), (hx_i + 15, hy_i + 19)],
            [(hx_i - 26, hy_i - 1), (hx_i - 18, hy_i + 20), (hx_i - 7, hy_i + 16)],
            [(hx_i + 26, hy_i - 1), (hx_i + 7, hy_i + 16), (hx_i + 18, hy_i + 20)],
        ]
        for poly in spikes:
            hd.polygon(poly, fill=(255, 215, 45, 255), outline=(255, 145, 15, 255))
        hd.line([(hx_i, hy_i - 16), (hx_i, hy_i + 15)], fill=(255, 252, 195, 255), width=2)

    return head_x, head_y, float(cx), float(foot_y - work.height * 0.52)


# ==============================================================================
# PRE-BUILT HIGH-DETAIL SHADED RGBA PROPS
# ==============================================================================

def make_flat_earth_disc():
    """Shaded 3D Azimuthal Flat-Earth Disc + Towering Antarctic Ice Wall + Wire Sun/Moon + Firmament Dome."""
    im = Image.new("RGBA", (116, 78), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = 58, 48
    # Dark rocky underside crust below the flat disc!
    dr.polygon([(cx - 44, cy), (cx + 44, cy), (cx + 26, cy + 16), (cx - 26, cy + 16)],
               fill=(72, 50, 36, 255), outline=(38, 26, 18, 255))
    # Deep azimuthal flat ocean
    dr.ellipse([cx - 46, cy - 16, cx + 46, cy + 16], fill=(22, 118, 210, 255), outline=(215, 245, 255, 255), width=3)
    # Flat green continents radiating from North Pole center
    for poly in [
        [(cx - 6, cy - 3), (cx - 24, cy - 7), (cx - 30, cy + 2), (cx - 12, cy + 5)],
        [(cx + 5, cy - 5), (cx + 28, cy - 8), (cx + 32, cy + 1), (cx + 14, cy + 4)],
        [(cx - 4, cy + 3), (cx + 8, cy + 10), (cx - 10, cy + 11)],
    ]:
        dr.polygon(poly, fill=(56, 188, 78, 255))
    # Jagged glittering Antarctic Ice Wall crown around the outer edge!
    for i in range(18):
        a = (i / 18.0) * 2 * math.pi
        ix = cx + math.cos(a) * 45
        iy = cy + math.sin(a) * 15
        dr.polygon([(ix - 3, iy), (ix, iy - 7), (ix + 3, iy)], fill=(235, 250, 255, 245), outline=(140, 210, 245, 220))
    # Translucent glass Firmament Dome + miniature Spotlight Sun & Moon!
    dr.pieslice([cx - 44, cy - 42, cx + 44, cy + 14], start=180, end=360,
                fill=(130, 225, 255, 48), outline=(195, 245, 255, 165), width=2)
    dr.ellipse([cx - 22, cy - 31, cx - 12, cy - 21], fill=(255, 220, 45, 255), outline=(255, 255, 190, 255))
    dr.ellipse([cx + 12, cy - 30, cx + 21, cy - 21], fill=(215, 225, 240, 255))
    return im


def make_nasa_globe():
    """Round 'FAKE NASA CGI' globe with red X slash."""
    im = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([4, 4, 40, 40], fill=(28, 98, 215, 255), outline=(255, 255, 255, 240), width=2)
    dr.ellipse([11, 10, 26, 23], fill=(55, 185, 82, 255))
    dr.ellipse([22, 22, 34, 34], fill=(55, 185, 82, 255))
    dr.line([(7, 7), (37, 37)], fill=(255, 42, 42, 255), width=4)
    dr.line([(37, 7), (7, 37)], fill=(255, 42, 42, 255), width=4)
    return im


def make_corkboard(front=True):
    """Pepe Silvia Red-String Conspiracy Corkboard (front w/ UFO, Demon, Pyramid & red yarn; wood/duct-tape back)."""
    im = Image.new("RGBA", (92, 68), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rectangle([2, 2, 89, 65], fill=(122, 82, 46, 255), outline=(58, 36, 18, 255), width=3)
    if not front:
        dr.rectangle([6, 6, 85, 61], fill=(96, 66, 38, 255))
        # Silver duct-tape X on back of board!
        dr.line([(16, 14), (76, 54)], fill=(192, 200, 210, 255), width=6)
        dr.line([(76, 14), (16, 54)], fill=(182, 190, 202, 255), width=6)
        return im
    dr.rectangle([6, 6, 85, 61], fill=(184, 134, 78, 255))
    # Pinned polaroids & newspaper clippings
    cards = [
        (10, 10, 28, 25, (240, 242, 245, 255)),  # UFO photo
        (36, 9, 56, 26, (255, 245, 215, 255)),   # Pyramid chart
        (62, 11, 81, 28, (245, 230, 230, 255)),  # Demon sketch
        (13, 35, 34, 54, (225, 248, 255, 255)),  # Flat earth map
        (42, 37, 62, 56, (250, 250, 240, 255)),  # 5G graph
        (66, 36, 82, 55, (255, 235, 205, 255)),  # Question note
    ]
    pins = []
    for x0, y0, x1, y1, col in cards:
        dr.rectangle([x0, y0, x1, y1], fill=col, outline=(70, 55, 40, 220))
        pins.append(((x0 + x1) // 2, y0 + 3))
    # Mini drawings inside polaroids
    dr.ellipse([14, 15, 24, 20], fill=(90, 95, 110, 255))  # UFO
    dr.polygon([(46, 13), (40, 23), (52, 23)], fill=(225, 185, 40, 255))  # Pyramid
    dr.ellipse([67, 15, 76, 24], fill=(215, 35, 35, 255))  # Demon
    dr.ellipse([17, 42, 30, 49], fill=(35, 135, 225, 255))  # Flat Earth
    # Crisscrossing frantic RED CONSPIRACY YARN between all pins!
    yarn_pairs = [(0, 1), (1, 2), (0, 3), (3, 1), (1, 4), (2, 4), (4, 5), (2, 5), (0, 4), (3, 5)]
    for a, b in yarn_pairs:
        dr.line([pins[a], pins[b]], fill=(245, 28, 38, 245), width=2)
    for px, py in pins:
        dr.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 220, 45, 255), outline=(140, 20, 20, 255))
    return im


def make_jet_plane():
    """White government chemtrail jet."""
    im = Image.new("RGBA", (54, 28), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.polygon([(48, 14), (12, 10), (4, 4), (8, 14), (4, 22), (14, 17)],
               fill=(238, 244, 252, 255), outline=(95, 112, 135, 255))
    dr.polygon([(28, 13), (18, 2), (22, 13)], fill=(195, 210, 228, 255))
    dr.polygon([(28, 15), (16, 26), (22, 15)], fill=(175, 192, 214, 255))
    dr.ellipse([38, 11, 45, 14], fill=(55, 185, 245, 255))
    return im


def make_rainbow_frog():
    """Hilarious neon-rainbow 'Turn-The-Frogs-Gay' hopping frog with rainbow halo!"""
    im = Image.new("RGBA", (32, 28), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    # Tiny rainbow arc over frog
    cols = [(255, 55, 75, 220), (255, 205, 45, 220), (55, 245, 120, 220), (65, 185, 255, 220)]
    for i, c in enumerate(cols):
        dr.arc([4 + i, 2 + i, 28 - i, 20 - i], start=180, end=360, fill=c, width=2)
    # Chubby frog body + big eyes
    dr.ellipse([7, 12, 25, 24], fill=(72, 235, 85, 255), outline=(22, 95, 32, 255))
    dr.ellipse([9, 8, 15, 14], fill=(255, 255, 255, 255), outline=(22, 95, 32, 255))
    dr.ellipse([17, 8, 23, 14], fill=(255, 255, 255, 255), outline=(22, 95, 32, 255))
    dr.ellipse([11, 10, 13, 12], fill=(15, 15, 20, 255))
    dr.ellipse([19, 10, 21, 12], fill=(15, 15, 20, 255))
    return im


def make_5g_tower():
    """Sinister steel-lattice 5G Mind-Control Cell Tower with glowing magenta emitter panels."""
    im = Image.new("RGBA", (64, 156), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = 32
    dr.line([(cx - 16, 150), (cx - 4, 28)], fill=(125, 138, 156, 255), width=3)
    dr.line([(cx + 16, 150), (cx + 4, 28)], fill=(125, 138, 156, 255), width=3)
    for y in range(42, 148, 18):
        hw = int(4 + (y - 28) * 0.10)
        dr.line([(cx - hw, y), (cx + hw, y + 14)], fill=(95, 108, 126, 240), width=2)
        dr.line([(cx + hw, y), (cx - hw, y + 14)], fill=(95, 108, 126, 240), width=2)
    # Top 3-sector 5G antenna array + blinking red FAA beacon
    dr.rectangle([cx - 15, 20, cx - 8, 44], fill=(220, 228, 240, 255), outline=(255, 55, 210, 255))
    dr.rectangle([cx + 8, 20, cx + 15, 44], fill=(220, 228, 240, 255), outline=(255, 55, 210, 255))
    dr.rectangle([cx - 5, 18, cx + 5, 45], fill=(240, 245, 255, 255), outline=(255, 55, 210, 255))
    dr.line([(cx, 4), (cx, 18)], fill=(190, 200, 215, 255), width=2)
    dr.ellipse([cx - 4, 2, cx + 4, 10], fill=(255, 40, 200, 255))
    return im


def make_pigeon_drone():
    """'BIRDS AREN'T REAL' Mechanical Surveillance Pigeon w/ rotor & glowing red Terminator lens!"""
    im = Image.new("RGBA", (44, 34), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    # Metallic grey pigeon body + riveted panels + antenna + top rotor
    dr.ellipse([10, 13, 34, 26], fill=(148, 158, 174, 255), outline=(52, 60, 74, 255), width=2)
    dr.ellipse([27, 8, 38, 18], fill=(168, 178, 194, 255), outline=(52, 60, 74, 255), width=2)
    dr.polygon([(37, 12), (43, 14), (37, 16)], fill=(245, 185, 45, 255))
    dr.polygon([(11, 17), (2, 13), (4, 22)], fill=(110, 120, 136, 255))
    # Glowing red surveillance camera lens eye!
    dr.ellipse([32, 10, 36, 14], fill=(255, 24, 36, 255))
    # Top drone propeller mast
    dr.line([(22, 5), (22, 13)], fill=(80, 90, 105, 255), width=2)
    dr.line([(10, 5), (34, 5)], fill=(220, 235, 255, 235), width=2)
    return im


def make_illuminati_pyramid():
    """Golden 3D All-Seeing Reptilian Eye Pyramid."""
    im = Image.new("RGBA", (76, 72), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = 38
    # Radiant golden halo
    dr.ellipse([8, 4, 68, 64], fill=(255, 225, 65, 68))
    # Left & right 3D pyramid faces with brick courses
    dr.polygon([(cx, 8), (8, 60), (cx, 66)], fill=(235, 190, 52, 255), outline=(120, 84, 16, 255), width=2)
    dr.polygon([(cx, 8), (cx, 66), (68, 60)], fill=(185, 142, 34, 255), outline=(120, 84, 16, 255), width=2)
    for y in range(24, 60, 9):
        w = int((y - 8) * 0.54)
        dr.line([(cx - w, y), (cx + w, y)], fill=(135, 96, 20, 170), width=1)
    # Floating capstone + Glowing Green Reptilian Slit-Eye!
    dr.ellipse([cx - 13, 25, cx + 13, 41], fill=(245, 255, 235, 255), outline=(35, 120, 45, 255), width=2)
    dr.ellipse([cx - 6, 27, cx + 6, 39], fill=(52, 225, 78, 255))
    dr.polygon([(cx, 28), (cx - 2, 33), (cx, 38), (cx + 2, 33)], fill=(12, 22, 14, 255))
    return im


def make_ufo_saucer():
    """Classic Chrome Area-51 Flying Saucer w/ glowing green cockpit & rim lights."""
    im = Image.new("RGBA", (104, 48), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy = 52, 26
    dr.pieslice([cx - 24, cy - 22, cx + 24, cy + 6], start=180, end=360,
                fill=(120, 255, 195, 195), outline=(210, 255, 235, 255), width=2)
    # Little green alien head inside glass dome!
    dr.ellipse([cx - 6, cy - 17, cx + 6, cy - 6], fill=(95, 240, 105, 255))
    dr.ellipse([cx - 5, cy - 13, cx - 2, cy - 10], fill=(12, 16, 18, 255))
    dr.ellipse([cx + 2, cy - 13, cx + 5, cy - 10], fill=(12, 16, 18, 255))
    # Metallic saucer hull
    dr.ellipse([cx - 48, cy - 9, cx + 48, cy + 11], fill=(168, 178, 196, 255), outline=(72, 82, 98, 255), width=2)
    dr.ellipse([cx - 38, cy - 6, cx + 38, cy + 4], fill=(222, 230, 244, 255))
    for i in range(-3, 4):
        lx = cx + i * 12
        col = (75, 255, 125, 255) if i % 2 == 0 else (255, 70, 220, 255)
        dr.ellipse([lx - 3, cy - 1, lx + 3, cy + 5], fill=col)
    return im


def make_katana():
    """Razor-sharp 5-foot Folded-Steel Anime Katana (vertical, hilt at bottom, tip at top)."""
    im = Image.new("RGBA", (28, 128), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = 14
    # Cyan/white sheen aura
    dr.line([(cx, 6), (cx, 96)], fill=(95, 225, 255, 95), width=9)
    # Curved steel blade + white hamon edge
    dr.polygon([(cx - 2, 96), (cx + 3, 96), (cx + 2, 12), (cx - 1, 4)], fill=(215, 228, 245, 255))
    dr.line([(cx + 2, 95), (cx + 1, 8)], fill=(255, 255, 255, 255), width=2)
    # Golden tsuba guard + diamond-wrapped black/crimson tsuka handle
    dr.rectangle([cx - 8, 95, cx + 8, 99], fill=(240, 195, 55, 255), outline=(110, 80, 15, 255))
    dr.rectangle([cx - 3, 99, cx + 3, 124], fill=(28, 24, 32, 255))
    for y in range(102, 123, 5):
        dr.polygon([(cx, y), (cx + 2, y + 2), (cx, y + 4), (cx - 2, y + 2)], fill=(215, 38, 52, 255))
    return im


def make_rune_greatsword():
    """Blazing Electric-Blue Cosmic Paladin Rune Broadsword (inspired by Video 2!)."""
    im = Image.new("RGBA", (46, 146), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = 23
    # Outer electric-blue plasma bloom
    dr.polygon([(cx, 2), (cx + 14, 20), (cx + 12, 108), (cx - 12, 108), (cx - 14, 20)],
               fill=(35, 165, 255, 105))
    # Broad rune blade + white energy core
    dr.polygon([(cx, 6), (cx + 8, 20), (cx + 7, 108), (cx - 7, 108), (cx - 8, 20)],
               fill=(135, 225, 255, 255), outline=(255, 255, 255, 245))
    dr.line([(cx, 12), (cx, 106)], fill=(255, 255, 255, 255), width=3)
    # Ornate silver-gold paladin crossguard + pommel
    dr.polygon([(cx - 18, 105), (cx + 18, 105), (cx + 14, 113), (cx - 14, 113)],
               fill=(228, 234, 245, 255), outline=(90, 110, 145, 255))
    dr.ellipse([cx - 4, 106, cx + 4, 112], fill=(60, 220, 255, 255))
    dr.rectangle([cx - 3, 113, cx + 3, 136], fill=(58, 44, 36, 255))
    dr.ellipse([cx - 6, 134, cx + 6, 144], fill=(235, 200, 65, 255), outline=(110, 85, 20, 255))
    return im


def make_dual_lightsaber():
    """Double-Bladed Crimson & Emerald Plasma Lightsaber Staff."""
    im = Image.new("RGBA", (28, 156), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = 14
    # Top crimson plasma blade
    dr.line([(cx, 6), (cx, 64)], fill=(255, 32, 65, 135), width=11)
    dr.line([(cx, 8), (cx, 64)], fill=(255, 95, 115, 245), width=6)
    dr.line([(cx, 10), (cx, 64)], fill=(255, 255, 255, 255), width=2)
    # Bottom cyan-emerald plasma blade
    dr.line([(cx, 92), (cx, 150)], fill=(35, 255, 165, 135), width=11)
    dr.line([(cx, 92), (cx, 148)], fill=(110, 255, 205, 245), width=6)
    dr.line([(cx, 92), (cx, 146)], fill=(255, 255, 255, 255), width=2)
    # Chrome dual-emitter hilt in center
    dr.rectangle([cx - 4, 63, cx + 4, 93], fill=(185, 195, 210, 255), outline=(45, 52, 64, 255))
    dr.rectangle([cx - 4, 73, cx + 4, 83], fill=(32, 36, 44, 255))
    return im


def make_d20_die(highlight_20=False):
    """Shaded translucent Ruby Icosahedral 20-Sided Die (D20) with crisp gold facets."""
    im = Image.new("RGBA", (52, 52), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx, cy, r = 26, 26, 21
    hex_pts = [(cx + math.cos(math.radians(-90 + i * 60)) * r, cy + math.sin(math.radians(-90 + i * 60)) * r) for i in range(6)]
    tri_pts = [(cx + math.cos(math.radians(-90 + i * 120)) * (r * 0.56), cy + math.sin(math.radians(-90 + i * 120)) * (r * 0.56)) for i in range(3)]
    fill_main = (235, 32, 68, 242) if not highlight_20 else (255, 58, 92, 255)
    dr.polygon(hex_pts, fill=fill_main, outline=(255, 215, 75, 255), width=2)
    dr.polygon(tri_pts, fill=(255, 75, 105, 255), outline=(255, 232, 120, 255), width=2)
    for i in range(6):
        dr.line([hex_pts[i], tri_pts[i // 2]], fill=(255, 215, 75, 210), width=1)
    if highlight_20:
        # Crisp bright '20' emblem inside center triangle!
        dr.line([(cx - 5, cy - 2), (cx - 1, cy - 2), (cx - 5, cy + 4), (cx - 1, cy + 4)], fill=(255, 255, 210, 255), width=2)
        dr.ellipse([cx + 1, cy - 3, cx + 6, cy + 4], outline=(255, 255, 210, 255), width=2)
    return im


def make_dm_screen():
    """3-panel Wooden D&D Dungeon Master Screen with dragon crest."""
    im = Image.new("RGBA", (88, 48), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for i, x0 in enumerate((4, 30, 58)):
        w = 26 if i != 1 else 28
        dr.rectangle([x0, 6, x0 + w, 44], fill=(104, 62, 34, 255), outline=(228, 182, 58, 255), width=2)
    dr.ellipse([36, 15, 52, 35], fill=(195, 38, 48, 255), outline=(250, 215, 75, 255))
    return im


def make_matrix_bullet():
    """Gleaming brass slow-motion Matrix bullet."""
    im = Image.new("RGBA", (26, 12), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.polygon([(24, 6), (15, 2), (3, 2), (3, 10), (15, 10)], fill=(235, 190, 65, 255), outline=(120, 88, 20, 255))
    dr.line([(5, 4), (18, 4)], fill=(255, 245, 185, 255), width=1)
    return im
