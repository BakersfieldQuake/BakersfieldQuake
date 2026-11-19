"""Build the 3D Spinning Horizontal Superman-Torpedo Kyle model (progs/kyle_torpedo.md3)
+ real studio Superman-flying textures (progs/kyle_torp_belly.png, kyle_torp_back.png,
kyle_torp_side.png) + animated 3D giant chrome barber scissors snapping straight out in front!

Sources (100% genuine horizontal Superman-flying Kyle — ZERO rotated standing poses!):
  - Side profile (kyle_torp_side.png): Real Grok studio Superman-flying Kyle (f_051.png,
    horizontal stomach-down, arched chest, head lifted smiling straight ahead, arms outstretched,
    legs stretched straight back!)
  - Top-down back (kyle_torp_back.png): Real Grok studio top-down horizontal Superman Kyle
    (f_164.png, straight above his back & outstretched arms!)
  - Bottom-up belly (kyle_torp_belly.png): Brand-new studio Superman belly-underneath photo
    (or Grok 3/4 front-stomach Superman f_015.png before belly sheet is generated).
  - Nose (+X): REAL 3D giant chrome barber scissors snapping vigorously 32 deg <-> 3 deg
    across 8 frames right out in front of Kyle's outstretched fists!

In-game (kyle.qc KY_MODE_HOMING):
  - Launches when locked onto a Winged John Bird (or sky vehicle within hairspray range <= 780u).
  - Cruises at bird_speed + 85 u/s (just slightly faster than the bird!).
  - Slowly spins flat in a 360-degree circle (~205 deg/s, ~1.75s per full slow turn) laying on
    his stomach chopping his giant chrome scissors as he hunts down the bird!

Run:
    python -I source/mm_tools/kyle_scissors/build_torpedo_md3.py
"""

import glob
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(HERE))
import md3lib
import build_scissors_md3 as scis_mod

ARTIFACT_ROOT = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671")
INSPO_FRAMES_DIR = ARTIFACT_ROOT / "scratch" / "inspo_frames"
OUT_MODEL_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "models"


def bleed_rgb_edges(rgba: np.ndarray, passes: int = 4) -> np.ndarray:
    out = rgba.copy()
    mask = out[..., 3] >= 24
    if not np.any(mask):
        return out
    rgb = out[..., :3].astype(np.float32)
    valid = mask.astype(np.float32)
    k = np.ones((3, 3), np.float32)
    for _ in range(passes):
        w_sum = cv2.filter2D(valid, -1, k, borderType=cv2.BORDER_REPLICATE)
        need = (valid < 0.5) & (w_sum > 0.5)
        if not np.any(need):
            break
        for c in range(3):
            c_sum = cv2.filter2D(rgb[..., c] * valid, -1, k, borderType=cv2.BORDER_REPLICATE)
            rgb[..., c][need] = c_sum[need] / w_sum[need]
        valid[need] = 1.0
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    return out


