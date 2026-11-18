"""Shared 3D procedural geometry primitives and pure-original Mega Man contraption builders.

Coordinate system (Quake / DarkPlaces MD3 standard):
  +X = forward, +Y = left, +Z = up, Z = 0 is the ground contact plane.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from mmw_geometry import (
    MeshPart,
    basis_from_axis,
    rot_axis,
    rot_x,
    rot_y,
    rot_z,
    smoothstep,
    vadd,
    vcross,
    vdot,
    vlen,
    vlerp,
    vmul,
    vnorm,
    vsub,
)
from tank_tex_gen import (
    UV_CHROME_BAR,
    UV_COTTER_YEL,
    UV_FX_GLINT,
    UV_FX_PLUME,
    UV_FX_RING,
    UV_HEX_ZINC,
    UV_RUBBER_CAP,
    UV_STAINLESS,
    UV_VALVE_BLK,
    UV_VALVE_BRASS,
    UV_WHEEL_IRIM,
    UV_WHEEL_RIM,
    UV_WHEEL_SIDE,
    UV_WHEEL_TREAD,
)

SHADER_MAP = {
    "orig":       "progs/mmt_orig",
    "chrome_bar": "progs/mmt_chrome_bar",
    "wheel":      "progs/mmt_wheel",
    "fx":         "progs/mmt_fx",
}


def xform_verts_norms(part, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0), scale=1.0):
    """Transforms a MeshPart's vertices & normals around pivot without mutating topology."""
    vv, nn = [], []
    px, py, pz = pivot
    ox, oy, oz = offset
    for p, n in zip(part.verts, part.norms):
        q = ((p[0] - px) * scale, (p[1] - py) * scale, (p[2] - pz) * scale)
        qn = n
        if rx:
            q, qn = rot_x(q, rx), rot_x(qn, rx)
        if ry:
            q, qn = rot_y(q, ry), rot_y(qn, ry)
        if rz:
            q, qn = rot_z(q, rz), rot_z(qn, rz)
        vv.append((q[0] + px + ox, q[1] + py + oy, q[2] + pz + oz))
        nn.append(vnorm(qn))
    return vv, nn


def combine_static_parts(parts):
    """Merges multiple MeshParts with the same material into one MeshPart."""
    assert parts, "Need at least one part"
    out = MeshPart(parts[0].mat)
    for p in parts:
        out.append_part(p)
    return out


def make_surface_from_frames(name, mat, template_part, frames_vn):
    """Builds an MD3 surface dict from a fixed-topology template MeshPart and per-frame (verts, norms)."""
    nv = len(template_part.verts)
    nt = len(template_part.tris)
    assert 0 < nv <= 4096, f"Surface {name} nv={nv} > 4096"
    assert 0 < nt <= 8192, f"Surface {name} nt={nt} > 8192"
    for fi, (vv, nn) in enumerate(frames_vn):
        assert len(vv) == nv and len(nn) == nv, f"Frame {fi} mismatch on {name}"
    return dict(
        name=name,
        mat=mat,
        shader=SHADER_MAP[mat],
        tris=list(template_part.tris),
        st=list(template_part.st),
        frames=frames_vn,
    )


