"""End-to-End 360° Sprite, Contact Sheet, Animated GIF, & HTML Showcase Builder
for David Ojeda & the 3 Running Pregnant Hispanic Women (BakersfieldQuake).

Outputs:
  1. progs/david.spr32            (344 frames, 256x288, origin (-128, 262), HDR pre-toned)
       0..7     idle[0..7]
       8..55    fast_run[d][k]        (8 dirs x 6 frames — mbox.qc compatible)
       56..103  turbo_sprint[d][k]    (8 dirs x 6 frames)
       104..151 money_hold[d][k]      (8 dirs x 6 frames)
       152..199 money_run[d][k]       (8 dirs x 6 frames)
       200..247 slot_spin[d][k]       (8 dirs x 6 frames)
       248..295 slot_jackpot[d][k]    (8 dirs x 6 frames)
       296..343 slot_bust[d][k]       (8 dirs x 6 frames)
  2. progs/preg_1.spr32 .. preg_3.spr32 (56 frames each, 128x144, origin (-64, 131), HDR pre-toned)
       0..7     idle[0..7]
       8..55    run[d][k]             (8 dirs x 6 frames — mbox.qc compatible)
  3. david_sprite/*.png           (all 480x540 high-res RGBA frames for web & inspection)
  4. david_sprite/*.gif           (4 smooth 360° orbiting turntable GIFs)
  5. david_sprite/*_sheet.png     (2 master 360° turnaround & running contact sheets)
  6. david_sprite/index.html & david_ojeda_sprites.html
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import math
import os
import struct
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent

for p in (str(CUR_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from david_rig import (
    STAGE_GY,
    STAGE_H,
    STAGE_W,
    build_all_character_animations,
    load_all_studio_assets,
    resize_rgba_premul,
)
from david_viewer_html import write_david_showcases

# SPR32 dimensions & foot-anchored origins
DV_SPR_W, DV_SPR_H = 256, 288
DV_SPR_OX = -(DV_SPR_W // 2)
DV_SPR_OY = round(STAGE_GY * DV_SPR_H / STAGE_H)  # 262

PR_SPR_W, PR_SPR_H = 128, 144
PR_SPR_OX = -(PR_SPR_W // 2)
PR_SPR_OY = round(STAGE_GY * PR_SPR_H / STAGE_H)  # 131

RUN_6_INDICES = [0, 1, 2, 4, 5, 6]
DIR_LABELS = ["0° Front", "45° Front-L", "90° Left", "135° Back-L", "180° Back", "225° Back-R", "270° Right", "315° Front-R"]


def pretone_for_darkplaces_hdr(frames_rgba: list[np.ndarray], target_mean_lum: float = 62.0) -> list[np.ndarray]:
    """Pre-tones SPR32 RGB for DarkPlaces r_hdr_scenebrightness ~2.5 so sprites match fr_rob/bryan (~60-65 lum)."""
    boosted: list[np.ndarray] = []
    lums: list[float] = []
    for fr in frames_rgba:
        rgb_im = Image.fromarray(fr[..., :3], "RGB")
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(1.15)
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


def write_spr32(path: Path, frames_rgba: list[np.ndarray], ox: int, oy: int) -> tuple[int, float]:
    """Writes an IDSP v32 SPR_VP_PARALLEL_UPRIGHT (stype=0) 32-bit RGBA DarkPlaces sprite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    maxw = max(f.shape[1] for f in frames_rgba)
    maxh = max(f.shape[0] for f in frames_rgba)
    rad = math.sqrt((maxw / 2.0) ** 2 + float(maxh) ** 2)

    buf = bytearray()
    buf += b"IDSP"
    buf += struct.pack("<iifiiifi", 32, 0, rad, maxw, maxh, len(frames_rgba), 0.0, 0)

    lums: list[float] = []
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


def _save_png(task: tuple[Path, np.ndarray]) -> None:
    p, arr = task
    Image.fromarray(arr, "RGBA").save(p, compress_level=3)


