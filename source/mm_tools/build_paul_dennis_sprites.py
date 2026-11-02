"""End-to-end reproducible builder for Paul ('Screaming Paul') and Dennis ('Reading Dennis')
character game sprites in BakersfieldQuake (graphics only — does not touch QC or .dat files).

Outputs:
  - progs/fr_paul.spr32            (56-frame DarkPlaces SPR32: 0..7 idle, 8..55 8-dir x 6 run)
  - progs/fr_dennis.spr32          (56-frame DarkPlaces SPR32: 0..7 idle, 8..55 8-dir x 6 run)
  - paul_sprite/                   (idle PNGs, 8x8 run PNGs, 8-frame scream PNGs, sheet, GIF, HTML)
  - dennis_sprite/                 (idle PNGs, 8x8 run PNGs, 8-frame lecture PNGs, sheet, GIF, HTML)
  - paul_dennis_sprites.html       (combined side-by-side interactive 360° showcase)

Run with:
  python3.13 source/mm_tools/build_paul_dennis_sprites.py
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "paul_dennis"

sys.path.insert(0, str(TOOLS_DIR))
from paul_dennis_rig import (
    CANVAS_W,
    CANVAS_H,
    TOP_Y,
    GROUND_Y,
    alpha_over,
    crop_normalize_view,
    graft_dennis_lecture_gesture,
    graft_video_face,
    key_magenta_studio,
    mirror_canvas_horiz,
    open_paul_jaw_90_photoreal,
    render_front_or_back_run_frame,
    render_side_or_diag_run_frame,
    warp_limb_3bone,
    warp_rigid_rgba,
)
from paul_dennis_viewer_html import (
    build_character_viewer_html,
    build_combined_showcase_html,
)

# In-game SPR32 dimensions (matches friends.qc / mbox.qc .scale 0.5 convention alongside fr_rob.spr32)
SPR_W = 96
SPR_H = 128
SPR_OX = -(SPR_W // 2)
SPR_OY = round(GROUND_Y * SPR_H / CANVAS_H)  # 119 px (origin anchored at feet)
RUN_6_INDICES = [0, 1, 2, 4, 5, 6]           # 6 evenly-paced frames from the 8-frame run cycle


def resize_rgba_premul(rgba: np.ndarray, tw: int, th: int) -> np.ndarray:
    """Resizes straight-RGBA via premultiplied-alpha Lanczos so transparent silhouettes never halo."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_u8 = np.clip(np.round(pm), 0, 255).astype(np.uint8)
    pm_im = Image.fromarray(pm_u8, "RGBA").resize((tw, th), Image.Resampling.LANCZOS)
    p = np.asarray(pm_im, dtype=np.float32)
    pa = p[..., 3:4] / 255.0
    rgb = np.where(pa > 1e-3, p[..., :3] / np.maximum(pa, 1e-3), 0.0)
    # Crisp slight alpha threshold so low-res in-game edges stay clean
    a_out = np.where(p[..., 3] < 10.0, 0.0, p[..., 3])
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(a_out), 0, 255).astype(np.uint8),
    ])


def pretone_for_darkplaces_hdr(frames_rgba: list[np.ndarray], target_mean_lum: float = 62.0) -> list[np.ndarray]:
    """Pre-tones SPR32 RGB for DarkPlaces r_hdr_scenebrightness 2.5 so sprites match fr_rob.spr32 (~60-65 lum)."""
    # First boost local micro-contrast slightly so facial features & suit folds read crisply in Quake lighting
    boosted: list[np.ndarray] = []
    lums = []
    for fr in frames_rgba:
        rgb_im = Image.fromarray(fr[..., :3], "RGB")
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(1.16)
        rgb_im = ImageEnhance.Color(rgb_im).enhance(1.06)
        rgb = np.asarray(rgb_im, dtype=np.float32)
        mask = fr[..., 3] > 128
        if np.any(mask):
            lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
            lums.append(float(lum[mask].mean()))
        boosted.append(np.dstack([np.clip(np.round(rgb), 0, 255).astype(np.uint8), fr[..., 3]]))

    cur_mean = float(np.mean(lums)) if lums else 100.0
    gain = float(np.clip(target_mean_lum / max(1.0, cur_mean), 0.38, 0.92))
    out: list[np.ndarray] = []
    for fr in boosted:
        toned = fr.copy()
        toned[..., :3] = np.clip(np.round(toned[..., :3].astype(np.float32) * gain), 0, 255).astype(np.uint8)
        out.append(toned)
    return out


