"""Builds clean, 100% complete, zero-speck master character & demon rigs across all 8 360° angles
strictly starring TINFOIL-HAT BRYAN (pointed silver tinfoil cone hat + rainbow unicorn shirt + RGB Demon Detector)
and his Demons (Crimson Horned Demon, Winged Red Demon, Cloaked Skeletal Grim Reaper, Muscular Grey Ram-Horned Demon).
"""
import math
import os
import cv2
import numpy as np
import torch
import torchvision
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
LAYERS_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_layers")
RIGS_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_rigs")
DBG_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_debug")
os.makedirs(RIGS_DIR, exist_ok=True)


def keep_significant_components(rgba, min_area=450):
    arr = rgba.copy()
    m = arr[..., 3] > 20
    lbl, n = ndimage.label(m)
    if n == 0:
        return arr
    sizes = ndimage.sum(m, lbl, range(1, n + 1))
    keep_ids = [1 + i for i, s in enumerate(sizes) if s >= min_area]
    if not keep_ids:
        keep_ids = [1 + int(np.argmax(sizes))]
    keep = ndimage.binary_dilation(np.isin(lbl, keep_ids), iterations=2)
    arr[~keep, 3] = 0
    return arr


def clean_split_pair_without_drawn_antenna():
    """Re-splits pair_q*.png cleanly before any drawn antenna stick so every quadrant is 100% pure."""
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    weights = torchvision.models.detection.MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    model = torchvision.models.detection.maskrcnn_resnet50_fpn_v2(weights=weights).to(dev).eval()
    preprocess = weights.transforms()

    bryan_raw = {}
    demon_raw = {}
    for qn in ("q0_front", "q1_fl45", "q2_profR", "q3_bl135"):
        q_rgba = np.array(Image.open(os.path.join(LAYERS_DIR, f"pair_{qn}.png")))
        H, W = q_rgba.shape[:2]
        fg = q_rgba[..., 3] > 8
        rgb = q_rgba[..., :3]
        af = q_rgba[..., 3:4].astype(np.float32) / 255.0
        comp_rgb = (rgb.astype(np.float32) * af + 118.0 * (1.0 - af)).astype(np.uint8)
        with torch.no_grad():
            pred = model([preprocess(Image.fromarray(comp_rgb)).to(dev)])[0]
        scores = pred["scores"].cpu().numpy()
        masks = pred["masks"].cpu().numpy()[:, 0]

        cands = []
        for i in range(len(scores)):
            if scores[i] < 0.35:
                continue
            m = masks[i]
            ov = float(np.sum((m > 0.4) & fg))
            if ov < 1200:
                continue
            ys, _ = np.nonzero((m > 0.45) & fg)
            ymid = np.percentile(ys, 55)
            up = (m > 0.45) & fg & (np.arange(H)[:, None] < ymid)
            rex = float(np.mean(rgb[up, 0].astype(np.float32) - np.maximum(rgb[up, 1], rgb[up, 2]).astype(np.float32))) if np.any(up) else 0.0
            cands.append((scores[i], ov, rex, m))

        p_b = max([c for c in cands if c[2] < 28.0], key=lambda c: c[1])[3]
        p_d = max([c for c in cands if c[2] >= 28.0], key=lambda c: c[1])[3]

        rf, gf, bf = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
        is_crimson = (rf - np.maximum(gf, bf) > 42.0) & (gf < 72.0) & (bf < 75.0)
        is_indigo = (bf - rf > 10.0) & (bf > 34.0)
        is_bright = (np.minimum(rf, np.minimum(gf, bf)) > 145.0) | ((rf > 165.0) & (gf > 140.0) & (bf < 80.0))

        sb = p_b + 0.55 * is_indigo + 0.55 * is_bright - 0.85 * is_crimson
        sd = p_d + 0.85 * is_crimson - 0.45 * is_indigo
        diff = cv2.GaussianBlur((sb - sd).astype(np.float32), (5, 5), 1.1)
        wb = np.clip(0.5 + diff * 2.5, 0.0, 1.0)
        wd = 1.0 - wb

        b_im = q_rgba.copy()
        d_im = q_rgba.copy()
        b_im[..., 3] = np.round(q_rgba[..., 3].astype(np.float32) * wb).astype(np.uint8)
        d_im[..., 3] = np.round(q_rgba[..., 3].astype(np.float32) * wd).astype(np.uint8)
        bryan_raw[qn] = keep_significant_components(b_im, 500)
        demon_raw[qn] = d_im
    return bryan_raw, demon_raw


