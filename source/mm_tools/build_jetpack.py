"""Procedural 3D Jetpack model for BakersfieldQuake, written into progs/ + scripts/:
  progs/jetpack.md3          multi-surface animated 3D jetpack (16 frames: frames 0-7 thrust, 8-15 standby idle)
  progs/jetpack_*.png        procedural PBR-style painted/brushed textures (authored for DarkPlaces lighting)
  scripts/jetpack.shader     unlit reactor/throat glow + scrolling additive shock-diamond exhaust plumes

Coordinate convention (Quake world / player back-attachment space):
  +X  forward (padded backplate & over-the-shoulder harness straps face +X to wrap a player's torso)
  -X  aft hero face (twin titanium propellant tanks, central plasma core, pressure dial, winglets)
  +Y  left / port,  -Y  right / starboard
  +Z  up (tank domes & valves at top, gimballed de Laval rocket bells & exhaust plumes below)

Usage:
    python3.13 source/mm_tools/build_jetpack.py [progs_dir]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")


# --------------------------------------------------------------------------- Vector & Frame Helpers
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def rot_x(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def frame_apply(f, p):
    o, X, Y, Z = f
    return (
        o[0] + X[0] * p[0] + Y[0] * p[1] + Z[0] * p[2],
        o[1] + X[1] * p[0] + Y[1] * p[1] + Z[1] * p[2],
        o[2] + X[2] * p[0] + Y[2] * p[1] + Z[2] * p[2],
    )


def frame_rot(f, n):
    return frame_apply(((0.0, 0.0, 0.0),) + tuple(f[1:]), n)


def frame_along(origin, axis, up_hint=(0.0, 0.0, 1.0)):
    """Right-handed frame whose local +X runs along axis, and local +Z leans toward up_hint."""
    X = norm(axis)
    if abs(dot(X, up_hint)) > 0.96:
        up_hint = (0.0, 1.0, 0.0) if abs(X[1]) < 0.9 else (1.0, 0.0, 0.0)
    Y = norm(cross(up_hint, X))
    Z = cross(X, Y)
    return (origin, X, Y, Z)


IDENT = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


# --------------------------------------------------------------------------- Tagged Multi-Material Mesh
class PartMesh:
    """Stores geometry grouped by (material, part_tag) so animated parts (nozzles, plumes) can move independently."""
    def __init__(self):
        self.parts = []  # list of dict(mat, tag, pivot, verts, norms, st, tris)

    def put(self, mat, verts, norms, st, tris, f=IDENT, tag="body", pivot=(0.0, 0.0, 0.0)):
        vv = [frame_apply(f, v) for v in verts]
        nn = [norm(frame_rot(f, n)) for n in norms]
        self.parts.append(dict(mat=mat, tag=tag, pivot=pivot, verts=vv, norms=nn, st=list(st), tris=list(tris)))


def smooth_normals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        n = cross(sub(verts[b], verts[a]), sub(verts[c], verts[a]))
        for i in (a, b, c):
            acc[i][0] += n[0]
            acc[i][1] += n[1]
            acc[i][2] += n[2]
    return [norm(a) for a in acc]


def lathe(mesh, mat, profile, f=IDENT, segs=20, sy=1.0, sz=1.0, a0=0.0, a1=360.0,
          ustretch=1.0, vflip=False, uv_rect=None, flat=False, tag="body", pivot=(0.0, 0.0, 0.0)):
    """Surface of revolution around local +X. Repeated profile points create crisp hard-edge normals."""
    cols = segs + 1
    xs = [p[0] for p in profile]
    x_min, span = min(xs), (max(xs) - min(xs)) or 1.0
    verts, st, tris = [], [], []
    for x, r in profile:
        t_v = (x - x_min) / span
        if vflip:
            t_v = 1.0 - t_v
        for j in range(cols):
            th = math.radians(a0 + (a1 - a0) * j / segs)
            verts.append((x, -math.sin(th) * r * sy, math.cos(th) * r * sz))
            u = (j / segs) * ustretch
            v = t_v
            if uv_rect is not None:
                u0, v0, u1, v1 = uv_rect
                u = u0 + (j / segs) * (u1 - u0)
                v = v0 + t_v * (v1 - v0)
            st.append((u, v))
    for i in range(len(profile) - 1):
        if profile[i] == profile[i + 1]:
            continue
        for j in range(segs):
            a = i * cols + j
            b, c, d = a + 1, a + cols, a + cols + 1
            tris.append((a, b, c))
            tris.append((b, d, c))
    if flat:
        uv_v, uv_s, uv_t = [], [], []
        for a, b, c in tris:
            for k in (a, b, c):
                uv_v.append(verts[k])
                uv_s.append(st[k])
            n = len(uv_v)
            uv_t.append((n - 3, n - 2, n - 1))
        verts, st, tris = uv_v, uv_s, uv_t
    norms = smooth_normals(verts, tris)
    mesh.put(mat, verts, norms, st, tris, f=f, tag=tag, pivot=pivot)


def disk(mesh, mat, radius, f=IDENT, segs=24, uv_rect=(0.0, 0.0, 1.0, 1.0), tag="body", pivot=(0.0, 0.0, 0.0)):
    """Flat circular face on local X=0 facing +X (local Y=left, local Z=up -> u right, v down)."""
    u0, v0, u1, v1 = uv_rect
    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
    ru, rv = 0.5 * (u1 - u0), 0.5 * (v1 - v0)
    verts = [(0.0, 0.0, 0.0)]
    norms = [(1.0, 0.0, 0.0)]
    st = [(uc, vc)]
    for j in range(segs + 1):
        th = 2.0 * math.pi * j / segs
        # Viewed from +X looking toward origin: -Y is right, +Z is up.
        # For CCW winding around +X: angle goes from -Y (+right) -> +Z (+up) -> +Y (-left) -> -Z (-down)
        y = -math.cos(th) * radius
        z = math.sin(th) * radius
        verts.append((0.0, y, z))
        norms.append((1.0, 0.0, 0.0))
        st.append((uc + math.cos(th) * ru, vc - math.sin(th) * rv))
    tris = [(0, j + 1, j + 2) for j in range(segs)]
    mesh.put(mat, verts, norms, st, tris, f=f, tag=tag, pivot=pivot)


def box(mesh, mat, lo, hi, f=IDENT, uvscale=0.1, uv_rect=None, tag="body", pivot=(0.0, 0.0, 0.0)):
    """Axis-aligned box in local frame f with crisp per-face normals."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    faces = [
        ((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
        ((-1, 0, 0), [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)]),
        ((0, 1, 0), [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)]),
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ((0, 0, -1), [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)]),
    ]
    verts, norms, st, tris = [], [], [], []
    local_uvs = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    for n, quad in faces:
        b = len(verts)
        for k, p in enumerate(quad):
            verts.append(p)
            norms.append(n)
            if uv_rect is not None:
                u0, v0, u1, v1 = uv_rect
                lu, lv = local_uvs[k]
                st.append((u0 + lu * (u1 - u0), v0 + lv * (v1 - v0)))
            elif n[0]:
                st.append((p[1] * uvscale, -p[2] * uvscale))
            elif n[1]:
                st.append((p[0] * uvscale, -p[2] * uvscale))
            else:
                st.append((p[0] * uvscale, p[1] * uvscale))
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    mesh.put(mat, verts, norms, st, tris, f=f, tag=tag, pivot=pivot)


