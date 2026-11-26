"""Procedural texture atlases, custom 3D floppy disk labels, glowing LEDs,
and animated CRT screens for all 4 Disc Sentry Gun concepts.
"""
from __future__ import annotations

import math
import os
from typing import Dict, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


_USE_BUILTIN_FONT = False


def _font(size: int, bold: bool = True, mono: bool = True) -> ImageFont.FreeTypeFont:
    if _USE_BUILTIN_FONT:
        return ImageFont.load_default(size=size)
    if mono:
        cands = ["consolab.ttf", "lucon.ttf", "courbd.ttf"] if bold else ["consola.ttf", "cour.ttf"]
    else:
        cands = ["impact.ttf", "arialbd.ttf", "tahomabd.ttf"] if bold else ["tahoma.ttf", "arial.ttf"]
    for nm in cands:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def _fbm(h: int, w: int, seed: int = 42, octaves: Tuple[int, ...] = (4, 8, 16, 32)) -> np.ndarray:
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tot = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh, gw = max(2, h // freq), max(2, w // freq)
        grid = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(grid, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tot += amp
    return acc / max(tot, 1e-6)


def _draw_hazard(dr: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
                 c1: Tuple[int, int, int], c2: Tuple[int, int, int], stripe_w: int = 24) -> None:
    dr.rectangle([x0, y0, x1, y1], fill=c1)
    h = y1 - y0
    for sx in range(x0 - h, x1 + h, stripe_w * 2):
        poly = [(sx, y1), (sx + stripe_w, y1), (sx + stripe_w + h, y0), (sx + h, y0)]
        dr.polygon(poly, fill=c2)
    dr.rectangle([x0, y0, x1, y1], outline=(18, 20, 24), width=3)


# ==============================================================================
# BODY ATLAS LAYOUT (1024x1024) SHARED UV REGIONS
# ==============================================================================
UV_TOWER_FRONT = (0.008, 0.008, 0.492, 0.242)   # [0..512,   0..256]   Tower/PC front (bays, switches, badge)
UV_TOWER_SIDE  = (0.508, 0.008, 0.992, 0.242)   # [512..1024,0..256]   Tower/PC side vents & stencil
UV_CRT_BEZEL   = (0.008, 0.258, 0.492, 0.492)   # [0..512,   256..512] CRT bezel trim + dials + badge
UV_CRT_BACK    = (0.508, 0.258, 0.992, 0.492)   # [512..1024,256..512] CRT rear housing & heat vents + sticker
UV_TRIPOD      = (0.008, 0.508, 0.492, 0.742)   # [0..512,   512..768] Tripod / heavy steel base / armor
UV_HAZARD      = (0.508, 0.508, 0.742, 0.742)   # [512..768, 512..768] Hazard stripe / accent plate
UV_DRUM_MAG    = (0.758, 0.508, 0.992, 0.742)   # [768..1024,512..768] Floppy drum / stacked floppy rack
UV_BARREL      = (0.008, 0.758, 0.242, 0.992)   # [0..256,   768..1024] Perforated gunmetal barrel shroud
UV_SPEAKER     = (0.258, 0.758, 0.492, 0.992)   # [256..512, 768..1024] 90s Speaker grille / Keyboard keycaps
UV_CABLE_DARK  = (0.508, 0.758, 0.742, 0.992)   # [512..768, 768..1024] Cables / rubber pads / dark hardware
UV_CHROME      = (0.758, 0.758, 0.992, 0.992)   # [768..1024,768..1024] Brushed steel / chrome barrels


def build_concept_body_texture(concept_id: str, out_dir: str) -> str:
    """Build 1024x1024 high-detail body texture atlas for one of the 4 sentry concepts."""
    W = H = 1024
    grain = _fbm(H, W, seed=101 + sum(ord(c) for c in concept_id), octaves=(4, 8, 16, 32))

    if concept_id == "retro":
        pc_col = np.array([208.0, 198.0, 172.0])
        metal_col = np.array([84.0, 92.0, 106.0])
        accent_a = (206, 62, 40)
        accent_b = (38, 42, 48)
        badge_bg = (182, 48, 32)
        badge_txt = "SENTRY-486"
        sub_txt = "TF FLOPPY TURRET"
    elif concept_id == "classic":
        pc_col = np.array([162.0, 150.0, 124.0])
        metal_col = np.array([68.0, 72.0, 80.0])
        accent_a = (46, 86, 158)
        accent_b = (162, 150, 124)
        badge_bg = (42, 74, 146)
        badge_txt = "486DX2-66"
        sub_txt = "BAKERSFIELD LAB #04"
    elif concept_id == "badass":
        pc_col = np.array([50.0, 54.0, 62.0])
        metal_col = np.array([38.0, 42.0, 48.0])
        accent_a = (232, 168, 28)
        accent_b = (22, 22, 26)
        badge_bg = (188, 26, 26)
        badge_txt = "MK-IV SHREDDER"
        sub_txt = "KILL_32.EXE // ARMED"
    else:  # msdos
        pc_col = np.array([200.0, 194.0, 174.0])
        metal_col = np.array([70.0, 76.0, 66.0])
        accent_a = (212, 54, 34)
        accent_b = (26, 30, 32)
        badge_bg = (22, 92, 172)
        badge_txt = "MS-DOS 6.22"
        sub_txt = "MG-FLOPPY STORM"

    arr = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        arr[..., c] = np.clip(pc_col[c] + grain * 11.0, 12, 248)

    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # 1. [0..512, 0..256] PC Front Faceplate
    dr.rectangle([4, 4, 507, 251], outline=tuple(int(min(255, x + 28)) for x in pc_col), width=4)
    # 5.25" optical / drive bay + 3.5" floppy bay
    dr.rounded_rectangle([24, 22, 288, 86], radius=4, fill=tuple(int(max(12, x - 26)) for x in pc_col), outline=(44, 46, 52), width=3)
    dr.line([44, 54, 268, 54], fill=(24, 26, 30), width=6)
    dr.rounded_rectangle([24, 98, 288, 162], radius=4, fill=tuple(int(max(12, x - 16)) for x in pc_col), outline=(44, 46, 52), width=3)
    dr.rectangle([48, 122, 254, 138], fill=(18, 20, 24), outline=(92, 96, 104), width=2)
    dr.rounded_rectangle([126, 114, 176, 146], radius=4, fill=(24, 26, 30), outline=(92, 96, 104), width=2)
    dr.text((52, 142), "1.44MB FLOPPY", fill=(84, 88, 96), font=_font(12, bold=True))

    for lx in range(28, 284, 14):
        dr.rounded_rectangle([lx, 178, lx + 7, 236], radius=2, fill=(26, 28, 32), outline=(88, 90, 96), width=1)

    dr.rounded_rectangle([310, 24, 488, 94], radius=5, fill=badge_bg, outline=(230, 232, 238), width=2)
    dr.text((322, 34), badge_txt, fill=(246, 246, 242), font=_font(20, bold=True))
    dr.text((322, 64), sub_txt, fill=(235, 224, 180), font=_font(12, bold=True))

    dr.rounded_rectangle([316, 112, 390, 166], radius=4, fill=(32, 36, 40), outline=(110, 114, 122), width=2)
    dr.text((328, 122), "66", fill=(96, 245, 118) if concept_id != "badass" else (255, 68, 58), font=_font(30, bold=True))
    dr.rounded_rectangle([404, 114, 480, 164], radius=4, fill=(148, 144, 134), outline=(48, 48, 52), width=2)
    dr.text((414, 130), "TURBO", fill=(28, 30, 34), font=_font(15, bold=True))
    dr.rounded_rectangle([316, 182, 480, 232], radius=4, fill=(132, 128, 120), outline=(48, 48, 52), width=2)
    dr.text((352, 198), "POWER", fill=(24, 24, 28), font=_font(18, bold=True))

    # 2. [512..1024, 0..256] PC Side Panels & Cooling Louvers (clean, no border white line)
    dr.rectangle([514, 2, 1021, 253], outline=(76, 80, 88), width=3)
    for vx in range(546, 760, 16):
        dr.line([vx, 34, vx, 218], fill=(32, 34, 38), width=6)
    dr.rounded_rectangle([786, 62, 994, 192], radius=6, fill=tuple(int(max(12, x - 20)) for x in pc_col), outline=accent_a, width=4)
    dr.text((806, 86), badge_txt, fill=accent_a, font=_font(22, bold=True))
    dr.text((806, 122), "AUTO-SENTRY", fill=(232, 232, 224) if concept_id == "badass" else (48, 50, 56), font=_font(15, bold=True))
    dr.text((806, 146), "3.5\" CANNON", fill=(232, 232, 224) if concept_id == "badass" else (48, 50, 56), font=_font(15, bold=True))

    # 3. [0..512, 256..512] CRT Monitor Bezel Trim (molded plastic + dials + badge)
    dr.rectangle([4, 260, 507, 507], outline=tuple(int(min(255, x + 24)) for x in pc_col), width=3)
    for dx in (210, 248, 286):
        dr.rounded_rectangle([dx, 462, dx + 26, 488], radius=3, fill=(64, 66, 70), outline=(28, 30, 32), width=2)
    dr.rounded_rectangle([46, 460, 156, 490], radius=3, fill=badge_bg)
    dr.text((54, 467), badge_txt[:10], fill=(246, 246, 240), font=_font(13, bold=True))

    # 4. [512..1024, 256..512] CRT Back Housing & Property Sticker
    for vy in range(282, 412, 14):
        dr.line([548, vy, 988, vy], fill=(30, 32, 36), width=5)
    dr.rounded_rectangle([654, 424, 884, 496], radius=4, fill=(232, 226, 206), outline=(64, 64, 68), width=2)
    dr.rectangle([660, 428, 878, 446], fill=accent_a)
    dr.text((674, 430), "HIGH VOLTAGE // CAUTION", fill=(248, 248, 245), font=_font(11, bold=True))
    dr.text((668, 454), f"MODEL: {badge_txt}", fill=(26, 28, 32), font=_font(13, bold=True))
    dr.text((668, 474), "WARNING: 3.5\" AMMO", fill=(168, 28, 24), font=_font(12, bold=True))

    # 5. [0..512, 512..768] Tripod / Heavy Steel Base / Armor
    base_patch = np.zeros((256, 512, 3), dtype=np.float32)
    for c in range(3):
        base_patch[..., c] = np.clip(metal_col[c] + grain[512:768, :512] * 18.0, 12, 240)
    im.paste(Image.fromarray(base_patch.astype(np.uint8), mode="RGB"), (0, 512))
    dr = ImageDraw.Draw(im)
    dr.rectangle([6, 518, 505, 761], outline=(146, 152, 162), width=3)
    for rx in range(28, 496, 48):
        for ry in (534, 742):
            dr.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=(168, 174, 184), outline=(28, 30, 34))

    # 6. [512..768, 512..768] Hazard / Accent Trim Plate
    _draw_hazard(dr, 512, 512, 767, 767, accent_a, accent_b, stripe_w=26)

    # 7. [768..1024, 512..768] Floppy Ammo Drum / Stacked Floppy Rack
    dr.rectangle([768, 512, 1023, 767], fill=(42, 46, 54), outline=(128, 134, 144), width=3)
    for fy in range(528, 754, 24):
        dr.rectangle([786, fy, 1006, fy + 16], fill=(24, 26, 32), outline=(142, 148, 160), width=1)
        dr.rectangle([818, fy + 2, 916, fy + 14], fill=(184, 192, 204))
        dr.rectangle([928, fy + 2, 994, fy + 14], fill=accent_a)

    # 8. [0..256, 768..1024] Perforated Gunmetal Barrel Shroud
    ux = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    br = 0.58 + 0.28 * np.cos(ux - 0.7) + 0.12 * np.cos(2.0 * ux) + 0.08 * grain[768:, :256]
    b_arr = np.zeros((256, 256, 3), dtype=np.uint8)
    tint = (0.82, 0.86, 0.94) if concept_id != "badass" else (0.64, 0.66, 0.72)
    for c in range(3):
        b_arr[..., c] = np.clip(br * 184.0 * tint[c], 14, 245).astype(np.uint8)
    im.paste(Image.fromarray(b_arr, mode="RGB"), (0, 768))
    dr = ImageDraw.Draw(im)
    for hx in range(28, 240, 40):
        for hy in range(794, 1004, 40):
            dr.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill=(16, 18, 22), outline=(138, 144, 156), width=2)

    # 9. [256..512, 768..1024] 90s Speaker Grille + Keyboard Keys Swatch
    dr.rectangle([256, 768, 511, 1023], fill=(42, 44, 48), outline=(146, 142, 128), width=4)
    # Dark perforated speaker mesh upper half [256..512, 768..912]
    for sx in range(274, 496, 12):
        for sy in range(784, 902, 12):
            dr.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(18, 20, 22))
    # Sculpted mechanical keycaps bottom half [256..512, 916..1023]
    for r_i in range(3):
        ky = 922 + r_i * 32
        for kx in range(264, 496, 24):
            dr.rounded_rectangle([kx, ky, kx + 20, ky + 26], radius=3, fill=(224, 214, 190), outline=(96, 90, 78), width=2)

    # 10. [512..768, 768..1024] Cables & Rubber Pads
    dr.rectangle([512, 768, 767, 1023], fill=(26, 28, 32))
    for cy in range(772, 1020, 10):
        dr.line([512, cy, 767, cy], fill=(44, 48, 54), width=3)

    # 11. [768..1024, 768..1024] Brushed Stainless Steel / Chrome Barrels
    ux2 = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    ch = 0.70 + 0.25 * np.cos(ux2 - 0.8) + 0.08 * np.cos(2.0 * ux2)
    c_arr = np.zeros((256, 256, 3), dtype=np.uint8)
    c_arr[..., 0] = np.clip(ch * 222.0, 30, 255).astype(np.uint8)
    c_arr[..., 1] = np.clip(ch * 228.0, 30, 255).astype(np.uint8)
    c_arr[..., 2] = np.clip(ch * 240.0, 35, 255).astype(np.uint8)
    im.paste(Image.fromarray(c_arr, mode="RGB"), (768, 768))

    out_path = os.path.join(out_dir, f"ds_{concept_id}_body.png")
    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_leds_texture(out_dir: str) -> str:
    im = Image.new("RGB", (256, 256), (0, 0, 0))
    dr = ImageDraw.Draw(im)

    def radial(x0: int, y0: int, edge: Tuple[int, int, int], core: Tuple[int, int, int]) -> None:
        for r in range(60, 0, -1):
            t = 1.0 - (r / 60.0)
            col = tuple(int(round(edge[k] + (core[k] - edge[k]) * (t ** 1.15))) for k in range(3))
            dr.ellipse([x0 + 64 - r, y0 + 64 - r, x0 + 64 + r, y0 + 64 + r], fill=col)

    radial(0, 0, (16, 128, 32), (138, 255, 158))
    radial(128, 0, (148, 74, 10), (255, 224, 88))
    radial(0, 128, (158, 18, 18), (255, 86, 76))
    radial(128, 128, (24, 175, 235), (210, 255, 255))

    path = os.path.join(out_dir, "ds_leds.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_floppy_texture(concept_id: str, out_dir: str) -> str:
    W = H = 512
    grain = _fbm(H, W, seed=700 + sum(ord(c) for c in concept_id), octaves=(2, 4, 8, 16))
    specs = {
        "retro":   ((38, 42, 50),   (242, 236, 218), (212, 52, 42), "LOL.BAT",     "AUTOSENTRY // 1.44M"),
        "classic": ((34, 106, 238), (246, 250, 255), (20, 212, 148), "BOOT_95.DSK", "VERBATIM // 3X TURBO"),
        "badass":  ((28, 30, 36),   (228, 224, 216), (176, 22, 26), "KILL_32.EXE", "ARMOR-PIERCING 3.5\""),
        "msdos":   ((212, 204, 182),(248, 246, 238), (206, 46, 34), "MS-DOS 6.22", "FORMAT C: /S // DISK1"),
    }
    shell_rgb, lbl_bg, stripe_rgb, title_txt, sub_txt = specs[concept_id]

    arr = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        arr[..., c] = np.clip(shell_rgb[c] + grain * 10.0, 10, 245)
    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # Q1: Front Face
    edge_col = (92, 248, 255) if concept_id == "classic" else (112, 118, 128)
    dr.rectangle([4, 4, 251, 251], outline=edge_col, width=4 if concept_id == "classic" else 2)
    dr.rectangle([40, 0, 214, 78], fill=(22, 24, 28), outline=(14, 16, 20), width=2)
    dr.polygon([(20, 16), (30, 34), (10, 34)], fill=(120, 126, 138))
    dr.text((222, 16), "HD", fill=(162, 248, 255) if concept_id == "classic" else (142, 148, 160), font=_font(13, bold=True))
    dr.rounded_rectangle([24, 84, 232, 242], radius=8, fill=lbl_bg, outline=(160, 156, 144), width=2)
    dr.rounded_rectangle([26, 86, 230, 112], radius=6, fill=stripe_rgb)
    dr.rectangle([26, 98, 230, 112], fill=stripe_rgb)
    dr.text((34, 91), sub_txt, fill=(248, 246, 240), font=_font(12, bold=True))
    for ry in (142, 176, 210):
        dr.line([34, ry, 222, ry], fill=(168, 184, 214), width=1)
    dr.text((32, 132), title_txt, fill=(18, 20, 28), font=_font(30 if len(title_txt) > 8 else 38, bold=True))
    dr.text((34, 186), "C:\\> EJECT_TARGET", fill=(64, 72, 88), font=_font(14, bold=True))
    dr.rectangle([10, 218, 24, 238], fill=(12, 12, 14), outline=(92, 96, 106))
    dr.rectangle([232, 218, 246, 238], fill=(12, 12, 14), outline=(92, 96, 106))

    # Q2: Back Face + Spindle Hub
    dr.rectangle([259, 4, 507, 251], outline=edge_col, width=4 if concept_id == "classic" else 2)
    dr.rectangle([292, 0, 476, 82], fill=(22, 24, 28), outline=(14, 16, 20), width=2)
    cx, cy = 384, 156
    dr.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=(18, 20, 24), outline=(96, 102, 114), width=2)
    yy, xx = np.mgrid[0:104, 0:104].astype(np.float32)
    dx, dy = xx - 51.5, yy - 51.5
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    sheen = 0.68 + 0.24 * np.cos(2.0 * ang - 0.7) + 0.08 * np.sin(4.0 * ang)
    hub_arr = np.zeros((104, 104, 4), dtype=np.uint8)
    for c in range(3):
        hub_arr[..., c] = np.clip(sheen * 212.0, 25, 250).astype(np.uint8)
    hub_arr[..., 3] = np.where(rr <= 46.0, 255, 0).astype(np.uint8)
    hub_im = Image.fromarray(hub_arr, mode="RGBA")
    hd = ImageDraw.Draw(hub_im)
    hd.rounded_rectangle([42, 42, 61, 61], radius=2, fill=(18, 20, 24, 255), outline=(140, 146, 158, 255))
    hd.rounded_rectangle([67, 45, 83, 58], radius=2, fill=(24, 20, 18, 255), outline=(140, 146, 158, 255))
    im.paste(hub_im, (cx - 52, cy - 52), hub_im)

    # Q3: Brushed Stainless Shutter
    ux = np.linspace(0.0, 1.0, 256, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    brush = 0.70 + 0.20 * np.sin(ux * math.pi * 2.4 - 0.4) + 0.04 * np.sin(vy * 300.0)
    sh_arr = np.zeros((256, 256, 3), dtype=np.uint8)
    sh_arr[..., 0] = np.clip(brush * 216.0, 24, 250).astype(np.uint8)
    sh_arr[..., 1] = np.clip(brush * 222.0, 24, 252).astype(np.uint8)
    sh_arr[..., 2] = np.clip(brush * 234.0, 28, 255).astype(np.uint8)
    sh_im = Image.fromarray(sh_arr, mode="RGB")
    sd = ImageDraw.Draw(sh_im)
    sd.rounded_rectangle([144, 30, 208, 224], radius=5, fill=(32, 24, 22), outline=(145, 150, 160), width=3)
    sd.rounded_rectangle([38, 44, 58, 210], radius=3, outline=(145, 152, 165), width=2)
    im.paste(sh_im, (0, 256))

    out_path = os.path.join(out_dir, f"ds_{concept_id}_floppy.png")
    im.save(out_path, "PNG", optimize=True)
    return out_path


# ==============================================================================
# POWER-OF-2 512x512 CRT SCREENS (Sharp on BOTH WebGL1 and WebGL2 + Mipmaps!)
# ==============================================================================
def _crt_base(tint: Tuple[float, float, float]) -> np.ndarray:
    W, H = 512, 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.5) / (H * 0.5)
    vig = np.clip(1.0 - 0.32 * (nx * nx * 0.7 + ny * ny * 0.9), 0.40, 1.0)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        arr[..., c] = tint[c] * vig
    return arr


