"""High-resolution textures & clean studio-keyed Kyle Tillet cutouts for the 5 Kyle Scissor Viewmodels.

Outputs (written into out_dir):
  - kyle_cutout.png (1024x1024 RGBA): full-body Kyle cutout, floating Kyle head cutout, $100 Kyle Bill, Invoice #050 sheet
  - kyle_metals.png (1024x1024 RGB):  anisotropic chrome scissor steel, gunmetal, antique brass, vintage green enamel,
                                      barber pole stripes, wood clipboard, gold coin, 50% CUT PSI gauge & marquee flags
  - kyle_hand.png   (512x512 RGB):    Quake Ranger distressed brown leather glove, bronze knuckle plate & riveted bracer
  - kyle_glass.png  (512x512 RGBA):   translucent cyan pressurized glass tube w/ specular highlights & air bubbles
  - kyle_fx.png     (512x512 RGBA):   additive scissor spark burst, shockwave ring, speed streaks & cash glitter
"""
import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PHOTO_HEAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "raw_photos", "media_1795056507412_c9227b8c.jpg")
PHOTO_BODY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "raw_photos", "media_1795056611778_b8a1f6c9.jpg")

# UV rects in kyle_cutout.png (u0, v0, u1, v1) with v=0 at top (standard Quake/WebGL image top-left UV)
UV_CUT_BODY    = (0.01, 0.01, 0.49, 0.99)
UV_CUT_HEAD    = (0.51, 0.01, 0.99, 0.49)
UV_DOLLAR_BILL = (0.51, 0.51, 0.99, 0.74)
UV_INVOICE     = (0.51, 0.76, 0.99, 0.99)

# UV rects in kyle_metals.png
UV_CHROME      = (0.02, 0.02, 0.48, 0.24)
UV_GUNMETAL    = (0.52, 0.02, 0.98, 0.24)
UV_BRASS       = (0.02, 0.27, 0.48, 0.49)
UV_REG_GREEN   = (0.52, 0.27, 0.98, 0.49)
UV_BARBER_POLE = (0.02, 0.52, 0.48, 0.74)
UV_WOOD_CLIP   = (0.52, 0.52, 0.98, 0.74)
UV_PSI_GAUGE   = (0.02, 0.77, 0.24, 0.98)
UV_GOLD_COIN   = (0.27, 0.77, 0.48, 0.98)
UV_MARQUEE_50  = (0.52, 0.77, 0.98, 0.98)

# UV rects in kyle_fx.png
UV_FX_SPARK = (0.02, 0.02, 0.48, 0.48)
UV_FX_RING  = (0.52, 0.02, 0.98, 0.48)
UV_FX_STREAK = (0.02, 0.52, 0.48, 0.98)
UV_FX_GLINT = (0.52, 0.52, 0.98, 0.98)


