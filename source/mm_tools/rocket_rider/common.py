"""Shared foundation for the 3 BakersfieldQuake Rocket Rider plane variants.

Runs strictly on standard Python 3.12 + numpy + Pillow (NO scipy) with
deterministic seeded RNG so generated assets are 100% CI-reproducible per AGENTS.md.

Coordinate convention (Quake / DarkPlaces MD3 standard):
  +X  forward (rocket nose / Ranger facing direction)
  +Y  left / port  (-Y right / starboard)
  +Z  up (Z = 0.0 is ground contact plane on `idle_ground` frames 56..67)

Vehicle Euler convention (`apply_vehicle_xform` / `euler_mat`):
  +pitch_deg : nose UP (+X pitches toward +Z; matches Quake entity angles_x)
  +yaw_deg   : yaw LEFT (+X turns toward +Y; matches Quake angles_y)
  +roll_deg  : bank RIGHT (+Y left wing rises toward +Z; matches Quake angles_z)

Ranger Rig Euler convention (`QuakeRangerRig.pose_frame`):
  +torso_pitch : leans torso FORWARD toward +X (-deg leans backward)
  +torso_yaw   : turns torso LEFT toward +Y
  +torso_roll  : tilts torso RIGHT (right-hand around +X)
  head_pitch/yaw/roll : evaluated in upright vehicle space (0,0,0 = looking straight +X)
                        +head_pitch tilts chin DOWN, -head_pitch tilts chin UP.
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MM_TOOLS_DIR = HERE.parent
REPO_ROOT = MM_TOOLS_DIR.parent.parent
OUT_DIR = MM_TOOLS_DIR / "out" / "rocket_rider"

if str(MM_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS_DIR))

import gokart_driver as _gd  # noqa: E402
import md3lib  # noqa: E402

# Hard Quake / DarkPlaces MD3 caps are 4096 verts / 8192 tris per surface;
# builders target a comfortable margin below the ceiling.
MAX_SURF_VERTS = 3600
MAX_SURF_TRIS = 7200
HARD_MD3_VERTS = 4096
HARD_MD3_TRIS = 8192

# Exact 7-clip, 100-frame John Bird-modeled animation schedule.
# Every clip is a seamless periodic loop with phase = 2 * pi * k / count.
CLIPS: list[dict[str, Any]] = [
    {
        "id": "fly_cruise",
        "label": "Cruise",
        "start": 0,
        "count": 16,
        "fps": 14,
        "loop": True,
        "jb_ref": "fly_breezy (0..15)",
        "desc": "Steady level cruise flight (780 u/s): smooth thrust hum, rhythmic sway/bob, Ranger leaning forward gripping tight.",
    },
    {
        "id": "fly_boost",
        "label": "Boost",
        "start": 16,
        "count": 16,
        "fps": 22,
        "loop": True,
        "jb_ref": "fast_fly (100..115)",
        "desc": "High-speed Shift/carve boost (>= 950 u/s): flaring afterburner cone + Mach shock diamonds, high-freq buffet, Ranger hunkered tight.",
    },
    {
        "id": "fly_hover",
        "label": "Hover / Climb",
        "start": 32,
        "count": 12,
        "fps": 12,
        "loop": True,
        "jb_ref": "hover_flutter (32..47)",
        "desc": "Nose-pitched VTOL hover & climb: pulsed exhaust, buoyant altitude bob, Ranger braced upright holding steady.",
    },
    {
        "id": "swoop_dive",
        "label": "Swoop Dive",
        "start": 44,
        "count": 12,
        "fps": 16,
        "loop": True,
        "jb_ref": "swoop_dive (48..59)",
        "desc": "Steep downward dive (vz < -420 u/s): nose pitched down, streamlined tight tuck over rocket nose, sleek trailing flame.",
    },
    {
        "id": "idle_ground",
        "label": "Idle Ground",
        "start": 56,
        "count": 12,
        "fps": 8,
        "loop": True,
        "jb_ref": "perch_breeze (60..71)",
        "desc": "Parked / landed at rest on Z = 0: calm pilot-light flame, gentle engine idle thrum, relaxed seated grip ready to launch.",
    },
    {
        "id": "hit_flail",
        "label": "Hit / Buck",
        "start": 68,
        "count": 16,
        "fps": 26,
        "loop": True,
        "jb_ref": "hit_flail (116..131)",
        "desc": "Damage reaction (JB_Pain 0.65s): erratic rocket buck/roll wobble, sputtering exhaust, Ranger jolted white-knuckled still holding on.",
    },
    {
        "id": "skypad_hyper",
        "label": "SkyPad Hyper",
        "start": 84,
        "count": 16,
        "fps": 30,
        "loop": True,
        "jb_ref": "skypad_hyper (132..147)",
        "desc": "Supersonic info_skypad blast (>= 1500 u/s): roaring hyper-plume + Mach diamonds + slipstream speed ribbons, Ranger pinned back holding on for dear life.",
    },
]

TOTAL_FRAMES = sum(c["count"] for c in CLIPS)
assert TOTAL_FRAMES == 100


def get_clip(clip_id: str) -> dict[str, Any]:
    for c in CLIPS:
        if c["id"] == clip_id:
            return c
    raise KeyError(f"Unknown clip id: {clip_id}")


def iter_clip_frames():
    """Yield `(frame_idx, clip_dict, k, u, phase, frame_name)` for frames 0..99."""
    fi = 0
    for clip in CLIPS:
        cnt = clip["count"]
        for k in range(cnt):
            u = k / float(cnt)
            phase = 2.0 * math.pi * u
            yield fi, clip, k, u, phase, f"{clip['id']}_{k:02d}"
            fi += 1


# ===========================================================================
# ROTATION, TRANSFORM & NORMAL MATH
# ===========================================================================

def rot_x_mat(deg: float) -> np.ndarray:
    """Right-hand rotation around +X (forward): +deg lifts +Y (left) toward +Z (up) = bank right."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float32)


def rot_y_nose_up_mat(deg: float) -> np.ndarray:
    """Vehicle pitch matrix around Y: +deg pitches +X (nose) UP toward +Z."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float32)


def rot_y_rh_mat(deg: float) -> np.ndarray:
    """Right-hand rotation around +Y: +deg tilts +Z (torso) FORWARD toward +X."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float32)


def rot_z_mat(deg: float) -> np.ndarray:
    """Right-hand rotation around +Z (up): +deg yaws +X (forward) LEFT toward +Y."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)


def euler_mat(pitch_deg: float = 0.0, yaw_deg: float = 0.0, roll_deg: float = 0.0) -> np.ndarray:
    """Vehicle rotation matrix (`v @ R.T`): roll around forward axis, then pitch (+nose up), then yaw (+left)."""
    return (rot_z_mat(yaw_deg) @ rot_y_nose_up_mat(pitch_deg) @ rot_x_mat(roll_deg)).astype(np.float32)


def apply_vehicle_xform(
    pts: np.ndarray,
    offset=(0.0, 0.0, 0.0),
    pitch_deg: float = 0.0,
    yaw_deg: float = 0.0,
    roll_deg: float = 0.0,
    pivot=(0.0, 0.0, 0.0),
) -> np.ndarray:
    """Rigid-body transform of `(N, 3)` vertices in Quake vehicle space.

    Order: subtract `pivot` -> roll (`+right bank`) -> pitch (`+nose up`) -> yaw (`+left`) -> add `pivot + offset`.
    """
    v = np.asarray(pts, dtype=np.float32)
    piv = np.asarray(pivot, dtype=np.float32)
    ofs = np.asarray(offset, dtype=np.float32)
    R = euler_mat(pitch_deg=pitch_deg, yaw_deg=yaw_deg, roll_deg=roll_deg)
    return ((v - piv) @ R.T + piv + ofs).astype(np.float32)


def compute_vertex_normals(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    """Vectorized area-weighted smooth vertex normals for CCW outward triangles."""
    v = np.asarray(verts, dtype=np.float32)
    t = np.asarray(tris, dtype=np.int32)
    v0 = v[t[:, 0]]
    v1 = v[t[:, 1]]
    v2 = v[t[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    vn = np.zeros_like(v, dtype=np.float32)
    np.add.at(vn, t[:, 0], fn)
    np.add.at(vn, t[:, 1], fn)
    np.add.at(vn, t[:, 2], fn)
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    safe = np.where(ln > 1e-8, ln, 1.0)
    vn = np.where(ln > 1e-8, vn / safe, np.array([0.0, 0.0, 1.0], dtype=np.float32))
    return vn.astype(np.float32)


def signed_mesh_volume(verts: np.ndarray, tris: np.ndarray, center=None) -> float:
    """Signed volume of a closed triangle mesh (> 0 means CCW outward normals)."""
    v = np.asarray(verts, dtype=np.float64)
    t = np.asarray(tris, dtype=np.int32)
    if len(t) == 0:
        return 0.0
    c = v.mean(axis=0) if center is None else np.asarray(center, dtype=np.float64)
    v0 = v[t[:, 0]] - c
    v1 = v[t[:, 1]] - c
    v2 = v[t[:, 2]] - c
    return float(np.sum(np.einsum("ij,ij->i", v0, np.cross(v1, v2))) / 6.0)


def verify_outward_winding(verts: np.ndarray, tris: np.ndarray, center=None) -> np.ndarray:
    """Ensure a closed part's triangles wind CCW outward (positive signed volume)."""
    t = np.asarray(tris, dtype=np.int32)
    if signed_mesh_volume(verts, t, center=center) < 0.0:
        return t[:, [0, 2, 1]].copy()
    return t.copy()


def _basis_from_axis(axis_dir, up_hint=(0.0, 0.0, 1.0)):
    ax = np.asarray(axis_dir, dtype=np.float64)
    ax_len = float(np.linalg.norm(ax))
    if ax_len < 1e-9:
        ax = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    else:
        ax = ax / ax_len
    uh = np.asarray(up_hint, dtype=np.float64)
    if abs(float(np.dot(ax, uh))) > 0.96:
        uh = np.array([0.0, 1.0, 0.0] if abs(ax[1]) < 0.9 else [1.0, 0.0, 0.0], dtype=np.float64)
    b1 = np.cross(uh, ax)
    b1 /= max(1e-9, float(np.linalg.norm(b1)))
    b2 = np.cross(ax, b1)
    b2 /= max(1e-9, float(np.linalg.norm(b2)))
    return ax, b1, b2


def _unit(v, fallback=(1.0, 0.0, 0.0)) -> np.ndarray:
    a = np.asarray(v, dtype=np.float64)
    l = float(np.linalg.norm(a))
    if l < 1e-9:
        return np.asarray(fallback, dtype=np.float64)
    return a / l


def _smoothstep(edge0: float, edge1: float, x):
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ===========================================================================
# CANONICAL QUAKE 1 RANGER RIG (wraps gokart_driver.py without modifying it)
# ===========================================================================

def _load_canonical_player_mdl_bytes() -> bytes:
    """Prefer repo-committed source/mm_tools/id1/player.mdl (CI-safe), fallback to gokart_driver."""
    repo_mdl = MM_TOOLS_DIR / "id1" / "player.mdl"
    if repo_mdl.is_file():
        return repo_mdl.read_bytes()
    return _gd._load_player_mdl_bytes()


def ensure_ranger_texture(out_path: Path | str | None = None) -> Path:
    """Extract the 296x194 Quake 1 Ranger palette skin, 2px edge-dilate, and save crisp 592x388 PNG."""
    dst = Path(out_path) if out_path is not None else (OUT_DIR / "ranger_skin.png")
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Use repo-committed player.mdl + embedded Quake palette so output is 100% CI-deterministic.
    data = _load_canonical_player_mdl_bytes()
    pal = base64.b64decode(_gd._QUAKE_PALETTE_B64)

    import struct

    hdr = struct.unpack("<4si3f3ff3f8if", data[:84])
    sw, sh = hdr[13], hdr[14]
    skin_idx = data[88 : 88 + sw * sh]

    im_p = Image.frombytes("P", (sw, sh), skin_idx)
    im_p.putpalette(pal)
    rgb = np.array(im_p.convert("RGB"), dtype=np.uint8)

    # 2px dilation of non-black UV islands prevents dark bilinear seam bleed.
    mask = rgb.sum(axis=2) > 12
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

    out_im = Image.fromarray(padded, mode="RGB").resize((sw * 2, sh * 2), Image.Resampling.BILINEAR)
    out_im.save(dst, "PNG", optimize=True)
    return dst


def _make_seg_frame_np(p0: np.ndarray, p1: np.ndarray, fwd_hint: np.ndarray):
    axis = _unit(p1 - p0, fallback=(1.0, 0.0, 0.0))
    fh = fwd_hint - axis * float(np.dot(fwd_hint, axis))
    if float(np.linalg.norm(fh)) < 1e-5:
        alt = np.array([1.0, 0.0, 0.0] if abs(axis[0]) < 0.8 else [0.0, 0.0, 1.0], dtype=np.float64)
        fh = alt - axis * float(np.dot(alt, axis))
    fwd = _unit(fh)
    lat = _unit(np.cross(axis, fwd))
    return axis, fwd, lat


