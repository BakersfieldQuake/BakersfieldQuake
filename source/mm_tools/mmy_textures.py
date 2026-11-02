"""Procedural texture & Quake shader generator for the 3-Version Mega Man Yeet Weapon Voting Studio:
  - progs/mmy_rig_steel.png (1024x1024: hot-rolled square steel tubing, mottled welded steel drum pan,
                             MIG weld seams, zinc hex nuts, black-oxide leveling bolts, 6-spoked gray steel
                             bull gear, bright white Delrin/nylon pinion gear, engraved steel ruler scale
                             with funny range markings, OSHA 'DANGER: MEGA-YEET' decal, hollow tube cavity)
  - progs/mmy_fx.png        (512x512 RGBA: supersonic Mach shockwave ring, centrifugal spark streaks,
                             railgun plasma arc, and tire-burnout smoke puff)
  - scripts/mm_yeet_gun.shader
"""
import math
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Shared UV Rects in mmy_rig_steel.png (u0, v0, u1, v1)
UV_SQ_TUBE     = (0.02, 0.02, 0.48, 0.30)
UV_DRUM_PAN    = (0.52, 0.02, 0.98, 0.30)
UV_WELD_BEAD   = (0.02, 0.33, 0.24, 0.55)
UV_HEX_ZINC    = (0.27, 0.33, 0.48, 0.43)
UV_BLACK_BOLT  = (0.27, 0.46, 0.48, 0.55)
UV_BULL_GEAR   = (0.52, 0.33, 0.74, 0.55)
UV_NYLON_WHITE = (0.77, 0.33, 0.98, 0.55)
UV_RULED_SCALE = (0.02, 0.59, 0.62, 0.79)
UV_OSHA_DECAL  = (0.66, 0.59, 0.98, 0.79)
UV_GRIP_CABLE  = (0.02, 0.82, 0.32, 0.98)
UV_RED_LEVER   = (0.35, 0.82, 0.54, 0.98)
UV_HOLLOW_DARK = (0.57, 0.82, 0.76, 0.98)
UV_BRASS_PIN   = (0.79, 0.82, 0.98, 0.98)

# Shared UV Rects in mmy_fx.png (u0, v0, u1, v1)
UV_FX_SHOCK = (0.02, 0.02, 0.48, 0.48)
UV_FX_SWIRL = (0.52, 0.02, 0.98, 0.48)
UV_FX_BOLT  = (0.02, 0.52, 0.48, 0.98)
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


