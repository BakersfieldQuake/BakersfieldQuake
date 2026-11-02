"""3D Procedural Geometry & 37-Frame Quake Animation Builders for the 3 Combined Mega Man Yeet Weapons.

Combines BOTH user-uploaded references in 3 radically distinct, funny, bad-ass Quake weapons:
  - Input 1 (Video): The 'Mega Man' contraption (polished chrome torpedo-nose shaft, TIG T-collar,
                     steel cross-axle, twin 5-ribbed pneumatic wheelbarrow tires on white concave dish rims)
  - Input 2 (Photo): Heavy shop-welded steel rotary launcher rig (circular hot-rolled steel drum pan with
                     3 black-oxide hex leveling bolts, hollow raw square-tube A-frame & 4-arm pinwheel cross,
                     giant zinc hex-nut threaded crossbar, brushed steel ruled scale spine, cylindrical motor
                     with bright white nylon pinion gear meshing into a 6-spoked gray steel bull gear, and
                     long slender diagonal steel trip/pushrod)

All 3 models follow BakersfieldQuake's exact 37-frame megaman.qc schedule:
  - Frames  0..15 (16 frames): Looping Idle (gears humming, wheels revving, subtle Quake sway)
  - Frames 16..35 (20 frames): High-power YEET Launch + Heavy Recoil + Funny Mechanical Reload
  - Frame  36     ( 1 frame ): Empty chamber ('empty1') while recharging
"""
import math
from mmw_geometry import (
    MM_WHEEL_Y,
    MeshPart,
    _build_single_wheel,
    basis_from_axis,
    build_articulated_ranger_hand,
    build_megaman_payload_parts,
    rot_axis,
    rot_x,
    rot_y,
    rot_z,
    smoothstep,
    transform_megaman_frame,
    vadd,
    vcross,
    vdot,
    vlen,
    vlerp,
    vmul,
    vnorm,
    vsub,
)
from mmy_textures import (
    UV_BLACK_BOLT,
    UV_BRASS_PIN,
    UV_BULL_GEAR,
    UV_DRUM_PAN,
    UV_FX_BOLT,
    UV_FX_SHOCK,
    UV_FX_SMOKE,
    UV_FX_SWIRL,
    UV_GRIP_CABLE,
    UV_HEX_ZINC,
    UV_HOLLOW_DARK,
    UV_NYLON_WHITE,
    UV_OSHA_DECAL,
    UV_RED_LEVER,
    UV_RULED_SCALE,
    UV_SQ_TUBE,
    UV_WELD_BEAD,
)


# ===========================================================================
# 1. REUSABLE UPLOAD-2 WELDED RIG 3D COMPONENT BUILDERS
# ===========================================================================
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


def add_hollow_square_tube(
    mp,
    p0,
    p1,
    half_w=0.42,
    wall_t=0.085,
    up_hint=(0.0, 0.0, 1.0),
    open_start=False,
    open_end=True,
    weld_start=True,
    weld_end=False,
    uv_outer=UV_SQ_TUBE,
):
    """Arbitrary-axis raw hot-rolled square steel tube with REAL dark hollow interior ends & MIG weld collars."""
    vec = vsub(p1, p0)
    L = vlen(vec)
    if L < 1e-5:
        return
    X, Y, Z = basis_from_axis(vec, up_hint=up_hint)
    hw = half_w
    iw = max(0.05, half_w - wall_t)

    def pt(x_s, y_s, z_s):
        return vadd(p0, vadd(vmul(X, x_s), vadd(vmul(Y, y_s), vmul(Z, z_s))))

    u0, v0, u1, v1 = uv_outer
    # 4 outer faces with crisp per-face normals
    corners = [(+hw, -hw), (+hw, +hw), (-hw, +hw), (-hw, -hw)]
    face_nrms = [Y, Z, vmul(Y, -1.0), vmul(Z, -1.0)]
    # Wait: check corners[0]->corners[1] = (+hw,-hw)->(+hw,+hw) -> normal is +Y!
    # corners[1]->corners[2] = (+hw,+hw)->(-hw,+hw) -> normal is +Z!
    # corners[2]->corners[3] = (-hw,+hw)->(-hw,-hw) -> normal is -Y!
    # corners[3]->corners[0] = (-hw,-hw)->(+hw,-hw) -> normal is -Z!
    for i in range(4):
        ya, za = corners[i]
        yb, zb = corners[(i + 1) % 4]
        mp.add_quad(
            pt(0.0, ya, za), pt(L, ya, za), pt(L, yb, zb), pt(0.0, yb, zb),
            (u0, v1), (u1, v1), (u1, v0), (u0, v0),
            nrm=face_nrms[i],
        )

    # End treatment (-X at x=0 and +X at x=L)
    du0, dv0, du1, dv1 = UV_HOLLOW_DARK
    ru0, rv0, ru1, rv1 = UV_HEX_ZINC
    throat_d = min(L * 0.42, hw * 1.45)

    for is_end, x_cap, nx_sgn, is_open in ((False, 0.0, -1.0, open_start), (True, L, +1.0, open_end)):
        cap_n = vmul(X, nx_sgn)
        if not is_open:
            mp.add_quad(
                pt(x_cap, -hw, -hw), pt(x_cap, +hw, -hw), pt(x_cap, +hw, +hw), pt(x_cap, -hw, +hw),
                (u0, v0), (u1, v0), (u1, v1), (u0, v1),
                nrm=cap_n,
            )
        else:
            in_corners = [(+iw, -iw), (+iw, +iw), (-iw, +iw), (-iw, -iw)]
            x_in = x_cap - nx_sgn * throat_d
            for i in range(4):
                oya, oza = corners[i]
                oyb, ozb = corners[(i + 1) % 4]
                iya, iza = in_corners[i]
                iyb, izb = in_corners[(i + 1) % 4]
                # Bright cut-steel wall thickness rim
                mp.add_quad(
                    pt(x_cap, oya, oza), pt(x_cap, oyb, ozb), pt(x_cap, iyb, izb), pt(x_cap, iya, iza),
                    (ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1),
                    nrm=cap_n,
                )
                # Dark recessed inner throat wall (inward normal = -face_nrms[i])
                mp.add_quad(
                    pt(x_cap, iya, iza), pt(x_cap, iyb, izb), pt(x_in, iyb, izb), pt(x_in, iya, iza),
                    (du0, dv0), (du1, dv0), (du1, dv1), (du0, dv1),
                    nrm=vmul(face_nrms[i], -1.0),
                )
            # Dark recessed plug floor inside cavity
            mp.add_quad(
                pt(x_in, -iw, -iw), pt(x_in, +iw, -iw), pt(x_in, +iw, +iw), pt(x_in, -iw, +iw),
                (du0, dv0), (du1, dv0), (du1, dv1), (du0, dv1),
                nrm=cap_n,
            )

    # Chunky 3D MIG weld bead collars at welded ends
    wu0, wv0, wu1, wv1 = UV_WELD_BEAD
    for do_w, x_a, x_b in ((weld_start, 0.0, min(L * 0.35, hw * 0.68)), (weld_end, max(L * 0.65, L - hw * 0.68), L)):
        if not do_w:
            continue
        wh = hw * 1.18
        w_c0 = [(+wh, -wh), (+wh, +wh), (-wh, +wh), (-wh, -wh)] if x_a == 0.0 else corners
        w_c1 = corners if x_a == 0.0 else [(+wh, -wh), (+wh, +wh), (-wh, +wh), (-wh, -wh)]
        for i in range(4):
            ya0, za0 = w_c0[i]
            yb0, zb0 = w_c0[(i + 1) % 4]
            ya1, za1 = w_c1[i]
            yb1, zb1 = w_c1[(i + 1) % 4]
            mp.add_quad(
                pt(x_a, ya0, za0), pt(x_b, ya1, za1), pt(x_b, yb1, zb1), pt(x_a, yb0, zb0),
                (wu0, wv0), (wu1, wv0), (wu1, wv1), (wu0, wv1),
                nrm=vnorm(vadd(face_nrms[i], vmul(X, 0.25 if x_a == 0.0 else -0.25))),
            )


def add_steel_drum_pan(
    mp,
    center,
    axis=(0.0, 0.0, 1.0),
    radius=4.65,
    height=1.12,
    bolt_angles=(-52.0, +68.0, +182.0),
    foot_drop=1.35,
    up_hint=(1.0, 0.0, 0.0),
):
    """Heavy circular dark-steel drum base + perimeter weld seam + 3 black-oxide hex leveling bolts & round pads."""
    X_a, Y_a, Z_a = basis_from_axis(axis, up_hint=up_hint)
    h2 = 0.5 * height
    # Main cylindrical drum pan with beveled weld lip
    mp.add_lathe(
        center, axis,
        [
            (-h2, 0.00, 0.02, radius),
            (-h2, radius * 0.94, 0.88, radius),
            (-h2 + 0.08, radius, 0.96, radius),
            (-h2 + 0.08, radius, 0.96, radius),
            (+h2 - 0.10, radius, 0.96, radius),
            (+h2, radius * 0.95, 0.92, radius),
            (+h2, 0.00, 0.02, radius),
        ],
        segs=28, uv_mode="polar", uv_rect=UV_DRUM_PAN, up_hint=up_hint,
    )
    # Circumferential stacked-dime weld ring around upper rim
    mp.add_lathe(
        center, axis,
        [
            (+h2 - 0.16, radius * 0.98, 0.1),
            (+h2 - 0.06, radius * 1.03, 0.5),
            (+h2 + 0.02, radius * 0.94, 0.9),
        ],
        segs=28, uv_rect=UV_WELD_BEAD, up_hint=up_hint,
    )

    # 3 Outrigger Tabs + Black-Oxide Hex-Head Leveling Bolts + Circular Foot Pads
    for ang_deg in bolt_angles:
        ar = math.radians(ang_deg)
        r_dir = vadd(vmul(Y_a, math.cos(ar)), vmul(Z_a, math.sin(ar)))
        # Welded steel lug bracket sticking out from drum rim
        lug_in = vadd(center, vmul(r_dir, radius * 0.88))
        lug_out = vadd(center, vmul(r_dir, radius + 0.68))
        add_hollow_square_tube(
            mp, lug_in, lug_out, half_w=0.30, open_start=False, open_end=False,
            weld_start=True, up_hint=X_a,
        )
        bolt_c = vadd(center, vmul(r_dir, radius + 0.52))
        # Circular steel leveling pad at bottom (-X_a * foot_drop)
        mp.add_lathe(
            bolt_c, axis,
            [
                (-foot_drop - 0.12, 0.00, 0.1, 0.72),
                (-foot_drop - 0.12, 0.68, 0.9, 0.72),
                (-foot_drop, 0.66, 0.95, 0.72),
                (-foot_drop + 0.08, 0.22, 0.3, 0.72),
            ],
            segs=14, uv_mode="polar", uv_rect=UV_DRUM_PAN, up_hint=up_hint,
        )
        # Threaded black-oxide bolt shaft
        mp.add_lathe(
            bolt_c, axis,
            [
                (-foot_drop, 0.20, 0.05),
                (+h2 + 0.58, 0.20, 0.95),
            ],
            segs=10, uv_rect=UV_BLACK_BOLT, up_hint=up_hint,
        )
        # Chunky 6-sided black-oxide hex bolt head on top!
        mp.add_lathe(
            bolt_c, axis,
            [
                (+h2 + 0.55, 0.20, 0.1),
                (+h2 + 0.56, 0.42, 0.2),
                (+h2 + 0.94, 0.42, 0.8),
                (+h2 + 0.95, 0.00, 1.0),
            ],
            segs=6, uv_rect=UV_BLACK_BOLT, up_hint=up_hint,
        )