def key_pure_white(path: Path, remove_holes: bool = True) -> np.ndarray:
    """Cleanly key pure #FFFFFF studio frames (with enclosed white-hole removal between arms
    and inside scissor handles, plus white-fringe decontamination)."""
    bgr = cv2.imread(str(path))
    if bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    dist = np.sqrt(np.sum((255.0 - rgb) ** 2, axis=2))

    # Border flood-fill for outer pure white background
    cand = (dist < 28.0).astype(np.uint8)
    ff = np.zeros((h + 2, w + 2), np.uint8)
    mask = cand.copy()
    for x in range(w):
        if mask[0, x] == 1:
            cv2.floodFill(mask, ff, (x, 0), 2)
        if mask[h - 1, x] == 1:
            cv2.floodFill(mask, ff, (x, h - 1), 2)
    for y in range(h):
        if mask[y, 0] == 1:
            cv2.floodFill(mask, ff, (0, y), 2)
        if mask[y, w - 1] == 1:
            cv2.floodFill(mask, ff, (w - 1, y), 2)
    bg = (mask == 2)

    # Remove pure-white enclosed interior gaps (between outstretched arms & inside handles)
    if remove_holes:
        pure_w = (dist < 14.0) & (~bg)
        num_l, labels, stats, _ = cv2.connectedComponentsWithStats(pure_w.astype(np.uint8))
        for i in range(1, num_l):
            if stats[i, cv2.CC_STAT_AREA] >= 25:
                bg |= (labels == i)

    bg_dil = cv2.dilate(bg.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    alpha = np.where(bg, 0.0, 255.0).astype(np.float32)
    fringe = bg_dil & (~bg)
    ramp = np.clip((dist - 10.0) / 34.0, 0.0, 1.0) * 255.0
    alpha[fringe] = np.minimum(alpha[fringe], ramp[fringe])

    a_norm = alpha / 255.0
    out_rgb = rgb.copy()
    semi = (a_norm > 0.05) & (a_norm < 0.98)
    for c in range(3):
        out_rgb[..., c][semi] = np.clip(
            (rgb[..., c][semi] - 255.0 * (1.0 - a_norm[semi])) / np.maximum(a_norm[semi], 0.12),
            0.0, 255.0,
        )
    rgba = np.dstack([np.round(out_rgb).astype(np.uint8), np.round(alpha).astype(np.uint8)])
    ys, xs = np.nonzero(rgba[..., 3] > 20)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def trim_right_blades(rgba: np.ndarray, keep_right_frac: float) -> np.ndarray:
    """Keep Kyle's entire Superman body, lifted head, outstretched arms & clean fists right up to
    his knuckles (before any clipped chrome scissor rings!), with clean anti-halo edge erosion so
    the REAL 3D chrome snapping scissors mount seamlessly right into his intact fists!"""
    arr = rgba.copy()
    h, w = arr.shape[:2]
    cut_x = int(round(w * keep_right_frac))
    fade_w = max(3, int(round(w * 0.010)))
    arr[:, cut_x:, 3] = 0
    for c in range(max(0, cut_x - fade_w), cut_x):
        t = (cut_x - c) / float(fade_w)
        arr[:, c, 3] = np.round(arr[:, c, 3].astype(np.float32) * t).astype(np.uint8)
    # Clean any subtle grey-white halo fringe near the right knuckles (low-sat bright edge pixels)
    a = arr[..., 3]
    eroded = cv2.erode((a >= 180).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    edge = (a > 0) & (~eroded)
    rgb = arr[..., :3].astype(np.float32)
    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    fuzz = edge & (lo > 175.0) & (sat < 0.14)
    arr[..., 3][fuzz] = 0
    ys, xs = np.nonzero(arr[..., 3] > 20)
    return arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def register_horizontal_knots(rgba: np.ndarray, src_knots: List[float], dst_knots: List[float]) -> np.ndarray:
    """Piecewise-linear horizontal registration so loafers, belt, shoulders, head & fists share
    EXACT matching 3D X-coordinates across Side, Top-Down Back, and Bottom-Up Belly planes!"""
    h, w = rgba.shape[:2]
    u_dst = np.linspace(0.0, 1.0, w, dtype=np.float32)
    u_src = np.interp(u_dst, np.array(dst_knots, dtype=np.float32), np.array(src_knots, dtype=np.float32))
    map_x = np.tile((u_src * (w - 1)).astype(np.float32)[None, :], (h, 1))
    map_y = np.tile(np.arange(h, dtype=np.float32)[:, None], (1, w))
    # Premultiplied remap to prevent dark/white edge ringing
    pm = rgba.astype(np.float32)
    pm[..., :3] *= (pm[..., 3:4] / 255.0)
    rem = cv2.remap(pm, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    out = np.zeros_like(rgba)
    a = np.clip(rem[..., 3], 0.0, 255.0)
    nz = a > 1.0
    rgb = np.zeros_like(rem[..., :3])
    rgb[nz] = rem[..., :3][nz] * (255.0 / a[nz, None])
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a), 0, 255).astype(np.uint8)
    return out


def pack_horizontal_tex(body_rgba: np.ndarray, out_png: Path, tex_wh=(512, 160),
                        align_v: str = "center", dim: float = 0.84) -> np.ndarray:
    """Pack a horizontal-flying Kyle body (loafers at left -U, fists cleanly padded inside right +U)
    onto a crisp RGBA texture with zero border clipping and RGB edge bleed."""
    im = Image.fromarray(body_rgba, "RGBA")
    tw, th = tex_wh
    pad_l, pad_r, pad_y = 6, 14, 6
    scale = min((tw - pad_l - pad_r) / float(im.width), (th - 2 * pad_y) / float(im.height))
    nw = max(4, int(round(im.width * scale)))
    nh = max(4, int(round(im.height * scale)))
    rsz = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    # Anchor cleanly inside the padded right margin (zero clipped knuckles!)
    dx = tw - nw - pad_r
    dy = (th - nh - pad_y) if align_v == "bottom" else (th - nh) // 2
    canvas.alpha_composite(rsz, (dx, dy))
    arr = np.asarray(canvas).copy()
    arr[..., :3] = np.clip(np.round(arr[..., :3].astype(np.float32) * dim), 0, 255).astype(np.uint8)
    arr = bleed_rgb_edges(arr, passes=4)
    Image.fromarray(arr, "RGBA").save(out_png, format="PNG", compress_level=6, optimize=False)
    print(f"Wrote {out_png} ({tw}x{th}, body {nw}x{nh})")
    return arr


def find_latest_belly_photo() -> Path:
    """Check if our dedicated studio Superman Belly-Underneath photo has been generated."""
    hits = sorted(ARTIFACT_ROOT.glob("kyle_superman_belly*.jpg")) + sorted(ARTIFACT_ROOT.glob("kyle_superman_belly*.png"))
    return hits[-1] if hits else None


def build_textures():
    # Exact canonical 3D longitudinal knots (loafers=0.0, belt=0.555, shoulders=0.830, fists=1.0)
    canon = [0.0, 0.555, 0.830, 1.0]

    # 1. TRUE HORIZONTAL SUPERMAN SIDE PROFILE (real Grok studio video f_051.png, flipped -> flying +X!)
    side_full = key_pure_white(INSPO_FRAMES_DIR / "f_051.png")[:, ::-1, :]
    side_body = trim_right_blades(side_full, keep_right_frac=0.720)
    # Register belt (0.465->0.555) & shoulders (0.793->0.830) so Side locks 1:1 with Back & Belly in 3D!
    side_reg = register_horizontal_knots(side_body, [0.0, 0.465, 0.793, 1.0], canon)
    pack_horizontal_tex(side_reg, OUT_MODEL_DIR / "kyle_torp_side.png", tex_wh=(512, 160), align_v="center", dim=0.84)

    # 2. TRUE HORIZONTAL TOP-DOWN BACK VIEW (real Grok studio video f_164.png, rotated -90 -> flying +X!)
    back_full = np.rot90(key_pure_white(INSPO_FRAMES_DIR / "f_164.png"), k=-1)
    back_body = trim_right_blades(back_full, keep_right_frac=0.780)
    back_reg = register_horizontal_knots(back_body, [0.0, 0.551, 0.829, 1.0], canon)
    pack_horizontal_tex(back_reg, OUT_MODEL_DIR / "kyle_torp_back.png", tex_wh=(512, 144), align_v="center", dim=0.84)

    # 3. TRUE HORIZONTAL SUPERMAN BELLY / UNDERSIDE VIEW
    belly_photo = find_latest_belly_photo()
    if belly_photo is not None:
        print(f"Using dedicated studio Superman Belly photo: {belly_photo.name}")
        belly_raw = key_pure_white(belly_photo)
        if belly_raw.shape[0] > belly_raw.shape[1]:
            belly_raw = np.rot90(belly_raw, k=-1)
        belly_body = trim_right_blades(belly_raw, keep_right_frac=0.782)
        belly_reg = register_horizontal_knots(belly_body, [0.0, 0.563, 0.830, 1.0], canon)
        pack_horizontal_tex(belly_reg, OUT_MODEL_DIR / "kyle_torp_belly.png", tex_wh=(512, 144), align_v="center", dim=0.84)
    else:
        front34_full = key_pure_white(INSPO_FRAMES_DIR / "f_015.png")[:, ::-1, :]
        front34_body = trim_right_blades(front34_full, keep_right_frac=0.710)
        pack_horizontal_tex(front34_body, OUT_MODEL_DIR / "kyle_torp_belly.png", tex_wh=(512, 160), align_v="center", dim=0.84)


def build_torpedo_md3(out_md3: Path):
    """Build 8-frame 3D Spinning Horizontal Superman-Torpedo Kyle MD3:
      - Body X from -38 (brown loafers) to +22 (outstretched fists) = 60u long:
        * Surface 0 ('belly'): horizontal XY plane (z = -0.4), facing -Z (visible from BELOW)
        * Surface 1 ('back'):  horizontal XY plane (z = +0.4), facing +Z (visible from ABOVE)
        * Surface 2 ('side'):  vertical XZ plane (y = 0), cull none (pure Superman side profile!)
      - Scissors X from +18 to +56: REAL 3D GIANT CHROME BARBER SCISSORS mounted right at his
        outstretched fists, snapping open & shut (32 deg <-> 3 deg) across all 8 frames!
    """
    x0, x1 = -38.0, 22.0   # 60u body length (centered nicely near his torso/belt around x=0 for clean spinning!)
    hw_xy = 9.0            # 18u wide horizontal belly/back plane (aspect 3.33:1 matching 512x144!)
    hz_lo, hz_hi = -7.2, 11.6  # 18.8u tall vertical Superman side profile (fists sit dead-center at z=0.0!)

    # Surface 0: Belly (facing -Z, visible from below when looking up into the sky!)
    v_belly = [
        (x0, -hw_xy, -0.40),
        (x1, -hw_xy, -0.40),
        (x1, +hw_xy, -0.40),
        (x0, +hw_xy, -0.40),
    ]
    n_belly = [(0.0, 0.0, -1.0)] * 4
    st_quad = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    t_belly = [(0, 2, 1), (0, 3, 2)]

    # Surface 1: Back (facing +Z, visible from above — exact match to Grok video top-down view!)
    v_back = [
        (x0, -hw_xy, +0.40),
        (x1, -hw_xy, +0.40),
        (x1, +hw_xy, +0.40),
        (x0, +hw_xy, +0.40),
    ]
    n_back = [(0.0, 0.0, +1.0)] * 4
    t_back = [(0, 1, 2), (0, 2, 3)]

    # Surface 2: Pure Superman Side Profile (vertical XZ plane, cull none in shader!)
    v_side = [
        (x0, 0.0, hz_lo),
        (x1, 0.0, hz_lo),
        (x1, 0.0, hz_hi),
        (x0, 0.0, hz_hi),
    ]
    n_side = [(0.0, 1.0, 0.0)] * 4
    t_side = [(0, 1, 2), (0, 2, 3)]

    # Surface 3: Real 3D Giant Chrome Barber Scissors snapping straight out in front of Kyle's fists!
    open_angles = [32.0, 24.0, 13.0, 3.0, 13.0, 25.0, 34.0, 27.0]
    scis_frames = []
    scis_tris = None
    scis_st = None
    for ang in open_angles:
        verts: List[Tuple[float, float, float]] = []
        tris: List[Tuple[int, int, int]] = []
        st: List[Tuple[float, float]] = []
        scis_mod.build_one_half(verts, tris, st, +ang, +0.34, +1.0)
        scis_mod.build_one_half(verts, tris, st, -ang, -0.34, -1.0)
        scis_mod.add_cylinder_z(verts, tris, st, 0.0, 0.0, -0.95, +0.95, radius=1.18, n_seg=12)
        # Scale 1.48x and seat finger rings right in Kyle's outstretched fists (x=+19..+25, z=0.0), blades -> x=+58!
        xformed = [(vx * 1.48 + 31.5, vy * 1.48, vz * 1.48) for (vx, vy, vz) in verts]
        norms = scis_mod.compute_vertex_normals(xformed, tris)
        scis_frames.append((xformed, norms))
        if scis_tris is None:
            scis_tris = tris
            scis_st = st

    nframes = len(open_angles)
    surfaces = [
        dict(name="belly",    shader="progs/kyle_torp_belly", tris=t_belly,   st=st_quad, frames=[(v_belly, n_belly)] * nframes),
        dict(name="back",     shader="progs/kyle_torp_back",  tris=t_back,    st=st_quad, frames=[(v_back, n_back)] * nframes),
        dict(name="side",     shader="progs/kyle_torp_side",  tris=t_side,    st=st_quad, frames=[(v_side, n_side)] * nframes),
        dict(name="scissors", shader="progs/kyle_scissors",   tris=scis_tris, st=scis_st, frames=scis_frames),
    ]
    md3lib.write(str(out_md3), dict(name="kyle_torpedo", surfaces=surfaces, nframes=nframes))
    print(f"Wrote {out_md3} ({nframes} frames, 4 surfaces: real Grok Superman body + 3D snapping chrome scissors!)")


def main():
    OUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    build_textures()
    build_torpedo_md3(OUT_MODEL_DIR / "kyle_torpedo.md3")


if __name__ == "__main__":
    main()
