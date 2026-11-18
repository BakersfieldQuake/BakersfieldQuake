"""Authentic Seated Quake Ranger Driver Builder for BakersfieldQuake Go-Karts.

Extracts the 1996 Quake Ranger body mesh (149 verts / 294 tris, stripping out
shotgun, axe, and muzzle-flash components) and 296x194 Quake-palette skin from
`bakersfield.pk3:progs/player_id1.mdl` (with fallback to `id1/pak0.pak`),
resolves MDL `onseam` UV splits into clean MD3 UVs, upscales the skin texture
with edge-bleed dilation to `progs/gk_driver.png`, and skins/poses the Ranger
into a distortion-free seated driving posture for any go-kart cockpit.
"""
from collections import defaultdict, deque
import argparse
import base64
import json
import math
import os
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib

REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(REPO_ROOT, "progs")
OUT_DIR = os.path.join(HERE, "out")
BAKER_PK3 = os.path.join(REPO_ROOT, "bakersfield.pk3")
ID1_PAK0 = os.path.abspath(os.path.join(REPO_ROOT, "..", "id1", "pak0.pak"))
# Quake 1.06 progs/player.mdl (sha256 10cecfe0...), committed so CI can build the driver without the paks.
ID1_PLAYER_MDL = os.path.join(HERE, "id1", "player.mdl")

DRIVER_SHADER = "progs/gk_driver"
DRIVER_TEX_REL = "progs/gk_driver.png"
DRIVER_TEX_ABS = os.path.join(PROGS_DIR, "gk_driver.png")

