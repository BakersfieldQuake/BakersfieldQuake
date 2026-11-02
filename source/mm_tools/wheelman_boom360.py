"""360° Multi-Angle Part Extractor, X-Ray Skeleton Generator, Photorealistic VFX Plate Loader,
and 4-Tier Escalating 3D Explosion & Gibs Simulation Engine for BakersfieldQuake Wheelman.

Tiers (each progressively bigger, longer, and crazier — all 100% 360° + Above/Below):
  Tier 1 (84f)  : Classic Chrome-Core Overload, Fireball, Flying Wheels/Bar (+ Mid-Air Pop) & 24 Gibs
  Tier 2 (108f) : Napalm Cluster Rampage — 360° Flaming Burnout, Triple Napalm Blast, Rocket Bar & 52 Gibs
  Tier 3 (132f) : Tesla X-Ray Plasma Tornado — Levitating X-Ray Skeleton, Singularity, Plasma Supernova,
                  3D Helical Gib/Wheel Cyclone & Sky-to-Ground Thunderbolt Slam (84 Gibs)
  Tier 4 (168f) : THERMONUCLEAR CATACLYSM — 2.0x Balloon Bloat, Orbital Sky-Beam, Whiteout, Towering
                  Thermonuclear Mushroom Cloud, 12-Blast Carpet Bombing & 140 Meteor Gibs + Final Head Pop!
"""
import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from scipy import ndimage

import wheelman_fx as fx


def _paint_ragged_stump(part_arr, cx_s, cy_s, rx_s, ry_s, seed=1):
    rng = np.random.default_rng(seed)
    ph, pw = part_arr.shape[:2]
    if ph < 4 or pw < 4:
        return part_arr
    pyg, pxg = np.mgrid[0:ph, 0:pw].astype(np.float32)
    ang = np.arctan2(pyg - cy_s, pxg - cx_s)
    jag = 1.0 + 0.18 * np.sin(5.0 * ang + rng.uniform(0, 6)) + 0.12 * np.cos(9.0 * ang)
    r = np.sqrt(((pxg - cx_s) / max(rx_s, 1.0)) ** 2 + ((pyg - cy_s) / max(ry_s, 1.0)) ** 2) / jag
    stump = r <= 1.0
    shade = np.clip(1.15 - 0.65 * r, 0.35, 1.0)
    part_arr[stump, 0] = np.clip(162.0 * shade[stump], 0, 255).astype(np.uint8)
    part_arr[stump, 1] = np.clip(18.0 * shade[stump], 0, 255).astype(np.uint8)
    part_arr[stump, 2] = np.clip(22.0 * shade[stump], 0, 255).astype(np.uint8)
    part_arr[stump, 3] = 255
    bone = r <= 0.36
    part_arr[bone, :3] = [235, 226, 210]
    return part_arr


def _crop_nonempty(rgba_arr, pad=2):
    rgba_arr = np.asarray(rgba_arr)
    ys, xs = np.nonzero(rgba_arr[..., 3] > 16)
    if len(xs) == 0:
        return Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    H, W = rgba_arr.shape[:2]
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(W, int(xs.max()) + pad + 1)
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(H, int(ys.max()) + pad + 1)
    return Image.fromarray(rgba_arr[y0:y1, x0:x1].copy(), "RGBA")