def draw_antenna_on_box(b_rgba, mode):
    """Draws ONE gleaming metallic telescopic antenna right on Bryan's held duct-tape Demon Detector box."""
    pil = Image.fromarray(b_rgba.copy(), "RGBA")
    arr = np.array(pil)
    a = arr[..., 3] > 140
    r, g, b = arr[..., 0].astype(np.float32), arr[..., 1].astype(np.float32), arr[..., 2].astype(np.float32)
    dr = ImageDraw.Draw(pil)

    if mode in ("front", "fl45"):
        green_led = a & (g > 195) & (g - r > 50) & (np.arange(512)[:, None] > 140) & (np.arange(512)[:, None] < 320)
        blue_led = a & (b > 195) & (b - r > 70) & (np.arange(512)[:, None] > 140) & (np.arange(512)[:, None] < 320)
        ys_g, xs_g = np.nonzero(green_led)
        ys_b, xs_b = np.nonzero(blue_led)
        span = abs(float(xs_b.mean()) - float(xs_g.mean()))
        bx = int(round(min(xs_g.mean(), xs_b.mean()) - span * 1.15))
        by = int(round(min(ys_g.mean(), ys_b.mean()) - 16))
        tx, ty = bx - 3, by - 88
    elif mode == "profR":
        # Outstretched hands & box on the right side (x > 375, y = 185..265)
        ys, xs = np.nonzero(a[185:265, 375:475])
        bx = 375 + int(np.percentile(xs, 72))
        by = 185 + int(np.min(ys)) + 4
        tx, ty = bx + 6, by - 86
    elif mode == "bl135":
        # Peeking box on far left (x = 40..105, y = 175..245)
        ys, xs = np.nonzero(a[175:245, 40:108])
        bx = 40 + int(np.percentile(xs, 32))
        by = 175 + int(np.min(ys)) + 4
        tx, ty = bx - 5, by - 80
    else:
        return b_rgba

    dr.line([(bx, by), (tx, ty)], fill=(102, 110, 124, 255), width=3)
    dr.line([(bx, by), (tx, ty)], fill=(238, 244, 255, 255), width=1)
    dr.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(248, 252, 255, 255))
    return np.array(pil)