def build_pneumatic_wheel(side_sign=+1, radius=36.0, half_width=9.5, segs=28):
    """Builds one clean original Mega Man 5-ribbed pneumatic wheel + smooth concave off-white dish rim +
    hex nut + yellow cotter pin + angled Schrader valve at origin. Outer face points along (0, side_sign, 0).
    """
    wp = MeshPart("wheel")
    hp = MeshPart("chrome_bar")
    axis = (0.0, float(side_sign), 0.0)
    up_h = (0.0, 0.0, 1.0)
    s_r = radius / 4.02
    s_w = half_width / 1.06

    # 1) Inner Off-White Steel Dish Rim
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.84 * s_w, 0.00 * s_r, 0.00, 2.38 * s_r),
            (-0.84 * s_w, 0.56 * s_r, 0.24, 2.38 * s_r),
            (-0.84 * s_w, 0.56 * s_r, 0.24, 2.38 * s_r),
            (-0.72 * s_w, 1.92 * s_r, 0.80, 2.38 * s_r),
            (-0.90 * s_w, 2.22 * s_r, 0.93, 2.38 * s_r),
            (-0.84 * s_w, 2.38 * s_r, 1.00, 2.38 * s_r),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHEEL_IRIM, up_hint=up_h,
    )

    # 2) Inner Sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.84 * s_w, 2.38 * s_r, 0.59, 4.02 * s_r),
            (-0.98 * s_w, 2.86 * s_r, 0.71, 4.02 * s_r),
            (-1.05 * s_w, 3.40 * s_r, 0.85, 4.02 * s_r),
            (-0.98 * s_w, 3.84 * s_r, 0.95, 4.02 * s_r),
            (-0.82 * s_w, 3.96 * s_r, 0.98, 4.02 * s_r),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHEEL_SIDE, up_hint=up_h,
    )

    # 3) 5-Ribbed Tread Crown (outer radius = radius)
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=up_h)
    tread_prof = [
        (-0.82 * s_w, 3.96 * s_r, 0.02),
        (-0.72 * s_w, 4.01 * s_r, 0.08),
        (-0.56 * s_w, 4.02 * s_r, 0.17),
        (-0.48 * s_w, 3.90 * s_r, 0.21),
        (-0.40 * s_w, 4.02 * s_r, 0.25),
        (-0.24 * s_w, 4.02 * s_r, 0.36),
        (-0.16 * s_w, 3.90 * s_r, 0.40),
        (-0.08 * s_w, 4.02 * s_r, 0.44),
        (+0.08 * s_w, 4.02 * s_r, 0.56),
        (+0.16 * s_w, 3.90 * s_r, 0.60),
        (+0.24 * s_w, 4.02 * s_r, 0.64),
        (+0.40 * s_w, 4.02 * s_r, 0.75),
        (+0.48 * s_w, 3.90 * s_r, 0.79),
        (+0.56 * s_w, 4.02 * s_r, 0.83),
        (+0.72 * s_w, 4.01 * s_r, 0.92),
        (+0.82 * s_w, 3.96 * s_r, 0.98),
    ]
    cols = segs + 1
    b_tr = len(wp.verts)
    tr_pts = []
    for sp, rp, ut in tread_prof:
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            cth, sth = math.cos(th), math.sin(th)
            tr_pts.append(vadd(vmul(X_w, sp), vadd(vmul(Y_w, rp * cth), vmul(Z_w, rp * sth))))
            wp.st.append((0.01 + 0.48 * ut, 0.01 + 0.48 * (j / float(segs))))
    tr_acc = [[0.0, 0.0, 0.0] for _ in tr_pts]
    tr_tris = []
    for i in range(len(tread_prof) - 1):
        for j in range(segs):
            a = i * cols + j
            b = a + 1
            c = a + cols
            d = c + 1
            for tri in ((a, b, c), (b, d, c)):
                fn = vcross(vsub(tr_pts[tri[1]], tr_pts[tri[0]]), vsub(tr_pts[tri[2]], tr_pts[tri[0]]))
                tr_tris.append(tri)
                for vi in tri:
                    tr_acc[vi][0] += fn[0]
                    tr_acc[vi][1] += fn[1]
                    tr_acc[vi][2] += fn[2]
    for i in range(len(tread_prof)):
        i0, i1 = i * cols, i * cols + segs
        sn = vadd(tr_acc[i0], tr_acc[i1])
        tr_acc[i0], tr_acc[i1] = list(sn), list(sn)
    wp.verts += tr_pts
    wp.norms += [vnorm(n) for n in tr_acc]
    wp.tris += [(a + b_tr, b + b_tr, c + b_tr) for (a, b, c) in tr_tris]

    # 4) Outer Sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.82 * s_w, 3.96 * s_r, 0.98, 4.02 * s_r),
            (+0.98 * s_w, 3.84 * s_r, 0.95, 4.02 * s_r),
            (+1.05 * s_w, 3.40 * s_r, 0.85, 4.02 * s_r),
            (+0.98 * s_w, 2.86 * s_r, 0.71, 4.02 * s_r),
            (+0.86 * s_w, 2.38 * s_r, 0.59, 4.02 * s_r),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHEEL_SIDE, up_hint=up_h,
    )

    # 5) Outer Off-White Stamped Steel Concave Dish Rim
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.86 * s_w, 2.38 * s_r, 1.00, 2.38 * s_r),
            (+0.95 * s_w, 2.24 * s_r, 0.94, 2.38 * s_r),
            (+0.82 * s_w, 2.02 * s_r, 0.85, 2.38 * s_r),
            (+0.42 * s_w, 1.72 * s_r, 0.72, 2.38 * s_r),
            (+0.36 * s_w, 1.08 * s_r, 0.45, 2.38 * s_r),
            (+0.40 * s_w, 0.62 * s_r, 0.26, 2.38 * s_r),
            (+0.40 * s_w, 0.62 * s_r, 0.26, 2.38 * s_r),
            (+0.66 * s_w, 0.54 * s_r, 0.23, 2.38 * s_r),
            (+0.66 * s_w, 0.54 * s_r, 0.23, 2.38 * s_r),
            (+0.68 * s_w, 0.26 * s_r, 0.11, 2.38 * s_r),
            (+0.68 * s_w, 0.00 * s_r, 0.00, 2.38 * s_r),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHEEL_RIM, up_hint=up_h,
    )

    # 6) Hub Hardware: Hex Nut + Axle Stub + Yellow Cotter Pin + Angled Valve
    hp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.66 * s_w, 0.24 * s_r, 0.05),
            (+0.66 * s_w, 0.44 * s_r, 0.10),
            (+0.66 * s_w, 0.44 * s_r, 0.10),
            (+0.92 * s_w, 0.44 * s_r, 0.90),
            (+0.92 * s_w, 0.44 * s_r, 0.90),
            (+0.92 * s_w, 0.22 * s_r, 0.96),
        ],
        segs=6, uv_rect=UV_HEX_ZINC, up_hint=up_h,
    )
    hp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.90 * s_w, 0.22 * s_r, 0.10),
            (+1.12 * s_w, 0.22 * s_r, 0.88),
            (+1.12 * s_w, 0.22 * s_r, 0.88),
            (+1.12 * s_w, 0.00 * s_r, 1.00),
        ],
        segs=10, uv_rect=UV_STAINLESS, up_hint=up_h,
    )
    pin_c = vmul(X_w, 1.01 * s_w)
    hp.add_tube(
        [vadd(pin_c, vmul(Z_w, -0.48 * s_r)), vadd(pin_c, vmul(Z_w, +0.40 * s_r))],
        [0.060 * s_r, 0.060 * s_r], segs=6, uv_rect=UV_COTTER_YEL,
    )
    va = math.radians(-35.0)
    v_rad = vadd(vmul(Y_w, math.cos(va)), vmul(Z_w, math.sin(va)))
    hp.add_tube(
        [vadd(vmul(X_w, 0.36 * s_w), vmul(v_rad, 1.54 * s_r)),
         vadd(vmul(X_w, 0.75 * s_w), vmul(v_rad, 1.35 * s_r))],
        [0.12 * s_r, 0.095 * s_r], segs=6, uv_rect=UV_VALVE_BLK,
    )
    hp.add_tube(
        [vadd(vmul(X_w, 0.75 * s_w), vmul(v_rad, 1.35 * s_r)),
         vadd(vmul(X_w, 0.94 * s_w), vmul(v_rad, 1.24 * s_r))],
        [0.085 * s_r, 0.078 * s_r], segs=6, uv_rect=UV_VALVE_BRASS,
    )
    return wp, hp


