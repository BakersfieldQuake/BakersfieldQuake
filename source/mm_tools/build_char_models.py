"""Builds the suit guy, the robe guy and the wife as their own Quake player models from their front/back reference photos.

python -E -P build_char_models.py [--preview DIR] [--only suitguy|robeguy|wifeguy]

  out/chars/ref/{suit,robe,wife}_{front,back}.jpg -> BakersfieldQuake/progs/{suitguy,robeguy,wifeguy}.mdl  (+ .mdl_0.tga, full colour
                                                for Darkplaces)

  1. silhouette of each photo (flat background key, holes filled)
  2. body = tubes (head, torso, lower body / robe skirt, arms, hands, legs, feet) along hand-placed joint lines; each
     tube's width at every station is measured off the front silhouette, its depth is a fixed fraction of that width
  3. skin = front photo | back photo side by side; front-facing triangles take the front photo (straight projection),
     back-facing ones the back photo (same tube station, same fraction across the back silhouette)
  4. skeleton + procedural poses for all 143 player.mdl frames in player.qc order (axrun / rockrun = the run cycle)
  5. IDPO v6 writer: 8-bit skin in the Quake palette (no colormap rows 16-31 / 96-111, no fullbrights)

Needs numpy, scipy, Pillow (run with -E -P, not -I: they live in the user site-packages).
"""
import math
import os
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "out", "chars", "ref")
PROGS = r"G:\Quake\Combat\BakersfieldQuake\progs"
PAK = r"G:\Quake\Combat\id1\pak0.pak"
ANORMS = r"D:\vibe\quake1opensource\idsrc\WinQuake\anorms.h"

TOP_Z, SOLE_Z = 29.0, -24.0      # stock player.mdl stands on z=-24 and is ~51 tall
SKIN_H = 480                     # 8-bit skin height (WinQuake MAX_LBM_HEIGHT)
TGA_MUL = 3                      # the Darkplaces skin is this many times bigger
TORSO_DEPTH = 0.62               # chest depth / width
SKIN_GAIN = 0.55                 # engines light models up to 2x (overbright): photos have to be darker than life

PREVIEW = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None

# ------------------------------------------------------------------ characters
# Keypoints are photo pixels.  Front photo: image right = his left (L).  Back photo: image right = his right (R).
# toe_* in the back photo is the point under the ankle on the floor.
ROBE = dict(
    name="robeguy", key="white", skirt=0.65, lower_depth=0.78, head_maxr=100, hidden_thighs=True,
    front=dict(img="robe_front.jpg", top=36, sole=1660, kp=dict(
        neck=(578, 322), waist=(578, 722), hem=(570, 1278), hip_c=(578, 845),
        sh_R=(370, 390), el_R=(330, 640), wr_R=(334, 893), tip_R=(330, 1030),
        sh_L=(787, 390), el_L=(826, 640), wr_L=(826, 878), tip_L=(815, 1028),
        hip_R=(505, 845), kn_R=(455, 1350), an_R=(432, 1592), toe_R=(398, 1652),
        hip_L=(652, 845), kn_L=(700, 1350), an_L=(712, 1592), toe_L=(748, 1652))),
    back=dict(img="robe_back.jpg", top=84, sole=1925, kp=dict(
        neck=(452, 322), waist=(452, 862), hem=(448, 1495), hip_c=(452, 1000),
        sh_L=(240, 458), el_L=(188, 760), wr_L=(195, 1052), tip_L=(205, 1212),
        sh_R=(668, 458), el_R=(716, 760), wr_R=(716, 1052), tip_R=(700, 1212),
        hip_L=(385, 1000), kn_L=(300, 1590), an_L=(288, 1840), toe_L=(285, 1922),
        hip_R=(522, 1000), kn_R=(600, 1590), an_R=(612, 1840), toe_R=(615, 1922))),
)
SUIT = dict(
    name="suitguy", key="gray", skirt=0.2, lower_depth=0.66, head_maxr=125, hidden_thighs=False,
    front=dict(img="suit_front.jpg", top=54, sole=1650, kp=dict(
        neck=(572, 315), waist=(572, 700), hem=(572, 912), hip_c=(572, 900),
        sh_R=(414, 400), el_R=(292, 590), wr_R=(215, 808), tip_R=(185, 942),
        sh_L=(731, 400), el_L=(856, 590), wr_L=(933, 808), tip_L=(968, 942),
        hip_R=(490, 900), kn_R=(458, 1210), an_R=(435, 1530), toe_R=(395, 1640),
        hip_L=(655, 900), kn_L=(690, 1210), an_L=(715, 1530), toe_L=(762, 1640))),
    back=dict(img="suit_back.jpg", top=55, sole=1625, kp=dict(
        neck=(572, 285), waist=(572, 700), hem=(572, 898), hip_c=(572, 898),
        sh_L=(414, 400), el_L=(296, 590), wr_L=(215, 815), tip_L=(190, 942),
        sh_R=(731, 400), el_R=(852, 590), wr_R=(933, 815), tip_R=(958, 942),
        hip_L=(490, 898), kn_L=(458, 1210), an_L=(440, 1530), toe_L=(432, 1612),
        hip_R=(655, 898), kn_R=(690, 1210), an_R=(712, 1530), toe_R=(718, 1612))),
)

WIFE = dict(
    name="wifeguy", key="light", skirt=0.0, lower_depth=0.8, torso_depth=0.75, head_maxr=100, hidden_thighs=False,
    front=dict(img="wife_front.jpg", top=82, sole=1062, kp=dict(
        neck=(400, 255), waist=(405, 500), hem=(405, 625), hip_c=(405, 610),
        sh_R=(315, 300), el_R=(293, 460), wr_R=(297, 615), tip_R=(300, 676),
        sh_L=(515, 300), el_L=(530, 460), wr_L=(530, 612), tip_L=(524, 676),
        hip_R=(358, 610), kn_R=(357, 805), an_R=(350, 975), toe_R=(340, 1052),
        hip_L=(455, 610), kn_L=(465, 805), an_L=(480, 975), toe_L=(488, 1052))),
    back=dict(img="wife_back.jpg", top=76, sole=1058, kp=dict(
        neck=(405, 258), waist=(405, 495), hem=(405, 625), hip_c=(405, 610),
        sh_L=(312, 300), el_L=(293, 460), wr_L=(295, 612), tip_L=(298, 668),
        sh_R=(515, 300), el_R=(532, 460), wr_R=(530, 612), tip_R=(527, 668),
        hip_L=(358, 610), kn_L=(356, 805), an_L=(350, 975), toe_L=(345, 1050),
        hip_R=(455, 610), kn_R=(462, 805), an_R=(476, 975), toe_R=(478, 1048))),
)

