"""Build the 3D Winged Breezy-Hair Head model ('progs/john_bird_head.md3' + sRGB textures).

Reconstructs a high-resolution 3D anatomical head from the uploaded green-screen portrait,
sculpts 64 sleek, tangential wind-swept 3D hair locks (swept bangs, parted crown wisps,
temple flicks, and nape locks) that ripple and flap naturally in the breeze, and attaches
broad, lushly feathered articulated 3-joint 3D bird wings.

72 seamless vertex-animated frames across 5 clips:
  0..15   fly_breezy     Cruising bird wingbeat + breezy flapping hair
  16..31  windy_soar     Outstretched soaring thermal glide + gusty billowing hair
  32..47  hover_flutter  Energetic figure-8 bird hover + wild downdraft hair
  48..59  swoop_dive     Swept-back falcon dive/swoop + high-speed streaming hair
  60..71  perch_breeze   Articulated folded wings tucked at rest + gentle breeze in hair
"""
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_char_models as B
import md3lib

ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out", "john_bird")
PROGS_DIR = os.path.join(ROOT_DIR, "progs")

DEFAULT_UPLOAD = r"C:\Users\qxdc\.gemini\antigravity\brain\f3bc66bf-35ae-4b35-915b-45b0c14f2ce6\.user_uploaded\media_1793536817679_085d79be.jpg"
LOCAL_UPLOAD_COPY = os.path.join(OUT_DIR, "uploaded_head_greenscreen.jpg")

HEAD_HEIGHT = 36.0          # Quake units (chin to crown)
BASE_Z = 48.0               # Hover altitude above ground shadow plane (z=0)
NH, MH = 56, 60             # Head cylindrical rings (56 around x 60 vertical)
HEAD_TEX_W, HEAD_TEX_H = 1024, 1024
TOTAL_FRAMES = 72


def smoothstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def bleed(rgb, mask, erode_px=4):
    core = ndimage.binary_erosion(mask, iterations=erode_px)
    if not core.any():
        core = mask
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    return rgb[idx[0], idx[1]]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float32)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float32)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)


def compute_vertex_normals(verts, tris):
    """Fast vectorized area-weighted smooth vertex normals."""
    v = np.asarray(verts, dtype=np.float32)
    t = np.asarray(tris, dtype=np.int32)
    v0, v1, v2 = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    vn = np.zeros_like(v)
    np.add.at(vn, t[:, 0], fn)
    np.add.at(vn, t[:, 1], fn)
    np.add.at(vn, t[:, 2], fn)
    ln = np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-8)
    return vn / ln


# ==============================================================================
# 1. CHROMA-KEY DESPILL & TEXTURE SYNTHESIS (HEAD, HAIR, BIRD FEATHERS)
# ==============================================================================

def load_and_despill_front():
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.isfile(DEFAULT_UPLOAD):
        shutil.copyfile(DEFAULT_UPLOAD, LOCAL_UPLOAD_COPY)
    src_path = LOCAL_UPLOAD_COPY if os.path.isfile(LOCAL_UPLOAD_COPY) else os.path.join(B.REF, "johnwave_head_green.jpg")
    im = Image.open(src_path).convert("RGB")
    if im.size != (1024, 566):
        im = im.resize((1024, 566), Image.Resampling.LANCZOS)

    rgb = np.asarray(im, dtype=np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    bg = (g > r + 24.0) & (g > b + 24.0) & (g > 70.0)
    fg = ndimage.binary_opening(~bg, iterations=2)
    lab, n = ndimage.label(fg)
    mask = lab == (1 + int(np.argmax(ndimage.sum(fg, lab, range(1, n + 1)))))
    mask = ndimage.binary_fill_holes(mask)
    mask = ndimage.binary_erosion(mask, iterations=1)

    # Edge-aware green despill: zero neon-green fringe on hair/beard/ears, 100% natural warm skin tones
    dist_in = ndimage.distance_transform_edt(mask)
    edge_w = np.clip(1.0 - (dist_in - 1.0) / 14.0, 0.0, 1.0)
    green_excess = np.maximum(0.0, g - np.maximum(r, b))
    spill_w = np.maximum(edge_w, smoothstep(2.0, 18.0, green_excess))
    rgb_clean = rgb.copy()
    rgb_clean[..., 1] = g - green_excess * spill_w
    halo = edge_w * smoothstep(55.0, 150.0, g) * 0.35
    rgb_clean *= (1.0 - halo[..., None])

    bled = bleed(rgb_clean, mask, erode_px=5)
    return bled, mask


def build_hair_strand_texture(front_rgb):
    """Synthesize a rich, glossy 512x512 hair strand texture directly from John's hair in the uploaded photo."""
    W, H = 512, 512
    dark_px = front_rgb[175:230, 430:560].reshape(-1, 3)
    dark_med = np.percentile(dark_px, 28, axis=0)          # Rich espresso shadow
    mid_med = np.percentile(dark_px, 68, axis=0)           # Warm dark brown
    hi_px = front_rgb[102:148, 490:560].reshape(-1, 3)
    hi_med = np.percentile(hi_px, 78, axis=0)              # Sunlit crown chestnut highlight

    rng = np.random.default_rng(42)
    u = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]

    f1 = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), sigma=(28.0, 1.2))
    f2 = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), sigma=(9.0, 0.7))
    fibers = np.clip(0.5 + 0.32 * (f1 / (f1.std() + 1e-6)) + 0.18 * (f2 / (f2.std() + 1e-6)), 0.0, 1.0)

    real_strip = Image.fromarray(front_rgb[112:232, 435:580].clip(0, 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR)
    real_arr = ndimage.gaussian_filter(np.asarray(real_strip, dtype=np.float32), sigma=(16.0, 6.0, 0.0))

    arch = np.clip(np.sin(u * math.pi), 0.0, 1.0) ** 0.70
    spec_band = np.exp(-(((v - 0.36 + 0.07 * np.sin(u * 8.0)) / 0.17) ** 2)) * (arch ** 1.4)
    root_ao = smoothstep(0.0, 0.18, v)
    tip_shade = 1.0 - 0.22 * smoothstep(0.76, 1.0, v)

    base = dark_med[None, None, :] * (1.0 - fibers[..., None]) + mid_med[None, None, :] * fibers[..., None]
    base = 0.76 * base + 0.24 * real_arr
    col = base * (0.62 + 0.44 * arch[..., None]) * (0.72 + 0.28 * root_ao[..., None]) * tip_shade[..., None]
    col += (hi_med[None, None, :] * 0.36) * (spec_band * (0.50 + 0.50 * fibers))[..., None]

    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))


