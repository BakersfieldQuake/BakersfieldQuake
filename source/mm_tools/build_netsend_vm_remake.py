"""Generates the high-DPI photorealistic 3.5" 'LOL.BAT' floppy disk texture strip (1024x300)
and orchestrates Blender 5.2 sculpting, Cycles SSS/micro-bump baking, 60-frame armature
animation, single-surface MD3 export (`progs/v_netsend.md3`), and preview sheet composition.

Usage:
    python3.13 source/mm_tools/build_netsend_vm_remake.py
"""
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
STAGED_PROGS = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\progs"
OUT_DIR = os.path.join(HERE, "out", "netsend_realhand")
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

sys.path.insert(0, HERE)
import md3lib


def _font(size, bold=True, mono=True, marker=False):
    if marker:
        cands = ["seguisb.ttf", "trebucbd.ttf", "comicbd.ttf", "arialbd.ttf"]
    elif mono:
        cands = ["consolab.ttf", "lucon.ttf", "courbd.ttf"] if bold else ["consola.ttf", "lucon.ttf", "cour.ttf"]
    else:
        cands = ["tahomabd.ttf", "arialbd.ttf"] if bold else ["tahoma.ttf", "arial.ttf"]
    for nm in cands:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=101, octaves=(2, 4, 8, 16, 32)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tot = 0.0
    for i, f in enumerate(octaves):
        amp = 0.52 ** i
        gh = max(2, h // f)
        gw = max(2, w // f)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tot += amp
    return acc / max(tot, 1e-6)


def build_floppy_strip_srgb(out_strip_path):
    """Synthesizes a photorealistic un-dimmed sRGB 1024x300 top atlas strip for the 3.5" HD floppy disk:
      - Panel 1 [x:   4..284, y: 4..284] (280x280): Front ABS shell + recessed warm paper label + Sharpie 'LOL.BAT'
      - Panel 2 [x: 296..576, y: 4..284] (280x280): Back ABS shell + radial brushed steel spindle chuck hub
      - Panel 3 [x: 588..852, y: 4..284] (264x280): Brushed stainless-steel sliding shutter + dark Mylar window
      - Panel 4 [x: 864..1020,y: 4..284] (156x280): Micro-pebbled ABS beveled rim & corner notch swatch
    """
    W, H = 1024, 300
    grain_fine = _fbm(H, W, seed=313, octaves=(1, 2, 4, 8))
    grain_med = _fbm(H, W, seed=907, octaves=(4, 8, 16, 32))

    # Realistic matte charcoal-black Verbatim/Sony 3.5" MF-2HD ABS plastic (micro-pebbled sheen, never pitch-black!)
    pebble = 58.0 + 6.5 * grain_fine + 4.5 * grain_med
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[..., 0] = pebble * 0.96
    arr[..., 1] = pebble * 0.99
    arr[..., 2] = pebble * 1.06

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # ==========================================================================
    # PANEL 1 [4..284, 4..284]: FRONT SHELL + PAPER STICKER LABEL ('LOL.BAT')
    # ==========================================================================
    x0, y0, S = 4, 4, 280
    # Outer molded bevel highlight & subtle bottom-right shadow
    dr.rectangle([x0 + 1, y0 + 1, x0 + S - 2, y0 + S - 2], outline=(98, 103, 114), width=2)
    dr.line([x0 + 2, y0 + 2, x0 + S - 3, y0 + 2], fill=(122, 128, 140), width=2)
    dr.line([x0 + 2, y0 + 2, x0 + 2, y0 + S - 3], fill=(114, 120, 132), width=2)

    # Recessed top sliding shutter pocket (x: 48..244, y: 0..88)
    dr.rectangle([x0 + 44, y0, x0 + 240, y0 + 88], fill=(34, 36, 42), outline=(22, 24, 28), width=2)
    dr.line([x0 + 45, y0 + 89, x0 + 239, y0 + 89], fill=(88, 93, 104), width=1)

    # Embossed insertion arrow (top-left) & crisp "HD" mark (top-right)
    dr.polygon([(x0 + 22, y0 + 14), (x0 + 33, y0 + 32), (x0 + 11, y0 + 32)], fill=(96, 101, 112), outline=(40, 42, 48))
    dr.rounded_rectangle([x0 + 247, y0 + 15, x0 + 271, y0 + 35], radius=2, outline=(104, 110, 122), width=1)
    dr.text((x0 + 250, y0 + 17), "HD", fill=(124, 130, 142), font=_font(13, bold=True))

    # Write-protect square window (bottom-left) + HD sense hole (bottom-right)
    dr.rectangle([x0 + 10, y0 + 240, x0 + 26, y0 + 264], fill=(16, 17, 20), outline=(86, 90, 100), width=1)
    dr.rectangle([x0 + 12, y0 + 242, x0 + 24, y0 + 252], fill=(42, 44, 50))  # closed write-protect tab
    dr.rectangle([x0 + 254, y0 + 240, x0 + 270, y0 + 264], fill=(12, 13, 16), outline=(86, 90, 100), width=1)

    # Recessed label well & authentic warm cream paper sticker (x0+30 .. x0+250, y0+95 .. y0+272)
    lx0, ly0, lx1, ly1 = x0 + 28, y0 + 95, x0 + 252, y0 + 272
    dr.rounded_rectangle([lx0 - 3, ly0 - 3, lx1 + 3, ly1 + 3], radius=8, fill=(26, 28, 33))

    # Build paper label with realistic fiber texture & subtle corner wear
    lw, lh = lx1 - lx0, ly1 - ly0
    p_noise = _fbm(lh, lw, seed=555, octaves=(2, 4, 8, 16))
    yy_l, xx_l = np.mgrid[0:lh, 0:lw].astype(np.float32)
    edge_vig = 1.0 - 0.06 * np.clip(
        np.maximum(np.abs(xx_l - lw * 0.5) / (lw * 0.5), np.abs(yy_l - lh * 0.5) / (lh * 0.5)) ** 3,
        0.0, 1.0
    )
    paper = np.zeros((lh, lw, 4), dtype=np.uint8)
    paper[..., 0] = np.clip((245.0 + 4.5 * p_noise) * edge_vig, 200, 255).astype(np.uint8)
    paper[..., 1] = np.clip((241.0 + 4.2 * p_noise) * edge_vig, 195, 252).astype(np.uint8)
    paper[..., 2] = np.clip((226.0 + 4.0 * p_noise) * edge_vig, 180, 242).astype(np.uint8)
    paper[..., 3] = 255
    lbl_im = Image.fromarray(paper, mode="RGBA")
    ld = ImageDraw.Draw(lbl_im)

    # Classic 90s crimson-red + navy index header strip & thin blue ruled lines
    ld.rectangle([0, 0, lw - 1, 22], fill=(204, 42, 38, 255))
    ld.line([0, 23, lw - 1, 23], fill=(42, 68, 132, 255), width=2)
    ld.text((8, 4), "INDEX // 3.5\" MF-2HD  1.44MB", fill=(250, 246, 238, 255), font=_font(12, bold=True))

    for ry in (56, 92, 128, 158):
        ld.line([8, ry, lw - 9, ry], fill=(166, 184, 216, 220), width=1)

    # Crisp, bold permanent-marker 'LOL.BAT' on a rotated overlay so it looks genuinely hand-written with a Sharpie!
    txt_layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    f_big = _font(47, bold=True, mono=True)
    # Slight felt-tip bleed halo + deep rich blue-black Sharpie ink core
    td.text((11, 39), "LOL.BAT", fill=(28, 32, 54, 120), font=f_big, stroke_width=3, stroke_fill=(28, 32, 54, 110))
    td.text((10, 38), "LOL.BAT", fill=(14, 16, 26, 252), font=f_big, stroke_width=2, stroke_fill=(14, 16, 26, 252))
    # Hand-drawn Sharpie double underline + DOS command note below
    td.line([13, 96, lw - 18, 92], fill=(16, 18, 30, 245), width=4)
    td.line([22, 103, lw - 34, 100], fill=(196, 36, 32, 230), width=2)
    td.text((16, 112), "C:\\> NET SEND * LOL", fill=(26, 30, 46, 238), font=_font(15, bold=True, mono=True))
    td.text((18, 136), "\"WHERE'S THE DISK?!\"", fill=(92, 96, 112, 215), font=_font(12, bold=True, mono=False))

    txt_rot = txt_layer.rotate(2.2, resample=Image.BICUBIC, expand=False)
    lbl_im = Image.alpha_composite(lbl_im, txt_rot)

    # Rounded mask for sticker corners + subtle paper border
    mask_lbl = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(mask_lbl).rounded_rectangle([0, 0, lw - 1, lh - 1], radius=6, fill=255)
    ImageDraw.Draw(lbl_im).rounded_rectangle([0, 0, lw - 1, lh - 1], radius=6, outline=(178, 172, 156, 255), width=1)
    im.paste(lbl_im, (lx0, ly0), mask_lbl)

    # ==========================================================================
    # PANEL 2 [296..576, 4..284]: BACK SHELL + RADIAL BRUSHED STEEL SPINDLE HUB
    # ==========================================================================
    bx0, by0 = 296, 4
    dr.rectangle([bx0 + 1, by0 + 1, bx0 + S - 2, by0 + S - 2], outline=(94, 99, 110), width=2)
    # Wide rear shutter slide track
    dr.rectangle([bx0 + 38, by0, bx0 + 242, by0 + 92], fill=(32, 34, 40), outline=(20, 22, 26), width=2)

    # Recessed circular well around metal drive spindle chuck (center: bx0+140, by0+168)
    cx, cy = bx0 + 140, by0 + 168
    dr.ellipse([cx - 62, cy - 62, cx + 62, cy + 62], fill=(22, 24, 28), outline=(82, 87, 98), width=2)

    # Anisotropic radial-brushed stainless steel spindle hub disc (r = 52)
    HS = 112
    yy_h, xx_h = np.mgrid[0:HS, 0:HS].astype(np.float32)
    dx_h, dy_h = xx_h - (HS - 1) * 0.5, yy_h - (HS - 1) * 0.5
    rr_h = np.hypot(dx_h, dy_h)
    ang_h = np.arctan2(dy_h, dx_h)
    # Conical brushed metal anisotropy + fine circular lathe rings
    sheen = (
        0.66
        + 0.23 * np.cos(2.0 * ang_h - 0.85)
        + 0.08 * np.sin(4.0 * ang_h + 0.4)
        + 0.035 * np.sin(rr_h * 2.4)
    )
    hub_u8 = np.zeros((HS, HS, 4), dtype=np.uint8)
    hub_u8[..., 0] = np.clip(sheen * 232.0, 28, 252).astype(np.uint8)
    hub_u8[..., 1] = np.clip(sheen * 238.0, 30, 254).astype(np.uint8)
    hub_u8[..., 2] = np.clip(sheen * 248.0, 34, 255).astype(np.uint8)
    hub_u8[..., 3] = np.clip((52.5 - rr_h) * 255.0, 0, 255).astype(np.uint8)
    hub_im = Image.fromarray(hub_u8, mode="RGBA")
    hd = ImageDraw.Draw(hub_im)
    # Center square spindle hole + offset rectangular drive-pin slot (showing dark magnetic media inside)
    hd.rounded_rectangle([45, 45, 66, 66], radius=2, fill=(18, 20, 24, 255), outline=(124, 130, 142, 255), width=1)
    hd.rounded_rectangle([72, 48, 90, 63], radius=2, fill=(30, 22, 20, 255), outline=(124, 130, 142, 255), width=1)
    hd.ellipse([4, 4, HS - 5, HS - 5], outline=(245, 248, 255, 220), width=1)
    im.paste(hub_im, (cx - HS // 2, cy - HS // 2), hub_im)

    # Molded rear grip ribs & write-protect windows
    for ly_g in range(by0 + 238, by0 + 268, 6):
        dr.line([bx0 + 68, ly_g, bx0 + 212, ly_g], fill=(40, 43, 50), width=2)
        dr.line([bx0 + 68, ly_g + 2, bx0 + 212, ly_g + 2], fill=(74, 78, 88), width=1)
    dr.rectangle([bx0 + 10, by0 + 240, bx0 + 26, by0 + 264], fill=(16, 17, 20), outline=(82, 86, 96), width=1)
    dr.rectangle([bx0 + 254, by0 + 240, bx0 + 270, by0 + 264], fill=(12, 13, 16), outline=(82, 86, 96), width=1)

    # ==========================================================================
    # PANEL 3 [588..852, 4..284]: BRUSHED STAINLESS-STEEL SLIDING SHUTTER
    # ==========================================================================
    sx0, sy0, sw, sh = 588, 4, 264, 280
    ux = np.linspace(0.0, 1.0, sw, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 1.0, sh, dtype=np.float32)[:, None]
    brush = (
        0.70
        + 0.19 * np.sin(ux * math.pi * 2.3 - 0.35)
        + 0.07 * np.cos(ux * math.pi * 5.2)
        + 0.03 * np.sin(vy * 360.0)
        + 0.025 * grain_fine[:sh, :sw]
    )
    sh_u8 = np.zeros((sh, sw, 3), dtype=np.uint8)
    sh_u8[..., 0] = np.clip(brush * 232.0, 30, 252).astype(np.uint8)
    sh_u8[..., 1] = np.clip(brush * 238.0, 32, 254).astype(np.uint8)
    sh_u8[..., 2] = np.clip(brush * 250.0, 36, 255).astype(np.uint8)
    sh_im = Image.fromarray(sh_u8, mode="RGB")
    sd = ImageDraw.Draw(sh_im)
    sd.rectangle([1, 1, sw - 2, sh - 2], outline=(245, 248, 255), width=2)
    # Rectangular read/write window showing dark glossy magnetic Mylar platter + subtle diagonal sheen
    sd.rounded_rectangle([148, 32, 218, 246], radius=6, fill=(28, 22, 20), outline=(126, 132, 144), width=3)
    sd.line([156, 46, 210, 232], fill=(64, 48, 42), width=3)
    sd.line([164, 46, 214, 218], fill=(46, 36, 32), width=2)
    # Stamped rectangular depression bar on left side of metal shutter
    sd.rounded_rectangle([38, 44, 62, 234], radius=3, outline=(138, 145, 158), width=2)
    sd.line([41, 46, 41, 232], fill=(238, 242, 250), width=1)
    im.paste(sh_im, (sx0, sy0))

    # ==========================================================================
    # PANEL 4 [864..1020, 4..284]: BEVELED ABS PLASTIC RIM SWATCH
    # ==========================================================================
    rx0, ry0, rw, rh = 864, 4, 156, 280
    dr.rectangle([rx0, ry0, rx0 + rw - 1, ry0 + rh - 1], fill=(54, 57, 65))
    # Subtle center parting seam line of two-halves injection-molded floppy shell!
    mid_x = rx0 + rw // 2
    dr.line([mid_x - 1, ry0, mid_x - 1, ry0 + rh - 1], fill=(34, 36, 42), width=2)
    dr.line([mid_x + 1, ry0, mid_x + 1, ry0 + rh - 1], fill=(82, 86, 96), width=1)

    os.makedirs(os.path.dirname(out_strip_path), exist_ok=True)
    im.save(out_strip_path, "PNG", optimize=True)
    print(f"  [OK] High-DPI Floppy Strip  : {out_strip_path}")
    return out_strip_path


def compose_preview_sheets(render_dir):
    """Composes high-res inspection contact sheets from Blender's rendered frames."""
    fp_list = [
        ("vm_fp_00.png", "f00: Idle Hold (LOL.BAT + Realistic Thumb/Palm)"),
        ("vm_fp_10.png", "f10: Wrist Pronating (Turning Disk Over)"),
        ("vm_fp_15.png", "f15: Flipped 180 (Dorsal Hand, Knuckles, Nails & Hub)"),
        ("vm_fp_20.png", "f20: Smooth Wrist Supination Return"),
        ("vm_fp_28.png", "f28: Smug Tilt & Index-Finger Corner Tap"),
        ("vm_fp_39.png", "f39: Seamless Loop End (-> f00)"),
        ("vm_fp_42.png", "f42: Sidearm Frisbee Wrist-Cock Windup"),
        ("vm_fp_43.png", "f43: Explosive Forward Wrist-Snap Whip"),
        ("vm_fp_44.png", "f44: Release! (Disk Spawns, Splayed Follow-Through)"),
        ("vm_fp_50.png", "f50: Hand Recovery"),
        ("vm_fp_53.png", "f53: Poised Empty-Hand Ready Pose (Ammo Recharge)"),
        ("vm_fp_57.png", "f57: Pocket Snatch Reload -> Idle"),
    ]

    cw, ch = 480, 270
    cols, rows = 4, 3
    pad, hdr, lbl_h = 10, 42, 26
    W = pad + cols * (cw + pad)
    H = hdr + rows * (ch + lbl_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 16, 20))
    dr = ImageDraw.Draw(sheet)
    dr.text((pad + 4, 10), "progs/v_netsend.md3 — Remade Realistic Hand + LOL.BAT Disk (60f, Green Cross = Crosshair)", fill=(120, 240, 155), font=_font(18, bold=True))

    f_lbl = _font(13, bold=True)
    for idx, (fn, cap) in enumerate(fp_list):
        p = os.path.join(render_dir, fn)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize((cw, ch), Image.LANCZOS)
        # Draw subtle green crosshair at exact center of first-person frame
        imd = ImageDraw.Draw(im)
        cx, cy = cw // 2, ch // 2
        imd.line([cx - 5, cy, cx + 5, cy], fill=(70, 245, 90), width=1)
        imd.line([cx, cy - 5, cx, cy + 5], fill=(70, 245, 90), width=1)

        r, c = divmod(idx, cols)
        x = pad + c * (cw + pad)
        y = hdr + r * (ch + lbl_h + pad)
        sheet.paste(im, (x, y))
        dr.rectangle([x, y + ch, x + cw - 1, y + ch + lbl_h - 1], fill=(24, 28, 36))
        dr.text((x + 8, y + ch + 5), cap, fill=(228, 234, 244), font=f_lbl)

    out_fp_sheet = os.path.join(render_dir, "sheet_realhand_fp_frames.png")
    sheet.save(out_fp_sheet, "PNG")

    # 6-angle close-up turntable of the hand + floppy grip
    turn_list = [
        ("vm_closeup_0.png", "1st-Person POV Close-Up"),
        ("vm_closeup_1.png", "Radial / Thumb-Web & Thumbnail"),
        ("vm_closeup_2.png", "Dorsal Knuckles, Veins & Fingernails"),
        ("vm_closeup_3.png", "Rear Floppy Hub & Finger Cradle"),
        ("vm_closeup_4.png", "Palmar Creases & Thenar Eminence"),
        ("vm_closeup_5.png", "Flipped Frame 15 Dorsal Inspection"),
    ]
    tw, th = 480, 360
    tcols, trows = 3, 2
    TW = pad + tcols * (tw + pad)
    TH = hdr + trows * (th + lbl_h + pad) + pad
    tsheet = Image.new("RGB", (TW, TH), (14, 16, 20))
    tdr = ImageDraw.Draw(tsheet)
    tdr.text((pad + 4, 10), "progs/v_netsend.md3 — Anatomical Realistic Hand & Grip Inspection", fill=(120, 220, 255), font=_font(18, bold=True))
    for idx, (fn, cap) in enumerate(turn_list):
        p = os.path.join(render_dir, fn)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        r, c = divmod(idx, tcols)
        x = pad + c * (tw + pad)
        y = hdr + r * (th + lbl_h + pad)
        tsheet.paste(im, (x, y))
        tdr.rectangle([x, y + th, x + tw - 1, y + th + lbl_h - 1], fill=(24, 28, 36))
        tdr.text((x + 8, y + th + 5), cap, fill=(228, 234, 244), font=f_lbl)

    out_turn_sheet = os.path.join(render_dir, "sheet_realhand_closeup.png")
    tsheet.save(out_turn_sheet, "PNG")
    print(f"  [OK] Contact sheets saved   :\n       {out_fp_sheet}\n       {out_turn_sheet}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS, exist_ok=True)

    strip_path = os.path.join(OUT_DIR, "floppy_strip_srgb.png")
    print("[1/4] Building photorealistic 3.5\" 'LOL.BAT' floppy disk strip...")
    build_floppy_strip_srgb(strip_path)

    blender_script = os.path.join(HERE, "blender_sculpt_netsend_hand.py")
    raw_npz = os.path.join(OUT_DIR, "v_netsend_raw.npz")
    atlas_srgb = os.path.join(OUT_DIR, "netsend_hand_srgb.png")
    atlas_dp = os.path.join(OUT_DIR, "netsend_hand_dp.png")

    print("[2/4] Launching Blender 5.2 to sculpt anatomical hand, bake Cycles SSS/AO, animate 60 frames & render previews...")
    cmd = [
        BLENDER_EXE,
        "--background",
        "--python-exit-code", "1",
        "--python", blender_script,
        "--",
        strip_path,
        OUT_DIR,
        raw_npz,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr.strip():
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        raise SystemExit(f"Blender failed with exit code {res.returncode}")

    print("[3/4] Writing single-surface MD3 (`progs/v_netsend.md3`) and installing `progs/netsend_hand.png`...")
    data = np.load(raw_npz)
    all_v = data["verts"]        # (60, NV, 3)
    all_n = data["norms"]        # (60, NV, 3)
    st_arr = data["st"]          # (NV, 2)
    tris_arr = data["tris"]      # (NT, 3)
    fnames = [str(x) for x in data["frame_names"]]

    nf, nv, _ = all_v.shape
    nt = len(tris_arr)
    assert nf == 60, f"Expected 60 frames, got {nf}"
    assert nv <= 4096, f"Vertex count {nv} exceeds MD3 4096 limit"
    assert nt <= 3000, f"Triangle count {nt} exceeds 3000 budget"
    assert np.all(np.isfinite(all_v)) and np.all(np.isfinite(all_n))
    assert np.max(np.abs(all_v)) < 500.0

    frames_list = []
    for fi in range(nf):
        vv = [tuple(map(float, p)) for p in all_v[fi]]
        nn = [tuple(map(float, n)) for n in all_n[fi]]
        frames_list.append((vv, nn))

    surf = dict(
        name="netsend_hand",
        shader="progs/netsend_hand",
        tris=[tuple(map(int, t)) for t in tris_arr],
        st=[tuple(map(float, uv)) for uv in st_arr],
        frames=frames_list,
    )
    model_dict = dict(name="v_netsend", surfaces=[surf], nframes=60, frame_names=fnames)

    out_md3_preview = os.path.join(OUT_DIR, "v_netsend.md3")
    md3lib.write(out_md3_preview, model_dict)

    if os.path.isdir(STAGED_PROGS):
        shutil.copy2(out_md3_preview, os.path.join(STAGED_PROGS, "v_netsend.md3"))
        shutil.copy2(atlas_dp, os.path.join(STAGED_PROGS, "netsend_hand.png"))
        print(f"  [STAGED] Installed into {STAGED_PROGS} (no loose duplicates in {PROGS})")
    else:
        os.makedirs(PROGS, exist_ok=True)
        shutil.copy2(out_md3_preview, os.path.join(PROGS, "v_netsend.md3"))
        shutil.copy2(atlas_dp, os.path.join(PROGS, "netsend_hand.png"))

    f0_min = all_v[0].min(axis=0)
    f0_max = all_v[0].max(axis=0)
    print(
        f"  [OK] progs/v_netsend.md3    : 1 surface, {nv} verts, {nt} tris, {nf} frames | "
        f"f0 bounds ({f0_min[0]:.1f},{f0_min[1]:.1f},{f0_min[2]:.1f})..({f0_max[0]:.1f},{f0_max[1]:.1f},{f0_max[2]:.1f})"
    )

    print("[4/4] Composing inspection contact sheets...")
    compose_preview_sheets(OUT_DIR)
    print("Done! Ready for visual & in-game DarkPlaces verification.")


if __name__ == "__main__":
    main()
