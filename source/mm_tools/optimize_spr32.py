"""Losslessly tight-crop transparent (alpha == 0) borders on all progs/*.spr32 sprites
(preserving a 1px transparent border for GL_LINEAR + GL_CLAMP_TO_EDGE filtering and adjusting
per-frame origin_x / origin_y so every pixel renders at the exact same world coordinate),
and strip the 48 disabled tail jetpack frames (744..791) from wheelman.spr32.

Originals are backed up in G:\\Quake\\Combat\\_bakersfield_dev\\orig_spr32\\.
"""
import glob
import math
import os
import shutil
import struct
from PIL import Image

ROOT = r"G:\Quake\Combat"
MOD = os.path.join(ROOT, "BakersfieldQuake")
PROGS = os.path.join(MOD, "progs")
BACKUP_DIR = os.path.join(ROOT, "_bakersfield_dev", "orig_spr32")


def optimize_spr32_file(path: str, backup_path: str, max_frames=None):
    if (not os.path.isfile(backup_path)) or (
        os.path.getmtime(path) > os.path.getmtime(backup_path) + 2.0
        and os.path.getsize(path) > os.path.getsize(backup_path)
    ):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(path, backup_path)

    data = open(backup_path, "rb").read()
    ident = data[:4]
    if ident != b"IDSP":
        print(f"Skipping non-IDSP file: {path}")
        return 0, 0
    ver, stype, radius, maxw, maxh, nframes, beamlen, synctype = struct.unpack("<iifiiifi", data[4:36])
    if ver != 32:
        print(f"Skipping non-spr32 (ver={ver}): {path}")
        return 0, 0

    off = 36
    frames = []
    limit = min(nframes, max_frames) if max_frames is not None else nframes
    new_maxw = 1
    new_maxh = 1

    for fi in range(nframes):
        ftype = struct.unpack_from("<i", data, off)[0]
        off += 4
        if ftype != 0:
            raise RuntimeError(f"Frame group (ftype={ftype}) not expected in {path}")
        ox, oy, w, h = struct.unpack_from("<iiii", data, off)
        off += 16
        px_bytes = w * h * 4
        raw = data[off:off + px_bytes]
        off += px_bytes
        if fi >= limit:
            continue

        im = Image.frombytes("RGBA", (w, h), raw)
        alpha = im.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            # Completely empty frame -> 1x1 transparent pixel
            x0, y0, x1, y1 = 0, 0, 1, 1
        else:
            # Preserve 1px alpha=0 border where available in original frame for GL_CLAMP_TO_EDGE
            x0 = max(0, bbox[0] - 1)
            y0 = max(0, bbox[1] - 1)
            x1 = min(w, bbox[2] + 1)
            y1 = min(h, bbox[3] + 1)

        cropped = im.crop((x0, y0, x1, y1))
        cw, ch = x1 - x0, y1 - y0
        new_ox = ox + x0
        new_oy = oy - y0
        new_maxw = max(new_maxw, cw)
        new_maxh = max(new_maxh, ch)
        frames.append((new_ox, new_oy, cw, ch, cropped.tobytes()))

    out = bytearray(b"IDSP")
    out += struct.pack("<iifiiifi", ver, stype, radius, new_maxw, new_maxh, len(frames), beamlen, synctype)
    for ox, oy, cw, ch, cbytes in frames:
        out += struct.pack("<iiiii", 0, ox, oy, cw, ch)
        out += cbytes

    open(path, "wb").write(out)
    return len(data), len(out)


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    tot_before = 0
    tot_after = 0
    for p in sorted(glob.glob(os.path.join(PROGS, "*.spr32"))):
        name = os.path.basename(p)
        bpath = os.path.join(BACKUP_DIR, name)
        # Strip disabled tail jetpack frames 744..791 on wheelman.spr32
        max_f = 744 if name.lower() == "wheelman.spr32" else None
        b_sz, a_sz = optimize_spr32_file(p, bpath, max_frames=max_f)
        if b_sz > 0:
            tot_before += b_sz
            tot_after += a_sz
            pct = (1.0 - a_sz / b_sz) * 100.0
            print(f"  {name:24s}: {b_sz/1048576:7.2f} MB -> {a_sz/1048576:7.2f} MB  (-{pct:4.1f}%)")
    print(f"TOTAL .spr32: {tot_before/1048576:.2f} MB -> {tot_after/1048576:.2f} MB (-{(1.0 - tot_after/tot_before)*100.0:.1f}%)")


if __name__ == "__main__":
    main()
