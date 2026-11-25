"""Build smooth classic Quake Ranger (`progs/player_id1.mdl`) death animations,
classic-skinned severed gibs, deterministic `zz_player_deaths.pk3` overlay, and
100% self-contained WebGL2 HTML 3D voting studio (`docs/player_death_vote.html`).

Usage:
    python -E -P source/mm_tools/build_player_deaths.py
    python -E -P source/mm_tools/build_player_deaths.py --render-check
    python -E -P source/mm_tools/build_player_deaths.py --picks ko_spin_b,gut_slide_a,limbs_off_a,head_off_a,backflip_a,spasm_a
    python -E -P source/mm_tools/build_player_deaths.py --votes path/to/votes.json
"""
import argparse
import base64
import gzip
import io
import json
import math
import os
import struct
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gokart_driver as gd

REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BAKER_PK3 = os.path.join(REPO_ROOT, "bakersfield.pk3")
ID1_PAK0 = os.path.abspath(os.path.join(REPO_ROOT, "..", "id1", "pak0.pak"))
ID1_PLAYER_MDL = os.path.join(HERE, "id1", "player.mdl")
ID1_H_PLAYER_MDL = os.path.join(HERE, "id1", "h_player.mdl")
TEMPLATE_HTML = os.path.join(HERE, "player_death_vote.template.html")
OUT_HTML = os.path.join(REPO_ROOT, "docs", "player_death_vote.html")
OUT_PK3 = os.path.join(REPO_ROOT, "zz_player_deaths.pk3")
OUT_MANIFEST = os.path.join(HERE, "out", "player_deaths_manifest.json")
OUT_QC_FRAMES = os.path.join(REPO_ROOT, "source", "qc_combat_decomp", "player_deaths_frames.qc")
OUT_PNG_CHECK = os.path.join(HERE, "out", "player_deaths_check.png")

DEFAULT_PICKS = {
    "ko_spin": "ko_spin_a",
    "gut_slide": "gut_slide_a",
    "limbs_off": "limbs_off_a",
    "head_off": "head_off_a",
    "backflip": "backflip_a",
    "spasm": "spasm_a",
}


# ---------------------------------------------------------------------------
# Vector & 3x3 rotation helpers (Quake coords: +X fwd, +Y left, +Z up)
# ---------------------------------------------------------------------------

def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _vnorm(a):
    l = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-8 else (1.0, 0.0, 0.0)


