"""Shared code for the Rob Dob view model tools (make_robdob_tuner.py, apply_robdob_vm.py).

progs/v_robdob.mdl bakes the hand pose into its vertices: frames 0-7 bob, frame 8 is 'gone' (the head dropped 45 units).
The pose comes from build_floathead.py's VM_* constants, so a finished mdl can be un-posed (back to a head centred on the
origin, face along +x, up +z) and re-posed without the turntable video the full build needs.

Orientation: v' = Rz(yaw) . Ry(pitch) . Rx(roll) . v  -- roll about the face axis (x), nod about the head's side axis (y,
+ = face tips up), turn about the vertical (z).  Quake axes: x forward, y left, z up.
"""
import math
import os
import re
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FLOATHEAD_PY = os.path.join(HERE, "build_floathead.py")
MDL = r"G:\Quake\Combat\BakersfieldQuake\progs\v_robdob.mdl"
ANORMS = r"D:\vibe\quake1opensource\idsrc\WinQuake\anorms.h"
GONE_DROP = np.array([0.0, 0.0, -45.0])          # frame 8 is the head with this added


def rx(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def rz(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def orient_matrix(yaw, pitch=0.0, roll=0.0):
    return rz(yaw) @ ry(pitch) @ rx(roll)


def orient(V, yaw, pitch=0.0, roll=0.0):
    return np.asarray(V) @ orient_matrix(yaw, pitch, roll).T


def current():
    """the pose build_floathead.py is set to (what the mdl on disk was last built with)"""
    t = open(FLOATHEAD_PY, encoding="utf-8").read()
    num = r"(-?[0-9.]+)"
    pos = re.search(r"^VM_POS\s*=\s*\(\s*%s\s*,\s*%s\s*,\s*%s\s*\)" % ((num,) * 3), t, re.M)
    one = lambda name, default: float(re.search(r"^%s\s*=\s*%s" % (name, num), t, re.M).group(1)) \
        if re.search(r"^%s\s*=\s*%s" % (name, num), t, re.M) else default
    return dict(pos=[float(g) for g in pos.groups()], yaw=one("VM_YAW", 0.0), pitch=one("VM_PITCH", 0.0),
                roll=one("VM_ROLL", 0.0), height=one("VM_HEIGHT", 9.0))


def read(path=MDL):
    d = open(path, "rb").read()
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale, tr = np.array(h[2:5]), np.array(h[5:8])
    nsk, sw, sh, nv, nt, nf = h[12:18]
    o = 84 + nsk * (4 + sw * sh)
    st = np.frombuffer(d, "<i4", nv * 3, o).reshape(nv, 3)
    o += nv * 12
    tri = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)[:, 1:]
    o += nt * 16
    frames_at = o
    frames = []
    for _ in range(nf):
        name = d[o + 12:o + 28].split(b"\0")[0].decode()
        v = np.frombuffer(d, np.uint8, nv * 4, o + 28).reshape(nv, 4)
        frames.append((name, v[:, :3] * scale + tr, v[:, 3].copy()))
        o += 28 + nv * 4
    assert o == len(d), (o, len(d))
    return dict(raw=d, head=h, sw=sw, sh=sh, nv=nv, st=st[:, 1:], tri=tri, frames=frames, frames_at=frames_at)


def head_mask(md):
    """True for head vertices (top 256 skin rows), False for the fedora & accessories (rows 256..383)."""
    return md["st"][:, 1] < 256


def head_local(md, cur=None):
    """frame 8 un-posed: the head (+ hat) centred on the head's origin, face along +x, at head height 1"""
    cur = cur or current()
    g = md["frames"][8][1] - np.array(cur["pos"]) - GONE_DROP
    L = g @ orient_matrix(cur["yaw"], cur["pitch"], cur["roll"])          # inverse of v @ R.T
    return L / cur["height"]


def bob_locals(md, cur=None):
    """frames 0..7 un-posed into head-local height-1 space (preserving any local nod / fedora-tip animation)"""
    cur = cur or current()
    R = orient_matrix(cur["yaw"], cur["pitch"], cur["roll"])
    out = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        g = md["frames"][i][1] - np.array(cur["pos"]) - np.array([0.0, 0.0, 0.35 * math.sin(a)])
        g = g @ rz(4 * math.sin(a + 1.0))                                 # inverse of v @ rz.T
        out.append((g @ R) / cur["height"])
    return out


def pose_frames(L, pos, yaw, pitch, roll, height, bobs=None):
    """the nine frames (name, vertices) for a head L (height 1) held at this pose; same bob as build_floathead.py"""
    head = orient(L * height, yaw, pitch, roll)
    out = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        bi = orient(bobs[i] * height, yaw, pitch, roll) if bobs is not None else head
        out.append(("bob%d" % (i + 1), orient(bi, 4 * math.sin(a + 1.0)) + np.array(pos) + [0, 0, 0.35 * math.sin(a)]))
    out.append(("gone", head + np.array(pos) + GONE_DROP))
    return out


def anorms():
    nums = re.findall(r"\{\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*\}", open(ANORMS).read())
    a = np.array(nums, float)
    assert len(a) == 162, len(a)
    return a


def vertex_normals(md, P, A):
    """index into the anorms table for every mdl vertex of positions P: face normals averaged over each point's copies"""
    key = np.round(md["frames"][0][1], 3)
    _, uid = np.unique(key, axis=0, return_inverse=True)
    uid = uid.reshape(-1)
    T = md["tri"]
    fn = np.cross(P[T[:, 2]] - P[T[:, 0]], P[T[:, 1]] - P[T[:, 0]])
    n = np.zeros((uid.max() + 1, 3))
    for j in range(3):
        np.add.at(n, uid[T[:, j]], fn)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    centre = P.mean(0)
    if np.mean(np.sum(n[uid] * (P - centre), 1)) < 0:                    # tris are clockwise from outside: flip
        n = -n
    return (n @ A.T).argmax(1).astype(np.uint8)[uid]


def write(md, frames, path=MDL):
    """rewrite the mdl with new positions for its nine frames; skin, texture coordinates and triangles stay"""
    d = bytearray(md["raw"])
    P = np.array([f[1] for f in frames])
    mn, mx = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    scale = (mx - mn) / 255.0
    h = list(md["head"])
    h[2:5], h[5:8], h[8] = scale, mn, float(np.linalg.norm(P, axis=2).max())
    struct.pack_into("<4si3f3ff", d, 0, h[0], h[1], *h[2:9])
    A = anorms()
    o = md["frames_at"]
    for name, pos in frames:
        q = np.rint((pos - mn) / scale).clip(0, 255).astype(np.uint8)
        ni = vertex_normals(md, pos, A)
        d[o + 4:o + 8] = bytes(list(q.min(0)) + [0])
        d[o + 8:o + 12] = bytes(list(q.max(0)) + [0])
        d[o + 12:o + 28] = name.encode("ascii")[:15].ljust(16, b"\0")
        d[o + 28:o + 28 + 4 * md["nv"]] = np.concatenate([q, ni[:, None]], 1).astype(np.uint8).tobytes()
        o += 28 + 4 * md["nv"]
    open(path, "wb").write(bytes(d))
