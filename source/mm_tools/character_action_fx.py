"""High-FPS (30–60 FPS) multi-animation & Mega Quake Gib Explosion engine for
QuakeGuy, Paul ('Screaming Paul'), and Dennis ('Reading Dennis') in BakersfieldQuake.

Generates:
  - 360° Run Cycle        : 8 angles x 16 frames = 128 frames
  - 360° Combat Jump      : 8 angles x 18 frames = 144 frames (crouch -> dust launch -> high tuck -> landing squash)
  - Turbo Sprint / Dash   : 24 frames (forward lean + energy speed-trails + wind streaks + boot dust)
  - Acrobatic Frontflip   : 32 frames (deep coil -> full 360° tucked mid-air somersault -> superhero shockwave landing)
  - Signature Action      : 24 frames (real high-rate video expressions & gestures + sonic shockwaves)
  - Mega Gib Explosion    : 48 frames (5-Act core overload -> HDR starburst + VFX fireball -> flying head, limbs,
                            signature props & 18 3D Quake gibs -> severed head sky-plummet & double gore bounce)
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from paul_dennis_rig import CANVAS_H, CANVAS_W, GROUND_Y, TOP_Y, alpha_over
from wheelman_fx import (
    _blit_evolving_vfx_fireball,
    _draw_hdr_starburst,
    _load_vfx_fireball_rgba,
    _paste_rotated_rgba,
    _premul_remap,
)

ACT_GROUND_Y = 588
ACT_SCALE = 0.72  # 398 px tall character -> 190 px open sky headroom above head for jumps, flips & explosions!


def _scale_anchor_feet(rgba: np.ndarray, scale: float = ACT_SCALE, dst_ground_y: int = ACT_GROUND_Y, src_ground_y: int = GROUND_Y) -> np.ndarray:
    """Scales a 480x640 character sprite around its foot anchor onto (CANVAS_W/2, dst_ground_y) with premultiplied Lanczos."""
    H, W = rgba.shape[:2]
    nw = max(2, int(round(W * scale)))
    nh = max(2, int(round(H * scale)))
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.clip(np.round(np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)), 0, 255).astype(np.uint8)
    pm_s = np.asarray(Image.fromarray(pm, "RGBA").resize((nw, nh), Image.Resampling.LANCZOS), dtype=np.float32)
    pa = pm_s[..., 3:4] / 255.0
    rgb_s = np.where(pa > 1e-3, pm_s[..., :3] / np.maximum(pa, 1e-3), 0.0)
    im_s = Image.fromarray(np.dstack([
        np.clip(np.round(rgb_s), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_s[..., 3]), 0, 255).astype(np.uint8),
    ]), "RGBA")

    ox = int(round(W * 0.5 - nw * 0.5))
    oy = int(round(dst_ground_y - src_ground_y * scale))
    stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stage.alpha_composite(im_s, (ox, oy))
    return np.asarray(stage, dtype=np.uint8)


def _deform_jump_body(
    base_scaled: np.ndarray,
    ground_y: int,
    crouch_squash: float = 0.0,
    air_tuck: float = 0.0,
    arm_lift: float = 0.0,
    lean_deg: float = 0.0,
    y_offset: float = 0.0,
) -> np.ndarray:
    """Fast vectorized C1 biomechanical deformation for crouch/squash, mid-air knee tuck, arm throw & ballistic lift."""
    H, W = base_scaled.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = W * 0.5

    # Inverse-map coordinates: start in shifted frame before y_offset
    ys = yg - y_offset
    xs = xg.copy()

    # Rotate around hip/waist pivot (cx, ground_y - 165) if lean_deg != 0
    if abs(lean_deg) > 0.05:
        rad = math.radians(-lean_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        px, py = cx, ground_y - 165.0
        dx0, dy0 = xs - px, ys - py
        xs = px + dx0 * ca - dy0 * sa
        ys = py + dx0 * sa + dy0 * ca

    # 1) Crouch / stretch anchored strictly at ground_y (crouch_squash > 0 = compress down; < 0 = launch stretch!)
    if abs(crouch_squash) > 1e-3:
        sy = 1.0 - 0.24 * crouch_squash
        sx = 1.0 + 0.09 * crouch_squash
        ys = ground_y - (ground_y - ys) / max(0.55, sy)
        # Widen slightly more in thighs/knees than head
        w_low = np.clip((ys - (ground_y - 260.0)) / 180.0, 0.25, 1.0)
        xs = cx + (xs - cx) / (1.0 + (sx - 1.0) * w_low)

    # 2) Mid-air knee & boot tuck (pulls lower legs/boots upward toward pelvis by up to +48 px!)
    if air_tuck > 1e-3:
        hip_y = ground_y - 175.0
        w_leg = 1.0 / (1.0 + np.exp(-(ys - hip_y) / 22.0))
        # Pull source y downward -> lifts boots/calves upward in destination!
        ys = ys + (48.0 * air_tuck) * w_leg
        # Slight athletic knee flare
        xs = cx + (xs - cx) / (1.0 + 0.06 * air_tuck * w_leg)

    # 3) Arm throw upward on launch / apex (outer columns |x - cx| > 34 around shoulder height)
    if abs(arm_lift) > 1e-3:
        sh_y = ground_y - 295.0
        w_arm_x = 1.0 / (1.0 + np.exp(-(np.abs(xs - cx) - 34.0) / 7.0))
        w_arm_y = np.exp(-((ys - (sh_y + 55.0)) / 78.0) ** 2)
        w_arm = w_arm_x * w_arm_y
        ys = ys + (32.0 * arm_lift) * w_arm
        xs = xs - np.sign(xs - cx) * (8.0 * arm_lift) * w_arm

    return _premul_remap(base_scaled, xs.astype(np.float32), ys.astype(np.float32))


def _draw_dust_burst(stage: Image.Image, cx: float, ground_y: float, prog_01: float, spread: float = 88.0, intensity: float = 1.0, seed: int = 11) -> None:
    if prog_01 < 0.0 or prog_01 >= 1.0:
        return
    ov = Image.new("RGBA", stage.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    rng = np.random.default_rng(seed)
    fade = (1.0 - prog_01) ** 1.35 * intensity

    # Expanding ground shockwave ring
    rx = 22.0 + spread * (prog_01 ** 0.62)
    ry = rx * 0.16
    a_ring = int(round(185.0 * fade))
    if a_ring > 6:
        dr.ellipse([cx - rx, ground_y - ry, cx + rx, ground_y + ry], outline=(232, 224, 210, a_ring), width=max(1, int(round(3.5 * (1.0 - prog_01)))))

    # Rolling left/right dust puffs
    for side in (-1.0, 1.0):
        for k in range(5):
            ang_jitter = rng.uniform(0.75, 1.28)
            px = cx + side * (14.0 + spread * 0.92 * (prog_01 ** 0.68) * ang_jitter)
            py = ground_y - 4.0 - (14.0 + 18.0 * prog_01) * rng.uniform(0.5, 1.2)
            rad = (8.0 + 16.0 * (prog_01 ** 0.55)) * rng.uniform(0.75, 1.2)
            al = int(round(145.0 * fade * rng.uniform(0.7, 1.0)))
            if al > 5:
                dr.ellipse([px - rad, py - rad * 0.72, px + rad, py + rad * 0.72], fill=(198, 190, 178, al))

    ov = ov.filter(ImageFilter.GaussianBlur(radius=1.4))
    stage.alpha_composite(ov)


def build_jump_8x18(idle_8: list[np.ndarray], run_8x16: list[list[np.ndarray]]) -> list[list[np.ndarray]]:
    """Synthesizes an 8-direction x 18-frame (144f) 360° orbitable Combat Jump sequence."""
    out_grid: list[list[np.ndarray]] = []
    N = 18

    for d in range(8):
        idle_s = _scale_anchor_feet(idle_8[d], ACT_SCALE, ACT_GROUND_Y)
        # Pick energetic mid-stride pose from run_8x16[d] to blend during airborne knee-tuck!
        stride_s = _scale_anchor_feet(run_8x16[d][12], ACT_SCALE, ACT_GROUND_Y)
        fwd_sign = -1.0 if d in (1, 2, 3) else (+1.0 if d in (5, 6, 7) else 0.0)

        row: list[np.ndarray] = []
        for f in range(N):
            stage = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            if f <= 3:
                # Anticipation coil crouch (0..3)
                u = math.sin(math.pi * (f + 1) / 4.8)
                posed = _deform_jump_body(idle_s, ACT_GROUND_Y, crouch_squash=0.95 * u, arm_lift=-0.45 * u, lean_deg=5.5 * fwd_sign * u)
                stage.alpha_composite(Image.fromarray(posed, "RGBA"))
            elif f <= 14:
                # Ballistic flight (f=4..14, apex at f=9)
                ua = (f - 3.6) / 11.4  # in (0, 1)
                parab = max(0.0, 1.0 - (2.0 * ua - 1.0) ** 2)
                lift_y = -148.0 * parab

                # Blend toward stride silhouette in mid-air for dynamic asymmetric combat knee tuck!
                w_stride = math.sin(math.pi * ua) ** 0.85
                src_mix = stride_s if w_stride > 0.55 else idle_s
                stretch = -0.42 * (1.0 - parab) if ua < 0.25 else (-0.25 * (1.0 - parab) if ua > 0.78 else 0.0)
                tuck = 0.92 * (parab ** 0.75)
                arms = 0.85 * (parab ** 0.6)
                lean = fwd_sign * (7.0 * (1.0 - 2.0 * ua))

                posed = _deform_jump_body(
                    src_mix, ACT_GROUND_Y,
                    crouch_squash=stretch, air_tuck=tuck, arm_lift=arms, lean_deg=lean, y_offset=lift_y,
                )

                # Launch dust ring (f=4..8)
                if f <= 8:
                    _draw_dust_burst(stage, CANVAS_W * 0.5, ACT_GROUND_Y, (f - 4) / 5.0, spread=86.0, intensity=1.0, seed=30 + d)

                # Subtle vertical air-whoosh streaks below boots during launch/descent
                if abs(ua - 0.5) > 0.16:
                    air_ov = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
                    adr = ImageDraw.Draw(air_ov)
                    al_w = int(round(95.0 * (1.0 - parab)))
                    for ox_w in (-26, 0, 26):
                        y0_w = ACT_GROUND_Y + lift_y + 12
                        adr.line([(240 + ox_w, y0_w), (240 + ox_w, min(ACT_GROUND_Y - 4, y0_w + 38))], fill=(210, 232, 255, al_w), width=2)
                    stage.alpha_composite(air_ov)

                stage.alpha_composite(Image.fromarray(posed, "RGBA"))
            else:
                # Heavy landing impact squash & rebound (f=15..17)
                sq_vals = [1.05, 0.52, 0.14]
                sq = sq_vals[f - 15]
                posed = _deform_jump_body(idle_s, ACT_GROUND_Y, crouch_squash=sq, arm_lift=0.25 * sq, lean_deg=4.0 * fwd_sign * sq)
                _draw_dust_burst(stage, CANVAS_W * 0.5, ACT_GROUND_Y, (f - 15) / 3.2, spread=108.0, intensity=1.15, seed=70 + d)
                stage.alpha_composite(Image.fromarray(posed, "RGBA"))

            row.append(np.asarray(stage, dtype=np.uint8))
        out_grid.append(row)
    return out_grid


def build_frontflip_32(idle_diag: np.ndarray, stride_diag: np.ndarray, accent_rgb: tuple[int, int, int]) -> list[np.ndarray]:
    """Synthesizes a 32-frame high-FPS Acrobatic 360° Frontflip Vault with tucked mid-air somersault & shockwave landing."""
    N = 32
    idle_s = _scale_anchor_feet(idle_diag, 0.70, ACT_GROUND_Y)
    stride_s = _scale_anchor_feet(stride_diag, 0.70, ACT_GROUND_Y)
    # Pre-tuck cannonball body for mid-air spin
    tucked_arr = _deform_jump_body(stride_s, ACT_GROUND_Y, air_tuck=1.18, arm_lift=0.55)
    ys_nz, xs_nz = np.nonzero(tucked_arr[..., 3] > 20)
    tuck_crop = Image.fromarray(
        tucked_arr[max(0, ys_nz.min() - 6):min(CANVAS_H, ys_nz.max() + 6), max(0, xs_nz.min() - 6):min(CANVAS_W, xs_nz.max() + 6)],
        "RGBA",
    )

    frames: list[np.ndarray] = []
    for f in range(N):
        stage = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        if f <= 4:
            # Deep coil crouch
            u = math.sin(math.pi * (f + 1) / 5.6)
            posed = _deform_jump_body(idle_s, ACT_GROUND_Y, crouch_squash=1.12 * u, arm_lift=-0.55 * u, lean_deg=-10.0 * u)
            stage.alpha_composite(Image.fromarray(posed, "RGBA"))
        elif f <= 25:
            # Airborne 360° tucked frontflip (f=5..25 -> 21 airborne frames!)
            ua = (f - 4.5) / 21.5
            parab = max(0.0, 1.0 - (2.0 * ua - 1.0) ** 2)
            lift_y = -172.0 * parab

            if f <= 10:
                _draw_dust_burst(stage, 240.0, ACT_GROUND_Y, (f - 5) / 6.0, spread=95.0, intensity=1.1, seed=101)

            # Smooth S-curve 360° forward rotation (-X facing -> counter-clockwise = negative angle in _paste_rotated_rgba)
            s_rot = ua * ua * (3.0 - 2.0 * ua)
            ang = -360.0 * s_rot
            cy_spin = (ACT_GROUND_Y - 195.0) + lift_y

            # Draw rotational motion-trail ghost & curved speed whoosh arcs during fast mid-spin
            spin_speed = 6.0 * ua * (1.0 - ua)
            if spin_speed > 0.25:
                _paste_rotated_rgba(stage, tuck_crop, 240.0, cy_spin, angle_deg=ang + 24.0 * spin_speed, alpha_mul=0.22 * spin_speed)
                whoosh = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
                wdr = ImageDraw.Draw(whoosh)
                r_w = 108.0
                a0 = int((-ang - 55) % 360)
                al_arc = int(round(150.0 * spin_speed))
                wdr.arc([240 - r_w, cy_spin - r_w, 240 + r_w, cy_spin + r_w], start=a0, end=a0 + 85, fill=(*accent_rgb, al_arc), width=4)
                wdr.arc([240 - r_w + 12, cy_spin - r_w + 12, 240 + r_w - 12, cy_spin + r_w - 12], start=a0 + 180, end=a0 + 255, fill=(255, 255, 255, int(al_arc * 0.75)), width=2)
                stage.alpha_composite(whoosh)

            if ua > 0.86:
                # Untuck cleanly into landing extension
                ext_t = (ua - 0.86) / 0.14
                posed = _deform_jump_body(idle_s, ACT_GROUND_Y, crouch_squash=-0.25 * (1.0 - ext_t), air_tuck=0.35 * (1.0 - ext_t), y_offset=lift_y)
                stage.alpha_composite(Image.fromarray(posed, "RGBA"))
            else:
                _paste_rotated_rgba(stage, tuck_crop, 240.0, cy_spin, angle_deg=ang)
        else:
            # Superhero two-boot shockwave landing & crisp recovery (f=26..31)
            u_land = (f - 26) / 5.0
            sq = math.exp(-3.2 * u_land) * 1.18
            posed = _deform_jump_body(idle_s, ACT_GROUND_Y, crouch_squash=sq, arm_lift=0.35 * sq, lean_deg=-6.0 * sq)
            _draw_dust_burst(stage, 240.0, ACT_GROUND_Y, u_land * 0.92, spread=128.0, intensity=1.35, seed=202)
            if f == 26:
                stage.alpha_composite(_draw_hdr_starburst((CANVAS_W, CANVAS_H), 240.0, ACT_GROUND_Y - 6.0, radius=62.0, intensity=0.65, n_rays=10, seed=55))
            stage.alpha_composite(Image.fromarray(posed, "RGBA"))

        frames.append(np.asarray(stage, dtype=np.uint8))
    return frames


def build_turbo_sprint_24(run_diag_16: list[np.ndarray], accent_rgb: tuple[int, int, int]) -> list[np.ndarray]:
    """Synthesizes a 24-frame ultra-fast forward-leaning Turbo Sprint with glowing speed afterimages & boot dust."""
    N = 24
    # Resample 16-frame stride smoothly to 24 frames with extra forward sprint lean (-9 deg)
    scaled_24: list[np.ndarray] = []
    for f in range(N):
        u = (f / float(N)) * 16.0
        i0 = int(math.floor(u)) % 16
        base_s = _scale_anchor_feet(run_diag_16[i0], 0.78, ACT_GROUND_Y)
        leaned = _deform_jump_body(base_s, ACT_GROUND_Y, lean_deg=-9.5, y_offset=-3.0 * abs(math.sin(2.0 * math.pi * f / N)))
        scaled_24.append(leaned)

    out: list[np.ndarray] = []
    for f in range(N):
        stage = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

        # 2 Energy-tinted speed-trail afterimages (+42 px and +21 px behind the sprinter!)
        for lag, shift_x, al_mul in ((3, 44, 0.16), (1, 22, 0.30)):
            prev = scaled_24[(f - lag) % N].astype(np.float32)
            prev[..., 0] = prev[..., 0] * 0.45 + accent_rgb[0] * 0.55
            prev[..., 1] = prev[..., 1] * 0.45 + accent_rgb[1] * 0.55
            prev[..., 2] = prev[..., 2] * 0.45 + accent_rgb[2] * 0.55
            prev[..., 3] *= al_mul
            ghost = Image.fromarray(np.clip(np.round(prev), 0, 255).astype(np.uint8), "RGBA")
            stage.alpha_composite(ghost, (shift_x, 0))

        # Kick-up dust puffs behind boots on every footstrike (f=0..5 and f=12..17)
        strike_age = (f % 12) / 6.0
        if strike_age < 1.0:
            _draw_dust_burst(stage, 268.0, ACT_GROUND_Y, strike_age, spread=58.0, intensity=0.85, seed=300 + (f // 12))

        # Horizontal supersonic speedlines
        spd_ov = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        sdr = ImageDraw.Draw(spd_ov)
        rng = np.random.default_rng(900 + f)
        for _ in range(6):
            sy = float(rng.integers(210, 565))
            sx0 = float(rng.integers(255, 370))
            slen = float(rng.integers(45, 105))
            sdr.line([(sx0, sy), (min(474.0, sx0 + slen), sy)], fill=(*accent_rgb, int(rng.integers(75, 155))), width=2)
        stage.alpha_composite(spd_ov)

        stage.alpha_composite(Image.fromarray(scaled_24[f], "RGBA"))
        out.append(np.asarray(stage, dtype=np.uint8))
    return out


# ---------------------------------------------------------------------------
# 48-Frame 5-Act Mega Quake Gib Explosion Engine (Character-Specific!)
# ---------------------------------------------------------------------------

def _paint_gore_stump(arr: np.ndarray, cx: float, cy: float, rx: float, ry: float, seed: int = 7) -> np.ndarray:
    out = arr.copy()
    H, W = out.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = np.arctan2(yg - cy, xg - cx)
    rng = np.random.default_rng(seed)
    ph1, ph2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    r_ell = np.hypot((xg - cx) / max(1.0, rx), (yg - cy) / max(1.0, ry))
    jagged = r_ell <= (1.0 + 0.18 * np.sin(4.0 * ang + ph1) + 0.12 * np.cos(7.0 * ang + ph2))
    rim = jagged & (out[..., 3] > 20)
    out[rim, 0] = 165
    out[rim, 1] = 16
    out[rim, 2] = 22
    out[rim, 3] = 255
    bone = (r_ell <= 0.36) & rim
    out[bone, :3] = [236, 226, 210]
    return out


def _extract_character_gib_parts(front_480: np.ndarray, scream_or_panic_480: np.ndarray, char_key: str) -> dict:
    """Slices real photographic Head, Left/Right Arms, Left/Right Boots+Legs, Signature Prop, and 18 3D Quake Gibs."""
    sc_front = _scale_anchor_feet(front_480, ACT_SCALE, ACT_GROUND_Y)
    sc_panic = _scale_anchor_feet(scream_or_panic_480, ACT_SCALE, ACT_GROUND_Y)

    # On scaled 480x640 (ACT_SCALE=0.72, ACT_GROUND_Y=588):
    # Head: y = 180..278, x = 202..278, padded with 8px transparent border so rotation never clips hair/chin!
    head_raw = sc_panic[180:278, 202:278].copy()
    head_raw = _paint_gore_stump(head_raw, 38.0, 88.0, 14.0, 7.0, seed=11)
    head_crop = np.pad(head_raw, ((8, 8), (8, 8), (0, 0)), mode="constant", constant_values=0)

    # Left & Right Arms: y = 272..432
    larm = sc_front[270:435, 168:214].copy()
    larm = _paint_gore_stump(larm, 36.0, 16.0, 11.0, 9.0, seed=21)
    rarm = sc_front[270:435, 266:312].copy()
    rarm = _paint_gore_stump(rarm, 10.0, 16.0, 11.0, 9.0, seed=22)

    # Left & Right Legs + Boots: y = 408..592
    lleg = sc_front[408:592, 188:240].copy()
    lleg = _paint_gore_stump(lleg, 28.0, 12.0, 15.0, 9.0, seed=31)
    rleg = sc_front[408:592, 240:292].copy()
    rleg = _paint_gore_stump(rleg, 24.0, 12.0, 15.0, 9.0, seed=32)

    # Character-specific signature prop shrapnel!
    if char_key == "quakeguy":
        # Torn QUAKE Crescent Logo Chest Scrap!
        prop1 = sc_front[286:362, 214:266].copy()
        # Dark Wayfarer Sunglasses!
        prop2 = sc_front[205:224, 218:262].copy()
    elif char_key == "dennis":
        # Crimson Red Necktie!
        prop1 = sc_front[272:358, 231:251].copy()
        # Wire-Rimmed Glasses!
        prop2 = sc_front[206:223, 219:261].copy()
    else:  # paul
        # Windowpane Checkered Shirt Collar/Placket!
        prop1 = sc_front[272:362, 224:258].copy()
        # Navy Blazer Lapel!
        prop2 = sc_front[276:356, 204:230].copy()

    # 18 Glossy Wet 3D-Shaded Quake Meat & Rib-Bone Gibs
    gibs = []
    rng = np.random.default_rng(1996 + sum(ord(c) for c in char_key))
    for gi in range(18):
        sz = int(rng.integers(18, 34))
        gim = np.zeros((sz, sz, 4), dtype=np.uint8)
        gy, gx = np.mgrid[0:sz, 0:sz].astype(np.float32)
        c = sz * 0.5
        ang = np.arctan2(gy - c, gx - c)
        rad = (sz * 0.35) * (1.0 + 0.24 * np.sin(3.0 * ang + gi) + 0.16 * np.cos(5.0 * ang + gi * 1.7))
        dist = np.hypot(gx - c, gy - c)
        inside = dist <= rad
        nx_g = (gx - c) / np.maximum(rad, 1.0)
        ny_g = (gy - c) / np.maximum(rad, 1.0)
        lit = np.clip(0.65 - 0.38 * nx_g - 0.42 * ny_g, 0.18, 1.15)
        spec_g = np.exp(-(((nx_g + 0.32) / 0.24) ** 2 + ((ny_g + 0.32) / 0.24) ** 2)) * 0.65
        gim[inside, 0] = np.clip(182.0 * lit[inside] + 75.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 1] = np.clip(18.0 * lit[inside] + 55.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 2] = np.clip(22.0 * lit[inside] + 55.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 3] = 255
        if gi % 3 == 0:
            bone_m = (np.abs(gy - c + (gx - c) * 0.4) < 2.2) & (gx > c - rad * 0.6) & (gx < c + rad * 0.95)
            gim[bone_m, :3] = [238, 228, 212]
            gim[bone_m, 3] = 255
        gibs.append(Image.fromarray(gim, "RGBA"))

    return dict(
        sc_panic=sc_panic,
        head=Image.fromarray(head_crop, "RGBA"),
        larm=Image.fromarray(larm, "RGBA"),
        rarm=Image.fromarray(rarm, "RGBA"),
        lleg=Image.fromarray(lleg, "RGBA"),
        rleg=Image.fromarray(rleg, "RGBA"),
        prop1=Image.fromarray(prop1, "RGBA"),
        prop2=Image.fromarray(prop2, "RGBA"),
        gibs=gibs,
    )


def build_mega_explosion_48(front_480: np.ndarray, panic_480: np.ndarray, char_key: str) -> list[np.ndarray]:
    """Synthesizes a 48-frame 5-Act Quake Detonation & Flying Gibs sequence."""
    W_s, H_s = CANVAS_W, CANVAS_H
    cx_s = W_s * 0.5
    ground_y = float(ACT_GROUND_Y)

    parts = _extract_character_gib_parts(front_480, panic_480, char_key)
    vfx_fb = _load_vfx_fireball_rgba()
    rng = np.random.default_rng(202611 + len(char_key) * 17)

    N = 48
    dt = 1.0 / 24.0
    GRAV = 1160.0
    DET_F = 8     # Primary core detonation
    SEC_F = 18    # Secondary mid-air prop plasma pop!

    p2_vert = parts["prop2"].height > parts["prop2"].width
    bodies = [
        dict(name="larm",  img=parts["larm"],  x=cx_s - 48.0, y=ground_y - 250.0, vx=-195.0, vy=-325.0, ang=-14.0, omg=-720.0, half_l=54.0, rad=15.0, is_vert=True,    bounce=0.42, fric=0.70, squash=0.0, active=True),
        dict(name="rarm",  img=parts["rarm"],  x=cx_s + 48.0, y=ground_y - 250.0, vx=+205.0, vy=-305.0, ang=+16.0, omg=+690.0, half_l=54.0, rad=15.0, is_vert=True,    bounce=0.42, fric=0.70, squash=0.0, active=True),
        dict(name="lleg",  img=parts["lleg"],  x=cx_s - 26.0, y=ground_y - 108.0, vx=-148.0, vy=-285.0, ang=-18.0, omg=-520.0, half_l=62.0, rad=17.0, is_vert=True,    bounce=0.36, fric=0.66, squash=0.0, active=True),
        dict(name="rleg",  img=parts["rleg"],  x=cx_s + 26.0, y=ground_y - 108.0, vx=+156.0, vy=-270.0, ang=+18.0, omg=+490.0, half_l=62.0, rad=17.0, is_vert=True,    bounce=0.36, fric=0.66, squash=0.0, active=True),
        dict(name="prop1", img=parts["prop1"], x=cx_s + 6.0,  y=ground_y - 265.0, vx=+84.0,  vy=-355.0, ang=-28.0, omg=+920.0, half_l=28.0, rad=12.0, is_vert=True,    bounce=0.30, fric=0.68, squash=0.0, active=True),
        dict(name="prop2", img=parts["prop2"], x=cx_s - 10.0, y=ground_y - 360.0, vx=-162.0, vy=-255.0, ang=0.0,   omg=-1180.0, half_l=22.0 if p2_vert else 14.0, rad=9.0, is_vert=p2_vert, bounce=0.34, fric=0.72, squash=0.0, active=True),
        # Hero severed head arcs cleanly into upper sky (apex ~y=173, zero top clipping) & bounces twice onto floor!
        dict(name="head",  img=parts["head"],  x=cx_s - 4.0,  y=ground_y - 342.0, vx=+18.0,  vy=-418.0, ang=0.0,   omg=+610.0, half_l=0.0,  rad=34.0, is_vert=False,   bounce=0.28, fric=0.66, squash=0.0, active=True),
    ]

    gibs = []
    for gi, gim in enumerate(parts["gibs"]):
        ang_g = math.radians(-165.0 + (gi / 17.0) * 150.0 + rng.uniform(-6.0, 6.0))
        spd = rng.uniform(175.0, 440.0)
        gibs.append(dict(
            img=gim, x=cx_s + rng.uniform(-20.0, 20.0), y=ground_y - rng.uniform(140.0, 280.0),
            vx=math.cos(ang_g) * spd * 0.72, vy=math.sin(ang_g) * spd,
            ang=rng.uniform(0, 360), omg=rng.uniform(-820.0, 820.0),
            rad=gim.height * 0.34, bounce=rng.uniform(0.28, 0.46), splatted=False,
        ))

    blood_drops: list[dict] = []
    sparks: list[dict] = []
    smoke_puffs: list[dict] = []
    floor_stains: list[dict] = []
    sec_xy = [cx_s, ground_y - 260.0]

    def spawn_sparks(sx, sy, count, speed_lo=100.0, speed_hi=380.0, upward_bias=-120.0):
        for _ in range(count):
            a = rng.uniform(0.0, 2.0 * math.pi)
            sp = rng.uniform(speed_lo, speed_hi)
            sparks.append(dict(
                x=float(sx), y=float(sy), vx=math.cos(a) * sp, vy=math.sin(a) * sp + upward_bias,
                life=1.0, decay=rng.uniform(1.6, 3.2), size=rng.uniform(1.6, 3.5),
            ))

    def spawn_blood(bx, by, count, speed_lo=65.0, speed_hi=340.0):
        for _ in range(count):
            a = rng.uniform(-math.pi * 0.96, -math.pi * 0.04)
            sp = rng.uniform(speed_lo, speed_hi)
            blood_drops.append(dict(
                x=float(bx + rng.uniform(-14, 14)), y=float(by + rng.uniform(-18, 18)),
                vx=math.cos(a) * sp * 0.78, vy=math.sin(a) * sp - rng.uniform(25.0, 100.0),
                r=rng.uniform(2.0, 5.0), alive=True,
            ))

    def spawn_fireball(fx, fy, count, scale_r=1.0):
        for _ in range(count):
            a = rng.uniform(0.0, 2.0 * math.pi)
            sp = rng.uniform(18.0, 165.0) * scale_r
            smoke_puffs.append(dict(
                x=float(fx + rng.uniform(-18, 18) * scale_r), y=float(fy + rng.uniform(-18, 18) * scale_r),
                vx=math.cos(a) * sp * 0.85, vy=math.sin(a) * sp * 0.65 - rng.uniform(35.0, 95.0),
                r=rng.uniform(20.0, 46.0) * scale_r, age=0.0, max_age=rng.uniform(0.55, 1.45),
            ))

    frames_out: list[np.ndarray] = []
    for f in range(N):
        stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))

        # ACT 1: Pre-Detonation Panic & Glowing Plasma Core Overload (f = 0 .. DET_F-1)
        if f < DET_F:
            ov = (f + 1) / float(DET_F)
            arr = parts["sc_panic"].astype(np.float32).copy()
            hy, hx = np.mgrid[0:H_s, 0:W_s].astype(np.float32)
            core_x, core_y = cx_s, ground_y - 255.0
            rc = np.sqrt(((hx - core_x) / 56.0) ** 2 + ((hy - core_y) / 88.0) ** 2)
            bloat = np.exp(-(rc ** 2)) * (0.26 * (ov ** 1.4) + 0.05 * math.sin(f * 3.1))
            arr = _premul_remap(arr.astype(np.uint8), (hx - (hx - core_x) * bloat).astype(np.float32), (hy - (hy - core_y) * bloat).astype(np.float32)).astype(np.float32)

            glow = np.exp(-(((hx - core_x) / (38.0 + 38.0 * ov)) ** 2 + ((hy - core_y) / (52.0 + 48.0 * ov)) ** 2)) * (arr[..., 3] > 60)
            arr[..., 0] = np.clip(arr[..., 0] + glow * 245.0 * ov, 0, 255)
            arr[..., 1] = np.clip(arr[..., 1] + glow * 168.0 * (ov ** 1.3), 0, 255)
            arr[..., 2] = np.clip(arr[..., 2] + glow * 80.0 * (ov ** 2.0), 0, 255)

            sh_x = int(round(math.sin(f * 4.2) * (1.5 + 5.5 * ov)))
            sh_y = int(round(math.cos(f * 5.4) * (1.0 + 3.5 * ov)))
            stage.alpha_composite(Image.fromarray(arr.astype(np.uint8), "RGBA"), (sh_x, sh_y))

            if f >= 2:
                fx_ov = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
                dr_o = ImageDraw.Draw(fx_ov)
                for _ in range(3 + int(7 * ov)):
                    ang_b = rng.uniform(0, 2 * math.pi)
                    pts = [(core_x + sh_x, core_y + sh_y)]
                    bx_c, by_c = float(core_x + sh_x), float(core_y + sh_y)
                    for _ in range(4):
                        ang_b += rng.uniform(-0.6, 0.6)
                        step_l = rng.uniform(14.0, 32.0) * (0.5 + 0.7 * ov)
                        bx_c += math.cos(ang_b) * step_l
                        by_c += math.sin(ang_b) * step_l
                        pts.append((bx_c, by_c))
                    dr_o.line(pts, fill=(255, 175, 45, int(220 * ov)), width=4)
                    dr_o.line(pts, fill=(255, 255, 225, int(250 * ov)), width=2)
                stage.alpha_composite(fx_ov)

            frames_out.append(np.asarray(stage, dtype=np.uint8))
            continue

        # PRIMARY DETONATION (f == DET_F)
        if f == DET_F:
            floor_stains.append(dict(x=cx_s, y=ground_y + 2.0, rx=84.0, ry=11.0, col=(24, 20, 20, 225)))
            floor_stains.append(dict(x=cx_s, y=ground_y + 1.0, rx=52.0, ry=7.0, col=(135, 12, 16, 232)))
            spawn_fireball(cx_s, ground_y - 220.0, 36, scale_r=1.25)
            spawn_blood(cx_s, ground_y - 235.0, 78, speed_lo=80.0, speed_hi=365.0)
            spawn_sparks(cx_s, ground_y - 210.0, 74, speed_lo=130.0, speed_hi=430.0, upward_bias=-140.0)

        # SECONDARY PROP DETONATION (f == SEC_F)
        p1 = bodies[4]
        if f == SEC_F:
            sec_xy[0], sec_xy[1] = p1["x"], p1["y"]
            spawn_fireball(p1["x"], p1["y"], 14, scale_r=0.70)
            spawn_sparks(p1["x"], p1["y"], 40, speed_lo=95.0, speed_hi=320.0, upward_bias=-60.0)
            p1["vx"] = -125.0
            p1["vy"] = -140.0

        # 1) Scorch crater & wet crimson pools
        fl_im = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        fdr = ImageDraw.Draw(fl_im)
        for st in floor_stains:
            fdr.ellipse([st["x"] - st["rx"], st["y"] - st["ry"], st["x"] + st["rx"], st["y"] + st["ry"]], fill=st["col"])
        stage.alpha_composite(fl_im)

        # 2) Photorealistic VFX Gasoline Fireball Plumes
        if DET_F <= f < DET_F + 22:
            _blit_evolving_vfx_fireball(stage, vfx_fb, cx_s, ground_y - 215.0, (f - DET_F) / 22.0, max_diam=310.0, rot_deg=(f - DET_F) * 4.0)
        if SEC_F <= f < SEC_F + 14:
            _blit_evolving_vfx_fireball(stage, vfx_fb, sec_xy[0], sec_xy[1], (f - SEC_F) / 14.0, max_diam=160.0, rot_deg=95.0 - (f - SEC_F) * 5.0)

        # 3) Billowing fireball -> cooling charcoal smoke
        sm_im = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        sdr = ImageDraw.Draw(sm_im)
        for sp in smoke_puffs:
            if sp["age"] >= sp["max_age"]:
                continue
            u = sp["age"] / sp["max_age"]
            rad = sp["r"] * (0.65 + 0.95 * (u ** 0.6))
            if u < 0.18:
                k = u / 0.18
                col = (255, int(252 - 42 * k), int(210 - 155 * k), int(245 - 25 * k))
            elif u < 0.42:
                k = (u - 0.18) / 0.24
                col = (int(255 - 95 * k), int(185 - 125 * k), int(48 - 22 * k), int(220 - 55 * k))
            else:
                k = (u - 0.42) / 0.58
                gv = int(56 - 24 * k)
                col = (gv + 6, gv, gv, int(165 * ((1.0 - k) ** 1.35)))
            sdr.ellipse([sp["x"] - rad, sp["y"] - rad * 0.88, sp["x"] + rad, sp["y"] + rad * 0.88], fill=col)
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            sp["vx"] *= 0.92
            sp["vy"] = sp["vy"] * 0.93 - 16.0 * dt
            sp["age"] += dt
        stage.alpha_composite(sm_im.filter(ImageFilter.GaussianBlur(radius=1.8)))

        # 4) 18 Chunky Quake Meat & Rib-Bone Gibs
        for gb in gibs:
            if f > DET_F:
                gb["vy"] += GRAV * dt
                gb["x"] += gb["vx"] * dt
                gb["y"] += gb["vy"] * dt
                gb["ang"] += gb["omg"] * dt
                if gb["y"] >= ground_y - gb["rad"]:
                    gb["y"] = ground_y - gb["rad"]
                    if abs(gb["vy"]) > 55.0:
                        gb["vy"] = -abs(gb["vy"]) * gb["bounce"]
                        gb["vx"] *= 0.62
                        gb["omg"] *= 0.55
                        if not gb["splatted"]:
                            gb["splatted"] = True
                            floor_stains.append(dict(x=gb["x"], y=ground_y + rng.uniform(-2, 4), rx=rng.uniform(10, 22), ry=rng.uniform(2.5, 5.0), col=(int(rng.integers(115, 165)), 10, 14, 215)))
                            spawn_blood(gb["x"], ground_y - 4.0, 4, speed_lo=35.0, speed_hi=110.0)
                    else:
                        gb["vy"] = 0.0
                        gb["vx"] *= 0.70
                        gb["omg"] *= 0.50
                gb["x"] = float(np.clip(gb["x"], 22.0, W_s - 22.0))
            _paste_rotated_rgba(stage, gb["img"], gb["x"], gb["y"], gb["ang"], max_bottom_y=ground_y + 4)

        # 5) Hero Photographic Limbs, Signature Props & Sky-Plummeting Severed Head
        for bd in bodies:
            if f > DET_F:
                bd["vy"] += GRAV * dt
                bd["x"] += bd["vx"] * dt
                bd["y"] += bd["vy"] * dt
                bd["ang"] += bd["omg"] * dt
                bd["squash"] *= 0.52

                if bd["name"] == "head" and bd["y"] < ground_y - 45 and (f % 2 == 0):
                    blood_drops.append(dict(x=bd["x"], y=bd["y"] + 18, vx=rng.uniform(-24, 24), vy=22.0, r=3.2, alive=True))

                rad_a = math.radians(bd["ang"])
                vert_proj = abs(math.cos(rad_a)) if bd["is_vert"] else abs(math.sin(rad_a))
                eff_ry = bd["rad"] + bd["half_l"] * vert_proj * 0.62
                if bd["y"] >= ground_y - eff_ry:
                    bd["y"] = ground_y - eff_ry
                    if bd["half_l"] > 0.0:
                        if bd["is_vert"]:
                            # Tall vertical limb/prop crops tip toward horizontal (+/-90 deg) when striking ground!
                            bd["omg"] = bd["omg"] * 0.42 + math.sin(2.0 * rad_a) * 440.0
                            rem = (bd["ang"] % 180.0) - 90.0
                            if abs(rem) > 80.0 and abs(bd["omg"]) < 90.0:
                                bd["omg"] += 220.0 if bd["vx"] >= 0.0 else -220.0
                            if abs(bd["vy"]) <= 62.0:
                                bd["ang"] -= rem * 0.54
                                bd["omg"] *= 0.26
                        else:
                            # Wide horizontal prop crops (sunglasses/glasses) settle toward 0/180 deg!
                            bd["omg"] = bd["omg"] * 0.42 - math.sin(2.0 * rad_a) * 380.0
                            if abs(bd["vy"]) <= 62.0:
                                rem = ((bd["ang"] + 90.0) % 180.0) - 90.0
                                bd["ang"] -= rem * 0.54
                                bd["omg"] *= 0.26
                    if abs(bd["vy"]) > 52.0:
                        bd["vy"] = -abs(bd["vy"]) * bd["bounce"]
                        bd["vx"] *= bd["fric"]
                        bd["squash"] = 0.22
                        floor_stains.append(dict(x=bd["x"], y=ground_y + 2.0, rx=22.0, ry=4.5, col=(145, 12, 16, 228)))
                        spawn_blood(bd["x"], ground_y - 4.0, 9, speed_lo=45.0, speed_hi=155.0)
                    else:
                        bd["vy"] = 0.0
                        bd["vx"] *= 0.68
                        if bd["name"] == "head":
                            bd["omg"] = 0.0
                            rem_h = ((bd["ang"] + 180.0) % 360.0) - 180.0
                            bd["ang"] = rem_h * 0.46
                if bd["x"] < 38.0:
                    bd["x"] = 38.0; bd["vx"] = abs(bd["vx"]) * 0.52
                elif bd["x"] > W_s - 38.0:
                    bd["x"] = W_s - 38.0; bd["vx"] = -abs(bd["vx"]) * 0.52
                if bd["y"] < 42.0:
                    bd["y"] = 42.0; bd["vy"] = abs(bd["vy"]) * 0.35

            _paste_rotated_rgba(stage, bd["img"], bd["x"], bd["y"], bd["ang"], sx=1.0 + bd["squash"], sy=1.0 - bd["squash"] * 0.78, max_bottom_y=ground_y + 5)

        # 6) Blood streaks, hot sparks, supersonic shockwaves & HDR starburst!
        fx_f = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        xdr = ImageDraw.Draw(fx_f)
        for dp in blood_drops:
            if not dp["alive"]:
                continue
            x0_b, y0_b = dp["x"], dp["y"]
            dp["vy"] += GRAV * 0.92 * dt
            dp["x"] += dp["vx"] * dt
            dp["y"] += dp["vy"] * dt
            if dp["y"] >= ground_y:
                dp["alive"] = False
                floor_stains.append(dict(x=dp["x"], y=ground_y + rng.uniform(-1.5, 3.5), rx=dp["r"] * 2.2, ry=dp["r"] * 0.65, col=(135, 11, 15, 200)))
                continue
            rb = dp["r"]
            xdr.line([(x0_b, y0_b), (dp["x"], dp["y"])], fill=(185, 16, 22, 225), width=max(2, int(round(rb * 1.3))))
            xdr.ellipse([dp["x"] - rb, dp["y"] - rb, dp["x"] + rb, dp["y"] + rb], fill=(215, 24, 30, 240))

        for spk in sparks:
            if spk["life"] <= 0.0:
                continue
            x0_s, y0_s = spk["x"], spk["y"]
            spk["vy"] += GRAV * 0.55 * dt
            spk["x"] += spk["vx"] * dt
            spk["y"] += spk["vy"] * dt
            if spk["y"] >= ground_y:
                spk["y"] = ground_y; spk["vy"] = -abs(spk["vy"]) * 0.45; spk["vx"] *= 0.75
            spk["life"] -= spk["decay"] * dt
            al = int(round(max(0.0, min(1.0, spk["life"])) * 255.0))
            if al > 8:
                xdr.line([(x0_s, y0_s), (spk["x"], spk["y"])], fill=(255, int(150 + 100 * max(0, spk["life"])), 60, al), width=max(1, int(round(spk["size"]))))
                xdr.ellipse([spk["x"] - 1.5, spk["y"] - 1.5, spk["x"] + 1.5, spk["y"] + 1.5], fill=(255, 250, 210, al))

        if DET_F <= f <= DET_F + 5:
            k_sh = (f - DET_F) / 5.0
            r_sh = 34.0 + k_sh * 210.0
            a_sh = int(round((1.0 - k_sh) * 235.0))
            cy_sh = ground_y - 220.0
            xdr.ellipse([cx_s - r_sh, cy_sh - r_sh * 0.78, cx_s + r_sh, cy_sh + r_sh * 0.78], outline=(255, 242, 185, a_sh), width=max(2, int(round(7 * (1.0 - k_sh)))))

        stage.alpha_composite(fx_f)

        if DET_F <= f <= DET_F + 2:
            k_fl = (f - DET_F) / 3.0
            stage.alpha_composite(_draw_hdr_starburst((W_s, H_s), cx_s, ground_y - 220.0, radius=145.0 * (1.0 - 0.25 * k_fl), intensity=1.18 * (1.0 - k_fl), n_rays=16, seed=40 + f))
        elif SEC_F <= f <= SEC_F + 1:
            k_fl2 = (f - SEC_F) / 2.0
            stage.alpha_composite(_draw_hdr_starburst((W_s, H_s), sec_xy[0], sec_xy[1], radius=68.0 * (1.0 - 0.25 * k_fl2), intensity=0.95 * (1.0 - k_fl2), n_rays=10, seed=90 + f))

        frames_out.append(np.asarray(stage, dtype=np.uint8))

    return frames_out


def overlay_sonic_scream_rings(rgba: np.ndarray, frame_idx: int, total_frames: int = 24) -> np.ndarray:
    """Adds subtle acoustic shockwave arcs & vibrato shake on peak 'PAAAAUUUUUL!' scream frames."""
    if frame_idx < 14:
        return rgba
    inten = min(1.0, (frame_idx - 13) / float(max(1, total_frames - 14)))
    stage = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    shx = int(round(math.sin(frame_idx * 4.5) * 2.5 * inten))
    shy = int(round(math.cos(frame_idx * 5.7) * 1.5 * inten))
    stage.alpha_composite(Image.fromarray(rgba, "RGBA"), (shx, shy))

    ov = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    mx, my = 240.0 + shx, 114.0 + shy
    phase = (frame_idx * 0.28) % 1.0
    for k in range(3):
        u = (phase + k / 3.0) % 1.0
        r = 28.0 + 98.0 * u
        al = int(round(175.0 * inten * (1.0 - u) ** 1.3))
        if al > 8:
            w = max(1, int(round(3.2 * (1.0 - u))))
            # Left & right acoustic shockwave arcs outside Paul's face
            dr.arc([mx - r, my - r * 0.78, mx + r, my + r * 0.78], start=142, end=218, fill=(255, 195, 110, al), width=w)
            dr.arc([mx - r, my - r * 0.78, mx + r, my + r * 0.78], start=-38, end=38, fill=(255, 195, 110, al), width=w)
    stage.alpha_composite(ov)
    return np.asarray(stage, dtype=np.uint8)