def build_feather_atlas(front_rgb, variant="hawk"):
    """Build a crisp 1024x1024 avian feather texture atlas:
      Top half    V=[0.00..0.52]: Individual flight/covert feather (U=0..1 across vane, V=0 root -> V=0.50 tip)
      Bottom-left V=[0.55..1.00], U=[0.00..0.55]: Layered covert shingle plumage (for wing arm)
      Bottom-right V=[0.55..1.00], U=[0.55..1.00]: Soft scapular shoulder down blending with John's hair
    """
    W, H = 1024, 1024
    out = np.zeros((H, W, 3), dtype=np.float32)
    hair_dark = np.percentile(front_rgb[170:225, 435:560].reshape(-1, 3), 45, axis=0)

    rng = np.random.default_rng(107 if variant == "hawk" else 209)

    if variant == "hawk":
        c_root = hair_dark * 1.12
        c_mid = np.array([124.0, 86.0, 56.0], dtype=np.float32)      # Rich golden-umber hawk plumage
        c_pale = np.array([214.0, 184.0, 144.0], dtype=np.float32)   # Warm cream-buff inner vane & tips
        c_bar = np.array([38.0, 26.0, 20.0], dtype=np.float32)       # Crisp dark raptor barring
        c_quill = np.array([238.0, 222.0, 196.0], dtype=np.float32)  # Ivory rachis quill
    else:
        c_root = np.array([192.0, 186.0, 178.0], dtype=np.float32)
        c_mid = np.array([236.0, 232.0, 224.0], dtype=np.float32)    # Angelic pearl white
        c_pale = np.array([252.0, 248.0, 240.0], dtype=np.float32)   # Warm ivory highlight
        c_bar = np.array([132.0, 142.0, 158.0], dtype=np.float32)    # Silver-slate primary tips
        c_quill = np.array([255.0, 252.0, 242.0], dtype=np.float32)

    h1 = 532
    u = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, h1, dtype=np.float32)[:, None]

    q_pos = 0.44
    du = u - q_pos
    dist_q = np.abs(du)

    barb_coord = v * 90.0 - dist_q * 56.0
    barbs = 0.5 + 0.5 * np.sin(barb_coord * 2.0 * math.pi)
    micro = ndimage.gaussian_filter(rng.standard_normal((h1, W)).astype(np.float32), sigma=(1.2, 3.0))
    barb_tex = np.clip(0.78 + 0.17 * barbs + 0.08 * (micro / (micro.std() + 1e-6)), 0.48, 1.15)

    outer_web = (du < 0.0).astype(np.float32)
    vane_col = (
        c_root[None, None, :] * (1.0 - smoothstep(0.0, 0.30, v))[..., None]
        + c_mid[None, None, :] * (smoothstep(0.0, 0.30, v) * (1.0 - smoothstep(0.64, 0.92, v)))[..., None]
        + c_bar[None, None, :] * smoothstep(0.68, 0.94, v)[..., None]
    )
    inner_glow = (1.0 - outer_web) * smoothstep(0.05, 0.30, du) * (1.0 - smoothstep(0.68, 0.92, v)) * 0.52
    vane_col = vane_col * (1.0 - inner_glow[..., None]) + c_pale[None, None, :] * inner_glow[..., None]

    bars = np.sin(v * 6.5 * math.pi)
    bar_w = smoothstep(0.24, 0.44, v) * (1.0 - smoothstep(0.78, 0.92, v)) * smoothstep(0.25, 0.75, bars) * 0.36
    vane_col = vane_col * (1.0 - bar_w[..., None]) + c_bar[None, None, :] * bar_w[..., None]

    tip_rim = smoothstep(0.91, 0.985, v) * 0.56
    vane_col = vane_col * (1.0 - tip_rim[..., None]) + c_pale[None, None, :] * tip_rim[..., None]

    vane_col *= barb_tex[..., None]
    edge_ao = 1.0 - 0.24 * smoothstep(0.36, 0.54, dist_q)
    vane_col *= edge_ao[..., None]

    q_half_w = 0.016 * (1.0 - 0.70 * v)
    quill_m = np.exp(-((du / np.maximum(q_half_w, 0.002)) ** 2))
    quill_ao = np.exp(-((du / np.maximum(q_half_w * 2.8, 0.005)) ** 2)) * (1.0 - quill_m) * 0.24
    vane_col *= (1.0 - quill_ao[..., None])
    vane_col = vane_col * (1.0 - quill_m[..., None]) + c_quill[None, None, :] * quill_m[..., None]
    out[:h1] = vane_col

    h2 = H - h1
    shingle = Image.new("RGB", (W, h2), tuple(int(x) for x in c_root.clip(0, 255)))
    dr = ImageDraw.Draw(shingle)
    rows, cols = 9, 14
    rw, rh = W / cols, h2 / rows
    for r_i in range(rows + 1):
        t_r = r_i / max(1, rows)
        for c_i in range(-1, cols + 1):
            cx = (c_i + (0.5 if (r_i & 1) else 0.0)) * rw
            cy = r_i * rh
            u_frac = np.clip(cx / W, 0.0, 1.0)
            hair_mix = smoothstep(0.52, 0.76, float(u_frac))
            f_base = c_mid * (1.0 - 0.30 * (1.0 - t_r))
            f_col = f_base * (1.0 - hair_mix) + (hair_dark * 1.08) * hair_mix
            shade = float(rng.uniform(0.90, 1.12))
            fill_dark = tuple(int(x) for x in (f_col * 0.64 * shade).clip(0, 255))
            fill_mid = tuple(int(x) for x in (f_col * 1.00 * shade).clip(0, 255))
            fill_rim = tuple(int(x) for x in ((f_col * 0.65 + c_pale * 0.35) * shade).clip(0, 255))
            dr.ellipse([cx - rw * 0.62, cy - rh * 0.75, cx + rw * 0.62, cy + rh * 0.88], fill=fill_dark)
            dr.ellipse([cx - rw * 0.54, cy - rh * 0.65, cx + rw * 0.54, cy + rh * 0.80], fill=fill_rim)
            dr.ellipse([cx - rw * 0.48, cy - rh * 0.62, cx + rw * 0.48, cy + rh * 0.68], fill=fill_mid)
            if hair_mix < 0.7:
                q_c = tuple(int(x) for x in (c_quill * 0.88).clip(0, 255))
                dr.line([(cx, cy - rh * 0.52), (cx, cy + rh * 0.66)], fill=q_c, width=2)

    sh_arr = np.asarray(shingle.filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32)
    fine_n = ndimage.gaussian_filter(rng.standard_normal((h2, W)).astype(np.float32), sigma=(3.5, 1.1))
    sh_arr *= np.clip(1.0 + 0.07 * (fine_n / (fine_n.std() + 1e-6)), 0.85, 1.15)[..., None]
    out[h1:] = sh_arr

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ==============================================================================
# 2. 3D ANATOMICAL HEAD RECONSTRUCTION & SKIN UNWRAP
# ==============================================================================

def outline_stats(mask, y0, y1, n, sigma):
    ys = np.arange(mask.shape[0], dtype=np.float32)
    has = mask.any(axis=1)
    lo = mask.argmax(axis=1).astype(np.float32)
    hi = (mask.shape[1] - 1 - mask[:, ::-1].argmax(axis=1)).astype(np.float32)
    lo = np.interp(ys, ys[has], lo[has])
    hi = np.interp(ys, ys[has], hi[has])
    lo = ndimage.gaussian_filter1d(lo, sigma)
    hi = ndimage.gaussian_filter1d(hi, sigma)
    yt = y0 + (y1 - y0) * np.linspace(0.0, 1.0, n)
    return yt, np.interp(yt, ys, 0.5 * (lo + hi)), np.interp(yt, ys, 0.5 * (hi - lo))


def hair_median(rgb, mask, y0, y1):
    sel = mask.copy()
    sel[:y0] = False
    sel[y1:] = False
    px = rgb[sel]
    dark = px[px.mean(axis=1) < 115.0]
    return np.median(dark if len(dark) else px, axis=0)


