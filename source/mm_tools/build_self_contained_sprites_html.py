"""Builds the upgraded High-FPS (up to 60 FPS), Multi-Animation 100% self-contained HTML inspector
(G:/Quake/Combat/BakersfieldQuake/character_sprites_inspector.html)
plus transparent animation contact sheets on disk for QuakeGuy, Paul, and Dennis.

Animations packed per character (484 frames per character = 1,452 embedded frames total):
  1. 360° Run Cycle        : 8 angles x 16 frames = 128f (360° orbitable)
  2. Turbo Sprint / Dash   : 24f (forward sprint lean + glowing afterimages + wind streaks + dust)
  3. 360° Combat Jump      : 8 angles x 18 frames = 144f (360° orbitable crouch, launch, tuck & land)
  4. Acrobatic Frontflip   : 32f (deep coil -> 360° tucked mid-air somersault -> shockwave landing)
  5. Mega Gib Explosion    : 48f (5-act core overload, HDR starburst, VFX fireball, flying head/limbs/props & 18 gibs)
  6. Signature Action      : 24f (QuakeGuy Combat Launch / Paul Sonic Scream / Dennis 30-Year Lecture)
  7. 360° Standing Idle    : 8f  (8 angles)
  8. Quake .SPR32          : 56f (exact 96x128 in-game sprite frames)

Run with:
  python3.13 source/mm_tools/build_self_contained_sprites_html.py
"""

from __future__ import annotations

import base64
import io
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent.parent
PD_REF = TOOLS_DIR / "ref" / "paul_dennis"
QG_REF = TOOLS_DIR / "ref" / "quakeguy"

sys.path.insert(0, str(TOOLS_DIR))
from build_paul_dennis_sprites import pose_paul_scream_body, resize_rgba_premul
from build_quakeguy_sprite import IDLE_8_FRAMES, key_white_studio_quakeguy
from character_action_fx import (
    ACT_GROUND_Y,
    build_frontflip_32,
    build_jump_8x18,
    build_mega_explosion_48,
    build_turbo_sprint_24,
    overlay_sonic_scream_rings,
)
from paul_dennis_rig import (
    CANVAS_H,
    CANVAS_W,
    GROUND_Y,
    TOP_Y,
    crop_normalize_view,
    graft_dennis_lecture_gesture,
    graft_video_face,
    key_magenta_studio,
    mirror_canvas_horiz,
    open_paul_jaw_90_photoreal,
    render_front_or_back_run_frame,
    render_side_or_diag_run_frame,
)

# Embedded WebP cell dimensions:
#   - 210x280 for huge 128-frame / 144-frame 8-direction grids
#   - 270x360 for 8f / 24f / 32f / 48f hero sequences & explosions
GRID_W, GRID_H = 210, 280
SEQ_W, SEQ_H = 270, 360
SPR_W, SPR_H = 96, 128


