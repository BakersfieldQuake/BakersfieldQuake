"""Extracts razor-sharp RGBA character & demon layers for Bryan & His Demons:
1. Studio Tinfoil-Hat Bryan + Demon Detector (from bryan_studio_sprint_2x2.jpg) -> isolated Bryan & Crimson Demon layers
2. Video 2 Cosmic-Hood Paladin Bryan (0°, 45°, 90°, 180°) + Winged Red Demon + Cloaked Reaper + Grey Ram-Horned Demon
   using GPU Mask R-CNN + color-guided edge alpha refinement + glowing blue broadsword extraction.
"""
import os
import cv2
import numpy as np
import torch
import torchvision
from PIL import Image, ImageOps
from scipy import ndimage

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
REF_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "ref", "bryan")
OUT_LAYERS = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_layers")
DBG_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_debug")
os.makedirs(OUT_LAYERS, exist_ok=True)
os.makedirs(DBG_DIR, exist_ok=True)


def key_green_studio(im_rgb):
    """Subpixel #00FF00 studio chroma-key that preserves enclosed RGB LEDs and rainbow shirt."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    gx = g - np.maximum(r, b)

    bg_strict = (gx > 62.0) & (g > 118.0)
    lbl, _ = ndimage.label(bg_strict)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)

    # Interior pure-green air pockets (e.g. between arm & torso or between demon claws),
    # strictly excluding the bright white-centered green LED (where r>100 or b>100).
    interior_green = (gx > 62.0) & (g > 165.0) & (r < 95.0) & (b < 95.0)
    bg_mask = np.isin(lbl, list(border_ids)) | interior_green

    dist = ndimage.distance_transform_edt(~bg_mask)
    alpha = np.ones_like(g, dtype=np.float32)
    alpha[bg_mask] = 0.0
    edge = (~bg_mask) & (dist <= 6.0)
    aramp = np.clip(1.0 - (gx - 10.0) / 56.0, 0.0, 1.0)
    use_r = edge & (gx > 10.0)
    alpha[use_r] = np.where(aramp[use_r] < 0.04, 0.0, aramp[use_r])

    rc, gc, bc = r.copy(), g.copy(), b.copy()
    semi = (alpha > 0.02) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    den = np.maximum(alpha[semi], 0.24)
    rc[semi] = np.clip(rc[semi] / den, 0.0, 255.0)
    gc[semi] = np.clip((gc[semi] - inv * 255.0) / den, 0.0, 255.0)
    bc[semi] = np.clip(bc[semi] / den, 0.0, 255.0)

    dsp = (alpha > 0.0) & (dist <= 6.0)
    gc[dsp] = np.minimum(gc[dsp], np.maximum(rc[dsp], bc[dsp]) + 5.0)

    return np.dstack([
        np.clip(np.round(rc), 0, 255).astype(np.uint8),
        np.clip(np.round(gc), 0, 255).astype(np.uint8),
        np.clip(np.round(bc), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])


def split_bryan_and_demon_quadrant(q_rgba, model, preprocess, dev, q_name):
    """Uses Mask R-CNN instance probabilities + color affinity to cleanly split Bryan vs Crimson Demon
    inside a 512x512 studio quadrant while keeping 100% of the exact #00FF00 outer alpha."""
    H, W = q_rgba.shape[:2]
    fg = q_rgba[..., 3] > 8
    rgb = q_rgba[..., :3]
    # Place on neutral mid-grey for Mask R-CNN so #00FF00 doesn't distract edges
    a_f = q_rgba[..., 3:4].astype(np.float32) / 255.0
    comp_rgb = (rgb.astype(np.float32) * a_f + 118.0 * (1.0 - a_f)).astype(np.uint8)
    pil_in = Image.fromarray(comp_rgb)

    with torch.no_grad():
        pred = model([preprocess(pil_in).to(dev)])[0]

    scores = pred["scores"].cpu().numpy()
    labels = pred["labels"].cpu().numpy()
    masks = pred["masks"].cpu().numpy()[:, 0]  # [N, H, W]
    boxes = pred["boxes"].cpu().numpy()

    # Keep top person/creature masks that cover substantial foreground
    cands = []
    for i in range(len(scores)):
        if scores[i] < 0.35:
            continue
        m = masks[i]
        fg_ov = float(np.sum((m > 0.4) & fg))
        if fg_ov < 1200:
            continue
        # Measure crimson-ness of upper half of this mask to identify Demon vs Bryan!
        ys, xs = np.nonzero((m > 0.45) & fg)
        y_mid = np.percentile(ys, 55)
        up = (m > 0.45) & fg & (np.arange(H)[:, None] < y_mid)
        r_ex = float(np.mean(rgb[up, 0].astype(np.float32) - np.maximum(rgb[up, 1], rgb[up, 2]).astype(np.float32))) if np.any(up) else 0.0
        cands.append((scores[i], fg_ov, r_ex, m, boxes[i]))

    # Pick strongest Bryan mask (lowest crimson excess, high overlap) and strongest Demon mask (highest crimson excess)
    bryan_cands = [c for c in cands if c[2] < 28.0]
    demon_cands = [c for c in cands if c[2] >= 28.0]

    p_bryan = max(bryan_cands, key=lambda c: c[1])[3] if bryan_cands else np.zeros((H, W), np.float32)
    p_demon = max(demon_cands, key=lambda c: c[1])[3] if demon_cands else np.zeros((H, W), np.float32)

    # Color priors for tie-breaking along the tiny contact seam:
    rf, gf, bf = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
    # Crimson demon skin/feet: vivid red (R - max(G,B) > 42, G < 65)
    is_crimson = (rf - np.maximum(gf, bf) > 42.0) & (gf < 72.0) & (bf < 75.0)
    # Bryan strong priors: silver tinfoil/box, blue/cyan/yellow/purple rainbow shirt, indigo blue jeans, white/yellow shoe trim
    is_indigo_jeans = (bf - rf > 10.0) & (bf > 34.0)
    is_bright_trim = (np.minimum(rf, np.minimum(gf, bf)) > 145.0) | ((rf > 165.0) & (gf > 140.0) & (bf < 80.0))

    score_b = p_bryan.copy() + 0.55 * is_indigo_jeans + 0.55 * is_bright_trim - 0.85 * is_crimson
    score_d = p_demon.copy() + 0.85 * is_crimson - 0.45 * is_indigo_jeans

    # Smooth boundary slightly and partition fgalpha cleanly (w_b + w_d == 1 on fg)
    diff = cv2.GaussianBlur((score_b - score_d).astype(np.float32), (5, 5), 1.1)
    w_b = np.clip(0.5 + diff * 2.5, 0.0, 1.0)
    w_d = 1.0 - w_b

    # Clean isolated tiny stray islands (< 60 px) on each layer
    for name_l, w in (("bryan", w_b), ("demon", w_d)):
        hard = (w > 0.5) & fg
        lb, nl = ndimage.label(hard)
        if nl > 1:
            sz = ndimage.sum(hard, lb, range(1, nl + 1))
            keep_ids = [1 + idx for idx, s in enumerate(sz) if s >= 80]
            keep_m = ndimage.binary_dilation(np.isin(lb, keep_ids), iterations=2)
            if name_l == "bryan":
                w_b = np.where(keep_m, w_b, 0.0)
                w_d = np.where(fg, 1.0 - w_b, 0.0)
            else:
                w_d = np.where(keep_m, w_d, 0.0)
                w_b = np.where(fg, 1.0 - w_d, 0.0)

    b_rgba = q_rgba.copy()
    d_rgba = q_rgba.copy()
    b_rgba[..., 3] = np.round(q_rgba[..., 3].astype(np.float32) * w_b).astype(np.uint8)
    d_rgba[..., 3] = np.round(q_rgba[..., 3].astype(np.float32) * w_d).astype(np.uint8)
    print(f"  [{q_name}] Bryan px={np.sum(b_rgba[...,3]>20)}, Demon px={np.sum(d_rgba[...,3]>20)}")
    return b_rgba, d_rgba


