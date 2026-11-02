"""Procedural texture, CRT screen sequence, and fallback sprite synthesis for the
"WHERE'S THE DISK?" (LOL.BAT / NET SEND) weapon & deployable 90s PC in BakersfieldQuake.

All lit model textures are baked at ~0.38x-0.46x brightness to compensate for BakersfieldQuake's
DarkPlaces scene brightness (~2.5x via r_hdr_scenebrightness), preventing highlight blowout while
preserving rich contrast. Self-illuminated CRT phosphor textures are tuned so scanlines and green/white
phosphor text stay razor-sharp under rgbGen identity + a dedicated additive CRT glow stage.
"""
import math
import os
import random
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _font(size, bold=True, mono=True):
    if mono:
        cands = ["consolab.ttf", "lucon.ttf", "courbd.ttf"] if bold else ["consola.ttf", "lucon.ttf", "cour.ttf"]
    else:
        cands = [" markers", "comicbd.ttf", "tahomabd.ttf", "arialbd.ttf"] if bold else ["comic.ttf", "tahoma.ttf", "arial.ttf"]
    for nm in cands:
        p = os.path.join(r"C:\Windows\Fonts", nm.strip())
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm_noise(h, w, seed=42, octaves=(4, 8, 16, 32)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tot = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        grid = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(grid, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tot += amp
    return acc / max(tot, 1e-6)


# ==============================================================================
# 1. 3.5" FLOPPY DISK TEXTURE ATLAS (progs/netsend_disk.png, 512x512)
# ==============================================================================
def build_disk_texture(out_dir):
    """512x512 4-quadrant atlas for the 3.5" 'LOL.BAT' floppy disk (baked ~0.43x for 2.5x DarkPlaces HDR):
      Q1 [0..256,   0..256]   (u:0.0..0.5, v:0.0..0.5): Front shell + recessed white paper label reading 'LOL.BAT'
      Q2 [256..512, 0..256]   (u:0.5..1.0, v:0.0..0.5): Back shell + brushed steel spindle hub + rear shutter slot
      Q3 [0..256,   256..512] (u:0.0..0.5, v:0.5..1.0): Brushed stainless-steel sliding metal shutter + media window
      Q4 [256..512, 256..512] (u:0.5..1.0, v:0.5..1.0): Bevelled dark plastic rim swatch + magnetic disk media
    """
    W = H = 512
    DIM = 0.64
    grain = _fbm_noise(H, W, seed=305, octaves=(2, 4, 8, 16))

    # Base micro-textured charcoal-black 3.5" floppy ABS plastic (raw ~68 -> dimmed ~44)
    base_v = np.clip(68.0 + 8.5 * grain, 44.0, 94.0)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[..., 0] = base_v * 0.95
    arr[..., 1] = base_v * 0.98
    arr[..., 2] = base_v * 1.07

    im = Image.fromarray((arr * DIM).clip(0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    def sc(rgb, mult=DIM):
        return tuple(max(0, min(255, int(round(c * mult)))) for c in rgb)

    # --- Q1 [0..256, 0..256]: FRONT FACE ---
    # Subtle outer bevel highlight & recessed shutter track at top (y = 0..76)
    dr.rectangle([3, 3, 252, 252], outline=sc((96, 102, 114)), width=2)
    dr.rectangle([42, 0, 218, 76], fill=sc((36, 38, 44)), outline=sc((22, 24, 28)), width=2)
    # Embossed directional insertion arrow (top-left) & "HD" mark (top-right)
    dr.polygon([(20, 16), (30, 32), (10, 32)], fill=sc((88, 92, 102)))
    dr.rectangle([226, 16, 246, 34], outline=sc((92, 96, 108)), width=1)
    dr.text((229, 17), "HD", fill=sc((110, 116, 128)), font=_font(12, bold=True))

    # Write-protect square notch window (bottom-left) & HD detect hole (bottom-right)
    dr.rectangle([10, 218, 26, 240], fill=sc((14, 15, 18)), outline=sc((82, 86, 96)), width=1)
    dr.rectangle([230, 218, 246, 240], fill=sc((14, 15, 18)), outline=sc((82, 86, 96)), width=1)

    # Recessed label pocket shadow + large warm-white paper label (x: 26..230, y: 84..246)
    dr.rounded_rectangle([24, 82, 232, 248], radius=7, fill=sc((24, 25, 30)))
    dr.rounded_rectangle([27, 85, 229, 245], radius=6, fill=sc((242, 238, 222)), outline=sc((185, 180, 166)), width=2)

    # Classic 90s floppy label header stripe (crimson red + thin navy ruled lines)
    dr.rounded_rectangle([29, 87, 227, 106], radius=4, fill=sc((212, 46, 42)))
    dr.rectangle([29, 98, 227, 106], fill=sc((212, 46, 42)))
    dr.text((36, 89), "INDEX // 3.5\" MF-2HD", fill=sc((248, 244, 236)), font=_font(11, bold=True))

    for ry in (134, 168, 202, 228):
        dr.line([34, ry, 222, ry], fill=sc((168, 184, 214)), width=1)

    # Bold Sharpie / Dot-Matrix "LOL.BAT" drawn big on its own layer with slight -3 deg hand-slapped angle
    lbl_layer = Image.new("RGBA", (220, 120), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lbl_layer)
    f_lol = _font(44, bold=True, mono=True)
    # Chunky permanent marker ink (deep blue-black, super high contrast against the warm-white paper)
    ink_main = sc((14, 16, 26)) + (255,)
    ink_bleed = sc((28, 32, 52)) + (150,)
    ld.text((11, 27), "LOL.BAT", fill=ink_bleed, font=f_lol, stroke_width=3, stroke_fill=ink_bleed)
    ld.text((10, 26), "LOL.BAT", fill=ink_main, font=f_lol, stroke_width=2, stroke_fill=ink_main)
    # Underline flourish + tiny dot-matrix batch hint below
    ld.line([14, 79, 198, 76], fill=ink_main, width=4)
    ld.line([24, 85, 182, 83], fill=sc((190, 36, 32)) + (235,), width=2)
    ld.text((22, 92), "C:\\> NET SEND * LOL", fill=sc((42, 46, 62)) + (245,), font=_font(14, bold=True, mono=True))

    lbl_rot = lbl_layer.rotate(2.4, resample=Image.BICUBIC, expand=False)
    im.paste(lbl_rot, (19, 108), lbl_rot)

    # --- Q2 [256..512, 0..256]: BACK FACE (metal hub + wide rear shutter recess) ---
    dr.rectangle([259, 3, 508, 252], outline=sc((92, 98, 110)), width=2)
    # Deep rear shutter slide pocket
    dr.rectangle([292, 0, 476, 82], fill=sc((32, 34, 40)), outline=sc((20, 22, 26)), width=2)
    # Circular central recess well for metal drive spindle hub
    cx, cy = 384, 154
    dr.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=sc((22, 24, 28)), outline=sc((78, 82, 92)), width=2)
    # Anisotropic brushed steel spindle hub disc (r = 46)
    hub_im = Image.new("RGBA", (104, 104), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:104, 0:104].astype(np.float32)
    dx, dy = xx - 51.5, yy - 51.5
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    sheen = 0.68 + 0.22 * np.cos(2.0 * ang - 0.7) + 0.08 * np.sin(4.0 * ang) + 0.04 * grain[:104, :104]
    h_rgb = np.clip(sheen * 245.0 * DIM, 25, 255)
    hub_arr = np.zeros((104, 104, 4), dtype=np.uint8)
    hub_arr[..., 0] = h_rgb * 0.97
    hub_arr[..., 1] = h_rgb * 0.99
    hub_arr[..., 2] = np.clip(h_rgb * 1.04, 0, 255)
    hub_arr[..., 3] = np.where(rr <= 46.0, 255, 0).astype(np.uint8)
    hub_im = Image.fromarray(hub_arr, mode="RGBA")
    hd = ImageDraw.Draw(hub_im)
    # Center square spindle hole + offset rectangular drive-chuck slot
    hd.rounded_rectangle([42, 42, 61, 61], radius=2, fill=sc((18, 20, 24)) + (255,), outline=sc((120, 126, 138)) + (255,), width=1)
    hd.rounded_rectangle([67, 45, 83, 58], radius=2, fill=sc((26, 20, 18)) + (255,), outline=sc((120, 126, 138)) + (255,), width=1)
    hd.ellipse([6, 6, 97, 97], outline=sc((250, 252, 255)) + (255,), width=1)
    im.paste(hub_im, (cx - 52, cy - 52), hub_im)

    # Molded plastic grip lines on lower back shell + write-protect windows
    for ly in range(218, 244, 6):
        dr.line([316, ly, 452, ly], fill=sc((42, 45, 52)), width=2)
    dr.rectangle([266, 218, 282, 240], fill=sc((14, 15, 18)), outline=sc((82, 86, 96)), width=1)
    dr.rectangle([486, 218, 502, 240], fill=sc((14, 15, 18)), outline=sc((82, 86, 96)), width=1)

    # --- Q3 [0..256, 256..512]: BRUSHED STAINLESS STEEL SHUTTER ---
    ux = np.linspace(0.0, 1.0, 256, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    brush = (
        0.72
        + 0.18 * np.sin(ux * math.pi * 2.2 - 0.4)
        + 0.07 * np.cos(ux * math.pi * 5.0)
        + 0.035 * np.sin(vy * 320.0)
        + 0.03 * grain[256:, :256]
    )
    sh_arr = np.zeros((256, 256, 3), dtype=np.uint8)
    sh_arr[..., 0] = np.clip(brush * 238.0 * DIM, 20, 255).astype(np.uint8)
    sh_arr[..., 1] = np.clip(brush * 244.0 * DIM, 20, 255).astype(np.uint8)
    sh_arr[..., 2] = np.clip(brush * 255.0 * DIM, 24, 255).astype(np.uint8)
    sh_im = Image.fromarray(sh_arr, mode="RGB")
    sd = ImageDraw.Draw(sh_im)
    sd.rectangle([2, 2, 253, 253], outline=sc((255, 255, 255)), width=2)
    # Rectangular read/write window cutout showing dark glossy Mylar magnetic disc underneath
    sd.rounded_rectangle([144, 30, 208, 224], radius=5, fill=sc((32, 24, 22)), outline=sc((135, 140, 150)), width=3)
    sd.line([150, 40, 202, 214], fill=sc((58, 44, 38)), width=2)
    # Stamped grip indentation bar on left side of shutter
    sd.rounded_rectangle([38, 44, 58, 210], radius=3, outline=sc((145, 152, 165)), width=2)
    im.paste(sh_im, (0, 256))

    # --- Q4 [256..512, 256..512]: PLASTIC RIM / BEVEL SWATCH ---
    dr.rectangle([256, 256, 511, 511], fill=sc((52, 55, 64)))
    for rx in range(264, 508, 12):
        dr.line([rx, 256, rx, 511], fill=sc((68, 72, 82)), width=2)

    path = os.path.join(out_dir, "netsend_disk.png")
    im.save(path, "PNG", optimize=True)
    return path


# ==============================================================================
# 2. QUAKE RANGER GLOVED HAND TEXTURE (progs/netsend_hand.png, 512x512)
# ==============================================================================
def build_hand_texture(out_dir):
    """512x512 Quake Ranger Leather Glove, Bronze Knuckle Plate & Riveted Gauntlet Cuff (dimmed ~0.46x)."""
    W = H = 512
    DIM = 0.68
    arr = np.zeros((H, W, 3), dtype=np.float32)
    grain = _fbm_noise(H, W, seed=409, octaves=(2, 4, 8, 16, 32))

    # Q1 [0..256, 0..256]: Warm Quake brown leather glove
    lth = 1.0 + 0.16 * grain[:256, :256]
    arr[:256, :256, 0] = np.clip(156.0 * lth, 45, 235)
    arr[:256, :256, 1] = np.clip(104.0 * lth, 30, 175)
    arr[:256, :256, 2] = np.clip(68.0 * lth, 20, 125)

    # Q2 [0..256, 256..512]: Suede palm pad & finger joint creases
    vy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    creases = 1.0 - 0.26 * (
        np.exp(-((vy - 0.33) ** 2) / 0.0014) + np.exp(-((vy - 0.66) ** 2) / 0.0014)
    )
    plm = (118.0 + 16.0 * grain[:256, 256:]) * creases
    arr[:256, 256:, 0] = plm * 1.12
    arr[:256, 256:, 1] = plm * 0.88
    arr[:256, 256:, 2] = plm * 0.68

    # Q3 [256..512, 0..256]: Riveted Quake Bronze-Iron Gauntlet Cuff
    ux = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    brz = 0.72 + 0.22 * np.cos(ux - 1.0) + 0.11 * grain[256:, :256]
    arr[256:, :256, 0] = np.clip(brz * 176.0, 40, 245)
    arr[256:, :256, 1] = np.clip(brz * 138.0, 32, 210)
    arr[256:, :256, 2] = np.clip(brz * 92.0, 22, 155)

    # Q4 top [256..384, 256..512]: Hammered Brass Knuckle Plate
    kn = 0.80 + 0.15 * grain[256:384, 256:]
    arr[256:384, 256:, 0] = np.clip(kn * 224.0, 60, 255)
    arr[256:384, 256:, 1] = np.clip(kn * 176.0, 45, 230)
    arr[256:384, 256:, 2] = np.clip(kn * 96.0, 25, 145)

    # Q4 bottom [384..512, 256..512]: Ranger Olive-Tan Combat Sleeve
    sy = np.arange(128, dtype=np.float32)[:, None]
    rib = 0.88 + 0.12 * np.sin(sy * 0.45)
    slv = (108.0 + 15.0 * grain[384:, 256:]) * rib
    arr[384:, 256:, 0] = slv * 0.96
    arr[384:, 256:, 1] = slv * 1.04
    arr[384:, 256:, 2] = slv * 0.72

    im = Image.fromarray(np.clip(arr * DIM, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    def sc(rgb):
        return tuple(max(0, min(255, int(round(c * DIM)))) for c in rgb)

    for sx_l in (34, 222):
        for sy_d in range(12, 244, 14):
            dr.line([sx_l, sy_d, sx_l, sy_d + 7], fill=sc((212, 168, 114)), width=2)

    for strap_y in (324, 434):
        dr.rectangle([0, strap_y, 255, strap_y + 24], fill=sc((78, 52, 34)), outline=sc((38, 24, 16)), width=2)
        dr.rounded_rectangle([106, strap_y - 3, 150, strap_y + 27], radius=3, outline=sc((238, 194, 96)), width=3)
    for rx_r in range(22, 246, 36):
        for ry_r in (278, 488):
            dr.ellipse([rx_r - 5, ry_r - 5, rx_r + 5, ry_r + 5], fill=sc((215, 188, 136)), outline=sc((46, 36, 26)))

    for ki in range(4):
        kx = 288 + ki * 56
        dr.ellipse([kx - 16, 304, kx + 16, 336], fill=sc((245, 202, 112)), outline=sc((96, 72, 34)), width=2)

    path = os.path.join(out_dir, "netsend_hand.png")
    im.save(path, "PNG", optimize=True)
    return path


# ==============================================================================
# 3. EARLY-90s BEIGE PC & STAND TEXTURE ATLAS (progs/netsend_pc_body.png, 1024x1024)
# ==============================================================================
def build_pc_body_texture(out_dir):
    """1024x1024 texture atlas for progs/netsend_pc.md3 (dimmed ~0.40x for DarkPlaces 2.5x HDR):
      [0..512,   0..256]    (u:0.0..0.5, v:0.00..0.25): Desktop Case Front Faceplate (vents, 3.5" bay, buttons, badge)
      [512..1024,0..128]    (u:0.5..1.0, v:0.00..0.125): Desktop Case Rear I/O Panel (PSU fan, ports, slots)
      [512..1024,128..256]  (u:0.5..1.0, v:0.125..0.25): Beige Painted Steel Case Sides/Top w/ vents
      [0..512,   256..640]  (u:0.0..0.5, v:0.25..0.625): CRT Monitor Front Bezel (aperture bevel, blank badge, dials)
      [512..1024,256..640]  (u:0.5..1.0, v:0.25..0.625): CRT Monitor Rounded Back Housing (heat louvers, FCC label)
      [0..320,   640..832]  (u:0.0..0.3125,v:0.625..0.8125): Sculpted Mechanical Keycaps Grid
      [320..512, 640..832]  (u:0.3125..0.5,v:0.625..0.8125): Beige Keyboard Wedge Shell & Lock Strip
      [512..800, 640..832]  (u:0.5..0.781, v:0.625..0.8125): Putty-Beige School Computer Stand / Desk Panels
      [800..1024,640..736]  (u:0.781..1.0, v:0.625..0.719): Beige 6-Outlet Surge Strip
      [800..1024,736..832]  (u:0.781..1.0, v:0.719..0.8125): Dark Rubber Feet / Brackets / Recess Dark Plastic
      [0..256,   832..1024] (u:0.00..0.25, v:0.8125..1.0): Matte Black AC Power Cord
      [256..512, 832..1024] (u:0.25..0.50, v:0.8125..1.0): Coiled Putty-Grey Keyboard / VGA Cable
      [512..768, 832..1024] (u:0.50..0.75, v:0.8125..1.0): Dark Coax Network Cable w/ Silver BNC Ring
      [768..1024,832..1024] (u:0.75..1.00, v:0.8125..1.0): Polished Chrome Telescoping Antenna Rod
    """
    W = H = 1024
    DIM = 0.44
    grain = _fbm_noise(H, W, seed=512, octaves=(4, 8, 16, 32))

    # Classic yellowed early-90s warm putty-beige ABS plastic
    beige_r = np.clip(218.0 + 8.0 * grain, 185, 242)
    beige_g = np.clip(208.0 + 7.5 * grain, 175, 232)
    beige_b = np.clip(182.0 + 7.0 * grain, 150, 206)
    arr = np.stack([beige_r, beige_g, beige_b], axis=-1)

    im = Image.fromarray(np.clip(arr * DIM, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    def sc(rgb, mult=DIM):
        return tuple(max(0, min(255, int(round(c * mult)))) for c in rgb)

    # --- 1. Desktop Case Front Faceplate [0..512, 0..256] ---
    dr.rectangle([4, 4, 507, 251], fill=sc((218, 208, 182)), outline=sc((242, 234, 210)), width=3)
    dr.line([16, 42, 496, 42], fill=sc((164, 154, 132)), width=3)
    dr.line([16, 45, 496, 45], fill=sc((238, 230, 206)), width=2)

    # Vertical cooling louver slots on left front
    for lx in range(28, 176, 12):
        dr.rounded_rectangle([lx, 62, lx + 6, 224], radius=2, fill=sc((46, 44, 40)), outline=sc((158, 148, 128)), width=1)

    # Power button, Turbo button, Reset button & little "486 DX2" case badge
    dr.rounded_rectangle([194, 66, 242, 114], radius=4, fill=sc((196, 186, 162)), outline=sc((92, 86, 74)), width=2)
    dr.text((203, 83), "PWR", fill=sc((72, 68, 58)), font=_font(14, bold=True))
    dr.rounded_rectangle([194, 128, 226, 156], radius=3, fill=sc((196, 186, 162)), outline=sc((92, 86, 74)), width=2)
    dr.text((198, 136), "TRB", fill=sc((72, 68, 58)), font=_font(11, bold=True))
    dr.ellipse([232, 134, 248, 150], fill=sc((168, 62, 54)), outline=sc((72, 44, 40)), width=2)
    # Recessed blank/clone case badge ("SCHOOL PC #04")
    dr.rounded_rectangle([194, 176, 252, 224], radius=3, fill=sc((184, 176, 154)), outline=sc((128, 120, 102)), width=2)
    dr.rectangle([200, 182, 246, 198], fill=sc((48, 76, 128)))
    dr.text((204, 184), "486DX", fill=sc((238, 236, 224)), font=_font(12, bold=True))
    dr.text((202, 203), "66MHz", fill=sc((68, 64, 56)), font=_font(12, bold=True))

    # 3.5" Floppy Drive Bay (right half of case front: x = 272..492, y = 58..178)
    dr.rounded_rectangle([272, 58, 492, 178], radius=4, fill=sc((202, 192, 168)), outline=sc((116, 108, 92)), width=3)
    # Recessed horizontal floppy insertion slot + center finger scoop
    dr.rectangle([288, 102, 476, 124], fill=sc((24, 24, 28)), outline=sc((136, 128, 110)), width=2)
    dr.rounded_rectangle([356, 92, 408, 134], radius=5, fill=sc((32, 32, 36)), outline=sc((146, 138, 118)), width=2)
    # Rectangular grey floppy eject button & unlit LED housing
    dr.rounded_rectangle([438, 134, 474, 156], radius=2, fill=sc((168, 164, 150)), outline=sc((76, 72, 62)), width=2)
    dr.rectangle([300, 140, 318, 150], fill=sc((42, 46, 38)), outline=sc((96, 90, 78)), width=1)
    dr.text((328, 140), "1.44 MB", fill=sc((92, 86, 74)), font=_font(12, bold=True))
    # Lower 5.25" blank filler plate seam
    dr.rectangle([272, 186, 492, 234], fill=sc((210, 200, 176)), outline=sc((132, 124, 106)), width=2)

    # --- 2a. Desktop Case Rear I/O Panel [512..1024, 0..128] ---
    dr.rectangle([512, 0, 1023, 127], fill=sc((152, 148, 138)), outline=sc((96, 92, 84)), width=3)
    # PSU circular fan exhaust grille + black IEC power socket
    fcx, fcy = 582, 64
    dr.ellipse([fcx - 42, fcy - 42, fcx + 42, fcy + 42], fill=sc((32, 32, 36)), outline=sc((96, 94, 88)), width=3)
    for r_g in (14, 26, 36):
        dr.ellipse([fcx - r_g, fcy - r_g, fcx + r_g, fcy + r_g], outline=sc((138, 136, 128)), width=2)
    dr.rounded_rectangle([640, 34, 694, 78], radius=4, fill=sc((26, 26, 30)), outline=sc((88, 86, 80)), width=2)
    # DB25 parallel, DB9 serial, VGA blue port, and ISA expansion brackets
    dr.rounded_rectangle([716, 26, 796, 52], radius=3, fill=sc((158, 58, 112)), outline=sc((210, 212, 216)), width=2)
    dr.rounded_rectangle([716, 64, 764, 90], radius=3, fill=sc((48, 128, 128)), outline=sc((210, 212, 216)), width=2)
    dr.rounded_rectangle([774, 64, 822, 90], radius=3, fill=sc((46, 74, 168)), outline=sc((210, 212, 216)), width=2)
    for sx_b in range(844, 1006, 26):
        dr.rectangle([sx_b, 18, sx_b + 18, 108], fill=sc((128, 126, 120)), outline=sc((74, 72, 68)), width=2)

    # --- 2b. Desktop Case Painted Steel Top/Sides [512..1024, 128..256] ---
    dr.rectangle([512, 128, 1023, 255], fill=sc((206, 196, 172)), outline=sc((164, 154, 134)), width=2)
    for vx in range(548, 720, 14):
        dr.line([vx, 154, vx, 228], fill=sc((88, 82, 70)), width=4)

    # --- 3. CRT Monitor Front Bezel [0..512, 256..640] ---
    dr.rectangle([0, 256, 511, 639], fill=sc((216, 206, 180)))
    dr.rectangle([6, 262, 505, 633], outline=sc((240, 232, 208)), width=4)
    # Recessed inner dark bevel framing the screen (x: 44..468, y: 292..562)
    dr.rounded_rectangle([38, 286, 474, 568], radius=14, fill=sc((164, 154, 132)), outline=sc((116, 108, 92)), width=3)
    dr.rounded_rectangle([50, 298, 462, 556], radius=10, fill=sc((36, 38, 36)))
    # Little brand-less recessed rectangular badge on lower-left chin + adjustment wheels + power button
    dr.rounded_rectangle([52, 584, 134, 616], radius=3, fill=sc((186, 176, 152)), outline=sc((118, 110, 94)), width=2)
    dr.rectangle([60, 592, 126, 608], fill=sc((156, 148, 128)))
    for wx in (248, 286, 324):
        dr.rounded_rectangle([wx, 590, wx + 24, 610], radius=3, fill=sc((82, 78, 68)), outline=sc((46, 44, 38)), width=2)
        for kx in range(wx + 4, wx + 22, 4):
            dr.line([kx, 592, kx, 608], fill=sc((142, 136, 120)), width=1)
    dr.rounded_rectangle([422, 584, 462, 618], radius=4, fill=sc((192, 182, 158)), outline=sc((86, 80, 68)), width=2)

    # --- 4. CRT Monitor Rounded Back Housing [512..1024, 256..640] ---
    dr.rectangle([512, 256, 1023, 639], fill=sc((204, 194, 168)))
    # Horizontal molded cooling louvers across upper CRT shell
    for vy_l in range(288, 436, 14):
        dr.line([556, vy_l, 980, vy_l], fill=sc((68, 64, 54)), width=5)
        dr.line([556, vy_l + 5, 980, vy_l + 5], fill=sc((228, 218, 194)), width=2)
    # Molded rear regulatory / school property asset tag sticker ("BAKERSFIELD HIGH LAB #12")
    dr.rounded_rectangle([672, 476, 864, 566], radius=4, fill=sc((232, 228, 214)), outline=sc((110, 106, 94)), width=2)
    dr.rectangle([678, 482, 858, 502], fill=sc((184, 44, 38)))
    dr.text((686, 485), "PROPERTY OF SCHOOL LAB", fill=sc((248, 246, 240)), font=_font(12, bold=True))
    dr.text((688, 512), "STATION: RM-204-PC", fill=sc((36, 36, 40)), font=_font(13, bold=True))
    dr.text((688, 534), "NO FLOPPY DISKS!!", fill=sc((172, 32, 28)), font=_font(14, bold=True))

    # --- 5a. Sculpted Mechanical Keycaps Grid [0..320, 640..832] ---
    dr.rectangle([0, 640, 319, 831], fill=sc((74, 70, 62)))
    rows_lbl = ["ESC F1 F2 F3 F4 F5 F6 F7", "` 1 2 3 4 5 6 7 8 9 0 -", "Q W E R T Y U I O P [ ]", "A S D F G H J K L ; ENTER", "Z X C V B N M , . / SHIFT"]
    for ri, rtxt in enumerate(rows_lbl):
        ky = 648 + ri * 30
        tokens = rtxt.split()
        kx = 8
        for tok in tokens:
            kw = 20 if len(tok) == 1 else (42 if len(tok) <= 3 else 58)
            if kx + kw > 312:
                break
            col = (182, 176, 158) if len(tok) > 1 else (226, 218, 198)
            dr.rounded_rectangle([kx, ky, kx + kw, ky + 24], radius=3, fill=sc(col), outline=sc((96, 90, 78)), width=2)
            dr.text((kx + 4, ky + 5), tok[:3], fill=sc((32, 32, 36)), font=_font(11, bold=True))
            kx += kw + 4
    # Spacebar row at bottom of keycap tile
    dr.rounded_rectangle([8, 800, 62, 824], radius=3, fill=sc((182, 176, 158)), outline=sc((96, 90, 78)), width=2)
    dr.rounded_rectangle([68, 800, 244, 824], radius=3, fill=sc((226, 218, 198)), outline=sc((96, 90, 78)), width=2)
    dr.rounded_rectangle([250, 800, 310, 824], radius=3, fill=sc((182, 176, 158)), outline=sc((96, 90, 78)), width=2)

    # --- 5b. Keyboard Wedge Shell [320..512, 640..832] ---
    dr.rectangle([320, 640, 511, 831], fill=sc((214, 204, 178)), outline=sc((168, 158, 136)), width=2)
    dr.rounded_rectangle([396, 654, 496, 678], radius=3, fill=sc((62, 60, 54)))
    for lx_i, lbl_k in enumerate(("NUM", "CAP", "SCR")):
        lx_p = 406 + lx_i * 28
        dr.ellipse([lx_p, 660, lx_p + 8, 668], fill=sc((72, 215, 86)))
        dr.text((lx_p - 2, 669), lbl_k, fill=sc((210, 206, 192)), font=_font(8, bold=True))

    # --- 6. School Computer Stand / Cart Panels [512..800, 640..832] ---
    dr.rectangle([512, 640, 799, 831], fill=sc((192, 184, 164)), outline=sc((136, 128, 112)), width=3)
    dr.rectangle([524, 652, 787, 819], outline=sc((218, 210, 190)), width=2)
    # Dark rubber bumper trim strip along stand edge
    dr.rectangle([512, 796, 799, 816], fill=sc((54, 52, 48)))

    # --- 7. Surge Strip [800..1024, 640..736] & Dark Hardware [800..1024, 736..832] ---
    dr.rectangle([800, 640, 1023, 735], fill=sc((208, 198, 176)), outline=sc((118, 110, 96)), width=2)
    for ox in range(846, 1012, 28):
        dr.rounded_rectangle([ox, 664, ox + 20, 712], radius=3, fill=sc((176, 168, 148)), outline=sc((88, 82, 72)), width=1)
        dr.rectangle([ox + 5, 674, ox + 7, 688], fill=sc((24, 24, 26)))
        dr.rectangle([ox + 13, 674, ox + 15, 688], fill=sc((24, 24, 26)))
        dr.ellipse([ox + 8, 696, ox + 12, 702], fill=sc((24, 24, 26)))
    dr.rectangle([800, 736, 1023, 831], fill=sc((38, 38, 42)))

    # --- 8. Cables & Chrome Antenna Rods [0..1024, 832..1024] ---
    # [0..256]: Ribbed matte-black AC cord
    for y_c in range(832, 1024):
        rib = int(round((34 + 9 * math.sin(y_c * 0.45)) * DIM))
        dr.line([0, y_c, 255, y_c], fill=(rib, rib, rib + 2))
    # [256..512]: Coiled putty-grey keyboard / VGA cord
    for y_c in range(832, 1024):
        rib = 148 + 34 * math.sin(y_c * 0.65)
        dr.line([256, y_c, 511, y_c], fill=sc((rib, rib * 0.96, rib * 0.86)))
    # [512..768]: Dark coax BNC network cable w/ silver crimp ferrule band
    for y_c in range(832, 1024):
        is_band = 910 <= y_c <= 936
        c_base = (210, 214, 222) if is_band else (48, 52, 58)
        dr.line([512, y_c, 767, y_c], fill=sc(c_base))
    # [768..1024]: Gleaming chrome telescoping antenna rod (circumferential sheen along X, telescopic joints along Y)
    for x_a in range(768, 1024):
        u_a = (x_a - 768) / 255.0 * 2.0 * math.pi
        sh = 0.66 + 0.26 * math.cos(u_a - 0.8) + 0.10 * math.cos(2.0 * u_a)
        col = sc((sh * 242, sh * 246, min(255, sh * 255)))
        dr.line([x_a, 832, x_a, 1023], fill=col)
    for joint_y in (880, 928, 976):
        dr.line([768, joint_y, 1023, joint_y], fill=sc((72, 76, 84)), width=3)

    path = os.path.join(out_dir, "netsend_pc_body.png")
    im.save(path, "PNG", optimize=True)
    return path


# ==============================================================================
# 4. UNLIT LEDs & BRIGHT ANTENNA TIPS (progs/netsend_leds.png, 128x128)
# ==============================================================================
def build_leds_texture(out_dir):
    """128x128 unlit (rgbGen identity) quadrant atlas:
      Q1 [0..64,  0..64]  (u:0.0..0.5, v:0.0..0.5): Bright Green Power LED
      Q2 [64..128,0..64]  (u:0.5..1.0, v:0.0..0.5): Bright Amber/Orange Floppy Activity LED
      Q3 [0..64,  64..128](u:0.0..0.5, v:0.5..1.0): Red Surge-Strip Rocker LED
      Q4 [64..128,64..128](u:0.5..1.0, v:0.5..1.0): Electric Cyan-White Antenna Tip Ball
    """
    im = Image.new("RGB", (128, 128), (10, 12, 10))
    dr = ImageDraw.Draw(im)

    def radial_led(x0, y0, edge_rgb, core_rgb):
        for r in range(32, 0, -1):
            t = 1.0 - (r / 32.0)
            col = tuple(int(round(edge_rgb[k] + (core_rgb[k] - edge_rgb[k]) * (t ** 1.4))) for k in range(3))
            dr.ellipse([x0 + 32 - r, y0 + 32 - r, x0 + 32 + r, y0 + 32 + r], fill=col)

    # Calibrated for 2.5x DarkPlaces HDR (rgbGen identity) so colors stay vividly saturated without clipping white
    radial_led(0, 0, (12, 68, 16), (52, 168, 62))        # Green Power LED
    radial_led(64, 0, (78, 36, 6), (175, 118, 24))       # Amber Floppy Drive LED
    radial_led(0, 64, (74, 12, 10), (168, 38, 32))       # Red Surge Switch LED
    radial_led(64, 64, (28, 96, 152), (138, 182, 205))   # Bright Electric Antenna Tip

    path = os.path.join(out_dir, "netsend_leds.png")
    im.save(path, "PNG", optimize=True)
    return path


# ==============================================================================
# 5. HIGH-RES CRT SCREEN SEQUENCE (progs/netsend_s_*.png, 512x256)
# ==============================================================================
def _crt_canvas(scanline_alpha=0.24):
    """Creates a 512x256 deep black-green phosphor CRT glass canvas with fine dither (no 8-bit HDR banding)."""
    W, H = 512, 256
    rng = np.random.default_rng(777)
    dith = rng.uniform(-0.45, 0.45, size=(H, W, 1)).astype(np.float32)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.5) / (H * 0.5)
    vig = np.clip(1.0 - 0.30 * (nx * nx * 0.7 + ny * ny * 0.9), 0.45, 1.0)
    arr[..., 0] = 2.2 * vig
    arr[..., 1] = 5.4 * vig
    arr[..., 2] = 2.8 * vig
    arr = np.clip(arr + dith, 1.0, 255.0)
    return arr, scanline_alpha


def _finalize_crt(base_arr, text_layer, scanline_strength=0.24):
    """Composites crisp phosphor text + localized phosphor bloom + 2px horizontal CRT scanlines."""
    W, H = 512, 256
    txt_np = np.asarray(text_layer, dtype=np.float32)
    # Soft localized halo around bright phosphor glyphs (baked single-pass so DarkPlaces animmap stays 1-stage!)
    bloom_im = text_layer.filter(ImageFilter.GaussianBlur(radius=3.0))
    bloom_np = np.asarray(bloom_im, dtype=np.float32)

    alpha = txt_np[..., 3:4] / 255.0
    out = base_arr + bloom_np[..., :3] * (bloom_np[..., 3:4] / 255.0) * 0.42
    out = out * (1.0 - alpha) + txt_np[..., :3] * alpha

    # Crisp 2px CRT aperture/scanline modulation
    scan = np.ones((H, 1, 1), dtype=np.float32)
    scan[1::2, 0, 0] = 1.0 - scanline_strength
    out *= scan

    # Subtle outer CRT glass bezel vignette border
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([2, 2, W - 3, H - 3], radius=12, outline=(6, 18, 9), width=4)
    return im


def build_crt_screen_textures(out_dir):
    """Generates the complete CRT screen sequence (512x256 each, mapped 1:1 to screen face ONLY):
      - netsend_s_off.png          : Black CRT glass (off)
      - netsend_s_n0..n2.png       : Power-on CRT warm-up & white-noise flicker
      - netsend_s_init0..1.png     : INITIALIZING BATCH FILE...
      - netsend_s_lol0..1.png      : C:\\> LOL.BAT
      - netsend_s_fst0..1.png      : NET SEND * LOL
      - netsend_s_l00..l15.png     : Looping live-typing hacking screen (hex + NET SEND * LOL + WHERE'S THE DISK? + MESSAGE SENT [OK])
      - netsend_s_dot0..1.png      : Shutdown CRT collapse line -> white phosphor dot
      - netsend_scr_glow.png       : Dedicated additive CRT glow stage texture
      - netsend_scr_black.png      : Zero-glow black texture for off state
    """
    W, H = 512, 256
    paths = {}

    # Phosphor palette calibrated for DarkPlaces 2.5x HDR (rgbGen identity):
    # Vivid luminous P1 phosphor green in 2.5x HDR without clipping R/B channels to solid white
    P_BRIGHT = (42, 162, 54, 255)    # Crisp bright phosphor headline / cursor
    P_GREEN  = (24, 132, 36, 255)    # Classic P1 green CRT text
    P_DIM    = (14, 78, 22, 255)     # Scrolling hex / header bar
    P_OK     = (58, 176, 72, 255)    # [OK] highlight

    f_huge = _font(38, bold=True, mono=True)
    f_big  = _font(30, bold=True, mono=True)
    f_med  = _font(23, bold=True, mono=True)
    f_hex  = _font(17, bold=True, mono=True)

    # 1. OFF screen
    arr_off, _ = _crt_canvas()
    im_off = Image.fromarray(arr_off.astype(np.uint8), mode="RGB")
    d_off = ImageDraw.Draw(im_off)
    d_off.line([54, 42, 138, 18], fill=(12, 16, 14), width=6)
    d_off.rounded_rectangle([2, 2, W - 3, H - 3], radius=12, outline=(6, 10, 8), width=4)
    p_off = os.path.join(out_dir, "netsend_s_off.png")
    im_off.save(p_off, "PNG", optimize=True)
    paths["off"] = p_off

    # 2. Power-On White Noise / CRT Warm-up Flicker (3 frames: n0, n1, n2)
    rng = np.random.default_rng(1999)
    for ni in range(3):
        arr_n, _ = _crt_canvas()
        noise = rng.uniform(0.0, 1.0, size=(H // 2, W // 4)).astype(np.float32)
        noise_up = np.asarray(Image.fromarray(noise, mode="F").resize((W, H), Image.NEAREST))
        if ni == 0:
            # Horizontal sync ignition flash band expanding from center
            yy = np.arange(H, dtype=np.float32)[:, None]
            band = np.exp(-((yy - H * 0.5) ** 2) / 180.0)
            val = (noise_up * 0.55 + 0.45) * band * 185.0
        elif ni == 1:
            # Full rolling static snow burst
            yy = np.arange(H, dtype=np.float32)[:, None]
            bars = 0.55 + 0.45 * np.sin(yy * 0.14 + 1.2)
            val = (noise_up > 0.42).astype(np.float32) * noise_up * bars * 155.0
        else:
            # Clearing static w/ sync tear
            yy = np.arange(H, dtype=np.float32)[:, None]
            band = (yy > 110).astype(np.float32) * 0.65 + 0.15
            val = (noise_up > 0.58).astype(np.float32) * noise_up * band * 135.0
        arr_n[..., 0] += val * 0.72
        arr_n[..., 1] += val * 1.00
        arr_n[..., 2] += val * 0.78
        scan = np.ones((H, 1, 1), dtype=np.float32)
        scan[1::2, 0, 0] = 0.74
        im_n = Image.fromarray(np.clip(arr_n * scan, 0, 255).astype(np.uint8), mode="RGB")
        pn = os.path.join(out_dir, f"netsend_s_n{ni}.png")
        im_n.save(pn, "PNG", optimize=True)

    # 3. Boot Stage A: INITIALIZING BATCH FILE... (cursor blink 0/1)
    for ci in (0, 1):
        base, _ = _crt_canvas()
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)
        td.text((22, 20), "MS-DOS 6.22  //  LAB-PC-04", fill=P_DIM, font=f_hex)
        td.line([20, 44, W - 20, 44], fill=P_DIM, width=2)
        td.text((24, 78), "INITIALIZING", fill=P_BRIGHT, font=f_huge)
        cur = " \u2588" if ci == 0 else ""
        td.text((24, 132), "BATCH FILE..." + cur, fill=P_BRIGHT, font=f_huge)
        td.text((24, 206), "READING A:\\LOL.BAT [1.44MB]", fill=P_GREEN, font=f_hex)
        im_i = _finalize_crt(base, tl)
        im_i.save(os.path.join(out_dir, f"netsend_s_init{ci}.png"), "PNG", optimize=True)

    # 4. Boot Stage B: C:\> LOL.BAT (cursor blink 0/1)
    for ci in (0, 1):
        base, _ = _crt_canvas()
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)
        td.text((22, 22), "INITIALIZING BATCH FILE... [OK]", fill=P_DIM, font=f_hex)
        td.line([20, 48, W - 20, 48], fill=P_DIM, width=2)
        cur = "\u2588" if ci == 0 else "_"
        td.text((22, 98), f"C:\\> LOL.BAT{cur}", fill=P_BRIGHT, font=f_huge)
        td.text((22, 168), "@ECHO OFF", fill=P_GREEN, font=f_med)
        td.text((22, 200), ":LOOP", fill=P_GREEN, font=f_med)
        im_l = _finalize_crt(base, tl)
        im_l.save(os.path.join(out_dir, f"netsend_s_lol{ci}.png"), "PNG", optimize=True)

    # 5. Boot Stage C: NET SEND * LOL (cursor blink 0/1)
    for ci in (0, 1):
        base, _ = _crt_canvas()
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)
        td.text((22, 20), "C:\\> LOL.BAT", fill=P_GREEN, font=f_med)
        td.line([20, 52, W - 20, 52], fill=P_DIM, width=2)
        cur = "\u2588" if ci == 0 else ""
        td.text((22, 86), f"NET SEND * LOL{cur}", fill=P_BRIGHT, font=f_big)
        td.text((22, 146), "SENDING TO * [254 WORKSTATIONS]", fill=P_GREEN, font=f_hex)
        if ci == 1:
            td.text((22, 184), "MESSAGE SENT [OK]", fill=P_OK, font=f_med)
        im_f = _finalize_crt(base, tl)
        im_f.save(os.path.join(out_dir, f"netsend_s_fst{ci}.png"), "PNG", optimize=True)

    # 6. Active Looping Hacking / Live-Typing Screen (16 frames: l00 .. l15)
    # Designed so walking up to the PC shows constant live typing, scrolling hex packets,
    # NET SEND * LOL, NET SEND * WHERE'S THE DISK?, and MESSAGE SENT [OK] with blinking cursor!
    loop_script = [
        # (line1, line2, line3, line4, line5_active, cursor_on)
        ("04A0: 4E 45 54 20 53 45 4E 44", "C:\\> LOL.BAT", "MESSAGE SENT [OK]", "04A8: FF FF BCAST -> LAB_NET", "> NET S", True),
        ("04A8: FF FF BCAST -> LAB_NET",  "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", "04B0: 4C 4F 4C 2E 42 41 54", "> NET SEND ", True),
        ("04A8: FF FF BCAST -> LAB_NET",  "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", "04B0: 4C 4F 4C 2E 42 41 54", "> NET SEND * ", False),
        ("04A8: FF FF BCAST -> LAB_NET",  "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", "04B0: 4C 4F 4C 2E 42 41 54", "> NET SEND * LOL", True),
        ("> NET SEND * WHERE'S THE DISK?","MESSAGE SENT [OK]", "04B8: TX 254/254 HOSTS [SMB]", "> NET SEND * LOL", "MESSAGE SENT [OK]", False),
        ("MESSAGE SENT [OK]",             "04B8: TX 254/254 HOSTS [SMB]", "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", True),
        ("04B8: TX 254/254 HOSTS [SMB]",  "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET ", True),
        ("04B8: TX 254/254 HOSTS [SMB]",  "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET SEND * ", False),
        ("04B8: TX 254/254 HOSTS [SMB]",  "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET SEND * WHERE'S", True),
        ("04B8: TX 254/254 HOSTS [SMB]",  "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET SEND * WHERE'S THE", True),
        ("04B8: TX 254/254 HOSTS [SMB]",  "> NET SEND * LOL", "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET SEND * WHERE'S THE DISK?", False),
        ("> NET SEND * LOL",              "MESSAGE SENT [OK]", "04C0: 57 48 45 52 45 27 53 3F", "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", True),
        ("MESSAGE SENT [OK]",             "04C8: 44 41 56 49 44 5F 44 53", "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", "04D0: GOTO LOOP // FLOOD=ON", False),
        ("04C8: 44 41 56 49 44 5F 44 53", "> NET SEND * WHERE'S THE DISK?", "MESSAGE SENT [OK]", "04D0: GOTO LOOP // FLOOD=ON", "> NET SEND * LOL", True),
        ("> NET SEND * WHERE'S THE DISK?","MESSAGE SENT [OK]", "04D0: GOTO LOOP // FLOOD=ON", "> NET SEND * LOL", "MESSAGE SENT [OK]", False),
        ("MESSAGE SENT [OK]",             "04D8: 4E 45 54 20 53 45 4E 44", "> NET SEND * LOL", "MESSAGE SENT [OK]", "> ", True),
    ]

    for li, (l1, l2, l3, l4, l5, cur_on) in enumerate(loop_script):
        base, _ = _crt_canvas()
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)

        # Crisp inverted phosphor header bar
        td.rectangle([16, 12, W - 16, 38], fill=(16, 72, 26, 255))
        td.text((24, 16), "C:\\> LOL.BAT  [NET SEND FLOOD]", fill=P_BRIGHT, font=f_hex)

        rows = [l1, l2, l3, l4, l5 + ("\u2588" if cur_on else "")]
        y_positions = [48, 86, 124, 162, 202]
        for r_idx, (txt, ry) in enumerate(zip(rows, y_positions)):
            if txt.startswith("04"):
                col, fnt = P_DIM, f_hex
                ry += 3
            elif "MESSAGE SENT" in txt:
                col, fnt = P_OK, f_med
            elif r_idx == 4:
                col, fnt = P_BRIGHT, f_med
            else:
                col, fnt = P_GREEN, f_med
            td.text((20, ry), txt, fill=col, font=fnt)

        im_lp = _finalize_crt(base, tl, scanline_strength=0.20)
        im_lp.save(os.path.join(out_dir, f"netsend_s_l{li:02d}.png"), "PNG", optimize=True)

    # 7. Shutdown CRT Collapse Line -> White Phosphor Dot (dot0, dot1)
    for di in (0, 1):
        arr_d, _ = _crt_canvas()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dx = xx - W * 0.5
        dy = yy - H * 0.5
        if di == 0:
            # Horizontal collapse flare pinching into center white dot (calibrated for 2.5x HDR)
            line_glow = np.exp(-(dy * dy) / 14.0) * np.exp(-(dx * dx) / 18000.0)
            dot_glow = np.exp(-(dx * dx + dy * dy) / 220.0)
            v_w = np.clip(line_glow * 115.0 + dot_glow * 175.0, 0, 255)
        else:
            # Crisp dying central white CRT phosphor dot
            dot_glow = np.exp(-(dx * dx + dy * dy) / 95.0)
            halo = np.exp(-(dx * dx + dy * dy) / 520.0)
            v_w = np.clip(halo * 46.0 + dot_glow * 180.0, 0, 255)
        arr_d[..., 0] = np.clip(arr_d[..., 0] + v_w * 0.90, 0, 255)
        arr_d[..., 1] = np.clip(arr_d[..., 1] + v_w * 1.00, 0, 255)
        arr_d[..., 2] = np.clip(arr_d[..., 2] + v_w * 0.92, 0, 255)
        im_d = Image.fromarray(arr_d.astype(np.uint8), mode="RGB")
        im_d.save(os.path.join(out_dir, f"netsend_s_dot{di}.png"), "PNG", optimize=True)

    # 8. Dedicated Additive CRT Glow Stage Texture (progs/netsend_scr_glow.png, 256x128)
    # Soft phosphor bloom that makes the CRT glow without washing out the sharp text stage
    gw, gh = 256, 128
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    nx = (xx - gw * 0.5) / (gw * 0.46)
    ny = (yy - gh * 0.5) / (gh * 0.46)
    r2 = nx * nx + ny * ny
    bloom = np.exp(-r2 * 1.85)
    g_arr = np.zeros((gh, gw, 3), dtype=np.uint8)
    g_arr[..., 0] = np.clip(bloom * 12.0, 0, 255).astype(np.uint8)
    g_arr[..., 1] = np.clip(bloom * 44.0, 0, 255).astype(np.uint8)
    g_arr[..., 2] = np.clip(bloom * 18.0, 0, 255).astype(np.uint8)
    Image.fromarray(g_arr, mode="RGB").save(os.path.join(out_dir, "netsend_scr_glow.png"), "PNG", optimize=True)
    Image.new("RGB", (64, 64), (0, 0, 0)).save(os.path.join(out_dir, "netsend_scr_black.png"), "PNG", optimize=True)

    return paths


# ==============================================================================
# 6. ELECTRIC LIGHTNING ARC TEXTURE & QUAKE .SPR FALLBACK
# ==============================================================================
def build_arc_texture_and_sprite(out_dir):
    """Generates:
      - progs/netsend_arc.png  (256x128 RGB additive jagged blue-white lightning ribbon texture for netsend_arc.md3)
      - progs/netsend_arc.spr  (Quake IDSP v1 8-frame lightning sprite fallback!)
    """
    W, H = 256, 128
    ux = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    vy = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None]

    # Subtle internal plasma kink along u so even straight segments crackle with fine filaments
    wiggle = 0.14 * np.sin(ux * math.pi * 6.0) + 0.07 * np.sin(ux * math.pi * 15.0 + 0.8)
    d = np.abs(vy - wiggle)
    end_taper = np.sin(np.clip(ux, 0.02, 0.98) * math.pi) ** 0.55

    core = np.exp(-(d * d) / 0.018) * end_taper
    mid  = np.exp(-(d * d) / 0.110) * end_taper
    halo = np.exp(-(d * d) / 0.380) * end_taper

    # Tuned for blendfunc add in DarkPlaces 2.5x HDR: crisp white-blue core + electric cyan corona
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    arr[..., 0] = np.clip((0.18 * halo + 0.52 * mid + 0.95 * core) * 195.0, 0, 255).astype(np.uint8)
    arr[..., 1] = np.clip((0.55 * halo + 0.86 * mid + 1.00 * core) * 215.0, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip((0.95 * halo + 1.00 * mid + 1.00 * core) * 245.0, 0, 255).astype(np.uint8)

    arc_png = os.path.join(out_dir, "netsend_arc.png")
    Image.fromarray(arr, mode="RGB").save(arc_png, "PNG", optimize=True)

    # Also write a genuine Quake 1 .spr sprite fallback (progs/netsend_arc.spr, 64x64, 8 frames, palette index 255 = transparent)
    # Quake standard palette electric blues: 244 (bright white-yellow), 254 (white), 208..215 (electric blue ramp)
    # Wait: in Quake palette, index 255 is transparent; index 254 is pure white (255,255,255); 240-243 are bright blue/cyan/white,
    # and indices 32..47 are the light-blue/slate ramp (47 = bright ice-blue, 43 = mid blue, 39 = deep blue)!
    SW = SH = 64
    frames_bin = []
    rng = random.Random(909)
    for fi in range(8):
        pix = bytearray([255] * (SW * SH))
        # Draw 3 jagged crossed electric arcs across the 64x64 sprite frame
        for b_idx in range(3):
            a0 = (fi * 0.78 + b_idx * 2.09)
            x0 = 32 + int(26 * math.cos(a0))
            y0 = 32 + int(26 * math.sin(a0))
            x1 = 32 - int(26 * math.cos(a0 + rng.uniform(-0.35, 0.35)))
            y1 = 32 - int(26 * math.sin(a0 + rng.uniform(-0.35, 0.35)))
            pts = [(x0, y0)]
            for s in range(1, 6):
                t = s / 6.0
                mx = x0 + (x1 - x0) * t + rng.randint(-6, 6)
                my = y0 + (y1 - y0) * t + rng.randint(-6, 6)
                pts.append((max(2, min(61, int(mx))), max(2, min(61, int(my)))))
            pts.append((x1, y1))

            for (px0, py0), (px1, py1) in zip(pts[:-1], pts[1:]):
                steps = max(abs(px1 - px0), abs(py1 - py0), 1)
                for st_i in range(steps + 1):
                    cx = int(round(px0 + (px1 - px0) * st_i / steps))
                    cy = int(round(py0 + (py1 - py0) * st_i / steps))
                    for oy in (-2, -1, 0, 1, 2):
                        for ox in (-2, -1, 0, 1, 2):
                            xx_p, yy_p = cx + ox, cy + oy
                            if 0 <= xx_p < SW and 0 <= yy_p < SH:
                                dist2 = ox * ox + oy * oy
                                idx = yy_p * SW + xx_p
                                if dist2 == 0:
                                    pix[idx] = 254  # pure bright white core
                                elif dist2 <= 2 and pix[idx] != 254:
                                    pix[idx] = 47   # bright electric ice-blue
                                elif dist2 <= 4 and pix[idx] == 255:
                                    pix[idx] = 43   # mid electric blue corona
        # Single-frame sprite picture record: group=0 (int32), origin_x=-32, origin_y=32, width=64, height=64
        frames_bin.append(struct.pack("<iiiii", 0, -SW // 2, SH // 2, SW, SH) + bytes(pix))

    # IDSP header: ident="IDSP", version=1, type=2 (SPR_VP_PARALLEL), boundingradius=46.0, width=64, height=64, numframes=8, beamlength=0.0, synctype=0
    spr_hdr = struct.pack("<4siifiiifi", b"IDSP", 1, 2, 46.0, SW, SH, len(frames_bin), 0.0, 0)
    spr_path = os.path.join(out_dir, "netsend_arc.spr")
    with open(spr_path, "wb") as f:
        f.write(spr_hdr + b"".join(frames_bin))

    return arc_png, spr_path


def build_all_netsend_textures(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    disk_p = build_disk_texture(out_dir)
    hand_p = build_hand_texture(out_dir)
    body_p = build_pc_body_texture(out_dir)
    leds_p = build_leds_texture(out_dir)
    scr_p = build_crt_screen_textures(out_dir)
    arc_p, spr_p = build_arc_texture_and_sprite(out_dir)
    return {
        "disk": disk_p,
        "hand": hand_p,
        "pc_body": body_p,
        "leds": leds_p,
        "screens": scr_p,
        "arc": arc_p,
        "spr": spr_p,
    }
