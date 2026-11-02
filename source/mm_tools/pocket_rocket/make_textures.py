"""Generates all brand-new high-resolution textures from scratch for the
Pocket Rocket / Pink Lady Torpedo throwable weapon & projectile 3D models.

Zero existing project assets are read or reused. Every texture is synthesized
procedurally and artistically painted with NumPy + SciPy + Pillow:
  - tex_skin.png        (1024x1024) Face (joyful laughing grin, hazel eyes, lashes, brows, blush), neck, cleavage & hands
  - tex_hair.png        (1024x1024) Dark-rooted center-parted silky champagne/platinum blonde hair strands
  - tex_pink_top.png    (1024x1024) Vibrant hot-pink jersey knit cardigan with radial tie-knot pleats & sleeve seams
  - tex_jeans.png       (1024x1024) Indigo diagonal-twill skinny jeans (front fly/pockets + rear patch pockets & whiskers)
  - tex_sneakers.png    (512x512)   Hot-pink athletic sneakers (mesh, overlays, criss-cross laces, sculpted sole)
  - tex_giant_hand.png  (1024x1024) Giant 1st-person right hand skin (dorsal knuckles/pores, palmar life lines, fingernails)
  - tex_speedlines.png  (512x256)   RGBA aerodynamic white/iridescent slipstream streaks
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "out", "pocket_rocket", "textures")


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(edge0, edge1, x):
    t = clamp01((x - edge0) / (edge1 - edge0 + 1e-12))
    return t * t * (3.0 - 2.0 * t)


def fbm_noise(h, w, scales=(4, 8, 16, 32, 64), weights=(0.35, 0.28, 0.18, 0.12, 0.07), seed=42):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    for sc, wt in zip(scales, weights):
        gh = max(2, h // sc)
        gw = max(2, w // sc)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        up = np.array(Image.fromarray(g).resize((w, h), Image.BILINEAR), dtype=np.float32)
        acc += wt * up
    acc = (acc - acc.mean()) / (acc.std() + 1e-8)
    return acc


# --------------------------------------------------------------------------- 1. Character Skin + Face + Cleavage (1024x1024)
# UV layout convention for surf_skin:
#   Top half    v in [0.00 .. 0.52] (image y 0..532): Head cylindrical wrap
#               u = 0.50 is nose/face center; u in [0.22..0.78] is front face, outer u is back of neck/scalp
#   Bottom-left u in [0.00 .. 0.65], v in [0.52 .. 1.00] (image y 532..1024): Neck + Collarbones + Plunging Cleavage & Inner Bust
#               u = 0.325 is sternum midline (deep cleavage crease!)
#   Bottom-right u in [0.65 .. 1.00], v in [0.52 .. 1.00]: Character hands, fingers, fingernails & ankle skin
def build_tex_skin():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    # Warm sun-kissed golden-tan base (inspired by video character)
    base = np.zeros((S, S, 3), dtype=np.float32)
    base[..., 0] = 0.895
    base[..., 1] = 0.665
    base[..., 2] = 0.535

    pores = fbm_noise(S, S, scales=(2, 4, 8, 16), weights=(0.4, 0.3, 0.2, 0.1), seed=101)
    base += pores[..., None] * np.array([0.010, 0.008, 0.007], dtype=np.float32)

    # --- A. Face region (v in [0.02..0.50], u centered at 0.50; 360 deg wrap -> front 180 deg is u in [0.25..0.75]) ---
    fu = (u - 0.50) / 0.195  # calibrated so fu = +-0.34 lands right at +-24 deg eye azimuth!
    fv = (v - 0.25) / 0.21   # -1 (forehead) .. +1 (chin/neck)
    in_face = (v < 0.52).astype(np.float32)

    # Soft forehead highlight & jawline warmth
    forehead_hi = np.exp(-((fu / 0.55) ** 2 + ((fv + 0.48) / 0.32) ** 2)) * in_face
    base += forehead_hi[..., None] * np.array([0.045, 0.040, 0.035])

    # Rosy warm cheek blush (lifted apples of cheeks from laughing!)
    for sgn in (-1.0, 1.0):
        cheek = np.exp(-(((fu - sgn * 0.44) / 0.26) ** 2 + ((fv - 0.06) / 0.20) ** 2)) * in_face
        base = base * (1.0 - 0.34 * cheek[..., None]) + np.array([0.93, 0.48, 0.46]) * (0.34 * cheek[..., None])
        # Cheekbone highlight
        ch_hi = np.exp(-(((fu - sgn * 0.38) / 0.16) ** 2 + ((fv + 0.02) / 0.10) ** 2)) * in_face
        base += ch_hi[..., None] * np.array([0.05, 0.042, 0.038])

    # Nose bridge highlight, tip blush & soft nostril shadows
    nose_bridge = np.exp(-((fu / 0.075) ** 2 + ((fv + 0.06) / 0.20) ** 2)) * in_face
    nose_tip = np.exp(-((fu / 0.10) ** 2 + ((fv - 0.10) / 0.08) ** 2)) * in_face
    base += (nose_bridge + 1.1 * nose_tip)[..., None] * np.array([0.055, 0.045, 0.038])
    for sgn in (-1.0, 1.0):
        ala = np.exp(-(((fu - sgn * 0.11) / 0.055) ** 2 + ((fv - 0.13) / 0.045) ** 2)) * in_face
        base *= (1.0 - 0.16 * ala[..., None])

    # --- B. Sternum & Deep Cleavage Shading (u in [0.00..0.65], v in [0.52..1.00]) ---
    in_chest = ((u < 0.65) & (v >= 0.52)).astype(np.float32)
    cu = (u - 0.325) / 0.325   # -1..+1 across chest skin UV, 0 = exact cleavage center
    cv = (v - 0.52) / 0.48     # 0 (neck/collarbone) .. 1 (underbust tie knot)

    # Collarbone subtle highlight & hollow at cv ~ 0.14
    for sgn in (-1.0, 1.0):
        clav = np.exp(-(((cu - sgn * 0.38) / 0.28) ** 2 + ((cv - 0.14) / 0.035) ** 2)) * in_chest
        base += clav[..., None] * np.array([0.045, 0.038, 0.032])

    # Deep realistic vertical cleavage shadow valley (warm sun-kissed subsurface shadow, never muddy/grey!)
    cleav_len = smoothstep(0.20, 0.38, cv) * (1.0 - 0.20 * smoothstep(0.90, 1.0, cv))
    cleav_valley = np.exp(-((cu / 0.075) ** 2)) * cleav_len * in_chest
    cleav_soft = np.exp(-((cu / 0.22) ** 2)) * cleav_len * in_chest
    c_cleav_deep = np.array([0.68, 0.41, 0.31], dtype=np.float32)
    c_cleav_warm = np.array([0.80, 0.54, 0.42], dtype=np.float32)
    base = base * (1.0 - 0.58 * cleav_valley[..., None]) + c_cleav_deep * (0.58 * cleav_valley[..., None])
    base = base * (1.0 - 0.28 * cleav_soft[..., None]) + c_cleav_warm * (0.28 * cleav_soft[..., None])

    # Luminous upper-inner breast dome highlights on each side of cleavage!
    for sgn in (-1.0, 1.0):
        dome_hi = np.exp(-(((cu - sgn * 0.42) / 0.28) ** 2 + ((cv - 0.54) / 0.24) ** 2)) * in_chest
        base += dome_hi[..., None] * np.array([0.075, 0.062, 0.050])

    # Subtle beauty marks on upper chest (visible in v1_f180 & v2_f060!)
    im = Image.fromarray((clamp01(base) * 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im, "RGBA")
    dr.ellipse((326, 650, 330, 654), fill=(115, 72, 54, 165))
    dr.ellipse((345, 672, 348, 675), fill=(120, 76, 58, 140))

    # --- Paint crisp facial features with supersampled vector drawing (2x -> Lanczos) ---
    F2 = S * 2
    overlay = Image.new("RGBA", (F2, F2), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")

    def fx(fu_val):
        return (0.50 + fu_val * 0.195) * F2

    def fy(fv_val):
        return (0.25 + fv_val * 0.21) * F2

    # 1. Arched honey-brown eyebrows
    for sgn in (-1.0, 1.0):
        pts = [
            (fx(sgn * 0.12), fy(-0.25)),
            (fx(sgn * 0.28), fy(-0.34)),
            (fx(sgn * 0.46), fy(-0.35)),
            (fx(sgn * 0.59), fy(-0.26)),
            (fx(sgn * 0.46), fy(-0.295)),
            (fx(sgn * 0.28), fy(-0.28)),
        ]
        od.polygon(pts, fill=(98, 64, 42, 225))

    # 2. Happy crinkled smiling eyes (almond curve, warm hazel-brown iris, catchlights, lush lashes)
    for sgn in (-1.0, 1.0):
        ex = fx(sgn * 0.32)
        ey = fy(-0.11)
        ew = 0.165 * 0.195 * F2
        eh = 0.068 * 0.21 * F2

        # Soft eyeshadow crease above eye
        od.arc((ex - ew * 1.15, ey - eh * 1.75, ex + ew * 1.15, ey + eh * 0.6), 195, 345, fill=(138, 84, 66, 135), width=6)

        # Sclera almond
        eye_poly = []
        for k in range(24):
            ang = 2 * math.pi * k / 24
            px = ex + math.cos(ang) * ew
            py = ey + math.sin(ang) * eh * (0.84 if math.sin(ang) > 0 else 1.06) - 0.15 * eh * math.cos(ang * 2)
            eye_poly.append((px, py))
        od.polygon(eye_poly, fill=(250, 246, 244, 250))

        # Warm honey-brown iris + dark pupil
        ir = eh * 0.94
        od.ellipse((ex - ir, ey - ir * 0.95, ex + ir, ey + ir * 0.95), fill=(92, 58, 34, 255))
        od.ellipse((ex - ir * 0.72, ey - ir * 0.70, ex + ir * 0.72, ey + ir * 0.70), fill=(138, 92, 54, 255))
        pr = ir * 0.42
        od.ellipse((ex - pr, ey - pr, ex + pr, ey + pr), fill=(20, 14, 14, 255))
        # Dual sparkly catchlights
        od.ellipse((ex - ir * 0.44, ey - ir * 0.54, ex - ir * 0.08, ey - ir * 0.18), fill=(255, 255, 255, 250))
        od.ellipse((ex + ir * 0.18, ey + ir * 0.10, ex + ir * 0.38, ey + ir * 0.30), fill=(255, 250, 245, 200))

        # Thick dark winged upper lash line + happy lower lash line
        upper_pts = []
        for t in np.linspace(-1.12, 1.20, 18):
            ux = ex + sgn * t * ew
            uy = ey - math.cos(t * 1.14) * eh * 0.98 - (0.26 * eh if t > 0.82 else 0.0)
            upper_pts.append((ux, uy))
        od.line(upper_pts, fill=(24, 15, 16, 252), width=10)
        # Lower laugh crinkle / aegyo-sal warmth
        od.arc((ex - ew * 0.95, ey - eh * 0.2, ex + ew * 0.95, ey + eh * 1.35), 15, 165, fill=(152, 92, 74, 140), width=5)

    # 3. Nostril openings
    for sgn in (-1.0, 1.0):
        nx = fx(sgn * 0.072)
        ny = fy(0.145)
        od.ellipse((nx - 10, ny - 5, nx + 10, ny + 5), fill=(102, 56, 44, 205))

    # 4. Big joyful laughing smile! (Glossy rose lips + bright white upper teeth + warm mouth interior)
    mx = fx(0.0)
    my = fy(0.35)
    mw = 0.34 * 0.195 * F2
    mh = 0.165 * 0.21 * F2

    # Nasolabial smile laugh lines (subtle)
    for sgn in (-1.0, 1.0):
        ax0 = min(mx + sgn * mw * 0.55, mx + sgn * mw * 1.25) - 36
        ax1 = max(mx + sgn * mw * 0.55, mx + sgn * mw * 1.25) + 36
        od.arc(
            (ax0, fy(0.12), ax1, fy(0.42)),
            295 if sgn > 0 else 185,
            355 if sgn > 0 else 245,
            fill=(168, 102, 82, 90),
            width=5,
        )

    # Outer lip contour (Cupid's bow on upper lip, full curved lower lip, upturned happy corners!)
    outer_lip = []
    for t in np.linspace(-1.0, 1.0, 33):
        lx = mx + t * mw
        cupid = 0.14 * mh * math.exp(-((t / 0.18) ** 2)) - 0.10 * mh * math.exp(-(((abs(t) - 0.18) / 0.14) ** 2))
        corner_lift = -0.24 * mh * (t * t)
        ly = my - (1.0 - t * t) * mh * 0.72 + cupid + corner_lift
        outer_lip.append((lx, ly))
    for t in np.linspace(1.0, -1.0, 33):
        lx = mx + t * mw
        corner_lift = -0.24 * mh * (t * t)
        ly = my + (1.0 - t * t) * mh * 1.18 + corner_lift
        outer_lip.append((lx, ly))
    od.polygon(outer_lip, fill=(198, 78, 92, 245))

    # Inner open mouth cavity
    inner_mouth = []
    iw, ih = mw * 0.82, mh * 0.68
    for t in np.linspace(-1.0, 1.0, 29):
        lx = mx + t * iw
        ly = my - (1.0 - t * t) * ih * 0.42 - 0.20 * mh * (t * t)
        inner_mouth.append((lx, ly))
    for t in np.linspace(1.0, -1.0, 29):
        lx = mx + t * iw
        ly = my + (1.0 - t * t) * ih * 0.88 - 0.20 * mh * (t * t)
        inner_mouth.append((lx, ly))
    od.polygon(inner_mouth, fill=(92, 26, 34, 255))

    # Warm pink tongue in lower mouth cavity
    tongue_pts = []
    for t in np.linspace(-0.62, 0.62, 21):
        lx = mx + t * iw
        ly = my + 0.12 * ih + (0.38 - t * t) * ih * 0.95
        tongue_pts.append((lx, ly))
    od.polygon(tongue_pts, fill=(196, 84, 94, 240))

    # Bright white upper teeth row!
    teeth_pts = []
    for t in np.linspace(-0.88, 0.88, 25):
        lx = mx + t * iw
        ly = my - (1.0 - t * t) * ih * 0.40 - 0.18 * mh * (t * t)
        teeth_pts.append((lx, ly))
    for t in np.linspace(0.88, -0.88, 25):
        lx = mx + t * iw
        ly = my + (1.0 - 0.65 * t * t) * ih * 0.18 - 0.18 * mh * (t * t)
        teeth_pts.append((lx, ly))
    od.polygon(teeth_pts, fill=(250, 248, 246, 255))
    # Subtle individual tooth vertical separators
    for tx_f in (-0.62, -0.40, -0.19, 0.0, 0.19, 0.40, 0.62):
        tx = mx + tx_f * iw
        od.line([(tx, my - ih * 0.32), (tx, my + ih * 0.14)], fill=(216, 206, 204, 150), width=2)

    # Glossy lower lip specular highlight
    od.arc((mx - mw * 0.48, my + mh * 0.52, mx + mw * 0.48, my + mh * 0.96), 15, 165, fill=(255, 215, 222, 160), width=7)

    # 5. Character manicured pale-pink fingernails patch at u in [0.85..0.98], v in [0.85..0.98]
    nx0, ny0, nx1, ny1 = int(0.84 * F2), int(0.84 * F2), int(0.98 * F2), int(0.98 * F2)
    od.rounded_rectangle((nx0, ny0, nx1, ny1), radius=24, fill=(246, 210, 218, 255))
    od.rectangle((nx0, ny0, nx1, ny0 + int(0.03 * F2)), fill=(255, 248, 250, 255))

    overlay_sm = overlay.filter(ImageFilter.GaussianBlur(1.1)).resize((S, S), Image.LANCZOS)
    im = Image.alpha_composite(im.convert("RGBA"), overlay_sm).convert("RGB")
    im.save(os.path.join(OUT_DIR, "tex_skin.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 2. Silky Center-Parted Blonde Hair (1024x1024)
# UV layout:
#   v = 0.00 is exact center part / roots at crown
#   v = 1.00 is feathered hair tips
#   u runs along hair curtain width
def build_tex_hair():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    rng = np.random.default_rng(202)
    # Multi-frequency vertical strand texture (dense silky individual locks)
    strand = np.zeros((S, S), dtype=np.float32)
    for freq, amp in ((48, 0.30), (112, 0.28), (240, 0.24), (460, 0.18)):
        prof = rng.standard_normal(freq).astype(np.float32)
        prof_up = np.array(Image.fromarray(prof[None, :]).resize((S, 1), Image.BICUBIC), dtype=np.float32)[0]
        # Slight organic wave along v
        shift = (4.0 * np.sin(v * 7.0 + u * 5.0)).astype(np.int32)
        idx = (xx.astype(np.int32) + shift) % S
        strand += amp * prof_up[idx]
    strand = (strand - strand.mean()) / (strand.std() + 1e-8)

    # Root-to-tip gradient: dark honey-ash root shadow (v < 0.11) -> golden champagne -> luminous platinum blonde
    root_t = smoothstep(0.015, 0.15, v)
    tip_t = smoothstep(0.45, 0.95, v)

    c_root = np.array([0.34, 0.24, 0.17], dtype=np.float32)
    c_mid = np.array([0.84, 0.72, 0.56], dtype=np.float32)
    c_tip = np.array([0.93, 0.85, 0.72], dtype=np.float32)

    col = c_root * (1.0 - root_t[..., None]) + c_mid * root_t[..., None]
    col = col * (1.0 - 0.65 * tip_t[..., None]) + c_tip * (0.65 * tip_t[..., None])

    # Apply strand variation (lowlights & highlights)
    col += strand[..., None] * np.array([0.075, 0.068, 0.055], dtype=np.float32) * (0.45 + 0.55 * root_t[..., None])

    # Anisotropic angelic hair sheen bands across v ~ 0.26 and v ~ 0.62
    sheen1 = np.exp(-(((v - 0.26 + 0.02 * np.sin(u * 18.0)) / 0.065) ** 2))
    sheen2 = np.exp(-(((v - 0.64 + 0.025 * np.cos(u * 14.0)) / 0.085) ** 2))
    col += (0.095 * sheen1 + 0.065 * sheen2)[..., None] * np.array([1.0, 0.97, 0.90])

    # Subtle scalp part skin line right at v < 0.014
    scalp = 1.0 - smoothstep(0.004, 0.018, v)
    col = col * (1.0 - 0.55 * scalp[..., None]) + np.array([0.82, 0.61, 0.49]) * (0.55 * scalp[..., None])

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    im.save(os.path.join(OUT_DIR, "tex_hair.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 3. Vibrant Hot-Pink Tie-Front Top (1024x1024)
# UV layout:
#   u in [0..1], v in [0..1]
#   Center tie-knot gather focal point at (u=0.50, v=0.72) on front torso; also tiled cleanly for sleeves & bow ribbons!
def build_tex_pink_top():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    # Signature vibrant hot-pink / magenta jersey color from videos (#e6146b)
    c_pink = np.array([0.905, 0.082, 0.425], dtype=np.float32)
    c_deep = np.array([0.560, 0.028, 0.245], dtype=np.float32)
    c_high = np.array([0.985, 0.270, 0.585], dtype=np.float32)

    # Fine jersey knit micro-rib
    rib = 0.5 + 0.5 * np.sin(xx * (2.0 * math.pi / 4.0)) * 0.6 + 0.4 * np.sin(yy * (2.0 * math.pi / 5.0))
    fuzz = fbm_noise(S, S, scales=(2, 4, 8), weights=(0.5, 0.3, 0.2), seed=303)

    col = np.broadcast_to(c_pink, (S, S, 3)).copy()
    col += (rib - 0.5)[..., None] * 0.018 + fuzz[..., None] * 0.012

    # Radial gathered tension pleats radiating from front tie-knot center (u=0.50, v=0.74)
    dx = u - 0.50
    dy = v - 0.74
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    pleat_env = np.exp(-((r / 0.34) ** 2)) * smoothstep(0.02, 0.09, r)
    pleat_wave = np.sin(ang * 22.0 + 3.0 * np.sin(ang * 5.0)) * 0.65 + 0.35 * np.sin(ang * 41.0)
    col = (
        col
        + np.maximum(0.0, pleat_wave)[..., None] * pleat_env[..., None] * (c_high - c_pink) * 0.55
        + np.maximum(0.0, -pleat_wave)[..., None] * pleat_env[..., None] * (c_pink - c_deep) * -0.65
    )

    # Soft breast cup volume highlight domes (u ~ 0.30 and u ~ 0.70, v ~ 0.48)
    for cu in (0.30, 0.70):
        cup_hi = np.exp(-(((u - cu) / 0.16) ** 2 + ((v - 0.46) / 0.18) ** 2))
        col = col * (1.0 - 0.28 * cup_hi[..., None]) + c_high * (0.28 * cup_hi[..., None])
        # Under-cup shadow crescent
        under_sh = np.exp(-(((u - cu) / 0.18) ** 2 + ((v - 0.76) / 0.07) ** 2))
        col = col * (1.0 - 0.35 * under_sh[..., None]) + c_deep * (0.35 * under_sh[..., None])

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    im.save(os.path.join(OUT_DIR, "tex_pink_top.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 4. Indigo Blue Skinny Jeans (1024x1024)
# UV layout:
#   Left half  u in [0.00 .. 0.50]: FRONT of jeans (u=0.25 is front fly midline, v=0.04 waistband .. v=0.96 ankle hem)
#   Right half u in [0.50 .. 1.00]: BACK  of jeans (u=0.75 is rear center seam, rear yoke + 2 angled patch pockets on glutes!)
def build_tex_jeans():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    c_indigo = np.array([0.195, 0.345, 0.505], dtype=np.float32)
    c_fade = np.array([0.385, 0.555, 0.725], dtype=np.float32)
    c_dark = np.array([0.105, 0.195, 0.305], dtype=np.float32)

    # Diagonal 45-degree twill weave + slub yarn streaks
    twill = np.sin((xx + yy) * (2.0 * math.pi / 3.2)) * 0.5
    slub_v = fbm_noise(S, S, scales=(2, 8, 24), weights=(0.5, 0.3, 0.2), seed=404)
    col = np.broadcast_to(c_indigo, (S, S, 3)).copy()
    col += twill[..., None] * 0.016 + slub_v[..., None] * 0.022

    # Front & back thigh / glute stonewash fade centers
    for cu, cv, rx, ry, k in (
        # Front left & right thigh fades
        (0.15, 0.44, 0.065, 0.22, 0.55),
        (0.35, 0.44, 0.065, 0.22, 0.55),
        # Back left & right glute & hamstring fades (matches v3_f168!)
        (0.64, 0.24, 0.075, 0.10, 0.48),
        (0.86, 0.24, 0.075, 0.10, 0.48),
        (0.64, 0.50, 0.060, 0.20, 0.38),
        (0.86, 0.50, 0.060, 0.20, 0.38),
    ):
        fd = np.exp(-(((u - cu) / rx) ** 2 + ((v - cv) / ry) ** 2))
        col = col * (1.0 - k * fd[..., None]) + c_fade * (k * fd[..., None])

    # Hip/groin vintage whisker creases on front (v ~ 0.20..0.28)
    for cu, sgn in ((0.17, -1.0), (0.33, 1.0)):
        for wy in (0.19, 0.225, 0.26):
            wh = np.exp(-(((u - cu) / 0.055) ** 2 + (((v - wy) - sgn * 0.18 * (u - cu)) / 0.008) ** 2))
            col = col * (1.0 - 0.35 * wh[..., None]) + c_fade * (0.35 * wh[..., None])

    # Darken waistband top strip (v < 0.065) and rolled ankle cuff strip (v > 0.94)
    wb = 1.0 - smoothstep(0.055, 0.070, v)
    cuff = smoothstep(0.935, 0.950, v)
    col = col * (1.0 - 0.22 * (wb + cuff)[..., None]) + c_dark * (0.22 * (wb + cuff)[..., None])

    # Outer & center seam Indigo puckering shadows
    for su in (0.01, 0.25, 0.49, 0.51, 0.75, 0.99):
        sm = np.exp(-(((u - su) / 0.010) ** 2))
        col = col * (1.0 - 0.32 * sm[..., None]) + c_dark * (0.32 * sm[..., None])

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im, "RGBA")
    STITCH = (206, 152, 74, 225)     # Classic golden-tan contrast denim topstitch
    DARK_SEAM = (24, 44, 72, 210)

    # Waistband bottom seam + double topstitch across full width
    dr.line([(0, int(0.062 * S)), (S, int(0.062 * S))], fill=DARK_SEAM, width=4)
    dr.line([(0, int(0.058 * S)), (S, int(0.058 * S))], fill=STITCH, width=2)
    dr.line([(0, int(0.012 * S)), (S, int(0.012 * S))], fill=STITCH, width=2)

    # Ankle cuff topstitch
    dr.line([(0, int(0.942 * S)), (S, int(0.942 * S))], fill=DARK_SEAM, width=4)
    dr.line([(0, int(0.948 * S)), (S, int(0.948 * S))], fill=STITCH, width=2)

    # Side & center vertical topstitching
    for su in (0.008, 0.492, 0.508, 0.992):
        sx = int(su * S)
        dr.line([(sx, int(0.062 * S)), (sx, int(0.945 * S))], fill=STITCH, width=2)
    # Rear center rise double stitch
    dr.line([(int(0.748 * S), int(0.062 * S)), (int(0.748 * S), int(0.32 * S))], fill=STITCH, width=2)
    dr.line([(int(0.753 * S), int(0.062 * S)), (int(0.753 * S), int(0.32 * S))], fill=STITCH, width=2)

    # Front J-fly seam + silver tack button (u = 0.25)
    fx = int(0.25 * S)
    dr.line([(fx, int(0.062 * S)), (fx, int(0.245 * S))], fill=DARK_SEAM, width=3)
    dr.arc((fx - 4, int(0.062 * S), fx + 28, int(0.235 * S)), 270, 90, fill=STITCH, width=2)
    # Button
    bx, by = fx + 4, int(0.036 * S)
    dr.ellipse((bx - 10, by - 10, bx + 10, by + 10), fill=(192, 198, 206, 255), outline=(90, 98, 110, 255), width=2)
    dr.ellipse((bx - 4, by - 4, bx + 4, by + 4), fill=(135, 142, 152, 255))

    # Front curved scoop pockets + coin pocket + copper rivets
    # Left side of front UV (u in 0.03..0.15) and Right side (u in 0.35..0.47)
    dr.arc((int(0.01 * S), int(0.01 * S), int(0.155 * S), int(0.165 * S)), 0, 92, fill=DARK_SEAM, width=4)
    dr.arc((int(0.01 * S), int(0.014 * S), int(0.151 * S), int(0.161 * S)), 0, 92, fill=STITCH, width=2)
    dr.arc((int(0.345 * S), int(0.01 * S), int(0.49 * S), int(0.165 * S)), 88, 180, fill=DARK_SEAM, width=4)
    dr.arc((int(0.349 * S), int(0.014 * S), int(0.49 * S), int(0.161 * S)), 88, 180, fill=STITCH, width=2)
    # Coin pocket on right hip
    dr.rectangle((int(0.385 * S), int(0.088 * S), int(0.455 * S), int(0.142 * S)), outline=STITCH, width=2)
    for rx, ry in ((0.148, 0.072), (0.352, 0.072), (0.385, 0.088), (0.455, 0.088)):
        px, py = int(rx * S), int(ry * S)
        dr.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(198, 128, 76, 255))

    # Back V-yoke seam (u in 0.50..1.00)
    dr.line([(int(0.505 * S), int(0.105 * S)), (int(0.75 * S), int(0.145 * S)), (int(0.995 * S), int(0.105 * S))], fill=DARK_SEAM, width=4)
    dr.line([(int(0.505 * S), int(0.101 * S)), (int(0.75 * S), int(0.141 * S)), (int(0.995 * S), int(0.101 * S))], fill=STITCH, width=2)

    # Two 5-point sculpted-look Rear Patch Pockets on glutes (u ~ 0.63 and u ~ 0.87, v ~ 0.14..0.28)
    for pu in (0.625, 0.875):
        pw, ph_top, ph_mid, ph_bot = 0.068 * S, 0.145 * S, 0.248 * S, 0.282 * S
        pcx = pu * S
        pts = [
            (pcx - pw, ph_top),
            (pcx + pw, ph_top),
            (pcx + pw * 0.88, ph_mid),
            (pcx, ph_bot),
            (pcx - pw * 0.88, ph_mid),
        ]
        # Slight dark drop-shadow around pocket edge
        sh_pts = [(x + 2, y + 3) for x, y in pts]
        dr.polygon(sh_pts, fill=(18, 34, 58, 145))
        dr.polygon(pts, fill=(46, 82, 122, 235), outline=DARK_SEAM)
        dr.line(pts + [pts[0]], fill=STITCH, width=2)
        inner_pts = [(pcx + (x - pcx) * 0.90, ph_top + 6 + (y - ph_top) * 0.88) for x, y in pts]
        dr.line(inner_pts + [inner_pts[0]], fill=STITCH, width=2)
        # Decorative pocket arcuate stitch
        dr.line([(pcx - pw * 0.82, ph_top + 42), (pcx, ph_top + 58), (pcx + pw * 0.82, ph_top + 42)], fill=STITCH, width=2)

    # 5 Belt loops around waistband
    for lu in (0.12, 0.38, 0.58, 0.75, 0.92):
        lx = int(lu * S)
        dr.rectangle((lx - 7, int(0.008 * S), lx + 7, int(0.074 * S)), fill=(38, 68, 104, 255), outline=STITCH, width=2)

    im.save(os.path.join(OUT_DIR, "tex_jeans.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 5. Hot-Pink Athletic Sneakers (512x512)
# UV layout:
#   Top-down / wrap projection: u=0.50 is instep/toe centerline, v=0.08 heel .. v=0.92 toe tip,
#   lower strip v in [0.82..1.00] or side wrap includes tonal pink sculpted rubber midsole
def build_tex_sneakers():
    S = 512
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    c_pink = np.array([0.915, 0.095, 0.445], dtype=np.float32)
    c_mesh = np.array([0.825, 0.068, 0.385], dtype=np.float32)
    c_sole = np.array([0.945, 0.165, 0.495], dtype=np.float32)

    # Breathable athletic mesh dimple pattern
    dimple = (np.sin(xx * (2 * math.pi / 6.0)) * np.sin(yy * (2 * math.pi / 6.0))) > 0.35
    col = np.where(dimple[..., None], c_mesh, c_pink).astype(np.float32)

    # Sole band along outer perimeter / bottom strip (v > 0.82)
    in_sole = smoothstep(0.80, 0.83, v)
    rib_sole = 0.5 + 0.5 * np.sin(xx * (2 * math.pi / 8.0))
    col = col * (1.0 - in_sole[..., None]) + (c_sole * (0.92 + 0.10 * rib_sole[..., None])) * in_sole[..., None]

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im, "RGBA")

    # Toe-box overlay & vamp stitching (u centered at 0.5, toe around v=0.68, tongue v=0.25..0.58)
    dr.arc((int(0.20 * S), int(0.46 * S), int(0.80 * S), int(0.78 * S)), 180, 360, fill=(145, 12, 68, 220), width=4)
    dr.arc((int(0.22 * S), int(0.48 * S), int(0.78 * S), int(0.76 * S)), 180, 360, fill=(252, 88, 155, 200), width=2)

    # Tongue throat recess + 5 pairs of eyelets + criss-cross hot-pink laces!
    dr.rounded_rectangle((int(0.38 * S), int(0.20 * S), int(0.62 * S), int(0.56 * S)), radius=18, fill=(176, 15, 82, 235), outline=(120, 8, 56, 240), width=3)
    ys = [int(f * S) for f in (0.25, 0.32, 0.39, 0.46, 0.52)]
    xl, xr = int(0.39 * S), int(0.61 * S)
    for i in range(len(ys) - 1):
        dr.line([(xl, ys[i]), (xr, ys[i + 1])], fill=(252, 62, 138, 255), width=8)
        dr.line([(xr, ys[i]), (xl, ys[i + 1])], fill=(235, 32, 114, 255), width=8)
    for y_e in ys:
        for x_e in (xl, xr):
            dr.ellipse((x_e - 5, y_e - 5, x_e + 5, y_e + 5), fill=(130, 10, 60, 255), outline=(255, 110, 170, 220), width=2)

    # Midsole groove line
    dr.line([(0, int(0.82 * S)), (S, int(0.82 * S))], fill=(145, 14, 68, 220), width=4)
    dr.line([(0, int(0.91 * S)), (S, int(0.91 * S))], fill=(168, 20, 80, 190), width=3)

    im.save(os.path.join(OUT_DIR, "tex_sneakers.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 6. Giant Articulated Right Hand + Nails (1024x1024)
# UV layout:
#   u in [0.00 .. 0.46], v in [0.00 .. 1.00]: DORSAL hand & fingers (knuckle folds, skin pores, subtle tendons)
#   u in [0.46 .. 0.86], v in [0.00 .. 1.00]: PALMAR hand & fingers (palmar warmth, life/head/heart lines, finger creases)
#   u in [0.86 .. 1.00], v in [0.00 .. 1.00]: FINGERNAIL plate UV (natural pale-pink nail bed, white lunula crescent, ivory free edge!)
def build_tex_giant_hand():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    pores = fbm_noise(S, S, scales=(2, 4, 8, 20), weights=(0.42, 0.28, 0.18, 0.12), seed=606)
    fine_lines = np.sin(yy * (2 * math.pi / 5.5) + 1.5 * pores) * 0.5

    # Warm Caucasian/tan male-or-neutral hand tone matching v1_f180 & v3_f096
    c_dorsal = np.array([0.855, 0.658, 0.535], dtype=np.float32)
    c_palm = np.array([0.895, 0.688, 0.575], dtype=np.float32)

    is_palm = smoothstep(0.45, 0.47, u) * (1.0 - smoothstep(0.85, 0.87, u))
    col = c_dorsal * (1.0 - is_palm[..., None]) + c_palm * is_palm[..., None]
    col += pores[..., None] * np.array([0.016, 0.013, 0.011]) + fine_lines[..., None] * 0.005

    # Rosy warmth on palmar pads & fingertips (v > 0.72)
    tip_rosy = smoothstep(0.68, 0.92, v) * (1.0 - smoothstep(0.85, 0.87, u))
    col = col * (1.0 - 0.18 * tip_rosy[..., None]) + np.array([0.88, 0.53, 0.47]) * (0.18 * tip_rosy[..., None])

    # --- Nail Plate Region (u in [0.86 .. 1.00], v = 0 cuticle/base -> v = 1 free tip) ---
    is_nail = smoothstep(0.858, 0.865, u)
    nu = (u - 0.93) / 0.065   # -1..+1 across nail width
    nv = v                    # 0 (cuticle) .. 1 (free tip)

    # Warm rosy-tan natural nail bed matching hand skin tone
    nail_col = np.broadcast_to(np.array([0.882, 0.672, 0.595], dtype=np.float32), (S, S, 3)).copy()
    # Longitudinal micro-ridges + specular sheen strip
    nail_ridge = np.sin(nu * 38.0) * 0.005 + np.exp(-(((nu + 0.22) / 0.22) ** 2)) * 0.042
    nail_col += nail_ridge[..., None]

    # Subtle half-moon lunula at base (nv < 0.18)
    lunula_r = np.hypot(nu * 0.90, (nv - 0.03) / 0.17)
    lunula = 1.0 - smoothstep(0.82, 1.02, lunula_r)
    nail_col = nail_col * (1.0 - 0.30 * lunula[..., None]) + np.array([0.93, 0.81, 0.76]) * (0.30 * lunula[..., None])

    # Short trimmed natural ivory free nail edge at tip (nv > 0.86 + arch)
    free_arch = 0.87 - 0.04 * (1.0 - nu * nu)
    free_tip = smoothstep(free_arch - 0.02, free_arch + 0.015, nv)
    # Thin darker pink hyponychium band right before free edge
    hypo = np.exp(-(((nv - (free_arch - 0.025)) / 0.022) ** 2))
    nail_col = nail_col * (1.0 - 0.20 * hypo[..., None]) + np.array([0.76, 0.51, 0.47]) * (0.20 * hypo[..., None])
    nail_col = nail_col * (1.0 - 0.65 * free_tip[..., None]) + np.array([0.93, 0.86, 0.79]) * (0.65 * free_tip[..., None])

    # Cuticle border shading around edges
    cuticle = 1.0 - smoothstep(0.0, 0.045, nv)
    nail_col *= (1.0 - 0.16 * cuticle[..., None])

    col = col * (1.0 - is_nail[..., None]) + nail_col * is_nail[..., None]

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im, "RGBA")

    # Paint Dorsal Knuckle Skin-Fold Ellipses (u in 0.05..0.41, finger PIP & DIP joints at v ~ 0.58 and v ~ 0.76)
    CREASE_DARK = (166, 114, 88, 105)
    CREASE_HI = (238, 194, 166, 70)
    for fu in (0.09, 0.18, 0.27, 0.36, 0.42):
        cx = int(fu * S)
        for jv, rx, ry in ((0.42, 24, 9), (0.60, 22, 10), (0.77, 18, 7)):
            cy = int(jv * S)
            for k in (-5, 0, 5):
                dr.arc((cx - rx, cy + k - ry, cx + rx, cy + k + ry), 10, 170, fill=CREASE_DARK, width=2)
                dr.arc((cx - rx, cy + k - ry + 2, cx + rx, cy + k + ry + 2), 190, 350, fill=CREASE_HI, width=1)

    # Paint Palmar Flexion Lines (Heart line, Head line, Thenar Life line + finger joint creases on u in 0.48..0.84)
    PALM_LINE = (164, 106, 84, 128)
    # Heart line
    dr.line([(int(0.50 * S), int(0.38 * S)), (int(0.64 * S), int(0.36 * S)), (int(0.76 * S), int(0.41 * S))], fill=PALM_LINE, width=4)
    # Head line
    dr.line([(int(0.79 * S), int(0.33 * S)), (int(0.66 * S), int(0.31 * S)), (int(0.53 * S), int(0.26 * S))], fill=PALM_LINE, width=4)
    # Thenar Life line curving around thumb base
    dr.arc((int(0.64 * S), int(0.11 * S), int(0.84 * S), int(0.36 * S)), 105, 265, fill=PALM_LINE, width=5)
    # Wrist bracelet creases
    dr.line([(int(0.54 * S), int(0.08 * S)), (int(0.78 * S), int(0.08 * S))], fill=PALM_LINE, width=3)
    dr.line([(int(0.56 * S), int(0.06 * S)), (int(0.76 * S), int(0.06 * S))], fill=PALM_LINE, width=2)
    # Palmar finger joint flexion creases
    for fu in (0.52, 0.60, 0.68, 0.76, 0.82):
        cx = int(fu * S)
        for jv in (0.44, 0.61, 0.77):
            cy = int(jv * S)
            dr.line([(cx - 20, cy), (cx + 20, cy)], fill=PALM_LINE, width=3)
            dr.line([(cx - 17, cy + 4), (cx + 17, cy + 4)], fill=PALM_LINE, width=2)

    im = im.filter(ImageFilter.GaussianBlur(0.55))
    im.save(os.path.join(OUT_DIR, "tex_giant_hand.png"), "PNG", optimize=True)
    return im


# --------------------------------------------------------------------------- 7. Aerodynamic Slipstream Speed-Lines (512x256 RGBA)
def build_tex_speedlines():
    W, H = 512, 256
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xx / W   # 0 = leading nose (+X), 1 = trailing tail (-X)
    v = yy / H   # across ribbon width

    # Tapered longitudinal fade + soft cross-ribbon Gaussian core
    long_env = smoothstep(0.02, 0.18, u) * (1.0 - smoothstep(0.45, 0.98, u))
    cross_env = np.exp(-(((v - 0.5) / 0.22) ** 2))
    core_env = np.exp(-(((v - 0.5) / 0.08) ** 2))

    # Subtle iridescent warm-pearl / cool-cyan shimmer matching v3_f120 & v3_f168 speed streaks
    shimmer = 0.5 + 0.5 * np.sin(u * 14.0 + v * 9.0)
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    rgb[..., 0] = 0.96 + 0.04 * shimmer
    rgb[..., 1] = 0.94 + 0.04 * (1.0 - shimmer)
    rgb[..., 2] = 0.98
    alpha = clamp01((0.42 * cross_env + 0.52 * core_env) * long_env)

    rgba = np.dstack([clamp01(rgb), alpha])
    im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    im.save(os.path.join(OUT_DIR, "tex_speedlines.png"), "PNG", optimize=True)
    return im


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build_tex_skin()
    build_tex_hair()
    build_tex_pink_top()
    build_tex_jeans()
    build_tex_sneakers()
    build_tex_giant_hand()
    build_tex_speedlines()
    print("Generated all 7 brand-new textures in:", OUT_DIR)


if __name__ == "__main__":
    main()