def build_base_head(front_rgb, front_mask):
    ys = np.nonzero(front_mask)[0]
    ybot, ytop = float(ys.max() - 2.0), float(ys.min() + 2.0)
    yt, cx, hw = outline_stats(front_mask, ybot, ytop, MH, sigma=3.8)
    hw = np.maximum(hw, 0.11 * hw.max())

    t = np.linspace(0.0, 1.0, MH)                                    # 0 = chin, 1 = top of crown
    th = -math.pi / 2.0 + 2.0 * math.pi * np.arange(NH) / NH         # k=0 back (-X), k=NH/2 face (+X)
    cs, sn = np.cos(th), np.sin(th)

    db = 0.80 + 0.44 * smoothstep(0.16, 0.56, t)
    fr = np.sign(sn) * (np.abs(sn) ** 0.76)

    P = np.zeros((MH, NH, 3), dtype=np.float32)
    P[..., 1] = cx[:, None] + hw[:, None] * cs[None, :]
    P[..., 0] = hw[:, None] * fr[None, :] * np.where(sn[None, :] > 0.0, 0.90, db[:, None])
    P[..., 2] = yt[:, None]

    UVF = P[..., [1, 2]].copy()
    face_w = np.clip(sn, 0.0, 1.0)[None, :] ** 1.85

    # High-detail 3D facial relief aligned to 1024x566 landmarks
    px, py = UVF[..., 0], UVF[..., 1]

    g_tip = np.exp(-(((px - 531.0) / 16.5) ** 2 + ((py - 332.0) / 22.0) ** 2))
    g_bridge = np.exp(-(((px - 528.5) / 11.5) ** 2 + ((py - 304.0) / 24.0) ** 2))
    g_alar_r = np.exp(-(((px - 511.0) / 10.0) ** 2 + ((py - 337.0) / 9.0) ** 2))
    g_alar_l = np.exp(-(((px - 548.0) / 10.0) ** 2 + ((py - 337.0) / 9.0) ** 2))
    P[..., 0] += (26.5 * g_tip + 14.0 * g_bridge + 6.5 * (g_alar_r + g_alar_l)) * face_w

    g_brow = np.exp(-(((px - 526.0) / 62.0) ** 2 + ((py - 274.0) / 11.0) ** 2))
    g_orb_r = np.exp(-(((px - 481.0) / 22.0) ** 2 + ((py - 291.0) / 12.5) ** 2))
    g_orb_l = np.exp(-(((px - 570.0) / 22.0) ** 2 + ((py - 290.0) / 12.5) ** 2))
    g_eye_r = np.exp(-(((px - 481.0) / 10.0) ** 2 + ((py - 291.0) / 7.0) ** 2))
    g_eye_l = np.exp(-(((px - 570.0) / 10.0) ** 2 + ((py - 290.0) / 7.0) ** 2))
    P[..., 0] += (8.0 * g_brow - 6.5 * (g_orb_r + g_orb_l) + 3.8 * (g_eye_r + g_eye_l)) * face_w

    g_chk_r = np.exp(-(((px - 454.0) / 28.0) ** 2 + ((py - 320.0) / 24.0) ** 2))
    g_chk_l = np.exp(-(((px - 592.0) / 28.0) ** 2 + ((py - 320.0) / 24.0) ** 2))
    g_stache = np.exp(-(((px - 529.0) / 42.0) ** 2 + ((py - 362.0) / 15.0) ** 2))
    g_beard = np.exp(-(((px - 524.0) / 56.0) ** 2 + ((py - 412.0) / 34.0) ** 2))
    P[..., 0] += (8.5 * (g_chk_r + g_chk_l) + 9.5 * g_stache + 11.0 * g_beard) * face_w

    bk = B.Photo(B.SUIT["back"], B.SUIT["key"])
    byt, bcx, bhw = outline_stats(bk.sil, 262.0, 58.0, MH, sigma=4.0)
    psi = np.angle(np.exp(1j * (th + math.pi / 2.0)))
    side = np.sin(np.clip(0.65 * psi, -math.pi / 2.0, math.pi / 2.0))
    UVB = np.stack([bcx[:, None] - bhw[:, None] * side[None, :], np.repeat(byt[:, None], NH, axis=1)], axis=-1)

    brgb = bleed(bk.rgb.astype(np.float32), bk.sil, erode_px=4)
    fh = hair_median(front_rgb, front_mask, int(ytop), int(ytop + 0.26 * (ybot - ytop)))
    bh = hair_median(brgb, bk.sil, 60, 200)
    tint = np.clip((fh / max(1.0, fh.mean())) / (bh / max(1.0, bh.mean())), 0.90, 1.10)
    brgb *= (fh.mean() / max(1.0, bh.mean())) * tint

    kk = (np.arange(HEAD_TEX_W) + 0.5) / HEAD_TEX_W * NH
    jj = np.clip((1.0 - (np.arange(HEAD_TEX_H) + 0.5) / HEAD_TEX_H) * (MH - 1), 0.5, MH - 1.001)
    KK, JJ = np.meshgrid(kk, jj)
    skin_arr = np.zeros((HEAD_TEX_H, HEAD_TEX_W, 3), dtype=np.float32)
    wf = smoothstep(0.10, 0.40, np.sin(-math.pi / 2.0 + 2.0 * math.pi * KK / NH))
    for grid, img_src, w in ((UVF, front_rgb, wf), (UVB, brgb, 1.0 - wf)):
        g_wrap = np.concatenate([grid, grid[:, :1]], axis=1)
        px_map = [ndimage.map_coordinates(g_wrap[..., c], [JJ, KK], order=1, mode="nearest") for c in range(2)]
        for c in range(3):
            skin_arr[..., c] += w * ndimage.map_coordinates(img_src[..., c], [px_map[1], px_map[0]], order=1, mode="nearest")

    # Softly blend top-crown pole rim highlight into rich natural dark hair so top pole has zero bright pinch
    pole_w = (1.0 - smoothstep(0.0, 0.09, np.linspace(0.0, 1.0, HEAD_TEX_H)[:, None]))[..., None]
    crown_med = fh[None, None, :] * 1.15
    skin_arr = skin_arr * (1.0 - 0.72 * pole_w) + np.minimum(skin_arr, crown_med) * (0.72 * pole_w)
    head_tex_im = Image.fromarray(np.clip(skin_arr * 1.06, 0, 255).astype(np.uint8))

    P_all = np.vstack([
        P.reshape(-1, 3),
        [[0.0, float(cx[0]), ybot + 2.0]],
        [[0.0, float(cx[-1]), ytop - 1.5]],
    ])
    P_all[:, 2] = -P_all[:, 2]
    lo, hi = P_all.min(axis=0), P_all.max(axis=0)
    scale = HEAD_HEIGHT / float(hi[2] - lo[2])
    center_px = 0.5 * (lo + hi)
    V_ring = (P_all[:-2] - center_px) * scale
    V_bot = (P_all[-2] - center_px) * scale
    V_top = (P_all[-1] - center_px) * scale

    verts = []
    uvs = []
    ring_meta = []
    NC = NH + 1
    for j in range(MH):
        tj = j / float(MH - 1)
        v_coord = 1.0 - tj
        for k in range(NC):
            km = k % NH
            pos = V_ring[j * NH + km].copy()
            u_coord = k / float(NH)
            th_k = -math.pi / 2.0 + 2.0 * math.pi * (km / float(NH))
            is_front = max(0.0, math.sin(th_k))
            hair_h_thresh = 0.64 * is_front + 0.36 * (1.0 - is_front)
            hw_rip = smoothstep(hair_h_thresh, hair_h_thresh + 0.16, tj)
            verts.append(pos)
            uvs.append((u_coord, v_coord))
            ring_meta.append((tj, th_k, hw_rip))

    tris = []
    for j in range(MH - 1):
        for k in range(NH):
            a = j * NC + k
            b = j * NC + (k + 1)
            c = (j + 1) * NC + (k + 1)
            d = (j + 1) * NC + k
            tris.append((a, b, c))
            tris.append((a, c, d))

    for is_top, pole_pos, j_ring in ((False, V_bot, 0), (True, V_top, MH - 1)):
        v_c = 1.0 if not is_top else 0.0
        for k in range(NH):
            ci = len(verts)
            verts.append(pole_pos.copy())
            uvs.append(((k + 0.5) / float(NH), v_c))
            ring_meta.append((1.0 if is_top else 0.0, 0.0, 0.55 if is_top else 0.0))
            a = j_ring * NC + k
            b = j_ring * NC + (k + 1)
            if is_top:
                tris.append((a, b, ci))
            else:
                tris.append((b, a, ci))

    verts = np.asarray(verts, dtype=np.float32)
    tris = np.asarray(tris, dtype=np.int32)
    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    cen = (v0 + v1 + v2) / 3.0
    nrm = np.cross(v1 - v0, v2 - v0)
    flip = np.einsum("ij,ij->i", nrm, cen) < 0.0
    tris[flip] = tris[flip][:, [0, 2, 1]]

    return dict(
        verts=verts,
        uvs=uvs,
        tris=[tuple(int(x) for x in t) for t in tris],
        ring_meta=np.asarray(ring_meta, dtype=np.float32),
        grid_pos=V_ring.reshape(MH, NH, 3),
        head_tex=head_tex_im,
    )


# ==============================================================================
# 3. 64 SLEEK, TANGENTIAL WIND-SWEPT 3D BREEZY HAIR STRANDS/LOCKS
# ==============================================================================

def sample_head_surface(grid_pos, t_h, theta_rad):
    jf = np.clip(t_h, 0.0, 0.999) * (MH - 1)
    j0 = int(math.floor(jf))
    j1 = min(MH - 1, j0 + 1)
    jt = jf - j0

    u_ang = ((theta_rad + math.pi / 2.0) / (2.0 * math.pi)) % 1.0
    kf = u_ang * NH
    k0 = int(math.floor(kf)) % NH
    k1 = (k0 + 1) % NH
    kt = kf - math.floor(kf)

    p00, p01 = grid_pos[j0, k0], grid_pos[j0, k1]
    p10, p11 = grid_pos[j1, k0], grid_pos[j1, k1]
    p = (1.0 - jt) * ((1.0 - kt) * p00 + kt * p01) + jt * ((1.0 - kt) * p10 + kt * p11)
    ring_c = grid_pos[j0].mean(axis=0) * (1.0 - jt) + grid_pos[j1].mean(axis=0) * jt
    out = p - ring_c
    out[2] += 4.2 * max(0.0, t_h - 0.65)
    out /= max(1e-6, float(np.linalg.norm(out)))
    return p, out


def make_tangent(vec, n_out, lift=0.08):
    """Project vec onto the local scalp tangent plane + tiny natural hair-volume lift so locks NEVER stick straight out!"""
    t = vec - np.dot(vec, n_out) * n_out + n_out * lift
    return (t / max(1e-6, float(np.linalg.norm(t)))).astype(np.float32)


