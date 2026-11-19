"""Build 3 ultra-detailed, ZERO-GHOSTING crisp cel-animated 2D HD FPS weapon viewmodels
for Kyle Tillet (#1 Pocket Kyle, #3 Scissor-Slingshot Ballista, #4 Forward-Aiming
Executive Audit Briefcase), modeled directly on v_milky / v_pickle / v_dookie.

Uses crisp multi-keyframe cel switches (open -> mid -> shut -> empty) combined with
smooth per-frame continuous motion (darting eyes, kicking legs, flexing scissor limbs,
animated 'MY CUT' gauge needle, crackling lightning, recoil & flying Kyle launch) so
every single frame is razor-sharp with ZERO optical-flow ghosting!
"""

import json
import math
import os
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

ARTIFACT_ROOT = r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
OUT_ROOT = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_2d_weapons_v2")

PLATES = {
    "v1_open": os.path.join(ARTIFACT_ROOT, "kyle_v1_open_1795060128374.jpg"),
    "v1_mid": os.path.join(ARTIFACT_ROOT, "kyle_v1_shut_clean_1795060360578.jpg"),
    "v1_shut": os.path.join(ARTIFACT_ROOT, "kyle_v1_shut_clean_1795060393299.jpg"),
    "v1_empty": os.path.join(ARTIFACT_ROOT, "kyle_v1_empty_1795060251052.jpg"),

    "v3_idle": os.path.join(ARTIFACT_ROOT, "kyle_v3_idle_1795060153639.jpg"),
    "v3_alt": os.path.join(ARTIFACT_ROOT, "kyle_v3_alt_1795060457973.jpg"),
    "v3_charged": os.path.join(ARTIFACT_ROOT, "kyle_v3_charged_1795060268776.jpg"),
    "v3_empty": os.path.join(ARTIFACT_ROOT, "kyle_v3_empty_1795060258215.jpg"),

    "v4_idle": os.path.join(ARTIFACT_ROOT, "kyle_v4_forward_idle_1795060134062.jpg"),
    "v4_charged": os.path.join(ARTIFACT_ROOT, "kyle_v4_charged_1795060270744.jpg"),
    "v4_empty": os.path.join(ARTIFACT_ROOT, "kyle_v4_empty_v2_1795060253527.jpg"),
}

BILL_PATH = os.path.join(ARTIFACT_ROOT, "scratch", "kyle_stage", "sprites", "cash_fx", "bill_front.png")


def key_white_studio(rgb: np.ndarray, protect_rects: List[Tuple[int, int, int, int]] = None,
                     lo_thresh: float = 228.0, sat_thresh: float = 0.085,
                     clear_trapped: bool = True, min_trapped_area: int = 80) -> np.ndarray:
    """Clean white-backdrop keying with border flood-fill, trapped-hole removal outside
    protected rects, SDF anti-aliasing, and white-backdrop color un-premultiplication."""
    h, w = rgb.shape[:2]
    arr = rgb.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    cand = ((lo > lo_thresh) & (sat < sat_thresh)).astype(np.uint8)
    _, lbl = cv2.connectedComponents(cand, connectivity=4)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)
    bg = np.isin(lbl, list(border_ids))

    if clear_trapped:
        trapped = ((lo > 240.0) & (sat < 0.055) & (~bg)).astype(np.uint8)
        if protect_rects:
            for x0, y0, x1, y1 in protect_rects:
                trapped[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = 0
        tn, tlbl, stats, _ = cv2.connectedComponentsWithStats(trapped, connectivity=4)
        for tid in range(1, tn):
            if stats[tid, cv2.CC_STAT_AREA] >= min_trapped_area:
                bg[tlbl == tid] = True

    fg = (~bg).astype(np.uint8)
    fn, flbl, fstats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if fn > 1:
        keep = np.zeros_like(fg, dtype=bool)
        for fid in range(1, fn):
            if fstats[fid, cv2.CC_STAT_AREA] >= 60:
                keep[flbl == fid] = True
        fg = keep.astype(np.uint8)

    dist_in = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    dist_out = cv2.distanceTransform(1 - fg, cv2.DIST_L2, 5)
    sdf = dist_in - dist_out

    alpha = np.clip((sdf + 0.35) / 1.40, 0.0, 1.0)
    rim = (fg > 0) & (dist_in <= 3.0) & (lo > 195.0) & (sat < 0.12)
    alpha[rim] *= np.clip((246.0 - lum[rim]) / 52.0, 0.0, 1.0)

    semi = (alpha > 0.04) & (alpha < 0.98)
    rgb_clean = arr.copy()
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.18)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)
    rgb_clean[alpha <= 0.03] = 0.0
    alpha[alpha <= 0.03] = 0.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return out