def _vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _rot_x(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def _rot_y(v, deg):
    # +deg pitches +X down toward -Z; -deg pitches +X up toward +Z (chin up)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def _rot_z(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def _rot_zyx(v, yaw, pitch, roll):
    return _rot_z(_rot_y(_rot_x(v, roll), pitch), yaw)


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _smootherstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _lerp(a, b, t):
    return a + (b - a) * t


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _ease_in(t):
    t = max(0.0, min(1.0, t))
    return t * t * t


def _sample_keyframes(keyframes, t):
    """Linearly/smoothly interpolate dict of float params across sorted [(t_i, dict_i), ...]."""
    if t <= keyframes[0][0]:
        return dict(keyframes[0][1])
    if t >= keyframes[-1][0]:
        return dict(keyframes[-1][1])
    for i in range(len(keyframes) - 1):
        t0, d0 = keyframes[i]
        t1, d1 = keyframes[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            # Use smoothstep unless a segment requests linear via '_linear': True
            if not d1.get("_linear", False):
                u = _smoothstep(u)
            out = {}
            keys = set(d0.keys()) | set(d1.keys())
            for k in keys:
                if k.startswith("_"):
                    continue
                v0 = d0.get(k, 0.0)
                v1 = d1.get(k, v0)
                out[k] = v0 + (v1 - v0) * u
            return out
    return dict(keyframes[-1][1])


# ---------------------------------------------------------------------------
# MDL loading & classic limb gib generation
# ---------------------------------------------------------------------------

def _load_anorms():
    cand = os.path.abspath(os.path.join(REPO_ROOT, "..", "monster_page", "anorm.json"))
    if os.path.isfile(cand):
        flat = json.load(open(cand, "r", encoding="utf-8"))
        return np.array(flat, dtype=np.float64).reshape(-1, 3)
    pts = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(162):
        z = 1.0 - (i / 161.0) * 2.0
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = ga * i
        pts.append((math.cos(th) * r, math.sin(th) * r, z))
    return np.array(pts, dtype=np.float64)


def _pack_mdl_frame(name, verts, tris, scale, trans, anorms):
    nv = len(verts)
    pos = np.array(verts, dtype=np.float64)
    sc = np.array(scale, dtype=np.float64)
    tr = np.array(trans, dtype=np.float64)
    q = np.rint((pos - tr) / sc).clip(0, 255).astype(np.uint8)

    vn = np.zeros((nv, 3), dtype=np.float64)
    for _, v0, v1, v2 in tris:
        fn = -np.cross(pos[v1] - pos[v0], pos[v2] - pos[v0])
        vn[v0] += fn
        vn[v1] += fn
        vn[v2] += fn
    norms = np.linalg.norm(vn, axis=1, keepdims=True)
    vn = vn / np.maximum(norms, 1e-9)
    ni = (vn @ anorms.T).argmax(axis=1).astype(np.uint8)

    bmin = bytes(list(q.min(axis=0)) + [0])
    bmax = bytes(list(q.max(axis=0)) + [0])
    nm = name.encode("ascii")[:15].ljust(16, b"\x00")
    vbytes = np.concatenate([q, ni[:, None]], axis=1).astype(np.uint8).tobytes()
    return struct.pack("<i", 0) + bmin + bmax + nm + vbytes


def _dilate_rgb(rgb):
    mask = rgb.sum(axis=2) > 12
    padded = rgb.copy()
    cur_mask = mask.copy()
    for _ in range(2):
        nxt = padded.copy()
        nxt_mask = cur_mask.copy()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr = np.roll(np.roll(padded, dy, axis=0), dx, axis=1)
            rm = np.roll(np.roll(cur_mask, dy, axis=0), dx, axis=1)
            fill = (~nxt_mask) & rm
            nxt[fill] = rr[fill]
            nxt_mask |= fill
        padded = nxt
        cur_mask = nxt_mask
    return padded


def load_id1_full(bakersfield_pk3=BAKER_PK3):
    """Load the 212-vert, 408-tri classic player_id1.mdl + dilated RGB skin + raw header info."""
    data = gd._load_player_mdl_bytes(bakersfield_pk3=bakersfield_pk3)
    pal = gd._load_quake_palette()
    hdr = list(struct.unpack("<4si3f3ff3f8if", data[:84]))
    scale, trans = tuple(hdr[2:5]), tuple(hdr[5:8])
    nskins, sw, sh, nverts, ntris, nframes = hdr[12:18]
    assert hdr[0] == b"IDPO" and hdr[1] == 6 and nverts == 212 and ntris == 408

    skin_idx = data[88 : 88 + sw * sh]
    im_p = Image.frombytes("P", (sw, sh), skin_idx)
    im_p.putpalette(pal)
    skin_rgb = _dilate_rgb(np.array(im_p.convert("RGB"), dtype=np.uint8))

    pos = 84 + nskins * (4 + sw * sh)
    st = [struct.unpack("<3i", data[pos + 12 * i : pos + 12 * i + 12]) for i in range(nverts)]
    pos += 12 * nverts
    tris = [struct.unpack("<4i", data[pos + 16 * i : pos + 16 * i + 16]) for i in range(ntris)]
    pos += 16 * ntris
    frame_len = 4 + 8 + 16 + nverts * 4
    raw_frames = [data[pos + i * frame_len : pos + (i + 1) * frame_len] for i in range(nframes)]

    def get_frame(fi):
        fbase = pos + fi * frame_len
        name = data[fbase + 12 : fbase + 28].split(b"\x00", 1)[0].decode("ascii", "ignore")
        verts = [
            tuple(data[fbase + 28 + 4 * vi + k] * scale[k] + trans[k] for k in range(3))
            for vi in range(nverts)
        ]
        return name, verts

    return {
        "raw": data,
        "hdr": hdr,
        "scale": scale,
        "trans": trans,
        "nskins": nskins,
        "sw": sw,
        "sh": sh,
        "skin_idx": skin_idx,
        "skin_rgb": skin_rgb,
        "st": st,
        "tris": tris,
        "nframes": nframes,
        "raw_frames": raw_frames,
        "get_frame": get_frame,
        "pal": pal,
    }


def load_id1_head_gib():
    """Load classic 1996 progs/h_player.mdl (committed asset preferred, id1/pak0.pak fallback)."""
    if os.path.isfile(ID1_H_PLAYER_MDL):
        with open(ID1_H_PLAYER_MDL, "rb") as f:
            raw = f.read()
    else:
        raw = gd._read_pak_entry(ID1_PAK0, "progs/h_player.mdl")
    pal = gd._load_quake_palette()
    hdr = struct.unpack("<4si3f3ff3f8if", raw[:84])
    scale, trans = hdr[2:5], hdr[5:8]
    nskins, sw, sh, nverts, ntris, nframes = hdr[12:18]
    skin_idx = raw[88 : 88 + sw * sh]
    im_p = Image.frombytes("P", (sw, sh), skin_idx)
    im_p.putpalette(pal)
    skin_rgb = _dilate_rgb(np.array(im_p.convert("RGB"), dtype=np.uint8))

    pos = 84 + nskins * (4 + sw * sh)
    st = [struct.unpack("<3i", raw[pos + 12 * i : pos + 12 * i + 12]) for i in range(nverts)]
    pos += 12 * nverts
    tris = [struct.unpack("<4i", raw[pos + 16 * i : pos + 16 * i + 16]) for i in range(ntris)]
    pos += 16 * ntris
    verts = [
        tuple(raw[pos + 28 + 4 * vi + k] * scale[k] + trans[k] for k in range(3))
        for vi in range(nverts)
    ]
    return {
        "raw": raw,
        "sw": sw,
        "sh": sh,
        "skin_rgb": skin_rgb,
        "st": st,
        "tris": tris,
        "verts": verts,
    }


def _find_blood_palette_index(pal_bytes):
    """Find a rich dark crimson index (<224 non-fullbright) in Quake palette for stump caps."""
    best_i, best_d = 70, 1e18
    target = (110, 10, 10)
    for i in range(224):
        r, g, b = pal_bytes[3 * i], pal_bytes[3 * i + 1], pal_bytes[3 * i + 2]
        d = (r - target[0]) ** 2 + (g - target[1]) ** 2 + (b - target[2]) ** 2
        if d < best_d:
            best_d, best_i = d, i
    return best_i


def build_classic_limb_gibs(mdl_info, anorms, bakersfield_pk3=BAKER_PK3):
    """Build 4 classic-skinned severed limb .mdl binaries & WebGL geometry from id1/player.mdl."""
    sw, sh = mdl_info["sw"], mdl_info["sh"]
    st_all = mdl_info["st"]
    tris_all = mdl_info["tris"]
    _, v17 = mdl_info["get_frame"](17)
    _, _, _, body, _, _ = gd._parse_id1_body(bakersfield_pk3=bakersfield_pk3)
    part_of = {vi: gd._classify_vert(vi, st_all, sw, sh)[0] for vi in body}

    # Paint a 6x6 blood patch at top-left corner (0..6, 0..6) of a copy of skin_idx for stump caps
    blood_idx = _find_blood_palette_index(mdl_info["pal"])
    gib_skin_arr = np.frombuffer(mdl_info["skin_idx"], dtype=np.uint8).reshape(sh, sw).copy()
    gib_skin_arr[0:8, 0:8] = blood_idx
    im_p = Image.frombytes("P", (sw, sh), gib_skin_arr.tobytes())
    im_p.putpalette(mdl_info["pal"])
    gib_skin_rgb = _dilate_rgb(np.array(im_p.convert("RGB"), dtype=np.uint8))

    gibs = {}
    name_map = {
        "l_arm": "gib_id1_arm_l",
        "r_arm": "gib_id1_arm_r",
        "l_leg": "gib_id1_leg_l",
        "r_leg": "gib_id1_leg_r",
    }

    for part_key, gib_name in name_map.items():
        pverts = sorted(vi for vi in body if part_of[vi] == part_key)
        pset = set(pverts)
        # Triangles purely inside this limb
        ptris = [t for t in tris_all if t[1] in pset and t[2] in pset and t[3] in pset]
        # Border vertices touching torso
        cross = [t for t in tris_all if any(v in pset for v in t[1:]) and any(part_of.get(v) == "torso" for v in t[1:])]
        border = sorted({v for t in cross for v in t[1:] if v in pset})
        # Find boundary directed edges on the open cut ring
        edge_counts = {}
        for _, a, b, c in ptris:
            for u, w in ((a, b), (b, c), (c, a)):
                edge_counts[(u, w)] = edge_counts.get((u, w), 0) + 1
        open_edges = [(u, w) for (u, w), cnt in edge_counts.items() if (w, u) not in edge_counts]

        # Center limb around its CoM so MOVETYPE_BOUNCE spins cleanly
        raw_pts = [v17[vi] for vi in pverts]
        com = gd._avg(raw_pts)
        local_pts = [_vsub(v17[vi], com) for vi in pverts]
        # Cap center vertex at centroid of border vertices
        cap_pt = _vsub(gd._avg([v17[vi] for vi in border]), com)
        remap = {vi: idx for idx, vi in enumerate(pverts)}
        cap_idx = len(local_pts)
        local_pts.append(cap_pt)

        # ST list: reuse original st for limb verts, blood patch (3, 3) for cap center
        gib_st = [st_all[vi] for vi in pverts] + [(0, 3, 3)]
        gib_tris = [(ff, remap[a], remap[b], remap[c]) for ff, a, b, c in ptris]
        for u, w in open_edges:
            if u in border or w in border:
                # Reverse winding (w -> u -> cap_idx) to close the cut cleanly facing outward
                gib_tris.append((0, remap[w], remap[u], cap_idx))

        # Tight MDL bounding box for high precision on small limb gib
        xs = [p[0] for p in local_pts]
        ys = [p[1] for p in local_pts]
        zs = [p[2] for p in local_pts]
        mins = (min(xs) - 0.5, min(ys) - 0.5, min(zs) - 0.5)
        maxs = (max(xs) + 0.5, max(ys) + 0.5, max(zs) + 0.5)
        sc = tuple(max((maxs[k] - mins[k]) / 255.0, 1e-4) for k in range(3))
        tr = mins

        # Bounding radius & pack IDPO v6
        rad = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in local_pts)
        hdr = struct.pack(
            "<4si3f3ff3f8if",
            b"IDPO", 6,
            sc[0], sc[1], sc[2],
            tr[0], tr[1], tr[2],
            rad,
            0.0, 0.0, 0.0,
            1, sw, sh, len(local_pts), len(gib_tris), 1,
            0, 0, 0.0,
        )
        skin_blob = struct.pack("<i", 0) + gib_skin_arr.tobytes()
        st_blob = b"".join(struct.pack("<3i", *s) for s in gib_st)
        tri_blob = b"".join(struct.pack("<4i", *t) for t in gib_tris)
        fr_blob = _pack_mdl_frame("gib1", local_pts, gib_tris, sc, tr, anorms)
        raw_mdl = hdr + skin_blob + st_blob + tri_blob + fr_blob

        gibs[part_key] = {
            "name": gib_name,
            "path": f"progs/{gib_name}.mdl",
            "raw": raw_mdl,
            "verts": local_pts,
            "tris": gib_tris,
            "st": gib_st,
            "sw": sw,
            "sh": sh,
            "skin_rgb": gib_skin_rgb,
        }
    return gibs


# ---------------------------------------------------------------------------
# Articulated Classic Ranger Rig (149-vert body + 63 weapon verts)
# ---------------------------------------------------------------------------

class RangerRig:
    def __init__(self, mdl_info, bakersfield_pk3=BAKER_PK3):
        self.sw = mdl_info["sw"]
        self.sh = mdl_info["sh"]
        self.st = mdl_info["st"]
        self.tris = mdl_info["tris"]
        _, self.stand1 = mdl_info["get_frame"](12)
        _, self.v17 = mdl_info["get_frame"](17)
        _, _, _, self.body, self.body_tris, _ = gd._parse_id1_body(bakersfield_pk3=bakersfield_pk3)
        self.body_set = set(self.body)
        self.parts = {}
        self.uvs = {}
        for vi in self.body:
            pn, uf, vf = gd._classify_vert(vi, self.st, self.sw, self.sh)
            self.parts.setdefault(pn, []).append(vi)
            self.uvs[vi] = (uf, vf)

        # Seam border sets for clean stump collapsing
        self.borders = {}
        part_of = {vi: self._part_of(vi) for vi in self.body}
        for p in ("head", "l_arm", "r_arm", "l_leg", "r_leg"):
            cross = [t for t in self.body_tris if any(part_of[v] == p for v in t[1:]) and any(part_of[v] == "torso" for v in t[1:])]
            self.borders[p] = {v for t in cross for v in t[1:] if part_of[v] == p}

        # Precompute source limb landmarks from axstnd1 (v17)
        self.src_arms = {}
        for side in ("l_arm", "r_arm"):
            av = self.parts[side]
            self.src_arms[side] = [
                gd._avg([self.v17[i] for i in av if 0.20 < self.uvs[i][1] <= 0.27]),
                gd._avg([self.v17[i] for i in av if 0.30 <= self.uvs[i][1] <= 0.38]),
                gd._avg([self.v17[i] for i in av if 0.44 <= self.uvs[i][1] <= 0.50]),
                gd._avg([self.v17[i] for i in av if self.uvs[i][1] > 0.51]),
            ]
        self.src_legs = {}
        for side in ("l_leg", "r_leg"):
            lv = self.parts[side]
            self.src_legs[side] = [
                gd._avg([self.v17[i] for i in lv if self.uvs[i][1] <= 0.63]),
                gd._avg([self.v17[i] for i in lv if 0.69 <= self.uvs[i][1] <= 0.77]),
                gd._avg([self.v17[i] for i in lv if 0.88 <= self.uvs[i][1] <= 0.92]),
                gd._avg([self.v17[i] for i in lv if self.uvs[i][1] >= 0.94]),
            ]

    def _part_of(self, vi):
        return gd._classify_vert(vi, self.st, self.sw, self.sh)[0]

    @staticmethod
    def _canon_torso_vert(vi, raw_v):
        if vi == 58:
            raw_v = (-4.2, +10.2, 18.2)
        elif vi == 30:
            raw_v = (-4.2, -10.2, 18.2)
        elif vi == 65:
            raw_v = (-7.8, +4.2, 17.0)
        p = _vsub(raw_v, (-4.5, -0.6, -2.2))
        return _rot_z(p, 8.0)

    def pose(self, p):
        """Evaluate 212-vert pose dict from articulated parameter dict `p`."""
        sp_p = p.get("spine_pitch", 0.0)
        sp_r = p.get("spine_roll", 0.0)
        sp_y = p.get("spine_yaw", 0.0)
        pelv_p = p.get("pelvis_pitch", 0.0)

        def xform_torso(vi):
            pt = self._canon_torso_vert(vi, self.v17[vi])
            h = max(0.0, min(1.0, pt[2] / 22.2))
            w_pelv = max(0.0, 1.0 - h / 0.45)
            w_chest = max(0.0, (h - 0.22) / 0.78)
            q_pelv = _rot_y((pt[0], pt[1], pt[2] - 2.0), pelv_p)
            q_pelv = (q_pelv[0], q_pelv[1], q_pelv[2] + 2.0)

            q_chest = _rot_zyx((pt[0], pt[1], pt[2] - 6.0), sp_y, sp_p, sp_r)
            q_chest = (q_chest[0], q_chest[1], q_chest[2] + 6.0)
            ws = max(1e-6, w_pelv + w_chest)
            out = _vlerp(q_pelv, q_chest, w_chest / ws)
            return out

        posed = {}
        for vi in self.parts["torso"]:
            posed[vi] = xform_torso(vi)

        # Neck anchor on bent chest
        q_neck = _rot_z(_vsub((-1.2, -0.4, 18.2), (-4.5, -0.6, -2.2)), 8.0)
        q_neck = _rot_zyx((q_neck[0], q_neck[1], q_neck[2] - 6.0), sp_y, sp_p, sp_r)
        neck_world = (q_neck[0], q_neck[1], q_neck[2] + 6.0)

        # Head
        detach_head = p.get("detach_head", 0.0) > 0.5
        if detach_head:
            # Sunken collar stump
            collar_ctr = gd._avg([posed[vi] for vi in (34, 57, 60, 65, 91, 176, 198) if vi in posed])
            down_dir = _rot_zyx((0.0, 0.0, -1.0), sp_y, sp_p, sp_r)
            sink_ctr = _vadd(collar_ctr, _vmul(down_dir, 2.2))
            for vi in self.parts["head"]:
                if vi in self.borders["head"]:
                    posed[vi] = _vlerp(xform_torso(vi), collar_ctr, 0.55)
                else:
                    posed[vi] = sink_ctr
        else:
            hp = p.get("head_pitch", 0.0)
            hy = p.get("head_yaw", 0.0)
            hr = p.get("head_roll", 0.0)
            head_origin = (-1.6, -0.3, 18.2)
            for vi in self.parts["head"]:
                q = _vsub(self.v17[vi], head_origin)
                q = _rot_z(q, 6.0)
                q = _rot_zyx(q, hy, hp, hr)
                q = _rot_zyx(q, sp_y, sp_p, sp_r)
                posed[vi] = _vadd((q[0] + 0.8, q[1], q[2] + 0.2), neck_world)

        # Arms FK
        detach_arms = p.get("detach_arms", 0.0) > 0.5
        for side_key, sign, tag in (("l_arm", +1.0, "la"), ("r_arm", -1.0, "ra")):
            av = self.parts[side_key]
            sh_canon = _rot_z(_vsub((-4.2, sign * 8.6, 15.6), (-4.5, -0.6, -2.2)), 8.0)
            sh_rot = _rot_zyx((sh_canon[0], sh_canon[1], sh_canon[2] - 6.0), sp_y, sp_p, sp_r)
            t_sh = (sh_rot[0], sh_rot[1], sh_rot[2] + 6.0)

            if detach_arms:
                out_dir = _rot_zyx((0.0, sign, -0.2), sp_y, sp_p, sp_r)
                stump_tip = _vadd(t_sh, _vmul(_vnorm(out_dir), 1.6))
                for vi in av:
                    if vi in self.borders[side_key]:
                        posed[vi] = _vlerp(xform_torso(vi), stump_tip, 0.45)
                    else:
                        posed[vi] = _vadd(t_sh, _vmul(_vnorm(out_dir), 0.7))
                continue

            # Shoulder angles: pitch (+ fwd / - back), abduct (+ out from body), roll (twist)
            sh_pitch = p.get(f"{tag}_pitch", 10.0)
            sh_abd = p.get(f"{tag}_abd", 18.0)
            sh_twist = p.get(f"{tag}_twist", 0.0)
            el_flex = max(0.0, min(145.0, p.get(f"{tag}_elbow", 25.0)))

            # Upper arm vector in chest-local coords: starts pointing down (0, 0, -1)
            u_local = (0.0, 0.0, -1.0)
            u_local = _rot_x(u_local, sign * sh_abd)     # abduct outward (+Y for L, -Y for R)
            u_local = _rot_y(u_local, -sh_pitch)         # +pitch swings arm forward (+X)
            u_world = _vnorm(_rot_zyx(u_local, sp_y, sp_p, sp_r))

            # Forearm flexes forward (+X in upper arm's local frame, rotated by sh_twist around upper arm)
            f_local = (0.0, 0.0, -1.0)
            f_local = _rot_y(f_local, -el_flex)
            f_local = _rot_z(f_local, sign * sh_twist)
            f_local = _rot_x(f_local, sign * sh_abd)
            f_local = _rot_y(f_local, -sh_pitch)
            f_world = _vnorm(_rot_zyx(f_local, sp_y, sp_p, sp_r))

            t_el = _vadd(t_sh, _vmul(u_world, 7.6))
            t_wr = _vadd(t_el, _vmul(f_world, 7.2))
            t_hd = _vadd(t_wr, _vmul(f_world, 3.8))

            fwd_u = _vnorm(_rot_zyx(_rot_y(_rot_x(_rot_z((1.0, 0.0, 0.0), sign * sh_twist), sign * sh_abd), -sh_pitch), sp_y, sp_p, sp_r))
            arm_posed = gd._pose_limb_chain(
                self.v17, av, self.uvs,
                self.src_arms[side_key],
                [t_sh, t_el, t_wr, t_hd],
                [(0.0, sign, 0.0), (0.0, sign, 0.0), (1.0, 0.0, 0.0)],
                [fwd_u, fwd_u, fwd_u],
                socket_blend_vmax=0.29,
                torso_pos_fn=xform_torso,
            )
            for vi, pv in arm_posed.items():
                posed[vi] = xform_torso(vi) if self.uvs[vi][1] <= 0.20 else pv

        # Legs FK
        detach_legs = p.get("detach_legs", 0.0) > 0.5
        for side_key, sign, tag in (("l_leg", +1.0, "ll"), ("r_leg", -1.0, "rl")):
            lv = self.parts[side_key]
            hp_rot = _rot_y((0.5, sign * 4.0, -3.5 - 2.0), pelv_p)
            t_hip = (hp_rot[0], hp_rot[1], hp_rot[2] + 2.0)

            if detach_legs:
                down_dir = _vnorm(_rot_y((0.0, sign * 0.15, -1.0), pelv_p))
                stump_tip = _vadd(t_hip, _vmul(down_dir, 3.2))
                for vi in lv:
                    if vi in self.borders[side_key]:
                        posed[vi] = _vlerp(xform_torso(vi), stump_tip, 0.38)
                    else:
                        posed[vi] = _vadd(t_hip, _vmul(down_dir, 2.2))
                continue

            hip_pitch = p.get(f"{tag}_pitch", 0.0)
            hip_abd = p.get(f"{tag}_abd", 6.0)
            hip_yaw = p.get(f"{tag}_yaw", 0.0)
            knee_flex = max(0.0, min(145.0, p.get(f"{tag}_knee", 10.0)))
            foot_pitch = p.get(f"{tag}_ankle", 0.0)

            th_local = (0.0, 0.0, -1.0)
            th_local = _rot_x(th_local, sign * hip_abd)
            th_local = _rot_y(th_local, -hip_pitch)
            th_local = _rot_z(th_local, sign * hip_yaw)
            th_dir = _vnorm(_rot_y(th_local, pelv_p))

            # Knee bends shin backward (+rot_y)
            sh_local = _rot_y((0.0, 0.0, -1.0), knee_flex)
            sh_local = _rot_x(sh_local, sign * hip_abd)
            sh_local = _rot_y(sh_local, -hip_pitch)
            sh_local = _rot_z(sh_local, sign * hip_yaw)
            sh_dir = _vnorm(_rot_y(sh_local, pelv_p))

            ft_local = _rot_y((1.0, 0.0, -0.35), knee_flex + foot_pitch)
            ft_local = _rot_x(ft_local, sign * hip_abd)
            ft_local = _rot_y(ft_local, -hip_pitch)
            ft_local = _rot_z(ft_local, sign * hip_yaw)
            ft_dir = _vnorm(_rot_y(ft_local, pelv_p))

            fwd_l = _vnorm(_rot_y(_rot_z(_rot_y(_rot_x((1.0, 0.0, 0.0), sign * hip_abd), -hip_pitch), sign * hip_yaw), pelv_p))
            t_knee = _vadd(t_hip, _vmul(th_dir, 9.0))
            t_ank = _vadd(t_knee, _vmul(sh_dir, 9.4))
            t_boot = _vadd(t_ank, _vmul(ft_dir, 4.4))

            leg_posed = gd._pose_limb_chain(
                self.v17, lv, self.uvs,
                self.src_legs[side_key],
                [t_hip, t_knee, t_ank, t_boot],
                [(1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)],
                [fwd_l, fwd_l, _vnorm((sh_dir[0] * -1.0, sh_dir[1], -sh_dir[2]))],
                socket_blend_vmax=0.63,
                torso_pos_fn=xform_torso,
            )
            for vi, pv in leg_posed.items():
                posed[vi] = pv

        # Whole-body rigid CoM transform (for spinning/backflips/falling flat)
        byaw = p.get("body_yaw", 0.0)
        bpitch = p.get("body_pitch", 0.0)
        broll = p.get("body_roll", 0.0)
        bx = p.get("body_x", 0.0)
        by = p.get("body_y", 0.0)
        bz = p.get("body_z", 0.0)
        com = (0.0, 0.0, 4.0)

        for vi in self.body:
            q = _vsub(posed[vi], com)
            q = _rot_zyx(q, byaw, bpitch, broll)
            posed[vi] = (q[0] + bx, q[1] + by + com[1], q[2] + bz + com[2])

        # Optional ground contact clamp (prevents sinking below Quake floor z = -23.6)
        if p.get("floor_clamp", 0.0) > 0.5:
            min_z = min(posed[vi][2] for vi in self.body)
            floor_z = -23.6
            if min_z < floor_z:
                dz = floor_z - min_z
                for vi in self.body:
                    x, y, z = posed[vi]
                    posed[vi] = (x, y, z + dz)

        # Combine into full 212-vert frame (tuck weapons into chest center)
        chest_pts = [posed[vi] for vi in self.parts["torso"]]
        chest_c = gd._avg(chest_pts)
        w_scale = p.get("weapon_scale", 0.0)
        blend_stand = p.get("blend_stand", 0.0)

        out = []
        for vi in range(212):
            if vi in self.body_set:
                v_out = posed[vi]
                if blend_stand > 1e-4:
                    v_out = _vlerp(v_out, self.stand1[vi], blend_stand)
                out.append(v_out)
            else:
                if w_scale <= 1e-4:
                    out.append(chest_c)
                else:
                    out.append(_vlerp(chest_c, self.stand1[vi], w_scale))
        return out


# ---------------------------------------------------------------------------
# 18 Death Animation Definitions (6 Categories x 3 Candidate Variations)
# ---------------------------------------------------------------------------

def _base_pose(**kw):
    d = {
        "spine_pitch": 0.0, "spine_roll": 0.0, "spine_yaw": 0.0, "pelvis_pitch": 0.0,
        "head_pitch": 0.0, "head_yaw": 0.0, "head_roll": 0.0,
        "la_pitch": 8.0, "la_abd": 14.0, "la_twist": 0.0, "la_elbow": 22.0,
        "ra_pitch": 8.0, "ra_abd": 14.0, "ra_twist": 0.0, "ra_elbow": 22.0,
        "ll_pitch": 6.0, "ll_abd": 6.0, "ll_yaw": 0.0, "ll_knee": 12.0, "ll_ankle": 0.0,
        "rl_pitch": -6.0, "rl_abd": 6.0, "rl_yaw": 0.0, "rl_knee": 14.0, "rl_ankle": 0.0,
        "body_yaw": 0.0, "body_pitch": 0.0, "body_roll": 0.0,
        "body_x": 0.0, "body_y": 0.0, "body_z": 0.0,
        "detach_head": 0.0, "detach_arms": 0.0, "detach_legs": 0.0,
        "floor_clamp": 0.0, "weapon_scale": 0.0, "blend_stand": 0.0,
    }
    d.update(kw)
    return d


def _gen_ko_spin(rig, variant):
    """Category 1: Knocked out hard, spinning in the air -> falls to the ground."""
    if variant == "a":
        # Corkscrew uppercut spin: 2.5 helicopter spins, wide flailing limbs, back-splat
        n = 26
        spins_deg = 900.0
        tilt_target = -78.0
        land_t = 0.72
        title = "Var A · Corkscrew Uppercut"
        desc = "Jaw-rocked uppercut snap launches him into 2.5 helicopter spins with limbs splayed wide before crashing flat onto his back."
        qc_vel = {"back": 180.0, "up": 280.0, "slide_friction": 0.85}
    elif variant == "b":
        # Wild ragdoll tornado: 3.5 fast skewed spins, knees tucked loosely, side-roll landing
        n = 28
        spins_deg = 1260.0
        tilt_target = -55.0
        land_t = 0.74
        title = "Var B · Ragdoll Tornado"
        desc = "Rapid 3.5-turn skewed tornado spin with loose ragdoll knees, dropping onto his side and rolling a quarter-turn to rest."
        qc_vel = {"back": 220.0, "up": 320.0, "slide_friction": 0.85}
    else:
        # Heavy side-hook cartwheel spin: roll + yaw spiral, face-down slam
        n = 26
        spins_deg = 720.0
        tilt_target = 88.0
        land_t = 0.70
        title = "Var C · Cartwheel Knockout"
        desc = "Violent sideways hook sends him cartwheeling in a roll+yaw spiral before slamming face-down with an arm draped over his head."
        qc_vel = {"back": 240.0, "up": 250.0, "slide_friction": 0.85}

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.12)
        air_u = min(1.0, t / land_t)
        land_u = max(0.0, (t - land_t) / (1.0 - land_t))

        # Spin eases out rapidly right before impact
        spin_u = _ease_out(min(1.0, t / (land_t + 0.08)))
        yaw = spins_deg * spin_u

        if variant == "a":
            pitch = -90.0 * _smoothstep((t - 0.10) / (land_t - 0.10))
            roll = 18.0 * math.sin(t * math.pi * 3.0) * (1.0 - land_u)
            bz = -21.0 * _smoothstep((t - 0.58) / 0.16) + 2.2 * math.sin(land_u * math.pi) * (1.0 - land_u * 0.5)
            la_abd = 82.0 * (1.0 - 0.35 * land_u)
            ra_abd = 86.0 * (1.0 - 0.30 * land_u)
            la_p = -20.0 + 35.0 * math.sin(t * 14.0) * (1.0 - land_u)
            ra_p = -10.0 - 35.0 * math.sin(t * 14.0) * (1.0 - land_u)
            ll_k = 28.0 * (1.0 - 0.5 * land_u)
            rl_k = 42.0 * (1.0 - 0.6 * land_u)
            sp_p = -18.0 * (1.0 - land_u)
            hp = -32.0 * (1.0 - 0.7 * land_u)
        elif variant == "b":
            pitch = -55.0 * _smoothstep((t - 0.08) / 0.25) - 35.0 * _smoothstep(land_u)
            roll = 78.0 * _smoothstep((t - 0.48) / 0.35)
            bz = -21.5 * _smoothstep((t - 0.60) / 0.16) + 1.8 * math.sin(land_u * math.pi)
            la_abd = 62.0
            ra_abd = 70.0
            la_p = 45.0 * math.sin(t * 18.0) * (1.0 - land_u)
            ra_p = -45.0 * math.sin(t * 18.0) * (1.0 - land_u)
            ll_k = 65.0 - 35.0 * land_u
            rl_k = 55.0 - 20.0 * land_u
            sp_p = 20.0 * (1.0 - land_u)
            hp = -22.0 + 18.0 * land_u
        else:
            pitch = 88.0 * _smoothstep((t - 0.12) / (land_t - 0.12))
            roll = 360.0 * spin_u
            bz = -20.5 * _smoothstep((t - 0.56) / 0.16) + 2.0 * math.sin(land_u * math.pi)
            la_abd = 75.0 - 30.0 * land_u
            ra_abd = 88.0 - 20.0 * land_u
            la_p = 115.0 * land_u + 30.0 * (1.0 - land_u)
            ra_p = -20.0 * (1.0 - land_u) + 25.0 * land_u
            ll_k = 22.0 * (1.0 - 0.5 * land_u)
            rl_k = 30.0 * (1.0 - 0.6 * land_u)
            sp_p = 12.0 * (1.0 - land_u)
            hp = 15.0 * land_u - 25.0 * (1.0 - land_u)

        p = _base_pose(
            spine_pitch=sp_p,
            head_pitch=hp,
            head_yaw=18.0 * math.sin(t * 10.0) * (1.0 - land_u),
            la_pitch=la_p, la_abd=la_abd, la_elbow=30.0 - 10.0 * land_u,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_elbow=28.0 - 10.0 * land_u,
            ll_pitch=16.0 * (1.0 - land_u), ll_abd=14.0, ll_knee=ll_k,
            rl_pitch=-14.0 * (1.0 - land_u), rl_abd=14.0, rl_knee=rl_k,
            body_yaw=yaw, body_pitch=pitch, body_roll=roll,
            body_z=bz,
            floor_clamp=1.0 if t > 0.52 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.10),
        )
        frames.append(rig.pose(p))

        # World trajectory simulation for HTML viewer (parabolic arc + short skid)
        wx = -qc_vel["back"] * 0.45 * min(t, land_t + 0.15)
        arc = math.sin(min(1.0, t / land_t) * math.pi) if t < land_t else 0.0
        wz = (qc_vel["up"] * 0.16) * arc
        traj.append({"x": round(wx, 2), "y": 0.0, "z": round(wz, 2)})

    return {
        "id": f"ko_spin_{variant}",
        "cat": "ko_spin",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "qc": qc_vel,
    }