BONES = ["pelvis", "chest", "head",
         "uarm_L", "farm_L", "hand_L", "uarm_R", "farm_R", "hand_R",
         "thigh_L", "shin_L", "foot_L", "thigh_R", "shin_R", "foot_R"]
BI = {b: i for i, b in enumerate(BONES)}
PARENT = dict(pelvis=None, chest="pelvis", head="chest",
              uarm_L="chest", farm_L="uarm_L", hand_L="farm_L", uarm_R="chest", farm_R="uarm_R", hand_R="farm_R",
              thigh_L="pelvis", shin_L="thigh_L", foot_L="shin_L", thigh_R="pelvis", shin_R="thigh_R", foot_R="shin_R")
BONE_HEAD = dict(pelvis="hip_c", chest="waist", head="neck", uarm_L="sh_L", farm_L="el_L", hand_L="wr_L",
                 uarm_R="sh_R", farm_R="el_R", hand_R="wr_R", thigh_L="hip_L", shin_L="kn_L", foot_L="an_L",
                 thigh_R="hip_R", shin_R="kn_R", foot_R="an_R")


def tube_parts(ch):
    """name, A, B, bone, (bone_a, zone_a), (bone_b, zone_b), ring verts, stations, depth ratio, max radius px"""
    P = [("head", "neck", "top", "head", ("chest", 0.18), None, 10, 8, 1.18, ch["head_maxr"]),
         ("torso", "waist", "neck", "chest", ("pelvis", 0.3), ("head", 0.08), 12, 7, ch.get("torso_depth", TORSO_DEPTH), 230),
         ("lower", "waist", "hem", "pelvis", ("chest", 0.2), None, 12, 6, ch["lower_depth"], 240)]
    for s in "LR":
        P += [("uarm_" + s, "sh_" + s, "el_" + s, "uarm_" + s, ("chest", 0.5), ("farm_" + s, 0.2), 8, 4, 0.95, 62),
              ("farm_" + s, "el_" + s, "wr_" + s, "farm_" + s, ("uarm_" + s, 0.2), ("hand_" + s, 0.15), 8, 4, 0.9, 58),
              ("hand_" + s, "wr_" + s, "tip_" + s, "hand_" + s, ("farm_" + s, 0.15), None, 6, 4, 0.5, 58),
              ("thigh_" + s, "hip_" + s, "kn_" + s, "thigh_" + s, ("pelvis", 0.15), ("shin_" + s, 0.15), 8, 5, 1.0, 72),
              ("shin_" + s, "kn_" + s, "an_" + s, "shin_" + s, ("thigh_" + s, 0.15), ("foot_" + s, 0.1), 8, 5, 1.0, 62)]
    return P