def load_keyed(key: str, protect: List[Tuple[int, int, int, int]] = None, **kw) -> np.ndarray:
    rgb = np.asarray(Image.open(PLATES[key]).convert("RGB"))
    return key_white_studio(rgb, protect_rects=protect, **kw)


def to_premul(rgba: np.ndarray) -> np.ndarray:
    out = rgba.astype(np.float32)
    out[..., :3] *= (out[..., 3:4] / 255.0)
    return out


def from_premul(pm: np.ndarray) -> np.ndarray:
    out = np.zeros_like(pm, dtype=np.uint8)
    a = np.clip(pm[..., 3], 0.0, 255.0)
    nz = a > 0.5
    rgb = np.zeros_like(pm[..., :3], dtype=np.float32)
    rgb[nz] = pm[..., :3][nz] * (255.0 / a[nz, None])
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return out


def shift_rgba(rgba: np.ndarray, dx: float, dy: float, angle_deg: float = 0.0,
               pivot: Tuple[float, float] = None, scale: float = 1.0) -> np.ndarray:
    h, w = rgba.shape[:2]
    if pivot is None:
        pivot = (w * 0.5, h * 0.5)
    pm = to_premul(rgba)
    M = cv2.getRotationMatrix2D(pivot, angle_deg, scale)
    M[0, 2] += dx
    M[1, 2] += dy
    warped = cv2.warpAffine(pm, M, (w, h), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return from_premul(warped)


def resize_rgba(rgba: np.ndarray, wh: Tuple[int, int]) -> np.ndarray:
    pm = to_premul(rgba)
    ds = cv2.resize(pm, wh, interpolation=cv2.INTER_AREA)
    return from_premul(ds)


def alpha_over_np(dst_rgba: np.ndarray, src_rgba: np.ndarray, xy: Tuple[int, int] = (0, 0)) -> np.ndarray:
    im = Image.fromarray(dst_rgba, "RGBA")
    src = Image.fromarray(src_rgba, "RGBA")
    im.alpha_composite(src, dest=xy)
    return np.asarray(im)


def make_glint(size: int = 120, color=(200, 255, 220), intensity: float = 1.0) -> np.ndarray:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size // 2
    rm = int(size * 0.45 * intensity)
    rw = max(2, int(size * 0.075))
    col = (*color, int(235 * min(1.0, intensity)))
    d.polygon([(c, c - rm), (c + rw, c), (c, c + rm), (c - rw, c)], fill=col)
    d.polygon([(c - rm, c), (c, c + rw), (c + rm, c), (c, c - rw)], fill=col)
    rc = max(4, int(size * 0.13 * intensity))
    d.ellipse((c - rc, c - rc, c + rc, c + rc), fill=(255, 255, 255, int(240 * min(1.0, intensity))))
    return np.asarray(im)


def draw_darting_eyes_v1(rgba: np.ndarray, look_dx: float, look_dy: float,
                         cross_eyed: float = 0.0, wide_scale: float = 1.0) -> np.ndarray:
    """Paint crisp photorealistic sclera + darting blue-grey irises + specular catchlights
    strictly inside Kyle's exact left (421, 456) and right (468, 453) eye openings!"""
    out = rgba.copy()
    eyes = [
        (421.0, 456.0, 11.8, 7.0 * wide_scale, +cross_eyed),
        (468.5, 453.5, 11.8, 7.0 * wide_scale, -cross_eyed),
    ]
    for cx, cy, rx, ry, x_off in eyes:
        x0, x1 = int(cx - rx - 3), int(cx + rx + 4)
        y0, y1 = int(cy - ry - 3), int(cy + ry + 4)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        eye_m = np.clip((1.0 - d) * 3.8, 0.0, 1.0)
        lid_shade = np.clip(0.84 + 0.16 * ((yy - (cy - ry)) / max(1.0, 2.0 * ry)), 0.78, 1.0)
        sclera = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.float32)
        sclera[..., 0] = 238.0 * lid_shade
        sclera[..., 1] = 230.0 * lid_shade
        sclera[..., 2] = 224.0 * lid_shade

        ix = cx + np.clip(look_dx + x_off, -6.2, 6.2)
        iy = cy + np.clip(look_dy, -3.4, 3.4)
        ri = 5.4
        rp = 2.7
        dist_i = np.sqrt((xx - ix) ** 2 + (yy - iy) ** 2)
        iris_m = np.clip((ri - dist_i) * 1.6, 0.0, 1.0)
        limbal = np.clip((dist_i - (ri - 1.3)) / 1.3, 0.0, 1.0) * iris_m
        pupil_m = np.clip((rp - dist_i) * 2.0, 0.0, 1.0)

        iris_rgb = np.array([72.0, 96.0, 118.0], dtype=np.float32)
        ring_rgb = np.array([30.0, 38.0, 48.0], dtype=np.float32)
        col = sclera * (1.0 - iris_m[..., None]) + iris_rgb * iris_m[..., None]
        col = col * (1.0 - limbal[..., None] * 0.78) + ring_rgb * (limbal[..., None] * 0.78)
        col = col * (1.0 - pupil_m[..., None]) + np.array([10.0, 10.0, 14.0]) * pupil_m[..., None]

        dist_gl = np.sqrt((xx - (ix - 1.7)) ** 2 + (yy - (iy - 1.6)) ** 2)
        gl_m = np.clip((1.7 - dist_gl) * 1.4, 0.0, 1.0)
        col = col * (1.0 - gl_m[..., None]) + 255.0 * gl_m[..., None]

        patch = out[y0:y1, x0:x1, :3].astype(np.float32)
        out[y0:y1, x0:x1, :3] = np.clip(patch * (1.0 - eye_m[..., None]) + col * eye_m[..., None], 0, 255).astype(np.uint8)
    return out