def build_bryan_180_back_clean(b_front, b_bl135):
    """Builds a rock-solid, 100% seamless 180° dead-rear view of Tinfoil-Hat Bryan
    using b_front's flipped upright head-to-toe silhouette so neck, shoulders, waist, and legs align with zero gaps:
      - Crisp pointed silver tinfoil cone hat + lush dark-brown rear hair & neck
      - Rear rainbow unicorn tie-dye t-shirt texture mapped cleanly inside torso/sleeves (no front detector box or waist flare)
      - Dark-indigo rear jeans + Vans sneakers with white heel tabs
      - Gleaming Demon Detector antenna rising cleanly from behind his left shoulder
    """
    base = np.fliplr(b_front.copy())
    H, W = base.shape[:2]
    a_orig = base[..., 3].copy()
    fg = a_orig > 25
    _, xs_all = np.nonzero(fg)
    mid = int(round(np.median(xs_all)))
    yg, xg = np.mgrid[0:H, 0:W]

    out = base.astype(np.float32)

    # 1. Rear Jeans & Sneakers (y >= 256): tone front yellow laces to dark canvas + crisp white heel tab
    shoe_zone = (yg >= 402) & fg
    yellow_lace = shoe_zone & (out[..., 0] > 125) & (out[..., 1] > 105) & (out[..., 2] < 85)
    out[yellow_lace, 0] = 30.0
    out[yellow_lace, 1] = 32.0
    out[yellow_lace, 2] = 38.0
    jeans_zone = (yg >= 254) & (yg < 402) & fg
    out[jeans_zone, :3] *= 0.88

    # 2. Rear Rainbow Unicorn Shirt Texture mapped seamlessly onto torso & sleeves (y = 114..266)
    b3_pil = Image.fromarray(b_bl135, "RGBA").rotate(-8.0, resample=Image.BICUBIC, center=(155, 195))
    b3_r = np.array(b3_pil)
    # Crop rich central rainbow unicorn tie-dye back panel from b3_r
    back_tex_crop = b3_r[118:256, 114:210].copy()
    # Fill any tiny transparent corner pixels inside back_tex_crop by nearest color before resizing
    bt_a = back_tex_crop[..., 3] > 120
    if not np.all(bt_a):
        _, idx_nd = ndimage.distance_transform_edt(~bt_a, return_indices=True)
        for c in range(3):
            ch = back_tex_crop[..., c]
            ch[~bt_a] = ch[tuple(idx_nd[:, ~bt_a])]
        back_tex_crop[..., 3] = 255

    # Find torso bounding box on `base` (y = 114..266)
    torso_mask = (yg >= 114) & (yg <= 268) & fg
    tys, txs = np.nonzero(torso_mask)
    tx0, tx1 = int(txs.min()), int(txs.max()) + 1
    ty0, ty1 = 114, 268
    tw, th = tx1 - tx0, ty1 - ty0

    # Resize back unicorn shirt texture to cover torso width & height, with natural cylindrical back shading
    tex_resized = np.array(
        Image.fromarray(back_tex_crop[..., :3], "RGB").resize((tw, th), Image.LANCZOS),
        dtype=np.float32,
    )
    # Cylindrical shading so outer elbows/sides darken naturally & sleeves blend
    rel_x = (np.arange(tw, dtype=np.float32)[None, :] - tw * 0.5) / (tw * 0.5)
    rel_y = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
    cyl_shade = np.clip(1.04 - 0.24 * (rel_x ** 2) - 0.08 * (rel_y ** 2), 0.72, 1.05)[..., None]
    tex_shaded = np.clip(tex_resized * cyl_shade, 0, 255)

    # Keep bare outer forearms/elbows slightly outside sleeves (abs(rel_x) > 0.68 & y in 172..232),
    # while replacing 100% of the front chest, hands, and detector box inside the torso with the rear unicorn tee!
    sub_out = out[ty0:ty1, tx0:tx1, :3]
    sub_fg = fg[ty0:ty1, tx0:tx1]
    is_outer_arm = (np.abs(rel_x) > 0.70) & (rel_y > 0.36) & (rel_y < 0.78)
    # Smooth blend weight between rear shirt fabric and outer bare elbows
    w_shirt = cv2.GaussianBlur((~is_outer_arm).astype(np.float32), (11, 11), 3.0)[..., None]
    # Also tuck in the bottom-center detector bulge slightly so rear t-shirt hem curves naturally over waist
    sub_out[sub_fg] = (sub_out * (1.0 - w_shirt) + tex_shaded * w_shirt)[sub_fg]
    out[ty0:ty1, tx0:tx1, :3] = sub_out

    # 3. Seamless Neck + Lush Dark-Brown Back of Hair under the Crisp Silver Tinfoil Hat (y = 66..124)
    # Keep silver tinfoil cone hat (bright metallic pixels above y=74) 100% intact!
    hat_bright = (yg < 78) & ((out[..., 0] + out[..., 1] + out[..., 2]) > 340.0) & fg
    # Paint neck skin at y = 100..124 inside fg so zero gap ever exists between head and collar
    neck_zone = (yg >= 98) & (yg <= 122) & fg & (~hat_bright)
    out[neck_zone, 0] = 162.0
    out[neck_zone, 1] = 118.0
    out[neck_zone, 2] = 94.0

    # Paint full dark-brown rear hair dome over face/beard area (y = 66..108) inside fg (plus slight fuller hair roundness)
    pil_res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    # Preserve full tinfoil hat cone (all fg pixels above y=66 plus bright silver brim folds down to y=76)
    hat_layer = np.zeros_like(base)
    rgb_sum = base[..., 0].astype(np.int32) + base[..., 1].astype(np.int32) + base[..., 2].astype(np.int32)
    rgb_sat = np.maximum(base[..., 0], np.maximum(base[..., 1], base[..., 2])).astype(np.int32) - np.minimum(base[..., 0], np.minimum(base[..., 1], base[..., 2])).astype(np.int32)
    hat_take = fg & ((yg < 66) | ((yg < 78) & (rgb_sum > 220) & (rgb_sat < 42)))
    hat_layer[hat_take] = base[hat_take]

    hd = ImageDraw.Draw(pil_res)
    # Smooth collar crew-neck rib at top of shirt
    hd.arc([mid - 24, 108, mid + 24, 126], start=10, end=170, fill=(78, 52, 135, 255), width=4)
    # Back-of-head dark brown hair dome (covers front face completely from y=64..110)
    hd.ellipse([mid - 29, 64, mid + 29, 111], fill=(38, 27, 20, 255))
    hd.ellipse([mid - 24, 68, mid + 24, 104], fill=(52, 37, 27, 255))
    for dx in range(-18, 20, 4):
        hd.arc([mid + dx - 6, 68, mid + dx + 6, 106], start=70, end=290, fill=(28, 19, 14, 200), width=2)

    # Composite crisp tinfoil hat right back on top of hair brim
    pil_res.alpha_composite(Image.fromarray(hat_layer, "RGBA"), (0, 0))

    # 4. Telescopic Demon Detector antenna rising cleanly from behind left shoulder (rooted inside shoulder silhouette!)
    antenna_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(antenna_layer)
    sx, sy = mid - 34, 134
    tx, ty = mid - 40, 52
    ad.line([(sx, sy), (tx, ty)], fill=(104, 112, 126, 255), width=3)
    ad.line([(sx, sy), (tx, ty)], fill=(238, 244, 255, 255), width=1)
    ad.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(248, 252, 255, 255))
    # Draw antenna BEHIND Bryan so it emerges naturally from behind his shoulder!
    final_pil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    final_pil.alpha_composite(antenna_layer, (0, 0))
    final_pil.alpha_composite(pil_res, (0, 0))
    return np.array(final_pil)