def write_spr32(path: Path, frames_rgba: list[np.ndarray], ox: int = SPR_OX, oy: int = SPR_OY) -> tuple[int, float]:
    """Writes a standard 56-frame IDSP v32 SPR_VP_PARALLEL_UPRIGHT (stype=0) Quake sprite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    maxw = max(f.shape[1] for f in frames_rgba)
    maxh = max(f.shape[0] for f in frames_rgba)
    rad = math.sqrt((maxw / 2.0) ** 2 + float(maxh) ** 2)

    buf = bytearray()
    buf += b"IDSP"
    buf += struct.pack("<iifiiifi", 32, 0, rad, maxw, maxh, len(frames_rgba), 0.0, 0)

    lums = []
    for fr in frames_rgba:
        h, w = fr.shape[:2]
        buf += struct.pack("<i", 0)
        buf += struct.pack("<iiii", ox, oy, w, h)
        buf += fr.tobytes()
        m = fr[..., 3] > 128
        if np.any(m):
            rgb = fr[..., :3].astype(np.float32)
            lums.append(float((0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[m].mean()))

    path.write_bytes(bytes(buf))
    return len(buf), (float(np.mean(lums)) if lums else 0.0)


def save_sheet_8x8(run_grid: list[list[np.ndarray]], out_path: Path, cell_w: int = 240, cell_h: int = 320) -> None:
    sheet = Image.new("RGBA", (cell_w * 8, cell_h * 8), (0, 0, 0, 0))
    for d in range(8):
        for f in range(8):
            cell = resize_rgba_premul(run_grid[d][f], cell_w, cell_h)
            sheet.paste(Image.fromarray(cell, "RGBA"), (f * cell_w, d * cell_h))
    sheet.save(out_path, optimize=True)


def save_turntable_gif(run_grid: list[list[np.ndarray]], action_frames: list[np.ndarray], out_path: Path) -> None:
    """Builds a smooth 360° spinning run + signature expression showcase GIF on dark checker backdrop."""
    gw, gh = 270, 360
    yg, xg = np.mgrid[0:gh, 0:gw]
    chk = ((xg // 15 + yg // 15) % 2 == 0)
    bg_arr = np.where(chk[..., None], np.array([38, 42, 52], np.uint8), np.array([28, 31, 39], np.uint8))

    seq: list[Image.Image] = []
    # 24 frames orbiting 360° while running (3 run steps per 45° angle)
    for step in range(24):
        d = (step // 3) % 8
        f = step % 8
        cell = resize_rgba_premul(run_grid[d][f], gw, gh)
        im = Image.fromarray(bg_arr, "RGB").convert("RGBA")
        im.alpha_composite(Image.fromarray(cell, "RGBA"))
        seq.append(im.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))

    # Append 8 signature expression frames (holding peak expression 2 ticks)
    for idx, afr in enumerate(action_frames):
        cell = resize_rgba_premul(afr, gw, gh)
        im = Image.fromarray(bg_arr, "RGB").convert("RGBA")
        im.alpha_composite(Image.fromarray(cell, "RGBA"))
        p_im = im.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        seq.append(p_im)
        if idx in (5, 6):
            seq.append(p_im)

    seq[0].save(
        out_path,
        save_all=True,
        append_images=seq[1:],
        duration=90,
        loop=0,
        optimize=True,
    )


def pose_paul_scream_body(studio_front: np.ndarray, vid_rgb: np.ndarray, el: tuple[float, float], er: tuple[float, float], intensity: float) -> np.ndarray:
    """Grafts Paul's real video expression and adds progressive upper-body tension as intensity -> 1.0."""
    # Oval grows downward slightly on wide-open scream frames so dropped jaw/teeth never clip
    ry_bot = 25.0 + 6.5 * intensity
    cy_off = 16.5 + 2.2 * intensity
    faced = graft_video_face(
        studio_front,
        vid_rgb,
        src_eye_l=el,
        src_eye_r=er,
        dst_eye_l=(229.0, 89.5),
        dst_eye_r=(251.5, 89.5),
        oval_cy_offset=cy_off,
        oval_rx=20.5,
        oval_ry_top=17.5,
        oval_ry_bot=ry_bot,
        chin_drop_shadow=(intensity > 0.35),
    )
    if intensity <= 0.05:
        return faced

    # Subtle upper-body forward lunge & shoulder flare on high-intensity scream frames!
    H, W = faced.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    t_hip = np.clip((yg.astype(np.float32) - 245.0) / 85.0, 0.0, 1.0)
    x_cut_l = 189.0 - 13.0 * t_hip
    x_cut_r = 291.0 + 10.0 * t_hip
    arm_l_m = (xg < x_cut_l) & (yg >= 164) & (yg <= 388) & (faced[..., 3] > 0)
    arm_r_m = (xg > x_cut_r) & (yg >= 164) & (yg <= 388) & (faced[..., 3] > 0)
    overlap = 8.5 * (1.0 - np.clip((yg.astype(np.float32) - 235.0) / 55.0, 0.0, 1.0))
    legs_m = (yg >= 346) & (~arm_l_m) & (~arm_r_m) & (faced[..., 3] > 0)
    torso_m = (yg < 352) & (faced[..., 3] > 0) & (
        (yg < 164) | ((xg >= (x_cut_l - overlap)) & (xg <= (x_cut_r + overlap)))
    )

    legs = np.where(legs_m[..., None], faced, 0)
    torso = np.where(torso_m[..., None], faced, 0)
    for yy in range(346, 352):
        torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((352 - yy) / 6.0)).astype(np.uint8)
    arm_l = np.where(arm_l_m[..., None], faced, 0)
    arm_r = np.where(arm_r_m[..., None], faced, 0)

    sc = 1.0 + 0.028 * intensity
    dy = -2.5 * intensity
    torso_w = warp_rigid_rgba(torso, (240.0, 340.0), sx=sc, sy=sc, dy=dy)
    arm_l_w = warp_limb_3bone(
        arm_l, (182.0, 176.0), (175.0, 265.0), (172.0, 342.0),
        ang_upper=4.5 * intensity, ang_lower=9.0 * intensity, sy_lower=1.0 - 0.06 * intensity,
        dx=-2.0 * intensity, dy=dy,
    )
    arm_r_w = warp_limb_3bone(
        arm_r, (298.0, 176.0), (305.0, 265.0), (308.0, 342.0),
        ang_upper=-4.5 * intensity, ang_lower=-9.0 * intensity, sy_lower=1.0 - 0.06 * intensity,
        dx=+2.0 * intensity, dy=dy,
    )
    out = alpha_over(legs, torso_w)
    out = alpha_over(out, arm_l_w)
    out = alpha_over(out, arm_r_w)
    return out


