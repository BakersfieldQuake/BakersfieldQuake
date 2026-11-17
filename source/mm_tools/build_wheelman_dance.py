"""Update progs/wheelman_dance.spr32 to IDSP v32 type 2 (SPR_VP_PARALLEL) while preserving
all existing 0..399 frames intact (for wcannon.qc, crowd_npcs.qc, intro_director*.qc) and
appending 8-dir x 6-frame above45 (400..447) and above90 (448..495) overhead dance tiers
with centered origins (ox = -w//2, oy = h//2).

python3.13 source/mm_tools/build_wheelman_dance.py
"""
import math
import os
import struct
import sys
import cv2
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
ACT_DIR = os.path.join(HERE, "wheelman_actions")
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if ACT_DIR not in sys.path:
    sys.path.insert(0, ACT_DIR)

import wheelman_actions_core as core
import build_wheelman_sprite as bw

PROGS_DST = os.path.join(MOD_DIR, "progs", "wheelman_dance.spr32")
STAGED_DST = os.path.abspath(os.path.join(MOD_DIR, "..", "_bakersfield_dev", "staged_assets", "progs", "wheelman_dance.spr32"))
OUT_DIR = os.path.join(HERE, "out", "wheelman_dance")
N = 80
CANVAS_HI = 360
BASE_FRAMES_COUNT = 400


