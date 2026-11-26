"""Key the white studio backdrop out of the "THE DISK" Grok videos (black glove, blue 3.5" floppy, bare forearm).

OpenCV + NumPy only (no SciPy). Per frame:
  1. Estimate the backdrop B as a smooth field: shrink the frame, inpaint the subject out, blow it back up.
     This follows the studio vignette and the grey cyclorama that some clips swing into.
  2. diff = distance from B. Sure subject = diff > CORE, sure backdrop = diff < BG connected to the frame border
     (plus big enclosed gaps between fingers). Small enclosed light patches (shutter glints, label paper) stay solid.
  3. The thin band in between gets a real matte: alpha = projection of (C - B) onto (F - B), F the colour of the
     nearest sure-subject pixel, and its colour is un-mixed from the backdrop so no white rim survives.
Returns straight (un-premultiplied) RGBA uint8, backdrop pixels zeroed.
"""
import cv2
import numpy as np

CORE = 58.0      # diff above this: certainly subject
BG = 16.0        # diff below this: candidate backdrop
GAP_AREA = 900   # enclosed backdrop-like regions bigger than this (px) are holes (between fingers), not subject
BAND = 7.0       # px: soft matte only this close to the solid subject


def estimate_backdrop(rgb, fg_guess):
    h, w, _ = rgb.shape
    sw, sh = w // 8, h // 8
    small = cv2.resize(rgb, (sw, sh), interpolation=cv2.INTER_AREA)
    m = cv2.resize(fg_guess.astype(np.uint8) * 255, (sw, sh), interpolation=cv2.INTER_AREA)
    m = cv2.dilate((m > 0).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    filled = cv2.inpaint(small, m, 6, cv2.INPAINT_TELEA)
    filled = cv2.GaussianBlur(filled, (0, 0), 3.0)
    return cv2.resize(filled, (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)


def _diff(rgb_f, bg):
    d = rgb_f - bg
    # darker-than-backdrop and more-saturated-than-backdrop both count; weight luminance a bit more
    return np.sqrt((d * d).sum(axis=2))


def disk_hull(rgb):
    """Anti-aliased convex hull (float 0..1) of the floppy's saturated blue plastic, or None."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hch, sch, vch = hsv[..., 0].astype(np.int16), hsv[..., 1], hsv[..., 2]
    blue = ((hch >= 98) & (hch <= 128) & (sch >= 90) & (vch >= 60)).astype(np.uint8)
    blue = cv2.morphologyEx(blue, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(blue, 8)
    if n <= 1:
        return None
    big = np.nonzero(stats[1:, cv2.CC_STAT_AREA] >= 400)[0] + 1
    if len(big) == 0:
        return None
    main = big[np.argmax(stats[big, cv2.CC_STAT_AREA])]
    # only blobs near the main one (the same disk split by a finger), never a second far-away blue thing
    mx, my, mw, mh = stats[main, :4]
    pad = max(mw, mh)
    sel = [b for b in big if stats[b, 0] < mx + mw + pad and stats[b, 0] + stats[b, 2] > mx - pad
           and stats[b, 1] < my + mh + pad and stats[b, 1] + stats[b, 3] > my - pad]
    pts = np.column_stack(np.nonzero(np.isin(lbl, sel)))[:, ::-1]
    hull = cv2.convexHull(pts.astype(np.int32))
    h, w, _ = rgb.shape
    m = np.zeros((h * 4, w * 4), np.uint8)
    cv2.fillConvexPoly(m, (hull * 4 + 2).astype(np.int32), 255, lineType=cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def key_frame(rgb, keep="all"):
    """rgb: HxWx3 uint8 (RGB). keep: 'all', or 'arm' (only blobs touching the bottom/right border: the hand
    after the disk has left it)."""
    h, w, _ = rgb.shape
    rgb_f = rgb.astype(np.float32)

    # first pass against flat white to find the subject roughly, then a real backdrop estimate
    white = np.full_like(rgb_f, 250.0)
    rough = _diff(rgb_f, white) > 40.0
    bg = estimate_backdrop(rgb, rough)
    diff = _diff(rgb_f, bg)

    core = (diff > CORE).astype(np.uint8)
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # drop specks (AI noise in the backdrop, confetti)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(core, 8)
    keep_ids = np.zeros(n, bool)
    keep_ids[1:] = stats[1:, cv2.CC_STAT_AREA] >= 250
    core = keep_ids[lbl].astype(np.uint8)

    # backdrop: low diff and either connected to the border or a big enclosed gap
    cand = (diff < BG).astype(np.uint8)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(cand, 4)
    border = np.zeros(n, bool)
    border[np.unique(np.concatenate([lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]]))] = True
    big = stats[:, cv2.CC_STAT_AREA] >= GAP_AREA
    is_bg = (border | big)
    is_bg[0] = False
    sure_bg = is_bg[lbl] & (cand > 0)

    # solid = everything that is not backdrop and not in the soft band; small enclosed light patches become solid
    not_bg = (~sure_bg).astype(np.uint8)
    dist_in = cv2.distanceTransform(core.astype(np.uint8) ^ 1, cv2.DIST_L2, 5)   # distance to nearest core px
    solid = (core > 0) | ((not_bg > 0) & (diff >= BG) & (dist_in <= 1.5))
    # enclosed non-bg islands fully inside the subject (label paper, shutter) -> solid
    holes = ((not_bg > 0) & ~solid).astype(np.uint8)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(holes, 4)
    if n > 1:
        ring = cv2.dilate(solid.astype(np.uint8), np.ones((3, 3), np.uint8)) & (~solid).astype(np.uint8)
        # an island is "inside" if it touches no sure-bg pixel
        bgd = cv2.dilate(sure_bg.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        touches_bg = np.zeros(n, bool)
        ids = lbl[bgd & (holes > 0)]
        touches_bg[np.unique(ids)] = True
        inside = ~touches_bg
        inside[0] = False
        solid = solid | inside[lbl]
        del ring

    # nearest solid colour for every pixel
    src = (~solid).astype(np.uint8)
    dist, labels = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(solid)   # raster order == label order (labels start at 1)
    if len(xs) == 0:
        return np.zeros((h, w, 4), np.uint8)
    lut = np.zeros((len(xs) + 1, 3), np.float32)
    lut[1:] = rgb_f[ys, xs]
    F = lut[labels]

    FB = F - bg
    CB = rgb_f - bg
    den = (FB * FB).sum(axis=2)
    proj = (CB * FB).sum(axis=2) / np.maximum(den, 1.0)
    proj = np.where(den < 400.0, diff / CORE, proj)      # subject colour too close to backdrop: fall back to diff
    alpha = np.clip(proj, 0.0, 1.0)
    alpha = np.where(solid, 1.0, alpha)
    alpha = np.where(sure_bg & (dist > 1.0), 0.0, alpha)
    alpha = np.where(dist > BAND, 0.0, alpha)
    alpha = np.where(alpha < 0.04, 0.0, alpha)

    # un-mix the band from the backdrop
    a3 = np.maximum(alpha, 1e-3)[..., None]
    unmix = np.clip(bg + CB / a3, 0, 255)
    wgt = np.clip((alpha - 0.15) / 0.6, 0.0, 1.0)[..., None]
    col = np.where(solid[..., None], rgb_f, F * (1.0 - wgt) + unmix * wgt)

    # the disk is convex: fill the hull of its blue plastic, so the near-white metal shutter (which wraps the disk's
    # top edge and is barely darker than the backdrop) and the label never get keyed out
    if keep != "arm":
        hull = disk_hull(rgb)
        if hull is not None:
            # only where the pixel is at least a touch off the backdrop (the shutter is; a warped-disk sliver of
            # pure backdrop inside the hull is not), closed so the shutter's flat areas stay whole
            off = np.clip((diff - 5.0) / 4.0, 0.0, 1.0).astype(np.float32)
            off = cv2.morphologyEx(off, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            # glints on the shutter are as white as the backdrop: close the matte across them geometrically
            closed = cv2.morphologyEx((alpha > 0.5).astype(np.uint8),
                                      cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71)))
            hull_in = hull * np.maximum(off, closed.astype(np.float32))
            # outside the disk nothing is light and grey: skin is saturated, the glove is dark. That light-grey
            # rim is backdrop (motion streaks, a halo)
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            pale = ((hsv[..., 2] > 185) & (hsv[..., 1] < 45) & (hull < 0.5)).astype(np.float32)
            pale = cv2.GaussianBlur(pale, (3, 3), 0.8)
            alpha = alpha * (1.0 - pale)
            alpha = np.maximum(alpha, hull_in)
            col = np.where((hull_in > 0.5)[..., None] & ~solid[..., None], rgb_f, col)

    if keep == "nodisk":
        # the release frame: cut the disk (its blue hull, grown a little) out of the hand
        hull = disk_hull(rgb)
        if hull is not None:
            cut = cv2.dilate((hull > 0.2).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
            alpha = alpha * (1.0 - cv2.GaussianBlur(cut, (5, 5), 1.2))
        keep = "arm"

    if keep == "arm":
        m = (alpha > 0.3).astype(np.uint8)
        n, lbl, _, _ = cv2.connectedComponentsWithStats(m, 8)
        edge_ids = np.unique(np.concatenate([lbl[-3:, :].ravel(), lbl[h // 3:, -3:].ravel()]))
        edge_ids = edge_ids[edge_ids != 0]
        armmask = np.isin(lbl, edge_ids).astype(np.uint8)
        armmask = cv2.dilate(armmask, np.ones((5, 5), np.uint8))
        alpha = alpha * cv2.GaussianBlur(armmask.astype(np.float32), (5, 5), 1.0)

    a8 = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    c8 = np.clip(np.round(col), 0, 255).astype(np.uint8)
    c8[a8 == 0] = 0
    return np.dstack([c8, a8])