def build_hair_locks_spec(grid_pos):
    """64 sleek, combed tangential hair locks matching John's parted swept hairstyle,
    designed to flow, wave, and flutter naturally in the breeze!"""
    rng = np.random.default_rng(77)
    locks = []

    # Group A: 18 Sleek Swept Forehead Bang Strands (parted on his left +Y, sweeping smoothly across brow toward -Y)
    for i in range(18):
        f = i / 17.0
        th_r = math.pi * (0.28 + 0.44 * f)
        t_h = 0.77 + 0.11 * (1.0 - abs(f - 0.30))
        p_root, n_out = sample_head_surface(grid_pos, t_h, th_r)
        p_root = p_root - n_out * 0.15
        raw_dir = np.array([0.45, -0.78 - 0.12 * (1.0 - f), -0.62], dtype=np.float32)
        dir0 = make_tangent(raw_dir, n_out, lift=0.06)
        curve = np.array([0.08, -0.42, -0.45], dtype=np.float32)
        locks.append(dict(
            kind="bang",
            root=p_root,
            n_out=n_out,
            dir0=dir0,
            curve=curve,
            length=8.2 + 2.6 * math.sin((0.15 + 0.75 * f) * math.pi),
            width=1.05 + 0.35 * float(rng.random()),
            thick=0.36,
            phase=float(i * 0.44 + rng.uniform(-0.15, 0.15)),
            u_off=float(rng.uniform(0.06, 0.24)),
            wind_amp=0.95,
        ))

    # Group B: 18 Combed Crown & Top Wind-Wisps (parted & sweeping sleekly across crown + trailing aft in wind!)
    for i in range(18):
        f = i / 17.0
        th_r = math.pi * (-0.15 + 0.85 * f)              # Rooted on crown/sides/upper-back, trailing sleekly aft
        t_h = 0.78 + 0.16 * ((i % 3) / 2.0)
        p_root, n_out = sample_head_surface(grid_pos, min(0.95, t_h), th_r)
        p_root = p_root - n_out * 0.22
        raw_dir = np.array([-0.92, -0.45 + 0.22 * f, -0.22], dtype=np.float32)
        dir0 = make_tangent(raw_dir, n_out, lift=0.04)
        curve = np.array([-0.95, -0.18, -0.68], dtype=np.float32)
        locks.append(dict(
            kind="crown",
            root=p_root,
            n_out=n_out,
            dir0=dir0,
            curve=curve,
            length=9.8 + 2.8 * float(rng.random()),
            width=1.45 + 0.42 * float(rng.random()),
            thick=0.42,
            phase=float(i * 0.51),
            u_off=float(rng.uniform(0.02, 0.18)),
            wind_amp=1.18,
        ))

    # Group C: 16 Sleek Temple & Ear-Sweep Strands (8 right -Y, 8 left +Y — hugging temples & flicking back at tips!)
    for side_sgn in (-1.0, 1.0):
        for i in range(8):
            f = i / 7.0
            base_th = math.pi if side_sgn < 0 else 0.0
            th_r = base_th - side_sgn * (0.28 - 0.52 * f)      # From front-temple around to above-ear
            t_h = 0.54 + 0.28 * f
            p_root, n_out = sample_head_surface(grid_pos, t_h, th_r)
            p_root = p_root - n_out * 0.18
            # Combed sleekly BACKWARD (-X) and slightly down along the temple, flaring gently at the tip!
            raw_dir = np.array([-0.92, side_sgn * 0.18, -0.28 + 0.20 * f], dtype=np.float32)
            dir0 = make_tangent(raw_dir, n_out, lift=0.08)
            curve = np.array([-0.75, side_sgn * 0.36, 0.14], dtype=np.float32)
            locks.append(dict(
                kind="side",
                root=p_root,
                n_out=n_out,
                dir0=dir0,
                curve=curve,
                length=8.4 + 2.4 * float(rng.random()),
                width=1.10 + 0.32 * float(rng.random()),
                thick=0.38,
                phase=float(i * 0.62 + (0.0 if side_sgn < 0 else 1.5)),
                u_off=float(rng.uniform(0.08, 0.25)),
                wind_amp=1.18,
            ))

    # Group D: 12 Back / Nape Slipstream Strands (streaming smoothly behind his head!)
    for i in range(12):
        f = i / 11.0
        th_r = -math.pi / 2.0 + (f - 0.5) * 1.25
        t_h = 0.42 + 0.38 * ((i % 3) / 2.0)
        p_root, n_out = sample_head_surface(grid_pos, t_h, th_r)
        p_root = p_root - n_out * 0.20
        y_lat = math.sin(th_r + math.pi / 2.0) * 0.25
        raw_dir = np.array([-0.90, y_lat, -0.35], dtype=np.float32)
        dir0 = make_tangent(raw_dir, n_out, lift=0.08)
        curve = np.array([-0.85, y_lat * 0.35, 0.12], dtype=np.float32)
        locks.append(dict(
            kind="back",
            root=p_root,
            n_out=n_out,
            dir0=dir0,
            curve=curve,
            length=9.2 + 2.8 * float(rng.random()),
            width=1.28 + 0.32 * float(rng.random()),
            thick=0.40,
            phase=float(i * 0.58 + 0.3),
            u_off=float(rng.uniform(0.05, 0.22)),
            wind_amp=1.22,
        ))

    # 6 middle stations x 4 crescent verts + root + pointed tip = 26 verts/lock -> 64*26 = 1664 verts!
    N_MID = 6
    uvs = []
    tris = []
    for li, lk in enumerate(locks):
        base_v = li * (N_MID * 4 + 2)
        u0 = lk["u_off"]
        u_span = 0.70
        uvs.append((u0 + 0.5 * u_span, 0.02))
        for si in range(N_MID):
            s = (si + 1) / float(N_MID + 1)
            uvs.append((u0 + 0.50 * u_span, s))
            uvs.append((u0 + 0.96 * u_span, s))
            uvs.append((u0 + 0.52 * u_span, s))
            uvs.append((u0 + 0.04 * u_span, s))
        uvs.append((u0 + 0.5 * u_span, 0.98))

        r_idx = base_v
        t_idx = base_v + 1 + N_MID * 4
        for c in range(4):
            c1 = (c + 1) % 4
            tris.append((r_idx, base_v + 1 + c, base_v + 1 + c1))
        for si in range(N_MID - 1):
            r0 = base_v + 1 + si * 4
            r1 = r0 + 4
            for c in range(4):
                c1 = (c + 1) % 4
                tris.append((r0 + c, r1 + c, r1 + c1))
                tris.append((r0 + c, r1 + c1, r0 + c1))
        last_r = base_v + 1 + (N_MID - 1) * 4
        for c in range(4):
            c1 = (c + 1) % 4
            tris.append((last_r + c, t_idx, last_r + c1))

    return locks, uvs, tris


def eval_hair_locks_frame(locks, wind_cfg, head_rot, head_pos):
    N_MID = 6
    verts = []
    t_phase = wind_cfg["phase"]
    harm = wind_cfg["harm"]
    breeze = wind_cfg["breeze"]
    flutter = wind_cfg["flutter"]
    gust_z = wind_cfg["gust_z"]

    for lk in locks:
        root = lk["root"]
        n_out = lk["n_out"]
        dir0 = lk["dir0"]
        curve = lk["curve"]
        L = lk["length"]
        W = lk["width"]
        H_th = lk["thick"]
        ph = lk["phase"]
        amp = lk["wind_amp"]
        kind = lk["kind"]

        N0 = n_out - np.dot(n_out, dir0) * dir0
        nl = float(np.linalg.norm(N0))
        N0 = (N0 / nl) if nl > 1e-5 else np.array([0.0, 0.0, 1.0], dtype=np.float32)

        s_vals = [0.0] + [(si + 1) / float(N_MID + 1) for si in range(N_MID)] + [1.0]
        spine = []
        normals = []
        binorms = []

        for s in s_vals:
            p = root + L * (dir0 * s + 0.36 * curve * (s ** 1.85))
            sw = (s ** 1.65) * amp
            wave1 = math.sin(harm * t_phase - 3.3 * s + ph)
            wave2 = math.cos(2 * harm * t_phase - 5.0 * s + ph * 1.6)
            lat_wave = math.sin(harm * t_phase - 2.6 * s + ph + 1.1)

            if kind == "bang":
                # Bangs sweep gracefully across forehead & flutter/ripple in the breeze without spiking above crown!
                lift_up = breeze * 0.55 + flutter * (1.15 * wave1 + 0.45 * wave2) + gust_z * 0.65
                push_x = 0.45 * breeze + flutter * (0.65 * wave1)
                sway_y = -1.35 * breeze + flutter * (1.55 * lat_wave)
                disp = np.array([push_x, sway_y, lift_up], dtype=np.float32) * sw
            elif kind == "crown":
                # Crown locks stream sleekly backward (-X) & wave up-and-down in the wind!
                disp = np.array([
                    -4.2 * breeze + flutter * (1.25 * wave2),
                    -0.95 * breeze + flutter * (1.65 * lat_wave),
                    -0.35 * breeze + flutter * (1.55 * wave1 + 0.55 * wave2) + gust_z * 0.85,
                ], dtype=np.float32) * sw
            elif kind == "side":
                sgn_y = 1.0 if root[1] >= 0.0 else -1.0
                disp = np.array([
                    -3.8 * breeze + flutter * (1.15 * wave2),
                    sgn_y * (1.05 * breeze + flutter * (1.35 * (0.4 + 0.6 * wave1))),
                    -0.15 * breeze + flutter * (1.55 * wave1) + gust_z * 0.85,
                ], dtype=np.float32) * sw
            else:
                disp = np.array([
                    -4.2 * breeze + flutter * (1.10 * wave2),
                    flutter * (1.75 * lat_wave),
                    -0.25 * breeze + flutter * (1.75 * wave1) + gust_z * 0.85,
                ], dtype=np.float32) * sw

            p = p + disp

            # Keep locks gently outside the head ellipsoid so strands never clip into scalp or forehead!
            if s > 0.04:
                ell = np.array([p[0] / 12.8, p[1] / 12.6, (p[2] - 0.5) / 18.0], dtype=np.float32)
                r_e = float(np.linalg.norm(ell))
                if r_e < 1.02:
                    p = p * (1.03 / max(0.25, r_e))

            spine.append(p)

        for idx_s, s in enumerate(s_vals):
            if idx_s == 0:
                tang = spine[1] - spine[0]
            elif idx_s == len(s_vals) - 1:
                tang = spine[-1] - spine[-2]
            else:
                tang = spine[idx_s + 1] - spine[idx_s - 1]
            tang /= max(1e-6, float(np.linalg.norm(tang)))
            twist = 0.26 * flutter * math.sin(harm * t_phase - 2.8 * s + ph) * s
            n_cur = N0 - np.dot(N0, tang) * tang
            nl = float(np.linalg.norm(n_cur))
            n_cur = (n_cur / nl) if nl > 1e-5 else N0
            b_cur = np.cross(tang, n_cur)
            b_cur /= max(1e-6, float(np.linalg.norm(b_cur)))
            ct, st = math.cos(twist), math.sin(twist)
            normals.append(ct * n_cur + st * b_cur)
            binorms.append(-st * n_cur + ct * b_cur)

        verts.append(spine[0])
        for si in range(N_MID):
            k = si + 1
            s = s_vals[k]
            # Sleek tapered hair lock profile (narrows cleanly to a wispy pointed tip!)
            w_s = W * (0.75 + 0.35 * math.sin(s * math.pi * 0.75)) * (1.0 - 0.72 * (s ** 1.75))
            h_s = H_th * (1.0 - 0.70 * (s ** 1.5))
            c_p = spine[k]
            nc, bc = normals[k], binorms[k]
            verts.append(c_p + nc * h_s)
            verts.append(c_p + bc * w_s - nc * (0.20 * h_s))
            verts.append(c_p + nc * (0.08 * h_s))
            verts.append(c_p - bc * w_s - nc * (0.20 * h_s))
        verts.append(spine[-1])

    V = np.asarray(verts, dtype=np.float32)
    return (V @ head_rot.T) + head_pos[None, :]