# Exact 768-byte Quake 1 palette (gfx/palette.lmp from id1/pak0.pak) for CI/headless builds.
_QUAKE_PALETTE_B64 = (
    "AAAADw8PHx8fLy8vPz8/S0tLW1tba2tre3t7i4uLm5ubq6uru7u7y8vL29vb6+vrDwsHFw8LHxcL"
    "JxsPLyMTNysXPy8XSzcbUzsbW0MfY0sfa1Mfc1cfe18jg2cjj28jCwsPExMbGxsnJyczLy8/NzdL"
    "Pz9XR0dnT09zW1t/Y2OLa2uXc3Oje3uvg4O7i4vLAAAABwcACwsAExMAGxsAIyMAKysHLy8HNzcH"
    "Pz8HR0cHS0sLU1MLW1sLY2MLa2sPBwAADwAAFwAAHwAAJwAALwAANwAAPwAARwAATwAAVwAAXwAA"
    "ZwAAbwAAdwAAfwAAExMAGxsAIyMALysANy8AQzcASzsHV0MHX0cHa0sLd1MPg1cTi1sTl18bo2Mf"
    "r2cjIxMHLxcLOx8PSyMTVysXYy8fczcjfzsrj0Mzn08zr2Mvv3cvz48r36sn78sf//MbCwcAGxMA"
    "KyMPNysTRzMbUzcjYz8rb0czf1M/i19Hm2tTp3tft4drw5N706OL47OXq4ujn3+Xk3OHi2d7f1tv"
    "d1Nja0tXXz9LVzdDSy83QycvNx8jKxcbIxMTFwsLDwcHu3Ofr2uPo1+Dl1d3i09rf0tfc0NTaztL"
    "XzM/Uys3RyMrOx8jLxcbIxMTFwsLDwcH28O7y7Onv6Obr5eLo4d7l3tvh29fe2NTa1dHX0s7Uz8z"
    "QzMnNysfJx8XGxMPDwsHb4N7Z3tvX3NnV2tfT2NXR1tPP1NHN0s/L0M3KzsvIzMnHysfFyMXDxsT"
    "CxMLBwsH//Mb798X28sTy7cPu6cPq5cLm4MHi3MHe2MHa1MAW0cASzcAOysAKx8AGw8ACwcAAAD/"
    "CwvvExPfGxvPIyO/KyuvLy+fLy+PLy9/Ly9vLy9fKytPIyM/GxsvExMfCwsPKwAAOwAASwcAXwcA"
    "bw8AfxcHkx8HoycLtzMPw0sbz2Mr238745dP56tf779399OLp3s7t5s3x8M35+NXf7//q+f/1/// "
    "ZwAAiwAAswAA1wAA/wAA//OT//fH////n1tT"
).replace(" ", "")


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vlen(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _vnorm(a):
    l = _vlen(a)
    if l < 1e-9:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def _vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _rot_x(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def _rot_y(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def _rot_z(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def _read_pak_entry(pak_path, target_name):
    target_low = target_name.lower()
    with open(pak_path, "rb") as f:
        magic, doff, dsz = struct.unpack("<4sii", f.read(12))
        if magic != b"PACK":
            raise RuntimeError(f"Invalid PAK magic in {pak_path}: {magic!r}")
        f.seek(doff)
        for _ in range(dsz // 64):
            ent = f.read(64)
            nm = ent[:56].split(b"\x00", 1)[0].decode("ascii", "ignore").lower()
            if nm == target_low:
                fpos, fsize = struct.unpack("<ii", ent[56:])
                f.seek(fpos)
                return f.read(fsize)
    raise FileNotFoundError(f"{target_name} not found in {pak_path}")


def _load_player_mdl_bytes(bakersfield_pk3=BAKER_PK3):
    if bakersfield_pk3 and os.path.isfile(bakersfield_pk3):
        with zipfile.ZipFile(bakersfield_pk3, "r") as z:
            if "progs/player_id1.mdl" in z.namelist():
                return z.read("progs/player_id1.mdl")
    if os.path.isfile(ID1_PAK0):
        return _read_pak_entry(ID1_PAK0, "progs/player.mdl")
    with open(ID1_PLAYER_MDL, "rb") as f:
        return f.read()


def _load_quake_palette():
    if os.path.isfile(ID1_PAK0):
        return _read_pak_entry(ID1_PAK0, "gfx/palette.lmp")
    return base64.b64decode(_QUAKE_PALETTE_B64)


def ensure_driver_texture(out_path=DRIVER_TEX_ABS, bakersfield_pk3=BAKER_PK3):
    """Extracts the 296x194 Quake Ranger skin, dilates UV borders to avoid black seams,
    and saves a crisp 592x388 PNG at `progs/gk_driver.png`.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    data = _load_player_mdl_bytes(bakersfield_pk3=bakersfield_pk3)
    pal = _load_quake_palette()

    hdr = struct.unpack("<4si3f3ff3f8if", data[:84])
    sw, sh = hdr[13], hdr[14]
    skin_idx = data[88 : 88 + sw * sh]

    im_p = Image.frombytes("P", (sw, sh), skin_idx)
    im_p.putpalette(pal)
    rgb = np.array(im_p.convert("RGB"), dtype=np.uint8)

    # Dilate non-black skin islands by 2 px into black background so mipmaps/bilinear never bleed black
    mask = (rgb.sum(axis=2) > 12)
    padded = rgb.copy()
    cur_mask = mask.copy()
    for _ in range(2):
        nxt = padded.copy()
        nxt_mask = cur_mask.copy()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            rolled_rgb = np.roll(np.roll(padded, dy, axis=0), dx, axis=1)
            rolled_m = np.roll(np.roll(cur_mask, dy, axis=0), dx, axis=1)
            fill = (~nxt_mask) & rolled_m
            nxt[fill] = rolled_rgb[fill]
            nxt_mask |= fill
        padded = nxt
        cur_mask = nxt_mask

    # Crisp 2x upscale (592x388) preserving iconic Quake pixel grit
    out_im = Image.fromarray(padded, mode="RGB").resize((sw * 2, sh * 2), Image.Resampling.BILINEAR)
    out_im.save(out_path, "PNG", optimize=True)
    return out_path


def _parse_id1_body(bakersfield_pk3=BAKER_PK3):
    """Returns (sw, sh, st, body_tris, frame_verts_fn) for the 149-vert Ranger body."""
    data = _load_player_mdl_bytes(bakersfield_pk3=bakersfield_pk3)
    hdr = struct.unpack("<4si3f3ff3f8if", data[:84])
    scale, trans = hdr[2:5], hdr[5:8]
    nskins, sw, sh, nverts, ntris, nframes = hdr[12:18]
    pos = 84 + nskins * (4 + sw * sh)
    st = [struct.unpack("<3i", data[pos + 12 * i : pos + 12 * i + 12]) for i in range(nverts)]
    pos += 12 * nverts
    tris = [struct.unpack("<4i", data[pos + 16 * i : pos + 16 * i + 16]) for i in range(ntris)]
    pos += 16 * ntris
    frame_len = 4 + 8 + 16 + nverts * 4

    def get_frame(fi):
        fbase = pos + fi * frame_len
        return [
            tuple(
                struct.unpack("<4B", data[fbase + 28 + 4 * vi : fbase + 28 + 4 * vi + 4])[k] * scale[k] + trans[k]
                for k in range(3)
            )
            for vi in range(nverts)
        ]

    # Isolate largest connected component (the 149-vertex Ranger body, excluding axe/gun/flash)
    adj = defaultdict(set)
    for ff, v0, v1, v2 in tris:
        for a, b in ((v0, v1), (v1, v2), (v2, v0)):
            adj[a].add(b)
            adj[b].add(a)
    seen = set()
    comps = []
    for v in range(nverts):
        if v in seen:
            continue
        q = deque([v])
        seen.add(v)
        comp = []
        while q:
            u = q.popleft()
            comp.append(u)
            for w in adj[u]:
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        comps.append(comp)
    body = max(comps, key=len)
    body_set = set(body)
    body_tris = [t for t in tris if t[1] in body_set]
    return sw, sh, st, body, body_tris, get_frame


def _classify_vert(vi, st, sw, sh):
    _, s, t = st[vi]
    uf = s / sw
    if uf >= 0.5:
        uf -= 0.5
    vf = t / sh
    if vf >= 0.58:
        return "l_leg" if uf >= 0.295 else "r_leg", uf, vf
    if vf <= 0.175 and 0.24 < uf < 0.36:
        return "head", uf, vf
    if uf > 0.39 and vf >= 0.16:
        return "l_arm", uf, vf
    if uf < 0.20 and vf >= 0.18:
        return "r_arm", uf, vf
    return "torso", uf, vf


def _avg(pts):
    n = len(pts)
    return (
        sum(p[0] for p in pts) / n,
        sum(p[1] for p in pts) / n,
        sum(p[2] for p in pts) / n,
    )


def _make_seg_frame(p0, p1, fwd_hint):
    """Right-handed orthonormal frame (axis, fwd, lat) along segment p0 -> p1."""
    axis = _vnorm(_vsub(p1, p0))
    # Remove axial component from fwd_hint
    fh = _vsub(fwd_hint, _vmul(axis, _vdot(fwd_hint, axis)))
    if _vlen(fh) < 1e-6:
        fh = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.8 else (0.0, 0.0, 1.0)
        fh = _vsub(fh, _vmul(axis, _vdot(fh, axis)))
    fwd = _vnorm(fh)
    lat = _vnorm(_vcross(axis, fwd))
    return axis, fwd, lat


def _pose_limb_chain(verts_src, v_list, uvs, src_pts, dst_pts, src_fwd_hints, dst_fwd_hints,
                     socket_blend_vmax=None, torso_pos_fn=None):
    """Maps a 3-segment limb (P0->P1->P2->P3) from source pose onto target polyline (T0->T1->T2->T3)
    using smooth joint-bisector plane blending so knees/elbows keep full volume at 90 deg bend.
    """
    # Compute source segment lengths and cumulative distances
    src_segs = [_make_seg_frame(src_pts[i], src_pts[i + 1], src_fwd_hints[i]) for i in range(3)]
    dst_segs = [_make_seg_frame(dst_pts[i], dst_pts[i + 1], dst_fwd_hints[i]) for i in range(3)]
    src_lens = [max(1e-5, _vlen(_vsub(src_pts[i + 1], src_pts[i]))) for i in range(3)]

    # Bisector planes at interior joints (i=1 knee/elbow, i=2 ankle/wrist)
    src_j_frames = []
    dst_j_frames = []
    for j in (1, 2):
        # Average axis, fwd, lat across incoming and outgoing segments
        sa = _vnorm(_vadd(src_segs[j - 1][0], src_segs[j][0]))
        sf = _vnorm(_vadd(src_segs[j - 1][1], src_segs[j][1]))
        sf = _vnorm(_vsub(sf, _vmul(sa, _vdot(sf, sa))))
        sl = _vnorm(_vcross(sa, sf))
        src_j_frames.append((sa, sf, sl))

        da = _vnorm(_vadd(dst_segs[j - 1][0], dst_segs[j][0]))
        df = _vnorm(_vadd(dst_segs[j - 1][1], dst_segs[j][1]))
        df = _vnorm(_vsub(df, _vmul(da, _vdot(df, da))))
        dl = _vnorm(_vcross(da, df))
        dst_j_frames.append((da, df, dl))

    out = {}
    for vi in v_list:
        p = verts_src[vi]
        # Find closest segment along polyline
        best_seg = 0
        best_t = 0.0
        best_d2 = 1e18
        for si in range(3):
            a, b = src_pts[si], src_pts[si + 1]
            ab = _vsub(b, a)
            l2 = max(1e-8, _vdot(ab, ab))
            t = max(0.0, min(1.0, _vdot(_vsub(p, a), ab) / l2))
            proj = _vlerp(a, b, t)
            d = _vsub(p, proj)
            d2 = _vdot(d, d)
            if d2 < best_d2:
                best_d2 = d2
                best_seg = si
                best_t = t

        # Smooth frame interpolation across joints so rings right at knee/elbow use bisector plane!
        si = best_seg
        t = best_t
        if si == 0 and t > 0.65:
            w = (t - 0.65) / 0.35 * 0.5
            sa = _vnorm(_vlerp(src_segs[0][0], src_j_frames[0][0], w * 2.0))
            sf = _vnorm(_vlerp(src_segs[0][1], src_j_frames[0][1], w * 2.0))
            sf = _vnorm(_vsub(sf, _vmul(sa, _vdot(sf, sa))))
            sl = _vnorm(_vcross(sa, sf))

            da = _vnorm(_vlerp(dst_segs[0][0], dst_j_frames[0][0], w * 2.0))
            df = _vnorm(_vlerp(dst_segs[0][1], dst_j_frames[0][1], w * 2.0))
            df = _vnorm(_vsub(df, _vmul(da, _vdot(df, da))))
            dl = _vnorm(_vcross(da, df))
        elif si == 1 and t < 0.35:
            w = (0.35 - t) / 0.35
            sa = _vnorm(_vlerp(src_segs[1][0], src_j_frames[0][0], w))
            sf = _vnorm(_vlerp(src_segs[1][1], src_j_frames[0][1], w))
            sf = _vnorm(_vsub(sf, _vmul(sa, _vdot(sf, sa))))
            sl = _vnorm(_vcross(sa, sf))

            da = _vnorm(_vlerp(dst_segs[1][0], dst_j_frames[0][0], w))
            df = _vnorm(_vlerp(dst_segs[1][1], dst_j_frames[0][1], w))
            df = _vnorm(_vsub(df, _vmul(da, _vdot(df, da))))
            dl = _vnorm(_vcross(da, df))
        elif si == 1 and t > 0.72:
            w = (t - 0.72) / 0.28
            sa = _vnorm(_vlerp(src_segs[1][0], src_j_frames[1][0], w))
            sf = _vnorm(_vlerp(src_segs[1][1], src_j_frames[1][1], w))
            sf = _vnorm(_vsub(sf, _vmul(sa, _vdot(sf, sa))))
            sl = _vnorm(_vcross(sa, sf))

            da = _vnorm(_vlerp(dst_segs[1][0], dst_j_frames[1][0], w))
            df = _vnorm(_vlerp(dst_segs[1][1], dst_j_frames[1][1], w))
            df = _vnorm(_vsub(df, _vmul(da, _vdot(df, da))))
            dl = _vnorm(_vcross(da, df))
        elif si == 2 and t < 0.30:
            w = (0.30 - t) / 0.30
            sa = _vnorm(_vlerp(src_segs[2][0], src_j_frames[1][0], w))
            sf = _vnorm(_vlerp(src_segs[2][1], src_j_frames[1][1], w))
            sf = _vnorm(_vsub(sf, _vmul(sa, _vdot(sf, sa))))
            sl = _vnorm(_vcross(sa, sf))

            da = _vnorm(_vlerp(dst_segs[2][0], dst_j_frames[1][0], w))
            df = _vnorm(_vlerp(dst_segs[2][1], dst_j_frames[1][1], w))
            df = _vnorm(_vsub(df, _vmul(da, _vdot(df, da))))
            dl = _vnorm(_vcross(da, df))
        else:
            sa, sf, sl = src_segs[si]
            da, df, dl = dst_segs[si]

        src_base = _vlerp(src_pts[si], src_pts[si + 1], t)
        delta = _vsub(p, src_base)
        c_ax = _vdot(delta, sa)
        c_fw = _vdot(delta, sf)
        c_lt = _vdot(delta, sl)

        # Preserve volume across bends while scaling segment length proportionally
        dst_len = _vlen(_vsub(dst_pts[si + 1], dst_pts[si]))
        len_ratio = dst_len / src_lens[si]
        rad_scale = 1.0
        dst_base = _vlerp(dst_pts[si], dst_pts[si + 1], t)
        p_limb = _vadd(
            dst_base,
            _vadd(
                _vmul(da, c_ax * len_ratio),
                _vadd(_vmul(df, c_fw * rad_scale), _vmul(dl, c_lt * rad_scale)),
            ),
        )

        # Blend socket vertices smoothly with torso if requested
        if socket_blend_vmax is not None and torso_pos_fn is not None:
            _, vf = uvs[vi]
            if vf < socket_blend_vmax:
                p_torso = torso_pos_fn(vi)
                alpha = max(0.0, min(1.0, (vf - (socket_blend_vmax - 0.08)) / 0.08))
                p_limb = _vlerp(p_torso, p_limb, alpha)

        out[vi] = p_limb
    return out


class DriverMesh:
    """MD3-ready mesh container matching MeshPart/KartMesh API (.verts, .norms, .tris, .st)."""

    def __init__(self, verts, norms, tris, st):
        self.verts = list(verts)
        self.norms = list(norms)
        self.tris = list(tris)
        self.st = list(st)

    def compute_normals(self):
        acc = [[0.0, 0.0, 0.0] for _ in range(len(self.verts))]
        for a, b, c in self.tris:
            pa, pb, pc = self.verts[a], self.verts[b], self.verts[c]
            ab = _vsub(pb, pa)
            ac = _vsub(pc, pa)
            fn = _vcross(ab, ac)
            for idx in (a, b, c):
                acc[idx][0] += fn[0]
                acc[idx][1] += fn[1]
                acc[idx][2] += fn[2]
        self.norms = [_vnorm(tuple(v)) for v in acc]
        return self


def build_seated_driver(
    seat_pos,
    steer_pos,
    foot_pos=(20.0, 6.8, 6.8),
    grip_half_y=6.5,
    torso_recline_deg=5.5,
    scale=1.18,
    head_pitch_deg=4.0,
    bakersfield_pk3=BAKER_PK3,
):
    """Builds the authentic Quake Ranger seated inside a go-kart cockpit.

    Args:
        seat_pos: (x, y, z) or dict{x,y,z} of seat pan center top.
        steer_pos: (x, y, z) or dict{x,y,z} of steering wheel center.
        foot_pos: (x, y_abs, z) target ankle/heel position inside footwells.
        grip_half_y: Half-width of steering wheel hand grip (|Y|).
        torso_recline_deg: Backward torso tilt against seat backrest (+deg leans back).
        scale: Overall Ranger body scale (1.18 gives ~34.5u seated height, ~22u shoulder span).
        head_pitch_deg: Slight downward/forward gaze angle.
        bakersfield_pk3: Path to bakersfield.pk3 containing progs/player_id1.mdl.
    """
    if isinstance(seat_pos, dict):
        seat_pos = (float(seat_pos["x"]), float(seat_pos["y"]), float(seat_pos["z"]))
    if isinstance(steer_pos, dict):
        steer_pos = (float(steer_pos["x"]), float(steer_pos["y"]), float(steer_pos["z"]))

    sw, sh, st, body, body_tris, get_frame = _parse_id1_body(bakersfield_pk3=bakersfield_pk3)
    vs17 = get_frame(17)  # axstnd1: arms free at sides, head straight!

    parts_verts = defaultdict(list)
    uvs = {}
    for vi in body:
        p_name, uf, vf = _classify_vert(vi, st, sw, sh)
        parts_verts[p_name].append(vi)
        uvs[vi] = (uf, vf)

    # 1. Canonicalize torso & head around local pelvis origin (0, 0, 0)
    # In axstnd1, torso X center ~ -4.5, Y center ~ -0.6, Z pelvis bottom ~ -2.2
    # Torso has ~ -8 deg combat yaw; rotate +8 deg around Z so chest faces straight +X.
    torso_origin = (-4.5, -0.6, -2.2)
    head_origin = (-1.6, -0.3, 18.2)
    sx, sy, sz = seat_pos
    pelvis_world = (sx + 2.2, sy, sz + 0.8)

    def xform_torso(vi):
        raw = vs17[vi]
        # Pull rear-cocked left shoulder pad (v58) & collar forward into symmetric shoulder plane
        if vi == 58:
            raw = (-4.2, +10.2, 18.2)
        elif vi == 30:
            raw = (-4.2, -10.2, 18.2)
        elif vi == 65:
            raw = (-7.8, +4.2, 17.0)
        p = _vsub(raw, torso_origin)
        p = _rot_z(p, 8.0)
        p = _vmul(p, scale)
        # Recline torso slightly backward (-ry leans -X backward, +Z up)
        p = _rot_y(p, -torso_recline_deg)
        return _vadd(p, pelvis_world)

    # Neck pivot in canonical torso space -> world space
    neck_local = _rot_y(_vmul(_rot_z(_vsub((-1.2, -0.4, 18.2), torso_origin), 8.0), scale), -torso_recline_deg)
    neck_world = _vadd(neck_local, pelvis_world)

    def xform_head(vi):
        p = _vsub(vs17[vi], head_origin)
        p = _vmul(p, scale)
        # Keep head upright and looking forward (+X) despite torso recline!
        p = _rot_y(p, head_pitch_deg)
        return _vadd(p, neck_world)

    posed = {}
    for vi in parts_verts["torso"]:
        posed[vi] = xform_torso(vi)
    for vi in parts_verts["head"]:
        posed[vi] = xform_head(vi)

    # 2. Arms: keep shoulder-pad cap (V <= 0.20) anchored on torso shoulders,
    #    pose deltoid -> elbow -> wrist -> glove tip smoothly onto steering wheel!
    wx, wy, wz = steer_pos
    for side_name, sign in (("l_arm", +1.0), ("r_arm", -1.0)):
        av = parts_verts[side_name]
        sh_vs = [vs17[i] for i in av if 0.20 < uvs[i][1] <= 0.27]
        el_vs = [vs17[i] for i in av if 0.30 <= uvs[i][1] <= 0.38]
        wr_vs = [vs17[i] for i in av if 0.44 <= uvs[i][1] <= 0.50]
        hd_vs = [vs17[i] for i in av if uvs[i][1] > 0.51]
        p_sh = _avg(sh_vs)
        p_el = _avg(el_vs)
        p_wr = _avg(wr_vs)
        p_hd = _avg(hd_vs)

        # Target shoulder socket anchored symmetrically to reclined torso
        t_sh_local = _rot_y(_vmul(_rot_z(_vsub((-4.2, sign * 9.0, 15.2), torso_origin), 8.0), scale), -torso_recline_deg)
        t_sh = _vadd(t_sh_local, pelvis_world)

        t_hd = (wx - 0.3, wy + sign * (grip_half_y - 0.2), wz + 0.1)
        t_wr = (wx - 2.5, wy + sign * (grip_half_y + 0.5), wz - 0.6)
        t_el = (
            t_sh[0] * 0.44 + t_wr[0] * 0.56 - 1.2,
            t_sh[1] * 0.35 + t_wr[1] * 0.65 + sign * 2.5,
            t_sh[2] * 0.48 + t_wr[2] * 0.52 - 3.8,
        )

        arm_posed = _pose_limb_chain(
            vs17, av, uvs,
            [p_sh, p_el, p_wr, p_hd],
            [t_sh, t_el, t_wr, t_hd],
            [(1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
            [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0)],
            socket_blend_vmax=0.29,
            torso_pos_fn=xform_torso,
        )
        for vi, pv in arm_posed.items():
            if uvs[vi][1] <= 0.20:
                posed[vi] = xform_torso(vi)
            else:
                posed[vi] = pv

    # 3. Legs: pose cleanly onto seat pan -> knee -> footwell!
    fx, fy_abs, fz = foot_pos
    for side_name, sign in (("l_leg", +1.0), ("r_leg", -1.0)):
        lv = parts_verts[side_name]
        hip_vs = [vs17[i] for i in lv if uvs[i][1] <= 0.63]
        knee_vs = [vs17[i] for i in lv if 0.69 <= uvs[i][1] <= 0.77]
        ank_vs = [vs17[i] for i in lv if 0.88 <= uvs[i][1] <= 0.92]
        boot_vs = [vs17[i] for i in lv if uvs[i][1] >= 0.94]

        p_hip = _avg(hip_vs)
        p_knee = _avg(knee_vs)
        p_ank = _avg(ank_vs)
        p_boot = _avg(boot_vs)

        t_hip = (sx + 3.2, sy + sign * 4.8, sz + 2.6)
        t_knee = (sx + 16.5, sy + sign * 6.8, sz + 6.4)
        t_ank = (fx, sy + sign * fy_abs, fz + 1.8)
        t_boot = (fx + 4.8, sy + sign * fy_abs, fz + 0.4)

        leg_posed = _pose_limb_chain(
            vs17, lv, uvs,
            [p_hip, p_knee, p_ank, p_boot],
            [t_hip, t_knee, t_ank, t_boot],
            [(1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)],
            [(0.0, 0.0, 1.0), (1.0, 0.0, 0.3), (0.0, 0.0, 1.0)],
            socket_blend_vmax=0.63,
            torso_pos_fn=xform_torso,
        )
        for vi, pv in leg_posed.items():
            vx, vy, vz = pv
            if vx > sx + 5.0 and abs(vy) < 4.5:
                vy = sign * 4.5
            if vx < sx + 10.0 and vz < sz - 0.5:
                vz = sz - 0.5
            if vx >= sx + 10.0 and vz < fz - 1.2:
                vz = fz - 1.2
            posed[vi] = (vx, vy, vz)

    # 4. Split MDL seam vertices cleanly into MD3 (pos, uv) list & reverse winding (v0, v2, v1) for CCW outward!
    key_to_idx = {}
    out_verts = []
    out_st = []
    out_tris = []

    for ff, v0, v1, v2 in body_tris:
        tri_idx = []
        for vi in (v0, v2, v1):  # reverse MDL CW -> MD3 CCW
            onseam, s, t = st[vi]
            if not ff and onseam:
                s += sw // 2
            key = (vi, s, t)
            if key not in key_to_idx:
                key_to_idx[key] = len(out_verts)
                out_verts.append(posed[vi])
                out_st.append((s / float(sw), t / float(sh)))
            tri_idx.append(key_to_idx[key])
        out_tris.append(tuple(tri_idx))

    mesh = DriverMesh(out_verts, [(0.0, 0.0, 1.0)] * len(out_verts), out_tris, out_st)
    mesh.compute_normals()
    return mesh


def _xform_mesh(mesh, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0)):
    vv, nn = [], []
    px, py, pz = pivot
    for p, n in zip(mesh.verts, mesh.norms):
        q = (p[0] - px, p[1] - py, p[2] - pz)
        qn = n
        if rx:
            q = _rot_x(q, rx)
            qn = _rot_x(qn, rx)
        if ry:
            q = _rot_y(q, ry)
            qn = _rot_y(qn, ry)
        if rz:
            q = _rot_z(q, rz)
            qn = _rot_z(qn, rz)
        vv.append((q[0] + px + offset[0], q[1] + py + offset[1], q[2] + pz + offset[2]))
        nn.append(_vnorm(qn))
    return vv, nn


def _simulate_driver_explosion(mesh, init_ry, init_pivot, vel0, ang_vel0, n_frames=20):
    base_vv, base_nn = _xform_mesh(mesh, ry=init_ry, pivot=init_pivot)
    n = len(base_vv)
    c0 = (
        sum(p[0] for p in base_vv) / n,
        sum(p[1] for p in base_vv) / n,
        sum(p[2] for p in base_vv) / n,
    )
    rel_v = [(p[0] - c0[0], p[1] - c0[1], p[2] - c0[2]) for p in base_vv]
    pos = list(c0)
    vel = list(vel0)
    ang = [0.0, 0.0, 0.0]
    w = list(ang_vel0)
    dt = 0.085
    grav = -145.0
    frames = []
    for k in range(n_frames):
        step_dt = dt * (0.45 if k == 0 else 1.0)
        vel[2] += grav * step_dt
        pos[0] += vel[0] * step_dt
        pos[1] += vel[1] * step_dt
        pos[2] += vel[2] * step_dt
        ang[0] += w[0] * step_dt
        ang[1] += w[1] * step_dt
        ang[2] += w[2] * step_dt
        vv_r, nn_r = [], []
        min_z = 1e9
        for q, qn in zip(rel_v, base_nn):
            q = _rot_z(_rot_y(_rot_x(q, ang[0]), ang[1]), ang[2])
            qn = _rot_z(_rot_y(_rot_x(qn, ang[0]), ang[1]), ang[2])
            vz = pos[2] + q[2]
            if vz < min_z:
                min_z = vz
            vv_r.append((pos[0] + q[0], pos[1] + q[1], vz))
            nn_r.append(_vnorm(qn))
        if min_z < 0.5:
            shift = 0.5 - min_z
            pos[2] += shift
            vv_r = [(p[0], p[1], p[2] + shift) for p in vv_r]
            if vel[2] < 0.0:
                vel[2] = -0.52 * vel[2]
                vel[0] *= 0.80
                vel[1] *= 0.80
                w[0] *= 0.72
                w[1] *= 0.72
                w[2] *= 0.72
        frames.append((vv_r, nn_r))
    return frames


def build_driver_md3(progs_dir=PROGS_DIR, meta_dir=OUT_DIR, bakersfield_pk3=BAKER_PK3):
    """Exports standalone 64-frame seated Quake Ranger MD3 (`progs/gokart_driver.md3`)
    so empty parked go-karts have no driver inside until a player gets in.
    """
    os.makedirs(progs_dir, exist_ok=True)
    tex_out = os.path.join(progs_dir, "gk_driver.png")
    ensure_driver_texture(out_path=tex_out, bakersfield_pk3=bakersfield_pk3)
    mesh = build_seated_driver(
        seat_pos={"x": -9.0, "y": 0.0, "z": 9.5},
        steer_pos={"x": 13.0, "y": 0.0, "z": 24.0},
        foot_pos=(19.5, 6.8, 7.0),
        grip_half_y=6.6,
        bakersfield_pk3=bakersfield_pk3,
    )

    frame_names = []
    frames = []
    squat_pivot = (-25.0, 0.0, 11.0)
    seat_pivot = (-9.0, 0.0, 10.0)

    # 0..11: idle
    for k in range(12):
        frame_names.append(f"idle_{k:02d}")
        ph = 2.0 * math.pi * (k / 12.0)
        dz = 0.16 * math.sin(ph * 2.0)
        frames.append(_xform_mesh(mesh, offset=(0.0, 0.0, dz)))

    # 12..27: fast (rides chassis chatter + subtle sporty forward lean)
    for k in range(16):
        frame_names.append(f"fast_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz = 0.34 * math.sin(ph * 2.0) + 0.14 * math.cos(ph * 4.0)
        ry = 0.25 * math.sin(ph * 2.0)
        rx = 0.18 * math.cos(ph)
        frames.append(_xform_mesh(mesh, offset=(0.0, 0.0, dz), rx=rx, ry=ry, pivot=seat_pivot))

    # 28..43: super (matches +1.8 deg rear squat / nose lift)
    for k in range(16):
        frame_names.append(f"super_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz = 0.26 * math.sin(ph * 4.0)
        squat_ry = 1.8 + 0.20 * math.sin(ph * 2.0)
        frames.append(_xform_mesh(mesh, offset=(0.0, 0.0, dz), ry=squat_ry, pivot=squat_pivot))

    # 44..63: explode (ballistic ejection)
    for k in range(20):
        frame_names.append(f"explode_{k:02d}")
    frames += _simulate_driver_explosion(mesh, 1.8, squat_pivot, (-26.0, 18.0, 168.0), (210.0, -340.0, 145.0), n_frames=20)

    model = dict(
        name="progs/gokart_driver.md3",
        frame_names=frame_names,
        surfaces=[dict(name="driver", shader=DRIVER_SHADER, tris=mesh.tris, st=mesh.st, frames=frames)],
    )
    md3_path = os.path.join(progs_dir, "gokart_driver.md3")
    md3lib.write(md3_path, model)

    skin_path = md3_path + "_0.skin"
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        f.write(f"driver,{DRIVER_SHADER}\n")

    if meta_dir is not None:
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, "gokart_driver_meta.json")
        with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(
                {
                    "id": "gokart_driver",
                    "name": "Quake Ranger Driver",
                    "md3File": "progs/gokart_driver.md3",
                    "textures": {DRIVER_SHADER: DRIVER_TEX_REL},
                    "materials": {DRIVER_SHADER: {"metallic": 0.12, "roughness": 0.68, "spec": 0.30}},
                },
                f,
                indent=2,
            )

    rt = md3lib.read(md3_path)
    assert rt["nframes"] == 64 and len(rt["surfaces"]) == 1
    print(f"[OK] {md3_path} | 64f | {len(mesh.verts)}v / {len(mesh.tris)}t | {skin_path}")
    return md3_path


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build seated Quake Ranger driver MD3 and skin texture.")
    parser.add_argument("--bakersfield-pk3", default=BAKER_PK3, help="Path to bakersfield.pk3")
    parser.add_argument("--out-dir", default=None, help="Output directory for gk_driver.png, gokart_driver.md3, and .skin")
    parser.add_argument("--meta-dir", default=None, help="Optional directory for gokart_driver_meta.json")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS_DIR
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    build_driver_md3(progs_dir=progs_dir, meta_dir=meta_dir, bakersfield_pk3=args.bakersfield_pk3)
