"""The floating head monster: progs/floathead.mdl (+ .mdl_0.tga closed mouth, .mdl_1.tga open mouth)
and its held first-person viewmodel progs/v_robdob.mdl (+ .mdl_0.tga), crowned with a jaunty crimson
"M'LADY" felt fedora (pinched teardrop crown, curled snap-brim, midnight-black grosgrain silk ribbon,
brass hatband buckle, vintage "M'LADY" press-card, and ivory-gold-scarlet plume feather).

Built from a turntable video of the head (out/chars/ref/floathead_turntable.mp4, 944x944, the bust spins once).
Four frames are the views: front (frame 137, with the sharper zoomed-in frame 1 warped onto its face), left profile
(50), back (74) and right profile (92).  Frame numbers count from 1, as ffmpeg numbers extracted frames.

Shape: every ring of the mesh is a horizontal slice.  Its width comes from the front silhouette (ears taken out),
its depth from the left profile; the slice is four superellipse quarters.  The nose (the profile's bump between
brow and lip) and the ears (the front silhouette's bumps) are pushed out of that.  The head is cut under the beard
along a slope up to the nape, so the neck stub sits underneath.

Skin atlas (384x384 8-bit paletted + 3x TGA 1152x1152):
  rows   0..255  cylindrical unwrap of the head (Skin 0 closed grin, Skin 1 painted screaming cartoon mouth)
  rows 256..383  crimson wool-felt fedora (outer crown/brim, shaded under-brim & leather sweatband, black silk
                 grosgrain ribbon, brass buckle, "M'LADY" press-card, and plume feather)

Frames (floathead.qc's $frame list must match):
  idle1-8   bob, wobble, and jaunty "M'Lady" fedora-tip salute, mouth shut   (skin 0)
  open1-4   the jaw drops and the acceleration blasts the fedora upward       (skin 1)
  rush1-4   furious chomping jaw while the fedora floats & flutters overhead  (skin 1)
  pain1-4   knocked back, "ow", hat knocked crooked sideways                  (skin 1)

The old one-photo version is build_floathead_photo.py.
python3 -E -P build_floathead.py [--preview DIR] [--debug DIR] [--out DIR] [--size UNITS] [--bright X]
"""
import math
import os
import struct
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_char_models as B
import robdob_vm as RV
from build_head_grenade import smoothstep

ARG = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = ARG("--out", B.PROGS)
PREVIEW = ARG("--preview", None)
DEBUG = ARG("--debug", None)
HEIGHT = float(ARG("--size", 40))        # quake units, top of the skull to the bottom of the beard: a big head
BRIGHT = float(ARG("--bright", 1.5))     # the world heads are drawn fullbright (EF_FULLBRIGHT): the skin is what you see
VIDEO = os.path.join(B.REF, "floathead_turntable.mp4")

NH, MH = 48, 56                          # ring vertices (vertex 0 at the back of the head), rings (0 = chin)
SW, HEAD_SH, SKIN_H = 384, 256, 384      # top 256 rows = head unwrap; bottom 128 rows = fedora & accessories
TGA_MUL = 3

# the views: video frame -> (yaw, row of the top of the ear).  Yaw 0 faces the camera, 90 shows his left side.
HIRES = 1                                # zoomed-in front frame, warped onto the front view's face
VIEWS = {137: (0, 372), 50: (90, 382), 74: (180, 375), 92: (270, 382)}
FRONT, PROFILE = 137, 50                 # the shape comes from these two
# canonical rows are frame 50's rows: crown (found), top of the ear, the beard's lowest point, the nape cut
EAR = 382
ZBOT = 716                               # bottom of the beard
NAPE = 600                               # the cut under the head rises to here at the back of the neck
JAWLINE = 610                            # below this the head narrows to the tip of the beard
NOSE_ROWS = (398, 520)                   # profile rows bridged over to take the nose off the face
EAR_ROWS = (360, 548)                    # front rows bridged over to take the ears off the width
HOLD = (150, 560)                        # column fit only between these rows (neck and the thin crown follow)
N_FRONT, N_BACK = 2.6, 2.25              # superellipse exponents: squarer face, rounder skull

# Fedora resting placement in canonical head space (HEIGHT = 40 -> skull z in [-20, +20])
# Cocked up on his right temple (-Y, facing inward toward the crosshair in 1st-person v_robdob.mdl!) and dipped over +Y brow
HAT_ORIGIN = np.array([-0.25, 0.48, 11.45])  # snug low-pulled hatband right above brow/temples
HAT_BASE_ROLL = -6.5                         # -deg lifts right side (-Y, card/feather side) & dips left (+Y) rakishly over brow
HAT_BASE_PITCH = 4.0                         # +deg tips front snap-brim boldly forward toward his eyebrows
HAT_BASE_YAW = 4.0                           # subtle swaggering twist toward his right side
HAT_RX, HAT_RY = 16.95, 13.45                # snug oval fit around skull + pompadour
HAT_BRIM_MUL = 1.52                          # snap-brim outer reach relative to crown base (~51.5u x 40.9u)
N_HAT = 48                                   # angular segments around the fedora


def video_frames(ids):
    cap = cv2.VideoCapture(VIDEO)
    out, n = {}, 0
    while len(out) < len(ids):
        ok, f = cap.read()
        if not ok:
            break
        n += 1
        if n in ids:
            out[n] = f[..., ::-1].astype(np.float32)
    cap.release()
    missing = set(ids) - set(out)
    assert not missing, "frames %s not in %s" % (sorted(missing), VIDEO)
    return out


def silhouette(a):
    """the bust against the pale backdrop and the grey turntable: anything saturated (skin) or dark (hair)"""
    m = (a.max(2) - a.min(2) > 28) | (a.mean(2) < 110)
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    m = lab == 1 + int(np.argmax(ndimage.sum(m, lab, range(1, n + 1))))
    return ndimage.binary_fill_holes(m)