def _gen_gut_slide(rig, variant):
    """Category 2: Gut hit -> arms & legs fold up -> flies across map & slides."""
    if variant == "a":
        n = 28
        title = "Var A · Gut-Fold Rocket Slide"
        desc = "Sharp gut-punch jackknife folds arms over stomach and tucks knees up, rockets backward across the map, and skids flat on his back."
        dist_x = -210.0
        arc_z = 36.0
        qc_vel = {"back": 620.0, "up": 195.0, "slide_friction": 0.965}
    elif variant == "b":
        n = 28
        title = "Var B · Cannonball Arc & Roll-Skid"
        desc = "Tight cannonball curl on impact launches him in a higher ballistic arc across the room before bouncing once into a sideways hip-skid."
        dist_x = -245.0
        arc_z = 54.0
        qc_vel = {"back": 700.0, "up": 250.0, "slide_friction": 0.97}
    else:
        n = 26
        title = "Var C · Low-Skim Belly Slide"
        desc = "Sudden doubled-over stomach recoil sends him skimming inches above the floor at high speed before dragging to a halt face-down."
        dist_x = -225.0
        arc_z = 18.0
        qc_vel = {"back": 680.0, "up": 135.0, "slide_friction": 0.972}

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.10)
        fold_in = _smoothstep(t / 0.20)
        unfold = _smoothstep((t - 0.56) / 0.24)
        fold = fold_in * (1.0 - 0.85 * unfold)

        if variant == "a":
            pitch = -88.0 * _smoothstep((t - 0.22) / 0.42)
            roll = 8.0 * math.sin(t * 7.0) * (1.0 - unfold)
            bz = -21.5 * _smoothstep((t - 0.48) / 0.18)
            sp_p = 56.0 * fold - 8.0 * unfold
            la_p = 65.0 * fold - 12.0 * unfold
            ra_p = 65.0 * fold - 8.0 * unfold
            la_abd = -18.0 * fold + 48.0 * unfold
            ra_abd = -18.0 * fold + 42.0 * unfold
            el = 115.0 * fold + 18.0 * (1.0 - fold)
            ll_p = 88.0 * fold + 4.0 * unfold
            rl_p = 78.0 * fold - 4.0 * unfold
            kn = 105.0 * fold + 10.0 * unfold
        elif variant == "b":
            pitch = -86.0 * _smoothstep((t - 0.18) / 0.45)
            roll = 72.0 * _smoothstep((t - 0.52) / 0.34)
            bz = -21.0 * _smoothstep((t - 0.50) / 0.18) + 2.5 * math.sin(max(0.0, (t - 0.55) / 0.22) * math.pi) * (1.0 if 0.55 <= t <= 0.77 else 0.0)
            sp_p = 64.0 * fold
            la_p = 74.0 * fold + 24.0 * unfold
            ra_p = 74.0 * fold + 20.0 * unfold
            la_abd = -22.0 * fold + 36.0 * unfold
            ra_abd = -22.0 * fold + 36.0 * unfold
            el = 128.0 * fold + 25.0 * (1.0 - fold)
            ll_p = 96.0 * fold + 12.0 * unfold
            rl_p = 92.0 * fold + 4.0 * unfold
            kn = 118.0 * fold + 22.0 * unfold
        else:
            # Low skim -> twists face-down on slide
            pitch = 88.0 * _smoothstep((t - 0.26) / 0.38)
            roll = 18.0 * _smoothstep((t - 0.50) / 0.35)
            bz = -21.2 * _smoothstep((t - 0.44) / 0.18)
            sp_p = 52.0 * fold
            la_p = 60.0 * fold + 95.0 * unfold
            ra_p = 60.0 * fold + 85.0 * unfold
            la_abd = -16.0 * fold + 26.0 * unfold
            ra_abd = -16.0 * fold + 26.0 * unfold
            el = 110.0 * fold + 35.0 * unfold
            ll_p = 82.0 * fold - 8.0 * unfold
            rl_p = 76.0 * fold - 12.0 * unfold
            kn = 98.0 * fold + 16.0 * unfold

        p = _base_pose(
            spine_pitch=sp_p,
            head_pitch=38.0 * fold - 14.0 * unfold,
            la_pitch=la_p, la_abd=la_abd, la_twist=45.0 * fold, la_elbow=el,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_twist=45.0 * fold, ra_elbow=el,
            ll_pitch=ll_p, ll_abd=10.0, ll_knee=kn,
            rl_pitch=rl_p, rl_abd=10.0, rl_knee=kn,
            body_pitch=pitch, body_roll=roll, body_z=bz,
            floor_clamp=1.0 if t > 0.46 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.08),
        )
        frames.append(rig.pose(p))

        # World trajectory: brief recoil (0..0.18), fast flight (0.18..0.58), long slide (0.58..1.0)
        if t < 0.16:
            wx = -6.0 * (t / 0.16)
            wz = 0.0
        elif t < 0.58:
            u = (t - 0.16) / 0.42
            wx = -6.0 + (dist_x * 0.58) * u
            wz = arc_z * math.sin(u * math.pi)
        else:
            u = (t - 0.58) / 0.42
            wx = -6.0 + dist_x * (0.58 + 0.42 * _ease_out(u))
            wz = 0.0
        traj.append({"x": round(wx, 2), "y": 0.0, "z": round(wz, 2)})

    return {
        "id": f"gut_slide_{variant}",
        "cat": "gut_slide",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "qc": qc_vel,
    }