def build_planted_idle_bryan(b_run_arr, angle_deg):
    """Creates a natural 2-feet-planted paranoid-scan stance from the sprint cutout across all 8 angles."""
    H, W = b_run_arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    arr = b_run_arr.copy()
    a = arr[..., 3] > 30

    if angle_deg in (270, 90):
        # Work in right-facing space (270°), flip at end if 90°
        work = arr.copy() if angle_deg == 270 else np.fliplr(arr.copy())
        wa = work[..., 3] > 30
        hx = int(round(np.median(np.nonzero(wa[245:275, :])[1])))
        # Erase ONLY the horizontally kicked-back rear shin/thigh below y=298 (preserving 100% of hip & buttock under shirt!)
        front_only = work.copy()
        kicked = (xg < (hx - 10)) & (yg > 298)
        front_only[kicked, 3] = 0
        front_only = keep_significant_components(front_only, 500)

        leg_crop = front_only[278:485, max(0, hx - 22):min(W, hx + 62)].copy().astype(np.float32)
        leg_crop[..., :3] *= 0.80
        leg_crop[:10, :, 3] *= np.linspace(0.0, 1.0, 10, dtype=np.float32)[:, None]
        rear_leg_pil = Image.fromarray(np.clip(leg_crop, 0, 255).astype(np.uint8), "RGBA")

        pil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pil.alpha_composite(rear_leg_pil, (max(0, hx - 22) - 16, 274))
        pil.alpha_composite(Image.fromarray(front_only, "RGBA"), (0, 0))
        res = np.array(pil)
        return res if angle_deg == 270 else np.fliplr(res)

    elif angle_deg in (135, 225):
        work = arr.copy() if angle_deg == 135 else np.fliplr(arr.copy())
        wa = work[..., 3] > 30
        hx = int(round(np.median(np.nonzero(wa[245:275, :])[1])))
        front_only = work.copy()
        kicked = (xg > (hx + 16)) & (yg > 312)
        front_only[kicked, 3] = 0
        front_only = keep_significant_components(front_only, 500)

        leg_crop = front_only[280:485, max(0, hx - 52):min(W, hx + 22)].copy().astype(np.float32)
        leg_crop[..., :3] *= 0.84
        leg_crop[:10, :, 3] *= np.linspace(0.0, 1.0, 10, dtype=np.float32)[:, None]
        rear_leg_pil = Image.fromarray(np.clip(leg_crop, 0, 255).astype(np.uint8), "RGBA")

        pil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pil.alpha_composite(rear_leg_pil, (max(0, hx - 52) + 20, 276))
        pil.alpha_composite(Image.fromarray(front_only, "RGBA"), (0, 0))
        res = np.array(pil)
        return res if angle_deg == 135 else np.fliplr(res)

    elif angle_deg in (45, 315):
        work = arr.copy() if angle_deg == 45 else np.fliplr(arr.copy())
        wa = work[..., 3] > 30
        hx = int(round(np.median(np.nonzero(wa[248:278, :])[1])))
        front_only = work.copy()
        kicked = (xg > (hx + 10)) & (yg > 312)
        front_only[kicked, 3] = 0
        front_only = keep_significant_components(front_only, 500)

        leg_crop = front_only[280:485, max(0, hx - 46):min(W, hx + 18)].copy().astype(np.float32)
        leg_crop[..., :3] *= 0.84
        leg_crop[:10, :, 3] *= np.linspace(0.0, 1.0, 10, dtype=np.float32)[:, None]
        rear_leg_pil = Image.fromarray(np.clip(leg_crop, 0, 255).astype(np.uint8), "RGBA")

        pil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pil.alpha_composite(rear_leg_pil, (max(0, hx - 46) + 24, 276))
        pil.alpha_composite(Image.fromarray(front_only, "RGBA"), (0, 0))
        res = np.array(pil)
        return res if angle_deg == 45 else np.fliplr(res)

    else:
        # 0° Front and 180° Back: stretch the raised leg smoothly down so both sneakers rest near ground level
        _, xs = np.nonzero(a)
        cx = int(np.median(xs))
        yl = np.max(np.nonzero(a[:, :cx])[0]) if np.any(a[:, :cx]) else 0
        yr = np.max(np.nonzero(a[:, cx:])[0]) if np.any(a[:, cx:]) else 0
        if abs(yl - yr) > 14:
            hip_y = 272
            x_slice = slice(cx, W) if yr < yl else slice(0, cx)
            stretch = min(1.30, max(1.0, ((max(yl, yr) - hip_y) / max(20.0, min(yl, yr) - hip_y)) * 0.97))
            sub = arr[hip_y:, x_slice].copy()
            sh_new = min(H - hip_y, int(round(sub.shape[0] * stretch)))
            sub_p = Image.fromarray(sub, "RGBA").resize((sub.shape[1], sh_new), Image.LANCZOS)
            out = arr.copy()
            out[hip_y:, x_slice] = 0
            pil = Image.fromarray(out, "RGBA")
            pil.alpha_composite(sub_p, (x_slice.start, hip_y))
            return np.array(pil)
        return arr