def _pose_limb_chain_scaled(
    verts_src: list[tuple[float, float, float]],
    v_list: list[int],
    uvs: dict[int, tuple[float, float]],
    src_pts: list[np.ndarray],
    dst_pts: list[np.ndarray],
    src_fwd_hints: list[np.ndarray],
    dst_fwd_hints: list[np.ndarray],
    rad_scale: float = 1.0,
    socket_blend_vmax: float | None = None,
    socket_blend_band: float = 0.08,
    torso_pos_fn=None,
) -> dict[int, np.ndarray]:
    """Map a 3-segment limb (P0->P1->P2->P3) onto target polyline (T0->T1->T2->T3)
    with smooth joint-bisector plane blending and proportional radial scaling.
    """
    src_segs = [_make_seg_frame_np(src_pts[i], src_pts[i + 1], src_fwd_hints[i]) for i in range(3)]
    dst_segs = [_make_seg_frame_np(dst_pts[i], dst_pts[i + 1], dst_fwd_hints[i]) for i in range(3)]
    src_lens = [max(1e-5, float(np.linalg.norm(src_pts[i + 1] - src_pts[i]))) for i in range(3)]
    dst_lens = [max(1e-5, float(np.linalg.norm(dst_pts[i + 1] - dst_pts[i]))) for i in range(3)]

    def _blend_frame(f0, f1, w: float):
        a = _unit(f0[0] * (1.0 - w) + f1[0] * w, fallback=f0[0])
        f = f0[1] * (1.0 - w) + f1[1] * w
        f = f - a * float(np.dot(f, a))
        if float(np.linalg.norm(f)) < 1e-5:
            f = f0[1] - a * float(np.dot(f0[1], a))
        f = _unit(f)
        l = _unit(np.cross(a, f))
        return a, f, l

    src_j = [_blend_frame(src_segs[j - 1], src_segs[j], 0.5) for j in (1, 2)]
    dst_j = [_blend_frame(dst_segs[j - 1], dst_segs[j], 0.5) for j in (1, 2)]

    out: dict[int, np.ndarray] = {}
    for vi in v_list:
        p = np.asarray(verts_src[vi], dtype=np.float64)
        best_si = 0
        best_t = 0.0
        best_d2 = 1e18
        for si in range(3):
            a, b = src_pts[si], src_pts[si + 1]
            ab = b - a
            l2 = max(1e-8, float(np.dot(ab, ab)))
            t = max(0.0, min(1.0, float(np.dot(p - a, ab)) / l2))
            proj = a + ab * t
            d = p - proj
            d2 = float(np.dot(d, d))
            if d2 < best_d2:
                best_d2 = d2
                best_si = si
                best_t = t

        si, t = best_si, best_t
        if si == 0 and t > 0.65:
            w = (t - 0.65) / 0.35
            sa, sf, sl = _blend_frame(src_segs[0], src_j[0], w)
            da, df, dl = _blend_frame(dst_segs[0], dst_j[0], w)
        elif si == 1 and t < 0.35:
            w = (0.35 - t) / 0.35
            sa, sf, sl = _blend_frame(src_segs[1], src_j[0], w)
            da, df, dl = _blend_frame(dst_segs[1], dst_j[0], w)
        elif si == 1 and t > 0.72:
            w = (t - 0.72) / 0.28
            sa, sf, sl = _blend_frame(src_segs[1], src_j[1], w)
            da, df, dl = _blend_frame(dst_segs[1], dst_j[1], w)
        elif si == 2 and t < 0.30:
            w = (0.30 - t) / 0.30
            sa, sf, sl = _blend_frame(src_segs[2], src_j[1], w)
            da, df, dl = _blend_frame(dst_segs[2], dst_j[1], w)
        else:
            sa, sf, sl = src_segs[si]
            da, df, dl = dst_segs[si]

        src_base = src_pts[si] * (1.0 - t) + src_pts[si + 1] * t
        delta = p - src_base
        c_ax = float(np.dot(delta, sa))
        c_fw = float(np.dot(delta, sf))
        c_lt = float(np.dot(delta, sl))

        len_ratio = dst_lens[si] / src_lens[si]
        dst_base = dst_pts[si] * (1.0 - t) + dst_pts[si + 1] * t
        p_limb = dst_base + da * (c_ax * len_ratio) + df * (c_fw * rad_scale) + dl * (c_lt * rad_scale)

        if socket_blend_vmax is not None and torso_pos_fn is not None:
            _, vf = uvs[vi]
            if vf < socket_blend_vmax:
                p_torso = torso_pos_fn(vi)
                alpha = max(0.0, min(1.0, (vf - (socket_blend_vmax - socket_blend_band)) / socket_blend_band))
                p_limb = p_torso * (1.0 - alpha) + p_limb * alpha

        out[vi] = p_limb
    return out


