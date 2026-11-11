"""Parallel 4,224-Frame 60 FPS WebP Sprite Atlas Baker, DarkPlaces 960-Frame 16-Angle `.spr32` Packer,
Real-Photo Accuracy Poster Generator, and Self-Contained HTML Showcase Builder.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
import struct
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy import ndimage

from build_html_showcase import write_self_contained_html
from greensuit_anims_60fps import (
    ANIM_SPECS,
    precompute_3d_gib_trajectories,
    render_monster_frame_ss,
)
from greensuit_core import (
    ANGLES_DEG,
    N_DIRS,
    OUT_GROUND,
    OUT_H,
    OUT_W,
    resize_rgba_premul,
)
from greensuit_turnarounds import (
    build_all_16_turnarounds,
    extract_real_gib_parts,
    save_turnaround_audit_sheet,
)

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_PACK_DIR = os.path.join(MOD_ROOT, "greensuit_wheelman_monster")
ATLAS_DIR = os.path.join(OUT_PACK_DIR, "atlases")
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
STAGED_PROGS_DIR = os.path.abspath(os.path.join(MOD_ROOT, "..", "_bakersfield_dev", "staged_assets", "progs"))
REF_PHOTOS_DIR = os.path.join(HERE, "ref_photos")

# DarkPlaces 8-angle tight-cropped .spr32 cell specs (11/17 of 136x136 -> 88x88; paired with self.scale = 0.8036 in QuakeC)
DP_W = 88
DP_H = 88
DP_GROUND = 78


def tone_for_darkplaces_rgba(rgba: np.ndarray) -> np.ndarray:
    """Tones RGBA cell for DarkPlaces r_hdr_scenebrightness 2.5 (Contrast 1.20, Brightness 0.50)."""
    pil = Image.fromarray(rgba, "RGBA")
    rgb = ImageEnhance.Contrast(pil.convert("RGB")).enhance(1.20)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.50)
    rgb.putalpha(pil.getchannel("A"))
    return np.asarray(rgb, dtype=np.uint8)


def _tight_crop_and_bleed(rgba: np.ndarray, base_ox: int, base_oy: int) -> Tuple[int, int, int, int, bytes]:
    h, w, _ = rgba.shape
    ys, xs = np.nonzero(rgba[:, :, 3] > 2)
    if len(xs) == 0:
        empty = np.zeros((2, 2, 4), dtype=np.uint8)
        return -1, 1, 2, 2, empty.tobytes()
    x0 = max(0, int(xs.min()) - 1)
    y0 = max(0, int(ys.min()) - 1)
    x1 = min(w, int(xs.max()) + 2)
    y1 = min(h, int(ys.max()) + 2)
    cropped = rgba[y0:y1, x0:x1].copy()
    pad_l = 1 if x0 == int(xs.min()) else 0
    pad_t = 1 if y0 == int(ys.min()) else 0
    pad_r = 1 if x1 == int(xs.max()) + 1 else 0
    pad_b = 1 if y1 == int(ys.max()) + 1 else 0
    if pad_l or pad_t or pad_r or pad_b:
        cropped = np.pad(cropped, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="constant", constant_values=0)
        x0 -= pad_l
        y0 -= pad_t
    fg = cropped[:, :, 3] >= 32
    if not np.any(fg):
        fg = cropped[:, :, 3] > 0
    if np.any(fg):
        tr = cropped[:, :, 3] == 0
        if np.any(tr):
            _, (iy, ix) = ndimage.distance_transform_edt(~fg, return_indices=True)
            cropped[tr, :3] = cropped[iy[tr], ix[tr], :3]
    cw, ch = cropped.shape[1], cropped.shape[0]
    return int(base_ox + x0), int(base_oy - y0), cw, ch, cropped.tobytes()


def write_darkplaces_spr32(spr_path: str, toned_frames: List[np.ndarray], w: int = DP_W, h: int = DP_H, ground_y: int = DP_GROUND) -> float:
    """Writes tight-cropped DarkPlaces IDSP v32 sprite, type 0 (SPR_VP_PARALLEL_UPRIGHT), anchored at wheel ground contact."""
    base_ox = -(w // 2)
    base_oy = ground_y
    packed = [_tight_crop_and_bleed(fr, base_ox, base_oy) for fr in toned_frames]
    max_cw = max(f[2] for f in packed)
    max_ch = max(f[3] for f in packed)
    rad = 0.5 * math.hypot(max_cw, max_ch)
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, max_cw, max_ch, len(packed), 0.0, 0))
    for fox, foy, cw, ch, fb in packed:
        buf += struct.pack("<iiiii", 0, fox, foy, cw, ch)
        buf += fb
    targets = [spr_path]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        stg_p = os.path.join(STAGED_PROGS_DIR, os.path.basename(spr_path))
        if os.path.normcase(stg_p) != os.path.normcase(spr_path):
            targets.append(stg_p)
    for dst in targets:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(buf)
        os.replace(tmp, dst)
    return len(buf) / (1024.0 * 1024.0)


def build_accuracy_and_16angle_poster(
    turnarounds: Dict[str, List[np.ndarray]],
    sample_anim_frames: Dict[str, List[List[np.ndarray]]],
    out_jpg: str,
) -> None:
    """Creates a crisp comparison & turnaround poster contrasting the real uploaded photos with our
    digitized live-action 60 FPS sprite and showing all 16 compass angles!
    """
    W, H = 1760, 1080
    poster = Image.new("RGB", (W, H), (14, 18, 27))
    dr = ImageDraw.Draw(poster)
    dr.text((24, 16), "GREEN-SUIT WHEELMAN MONSTER — 100% REAL PHOTO-DIGITIZED 16-ANGLE (360°) @ 60 FPS SPRITE", fill=(128, 245, 66))
    dr.text((24, 38), "Zero Procedural 3D Human Meshes · Authentic Live-Action Likeness · Seated Cruise, Ab-Roller Charge, Pipe-Vault Sky-Point Slam & 3D Quake Gibs", fill=(165, 180, 204))

    # Top row: 3 side-by-side pairs (Real Uploaded Photo vs Digitized 60 FPS Sprite Frame!)
    pairs = [
        ("ref_02_seated_front.jpg", sample_anim_frames["cruise"][15][4], "Pose 1: Seated Low-Rider Cruise (Real Photo vs Digitized Sprite)"),
        ("ref_05_plank_charge.jpg", sample_anim_frames["charge"][2][6],  "Pose 2: Screaming Ab-Roller Charge (Real Photo vs Digitized Sprite)"),
        ("ref_04_crane_point.jpg",  sample_anim_frames["jump_slam"][15][24], "Pose 3: Mid-Air Crane-Kick Sky-Point Jump (Real Photo vs Digitized Sprite)"),
    ]
    box_w = 556
    box_h = 280
    for idx, (ref_fn, spr_rgba, caption) in enumerate(pairs):
        bx = 24 + idx * (box_w + 22)
        by = 68
        dr.rectangle([bx, by, bx + box_w, by + box_h], fill=(22, 29, 43), outline=(48, 65, 96), width=2)
        dr.text((bx + 10, by + 7), caption, fill=(251, 191, 36))

        # Left half: Real Reference Photo center-cropped/fitted
        ref_im = Image.open(os.path.join(REF_PHOTOS_DIR, ref_fn)).convert("RGB")
        rw, rh = ref_im.size
        scale_r = min(256.0 / rw, 232.0 / rh)
        ref_rs = ref_im.resize((int(rw * scale_r), int(rh * scale_r)), Image.LANCZOS)
        poster.paste(ref_rs, (bx + 14 + (256 - ref_rs.width) // 2, by + 34 + (232 - ref_rs.height) // 2))
        dr.text((bx + 18, by + box_h - 18), "Original Camera Photo", fill=(148, 163, 184))

        # Right half: Digitized Sprite on dark checker
        tile = Image.new("RGBA", (256, 232), (28, 36, 52, 255))
        spr_rs = resize_rgba_premul(spr_rgba, 232, 232)
        tile.alpha_composite(Image.fromarray(spr_rs, "RGBA"), (12, 0))
        poster.paste(tile.convert("RGB"), (bx + 284, by + 34))
        dr.text((bx + 288, by + box_h - 18), "Digitized 60 FPS Sprite", fill=(128, 245, 66))

    # Middle rows: Full 16-Angle Turnaround Strip (0°..337.5°) across all 4 core pose sets!
    dr.text((24, 366), "FULL 16-DIRECTION (EVERY 22.5°) LIVE-ACTION TURNAROUND — SEATED CRUISE / AB-ROLLER CHARGE / BATTERING-RAM MELEE / SKY-POINT JUMP", fill=(56, 189, 248))
    cw, ch = 107, 112
    pose_rows = [
        ("cruise",          0,  "Cruise"),
        ("charge",          4,  "Charge"),
        ("whirlwind_melee", 0,  "Melee"),
        ("jump_slam",       24, "Jump"),
    ]
    for r_i, (aid, f_pick, short_lbl) in enumerate(pose_rows):
        for d in range(N_DIRS):
            ox = 24 + d * cw
            oy = 392 + r_i * (ch + 6)
            bg = (24, 31, 45, 255) if (d + r_i) % 2 == 0 else (34, 43, 62, 255)
            tile = Image.new("RGBA", (cw, ch), bg)
            fr = resize_rgba_premul(sample_anim_frames[aid][d][f_pick], cw, cw)
            tile.alpha_composite(Image.fromarray(fr, "RGBA"), (0, ch - cw))
            poster.paste(tile.convert("RGB"), (ox, oy))
            dr.text((ox + 3, oy + 2), f"{ANGLES_DEG[d]:.1f}°", fill=(250, 204, 21) if d % 2 == 0 else (203, 213, 225))

    # Bottom row: Action Strip of Pipe-Vault Jump -> Sky-Point -> Slam + 3D Quake Gib Detonation!
    dr.text((24, 872), "60 FPS ACTION SEQUENCE: PIPE-VAULT SKY-POINT SLAM & 3D BALLISTIC QUAKE MEGA-GIBS (BOUNCING TIRES & STAINLESS PIPE!)", fill=(244, 63, 94))
    seq_picks = [
        ("jump_slam", 2, 5,  "Vault Plant"),
        ("jump_slam", 2, 13, "Ascent"),
        ("jump_slam", 0, 22, "Sky-Point 0°"),
        ("jump_slam", 4, 26, "Sky-Point 90°"),
        ("jump_slam", 12, 30, "Sky-Point 270°"),
        ("jump_slam", 2, 39, "Meteor Dive"),
        ("jump_slam", 2, 46, "Shockwave Slam!"),
        ("wheelie_taunt", 4, 18, "Wheelie Rev"),
        ("whirlwind_melee", 2, 16, "360° Spin"),
        ("pain", 2, 4, "Pain Blood"),
        ("gib_death", 0, 7, "Gib Rupture"),
        ("gib_death", 2, 15, "Flying Tires!"),
        ("gib_death", 4, 25, "Pipe Bounce!"),
        ("gib_death", 0, 38, "Blood Pool"),
    ]
    sw_cell = 122
    sh_cell = 168
    for i, (aid, d_p, f_p, lbl) in enumerate(seq_picks):
        ox = 24 + i * sw_cell
        oy = 896
        tile = Image.new("RGBA", (sw_cell - 4, sh_cell), (25, 31, 44, 255))
        fr = resize_rgba_premul(sample_anim_frames[aid][d_p][f_p], sw_cell - 4, sw_cell - 4)
        tile.alpha_composite(Image.fromarray(fr, "RGBA"), (0, 22))
        poster.paste(tile.convert("RGB"), (ox, oy))
        dr.text((ox + 4, oy + 4), lbl, fill=(134, 239, 172))

    os.makedirs(os.path.dirname(out_jpg), exist_ok=True)
    poster.save(out_jpg, quality=91)


def save_preview_gif(all_out_frames: Dict[str, List[List[np.ndarray]]], out_gif: str) -> None:
    """Builds a lively animated showcase GIF chaining Cruise -> Charge -> Pipe-Vault Jump & Slam -> Gibs while orbiting 360°!"""
    gif_frames = []
    # Sample every 2nd 60fps frame (= 30fps GIF) across a dramatic 360° orbit!
    plan = [
        ("cruise", 36),
        ("charge", 30),
        ("jump_slam", 54),
        ("whirlwind_melee", 36),
        ("gib_death", 48),
    ]
    step_global = 0
    for aid, nf in plan:
        for f in range(0, nf, 2):
            d = (step_global // 4) % N_DIRS
            step_global += 1
            bg = Image.new("RGBA", (OUT_W, OUT_H), (20, 25, 36, 255))
            bg.alpha_composite(Image.fromarray(all_out_frames[aid][d][f], "RGBA"))
            q = bg.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
            gif_frames.append(q)
    gif_frames[0].save(out_gif, save_all=True, append_images=gif_frames[1:], duration=33, loop=0)


def main() -> None:
    t0 = time.time()
    spr32_only = ("--spr32-only" in sys.argv)
    os.makedirs(ATLAS_DIR, exist_ok=True)
    print("[1/5] Building 16-angle photorealistic studio turnarounds & real gib parts...")
    turnarounds = build_all_16_turnarounds()
    gib_parts = extract_real_gib_parts()
    gib_hist = precompute_3d_gib_trajectories(48)

    if not spr32_only:
        save_turnaround_audit_sheet(turnarounds, os.path.join(HERE, "work", "audit_16angle_final.jpg"))

    # Compact 248-frame 8-direction layout for QuakeC GreenSuit_Customize (d = 0..7 -> even d_i = 0,2,..,14):
    #   0   + d*4 + k : cruise          (4 steps, 32 frames, 0..31)
    #   32  + d*4 + k : charge          (4 steps, 32 frames, 32..63)
    #   64  + d*6 + s : jump_slam       (6 steps, 48 frames, 64..111)
    #   112 + d*4 + s : whirlwind_melee (4 steps, 32 frames, 112..143)
    #   144 + d*4 + k : wheelie_taunt   (4 steps, 32 frames, 144..175)
    #   176 + d*4 + s : pain            (4 steps, 32 frames, 176..207)
    #   208 + d*5 + s : gib_death       (5 steps, 40 frames, 208..247)
    spr_plan = [
        ("cruise",          [0, 9, 18, 27]),
        ("charge",          [0, 8, 15, 23]),
        ("jump_slam",       [2, 11, 20, 28, 38, 46]),
        ("whirlwind_melee", [0, 10, 18, 28]),
        ("wheelie_taunt",   [0, 9, 18, 27]),
        ("pain",            [0, 7, 14, 21]),
        ("gib_death",       [1, 11, 21, 33, 47]),
    ]
    nf_by_id = {s["id"]: s["frames"] for s in ANIM_SPECS}

    all_out_frames: Dict[str, List[List[np.ndarray]]] = {}
    atlas_paths: Dict[str, str] = {}

    if spr32_only:
        print("[2/3] Synthesizing 248 compact 8-angle frames for DarkPlaces progs/greensuit_wheelman.spr32...")
        req_tasks: List[Tuple[str, int, int]] = [
            (aid, d_i, fi)
            for aid, kf_list in spr_plan
            for d_i in range(0, N_DIRS, 2)
            for fi in kf_list
        ]

        def _dp_direct(item: Tuple[str, int, int]) -> np.ndarray:
            aid, d_i, f_i = item
            ss_rgba = render_monster_frame_ss(aid, d_i, f_i, nf_by_id[aid], turnarounds, gib_hist, gib_parts)
            rs = resize_rgba_premul(ss_rgba, DP_W, DP_H)
            return tone_for_darkplaces_rgba(rs)

        with ThreadPoolExecutor(max_workers=12) as ex:
            dp_toned = list(ex.map(_dp_direct, req_tasks))

        assert len(dp_toned) == 248, f"Expected 248 SPR32 frames, got {len(dp_toned)}"
        spr_out = os.path.join(PROGS_DIR, "greensuit_wheelman.spr32")
        spr_mb = write_darkplaces_spr32(spr_out, dp_toned)
        print(f"[3/3] Wrote {spr_out} (248 frames, 8 angles, tight-cropped {DP_W}x{DP_H}, {spr_mb:.2f} MiB) in {time.time() - t0:.1f}s!")
        return

    print("[2/5] Synthesizing all 4,224 frames (7 animations x 16 angles @ native 60 FPS)...")
    for spec in ANIM_SPECS:
        aid = spec["id"]
        nf = spec["frames"]
        t_anim = time.time()

        tasks: List[Tuple[int, int]] = [(d, f) for d in range(N_DIRS) for f in range(nf)]

        def _worker(df: Tuple[int, int]) -> Tuple[int, int, np.ndarray]:
            d_i, f_i = df
            ss_rgba = render_monster_frame_ss(aid, d_i, f_i, nf, turnarounds, gib_hist, gib_parts)
            out_rgba = resize_rgba_premul(ss_rgba, OUT_W, OUT_H)
            return d_i, f_i, out_rgba

        grid: List[List[np.ndarray]] = [[None] * nf for _ in range(N_DIRS)]  # type: ignore
        with ThreadPoolExecutor(max_workers=12) as ex:
            for d_i, f_i, out_rgba in ex.map(_worker, tasks):
                grid[d_i][f_i] = out_rgba

        all_out_frames[aid] = grid

        # Assemble 16-row x nf-col WebP atlas
        atlas_arr = np.zeros((N_DIRS * OUT_H, nf * OUT_W, 4), dtype=np.uint8)
        for d_i in range(N_DIRS):
            y0 = d_i * OUT_H
            for f_i in range(nf):
                x0 = f_i * OUT_W
                atlas_arr[y0:y0 + OUT_H, x0:x0 + OUT_W] = grid[d_i][f_i]

        webp_path = os.path.join(ATLAS_DIR, f"{aid}.webp")
        Image.fromarray(atlas_arr, "RGBA").save(webp_path, "WEBP", quality=82, method=4)
        atlas_paths[aid] = webp_path
        sz_mb = os.path.getsize(webp_path) / (1024.0 * 1024.0)
        print(f"  -> {aid:16s}: {N_DIRS}x{nf:2d} = {N_DIRS*nf:3d} frames -> {sz_mb:.2f} MB WebP ({time.time() - t_anim:.1f}s)")

    print("[3/5] Packing 248-frame 8-Angle tight-cropped DarkPlaces progs/greensuit_wheelman.spr32...")
    dp_tasks: List[np.ndarray] = []
    for aid, kf_list in spr_plan:
        for d_i in range(0, N_DIRS, 2):
            for fi in kf_list:
                dp_tasks.append(all_out_frames[aid][d_i][fi])

    def _dp_tone(fr_rgba: np.ndarray) -> np.ndarray:
        rs = resize_rgba_premul(fr_rgba, DP_W, DP_H)
        return tone_for_darkplaces_rgba(rs)

    with ThreadPoolExecutor(max_workers=12) as ex:
        dp_toned = list(ex.map(_dp_tone, dp_tasks))

    assert len(dp_toned) == 248, f"Expected 248 SPR32 frames, got {len(dp_toned)}"
    spr_out = os.path.join(PROGS_DIR, "greensuit_wheelman.spr32")
    spr_mb = write_darkplaces_spr32(spr_out, dp_toned)
    print(f"  -> Wrote {spr_out} (248 frames, 8 angles, {spr_mb:.2f} MiB)")

    print("[4/5] Rendering Real-Photo Accuracy Poster & 360° Action Preview GIF...")
    poster_jpg = os.path.join(OUT_PACK_DIR, "turnaround_and_accuracy_poster.jpg")
    build_accuracy_and_16angle_poster(turnarounds, all_out_frames, poster_jpg)
    preview_gif = os.path.join(OUT_PACK_DIR, "greensuit_monster_360_preview.gif")
    save_preview_gif(all_out_frames, preview_gif)

    meta = {
        "cellW": OUT_W,
        "cellH": OUT_H,
        "groundY": OUT_GROUND,
        "dirs": N_DIRS,
        "totalFrames": sum(s["frames"] * N_DIRS for s in ANIM_SPECS),
        "spr32Frames": 960,
        "anims": ANIM_SPECS,
    }
    with open(os.path.join(OUT_PACK_DIR, "sprite_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("[5/5] Building 100% Self-Contained HTML5 Showcase...")
    root_html = os.path.join(MOD_ROOT, "greensuit_wheelman_monster.html")
    pack_html = os.path.join(OUT_PACK_DIR, "index.html")
    html_mb = write_self_contained_html(root_html, meta, atlas_paths, poster_jpg)
    with open(root_html, "rb") as f_src, open(pack_html, "wb") as f_dst:
        f_dst.write(f_src.read())
    print(f"  -> Wrote self-contained {root_html} ({html_mb:.2f} MB) in {time.time() - t0:.1f}s total!")


if __name__ == "__main__":
    main()
