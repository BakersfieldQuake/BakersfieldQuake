"""End-to-end reproducible builder for 'The Flamingo Fiend' (`robeguy`) Monster Sprite Pack
in BakersfieldQuake (graphics & audio assets only — does NOT modify shared .qc, progs.dat, or .pk3).

Outputs:
  - progs/robeguy.spr32                      (336-frame tight-cropped HDR pre-toned DarkPlaces SPR32)
  - sound/robeguy/*.wav                      (5 synthesized monster WAV sound effects)
  - robeguy_sprite/frames/*.png              (High-res 520x585 RGBA PNG animation frames)
  - robeguy_sprite/robeguy_5_animations_sheet.png
  - robeguy_sprite/robeguy_360_turnaround_sheet.png
  - robeguy_sprite/anim1_monster_idle_360.gif
  - robeguy_sprite/anim2_berserker_charge_360.gif
  - robeguy_sprite/anim3_robe_flash_laser.gif
  - robeguy_sprite/anim4_flamingo_attack_360.gif
  - robeguy_sprite/anim5_flamingo_gib_death.gif
  - robeguy_sprite/robeguy_all_5_showcase.gif
  - robeguy_monster_sprite.html              (100% self-contained <canvas> 360° HTML inspector)

Run with:
  python3.13 source/mm_tools/robeguy/build_robeguy_sprites.py
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import math
import os
import shutil
import struct
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent

for p in (str(CUR_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from robeguy_keying import STAGE_GY, STAGE_H, STAGE_W, resize_rgba_premul
from robeguy_rig import load_all_robeguy_assets, synthesize_all_5_animations
from robeguy_sounds import build_all_robeguy_sounds
from robeguy_viewer_html import (
    build_antigravity_artifact_html,
    build_self_contained_robeguy_html,
    pack_webp_atlases_b64,
)

# DarkPlaces SPR32 grid (exact 8:9 aspect ratio matching 520x585 stage)
SPR_W = 256
SPR_H = 288
SPR_OX = -(SPR_W // 2)                      # -128 px
SPR_OY = round(STAGE_GY * SPR_H / STAGE_H)   #  262 px (anchored at bare feet)
RUN_6_INDICES = [0, 1, 2, 4, 5, 6]           # mbox.qc 6-frame run cadence


def pretone_and_write_tight_spr32(
    path: Path,
    stage_frames: list[np.ndarray],
    target_mean_lum: float = 62.0,
) -> tuple[int, int, float]:
    """Resizes 520x585 RGBA stage frames -> 256x288, pre-tones for DarkPlaces r_hdr_scenebrightness
    (~62 mean lum on body frames while preserving hot laser/explosion cores), and writes a lossless
    tight-cropped IDSP v32 SPR_VP_PARALLEL_UPRIGHT sprite with 1px GL clamp border."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        scaled = list(ex.map(lambda fr: resize_rgba_premul(fr, SPR_W, SPR_H), stage_frames))

    # Boost micro-contrast first, then measure mean opaque luminance across body frames (0..119)
    boosted: list[np.ndarray] = []
    ref_lums = []
    for idx, fr in enumerate(scaled):
        rgb_im = ImageEnhance.Contrast(Image.fromarray(fr[..., :3], "RGB")).enhance(1.14)
        rgb_im = ImageEnhance.Color(rgb_im).enhance(1.06)
        rgb = np.asarray(rgb_im, dtype=np.float32)
        if idx < 120:
            m = fr[..., 3] > 128
            if np.any(m):
                ref_lums.append(float((0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[m].mean()))
        boosted.append((rgb, fr[..., 3]))

    cur_mean = float(np.mean(ref_lums)) if ref_lums else 120.0
    gain = float(np.clip(target_mean_lum / max(1.0, cur_mean), 0.32, 0.88))

    cropped_records = []
    max_cw, max_ch = 1, 1
    out_lums = []

    for idx, (rgb, alpha_ch) in enumerate(boosted):
        if idx >= 120:
            # Preserve incandescent laser & explosion cores (>232 lum) on VFX attack/death banks
            lum_px = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
            emissive = np.clip((lum_px - 232.0) / 23.0, 0.0, 1.0)[..., None]
            eff_gain = gain * (1.0 - 0.50 * emissive) + 0.88 * (0.50 * emissive)
            toned_rgb = np.clip(np.round(rgb * eff_gain), 0, 255).astype(np.uint8)
        else:
            toned_rgb = np.clip(np.round(rgb * gain), 0, 255).astype(np.uint8)
        toned = np.dstack([toned_rgb, alpha_ch])

        if idx < 120:
            m = toned[..., 3] > 128
            if np.any(m):
                tr = toned[..., :3].astype(np.float32)
                out_lums.append(float((0.299 * tr[..., 0] + 0.587 * tr[..., 1] + 0.114 * tr[..., 2])[m].mean()))

        pil_f = Image.fromarray(toned, "RGBA")
        bbox = pil_f.getchannel("A").getbbox()
        if bbox is None:
            x0, y0, x1, y1 = 0, 0, 1, 1
        else:
            x0 = max(0, bbox[0] - 1)
            y0 = max(0, bbox[1] - 1)
            x1 = min(SPR_W, bbox[2] + 1)
            y1 = min(SPR_H, bbox[3] + 1)
        sub = pil_f.crop((x0, y0, x1, y1))
        cw, ch = x1 - x0, y1 - y0
        new_ox = SPR_OX + x0
        new_oy = SPR_OY - y0
        max_cw = max(max_cw, cw)
        max_ch = max(max_ch, ch)
        cropped_records.append((new_ox, new_oy, cw, ch, sub.tobytes()))

    unopt_bytes = 36 + len(scaled) * (20 + SPR_W * SPR_H * 4)
    rad = math.sqrt((max_cw / 2.0) ** 2 + float(max_ch) ** 2)
    buf = bytearray(b"IDSP")
    buf += struct.pack("<iifiiifi", 32, 0, rad, max_cw, max_ch, len(cropped_records), 0.0, 0)
    for ox, oy, cw, ch, raw in cropped_records:
        buf += struct.pack("<iiiii", 0, ox, oy, cw, ch)
        buf += raw

    path.write_bytes(bytes(buf))
    return unopt_bytes, len(buf), (float(np.mean(out_lums)) if out_lums else 0.0)


def _make_checker_rgb(w: int, h: int, cell: int = 16) -> np.ndarray:
    yg, xg = np.mgrid[0:h, 0:w]
    c = ((xg // cell + yg // cell) % 2 == 0)
    return np.where(c[..., None], np.array([34, 30, 48], np.uint8), np.array([23, 20, 34], np.uint8))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/consolab.ttf"):
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                pass
    return ImageFont.load_default()


def save_master_sheets(anims: dict, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    f_title = _load_font(24)
    f_row = _load_font(16)
    f_lbl = _load_font(12)

    # 1) Master 5-Animations Sheet (8 columns x 5 rows + header banner)
    cw, ch = 200, 225
    hdr_h = 68
    row_hdr = 30
    W1 = cw * 8
    H1 = hdr_h + 5 * (row_hdr + ch)
    sheet1 = Image.fromarray(_make_checker_rgb(W1, H1, 16), "RGB").convert("RGBA")
    dr1 = ImageDraw.Draw(sheet1)
    dr1.rectangle([0, 0, W1, hdr_h], fill=(18, 14, 28, 255))
    dr1.text((20, 12), "THE FLAMINGO FIEND (progs/robeguy.spr32) — ALL 5 MONSTER ANIMATIONS", fill=(255, 90, 178), font=f_title)
    dr1.text((20, 42), "Digitized DSLR Bathrobe Monster · Full 8-Angle 360° Rig + 4-Act Quake Feather & Gib Explosion", fill=(205, 198, 224), font=f_row)

    rows_5 = [
        ("ANIM 1: Unhinged 3 AM Flamingo Whisperer (360° Idle — Glowing Red Eyes + Snapping Fanged Pocket Flamingos)",
         [(anims["monster_idle"][d][d % 8], f"{d*45}° f{d%8}") for d in range(8)]),
        ("ANIM 2: 'STAY OFF MY LAWN!' Barefoot Bathrobe Berserker Charge (360° Sprint — Wild Arms, Billowing Skirt & Feathers)",
         [(anims["berserker_charge"][d][d % 8], f"{d*45}° f{d%8}") for d in range(8)]),
        ("ANIM 3: The 'MY EYES!!' Heart-Boxers Chest-Hair Mega-Laser (Whips Robe Like Bat-Wings + Fires Volumetric Pink Beam)",
         [(anims["robe_flash_laser"][0][0], "0° Windup"),
          (anims["robe_flash_laser"][0][2], "0° WhipOpen"),
          (anims["robe_flash_laser"][0][4], "0° Blast!"),
          (anims["robe_flash_laser"][1][5], "45° Beam"),
          (anims["robe_flash_laser"][2][5], "90° Beam"),
          (anims["robe_flash_laser"][6][5], "270° Beam"),
          (anims["robe_flash_laser"][7][5], "315° Beam"),
          (anims["robe_flash_laser"][0][10], "0° SmugGrin")]),
        ("ANIM 4: Dual Fanged Lawn-Flamingo Club & '#1 MONSTER' Hot-Coffee Rampage (+ Torpedo Flamingo Missile)",
         [(anims["flamingo_attack"][0][1], "0° Windup"),
          (anims["flamingo_attack"][0][4], "0° Swing+Launch"),
          (anims["flamingo_attack"][1][5], "45° Missile"),
          (anims["flamingo_attack"][2][3], "90° ClubArc"),
          (anims["flamingo_attack"][2][6], "90° Torpedo"),
          (anims["flamingo_attack"][4][5], "180° Back"),
          (anims["flamingo_attack"][6][6], "270° Torpedo"),
          (anims["flamingo_attack"][7][5], "315° Rampage")]),
        ("ANIM 5: Catastrophic 4-Act Flamingo Feather & Quake Gib Explosion (24 Frames: Overload -> Fireball -> Bouncing Head -> Robe Pile)",
         [(anims["flamingo_gib_death"][k], f"Frame {k+1}/24") for k in (1, 4, 5, 7, 10, 14, 18, 23)]),
    ]

    for ri, (rtitle, cells) in enumerate(rows_5):
        y0 = hdr_h + ri * (row_hdr + ch)
        dr1.rectangle([0, y0, W1, y0 + row_hdr], fill=(32, 22, 48, 245))
        dr1.text((14, y0 + 6), rtitle, fill=(255, 224, 242), font=f_row)
        for ci, (fr, clbl) in enumerate(cells):
            x0 = ci * cw
            yc = y0 + row_hdr
            cell_im = Image.fromarray(resize_rgba_premul(fr, cw, ch), "RGBA")
            sheet1.alpha_composite(cell_im, (x0, yc))
            dr1.text((x0 + 8, yc + ch - 20), clbl, fill=(251, 191, 36), font=f_lbl)

    p_five = out_dir / "robeguy_5_animations_sheet.png"
    sheet1.convert("RGB").save(p_five, optimize=True)

    # 2) Master 360° Turnaround Sheet (8 angles 0°..315° x 4 directional animations)
    H2 = hdr_h + 4 * (row_hdr + ch)
    sheet2 = Image.fromarray(_make_checker_rgb(W1, H2, 16), "RGB").convert("RGBA")
    dr2 = ImageDraw.Draw(sheet2)
    dr2.rectangle([0, 0, W1, hdr_h], fill=(18, 14, 28, 255))
    dr2.text((20, 12), "THE FLAMINGO FIEND — FULL 8-ANGLE 360° TURNAROUND SHEET (0° TO 315°)", fill=(56, 189, 248), font=f_title)
    dr2.text((20, 42), "Consistent Crown Height, Barefoot Stride, Billowing Pink Robe & 3D Depth-Sorted Props Across All 8 Angles", fill=(205, 198, 224), font=f_row)

    dir_names = ["0° Front", "45° Front-L", "90° Left", "135° Back-L", "180° Back", "225° Back-R", "270° Right", "315° Front-R"]
    turn_rows = [
        ("1. Unhinged Whisperer Idle (Peak Pocket-Flamingo Snap)", [anims["monster_idle"][d][2] for d in range(8)]),
        ("2. Barefoot Bathrobe Berserker Charge (Peak Stride)", [anims["berserker_charge"][d][1] for d in range(8)]),
        ("3. Heart-Boxers Chest-Hair Mega-Laser (Peak Beam Blast)", [anims["robe_flash_laser"][d][5] for d in range(8)]),
        ("4. Dual Lawn-Flamingo & Hot-Coffee Attack (Peak Missile)", [anims["flamingo_attack"][d][5] for d in range(8)]),
    ]
    for ri, (rtitle, frames) in enumerate(turn_rows):
        y0 = hdr_h + ri * (row_hdr + ch)
        dr2.rectangle([0, y0, W1, y0 + row_hdr], fill=(24, 30, 48, 245))
        dr2.text((14, y0 + 6), rtitle, fill=(224, 242, 254), font=f_row)
        for d, fr in enumerate(frames):
            x0 = d * cw
            yc = y0 + row_hdr
            sheet2.alpha_composite(Image.fromarray(resize_rgba_premul(fr, cw, ch), "RGBA"), (x0, yc))
            dr2.text((x0 + 8, yc + ch - 20), dir_names[d], fill=(125, 211, 252), font=f_lbl)

    p_turn = out_dir / "robeguy_360_turnaround_sheet.png"
    sheet2.convert("RGB").save(p_turn, optimize=True)
    return {"five_anims": p_five, "turnaround": p_turn}


def _frames_to_gif(frames_rgba: list[np.ndarray], out_path: Path, gw: int = 288, gh: int = 324, duration_ms: int | list[int] = 80, labels: list[str] | None = None) -> None:
    bg = _make_checker_rgb(gw, gh, 14)
    font = _load_font(13)
    pal_frames: list[Image.Image] = []
    for i, fr in enumerate(frames_rgba):
        tile = Image.fromarray(bg, "RGB").convert("RGBA")
        tile.alpha_composite(Image.fromarray(resize_rgba_premul(fr, gw, gh), "RGBA"))
        if labels and i < len(labels) and labels[i]:
            dr = ImageDraw.Draw(tile)
            dr.rounded_rectangle([8, 8, gw - 8, 30], radius=6, fill=(14, 11, 22, 215), outline=(255, 65, 162, 220))
            dr.text((15, 11), labels[i], fill=(255, 225, 244), font=font)
        pal_frames.append(tile.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG))

    pal_frames[0].save(
        out_path,
        save_all=True,
        append_images=pal_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def save_all_gifs(anims: dict, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # 1. Idle 360 orbit (32 frames: 4 frames per direction)
    seq1 = [anims["monster_idle"][(s // 4) % 8][s % 8] for s in range(32)]
    p1 = out_dir / "anim1_monster_idle_360.gif"
    _frames_to_gif(seq1, p1, duration_ms=95, labels=[f"1. Whisperer Idle · {((s//4)%8)*45}°" for s in range(32)])
    paths["monster_idle"] = p1

    # 2. Berserker Charge 360 orbit (32 frames)
    seq2 = [anims["berserker_charge"][(s // 4) % 8][s % 8] for s in range(32)]
    p2 = out_dir / "anim2_berserker_charge_360.gif"
    _frames_to_gif(seq2, p2, duration_ms=70, labels=[f"2. Berserker Charge · {((s//4)%8)*45}°" for s in range(32)])
    paths["berserker_charge"] = p2

    # 3. Heart-Boxers Chest-Hair Laser (0° Front + 45° + 90° + 315° showcase = 28 frames)
    seq3, lbl3 = [], []
    for d_show, d_lbl in ((0, "0° Front"), (1, "45° Diag"), (2, "90° Side")):
        for f in range(12):
            seq3.append(anims["robe_flash_laser"][d_show][f])
            lbl3.append(f"3. Chest-Hair Laser · {d_lbl}")
    p3 = out_dir / "anim3_robe_flash_laser.gif"
    _frames_to_gif(seq3, p3, duration_ms=85, labels=lbl3)
    paths["robe_flash_laser"] = p3

    # 4. Dual Lawn-Flamingo & Coffee Attack (0°, 45°, 90°, 270°)
    seq4, lbl4 = [], []
    for d_show, d_lbl in ((0, "0° Front"), (2, "90° Left"), (6, "270° Right")):
        for f in range(12):
            seq4.append(anims["flamingo_attack"][d_show][f])
            lbl4.append(f"4. Flamingo & Coffee · {d_lbl}")
    p4 = out_dir / "anim4_flamingo_attack_360.gif"
    _frames_to_gif(seq4, p4, duration_ms=80, labels=lbl4)
    paths["flamingo_attack"] = p4

    # 5. 4-Act Catastrophic Flamingo Feather & Gib Explosion (24 frames, hold final corpse 4 ticks)
    seq5 = list(anims["flamingo_gib_death"])
    durs5 = [80] * 23 + [550]
    p5 = out_dir / "anim5_flamingo_gib_death.gif"
    _frames_to_gif(seq5, p5, duration_ms=durs5, labels=[f"5. Gib Explosion · Frame {i+1}/24" for i in range(24)])
    paths["flamingo_gib_death"] = p5

    # 6. Combined All-5 Showcase Reel!
    showcase_seq, showcase_lbl, showcase_dur = [], [], []
    for f in range(8):
        showcase_seq.append(anims["monster_idle"][0][f])
        showcase_lbl.append("1/5: Unhinged Flamingo Whisperer")
        showcase_dur.append(90)
    for s in range(12):
        d = (s // 3) % 8
        showcase_seq.append(anims["berserker_charge"][d][s % 8])
        showcase_lbl.append(f"2/5: Barefoot Berserker ({d*45}°)")
        showcase_dur.append(70)
    for f in range(12):
        showcase_seq.append(anims["robe_flash_laser"][0][f])
        showcase_lbl.append("3/5: Heart-Boxers Chest-Hair Laser!")
        showcase_dur.append(85)
    for f in range(12):
        showcase_seq.append(anims["flamingo_attack"][2 if 3 <= f <= 8 else 0][f])
        showcase_lbl.append("4/5: Lawn-Flamingo & Coffee Attack!")
        showcase_dur.append(80)
    for i, fr in enumerate(anims["flamingo_gib_death"]):
        showcase_seq.append(fr)
        showcase_lbl.append("5/5: Flamingo Feather & Gib Boom!")
        showcase_dur.append(500 if i == 23 else 75)

    p_show = out_dir / "robeguy_all_5_showcase.gif"
    _frames_to_gif(showcase_seq, p_show, duration_ms=showcase_dur, labels=showcase_lbl)
    paths["showcase"] = p_show
    return paths


def export_highres_pngs(anims: dict, frames_dir: Path) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[Path, np.ndarray]] = []
    for m_key in ("monster_idle", "berserker_charge", "robe_flash_laser", "flamingo_attack"):
        grid = anims[m_key]
        for d in range(8):
            for f, arr in enumerate(grid[d]):
                jobs.append((frames_dir / f"{m_key}_d{d}_f{f:02d}.png", arr))
    for f, arr in enumerate(anims["flamingo_gib_death"]):
        jobs.append((frames_dir / f"flamingo_gib_death_f{f:02d}.png", arr))

    def _save(item: tuple[Path, np.ndarray]) -> None:
        Image.fromarray(item[1], "RGBA").save(item[0], compress_level=4)

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        list(ex.map(_save, jobs))
    return len(jobs)


def main() -> None:
    t0 = time.time()
    print("[1/7] Synthesizing 5 custom monster WAV sound effects...")
    snd_dir = MOD_DIR / "sound" / "robeguy"
    sound_paths = build_all_robeguy_sounds(snd_dir)
    for k, p in sound_paths.items():
        print(f"      {k:20s} -> {p.relative_to(MOD_DIR)} ({p.stat().st_size // 1024} KB)")

    print("[2/7] Loading & chroma-keying DSLR studio plates + AI turnaround/heads/props...")
    assets = load_all_robeguy_assets()

    print("[3/7] Synthesizing all 5 monster animations in parallel across 360°...")
    anims = synthesize_all_5_animations(assets)

    out_dir = MOD_DIR / "robeguy_sprite"
    print("[4/7] Exporting 344 high-res (520x585) RGBA PNG frames...")
    n_png = export_highres_pngs(anims, out_dir / "frames")
    print(f"      Exported {n_png} RGBA PNGs to {out_dir / 'frames'}")

    print("[5/7] Building HDR pre-toned tight-cropped DarkPlaces sprite progs/robeguy.spr32...")
    spr_frames: list[np.ndarray] = []
    # 0..7: 8-dir Standing Monster Idle keyposes (mbox.qc compatible)
    for d in range(8):
        spr_frames.append(anims["monster_idle"][d][0])
    # 8..55: 8-dir x 6f Barefoot Berserker Charge Run (mbox.qc compatible: 8 + d*6 + k)
    for d in range(8):
        for k in RUN_6_INDICES:
            spr_frames.append(anims["berserker_charge"][d][k])
    # 56..119: 8-dir x 8f Animated Unhinged Flamingo Whisperer Idle
    for d in range(8):
        spr_frames.extend(anims["monster_idle"][d])
    # 120..215: 8-dir x 12f Heart-Boxers Chest-Hair Mega-Laser
    for d in range(8):
        spr_frames.extend(anims["robe_flash_laser"][d])
    # 216..311: 8-dir x 12f Dual Lawn-Flamingo & Hot-Coffee Rampage
    for d in range(8):
        spr_frames.extend(anims["flamingo_attack"][d])
    # 312..335: 24-frame 4-Act Flamingo Feather & Quake Gib Explosion
    spr_frames.extend(anims["flamingo_gib_death"])

    spr_path = MOD_DIR / "progs" / "robeguy.spr32"
    raw_sz, opt_sz, mean_lum = pretone_and_write_tight_spr32(spr_path, spr_frames, target_mean_lum=62.0)
    pct_saved = (1.0 - opt_sz / max(1, raw_sz)) * 100.0
    print(f"      Wrote {spr_path.relative_to(MOD_DIR)}: {len(spr_frames)} frames, mean_lum={mean_lum:.1f}, "
          f"{raw_sz/1048576:.2f} MB -> {opt_sz/1048576:.2f} MB (-{pct_saved:.1f}% tight-crop)")

    print("[6/7] Rendering master contact sheets & 6 animated showcase GIFs...")
    sheet_paths = save_master_sheets(anims, out_dir)
    gif_paths = save_all_gifs(anims, out_dir)

    print("[7/7] Packing RGBA WebP 360° atlases & building self-contained interactive HTML viewers...")
    atlases_b64 = pack_webp_atlases_b64(anims)
    html_path = MOD_DIR / "robeguy_monster_sprite.html"
    h_sz = build_self_contained_robeguy_html(atlases_b64, sound_paths, gif_paths, sheet_paths, html_path)
    print(f"      Wrote {html_path.name} ({h_sz / 1048576:.2f} MB, 100% self-contained)")

    dev_dir = MOD_DIR.parent / "_bakersfield_dev"
    if dev_dir.is_dir():
        shutil.copy2(html_path, dev_dir / "robeguy_monster_sprite.html")
        print(f"      Copied viewer to {dev_dir / 'robeguy_monster_sprite.html'}")

    print(f"DONE in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