def _gen_limbs_off(rig, variant):
    """Category 3: Legs and arms blow off (stump torso + 4 classic flying limb gibs)."""
    if variant == "a":
        n = 22
        title = "Var A · Quad-Burst Nugget Plop"
        desc = "All four limbs detonate outward in classic gib chunks while the stunned torso pops up, pitches forward, and thuds onto the floor."
        arm_t, leg_t = 0.08, 0.08
    elif variant == "b":
        n = 24
        title = "Var B · Staggered Rip & Bounce"
        desc = "Arms shear off first on impact, then legs blow away a beat later—dropping the spinning torso nugget onto its pelvis stump."
        arm_t, leg_t = 0.06, 0.24
    else:
        n = 24
        title = "Var C · Nugget Back-Flip Launch"
        desc = "Explosive blast shears off every limb while punting the limbless torso+head into a stunned half-backflip onto its back."
        arm_t, leg_t = 0.06, 0.06

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.07)
        d_arms = 1.0 if t >= arm_t else 0.0
        d_legs = 1.0 if t >= leg_t else 0.0

        if variant == "a":
            drop_u = _smoothstep((t - 0.14) / 0.48)
            settle = _smoothstep((t - 0.62) / 0.30)
            pitch = 86.0 * drop_u
            roll = 18.0 * settle
            bz = -21.0 * _smoothstep((t - 0.14) / 0.44) + 3.5 * math.sin(min(1.0, t / 0.32) * math.pi)
            hp = -22.0 * (1.0 - drop_u) + 32.0 * drop_u
            byaw = 14.0 * settle
        elif variant == "b":
            drop_u = _smoothstep((t - 0.26) / 0.44)
            pitch = -78.0 * drop_u
            roll = -24.0 * _smoothstep((t - 0.50) / 0.40)
            bz = -20.5 * _smoothstep((t - 0.22) / 0.42)
            byaw = 145.0 * _ease_out(min(1.0, max(0.0, (t - 0.10) / 0.60)))
            hp = -25.0 * (1.0 - drop_u) - 12.0 * drop_u
        else:
            flip_u = _smoothstep((t - 0.08) / 0.64)
            pitch = -265.0 * flip_u
            roll = 12.0 * flip_u
            bz = -21.0 * _smoothstep((t - 0.48) / 0.24) + 12.0 * math.sin(min(1.0, t / 0.56) * math.pi)
            byaw = 22.0 * flip_u
            hp = -18.0

        p = _base_pose(
            spine_pitch=10.0 * (1.0 - min(1.0, t * 2.0)),
            head_pitch=hp, head_yaw=15.0 * math.sin(t * 9.0) * (1.0 - min(1.0, t * 1.4)),
            la_pitch=15.0, la_abd=52.0, ra_pitch=-10.0, ra_abd=52.0,
            ll_pitch=18.0, ll_knee=22.0, rl_pitch=-15.0, rl_knee=26.0,
            body_yaw=byaw, body_pitch=pitch, body_roll=roll, body_z=bz,
            detach_arms=d_arms, detach_legs=d_legs,
            floor_clamp=1.0 if t > 0.25 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.07),
        )
        frames.append(rig.pose(p))
        traj.append({"x": 0.0, "y": 0.0, "z": 0.0})

    gibs = [
        {"part": "l_arm", "start_t": arm_t, "pos": [-2.0, 9.0, 12.0], "vel": [40.0, 130.0, 195.0], "avel": [420, -260, 310]},
        {"part": "r_arm", "start_t": arm_t, "pos": [-2.0, -9.0, 12.0], "vel": [-35.0, -140.0, 210.0], "avel": [-380, 310, -290]},
        {"part": "l_leg", "start_t": leg_t, "pos": [1.0, 4.5, -10.0], "vel": [110.0, 85.0, 165.0], "avel": [340, 410, -180]},
        {"part": "r_leg", "start_t": leg_t, "pos": [-2.0, -4.5, -10.0], "vel": [-105.0, -75.0, 175.0], "avel": [-360, -340, 220]},
    ]
    return {
        "id": f"limbs_off_{variant}",
        "cat": "limbs_off",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": gibs,
        "qc": {"back": 60.0, "up": 120.0, "slide_friction": 0.85, "gib_mode": "limbs"},
    }