def build_cross_axle(half_span=50.5, radius=2.15, collar_rad=3.2):
    """Builds the straight polished stainless cross-axle spanning wheel-to-wheel at Z=0 (later placed at Z=36)."""
    ax = MeshPart("chrome_bar")
    s_y = half_span
    ax.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        [
            (-s_y,        0.0,        0.02),
            (-s_y,        collar_rad, 0.04),
            (-s_y,        collar_rad, 0.04),
            (-s_y + 8.0,  collar_rad, 0.10),
            (-s_y + 8.0,  collar_rad, 0.10),
            (-s_y + 8.2,  radius,     0.12),
            (+s_y - 8.2,  radius,     0.88),
            (+s_y - 8.0,  collar_rad, 0.90),
            (+s_y - 8.0,  collar_rad, 0.90),
            (+s_y,        collar_rad, 0.96),
            (+s_y,        collar_rad, 0.96),
            (+s_y,        0.0,        0.98),
        ],
        segs=18, uv_rect=UV_STAINLESS,
    )
    return ax


def build_t_collar(radius_scale=1.0, length_scale=1.0):
    """Builds the welded transverse TIG T-collar sleeve & twin retaining collars that stay on the axle."""
    tc = MeshPart("chrome_bar")
    R = radius_scale
    L = length_scale
    tc.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        [
            (-10.8 * L, 2.1 * R, 0.96),
            (-10.8 * L, 4.4 * R, 0.92),
            (-10.8 * L, 4.4 * R, 0.92),
            (-6.2 * L,  4.8 * R, 0.82),
            (0.0,       5.2 * R, 0.74),
            (+6.2 * L,  4.8 * R, 0.82),
            (+10.8 * L, 4.4 * R, 0.92),
            (+10.8 * L, 4.4 * R, 0.92),
            (+10.8 * L, 2.1 * R, 0.96),
        ],
        segs=20, uv_rect=UV_STAINLESS,
    )
    for sgn in (-1.0, +1.0):
        tc.add_lathe(
            (0.0, sgn * 13.0 * L, 0.0), (0.0, sgn, 0.0),
            [
                (-1.6 * L, 2.1 * R, 0.08),
                (-1.6 * L, 3.8 * R, 0.16),
                (-1.6 * L, 3.8 * R, 0.16),
                (+1.6 * L, 3.8 * R, 0.84),
                (+1.6 * L, 3.8 * R, 0.84),
                (+1.6 * L, 2.1 * R, 0.92),
            ],
            segs=16, uv_rect=UV_HEX_ZINC,
        )
    return tc


