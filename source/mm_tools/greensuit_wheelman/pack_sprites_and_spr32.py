r"""Packs the 1,200 rendered 3D RGBA frames of Green-Suit Wheelman into:
  1. WebGL/Canvas-safe (<4096x4096) RGBA WebP Atlases (280x280/cell) in greensuit_wheelman_sprite/atlases/
  2. Tight-cropped DarkPlaces IDSP v32 Sprite: progs/greensuit_wheelman.spr32 (256 directional frames)
  3. Master 8-Angle 360° Turnaround Sheet, 12-Animation Poster, & Animated Showcase GIFs!
"""
from __future__ import annotations

import json
import math
import os
import struct
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RAW_DIR = os.path.join(HERE, "renders_raw")
REF_DIR = os.path.join(HERE, "ref")
OUT_SPR_DIR = os.path.join(MOD_DIR, "greensuit_wheelman_sprite")
ATLAS_DIR = os.path.join(OUT_SPR_DIR, "atlases")
PROGS_DIR = os.path.join(MOD_DIR, "progs")
SPR32_OUT = os.path.join(PROGS_DIR, "greensuit_wheelman.spr32")

os.makedirs(ATLAS_DIR, exist_ok=True)
os.makedirs(PROGS_DIR, exist_ok=True)

CELL_W, CELL_H = 280, 280  # 14 cols * 280 = 3920 <= 4096; 8 rows * 280 = 2240 <= 4096!


def resize_rgba_premul(arr: np.ndarray, tw: int, th: int) -> np.ndarray:
    """Premultiplied-alpha Lanczos resize for zero dark edge halos."""
    if arr.shape[1] == tw and arr.shape[0] == th:
        return arr
    f = arr.astype(np.float32)
    a = f[..., 3:4] / 255.0
    rgb_p = f[..., :3] * a
    pre = np.concatenate([rgb_p, f[..., 3:4]], axis=-1)
    res = cv2.resize(pre, (tw, th), interpolation=cv2.INTER_AREA if tw < arr.shape[1] else cv2.INTER_LANCZOS4)
    a_out = np.clip(res[..., 3:4], 0.0, 255.0)
    denom = np.maximum(a_out / 255.0, 1e-4)
    rgb_out = np.where(a_out > 0.5, np.clip(res[..., :3] / denom, 0.0, 255.0), 0.0)
    return np.concatenate([rgb_out, a_out], axis=-1).round().astype(np.uint8)


def load_frame(anim_id: str, d: int, f: int) -> np.ndarray:
    p = os.path.join(RAW_DIR, anim_id, f"d{d}_f{f:02d}.png")
    return np.asarray(Image.open(p).convert("RGBA"), dtype=np.uint8)


def build_atlases(specs: List[Dict]) -> Dict[str, dict]:
    meta_out: Dict[str, dict] = {}
    for sp in specs:
        aid = sp["id"]
        nf = int(sp["frames"])
        atlas = Image.new("RGBA", (nf * CELL_W, 8 * CELL_H), (0, 0, 0, 0))
        for d in range(8):
            for f in range(nf):
                rgba = resize_rgba_premul(load_frame(aid, d, f), CELL_W, CELL_H)
                atlas.paste(Image.fromarray(rgba, "RGBA"), (f * CELL_W, d * CELL_H))
        out_webp = os.path.join(ATLAS_DIR, f"{aid}.webp")
        atlas.save(out_webp, format="WEBP", quality=90, alpha_quality=94, method=4)
        sz_kb = os.path.getsize(out_webp) / 1024.0
        print(f"  Atlas {aid:18s}: {nf*CELL_W}x{8*CELL_H} -> {sz_kb:6.1f} KB")
        meta_out[aid] = {
            "id": aid,
            "title": sp["title"],
            "frames": nf,
            "dirs": 8,
            "fps": sp["fps"],
            "cellW": CELL_W,
            "cellH": CELL_H,
        }
    return meta_out