def _gen_head_off(rig, variant):
    """Category 4: Head blows off and he falls down."""
    if variant == "a":
        n = 24
        title = "Var A · Clean Pop & Timber Back"
        desc = "Head rockets skyward spinning in a blood geyser while his headless body freezes for a beat, arms jittering, then timbers stiffly backward."
    elif variant == "b":
        n = 26
        title = "Var B · Blind Sway & Knee Faceplant"
        desc = "Head blasts off sideways; headless torso sways blindly reaching toward its missing skull before dropping to its knees and faceplanting."
    else:
        n = 22
        title = "Var C · Cut-Strings Instant Crumple"
        desc = "Head explodes straight up and his body immediately loses all tension, folding down like a marionette with cut strings."

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.06)
        d_head = 1.0 if t >= 0.05 else 0.0

        if variant == "a":
            fall_u = _smoothstep((t - 0.24) / 0.56)
            bounce = math.sin(max(0.0, (t - 0.78) / 0.22) * math.pi) * (1.0 if t > 0.78 else 0.0)
            pitch = -90.0 * fall_u
            bz = -22.0 * _smoothstep((t - 0.30) / 0.50) + 1.5 * bounce
            la_p = 42.0 * math.sin(min(1.0, t / 0.30) * math.pi * 0.5) * (1.0 - fall_u) - 10.0 * fall_u
            ra_p = 38.0 * math.sin(min(1.0, t / 0.30) * math.pi * 0.5) * (1.0 - fall_u) - 14.0 * fall_u
            la_abd = 20.0 + 42.0 * fall_u
            ra_abd = 20.0 + 46.0 * fall_u
            el = 65.0 * (1.0 - 0.72 * fall_u)
            ll_k = 14.0 + 16.0 * math.sin(fall_u * math.pi)
            rl_k = 18.0 + 18.0 * math.sin(fall_u * math.pi)
            sp_p = -8.0 * (1.0 - fall_u)
            sp_r = 0.0
            sp_y = 0.0
            ll_p, rl_p = 6.0, -6.0
        elif variant == "b":
            sway = math.sin(min(1.0, t / 0.38) * math.pi * 2.0) * (1.0 - _smoothstep((t - 0.32) / 0.14))
            kneel_u = _smoothstep((t - 0.30) / 0.28)
            face_u = _smoothstep((t - 0.55) / 0.32)
            pitch = 88.0 * face_u
            bz = -10.5 * kneel_u - 11.5 * face_u
            sp_p = 18.0 * kneel_u - 10.0 * face_u
            sp_r = 14.0 * sway
            sp_y = 12.0 * sway
            la_p = 78.0 * (1.0 - 0.5 * face_u)
            ra_p = 84.0 * (1.0 - 0.5 * face_u)
            la_abd = 8.0 + 32.0 * face_u
            ra_abd = 8.0 + 28.0 * face_u
            el = 96.0 * (1.0 - 0.6 * face_u)
            ll_k = 105.0 * kneel_u * (1.0 - 0.7 * face_u) + 15.0
            rl_k = 105.0 * kneel_u * (1.0 - 0.7 * face_u) + 15.0
            ll_p = 45.0 * kneel_u * (1.0 - face_u)
            rl_p = 40.0 * kneel_u * (1.0 - face_u)
        else:
            crumple = _smoothstep((t - 0.08) / 0.56)
            slump = _smoothstep((t - 0.54) / 0.38)
            pitch = 58.0 * slump
            bz = -17.0 * crumple - 4.0 * slump
            sp_p = 48.0 * crumple - 25.0 * slump
            sp_r = 14.0 * slump
            sp_y = -18.0 * slump
            la_p = 35.0 * crumple + 25.0 * slump
            ra_p = 28.0 * crumple + 30.0 * slump
            la_abd = 28.0 + 24.0 * slump
            ra_abd = 28.0 + 20.0 * slump
            el = 55.0 * crumple + 20.0
            ll_p = 74.0 * crumple - 30.0 * slump
            rl_p = 68.0 * crumple - 24.0 * slump
            ll_k = 115.0 * crumple - 45.0 * slump
            rl_k = 108.0 * crumple - 40.0 * slump

        p = _base_pose(
            spine_pitch=sp_p, spine_roll=sp_r, spine_yaw=sp_y,
            la_pitch=la_p, la_abd=la_abd, la_elbow=el,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_elbow=el,
            ll_pitch=ll_p, ll_abd=10.0, ll_knee=ll_k,
            rl_pitch=rl_p, rl_abd=10.0, rl_knee=rl_k,
            body_pitch=pitch, body_z=bz,
            detach_head=d_head,
            floor_clamp=1.0 if t > 0.18 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.06),
        )
        frames.append(rig.pose(p))
        traj.append({"x": 0.0, "y": 0.0, "z": 0.0})

    if variant == "a":
        h_vel = [35.0, 18.0, 265.0]
    elif variant == "b":
        h_vel = [45.0, 115.0, 215.0]
    else:
        h_vel = [-25.0, -20.0, 290.0]

    gibs = [
        {"part": "head", "start_t": 0.05, "pos": [0.0, 0.0, 22.0], "vel": h_vel, "avel": [520, -390, 260]},
    ]
    return {
        "id": f"head_off_{variant}",
        "cat": "head_off",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": gibs,
        "qc": {"back": 40.0, "up": 80.0, "slide_friction": 0.85, "gib_mode": "head"},
    }


