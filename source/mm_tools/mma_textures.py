"""Procedural high-resolution texture & Quake shader generator for the 4-Version Mega Man Arsenal:
  - progs/mma_wheel.png    (1024x1024: 5-ribbed pneumatic tire w/ high-contrast sipes & chalk tick marks +
                            glossy white stamped-steel rims w/ 4 oval vent windows & sealed ball bearing
                            matching the uploaded video so wheel spin in Idle is 100% unmistakable!)
  - progs/mma_arsenal.png  (1024x1024: cast siege-cannon iron, burnished riveted brass, oiled American walnut,
                            translucent golden surgical latex bands, stitched leather slingshot pouch,
                            woven matte carbon bow limbs, braided bowstring & cam alloy, glowing fiber-optic
                            sight / sizzling cannon fuse, and woven red mechanic's shop polishing rag!)
  - progs/mma_fx.png       (512x512 RGBA: fiery cannon muzzle blast, cyan-white supersonic air-snap ring,
                            8-ray chrome polish star-sparkle glint, and warm breech smoke/fuse spark!)
  - scripts/mm_arsenal.shader
"""
import math
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import mmw_textures

# UV Rects in mma_arsenal.png (u0, v0, u1, v1)
UV_CANNON_IRON   = (0.02, 0.02, 0.48, 0.23)
UV_BRASS_BAND    = (0.52, 0.02, 0.98, 0.23)
UV_WALNUT_WOOD   = (0.02, 0.27, 0.48, 0.48)
UV_LATEX_AMBER   = (0.52, 0.27, 0.74, 0.48)
UV_POUCH_LEATHER = (0.77, 0.27, 0.98, 0.48)
UV_CARBON_LIMB   = (0.02, 0.52, 0.48, 0.73)
UV_BOW_CAM_STR   = (0.52, 0.52, 0.74, 0.73)
UV_FIBER_SIGHT   = (0.77, 0.52, 0.98, 0.73)
UV_SHOP_RAG      = (0.02, 0.77, 0.34, 0.98)
UV_DARK_BORE     = (0.37, 0.77, 0.66, 0.98)
UV_COIL_STEEL    = (0.69, 0.77, 0.98, 0.98)

# UV Rects in mma_fx.png (u0, v0, u1, v1)
UV_FX_BLAST = (0.02, 0.02, 0.48, 0.48)
UV_FX_SNAP  = (0.52, 0.02, 0.98, 0.48)
UV_FX_GLINT = (0.02, 0.52, 0.48, 0.98)
UV_FX_SMOKE = (0.52, 0.52, 0.98, 0.98)