def make_david_master_sheet(dv: dict, out_path: Path) -> None:
    rows = [
        ("Standing Idle 360°", [dv["idle"][d] for d in range(8)]),
        ("Fast Run 360°", [dv["fast_run"][d][1] for d in range(8)]),
        ("Turbo Sprint 360°", [dv["turbo_sprint"][d][1] for d in range(8)]),
        ("Holding Money Bag 360°", [dv["money_hold"][d][2] for d in range(8)]),
        ("Money-Bag Sprint 360°", [dv["money_run"][d][1] for d in range(8)]),
        ("Slot Machine Spin 360°", [dv["slot_spin"][d][1] for d in range(8)]),
        ("Slot 7-7-7 JACKPOT 360°", [dv["slot_jackpot"][d][2] for d in range(8)]),
        ("Slot Machine BUST 360°", [dv["slot_bust"][d][0] for d in range(8)]),
    ]
    cw, ch = 200, 225
    hdr_h = 34
    sheet = Image.new("RGB", (cw * 8, hdr_h + ch * len(rows)), (20, 23, 31))
    dr = ImageDraw.Draw(sheet)
    for d in range(8):
        dr.text((d * cw + 52, 10), DIR_LABELS[d], fill=(253, 230, 138))

    for r_i, (lbl, imgs) in enumerate(rows):
        oy = hdr_h + r_i * ch
        for d in range(8):
            ox = d * cw
            bg_c = (28, 32, 43) if (r_i + d) % 2 == 0 else (23, 27, 36)
            dr.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], fill=bg_c, outline=(42, 49, 64))
            cell = Image.fromarray(resize_rgba_premul(imgs[d], cw, ch), "RGBA")
            sheet.paste(cell, (ox, oy), cell)
        dr.rectangle([6, oy + 6, 178, oy + 24], fill=(14, 17, 24))
        dr.text((11, oy + 9), lbl, fill=(248, 250, 252))

    sheet.save(out_path, optimize=True)


def make_pregnant_runners_sheet(anims: dict, out_path: Path) -> None:
    rows = [
        ("Runner #1 (Coral Top) - 360° Stride A", [anims["preg1"]["run"][d][0] for d in range(8)]),
        ("Runner #1 (Coral Top) - 360° Stride B", [anims["preg1"]["run"][d][2] for d in range(8)]),
        ("Runner #2 (Teal Top) - 360° Stride A", [anims["preg2"]["run"][d][0] for d in range(8)]),
        ("Runner #2 (Teal Top) - 360° Stride B", [anims["preg2"]["run"][d][2] for d in range(8)]),
        ("Runner #3 (Yellow Top) - 360° Stride A", [anims["preg3"]["run"][d][0] for d in range(8)]),
        ("Runner #3 (Yellow Top) - 360° Stride B", [anims["preg3"]["run"][d][2] for d in range(8)]),
    ]
    cw, ch = 200, 225
    hdr_h = 34
    sheet = Image.new("RGB", (cw * 8, hdr_h + ch * len(rows)), (18, 24, 28))
    dr = ImageDraw.Draw(sheet)
    for d in range(8):
        dr.text((d * cw + 52, 10), DIR_LABELS[d], fill=(167, 243, 208))

    for r_i, (lbl, imgs) in enumerate(rows):
        oy = hdr_h + r_i * ch
        for d in range(8):
            ox = d * cw
            bg_c = (26, 33, 40) if (r_i + d) % 2 == 0 else (21, 28, 34)
            dr.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], fill=bg_c, outline=(40, 52, 60))
            cell = Image.fromarray(resize_rgba_premul(imgs[d], cw, ch), "RGBA")
            sheet.paste(cell, (ox, oy), cell)
        dr.rectangle([6, oy + 6, 238, oy + 24], fill=(12, 18, 22))
        dr.text((11, oy + 9), lbl, fill=(236, 253, 245))

    sheet.save(out_path, optimize=True)