def _gen_backflip(rig, variant):
    """Category 5 (AI Pick #1): Wild Backflip Ragdoll Pancake."""
    if variant == "a":
        n = 26
        title = "Var A · 1.5x Starfish Backflip Splat"
        desc = "Blasted high backward into a wide starfish 1.5x backflip before slamming belly/face-first flat onto the ground."
        flip_deg = -450.0  # -90 is back, -270 is face-down? Wait: +rot_y pitches +X down toward -Z (face down = +90). -270 = +90 mod 360!
        # Let's check: -rot_y tilts +X UP toward +Z -> backflip goes 0 -> -90 (on back) -> -180 (upside down) -> -270 (face down!).
        # 1.5x backflip = -630 deg? No: 1.5 flip = 540 deg (starts upright facing +X, ends upside down facing -X). Wait: -270 = 0.75 flip (face down); -630 = 1.75 flip (1.5+ backflip landing face down!).
        flip_deg = -630.0
    elif variant == "b":
        n = 26
        title = "Var B · Tucked Gainer Belly-Flop"
        desc = "Snappy tucked gainer backflip opens up wide right above the ground into a dramatic belly-flop splat and short skid."
        flip_deg = -450.0  # -450 = 1.25 backflip? Wait: -270 is face down, -450 is back down! Let's use -630 or +90?
        # Wait: +90 is face down. -270 is face down (0.75 turn). -630 is face down (1.75 turns).
        # Let's make Var B 1.25 forward-gainer OR -270 + 180 yaw = face down! Actually -270 (-0.75) vs -630 (-1.75) vs -450 (-1.25 back-down)!
        # Let's use -630 for A & C (face-down pancake!) and -270 for fast single whip-backflip? Better: -630 for A, -450 + roll 180 for B (lands face-down via twist!), -630 for C!
        flip_deg = -450.0
    else:
        n = 26
        title = "Var C · Loose Whip-Ragdoll Flip"
        desc = "Chest snaps back first while legs trail like a ragdoll whip through a 1.75x backflip, slamming face-first with boots rebounding up."
        flip_deg = -630.0

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.08)
        land_t = 0.74
        flip_u = _smoothstep(min(1.0, t / land_t))
        land_u = max(0.0, (t - land_t) / (1.0 - land_t))

        pitch = flip_deg * flip_u
        if variant == "b":
            # Twist 180 mid-air so -450 ends face-down too!
            roll = 180.0 * _smoothstep((t - 0.35) / 0.35)
        else:
            roll = 10.0 * math.sin(t * 8.0) * (1.0 - land_u)

        bz = -21.0 * _smoothstep((t - 0.62) / 0.14) + 2.6 * math.sin(land_u * math.pi) * (1.0 if t > land_t else 0.0)

        if variant == "a":
            splay = _smoothstep(t / 0.25) * (1.0 - 0.25 * land_u)
            la_abd = 15.0 + 78.0 * splay
            ra_abd = 15.0 + 78.0 * splay
            la_p = 20.0 + 18.0 * land_u
            ra_p = 20.0 + 14.0 * land_u
            ll_k = 20.0 + 25.0 * math.sin(min(1.0, t / land_t) * math.pi) - 12.0 * land_u
            rl_k = 20.0 + 25.0 * math.sin(min(1.0, t / land_t) * math.pi) - 12.0 * land_u
            sp_p = -18.0 * math.sin(min(1.0, t / land_t) * math.pi)
        elif variant == "b":
            tuck = math.sin(min(1.0, (t - 0.06) / 0.50) * math.pi) if 0.06 < t < 0.56 else 0.0
            open_w = _smoothstep((t - 0.48) / 0.22)
            la_abd = 20.0 + 70.0 * open_w
            ra_abd = 20.0 + 70.0 * open_w
            la_p = 65.0 * tuck + 40.0 * open_w
            ra_p = 65.0 * tuck + 40.0 * open_w
            ll_k = 105.0 * tuck + 12.0 * open_w
            rl_k = 100.0 * tuck + 12.0 * open_w
            sp_p = 45.0 * tuck - 10.0 * open_w
        else:
            # Whip lag: legs kick up on impact
            rebound = math.sin(land_u * math.pi) if t > land_t else 0.0
            la_abd = 60.0
            ra_abd = 68.0
            la_p = -30.0 * (1.0 - land_u) + 70.0 * land_u
            ra_p = -25.0 * (1.0 - land_u) + 55.0 * land_u
            ll_k = 18.0 + 68.0 * rebound
            rl_k = 22.0 + 58.0 * rebound
            sp_p = -28.0 * (1.0 - land_u)

        p = _base_pose(
            spine_pitch=sp_p,
            head_pitch=-25.0 * (1.0 - land_u) + 15.0 * land_u,
            la_pitch=la_p, la_abd=la_abd, la_elbow=22.0,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_elbow=22.0,
            ll_pitch=14.0 * (1.0 - land_u), ll_abd=16.0, ll_knee=ll_k,
            rl_pitch=-10.0 * (1.0 - land_u), rl_abd=16.0, rl_knee=rl_k,
            body_pitch=pitch, body_roll=roll, body_z=bz,
            floor_clamp=1.0 if t > 0.62 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.08),
        )
        frames.append(rig.pose(p))

        arc = math.sin(min(1.0, t / land_t) * math.pi) if t < land_t else 0.0
        wx = -85.0 * min(t, land_t + 0.12)
        wz = 62.0 * arc
        traj.append({"x": round(wx, 2), "y": 0.0, "z": round(wz, 2)})

    return {
        "id": f"backflip_{variant}",
        "cat": "backflip",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "qc": {"back": 240.0, "up": 340.0, "slide_friction": 0.88},
    }