def _font(size, bold=True):
    candidates = ["consolab.ttf", "arialbd.ttf", "tahomabd.ttf"] if bold else ["consola.ttf", "arial.ttf", "tahoma.ttf"]
    for nm in candidates:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=77, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.Resampling.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def build_mma_wheel_texture(out_path):
    """1024x1024 high-readability wheel atlas matching the uploaded video:
      Q1 [0..512,   0..512]   (u:0.0..0.5, v:0.0..0.5): 5-ribbed rubber tread w/ bold sipes & tread wear bands
      Q2 [0..512,   512..1024](u:0.5..1.0, v:0.0..0.5): Molded rubber sidewall w/ raised lettering & chalk marks
      Q3 [512..1024,0..512]   (u:0.0..0.5, v:0.5..1.0): Outer glossy white concave dish rim w/ 4 oval vent windows
      Q4 [512..1024,512..1024](u:0.5..1.0, v:0.5..1.0): Inner white rim w/ 4 bold oval vent holes & ball-bearing hub!
    """
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    grain = _fbm(H, W, seed=505, octaves=(2, 4, 8, 16, 32))

    # --- Q1 [0..512, 0..512]: 5-Ribbed Tire Tread with Bold Sipes so Rotation Pops! ---
    ux = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[:, None]
    groove_mask = np.zeros_like(ux)
    for gc in (0.21, 0.40, 0.60, 0.79):
        groove_mask += np.exp(-((ux - gc) ** 2) / (2.0 * 0.022 ** 2))
    groove_mask = np.clip(groove_mask, 0.0, 1.0)

    # Bold transverse tread lugs / sipes + 2 subtle shop-chalk inspection stripes across ribs so spin reads instantly!
    sipes = 0.24 * (np.sin(vy * 28.0) > 0.45).astype(np.float32) * (1.0 - groove_mask)
    chalk1 = np.exp(-((vy - 1.25) ** 2) / 0.008) * (1.0 - groove_mask)
    chalk2 = np.exp(-((vy - 4.40) ** 2) / 0.006) * (1.0 - groove_mask)
    shoulder = 1.0 - 0.20 * ((2.0 * ux - 1.0) ** 4)
    base_rub = (48.0 - 33.0 * groove_mask - 11.0 * sipes) * shoulder + 4.8 * grain[:512, :512]
    dust = 9.0 * (1.0 - groove_mask) * (0.55 + 0.45 * np.sin(vy * 4.0 + 0.7))
    tread_c = np.clip(base_rub + dust + 38.0 * chalk1 + 24.0 * chalk2, 7.0, 135.0)
    arr[:512, :512, 0] = tread_c * 0.97
    arr[:512, :512, 1] = tread_c * 0.99
    arr[:512, :512, 2] = tread_c * 1.04

    # --- Q2 [0..512, 512..1024]: Polar Molded Rubber Sidewall ---
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)

    sw = 39.0 + 12.0 * np.exp(-((rr - 0.78) ** 2) / 0.008)
    sw += 12.0 * np.exp(-((rr - 0.61) ** 2) / 0.0003) - 9.0 * np.exp(-((rr - 0.625) ** 2) / 0.0003)
    sw += 9.0 * np.exp(-((rr - 0.89) ** 2) / 0.0003) - 7.0 * np.exp(-((rr - 0.903) ** 2) / 0.0003)
    # Radial molded sidewall ribs (8 ribs around tire sidewall!) so spinning sidewall reads super clearly!
    sw_ribs = 9.5 * (np.cos(ang * 8.0) > 0.78).astype(np.float32) * np.exp(-((rr - 0.75) ** 2) / 0.012)
    sw = sw + sw_ribs - 16.0 * np.exp(-((rr - 0.56) ** 2) / 0.0008) + 3.8 * grain[:512, 512:]
    arr[:512, 512:, 0] = np.clip(sw * 0.97, 10, 96)
    arr[:512, 512:, 1] = np.clip(sw * 0.99, 10, 98)
    arr[:512, 512:, 2] = np.clip(sw * 1.05, 12, 104)

    # Helper for the 4 stamped oval ventilation windows seen in 00:03-00:04 of the uploaded video!
    def add_four_oval_windows(rim_img, hole_r=0.52, rad_w=0.115, tan_w=0.175, depth=138.0):
        out = rim_img.copy()
        for k in range(4):
            a0 = math.radians(k * 90.0 + 45.0)
            ca, sa = math.cos(a0), math.sin(a0)
            # Local coords centered on oval window: u_rad along radius, u_tan tangential
            dx = rx - hole_r * ca
            dy = ry - hole_r * sa
            u_rad = dx * ca + dy * sa
            u_tan = -dx * sa + dy * ca
            ell = (u_rad / rad_w) ** 2 + (u_tan / tan_w) ** 2
            # Crisp stamped steel bevel highlight ring around ell ~ 1.15, deep shadowed cutout inside ell < 0.88!
            bevel = 26.0 * np.exp(-((ell - 1.18) ** 2) / 0.08)
            cavity = depth * (1.0 / (1.0 + np.exp(np.clip((ell - 0.88) * 14.0, -40.0, 40.0))))
            out = out + bevel - cavity
        return out

    # --- Q3 [512..1024, 0..512]: Stamped Off-White Steel Outer Concave Dish Rim ---
    rim = np.full((512, 512), 232.0, dtype=np.float32)
    rim += 22.0 * np.exp(-((rr - 0.93) ** 2) / 0.0012)
    rim -= 36.0 * np.exp(-((rr - 0.83) ** 2) / 0.0022)
    rim -= 16.0 * np.exp(-((rr - 0.52) ** 2) / 0.045)
    rim += 14.0 * (rx * -0.55 + ry * -0.55) * np.clip(1.0 - np.abs(rr - 0.55), 0.0, 1.0)
    rim = add_four_oval_windows(rim, hole_r=0.50, rad_w=0.105, tan_w=0.165, depth=118.0)
    rim -= 28.0 * np.exp(-((rr - 0.26) ** 2) / 0.0009)
    rim += 10.0 * (rr < 0.24).astype(np.float32)
    # Schrader valve grommet shadow at angle = -35 deg, r = 0.66
    va = math.radians(-35.0)
    vdx = rx - 0.66 * math.cos(va)
    vdy = ry - 0.66 * math.sin(va)
    rim -= 110.0 * np.exp(-(vdx * vdx + vdy * vdy) / 0.0018)
    rim += 2.6 * grain[512:, :512]
    arr[512:, :512, 0] = np.clip(rim * 0.985, 22, 253)
    arr[512:, :512, 1] = np.clip(rim * 0.995, 22, 254)
    arr[512:, :512, 2] = np.clip(rim * 1.015, 25, 255)

    # --- Q4 [512..1024, 512..1024]: Inner White Rim w/ 4 Bold Oval Cutouts & Sealed Ball-Bearing Hub (Video 00:04!) ---
    irim = np.full((512, 512), 226.0, dtype=np.float32)
    irim += 20.0 * np.exp(-((rr - 0.92) ** 2) / 0.0015) - 30.0 * np.exp(-((rr - 0.82) ** 2) / 0.0025)
    irim = add_four_oval_windows(irim, hole_r=0.53, rad_w=0.118, tan_w=0.182, depth=158.0)
    # Central sealed ball-bearing race (outer chrome ring r=0.26..0.31, black rubber dust seal r=0.16..0.25, inner steel race r<0.15)
    seal_mask = (rr >= 0.155) & (rr <= 0.255)
    outer_race = (rr > 0.255) & (rr <= 0.315)
    inner_bore = rr < 0.095
    irim = np.where(outer_race, 185.0 + 35.0 * np.cos(ang * 2.0), irim)
    irim = np.where(seal_mask, 42.0 + 8.0 * np.sin(ang * 6.0), irim)
    irim = np.where(inner_bore, 30.0, irim)
    irim += 2.8 * grain[512:, 512:]
    arr[512:, 512:, 0] = np.clip(irim * 0.985, 18, 252)
    arr[512:, 512:, 1] = np.clip(irim * 0.995, 18, 254)
    arr[512:, 512:, 2] = np.clip(irim * 1.015, 20, 255)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    f_sw = _font(16, bold=True)
    label = "4.10/3.50-4  MEGA-MAN PNEUMATIC  •  HIGH-RPM  •  "
    for i, ch in enumerate(label):
        a_ch = math.radians(i * (360.0 / len(label)))
        tx = 768 + math.cos(a_ch) * 184
        ty = 256 + math.sin(a_ch) * 184
        dr.text((tx - 4, ty - 6), ch, fill=(68, 70, 78), font=f_sw)
        dr.text((tx - 5, ty - 7), ch, fill=(26, 28, 32), font=f_sw)

    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_mma_arsenal_texture(out_path):
    """1024x1024 rich multi-material weapon atlas for Cannon, Slingshot, Bow & Polishing Rag."""
    W = H = 1024
    arr = np.full((H, W, 3), 42.0, dtype=np.float32)
    nc = _fbm(H, W, seed=611, octaves=(4, 8, 16, 32))
    nf = _fbm(H, W, seed=612, octaves=(2, 4, 8))

    # 1. [0..256, 0..512] UV_CANNON_IRON: Heavy Cast Naval/Siege Cannon Iron w/ hammered sheen & rivets
    yi, xi = np.mgrid[0:256, 0:512].astype(np.float32)
    iron = 68.0 + 16.0 * nc[:256, :512] + 9.0 * nf[:256, :512]
    iron += 18.0 * np.cos((yi / 255.0 - 0.38) * math.pi)
    arr[:256, :512, 0] = np.clip(iron * 1.02, 20, 165)
    arr[:256, :512, 1] = np.clip(iron * 1.00, 20, 165)
    arr[:256, :512, 2] = np.clip(iron * 1.05, 22, 175)

    # 2. [0..256, 512..1024] UV_BRASS_BAND: Burnished Naval Brass Bands, Sights & Cams
    yb, xb = np.mgrid[0:256, 0:512].astype(np.float32)
    b_sheen = 0.68 + 0.24 * np.cos((yb / 255.0 - 0.35) * math.pi * 2.0) + 0.08 * nf[:256, 512:]
    # Rivet row along center v
    for rx_p in range(32, 512, 64):
        d2 = (xb - rx_p) ** 2 + (yb - 128.0) ** 2
        b_sheen += 0.18 * np.exp(-d2 / 95.0) - 0.14 * np.exp(-((np.sqrt(d2) - 11.5) ** 2) / 8.0)
    arr[:256, 512:, 0] = np.clip(b_sheen * 238.0, 45, 255)
    arr[:256, 512:, 1] = np.clip(b_sheen * 186.0, 35, 235)
    arr[:256, 512:, 2] = np.clip(b_sheen * 84.0, 15, 145)

    # 3. [256..512, 0..512] UV_WALNUT_WOOD: Oiled American Walnut Wood Grain (Cannon Stock & Slingshot Y-Fork!)
    yw, xw = np.mgrid[0:256, 0:512].astype(np.float32)
    grain_wave = np.sin(yw * 0.26 + 3.8 * nc[256:512, :512] + 0.015 * xw)
    wood = 0.58 + 0.22 * grain_wave + 0.08 * nf[256:512, :512]
    arr[256:512, :512, 0] = np.clip(wood * 168.0, 38, 218)
    arr[256:512, :512, 1] = np.clip(wood * 102.0, 22, 148)
    arr[256:512, :512, 2] = np.clip(wood * 58.0, 12, 92)

    # 4. [256..512, 512..768] UV_LATEX_AMBER: Golden-Amber Surgical Latex Elastic Slingshot Tubing!
    yl, xl = np.mgrid[0:256, 0:256].astype(np.float32)
    lat_hi = 0.72 + 0.26 * np.cos((yl / 255.0 - 0.35) * math.pi * 2.0) + 0.04 * nf[256:512, 512:768]
    arr[256:512, 512:768, 0] = np.clip(lat_hi * 248.0, 80, 255)
    arr[256:512, 512:768, 1] = np.clip(lat_hi * 176.0, 50, 228)
    arr[256:512, 512:768, 2] = np.clip(lat_hi * 46.0, 12, 95)

    # 5. [256..512, 768..1024] UV_POUCH_LEATHER: Stitched Saddle-Leather Slingshot Pouch & Paracord Wrap
    yp, xp = np.mgrid[0:256, 0:256].astype(np.float32)
    leath = 96.0 + 18.0 * nc[256:512, 768:] + 11.0 * nf[256:512, 768:]
    # Saddle-stitch border dashes near top & bottom
    stitch = ((np.abs(yp - 26.0) < 4.0) | (np.abs(yp - 230.0) < 4.0)) & ((xp.astype(np.int32) // 14) % 2 == 0)
    arr[256:512, 768:, 0] = np.where(stitch, 226.0, np.clip(leath * 1.18, 32, 175))
    arr[256:512, 768:, 1] = np.where(stitch, 198.0, np.clip(leath * 0.84, 22, 130))
    arr[256:512, 768:, 2] = np.where(stitch, 138.0, np.clip(leath * 0.56, 14, 92))

    # 6. [512..768, 0..512] UV_CARBON_LIMB: Woven Matte Carbon-Fiber & Teal-Anodized Bow Riser/Limbs
    yc, xc = np.mgrid[0:256, 0:512].astype(np.float32)
    twill = 0.5 + 0.5 * np.sin((xc + yc) * 0.65) * np.cos((xc - yc) * 0.65)
    carb = 48.0 + 26.0 * twill + 7.0 * nf[512:768, :512]
    # Crisp anodized cyan-emerald racing stripe along limb edge
    stripe = np.exp(-((yc - 34.0) ** 2) / 55.0) + np.exp(-((yc - 222.0) ** 2) / 55.0)
    arr[512:768, :512, 0] = np.clip(carb * 0.92 + 22.0 * stripe, 18, 195)
    arr[512:768, :512, 1] = np.clip(carb * 1.02 + 135.0 * stripe, 20, 240)
    arr[512:768, :512, 2] = np.clip(carb * 1.12 + 165.0 * stripe, 24, 252)

    # 7. [512..768, 512..768] UV_BOW_CAM_STR: Waxed Braided Bowstring, Alloy Cams & Bright Arrow Fletching
    ys, xs = np.mgrid[0:256, 0:256].astype(np.float32)
    braid = 172.0 + 36.0 * np.sin(xs * 0.85 + ys * 0.45) + 8.0 * nf[512:768, 512:768]
    # Top half = silver-white braided string/alloy; bottom half = blazing lime/orange arrow vane fletching!
    is_vane = ys > 136.0
    vane_rib = 0.82 + 0.18 * np.sin(xs * 1.2)
    arr[512:768, 512:768, 0] = np.where(is_vane, 250.0 * vane_rib, np.clip(braid * 0.96, 60, 245))
    arr[512:768, 512:768, 1] = np.where(is_vane, 92.0 * vane_rib,  np.clip(braid * 1.00, 60, 248))
    arr[512:768, 512:768, 2] = np.where(is_vane, 38.0 * vane_rib,  np.clip(braid * 1.05, 65, 255))

    # 8. [512..768, 768..1024] UV_FIBER_SIGHT: Glowing Neon Sight Pins & Sizzling Cannon Fuse Cord
    yf, xf = np.mgrid[0:256, 0:256].astype(np.float32)
    is_fuse = yf > 128.0
    fuse_twist = 0.65 + 0.35 * np.sin(xf * 0.75 + yf * 0.55)
    arr[512:768, 768:, 0] = np.where(is_fuse, 235.0 * fuse_twist, 65.0)
    arr[512:768, 768:, 1] = np.where(is_fuse, 148.0 * fuse_twist, 252.0)
    arr[512:768, 768:, 2] = np.where(is_fuse, 62.0 * fuse_twist,  112.0)

    # 9. [768..1024, 0..356] UV_SHOP_RAG: Classic Red Mechanic's Shop Polishing Rag (for CoD Clean-the-Bar Inspect!)
    yr, xr = np.mgrid[0:256, 0:356].astype(np.float32)
    weave = 0.88 + 0.12 * np.sin(xr * 1.4) * np.sin(yr * 1.4) + 0.08 * nc[768:, :356]
    # Subtle dark chrome-polish smudge in the middle of the cloth for comedy realism!
    smudge = 1.0 - 0.32 * np.exp(-(((xr - 178.0) / 68.0) ** 2 + ((yr - 128.0) / 56.0) ** 2))
    arr[768:, :356, 0] = np.clip(218.0 * weave * smudge, 45, 248)
    arr[768:, :356, 1] = np.clip(48.0 * weave * smudge, 14, 95)
    arr[768:, :356, 2] = np.clip(54.0 * weave * smudge, 16, 102)

    # 10. [768..1024, 356..688] UV_DARK_BORE: Soot-Black Cannon Bore Interior & Slotted Liner
    yd, xd = np.mgrid[0:256, 0:332].astype(np.float32)
    bore = 24.0 + 7.0 * nc[768:, 356:688] + 5.0 * np.sin(xd * 0.35)
    arr[768:, 356:688, 0] = np.clip(bore, 8, 48)
    arr[768:, 356:688, 1] = np.clip(bore, 8, 48)
    arr[768:, 356:688, 2] = np.clip(bore * 1.08, 10, 54)

    # 11. [768..1024, 688..1024] UV_COIL_STEEL: Brushed Spring Steel & Knurled Tactical Checkering
    yk, xk = np.mgrid[0:256, 0:336].astype(np.float32)
    knurl = 0.5 + 0.5 * np.sin((xk + yk) * 0.55) * np.sin((xk - yk) * 0.55)
    st_val = 128.0 + 38.0 * knurl + 10.0 * nf[768:, 688:]
    arr[768:, 688:, 0] = np.clip(st_val * 0.96, 35, 225)
    arr[768:, 688:, 1] = np.clip(st_val * 0.99, 35, 230)
    arr[768:, 688:, 2] = np.clip(st_val * 1.05, 40, 242)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    f_st = _font(20, bold=True)
    dr.text((26, 22), "BROADSIDE MK-IV // MEGA-BORE", fill=(188, 152, 92), font=f_st)
    dr.text((26, 536), "RECURVE PRO // 180-LB DRAW", fill=(95, 232, 245), font=f_st)
    dr.text((22, 992), "CHROME POLISH RAG", fill=(248, 185, 185), font=_font(16, bold=True))

    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_mma_fx_texture(out_path):
    """512x512 RGBA additive FX atlas:
      Q1 [0..256,   0..256]: Fiery amber-gold cannon blast shockwave
      Q2 [0..256,   256..512]: Crisp cyan-white supersonic air-snap vortex ring (Slingshot / Bow / Throw)
      Q3 [256..512, 0..256]: Brilliant 8-Ray CoD Chrome-Polish Star-Sparkle Glint!
      Q4 [256..512, 256..512]: Sizzling cannon fuse spark / warm smoke puff
    """
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    nx = (xx - 127.5) / 120.0
    ny = (yy - 127.5) / 120.0
    rr = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)

    # Q1: Fiery Cannon Muzzle Blast Ring
    ring1 = np.exp(-((rr - 0.68) ** 2) / 0.022) * (0.72 + 0.28 * np.cos(ang * 12.0))
    core1 = np.exp(-(rr * rr) / 0.14)
    a1 = np.clip(ring1 + 0.65 * core1, 0.0, 1.0)
    rgba[:256, :256, 0] = 255.0 * a1
    rgba[:256, :256, 1] = (185.0 * ring1 + 240.0 * core1)
    rgba[:256, :256, 2] = (55.0 * ring1 + 150.0 * core1)
    rgba[:256, :256, 3] = 255.0 * a1

    # Q2: Supersonic Cyan-White Air-Snap Ring
    ring2 = np.exp(-((rr - 0.72) ** 2) / 0.014) * (0.80 + 0.20 * np.sin(ang * 8.0))
    rgba[:256, 256:, 0] = 175.0 * ring2
    rgba[:256, 256:, 1] = 238.0 * ring2
    rgba[:256, 256:, 2] = 255.0 * ring2
    rgba[:256, 256:, 3] = 255.0 * np.clip(ring2, 0.0, 1.0)

    # Q3: Brilliant 8-Ray CoD Chrome-Polish Star-Sparkle Glint!
    ray_main = np.exp(-(nx * nx) / 0.0045) * np.exp(-(ny * ny) / 0.28) + np.exp(-(ny * ny) / 0.0045) * np.exp(-(nx * nx) / 0.28)
    dx1 = (nx + ny) * 0.7071
    dy1 = (nx - ny) * 0.7071
    ray_diag = 0.65 * (np.exp(-(dx1 * dx1) / 0.005) * np.exp(-(dy1 * dy1) / 0.14) + np.exp(-(dy1 * dy1) / 0.005) * np.exp(-(dx1 * dx1) / 0.14))
    halo = 0.55 * np.exp(-(rr * rr) / 0.045)
    glint = np.clip(ray_main + ray_diag + halo, 0.0, 1.0)
    rgba[256:, :256, 0] = 255.0 * glint
    rgba[256:, :256, 1] = 252.0 * glint
    rgba[256:, :256, 2] = np.clip(225.0 * glint + 30.0 * ray_main, 0, 255)
    rgba[256:, :256, 3] = 255.0 * glint

    # Q4: Sizzling Fuse Spark / Warm Puff
    sp_rays = 0.5 + 0.5 * np.cos(ang * 10.0)
    spark = np.exp(-(rr * rr) / 0.16) * (0.65 + 0.35 * sp_rays)
    rgba[256:, 256:, 0] = 255.0 * spark
    rgba[256:, 256:, 1] = 205.0 * spark
    rgba[256:, 256:, 2] = 85.0 * spark
    rgba[256:, 256:, 3] = 255.0 * np.clip(spark, 0.0, 1.0)

    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    im.save(out_path, "PNG", optimize=True)
    return out_path


SHADER_TEXT = """// written by mm_tools/build_megaman_arsenal_4v.py

progs/mma_wheel
{
\tcull none
\t{
\t\tmap progs/mma_wheel
\t\trgbGen lightingDiffuse
\t}
}

progs/mma_arsenal
{
\tcull none
\t{
\t\tmap progs/mma_arsenal
\t\trgbGen lightingDiffuse
\t}
}

progs/mma_fx
{
\tcull none
\t{
\t\tmap progs/mma_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""


def ensure_arsenal_textures_and_shader(mod_dir, stage_dir):
    os.makedirs(stage_dir, exist_ok=True)
    progs_dir = os.path.join(mod_dir, "progs")
    scripts_dir = os.path.join(mod_dir, "scripts")
    os.makedirs(progs_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    # Ensure shared chrome_axle & hand textures exist
    p_chrome_stage = mmw_textures.build_chrome_axle_texture(stage_dir)
    p_hand_stage = mmw_textures.build_hand_texture(stage_dir)
    for src_p in (p_chrome_stage, p_hand_stage):
        dst_p = os.path.join(progs_dir, os.path.basename(src_p))
        if not os.path.exists(dst_p):
            shutil.copy2(src_p, dst_p)

    p_wheel = build_mma_wheel_texture(os.path.join(stage_dir, "mma_wheel.png"))
    p_arsenal = build_mma_arsenal_texture(os.path.join(stage_dir, "mma_arsenal.png"))
    p_fx = build_mma_fx_texture(os.path.join(stage_dir, "mma_fx.png"))

    for src_p in (p_wheel, p_arsenal, p_fx):
        shutil.copy2(src_p, os.path.join(progs_dir, os.path.basename(src_p)))

    shader_path = os.path.join(scripts_dir, "mm_arsenal.shader")
    with open(shader_path, "w", encoding="ascii", newline="\n") as f:
        f.write(SHADER_TEXT)

    return dict(
        chrome_axle=p_chrome_stage,
        hand=p_hand_stage,
        wheel=p_wheel,
        arsenal=p_arsenal,
        fx=p_fx,
        shader=shader_path,
    )