def extract_all_360_parts(norm_views, scream_grid, vert_norm):
    """Extracts clean 8-angle (d=0..7) + overhead/underneath rigid-body sprites:
      - heads_8[0..7]   : 8-angle severed screaming head with bloody neck stump
      - wheels_8[0..7]  : 8-angle clean skin-repaired rubber tire + white steel rim (0=edge, 1=45°, 2=full dish...)
      - bars_8[0..7]    : 8-angle steel axle bar + gleaming central chrome cylinder + fluted cap
      - llegs_8[0..7]   : 8-angle bare left leg + foot
      - rlegs_8[0..7]   : 8-angle bare right leg + foot
      - xrays_8[0..7]   : 8-angle glowing high-voltage X-ray skeleton matched to each Wheelman silhouette
      - gibs[0..23]     : 24 glossy 3D-shaded Quake meat chunks, ribcages, femurs & organs
      - shrap_cap, shrap_nut : Fluted chrome cap & steel hex nut shrapnel
    """
    heads_8 = []
    wheels_8 = []
    bars_8 = []
    llegs_8 = []
    rlegs_8 = []
    xrays_8 = []

    # 1) Extract 8-angle Severed Screaming Heads
    head_boxes = {
        0: (118, 52, 184, 126, 33.0, 66.0),
        1: (196, 42, 266, 116, 36.0, 66.0),
        2: (236, 56, 306, 132, 38.0, 68.0),
        3: (208, 38, 280, 114, 36.0, 68.0),
        4: (124, 66, 196, 144, 36.0, 70.0),
        5: (40,  38, 112, 114, 36.0, 68.0),
        6: (14,  56, 84,  132, 32.0, 68.0),
        7: (54,  42, 124, 116, 34.0, 66.0),
    }
    for d in range(8):
        s_arr = np.array(scream_grid[d][3])  # Wide-open peak scream frame (zero sound-wave overlap inside head)
        # Re-render without sound waves so head cutout has zero yellow arc pixels
        base_im, c_specs = norm_views[d]
        clean_s = np.array(fx.apply_scream_face_and_body(base_im, d, 0.25, c_specs, intensity=1.14, sound_waves=False))
        x0, y0, x1, y1, sx, sy = head_boxes[d]
        hc = clean_s[y0:y1, x0:x1].copy()
        hy, hx = np.mgrid[0:hc.shape[0], 0:hc.shape[1]].astype(np.float32)
        neck_cut = hy > (sy + 3.0 * np.sin(hx * 0.42 + d))
        hc[neck_cut, 3] = 0
        hc = _paint_ragged_stump(hc, sx, sy - 2.0, 10.5, 4.5, seed=10 + d)
        heads_8.append(_crop_nonempty(hc, pad=2))

    # 2) Extract 8-angle Clean Skin-Free Wheels (repairing arm/hand grip on d=1,2,3,5,6,7!)
    for d in range(8):
        base_im, c_specs = norm_views[d]
        arr = np.array(base_im).copy()
        H, W = arr.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
        # Pick the primary foreground wheel for this angle so every angle of wheel spin looks authentic:
        # d=0: edge-on tire, d=1: 45° deep-dish wheel, d=2: full circular white dish profile wheel,
        # d=3: 135° wheel, d=4: rear edge-on tire, d=5..7: mirrored counterparts
        ws = max(c_specs, key=lambda w: w["rx"] * w["ry"])
        wcx, wcy, wrx, wry = ws["cx"], ws["cy"], ws["rx"], ws["ry"]
        ang = math.radians(ws["ang"])
        ca, sa = math.cos(ang), math.sin(ang)
        du = ((xg - wcx) * ca + (yg - wcy) * sa) / max(wrx, 1.0)
        dv = (-(xg - wcx) * sa + (yg - wcy) * ca) / max(wry, 1.0)
        r_ell = np.sqrt(du * du + dv * dv)
        w_mask = (r_ell <= 1.04) & (arr[..., 3] > 60)

        # Repair any bare hand/arm gripping the wheel hub by mirroring from opposite clean wheel sector!
        rf = arr[..., :3].astype(np.float32)
        is_skin = w_mask & ((rf[..., 0] - rf[..., 2]) > 15.0) & ((rf[..., 0] - rf[..., 1]) > 7.0) & (rf[..., 0] > 80.0)
        if np.any(is_skin):
            skin_dil = ndimage.binary_dilation(is_skin, iterations=3) & w_mask
            opp_x = np.clip(np.round(2.0 * wcx - xg), 0, W - 1).astype(np.int32)
            opp_y = np.clip(np.round(2.0 * wcy - yg), 0, H - 1).astype(np.int32)
            arr[skin_dil, :3] = arr[opp_y, opp_x][skin_dil, :3]
            # Any remaining skin outside rim becomes transparent
            still_skin = skin_dil & ((arr[..., 0].astype(np.float32) - arr[..., 2].astype(np.float32)) > 16.0)
            arr[still_skin, 3] = 0

        arr[~w_mask, 3] = 0
        wheels_8.append(_crop_nonempty(arr, pad=2))

    # 3) Extract/Build 8-angle Steel Axle Bar + Gleaming Central Chrome Cylinder + Fluted Cap!
    arr_d0 = np.array(norm_views[0][0])
    cyl_d0 = arr_d0[212:266, 150:196].copy()
    is_metal0 = ((cyl_d0[..., 0].astype(np.float32) - cyl_d0[..., 2].astype(np.float32)) < 16.0) & (cyl_d0[..., 3] > 80)
    cyl_d0[~is_metal0, 3] = 0
    cyl_d0_im = Image.fromarray(cyl_d0, "RGBA")

    # Also extract authentic side-profile gleaming chrome cylinder from d=2 (pointing left: x=4..102, y=214..252)
    arr_d2 = np.array(norm_views[2][0])
    cyl_d2 = arr_d2[212:256, 2:102].copy()
    is_metal2 = ((cyl_d2[..., 0].astype(np.float32) - cyl_d2[..., 2].astype(np.float32)) < 18.0) & (cyl_d2[..., 3] > 70)
    cyl_d2[~is_metal2, 3] = 0
    cyl_d2_im = _crop_nonempty(cyl_d2, pad=1)

    for d in range(8):
        th = math.radians(d * 45.0)
        # Apparent axle span = |cos(th)|, forward chrome projection = -sin(th)
        span_ax = int(round(28 + 116 * abs(math.cos(th))))
        bw, bh = max(96, span_ax + 36), 62
        bim = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        bdr = ImageDraw.Draw(bim)
        cx_b, cy_b = bw // 2, bh // 2
        if d in (2, 6):
            # Profile view: chrome cylinder sticks straight out horizontally (-X for d=2, +X for d=6) + steel hub!
            c_prof = cyl_d2_im if d == 2 else ImageOps.mirror(cyl_d2_im)
            cw_p = min(bw - 24, c_prof.width)
            c_prof_r = c_prof.resize((cw_p, c_prof.height), Image.BICUBIC)
            px_c = (cx_b - cw_p + 8) if d == 2 else (cx_b - 8)
            bim.alpha_composite(c_prof_r, (px_c, cy_b - c_prof_r.height // 2))
            bdr.ellipse([cx_b - 11, cy_b - 11, cx_b + 11, cy_b + 11], fill=(224, 230, 238, 255), outline=(60, 66, 75, 255), width=2)
            bdr.regular_polygon((cx_b, cy_b, 6), n_sides=6, fill=(155, 162, 172, 255), outline=(50, 55, 64, 255))
        else:
            xL, xR = cx_b - span_ax // 2, cx_b + span_ax // 2
            # If rear view (d=3,4,5), draw foreshortened chrome cylinder BEHIND steel axle bar!
            if d in (3, 4, 5):
                c_back = cyl_d0_im.resize((34, 38), Image.BICUBIC).rotate(180 if d == 4 else (135 if d == 3 else -135), expand=True)
                bim.alpha_composite(c_back, (cx_b - c_back.width // 2, cy_b - c_back.height // 2 - 8))
            bdr.rounded_rectangle([xL, cy_b - 5, xR, cy_b + 5], radius=4, fill=(94, 100, 108, 255), outline=(40, 44, 50, 255))
            bdr.line([(xL + 3, cy_b - 2), (xR - 3, cy_b - 2)], fill=(226, 234, 244, 255), width=2)
            bdr.rectangle([xL, cy_b - 8, xL + 11, cy_b + 8], fill=(232, 236, 240, 255), outline=(98, 104, 112, 255))
            bdr.rectangle([xR - 11, cy_b - 8, xR, cy_b + 8], fill=(232, 236, 240, 255), outline=(98, 104, 112, 255))
            if d in (0, 1, 7):
                ang_c = 0 if d == 0 else (28 if d == 1 else -28)
                c_fg = cyl_d0_im.rotate(ang_c, resample=Image.BICUBIC, expand=True)
                bim.alpha_composite(c_fg, (cx_b - c_fg.width // 2 + (-8 if d == 1 else (8 if d == 7 else 2)), cy_b - 10))
        bars_8.append(_crop_nonempty(bim, pad=2))

    # 4) Extract 8-angle Bare Legs & Feet
    parts_d0 = fx._extract_d0_anatomical_and_mech_parts(norm_views[0][0], norm_views[0][1])
    for d in range(8):
        if d == 0:
            llegs_8.append(parts_d0["lleg"])
            rlegs_8.append(parts_d0["rleg"])
        elif d == 4:
            # Rear bare V-legs (top-left & top-right above wheels)
            a4 = np.array(norm_views[4][0]).copy()
            yg, xg = np.mgrid[0:a4.shape[0], 0:a4.shape[1]].astype(np.float32)
            mL = (xg < 132) & (yg < 178) & (a4[..., 3] > 50)
            mR = (xg > 188) & (yg < 178) & (a4[..., 3] > 50)
            l_a, r_a = a4.copy(), a4.copy()
            l_a[~mL, 3] = 0
            r_a[~mR, 3] = 0
            llegs_8.append(_crop_nonempty(_paint_ragged_stump(l_a[34:182, 22:136], 94, 134, 9, 7, seed=41)))
            rlegs_8.append(_crop_nonempty(_paint_ragged_stump(r_a[34:182, 184:298], 20, 134, 9, 7, seed=42)))
        elif d in (2, 6):
            ap = np.array(norm_views[d][0]).copy()
            yg, xg = np.mgrid[0:ap.shape[0], 0:ap.shape[1]].astype(np.float32)
            m_leg = ((xg < 208) if d == 2 else (xg > 112)) & (yg < 186) & (ap[..., 3] > 50)
            la = ap.copy()
            la[~m_leg, 3] = 0
            lc = np.array(_crop_nonempty(la, pad=3))
            lh, lw = lc.shape[:2]
            lc = _paint_ragged_stump(lc, lw - 12 if d == 2 else 12, lh - 10, 10, 7, seed=45 + d)
            leg_im = Image.fromarray(lc, "RGBA")
            llegs_8.append(leg_im)
            rlegs_8.append(leg_im)
        elif d in (1, 3):
            llegs_8.append(parts_d0["lleg"])
            rlegs_8.append(ImageOps.mirror(parts_d0["lleg"]))
        else:
            llegs_8.append(ImageOps.mirror(parts_d0["rleg"]))
            rlegs_8.append(parts_d0["rleg"])

    # 5) Build 8-angle High-Voltage Glowing X-Ray Skeleton Sprites (for Tiers 3 & 4!)
    for d in range(8):
        base_im, c_specs = norm_views[d]
        s_im = fx.apply_scream_face_and_body(base_im, d, 0.25, c_specs, intensity=1.15, sound_waves=False)
        xrays_8.append(_build_xray_skeleton_view(s_im, d, c_specs))

    xray_above90 = _build_xray_above_view(vert_norm["above90"])

    # 6) Build 24 Glossy 3D-Shaded Quake Meat Chunks, Ribcage Arcs, Femur Bones & Eyeballs!
    gibs_24 = list(parts_d0["gibs"])
    rng = np.random.default_rng(9001)
    for extra in range(4):
        # Curved bloody ribcage / femur bone chunks for crazy Tier 3 & 4 carnage
        im_b = Image.new("RGBA", (34, 34), (0, 0, 0, 0))
        dr_b = ImageDraw.Draw(im_b)
        if extra % 2 == 0:
            dr_b.line([(5, 27), (28, 6)], fill=(165, 18, 24, 255), width=8)
            dr_b.line([(6, 26), (27, 7)], fill=(238, 230, 212, 255), width=4)
            for ex_p, ey_p in ((5, 27), (28, 6)):
                dr_b.ellipse([ex_p - 4, ey_p - 4, ex_p + 4, ey_p + 4], fill=(242, 234, 218, 255), outline=(140, 20, 24, 255))
        else:
            for ri in range(3):
                off = ri * 5
                dr_b.arc([4 + off, 4 + off, 30 - off // 2, 29 - off // 2], start=195, end=355, fill=(236, 228, 210, 255), width=3)
            dr_b.ellipse([10, 12, 24, 25], fill=(172, 16, 22, 235))
        gibs_24.append(im_b)

    return dict(
        heads=heads_8,
        wheels=wheels_8,
        bars=bars_8,
        llegs=llegs_8,
        rlegs=rlegs_8,
        xrays=xrays_8,
        xray_above90=xray_above90,
        gibs=gibs_24,
        shrap_cap=parts_d0["shrap_cap"],
        shrap_nut=parts_d0["shrap_nut"],
    )


def _build_xray_skeleton_view(scream_im, d_idx, wheel_specs):
    """Creates an arcade/Quake high-voltage X-Ray skeleton sprite strictly fitted inside Wheelman's 320x304 silhouette."""
    arr = np.array(scream_im)
    H, W = arr.shape[:2]
    alpha = arr[..., 3]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    # Exclude rubber wheels so only his human body turns into glowing X-ray flesh + bones while wheels spark!
    wheel_m = np.zeros((H, W), dtype=bool)
    for ws in wheel_specs:
        ang = math.radians(ws["ang"])
        ca, sa = math.cos(ang), math.sin(ang)
        du = ((xg - ws["cx"]) * ca + (yg - ws["cy"]) * sa) / max(ws["rx"] + 2.0, 1.0)
        dv = (-(xg - ws["cx"]) * sa + (yg - ws["cy"]) * ca) / max(ws["ry"] + 2.0, 1.0)
        wheel_m |= (du * du + dv * dv) <= 1.02

    body_m = (alpha > 90) & (~wheel_m)
    out = arr.copy()
    # Darken flesh into translucent electric-indigo X-ray medium; invert metal/wheels with cyan rim glow
    out[body_m, 0] = 14
    out[body_m, 1] = 34
    out[body_m, 2] = 68

    skel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(skel)
    spec = fx.FACE_SPECS_320[d_idx]
    nx, ny = spec["nx"], spec["ny"]
    hx = spec.get("mx", spec.get("hx", nx))
    hy = spec.get("my", spec.get("hy", ny - 22.0)) - 12.0
    y_ax = sum(ws["cy"] for ws in wheel_specs) / len(wheel_specs)
    bone_c = (235, 252, 255, 255)
    glow_c = (56, 225, 255, 210)

    # Cranium + jaw
    dr.ellipse([hx - 15, hy - 18, hx + 15, hy + 10], fill=glow_c)
    dr.ellipse([hx - 13, hy - 16, hx + 13, hy + 8], fill=bone_c)
    if "eyes" in spec:
        for ex, ey in spec["eyes"]:
            dr.ellipse([ex - 4.2, ey - 4.0, ex + 4.2, ey + 4.0], fill=(10, 22, 46, 255))
        dr.rounded_rectangle([hx - 8, hy + 5, hx + 8, hy + 21], radius=3, fill=bone_c, outline=glow_c)
        dr.rectangle([hx - 5, hy + 8, hx + 5, hy + 16], fill=(8, 18, 38, 255))

    # Spine + Ribcage + Pelvis
    pelvis_x = 160.0 if d_idx in (0, 4) else (196.0 if d_idx in (1, 2, 3) else 124.0)
    pelvis_y = y_ax - 18.0
    dr.line([(nx, ny - 4), (pelvis_x, pelvis_y)], fill=glow_c, width=7)
    dr.line([(nx, ny - 4), (pelvis_x, pelvis_y)], fill=bone_c, width=3)
    for ri in range(5):
        u = (ri + 1) / 6.0
        rx_c = nx + (pelvis_x - nx) * u
        ry_c = ny + (pelvis_y - ny) * u
        rw_r = (22.0 - abs(ri - 2) * 3.0) * (0.55 if d_idx in (2, 6) else 1.0)
        dr.arc([rx_c - rw_r, ry_c - 6, rx_c + rw_r, ry_c + 7], start=190, end=350, fill=bone_c, width=2)
    dr.ellipse([pelvis_x - 18, pelvis_y - 8, pelvis_x + 18, pelvis_y + 9], outline=bone_c, width=3)

    # Femur + Tibia leg bones matched to direction d
    leg_targets = {
        0: [((pelvis_x - 14, pelvis_y), (82, 138), (28, 92)), ((pelvis_x + 14, pelvis_y), (238, 138), (292, 92))],
        1: [((pelvis_x - 10, pelvis_y), (146, 122), (96, 86)), ((pelvis_x + 8, pelvis_y), (186, 128), (112, 108))],
        2: [((pelvis_x, pelvis_y), (192, 122), (108, 128))],
        3: [((pelvis_x - 10, pelvis_y), (115, 118), (62, 62)), ((pelvis_x + 8, pelvis_y), (168, 110), (142, 62))],
        4: [((pelvis_x - 14, pelvis_y), (108, 124), (68, 66)), ((pelvis_x + 14, pelvis_y), (212, 124), (252, 66))],
        5: [((pelvis_x + 10, pelvis_y), (205, 118), (258, 62)), ((pelvis_x - 8, pelvis_y), (152, 110), (178, 62))],
        6: [((pelvis_x, pelvis_y), (128, 122), (212, 128))],
        7: [((pelvis_x + 10, pelvis_y), (174, 122), (224, 86)), ((pelvis_x - 8, pelvis_y), (134, 128), (208, 108))],
    }[d_idx]
    for hip_p, knee_p, foot_p in leg_targets:
        dr.line([hip_p, knee_p], fill=glow_c, width=6)
        dr.line([hip_p, knee_p], fill=bone_c, width=3)
        dr.line([knee_p, foot_p], fill=glow_c, width=5)
        dr.line([knee_p, foot_p], fill=bone_c, width=2)
        dr.ellipse([knee_p[0] - 4, knee_p[1] - 4, knee_p[0] + 4, knee_p[1] + 4], fill=bone_c)

    skel_blur = skel.filter(ImageFilter.GaussianBlur(radius=2.2))
    comp = Image.fromarray(out, "RGBA")
    comp.alpha_composite(skel_blur)
    comp.alpha_composite(skel)
    # Clamp strictly to original silhouette alpha so zero bone leaks outside body!
    c_arr = np.array(comp)
    c_arr[..., 3] = np.minimum(c_arr[..., 3], alpha)
    return Image.fromarray(c_arr, "RGBA")


def _build_xray_above_view(above90_im):
    arr = np.array(above90_im).copy()
    alpha = arr[..., 3]
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    body_m = (alpha > 80) & (xg > 96) & (xg < W - 96)
    arr[body_m, 0] = 14
    arr[body_m, 1] = 34
    arr[body_m, 2] = 68
    skel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(skel)
    bone_c = (235, 252, 255, 255)
    dr.ellipse([142, 92, 178, 128], fill=bone_c, outline=(56, 225, 255, 220), width=3)
    dr.line([(116, 112), (204, 112)], fill=bone_c, width=3)
    dr.line([(116, 112), (118, 150)], fill=bone_c, width=3)
    dr.line([(204, 112), (202, 150)], fill=bone_c, width=3)
    dr.line([(136, 146), (132, 196)], fill=bone_c, width=3)
    dr.line([(184, 146), (188, 196)], fill=bone_c, width=3)
    comp = Image.fromarray(arr, "RGBA")
    comp.alpha_composite(skel)
    ca = np.array(comp)
    ca[..., 3] = np.minimum(ca[..., 3], alpha)
    return Image.fromarray(ca, "RGBA")


def load_black_vfx_plate(path, target_size=360, gamma_a=0.76, thresh=0.04):
    """Extracts crisp un-premultiplied RGBA from a pure-#000000 studio VFX explosion plate,
    with radial feather near borders so zero rectangular edge can ever appear."""
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGB").resize((target_size, target_size), Image.LANCZOS)
    rgb = np.asarray(im, dtype=np.float32)
    H, W = rgb.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    edge_dist = np.minimum(np.minimum(xg, W - 1 - xg), np.minimum(yg, H - 1 - yg))
    border_fade = np.clip(edge_dist / (target_size * 0.08), 0.0, 1.0)

    mx = np.max(rgb, axis=-1) / 255.0
    alpha = (np.clip((mx - thresh) / 0.36, 0.0, 1.0) ** gamma_a) * border_fade
    denom = np.maximum(alpha[..., None], 0.18)
    clean_rgb = np.clip(rgb / denom, 0.0, 255.0)
    rgba = np.dstack([clean_rgb.astype(np.uint8), np.clip(alpha * 255.0, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def build_vfx_plates_dict(views_dir):
    """Loads photorealistic AI VFX plates (fireball & thermonuclear mushroom cloud) and synthesizes
    matching photographic multi-lobed Napalm Cluster & Fractal-Lightning Plasma Supernova RGBA plates."""
    fire_p = load_black_vfx_plate(os.path.join(views_dir, "fx_fireball_blast.jpg"), target_size=340)
    nuke_p = load_black_vfx_plate(os.path.join(views_dir, "fx_nuke_mushroom.jpg"), target_size=420, gamma_a=0.72, thresh=0.03)

    # Synthesize Tier 2 Multi-Lobed Napalm Cluster RGBA from real pyrotechnic fireball lobes + liquid-fire embers
    napalm_p = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    if fire_p is not None:
        for dx, dy, sc, rot in ((-44, 18, 0.72, -32), (46, 12, 0.75, 44), (0, -28, 0.84, 128)):
            lobe = fire_p.resize((int(340 * sc), int(340 * sc)), Image.BICUBIC).rotate(rot, resample=Image.BICUBIC)
            la = np.array(lobe, dtype=np.float32)
            # Deep rich crimson-scarlet napalm color grade
            la[..., 0] = np.clip(la[..., 0] * 1.18, 0, 255)
            la[..., 1] = np.clip((la[..., 1] / 255.0) ** 1.28 * 240.0, 0, 255)
            la[..., 2] = np.clip((la[..., 2] / 255.0) ** 1.75 * 180.0, 0, 255)
            lobe_c = Image.fromarray(la.astype(np.uint8), "RGBA")
            napalm_p.alpha_composite(lobe_c, (180 + dx - lobe_c.width // 2, 180 + dy - lobe_c.height // 2))
        ndr = ImageDraw.Draw(napalm_p)
        rng_n = np.random.default_rng(202)
        for _ in range(38):
            a = rng_n.uniform(0, 2 * math.pi)
            r0, r1 = rng_n.uniform(22, 65), rng_n.uniform(95, 168)
            ndr.line([(180 + math.cos(a)*r0, 180 + math.sin(a)*r0), (180 + math.cos(a)*r1, 180 + math.sin(a)*r1)], fill=(255, 175, 45, 215), width=2)
            ndr.ellipse([180 + math.cos(a)*r1 - 3, 180 + math.sin(a)*r1 - 3, 180 + math.cos(a)*r1 + 3, 180 + math.sin(a)*r1 + 3], fill=(255, 245, 190, 245))

    # Synthesize Tier 3 High-Voltage Cyan-Ultraviolet Plasma Supernova RGBA from real volumetric blast + fractal Tesla bolts
    plasma_p = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    if fire_p is not None:
        pa = np.array(fire_p.resize((340, 340), Image.BICUBIC), dtype=np.float32)
        lum = (0.35 * pa[..., 0] + 0.50 * pa[..., 1] + 0.15 * pa[..., 2]) / 255.0
        out_p = np.zeros_like(pa)
        # Outer dark smoke -> deep ultraviolet-magenta; mid flame -> electric cyan-azure; core -> blinding white!
        out_p[..., 0] = np.clip((lum ** 2.2) * 255.0 + np.sin(np.clip(lum * math.pi, 0, math.pi)) * 125.0, 0, 255)
        out_p[..., 1] = np.clip((lum ** 0.88) * 255.0, 0, 255)
        out_p[..., 2] = np.clip((lum ** 0.52) * 255.0 + 35.0 * (lum > 0.08), 0, 255)
        out_p[..., 3] = pa[..., 3]
        plasma_p.alpha_composite(Image.fromarray(out_p.astype(np.uint8), "RGBA"), (10, 10))

        # Recursive branching Tesla lightning bolts
        l_ov = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
        ldr = ImageDraw.Draw(l_ov)
        rng_p = np.random.default_rng(303)
        for bi in range(14):
            ang = (bi / 14.0) * 2.0 * math.pi + rng_p.uniform(-0.15, 0.15)
            bx, by = 180.0, 180.0
            pts = [(bx, by)]
            for step in range(6):
                ang += rng_p.uniform(-0.48, 0.48)
                sl = rng_p.uniform(18.0, 28.0)
                bx += math.cos(ang) * sl
                by += math.sin(ang) * sl
                pts.append((bx, by))
                if step == 2:
                    ang2 = ang + rng_p.choice([-0.75, 0.75])
                    ldr.line([(bx, by), (bx + math.cos(ang2)*34, by + math.sin(ang2)*34)], fill=(195, 110, 255, 225), width=3)
                    ldr.line([(bx, by), (bx + math.cos(ang2)*34, by + math.sin(ang2)*34)], fill=(255, 255, 255, 240), width=1)
            ldr.line(pts, fill=(56, 215, 255, 225), width=5)
            ldr.line(pts, fill=(255, 255, 255, 250), width=2)
        plasma_p.alpha_composite(l_ov)

    return dict(fire=fire_p, napalm=napalm_p, plasma=plasma_p, nuke=nuke_p)


# ---------------------------------------------------------------------------
# True 3D (X, Y, Z) -> Any 360° Camera Yaw (d=0..7) Escalating 4-Tier Renderer
# ---------------------------------------------------------------------------

TIER_CONFIGS = {
    1: dict(name="Boom 1: Classic Core Overload", n_frames=84,  det_f=30, n_gibs=24),
    2: dict(name="Boom 2: Napalm Cluster Rampage", n_frames=108, det_f=30, n_gibs=52),
    3: dict(name="Boom 3: Tesla X-Ray Plasma Tornado", n_frames=132, det_f=34, n_gibs=84),
    4: dict(name="Boom 4: THERMONUCLEAR CATACLYSM", n_frames=168, det_f=38, n_gibs=140),
}


def simulate_3d_explosion_tier(tier, seed=20261101):
    """Simulates deterministic 3D (X, Y, Z) rigid bodies, gibs, secondary blasts & floor craters
    for Tier 1..4 so ANY camera angle (0°..360° + Above/Below) can render exact depth-sorted frames!
    Coordinate convention:
      X : Wheelman axle axis (+X = screen-right at d=0, -X = screen-left at d=0)
      Y : Height above ground (Y=0 is floor, +Y is upward!)
      Z : Forward axis (+Z = toward viewer at d=0 where chrome cylinder points)
    """
    cfg = TIER_CONFIGS[tier]
    n_f = cfg["n_frames"]
    det_f = cfg["det_f"]
    n_gibs = cfg["n_gibs"]
    rng = np.random.default_rng(seed + tier * 101)
    dt = 1.0 / 24.0
    grav = 860.0 if tier < 4 else 760.0

    vel_mult = {1: 1.0, 2: 1.32, 3: 1.48, 4: 1.85}[tier]

    # Hero 3D rigid bodies
    bodies = [
        dict(kind="wheel", side=-1, x=-84.0, y=54.0,  z=0.0,   vx=-175*vel_mult, vy=295*vel_mult, vz=55*vel_mult,  ang=0.0, omg=-720*vel_mult, rad=46.0, bounce=0.64, on_fire=(tier>=2)),
        dict(kind="wheel", side=+1, x=+86.0, y=54.0,  z=0.0,   vx=+182*vel_mult, vy=318*vel_mult, vz=-62*vel_mult, ang=0.0, omg=+760*vel_mult, rad=46.0, bounce=0.66, on_fire=(tier>=2)),
        dict(kind="bar",   side=0,  x=+4.0,  y=58.0,  z=+18.0, vx=+68*vel_mult,  vy=375*vel_mult, vz=+125*vel_mult,ang=-8.0,omg=+1080*vel_mult,rad=22.0, bounce=0.50, on_fire=(tier>=2)),
        dict(kind="lleg",  side=-1, x=-78.0, y=142.0, z=+14.0, vx=-138*vel_mult, vy=290*vel_mult, vz=-85*vel_mult, ang=0.0, omg=-540*vel_mult, rad=28.0, bounce=0.38, on_fire=(tier>=4)),
        dict(kind="rleg",  side=+1, x=+80.0, y=142.0, z=+14.0, vx=+144*vel_mult, vy=280*vel_mult, vz=+92*vel_mult, ang=0.0, omg=+520*vel_mult, rad=28.0, bounce=0.38, on_fire=(tier>=4)),
        # Severed screaming head flies super high so it lands dramatically in Act 5!
        dict(kind="head",  side=0,  x=0.0,   y=194.0, z=+8.0,  vx=+16.0,         vy={1:545, 2:660, 3:610, 4:940}[tier], vz=+44.0, ang=0.0, omg=+590.0, rad=25.0, bounce=0.52, on_fire=(tier>=2)),
        dict(kind="cap",   side=0,  x=0.0,   y=0.0,   z=0.0,   vx=+210.0,        vy=230.0,        vz=+160.0,       ang=0.0, omg=+1450.0,       rad=11.0, bounce=0.58, active=False),
        dict(kind="nut",   side=-1, x=0.0,   y=0.0,   z=0.0,   vx=-235.0,        vy=195.0,        vz=-140.0,       ang=0.0, omg=-1650.0,       rad=8.0,  bounce=0.62, active=False),
        dict(kind="nut",   side=+1, x=0.0,   y=0.0,   z=0.0,   vx=+165.0,        vy=275.0,        vz=-175.0,       ang=0.0, omg=+1600.0,       rad=8.0,  bounce=0.62, active=False),
    ]
    for b in bodies:
        b.setdefault("active", True)

    gibs = []
    for gi in range(n_gibs):
        az = rng.uniform(0.0, 2.0 * math.pi)
        el = rng.uniform(0.18, 1.38)
        sp = rng.uniform(160.0, 460.0) * vel_mult
        gibs.append(dict(
            gidx=gi % 24,
            x=float(rng.uniform(-22, 22)),
            y=float(rng.uniform(75, 165)),
            z=float(rng.uniform(-22, 22)),
            vx=math.cos(az) * math.cos(el) * sp,
            vy=math.sin(el) * sp + (180.0 if tier == 4 else 0.0),
            vz=math.sin(az) * math.cos(el) * sp,
            ang=float(rng.uniform(0, 360)),
            omg=float(rng.uniform(-820, 820)),
            rad=float(rng.uniform(9.0, 15.0)),
            bounce=float(rng.uniform(0.28, 0.48)),
            volatile=(tier == 2 and gi < 4) or (tier == 4 and gi < 8),
            popped=False,
        ))

    blasts = []   # list of dict(f0, dur, x, y, z, max_r, style)
    craters = []  # persistent floor craters (x, z, r, style, f0)
    history = []

    for f in range(n_f):
        # Trigger primary detonation(s)
        if f == det_f:
            if tier == 1:
                blasts.append(dict(f0=f, dur=26, x=0.0, y=96.0, z=10.0, max_r=275.0, style="fire"))
                craters.append(dict(x=0.0, z=0.0, r=78.0, style="blood", f0=f))
            elif tier == 2:
                blasts.append(dict(f0=f,     dur=28, x=0.0,   y=105.0, z=12.0,  max_r=315.0, style="napalm"))
                blasts.append(dict(f0=f + 4, dur=26, x=-92.0, y=82.0,  z=+42.0, max_r=255.0, style="fire"))
                blasts.append(dict(f0=f + 8, dur=28, x=+96.0, y=94.0,  z=-38.0, max_r=275.0, style="napalm"))
                craters.append(dict(x=0.0, z=0.0, r=112.0, style="napalm", f0=f))
            elif tier == 3:
                blasts.append(dict(f0=f, dur=34, x=0.0, y=135.0, z=0.0, max_r=365.0, style="plasma"))
                craters.append(dict(x=0.0, z=0.0, r=128.0, style="plasma", f0=f))
            elif tier == 4:
                blasts.append(dict(f0=f, dur=96, x=0.0, y=165.0, z=0.0, max_r=445.0, style="nuke"))
                craters.append(dict(x=0.0, z=0.0, r=185.0, style="magma", f0=f))

        if f > det_f:
            bar_b = bodies[2]
            # Tier 1: Mid-air secondary bar pop at f=44
            if tier == 1 and f == 44:
                blasts.append(dict(f0=f, dur=18, x=bar_b["x"], y=bar_b["y"], z=bar_b["z"], max_r=170.0, style="fire"))
                bar_b["vx"], bar_b["vy"], bar_b["omg"] = -125.0, 145.0, -1350.0
                for sb in bodies[6:]:
                    sb["active"] = True
                    sb["x"], sb["y"], sb["z"] = bar_b["x"], bar_b["y"], bar_b["z"]

            # Tier 2: Rocket-propelled chrome bar corkscrews before exploding at f=58!
            if tier == 2 and f < 58:
                ang_r = f * 0.42
                bar_b["vx"] += math.cos(ang_r) * 32.0
                bar_b["vz"] += math.sin(ang_r) * 32.0
                bar_b["vy"] += 26.0
            elif tier == 2 and f == 58:
                blasts.append(dict(f0=f, dur=24, x=bar_b["x"], y=bar_b["y"], z=bar_b["z"], max_r=235.0, style="napalm"))
                for sb in bodies[6:]:
                    sb["active"] = True
                    sb["x"], sb["y"], sb["z"] = bar_b["x"], bar_b["y"], bar_b["z"]

            # Tier 3: 3D Helical Plasma Tornado (f=36..94) whipping bodies & 84 gibs in a giant 3D cyclone,
            # punctuated by 6 chain plasma blasts, then colossal Thunderbolt Slam at f=96!
            in_tornado = (tier == 3 and 36 <= f < 96)
            if tier == 3 and f in (46, 55, 64, 73, 82, 90):
                ang_p = f * 0.9
                blasts.append(dict(f0=f, dur=16, x=math.cos(ang_p)*95, y=95 + (f-40)*1.8, z=math.sin(ang_p)*95, max_r=185.0, style="plasma"))
            if tier == 3 and f == 96:
                blasts.append(dict(f0=f, dur=26, x=0.0, y=95.0, z=0.0, max_r=350.0, style="plasma"))
                for sb in bodies[6:]:
                    sb["active"] = True
                    sb["x"], sb["y"], sb["z"] = 0.0, 140.0, 0.0

            # Tier 4: 12-Blast Rolling Carpet-Bombing Apocalypse across the 3D arena (f=48..114)!
            if tier == 4 and f >= 48 and f <= 114 and (f - 48) % 6 == 0:
                idx_cb = (f - 48) // 6
                az_cb = idx_cb * 2.15
                rad_cb = 65.0 + (idx_cb % 4) * 52.0
                bx_c, bz_c = math.cos(az_cb) * rad_cb, math.sin(az_cb) * rad_cb
                blasts.append(dict(f0=f, dur=22, x=bx_c, y=68.0, z=bz_c, max_r=220.0, style="napalm" if idx_cb % 2 else "fire"))
                craters.append(dict(x=bx_c, z=bz_c, r=52.0, style="magma", f0=f))
            # Tier 4 Final Comic Head Mini-Nuke POP at f=152!
            if tier == 4 and f == 152:
                hb = bodies[5]
                blasts.append(dict(f0=f, dur=16, x=hb["x"], y=hb["y"] + 24.0, z=hb["z"], max_r=165.0, style="fire"))
                hb["vy"] = 220.0
                hb["omg"] = 980.0

            # Step Rigid Bodies in 3D
            arena_lim = 205.0 if tier < 3 else 235.0
            for bd in bodies:
                if not bd["active"]:
                    continue
                if in_tornado and bd["kind"] != "head":
                    # Swirl around vertical Y axis in a roaring 3D funnel!
                    swirl_r = 65.0 + 0.55 * bd["y"]
                    cur_r = max(8.0, math.hypot(bd["x"], bd["z"]))
                    tx_t, tz_t = -bd["z"] / cur_r, bd["x"] / cur_r
                    rx_t, rz_t = (swirl_r - cur_r) * (bd["x"] / cur_r), (swirl_r - cur_r) * (bd["z"] / cur_r)
                    bd["vx"] = tx_t * 440.0 + rx_t * 6.0
                    bd["vz"] = tz_t * 440.0 + rz_t * 6.0
                    bd["vy"] = 95.0 * math.sin(f * 0.25 + bd["side"]) + (165.0 - bd["y"]) * 2.5
                elif tier == 3 and f == 96:
                    # Thunderbolt blasts everything outward & downward!
                    ang_out = math.atan2(bd["z"], bd["x"] + 0.1)
                    bd["vx"] = math.cos(ang_out) * 340.0
                    bd["vz"] = math.sin(ang_out) * 340.0
                    bd["vy"] = -260.0
                else:
                    bd["vy"] -= grav * dt

                bd["x"] += bd["vx"] * dt
                bd["y"] += bd["vy"] * dt
                bd["z"] += bd["vz"] * dt
                bd["ang"] += bd["omg"] * dt

                if bd["y"] <= bd["rad"]:
                    bd["y"] = bd["rad"]
                    if abs(bd["vy"]) > 48.0:
                        bd["vy"] = abs(bd["vy"]) * bd["bounce"]
                        bd["vx"] *= 0.80
                        bd["vz"] *= 0.80
                        bd["omg"] *= 0.68
                        if bd["kind"] == "wheel" and tier >= 2:
                            craters.append(dict(x=bd["x"], z=bd["z"], r=28.0, style="napalm", f0=f))
                    else:
                        bd["vy"] = 0.0
                        bd["vx"] *= 0.72
                        bd["vz"] *= 0.72
                        if bd["kind"] == "head":
                            bd["omg"] = 0.0
                            bd["ang"] *= 0.45
                        else:
                            bd["omg"] *= 0.55

                for ax_k, v_k in (("x", "vx"), ("z", "vz")):
                    if bd[ax_k] < -arena_lim:
                        bd[ax_k] = -arena_lim
                        bd[v_k] = abs(bd[v_k]) * 0.68
                    elif bd[ax_k] > arena_lim:
                        bd[ax_k] = arena_lim
                        bd[v_k] = -abs(bd[v_k]) * 0.68

            # Step 3D Gibs
            for gi, gb in enumerate(gibs):
                if in_tornado:
                    target_y = 35.0 + (gi / float(max(1, n_gibs))) * 225.0
                    swirl_r = 32.0 + 0.52 * target_y
                    ang_g = f * 0.28 + gi * 0.55
                    gb["x"] = math.cos(ang_g) * swirl_r
                    gb["z"] = math.sin(ang_g) * swirl_r
                    gb["y"] += (target_y - gb["y"]) * 0.24
                    gb["ang"] += gb["omg"] * dt
                    continue
                elif tier == 3 and f == 96:
                    ang_o = math.atan2(gb["z"], gb["x"] + 0.01)
                    sp_o = 140.0 + (gi % 9) * 34.0
                    gb["vx"] = math.cos(ang_o) * sp_o
                    gb["vz"] = math.sin(ang_o) * sp_o
                    gb["vy"] = -180.0 + (gi % 5) * 45.0

                gb["vy"] -= grav * dt
                gb["x"] += gb["vx"] * dt
                gb["y"] += gb["vy"] * dt
                gb["z"] += gb["vz"] * dt
                gb["ang"] += gb["omg"] * dt

                if gb["y"] <= gb["rad"]:
                    gb["y"] = gb["rad"]
                    if gb["volatile"] and not gb["popped"] and f > det_f + 14:
                        gb["popped"] = True
                        gb["vy"] = 285.0
                        blasts.append(dict(f0=f, dur=15, x=gb["x"], y=26.0, z=gb["z"], max_r=135.0, style="fire"))
                        craters.append(dict(x=gb["x"], z=gb["z"], r=34.0, style="napalm", f0=f))
                    elif abs(gb["vy"]) > 52.0:
                        gb["vy"] = abs(gb["vy"]) * gb["bounce"]
                        gb["vx"] *= 0.65
                        gb["vz"] *= 0.65
                        gb["omg"] *= 0.55
                    else:
                        gb["vy"] = 0.0
                        gb["vx"] *= 0.68
                        gb["vz"] *= 0.68
                        gb["omg"] *= 0.45

                for ax_k, v_k in (("x", "vx"), ("z", "vz")):
                    if abs(gb[ax_k]) > arena_lim + 15.0:
                        gb[ax_k] = math.copysign(arena_lim + 15.0, gb[ax_k])
                        gb[v_k] *= -0.55

        # Snapshot frame state
        history.append(dict(
            f=f,
            bodies=[dict(b) for b in bodies if b["active"]],
            gibs=[dict(g) for g in gibs],
            blasts=[dict(bl) for bl in blasts if bl["f0"] <= f < bl["f0"] + bl["dur"]],
            craters=[dict(cr) for cr in craters if cr["f0"] <= f],
        ))
    return history


def render_3d_explosion_frame(tier, sim_state, cam_d, parts_360, scream_grid, norm_views, vfx_plates, stage_wh=(480, 340), ground_y=308):
    """Renders a single frame of Tier 1..4 from ANY 360° camera angle `cam_d` (0..7) with true 3D (X,Y,Z) projection,
    perspective depth-sorting, 8-angle rigid-body part switching, X-ray strobing, and photorealistic VFX plates!"""
    W_s, H_s = stage_wh
    cx_s = W_s * 0.5
    f = sim_state["f"]
    cfg = TIER_CONFIGS[tier]
    det_f = cfg["det_f"]
    th = math.radians(cam_d * 45.0)
    ct, st = math.cos(th), math.sin(th)

    def proj3d(x, y, z):
        u = x * ct - z * st
        depth = x * st + z * ct
        persp = max(0.70, min(1.38, 760.0 / max(320.0, 760.0 - depth)))
        sx = cx_s + u * persp
        sy = (ground_y + depth * 0.13) - y * persp
        return sx, sy, depth, persp

    stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))

    # --- PRE-DETONATION (Act 1 & Act 2: f < det_f) ---
    if f < det_f:
        # Tier 2 spins a frantic 360° burnout across all 8 angles before exploding!
        eff_d = (cam_d + (f // 2 if tier == 2 else 0)) % 8
        ph_k = (f * 2) % len(scream_grid[eff_d])
        wm_im = scream_grid[eff_d][ph_k].copy()

        # Tier 3 & Tier 4 strobe high-voltage 360° X-Ray Skeleton!
        use_xray = (tier == 3 and f >= 8 and (f % 2 == 0)) or (tier == 4 and f >= 18 and (f % 2 == 0))
        if use_xray:
            wm_im = parts_360["xrays"][eff_d].copy()

        ov_start = 14 if tier >= 2 else 18
        shake_x, shake_y = 0, 0
        lift_y = 0
        if tier == 3 and f >= 8:
            # Electromagnetic levitation off the ground!
            lift_y = int(round(min(1.0, (f - 8) / 18.0) * 28.0 + 4.0 * math.sin(f * 0.9)))

        if f >= ov_start:
            ov = (f - ov_start) / float(max(1, det_f - ov_start))
            wm_arr = np.array(wm_im).astype(np.float32)
            hy, hx = np.mgrid[0:wm_arr.shape[0], 0:wm_arr.shape[1]].astype(np.float32)
            rc = np.sqrt(((hx - 160.0) / 72.0) ** 2 + ((hy - 188.0) / 80.0) ** 2)
            if tier == 3 and f >= det_f - 5:
                # Singularity implosion crush right before plasma supernova!
                bloat = -0.42 * ((f - (det_f - 6)) / 5.0) * np.exp(-(rc * 0.85) ** 2)
            else:
                max_bloat = {1: 0.24, 2: 0.42, 3: 0.22, 4: 0.68}[tier]
                bloat = np.exp(-(rc ** 2)) * (max_bloat * (ov ** 1.35) + 0.05 * math.sin(f * 2.8))
            wm_arr = fx._premul_remap(wm_arr.astype(np.uint8), (hx - (hx - 160.0) * bloat).astype(np.float32), (hy - (hy - 188.0) * bloat).astype(np.float32)).astype(np.float32)

            glow = np.exp(-(((hx - 160.0) / (52.0 + 48.0 * ov)) ** 2 + ((hy - 202.0) / (54.0 + 48.0 * ov)) ** 2)) * (wm_arr[..., 3] > 60)
            if tier == 3:
                wm_arr[..., 0] = np.clip(wm_arr[..., 0] + glow * 140.0 * ov, 0, 255)
                wm_arr[..., 1] = np.clip(wm_arr[..., 1] + glow * 235.0 * ov, 0, 255)
                wm_arr[..., 2] = np.clip(wm_arr[..., 2] + glow * 255.0 * ov, 0, 255)
            else:
                wm_arr[..., 0] = np.clip(wm_arr[..., 0] + glow * 250.0 * ov, 0, 255)
                wm_arr[..., 1] = np.clip(wm_arr[..., 1] + glow * 185.0 * (ov ** 1.2), 0, 255)
                wm_arr[..., 2] = np.clip(wm_arr[..., 2] + glow * 110.0 * (ov ** 1.6), 0, 255)
            wm_im = Image.fromarray(wm_arr.astype(np.uint8), "RGBA")
            shake_amp = (2.0 + 6.0 * ov) * (1.35 if tier >= 3 else 1.0)
            shake_x = int(round(math.sin(f * 4.1) * shake_amp))
            shake_y = int(round(math.cos(f * 5.3) * shake_amp * 0.65))

        # Tier 4: 3D Spinning Target-Lock Laser Reticle on Floor + Volumetric Sky-Beam Strike (f=30..37)!
        if tier == 4:
            ret = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
            rdr = ImageDraw.Draw(ret)
            for rr in (95.0, 58.0):
                rdr.ellipse([cx_s - rr, ground_y - rr * 0.22, cx_s + rr, ground_y + rr * 0.22], outline=(255, 42, 68, 210), width=2)
            stage.alpha_composite(ret)
            if f >= det_f - 8:
                beam_im = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
                bdr_s = ImageDraw.Draw(beam_im)
                bw_beam = int(16 + (f - (det_f - 8)) * 11)
                bdr_s.rectangle([cx_s - bw_beam, 0, cx_s + bw_beam, ground_y + 6], fill=(255, 145, 50, 195))
                bdr_s.rectangle([cx_s - bw_beam // 2, 0, cx_s + bw_beam // 2, ground_y + 6], fill=(255, 255, 250, 250))
                stage.alpha_composite(beam_im.filter(ImageFilter.GaussianBlur(radius=6.0)))
                core_im = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
                ImageDraw.Draw(core_im).rectangle([cx_s - bw_beam // 3, 0, cx_s + bw_beam // 3, ground_y + 4], fill=(255, 255, 255, 245))
                stage.alpha_composite(core_im)

        ox_w = int(round(cx_s - wm_im.width * 0.5)) + shake_x
        oy_w = int(round(ground_y - 288)) + shake_y - lift_y
        stage.alpha_composite(wm_im, (ox_w, oy_w))

        # Tier 2 Flaming Burnout Tires / Tier 3 Tesla Arcs
        if tier in (2, 3) and f >= 6:
            ov_fx = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
            odr = ImageDraw.Draw(ov_fx)
            rng_f = np.random.default_rng(700 + tier * 50 + f)
            col_main = (80, 235, 255, 230) if tier == 3 else (255, 165, 35, 220)
            for _ in range(7):
                pts = [(cx_s + shake_x, ground_y - 95 - lift_y)]
                bx, by = pts[0]
                a0 = rng_f.uniform(0, 2 * math.pi)
                for _ in range(4):
                    a0 += rng_f.uniform(-0.65, 0.65)
                    bx += math.cos(a0) * 26.0
                    by += math.sin(a0) * 24.0
                    pts.append((bx, by))
                odr.line(pts, fill=col_main, width=3)
                odr.line(pts, fill=(255, 255, 255, 240), width=1)
            stage.alpha_composite(ov_fx)
        return stage

    # --- POST-DETONATION 3D DEPTH-SORTED RENDERING ---
    # 1) Soft Feathered 3D Scorch, Napalm, Plasma & Magma Floor Craters
    flr = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    fdr = ImageDraw.Draw(flr)
    for cr in sim_state["craters"]:
        sx, sy, _, persp = proj3d(cr["x"], 0.0, cr["z"])
        rx = cr["r"] * persp
        ry = rx * 0.18
        fdr.ellipse([sx - rx, sy - ry, sx + rx, sy + ry], fill=(18, 14, 14, 195))
        in_col = {
            "blood": (132, 12, 16, 205),
            "napalm": (245, 95, 18, 175),
            "plasma": (48, 195, 245, 165),
            "magma": (250, 80, 14, 190),
        }[cr["style"]]
        fdr.ellipse([sx - rx * 0.58, sy - ry * 0.58, sx + rx * 0.58, sy + ry * 0.58], fill=in_col)
    stage.alpha_composite(flr.filter(ImageFilter.GaussianBlur(radius=4.2)))

    # Tier 3 Vertical Ionized Plasma Cyclone Funnel Glow (f=36..95)
    if tier == 3 and 36 <= f < 96:
        vort = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        vdr = ImageDraw.Draw(vort)
        for h_v in range(16, 256, 20):
            sw_r = (32.0 + 0.52 * h_v)
            a_v = f * 0.34 + h_v * 0.05
            p0 = proj3d(math.cos(a_v) * sw_r, h_v, math.sin(a_v) * sw_r)
            p1 = proj3d(math.cos(a_v + 2.1) * sw_r, h_v + 18, math.sin(a_v + 2.1) * sw_r)
            vdr.line([(p0[0], p0[1]), (p1[0], p1[1])], fill=(64, 225, 255, 145), width=4)
        stage.alpha_composite(vort.filter(ImageFilter.GaussianBlur(radius=2.0)))

    # Collect all 3D renderables (blasts, gibs, rigid bodies) and sort back-to-front by `depth`!
    draw_queue = []

    for bl in sim_state["blasts"]:
        sx, sy, depth, persp = proj3d(bl["x"], bl["y"], bl["z"])
        prog = (f - bl["f0"]) / float(max(1, bl["dur"]))
        draw_queue.append((depth, "blast", (bl, sx, sy, persp, prog)))

    for gb in sim_state["gibs"]:
        sx, sy, depth, persp = proj3d(gb["x"], gb["y"], gb["z"])
        draw_queue.append((depth, "gib", (gb, sx, sy, persp)))

    for bd in sim_state["bodies"]:
        sx, sy, depth, persp = proj3d(bd["x"], bd["y"], bd["z"])
        draw_queue.append((depth, "body", (bd, sx, sy, persp)))

    draw_queue.sort(key=lambda item: item[0])

    for _, kind, payload in draw_queue:
        if kind == "blast":
            bl, sx, sy, persp, prog = payload
            plate = vfx_plates.get(bl["style"]) or vfx_plates.get("fire")
            if plate is not None:
                if bl["style"] == "nuke":
                    # Towering Thermonuclear Mushroom Cloud erupts straight out of ground_y & fills the sky!
                    sc_n = 0.56 + 0.58 * (prog ** 0.38)
                    h_nuke = max(32, int(round(min(H_s * 1.05, bl["max_r"] * 0.88) * sc_n * persp)))
                    w_nuke = max(32, int(round(h_nuke * 1.02)))
                    im_p = plate.resize((w_nuke, h_nuke), Image.BICUBIC)
                    if cam_d in (2, 3, 6, 7):
                        im_p = ImageOps.mirror(im_p)
                    arr_p = np.array(im_p, dtype=np.float32)
                    if prog < 0.14:
                        arr_p[..., :3] = np.clip(arr_p[..., :3] * (1.0 + (1.0 - prog / 0.14) * 0.65), 0, 255)
                    elif prog > 0.66:
                        fade_n = max(0.0, 1.0 - (prog - 0.66) / 0.34)
                        arr_p[..., 3] *= fade_n
                    im_p = Image.fromarray(np.clip(arr_p, 0, 255).astype(np.uint8), "RGBA")
                    py_nuke = int(round((ground_y + 10) - im_p.height * 0.91))
                    stage.alpha_composite(im_p, (int(round(sx - im_p.width * 0.5)), py_nuke))
                else:
                    fx._blit_evolving_vfx_fireball(stage, plate, sx, sy, prog, max_diam=bl["max_r"] * persp, rot_deg=prog * 45.0)
        elif kind == "gib":
            gb, sx, sy, persp = payload
            gim = parts_360["gibs"][gb["gidx"]]
            fx._paste_rotated_rgba(stage, gim, sx, sy, gb["ang"], sx=persp, sy=persp, max_bottom_y=ground_y + 26)
        elif kind == "body":
            bd, sx, sy, persp = payload
            b_kind = bd["kind"]
            spin_step = int(round(bd["ang"] / 90.0))
            eff_d = (cam_d + spin_step) % 8
            if b_kind == "head":
                im_b = parts_360["heads"][cam_d]
            elif b_kind == "wheel":
                im_b = parts_360["wheels"][eff_d]
            elif b_kind == "bar":
                im_b = parts_360["bars"][eff_d]
            elif b_kind == "lleg":
                im_b = parts_360["llegs"][cam_d]
            elif b_kind == "rleg":
                im_b = parts_360["rlegs"][cam_d]
            elif b_kind == "cap":
                im_b = parts_360["shrap_cap"]
            else:
                im_b = parts_360["shrap_nut"]

            if bd.get("on_fire") and f < cfg["n_frames"] - 18:
                # Fiery/plasma halo behind burning flying wheels & rocket bar!
                fl_p = vfx_plates.get("plasma" if tier == 3 else "fire")
                if fl_p is not None:
                    fx._blit_evolving_vfx_fireball(stage, fl_p, sx, sy, 0.18 + 0.15 * ((f % 5) / 5.0), max_diam=78.0 * persp, rot_deg=f * 19.0)
            fx._paste_rotated_rgba(stage, im_b, sx, sy, bd["ang"], sx=persp, sy=persp, max_bottom_y=ground_y + 28)

    # Foreground Shockwave Rings, Thunderbolt Slam (Tier 3 f=96) & HDR Starburst Flash!
    fg = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    fdr2 = ImageDraw.Draw(fg)
    if det_f <= f <= det_f + 8:
        k_s = (f - det_f) / 8.0
        r_sh = 34.0 + k_s * (260.0 if tier >= 3 else 205.0)
        col_sh = (110, 240, 255, int(240 * (1 - k_s))) if tier == 3 else (255, 242, 185, int(240 * (1 - k_s)))
        fdr2.ellipse([cx_s - r_sh, (ground_y - 95) - r_sh * 0.45, cx_s + r_sh, (ground_y - 95) + r_sh * 0.45], outline=col_sh, width=max(2, int(7 * (1 - k_s))))

    if tier == 3 and 95 <= f <= 101:
        # Sky-to-Ground Giant Jagged Thunderbolt Slam!
        pts_t = [(cx_s - 12, 0), (cx_s + 22, 85), (cx_s - 18, 165), (cx_s + 16, 235), (cx_s, ground_y)]
        fdr2.line(pts_t, fill=(65, 225, 255, 235), width=16)
        fdr2.line(pts_t, fill=(255, 255, 255, 255), width=7)

    stage.alpha_composite(fg)

    if det_f <= f <= det_f + 3:
        k_fl = (f - det_f) / 4.0
        rad_fl = {1: 135.0, 2: 175.0, 3: 210.0, 4: 295.0}[tier]
        sb = fx._draw_hdr_starburst(stage_wh, cx_s, ground_y - 105.0, radius=rad_fl * (1.0 - 0.2 * k_fl), intensity=1.25 * (1.0 - k_fl), n_rays=18, seed=tier * 30 + f)
        stage.alpha_composite(sb)

    return stage