def read_existing_base_frames(path, count=BASE_FRAMES_COUNT):
    """Reads the existing 0..399 tight-cropped frames verbatim so indices/origins never shift."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"IDSP":
        raise RuntimeError(f"Not an IDSP sprite: {path}")
    ver, stype, rad, mw, mh, nf, bl, st = struct.unpack("<iifiiifi", data[4:36])
    if ver != 32 or nf < count:
        raise RuntimeError(f"Unexpected wheelman_dance.spr32 header ver={ver}, nf={nf} in {path}")
    frames = []
    off = 36
    for i in range(count):
        ft, ox, oy, cw, ch = struct.unpack_from("<iiiii", data, off)
        off += 20
        nbytes = cw * ch * 4
        raw = data[off:off + nbytes]
        off += nbytes
        frames.append((ox, oy, cw, ch, raw))
    return frames


def clean_dance_overhead_plate(img_path, flange_y0, skin_samples):
    """Keys #FF00FF studio magenta, diffuses black athletic shorts to bare skin while keeping
    chrome cylinder, steel axle, and black tires intact, and calibrates skin tone."""
    orig = core.key_studio_magenta(Image.open(img_path))
    arr = np.array(orig).astype(np.float32)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ys, xs = np.nonzero(arr[..., 3] > 24)
    bx0, bx1 = float(xs.min()), float(xs.max())
    by0, by1 = float(ys.min()), float(ys.max())
    bw_p, bh_p = max(1.0, bx1 - bx0), max(1.0, by1 - by0)
    ll = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    rbb = arr[..., 0] - arr[..., 2]

    mech_wheels = (xx < bx0 + 0.24 * bw_p) | (xx > bx0 + 0.76 * bw_p)
    mech_flange = (
        (xx >= bx0 + 0.44 * bw_p) & (xx <= bx0 + 0.55 * bw_p)
        & (yy >= by0 + flange_y0 * bh_p) & (yy <= by0 + 0.82 * bh_p)
    )
    mech_axle = (yy >= by0 + 0.56 * bh_p) & (yy <= by0 + 0.63 * bh_p) & (ll > 92.0) & (rbb < 16.0)
    mech = mech_wheels | mech_flange | mech_axle

    in_roi = (
        (xx >= bx0 + 0.28 * bw_p) & (xx <= bx0 + 0.74 * bw_p)
        & (yy >= by0 + 0.44 * bh_p) & (yy <= by0 + 0.72 * bh_p)
    )
    dark_sh = in_roi & (arr[..., 3] > 30) & (~mech) & (rbb < 20.0) & (ll < 112.0)
    dark_sh = ndimage.binary_dilation(dark_sh, iterations=3) & (~mech) & (arr[..., 3] > 20)

    gx0 = max(0, int(bx0 + 0.44 * bw_p))
    gy0 = max(0, int(by0 + 0.36 * bh_p))
    gx1 = min(w, int(bx0 + 0.56 * bw_p))
    gy1 = min(h, int(by0 + 0.45 * bh_p))
    cleaned = bw.inpaint_region_with_surrounding_skin(orig, dark_sh, grain_src_box=(gx0, gy0, gx1, gy1))
    c_arr = np.array(cleaned)
    c_arr[mech] = np.array(orig)[mech]
    cleaned = Image.fromarray(c_arr, "RGBA")
    return core.calibrate_skin_to_ref(cleaned, skin_samples, strength=0.55)


def center_on_square_canvas(im_rgba, size=CANVAS_HI, max_span=280.0):
    arr = np.array(im_rgba)
    ys, xs = np.nonzero(arr[..., 3] > 24)
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    sw, sh = max(1.0, x1 - x0), max(1.0, y1 - y0)
    scale = min(max_span / sw, max_span / sh)
    rw, rh = max(2, int(round(im_rgba.width * scale))), max(2, int(round(im_rgba.height * scale)))
    rsz = im_rgba.resize((rw, rh), Image.LANCZOS)
    cx_src, cy_src = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    ox = int(round(size * 0.5 - cx_src * scale))
    oy = int(round(size * 0.5 - cy_src * scale))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(rsz, (ox, oy), rsz)
    return out


def animate_overhead_dance_6(norm_im, is_above90=False):
    """Synthesizes 6 lively disco-dance frames (k = 0..5) alternating left/right arm sky-points,
    hip thrusts, wheel-bar wagging, and knee kicks from the overhead plate."""
    arr_a = np.array(norm_im)
    arr_b = np.array(ImageOps.mirror(norm_im))
    H, W = arr_a.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.5, H * 0.5

    out_frames = []
    for k in range(6):
        ph = k / 6.0
        t = 2.0 * math.pi * ph
        src = arr_a if k < 3 else arr_b

        # Funky 2-beat bounce + hip sway
        hip_sway = 7.5 * math.sin(2.0 * t) * np.exp(-((yg - (cy + 10.0)) / 62.0) ** 2)
        bob_y = -6.0 * abs(math.sin(2.0 * t)) * np.clip((H - 28.0 - yg) / 40.0, 0.0, 1.0)

        # Stuck metal bar & dual wheels wag rhythmically around hips
        rig_zone = np.exp(-((yg - (cy + 20.0)) / 48.0) ** 2) * ((np.abs(xg - cx) > 36.0) | (np.abs(yg - (cy + 24.0)) < 22.0))
        wag_ang = math.radians(7.5 * math.sin(2.0 * t - 0.35))
        cw_a, sw_a = math.cos(-wag_ang), math.sin(-wag_ang)
        dx_wag = (cx + (xg - cx) * cw_a - (yg - (cy + 20.0)) * sw_a - xg) * rig_zone
        dy_wag = ((cy + 20.0) + (xg - cx) * sw_a + (yg - (cy + 20.0)) * cw_a - yg) * rig_zone

        # Disco sky-point arm pump (upper quadrant)
        arm_w = np.clip((cy - 20.0 - yg) / 36.0, 0.0, 1.0)
        dx_arm = 5.5 * math.cos(2.0 * t) * arm_w
        dy_arm = -7.5 * (0.5 + 0.5 * math.sin(4.0 * t)) * arm_w

        # Jigging lower legs / raised knee
        leg_w = np.clip((yg - (cy + 25.0)) / 32.0, 0.0, 1.0)
        dy_leg = -6.5 * math.sin(4.0 * t) * leg_w

        mx = (xg - (hip_sway + dx_wag + dx_arm)).astype(np.float32)
        my = (yg - (bob_y + dy_wag + dy_arm + dy_leg)).astype(np.float32)
        warped = core.premul_remap(src, mx, my)

        # Tire tread pulse on outer left/right wheels
        rf = warped.astype(np.float32)
        pa = rf[..., 3] > 80
        lum = rf[..., :3].mean(axis=2)
        is_tire = pa & ((xg < 110.0) | (xg > W - 110.0)) & (lum < 80.0)
        wave = np.sin(9.0 * (yg - cy) / 48.0 - math.sin(2.0 * t) * math.pi) * 11.0 * is_tire
        rf[..., :3] = np.clip(rf[..., :3] + wave[..., None], 0.0, 255.0)
        out_frames.append(Image.fromarray(rf.astype(np.uint8), "RGBA"))
    return out_frames


def resize_premul_80(im_rgba):
    arr = np.asarray(im_rgba.convert("RGBA"), dtype=np.float32)
    a = arr[..., 3:4] / 255.0
    pre = np.concatenate([arr[..., :3] * a, arr[..., 3:4]], axis=-1)
    res = cv2.resize(pre, (N, N), interpolation=cv2.INTER_AREA)
    a_out = np.clip(res[..., 3:4], 0.0, 255.0)
    denom = np.maximum(a_out / 255.0, 1e-4)
    rgb_out = np.where(a_out >= 1.0, np.clip(res[..., :3] / denom, 0.0, 255.0), 0.0)
    a_clean = np.where(a_out < 6.0, 0.0, a_out)
    rgba = np.concatenate([np.round(rgb_out), np.round(a_clean)], axis=-1).astype(np.uint8)
    rgb_im = Image.fromarray(rgba[..., :3], "RGB").filter(ImageFilter.UnsharpMask(radius=0.85, percent=26, threshold=2))
    return np.dstack([np.asarray(rgb_im, dtype=np.uint8), rgba[..., 3]])


def pack_centered_frame(rgba80):
    fox, foy, cw, ch, raw = bw._tight_crop_and_bleed_rgba(rgba80, -(N // 2), N // 2)
    return -(cw // 2), ch // 2, cw, ch, raw


def write_packed_spr32(paths, packed_frames, sprite_type=2):
    max_cw = max(f[2] for f in packed_frames)
    max_ch = max(f[3] for f in packed_frames)
    rad = 0.5 * math.hypot(max_cw, max_ch)
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, sprite_type, rad, max_cw, max_ch, len(packed_frames), 0.0, 0))
    for ox, oy, cw, ch, raw in packed_frames:
        buf += struct.pack("<iiiii", 0, ox, oy, cw, ch) + raw
    for dst in paths:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(buf)
        os.replace(tmp, dst)
        print(f"wrote {dst} ({len(packed_frames)} frames, type={sprite_type}, max={max_cw}x{max_ch}, {len(buf)/1048576:.2f} MiB)")


def main():
    skin_samples, _ = core.load_authentic_skin_ref()

    base_frames = read_existing_base_frames(PROGS_DST, count=BASE_FRAMES_COUNT)
    print(f"Loaded {len(base_frames)} existing base frames (0..{len(base_frames)-1}) intact from {PROGS_DST}")

    p45 = os.path.join(ACT_DIR, "ref", "dance_above_45.jpg")
    p90 = os.path.join(ACT_DIR, "ref", "dance_above_90.jpg")
    clean45 = clean_dance_overhead_plate(p45, 0.625, skin_samples)
    clean90 = clean_dance_overhead_plate(p90, 0.605, skin_samples)

    norm45 = center_on_square_canvas(clean45, CANVAS_HI, max_span=292.0)
    norm90 = center_on_square_canvas(clean90, CANVAS_HI, max_span=268.0)

    anim45_6 = animate_overhead_dance_6(norm45, is_above90=False)
    anim90_6 = animate_overhead_dance_6(norm90, is_above90=True)

    # Build 8-dir x 6-frame above90 (448..495) via -d*45 Z-rotation
    above90_8dir = []
    for d in range(8):
        above90_8dir.append([fr.rotate(-d * 45.0, resample=Image.BICUBIC, expand=False) for fr in anim90_6])

    # Build 8-dir x 6-frame above45 (400..447):
    #   d=0 (front): dance_above_45
    #   d=1 (front-left): dance_above_45 rotated -38 deg; d=7 mirrored
    #   d=2..6 (sides & back): dance_above_90 rotated -d*45 deg (so back/sides show top of head & hair, never upside-down face!)
    above45_8dir = [None] * 8
    above45_8dir[0] = anim45_6
    above45_8dir[1] = [fr.rotate(-38.0, resample=Image.BICUBIC, expand=False) for fr in anim45_6]
    above45_8dir[7] = [ImageOps.mirror(fr) for fr in above45_8dir[1]]
    for d in (2, 3, 4, 5, 6):
        above45_8dir[d] = above90_8dir[d]

    packed_all = list(base_frames)
    preview_a45 = []
    preview_a90 = []
    for d in range(8):
        row = []
        for k in range(6):
            toned = core.tone_for_darkplaces(above45_8dir[d][k])
            arr80 = resize_premul_80(toned)
            row.append(Image.fromarray(arr80, "RGBA"))
            packed_all.append(pack_centered_frame(arr80))
        preview_a45.append(row)

    for d in range(8):
        row = []
        for k in range(6):
            toned = core.tone_for_darkplaces(above90_8dir[d][k])
            arr80 = resize_premul_80(toned)
            row.append(Image.fromarray(arr80, "RGBA"))
            packed_all.append(pack_centered_frame(arr80))
        preview_a90.append(row)

    assert len(packed_all) == 496, f"Expected 496 frames, got {len(packed_all)}"

    targets = [PROGS_DST]
    if os.path.isdir(os.path.dirname(STAGED_DST)):
        targets.append(STAGED_DST)
    write_packed_spr32(targets, packed_all, sprite_type=2)

    # Save audit contact sheet
    os.makedirs(OUT_DIR, exist_ok=True)
    cw_a, ch_a = 96, 96
    sheet = Image.new("RGB", (cw_a * 8, ch_a * 12), (26, 29, 36))
    dr = ImageDraw.Draw(sheet)
    for blk_i, (lbl, grid) in enumerate([("a45", preview_a45), ("a90", preview_a90)]):
        for d in range(8):
            for k in range(6):
                r = blk_i * 6 + k
                tile = Image.new("RGBA", (cw_a, ch_a), (30 + 4 * ((r + d) % 2), 33, 40, 255))
                im = grid[d][k]
                tile.alpha_composite(im, ((cw_a - im.width) // 2, (ch_a - im.height) // 2))
                sheet.paste(tile.convert("RGB"), (d * cw_a, r * ch_a))
                dr.text((d * cw_a + 3, r * ch_a + 2), f"{lbl} d{d}k{k}", fill=(120, 240, 180))
    sheet_path = os.path.join(OUT_DIR, "audit_overhead_dance.png")
    sheet.save(sheet_path)
    print(f"wrote {sheet_path}")


if __name__ == "__main__":
    main()