def add_threaded_hex_crossbar(
    mp,
    center,
    bar_dir=(0.0, 1.0, 0.0),
    half_len=4.15,
    stud_ext=1.18,
    tube_hw=0.38,
    nut_r=0.62,
    up_hint=(0.0, 0.0, 1.0),
):
    """Square-tube crossbeam + welded end-caps + coarse threaded studs + GIANT 6-sided zinc hex nuts on both ends."""
    B = vnorm(bar_dir)
    p_l = vadd(center, vmul(B, +half_len))
    p_r = vadd(center, vmul(B, -half_len))
    add_hollow_square_tube(
        mp, p_r, p_l, half_w=tube_hw, open_start=False, open_end=False,
        weld_start=True, weld_end=True, up_hint=up_hint,
    )
    for sgn, end_p in ((+1.0, p_l), (-1.0, p_r)):
        ax = vmul(B, sgn)
        # Coarse machined threaded stud
        mp.add_lathe(
            end_p, ax,
            [
                (0.00, 0.26, 0.05),
                (stud_ext, 0.26, 0.95),
                (stud_ext + 0.05, 0.20, 0.98),
                (stud_ext + 0.05, 0.00, 1.00),
            ],
            segs=12, uv_rect=UV_HEX_ZINC, up_hint=up_hint,
        )
        # Giant 6-sided Zinc Hex Nut near outer tip (exact match to reference photo!)
        mp.add_lathe(
            end_p, ax,
            [
                (stud_ext * 0.42, 0.26, 0.05),
                (stud_ext * 0.44, nut_r, 0.15),
                (stud_ext * 0.88, nut_r, 0.85),
                (stud_ext * 0.90, 0.26, 0.95),
            ],
            segs=6, uv_rect=UV_HEX_ZINC, up_hint=up_hint,
        )


def add_ruled_scale_spine(
    mp,
    x0,
    x1,
    y_c=0.0,
    z_top=0.68,
    width=1.46,
    thick=0.52,
    stepped_tail=True,
):
    """Heavy flat brushed-steel spine bar with engraved distance ruler ('10m..BAKERSFIELD..FRESNO..ORBIT..BYE!!')."""
    hw = 0.5 * width
    z_bot = z_top - thick
    mp.add_chamfer_box(
        x0, x1, y_c - hw, y_c + hw, z_bot, z_top,
        ch=0.06, uv_rect=UV_SQ_TUBE, side_uv=UV_SQ_TUBE, top_uv=UV_RULED_SCALE,
    )
    if stepped_tail:
        # Welded stepped tail-beam drop matching foreground of reference photo!
        mp.add_chamfer_box(
            x0 - 2.35, x0 + 0.25, y_c - hw * 0.94, y_c + hw * 0.94, z_bot - 0.34, z_top - 0.26,
            ch=0.05, uv_rect=UV_SQ_TUBE, top_uv=UV_SQ_TUBE,
        )
        # Transverse MIG weld bead across step seam at x0
        mp.add_chamfer_box(
            x0 - 0.16, x0 + 0.18, y_c - hw * 0.98, y_c + hw * 0.98, z_top - 0.32, z_top + 0.03,
            ch=0.04, uv_rect=UV_WELD_BEAD, top_uv=UV_WELD_BEAD,
        )


