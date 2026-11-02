"""Procedural high-resolution texture synthesis for the Quake 'WEW CANNON' weapon suite:

Generates staging full-brightness textures (for WebGL2 / GLB / Blender renders),
DarkPlaces HDR-calibrated textures in `progs/`, and a unified `512x256` / `1024x512`
classic Quake `.mdl` atlas (for `IDPO` v6 `.mdl` + external `_0.tga` hires skin):

  1. `wew_silver.png` (1024x1024):
       - u:[0.0..0.5], v:[0.0..0.5] : Anisotropic Liquid-Mirror Silver & Brushed Platinum Barrel Metal
       - u:[0.5..1.0], v:[0.0..0.5] : Heavy Machined Silver Reinforcing Hoops, Rivets & Rifled Bore
       - u:[0.0..1.0], v:[0.5..0.78]: Embossed Heavy Silver-on-Obsidian `"WEW CANNON"` Artillery Plaque
       - u:[0.0..1.0], v:[0.78..1.0]: Fluted Hydraulic Recoil Cylinders, Saddle Cradle & Grip Wrap
  2. `wew_hand.png`   (512x512):
       - Quake Ranger distressed leather combat glove, silver-steel knuckle plate & riveted bracer
  3. `wew_core.png`   (512x512):
       - Self-illuminated Breech Pressure Dial (`WEW-METER`), Plasma Core Window, Barrel Energy Vents,
         and the Colossal Glowing Silver-Plasma `"WEW"` Cannonball Projectile!
  4. `wew_fx.png`     (512x512 RGBA):
       - Starburst Muzzle Blast, Concentric Supersonic Shockwave Ring, Charge Arcs & Steam Plume!
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# Canonical UV rectangles shared with geometry builder (u0, v0, u1, v1) in [0..1] top-down UV space
UV_SILVER_BARREL  = (0.02, 0.02, 0.48, 0.48)
UV_SILVER_BAND    = (0.52, 0.02, 0.98, 0.185)
UV_HAZARD_STRIPE  = (0.52, 0.195, 0.98, 0.255)
UV_GUNMETAL_ARMOR = (0.52, 0.270, 0.98, 0.375)
UV_DARK_BORE      = (0.52, 0.385, 0.98, 0.485)
UV_WEW_PLAQUE     = (0.015, 0.510, 0.985, 0.770)
UV_HYDRAULIC      = (0.02, 0.795, 0.48, 0.985)
UV_GRIP_WRAP      = (0.52, 0.795, 0.73, 0.985)
UV_CRT_VENT       = (0.76, 0.800, 0.985, 0.885)
UV_CRT_BEZEL      = (0.76, 0.895, 0.985, 0.985)

UV_CORE_DIAL     = (0.02, 0.02, 0.48, 0.48)
UV_CORE_PLASMA   = (0.52, 0.02, 0.98, 0.48)
UV_MUZZLE_THROAT = (0.02, 0.52, 0.98, 0.98)

UV_FX_STARBURST  = (0.02, 0.02, 0.48, 0.48)
UV_FX_SHOCKRING  = (0.52, 0.02, 0.98, 0.48)
UV_FX_LIGHTNING  = (0.02, 0.52, 0.48, 0.98)
UV_FX_STEAM      = (0.52, 0.52, 0.98, 0.98)


def _font(size, prefer=("ariblk.ttf", "impact.ttf", "tahomabd.ttf", "arialbd.ttf", "consolab.ttf")):
    for nm in prefer:
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
        im = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _draw_rivet(draw, cx, cy, r):
    draw.ellipse((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), fill=(26, 30, 38))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(175, 186, 202))
    draw.arc((cx - r, cy - r, cx + r, cy + r), 195, 345, fill=(248, 252, 255), width=2)
    draw.arc((cx - r, cy - r, cx + r, cy + r), 15, 165, fill=(72, 80, 94), width=2)


def build_silver_texture(out_dir):
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise_fine = _fbm(H, W, seed=101, octaves=(2, 4, 8, 16))
    noise_med = _fbm(H, W, seed=202, octaves=(8, 16, 32, 64))

    # --- 1. Q1 [0..512, 0..512]: Seamless Machined Military Titanium-Silver Fluted Barrel ---
    # Exact period over u in [0.02..0.48] so cylindrical wrap has ZERO seam!
    u_px = (np.arange(512, dtype=np.float32)[None, :] / 512.0 - 0.02) / 0.46 * (2.0 * math.pi)
    v = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    # Anisotropic satin-titanium base + 8 crisp machined longitudinal barrel flutes!
    flute_8 = np.cos(8.0 * u_px)
    flute_groove = np.exp(-((np.sin(4.0 * u_px)) ** 2) / 0.035)  # 8 dark machined flute channels
    refl = (
        0.64
        + 0.20 * np.cos(u_px - 1.05)
        + 0.11 * np.cos(2.0 * u_px + 0.40)
        + 0.09 * flute_8
        - 0.22 * flute_groove
    )
    # Brushed steel lathe grain + machined ordnance ring seams at v = 0.22, 0.48, 0.74
    lathe = 0.022 * np.sin(v * 380.0) + 0.025 * noise_fine[:512, :512]
    ring_seams = (
        np.exp(-((v - 0.22) ** 2) / 0.00018)
        + np.exp(-((v - 0.50) ** 2) / 0.00018)
        + np.exp(-((v - 0.76) ** 2) / 0.00018)
    )
    end_ao = (1.0 - 0.24 * np.exp(-((v - 0.03) ** 2) / 0.0012)) * (1.0 - 0.24 * np.exp(-((v - 0.97) ** 2) / 0.0012))
    s_val = np.clip((refl + lathe) * end_ao * (1.0 - 0.48 * ring_seams), 0.16, 1.04)
    arr[:512, :512, 0] = np.clip(s_val * 228.0, 0, 255)
    arr[:512, :512, 1] = np.clip(s_val * 236.0, 0, 255)
    arr[:512, :512, 2] = np.clip(s_val * 246.0 + 4.0, 0, 255)

    # --- 2. Q2 Top [0..194, 512..1024]: Heavy Brushed Titanium & Gunmetal Locking Collars (`UV_SILVER_BAND`) ---
    ub = (np.arange(512, dtype=np.float32)[None, :] / 512.0 - 0.02) / 0.46 * (2.0 * math.pi)
    vb = np.linspace(0.0, 1.0, 194, dtype=np.float32)[:, None]
    bevel = np.maximum(0.0, np.sin(np.clip(vb, 0.0, 1.0) * math.pi)) ** 0.42
    center_chan = np.exp(-((vb - 0.50) ** 2) / 0.012)
    hoop = (0.58 + 0.22 * np.cos(ub - 1.05) + 0.10 * np.cos(2.0 * ub)) * (0.44 + 0.58 * bevel) * (1.0 - 0.34 * center_chan)
    arr[:194, 512:, 0] = np.clip(hoop * 222.0, 20, 252)
    arr[:194, 512:, 1] = np.clip(hoop * 230.0, 22, 254)
    arr[:194, 512:, 2] = np.clip(hoop * 242.0, 26, 255)

    # --- 2b. Q2 Hazard Band [194..268, 512..1024]: 45-Deg Military Yellow/Black Hazard Stripes (`UV_HAZARD_STRIPE`) ---
    xh = np.arange(512, dtype=np.float32)[None, :]
    yh = np.arange(74, dtype=np.float32)[:, None]
    chev = ((np.floor((xh + yh * 1.05) / 22.0).astype(np.int32)) & 1).astype(np.float32)
    wear_h = 0.88 + 0.12 * noise_fine[194:268, 512:]
    border_h = ((yh < 5) | (yh > 68)).astype(np.float32)
    haz_r = np.where(border_h > 0.5, 42.0, (28.0 + 214.0 * chev) * wear_h)
    haz_g = np.where(border_h > 0.5, 46.0, (28.0 + 172.0 * chev) * wear_h)
    haz_b = np.where(border_h > 0.5, 50.0, (26.0 + 12.0 * chev) * wear_h)
    arr[194:268, 512:, 0] = np.clip(haz_r, 12, 250)
    arr[194:268, 512:, 1] = np.clip(haz_g, 12, 220)
    arr[194:268, 512:, 2] = np.clip(haz_b, 10, 80)

    # --- 3a. Q2 Mid [268..388, 512..1024]: Parkerized Gunmetal / Olive-Drab Tactical Armor (`UV_GUNMETAL_ARMOR`) ---
    ug = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vg = np.linspace(0.0, 1.0, 120, dtype=np.float32)[:, None]
    rib_g = 0.5 + 0.5 * np.cos(ug * 2.0 * math.pi * 16.0)
    edge_hi = np.exp(-((vg - 0.08) ** 2) / 0.004) + np.exp(-((vg - 0.92) ** 2) / 0.004)
    gm_base = 54.0 + 18.0 * rib_g + 28.0 * edge_hi + 9.0 * noise_fine[268:388, 512:] + 6.0 * noise_med[268:388, 512:]
    arr[268:388, 512:, 0] = np.clip(gm_base * 0.94, 18, 165)
    arr[268:388, 512:, 1] = np.clip(gm_base * 1.01, 20, 175)
    arr[268:388, 512:, 2] = np.clip(gm_base * 0.96, 18, 168)

    # --- 3b. Q2 Bot [388..512, 512..1024]: Spiral-Rifled Blackened Bore w/ Glowing Depth (`UV_DARK_BORE`) ---
    ur = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vr = np.linspace(0.0, 1.0, 124, dtype=np.float32)[:, None]
    rifling = 0.5 + 0.5 * np.cos((ur * 12.0 + vr * 2.5) * 2.0 * math.pi)
    depth_fade = 0.20 + 0.80 * (vr ** 1.35)
    bore_v = (20.0 + 52.0 * rifling + 8.0 * noise_fine[388:512, 512:]) * depth_fade
    deep_glow = np.exp(-((vr - 0.08) ** 2) / 0.018)
    arr[388:512, 512:, 0] = np.clip(bore_v * 0.92 + deep_glow * 38.0, 6, 210)
    arr[388:512, 512:, 1] = np.clip(bore_v * 0.98 + deep_glow * 115.0, 8, 225)
    arr[388:512, 512:, 2] = np.clip(bore_v * 1.08 + deep_glow * 185.0, 10, 245)

    # --- 4. Q4 [790..1024, 0..1024]: Military Recuperator Housing (Left), OD Combat Grip (Mid), Tactical CRT (Right) ---
    uh = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vh = np.linspace(0.0, 1.0, 234, dtype=np.float32)[:, None]
    flutes = 0.46 + 0.24 * np.cos(uh * 2.0 * math.pi * 10.0) + 0.06 * np.sin(vh * 90.0)
    arr[790:, :512, 0] = np.clip(flutes * 148.0 + 8.0 * noise_fine[790:, :512], 20, 215)
    arr[790:, :512, 1] = np.clip(flutes * 158.0 + 8.0 * noise_fine[790:, :512], 24, 225)
    arr[790:, :512, 2] = np.clip(flutes * 146.0 + 8.0 * noise_fine[790:, :512], 20, 212)

    knurl = (
        0.5
        + 0.25 * np.cos((uh * 30.0 + vh * 15.0) * 2.0 * math.pi)
        + 0.25 * np.cos((uh * 30.0 - vh * 15.0) * 2.0 * math.pi)
    )
    grip = 32.0 + 30.0 * knurl + 6.0 * noise_med[790:, 512:]
    arr[790:, 512:760, 0] = np.clip(grip[:, :248] * 0.88, 14, 96)
    arr[790:, 512:760, 1] = np.clip(grip[:, :248] * 0.98, 16, 108)
    arr[790:, 512:760, 2] = np.clip(grip[:, :248] * 0.82, 12, 92)

    # Ruggedized Military Field Terminal Casing (`WEW-TAC 98` Olive-Drab / Tactical Slate, `x=760..1024, y=790..1024`)
    tac_crt = 104.0 + 9.0 * noise_fine[790:, 760:] + 6.0 * noise_med[790:, 760:]
    arr[790:, 760:, 0] = np.clip(tac_crt * 0.92, 52, 155)
    arr[790:, 760:, 1] = np.clip(tac_crt * 1.02, 58, 168)
    arr[790:, 760:, 2] = np.clip(tac_crt * 0.84, 46, 142)

    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(im)

    # Slotted cooling ports & stencil stripes on `UV_HYDRAULIC` (`x=0..512, y=790..1024`)
    for sx in range(36, 476, 56):
        draw.rectangle((sx, 822, sx + 34, 852), fill=(18, 22, 24), outline=(140, 152, 146), width=2)
        draw.rectangle((sx, 956, sx + 34, 986), fill=(18, 22, 24), outline=(140, 152, 146), width=2)
    draw.rectangle((20, 896, 492, 912), fill=(212, 168, 32))
    f_hyd = _font(15)
    draw.text((34, 895), "HYDROPNEUMATIC RECUPERATOR // 4200 PSI", fill=(20, 22, 20), font=f_hyd)

    # Molded cooling louver vents in `UV_CRT_VENT` (`y=815..900, x=780..1006`) + tactical bezel in `UV_CRT_BEZEL`
    for vy in range(822, 898, 12):
        draw.rectangle((786, vy, 1002, vy + 5), fill=(28, 32, 26))
        draw.line((786, vy + 6, 1002, vy + 6), fill=(138, 148, 126), width=1)
    # Ruggedized Field Monitor Front Control Strip (`y=916..1008`)
    draw.rectangle((774, 916, 1014, 1008), fill=(62, 68, 56), outline=(30, 34, 28), width=3)
    draw.rectangle((780, 922, 1008, 1002), outline=(132, 142, 118), width=1)
    f_crt_b = _font(15)
    draw.text((788, 952), "WEW-TAC 98", fill=(226, 232, 204), font=f_crt_b)
    for bx in (916, 938, 960):
        draw.rectangle((bx, 952, bx + 15, 969), fill=(42, 46, 40), outline=(148, 156, 136))
    draw.ellipse((980, 953, 994, 967), fill=(255, 180, 36), outline=(70, 48, 12))   # Amber LINK LED
    draw.ellipse((996, 953, 1010, 967), fill=(50, 245, 75), outline=(20, 80, 28))   # Green PWR LED

    # Add 3D armor hex-rivets along Q2 locking collar (`UV_SILVER_BAND`) and gunmetal shroud (`UV_GUNMETAL_ARMOR`)
    for rx in range(544, 1008, 48):
        _draw_rivet(draw, rx, 44, 9)
        _draw_rivet(draw, rx, 148, 9)
        _draw_rivet(draw, rx, 294, 7)
        _draw_rivet(draw, rx, 362, 7)

    # --- 5. Q3 [y=512..790, x=0..1024]: MIL-SPEC ARMORED "WEW CANNON" ORDNANCE PLAQUE ---
    # Render at 2x supersampling (2048 x 556) for razor-sharp beveled titanium-silver military typography!
    PW, PH = 2048, 556
    plaque = Image.new("RGB", (PW, PH), (168, 178, 188))
    pd = ImageDraw.Draw(plaque)

    # Brushed titanium outer armor frame
    pd.rectangle((0, 0, PW - 1, PH - 1), fill=(182, 192, 204))
    pd.rectangle((8, 8, PW - 9, PH - 9), outline=(238, 244, 250), width=7)
    pd.rectangle((16, 16, PW - 17, PH - 17), outline=(36, 42, 48), width=8)

    # Recessed dark charcoal-olive military armor plate so silver "WEW CANNON" pops with maximum contrast!
    enamel = np.zeros((PH - 64, PW - 64, 3), dtype=np.float32)
    ey = np.linspace(0.0, 1.0, PH - 64, dtype=np.float32)[:, None]
    ex = np.linspace(0.0, 1.0, PW - 64, dtype=np.float32)[None, :]
    ebase = 28.0 + 14.0 * np.sin(ey * math.pi) + 6.0 * np.cos(ex * 2.0 * math.pi)
    enamel[..., 0] = ebase * 0.94
    enamel[..., 1] = ebase * 1.04
    enamel[..., 2] = ebase * 0.96
    plaque.paste(Image.fromarray(np.clip(enamel, 10, 68).astype(np.uint8)), (32, 32))

    # Left & Right 45-degree yellow/black hazard chevron end-bars inside the armor plate!
    for hx0, hx1 in ((40, 146), (PW - 146, PW - 40)):
        hw = hx1 - hx0
        hh = PH - 80
        xx_h = np.arange(hw, dtype=np.float32)[None, :]
        yy_h = np.arange(hh, dtype=np.float32)[:, None]
        st_h = ((np.floor((xx_h + yy_h) / 26.0).astype(np.int32)) & 1).astype(np.float32)
        hbar = np.zeros((hh, hw, 3), dtype=np.uint8)
        hbar[..., 0] = np.clip(24.0 + 208.0 * st_h, 0, 255).astype(np.uint8)
        hbar[..., 1] = np.clip(24.0 + 168.0 * st_h, 0, 255).astype(np.uint8)
        hbar[..., 2] = np.clip(22.0 + 8.0 * st_h, 0, 255).astype(np.uint8)
        plaque.paste(Image.fromarray(hbar, mode="RGB"), (hx0, 40))
        pd.rectangle((hx0, 40, hx1, PH - 40), outline=(18, 22, 24), width=5)

    # Inner titanium pinstripe border & military ordnance stencils
    pd.rectangle((40, 40, PW - 41, PH - 41), outline=(156, 168, 178), width=4)
    f_mil = _font(32, prefer=("consolab.ttf", "tahomabd.ttf", "arialbd.ttf"))
    pd.text((178, 54), "XM-98 HEAVY ARTILLERY  //  155MM HV", fill=(218, 184, 62), font=f_mil)
    pd.text((PW - 720, 54), "MIL-STD-1998 // LOT WEW-01", fill=(168, 182, 176), font=f_mil)
    pd.text((178, PH - 90), "CAUTION: HIGH-IMPULSE AXIAL RECOIL", fill=(218, 184, 62), font=f_mil)
    pd.text((PW - 640, PH - 90), "ARMORED BREECH LOCKED", fill=(168, 182, 176), font=f_mil)

    # Heavy armor bolts along top & bottom rails
    for rx in (168, 560, PW // 2, PW - 560, PW - 168):
        _draw_rivet(pd, rx, 24, 11)
        _draw_rivet(pd, rx, PH - 24, 11)

    # Supersampled metallic beveled "WEW CANNON" typography between the hazard bars!
    text = "WEW CANNON"
    fsize = 236
    font = _font(fsize)
    while fsize > 80:
        font = _font(fsize)
        bb = pd.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        if tw <= (PW - 360) * 0.92 and th <= PH * 0.56:
            break
        fsize -= 6

    tx = (PW - tw) // 2 - bb[0]
    ty = (PH - th) // 2 - bb[1]

    mask_im = Image.new("L", (PW, PH), 0)
    md = ImageDraw.Draw(mask_im)
    md.text((tx, ty), text, fill=255, font=font)
    # Cut crisp military stencil bridges across vertical strokes for an authentic heavy-ordnance look!
    md.rectangle((160, PH // 2 - 5, PW - 160, PH // 2 + 5), fill=0)

    dilated = mask_im.filter(ImageFilter.MaxFilter(17))
    shadow = mask_im.filter(ImageFilter.GaussianBlur(9))
    sh_np = np.asarray(shadow, dtype=np.float32) / 255.0
    dil_np = np.asarray(dilated, dtype=np.float32) / 255.0
    msk_np = np.asarray(mask_im, dtype=np.float32) / 255.0

    blur_bevel = np.asarray(mask_im.filter(ImageFilter.GaussianBlur(3.5)), dtype=np.float32) / 255.0
    gy, gx = np.gradient(blur_bevel)
    bevel_light = np.clip(-gy * 3.8 - gx * 1.6, -1.0, 1.0)

    yy = np.arange(PH, dtype=np.float32)[:, None]
    t_rel = np.clip((yy - (PH * 0.24)) / max(1.0, PH * 0.52), 0.0, 1.0)
    chrome_grad = (
        0.92
        - 0.20 * t_rel
        - 0.30 * np.exp(-((t_rel - 0.54) ** 2) / 0.0055)
        + 0.22 * np.exp(-((t_rel - 0.43) ** 2) / 0.0045)
        + 0.16 * np.exp(-((t_rel - 0.82) ** 2) / 0.0150)
    )
    letter_lum = np.clip(chrome_grad + 0.32 * bevel_light, 0.24, 1.08)

    pl_np = np.asarray(plaque, dtype=np.float32).copy()
    trench = np.clip(dil_np - msk_np, 0.0, 1.0)
    pl_np *= (1.0 - 0.72 * sh_np[:, :, None])
    pl_np = pl_np * (1.0 - trench[:, :, None]) + np.array([12.0, 15.0, 18.0], dtype=np.float32) * trench[:, :, None]

    lr = np.clip(letter_lum * 242.0, 0, 255)
    lg = np.clip(letter_lum * 248.0, 0, 255)
    lb = np.clip(letter_lum * 255.0, 0, 255)
    let_rgb = np.stack([lr, lg, lb], axis=-1)
    pl_np = pl_np * (1.0 - msk_np[:, :, None]) + let_rgb * msk_np[:, :, None]

    plaque_final = Image.fromarray(np.clip(pl_np, 0, 255).astype(np.uint8), mode="RGB")
    plaque_1k = plaque_final.resize((1024, 278), Image.LANCZOS)
    im.paste(plaque_1k, (0, 512))

    path = os.path.join(out_dir, "wew_silver.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_hand_texture(out_dir):
    """512x512 Tactical Spec-Ops Combat Gauntlet: charcoal/OD leather, titanium knuckle armor & OD-steel bracer."""
    W = H = 512
    arr = np.zeros((H, W, 3), dtype=np.float32)
    nf = _fbm(H, W, seed=303, octaves=(4, 8, 16, 32, 64))

    # Top half [0..256]: Tactical dark charcoal / olive-drab reinforced combat glove
    grain = 52.0 + 16.0 * nf[:256, :]
    arr[:256, :, 0] = np.clip(grain * 0.94, 18, 108)
    arr[:256, :, 1] = np.clip(grain * 1.02, 20, 116)
    arr[:256, :, 2] = np.clip(grain * 0.86, 16, 98)

    # Bottom-left [256..512, 0..256]: Brushed titanium-steel hard knuckle armor plate
    u = np.linspace(0.0, 1.0, 256, dtype=np.float32)[None, :]
    plate = 154.0 + 44.0 * np.sin(u * math.pi) + 12.0 * nf[256:, :256]
    arr[256:, :256, 0] = np.clip(plate * 0.96, 38, 242)
    arr[256:, :256, 1] = np.clip(plate * 1.00, 40, 246)
    arr[256:, :256, 2] = np.clip(plate * 1.03, 42, 252)

    # Bottom-right [256..512, 256..512]: Heavy armored olive-gunmetal & steel forearm gauntlet
    v = np.linspace(0.0, 1.0, 256, dtype=np.float32)[:, None]
    bracer = 88.0 + 34.0 * np.cos(u * 2.0 * math.pi) + 12.0 * np.sin(v * 24.0) + 10.0 * nf[256:, 256:]
    arr[256:, 256:, 0] = np.clip(bracer * 0.92, 24, 195)
    arr[256:, 256:, 1] = np.clip(bracer * 1.02, 28, 208)
    arr[256:, 256:, 2] = np.clip(bracer * 0.88, 22, 188)

    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    d = ImageDraw.Draw(im)
    # Yellow-gold military chevron rank stripe & titanium rivets on forearm gauntlet!
    d.rectangle((272, 286, 496, 300), fill=(208, 168, 42))
    for rx in (48, 108, 168, 224):
        _draw_rivet(d, rx, 320, 9)
        _draw_rivet(d, rx, 448, 9)
    for rx in (300, 364, 428, 480):
        _draw_rivet(d, rx, 330, 8)
        _draw_rivet(d, rx, 462, 8)
    path = os.path.join(out_dir, "wew_hand.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_core_and_projectile_texture(out_dir):
    """512x512 self-illuminated gauge + plasma core + colossal glowing silver-plasma WEW projectile."""
    W = H = 512
    im = Image.new("RGB", (W, H), (14, 20, 30))
    d = ImageDraw.Draw(im)
    nf = _fbm(H, W, seed=404, octaves=(4, 8, 16, 32))

    # --- Q1 [0..256, 0..256]: Breech Overcharge Dial ("WEW-METER") ---
    cx, cy = 128, 128
    d.ellipse((cx - 116, cy - 116, cx + 116, cy + 116), fill=(12, 18, 28), outline=(190, 210, 236), width=8)
    d.ellipse((cx - 102, cy - 102, cx + 102, cy + 102), outline=(45, 190, 255), width=3)
    for k in range(19):
        ang = math.radians(225.0 - k * (270.0 / 18.0))
        r0 = 76 if (k % 3 == 0) else 84
        r1 = 96
        col = (255, 75, 45) if k >= 14 else ((255, 210, 60) if k >= 10 else (70, 230, 255))
        x0, y0 = cx + r0 * math.cos(ang), cy - r0 * math.sin(ang)
        x1, y1 = cx + r1 * math.cos(ang), cy - r1 * math.sin(ang)
        d.line((x0, y0, x1, y1), fill=col, width=4 if k % 3 == 0 else 2)
    f_dial = _font(26)
    bb = d.textbbox((0, 0), "WEW", font=f_dial)
    d.text((cx - (bb[2] - bb[0]) // 2, cy + 32), "WEW", fill=(225, 245, 255), font=f_dial)
    f_sub = _font(18)
    bb2 = d.textbbox((0, 0), "MAX BLAST", font=f_sub)
    d.text((cx - (bb2[2] - bb2[0]) // 2, cy + 62), "MAX BLAST", fill=(255, 120, 60), font=f_sub)

    # --- Q2 [0..256, 256..512]: Incandescent Plasma Core & Barrel Vent Energy ---
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    rr = np.sqrt(((xx - 128.0) / 120.0) ** 2 + ((yy - 128.0) / 120.0) ** 2)
    ribs = 0.5 + 0.5 * np.cos(yy * 0.28)
    core = np.clip(1.15 - rr * 0.85 + 0.18 * ribs + 0.14 * nf[:256, 256:], 0.0, 1.2)
    q2 = np.zeros((256, 256, 3), dtype=np.uint8)
    q2[..., 0] = np.clip(core * 155.0 + np.maximum(0.0, core - 0.75) * 260.0, 0, 255).astype(np.uint8)
    q2[..., 1] = np.clip(core * 235.0, 0, 255).astype(np.uint8)
    q2[..., 2] = np.clip(core * 255.0, 0, 255).astype(np.uint8)
    im.paste(Image.fromarray(q2, mode="RGB"), (256, 0))

    # --- Bottom Half [256..512, 0..512]: Incandescent Concentric Accelerator Throat Coils ---
    py, px = np.mgrid[0:256, 0:512].astype(np.float32)
    dx_t = (px - 256.0) / 240.0
    dy_t = (py - 128.0) / 118.0
    rt = np.sqrt(dx_t * dx_t + dy_t * dy_t)
    coils = 0.5 + 0.5 * np.cos(rt * 22.0)
    glow_t = np.clip(1.18 - rt * 0.95 + 0.22 * coils + 0.10 * nf[256:, :], 0.0, 1.25)
    pr = glow_t * 110.0 + np.maximum(0.0, glow_t - 0.72) * 280.0
    pg = glow_t * 220.0
    pb = glow_t * 255.0
    throat_img = Image.fromarray(np.clip(np.stack([pr, pg, pb], axis=-1), 0, 255).astype(np.uint8), mode="RGB")
    im.paste(throat_img, (0, 256))

    path = os.path.join(out_dir, "wew_core.png")
    im.save(path, "PNG", optimize=True)
    return path


def build_fx_texture(out_dir):
    """512x512 RGBA additive FX atlas: Starburst Blast, Supersonic Shock-Ring, Arcs & Steam."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    nf = _fbm(H, W, seed=505, octaves=(4, 8, 16, 32))

    # --- Q1 [0..256, 0..256]: Blazing Fiery-Gold & Cyan Starburst Muzzle Flash ---
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    dx, dy = (xx - 128.0) / 128.0, (yy - 128.0) / 128.0
    r = np.sqrt(dx * dx + dy * dy) + 1e-6
    ang = np.arctan2(dy, dx)
    rays = 0.52 + 0.48 * np.cos(ang * 12.0 + 0.35 * nf[:256, :256])
    burst = np.clip(np.maximum(0.0, 1.0 - r / (0.58 + 0.40 * rays)) ** 1.35, 0.0, 1.0)
    core_hot = np.exp(-(r * r) / 0.12)
    a1 = np.clip(burst + core_hot, 0.0, 1.0)
    rgba[:256, :256, 0] = np.clip((1.00 * burst + 1.00 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 1] = np.clip((0.72 * burst + 0.98 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 2] = np.clip((0.35 * burst + 1.00 * core_hot) * 255.0, 0, 255)
    rgba[:256, :256, 3] = a1 * 255.0

    # --- Q2 [0..256, 256..512]: Concentric Supersonic Shockwave Ring ---
    ring = np.exp(-((r - 0.72) ** 2) / 0.011) * np.clip(1.0 - np.maximum(0.0, r - 0.94) * 16.0, 0.0, 1.0)
    inner_glow = 0.35 * np.exp(-((r - 0.48) ** 2) / 0.020)
    a2 = np.clip(ring + inner_glow, 0.0, 1.0)
    rgba[:256, 256:, 0] = np.clip(a2 * 215.0, 0, 255)
    rgba[:256, 256:, 1] = np.clip(a2 * 242.0, 0, 255)
    rgba[:256, 256:, 2] = np.clip(a2 * 255.0, 0, 255)
    rgba[:256, 256:, 3] = a2 * 255.0

    # --- Q3 [256..512, 0..256]: Jagged Plasma Charge Lightning ---
    ux = xx / 256.0
    uy = (yy - 128.0) / 128.0
    wiggle = 0.24 * np.sin(ux * 22.0) + 0.14 * nf[256:, :256]
    bolt = np.exp(-((uy - wiggle) ** 2) / 0.010) * np.sin(np.clip(ux, 0.0, 1.0) * math.pi)
    rgba[256:, :256, 0] = np.clip(bolt * 185.0, 0, 255)
    rgba[256:, :256, 1] = np.clip(bolt * 240.0, 0, 255)
    rgba[256:, :256, 2] = np.clip(bolt * 255.0, 0, 255)
    rgba[256:, :256, 3] = np.clip(bolt * 255.0, 0, 255)

    # --- Q4 [256..512, 256..512]: Pressurized Silver Steam Blowoff Plume ---
    cloud = np.clip((np.maximum(0.0, 1.0 - r) ** 1.3) * (0.68 + 0.32 * nf[256:, 256:]), 0.0, 1.0)
    rgba[256:, 256:, 0] = cloud * 215.0
    rgba[256:, 256:, 1] = cloud * 228.0
    rgba[256:, 256:, 2] = cloud * 245.0
    rgba[256:, 256:, 3] = cloud * 185.0

    path = os.path.join(out_dir, "wew_fx.png")
    Image.fromarray(rgba.astype(np.uint8), mode="RGBA").save(path, "PNG", optimize=True)
    return path


def _win98_box(d, x0, y0, x1, y1, fill=(192, 192, 192), sunken=False):
    d.rectangle((x0, y0, x1, y1), fill=fill)
    hi = (64, 64, 64) if sunken else (255, 255, 255)
    lo = (255, 255, 255) if sunken else (64, 64, 64)
    mid_hi = (128, 128, 128) if sunken else (223, 223, 223)
    mid_lo = (223, 223, 223) if sunken else (128, 128, 128)
    d.line((x0, y0, x1, y0), fill=hi, width=2)
    d.line((x0, y0, x0, y1), fill=hi, width=2)
    d.line((x0 + 2, y0 + 2, x1 - 2, y0 + 2), fill=mid_hi, width=1)
    d.line((x0 + 2, y0 + 2, x0 + 2, y1 - 2), fill=mid_hi, width=1)
    d.line((x0, y1, x1, y1), fill=lo, width=2)
    d.line((x1, y0, x1, y1), fill=lo, width=2)
    d.line((x0 + 2, y1 - 2, x1 - 2, y1 - 2), fill=mid_lo, width=1)
    d.line((x1 - 2, y0 + 2, x1 - 2, y1 - 2), fill=mid_lo, width=1)


def _draw_cursor(d, mx, my, clicking=False):
    """Draws a classic big bold Windows 98 white pixel arrow cursor (with optional click burst!)."""
    if clicking:
        for ang in range(0, 360, 45):
            r = math.radians(ang)
            d.line((mx + 4 * math.cos(r), my + 4 * math.sin(r),
                    mx + 14 * math.cos(r), my + 14 * math.sin(r)), fill=(255, 240, 60), width=3)
    pts = [
        (mx, my),
        (mx, my + 32),
        (mx + 8, my + 24),
        (mx + 14, my + 37),
        (mx + 20, my + 34),
        (mx + 14, my + 21),
        (mx + 24, my + 21),
    ]
    d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0))
    d.line(pts + [pts[0]], fill=(0, 0, 0), width=2)