# ==============================================================================
# 4. ARTICULATED 3-JOINT LUSH FEATHERED 3D BIRD WINGS
# ==============================================================================

class WingTemplateBuilder:
    def __init__(self):
        self.uvs = []
        self.tris = []
        self.feathers = []
        self.arm_rings = []
        self._build_topology()

    def _add_arm_tube(self, side):
        N_ST = 7
        N_RING = 8
        base = len(self.uvs)
        for si in range(N_ST):
            u_s = 0.05 + 0.45 * (si / float(N_ST - 1))
            for ri in range(N_RING + 1):
                v_r = 0.58 + 0.38 * (ri / float(N_RING))
                self.uvs.append((u_s, v_r))
        for si in range(N_ST - 1):
            r0 = base + si * (N_RING + 1)
            r1 = r0 + (N_RING + 1)
            for k in range(N_RING):
                a, b, c, d = r0 + k, r0 + k + 1, r1 + k + 1, r1 + k
                if side > 0:
                    self.tris.append((a, b, c))
                    self.tris.append((a, c, d))
                else:
                    self.tris.append((a, c, b))
                    self.tris.append((a, d, c))
        tip_i = len(self.uvs)
        self.uvs.append((0.48, 0.78))
        r_last = base + (N_ST - 1) * (N_RING + 1)
        for k in range(N_RING):
            if side > 0:
                self.tris.append((r_last + k, r_last + k + 1, tip_i))
            else:
                self.tris.append((r_last + k + 1, r_last + k, tip_i))
        self.arm_rings.append(dict(side=side, base=base, n_st=N_ST, n_ring=N_RING))

    def _add_feather(self, spec):
        N_FS = 5
        base = len(self.uvs)
        is_scap = spec.get("scapular", False)
        if is_scap:
            u_l, u_q, u_r = 0.58, 0.76, 0.94
            v0, v1 = 0.58, 0.96
        else:
            u_l, u_q, u_r = 0.04, 0.44, 0.96
            v0, v1 = 0.02, 0.495

        self.uvs.append((u_q, v0))
        for si in range(N_FS):
            vf = v0 + (v1 - v0) * ((si + 1) / float(N_FS + 1))
            self.uvs.append((u_q, vf))
            self.uvs.append((u_l, vf))
            self.uvs.append((u_q, vf))
            self.uvs.append((u_r, vf))
        self.uvs.append((u_q, v1))

        r_idx = base
        t_idx = base + 1 + N_FS * 4
        flip = spec["side"] < 0
        for c in range(4):
            c1 = (c + 1) % 4
            tri = (r_idx, base + 1 + c, base + 1 + c1)
            self.tris.append((tri[0], tri[2], tri[1]) if flip else tri)
        for si in range(N_FS - 1):
            r0 = base + 1 + si * 4
            r1 = r0 + 4
            for c in range(4):
                c1 = (c + 1) % 4
                t1 = (r0 + c, r1 + c, r1 + c1)
                t2 = (r0 + c, r1 + c1, r0 + c1)
                if flip:
                    self.tris.append((t1[0], t1[2], t1[1]))
                    self.tris.append((t2[0], t2[2], t2[1]))
                else:
                    self.tris.append(t1)
                    self.tris.append(t2)
        last_r = base + 1 + (N_FS - 1) * 4
        for c in range(4):
            c1 = (c + 1) % 4
            tri = (last_r + c, t_idx, last_r + c1)
            self.tris.append((tri[0], tri[2], tri[1]) if flip else tri)

        spec["base"] = base
        self.feathers.append(spec)

    def _build_topology(self):
        for side in (1.0, -1.0):
            self._add_arm_tube(side)

            # 1. 10 Broad, Slotted Primary Flight Feathers (seg=2 hand wing)
            for i in range(10):
                f = i / 9.0
                self._add_feather(dict(
                    side=side,
                    seg=2,
                    pos_t=0.06 + 0.90 * f,
                    z_off=-0.08 + 0.04 * i,
                    x_off=-0.35 + 0.40 * f,
                    sweep_deg=-78.0 + 62.0 * (f ** 0.90),
                    dihedral_deg=-2.5 + 5.0 * f,
                    length=22.0 + 9.5 * math.sin((0.18 + 0.74 * f) * math.pi) - 2.2 * (f ** 4),
                    w_lead=1.55 * (1.0 - 0.30 * f),
                    w_trail=3.55 * (1.0 - 0.22 * f),
                    thick=0.52,
                    camber=1.05,
                    flex_gain=0.45 + 0.95 * (f ** 1.4),
                    twist_gain=0.35 + 0.85 * f,
                    emarginated=(i >= 5),
                ))

            # 2. Alula (3 thumb feathers at wrist leading edge)
            for i in range(3):
                f = i / 2.0
                self._add_feather(dict(
                    side=side,
                    seg=2,
                    pos_t=0.05 + 0.14 * f,
                    z_off=0.62 + 0.12 * i,
                    x_off=1.05,
                    sweep_deg=2.0 - 16.0 * f,
                    dihedral_deg=9.0 - 3.0 * f,
                    length=7.4 + 2.0 * f,
                    w_lead=0.92,
                    w_trail=1.75,
                    thick=0.40,
                    camber=0.50,
                    flex_gain=0.15,
                    twist_gain=0.20,
                    alula=True,
                ))

            # 3. 12 Lush Overlapping Secondary Flight Feathers (filling humerus + ulna chord seamlessly!)
            for i in range(12):
                f = i / 11.0
                seg = 0 if i < 3 else 1
                pt = (0.35 + 0.24 * i) if i < 3 else ((i - 2.5) / 9.8)
                self._add_feather(dict(
                    side=side,
                    seg=seg,
                    pos_t=min(0.96, pt),
                    z_off=-0.10 + 0.03 * (i % 3),
                    x_off=-0.50,
                    sweep_deg=-85.0 + 12.0 * f,
                    dihedral_deg=-3.5,
                    length=18.5 + 4.2 * math.sin((0.15 + 0.76 * f) * math.pi),
                    w_lead=1.85,
                    w_trail=3.85,
                    thick=0.54,
                    camber=1.15,
                    flex_gain=0.34,
                    twist_gain=0.32,
                ))

            # 4. Upper Greater & Median Coverts (16 broad shingled feathers)
            for row_i, (len_sc, z_lift, x_sh) in enumerate(((0.62, 0.58, 0.18), (0.42, 0.98, 0.75))):
                n_cov = 9 if row_i == 0 else 7
                for i in range(n_cov):
                    u_all = (i + 0.35) / float(n_cov)
                    if u_all < 0.34:
                        seg, pt = 0, u_all / 0.34
                    elif u_all < 0.74:
                        seg, pt = 1, (u_all - 0.34) / 0.40
                    else:
                        seg, pt = 2, (u_all - 0.74) / 0.34
                    self._add_feather(dict(
                        side=side,
                        seg=seg,
                        pos_t=min(0.92, pt),
                        z_off=z_lift + 0.04 * (i % 2),
                        x_off=x_sh,
                        sweep_deg=-78.0 + 36.0 * (u_all ** 1.3),
                        dihedral_deg=2.5 - 3.5 * row_i,
                        length=(17.0 + 3.4 * u_all) * len_sc,
                        w_lead=1.85,
                        w_trail=3.35,
                        thick=0.50,
                        camber=0.75,
                        flex_gain=0.15,
                        twist_gain=0.12,
                    ))

            # 5. Underwing Coverts / Lining (10 broad feathers visible from front/below!)
            for i in range(10):
                u_all = (i + 0.3) / 10.0
                if u_all < 0.36:
                    seg, pt = 0, u_all / 0.36
                elif u_all < 0.78:
                    seg, pt = 1, (u_all - 0.36) / 0.42
                else:
                    seg, pt = 2, (u_all - 0.78) / 0.28
                self._add_feather(dict(
                    side=side,
                    seg=seg,
                    pos_t=min(0.88, pt),
                    z_off=-0.62 - 0.03 * (i % 2),
                    x_off=0.22,
                    sweep_deg=-80.0 + 30.0 * (u_all ** 1.2),
                    dihedral_deg=-2.0,
                    length=11.0 + 2.6 * math.sin(u_all * math.pi),
                    w_lead=1.80,
                    w_trail=3.30,
                    thick=0.44,
                    camber=0.55,
                    flex_gain=0.12,
                    twist_gain=0.10,
                ))

            # 6. Scapular / Root Shoulder Plumage (6 soft feathers blending wing root into head!)
            for i in range(6):
                f = i / 5.0
                ang = (f - 0.5) * 1.45
                self._add_feather(dict(
                    side=side,
                    seg=0,
                    pos_t=0.02 + 0.18 * (i % 2),
                    z_off=1.05 * math.cos(ang),
                    x_off=0.75 * math.sin(ang),
                    sweep_deg=-84.0 + 22.0 * (f - 0.5),
                    dihedral_deg=10.0 * math.cos(ang),
                    length=8.2 + 1.6 * math.cos(ang),
                    w_lead=1.75,
                    w_trail=2.55,
                    thick=0.56,
                    camber=0.55,
                    flex_gain=0.06,
                    twist_gain=0.05,
                    scapular=True,
                ))

    def eval_frame(self, wing_pose, head_rot, head_pos):
        n_verts = len(self.uvs)
        V = np.zeros((n_verts, 3), dtype=np.float32)

        L_HUM = 13.5
        L_ULNA = 16.5
        L_HAND = 16.5

        for side in (1.0, -1.0):
            wp = wing_pose["L" if side > 0 else "R"]
            p0 = np.array([-3.2, side * 11.0, 2.6], dtype=np.float32)

            # Note: positive hum_pitch tilts leading edge UP (+Z) and trailing feathers DOWN (-Z),
            # presenting the broad lush feathered chord richly to front & 3/4 cameras!
            R0 = (
                rot_z(side * wp["hum_sweep"])
                @ rot_x(side * wp["hum_flap"])
                @ rot_y(-wp["hum_pitch"])
            )
            p1 = p0 + R0 @ np.array([0.0, side * L_HUM, 0.0], dtype=np.float32)

            R1 = R0 @ rot_z(side * wp["elbow_sweep"]) @ rot_x(side * wp["elbow_flap"]) @ rot_y(-wp["elbow_pitch"])
            p2 = p1 + R1 @ np.array([0.0, side * L_ULNA, 0.0], dtype=np.float32)

            R2 = R1 @ rot_z(side * wp["wrist_sweep"]) @ rot_x(side * wp["wrist_flap"]) @ rot_y(-wp["wrist_pitch"])
            p3 = p2 + R2 @ np.array([0.0, side * L_HAND, 0.0], dtype=np.float32)

            segs = [
                (p0, p1, R0, L_HUM),
                (p1, p2, R1, L_ULNA),
                (p2, p3, R2, L_HAND),
            ]

            arm = [a for a in self.arm_rings if a["side"] == side][0]
            arm_stations = [
                (0, 0.00, 2.35, 1.80),
                (0, 0.50, 2.05, 1.50),
                (0, 1.00, 1.80, 1.30),
                (1, 0.50, 1.55, 1.10),
                (1, 1.00, 1.35, 0.95),
                (2, 0.50, 1.05, 0.72),
                (2, 1.00, 0.58, 0.44),
            ]
            for si, (sg_i, st_t, rx_a, rz_a) in enumerate(arm_stations):
                sa, sb, sR, _ = segs[sg_i]
                cen = sa * (1.0 - st_t) + sb * st_t + sR @ np.array([0.55 * rx_a, 0.0, 0.10], dtype=np.float32)
                r0 = arm["base"] + si * (arm["n_ring"] + 1)
                for k in range(arm["n_ring"] + 1):
                    ang = 2.0 * math.pi * (k / float(arm["n_ring"]))
                    loc = np.array([rx_a * math.cos(ang), 0.0, rz_a * math.sin(ang)], dtype=np.float32)
                    V[r0 + k] = cen + sR @ loc
            tip_idx = arm["base"] + arm["n_st"] * (arm["n_ring"] + 1)
            V[tip_idx] = p3 + R2 @ np.array([0.35, side * 0.85, 0.0], dtype=np.float32)

            aero_load = wp["aero_load"]
            aero_twist = wp["aero_twist"]
            fold_amt = wp.get("fold", 0.0)

            for f in self.feathers:
                if f["side"] != side:
                    continue
                sa, sb, sR, _ = segs[f["seg"]]
                t_p = f["pos_t"]
                anchor = sa * (1.0 - t_p) + sb * t_p + sR @ np.array([f["x_off"], 0.0, f["z_off"]], dtype=np.float32)

                sw_rad = math.radians(f["sweep_deg"] - fold_amt * (24.0 if f["seg"] == 2 else 10.0))
                dh_rad = math.radians(f["dihedral_deg"] + (8.0 * wp.get("alula_open", 0.0) if f.get("alula") else 0.0))

                t_loc = np.array([
                    math.sin(sw_rad) * math.cos(dh_rad),
                    side * math.cos(sw_rad) * math.cos(dh_rad),
                    math.sin(dh_rad),
                ], dtype=np.float32)
                t_loc /= max(1e-6, float(np.linalg.norm(t_loc)))

                up_loc = np.array([0.0, 0.0, 1.0], dtype=np.float32)
                n_loc = up_loc - np.dot(up_loc, t_loc) * t_loc
                nl = float(np.linalg.norm(n_loc))
                n_loc = (n_loc / nl) if nl > 1e-5 else up_loc
                lead_loc = np.cross(n_loc, t_loc) * side
                lead_loc /= max(1e-6, float(np.linalg.norm(lead_loc)))

                T_w = sR @ t_loc
                N_w = sR @ n_loc
                L_w = sR @ lead_loc

                Lf = f["length"]
                wl = f["w_lead"]
                wt = f["w_trail"]
                thk = f["thick"]
                cmb = f["camber"]
                fg = f["flex_gain"]
                tg = f["twist_gain"]
                emarg = f.get("emarginated", False)

                b_idx = f["base"]
                V[b_idx] = anchor

                N_FS = 5
                for si in range(N_FS + 1):
                    s = (si + 1) / float(N_FS + 1)
                    bend_up = (aero_load * fg * 3.8 * (s ** 1.95)) - cmb * 0.85 * (s ** 1.5)
                    aft_curve = -cmb * 0.55 * (s ** 1.7)
                    c_pt = anchor + T_w * (Lf * s) + N_w * bend_up + L_w * aft_curve

                    if si == N_FS:
                        V[b_idx + 1 + N_FS * 4] = c_pt
                        break

                    tw_ang = aero_twist * tg * s
                    ct, st = math.cos(tw_ang), math.sin(tw_ang)
                    n_s = ct * N_w + st * L_w
                    l_s = -st * N_w + ct * L_w

                    prof = math.sin(min(1.0, s * 1.18) * math.pi * 0.78) * (1.0 - 0.36 * (s ** 2.6))
                    notch = (1.0 - 0.34 * smoothstep(0.52, 0.76, s)) if (emarg and s > 0.52) else 1.0

                    w_l = wl * prof * notch
                    w_t = wt * prof * notch
                    h_s = thk * (1.0 - 0.62 * (s ** 1.6))

                    vi = b_idx + 1 + si * 4
                    V[vi + 0] = c_pt + n_s * h_s
                    V[vi + 1] = c_pt + l_s * w_l - n_s * (0.18 * h_s)
                    V[vi + 2] = c_pt - n_s * (0.32 * h_s)
                    V[vi + 3] = c_pt - l_s * w_t - n_s * (0.42 * h_s)

        return (V @ head_rot.T) + head_pos[None, :]