def build_tank_silver_bar(length_scale=1.0, radius_scale=1.0, segs=26):
    """Builds the iconic gleaming mirror-chrome Mega Man Silver Bar + stepped black rubber rear end-cap."""
    ba = MeshPart("chrome_bar")
    L = length_scale
    R = radius_scale

    # Rear Stepped Matte-Black Rubber End-Cap
    ba.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [
            (-44.0 * L, 0.00 * R, 0.02),
            (-44.0 * L, 5.10 * R, 0.12),
            (-44.0 * L, 5.10 * R, 0.12),
            (-43.0 * L, 6.20 * R, 0.20),
            (-39.8 * L, 6.20 * R, 0.45),
            (-39.4 * L, 5.85 * R, 0.52),
            (-36.8 * L, 5.85 * R, 0.72),
            (-36.4 * L, 6.20 * R, 0.78),
            (-33.8 * L, 6.20 * R, 0.94),
            (-33.8 * L, 6.20 * R, 0.94),
            (-33.6 * L, 5.60 * R, 0.98),
        ],
        segs=segs, uv_rect=UV_RUBBER_CAP,
    )

    # Mirror-Chrome Central Bar + Ogive Torpedo Bullet Nose
    prof = [
        (-33.6 * L, 5.60 * R, 0.02),
        (-16.0 * L, 5.60 * R, 0.24),
        (-7.8 * L,  5.80 * R, 0.36),
        (-5.0 * L,  6.65 * R, 0.42),
        (0.0,       6.85 * R, 0.46),
        (+5.0 * L,  6.65 * R, 0.50),
        (+7.8 * L,  5.80 * R, 0.56),
        (+30.0 * L, 5.60 * R, 0.79),
    ]
    for k in range(1, 9):
        t = k / 8.0
        xn = (30.0 + 18.0 * t) * L
        rn = (5.60 * R) * (math.cos(t * math.pi * 0.5) ** 0.76) if k < 8 else 0.0
        prof.append((xn, rn, 0.79 + 0.19 * t))
    ba.add_lathe((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), prof, segs=segs, uv_rect=UV_CHROME_BAR)
    return ba


