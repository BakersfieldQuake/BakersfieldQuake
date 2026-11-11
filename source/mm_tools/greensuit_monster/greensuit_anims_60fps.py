"""7-State x 16-Angle x 60 FPS Digitized Live-Action Monster Animation & 3D Quake Gib Engine.

Animations (all 16 compass angles every 22.5° at native 60 FPS):
  1. `cruise`          — 36 frames (0.60s): Seated Low-Rider Smirk Prowl
  2. `charge`          — 30 frames (0.50s): Screaming Ab-Roller Plank Torpedo Sprint
  3. `jump_slam`       — 54 frames (0.90s): Stainless Pipe Pole-Vault -> Crane Sky-Point Apex -> Spark-Shower Slam
  4. `whirlwind_melee` — 36 frames (0.60s): Full 360° 16-Angle Battering-Ram Tornado Swing
  5. `wheelie_taunt`   — 36 frames (0.60s): High-RPM Wheelie Burnout & Battle-Cry Rev
  6. `pain`            — 24 frames (0.40s): Heavy Impact Recoil, Blood Hit-Splat & Skid Recovery
  7. `gib_death`       — 48 frames (0.80s): Bloody Quake Mega-Gib Detonation (Bouncing Tires, Chrome Pipe & Meat)
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

from greensuit_core import (
    N_DIRS,
    SS_CX,
    SS_GROUND,
    SS_H,
    SS_W,
    alpha_over,
    bbox_of_rgba,
    detect_tire_regions_and_spin,
    draw_sparks_and_dust,
    from_premul_f32,
    make_contact_shadow,
    resize_rgba_premul,
    to_premul_f32,
)

ANIM_SPECS = [
    {"id": "cruise",          "title": "Seated Wheel-Cruise",         "frames": 36, "fps": 60, "loop": True,  "ico": "🛞", "desc": "Cheeky low-rider prowl with knees tucked high, 60 FPS ribbed tire rotation & rhythmic suspension bounce."},
    {"id": "charge",          "title": "Ab-Roller Torpedo Charge",    "frames": 30, "fps": 60, "loop": True,  "ico": "⚡", "desc": "Screaming prone plank blitz on extended arms & scrambling green toes kicking up hot friction sparks!"},
    {"id": "jump_slam",       "title": "Pipe-Vault Sky-Point Slam",   "frames": 54, "fps": 60, "loop": True,  "ico": "🚀", "desc": "Pole-vaults off the stainless center pipe into his iconic mid-air Crane-Kick Sky-Point ('OOOO!') & shockwave slam!"},
    {"id": "whirlwind_melee", "title": "360° Wheel-Bar Whirlwind",    "frames": 36, "fps": 60, "loop": True,  "ico": "🌪️", "desc": "Spins his entire digitized body through all 16 angles swinging the heavy two-wheel battering ram!"},
    {"id": "wheelie_taunt",   "title": "Wheelie Burnout Battle-Cry",  "frames": 36, "fps": 60, "loop": True,  "ico": "🔥", "desc": "Yanks back into a steep rear-tilted wheelie revving billowing tire smoke & golden sparks!"},
    {"id": "pain",            "title": "Impact Recoil & Tire Skid",   "frames": 24, "fps": 60, "loop": False, "ico": "💥", "desc": "Violent knockback jolt with crimson hit-splatter, skidding rubber tires & gritty combat recovery."},
    {"id": "gib_death",       "title": "Quake Mega-Gib Detonation",   "frames": 48, "fps": 60, "loop": False, "ico": "💀", "desc": "3D ballistic blood & meat explosion launching both bouncing pneumatic tires, clanging chrome pipe & suit shreds!"},
]


# ---------------------------------------------------------------------------
# 1. Sub-Pixel Premultiplied Kinematic Warp & FX Helpers
# ---------------------------------------------------------------------------

def warp_kinematic_rgba(
    rgba: np.ndarray,
    dx: float = 0.0,
    dy: float = 0.0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    rot_deg: float = 0.0,
    shear_top_x: float = 0.0,
    pivot: Tuple[float, float] = (SS_CX, SS_GROUND),
    wave_amp_x: float = 0.0,
    wave_amp_y: float = 0.0,
    wave_phase: float = 0.0,
) -> np.ndarray:
    """Applies smooth C1 premultiplied-alpha skeletal/postural deformation around `pivot`."""
    h, w = rgba.shape[:2]
    yy, xx = np.indices((h, w), dtype=np.float32)
    px, py = pivot

    # Inverse mapping: given output pixel (xx, yy), find source pixel (sx, sy)
    ux = xx - px - dx
    uy = yy - py - dy

    # Undo rotation
    if abs(rot_deg) > 1e-3:
        rad = math.radians(-rot_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        rx = ux * ca - uy * sa
        ry = ux * sa + uy * ca
    else:
        rx, ry = ux, uy

    # Height factor above ground pivot (0 at ground, 1 at 240px above ground)
    h_frac = np.clip(-ry / 230.0, 0.0, 1.35)
    rx = rx - shear_top_x * h_frac

    sx = rx / max(scale_x, 0.15) + px
    sy = ry / max(scale_y, 0.15) + py

    if abs(wave_amp_x) > 0.05:
        sx = sx - wave_amp_x * np.sin(h_frac * 4.2 + wave_phase) * np.clip(h_frac * 1.4, 0.0, 1.0)
    if abs(wave_amp_y) > 0.05:
        u_horiz = (sx - px) / 140.0
        sy = sy - wave_amp_y * np.sin(u_horiz * 4.5 + wave_phase) * np.clip(np.abs(u_horiz), 0.0, 1.2)

    pm = to_premul_f32(rgba)
    warped_pm = cv2.remap(pm, sx.astype(np.float32), sy.astype(np.float32), interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return from_premul_f32(warped_pm)


def blend_rgba_pair(im_a: np.ndarray, im_b: np.ndarray, w_b: float) -> np.ndarray:
    if w_b <= 0.01:
        return im_a.copy()
    if w_b >= 0.99:
        return im_b.copy()
    pma = to_premul_f32(im_a)
    pmb = to_premul_f32(im_b)
    return from_premul_f32(pma * (1.0 - w_b) + pmb * w_b)


def draw_smoke_puffs(
    canvas: np.ndarray,
    origins: List[Tuple[float, float]],
    phase_01: float,
    drift_x: float = 0.0,
    intensity: float = 1.0,
    seed: int = 19,
) -> np.ndarray:
    """Draws billowing translucent tire-burnout smoke clouds."""
    pil = Image.fromarray(canvas, "RGBA")
    ov = Image.new("RGBA", (SS_W, SS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    rng = np.random.RandomState(seed)
    n_puffs = int(round(9 * intensity))
    for ox, oy in origins:
        for i in range(n_puffs):
            p = (phase_01 * 1.8 + i / max(n_puffs, 1)) % 1.0
            px = ox + drift_x * p * 68.0 + rng.uniform(-18.0, 18.0) * p
            py = oy - p * rng.uniform(22.0, 56.0)
            rad = 9.0 + p * 26.0
            a = int(round(135 * (1.0 - p) ** 1.4 * math.sin(min(1.0, p * 4.0) * math.pi * 0.5) * min(intensity, 1.2)))
            if a > 6:
                dr.ellipse([px - rad, py - rad * 0.72, px + rad, py + rad * 0.72], fill=(212, 220, 228, a))
    pil.alpha_composite(ov)
    return np.asarray(pil, dtype=np.uint8)


def draw_whirlwind_slash_ribbons(canvas: np.ndarray, phase_01: float, cy: float = 216.0) -> np.ndarray:
    """Draws gleaming 3D elliptical silver & neon-green kinetic motion ribbons around the 360° melee spin."""
    pil = Image.fromarray(canvas, "RGBA")
    ov = Image.new("RGBA", (SS_W, SS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    env = math.sin(np.clip((phase_01 - 0.12) / 0.76, 0.0, 1.0) * math.pi)
    if env <= 0.04:
        return canvas
    for idx, (ry_off, rx, ry, col) in enumerate([
        (-18.0, 156.0, 36.0, (230, 245, 255)),
        (6.0,   168.0, 42.0, (134, 252, 88)),
        (28.0,  144.0, 32.0, (255, 214, 102)),
    ]):
        a0 = (phase_01 * 720.0 + idx * 115.0) % 360.0
        span = 145.0 * env
        alpha = int(round(195 * env))
        bbox = [SS_CX - rx, cy + ry_off - ry, SS_CX + rx, cy + ry_off + ry]
        dr.arc(bbox, start=a0, end=a0 + span, fill=(*col, alpha), width=5 - idx)
        dr.arc([bbox[0] + 5, bbox[1] + 2, bbox[2] - 5, bbox[3] - 2], start=a0 + 18, end=a0 + span * 0.75, fill=(255, 255, 255, alpha // 2), width=2)
    pil.alpha_composite(ov)
    return np.asarray(pil, dtype=np.uint8)


def draw_blood_hit_burst(canvas: np.ndarray, phase_01: float, dir_x: float) -> np.ndarray:
    """Draws visceral Quake crimson blood droplets & mist on pain flinch."""
    if phase_01 > 0.62:
        return canvas
    t = phase_01 / 0.62
    pil = Image.fromarray(canvas, "RGBA")
    ov = Image.new("RGBA", (SS_W, SS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    rng = np.random.RandomState(42)
    ox, oy = SS_CX + dir_x * 10.0, 204.0
    for i in range(18):
        ang = rng.uniform(-2.4, -0.6) + dir_x * 0.45
        spd = rng.uniform(35.0, 125.0)
        bx = ox + math.cos(ang) * spd * t + dir_x * 36.0 * t
        by = oy + math.sin(ang) * spd * t + 135.0 * (t ** 2)
        rad = max(1.5, rng.uniform(2.5, 6.2) * (1.0 - 0.55 * t))
        a = int(round(240 * (1.0 - t) ** 0.85))
        col = (185, 14, 18, a) if i % 2 == 0 else (128, 8, 12, a)
        dr.ellipse([bx - rad, by - rad, bx + rad, by + rad], fill=col)
    pil.alpha_composite(ov)
    return np.asarray(pil, dtype=np.uint8)


# ---------------------------------------------------------------------------
# 2. 3D Ballistic Quake Mega-Gib Physics Simulator (Projected to All 16 Angles!)
# ---------------------------------------------------------------------------

def precompute_3d_gib_trajectories(n_frames: int = 48) -> List[Dict]:
    """Precomputes 3D world-space trajectories `(x, y, z)` in units of pixels (`z=0` floor)
    for both pneumatic tires, the stainless bullet-nosed pipe, and 18 meat/bone/green-suit chunks!
    """
    rng = np.random.RandomState(1337)
    bodies = [
        # Two real pneumatic tires on white steel rims!
        {"kind": "tire", "x": 0.0, "y": -26.0, "z": 38.0, "vx": 42.0,  "vy": -168.0, "vz": 245.0, "rest": 0.68, "rot0": 0.0,  "omega": 11.5, "scale": 0.86},
        {"kind": "tire", "x": 0.0, "y":  26.0, "z": 38.0, "vx": -54.0, "vy":  162.0, "vz": 268.0, "rest": 0.66, "rot0": 40.0, "omega": -13.0, "scale": 0.86},
        # Mirror-polished stainless bullet-nosed center pipe!
        {"kind": "pipe", "x": 14.0, "y": 0.0,  "z": 46.0, "vx": 88.0,  "vy":  28.0,  "vz": 310.0, "rest": 0.44, "rot0": 15.0, "omega": 18.5, "scale": 0.82},
    ]
    # 18 visceral Quake meat chunks, white bone fragments & torn neon-green morphsuit rags!
    for i in range(18):
        az = (i / 18.0) * 2.0 * math.pi + rng.uniform(-0.18, 0.18)
        horiz = rng.uniform(75.0, 215.0)
        subkind = "suit_meat" if i % 3 == 0 else ("bone" if i % 5 == 0 else "meat")
        bodies.append({
            "kind": subkind,
            "x": rng.uniform(-14.0, 14.0),
            "y": rng.uniform(-14.0, 14.0),
            "z": rng.uniform(28.0, 88.0),
            "vx": math.cos(az) * horiz,
            "vy": math.sin(az) * horiz,
            "vz": rng.uniform(130.0, 320.0),
            "rest": 0.32 if subkind != "bone" else 0.48,
            "rot0": rng.uniform(0.0, 360.0),
            "omega": rng.uniform(-16.0, 16.0),
            "rad": rng.uniform(6.5, 14.5),
            "splat_r": rng.uniform(12.0, 26.0),
        })

    grav = 690.0
    dt = 1.0 / 60.0
    history: List[Dict] = []
    splats: List[Tuple[float, float, float]] = []  # (x, y, radius) on z=0 floor

    for f in range(n_frames):
        snap_bodies = []
        spark_events = []
        if f >= 5:
            for b in bodies:
                b["x"] += b["vx"] * dt
                b["y"] += b["vy"] * dt
                b["z"] += b["vz"] * dt
                b["vz"] -= grav * dt
                b["vx"] *= 0.992
                b["vy"] *= 0.992
                b["rot0"] += b["omega"] * dt * 57.2958
                if b["z"] <= 0.0:
                    b["z"] = 0.0
                    impact = abs(b["vz"])
                    b["vz"] = impact * b["rest"]
                    b["vx"] *= 0.78
                    b["vy"] *= 0.78
                    b["omega"] *= 0.72
                    if b["kind"] in ("meat", "suit_meat") and impact > 35.0 and len(splats) < 42:
                        splats.append((b["x"], b["y"], b["splat_r"]))
                    if b["kind"] == "pipe" and impact > 55.0:
                        spark_events.append((b["x"], b["y"]))
                snap_bodies.append(dict(b))
        history.append({
            "frame": f,
            "bodies": snap_bodies,
            "splats": list(splats),
            "pipe_sparks": spark_events,
        })
    return history


def _rotate_paste_rgba(dst_pil: Image.Image, part_rgba: np.ndarray, cx: float, cy: float, angle_deg: float, scale: float) -> None:
    if scale <= 0.05:
        return
    nw = max(4, int(round(part_rgba.shape[1] * scale)))
    nh = max(4, int(round(part_rgba.shape[0] * scale)))
    rs = resize_rgba_premul(part_rgba, nw, nh)
    pil_p = Image.fromarray(rs, "RGBA").rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    px = int(round(cx - pil_p.width * 0.5))
    py = int(round(cy - pil_p.height * 0.5))
    dst_pil.alpha_composite(pil_p, (px, py))


def render_gib_death_frame(
    f: int,
    n_frames: int,
    d_idx: int,
    melee_view: np.ndarray,
    gib_hist: List[Dict],
    gib_parts: Dict[str, np.ndarray],
) -> np.ndarray:
    """Renders frame `f` of the 48-frame 60 FPS Bloody Quake Mega-Gib Detonation at compass angle `d_idx`."""
    ang_rad = math.radians(d_idx * 22.5)
    ca, sa = math.cos(ang_rad), math.sin(ang_rad)

    def proj_3d(wx: float, wy: float, wz: float) -> Tuple[float, float, float]:
        # Viewer stands at azimuth `ang_rad`: camera right = (-sin, cos) or matching our turnaround chirality:
        # Check d=4 (90°): monster +x points screen-left (-1), +y points toward viewer (+depth).
        sx = SS_CX + (-wx * sa + wy * ca)
        depth = wx * ca + wy * sa
        sy = SS_GROUND - wz + depth * 0.24
        return sx, sy, depth

    # Frames 0..4: Violent bloated shock-shake & crimson core rupture right before detonation!
    if f < 5:
        t = f / 4.0
        swell_x = 1.0 + 0.14 * t + (0.03 if f % 2 == 0 else -0.03)
        swell_y = 1.0 + 0.08 * t
        shaken = warp_kinematic_rgba(melee_view, dx=(5.0 if f % 2 == 0 else -5.0), scale_x=swell_x, scale_y=swell_y)
        # Tint core warm crimson-orange right before burst
        rgb = shaken[..., :3].astype(np.float32)
        a_m = shaken[..., 3] > 20
        rgb[a_m, 0] = np.clip(rgb[a_m, 0] * (1.0 + 0.55 * t) + 45.0 * t, 0, 255)
        rgb[a_m, 1] = np.clip(rgb[a_m, 1] * (1.0 - 0.25 * t), 0, 255)
        shaken[..., :3] = np.round(rgb).astype(np.uint8)
        shadow = make_contact_shadow(185, 32, opacity=0.44)
        return alpha_over(shadow, shaken)

    state = gib_hist[f]
    t_boom = (f - 5) / float(max(1, n_frames - 6))
    pil = Image.new("RGBA", (SS_W, SS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(pil)

    # 1. Central persistent crimson blood pool + splatter puddles on ground plane
    pool_rx = min(132.0, 36.0 + t_boom * 115.0)
    pool_ry = pool_rx * 0.27
    dr.ellipse([SS_CX - pool_rx, SS_GROUND - pool_ry, SS_CX + pool_rx, SS_GROUND + pool_ry], fill=(108, 6, 10, 215))
    dr.ellipse([SS_CX - pool_rx * 0.7, SS_GROUND - pool_ry * 0.7, SS_CX + pool_rx * 0.7, SS_GROUND + pool_ry * 0.7], fill=(148, 10, 14, 235))
    for spx, spy, spr in state["splats"]:
        sx, sy, _ = proj_3d(spx, spy, 0.0)
        rx_s = spr
        ry_s = spr * 0.30
        dr.ellipse([sx - rx_s, sy - ry_s, sx + rx_s, sy + ry_s], fill=(132, 8, 12, 210))

    # 2. Initial crimson blood-mist & detonation flash (frames 5..18)
    if f < 20:
        ft = (f - 5) / 15.0
        mist_r = 42.0 + ft * 118.0
        mist_a = int(round(215 * (1.0 - ft) ** 1.3))
        dr.ellipse([SS_CX - mist_r, (SS_GROUND - 78) - mist_r * 0.85, SS_CX + mist_r, (SS_GROUND - 78) + mist_r * 0.85], fill=(175, 16, 20, mist_a))
        if f < 10:
            fl_r = 55.0 + (f - 5) * 16.0
            fl_a = int(round(230 * (1.0 - (f - 5) / 5.0)))
            dr.ellipse([SS_CX - fl_r, (SS_GROUND - 82) - fl_r, SS_CX + fl_r, (SS_GROUND - 82) + fl_r], fill=(255, 215, 130, fl_a))

    # 3. Depth-sort all 3D bodies back-to-front so occlusion between tires, pipe & meat is 100% physical!
    projected = []
    for b in state["bodies"]:
        sx, sy, depth = proj_3d(b["x"], b["y"], b["z"])
        gx, gy, _ = proj_3d(b["x"], b["y"], 0.0)
        projected.append((depth, sx, sy, gx, gy, b))
    projected.sort(key=lambda item: item[0])

    # Draw small ground shadows under airborne tires/pipe/gibs first
    for _, _, _, gx, gy, b in projected:
        sh_r = 22.0 if b["kind"] in ("tire", "pipe") else 8.0
        sh_a = int(round(max(20.0, 125.0 * math.exp(-b["z"] / 120.0))))
        dr.ellipse([gx - sh_r, gy - sh_r * 0.28, gx + sh_r, gy + sh_r * 0.28], fill=(0, 0, 0, sh_a))

    # Draw sorted 3D bodies
    for depth, sx, sy, _, _, b in projected:
        persp = np.clip(1.0 + depth / 900.0, 0.82, 1.18)
        kind = b["kind"]
        if kind == "tire":
            # Blend between circular side view and foreshortened oval view as tire tumbles!
            wobble = abs(math.sin(math.radians(b["rot0"] * 0.7 + d_idx * 22.5)))
            part = gib_parts["wheel_side"] if wobble > 0.42 else gib_parts["wheel_edge"]
            _rotate_paste_rgba(pil, part, sx, sy - 22.0, b["rot0"], b["scale"] * persp)
        elif kind == "pipe":
            _rotate_paste_rgba(pil, gib_parts["chrome_pipe"], sx, sy - 20.0, b["rot0"], b["scale"] * persp)
        else:
            r = b["rad"] * persp
            ang = math.radians(b["rot0"])
            dx_r, dy_r = math.cos(ang) * r * 1.35, math.sin(ang) * r * 0.85
            cy_b = sy - r * 0.65
            if kind == "bone":
                dr.line([(sx - dx_r, cy_b - dy_r), (sx + dx_r, cy_b + dy_r)], fill=(238, 228, 212, 255), width=max(3, int(r * 0.55)))
                dr.ellipse([sx - dx_r - 3, cy_b - dy_r - 3, sx - dx_r + 3, cy_b - dy_r + 3], fill=(205, 42, 42, 255))
            elif kind == "suit_meat":
                # Torn neon-green spandex morphsuit strip + crimson meat core!
                dr.polygon([
                    (sx - dx_r, cy_b - dy_r),
                    (sx + dy_r * 0.9, cy_b - dx_r * 0.7),
                    (sx + dx_r * 1.1, cy_b + dy_r),
                    (sx - dy_r * 0.8, cy_b + dx_r * 0.8),
                ], fill=(118, 232, 58, 255))
                dr.ellipse([sx - r * 0.55, cy_b - r * 0.55, sx + r * 0.55, cy_b + r * 0.55], fill=(168, 16, 22, 255))
            else:
                dr.ellipse([sx - r * 1.15, cy_b - r * 0.85, sx + r * 1.15, cy_b + r * 0.85], fill=(156, 12, 18, 255))
                dr.ellipse([sx - r * 0.55, cy_b - r * 0.55, sx + r * 0.35, cy_b + r * 0.25], fill=(212, 34, 38, 235))

    out = np.asarray(pil, dtype=np.uint8)
    if state["pipe_sparks"]:
        sp_pts = [proj_3d(px, py, 4.0)[:2] for px, py in state["pipe_sparks"]]
        out = draw_sparks_and_dust(out, sp_pts, phase_01=0.25, intensity=1.15, seed=f * 13 + d_idx)
    return out


# ---------------------------------------------------------------------------
# 3. Master Per-Frame Synthesizer Across All 7 States x 16 Angles @ 60 FPS
# ---------------------------------------------------------------------------

def render_monster_frame_ss(
    anim_id: str,
    d_idx: int,
    f_idx: int,
    n_frames: int,
    turnarounds: Dict[str, List[np.ndarray]],
    gib_hist: List[Dict],
    gib_parts: Dict[str, np.ndarray],
) -> np.ndarray:
    """Synthesizes a single 384x384 super-sampled RGBA frame for `(anim_id, d_idx, f_idx)`."""
    phase = f_idx / float(n_frames)
    tau = 2.0 * math.pi * phase
    ang_rad = math.radians(d_idx * 22.5)
    # Screen-space projection of monster's forward axis:
    # d=0 (0°): fwd=(0, +0.34); d=4 (90° left): fwd=(-1, 0); d=8 (180°): fwd=(0, -0.34); d=12 (270° right): fwd=(+1, 0)
    fwd_x = -math.sin(ang_rad)
    fwd_y = 0.34 * math.cos(ang_rad)
    side_sign = -1.0 if math.sin(ang_rad) >= 0.0 else 1.0
    side_mag = abs(math.sin(ang_rad))

    # 1. SEATED LOW-RIDER CRUISE (36 frames @ 60 FPS)
    if anim_id == "cruise":
        base = detect_tire_regions_and_spin(turnarounds["seated"][d_idx], d_idx, spin_angle_rad=tau * 2.0, tread_strength=1.05)
        bounce_y = -4.2 * abs(math.sin(tau))
        pump_shear = fwd_x * 6.5 * math.sin(tau) + math.cos(ang_rad) * 2.8 * math.sin(tau)
        scale_loom = 1.0 + 0.022 * math.cos(ang_rad) * math.sin(tau)
        squash = 1.0 - 0.025 * math.cos(2.0 * tau)
        rock_deg = fwd_x * 2.8 * math.sin(tau + 0.4)
        warped = warp_kinematic_rgba(
            base,
            dx=fwd_x * 2.5 * math.sin(tau),
            dy=bounce_y,
            scale_x=scale_loom / math.sqrt(squash),
            scale_y=scale_loom * squash,
            rot_deg=rock_deg,
            shear_top_x=pump_shear,
            wave_amp_x=1.8,
            wave_phase=tau,
        )
        sh_w = 220 - 46 * side_mag
        shadow = make_contact_shadow(sh_w, 34, opacity=0.42)
        out = alpha_over(shadow, warped)
        # Subtle chrome-pipe floor kiss spark when dipping lowest
        if abs(math.sin(tau)) < 0.22:
            out = draw_sparks_and_dust(
                out,
                [(SS_CX + fwd_x * 42.0, SS_GROUND - 3.0)],
                phase_01=(phase * 2.0) % 1.0,
                vel_bias=(-fwd_x, -0.4),
                intensity=0.45,
                seed=101 + d_idx,
            )
        return out

    # 2. SCREAMING AB-ROLLER PLANK TORPEDO CHARGE (30 frames @ 60 FPS)
    if anim_id == "charge":
        base = detect_tire_regions_and_spin(turnarounds["plank"][d_idx], d_idx, spin_angle_rad=tau * 3.0, tread_strength=1.25)
        surge = math.sin(tau)
        # Rapid green-socked toe scramble & ab-roller extension wave!
        warped = warp_kinematic_rgba(
            base,
            dx=fwd_x * 6.8 * surge,
            dy=-3.0 * abs(math.sin(2.0 * tau)),
            scale_x=(1.0 + 0.045 * abs(fwd_x) * surge) * (1.0 + 0.03 * math.cos(ang_rad) * surge),
            scale_y=1.0 - 0.032 * surge,
            rot_deg=fwd_x * 2.4 * math.cos(tau),
            shear_top_x=fwd_x * 8.5 * surge,
            wave_amp_x=2.6,
            wave_amp_y=4.8,
            wave_phase=2.0 * tau,
        )
        sh_w = 248 + 42 * side_mag
        shadow = make_contact_shadow(sh_w, 32, opacity=0.45)
        out = alpha_over(shadow, warped)
        out = draw_sparks_and_dust(
            out,
            [(SS_CX + fwd_x * 58.0 - 24.0 * (1.0 - side_mag), SS_GROUND - 4.0),
             (SS_CX + fwd_x * 58.0 + 24.0 * (1.0 - side_mag), SS_GROUND - 4.0)],
            phase_01=phase,
            vel_bias=(-fwd_x * 1.4, -0.5),
            intensity=1.05,
            seed=202 + d_idx,
        )
        return out

    # 3. PIPE-VAULT INTO MID-AIR CRANE-KICK SKY-POINT & AXLE SLAM (54 frames @ 60 FPS)
    if anim_id == "jump_slam":
        t = f_idx / float(n_frames - 1)
        # Phase A (f=0..8): Coil & jam stainless center pipe into floor!
        if f_idx <= 8:
            u = f_idx / 8.0
            coil_pose = blend_rgba_pair(turnarounds["seated"][d_idx], turnarounds["melee"][d_idx], min(1.0, u * 1.25))
            coil_pose = detect_tire_regions_and_spin(coil_pose, d_idx, spin_angle_rad=u * 3.0)
            sq_y = 1.0 - 0.18 * math.sin(u * math.pi * 0.85)
            sq_x = 1.0 / math.sqrt(sq_y)
            warped = warp_kinematic_rgba(coil_pose, dy=2.0, scale_x=sq_x, scale_y=sq_y, rot_deg=fwd_x * 8.0 * u)
            shadow = make_contact_shadow(226, 36, opacity=0.48)
            out = alpha_over(shadow, warped)
            if f_idx >= 4:
                out = draw_sparks_and_dust(
                    out,
                    [(SS_CX + fwd_x * 32.0, SS_GROUND - 2.0)],
                    phase_01=(f_idx - 4) / 6.0,
                    vel_bias=(0.0, -1.3),
                    intensity=1.35,
                    seed=303 + d_idx,
                    include_ring=(f_idx in (5, 6, 7)),
                )
            return out

        # Phase B (f=9..44): Ballistic Parabolic Leap -> Iconic Sky-Point Crane Apex -> Dive Tuck!
        if f_idx <= 44:
            air_u = (f_idx - 9) / 35.0  # 0.0 takeoff -> 0.5 apex -> 1.0 touchdown
            parabola = 4.0 * air_u * (1.0 - air_u)  # peaks at 1.0 when air_u=0.5
            lift_px = 68.0 * parabola + 10.0 * math.sin(air_u * math.pi)

            # Blend smoothly into `jump` for ascent+apex (air_u 0.0..0.78), then tuck into `melee` for meteor slam!
            if air_u < 0.16:
                w_jump = air_u / 0.16
                pose = blend_rgba_pair(turnarounds["melee"][d_idx], turnarounds["jump"][d_idx], w_jump)
            elif air_u <= 0.76:
                pose = detect_tire_regions_and_spin(turnarounds["jump"][d_idx], d_idx, spin_angle_rad=air_u * 16.0, tread_strength=1.1)
            else:
                w_slam = (air_u - 0.76) / 0.24
                pose = blend_rgba_pair(turnarounds["jump"][d_idx], turnarounds["melee"][d_idx], w_slam)

            # Dynamic pitch: tilt back slightly on vault ascent, upright heroic sky-point at apex, pitch nose-down on slam!
            if air_u < 0.30:
                tilt = -fwd_x * 14.0 * math.sin((air_u / 0.30) * math.pi)
            elif air_u < 0.72:
                tilt = math.sin((air_u - 0.30) * 14.0) * 3.2
            else:
                tilt = fwd_x * 18.0 * math.sin(((air_u - 0.72) / 0.28) * math.pi)

            stretch_y = 1.0 + 0.08 * (1.0 - parabola) if (air_u < 0.2 or air_u > 0.8) else (1.0 + 0.025 * math.sin(air_u * 18.0))
            warped = warp_kinematic_rgba(
                pose,
                dy=-lift_px,
                scale_x=1.0 / math.sqrt(stretch_y),
                scale_y=stretch_y,
                rot_deg=tilt,
                pivot=(SS_CX, 220.0),
                wave_amp_x=1.6,
                wave_phase=air_u * 12.0,
            )
            # Ground shadow shrinks and softens far below him so the jump height reads unmistakably!
            sh_scale = 1.0 - 0.45 * parabola
            shadow = make_contact_shadow(215 * sh_scale, 32 * sh_scale, opacity=0.42 * (1.0 - 0.58 * parabola))
            return alpha_over(shadow, warped)

        # Phase C (f=45..53): Heavy Tire-Squish Impact Shockwave & Spark-Shower Recovery!
        land_u = (f_idx - 45) / 8.0
        pose = blend_rgba_pair(turnarounds["melee"][d_idx], turnarounds["seated"][d_idx], land_u)
        pose = detect_tire_regions_and_spin(pose, d_idx, spin_angle_rad=land_u * 4.0)
        damped_sq = 1.0 - 0.21 * math.exp(-land_u * 3.2) * math.cos(land_u * math.pi * 1.5)
        warped = warp_kinematic_rgba(
            pose,
            scale_x=1.0 / math.sqrt(max(0.65, damped_sq)),
            scale_y=damped_sq,
            rot_deg=fwd_x * 5.0 * (1.0 - land_u),
        )
        shadow = make_contact_shadow(245, 38, opacity=0.50)
        out = alpha_over(shadow, warped)
        out = draw_sparks_and_dust(
            out,
            [(SS_CX, SS_GROUND - 3.0), (SS_CX - 48.0, SS_GROUND - 5.0), (SS_CX + 48.0, SS_GROUND - 5.0)],
            phase_01=land_u,
            vel_bias=(0.0, -0.9),
            intensity=1.55 * (1.0 - 0.55 * land_u),
            seed=404 + d_idx,
            include_ring=True,
        )
        return out

    # 4. 360° WHEEL-BAR WHIRLWIND BATTERING-RAM MELEE (36 frames @ 60 FPS)
    if anim_id == "whirlwind_melee":
        # Sweeps through ALL 16 real digitized turnaround angles during the tornado swing!
        if f_idx < 6:
            u = f_idx / 6.0
            spin_offset = -2.0 * math.sin(u * math.pi * 0.5)
            lunge = -0.3 * u
        elif f_idx < 30:
            u = (f_idx - 6) / 24.0
            # Ease-in-out full 16-step (360°) revolution from -2 to +16!
            ease = u * u * (3.0 - 2.0 * u)
            spin_offset = -2.0 + 18.0 * ease
            lunge = 0.6 * math.sin(u * math.pi)
        else:
            u = (f_idx - 30) / 6.0
            spin_offset = 0.0
            lunge = (1.0 - u) * 0.95

        eff_f = (d_idx + spin_offset) % N_DIRS
        d0 = int(math.floor(eff_f)) % N_DIRS
        d1 = (d0 + 1) % N_DIRS
        frac = eff_f - math.floor(eff_f)
        spun_view = blend_rgba_pair(turnarounds["melee"][d0], turnarounds["melee"][d1], frac)
        spun_view = detect_tire_regions_and_spin(spun_view, d0, spin_angle_rad=tau * 3.0, tread_strength=1.15)

        warped = warp_kinematic_rgba(
            spun_view,
            dx=fwd_x * 14.0 * lunge,
            dy=fwd_y * 8.0 * lunge - 3.0 * abs(math.sin(tau)),
            scale_x=1.0 + 0.05 * lunge,
            scale_y=1.0 - 0.03 * abs(lunge),
            rot_deg=fwd_x * 5.5 * lunge,
        )
        shadow = make_contact_shadow(232, 36, opacity=0.45)
        out = alpha_over(shadow, warped)
        out = draw_whirlwind_slash_ribbons(out, phase_01=phase, cy=212.0)
        if 7 <= f_idx <= 29:
            out = draw_sparks_and_dust(
                out,
                [(SS_CX - 64.0, 224.0), (SS_CX + 64.0, 224.0)],
                phase_01=(f_idx - 7) / 22.0,
                intensity=0.85,
                seed=505 + f_idx,
            )
        return out

    # 5. WHEELIE BURNOUT BATTLE-CRY TAUNT (36 frames @ 60 FPS)
    if anim_id == "wheelie_taunt":
        env = math.sin(phase * math.pi) ** 0.65
        # Blend seated + roaring melee expression energy
        base = blend_rgba_pair(turnarounds["seated"][d_idx], turnarounds["melee"][d_idx], 0.45 * env)
        base = detect_tire_regions_and_spin(base, d_idx, spin_angle_rad=tau * 4.0, tread_strength=1.35)
        vib = math.sin(tau * 4.0)
        wheelie_rot = -fwd_x * (16.5 * env + 2.8 * vib)
        wheelie_lift = -9.0 * env * (1.0 - 0.4 * side_mag) - 2.5 * abs(vib)
        warped = warp_kinematic_rgba(
            base,
            dx=-fwd_x * 6.0 * env + 1.8 * vib,
            dy=wheelie_lift,
            scale_x=1.0 + 0.025 * vib * env,
            scale_y=1.0 + 0.04 * env,
            rot_deg=wheelie_rot,
            shear_top_x=-fwd_x * 11.0 * env,
        )
        shadow = make_contact_shadow(218, 34, opacity=0.43)
        out = alpha_over(shadow, warped)
        smoke_pts = [(SS_CX - 54.0 * (1.0 - 0.5 * side_mag), SS_GROUND - 6.0),
                     (SS_CX + 54.0 * (1.0 - 0.5 * side_mag), SS_GROUND - 6.0)]
        out = draw_smoke_puffs(out, smoke_pts, phase_01=phase, drift_x=-fwd_x, intensity=1.15 * env, seed=606 + d_idx)
        out = draw_sparks_and_dust(out, smoke_pts, phase_01=phase, vel_bias=(-fwd_x, -0.7), intensity=1.10 * env, seed=616 + d_idx)
        return out

    # 6. HEAVY PAIN RECOIL & TIRE-SKID RECOVERY (24 frames @ 60 FPS)
    if anim_id == "pain":
        # Snaps back at f=0..5, skids/wobbles f=6..15, recovers f=16..23
        if f_idx <= 5:
            recoil = math.sin((f_idx / 5.0) * math.pi * 0.5)
        else:
            u = (f_idx - 5) / 18.0
            recoil = math.cos(u * math.pi * 0.5) * (1.0 - u)

        base = blend_rgba_pair(turnarounds["seated"][d_idx], turnarounds["melee"][d_idx], 0.65 * max(0.0, recoil))
        wobble = math.sin(phase * math.pi * 5.0) * (1.0 - phase)
        warped = warp_kinematic_rgba(
            base,
            dx=-fwd_x * 20.0 * recoil + 6.5 * wobble,
            dy=-fwd_y * 10.0 * recoil,
            scale_x=1.0 + 0.08 * recoil,
            scale_y=1.0 - 0.07 * recoil,
            rot_deg=-fwd_x * 13.5 * recoil + 5.0 * wobble,
            shear_top_x=-fwd_x * 14.0 * recoil,
        )
        # Brief crimson-white pain flash on first 3 frames
        if f_idx < 3:
            fl = (3 - f_idx) / 3.0
            rgb = warped[..., :3].astype(np.float32)
            m = warped[..., 3] > 20
            rgb[m, 0] = np.clip(rgb[m, 0] + 95.0 * fl, 0, 255)
            rgb[m, 1] = np.clip(rgb[m, 1] + 25.0 * fl, 0, 255)
            rgb[m, 2] = np.clip(rgb[m, 2] + 25.0 * fl, 0, 255)
            warped[..., :3] = np.round(rgb).astype(np.uint8)

        shadow = make_contact_shadow(224, 34, opacity=0.42)
        out = alpha_over(shadow, warped)
        out = draw_blood_hit_burst(out, phase_01=phase, dir_x=-fwd_x if abs(fwd_x) > 0.2 else 0.6)
        return out

    # 7. BLOODY QUAKE MEGA-GIB DETONATION (48 frames @ 60 FPS)
    return render_gib_death_frame(f_idx, n_frames, d_idx, turnarounds["melee"][d_idx], gib_hist, gib_parts)