def build_win98_crt_textures(stage_tex_dir, progs_dir):
    """Synthesizes 16 animated 512x512 Windows 98 Desktop + Internet Explorer 4 CRT screens
    browsing `goodwebsites.html`, `zxc.cc`, `biblefirst.com`, and `wxcs.com/rob`!"""
    W = H = 512
    f_icon  = _font(14, ("tahomabd.ttf", "arialbd.ttf"))
    f_title = _font(18, ("tahomabd.ttf", "arialbd.ttf"))
    f_addr  = _font(23, ("tahomabd.ttf", "arialbd.ttf"))
    f_h1    = _font(36, ("impact.ttf", "ariblk.ttf", "arialbd.ttf"))
    f_h2    = _font(25, ("tahomabd.ttf", "arialbd.ttf"))
    f_link  = _font(24, ("tahomabd.ttf", "arialbd.ttf"))
    f_body  = _font(19, ("tahomabd.ttf", "arialbd.ttf"))

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    scanline = 0.92 + 0.08 * np.cos(yy * math.pi)
    rx_c = (xx - 256.0) / 256.0
    ry_c = (yy - 256.0) / 256.0
    vignette = np.clip(1.04 - 0.18 * (rx_c * rx_c + ry_c * ry_c) ** 1.4, 0.72, 1.04)
    crt_mask = (scanline * vignette)[:, :, None]

    stage_frames = []
    for fi in range(16):
        site_idx = fi // 4      # 0: goodwebsites.html, 1: zxc.cc, 2: biblefirst.com, 3: wxcs.com/rob
        sub      = fi % 4       # 0..3 cursor / animation beat on that site

        # 1. Iconic Windows 98 `#008080` Teal Desktop Background!
        im = Image.new("RGB", (W, H), (0, 128, 128))
        d = ImageDraw.Draw(im)

        # Left-hand Windows 98 Desktop Icons (`My Computer`, `Recycle Bin`, `Quake`, `goodwebsites`)
        icons = [
            (14, 18,  (210, 220, 235), (40, 110, 210), "My PC"),
            (14, 106, (215, 215, 215), (70, 175, 90),  "Recycle"),
            (14, 194, (145, 95, 45),   (235, 180, 50), "Quake"),
            (14, 282, (255, 255, 220), (30, 90, 220),  "Sites"),
        ]
        for ix, iy, c_outer, c_inner, lbl in icons:
            _win98_box(d, ix + 8, iy, ix + 46, iy + 34, fill=c_outer)
            d.rectangle((ix + 14, iy + 6, ix + 40, iy + 24), fill=c_inner)
            bb = d.textbbox((0, 0), lbl, font=f_icon)
            lx = ix + 27 - (bb[2] - bb[0]) // 2
            d.text((lx + 1, iy + 39), lbl, fill=(0, 0, 0), font=f_icon)
            d.text((lx, iy + 38), lbl, fill=(255, 255, 255), font=f_icon)

        # 2. Classic Windows 98 Gray Taskbar at Bottom (`y = 466..511`)
        _win98_box(d, 0, 466, W - 1, H - 1, fill=(192, 192, 192))
        # `[Start]` button with 4-color Windows 98 pixel flag!
        _win98_box(d, 6, 472, 102, 506, fill=(192, 192, 192))
        d.rectangle((14, 480, 22, 488), fill=(235, 50, 35))
        d.rectangle((24, 480, 32, 488), fill=(45, 190, 55))
        d.rectangle((14, 490, 22, 498), fill=(35, 95, 235))
        d.rectangle((24, 490, 32, 498), fill=(245, 210, 30))
        d.text((38, 479), "Start", fill=(0, 0, 0), font=f_title)

        site_titles = ["goodwebsites.html", "zxc.cc", "biblefirst.com", "wxcs.com/rob"]
        _win98_box(d, 110, 472, 382, 506, fill=(214, 214, 214), sunken=True)
        d.ellipse((118, 480, 136, 498), fill=(25, 115, 235), outline=(255, 255, 255))
        d.text((142, 479), site_titles[site_idx], fill=(0, 0, 128), font=f_title)

        # System tray clock (`4:20 PM`)
        _win98_box(d, 390, 472, 505, 506, fill=(192, 192, 192), sunken=True)
        d.text((404, 480), f"4:2{site_idx} PM", fill=(0, 0, 0), font=f_title)

        # 3. Internet Explorer 4.0 Browser Window (`x = 76..504, y = 10..458`)
        wx0, wy0, wx1, wy1 = 76, 10, 504, 458
        _win98_box(d, wx0, wy0, wx1, wy1, fill=(192, 192, 192))

        # Navy-to-Royal-Blue Win98 Active Titlebar (`y = 16..48`)
        for gx in range(wx0 + 5, wx1 - 4):
            t_g = (gx - wx0) / max(1, (wx1 - wx0))
            col_g = (int(0 + 16 * t_g), int(0 + 132 * t_g), int(128 + 80 * t_g))
            d.line((gx, wy0 + 5, gx, wy0 + 36), fill=col_g)
        d.text((wx0 + 12, wy0 + 10), f"{site_titles[site_idx]} - Explorer", fill=(255, 255, 255), font=f_title)
        # `[ _ ][ □ ][ X ]` titlebar buttons
        for bi, sym in enumerate(("_", "□", "X")):
            bx0 = wx1 - 86 + bi * 27
            _win98_box(d, bx0, wy0 + 8, bx0 + 23, wy0 + 32, fill=(192, 192, 192))
            d.text((bx0 + 6, wy0 + 9), sym, fill=(0, 0, 0), font=f_icon)

        # Address Bar (`y = 44..88`) — EXTRA BOLD & HIGH CONTRAST so every URL pops in Quake POV!
        d.text((wx0 + 10, wy0 + 46), "URL:", fill=(0, 0, 0), font=f_title)
        _win98_box(d, wx0 + 58, wy0 + 41, wx1 - 10, wy0 + 79, fill=(255, 255, 255), sunken=True)
        urls = [
            "goodwebsites.html",
            "http://zxc.cc",
            "http://biblefirst.com",
            "http://wxcs.com/rob",
        ]
        d.text((wx0 + 68, wy0 + 46), urls[site_idx], fill=(0, 0, 0), font=f_addr)

        # Webpage Viewport (`vx0..vx1, vy0..vy1`) + Right Win98 Scrollbar
        vx0, vy0, vx1, vy1 = wx0 + 8, wy0 + 85, wx1 - 28, wy1 - 10
        _win98_box(d, vx0 - 2, vy0 - 2, wx1 - 8, vy1 + 2, fill=(255, 255, 255), sunken=True)
        # Win98 vertical scrollbar
        _win98_box(d, vx1 + 1, vy0, wx1 - 10, vy1, fill=(212, 212, 212))
        _win98_box(d, vx1 + 1, vy0, wx1 - 10, vy0 + 22, fill=(192, 192, 192))
        _win98_box(d, vx1 + 1, vy0 + 24 + sub * 18, wx1 - 10, vy0 + 88 + sub * 18, fill=(192, 192, 192))
        _win98_box(d, vx1 + 1, vy1 - 22, wx1 - 10, vy1, fill=(192, 192, 192))

        mx, my, click = 320, 260, False

        if site_idx == 0:
            # --- SITE 0: `goodwebsites.html` (Classic 1998 Local Bookmarks HTML Page!) ---
            d.rectangle((vx0, vy0, vx1, vy1), fill=(255, 255, 214))
            d.rectangle((vx0, vy0, vx1, vy0 + 54), fill=(180, 0, 40))
            d.text((vx0 + 14, vy0 + 7), "GOODWEBSITES.HTML", fill=(255, 255, 80), font=f_h1)
            d.line((vx0 + 10, vy0 + 62, vx1 - 10, vy0 + 62), fill=(128, 128, 128), width=3)

            links = [
                ("• zxc.cc",            "COOL!!"),
                ("• biblefirst.com",    "AMEN"),
                ("• wxcs.com/rob",      "ROB!!"),
                ("• goodwebsites.html", "HOME"),
            ]
            for li, (ltxt, badge_txt) in enumerate(links):
                ly = vy0 + 76 + li * 66
                is_act = (sub == 3 and li == 0)
                lcol = (255, 0, 0) if is_act else (0, 0, 238)
                d.text((vx0 + 16, ly), ltxt, fill=lcol, font=f_link)
                bb_l = d.textbbox((vx0 + 16, ly), ltxt, font=f_link)
                d.line((bb_l[0], bb_l[3] + 2, bb_l[2], bb_l[3] + 2), fill=lcol, width=3)
                # Little 1998 yellow/red `[NEW!]` tag
                d.rectangle((vx1 - 92, ly + 2, vx1 - 12, ly + 30), fill=(255, 230, 0), outline=(200, 0, 0), width=2)
                d.text((vx1 - 84, ly + 4), badge_txt, fill=(180, 0, 0), font=f_body)

            mx = 350 - sub * 52
            my = 290 - sub * 36
            click = (sub == 3)

        elif site_idx == 1:
            # --- SITE 1: `zxc.cc` (1998 Dark Cyber / Clan / Warez Portal!) ---
            d.rectangle((vx0, vy0, vx1, vy1), fill=(6, 10, 24))
            d.rectangle((vx0 + 8, vy0 + 8, vx1 - 8, vy1 - 8), outline=(0, 255, 90), width=3)
            d.rectangle((vx0 + 14, vy0 + 14, vx1 - 14, vy0 + 82), fill=(12, 32, 24), outline=(0, 230, 255), width=2)
            d.text((vx0 + 52, vy0 + 24), "[ Z X C . C C ]", fill=(50, 255, 110), font=f_h1)

            # Scrolling marquee bar
            d.rectangle((vx0 + 14, vy0 + 94, vx1 - 14, vy0 + 132), fill=(150, 0, 40))
            d.text((vx0 + 28 - sub * 4, vy0 + 100), ">> ZXC.CC #1 QUAKE HQ <<", fill=(255, 245, 60), font=f_body)

            for bi, btxt in enumerate(("[ FILES ]", "[ SCRIPTS ]", "[ SECRET ]")):
                by = vy0 + 148 + bi * 50
                hi_b = (sub >= 2 and bi == 2)
                d.rectangle((vx0 + 48, by, vx1 - 48, by + 40),
                            fill=(0, 110, 60) if hi_b else (16, 26, 48), outline=(0, 255, 120), width=2)
                d.text((vx0 + 104, by + 6), btxt, fill=(255, 255, 255) if hi_b else (80, 255, 220), font=f_h2)

            # Retro green odometer counter
            d.rectangle((vx0 + 78, vy1 - 46, vx1 - 78, vy1 - 14), fill=(0, 0, 0), outline=(140, 140, 140), width=2)
            d.text((vx0 + 92, vy1 - 42), f"HITS: 00042{sub}", fill=(0, 255, 70), font=f_body)
            mx = 220 + sub * 24
            my = 235 + sub * 32
            click = (sub == 3)

        elif site_idx == 2:
            # --- SITE 2: `biblefirst.com` (Wholesome 1998 Sky-Blue & Gold Church Page!) ---
            d.rectangle((vx0, vy0, vx1, vy1), fill=(214, 238, 255))
            d.rectangle((vx0, vy0, vx1, vy0 + 66), fill=(22, 68, 156))
            # Shining gold cross on left
            d.rectangle((vx0 + 22, vy0 + 10, vx0 + 34, vy0 + 56), fill=(255, 215, 40))
            d.rectangle((vx0 + 10, vy0 + 22, vx0 + 46, vy0 + 34), fill=(255, 215, 40))
            d.text((vx0 + 58, vy0 + 12), "BIBLEFIRST.COM", fill=(255, 245, 160), font=f_h1)

            # Warm parchment scripture card
            d.rectangle((vx0 + 16, vy0 + 80, vx1 - 16, vy0 + 228), fill=(255, 250, 226), outline=(185, 145, 55), width=3)
            d.text((vx0 + 30, vy0 + 92), "VERSE OF THE DAY:", fill=(155, 30, 30), font=f_h2)
            d.text((vx0 + 28, vy0 + 132), "\"THOU SHALT NOT", fill=(20, 25, 60), font=f_h2)
            d.text((vx0 + 28, vy0 + 166), " CAMP QUAD\"", fill=(20, 25, 60), font=f_h2)
            d.text((vx0 + 165, vy0 + 196), "- Wew 3:16", fill=(110, 75, 25), font=f_body)

            # Big 3D Win98 `[ AMEN! ]` button + popup blessing on click!
            _win98_box(d, vx0 + 82, vy0 + 246, vx1 - 82, vy0 + 302, fill=(212, 208, 200), sunken=(sub >= 2))
            d.text((vx0 + 124, vy0 + 258), "[ AMEN!! ]", fill=(0, 0, 140), font=f_h2)
            if sub >= 2:
                _win98_box(d, vx0 + 56, vy0 + 308, vx1 - 56, vy1 - 10, fill=(255, 255, 190))
                d.text((vx0 + 78, vy0 + 314), "BLESSED! +100 HP", fill=(180, 20, 20), font=f_body)

            mx = 320 - sub * 18
            my = 325 + sub * 14
            click = (sub == 2)

        else:
            # --- SITE 3: `wxcs.com/rob` (Peak 1998 GeoCities "ROB'S HOMEPAGE" w/ Under Construction!) ---
            d.rectangle((vx0, vy0, vx1, vy1), fill=(22, 12, 68))
            # Yellow & black 1998 UNDER CONSTRUCTION hazard stripes clipped cleanly inside viewport!
            d.rectangle((vx0, vy0, vx1, vy0 + 22), fill=(20, 20, 20))
            d.rectangle((vx0, vy1 - 22, vx1, vy1), fill=(20, 20, 20))
            for sx in range(vx0 + 6, vx1 - 16, 28):
                d.polygon([(sx, vy0), (sx + 14, vy0), (sx + 6, vy0 + 22), (sx - 8, vy0 + 22)], fill=(255, 215, 0))
                d.polygon([(sx, vy1 - 22), (sx + 14, vy1 - 22), (sx + 6, vy1), (sx - 8, vy1)], fill=(255, 215, 0))

            d.text((vx0 + 22, vy0 + 30), "WXCS.COM/ROB", fill=(80, 255, 255), font=f_h1)
            d.text((vx0 + 24, vy0 + 76), "ROB'S COOL PAGE!!", fill=(255, 110, 240), font=f_h2)

            # Cheerful cartoon Rob avatar box w/ cool 90s shades!
            ax0, ay0 = vx0 + 22, vy0 + 116
            d.rectangle((ax0, ay0, ax0 + 116, ay0 + 124), fill=(40, 140, 210), outline=(255, 255, 255), width=3)
            d.ellipse((ax0 + 18, ay0 + 14, ax0 + 98, ay0 + 102), fill=(245, 200, 160), outline=(0, 0, 0), width=2)
            # Cool sunglasses
            d.rectangle((ax0 + 26, ay0 + 38, ax0 + 54, ay0 + 54), fill=(10, 10, 15))
            d.rectangle((ax0 + 62, ay0 + 38, ax0 + 90, ay0 + 54), fill=(10, 10, 15))
            d.line((ax0 + 22, ay0 + 42, ax0 + 94, ay0 + 42), fill=(10, 10, 15), width=4)
            # Big grin
            d.arc((ax0 + 34, ay0 + 56, ax0 + 82, ay0 + 88), 10, 170, fill=(160, 20, 20), width=4)
            d.text((ax0 + 34, ay0 + 102), "ROB", fill=(255, 255, 90), font=f_body)

            # Right column GeoCities blurbs & Guestbook
            d.text((ax0 + 132, ay0 + 6),  "• QUAKE GOD", fill=(120, 255, 120), font=f_body)
            d.text((ax0 + 132, ay0 + 38), "• ROB DOB FAN", fill=(255, 240, 90), font=f_body)
            d.text((ax0 + 132, ay0 + 70), "• ICQ #42069", fill=(120, 225, 255), font=f_body)
            _win98_box(d, ax0 + 130, ay0 + 100, vx1 - 14, ay0 + 138, fill=(192, 192, 192))
            d.text((ax0 + 142, ay0 + 108), "GUESTBOOK", fill=(0, 0, 128), font=f_body)

            d.text((vx0 + 36, vy1 - 58), "UNDER CONSTRUCTION", fill=(255, 230, 40), font=f_h2)
            mx = 290 + sub * 20
            my = 310 + sub * 10
            click = (sub == 3)

        # Draw big crisp Windows 98 mouse cursor on top!
        _draw_cursor(d, mx, my, clicking=click)

        # Apply subtle CRT phosphor scanlines & glass vignette
        arr_f = np.clip(np.asarray(im, dtype=np.float32) * crt_mask, 0, 255)
        st_im = Image.fromarray(arr_f.astype(np.uint8), mode="RGB")
        st_path = os.path.join(stage_tex_dir, f"wew_crt_{fi:02d}.png")
        st_im.save(st_path, "PNG", optimize=True)
        stage_frames.append(st_path)

        # Deploy DarkPlaces-calibrated CRT frame (`progs/wew_crt_00.png` .. `wew_crt_15.png`)
        dp_im = Image.fromarray(np.clip(arr_f * 0.78, 0, 255).astype(np.uint8), mode="RGB")
        dp_im.save(os.path.join(progs_dir, f"wew_crt_{fi:02d}.png"), "PNG", optimize=True)

    # Also save static `wew_crt_screen.png` (Win98 desktop + `goodwebsites.html` showing all 4 URLs!)
    im0 = Image.open(stage_frames[0]).convert("RGB")
    static_stage = os.path.join(stage_tex_dir, "wew_crt_screen.png")
    im0.save(static_stage, "PNG", optimize=True)
    im0_dp = Image.fromarray(np.clip(np.asarray(im0, dtype=np.float32) * 0.78, 0, 255).astype(np.uint8), mode="RGB")
    im0_dp.save(os.path.join(progs_dir, "wew_crt_screen.png"), "PNG", optimize=True)
    return static_stage, stage_frames