def build_turret_fx_mesh(muzzle_x=88.0, ring_amp=0.0, glint_pos=(60.0, 0.0, 0.0), glint_amp=0.0, fx_scale=1.75):
    """Fixed-topology additive FX mesh for turrets (launch shockwave ring + reload star-glint)."""
    fx = MeshPart("fx")
    r_c = (muzzle_x, 0.0, 0.0) if ring_amp > 0.01 else (0.0, 0.0, 0.0)
    r_maj = ((7.5 + 15.0 * ring_amp) * fx_scale) if ring_amp > 0.01 else 0.004
    r_min = ((2.2 * ring_amp) * fx_scale) if ring_amp > 0.01 else 0.002
    segs_u, segs_v = 16, 6
    b = len(fx.verts)
    u0, v0, u1, v1 = UV_FX_RING
    for i in range(segs_u + 1):
        th = 2.0 * math.pi * (i / float(segs_u))
        ct, st = math.cos(th), math.sin(th)
        for j in range(segs_v + 1):
            ph = 2.0 * math.pi * (j / float(segs_v))
            cp, sp = math.cos(ph), math.sin(ph)
            rr = r_maj + r_min * cp
            fx.verts.append((r_c[0] + r_min * sp, r_c[1] + rr * ct, r_c[2] + rr * st))
            fx.norms.append(vnorm((sp, cp * ct, cp * st)))
            fx.st.append((u0 + (u1 - u0) * (i / float(segs_u)), v0 + (v1 - v0) * (j / float(segs_v))))
    cols = segs_v + 1
    for i in range(segs_u):
        for j in range(segs_v):
            a = b + i * cols + j
            fx.tris += [(a, a + cols, a + 1), (a + 1, a + cols, a + cols + 1)]

    gs = ((8.5 * glint_amp) * fx_scale) if glint_amp > 0.01 else 0.003
    gp = glint_pos if glint_amp > 0.01 else (0.0, 0.0, 0.0)
    gu0, gv0, gu1, gv1 = UV_FX_GLINT
    for axis_a, axis_b in (((0, 1, 0), (0, 0, 1)), ((1, 0, 0), (0, 0, 1)), ((1, 0, 0), (0, 1, 0))):
        p0 = vadd(gp, vadd(vmul(axis_a, -gs), vmul(axis_b, -gs)))
        p1 = vadd(gp, vadd(vmul(axis_a, +gs), vmul(axis_b, -gs)))
        p2 = vadd(gp, vadd(vmul(axis_a, +gs), vmul(axis_b, +gs)))
        p3 = vadd(gp, vadd(vmul(axis_a, -gs), vmul(axis_b, +gs)))
        fx.add_quad(p0, p1, p2, p3, (gu0, gv0), (gu1, gv0), (gu1, gv1), (gu0, gv1), two_sided=True)
    return fx