def _gen_spasm(rig, variant):
    """Category 6 (AI Pick #2): Violent Jitter-Spasm Collapse."""
    if variant == "a":
        n = 28
        title = "Var A · High-Voltage Arc Crumple"
        desc = "Rapid chest-arched shock convulsions jerk arms, shoulders, and knees for 0.7s before power cuts out and he drops limp into a heap."
    elif variant == "b":
        n = 28
        title = "Var B · Wild Side-Twist Seizure"
        desc = "Violent left/right alternating torso twists and flailing elbows whip him 90 degrees before collapsing sideways onto his shoulder."
    else:
        n = 26
        title = "Var C · Rigid Back-Arch Plank Drop"
        desc = "Stiff-legged backward seizure shakes violently with head thrown back, then locks rigid and slams straight backward like a plank."

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.06)
        cut_t = 0.56
        spasm_env = (1.0 - _smoothstep((t - cut_t + 0.08) / 0.10)) * _smoothstep(t / 0.08)
        drop_u = _smoothstep((t - cut_t) / (1.0 - cut_t))

        # High-frequency alternating convulsions
        osc1 = math.sin(i * 2.5)
        osc2 = math.cos(i * 2.9)

        if variant == "a":
            sp_p = -18.0 * spasm_env + 10.0 * osc1 * spasm_env + 32.0 * drop_u
            sp_r = 16.0 * osc2 * spasm_env
            sp_y = 22.0 * osc1 * spasm_env
            hp = -28.0 * spasm_env + 16.0 * osc2 * spasm_env + 22.0 * drop_u
            hy = 28.0 * osc1 * spasm_env
            la_p = 45.0 * spasm_env + 24.0 * osc1 * spasm_env + 25.0 * drop_u
            ra_p = 45.0 * spasm_env - 24.0 * osc1 * spasm_env + 20.0 * drop_u
            la_abd = 38.0 * spasm_env + 18.0 * osc2 * spasm_env + 22.0 * drop_u
            ra_abd = 38.0 * spasm_env - 18.0 * osc2 * spasm_env + 26.0 * drop_u
            el = 92.0 * spasm_env + 35.0 * (1.0 - drop_u)
            ll_p = 20.0 * spasm_env + 68.0 * drop_u
            rl_p = 15.0 * spasm_env + 52.0 * drop_u
            ll_k = 28.0 + 18.0 * abs(osc1) * spasm_env + 76.0 * drop_u
            rl_k = 28.0 + 18.0 * abs(osc2) * spasm_env + 66.0 * drop_u
            pitch = 72.0 * _smoothstep((t - 0.68) / 0.28)
            roll = 16.0 * drop_u
            byaw = 0.0
            bz = -21.0 * drop_u
        elif variant == "b":
            sp_p = 12.0 * abs(osc1) * spasm_env
            sp_r = 26.0 * osc1 * spasm_env
            sp_y = 40.0 * osc2 * spasm_env
            hp = -16.0 * spasm_env + 20.0 * osc1 * spasm_env
            hy = -34.0 * osc2 * spasm_env
            la_p = 65.0 * osc1 * spasm_env + 30.0 * drop_u
            ra_p = -65.0 * osc1 * spasm_env + 20.0 * drop_u
            la_abd = 55.0 * spasm_env + 25.0 * drop_u
            ra_abd = 55.0 * spasm_env + 30.0 * drop_u
            el = 65.0 + 30.0 * osc2 * spasm_env
            ll_p = 12.0 * osc1 * spasm_env + 22.0 * drop_u
            rl_p = -12.0 * osc1 * spasm_env - 10.0 * drop_u
            ll_k = 25.0 + 22.0 * abs(osc2) * spasm_env + 25.0 * drop_u
            rl_k = 25.0 + 22.0 * abs(osc1) * spasm_env + 35.0 * drop_u
            pitch = 10.0 * drop_u
            roll = 88.0 * _smoothstep((t - 0.58) / 0.34)
            byaw = 85.0 * drop_u
            bz = -21.0 * _smoothstep((t - 0.56) / 0.36)
        else:
            sp_p = -28.0 * spasm_env + 8.0 * osc1 * spasm_env
            sp_r = 12.0 * osc2 * spasm_env
            sp_y = 14.0 * osc1 * spasm_env
            hp = -42.0 * spasm_env + 12.0 * osc2 * spasm_env
            hy = 18.0 * osc1 * spasm_env
            la_p = -15.0 * spasm_env + 25.0 * osc1 * spasm_env + 15.0 * drop_u
            ra_p = -15.0 * spasm_env - 25.0 * osc1 * spasm_env + 10.0 * drop_u
            la_abd = 44.0 + 18.0 * osc2 * spasm_env
            ra_abd = 44.0 - 18.0 * osc2 * spasm_env
            el = 38.0 + 22.0 * abs(osc1) * spasm_env
            ll_p = 4.0
            rl_p = -4.0
            ll_k = 8.0 + 14.0 * math.sin(max(0.0, (t - 0.80) / 0.20) * math.pi)
            rl_k = 8.0 + 14.0 * math.sin(max(0.0, (t - 0.80) / 0.20) * math.pi)
            pitch = -90.0 * _smoothstep((t - 0.58) / 0.30)
            roll = 0.0
            byaw = 0.0
            bz = -22.0 * _smoothstep((t - 0.58) / 0.30)

        p = _base_pose(
            spine_pitch=sp_p, spine_roll=sp_r, spine_yaw=sp_y,
            head_pitch=hp, head_yaw=hy,
            la_pitch=la_p, la_abd=la_abd, la_elbow=el,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_elbow=el,
            ll_pitch=ll_p, ll_abd=12.0, ll_knee=ll_k,
            rl_pitch=rl_p, rl_abd=12.0, rl_knee=rl_k,
            body_yaw=byaw, body_pitch=pitch, body_roll=roll, body_z=bz,
            floor_clamp=1.0 if t > 0.54 else 0.0,
            blend_stand=blend_stand,
            weapon_scale=max(0.0, 1.0 - t / 0.06),
        )
        frames.append(rig.pose(p))
        traj.append({"x": 0.0, "y": 0.0, "z": 0.0})

    return {
        "id": f"spasm_{variant}",
        "cat": "spasm",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "qc": {"back": 30.0, "up": 40.0, "slide_friction": 0.85},
    }


CATEGORIES = [
    {
        "cat": "ko_spin",
        "label": "1 · KO Air Spin",
        "badge": "REQUESTED",
        "summary": "Goes spinning in the air as if knocked out really hard, then falls to the ground.",
        "gen": _gen_ko_spin,
    },
    {
        "cat": "gut_slide",
        "label": "2 · Gut-Fold Fly & Slide",
        "badge": "REQUESTED",
        "summary": "Gets pushed back with arms & legs folded up like a stomach hit, flies across the map, and slides.",
        "gen": _gen_gut_slide,
    },
    {
        "cat": "limbs_off",
        "label": "3 · Limbs Blow Off",
        "badge": "REQUESTED",
        "summary": "Both arms and both legs blow off as classic-skinned gibs while the stump torso drops.",
        "gen": _gen_limbs_off,
    },
    {
        "cat": "head_off",
        "label": "4 · Head Blows Off",
        "badge": "REQUESTED",
        "summary": "Head rockets off with blood spray while the headless classic Ranger collapses.",
        "gen": _gen_head_off,
    },
    {
        "cat": "backflip",
        "label": "5 · Wild Backflip Pancake",
        "badge": "AI PICK #1",
        "summary": "Blasted upward into a loose ragdoll backflip and slams face-first onto the floor.",
        "gen": _gen_backflip,
    },
    {
        "cat": "spasm",
        "label": "6 · Violent Jitter-Spasm",
        "badge": "AI PICK #2",
        "summary": "High-voltage shock convulsions shake every limb before dropping limp into a heap.",
        "gen": _gen_spasm,
    },
]


def _clamp_to_mdl_box(verts, scale, trans):
    """Ensure every vertex fits strictly inside player_id1.mdl's quantization box."""
    lo = [trans[k] + 0.05 for k in range(3)]
    hi = [trans[k] + 255.0 * scale[k] - 0.05 for k in range(3)]
    return [
        tuple(max(lo[k], min(hi[k], p[k])) for k in range(3))
        for p in verts
    ]


def _quantize_roundtrip(verts_list, scale, trans):
    q_frames = []
    for fr in verts_list:
        q = []
        for p in fr:
            qp = tuple(
                round(max(0, min(255, round((p[k] - trans[k]) / scale[k]))) * scale[k] + trans[k], 3)
                for k in range(3)
            )
            q.append(qp)
        q_frames.append(q)
    return q_frames


def generate_all_candidates(mdl_info, rig):
    all_anims = []
    for cat_info in CATEGORIES:
        for var in ("a", "b", "c"):
            anim = cat_info["gen"](rig, var)
            anim["cat_label"] = cat_info["label"]
            anim["badge"] = cat_info["badge"]
            # Clamp & quantize roundtrip so HTML preview shows exact in-game MDL vertices
            clamped = [_clamp_to_mdl_box(fr, mdl_info["scale"], mdl_info["trans"]) for fr in anim["frames"]]
            anim["frames"] = _quantize_roundtrip(clamped, mdl_info["scale"], mdl_info["trans"])
            all_anims.append(anim)
    return all_anims


# ---------------------------------------------------------------------------
# Diagnostic PNG Check
# ---------------------------------------------------------------------------

def render_diagnostic_png(mdl_info, all_anims, picks, out_path=OUT_PNG_CHECK):
    tris = mdl_info["tris"]
    selected = [a for a in all_anims if a["id"] in set(picks.values())]
    cols = 4
    rows = len(selected)
    cw, ch = 260, 220
    im = Image.new("RGB", (cols * cw, rows * ch), (14, 18, 28))
    dr = ImageDraw.Draw(im)

    yr = math.radians(-125.0)
    pr = math.radians(14.0)
    cyw, syw = math.cos(yr), math.sin(yr)
    cpt, spt = math.cos(pr), math.sin(pr)

    for r_idx, anim in enumerate(selected):
        nf = len(anim["frames"])
        sample_idxs = [0, nf // 3, (2 * nf) // 3, nf - 1]
        for c_idx, fi in enumerate(sample_idxs):
            ox = c_idx * cw + cw // 2
            oy = r_idx * ch + ch // 2 + 16
            sc = 3.2
            verts = anim["frames"][fi]
            proj = []
            for x, y, z in verts:
                rx = x * cyw - y * syw
                ry = x * syw + y * cyw
                px = rx * cpt + z * spt
                pz = -rx * spt + z * cpt
                proj.append((ox + ry * sc, oy - pz * sc, px))
            draw_tris = []
            for _, v0, v1, v2 in tris:
                p0, p1, p2 = verts[v0], verts[v1], verts[v2]
                fn = _vcross(_vsub(p1, p0), _vsub(p2, p0))
                if math.sqrt(fn[0] ** 2 + fn[1] ** 2 + fn[2] ** 2) < 1e-4:
                    continue
                zavg = (proj[v0][2] + proj[v1][2] + proj[v2][2]) / 3.0
                shade = max(0.28, min(1.0, 0.55 + 0.45 * _vnorm(fn)[2]))
                draw_tris.append((zavg, v0, v1, v2, shade))
            draw_tris.sort(key=lambda t: t[0])
            for _, v0, v1, v2, shade in draw_tris:
                col = (int(200 * shade), int(155 * shade), int(115 * shade))
                pts = [(proj[v0][0], proj[v0][1]), (proj[v1][0], proj[v1][1]), (proj[v2][0], proj[v2][1])]
                dr.polygon(pts, fill=col, outline=(32, 38, 52))
            dr.rectangle([c_idx * cw, r_idx * ch, (c_idx + 1) * cw - 1, (r_idx + 1) * ch - 1], outline=(40, 48, 68))
            dr.text((c_idx * cw + 8, r_idx * ch + 6), f"{anim['id']} f{fi}/{nf-1}", fill=(255, 196, 108))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path)
    print(f"Wrote diagnostic sheet: {out_path}")


# ---------------------------------------------------------------------------
# Deterministic Overlay PK3 + Manifest
# ---------------------------------------------------------------------------