def build_paul(lm: dict) -> None:
    print("=== Building PAUL ('Screaming Paul') ===")
    out_dir = ROOT_DIR / "paul_sprite"
    spr_dir = out_dir / "spr32"
    spr_dir.mkdir(parents=True, exist_ok=True)

    p_front_key = key_magenta_studio(Image.open(REF_DIR / "paul_studio_front.jpg"))
    p_turn_key = key_magenta_studio(Image.open(REF_DIR / "paul_studio_turn.jpg"))

    # Canonical 5 left-oriented views: 0°, 45°, 90°, 135°, 180°
    p5_raw = [
        crop_normalize_view(p_front_key, (0, 0, p_front_key.shape[1], p_front_key.shape[0]), mirror=False),
        crop_normalize_view(p_turn_key, (15, 25, 310, 975), mirror=True),     # 45° front-left
        crop_normalize_view(p_turn_key, (315, 25, 508, 975), mirror=True),    # 90° left profile
        crop_normalize_view(p_turn_key, (508, 25, 715, 975), mirror=False),   # 135° back-left
        crop_normalize_view(p_turn_key, (718, 25, 1010, 975), mirror=False),  # 180° back
    ]

    def load_p_exp(fidx: int):
        info = lm["paul"][str(fidx)]
        im = np.asarray(Image.open(REF_DIR / info["file"]).convert("RGB"))
        return im, tuple(info["eye_l"]), tuple(info["eye_r"]), tuple(info["mouth"])

    # Graft authentic video f=0 warm smile onto Paul's 0° standing idle
    v0, el0, er0, _ = load_p_exp(0)
    idle_0 = graft_video_face(
        p5_raw[0], v0, el0, er0, (229.0, 89.5), (251.5, 89.5),
        oval_cy_offset=16.5, oval_rx=20.0, oval_ry_top=16.5, oval_ry_bot=24.5,
    )

    # 8-direction standing idle (0..7)
    idle_8 = [
        idle_0,
        p5_raw[1],
        p5_raw[2],
        p5_raw[3],
        p5_raw[4],
        mirror_canvas_horiz(p5_raw[3]),
        mirror_canvas_horiz(p5_raw[2]),
        mirror_canvas_horiz(p5_raw[1]),
    ]
    for d, im in enumerate(idle_8):
        Image.fromarray(im, "RGBA").save(out_dir / f"paul_idle_d{d}.png", optimize=True)

    # Screaming bases for frantic sprinting!
    # d=0 cycles live across real screaming frames [100, 104, 108, 116, 124, 116, 108, 104]!
    scream_cycle_f = [100, 104, 108, 116, 124, 116, 108, 104]
    front_scream_bases = []
    for vf in scream_cycle_f:
        vim, vel, ver, _ = load_p_exp(vf)
        front_scream_bases.append(
            graft_video_face(
                p5_raw[0], vim, vel, ver, (229.0, 89.5), (251.5, 89.5),
                oval_cy_offset=18.5, oval_rx=20.5, oval_ry_top=17.5, oval_ry_bot=31.0,
                chin_drop_shadow=True,
            )
        )

    v104, el104, er104, m104 = load_p_exp(104)
    p45_scream = graft_video_face(
        p5_raw[1], v104, el104, er104, (213.5, 83.5), (232.5, 83.5),
        oval_cy_offset=23.5, oval_rx=10.2, oval_ry_top=8.8, oval_ry_bot=14.8,
        oval_dx=+0.5, chin_drop_shadow=True,
        src_mouth=m104, dst_mouth=(222.5, 107.5),
    )
    p90_scream = open_paul_jaw_90_photoreal(p5_raw[2])

    # Synthesize canonical 5 directions x 8 run frames
    run_5: list[list[np.ndarray]] = []
    run_5.append([render_front_or_back_run_frame(front_scream_bases[f], f, 8, is_back=False) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(p45_scream, 45, f, 8) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(p90_scream, 90, f, 8) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(p5_raw[3], 135, f, 8) for f in range(8)])
    run_5.append([render_front_or_back_run_frame(p5_raw[4], f, 8, is_back=True) for f in range(8)])

    run_8: list[list[np.ndarray]] = [
        run_5[0],
        run_5[1],
        run_5[2],
        run_5[3],
        run_5[4],
        [mirror_canvas_horiz(run_5[3][(f + 4) % 8]) for f in range(8)],
        [mirror_canvas_horiz(run_5[2][(f + 4) % 8]) for f in range(8)],
        [mirror_canvas_horiz(run_5[1][(f + 4) % 8]) for f in range(8)],
    ]
    for d in range(8):
        for f in range(8):
            Image.fromarray(run_8[d][f], "RGBA").save(out_dir / f"paul_d{d}_f{f}.png", optimize=True)

    # Signature 8-frame escalating "Paul... Pauuul... PAAAAUUUUUL!" sequence
    scream_seq_spec = [
        (0, 0.00),
        (14, 0.15),
        (38, 0.30),
        (52, 0.45),
        (92, 0.72),
        (100, 0.90),
        (108, 0.96),
        (124, 1.00),
    ]
    scream_8: list[np.ndarray] = []
    for i, (vf, inten) in enumerate(scream_seq_spec):
        vim, vel, ver, _ = load_p_exp(vf)
        fr = pose_paul_scream_body(p5_raw[0], vim, vel, ver, inten)
        scream_8.append(fr)
        Image.fromarray(fr, "RGBA").save(out_dir / f"paul_scream_{i:02d}.png", optimize=True)

    # Assemble 56 SPR32 frames (0..7 idle, 8..55 8-dir x 6 run)
    spr_display_frames: list[np.ndarray] = []
    for d in range(8):
        spr_display_frames.append(resize_rgba_premul(idle_8[d], SPR_W, SPR_H))
    for d in range(8):
        for k in RUN_6_INDICES:
            spr_display_frames.append(resize_rgba_premul(run_8[d][k], SPR_W, SPR_H))

    for idx, sfr in enumerate(spr_display_frames):
        Image.fromarray(sfr, "RGBA").save(spr_dir / f"f_{idx:02d}.png", optimize=True)

    spr_toned = pretone_for_darkplaces_hdr(spr_display_frames, target_mean_lum=62.0)
    spr_path = ROOT_DIR / "progs" / "fr_paul.spr32"
    nbytes, mlum = write_spr32(spr_path, spr_toned)
    print(f"  Wrote {spr_path} ({len(spr_toned)} frames, {nbytes / 1e6:.2f} MB, mean_lum={mlum:.1f})")

    save_sheet_8x8(run_8, out_dir / "paul_360_sheet_8x8.png")
    save_turntable_gif(run_8, scream_8, out_dir / "paul_360_spin.gif")
    (out_dir / "index.html").write_text(
        build_character_viewer_html(
            char_key="paul",
            title='PAUL — "PAAAAUUUUUL!" Character Sprite',
            subtitle="8-Direction 360° Idle & Frantic Scream-Run Cycle · Real Video Expression Graft · DarkPlaces .SPR32",
            action_tab_label='😱 "PAAAAUUUUUL!" Scream (8f)',
            action_prefix="paul_scream",
            n_dirs=8,
            n_run=8,
            n_action=8,
            canvas_w=CANVAS_W,
            canvas_h=CANVAS_H,
            ground_y=GROUND_Y,
            spr_w=SPR_W,
            spr_h=SPR_H,
            accent="#fb923c",
        ),
        encoding="utf-8",
    )