class QuakeRangerRig:
    """Articulated Quake 1 Ranger rig extracted from `source/mm_tools/id1/player.mdl` frame 17 (`axstnd1`).

    Attributes:
        tris: `(294, 3)` int32 CCW outward triangles in MD3 vertex order.
        uvs:  `(218, 2)` float32 UVs (`v = 0` top, `v = 1` bottom) with `onseam` splits resolved.
        n_verts: int (218 after seam splits; 149 unique body vertices).
        n_tris: int (294).
    """

    TORSO_ORIGIN = np.array([-4.5, -0.6, -2.2], dtype=np.float64)
    HEAD_ORIGIN = np.array([-1.6, -0.3, 18.2], dtype=np.float64)
    NECK_IN_TORSO = np.array([-1.2, -0.4, 18.2], dtype=np.float64)
    SHOULDER_FIX = {
        58: (-4.2, +10.2, 18.2),
        30: (-4.2, -10.2, 18.2),
        65: (-7.8, +4.2, 17.0),
    }

    def __init__(self, bakersfield_pk3: str | Path | None = None):
        # Load canonical 1996 player.mdl (prefer repo-committed CI-safe copy)
        repo_mdl = MM_TOOLS_DIR / "id1" / "player.mdl"
        if bakersfield_pk3 is None and repo_mdl.is_file():
            # Temporarily pass None so _parse_id1_body doesn't fail if bakersfield.pk3 is absent;
            # parse using repo_mdl directly with the exact same algorithm as gokart_driver._parse_id1_body.
            self._init_from_mdl_bytes(repo_mdl.read_bytes())
        else:
            bk = str(bakersfield_pk3) if bakersfield_pk3 is not None else _gd.BAKER_PK3
            self._init_from_mdl_bytes(_gd._load_player_mdl_bytes(bakersfield_pk3=bk))

    def _init_from_mdl_bytes(self, data: bytes) -> None:
        import struct
        from collections import deque

        hdr = struct.unpack("<4si3f3ff3f8if", data[:84])
        scale, trans = hdr[2:5], hdr[5:8]
        nskins, sw, sh, nverts, ntris, _nframes = hdr[12:18]
        pos = 84 + nskins * (4 + sw * sh)
        st = [struct.unpack("<3i", data[pos + 12 * i : pos + 12 * i + 12]) for i in range(nverts)]
        pos += 12 * nverts
        tris_raw = [struct.unpack("<4i", data[pos + 16 * i : pos + 16 * i + 16]) for i in range(ntris)]
        pos += 16 * ntris
        frame_len = 4 + 8 + 16 + nverts * 4

        # Frame 17: axstnd1 (arms free at sides, head straight)
        fbase = pos + 17 * frame_len
        vs17 = [
            tuple(
                struct.unpack("<4B", data[fbase + 28 + 4 * vi : fbase + 28 + 4 * vi + 4])[k] * scale[k] + trans[k]
                for k in range(3)
            )
            for vi in range(nverts)
        ]

        # Isolate 149-vert Ranger body (largest connected component; strips axe/shotgun/muzzle flash)
        adj: dict[int, set[int]] = defaultdict(set)
        for _ff, v0, v1, v2 in tris_raw:
            for a, b in ((v0, v1), (v1, v2), (v2, v0)):
                adj[a].add(b)
                adj[b].add(a)
        seen: set[int] = set()
        comps: list[list[int]] = []
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
        body_tris = [t for t in tris_raw if t[1] in body_set]

        self._vs17 = vs17
        self._body = body
        self._parts: dict[str, list[int]] = defaultdict(list)
        self._uv_part: dict[int, tuple[float, float]] = {}
        for vi in body:
            pname, uf, vf = _gd._classify_vert(vi, st, sw, sh)
            self._parts[pname].append(vi)
            self._uv_part[vi] = (uf, vf)

        # Build invariant MD3 seam-split vertex table & CCW outward triangle winding (v0, v2, v1)
        key_to_idx: dict[tuple[int, int, int], int] = {}
        md3_src_vi: list[int] = []
        out_st: list[tuple[float, float]] = []
        out_tris: list[tuple[int, int, int]] = []
        for ff, v0, v1, v2 in body_tris:
            tri_idx = []
            for vi in (v0, v2, v1):  # reverse MDL CW -> MD3 CCW outward
                onseam, s, t = st[vi]
                if not ff and onseam:
                    s += sw // 2
                key = (vi, s, t)
                if key not in key_to_idx:
                    key_to_idx[key] = len(md3_src_vi)
                    md3_src_vi.append(vi)
                    out_st.append((s / float(sw), t / float(sh)))
                tri_idx.append(key_to_idx[key])
            out_tris.append((tri_idx[0], tri_idx[1], tri_idx[2]))

        self._md3_src_vi = md3_src_vi
        self.uvs = np.asarray(out_st, dtype=np.float32)
        self.tris = np.asarray(out_tris, dtype=np.int32)
        self.n_verts = len(md3_src_vi)
        self.n_tris = len(out_tris)

        # Precompute canonical rest limb joint centroids in axstnd1
        self._arm_src: dict[str, list[np.ndarray]] = {}
        self._hand_md3_indices: dict[str, list[int]] = {}
        for side_name in ("l_arm", "r_arm"):
            av = self._parts[side_name]
            sh_vs = [vs17[i] for i in av if 0.20 < self._uv_part[i][1] <= 0.295]
            el_vs = [vs17[i] for i in av if 0.30 <= self._uv_part[i][1] <= 0.38]
            wr_vs = [vs17[i] for i in av if 0.44 <= self._uv_part[i][1] <= 0.52]
            hd_vs = [vs17[i] for i in av if self._uv_part[i][1] > 0.52]
            self._arm_src[side_name] = [
                np.mean(sh_vs, axis=0),
                np.mean(el_vs, axis=0),
                np.mean(wr_vs, axis=0),
                np.mean(hd_vs, axis=0),
            ]
            hd_set = {i for i in av if self._uv_part[i][1] > 0.52}
            self._hand_md3_indices[side_name] = [mi for mi, vi in enumerate(md3_src_vi) if vi in hd_set]

        self._leg_src: dict[str, list[np.ndarray]] = {}
        self._foot_md3_indices: dict[str, list[int]] = {}
        for side_name in ("l_leg", "r_leg"):
            lv = self._parts[side_name]
            hip_vs = [vs17[i] for i in lv if self._uv_part[i][1] <= 0.63]
            kn_vs = [vs17[i] for i in lv if 0.69 <= self._uv_part[i][1] <= 0.77]
            ank_vs = [vs17[i] for i in lv if 0.88 <= self._uv_part[i][1] <= 0.92]
            bt_vs = [vs17[i] for i in lv if self._uv_part[i][1] >= 0.94]
            self._leg_src[side_name] = [
                np.mean(hip_vs, axis=0),
                np.mean(kn_vs, axis=0),
                np.mean(ank_vs, axis=0),
                np.mean(bt_vs, axis=0),
            ]
            bt_set = {i for i in lv if self._uv_part[i][1] >= 0.94}
            self._foot_md3_indices[side_name] = [mi for mi, vi in enumerate(md3_src_vi) if vi in bt_set]

        # Straightening matrix (+8 deg around Z cancels axstnd1 combat yaw)
        self._R_straight = rot_z_mat(8.0).astype(np.float64)

    def hand_centroid(self, posed_verts: np.ndarray, side: str) -> np.ndarray:
        """Return actual posed centroid of gloved hand tips ('l_arm' or 'r_arm')."""
        return posed_verts[self._hand_md3_indices[side]].mean(axis=0)

    def foot_centroid(self, posed_verts: np.ndarray, side: str) -> np.ndarray:
        """Return actual posed centroid of boot/foot vertices ('l_leg' or 'r_leg')."""
        return posed_verts[self._foot_md3_indices[side]].mean(axis=0)

    def pose_frame(
        self,
        hip_pos,
        torso_pitch: float = 18.0,
        torso_yaw: float = 0.0,
        torso_roll: float = 0.0,
        head_pitch: float = 0.0,
        head_yaw: float = 0.0,
        head_roll: float = 0.0,
        l_hand=None,
        r_hand=None,
        l_elbow_hint=None,
        r_elbow_hint=None,
        l_knee=None,
        r_knee=None,
        l_foot=None,
        r_foot=None,
        scale: float = 1.18,
        lean_x: float = 0.0,
    ) -> np.ndarray:
        """Pose the canonical Quake Ranger body and return `(218, 3)` float32 vertices in MD3 order.

        Args:
            hip_pos: `(x, y, z)` pelvis/saddle contact point in vehicle local space.
            torso_pitch: +deg leans torso FORWARD (+X), -deg leans BACKWARD (-X).
            torso_yaw: +deg turns torso LEFT (+Y).
            torso_roll: +deg tilts torso RIGHT.
            head_pitch: +deg tilts chin DOWN, -deg tilts chin UP (in upright vehicle space).
            head_yaw: +deg looks LEFT (+Y).
            head_roll: +deg tilts head RIGHT.
            l_hand, r_hand: `(x, y, z)` target gloved-hand grip positions (e.g. handlebars / rocket nose).
            l_elbow_hint, r_elbow_hint: `(x, y, z)` target elbow positions (auto-computed if None).
            l_knee, r_knee: `(x, y, z)` target knee positions straddling the rocket fuselage.
            l_foot, r_foot: `(x, y, z)` target boot/foot positions on pegs/fins.
            scale: overall Ranger scale (`1.18` matches `gokart_driver.py` ~34.5u seated height).
            lean_x: additional forward/aft upper-body shear offset in Quake units.
        """
        hip = np.asarray(hip_pos, dtype=np.float64)
        R_torso = (
            rot_z_mat(torso_yaw).astype(np.float64)
            @ rot_y_rh_mat(torso_pitch).astype(np.float64)
            @ rot_x_mat(torso_roll).astype(np.float64)
        )
        R_head = (
            rot_z_mat(head_yaw).astype(np.float64)
            @ rot_y_rh_mat(head_pitch).astype(np.float64)
            @ rot_x_mat(head_roll).astype(np.float64)
        )

        def xform_torso_pt(raw_pt) -> np.ndarray:
            p = (np.asarray(raw_pt, dtype=np.float64) - self.TORSO_ORIGIN) @ self._R_straight.T * scale
            h_frac = max(0.0, min(1.0, p[2] / max(1e-6, 20.0 * scale)))
            p_rot = R_torso @ p
            p_rot[0] += lean_x * h_frac
            return p_rot + hip

        def xform_torso_vi(vi: int) -> np.ndarray:
            raw = self.SHOULDER_FIX.get(vi, self._vs17[vi])
            return xform_torso_pt(raw)

        neck_world = xform_torso_pt(self.NECK_IN_TORSO)

        def xform_head_vi(vi: int) -> np.ndarray:
            p = (np.asarray(self._vs17[vi], dtype=np.float64) - self.HEAD_ORIGIN) * scale
            return R_head @ p + neck_world

        posed: dict[int, np.ndarray] = {}
        for vi in self._parts["torso"]:
            posed[vi] = xform_torso_vi(vi)
        for vi in self._parts["head"]:
            posed[vi] = xform_head_vi(vi)

        torso_up = R_torso @ np.array([0.0, 0.0, 1.0], dtype=np.float64)
        torso_fwd = R_torso @ np.array([1.0, 0.0, 0.0], dtype=np.float64)

        # ---- Arms (Left +Y, Right -Y) ----
        for side_name, sign, hand_tgt, elbow_tgt in (
            ("l_arm", +1.0, l_hand, l_elbow_hint),
            ("r_arm", -1.0, r_hand, r_elbow_hint),
        ):
            av = self._parts[side_name]
            src_pts = self._arm_src[side_name]
            p_sh, p_el, p_wr, p_hd = src_pts
            t_sh = xform_torso_pt((-4.2, sign * 9.0, 15.2))

            if hand_tgt is None:
                t_hd = t_sh + np.array([15.0 * scale, -sign * 2.5 * scale, -3.5 * scale], dtype=np.float64)
            else:
                t_hd = np.asarray(hand_tgt, dtype=np.float64)

            if elbow_tgt is None:
                t_el = t_sh * 0.48 + t_hd * 0.52 + np.array([-1.5 * scale, sign * 3.5 * scale, -4.0 * scale])
            else:
                t_el = np.asarray(elbow_tgt, dtype=np.float64)

            hand_len = float(np.linalg.norm(p_hd - p_wr)) * scale
            fore_vec = t_hd - t_el
            fore_len = float(np.linalg.norm(fore_vec))
            if fore_len < hand_len + 1.0:
                fore_dir = _unit(t_hd - t_sh, fallback=(1.0, 0.0, 0.0))
                t_wr = t_hd - fore_dir * min(hand_len, max(1.0, fore_len * 0.4))
            else:
                t_wr = t_hd - (fore_vec / fore_len) * hand_len

            # Anatomical twist-free forward hints:
            # In axstnd1, arm hangs -Z and +X is bicep / inner-elbow / palm-front.
            u_dir = _unit(t_el - t_sh)
            f_dir = _unit(t_wr - t_el)
            bend_in = f_dir - u_dir
            if float(np.linalg.norm(bend_in)) > 0.15:
                arm_fwd = _unit(bend_in)
            else:
                arm_fwd = _unit(torso_up * 0.8 + torso_fwd * 0.6)

            arm_posed = _pose_limb_chain_scaled(
                self._vs17,
                av,
                self._uv_part,
                src_pts,
                [t_sh, t_el, t_wr, t_hd],
                [
                    np.array([1.0, 0.0, 0.0]),
                    np.array([1.0, 0.0, 0.0]),
                    np.array([1.0, 0.0, 0.0]),
                ],
                [arm_fwd, arm_fwd, arm_fwd],
                rad_scale=scale,
                socket_blend_vmax=0.29,
                socket_blend_band=0.08,
                torso_pos_fn=xform_torso_vi,
            )
            for vi, pv in arm_posed.items():
                if self._uv_part[vi][1] <= 0.20:
                    posed[vi] = xform_torso_vi(vi)
                else:
                    posed[vi] = pv

        # ---- Legs (Left +Y, Right -Y) ----
        for side_name, sign, knee_tgt, foot_tgt in (
            ("l_leg", +1.0, l_knee, l_foot),
            ("r_leg", -1.0, r_knee, r_foot),
        ):
            lv = self._parts[side_name]
            src_pts = self._leg_src[side_name]
            p_hip, p_kn, p_ank, p_bt = src_pts
            t_hip = xform_torso_pt((-4.0, sign * 4.8, 0.2))

            if knee_tgt is None:
                t_kn = hip + np.array([11.0 * scale, sign * 11.5 * scale, -4.5 * scale], dtype=np.float64)
            else:
                t_kn = np.asarray(knee_tgt, dtype=np.float64)

            if foot_tgt is None:
                t_bt = hip + np.array([2.5 * scale, sign * 12.5 * scale, -18.0 * scale], dtype=np.float64)
            else:
                t_bt = np.asarray(foot_tgt, dtype=np.float64)

            # Place ankle naturally above/behind boot centroid so toes face +X and boot lands on foot_tgt!
            boot_dx = float(p_bt[0] - p_ank[0]) * scale  # ~ +3.2*scale
            boot_dz = float(p_bt[2] - p_ank[2]) * scale  # ~ -3.1*scale
            t_ank = t_bt - np.array([boot_dx, 0.0, boot_dz], dtype=np.float64)

            # Anatomical twist-free forward hints:
            # In axstnd1, +X is front of thigh / kneecap / shin; knee bends backward, so (u_leg - l_leg) points out the kneecap!
            u_leg = _unit(t_kn - t_hip)
            l_leg = _unit(t_ank - t_kn)
            knee_out = u_leg - l_leg
            if float(np.linalg.norm(knee_out)) > 0.15:
                leg_fwd = _unit(knee_out)
            else:
                leg_fwd = np.array([1.0, 0.0, 0.25], dtype=np.float64)

            leg_posed = _pose_limb_chain_scaled(
                self._vs17,
                lv,
                self._uv_part,
                src_pts,
                [t_hip, t_kn, t_ank, t_bt],
                [
                    np.array([1.0, 0.0, 0.0]),
                    np.array([1.0, 0.0, 0.0]),
                    np.array([0.0, 0.0, 1.0]),
                ],
                [leg_fwd, leg_fwd, np.array([0.0, 0.0, 1.0])],
                rad_scale=scale,
                socket_blend_vmax=0.63,
                socket_blend_band=0.06,
                torso_pos_fn=xform_torso_vi,
            )
            for vi, pv in leg_posed.items():
                posed[vi] = pv

        out = np.empty((self.n_verts, 3), dtype=np.float32)
        for mi, vi in enumerate(self._md3_src_vi):
            out[mi] = posed[vi]
        return out


# ===========================================================================
# PROCEDURAL ROCKET GEOMETRY BUILDER (`SurfBuilder`)
# ===========================================================================