# ==============================================================================
# 5. 5 SEAMLESS AVIAN FLIGHT & BREEZY HAIR ANIMATION CLIPS (72 FRAMES)
# ==============================================================================

def symmetric_wing(hum_flap, hum_sweep, hum_pitch, elbow_flap, elbow_sweep, elbow_pitch,
                   wrist_flap, wrist_sweep, wrist_pitch, aero_load, aero_twist, fold=0.0, alula_open=0.0, bank_asym=0.0):
    base_L = dict(
        hum_flap=hum_flap + bank_asym,
        hum_sweep=hum_sweep,
        hum_pitch=hum_pitch,
        elbow_flap=elbow_flap,
        elbow_sweep=elbow_sweep,
        elbow_pitch=elbow_pitch,
        wrist_flap=wrist_flap + 0.5 * bank_asym,
        wrist_sweep=wrist_sweep,
        wrist_pitch=wrist_pitch,
        aero_load=aero_load,
        aero_twist=aero_twist,
        fold=fold,
        alula_open=alula_open,
    )
    base_R = dict(base_L)
    base_R["hum_flap"] = hum_flap - bank_asym
    base_R["wrist_flap"] = wrist_flap - 0.5 * bank_asym
    return dict(L=base_L, R=base_R)


def eval_clip_pose(fi):
    if fi < 16:
        # Clip 1 (0..15): CRUISING BIRD FLAP & BREEZY HAIR
        u = (fi - 0) / 16.0
        ph = 2.0 * math.pi * u
        s1 = math.sin(ph)
        c1 = math.cos(ph)
        s_lag = math.sin(ph - 0.68)
        upstroke = max(0.0, c1)

        hum_flap = 0.64 * s1 + 0.06
        hum_sweep = 0.16 * c1 - 0.04
        # Positive pitch presents the lush feathered airfoil chord toward front/below!
        hum_pitch = 0.28 + 0.16 * max(0.0, -c1) - 0.22 * upstroke
        elbow_flap = 0.24 * s_lag - 0.12 * upstroke
        elbow_sweep = 0.18 - 0.42 * upstroke
        wrist_flap = 0.48 * math.sin(ph - 0.92) - 0.26 * upstroke
        wrist_sweep = -0.06 - 0.42 * upstroke
        wrist_pitch = 0.12 * max(0.0, -c1) - 0.28 * upstroke

        head_pos = np.array([0.6 * math.sin(ph + 0.4), 0.0, BASE_Z + 2.8 * math.sin(ph - 1.15)], dtype=np.float32)
        head_rot = rot_y(0.05 * math.cos(ph)) @ rot_x(0.03 * math.sin(ph))
        wind_cfg = dict(
            phase=ph,
            harm=2,
            breeze=0.92,
            flutter=1.08,
            gust_z=0.65 * max(0.0, -c1),
        )
        wing_pose = symmetric_wing(
            hum_flap, hum_sweep, hum_pitch,
            elbow_flap, elbow_sweep, 0.04,
            wrist_flap, wrist_sweep, wrist_pitch,
            aero_load=0.95 * max(0.0, -c1) - 0.40 * upstroke,
            aero_twist=0.58 * upstroke,
        )
        return f"fly_{fi:02d}", head_pos, head_rot, wind_cfg, wing_pose

    elif fi < 32:
        # Clip 2 (16..31): WINDY THERMAL SOAR / GLIDE
        k = fi - 16
        u = k / 16.0
        ph = 2.0 * math.pi * u
        bank = 0.19 * math.sin(ph)
        gust = 0.5 + 0.5 * math.sin(ph - 0.5)

        head_pos = np.array([
            1.2 * math.cos(ph),
            3.6 * math.sin(ph),
            BASE_Z + 2.2 + 2.4 * math.sin(ph + 0.7),
        ], dtype=np.float32)
        head_rot = rot_x(bank) @ rot_z(-0.10 * math.sin(ph)) @ rot_y(0.04 * math.cos(ph))
        wind_cfg = dict(
            phase=ph,
            harm=2,
            breeze=1.24 + 0.26 * gust,
            flutter=1.32,
            gust_z=0.35 * math.sin(2.0 * ph),
        )
        wing_pose = symmetric_wing(
            hum_flap=0.12 + 0.06 * math.sin(2.0 * ph),
            hum_sweep=0.08,
            hum_pitch=0.26,
            elbow_flap=0.05 * math.cos(2.0 * ph),
            elbow_sweep=0.22,
            elbow_pitch=0.05,
            wrist_flap=0.10 + 0.07 * math.sin(2.0 * ph - 0.6),
            wrist_sweep=-0.04,
            wrist_pitch=0.06,
            aero_load=0.78 + 0.22 * math.sin(2.0 * ph),
            aero_twist=0.08 * math.cos(2.0 * ph),
            bank_asym=-0.12 * math.cos(ph),
        )
        return f"soar_{k:02d}", head_pos, head_rot, wind_cfg, wing_pose

    elif fi < 48:
        # Clip 3 (32..47): RAPID HOVER FLUTTER
        k = fi - 32
        u = k / 16.0
        ph = 4.0 * math.pi * u
        ph1 = 2.0 * math.pi * u
        s1, c1 = math.sin(ph), math.cos(ph)

        head_pos = np.array([
            -0.8 * math.cos(ph),
            0.9 * math.sin(ph1),
            BASE_Z + 1.5 + 1.6 * math.sin(ph - 0.9),
        ], dtype=np.float32)
        head_rot = rot_y(-0.08 + 0.04 * s1) @ rot_z(0.06 * math.sin(ph1))
        wind_cfg = dict(
            phase=ph1,
            harm=3,
            breeze=0.92,
            flutter=1.45,
            gust_z=0.85 * s1,
        )
        wing_pose = symmetric_wing(
            hum_flap=0.52 * s1 + 0.20,
            hum_sweep=0.44 * c1 + 0.08,
            hum_pitch=0.46 + 0.22 * s1,
            elbow_flap=0.26 * math.sin(ph - 0.55),
            elbow_sweep=0.16 - 0.22 * max(0.0, -s1),
            elbow_pitch=0.12 * c1,
            wrist_flap=0.44 * math.sin(ph - 0.95),
            wrist_sweep=-0.10 - 0.22 * max(0.0, -s1),
            wrist_pitch=0.28 * c1,
            aero_load=0.85 * abs(c1),
            aero_twist=0.52 * max(0.0, -s1),
            alula_open=0.85,
        )
        return f"hov_{k:02d}", head_pos, head_rot, wind_cfg, wing_pose

    elif fi < 60:
        # Clip 4 (48..59): PEREGRINE SWOOP / DIVE
        k = fi - 48
        u = k / 12.0
        ph = 2.0 * math.pi * u
        flare = max(0.0, math.sin(ph - 1.2))

        head_pos = np.array([
            2.4 * math.sin(ph),
            0.0,
            BASE_Z + 4.5 * math.cos(ph),
        ], dtype=np.float32)
        head_rot = rot_y(0.22 - 0.28 * flare) @ rot_x(0.06 * math.sin(ph))
        wind_cfg = dict(
            phase=ph,
            harm=2,
            breeze=1.50,
            flutter=1.22,
            gust_z=0.45 * flare,
        )
        wing_pose = symmetric_wing(
            hum_flap=-0.04 + 0.38 * flare,
            hum_sweep=-0.34 + 0.42 * flare,
            hum_pitch=0.16 + 0.34 * flare,
            elbow_flap=-0.08 + 0.24 * flare,
            elbow_sweep=0.30 - 0.10 * flare,
            elbow_pitch=0.04,
            wrist_flap=-0.15 + 0.42 * flare,
            wrist_sweep=-0.72 + 0.58 * flare,
            wrist_pitch=0.08 + 0.18 * flare,
            aero_load=0.45 + 0.75 * flare,
            aero_twist=0.10,
            alula_open=0.75 * flare,
        )
        return f"dive_{k:02d}", head_pos, head_rot, wind_cfg, wing_pose

    else:
        # Clip 5 (60..71): FOLDED-WING PERCH IN THE BREEZE (True avian Z-fold tucked down & aft!)
        k = fi - 60
        u = k / 12.0
        ph = 2.0 * math.pi * u
        breath = math.sin(ph)

        head_pos = np.array([
            0.0,
            0.0,
            BASE_Z - 13.0 + 0.65 * breath,
        ], dtype=np.float32)
        head_rot = rot_z(0.11 * math.sin(ph)) @ rot_x(0.055 * math.cos(ph)) @ rot_y(-0.03 * breath)
        wind_cfg = dict(
            phase=ph,
            harm=1,
            breeze=0.62 + 0.15 * breath,
            flutter=0.82,
            gust_z=0.18 * breath,
        )
        # Humerus sweeps aft & down alongside skull; forearm folds forward/up; hand & primaries sweep sleekly down-aft!
        wing_pose = symmetric_wing(
            hum_flap=-0.78 + 0.03 * breath,
            hum_sweep=-0.72,
            hum_pitch=0.35,
            elbow_flap=0.55,
            elbow_sweep=1.42,
            elbow_pitch=-0.12,
            wrist_flap=-0.42,
            wrist_sweep=-1.68,
            wrist_pitch=0.15,
            aero_load=0.05,
            aero_twist=0.0,
            fold=1.0,
        )
        return f"perch_{k:02d}", head_pos, head_rot, wind_cfg, wing_pose