def build_dennis(lm: dict) -> None:
    print("=== Building DENNIS ('Reading For 30 Years') ===")
    out_dir = ROOT_DIR / "dennis_sprite"
    spr_dir = out_dir / "spr32"
    spr_dir.mkdir(parents=True, exist_ok=True)

    d_front_key = key_magenta_studio(Image.open(REF_DIR / "dennis_studio_front.jpg"))
    d_turn_key = key_magenta_studio(Image.open(REF_DIR / "dennis_studio_turn.jpg"))

    d5_raw = [
        crop_normalize_view(d_front_key, (0, 0, d_front_key.shape[1], d_front_key.shape[0]), mirror=False),
        crop_normalize_view(d_turn_key, (95, 25, 420, 1000), mirror=False),   # 45° front-left
        crop_normalize_view(d_turn_key, (565, 25, 700, 510), mirror=False),   # 90° left profile
        crop_normalize_view(d_turn_key, (555, 520, 735, 1015), mirror=False), # 135° back-left
        crop_normalize_view(d_turn_key, (780, 520, 970, 1015), mirror=False), # 180° back
    ]

    def load_d_exp(fidx: int):
        info = lm["dennis"][str(fidx)]
        im = np.asarray(Image.open(REF_DIR / info["file"]).convert("RGB"))
        return im, tuple(info["eye_l"]), tuple(info["eye_r"])

    # Graft authentic video f=0 warm friendly smile onto Dennis's 0° standing idle
    v0, el0, er0 = load_d_exp(0)
    idle_0 = graft_video_face(
        d5_raw[0], v0, el0, er0, (229.0, 82.5), (251.0, 81.5),
        oval_cy_offset=16.0, oval_rx=19.5, oval_ry_top=14.0, oval_ry_bot=24.5,
    )

    idle_8 = [
        idle_0,
        d5_raw[1],
        d5_raw[2],
        d5_raw[3],
        d5_raw[4],
        mirror_canvas_horiz(d5_raw[3]),
        mirror_canvas_horiz(d5_raw[2]),
        mirror_canvas_horiz(d5_raw[1]),
    ]
    for d, im in enumerate(idle_8):
        Image.fromarray(im, "RGBA").save(out_dir / f"dennis_idle_d{d}.png", optimize=True)

    # Live speaking expressions across 0° front run cycle!
    talk_cycle_f = [0, 5, 25, 48, 65, 55, 25, 5]
    front_talk_bases = []
    for vf in talk_cycle_f:
        vim, vel, ver = load_d_exp(vf)
        front_talk_bases.append(
            graft_video_face(
                d5_raw[0], vim, vel, ver, (229.0, 82.5), (251.0, 81.5),
                oval_cy_offset=16.0, oval_rx=19.5, oval_ry_top=14.0, oval_ry_bot=24.5,
            )
        )

    run_5: list[list[np.ndarray]] = []
    run_5.append([render_front_or_back_run_frame(front_talk_bases[f], f, 8, is_back=False) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(d5_raw[1], 45, f, 8) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(d5_raw[2], 90, f, 8) for f in range(8)])
    run_5.append([render_side_or_diag_run_frame(d5_raw[3], 135, f, 8) for f in range(8)])
    run_5.append([render_front_or_back_run_frame(d5_raw[4], f, 8, is_back=True) for f in range(8)])

    run_8: list[list[np.ndarray]] = [
        run_5[0],
        run_5[1],
        run_5[2],
        run_5[3],
        run_5[4],
        [mirror_canvas_horiz(run_5[3][(f + 4) % 8]) for f in range(8)],
        [mirror_canvas_horiz(run_5[2][(f + 4) % 8]) for f in range(8)],
        [mirror_canvas_horiz(run_5[1][(f + 4) % 8]) for f in range(8)],
    ]
    for d in range(8):
        for f in range(8):
            Image.fromarray(run_8[d][f], "RGBA").save(out_dir / f"dennis_d{d}_f{f}.png", optimize=True)

    # Signature 8-frame "My name is Dennis. I've been reading to you for 30 years" speaking & lecturing gesture
    read_seq_spec = [
        (0, 0.00),
        (25, 0.00),
        (55, 0.26),
        (79, 0.74),
        (84, 0.96),
        (89, 1.00),
        (96, 0.88),
        (48, 0.28),
    ]
    read_8: list[np.ndarray] = []
    for i, (vf, rt) in enumerate(read_seq_spec):
        vim, vel, ver = load_d_exp(vf)
        fr = graft_dennis_lecture_gesture(d5_raw[0], vim, vel, ver, rt)
        read_8.append(fr)
        Image.fromarray(fr, "RGBA").save(out_dir / f"dennis_read_{i:02d}.png", optimize=True)

    # Assemble 56 SPR32 frames (0..7 idle, 8..55 8-dir x 6 run)
    spr_display_frames: list[np.ndarray] = []
    for d in range(8):
        spr_display_frames.append(resize_rgba_premul(idle_8[d], SPR_W, SPR_H))
    for d in range(8):
        for k in RUN_6_INDICES:
            spr_display_frames.append(resize_rgba_premul(run_8[d][k], SPR_W, SPR_H))

    for idx, sfr in enumerate(spr_display_frames):
        Image.fromarray(sfr, "RGBA").save(spr_dir / f"f_{idx:02d}.png", optimize=True)

    spr_toned = pretone_for_darkplaces_hdr(spr_display_frames, target_mean_lum=62.0)
    spr_path = ROOT_DIR / "progs" / "fr_dennis.spr32"
    nbytes, mlum = write_spr32(spr_path, spr_toned)
    print(f"  Wrote {spr_path} ({len(spr_toned)} frames, {nbytes / 1e6:.2f} MB, mean_lum={mlum:.1f})")

    save_sheet_8x8(run_8, out_dir / "dennis_360_sheet_8x8.png")
    save_turntable_gif(run_8, read_8, out_dir / "dennis_360_spin.gif")
    (out_dir / "index.html").write_text(
        build_character_viewer_html(
            char_key="dennis",
            title='DENNIS — "Reading For 30 Years" Character Sprite',
            subtitle="8-Direction 360° Idle & Suit Run Cycle · Earnest Speaking & Hand Gesture · DarkPlaces .SPR32",
            action_tab_label='📖 "Reading 30 Years" Gesture (8f)',
            action_prefix="dennis_read",
            n_dirs=8,
            n_run=8,
            n_action=8,
            canvas_w=CANVAS_W,
            canvas_h=CANVAS_H,
            ground_y=GROUND_Y,
            spr_w=SPR_W,
            spr_h=SPR_H,
            accent="#38bdf8",
        ),
        encoding="utf-8",
    )


def main() -> None:
    lm_path = REF_DIR / "expression_landmarks.json"
    with open(lm_path, "r", encoding="utf-8") as fp:
        lm = json.load(fp)

    build_paul(lm)
    build_dennis(lm)

    combo_html = ROOT_DIR / "paul_dennis_sprites.html"
    combo_html.write_text(build_combined_showcase_html(CANVAS_W, CANVAS_H), encoding="utf-8")
    print(f"=== Wrote combined showcase: {combo_html} ===")


if __name__ == "__main__":
    main()