def build_spoked_bull_gear(outer_r=2.92, rim_in_r=2.12, hub_r=0.88, thick=0.28, n_teeth=30, n_spokes=6):
    """True 3D 6-spoked gray steel bull ring gear (in local XY plane, spin axis +Z) with 30 3D teeth & 6 hub bolts!"""
    gp = MeshPart("rig_steel")
    hz = 0.5 * thick
    root_r = outer_r - 0.20
    u0, v0, u1, v1 = UV_BULL_GEAR
    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
    ru, rv = 0.48 * (u1 - u0), 0.48 * (v1 - v0)

    def uv_xy(x, y):
        return (uc + ru * (x / outer_r), vc + rv * (y / outer_r))

    # 1. Central hub boss + 6 zinc hex flange bolts
    gp.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
        [
            (-hz * 1.35, 0.00, 0.0, hub_r),
            (-hz * 1.35, hub_r, 0.9, hub_r),
            (+hz * 1.55, hub_r, 0.9, hub_r),
            (+hz * 1.55, 0.00, 0.0, hub_r),
        ],
        segs=18, uv_mode="polar", uv_rect=UV_BULL_GEAR, up_hint=(1.0, 0.0, 0.0),
    )
    for k in range(6):
        ba = math.radians(k * 60.0 + 30.0)
        bx, by = 0.62 * hub_r * math.cos(ba), 0.62 * hub_r * math.sin(ba)
        gp.add_lathe(
            (bx, by, +hz * 1.55), (0.0, 0.0, 1.0),
            [(0.0, 0.14, 0.2), (0.18, 0.14, 0.8), (0.19, 0.00, 1.0)],
            segs=6, uv_rect=UV_HEX_ZINC, up_hint=(1.0, 0.0, 0.0),
        )

    # 2. Outer annular steel ring (rim_in_r .. root_r) with top, bottom, and inner cylindrical wall
    segs_ring = n_teeth * 2
    for i in range(segs_ring):
        a0 = 2.0 * math.pi * (i / float(segs_ring))
        a1 = 2.0 * math.pi * ((i + 1) / float(segs_ring))
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        pi0 = (rim_in_r * c0, rim_in_r * s0)
        pi1 = (rim_in_r * c1, rim_in_r * s1)
        po0 = (root_r * c0, root_r * s0)
        po1 = (root_r * c1, root_r * s1)
        # Top (+Z) & Bottom (-Z) annular ring quads
        gp.add_quad(
            (pi0[0], pi0[1], +hz), (po0[0], po0[1], +hz), (po1[0], po1[1], +hz), (pi1[0], pi1[1], +hz),
            uv_xy(*pi0), uv_xy(*po0), uv_xy(*po1), uv_xy(*pi1), nrm=(0.0, 0.0, 1.0),
        )
        gp.add_quad(
            (pi0[0], pi0[1], -hz), (pi1[0], pi1[1], -hz), (po1[0], po1[1], -hz), (po0[0], po0[1], -hz),
            uv_xy(*pi0), uv_xy(*pi1), uv_xy(*po1), uv_xy(*po0), nrm=(0.0, 0.0, -1.0),
        )
        # Inner cutout cylindrical wall (facing inward toward hub!)
        in_n = (-0.5 * (c0 + c1), -0.5 * (s0 + s1), 0.0)
        gp.add_quad(
            (pi0[0], pi0[1], -hz), (pi0[0], pi0[1], +hz), (pi1[0], pi1[1], +hz), (pi1[0], pi1[1], -hz),
            (u0, v0), (u0, v1), (u1, v1), (u1, v0), nrm=vnorm(in_n),
        )

    # 3. 30 Sculpted 3D Involute-Trapezoid Gear Teeth around root_r -> outer_r!
    da = 2.0 * math.pi / float(n_teeth)
    for t in range(n_teeth):
        ac = t * da
        # Tooth spans [-0.34*da .. +0.34*da] at root, [-0.18*da .. +0.18*da] at tip; valley gap to next tooth
        a_r0 = ac - 0.34 * da
        a_t0 = ac - 0.18 * da
        a_t1 = ac + 0.18 * da
        a_r1 = ac + 0.34 * da
        a_next = (t + 1) * da - 0.34 * da

        pr0 = (root_r * math.cos(a_r0), root_r * math.sin(a_r0))
        pt0 = (outer_r * math.cos(a_t0), outer_r * math.sin(a_t0))
        pt1 = (outer_r * math.cos(a_t1), outer_r * math.sin(a_t1))
        pr1 = (root_r * math.cos(a_r1), root_r * math.sin(a_r1))
        pnx = (root_r * math.cos(a_next), root_r * math.sin(a_next))

        # Top & bottom tooth faces
        gp.add_quad(
            (pr0[0], pr0[1], +hz), (pt0[0], pt0[1], +hz), (pt1[0], pt1[1], +hz), (pr1[0], pr1[1], +hz),
            uv_xy(*pr0), uv_xy(*pt0), uv_xy(*pt1), uv_xy(*pr1), nrm=(0.0, 0.0, 1.0),
        )
        gp.add_quad(
            (pr0[0], pr0[1], -hz), (pr1[0], pr1[1], -hz), (pt1[0], pt1[1], -hz), (pt0[0], pt0[1], -hz),
            uv_xy(*pr0), uv_xy(*pr1), uv_xy(*pt1), uv_xy(*pt0), nrm=(0.0, 0.0, -1.0),
        )
        # 4 outer perimeter segments (flank0, tip, flank1, valley)
        for q0, q1 in ((pr0, pt0), (pt0, pt1), (pt1, pr1), (pr1, pnx)):
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            out_n = vnorm((dy, -dx, 0.0))
            gp.add_quad(
                (q0[0], q0[1], -hz), (q1[0], q1[1], -hz), (q1[0], q1[1], +hz), (q0[0], q0[1], +hz),
                (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=out_n,
            )

    # 4. 6 Open-Window Flat Steel Radial Spokes!
    sp_hw = 0.24
    for s in range(n_spokes):
        sa = math.radians(s * (360.0 / n_spokes))
        X_s = (math.cos(sa), math.sin(sa), 0.0)
        Y_s = (-math.sin(sa), math.cos(sa), 0.0)
        r_a, r_b = hub_r * 0.85, rim_in_r * 1.04

        def sp_pt(rr, yy, zz):
            return (X_s[0] * rr + Y_s[0] * yy, X_s[1] * rr + Y_s[1] * yy, zz)

        shz = hz * 0.86
        gp.add_quad(
            sp_pt(r_a, -sp_hw, +shz), sp_pt(r_b, -sp_hw, +shz), sp_pt(r_b, +sp_hw, +shz), sp_pt(r_a, +sp_hw, +shz),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=(0.0, 0.0, 1.0),
        )
        gp.add_quad(
            sp_pt(r_a, -sp_hw, -shz), sp_pt(r_a, +sp_hw, -shz), sp_pt(r_b, +sp_hw, -shz), sp_pt(r_b, -sp_hw, -shz),
            (u0, v0), (u0, v1), (u1, v1), (u1, v0), nrm=(0.0, 0.0, -1.0),
        )
        gp.add_quad(
            sp_pt(r_a, +sp_hw, -shz), sp_pt(r_a, +sp_hw, +shz), sp_pt(r_b, +sp_hw, +shz), sp_pt(r_b, +sp_hw, -shz),
            (u0, v0), (u0, v1), (u1, v1), (u1, v0), nrm=Y_s,
        )
        gp.add_quad(
            sp_pt(r_a, -sp_hw, -shz), sp_pt(r_b, -sp_hw, -shz), sp_pt(r_b, -sp_hw, +shz), sp_pt(r_a, -sp_hw, +shz),
            (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=vmul(Y_s, -1.0),
        )
    return gp


def build_nylon_pinion_gear(outer_r=0.82, thick=0.46, n_teeth=12):
    """Bright-white Delrin/Nylon 12-tooth spur pinion gear + zinc hex cap bolt (local XY plane, spin axis +Z)."""
    np_p = MeshPart("rig_steel")
    hz = 0.5 * thick
    root_r = outer_r - 0.16
    u0, v0, u1, v1 = UV_NYLON_WHITE
    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)

    # Solid white nylon core cylinder up to root_r
    np_p.add_lathe(
        (0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
        [(-hz, 0.0, 0.0, root_r), (-hz, root_r, 0.9, root_r), (+hz, root_r, 0.9, root_r), (+hz, 0.0, 0.0, root_r)],
        segs=n_teeth * 2, uv_mode="polar", uv_rect=UV_NYLON_WHITE, up_hint=(1.0, 0.0, 0.0),
    )
    # 12 crisp 3D white nylon spur teeth!
    da = 2.0 * math.pi / float(n_teeth)
    for t in range(n_teeth):
        ac = t * da
        pr0 = (root_r * math.cos(ac - 0.34 * da), root_r * math.sin(ac - 0.34 * da))
        pt0 = (outer_r * math.cos(ac - 0.19 * da), outer_r * math.sin(ac - 0.19 * da))
        pt1 = (outer_r * math.cos(ac + 0.19 * da), outer_r * math.sin(ac + 0.19 * da))
        pr1 = (root_r * math.cos(ac + 0.34 * da), root_r * math.sin(ac + 0.34 * da))
        np_p.add_quad(
            (pr0[0], pr0[1], +hz), (pt0[0], pt0[1], +hz), (pt1[0], pt1[1], +hz), (pr1[0], pr1[1], +hz),
            (uc, vc), (u1, vc), (u1, v1), (uc, v1), nrm=(0.0, 0.0, 1.0),
        )
        np_p.add_quad(
            (pr0[0], pr0[1], -hz), (pr1[0], pr1[1], -hz), (pt1[0], pt1[1], -hz), (pt0[0], pt0[1], -hz),
            (uc, vc), (uc, v1), (u1, v1), (u1, vc), nrm=(0.0, 0.0, -1.0),
        )
        for q0, q1 in ((pr0, pt0), (pt0, pt1), (pt1, pr1)):
            out_n = vnorm((q1[1] - q0[1], -(q1[0] - q0[0]), 0.0))
            np_p.add_quad(
                (q0[0], q0[1], -hz), (q1[0], q1[1], -hz), (q1[0], q1[1], +hz), (q0[0], q0[1], +hz),
                (u0, v0), (u1, v0), (u1, v1), (u0, v1), nrm=out_n,
            )

    # Central zinc washer + 6-sided hex cap bolt on top (+Z) matching reference photo!
    np_p.add_lathe(
        (0.0, 0.0, +hz), (0.0, 0.0, 1.0),
        [(0.0, 0.38, 0.1), (0.06, 0.38, 0.3), (0.07, 0.24, 0.4), (0.28, 0.24, 0.85), (0.29, 0.00, 1.0)],
        segs=6, uv_rect=UV_HEX_ZINC, up_hint=(1.0, 0.0, 0.0),
    )
    return np_p


def add_motor_canister(mp, base_pos, axis=(0.0, 0.0, 1.0), radius=0.96, length=1.75, up_hint=(1.0, 0.0, 0.0)):
    """Brushed aluminum cylindrical gearbox/motor housing supporting the white nylon pinion gear."""
    mp.add_lathe(
        base_pos, axis,
        [
            (0.00, 0.00, 0.02, radius),
            (0.00, radius * 1.05, 0.12, radius),
            (0.22, radius * 1.05, 0.18, radius),
            (0.24, radius, 0.22, radius),
            (length - 0.14, radius, 0.88, radius),
            (length, radius * 0.86, 0.96, radius),
            (length, 0.00, 1.00, radius),
        ],
        segs=18, uv_mode="polar", uv_rect=UV_BULL_GEAR, up_hint=up_hint,
    )


def build_4arm_pinwheel_rotor(mast_h=2.55, arm_len=4.95, mast_hw=0.40, arm_hw=0.28, with_plunger=True):
    """Upload 2's hollow vertical square-tube mast + 4 welded square-tube rotor arms + notched end tabs + release pin."""
    rp = MeshPart("rig_steel")
    # Vertical hollow square-tube mast (open hollow top at z = +mast_h!)
    add_hollow_square_tube(
        rp, (0.0, 0.0, 0.0), (0.0, 0.0, mast_h),
        half_w=mast_hw, open_start=False, open_end=True, weld_start=True, up_hint=(1.0, 0.0, 0.0),
    )
    arm_z = mast_h - 0.56
    for k in range(4):
        ang = math.radians(k * 90.0)
        ca, sa = math.cos(ang), math.sin(ang)
        p_in = (ca * (mast_hw * 0.85), sa * (mast_hw * 0.85), arm_z)
        p_out = (ca * (arm_len - 0.65), sa * (arm_len - 0.65), arm_z)
        add_hollow_square_tube(
            rp, p_in, p_out, half_w=arm_hw, open_start=False, open_end=False,
            weld_start=True, up_hint=(0.0, 0.0, 1.0),
        )
        # Stepped flat steel end-tab with dark pin-hole swatch (matches reference photo's notched arm tips!)
        p_tip = (ca * (arm_len + 0.25), sa * (arm_len + 0.25), arm_z - 0.08)
        add_hollow_square_tube(
            rp,
            (ca * (arm_len - 0.72), sa * (arm_len - 0.72), arm_z - 0.08),
            p_tip,
            half_w=arm_hw * 0.72, open_start=False, open_end=True, weld_start=True, up_hint=(0.0, 0.0, 1.0),
        )
        if with_plunger and k == 0:
            # Vertical stainless spring-loaded release plunger pin on Arm 0 (+X)!
            pin_x = arm_len - 0.18
            rp.add_lathe(
                (pin_x, 0.0, arm_z - 0.95), (0.0, 0.0, 1.0),
                [
                    (0.00, 0.00, 0.0),
                    (0.00, 0.11, 0.1),
                    (0.75, 0.11, 0.5),
                    (0.77, 0.24, 0.6),
                    (1.38, 0.24, 0.85),
                    (1.40, 0.32, 0.92),
                    (1.58, 0.32, 0.98),
                    (1.58, 0.00, 1.0),
                ],
                segs=10, uv_rect=UV_BRASS_PIN, up_hint=(1.0, 0.0, 0.0),
            )
    return rp


def add_pistol_grip_and_trigger(mp, gx=2.45, gy=-0.65, gz=-1.55):
    """Ergonomic shop-welded knurled pistol grip + red plastidip trigger guard assembly."""
    grip_pts = [
        (gx + 0.45, gy, gz + 0.35),
        (gx + 0.10, gy - 0.05, gz - 0.85),
        (gx - 0.38, gy - 0.10, gz - 2.15),
        (gx - 0.68, gy - 0.12, gz - 3.15),
    ]
    mp.add_tube(grip_pts, [(0.56, 0.78), (0.52, 0.74), (0.50, 0.72), (0.58, 0.80)], segs=12, uv_rect=UV_GRIP_CABLE)
    # Trigger guard loop
    tg_pts = [
        (gx + 0.25, gy, gz - 1.35),
        (gx + 1.35, gy, gz - 1.50),
        (gx + 1.85, gy, gz - 0.65),
        (gx + 1.65, gy, gz + 0.15),
    ]
    mp.add_tube(tg_pts, [0.11] * 4, segs=8, uv_rect=UV_SQ_TUBE)


def build_fx_template():
    """Fixed-topology additive FX mesh (Mach shock cone + centrifugal/burnout swirl + twin plasma arcs + smoke)."""
    fx = MeshPart("fx")
    # 1. Muzzle Mach shockwave billboard disc (8 verts / 4 quads -> simple crossed/layered shock discs)
    su0, sv0, su1, sv1 = UV_FX_SHOCK
    fx.add_quad(
        (0.0, -1.0, -1.0), (0.0, +1.0, -1.0), (0.0, +1.0, +1.0), (0.0, -1.0, +1.0),
        (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    fx.add_quad(
        (0.8, -0.7, -0.7), (0.8, +0.7, -0.7), (0.8, +0.7, +0.7), (0.8, -0.7, +0.7),
        (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    # 2. Horizontal/angled spark swirl disc
    wu0, wv0, wu1, wv1 = UV_FX_SWIRL
    fx.add_quad(
        (-1.0, -1.0, 0.0), (+1.0, -1.0, 0.0), (+1.0, +1.0, 0.0), (-1.0, +1.0, 0.0),
        (wu0, wv1), (wu1, wv1), (wu1, wv0), (wu0, wv0), nrm=(0.0, 0.0, 1.0), two_sided=True,
    )
    # 3. Twin electric rail/launch lightning ribbons
    bu0, bv0, bu1, bv1 = UV_FX_BOLT
    for sgn in (-1.0, +1.0):
        fx.add_quad(
            (-1.2, sgn * 0.45, -0.22), (+1.4, sgn * 0.45, -0.22), (+1.4, sgn * 0.45, +0.22), (-1.2, sgn * 0.45, +0.22),
            (bu0, bv1), (bu1, bv1), (bu1, bv0), (bu0, bv0), nrm=(0.0, sgn, 0.0), two_sided=True,
        )
    # 4. Burnout smoke / steam billboard
    mu0, mv0, mu1, mv1 = UV_FX_SMOKE
    fx.add_quad(
        (-0.4, -0.9, -0.6), (-0.4, +0.9, -0.6), (-0.4, +0.9, +0.9), (-0.4, -0.9, +0.9),
        (mu0, mv1), (mu1, mv1), (mu1, mv0), (mu0, mv0), nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    return fx


# ===========================================================================
# 2. SHARED 37-FRAME QUAKE SCHEDULE GENERATOR & EYE TRANSFORM
# ===========================================================================
FRAME_NAMES_37 = (
    [f"idle{i + 1}" for i in range(16)]
    + [f"fire{i + 1}" for i in range(20)]
    + ["empty1"]
)


def make_eye_xform(base, scale, yaw, pitch, roll):
    def to_eye_pt(p, dx=0.0, dy=0.0, dz=0.0, kp=0.0, kr=0.0, ky=0.0):
        q = (p[0] + dx, p[1] + dy, p[2] + dz)
        q = rot_x(q, roll + kr)
        q = rot_y(q, pitch + kp)
        q = vmul(q, scale)
        q = rot_z(q, yaw + ky)
        return vadd(q, base)

    def to_eye_nrm(n, kp=0.0, kr=0.0, ky=0.0):
        qn = rot_x(n, roll + kr)
        qn = rot_y(qn, pitch + kp)
        qn = rot_z(qn, yaw + ky)
        return vnorm(qn)

    return to_eye_pt, to_eye_nrm


def apply_eye_list(vv, nn, to_pt, to_nrm, dx=0.0, dy=0.0, dz=0.0, kp=0.0, kr=0.0, ky=0.0):
    return (
        [to_pt(p, dx, dy, dz, kp, kr, ky) for p in vv],
        [to_nrm(n, kp, kr, ky) for n in nn],
    )


def pack_surface(name, mat, shader, st, tris, frames):
    return dict(name=name, mat=mat, shader=shader, st=list(st), tris=list(tris), frames=frames)


def add_osha_placard(mp, x0, x1, y0, y1, z0, z1):
    """Welded steel placard box with properly oriented (left-to-right legible) OSHA decal on both +Y and -Y faces."""
    mp.add_chamfer_box(x0, x1, y0, y1, z0, z1, ch=0.03, uv_rect=UV_SQ_TUBE)
    u0, v0, u1, v1 = UV_OSHA_DECAL
    # +Y face (viewed from +Y looking -Y: +X is to the LEFT, so x1 maps to u0 and x0 maps to u1!)
    mp.add_quad(
        (x1, y1 + 0.008, z0 + 0.03), (x0, y1 + 0.008, z0 + 0.03),
        (x0, y1 + 0.008, z1 - 0.03), (x1, y1 + 0.008, z1 - 0.03),
        (u0, v1), (u1, v1), (u1, v0), (u0, v0), nrm=(0.0, 1.0, 0.0),
    )
    # -Y face (viewed from -Y looking +Y: +X is to the RIGHT, so x0 maps to u0 and x1 maps to u1!)
    mp.add_quad(
        (x0, y0 - 0.008, z0 + 0.03), (x1, y0 - 0.008, z0 + 0.03),
        (x1, y0 - 0.008, z1 - 0.03), (x0, y0 - 0.008, z1 - 0.03),
        (u0, v1), (u1, v1), (u1, v0), (u0, v0), nrm=(0.0, -1.0, 0.0),
    )


# ===========================================================================
# 3. VERSION 1: 'THE WHIRLY-YEET 9000' (4-Arm Rotary Centrifuge Sling Turret)
# ===========================================================================
def build_v1_whirly_yeet():
    """Builds 37-frame MD3 surfaces for Version 1: Overclocked 4-Arm Rotary Centrifuge Cannon."""
    to_pt, to_nrm = make_eye_xform(
        base=(5.45, -4.65, -4.85), scale=0.84, yaw=13.5, pitch=5.2, roll=-5.0,
    )

    # --- Static Rig Body (Drum Pan + 3 Leveling Bolts + Hollow A-Frame + Hex Crossbar + Ruled Spine + Motor) ---
    body = MeshPart("rig_steel")
    # Heavy circular steel drum pan w/ 3 black-oxide hex leveling bolts
    add_steel_drum_pan(
        body, center=(9.6, 0.0, -2.05), axis=(0.0, 0.0, 1.0),
        radius=4.65, height=1.10, bolt_angles=(-52.0, +62.0, +182.0), foot_drop=1.32,
    )
    # Hollow square-tube A-frame legs rising from drum pan (open hollow tops just like reference photo!)
    for sgn in (-1.0, +1.0):
        add_hollow_square_tube(
            body, (7.1, sgn * 3.15, -1.65), (8.05, sgn * 1.65, +0.28),
            half_w=0.36, open_start=False, open_end=True, weld_start=True,
        )
    # Horizontal square-tube crossbeam + GIANT zinc hex nuts on both ends!
    add_threaded_hex_crossbar(
        body, center=(8.05, 0.0, -0.35), bar_dir=(0.0, 1.0, 0.0),
        half_len=4.15, stud_ext=1.20, tube_hw=0.36, nut_r=0.62,
    )
    # Brushed-steel Ruled Scale Spine Bar ('10m..80m..BAKERSFIELD..FRESNO..ORBIT..BYE!!')
    add_ruled_scale_spine(body, x0=3.1, x1=21.6, y_c=0.0, z_top=+0.68, width=1.48, thick=0.52, stepped_tail=True)

    # Flared OSHA 'DANGER: MEGA-YEET' safety-yellow launch chute cheeks at muzzle (x = 15.8 .. 21.8)
    for sgn in (-1.0, +1.0):
        add_osha_placard(body, 15.6, 21.8, sgn * 1.18 - 0.16, sgn * 1.18 + 0.16, +0.35, +1.42)

    # Cylindrical drive motor canister at x=9.15 supporting the White Nylon Pinion Gear!
    add_motor_canister(body, base_pos=(9.18, 0.0, +0.66), axis=(0.0, 0.0, 1.0), radius=0.92, length=1.52)
    # Bull-gear support pedestal at x=12.75
    add_hollow_square_tube(
        body, (12.75, 0.0, +0.66), (12.75, 0.0, +2.25),
        half_w=0.52, open_start=False, open_end=False, weld_start=True,
    )
    # Pistol grip + Left angled foregrip welded off left crossbar!
    add_pistol_grip_and_trigger(body, gx=2.45, gy=-0.55, gz=-1.15)
    body.add_tube(
        [(8.05, +3.35, -0.45), (8.25, +3.65, -2.25), (8.35, +3.55, -3.15)],
        [0.44, 0.48, 0.52], segs=10, uv_rect=UV_RED_LEVER,
    )

    # --- Dynamic Moving Rig Parts (6-Spoked Bull Gear + White Nylon Pinion + 4-Arm Pinwheel + Diagonal Trip-Rod) ---
    bull_gear = build_spoked_bull_gear(outer_r=2.86, rim_in_r=2.08, hub_r=0.86, thick=0.28, n_teeth=30, n_spokes=6)
    nylon_pinion = build_nylon_pinion_gear(outer_r=0.82, thick=0.46, n_teeth=12)
    rotor_4arm = build_4arm_pinwheel_rotor(mast_h=2.42, arm_len=4.85, mast_hw=0.38, arm_hw=0.27, with_plunger=True)
    trip_rod = MeshPart("rig_steel")
    trip_rod.add_tube([(0.0, 0.0, 0.0), (-7.8, -3.6, -2.35)], [0.11, 0.11], segs=8, uv_rect=UV_HEX_ZINC)
    trip_rod.add_lathe(
        (-7.8, -3.6, -2.35), vnorm((-7.8, -3.6, -2.35)),
        [(0.0, 0.24, 0.2), (0.55, 0.24, 0.8), (0.56, 0.0, 1.0)],
        segs=6, uv_rect=UV_RED_LEVER,
    )

    mm_parts = build_megaman_payload_parts()
    fx_tpl = build_fx_template()

    lhand_local = build_articulated_ranger_hand(
        palm_center=(8.25, +3.25, -2.35),
        fwd_dir=(+0.25, +0.42, +0.87),
        up_dir=(-0.22, +0.88, -0.42),
        side_sign=+1.0,
        finger_curls=(0.82, 0.86, 0.88, 0.88),
        hand_scale=0.82,
        forearm_len=8.8,
    )

    body_frames, mech_frames, mm_bar_frames, mm_whl_frames, hand_frames, fx_frames = [], [], [], [], [], []
    mm_wh_tris = list(mm_parts["wheel_l"].tris) + [
        (a + len(mm_parts["wheel_l"].verts), b + len(mm_parts["wheel_l"].verts), c + len(mm_parts["wheel_l"].verts))
        for (a, b, c) in mm_parts["wheel_r"].tris
    ]
    mm_wh_st = list(mm_parts["wheel_l"].st) + list(mm_parts["wheel_r"].st)

    mm_bar_nv0 = len(mm_parts["bar_axle"].verts)
    mm_bar_nv1 = mm_bar_nv0 + len(mm_parts["wheel_hw_l"].verts)
    mm_bar_st = list(mm_parts["bar_axle"].st) + list(mm_parts["wheel_hw_l"].st) + list(mm_parts["wheel_hw_r"].st)
    mm_bar_tris = (
        list(mm_parts["bar_axle"].tris)
        + [(a + mm_bar_nv0, b + mm_bar_nv0, c + mm_bar_nv0) for (a, b, c) in mm_parts["wheel_hw_l"].tris]
        + [(a + mm_bar_nv1, b + mm_bar_nv1, c + mm_bar_nv1) for (a, b, c) in mm_parts["wheel_hw_r"].tris]
    )

    # Combined mech topology (bull_gear + nylon_pinion + rotor_4arm + trip_rod)
    mech_parts = [bull_gear, nylon_pinion, rotor_4arm, trip_rod]
    mech_st, mech_tris = [], []
    ofs = 0
    for mp_i in mech_parts:
        mech_st.extend(mp_i.st)
        mech_tris.extend([(a + ofs, b + ofs, c + ofs) for (a, b, c) in mp_i.tris])
        ofs += len(mp_i.verts)

    for fi in range(37):
        dx = dy = dz = kp = kr = ky = 0.0
        rotor_deg = 0.0
        mm_show = True
        mm_pos = (17.25, 0.0, 2.02)
        mm_yaw = 0.0
        mm_pitch = 0.0
        mm_sc = 0.92
        mm_spin = 0.0
        rod_pull = 0.0
        trig = 0.0
        fx_sc = 0.0005
        fx_pos = (10.0, 0.0, -1.5)
        fx_rot = 0.0

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            dx = 0.14 * math.sin(ph)
            dz = 0.18 * math.sin(ph * 2.0 + 0.4)
            kp = 0.55 * math.sin(ph + 0.3)
            kr = 0.70 * math.cos(ph)
            # Idle: gentle oscillatory motor hum & continuous Mega Man tire revving!
            rotor_deg = 4.5 * math.sin(ph * 2.0)
            ar = math.radians(rotor_deg)
            mm_pos = (12.75 + 4.55 * math.cos(ar), 4.55 * math.sin(ar), 2.02 + 0.04 * math.sin(ph * 4.0))
            mm_yaw = rotor_deg
            mm_spin = fi * 22.5
        elif fi == 36:
            # Empty frame while recharging
            mm_show = False
            mm_sc = 0.001
            mm_pos = (9.6, 0.0, -2.0)
            rotor_deg = 45.0
        else:
            k = fi - 16  # 0..19
            if k == 0:    # Trigger yank, wind-up begins!
                trig, rod_pull = 0.7, 0.65
                rotor_deg = -38.0
                dx, dz, kp, kr = -0.35, +0.12, +1.8, -2.2
                mm_spin = 65.0
            elif k == 1:  # Full centrifugal tornado whip around back/left!
                trig, rod_pull = 1.0, 1.0
                rotor_deg = +145.0
                dx, dy, dz, kp, kr, ky = -0.75, +0.45, +0.25, +3.6, +4.5, -2.5
                mm_spin = 190.0
                fx_sc, fx_pos, fx_rot = 3.2, (12.75, 0.0, 3.6), 80.0
            elif k == 2:  # Whipping past 285 deg at blistering RPM!
                trig, rod_pull = 1.0, 1.0
                rotor_deg = +295.0
                dx, dy, dz, kp, kr, ky = -1.45, -0.55, +0.45, +6.2, -5.8, +2.8
                mm_spin = 340.0
                fx_sc, fx_pos, fx_rot = 4.8, (15.5, 0.0, 2.8), 195.0
            elif k == 3:  # FRAME 19: RELEASE PIN POPS! CENTRIFUGAL MACH YEET DOWN THE RULED RAIL!
                trig, rod_pull = 1.0, 0.9
                rotor_deg = +372.0
                dx, dy, dz, kp, kr, ky = -2.55, -0.35, +0.72, +9.4, -7.2, +3.2
                mm_pos = (27.8, 0.0, 2.35)
                mm_yaw, mm_pitch, mm_spin = 0.0, -2.5, 520.0
                fx_sc, fx_pos, fx_rot = 5.6, (22.2, 0.0, 2.1), 310.0
            elif k == 4:  # Frame 20: Clean handoff shrink + peak recoil & shockwave
                trig, rod_pull = 0.7, 0.5
                rotor_deg = +455.0
                dx, dz, kp, kr, ky = -2.15, +0.58, +7.8, -5.0, +2.0
                mm_pos, mm_sc = (38.0, 0.0, 2.8), 0.001
                fx_sc, fx_pos, fx_rot = 3.8, (23.0, 0.0, 2.2), 45.0
            elif k <= 8:  # Frames 21..24: Rotor free-spins to next 90-deg detent (540 -> 720)
                t_c = (k - 4) / 4.0
                rotor_deg = 455.0 + 265.0 * smoothstep(t_c)
                dx = -1.6 * (1.0 - t_c)
                dz = +0.35 * (1.0 - t_c)
                kp = +5.2 * (1.0 - t_c)
                kr = -3.2 * (1.0 - t_c)
                mm_show, mm_sc, mm_pos = False, 0.001, (9.6, 0.0, -2.0)
                if k == 5:
                    fx_sc, fx_pos = 1.8, (22.0, 0.0, 2.1)
            else:         # Frames 25..35 (k=9..19): Fresh Mega Man pops up from drum pan & latches onto next arm!
                t_r = (k - 9) / 10.0
                s_r = smoothstep(min(1.0, t_r * 1.25))
                overshoot = math.sin(t_r * math.pi) * 0.22 * (1.0 - t_r)
                rotor_deg = 720.0 + 8.0 * math.sin(t_r * math.pi * 2.0) * (1.0 - t_r)
                mm_sc = 0.92 * smoothstep(min(1.0, t_r * 2.2))
                mm_pos = (
                    11.5 + 5.75 * s_r,
                    0.0,
                    -1.45 + (3.47 + overshoot) * s_r,
                )
                mm_pitch = 14.0 * (1.0 - s_r)
                mm_spin = t_r * 180.0
                dx = -0.18 * math.sin(t_r * math.pi)
                dz = -0.22 * math.sin(t_r * math.pi)
                kp = -1.2 * math.sin(t_r * math.pi)

            if k <= 2:
                ar = math.radians(rotor_deg)
                mm_pos = (12.75 + 4.65 * math.cos(ar), 4.65 * math.sin(ar), 2.08)
                mm_yaw = rotor_deg + 18.0

        # 1) Static rig body in eye space
        body_frames.append(apply_eye_list(body.verts, body.norms, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 2) Dynamic gears + 4-arm pinwheel + trip-rod (pinion spins -2.5x opposite to bull gear!)
        bv_g, bn_g = transform_part(bull_gear, pos=(12.75, 0.0, +2.38), rz=rotor_deg)
        pv_g, pn_g = transform_part(nylon_pinion, pos=(9.18, 0.0, +2.38), rz=-rotor_deg * 2.5 + 15.0)
        rv_g, rn_g = transform_part(rotor_4arm, pos=(12.75, 0.0, +2.48), rz=rotor_deg)
        tv_g, tn_g = transform_part(trip_rod, pos=(12.35 - 0.65 * rod_pull, -0.35, +1.58))
        mech_frames.append(apply_eye_list(
            bv_g + pv_g + rv_g + tv_g,
            bn_g + pn_g + rn_g + tn_g,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 3) Hero Mega Man Payload
        mm_xf = transform_megaman_frame(
            mm_parts, spin_deg=mm_spin, bar_pitch_deg=mm_pitch,
            pos=mm_pos, yaw_deg=mm_yaw, scale=mm_sc if mm_show else 0.001,
        )
        bar_v = mm_xf["bar_axle"][0] + mm_xf["wheel_hw_l"][0] + mm_xf["wheel_hw_r"][0]
        bar_n = mm_xf["bar_axle"][1] + mm_xf["wheel_hw_l"][1] + mm_xf["wheel_hw_r"][1]
        whl_v = mm_xf["wheel_l"][0] + mm_xf["wheel_r"][0]
        whl_n = mm_xf["wheel_l"][1] + mm_xf["wheel_r"][1]
        mm_bar_frames.append(apply_eye_list(bar_v, bar_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))
        mm_whl_frames.append(apply_eye_list(whl_v, whl_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 4) Ranger Hands
        rh = build_articulated_ranger_hand(
            palm_center=(2.35, -0.78, -2.55),
            fwd_dir=(+0.78, +0.44, +0.44),
            up_dir=(-0.22, -0.52, +0.82),
            side_sign=-1.0,
            finger_curls=(0.45 + 0.42 * trig, 0.86, 0.88, 0.90),
            hand_scale=0.82,
            forearm_len=8.6,
        )
        hand_frames.append(apply_eye_list(
            rh.verts + lhand_local.verts,
            rh.norms + lhand_local.norms,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 5) Additive Muzzle / Swirl FX
        fv, fn = transform_part(fx_tpl, pos=fx_pos, rx=fx_rot, rz=fx_rot * 0.5, scale=fx_sc)
        fx_frames.append(apply_eye_list(fv, fn, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

    rh0 = build_articulated_ranger_hand((0, 0, 0), (1, 0, 0), (0, 0, 1), hand_scale=0.82, forearm_len=8.6)
    hand_st = list(rh0.st) + list(lhand_local.st)
    n_rh = len(rh0.verts)
    hand_tris = list(rh0.tris) + [(a + n_rh, b + n_rh, c + n_rh) for (a, b, c) in lhand_local.tris]

    muzzle_eye = [round(c, 2) for c in to_pt((22.4, 0.0, 2.15))]
    return [
        pack_surface("rig_body",   "rig_steel",   "progs/mmy_rig_steel",   body.st,   body.tris,   body_frames),
        pack_surface("rig_mech",   "rig_steel",   "progs/mmy_rig_steel",   mech_st,   mech_tris,   mech_frames),
        pack_surface("megaman_bar","chrome_axle", "progs/mmw_chrome_axle", mm_bar_st, mm_bar_tris, mm_bar_frames),
        pack_surface("megaman_whl","wheel",       "progs/mmw_wheel",       mm_wh_st,  mm_wh_tris,  mm_whl_frames),
        pack_surface("hands",      "hand",        "progs/mmw_hand",        hand_st,   hand_tris,   hand_frames),
        pack_surface("yeet_fx",    "fx",          "progs/mmy_fx",          fx_tpl.st, fx_tpl.tris, fx_frames),
    ], muzzle_eye


# ===========================================================================
# 4. VERSION 2: 'THE NUT-CRACKER SIEGE BALLISTA' (Wheelbarrow-Cam Crossbow)
# ===========================================================================
def build_v2_ballista_yeet():
    """Builds 37-frame MD3 surfaces for Version 2: Twin Wheelbarrow-Cam Compound Siege Ballista ('Tailpipe Spanker')."""
    to_pt, to_nrm = make_eye_xform(
        base=(5.15, -4.35, -4.45), scale=0.83, yaw=12.8, pitch=4.4, roll=-3.8,
    )

    body = MeshPart("rig_steel")
    # 1. Extra-long Ruled Steel Ballista Flight Track (x = 1.6 .. 23.8)
    add_ruled_scale_spine(body, x0=1.6, x1=23.8, y_c=0.0, z_top=+0.82, width=1.52, thick=0.54, stepped_tail=True)
    # Twin slotted guide rails along flight deck
    for sgn in (-1.0, +1.0):
        body.add_chamfer_box(2.2, 23.4, sgn * 0.94 - 0.14, sgn * 0.94 + 0.14, +0.62, +1.18, ch=0.03, uv_rect=UV_SQ_TUBE)

    # 2. Rear Breech Steel Drum Pan (tilted heroically as siege recoil drum w/ 3 hex leveling spikes!)
    add_steel_drum_pan(
        body, center=(2.2, 0.0, -1.05), axis=(-0.82, 0.0, -0.57),
        radius=3.85, height=1.02, bolt_angles=(-45.0, +45.0, +180.0), foot_drop=1.18, up_hint=(0.0, 0.0, 1.0),
    )
    # Hollow square-tube under-spine truss & front A-frame yoke struts
    for sgn in (-1.0, +1.0):
        add_hollow_square_tube(
            body, (3.2, sgn * 1.45, -1.15), (17.2, sgn * 1.85, +0.25),
            half_w=0.32, open_start=False, open_end=True, weld_start=True,
        )
    # 3. Front Prod Yoke: Upload 2's Threaded Square-Tube Crossbar w/ GIANT Zinc Hex Nuts!
    add_threaded_hex_crossbar(
        body, center=(17.8, 0.0, +0.52), bar_dir=(0.0, 1.0, 0.0),
        half_len=3.65, stud_ext=1.15, tube_hw=0.40, nut_r=0.64,
    )
    # Winch motor canister mounted at rear-left (x=5.0, y=+1.65) in crisp view of the player!
    add_motor_canister(body, base_pos=(4.95, +1.72, -0.15), axis=(0.0, +0.35, +0.94), radius=0.82, length=1.42)
    # OSHA 'DANGER: MEGA-YEET' side armor plate
    add_osha_placard(body, 6.2, 12.6, +0.95, +1.18, -0.42, +0.58)
    add_pistol_grip_and_trigger(body, gx=2.85, gy=-0.55, gz=-0.95)
    # Front vertical foregrip under yoke
    body.add_tube([(11.6, +1.05, -0.55), (11.8, +1.35, -2.55)], [0.46, 0.50], segs=10, uv_rect=UV_RED_LEVER)

    # --- Dynamic Parts ---
    bull_gear = build_spoked_bull_gear(outer_r=2.35, rim_in_r=1.68, hub_r=0.74, thick=0.26, n_teeth=28, n_spokes=6)
    nylon_pinion = build_nylon_pinion_gear(outer_r=0.72, thick=0.42, n_teeth=12)
    mini_capstan = build_4arm_pinwheel_rotor(mast_h=1.45, arm_len=2.15, mast_hw=0.30, arm_hw=0.20, with_plunger=False)

    # Left & Right Hollow Square-Tube Crossbow Limbs (local origin at hinge pivot, extending along +Y / -Y)
    limb_l = MeshPart("rig_steel")
    add_hollow_square_tube(limb_l, (0.0, 0.0, 0.0), (-2.35, +5.35, +0.22), half_w=0.34, open_end=True, weld_start=True)
    limb_r = MeshPart("rig_steel")
    add_hollow_square_tube(limb_r, (0.0, 0.0, 0.0), (-2.35, -5.35, +0.22), half_w=0.34, open_end=True, weld_start=True)

    # Square-Tube 'TAILPIPE SPANKER' Striker Sled
    striker = MeshPart("rig_steel")
    striker.add_chamfer_box(-0.75, +0.45, -1.15, +1.15, -0.35, +1.05, ch=0.08, uv_rect=UV_OSHA_DECAL, top_uv=UV_OSHA_DECAL)
    striker.add_lathe((+0.45, 0.0, +0.42), (1.0, 0.0, 0.0), [(0.0, 0.52, 0.1), (0.35, 0.46, 0.9), (0.36, 0.0, 1.0)], segs=12, uv_rect=UV_RED_LEVER)

    # Twin Wheelbarrow-Tire Compound Cams (mounted horizontally at limb tips!)
    cam_whl_base, cam_hw_base = _build_single_wheel(+1)

    mm_parts = build_megaman_payload_parts()
    fx_tpl = build_fx_template()

    lhand_local = build_articulated_ranger_hand(
        palm_center=(11.55, +1.35, -2.05),
        fwd_dir=(+0.32, -0.62, +0.72),
        up_dir=(-0.18, +0.72, +0.67),
        side_sign=+1.0,
        finger_curls=(0.82, 0.86, 0.88, 0.88),
        hand_scale=0.82,
        forearm_len=8.5,
    )

    # Fixed-topology 3D braided steel bowstring cable (left cam -> striker -> right cam: 5 points, 8-seg tube)
    def build_bowstring(p_cam_l, p_strk, p_cam_r):
        sp = MeshPart("rig_steel")
        pts = [
            p_cam_l,
            vlerp(p_cam_l, p_strk, 0.52),
            p_strk,
            vlerp(p_strk, p_cam_r, 0.48),
            p_cam_r,
        ]
        sp.add_tube(pts, [0.11, 0.10, 0.12, 0.10, 0.11], segs=8, uv_rect=UV_GRIP_CABLE)
        return sp

    str0 = build_bowstring((15.0, +8.5, +1.3), (5.5, 0.0, +1.3), (15.0, -8.5, +1.3))
    mech_parts = [bull_gear, nylon_pinion, mini_capstan, limb_l, limb_r, striker, str0]
    mech_st, mech_tris = [], []
    ofs = 0
    for mp_i in mech_parts:
        mech_st.extend(mp_i.st)
        mech_tris.extend([(a + ofs, b + ofs, c + ofs) for (a, b, c) in mp_i.tris])
        ofs += len(mp_i.verts)

    # Cam wheel surface (2 wheels -> ~2640 verts, well under 4096!)
    nw_c = len(cam_whl_base.verts)
    cam_whl_st = list(cam_whl_base.st) + list(cam_whl_base.st)
    cam_whl_tris = list(cam_whl_base.tris) + [(a + nw_c, b + nw_c, c + nw_c) for (a, b, c) in cam_whl_base.tris]

    # Payload surfaces
    mm_wh_tris = list(mm_parts["wheel_l"].tris) + [
        (a + len(mm_parts["wheel_l"].verts), b + len(mm_parts["wheel_l"].verts), c + len(mm_parts["wheel_l"].verts))
        for (a, b, c) in mm_parts["wheel_r"].tris
    ]
    mm_wh_st = list(mm_parts["wheel_l"].st) + list(mm_parts["wheel_r"].st)
    nhw_c = len(cam_hw_base.verts)
    mm_bar_nv0 = len(mm_parts["bar_axle"].verts)
    mm_bar_nv1 = mm_bar_nv0 + len(mm_parts["wheel_hw_l"].verts)
    mm_bar_nv2 = mm_bar_nv1 + len(mm_parts["wheel_hw_r"].verts)
    mm_bar_nv3 = mm_bar_nv2 + nhw_c
    mm_bar_st = (
        list(mm_parts["bar_axle"].st)
        + list(mm_parts["wheel_hw_l"].st)
        + list(mm_parts["wheel_hw_r"].st)
        + list(cam_hw_base.st)
        + list(cam_hw_base.st)
    )
    mm_bar_tris = (
        list(mm_parts["bar_axle"].tris)
        + [(a + mm_bar_nv0, b + mm_bar_nv0, c + mm_bar_nv0) for (a, b, c) in mm_parts["wheel_hw_l"].tris]
        + [(a + mm_bar_nv1, b + mm_bar_nv1, c + mm_bar_nv1) for (a, b, c) in mm_parts["wheel_hw_r"].tris]
        + [(a + mm_bar_nv2, b + mm_bar_nv2, c + mm_bar_nv2) for (a, b, c) in cam_hw_base.tris]
        + [(a + mm_bar_nv3, b + mm_bar_nv3, c + mm_bar_nv3) for (a, b, c) in cam_hw_base.tris]
    )

    body_frames, mech_frames, cam_whl_frames, mm_bar_frames, mm_whl_frames, hand_frames, fx_frames = [], [], [], [], [], [], []
    winch_ax = vnorm((0.0, +0.35, +0.94))

    for fi in range(37):
        dx = dy = dz = kp = kr = ky = 0.0
        draw_t = 1.0  # 1.0 = fully cocked back, 0.0 = snapped forward!
        winch_deg = 0.0
        pinion_disengage = 0.0
        mm_show = True
        mm_x = 10.65
        mm_z = 1.78
        mm_pitch = 0.0
        mm_sc = 0.90
        mm_spin = 0.0
        trig = 0.0
        fx_sc = 0.0005
        fx_pos = (10.0, 0.0, 0.0)
        fx_rot = 0.0

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            dx = 0.12 * math.sin(ph)
            dz = 0.16 * math.sin(ph * 2.0 + 0.5)
            kp = 0.45 * math.sin(ph + 0.3)
            kr = 0.55 * math.cos(ph)
            draw_t = 1.0 + 0.015 * math.sin(ph * 2.0)
            winch_deg = 2.5 * math.sin(ph * 2.0)
            mm_spin = fi * 22.5
        elif fi == 36:
            mm_show = False
            mm_sc = 0.001
            mm_x, mm_z = 4.0, -1.0
            draw_t = 0.15
        else:
            k = fi - 16
            if k == 0:    # Trigger pull, nylon pinion pops out of ratchet!
                trig, pinion_disengage = 0.75, 0.35
                draw_t = 1.04
                dx, dz, kp = -0.25, +0.10, +1.4
                mm_spin = 50.0
            elif k == 1:  # Striker begins surging!
                trig, pinion_disengage = 1.0, 0.55
                draw_t = 0.68
                mm_x = 14.2
                winch_deg = -140.0
                dx, dz, kp, kr = -0.85, +0.26, +3.8, -1.8
                mm_spin = 140.0
                fx_sc, fx_pos, fx_rot = 2.2, (11.5, 0.0, 1.8), 35.0
            elif k == 2:  # Tailpipe Spanker SLAMS Mega Man down flight deck!
                trig, pinion_disengage = 1.0, 0.55
                draw_t = 0.18
                mm_x = 20.4
                winch_deg = -360.0
                dx, dz, kp, kr = -1.75, +0.48, +6.8, -3.2
                mm_spin = 280.0
                fx_sc, fx_pos, fx_rot = 4.6, (21.5, 0.0, 1.9), 120.0
            elif k == 3:  # FRAME 19: SUPERSONIC BALLISTA LAUNCH!
                trig, pinion_disengage = 1.0, 0.55
                draw_t = -0.08  # limbs spring slightly past zero!
                mm_x, mm_z, mm_pitch = 29.2, 2.15, -2.0
                winch_deg = -580.0
                dx, dz, kp, kr = -2.65, +0.68, +9.2, -4.4
                mm_spin = 460.0
                fx_sc, fx_pos, fx_rot = 5.8, (24.0, 0.0, 1.9), 240.0
            elif k == 4:  # Frame 20: Clean handoff shrink + damped bowstring twang!
                trig, pinion_disengage = 0.65, 0.45
                draw_t = +0.06
                mm_x, mm_sc = 39.0, 0.001
                winch_deg = -720.0
                dx, dz, kp, kr = -2.10, +0.52, +7.2, -3.0
                fx_sc, fx_pos, fx_rot = 3.5, (24.4, 0.0, 1.9), 310.0
            elif k <= 8:  # Frames 21..24: Bowstring harmonic twang, pinion re-engages!
                t_c = (k - 4) / 4.0
                draw_t = 0.04 * math.cos(t_c * math.pi * 3.0) * (1.0 - t_c)
                pinion_disengage = 0.45 * (1.0 - smoothstep(t_c))
                winch_deg = -720.0 - 60.0 * t_c
                dx = -1.5 * (1.0 - t_c)
                dz = +0.32 * (1.0 - t_c)
                kp = +4.8 * (1.0 - t_c)
                mm_show, mm_sc = False, 0.001
            else:         # Frames 25..35 (k=9..19): White nylon pinion cranks bull-gear winch back to full draw!
                t_r = (k - 9) / 10.0
                s_r = smoothstep(t_r)
                draw_t = s_r
                winch_deg = -780.0 + 780.0 * s_r
                # Fresh Mega Man rises onto flight deck in second half of crank!
                pop_t = smoothstep(max(0.0, min(1.0, (t_r - 0.32) / 0.58)))
                mm_sc = 0.90 * smoothstep(max(0.0, min(1.0, (t_r - 0.25) / 0.35)))
                mm_show = mm_sc > 0.01
                mm_x = 10.65
                mm_z = -0.95 + 2.73 * pop_t
                mm_pitch = 10.0 * (1.0 - pop_t)
                mm_spin = t_r * 160.0
                dx = -0.22 * math.sin(t_r * math.pi)
                kp = -1.1 * math.sin(t_r * math.pi)

        # Limb sweep angle: cocked = +22 deg swept back; snapped forward = -18 deg!
        limb_ang = -18.0 + 40.0 * draw_t
        strk_x = 5.15 + 15.65 * (1.0 - draw_t)

        # Limb tip positions in gun space (pivots at (17.8, +/-3.4, +0.62))
        tip_local_l = rot_z((-2.35, +5.35, +0.22), +limb_ang)
        tip_local_r = rot_z((-2.35, -5.35, +0.22), -limb_ang)
        cam_pos_l = vadd((17.8, +3.4, +0.62), tip_local_l)
        cam_pos_r = vadd((17.8, -3.4, +0.62), tip_local_r)

        # 1) Static Body
        body_frames.append(apply_eye_list(body.verts, body.norms, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 2) Mech (Bull Gear + White Nylon Pinion + 4-Arm Capstan + Limbs + Striker + Live Bowstring)
        bv_g, bn_g = transform_part(bull_gear, pos=(6.35, +2.05, +1.62), rx=-20.0, axis_rot=(winch_ax, winch_deg))
        pv_g, pn_g = transform_part(
            nylon_pinion,
            pos=(4.65 - 0.45 * pinion_disengage, +2.25, +1.25),
            rx=-20.0,
            axis_rot=(winch_ax, -winch_deg * 2.4),
        )
        cv_g, cn_g = transform_part(mini_capstan, pos=(6.35, +2.20, +1.85), rx=-20.0, axis_rot=(winch_ax, winch_deg))
        ll_v, ll_n = transform_part(limb_l, pos=(17.8, +3.4, +0.62), rz=+limb_ang)
        lr_v, lr_n = transform_part(limb_r, pos=(17.8, -3.4, +0.62), rz=-limb_ang)
        st_v, st_n = transform_part(striker, pos=(strk_x, 0.0, +0.92))
        bstr = build_bowstring(
            (cam_pos_l[0], cam_pos_l[1], cam_pos_l[2] + 0.35),
            (strk_x - 0.35, 0.0, +1.28),
            (cam_pos_r[0], cam_pos_r[1], cam_pos_r[2] + 0.35),
        )
        mech_frames.append(apply_eye_list(
            bv_g + pv_g + cv_g + ll_v + lr_v + st_v + bstr.verts,
            bn_g + pn_g + cn_g + ll_n + lr_n + st_n + bstr.norms,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 3) Horizontal Wheelbarrow-Tire Compound Cams (rx=-90 puts wheel dish facing +Z skyward!)
        cam_spin = (1.0 - draw_t) * 280.0
        cwl_v, cwl_n = transform_part(cam_whl_base, pos=cam_pos_l, rx=-90.0, rz=+cam_spin, scale=0.62)
        cwr_v, cwr_n = transform_part(cam_whl_base, pos=cam_pos_r, rx=-90.0, rz=-cam_spin, scale=0.62)
        cam_whl_frames.append(apply_eye_list(cwl_v + cwr_v, cwl_n + cwr_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        chl_v, chl_n = transform_part(cam_hw_base, pos=cam_pos_l, rx=-90.0, rz=+cam_spin, scale=0.62)
        chr_v, chr_n = transform_part(cam_hw_base, pos=cam_pos_r, rx=-90.0, rz=-cam_spin, scale=0.62)

        # 4) Hero Mega Man + Cam Hub Hardware
        mm_xf = transform_megaman_frame(
            mm_parts, spin_deg=mm_spin, bar_pitch_deg=mm_pitch,
            pos=(mm_x, 0.0, mm_z), scale=mm_sc if mm_show else 0.001,
        )
        bar_v = mm_xf["bar_axle"][0] + mm_xf["wheel_hw_l"][0] + mm_xf["wheel_hw_r"][0] + chl_v + chr_v
        bar_n = mm_xf["bar_axle"][1] + mm_xf["wheel_hw_l"][1] + mm_xf["wheel_hw_r"][1] + chl_n + chr_n
        whl_v = mm_xf["wheel_l"][0] + mm_xf["wheel_r"][0]
        whl_n = mm_xf["wheel_l"][1] + mm_xf["wheel_r"][1]
        mm_bar_frames.append(apply_eye_list(bar_v, bar_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))
        mm_whl_frames.append(apply_eye_list(whl_v, whl_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 5) Hands
        rh = build_articulated_ranger_hand(
            palm_center=(2.75, -0.78, -2.35),
            fwd_dir=(+0.78, +0.44, +0.44),
            up_dir=(-0.22, -0.52, +0.82),
            side_sign=-1.0,
            finger_curls=(0.45 + 0.42 * trig, 0.86, 0.88, 0.90),
            hand_scale=0.82,
            forearm_len=8.6,
        )
        hand_frames.append(apply_eye_list(
            rh.verts + lhand_local.verts, rh.norms + lhand_local.norms,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 6) FX
        fv, fn = transform_part(fx_tpl, pos=fx_pos, rx=fx_rot, scale=fx_sc)
        fx_frames.append(apply_eye_list(fv, fn, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

    rh0 = build_articulated_ranger_hand((0, 0, 0), (1, 0, 0), (0, 0, 1), hand_scale=0.82, forearm_len=8.6)
    n_rh = len(rh0.verts)
    hand_st = list(rh0.st) + list(lhand_local.st)
    hand_tris = list(rh0.tris) + [(a + n_rh, b + n_rh, c + n_rh) for (a, b, c) in lhand_local.tris]

    muzzle_eye = [round(c, 2) for c in to_pt((24.2, 0.0, 1.95))]
    return [
        pack_surface("rig_body",    "rig_steel",   "progs/mmy_rig_steel",   body.st,    body.tris,    body_frames),
        pack_surface("rig_mech",    "rig_steel",   "progs/mmy_rig_steel",   mech_st,    mech_tris,    mech_frames),
        pack_surface("cam_wheels",  "wheel",       "progs/mmw_wheel",       cam_whl_st, cam_whl_tris, cam_whl_frames),
        pack_surface("megaman_bar", "chrome_axle", "progs/mmw_chrome_axle", mm_bar_st,  mm_bar_tris,  mm_bar_frames),
        pack_surface("megaman_whl", "wheel",       "progs/mmw_wheel",       mm_wh_st,   mm_wh_tris,   mm_whl_frames),
        pack_surface("hands",       "hand",        "progs/mmw_hand",        hand_st,    hand_tris,    hand_frames),
        pack_surface("yeet_fx",     "fx",          "progs/mmy_fx",          fx_tpl.st,  fx_tpl.tris,  fx_frames),
    ], muzzle_eye


# ===========================================================================
# 5. VERSION 3: 'THE BURNOUT PITCHING-BAZOOKA' (4-Tube Cage + Dual Squeeze Tires)
# ===========================================================================
def build_v3_burnout_bazooka():
    """Builds 37-frame MD3 surfaces for Version 3: 4-Square-Tube Open Railgun + Dual Burnout Squeeze-Tire Cannon."""
    to_pt, to_nrm = make_eye_xform(
        base=(5.05, -4.75, -4.85), scale=0.83, yaw=13.6, pitch=4.0, roll=-3.8,
    )

    body = MeshPart("rig_steel")
    # 1. 4 Parallel Hollow Square-Tube Open Railgun Cage Arms (with hollow open muzzles!)
    rail_coords = [
        (-2.05, +0.25),
        (+2.05, +0.25),
        (-1.82, +3.18),
        (+1.82, +3.18),
    ]
    for ry, rz in rail_coords:
        add_hollow_square_tube(
            body, (2.2, ry, rz), (21.6, ry, rz),
            half_w=0.31, open_start=False, open_end=True, weld_start=True,
        )

    # 2. Two Threaded Square-Tube Cross-Frames w/ GIANT Zinc Hex Nuts at x=6.0 & x=16.8!
    add_threaded_hex_crossbar(body, center=(6.0, 0.0, +0.25), bar_dir=(0.0, 1.0, 0.0), half_len=2.65, stud_ext=1.10, tube_hw=0.34, nut_r=0.58)
    add_threaded_hex_crossbar(body, center=(16.8, 0.0, +0.25), bar_dir=(0.0, 1.0, 0.0), half_len=2.85, stud_ext=1.15, tube_hw=0.36, nut_r=0.60)
    # Vertical side square-tube stanchions tying upper & lower rails
    for x_st in (3.2, 6.0, 16.8):
        for sgn in (-1.0, +1.0):
            add_hollow_square_tube(
                body, (x_st, sgn * 1.95, +0.25), (x_st, sgn * 1.82, +3.18),
                half_w=0.25, open_start=False, open_end=False, weld_start=True, weld_end=True,
            )

    # 3. Top Brushed-Steel Ruled Scale Spine Bar ('10m..80m..BAKERSFIELD..FRESNO..ORBIT..BYE!!')
    add_ruled_scale_spine(body, x0=2.4, x1=17.6, y_c=0.0, z_top=+3.78, width=1.36, thick=0.42, stepped_tail=True)

    # 4. Underslung Heavy Circular Steel Drum Pan Magazine w/ 3 Hex Leveling Bolts!
    add_steel_drum_pan(
        body, center=(10.2, 0.0, -2.15), axis=(0.0, 0.0, 1.0),
        radius=4.35, height=1.08, bolt_angles=(-58.0, +62.0, +180.0), foot_drop=1.22,
    )
    # OSHA 'DANGER: MEGA-YEET' side placard + Side Motor Canister for White Nylon Pinion!
    add_osha_placard(body, 10.8, 16.2, +1.88, +2.10, +0.55, +2.85)
    add_motor_canister(body, base_pos=(5.15, +2.12, +1.72), axis=(0.0, 1.0, 0.0), radius=0.80, length=1.25)

    # Long polished steel diagonal driveshaft connecting side bull-gear forward to muzzle burnout wheels!
    body.add_tube([(7.9, +2.95, +1.72), (19.6, +4.05, +1.72)], [0.14, 0.14], segs=10, uv_rect=UV_HEX_ZINC)
    add_pistol_grip_and_trigger(body, gx=2.55, gy=-0.55, gz=-0.55)
    body.add_tube([(14.8, +1.55, -0.15), (15.1, +1.75, -2.35)], [0.46, 0.50], segs=10, uv_rect=UV_RED_LEVER)

    # --- Dynamic Parts (Side 6-Spoked Bull Gear + White Nylon Pinion + 4-Arm Chopper + Feeder Rod + Muzzle Forks) ---
    bull_gear = build_spoked_bull_gear(outer_r=2.38, rim_in_r=1.70, hub_r=0.74, thick=0.26, n_teeth=28, n_spokes=6)
    nylon_pinion = build_nylon_pinion_gear(outer_r=0.72, thick=0.42, n_teeth=12)
    side_chopper = build_4arm_pinwheel_rotor(mast_h=1.15, arm_len=1.95, mast_hw=0.28, arm_hw=0.18, with_plunger=False)

    fork_l = MeshPart("rig_steel")
    add_hollow_square_tube(fork_l, (-3.2, -1.2, 0.0), (0.0, 0.0, 0.0), half_w=0.30, open_end=True, weld_start=True)
    fork_r = MeshPart("rig_steel")
    add_hollow_square_tube(fork_r, (-3.2, +1.2, 0.0), (0.0, 0.0, 0.0), half_w=0.30, open_end=True, weld_start=True)

    feeder = MeshPart("rig_steel")
    feeder.add_tube([(-6.5, 0.0, 0.0), (0.0, 0.0, 0.0)], [0.22, 0.28], segs=10, uv_rect=UV_HEX_ZINC)
    feeder.add_lathe((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), [(0.0, 0.65, 0.1), (0.42, 0.62, 0.9), (0.43, 0.0, 1.0)], segs=12, uv_rect=UV_BRASS_PIN)

    fly_whl_base, fly_hw_base = _build_single_wheel(+1)
    mm_parts = build_megaman_payload_parts()
    fx_tpl = build_fx_template()

    lhand_local = build_articulated_ranger_hand(
        palm_center=(14.95, +1.65, -1.85),
        fwd_dir=(+0.30, -0.62, +0.72),
        up_dir=(-0.18, +0.72, +0.67),
        side_sign=+1.0,
        finger_curls=(0.82, 0.86, 0.88, 0.88),
        hand_scale=0.82,
        forearm_len=8.5,
    )

    mech_parts = [bull_gear, nylon_pinion, side_chopper, fork_l, fork_r, feeder]
    mech_st, mech_tris = [], []
    ofs = 0
    for mp_i in mech_parts:
        mech_st.extend(mp_i.st)
        mech_tris.extend([(a + ofs, b + ofs, c + ofs) for (a, b, c) in mp_i.tris])
        ofs += len(mp_i.verts)

    nw_f = len(fly_whl_base.verts)
    fly_whl_st = list(fly_whl_base.st) + list(fly_whl_base.st)
    fly_whl_tris = list(fly_whl_base.tris) + [(a + nw_f, b + nw_f, c + nw_f) for (a, b, c) in fly_whl_base.tris]

    mm_wh_tris = list(mm_parts["wheel_l"].tris) + [
        (a + len(mm_parts["wheel_l"].verts), b + len(mm_parts["wheel_l"].verts), c + len(mm_parts["wheel_l"].verts))
        for (a, b, c) in mm_parts["wheel_r"].tris
    ]
    mm_wh_st = list(mm_parts["wheel_l"].st) + list(mm_parts["wheel_r"].st)
    nhw_f = len(fly_hw_base.verts)
    mm_bar_nv0 = len(mm_parts["bar_axle"].verts)
    mm_bar_nv1 = mm_bar_nv0 + len(mm_parts["wheel_hw_l"].verts)
    mm_bar_nv2 = mm_bar_nv1 + len(mm_parts["wheel_hw_r"].verts)
    mm_bar_nv3 = mm_bar_nv2 + nhw_f
    mm_bar_st = (
        list(mm_parts["bar_axle"].st)
        + list(mm_parts["wheel_hw_l"].st)
        + list(mm_parts["wheel_hw_r"].st)
        + list(fly_hw_base.st)
        + list(fly_hw_base.st)
    )
    mm_bar_tris = (
        list(mm_parts["bar_axle"].tris)
        + [(a + mm_bar_nv0, b + mm_bar_nv0, c + mm_bar_nv0) for (a, b, c) in mm_parts["wheel_hw_l"].tris]
        + [(a + mm_bar_nv1, b + mm_bar_nv1, c + mm_bar_nv1) for (a, b, c) in mm_parts["wheel_hw_r"].tris]
        + [(a + mm_bar_nv2, b + mm_bar_nv2, c + mm_bar_nv2) for (a, b, c) in fly_hw_base.tris]
        + [(a + mm_bar_nv3, b + mm_bar_nv3, c + mm_bar_nv3) for (a, b, c) in fly_hw_base.tris]
    )

    body_frames, mech_frames, fly_whl_frames, mm_bar_frames, mm_whl_frames, hand_frames, fx_frames = [], [], [], [], [], [], []

    for fi in range(37):
        dx = dy = dz = kp = kr = ky = 0.0
        fly_spin = 0.0
        gear_deg = 0.0
        squeeze_y = 3.92   # Muzzle burnout wheel center Y (wheel r = 4.02*0.86 = 3.46 -> 0.46 gap for chrome shaft!)
        feed_x = 6.35
        mm_show = True
        mm_x = 11.45       # Chrome bullet nose (+4.8) sits right at x=16.25 kissing the twin burnout tires!
        mm_z = 1.72
        mm_pitch = 0.0
        mm_sc = 0.88
        mm_spin = 0.0
        trig = 0.0
        fx_sc = 0.0005
        fx_pos = (10.0, 0.0, 0.0)
        fx_rot = 0.0

        if fi < 16:
            ph = 2.0 * math.pi * (fi / 16.0)
            dx = 0.13 * math.sin(ph)
            dz = 0.17 * math.sin(ph * 2.0 + 0.4)
            kp = 0.50 * math.sin(ph + 0.3)
            kr = 0.60 * math.cos(ph)
            # Continuous idle flywheel hum (full 360 across 16 frames so seamless loop!)
            fly_spin = fi * 22.5
            gear_deg = fi * 22.5
            mm_spin = fi * 22.5
            mm_x = 11.45 + 0.08 * math.sin(ph * 4.0)
        elif fi == 36:
            mm_show = False
            mm_sc = 0.001
            mm_x, mm_z = 10.2, -2.0
            fly_spin = 0.0
        else:
            k = fi - 16
            if k == 0:    # Trigger squeeze! Twin muzzle tires rev hard & pinch inward!
                trig = 0.75
                squeeze_y = 3.68
                fly_spin, gear_deg = 85.0, 55.0
                feed_x = 7.4
                mm_x = 12.5
                dx, dz, kp = -0.35, +0.12, +1.8
                fx_sc, fx_pos, fx_rot = 2.0, (19.8, 0.0, 1.72), 40.0
            elif k == 1:  # CHROME SHAFT PLUNGES BETWEEN SQUEEZING BURNOUT TIRES!
                trig = 1.0
                squeeze_y = 3.58  # Maximum tire-bun pinch on chrome shaft!
                fly_spin, gear_deg = 225.0, 145.0
                feed_x = 11.8
                mm_x = 16.8
                mm_spin = 160.0
                dx, dz, kp, kr = -0.95, +0.28, +4.2, -2.0
                fx_sc, fx_pos, fx_rot = 3.8, (20.4, 0.0, 1.72), 115.0
            elif k == 2:  # TIRES VIOLENTLY GRAB AXLE & SPRING WIDE AS MEGA MAN BLASTS THROUGH!
                trig = 1.0
                squeeze_y = 6.55  # Spring forks kick wide open so Mega Man's wide vertical tires clear cleanly!
                fly_spin, gear_deg = 410.0, 260.0
                feed_x = 14.8
                mm_x = 23.2
                mm_spin = 340.0
                dx, dz, kp, kr = -1.95, +0.52, +7.6, -3.5
                fx_sc, fx_pos, fx_rot = 5.4, (22.6, 0.0, 1.78), 210.0
            elif k == 3:  # FRAME 19: MACH-4 BURNOUT RAILGUN YEET!
                trig = 1.0
                squeeze_y = 5.45
                fly_spin, gear_deg = 620.0, 385.0
                feed_x = 14.5
                mm_x, mm_z, mm_pitch = 30.5, 2.05, -2.2
                mm_spin = 540.0
                dx, dz, kp, kr = -2.85, +0.74, +10.2, -4.6
                fx_sc, fx_pos, fx_rot = 6.2, (23.8, 0.0, 1.82), 315.0
            elif k == 4:  # Frame 20: Clean handoff shrink + burnout smoke plume!
                trig = 0.7
                squeeze_y = 3.98
                fly_spin, gear_deg = 790.0, 490.0
                feed_x = 12.2
                mm_x, mm_sc = 40.0, 0.001
                dx, dz, kp, kr = -2.25, +0.56, +7.8, -3.2
                fx_sc, fx_pos, fx_rot = 4.2, (23.2, 0.0, 1.85), 55.0
            elif k <= 8:  # Frames 21..24: Feeder rod retracts, burnout tires coast down
                t_c = (k - 4) / 4.0
                squeeze_y = 3.92
                fly_spin = 790.0 + 290.0 * t_c
                gear_deg = 490.0 + 230.0 * t_c
                feed_x = 12.2 - 5.85 * smoothstep(t_c)
                dx = -1.6 * (1.0 - t_c)
                dz = +0.35 * (1.0 - t_c)
                kp = +5.0 * (1.0 - t_c)
                mm_show, mm_sc = False, 0.001
            else:         # Frames 25..35 (k=9..19): Fresh Mega Man clatters up from Circular Drum Pan into 4-tube cage!
                t_r = (k - 9) / 10.0
                s_r = smoothstep(min(1.0, t_r * 1.2))
                fly_spin = 1080.0 + 360.0 * t_r
                gear_deg = 720.0 + 360.0 * t_r
                mm_sc = 0.88 * smoothstep(min(1.0, t_r * 2.2))
                mm_x = 10.2 + 1.25 * s_r
                mm_z = -1.85 + 3.57 * s_r + 0.16 * math.sin(t_r * math.pi) * (1.0 - t_r)
                mm_pitch = 12.0 * (1.0 - s_r)
                mm_spin = t_r * 180.0
                dx = -0.18 * math.sin(t_r * math.pi)
                dz = -0.20 * math.sin(t_r * math.pi)

        # 1) Static 4-tube cage + drum pan
        body_frames.append(apply_eye_list(body.verts, body.norms, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 2) Side Bull-Gear (rx=-90 puts gear face facing +Y toward player!) + White Nylon Pinion + Forks + Feeder
        bv_g, bn_g = transform_part(bull_gear, pos=(8.25, +2.78, +1.72), rx=-90.0, axis_rot=((0.0, 1.0, 0.0), gear_deg))
        pv_g, pn_g = transform_part(nylon_pinion, pos=(5.25, +2.92, +1.72), rx=-90.0, axis_rot=((0.0, 1.0, 0.0), -gear_deg * 2.4))
        ch_v, ch_n = transform_part(side_chopper, pos=(8.25, +2.92, +1.72), rx=-90.0, axis_rot=((0.0, 1.0, 0.0), gear_deg))
        fl_v, fl_n = transform_part(fork_l, pos=(20.1, +squeeze_y, +1.72))
        fr_v, fr_n = transform_part(fork_r, pos=(20.1, -squeeze_y, +1.72))
        fd_v, fd_n = transform_part(feeder, pos=(feed_x, 0.0, +1.72))
        mech_frames.append(apply_eye_list(
            bv_g + pv_g + ch_v + fl_v + fr_v + fd_v,
            bn_g + pn_g + ch_n + fl_n + fr_n + fd_n,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 3) Muzzle Dual Counter-Rotating Burnout Wheelbarrow Tires (rx=-90 -> white dish faces +Z!)
        fwl_v, fwl_n = transform_part(fly_whl_base, pos=(20.1, +squeeze_y, +1.72), rx=-90.0, rz=-fly_spin, scale=0.84)
        fwr_v, fwr_n = transform_part(fly_whl_base, pos=(20.1, -squeeze_y, +1.72), rx=-90.0, rz=+fly_spin, scale=0.84)
        fly_whl_frames.append(apply_eye_list(fwl_v + fwr_v, fwl_n + fwr_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        fhl_v, fhl_n = transform_part(fly_hw_base, pos=(20.1, +squeeze_y, +1.72), rx=-90.0, rz=-fly_spin, scale=0.84)
        fhr_v, fhr_n = transform_part(fly_hw_base, pos=(20.1, -squeeze_y, +1.72), rx=-90.0, rz=+fly_spin, scale=0.84)

        # 4) Hero Mega Man + Flywheel Hub Hardware
        mm_xf = transform_megaman_frame(
            mm_parts, spin_deg=mm_spin, bar_pitch_deg=mm_pitch,
            pos=(mm_x, 0.0, mm_z), scale=mm_sc if mm_show else 0.001,
        )
        bar_v = mm_xf["bar_axle"][0] + mm_xf["wheel_hw_l"][0] + mm_xf["wheel_hw_r"][0] + fhl_v + fhr_v
        bar_n = mm_xf["bar_axle"][1] + mm_xf["wheel_hw_l"][1] + mm_xf["wheel_hw_r"][1] + fhl_n + fhr_n
        whl_v = mm_xf["wheel_l"][0] + mm_xf["wheel_r"][0]
        whl_n = mm_xf["wheel_l"][1] + mm_xf["wheel_r"][1]
        mm_bar_frames.append(apply_eye_list(bar_v, bar_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))
        mm_whl_frames.append(apply_eye_list(whl_v, whl_n, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

        # 5) Hands
        rh = build_articulated_ranger_hand(
            palm_center=(2.45, -0.78, -1.95),
            fwd_dir=(+0.78, +0.44, +0.44),
            up_dir=(-0.22, -0.52, +0.82),
            side_sign=-1.0,
            finger_curls=(0.45 + 0.42 * trig, 0.86, 0.88, 0.90),
            hand_scale=0.82,
            forearm_len=8.6,
        )
        hand_frames.append(apply_eye_list(
            rh.verts + lhand_local.verts, rh.norms + lhand_local.norms,
            to_pt, to_nrm, dx, dy, dz, kp, kr, ky,
        ))

        # 6) FX
        fv, fn = transform_part(fx_tpl, pos=fx_pos, rx=fx_rot, scale=fx_sc)
        fx_frames.append(apply_eye_list(fv, fn, to_pt, to_nrm, dx, dy, dz, kp, kr, ky))

    rh0 = build_articulated_ranger_hand((0, 0, 0), (1, 0, 0), (0, 0, 1), hand_scale=0.82, forearm_len=8.6)
    n_rh = len(rh0.verts)
    hand_st = list(rh0.st) + list(lhand_local.st)
    hand_tris = list(rh0.tris) + [(a + n_rh, b + n_rh, c + n_rh) for (a, b, c) in lhand_local.tris]

    muzzle_eye = [round(c, 2) for c in to_pt((23.6, 0.0, 1.82))]
    return [
        pack_surface("rig_body",    "rig_steel",   "progs/mmy_rig_steel",   body.st,    body.tris,    body_frames),
        pack_surface("rig_mech",    "rig_steel",   "progs/mmy_rig_steel",   mech_st,    mech_tris,    mech_frames),
        pack_surface("fly_wheels",  "wheel",       "progs/mmw_wheel",       fly_whl_st, fly_whl_tris, fly_whl_frames),
        pack_surface("megaman_bar", "chrome_axle", "progs/mmw_chrome_axle", mm_bar_st,  mm_bar_tris,  mm_bar_frames),
        pack_surface("megaman_whl", "wheel",       "progs/mmw_wheel",       mm_wh_st,   mm_wh_tris,   mm_whl_frames),
        pack_surface("hands",       "hand",        "progs/mmw_hand",        hand_st,    hand_tris,    hand_frames),
        pack_surface("yeet_fx",     "fx",          "progs/mmy_fx",          fx_tpl.st,  fx_tpl.tris,  fx_frames),
    ], muzzle_eye