def build_all_textures(stage_tex_dir, progs_dir):
    os.makedirs(stage_tex_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    crt_static, crt_frames = build_win98_crt_textures(stage_tex_dir, progs_dir)
    paths = {
        "silver":     build_silver_texture(stage_tex_dir),
        "hand":       build_hand_texture(stage_tex_dir),
        "core":       build_core_and_projectile_texture(stage_tex_dir),
        "fx":         build_fx_texture(stage_tex_dir),
        "crt":        crt_static,
        "crt_frames": crt_frames,
    }
    # Paste crisp Win98 CRT screen (`goodwebsites.html` w/ all 4 URLs) into Q1 of `wew_core.png` so `.mdl` single-skin atlas shows it too!
    core_im = Image.open(paths["core"]).convert("RGB")
    core_im.paste(Image.open(crt_static).convert("RGB").resize((256, 256), Image.LANCZOS), (0, 0))
    core_im.save(paths["core"], "PNG", optimize=True)

    # Deploy DarkPlaces-calibrated textures into progs/ (matching BakersfieldQuake gamma/HDR so silver gleams without whiteout!)
    for key, gain in (("silver", 0.56), ("hand", 0.50), ("core", 0.68)):
        arr = np.asarray(Image.open(paths[key]).convert("RGB"), dtype=np.float32)
        Image.fromarray(np.clip(arr * gain, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(progs_dir, f"wew_{key}.png"), "PNG", optimize=True
        )

    fx_rgba = np.asarray(Image.open(paths["fx"]).convert("RGBA"), dtype=np.float32)
    fx_premul = fx_rgba[..., :3] * (fx_rgba[..., 3:4] / 255.0) * 0.78
    Image.fromarray(np.clip(fx_premul, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(progs_dir, "wew_fx.png"), "PNG", optimize=True
    )

    # Also build unified 2:1 classic Quake MDL single-skin atlas (1024x512 hires for _0.tga, 512x256 for embedded IDPO v6 skin!)
    # Atlas Quadrant Layout (W=2*H, strictly height=256 <= MAX_LBM_HEIGHT=480!):
    #   [u: 0.0..0.5, v: 0.0..1.0] -> wew_silver (512x256 / 512x512)
    #   [u: 0.5..0.75, v: 0.0..0.5] -> wew_hand
    #   [u: 0.75..1.0, v: 0.0..0.5] -> wew_core (fullbright-eligible!)
    #   [u: 0.5..1.0, v: 0.5..1.0]  -> wew_fx premultiplied on black/glow
    atlas_hi = Image.new("RGB", (1024, 512), (16, 20, 28))
    atlas_hi.paste(Image.open(paths["silver"]).convert("RGB").resize((512, 512), Image.LANCZOS), (0, 0))
    atlas_hi.paste(Image.open(paths["hand"]).convert("RGB").resize((256, 256), Image.LANCZOS), (512, 0))
    atlas_hi.paste(Image.open(paths["core"]).convert("RGB").resize((256, 256), Image.LANCZOS), (768, 0))
    fx_rgb_hi = Image.fromarray(np.clip(fx_rgba[..., :3] * (fx_rgba[..., 3:4] / 255.0), 0, 255).astype(np.uint8), mode="RGB")
    atlas_hi.paste(fx_rgb_hi.resize((512, 256), Image.LANCZOS), (512, 256))

    paths["mdl_atlas_hi"] = os.path.join(stage_tex_dir, "wew_mdl_atlas_1024x512.png")
    atlas_hi.save(paths["mdl_atlas_hi"], "PNG", optimize=True)

    atlas_lo = atlas_hi.resize((512, 256), Image.LANCZOS)
    paths["mdl_atlas_lo"] = os.path.join(stage_tex_dir, "wew_mdl_atlas_512x256.png")
    atlas_lo.save(paths["mdl_atlas_lo"], "PNG", optimize=True)

    return paths
