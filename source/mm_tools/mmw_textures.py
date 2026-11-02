"""Procedural high-resolution texture synthesis for the BakersfieldQuake Mega Man Weapon ('The Mega-Slinger' Mk.II):
  - mmw_chrome_axle.png  (512x512: high-contrast anisotropic chrome bar, TIG weld T-collar, ribbed rubber cap, axle, nut, pin, valve)
  - mmw_wheel.png        (1024x1024: 5-ribbed lugged rubber tread, embossed sidewall, 4-cutout white stamped-steel concave rim & bearing)
  - mmw_gun_metal.png    (1024x1024: sleek anodized gunmetal-titanium chassis, brushed mag-rails, hazard trim, copper tanks & coils)
  - mmw_hand.png         (512x512: Quake Ranger distressed brown leather glove, bronze knuckle plate, riveted iron/brass bracer)
  - mmw_gauge_glow.png   (512x512: 0-250 PSI dial, glowing needle, cyan accelerator rail chevrons, MEGA-CORE & recharge bars)
  - mmw_fx.png           (512x512 RGBA: jagged cyan rail plasma bolt, feathered starburst/Mach cone, turbulent gas vent plume)
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _font(size, bold=True):
    candidates = ["consolab.ttf", "tahomabd.ttf", "arialbd.ttf"] if bold else ["consola.ttf", "tahoma.ttf", "arial.ttf"]
    for nm in candidates:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm_noise(h, w, seed=42, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tot_w = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        grid = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(grid, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tot_w += amp
    acc /= max(tot_w, 1e-6)
    return acc


def build_chrome_axle_texture(out_dir):
    """512x512 atlas for the central chrome bar, T-collar weld, black rubber cap, steel axle, hex nut, yellow pin & valve.
    UV Quadrants (100% compatible with mmw_geometry.py & mma_geometry.py):
      [0..256,   0..256]  (u: 0.0..0.5, v: 0.0..0.5): Mirror-polished chrome central bar
      [256..512, 0..256]  (u: 0.5..1.0, v: 0.0..0.5): Machined steel cross-axle & heat-tinted TIG-welded T-collar
      [0..256,   256..512](u: 0.0..0.5, v: 0.5..1.0): Matte ribbed charcoal-black rubber rear pipe cap
      [256..512, 256..512](u: 0.5..1.0, v: 0.5..1.0): Hardware sub-swatches (hex nut, yellow cotter pin, rubber & brass valve)
    """
    W = H = 512
    arr = np.zeros((H, W, 3), dtype=np.float32)
    n_fine = _fbm_noise(H, W, seed=101, octaves=(2, 4, 8, 16))

    # --- Q1 [0..256, 0..256]: Liquid-Mirror Polished Chrome Central Bar ---
    u = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    refl = (
        0.58
        + 0.27 * np.cos(u - 0.85)
        + 0.16 * np.cos(2.0 * u + 0.45)
        + 0.09 * np.sin(3.0 * u - 0.25)
        - 0.18 * np.exp(-((u - 3.55) ** 2) / 0.14)  # crisp dark horizon reflection band
        + 0.24 * np.exp(-((u - 1.52) ** 2) / 0.07)  # razor-bright studio key reflection
    )
    lathe_lines = 0.015 * np.sin(v * 260.0)
    weld_ao = 1.0 - 0.20 * np.exp(-((v - 0.46) ** 2) / 0.0020)
    c_val = np.clip((refl + lathe_lines + 0.020 * n_fine[:256, :256]) * weld_ao, 0.10, 1.0)
    arr[:256, :256, 0] = c_val * 238.0
    arr[:256, :256, 1] = c_val * 244.0
    arr[:256, :256, 2] = np.clip(c_val * 253.0 + 4.0, 0, 255)

    # --- Q2 [0..256, 256..512]: Brushed Stainless Axle & Heat-Tinted TIG Weld Collar ---
    u2 = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    v2 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    steel = 0.56 + 0.21 * np.cos(u2 - 0.65) + 0.10 * np.cos(2.0 * u2) + 0.035 * n_fine[:256, 256:]
    steel += 0.022 * np.sin(v2 * 320.0)
    tint_straw = np.exp(-((v2 - 0.84) ** 2) / 0.0032)
    tint_blue = np.exp(-((v2 - 0.90) ** 2) / 0.0018)
    bead_rip = 1.0 + 0.15 * np.sin(u2 * 20.0) * np.exp(-((v2 - 0.95) ** 2) / 0.0022)
    s_r = steel * 218.0 + tint_straw * 40.0 - tint_blue * 24.0
    s_g = steel * 222.0 + tint_straw * 18.0 - tint_blue * 10.0
    s_b = steel * 230.0 - tint_straw * 26.0 + tint_blue * 36.0
    arr[:256, 256:, 0] = np.clip(s_r * bead_rip, 22, 255)
    arr[:256, 256:, 1] = np.clip(s_g * bead_rip, 22, 255)
    arr[:256, 256:, 2] = np.clip(s_b * bead_rip, 24, 255)

    # --- Q3 [256..512, 0..256]: Matte Ribbed Charcoal Rubber End-Cap ---
    vr = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    ribs = 0.5 + 0.5 * np.cos(vr * 2.0 * math.pi * 6.0)
    rub = 44.0 + 18.0 * ribs + 5.0 * n_fine[256:, :256]
    arr[256:, :256, 0] = np.clip(rub * 0.95, 14, 98)
    arr[256:, :256, 1] = np.clip(rub * 0.98, 14, 102)
    arr[256:, :256, 2] = np.clip(rub * 1.06, 16, 112)

    # --- Q4 [256..512, 256..512]: Hardware Sub-Swatches ---
    zn = 186.0 + 18.0 * n_fine[256:384, 256:384]
    arr[256:384, 256:384, 0] = zn * 0.97
    arr[256:384, 256:384, 1] = zn * 1.00
    arr[256:384, 256:384, 2] = zn * 1.05

    yp = 1.0 + 0.08 * n_fine[256:384, 384:512]
    arr[256:384, 384:512, 0] = np.clip(248.0 * yp, 0, 255)
    arr[256:384, 384:512, 1] = np.clip(204.0 * yp, 0, 255)
    arr[256:384, 384:512, 2] = np.clip(38.0 * yp, 0, 255)

    vb = 32.0 + 5.0 * n_fine[384:512, 256:384]
    arr[384:512, 256:384, 0] = vb
    arr[384:512, 256:384, 1] = vb + 1.0
    arr[384:512, 256:384, 2] = vb + 4.0

    v_th = np.linspace(0.0, 1.0, 128, dtype=np.float32)[:, None]
    br = (0.86 + 0.14 * np.sin(v_th * 96.0)) * (1.0 + 0.05 * n_fine[384:512, 384:512])
    arr[384:512, 384:512, 0] = np.clip(224.0 * br, 0, 255)
    arr[384:512, 384:512, 1] = np.clip(180.0 * br, 0, 255)
    arr[384:512, 384:512, 2] = np.clip(78.0 * br, 0, 255)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    p = os.path.join(out_dir, "mmw_chrome_axle.png")
    im.save(p, "PNG", optimize=True)
    return p


def _stamp_4_wheel_cutouts(rim, rx, ry, rr, outer_side=True):
    """Stamps 4 bold beveled oval/kidney ventilation cutouts + central sealed bearing race onto a 512x512 polar rim quadrant.
    Angles 10, 100, 190, 280 deg place the -35 deg (325 deg) Schrader valve stem cleanly mid-web between cutouts!
    """
    for ang_d in (10.0, 100.0, 190.0, 280.0):
        ar = math.radians(ang_d)
        ca, sa = math.cos(ar), math.sin(ar)
        # Local radial (dr) and tangential (dt) coordinates around oval center at r = 0.50
        dx = rx - 0.50 * ca
        dy = ry - 0.50 * sa
        u_rad = dx * ca + dy * sa
        u_tan = -dx * sa + dy * ca
        # Kidney/oval distance metric (wider tangentially than radially, like stamped hand-truck wheels!)
        ell = np.sqrt((u_rad / 0.145) ** 2 + (u_tan / 0.215) ** 2)

        # Stamped flared enamel lip highlight around cutout (ell in 1.0 .. 1.24)
        bevel_ring = np.exp(-((ell - 1.12) ** 2) / 0.016)
        light_dir = (dx * -0.65 + dy * -0.65) / np.maximum(np.sqrt(dx * dx + dy * dy), 0.05)
        rim += (22.0 + 14.0 * light_dir) * bevel_ring

        # Deep shadowed cutout aperture (smooth antialiased edge at ell = 1.0)
        hole = np.clip((1.03 - ell) / 0.08, 0.0, 1.0)
        # Subtle inner steel flange rim at ell ~ 0.94 before deep dark shadow
        inner_lip = 48.0 * np.exp(-((ell - 0.93) ** 2) / 0.004)
        hole_col = 22.0 + inner_lip
        rim = rim * (1.0 - hole) + hole_col * hole

        # Stamped lug bolt / rivet between cutouts (at ang_d + 45 deg, r = 0.31)
        ba = math.radians(ang_d + 45.0)
        bdx = rx - 0.31 * math.cos(ba)
        bdy = ry - 0.31 * math.sin(ba)
        bd2 = bdx * bdx + bdy * bdy
        rim -= 32.0 * np.exp(-bd2 / 0.00055)
        rim += 18.0 * np.exp(-((bdx + 0.008) ** 2 + (bdy + 0.008) ** 2) / 0.00028)

    # Central sealed ball-bearing race & grease shield ring (r < 0.23)
    bearing_seal = np.exp(-((rr - 0.20) ** 2) / 0.0006)
    bearing_groove = np.exp(-((rr - 0.14) ** 2) / 0.0005)
    rim -= 65.0 * bearing_seal
    rim -= 38.0 * bearing_groove
    if outer_side:
        rim = np.where(rr < 0.185, rim * 0.72 + 24.0, rim)
    return rim


def build_wheel_texture(out_dir):
    """1024x1024 atlas for Mega Man's pneumatic 5-ribbed rubber tires & 4-cutout white stamped-steel wheel rims:
      [0..512,   0..512]   (u: 0.0..0.5, v: 0.0..0.5): High-contrast 5-rib + radial-lug rubber tread
      [512..1024,0..512]   (u: 0.5..1.0, v: 0.0..0.5): Polar molded rubber sidewall
      [0..512,   512..1024](u: 0.0..0.5, v: 0.5..1.0): Stamped off-white steel outer concave dish w/ 4 oval cutouts
      [512..1024,512..1024](u: 0.5..1.0, v: 0.5..1.0): Painted off-white steel inner hub disc w/ 4 oval cutouts
    """
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    grain = _fbm_noise(H, W, seed=202, octaves=(2, 4, 8, 16, 32))

    # --- Q1 [0..512, 0..512]: Crisp 5-Ribbed + Staggered-Sipe Tire Tread ---
    ux = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[:, None]
    groove_mask = np.zeros_like(ux)
    for gc in (0.21, 0.40, 0.60, 0.79):
        groove_mask += np.exp(-((ux - gc) ** 2) / (2.0 * 0.020 ** 2))
    groove_mask = np.clip(groove_mask, 0.0, 1.0)

    # Alternating staggered transverse tread blocks (24 lugs around circumference -> super readable spin!)
    rib_phase = np.where((ux > 0.21) & (ux < 0.40) | (ux > 0.60) & (ux < 0.79), math.pi, 0.0)
    lug_wave = np.cos(vy * 24.0 + rib_phase)
    sipes = np.clip((lug_wave - 0.55) / 0.25, 0.0, 1.0) * (1.0 - groove_mask)
    lug_hi = np.clip((-lug_wave - 0.35) / 0.45, 0.0, 1.0) * (1.0 - groove_mask)

    shoulder = 1.0 - 0.18 * ((2.0 * ux - 1.0) ** 4)
    base_rub = (58.0 - 40.0 * groove_mask - 18.0 * sipes + 9.5 * lug_hi) * shoulder + 4.5 * grain[:512, :512]
    dust = 8.5 * (1.0 - groove_mask) * np.exp(-((ux - 0.5) ** 2) / 0.14) * (0.65 + 0.35 * np.sin(vy * 2.0 + 0.9))
    tread_c = np.clip(base_rub + dust, 10.0, 96.0)
    arr[:512, :512, 0] = tread_c * 0.96
    arr[:512, :512, 1] = tread_c * 0.99
    arr[:512, :512, 2] = tread_c * 1.06

    # --- Q2 [0..512, 512..1024]: Polar Molded Rubber Sidewall ---
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang_sw = np.arctan2(ry, rx)
    # Subtle 12-spoke molded radial sidewall scuff/rib ticks so spin reads from pure profile too
    rad_ticks = 4.5 * (np.cos(ang_sw * 12.0) > 0.82).astype(np.float32) * np.exp(-((rr - 0.80) ** 2) / 0.004)
    sw = 48.0 + 13.0 * np.exp(-((rr - 0.77) ** 2) / 0.009) + rad_ticks
    sw += 13.0 * np.exp(-((rr - 0.61) ** 2) / 0.00025) - 10.0 * np.exp(-((rr - 0.625) ** 2) / 0.00025)
    sw += 10.0 * np.exp(-((rr - 0.89) ** 2) / 0.00025) - 8.5 * np.exp(-((rr - 0.904) ** 2) / 0.00025)
    sw -= 20.0 * np.exp(-((rr - 0.56) ** 2) / 0.0008)
    sw += 3.8 * grain[:512, 512:]
    arr[:512, 512:, 0] = np.clip(sw * 0.96, 12, 98)
    arr[:512, 512:, 1] = np.clip(sw * 0.99, 12, 100)
    arr[:512, 512:, 2] = np.clip(sw * 1.06, 14, 108)

    # --- Q3 [512..1024, 0..512]: Stamped Off-White Steel Outer Concave Dish Rim w/ 4 Oval Cutouts ---
    rim = np.full((512, 512), 232.0, dtype=np.float32)
    rim += 22.0 * np.exp(-((rr - 0.93) ** 2) / 0.0012)
    rim -= 36.0 * np.exp(-((rr - 0.83) ** 2) / 0.0020)
    rim -= 16.0 * np.exp(-((rr - 0.52) ** 2) / 0.045)
    rim += 15.0 * (rx * -0.55 + ry * -0.55) * np.clip(1.0 - np.abs(rr - 0.56), 0.0, 1.0)
    rim -= 26.0 * np.exp(-((rr - 0.25) ** 2) / 0.0009)
    rim = _stamp_4_wheel_cutouts(rim, rx, ry, rr, outer_side=True)
    # Dark rubber grommet shadow around Schrader valve hole at angle = -35 deg, r = 0.64
    va = math.radians(-35.0)
    vdx = rx - 0.64 * math.cos(va)
    vdy = ry - 0.64 * math.sin(va)
    rim -= 110.0 * np.exp(-(vdx * vdx + vdy * vdy) / 0.0016)
    rim += 2.5 * grain[512:, :512]
    arr[512:, :512, 0] = np.clip(rim * 0.985, 18, 253)
    arr[512:, :512, 1] = np.clip(rim * 0.995, 18, 254)
    arr[512:, :512, 2] = np.clip(rim * 1.015, 22, 255)

    # --- Q4 [512..1024, 512..1024]: Inner Off-White Steel Hub Disc w/ Matching 4 Oval Cutouts ---
    irim = np.full((512, 512), 218.0, dtype=np.float32)
    irim += 18.0 * np.exp(-((rr - 0.92) ** 2) / 0.0015) - 28.0 * np.exp(-((rr - 0.82) ** 2) / 0.0025)
    irim = _stamp_4_wheel_cutouts(irim, rx, ry, rr, outer_side=False)
    irim += 2.8 * grain[512:, 512:]
    arr[512:, 512:, 0] = np.clip(irim * 0.98, 18, 250)
    arr[512:, 512:, 1] = np.clip(irim * 0.99, 18, 252)
    arr[512:, 512:, 2] = np.clip(irim * 1.01, 22, 255)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    f_sw = _font(15, bold=True)
    label = "4.10/3.50-4  PNEUMATIC  •  MEGA-MAN SPEC  •  "
    for i, ch in enumerate(label):
        ang = math.radians(i * (360.0 / len(label)))
        tx = 768 + math.cos(ang) * 184
        ty = 256 + math.sin(ang) * 184
        dr.text((tx - 4, ty - 6), ch, fill=(76, 80, 88), font=f_sw)
        dr.text((tx - 5, ty - 7), ch, fill=(28, 30, 34), font=f_sw)

    p = os.path.join(out_dir, "mmw_wheel.png")
    im.save(p, "PNG", optimize=True)
    return p


def build_gun_metal_texture(out_dir):
    """1024x1024 sleek sci-fi/Quake weapon atlas for 'THE MEGA-SLINGER' Mk.II Pneumatic Mag-Rail Catapult:
      [0..512,   0..256]   (u:0.0..0.5, v:0.00..0.25): Anodized dark gunmetal-titanium chassis armor w/ bevel seams
      [0..512,   256..512] (u:0.0..0.5, v:0.25..0.50): Brushed silver-titanium linear-accelerator rail w/ T-slot channel
      [512..1024,0..256]   (u:0.5..1.0, v:0.00..0.25): High-contrast Black & Quake-Amber Hazard Chevron trim
      [512..1024,256..512] (u:0.5..1.0, v:0.25..0.50): Burnished copper/brass high-pressure accumulator bottle
      [0..512,   512..768] (u:0.0..0.5, v:0.50..0.75): Sleek side shroud armor ('MEGA-SLINGER // MK.II') + angled vents
      [512..1024,512..768] (u:0.5..1.0, v:0.50..0.75): Wound copper booster coil [512..768] + Braided steel hose [768..1024]
      [0..512,   768..1024](u:0.0..0.5, v:0.75..1.00): Carbon-polymer diamond-knurled tactical grip
      [512..1024,768..1024](u:0.5..1.0, v:0.75..1.00): Mirror chrome piston rod [512..768] + Machined bronze-titanium sabot [768..1024]
    """
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm_noise(H, W, seed=303, octaves=(4, 8, 16, 32, 64))

    # 1. Sleek Brushed Anodized Gunmetal-Titanium Chassis [0..256, 0..512] (silky horizontal grain, zero pixel speckle!)
    vy0 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    rng_gm = np.random.default_rng(311)
    brush_gm = rng_gm.standard_normal((256, 1)).astype(np.float32)
    sheen0 = (
        18.0 * np.exp(-((vy0 - 0.16) ** 2) / 0.012)
        + 8.0 * np.exp(-((vy0 - 0.52) ** 2) / 0.030)
        - 14.0 * np.exp(-((vy0 - 0.88) ** 2) / 0.014)
    )
    iron = 62.0 + sheen0 + 3.2 * brush_gm + 2.2 * noise[:256, :512]
    arr[:256, :512, 0] = iron * 0.90
    arr[:256, :512, 1] = iron * 0.98
    arr[:256, :512, 2] = iron * 1.12

    # 2. Brushed Silver-Titanium Launch Rails [256..512, 0..512]
    vy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    rng = np.random.default_rng(77)
    row_s = rng.standard_normal((256, 1)).astype(np.float32)
    rail = (
        148.0
        + 14.0 * row_s
        + 36.0 * np.exp(-((vy - 0.16) ** 2) / 0.006)   # crisp bright machined bevel highlight
        - 52.0 * np.exp(-((vy - 0.52) ** 2) / 0.005)   # deep T-slot magnetic guide channel
        + 22.0 * np.exp(-((vy - 0.78) ** 2) / 0.008)
        + 7.0 * noise[256:512, :512]
    )
    arr[256:512, :512, 0] = np.clip(rail * 0.95, 22, 248)
    arr[256:512, :512, 1] = np.clip(rail * 1.00, 24, 252)
    arr[256:512, :512, 2] = np.clip(rail * 1.08, 28, 255)

    # 3. Crisp Industrial Hazard Chevron Trim [0..256, 512..1024]
    hx = np.arange(512, dtype=np.float32)[None, :]
    hy = np.arange(256, dtype=np.float32)[:, None]
    stripe = (((hx + hy * 0.95) // 34) % 2 == 0).astype(np.float32)
    wear = np.clip(0.88 + 0.16 * noise[:256, 512:], 0.55, 1.10)
    border = ((hy < 14) | (hy > 241)).astype(np.float32)
    r_haz = (stripe * 236.0 + (1.0 - stripe) * 26.0) * wear
    g_haz = (stripe * 172.0 + (1.0 - stripe) * 28.0) * wear
    b_haz = (stripe * 28.0 + (1.0 - stripe) * 34.0) * wear
    arr[:256, 512:, 0] = np.where(border > 0.5, 86.0, r_haz)
    arr[:256, 512:, 1] = np.where(border > 0.5, 92.0, g_haz)
    arr[:256, 512:, 2] = np.where(border > 0.5, 102.0, b_haz)

    # 4. Burnished Copper/Brass Pneumatic Accumulator Bottle [256..512, 512..1024]
    cu_u = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[None, :]
    cu_v = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    cu_sh = 0.66 + 0.26 * np.cos(cu_u - 0.85) + 0.11 * np.cos(2.0 * cu_u) + 0.045 * noise[256:512, 512:]
    strap = (np.abs(cu_v - 0.20) < 0.042) | (np.abs(cu_v - 0.80) < 0.042)
    arr[256:512, 512:, 0] = np.where(strap, 52.0, np.clip(cu_sh * 228.0, 30, 252))
    arr[256:512, 512:, 1] = np.where(strap, 56.0, np.clip(cu_sh * 154.0, 24, 210))
    arr[256:512, 512:, 2] = np.where(strap, 64.0, np.clip(cu_sh * 82.0, 18, 135))

    # 5. Sleek Side Receiver Shroud [512..768, 0..512]
    plate = 74.0 + sheen0 + 8.5 * noise[512:768, :512]
    arr[512:768, :512, 0] = plate * 0.94
    arr[512:768, :512, 1] = plate * 0.99
    arr[512:768, :512, 2] = plate * 1.08

    # 6a. Wound Copper Electromagnetic Booster Coil [512..768, 512..768]
    wy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    wx = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    windings = 0.56 + 0.44 * np.abs(np.sin(wy * math.pi * 24.0))
    c_spec = 0.72 + 0.28 * np.cos(wx - 0.7)
    arr[512:768, 512:768, 0] = np.clip(windings * c_spec * 242.0, 25, 255)
    arr[512:768, 512:768, 1] = np.clip(windings * c_spec * 136.0, 18, 210)
    arr[512:768, 512:768, 2] = np.clip(windings * c_spec * 64.0, 12, 130)

    # 6b. Braided Stainless Steel Air Hose [512..768, 768..1024]
    bx = np.arange(256, dtype=np.float32)[None, :]
    by = np.arange(256, dtype=np.float32)[:, None]
    braid = 0.60 + 0.24 * np.sin((bx + by) * 0.36) * np.sin((bx - by) * 0.36) + 0.06 * noise[512:768, 768:]
    arr[512:768, 768:, 0] = braid * 184.0
    arr[512:768, 768:, 1] = braid * 192.0
    arr[512:768, 768:, 2] = braid * 204.0

    # 7. Carbon-Polymer Diamond Checkered Grip [768..1024, 0..512]
    gx = np.arange(512, dtype=np.float32)[None, :]
    gy = np.arange(256, dtype=np.float32)[:, None]
    knurl = np.abs(np.sin((gx + gy) * 0.40)) * np.abs(np.sin((gx - gy) * 0.40))
    gv = 28.0 + 30.0 * knurl + 3.5 * noise[768:, :512]
    arr[768:, :512, 0] = gv * 0.96
    arr[768:, :512, 1] = gv * 1.00
    arr[768:, :512, 2] = gv * 1.08

    # 8a. Chrome Piston Rod [768..1024, 512..768]
    px_u = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    pr_c = 0.66 + 0.28 * np.cos(px_u - 0.8) + 0.08 * np.cos(2.0 * px_u)
    arr[768:, 512:768, 0] = np.clip(pr_c * 238.0, 30, 255)
    arr[768:, 512:768, 1] = np.clip(pr_c * 244.0, 30, 255)
    arr[768:, 512:768, 2] = np.clip(pr_c * 252.0, 35, 255)

    # 8b. Machined Champagne-Bronze / Titanium Sabot Alloy [768..1024, 768..1024]
    vy_r = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    ram_c = 132.0 + 24.0 * np.cos(vy_r * math.pi * 2.0) + 10.0 * noise[768:, 768:]
    arr[768:, 768:, 0] = np.clip(ram_c * 1.24, 35, 248)
    arr[768:, 768:, 1] = np.clip(ram_c * 1.06, 30, 224)
    arr[768:, 768:, 2] = np.clip(ram_c * 0.78, 22, 180)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # Crisp machined panel seams & hex socket bolts on Gunmetal Chassis [0..512, 0..256]
    dr.rectangle([6, 6, 505, 249], outline=(34, 38, 46), width=3)
    dr.line([9, 10, 502, 10], fill=(116, 126, 142), width=2)
    dr.line([9, 128, 502, 128], fill=(42, 46, 56), width=2)
    dr.line([9, 130, 502, 130], fill=(104, 114, 128), width=1)
    for rx_p in range(32, 492, 64):
        for ry_p in (24, 232):
            dr.ellipse([rx_p - 5, ry_p - 5, rx_p + 5, ry_p + 5], fill=(96, 104, 118), outline=(28, 32, 38))
            dr.point((rx_p - 2, ry_p - 2), fill=(172, 182, 198))

    # Sleek Shroud Louvers, Cyan Accent Line & Badge on [0..512, 512..768]
    dr.rounded_rectangle([14, 524, 498, 754], radius=10, fill=(52, 57, 66), outline=(112, 122, 138), width=3)
    # Sleek forward-raked exhaust gills on left
    for li in range(6):
        lx = 34 + li * 24
        dr.polygon([(lx + 10, 552), (lx + 21, 552), (lx + 9, 726), (lx - 2, 726)], fill=(18, 22, 28), outline=(92, 102, 116))
    # Subtle anodized cyan trim stripe
    dr.rectangle([196, 548, 480, 554], fill=(56, 198, 246))
    dr.rounded_rectangle([196, 562, 480, 672], radius=6, fill=(34, 38, 46), outline=(196, 162, 88), width=2)
    dr.text((212, 572), "MEGA-SLINGER", fill=(246, 202, 96), font=_font(24, bold=True))
    dr.text((214, 606), "MAG-PNEUMATIC RAIL CATAPULT", fill=(192, 208, 226), font=_font(13, bold=True))
    dr.text((214, 632), "MK.II  •  245 PSI  •  CAL. 4.10", fill=(116, 212, 248), font=_font(12, bold=True))
    dr.rectangle([196, 684, 480, 728], fill=(24, 28, 34), outline=(218, 164, 42), width=2)
    dr.text((212, 697), "DANGER: HIGH-VELOCITY AXLE LAUNCH", fill=(245, 186, 52), font=_font(12, bold=True))

    # Tank stencil on Copper Accumulator [512..1024, 256..512]
    dr.text((624, 366), "HP PNEUMO ACCUMULATOR  •  250 PSI", fill=(250, 238, 205), font=_font(15, bold=True))

    p = os.path.join(out_dir, "mmw_gun_metal.png")
    im.save(p, "PNG", optimize=True)
    return p


def build_hand_texture(out_dir):
    """512x512 Quake Ranger Armored Gauntlet & Combat Leather Glove atlas (100% UV-compatible with mma_geometry.py)."""
    W = H = 512
    arr = np.zeros((H, W, 3), dtype=np.float32)
    grain = _fbm_noise(H, W, seed=404, octaves=(2, 4, 8, 16, 32))

    # Q1: Rich distressed Quake brown leather [0..256, 0..256]
    lth = 1.0 + 0.16 * grain[:256, :256]
    arr[:256, :256, 0] = np.clip(104.0 * lth, 32, 172)
    arr[:256, :256, 1] = np.clip(68.0 * lth, 22, 124)
    arr[:256, :256, 2] = np.clip(45.0 * lth, 15, 88)

    # Q2: Reinforced dark suede palm & finger flexion creases [0..256, 256..512]
    vy = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    creases = 1.0 - 0.25 * (
        np.exp(-((vy - 0.33) ** 2) / 0.0012) + np.exp(-((vy - 0.66) ** 2) / 0.0012)
    )
    plm = (68.0 + 10.0 * grain[:256, 256:]) * creases
    arr[:256, 256:, 0] = plm * 1.08
    arr[:256, 256:, 1] = plm * 0.88
    arr[:256, 256:, 2] = plm * 0.72

    # Q3: Riveted Quake Bronze-Iron Gauntlet Cuff [256..512, 0..256]
    ux = np.linspace(0.0, 2.0 * math.pi, 256, dtype=np.float32)[None, :]
    brz = (0.70 + 0.24 * np.cos(ux - 1.0) + 0.11 * grain[256:, :256])
    arr[256:, :256, 0] = np.clip(brz * 134.0, 30, 220)
    arr[256:, :256, 1] = np.clip(brz * 106.0, 24, 184)
    arr[256:, :256, 2] = np.clip(brz * 72.0, 18, 136)

    # Q4 top [256..384, 256..512]: Hammered Brass Knuckle Guard
    kn = 0.80 + 0.15 * grain[256:384, 256:]
    arr[256:384, 256:, 0] = np.clip(kn * 192.0, 44, 245)
    arr[256:384, 256:, 1] = np.clip(kn * 150.0, 34, 208)
    arr[256:384, 256:, 2] = np.clip(kn * 82.0, 22, 128)

    # Q4 bottom [384..512, 256..512]: Quake Ranger Olive-Drab Quilted Combat Sleeve
    sy = np.arange(128, dtype=np.float32)[:, None]
    rib = 0.88 + 0.12 * np.sin(sy * 0.45)
    slv = (72.0 + 11.0 * grain[384:, 256:]) * rib
    arr[384:, 256:, 0] = slv * 0.94
    arr[384:, 256:, 1] = slv * 1.05
    arr[384:, 256:, 2] = slv * 0.74

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    for sx_l in (36, 220):
        for sy_d in range(12, 244, 14):
            dr.line([sx_l, sy_d, sx_l, sy_d + 7], fill=(156, 118, 78), width=2)

    for strap_y in (325, 435):
        dr.rectangle([0, strap_y, 255, strap_y + 24], fill=(54, 36, 24), outline=(28, 18, 12), width=2)
        dr.rounded_rectangle([108, strap_y - 3, 148, strap_y + 27], radius=3, outline=(214, 172, 84), width=3)
    for rx_r in range(22, 246, 36):
        for ry_r in (278, 488):
            dr.ellipse([rx_r - 5, ry_r - 5, rx_r + 5, ry_r + 5], fill=(184, 160, 114), outline=(36, 28, 20))

    for ki in range(4):
        kx = 288 + ki * 56
        dr.ellipse([kx - 16, 304, kx + 16, 336], fill=(218, 176, 98), outline=(78, 58, 28), width=2)

    p = os.path.join(out_dir, "mmw_hand.png")
    im.save(p, "PNG", optimize=True)
    return p


def build_gauge_glow_texture(out_dir):
    """512x512 unlit/emissive telemetry & linear-accelerator rail glow atlas:
      [0..320,   0..320]   (u:0.000..0.625, v:0.000..0.625): Illuminated 0-250 PSI Analog Pressure Dial face
      [320..512, 0..128]   (u:0.625..1.000, v:0.000..0.250): Hot glowing red-orange indicator needle swatch
      [320..512, 132..232] (u:0.625..1.000, v:0.258..0.453): Electric-cyan linear-accelerator rail chevron strip (>>>)
      [320..512, 236..332] (u:0.625..1.000, v:0.461..0.648): Overdrive white-cyan muzzle ring & surge glow swatch
      [0..512,   336..416] (u:0.000..1.000, v:0.656..0.812): Electric-Cyan 'MEGA-CORE // ARMED' reflex reticle & bar
      [0..512,   424..504] (u:0.000..1.000, v:0.828..0.984): Warm-Amber 'CHAMBER CYCLING' recharge bar
    """
    W = H = 512
    im = Image.new("RGB", (W, H), (12, 15, 22))
    dr = ImageDraw.Draw(im)

    # --- Analog PSI Dial centered at (160, 160), radius 146 ---
    cx, cy, R = 160, 160, 146
    dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(14, 20, 30), outline=(196, 160, 86), width=6)
    dr.ellipse([cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10], fill=(18, 26, 38), outline=(56, 98, 136), width=2)

    arc_box = [cx - 118, cy - 118, cx + 118, cy + 118]
    dr.arc(arc_box, start=135, end=265, fill=(56, 228, 128), width=14)   # Green standby
    dr.arc(arc_box, start=265, end=355, fill=(64, 224, 255), width=14)   # Cyan armed optimal
    dr.arc(arc_box, start=355, end=405, fill=(255, 84, 58), width=14)    # Redline overdrive

    f_num = _font(15, bold=True)
    for step in range(26):
        frac = step / 25.0
        ang = math.radians(135.0 + frac * 270.0)
        major = (step % 5 == 0)
        r0 = 94 if major else 106
        r1 = 123
        dr.line(
            [cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)],
            fill=(244, 248, 255) if major else (130, 152, 178),
            width=3 if major else 1,
        )
        if major:
            lbl = str(step * 10)
            lx = cx + 72 * math.cos(ang) - len(lbl) * 4.5
            ly = cy + 72 * math.sin(ang) - 8
            dr.text((lx, ly), lbl, fill=(232, 242, 255), font=f_num)

    dr.text((cx - 21, cy + 34), "PSI", fill=(255, 206, 92), font=_font(21, bold=True))
    dr.text((cx - 44, cy + 60), "MAG-PNEUMO", fill=(96, 222, 255), font=_font(11, bold=True))
    dr.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(96, 108, 126), outline=(220, 232, 248), width=2)

    # --- Glowing Red-Orange Needle Swatch [320..512, 0..128] ---
    dr.rectangle([324, 6, 506, 122], fill=(255, 64, 42), outline=(255, 210, 175), width=5)
    dr.rectangle([350, 44, 480, 84], fill=(255, 232, 210))

    # --- Linear-Accelerator Rail Chevron Strip [320..512, 132..232] (u runs along rail length -> forward +u!) ---
    dr.rectangle([322, 134, 508, 230], fill=(10, 34, 58), outline=(48, 180, 235), width=2)
    # Draw 6 crisp forward-pointing glowing plasma chevrons along X (u: 0.635 -> 0.990)
    for ci in range(6):
        bx = 330 + ci * 29
        pts_outer = [(bx, 144), (bx + 14, 144), (bx + 25, 182), (bx + 14, 220), (bx, 220), (bx + 11, 182)]
        pts_core = [(bx + 4, 152), (bx + 12, 152), (bx + 21, 182), (bx + 12, 212), (bx + 4, 212), (bx + 13, 182)]
        dr.polygon(pts_outer, fill=(42, 206, 255))
        dr.polygon(pts_core, fill=(215, 250, 255))

    # --- Overdrive White-Cyan Surge & Muzzle Ring Swatch [320..512, 236..332] ---
    dr.rounded_rectangle([324, 238, 506, 330], radius=8, fill=(56, 224, 255), outline=(228, 252, 255), width=4)
    dr.rounded_rectangle([342, 258, 488, 310], radius=5, fill=(235, 254, 255))

    # --- Armed Cyan MEGA-CORE Reflex Sight & Bar [0..512, 336..416] ---
    dr.rounded_rectangle([10, 340, 502, 412], radius=10, fill=(10, 48, 82), outline=(88, 232, 255), width=4)
    for seg in range(10):
        sx0 = 24 + seg * 46
        dr.rounded_rectangle([sx0, 350, sx0 + 38, 402], radius=4, fill=(48, 214, 255))
        dr.rounded_rectangle([sx0 + 6, 358, sx0 + 32, 394], radius=3, fill=(135, 242, 255))
    dr.rounded_rectangle([128, 354, 384, 398], radius=6, fill=(10, 54, 88), outline=(140, 242, 255), width=2)
    dr.text((146, 365), "MEGA-CORE // ARMED", fill=(244, 254, 255), font=_font(19, bold=True))

    # --- Recharging Amber Bar [0..512, 424..504] ---
    dr.rounded_rectangle([10, 428, 502, 500], radius=10, fill=(58, 30, 8), outline=(255, 178, 52), width=4)
    for seg in range(6):
        sx0 = 24 + seg * 46
        dr.rounded_rectangle([sx0, 438, sx0 + 38, 490], radius=4, fill=(255, 164, 38))
    dr.rounded_rectangle([132, 442, 380, 486], radius=6, fill=(64, 32, 8), outline=(255, 198, 92), width=2)
    dr.text((150, 453), "CHAMBER CYCLING...", fill=(255, 240, 204), font=_font(19, bold=True))

    p = os.path.join(out_dir, "mmw_gauge_glow.png")
    im.save(p, "PNG", optimize=True)
    return p


def build_fx_texture(out_dir):
    """512x512 RGBA high-definition additive FX atlas (smoothly feathered to zero at every sub-swatch boundary!):
      Q1 [0..256,   0..256]   (u:0.0..0.5, v:0.0..0.5): Jagged multi-strand electric-cyan plasma lightning arc & wake
      Q2 [0..256,   256..512] (u:0.0..0.5, v:0.5..1.0): Feathered starburst rail-muzzle flash & soft Mach shock-cone
      Right [256..512, 0..512](u:0.5..1.0, v:0.0..1.0): Billowing turbulent pressurized gas/steam vent & hot spark plume
    """
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    turb = _fbm_noise(H, W, seed=606, octaves=(4, 8, 16, 32))

    # --- Q1 [0..256, 0..256]: Jagged Multi-Strand Electric-Cyan Plasma Arc ---
    ux1 = np.linspace(-1.0, 1.0, 256, dtype=np.float32)[None, :]
    vy1 = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    env_v1 = np.maximum(0.0, np.sin(vy1 * math.pi)) ** 0.75
    env_u1 = np.clip(1.0 - np.abs(ux1), 0.0, 1.0)
    jag1 = 0.16 * np.sin(vy1 * 42.0 + 0.7) + 0.09 * np.cos(vy1 * 97.0)
    jag2 = -0.18 * np.cos(vy1 * 33.0 - 0.4) + 0.08 * np.sin(vy1 * 83.0)
    bolt_main = np.exp(-((ux1 - jag1) ** 2) / 0.018) * env_v1
    bolt_sub = 0.65 * np.exp(-((ux1 - jag2) ** 2) / 0.030) * env_v1
    halo1 = np.exp(-(ux1 * ux1) / 0.34) * env_v1 * env_u1
    b_tot = np.clip(bolt_main + bolt_sub, 0.0, 1.2)
    rgba[:256, :256, 0] = np.clip((0.28 * halo1 + 0.96 * b_tot) * 255.0, 0, 255)
    rgba[:256, :256, 1] = np.clip((0.84 * halo1 + 1.00 * b_tot) * 255.0, 0, 255)
    rgba[:256, :256, 2] = np.clip((1.00 * halo1 + 1.00 * b_tot) * 255.0, 0, 255)
    rgba[:256, :256, 3] = np.clip((0.72 * halo1 + 0.98 * b_tot) * 255.0, 0, 255)

    # --- Q2 [256..512, 0..256]: Translucent Electric-Cyan Starburst Flash & Wispy Mach Shock-Halo ---
    # Scaled by /98.0 so alpha reaches 0.000 well inside UV_FLASH=(0.03,0.53,0.47,0.97) -> ZERO hard polygon edges!
    yy2, xx2 = np.mgrid[0:256, 0:256].astype(np.float32)
    rx2 = (xx2 - 127.5) / 98.0
    ry2 = (yy2 - 127.5) / 98.0
    rr2 = np.sqrt(rx2 * rx2 + ry2 * ry2)
    ang2 = np.arctan2(ry2, rx2)
    fall2 = np.clip(1.0 - rr2, 0.0, 1.0) ** 2.4
    rays = (0.18 + 0.82 * (np.cos(ang2 * 4.0) ** 8)) * np.exp(-rr2 * 2.6) * fall2
    shock_band = 0.46 * np.exp(-((rr2 - 0.62) ** 2) / 0.009) * (np.clip(1.0 - rr2, 0.0, 1.0) ** 1.4)
    hot_core = 0.85 * np.exp(-rr2 * 7.5) * fall2
    c_halo = rays + shock_band
    rgba[256:, :256, 0] = np.clip((0.18 * c_halo + 0.95 * hot_core) * 255.0, 0, 255)
    rgba[256:, :256, 1] = np.clip((0.82 * c_halo + 0.98 * hot_core) * 255.0, 0, 255)
    rgba[256:, :256, 2] = np.clip((1.00 * (c_halo + hot_core)) * 255.0, 0, 255)
    rgba[256:, :256, 3] = np.clip((0.62 * c_halo + 0.92 * hot_core) * 255.0, 0, 255)

    # --- Right Half [0..512, 256..512]: Seamless-Wrap Pressurized Ionized Compensator Jet Plume ---
    # Wraps seamlessly around tube circumference (u) while erupting bright at nozzle (v~0.14) & dissipating to v=1.0!
    yy3, xx3 = np.mgrid[0:512, 0:256].astype(np.float32)
    u_ang = (xx3 / 256.0) * (2.0 * math.pi)
    v_jet = yy3 / 511.0
    # Periodic angular streaks around jet circumference (seamless at u=0 / u=1!)
    streak = 0.78 + 0.22 * np.cos(u_ang * 3.0 + v_jet * 5.0) * np.cos(u_ang * 2.0 - v_jet * 3.0)
    u_guard = np.maximum(0.0, np.sin(np.clip(xx3 / 255.0, 0.0, 1.0) * math.pi)) ** 0.25  # zero seam bleed at x=256/511
    nozzle_on = np.clip(v_jet / 0.14, 0.0, 1.0) ** 0.85
    tail_fade = np.clip((0.97 - v_jet) / 0.83, 0.0, 1.0) ** 1.75
    cloud_n = np.clip(0.82 + 0.32 * turb[:, 256:], 0.42, 1.25)
    puff = nozzle_on * tail_fade * streak * cloud_n * u_guard
    hot = (np.clip((0.46 - v_jet) / 0.36, 0.0, 1.0) ** 1.6) * nozzle_on * u_guard
    rgba[:, 256:, 0] = np.clip((0.44 * puff + 0.92 * hot) * 255.0, 0, 255)
    rgba[:, 256:, 1] = np.clip((0.86 * puff + 0.98 * hot) * 255.0, 0, 255)
    rgba[:, 256:, 2] = np.clip((1.00 * puff + 1.00 * hot) * 255.0, 0, 255)
    rgba[:, 256:, 3] = np.clip((0.78 * puff + 0.35 * hot) * 235.0, 0, 255)

    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    p = os.path.join(out_dir, "mmw_fx.png")
    im.save(p, "PNG", optimize=True)
    return p


def build_all_textures(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    return {
        "chrome_axle": build_chrome_axle_texture(out_dir),
        "wheel": build_wheel_texture(out_dir),
        "gun_metal": build_gun_metal_texture(out_dir),
        "hand": build_hand_texture(out_dir),
        "gauge_glow": build_gauge_glow_texture(out_dir),
        "fx": build_fx_texture(out_dir),
    }