def warp_hires(hi, lo):
    """the zoomed-in front frame onto the front view: SIFT matches on the face, a similarity fitted with RANSAC;
    where the zoomed frame does not reach (the top of the hair) the front view shows through with smooth tonal match"""
    g = lambda a: cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    sift = cv2.SIFT_create(4000)
    k1, d1 = sift.detectAndCompute(g(hi), None)
    k2, d2 = sift.detectAndCompute(g(lo), None)
    good = [m for m, n in cv2.BFMatcher().knnMatch(d1, d2, k=2) if m.distance < 0.75 * n.distance]
    p1 = np.float32([k1[m.queryIdx].pt for m in good])
    p2 = np.float32([k2[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=4.0)
    H, W = lo.shape[:2]
    w = cv2.warpAffine(hi, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(-1, -1, -1))
    cover = w[..., 0] >= 0
    # Soften the upper forehead transition and match low-frequency illumination near the top edge so when the
    # fedora blows off his head during a dash there is no harsh horizontal lighting seam across his brow.
    safe = np.where(cover[..., None], w, lo)
    lo_lf = ndimage.gaussian_filter(lo, (28, 28, 0))
    hi_lf = ndimage.gaussian_filter(safe, (28, 28, 0))
    ratio = np.clip(lo_lf / np.maximum(hi_lf, 12.0), 0.72, 1.38)
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    rim_match = 1.0 - smoothstep(325.0, 405.0, yy)
    w_matched = safe * (1.0 + rim_match * (ratio - 1.0))
    eroded = ndimage.binary_erosion(cover, iterations=16).astype(np.float32)
    feather = ndimage.gaussian_filter(eroded, 10.0)[..., None]
    print("front: frame %d onto frame %d, %d/%d matches, scale %.3f" % (HIRES, FRONT, inl.sum(), len(good),
                                                                       np.hypot(M[0, 0], M[0, 1])))
    return (w_matched * feather + lo * (1 - feather)).clip(0, 255)


def edges(m, rows):
    """left and right silhouette columns at (fractional) rows, nan where the row is empty"""
    r = np.clip(np.round(rows).astype(int), 0, m.shape[0] - 1)
    has = m[r].any(1)
    lo = np.where(has, m[r].argmax(1), np.nan).astype(float)
    hi = np.where(has, m.shape[1] - 1 - m[r][:, ::-1].argmax(1), np.nan).astype(float)
    return lo, hi


def bridge(y, rows, a, b):
    """y with rows a..b replaced by a smooth line between its values just outside them"""
    y = y.copy()
    i = (rows >= a) & (rows <= b)
    ia, ib = np.nonzero(rows < a)[0][-1], np.nonzero(rows > b)[0][0]
    y[i] = np.interp(rows[i], [rows[ia], rows[ib]], [y[ia], y[ib]])
    return y


class View:
    def __init__(self, n, img, crown):
        self.n, self.img = n, img
        self.yaw, self.ear = VIEWS[n]
        self.mask = silhouette(img)
        self.crown = np.nonzero(self.mask.any(1))[0][0]
        self.CROWN = crown

    def row(self, z):
        """canonical row -> this frame's row: crown and ear top pinned, one to one below the ear"""
        z = np.asarray(z, float)
        above = self.crown + (z - self.CROWN) * (self.ear - self.crown) / (EAR - self.CROWN)
        return np.where(z < EAR, above, self.ear + (z - EAR))

    def sample(self, img, u, v):
        return np.stack([ndimage.map_coordinates(img[..., c], [v, u], order=1, mode="nearest") for c in range(3)], -1)


def build():
    fr = video_frames(sorted(set(VIEWS) | {HIRES}))
    crown = int(np.nonzero(silhouette(fr[PROFILE]).any(1))[0][0])
    fr[FRONT] = warp_hires(fr[HIRES], fr[FRONT])
    views = {n: View(n, fr[n], crown) for n in VIEWS}
    F, P = views[FRONT], views[PROFILE]

    # slices from the crown to the bottom of the beard, closer together at the top where the skull rounds over
    t = np.linspace(0, 1, MH)
    z = ZBOT - (ZBOT - crown - 3) * (1 - (1 - t) ** 1.35)            # ring rows; t=0 the chin, t=1 the crown
    rows = np.arange(crown, ZBOT + 1, dtype=float)

    # width: the front silhouette about the face's middle, ears bridged over (their bumps go back on as ears)
    lo, hi = edges(F.mask, F.row(rows))
    ok = ~np.isnan(lo)
    lo, hi = np.interp(rows, rows[ok], lo[ok]), np.interp(rows, rows[ok], hi[ok])
    c0 = float(np.median(((lo + hi) / 2)[(rows > 200) & (rows < 340)]))
    hw_ears = ndimage.gaussian_filter1d((hi - lo) / 2, 2)
    hw = ndimage.gaussian_filter1d(bridge((hi - lo) / 2, rows, *EAR_ROWS), 3)
    # under the jaw the front silhouette is neck and then shoulders: narrow it to the tip of the beard instead
    k = np.clip((rows - JAWLINE) / (ZBOT - JAWLINE), 0, 1)
    hw = np.where(rows > JAWLINE, np.interp(JAWLINE, rows, hw) * (1 - 0.62 * k ** 1.6), hw)
    ear = np.clip(hw_ears - hw, 0, None) * ((rows > EAR_ROWS[0]) & (rows < EAR_ROWS[1]))
    # depth: the left profile (face to the image left) about the ear's middle column
    lo, hi = edges(P.mask, P.row(rows))
    ok = ~np.isnan(lo)
    lo, hi = np.interp(rows, rows[ok], lo[ok]), np.interp(rows, rows[ok], hi[ok])
    ear_u = EAR_COL
    xf_nose = ndimage.gaussian_filter1d(ear_u - lo, 1.5)               # front of the face, nose and all
    xf = ndimage.gaussian_filter1d(bridge(ear_u - lo, rows, *NOSE_ROWS), 2)
    xb = ndimage.gaussian_filter1d(ear_u - hi, 3)                    # back of the head (negative)
    # under the head: from the nape the cut slopes forward and down to the beard's tip
    s = np.clip((rows - NAPE) / (ZBOT - NAPE), 0, 1)
    cut = np.interp(NAPE, rows, xb) + s * (np.interp(ZBOT, rows, xf) - 12 - np.interp(NAPE, rows, xb))
    xb = np.where(rows > NAPE, np.maximum(xb, cut), xb)
    nose = np.clip(xf_nose - xf, 0, None)

    I = lambda y: np.interp(z, rows, y)
    W, XF, XB, NOSE, EARB = I(hw), I(xf), I(xb), I(nose), I(ear)
    W = np.maximum(W, 3.0)
    XM = XB + 0.42 * (XF - XB)                                       # depth of the widest point (about the ears)
    th = -np.pi / 2 + 2 * np.pi * np.arange(NH) / NH                # k=0 back of the head, k=NH/2 the face
    cs, sn = np.cos(th), np.sin(th)
    se = lambda c, n: np.sign(c) * np.abs(c) ** (2 / n)
    front = sn[None] > 0
    lat = W[:, None] * np.where(front, se(cs, N_FRONT)[None], se(cs, N_BACK)[None])
    dep = np.where(front, (XF - XM)[:, None] * se(sn, N_FRONT)[None], (XM - XB)[:, None] * se(sn, N_BACK)[None])
    x = XM[:, None] + dep
    # the nose: the profile's bump, narrow at the bridge and spreading to the nostrils
    nw = 16 + 26 * smoothstep(NOSE_ROWS[0] + 40, NOSE_ROWS[1] - 10, z)[:, None]
    x = x + NOSE[:, None] * np.exp(-(lat / nw) ** 2) * front
    # the ears: out sideways at the ear's depth
    ex = np.exp(-((x - 0) / 40) ** 2) * (np.abs(cs)[None] > 0.5)
    lat = lat + np.sign(cs)[None] * EARB[:, None] * ex
    Pg = np.zeros((MH, NH, 3))
    Pg[..., 0], Pg[..., 1], Pg[..., 2] = x, c0 + lat, z[:, None]
    m = dict(P=Pg, c0=c0, z=z, crown=crown, views=views, front=F.img)
    if DEBUG:
        debug_shape(m, rows, hw, hw_ears, xf_nose, xf, xb)
    return m


EAR_COL = 530                            # frame 50: the ear's middle column, the head's depth origin


def debug_shape(m, rows, hw, hw_ears, xf_nose, xf, xb):
    os.makedirs(DEBUG, exist_ok=True)
    for n, v in m["views"].items():
        a = v.img.copy()
        a[v.mask] = a[v.mask] * 0.6 + np.array([0, 120, 0]) * 0.4
        Image.fromarray(a.clip(0, 255).astype(np.uint8)).resize((472, 472)).save(os.path.join(DEBUG, "mask_%03d.jpg" % n))
    Image.fromarray(m["front"].clip(0, 255).astype(np.uint8)).save(os.path.join(DEBUG, "front_composite.jpg"))
    im = Image.new("RGB", (900, 760), (30, 30, 30))
    d = ImageDraw.Draw(im)
    for y, col in ((hw_ears, (90, 90, 255)), (hw, (255, 255, 255)), (xf_nose, (255, 90, 90)), (xf, (255, 200, 0)),
                   (-xb, (0, 220, 120))):
        d.line(list(zip(450 + y, rows)), fill=col, width=2)
    d.text((10, 10), "white: half width  blue: with ears  red/yellow: face front with/without nose  green: back", fill=(255, 255, 255))
    im.save(os.path.join(DEBUG, "profiles.png"))


def paint_mouth(rgb):
    """skin 1: a big cartoon mouth between the lips (dark inside, top teeth, tongue), in front view pixels"""
    H, W = rgb.shape[:2]
    S = 4                                                           # supersampled drawing
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mx, my = MOUTH
    x0, x1, y0, y1 = (mx - MOUTH_RX) * S, (mx + MOUTH_RX) * S, MOUTH_TOP * S, MOUTH_BOT * S
    d.ellipse([x0, y0, x1, y1], fill=(28, 4, 6, 255))
    d.ellipse([x0 + 10 * S, y0 + 5 * S, x1 - 10 * S, y1 - 2 * S], fill=(62, 8, 12, 255))
    d.ellipse([(mx - 32) * S, (MOUTH_TOP + 17) * S, (mx + 36) * S, (MOUTH_BOT + 6) * S], fill=(176, 64, 74, 255))
    d.line([(mx * S, (MOUTH_TOP + 20) * S), (mx * S, (MOUTH_BOT - 2) * S)], fill=(130, 40, 48, 255), width=2 * S)
    lay = Image.composite(lay, Image.new("RGBA", lay.size, (0, 0, 0, 0)), mouth_shape(W, H, S))
    # top teeth: a row along the upper lip, clipped to the mouth
    teeth = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    t = ImageDraw.Draw(teeth)
    tw = 14
    for i in range(-5, 5):
        cx = mx + i * tw + tw / 2
        t.rounded_rectangle([(cx - tw / 2 + 1) * S, (MOUTH_TOP - 2) * S, (cx + tw / 2 - 1) * S, (MOUTH_TOP + 9) * S],
                            radius=3 * S, fill=(232, 226, 205, 255))
    teeth = Image.composite(teeth, Image.new("RGBA", lay.size, (0, 0, 0, 0)), mouth_shape(W, H, S))
    lay = Image.alpha_composite(lay, teeth)
    lay = lay.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(lay).astype(np.float32)
    al = a[..., 3:] / 255
    return rgb * (1 - al) + a[..., :3] * al


def mouth_shape(W, H, S):
    m = Image.new("L", (W * S, H * S), 0)
    mx = MOUTH[0]
    ImageDraw.Draw(m).ellipse([(mx - MOUTH_RX) * S, MOUTH_TOP * S, (mx + MOUTH_RX) * S, MOUTH_BOT * S], fill=255)
    return m


# the mouth in front view pixels (frame 137 with frame 1 on it)
MOUTH = (478, 560)
MOUTH_RX, MOUTH_TOP, MOUTH_BOT = 70, 545, 580
JAW = 62                                 # pixels the chin drops when the mouth is fully open
VM_HEIGHT = 15.2                          # the head in your hand: quake units tall
VM_POS = (18.8, -18.9, -9.3)              # ...and where it floats in eye space (x forward, y left, z up)
VM_YAW = 126                             # face turned back towards the eye
VM_PITCH = 13                             # nod: + tips the face up (robdob_viewmodel_tuner.html / apply_robdob_vm.py set these)
VM_ROLL = 0                              # tilt: + puts the left ear up


# ------------------------------------------------------------------ Crimson "M'LADY" Fedora (Mesh + Texture Strip)

def _hat_se(v, n=2.35):
    return np.sign(v) * (np.abs(v) ** (2.0 / n))


def _hat_xy(th, r_mul, dr=0.0):
    """Superellipse point (hx, hy) at angle th (0 = +x front, pi/2 = +y left) with radial scale r_mul and offset dr."""
    c, s = np.cos(th), np.sin(th)
    bx, by = _hat_se(c), _hat_se(s)
    rx = HAT_RX * r_mul + dr
    ry = HAT_RY * r_mul + dr
    return rx * bx, ry * by


def _brim_z(th, t):
    """Snap-brim height curve at normalized brim radius t in [0, 1] (leaves crown flat, swoops down in front, curls up at sides/back)."""
    c = np.cos(th)
    wf = np.maximum(0.0, c) ** 1.35
    down_front = -2.45 * (t ** 1.45) * wf
    up_back = 2.15 * (t ** 2.25) * (1.0 - wf)
    lip = 0.50 * (t ** 3.8)
    return down_front + up_back + lip


def _crown_r_z(th, u):
    """Outer crown (r_mul, hz) for u in [0, 1] from band base to top ridge, with classic front side-pinches."""
    c = np.cos(th)
    hz_ridge = 11.65 + 0.80 * c
    taper = 1.01 - (0.18 + 0.04 * c) * (u ** 0.92)
    # Symmetric gangster/detective thumb-pinches in the upper hollow of the crown (u > 0.44, above the skull dome)
    ang = np.abs((th + np.pi) % (2.0 * np.pi) - np.pi)
    u_p = np.clip((u - 0.44) / 0.56, 0.0, 1.0)
    pinch = 0.165 * (np.sin(np.pi * u_p) ** 1.15) * np.exp(-((ang - 0.64) / 0.36) ** 2)
    return taper - pinch, 0.12 + (hz_ridge - 0.12) * u


def hat_mesh():
    """Builds the closed crimson fedora, black grosgrain silk ribbon, brass buckle, 'M'LADY' press-card,
    and curved plume feather in local hat space (hz=0 at band base, +hx front, +hy left).
    Returns (Vh, tris, st) with counter-clockwise outward winding and UVs in base 384x384 space (rows 256..383).
    """
    Vh, st, tris = [], [], []
    max_x = HAT_RX * HAT_BRIM_MUL * 1.04
    max_y = HAT_RY * HAT_BRIM_MUL * 1.04

    def uv_outer_polar(th, s_prof):
        return (64.0 + 53.0 * s_prof * math.cos(th),
                320.0 - 53.0 * s_prof * math.sin(th))

    def uv_inner(x, y):
        return (192.0 + 53.0 * np.clip(x / max_x, -1.0, 1.0),
                320.0 - 53.0 * np.clip(y / max_y, -1.0, 1.0))

    def add_v(pt, uv):
        Vh.append(np.asarray(pt, dtype=float))
        st.append((float(uv[0]), float(uv[1])))
        return len(Vh) - 1

    def add_tri(a, b, c, out_dir):
        pa, pb, pc = Vh[a], Vh[b], Vh[c]
        if np.cross(pb - pa, pc - pa) @ np.asarray(out_dir, dtype=float) < 0:
            b, c = c, b
        tris.append((a, b, c))

    def add_quad(a, b, c, d, out_dir):
        add_tri(a, b, c, out_dir)
        add_tri(a, c, d, out_dir)

    ths = 2.0 * np.pi * np.arange(N_HAT) / N_HAT

    # --- 1A. Interior Crown Ceiling + Sweatband + Under-Brim (Island 2: shaded underside, normals down/inward) ---
    c_in_apex = add_v((0.0, 0.0, 9.55), uv_inner(0.0, 0.0))
    in_rings = []
    # Inner crown ceiling -> sweatband -> brim underside out to rolled edge
    for r_m, hz_fn, n_sign in (
        (0.58, lambda th: 9.45, -1),
        (0.84, lambda th: 5.80, -1),
        (0.95, lambda th: 1.40, -1),
        (0.97, lambda th: -0.38, -1),
        (0.97 + 0.34 * (HAT_BRIM_MUL - 0.97), lambda th: _brim_z(th, 0.34) - 0.56, -1),
        (0.97 + 0.70 * (HAT_BRIM_MUL - 0.97), lambda th: _brim_z(th, 0.70) - 0.54, -1),
        (0.97 + 0.95 * (HAT_BRIM_MUL - 0.97), lambda th: _brim_z(th, 0.95) - 0.36, -1),
        (HAT_BRIM_MUL + 0.015, lambda th: _brim_z(th, 1.00) + 0.02, 0),
    ):
        ring = []
        for th in ths:
            x, y = _hat_xy(th, r_m)
            z = float(hz_fn(th))
            ring.append(add_v((x, y, z), uv_inner(x, y)))
        in_rings.append(ring)

    # Cap inner ceiling (visible from below when the hat blows off his head: outward normal is -Z)
    for k in range(N_HAT):
        k1 = (k + 1) % N_HAT
        add_tri(in_rings[0][k], in_rings[0][k1], c_in_apex, (0.0, 0.0, -1.0))

    for ri in range(len(in_rings) - 1):
        r0, r1 = in_rings[ri], in_rings[ri + 1]
        for k in range(N_HAT):
            k1 = (k + 1) % N_HAT
            th_m = 2.0 * np.pi * (k + 0.5) / N_HAT
            if ri < 3:
                # Inner wall faces inward toward (0, 0) and downward
                out_d = (-math.cos(th_m), -math.sin(th_m), -0.35)
            elif ri < 6:
                # Brim underside faces mostly -Z
                out_d = (0.15 * math.cos(th_m), 0.15 * math.sin(th_m), -1.0)
            else:
                # Lower-outer rim rounding outward
                out_d = (math.cos(th_m), math.sin(th_m), -0.45)
            add_quad(r0[k], r0[k1], r1[k1], r1[k], out_d)

    # --- 1B. Rolled Outer Rim -> Snap-Brim Top -> Pinched Crown -> Teardrop Top Crease (Island 1: monotonic polar UV) ---
    out_rings = []
    # Monotonic s_prof from 0.98 (outer rim) -> 0.63 (crown-brim crease) -> 0.32 (crown top ridge) -> 0.08 (inner bash)
    brim_top_specs = [
        (HAT_BRIM_MUL + 0.015, lambda th: _brim_z(th, 1.00) + 0.02, "rim",    0.98),
        (1.01 + 0.93 * (HAT_BRIM_MUL - 1.01), lambda th: _brim_z(th, 0.93) + 0.42, "brim",   0.92),
        (1.01 + 0.64 * (HAT_BRIM_MUL - 1.01), lambda th: _brim_z(th, 0.64) + 0.48, "brim",   0.81),
        (1.01 + 0.28 * (HAT_BRIM_MUL - 1.01), lambda th: _brim_z(th, 0.28) + 0.42, "brim",   0.70),
        (1.01, lambda th: 0.22, "crease", 0.63),
    ]
    for r_m, hz_fn, kind, sp in brim_top_specs:
        ring = []
        for th in ths:
            x, y = _hat_xy(th, r_m)
            z = float(hz_fn(th))
            ring.append((add_v((x, y, z), uv_outer_polar(float(th), sp)), kind))
        out_rings.append(ring)

    # Pinched crown outer wall u in (0.24 .. 1.00) -> s_prof in (0.56 .. 0.32)
    for u, sp in ((0.24, 0.56), (0.46, 0.49), (0.68, 0.42), (0.88, 0.36), (1.00, 0.32)):
        ring = []
        for th in ths:
            rm, z = _crown_r_z(th, u)
            x, y = _hat_xy(th, float(rm))
            ring.append((add_v((x, y, float(z)), uv_outer_polar(float(th), sp)), "crown"))
        out_rings.append(ring)

    # Teardrop top bash (ridge -> inner slope -> smooth flat-ish teardrop basin)
    for rho, dz_ridge, sp in ((0.84, +0.34, 0.26), (0.56, -0.72, 0.18), (0.26, -1.12, 0.09)):
        ring = []
        for th in ths:
            rm_top, z_top = _crown_r_z(th, 1.0)
            x, y = _hat_xy(th, float(rm_top) * rho)
            # Blend out the front-to-back slope near the centre so the central pinch dome has smooth level normals
            z_level = 11.65 + (float(z_top) - 11.65) * (rho ** 0.7)
            z = z_level + dz_ridge
            ring.append((add_v((x, y, z), uv_outer_polar(float(th), sp)), "top"))
        out_rings.append(ring)

    c_top_apex = add_v((0.0, 0.0, 11.65 - 0.92), (64.0, 320.0))

    for ri in range(len(out_rings) - 1):
        r0, r1 = out_rings[ri], out_rings[ri + 1]
        kind = r1[0][1]
        for k in range(N_HAT):
            k1 = (k + 1) % N_HAT
            th_m = 2.0 * np.pi * (k + 0.5) / N_HAT
            if ri == 0:
                out_d = (math.cos(th_m), math.sin(th_m), 0.55)
            elif kind in ("brim", "crease"):
                out_d = (0.15 * math.cos(th_m), 0.15 * math.sin(th_m), 1.0)
            elif kind == "crown":
                out_d = (math.cos(th_m), math.sin(th_m), 0.22)
            else:
                out_d = (0.08 * math.cos(th_m), 0.08 * math.sin(th_m), 1.0)
            add_quad(r0[k][0], r0[k1][0], r1[k1][0], r1[k][0], out_d)

    last_ring = out_rings[-1]
    for k in range(N_HAT):
        k1 = (k + 1) % N_HAT
        add_tri(last_ring[k][0], last_ring[k1][0], c_top_apex, (0.0, 0.0, 1.0))

    # --- 2. Midnight-Black Grosgrain Silk Hatband Ribbon (Island 3: u in [258, 336], v in [260, 296]) ---
    # Bold continuous 360-degree silk band sitting cleanly above the crown-brim crease
    rib_rings = []
    for vi, (u_c, v_tex, dr) in enumerate(((0.025, 295.0, 0.48), (0.140, 278.0, 0.50), (0.255, 261.0, 0.45))):
        ring = []
        for k in range(N_HAT + 1):
            th = 2.0 * np.pi * k / N_HAT
            rm, z = _crown_r_z(th, u_c)
            x, y = _hat_xy(th, float(rm), dr=dr)
            u_tex = 258.0 + 78.0 * (k / N_HAT)
            ring.append(add_v((x, y, float(z)), (u_tex, v_tex)))
        rib_rings.append(ring)

    for ri in range(len(rib_rings) - 1):
        r0, r1 = rib_rings[ri], rib_rings[ri + 1]
        for k in range(N_HAT):
            th_m = 2.0 * np.pi * (k + 0.5) / N_HAT
            add_quad(r0[k], r0[k + 1], r1[k + 1], r1[k], (math.cos(th_m), math.sin(th_m), 0.08))
    # Top & bottom lips of the ribbon back to the crown so looking from above or below sees a thick solid silk band
    top_crown_ring, bot_crown_ring = [], []
    for k in range(N_HAT + 1):
        th = 2.0 * np.pi * k / N_HAT
        rm_t, z_t = _crown_r_z(th, 0.258)
        xt, yt = _hat_xy(th, float(rm_t), dr=0.02)
        top_crown_ring.append(add_v((xt, yt, float(z_t)), (258.0 + 78.0 * (k / N_HAT), 261.0)))
        rm_b, z_b = _crown_r_z(th, 0.022)
        xb, yb = _hat_xy(th, float(rm_b), dr=0.02)
        bot_crown_ring.append(add_v((xb, yb, float(z_b)), (258.0 + 78.0 * (k / N_HAT), 295.0)))
    for k in range(N_HAT):
        add_quad(rib_rings[-1][k], rib_rings[-1][k + 1], top_crown_ring[k + 1], top_crown_ring[k], (0.0, 0.0, 1.0))
        add_quad(rib_rings[0][k], rib_rings[0][k + 1], bot_crown_ring[k + 1], bot_crown_ring[k], (0.0, 0.0, -1.0))

    # --- 3. Polished Brass/Gold Side Hatband Buckle (Island 4: u in [258, 294], v in [302, 324]) ---
    th_b = math.radians(-74.0)
    rm_b, z_b0 = _crown_r_z(th_b, 0.14)
    bx0, by0 = _hat_xy(th_b, float(rm_b), dr=0.72)
    n_b = np.array([math.cos(th_b), math.sin(th_b), 0.06])
    n_b /= np.linalg.norm(n_b)
    t_b = np.array([-math.sin(th_b), math.cos(th_b), 0.0])
    up_b = np.cross(t_b, n_b)
    b_cen = np.array([bx0, by0, float(z_b0)])
    b_out, b_in = [], []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p_o = b_cen + t_b * (sx * 1.65) + up_b * (sy * 1.62) + n_b * 0.14
        p_i = b_cen + t_b * (sx * 0.96) + up_b * (sy * 0.90) + n_b * 0.16
        uv_o = (276.0 + sx * 17.0, 313.0 - sy * 10.0)
        uv_i = (276.0 + sx * 9.0, 313.0 - sy * 5.5)
        b_out.append(add_v(p_o, uv_o))
        b_in.append(add_v(p_i, uv_i))
    for i in range(4):
        i1 = (i + 1) % 4
        add_quad(b_out[i], b_out[i1], b_in[i1], b_in[i], n_b)

    # --- 4. Jaunty Vintage "M'LADY" Press-Card (Island 5: u in [258, 336], v in [330, 378]) ---
    # Tucked inside the top of the black silk ribbon on the front-right temple (-Y, th = -40 deg: faces crosshair in 1P VM!)
    th_c = math.radians(-40.0)
    rm_c, z_c0 = _crown_r_z(th_c, 0.21)
    cx0, cy0 = _hat_xy(th_c, float(rm_c), dr=0.26)
    n_rad = np.array([math.cos(th_c), math.sin(th_c), 0.0])
    t_tan = np.array([-math.sin(th_c), math.cos(th_c), 0.0])   # +v_right when viewing outer face in Quake!
    # Flare the card 16 deg outward from vertical and rake it 7 deg backward (-t_tan on -Y side) for cartoon swagger
    flare = math.radians(16.0)
    rake = math.radians(-7.0)
    card_up = np.array([0.0, 0.0, math.cos(flare)]) + n_rad * math.sin(flare) + t_tan * math.sin(rake)
    card_up /= np.linalg.norm(card_up)
    card_right = t_tan - card_up * (t_tan @ card_up)
    card_right /= np.linalg.norm(card_right)
    card_n = np.cross(card_right, card_up)
    if card_n @ n_rad < 0:
        card_n = -card_n
    card_base = np.array([cx0, cy0, float(z_c0)])
    CW, CH, CT = 7.8, 5.2, 0.44                                # width, height, cardstock thickness (immune to uint8 snap)

    # Slight barrel curve along width so the bottom hugs the curved ribbon naturally
    nx_steps = (-0.5, 0.0, 0.5)
    ny_steps = (0.0, 0.5, 1.0)

    def card_pt(sx, sy, side_sign):
        bend = -0.38 * ((2.0 * sx) ** 2) * (1.0 - 0.55 * sy)
        return (card_base
                + card_right * (sx * CW)
                + card_up * (sy * CH)
                + card_n * (bend + side_sign * (CT * 0.5)))

    # Front/outer face (u left->right along +card_right)
    cf = [[add_v(card_pt(sx, sy, +1.0), (259.0 + (sx + 0.5) * 76.0, 377.0 - sy * 46.0))
           for sx in nx_steps] for sy in ny_steps]
    for j in range(2):
        for i in range(2):
            add_quad(cf[j][i], cf[j][i + 1], cf[j + 1][i + 1], cf[j + 1][i], card_n)

    # Back/inner face (viewed from -card_n: screen-right is -card_right, so u runs +0.5 -> -0.5 to read un-mirrored!)
    cb = [[add_v(card_pt(sx, sy, -1.0), (259.0 + (0.5 - sx) * 76.0, 377.0 - sy * 46.0))
           for sx in nx_steps] for sy in ny_steps]
    for j in range(2):
        for i in range(2):
            add_quad(cb[j][i], cb[j][i + 1], cb[j + 1][i + 1], cb[j + 1][i], -card_n)

    # Crisp cardstock top & side edges
    for i in range(2):
        add_quad(cf[2][i], cf[2][i + 1], cb[2][i + 1], cb[2][i], card_up)
    for j in range(2):
        add_quad(cf[j][0], cf[j + 1][0], cb[j + 1][0], cb[j][0], -card_right)
        add_quad(cf[j][2], cf[j + 1][2], cb[j + 1][2], cb[j][2], card_right)

    # --- 5. Jaunty Ivory-Gold-Scarlet Plume Feather (Island 6: u in [344, 378], v in [260, 378]) ---
    # Sweeps from the gold buckle (th = -76 deg, hz = 1.5) upward and backward past the crown ridge (hz = 13.8)
    N_F = 10
    spines, n_fs = [], []
    for si in range(N_F):
        tf = si / (N_F - 1)
        th_f = math.radians(-76.0 - 48.0 * (tf ** 1.08))
        hz_f = 1.45 + 12.55 * (tf ** 0.88) - 1.15 * (tf ** 2.6)
        rm_f, _ = _crown_r_z(th_f, min(1.0, hz_f / 11.6))
        flare_r = 0.78 + 1.90 * (tf ** 1.15)
        fx, fy = _hat_xy(th_f, float(rm_f), dr=flare_r)
        spines.append(np.array([fx, fy, hz_f]))
        nf = np.array([math.cos(th_f), math.sin(th_f), 0.14])
        n_fs.append(nf / np.linalg.norm(nf))

    f_front, f_back = [], []
    for si in range(N_F):
        tf = si / (N_F - 1)
        spine, n_f = spines[si], n_fs[si]
        t_f = spines[min(N_F - 1, si + 1)] - spines[max(0, si - 1)]
        t_f /= np.linalg.norm(t_f)
        w_dir = np.cross(n_f, t_f)
        w_dir /= np.linalg.norm(w_dir)
        half_w = 0.22 + 2.35 * (math.sin(math.pi * (tf ** 0.78)) ** 0.85) * (1.0 - 0.18 * tf)
        if si == N_F - 1:
            half_w = 0.18
        v_uv = 377.0 - tf * 116.0
        row_f, row_b = [], []
        for wi, (ws, u_uv, keel) in enumerate(((-1.0, 345.0, -0.18), (0.0, 361.0, +0.16), (1.0, 377.0, -0.18))):
            p_mid = spine + w_dir * (ws * half_w) + n_f * keel
            row_f.append(add_v(p_mid + n_f * 0.21, (u_uv, v_uv)))
            row_b.append(add_v(p_mid - n_f * 0.21, (377.0 - (u_uv - 345.0), v_uv)))
        f_front.append((row_f, n_f))
        f_back.append((row_b, -n_f))

    for si in range(N_F - 1):
        rf0, nf = f_front[si]
        rf1, _ = f_front[si + 1]
        rb0, nb = f_back[si]
        rb1, _ = f_back[si + 1]
        for wi in range(2):
            add_quad(rf0[wi], rf0[wi + 1], rf1[wi + 1], rf1[wi], nf)
            add_quad(rb0[wi], rb0[wi + 1], rb1[wi + 1], rb1[wi], nb)

    return np.array(Vh), np.array(tris), np.array(st)


def _load_font(size, serif=False):
    candidates = ("georgiab.ttf", "timesbd.ttf", "arialbd.ttf", "impact.ttf", "consolab.ttf") if serif else (
        "arialbd.ttf", "impact.ttf", "consolab.ttf", "calibrib.ttf")
    for fn in candidates:
        p = os.path.join(r"C:\Windows\Fonts", fn)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def fedora_strip(mul):
    """Renders the 384*mul x 128*mul pre-gain RGB strip (rows 256..383) for the crimson 'M'LADY' fedora."""
    S = mul * 2                                                     # 2x supersampled over final TGA resolution
    W_s, H_s = SW * S, (SKIN_H - HEAD_SH) * S
    rng = np.random.default_rng(1337)

    # Base wool-felt weave noise across the strip
    coarse = np.asarray(
        Image.fromarray((rng.random((96, 32)) * 255).astype(np.uint8), "L").resize((W_s, H_s), Image.BILINEAR),
        dtype=np.float32,
    ) / 255.0
    fine = rng.random((H_s, W_s), dtype=np.float32)
    yy, xx = np.meshgrid(np.arange(H_s, dtype=np.float32) / S, np.arange(W_s, dtype=np.float32) / S, indexing="ij")
    twill = 0.025 * np.sin((xx + yy) * math.pi * 3.5) * np.cos((xx - yy) * math.pi * 3.5)
    felt_grain = 0.92 + 0.11 * (coarse - 0.5) + 0.05 * (fine - 0.5) + twill

    canvas = np.zeros((H_s, W_s, 3), dtype=np.float32)
    # Deep crimson gutter fill so mipmaps never bleed grey/black onto crimson edges
    canvas[..., 0], canvas[..., 1], canvas[..., 2] = 150.0, 16.0, 22.0

    # --- Island 1: Outer/Top Plush Crimson Wool Felt (monotonic s_prof: 0..0.32 top, 0.32..0.63 crown, 0.63..0.98 brim) ---
    m1 = (xx >= 2) & (xx <= 126) & (yy >= 2) & (yy <= 126)
    nx = (xx - 64.0) / 53.0
    ny = (64.0 - yy) / 53.0
    rn = np.hypot(nx, ny)
    ang = np.arctan2(ny, nx)
    # Subtle AO right at the crown-brim crease (s_prof = 0.63)
    ao_band = 1.0 - 0.24 * np.exp(-((rn - 0.635) / 0.042) ** 2)
    # Teardrop top crease soft basin (rn < 0.22) + crown rim ridge highlight (rn ~ 0.29)
    crease_sh = 1.0 - 0.16 * np.exp(-((rn - 0.13) / 0.11) ** 2) + 0.12 * np.exp(-((rn - 0.29) / 0.055) ** 2)
    # Front thumb-pinches subtle velvet contour strictly on upper crown (rn in [0.35, 0.48], ang ~ +-37 deg)
    pinch_sh = 1.0 - 0.13 * np.exp(-((rn - 0.41) / 0.055) ** 2) * (
        np.exp(-((np.abs(ang) - 0.64) / 0.26) ** 2))
    # Curled outer brim lip highlight
    lip_hi = 1.0 + 0.12 * np.exp(-((rn - 0.95) / 0.05) ** 2)
    sh1 = felt_grain * ao_band * crease_sh * pinch_sh * lip_hi
    c1 = np.stack([204.0 * sh1, 22.0 * sh1, 31.0 * sh1], axis=-1)
    canvas[m1] = np.clip(c1[m1], 0, 255)

    # --- Island 2: Under-Brim Shaded Felt + Espresso Leather Sweatband + Satin Crown Lining ---
    m2 = (xx >= 130) & (xx <= 254) & (yy >= 2) & (yy <= 126)
    nx2 = (xx - 192.0) / 53.0
    ny2 = (64.0 - yy) / 53.0
    se_r2 = (np.abs(nx2) ** 2.35 + np.abs(ny2) ** 2.35) ** (1.0 / 2.35)
    ang2 = np.arctan2(ny2, nx2)
    # Default under-brim shaded crimson felt (se_r2 > 0.615)
    ub_sh = felt_grain * (0.76 + 0.24 * np.clip((se_r2 - 0.615) / 0.37, 0.0, 1.0))
    c2 = np.stack([142.0 * ub_sh, 15.0 * ub_sh, 22.0 * ub_sh], axis=-1)
    # Smooth espresso calfskin leather sweatband ring (se_r2 in [0.525, 0.615], matching superellipse rings!)
    sweat = (se_r2 >= 0.525) & (se_r2 <= 0.616) & m2
    lth = 0.92 + 0.16 * coarse
    c2[sweat] = np.stack([52.0 * lth[sweat], 30.0 * lth[sweat], 21.0 * lth[sweat]], axis=-1)
    # Continuous burnished brass/tan leather piping right at the brim-sweatband lip
    piping = (np.abs(se_r2 - 0.614) < 0.007) & m2
    c2[piping] = [138.0, 102.0, 62.0]
    # Deep burgundy-crimson satin lining inside the crown (se_r2 < 0.525) + gold hatter's crest diamond
    lin = (se_r2 < 0.525) & m2
    sat = 0.82 + 0.18 * np.cos(ang2 * 2.0 - 0.6) * (se_r2 / 0.525)
    c2[lin] = np.stack([96.0 * sat[lin], 12.0 * sat[lin], 20.0 * sat[lin]], axis=-1)
    crest = (np.abs(np.abs(nx2) * 1.25 + np.abs(ny2) - 0.13) < 0.016) & m2
    c2[crest] = [186.0, 148.0, 74.0]
    canvas[m2] = np.clip(c2[m2], 0, 255)

    # --- Island 3: Midnight-Black Grosgrain Silk Ribbon (u in [256, 338], v_local in [2, 42]) ---
    m3 = (xx >= 256) & (xx <= 338) & (yy >= 2) & (yy <= 42)
    u_rib = (xx - 258.0) / 78.0
    v_rib = (yy - 4.0) / 36.0
    ribs = 0.90 + 0.12 * np.sin(yy * math.pi * 3.2)
    sheen = 26.0 + 26.0 * (np.sin(u_rib * math.pi * 4.0 + 0.4) ** 4)
    edge_fold = 1.0 - 0.25 * (np.exp(-((v_rib - 0.0) / 0.08) ** 2) + np.exp(-((v_rib - 1.0) / 0.08) ** 2))
    rb_v = sheen * ribs * edge_fold
    c3 = np.stack([rb_v * 1.02, rb_v * 0.96, rb_v * 1.12], axis=-1)
    canvas[m3] = np.clip(c3[m3], 0, 255)

    # --- Island 4: Polished Brass/Gold Hatband Buckle (u in [256, 296], v_local in [44, 70]) ---
    m4 = (xx >= 256) & (xx <= 296) & (yy >= 44) & (yy <= 70)
    bx_n = (xx - 276.0) / 17.0
    by_n = (yy - 57.0) / 10.0
    bevel = 1.0 + 0.22 * np.cos((bx_n + by_n) * 1.6) - 0.16 * (np.maximum(np.abs(bx_n), np.abs(by_n)) - 0.72) ** 2
    c4 = np.stack([226.0 * bevel, 182.0 * bevel, 58.0 * bevel], axis=-1)
    canvas[m4] = np.clip(c4[m4], 0, 255)

    # --- Island 6: Ivory -> Gold -> Scarlet Plume Feather (u in [342, 382], v_local in [2, 124]) ---
    m6 = (xx >= 342) & (xx <= 382) & (yy >= 2) & (yy <= 124)
    fu = (xx - 361.0) / 16.0                                        # -1 .. +1 across vane
    fv = np.clip((121.0 - yy) / 116.0, 0.0, 1.0)                    # 0 = quill base, 1 = scarlet tip
    barbs = 0.88 + 0.14 * np.sin((np.abs(fu) * 10.0 - fv * 22.0) * math.pi)
    # 3-stop gradient: warm ivory (0..0.38) -> rich gold (0.38..0.68) -> bright crimson-scarlet tip (0.68..1.0)
    w_gold = smoothstep(0.24, 0.54, fv) * (1.0 - smoothstep(0.62, 0.84, fv))
    w_red = smoothstep(0.58, 0.84, fv)
    w_iv = np.maximum(0.0, 1.0 - w_gold - w_red)
    fr = (234.0 * w_iv + 236.0 * w_gold + 218.0 * w_red) * barbs
    fg = (224.0 * w_iv + 178.0 * w_gold + 26.0 * w_red) * barbs
    fb = (194.0 * w_iv + 46.0 * w_gold + 32.0 * w_red) * barbs
    c6 = np.stack([fr, fg, fb], axis=-1)
    quill = (np.abs(fu) < 0.09) & m6
    c6[quill] = np.stack([242.0 - 60.0 * fv[quill], 232.0 - 140.0 * fv[quill], 204.0 - 140.0 * fv[quill]], axis=-1)
    canvas[m6] = np.clip(c6[m6], 0, 255)

    # --- PIL Vector Overlay: Island 5 ("M'LADY" Vintage Press-Card) + Rear Ribbon "M'LADY" Woven Tab ---
    im = Image.fromarray(canvas.clip(0, 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im)

    # Island 5: u in [258, 336], v_local in [74, 122]  (v = 330..378 in full skin)
    cx0, cy0, cx1, cy1 = int(258 * S), int(73 * S), int(336 * S), int(122 * S)
    dr.rectangle([cx0 - 2 * S, cy0 - 2 * S, cx1 + 2 * S, cy1 + 2 * S], fill=(234, 224, 198))
    # Subtle vintage cardstock border + crimson press header bar
    pad = max(2, int(2.6 * S))
    dr.rectangle([cx0 + pad, cy0 + pad, cx1 - pad, cy1 - pad], outline=(42, 26, 28), width=max(1, int(1.3 * S)))
    hdr_h = int(10.5 * S)
    dr.rectangle([cx0 + pad + S, cy0 + pad + S, cx1 - pad - S, cy0 + pad + hdr_h], fill=(188, 22, 30))

    f_sub = _load_font(max(8, int(6.8 * S)), serif=False)
    f_main = _load_font(max(12, int(15.5 * S)), serif=True)
    # Center "PRESS · VIP" in crimson top bar
    sub_txt = "VIP · PRESS"
    sb = dr.textbbox((0, 0), sub_txt, font=f_sub)
    dr.text(((cx0 + cx1 - (sb[2] - sb[0])) / 2, cy0 + pad + S + (hdr_h - (sb[3] - sb[1])) / 2 - 0.5 * S),
            sub_txt, font=f_sub, fill=(242, 234, 212))
    # Center bold "M'LADY" across the cream body of the press-card
    ml_txt = "M'LADY"
    mb = dr.textbbox((0, 0), ml_txt, font=f_main)
    body_y0 = cy0 + pad + hdr_h + S
    body_y1 = cy1 - pad - int(3.0 * S)
    tx = (cx0 + cx1 - (mb[2] - mb[0])) / 2 - mb[0]
    ty = (body_y0 + body_y1 - (mb[3] - mb[1])) / 2 - mb[1]
    dr.text((tx, ty), ml_txt, font=f_main, fill=(24, 14, 16))

    im = im.resize((SW * mul, (SKIN_H - HEAD_SH) * mul), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)


def pose_hat(Vh, tip_pitch=0.0, extra_roll=0.0, extra_yaw=0.0, lift=(0.0, 0.0, 0.0),
             head_roll=0.0, head_pitch=0.0, head_yaw=0.0, head_shift=(0.0, 0.0, 0.0)):
    """Places the local fedora on the head in its jaunty resting tilt + local hat animation (tip/lift/flutter),
    then applies the head's own frame rotation & translation so hat + head move together cleanly."""
    H = Vh.copy()
    # Forward "M'Lady" salute (tip_pitch >= 0) hinges on the front brow; wind-blown backward pop hinges about crown center
    pivot = np.array([HAT_RX * 0.72, 0.0, 0.0]) if tip_pitch >= 0.0 else np.zeros(3)
    H = rot(H - pivot, 1, tip_pitch) + pivot
    H = rot(H, 0, HAT_BASE_ROLL + extra_roll)
    H = rot(H, 1, HAT_BASE_PITCH)
    H = rot(H, 2, HAT_BASE_YAW + extra_yaw)
    H = H + HAT_ORIGIN + np.asarray(lift, dtype=float)
    if head_pitch:
        H = rot(H, 1, head_pitch)
    if head_roll:
        H = rot(H, 0, head_roll)
    if head_yaw:
        H = rot(H, 2, head_yaw)
    return H + np.asarray(head_shift, dtype=float)


def check_hat_clearance(head_shut, hat_rest):
    """Verify no upper-skull/hair vertices poke out through the fedora crown at rest OR during a +11.5 deg salute."""
    upper = head_shut[head_shut[:, 2] > 11.6]
    brow_pivot = np.array([HAT_RX * 0.72, 0.0, 0.0])
    for label, tip, lft_z in (("rest", 0.0, 0.0), ("tip+11.5", 11.5, 0.45)):
        Q = upper - HAT_ORIGIN - np.array([0.0, 0.0, lft_z])
        Q = rot(Q, 2, -HAT_BASE_YAW)
        Q = rot(Q, 1, -HAT_BASE_PITCH)
        Q = rot(Q, 0, -HAT_BASE_ROLL)
        Q = rot(Q - brow_pivot, 1, -tip) + brow_pivot
        inside_h = Q[Q[:, 2] >= 0.0]
        th = np.arctan2(inside_h[:, 1] / HAT_RY, inside_h[:, 0] / HAT_RX)
        u = np.clip((inside_h[:, 2] - 0.12) / 11.4, 0.0, 1.0)
        rm_wall, _ = _crown_r_z(th, u)
        c, s = np.cos(th), np.sin(th)
        wx = HAT_RX * rm_wall * _hat_se(c)
        wy = HAT_RY * rm_wall * _hat_se(s)
        margin = float((np.hypot(wx, wy) - np.hypot(inside_h[:, 0], inside_h[:, 1])).min())
        print("fedora clearance [%s]: min radial margin %.2fu" % (label, margin))
        assert margin > 0.20, "Scalp pokes through fedora crown in %s (margin=%.2f)" % (label, margin)
    top_margin = float(hat_rest[:, 2].max() - head_shut[:, 2].max())
    print("fedora crown height above hair: +%.2fu" % top_margin)


def combine_mdl(head_V, hat_V, hat_tris, hat_st):
    """Runs mdl_data on the head ring mesh and appends the fedora mesh + UVs."""
    from build_head_grenade import mdl_data
    Vh0, tris_h, rad_h, st_f, st_b = mdl_data(head_V)
    off = len(Vh0)
    V_all = np.vstack([Vh0, hat_V])
    tris_all = np.vstack([tris_h, hat_tris + off])
    rad_hat = np.tile(np.array([[1.0, 0.0, 0.0]]), (len(hat_tris), 1))
    rad_all = np.vstack([rad_h, rad_hat])
    st_f_all = np.vstack([st_f, hat_st])
    st_b_all = np.vstack([st_b, hat_st])
    return V_all, tris_all, rad_all, st_f_all, st_b_all


# ------------------------------------------------------------------ Head Unwrap & Rigging

def fits(m):
    """per view and ring: the column map u_image = a * u_model + b that lays the view's silhouette on the model's.
    u_model is the model seen from that side (orthographic, the head's +y to the right when it faces you)."""
    P, z = m["P"], m["z"]
    x, lat = P[..., 0], P[..., 1] - m["c0"]
    for v in m["views"].values():
        ps = np.radians(v.yaw)
        um = -np.sin(ps) * x + np.cos(ps) * lat
        Lm, Rm = um.min(1), um.max(1)
        Li, Ri = edges(v.mask, v.row(z))
        a = (Ri - Li) / np.maximum(Rm - Lm, 1)
        ok = (z >= HOLD[0]) & (z <= HOLD[1]) & ~np.isnan(a)
        a = np.clip(np.where(ok, a, np.nan), 0.75, 1.3)
        b = Li - a * Lm
        idx = np.arange(len(z))
        a = np.interp(idx, idx[ok], a[ok])                          # outside the fitted rows hold the nearest fit
        b = np.interp(idx, idx[ok], b[ok])
        v.a, v.b = ndimage.gaussian_filter1d(a, 1.5), ndimage.gaussian_filter1d(b, 1.5)
        v.bled = bleed(v.img, v.mask)


def bleed(rgb, m, erode=3):
    """everything outside the (eroded) silhouette becomes the nearest colour inside, so a texel that lands just
    off the edge of a view picks up hair or skin, not the backdrop"""
    core = ndimage.binary_erosion(m, iterations=erode)
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    return rgb[idx[0], idx[1]]


def grid_normals(P):
    """outward vertex normals of the ring grid in (x forward, y left, z up)"""
    Q = np.stack([P[..., 0], P[..., 1], -P[..., 2]], -1)
    dk = np.roll(Q, -1, 1) - np.roll(Q, 1, 1)
    dj = np.concatenate([Q[1:2] - Q[0:1], Q[2:] - Q[:-2], Q[-1:] - Q[-2:-1]], 0)
    n = np.cross(dk, dj)
    out = Q - Q.mean(1, keepdims=True)
    n *= np.sign(np.sum(n * out, -1, keepdims=True) + 1e-9)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)


def skin(m, imgs, mul, gain, hat_strip=None):
    """cylindrical unwrap in top 256*mul rows + crimson 'M'LADY' fedora atlas in bottom 128*mul rows"""
    W_, H_head = SW * mul, HEAD_SH * mul
    kk = (np.arange(W_) + 0.5) / W_ * NH
    jj = np.maximum((1 - (np.arange(H_head) + 0.5) / H_head) * (MH - 1), 0.0)
    KK, JJ = np.meshgrid(kk, jj)
    wrap = lambda g: np.concatenate([g, g[:, :1]], 1)
    at = lambda g: ndimage.map_coordinates(wrap(g), [JJ, KK], order=1, mode="nearest")
    P, N = m["P"], grid_normals(m["P"])
    x, lat, z = at(P[..., 0]), at(P[..., 1]) - m["c0"], at(P[..., 2])
    n = np.stack([at(N[..., c]) for c in range(3)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    acc = np.zeros((H_head, W_, 3), np.float32)
    wsum = np.zeros((H_head, W_, 1), np.float32)
    for key, v in m["views"].items():
        ps = np.radians(v.yaw)
        facing = n[..., 0] * np.cos(ps) + n[..., 1] * np.sin(ps)
        w = np.exp(10 * facing)[..., None]
        um = -np.sin(ps) * x + np.cos(ps) * lat
        a, b = np.interp(JJ, np.arange(MH), v.a), np.interp(JJ, np.arange(MH), v.b)
        acc += w * v.sample(imgs[key], a * um + b, v.row(z))
        wsum += w
    head_rgb = acc / wsum
    strip = hat_strip if hat_strip is not None else fedora_strip(mul)
    full = np.concatenate([head_rgb, strip], axis=0)
    return (full * gain).clip(0, 255).astype(np.uint8)


def jaw(V, uv, fw, J):
    """drop the jaw by J (0..1): everything under the lips moves down (and a little forward), fading out to the sides
    and the back, so the painted mouth between the lips stretches open.  uv is each vertex in front view pixels."""
    V = V.copy()
    wv = smoothstep(MOUTH_TOP, MOUTH_BOT, uv[:, 1])
    wx = 1 - smoothstep(1.1 * MOUTH_RX, 2.7 * MOUTH_RX, np.abs(uv[:, 0] - MOUTH[0]))
    wf = smoothstep(-0.25, 0.45, fw)
    d = J * JAW * wv * wx * wf
    V[:, 2] += d
    V[:, 0] += 0.18 * d
    return V


def place(Vc, lo, hi):
    """model pixels (z down) -> quake units, z up, centred on the closed head's box"""
    V = Vc.copy()
    V[:, 2] = -V[:, 2]
    return (V - (lo + hi) / 2) * (HEIGHT / (hi[2] - lo[2]))


def rot(V, axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    V = V.copy()
    V[:, i], V[:, j] = c * V[:, i] - s * V[:, j], s * V[:, i] + c * V[:, j]
    return V


def mesh(m):
    """vertex list for mdl_data (rings, then the chin and crown centres), each vertex in front view pixels, and how
    much it faces forward"""
    P = m["P"]
    F = m["views"][FRONT]
    V = P.reshape(-1, 3)
    V = np.vstack([V, P[0].mean(0) + [0, 0, 2], P[-1].mean(0) - [0, 0, 2]])
    j = np.concatenate([np.repeat(np.arange(MH), NH), [0, MH - 1]])
    um = V[:, 1] - m["c0"]                                          # the front view: u_model is the lateral offset
    uv = np.stack([np.interp(j, np.arange(MH), F.a) * um + np.interp(j, np.arange(MH), F.b), F.row(V[:, 2])], -1)
    th = -np.pi / 2 + 2 * np.pi * np.arange(NH) / NH
    fw = np.concatenate([np.tile(np.sin(th), MH), [1.0, -1.0]])
    # the head's mesh axis is lateral = P1: centre it on the face's middle so it spins about itself
    V[:, 1] -= m["c0"]
    return V, uv, fw


def frames(m, Vh):
    """Builds the 20 animation frames (name, head_V, hat_V) for floathead.mdl."""
    V, uv, fw = mesh(m)
    base = V.copy()
    base[:, 2] = -base[:, 2]
    lo, hi = base.min(0), base.max(0)
    out = []
    shut = place(V, lo, hi)
    check_hat_clearance(shut, pose_hat(Vh))

    # 1. idle1-8: buoyant balloon bob + smug "M'Lady" forward fedora-tip salute & springy follow-through
    for i in range(8):
        a = 2 * np.pi * i / 8
        h_roll = 5.0 * np.sin(a)
        h_pitch = 2.4 * np.maximum(0.0, np.sin(a - 0.35)) - 1.1 * np.sin(a)
        h_shift = np.array([0.0, 0.0, 1.4 * np.sin(a + 0.6)])
        tip_pulse = max(0.0, math.sin(a - 0.35)) ** 1.45
        tip_deg = 7.4 * tip_pulse - 1.4 * math.sin(a - 1.1)
        hat_r = 2.0 * math.cos(a)
        hat_lift = (0.0, 0.0, 0.35 * tip_pulse)
        H_head = rot(rot(shut, 1, h_pitch), 0, h_roll) + h_shift
        H_hat = pose_hat(Vh, tip_pitch=tip_deg, extra_roll=hat_r, lift=hat_lift,
                         head_roll=h_roll, head_pitch=h_pitch, head_shift=h_shift)
        out.append(("idle%d" % (i + 1), H_head, H_hat))

    # 2. open1-4: jaw drops wide while sudden acceleration blasts the fedora cleanly UP off his hair into mid-air!
    open_specs = (
        (0.25,  -4.5,  1.5, 0.0, (-0.8,  0.0,  3.6)),
        (0.60, -10.5,  3.5, 2.5, (-2.0, -0.2,  8.4)),
        (0.95, -15.5,  5.5, 5.0, (-3.2, -0.4, 12.6)),
        (1.18, -18.5,  6.5, 7.5, (-4.0, -0.5, 15.2)),
    )
    for i, (J, tp, er, ey, lft) in enumerate(open_specs):
        H_head = place(jaw(V, uv, fw, J), lo, hi)
        H_hat = pose_hat(Vh, tip_pitch=tp, extra_roll=er, extra_yaw=ey, lift=lft)
        out.append(("open%d" % (i + 1), H_head, H_hat))

    # 3. rush1-4: furious chomping jaw + puffed cheeks while fedora hovers high in the slipstream fluttering wildly!
    rush_specs = (
        # (jaw_J, cheek_mul, head_roll, head_yaw, head_jolt, hat_pitch, hat_roll, hat_yaw, hat_lift)
        (1.24, 0.095,  5.2, -3.2, ( 0.4,  0.5,  0.4), -17.5,  -1.5,   9.0, (-3.6, -0.6, 15.6)),
        (0.50, 0.035, -4.8,  3.5, (-0.3, -0.5, -0.4), -21.0,  14.5, -10.0, (-4.5,  0.7, 17.0)),
        (1.14, 0.085, -5.4,  2.8, ( 0.3, -0.4,  0.5), -16.5,  15.5,  -8.5, (-3.4,  0.6, 15.4)),
        (0.42, 0.030,  4.6, -3.6, (-0.4,  0.5, -0.5), -20.0,  -2.0,   9.5, (-4.3, -0.7, 16.7)),
    )
    for i, (J, chk, hr, hy, jolt, hp, hrl, hyw, hlft) in enumerate(rush_specs):
        W_h = place(jaw(V, uv, fw, J), lo, hi)
        low = smoothstep(0.55, 0.10, (W_h[:, 2] - W_h[:, 2].min()) / (W_h[:, 2].max() - W_h[:, 2].min()))
        W_h[:, 1] *= 1.0 + chk * low
        W_h = rot(rot(W_h, 0, hr), 2, hy) + np.asarray(jolt)
        H_hat = pose_hat(Vh, tip_pitch=hp, extra_roll=hrl, extra_yaw=hyw, lift=hlft,
                         head_roll=hr * 0.35, head_yaw=hy * 0.35, head_shift=jolt)
        assert H_hat[:, 2].min() > W_h[:, 2].max(), "Rush %d hat clips hair (%.2f <= %.2f)" % (
            i + 1, H_hat[:, 2].min(), W_h[:, 2].max())
        out.append(("rush%d" % (i + 1), W_h, H_hat))

    # 4. pain1-4: knocked back "ow!", fedora popped crooked sideways and settling back onto his head
    pain_specs = (
        (0.62, -16.0, -12.0,  22.0, -12.0, (-1.8, 1.2, 11.2)),
        (0.45, -11.5,  -8.0,  15.0,  -8.0, (-1.1, 0.8,  7.4)),
        (0.26,  -6.5,  -4.0,   8.0,  -4.0, (-0.5, 0.4,  3.6)),
        (0.10,  -2.0,  -1.0,   2.5,  -1.0, (-0.1, 0.1,  0.9)),
    )
    for i, (J, hpitch, tp, er, ey, lft) in enumerate(pain_specs):
        ow = place(jaw(V, uv, fw, J), lo, hi)
        H_head = rot(ow, 1, hpitch)
        H_hat = pose_hat(Vh, tip_pitch=tp, extra_roll=er, extra_yaw=ey, lift=lft, head_pitch=hpitch)
        out.append(("pain%d" % (i + 1), H_head, H_hat))

    return out


def viewmodel(m, Vh, hat_tris, hat_st, shut, gain):
    """progs/v_robdob.mdl: the Rob Dob in your hand, a small head hovering at the lower right with its face to you,
    jauntily tipping its crimson 'M'LADY' fedora at you.
    Frames 0-7 bob & tip, frame 8 is 'gone' (it is out flying): the hand is empty until the next one has recharged."""
    V, uv, fw = mesh(m)
    base = V.copy()
    base[:, 2] = -base[:, 2]
    lo, hi = base.min(0), base.max(0)
    sc = VM_HEIGHT / HEIGHT
    head0 = place(V, lo, hi)
    hat0 = pose_hat(Vh)

    # Rest combined pose (used in frame 8 'gone' so robdob_vm.py can un-pose head + hat cleanly)
    V0, tris, rad, st_f, st_b = combine_mdl(head0 * sc, hat0 * sc, hat_tris, hat_st)
    rest_posed = RV.orient(V0, VM_YAW, VM_PITCH, VM_ROLL)

    out_frames = []
    for i in range(8):
        a = 2 * np.pi * i / 8
        # Smug gentlemanly nod + forward "M'Lady" brim-tip right toward the player's eyes
        tip_pulse = max(0.0, math.sin(a - 0.3)) ** 1.6
        nod = 3.2 * tip_pulse
        tip_deg = 11.5 * tip_pulse - 1.5 * math.sin(a - 1.0)
        h_loc = rot(head0, 1, nod) * sc
        hat_loc = pose_hat(Vh, tip_pitch=tip_deg, extra_roll=-2.0 * math.cos(a),
                           lift=(0.0, 0.0, 0.45 * tip_pulse), head_pitch=nod) * sc
        comb = combine_mdl(h_loc, hat_loc, hat_tris, hat_st)[0]
        oriented = RV.orient(comb, VM_YAW, VM_PITCH, VM_ROLL)
        F = rot(oriented, 2, 4.0 * np.sin(a + 1.0)) + np.array(VM_POS) + [0, 0, 0.35 * np.sin(a)]
        out_frames.append(("bob%d" % (i + 1), F))

    out_frames.append(("gone", rest_posed + np.array(VM_POS) + [0, 0, -45]))

    path = os.path.join(OUT, "v_robdob.mdl")
    B.SKIN_H = SKIN_H
    strip1 = fedora_strip(1)
    strip3 = fedora_strip(TGA_MUL)
    B.write_mdl(path, dict(V=out_frames[0][1], tris=tris, rad=rad), out_frames,
                B.to_palette(skin(m, shut, 1, gain, strip1)), st_f, st_b, SW)
    Image.fromarray(skin(m, shut, TGA_MUL, gain, strip3)).save(path + "_0.tga", compression="tga_rle")
    print("v_robdob.mdl: %d verts, %d tris, %d frames, %d bytes" % (
        len(out_frames[0][1]), len(tris), len(out_frames), os.path.getsize(path)))
    return path


def add_skin(path, skin8):
    """write_mdl writes one skin: append a second one (header numskins is at byte 48, skins follow the header)"""
    d = bytearray(open(path, "rb").read())
    n = struct.unpack_from("<i", d, 48)[0]
    struct.pack_into("<i", d, 48, n + 1)
    at = 84 + n * (4 + SW * SKIN_H)
    d[at:at] = struct.pack("<i", 0) + skin8.tobytes()
    open(path, "wb").write(bytes(d))


def main():
    import build_head_grenade as G
    G.NH, G.MH, G.SW, G.SKIN_H = NH, MH, SW, HEAD_SH                # mdl_data maps the head onto top 256 rows
    m = build()
    fits(m)
    Vh, hat_tris, hat_st = hat_mesh()
    shut = {k: v.bled for k, v in m["views"].items()}
    opened = dict(shut)
    opened[FRONT] = paint_mouth(shut[FRONT])
    fr = frames(m, Vh)
    V0, tris, rad, st_f, st_b = combine_mdl(fr[0][1], fr[0][2], hat_tris, hat_st)
    out_frames = [(name, combine_mdl(hv, hatv, hat_tris, hat_st)[0]) for name, hv, hatv in fr]
    gain = B.SKIN_GAIN * BRIGHT
    B.SKIN_H = SKIN_H
    strip1 = fedora_strip(1)
    strip3 = fedora_strip(TGA_MUL)
    path = os.path.join(OUT, "floathead.mdl")
    nv, nt = B.write_mdl(path, dict(V=V0, tris=tris, rad=rad), out_frames,
                         B.to_palette(skin(m, shut, 1, gain, strip1)), st_f, st_b, SW)
    add_skin(path, B.to_palette(skin(m, opened, 1, gain, strip1)))
    for i, imgs in enumerate((shut, opened)):
        Image.fromarray(skin(m, imgs, TGA_MUL, gain, strip3)).save(path + "_%d.tga" % i, compression="tga_rle")
    viewmodel(m, Vh, hat_tris, hat_st, shut, B.SKIN_GAIN * 1.5)
    lo, hi = np.min([f[1].min(0) for f in out_frames], 0), np.max([f[1].max(0) for f in out_frames], 0)
    print("floathead.mdl: %d verts, %d tris, %d frames, 2 skins %dx%d (tga x%d), box %s .. %s, %d bytes" % (
        nv, nt, len(out_frames), SW, SKIN_H, TGA_MUL, np.round(lo, 1), np.round(hi, 1), os.path.getsize(path)))
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        md = B.read_mdl(path)
        texs = [skin(m, imgs, TGA_MUL, BRIGHT, strip3) for imgs in (shut, opened)]
        zoom = 300 / (HEIGHT * 1.85)
        rows = []
        for fi in (0, 2, 11, 12, 13):
            tex = texs[0] if fi < 8 else texs[1]
            rows.append(np.concatenate([B.render(md, fi, yaw, size=360, zoom=zoom * 1.2, tex=tex)
                                        for yaw in (0, 45, 90, 135, 180, 270)], 1))
        Image.fromarray(np.concatenate(rows, 0)).save(os.path.join(PREVIEW, "floathead_views.png"))
        Image.fromarray(texs[0]).save(os.path.join(PREVIEW, "floathead_skin.png"))
        Image.fromarray(texs[1]).save(os.path.join(PREVIEW, "floathead_skin_open.png"))


if __name__ == "__main__":
    main()