# ==============================================================================
# 6. SOFTWARE PREVIEW RENDERER (FOR VISUAL VERIFICATION & SHOWCASE THUMBNAILS)
# ==============================================================================

def render_preview_tile(surfaces_data, tex_map, fi, az_deg, el_deg, dist=138.0, tgt_z=48.0, tile_w=420, tile_h=340):
    img = np.zeros((tile_h, tile_w, 3), dtype=np.float32)
    gy = np.linspace(0.0, 1.0, tile_h, dtype=np.float32)[:, None]
    img[..., 0] = 18.0 + 26.0 * (1.0 - gy)
    img[..., 1] = 36.0 + 50.0 * (1.0 - gy)
    img[..., 2] = 68.0 + 70.0 * (1.0 - gy)
    zbuf = np.full((tile_h, tile_w), 1e9, dtype=np.float32)

    az, el = math.radians(az_deg), math.radians(el_deg)
    tgt = np.array([0.0, 0.0, tgt_z], dtype=np.float32)
    eye = tgt + dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)], dtype=np.float32)
    fwd = tgt - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0], dtype=np.float32))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    fov_scale = (tile_h * 0.5) / math.tan(math.radians(23.0))
    L1 = np.array([0.55, -0.38, 0.74], dtype=np.float32)
    L1 /= np.linalg.norm(L1)
    L2 = np.array([-0.62, 0.52, 0.58], dtype=np.float32)
    L2 /= np.linalg.norm(L2)

    for s in surfaces_data:
        tex = tex_map[s["shader"]]
        th, tw = tex.shape[:2]
        vv, nn = s["frames"][fi]
        V = np.asarray(vv, dtype=np.float32)
        N = np.asarray(nn, dtype=np.float32)
        UV = np.asarray(s["st"], dtype=np.float32)

        rel = V - eye[None, :]
        cz = rel @ fwd
        cx = rel @ right
        cy = rel @ up
        sx = (tile_w * 0.5) + (cx / np.maximum(cz, 1.0)) * fov_scale
        sy = (tile_h * 0.5) - (cy / np.maximum(cz, 1.0)) * fov_scale

        lit = 0.40 + 0.66 * np.maximum(0.0, N @ L1) + 0.28 * np.maximum(0.0, N @ L2)

        for i0, i1, i2 in s["tris"]:
            if cz[i0] < 4.0 or cz[i1] < 4.0 or cz[i2] < 4.0:
                continue
            x0, y0 = sx[i0], sy[i0]
            x1, y1 = sx[i1], sy[i1]
            x2, y2 = sx[i2], sy[i2]
            denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(denom) < 1e-4:
                continue

            ix0 = max(0, int(math.floor(min(x0, x1, x2))))
            ix1 = min(tile_w - 1, int(math.ceil(max(x0, x1, x2))))
            iy0 = max(0, int(math.floor(min(y0, y1, y2))))
            iy1 = min(tile_h - 1, int(math.ceil(max(y0, y1, y2))))
            if ix0 > ix1 or iy0 > iy1:
                continue

            px, py = np.meshgrid(
                np.arange(ix0, ix1 + 1, dtype=np.float32) + 0.5,
                np.arange(iy0, iy1 + 1, dtype=np.float32) + 0.5,
            )
            w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
            w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not inside.any():
                continue

            z = w0 * cz[i0] + w1 * cz[i1] + w2 * cz[i2]
            sub_z = zbuf[iy0:iy1 + 1, ix0:ix1 + 1]
            vis = inside & (z < sub_z)
            if not vis.any():
                continue

            sub_z[vis] = z[vis]
            u = (w0[vis] * UV[i0, 0] + w1[vis] * UV[i1, 0] + w2[vis] * UV[i2, 0]) % 1.0
            v = np.clip(w0[vis] * UV[i0, 1] + w1[vis] * UV[i1, 1] + w2[vis] * UV[i2, 1], 0.0, 1.0)
            tx = np.clip((u * (tw - 1)).astype(np.int32), 0, tw - 1)
            ty = np.clip((v * (th - 1)).astype(np.int32), 0, th - 1)
            shade = (w0[vis] * lit[i0] + w1[vis] * lit[i1] + w2[vis] * lit[i2])[:, None]
            if denom > 0:
                shade = np.maximum(shade, 0.55)
            sub_img = img[iy0:iy1 + 1, ix0:ix1 + 1]
            sub_img[vis] = np.clip(tex[ty, tx] * shade, 0.0, 255.0)

    return Image.fromarray(img.astype(np.uint8))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)

    print("1. Loading uploaded green-screen portrait & despilling...", flush=True)
    front_rgb, front_mask = load_and_despill_front()

    print("2. Reconstructing 3D anatomical head & baking 1024x1024 seamless skin...", flush=True)
    head_data = build_base_head(front_rgb, front_mask)
    head_tex_p = os.path.join(PROGS_DIR, "john_bird_head.png")
    head_data["head_tex"].save(head_tex_p, optimize=True)
    head_data["head_tex"].save(os.path.join(OUT_DIR, "john_bird_head.png"), optimize=True)

    print("3. Synthesizing real-photo 3D hair lock texture & avian feather atlases...", flush=True)
    hair_tex = build_hair_strand_texture(front_rgb)
    hair_tex_p = os.path.join(PROGS_DIR, "john_bird_hair.png")
    hair_tex.save(hair_tex_p, optimize=True)
    hair_tex.save(os.path.join(OUT_DIR, "john_bird_hair.png"), optimize=True)

    wing_hawk = build_feather_atlas(front_rgb, variant="hawk")
    wing_hawk_p = os.path.join(PROGS_DIR, "john_bird_wings.png")
    wing_hawk.save(wing_hawk_p, optimize=True)
    wing_hawk.save(os.path.join(OUT_DIR, "john_bird_wings.png"), optimize=True)

    wing_white = build_feather_atlas(front_rgb, variant="white")
    wing_white_p = os.path.join(OUT_DIR, "john_bird_wings_white.png")
    wing_white.save(wing_white_p, optimize=True)

    print("4. Sculpting 64 sleek breezy 3D hair locks & articulated 3-joint feathered bird wings...", flush=True)
    hair_locks, hair_uvs, hair_tris = build_hair_locks_spec(head_data["grid_pos"])
    wing_builder = WingTemplateBuilder()

    head_v0 = head_data["verts"]
    head_tris = head_data["tris"]
    ring_meta = head_data["ring_meta"]

    head_frames = []
    hair_frames = []
    wing_frames = []
    frame_names = []

    print(f"5. Animating {TOTAL_FRAMES} seamless frames across 5 flight & breeze clips...", flush=True)
    for fi in range(TOTAL_FRAMES):
        fname, h_pos, h_rot, wind_cfg, wing_pose = eval_clip_pose(fi)
        frame_names.append(fname)

        tj = ring_meta[:, 0]
        th_k = ring_meta[:, 1]
        hw_rip = ring_meta[:, 2]
        ph = wind_cfg["phase"] * wind_cfg["harm"]
        rip = hw_rip * wind_cfg["flutter"] * 0.36 * np.sin(ph - 2.5 * tj + 2.0 * th_k)
        hv = head_v0.copy()
        hv[:, 0] -= hw_rip * wind_cfg["breeze"] * 0.48
        hv[:, 1] += rip * np.cos(th_k)
        hv[:, 2] += np.abs(rip) * 0.55
        hv_world = (hv @ h_rot.T) + h_pos[None, :]
        hn_world = compute_vertex_normals(hv_world, head_tris)
        head_frames.append(([tuple(map(float, p)) for p in hv_world], [tuple(map(float, n)) for n in hn_world]))

        hr_world = eval_hair_locks_frame(hair_locks, wind_cfg, h_rot, h_pos)
        hr_norms = compute_vertex_normals(hr_world, hair_tris)
        hair_frames.append(([tuple(map(float, p)) for p in hr_world], [tuple(map(float, n)) for n in hr_norms]))

        wg_world = wing_builder.eval_frame(wing_pose, h_rot, h_pos)
        wg_norms = compute_vertex_normals(wg_world, wing_builder.tris)
        wing_frames.append(([tuple(map(float, p)) for p in wg_world], [tuple(map(float, n)) for n in wg_norms]))

    surfaces = [
        dict(name="head", shader="progs/john_bird_head", tris=head_tris, st=head_data["uvs"], frames=head_frames),
        dict(name="hair_breezy", shader="progs/john_bird_hair", tris=hair_tris, st=hair_uvs, frames=hair_frames),
        dict(name="wings_bird", shader="progs/john_bird_wings", tris=wing_builder.tris, st=wing_builder.uvs, frames=wing_frames),
    ]

    md3_path = os.path.join(PROGS_DIR, "john_bird_head.md3")
    md3lib.write(md3_path, dict(name="progs/john_bird_head.md3", surfaces=surfaces, frame_names=frame_names))
    shutil.copyfile(md3_path, os.path.join(OUT_DIR, "john_bird_head.md3"))

    skin_txt = (
        "head,progs/john_bird_head.png\n"
        "hair_breezy,progs/john_bird_hair.png\n"
        "wings_bird,progs/john_bird_wings.png\n"
    )
    open(os.path.join(PROGS_DIR, "john_bird_head_0.skin"), "w", encoding="utf-8").write(skin_txt)

    tot_v = sum(len(s["st"]) for s in surfaces)
    tot_t = sum(len(s["tris"]) for s in surfaces)
    print(f"   Wrote {md3_path} ({os.path.getsize(md3_path)/1e6:.2f} MB) | {tot_v} verts, {tot_t} tris, {TOTAL_FRAMES} frames")
    for s in surfaces:
        print(f"     - {s['name']:12s}: {len(s['st']):4d} verts, {len(s['tris']):4d} tris, shader={s['shader']}")

    print("6. Rendering showcase angle tiles & verification sheet...", flush=True)
    tex_np = {
        "progs/john_bird_head": np.asarray(head_data["head_tex"], dtype=np.float32),
        "progs/john_bird_hair": np.asarray(hair_tex, dtype=np.float32),
        "progs/john_bird_wings": np.asarray(wing_hawk, dtype=np.float32),
    }

    tile_specs = [
        ("t0_hero_flap.png",   "3/4 Cruising Wingbeat & Breeze",  3,  28,  14, 146.0, 49.0),
        ("t1_closeup_hair.png","Close-Up: Breezy Flapping Hair",  5,  16,   9,  68.0, 51.0),
        ("t2_side_profile.png","Side Profile: 3D Relief & Wing",  3, -72,  14, 138.0, 49.0),
        ("t3_rear_roots.png",  "Rear Skull & Feathered Roots",   11, 152,  18, 142.0, 49.0),
        ("t4_upstroke.png",    "Feathered Upstroke Recovery",    12,  32,  15, 146.0, 48.0),
        ("t5_soar_glide.png",  "Windy Thermal Soar / Glide",     20,  26,  20, 156.0, 50.0),
        ("t6_hover_scull.png", "Rapid Hover Sculling & Gust",    35,  34,  15, 146.0, 49.0),
        ("t7_perch_fold.png",  "Folded-Wing Perch in Breeze",    63,  34,  14,  92.0, 35.0),
    ]

    tiles = []
    for fn, lbl, fi_t, az_t, el_t, dist_t, tz_t in tile_specs:
        im_t = render_preview_tile(surfaces, tex_np, fi=fi_t, az_deg=az_t, el_deg=el_t, dist=dist_t, tgt_z=tz_t)
        im_t.save(os.path.join(OUT_DIR, fn), optimize=True)
        tiles.append((im_t, lbl))

    sheet = Image.new("RGB", (420 * 4, 340 * 2), (10, 15, 25))
    dr = ImageDraw.Draw(sheet)
    for idx, (im_t, lbl) in enumerate(tiles):
        gx, gy_p = (idx % 4) * 420, (idx // 4) * 340
        sheet.paste(im_t, (gx, gy_p))
        dr.rectangle([gx + 8, gy_p + 8, gx + 315, gy_p + 30], fill=(10, 16, 28))
        dr.text((gx + 14, gy_p + 13), lbl, fill=(255, 200, 90) if idx < 4 else (110, 231, 183))

    verify_p = os.path.join(OUT_DIR, "john_bird_verify.png")
    sheet.save(verify_p)
    print(f"   Saved verification sheet: {verify_p}", flush=True)


if __name__ == "__main__":
    main()
