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
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

SRC = r"G:\Quake\Combat\BakersfieldQuake\quake_6chars_sprites"
DST = r"G:\Quake\Combat\BakersfieldQuake\progs"
SCALE = 0.30
TARGET_LUM = 62.0
PIVOT = (256, 464)
UNITS_TALL = 52.0
WALK_COLS, RUN_COLS = 24, 20


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

        walk = load_cells(os.path.join(cdir, "walk_sheet.png"), WALK_COLS, box, list(range(0, 24, 2)))
        run = load_cells(os.path.join(cdir, "run_sheet.png"), RUN_COLS, box, list(range(0, 20, 2)))

        frames = []
        for d in range(8):
            frames.append(walk[(d, 0)])
        for d in range(8):
            for k in range(12):
                frames.append(walk[(d, k)])
        for d in range(8):
            for k in range(10):
                frames.append(run[(d, k)])

        small = []
        for im in frames:
            im = im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")
            small.append(np.array(im, dtype=np.float32))

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
        print(f"  front view {cell_height:.0f}px tall -> entity scale {scale:.3f}", flush=True)
        info[ch] = {"w": w, "h": h, "height_px": cell_height, "scale": round(scale, 3), "frames": len(small), "gain": round(gain, 3)}

        path = os.path.join(DST, f"crowd_c{ch}.spr32")
        rad = math.sqrt((w / 2.0) ** 2 + (h / 2.0) ** 2)
        with open(path, "wb") as fp:
            fp.write(b"IDSP")
            fp.write(struct.pack("<iifiiifi", 32, 0, rad, w, h, len(small), 0.0, 0))
            for a in small:
                a = a.copy()
                a[..., :3] = np.clip(a[..., :3] * gain, 0, 255)
                fp.write(struct.pack("<iiiii", 0, int(round(-px)), int(round(py)), w, h))
                fp.write(a.astype(np.uint8).tobytes())
        print(f"  wrote {path}: {os.path.getsize(path):,} bytes", flush=True)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crowd_sprites_info.json")
    old = {}
    if os.path.exists(out):
        old = json.load(open(out))
    old.update({str(k): v for k, v in info.items()})
    json.dump(old, open(out, "w"), indent=1)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or None)