def _write_deterministic_pk3(out_pk3, entries):
    """Write reproducible pk3 with 1980-01-01 timestamps and sorted entry names."""
    os.makedirs(os.path.dirname(os.path.abspath(out_pk3)), exist_ok=True)
    with zipfile.ZipFile(out_pk3, "w") as zf:
        for arcname, raw_bytes in sorted(entries, key=lambda e: e[0]):
            zi = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, raw_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def build_player_id1_with_deaths(mdl_info, selected_anims, anorms):
    """Extend 288-frame progs/player_id1.mdl with the 6 selected death animations starting at frame 288."""
    hdr = list(mdl_info["hdr"])
    scale = mdl_info["scale"]
    trans = mdl_info["trans"]
    tris = mdl_info["tris"]

    extra_frames = []
    manifest = {}
    cur_idx = mdl_info["nframes"]  # 288

    for anim in selected_anims:
        start_idx = cur_idx
        short_tag = anim["cat"][:6]
        for fi, verts in enumerate(anim["frames"]):
            fname = f"d_{short_tag}_{fi+1}"
            extra_frames.append(_pack_mdl_frame(fname, verts, tris, scale, trans, anorms))
            cur_idx += 1
        end_idx = cur_idx - 1
        manifest[anim["cat"]] = {
            "id": anim["id"],
            "title": anim["title"],
            "start_frame": start_idx,
            "end_frame": end_idx,
            "num_frames": len(anim["frames"]),
            "fps": anim["fps"],
            "qc": anim["qc"],
        }

    total_frames = mdl_info["nframes"] + len(extra_frames)
    hdr[17] = total_frames
    new_hdr = struct.pack("<4si3f3ff3f8if", *hdr)

    # Original header(84) + skins + verts/tris + original 288 frames are untouched up to frame data end
    skin_len = mdl_info["nskins"] * (4 + mdl_info["sw"] * mdl_info["sh"])
    vt_len = 212 * 12 + 408 * 16
    prefix_end = 84 + skin_len + vt_len
    new_mdl = new_hdr + mdl_info["raw"][84:prefix_end] + b"".join(mdl_info["raw_frames"]) + b"".join(extra_frames)
    return new_mdl, manifest


# ---------------------------------------------------------------------------
# Self-Contained WebGL2 HTML Voting Studio Builder
# ---------------------------------------------------------------------------

def _png_b64(rgb_arr):
    im = Image.fromarray(rgb_arr, mode="RGB")
    bio = io.BytesIO()
    im.save(bio, "PNG", optimize=True)
    return base64.b64encode(bio.getvalue()).decode("ascii")


def _pack_mesh_for_js(tris, st, sw, sh, flip_tri_winding=True):
    """Unroll indexed tris into flat triangle vertex indices + UV floats for WebGL2."""
    # Note: Quake MDL tris are CW when seen from outside; reversing (v0,v2,v1) gives CCW for WebGL front-face.
    tri_idx = []
    for _, v0, v1, v2 in tris:
        if flip_tri_winding:
            tri_idx.extend((v0, v2, v1))
        else:
            tri_idx.extend((v0, v1, v2))
    uv = []
    for onseam, s, t in st:
        u = (s + 0.5) / float(sw)
        v = (t + 0.5) / float(sh)
        uv.extend((round(u, 5), round(v, 5)))
    return tri_idx, uv


def build_voting_html(mdl_info, rig, head_gib, limb_gibs, all_anims, picks, out_html=OUT_HTML):
    if not os.path.isfile(TEMPLATE_HTML):
        raise FileNotFoundError(f"Missing HTML template: {TEMPLATE_HTML}")

    tri_idx, uv = _pack_mesh_for_js(mdl_info["tris"], mdl_info["st"], mdl_info["sw"], mdl_info["sh"])
    head_tri, head_uv = _pack_mesh_for_js(head_gib["tris"], head_gib["st"], head_gib["sw"], head_gib["sh"])

    gibs_js = {
        "head": {
            "tris": head_tri,
            "uv": head_uv,
            "verts": [round(c, 3) for p in head_gib["verts"] for c in p],
            "skin": "data:image/png;base64," + _png_b64(head_gib["skin_rgb"]),
        }
    }
    for pk, g in limb_gibs.items():
        gtri, guv = _pack_mesh_for_js(g["tris"], g["st"], g["sw"], g["sh"])
        gibs_js[pk] = {
            "tris": gtri,
            "uv": guv,
            "verts": [round(c, 3) for p in g["verts"] for c in p],
            "skin": "data:image/png;base64," + _png_b64(g["skin_rgb"]),
        }

    anims_js = []
    for anim in all_anims:
        flat_frames = []
        for fr in anim["frames"]:
            flat_frames.append([round(c, 3) for p in fr for c in p])
        anims_js.append({
            "id": anim["id"],
            "cat": anim["cat"],
            "cat_label": anim["cat_label"],
            "badge": anim["badge"],
            "title": anim["title"],
            "desc": anim["desc"],
            "fps": anim["fps"],
            "frames": flat_frames,
            "traj": anim["traj"],
            "gibs": anim["gibs"],
            "qc": anim["qc"],
        })

    payload = {
        "categories": [
            {"cat": c["cat"], "label": c["label"], "badge": c["badge"], "summary": c["summary"]}
            for c in CATEGORIES
        ],
        "default_picks": picks,
        "player": {
            "nverts": 212,
            "tris": tri_idx,
            "uv": uv,
            "stand1": [round(c, 3) for p in rig.stand1 for c in p],
            "skin": "data:image/png;base64," + _png_b64(mdl_info["skin_rgb"]),
        },
        "gibs": gibs_js,
        "anims": anims_js,
    }

    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(TEMPLATE_HTML, "r", encoding="utf-8").read()
    html = tpl.replace("__PAYLOAD_JSON__", payload_json)
    os.makedirs(os.path.dirname(os.path.abspath(out_html)), exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote voting studio HTML: {out_html} ({os.path.getsize(out_html)} bytes)")


# ---------------------------------------------------------------------------
# CLI Entry
# ---------------------------------------------------------------------------

def resolve_picks(args):
    picks = dict(DEFAULT_PICKS)
    if args.votes and os.path.isfile(args.votes):
        vdata = json.load(open(args.votes, "r", encoding="utf-8"))
        src = vdata.get("picks", vdata)
        for k, v in src.items():
            if k in picks:
                picks[k] = v
    if args.picks:
        for item in args.picks.split(","):
            item = item.strip()
            if not item:
                continue
            for cat_info in CATEGORIES:
                c = cat_info["cat"]
                if item.startswith(c + "_"):
                    picks[c] = item
    return picks


def main():
    import hashlib

    ap = argparse.ArgumentParser(description="Build classic Ranger custom death animations, voting HTML, and zz_player_deaths.pk3.")
    ap.add_argument("--bakersfield-pk3", type=str, default=BAKER_PK3, help="Path to base bakersfield.pk3")
    ap.add_argument("--out-pk3", type=str, default=OUT_PK3, help="Output path for zz_player_deaths.pk3")
    ap.add_argument("--picks", type=str, default="", help="Comma-separated winning anim IDs (e.g. ko_spin_b,gut_slide_a,...)")
    ap.add_argument("--votes", type=str, default="", help="Optional exported votes JSON file from docs/player_death_vote.html")
    ap.add_argument("--render-check", action="store_true", help="Render diagnostic PNG contact sheet")
    ap.add_argument("--skip-html", action="store_true", help="Skip generating docs/player_death_vote.html")
    ap.add_argument("--no-qc", action="store_true", help="Skip writing QC frame constants and manifest (useful in CI)")
    ap.add_argument("--verify-repro", action="store_true", help="Verify two consecutive pk3 writes produce identical sha256")
    args = ap.parse_args()

    picks = resolve_picks(args)
    anorms = _load_anorms()
    mdl_info = load_id1_full(bakersfield_pk3=args.bakersfield_pk3)
    rig = RangerRig(mdl_info, bakersfield_pk3=args.bakersfield_pk3)
    head_gib = load_id1_head_gib()
    limb_gibs = build_classic_limb_gibs(mdl_info, anorms, bakersfield_pk3=args.bakersfield_pk3)
    all_anims = generate_all_candidates(mdl_info, rig)

    if args.render_check:
        render_diagnostic_png(mdl_info, all_anims, picks)

    by_id = {a["id"]: a for a in all_anims}
    selected = [by_id[picks[c["cat"]]] for c in CATEGORIES]

    new_mdl, manifest = build_player_id1_with_deaths(mdl_info, selected, anorms)

    pk3_entries = [
        ("progs/player_id1.mdl", new_mdl),
        ("progs/h_player_id1.mdl", head_gib["raw"]),
    ]
    for g in limb_gibs.values():
        pk3_entries.append((g["path"], g["raw"]))

    _write_deterministic_pk3(args.out_pk3, pk3_entries)
    h1 = hashlib.sha256(open(args.out_pk3, "rb").read()).hexdigest()
    if args.verify_repro:
        _write_deterministic_pk3(args.out_pk3, pk3_entries)
        h2 = hashlib.sha256(open(args.out_pk3, "rb").read()).hexdigest()
        assert h1 == h2, f"Non-deterministic pk3 write: {h1} != {h2}"
    print(f"Wrote deterministic overlay pk3: {args.out_pk3} ({os.path.getsize(args.out_pk3)} bytes, sha256={h1}, frames={mdl_info['nframes'] + sum(len(a['frames']) for a in selected)})")

    if not args.no_qc:
        os.makedirs(os.path.dirname(OUT_MANIFEST), exist_ok=True)
        with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"Wrote manifest: {OUT_MANIFEST}")

        qc_lines = [
            "// Auto-generated by source/mm_tools/build_player_deaths.py -- do not hand-edit.",
            "// Frame ranges inside progs/player_id1.mdl (20 fps, nextthink = time + 0.05).",
            "",
        ]
        for cat, info in manifest.items():
            up = cat.upper()
            qc_lines.append(f"float PD_{up}_START = {info['start_frame']};\t// {info['id']}")
            qc_lines.append(f"float PD_{up}_END = {info['end_frame']};")
            qc_lines.append(f"float PD_{up}_GIB_ARM_F = {info['start_frame'] + max(1, int(round((info['num_frames'] - 1) * (0.08 if info['id'] != 'limbs_off_b' else 0.06))))};")
            qc_lines.append(f"float PD_{up}_GIB_LEG_F = {info['start_frame'] + max(1, int(round((info['num_frames'] - 1) * (0.24 if info['id'] == 'limbs_off_b' else 0.08))))};")
        with open(OUT_QC_FRAMES, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(qc_lines) + "\n")
        print(f"Wrote QC frame constants: {OUT_QC_FRAMES}")

    for cat, info in manifest.items():
        print(f"  {cat:10s} -> {info['id']:14s} frames {info['start_frame']}..{info['end_frame']} ({info['num_frames']}f @ {info['fps']}fps)")

    if not args.skip_html and os.path.isfile(TEMPLATE_HTML):
        build_voting_html(mdl_info, rig, head_gib, limb_gibs, all_anims, picks)


if __name__ == "__main__":
    main()