def build_rig_steel_texture(out_path):
    W = H = 1024
    arr = np.full((H, W, 3), 48.0, dtype=np.float32)
    n_coarse = _fbm(H, W, seed=401, octaves=(4, 8, 16, 32))
    n_fine   = _fbm(H, W, seed=402, octaves=(2, 4, 8))

    # 1. [0..320, 0..512] Raw Hot-Rolled Mill-Scale Square-Tube Steel
    y1, x1 = np.mgrid[0:320, 0:512].astype(np.float32)
    mill = 98.0 + 18.0 * n_coarse[:320, :512] + 8.0 * n_fine[:320, :512]
    # Directional brushed / grinder scratches along tube length (x) + bright ground bevels near edges
    brush = 6.5 * np.sin(y1 * 0.85 + 2.5 * n_coarse[:320, :512])
    edge_hi = 34.0 * (np.exp(-((y1 - 18.0) ** 2) / 90.0) + np.exp(-((y1 - 302.0) ** 2) / 90.0))
    # Subtle warm/cool mill-scale variación matching reference photo
    arr[:320, :512, 0] = np.clip(mill * 0.99 + brush + edge_hi, 30, 225)
    arr[:320, :512, 1] = np.clip(mill * 0.98 + brush + edge_hi, 30, 225)
    arr[:320, :512, 2] = np.clip(mill * 1.01 + brush + edge_hi * 1.04, 32, 232)

    # 2. [0..320, 512..1024] Heavy Circular Steel Drum Pan (warm dark oxidized shop steel)
    yd, xd = np.mgrid[0:320, 0:512].astype(np.float32)
    rx = (xd - 255.5) / 248.0
    ry = (yd - 159.5) / 152.0
    rr = np.sqrt(rx * rx + ry * ry)
    drum = 86.0 + 21.0 * n_coarse[:320, 512:] + 9.0 * n_fine[:320, 512:]
    # Welded perimeter rim highlight & dark oil stain rings
    drum += 26.0 * np.exp(-((rr - 0.90) ** 2) / 0.004)
    drum -= 16.0 * np.exp(-((rr - 0.45) ** 2) / 0.03)
    rust = np.clip(n_coarse[:320, 512:], -0.5, 1.2)
    arr[:320, 512:, 0] = np.clip(drum * 1.04 + 10.0 * rust, 26, 205)
    arr[:320, 512:, 1] = np.clip(drum * 0.96 + 4.0 * rust, 24, 195)
    arr[:320, 512:, 2] = np.clip(drum * 0.91 - 3.0 * rust, 22, 188)

    # 3. [320..576, 0..256] Stacked-Dime MIG Weld Bead + Rainbow Heat-Affected Zone
    yw, xw = np.mgrid[0:256, 0:256].astype(np.float32)
    vw = yw / 255.0
    uw = xw / 255.0
    dimes = 0.5 + 0.5 * np.cos(uw * 2.0 * math.pi * 14.0 + 1.4 * np.sin(vw * math.pi))
    bead_mask = np.exp(-((vw - 0.5) ** 2) / 0.035)
    straw = np.exp(-((np.abs(vw - 0.5) - 0.19) ** 2) / 0.004)
    violet = np.exp(-((np.abs(vw - 0.5) - 0.27) ** 2) / 0.004)
    wb = 108.0 + 58.0 * dimes * bead_mask + 10.0 * n_fine[320:576, :256]
    arr[320:576, :256, 0] = np.clip(wb + 42.0 * straw - 12.0 * violet, 28, 245)
    arr[320:576, :256, 1] = np.clip(wb + 18.0 * straw - 18.0 * violet, 28, 235)
    arr[320:576, :256, 2] = np.clip(wb - 24.0 * straw + 38.0 * violet, 28, 245)

    # 4. [320..448, 256..512] Bright Zinc Hex Nut & Coarse Machined Bolt Threads
    yz, xz = np.mgrid[0:128, 0:256].astype(np.float32)
    threads = 18.0 * np.sin(xz * 0.55)
    zinc = 196.0 + threads + 10.0 * n_fine[320:448, 256:512] + 22.0 * np.cos(yz / 128.0 * math.pi * 2.0)
    arr[320:448, 256:512, 0] = np.clip(zinc * 0.97, 60, 250)
    arr[320:448, 256:512, 1] = np.clip(zinc * 0.99, 60, 252)
    arr[320:448, 256:512, 2] = np.clip(zinc * 1.04, 65, 255)

    # 5. [448..576, 256..512] Dark Black-Oxide Leveling Bolt
    yb, xb = np.mgrid[0:128, 0:256].astype(np.float32)
    blk = 44.0 + 9.0 * np.sin(xb * 0.65) + 6.0 * n_fine[448:576, 256:512]
    arr[448:576, 256:512, 0] = np.clip(blk * 1.00, 16, 95)
    arr[448:576, 256:512, 1] = np.clip(blk * 1.01, 16, 96)
    arr[448:576, 256:512, 2] = np.clip(blk * 1.06, 18, 102)

    # 6. [320..576, 512..768] Machined Matte-Gray Steel Spoked Bull Gear & Aluminum Motor
    yg, xg = np.mgrid[0:256, 0:256].astype(np.float32)
    gx = (xg - 127.5) / 124.0
    gy = (yg - 127.5) / 124.0
    gr = np.sqrt(gx * gx + gy * gy)
    ga = np.arctan2(gy, gx)
    lathe = 138.0 + 18.0 * np.cos(2.0 * ga - 0.7) + 7.0 * np.sin(gr * 95.0) + 7.0 * n_fine[320:576, 512:768]
    # Darkened gear tooth oil ring near outer perimeter
    lathe -= 26.0 * np.exp(-((gr - 0.94) ** 2) / 0.006)
    arr[320:576, 512:768, 0] = np.clip(lathe * 0.97, 38, 228)
    arr[320:576, 512:768, 1] = np.clip(lathe * 1.00, 40, 232)
    arr[320:576, 512:768, 2] = np.clip(lathe * 1.04, 42, 238)

    # 7. [320..576, 768..1024] Crisp Bright-White Delrin / Nylon Spur Pinion Gear (#f2f4f8)
    yn, xn = np.mgrid[0:256, 0:256].astype(np.float32)
    nx = (xn - 127.5) / 124.0
    ny = (yn - 127.5) / 124.0
    nr = np.sqrt(nx * nx + ny * ny)
    nylon = 238.0 - 14.0 * np.exp(-((nr - 0.55) ** 2) / 0.04) + 5.0 * n_fine[320:576, 768:1024]
    arr[320:576, 768:1024, 0] = np.clip(nylon * 0.99, 175, 253)
    arr[320:576, 768:1024, 1] = np.clip(nylon * 1.00, 178, 254)
    arr[320:576, 768:1024, 2] = np.clip(nylon * 1.01, 182, 255)

    # 8. [576..816, 0..640] Brushed Stainless Spine Bar with Recessed Engraved Ruler Scale
    ys, xs = np.mgrid[0:240, 0:640].astype(np.float32)
    bar = 166.0 + 14.0 * np.sin(xs * 0.04) + 8.0 * np.sin(ys * 0.5) + 8.0 * n_fine[576:816, :640]
    # Recessed satin-bright ruler strip down middle (ys in 58..182)
    in_strip = ((ys >= 56) & (ys <= 184)).astype(np.float32)
    strip_bevel = np.exp(-((ys - 56) ** 2) / 14.0) + np.exp(-((ys - 184) ** 2) / 14.0)
    bar = bar * (1.0 - 0.25 * in_strip) + 206.0 * 0.25 * in_strip - 38.0 * strip_bevel
    arr[576:816, :640, 0] = np.clip(bar * 0.98, 40, 245)
    arr[576:816, :640, 1] = np.clip(bar * 1.00, 42, 248)
    arr[576:816, :640, 2] = np.clip(bar * 1.03, 45, 252)

    # 9. [576..816, 640..1024] Distressed Safety-Yellow & Black OSHA Hazard Plate
    yh, xh = np.mgrid[0:240, 0:384].astype(np.float32)
    # Hazard chevron border at top & bottom 36px
    stripe = (((xh + yh) // 22) % 2 == 0).astype(np.float32)
    border = ((yh < 34) | (yh > 206)).astype(np.float32)
    yel_r = 238.0 - 18.0 * np.abs(n_coarse[576:816, 640:])
    yel_g = 178.0 - 16.0 * np.abs(n_coarse[576:816, 640:])
    yel_b = 34.0 + 8.0 * np.abs(n_fine[576:816, 640:])
    haz_m = border * (1.0 - stripe)  # 1 where black chevron stripe on border
    arr[576:816, 640:, 0] = np.clip(yel_r * (1.0 - 0.86 * haz_m), 18, 250)
    arr[576:816, 640:, 1] = np.clip(yel_g * (1.0 - 0.86 * haz_m), 18, 210)
    arr[576:816, 640:, 2] = np.clip(yel_b * (1.0 - 0.50 * haz_m), 16, 70)

    # 10. [816..1024, 0..340] Knurled Dark Grip & Twisted Braided Steel Cable
    yk, xk = np.mgrid[0:208, 0:340].astype(np.float32)
    knurl = 0.5 + 0.5 * np.sin((xk + yk) * 0.48) * np.sin((xk - yk) * 0.48)
    kc = 52.0 + 38.0 * knurl + 6.0 * n_fine[816:, :340]
    arr[816:, :340, 0] = np.clip(kc * 0.98, 18, 145)
    arr[816:, :340, 1] = np.clip(kc * 1.00, 18, 148)
    arr[816:, :340, 2] = np.clip(kc * 1.05, 20, 156)

    # 11. [816..1024, 340..560] Shop-Red Plastidip Trigger / Lever Handle
    red_base = 188.0 + 18.0 * n_fine[816:, 340:560]
    arr[816:, 340:560, 0] = np.clip(red_base, 90, 238)
    arr[816:, 340:560, 1] = np.clip(red_base * 0.22, 18, 62)
    arr[816:, 340:560, 2] = np.clip(red_base * 0.19, 16, 56)

    # 12. [816..1024, 560..780] Deep Sooty Matte-Black Hollow Tube Cavity
    cav = 16.0 + 3.0 * n_fine[816:, 560:780]
    arr[816:, 560:780, 0] = np.clip(cav, 8, 28)
    arr[816:, 560:780, 1] = np.clip(cav + 1.0, 9, 30)
    arr[816:, 560:780, 2] = np.clip(cav + 3.0, 10, 34)

    # 13. [816..1024, 780..1024] Burnished Brass / Stainless Plunger & Clevis Hardware
    yb2, xb2 = np.mgrid[0:208, 0:244].astype(np.float32)
    brs = 196.0 + 24.0 * np.cos(xb2 / 244.0 * math.pi * 2.0) + 9.0 * np.sin(yb2 * 0.5) + 7.0 * n_fine[816:, 780:]
    arr[816:, 780:, 0] = np.clip(brs * 1.06, 70, 252)
    arr[816:, 780:, 1] = np.clip(brs * 0.90, 60, 225)
    arr[816:, 780:, 2] = np.clip(brs * 0.48, 30, 138)

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # --- Crisp Engraved Ruler Ticks, Countersunk Bolt Holes & Funny Range Callouts on Region 8 [576..816, 0..640] ---
    y_mid = 576 + 120
    dr.line([(22, y_mid), (618, y_mid)], fill=(54, 58, 66), width=2)
    for tx in range(28, 616, 8):
        major = ((tx - 28) % 40 == 0)
        med = ((tx - 28) % 20 == 0)
        th = 24 if major else (14 if med else 7)
        w_tk = 2 if major else 1
        dr.line([(tx, y_mid - th), (tx, y_mid + th)], fill=(42, 46, 54), width=w_tk)

    # Two dark countersunk bolt holes matching reference photo!
    for hx in (185, 435):
        hy = 576 + 34
        dr.ellipse([hx - 13, hy - 13, hx + 13, hy + 13], fill=(22, 24, 28), outline=(92, 98, 108), width=3)

    f_scale = _font(17, bold=True)
    callouts = [
        (30,  "10m"),
        (106, "80m"),
        (192, "BAKERSFIELD"),
        (354, "FRESNO"),
        (456, "ORBIT"),
        (536, "BYE!!"),
    ]
    for cx, txt in callouts:
        col = (178, 28, 24) if txt in ("ORBIT", "BYE!!") else (36, 40, 48)
        dr.text((cx, y_mid + 27), txt, fill=col, font=f_scale)

    # --- Funny OSHA Shop Stencil on Region 9 [576..816, 640..1024] ---
    f_big = _font(28, bold=True)
    f_med = _font(18, bold=True)
    f_sm  = _font(15, bold=True)
    dr.rectangle([658, 618, 1006, 658], fill=(22, 22, 24))
    dr.text((674, 623), "DANGER: MEGA-YEET", fill=(246, 188, 38), font=f_big)
    dr.text((666, 668), "SHOOTS CHROME BOI", fill=(22, 22, 24), font=f_med)
    dr.text((666, 692), "STUPIDLY FAR AWAY", fill=(168, 24, 18), font=f_med)
    dr.text((666, 720), "KEEP THUMBS & DIGNITY CLEAR", fill=(28, 28, 30), font=f_sm)
    dr.text((666, 742), "BAKERSFIELD ORDNANCE CO.", fill=(48, 48, 52), font=f_sm)

    # Soapstone chalk mark on Drum Pan [0..320, 512..1024]
    f_chalk = _font(20, bold=True)
    dr.text((548, 36), "YEET-RIG #04 // DO NOT OSHA", fill=(186, 184, 176), font=f_chalk)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_fx_texture(out_path):
    """512x512 RGBA additive FX texture for supersonic shockwave rings, centrifugal sparks, arcs & burnout smoke."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    nx = (xx - 127.5) / 120.0
    ny = (yy - 127.5) / 120.0
    rr = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)

    # Q1 [0..256, 0..256]: Supersonic Mach Shockwave Ring (Amber-Gold Core + Cyan Rim)
    ring1 = np.exp(-((rr - 0.72) ** 2) / 0.012) * (0.78 + 0.22 * np.cos(ang * 10.0))
    ring2 = np.exp(-((rr - 0.44) ** 2) / 0.020)
    core  = np.exp(-(rr * rr) / 0.08) * 0.65
    a1 = np.clip((ring1 + ring2 * 0.8 + core) * (rr < 0.98), 0.0, 1.0)
    rgba[:256, :256, 0] = np.clip((ring2 * 1.0 + core * 1.0 + ring1 * 0.45) * 255.0, 0, 255)
    rgba[:256, :256, 1] = np.clip((ring2 * 0.72 + core * 0.88 + ring1 * 0.88) * 255.0, 0, 255)
    rgba[:256, :256, 2] = np.clip((ring2 * 0.20 + core * 0.55 + ring1 * 1.00) * 255.0, 0, 255)
    rgba[:256, :256, 3] = a1 * 255.0

    # Q2 [0..256, 256..512]: Centrifugal / Flywheel Grinding Spark Swirl
    swirl = np.exp(-((rr - 0.76) ** 2) / 0.016) * np.clip(np.sin(ang * 6.0 + rr * 8.0), 0.0, 1.0)
    sparks = np.exp(-((rr - 0.62) ** 2) / 0.03) * (np.sin(ang * 22.0) > 0.72).astype(np.float32)
    a2 = np.clip((swirl * 0.9 + sparks) * (rr < 0.98), 0.0, 1.0)
    rgba[:256, 256:, 0] = 255.0 * np.clip(a2 * 1.2, 0, 1)
    rgba[:256, 256:, 1] = 255.0 * np.clip(swirl * 0.70 + sparks * 0.92, 0, 1)
    rgba[:256, 256:, 2] = 255.0 * np.clip(swirl * 0.22 + sparks * 0.55, 0, 1)
    rgba[:256, 256:, 3] = a2 * 255.0

    # Q3 [256..512, 0..256]: Electric Railgun / Induction Lightning Arc
    u_arc = xx / 255.0
    v_arc = (yy - 127.5) / 120.0
    jag1 = 0.22 * np.sin(u_arc * 19.0) + 0.11 * np.sin(u_arc * 47.0 + 1.2)
    jag2 = -0.18 * np.sin(u_arc * 15.0 + 2.1) + 0.09 * np.cos(u_arc * 41.0)
    b1 = np.exp(-((v_arc - jag1) ** 2) / 0.0045)
    b2 = np.exp(-((v_arc - jag2) ** 2) / 0.0065) * 0.75
    fade_u = np.clip(np.sin(u_arc * math.pi), 0.0, 1.0) ** 0.55
    a3 = np.clip((b1 + b2) * fade_u, 0.0, 1.0)
    rgba[256:, :256, 0] = np.clip(a3 * 150.0 + (b1 ** 2) * 105.0, 0, 255)
    rgba[256:, :256, 1] = np.clip(a3 * 228.0 + (b1 ** 2) * 40.0, 0, 255)
    rgba[256:, :256, 2] = 255.0 * np.clip(a3 * 1.25, 0, 1)
    rgba[256:, :256, 3] = a3 * 255.0

    # Q4 [256..512, 256..512]: Tire-Burnout Smoke & Steam Plume
    n_sm = _fbm(256, 256, seed=909, octaves=(4, 8, 16))
    puff = np.exp(-(rr * rr) / 0.30) * np.clip(0.72 + 0.32 * n_sm, 0.0, 1.0) * (rr < 0.96)
    rgba[256:, 256:, 0] = 232.0 * puff
    rgba[256:, 256:, 1] = 224.0 * puff
    rgba[256:, 256:, 2] = 216.0 * puff
    rgba[256:, 256:, 3] = np.clip(puff * 0.85, 0.0, 1.0) * 255.0

    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", optimize=True)
    return out_path


def ensure_yeet_textures_and_shader(mod_dir, stage_dir):
    progs_dir = os.path.join(mod_dir, "progs")
    scripts_dir = os.path.join(mod_dir, "scripts")
    os.makedirs(progs_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(stage_dir, exist_ok=True)

    # 1. Build crisp full-brightness textures in stage_dir for the WebGL2 HTML Voting Studio
    import mmw_textures
    mmw_stage = mmw_textures.build_all_textures(stage_dir)

    stage_rig = os.path.join(stage_dir, "mmy_rig_steel.png")
    stage_fx  = os.path.join(stage_dir, "mmy_fx.png")
    build_rig_steel_texture(stage_rig)
    build_fx_texture(stage_fx)

    # 2. Ensure shared Mega Man textures exist in progs/ (preserve existing HDR-calibrated copies if present)
    for fn, src_key, dim in (
        ("mmw_chrome_axle.png", "chrome_axle", 0.42),
        ("mmw_wheel.png",       "wheel",       0.34),
        ("mmw_hand.png",        "hand",        0.45),
    ):
        dst = os.path.join(progs_dir, fn)
        if not os.path.isfile(dst):
            im = np.asarray(Image.open(mmw_stage[src_key]).convert("RGB")).astype(np.float32)
            Image.fromarray(np.clip(im * dim, 0, 255).astype(np.uint8)).save(dst, "PNG", optimize=True)

    # 3. Write DarkPlaces HDR-calibrated (r_hdr_scenebrightness 2.5) mmy_rig_steel.png & premultiplied mmy_fx.png to progs/
    rig_arr = np.asarray(Image.open(stage_rig).convert("RGB")).astype(np.float32)
    Image.fromarray(np.clip(rig_arr * 0.42, 0, 255).astype(np.uint8)).save(
        os.path.join(progs_dir, "mmy_rig_steel.png"), "PNG", optimize=True
    )

    fx_arr = np.asarray(Image.open(stage_fx).convert("RGBA")).astype(np.float32)
    fx_rgb = fx_arr[..., :3] * (fx_arr[..., 3:4] / 255.0) * 0.62
    Image.fromarray(np.clip(fx_rgb, 0, 255).astype(np.uint8)).save(
        os.path.join(progs_dir, "mmy_fx.png"), "PNG", optimize=True
    )

    shader_txt = """// written by mm_tools/build_megaman_yeet_vote.py

progs/mmy_rig_steel
{
\tcull none
\t{
\t\tmap progs/mmy_rig_steel
\t\trgbGen lightingDiffuse
\t}
}

progs/mmy_fx
{
\tcull none
\t{
\t\tmap progs/mmy_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    shader_p = os.path.join(scripts_dir, "mm_yeet_gun.shader")
    with open(shader_p, "w", encoding="ascii", newline="\n") as f:
        f.write(shader_txt)

    return {
        "rig_steel":   stage_rig,
        "chrome_axle": mmw_stage["chrome_axle"],
        "wheel":       mmw_stage["wheel"],
        "hand":        mmw_stage["hand"],
        "fx":          stage_fx,
    }