def chamfer_box(mesh, mat, lo, hi, bev=0.35, f=IDENT, uvscale=0.09, tag="body"):
    """Octagonal-prism / bevelled block along Z (rounds the 4 vertical X/Y corners cleanly)."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    b = min(bev, 0.45 * (x1 - x0), 0.45 * (y1 - y0))
    ring = [
        (x1, y0 + b), (x1, y1 - b),
        (x1 - b, y1), (x0 + b, y1),
        (x0, y1 - b), (x0, y0 + b),
        (x0 + b, y0), (x1 - b, y0),
    ]
    m = len(ring)
    verts, st, tris = [], [], []
    # Side walls (CCW around +Z seen from outside)
    perim = [0.0]
    for i in range(m):
        nx, ny = ring[(i + 1) % m]
        cx, cy = ring[i]
        perim.append(perim[-1] + math.hypot(nx - cx, ny - cy))
    for i in range(m):
        p0 = ring[i]
        p1 = ring[(i + 1) % m]
        base = len(verts)
        quad = [(p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1)]
        uvs = [(perim[i] * uvscale, -z0 * uvscale), (perim[i + 1] * uvscale, -z0 * uvscale),
               (perim[i + 1] * uvscale, -z1 * uvscale), (perim[i] * uvscale, -z1 * uvscale)]
        verts += quad
        st += uvs
        tris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    # Top cap (+Z) & bottom cap (-Z)
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    bt = len(verts)
    verts.append((cx, cy, z1))
    st.append((cx * uvscale, cy * uvscale))
    for px, py in ring:
        verts.append((px, py, z1))
        st.append((px * uvscale, py * uvscale))
    for i in range(m):
        tris.append((bt, bt + 1 + i, bt + 1 + ((i + 1) % m)))

    bb = len(verts)
    verts.append((cx, cy, z0))
    st.append((cx * uvscale, cy * uvscale))
    for px, py in ring:
        verts.append((px, py, z0))
        st.append((px * uvscale, py * uvscale))
    for i in range(m):
        tris.append((bb, bb + 1 + ((i + 1) % m), bb + 1 + i))

    mesh.put(mat, verts, smooth_normals(verts, tris), st, tris, f=f, tag=tag)


def catmull_rom(ctrl, subdiv=6):
    """Smooth spline interpolation through 3D control points."""
    pts = []
    n = len(ctrl)
    for i in range(n - 1):
        p0 = ctrl[max(0, i - 1)]
        p1 = ctrl[i]
        p2 = ctrl[i + 1]
        p3 = ctrl[min(n - 1, i + 2)]
        steps = subdiv if i < n - 2 else subdiv + 1
        for s in range(steps):
            t = s / float(subdiv)
            t2, t3 = t * t, t * t * t
            c0 = -0.5 * t3 + t2 - 0.5 * t
            c1 = 1.5 * t3 - 2.5 * t2 + 1.0
            c2 = -1.5 * t3 + 2.0 * t2 + 0.5 * t
            c3 = 0.5 * t3 - 0.5 * t2
            pts.append((
                c0 * p0[0] + c1 * p1[0] + c2 * p2[0] + c3 * p3[0],
                c0 * p0[1] + c1 * p1[1] + c2 * p2[1] + c3 * p3[1],
                c0 * p0[2] + c1 * p1[2] + c2 * p2[2] + c3 * p3[2],
            ))
    return pts


def sweep_tube(mesh, mat, pts, r_y, r_z=None, segs=12, up_hint=(0.0, 0.0, 1.0),
               v_repeat=3.0, cap_ends=True, tag="body"):
    """Sweeps an elliptical cross-section along 3D polyline pts using parallel-transport frames."""
    if r_z is None:
        r_z = r_y
    m = len(pts)
    tangents = []
    for i in range(m):
        if i == 0:
            t = sub(pts[1], pts[0])
        elif i == m - 1:
            t = sub(pts[-1], pts[-2])
        else:
            t = sub(pts[i + 1], pts[i - 1])
        tangents.append(norm(t))

    # Initial normal & binormal: T x N = B (right-handed, matching lathe)
    t0 = tangents[0]
    uh = up_hint
    if abs(dot(t0, uh)) > 0.94:
        uh = (1.0, 0.0, 0.0) if abs(t0[0]) < 0.9 else (0.0, 1.0, 0.0)
    N = norm(cross(uh, t0))
    B = cross(t0, N)
    frames_nb = [(N, B)]
    arc = [0.0]
    for i in range(1, m):
        ti = tangents[i]
        N = norm(sub(N, mul(ti, dot(N, ti))))
        B = cross(ti, N)
        frames_nb.append((N, B))
        arc.append(arc[-1] + math.sqrt(dot(sub(pts[i], pts[i - 1]), sub(pts[i], pts[i - 1]))))
    total_len = arc[-1] or 1.0

    cols = segs + 1
    verts, st, tris = [], [], []

    def add_ring(pt, Ni, Bi, ry, rz, v_coord):
        for j in range(cols):
            th = 2.0 * math.pi * j / segs
            off = add(mul(Ni, -math.sin(th) * ry), mul(Bi, math.cos(th) * rz))
            verts.append(add(pt, off))
            st.append((j / float(segs), v_coord))

    if cap_ends:
        add_ring(pts[0], frames_nb[0][0], frames_nb[0][1], 0.0, 0.0, 0.0)
        add_ring(pts[0], frames_nb[0][0], frames_nb[0][1], r_y, r_z, 0.0)

    ring_start = 2 if cap_ends else 0
    for i in range(m):
        ry = r_y(i / (m - 1)) if callable(r_y) else r_y
        rz = r_z(i / (m - 1)) if callable(r_z) else r_z
        add_ring(pts[i], frames_nb[i][0], frames_nb[i][1], ry, rz, arc[i] / total_len * v_repeat)

    if cap_ends:
        ry_end = r_y(1.0) if callable(r_y) else r_y
        rz_end = r_z(1.0) if callable(r_z) else r_z
        add_ring(pts[-1], frames_nb[-1][0], frames_nb[-1][1], ry_end, rz_end, v_repeat)
        add_ring(pts[-1], frames_nb[-1][0], frames_nb[-1][1], 0.0, 0.0, v_repeat)

    total_rings = len(verts) // cols
    for i in range(total_rings - 1):
        # Skip duplicate hard-edge seam rings
        if i in (1, ring_start + m - 1) and cap_ends:
            continue
        for j in range(segs):
            a = i * cols + j
            b, c, d = a + 1, a + cols, a + cols + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    mesh.put(mat, verts, smooth_normals(verts, tris), st, tris, tag=tag)


def rod(mesh, mat, p0, p1, r, segs=10, tag="body", pivot=(0.0, 0.0, 0.0)):
    d = sub(p1, p0)
    L = math.sqrt(dot(d, d)) or 0.01
    lathe(
        mesh, mat,
        [(0, 0), (0, r), (0, r), (L, r), (L, r), (L, 0)],
        f=frame_along(p0, d), segs=segs, tag=tag, pivot=pivot,
    )


def build_winglet(mesh, side):
    """Swept aerodynamic dorsal stabilizer fin on outer side of tank (side = +1 left, -1 right)."""
    # Root at Y = side * 7.25, Tip at Y = side * 10.1
    y_root = side * 7.15
    y_tip = side * 10.05
    # 6-point airfoil loop in (X, Z) at root and tip
    # Chord runs from leading top (+Z) down-and-back; thickness in X
    def foil(xc, z0, z1, thick):
        zm = 0.5 * (z0 + z1)
        return [
            (xc + thick * 0.35, z1),               # top leading edge
            (xc + thick, zm + 0.15 * (z1 - z0)),   # front (+X) max camber
            (xc + thick * 0.3, z0),                # bottom edge front
            (xc - thick * 0.45, z0 - 0.2),         # bottom trailing corner
            (xc - thick, zm),                      # rear (-X) spine
            (xc - thick * 0.4, z1 - 0.15),         # top trailing corner
        ]

    root_loop = foil(-3.0, -1.6, 5.8, 0.52)
    tip_loop = foil(-4.15, -2.8, 2.2, 0.24)
    n = len(root_loop)

    verts, st, tris = [], [], []
    # Side skin quads: ensure outward CCW winding for both +Y and -Y sides!
    for i in range(n):
        j = (i + 1) % n
        r0, r1 = root_loop[i], root_loop[j]
        t0, t1 = tip_loop[i], tip_loop[j]
        b = len(verts)
        p_r0 = (r0[0], y_root, r0[1])
        p_r1 = (r1[0], y_root, r1[1])
        p_t1 = (t1[0], y_tip, t1[1])
        p_t0 = (t0[0], y_tip, t0[1])
        verts += [p_r0, p_r1, p_t1, p_t0]
        # U = 0 at root -> U = 1 at wingtip (so hazard stripe near U=0.72..1.0 sits cleanly on wingtip!)
        v0 = 1.0 - (i / float(n))
        v1 = 1.0 - ((i + 1) / float(n))
        st += [(0.05, v0), (0.05, v1), (0.98, v1), (0.98, v0)]
        # Check outward normal against cross product
        nrm = cross(sub(p_r1, p_r0), sub(p_t0, p_r0))
        # Midpoint relative to wing center (-3.5, 0.5*(y_root+y_tip), 1.5)
        mid = (0.25 * (p_r0[0] + p_r1[0] + p_t0[0] + p_t1[0]) + 3.5, 0.0,
               0.25 * (p_r0[2] + p_r1[2] + p_t0[2] + p_t1[2]) - 1.5)
        if dot(nrm, mid) >= 0:
            tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        else:
            tris += [(b, b + 2, b + 1), (b, b + 3, b + 2)]

    # Tip cap
    bt = len(verts)
    tc_x = sum(p[0] for p in tip_loop) / n
    tc_z = sum(p[1] for p in tip_loop) / n
    verts.append((tc_x, y_tip, tc_z))
    st.append((0.92, 0.5))
    for px, pz in tip_loop:
        verts.append((px, y_tip, pz))
        st.append((0.95, 0.5))
    for i in range(n):
        a, b2, c2 = bt, bt + 1 + i, bt + 1 + ((i + 1) % n)
        nrm = cross(sub(verts[b2], verts[a]), sub(verts[c2], verts[a]))
        if nrm[1] * side >= 0:
            tris.append((a, b2, c2))
        else:
            tris.append((a, c2, b2))

    mesh.put("wing", verts, smooth_normals(verts, tris), st, tris)

    # Wingtip torpedo pod + navigation strobe light (red on port/+Y, green on starboard/-Y)
    pod_f = frame_along((-4.9, y_tip, -0.3), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    # Nose (+X local is -X aft): run from front (+1.8) to aft (-1.6) along pod axis
    pod_front = frame_along((-2.8, y_tip, -0.3), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    lathe(mesh, "dark", [(0.0, 0.0), (0.35, 0.36), (0.8, 0.46), (2.9, 0.46), (3.2, 0.34), (3.2, 0.34)], pod_front, segs=12)
    strobe_uv = (0.04, 0.54, 0.46, 0.96) if side > 0 else (0.54, 0.54, 0.96, 0.96)
    lathe(mesh, "glow", [(3.2, 0.34), (3.55, 0.28), (3.72, 0.0)], pod_front, segs=12, uv_rect=strobe_uv)


# --------------------------------------------------------------------------- Complete Jetpack Assembly
def build_jetpack_parts():
    m = PartMesh()
    TANK_X = -3.0
    TANK_Y = 4.45
    TANK_R = 2.95

    # ==================== 1. TWIN PROPELLANT TANKS & GIMBALLED NOZZLES ====================
    for side in (-1, 1):
        ty = side * TANK_Y
        tag_noz = "nozL" if side > 0 else "nozR"
        tag_plume = "plumeL" if side > 0 else "plumeR"

        # Tank axis runs bottom -> top (+Z); up_hint=(+1,0,0) hides UV seam at +X (backplate)
        # so u=0.5 sits dead-center on the -X hero face!
        tf = frame_along((TANK_X, ty, -4.4), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))

        # Lower dome bulkhead (z = -4.4 .. -2.8 => local x = 0.0 .. 1.6)
        lathe(m, "metal", [
            (0.0, 0.0), (0.0, 1.55), (0.0, 1.55),
            (0.35, 1.85), (0.85, 2.52), (1.35, 2.86), (1.6, 2.95),
        ], tf, segs=24)

        # Main painted titanium cylinder (z = -2.8 .. +7.8 => local x = 1.6 .. 12.2)
        lathe(m, "tank", [(1.6, TANK_R), (12.2, TANK_R)], tf, segs=24, vflip=True)

        # Upper elliptical dome (z = +7.8 .. +10.4 => local x = 12.2 .. 14.8)
        dome_prof = [(12.2, TANK_R)]
        for k in range(1, 6):
            ang = (k / 5.0) * (math.pi * 0.44)
            dome_prof.append((12.2 + math.sin(ang) * 2.65, TANK_R * math.cos(ang)))
        lathe(m, "metal", dome_prof, tf, segs=24)

        # Top bleed valve assembly & knurled cap (local x = 14.75 .. 16.5 => z = +10.35 .. +12.1)
        r_top = dome_prof[-1][1]
        lathe(m, "dark", [
            (14.75, r_top), (14.75, 1.15), (14.75, 1.15),
            (15.35, 1.15), (15.35, 1.15), (15.35, 0.72),
        ], tf, segs=8, flat=True)
        lathe(m, "glow", [(15.35, 0.76), (15.62, 0.76)], tf, segs=16, uv_rect=(0.55, 0.55, 0.95, 0.95))
        lathe(m, "metal", [
            (15.62, 0.74), (15.62, 0.98), (15.62, 0.98),
            (16.25, 0.98), (16.45, 0.75), (16.45, 0.0),
        ], tf, segs=16)

        # Protective steel roll-bar guard hoop over each top valve
        guard_pts = catmull_rom([
            (TANK_X - 1.9, ty, 9.7),
            (TANK_X - 1.5, ty, 12.35),
            (TANK_X + 1.5, ty, 12.35),
            (TANK_X + 1.9, ty, 9.7),
        ], subdiv=6)
        sweep_tube(m, "dark", guard_pts, 0.24, segs=10, up_hint=(0.0, 1.0, 0.0))

        # Two heavy gunmetal clamping bands around each tank + hex bolts on rear face
        for z_band in (-1.4, 5.4):
            bx = z_band - (-4.4)
            lathe(m, "dark", [
                (bx, TANK_R), (bx, TANK_R + 0.24), (bx, TANK_R + 0.24),
                (bx + 1.05, TANK_R + 0.24), (bx + 1.05, TANK_R + 0.24), (bx + 1.05, TANK_R),
            ], tf, segs=28)
            # Twin hex bolt heads on rear/outer side of clamping ring
            for ang_deg in (148, 212):
                rad = math.radians(ang_deg)
                bp = (TANK_X + math.cos(rad) * (TANK_R + 0.2), ty + math.sin(rad) * (TANK_R + 0.2), z_band + 0.52)
                bdir = (math.cos(rad), math.sin(rad), 0.0)
                lathe(m, "metal", [(0, 0), (0, 0.28), (0, 0.28), (0.28, 0.28), (0.28, 0.28), (0.28, 0)],
                      frame_along(bp, bdir), segs=6, flat=True)

        # ---- Gimballed De Laval Rocket Nozzle (pivots at tank base z = -4.4) ----
        noz_pivot = (TANK_X, ty, -4.4)
        # Canted 5.5 deg outward (away from centerline) and 3 deg aft
        noz_dir = norm((-0.052, side * 0.096, -1.0))
        nf = frame_along(noz_pivot, noz_dir, (1.0, 0.0, 0.0))

        # Gimbal actuator collar + convergent throat + parabolic bell skirt
        lathe(m, "dark", [
            (0.0, 0.0), (0.0, 1.62), (0.0, 1.62),
            (0.55, 1.62), (0.85, 1.24),               # convergent section into throat
            (1.35, 1.16),                              # throat
            (2.05, 1.52), (2.95, 1.96), (3.95, 2.34), (4.85, 2.58),  # flared de Laval bell
            (4.85, 2.58), (4.85, 2.34),                # nozzle exit rim
            (4.25, 2.12),                              # dark lip step inside
        ], nf, segs=26, tag=tag_noz, pivot=noz_pivot)

        # Bright machined regenerative-cooling rings around nozzle exterior
        for rx, rr in ((1.22, 1.30), (2.55, 1.86), (3.85, 2.39)):
            lathe(m, "metal", [
                (rx, rr - 0.12), (rx, rr + 0.08), (rx, rr + 0.08),
                (rx + 0.24, rr + 0.08), (rx + 0.24, rr + 0.08), (rx + 0.24, rr - 0.08),
            ], nf, segs=20, tag=tag_noz, pivot=noz_pivot)

        # Glowing incandescent inner nozzle cavity & injector plate (visible from below/angles!)
        lathe(m, "glow", [
            (4.25, 2.12), (3.1, 1.62), (1.85, 1.08), (1.85, 1.08), (1.85, 0.0),
        ], nf, segs=24, uv_rect=(0.54, 0.04, 0.96, 0.46), tag=tag_noz, pivot=noz_pivot)

        # Two hydraulic gimbal actuator struts around each nozzle
        for s_ang in (-55, 125):
            ar = math.radians(s_ang)
            p_top = (TANK_X + math.cos(ar) * 2.25, ty + math.sin(ar) * 2.25, -3.7)
            p_bot = add(noz_pivot, add(mul(noz_dir, 2.5), (math.cos(ar) * 1.92, math.sin(ar) * 1.92, 0.0)))
            rod(m, "metal", p_top, p_bot, 0.17, segs=8, tag=tag_noz, pivot=noz_pivot)

        # ---- Supersonic Shock-Diamond Exhaust Plume (animated via tag_plume) ----
        plume_origin = add(noz_pivot, mul(noz_dir, 4.45))
        pf = frame_along(plume_origin, noz_dir, (1.0, 0.0, 0.0))
        # Outer soft plasma envelope cone (uses left half of plume texture u=0.02..0.48, v=0 nozzle -> v=1 tail fade)
        lathe(m, "plume", [
            (0.0, 1.05), (0.55, 2.25), (2.2, 2.38), (5.2, 1.95), (8.6, 1.25), (11.8, 0.35),
        ], pf, segs=18, uv_rect=(0.04, 0.0, 0.46, 1.0), tag=tag_plume, pivot=plume_origin)
        # Inner bright Mach shock-diamond core cone (uses right half u=0.54..0.96, hotter white-cyan core)
        lathe(m, "plume", [
            (0.0, 0.55), (0.65, 1.32), (2.3, 0.96), (4.0, 1.18), (6.2, 0.72), (9.2, 0.12),
        ], pf, segs=14, uv_rect=(0.54, 0.0, 0.96, 1.0), tag=tag_plume, pivot=plume_origin)
        # Crossed axial shock-diamond fins (soft lateral falloff across u=0.50..1.0)
        for fin_axis in ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
            fv, fn, fst, ftr = [], [], [], []
            hw = 2.35
            L_fin = 11.4
            for ix, xf in enumerate((0.0, 1.8, 4.5, 7.8, L_fin)):
                w_scale = 1.0 if ix < 2 else (0.85 if ix == 2 else (0.58 if ix == 3 else 0.22))
                vf_uv = xf / L_fin
                for sgn, u_uv in ((-1.0, 0.50), (0.0, 0.75), (1.0, 1.00)):
                    fv.append((xf, fin_axis[1] * sgn * hw * w_scale, fin_axis[2] * sgn * hw * w_scale))
                    fn.append((0.0, fin_axis[2], fin_axis[1]))
                    fst.append((u_uv, vf_uv))
            for ix in range(4):
                r0 = ix * 3
                r1 = (ix + 1) * 3
                ftr += [
                    (r0, r0 + 1, r1), (r0 + 1, r1 + 1, r1),
                    (r0 + 1, r0 + 2, r1 + 1), (r0 + 2, r1 + 2, r1 + 1),
                ]
            m.put("plume", fv, fn, fst, ftr, f=pf, tag=tag_plume, pivot=plume_origin)

        # Aerodynamic dorsal winglet on outer flank
        build_winglet(m, side)

    # ==================== 2. CENTRAL REACTOR / TURBOPUMP SPINE ====================
    # Main octagonal gunmetal spine nestled between the two tanks
    chamfer_box(m, "dark", (-5.25, -2.05, -3.6), (-1.15, 2.05, 8.3), bev=0.55)
    # Upper & lower machined manifold caps
    chamfer_box(m, "metal", (-5.05, -1.75, 8.3), (-1.45, 1.75, 9.15), bev=0.45)
    chamfer_box(m, "metal", (-4.95, -1.65, -4.25), (-1.55, 1.65, -3.6), bev=0.4)

    # Structural cross-bridge Saddles tying spine rigidly into both tanks
    for z_br in (-1.35, 5.45):
        box(m, "dark", (-4.55, -4.6, z_br), (-1.45, 4.6, z_br + 0.95))

    # Glowing Cyan Plasma Core Window on aft spine (-X hero face)
    # Outer metallic bezel
    chamfer_box(m, "metal", (-5.58, -1.35, 0.15), (-5.15, 1.35, 4.85), bev=0.28)
    # Glowing curved cyan plasma cell (mapped to top-left UV quadrant of jetpack_glow.png)
    core_f = frame_along((-5.42, 0.0, 0.35), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))
    lathe(m, "glow", [(0.0, 1.08), (4.3, 1.08)], core_f, segs=14, sy=1.0, sz=0.36,
          a0=-85, a1=85, uv_rect=(0.04, 0.04, 0.46, 0.46))
    # Horizontal containment ribs across the plasma window
    for zr in (1.35, 2.5, 3.65):
        box(m, "dark", (-5.82, -1.22, zr - 0.11), (-5.40, 1.22, zr + 0.11))

    # Heat-exchanger cooling fins below plasma window
    for zf in (-3.1, -2.55, -2.0, -1.45, -0.9):
        box(m, "metal", (-5.52, -1.45, zf - 0.09), (-5.15, 1.45, zf + 0.09))

    # Central Auxiliary Vernier Thruster Nozzle under spine
    vf = frame_along((-3.2, 0.0, -4.25), (-0.08, 0.0, -1.0), (1.0, 0.0, 0.0))
    lathe(m, "dark", [
        (0.0, 0.85), (0.5, 0.65), (1.55, 1.08), (1.55, 1.08), (1.55, 0.92),
    ], vf, segs=16)
    lathe(m, "glow", [(1.55, 0.92), (0.7, 0.55), (0.7, 0.0)], vf, segs=14, uv_rect=(0.54, 0.04, 0.96, 0.46))

    # Top-Rear Analog Pressure Dial (proud of aft spine at (-5.35, 0, 6.65))
    dial_orig = (-5.32, 0.0, 6.65)
    dial_dir = norm((-1.0, 0.0, 0.28))
    df = frame_along(dial_orig, dial_dir, (0.0, 0.0, 1.0))
    lathe(m, "metal", [
        (0.0, 0.0), (0.0, 1.24), (0.0, 1.24),
        (0.52, 1.24), (0.62, 1.12), (0.62, 0.98), (0.48, 0.98),
    ], df, segs=24)
    disk(m, "dial", 0.99, frame_along(add(dial_orig, mul(dial_dir, 0.50)), dial_dir, (0.0, 0.0, 1.0)), segs=24)

    # Twin Braided High-Pressure Fuel Hoses arching from central top manifold into tank shoulders
    for side in (-1, 1):
        hose_pts = catmull_rom([
            (-3.4, side * 1.15, 8.85),
            (-4.25, side * 1.85, 10.65),
            (-4.15, side * 3.15, 10.95),
            (-3.45, side * 3.85, 9.65),
        ], subdiv=6)
        sweep_tube(m, "hose", hose_pts, 0.34, segs=12, v_repeat=5.0)
        # Brass/steel hex Swagelok fittings at both ends of each hose
        for p_fit, d_fit in (
            ((-3.4, side * 1.15, 8.7), (-0.3, side * 0.3, 1.0)),
            ((-3.45, side * 3.85, 9.55), (-0.2, -side * 0.4, 1.0)),
        ):
            lathe(m, "metal", [(0, 0), (0, 0.48), (0, 0.48), (0.45, 0.48), (0.45, 0.48), (0.45, 0)],
                  frame_along(p_fit, d_fit), segs=6, flat=True)

    # ==================== 3. ERGONOMIC BACKPLATE, HARNESS & THROTTLE ARMS (+X) ====================
    # Rigid alloy carrier plate behind cushion
    chamfer_box(m, "metal", (-1.25, -5.3, -3.5), (-0.25, 5.3, 7.6), bev=0.6)

    # Quilted dark charcoal EVA foam back cushion + bolstered lumbar pad (+X face)
    chamfer_box(m, "strap", (-0.25, -4.75, -1.2), (0.72, 4.75, 7.1), bev=0.65)
    chamfer_box(m, "strap", (-0.25, -4.95, -3.35), (0.98, 4.95, -1.45), bev=0.55)
    # Twin vertical ventilation pads on upper backplate
    for side in (-1, 1):
        chamfer_box(m, "strap", (0.55, side * 2.35 - 1.35, -0.8), (1.05, side * 2.35 + 1.35, 6.6), bev=0.35)

    # Over-the-Shoulder Harness Straps looping forward (+X) around wearer's torso
    for side in (-1, 1):
        strap_pts = catmull_rom([
            (0.45, side * 3.15, 6.75),     # upper back anchor
            (1.85, side * 3.45, 8.65),     # rising behind traps
            (4.15, side * 3.55, 8.85),     # crest of shoulder
            (6.45, side * 3.10, 5.85),     # upper chest
            (6.85, side * 2.65, 2.15),     # sternum level
            (5.75, side * 4.15, -1.05),    # ribcage underarm curve
            (2.85, side * 4.85, -2.35),    # side hip return
            (0.35, side * 4.55, -2.55),    # lower backframe anchor
        ], subdiv=6)
        sweep_tube(m, "strap", strap_pts, r_y=0.68, r_z=0.22, segs=12, up_hint=(0.0, 1.0, 0.0), v_repeat=8.0)

    # Horizontal sternum strap + quick-release metallic chest buckle
    sternum_pts = catmull_rom([
        (6.78, -2.75, 2.55),
        (7.15, -1.1, 2.55),
        (7.15, 1.1, 2.55),
        (6.78, 2.75, 2.55),
    ], subdiv=5)
    sweep_tube(m, "strap", sternum_pts, r_y=0.38, r_z=0.15, segs=10, up_hint=(0.0, 0.0, 1.0), v_repeat=3.0)
    chamfer_box(m, "metal", (6.92, -0.95, 2.02), (7.42, 0.95, 3.08), bev=0.16)
    box(m, "glow", (7.36, -0.32, 2.28), (7.52, 0.32, 2.82), uv_rect=(0.05, 0.55, 0.45, 0.95))

    # Waist belt loop + central waist buckle
    waist_pts = catmull_rom([
        (0.55, -4.85, -2.45),
        (4.25, -5.35, -2.55),
        (7.05, -2.45, -2.55),
        (7.35, 0.0, -2.55),
        (7.05, 2.45, -2.55),
        (4.25, 5.35, -2.55),
        (0.55, 4.85, -2.45),
    ], subdiv=5)
    sweep_tube(m, "strap", waist_pts, r_y=0.52, r_z=0.18, segs=10, up_hint=(0.0, 0.0, 1.0), v_repeat=6.0)
    chamfer_box(m, "metal", (7.12, -1.15, -3.15), (7.62, 1.15, -1.95), bev=0.18)

    # Twin Fold-Down Pilot Control Arms & Ergonomic Hand-Grip Joysticks
    for side in (-1, 1):
        # Hinged shoulder-side bracket
        chamfer_box(m, "dark", (-0.95, side * 5.35 - 0.55, -1.35), (0.65, side * 5.35 + 0.55, 0.15), bev=0.18)
        arm_pts = catmull_rom([
            (0.35, side * 5.45, -0.65),
            (3.25, side * 6.05, -0.85),
            (6.15, side * 5.35, -0.35),
        ], subdiv=5)
        sweep_tube(m, "dark", arm_pts, 0.32, segs=10, v_repeat=2.0)

        # Angled ribbed joystick grip + red thumb ignition trigger button
        grip_base = (6.05, side * 5.32, -0.55)
        grip_dir = norm((0.28, -side * 0.08, 1.0))
        gf = frame_along(grip_base, grip_dir, (1.0, 0.0, 0.0))
        prof = [(0.0, 0.0), (0.0, 0.58), (0.25, 0.62)]
        gx = 0.35
        while gx < 2.55:
            prof += [(gx, 0.56), (gx + 0.22, 0.49)]
            gx += 0.44
        prof += [(2.75, 0.66), (3.05, 0.62), (3.15, 0.42), (3.15, 0.0)]
        lathe(m, "hose", prof, gf, segs=14)
        # Red thumb fire/boost button on top of grip
        btn_pos = add(grip_base, mul(grip_dir, 3.05))
        lathe(m, "glow", [(0.0, 0.28), (0.22, 0.26), (0.28, 0.0)],
              frame_along(btn_pos, grip_dir, (1.0, 0.0, 0.0)), segs=12, uv_rect=(0.05, 0.55, 0.45, 0.95))

    return m


# --------------------------------------------------------------------------- 16-Frame Animation Baker
def bake_animated_md3(part_mesh):
    """Frames 0..7 = thrust1..8 (active hovering afterburner + shock-diamond plumes)
       Frames 8..15 = idle1..8 (calm rack/standby hover with small pilot glow)"""
    # Group parts by material to form clean MD3 surfaces
    by_mat = {}
    for p in part_mesh.parts:
        by_mat.setdefault(p["mat"], []).append(p)

    surfaces = []
    n_frames = 16

    for mat in sorted(by_mat.keys()):
        plist = by_mat[mat]
        st_all, tris_all = [], []
        base_v = 0
        for p in plist:
            st_all += p["st"]
            tris_all += [(a + base_v, b + base_v, c + base_v) for a, b, c in p["tris"]]
            base_v += len(p["verts"])

        frames = []
        for fi in range(n_frames):
            is_thrust = fi < 8
            ph = 2.0 * math.pi * (fi % 8) / 8.0

            if is_thrust:
                # Dynamic hovering thrust: subtle forward flight pitch, vertical bob, slight roll oscillation
                body_dz = 0.48 * math.sin(ph)
                body_pitch = -3.8 + 1.1 * math.cos(ph)
                body_roll = 1.4 * math.sin(ph)
                gimbal_L = 2.2 * math.sin(ph * 2.0)
                gimbal_R = -2.2 * math.sin(ph * 2.0)
                plume_len_L = 0.92 + 0.22 * math.sin(ph * 2.0 + 0.4)
                plume_rad_L = 0.96 + 0.10 * math.cos(ph * 2.0)
                plume_len_R = 0.92 + 0.22 * math.cos(ph * 2.0 - 0.3)
                plume_rad_R = 0.96 - 0.10 * math.sin(ph * 2.0)
            else:
                # Calm standby idle: upright, gentle slow bob, plumes retracted to small pilot flames
                body_dz = 0.22 * math.sin(ph)
                body_pitch = 0.5 * math.sin(ph)
                body_roll = 0.0
                gimbal_L = 0.4 * math.sin(ph)
                gimbal_R = -0.4 * math.sin(ph)
                plume_len_L = 0.16 + 0.04 * math.sin(ph * 2.0)
                plume_rad_L = 0.44 + 0.05 * math.cos(ph * 2.0)
                plume_len_R = 0.16 + 0.04 * math.cos(ph * 2.0)
                plume_rad_R = 0.44 - 0.05 * math.sin(ph * 2.0)

            vv_frame, nn_frame = [], []
            for p in plist:
                tag = p["tag"]
                piv = p["pivot"]
                for v, n in zip(p["verts"], p["norms"]):
                    qv, qn = v, n
                    if tag in ("plumeL", "plumeR"):
                        s_len = plume_len_L if tag == "plumeL" else plume_len_R
                        s_rad = plume_rad_L if tag == "plumeL" else plume_rad_R
                        side = 1 if tag == "plumeL" else -1
                        noz_dir = norm((-0.052, side * 0.096, -1.0))
                        rel = sub(qv, piv)
                        along = dot(rel, noz_dir)
                        perp = sub(rel, mul(noz_dir, along))
                        qv = add(piv, add(mul(noz_dir, along * s_len), mul(perp, s_rad)))
                        # Apply nozzle gimbal around tank base pivot (-3.0, side*4.45, -4.4)
                        noz_piv = (-3.0, side * 4.45, -4.4)
                        g_ang = gimbal_L if tag == "plumeL" else gimbal_R
                        qv = add(noz_piv, rot_y(sub(qv, noz_piv), g_ang))
                        qn = rot_y(qn, g_ang)
                    elif tag in ("nozL", "nozR"):
                        g_ang = gimbal_L if tag == "nozL" else gimbal_R
                        qv = add(piv, rot_y(sub(qv, piv), g_ang))
                        qn = rot_y(qn, g_ang)

                    # Whole-body hover pose
                    qv = rot_x(qv, body_roll)
                    qv = rot_y(qv, body_pitch)
                    qv = (qv[0], qv[1], qv[2] + body_dz)
                    qn = norm(rot_y(rot_x(qn, body_roll), body_pitch))

                    vv_frame.append(qv)
                    nn_frame.append(qn)
            frames.append((vv_frame, nn_frame))

        surfaces.append(dict(
            name=mat,
            shader=f"progs/jetpack_{mat}",
            tris=tris_all,
            st=st_all,
            frames=frames,
        ))

    return dict(name="jetpack", surfaces=surfaces, nframes=n_frames)


# --------------------------------------------------------------------------- Procedural Textures & Shader
def get_font(size):
    for f in ("bahnschrift.ttf", "arialbd.ttf", "consolab.ttf", "impact.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", f), size)
        except OSError:
            pass
    return ImageFont.load_default()


def noise_img(w, h, base, amp, seed, streak_h=False, streak_v=False, blur=0.7):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h))
    px = im.load()
    col_bias = [rnd.uniform(-amp, amp) if streak_v else 0.0 for _ in range(w)]
    for y in range(h):
        row_bias = rnd.uniform(-amp, amp) if streak_h else 0.0
        for x in range(w):
            fine = rnd.uniform(-amp, amp) * (0.35 if (streak_h or streak_v) else 1.0)
            k = row_bias + col_bias[x] + fine
            px[x, y] = tuple(max(0, min(255, int(c + k))) for c in base)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


def save_png(im, stem):
    path = os.path.join(OUT, f"{stem}.png")
    im.save(path, "PNG", optimize=True)
    print(f"wrote {path} ({im.size[0]}x{im.size[1]})")


def build_textures():
    # Authored slightly toned-down (~0.58x albedo) to match Combat+ / DarkPlaces overbright lighting
    # 1. Tank wrap (256x256): brushed titanium cylinder + bold orange-amber racing band + hazard chevrons + "JP-02"
    tank = noise_img(256, 256, (108, 114, 124), 12, seed=101, streak_h=True, blur=0.6)
    d = ImageDraw.Draw(tank)
    # Subtle circumferential panel weld lines + rivets
    for y_seam in (36, 198):
        d.line([(0, y_seam), (255, y_seam)], fill=(54, 58, 66), width=2)
        d.line([(0, y_seam + 2), (255, y_seam + 2)], fill=(138, 144, 154), width=1)
        for rx in range(8, 256, 16):
            d.ellipse([rx - 2, y_seam - 6, rx + 2, y_seam - 2], fill=(68, 72, 80))
            d.ellipse([rx - 2, y_seam + 5, rx + 2, y_seam + 9], fill=(68, 72, 80))

    # Bold aerospace orange-gold band across upper-mid barrel
    d.rectangle([0, 62, 255, 126], fill=(186, 88, 18))
    d.rectangle([0, 62, 255, 67], fill=(24, 24, 28))
    d.rectangle([0, 121, 255, 126], fill=(24, 24, 28))
    d.rectangle([0, 68, 255, 71], fill=(222, 168, 42))

    # Diagonal hazard chevron stripe band near lower barrel
    d.rectangle([0, 162, 255, 184], fill=(184, 146, 20))
    for sx in range(-32, 288, 24):
        d.polygon([(sx, 184), (sx + 12, 184), (sx + 24, 162), (sx + 12, 162)], fill=(24, 24, 28))
    d.rectangle([0, 161, 255, 163], fill=(24, 24, 28))
    d.rectangle([0, 183, 255, 185], fill=(24, 24, 28))

    # Stencil "JP-02" centered dead-on u=0.5 (x=128) on the -X hero face!
    f_big = get_font(26)
    f_sm = get_font(12)
    lbl1 = "JP-02"
    b1 = d.textbbox((0, 0), lbl1, font=f_big)
    x1 = 128 - (b1[2] - b1[0]) // 2
    d.text((x1 + 2, 79), lbl1, font=f_big, fill=(22, 22, 25))
    d.text((x1, 77), lbl1, font=f_big, fill=(238, 235, 224))
    lbl2 = "LOX / RP-1  3800 PSI"
    b2 = d.textbbox((0, 0), lbl2, font=f_sm)
    x2 = 128 - (b2[2] - b2[0]) // 2
    d.text((x2, 136), lbl2, font=f_sm, fill=(28, 31, 36))
    save_png(tank, "jetpack_tank")

    # 2. Bright machined steel/aluminum
    metal = noise_img(128, 128, (118, 124, 134), 13, seed=102, streak_h=True, blur=0.5)
    save_png(metal, "jetpack_metal")

    # 3. Heavy gunmetal structural alloy
    dark = noise_img(128, 128, (48, 52, 60), 8, seed=103, blur=0.5)
    dd = ImageDraw.Draw(dark)
    for y in range(0, 128, 32):
        dd.line([(0, y), (127, y)], fill=(34, 37, 44), width=2)
    save_png(dark, "jetpack_dark")

    # 4. Winglet skin (U=0 root -> U=1 tip, with diagonal yellow/black hazard tip at x=90..127)
    wing = noise_img(128, 128, (62, 68, 78), 7, seed=104, streak_v=True, blur=0.5)
    wd = ImageDraw.Draw(wing)
    wd.rectangle([90, 0, 127, 127], fill=(192, 150, 18))
    for sy in range(-128, 256, 22):
        wd.polygon([(90, sy), (127, sy + 37), (127, sy + 26), (90, sy - 11)], fill=(22, 24, 28))
    wd.line([(89, 0), (89, 127)], fill=(22, 24, 28), width=3)
    for ry in range(12, 128, 20):
        wd.ellipse([18, ry - 2, 22, ry + 2], fill=(40, 44, 52))
    save_png(wing, "jetpack_wing")

    # 5. Quilted ballistic nylon harness & padded backplate
    strap = noise_img(128, 128, (30, 33, 38), 5, seed=105, blur=0.3)
    sd = ImageDraw.Draw(strap)
    for y in range(0, 128, 8):
        sd.line([(0, y), (127, y)], fill=(20, 22, 26), width=2)
    for x in (10, 117):
        for y in range(2, 128, 8):
            sd.line([(x, y), (x, y + 4)], fill=(86, 72, 34), width=2)  # tactical contrast stitching
    save_png(strap, "jetpack_strap")

    # 6. Braided / corrugated high-pressure fuel hose & grip rubber
    hose = noise_img(64, 64, (56, 60, 66), 9, seed=106, blur=0.3)
    hd = ImageDraw.Draw(hose)
    for y in range(0, 64, 6):
        hd.line([(0, y), (63, y)], fill=(24, 26, 30), width=2)
        hd.line([(0, y + 2), (63, y + 2)], fill=(96, 102, 112), width=1)
    for x in range(0, 64, 8):
        hd.line([(x, 0), ((x + 16) % 64, 63)], fill=(76, 80, 88), width=1)
    save_png(hose, "jetpack_hose")

    # 7. Analog pressure gauge dial (128x128)
    dial = Image.new("RGB", (128, 128), (18, 22, 28))
    gd = ImageDraw.Draw(dial)
    gd.ellipse([4, 4, 123, 123], fill=(215, 218, 212), outline=(45, 50, 58), width=4)
    # Green / yellow / red pressure zones along outer arc
    gd.arc([14, 14, 113, 113], start=135, end=270, fill=(36, 152, 62), width=10)
    gd.arc([14, 14, 113, 113], start=270, end=330, fill=(212, 156, 22), width=10)
    gd.arc([14, 14, 113, 113], start=330, end=405, fill=(198, 42, 32), width=10)
    for deg in range(135, 406, 18):
        rad = math.radians(deg)
        r0 = 38 if deg % 36 == 0 else 43
        x0, y0 = 64 + math.cos(rad) * r0, 64 + math.sin(rad) * r0
        x1, y1 = 64 + math.cos(rad) * 52, 64 + math.sin(rad) * 52
        gd.line([(x0, y0), (x1, y1)], fill=(25, 28, 32), width=2 if deg % 36 == 0 else 1)
    gd.text((48, 78), "PSI", font=get_font(15), fill=(30, 34, 40))
    # Indicator needle pointing into high nominal / yellow-edge boost!
    n_rad = math.radians(308)
    gd.line([(64, 64), (64 + math.cos(n_rad) * 44, 64 + math.sin(n_rad) * 44)], fill=(205, 36, 28), width=4)
    gd.ellipse([57, 57, 71, 71], fill=(38, 42, 48))
    save_png(dial, "jetpack_dial")

    # 8. Unlit Emissive Atlas (128x128):
    #    TL (0..64, 0..64): Cyan plasma core   | TR (64..128, 0..64): Hot orange rocket throat
    #    BL (0..64, 64..128): Red strobe/btn   | BR (64..128, 64..128): Green valve/stbd LED
    glow = Image.new("RGB", (128, 128), (0, 0, 0))
    gp = glow.load()
    for y in range(64):
        for x in range(64):
            # TL: glowing cyan reactor core with bright vertical center spine
            dx = abs(x - 31.5) / 31.5
            pulse = 0.88 + 0.12 * math.sin(y * 0.45)
            r = int(max(0, min(255, (55 + 185 * (1.0 - dx) ** 2.2) * pulse)))
            g = int(max(0, min(255, (185 + 70 * (1.0 - dx)) * pulse)))
            b = int(max(0, min(255, 255 * pulse)))
            gp[x, y] = (r, g, b)

            # TR: incandescent rocket nozzle throat (v=0 lip -> v=1 white-hot injector core)
            heat = y / 63.0
            rr = int(min(255, 165 + 90 * heat))
            gg = int(min(255, 48 + 185 * (heat ** 1.5)))
            bb = int(min(255, 12 + 150 * (heat ** 3.0)))
            gp[64 + x, y] = (rr, gg, bb)

            # BL: bright red button / port strobe
            rr_d = math.hypot(x - 31.5, y - 31.5) / 32.0
            k = max(0.35, 1.0 - 0.55 * rr_d * rr_d)
            gp[x, 64 + y] = (int(245 * k), int(38 * k), int(32 * k))

            # BR: bright emerald status LED / starboard strobe
            gp[64 + x, 64 + y] = (int(42 * k), int(238 * k), int(92 * k))
    save_png(glow, "jetpack_glow")

    # 9. Additive 4-Frame Animated Shock-Diamond Thruster Plume (128x256 RGB: jetpack_plume_0..3.png)
    #    Left half (x=0..63): soft outer golden-orange/blue plasma sheath, fading to 0 at v=1 tail
    #    Right half (x=64..127): intense white-cyan-amber Mach shock diamonds with lateral fade at x=64 & x=127
    for k in range(4):
        phase = k / 4.0
        plume = Image.new("RGB", (128, 256), (0, 0, 0))
        pp = plume.load()
        for y in range(256):
            v = y / 255.0
            # Smooth nozzle ramp-in (v=0..0.05) and smooth tail fade-out to black (v=0.45..1.0)
            env = min(1.0, v / 0.04) * (max(0.0, 1.0 - v) ** 1.55)
            # Travelling Mach shock diamonds moving down (+v) with frame phase
            wave = math.sin((v * 3.6 - phase) * math.pi * 2.0)
            shock = max(0.0, wave) ** 2.2
            base_glow = 0.42 + 0.58 * shock
            # Color shifts from electric cyan-blue near nozzle (v<0.28) to fiery amber-orange downstream
            blue_mix = max(0.0, 1.0 - v * 2.3)
            for x in range(64):
                # Left half: outer volumetric sheath (dimmer so nested cones stack smoothly without blowing out)
                s = env * (0.36 + 0.24 * shock)
                r = int(min(255, (210 * (1.0 - 0.45 * blue_mix) + 60 * shock) * s))
                g = int(min(255, (115 + 75 * blue_mix + 55 * shock) * s))
                b = int(min(255, (35 + 210 * blue_mix + 45 * shock) * s))
                pp[x, y] = (r, g, b)
            for x in range(64):
                # Right half: inner core & crossed fins (bell-curve across u=0.5..1.0 so fin edges vanish!)
                lat = math.sin((x / 63.0) * math.pi) ** 1.35
                s = env * base_glow * lat
                r = int(min(255, (245 * (1.0 - 0.25 * blue_mix) + 50 * shock) * s))
                g = int(min(255, (165 + 75 * blue_mix + 55 * shock) * s))
                b = int(min(255, (80 + 175 * blue_mix + 70 * shock) * s))
                pp[64 + x, y] = (r, g, b)
        plume = plume.filter(ImageFilter.GaussianBlur(1.4))
        save_png(plume, f"jetpack_plume_{k}")
        if k == 0:
            save_png(plume, "jetpack_plume")


def write_shader():
    os.makedirs(SCRIPTS, exist_ok=True)
    sh_path = os.path.join(SCRIPTS, "jetpack.shader")
    shader_txt = """// written by mm_tools/build_jetpack.py