def tone_for_darkplaces(im_rgba: Image.Image) -> Image.Image:
    """Calibrates HDR scene brightness (contrast 1.15, brightness 0.58) matching BakersfieldQuake .spr32 convention."""
    r, g, b, a = im_rgba.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.58)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def build_spr32() -> Tuple[int, int]:
    """Builds progs/greensuit_wheelman.spr32 (IDSP v32, tight-cropped per frame with ground-anchored origin)."""
    spr_w, spr_h = 224, 224
    ground_y = 196  # Ground contact row in 224x224 canvas
    base_ox = -(spr_w // 2)
    base_oy = ground_y

    plan = [
        ("seated_cruise",    [0]),                    # 0..7:    8-dir Idle
        ("seated_cruise",    [0, 2, 4, 6, 8, 10]),    # 8..55:   8-dir Seated Cruise (6f)
        ("scream_turbo",     [0, 2, 4, 6, 8, 10]),    # 56..103: 8-dir Scream Turbo (6f)
        ("hero_crane_point", [0, 2, 4, 6, 8, 10]),    # 104..151:8-dir Hero Crane Point (6f)
        ("plank_rollout",    [0, 2, 4, 6, 8, 10]),    # 152..199:8-dir Plank Rollout (6f)
        ("gib_explosion",    [0, 2, 4, 6, 8, 10, 12]),# 200..255:8-dir Gib Explosion (7f)
    ]

    packed_frames = []
    max_cw, max_ch = 1, 1

    for aid, f_indices in plan:
        for d in range(8):
            for fi in f_indices:
                rgba = resize_rgba_premul(load_frame(aid, d, fi), spr_w, spr_h)
                im = tone_for_darkplaces(Image.fromarray(rgba, "RGBA"))
                bbox = im.getchannel("A").getbbox()
                if bbox is None:
                    x0, y0, x1, y1 = 0, 0, 1, 1
                else:
                    x0 = max(0, bbox[0] - 1)
                    y0 = max(0, bbox[1] - 1)
                    x1 = min(spr_w, bbox[2] + 1)
                    y1 = min(spr_h, bbox[3] + 1)
                crop = im.crop((x0, y0, x1, y1))
                cw, ch = x1 - x0, y1 - y0
                ox = base_ox + x0
                oy = base_oy - y0
                max_cw = max(max_cw, cw)
                max_ch = max(max_ch, ch)
                packed_frames.append((ox, oy, cw, ch, crop.tobytes()))

    radius = math.hypot(max_cw * 0.5, max_ch * 0.5)
    out = bytearray(b"IDSP")
    out += struct.pack("<iifiiifi", 32, 0, radius, max_cw, max_ch, len(packed_frames), 0.0, 0)
    for ox, oy, cw, ch, raw in packed_frames:
        out += struct.pack("<iiiii", 0, ox, oy, cw, ch)
        out += raw

    with open(SPR32_OUT, "wb") as fp:
        fp.write(out)
    # Also save a copy in greensuit_wheelman_sprite/ for easy VPS download
    with open(os.path.join(OUT_SPR_DIR, "greensuit_wheelman.spr32"), "wb") as fp:
        fp.write(out)
    print(f"  Built {SPR32_OUT}: {len(packed_frames)} frames, {len(out)/1048576:.2f} MB")
    return len(packed_frames), len(out)


def build_posters_and_gifs(specs: List[Dict]) -> None:
    # 1) 8-Direction 360° Turnaround Sheet (Seated Cruise + Hero Crane Point)
    cw, ch = 220, 220
    turn = Image.new("RGB", (8 * cw, 2 * ch + 56), (18, 22, 30))
    dr = ImageDraw.Draw(turn)
    dr.text((16, 10), "GREEN-SUIT WHEELMAN - 8-ANGLE 360° TURNAROUND (0° -> 315°)", fill=(134, 239, 172))
    angles = ["0° Front", "45° Front-L", "90° Left", "135° Back-L", "180° Back", "225° Back-R", "270° Right", "315° Front-R"]
    for d in range(8):
        for r_idx, (aid, fi) in enumerate((("seated_cruise", 0), ("hero_crane_point", 3))):
            cell = Image.new("RGBA", (cw, ch), (26, 31, 42, 255))
            im = Image.fromarray(resize_rgba_premul(load_frame(aid, d, fi), cw, ch), "RGBA")
            cell.alpha_composite(im)
            x0, y0 = d * cw, 38 + r_idx * ch
            turn.paste(cell.convert("RGB"), (x0, y0))
            dr.rectangle([x0, y0, x0 + cw - 1, y0 + ch - 1], outline=(52, 62, 82), width=1)
            if r_idx == 0:
                dr.text((x0 + 8, y0 + 6), angles[d], fill=(203, 213, 225))
    turn.save(os.path.join(OUT_SPR_DIR, "greensuit_360_turnaround.jpg"), quality=92)

    # 2) Master 12-Animation Showcase Poster (4x3 grid)
    pw, ph = 280, 260
    poster = Image.new("RGB", (4 * pw, 3 * ph + 48), (15, 18, 25))
    pdr = ImageDraw.Draw(poster)
    pdr.text((16, 14), "GREEN-SUIT WHEELMAN - ALL 12 360° 3D SPRITE ANIMATIONS", fill=(134, 239, 172))
    hero_frames = {
        "seated_cruise": (0, 2),
        "scream_turbo": (1, 3),
        "plank_rollout": (1, 6),
        "hero_crane_point": (0, 3),
        "overhead_press": (0, 8),
        "cyclone_spin": (0, 2),
        "wheelie_backflip": (1, 6),
        "bazooka_ram": (1, 2),
        "throw_boomerang": (0, 7),
        "breakdance_flare": (0, 3),
        "victory_groove": (0, 3),
        "gib_explosion": (0, 7),
    }
    for idx, sp in enumerate(specs[:12]):
        r, c = divmod(idx, 4)
        d_pick, f_pick = hero_frames.get(sp["id"], (0, 0))
        cell = Image.new("RGBA", (pw, ph), (24, 29, 40, 255))
        im = Image.fromarray(resize_rgba_premul(load_frame(sp["id"], d_pick, f_pick), ph, ph), "RGBA")
        cell.alpha_composite(im, ((pw - ph) // 2, 0))
        x0, y0 = c * pw, 48 + r * ph
        poster.paste(cell.convert("RGB"), (x0, y0))
        pdr.rectangle([x0, y0, x0 + pw - 1, y0 + ph - 1], outline=(55, 65, 85), width=1)
        pdr.text((x0 + 10, y0 + 8), f"#{idx+1} {sp['title']}", fill=(134, 239, 172))
    poster.save(os.path.join(OUT_SPR_DIR, "greensuit_12anims_poster.jpg"), quality=92)

    # 3) 4 Reference Photo vs. 3D Sprite Comparison Grid (2x2 side-by-side 1:1 square cards, zero distortion!)
    def square_crop_rel(im_src: Image.Image, cx_r: float, cy_r: float, sz_h_r: float, out_px: int) -> Image.Image:
        iw, ih = im_src.size
        half = int(round(ih * sz_h_r * 0.5))
        cx, cy = int(round(iw * cx_r)), int(round(ih * cy_r))
        x0 = max(0, min(iw - 2 * half, cx - half))
        y0 = max(0, min(ih - 2 * half, cy - half))
        return im_src.crop((x0, y0, x0 + 2 * half, y0 + 2 * half)).resize((out_px, out_px), Image.Resampling.LANCZOS)

    comp_pairs = [
        ("ref_studio_smile.png", 0.46, 0.41, 0.74, "seated_cruise",    7, 0, "Pose 1: Seated Wheel-Cruise (315°)"),
        ("ref_scream.jpg",       0.51, 0.55, 0.70, "scream_turbo",     0, 3, "Pose 2: Battle-Cry Overdrive (0°)"),
        ("ref_plank.png",        0.27, 0.51, 0.74, "plank_rollout",    1, 6, "Pose 3: Ab-Roller Plank Launch (45°)"),
        ("ref_pose_point.jpg",   0.50, 0.42, 0.78, "hero_crane_point", 0, 3, "Pose 4: Crane Kick & Sky-Point (0°)"),
    ]
    card_sz = 256
    pair_w, pair_h = card_sz * 2 + 20, card_sz + 56
    strip = Image.new("RGB", (pair_w * 2, pair_h * 2), (16, 20, 28))
    sdr = ImageDraw.Draw(strip)
    for i, (rfn, cx_r, cy_r, sz_r, aid, d_i, f_i, label) in enumerate(comp_pairs):
        r_grid, c_grid = divmod(i, 2)
        ox, oy = c_grid * pair_w, r_grid * pair_h
        ref_full = Image.open(os.path.join(REF_DIR, rfn)).convert("RGB")
        ref_sq = square_crop_rel(ref_full, cx_r, cy_r, sz_r, card_sz)
        spr_card = Image.new("RGBA", (card_sz, card_sz), (222, 226, 232, 255))
        spr_rgba = Image.fromarray(resize_rgba_premul(load_frame(aid, d_i, f_i), card_sz, card_sz), "RGBA")
        spr_card.alpha_composite(spr_rgba, (0, 0))
        strip.paste(ref_sq, (ox + 6, oy + 32))
        strip.paste(spr_card.convert("RGB"), (ox + card_sz + 14, oy + 32))
        sdr.rectangle([ox + 2, oy + 2, ox + pair_w - 3, oy + pair_h - 3], outline=(62, 74, 96), width=1)
        sdr.text((ox + 10, oy + 10), label, fill=(134, 239, 172))
        sdr.text((ox + 12, oy + card_sz + 36), "Real Reference Photo", fill=(148, 163, 184))
        sdr.text((ox + card_sz + 20, oy + card_sz + 36), "Rendered 3D Sprite", fill=(74, 222, 128))
    strip.save(os.path.join(OUT_SPR_DIR, "greensuit_ref_vs_3d.jpg"), quality=92)

    # 4) Animated 360° Turntable GIF (24 frames orbiting all 8 directions!)
    gif_frames = []
    for k in range(24):
        d = (k // 3) % 8
        f = (k * 2) % 12
        bg = Image.new("RGBA", (260, 260), (22, 27, 38, 255))
        im = Image.fromarray(resize_rgba_premul(load_frame("seated_cruise", d, f), 260, 260), "RGBA")
        bg.alpha_composite(im)
        gif_frames.append(bg.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT))
    gif_frames[0].save(
        os.path.join(OUT_SPR_DIR, "greensuit_360_spin.gif"),
        save_all=True,
        append_images=gif_frames[1:],
        duration=55,
        loop=0,
    )
    print("  Built posters, ref-vs-3D strip, and animated 360° GIF ->", OUT_SPR_DIR)


def main() -> None:
    with open(os.path.join(RAW_DIR, "manifest.json"), "r", encoding="utf-8") as fp:
        specs = json.load(fp)
    meta = build_atlases(specs)
    nf_spr, sz_spr = build_spr32()
    build_posters_and_gifs(specs)
    with open(os.path.join(OUT_SPR_DIR, "sprite_meta.json"), "w", encoding="utf-8") as fp:
        json.dump({"anims": list(meta.values()), "spr32Frames": nf_spr, "spr32Bytes": sz_spr}, fp, indent=2)
    print("PACKING COMPLETE!")


if __name__ == "__main__":
    main()