def wiggle_lower_legs_v1(rgba: np.ndarray, angle_l: float, angle_r: float) -> np.ndarray:
    """Kick/dangle Kyle's khaki legs & brown loafers below the gripping hand."""
    h, w = rgba.shape[:2]
    out = rgba.copy()
    mask_l = np.zeros((h, w), dtype=bool)
    mask_l[825:1165, 330:448] = True
    mask_r = np.zeros((h, w), dtype=bool)
    mask_r[825:1165, 448:545] = True

    leg_l = np.zeros_like(rgba)
    leg_l[mask_l] = rgba[mask_l]
    leg_r = np.zeros_like(rgba)
    leg_r[mask_r] = rgba[mask_r]
    out[mask_l | mask_r] = 0

    leg_l_rot = shift_rgba(leg_l, 0, 0, angle_deg=angle_l, pivot=(412.0, 825.0))
    leg_r_rot = shift_rgba(leg_r, 0, 0, angle_deg=angle_r, pivot=(476.0, 825.0))
    out = alpha_over_np(out, leg_l_rot)
    out = alpha_over_np(out, leg_r_rot)
    return out


def build_v1_pocket_kyle(out_dir: str) -> Dict:
    """#1: Pocket Kyle — razor-sharp 3-pose scissoring arms + darting eyes + kicking legs + empty open palm."""
    protect = [(405, 440, 485, 515), (460, 565, 525, 622), (320, 720, 570, 800)]
    v_open = load_keyed("v1_open", protect=protect, lo_thresh=228.0, sat_thresh=0.085)
    v_mid = load_keyed("v1_mid", protect=protect, lo_thresh=228.0, sat_thresh=0.085)
    v_shut = load_keyed("v1_shut", protect=protect, lo_thresh=228.0, sat_thresh=0.085)
    v_empty = load_keyed("v1_empty", protect=None, lo_thresh=228.0, sat_thresh=0.085)

    # Lock lower body/hand/face from v_open below y=608 on v_mid & v_shut so hand/pants/nametag NEVER jitter!
    h, w = v_open.shape[:2]
    for v_pose in (v_mid, v_shut):
        v_pose[608:, :] = v_open[608:, :]

    # Extract full mini-Kyle + open scissors (without forearm/hand) for Fire flying projectile
    yy, xx = np.ogrid[:h, :w]
    kyle_fly_m = (yy < 1155) & ~((xx > 535) & (yy > 640)) & ~((xx > 475) & (yy > 880))
    kyle_fly = v_open.copy()
    kyle_fly[~kyle_fly_m] = 0
    im_kf = Image.fromarray(kyle_fly, "RGBA")
    kb = im_kf.getbbox()
    im_kf = im_kf.crop(kb) if kb else im_kf

    # Save zoomed eye-dart audit strip (Left, Right, Up, Cross-eyed)
    eye_strip = Image.new("RGB", (220 * 4, 220), (24, 30, 42))
    for idx, (ldx, ldy, cr) in enumerate([(-6.0, 0.0, 0.0), (6.0, 0.0, 0.0), (0.0, -3.2, 0.0), (0.0, -1.0, 3.0)]):
        ef = draw_darting_eyes_v1(v_open, ldx, ldy, cross_eyed=cr, wide_scale=1.18)
        crop = Image.fromarray(ef[365:545, 355:535], "RGBA")
        cell = Image.new("RGBA", (220, 220), (24, 30, 42, 255))
        cell.alpha_composite(crop.resize((220, 220), Image.Resampling.LANCZOS))
        eye_strip.paste(cell.convert("RGB"), (idx * 220, 0))
    eye_strip.save(os.path.join(out_dir, "_audit_v1_eyes.jpg"), quality=92)

    canvas_wh = (460, 616)

    # Crisp 32-frame Idle choreography:
    # Two snappy arm-scissoring chomps (open -> mid -> shut -> shut -> mid -> open) while eyes dart playfully!
    idle_arm_seq = (
        ["open"] * 7 + ["mid", "shut", "shut", "mid"] + ["open"] * 5
        + ["open"] * 6 + ["mid", "shut", "shut", "shut", "mid"] + ["open"] * 5
    )  # 32 frames
    # Eye dart choreography (32f): center -> quick snap LEFT -> hold -> quick snap RIGHT -> hold -> glance UP at scissors -> crazy stare!
    idle_eyes = (
        [(0.0, 0.0)] * 3 + [(-5.8, 0.0)] * 5 + [(0.0, 0.0)] * 2 + [(5.8, 0.2)] * 5
        + [(0.0, -3.2)] * 5 + [(-5.0, -2.2)] * 3 + [(5.0, -2.2)] * 3
        + [(0.0, 0.0)] * 3 + [(0.0, -0.5)] * 3
    )  # 32 frames

    # Frantic 24-frame Lock-On choreography: rapid arm-scissoring (6 full chomps/sec!) + wild darting/cross-eyed eyes!
    lock_arm_seq = (["open", "mid", "shut", "mid"] * 6)  # 24 frames

    pose_map = {"open": v_open, "mid": v_mid, "shut": v_shut}

    def compose(mode: str, i: int, n: int) -> Image.Image:
        t = i / n
        if mode == "idle":
            pkey = idle_arm_seq[i % len(idle_arm_seq)]
            fr = pose_map[pkey].copy()
            edx, edy = idle_eyes[i % len(idle_eyes)]
            fr = draw_darting_eyes_v1(fr, edx, edy, cross_eyed=0.0, wide_scale=1.10)
            kick = math.sin(2 * math.pi * t * 4) * (4.0 if pkey == "open" else 7.5)
            fr = wiggle_lower_legs_v1(fr, kick, -kick * 0.9)
            if pkey == "shut":
                fr = alpha_over_np(fr, make_glint(145, (235, 252, 255), 0.95), (382, 130))
            bob_x = 5.0 * math.sin(2 * math.pi * t)
            bob_y = 8.0 * math.cos(2 * math.pi * t * 2) - (8.0 if pkey == "shut" else 0.0)
            fr = shift_rgba(fr, bob_x, bob_y, angle_deg=1.3 * math.sin(2 * math.pi * t), pivot=(w * 0.78, h * 0.95))

        elif mode == "lock":
            pkey = lock_arm_seq[i % len(lock_arm_seq)]
            fr = pose_map[pkey].copy()
            # Rapid darting + cross-eyed lock focus!
            edx = 5.8 * math.sin(2 * math.pi * t * 5)
            edy = -2.8 * abs(math.cos(2 * math.pi * t * 4))
            cross = 2.6 * (0.5 + 0.5 * math.sin(2 * math.pi * t * 3))
            fr = draw_darting_eyes_v1(fr, edx, edy, cross_eyed=cross, wide_scale=1.26)
            kick = 10.0 * math.sin(2 * math.pi * t * 8)
            fr = wiggle_lower_legs_v1(fr, kick, -kick)
            if pkey == "shut":
                fr = alpha_over_np(fr, make_glint(185, (110, 255, 160), 1.0), (362, 108))
            sx = 7.5 * math.sin(2 * math.pi * t * 9)
            sy = 6.5 * math.cos(2 * math.pi * t * 7) - 18.0
            fr = shift_rgba(fr, sx, sy, angle_deg=2.6 * math.sin(2 * math.pi * t * 6), pivot=(w * 0.78, h * 0.95))

        else:
            # Fire (22f): 0..4 squeeze wind-back, 5..14 EMPTY OPEN PALM + spinning Kyle dart flying up-left, 15..21 fresh Pocket Kyle rises!
            if i <= 4:
                p = i / 4.0
                pkey = "open" if i <= 1 else ("mid" if i == 2 else "shut")
                fr = pose_map[pkey].copy()
                fr = draw_darting_eyes_v1(fr, 0.0, -2.5, cross_eyed=3.0 * p, wide_scale=1.35)
                fr = wiggle_lower_legs_v1(fr, 11.0 * p, -11.0 * p)
                fr = shift_rgba(fr, 55 * p, 90 * p, angle_deg=-11.0 * p, pivot=(w * 0.80, h * 0.96))
            elif i <= 14:
                p = (i - 4) / 10.0
                whip = math.sin(min(1.0, p * 1.4) * math.pi)
                drop = max(0.0, (p - 0.45) / 0.55) ** 1.6
                hx = -75 * whip + 85 * drop
                hy = -35 * whip + 420 * drop
                fr = shift_rgba(v_empty, hx, hy, angle_deg=15.0 * whip - 10.0 * drop, pivot=(w * 0.78, h * 0.95))
                if p <= 0.85:
                    fp = p / 0.85
                    sc = max(0.14, 0.72 * (1.0 - fp * 0.84))
                    kw, kh = int(im_kf.width * sc), int(im_kf.height * sc)
                    if kw > 8 and kh > 8:
                        k_rs = im_kf.resize((kw, kh), Image.Resampling.BILINEAR)
                        k_arr = shift_rgba(np.asarray(k_rs), 0, 0, angle_deg=fp * 360.0)
                        kx = max(0, int(360 - fp * 310 - kw * 0.5))
                        ky = max(0, int(340 - fp * 310 - kh * 0.5))
                        fr = alpha_over_np(fr, k_arr, (kx, ky))
            else:
                p = (i - 14) / 7.0
                ease = 1.0 - (1.0 - p) ** 3
                fr = draw_darting_eyes_v1(v_open, 5.0 * (1.0 - ease), 0.0, wide_scale=1.12)
                fr = shift_rgba(fr, 30 * (1.0 - ease), 360 * (1.0 - ease), angle_deg=-8.0 * (1.0 - ease), pivot=(w * 0.8, h * 0.95))

        return Image.fromarray(resize_rgba(fr, canvas_wh), "RGBA")

    return _save_seq(out_dir, "v1_pocket_kyle", compose, 32, 24, 22)


