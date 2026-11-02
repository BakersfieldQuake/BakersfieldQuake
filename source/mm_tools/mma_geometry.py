"""3D Procedural Geometry & 89-Frame Animation Builders for the 4-Version Mega Man Arsenal:

  1. V1 · THE CANNON     (progs/v_mm_cannon.md3)    : Slotted Cast-Iron & Riveted-Brass Blunder-Cannon
  2. V2 · THE SLINGSHOT  (progs/v_mm_slingshot.md3) : Carved Walnut & Surgical-Latex Tactical Wrist-Rocket Y-Slinger
  3. V3 · THE BOW        (progs/v_mm_bow.md3)       : Carbon-Weave Compound/Recurve Battle Bow & Fletched Mega-Arrow
  4. V4 · HAND-THROWER   (progs/v_mm_handthrow.md3) : Bare-Handed Quake Ranger Gloved Grip & Overhand Mega-Chuck

All 4 weapon models share a unified 89-frame schedule (100% backward-compatible on 0..36 with megaman.qc):
  - Frames  0..15 (16 frames): Idle Loop — Continuous 360° wheel spin + lively multi-axis contraption bobbling!
  - Frames 16..35 (20 frames): Fire / Launch (frame 19) / Recoil / Weapon-Specific Mechanical or Hand Reload!
  - Frame  36     ( 1 frame ): Empty state ('empty1') while recharging
  - Frames 37..60 (24 frames): CoD Inspect A ('Hold Out') — Tilts & turns weapon left/right to admire + flourish!
  - Frames 61..88 (28 frames): CoD Inspect B ('Clean the Bar') — Grabs the gleaming chrome bar with a red shop rag,
                               strokes/polishes it up-and-down from collar to tip, ending with a 3D star-glint!
"""
import math
from mmw_geometry import (
    MM_WHEEL_Y,
    MeshPart,
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
from mma_textures import (
    UV_BOW_CAM_STR,
    UV_BRASS_BAND,
    UV_CANNON_IRON,
    UV_CARBON_LIMB,
    UV_COIL_STEEL,
    UV_DARK_BORE,
    UV_FIBER_SIGHT,
    UV_FX_BLAST,
    UV_FX_GLINT,
    UV_FX_SMOKE,
    UV_FX_SNAP,
    UV_LATEX_AMBER,
    UV_POUCH_LEATHER,
    UV_SHOP_RAG,
    UV_WALNUT_WOOD,
)

FRAME_NAMES_89 = (
    [f"idle{i + 1}" for i in range(16)]
    + [f"fire{i + 1}" for i in range(20)]
    + ["empty1"]
    + [f"insp_hold{i + 1}" for i in range(24)]
    + [f"insp_clean{i + 1}" for i in range(28)]
)
assert len(FRAME_NAMES_89) == 89


# ===========================================================================
# SHARED TRANSFORMS, SHOP POLISHING RAG & FX BUILDERS
# ===========================================================================
def rig_pt_to_eye(p, base, scale, roll_d, pitch_d, yaw_d):
    q = vmul(p, scale)
    q = rot_x(q, roll_d)
    q = rot_y(q, pitch_d)
    q = rot_z(q, yaw_d)
    return vadd(q, base)


def rig_nrm_to_eye(n, roll_d, pitch_d, yaw_d):
    qn = rot_x(n, roll_d)
    qn = rot_y(qn, pitch_d)
    qn = rot_z(qn, yaw_d)
    return vnorm(qn)


def transform_mesh_to_eye(mp, base, scale, roll_d, pitch_d, yaw_d, local_off=(0.0, 0.0, 0.0), local_rx=0.0, local_ry=0.0, local_rz=0.0, local_sc=1.0):
    vv, nn = [], []
    for p, n in zip(mp.verts, mp.norms):
        lp = vmul(p, local_sc)
        ln = n
        if local_rx:
            lp, ln = rot_x(lp, local_rx), rot_x(ln, local_rx)
        if local_ry:
            lp, ln = rot_y(lp, local_ry), rot_y(ln, local_ry)
        if local_rz:
            lp, ln = rot_z(lp, local_rz), rot_z(ln, local_rz)
        lp = vadd(lp, local_off)
        vv.append(rig_pt_to_eye(lp, base, scale, roll_d, pitch_d, yaw_d))
        nn.append(rig_nrm_to_eye(ln, roll_d, pitch_d, yaw_d))
    return vv, nn


def megaman_eye_frames_and_tip(mm_parts, mm_local_pos, spin_deg, mm_pitch, mm_roll, mm_yaw, mm_scale, base, rig_scale, rig_roll, rig_pitch, rig_yaw):
    """Transforms Mega Man payload into eye space AND returns exact eye-space (bar_origin, bar_unit_axis, tip_pos)."""
    xf = transform_megaman_frame(
        mm_parts,
        spin_deg=spin_deg,
        bar_pitch_deg=mm_pitch,
        pos=mm_local_pos,
        yaw_deg=mm_yaw,
        roll_deg=mm_roll,
        scale=mm_scale,
    )
    ca_v_loc = xf["bar_axle"][0] + xf["wheel_hw_l"][0] + xf["wheel_hw_r"][0]
    ca_n_loc = xf["bar_axle"][1] + xf["wheel_hw_l"][1] + xf["wheel_hw_r"][1]
    wh_v_loc = xf["wheel_l"][0] + xf["wheel_r"][0]
    wh_n_loc = xf["wheel_l"][1] + xf["wheel_r"][1]

    ca_v = [rig_pt_to_eye(p, base, rig_scale, rig_roll, rig_pitch, rig_yaw) for p in ca_v_loc]
    ca_n = [rig_nrm_to_eye(n, rig_roll, rig_pitch, rig_yaw) for n in ca_n_loc]
    wh_v = [rig_pt_to_eye(p, base, rig_scale, rig_roll, rig_pitch, rig_yaw) for p in wh_v_loc]
    wh_n = [rig_nrm_to_eye(n, rig_roll, rig_pitch, rig_yaw) for n in wh_n_loc]

    # Exact bar axis & tip in local rig space -> eye space
    def mm_pt_loc(px):
        q = (px, 0.0, 0.0)
        if mm_pitch:
            q = rot_y(q, mm_pitch)
        if mm_roll:
            q = rot_x(q, mm_roll)
        if mm_yaw:
            q = rot_z(q, mm_yaw)
        return vadd(vmul(q, mm_scale), mm_local_pos)

    p_orig_eye = rig_pt_to_eye(mm_pt_loc(0.0), base, rig_scale, rig_roll, rig_pitch, rig_yaw)
    p_tip_eye = rig_pt_to_eye(mm_pt_loc(5.38), base, rig_scale, rig_roll, rig_pitch, rig_yaw)
    bar_axis_eye = vnorm(vsub(p_tip_eye, p_orig_eye))
    return (ca_v, ca_n), (wh_v, wh_n), p_orig_eye, bar_axis_eye, p_tip_eye


def build_shop_rag_part(center_eye, bar_axis_eye, wrap_up_eye, vis_scale=1.0, wave_ph=0.0):
    """Fixed-topology curved red mechanic's shop cloth wrapping around the chrome bar during Inspect B!
    When vis_scale < 0.02, shrinks neatly inside the polishing hand's cuff so vertex count stays 100% constant.
    """
    mp = MeshPart("arsenal")
    X = vnorm(bar_axis_eye)
    Z_raw = vsub(wrap_up_eye, vmul(X, vdot(wrap_up_eye, X)))
    Z = vnorm(Z_raw) if vlen(Z_raw) > 1e-5 else basis_from_axis(X)[2]
    Y = vcross(Z, X)  # right-handed: X, Y, Z -> X x Y = Z

    sc = max(0.002, vis_scale)
    # Curved cloth sleeve + fluttering corner tail (5x5 grid -> 16 two-sided or outward+inward quads = fixed verts!)
    u0, v0, u1, v1 = UV_SHOP_RAG
    rows, cols = 5, 6
    grid = []
    for r in range(rows):
        tr = r / float(rows - 1)  # along bar: -0.95 .. +0.95
        x_s = (-0.92 + 1.84 * tr) * sc
        row_pts = []
        for c in range(cols):
            tc = c / float(cols - 1)  # wraps 230 deg around chrome bar + hanging rag corner!
            ang = math.radians(-115.0 + 230.0 * tc)
            rad = (0.64 + 0.08 * math.sin(tr * math.pi)) * sc
            # Rag tail corner flares out slightly on last column
            flare = (0.42 * sc * (0.6 + 0.4 * math.sin(wave_ph + tr * 2.5))) if c == cols - 1 else 0.0
            py = (rad * math.sin(ang) + flare * 0.65)
            pz = (rad * math.cos(ang) - flare * 0.75)
            pt = vadd(center_eye, vadd(vmul(X, x_s), vadd(vmul(Y, py), vmul(Z, pz))))
            row_pts.append(pt)
        grid.append(row_pts)

    for r in range(rows - 1):
        for c in range(cols - 1):
            p00 = grid[r][c]
            p10 = grid[r + 1][c]
            p11 = grid[r + 1][c + 1]
            p01 = grid[r][c + 1]
            ua = u0 + (u1 - u0) * (r / float(rows - 1))
            ub = u0 + (u1 - u0) * ((r + 1) / float(rows - 1))
            va = v0 + (v1 - v0) * (c / float(cols - 1))
            vb = v0 + (v1 - v0) * ((c + 1) / float(cols - 1))
            mp.add_quad(p00, p10, p11, p01, (ua, va), (ub, va), (ub, vb), (ua, vb), two_sided=True)
    return mp


def build_arsenal_fx_eye(muzzle_eye, fwd_eye, blast_amp, blast_uv, glint_pos_eye, glint_amp, extra_pos_eye=(8.0, 0.0, -9.0), extra_amp=0.0):
    """Fixed-topology additive FX mesh in eye space:
      1) Muzzle shockwave / supersonic snap torus ring at muzzle_eye
      2) 3D crossed 8-ray Chrome Star-Sparkle Glint right on the polished chrome bullet nose!
      3) Optional secondary spark puff (e.g. sizzling cannon fuse spark or bow/sling flash)
    """
    fx = MeshPart("fx")

    # 1) Launch Shockwave / Air-Snap Ring
    if blast_amp > 0.01:
        r_c = vadd(muzzle_eye, vmul(fwd_eye, 4.2 * (1.0 - blast_amp)))
        r_maj = 1.6 + 3.4 * blast_amp
        r_min = 0.48 * blast_amp
    else:
        r_c = (6.0, -3.0, -9.5)
        r_maj = 0.003
        r_min = 0.001
    fx.add_lathe(
        r_c, fwd_eye,
        [
            (-r_min, max(0.001, r_maj - r_min), 0.05),
            (0.0, r_maj + r_min, 0.50),
            (+r_min, max(0.001, r_maj - r_min), 0.95),
        ],
        segs=18, uv_rect=blast_uv,
    )

    # 2) CoD 'Clean the Bar' Chrome Star-Sparkle Glint (two crossed camera-facing billboard quads at glint_pos_eye!)
    u0, v0, u1, v1 = UV_FX_GLINT
    if glint_amp > 0.01:
        gc = glint_pos_eye
        gs = 1.95 * glint_amp
        # Spin star glint slightly as it pings!
        spin_r = (1.0 - glint_amp) * 0.85
        ca, sa = math.cos(spin_r), math.sin(spin_r)
        Y1 = (0.0, ca * gs, sa * gs)
        Z1 = (0.0, -sa * gs, ca * gs)
        X1 = (gs * 0.75, 0.0, 0.0)
    else:
        gc = (6.0, -3.0, -9.5)
        Y1 = (0.0, 0.002, 0.0)
        Z1 = (0.0, 0.0, 0.002)
        X1 = (0.002, 0.0, 0.0)

    # Billboard quad 1 (screen-aligned YZ plane)
    fx.add_quad(
        vadd(gc, vadd(vmul(Y1, -1), vmul(Z1, -1))),
        vadd(gc, vadd(vmul(Y1, +1), vmul(Z1, -1))),
        vadd(gc, vadd(vmul(Y1, +1), vmul(Z1, +1))),
        vadd(gc, vadd(vmul(Y1, -1), vmul(Z1, +1))),
        (u0, v1), (u1, v1), (u1, v0), (u0, v0),
        nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    # Crossed quad 2 (angled XZ/XY plane so glint sparkles in 360° Orbit too!)
    fx.add_quad(
        vadd(gc, vadd(vmul(X1, -1), vmul(Z1, -1))),
        vadd(gc, vadd(vmul(X1, +1), vmul(Z1, -1))),
        vadd(gc, vadd(vmul(X1, +1), vmul(Z1, +1))),
        vadd(gc, vadd(vmul(X1, -1), vmul(Z1, +1))),
        (u0, v1), (u1, v1), (u1, v0), (u0, v0),
        nrm=(0.0, 1.0, 0.0), two_sided=True,
    )

    # 3) Secondary Spark / Fuse Sizzle Quad
    su0, sv0, su1, sv1 = UV_FX_SMOKE
    if extra_amp > 0.01:
        ec = extra_pos_eye
        es = 0.72 * extra_amp
    else:
        ec = (6.0, -3.0, -9.5)
        es = 0.002
    fx.add_quad(
        (ec[0], ec[1] - es, ec[2] - es),
        (ec[0], ec[1] + es, ec[2] - es),
        (ec[0], ec[1] + es, ec[2] + es),
        (ec[0], ec[1] - es, ec[2] + es),
        (su0, sv1), (su1, sv1), (su1, sv0), (su0, sv0),
        nrm=(-1.0, 0.0, 0.0), two_sided=True,
    )
    return fx


def pack_surfaces_from_frames(arsenal_frames, arsen_ref, ca_frames, ca_ref, wh_frames, wh_ref, hand_frames, hand_ref, fx_frames, fx_ref):
    out = []
    if arsen_ref is not None:
        out.append(dict(
            name="arsenal_rig", shader="progs/mma_arsenal", mat="arsenal",
            tris=arsen_ref.tris, st=arsen_ref.st, frames=arsenal_frames,
        ))
    out.append(dict(
        name="megaman_bar", shader="progs/mmw_chrome_axle", mat="chrome_axle",
        tris=ca_ref.tris, st=ca_ref.st, frames=ca_frames,
    ))
    out.append(dict(
        name="megaman_whl", shader="progs/mma_wheel", mat="wheel",
        tris=wh_ref.tris, st=wh_ref.st, frames=wh_frames,
    ))
    out.append(dict(
        name="ranger_hands", shader="progs/mmw_hand", mat="hand",
        tris=hand_ref.tris, st=hand_ref.st, frames=hand_frames,
    ))
    out.append(dict(
        name="arsenal_fx", shader="progs/mma_fx", mat="fx",
        tris=fx_ref.tris, st=fx_ref.st, frames=fx_frames, unlit=1, additive=1,
    ))
    return out


def make_mm_ref_meshes(mm_parts):
    ca_ref = MeshPart("chrome_axle")
    for k in ("bar_axle", "wheel_hw_l", "wheel_hw_r"):
        ca_ref.append_part(mm_parts[k])
    wh_ref = MeshPart("wheel")
    for k in ("wheel_l", "wheel_r"):
        wh_ref.append_part(mm_parts[k])
    return ca_ref, wh_ref


def idle_bobble_channels(i, amp_scale=1.0):
    """Seamless 16-frame multi-harmonic bobble + 360° wheel spin for Idle (frames 0..15)."""
    ph = 2.0 * math.pi * (i / 16.0)
    return dict(
        spin=i * 22.5,
        # Lively, unmistakable pneumatic bounce + off-balance wheel rock + nose chatter!
        mm_dz=amp_scale * (0.38 * math.sin(ph * 2.0) + 0.14 * math.sin(ph * 4.0 + 0.6)),
        mm_dy=amp_scale * (0.20 * math.cos(ph * 2.0)),
        mm_roll=amp_scale * (5.6 * math.sin(ph * 2.0 + 0.35) + 1.8 * math.cos(ph * 3.0)),
        mm_pitch=amp_scale * (4.4 * math.cos(ph * 2.0 - 0.25) + 1.4 * math.sin(ph * 4.0)),
        mm_yaw=amp_scale * (2.6 * math.sin(ph * 2.0 + 1.1)),
        sway_dx=0.14 * math.sin(ph),
        sway_dy=0.16 * math.cos(ph),
        sway_dz=0.20 * math.sin(ph * 2.0 + 0.4),
        sway_r=0.9 * math.cos(ph),
        sway_p=0.7 * math.sin(ph + 0.4),
        sway_y=0.6 * math.sin(ph),
    )


def inspect_hold_envelope(k):
    """k in 0..23 (24 frames): CoD 'Hold Out' left/right turn & flourish profile."""
    u = k / 23.0
    env = smoothstep(min(1.0, k / 4.2)) * smoothstep(min(1.0, (23 - k) / 4.2))
    # First tilt/roll left (+1) around k=5..10, then roll right (-1) around k=13..18!
    turn_wave = math.sin(u * 2.0 * math.pi)
    flourish = math.exp(-((k - 15.5) ** 2) / 3.8)
    return env, turn_wave, flourish


def inspect_clean_envelope(k):
    """k in 0..27 (28 frames): CoD 'Grab the Bar & Clean It' stroke & star-glint profile!
      - k = 0..4  : Raise weapon to center & bring polishing hand + red shop rag onto bar
      - k = 5..19 : Grip bar & stroke briskly back-and-forth 3.5 cycles along chrome shaft!
      - k = 20..23: Open hand slightly off tip as bright chrome star-glint sparkles!
      - k = 24..27: Smoothly return weapon & hand to idle1!
    """
    present_env = smoothstep(min(1.0, k / 4.2)) * smoothstep(min(1.0, (27 - k) / 3.8))
    on_bar_env = smoothstep(min(1.0, max(0.0, (k - 2.0) / 3.2))) * smoothstep(min(1.0, max(0.0, (23.5 - k) / 2.8)))
    # Polishing stroke s_t in [0..1] along the chrome bar (0 = near T-collar, 1 = near rounded bullet tip)
    if k < 5:
        stroke_t = 0.25 * smoothstep(k / 5.0)
        rub_rock = 0.0
    elif k <= 19:
        cyc = (k - 5.0) / 14.0  # 0..1 -> 3.25 brisk back-and-forth strokes ending near tip!
        stroke_t = 0.52 - 0.44 * math.cos(cyc * math.pi * 6.5)
        rub_rock = math.sin(cyc * math.pi * 6.5)
    else:
        stroke_t = 0.88
        rub_rock = 0.0

    # Admire release (k = 20..24) + Star-Sparkle Glint peaking at k = 21..22 (frame 82-83)!
    admire = smoothstep(min(1.0, max(0.0, (k - 19.2) / 1.8))) * smoothstep(min(1.0, max(0.0, (24.5 - k) / 2.0)))
    glint_amp = math.exp(-((k - 21.3) ** 2) / 1.85)
    if glint_amp < 0.04:
        glint_amp = 0.0
    return present_env, on_bar_env, stroke_t, rub_rock, admire, glint_amp


# ===========================================================================
# WEAPON 1: THE CANNON ('The Broadside Blunder-Cannon') — progs/v_mm_cannon.md3
# ===========================================================================
def _add_arched_barrel_shell(mp, x0, x1, z_c, r_in, r_out, deg0, deg1, segs=12, uv_out=UV_CANNON_IRON, uv_in=UV_DARK_BORE, uv_rim=UV_BRASS_BAND):
    """Builds an arched cylindrical cannon barrel shell segment around (0, z_c) from angle deg0..deg1 in (Y, Z)."""
    angs = [math.radians(deg0 + (deg1 - deg0) * (j / float(segs))) for j in range(segs + 1)]
    u0, v0, u1, v1 = uv_out
    bu0, bv0, bu1, bv1 = uv_in
    ru0, rv0, ru1, rv1 = uv_rim

    for j in range(segs):
        a0, a1 = angs[j], angs[j + 1]
        y0_o, z0_o = r_out * math.cos(a0), z_c + r_out * math.sin(a0)
        y1_o, z1_o = r_out * math.cos(a1), z_c + r_out * math.sin(a1)
        y0_i, z0_i = r_in * math.cos(a0), z_c + r_in * math.sin(a0)
        y1_i, z1_i = r_in * math.cos(a1), z_c + r_in * math.sin(a1)
        am = 0.5 * (a0 + a1)
        n_out = (0.0, math.cos(am), math.sin(am))
        n_in = (0.0, -math.cos(am), -math.sin(am))
        va = v0 + (v1 - v0) * (j / float(segs))
        vb = v0 + (v1 - v0) * ((j + 1) / float(segs))

        # Outer cast-iron / brass wall
        mp.add_quad((x0, y0_o, z0_o), (x1, y0_o, z0_o), (x1, y1_o, z1_o), (x0, y1_o, z1_o), (u0, va), (u1, va), (u1, vb), (u0, vb), nrm=n_out)
        # Inner dark soot bore wall
        mp.add_quad((x0, y1_i, z1_i), (x1, y1_i, z1_i), (x1, y0_i, z0_i), (x0, y0_i, z0_i), (bu0, vb), (bu1, vb), (bu1, va), (bu0, va), nrm=n_in)
        # Front (+X) & Rear (-X) end-wall caps
        mp.add_quad((x1, y0_i, z0_i), (x1, y1_i, z1_i), (x1, y1_o, z1_o), (x1, y0_o, z0_o), (ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1), nrm=(+1.0, 0.0, 0.0))
        mp.add_quad((x0, y0_o, z0_o), (x0, y1_o, z1_o), (x0, y1_i, z1_i), (x0, y0_i, z0_i), (ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1), nrm=(-1.0, 0.0, 0.0))

    # Longitudinal slot-edge flats at deg0 and deg1
    for a_end, sgn_n in ((angs[0], -1.0), (angs[-1], +1.0)):
        yo, zo = r_out * math.cos(a_end), z_c + r_out * math.sin(a_end)
        yi, zi = r_in * math.cos(a_end), z_c + r_in * math.sin(a_end)
        n_edge = (0.0, -sgn_n * math.sin(a_end), sgn_n * math.cos(a_end))
        mp.add_quad((x0, yi, zi), (x1, yi, zi), (x1, yo, zo), (x0, yo, zo), (ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1), nrm=n_edge)


def _build_cannon_static_parts():
    bore_z = 2.22
    barrel = MeshPart("arsenal")

    # 1. Heavy Cast-Iron Closed Breech Drum + Cascabel Ball Knob (x = -1.95 .. 8.25)
    barrel.add_lathe(
        (0.0, 0.0, bore_z), (1.0, 0.0, 0.0),
        [
            (-1.95, 0.00, 0.02),
            (-1.82, 0.68, 0.08),  # cascabel breech ball!
            (-1.35, 0.72, 0.14),
            (-0.98, 0.42, 0.19),  # cascabel neck
            (-0.75, 1.65, 0.24),
            (-0.20, 2.15, 0.30),  # heavy breech ring
            (+3.80, 2.12, 0.62),
            (+8.25, 1.98, 0.96),
            (+8.25, 1.28, 1.00),
        ],
        segs=24, uv_rect=UV_CANNON_IRON,
    )
    # Breech Brass Reinforcing Ring & Touch-Hole Boss
    barrel.add_lathe(
        (1.6, 0.0, bore_z), (1.0, 0.0, 0.0),
        [(0.0, 2.12, 0.1), (0.05, 2.26, 0.2), (1.15, 2.26, 0.8), (1.20, 2.12, 0.9)],
        segs=24, uv_rect=UV_BRASS_BAND,
    )
    # Coiled Sizzling Fuse Cord curving out of top-left breech touch-hole!
    fuse_pts = [
        (2.2, +0.85, bore_z + 2.05),
        (2.0, +1.55, bore_z + 2.65),
        (1.5, +2.05, bore_z + 2.48),
        (1.2, +2.32, bore_z + 2.02),
    ]
    barrel.add_tube(fuse_pts, [0.16, 0.15, 0.14, 0.13], segs=8, uv_rect=(0.77, 0.63, 0.98, 0.73))

    # 2. Slotted Forward Cannon Barrel (x = 8.15 .. 19.65): Upper & Lower Arched Cast-Iron Half-Shells!
    # Leaves wide horizontal side slots at z = bore_z +/- 0.74 so Mega Man's cross-axle & spinning wheels stick right out!
    _add_arched_barrel_shell(barrel, 8.15, 19.65, bore_z, r_in=1.28, r_out=1.96, deg0=23.0, deg1=157.0, segs=12)
    _add_arched_barrel_shell(barrel, 8.15, 19.65, bore_z, r_in=1.28, r_out=1.96, deg0=203.0, deg1=337.0, segs=12)

    # Mid-barrel Riveted Brass Band arcs (x = 12.6 .. 13.5) & Bell-Flared Brass Blunderbuss Muzzle Crown (x = 18.9 .. 20.55)!
    _add_arched_barrel_shell(barrel, 12.60, 13.55, bore_z, r_in=1.95, r_out=2.12, deg0=22.0, deg1=158.0, segs=10, uv_out=UV_BRASS_BAND, uv_in=UV_BRASS_BAND)
    _add_arched_barrel_shell(barrel, 12.60, 13.55, bore_z, r_in=1.95, r_out=2.12, deg0=202.0, deg1=338.0, segs=10, uv_out=UV_BRASS_BAND, uv_in=UV_BRASS_BAND)
    _add_arched_barrel_shell(barrel, 18.85, 20.55, bore_z, r_in=1.32, r_out=2.42, deg0=25.0, deg1=155.0, segs=12, uv_out=UV_BRASS_BAND, uv_in=UV_DARK_BORE)
    _add_arched_barrel_shell(barrel, 18.85, 20.55, bore_z, r_in=1.32, r_out=2.42, deg0=205.0, deg1=335.0, segs=12, uv_out=UV_BRASS_BAND, uv_in=UV_DARK_BORE)

    # Brass Quadrant Rear Sight & Front Muzzle Sight Fin
    barrel.add_chamfer_box(3.8, 4.9, -0.58, +0.58, bore_z + 2.02, bore_z + 2.75, ch=0.06, uv_rect=UV_BRASS_BAND)
    barrel.add_chamfer_box(19.2, 20.3, -0.14, +0.14, bore_z + 2.35, bore_z + 2.95, ch=0.04, uv_rect=UV_BRASS_BAND)

    # 3. Oiled American Walnut Carriage Stock, Brass Trunnion Cheeks, Grip & Foregrip (stationary carriage!)
    stock = MeshPart("arsenal")
    stock.add_chamfer_box(0.4, 15.8, -1.62, +1.62, -1.48, +0.42, ch=0.26, uv_rect=UV_WALNUT_WOOD, side_uv=UV_WALNUT_WOOD, top_uv=UV_WALNUT_WOOD)
    # Brass trunnion side plates + twin recoil spring rods
    for sgn in (-1.0, +1.0):
        stock.add_chamfer_box(4.8, 12.4, sgn * 1.66 - 0.10, sgn * 1.66 + 0.10, -0.65, +1.25, ch=0.04, uv_rect=UV_BRASS_BAND)
        stock.add_lathe(
            (3.2, sgn * 1.28, +0.62), (1.0, 0.0, 0.0),
            [(0.0, 0.34, 0.05), (9.6, 0.34, 0.95)],
            segs=10, uv_rect=UV_COIL_STEEL,
        )
    # Contoured Walnut Pistol Grip + Brass Trigger Guard + Turned-Walnut/Brass Vertical Foregrip
    stock.add_tube([(3.0, 0.0, -1.35), (2.4, 0.0, -3.05), (1.75, 0.0, -4.95)], [(0.92, 0.64), (0.86, 0.58), (0.95, 0.66)], segs=12, uv_rect=UV_WALNUT_WOOD)
    stock.add_tube([(4.85, 0.0, -1.42), (4.65, 0.0, -2.55), (3.40, 0.0, -2.78), (2.65, 0.0, -2.35)], [0.13] * 4, segs=8, uv_rect=UV_BRASS_BAND)
    stock.add_lathe(
        (11.35, +0.35, -1.35), (0.0, 0.0, -1.0),
        [(0.0, 0.68, 0.05), (0.4, 0.52, 0.18), (1.6, 0.64, 0.55), (2.9, 0.56, 0.90), (3.15, 0.72, 0.96), (3.25, 0.0, 1.0)],
        segs=14, uv_rect=UV_BRASS_BAND,
    )

    # 4. Sliding Brass Breech Pusher Ram inside slotted bore (built around ram_x = 0)
    ram = MeshPart("arsenal")
    ram.add_lathe(
        (0.0, 0.0, bore_z), (1.0, 0.0, 0.0),
        [(-5.5, 0.42, 0.05), (-0.9, 0.42, 0.65), (-0.85, 1.12, 0.72), (+0.05, 1.12, 0.96), (+0.05, 0.0, 1.0)],
        segs=16, uv_rect=UV_BRASS_BAND,
    )
    return barrel, stock, ram, bore_z


def build_v1_cannon():
    mm_parts = build_megaman_payload_parts()
    ca_ref, wh_ref = make_mm_ref_meshes(mm_parts)
    barrel_p, stock_p, ram_p, bore_z = _build_cannon_static_parts()

    BASE = (7.10, -5.25, -5.15)
    SCALE = 0.73
    R0, P0, Y0 = -2.8, +2.6, +12.0
    MM_REST_X = 14.85

    arsen_frames, ca_frames, wh_frames, hand_frames, fx_frames = [], [], [], [], []
    arsen_ref = hand_ref = fx_ref = None

    for fi in range(89):
        # Default frame parameters
        rig_dx = rig_dy = rig_dz = 0.0
        rig_r, rig_p, rig_y = R0, P0, Y0
        brl_recoil = 0.0
        mm_x, mm_y, mm_z = MM_REST_X, 0.0, bore_z
        mm_p = mm_r = mm_yw = 0.0
        mm_sc = 1.0
        spin = 0.0
        ram_x = MM_REST_X - 5.02
        trig = 0.0
        blast = 0.0
        fuse_sp = 0.55 + 0.35 * math.sin(fi * 1.7)
        clean_on = 0.0
        stroke_t = 0.0
        rub_rock = 0.0
        admire = 0.0
        glint = 0.0

        if fi < 16:
            # IDLE: Continuous wheel spin + lively cannon-cradle bobble!
            ch = idle_bobble_channels(fi, amp_scale=1.05)
            spin = ch["spin"]
            mm_z += ch["mm_dz"]
            mm_y += ch["mm_dy"] * 0.4
            mm_r = ch["mm_roll"]
            mm_p = ch["mm_pitch"]
            mm_yw = ch["mm_yaw"]
            rig_dx, rig_dy, rig_dz = ch["sway_dx"], ch["sway_dy"], ch["sway_dz"]
            rig_r += ch["sway_r"]
            rig_p += ch["sway_p"]
            rig_y += ch["sway_y"]
        elif fi < 36:
            # FIRE & RELOAD (20 frames: 16..35, launch at 19!)
            k = fi - 16
            if k < 3:
                # 16..18: Fuse flares white-hot, wheels rev hard!
                u = (k + 1) / 3.0
                trig = u
                fuse_sp = 1.35 + 0.45 * u
                spin = k * 52.0
                rig_dx = -0.35 * u
                rig_p += 1.8 * u
                mm_z += 0.25 * math.sin(k * 2.4)
            elif k == 3:
                # 19 (fire4): BOOOOM!! Cannon blasts Mega Man out the flared brass muzzle!
                trig = 1.0
                brl_recoil = -2.35
                rig_dx, rig_dz = -2.40, +0.65
                rig_p += 10.5
                rig_r -= 4.2
                mm_x = 26.8
                spin = 240.0
                ram_x = 19.6
                blast = 1.0
                fuse_sp = 1.6
            elif k < 9:
                # 20..24: Heavy barrel recoil recovery & smoke vent; bore empty
                u = (k - 3) / 5.0
                brl_recoil = -2.35 * (1.0 - smoothstep(u))
                rig_dx = -2.1 * (1.0 - smoothstep(u))
                rig_dz = +0.55 * (1.0 - smoothstep(u))
                rig_p += 9.0 * (1.0 - smoothstep(u))
                mm_sc = 0.001
                mm_x, mm_z = 6.0, -8.0
                ram_x = 19.6 - 10.2 * smoothstep(u)
                blast = max(0.0, 0.62 - 0.28 * (k - 3))
                fuse_sp = 0.25
            else:
                # 25..35: Breech feeds fresh spinning Mega Man forward through the cannon into slotted cradle!
                u = (k - 9) / 10.0
                su = smoothstep(min(1.0, u * 1.18))
                overshoot = 0.35 * math.sin(u * math.pi * 2.0) * (1.0 - u)
                mm_x = 8.8 + (MM_REST_X - 8.8) * su + overshoot
                mm_z = bore_z + 0.28 * math.sin(u * math.pi * 3.0) * (1.0 - u)
                mm_sc = min(1.0, 0.35 + 0.85 * u)
                ram_x = mm_x - 5.02
                spin = (k - 9) * 32.0
                rig_p += -1.6 * math.sin(u * math.pi)
        elif fi == 36:
            # EMPTY1
            mm_sc = 0.001
            mm_x, mm_z = 6.0, -8.0
            fuse_sp = 0.0
        elif fi < 61:
            # COD INSPECT A (37..60): Hold heavy cannon out sideways left & right to admire broadside & spinning wheels!
            k = fi - 37
            env, turn_w, fl = inspect_hold_envelope(k)
            spin = k * 30.0
            mm_z += 0.28 * math.sin(k * 0.8)
            mm_r = 3.8 * math.cos(k * 0.8)
            rig_dx = +0.85 * env
            rig_dy = +2.45 * env - 0.85 * turn_w * env
            rig_dz = +1.35 * env + 0.55 * fl
            rig_r += 36.0 * turn_w * env
            rig_y += (14.0 + 18.0 * turn_w) * env
            rig_p += (5.5 + 4.5 * fl) * env
        else:
            # COD INSPECT B (61..88): Angle cannon across center-screen, push chrome bar clear past muzzle, GRAB BAR w/ red shop rag & CLEAN IT!
            k = fi - 61
            pres, clean_on, stroke_t, rub_rock, admire, glint = inspect_clean_envelope(k)
            spin = k * (720.0 / 28.0)
            # Breech ram pushes Mega Man to the muzzle rim & tilts the chrome bar +42° UP above the brass crown for a hero close-up rag polish!
            mm_x = MM_REST_X + 6.15 * pres + 0.20 * rub_rock * clean_on
            mm_z = bore_z + 0.78 * pres
            ram_x = mm_x - 5.02
            mm_r = 4.5 * rub_rock * clean_on
            mm_p = 42.0 * pres + 2.5 * rub_rock * clean_on
            # Pull muzzle close & low so the upturned chrome shaft, red shop rag & left hand fill center-screen!
            rig_dx = -6.15 * pres
            rig_dy = +2.85 * pres
            rig_dz = -1.25 * pres + 0.14 * rub_rock * clean_on
            rig_y += -2.0 * pres
            rig_p += -6.5 * pres + 1.4 * rub_rock * clean_on
            rig_r += +3.0 * pres

        cur_base = (BASE[0] + rig_dx, BASE[1] + rig_dy, BASE[2] + rig_dz)

        # Transform Mega Man & get exact chrome bar centerline in eye space
        (ca_v, ca_n), (wh_v, wh_n), bar_orig_eye, bar_axis_eye, tip_eye = megaman_eye_frames_and_tip(
            mm_parts, (mm_x, mm_y, mm_z), spin, mm_p, mm_r, mm_yw, mm_sc,
            cur_base, SCALE, rig_r, rig_p, rig_y,
        )

        # Left Foregrip Hand -> smoothly transitions from Brass Foregrip onto Chrome Bar during Inspect Clean!
        fg_palm_eye = rig_pt_to_eye((11.35, +0.55, -2.75), cur_base, SCALE, rig_r, rig_p, rig_y)
        fg_fwd_eye = rig_nrm_to_eye((+0.35, -0.84, +0.42), rig_r, rig_p, rig_y)
        fg_up_eye = rig_nrm_to_eye((-0.18, +0.42, +0.89), rig_r, rig_p, rig_y)

        # Polishing pose along the exposed chrome bar shaft (s from 1.65 to 4.65 completely clear of the brass muzzle!)
        s_along = 1.65 + 3.00 * stroke_t
        rub_center_eye = vadd(bar_orig_eye, vmul(bar_axis_eye, s_along * SCALE))
        pol_palm_eye = vadd(rub_center_eye, vadd(vmul((0.0, 1.0, 0.0), 0.78 + 1.15 * admire), vmul((0.0, 0.0, -1.0), 0.68 - 0.30 * admire)))
        pol_fwd_eye = vnorm(vadd(vmul(bar_axis_eye, 0.25), (0.20, -0.82, +0.48)))
        pol_up_eye = vnorm((-0.35, +0.45, +0.82))

        lh_palm = vlerp(fg_palm_eye, pol_palm_eye, clean_on)
        lh_fwd = vnorm(vlerp(fg_fwd_eye, pol_fwd_eye, clean_on))
        lh_up = vnorm(vlerp(fg_up_eye, pol_up_eye, clean_on))
        c_curl = 0.85 - 0.52 * admire
        lh_curls = (
            0.82 * (1.0 - clean_on) + c_curl * clean_on,
            0.86 * (1.0 - clean_on) + (c_curl + 0.03) * clean_on,
            0.88 * (1.0 - clean_on) + (c_curl + 0.05) * clean_on,
            0.85 * (1.0 - clean_on) + c_curl * clean_on,
        )

        lh = build_articulated_ranger_hand(
            palm_center=lh_palm, fwd_dir=lh_fwd, up_dir=lh_up,
            side_sign=+1.0, finger_curls=lh_curls, thumb_curl=0.74 - 0.35 * admire * clean_on,
            thumb_abd=38.0, hand_scale=0.62, forearm_len=8.5,
            forearm_dir=vnorm((-0.52, +0.52, -0.68)),
        )
        rh = build_articulated_ranger_hand(
            palm_center=rig_pt_to_eye((2.45, -0.78, -2.95), cur_base, SCALE, rig_r, rig_p, rig_y),
            fwd_dir=rig_nrm_to_eye((+0.78, +0.46, +0.42), rig_r, rig_p, rig_y),
            up_dir=rig_nrm_to_eye((-0.22, -0.52, +0.82), rig_r, rig_p, rig_y),
            side_sign=-1.0, finger_curls=(0.48 + 0.38 * trig, 0.86, 0.88, 0.90),
            thumb_curl=0.78, thumb_abd=34.0, hand_scale=0.64, forearm_len=8.0,
            forearm_dir=vnorm((-0.55, -0.48, -0.68)),
        )

        # Shop Polishing Rag (wraps camera-facing side of chrome bar during clean_on, tucked inside left cuff otherwise!)
        rag_pos = vlerp(vadd(lh_palm, (-0.8, +0.4, -0.6)), rub_center_eye, clean_on)
        rag_mp = build_shop_rag_part(rag_pos, bar_axis_eye, (-0.62, +0.35, +0.70), vis_scale=1.12 * clean_on * (1.0 - 0.55 * admire), wave_ph=fi * 0.9)

        # Assemble Arsenal Surface (barrel + stock + ram + rag)
        bv, bn = transform_mesh_to_eye(barrel_p, cur_base, SCALE, rig_r, rig_p, rig_y, local_off=(brl_recoil, 0.0, 0.0))
        sv, sn = transform_mesh_to_eye(stock_p, cur_base, SCALE, rig_r, rig_p, rig_y)
        rv, rn = transform_mesh_to_eye(ram_p, cur_base, SCALE, rig_r, rig_p, rig_y, local_off=(ram_x + brl_recoil, 0.0, 0.0))

        arsen_frames.append((bv + sv + rv + rag_mp.verts, bn + sn + rn + rag_mp.norms))
        ca_frames.append((ca_v, ca_n))
        wh_frames.append((wh_v, wh_n))
        hand_frames.append((lh.verts + rh.verts, lh.norms + rh.norms))

        muz_eye = rig_pt_to_eye((21.2, 0.0, bore_z), cur_base, SCALE, rig_r, rig_p, rig_y)
        fwd_eye = rig_nrm_to_eye((1.0, 0.0, 0.0), rig_r, rig_p, rig_y)
        fuse_tip_eye = rig_pt_to_eye((1.2 + brl_recoil, +2.32, bore_z + 2.02), cur_base, SCALE, rig_r, rig_p, rig_y)
        fx_mp = build_arsenal_fx_eye(muz_eye, fwd_eye, blast, UV_FX_BLAST, tip_eye, glint, extra_pos_eye=fuse_tip_eye, extra_amp=fuse_sp)
        fx_frames.append((fx_mp.verts, fx_mp.norms))

        if fi == 0:
            arsen_ref = MeshPart("arsenal")
            for p_sub in (barrel_p, stock_p, ram_p, rag_mp):
                arsen_ref.append_part(p_sub)
            hand_ref = MeshPart("hand")
            hand_ref.append_part(lh)
            hand_ref.append_part(rh)
            fx_ref = fx_mp
            muzzle_out = [round(c, 2) for c in muz_eye]

    surfs = pack_surfaces_from_frames(arsen_frames, arsen_ref, ca_frames, ca_ref, wh_frames, wh_ref, hand_frames, hand_ref, fx_frames, fx_ref)
    return surfs, muzzle_out


# ===========================================================================
# WEAPON 2: THE SLINGSHOT ('The Wrist-Rocket Y-Slinger') — progs/v_mm_slingshot.md3
# ===========================================================================
def _build_slingshot_frame_mesh(pouch_c, fork_l, fork_r, whip_wave=0.0):
    """Builds the sculpted Walnut Y-Fork + Wrist-Brace + Dynamic 4-Strand Surgical Latex Bands + Stitched Pouch!"""
    mp = MeshPart("arsenal")

    # 1. Contoured Paracord/Leather Grip + Carved American Walnut Y-Fork Uprights
    mp.add_tube(
        [(13.8, 0.0, -4.85), (14.0, 0.0, -2.85), (14.2, 0.0, -0.85), (14.3, 0.0, +0.35)],
        [(0.86, 0.64), (0.82, 0.60), (0.84, 0.62), (0.96, 0.72)],
        segs=12, uv_rect=UV_POUCH_LEATHER,
    )
    # Brass collar ring at Y-junction + padded walnut saddle rest between forks
    mp.add_lathe((14.3, 0.0, +0.35), (0.0, 0.0, 1.0), [(0.0, 0.98, 0.1), (0.45, 1.06, 0.9)], segs=14, uv_rect=UV_BRASS_BAND)

    # Left & Right Sweeping Carved Walnut Y-Fork Arms + Grooved Brass Band-Tie Spools
    for sgn, f_tip in ((+1.0, fork_l), (-1.0, fork_r)):
        arm_pts = [
            (14.35, sgn * 0.35, +0.62),
            (14.55, sgn * 1.65, +1.55),
            (14.80, sgn * 2.95, +2.85),
            (f_tip[0], f_tip[1], f_tip[2] - 0.45),
            f_tip,
        ]
        mp.add_tube(arm_pts, [0.58, 0.52, 0.46, 0.42, 0.48], segs=10, uv_rect=UV_WALNUT_WOOD)
        # Brass band-anchor spool cap at fork tip
        mp.add_lathe(f_tip, (0.0, 0.0, 1.0), [(-0.35, 0.52, 0.1), (+0.28, 0.54, 0.85), (+0.32, 0.0, 1.0)], segs=12, uv_rect=UV_BRASS_BAND)

    # Folding Tubular Steel Wrist-Brace + Padded Saddle-Leather Forearm Cuff
    for sgn in (-1.0, +1.0):
        brace_pts = [
            (14.0, sgn * 0.62, -1.15),
            (11.4, +0.35 + sgn * 0.92, -2.25),
            (8.2,  +0.95 + sgn * 1.08, -3.55),
        ]
        mp.add_tube(brace_pts, [0.16, 0.15, 0.15], segs=8, uv_rect=UV_COIL_STEEL)
    mp.add_tube(
        [(8.3, +2.05, -3.35), (8.2, +0.95, -2.55), (8.1, -0.15, -3.45)],
        [0.32, 0.36, 0.32], segs=8, uv_rect=UV_POUCH_LEATHER,
    )

    # 2. Stitched Saddle-Leather Ammo Pouch cupping Mega Man's rear rubber cap
    px, py, pz = pouch_c
    pouch_pts = [
        (px + 0.65, py + 1.05, pz),
        (px - 0.18, py + 0.58, pz),
        (px - 0.42, py,        pz),
        (px - 0.18, py - 0.58, pz),
        (px + 0.65, py - 1.05, pz),
    ]
    mp.add_tube(pouch_pts, [(0.16, 0.62), (0.18, 0.78), (0.20, 0.84), (0.18, 0.78), (0.16, 0.62)], segs=8, uv_rect=UV_POUCH_LEATHER)

    # 3. Four Dynamic Golden-Amber Surgical Latex Elastic Tubes (2 per fork horn -> real Poisson thinning under draw!)
    for sgn, f_tip in ((+1.0, fork_l), (-1.0, fork_r)):
        for z_off in (+0.20, -0.22):
            p_start = (f_tip[0], f_tip[1], f_tip[2] + z_off)
            p_end = (px + 0.55, py + sgn * 0.98, pz + z_off * 1.2)
            span = max(1.5, vlen(vsub(p_end, p_start)))
            # Thin realistically as stretched from rest length 5.5 -> 11.0!
            r_band = max(0.095, min(0.22, 0.185 * math.sqrt(5.8 / span)))
            b_pts = []
            for s in range(5):
                t = s / 4.0
                mid = vlerp(p_start, p_end, t)
                arc_sag = math.sin(t * math.pi)
                # Whip flutter right after snap release!
                wy = sgn * 0.55 * whip_wave * math.sin(t * math.pi * 2.0)
                wz = 0.45 * whip_wave * arc_sag - (0.35 * arc_sag if span < 4.5 else 0.0)
                b_pts.append((mid[0], mid[1] + wy, mid[2] + wz))
            mp.add_tube(b_pts, [r_band * 1.12, r_band, r_band * 0.96, r_band, r_band * 1.08], segs=8, uv_rect=UV_LATEX_AMBER)

    return mp


def build_v2_slingshot():
    mm_parts = build_megaman_payload_parts()
    ca_ref, wh_ref = make_mm_ref_meshes(mm_parts)

    BASE = (6.50, -3.75, -4.55)
    SCALE = 0.76
    R0, P0, Y0 = -2.2, +2.0, +9.8
    FORK_L = (15.05, +3.65, +4.45)
    FORK_R = (15.05, -3.65, +4.45)
    MM_REST = (10.15, 0.0, +2.65)

    arsen_frames, ca_frames, wh_frames, hand_frames, fx_frames = [], [], [], [], []
    arsen_ref = hand_ref = fx_ref = None

    for fi in range(89):
        rig_dx = rig_dy = rig_dz = 0.0
        rig_r, rig_p, rig_y = R0, P0, Y0
        mm_x, mm_y, mm_z = MM_REST
        mm_p = mm_r = mm_yw = 0.0
        mm_sc = 1.0
        spin = 0.0
        pouch_c = (mm_x - 4.75, 0.0, mm_z)
        whip = 0.0
        pinch_open = 0.0
        blast = 0.0
        clean_on = 0.0
        stroke_t = 0.0
        rub_rock = 0.0
        admire = 0.0
        glint = 0.0

        if fi < 16:
            # IDLE: Suspended in taut elastic sling — wheels spin 360° & Mega Man bobbles springily on the rubber bands!
            ch = idle_bobble_channels(fi, amp_scale=1.22)
            spin = ch["spin"]
            mm_z += ch["mm_dz"]
            mm_y += ch["mm_dy"]
            mm_r = ch["mm_roll"]
            mm_p = ch["mm_pitch"]
            mm_yw = ch["mm_yaw"]
            pouch_c = (mm_x - 4.75, mm_y * 0.6, mm_z - 0.08 * mm_p)
            rig_dx, rig_dy, rig_dz = ch["sway_dx"], ch["sway_dy"], ch["sway_dz"]
            rig_r += ch["sway_r"]
            rig_p += ch["sway_p"]
            rig_y += ch["sway_y"]
        elif fi < 36:
            k = fi - 16
            if k < 3:
                # 16..18: FULL WRIST-ROCKET DRAW! Right hand hauls pouch & spinning Mega Man deep back to x=5.8!
                u = smoothstep((k + 1) / 3.0)
                mm_x = MM_REST[0] - 4.35 * u
                mm_z = MM_REST[2] - 0.35 * u
                pouch_c = (mm_x - 4.75, 0.0, mm_z)
                spin = (k + 1) * 58.0
                rig_dx = +0.55 * u  # left arm braces Y-fork forward against the heavy rubber draw!
                rig_p += +2.4 * u
            elif k == 3:
                # 19 (fire4): SNAP RELEASE!! Pouch & 4 latex bands whip past Y-fork as Mega Man rockets through!
                mm_x = 24.5
                mm_z = 3.15
                spin = 265.0
                pouch_c = (18.4, 0.0, 4.15)
                whip = +1.0
                pinch_open = 1.0
                blast = 1.0
                rig_dx, rig_dz = -1.15, +0.42
                rig_p += +5.2
            elif k < 9:
                # 20..24: Elastic bands snap & oscillate wildly back to slack between forks!
                u = (k - 3) / 5.0
                mm_sc = 0.001
                mm_x, mm_z = 8.0, -9.0
                osc = math.cos(u * math.pi * 3.0) * (1.0 - u)
                pouch_c = (14.4 + 3.2 * osc, 0.0, 3.6 + 0.5 * osc)
                whip = osc * 1.15
                pinch_open = 1.0 - 0.4 * u
                blast = max(0.0, 0.52 - 0.24 * (k - 3))
                rig_dx = -0.85 * (1.0 - smoothstep(u))
            else:
                # 25..35: Right hand brings fresh spinning Mega Man up, seats rear cap in leather pouch & draws back!
                u = (k - 9) / 10.0
                su = smoothstep(u)
                mm_x = 13.4 - (13.4 - MM_REST[0]) * su
                mm_z = -0.8 + (MM_REST[2] - (-0.8)) * smoothstep(min(1.0, u * 1.35))
                mm_z += 0.32 * math.sin(u * math.pi * 2.0) * (1.0 - u)
                mm_sc = min(1.0, 0.35 + 0.90 * u)
                pouch_c = (mm_x - 4.75, 0.0, mm_z)
                spin = (k - 9) * 34.0
                pinch_open = max(0.0, 0.65 * (1.0 - u * 1.6))
        elif fi == 36:
            mm_sc = 0.001
            mm_x, mm_z = 8.0, -9.0
            pouch_c = (13.8, 0.0, 2.85)
            pinch_open = 0.85
        elif fi < 61:
            # COD INSPECT A (37..60): Hold Y-fork slingshot out left/right + elastic tug test!
            k = fi - 37
            env, turn_w, fl = inspect_hold_envelope(k)
            spin = k * 30.0
            tug = 1.65 * fl
            mm_x = MM_REST[0] - tug
            mm_z = MM_REST[2] + 0.30 * math.sin(k * 0.9)
            mm_r = 4.8 * math.cos(k * 0.9)
            pouch_c = (mm_x - 4.75, 0.0, mm_z)
            rig_dx = +0.65 * env
            rig_dy = +1.95 * env - 0.90 * turn_w * env
            rig_dz = +1.05 * env
            rig_r += 42.0 * turn_w * env
            rig_y += (12.0 + 22.0 * turn_w) * env
            rig_p += 5.0 * env
        else:
            # COD INSPECT B (61..88): Ease pouch into Y-fork saddle, tilt chrome bar up close; Right Hand + Red Rag CLEANS BAR!
            k = fi - 61
            pres, clean_on, stroke_t, rub_rock, admire, glint = inspect_clean_envelope(k)
            spin = k * (720.0 / 28.0)
            mm_x = MM_REST[0] + 3.65 * pres + 0.18 * rub_rock * clean_on
            mm_z = MM_REST[2] + 0.65 * pres
            mm_r = 4.6 * rub_rock * clean_on
            mm_p = 14.0 * pres + 2.5 * rub_rock * clean_on
            pouch_c = (mm_x - 4.75, 0.0, mm_z)
            rig_dx = -2.35 * pres
            rig_dy = +2.35 * pres
            rig_dz = -0.35 * pres
            rig_y += +14.0 * pres
            rig_p += +14.5 * pres
            rig_r += -6.0 * pres

        cur_base = (BASE[0] + rig_dx, BASE[1] + rig_dy, BASE[2] + rig_dz)
        sling_local = _build_slingshot_frame_mesh(pouch_c, FORK_L, FORK_R, whip_wave=whip)

        (ca_v, ca_n), (wh_v, wh_n), bar_orig_eye, bar_axis_eye, tip_eye = megaman_eye_frames_and_tip(
            mm_parts, (mm_x, mm_y, mm_z), spin, mm_p, mm_r, mm_yw, mm_sc,
            cur_base, SCALE, rig_r, rig_p, rig_y,
        )

        # Left Hand grips Slingshot Handle (forearm stays anchored toward bottom-left of screen!)
        lh = build_articulated_ranger_hand(
            palm_center=rig_pt_to_eye((14.1, +0.62, -2.35), cur_base, SCALE, rig_r, rig_p, rig_y),
            fwd_dir=rig_nrm_to_eye((+0.78, -0.58, +0.22), rig_r, rig_p, rig_y),
            up_dir=rig_nrm_to_eye((-0.18, +0.16, +0.97), rig_r, rig_p, rig_y),
            side_sign=+1.0, finger_curls=(0.86, 0.88, 0.90, 0.90),
            thumb_curl=0.78, thumb_abd=36.0, hand_scale=0.62, forearm_len=9.0,
            forearm_dir=vnorm((-0.58, +0.42, -0.70)),
        )

        # Right Hand: Pinches leather pouch normally -> cradles underneath w/ red shop rag on top to polish chrome bar!
        rh_pinch_loc = (
            (pouch_c[0] - 1.55, pouch_c[1] - 0.65, pouch_c[2] - 0.45)
            if pinch_open < 0.5
            else (7.2, -1.8, +0.2)
        )
        pouch_palm_eye = rig_pt_to_eye(rh_pinch_loc, cur_base, SCALE, rig_r, rig_p, rig_y)
        pouch_fwd_eye = rig_nrm_to_eye((+0.78, +0.52, +0.34), rig_r, rig_p, rig_y)
        pouch_up_eye = rig_nrm_to_eye((-0.26, -0.35, +0.90), rig_r, rig_p, rig_y)

        s_along = 1.15 + 3.25 * stroke_t
        rub_center_eye = vadd(bar_orig_eye, vmul(bar_axis_eye, s_along * SCALE))
        pol_palm_eye = vadd(rub_center_eye, (+0.32, -0.82 - 1.10 * admire, -0.76 + 0.25 * admire))
        pol_fwd_eye = vnorm(vadd(vmul(bar_axis_eye, 0.20), (+0.22, +0.72, +0.62)))
        pol_up_eye = vnorm((-0.28, -0.52, +0.81))

        rh_palm = vlerp(pouch_palm_eye, pol_palm_eye, clean_on)
        rh_fwd = vnorm(vlerp(pouch_fwd_eye, pol_fwd_eye, clean_on))
        rh_up = vnorm(vlerp(pouch_up_eye, pol_up_eye, clean_on))
        base_c = 0.84 * (1.0 - 0.72 * pinch_open)
        pol_c = 0.86 - 0.52 * admire
        rh_curls = tuple(base_c * (1.0 - clean_on) + pol_c * clean_on for _ in range(4))

        rh = build_articulated_ranger_hand(
            palm_center=rh_palm, fwd_dir=rh_fwd, up_dir=rh_up,
            side_sign=-1.0, finger_curls=rh_curls,
            thumb_curl=(0.76 * (1.0 - 0.65 * pinch_open)) * (1.0 - clean_on) + (0.76 - 0.35 * admire) * clean_on,
            thumb_abd=34.0, hand_scale=0.62, forearm_len=8.5,
            forearm_dir=vnorm((-0.42, -0.58, -0.70)),
        )

        rag_pos = vlerp(vadd(rh_palm, (-0.8, -0.4, -0.6)), rub_center_eye, clean_on)
        rag_mp = build_shop_rag_part(rag_pos, bar_axis_eye, (-0.65, +0.28, +0.70), vis_scale=1.12 * clean_on * (1.0 - 0.55 * admire), wave_ph=fi * 0.95)

        sv, sn = transform_mesh_to_eye(sling_local, cur_base, SCALE, rig_r, rig_p, rig_y)
        arsen_frames.append((sv + rag_mp.verts, sn + rag_mp.norms))
        ca_frames.append((ca_v, ca_n))
        wh_frames.append((wh_v, wh_n))
        hand_frames.append((lh.verts + rh.verts, lh.norms + rh.norms))

        muz_eye = rig_pt_to_eye((16.5, 0.0, 3.65), cur_base, SCALE, rig_r, rig_p, rig_y)
        fwd_eye = rig_nrm_to_eye((1.0, 0.0, 0.0), rig_r, rig_p, rig_y)
        fx_mp = build_arsenal_fx_eye(muz_eye, fwd_eye, blast, UV_FX_SNAP, tip_eye, glint)
        fx_frames.append((fx_mp.verts, fx_mp.norms))

        if fi == 0:
            arsen_ref = MeshPart("arsenal")
            arsen_ref.append_part(sling_local)
            arsen_ref.append_part(rag_mp)
            hand_ref = MeshPart("hand")
            hand_ref.append_part(lh)
            hand_ref.append_part(rh)
            fx_ref = fx_mp
            muzzle_out = [round(c, 2) for c in muz_eye]

    surfs = pack_surfaces_from_frames(arsen_frames, arsen_ref, ca_frames, ca_ref, wh_frames, wh_ref, hand_frames, hand_ref, fx_frames, fx_ref)
    return surfs, muzzle_out


# ===========================================================================
# WEAPON 3: THE BOW ('The Recurve Mega-Bow') — progs/v_mm_bow.md3
# ===========================================================================
def _build_bow_frame_mesh(draw_t, string_vib, arrow_show, mm_pos, mm_pitch):
    """Builds Carbon/Alloy Riser + 3-Pin Fiber Sight + Dynamic Flexing Recurve Limbs + Rotating Cams +
    Vibrating Bowstring + 3-Vane Fletched Arrow Nock Shaft attached to Mega Man's rear cap!
    """
    mp = MeshPart("arsenal")
    riser_x = 12.85

    # 1. Sculpted Carbon & Anodized Alloy Bow Riser + Cutaway Sight Window + Forward Stabilizer
    riser_pts = [
        (riser_x - 0.15, 0.0, -4.65),
        (riser_x + 0.15, -0.15, -2.55),  # ergonomic grip curve
        (riser_x + 0.25, -0.35, -0.45),
        (riser_x + 0.30, -0.55, +1.55),  # cutaway arrow-shelf window (leaves +Y=+0.45 clear!)
        (riser_x + 0.10, -0.10, +3.45),
        (riser_x - 0.15, 0.0, +4.65),
    ]
    mp.add_tube(riser_pts, [(0.52, 0.42), (0.56, 0.44), (0.58, 0.46), (0.52, 0.40), (0.56, 0.44), (0.52, 0.42)], segs=10, uv_rect=UV_CARBON_LIMB)

    # Twin-Roller Brass Arrow Rest at (riser_x + 0.35, +0.42, +0.42) + 3-Pin Glowing Fiber Sight Ring!
    mp.add_chamfer_box(riser_x - 0.15, riser_x + 0.75, -0.35, +0.85, +0.02, +0.28, ch=0.04, uv_rect=UV_BRASS_BAND)
    mp.add_lathe(
        (riser_x + 0.55, +1.28, +1.85), (1.0, 0.0, 0.0),
        [(0.0, 0.68, 0.1), (0.0, 0.82, 0.2), (0.45, 0.82, 0.8), (0.45, 0.68, 0.9)],
        segs=16, uv_rect=UV_BRASS_BAND,
    )
    # Glowing neon sight pin inside sight ring
    mp.add_tube([(riser_x + 0.75, +1.28, +1.18), (riser_x + 0.75, +1.28, +1.85)], [0.06, 0.09], segs=6, uv_rect=(0.78, 0.53, 0.97, 0.62))
    # Forward Carbon Stabilizer Rod + Brass Counterweight
    mp.add_lathe(
        (riser_x + 0.25, 0.0, -2.55), (1.0, 0.0, 0.0),
        [(0.0, 0.24, 0.05), (3.4, 0.20, 0.75), (3.5, 0.48, 0.82), (4.2, 0.48, 0.96), (4.25, 0.0, 1.0)],
        segs=12, uv_rect=UV_BRASS_BAND,
    )

    # 2. Dynamic Flexing Upper & Lower Recurve Carbon Limbs + Rotating Eccentric Pulley Cams!
    cam_tips = []
    for sgn in (+1.0, -1.0):
        limb_pts = []
        for s in range(6):
            t = s / 5.0
            # Recurve S-curve that bends backward (-X) and inward (-|Z|) under draw_t!
            bx = riser_x - 0.15 - (3.15 + 3.10 * draw_t) * (t ** 1.45) + 0.75 * math.sin(t * math.pi) * (1.0 - 0.45 * draw_t)
            bz = sgn * (4.55 + (5.95 - 0.88 * draw_t) * (t ** 0.92))
            limb_pts.append((bx, 0.0, bz))
        mp.add_tube(
            limb_pts,
            [(0.18, 0.56), (0.16, 0.52), (0.15, 0.48), (0.14, 0.44), (0.13, 0.40), (0.15, 0.36)],
            segs=8, uv_rect=UV_CARBON_LIMB,
        )
        c_tip = limb_pts[-1]
        cam_tips.append(c_tip)
        # Eccentric Compound Pulley Cam at limb tip (rotates as string draws!)
        cam_ang = sgn * draw_t * 145.0
        ecc_off = rot_y((0.28, 0.0, 0.0), cam_ang)
        cam_c = vadd(c_tip, ecc_off)
        mp.add_lathe(
            cam_c, (0.0, 1.0, 0.0),
            [(-0.18, 0.0, 0.0), (-0.18, 1.28, 0.2), (+0.18, 1.28, 0.8), (+0.18, 0.0, 1.0)],
            segs=14, uv_rect=UV_BRASS_BAND,
        )

    # 3. Dynamic Braided Bowstring (Upper Cam -> Nock Point -> Lower Cam) + Buss Cable!
    nock_x = 7.45 - 3.25 * draw_t + string_vib
    nock_p = (nock_x, +0.42, +0.55)
    mp.add_tube([cam_tips[0], nock_p, cam_tips[1]], [0.075, 0.085, 0.075], segs=6, uv_rect=(0.52, 0.52, 0.74, 0.62))
    mp.add_tube([(cam_tips[0][0] + 0.45, -0.22, cam_tips[0][2]), (cam_tips[1][0] + 0.45, -0.22, cam_tips[1][2])], [0.05, 0.05], segs=6, uv_rect=(0.52, 0.52, 0.74, 0.62))

    # 4. 3-Vane Fletched Carbon Arrow Nock-Tail mated into Mega Man's rear cap (turns Mega Man into a Mega-Arrow!)
    asc = 1.0 if arrow_show else 0.002
    a_orig = mm_pos if arrow_show else (riser_x, 0.0, -9.0)
    a_dir = rot_y((-1.0, 0.0, 0.0), mm_pitch)  # points backward from Mega Man center toward bowstring nock!
    tail_start = vadd(a_orig, vmul(a_dir, 4.75 * asc))
    tail_end = vadd(a_orig, vmul(a_dir, 8.65 * asc))
    mp.add_tube([tail_start, tail_end], [0.24 * asc, 0.20 * asc], segs=8, uv_rect=UV_CARBON_LIMB)
    # 3 Blazing Orange-Red Arrow Fletching Vanes spaced 120° around shaft!
    _, Y_a, Z_a = basis_from_axis(a_dir)
    vu0, vv0, vu1, vv1 = (0.53, 0.64, 0.73, 0.73)
    for vi in range(3):
        va = math.radians(vi * 120.0 + 30.0)
        v_out = vadd(vmul(Y_a, math.cos(va)), vmul(Z_a, math.sin(va)))
        p0 = vadd(a_orig, vadd(vmul(a_dir, 6.05 * asc), vmul(v_out, 0.18 * asc)))
        p1 = vadd(a_orig, vadd(vmul(a_dir, 8.35 * asc), vmul(v_out, 0.18 * asc)))
        p2 = vadd(a_orig, vadd(vmul(a_dir, 8.15 * asc), vmul(v_out, 0.88 * asc)))
        p3 = vadd(a_orig, vadd(vmul(a_dir, 6.55 * asc), vmul(v_out, 0.62 * asc)))
        mp.add_quad(p0, p1, p2, p3, (vu0, vv1), (vu1, vv1), (vu1, vv0), (vu0, vv0), two_sided=True)

    return mp, nock_p


def build_v3_bow():
    mm_parts = build_megaman_payload_parts()
    ca_ref, wh_ref = make_mm_ref_meshes(mm_parts)

    # Classic heroic FPS Bow cant (+22° roll tilts upper limb gracefully top-left!)
    BASE = (6.35, -3.15, -3.15)
    SCALE = 0.72
    R0, P0, Y0 = +22.0, +1.8, +8.5
    MM_BRACE_X = 16.05
    MM_Y = +0.42
    MM_Z = +0.55

    arsen_frames, ca_frames, wh_frames, hand_frames, fx_frames = [], [], [], [], []
    arsen_ref = hand_ref = fx_ref = None

    for fi in range(89):
        rig_dx = rig_dy = rig_dz = 0.0
        rig_r, rig_p, rig_y = R0, P0, Y0
        draw_t = 0.0
        str_vib = 0.0
        mm_x, mm_y, mm_z = MM_BRACE_X, MM_Y, MM_Z
        mm_p = mm_r = mm_yw = 0.0
        mm_sc = 1.0
        arrow_show = True
        spin = 0.0
        blast = 0.0
        str_release = 0.0
        pluck_off = (0.0, 0.0, 0.0)
        clean_on = 0.0
        stroke_t = 0.0
        rub_rock = 0.0
        admire = 0.0
        glint = 0.0

        if fi < 16:
            # IDLE: Nocked at brace height — both wheels spin 360° & Mega-Arrow bobbles/chatters on the roller rest!
            ch = idle_bobble_channels(fi, amp_scale=1.12)
            spin = ch["spin"]
            mm_z += ch["mm_dz"] * 0.85
            mm_r = ch["mm_roll"]
            mm_p = ch["mm_pitch"] * 0.75
            mm_yw = ch["mm_yaw"] * 0.75
            str_vib = 0.06 * math.sin(fi * math.pi * 0.5)
            rig_dx, rig_dy, rig_dz = ch["sway_dx"], ch["sway_dy"], ch["sway_dz"]
            rig_r += ch["sway_r"]
            rig_p += ch["sway_p"]
            rig_y += ch["sway_y"]
        elif fi < 36:
            k = fi - 16
            if k < 3:
                # 16..18: FULL COMPOUND ARCHERY DRAW! Limbs bend back, cams spin, Mega-Arrow pulls back to roller rest!
                draw_t = smoothstep((k + 1) / 3.0)
                mm_x = MM_BRACE_X - 2.35 * draw_t
                spin = (k + 1) * 60.0
                rig_dx = +0.55 * draw_t
                rig_r -= 4.0 * draw_t  # uprights slightly into precision archer sight picture!
            elif k == 3:
                # 19 (fire4): TWAAANG!! Bowstring & limbs snap forward launching Mega-Arrow downrange!
                draw_t = -0.14  # forward limb snap overshoot!
                str_vib = +0.95
                mm_x = 25.5
                spin = 270.0
                str_release = 1.0
                blast = 1.0
                rig_dx, rig_dz = -0.95, +0.35
                rig_p += 4.2
            elif k < 9:
                # 20..24: High-frequency bowstring vibration dampens out; bow un-nocked
                u = (k - 3) / 5.0
                draw_t = -0.10 * math.cos(u * math.pi * 3.0) * (1.0 - u)
                str_vib = 0.82 * math.sin(u * math.pi * 5.0) * (1.0 - u)
                mm_sc = 0.001
                arrow_show = False
                mm_x, mm_z = 9.0, -9.0
                str_release = 1.0 - 0.5 * u
                blast = max(0.0, 0.48 - 0.22 * (k - 3))
            else:
                # 25..35: Right hand pulls fresh spinning Mega-Arrow up from quiver, seats onto rest & clicks onto string!
                u = (k - 9) / 10.0
                su = smoothstep(min(1.0, u * 1.25))
                mm_x = 12.2 + (MM_BRACE_X - 12.2) * su
                mm_z = -3.2 + (MM_Z - (-3.2)) * su + 0.25 * math.sin(u * math.pi * 2.0) * (1.0 - u)
                mm_p = -14.0 * (1.0 - su)
                mm_sc = min(1.0, 0.35 + 0.90 * u)
                spin = (k - 9) * 34.0
                str_release = max(0.0, 0.55 * (1.0 - u * 1.6))
        elif fi == 36:
            mm_sc = 0.001
            arrow_show = False
            mm_x, mm_z = 9.0, -9.0
            str_release = 0.8
        elif fi < 61:
            # COD INSPECT A (37..60): Cant bow smoothly left/right across viewport to admire cams & PLUCK BOWSTRING!
            k = fi - 37
            env, turn_w, fl = inspect_hold_envelope(k)
            spin = k * 30.0
            mm_z += 0.24 * math.sin(k * 0.85)
            mm_r = 4.0 * math.cos(k * 0.85)
            # Pluck string at k=13..18 -> string vibrates visibly!
            if k >= 13:
                str_vib = 0.68 * math.sin((k - 13) * 2.4) * math.exp(-(k - 13) * 0.32)
            pluck_off = (-1.15 * fl, -0.55 * fl, -0.25 * fl)
            rig_dx = +0.55 * env
            rig_dy = +1.75 * env - 0.70 * turn_w * env
            rig_dz = +0.85 * env
            rig_r += +22.0 * env + 20.0 * turn_w * env  # clean CoD Combat Bow cant without flipping elbow into view!
            rig_y += (14.0 + 18.0 * turn_w) * env
            rig_p += +6.5 * env
        else:
            # COD INSPECT B (61..88): Pull bow closer, pitch warhead up, Right Hand + Red Shop Rag CLEANS CHROME BAR!
            k = fi - 61
            pres, clean_on, stroke_t, rub_rock, admire, glint = inspect_clean_envelope(k)
            spin = k * (720.0 / 28.0)
            mm_r = 4.5 * rub_rock * clean_on
            mm_p = 10.0 * pres + 2.2 * rub_rock * clean_on
            rig_dx = -2.85 * pres
            rig_dy = +2.45 * pres
            rig_dz = -0.35 * pres
            rig_r += +10.0 * pres
            rig_y += +16.0 * pres
            rig_p += +14.5 * pres

        cur_base = (BASE[0] + rig_dx, BASE[1] + rig_dy, BASE[2] + rig_dz)
        bow_local, nock_p = _build_bow_frame_mesh(draw_t, str_vib, arrow_show, (mm_x, mm_y, mm_z), mm_p)

        (ca_v, ca_n), (wh_v, wh_n), bar_orig_eye, bar_axis_eye, tip_eye = megaman_eye_frames_and_tip(
            mm_parts, (mm_x, mm_y, mm_z), spin, mm_p, mm_r, mm_yw, mm_sc,
            cur_base, SCALE, rig_r, rig_p, rig_y,
        )

        # Left Hand grips Bow Riser (eye-space forearm stays cleanly anchored to bottom-left!)
        lh = build_articulated_ranger_hand(
            palm_center=rig_pt_to_eye((12.75, +0.35, -1.85), cur_base, SCALE, rig_r, rig_p, rig_y),
            fwd_dir=rig_nrm_to_eye((+0.82, -0.52, +0.24), rig_r, rig_p, rig_y),
            up_dir=rig_nrm_to_eye((-0.20, +0.14, +0.97), rig_r, rig_p, rig_y),
            side_sign=+1.0, finger_curls=(0.85, 0.88, 0.90, 0.88),
            thumb_curl=0.76, thumb_abd=36.0, hand_scale=0.62, forearm_len=8.5,
            forearm_dir=vnorm((-0.58, +0.44, -0.68)),
        )

        # Right Hand: Mediterranean 3-finger bowstring hook -> reaches forward w/ red shop rag on top of chrome bar!
        rh_str_loc = (
            vadd((nock_p[0] - 1.45, nock_p[1] - 0.65, nock_p[2] - 0.35), pluck_off)
            if str_release < 0.5
            else (4.8, -1.9, -0.8)
        )
        str_palm_eye = rig_pt_to_eye(rh_str_loc, cur_base, SCALE, rig_r, rig_p, rig_y)
        str_fwd_eye = rig_nrm_to_eye((+0.80, +0.48, +0.35), rig_r, rig_p, rig_y)
        str_up_eye = rig_nrm_to_eye((-0.22, -0.45, +0.86), rig_r, rig_p, rig_y)

        s_along = 1.15 + 3.25 * stroke_t
        rub_center_eye = vadd(bar_orig_eye, vmul(bar_axis_eye, s_along * SCALE))
        pol_palm_eye = vadd(rub_center_eye, (+0.32, -0.82 - 1.10 * admire, -0.76 + 0.25 * admire))
        pol_fwd_eye = vnorm(vadd(vmul(bar_axis_eye, 0.20), (+0.22, +0.72, +0.62)))
        pol_up_eye = vnorm((-0.28, -0.52, +0.81))

        rh_palm = vlerp(str_palm_eye, pol_palm_eye, clean_on)
        rh_fwd = vnorm(vlerp(str_fwd_eye, pol_fwd_eye, clean_on))
        rh_up = vnorm(vlerp(str_up_eye, pol_up_eye, clean_on))
        hook_c = 0.80 * (1.0 - 0.72 * str_release)
        pol_c = 0.86 - 0.52 * admire
        rh_curls = (
            hook_c * (1.0 - clean_on) + pol_c * clean_on,
            (hook_c + 0.05) * (1.0 - clean_on) + (pol_c + 0.03) * clean_on,
            hook_c * (1.0 - clean_on) + (pol_c + 0.04) * clean_on,
            0.88 * (1.0 - clean_on) + pol_c * clean_on,
        )

        rh = build_articulated_ranger_hand(
            palm_center=rh_palm, fwd_dir=rh_fwd, up_dir=rh_up,
            side_sign=-1.0, finger_curls=rh_curls,
            thumb_curl=0.72 * (1.0 - clean_on) + (0.76 - 0.35 * admire) * clean_on,
            thumb_abd=34.0, hand_scale=0.62, forearm_len=8.5,
            forearm_dir=vnorm((-0.42, -0.58, -0.70)),
        )

        rag_pos = vlerp(vadd(rh_palm, (-0.8, -0.4, -0.6)), rub_center_eye, clean_on)
        rag_mp = build_shop_rag_part(rag_pos, bar_axis_eye, (-0.65, +0.28, +0.70), vis_scale=1.12 * clean_on * (1.0 - 0.55 * admire), wave_ph=fi * 0.9)

        bv, bn = transform_mesh_to_eye(bow_local, cur_base, SCALE, rig_r, rig_p, rig_y)
        arsen_frames.append((bv + rag_mp.verts, bn + rag_mp.norms))
        ca_frames.append((ca_v, ca_n))
        wh_frames.append((wh_v, wh_n))
        hand_frames.append((lh.verts + rh.verts, lh.norms + rh.norms))

        muz_eye = rig_pt_to_eye((19.5, MM_Y, MM_Z), cur_base, SCALE, rig_r, rig_p, rig_y)
        fwd_eye = rig_nrm_to_eye((1.0, 0.0, 0.0), rig_r, rig_p, rig_y)
        fx_mp = build_arsenal_fx_eye(muz_eye, fwd_eye, blast, UV_FX_SNAP, tip_eye, glint)
        fx_frames.append((fx_mp.verts, fx_mp.norms))

        if fi == 0:
            arsen_ref = MeshPart("arsenal")
            arsen_ref.append_part(bow_local)
            arsen_ref.append_part(rag_mp)
            hand_ref = MeshPart("hand")
            hand_ref.append_part(lh)
            hand_ref.append_part(rh)
            fx_ref = fx_mp
            muzzle_out = [round(c, 2) for c in muz_eye]

    surfs = pack_surfaces_from_frames(arsen_frames, arsen_ref, ca_frames, ca_ref, wh_frames, wh_ref, hand_frames, hand_ref, fx_frames, fx_ref)
    return surfs, muzzle_out


# ===========================================================================
# WEAPON 4: HAND-HELD THROWER ('Bare-Handed Mega-Chuck') — progs/v_mm_handthrow.md3
# ===========================================================================
def build_v4_handthrow():
    """Pure bare-handed gloved grip on the live revving Mega Man contraption + overhand chuck + hilarious CoD rag polish!"""
    mm_parts = build_megaman_payload_parts()
    ca_ref, wh_ref = make_mm_ref_meshes(mm_parts)

    EYE_ZERO = (0.0, 0.0, 0.0)
    MM_BASE = (12.10, -2.85, -1.95)
    MM_SCALE_0 = 0.78
    R0, P0, Y0 = -6.5, +6.5, +16.5

    arsen_frames, ca_frames, wh_frames, hand_frames, fx_frames = [], [], [], [], []
    arsen_ref = hand_ref = fx_ref = None

    for fi in range(89):
        mm_pos = list(MM_BASE)
        mm_r, mm_p, mm_yw = R0, P0, Y0
        mm_sc = MM_SCALE_0
        spin = 0.0
        grip_back = 2.65  # distance behind T-collar where Right Hand grips the rear chrome tube!
        rh_open = 0.0
        rh_detached_pos = None
        juggle_gap = 0.0
        lh_rest_pos = (9.6, +4.4, -5.8)
        blast = 0.0
        clean_on = 0.0
        stroke_t = 0.0
        rub_rock = 0.0
        admire = 0.0
        glint = 0.0

        if fi < 16:
            # IDLE: Bare-handed grip on a live motorized wheeled contraption — big wheel spin + wild bucking bobble!
            ch = idle_bobble_channels(fi, amp_scale=1.28)
            spin = ch["spin"]
            mm_pos[0] += ch["sway_dx"]
            mm_pos[1] += ch["mm_dy"] + ch["sway_dy"]
            mm_pos[2] += ch["mm_dz"] + ch["sway_dz"]
            mm_r += ch["mm_roll"]
            mm_p += ch["mm_pitch"]
            mm_yw += ch["mm_yaw"]
            lh_rest_pos = (9.6, +4.4 + 0.25 * math.cos(fi * math.pi / 8.0), -5.6 + 0.28 * math.sin(fi * math.pi / 8.0))
        elif fi < 36:
            k = fi - 16
            if k < 3:
                # 16..18: OVERHAND BASEBALL WIND-UP! Right hand cocks Mega Man back & up inside viewport; Left hand sights forward!
                u = smoothstep((k + 1) / 3.0)
                mm_pos = list(vlerp(MM_BASE, (8.95, -4.45, -0.25), u))
                mm_p = P0 + 18.0 * u
                mm_r = R0 + 22.0 * u
                mm_yw = Y0 - 10.0 * u
                spin = (k + 1) * 62.0
                lh_rest_pos = vlerp((9.6, +4.4, -5.8), (11.5, +2.8, -2.4), u)
            elif k == 3:
                # 19 (fire4): WHIP RELEASE!! Right arm snaps forward across view, fingers flick wide open!
                mm_pos = [18.8, -1.2, -0.4]
                spin = 280.0
                rh_detached_pos = (14.6, -1.8, -1.2)
                rh_open = 1.0
                blast = 1.0
                lh_rest_pos = (9.8, +3.8, -4.2)
            elif k < 9:
                # 20..24: Throwing arm follow-through down-left; Mega Man airborne downrange
                u = (k - 3) / 5.0
                su = smoothstep(u)
                mm_sc = 0.001
                mm_pos = [8.0, 0.0, -10.0]
                rh_detached_pos = vlerp((14.2, -1.0, -1.8), (10.2, -1.6, -5.4), su)
                rh_open = 1.0 - 0.35 * su
                blast = max(0.0, 0.52 - 0.24 * (k - 3))
                lh_rest_pos = vlerp((9.8, +3.8, -4.2), (9.6, +4.4, -5.8), su)
            else:
                # 25..35: Snatches fresh revving Mega Man up from belt with a bouncy catch settle!
                u = (k - 9) / 10.0
                su = smoothstep(min(1.0, u * 1.25))
                bounce = 0.55 * math.sin(u * math.pi * 2.0) * (1.0 - u)
                mm_pos = list(vlerp((8.8, -4.6, -6.2), MM_BASE, su))
                mm_pos[2] += bounce
                mm_p = P0 - 18.0 * (1.0 - su)
                mm_r = R0 + 12.0 * math.sin(u * math.pi * 2.0) * (1.0 - u)
                mm_sc = MM_SCALE_0 * min(1.0, 0.38 + 0.90 * u)
                spin = (k - 9) * 36.0
                rh_open = max(0.0, 0.65 * (1.0 - u * 1.8))
        elif fi == 36:
            mm_sc = 0.001
            mm_pos = [8.0, 0.0, -10.0]
            rh_detached_pos = (10.5, -3.4, -4.8)
            rh_open = 0.82
        elif fi < 61:
            # COD INSPECT A (37..60): Hold spinning Mega Man out center-screen, twist wrist left/right + palm juggle hop!
            k = fi - 37
            env, turn_w, fl = inspect_hold_envelope(k)
            spin = k * 30.0
            juggle_gap = 1.45 * fl  # quick 1.4u palm toss-and-catch in mid-air!
            rh_open = 0.58 * fl
            mm_pos = [
                MM_BASE[0] + 0.55 * env,
                MM_BASE[1] + 1.95 * env - 0.75 * turn_w * env,
                MM_BASE[2] + 0.95 * env + juggle_gap,
            ]
            mm_yw = Y0 + 46.0 * turn_w * env
            mm_r = R0 + 34.0 * turn_w * env
            mm_p = P0 + 10.0 * env + 12.0 * fl
            lh_rest_pos = vlerp((9.6, +4.4, -5.8), (10.6, +3.2, -3.9), env)
        else:
            # COD INSPECT B (61..88): Right hand grips rear cap & tilts gleaming chrome bar UP at +32° dead-center;
            # Left gloved hand rises w/ red shop rag, wraps around shaft & strokes/polishes 3.5x -> STAR GLINT!
            k = fi - 61
            pres, clean_on, stroke_t, rub_rock, admire, glint = inspect_clean_envelope(k)
            spin = k * (720.0 / 28.0)
            grip_back = 2.65 + 1.45 * pres  # shift right hand back onto rear rubber cap so full chrome shaft is exposed!
            mm_pos = [
                MM_BASE[0] - 0.55 * pres,
                MM_BASE[1] + 1.85 * pres,
                MM_BASE[2] + 0.45 * pres + 0.14 * rub_rock * clean_on,
            ]
            mm_p = P0 + 25.5 * pres + 2.2 * rub_rock * clean_on  # tilts bullet nose proudly upward!
            mm_yw = Y0 + 12.0 * pres
            mm_r = R0 + 6.5 * pres + 4.8 * rub_rock * clean_on

        (ca_v, ca_n), (wh_v, wh_n), bar_orig_eye, bar_axis_eye, tip_eye = megaman_eye_frames_and_tip(
            mm_parts, tuple(mm_pos), spin, mm_p, mm_r, mm_yw, mm_sc,
            EYE_ZERO, 1.0, 0.0, 0.0, 0.0,
        )

        # Right Hand grips rear chrome bar (or follows throwing/juggling motion)
        if rh_detached_pos is not None:
            rh_palm = rh_detached_pos
            rh_fwd = vnorm((+0.78, +0.42, +0.46))
            rh_up = vnorm((-0.28, -0.35, +0.89))
        else:
            grip_pt = vsub(bar_orig_eye, vmul(bar_axis_eye, grip_back * mm_sc))
            rh_palm = vadd(grip_pt, (0.0, -0.32, -0.52 - juggle_gap))
            rh_fwd = vnorm(vadd(vmul(bar_axis_eye, 0.45), (+0.25, +0.68, +0.52)))
            rh_up = vnorm((-0.32, -0.45, +0.83))

        rc = 0.86 * (1.0 - 0.78 * rh_open)
        rh = build_articulated_ranger_hand(
            palm_center=rh_palm, fwd_dir=rh_fwd, up_dir=rh_up,
            side_sign=-1.0, finger_curls=(rc, rc + 0.03, rc + 0.05, rc + 0.04),
            thumb_curl=0.78 * (1.0 - 0.68 * rh_open), thumb_abd=36.0,
            hand_scale=0.65, forearm_len=8.8,
            forearm_dir=vnorm((-0.68, -0.52, -0.52)),
        )

        # Left Hand: Low-ready balance -> rises w/ red shop rag to stroke & clean the gleaming chrome shaft!
        lh_idle_fwd = vnorm((+0.68, -0.62, +0.38))
        lh_idle_up = vnorm((-0.22, +0.32, +0.92))

        s_along = 0.95 + 3.45 * stroke_t
        rub_center_eye = vadd(bar_orig_eye, vmul(bar_axis_eye, s_along * MM_SCALE_0))
        pol_palm_eye = vadd(rub_center_eye, (0.05, +0.76 + 1.15 * admire, -0.48 + 0.32 * admire))
        pol_fwd_eye = vnorm(vadd(vmul(bar_axis_eye, 0.25), (0.20, -0.82, +0.48)))
        pol_up_eye = vnorm((-0.35, +0.45, +0.82))

        lh_palm = vlerp(lh_rest_pos, pol_palm_eye, clean_on)
        lh_fwd = vnorm(vlerp(lh_idle_fwd, pol_fwd_eye, clean_on))
        lh_up = vnorm(vlerp(lh_idle_up, pol_up_eye, clean_on))
        lc = 0.55 * (1.0 - clean_on) + (0.86 - 0.52 * admire) * clean_on

        lh = build_articulated_ranger_hand(
            palm_center=lh_palm, fwd_dir=lh_fwd, up_dir=lh_up,
            side_sign=+1.0, finger_curls=(lc, lc + 0.04, lc + 0.06, lc + 0.05),
            thumb_curl=0.52 * (1.0 - clean_on) + (0.76 - 0.35 * admire) * clean_on,
            thumb_abd=38.0, hand_scale=0.63, forearm_len=8.5,
            forearm_dir=vnorm((-0.62, +0.52, -0.58)),
        )

        rag_pos = vlerp(vadd(lh_palm, (-0.8, +0.4, -0.6)), rub_center_eye, clean_on)
        rag_mp = build_shop_rag_part(rag_pos, bar_axis_eye, (0.0, +0.55, +0.83), vis_scale=0.92 * clean_on * (1.0 - 0.55 * admire), wave_ph=fi * 0.95)

        arsen_frames.append((rag_mp.verts, rag_mp.norms))
        ca_frames.append((ca_v, ca_n))
        wh_frames.append((wh_v, wh_n))
        hand_frames.append((lh.verts + rh.verts, lh.norms + rh.norms))

        muz_eye = (15.5, -1.6, -1.0)
        fwd_eye = vnorm((1.0, 0.08, 0.04))
        fx_mp = build_arsenal_fx_eye(muz_eye, fwd_eye, blast, UV_FX_SNAP, tip_eye, glint)
        fx_frames.append((fx_mp.verts, fx_mp.norms))

        if fi == 0:
            arsen_ref = rag_mp
            hand_ref = MeshPart("hand")
            hand_ref.append_part(lh)
            hand_ref.append_part(rh)
            fx_ref = fx_mp
            muzzle_out = [round(c, 2) for c in muz_eye]

    surfs = pack_surfaces_from_frames(arsen_frames, arsen_ref, ca_frames, ca_ref, wh_frames, wh_ref, hand_frames, hand_ref, fx_frames, fx_ref)
    return surfs, muzzle_out