def save_orbit_gif(seq_rgba: list[np.ndarray], labels: list[str], out_path: Path, w: int = 280, h: int = 315, duration_ms: int = 75) -> None:
    pil_frames: list[Image.Image] = []
    for arr, lbl in zip(seq_rgba, labels):
        bg = Image.new("RGB", (w, h), (26, 22, 30))
        dr = ImageDraw.Draw(bg)
        # Subtle warm casino floor vignette
        dr.ellipse([24, h - 52, w - 24, h - 14], fill=(42, 33, 38))
        scaled = Image.fromarray(resize_rgba_premul(arr, w, h), "RGBA")
        bg.paste(scaled, (0, 0), scaled)
        dr.rectangle([8, 8, min(w - 8, 14 + len(lbl) * 6), 26], fill=(12, 14, 20))
        dr.text((13, 11), lbl, fill=(253, 230, 138))
        pil_frames.append(bg.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    pil_frames[0].save(
        out_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def save_trio_runners_gif(anims: dict, out_path: Path) -> None:
    cw, ch = 180, 202
    W, H = cw * 3, ch
    pil_frames: list[Image.Image] = []
    for step in range(24):
        d = (step // 3) % 8
        f = step % 8
        bg = Image.new("RGB", (W, H), (20, 26, 32))
        dr = ImageDraw.Draw(bg)
        for i, key in enumerate(("preg1", "preg2", "preg3")):
            arr = anims[key]["run"][d][(f + i * 2) % 8]
            im = Image.fromarray(resize_rgba_premul(arr, cw, ch), "RGBA")
            bg.paste(im, (i * cw, 0), im)
        dr.rectangle([8, 6, 228, 23], fill=(12, 16, 22))
        dr.text((13, 9), f"3 Pregnant Runners · {DIR_LABELS[d]}", fill=(167, 243, 208))
        pil_frames.append(bg.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    pil_frames[0].save(out_path, save_all=True, append_images=pil_frames[1:], duration=75, loop=0, optimize=True)


def main() -> None:
    t0 = time.time()
    print("[1/5] Loading studio plates, facial expressions, money bag, & slot machine...")
    assets = load_all_studio_assets()

    print("[2/5] Synthesizing full 8-direction x 8-frame 360° animations in parallel...")
    anims = build_all_character_animations(assets, n_frames=8)
    dv = anims["david"]

    web_dir = MOD_DIR / "david_sprite"
    progs_dir = MOD_DIR / "progs"
    web_dir.mkdir(parents=True, exist_ok=True)
    progs_dir.mkdir(parents=True, exist_ok=True)

    print("[3/5] Saving 640+ high-res 480x540 RGBA PNG frames to david_sprite/...")
    png_tasks: list[tuple[Path, np.ndarray]] = []
    for d in range(8):
        png_tasks.append((web_dir / f"david_idle_d{d}.png", dv["idle"][d]))
        for mode in ("fast_run", "turbo_sprint", "money_hold", "money_run", "slot_spin", "slot_jackpot", "slot_bust"):
            for f in range(8):
                png_tasks.append((web_dir / f"david_{mode}_d{d}_f{f}.png", dv[mode][d][f]))
        for p_idx, p_key in enumerate(("preg1", "preg2", "preg3"), start=1):
            png_tasks.append((web_dir / f"preg{p_idx}_idle_d{d}.png", anims[p_key]["idle"][d]))
            for f in range(8):
                png_tasks.append((web_dir / f"preg{p_idx}_run_d{d}_f{f}.png", anims[p_key]["run"][d][f]))

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        list(ex.map(_save_png, png_tasks))
    print(f"      Saved {len(png_tasks)} PNGs.")

    print("[4/5] Building HDR-pretoned DarkPlaces SPR32 sprites in progs/...")
    # 4a) progs/david.spr32 (344 frames, 256x288)
    dv_raw_list: list[np.ndarray] = [dv["idle"][d] for d in range(8)]
    for mode in ("fast_run", "turbo_sprint", "money_hold", "money_run", "slot_spin", "slot_jackpot", "slot_bust"):
        for d in range(8):
            for k in RUN_6_INDICES:
                dv_raw_list.append(dv[mode][d][k])
    assert len(dv_raw_list) == 344, f"Expected 344 David frames, got {len(dv_raw_list)}"

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        dv_scaled = list(ex.map(lambda a: resize_rgba_premul(a, DV_SPR_W, DV_SPR_H), dv_raw_list))
    dv_toned = pretone_for_darkplaces_hdr(dv_scaled, target_mean_lum=62.0)
    dv_bytes, dv_lum = write_spr32(progs_dir / "david.spr32", dv_toned, DV_SPR_OX, DV_SPR_OY)
    print(f"      progs/david.spr32: {len(dv_toned)} frames ({DV_SPR_W}x{DV_SPR_H}, origin=({DV_SPR_OX},{DV_SPR_OY})), {dv_bytes / 1048576:.2f} MB, lum={dv_lum:.1f}")

    # 4b) progs/preg_1.spr32, preg_2.spr32, preg_3.spr32 (56 frames each, 128x144)
    for p_idx, p_key in enumerate(("preg1", "preg2", "preg3"), start=1):
        pr_raw_list: list[np.ndarray] = [anims[p_key]["idle"][d] for d in range(8)]
        for d in range(8):
            for k in RUN_6_INDICES:
                pr_raw_list.append(anims[p_key]["run"][d][k])
        assert len(pr_raw_list) == 56
        pr_scaled = [resize_rgba_premul(a, PR_SPR_W, PR_SPR_H) for a in pr_raw_list]
        pr_toned = pretone_for_darkplaces_hdr(pr_scaled, target_mean_lum=62.0)
        pr_bytes, pr_lum = write_spr32(progs_dir / f"preg_{p_idx}.spr32", pr_toned, PR_SPR_OX, PR_SPR_OY)
        print(f"      progs/preg_{p_idx}.spr32: {len(pr_toned)} frames ({PR_SPR_W}x{PR_SPR_H}, origin=({PR_SPR_OX},{PR_SPR_OY})), {pr_bytes / 1048576:.2f} MB, lum={pr_lum:.1f}")

    print("[5/5] Exporting master 360° contact sheets, animated turntable GIFs, & HTML showcases...")
    make_david_master_sheet(dv, web_dir / "david_360_turnaround_sheet.png")
    make_pregnant_runners_sheet(anims, web_dir / "pregnant_runners_360_sheet.png")

    # Orbiting GIF 1: Fast Run + Turbo Sprint 360°
    seq_run, lbl_run = [], []
    for step in range(32):
        d = (step // 2) % 8
        m = "fast_run" if step < 16 else "turbo_sprint"
        seq_run.append(dv[m][d][step % 8])
        lbl_run.append(f"{'Fast Run' if step < 16 else 'Turbo Sprint'} · {DIR_LABELS[d]}")
    save_orbit_gif(seq_run, lbl_run, web_dir / "david_fast_run_360.gif")

    # Orbiting GIF 2: Holding Money Bag + Running w/ Money Bag 360°
    seq_mb, lbl_mb = [], []
    for step in range(32):
        d = (step // 2) % 8
        m = "money_hold" if step < 16 else "money_run"
        seq_mb.append(dv[m][d][step % 8])
        lbl_mb.append(f"{'Money Bag Hold' if step < 16 else 'Money Heist Run'} · {DIR_LABELS[d]}")
    save_orbit_gif(seq_mb, lbl_mb, web_dir / "david_money_bag_360.gif")

    # Orbiting GIF 3: Slot Machine Spin -> 777 Jackpot -> Bust 360°
    seq_sl, lbl_sl = [], []
    for phase_i, (m, tag) in enumerate((("slot_spin", "Slot Spin"), ("slot_jackpot", "7-7-7 JACKPOT!"), ("slot_bust", "Slot BUST!"))):
        for step in range(16):
            d = (step // 2) % 8
            seq_sl.append(dv[m][d][step % 8])
            lbl_sl.append(f"{tag} · {DIR_LABELS[d]}")
    save_orbit_gif(seq_sl, lbl_sl, web_dir / "david_slot_machine_360.gif")

    # Orbiting GIF 4: All 3 Pregnant Hispanic Women Running 360°
    save_trio_runners_gif(anims, web_dir / "pregnant_runners_360.gif")

    write_david_showcases(MOD_DIR)
    print(f"ALL DONE in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