def _font(size, bold=True):
    candidates = ["consolab.ttf", "arialbd.ttf", "tahomabd.ttf"] if bold else ["consola.ttf", "arial.ttf", "tahoma.ttf"]
    for nm in candidates:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=77, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.Resampling.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _key_studio_bg(bgr, seed_points, lab_thresh=14.5, include_interior_holes=True, bottom_shirt_crop=False):
    """Cleanly keys off-white studio background using CIE Lab color distance + connected flood-fill + soft edge despill."""
    h, w = bgr.shape[:2]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    # Estimate studio background Lab from top corner patches
    patch = np.vstack([
        lab[0:12, 0:12].reshape(-1, 3),
        lab[0:12, w - 12:w].reshape(-1, 3),
    ])
    bg_lab = np.median(patch, axis=0)
    bg_bgr = np.median(
        np.vstack([bgr[0:12, 0:12].reshape(-1, 3), bgr[0:12, w - 12:w].reshape(-1, 3)]),
        axis=0,
    ).astype(np.float32)

    # Weighted Lab distance (slightly less sensitive to L shading, very strict on a/b chroma)
    dL = (lab[..., 0] - bg_lab[0]) * 0.65
    da = (lab[..., 1] - bg_lab[1]) * 1.35
    db = (lab[..., 2] - bg_lab[2]) * 1.35
    dist = np.sqrt(dL * dL + da * da + db * db)

    # Candidate background pixels: very close to studio white/cream
    cand = (dist < lab_thresh).astype(np.uint8) * 255

    # Connected components of candidate bg
    num_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(cand, connectivity=8)
    bg_mask = np.zeros((h, w), dtype=np.uint8)

    # Mark components connected to seeded border pixels
    seed_lbls = set()
    for sx, sy in seed_points:
        sx_c = max(0, min(w - 1, sx))
        sy_c = max(0, min(h - 1, sy))
        lbl = int(labels[sy_c, sx_c])
        if lbl > 0:
            seed_lbls.add(lbl)

    # Also mark any component touching top/left/right edges
    for edge_slice in (labels[0, :], labels[:, 0], labels[:, -1]):
        for lbl in np.unique(edge_slice):
            if lbl > 0:
                seed_lbls.add(int(lbl))

    # Optionally catch small enclosed studio gaps (e.g., between Kyle's arm and waist, or legs)
    # where Lab distance is VERY tight (< 8.5) and brightness L > 205
    if include_interior_holes:
        for lbl in range(1, num_lbl):
            if lbl in seed_lbls:
                continue
            area = int(stats[lbl, cv2.CC_STAT_AREA])
            if area < 150:
                continue
            comp_mask = (labels == lbl)
            mean_d = float(dist[comp_mask].mean())
            mean_L = float(lab[comp_mask, 0].mean())
            if mean_d < 9.0 and mean_L > 205.0:
                seed_lbls.add(lbl)

    for lbl in seed_lbls:
        bg_mask[labels == lbl] = 255

    # Foreground mask
    fg = 255 - bg_mask
    # Remove tiny noise specks
    num_f, flbl, fstats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if num_f > 1:
        # Keep largest foreground component
        areas = fstats[1:, cv2.CC_STAT_AREA]
        keep = 1 + int(np.argmax(areas))
        fg = np.where(flbl == keep, 255, 0).astype(np.uint8)

    # Optional clean neck/oval cut for floating head cutout
    if bottom_shirt_crop:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        # Keep face, hair, ears, chin & upper neck cleanly; cut blue polo & collar fold cleanly
        cx, cy = w * 0.50, h * 0.45
        oval = ((xx - cx) / (w * 0.43)) ** 2 + ((yy - cy) / (h * 0.44)) ** 2
        b_ch, g_ch, r_ch = bgr[..., 0].astype(np.float32), bgr[..., 1].astype(np.float32), bgr[..., 2].astype(np.float32)
        # Only cut blue polo pixels or outside the chin oval (never bright neutral skin/teeth inside oval)
        is_collar = (yy > h * 0.64) & (((b_ch - r_ch) > 12.0) | (oval > 0.78))
        below_neck = yy > h * 0.84
        collar_dil = cv2.dilate((is_collar | below_neck).astype(np.uint8) * 255, np.ones((7, 7), np.uint8)) > 0
        fg[collar_dil] = 0
        # Keep largest component & fill any interior holes (e.g. teeth/highlights)
        num_f, flbl, fstats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        if num_f > 1:
            keep = 1 + int(np.argmax(fstats[1:, cv2.CC_STAT_AREA]))
            fg = np.where(flbl == keep, 255, 0).astype(np.uint8)
        inv = 255 - fg
        num_h, hlbl, _, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
        edge_bg = int(hlbl[0, 0])
        fg[hlbl != edge_bg] = 255

    # Erode 1px & Gaussian feather for crisp anti-aliased alpha without white halo
    fg_f = fg.astype(np.float32) / 255.0
    # Softly attenuate pixels right on the boundary that are close to bg color
    edge_band = cv2.dilate(bg_mask, np.ones((5, 5), np.uint8)) & fg
    alpha = fg_f.copy()
    bg_sim = np.clip((dist - 8.0) / 10.0, 0.0, 1.0)
    alpha = np.where(edge_band > 0, alpha * bg_sim, alpha)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.75)
    alpha = np.clip((alpha - 0.12) / 0.78, 0.0, 1.0)

    # Despill border RGB: pull off-white studio fringe toward neighbor interior color
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    bg_rgb = bg_bgr[::-1]
    eroded = cv2.erode((alpha > 0.88).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    # For semi-transparent edge pixels, decontaminate studio bg contribution
    edge_px = (alpha > 0.02) & (alpha < 0.92) & (eroded == 0)
    a_safe = np.maximum(alpha, 0.25)[..., None]
    unmixed = np.clip((rgb - bg_rgb[None, None, :] * (1.0 - alpha[..., None])) / a_safe, 0.0, 255.0)
    rgb = np.where(edge_px[..., None], unmixed, rgb)

    rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.clip(alpha * 255.0, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, mode="RGBA")


def _crop_to_alpha(pil_rgba, pad=8):
    arr = np.asarray(pil_rgba)
    ys, xs = np.where(arr[..., 3] > 16)
    if len(xs) == 0:
        return pil_rgba
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(pil_rgba.width, int(xs.max()) + pad + 1)
    y1 = min(pil_rgba.height, int(ys.max()) + pad + 1)
    return pil_rgba.crop((x0, y0, x1, y1))


def _place_fitted(canvas, im_rgba, rect_uv):
    W, H = canvas.size
    x0 = int(round(rect_uv[0] * W))
    y0 = int(round(rect_uv[1] * H))
    x1 = int(round(rect_uv[2] * W))
    y1 = int(round(rect_uv[3] * H))
    rw, rh = max(4, x1 - x0), max(4, y1 - y0)
    sc = min(rw / im_rgba.width, rh / im_rgba.height)
    nw = max(1, int(round(im_rgba.width * sc)))
    nh = max(1, int(round(im_rgba.height * sc)))
    resized = im_rgba.resize((nw, nh), Image.Resampling.LANCZOS)
    px = x0 + (rw - nw) // 2
    py = y0 + (rh - nh) // 2
    canvas.paste(resized, (px, py), resized)


def _draw_dollar_bill_image(w=480, h=220):
    """Crisp humorous $100 KYLE-BUCK ('50% CUT - IN SCISSORS WE TRUST')."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    # Paper base with crisp green treasury border
    dr.rounded_rectangle([4, 4, w - 5, h - 5], radius=8, fill=(214, 228, 194, 255), outline=(44, 92, 52, 255), width=6)
    dr.rectangle([16, 16, w - 17, h - 17], outline=(62, 118, 68, 255), width=3)
    # Subtle guilloche stripes
    for gx in range(28, w - 28, 18):
        dr.line([(gx, 22), (gx, h - 22)], fill=(186, 208, 168, 130), width=1)
    # Center oval seal
    dr.ellipse([w // 2 - 58, h // 2 - 56, w // 2 + 58, h // 2 + 56], fill=(192, 214, 174, 255), outline=(42, 94, 52, 255), width=3)
    f_big = _font(36, bold=True)
    f_med = _font(20, bold=True)
    f_sm = _font(14, bold=True)
    dr.text((28, 24), "100", fill=(28, 76, 36, 255), font=f_big)
    dr.text((w - 102, 24), "100", fill=(28, 76, 36, 255), font=f_big)
    dr.text((28, h - 64), "50%", fill=(154, 34, 28, 255), font=f_big)
    dr.text((w - 102, h - 64), "100", fill=(28, 76, 36, 255), font=f_big)
    dr.text((w // 2 - 44, h // 2 - 22), "KYLE", fill=(24, 68, 32, 255), font=f_med)
    dr.text((w // 2 - 36, h // 2 + 4), "CUT$", fill=(154, 34, 28, 255), font=f_med)
    dr.text((w // 2 - 106, 24), "RESERVE OF BAKERSFIELD", fill=(32, 82, 42, 255), font=f_sm)
    dr.text((w // 2 - 96, h - 38), "GIMME MY 50% COMMISSION", fill=(32, 82, 42, 255), font=f_sm)
    return im


def _draw_invoice_image(w=480, h=220):
    """Crisp official barber commission invoice: 'GIMME MY CUT - 50%'."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([4, 4, w - 5, h - 5], radius=6, fill=(246, 243, 232, 255), outline=(60, 64, 72, 255), width=4)
    # Header bar
    dr.rectangle([12, 12, w - 13, 50], fill=(28, 58, 118, 255))
    f_hdr = _font(22, bold=True)
    f_big = _font(30, bold=True)
    f_sm = _font(15, bold=True)
    dr.text((22, 18), "INVOICE #050 // PAST DUE", fill=(248, 246, 240, 255), font=f_hdr)
    # Ledger lines
    for ly in (72, 102, 132, 162, 190):
        dr.line([(20, ly), (w - 20, ly)], fill=(190, 196, 208, 255), width=2)
    dr.text((22, 54), "ITEM: BARBER SHOP SHEAR WORK", fill=(36, 40, 48, 255), font=f_sm)
    dr.text((22, 84), "RATE: HALF OF EVERYTHING YOU OWN", fill=(36, 40, 48, 255), font=f_sm)
    # Red stamped box
    dr.rectangle([22, 118, w - 22, 178], outline=(196, 26, 22, 255), width=4, fill=(252, 232, 228, 255))
    dr.text((42, 130), "GIMME MY CUT - 50%", fill=(192, 22, 18, 255), font=f_big)
    dr.text((22, 186), "PAYABLE IMMEDIATELY TO KYLE TILLET", fill=(54, 62, 76, 255), font=f_sm)
    return im


def build_kyle_cutout_atlas(out_path):
    """Builds 1024x1024 RGBA atlas with cleanly keyed full-body Kyle, floating Kyle head, $100 bill & invoice."""
    bgr_head = cv2.imread(PHOTO_HEAD)
    bgr_body = cv2.imread(PHOTO_BODY)
    assert bgr_head is not None and bgr_body is not None, "Missing Kyle user_uploaded photos!"

    head_rgba = _crop_to_alpha(
        _key_studio_bg(bgr_head, [(6, 6), (bgr_head.shape[1] - 6, 6)], lab_thresh=15.0, include_interior_holes=False, bottom_shirt_crop=True),
        pad=10,
    )
    body_rgba = _crop_to_alpha(
        _key_studio_bg(bgr_body, [(6, 6), (bgr_body.shape[1] - 6, 6), (6, bgr_body.shape[0] - 6)], lab_thresh=13.5, include_interior_holes=True, bottom_shirt_crop=False),
        pad=8,
    )

    atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    _place_fitted(atlas, body_rgba, UV_CUT_BODY)
    _place_fitted(atlas, head_rgba, UV_CUT_HEAD)
    _place_fitted(atlas, _draw_dollar_bill_image(), UV_DOLLAR_BILL)
    _place_fitted(atlas, _draw_invoice_image(), UV_INVOICE)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    atlas.save(out_path, "PNG", optimize=True)
    return out_path


def build_metals_atlas(out_path):
    """Builds 1024x1024 RGB material atlas for chrome shears, gunmetal, brass, green register, barber pole, wood & dials."""
    W = H = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    n_c = _fbm(H, W, seed=501, octaves=(4, 8, 16, 32))
    n_f = _fbm(H, W, seed=502, octaves=(2, 4, 8))

    # 1. Chrome Scissor Steel [0..256, 0..512]
    y1, x1 = np.mgrid[0:256, 0:512].astype(np.float32)
    u_c = x1 / 511.0 * 2.0 * math.pi
    chr_v = 0.68 + 0.22 * np.cos(u_c - 0.7) + 0.14 * np.cos(2.0 * u_c + 0.5) + 0.04 * n_f[:256, :512]
    chr_v += 0.03 * np.sin(y1 * 0.9)
    arr[:256, :512, 0] = np.clip(chr_v * 234.0, 45, 250)
    arr[:256, :512, 1] = np.clip(chr_v * 240.0, 48, 252)
    arr[:256, :512, 2] = np.clip(chr_v * 252.0, 52, 255)

    # 2. Dark Gunmetal / Blued Steel [0..256, 512..1024]
    gm = 74.0 + 14.0 * n_c[:256, 512:] + 6.0 * n_f[:256, 512:]
    arr[:256, 512:, 0] = np.clip(gm * 0.92, 24, 150)
    arr[:256, 512:, 1] = np.clip(gm * 0.98, 26, 158)
    arr[:256, 512:, 2] = np.clip(gm * 1.12, 30, 175)

    # 3. Burnished Antique Brass [256..512, 0..512]
    yb, xb = np.mgrid[0:256, 0:512].astype(np.float32)
    br = 188.0 + 28.0 * np.cos(xb / 511.0 * math.pi * 2.0 - 0.4) + 12.0 * n_c[256:512, :512] + 6.0 * np.sin(yb * 0.45)
    arr[256:512, :512, 0] = np.clip(br * 1.08, 65, 252)
    arr[256:512, :512, 1] = np.clip(br * 0.86, 52, 218)
    arr[256:512, :512, 2] = np.clip(br * 0.36, 22, 118)

    # 4. Vintage Barber Cash-Register Forest-Green Enamel [256..512, 512..1024]
    yg, xg = np.mgrid[0:256, 0:512].astype(np.float32)
    en = 1.0 + 0.14 * n_c[256:512, 512:] + 0.06 * np.sin(yg / 255.0 * math.pi)
    arr[256:512, 512:, 0] = np.clip(32.0 * en, 14, 78)
    arr[256:512, 512:, 1] = np.clip(112.0 * en, 44, 168)
    arr[256:512, 512:, 2] = np.clip(64.0 * en, 24, 108)

    # 5. Barber Pole Red-White-Blue Spiral [512..768, 0..512]
    yp, xp = np.mgrid[0:256, 0:512].astype(np.float32)
    phase = ((xp / 512.0) * 2.0 + (yp / 256.0) * 2.0) % 1.0
    # 0.00..0.28 red, 0.28..0.50 white, 0.50..0.78 blue, 0.78..1.00 white
    r_p = np.where(phase < 0.28, 224.0, np.where(phase < 0.50, 244.0, np.where(phase < 0.78, 34.0, 244.0)))
    g_p = np.where(phase < 0.28, 36.0,  np.where(phase < 0.50, 244.0, np.where(phase < 0.78, 76.0, 244.0)))
    b_p = np.where(phase < 0.28, 42.0,  np.where(phase < 0.50, 248.0, np.where(phase < 0.78, 212.0, 248.0)))
    gloss = 0.86 + 0.14 * np.cos(xp / 511.0 * 2.0 * math.pi)
    arr[512:768, :512, 0] = np.clip(r_p * gloss, 15, 255)
    arr[512:768, :512, 1] = np.clip(g_p * gloss, 15, 255)
    arr[512:768, :512, 2] = np.clip(b_p * gloss, 15, 255)

    # 6. Clipboard Wood / Mahogany [512..768, 512..1024]
    yw, xw = np.mgrid[0:256, 0:512].astype(np.float32)
    grain = np.sin(yw * 0.28 + 3.2 * n_c[512:768, 512:]) * 14.0 + 10.0 * n_c[512:768, 512:]
    arr[512:768, 512:, 0] = np.clip(148.0 + grain, 56, 215)
    arr[512:768, 512:, 1] = np.clip(96.0 + grain * 0.7, 36, 158)
    arr[512:768, 512:, 2] = np.clip(52.0 + grain * 0.4, 20, 102)

    # 7. PSI Dial Background [768..1024, 0..256]
    arr[768:1024, :256, :] = 236.0

    # 8. Gold Coin Metallic [768..1024, 256..512]
    yc, xc = np.mgrid[0:256, 0:256].astype(np.float32)
    rc = np.sqrt(((xc - 127.5) / 118.0) ** 2 + ((yc - 127.5) / 118.0) ** 2)
    rim_hi = 28.0 * np.exp(-((rc - 0.86) ** 2) / 0.008)
    gold = 212.0 + rim_hi + 12.0 * n_f[768:1024, 256:512]
    arr[768:1024, 256:512, 0] = np.clip(gold * 1.15, 90, 255)
    arr[768:1024, 256:512, 1] = np.clip(gold * 0.90, 70, 232)
    arr[768:1024, 256:512, 2] = np.clip(gold * 0.24, 15, 96)

    # 9. Register Marquee Plate [768..1024, 512..1024]
    arr[768:1024, 512:, 0] = 28.0
    arr[768:1024, 512:, 1] = 26.0
    arr[768:1024, 512:, 2] = 24.0

    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # Draw 50% CUT PSI Gauge at [0..256, 768..1024]
    cx, cy = 128, 768 + 128
    dr.ellipse([cx - 106, cy - 106, cx + 106, cy + 106], fill=(246, 242, 228), outline=(44, 48, 56), width=8)
    dr.arc([cx - 88, cy - 88, cx + 88, cy + 88], start=135, end=315, fill=(38, 128, 56), width=10)
    dr.arc([cx - 88, cy - 88, cx + 88, cy + 88], start=315, end=45, fill=(204, 34, 28), width=12)
    for k in range(9):
        ang = math.radians(135 + k * 33.75)
        dr.line(
            [(cx + math.cos(ang) * 72, cy + math.sin(ang) * 72),
             (cx + math.cos(ang) * 92, cy + math.sin(ang) * 92)],
            fill=(28, 28, 32), width=4,
        )
    # Red needle pointing hot
    dr.line([(cx, cy), (cx + 66, cy - 38)], fill=(208, 24, 20), width=6)
    dr.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(42, 42, 46))
    f_g = _font(22, bold=True)
    dr.text((cx - 48, cy + 32), "50% CUT", fill=(180, 24, 20), font=f_g)

    # Draw Gold Coin '$50%' emblem at [256..512, 768..1024]
    gcx, gcy = 384, 768 + 128
    dr.ellipse([gcx - 92, gcy - 92, gcx + 92, gcy + 92], outline=(168, 118, 18), width=6)
    f_coin = _font(54, bold=True)
    dr.text((gcx - 50, gcy - 30), "50%", fill=(138, 92, 12), font=f_coin)

    # Draw Register Marquee Flags at [512..1024, 768..1024]
    f_mq = _font(36, bold=True)
    f_mq2 = _font(24, bold=True)
    dr.rectangle([534, 792, 1002, 886], fill=(244, 232, 198), outline=(188, 148, 48), width=6)
    dr.text((552, 816), "50% CUT // PAY UP!", fill=(182, 24, 20), font=f_mq)
    dr.rectangle([534, 904, 1002, 998], fill=(24, 74, 42), outline=(212, 168, 56), width=6)
    dr.text((556, 932), "COMMISSION: $50.00", fill=(248, 224, 118), font=f_mq2)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_glass_texture(out_path):
    """512x512 RGBA translucent pressurized glass tube with specular streaks, meniscus & air bubbles."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xx / 511.0
    v = yy / 511.0

    # Cool cyan-tinted borosilicate glass base
    spec1 = np.exp(-((u - 0.24) ** 2) / 0.0028) * 0.92
    spec2 = np.exp(-((u - 0.72) ** 2) / 0.0080) * 0.45
    rim_v = (np.exp(-((v - 0.04) ** 2) / 0.0012) + np.exp(-((v - 0.96) ** 2) / 0.0012)) * 0.65

    alpha = np.clip(0.20 + 0.42 * spec1 + 0.24 * spec2 + 0.40 * rim_v, 0.16, 0.84)
    rgba[..., 0] = np.clip(145.0 + 110.0 * spec1 + 80.0 * spec2, 0, 255)
    rgba[..., 1] = np.clip(222.0 + 33.0 * spec1 + 30.0 * spec2, 0, 255)
    rgba[..., 2] = np.clip(246.0 + 9.0 * spec1, 0, 255)
    rgba[..., 3] = alpha * 255.0

    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    dr = ImageDraw.Draw(im)
    # Pressurized air bubbles inside glass tube
    rng = np.random.default_rng(88)
    for _ in range(28):
        bx = int(rng.integers(32, 480))
        by = int(rng.integers(36, 476))
        br = int(rng.integers(5, 16))
        dr.ellipse([bx - br, by - br, bx + br, by + br], outline=(235, 252, 255, 185), width=2)
        dr.ellipse([bx - br // 2, by - br // 2, bx, by], fill=(255, 255, 255, 175))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_fx_texture(out_path):
    """512x512 RGBA additive FX texture for scissor sparks, shockwave ring, launch speed streaks & glints."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    nx = (xx - 127.5) / 120.0
    ny = (yy - 127.5) / 120.0
    rr = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)

    # Q1: Sharp Metallic Scissor Spark Burst
    rays = np.exp(-((np.abs(np.sin(ang * 4.0))) ** 0.7) * 4.5) * np.exp(-rr * 2.1)
    core = np.exp(-(rr * rr) / 0.06)
    a1 = np.clip((rays * 0.95 + core) * (rr < 0.98), 0.0, 1.0)
    rgba[:256, :256, 0] = 255.0 * a1
    rgba[:256, :256, 1] = 235.0 * a1
    rgba[:256, :256, 2] = np.clip(145.0 * a1 + 110.0 * core, 0, 255)
    rgba[:256, :256, 3] = a1 * 255.0

    # Q2: Pneumatic / Railgun Shockwave Ring
    ring = np.exp(-((rr - 0.68) ** 2) / 0.014)
    inner = np.exp(-((rr - 0.36) ** 2) / 0.025) * 0.75
    a2 = np.clip((ring + inner) * (rr < 0.98), 0.0, 1.0)
    rgba[:256, 256:, 0] = np.clip((ring * 0.45 + inner * 1.0) * 255.0, 0, 255)
    rgba[:256, 256:, 1] = np.clip((ring * 0.90 + inner * 0.85) * 255.0, 0, 255)
    rgba[:256, 256:, 2] = np.clip((ring * 1.00 + inner * 0.45) * 255.0, 0, 255)
    rgba[:256, 256:, 3] = a2 * 255.0

    # Q3: Launch Motion Speed Streaks
    u_s = xx / 255.0
    v_s = (yy - 127.5) / 120.0
    streak = (
        np.exp(-((v_s - 0.00) ** 2) / 0.012)
        + 0.75 * np.exp(-((v_s - 0.34) ** 2) / 0.007)
        + 0.75 * np.exp(-((v_s + 0.34) ** 2) / 0.007)
    ) * np.clip(np.sin(u_s * math.pi), 0.0, 1.0) ** 0.6
    a3 = np.clip(streak, 0.0, 1.0)
    rgba[256:, :256, 0] = 210.0 * a3
    rgba[256:, :256, 1] = 245.0 * a3
    rgba[256:, :256, 2] = 255.0 * a3
    rgba[256:, :256, 3] = a3 * 255.0

    # Q4: Gold Cash / Scissor Glint Star
    glint = (np.exp(-(nx * nx) / 0.006) * np.exp(-(ny * ny) / 0.25)
             + np.exp(-(ny * ny) / 0.006) * np.exp(-(nx * nx) / 0.25)
             + np.exp(-(rr * rr) / 0.04)) * (rr < 0.98)
    a4 = np.clip(glint, 0.0, 1.0)
    rgba[256:, 256:, 0] = 255.0 * a4
    rgba[256:, 256:, 1] = 228.0 * a4
    rgba[256:, 256:, 2] = 120.0 * a4
    rgba[256:, 256:, 3] = a4 * 255.0

    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", optimize=True)
    return out_path


def build_all_weapon_textures(out_dir):
    """Generates all 5 weapon skin PNGs into out_dir and returns a dict of paths."""
    import sys
    mm_tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if mm_tools_dir not in sys.path:
        sys.path.insert(0, mm_tools_dir)
    import mmw_textures

    os.makedirs(out_dir, exist_ok=True)
    cutout_p = build_kyle_cutout_atlas(os.path.join(out_dir, "kyle_cutout.png"))
    metals_p = build_metals_atlas(os.path.join(out_dir, "kyle_metals.png"))
    glass_p  = build_glass_texture(os.path.join(out_dir, "kyle_glass.png"))
    fx_p     = build_fx_texture(os.path.join(out_dir, "kyle_fx.png"))
    hand_p   = mmw_textures.build_hand_texture(out_dir)
    # Rename mmw_hand.png -> kyle_hand.png for clean self-contained naming
    kyle_hand_p = os.path.join(out_dir, "kyle_hand.png")
    if os.path.isfile(hand_p) and hand_p != kyle_hand_p:
        os.replace(hand_p, kyle_hand_p)

    return {
        "cutout": cutout_p,
        "metals": metals_p,
        "hand":   kyle_hand_p,
        "glass":  glass_p,
        "fx":     fx_p,
    }