def add_crisp_detector_antenna(b_rgba, side="left"):
    """Restores a razor-sharp gleaming telescopic radio antenna + glowing tip bead on Bryan's detector box."""
    out = b_rgba.copy()
    arr = out.astype(np.float32)
    a = arr[..., 3] > 120
    # Locate the RGB LEDs on the detector box if visible (bright red/green/blue cluster)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    blue_led = a & (b > 195) & (b - r > 70)
    green_led = a & (g > 195) & (g - r > 50)
    red_led = a & (r > 205) & (r - g > 70) & (np.arange(out.shape[0])[:, None] > 140) & (np.arange(out.shape[0])[:, None] < 320)

    pil = Image.fromarray(out, "RGBA")
    from PIL import ImageDraw
    dr = ImageDraw.Draw(pil)

    if np.sum(blue_led) > 4 and np.sum(green_led) > 4:
        # Front / 45° view: antenna rises from top-left of detector box
        ys_g, xs_g = np.nonzero(green_led)
        ys_b, xs_b = np.nonzero(blue_led)
        span = abs(float(xs_b.mean()) - float(xs_g.mean()))
        bx = int(round(min(xs_g.mean(), xs_b.mean()) - span * 1.15))
        by = int(round(min(ys_g.mean(), ys_b.mean()) - 18))
        top_x = bx - 3
        top_y = by - 92
        dr.line([(bx, by), (top_x, top_y)], fill=(110, 118, 130, 255), width=3)
        dr.line([(bx, by), (top_x, top_y)], fill=(232, 240, 250, 255), width=1)
        dr.ellipse([top_x - 3, top_y - 3, top_x + 3, top_y + 3], fill=(245, 250, 255, 255))
    elif side == "profile_right":
        # Quadrant BL (facing right): detector box held in front-right hands around x~395..445, y~200..265
        ys, xs = np.nonzero(a & (np.arange(out.shape[0])[:, None] > 180) & (np.arange(out.shape[0])[:, None] < 275))
        if len(xs) > 20:
            bx = int(np.max(xs) - 10)
            by = int(np.min(ys[xs > bx - 18]) + 6)
            top_x, top_y = bx + 8, by - 92
            dr.line([(bx, by), (top_x, top_y)], fill=(110, 118, 130, 255), width=3)
            dr.line([(bx, by), (top_x, top_y)], fill=(235, 242, 252, 255), width=1)
            dr.ellipse([top_x - 3, top_y - 3, top_x + 3, top_y + 3], fill=(245, 250, 255, 255))
    elif side == "back_left":
        # Quadrant BR (135° back-left): detector box peeks on left at x~60..95, y~175..235
        ys, xs = np.nonzero(a & (np.arange(out.shape[0])[:, None] > 165) & (np.arange(out.shape[0])[:, None] < 245))
        if len(xs) > 20:
            bx = int(np.min(xs) + 12)
            by = int(np.min(ys[xs < bx + 18]) + 4)
            top_x, top_y = bx - 6, by - 78
            dr.line([(bx, by), (top_x, top_y)], fill=(110, 118, 130, 255), width=3)
            dr.line([(bx, by), (top_x, top_y)], fill=(235, 242, 252, 255), width=1)
            dr.ellipse([top_x - 2, top_y - 2, top_x + 2, top_y + 2], fill=(245, 250, 255, 255))
    return np.array(pil)


