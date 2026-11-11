"""Multi-View Photographic & Procedural Texture Builder for THE ERIC DEASON CANNON.

Extracts real high-resolution photographic skin, facial features, hair, and giant ear
anatomy directly from the calibrated 1168x768 360-degree studio turntable frames
(`frame_240` 0-deg front, `frame_001` closeup hero, `frame_087` 90-deg left profile,
`frame_185` 270-deg right profile, `frame_137` 180-deg rear), and synthesizes weathered
olive-drab launcher armor, tactical webbing/buckles, decals, and additive blast FX:

  1. `eric_cannon_head.png`  (1024x1024): Seamless 360-deg cylindrical unwrap of Eric's head
  2. `eric_cannon_ears.png`  (1024x1024): Front (left half) + Back (right half) giant ear photo atlas
  3. `eric_cannon_metal.png` (1024x1024): Olive tube, black muzzle collar, rear bore, DALUCTION &
                                          triangle hazard decals, webbing straps, buckles, cast tripod
  4. `eric_cannon_fx.png`    (512x512)  : Starburst flash, Mach shockwave ring, rocket jetcone & steam
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import ndimage


HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "eric_cannon")
REF_FRAMES = os.path.join(OUT_ROOT, "ref", "video_frames")
STAGE_TEX = os.path.join(OUT_ROOT, "textures")
PROGS_DIR = os.path.join(MOD_ROOT, "progs")

# Canonical UV Rectangles on `eric_cannon_metal.png` (u0, v0, u1, v1)
UV_OLIVE_TUBE      = (0.02, 0.02, 0.48, 0.46)
UV_BLACK_COLLAR    = (0.52, 0.02, 0.98, 0.23)
UV_REAR_BORE       = (0.52, 0.25, 0.74, 0.47)
UV_TRUNNION_HUB    = (0.76, 0.25, 0.98, 0.47)
UV_DECAL_DALUCTION = (0.02, 0.50, 0.48, 0.72)
UV_DECAL_HAZARD    = (0.52, 0.50, 0.74, 0.72)
UV_WEBBING_STRAP   = (0.76, 0.50, 0.98, 0.72)
UV_BUCKLE_POLY     = (0.02, 0.75, 0.26, 0.98)
UV_CAST_OLIVE      = (0.28, 0.75, 0.98, 0.98)

# Canonical UV Rectangles on `eric_cannon_fx.png`
UV_FX_STARBURST = (0.02, 0.02, 0.48, 0.48)
UV_FX_SHOCKRING = (0.52, 0.02, 0.98, 0.48)
UV_FX_JETFLAME  = (0.02, 0.52, 0.48, 0.98)
UV_FX_STEAM     = (0.52, 0.52, 0.98, 0.98)


def smoothstep(a, b, x):
    u = np.clip((x - a) / np.maximum(1e-8, b - a), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def bleed_rgb(rgb, mask, erode_px=3):
    core = ndimage.binary_erosion(mask, iterations=erode_px) if erode_px > 0 else mask
    if not core.any():
        core = mask
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    return rgb[idx[0], idx[1]]


def _font(size, prefer=("ariblk.ttf", "impact.ttf", "tahomabd.ttf", "arialbd.ttf", "consolab.ttf")):
    for nm in prefer:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=101, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        wt = 0.5 ** i
        grid = rng.random((max(2, freq), max(2, freq)), dtype=np.float32)
        up = np.asarray(
            Image.fromarray((grid * 255.0).astype(np.uint8), mode="L").resize((w, h), Image.BICUBIC),
            dtype=np.float32,
        ) / 255.0
        acc += up * wt
        tw += wt
    acc /= max(tw, 1e-6)
    return acc


def load_ref_frame(fidx):
    p = os.path.join(REF_FRAMES, f"frame_{fidx:03d}.png")
    im = Image.open(p).convert("RGB")
    return np.asarray(im, dtype=np.float32)


# ==============================================================================
# 1. ERIC DEASON 360-DEG MULTI-VIEW HEAD TEXTURE (`eric_cannon_head.png`)
# ==============================================================================
def build_head_texture(stage_dir):
    """Unwraps Eric's head onto a 1024x1024 cylindrical map:
      u = 0.5 + atan2(y, x) / (2 * pi):
        u = 0.00 / 1.00 -> -X (back of head / occiput)
        u = 0.25        -> -Y (Eric's right cheek, viewer's left in f240)
        u = 0.50        -> +X (dead-center front face: eyes, nose, snarling teeth, bangs)
        u = 0.75        -> +Y (Eric's left cheek, viewer's right in f240)
      v in [0..1]:
        v = 0.00        -> top of crown (+Z)
        v = 1.00        -> bottom of chin / neck base (-Z)
    """
    W, H = 1024, 1024
    f240 = load_ref_frame(240)   # Dead-on 0 deg front (eye midpoint x=584, crown y=92, chin y=326)

    y_top_f, y_bot_f = 92.0, 326.0
    x_ctr_f = 584.0

    # Sample authentic pore-rich cheek skin directly from Eric's clean left & right cheeks in f240
    cheek_patch_l = f240[214:272, 536:562]
    cheek_patch_r = f240[214:272, 608:642]
    front_skin_med = 0.5 * (np.median(cheek_patch_l, axis=(0, 1)) + np.median(cheek_patch_r, axis=(0, 1)))

    # Tileable organic cheek/jaw/neck skin texture matched to Eric's exact complexion & pore/blemish contrast
    pore_f1 = _fbm(H, W, seed=44, octaves=(18, 36, 72, 144))
    pore_f2 = _fbm(H, W, seed=91, octaves=(6, 12, 24))
    speck   = _fbm(H, W, seed=133, octaves=(28, 56, 112))
    pore_delta = (pore_f1 - 0.5) * 19.0 + (pore_f2 - 0.5) * 14.0

    # Synthesize dense realistic short chestnut-espresso hair for crown, temples, and occiput
    hair_patch = f240[102:145, 542:626]
    hair_dark = np.percentile(hair_patch.reshape(-1, 3), 20, axis=0)
    hair_mid  = np.percentile(hair_patch.reshape(-1, 3), 58, axis=0)
    hair_hi   = np.percentile(hair_patch.reshape(-1, 3), 88, axis=0)

    rng = np.random.default_rng(73)
    s1 = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), sigma=(18.0, 1.4))
    s2 = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), sigma=(6.5, 0.8))
    strands = np.clip(0.5 + 0.30 * (s1 / (s1.std() + 1e-6)) + 0.20 * (s2 / (s2.std() + 1e-6)), 0.0, 1.0)
    hair_layer = (
        hair_dark[None, None, :] * (1.0 - strands[..., None])
        + hair_mid[None, None, :] * strands[..., None]
        + hair_hi[None, None, :] * (np.maximum(0.0, strands - 0.65) * 0.85)[..., None]
    )

    uu = (np.arange(W, dtype=np.float32) + 0.5) / W
    vv = (np.arange(H, dtype=np.float32) + 0.5) / H
    UU, VV = np.meshgrid(uu, vv)
    # phi = 0 at u=0.5 (+X front), -pi/2 at u=0.25 (-Y viewer left), +pi/2 at u=0.75 (+Y viewer right)
    PHI = (UU - 0.5) * (2.0 * math.pi)
    cos_phi = np.cos(PHI)
    sin_phi = np.sin(PHI)
    abs_phi = np.abs(PHI)

    # Sample Front Projection symmetrically inside strap-free face zone (531..637 in f240)
    fx_map = x_ctr_f + np.clip(sin_phi / 0.76, -1.0, 1.0) * 53.0
    fy_map = y_top_f + VV * (y_bot_f - y_top_f)
    front_samp = np.stack([
        ndimage.map_coordinates(f240[..., c], [fy_map, fx_map], order=1, mode="nearest")
        for c in range(3)
    ], axis=-1)

    # Seamless 3D Side & Back Skin + Hair Layer:
    t_back = 0.5 * (1.0 - cos_phi)  # 0 at front, 0.5 at +-90 deg sides, 1.0 at 180 deg back
    vert_shade = 1.03 - 0.14 * smoothstep(0.58, 0.98, VV) - 0.09 * smoothstep(0.25, 0.95, t_back)
    skin_base = front_skin_med[None, None, :] * vert_shade[..., None]
    rosy = np.exp(-(((VV - 0.58) / 0.19) ** 2)) * (0.35 + 0.55 * np.abs(sin_phi))
    blemish = np.maximum(0.0, speck - 0.66) * 28.0 * smoothstep(0.38, 0.62, VV) * (1.0 - smoothstep(0.80, 0.94, VV))
    skin_base[..., 0] += 7.5 * rosy + 0.55 * blemish
    skin_base[..., 1] -= 2.5 * rosy + 0.45 * blemish
    skin_base[..., 2] -= 2.0 * rosy + 0.45 * blemish
    skin_layer = np.clip(skin_base + pore_delta[..., None], 0, 255)

    # Monotonic natural bowl-fringe -> temple -> nape hairline curve
    hairline_v = 0.235 + 0.44 * (t_back ** 1.55)
    is_hair = 1.0 - smoothstep(hairline_v - 0.032, hairline_v + 0.042, VV)
    side_back_samp = hair_layer * is_hair[..., None] + skin_layer * (1.0 - is_hair[..., None])

    # Oval clean-face mask so w_front feathers to 0 BEFORE fx_map ever touches straps, outer brow tip, or chin background!
    jaw_narrow = 0.16 * smoothstep(0.68, 0.94, VV) + 0.22 * (1.0 - smoothstep(0.08, 0.24, VV))
    phi_inner = 0.56 - jaw_narrow
    phi_outer = 0.79 - jaw_narrow
    w_ang = 1.0 - smoothstep(phi_inner, phi_outer, abs_phi)
    w_top = smoothstep(0.03, 0.10, VV)
    w_bot = 1.0 - smoothstep(0.90, 0.98, VV)
    w_front = w_ang * w_top * w_bot

    head_rgb = front_samp * w_front[..., None] + side_back_samp * (1.0 - w_front[..., None])

    # Top crown cap (VV < 0.09) is seamless dark brown hair all 360 deg around
    crown_w = 1.0 - smoothstep(0.02, 0.09, VV)
    head_rgb = head_rgb * (1.0 - crown_w[..., None]) + hair_layer * crown_w[..., None]

    # Crisp unsharp micro-detail boost on the front face (eyes, teeth, brows, pores!)
    im_stage = Image.fromarray(np.clip(head_rgb, 0, 255).astype(np.uint8), mode="RGB")
    im_sharp = im_stage.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
    p_out = os.path.join(stage_dir, "eric_cannon_head.png")
    im_sharp.save(p_out, "PNG", optimize=True)
    return p_out


# ==============================================================================
# 2. GIANT HUMAN EARS PHOTOGRAPHIC ATLAS (`eric_cannon_ears.png`)
# ==============================================================================
def build_ears_texture(stage_dir):
    """1024x1024 Giant Ear Photographic Atlas:
      Left Half  u=[0.0..0.5], v=[0.0..1.0]: Real high-res front ear from f001 (x=656..836, y=102..382),
                                             cleanly masked & edge-bled so zero background fringe exists!
                                             u=0.02 is inner ear root (tragus/cheek side), u=0.48 is outer helix rim!
      Right Half u=[0.5..1.0], v=[0.0..1.0]: Real back-of-ear fleshy pink skin from f137 (x=402..498, y=152..340),
                                             color-matched to front helix rim for seamless wrap-around!
    """
    W, H = 1024, 1024
    f001 = load_ref_frame(1)
    f137 = load_ref_frame(137)

    # Extract f001 left-viewer giant ear (Eric's right ear): x=654..836, y=102..382
    # Note: in f001, outer helix rim is on the LEFT (x=656), inner root/tragus is on the RIGHT (x=822, next to strap x>=824).
    ear_crop = f001[100:386, 654:836].copy()   # (286, 182, 3)
    eh, ew, _ = ear_crop.shape
    yy, xx = np.mgrid[0:eh, 0:ew]

    # Segment warm fleshy pink/tan ear skin vs dark black muzzle collar (on left) & olive strap (on right) & white bg (top)
    r, g, b = ear_crop[..., 0], ear_crop[..., 1], ear_crop[..., 2]
    skin_warmth = r - 0.5 * (g + b)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    not_white_bg = luma < 244.0
    not_dark_metal = (skin_warmth > 13.5) & (r > 72.0)
    # Exclude strap pixels on far right (xx > 154 where green >= red - 8)
    not_strap = ~((xx > 142) & (skin_warmth < 22.0))
    ear_mask = not_white_bg & not_dark_metal & not_strap
    ear_mask = ndimage.binary_closing(ear_mask, iterations=3)
    ear_mask = ndimage.binary_fill_holes(ear_mask)
    lab, nlab = ndimage.label(ear_mask)
    if nlab > 0:
        sizes = ndimage.sum(ear_mask, lab, range(1, nlab + 1))
        ear_mask = lab == (1 + int(np.argmax(sizes)))
    ear_mask = ndimage.binary_erosion(ear_mask, iterations=2)

    # Flip horizontally so u_local=0 is INNER ROOT (tragus/head attachment) and u_local=1 is OUTER HELIX RIM!
    ear_bled = bleed_rgb(ear_crop, ear_mask, erode_px=3)[:, ::-1, :]
    front_half = Image.fromarray(np.clip(ear_bled, 0, 255).astype(np.uint8)).resize((W // 2, H), Image.LANCZOS)
    front_half = front_half.filter(ImageFilter.UnsharpMask(radius=1.3, percent=45, threshold=2))

    # Extract f137 rear ear skin: x=402..498, y=152..340
    back_crop = f137[150:342, 400:498].copy()
    br, bg_c, bb = back_crop[..., 0], back_crop[..., 1], back_crop[..., 2]
    b_warm = br - 0.5 * (bg_c + bb)
    b_mask = (b_warm > 12.0) & (br > 85.0) & (0.299 * br + 0.587 * bg_c + 0.114 * bb < 212.0)
    b_mask = ndimage.binary_fill_holes(ndimage.binary_closing(b_mask, iterations=2))
    b_bled = bleed_rgb(back_crop, b_mask, erode_px=3)   # outer rim on left -> flip so u_local=0 is root, u_local=1 is outer rim
    b_bled = b_bled[:, ::-1, :]

    # Match overall brightness/warmth of back skin to front helix rim
    front_arr = np.asarray(front_half, dtype=np.float32)
    rim_med = np.median(front_arr[200:800, 420:500], axis=(0, 1))
    back_med = np.median(b_bled, axis=(0, 1))
    b_matched = np.clip(b_bled * (rim_med / np.maximum(1.0, back_med))[None, None, :], 0, 255)
    back_half = Image.fromarray(b_matched.astype(np.uint8)).resize((W // 2, H), Image.BICUBIC)

    # Add subtle organic retroauricular vascular/pore micro-texture to back_half
    back_arr = np.asarray(back_half, dtype=np.float32)
    micro = (_fbm(H, W // 2, seed=211) - 0.5) * 9.0
    back_arr = np.clip(back_arr + micro[..., None], 0, 255)

    atlas = Image.new("RGB", (W, H))
    atlas.paste(front_half, (0, 0))
    atlas.paste(Image.fromarray(back_arr.astype(np.uint8)), (W // 2, 0))

    p_out = os.path.join(stage_dir, "eric_cannon_ears.png")
    atlas.save(p_out, "PNG", optimize=True)
    return p_out


# ==============================================================================
# 3. MILITARY OLIVE LAUNCHER, DECALS, WEBBING & TRIPOD (`eric_cannon_metal.png`)
# ==============================================================================
def build_metal_texture(stage_dir):
    W, H = 1024, 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[:] = [74.0, 81.0, 54.0]   # Base weathered olive-drab (#4a5136)

    n_fine = _fbm(H, W, seed=31, octaves=(8, 16, 32, 64, 128))
    n_chip = _fbm(H, W, seed=59, octaves=(12, 24, 48, 96))

    # --- Q1 Top-Left [0..512, 0..490]: Weathered Olive-Drab Launcher Tube ---
    h1, w1 = 490, 512
    yy, xx = np.mgrid[0:h1, 0:w1]
    lathe = 0.5 + 0.5 * np.sin(yy * 0.45)
    olive = np.zeros((h1, w1, 3), dtype=np.float32)
    olive[:] = [78.0, 85.0, 56.0]
    olive *= (0.88 + 0.22 * n_fine[:h1, :w1, None]) * (0.97 + 0.05 * lathe[..., None])
    # Realistic fine military paint micro-chips & rust specks (matching f185 / ref_photo_1!)
    n_micro = _fbm(H, W, seed=147, octaves=(32, 64, 128, 256))
    chips = (n_micro[:h1, :w1] > 0.785) & (n_chip[:h1, :w1] > 0.58)
    rust  = (n_micro[:h1, :w1] > 0.755) & (~chips) & (n_chip[:h1, :w1] > 0.56)
    olive[chips] = [46.0, 45.0, 40.0]
    olive[rust]  = [96.0, 70.0, 44.0]
    # Subtle circumferential panel seam lines
    for sy in (95, 215, 345, 430):
        olive[max(0, sy - 2):sy + 2, :] *= 0.62
        olive[min(h1 - 1, sy + 2):min(h1, sy + 5), :] *= 1.16
    arr[:h1, :w1] = olive

    # --- Top-Right Upper [512..1024, 0..245]: Matte Black Muzzle Collar, Gunmetal Lip & Deep Dark Bore ---
    h2, w2 = 245, 512
    blk = np.zeros((h2, w2, 3), dtype=np.float32)
    blk[:] = [38.0, 40.0, 39.0]
    # Rolled front muzzle lip highlight band (tv = 0.44..0.68 -> y = 108..166)
    lip_y = np.arange(h2, dtype=np.float32)[:, None, None]
    lip_hi = np.exp(-(((lip_y - 138.0) / 18.0) ** 2))
    bore_dk = smoothstep(170.0, 198.0, lip_y)
    blk = blk * (1.0 - 0.68 * bore_dk) + lip_hi * np.array([34.0, 36.0, 35.0], dtype=np.float32)
    blk *= (0.88 + 0.24 * n_fine[:h2, 512:, None])
    silver_scratches = (n_chip[:h2, 512:] > 0.785) & (lip_y[:, :, 0] < 175.0)
    blk[silver_scratches] = [112.0, 114.0, 110.0]
    arr[:h2, 512:] = blk

    # --- Rear Bore & Trunnion Hub [512..1024, 245..495] ---
    im_tmp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im_tmp)

    # Rear Venturi Bore (center (640, 370), r=112): matches f137 crisp steel 8-bolt inner ring + pitch-black bore!
    cx_b, cy_b = 640, 370
    dr.rectangle([512, 245, 768, 495], fill=(34, 36, 34))
    dr.ellipse([cx_b - 112, cy_b - 112, cx_b + 112, cy_b + 112], fill=(58, 62, 54), outline=(128, 134, 122), width=5)
    dr.ellipse([cx_b - 94, cy_b - 94, cx_b + 94, cy_b + 94], fill=(88, 94, 76), outline=(32, 34, 30), width=3)
    for bi in range(8):
        ang = bi * (2.0 * math.pi / 8.0) + 0.2
        bx = cx_b + 79.0 * math.cos(ang)
        by = cy_b + 79.0 * math.sin(ang)
        dr.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=(148, 152, 144), outline=(22, 24, 22), width=2)
    dr.ellipse([cx_b - 64, cy_b - 64, cx_b + 64, cy_b + 64], fill=(8, 9, 10), outline=(116, 122, 112), width=4)

    # Trunnion Bearing Hub Cap (center (896, 370), r=108): matches f185 circular bearing w/ 4 pin holes!
    cx_t, cy_t = 896, 370
    dr.rectangle([768, 245, 1024, 495], fill=(68, 74, 50))
    dr.ellipse([cx_t - 104, cy_t - 104, cx_t + 104, cy_t + 104], fill=(56, 61, 44), outline=(30, 33, 24), width=5)
    dr.ellipse([cx_t - 82, cy_t - 82, cx_t + 82, cy_t + 82], fill=(74, 80, 56), outline=(98, 104, 78), width=3)
    dr.ellipse([cx_t - 28, cy_t - 28, cx_t + 28, cy_t + 28], fill=(46, 50, 38), outline=(105, 110, 86), width=3)
    for bi in range(4):
        ang = bi * (math.pi / 2.0) + math.pi / 4.0
        bx = cx_t + 54.0 * math.cos(ang)
        by = cy_t + 54.0 * math.sin(ang)
        dr.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=(24, 26, 22), outline=(96, 102, 78), width=2)

    # --- DALUCTION / JOLLSZAX / SUSE AYEA Yellow Stencil Decal [0..512, 500..745] ---
    dr.rectangle([0, 500, 512, 745], fill=(76, 83, 55))
    # Outer yellow rounded-ish stencil box
    bx0, by0, bx1, by1 = 48, 526, 464, 720
    dr.rounded_rectangle([bx0, by0, bx1, by1], radius=12, fill=(224, 184, 26), outline=(24, 24, 20), width=6)
    # Top black header band inside box ("DALUCTION")
    dr.rounded_rectangle([bx0 + 6, by0 + 6, bx1 - 6, by0 + 74], radius=6, fill=(24, 25, 22))
    f_hdr = _font(48)
    f_sub = _font(36)
    dr.text((bx0 + 52, by0 + 13), "DALUCTION", fill=(232, 192, 34), font=f_hdr)
    dr.text((bx0 + 88, by0 + 88), "JOLLSZAX", fill=(26, 26, 20), font=f_sub)
    dr.text((bx0 + 82, by0 + 136), "SUSE AYEA", fill=(26, 26, 20), font=f_sub)

    # --- Yellow Hazard Warning Triangle Decal [512..768, 500..745] ---
    dr.rectangle([512, 500, 768, 745], fill=(76, 83, 55))
    tri_pts = [(640, 528), (742, 706), (538, 706)]
    dr.polygon(tri_pts, fill=(228, 188, 28), outline=(20, 20, 18))
    # Thick black inner triangle border + rocket/burst icon inside (matching ref_photo_1!)
    tri_in = [(640, 546), (726, 696), (554, 696)]
    dr.line([tri_pts[0], tri_pts[1], tri_pts[2], tri_pts[0]], fill=(20, 20, 18), width=9)
    dr.line([tri_in[0], tri_in[1], tri_in[2], tri_in[0]], fill=(20, 20, 18), width=4)
    # Burst glyph inside hazard triangle
    dr.polygon([(640, 668), (626, 616), (640, 628), (654, 616)], fill=(20, 20, 18))
    dr.line([(640, 676), (612, 640)], fill=(20, 20, 18), width=5)
    dr.line([(640, 676), (668, 640)], fill=(20, 20, 18), width=5)
    dr.ellipse([633, 594, 647, 608], fill=(20, 20, 18))

    # --- Tactical Olive Nylon Webbing Strap [768..1024, 500..745] ---
    dr.rectangle([768, 500, 1024, 745], fill=(60, 66, 48))
    for wy in range(504, 742, 6):
        dr.line([(772, wy), (1020, wy)], fill=(46, 51, 37), width=2)
        dr.line([(772, wy + 2), (1020, wy + 2)], fill=(74, 81, 60), width=1)
    # Stitched edge borders
    for sx in (782, 1010):
        for wy in range(506, 740, 10):
            dr.line([(sx, wy), (sx, wy + 5)], fill=(88, 95, 72), width=3)

    # --- Matte Black Quick-Release Buckle Polymer [0..275, 748..1024] ---
    dr.rectangle([0, 748, 275, 1024], fill=(32, 34, 35))
    dr.rounded_rectangle([24, 772, 250, 1000], radius=16, fill=(42, 45, 47), outline=(18, 20, 21), width=6)
    dr.rounded_rectangle([54, 842, 220, 930], radius=10, fill=(24, 26, 28), outline=(66, 70, 74), width=3)

    # --- Heavy Cast Olive Tripod & Yoke Steel [276..1024, 748..1024] ---
    dr.rectangle([276, 748, 1024, 1024], fill=(70, 76, 51))
    # Subtle cast-iron ribs & bolts
    for rx in range(320, 1000, 110):
        dr.rectangle([rx, 760, rx + 26, 1012], fill=(80, 87, 59), outline=(46, 50, 34), width=3)
        dr.ellipse([rx + 5, 780, rx + 21, 796], fill=(102, 108, 82), outline=(30, 32, 22), width=2)
        dr.ellipse([rx + 5, 976, rx + 21, 992], fill=(102, 108, 82), outline=(30, 32, 22), width=2)

    # Apply subtle grunge & paint-chip weathering across decals & cast steel so nothing looks plastic!
    arr_out = np.asarray(im_tmp, dtype=np.float32)
    grunge = 0.90 + 0.18 * n_fine[:, :, None]
    arr_out[495:, :] *= grunge[495:, :]
    decal_scratches = (n_chip[520:725, 40:755] > 0.79)
    sub_dec = arr_out[520:725, 40:755]
    sub_dec[decal_scratches] = [72.0, 78.0, 52.0]
    arr_out[520:725, 40:755] = sub_dec

    p_out = os.path.join(stage_dir, "eric_cannon_metal.png")
    Image.fromarray(np.clip(arr_out, 0, 255).astype(np.uint8), mode="RGB").save(p_out, "PNG", optimize=True)
    return p_out


# ==============================================================================
# 4. ADDITIVE ARTILLERY BLAST, SHOCKRING & ROCKET JET FX (`eric_cannon_fx.png`)
# ==============================================================================
def build_fx_texture(stage_dir):
    W, H = 512, 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    hw = 256
    yy, xx = np.mgrid[0:hw, 0:hw]
    dx = (xx - 127.5) / 127.5
    dy = (yy - 127.5) / 127.5
    rr = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)

    # Q1 (0..256, 0..256): Starburst Artillery Flash (fiery white-gold core -> orange spikes!)
    spikes = 0.55 + 0.45 * np.cos(ang * 10.0) * np.cos(ang * 4.0 + 0.7)
    core = np.exp(-((rr / 0.34) ** 2))
    rays = np.exp(-((rr / (0.52 + 0.38 * spikes)) ** 2.4)) * (1.0 - smoothstep(0.78, 0.98, rr))
    a1 = np.clip(core + 0.85 * rays, 0.0, 1.0)
    rgba[:hw, :hw, 0] = 255.0
    rgba[:hw, :hw, 1] = np.clip(145.0 + 110.0 * core, 0.0, 255.0)
    rgba[:hw, :hw, 2] = np.clip(40.0 + 215.0 * (core ** 1.8), 0.0, 255.0)
    rgba[:hw, :hw, 3] = a1 * 255.0

    # Q2 (256..512, 0..256): Supersonic Mach Shockwave Ring (like wew_cannon!)
    ring = np.exp(-(((rr - 0.72) / 0.11) ** 2)) * (1.0 - smoothstep(0.88, 0.98, rr))
    inner_glow = 0.28 * np.exp(-(((rr - 0.48) / 0.16) ** 2))
    a2 = np.clip(ring + inner_glow, 0.0, 1.0)
    rgba[:hw, hw:, 0] = 255.0
    rgba[:hw, hw:, 1] = np.clip(205.0 + 50.0 * ring, 0.0, 255.0)
    rgba[:hw, hw:, 2] = np.clip(120.0 + 130.0 * ring, 0.0, 255.0)
    rgba[:hw, hw:, 3] = a2 * 255.0

    # Q3 (0..256, 256..512): Rocket Venturi Exhaust Plume Cone (u across cone, v=0 nozzle -> v=1 tail)
    u_j = xx / 255.0
    v_j = yy / 255.0
    center_w = np.sin(u_j * math.pi) ** 0.75
    diamonds = 0.65 + 0.35 * np.cos(v_j * 5.0 * math.pi) ** 2
    plume = center_w * (1.0 - smoothstep(0.15, 0.98, v_j)) * diamonds
    rgba[hw:, :hw, 0] = 255.0
    rgba[hw:, :hw, 1] = np.clip(120.0 + 135.0 * (1.0 - v_j), 0.0, 255.0)
    rgba[hw:, :hw, 2] = np.clip(30.0 + 210.0 * ((1.0 - v_j) ** 2.4), 0.0, 255.0)
    rgba[hw:, :hw, 3] = np.clip(plume * 255.0, 0.0, 255.0)

    # Q4 (256..512, 256..512): Overpressure Steam / Smoke Puff
    noise_s = _fbm(hw, hw, seed=88)
    puff = np.exp(-((rr / 0.62) ** 2)) * (0.55 + 0.65 * noise_s) * (1.0 - smoothstep(0.72, 0.96, rr))
    rgba[hw:, hw:, 0] = 235.0
    rgba[hw:, hw:, 1] = 225.0
    rgba[hw:, hw:, 2] = 205.0
    rgba[hw:, hw:, 3] = np.clip(puff * 185.0, 0.0, 255.0)

    p_out = os.path.join(stage_dir, "eric_cannon_fx.png")
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(p_out, "PNG", optimize=True)
    return p_out


def build_all_textures(stage_dir=STAGE_TEX, progs_dir=PROGS_DIR):
    os.makedirs(stage_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    paths = dict(
        head=build_head_texture(stage_dir),
        ears=build_ears_texture(stage_dir),
        metal=build_metal_texture(stage_dir),
        fx=build_fx_texture(stage_dir),
    )

    # Deploy DarkPlaces-calibrated diffuse textures to `progs/` (prevents sunlit blowout in downtownsmall!)
    gains = dict(head=0.84, ears=0.84, metal=0.88)
    for key, gain in gains.items():
        arr = np.asarray(Image.open(paths[key]).convert("RGB"), dtype=np.float32)
        Image.fromarray(np.clip(arr * gain, 0, 255).astype(np.uint8), mode="RGB").save(
            os.path.join(progs_dir, f"eric_cannon_{key}.png"), "PNG", optimize=True
        )

    # Premultiplied RGB for `blendfunc add` in DarkPlaces!
    fx_rgba = np.asarray(Image.open(paths["fx"]).convert("RGBA"), dtype=np.float32)
    fx_premul = fx_rgba[..., :3] * (fx_rgba[..., 3:4] / 255.0) * 0.85
    Image.fromarray(np.clip(fx_premul, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(progs_dir, "eric_cannon_fx.png"), "PNG", optimize=True
    )

    # Save 2x2 diagnostic preview sheet
    sheet = Image.new("RGB", (1024, 1024), (18, 20, 24))
    for idx, key in enumerate(("head", "ears", "metal", "fx")):
        im = Image.open(paths[key])
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (16, 18, 22))
            bg.paste(im, mask=im.split()[3])
            im = bg
        else:
            im = im.convert("RGB")
        im = im.resize((512, 512), Image.LANCZOS)
        sheet.paste(im, ((idx % 2) * 512, (idx // 2) * 512))
    sheet.save(os.path.join(stage_dir, "_preview_2x2.png"), "PNG")

    return paths


if __name__ == "__main__":
    p = build_all_textures()
    print("Built all Eric Deason Cannon textures:", p)