def complete_crimson_demons(demon_raw):
    """Builds 100% speck-free, shin-connected, 2-armed Crimson Horned Demon rigs across all 8 angles."""
    d_q0 = keep_significant_components(demon_raw["q0_front"], 500)
    d_q1 = keep_significant_components(demon_raw["q1_fl45"], 500)
    d_q2 = demon_raw["q2_profR"].copy()
    d_q3 = keep_significant_components(demon_raw["q3_bl135"], 650)

    # Erase the tiny orange-red hem sliver on left of d_q1 (x < 268, y > 245) before mirroring!
    yg, xg = np.mgrid[0:512, 0:512]
    d_q1[(xg < 268) & (yg > 245), 3] = 0
    d_q1 = keep_significant_components(d_q1, 600)

    a1 = d_q1[..., 3] > 40
    _, hx = np.nonzero(a1[:135, :])
    cx1 = int(round(np.median(hx)))

    front_d = d_q1.copy()
    r_half = d_q1[:265, cx1:min(512, cx1 + 175)].copy()
    l_arm = np.fliplr(r_half)
    x_start = max(0, cx1 - l_arm.shape[1])
    dst = front_d[:265, x_start:cx1]
    src_crop = l_arm[:, l_arm.shape[1] - (cx1 - x_start):]
    take = (dst[..., 3] < 40) & (src_crop[..., 3] > 20)
    dst[take] = src_crop[take]
    front_d[:265, x_start:cx1] = dst

    # 45° Demon: raised menacing claw from d_q0!
    a0 = d_q0[..., 3] > 40
    _, hx0 = np.nonzero(a0[:135, :])
    cx0 = int(round(np.median(hx0)))
    fl45_d = front_d.copy()
    arm_q0 = d_q0[:225, cx0:].copy()
    w_copy = min(arm_q0.shape[1], 512 - cx1)
    fl45_d[:225, cx1:cx1 + w_copy] = arm_q0[:, :w_copy]

    # Profile Demon (d_q2): connect forward right bent knee directly down to the separated red foot right below it!
    m2 = d_q2[..., 3] > 20
    lbl2, n2 = ndimage.label(m2)
    profR_d = d_q2.copy()
    foot_cx, foot_top_y = None, None
    for cid in range(1, n2 + 1):
        comp = lbl2 == cid
        ys_c, xs_c = np.nonzero(comp)
        if len(xs_c) < 160 or (np.mean(ys_c) < 350 and len(xs_c) < 900):
            profR_d[comp, 3] = 0
        elif len(xs_c) < 2500 and np.mean(ys_c) > 410:
            foot_cx = int(round(np.percentile(xs_c, 32)))
            foot_top_y = int(np.min(ys_c)) + 5

    if foot_cx is not None:
        # Look strictly in the vertical column above foot_cx for the forward bent knee!
        knee_col = (profR_d[..., 3] > 60) & (np.abs(xg - foot_cx) < 42) & (yg > 280) & (yg < foot_top_y - 8)
        kys, kxs = np.nonzero(knee_col)
        if len(kxs) > 10:
            ymax_k = int(np.max(kys))
            knee_cx = int(round(np.median(kxs[kys >= ymax_k - 12])))
            pil_p2 = Image.fromarray(profR_d, "RGBA")
            dr2 = ImageDraw.Draw(pil_p2)
            mid_y = int(round(ymax_k * 0.35 + foot_top_y * 0.65))
            # Torn dark pant shin down to mid_y, then muscular crimson ankle into foot_top_y
            dr2.polygon([
                (knee_cx - 15, ymax_k - 10),
                (knee_cx + 14, ymax_k - 10),
                (foot_cx + 11, mid_y + 4),
                (foot_cx - 10, mid_y + 4),
            ], fill=(24, 24, 27, 255))
            dr2.polygon([
                (foot_cx - 9, mid_y),
                (foot_cx + 10, mid_y),
                (foot_cx + 9, foot_top_y + 3),
                (foot_cx - 8, foot_top_y + 3),
            ], fill=(142, 22, 28, 255))
            # Subtle highlight down front of shin
            dr2.line([(knee_cx + 4, ymax_k - 6), (foot_cx + 3, mid_y)], fill=(42, 42, 48, 255), width=3)
            dr2.line([(foot_cx + 3, mid_y + 2), (foot_cx + 3, foot_top_y + 2)], fill=(182, 34, 40, 255), width=3)
            profR_d = np.array(pil_p2)

    # 135° Demon (d_q3): copy the real shaded right crimson foot onto the left ankle seamlessly!
    bl135_d = d_q3.copy()
    # Right foot in d_q3 is at bottom-right (x > 400, y > 435)
    rfoot_mask = (bl135_d[..., 3] > 50) & (xg > 395) & (yg > 432)
    ry_s, rx_s = np.nonzero(rfoot_mask)
    left_leg_a = (bl135_d[..., 3] > 80) & (xg < 370) & (yg > 360)
    lys, lxs = np.nonzero(left_leg_a)
    if len(lxs) > 10 and len(rx_s) > 20:
        ly_bot = int(np.max(lys))
        lx_bot = int(round(np.median(lxs[lys >= ly_bot - 10])))
        rf_crop = bl135_d[int(ry_s.min()):int(ry_s.max()) + 1, int(rx_s.min()):int(rx_s.max()) + 1].copy()
        # Flip horizontally so toes point left-forward matching the left leg!
        lf_pil = Image.fromarray(np.fliplr(rf_crop), "RGBA")
        pil_p3 = Image.fromarray(bl135_d, "RGBA")
        # Overlap 10px with the bottom of the left crimson calf so there is zero gap!
        pil_p3.alpha_composite(lf_pil, (lx_bot - lf_pil.width // 2 - 4, ly_bot - 10))
        bl135_d = np.array(pil_p3)

    # 180° Rear Demon: smooth shaded crimson back & occiput (zero eye dots, fangs, or front abs; crisp black horns!)
    back_d = front_d.copy()
    rf = back_d.astype(np.float32)
    lum = 0.299 * rf[..., 0] + 0.587 * rf[..., 1] + 0.114 * rf[..., 2]
    # Preserve outer black horns (abs(x - cx1) > 18 & y < 95 & dark), smooth ALL face pixels + red torso into muscular back!
    is_horn = (yg < 96) & (np.abs(xg - cx1) > 18) & (lum < 62.0) & (rf[..., 3] > 80)
    is_head_face = (yg >= 54) & (yg < 138) & (np.abs(xg - cx1) < 36) & (rf[..., 3] > 100) & (~is_horn)
    is_torso_skin = (yg >= 115) & (yg < 256) & (np.abs(xg - cx1) < 62) & (rf[..., 3] > 100) & ((rf[..., 0] - rf[..., 1]) > 22.0)
    replace_back = is_head_face | is_torso_skin

    # Build clean crimson skin base before blurring so dark eye/mouth pixels don't leave dark smudges
    clean_crimson = rf[..., :3].copy()
    dark_facial = is_head_face & ((clean_crimson[..., 0] - clean_crimson[..., 1]) < 45.0)
    clean_crimson[dark_facial, 0] = 172.0
    clean_crimson[dark_facial, 1] = 28.0
    clean_crimson[dark_facial, 2] = 34.0
    blurred_rgb = cv2.GaussianBlur(clean_crimson, (25, 25), 8.0)

    spine_shade = 1.0 - 0.22 * np.exp(-((xg - cx1) / 7.5) ** 2) * ((yg > 108) & (yg < 252))
    for ch_i, base_mul in enumerate((0.92, 0.72, 0.75)):
        rf[replace_back, ch_i] = np.clip(blurred_rgb[replace_back, ch_i] * base_mul * spine_shade[replace_back], 0, 255)
    back_d = rf.astype(np.uint8)

    return {
        0: front_d,
        45: fl45_d,
        90: np.fliplr(profR_d),
        135: bl135_d,
        180: back_d,
        225: np.fliplr(bl135_d),
        270: profR_d,
        315: np.fliplr(fl45_d),
    }


def complete_v2_trio_demons():
    """Polishes the 3 Video 2 Dungeon Demons (Winged Red, Cloaked Reaper, Grey Ram-Demon) onto clean 512x512 RGBA cells."""
    w_red = np.array(Image.open(os.path.join(LAYERS_DIR, "demon_winged_red.png")))
    reaper = np.array(Image.open(os.path.join(LAYERS_DIR, "demon_reaper.png")))
    ram = np.array(Image.open(os.path.join(LAYERS_DIR, "demon_grey_ram.png")))

    def fit_512(rgba, symmetric_mirror=False, wispy_bottom=False):
        a = rgba[..., 3] > 35
        ys, xs = np.nonzero(a)
        crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1].copy()
        if symmetric_mirror:
            ha = crop[:int(crop.shape[0] * 0.25), :, 3] > 60
            hxs = np.nonzero(ha)[1]
            cx = int(np.percentile(hxs, 68)) if len(hxs) > 10 else int(crop.shape[1] * 0.72)
            left_part = crop[:, :cx]
            sym = np.zeros((crop.shape[0], cx * 2, 4), dtype=np.uint8)
            sym[:, :cx] = left_part
            sym[:, cx:] = np.fliplr(left_part)
            crop = sym
        pil_c = Image.fromarray(crop, "RGBA")
        sc = min(460.0 / pil_c.width, 450.0 / pil_c.height)
        rsz = pil_c.resize((max(2, int(pil_c.width * sc)), max(2, int(pil_c.height * sc))), Image.LANCZOS)
        if wispy_bottom:
            arr_r = np.array(rsz, dtype=np.float32)
            H_r = arr_r.shape[0]
            fade = np.clip((H_r - np.arange(H_r)[:, None]) / (H_r * 0.22), 0.0, 1.0)
            arr_r[..., 3] *= fade
            rsz = Image.fromarray(arr_r.astype(np.uint8), "RGBA")
        cell = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        cell.paste(rsz, ((512 - rsz.width) // 2, 490 - rsz.height), rsz)
        return np.array(cell)

    return {
        "winged_red": fit_512(w_red, symmetric_mirror=True),
        "reaper": fit_512(reaper, wispy_bottom=True),
        "grey_ram": fit_512(ram),
    }


def main():
    bryan_raw, demon_raw = clean_split_pair_without_drawn_antenna()

    b0 = draw_antenna_on_box(bryan_raw["q0_front"], "front")
    b1 = draw_antenna_on_box(bryan_raw["q1_fl45"], "fl45")
    b2 = draw_antenna_on_box(bryan_raw["q2_profR"], "profR")
    b3 = draw_antenna_on_box(bryan_raw["q3_bl135"], "bl135")
    b4 = build_bryan_180_back_clean(bryan_raw["q0_front"], bryan_raw["q3_bl135"])

    bryan_run_8 = {
        0: b0,
        45: b1,
        90: np.fliplr(b2),
        135: b3,
        180: b4,
        225: np.fliplr(b3),
        270: b2,
        315: np.fliplr(b1),
    }
    bryan_idle_8 = {ang: build_planted_idle_bryan(im, ang) for ang, im in bryan_run_8.items()}
    crimson_8 = complete_crimson_demons(demon_raw)
    trio = complete_v2_trio_demons()

    for idx, ang in enumerate((0, 45, 90, 135, 180, 225, 270, 315)):
        Image.fromarray(bryan_run_8[ang]).save(os.path.join(RIGS_DIR, f"bryan_run_d{idx}.png"))
        Image.fromarray(bryan_idle_8[ang]).save(os.path.join(RIGS_DIR, f"bryan_idle_d{idx}.png"))
        Image.fromarray(crimson_8[ang]).save(os.path.join(RIGS_DIR, f"crimson_d{idx}.png"))
    for k, im in trio.items():
        Image.fromarray(im).save(os.path.join(RIGS_DIR, f"trio_{k}.png"))

    # Visual audit sheet (3 rows x 8 cols + Trio)
    cw, ch = 160, 190
    W_g, H_g = cw * 8, ch * 3
    yy, xx = np.mgrid[0:H_g, 0:W_g]
    chk = np.where(((xx // 14 + yy // 14) % 2) == 0, 48, 30)[..., None].astype(np.uint8)
    grid = Image.fromarray(np.repeat(chk, 3, axis=-1), "RGB")

    rows = [bryan_idle_8, bryan_run_8, crimson_8]
    angs = (0, 45, 90, 135, 180, 225, 270, 315)
    for r_i, r_dict in enumerate(rows):
        for c_i, ang in enumerate(angs):
            im = Image.fromarray(r_dict[ang], "RGBA")
            ys, xs = np.nonzero(r_dict[ang][..., 3] > 20)
            crop = im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
            sc = min((cw - 12) / crop.width, (ch - 14) / crop.height)
            rsz = crop.resize((max(2, int(crop.width * sc)), max(2, int(crop.height * sc))), Image.LANCZOS)
            gx = c_i * cw + (cw - rsz.width) // 2
            gy = r_i * ch + (ch - 6 - rsz.height)
            sub = grid.crop((gx, gy, gx + rsz.width, gy + rsz.height)).convert("RGBA")
            sub.alpha_composite(rsz)
            grid.paste(sub.convert("RGB"), (gx, gy))

    audit_p = os.path.join(DBG_DIR, "master_rigs_8dir_v2_audit.jpg")
    grid.save(audit_p, quality=92)
    print("Saved v2 clean 8-direction master rigs audit:", audit_p)


if __name__ == "__main__":
    main()