def extract_v2_character(fn, box_target, model, preprocess, dev, include_blue_sword=False):
    """Extracts a crisp feathered RGBA cutout from a Video 2 frame matching box_target=[x0,y0,x1,y1]."""
    im = Image.open(os.path.join(REF_DIR, fn)).convert("RGB")
    rgb = np.array(im)
    H, W = rgb.shape[:2]
    with torch.no_grad():
        pred = model([preprocess(im).to(dev)])[0]
    boxes = pred["boxes"].cpu().numpy()
    masks = pred["masks"].cpu().numpy()[:, 0]
    scores = pred["scores"].cpu().numpy()

    # IoU match against box_target
    tx0, ty0, tx1, ty1 = box_target
    best_i, best_iou = -1, -1.0
    for i in range(len(scores)):
        if scores[i] < 0.40:
            continue
        bx0, by0, bx1, by1 = boxes[i]
        ix0, iy0 = max(tx0, bx0), max(ty0, by0)
        ix1, iy1 = min(tx1, bx1), min(ty1, by1)
        inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
        area_a = (tx1 - tx0) * (ty1 - ty0)
        area_b = (bx1 - bx0) * (by1 - by0)
        iou = inter / max(1.0, area_a + area_b - inter)
        if iou > best_iou:
            best_iou = iou
            best_i = i

    prob = masks[best_i].copy()
    alpha = np.clip((prob - 0.38) / 0.35, 0.0, 1.0)

    if include_blue_sword:
        # Also capture the blazing electric-blue broadsword blade connected to Bryan's hands!
        rf, gf, bf = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
        sword_glow = np.clip(((bf - rf) - 42.0) / 55.0, 0.0, 1.0) * np.clip((bf - 135.0) / 80.0, 0.0, 1.0)
        sword_core = np.clip((np.minimum(gf, bf) - 185.0) / 45.0, 0.0, 1.0) * (bf > rf + 15.0)
        sw = np.maximum(sword_glow, sword_core)
        # Keep sword components near upper body / hands
        near_body = ndimage.binary_dilation(alpha > 0.25, iterations=48)
        lbl_s, ns = ndimage.label(sw > 0.12)
        keep_s = np.zeros((H, W), dtype=bool)
        for cid in range(1, ns + 1):
            comp = lbl_s == cid
            if np.any(comp & near_body):
                keep_s |= ndimage.binary_dilation(comp, iterations=4)
        alpha = np.maximum(alpha, sw * keep_s)

    alpha = cv2.GaussianBlur(alpha.astype(np.float32), (5, 5), 0.9)
    rgba = np.dstack([rgb, np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)])
    return rgba