progs/jetpack_glow
{
\tcull none
\t{
\t\tmap progs/jetpack_glow
\t\trgbGen identity
\t}
}

progs/jetpack_plume
{
\tcull none
\t{
\t\tanimmap 18 progs/jetpack_plume_0 progs/jetpack_plume_1 progs/jetpack_plume_2 progs/jetpack_plume_3
\t\tblendfunc add
\t}
}
"""
    # Everything else is double-sided too: the winglets, dial and tank windows are single planes (and the dial's winding is
    # reversed), so with the default back-face culling they vanish from behind / inside and you see straight through the pack.
    for mat in ("dark", "dial", "hose", "metal", "strap", "tank", "wing"):
        shader_txt += f"\nprogs/jetpack_{mat}\n{{\n\tcull none\n\t{{\n\t\tmap progs/jetpack_{mat}\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(shader_txt)
    print(f"wrote {sh_path}")


def main():
    os.makedirs(OUT, exist_ok=True)
    build_textures()
    write_shader()
    parts = build_jetpack_parts()
    md3 = bake_animated_md3(parts)
    total_nv = sum(len(s["st"]) for s in md3["surfaces"])
    total_nt = sum(len(s["tris"]) for s in md3["surfaces"])
    for s in md3["surfaces"]:
        assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, (s["name"], len(s["st"]), len(s["tris"]))
    out_md3 = os.path.join(OUT, "jetpack.md3")
    md3lib.write(out_md3, md3)
    print(f"wrote {out_md3}: {len(md3['surfaces'])} surfaces, {total_nv} verts, {total_nt} tris, {md3['nframes']} frames")


if __name__ == "__main__":
    main()