def encode_atlas(images: list[np.ndarray | Image.Image], cols: int, cw: int, ch: int, lossless: bool = False, quality: int = 90) -> str:
    rows = (len(images) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    for idx, item in enumerate(images):
        if isinstance(item, np.ndarray):
            if item.shape[1] != cw or item.shape[0] != ch:
                im = Image.fromarray(resize_rgba_premul(item, cw, ch), "RGBA")
            else:
                im = Image.fromarray(item, "RGBA")
        else:
            im = item if item.size == (cw, ch) else item.resize((cw, ch), Image.Resampling.LANCZOS)
        r, c = divmod(idx, cols)
        atlas.paste(im, (c * cw, r * ch))

    buf = io.BytesIO()
    if lossless:
        atlas.save(buf, format="PNG", compress_level=6)
        mime = "image/png"
    else:
        atlas.save(buf, format="WEBP", quality=quality, alpha_quality=95, method=4)
        mime = "image/webp"
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def save_contact_sheet(frames: list[np.ndarray], cols: int, cw: int, ch: int, out_path: Path) -> None:
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    for idx, fr in enumerate(frames):
        r, c = divmod(idx, cols)
        cell = Image.fromarray(resize_rgba_premul(fr, cw, ch), "RGBA")
        sheet.paste(cell, (c * cw, r * ch))
    sheet.save(out_path, compress_level=6)


# ---------------------------------------------------------------------------
# High-FPS Character Sequence Builders (QuakeGuy, Paul, Dennis)
# ---------------------------------------------------------------------------

QG_RUN16_PLAN: dict[int, list[tuple[int, bool]]] = {
    0: [(f, False) for f in range(307, 323)],                                                        # 0° Front (16f)
    1: [(f, False) for f in range(85, 101)],                                                         # 45° Front-Left (16f)
    2: [(f, False) for f in range(125, 141)],                                                        # 90° Left Profile (16f)
    3: [(f, False) for f in range(148, 156)] + [(f, True) for f in range(198, 206)],                 # 135° Back-Left (16f)
    4: [(f, False) for f in range(166, 182)],                                                        # 180° Back (16f)
    5: [(f, False) for f in range(198, 206)] + [(f, True) for f in range(148, 156)],                 # 225° Back-Right (16f)
    6: [(f, False) for f in range(212, 228)],                                                        # 270° Right Profile (16f)
    7: [(f, False) for f in range(244, 260)],                                                        # 315° Front-Right (16f, unmirrored QUAKE logo)
}


def build_quakeguy_all() -> dict:
    t0 = time.perf_counter()
    print("=== [1/3] Generating High-FPS Multi-Animations for QUAKEGUY ===")
    folder = ROOT_DIR / "quakeguy_sprite"
    meta = json.loads((QG_REF / "quakeguy_meta.json").read_text(encoding="utf-8"))
    cache: dict[int, np.ndarray] = {}

    def get_norm(fi: int) -> np.ndarray:
        if fi in cache:
            return cache[fi]
        info = meta["frames"][str(fi)]
        rgb = np.asarray(Image.open(QG_REF / info["file"]).convert("RGB"))
        rgba = key_white_studio_quakeguy(rgb)
        char_h = max(400.0, float(info["floor_y"] - info["head_y"]))
        sc = (GROUND_Y - TOP_Y) / char_h
        nw = max(1, int(round(rgba.shape[1] * sc)))
        nh = max(1, int(round(rgba.shape[0] * sc)))
        scaled = Image.fromarray(resize_rgba_premul(rgba, nw, nh), "RGBA")
        ox = int(round(CANVAS_W / 2.0 - float(info["cx"]) * sc))
        oy = int(round(GROUND_Y - float(info["floor_y"]) * sc))
        cv_im = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        cv_im.alpha_composite(scaled, (ox, oy))
        arr = np.asarray(cv_im, dtype=np.uint8)
        cache[fi] = arr
        return arr

    idle_8 = [get_norm(fi) for fi in IDLE_8_FRAMES]
    run_16: list[list[np.ndarray]] = []
    for d in range(8):
        row = []
        for fi, mir in QG_RUN16_PLAN[d]:
            im = get_norm(fi)
            row.append(mirror_canvas_horiz(im) if mir else im)
        run_16.append(row)

    launch_24_idx = [int(round(k * 56 / 23.0)) for k in range(24)]
    action_24 = [get_norm(fi) for fi in launch_24_idx]

    accent_rgb = (245, 158, 11)
    sprint_24 = build_turbo_sprint_24(run_16[1], accent_rgb)
    jump_8x18 = build_jump_8x18(idle_8, run_16)
    flip_32 = build_frontflip_32(idle_8[1], run_16[1][12], accent_rgb)
    explosion_48 = build_mega_explosion_48(idle_8[0], action_24[18], "quakeguy")
    spr_56 = [Image.open(folder / "spr32" / f"f_{i:02d}.png").convert("RGBA") for i in range(56)]

    # Save standalone high-FPS sheets to quakeguy_sprite/
    save_contact_sheet([fr for row in run_16 for fr in row], 16, 150, 200, folder / "quakeguy_run16_sheet_8x16.png")
    save_contact_sheet([fr for row in jump_8x18 for fr in row], 18, 150, 200, folder / "quakeguy_jump_sheet_8x18.png")
    save_contact_sheet(explosion_48, 8, 210, 280, folder / "quakeguy_explosion_sheet_6x8.png")
    save_contact_sheet(flip_32, 8, 210, 280, folder / "quakeguy_flip_sheet_8x4.png")
    print(f"  QuakeGuy ready in {time.perf_counter() - t0:.1f}s")

    return pack_char_payload(
        key="quakeguy",
        name='QUAKEGUY — "Quake Shirt Ranger"',
        tagline="128f Live-Action 360° Run · 144f Jump · Flip · Gib Explosion",
        spr_file="progs/fr_quakeguy.spr32",
        action_label="🎬 Combat Launch (24f)",
        accent="#f59e0b",
        idle_8=idle_8,
        run_16=run_16,
        sprint_24=sprint_24,
        jump_8x18=jump_8x18,
        flip_32=flip_32,
        explosion_48=explosion_48,
        action_24=action_24,
        spr_56=spr_56,
    )


def build_paul_all(lm: dict) -> dict:
    t0 = time.perf_counter()
    print("=== [2/3] Generating High-FPS Multi-Animations for PAUL ===")
    folder = ROOT_DIR / "paul_sprite"

    p_front_key = key_magenta_studio(Image.open(PD_REF / "paul_studio_front.jpg"))
    p_turn_key = key_magenta_studio(Image.open(PD_REF / "paul_studio_turn.jpg"))
    p5_raw = [
        crop_normalize_view(p_front_key, (0, 0, p_front_key.shape[1], p_front_key.shape[0]), mirror=False),
        crop_normalize_view(p_turn_key, (15, 25, 310, 975), mirror=True),
        crop_normalize_view(p_turn_key, (315, 25, 508, 975), mirror=True),
        crop_normalize_view(p_turn_key, (508, 25, 715, 975), mirror=False),
        crop_normalize_view(p_turn_key, (718, 25, 1010, 975), mirror=False),
    ]

    def load_p_exp(fidx: int):
        info = lm["paul"][str(fidx)]
        im = np.asarray(Image.open(PD_REF / info["file"]).convert("RGB"))
        return im, tuple(info["eye_l"]), tuple(info["eye_r"]), tuple(info["mouth"])

    idle_8 = [np.asarray(Image.open(folder / f"paul_idle_d{d}.png").convert("RGBA")) for d in range(8)]

    # 16-frame 0° front screaming bases from real optical-flow-tracked video frames
    run0_16: list[np.ndarray] = []
    for f, vf in enumerate(lm["paul_run16_seq"]):
        vim, vel, ver, _ = load_p_exp(vf)
        base_f = graft_video_face(
            p5_raw[0], vim, vel, ver, (229.0, 89.5), (251.5, 89.5),
            oval_cy_offset=18.5, oval_rx=20.5, oval_ry_top=17.5, oval_ry_bot=31.0,
            chin_drop_shadow=True,
        )
        run0_16.append(render_front_or_back_run_frame(base_f, f, 16, is_back=False))

    v104, el104, er104, m104 = load_p_exp(104)
    p45_scream = graft_video_face(
        p5_raw[1], v104, el104, er104, (213.5, 83.5), (232.5, 83.5),
        oval_cy_offset=23.5, oval_rx=10.2, oval_ry_top=8.8, oval_ry_bot=14.8,
        oval_dx=+0.5, chin_drop_shadow=True,
        src_mouth=m104, dst_mouth=(222.5, 107.5),
    )
    p90_scream = open_paul_jaw_90_photoreal(p5_raw[2])

    # Reuse cached even poses (2*k -> paul_d{d}_f{k}.png) and synthesize odd poses (1,3,...,15) for 2x speed!
    def build_canon_16(d_idx: int, base_im: np.ndarray, yaw_deg: int | None, is_back: bool = False) -> list[np.ndarray]:
        seq: list[np.ndarray] = []
        for f in range(16):
            if f % 2 == 0:
                seq.append(np.asarray(Image.open(folder / f"paul_d{d_idx}_f{f // 2}.png").convert("RGBA")))
            else:
                if yaw_deg is None:
                    seq.append(render_front_or_back_run_frame(base_im, f, 16, is_back=is_back))
                else:
                    seq.append(render_side_or_diag_run_frame(base_im, yaw_deg, f, 16))
        return seq

    r1 = build_canon_16(1, p45_scream, 45)
    r2 = build_canon_16(2, p90_scream, 90)
    r3 = build_canon_16(3, p5_raw[3], 135)
    r4 = build_canon_16(4, p5_raw[4], None, is_back=True)

    run_16 = [
        run0_16,
        r1,
        r2,
        r3,
        r4,
        [mirror_canvas_horiz(r3[(f + 8) % 16]) for f in range(16)],
        [mirror_canvas_horiz(r2[(f + 8) % 16]) for f in range(16)],
        [mirror_canvas_horiz(r1[(f + 8) % 16]) for f in range(16)],
    ]

    # 24-frame escalating "Paul... Pauuul... PAAAAUUUUUL!" sonic scream sequence
    action_24: list[np.ndarray] = []
    for k, vf in enumerate(lm["paul_24_seq"]):
        inten = max(0.0, min(1.0, (k / 23.0) ** 1.15))
        vim, vel, ver, _ = load_p_exp(vf)
        posed = pose_paul_scream_body(p5_raw[0], vim, vel, ver, inten)
        action_24.append(overlay_sonic_scream_rings(posed, k, 24))

    accent_rgb = (251, 146, 60)
    sprint_24 = build_turbo_sprint_24(run_16[1], accent_rgb)
    jump_8x18 = build_jump_8x18(idle_8, run_16)
    flip_32 = build_frontflip_32(p45_scream, run_16[1][12], accent_rgb)
    panic_0 = pose_paul_scream_body(p5_raw[0], *load_p_exp(126)[:3], 1.0)
    explosion_48 = build_mega_explosion_48(idle_8[0], panic_0, "paul")
    spr_56 = [Image.open(folder / "spr32" / f"f_{i:02d}.png").convert("RGBA") for i in range(56)]

    save_contact_sheet([fr for row in run_16 for fr in row], 16, 150, 200, folder / "paul_run16_sheet_8x16.png")
    save_contact_sheet([fr for row in jump_8x18 for fr in row], 18, 150, 200, folder / "paul_jump_sheet_8x18.png")
    save_contact_sheet(explosion_48, 8, 210, 280, folder / "paul_explosion_sheet_6x8.png")
    save_contact_sheet(flip_32, 8, 210, 280, folder / "paul_flip_sheet_8x4.png")
    print(f"  Paul ready in {time.perf_counter() - t0:.1f}s")

    return pack_char_payload(
        key="paul",
        name='PAUL — "PAAAAUUUUUL!"',
        tagline="128f Scream-Run · 144f Jump · Sonic Scream · Gib Explosion",
        spr_file="progs/fr_paul.spr32",
        action_label='😱 "PAAAAUUUUUL!" Scream (24f)',
        accent="#fb923c",
        idle_8=idle_8,
        run_16=run_16,
        sprint_24=sprint_24,
        jump_8x18=jump_8x18,
        flip_32=flip_32,
        explosion_48=explosion_48,
        action_24=action_24,
        spr_56=spr_56,
    )


def build_dennis_all(lm: dict) -> dict:
    t0 = time.perf_counter()
    print("=== [3/3] Generating High-FPS Multi-Animations for DENNIS ===")
    folder = ROOT_DIR / "dennis_sprite"

    d_front_key = key_magenta_studio(Image.open(PD_REF / "dennis_studio_front.jpg"))
    d_turn_key = key_magenta_studio(Image.open(PD_REF / "dennis_studio_turn.jpg"))
    d5_raw = [
        crop_normalize_view(d_front_key, (0, 0, d_front_key.shape[1], d_front_key.shape[0]), mirror=False),
        crop_normalize_view(d_turn_key, (95, 25, 420, 1000), mirror=False),
        crop_normalize_view(d_turn_key, (565, 25, 700, 510), mirror=False),
        crop_normalize_view(d_turn_key, (555, 520, 735, 1015), mirror=False),
        crop_normalize_view(d_turn_key, (780, 520, 970, 1015), mirror=False),
    ]

    def load_d_exp(fidx: int):
        info = lm["dennis"][str(fidx)]
        im = np.asarray(Image.open(PD_REF / info["file"]).convert("RGB"))
        return im, tuple(info["eye_l"]), tuple(info["eye_r"])

    idle_8 = [np.asarray(Image.open(folder / f"dennis_idle_d{d}.png").convert("RGBA")) for d in range(8)]

    run0_16: list[np.ndarray] = []
    for f, vf in enumerate(lm["dennis_run16_seq"]):
        vim, vel, ver = load_d_exp(vf)
        base_f = graft_video_face(
            d5_raw[0], vim, vel, ver, (229.0, 82.5), (251.0, 81.5),
            oval_cy_offset=16.0, oval_rx=19.5, oval_ry_top=14.0, oval_ry_bot=24.5,
        )
        run0_16.append(render_front_or_back_run_frame(base_f, f, 16, is_back=False))

    def build_canon_16(d_idx: int, base_im: np.ndarray, yaw_deg: int | None, is_back: bool = False) -> list[np.ndarray]:
        seq: list[np.ndarray] = []
        for f in range(16):
            if f % 2 == 0:
                seq.append(np.asarray(Image.open(folder / f"dennis_d{d_idx}_f{f // 2}.png").convert("RGBA")))
            else:
                if yaw_deg is None:
                    seq.append(render_front_or_back_run_frame(base_im, f, 16, is_back=is_back))
                else:
                    seq.append(render_side_or_diag_run_frame(base_im, yaw_deg, f, 16))
        return seq

    r1 = build_canon_16(1, d5_raw[1], 45)
    r2 = build_canon_16(2, d5_raw[2], 90)
    r3 = build_canon_16(3, d5_raw[3], 135)
    r4 = build_canon_16(4, d5_raw[4], None, is_back=True)

    run_16 = [
        run0_16,
        r1,
        r2,
        r3,
        r4,
        [mirror_canvas_horiz(r3[(f + 8) % 16]) for f in range(16)],
        [mirror_canvas_horiz(r2[(f + 8) % 16]) for f in range(16)],
        [mirror_canvas_horiz(r1[(f + 8) % 16]) for f in range(16)],
    ]

    # Smooth 24-frame "Reading to you for 30 years" speaking & raised-hand gesture
    action_24: list[np.ndarray] = []
    for k, vf in enumerate(lm["dennis_24_seq"]):
        # Dennis raises his hand earnestly around video f=70..102 (k=14..21), then lowers smoothly
        if k < 10:
            rt = 0.0
        elif k <= 18:
            u = (k - 10) / 8.0
            rt = u * u * (3.0 - 2.0 * u)
        else:
            u = (23 - k) / 5.0
            rt = 0.25 + 0.75 * (u * u * (3.0 - 2.0 * u))
        vim, vel, ver = load_d_exp(vf)
        action_24.append(graft_dennis_lecture_gesture(d5_raw[0], vim, vel, ver, rt))

    accent_rgb = (56, 189, 248)
    sprint_24 = build_turbo_sprint_24(run_16[1], accent_rgb)
    jump_8x18 = build_jump_8x18(idle_8, run_16)
    flip_32 = build_frontflip_32(idle_8[1], run_16[1][12], accent_rgb)
    explosion_48 = build_mega_explosion_48(idle_8[0], action_24[18], "dennis")
    spr_56 = [Image.open(folder / "spr32" / f"f_{i:02d}.png").convert("RGBA") for i in range(56)]

    save_contact_sheet([fr for row in run_16 for fr in row], 16, 150, 200, folder / "dennis_run16_sheet_8x16.png")
    save_contact_sheet([fr for row in jump_8x18 for fr in row], 18, 150, 200, folder / "dennis_jump_sheet_8x18.png")
    save_contact_sheet(explosion_48, 8, 210, 280, folder / "dennis_explosion_sheet_6x8.png")
    save_contact_sheet(flip_32, 8, 210, 280, folder / "dennis_flip_sheet_8x4.png")
    print(f"  Dennis ready in {time.perf_counter() - t0:.1f}s")

    return pack_char_payload(
        key="dennis",
        name='DENNIS — "Reading For 30 Years"',
        tagline="128f Suit Run · 144f Jump · 30-Yr Lecture · Gib Explosion",
        spr_file="progs/fr_dennis.spr32",
        action_label='📖 "Reading 30 Years" (24f)',
        accent="#38bdf8",
        idle_8=idle_8,
        run_16=run_16,
        sprint_24=sprint_24,
        jump_8x18=jump_8x18,
        flip_32=flip_32,
        explosion_48=explosion_48,
        action_24=action_24,
        spr_56=spr_56,
    )


def pack_char_payload(
    key: str,
    name: str,
    tagline: str,
    spr_file: str,
    action_label: str,
    accent: str,
    idle_8: list[np.ndarray],
    run_16: list[list[np.ndarray]],
    sprint_24: list[np.ndarray],
    jump_8x18: list[list[np.ndarray]],
    flip_32: list[np.ndarray],
    explosion_48: list[np.ndarray],
    action_24: list[np.ndarray],
    spr_56: list[Image.Image],
) -> dict:
    print(f"  Encoding base64 WebP atlases for {key} ...")
    run_flat = [fr for row in run_16 for fr in row]
    jump_flat = [fr for row in jump_8x18 for fr in row]

    return {
        "key": key,
        "name": name,
        "tagline": tagline,
        "sprFile": spr_file,
        "actionLabel": action_label,
        "accent": accent,
        "gridW": GRID_W,
        "gridH": GRID_H,
        "seqW": SEQ_W,
        "seqH": SEQ_H,
        "sprW": SPR_W,
        "sprH": SPR_H,
        "groundFull": round(GROUND_Y / float(CANVAS_H), 5),
        "groundAct": round(ACT_GROUND_Y / float(CANVAS_H), 5),
        "idleAtlas": encode_atlas(idle_8, cols=8, cw=SEQ_W, ch=SEQ_H, quality=92),
        "runAtlas": encode_atlas(run_flat, cols=16, cw=GRID_W, ch=GRID_H, quality=88),
        "sprintAtlas": encode_atlas(sprint_24, cols=8, cw=SEQ_W, ch=SEQ_H, quality=90),
        "jumpAtlas": encode_atlas(jump_flat, cols=18, cw=GRID_W, ch=GRID_H, quality=88),
        "flipAtlas": encode_atlas(flip_32, cols=8, cw=SEQ_W, ch=SEQ_H, quality=90),
        "expAtlas": encode_atlas(explosion_48, cols=8, cw=SEQ_W, ch=SEQ_H, quality=90),
        "actAtlas": encode_atlas(action_24, cols=8, cw=SEQ_W, ch=SEQ_H, quality=91),
        "sprAtlas": encode_atlas(spr_56, cols=8, cw=SPR_W, ch=SPR_H, lossless=True),
    }


def build_html(chars_data: list[dict]) -> str:
    payload_json = json.dumps(chars_data, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BakersfieldQuake — 60 FPS Multi-Animation Character Sprite Inspector</title>
<style>
  :root {{
    --bg:#0b0e14; --panel:#151a24; --panel2:#1f2737; --border:#2d374e;
    --ink:#f1f5f9; --dim:#94a3b8; --accent:#f59e0b; --green:#4ade80; --blue:#38bdf8; --red:#f87171;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:12px;
    padding:14px 16px 48px; min-height:100vh;
  }}
  header {{ text-align:center; max-width:1240px; }}
  h1 {{ font-size:23px; margin:0 0 4px; font-weight:800; letter-spacing:-0.015em; }}
  .sub {{ color:var(--dim); font-size:13px; margin:0; }}
  .pill-ok {{
    display:inline-block; background:#133326; color:#86efac; border:1px solid #22c55e;
    font-size:11.5px; font-weight:700; border-radius:999px; padding:2px 10px; margin-left:6px;
    vertical-align:middle;
  }}
  .pill-fps {{
    display:inline-block; background:#3b1d16; color:#fdba74; border:1px solid #f97316;
    font-size:11.5px; font-weight:700; border-radius:999px; padding:2px 10px; margin-left:6px;
    vertical-align:middle;
  }}

  .char-bar, .mode-bar, .ctrl-bar {{
    display:flex; flex-wrap:wrap; gap:7px; align-items:center; justify-content:center;
    width:min(100%, 1240px); background:var(--panel); border:1px solid var(--border);
    border-radius:12px; padding:9px 12px;
  }}
  .cbtn {{
    flex:1 1 200px; padding:9px 12px; border-radius:9px; border:2px solid #313b52;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:800; font-size:14px;
    cursor:pointer; transition:all 0.12s ease; display:flex; flex-direction:column; gap:2px; align-items:center;
  }}
  .cbtn small {{ font-weight:600; font-size:11px; color:var(--dim); font-family:ui-monospace, Consolas, monospace; }}
  .cbtn:hover {{ border-color:#536388; }}
  .cbtn.on {{ background:#1e293b; border-color:var(--accent); box-shadow:0 0 18px rgba(245,158,11,0.22); }}

  .mbtn, .btn, .fps-pill {{
    padding:7px 12px; border-radius:8px; border:1.5px solid #333d54;
    background:var(--panel2); color:var(--ink); font:inherit; font-weight:700; font-size:12.5px;
    cursor:pointer; transition:border-color 0.1s ease, background 0.1s ease;
  }}
  .fps-pill {{ padding:5px 8px; font-size:11.5px; font-variant-numeric:tabular-nums; }}
  .mbtn:hover, .btn:hover, .fps-pill:hover {{ border-color:#5a6b92; }}
  .mbtn.on {{ background:#153628; border-color:var(--green); color:#bbf7d0; box-shadow:0 0 12px rgba(74,222,128,0.16); }}
  .mbtn[data-mode="explosion"].on {{ background:#3f1519; border-color:var(--red); color:#fecaca; box-shadow:0 0 14px rgba(248,113,113,0.28); }}
  .btn.on, .fps-pill.on {{ background:#13324a; border-color:var(--blue); color:#bae6fd; }}
  label {{ color:var(--dim); display:flex; gap:5px; align-items:center; font-size:12.5px; font-weight:600; }}
  input[type=range] {{ accent-color:var(--accent); cursor:pointer; }}

  #stages {{
    width:min(100%, 1240px); display:grid; gap:14px;
    grid-template-columns:1fr;
  }}
  #stages.trio {{ grid-template-columns:repeat(3, 1fr); }}
  @media (max-width:920px) {{ #stages.trio {{ grid-template-columns:1fr; }} }}

  .stage-card {{
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    padding:12px; display:flex; flex-direction:column; gap:8px;
  }}
  .stage-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px; flex-wrap:wrap; }}
  .stage-title {{ font-weight:800; font-size:16px; }}
  .stage-meta {{ font-size:11.5px; color:var(--dim); font-family:ui-monospace, Consolas, monospace; }}

  .viewport {{
    width:100%; height:495px; border-radius:11px; border:1px solid #333c52;
    position:relative; display:flex; align-items:center; justify-content:center;
    overflow:hidden; cursor:grab; user-select:none; touch-action:none;
  }}
  #stages.trio .viewport {{ height:415px; }}
  .viewport:active {{ cursor:grabbing; }}
  .viewport.checker {{ background:repeating-conic-gradient(#292e3a 0% 25%, #1d212a 0% 50%) 0 0/24px 24px; }}
  .viewport.quake   {{ background:radial-gradient(circle at 50% 68%, #423022 0%, #1e1510 70%, #0d0a08 100%); }}
  .viewport.white   {{ background:#f8fafc; }}
  .viewport.slate   {{ background:radial-gradient(circle at 50% 55%, #1e293b 0%, #0b1120 88%); }}
  .viewport.green   {{ background:#00b140; }}

  canvas.main-cv {{
    height:95%; aspect-ratio:3/4; max-width:96%;
    image-rendering:auto;
  }}
  canvas.main-cv.pixel {{ image-rendering:pixelated; }}

  .badge-ang {{
    position:absolute; top:10px; left:12px; background:rgba(11,14,21,0.86);
    border:1px solid #3c465e; border-radius:7px; padding:5px 10px;
    font-size:12.5px; font-weight:800; color:#f8fafc; pointer-events:none;
  }}
  .badge-fr {{
    position:absolute; top:10px; right:12px; background:rgba(11,14,21,0.84);
    border:1px solid #3c465e; border-radius:7px; padding:5px 10px;
    font-size:12px; color:#e2e8f0; font-variant-numeric:tabular-nums; pointer-events:none;
  }}
  .drag-tip {{
    position:absolute; bottom:9px; right:12px; background:rgba(11,14,21,0.80);
    border:1px solid #2e3648; border-radius:6px; padding:3px 9px;
    font-size:11.5px; color:#cbd5e1; pointer-events:none;
  }}

  .section-box {{
    width:min(100%, 1240px); background:var(--panel); border:1px solid var(--border);
    border-radius:14px; padding:14px; display:flex; flex-direction:column; gap:10px;
  }}
  .section-box h2 {{ margin:0; font-size:15px; font-weight:800; color:#e2e8f0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; }}
  .section-box h2 span {{ font-size:12px; font-weight:600; color:var(--dim); }}

  #dir-strip {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:7px;
  }}
  @media (max-width:720px) {{ #dir-strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  .dir-btn {{
    background:var(--panel2); border:2px solid transparent; border-radius:9px;
    padding:5px 4px 4px; cursor:pointer; display:flex; flex-direction:column; align-items:center; gap:3px;
    color:var(--dim); font-size:11.5px; font-weight:700;
  }}
  .dir-btn.on {{ border-color:var(--accent); color:var(--ink); background:#273044; }}
  .dir-btn canvas {{ width:100%; aspect-ratio:3/4; border-radius:5px; background:repeating-conic-gradient(#262a35 0% 25%, #1c1f28 0% 50%) 0 0/14px 14px; }}

  #sheet-grid {{
    display:grid; grid-template-columns:repeat(8, 1fr); gap:5px;
  }}
  #sheet-grid.cols-12 {{ grid-template-columns:repeat(12, 1fr); }}
  #sheet-grid.cols-16 {{ grid-template-columns:repeat(16, 1fr); gap:4px; }}
  #sheet-grid.cols-18 {{ grid-template-columns:repeat(18, 1fr); gap:3px; }}
  @media (max-width:960px) {{
    #sheet-grid.cols-16, #sheet-grid.cols-18, #sheet-grid.cols-12 {{ grid-template-columns:repeat(8, 1fr); }}
  }}
  .cell-btn {{
    background:repeating-conic-gradient(#262a35 0% 25%, #1c1f28 0% 50%) 0 0/14px 14px;
    border:1.5px solid #2d3548; border-radius:6px; padding:2px; cursor:pointer;
    position:relative; display:flex; flex-direction:column; align-items:center;
  }}
  .cell-btn.white-bg {{ background:#f8fafc; }}
  .cell-btn:hover {{ border-color:#64748b; }}
  .cell-btn.on {{ border-color:var(--green); box-shadow:0 0 0 1.5px var(--green); }}
  .cell-btn canvas {{ width:100%; aspect-ratio:3/4; display:block; }}
  .cell-lbl {{
    position:absolute; top:2px; left:3px; background:rgba(10,13,20,0.78);
    color:#cbd5e1; font-size:9.5px; font-weight:700; padding:1px 3px; border-radius:3px;
    pointer-events:none;
  }}
</style>
</head>
<body>
  <header>
    <h1>BakersfieldQuake — Character Sprite &amp; VFX Inspector <span class="pill-ok">100% Self-Contained</span> <span class="pill-fps">Up to 60 FPS · 1,452 Frames</span></h1>
    <p class="sub">Drag horizontally on any character to orbit 360° &bull; Switch between <b>128f Run</b>, <b>Turbo Sprint</b>, <b>144f 360° Jump</b>, <b>Frontflip</b> &amp; <b>48f Quake Gib Explosion</b> &bull; Keys: <code>1–8</code> Animations, <code>Arrows</code> Orbit/Step, <code>Space</code> Play/Pause</p>
  </header>

  <div class="char-bar" id="char-bar"></div>

  <div class="mode-bar">
    <button class="mbtn on" data-mode="run">🏃 360° Run (8×16 = 128f)</button>
    <button class="mbtn" data-mode="sprint">💨 Turbo Sprint (24f)</button>
    <button class="mbtn" data-mode="jump">🦘 360° Jump (8×18 = 144f)</button>
    <button class="mbtn" data-mode="flip">🤸 Frontflip Vault (32f)</button>
    <button class="mbtn" data-mode="explosion">💥 Gib Explosion (48f)</button>
    <button class="mbtn" data-mode="action" id="act-tab-btn">🎬 Signature Action (24f)</button>
    <button class="mbtn" data-mode="idle">🧍 360° Idle (8f)</button>
    <button class="mbtn" data-mode="spr32">🕹️ Quake .SPR32 (56f)</button>
  </div>

  <div class="ctrl-bar">
    <button class="btn on" id="play-btn">⏸ Pause</button>
    <button class="btn on" id="spin-btn">🔄 Auto-Spin 360°: ON</button>
    <label>FPS <input id="fps-rng" type="range" min="8" max="60" value="36" style="width:92px"> <span id="fps-val" style="min-width:24px;color:var(--ink)">36</span></label>
    <button class="fps-pill" data-fps="24">24</button>
    <button class="fps-pill on" data-fps="36">36</button>
    <button class="fps-pill" data-fps="48">48</button>
    <button class="fps-pill" data-fps="60">60 FPS</button>
    <button class="btn" id="blend-btn" title="Sub-frame alpha interpolation at 60Hz">✨ 60Hz Blend: OFF</button>
    <label>Angle <input id="ang-rng" type="range" min="0" max="7" value="0" style="width:88px"> <span id="ang-val" style="min-width:32px;color:var(--ink)">0°</span></label>
    <label>Frame <input id="frm-rng" type="range" min="0" max="15" value="0" style="width:95px"> <span id="frm-val" style="min-width:40px;color:var(--ink)">0/15</span></label>
    <label>Zoom <input id="zm-rng" type="range" min="75" max="175" value="100" style="width:72px"></label>
    <button class="btn" id="orig-btn">🎯 Origin</button>
    <button class="btn" id="bg-btn">🎨 BG: Checker</button>
  </div>

  <div id="stages"></div>

  <div class="section-box">
    <h2>
      <span id="strip-title" style="font-size:15px;color:var(--ink)">360° Turnaround Strip (Click an Angle to Lock Camera)</span>
      <span>Shortcuts: <b>1–8</b> Switch Animation &bull; <b>Left/Right</b> Orbit 360° &bull; <b>Up/Down</b> Step Frame &bull; <b>R</b> Replay Explosion</span>
    </h2>
    <div id="dir-strip"></div>
  </div>

  <div class="section-box">
    <h2>
      <span id="grid-title" style="font-size:15px;color:var(--ink)">Full Frame Sheet Inspector (Click Any Frame to Pause &amp; Inspect)</span>
      <span id="grid-sub">128 transparent RGBA frames</span>
    </h2>
    <div id="sheet-grid"></div>
  </div>

<script>
const CHARS = {payload_json};
const DIR_LABELS = [
  "0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left",
  "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"
];
const MODES_ORDER = ["run", "sprint", "jump", "flip", "explosion", "action", "idle", "spr32"];
const BGS = ["checker", "quake", "white", "slate", "green"];
const BG_NAMES = ["Checker", "Quake Dungeon", "Pure White", "Dark Slate", "Green Screen"];

let selChar = 0; // 0=QuakeGuy, 1=Paul, 2=Dennis, 3=All 3 Trio
let mode = "run";
let curDir = 0, curFrame = 0;
let frameFloat = 0.0, spinAccum = 0.0;
let playing = true, autoSpin = true, smoothBlend = false, showOrigin = false, zoomPct = 100, bgIdx = 0;
let prevRafT = performance.now();

const decoded = CHARS.map(c => {{
  const load = src => {{ const im = new Image(); im.src = src; return im; }};
  return {{
    idle:   load(c.idleAtlas),
    run:    load(c.runAtlas),
    sprint: load(c.sprintAtlas),
    jump:   load(c.jumpAtlas),
    flip:   load(c.flipAtlas),
    exp:    load(c.expAtlas),
    act:    load(c.actAtlas),
    spr:    load(c.sprAtlas),
  }};
}});

const charBar   = document.getElementById("char-bar");
const stagesEl  = document.getElementById("stages");
const dirStrip  = document.getElementById("dir-strip");
const sheetGrid = document.getElementById("sheet-grid");
const actTabBtn = document.getElementById("act-tab-btn");
const playBtn   = document.getElementById("play-btn");
const spinBtn   = document.getElementById("spin-btn");
const blendBtn  = document.getElementById("blend-btn");
const origBtn   = document.getElementById("orig-btn");
const bgBtn     = document.getElementById("bg-btn");
const angRng    = document.getElementById("ang-rng"), angVal = document.getElementById("ang-val");
const frmRng    = document.getElementById("frm-rng"), frmVal = document.getElementById("frm-val");
const fpsRng    = document.getElementById("fps-rng"), fpsVal = document.getElementById("fps-val");
const zmRng     = document.getElementById("zm-rng");

// Character buttons + Trio button
const charBtns = [];
CHARS.forEach((c, idx) => {{
  const b = document.createElement("button");
  b.className = "cbtn" + (idx === 0 ? " on" : "");
  b.innerHTML = `<span style="color:${{c.accent}}">${{c.name}}</span><small>${{c.tagline}}</small>`;
  b.onclick = () => selectCharacter(idx);
  charBar.appendChild(b);
  charBtns.push(b);
}});
const trioBtn = document.createElement("button");
trioBtn.className = "cbtn";
trioBtn.innerHTML = `<span style="color:#a78bfa">👥 ALL 3 SIDE-BY-SIDE</span><small>Synchronized 60 FPS Trio</small>`;
trioBtn.onclick = () => selectCharacter(3);
charBar.appendChild(trioBtn);
charBtns.push(trioBtn);

function isOrbitableMode(m) {{
  return m === "run" || m === "jump" || m === "idle" || m === "spr32";
}}

function frameCount(m = mode) {{
  if (m === "run") return 16;
  if (m === "sprint") return 24;
  if (m === "jump") return 18;
  if (m === "flip") return 32;
  if (m === "explosion") return 48;
  if (m === "action") return 24;
  if (m === "spr32") return 6;
  return 1; // idle
}}

function modeGroundFrac(c, m) {{
  return (m === "jump" || m === "flip" || m === "sprint" || m === "explosion") ? c.groundAct : c.groundFull;
}}

function getAtlasSlice(c, imgs, m, dir, frm) {{
  const d = ((dir % 8) + 8) % 8;
  const nf = frameCount(m);
  const f = ((frm % nf) + nf) % nf;
  if (m === "run") {{
    return {{ atlas: imgs.run, sx: f * c.gridW, sy: d * c.gridH, sw: c.gridW, sh: c.gridH }};
  }} else if (m === "jump") {{
    return {{ atlas: imgs.jump, sx: f * c.gridW, sy: d * c.gridH, sw: c.gridW, sh: c.gridH }};
  }} else if (m === "sprint") {{
    return {{ atlas: imgs.sprint, sx: (f % 8) * c.seqW, sy: Math.floor(f / 8) * c.seqH, sw: c.seqW, sh: c.seqH }};
  }} else if (m === "flip") {{
    return {{ atlas: imgs.flip, sx: (f % 8) * c.seqW, sy: Math.floor(f / 8) * c.seqH, sw: c.seqW, sh: c.seqH }};
  }} else if (m === "explosion") {{
    return {{ atlas: imgs.exp, sx: (f % 8) * c.seqW, sy: Math.floor(f / 8) * c.seqH, sw: c.seqW, sh: c.seqH }};
  }} else if (m === "action") {{
    return {{ atlas: imgs.act, sx: (f % 8) * c.seqW, sy: Math.floor(f / 8) * c.seqH, sw: c.seqW, sh: c.seqH }};
  }} else if (m === "spr32") {{
    const sIdx = 8 + d * 6 + f;
    return {{ atlas: imgs.spr, sx: (sIdx % 8) * c.sprW, sy: Math.floor(sIdx / 8) * c.sprH, sw: c.sprW, sh: c.sprH }};
  }} else {{
    return {{ atlas: imgs.idle, sx: d * c.seqW, sy: 0, sw: c.seqW, sh: c.seqH }};
  }}
}}

function drawSpriteFrame(ctx, cw, ch, cIdx, m, dir, frm, withOrigin, zPct, blendFrac = 0.0) {{
  ctx.clearRect(0, 0, cw, ch);
  const c = CHARS[cIdx], imgs = decoded[cIdx];
  const sl = getAtlasSlice(c, imgs, m, dir, frm);
  if (!sl.atlas.complete || !sl.atlas.naturalWidth) return;

  ctx.imageSmoothingEnabled = (m !== "spr32");
  ctx.imageSmoothingQuality = "high";

  const gFrac = modeGroundFrac(c, m);
  const scale = zPct / 100.0;
  const dw = cw * scale, dh = ch * scale;
  const dx = (cw - dw) * 0.5;
  const footY = ch * gFrac;
  const dy = footY - dh * gFrac;

  ctx.globalAlpha = 1.0;
  ctx.drawImage(sl.atlas, sl.sx, sl.sy, sl.sw, sl.sh, dx, dy, dw, dh);

  if (blendFrac > 0.02 && m !== "spr32" && m !== "idle") {{
    const nf = frameCount(m);
    const nextF = (m === "explosion") ? Math.min(nf - 1, frm + 1) : ((frm + 1) % nf);
    if (nextF !== frm) {{
      const sl2 = getAtlasSlice(c, imgs, m, dir, nextF);
      ctx.globalAlpha = blendFrac;
      ctx.drawImage(sl2.atlas, sl2.sx, sl2.sy, sl2.sw, sl2.sh, dx, dy, dw, dh);
      ctx.globalAlpha = 1.0;
    }}
  }}

  if (withOrigin) {{
    ctx.save();
    ctx.strokeStyle = "rgba(251, 191, 36, 0.9)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(cw * 0.06, footY); ctx.lineTo(cw * 0.94, footY); ctx.stroke();
    ctx.strokeStyle = "rgba(56, 189, 248, 0.75)";
    ctx.beginPath(); ctx.moveTo(cw * 0.5, ch * 0.04); ctx.lineTo(cw * 0.5, ch * 0.98); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#fbbf24";
    ctx.beginPath(); ctx.arc(cw * 0.5, footY, 5, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#0f172a"; ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
  }}
}}

let stageViews = [];
function rebuildStages() {{
  stagesEl.innerHTML = "";
  stagesEl.classList.toggle("trio", selChar === 3);
  stageViews = [];
  const indices = selChar === 3 ? [0, 1, 2] : [selChar];
  indices.forEach(cIdx => {{
    const c = CHARS[cIdx];
    const card = document.createElement("div");
    card.className = "stage-card";
    card.innerHTML = `
      <div class="stage-head">
        <span class="stage-title" style="color:${{c.accent}}">${{c.name}}</span>
        <span class="stage-meta">${{c.sprFile}}</span>
      </div>
      <div class="viewport ${{BGS[bgIdx]}}">
        <div class="badge-ang">0° Front</div>
        <div class="badge-fr">Frame 0/15</div>
        <canvas class="main-cv" width="480" height="640"></canvas>
        <div class="drag-tip">↔ Drag horizontally to orbit 360°</div>
      </div>
    `;
    const vp = card.querySelector(".viewport");
    const cv = card.querySelector("canvas");
    const bAng = card.querySelector(".badge-ang");
    const bFr  = card.querySelector(".badge-fr");
    const dTip = card.querySelector(".drag-tip");

    let dragX = null, startD = 0, startF = 0;
    vp.addEventListener("pointerdown", e => {{
      dragX = e.clientX; startD = curDir; startF = curFrame;
      autoSpin = false;
      if (!isOrbitableMode(mode)) playing = false;
      syncControls();
      vp.setPointerCapture(e.pointerId);
    }});
    vp.addEventListener("pointermove", e => {{
      if (dragX === null) return;
      if (isOrbitableMode(mode)) {{
        const steps = Math.round((e.clientX - dragX) / 32);
        curDir = (((startD - steps) % 8) + 8) % 8;
      }} else {{
        const nf = frameCount(mode);
        const steps = Math.round((e.clientX - dragX) / 14);
        curFrame = (((startF + steps) % nf) + nf) % nf;
        frameFloat = curFrame;
      }}
      renderAll();
    }});
    const endDrag = () => {{ dragX = null; }};
    vp.addEventListener("pointerup", endDrag);
    vp.addEventListener("pointercancel", endDrag);

    stagesEl.appendChild(card);
    stageViews.push({{ cIdx, vp, cv, ctx: cv.getContext("2d"), bAng, bFr, dTip }});
  }});
}}

// 8-Direction quick strip
const dirThumbCvs = [];
for (let d = 0; d < 8; d++) {{
  const b = document.createElement("button");
  b.className = "dir-btn";
  const cv = document.createElement("canvas");
  cv.width = 144; cv.height = 192;
  const sp = document.createElement("span");
  sp.textContent = (d * 45) + "°";
  b.appendChild(cv); b.appendChild(sp);
  b.onclick = () => {{
    autoSpin = false; curDir = d;
    if (!isOrbitableMode(mode)) {{ mode = "run"; curFrame = 0; frameFloat = 0; syncModeTabs(); rebuildSheetGrid(); }}
    syncControls(); renderAll();
  }};
  dirStrip.appendChild(b);
  dirThumbCvs.push({{ btn: b, cv, ctx: cv.getContext("2d") }});
}}

// Dynamic full-sheet inspector grid
let sheetCells = [];
function rebuildSheetGrid() {{
  sheetGrid.innerHTML = "";
  sheetGrid.className = "";
  sheetCells = [];
  const activeIdx = selChar === 3 ? 0 : selChar;
  const c = CHARS[activeIdx];
  const gridTitle = document.getElementById("grid-title");
  const gridSub = document.getElementById("grid-sub");

  let items = [];
  if (mode === "run") {{
    sheetGrid.classList.add("cols-16");
    gridTitle.textContent = `${{c.name}} — Full 8×16 (128-Frame) High-FPS 360° Run Sheet`;
    gridSub.textContent = `8 angles × 16 frames = 128 RGBA frames (click any cell to inspect)`;
    for (let d = 0; d < 8; d++) {{
      for (let f = 0; f < 16; f++) items.push({{ d, f, lbl: `${{d*45}}°·${{f}}` }});
    }}
  }} else if (mode === "jump") {{
    sheetGrid.classList.add("cols-18");
    gridTitle.textContent = `${{c.name}} — Full 8×18 (144-Frame) 360° Combat Jump Sheet`;
    gridSub.textContent = `Crouch coil → Launch dust → High knee tuck → Landing squash across all 8 angles`;
    for (let d = 0; d < 8; d++) {{
      for (let f = 0; f < 18; f++) items.push({{ d, f, lbl: `${{d*45}}°·${{f}}` }});
    }}
  }} else if (mode === "sprint") {{
    sheetGrid.classList.add("cols-12");
    gridTitle.textContent = `${{c.name}} — 24-Frame Turbo Sprint & Speed Afterimages`;
    gridSub.textContent = `Forward sprint lean + glowing energy ghosts + supersonic wind streaks`;
    for (let f = 0; f < 24; f++) items.push({{ d: 1, f, lbl: `#${{f}}` }});
  }} else if (mode === "flip") {{
    gridTitle.textContent = `${{c.name}} — 32-Frame Acrobatic 360° Frontflip Vault`;
    gridSub.textContent = `Deep coil → 360° tucked mid-air somersault → Superhero HDR shockwave landing`;
    for (let f = 0; f < 32; f++) items.push({{ d: 1, f, lbl: `#${{f}}` }});
  }} else if (mode === "explosion") {{
    sheetGrid.classList.add("cols-12");
    gridTitle.textContent = `${{c.name}} — 48-Frame 5-Act Mega Quake Gib Explosion`;
    gridSub.textContent = `Core bloat & lightning → HDR starburst & VFX fireball → Flying head, limbs, props & 18 Quake gibs`;
    for (let f = 0; f < 48; f++) items.push({{ d: 0, f, lbl: `#${{f}}` }});
  }} else if (mode === "action") {{
    sheetGrid.classList.add("cols-12");
    gridTitle.textContent = `${{c.name}} — ${{c.actionLabel}}`;
    gridSub.textContent = `24 optical-flow-tracked live expression & gesture frames`;
    for (let f = 0; f < 24; f++) items.push({{ d: 0, f, lbl: `#${{f}}` }});
  }} else if (mode === "idle") {{
    gridTitle.textContent = `${{c.name}} — 8-Direction Standing Idle Sheet`;
    gridSub.textContent = `progs/${{c.sprFile.split("/").pop()}} frames 0..7`;
    for (let d = 0; d < 8; d++) items.push({{ d, f: 0, lbl: `${{d*45}}°` }});
  }} else {{
    gridTitle.textContent = `${{c.name}} — Complete 56-Frame In-Game .SPR32 Atlas (${{c.sprW}}×${{c.sprH}})`;
    gridSub.textContent = `Frames 0..7 Idle + Frames 8..55 Run (8 angles × 6 frames)`;
    for (let d = 0; d < 8; d++) items.push({{ sprIdle: true, sIdx: d, d, f: 0, lbl: `Idle ${{d*45}}°` }});
    for (let d = 0; d < 8; d++) {{
      for (let f = 0; f < 6; f++) items.push({{ d, f, sIdx: 8 + d*6 + f, lbl: `#${{8+d*6+f}}` }});
    }}
  }}

  const thumbW = items.length > 80 ? 84 : 126;
  const thumbH = items.length > 80 ? 112 : 168;
  items.forEach(it => {{
    const b = document.createElement("button");
    b.className = "cell-btn" + (BGS[bgIdx] === "white" ? " white-bg" : "");
    const cv = document.createElement("canvas");
    cv.width = thumbW; cv.height = thumbH;
    const lb = document.createElement("span");
    lb.className = "cell-lbl";
    lb.textContent = it.lbl;
    b.appendChild(cv); b.appendChild(lb);
    b.onclick = () => {{
      playing = false; autoSpin = false;
      if (it.sprIdle) {{ mode = "idle"; syncModeTabs(); rebuildSheetGrid(); }}
      curDir = it.d; curFrame = it.f; frameFloat = it.f;
      syncControls(); renderAll();
    }};
    sheetGrid.appendChild(b);
    sheetCells.push({{ btn: b, cv, ctx: cv.getContext("2d"), it }});
  }});
  drawSheetCells();
}}

function drawSheetCells() {{
  const activeIdx = selChar === 3 ? 0 : selChar;
  const c = CHARS[activeIdx], imgs = decoded[activeIdx];
  sheetCells.forEach(cell => {{
    cell.btn.classList.toggle("white-bg", BGS[bgIdx] === "white");
    const {{ ctx, cv, it }} = cell;
    if (it.sprIdle) {{
      ctx.clearRect(0, 0, cv.width, cv.height);
      if (imgs.spr.complete && imgs.spr.naturalWidth) {{
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(imgs.spr, it.sIdx * c.sprW, 0, c.sprW, c.sprH, 0, 0, cv.width, cv.height);
      }}
    }} else {{
      drawSpriteFrame(ctx, cv.width, cv.height, activeIdx, mode, it.d, it.f, false, 100, 0.0);
    }}
  }});
}}

const MODE_BADGES = {{
  run: "360° Run",
  sprint: "💨 Turbo Sprint",
  jump: "🦘 360° Jump",
  flip: "🤸 Frontflip Vault",
  explosion: "💥 Gib Explosion",
  idle: "Idle",
  spr32: ".SPR32",
}};

function renderAll(blendFrac = 0.0) {{
  const nf = frameCount(mode);
  curDir = ((curDir % 8) + 8) % 8;
  curFrame = ((curFrame % nf) + nf) % nf;
  angRng.value = curDir; angVal.textContent = (curDir * 45) + "°";
  frmRng.max = Math.max(0, nf - 1); frmRng.value = curFrame; frmVal.textContent = `${{curFrame}}/${{nf - 1}}`;

  const activeIdx = selChar === 3 ? 0 : selChar;
  document.documentElement.style.setProperty("--accent", CHARS[activeIdx].accent);
  actTabBtn.textContent = CHARS[activeIdx].actionLabel;

  const orbitOk = isOrbitableMode(mode);
  stageViews.forEach(sv => {{
    sv.vp.className = "viewport " + BGS[bgIdx];
    sv.cv.classList.toggle("pixel", mode === "spr32");
    drawSpriteFrame(sv.ctx, sv.cv.width, sv.cv.height, sv.cIdx, mode, curDir, curFrame, showOrigin, zoomPct, blendFrac);

    if (mode === "action") {{
      sv.bAng.textContent = CHARS[sv.cIdx].actionLabel;
    }} else if (orbitOk) {{
      sv.bAng.textContent = `${{DIR_LABELS[curDir]}} · ${{MODE_BADGES[mode]}}`;
    }} else {{
      sv.bAng.textContent = MODE_BADGES[mode];
    }}
    sv.bFr.textContent = `${{fpsRng.value}} FPS · Frame ${{curFrame}}/${{nf - 1}}`;
    sv.dTip.textContent = orbitOk ? "↔ Drag horizontally to orbit 360°" : "↔ Drag horizontally to scrub frames";
  }});

  const stripThumbMode = orbitOk ? mode : "run";
  const stripFrm = curFrame % frameCount(stripThumbMode);
  dirThumbCvs.forEach((dt, d) => {{
    dt.btn.classList.toggle("on", orbitOk && d === curDir);
    drawSpriteFrame(dt.ctx, dt.cv.width, dt.cv.height, activeIdx, stripThumbMode, d, stripFrm, false, 100, 0.0);
  }});

  sheetCells.forEach(cell => {{
    const matchDir = orbitOk ? (cell.it.d === curDir) : true;
    const on = !cell.it.sprIdle && matchDir && cell.it.f === curFrame;
    cell.btn.classList.toggle("on", on);
  }});
}}

function syncControls() {{
  playBtn.textContent = playing ? "⏸ Pause" : "▶ Play";
  playBtn.classList.toggle("on", playing);
  spinBtn.textContent = "🔄 Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  spinBtn.classList.toggle("on", autoSpin);
  blendBtn.textContent = "✨ 60Hz Blend: " + (smoothBlend ? "ON" : "OFF");
  blendBtn.classList.toggle("on", smoothBlend);
  origBtn.textContent = showOrigin ? "🎯 Origin: ON" : "🎯 Origin";
  origBtn.classList.toggle("on", showOrigin);
  bgBtn.textContent = "🎨 BG: " + BG_NAMES[bgIdx];
  fpsVal.textContent = fpsRng.value;
  document.querySelectorAll(".fps-pill").forEach(p => p.classList.toggle("on", +p.dataset.fps === +fpsRng.value));
}}

function syncModeTabs() {{
  document.querySelectorAll(".mbtn").forEach(b => b.classList.toggle("on", b.dataset.mode === mode));
}}

function setMode(newMode) {{
  mode = newMode;
  curFrame = 0;
  frameFloat = 0.0;
  spinAccum = 0.0;
  playing = true;
  syncModeTabs();
  syncControls();
  rebuildSheetGrid();
  renderAll();
}}

function selectCharacter(idx) {{
  selChar = idx;
  charBtns.forEach((b, k) => b.classList.toggle("on", k === idx));
  rebuildStages();
  rebuildSheetGrid();
  renderAll();
}}

document.querySelectorAll(".mbtn").forEach(b => {{
  b.onclick = () => setMode(b.dataset.mode);
}});

document.querySelectorAll(".fps-pill").forEach(p => {{
  p.onclick = () => {{
    fpsRng.value = p.dataset.fps;
    syncControls();
    renderAll();
  }};
}});

playBtn.onclick  = () => {{ playing = !playing; syncControls(); }};
spinBtn.onclick  = () => {{ autoSpin = !autoSpin; syncControls(); }};
blendBtn.onclick = () => {{ smoothBlend = !smoothBlend; syncControls(); renderAll(); }};
origBtn.onclick  = () => {{ showOrigin = !showOrigin; syncControls(); renderAll(); }};
bgBtn.onclick    = () => {{ bgIdx = (bgIdx + 1) % BGS.length; syncControls(); drawSheetCells(); renderAll(); }};
angRng.oninput   = () => {{ autoSpin = false; curDir = +angRng.value; syncControls(); renderAll(); }};
frmRng.oninput   = () => {{ playing = false; curFrame = +frmRng.value; frameFloat = curFrame; syncControls(); renderAll(); }};
fpsRng.oninput   = () => {{ syncControls(); renderAll(); }};
zmRng.oninput    = () => {{ zoomPct = +zmRng.value; renderAll(); }};

addEventListener("keydown", e => {{
  if (e.code === "Space") {{ e.preventDefault(); playing = !playing; syncControls(); }}
  else if (e.code === "KeyR") {{ e.preventDefault(); curFrame = 0; frameFloat = 0; playing = true; syncControls(); renderAll(); }}
  else if (e.key >= "1" && e.key <= "8") {{ setMode(MODES_ORDER[+e.key - 1]); }}
  else if (e.code === "ArrowRight") {{ e.preventDefault(); autoSpin = false; curDir++; syncControls(); renderAll(); }}
  else if (e.code === "ArrowLeft")  {{ e.preventDefault(); autoSpin = false; curDir--; syncControls(); renderAll(); }}
  else if (e.code === "ArrowUp")    {{ e.preventDefault(); playing = false; curFrame++; frameFloat = curFrame; syncControls(); renderAll(); }}
  else if (e.code === "ArrowDown")  {{ e.preventDefault(); playing = false; curFrame--; frameFloat = curFrame; syncControls(); renderAll(); }}
}});

decoded.forEach(group => Object.values(group).forEach(im => {{
  im.onload = () => {{ drawSheetCells(); renderAll(); }};
}}));

// True 60Hz fractional-accumulator loop (supports genuine 36 / 48 / 60 FPS without rAF aliasing!)
function tick(t) {{
  const dt = Math.min(0.08, Math.max(0.0, (t - prevRafT) / 1000.0));
  prevRafT = t;
  const fps = +fpsRng.value;
  const nf = frameCount(mode);
  let dirty = false;
  let blendFrac = 0.0;

  if (playing && nf > 1) {{
    // Hold final smoking aftermath of Explosion for 14 virtual ticks before re-detonating
    const cycleSpan = (mode === "explosion") ? (nf + 14) : nf;
    frameFloat = (frameFloat + dt * fps) % cycleSpan;
    const nextInt = Math.min(nf - 1, Math.floor(frameFloat));
    blendFrac = (smoothBlend && frameFloat < nf - 1) ? (frameFloat - nextInt) : 0.0;
    if (nextInt !== curFrame || blendFrac > 0.0) {{
      curFrame = nextInt;
      dirty = true;
    }}
  }}

  if (autoSpin && isOrbitableMode(mode)) {{
    // Orbit smoothly every ~0.55s (or once per full jump arc in Jump mode)
    const spinRate = (mode === "jump") ? (fps / 18.0) : 1.75;
    spinAccum += dt * spinRate;
    if (spinAccum >= 1.0) {{
      const steps = Math.floor(spinAccum);
      spinAccum -= steps;
      curDir = (curDir + steps) % 8;
      dirty = true;
    }}
  }}

  if (dirty) renderAll(blendFrac);
  requestAnimationFrame(tick);
}}

rebuildStages();
rebuildSheetGrid();
syncControls();
renderAll();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def main() -> None:
    t_start = time.perf_counter()
    lm = json.loads((PD_REF / "expression_landmarks.json").read_text(encoding="utf-8"))

    chars = [
        build_quakeguy_all(),
        build_paul_all(lm),
        build_dennis_all(lm),
    ]

    out_html = ROOT_DIR / "character_sprites_inspector.html"
    html_str = build_html(chars)
    out_html.write_text(html_str, encoding="utf-8")
    print(f"\n=== Wrote High-FPS Multi-Animation HTML: {out_html} ({len(html_str) / 1e6:.2f} MB, total {time.perf_counter() - t_start:.1f}s) ===")


if __name__ == "__main__":
    main()