# ------------------------------------------------------------------ Quake data
def read_pak_file(pak, name):
    d = open(pak, "rb").read()
    ident, ofs, ln = struct.unpack_from("<4sii", d, 0)
    assert ident == b"PACK"
    for i in range(ln // 64):
        n, o, s = struct.unpack_from("<56sii", d, ofs + 64 * i)
        if n.split(b"\0")[0].decode("ascii").lower() == name:
            return d[o:o + s]
    raise KeyError(name)


PALETTE = np.frombuffer(read_pak_file(PAK, "gfx/palette.lmp"), np.uint8).reshape(256, 3).astype(np.int32)
USABLE = np.array([i for i in range(224) if not (16 <= i < 32 or 96 <= i < 112)])
_txt = re.sub(r"//.*", "", open(ANORMS).read())
ANORM = np.array([tuple(map(float, m)) for m in
                  re.findall(r"\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}", _txt)])
assert ANORM.shape == (162, 3)


def to_palette(rgb):
    """H x W x 3 uint8 -> H x W palette indices, Floyd-Steinberg dithered over the usable colours (Quake has no
    light pinks: plain nearest-colour turns the robe white)"""
    pal_img = Image.new("P", (1, 1))
    flat = PALETTE[USABLE].astype(np.uint8).reshape(-1).tolist()
    pal_img.putpalette(flat + flat[:3] * (256 - len(USABLE)))
    q = Image.fromarray(rgb).quantize(palette=pal_img, dither=Image.Dither.FLOYDSTEINBERG)
    idx = np.asarray(q).astype(int)
    idx[idx >= len(USABLE)] = 0                            # the padding entries are copies of colour 0
    return USABLE[idx].astype(np.uint8)


# ------------------------------------------------------------------ photos
class Photo:
    def __init__(self, cfg, key):
        self.rgb = np.asarray(Image.open(os.path.join(REF, cfg["img"])).convert("RGB"))
        a = self.rgb.astype(np.int16)
        sat = a.max(-1) - a.min(-1)
        v = a.mean(-1)
        bg = {"white": (v > 238) & (sat < 14), "light": (v > 150) & (sat < 16)}.get(key, (sat < 12) & (v > 88) & (v < 140))
        fg = ndimage.binary_opening(~bg, iterations=2)
        lab, n = ndimage.label(fg)
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        body = lab == 1 + int(np.argmax(sizes))
        holes = ndimage.binary_fill_holes(body) & ~body
        if key == "white":                   # keep real gaps (arm against the robe); only fill specks
            hl, hn = ndimage.label(holes)
            hs = ndimage.sum(holes, hl, range(1, hn + 1))
            holes = np.isin(hl, 1 + np.nonzero(hs < 300)[0])
        self.sil = body | holes              # grey key: the shirt next to the tie keys out, fill it all
        self.H, self.W = self.sil.shape
        self.kp = {k: np.array(v, float) for k, v in cfg["kp"].items()}
        self.top, self.sole = cfg["top"], cfg["sole"]
        self.kp["top"] = np.array([self.kp["neck"][0], self.top], float)

    def walk(self, mask, P, d, maxr):
        """distance from P along d to the first pixel outside mask (None if still inside at maxr)"""
        r = np.arange(0, maxr + 1)
        q = np.rint(P[None] + r[:, None] * d[None]).astype(int)
        ok = (q[:, 0] >= 0) & (q[:, 0] < self.W) & (q[:, 1] >= 0) & (q[:, 1] < self.H)
        inside = np.zeros(len(r), bool)
        inside[ok] = mask[q[ok, 1], q[ok, 0]]
        if not inside[0]:
            return 0.0
        out = np.nonzero(~inside)[0]
        return float(out[0]) - 0.5 if len(out) else None

    def measure(self, mask, A, B, perp, maxr, n=48):
        """centre offset (along perp) and half width at n stations along A->B; gaps interpolated, smoothed"""
        ts = (np.arange(n) + 0.5) / n
        off = np.full(n, np.nan)
        hw = np.full(n, np.nan)
        for i, t in enumerate(ts):
            P = A + (B - A) * t
            lo, hi = self.walk(mask, P, -perp, maxr), self.walk(mask, P, perp, maxr)
            if lo is not None and hi is not None:
                off[i], hw[i] = (hi - lo) / 2, (hi + lo) / 2
            elif lo is not None or hi is not None:
                off[i], hw[i] = 0.0, lo if lo is not None else hi
        good = ~np.isnan(hw)
        if not good.any():
            return ts, np.zeros(n), np.full(n, maxr * 0.5)
        for arr in (off, hw):
            arr[~good] = np.interp(ts[~good], ts[good], arr[good])
        k = np.ones(5) / 5
        pad = lambda a: np.concatenate([a[:1].repeat(2), a, a[-1:].repeat(2)])
        return ts, np.convolve(pad(off), k, "valid"), np.convolve(pad(hw), k, "valid")


def perp_img(d, left):
    """unit perpendicular to image direction d, on the side of image direction `left`"""
    d = d / np.linalg.norm(d)
    p = np.array([-d[1], d[0]])
    return p if p @ left > 0 else -p


# ------------------------------------------------------------------ geometry
def build(ch):
    F, Bk = Photo(ch["front"], ch["key"]), Photo(ch["back"], ch["key"])
    s = (TOP_Z - SOLE_Z) / (F.sole - F.top)          # units per front pixel
    cx = F.kp["neck"][0]

    def to3d(p):
        return np.array([0.0, (p[0] - cx) * s, SOLE_Z + (F.sole - p[1]) * s])

    def to_front(v):
        return np.array([cx + v[1] / s, F.sole - (v[2] - SOLE_Z) / s])

    joints = {k: to3d(v) for k, v in F.kp.items()}
    bscale = (Bk.sole - Bk.top) / (F.sole - F.top)

    V, W, UVF, UVB, TRI, RAD = [], [], [], [], [], []   # TRI: (a, b, c, radial dir)
    meas = {}

    def measure_part(name, A, B, maxr, maskF, maskB):
        a2, b2 = F.kp[A], F.kp[B]
        dF = b2 - a2
        pF = perp_img(dF, np.array([1.0, 0.0]))
        ab, bb = Bk.kp[A], Bk.kp[B]
        pB = perp_img(bb - ab, np.array([-pF[0], pF[1]]))
        tsF, offF, hwF = F.measure(maskF, a2, b2, pF, maxr)
        tsB, offB, hwB = Bk.measure(maskB, ab, bb, pB, int(maxr * bscale))
        meas[name] = (a2, b2, pF, offF, hwF, ab, bb, pB, offB, hwB, tsF)

    def outline(img_side, name):
        a2, b2, pF, offF, hwF, ab, bb, pB, offB, hwB, ts = meas[name]
        if img_side == 0:
            A, Bp, p, off, hw = a2, b2, pF, offF, hwF
        else:
            A, Bp, p, off, hw = ab, bb, pB, offB, hwB
        c = A[None] + (Bp - A)[None] * ts[:, None] + off[:, None] * p[None]
        return np.concatenate([c + hw[:, None] * p, (c - hw[:, None] * p)[::-1]])

    parts = tube_parts(ch)
    limbs = [p for p in parts if p[0] not in ("head", "torso", "lower")]
    for p in limbs:
        measure_part(p[0], p[1], p[2], p[9], F.sil, Bk.sil)
    if ch["hidden_thighs"]:                    # under the robe: as wide as the top of the shin, a bit more at the hip
        for sd in "LR":
            mt, ms = list(meas["thigh_" + sd]), meas["shin_" + sd]
            ts = mt[10]
            mt[3], mt[8] = np.zeros_like(ts), np.zeros_like(ts)
            mt[4] = ms[4][0] * (1.25 - 0.25 * ts)
            mt[9] = ms[9][0] * (1.25 - 0.25 * ts)
            meas["thigh_" + sd] = tuple(mt)
    excl = []
    for side, ph in ((0, F), (1, Bk)):
        im = Image.new("L", (ph.W, ph.H), 0)
        dr = ImageDraw.Draw(im)
        for p in limbs:
            if p[0][:4] in ("uarm", "farm", "hand"):
                dr.polygon([tuple(q) for q in outline(side, p[0])], fill=255)
        excl.append(ph.sil & ~(np.asarray(im) > 0))
    for p in parts[:3]:
        measure_part(p[0], p[1], p[2], p[9], excl[0], excl[1])
    # torso and lower body share their waist ring exactly (no ledge, no cap there): ease both onto the average
    mt, ml = list(meas["torso"]), list(meas["lower"])
    ts = mt[10]
    ease = np.clip(1 - ts / 0.25, 0, 1)
    for i in (3, 4, 8, 9):
        target = (np.interp(0, ts, mt[i]) + np.interp(0, ts, ml[i])) / 2
        mt[i] = mt[i] + (target - np.interp(0, ts, mt[i])) * ease
        ml[i] = ml[i] + (target - np.interp(0, ts, ml[i])) * ease
    meas["torso"], meas["lower"] = tuple(mt), tuple(ml)

    def add_vert(v, w, uvf, uvb):
        V.append(v)
        W.append(w)
        UVF.append(uvf)
        UVB.append(uvb)
        return len(V) - 1

    for name, A, B, bone, ba, bb_, N, M, depth, maxr in parts:
        a2, b2, pF, offF, hwF, ab, bb, pB, offB, hwB, ts = meas[name]
        A3, B3 = joints[A], joints[B]
        d = B3 - A3
        d /= np.linalg.norm(d)
        ew = np.array([0.0, pF[0], -pF[1]])
        ew /= np.linalg.norm(ew)
        ed = np.cross(ew, d)
        if ed[0] + 0.5 * ed[2] < 0:
            ed = -ed
        tst = np.linspace(0.0, 1.0, M)          # rings sit right on the joints: neighbours meet, no seams
        rings = []
        for t in tst:
            oF, hF = np.interp(t, ts, offF), np.interp(t, ts, hwF)
            oB, hB = np.interp(t, ts, offB), np.interp(t, ts, hwB)
            if name == "torso":                    # slope the shoulders in towards the neck
                f = 1 - 0.35 * smooth((t - 0.78) / 0.22)
                hF, hB = hF * f, hB * f
            if name.startswith("uarm"):             # round the top of the arm into the shoulder
                f = 0.55 + 0.45 * smooth(t / 0.35)
                hF, hB = hF * f, hB * f
            C = A3 + (B3 - A3) * t + ew * oF * s
            dep = depth * (1.0 + (0.12 if name == "head" and t < 0.35 else 0.0))
            if name == "lower":                    # starts as deep as the torso so the waist rings match
                td = ch.get("torso_depth", TORSO_DEPTH)
                dep = td + (depth - td) * smooth(t / 0.3)
            ring = []
            for k in range(N):
                th = 2 * math.pi * k / N
                c, sn = math.cos(th), math.sin(th)
                v = C + ew * c * hF * s + ed * sn * hF * dep * s
                w = np.zeros(len(BONES))
                wa = 0.5 * max(0.0, 1 - t / ba[1]) if ba else 0.0
                wb = 0.5 * max(0.0, 1 - (1 - t) / bb_[1]) if bb_ else 0.0
                if ba:
                    w[BI[ba[0]]] += wa
                if bb_:
                    w[BI[bb_[0]]] += wb
                if name == "lower":                     # the skirt swings with the legs
                    sideL = c                           # ew points to his left
                    kL = ch["skirt"] * t * min(1, max(0, 0.5 + 0.8 * sideL))
                    kR = ch["skirt"] * t * min(1, max(0, 0.5 - 0.8 * sideL))
                    w[BI["thigh_L"]] += kL
                    w[BI["thigh_R"]] += kR
                    wb += kL + kR
                w[BI[bone]] += 1 - wa - wb
                uvb = ab + (bb - ab) * t + (oB + c * hB) * pB
                ring.append(add_vert(v, w, to_front(v), uvb))
            rings.append((ring, C))
        for j in range(M - 1):
            r0, c0 = rings[j]
            r1, c1 = rings[j + 1]
            for k in range(N):
                k1 = (k + 1) % N
                cen = (V[r0[k]] + V[r0[k1]] + V[r1[k]] + V[r1[k1]]) / 4
                rad = cen - (c0 + c1) / 2
                TRI.append((r0[k], r0[k1], r1[k1], rad))
                TRI.append((r0[k], r1[k1], r1[k], rad))
        for (ring, C), end, sign in ((rings[0], A3, -1), (rings[-1], B3, 1)):
            if sign < 0 and name in ("torso", "lower"):
                continue                           # the shared waist ring
            t = 0.0 if sign < 0 else 1.0
            capc = C + d * sign * (0.4 if name.startswith("hand") and sign > 0 else
                                    0.0)
            wc = np.array(W[ring[0]]) * 0 + np.mean([W[i] for i in ring], 0)
            uvbc = np.mean([UVB[i] for i in ring], 0)
            ci = add_vert(capc, wc, to_front(capc), uvbc)
            for k in range(N):
                TRI.append((ring[k], ring[(k + 1) % N], ci, d * sign))

    # feet: flat tubes from the heel to the toes along +x
    for sd in "LR":
        an, toe = joints["an_" + sd], joints["toe_" + sd]
        hw = F.walk(F.sil, np.array([F.kp["toe_" + sd][0], F.sole - 18.0]), np.array([1.0, 0]), 120)
        hw2 = F.walk(F.sil, np.array([F.kp["toe_" + sd][0], F.sole - 18.0]), np.array([-1.0, 0]), 120)
        half = min(2.1, max(1.2, ((hw or 60) + (hw2 or 60)) / 2 * s))
        heel_h = max(1.4, (an[2] - SOLE_Z) / 2 + 0.5)     # tall enough to reach the bottom of the shin
        A3 = np.array([-2.0, an[1], SOLE_Z + heel_h])
        B3 = np.array([5.8, toe[1], SOLE_Z + 0.9])
        bone = "foot_" + sd
        anb, toeb = Bk.kp["an_" + sd], Bk.kp["toe_" + sd]
        sb = (TOP_Z - SOLE_Z) / (Bk.sole - Bk.top)
        N, M = 6, 4
        rings = []
        for t in np.linspace(0.0, 1.0, M):
            C = A3 + (B3 - A3) * t
            hgt = heel_h - (heel_h - 0.7) * t
            ring = []
            for k in range(N):
                th = 2 * math.pi * k / N
                v = C + np.array([0, math.cos(th) * half * (0.85 + 0.15 * t), math.sin(th) * hgt])
                v[2] = max(v[2], SOLE_Z)
                w = np.zeros(len(BONES))
                w[BI[bone]] = 1
                uvb = np.array([anb[0] - (v[1] - an[1]) / sb, toeb[1] - (v[2] - SOLE_Z) / sb])
                ring.append(add_vert(v, w, to_front(v), uvb))
            rings.append((ring, C))
        for j in range(M - 1):
            r0, c0 = rings[j]
            r1, c1 = rings[j + 1]
            for k in range(N):
                k1 = (k + 1) % N
                cen = (V[r0[k]] + V[r0[k1]] + V[r1[k]] + V[r1[k1]]) / 4
                rad = cen - (c0 + c1) / 2
                TRI.append((r0[k], r0[k1], r1[k1], rad))
                TRI.append((r0[k], r1[k1], r1[k], rad))
        for (ring, C), sign in ((rings[0], -1), (rings[-1], 1)):
            dd = np.array([sign * 0.6, 0, 0])
            w = np.zeros(len(BONES))
            w[BI[bone]] = 1
            ci = add_vert(C + dd, w, to_front(C + dd), np.mean([UVB[i] for i in ring], 0))
            for k in range(N):
                TRI.append((ring[k], ring[(k + 1) % N], ci, dd))

    V = np.array(V)
    W = np.array(W)
    W /= W.sum(1, keepdims=True)
    tris = []
    for a, b, c, rad in TRI:
        n = np.cross(V[b] - V[a], V[c] - V[a])
        if n @ rad < 0:
            b, c = c, b
        tris.append((a, b, c))
    tris = np.array(tris)
    rest_j = {b: joints[BONE_HEAD[b]] for b in BONES}
    return dict(V=V, W=W, UVF=np.array(UVF), UVB=np.array(UVB), tris=tris, rad=np.array([t[3] for t in TRI]),
                joints=rest_j, F=F, Bk=Bk, meas=meas, outline=outline, s=s)


# ------------------------------------------------------------------ skin
def make_skin(m, ch):
    """front | back crops of the photos; returns 8-bit skin, the full colour skin, and per-tri st"""
    crops = []
    for ph in (m["F"], m["Bk"]):
        ys, xs = np.nonzero(ph.sil)
        x0, x1 = max(0, xs.min() - 8), min(ph.W, xs.max() + 9)
        y0, y1 = max(0, ys.min() - 8), min(ph.H, ys.max() + 9)
        crops.append((ph, x0, y0, x1, y1))
    k = [SKIN_H / (y1 - y0) for ph, x0, y0, x1, y1 in crops]
    ws = [int(math.ceil((x1 - x0) * kk)) for (ph, x0, y0, x1, y1), kk in zip(crops, k)]
    SW = (sum(ws) + 3) // 4 * 4

    def sheet(mul):
        out = np.zeros((SKIN_H * mul, SW * mul, 3), np.uint8)
        have = np.zeros((SKIN_H * mul, SW * mul), bool)
        ox = 0
        for (ph, x0, y0, x1, y1), w in zip(crops, ws):
            sz = (w * mul, SKIN_H * mul)
            img = Image.fromarray(ph.rgb[y0:y1, x0:x1]).resize(sz, Image.LANCZOS)
            msk = Image.fromarray((ph.sil[y0:y1, x0:x1] * 255).astype(np.uint8)).resize(sz, Image.BILINEAR)
            msk = ndimage.binary_erosion(np.asarray(msk) > 160, iterations=max(1, mul))
            out[:, ox * mul:ox * mul + w * mul] = np.asarray(img)
            have[:, ox * mul:ox * mul + w * mul] = msk
            ox += w
        # bleed the body colours out over the background so edge texels never pick up the backdrop
        idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
        return (out[idx[0], idx[1]] * SKIN_GAIN).astype(np.uint8)

    def st_of(uv, side):
        ph, x0, y0, x1, y1 = crops[side]
        ox = 0 if side == 0 else ws[0]
        return np.stack([(uv[:, 0] - x0) * k[side] + ox, (uv[:, 1] - y0) * k[side]], 1)

    return sheet(1), sheet(TGA_MUL), st_of(m["UVF"], 0), st_of(m["UVB"], 1), SW


# ------------------------------------------------------------------ skeleton + poses
def rx(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def abduction(v, side):
    """angle (deg) of a limb direction away from straight down, outwards positive (front plane)"""
    return math.degrees(math.atan2(side * v[1], -v[2]))


class Rig:
    def __init__(self, m):
        self.m = m
        J = m["joints"]
        self.J = J
        self.ab = {}
        for sd, sg in (("L", 1), ("R", -1)):
            K = {k: J[k] for k in J}
            self.ab["uarm_" + sd] = abduction(J["farm_" + sd] - J["uarm_" + sd], sg)
            self.ab["farm_" + sd] = abduction(J["hand_" + sd] - J["farm_" + sd], sg)
            tip = m["F"].kp["tip_" + sd]
            tip3 = np.array([0.0, (tip[0] - m["F"].kp["neck"][0]) * m["s"], SOLE_Z + (m["F"].sole - tip[1]) * m["s"]])
            self.ab["hand_" + sd] = abduction(tip3 - J["hand_" + sd], sg)
            self.ab["thigh_" + sd] = abduction(J["shin_" + sd] - J["thigh_" + sd], sg)
            self.ab["shin_" + sd] = abduction(J["foot_" + sd] - J["shin_" + sd], sg)

    def limbs(self, sd, arm_swing=0, arm_out=8, elbow=10, wrist=0, leg_swing=0, leg_out=3, knee=0, foot=0,
              arm_twist=0):
        """local rotations for one side.  swing: forwards positive; elbow/knee: bend positive; foot: toes up"""
        sg = 1 if sd == "L" else -1
        ab = self.ab
        return {
            "uarm_" + sd: ry(-arm_swing) @ rx(sg * (arm_out - ab["uarm_" + sd])) @ rz(sg * arm_twist),
            "farm_" + sd: ry(-elbow) @ rx(sg * (ab["uarm_" + sd] - ab["farm_" + sd])),
            "hand_" + sd: ry(-wrist) @ rx(sg * (ab["farm_" + sd] - ab["hand_" + sd])),
            "thigh_" + sd: ry(-leg_swing) @ rx(sg * (leg_out - ab["thigh_" + sd])),
            "shin_" + sd: ry(knee) @ rx(sg * (ab["thigh_" + sd] - ab["shin_" + sd])),
            "foot_" + sd: ry(-foot),
        }

    def pose(self, local, root=np.eye(3), pivot=None, lift=0.0, center=0.0):
        J = self.J
        if pivot is None:
            pivot = J["pelvis"]
        Rg, Pg = {}, {}
        for b in BONES:
            L = local.get(b, np.eye(3))
            p = PARENT[b]
            if p is None:
                Rg[b] = root @ L
                Pg[b] = pivot + root @ (J[b] - pivot)
            else:
                Rg[b] = Rg[p] @ L
                Pg[b] = Pg[p] + Rg[p] @ (J[b] - J[p])
        V, W = self.m["V"], self.m["W"]
        out = np.zeros_like(V)
        for b in BONES:
            i = BI[b]
            w = W[:, i]
            if not w.any():
                continue
            out += w[:, None] * ((V - J[b]) @ Rg[b].T + Pg[b])
        out[:, 2] += SOLE_Z - out[:, 2].min() + lift          # stand on the floor
        if center:
            mid = (out[:, :2].min(0) + out[:, :2].max(0)) / 2
            out[:, :2] -= mid * center
        return out


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def run_pose(rig, i, n=6):
    ph = 2 * math.pi * i / n
    sn, cs = math.sin(ph), math.cos(ph)
    loc = {"pelvis": rz(7 * sn) @ ry(11), "chest": rz(-15 * sn) @ ry(5), "head": rz(8 * sn) @ ry(-12)}
    for sd, sg in (("L", 1), ("R", -1)):
        sw = 40 * sn * sg + 6
        kn = 14 + 80 * ((1 + math.cos(ph + 0.5 + (0 if sg > 0 else math.pi))) / 2) ** 1.6
        ft = 0.6 * (kn - sw) - 5
        loc.update(rig.limbs(sd, arm_swing=-44 * sn * sg + 12, arm_out=12, elbow=85 + 18 * sn * sg * -1,
                             wrist=10, leg_swing=sw, leg_out=2, knee=kn, foot=ft))
    return rig.pose(loc, lift=1.6 * abs(sn) ** 2)


def idle_pose(rig, i, n):
    ph = 2 * math.pi * i / n
    loc = {"chest": ry(1.5 * math.sin(ph)), "head": rz(4 * math.sin(ph)) @ ry(-1.5 * math.sin(ph))}
    for sd in "LR":
        loc.update(rig.limbs(sd, arm_swing=3 + 2 * math.sin(ph), arm_out=9, elbow=12 + 3 * math.sin(ph), leg_out=4))
    return rig.pose(loc)


def pain_pose(rig, i, n, side=1):
    k = [0.6, 1.0, 0.8, 0.5, 0.25, 0.05][min(i, 5)]
    loc = {"pelvis": ry(-4 * k), "chest": ry(-16 * k) @ rz(side * 10 * k), "head": ry(-14 * k)}
    for sd in "LR":
        loc.update(rig.limbs(sd, arm_swing=10 + 20 * k, arm_out=10 + 28 * k, elbow=15 + 50 * k, leg_out=4,
                             leg_swing=4 * k, knee=12 * k))
    return rig.pose(loc)


def shoot_pose(rig, k, kick=1.0):
    """both hands up in front as if holding a gun; k = recoil 0..1"""
    loc = {"pelvis": ry(4), "chest": ry(-8 * k * kick) @ rz(-12), "head": ry(-4) @ rz(10)}
    loc.update(rig.limbs("R", arm_swing=78 - 18 * k * kick, arm_out=6, elbow=12 + 10 * k, wrist=-10,
                         leg_swing=-8, leg_out=6, knee=6))
    loc.update(rig.limbs("L", arm_swing=70 - 14 * k * kick, arm_out=-30, elbow=38 + 10 * k, wrist=-10,
                         leg_swing=14, leg_out=6, knee=10))
    return rig.pose(loc)


def axe_pose(rig, i, variant):
    """over-arm chop (variant 0/2) or side swipe (1/3) with the right hand"""
    t = i / 5.0
    loc = {"pelvis": ry(4)}
    if variant % 2 == 0:
        sw = 160 - 190 * smooth(t) if variant == 0 else 140 - 170 * smooth(t * 1.2)
        loc["chest"] = ry(-10 + 25 * smooth(t)) @ rz(-15 + 20 * t)
        loc.update(rig.limbs("R", arm_swing=sw, arm_out=10, elbow=40 - 30 * t, leg_swing=-6, leg_out=6, knee=8))
    else:
        tw = 50 - 100 * smooth(t)
        loc["chest"] = rz(tw * (1 if variant == 1 else -1) * 0.6) @ ry(6)
        loc.update(rig.limbs("R", arm_swing=70, arm_out=60 - 70 * smooth(t), elbow=20, leg_swing=-6, leg_out=6,
                             knee=8, arm_twist=0))
    loc.update(rig.limbs("L", arm_swing=20, arm_out=18, elbow=50, leg_swing=12, leg_out=6, knee=12))
    return rig.pose(loc)


def death_pose(rig, i, n, kind):
    """kind: back / forward / spin / knees / side"""
    t = i / (n - 1)
    J = rig.J
    feet = (J["foot_L"] + J["foot_R"]) / 2
    pivot = np.array([feet[0], feet[1], SOLE_Z])
    loc = {}
    if kind in ("back", "spin"):
        f = smooth(t * 1.15) if kind == "back" else smooth((t - 0.25) / 0.75)
        root = ry(-92 * f) @ (rz(70 * smooth(t)) if kind == "spin" else np.eye(3))
        loc["chest"] = ry(-10 * math.sin(math.pi * t))
        loc["head"] = ry(-20 * math.sin(math.pi * t) - 5 * f)
        for sd in "LR":
            loc.update(rig.limbs(sd, arm_swing=60 * math.sin(math.pi * min(1, t * 1.3)) + 20 * f,
                                 arm_out=15 + 50 * f, elbow=30 + 20 * f, leg_out=4 + 8 * f,
                                 leg_swing=25 * math.sin(math.pi * t), knee=50 * math.sin(math.pi * t) + 8 * f))
    elif kind in ("forward", "knees"):
        if kind == "knees":
            kneel = smooth(t / 0.45)
            f = smooth((t - 0.45) / 0.55)
        else:
            kneel = 0.4 * math.sin(math.pi * t)
            f = smooth(t * 1.1)
        root = ry(88 * f)
        loc["chest"] = ry(15 * kneel * (1 - f))
        loc["head"] = ry(-25 * f)
        for sd in "LR":
            loc.update(rig.limbs(sd, arm_swing=40 * kneel + 120 * f, arm_out=20 + 20 * f, elbow=40 * (1 - f) + 15,
                                 leg_swing=95 * kneel * (1 - f), leg_out=5, knee=120 * kneel * (1 - f) + 5 * f))
    else:
        f = smooth(t * 1.1)
        root = rx(85 * f)
        loc["chest"] = rx(-10 * math.sin(math.pi * t))
        for sd in "LR":
            loc.update(rig.limbs(sd, arm_swing=20 * f, arm_out=20 + 40 * f, elbow=30, leg_out=5 + 8 * f,
                                 knee=30 * math.sin(math.pi * t) + 10))
    return rig.pose(loc, root=root, pivot=pivot, center=f)


def all_frames(rig):
    """(name, verts) for the 143 player.mdl frames in player.qc order"""
    fr = []
    for pre in ("axrun", "rockrun"):
        fr += [("%s%d" % (pre, i + 1), run_pose(rig, i)) for i in range(6)]
    fr += [("stand%d" % (i + 1), idle_pose(rig, i, 5)) for i in range(5)]
    fr += [("axstnd%d" % (i + 1), idle_pose(rig, i, 12)) for i in range(12)]
    fr += [("axpain%d" % (i + 1), pain_pose(rig, i, 6, -1)) for i in range(6)]
    fr += [("pain%d" % (i + 1), pain_pose(rig, i, 6, 1)) for i in range(6)]
    fr += [("axdeth%d" % (i + 1), death_pose(rig, i, 9, "back")) for i in range(9)]
    fr += [("deatha%d" % (i + 1), death_pose(rig, i, 11, "back")) for i in range(11)]
    fr += [("deathb%d" % (i + 1), death_pose(rig, i, 9, "forward")) for i in range(9)]
    fr += [("deathc%d" % (i + 1), death_pose(rig, i, 15, "spin")) for i in range(15)]
    fr += [("deathd%d" % (i + 1), death_pose(rig, i, 9, "knees")) for i in range(9)]
    fr += [("deathe%d" % (i + 1), death_pose(rig, i, 9, "side")) for i in range(9)]
    fr += [("nailatt1", shoot_pose(rig, 0.5, 0.4)), ("nailatt2", shoot_pose(rig, 0.0, 0.4))]
    fr += [("light1", shoot_pose(rig, 0.3, 0.3)), ("light2", shoot_pose(rig, 0.1, 0.3))]
    kk = [1.0, 0.7, 0.45, 0.25, 0.1, 0.0]
    fr += [("rockatt%d" % (i + 1), shoot_pose(rig, kk[i], 1.4)) for i in range(6)]
    fr += [("shotatt%d" % (i + 1), shoot_pose(rig, kk[i], 1.0)) for i in range(6)]
    for v, pre in enumerate(("axatt", "axattb", "axattc", "axattd")):
        fr += [("%s%d" % (pre, i + 1), axe_pose(rig, i, v)) for i in range(6)]
    assert len(fr) == 143
    return fr


# ------------------------------------------------------------------ MDL
def write_mdl(path, m, frames, skin8, st_f, st_b, SW):
    V, tris, rad = m["V"], m["tris"], m["rad"]
    # a triangle takes the back photo when it faces away from the camera that took the front one
    side = np.array([0 if rad[i][0] + 0.15 * abs(rad[i][2]) >= -0.05 * np.linalg.norm(rad[i]) else 1
                     for i in range(len(tris))])
    key, out_tris = {}, []
    for (a, b, c), sd in zip(tris, side):
        vs = []
        for g in (a, b, c):
            if (g, sd) not in key:
                key[(g, sd)] = len(key)
            vs.append(key[(g, sd)])
        out_tris.append((vs[0], vs[2], vs[1]))           # Quake wants them clockwise from outside
    geo = np.zeros(len(key), int)
    st = np.zeros((len(key), 2))
    for (g, sd), i in key.items():
        geo[i] = g
        st[i] = (st_f if sd == 0 else st_b)[g]
    st = np.rint(st).astype(int)
    st[:, 0] = st[:, 0].clip(0, SW - 1)
    st[:, 1] = st[:, 1].clip(0, SKIN_H - 1)
    P = np.array([f[1] for f in frames])                 # frames x geo verts x 3
    mn, mx = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    scale = (mx - mn) / 255.0
    nv, nt = len(key), len(out_tris)
    radius = float(np.linalg.norm(P, axis=2).max())
    edge = np.mean([np.linalg.norm(V[a] - V[b]) for a, b, c in tris])
    b = bytearray(struct.pack("<4si3f3ff3f8if", b"IDPO", 6, *scale, *mn, radius, 0.0, 0.0, 22.0,
                              1, SW, SKIN_H, nv, nt, len(frames), 0, 0, float(edge)))
    b += struct.pack("<i", 0) + skin8.tobytes()
    for s_, t_ in st:
        b += struct.pack("<3i", 0, int(s_), int(t_))
    for t in out_tris:
        b += struct.pack("<4i", 1, *t)
    for name, pos in frames:
        q = np.rint((pos - mn) / scale).clip(0, 255).astype(np.uint8)
        # vertex normals (geometry tris are counter-clockwise from outside)
        n = np.zeros_like(pos)
        fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
        for j in range(3):
            np.add.at(n, tris[:, j], fn)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        ni = (n @ ANORM.T).argmax(1).astype(np.uint8)
        qv = q[geo]
        nn = ni[geo]
        b += struct.pack("<i", 0)
        b += bytes(list(qv.min(0)) + [0]) + bytes(list(qv.max(0)) + [0])
        b += name.encode("ascii")[:15].ljust(16, b"\0")
        b += np.concatenate([qv, nn[:, None]], 1).astype(np.uint8).tobytes()
    open(path, "wb").write(bytes(b))
    return nv, nt


def read_mdl(path):
    d = open(path, "rb").read()
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale, tr = np.array(h[2:5]), np.array(h[5:8])
    nsk, sw, sh, nv, nt, nf = h[12:18]
    o = 84
    skins = []
    for _ in range(nsk):
        assert struct.unpack_from("<i", d, o)[0] == 0
        skins.append(np.frombuffer(d, np.uint8, sw * sh, o + 4).reshape(sh, sw))
        o += 4 + sw * sh
    st = np.frombuffer(d, "<i4", nv * 3, o).reshape(nv, 3)
    o += nv * 12
    tri = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16
    frames = []
    for _ in range(nf):
        assert struct.unpack_from("<i", d, o)[0] == 0
        name = d[o + 12:o + 28].split(b"\0")[0].decode()
        v = np.frombuffer(d, np.uint8, nv * 4, o + 28).reshape(nv, 4)
        frames.append((name, v[:, :3] * scale + tr, v[:, 3]))
        o += 28 + nv * 4
    assert o == len(d), (o, len(d))
    return dict(skin=skins[0], sw=sw, sh=sh, st=st[:, 1:].astype(float), onseam=st[:, 0], tri=tri[:, 1:],
                frames=frames)


# ------------------------------------------------------------------ previews
def render(md, fi, yaw, size=220, zoom=3.6, tex=None):
    """orthographic software render of frame fi from direction yaw (0 = looking at his front)"""
    name, P, nidx = md["frames"][fi]
    a = math.radians(yaw)
    fwd = np.array([math.cos(a), math.sin(a), 0.0])          # camera sits at +fwd looking back
    right = np.array([-math.sin(a), math.cos(a), 0.0]) * -1
    sx = P @ right * zoom + size / 2
    sy = -(P[:, 2] - 3) * zoom + size / 2
    sz = P @ fwd
    img = np.full((size, size, 3), 40, np.uint8)
    zb = np.full((size, size), -1e9)
    T = md["tri"]
    if tex is None:
        tex = PALETTE[md["skin"]].astype(np.uint8)
    th, tw = tex.shape[:2]
    stx = (md["st"][:, 0] + 0.5) / md["sw"] * tw
    sty = (md["st"][:, 1] + 0.5) / md["sh"] * th
    for a_, b_, c_ in T:
        xs, ys = sx[[a_, b_, c_]], sy[[a_, b_, c_]]
        x0, x1 = int(max(0, math.floor(xs.min()))), int(min(size - 1, math.ceil(xs.max())))
        y0, y1 = int(max(0, math.floor(ys.min()))), int(min(size - 1, math.ceil(ys.max())))
        if x0 > x1 or y0 > y1:
            continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not ins.any():
            continue
        z = w0 * sz[a_] + w1 * sz[b_] + w2 * sz[c_]
        cur = zb[y0:y1 + 1, x0:x1 + 1]
        upd = ins & (z > cur)
        if not upd.any():
            continue
        cur[upd] = z[upd]
        u = (w0 * stx[a_] + w1 * stx[b_] + w2 * stx[c_]).astype(int).clip(0, tw - 1)
        v = (w0 * sty[a_] + w1 * sty[b_] + w2 * sty[c_]).astype(int).clip(0, th - 1)
        n = -np.cross(P[b_] - P[a_], P[c_] - P[a_])     # MDL tris are clockwise from outside
        n /= np.linalg.norm(n) + 1e-9
        lit = 0.55 + 0.45 * max(0.0, n @ np.array([0.5, 0.3, 0.8]) / 1.0) + 0.15 * max(0.0, n @ fwd)
        col = (tex[v, u].astype(float) * min(1.2, lit)).clip(0, 255).astype(np.uint8)
        img[y0:y1 + 1, x0:x1 + 1][upd] = col[upd]
    return img


def contact_sheet(md, path, tex=None):
    names = [f[0] for f in md["frames"]]
    rows = [
        [("stand1", y) for y in (0, 45, 90, 180, 270)],
        [("rockrun%d" % (i + 1), 90) for i in range(6)],
        [("rockrun%d" % (i + 1), 30) for i in range(6)],
        [("shotatt1", 30), ("axatt3", 30), ("pain2", 30), ("deatha6", 90), ("deatha11", 60), ("deathb9", 60)],
        [("deathc15", 60), ("deathd5", 90), ("deathd9", 60), ("deathe9", 30), ("axattb3", 30), ("axstnd6", 0)],
    ]
    S = 220
    sheet = np.zeros((S * len(rows), S * 6, 3), np.uint8)
    for r, row in enumerate(rows):
        for c, (nm, yaw) in enumerate(row):
            sheet[r * S:(r + 1) * S, c * S:(c + 1) * S] = render(md, names.index(nm), yaw, S, tex=tex)
    Image.fromarray(sheet).save(path)


def fit_overlay(m, path):
    """the fitted tube outlines drawn on both photos, to check the keypoints"""
    ims = []
    for side, ph in ((0, m["F"]), (1, m["Bk"])):
        im = Image.fromarray(ph.rgb).copy()
        dr = ImageDraw.Draw(im)
        for name in m["meas"]:
            pts = [tuple(q) for q in m["outline"](side, name)]
            dr.line(pts + [pts[0]], fill=(255, 0, 0), width=3)
        for k, p in ph.kp.items():
            dr.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(0, 255, 255))
        im = im.resize((int(im.width * 700 / im.height), 700))
        ims.append(im)
    out = Image.new("RGB", (ims[0].width + ims[1].width, 700))
    out.paste(ims[0], (0, 0))
    out.paste(ims[1], (ims[0].width, 0))
    out.save(path)


# ------------------------------------------------------------------ main
def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    for ch in (SUIT, ROBE, WIFE):
        if only and ch["name"] != only:
            continue
        m = build(ch)
        skin, big, st_f, st_b, SW = make_skin(m, ch)
        skin8 = to_palette(skin)
        rig = Rig(m)
        frames = all_frames(rig)
        path = os.path.join(PROGS, ch["name"] + ".mdl")
        nv, nt = write_mdl(path, m, frames, skin8, st_f, st_b, SW)
        Image.fromarray(big).save(path + "_0.tga", compression="tga_rle")
        md = read_mdl(path)
        assert len(md["frames"]) == 143
        lo = np.array([f[1].min(0) for f in md["frames"]])
        hi = np.array([f[1].max(0) for f in md["frames"]])
        print("%s: %d verts, %d tris, skin %dx%d, %d frames, z %.1f..%.1f, stand height %.1f, %d bytes"
              % (ch["name"], nv, nt, SW, SKIN_H, len(md["frames"]), lo[:, 2].min(), hi[:, 2].max(),
                 hi[12, 2] - lo[12, 2], os.path.getsize(path)))
        if PREVIEW:
            os.makedirs(PREVIEW, exist_ok=True)
            fit_overlay(m, os.path.join(PREVIEW, ch["name"] + "_fit.png"))
            contact_sheet(md, os.path.join(PREVIEW, ch["name"] + "_frames8bit.png"))
            contact_sheet(md, os.path.join(PREVIEW, ch["name"] + "_frames.png"), tex=big)
            Image.fromarray(PALETTE[skin8].astype(np.uint8)).save(os.path.join(PREVIEW, ch["name"] + "_skin8.png"))


if __name__ == "__main__":
    main()