def main():
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    weights = torchvision.models.detection.MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    model = torchvision.models.detection.maskrcnn_resnet50_fpn_v2(weights=weights).to(dev).eval()
    preprocess = weights.transforms()

    # 1. Key & split the 4 studio quadrants
    sheet = Image.open(os.path.join(REF_DIR, "bryan_studio_sprint_2x2.jpg")).convert("RGB")
    full_rgba = key_green_studio(sheet)
    quads = {
        "q0_front": full_rgba[0:512, 0:512],
        "q1_fl45":  full_rgba[0:512, 512:1024],
        "q2_profR": full_rgba[512:1024, 0:512],
        "q3_bl135": full_rgba[512:1024, 512:1024],
    }

    bryan_q = {}
    demon_q = {}
    for qn, qim in quads.items():
        # Save combined keyed quadrant too!
        Image.fromarray(qim).save(os.path.join(OUT_LAYERS, f"pair_{qn}.png"))
        b_im, d_im = split_bryan_and_demon_quadrant(qim, model, preprocess, dev, qn)
        if qn in ("q0_front", "q1_fl45"):
            b_im = add_crisp_detector_antenna(b_im, side="left")
        elif qn == "q2_profR":
            b_im = add_crisp_detector_antenna(b_im, side="profile_right")
        elif qn == "q3_bl135":
            b_im = add_crisp_detector_antenna(b_im, side="back_left")
        bryan_q[qn] = b_im
        demon_q[qn] = d_im
        Image.fromarray(b_im).save(os.path.join(OUT_LAYERS, f"bryan_{qn}.png"))
        Image.fromarray(d_im).save(os.path.join(OUT_LAYERS, f"demon_{qn}.png"))

    # 2. Extract Video 2 Paladin Bryan (0°, 45°, 90°, 180°) + Dungeon Demons (Winged Red, Reaper, Grey Ram)
    v2_specs = [
        ("paladin_000_stand", "v2_sword_f0000.jpg", [197, 454, 558, 1163], False),
        ("paladin_000_sword", "v2_sword_f0192.jpg", [187, 282, 522, 1152], True),
        ("paladin_045_slash", "v2_sword_f0288.jpg", [218, 368, 492, 1154], True),
        ("paladin_090_prof",  "v2_sword_f0240.jpg", [260, 436, 489, 1164], True),
        ("paladin_180_back",  "v2_sword_f0216.jpg", [175, 384, 464, 1168], True),
        ("demon_reaper",      "v2_sword_f0000.jpg", [380, 305, 583, 641],  False),
        ("demon_winged_red",  "v2_sword_f0000.jpg", [31, 377, 321, 1061],  False),
        ("demon_grey_ram",    "v2_sword_f0000.jpg", [498, 397, 762, 1150], False),
    ]
    v2_out = {}
    for out_name, fn, box, sw in v2_specs:
        cut = extract_v2_character(fn, box, model, preprocess, dev, include_blue_sword=sw)
        v2_out[out_name] = cut
        Image.fromarray(cut).save(os.path.join(OUT_LAYERS, f"{out_name}.png"))
        print(f"  [v2] {out_name}: fg_px={np.sum(cut[...,3]>40)}")

    # 3. Build visual audit grid on dark checker
    thumbs = []
    for k in ("q0_front", "q1_fl45", "q2_profR", "q3_bl135"):
        thumbs.append(bryan_q[k])
    for k in ("q0_front", "q1_fl45", "q2_profR", "q3_bl135"):
        thumbs.append(demon_q[k])
    for k in ("paladin_000_sword", "paladin_045_slash", "paladin_090_prof", "paladin_180_back",
              "demon_winged_red", "demon_reaper", "demon_grey_ram", "paladin_000_stand"):
        im_p = Image.fromarray(v2_out[k], "RGBA")
        # Crop to bbox and fit in 512x512
        ys, xs = np.nonzero(v2_out[k][..., 3] > 25)
        crop = im_p.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
        sc = min(470.0 / crop.width, 470.0 / crop.height)
        rsz = crop.resize((max(2, int(crop.width * sc)), max(2, int(crop.height * sc))), Image.LANCZOS)
        cell = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        cell.paste(rsz, ((512 - rsz.width) // 2, 500 - rsz.height), rsz)
        thumbs.append(np.array(cell))

    # 4x4 grid of 256x256 cells
    grid = Image.new("RGB", (1024, 1024), (32, 34, 42))
    yy, xx = np.mgrid[0:1024, 0:1024]
    chk = np.where(((xx // 16 + yy // 16) % 2) == 0, 48, 30)[..., None].astype(np.uint8)
    grid = Image.fromarray(np.repeat(chk, 3, axis=-1), "RGB")
    for idx, th in enumerate(thumbs):
        c_im = Image.fromarray(th, "RGBA").resize((256, 256), Image.LANCZOS)
        gx, gy = (idx % 4) * 256, (idx // 4) * 256
        sub = grid.crop((gx, gy, gx + 256, gy + 256)).convert("RGBA")
        sub.alpha_composite(c_im)
        grid.paste(sub.convert("RGB"), (gx, gy))
    audit_path = os.path.join(DBG_DIR, "extracted_layers_audit.jpg")
    grid.save(audit_path, quality=92)
    print("Saved audit sheet:", audit_path)


if __name__ == "__main__":
    main()