def flex_v3_limbs(rgba: np.ndarray, flex_deg: float) -> np.ndarray:
    """Smoothly bend left & right colossal scissor bow limbs backward under draw tension!"""
    if abs(flex_deg) < 0.25:
        return rgba
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dl = np.clip((470.0 - xx) / 420.0, 0.0, 1.0)
    dr = np.clip((xx - 730.0) / 420.0, 0.0, 1.0)
    limb_y = np.clip((yy - 210.0) / 55.0, 0.0, 1.0) * np.clip((620.0 - yy) / 80.0, 0.0, 1.0)
    bend = (dl ** 1.45 + dr ** 1.45) * limb_y
    map_y = yy - bend * flex_deg * 3.8
    map_x = xx - (dl ** 1.45) * limb_y * flex_deg * 1.5 + (dr ** 1.45) * limb_y * flex_deg * 1.5
    pm = to_premul(rgba)
    warped = cv2.remap(pm, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return from_premul(warped)


def draw_v3_laser_lock(rgba: np.ndarray, intensity: float) -> np.ndarray:
    """Draw twin converging lock-on laser beams from the scissor bow tips toward Kyle's snip point."""
    if intensity <= 0.05:
        return rgba
    im = Image.fromarray(rgba, "RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    tx, ty = 955, 190
    a_out = int(75 * intensity)
    a_in = int(205 * intensity)
    col_out = (80, 255, 130, a_out) if intensity > 0.7 else (255, 160, 40, a_out)
    col_in = (190, 255, 200, a_in) if intensity > 0.7 else (255, 235, 140, a_in)
    for sx, sy in [(115, 350), (1105, 345)]:
        d.line([(sx, sy), (tx, ty)], fill=col_out, width=8)
        d.line([(sx, sy), (tx, ty)], fill=col_in, width=2)
    im.alpha_composite(ov)
    return np.asarray(im)


def build_v3_scissor_ballista(out_dir: str) -> Dict:
    """#3: Scissor-Slingshot Ballista — razor-sharp 4-keyframe multi-pose cycle + smooth limb flex + laser + whipping empty launch."""
    protect = [(645, 110, 745, 225), (520, 620, 675, 760)]
    v_idle = load_keyed("v3_idle", protect=protect, lo_thresh=228.0, sat_thresh=0.088)
    v_alt = load_keyed("v3_alt", protect=protect, lo_thresh=228.0, sat_thresh=0.088)
    v_chg = load_keyed("v3_charged", protect=protect, lo_thresh=228.0, sat_thresh=0.088)
    v_emp = load_keyed("v3_empty", protect=[(520, 620, 675, 760), (570, 40, 810, 340)], lo_thresh=228.0, sat_thresh=0.088)

    h, w = v_idle.shape[:2]
    # Extract clean flying Kyle cutout from v_idle for Fire zoom-out
    diff = np.abs(v_idle[..., :3].astype(np.float32) - v_emp[..., :3].astype(np.float32)).mean(axis=2)
    yy, xx = np.ogrid[:h, :w]
    kyle_m = (diff > 18.0) & (v_idle[..., 3] > 128) & (yy < 580) & (xx > 315) & (xx < 1015)
    kyle_m = cv2.morphologyEx(kyle_m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
    kyle_cut = v_idle.copy()
    kyle_cut[~kyle_m] = 0
    im_kc = Image.fromarray(kyle_cut, "RGBA")
    kb = im_kc.getbbox()
    im_kc = im_kc.crop(kb) if kb else im_kc

    pose_map = {"idle": v_idle, "alt": v_alt, "chg": v_chg}
    # Rich 32-frame Idle: looks ahead -> kicks leg high & glances maniacally at player -> snaps scissors shut! -> relaxes!
    idle_seq = (
        ["idle"] * 7 + ["alt"] * 7 + ["chg"] * 4 + ["alt"] * 4 + ["chg"] * 3 + ["idle"] * 7
    )  # 32f
    # Frantic 28-frame Hold-to-Lock: rapid kicking + cranking + open/shut scissor chomping!
    lock_seq = (["alt", "alt", "chg", "chg"] * 7)  # 28f

    canvas_wh = (600, 448)

    def compose(mode: str, i: int, n: int) -> Image.Image:
        t = i / n
        if mode == "idle":
            pk = idle_seq[i % len(idle_seq)]
            fr = pose_map[pk].copy()
            # Subtle breathing limb flex synced with crank/kicks
            flx = 2.5 if pk == "alt" else (4.2 if pk == "chg" else 0.5)
            fr = flex_v3_limbs(fr, flx)
            bx = 6.0 * math.sin(2 * math.pi * t)
            by = 7.0 * math.cos(2 * math.pi * t * 2)
            fr = shift_rgba(fr, bx, by, angle_deg=1.0 * math.sin(2 * math.pi * t), pivot=(w * 0.5, h * 0.95))

        elif mode == "lock":
            pk = lock_seq[i % len(lock_seq)]
            fr = pose_map[pk].copy()
            # Progressive heavy bow draw flex (ramps up to 14 deg + pulsing tension!)
            flex = 6.0 + 9.0 * math.sin(min(1.0, t * 1.6) * math.pi * 0.5) + (2.0 if pk == "chg" else 0.0)
            fr = flex_v3_limbs(fr, flex)
            laser_int = 0.45 + 0.55 * min(1.0, t * 1.5)
            fr = draw_v3_laser_lock(fr, laser_int)
            if pk == "chg":
                fr = alpha_over_np(fr, make_glint(175, (110, 255, 155), 1.0), (905, 108))
            jx = 6.0 * math.sin(2 * math.pi * t * 9)
            jy = 5.0 * math.cos(2 * math.pi * t * 7) + 12.0 * (flex / 15.0)
            fr = shift_rgba(fr, jx, jy, angle_deg=1.5 * math.sin(2 * math.pi * t * 6), pivot=(w * 0.5, h * 0.95))

        else:
            if i <= 2:
                p = i / 2.0
                fr = flex_v3_limbs(v_chg, 16.0 * p)
                fr = draw_v3_laser_lock(fr, 1.0)
                fr = shift_rgba(fr, 0, 26 * p)
            elif i <= 15:
                p = (i - 2) / 13.0
                snap = -11.0 * math.exp(-p * 5.0) * math.cos(p * 18.0)
                fr = flex_v3_limbs(v_emp, snap)
                kick = math.sin(min(1.0, p * 2.6) * math.pi) if p < 0.42 else 0.0
                fr = shift_rgba(fr, 0, 58 * kick, scale=1.0 + 0.04 * kick, pivot=(w * 0.5, h * 0.92))
                if p <= 0.75:
                    fp = p / 0.75
                    sc = max(0.14, 0.85 * (1.0 - fp * 0.86))
                    kw, kh = int(im_kc.width * sc), int(im_kc.height * sc)
                    if kw > 8 and kh > 8:
                        k_rs = im_kc.resize((kw, kh), Image.Resampling.BILINEAR)
                        k_arr = shift_rgba(np.asarray(k_rs), 0, 0, angle_deg=-15.0 * fp)
                        kx = max(0, int(600 - kw * 0.5 + 30 * (1.0 - fp)))
                        ky = max(0, int(290 - fp * 250 - kh * 0.5))
                        fr = alpha_over_np(fr, k_arr, (kx, ky))
                if i <= 5:
                    fr = alpha_over_np(fr, make_glint(210, (255, 225, 110), 1.0 - (i - 3) * 0.3), (495, 220))
            else:
                p = (i - 15) / 8.0
                ease = 1.0 - (1.0 - p) ** 3
                fr = shift_rgba(v_idle, 0, 240 * (1.0 - ease))

        return Image.fromarray(resize_rgba(fr, canvas_wh), "RGBA")

    return _save_seq(out_dir, "v3_scissor_ballista", compose, 32, 28, 24)


def clean_v4_dial_and_draw_needle(rgba: np.ndarray, angle_deg: float, hot: float = 0.0) -> np.ndarray:
    """Cleanly cover the static printed needle inside V4's 'MY CUT' dial (1013, 498) and draw
    ONE razor-sharp animated needle + fiery danger glow!"""
    im = Image.fromarray(rgba, "RGBA")
    d = ImageDraw.Draw(im)
    cx, cy, rad = 1013.0, 498.0, 44.0
    # Paint warm cream/amber dial center disc (keeping outer tick marks & 'MY CUT' text untouched!)
    disc_col = (255, 215, 130, 255) if hot > 0.4 else (246, 225, 165, 255)
    d.ellipse((cx - 26, cy - 26, cx + 26, cy + 16), fill=disc_col)
    if hot > 0.05:
        glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gr = int(rad * 1.32)
        gd.ellipse((cx - gr, cy - gr, cx + gr, cy + gr), fill=(255, 85, 20, int(85 * hot)))
        im.alpha_composite(glow)
        d = ImageDraw.Draw(im)
    rad_a = math.radians(angle_deg)
    x1 = cx + math.cos(rad_a) * rad * 0.80
    y1 = cy + math.sin(rad_a) * rad * 0.80
    x0 = cx - math.cos(rad_a) * rad * 0.16
    y0 = cy - math.sin(rad_a) * rad * 0.16
    col = (230, 30, 18, 255) if hot > 0.4 else (32, 24, 20, 255)
    d.line([(x0, y0), (x1, y1)], fill=col, width=6)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(38, 32, 26, 255))
    return np.asarray(im)


def build_v4_audit_briefcase(out_dir: str) -> Dict:
    """#4: REDESIGNED forward-aiming Executive Audit Briefcase Launcher — razor-sharp zero-ghost animation."""
    protect = [(430, 235, 560, 370), (940, 425, 1085, 575), (440, 340, 610, 460)]
    v_idle = load_keyed("v4_idle", protect=protect, lo_thresh=228.0, sat_thresh=0.088)
    v_chg = load_keyed("v4_charged", protect=protect + [(270, 120, 560, 470)], lo_thresh=228.0, sat_thresh=0.088)
    v_emp = load_keyed("v4_empty", protect=[(940, 425, 1085, 575), (180, 160, 660, 560)], lo_thresh=228.0, sat_thresh=0.088)

    h, w = v_idle.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    bill_im = Image.open(BILL_PATH).convert("RGBA") if os.path.exists(BILL_PATH) else None

    kyle_m = (xx >= 380) & (xx <= 585) & (yy >= 230) & (yy <= 430) & (v_idle[..., 3] > 128)
    kyle_cut = v_idle.copy()
    kyle_cut[~kyle_m] = 0
    im_kc = Image.fromarray(kyle_cut, "RGBA")
    kb = im_kc.getbbox()
    im_kc = im_kc.crop(kb) if kb else im_kc

    canvas_wh = (600, 448)

    def compose(mode: str, i: int, n: int) -> Image.Image:
        t = i / n
        if mode == "idle":
            # Crisp v_idle with occasional electric teaser blink (frames 13..15) + live ticking 'MY CUT' gauge + breathing sway!
            is_spark = (13 <= i <= 15)
            fr = (v_chg if is_spark else v_idle).copy()
            g_ang = -140.0 + 38.0 * math.sin(2 * math.pi * t * 2) + (35.0 if is_spark else 0.0)
            fr = clean_v4_dial_and_draw_needle(fr, g_ang, hot=0.45 if is_spark else 0.0)
            bx = 5.5 * math.sin(2 * math.pi * t)
            by = 6.5 * math.cos(2 * math.pi * t * 2)
            fr = shift_rgba(fr, bx, by, angle_deg=0.9 * math.sin(2 * math.pi * t), pivot=(w * 0.80, h * 0.94))

        elif mode == "lock":
            # Rapid electric crackling alternation between v_chg (green lightning + flying bills) and high-intensity glint pulses!
            flicker = (i % 4) != 0
            fr = (v_chg if flicker else v_idle).copy()
            g_ang = -25.0 + 22.0 * math.sin(2 * math.pi * t * 7)
            fr = clean_v4_dial_and_draw_needle(fr, g_ang, hot=0.85 if flicker else 0.55)
            if (i % 3) == 0:
                fr = alpha_over_np(fr, make_glint(175, (110, 255, 145), 1.0), (245, 195))
            elif (i % 3) == 1:
                fr = alpha_over_np(fr, make_glint(150, (140, 255, 180), 0.9), (210, 315))
            jx = 7.0 * math.sin(2 * math.pi * t * 9)
            jy = 5.5 * math.cos(2 * math.pi * t * 7) - 6.0
            fr = shift_rgba(fr, jx, jy, angle_deg=1.6 * math.sin(2 * math.pi * t * 6), pivot=(w * 0.80, h * 0.94))

        else:
            if i <= 2:
                p = i / 2.0
                fr = clean_v4_dial_and_draw_needle(v_chg, 12.0, hot=1.0)
                fr = shift_rgba(fr, 18 * p, 14 * p)
            elif i <= 15:
                p = (i - 2) / 13.0
                kick = math.sin(min(1.0, p * 2.5) * math.pi) if p < 0.44 else 0.0
                fr = clean_v4_dial_and_draw_needle(v_emp, 12.0 - 150.0 * p, hot=max(0.0, 1.0 - p * 1.5))
                fr = shift_rgba(fr, 68 * kick, 48 * kick, angle_deg=-7.0 * kick, pivot=(w * 0.82, h * 0.95))
                if p <= 0.75:
                    fp = p / 0.75
                    sc = max(0.16, 0.90 * (1.0 - fp * 0.82))
                    kw, kh = int(im_kc.width * sc), int(im_kc.height * sc)
                    if kw > 8 and kh > 8:
                        k_rs = im_kc.resize((kw, kh), Image.Resampling.BILINEAR)
                        k_arr = shift_rgba(np.asarray(k_rs), 0, 0, angle_deg=fp * 260.0)
                        kx = max(0, int(350 - fp * 270 - kw * 0.5))
                        ky = max(0, int(280 - fp * 220 - kh * 0.5))
                        fr = alpha_over_np(fr, k_arr, (kx, ky))
                if bill_im is not None and p <= 0.7:
                    bp = p / 0.7
                    for bi in range(4):
                        bx = max(0, int(340 - bp * (240 + bi * 35)))
                        by = max(0, int(320 - bp * (180 - bi * 55)))
                        b_rs = np.asarray(bill_im.resize((88, 44)))
                        b_rot = shift_rgba(b_rs, 0, 0, angle_deg=bp * 300 + bi * 55)
                        fr = alpha_over_np(fr, b_rot, (bx, by))
            else:
                p = (i - 15) / 8.0
                ease = 1.0 - (1.0 - p) ** 3
                fr = clean_v4_dial_and_draw_needle(v_idle, -140.0, hot=0.0)
                fr = shift_rgba(fr, 45 * (1.0 - ease), 230 * (1.0 - ease))

        return Image.fromarray(resize_rgba(fr, canvas_wh), "RGBA")

    return _save_seq(out_dir, "v4_audit_briefcase", compose, 28, 24, 24)


def _save_seq(out_dir: str, wid: str, fn, n_idle: int, n_lock: int, n_fire: int) -> Dict:
    wdir = os.path.join(out_dir, wid)
    os.makedirs(wdir, exist_ok=True)
    meta = {"id": wid, "idle": [], "lock": [], "fire": []}
    for mode, count in [("idle", n_idle), ("lock", n_lock), ("fire", n_fire)]:
        for i in range(count):
            im = fn(mode, i, count)
            fname = f"{mode}_{i:02d}.png"
            im.save(os.path.join(wdir, fname), optimize=True)
            meta[mode].append(fname)
    meta["size"] = list(Image.open(os.path.join(wdir, meta["idle"][0])).size)
    return meta


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    builders = [
        build_v1_pocket_kyle,
        build_v3_scissor_ballista,
        build_v4_audit_briefcase,
    ]
    manifest = {"weapons": []}
    sheet_rows = []
    for b in builders:
        m = b(OUT_ROOT)
        manifest["weapons"].append(m)
        print(f"Built {m['id']}: {m['size']} (idle={len(m['idle'])}, lock={len(m['lock'])}, fire={len(m['fire'])})")
        # Pick 6 representative crisp frames: idle_00, idle_mid/alt, idle_shut/spark, lock_active, fire_launch, fire_empty
        picks = [
            m["idle"][0],
            m["idle"][7],
            m["idle"][9 if m["id"] == "v1_pocket_kyle" else 14],
            m["lock"][2],
            m["fire"][5],
            m["fire"][10],
        ]
        row = []
        for fn in picks:
            im = Image.open(os.path.join(OUT_ROOT, m["id"], fn)).convert("RGBA")
            cell = Image.new("RGBA", (300, 250), (24, 30, 42, 255))
            im.thumbnail((286, 238), Image.Resampling.LANCZOS)
            cell.alpha_composite(im, ((300 - im.width) // 2, 250 - im.height))
            row.append(cell)
        sheet_rows.append(row)

    sheet = Image.new("RGB", (300 * 6, 250 * len(sheet_rows)), (18, 22, 32))
    for ri, row in enumerate(sheet_rows):
        for ci, cell in enumerate(row):
            sheet.paste(cell.convert("RGB"), (ci * 300, ri * 250))
    sheet_path = os.path.join(OUT_ROOT, "_audit_v2_sheet.jpg")
    sheet.save(sheet_path, quality=92)
    with open(os.path.join(OUT_ROOT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("Wrote", sheet_path)


if __name__ == "__main__":
    main()
