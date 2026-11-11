"""Build progs/crowd_c1.spr32 .. crowd_c7.spr32 (the street crowd of crowd_npcs.qc) from the 512x512 HD 16-angle sheets in
quake_6chars_sprites/character_N (walk 24f, run 20f). Each sprite keeps 8 of the 16 angles (every 45 degrees, source row 2 * d),
half the walk (12 frames) and half the run (10 frames), cropped to the character and scaled by SCALE:

  0..7                idle (walk frame 0)        d = 0..7
  8 + d * 12 + k      walk, k = 0..11 (source walk frames 0, 2, .. 22)
  104 + d * 10 + k    run,  k = 0..9  (source run frames 0, 2, .. 18)

d = 0 is the character facing the viewer, d = 2 the viewer at its left (source angle 90 deg: the character walks toward the left
of the picture), the same convention as every other sprite of the mod (daniel.qc, mbox.qc).
The ground pivot (256, 464) of the sheets becomes the sprite origin, so the feet are at the entity origin.
RGB is scaled so the mean opaque brightness is TARGET_LUM (the other sprites sit at 59-65 under the 2.5x scene brightness).
Prints the in-game scale that makes each character 52 units tall.

python3.13 build_crowd_sprites.py     (the WindowsApps Python 3.13, without -I: it has PIL and numpy)"""
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None

SRC = r"G:\Quake\Combat\BakersfieldQuake\quake_6chars_sprites"
DST = r"G:\Quake\Combat\BakersfieldQuake\progs"
STAGED_DST = r"G:\Quake\Combat\_bakersfield_dev\staged_assets\progs"
SCALE = 0.21
TARGET_LUM = 62.0
PIVOT = (256, 464)
UNITS_TALL = 52.0
WALK_COLS, RUN_COLS = 24, 20


def tight_crop_and_bleed(rgba: np.ndarray, ox: int, oy: int):
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
    return int(ox + x0), int(oy - y0), cw, ch, cropped.tobytes()


def load_cells(path, cols, box, picks):
    """{(d, k): premultiplied cropped RGBa image} for the 8 angles d and the source columns in picks."""
    sheet = Image.open(path).convert("RGBA")
    out = {}
    for d in range(8):
        for k, col in enumerate(picks):
            x, y = col * 512, d * 2 * 512
            out[(d, k)] = sheet.crop((x + box[0], y + box[1], x + box[2], y + box[3]))
    sheet.close()
    return out


def main(only=None):
    info = {}
    for ch in range(1, 8):
        if only and ch not in only:
            continue
        cdir = os.path.join(SRC, f"character_{ch}")
        meta = json.load(open(os.path.join(cdir, "hd_viewer_meta.json")))
        x0 = min(meta[a]["crop_x"] for a in ("walk", "run"))
        y0 = min(meta[a]["crop_y"] for a in ("walk", "run"))
        x1 = max(meta[a]["crop_x"] + meta[a]["crop_w"] for a in ("walk", "run"))
        y1 = max(meta[a]["crop_y"] + meta[a]["crop_h"] for a in ("walk", "run"))
        x0, y0, x1, y1 = max(0, x0 - 4), max(0, y0 - 4), min(512, x1 + 4), min(512, y1 + 4)
        box = (x0, y0, x1, y1)
        w, h = int(math.ceil((x1 - x0) * SCALE)), int(math.ceil((y1 - y0) * SCALE))
        px, py = (PIVOT[0] - x0) * SCALE, (PIVOT[1] - y0) * SCALE
        print(f"character_{ch}: crop {box} -> {w}x{h}, pivot ({px:.1f}, {py:.1f})", flush=True)

        walk = load_cells(os.path.join(cdir, "walk_sheet.png"), WALK_COLS, box, list(range(0, 24, 4)))
        run = load_cells(os.path.join(cdir, "run_sheet.png"), RUN_COLS, box, list(range(0, 20, 4)))

        frames = []
        for d in range(8):
            frames.append(walk[(d, 0)])
        for d in range(8):
            for k in range(6):
                frames.append(walk[(d, k)])
        for d in range(8):
            for k in range(5):
                frames.append(run[(d, k)])

        small = []
        for im in frames:
            im = im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")
            rgb_s = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=0.85, percent=32, threshold=2))
            rgb_s.putalpha(im.getchannel("A"))
            small.append(np.array(rgb_s, dtype=np.float32))

        # brightness: mean luminance of the opaque pixels over the whole set
        lum_sum, lum_n = 0.0, 0.0
        for a in small:
            m = a[..., 3] > 200
            if m.any():
                rgb = a[..., :3][m]
                lum_sum += float((rgb[:, 0] * 0.299 + rgb[:, 1] * 0.587 + rgb[:, 2] * 0.114).sum())
                lum_n += rgb.shape[0]
        mean_lum = lum_sum / max(1.0, lum_n)
        gain = min(1.5, max(0.5, TARGET_LUM / mean_lum))   # dark clothes (the black hoodie) stay dark
        print(f"  mean opaque lum {mean_lum:.1f} -> gain {gain:.3f}", flush=True)

        # character height in the cell (front view, standing frame): ground row py minus the top of the opaque pixels
        a0 = small[0]
        rows = np.where((a0[..., 3] > 128).any(axis=1))[0]
        top = int(rows.min()) if rows.size else 0
        cell_height = py - top
        scale = UNITS_TALL / cell_height
        print(f"  front view {cell_height:.1f}px tall -> entity scale {scale:.4f}", flush=True)
        info[ch] = {"w": w, "h": h, "height_px": round(cell_height, 2), "scale": round(scale, 4), "frames": len(small), "gain": round(gain, 3)}

        path = os.path.join(DST, f"crowd_c{ch}.spr32")
        base_ox, base_oy = int(round(-px)), int(round(py))
        packed = []
        max_cw, max_ch = 1, 1
        for a in small:
            a = a.copy()
            a[..., :3] = np.clip(np.round(a[..., :3] * gain), 0, 255)
            fox, foy, cw, ch_f, raw = tight_crop_and_bleed(a.astype(np.uint8), base_ox, base_oy)
            max_cw = max(max_cw, cw)
            max_ch = max(max_ch, ch_f)
            packed.append((fox, foy, cw, ch_f, raw))
        rad = math.sqrt((max_cw / 2.0) ** 2 + (max_ch / 2.0) ** 2)
        buf = bytearray(b"IDSP")
        buf += struct.pack("<iifiiifi", 32, 0, rad, max_cw, max_ch, len(packed), 0.0, 0)
        for fox, foy, cw, ch_f, raw in packed:
            buf += struct.pack("<iiiii", 0, fox, foy, cw, ch_f)
            buf += raw
        write_targets = [path]
        if os.path.isdir(os.path.dirname(STAGED_DST)):
            write_targets.append(os.path.join(STAGED_DST, f"crowd_c{ch}.spr32"))
        for wp in write_targets:
            os.makedirs(os.path.dirname(wp), exist_ok=True)
            with open(wp, "wb") as fp:
                fp.write(buf)
        print(f"  wrote {path}: {len(buf):,} bytes ({len(buf)/1048576:.2f} MiB)", flush=True)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crowd_sprites_info.json")
    old = {}
    if os.path.exists(out):
        old = json.load(open(out))
    old.update({str(k): v for k, v in info.items()})
    json.dump(old, open(out, "w"), indent=1)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or None)
