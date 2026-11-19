"""3D Procedural Geometry & 36-Frame Quake Animation Builders for the 5 Kyle Scissor Viewmodels.

Coordinate system (Quake 1st-person viewmodel):
  +X = forward (downrange), +Y = left, +Z = up
  Camera eye at (0,0,0), target (100, 0, -2.2), hfov = 90 deg.
  All 5 models are framed around X=14..32, Y=-10..+2, Z=-12..-2.

36-Frame Animation Schedule (every model):
  - Frames  0..15 (16 frames): Idle (seamless breathing, bobbing, spinning barber pole/bubbles)
  - Frames 16..27 (12 frames): Hold-to-Lock (rapid accelerating scissor-snipping & mechanism charge)
  - Frames 28..35 ( 8 frames): Fire / Launch recoil + payload launch + mechanical reload
"""
import math
import os
import sys

MM_TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)

from mmw_geometry import (
    MeshPart,
    basis_from_axis,
    build_articulated_ranger_hand,
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
from kw_textures import (
    UV_BARBER_POLE,
    UV_BRASS,
    UV_CHROME,
    UV_CUT_BODY,
    UV_CUT_HEAD,
    UV_DOLLAR_BILL,
    UV_FX_GLINT,
    UV_FX_RING,
    UV_FX_SPARK,
    UV_FX_STREAK,
    UV_GOLD_COIN,
    UV_GUNMETAL,
    UV_INVOICE,
    UV_MARQUEE_50,
    UV_PSI_GAUGE,
    UV_REG_GREEN,
    UV_WOOD_CLIP,
)

FRAME_NAMES_36 = (
    [f"idle{i + 1}" for i in range(16)]
    + [f"lock{i + 1}" for i in range(12)]
    + [f"fire{i + 1}" for i in range(8)]
)


def transform_part(part, pos=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, axis_rot=None, scale=1.0):
    """Returns (verts, norms) of MeshPart transformed by scale -> rx -> ry -> rz -> axis_rot -> +pos."""
    vv, nn = [], []
    for p, n in zip(part.verts, part.norms):
        if isinstance(scale, tuple):
            q = (p[0] * scale[0], p[1] * scale[1], p[2] * scale[2])
        else:
            q = vmul(p, scale)
        qn = n
        if rx:
            q, qn = rot_x(q, rx), rot_x(qn, rx)
        if ry:
            q, qn = rot_y(q, ry), rot_y(qn, ry)
        if rz:
            q, qn = rot_z(q, rz), rot_z(qn, rz)
        if axis_rot is not None:
            ax, deg = axis_rot
            if deg:
                q, qn = rot_axis(q, ax, deg), rot_axis(qn, ax, deg)
        vv.append(vadd(q, pos))
        nn.append(vnorm(qn))
    return vv, nn


def combine_parts(parts_and_xforms):
    """Transforms and merges a list of (MeshPart, kwargs) into (verts, norms)."""
    all_v, all_n = [], []
    for part, kw in parts_and_xforms:
        vv, nn = transform_part(part, **kw)
        all_v.extend(vv)
        all_n.extend(nn)
    return all_v, all_n


def merge_topology(parts):
    """Merges st and tris of static list of MeshParts (order must match combine_parts!)."""
    st, tris = [], []
    ofs = 0
    for p in parts:
        st.extend(p.st)
        tris.extend([(a + ofs, b + ofs, c + ofs) for (a, b, c) in p.tris])
        ofs += len(p.verts)
    return st, tris


def pack_surface(name, mat, shader, st, tris, frames):
    return dict(name=name, mat=mat, shader=shader, st=list(st), tris=list(tris), frames=frames)


def apply_sway(vv, nn, pos=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(18.0, -4.0, -7.0)):
    """Applies global viewmodel idle/recoil sway around a shoulder/wrist pivot."""
    pv = pivot
    out_v, out_n = [], []
    for p, n in zip(vv, nn):
        q = vsub(p, pv)
        qn = n
        if rx:
            q, qn = rot_x(q, rx), rot_x(qn, rx)
        if ry:
            q, qn = rot_y(q, ry), rot_y(qn, ry)
        if rz:
            q, qn = rot_z(q, rz), rot_z(qn, rz)
        out_v.append(vadd(vadd(q, pv), pos))
        out_n.append(vnorm(qn))
    return out_v, out_n


def apply_quake_cant(vv, nn, origin=(19.0, -4.5, -6.5), shift=(0.0, 0.0, 0.0), yaw=12.0, pitch=3.5, roll=-4.0, scale=1.18):
    """Applies classic Quake 1st-person viewmodel inward cant & hero framing around weapon origin."""
    out_v, out_n = [], []
    for p, n in zip(vv, nn):
        q = vmul(vsub(p, origin), scale)
        qn = n
        if roll:
            q, qn = rot_x(q, roll), rot_x(qn, roll)
        if pitch:
            q, qn = rot_y(q, pitch), rot_y(qn, pitch)
        if yaw:
            q, qn = rot_z(q, yaw), rot_z(qn, yaw)
        out_v.append(vadd(vadd(q, origin), shift))
        out_n.append(vnorm(qn))
    return out_v, out_n


# ===========================================================================
# SHARED 3D SCISSOR, KYLE PHOTO RELIEF, CASH & FX BUILDERS
# ===========================================================================
def build_scissor_half(
    blade_len=7.0,
    blade_w=1.15,
    thick=0.22,
    tang_len=3.2,
    ring_r=1.05,
    mirror_z=1.0,
    with_pivot=True,
    handle_uv=UV_BRASS,
):
    """Builds one half of a 3D hollow-ground steel scissor/shear in local space.
    Pivot is at (0, 0, 0); blade points along +X, edge faces -Z*mirror_z, handle extends to -X.
    Rotate around Y (pitch) by +/-angle to open/close!
    """
    mp = MeshPart("metals")
    u0, v0, u1, v1 = UV_CHROME
    bu0, bv0, bu1, bv1 = UV_BRASS
    hy = 0.5 * thick
    ez = mirror_z

    # Tapered beveled blade sections from x=-0.5 to x=+blade_len
    prof = [
        (-0.55, 0.00, 0.48 * blade_w * ez),
        (0.00,  0.00, 0.62 * blade_w * ez),
        (blade_len * 0.52, -0.04 * blade_w * ez, 0.52 * blade_w * ez),
        (blade_len * 0.86, -0.06 * blade_w * ez, 0.28 * blade_w * ez),
        (blade_len,        -0.02 * blade_w * ez, 0.02 * blade_w * ez),
    ]
    for i in range(len(prof) - 1):
        xa, z_edge_a, z_sp_a = prof[i]
        xb, z_edge_b, z_sp_b = prof[i + 1]
        z_mid_a = 0.5 * (z_edge_a + z_sp_a)
        z_mid_b = 0.5 * (z_edge_b + z_sp_b)
        for sy in (-1.0, +1.0):
            # Spine bevel face
            p0 = (xa, sy * hy, z_sp_a)
            p1 = (xb, sy * hy, z_sp_b)
            p2 = (xb, sy * hy * 0.65, z_mid_b)
            p3 = (xa, sy * hy * 0.65, z_mid_a)
            mp.add_quad(p0, p1, p2, p3, (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=(0.0, sy, 0.15 * ez), two_sided=True)
            # Razor edge bevel face
            q0 = (xa, sy * hy * 0.65, z_mid_a)
            q1 = (xb, sy * hy * 0.65, z_mid_b)
            q2 = (xb, 0.0, z_edge_b)
            q3 = (xa, 0.0, z_edge_a)
            mp.add_quad(q0, q1, q2, q3, (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=(0.0, sy * 0.85, -0.52 * ez), two_sided=True)
        # Spine flat back
        mp.add_quad(
            (xa, -hy, z_sp_a), (xb, -hy, z_sp_b), (xb, +hy, z_sp_b), (xa, +hy, z_sp_a),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=(0.0, 0.0, ez), two_sided=True,
        )

    # Rear tang + oval finger-ring handle
    if tang_len > 0.1:
        tang_end = (-tang_len, 0.0, 0.42 * blade_w * ez)
        mp.add_tube(
            [(0.0, 0.0, 0.15 * blade_w * ez), tang_end],
            [0.24 * blade_w, 0.18 * blade_w],
            segs=8, uv_rect=handle_uv,
        )
        # Finger loop ring behind tang
        rc = (-tang_len - ring_r * 0.95, 0.0, (0.42 * blade_w + ring_r * 0.55) * ez)
        ring_pts = []
        for k in range(13):
            th = 2.0 * math.pi * (k / 12.0)
            ring_pts.append((rc[0] + ring_r * 1.15 * math.cos(th), 0.0, rc[2] + ring_r * 0.82 * math.sin(th)))
        mp.add_tube(ring_pts, [0.18] * len(ring_pts), segs=8, uv_rect=handle_uv, cap_start=False, cap_end=False)

    # Brass pivot bolt boss at (0, 0, 0)
    if with_pivot:
        mp.add_lathe(
            (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
            [
                (-hy * 1.6, 0.0),
                (-hy * 1.6, 0.34 * blade_w),
                (+hy * 1.6, 0.34 * blade_w),
                (+hy * 1.6, 0.0),
            ],
            segs=10, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
        )
    return mp


def build_kyle_head_3d(radius_y=1.35, radius_z=1.55, depth_x=0.14):
    """Builds a crisp 3D curved front+back floating Kyle head medallion (UV_CUT_HEAD) with zero ghost doubling."""
    mp = MeshPart("cutout")
    u0, v0, u1, v1 = UV_CUT_HEAD
    nx, nz = 4, 4

    def add_curved_face(face_sign):
        grid = []
        for iz in range(nz + 1):
            tz = iz / float(nz)
            z = -radius_z + 2.0 * radius_z * tz
            vv_uv = v1 + (v0 - v1) * tz
            row = []
            for iy in range(nx + 1):
                ty = iy / float(nx)
                if face_sign < 0:
                    y = +radius_y - 2.0 * radius_y * ty
                else:
                    y = -radius_y + 2.0 * radius_y * ty
                uu_uv = u0 + (u1 - u0) * ty
                ny_n = (ty - 0.5) * 2.0
                nz_n = (tz - 0.5) * 2.0
                dome = max(0.0, 1.0 - 0.45 * (ny_n * ny_n + nz_n * nz_n))
                x = face_sign * (0.03 + depth_x * dome)
                nrm = vnorm((face_sign, 0.28 * (y / max(radius_y, 1e-4)), 0.25 * (z / max(radius_z, 1e-4))))
                row.append(((x, y, z), (uu_uv, vv_uv), nrm))
            grid.append(row)

        for iz in range(nz):
            for iy in range(nx):
                p00, uv00, n00 = grid[iz][iy]
                p10, uv10, _   = grid[iz][iy + 1]
                p11, uv11, _   = grid[iz + 1][iy + 1]
                p01, uv01, _   = grid[iz + 1][iy]
                mp.add_quad(p00, p10, p11, p01, uv00, uv10, uv11, uv01, nrm=n00, two_sided=False)

    add_curved_face(-1.0)
    add_curved_face(+1.0)
    return mp


def build_kyle_body_3d(height=7.5, width=3.4, depth_x=0.14):
    """Builds a crisp 3D curved front+back photo-cutout mini Kyle (UV_CUT_BODY) with zero ghost doubling."""
    mp = MeshPart("cutout")
    u0, v0, u1, v1 = UV_CUT_BODY
    ny, nz = 4, 6
    hy = 0.5 * width
    hz = 0.5 * height

    def add_body_face(face_sign):
        grid = []
        for iz in range(nz + 1):
            tz = iz / float(nz)
            z = -hz + height * tz
            vv_uv = v1 + (v0 - v1) * tz
            row = []
            for iy in range(ny + 1):
                ty = iy / float(ny)
                y = (+hy - width * ty) if face_sign < 0 else (-hy + width * ty)
                uu_uv = u0 + (u1 - u0) * ty
                ny_n = (ty - 0.5) * 2.0
                dome = max(0.0, 1.0 - 0.6 * ny_n * ny_n)
                x = face_sign * (0.03 + depth_x * dome)
                nrm = vnorm((face_sign, 0.28 * (y / max(hy, 1e-4)), 0.0))
                row.append(((x, y, z), (uu_uv, vv_uv), nrm))
            grid.append(row)

        for iz in range(nz):
            for iy in range(ny):
                p00, uv00, n00 = grid[iz][iy]
                p10, uv10, _   = grid[iz][iy + 1]
                p11, uv11, _   = grid[iz + 1][iy + 1]
                p01, uv01, _   = grid[iz + 1][iy]
                mp.add_quad(p00, p10, p11, p01, uv00, uv10, uv11, uv01, nrm=n00, two_sided=False)

    add_body_face(-1.0)
    add_body_face(+1.0)
    return mp


def build_dollar_bill_3d(length=2.8, width=1.35, wave=0.18):
    """Curved fluttering $100 Kyle-Buck bill (centered at origin, lying in XY plane)."""
    mp = MeshPart("cutout")
    u0, v0, u1, v1 = UV_DOLLAR_BILL
    hx, hy = 0.5 * length, 0.5 * width
    nx = 4
    for i in range(nx):
        t0, t1 = i / float(nx), (i + 1) / float(nx)
        x0, x1 = -hx + length * t0, -hx + length * t1
        z0 = wave * math.sin(t0 * math.pi * 1.5)
        z1 = wave * math.sin(t1 * math.pi * 1.5)
        uu0 = u0 + (u1 - u0) * t0
        uu1 = u0 + (u1 - u0) * t1
        mp.add_quad(
            (x0, +hy, z0), (x1, +hy, z1), (x1, -hy, z1), (x0, -hy, z0),
            (uu0, v1), (uu1, v1), (uu1, v0), (uu0, v0),
            nrm=(0.0, 0.0, 1.0), two_sided=True,
        )
    return mp


def build_gold_coin_3d(radius=0.58, thick=0.14):
    """3D gleaming gold 50% coin."""
    mp = MeshPart("metals")
    mp.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        [
            (-0.5 * thick, 0.0, 0.0, radius),
            (-0.5 * thick, radius, 0.96, radius),
            (+0.5 * thick, radius, 0.96, radius),
            (+0.5 * thick, 0.0, 0.0, radius),
        ],
        segs=14, uv_mode="polar", uv_rect=UV_GOLD_COIN, up_hint=(0.0, 0.0, 1.0),
    )
    return mp


def build_fx_burst():
    """Additive scissor spark + shockwave ring + launch speed streaks."""
    fx = MeshPart("fx")
    # 1. Scissor spark starburst (facing -X)
    su0, sv0, su1, sv1 = UV_FX_SPARK
    fx.add_quad(
        (0.0, +1.0, -1.0), (0.0, -1.0, -1.0), (0.0, -1.0, +1.0), (0.0, +1.0, +1.0),
        (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    # 2. Shockwave ring (facing -X)
    ru0, rv0, ru1, rv1 = UV_FX_RING
    fx.add_quad(
        (0.6, +1.2, -1.2), (0.6, -1.2, -1.2), (0.6, -1.2, +1.2), (0.6, +1.2, +1.2),
        (ru0, rv1), (ru1, rv1), (ru1, rv0), (ru0, rv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    # 3. Crossed speed streak ribbons along +X
    tu0, tv0, tu1, tv1 = UV_FX_STREAK
    fx.add_quad(
        (-1.2, 0.0, -0.55), (+2.2, 0.0, -0.55), (+2.2, 0.0, +0.55), (-1.2, 0.0, +0.55),
        (tu0, tv1), (tu1, tv1), (tu1, tv0), (tu0, tv0), nrm=(0.0, 1.0, 0.0), two_sided=True,
    )
    fx.add_quad(
        (-1.2, -0.55, 0.0), (+2.2, -0.55, 0.0), (+2.2, +0.55, 0.0), (-1.2, +0.55, 0.0),
        (tu0, tv1), (tu1, tv1), (tu1, tv0), (tu0, tv0), nrm=(0.0, 0.0, 1.0), two_sided=True,
    )
    return fx


# ===========================================================================
# WEAPON 1: v_kyle_v1_cannon.md3 — 'THE KYLE CANNON'
# ===========================================================================
def build_v1_cannon():
    """Blow-dart/air-cannon barrel with giant steel scissor blades jutting from the muzzle,
    brass fittings, 50% CUT pressure dial, and a translucent glass pressure tube on top
    containing Kyle's floating bobbing head!
    """
    # Centered around X=14..32, Y=-9..-1, Z=-11..-2
    body = MeshPart("metals")

    # Main gunmetal air-cannon receiver & fluted barrel (X=11.5..27.5, Y=-4.5, Z=-6.8)
    yc, zc = -4.5, -6.8
    body.add_lathe(
        (11.5, yc, zc), (1.0, 0.0, 0.0),
        [
            (0.0, 0.0, 0.0),
            (0.0, 1.85, 0.1),
            (5.5, 1.92, 0.35),
            (5.8, 1.48, 0.42),
            (13.8, 1.38, 0.80),
            (14.0, 1.68, 0.85),
            (15.6, 1.68, 0.94),
            (15.8, 1.10, 0.98),
            (15.8, 0.0, 1.0),
        ],
        segs=18, uv_rect=UV_GUNMETAL, up_hint=(0.0, 0.0, 1.0),
    )

    # Ornate brass collars & breech bands
    for bx, bw, br in ((12.0, 1.0, 2.02), (17.2, 0.8, 1.66), (25.5, 1.2, 1.78)):
        body.add_lathe(
            (bx, yc, zc), (1.0, 0.0, 0.0),
            [(0.0, br * 0.92, 0.0), (0.0, br, 0.1), (bw, br, 0.9), (bw, br * 0.92, 1.0)],
            segs=18, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
        )

    # Brass end-caps & mounting stanchions for top glass pressure tube (X=15.0..23.5, Z=-3.5)
    tz = -3.35
    for sx in (15.2, 23.2):
        # Vertical brass stanchion from barrel to glass tube
        body.add_chamfer_box(sx - 0.45, sx + 0.45, yc - 0.55, yc + 0.55, zc + 1.2, tz - 1.35, ch=0.08, uv_rect=UV_BRASS)
        # Brass tube end-cap flange
        body.add_lathe(
            (sx - 0.55, yc, tz), (1.0, 0.0, 0.0),
            [(0.0, 0.0, 0.0), (0.0, 1.78, 0.1), (0.95, 1.78, 0.9), (0.95, 0.0, 1.0)],
            segs=18, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
        )
    # Top brass connecting pressure pipe across the glass tank
    body.add_tube([(15.2, yc, tz + 1.85), (23.2, yc, tz + 1.85)], [0.22, 0.22], segs=8, uv_rect=UV_BRASS)

    # Side '50% CUT' PSI pressure gauge tilted toward player (-X, -Y)
    gx, gy, gz = 16.5, yc + 1.75, zc + 0.65
    body.add_lathe(
        (gx, gy, gz), (-0.45, 0.85, 0.25),
        [(0.0, 0.0, 0.0), (0.0, 1.15, 0.1), (0.55, 1.15, 0.9), (0.55, 0.0, 1.0)],
        segs=16, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
    )
    # Dial face facing -X/+Y toward camera
    gu0, gv0, gu1, gv1 = UV_PSI_GAUGE
    d_c = (gx - 0.26, gy + 0.48, gz + 0.14)
    body.add_quad(
        vadd(d_c, (-0.1, +0.92, -0.92)), vadd(d_c, (-0.1, -0.92, -0.92)),
        vadd(d_c, (-0.1, -0.92, +0.92)), vadd(d_c, (-0.1, +0.92, +0.92)),
        (gu0, gv1), (gu1, gv1), (gu1, gv0), (gu0, gv0),
        nrm=vnorm((-0.85, 0.45, 0.2)), two_sided=True,
    )

    # Rear angled pistol grip
    body.add_tube(
        [(13.0, yc, zc - 1.5), (12.4, yc - 0.1, zc - 3.2), (11.8, yc - 0.2, zc - 4.8)],
        [0.62, 0.56, 0.64], segs=10, uv_rect=UV_GUNMETAL,
    )

    # Dynamic parts: under-barrel pump grip, upper & lower giant muzzle scissor blades, Kyle floating head, mini-Kyle projectile, glass tube, FX
    pump = MeshPart("metals")
    pump.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [(0.0, 0.78, 0.0), (0.0, 1.05, 0.15), (3.8, 1.05, 0.85), (3.8, 0.78, 1.0)],
        segs=12, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
    )
    blade_top = build_scissor_half(blade_len=6.6, blade_w=1.28, thick=0.22, tang_len=1.8, ring_r=0.72, mirror_z=1.0, with_pivot=True, handle_uv=UV_BRASS)
    blade_bot = build_scissor_half(blade_len=6.6, blade_w=1.28, thick=0.22, tang_len=1.8, ring_r=0.72, mirror_z=-1.0, with_pivot=False, handle_uv=UV_BRASS)

    kyle_head = build_kyle_head_3d(radius_y=1.42, radius_z=1.55, depth_x=0.14)
    kyle_proj = build_kyle_body_3d(height=5.2, width=2.4, depth_x=0.14)

    # Translucent glass pressure tube around Kyle's floating head (X=15.6..22.8, Z=tz)
    glass = MeshPart("glass")
    glass.add_lathe(
        (15.65, yc, tz), (1.0, 0.0, 0.0),
        [(0.0, 1.85, 0.02), (7.10, 1.85, 0.98)],
        segs=22, uv_rect=(0.0, 0.0, 1.0, 1.0), up_hint=(0.0, 0.0, 1.0),
    )

    fx_part = build_fx_burst()
    hand_r = build_articulated_ranger_hand(
        palm_center=(12.4, yc - 0.1, zc - 3.0),
        fwd_dir=(0.76, 0.44, 0.48), up_dir=(-0.22, -0.52, 0.82),
        side_sign=-1.0, finger_curls=(0.75, 0.86, 0.88, 0.88), hand_scale=0.80, forearm_len=7.5,
    )
    hand_l_tpl = build_articulated_ranger_hand(
        palm_center=(0.0, 0.0, 0.0),
        fwd_dir=(0.35, -0.55, 0.75), up_dir=(-0.25, 0.78, 0.56),
        side_sign=+1.0, finger_curls=(0.82, 0.86, 0.88, 0.88), hand_scale=0.78, forearm_len=7.5,
    )

    met_parts = [body, pump, blade_top, blade_bot]
    met_st, met_tris = merge_topology(met_parts)
    cut_parts = [kyle_head, kyle_proj]
    cut_st, cut_tris = merge_topology(cut_parts)
    hnd_parts = [hand_r, hand_l_tpl]
    hnd_st, hnd_tris = merge_topology(hnd_parts)

    met_fr, cut_fr, gls_fr, hnd_fr, fx_fr = [], [], [], [], []
    cant_kw = dict(origin=(18.5, yc, zc), shift=(-0.5, -0.8, 0.4), yaw=16.0, pitch=4.0, roll=-5.0, scale=1.18)

    for fi in range(36):
        sw_dx = sw_dz = sw_ry = sw_rx = 0.0
        pump_dx = 0.0
        snip_deg = 12.0
        head_bob = 0.0
        head_rz = -52.0   # smile toward player's 1st-person POV through side of glass tube!
        head_rx = 0.0
        head_sc = 1.0
        proj_x = 24.0
        proj_sc = 0.001
        fx_sc = 0.001
        fx_x = 28.0

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            sw_dx = 0.20 * math.sin(ph)
            sw_dz = 0.22 * math.sin(ph * 2.0)
            sw_ry = 0.8 * math.sin(ph)
            snip_deg = 10.0 + 5.0 * math.sin(ph)
            head_bob = 0.24 * math.sin(ph * 2.0)
            head_rz = -52.0 + 16.0 * math.sin(ph)
            head_rx = 8.0 * math.cos(ph)
        elif fi < 28:
            k = fi - 16  # 0..11
            t = k / 11.0
            snip_deg = 3.0 + 26.0 * (0.5 + 0.5 * math.sin(t * math.pi * 6.0))
            pump_dx = -1.6 * math.sin(t * math.pi * 3.0)
            sw_dx = -0.5 * t + 0.15 * math.sin(k * 2.4)
            sw_dz = 0.18 * math.cos(k * 2.8)
            head_bob = 0.28 * math.sin(k * 2.1)
            head_rz = -52.0 + 35.0 * math.sin(k * 1.6)
            head_rx = 16.0 * math.cos(k * 2.0)
        else:
            k = fi - 28  # 0..7
            if k == 0:
                snip_deg = 1.5
                sw_dx, sw_ry = -2.2, -5.5
                proj_x, proj_sc = 28.5, 0.85
                fx_sc, fx_x = 3.4, 29.0
                head_sc = 0.35
            elif k == 1:
                snip_deg = 2.0
                sw_dx, sw_ry = -2.8, -7.0
                proj_x, proj_sc = 37.0, 0.65
                fx_sc, fx_x = 2.4, 30.5
                head_sc = 0.15
            elif k == 2:
                snip_deg = 16.0
                sw_dx, sw_ry = -1.6, -4.0
                proj_x, proj_sc = 45.0, 0.001
                fx_sc = 0.9
                head_sc = 0.25
            else:
                tr = (k - 2) / 5.0
                s = smoothstep(tr)
                sw_dx = -1.6 * (1.0 - s)
                sw_ry = -4.0 * (1.0 - s)
                snip_deg = 16.0 - 6.0 * s
                head_sc = 0.25 + 0.75 * s
                head_bob = -0.8 * (1.0 - s)
                head_rz = -52.0 + 360.0 * (1.0 - s)

        mv, mn = combine_parts([
            (body, dict()),
            (pump, dict(pos=(19.2 + pump_dx, yc, zc - 1.55))),
            (blade_top, dict(pos=(26.2, yc, zc + 0.25), ry=-snip_deg)),
            (blade_bot, dict(pos=(26.2, yc, zc - 0.25), ry=+snip_deg)),
        ])
        mv, mn = apply_sway(mv, mn, pos=(sw_dx, 0.0, sw_dz), rx=sw_rx, ry=sw_ry)
        met_fr.append(apply_quake_cant(mv, mn, **cant_kw))

        cv, cn = combine_parts([
            (kyle_head, dict(pos=(19.2, yc, tz + head_bob), rx=head_rx, rz=head_rz, scale=head_sc)),
            (kyle_proj, dict(pos=(proj_x, yc, zc), ry=88.0, rz=0.0, scale=proj_sc)),
        ])
        cv, cn = apply_sway(cv, cn, pos=(sw_dx, 0.0, sw_dz), rx=sw_rx, ry=sw_ry)
        cut_fr.append(apply_quake_cant(cv, cn, **cant_kw))

        gv, gn = transform_part(glass)
        gv, gn = apply_sway(gv, gn, pos=(sw_dx, 0.0, sw_dz), rx=sw_rx, ry=sw_ry)
        gls_fr.append(apply_quake_cant(gv, gn, **cant_kw))

        hv, hn = combine_parts([
            (hand_r, dict()),
            (hand_l_tpl, dict(pos=(21.1 + pump_dx, yc + 0.35, zc - 2.35))),
        ])
        hv, hn = apply_sway(hv, hn, pos=(sw_dx, 0.0, sw_dz), rx=sw_rx, ry=sw_ry)
        hnd_fr.append(apply_quake_cant(hv, hn, **cant_kw))

        fv, fn = transform_part(fx_part, pos=(fx_x, yc, zc), rx=fi * 40.0, scale=fx_sc)
        fv, fn = apply_sway(fv, fn, pos=(sw_dx, 0.0, sw_dz), rx=sw_rx, ry=sw_ry)
        fx_fr.append(apply_quake_cant(fv, fn, **cant_kw))

    return [
        pack_surface("cannon_metal", "metals", "kyle_metals", met_st, met_tris, met_fr),
        pack_surface("cannon_hands", "hand",   "kyle_hand",   hnd_st, hnd_tris, hnd_fr),
        pack_surface("cannon_kyle",  "cutout", "kyle_cutout", cut_st, cut_tris, cut_fr),
        pack_surface("cannon_glass", "glass",  "kyle_glass",  glass.st, glass.tris, gls_fr),
        pack_surface("cannon_fx",    "fx",     "kyle_fx",     fx_part.st, fx_part.tris, fx_fr),
    ], dict(
        id="v_kyle_v1_cannon",
        title="The Kyle Cannon",
        subtitle="Brass Blow-Dart Cannon w/ Scissor Bayonet & Glass Kyle Head Tank",
        flavor="Pressurized to 50% commission! Kyle's smiling head bobs in the glass boiler while giant steel shears chop the air.",
        muzzle=[28.0, yc, zc],
        orbitCenter=[20.5, yc, -5.2],
        orbitDist=24.0,
    )


# ===========================================================================
# WEAPON 2: v_kyle_v2_hand.md3 — 'HAND-HELD KYLE DART'
# ===========================================================================
def build_v2_hand():
    """Gloved first-person hand gripping mini Kyle directly by his khakis;
    he holds giant scissors overhead and frantically snips faster on lock, then gets yeeted like a dart!
    """
    yc, zc = -4.2, -6.5
    kyle_doll = build_kyle_body_3d(height=7.8, width=3.5, depth_x=0.45)

    # Mini 3D blue polo arms reaching up overhead to hold the giant scissors
    arms = MeshPart("metals")
    for sgn in (-1.0, +1.0):
        arms.add_tube(
            [(0.0, sgn * 1.15, 1.35), (0.35, sgn * 1.45, 2.85), (0.55, sgn * 0.55, 4.10)],
            [0.34, 0.28, 0.24], segs=8, uv_rect=UV_GUNMETAL,
        )

    blade_l = build_scissor_half(blade_len=5.6, blade_w=0.95, thick=0.18, tang_len=1.9, ring_r=0.62, mirror_z=1.0, with_pivot=True)
    blade_r = build_scissor_half(blade_len=5.6, blade_w=0.95, thick=0.18, tang_len=1.9, ring_r=0.62, mirror_z=-1.0, with_pivot=False)

    # Right Ranger Hand (grips Kyle by his khakis!) - build open & closed poses as morphable topology?
    # Wait: build_articulated_ranger_hand generates identical vertex counts for different finger_curls!
    # Let's verify: yes, finger_curls only affects joint angles, not topology!
    hand_r0 = build_articulated_ranger_hand(
        palm_center=(0.0, 0.0, 0.0),
        fwd_dir=(0.35, 0.92, 0.15), up_dir=(-0.20, -0.08, 0.98),
        side_sign=-1.0, finger_curls=(0.82, 0.85, 0.88, 0.88), hand_scale=0.92, forearm_len=9.5,
    )
    # Left stabilizing hand tucked lower-left
    hand_l0 = build_articulated_ranger_hand(
        palm_center=(0.0, 0.0, 0.0),
        fwd_dir=(0.82, -0.45, 0.35), up_dir=(-0.20, 0.42, 0.88),
        side_sign=+1.0, finger_curls=(0.65, 0.70, 0.72, 0.75), hand_scale=0.84, forearm_len=9.5,
    )
    fx_part = build_fx_burst()

    met_parts = [arms, blade_l, blade_r]
    met_st, met_tris = merge_topology(met_parts)
    hnd_st, hnd_tris = merge_topology([hand_r0, hand_l0])

    met_fr, cut_fr, hnd_fr, fx_fr = [], [], [], []
    cant_kw = dict(origin=(19.5, yc, zc), shift=(-1.2, -0.5, 0.8), yaw=12.0, pitch=3.0, roll=-3.0, scale=1.22)

    for fi in range(36):
        kyle_pos = (21.5, yc, zc + 0.5)
        kyle_ry = -12.0   # tilted slightly forward like a dart
        kyle_rz = -26.0   # facing 3/4 toward player camera!
        kyle_rx = 0.0
        kyle_sc = 1.0
        snip_deg = 16.0
        hr_pos = (20.2, yc - 0.9, zc - 1.35)
        hr_curl = (0.82, 0.85, 0.88, 0.88)
        hl_pos = (16.5, yc + 4.4, zc - 3.2)
        fx_sc = 0.001
        fx_pos = (25.0, yc, zc)

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            kyle_pos = (21.5 + 0.25 * math.sin(ph), yc, zc + 0.5 + 0.28 * math.sin(ph * 2.0))
            kyle_ry = -12.0 + 3.5 * math.sin(ph)
            hr_pos = (20.2 + 0.25 * math.sin(ph), yc - 0.9, zc - 1.35 + 0.28 * math.sin(ph * 2.0))
            snip_deg = 14.0 + 6.0 * math.sin(ph * 2.0)
        elif fi < 28:
            k = fi - 16
            t = k / 11.0
            cock_x = -2.6 * smoothstep(min(1.0, t * 1.4))
            jitter_z = 0.22 * math.sin(k * 2.7)
            kyle_pos = (21.5 + cock_x, yc - 0.3 * t, zc + 0.7 + jitter_z)
            kyle_ry = -12.0 - 18.0 * smoothstep(t)
            kyle_rx = 10.0 * math.sin(k * 2.2)
            hr_pos = (20.2 + cock_x, yc - 1.1 - 0.3 * t, zc - 1.15 + jitter_z)
            hl_pos = (17.2 + cock_x * 0.5, yc + 3.8, zc - 2.6)
            snip_deg = 3.0 + 32.0 * (0.5 + 0.5 * math.sin(t * math.pi * 7.5))
        else:
            k = fi - 28  # 0..7
            if k == 0:
                kyle_pos = (27.5, yc + 0.5, zc + 1.4)
                kyle_ry = 82.0
                kyle_rz = 0.0
                hr_pos = (23.8, yc - 0.6, zc - 0.8)
                hr_curl = (0.15, 0.18, 0.20, 0.22)
                snip_deg = 4.0
                fx_sc, fx_pos = 3.2, (25.5, yc + 0.2, zc + 0.8)
            elif k == 1:
                kyle_pos = (36.5, yc + 1.1, zc + 2.0)
                kyle_ry = 88.0
                kyle_rz = 0.0
                kyle_sc = 0.85
                hr_pos = (24.5, yc - 0.4, zc - 1.1)
                hr_curl = (0.10, 0.12, 0.14, 0.16)
                snip_deg = 2.0
                fx_sc, fx_pos = 2.6, (30.0, yc + 0.6, zc + 1.2)
            elif k == 2:
                kyle_pos = (45.0, yc + 1.5, zc + 2.5)
                kyle_sc = 0.001
                hr_pos = (22.5, yc - 0.8, zc - 2.2)
                hr_curl = (0.25, 0.28, 0.30, 0.32)
            else:
                tr = (k - 2) / 5.0
                s = smoothstep(tr)
                kyle_pos = (21.5, yc, zc - 6.5 * (1.0 - s) + 0.5 * s)
                kyle_ry = -12.0 * s
                kyle_sc = 0.2 + 0.8 * s
                hr_pos = (20.2, yc - 0.9, zc - 5.5 * (1.0 - s) - 1.35 * s)
                hr_curl = (0.82, 0.85, 0.88, 0.88)
                snip_deg = 14.0

        kv, kn = transform_part(kyle_doll, pos=kyle_pos, rx=kyle_rx, ry=kyle_ry, rz=kyle_rz, scale=kyle_sc)
        cut_fr.append(apply_quake_cant(kv, kn, **cant_kw))

        # Mini Kyle's overhead arms + giant scissor blades angled diagonally so scissor chomp reads boldly in 1st-person!
        sc_rz = kyle_rz - 55.0 if fi < 28 else kyle_rz
        sc_piv = vadd(kyle_pos, rot_z(rot_y((0.4, 0.0, 4.35 * kyle_sc), kyle_ry), kyle_rz))
        mv, mn = combine_parts([
            (arms, dict(pos=kyle_pos, rx=kyle_rx, ry=kyle_ry, rz=kyle_rz, scale=kyle_sc)),
            (blade_l, dict(pos=sc_piv, rx=kyle_rx, ry=kyle_ry - snip_deg, rz=sc_rz, scale=kyle_sc)),
            (blade_r, dict(pos=sc_piv, rx=kyle_rx, ry=kyle_ry + snip_deg, rz=sc_rz, scale=kyle_sc)),
        ])
        met_fr.append(apply_quake_cant(mv, mn, **cant_kw))

        hr_k = build_articulated_ranger_hand(
            palm_center=hr_pos,
            fwd_dir=(0.35, 0.92, 0.15), up_dir=(-0.20, -0.08, 0.98),
            side_sign=-1.0, finger_curls=hr_curl, hand_scale=0.92, forearm_len=9.5,
        )
        hl_k = build_articulated_ranger_hand(
            palm_center=hl_pos,
            fwd_dir=(0.82, -0.45, 0.35), up_dir=(-0.20, 0.42, 0.88),
            side_sign=+1.0, finger_curls=(0.65, 0.70, 0.72, 0.75), hand_scale=0.84, forearm_len=9.5,
        )
        hnd_fr.append(apply_quake_cant(hr_k.verts + hl_k.verts, hr_k.norms + hl_k.norms, **cant_kw))

        fv, fn = transform_part(fx_part, pos=fx_pos, rx=fi * 35.0, scale=fx_sc)
        fx_fr.append(apply_quake_cant(fv, fn, **cant_kw))

    return [
        pack_surface("hand_scissors", "metals", "kyle_metals", met_st, met_tris, met_fr),
        pack_surface("hand_gloves",   "hand",   "kyle_hand",   hnd_st, hnd_tris, hnd_fr),
        pack_surface("hand_kyle",     "cutout", "kyle_cutout", kyle_doll.st, kyle_doll.tris, cut_fr),
        pack_surface("hand_fx",       "fx",     "kyle_fx",     fx_part.st, fx_part.tris, fx_fr),
    ], dict(
        id="v_kyle_v2_hand",
        title="Hand-Held Kyle Dart",
        subtitle="First-Person Ranger Glove Gripping Mini-Kyle by the Khakis",
        flavor="Direct kinetic persuasion: squeeze Kyle's khakis to charge his overhead scissor frenzy, then yeet him like a lawn dart!",
        muzzle=[26.0, yc, zc + 1.0],
        orbitCenter=[20.5, yc, zc],
        orbitDist=21.5,
    )


# ===========================================================================
# WEAPON 3: v_kyle_v3_register.md3 — 'COMMISSION CASH-REGISTER LAUNCHER'
# ===========================================================================
def build_v3_register():
    """Vintage brass/green barber cash register with scissor-blade guide rails,
    hand crank that spins on lock, and popping cash drawer bursting with dollar bills when Kyle launches!
    """
    yc, zc = -4.2, -7.8
    reg = MeshPart("metals")

    # Vintage tiered green enamel + brass cash register body (X=14.5..24.5, Y=yc, Z=zc)
    reg.add_chamfer_box(14.5, 24.5, yc - 3.6, yc + 3.6, zc - 2.2, zc + 0.3, ch=0.18, uv_rect=UV_BRASS)
    reg.add_chamfer_box(15.2, 23.8, yc - 3.3, yc + 3.3, zc + 0.3, zc + 3.2, ch=0.28, uv_rect=UV_REG_GREEN)
    # Sloped brass keyboard bank at rear facing player
    reg.add_loft([
        (14.8, yc, 3.1, zc + 0.6, 0.45, 0.10),
        (18.0, yc, 3.1, zc + 2.6, 0.45, 0.10),
    ], uv_rect=UV_BRASS)
    # Two rows of chunky brass register keys
    for row in range(2):
        for col in range(5):
            kx = 15.6 + row * 1.15
            ky = yc - 2.0 + col * 1.0
            kz = zc + 1.25 + row * 0.65
            reg.add_chamfer_box(kx - 0.32, kx + 0.32, ky - 0.32, ky + 0.32, kz, kz + 0.45, ch=0.05, uv_rect=UV_GOLD_COIN)

    # Top display marquee frame ('50% CUT // PAY UP!') facing -X
    reg.add_chamfer_box(19.5, 22.8, yc - 3.1, yc + 3.1, zc + 3.2, zc + 5.1, ch=0.12, uv_rect=UV_BRASS)
    mu0, mv0, mu1, mv1 = (0.52, 0.77, 0.98, 0.87)
    reg.add_quad(
        (19.44, yc + 2.8, zc + 3.4), (19.44, yc - 2.8, zc + 3.4),
        (19.44, yc - 2.8, zc + 4.9), (19.44, yc + 2.8, zc + 4.9),
        (mu0, mv1), (mu1, mv1), (mu1, mv0), (mu0, mv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )

    # Dynamic parts: Side brass hand crank, Twin scissor-blade guide rails on top, Sliding cash drawer, Dollar bills + Gold coins, Kyle payload
    crank = MeshPart("metals")
    crank.add_tube([(0.0, 0.0, 0.0), (0.0, 1.1, 0.0), (0.0, 1.1, 2.1), (0.0, 2.0, 2.1)], [0.22, 0.22, 0.20, 0.28], segs=8, uv_rect=UV_BRASS)

    rail_l = build_scissor_half(blade_len=8.5, blade_w=0.95, thick=0.18, tang_len=1.5, ring_r=0.55, mirror_z=1.0, with_pivot=True)
    rail_r = build_scissor_half(blade_len=8.5, blade_w=0.95, thick=0.18, tang_len=1.5, ring_r=0.55, mirror_z=-1.0, with_pivot=False)

    drawer = MeshPart("metals")
    drawer.add_chamfer_box(-3.6, +3.6, -3.2, +3.2, -0.95, +0.95, ch=0.10, uv_rect=UV_BRASS)
    # Drawer pull handle on front (+X)
    drawer.add_tube([(3.65, -1.1, 0.0), (4.25, -1.1, 0.0), (4.25, +1.1, 0.0), (3.65, +1.1, 0.0)], [0.16] * 4, segs=8, uv_rect=UV_GOLD_COIN)

    coin_tpl = build_gold_coin_3d(radius=0.52, thick=0.12)
    bill_tpl = build_dollar_bill_3d(length=2.6, width=1.25, wave=0.22)
    kyle_doll = build_kyle_body_3d(height=5.8, width=2.6, depth_x=0.40)
    fx_part = build_fx_burst()

    hand_r = build_articulated_ranger_hand(
        palm_center=(14.4, yc - 2.6, zc - 0.5),
        fwd_dir=(0.75, 0.45, 0.48), up_dir=(-0.22, -0.48, 0.85),
        side_sign=-1.0, finger_curls=(0.75, 0.82, 0.85, 0.85), hand_scale=0.80, forearm_len=7.5,
    )
    hand_l_tpl = build_articulated_ranger_hand(
        palm_center=(0.0, 0.0, 0.0),
        fwd_dir=(0.40, -0.78, 0.48), up_dir=(-0.20, 0.45, 0.87),
        side_sign=+1.0, finger_curls=(0.82, 0.86, 0.88, 0.88), hand_scale=0.78, forearm_len=7.5,
    )

    # 4 coins + 5 bills bursting from cash drawer
    met_parts = [reg, crank, rail_l, rail_r, drawer] + [coin_tpl] * 4
    met_st, met_tris = merge_topology(met_parts)
    cut_parts = [kyle_doll] + [bill_tpl] * 5
    cut_st, cut_tris = merge_topology(cut_parts)
    hnd_st, hnd_tris = merge_topology([hand_r, hand_l_tpl])

    met_fr, cut_fr, hnd_fr, fx_fr = [], [], [], []
    crank_piv = (19.6, yc + 3.45, zc + 1.4)
    cant_kw = dict(origin=(19.5, yc, zc), shift=(-0.8, -0.5, 0.8), yaw=18.0, pitch=4.0, roll=-5.0, scale=1.18)

    for fi in range(36):
        sw_dx = sw_dz = sw_ry = 0.0
        crank_deg = 0.0
        rail_snip = 10.0
        drawer_x = 20.6
        burst_t = 0.0
        kyle_pos = (24.0, yc, zc + 5.8)
        kyle_ry = -8.0
        kyle_sc = 0.90
        fx_sc = 0.001

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            sw_dz = 0.22 * math.sin(ph * 2.0)
            sw_dx = 0.15 * math.sin(ph)
            crank_deg = 12.0 * math.sin(ph)
            rail_snip = 10.0 + 3.0 * math.sin(ph)
            kyle_pos = (24.0, yc, zc + 5.8 + 0.16 * math.sin(ph * 2.0))
        elif fi < 28:
            k = fi - 16
            t = k / 11.0
            crank_deg = 1080.0 * t
            rail_snip = 2.0 + 18.0 * (0.5 + 0.5 * math.sin(t * math.pi * 6.0))
            sw_dx = -0.4 * t + 0.15 * math.sin(k * 2.5)
            kyle_pos = (24.0 + 0.4 * math.sin(k * 2.0), yc, zc + 5.8 + 0.25 * math.cos(k * 2.2))
            kyle_ry = -15.0 * t
        else:
            k = fi - 28
            if k <= 3:
                drawer_x = 20.6 + 5.2 * smoothstep(min(1.0, k * 0.85 + 0.35))
                burst_t = 0.2 + 0.8 * (k / 3.0)
                sw_dx = -2.2 * math.exp(-k * 0.5)
                sw_ry = -5.5 * math.exp(-k * 0.5)
                kyle_pos = (26.5 + 8.5 * k, yc, zc + 6.2 + 1.2 * k)
                kyle_ry = 75.0
                kyle_sc = 0.90 if k <= 1 else (0.5 if k == 2 else 0.001)
                fx_sc = 3.2 if k == 0 else (2.0 if k == 1 else 0.001)
            else:
                tr = (k - 3) / 4.0
                s = smoothstep(tr)
                drawer_x = 25.8 - 5.2 * s
                burst_t = max(0.0, 1.0 - tr * 1.3)
                kyle_pos = (24.0, yc, zc + 1.5 + 4.3 * s)
                kyle_sc = 0.2 + 0.7 * s

        cr_rad = math.radians(crank_deg)
        hand_l_pos = (
            crank_piv[0] - 2.1 * math.sin(cr_rad),
            crank_piv[1] + 2.0,
            crank_piv[2] + 2.1 * math.cos(cr_rad),
        )

        coin_xforms = []
        for ci in range(4):
            ang = (ci - 1.5) * 0.55
            c_sc = 0.001 if burst_t <= 0.02 else 0.95 * math.sin(min(1.0, burst_t) * math.pi * 0.85 + 0.2)
            c_pos = (
                drawer_x + 2.2 + 4.5 * burst_t,
                yc + math.sin(ang) * (1.2 + 3.8 * burst_t),
                zc + 0.8 + 4.2 * burst_t - 2.5 * burst_t * burst_t + ci * 0.3,
            )
            coin_xforms.append((coin_tpl, dict(pos=c_pos, rx=fi * 45.0 + ci * 30.0, rz=fi * 60.0, scale=c_sc)))

        mv, mn = combine_parts([
            (reg, dict()),
            (crank, dict(pos=crank_piv, ry=crank_deg)),
            (rail_l, dict(pos=(21.5, yc + 1.45, zc + 4.6), rx=90.0, ry=-rail_snip)),
            (rail_r, dict(pos=(21.5, yc - 1.45, zc + 4.6), rx=90.0, ry=+rail_snip)),
            (drawer, dict(pos=(drawer_x, yc, zc - 1.0))),
        ] + coin_xforms)
        mv, mn = apply_sway(mv, mn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        met_fr.append(apply_quake_cant(mv, mn, **cant_kw))

        bill_xforms = []
        for bi in range(5):
            ang = (bi - 2.0) * 0.42
            b_sc = 0.001 if burst_t <= 0.02 else 0.95
            b_pos = (
                drawer_x + 2.5 + 5.0 * burst_t,
                yc + math.sin(ang) * (1.4 + 4.6 * burst_t),
                zc + 0.5 + 4.8 * burst_t - 1.8 * burst_t * burst_t + bi * 0.25,
            )
            bill_xforms.append((bill_tpl, dict(pos=b_pos, rx=35.0 * math.sin(fi + bi), ry=-25.0 + 20.0 * bi, rz=ang * 45.0, scale=b_sc)))

        cv, cn = combine_parts([
            (kyle_doll, dict(pos=kyle_pos, ry=kyle_ry, rz=-24.0, scale=kyle_sc)),
        ] + bill_xforms)
        cv, cn = apply_sway(cv, cn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        cut_fr.append(apply_quake_cant(cv, cn, **cant_kw))

        hl_k = build_articulated_ranger_hand(
            palm_center=hand_l_pos,
            fwd_dir=(0.40, -0.78, 0.48), up_dir=(-0.20, 0.45, 0.87),
            side_sign=+1.0, finger_curls=(0.82, 0.86, 0.88, 0.88), hand_scale=0.78, forearm_len=7.5,
        )
        hv, hn = apply_sway(hand_r.verts + hl_k.verts, hand_r.norms + hl_k.norms, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        hnd_fr.append(apply_quake_cant(hv, hn, **cant_kw))

        fv, fn = transform_part(fx_part, pos=(27.5, yc, zc + 5.2), scale=fx_sc)
        fv, fn = apply_sway(fv, fn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        fx_fr.append(apply_quake_cant(fv, fn, **cant_kw))

    return [
        pack_surface("register_metal", "metals", "kyle_metals", met_st, met_tris, met_fr),
        pack_surface("register_hands", "hand",   "kyle_hand",   hnd_st, hnd_tris, hnd_fr),
        pack_surface("register_kyle",  "cutout", "kyle_cutout", cut_st, cut_tris, cut_fr),
        pack_surface("register_fx",    "fx",     "kyle_fx",     fx_part.st, fx_part.tris, fx_fr),
    ], dict(
        id="v_kyle_v3_register",
        title="Commission Cash-Register Launcher",
        subtitle="Vintage Barber Register w/ Scissor Rails, Spinning Crank & Cash Burst",
        flavor="Hold fire to crank up his 50% commission; release for a CHA-CHING cash drawer eruption that launches Kyle downrange!",
        muzzle=[28.0, yc, zc + 5.6],
        orbitCenter=[20.5, yc, zc + 2.2],
        orbitDist=24.5,
    )


# ===========================================================================
# WEAPON 4: v_kyle_v4_shears.md3 — 'GIANT BARBER-SHEARS RAILGUN'
# ===========================================================================
def build_v4_shears():
    """Massive gleaming chrome tailor's shears hinged in 1st-person that spread wide
    during lock-on with a spinning barber pole core and mini Kyle chambered inside the blades!
    """
    yc, zc = -4.0, -6.2
    piv_x = 18.0

    # Massive chrome shear halves hinged around Z axis (horizontal Y-plane scissor chomp!) or Y axis (vertical)?
    # Let's angle them at 28 deg roll so BOTH giant blades & finger rings read heroically in 1st-person POV!
    blade_u = build_scissor_half(blade_len=13.5, blade_w=2.05, thick=0.34, tang_len=4.2, ring_r=1.25, mirror_z=1.0, with_pivot=True)
    blade_d = build_scissor_half(blade_len=13.5, blade_w=2.05, thick=0.34, tang_len=4.2, ring_r=1.25, mirror_z=-1.0, with_pivot=False)

    # Spinning Red-White-Blue Barber Pole core down the railgun spine
    barber_pole = MeshPart("metals")
    barber_pole.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [
            (0.0, 0.0, 0.0),
            (0.0, 0.88, 0.05),
            (9.5, 0.88, 0.95),
            (9.5, 0.0, 1.0),
        ],
        segs=18, uv_rect=UV_BARBER_POLE, up_hint=(0.0, 0.0, 1.0),
    )
    # Brass end-caps on barber pole core
    for bx in (-0.35, 9.5):
        barber_pole.add_lathe(
            (bx, 0.0, 0.0), (1.0, 0.0, 0.0),
            [(0.0, 0.0, 0.0), (0.0, 1.05, 0.1), (0.45, 1.05, 0.9), (0.45, 0.0, 1.0)],
            segs=16, uv_rect=UV_BRASS, up_hint=(0.0, 0.0, 1.0),
        )

    kyle_doll = build_kyle_body_3d(height=5.4, width=2.45, depth_x=0.38)
    fx_part = build_fx_burst()

    hand_r = build_articulated_ranger_hand(
        palm_center=(13.2, yc - 0.6, zc - 2.0),
        fwd_dir=(0.80, 0.38, 0.46), up_dir=(-0.22, -0.45, 0.86),
        side_sign=-1.0, finger_curls=(0.82, 0.86, 0.88, 0.88), hand_scale=0.84, forearm_len=7.5,
    )
    hand_l = build_articulated_ranger_hand(
        palm_center=(14.5, yc + 2.8, zc + 0.6),
        fwd_dir=(0.76, -0.52, 0.38), up_dir=(-0.18, 0.42, 0.88),
        side_sign=+1.0, finger_curls=(0.80, 0.84, 0.86, 0.86), hand_scale=0.80, forearm_len=7.5,
    )

    met_parts = [blade_u, blade_d, barber_pole]
    met_st, met_tris = merge_topology(met_parts)
    hnd_st, hnd_tris = merge_topology([hand_r, hand_l])

    met_fr, cut_fr, hnd_fr, fx_fr = [], [], [], []
    cant_kw = dict(origin=(18.5, yc, zc), shift=(-0.6, -0.4, 0.5), yaw=18.0, pitch=5.0, roll=-8.0, scale=1.22)

    for fi in range(36):
        sw_dx = sw_dz = sw_ry = 0.0
        shear_deg = 12.0
        pole_spin = 0.0
        kyle_pos = (23.2, yc, zc + 0.6)
        kyle_sc = 0.92
        fx_sc = 0.001

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            sw_dx = 0.2 * math.sin(ph)
            sw_dz = 0.22 * math.sin(ph * 2.0)
            shear_deg = 13.0 + 3.0 * math.sin(ph)
            pole_spin = fi * (360.0 / 16.0)
            kyle_pos = (23.2, yc, zc + 0.6 + 0.18 * math.sin(ph * 2.0))
        elif fi < 28:
            k = fi - 16
            t = k / 11.0
            shear_deg = 13.0 + 21.0 * smoothstep(t) + 3.5 * math.sin(k * 2.6)
            pole_spin = fi * 55.0
            sw_dx = -0.8 * t + 0.14 * math.sin(k * 3.0)
            kyle_pos = (23.2 - 0.6 * t, yc, zc + 0.6 + 0.20 * math.sin(k * 2.4))
            fx_sc = 0.7 + 0.6 * t
        else:
            k = fi - 28  # 0..7
            if k == 0:
                shear_deg = 0.5
                sw_dx, sw_ry = -2.6, -6.5
                pole_spin = fi * 70.0
                kyle_pos = (29.5, yc, zc + 0.8)
                fx_sc = 3.8
            elif k == 1:
                shear_deg = 1.0
                sw_dx, sw_ry = -2.2, -5.0
                pole_spin = fi * 70.0
                kyle_pos = (39.0, yc, zc + 1.2)
                kyle_sc = 0.75
                fx_sc = 2.4
            elif k == 2:
                shear_deg = 4.0
                sw_dx, sw_ry = -1.2, -2.5
                kyle_pos = (48.0, yc, zc + 1.5)
                kyle_sc = 0.001
            else:
                tr = (k - 2) / 5.0
                s = smoothstep(tr)
                shear_deg = 4.0 + 9.0 * s
                sw_dx = -1.2 * (1.0 - s)
                sw_ry = -2.5 * (1.0 - s)
                pole_spin = fi * 22.5
                kyle_pos = (23.2, yc, zc - 2.5 * (1.0 - s) + 0.6 * s)
                kyle_sc = 0.25 + 0.67 * s

        # Cant shears 26 deg around X so player sees blades, barber pole & chambered Kyle clearly!
        mv, mn = combine_parts([
            (blade_u, dict(pos=(piv_x, yc, zc), rx=26.0, ry=-shear_deg)),
            (blade_d, dict(pos=(piv_x, yc, zc), rx=26.0, ry=+shear_deg)),
            (barber_pole, dict(pos=(14.5, yc, zc), rx=pole_spin)),
        ])
        mv, mn = apply_sway(mv, mn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        met_fr.append(apply_quake_cant(mv, mn, **cant_kw))

        cv, cn = transform_part(kyle_doll, pos=kyle_pos, ry=8.0 if fi < 28 else 82.0, rz=-24.0 if fi < 28 else 0.0, scale=kyle_sc)
        cv, cn = apply_sway(cv, cn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        cut_fr.append(apply_quake_cant(cv, cn, **cant_kw))

        hv, hn = apply_sway(hand_r.verts + hand_l.verts, hand_r.norms + hand_l.norms, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        hnd_fr.append(apply_quake_cant(hv, hn, **cant_kw))

        fv, fn = transform_part(fx_part, pos=(28.5, yc, zc + 0.4), rx=fi * 45.0, scale=fx_sc)
        fv, fn = apply_sway(fv, fn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        fx_fr.append(apply_quake_cant(fv, fn, **cant_kw))

    return [
        pack_surface("shears_metal", "metals", "kyle_metals", met_st, met_tris, met_fr),
        pack_surface("shears_hands", "hand",   "kyle_hand",   hnd_st, hnd_tris, hnd_fr),
        pack_surface("shears_kyle",  "cutout", "kyle_cutout", kyle_doll.st, kyle_doll.tris, cut_fr),
        pack_surface("shears_fx",    "fx",     "kyle_fx",     fx_part.st, fx_part.tris, fx_fr),
    ], dict(
        id="v_kyle_v4_shears",
        title="Giant Barber-Shears Railgun",
        subtitle="Chrome Tailor's Shears w/ Spinning Barber Pole Core & Chambered Kyle",
        flavor="Spread the massive chrome blades wide on lock-on, rev the red-white-blue barber pole, and SNAP-launch Kyle at Mach 2!",
        muzzle=[31.0, yc, zc + 0.5],
        orbitCenter=[21.5, yc, zc],
        orbitDist=24.0,
    )


# ===========================================================================
# WEAPON 5: v_kyle_v5_invoice.md3 — 'PAPER-PLANE INVOICE CANNON'
# ===========================================================================
def build_paper_plane_invoice():
    """Folded aerodynamic paper airplane made of Invoice #050 ('GIMME MY CUT - 50%') & $100 bills."""
    mp = MeshPart("cutout")
    iu0, iv0, iu1, iv1 = UV_INVOICE
    du0, dv0, du1, dv1 = UV_DOLLAR_BILL

    # Main folded delta wings (center keel at z=-0.6, wingtips flaring up at z=+0.5, nose at +X=5.5, tail at -X=-4.5)
    for sgn in (-1.0, +1.0):
        # Outer wing panel (Invoice sheet)
        p0 = (-4.5, 0.0, 0.15)
        p1 = (+5.5, 0.0, 0.10)
        p2 = (-4.2, sgn * 3.8, 0.72)
        p3 = (-4.5, sgn * 1.4, 0.30)
        mp.add_quad(
            p0, p1, p2, p3,
            (iu0, iv1), (iu1, iv1), (iu1, iv0), (iu0, iv0),
            nrm=vnorm((0.0, -sgn * 0.15, 1.0)), two_sided=True,
        )
        # Underside keel fold ($100 bill lining)
        mp.add_quad(
            (-4.5, 0.0, -1.10), (+5.5, 0.0, 0.05), (-4.4, sgn * 0.75, 0.18), (-4.5, 0.0, 0.15),
            (du0, dv1), (du1, dv1), (du1, dv0), (du0, dv0),
            nrm=(0.0, sgn, 0.0), two_sided=True,
        )
    return mp


def build_v5_invoice():
    """Office clipboard/invoice ('GIMME MY CUT - 50%') folded into a crisp $100-bill
    paper airplane launcher with Kyle riding on top holding scissors!
    """
    yc, zc = -4.2, -7.2
    clip = MeshPart("metals")
    # Mahogany wood clipboard + brass spring clip at rear
    clip.add_chamfer_box(13.0, 24.0, yc - 3.6, yc + 3.6, zc - 0.55, zc - 0.05, ch=0.06, uv_rect=UV_WOOD_CLIP)
    clip.add_chamfer_box(13.6, 15.2, yc - 1.8, yc + 1.8, zc - 0.05, zc + 0.65, ch=0.08, uv_rect=UV_BRASS)

    # Extra spare 'GIMME MY CUT - 50%' invoice sheet lying flat on clipboard
    flat_inv = MeshPart("cutout")
    iu0, iv0, iu1, iv1 = UV_INVOICE
    flat_inv.add_quad(
        (14.5, yc + 3.1, zc + 0.02), (14.5, yc - 3.1, zc + 0.02),
        (23.5, yc - 3.1, zc + 0.02), (23.5, yc + 3.1, zc + 0.02),
        (iu0, iv1), (iu1, iv1), (iu1, iv0), (iu0, iv0), nrm=(0.0, 0.0, 1.0), two_sided=True,
    )

    plane = build_paper_plane_invoice()
    kyle_doll = build_kyle_body_3d(height=5.2, width=2.4, depth_x=0.38)
    bill_tpl = build_dollar_bill_3d(length=2.4, width=1.15, wave=0.20)
    blade_l = build_scissor_half(blade_len=4.6, blade_w=0.80, thick=0.16, tang_len=1.4, ring_r=0.50, mirror_z=1.0, with_pivot=True)
    blade_r = build_scissor_half(blade_len=4.6, blade_w=0.80, thick=0.16, tang_len=1.4, ring_r=0.50, mirror_z=-1.0, with_pivot=False)
    fx_part = build_fx_burst()

    hand_l = build_articulated_ranger_hand(
        palm_center=(14.5, yc + 3.5, zc - 0.8),
        fwd_dir=(0.75, -0.52, 0.40), up_dir=(-0.18, 0.42, 0.88),
        side_sign=+1.0, finger_curls=(0.78, 0.82, 0.85, 0.85), hand_scale=0.80, forearm_len=7.5,
    )
    hand_r0 = build_articulated_ranger_hand(
        palm_center=(0.0, 0.0, 0.0),
        fwd_dir=(0.82, 0.40, 0.40), up_dir=(-0.20, -0.45, 0.87),
        side_sign=-1.0, finger_curls=(0.75, 0.80, 0.84, 0.84), hand_scale=0.82, forearm_len=7.5,
    )

    met_parts = [clip, blade_l, blade_r]
    met_st, met_tris = merge_topology(met_parts)
    cut_parts = [flat_inv, plane, kyle_doll] + [bill_tpl] * 3
    cut_st, cut_tris = merge_topology(cut_parts)
    hnd_st, hnd_tris = merge_topology([hand_r0, hand_l])

    met_fr, cut_fr, hnd_fr, fx_fr = [], [], [], []
    cant_kw = dict(origin=(18.5, yc, zc), shift=(-0.8, -0.6, 1.0), yaw=14.0, pitch=14.0, roll=-5.0, scale=1.20)

    for fi in range(36):
        sw_dx = sw_dz = sw_ry = 0.0
        pl_pos = (21.5, yc, zc + 1.45)
        pl_rx = pl_ry = 0.0
        pl_sc = 1.0
        snip_deg = 12.0
        hr_pos = (16.5, yc - 1.2, zc + 0.5)
        bill_sc = 0.001
        fx_sc = 0.001

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            sw_dz = 0.20 * math.sin(ph * 2.0)
            pl_pos = (21.5, yc, zc + 1.45 + 0.22 * math.sin(ph * 2.0))
            pl_rx = 6.0 * math.sin(ph)
            snip_deg = 12.0 + 4.0 * math.sin(ph * 2.0)
        elif fi < 28:
            k = fi - 16
            t = k / 11.0
            pull_x = -3.2 * smoothstep(t)
            pl_pos = (21.5 + pull_x, yc, zc + 1.6 + 0.25 * math.sin(k * 2.5))
            pl_ry = -10.0 * t
            pl_rx = 4.0 * math.sin(k * 2.3)
            hr_pos = (16.5 + pull_x, yc - 1.2, zc + 0.5)
            snip_deg = 2.0 + 26.0 * (0.5 + 0.5 * math.sin(t * math.pi * 7.0))
        else:
            k = fi - 28  # 0..7
            if k <= 2:
                pl_pos = (24.5 + 10.5 * k, yc + 0.6 * k, zc + 2.0 + 1.6 * k)
                pl_ry = -14.0
                pl_rx = 18.0 * k
                pl_sc = 1.0 if k <= 1 else 0.001
                hr_pos = (21.0 - 1.5 * k, yc - 0.8, zc + 1.2)
                bill_sc = 0.90
                fx_sc = 3.0 if k == 0 else 1.5
            else:
                tr = (k - 2) / 5.0
                s = smoothstep(tr)
                pl_pos = (21.5, yc, zc + 0.1 + 1.35 * s)
                pl_sc = 0.25 + 0.75 * s
                hr_pos = (16.5, yc - 1.2, zc + 0.5)

        kyle_pos = vadd(pl_pos, (0.2, 0.0, 2.75 * pl_sc))
        sc_pos = vadd(kyle_pos, (1.1 * pl_sc, 0.0, 0.5 * pl_sc))

        mv, mn = combine_parts([
            (clip, dict()),
            (blade_l, dict(pos=sc_pos, rx=pl_rx, ry=pl_ry - snip_deg, scale=pl_sc)),
            (blade_r, dict(pos=sc_pos, rx=pl_rx, ry=pl_ry + snip_deg, scale=pl_sc)),
        ])
        mv, mn = apply_sway(mv, mn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        met_fr.append(apply_quake_cant(mv, mn, **cant_kw))

        bill_xforms = [
            (bill_tpl, dict(pos=(22.0 + bi * 2.5, yc + (bi - 1) * 1.8, zc + 1.5 + bi * 0.9), rx=fi * 40.0 + bi * 45.0, ry=20.0, scale=bill_sc))
            for bi in range(3)
        ]
        cv, cn = combine_parts([
            (flat_inv, dict()),
            (plane, dict(pos=pl_pos, rx=pl_rx, ry=pl_ry, scale=pl_sc)),
            (kyle_doll, dict(pos=kyle_pos, rx=pl_rx, ry=pl_ry - 14.0, rz=-20.0, scale=pl_sc)),
        ] + bill_xforms)
        cv, cn = apply_sway(cv, cn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        cut_fr.append(apply_quake_cant(cv, cn, **cant_kw))

        hr_k = build_articulated_ranger_hand(
            palm_center=hr_pos,
            fwd_dir=(0.82, 0.40, 0.40), up_dir=(-0.20, -0.45, 0.87),
            side_sign=-1.0, finger_curls=(0.75, 0.80, 0.84, 0.84), hand_scale=0.82, forearm_len=7.5,
        )
        hv, hn = apply_sway(hr_k.verts + hand_l.verts, hr_k.norms + hand_l.norms, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        hnd_fr.append(apply_quake_cant(hv, hn, **cant_kw))

        fv, fn = transform_part(fx_part, pos=(26.0, yc, zc + 2.0), scale=fx_sc)
        fv, fn = apply_sway(fv, fn, pos=(sw_dx, 0.0, sw_dz), ry=sw_ry)
        fx_fr.append(apply_quake_cant(fv, fn, **cant_kw))

    return [
        pack_surface("invoice_metal",  "metals", "kyle_metals", met_st, met_tris, met_fr),
        pack_surface("invoice_hands",  "hand",   "kyle_hand",   hnd_st, hnd_tris, hnd_fr),
        pack_surface("invoice_kyle",   "cutout", "kyle_cutout", cut_st, cut_tris, cut_fr),
        pack_surface("invoice_fx",     "fx",     "kyle_fx",     fx_part.st, fx_part.tris, fx_fr),
    ], dict(
        id="v_kyle_v5_invoice",
        title="Paper-Plane Invoice Cannon",
        subtitle="Clipboard & 'GIMME MY CUT - 50%' $100-Bill Paper Airplane Launcher",
        flavor="Folded from an overdue Bakersfield barber invoice! Pull back the $100-bill glider while Kyle snips on top, then launch it straight into their face.",
        muzzle=[27.5, yc, zc + 1.8],
        orbitCenter=[20.0, yc, zc + 1.5],
        orbitDist=23.5,
    )