def _finish_crt(base_arr: np.ndarray, layer: Image.Image, scan_str: float = 0.22) -> Image.Image:
    W, H = 512, 512
    txt = np.asarray(layer, dtype=np.float32)
    bloom = np.asarray(layer.filter(ImageFilter.GaussianBlur(radius=3.5)), dtype=np.float32)
    a = txt[..., 3:4] / 255.0
    out = base_arr + bloom[..., :3] * (bloom[..., 3:4] / 255.0) * 0.52
    out = out * (1.0 - a) + txt[..., :3] * a
    scan = np.ones((H, 1, 1), dtype=np.float32)
    scan[1::2, 0, 0] = 1.0 - scan_str
    out *= scan
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([3, 3, W - 4, H - 4], radius=18, outline=(10, 14, 12), width=6)
    return im


def build_crt_screens_for_concept(concept_id: str, out_dir: str) -> Dict[str, str]:
    W, H = 512, 512
    f_huge = _font(48, bold=True, mono=True)
    f_big = _font(32, bold=True, mono=True)
    f_med = _font(24, bold=True, mono=True)
    f_sm = _font(18, bold=True, mono=True)

    tint_map = {
        "retro":   (4.0, 20.0, 9.0),
        "classic": (14.0, 10.0, 3.0),
        "badass":  (24.0, 4.0, 4.0),
        "msdos":   (6.0, 12.0, 28.0),
    }
    fg_map = {
        "retro":   ((82, 255, 118, 255), (38, 206, 74, 255)),
        "classic": ((255, 214, 86, 255), (224, 158, 42, 255)),
        "badass":  ((255, 72, 66, 255), (224, 34, 34, 255)),
        "msdos":   ((250, 252, 255, 255), (96, 228, 255, 255)),
    }
    tint = tint_map[concept_id]
    p_hi, p_mid = fg_map[concept_id]
    paths: Dict[str, str] = {}

    # 1. OFF
    im_off = Image.fromarray(_crt_base((4.0, 6.0, 5.0)).astype(np.uint8), mode="RGB")
    d0 = ImageDraw.Draw(im_off)
    d0.line([48, 66, 178, 28], fill=(24, 30, 28), width=10)
    d0.rounded_rectangle([3, 3, W - 4, H - 4], radius=18, outline=(8, 10, 10), width=6)
    p = os.path.join(out_dir, f"ds_{concept_id}_scr_off.png")
    im_off.save(p, "PNG", optimize=True)
    paths["off"] = p

    # 2. STATIC
    rng = np.random.default_rng(900 + sum(ord(c) for c in concept_id))
    arr_s = _crt_base(tint)
    noise = rng.uniform(0.0, 1.0, size=(H // 2, W // 4)).astype(np.float32)
    nup = np.asarray(Image.fromarray(noise, mode="F").resize((W, H), Image.NEAREST))
    yy = np.arange(H, dtype=np.float32)[:, None]
    band = np.exp(-((yy - H * 0.48) ** 2) / 1800.0) + 0.35
    val = (nup > 0.35).astype(np.float32) * nup * band * 210.0
    arr_s[..., 0] += val * (1.0 if concept_id == "badass" else 0.72)
    arr_s[..., 1] += val * (0.35 if concept_id == "badass" else 0.96)
    arr_s[..., 2] += val * (0.30 if concept_id in ("classic", "badass") else 0.85)
    im_st = _finish_crt(arr_s, Image.new("RGBA", (W, H), (0, 0, 0, 0)), scan_str=0.30)
    p = os.path.join(out_dir, f"ds_{concept_id}_scr_static.png")
    im_st.save(p, "PNG", optimize=True)
    paths["static"] = p

    # 3. ACTIVE
    base = _crt_base(tint)
    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    if concept_id == "retro":
        td.rectangle([18, 20, W - 18, 66], fill=(24, 118, 44, 225))
        td.text((28, 30), "TF-SENTRY OS v2.9 // LOL.BAT", fill=p_hi, font=f_med)
        cx, cy = 138, 286
        for rr in (42, 82, 118):
            td.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=p_mid, width=3)
        td.line([cx - 122, cy, cx + 122, cy], fill=p_mid, width=2)
        td.line([cx, cy - 122, cx, cy + 122], fill=p_mid, width=2)
        td.polygon([(cx + 42, cy - 64), (cx + 60, cy - 46), (cx + 42, cy - 28), (cx + 24, cy - 46)], outline=p_hi, width=4)
        td.text((272, 108), "ARMED", fill=p_hi, font=f_huge)
        td.text((272, 174), "AMMO: LOL.BAT", fill=p_mid, font=f_med)
        td.text((272, 218), "SWEEP: +/-60", fill=p_mid, font=f_med)
        td.text((272, 262), "LOCK: ACTIVE", fill=p_hi, font=f_med)
        td.rectangle([268, 340, 490, 392], fill=(42, 220, 82, 230))
        td.text((280, 353), ">> EJECT READY", fill=(8, 22, 10, 255), font=f_med)
    elif concept_id == "classic":
        # Authentic 1994 Classic Retro Win95/BIOS + Messenger Service hybrid!
        td.rectangle([20, 20, W - 20, 62], fill=(24, 58, 146, 240))
        td.text((32, 28), "Messenger Service // LAB-PC", fill=(255, 255, 255, 255), font=f_med)
        td.text((28, 86), "PhoenixBIOS 4.0 // 486DX2-66", fill=p_mid, font=f_sm)
        td.text((28, 126), "65536K OK  |  A:\\BOOT_95.DSK", fill=p_hi, font=f_med)
        td.rectangle([28, 180, W - 28, 344], fill=(24, 30, 42, 220), outline=p_hi, width=3)
        td.text((46, 200), "Sending NET SEND.", fill=p_hi, font=f_big)
        td.text((46, 250), "Message: WHERE'S THE DISK?", fill=(255, 255, 255, 255), font=f_med)
        td.rectangle([188, 294, 324, 330], fill=p_mid)
        td.text((234, 300), "OK", fill=(16, 18, 22, 255), font=f_med)
        td.text((28, 384), "C:\\> SENTRY.SYS /TURBO _", fill=p_hi, font=f_big)
        td.text((28, 444), "TWIN SPEAKER CANNONS: ARMED", fill=p_mid, font=f_med)
    elif concept_id == "badass":
        td.rectangle([18, 18, W - 18, 66], fill=(178, 18, 22, 235))
        td.text((28, 30), "KILL_32.EXE // TERMINATE", fill=(255, 242, 220, 255), font=f_med)
        cx, cy = W // 2, 274
        for rr in (54, 108, 152):
            td.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=p_hi, width=4)
        td.line([cx - 180, cy, cx - 28, cy], fill=p_hi, width=5)
        td.line([cx + 28, cy, cx + 180, cy], fill=p_hi, width=5)
        td.line([cx, cy - 168, cx, cy - 28], fill=p_hi, width=5)
        td.line([cx, cy + 28, cx, cy + 168], fill=p_hi, width=5)
        td.text((26, 86), "TGT LOCKED", fill=p_hi, font=f_med)
        td.text((342, 86), "RPM: 1800", fill=p_hi, font=f_med)
        td.text((44, 448), "GATLING SHREDDER ARMED", fill=(255, 206, 68, 255), font=f_big)
    else:  # msdos
        td.rectangle([14, 14, W - 14, 62], fill=(22, 92, 206, 245))
        td.text((24, 24), "MS-DOS 6.22 // SENTRY_MG.BAT", fill=(255, 255, 255, 255), font=f_med)
        td.text((22, 82), "Microsoft(R) MS-DOS(R) 6.22", fill=p_mid, font=f_sm)
        td.text((22, 118), "C:\\> LOADHIGH FLOPPYMG.EXE", fill=p_hi, font=f_med)
        td.text((22, 162), "C:\\> FORMAT C: /AUTOTARGET", fill=(255, 218, 72, 255), font=f_med)
        td.text((22, 208), "C:\\> COPY A:\\*.* ENEMY", fill=p_hi, font=f_med)
        td.text((22, 260), " EJECTING 1.44MB STORM...", fill=(92, 255, 138, 255), font=f_med)
        td.text((22, 306), " 148 DISK(S) COPIED [MAX]", fill=(92, 255, 138, 255), font=f_med)
        td.rectangle([20, 368, 492, 464], fill=(182, 30, 28, 230))
        td.text((34, 396), "C:\\> FIRE_EVERYWHERE.BAT", fill=(255, 255, 255, 255), font=f_big)
    im_act = _finish_crt(base, tl)
    p = os.path.join(out_dir, f"ds_{concept_id}_scr_active.png")
    im_act.save(p, "PNG", optimize=True)
    paths["active"] = p

    # 4. FIRE
    base_f = _crt_base((48.0, 14.0, 8.0) if concept_id != "msdos" else (12.0, 32.0, 72.0))
    tf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tdf = ImageDraw.Draw(tf)
    tdf.rectangle([18, 18, W - 18, H - 18], outline=(80, 255, 220, 255), width=10)
    tdf.rectangle([28, 176, W - 28, 336], fill=(224, 38, 28, 245))
    tdf.text((46, 200), "FIRING FLOPPIES!", fill=(255, 255, 255, 255), font=f_huge)
    tdf.text((66, 272), ">>> HYPER EJECT 3X <<<", fill=(140, 255, 245, 255), font=f_big)
    tdf.text((38, 66), "C:\\> NET SEND * DIE" if concept_id == "msdos" else "TARGET LOCKED // 600 RPM", fill=(130, 255, 190, 255), font=f_big)
    tdf.text((44, 404), "3X OVERDRIVE  //  1.44MB STORM", fill=(255, 212, 84, 255), font=f_med)
    im_f = _finish_crt(base_f, tf, scan_str=0.18)
    p = os.path.join(out_dir, f"ds_{concept_id}_scr_fire.png")
    im_f.save(p, "PNG", optimize=True)
    paths["fire"] = p

    # 5. FATAL
    base_d = _crt_base((8.0, 28.0, 146.0) if concept_id in ("classic", "msdos") else (52.0, 4.0, 4.0))
    td2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tdd = ImageDraw.Draw(td2)
    tdd.rectangle([108, 48, 404, 98], fill=(235, 235, 235, 245))
    tdd.text((130, 58), "FATAL EXCEPTION", fill=(18, 34, 148, 255), font=f_big)
    tdd.text((34, 146), "ERROR 0xDEAD : OVERLOAD", fill=(255, 255, 255, 255), font=f_big)
    tdd.text((34, 214), "CORE DUMPED TO FLOPPY", fill=(255, 224, 128, 255), font=f_med)
    tdd.text((34, 274), "DETONATING 1.44MB RESERVE", fill=(255, 112, 96, 255), font=f_med)
    cx, cy = 264, 260
    for ang_d in (18, 62, 114, 158, 212, 265, 312, 345):
        r = math.radians(ang_d)
        tdd.line([cx, cy, cx + int(math.cos(r) * 280), cy + int(math.sin(r) * 280)], fill=(255, 255, 255, 220), width=4)
    im_d = _finish_crt(base_d, td2, scan_str=0.22)
    p = os.path.join(out_dir, f"ds_{concept_id}_scr_fatal.png")
    im_d.save(p, "PNG", optimize=True)
    paths["fatal"] = p

    return paths
