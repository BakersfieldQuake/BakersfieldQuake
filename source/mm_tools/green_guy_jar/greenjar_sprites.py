"""60 FPS Optical-Glass Weapon Sprite, Tumbling Jar Projectile, Green-Smoke Fireball Ignition,
and 12-Gremlin Wall-Climb / Face-Swarm / Helium-Spin / Rainbow-Confetti-Pop Synthesizer!

Generates:
  1. First-Person Weapon Viewmodel (`v_greenjar`):
     - `idle`   (180 frames @ 60 FPS = 3.0s seamless 4-antic spaz loop; 72 skins for DarkPlaces `v_greenjar.md3`)
         Antic 0 (0..44):   Hamster-Wheel Glass-Wall Climb & Ceiling Lid-Bonk Flip!
         Antic 1 (45..89):  Squished-Face Front-Glass Slam & Breath-Fog Halo ("HEHEHE / AAAAH!")!
         Antic 2 (90..134): Hyper Pogo Sky-Point Bounce ("OOOO!") rattling the perforated stainless lid!
         Antic 3 (135..179): 360° Whirlwind Tornado Spaz inside swirling green mist + full-hand jitter!
     - `shake`  (24 frames @ 60 FPS = 0.40s cocktail-shaker windup, loopable while holding Fire!)
     - `throw`  (18 frames @ 60 FPS = 0.30s high cock-back -> cross-screen whip -> splayed open-gauntlet release!)
     - `reload` (18 frames @ 60 FPS = 0.30s belt-snatch fresh rattling jar raise & elastic settle!)
  2. Thrown Tumbling Glass Jar Projectile (`proj_jar`: 24 frames @ 60 FPS; 16 frames `.spr32`)
  3. Shattering Glass & Igniting Neon-Green Smoke Fireball (`smoke_burst`: 36 frames @ 60 FPS; 14 frames `.spr32`)
  4. Mini-Green-Guy Gremlin (`mini_gremlin`: 60 FPS WebP sheets + DarkPlaces `progs/greenguy_mini.spr32`):
     - `scurry`     (16 angles x 12 frames): Hyper-speed Ab-Roller / Low-Rider floor & ankle orbit!
     - `wall_climb` (16 angles x 12 frames): 85°-tilted vertical building/wall climber with green tire sparks!
     - `pogo_jump`  (16 angles x 12 frames): Weightless rubber-flea Crane-Kick Sky-Point face-blocking bounce!
     - `shot_spin`  (24 frames): 1-Hit Punctured-Helium-Balloon 360°x720° cartwheel pinwheel spin + mist jet!
     - `balloon_pop`(24 frames): 1.55x spherical balloon swell -> crisp shock-ring + 65 3D rainbow confetti streamers!
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
GS_DIR = os.path.abspath(os.path.join(HERE, "..", "greensuit_monster"))
if GS_DIR not in sys.path:
    sys.path.insert(0, GS_DIR)

from greensuit_core import (
    N_DIRS,
    alpha_over,
    bbox_of_rgba,
    from_premul_f32,
    harmonize_green_suit_and_contrast,
    key_magenta_plate,
    resize_rgba_premul,
    to_premul_f32,
)
from greensuit_turnarounds import build_all_16_turnarounds


def rotate_scale_translate_rgba(
    rgba: np.ndarray,
    angle_deg: float,
    scale_x: float,
    scale_y: float,
    dx: float,
    dy: float,
    pivot: Tuple[float, float],
    out_hw: Tuple[int, int],
) -> np.ndarray:
    """Premultiplied-alpha 2D scale + rotation + translation around `pivot` onto `out_hw=(H, W)`."""
    out_h, out_w = out_hw
    px, py = pivot
    rad = math.radians(angle_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    m00 = c * scale_x
    m01 = -s * scale_y
    m02 = px + dx - m00 * px - m01 * py
    m10 = s * scale_x
    m11 = c * scale_y
    m12 = py + dy - m10 * px - m11 * py
    M = np.array([[m00, m01, m02], [m10, m11, m12]], dtype=np.float32)
    pm = to_premul_f32(rgba)
    interp = cv2.INTER_AREA if (scale_x < 0.85 and scale_y < 0.85) else cv2.INTER_LINEAR
    warped = cv2.warpAffine(
        pm,
        M,
        (out_w, out_h),
        flags=interp,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return from_premul_f32(warped)

PLATES_DIR = os.path.join(HERE, "studio_plates")
WORK_DIR = os.path.join(HERE, "work")

# Viewmodel output resolution (matches Pickle Surprise aspect ratio cleanly, crisp in HTML & DarkPlaces)
VM_SS_W = 540
VM_SS_H = 580
VM_OUT_W = 360
VM_OUT_H = 386


def _load_plate_rgba(fn: str, harmonize_green: bool = False) -> np.ndarray:
    p = os.path.join(PLATES_DIR, fn)
    rgba = key_magenta_plate(p)
    if harmonize_green:
        rgba = harmonize_green_suit_and_contrast(rgba, ref_green_luma=192.0)
    return rgba


class JarGauntletRig:
    """Decomposes `jar_gauntlet_grip.jpg` and `jar_gauntlet_open.jpg` into optical layers:
      - Back glass + perforated stainless lid + back gauntlet/vambrace
      - Cylindrical interior cavity mask + barrel refraction LUT
      - Front glass Fresnel specular reflection layer + wrapped front leather/bronze fingers
      - Extracted standalone glass jar (without hand) for the tumbling thrown projectile!
    """

    def __init__(self, turns_16: Dict[str, List[np.ndarray]]) -> None:
        self.turns = turns_16
        grip_1k = _load_plate_rgba("jar_gauntlet_grip.jpg", harmonize_green=False)
        open_1k = _load_plate_rgba("jar_gauntlet_open.jpg", harmonize_green=False)
        self.squish_grin = _load_plate_rgba("greenguy_glass_squish_grin.jpg", harmonize_green=True)
        self.squish_scream = _load_plate_rgba("greenguy_glass_squish_scream.jpg", harmonize_green=True)

        # Fit 1024x1024 plates onto VM_SS_W x VM_SS_H with headroom above lid AND extended vambrace at bottom-right
        # so violent cocktail-shaking & high cock-back never clip the lid at top or show a cut wrist edge!
        pad_top, pad_br = 56, 72
        def _pad_plate(p1k: np.ndarray) -> np.ndarray:
            padded = np.zeros((1024 + pad_top + pad_br, 1024 + pad_br, 4), dtype=np.uint8)
            padded[pad_top:pad_top + 1024, :1024] = p1k
            # Extrapolate bottom-right diagonal vambrace cleanly into the pad_br margin
            for k in range(1, pad_br + 1):
                sx_e = min(1023, max(0, 1024 - k))
                padded[pad_top + 1024 + k - 1, k:1024 + k] = p1k[1023, :1024]
                padded[pad_top:pad_top + 1024, 1024 + k - 1] = p1k[:, 1023]
            crop = padded[16:16 + 1068, 128:128 + 968]
            return resize_rgba_premul(crop, VM_SS_W, VM_SS_H)

        self.grip_ss = _pad_plate(grip_1k)
        self.open_ss = _pad_plate(open_1k)

        # Measure exact upright glass jar geometry on VM_SS_W x VM_SS_H
        a = self.grip_ss[..., 3] > 128
        rgb = self.grip_ss[..., :3].astype(np.float32)

        # Upper-mid jar section (y = 135..245 in 580px height) has ONLY the glass cylinder!
        mid_band = a[135:245, :]
        xs_jar = np.where(mid_band.mean(axis=0) > 0.5)[0]
        self.jx0 = int(xs_jar[0])
        self.jx1 = int(xs_jar[-1])
        self.j_cx = 0.5 * (self.jx0 + self.jx1)
        self.j_rad = 0.5 * (self.jx1 - self.jx0)

        col_mid = np.where(a[:, int(self.j_cx)])[0]
        self.lid_y0 = int(col_mid[0])
        # Perforated stainless lid spans roughly top 50px of the jar
        self.lid_y1 = self.lid_y0 + int(round(0.088 * VM_SS_H))
        # Bottom of the glass jar sits around y = 746 in original 1024 -> (746 + pad_top - 16) * VM_SS_H / 1068
        self.jar_y1 = int(round((746 + pad_top - 16) * VM_SS_H / 1068.0))

        yy, xx = np.indices((VM_SS_H, VM_SS_W), dtype=np.float32)
        self.yy = yy
        self.xx = xx

        # Smooth rounded-bottom cylinder cavity mask (inside the thick glass walls)
        wall_pad = 8.0
        in_x = np.abs(xx - self.j_cx) <= (self.j_rad - wall_pad)
        # Elliptical bottom cap curve
        bot_curve = 8.0 * np.sqrt(np.clip(1.0 - ((xx - self.j_cx) / max(1.0, self.j_rad - wall_pad)) ** 2, 0.0, 1.0))
        in_y = (yy >= self.lid_y1 + 2) & (yy <= (self.jar_y1 - 12 + bot_curve))
        cavity_raw = in_x & in_y & a
        self.cavity_alpha = cv2.GaussianBlur(cavity_raw.astype(np.float32), (5, 5), 1.1)

        # Separate wrapped FRONT leather/skin/bronze fingers from neutral smoked-glass!
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        warmness = (r - b) + 0.5 * (r - g)
        # Wrapped left-side fingertips (x < jx0 + 34, y > lid_y1 + 135) have strong warm leather/skin tone
        front_fingers = (
            a
            & (yy > self.lid_y1 + 135)
            & (xx < self.jx0 + 34.0)
            & (warmness > 20.0)
            & (luma > 26.0)
        )
        front_fingers = ndimage.binary_closing(front_fingers, structure=np.ones((5, 5), bool))
        self.front_finger_alpha = cv2.GaussianBlur(front_fingers.astype(np.float32), (3, 3), 0.7)

        # Back palm/thumb silhouette visible dimly BEHIND the lower glass: warm pixels on right/bottom inside cavity
        back_hand_behind_glass = (
            cavity_raw
            & (~front_fingers)
            & (yy > self.lid_y1 + 130)
            & (warmness > 14.0)
        )
        self.back_hand_alpha = cv2.GaussianBlur(back_hand_behind_glass.astype(np.float32), (5, 5), 1.2)

        # Pure smoked-glass interior window (where background refracts through!)
        pure_glass_win = cavity_raw & (~front_fingers) & (~back_hand_behind_glass)
        self.glass_win_mask = cv2.GaussianBlur(pure_glass_win.astype(np.float32), (5, 5), 1.0)

        # Specular glass highlight layer (excess neutral brightness above median smoked-glass luma ~78)
        spec_excess = np.clip((luma - 84.0) / 155.0, 0.0, 1.0) * np.clip(1.0 - warmness / 28.0, 0.0, 1.0)
        spec_in_jar = spec_excess * np.clip(
            ((xx >= self.jx0) & (xx <= self.jx1) & (yy >= self.lid_y1) & (yy <= self.jar_y1)).astype(np.float32),
            0.0,
            1.0,
        )
        self.glass_spec = spec_in_jar

        # Build base backplate with genuinely translucent clear-smoked glass window (alpha ~0.38 in clear window!)
        self.base_back_rgba = self.grip_ss.copy().astype(np.float32)
        orig_a = self.base_back_rgba[..., 3] / 255.0
        translucent_a = orig_a * (1.0 - 0.62 * self.glass_win_mask * (1.0 - 0.75 * self.glass_spec))
        self.base_back_rgba[..., 3] = np.clip(translucent_a * 255.0, 0.0, 255.0)

        # Precompute normalized cylindrical coordinates u_x in [-1, 1], u_y in [0, 1] for fast 60 FPS mist + refraction
        self.u_x = (xx - self.j_cx) / max(1.0, self.j_rad - wall_pad)
        self.u_y = (yy - self.lid_y1) / max(1.0, float(self.jar_y1 - self.lid_y1))

        # Precompute standalone pure Glass Jar sprite (without hand!) for `proj_jar`
        self.standalone_jar = self._extract_standalone_jar()

        # Pre-crop squish character plates cleanly for Antic 2
        self.squish_grin_crop = self._prep_squish_plate(self.squish_grin)
        self.squish_scream_crop = self._prep_squish_plate(self.squish_scream)

    def _prep_squish_plate(self, rgba: np.ndarray) -> np.ndarray:
        x0, y0, x1, y1 = bbox_of_rgba(rgba, 20)
        crop = rgba[y0:y1, x0:x1]
        tw = int(round((self.j_rad - 6) * 1.92))
        th = int(round(crop.shape[0] * (tw / max(1.0, float(crop.shape[1])))))
        return resize_rgba_premul(crop, tw, min(th, int(self.jar_y1 - self.lid_y1 - 8)))

    def _extract_standalone_jar(self) -> np.ndarray:
        """Builds a clean 220x220 standalone Specimen Glass Jar (lid + clear glass cylinder) for thrown projectile."""
        jc_w = int(self.jx1 - self.jx0 + 24)
        jc_h = int(self.jar_y1 - self.lid_y0 + 24)
        ox = max(0, self.jx0 - 12)
        oy = max(0, self.lid_y0 - 12)
        sub = self.grip_ss[oy:oy + jc_h, ox:ox + jc_w].copy().astype(np.float32)

        # Replace lower warm hand pixels inside the jar silhouette with mirrored upper clean glass!
        sh, sw = sub.shape[:2]
        s_yy, s_xx = np.indices((sh, sw), dtype=np.float32)
        cx_loc = self.j_cx - ox
        rad_loc = self.j_rad
        lid_bot_loc = self.lid_y1 - oy
        bot_loc = self.jar_y1 - oy

        in_cyl = (
            (np.abs(s_xx - cx_loc) <= rad_loc)
            & (s_yy >= (self.lid_y0 - oy))
            & (s_yy <= bot_loc)
        )
        # Clean upper glass template row (around y = lid_bot_loc + 45, completely hand-free!)
        ref_row_rgb = np.median(sub[lid_bot_loc + 25:lid_bot_loc + 85, :, :3], axis=0)
        warm = (sub[..., 0] - sub[..., 2]) + 0.5 * (sub[..., 0] - sub[..., 1])
        hand_px = (s_yy > lid_bot_loc + 95) & ((warm > 12.0) | (~in_cyl))

        # Outside cylinder below lid -> alpha = 0; inside lower cylinder -> crystal-clear upper glass profile!
        outside_jar = (s_yy > lid_bot_loc) & (np.abs(s_xx - cx_loc) > rad_loc)
        sub[outside_jar, 3] = 0.0
        sub[outside_jar, :3] = 0.0

        fill_glass = in_cyl & (s_yy > lid_bot_loc + 82) & (s_yy < bot_loc - 6)
        for c in range(3):
            row_broadcast = np.broadcast_to(ref_row_rgb[None, :, c], (sh, sw))
            sub[..., c] = np.where(fill_glass, row_broadcast, sub[..., c])

        # Bottom curved rim highlight
        rim_band = in_cyl & (np.abs(s_yy - (bot_loc - 6)) < 5.0)
        sub[rim_band, :3] = np.clip(sub[rim_band, :3] * 1.35 + 38.0, 0.0, 255.0)
        # Make glass interior translucent
        interior = in_cyl & (s_yy > lid_bot_loc + 4) & (s_yy < bot_loc - 8) & (np.abs(s_xx - cx_loc) < rad_loc - 6)
        sub[interior, 3] = np.clip(sub[interior, 3] * 0.46, 0.0, 255.0)

        sq = max(jc_w, jc_h) + 20
        canvas = np.zeros((sq, sq, 4), dtype=np.uint8)
        px = (sq - sw) // 2
        py = (sq - sh) // 2
        canvas[py:py + sh, px:px + sw] = np.clip(np.round(sub), 0, 255).astype(np.uint8)
        return resize_rgba_premul(canvas, 220, 220)

    def _synth_mist_layers(self, phase: float, intensity: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """Generates animated 60 FPS swirling volumetric neon-green mist (back_mist_rgba, front_mist_rgba)
        plus rising plasma wisps venting out of the perforated lid holes!
        """
        ux = self.u_x
        uy = self.u_y
        cav = self.cavity_alpha

        # Multi-frequency swirling plasma vortex inside the cylinder
        ang = phase * 2.0 * math.pi
        w1 = np.sin(ux * 3.4 + np.sin(uy * 4.2 - ang) * 1.4 + ang)
        w2 = np.cos(uy * 5.6 - ang * 2.0 + np.cos(ux * 2.8 + ang) * 1.3)
        w3 = np.sin((ux * 2.2 - uy * 3.8) * 2.1 + ang * 3.0)
        swirl = np.clip(0.50 + 0.24 * w1 + 0.18 * w2 + 0.14 * w3, 0.0, 1.0)

        # Denser near bottom & glass walls, glowing core
        radial_fade = np.clip(1.08 - 0.32 * (ux ** 2), 0.0, 1.0)
        density_back = np.clip(swirl * radial_fade * (0.58 + 0.35 * uy) * intensity, 0.0, 1.0) * cav

        back_rgba = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.uint8)
        back_rgba[..., 0] = np.clip(38.0 + 95.0 * swirl * intensity, 0, 255).astype(np.uint8)
        back_rgba[..., 1] = np.clip(185.0 + 70.0 * swirl * intensity, 0, 255).astype(np.uint8)
        back_rgba[..., 2] = np.clip(24.0 + 58.0 * (swirl ** 2) * intensity, 0, 255).astype(np.uint8)
        back_rgba[..., 3] = np.clip(density_back * 175.0, 0, 235).astype(np.uint8)

        # Front wisps + venting mist puffs rising out of the perforated stainless lid!
        w_front = np.clip(0.45 + 0.35 * np.sin(ux * 4.8 - ang * 2.0) * np.cos(uy * 6.5 - ang * 3.0), 0.0, 1.0)
        edge_fresnel = np.clip((np.abs(ux) - 0.55) / 0.45, 0.0, 1.0) ** 1.5
        front_in = cav * np.clip((0.20 * w_front + 0.32 * edge_fresnel) * intensity, 0.0, 0.85)

        # Lid vent plumes above lid_y0!
        vent_y = (self.lid_y0 - self.yy) / 48.0
        in_vent = (vent_y >= -0.12) & (vent_y <= 1.0) & (np.abs(ux) <= 0.78)
        vent_wave = np.sin(ux * 9.5 + np.sin(vent_y * 5.0 - ang * 2.0)) * 0.5 + 0.5
        vent_a = np.where(
            in_vent,
            np.clip((1.0 - np.clip(vent_y, 0.0, 1.0)) ** 1.6 * vent_wave * 0.42 * intensity, 0.0, 0.72),
            0.0,
        )

        tot_front_a = np.clip(front_in + vent_a, 0.0, 0.90)
        front_rgba = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.uint8)
        front_rgba[..., 0] = np.clip(95.0 + 95.0 * w_front, 0, 255).astype(np.uint8)
        front_rgba[..., 1] = 250
        front_rgba[..., 2] = np.clip(65.0 + 75.0 * w_front, 0, 255).astype(np.uint8)
        front_rgba[..., 3] = np.clip(tot_front_a * 255.0, 0, 255).astype(np.uint8)
        return back_rgba, front_rgba

    def _refract_inside_cylinder(self, char_canvas: np.ndarray) -> np.ndarray:
        """Applies optical cylindrical glass barrel refraction across the jar width & clips cleanly to cavity!"""
        ux = self.u_x
        inside = np.abs(ux) < 1.02
        # Cylindrical barrel lens curve: magnifies center slightly and compresses edges toward glass wall!
        u_src = np.where(inside, np.arcsin(np.clip(ux, -0.98, 0.98)) / (0.5 * math.pi), ux)
        map_x = (self.j_cx + u_src * max(1.0, self.j_rad - 8.0)).astype(np.float32)
        map_y = self.yy.astype(np.float32)

        premul = char_canvas.astype(np.float32)
        a_f = premul[..., 3:4] / 255.0
        premul[..., :3] *= a_f
        warped = cv2.remap(premul, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        wa = warped[..., 3:4] / 255.0
        rgb = np.where(wa > 1e-4, warped[..., :3] / np.maximum(wa, 1e-4), 0.0)
        # Clip cleanly to inside of the jar cavity + subtle green internal light tint!
        rgb[..., 1] = np.clip(rgb[..., 1] * 1.06 + 8.0, 0.0, 255.0)
        final_a = np.clip(warped[..., 3] * self.cavity_alpha, 0.0, 255.0)
        out = np.zeros_like(char_canvas)
        out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
        out[..., 3] = np.round(final_a).astype(np.uint8)
        out[out[..., 3] == 0, :3] = 0
        return out

    def render_held_jar_frame_ss(
        self,
        antic_mode: str,
        sub_t: float,
        global_phase: float,
        mist_intensity: float = 1.0,
    ) -> Tuple[np.ndarray, float, float, float]:
        """Renders one 540x580 frame of the held glass jar + spazzing Green-Suit Guy inside, returning
        `(rgba_ss, jar_jolt_dx, jar_jolt_dy, jar_jolt_deg)`.
        """
        back_mist, front_mist = self._synth_mist_layers(global_phase, intensity=mist_intensity)

        char_layer = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.uint8)
        fog_alpha = np.zeros((VM_SS_H, VM_SS_W), dtype=np.float32)
        lid_bump_y = 0.0
        jolt_dx, jolt_dy, jolt_deg = 0.0, 0.0, 0.0

        jar_h = float(self.jar_y1 - self.lid_y1)
        cy_mid = 0.5 * (self.lid_y1 + self.jar_y1)

        if antic_mode == "hamster_climb":
            # Antic 0: Drives his tiny wheel-bar up the right glass wall, flips upside-down across the lid, slides down left!
            ang_loop = sub_t * 2.0 * math.pi
            ox = self.j_cx + math.sin(ang_loop) * (self.j_rad * 0.44)
            oy = cy_mid + math.cos(ang_loop) * (jar_h * 0.32)
            tilt_deg = -math.degrees(ang_loop)
            d_idx = int(round((sub_t * 16))) % N_DIRS
            src_sp = self.turns["plank" if 0.15 < sub_t < 0.72 else "seated"][d_idx]
            mini = rotate_scale_translate_rgba(
                src_sp,
                angle_deg=tilt_deg,
                scale_x=0.46,
                scale_y=0.46,
                dx=ox - 192.0,
                dy=oy - 210.0,
                pivot=(192.0, 210.0),
                out_hw=(VM_SS_H, VM_SS_W),
            )
            char_layer = mini
            if 0.42 < sub_t < 0.58:
                lid_bump_y = -3.5 * math.sin((sub_t - 0.42) / 0.16 * math.pi)
                jolt_dy = lid_bump_y * 0.8

        elif antic_mode == "glass_squish":
            # Antic 1: Lunges forward and squishes his grinning/screaming bearded face flat on the front glass!
            slam_in = min(1.0, sub_t / 0.14) if sub_t < 0.84 else max(0.0, (1.0 - sub_t) / 0.16)
            slam_ease = 1.0 - (1.0 - slam_in) ** 3
            plate = self.squish_scream_crop if (int(sub_t * 7.0) % 2 == 1) else self.squish_grin_crop
            ph, pw = plate.shape[:2]
            sc = 0.76 + 0.28 * slam_ease
            slide_y = max(0.0, (sub_t - 0.25) * 26.0) * slam_ease
            w_s = max(16, int(round(pw * sc)))
            h_s = max(16, int(round(ph * sc * (1.0 - 0.05 * math.sin(sub_t * 28.0)))))
            rs = resize_rgba_premul(plate, w_s, h_s)
            px = int(round(self.j_cx - w_s * 0.5 + 3.0 * math.sin(sub_t * 36.0)))
            py = int(round(cy_mid - h_s * 0.48 + slide_y))
            y0 = max(0, py); x0 = max(0, px)
            y1 = min(VM_SS_H, py + h_s); x1 = min(VM_SS_W, px + w_s)
            if y1 > y0 and x1 > x0:
                char_layer[y0:y1, x0:x1] = rs[y0 - py:y1 - py, x0 - px:x1 - px]
            # Warm misty breath condensation halo on the front glass around his mouth!
            fog_r = np.hypot((self.xx - self.j_cx) / 48.0, (self.yy - (cy_mid - 14.0 + slide_y * 0.6)) / 38.0)
            fog_alpha = np.clip((1.0 - fog_r) * 0.42 * slam_ease, 0.0, 0.42) * self.cavity_alpha
            if sub_t < 0.20:
                jolt_dx = 3.5 * math.sin(sub_t * 60.0) * (1.0 - sub_t / 0.20)
                jolt_dy = 2.5 * math.cos(sub_t * 50.0)

        elif antic_mode == "pogo_bonk":
            # Antic 2: Hyper-fast 3x Pogo Sky-Point bounces bonking off the perforated stainless lid!
            b_phase = (sub_t * 3.0) % 1.0
            arc = math.sin(b_phase * math.pi)
            oy = (self.jar_y1 - 45.0) - arc * (jar_h * 0.56)
            ox = self.j_cx + 16.0 * math.sin(sub_t * 6.0 * math.pi)
            d_idx = (0 if int(sub_t * 3.0) % 2 == 0 else 15) if b_phase > 0.25 else 2
            src_sp = self.turns["jump" if b_phase > 0.18 else "melee"][d_idx]
            char_layer = rotate_scale_translate_rgba(
                src_sp,
                angle_deg=10.0 * math.sin(sub_t * 18.0),
                scale_x=0.47,
                scale_y=0.47 * (1.08 if 0.2 < b_phase < 0.8 else 0.88),
                dx=ox - 192.0,
                dy=oy - 200.0,
                pivot=(192.0, 200.0),
                out_hw=(VM_SS_H, VM_SS_W),
            )
            if 0.42 < b_phase < 0.58:
                lid_bump_y = -4.2 * math.sin((b_phase - 0.42) / 0.16 * math.pi)
                jolt_dy = -3.0

        else:
            # Antic 3 ("tornado_spaz" or "shake_pinball"): Rapid 360° whirlwind spin + full-jar rattle!
            fast_mult = 5.0 if antic_mode == "shake_pinball" else 3.0
            d_idx = int(round(sub_t * 16.0 * fast_mult)) % N_DIRS
            roll = (sub_t * 720.0 if antic_mode == "shake_pinball" else 16.0 * math.sin(sub_t * 38.0))
            ox = self.j_cx + (26.0 if antic_mode == "shake_pinball" else 18.0) * math.sin(sub_t * 32.0)
            oy = cy_mid + (58.0 if antic_mode == "shake_pinball" else 28.0) * math.cos(sub_t * 27.0)
            pose_key = "jump" if (antic_mode == "shake_pinball" and int(sub_t * 12) % 2 == 0) else "melee"
            char_layer = rotate_scale_translate_rgba(
                self.turns[pose_key][d_idx],
                angle_deg=roll,
                scale_x=0.46,
                scale_y=0.46,
                dx=ox - 192.0,
                dy=oy - 210.0,
                pivot=(192.0, 210.0),
                out_hw=(VM_SS_H, VM_SS_W),
            )
            jolt_dx = 3.2 * math.sin(sub_t * 24.0 * math.pi)
            jolt_dy = 2.4 * math.cos(sub_t * 30.0 * math.pi)
            jolt_deg = 1.4 * math.sin(sub_t * 18.0 * math.pi)

        refracted_char = self._refract_inside_cylinder(char_layer)

        # Assemble back-to-front optical stack!
        canvas = np.clip(np.round(self.base_back_rgba), 0, 255).astype(np.uint8)

        # Optional lid rattle upward bump on bonk frames
        if abs(lid_bump_y) > 0.4:
            lid_slice = canvas[max(0, self.lid_y0 - 4):self.lid_y1 + 4, self.jx0 - 4:self.jx1 + 4].copy()
            canvas[max(0, self.lid_y0 - 4):self.lid_y1 + 4, self.jx0 - 4:self.jx1 + 4, 3] = 0
            by0 = max(0, int(round(self.lid_y0 - 4 + lid_bump_y)))
            canvas[by0:by0 + lid_slice.shape[0], self.jx0 - 4:self.jx1 + 4] = lid_slice

        canvas = alpha_over(canvas, back_mist)
        canvas = alpha_over(canvas, refracted_char)
        canvas = alpha_over(canvas, front_mist)

        # Breath fog halo on front glass during Antic 1
        if np.any(fog_alpha > 0.01):
            fog_rgba = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.uint8)
            fog_rgba[..., 0] = 215
            fog_rgba[..., 1] = 255
            fog_rgba[..., 2] = 220
            fog_rgba[..., 3] = np.clip(fog_alpha * 255.0, 0, 255).astype(np.uint8)
            canvas = alpha_over(canvas, fog_rgba)

        # Front glass specular highlights + wrapped front gauntlet fingers (with emerald rim glow!)
        front_overlay = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.float32)
        spec_a = np.clip(self.glass_spec * 0.78, 0.0, 0.85)
        fing_a = self.front_finger_alpha
        comb_a = np.clip( fing_a + spec_a * (1.0 - fing_a), 0.0, 1.0)

        # Finger RGB tinted slightly on upper-right edge by pulsing neon-green jar glow
        fing_rgb = self.grip_ss[..., :3].astype(np.float32)
        rim_dist = np.clip(1.0 - np.abs(self.xx - self.jx0) / 36.0, 0.0, 1.0) * (self.yy > self.lid_y1 + 120)
        fing_rgb[..., 1] = np.clip(fing_rgb[..., 1] + 34.0 * rim_dist * mist_intensity, 0.0, 255.0)
        fing_rgb[..., 0] = np.clip(fing_rgb[..., 0] + 10.0 * rim_dist * mist_intensity, 0.0, 255.0)

        spec_rgb = np.dstack([
            np.full((VM_SS_H, VM_SS_W), 228.0, dtype=np.float32),
            np.full((VM_SS_H, VM_SS_W), 255.0, dtype=np.float32),
            np.full((VM_SS_H, VM_SS_W), 232.0, dtype=np.float32),
        ])
        w_fing = np.where(comb_a > 1e-4, fing_a / np.maximum(comb_a, 1e-4), 0.0)[..., None]
        front_overlay[..., :3] = fing_rgb * w_fing + spec_rgb * (1.0 - w_fing)
        front_overlay[..., 3] = comb_a * 255.0
        canvas = alpha_over(canvas, np.clip(np.round(front_overlay), 0, 255).astype(np.uint8))

        return canvas, jolt_dx, jolt_dy, jolt_deg

    def render_viewmodel_sequences_out(self) -> Dict[str, List[np.ndarray]]:
        """Renders all 4 first-person 60 FPS sequences (`idle`, `shake`, `throw`, `reload`) at `VM_OUT_W x VM_OUT_H`."""
        pivot_wrist = (VM_SS_W * 0.82, VM_SS_H * 0.92)

        # 1. IDLE (180 frames @ 60 FPS = 3.0s seamless loop cycling all 4 manic antics!)
        idle_frames: List[np.ndarray] = []
        antics = ["hamster_climb", "glass_squish", "pogo_bonk", "tornado_spaz"]
        f_per_antic = 45
        n_idle = f_per_antic * len(antics)  # 180
        for f in range(n_idle):
            a_idx = f // f_per_antic
            sub_t = (f % f_per_antic) / float(f_per_antic)
            g_phase = (f / float(n_idle)) * 4.0
            ss, jdx, jdy, jdeg = self.render_held_jar_frame_ss(
                antics[a_idx], sub_t, g_phase, mist_intensity=1.0 + 0.15 * math.sin(g_phase * 2.0 * math.pi)
            )
            # Subtle organic breathing sway + jar jolt
            br_t = (f / float(n_idle)) * 2.0 * math.pi
            dx = jdx + 3.0 * math.sin(br_t)
            dy = jdy + 3.5 * math.cos(br_t * 2.0)
            deg = jdeg + 0.8 * math.sin(br_t)
            posed = rotate_scale_translate_rgba(ss, deg, 1.0, 1.0, dx, dy, pivot=pivot_wrist, out_hw=(VM_SS_H, VM_SS_W))
            idle_frames.append(resize_rgba_premul(posed, VM_OUT_W, VM_OUT_H))

        # 2. COCKTAIL-SHAKER WINDUP (24 frames @ 60 FPS = 0.40s, loopable while holding Fire!)
        shake_frames: List[np.ndarray] = []
        n_shake = 24
        for f in range(n_shake):
            u = f / float(n_shake)
            sh_ang = u * 3.0 * 2.0 * math.pi  # 3 violent cocktail shakes in 0.40s!
            ss, _, _, _ = self.render_held_jar_frame_ss("shake_pinball", u, u * 3.0, mist_intensity=1.85)
            dy = -26.0 * math.sin(sh_ang)
            dx = -12.0 * math.cos(sh_ang)
            deg = 7.5 * math.sin(sh_ang)
            # 3-tap directional motion blur along shake vector for juicy high-speed kinetic feel!
            acc = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.float32)
            for tap_w, dt_tap in [(0.25, -0.012), (0.50, 0.0), (0.25, 0.012)]:
                ang_t = (u + dt_tap) * 3.0 * 2.0 * math.pi
                p_tap = rotate_scale_translate_rgba(
                    ss,
                    7.5 * math.sin(ang_t),
                    1.0,
                    1.0,
                    -12.0 * math.cos(ang_t),
                    -26.0 * math.sin(ang_t),
                    pivot=pivot_wrist,
                    out_hw=(VM_SS_H, VM_SS_W),
                ).astype(np.float32)
                p_tap[..., :3] *= (p_tap[..., 3:4] / 255.0)
                acc += p_tap * tap_w
            wa = acc[..., 3:4] / 255.0
            out_s = np.zeros((VM_SS_H, VM_SS_W, 4), dtype=np.uint8)
            out_s[..., :3] = np.clip(np.round(np.where(wa > 1e-4, acc[..., :3] / np.maximum(wa, 1e-4), 0.0)), 0, 255).astype(np.uint8)
            out_s[..., 3] = np.clip(np.round(acc[..., 3]), 0, 255).astype(np.uint8)
            shake_frames.append(resize_rgba_premul(out_s, VM_OUT_W, VM_OUT_H))

        # 3. OVERHAND WHIP-THROW & SPLAYED OPEN-CLAW RELEASE (18 frames @ 60 FPS = 0.30s; jar leaves at f=8!)
        throw_frames: List[np.ndarray] = []
        n_throw = 18
        ss_charged, _, _, _ = self.render_held_jar_frame_ss("shake_pinball", 0.35, 0.5, mist_intensity=2.1)
        for f in range(n_throw):
            if f < 5:
                # High cock-back to upper-right
                u = f / 5.0
                ease = math.sin(u * 0.5 * math.pi)
                posed = rotate_scale_translate_rgba(
                    ss_charged, -14.0 * ease, 1.03, 1.03, 34.0 * ease, -24.0 * ease, pivot=pivot_wrist, out_hw=(VM_SS_H, VM_SS_W)
                )
            elif f < 8:
                # Blistering cross-screen forward whip right to release point!
                u = (f - 5) / 3.0
                dx = 34.0 * (1.0 - u) - 48.0 * u
                dy = -24.0 * (1.0 - u) + 18.0 * u
                deg = -14.0 * (1.0 - u) + 18.0 * u
                posed = rotate_scale_translate_rgba(ss_charged, deg, 1.0, 1.0, dx, dy, pivot=pivot_wrist, out_hw=(VM_SS_H, VM_SS_W))
            else:
                # Splayed open-claw follow-through (`self.open_ss`) recoiling & dropping down!
                u = (f - 8) / float(n_throw - 8)
                shudder = math.sin(u * 4.0 * math.pi) * (1.0 - u) * 5.0
                dx = -28.0 * (1.0 - u) + 22.0 * (u ** 2) + shudder
                dy = 12.0 + 165.0 * (u ** 2.1)
                deg = 12.0 * (1.0 - u) - 8.0 * u
                posed = rotate_scale_translate_rgba(self.open_ss, deg, 1.0, 1.0, dx, dy, pivot=pivot_wrist, out_hw=(VM_SS_H, VM_SS_W))
            throw_frames.append(resize_rgba_premul(posed, VM_OUT_W, VM_OUT_H))

        # 4. BELT-SNATCH FRESH JAR RELOAD (18 frames @ 60 FPS = 0.30s)
        reload_frames: List[np.ndarray] = []
        n_reload = 18
        for f in range(n_reload):
            u = f / float(n_reload - 1)
            # Overshoot spring curve
            spring = 1.0 - math.exp(-5.2 * u) * math.cos(5.8 * u)
            ss_rel, _, _, _ = self.render_held_jar_frame_ss("hamster_climb", u * 0.35, u, mist_intensity=1.05)
            dy = (1.0 - spring) * 210.0
            dx = (1.0 - spring) * 45.0
            deg = (1.0 - spring) * -16.0
            posed = rotate_scale_translate_rgba(ss_rel, deg, 1.0, 1.0, dx, dy, pivot=pivot_wrist, out_hw=(VM_SS_H, VM_SS_W))
            reload_frames.append(resize_rgba_premul(posed, VM_OUT_W, VM_OUT_H))

        return {
            "vm_idle": idle_frames,
            "vm_shake": shake_frames,
            "vm_throw": throw_frames,
            "vm_reload": reload_frames,
        }


def build_projectile_and_smoke_sprites(rig: JarGauntletRig) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Builds:
      1. `proj_jar` (24 frames @ 200x200): End-over-end tumbling sealed glass jar with glowing green mist & tiny screaming guy!
      2. `smoke_burst` (36 frames @ 256x256): Shattering glass shards + igniting neon-green smoke fireball cloud!
    """
    # 1. Compose a single upright filled standalone jar (220x220) with bright green mist + tiny guy inside
    jar_base = rig.standalone_jar.copy()
    jh, jw = jar_base.shape[:2]
    yy, xx = np.indices((jh, jw), dtype=np.float32)

    proj_frames: List[np.ndarray] = []
    for f in range(24):
        u = f / 24.0
        # Glowing emerald mist core inside the 220x220 jar
        mist = np.zeros((jh, jw, 4), dtype=np.uint8)
        rx = (xx - 110.0) / 38.0
        ry = (yy - 118.0) / 68.0
        in_c = (np.abs(rx) < 1.0) & (np.abs(ry) < 1.0)
        sw = 0.55 + 0.45 * np.sin(rx * 3.5 + u * 4.0 * math.pi) * np.cos(ry * 4.5 - u * 6.0 * math.pi)
        mist[..., 0] = 85
        mist[..., 1] = 250
        mist[..., 2] = 55
        mist[..., 3] = np.where(in_c, np.clip(sw * 185.0, 0, 210), 0).astype(np.uint8)

        tiny_d = (f * 2) % N_DIRS
        tiny_guy = rotate_scale_translate_rgba(
            rig.turns["jump"][tiny_d],
            angle_deg=25.0 * math.sin(u * 4.0 * math.pi),
            scale_x=0.28,
            scale_y=0.28,
            dx=110.0 - 192.0,
            dy=122.0 - 200.0,
            pivot=(192.0, 200.0),
            out_hw=(jh, jw),
        )
        tiny_guy[..., 3] = np.where(in_c, tiny_guy[..., 3], 0)

        filled = alpha_over(mist, tiny_guy)
        filled = alpha_over(filled, jar_base)

        rot_deg = -u * 360.0
        tumbled = rotate_scale_translate_rgba(filled, rot_deg, 0.84, 0.84, -10.0, -10.0, pivot=(110.0, 110.0), out_hw=(200, 200))
        proj_frames.append(tumbled)

    # 2. Glass-Shatter & Igniting Neon-Green Smoke Fireball (36 frames @ 256x256)
    rng = np.random.default_rng(77123)
    W = 256
    yy_s, xx_s = np.indices((W, W), dtype=np.float32)

    # Pre-seed 24 billowing smoke puffs & 28 glittering glass shards + spinning stainless lid!
    puffs = []
    for i in range(24):
        ang = (i / 24.0) * 2.0 * math.pi + rng.uniform(-0.2, 0.2)
        spd = rng.uniform(22.0, 88.0)
        lift = rng.uniform(18.0, 62.0)
        r0 = rng.uniform(16.0, 28.0)
        r1 = rng.uniform(34.0, 56.0)
        hot = rng.uniform(0.0, 1.0)
        puffs.append((ang, spd, lift, r0, r1, hot))

    shards = []
    for i in range(28):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        spd = rng.uniform(65.0, 145.0)
        sz = rng.uniform(4.0, 9.5)
        spin = rng.uniform(-14.0, 14.0)
        shards.append((ang, spd, sz, spin))

    burst_frames: List[np.ndarray] = []
    for f in range(36):
        u = f / 35.0
        ease = 1.0 - (1.0 - u) ** 2.4
        acc_rgb = np.zeros((W, W, 3), dtype=np.float32)
        acc_a = np.zeros((W, W), dtype=np.float32)

        # Initial blinding radioactive ignition flash (frames 0..6)
        if f < 7:
            fl_u = 1.0 - f / 7.0
            dist_c = np.hypot(xx_s - 128.0, yy_s - 142.0)
            fl_base = np.maximum(0.0, 1.0 - dist_c / (48.0 + 42.0 * (1.0 - fl_u)))
            fl_a = np.clip((fl_base ** 1.7) * fl_u * 0.95, 0.0, 1.0)
            acc_rgb[..., 0] += 210.0 * fl_a
            acc_rgb[..., 1] += 255.0 * fl_a
            acc_rgb[..., 2] += 185.0 * fl_a
            acc_a = np.clip(acc_a + fl_a, 0.0, 1.0)

        # Billowing neon-green igniting smoke cloud
        fade_out = np.clip((1.0 - max(0.0, (u - 0.52) / 0.48)) ** 1.35, 0.0, 1.0)
        for ang, spd, lift, r0, r1, hot in puffs:
            px = 128.0 + math.cos(ang) * spd * ease
            py = 148.0 + math.sin(ang) * spd * 0.65 * ease - lift * (u ** 1.15)
            rad = r0 + (r1 - r0) * ease
            d2 = ((xx_s - px) ** 2 + (yy_s - py) ** 2) / max(1.0, rad * rad)
            pa = (np.maximum(0.0, 1.0 - d2) ** 1.6) * 0.52 * fade_out
            if not np.any(pa > 0.005):
                continue
            # Bright lime-white ignition core cooling into deep toxic emerald smoke
            ignite_heat = hot * max(0.0, 1.0 - u * 1.9)
            cr = 32.0 + 165.0 * ignite_heat
            cg = 165.0 + 90.0 * (0.4 + 0.6 * ignite_heat)
            cb = 26.0 + 95.0 * ignite_heat
            acc_rgb[..., 0] = acc_rgb[..., 0] * (1.0 - pa) + cr * pa
            acc_rgb[..., 1] = acc_rgb[..., 1] * (1.0 - pa) + cg * pa
            acc_rgb[..., 2] = acc_rgb[..., 2] * (1.0 - pa) + cb * pa
            acc_a = acc_a + pa * (1.0 - acc_a)

        out = np.zeros((W, W, 4), dtype=np.uint8)
        out[..., :3] = np.clip(np.round(acc_rgb), 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(np.round(acc_a * 255.0), 0, 255).astype(np.uint8)

        # Crisp glittering glass shards flying outward (frames 0..22)
        if f < 24:
            pil = Image.fromarray(out, "RGBA")
            dr = ImageDraw.Draw(pil, "RGBA")
            sh_fade = int(255 * max(0.0, 1.0 - f / 23.0))
            for ang, spd, sz, spin in shards:
                t_s = f / 22.0
                sx = 128.0 + math.cos(ang) * spd * t_s
                sy = 144.0 + math.sin(ang) * spd * 0.75 * t_s + 52.0 * (t_s ** 2)
                if 4 < sx < W - 4 and 4 < sy < W - 4:
                    theta = f * spin
                    pts = [
                        (sx + math.cos(theta) * sz, sy + math.sin(theta) * sz),
                        (sx + math.cos(theta + 2.1) * sz * 0.8, sy + math.sin(theta + 2.1) * sz * 0.8),
                        (sx + math.cos(theta + 4.2) * sz * 0.9, sy + math.sin(theta + 4.2) * sz * 0.9),
                    ]
                    dr.polygon(pts, fill=(215, 255, 235, sh_fade), outline=(255, 255, 255, sh_fade))
            out = np.array(pil, dtype=np.uint8)

        burst_frames.append(out)

    return proj_frames, burst_frames


def build_mini_gremlin_sprites(turns_16: Dict[str, List[np.ndarray]]) -> Dict[str, object]:
    """Builds the 5 Mini-Green-Guy Gremlin sprite sets (`160x160` RGBA cells):
      - `scurry`      : 16 angles x 12 frames (hyper-fast floor & ankle-orbit zoom!)
      - `wall_climb`  : 16 angles x 12 frames (vertical 84°-tilted building climber with emerald sparks!)
      - `pogo_jump`   : 16 angles x 12 frames (weightless rubber-flea Crane-Kick Sky-Point face-swarm jump!)
      - `shot_spin`   : 24 frames (1-hit punctured-helium-balloon 360°x720° pinwheel spin + green mist jet!)
      - `balloon_pop` : 24 frames (1.55x spherical balloon swell -> shock-ring + 65 3D rainbow confetti streamers!)
    """
    CW = 160
    yy, xx = np.indices((CW, CW), dtype=np.float32)

    scurry_grid: List[List[np.ndarray]] = [[None] * 12 for _ in range(N_DIRS)]  # type: ignore
    wall_grid: List[List[np.ndarray]] = [[None] * 12 for _ in range(N_DIRS)]    # type: ignore
    pogo_grid: List[List[np.ndarray]] = [[None] * 12 for _ in range(N_DIRS)]    # type: ignore

    for d in range(N_DIRS):
        plank_d = turns_16["plank"][d]
        seat_d = turns_16["seated"][d]
        jump_d = turns_16["jump"][d]
        melee_d = turns_16["melee"][d]

        for f in range(12):
            ph = (f / 12.0) * 2.0 * math.pi
            # 1. Hyper Floor Scurry (alternates rapid plank/seated bob + tiny green speed trail)
            bob_y = -4.5 * abs(math.sin(ph * 2.0))
            sq_x = 1.0 + 0.07 * math.sin(ph * 2.0)
            sq_y = 1.0 - 0.06 * math.sin(ph * 2.0)
            src = plank_d if (d % 2 == 0) else seat_d
            fr_s = rotate_scale_translate_rgba(
                src, 4.5 * math.sin(ph), 0.36 * sq_x, 0.36 * sq_y, 80.0 - 192.0, 138.0 + bob_y - 340.0, pivot=(192.0, 340.0), out_hw=(CW, CW)
            )
            scurry_grid[d][f] = fr_s

            # 2. Vertical Building / Wall Climber (tilted vertically up the wall at -82° / +82°!)
            climb_tilt = -82.0 if d < 8 else 82.0
            jitter_x = 2.5 * math.sin(ph * 2.0)
            jitter_y = -5.0 * math.sin(ph)
            fr_w = rotate_scale_translate_rgba(
                plank_d,
                climb_tilt + 6.0 * math.sin(ph * 2.0),
                0.36,
                0.36,
                80.0 + jitter_x - 192.0,
                84.0 + jitter_y - 240.0,
                pivot=(192.0, 240.0),
                out_hw=(CW, CW),
            )
            # Tiny green wall-traction sparks!
            pil_w = Image.fromarray(fr_w, "RGBA")
            dr_w = ImageDraw.Draw(pil_w, "RGBA")
            for sp_i in range(3):
                sx = 80 + (-18 if d < 8 else 18) + int(6 * math.sin(ph + sp_i * 2.1))
                sy = 104 + sp_i * 9 + int(5 * math.cos(ph * 2.0 + sp_i))
                dr_w.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(150, 255, 90, 220))
            wall_grid[d][f] = np.array(pil_w, dtype=np.uint8)

            # 3. Weightless Rubber-Flea Pogo / Face-Blocking Sky-Point Jump! (fits cleanly inside 160x160!)
            arc = math.sin((f / 12.0) * math.pi)
            lift = -22.0 * arc
            stretch_y = 0.88 + 0.18 * arc
            stretch_x = 1.08 - 0.12 * arc
            src_j = jump_d if (0.14 < (f / 12.0) < 0.86) else melee_d
            fr_p = rotate_scale_translate_rgba(
                src_j,
                9.0 * math.sin(ph),
                0.32 * stretch_x,
                0.32 * stretch_y,
                80.0 - 192.0,
                148.0 + lift - 332.0,
                pivot=(192.0, 332.0),
                out_hw=(CW, CW),
            )
            pogo_grid[d][f] = fr_p

    # 4. 1-Hit Punctured-Helium-Balloon Death-Spin (24 frames @ 160x160)
    shot_spin_frames: List[np.ndarray] = []
    for f in range(24):
        u = f / 24.0
        d_spin = (f * 3) % N_DIRS
        roll_deg = u * 720.0  # Two full upside-down cartwheels while spinning 360°!
        wobble_x = 12.0 * math.sin(u * 4.0 * math.pi)
        wobble_y = -10.0 * math.cos(u * 4.0 * math.pi)
        fr = rotate_scale_translate_rgba(
            turns_16["jump"][d_spin],
            roll_deg,
            0.33 * (1.0 + 0.10 * u),
            0.33 * (1.0 + 0.10 * u),
            80.0 + wobble_x - 192.0,
            82.0 + wobble_y - 210.0,
            pivot=(192.0, 210.0),
            out_hw=(CW, CW),
        )
        # Punctured green helium mist jetting out in a spiral!
        pil = Image.fromarray(fr, "RGBA")
        dr = ImageDraw.Draw(pil, "RGBA")
        jet_ang = math.radians(roll_deg + 90.0)
        for j_i in range(6):
            dist_j = 18.0 + j_i * 7.5
            jx = 80.0 + wobble_x + math.cos(jet_ang - j_i * 0.28) * dist_j
            jy = 82.0 + wobble_y + math.sin(jet_ang - j_i * 0.28) * dist_j
            rad_j = max(2, 7 - j_i)
            dr.ellipse([jx - rad_j, jy - rad_j, jx + rad_j, jy + rad_j], fill=(120, 255, 80, max(35, 210 - j_i * 32)))
        shot_spin_frames.append(np.array(pil, dtype=np.uint8))

    # 5. Over-Inflated Balloon Swell -> Rainbow Party-Confetti Pop! (24 frames @ 160x160)
    CONFETTI_COLORS = [
        (255, 64, 140),   # Hot Party Pink
        (255, 214, 10),   # Bright Gold
        (56, 220, 255),   # Electric Cyan
        (132, 255, 58),   # Neon Green-Suit Lime
        (192, 98, 255),   # Vivid Purple
        (255, 132, 38),   # Party Orange
        (255, 255, 255),  # White Sparkle
    ]
    rng_c = np.random.default_rng(99911)
    streamers = []
    for i in range(68):
        ang = rng_c.uniform(0.0, 2.0 * math.pi)
        spd = rng_c.uniform(22.0, 74.0)
        grav = rng_c.uniform(18.0, 42.0)
        flutter_hz = rng_c.uniform(2.5, 6.5)
        rot0 = rng_c.uniform(0.0, math.pi)
        col = CONFETTI_COLORS[i % len(CONFETTI_COLORS)]
        w_c = rng_c.uniform(3.2, 6.2)
        h_c = rng_c.uniform(2.0, 3.8)
        streamers.append((ang, spd, grav, flutter_hz, rot0, col, w_c, h_c))

    balloon_pop_frames: List[np.ndarray] = []
    base_front = rotate_scale_translate_rgba(
        turns_16["jump"][0], 0.0, 0.31, 0.31, 80.0 - 192.0, 90.0 - 210.0, pivot=(192.0, 210.0), out_hw=(CW, CW)
    )
    for f in range(24):
        if f < 6:
            # Spherical balloon over-inflation (1.0x -> 1.46x round balloon bulge + bright lime flush!)
            sw_u = f / 5.0
            scale_b = 1.0 + 0.46 * (sw_u ** 1.5)
            rx = (xx - 80.0) / (44.0 * scale_b)
            ry = (yy - 86.0) / (44.0 * scale_b)
            r2 = rx * rx + ry * ry
            bulge = np.where(r2 < 1.0, 1.0 - 0.34 * sw_u * (1.0 - r2), 1.0)
            map_x = (80.0 + (xx - 80.0) / scale_b * bulge).astype(np.float32)
            map_y = (86.0 + (yy - 86.0) / (scale_b * (0.92 + 0.08 * sw_u)) * bulge).astype(np.float32)
            pm = base_front.astype(np.float32)
            pm[..., :3] *= (pm[..., 3:4] / 255.0)
            w_pm = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            wa = w_pm[..., 3:4] / 255.0
            rgb = np.where(wa > 1e-4, w_pm[..., :3] / np.maximum(wa, 1e-4), 0.0)
            # Bright pressurized neon sheen right before bursting!
            rgb[..., 0] = np.clip(rgb[..., 0] + 65.0 * sw_u, 0, 255)
            rgb[..., 1] = np.clip(rgb[..., 1] + 55.0 * sw_u, 0, 255)
            rgb[..., 2] = np.clip(rgb[..., 2] + 45.0 * sw_u, 0, 255)
            fr_b = np.zeros((CW, CW, 4), dtype=np.uint8)
            fr_b[..., :3] = np.round(rgb).astype(np.uint8)
            fr_b[..., 3] = np.clip(np.round(w_pm[..., 3]), 0, 255).astype(np.uint8)
            balloon_pop_frames.append(fr_b)
        else:
            # Frame 6..23: Crisp party-balloon POP shock-ring + 68 tumbling rainbow confetti streamers!
            pu = (f - 6) / 17.0
            pil = Image.new("RGBA", (CW, CW), (0, 0, 0, 0))
            dr = ImageDraw.Draw(pil, "RGBA")

            # Crisp white/lime balloon shock-ring on frames 6..10
            if f < 11:
                ru = (f - 6) / 5.0
                rr = 18.0 + 48.0 * ru
                ra = int(235 * (1.0 - ru))
                dr.ellipse([80 - rr, 80 - rr, 80 + rr, 80 + rr], outline=(205, 255, 150, ra), width=max(1, int(4 * (1.0 - ru))))

            # Soft green mist puff at center
            if pu < 0.55:
                mr = 22.0 + 26.0 * pu
                ma = int(130 * (1.0 - pu / 0.55))
                dr.ellipse([80 - mr, 80 - mr, 80 + mr, 80 + mr], fill=(120, 255, 85, ma))

            # 68 3D-tumbling rainbow party confetti streamers!
            drag_t = 1.0 - (1.0 - pu) ** 2.3
            alpha_c = int(255 * np.clip((1.0 - max(0.0, (pu - 0.62) / 0.38)), 0.0, 1.0))
            if alpha_c > 4:
                for ang, spd, grav, fl_hz, rot0, col, w_c, h_c in streamers:
                    cx = 80.0 + math.cos(ang) * spd * drag_t + 4.5 * math.sin(pu * fl_hz * 2.0 * math.pi + rot0)
                    cy = 78.0 + math.sin(ang) * spd * 0.85 * drag_t + grav * (pu ** 1.65)
                    if 3 < cx < CW - 3 and 3 < cy < CW - 3:
                        # 3D tumble foreshortening
                        th = rot0 + pu * fl_hz * 4.5
                        flip_3d = 0.25 + 0.75 * abs(math.cos(th * 1.7))
                        dx1 = math.cos(th) * w_c
                        dy1 = math.sin(th) * w_c
                        dx2 = -math.sin(th) * h_c * flip_3d
                        dy2 = math.cos(th) * h_c * flip_3d
                        quad = [
                            (cx - dx1 - dx2, cy - dy1 - dy2),
                            (cx + dx1 - dx2, cy + dy1 - dy2),
                            (cx + dx1 + dx2, cy + dy1 + dy2),
                            (cx - dx1 + dx2, cy - dy1 + dy2),
                        ]
                        dr.polygon(quad, fill=(col[0], col[1], col[2], alpha_c))
            balloon_pop_frames.append(np.array(pil, dtype=np.uint8))

    return {
        "scurry": scurry_grid,
        "wall_climb": wall_grid,
        "pogo_jump": pogo_grid,
        "shot_spin": shot_spin_frames,
        "balloon_pop": balloon_pop_frames,
    }