class SurfBuilder:
    """Procedural MD3 surface accumulator with outward winding verification & budget guard.

    All primitives emit CCW outward triangles in Quake space (+X forward, +Y left, +Z up)
    and smooth per-part normals (preserving crisp hard edges between distinct parts).
    """

    def __init__(
        self,
        name: str,
        shader: str,
        max_verts: int = MAX_SURF_VERTS,
        max_tris: int = MAX_SURF_TRIS,
    ):
        self.name = name
        self.shader = shader
        self.max_verts = max_verts
        self.max_tris = max_tris
        self._verts: list[np.ndarray] = []
        self._norms: list[np.ndarray] = []
        self._uvs: list[np.ndarray] = []
        self._tris: list[np.ndarray] = []
        self._nv = 0
        self._nt = 0

    @property
    def num_verts(self) -> int:
        return self._nv

    @property
    def num_tris(self) -> int:
        return self._nt

    def add_mesh(
        self,
        verts,
        tris,
        uvs,
        norms=None,
        verify_center=None,
        R: np.ndarray | None = None,
        offset=(0.0, 0.0, 0.0),
    ) -> None:
        va = np.asarray(verts, dtype=np.float32)
        ta = np.asarray(tris, dtype=np.int32)
        ua = np.asarray(uvs, dtype=np.float32)
        if len(va) == 0 or len(ta) == 0:
            return
        if R is not None:
            va = va @ np.asarray(R, dtype=np.float32).T
        if offset != (0.0, 0.0, 0.0):
            va = va + np.asarray(offset, dtype=np.float32)[None, :]
        if verify_center is not None:
            vc = np.asarray(verify_center, dtype=np.float64)
            if R is not None:
                vc = vc @ np.asarray(R, dtype=np.float64).T
            vc = vc + np.asarray(offset, dtype=np.float64)
            ta = verify_outward_winding(va, ta, center=vc)
        if norms is None:
            na = compute_vertex_normals(va, ta)
        else:
            na = np.asarray(norms, dtype=np.float32)
            if R is not None:
                na = na @ np.asarray(R, dtype=np.float32).T
            nl = np.maximum(np.linalg.norm(na, axis=1, keepdims=True), 1e-8)
            na = (na / nl).astype(np.float32)

        new_nv = self._nv + len(va)
        new_nt = self._nt + len(ta)
        if new_nv > self.max_verts or new_nt > self.max_tris:
            raise ValueError(
                f"Surface '{self.name}' exceeds budget ({new_nv}v/{new_nt}t > {self.max_verts}v/{self.max_tris}t). "
                "Split into two surfaces or reduce segment counts."
            )
        self._verts.append(va)
        self._norms.append(na)
        self._uvs.append(ua)
        self._tris.append(ta + self._nv)
        self._nv = new_nv
        self._nt = new_nt

    def add_lathe_axis(
        self,
        origin,
        axis_dir,
        profile,
        n_seg: int = 28,
        u_range=(0.02, 0.98),
        v_range=(0.02, 0.98),
        check_winding: bool = True,
        up_hint=(0.0, 0.0, 1.0),
    ) -> None:
        """Revolve `profile` of `[(s, r), ...]` or `[(s, r, v_frac), ...]` around `axis_dir` from `origin`."""
        org = np.asarray(origin, dtype=np.float64)
        ax, b1, b2 = _basis_from_axis(axis_dir, up_hint=up_hint)
        n_rings = len(profile)
        assert n_rings >= 2

        verts = []
        uvs = []
        rads = []
        s_vals = []
        for ri, row in enumerate(profile):
            s = float(row[0])
            r = float(row[1])
            vf = float(row[2]) if len(row) >= 3 else (ri / float(n_rings - 1))
            vv = v_range[0] + (v_range[1] - v_range[0]) * vf
            rads.append(r)
            s_vals.append(s)
            c_pt = org + ax * s
            for si in range(n_seg + 1):
                u_frac = si / float(n_seg)
                ang = 2.0 * math.pi * u_frac
                uu = u_range[0] + (u_range[1] - u_range[0]) * u_frac
                pt = c_pt + (b1 * math.cos(ang) + b2 * math.sin(ang)) * r
                verts.append(pt)
                uvs.append((uu, vv))

        stride = n_seg + 1
        tris = []
        for ri in range(n_rings - 1):
            r0 = ri * stride
            r1 = (ri + 1) * stride
            rad0, rad1 = rads[ri], rads[ri + 1]
            for si in range(n_seg):
                a, b = r0 + si, r0 + si + 1
                c, d = r1 + si + 1, r1 + si
                if rad0 > 1e-5:
                    tris.append((a, b, c))
                if rad1 > 1e-5:
                    tris.append((a, c, d))

        center = org + ax * (0.5 * (min(s_vals) + max(s_vals))) if check_winding else None
        self.add_mesh(verts, tris, uvs, verify_center=center)

    def add_lathe_x(
        self,
        profile,
        n_seg: int = 28,
        axis_offset=(0.0, 0.0, 0.0),
        u_range=(0.02, 0.98),
        v_range=(0.02, 0.98),
        check_winding: bool = True,
    ) -> None:
        """Revolve `[(x, r), ...]` or `[(x, r, v_frac), ...]` around the +X axis."""
        self.add_lathe_axis(
            origin=axis_offset,
            axis_dir=(1.0, 0.0, 0.0),
            profile=profile,
            n_seg=n_seg,
            u_range=u_range,
            v_range=v_range,
            check_winding=check_winding,
            up_hint=(0.0, 0.0, 1.0),
        )

    def add_nozzle_bell(
        self,
        origin,
        axis_dir=(-1.0, 0.0, 0.0),
        r_throat: float = 6.5,
        r_exit: float = 10.5,
        length: float = 14.0,
        n_seg: int = 24,
        u_range=(0.02, 0.98),
        v_range=(0.02, 0.98),
        hollow: bool = True,
    ) -> None:
        """Machined converging-diverging rocket exhaust bell nozzle with recessed dark interior."""
        prof = [
            (0.0, 0.0, 0.00),
            (0.0, r_throat * 1.12, 0.08),
            (length * 0.20, r_throat * 1.15, 0.22),
            (length * 0.30, r_throat, 0.34),
            (length * 0.62, r_exit * 0.88, 0.64),
            (length * 0.90, r_exit * 0.99, 0.84),
            (length, r_exit, 0.92),
        ]
        if hollow:
            prof.extend([
                (length, r_exit * 0.86, 0.95),
                (length * 0.36, r_throat * 0.68, 0.98),
                (length * 0.36, 0.0, 1.00),
            ])
        else:
            prof.append((length, 0.0, 1.00))
        self.add_lathe_axis(origin, axis_dir, prof, n_seg=n_seg, u_range=u_range, v_range=v_range, check_winding=True)

    def add_fin(
        self,
        root_x0: float,
        root_x1: float,
        tip_x0: float,
        tip_x1: float,
        r_root: float,
        span: float,
        angle_deg: float,
        thickness_root: float = 2.0,
        thickness_tip: float = 0.75,
        uv_rect=(0.02, 0.02, 0.98, 0.98),
        axis_offset=(0.0, 0.0, 0.0),
        sweep_stations: int = 4,
    ) -> None:
        """Build a solid 3D beveled swept rocket stabilizer fin mounted at `angle_deg` around X.

        `angle_deg`: 0 = +Y (left), 90 = +Z (top), 180 = -Y (right), 270 = -Z (bottom);
                     45/135/225/315 give X-configuration tail fins.
        `root_x0 < root_x1`: trailing-to-leading X at root; `tip_x0 < tip_x1`: trailing-to-leading X at tip.
        """
        ang = math.radians(angle_deg)
        rad_dir = np.array([0.0, math.cos(ang), math.sin(ang)], dtype=np.float64)
        lat_dir = np.array([0.0, -math.sin(ang), math.cos(ang)], dtype=np.float64)
        ofs = np.asarray(axis_offset, dtype=np.float64)
        u0, v0, u1, v1 = uv_rect

        # 6-point hexagonal beveled airfoil cross-section around chord (0=TE, 1=LE)
        # Order goes around perimeter: TE -> +side aft -> +side fore -> LE -> -side fore -> -side aft
        sec_t = [0.00, 0.22, 0.78, 1.00, 0.78, 0.22]
        sec_w = [0.00, 0.50, 0.50, 0.00, -0.50, -0.50]
        sec_u = [0.00, 0.25, 0.75, 1.00, 0.75, 0.25]
        n_sec = len(sec_t)

        n_st = max(2, sweep_stations)
        verts = []
        uvs = []
        for si in range(n_st):
            f = si / float(n_st - 1)
            r_cur = r_root + span * f
            x_te = root_x0 * (1.0 - f) + tip_x0 * f
            x_le = root_x1 * (1.0 - f) + tip_x1 * f
            thk = thickness_root * (1.0 - f) + thickness_tip * f
            vv = v0 + (v1 - v0) * f
            for pi in range(n_sec):
                x = x_te + (x_le - x_te) * sec_t[pi]
                pt = ofs + np.array([x, 0.0, 0.0]) + rad_dir * r_cur + lat_dir * (thk * sec_w[pi])
                verts.append(pt)
                uvs.append((u0 + (u1 - u0) * sec_u[pi], vv))

        tris = []
        for si in range(n_st - 1):
            b0 = si * n_sec
            b1 = (si + 1) * n_sec
            for pi in range(n_sec):
                pn = (pi + 1) % n_sec
                tris.append((b0 + pi, b0 + pn, b1 + pn))
                tris.append((b0 + pi, b1 + pn, b1 + pi))

        # Cap root (si=0) and tip (si=n_st-1) cleanly
        root_ctr_idx = len(verts)
        root_pts = np.asarray(verts[:n_sec], dtype=np.float64)
        verts.append(root_pts.mean(axis=0))
        uvs.append((0.5 * (u0 + u1), v0))
        for pi in range(n_sec):
            pn = (pi + 1) % n_sec
            tris.append((root_ctr_idx, pn, pi))

        tip_base = (n_st - 1) * n_sec
        tip_ctr_idx = len(verts)
        tip_pts = np.asarray(verts[tip_base : tip_base + n_sec], dtype=np.float64)
        verts.append(tip_pts.mean(axis=0))
        uvs.append((0.5 * (u0 + u1), v1))
        for pi in range(n_sec):
            pn = (pi + 1) % n_sec
            tris.append((tip_ctr_idx, tip_base + pi, tip_base + pn))

        ctr = ofs + np.array([0.25 * (root_x0 + root_x1 + tip_x0 + tip_x1), 0.0, 0.0]) + rad_dir * (r_root + 0.5 * span)
        self.add_mesh(verts, tris, uvs, verify_center=ctr)

    def add_tube(
        self,
        points,
        radii,
        n_seg: int = 12,
        uv_rect=(0.02, 0.02, 0.98, 0.98),
        cap_ends: bool = True,
    ) -> None:
        """Sweep a smooth circular tube along a 3D polyline using twist-free parallel-transport frames."""
        pts = [np.asarray(p, dtype=np.float64) for p in points]
        n_p = len(pts)
        assert n_p >= 2
        if isinstance(radii, (int, float)):
            rads = [float(radii)] * n_p
        else:
            rads = [float(r) for r in radii]
            assert len(rads) == n_p

        u0, v0, u1, v1 = uv_rect
        tangents = []
        for i in range(n_p):
            if i == 0:
                t = _unit(pts[1] - pts[0])
            elif i == n_p - 1:
                t = _unit(pts[-1] - pts[-2])
            else:
                t = _unit(_unit(pts[i + 1] - pts[i]) + _unit(pts[i] - pts[i - 1]), fallback=_unit(pts[i + 1] - pts[i]))
            tangents.append(t)

        # Parallel-transport normal frame along polyline
        t0, n_cur, b_cur = _basis_from_axis(tangents[0])
        frames = [(t0, n_cur, b_cur)]
        for i in range(1, n_p):
            ti = tangents[i]
            proj = n_cur - ti * float(np.dot(n_cur, ti))
            if float(np.linalg.norm(proj)) < 1e-6:
                _, n_cur, b_cur = _basis_from_axis(ti)
            else:
                n_cur = _unit(proj)
                b_cur = _unit(np.cross(ti, n_cur))
            frames.append((ti, n_cur, b_cur))

        verts = []
        uvs = []
        for i in range(n_p):
            vv = v0 + (v1 - v0) * (i / float(n_p - 1))
            _, ni, bi = frames[i]
            ri = rads[i]
            for si in range(n_seg + 1):
                uf = si / float(n_seg)
                ang = 2.0 * math.pi * uf
                pt = pts[i] + (ni * math.cos(ang) + bi * math.sin(ang)) * ri
                verts.append(pt)
                uvs.append((u0 + (u1 - u0) * uf, vv))

        stride = n_seg + 1
        tris = []
        for i in range(n_p - 1):
            r0 = i * stride
            r1 = (i + 1) * stride
            for si in range(n_seg):
                a, b = r0 + si, r0 + si + 1
                c, d = r1 + si + 1, r1 + si
                tris.append((a, b, c))
                tris.append((a, c, d))

        if cap_ends:
            c0 = len(verts)
            verts.append(pts[0])
            uvs.append((0.5 * (u0 + u1), v0))
            for si in range(n_seg):
                tris.append((c0, si + 1, si))
            c1 = len(verts)
            verts.append(pts[-1])
            uvs.append((0.5 * (u0 + u1), v1))
            last_r = (n_p - 1) * stride
            for si in range(n_seg):
                tris.append((c1, last_r + si, last_r + si + 1))

        ctr = np.mean(pts, axis=0)
        self.add_mesh(verts, tris, uvs, verify_center=ctr if cap_ends else None)

    def add_ring_band(
        self,
        x_center: float,
        radius: float,
        width: float = 3.0,
        height: float = 0.85,
        n_seg: int = 28,
        axis_offset=(0.0, 0.0, 0.0),
        uv_rect=(0.02, 0.02, 0.98, 0.98),
        rivets: int = 0,
        rivet_radius: float = 0.55,
    ) -> None:
        """Machined clamp collar / reinforcing strap band around the fuselage, with optional 3D dome rivets."""
        hw = width * 0.5
        bv = min(width * 0.18, height * 0.6)
        r_in = max(0.1, radius - 0.15)
        r_out = radius + height
        prof = [
            (x_center - hw, r_in, 0.00),
            (x_center - hw + bv, r_out, 0.18),
            (x_center + hw - bv, r_out, 0.82),
            (x_center + hw, r_in, 1.00),
            (x_center - hw, r_in, 1.00),
        ]
        u0, v0, u1, v1 = uv_rect
        self.add_lathe_x(prof, n_seg=n_seg, axis_offset=axis_offset, u_range=(u0, u1), v_range=(v0, v1), check_winding=True)
        if rivets > 0:
            ox, oy, oz = axis_offset
            for k in range(rivets):
                ang = 2.0 * math.pi * (k / float(rivets))
                rc = (
                    ox + x_center,
                    oy + (r_out + rivet_radius * 0.25) * math.cos(ang),
                    oz + (r_out + rivet_radius * 0.25) * math.sin(ang),
                )
                self.add_sphere(rc, rivet_radius, rivet_radius, rivet_radius, n_seg=8, n_rings=5, uv_rect=uv_rect)

    def add_box(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        uv_rect=(0.02, 0.02, 0.98, 0.98),
        R: np.ndarray | None = None,
        offset=(0.0, 0.0, 0.0),
    ) -> None:
        """Add an axis-aligned solid box with separate per-face UVs & crisp hard edges."""
        u0, v0, u1, v1 = uv_rect
        faces = [
            # (+X front)
            [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            # (-X back)
            [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            # (+Y left)
            [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            # (-Y right)
            [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            # (+Z top)
            [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            # (-Z bottom)
            [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        ]
        verts, uvs, tris = [], [], []
        for quad in faces:
            b = len(verts)
            verts.extend(quad)
            uvs.extend([(u0, v1), (u1, v1), (u1, v0), (u0, v0)])
            tris.extend([(b + 0, b + 1, b + 2), (b + 0, b + 2, b + 3)])
        ctr = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
        self.add_mesh(verts, tris, uvs, verify_center=ctr, R=R, offset=offset)

    def add_sphere(
        self,
        center,
        rx: float,
        ry: float | None = None,
        rz: float | None = None,
        n_seg: int = 16,
        n_rings: int = 10,
        uv_rect=(0.02, 0.02, 0.98, 0.98),
    ) -> None:
        """Add an ellipsoid / rivet / dome centered at `center`."""
        ry = rx if ry is None else ry
        rz = rx if rz is None else rz
        cx, cy, cz = center
        u0, v0, u1, v1 = uv_rect
        verts, uvs = [], []
        for ri in range(n_rings + 1):
            vf = ri / float(n_rings)
            phi = -0.5 * math.pi + math.pi * vf
            cp, sp = math.cos(phi), math.sin(phi)
            vv = v0 + (v1 - v0) * (1.0 - vf)
            for si in range(n_seg + 1):
                uf = si / float(n_seg)
                th = 2.0 * math.pi * uf
                verts.append((cx + rx * cp * math.cos(th), cy + ry * cp * math.sin(th), cz + rz * sp))
                uvs.append((u0 + (u1 - u0) * uf, vv))
        stride = n_seg + 1
        tris = []
        for ri in range(n_rings):
            r0, r1 = ri * stride, (ri + 1) * stride
            for si in range(n_seg):
                a, b = r0 + si, r0 + si + 1
                c, d = r1 + si + 1, r1 + si
                if ri > 0:
                    tris.append((a, b, c))
                if ri < n_rings - 1:
                    tris.append((a, c, d))
        self.add_mesh(verts, tris, uvs, verify_center=center)

    def finalize(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return `(verts, norms, uvs, tris)` as contiguous numpy arrays."""
        if not self._verts:
            raise ValueError(f"Surface '{self.name}' is empty")
        va = np.vstack(self._verts).astype(np.float32)
        na = np.vstack(self._norms).astype(np.float32)
        ua = np.vstack(self._uvs).astype(np.float32)
        ta = np.vstack(self._tris).astype(np.int32)
        return va, na, ua, ta


# ===========================================================================
# ADDITIVE FLAME TEXTURE & ANIMATED MULTI-NOZZLE FLAME BUILDER
# ===========================================================================

def _value_noise_2d(h: int, w: int, grid_y: int, grid_x: int, rng: np.random.Generator) -> np.ndarray:
    """Deterministic bilinear tileable value noise using pure numpy (no scipy)."""
    g = rng.uniform(0.0, 1.0, (grid_y, grid_x)).astype(np.float32)
    ys = np.linspace(0.0, grid_y, h, endpoint=False, dtype=np.float32)
    xs = np.linspace(0.0, grid_x, w, endpoint=False, dtype=np.float32)
    y0 = np.floor(ys).astype(np.int32) % grid_y
    x0 = np.floor(xs).astype(np.int32) % grid_x
    y1 = (y0 + 1) % grid_y
    x1 = (x0 + 1) % grid_x
    fy = ys - np.floor(ys)
    fx = xs - np.floor(xs)
    fy = fy * fy * (3.0 - 2.0 * fy)
    fx = fx * fx * (3.0 - 2.0 * fx)
    c00 = g[y0[:, None], x0[None, :]]
    c10 = g[y0[:, None], x1[None, :]]
    c01 = g[y1[:, None], x0[None, :]]
    c11 = g[y1[:, None], x1[None, :]]
    top = c00 * (1.0 - fx[None, :]) + c10 * fx[None, :]
    bot = c01 * (1.0 - fx[None, :]) + c11 * fx[None, :]
    return (top * (1.0 - fy[:, None]) + bot * fy[:, None]).astype(np.float32)


def make_flame_texture(path: Path | str, style: str = "classic", size: int = 512) -> Path:
    """Generate a deterministic 512x512 RGB additive flame atlas fading cleanly to pure (0,0,0) at edges/tips.

    Atlas layout (4 quadrants, v=0 top -> v=1 bottom):
      Q1 (u 0.0..0.5, v 0.0..0.5): Outer turbulent exhaust cone (v=0 nozzle -> v=0.5 tip fade)
      Q2 (u 0.5..1.0, v 0.0..0.5): Inner white-gold/cyan Mach shock-diamond core
      Q3 (u 0.0..0.5, v 0.5..1.0): Crossed longitudinal flame fin card (feathered on all 4 edges)
      Q4 (u 0.5..1.0, v 0.5..1.0): Supersonic slipstream speed ribbons (feathered on all 4 edges)

    Styles: `"classic"` (Quake molten orange-gold), `"cartoon"` (vibrant ACME red-yellow), `"plasma"` (cobalt-cyan afterburner).
    """
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    H = W = int(size)
    half = H // 2

    seed_map = {"classic": 1996, "cartoon": 2001, "plasma": 3003}
    if style not in seed_map:
        raise ValueError(f"Unknown flame style '{style}'; expected one of {list(seed_map)}")
    rng = np.random.default_rng(seed_map[style])

    # Multi-octave deterministic noise
    n1 = _value_noise_2d(half, half, 8, 12, rng)
    n2 = _value_noise_2d(half, half, 20, 28, rng)
    turb = 0.65 * n1 + 0.35 * n2

    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, half, dtype=np.float32),
        np.linspace(0.0, 1.0, half, dtype=np.float32),
        indexing="ij",
    )

    # Style color ramps (outer_hot, outer_mid, outer_tip, core_hot, core_edge, ribbon_col)
    if style == "classic":
        c_hot = np.array([1.00, 0.94, 0.68], dtype=np.float32)
        c_mid = np.array([1.00, 0.52, 0.10], dtype=np.float32)
        c_tip = np.array([0.85, 0.16, 0.02], dtype=np.float32)
        c_core = np.array([1.00, 0.98, 0.86], dtype=np.float32)
        c_core_ring = np.array([1.00, 0.72, 0.22], dtype=np.float32)
        c_rib = np.array([1.00, 0.82, 0.50], dtype=np.float32)
    elif style == "cartoon":
        c_hot = np.array([1.00, 1.00, 0.78], dtype=np.float32)
        c_mid = np.array([1.00, 0.62, 0.04], dtype=np.float32)
        c_tip = np.array([0.96, 0.14, 0.02], dtype=np.float32)
        c_core = np.array([1.00, 1.00, 0.92], dtype=np.float32)
        c_core_ring = np.array([1.00, 0.86, 0.15], dtype=np.float32)
        c_rib = np.array([1.00, 0.94, 0.62], dtype=np.float32)
    else:  # "plasma"
        c_hot = np.array([0.88, 0.98, 1.00], dtype=np.float32)
        c_mid = np.array([0.20, 0.74, 1.00], dtype=np.float32)
        c_tip = np.array([0.28, 0.22, 0.95], dtype=np.float32)
        c_core = np.array([0.96, 0.99, 1.00], dtype=np.float32)
        c_core_ring = np.array([0.45, 0.88, 1.00], dtype=np.float32)
        c_rib = np.array([0.55, 0.92, 1.00], dtype=np.float32)

    atlas = np.zeros((H, W, 3), dtype=np.float32)

    # --- Q1: Outer turbulent exhaust cone (v=0 root -> v=1 faded tip, periodic in u) ---
    root_in = _smoothstep(0.0, 0.06, yy)
    tip_out = (1.0 - _smoothstep(0.18, 0.96, yy)) ** 1.35
    streaks = 0.68 + 0.32 * np.sin(xx * 2.0 * math.pi * 6.0 + turb * 4.2 + yy * 5.0)
    flk = (0.76 + 0.38 * turb) * streaks
    q1_env = np.clip(root_in * tip_out * flk, 0.0, 1.0)
    w_hot = np.exp(-((yy / 0.26) ** 1.7))
    w_mid = np.exp(-(((yy - 0.35) / 0.34) ** 2))
    q1_col = (
        c_tip[None, None, :] * (1.0 - w_mid)[..., None]
        + c_mid[None, None, :] * w_mid[..., None]
    )
    q1_col = q1_col * (1.0 - w_hot)[..., None] + c_hot[None, None, :] * w_hot[..., None]
    atlas[:half, :half] = q1_col * q1_env[..., None]

    # --- Q2: Inner Mach shock-diamond core (periodic pulsing diamonds along v) ---
    diamonds = 0.55 + 0.45 * (np.cos((yy * 4.5 - 0.2) * 2.0 * math.pi) ** 2)
    q2_root = _smoothstep(0.0, 0.05, yy)
    q2_tip = (1.0 - _smoothstep(0.15, 0.94, yy)) ** 1.6
    q2_env = np.clip(q2_root * q2_tip * diamonds * (0.85 + 0.15 * np.sin(xx * 2.0 * math.pi * 4.0)), 0.0, 1.0)
    w_d = np.clip(diamonds ** 1.5 * np.exp(-((yy / 0.58) ** 1.6)), 0.0, 1.0)
    q2_col = c_core_ring[None, None, :] * (1.0 - w_d)[..., None] + c_core[None, None, :] * w_d[..., None]
    atlas[:half, half:] = q2_col * q2_env[..., None]

    # --- Q3: Crossed flame fin card (centered at u=0.5, feathered smoothly to 0 on ALL 4 borders!) ---
    dx = np.abs(xx - 0.5) * 2.0  # 0 at center, 1 at left/right edges
    # Width narrows smoothly toward flame tip (yy -> 1)
    half_w = np.maximum(0.06, 0.86 * (1.0 - 0.80 * (yy ** 1.25)) * (0.88 + 0.18 * np.sin(yy * 14.0 + turb * 3.5)))
    lat_mask = np.clip(1.0 - (dx / half_w) ** 1.8, 0.0, 1.0)
    # Hard safety border fade to exact 0.0 on all 4 edges
    border_u = _smoothstep(0.02, 0.12, xx) * (1.0 - _smoothstep(0.88, 0.98, xx))
    border_v = _smoothstep(0.02, 0.09, yy) * (1.0 - _smoothstep(0.85, 0.97, yy))
    core_stripe = np.exp(-((dx / np.maximum(0.05, half_w * 0.42)) ** 2)) * np.exp(-((yy / 0.45) ** 1.6))
    q3_env = np.clip(lat_mask * border_u * border_v * (0.78 + 0.30 * turb), 0.0, 1.0)
    q3_col = (
        c_tip[None, None, :] * (1.0 - _smoothstep(0.0, 0.65, 1.0 - yy))[..., None]
        + c_mid[None, None, :] * _smoothstep(0.0, 0.65, 1.0 - yy)[..., None]
    )
    q3_col = q3_col * (1.0 - core_stripe)[..., None] + c_core[None, None, :] * core_stripe[..., None]
    atlas[half:, :half] = q3_col * q3_env[..., None]

    # --- Q4: Supersonic slipstream speed ribbons (feathered smoothly to 0 on ALL 4 edges!) ---
    r_lat = np.exp(-(((xx - 0.5) / 0.24) ** 2)) * _smoothstep(0.04, 0.18, xx) * (1.0 - _smoothstep(0.82, 0.96, xx))
    r_lon = _smoothstep(0.03, 0.20, yy) * (1.0 - _smoothstep(0.45, 0.96, yy)) ** 1.4
    r_core = np.exp(-(((xx - 0.5) / 0.10) ** 2))
    r_env = np.clip(r_lat * r_lon * (0.80 + 0.20 * np.sin(yy * 18.0)), 0.0, 1.0)
    r_col = c_rib[None, None, :] * (1.0 - 0.5 * r_core)[..., None] + np.array([1.0, 1.0, 1.0])[None, None, :] * (0.5 * r_core)[..., None]
    atlas[half:, half:] = r_col * r_env[..., None]

    # Guarantee pure black 2px outer border & cross-seam divider so bilinear filtering never leaks across quadrants!
    atlas[:2, :] = 0.0
    atlas[-2:, :] = 0.0
    atlas[:, :2] = 0.0
    atlas[:, -2:] = 0.0
    atlas[half - 2 : half + 2, :] = 0.0
    atlas[:, half - 2 : half + 2] = 0.0

    img = Image.fromarray(np.clip(np.rint(atlas * 255.0), 0, 255).astype(np.uint8), mode="RGB")
    img.save(dst, "PNG", optimize=True)
    return dst


class FlameBuilder:
    """Multi-nozzle animated additive exhaust flame + Mach core + crossed cards + slipstream ribbons."""

    def __init__(
        self,
        n_nozzles: int = 1,
        n_seg: int = 14,
        n_rings: int = 8,
        n_cards: int = 4,
        n_ribbons: int = 6,
    ):
        self.n_nozzles = int(n_nozzles)
        self.n_seg = int(n_seg)
        self.n_rings = int(n_rings)
        self.n_cards = int(n_cards)
        self.n_ribbons = int(n_ribbons)
        self.uvs, self.tris = self._build_topology()

    def _build_topology(self) -> tuple[np.ndarray, np.ndarray]:
        uvs: list[tuple[float, float]] = []
        tris: list[tuple[int, int, int]] = []

        # Helper to append a grid mesh (n_r rings x (n_s+1) cols)
        def add_grid(n_r: int, n_s: int, u0: float, v0: float, u1: float, v1: float, closed_tip: bool = True):
            base = len(uvs)
            for ri in range(n_r):
                vf = ri / float(n_r - 1)
                vv = v0 + (v1 - v0) * vf
                for si in range(n_s + 1):
                    uf = si / float(n_s)
                    uvs.append((u0 + (u1 - u0) * uf, vv))
            stride = n_s + 1
            for ri in range(n_r - 1):
                r0 = base + ri * stride
                r1 = base + (ri + 1) * stride
                for si in range(n_s):
                    a, b = r0 + si, r0 + si + 1
                    c, d = r1 + si + 1, r1 + si
                    tris.append((a, b, c))
                    if not (closed_tip and ri == n_r - 2):
                        tris.append((a, c, d))

        core_rings = max(5, self.n_rings - 1)
        core_segs = max(8, self.n_seg - 4)

        for _ in range(self.n_nozzles):
            # 1. Outer exhaust cone -> Q1 (u 0.02..0.48, v 0.02..0.48)
            add_grid(self.n_rings, self.n_seg, 0.02, 0.02, 0.48, 0.48, closed_tip=True)
            # 2. Inner Mach shock-diamond core -> Q2 (u 0.52..0.98, v 0.02..0.48)
            add_grid(core_rings, core_segs, 0.52, 0.02, 0.98, 0.48, closed_tip=True)
            # 3. Crossed longitudinal flame fin cards -> Q3 (u 0.02..0.48, v 0.52..0.98)
            for _c in range(self.n_cards):
                base = len(uvs)
                for ri in range(self.n_rings):
                    vf = ri / float(self.n_rings - 1)
                    vv = 0.52 + 0.46 * vf
                    uvs.append((0.03, vv))
                    uvs.append((0.47, vv))
                for ri in range(self.n_rings - 1):
                    b0 = base + ri * 2
                    b1 = b0 + 2
                    tris.append((b0, b0 + 1, b1 + 1))
                    tris.append((b0, b1 + 1, b1))

        # 4. Optional slipstream speed ribbons -> Q4 (u 0.52..0.98, v 0.52..0.98)
        rib_rings = 9
        for _r in range(self.n_ribbons):
            base = len(uvs)
            for ri in range(rib_rings):
                vf = ri / float(rib_rings - 1)
                vv = 0.53 + 0.44 * vf
                uvs.append((0.54, vv))
                uvs.append((0.96, vv))
            for ri in range(rib_rings - 1):
                b0 = base + ri * 2
                b1 = b0 + 2
                tris.append((b0, b0 + 1, b1 + 1))
                tris.append((b0, b1 + 1, b1))

        return np.asarray(uvs, dtype=np.float32), np.asarray(tris, dtype=np.int32)

    def eval_frame(self, nozzle_specs: list[dict[str, Any]], ribbon_specs: list[dict[str, Any]] | None = None) -> np.ndarray:
        """Evaluate all flame + ribbon vertex positions for one frame.

        Each nozzle dict supports:
          - `origin`: `(x, y, z)` nozzle exit
          - `dir`: `(dx, dy, dz)` exhaust direction (default `(-1, 0, 0)`)
          - `length`: float plume length (Quake units)
          - `radius`: float base plume radius
          - `flicker_phase`: float periodic phase `0..2*pi`
          - `intensity`: float `0.0..2.0` (scales sway/core fullness; `<= 0` collapses cleanly)
          - `ribbons_alpha`: float `0.0..1.0` (`<= 0.01` collapses slipstream ribbons to zero area)
        """
        assert len(nozzle_specs) == self.n_nozzles, f"Expected {self.n_nozzles} nozzles, got {len(nozzle_specs)}"
        verts: list[np.ndarray] = []
        core_rings = max(5, self.n_rings - 1)
        core_segs = max(8, self.n_seg - 4)

        for ni, ns in enumerate(nozzle_specs):
            org = np.asarray(ns["origin"], dtype=np.float64)
            ax, b1, b2 = _basis_from_axis(ns.get("dir", (-1.0, 0.0, 0.0)))
            length = max(0.0, float(ns.get("length", 32.0)))
            radius = max(0.0, float(ns.get("radius", 8.0)))
            ph = float(ns.get("flicker_phase", 0.0)) + ni * 1.35
            inten = max(0.0, float(ns.get("intensity", 1.0)))

            if inten <= 1e-4 or length <= 1e-4 or radius <= 1e-4:
                # Collapse cleanly to origin (zero area)
                n_noz_v = (
                    self.n_rings * (self.n_seg + 1)
                    + core_rings * (core_segs + 1)
                    + self.n_cards * self.n_rings * 2
                )
                verts.append(np.repeat(org[None, :], n_noz_v, axis=0))
                continue

            # 1. Outer turbulent plume cone
            outer_pts = []
            for ri in range(self.n_rings):
                t = ri / float(self.n_rings - 1)
                # Natural rocket plume silhouette: widens slightly right out of nozzle then tapers to flame tip
                prof = (0.68 + 0.42 * math.sin(min(1.0, t * 1.45) * math.pi * 0.72)) * ((1.0 - t) ** 0.72)
                if ri == self.n_rings - 1:
                    prof = 0.0
                # High-frequency periodic harmonic flicker & subtle tip whip
                pulse = 1.0 + 0.09 * min(1.4, inten) * math.sin(2.0 * ph - 5.2 * t)
                sway1 = radius * 0.14 * min(1.4, inten) * (t ** 1.4) * math.sin(ph - 4.0 * t)
                sway2 = radius * 0.12 * min(1.4, inten) * (t ** 1.4) * math.cos(2.0 * ph - 3.6 * t)
                c_pt = org + ax * (length * t) + b1 * sway1 + b2 * sway2
                r_cur = radius * prof * pulse
                for si in range(self.n_seg + 1):
                    ang = 2.0 * math.pi * (si / float(self.n_seg))
                    wob = 1.0 + 0.08 * (t ** 0.8) * math.sin(3.0 * ang + ph - 5.0 * t)
                    outer_pts.append(c_pt + (b1 * math.cos(ang) + b2 * math.sin(ang)) * (r_cur * wob))
            verts.append(np.asarray(outer_pts, dtype=np.float64))

            # 2. Inner Mach shock-diamond core
            core_pts = []
            core_len = length * (0.58 + 0.10 * min(1.5, inten))
            core_rad = radius * 0.50
            for ri in range(core_rings):
                t = ri / float(core_rings - 1)
                diamond = 1.0 + 0.24 * math.sin(t * 3.5 * 2.0 * math.pi - ph)
                prof = (0.78 * ((1.0 - t) ** 0.65)) * diamond
                if ri == core_rings - 1:
                    prof = 0.0
                c_pt = org + ax * (core_len * t)
                r_cur = core_rad * max(0.0, prof)
                for si in range(core_segs + 1):
                    ang = 2.0 * math.pi * (si / float(core_segs))
                    core_pts.append(c_pt + (b1 * math.cos(ang) + b2 * math.sin(ang)) * r_cur)
            verts.append(np.asarray(core_pts, dtype=np.float64))

            # 3. Crossed longitudinal flame fin cards (full volume from side/top/rear)
            card_pts = []
            card_len = length * 1.08
            card_hw = radius * 1.18
            for ci in range(self.n_cards):
                c_ang = math.pi * (ci / float(self.n_cards))
                c_dir = b1 * math.cos(c_ang) + b2 * math.sin(c_ang)
                c_perp = -b1 * math.sin(c_ang) + b2 * math.cos(c_ang)
                for ri in range(self.n_rings):
                    t = ri / float(self.n_rings - 1)
                    hw = card_hw * (0.72 + 0.36 * math.sin(min(1.0, t * 1.35) * math.pi * 0.78)) * ((1.0 - 0.88 * t) ** 0.6)
                    hw *= 1.0 + 0.10 * math.sin(2.0 * ph - 4.8 * t + ci * 1.2)
                    sw = radius * 0.14 * (t ** 1.45) * math.sin(ph - 4.0 * t + ci * 0.7)
                    c_pt = org + ax * (card_len * t) + c_perp * sw
                    card_pts.append(c_pt - c_dir * hw)
                    card_pts.append(c_pt + c_dir * hw)
            verts.append(np.asarray(card_pts, dtype=np.float64))

        # 4. Optional slipstream speed ribbons (active in fly_boost / skypad_hyper, zero-area otherwise)
        if self.n_ribbons > 0:
            rib_rings = 9
            n0 = nozzle_specs[0]
            org0 = np.asarray(n0["origin"], dtype=np.float64)
            ax0, b10, b20 = _basis_from_axis(n0.get("dir", (-1.0, 0.0, 0.0)))
            r_alpha = max(float(ns.get("ribbons_alpha", 0.0)) for ns in nozzle_specs)
            ph0 = float(n0.get("flicker_phase", 0.0))
            rad0 = max(10.0, float(n0.get("radius", 10.0)))

            if r_alpha <= 0.01:
                verts.append(np.repeat(org0[None, :], self.n_ribbons * rib_rings * 2, axis=0))
            else:
                rib_pts = []
                for ri_idx in range(self.n_ribbons):
                    if ribbon_specs is not None and ri_idx < len(ribbon_specs):
                        rs = ribbon_specs[ri_idx]
                        r_ang = math.radians(float(rs.get("angle_deg", ri_idx * (360.0 / self.n_ribbons))))
                        r_dist = float(rs.get("ring_radius", rad0 * 2.2))
                        x_lead = float(rs.get("lead_offset", -52.0))  # negative along ax0 = forward toward nose
                        r_len = float(rs.get("length", 68.0)) * (0.55 + 0.45 * r_alpha)
                        r_hw = float(rs.get("half_width", 2.2)) * r_alpha
                    else:
                        r_ang = 2.0 * math.pi * ((ri_idx + 0.25) / float(self.n_ribbons))
                        r_dist = rad0 * (2.15 + 0.35 * (ri_idx % 2))
                        x_lead = -48.0 - 12.0 * (ri_idx % 3)
                        r_len = (58.0 + 18.0 * (ri_idx % 2)) * (0.55 + 0.45 * r_alpha)
                        r_hw = 2.1 * r_alpha

                    rad_v = b10 * math.cos(r_ang) + b20 * math.sin(r_ang)
                    tan_v = -b10 * math.sin(r_ang) + b20 * math.cos(r_ang)
                    # Periodic scroll back along exhaust axis ax0
                    scroll = ((ph0 / (2.0 * math.pi)) + ri_idx * 0.29) % 1.0
                    shift_ax = (scroll - 0.5) * 18.0
                    for k in range(rib_rings):
                        t = k / float(rib_rings - 1)
                        dist_cur = r_dist * (1.0 + 0.18 * t) + 1.4 * math.sin(ph0 - 4.0 * t + ri_idx)
                        c_pt = org0 + ax0 * (x_lead + shift_ax + r_len * t) + rad_v * dist_cur
                        hw = r_hw * math.sin(t * math.pi) ** 0.55
                        rib_pts.append(c_pt - tan_v * hw)
                        rib_pts.append(c_pt + tan_v * hw)
                verts.append(np.asarray(rib_pts, dtype=np.float64))

        return np.vstack(verts).astype(np.float32)


def make_animated_flame_surface(
    frame_nozzle_specs: list[list[dict[str, Any]]],
    surface_name: str = "rocket_flame",
    shader_name: str = "progs/rr_flame",
    tex_filename: str = "flame.png",
    ribbon_specs: list[dict[str, Any]] | None = None,
    n_seg: int = 14,
    n_rings: int = 8,
    n_cards: int = 4,
    n_ribbons: int = 6,
) -> dict[str, Any]:
    """Build a complete 100-frame additive flame surface dict ready for `export_variant(...)`."""
    assert len(frame_nozzle_specs) == TOTAL_FRAMES, f"Expected {TOTAL_FRAMES} frames, got {len(frame_nozzle_specs)}"
    n_nozzles = len(frame_nozzle_specs[0])
    fb = FlameBuilder(
        n_nozzles=n_nozzles,
        n_seg=n_seg,
        n_rings=n_rings,
        n_cards=n_cards,
        n_ribbons=n_ribbons,
    )
    frames = [fb.eval_frame(ns, ribbon_specs=ribbon_specs) for ns in frame_nozzle_specs]
    return {
        "name": surface_name,
        "shader": shader_name,
        "tex": tex_filename,
        "tris": fb.tris,
        "uvs": fb.uvs,
        "frames": frames,
        "unlit": 1,
        "additive": 1,
        "twoSided": 1,
        "role": "flame",
        "metallic": 0.0,
        "roughness": 1.0,
        "spec": 0.0,
    }


# ===========================================================================
# GROUNDING & UNIFIED VARIANT EXPORTER
# ===========================================================================

def ground_idle_frames(
    surfaces: list[dict[str, Any]],
    idle_start: int = 56,
    idle_count: int = 12,
    target_z_min: float = 0.0,
) -> float:
    """Shift `idle_ground` frames (56..67) across ALL surfaces in-place so the lowest solid vertex sits at `target_z_min`.

    Returns the Z shift applied (in Quake units).
    """
    solid_z_mins = []
    for s in surfaces:
        if s.get("additive", 0):
            continue
        for fi in range(idle_start, idle_start + idle_count):
            fr = s["frames"][fi]
            vv = fr[0] if isinstance(fr, tuple) else fr
            solid_z_mins.append(float(np.asarray(vv, dtype=np.float32)[:, 2].min()))
    if not solid_z_mins:
        return 0.0
    dz = float(target_z_min - min(solid_z_mins))
    if abs(dz) < 1e-6:
        return 0.0
    shift = np.array([0.0, 0.0, dz], dtype=np.float32)
    for s in surfaces:
        frames = s["frames"]
        for fi in range(idle_start, idle_start + idle_count):
            fr = frames[fi]
            if isinstance(fr, tuple):
                frames[fi] = (np.asarray(fr[0], dtype=np.float32) + shift, fr[1])
            else:
                frames[fi] = np.asarray(fr, dtype=np.float32) + shift
    return dz


def _write_variant_shader(shader_path: Path, variant_id: str, surfaces_meta: list[dict[str, Any]], shaders: list[str]) -> None:
    shader_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"// Rocket Rider variant shader ({variant_id}) - generated by source/mm_tools/rocket_rider/common.py\n"]
    seen: set[str] = set()
    for sm, sh in zip(surfaces_meta, shaders):
        if sh in seen:
            continue
        seen.add(sh)
        tex_stem = Path(sm["tex"]).stem
        map_path = f"progs/{tex_stem}"
        if sm.get("additive", 0):
            lines.append(
                f"{sh}\n"
                "{\n"
                "\tcull none\n"
                "\t{\n"
                f"\t\tmap {map_path}\n"
                "\t\tblendfunc add\n"
                "\t\trgbGen identity\n"
                "\t}\n"
                "}\n"
            )
        else:
            rgb_gen = "identity" if sm.get("unlit", 0) else "lightingDiffuse"
            block = (
                f"{sh}\n"
                "{\n"
                "\tcull none\n"
                "\t{\n"
                f"\t\tmap {map_path}\n"
                f"\t\trgbGen {rgb_gen}\n"
                "\t}\n"
            )
            if sm.get("glowTex"):
                glow_stem = Path(sm["glowTex"]).stem
                block += (
                    "\t{\n"
                    f"\t\tmap progs/{glow_stem}\n"
                    "\t\tblendfunc add\n"
                    "\t\trgbGen identity\n"
                    "\t}\n"
                )
            block += "}\n"
            lines.append(block)
    shader_path.write_text("\n".join(lines), encoding="ascii", newline="\n")


def export_variant(
    variant_id: str,
    short_label: str,
    title: str,
    subtitle: str,
    accent: str,
    surfaces: list[dict[str, Any]],
    mix_chips: list[str],
    notes: list[str],
    cam_defaults: dict[str, Any] | None = None,
    out_dir: Path | str = OUT_DIR,
    clips: list[dict[str, Any]] | None = None,
    auto_ground_idle: bool = True,
) -> dict[str, Any]:
    """Validate, write MD3 + `.md3_0.skin` + `.shader` + `_meta.json`, and run full round-trip verification.

    Args:
        variant_id: e.g. `"v1_classic"`, `"v2_acme"`, `"v3_twin"`.
        short_label: e.g. `"V1"`, `"V2"`, `"V3"`.
        title, subtitle, accent: display metadata for the vote UI.
        surfaces: list of surface dicts `{name, tex, tris, uvs, frames, shader?, unlit?, additive?, glowTex?, metallic?, roughness?, spec?}`.
        mix_chips: feature mix-and-match tags for the vote page.
        notes: concise bullet notes describing design & animation details.
        cam_defaults: optional `{yaw, pitch, dist, target}`.
        out_dir: output directory (default `OUT_DIR`).
        clips: clip table (default `CLIPS`).
        auto_ground_idle: if True, shifts frames `56..67` so lowest solid vertex touches `Z = 0.0`.
    """
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    clips_use = CLIPS if clips is None else clips
    expected_nf = sum(c["count"] for c in clips_use)
    assert expected_nf == TOTAL_FRAMES, f"Expected {TOTAL_FRAMES} total frames, got {expected_nf}"

    # Verify textures exist before writing MD3
    for s in surfaces:
        tex_p = out_root / s["tex"]
        if not tex_p.is_file():
            raise FileNotFoundError(f"Missing texture for surface '{s['name']}': {tex_p}")
        if s.get("glowTex"):
            glow_p = out_root / s["glowTex"]
            if not glow_p.is_file():
                raise FileNotFoundError(f"Missing glowTex for surface '{s['name']}': {glow_p}")

    # Optionally snap idle_ground frames (56..67) so lowest solid vertex sits at Z = 0.0
    idle_clip = next((c for c in clips_use if c["id"] == "idle_ground"), None)
    if auto_ground_idle and idle_clip is not None:
        ground_idle_frames(surfaces, idle_start=idle_clip["start"], idle_count=idle_clip["count"], target_z_min=0.0)

    # Frame names
    frame_names: list[str] = []
    for clip in clips_use:
        for k in range(clip["count"]):
            frame_names.append(f"{clip['id']}_{k:02d}")

    md3_surfs = []
    surfaces_meta = []
    shader_names = []
    skin_lines = []
    tot_verts = 0
    tot_tris = 0

    for s in surfaces:
        sname = s["name"]
        shader = s.get("shader") or f"progs/rr_{variant_id}_{sname}"
        tris_np = np.asarray(s["tris"], dtype=np.int32)
        uvs_np = np.asarray(s["uvs"], dtype=np.float32)
        frames_in = s["frames"]

        nv = len(uvs_np)
        nt = len(tris_np)
        assert len(frames_in) == TOTAL_FRAMES, f"Surface '{sname}' has {len(frames_in)} frames (expected {TOTAL_FRAMES})"
        assert 0 < nv < HARD_MD3_VERTS, f"Surface '{sname}' nv={nv} must be in (0, {HARD_MD3_VERTS})"
        assert 0 < nt < HARD_MD3_TRIS, f"Surface '{sname}' nt={nt} must be in (0, {HARD_MD3_TRIS})"

        tot_verts += nv
        tot_tris += nt

        frames_md3 = []
        for fi, fr in enumerate(frames_in):
            if isinstance(fr, tuple):
                vv_np = np.asarray(fr[0], dtype=np.float32)
                nn_np = np.asarray(fr[1], dtype=np.float32)
            else:
                vv_np = np.asarray(fr, dtype=np.float32)
                nn_np = compute_vertex_normals(vv_np, tris_np)
            assert vv_np.shape == (nv, 3), f"Surface '{sname}' frame {fi} verts shape {vv_np.shape} != ({nv}, 3)"
            assert np.isfinite(vv_np).all() and np.isfinite(nn_np).all(), f"NaN/Inf in {sname} frame {fi}"
            max_abs = float(np.max(np.abs(vv_np)))
            assert max_abs < 500.0, f"Surface '{sname}' frame {fi} max |coord|={max_abs:.1f} >= 500u MD3 limit!"
            frames_md3.append((vv_np.tolist(), nn_np.tolist()))

        md3_surfs.append(
            {
                "name": sname,
                "shader": shader,
                "tris": tris_np.tolist(),
                "st": uvs_np.tolist(),
                "frames": frames_md3,
            }
        )
        skin_lines.append(f"{sname},{shader}")
        shader_names.append(shader)

        s_meta: dict[str, Any] = {
            "name": sname,
            "tex": s["tex"],
            "unlit": int(bool(s.get("unlit", 0))),
            "additive": int(bool(s.get("additive", 0))),
        }
        if s.get("glowTex"):
            s_meta["glowTex"] = s["glowTex"]
        if "metallic" in s:
            s_meta["metallic"] = float(s["metallic"])
        if "roughness" in s:
            s_meta["roughness"] = float(s["roughness"])
        if "spec" in s:
            s_meta["spec"] = float(s["spec"])
        if "twoSided" in s:
            s_meta["twoSided"] = int(bool(s["twoSided"]))
        if "role" in s:
            s_meta["role"] = str(s["role"])
        surfaces_meta.append(s_meta)

    md3_rel = f"{variant_id}.md3"
    skin_rel = f"{variant_id}.md3_0.skin"
    shader_rel = f"scripts/{variant_id}.shader"
    meta_rel = f"{variant_id}_meta.json"

    md3_path = out_root / md3_rel
    skin_path = out_root / skin_rel
    shader_path = out_root / shader_rel
    meta_path = out_root / meta_rel

    md3lib.write(
        str(md3_path),
        {
            "name": f"progs/rr_{variant_id}.md3",
            "surfaces": md3_surfs,
            "frame_names": frame_names,
        },
    )
    skin_path.write_text("\n".join(skin_lines) + "\n", encoding="ascii", newline="\n")
    _write_variant_shader(shader_path, variant_id, surfaces_meta, shader_names)

    # Full MD3 round-trip verification
    rt = md3lib.read(str(md3_path))
    assert rt["nframes"] == TOTAL_FRAMES, f"Round-trip nframes={rt['nframes']} != {TOTAL_FRAMES}"
    assert len(rt["surfaces"]) == len(surfaces), f"Round-trip surface count mismatch"

    fly_pts = []
    idle_pts = []
    fly_clip = clips_use[0]
    for s_rt, sm in zip(rt["surfaces"], surfaces_meta):
        nv_rt = len(s_rt["st"])
        nt_rt = len(s_rt["tris"])
        assert 0 < nv_rt < HARD_MD3_VERTS and 0 < nt_rt < HARD_MD3_TRIS
        all_v = np.asarray([fr[0] for fr in s_rt["frames"]], dtype=np.float32)
        all_n = np.asarray([fr[1] for fr in s_rt["frames"]], dtype=np.float32)
        assert np.isfinite(all_v).all() and np.isfinite(all_n).all(), f"NaN/Inf in round-trip {s_rt['name']}"
        assert float(np.max(np.abs(all_v))) < 500.0, f"Round-trip {s_rt['name']} exceeds +-500u"
        if not sm["additive"]:
            fly_pts.append(all_v[fly_clip["start"] : fly_clip["start"] + fly_clip["count"]].reshape(-1, 3))
            if idle_clip is not None:
                idle_pts.append(all_v[idle_clip["start"] : idle_clip["start"] + idle_clip["count"]].reshape(-1, 3))

    fly_cat = np.vstack(fly_pts)
    bounds_fly = {
        "min": [round(float(x), 2) for x in fly_cat.min(axis=0)],
        "max": [round(float(x), 2) for x in fly_cat.max(axis=0)],
    }
    if idle_pts:
        idle_cat = np.vstack(idle_pts)
        z_min_idle = float(idle_cat[:, 2].min())
        assert -0.5 <= z_min_idle <= 0.5, f"idle_ground solid z_min={z_min_idle:.3f} outside [-0.5, +0.5]!"
        bounds_idle = {
            "min": [round(float(x), 2) for x in idle_cat.min(axis=0)],
            "max": [round(float(x), 2) for x in idle_cat.max(axis=0)],
        }
    else:
        bounds_idle = bounds_fly

    if cam_defaults is None:
        cam_defaults = {"yaw": -35, "pitch": 18, "dist": 175, "target": [0, 0, 32]}

    meta = {
        "id": variant_id,
        "short_label": short_label,
        "title": title,
        "subtitle": subtitle,
        "accent": accent,
        "md3_path": md3_rel,
        "skin_path": skin_rel,
        "shader_path": shader_rel,
        "surfaces": surfaces_meta,
        "clips": clips_use,
        "stats": {
            "verts": tot_verts,
            "tris": tot_tris,
            "frames": TOTAL_FRAMES,
            "surfaces": len(surfaces_meta),
            "bounds_fly": bounds_fly,
            "bounds_idle": bounds_idle,
        },
        "mix_chips": list(mix_chips),
        "notes": list(notes),
        "cam_defaults": cam_defaults,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"[OK] Exported {variant_id}: {md3_path.name} ({md3_path.stat().st_size:,} B) | "
        f"{len(surfaces_meta)} surfs, {tot_verts}v, {tot_tris}t, 100f | "
        f"idle z_min={bounds_idle['min'][2]:.2f}",
        flush=True,
    )
    return meta


# ===========================================================================
# SELF-TEST (run `python source/mm_tools/rocket_rider/common.py`)
# ===========================================================================

def _run_self_test() -> None:
    import shutil
    import tempfile

    print("=== Rocket Rider common.py self-test ===", flush=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="rr_selftest_"))
    try:
        # 1. Ranger texture + Rig pose math, outward normals, limb accuracy & continuity
        tex_p = ensure_ranger_texture(tmp_dir / "ranger_skin.png")
        im = Image.open(tex_p)
        assert im.size == (592, 388), f"Unexpected ranger_skin size {im.size}"
        print(f"  [1] Ranger skin OK: {im.size} PNG ({tex_p.stat().st_size:,} B)")

        rig = QuakeRangerRig()
        # Check neutral and several Rocket Rider straddle poses (cruise, boost, dive, hyper)
        test_poses = [
            (
                "cruise_straddle",
                dict(
                    hip_pos=(-6.0, 0.0, 14.0),
                    torso_pitch=24.0,
                    head_pitch=-4.0,
                    l_hand=(18.0, 11.0, 26.0),
                    r_hand=(18.0, -11.0, 26.0),
                    l_elbow_hint=(4.0, 16.5, 22.0),
                    r_elbow_hint=(4.0, -16.5, 22.0),
                    l_knee=(7.0, 13.5, 7.5),
                    r_knee=(7.0, -13.5, 7.5),
                    l_foot=(-3.0, 15.0, -5.0),
                    r_foot=(-3.0, -15.0, -5.0),
                    scale=1.18,
                    lean_x=2.0,
                ),
            ),
            (
                "swoop_tuck",
                dict(
                    hip_pos=(-8.0, 0.0, 13.5),
                    torso_pitch=42.0,
                    head_pitch=-10.0,
                    l_hand=(22.0, 9.5, 22.0),
                    r_hand=(22.0, -9.5, 22.0),
                    l_elbow_hint=(8.0, 15.0, 19.0),
                    r_elbow_hint=(8.0, -15.0, 19.0),
                    l_knee=(6.0, 13.0, 6.0),
                    r_knee=(6.0, -13.0, 6.0),
                    l_foot=(-6.0, 14.5, -4.5),
                    r_foot=(-6.0, -14.5, -4.5),
                    scale=1.18,
                    lean_x=3.5,
                ),
            ),
            (
                "skypad_pinned_back",
                dict(
                    hip_pos=(-10.0, 0.0, 14.0),
                    torso_pitch=-22.0,
                    torso_roll=6.0,
                    head_pitch=-6.0,
                    l_hand=(16.0, 10.5, 24.0),
                    r_hand=(16.0, -10.5, 24.0),
                    l_elbow_hint=(0.0, 16.0, 25.0),
                    r_elbow_hint=(0.0, -16.0, 25.0),
                    l_knee=(6.0, 14.0, 7.0),
                    r_knee=(6.0, -14.0, 7.0),
                    l_foot=(-5.0, 15.5, -4.5),
                    r_foot=(-5.0, -15.5, -4.5),
                    scale=1.18,
                    lean_x=-3.5,
                ),
            ),
        ]

        # Measure max edge length in rest pose (straightened axstnd1 * 1.18) for stretch check
        rest_v = np.asarray([rig._vs17[vi] for vi in rig._md3_src_vi], dtype=np.float32) * 1.18
        e_pairs = np.vstack([rig.tris[:, [0, 1]], rig.tris[:, [1, 2]], rig.tris[:, [2, 0]]])
        rest_elens = np.linalg.norm(rest_v[e_pairs[:, 0]] - rest_v[e_pairs[:, 1]], axis=1)
        max_rest_edge = float(rest_elens.max())

        for pname, kwargs in test_poses:
            V = rig.pose_frame(**kwargs)
            vol = signed_mesh_volume(V, rig.tris)
            assert vol > 2500.0, f"{pname}: signed volume {vol:.1f} not strongly positive (inverted normals?)"

            # Per-part outward dot check (face normal vs part-centroid -> face vector)
            v0, v1, v2 = V[rig.tris[:, 0]], V[rig.tris[:, 1]], V[rig.tris[:, 2]]
            fn = np.cross(v1 - v0, v2 - v0)
            fc = (v0 + v1 + v2) / 3.0
            c_all = V.mean(axis=0)
            pct_out = float((np.einsum("ij,ij->i", fc - c_all, fn) > 0).mean() * 100.0)
            assert pct_out > 60.0, f"{pname}: outward face dot ratio too low ({pct_out:.1f}%)"

            # Target accuracy (< 2.0u)
            lh_err = float(np.linalg.norm(rig.hand_centroid(V, "l_arm") - np.asarray(kwargs["l_hand"])))
            rh_err = float(np.linalg.norm(rig.hand_centroid(V, "r_arm") - np.asarray(kwargs["r_hand"])))
            lf_err = float(np.linalg.norm(rig.foot_centroid(V, "l_leg") - np.asarray(kwargs["l_foot"])))
            rf_err = float(np.linalg.norm(rig.foot_centroid(V, "r_leg") - np.asarray(kwargs["r_foot"])))
            assert max(lh_err, rh_err, lf_err, rf_err) < 2.0, (
                f"{pname}: hand/foot target error too large: Lh={lh_err:.2f} Rh={rh_err:.2f} Lf={lf_err:.2f} Rf={rf_err:.2f}"
            )

            # Stretch check: no detached or exploded triangles
            cur_elens = np.linalg.norm(V[e_pairs[:, 0]] - V[e_pairs[:, 1]], axis=1)
            max_edge = float(cur_elens.max())
            assert max_edge < max(26.0, max_rest_edge * 1.9), f"{pname}: stretched edge {max_edge:.2f}u"
            print(
                f"  [2] Pose '{pname:18s}': vol=+{vol:6.1f} out={pct_out:4.1f}% "
                f"err(Lh={lh_err:.2f}, Rh={rh_err:.2f}, Lf={lf_err:.2f}, Rf={rf_err:.2f}) max_edge={max_edge:.1f}u"
            )

        # 2. Flame textures (all 3 styles) & pure-black border verification
        for st in ("classic", "cartoon", "plasma"):
            fp = make_flame_texture(tmp_dir / f"flame_{st}.png", style=st)
            arr = np.asarray(Image.open(fp))
            assert arr.shape == (512, 512, 3)
            assert arr[0].max() == 0 and arr[-1].max() == 0 and arr[:, 0].max() == 0 and arr[:, -1].max() == 0
            assert arr.max() > 220, f"Flame texture '{st}' too dim!"
        print("  [3] All 3 flame textures OK (512x512 RGB, pure-black 2px borders, bright cores)")

        # 3. Dummy Rocket + Ranger + Multi-Nozzle Flame 100-frame MD3 export round-trip
        sb = SurfBuilder("rocket_body", "progs/rr_selftest_body")
        sb.add_lathe_x(
            [(-44.0, 0.0), (-44.0, 11.0), (-36.0, 13.0), (24.0, 13.0), (42.0, 7.5), (54.0, 0.0)],
            n_seg=24,
        )
        sb.add_nozzle_bell((-44.0, 0.0, 0.0), (-1.0, 0.0, 0.0), r_throat=6.5, r_exit=10.0, length=12.0, n_seg=20)
        for ang in (45.0, 135.0, 225.0, 315.0):
            sb.add_fin(-44.0, -20.0, -48.0, -34.0, r_root=11.5, span=14.0, angle_deg=ang)
        sb.add_ring_band(10.0, 13.0, width=3.0, height=0.8, rivets=8)
        sb.add_tube([(16.0, -11.5, 25.0), (18.0, 0.0, 27.0), (16.0, 11.5, 25.0)], [1.1, 1.2, 1.1], n_seg=10)
        sb.add_box(-14.0, -2.0, -6.5, 6.5, 11.5, 14.2)
        rb_v, _, rb_u, rb_t = sb.finalize()
        rb_vol = signed_mesh_volume(rb_v, rb_t)
        assert rb_vol > 10000.0, f"Dummy rocket body signed volume {rb_vol:.1f} not positive!"

        # Write dummy solid rocket texture
        Image.new("RGB", (64, 64), (160, 70, 40)).save(tmp_dir / "dummy_rocket.png", "PNG")

        rocket_frames = []
        ranger_frames = []
        flame_nozzles = []
        for fi, clip, k, u, ph, _fname in iter_clip_frames():
            cid = clip["id"]
            if cid == "idle_ground":
                pitch, roll, z_off, f_len, r_alp = 0.0, 0.0, 24.0, 8.0, 0.0
            elif cid == "skypad_hyper":
                pitch, roll, z_off, f_len, r_alp = 10.0, 4.0 * math.sin(ph), 34.0 + 2.0 * math.sin(ph), 78.0, 1.0
            elif cid == "fly_boost":
                pitch, roll, z_off, f_len, r_alp = -4.0, 3.0 * math.sin(ph), 32.0 + 1.5 * math.sin(ph), 58.0, 0.65
            elif cid == "swoop_dive":
                pitch, roll, z_off, f_len, r_alp = -22.0, 2.0 * math.sin(ph), 30.0, 44.0, 0.25
            elif cid == "fly_hover":
                pitch, roll, z_off, f_len, r_alp = 20.0, 2.5 * math.sin(ph), 35.0 + 4.0 * math.sin(ph), 34.0, 0.0
            elif cid == "hit_flail":
                pitch, roll, z_off, f_len, r_alp = 12.0 * math.sin(2.0 * ph), 22.0 * math.cos(ph), 32.0 + 3.0 * math.sin(3.0 * ph), 22.0, 0.0
            else:
                pitch, roll, z_off, f_len, r_alp = 2.0 * math.cos(ph), 3.0 * math.sin(ph), 32.0 + 2.5 * math.sin(ph), 38.0, 0.0

            rv = apply_vehicle_xform(rb_v, offset=(0.0, 0.0, z_off), pitch_deg=pitch, roll_deg=roll)
            rocket_frames.append(rv)

            r_loc = rig.pose_frame(
                hip_pos=(-6.0, 0.0, 14.0),
                torso_pitch=22.0 + 4.0 * math.sin(ph),
                l_hand=(16.5, 10.5, 25.2),
                r_hand=(16.5, -10.5, 25.2),
                l_knee=(6.0, 13.5, 7.0),
                r_knee=(6.0, -13.5, 7.0),
                l_foot=(-3.0, 14.5, -5.0),
                r_foot=(-3.0, -14.5, -5.0),
            )
            ranger_frames.append(apply_vehicle_xform(r_loc, offset=(0.0, 0.0, z_off), pitch_deg=pitch, roll_deg=roll))

            R_v = euler_mat(pitch_deg=pitch, roll_deg=roll)
            noz_org = (np.array([-55.5, 0.0, 0.0], dtype=np.float32) @ R_v.T) + np.array([0.0, 0.0, z_off], dtype=np.float32)
            noz_dir = np.array([-1.0, 0.0, 0.0], dtype=np.float32) @ R_v.T
            flame_nozzles.append([
                dict(origin=noz_org, dir=noz_dir, length=f_len, radius=9.2, flicker_phase=ph, intensity=1.0, ribbons_alpha=r_alp)
            ])

        flame_surf = make_animated_flame_surface(
            flame_nozzles,
            surface_name="rocket_flame",
            shader_name="progs/rr_selftest_flame",
            tex_filename="flame_classic.png",
        )
        surfs = [
            {"name": "rocket_body", "tex": "dummy_rocket.png", "tris": rb_t, "uvs": rb_u, "frames": rocket_frames},
            {"name": "ranger", "tex": "ranger_skin.png", "tris": rig.tris, "uvs": rig.uvs, "frames": ranger_frames},
            flame_surf,
        ]
        meta = export_variant(
            variant_id="selftest_dummy",
            short_label="TEST",
            title="Self-Test Dummy Rocket",
            subtitle="Round-trip verification",
            accent="#ff7b29",
            surfaces=surfs,
            mix_chips=["Dummy Chip"],
            notes=["Self-test note"],
            out_dir=tmp_dir,
        )
        assert meta["stats"]["frames"] == 100
        assert abs(meta["stats"]["bounds_idle"]["min"][2]) < 0.05
        assert (tmp_dir / "selftest_dummy.md3").is_file()
        assert (tmp_dir / "selftest_dummy.md3_0.skin").is_file()
        assert (tmp_dir / "scripts" / "selftest_dummy.shader").is_file()
        assert (tmp_dir / "selftest_dummy_meta.json").is_file()
        print(
            f"  [4] Dummy MD3 round-trip OK: {meta['stats']['verts']}v/{meta['stats']['tris']}t, "
            f"rocket_vol=+{rb_vol:.0f}, fly_z={meta['stats']['bounds_fly']['min'][2]}..{meta['stats']['bounds_fly']['max'][2]}, "
            f"idle_z={meta['stats']['bounds_idle']['min'][2]}..{meta['stats']['bounds_idle']['max'][2]}"
        )
        print("=== ALL SELF-TESTS PASSED! ===", flush=True)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    _run_self_test()
