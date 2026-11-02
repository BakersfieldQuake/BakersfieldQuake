"""Headless Blender 5.2 Sculpted Multi-Part 3D Builder for BakersfieldQuake's 3 NEW Wild Vehicles:
  1. hdtruck   : Heavy-Duty Crew-Cab Diesel Dually Rig Truck (6 Wheels, Bullbar, Twin Chrome Stacks)
  2. schoolbus : Full-Size Type-C Conventional Yellow School Bus (6 Wheels, 14 Side Windows, STOP Sign,
                 Bi-Fold Entry Door, Emergency Exit Door, Roof Escape Hatches, Interior Bench Seats)
  3. gtcar     : V8 Street Muscle Fastback Car (4 Wide 5-Spoke Alloys, Twin-Scoop Hood, Muscle Spoiler)

Usage:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python source/mm_tools/blender_build_wild_vehicles.py
"""
import json
import math
import os
import random
import sys

import bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import veh_specs as vs
import wild_vehicles_specs_tex as wvs
import blender_build_vehicles as bbv
from blender_build_vehicles import PartBuilder, build_3d_wheel, arch_lift, add_curved_fascia, add_wraparound_bumper

OUT_JSON = argv[0] if len(argv) > 0 else os.path.join(HERE, "out", "wild_vehicles_parts.json")

# Sync SWATCH_RECTS["engine"] to the isolated wild engine sub-rect so engine blocks never touch decals!
bbv.SWATCH_RECTS["engine"] = wvs.RECT_WILD_ENGINE


def _place_wheel(proto, nm, wx, wy, wz):
    cp = dict(proto)
    cp["name"] = nm
    cp["origin"] = [round(wx, 3), round(wy, 3), round(wz, 3)]
    return cp


def add_uv_quad(pb, p0, p1, p2, p3, uv0, uv1, uv2, uv3, region="decal"):
    """Adds an outward CCW quad with explicit per-corner UVs (zero distortion, always right-reading!)."""
    pts = [Vector(p0), Vector(p1), Vector(p2), Vector(p3)]
    if (pts[1] - pts[0]).length < 1e-4 or (pts[2] - pts[1]).length < 1e-4:
        return
    verts = [pb.bm.verts.new(p) for p in pts]
    try:
        f = pb.bm.faces.new(verts)
    except ValueError:
        return
    f[pb.mat_layer] = region.encode("ascii")
    for l, uv in zip(f.loops, (uv0, uv1, uv2, uv3)):
        l[pb.uv_layer].uv = (round(float(uv[0]), 4), round(float(uv[1]), 4))


def add_uv_tri(pb, p0, p1, p2, uv0, uv1, uv2, region="decal"):
    pts = [Vector(p0), Vector(p1), Vector(p2)]
    if (pts[1] - pts[0]).cross(pts[2] - pts[0]).length < 1e-5:
        return
    verts = [pb.bm.verts.new(p) for p in pts]
    try:
        f = pb.bm.faces.new(verts)
    except ValueError:
        return
    f[pb.mat_layer] = region.encode("ascii")
    for l, uv in zip(f.loops, (uv0, uv1, uv2)):
        l[pb.uv_layer].uv = (round(float(uv[0]), 4), round(float(uv[1]), 4))


def add_painted_panel(pb, grid_pts, thickness_vec, outer_region="top", inner_region="trim", edge_region="top"):
    """Builds a 3D sheet-metal panel whose rolled perimeter edges match outer_region (zero black seam bleed!)."""
    nx = len(grid_pts)
    ny = len(grid_pts[0])
    tv = Vector(thickness_vec)
    top_g = [[Vector(grid_pts[i][j]) for j in range(ny)] for i in range(nx)]
    bot_g = [[top_g[i][j] + tv for j in range(ny)] for i in range(nx)]

    e1 = top_g[1][0] - top_g[0][0]
    e2 = top_g[0][1] - top_g[0][0]
    flip = e1.cross(e2).dot(-tv) < 0

    for i in range(nx - 1):
        for j in range(ny - 1):
            pb.add_quad(top_g[i][j], top_g[i + 1][j], top_g[i + 1][j + 1], top_g[i][j + 1], outer_region, flip=flip)
            pb.add_quad(bot_g[i][j], bot_g[i][j + 1], bot_g[i + 1][j + 1], bot_g[i + 1][j], inner_region, flip=flip)

    for i in range(nx - 1):
        pb.add_quad(top_g[i][0], bot_g[i][0], bot_g[i + 1][0], top_g[i + 1][0], edge_region, flip=flip)
        pb.add_quad(top_g[i + 1][ny - 1], bot_g[i + 1][ny - 1], bot_g[i][ny - 1], top_g[i][ny - 1], edge_region, flip=flip)
    for j in range(ny - 1):
        pb.add_quad(top_g[0][j + 1], bot_g[0][j + 1], bot_g[0][j], top_g[0][j], edge_region, flip=flip)
        pb.add_quad(top_g[nx - 1][j], bot_g[nx - 1][j], bot_g[nx - 1][j + 1], top_g[nx - 1][j + 1], edge_region, flip=flip)


def add_bilateral_side_decal(pb_l, pb_r, x_rear, x_front, z_lo, z_hi, y_at_xz, rect, n_segs=4, pad_px=4.0, y_ofs=0.24):
    """Places flush right-reading signage/badge quads on BOTH +Y (driver) and -Y (passenger) sides!"""
    rx0, ry0, rx1, ry1 = rect
    u0 = (rx0 + pad_px) / vs.W_ATLAS
    u1 = (rx1 - pad_px) / vs.W_ATLAS
    v_top = (ry0 + pad_px) / vs.H_ATLAS
    v_bot = (ry1 - pad_px) / vs.H_ATLAS

    for k in range(n_segs):
        t0 = k / float(n_segs)
        t1 = (k + 1) / float(n_segs)
        xa = x_rear + (x_front - x_rear) * t0
        xb = x_rear + (x_front - x_rear) * t1

        ya_lo = y_at_xz(xa, z_lo) + y_ofs
        ya_hi = y_at_xz(xa, z_hi) + y_ofs
        yb_lo = y_at_xz(xb, z_lo) + y_ofs
        yb_hi = y_at_xz(xb, z_hi) + y_ofs

        # Right / Passenger side (-Y, viewer faces +Y: viewer LEFT = x_rear, viewer RIGHT = x_front)
        if pb_r is not None:
            ur_a = u0 + (u1 - u0) * t0
            ur_b = u0 + (u1 - u0) * t1
            add_uv_quad(
                pb_r,
                (xa, -ya_lo, z_lo), (xb, -yb_lo, z_lo), (xb, -yb_hi, z_hi), (xa, -ya_hi, z_hi),
                (ur_a, v_bot), (ur_b, v_bot), (ur_b, v_top), (ur_a, v_top),
            )

        # Left / Driver side (+Y, viewer faces -Y: viewer LEFT = x_front, viewer RIGHT = x_rear!)
        if pb_l is not None:
            ul_b = u0 + (u1 - u0) * (1.0 - t1)
            ul_a = u0 + (u1 - u0) * (1.0 - t0)
            add_uv_quad(
                pb_l,
                (xb, yb_lo, z_lo), (xa, ya_lo, z_lo), (xa, ya_hi, z_hi), (xb, yb_hi, z_hi),
                (ul_b, v_bot), (ul_a, v_bot), (ul_a, v_top), (ul_b, v_top),
            )


def _build_crumpled_wreck(chassis_dict, sp, seed):
    zb = sp["z_belt"]
    z1 = sp["z_roof"]
    x1 = sp["x1"]
    hw = sp["hw"]
    z_slump = -sp["wheel_r"] * 0.36

    u_eng_max = 146.0 / vs.W_ATLAS
    v_eng_min = 800.0 / vs.H_ATLAS
    v_eng_max = 958.0 / vs.H_ATLAS
    u_gls_min, u_gls_max = 512.0 / vs.W_ATLAS, 800.0 / vs.W_ATLAS
    v_gls_min, v_gls_max = 544.0 / vs.H_ATLAS, 800.0 / vs.H_ATLAS

    wreck_verts, wreck_norms, wreck_uvs = [], [], []
    for (vx, vy, vz), (nx, ny, nz), (u, v) in zip(chassis_dict["verts"], chassis_dict["norms"], chassis_dict["uvs"]):
        is_eng = (u <= u_eng_max and v_eng_min <= v <= v_eng_max)
        is_gls = (u_gls_min <= u <= u_gls_max and v_gls_min <= v <= v_gls_max)
        h_frac = max(0.0, (vz - zb) / max(1.0, z1 - zb))
        # Realistic crash/blast deformation: buckled roof, banana-bent frame, accordion nose/tail dents!
        cave_z = -h_frac * (6.2 + 4.0 * math.sin(vx * 0.038 + 0.5))
        twist_y = h_frac * 4.5 * math.cos(vx * 0.032)
        banana_z = ((vx / max(1.0, x1)) ** 2) * 5.2
        if is_eng:
            banana_z -= 2.5 + 1.8 * math.cos(vy * 0.18)
        dent_y = -0.08 * vy * (0.5 + 0.5 * math.sin(vx * 0.08 + vz * 0.07))
        nx_v = vx * 0.975 + math.sin(vz * 0.10 + vy * 0.08) * 1.6
        ny_v = vy + twist_y + dent_y
        nz_v = max(1.2, vz + z_slump + cave_z + banana_z)
        wreck_verts.append([round(nx_v, 3), round(ny_v, 3), round(nz_v, 3)])
        wreck_norms.append([nx, ny, nz])
        if is_eng:
            wu, wv = vs.rect_uv(vs.RECT_EMBER, u / u_eng_max, (v - v_eng_min) / (v_eng_max - v_eng_min))
        elif is_gls:
            # Keep shattered spiderweb glass UV from burn_atlas!
            wu, wv = u, v
        else:
            su = (abs(vx * 0.011 + vy * 0.014)) % 1.0
            sv = (abs(vz * 0.016 + vx * 0.008)) % 1.0
            wu, wv = vs.rect_uv(vs.RECT_WRECK, su, sv)
        wreck_uvs.append([wu, wv])

    # Smooth 60-point 3D perimeter roll-cage hull around the deformed wreck for realistic multi-turn barrel rolls!
    roll_hull = []
    x_min = sp["x0"] * 0.95
    x_max = sp["x1"] * 0.95
    z_lo = max(2.0, sp["z_bot"] + z_slump)
    z_hi = max(z_lo + 18.0, z1 + z_slump - 5.5)
    z_mid = 0.5 * (z_lo + z_hi)
    rx_z = 0.5 * (z_hi - z_lo)
    ry_w = hw * 0.94

    for k_x in range(6):
        xs_f = x_min + (x_max - x_min) * k_x / 5.0
        end_taper = 0.86 if (xs_f == x_min or xs_f == x_max) else 1.0
        for k in range(10):
            ang = 2.0 * math.pi * k / 10.0
            hy = math.cos(ang) * ry_w * end_taper
            hz = z_mid + math.sin(ang) * rx_z * (0.82 if xs_f > sp["x_cowl"] else 1.0)
            hz = max(1.5, hz)
            roll_hull.append([round(float(xs_f), 2), round(float(hy), 2), round(float(hz), 2)])

    return {
        "name": "wreck_chassis",
        "origin": [0.0, 0.0, 0.0],
        "verts": wreck_verts,
        "norms": wreck_norms,
        "uvs": wreck_uvs,
        "tris": chassis_dict["tris"],
        "roll_hull": roll_hull,
    }


def _build_shrapnel_set(sp, seed, count=12):
    rng_w = random.Random(seed)
    shraps = []
    x1, hw, zb = sp["x1"], sp["hw"], sp["z_belt"]
    for si in range(count):
        spb = PartBuilder(f"shrap_{si}", sp)
        r_sh = 5.0 + (si % 4) * 2.6
        thk = 1.0 + (si % 3) * 0.65
        reg = ("auto", "wreck", "glass", "chrome", "ember")[si % 5]
        pts_grid = []
        for gi in range(3):
            row = []
            for gj in range(3):
                px = (gi - 1) * r_sh + rng_w.uniform(-1.8, 1.8)
                py = (gj - 1) * r_sh * 0.80 + rng_w.uniform(-1.5, 1.5)
                pz = math.sin(gi * 1.5 + gj * 1.2 + si) * 2.8
                row.append((px, py, pz))
            pts_grid.append(row)
        add_painted_panel(spb, pts_grid, (0.0, 0.0, -thk), outer_region=reg, inner_region="wreck", edge_region="wreck")
        sd = spb.export_dict(custom_origin=(0.0, 0.0, 0.0))
        ang = 2.0 * math.pi * si / float(count)
        sd["origin"] = [
            round(math.cos(ang) * (x1 * 0.46), 2),
            round(math.sin(ang) * (hw * 0.64), 2),
            round(zb * 0.78 + (si % 3) * 6.0, 2),
        ]
        shraps.append(sd)
    return shraps


# ==============================================================================
# 1. HEAVY-DUTY CREW-CAB DIESEL DUALLY RIG TRUCK ("hdtruck")
# ==============================================================================
def build_hdtruck():
    sp = dict(wvs.get_wild_spec("hdtruck"))
    x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
    z0, z_bmp, zb, z1 = sp["z_bot"], sp["z_bmp"], sp["z_belt"], sp["z_roof"]
    zn_top, zr_top = sp["z_nose_top"], sp["z_rear_top"]
    wxs = (sp["wheel_x_f"], sp["wheel_x_r"])

    chassis = PartBuilder("chassis", sp)
    hood = PartBuilder("hood", sp)
    door_l = PartBuilder("door_l", sp)
    door_r = PartBuilder("door_r", sp)
    extra = PartBuilder("extra_part", sp)
    bumper_f = PartBuilder("bumper_f", sp)
    bumper_r = PartBuilder("bumper_r", sp)
    detail = PartBuilder("detail_vib", sp)

    x_nose = x1 - 3.5
    x_tail = x0 + 3.0

    xs = sorted(set(
        [round(x_tail + (x_nose - x_tail) * i / 38.0, 2) for i in range(39)]
        + [sp["x_door0"], sp["x_door1"], sp["x_cowl"], -28.0]
    ))

    def side_profile(x):
        t_f = max(0.0, (x - (x_nose - 20.0)) / 20.0)
        t_r = max(0.0, ((x_tail + 14.0) - x) / 14.0)
        taper = 1.0 - 0.08 * (t_f ** 1.6) - 0.04 * (t_r ** 1.6)
        dz_a, dy_f = arch_lift(x, wxs, sp["arch_r"], sp["flare"])
        dually_bulge = 0.0
        dx_r = abs(x - sp["wheel_x_r"])
        if dx_r < 34.0:
            dually_bulge = 4.8 * math.cos(0.5 * math.pi * (dx_r / 34.0)) ** 1.3
        if x > sp["x_cowl"]:
            ft = min(1.0, (x - sp["x_cowl"]) / max(1.0, x_nose - sp["x_cowl"]))
            zb_x = zb + (zn_top - zb) * (ft ** 1.15)
        else:
            zb_x = zb
        y_sh = hw * taper + dy_f + dually_bulge
        y_sill = hw * 0.91 * taper + dy_f * 0.4 + dually_bulge * 0.65
        y_blt = hw * 0.95 * taper + dually_bulge * 0.35
        z_flr = z0 + dz_a
        if x > x_nose - 5.5 or x < x_tail + 5.5:
            z_flr = max(z_flr, z_bmp - 0.5)
        return y_sill, y_sh, y_blt, min(zb_x - 4.0, z_flr), zb_x

    def side_y_at(x, z):
        ys, ysh, yblt, zs, zbx = side_profile(x)
        zm = 0.5 * (zs + zbx)
        if z <= zm:
            t = max(0.0, min(1.0, (z - zs) / max(0.5, zm - zs)))
            return ys + (ysh - ys) * t
        t = max(0.0, min(1.0, (z - zm) / max(0.5, zbx - zm)))
        return ysh + (yblt - ysh) * t

    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        xm = 0.5 * (xa + xb)
        ys_a, ysh_a, yb_a, zs_a, zba = side_profile(xa)
        ys_b, ysh_b, yb_b, zs_b, zbb = side_profile(xb)
        zmid_a = 0.5 * (zs_a + zba)
        zmid_b = 0.5 * (zs_b + zbb)

        in_door = (xm > sp["x_door0"] + 0.05) and (xm < sp["x_door1"] - 0.05)
        tl = door_l if in_door else chassis
        tr = door_r if in_door else chassis

        tl.add_quad((xb, ys_b, zs_b), (xa, ys_a, zs_a), (xa, ysh_a, zmid_a), (xb, ysh_b, zmid_b), "auto")
        tl.add_quad((xb, ysh_b, zmid_b), (xa, ysh_a, zmid_a), (xa, yb_a, zba), (xb, yb_b, zbb), "auto")
        tr.add_quad((xa, -ys_a, zs_a), (xb, -ys_b, zs_b), (xb, -ysh_b, zmid_b), (xa, -ysh_a, zmid_a), "auto")
        tr.add_quad((xa, -ysh_a, zmid_a), (xb, -ysh_b, zmid_b), (xb, -yb_b, zbb), (xa, -yb_a, zba), "auto")

        if in_door:
            yi = 2.6
            door_l.add_quad((xa, ys_a - yi, zs_a + 1.5), (xb, ys_b - yi, zs_b + 1.5), (xb, yb_b - yi, zbb - 0.4), (xa, yb_a - yi, zba - 0.4), "interior")
            door_l.add_quad((xa, yb_a, zba), (xa, yb_a - yi, zba - 0.4), (xb, yb_b - yi, zbb - 0.4), (xb, yb_b, zbb), "trim")
            door_r.add_quad((xb, -ys_b + yi, zs_b + 1.5), (xa, -ys_a + yi, zs_a + 1.5), (xa, -yb_a + yi, zba - 0.4), (xb, -yb_b + yi, zbb - 0.4), "interior")
            door_r.add_quad((xb, -yb_b, zbb), (xb, -yb_b + yi, zbb - 0.4), (xa, -yb_a + yi, zba - 0.4), (xa, -yb_a, zba), "trim")

        yw = 19.0
        chassis.add_quad((xa, -yw, z0), (xa, yw, z0), (xb, yw, z0), (xb, -yw, z0), "bottom")
        chassis.add_quad((xa, yw, zs_a), (xa, ys_a, zs_a), (xb, ys_b, zs_b), (xb, yw, zs_b), "trim")
        chassis.add_quad((xa, -ys_a, zs_a), (xa, -yw, zs_a), (xb, -yw, zs_b), (xb, -ys_b, zs_b), "trim")

    # Right-reading 3D Fender Emblem ("6.7TD TURBO DIESEL") & Rear Bedside ("4x4 HEAVY DUALLY") on BOTH sides!
    add_bilateral_side_decal(chassis, chassis, 44.8, 55.2, zb - 10.2, zb - 3.6, side_y_at, wvs.RECT_BADGE_A, n_segs=4, pad_px=4.0, y_ofs=0.45)
    add_bilateral_side_decal(chassis, chassis, -120.5, -99.5, zb - 11.2, zb - 4.2, side_y_at, wvs.RECT_DECAL_STRIP, n_segs=6, pad_px=4.0, y_ofs=0.45)

    # Crew-cab chrome tubular side steps
    for sy in (-1.0, 1.0):
        chassis.add_cylinder((-26.0, sy * (hw + 0.5), z0 - 2.2), (39.0, sy * (hw + 0.5), z0 - 2.2), 2.1, 2.1, segs=8, region="chrome")

    # Front Fascia + Heavy Welded Steel Bullbar Bumper (framing RIG emblem & plate cleanly!) + Engine Bay
    _, _, yb_f, _, _ = side_profile(x_nose)
    add_curved_fascia(chassis, x_nose, 2.4, yb_f, z_bmp, zn_top + 2.2, is_front=True, n_strips=6)
    add_wraparound_bumper(bumper_f, x_nose - 0.5, x1 + 1.5, 2.8, hw * 0.98, z0 - 1.0, z_bmp + 1.5, wing_len=7.5, is_front=True, top_reg="chrome")
    for sy in (-1.0, 1.0):
        bumper_f.add_box(x1 + 0.5, sy * 23.5 - 1.5, z0 + 1.0, x1 + 3.6, sy * 23.5 + 1.5, zn_top - 1.5, "trim")
    bumper_f.add_cylinder((x1 + 3.0, -24.5, zn_top - 2.5), (x1 + 3.0, 24.5, zn_top - 2.5), 1.8, 1.8, segs=8, region="chrome")
    bumper_f.add_cylinder((x1 + 3.3, -24.0, z_bmp + 1.8), (x1 + 3.3, 24.0, z_bmp + 1.8), 1.6, 1.6, segs=8, region="trim")

    xc = sp["x_cowl"]
    ye = yb_f * 0.82
    ze_flr = zn_top - 12.0
    chassis.add_box(xc + 2.0, -ye, ze_flr, x_nose - 2.5, ye, ze_flr + 2.2, "trim")
    chassis.add_box(xc + 6.0, -14.5, ze_flr + 2.2, x_nose - 10.0, 14.5, zn_top - 1.5, "engine")
    _, _, yb_cowl, _, zb_cowl = side_profile(xc)
    for sgn_y in (-1.0, 1.0):
        if sgn_y > 0:
            chassis.add_quad((xc, ye, zb_cowl - 0.4), (x_nose, ye, zn_top - 0.4), (x_nose, yb_f, zn_top), (xc, yb_cowl, zb_cowl), "top")
        else:
            chassis.add_quad((xc, -yb_cowl, zb_cowl), (x_nose, -yb_f, zn_top), (x_nose, -ye, zn_top - 0.4), (xc, -ye, zb_cowl - 0.4), "top")

    # Power-dome diesel hood (rolled painted perimeter edges — zero black seam dashes!)
    hood_grid = []
    for i in range(5):
        tx = i / 4.0
        xh = (xc + 0.8) + (x_nose + 0.8 - (xc + 0.8)) * tx
        _, _, yb_h, _, zbh = side_profile(xh)
        yh_max = yb_h * 0.85
        row = []
        for j in range(7):
            ty = -1.0 + 2.0 * j / 6.0
            crown = (1.0 - ty * ty) * 3.0 + (2.2 * math.sin(math.pi * (0.1 + 0.8 * tx)) if abs(ty) < 0.48 else 0.0)
            row.append((xh, yh_max * ty, zbh + crown))
        hood_grid.append(row)
    add_painted_panel(hood, hood_grid, (0.0, 0.0, -1.6), outer_region="top", inner_region="trim", edge_region="top")

    # Crew-Cab Interior + Roof + 5 Amber Clearance Light Pods
    z_cab_flr = z0 + 4.5
    chassis.add_box(-25.0, -hw * 0.74, z_cab_flr, xc - 2.0, hw * 0.74, z_cab_flr + 2.2, "int_floor")
    chassis.add_box(xc - 13.0, -hw * 0.72, z_cab_flr + 2.2, xc - 2.0, hw * 0.72, zb + 1.5, "int_dash")
    chassis.add_cylinder((xc - 13.5, 15.0, zb - 0.5), (xc - 17.5, 15.0, zb + 2.2), 5.6, 5.6, segs=10, region="trim")
    for sy in (-15.5, 15.5):
        chassis.add_box(10.0, sy - 9.0, z_cab_flr + 2.2, 26.0, sy + 9.0, zb - 3.0, "int_seat")
        chassis.add_box(8.5, sy - 8.5, zb - 3.0, 14.5, sy + 8.5, zb + 11.5, "int_seat")
    chassis.add_box(-24.0, -hw * 0.68, z_cab_flr + 2.2, -6.0, hw * 0.68, zb + 9.5, "int_seat")

    yr = sp["y_roof"]
    xr0, xr1 = sp["x_roof0"], sp["x_roof1"]
    zr_edge = z1 - 1.8
    for j in range(4):
        ya = -yr + 2.0 * yr * j / 4.0
        yb_s = -yr + 2.0 * yr * (j + 1) / 4.0
        za = zr_edge + (1.0 - (ya / yr) ** 2) * 1.9
        zbs = zr_edge + (1.0 - (yb_s / yr) ** 2) * 1.9
        chassis.add_quad((xr0, ya, za), (xr1, ya, za), (xr1, yb_s, zbs), (xr0, yb_s, zbs), "top")
        chassis.add_quad((xr1, ya, zr_edge), (xr1, yb_s, zr_edge), (xr1, yb_s, zbs), (xr1, ya, za), "top")
        chassis.add_quad((xr0, yb_s, zr_edge), (xr0, ya, zr_edge), (xr0, ya, za), (xr0, yb_s, zbs), "top")
    for ly in (-22.0, -11.0, 0.0, 11.0, 22.0):
        chassis.add_box(xr1 - 5.5, ly - 2.2, z1 - 0.5, xr1 - 1.5, ly + 2.2, z1 + 1.8, "top")

    yb_cab = side_profile(20.0)[2]
    chassis.add_framed_window((xc, -yb_cowl, zb), (xc, yb_cowl, zb), (xr1, yr, zr_edge), (xr1, -yr, zr_edge),
                              w_bot=2.4, w_right=4.4, w_top=3.0, w_left=4.4, recess=1.0, bot_reg="trim", top_reg="top")
    chassis.add_framed_window((-28.0, yb_cab, zb), (-28.0, -yb_cab, zb), (xr0, -yr, zr_edge), (xr0, yr, zr_edge),
                              w_bot=3.0, w_right=6.8, w_top=3.0, w_left=6.8, recess=0.9)
    chassis.add_framed_window((4.0, yb_cab, zb), (-28.0, yb_cab, zb), (xr0, yr, zr_edge), (4.0, yr, zr_edge),
                              w_bot=1.6, w_right=5.0, w_top=2.6, w_left=2.4, recess=0.85, bot_reg="trim", left_reg="trim")
    chassis.add_framed_window((-28.0, -yb_cab, zb), (4.0, -yb_cab, zb), (4.0, -yr, zr_edge), (xr0, -yr, zr_edge),
                              w_bot=1.6, w_right=2.4, w_top=2.6, w_left=5.0, recess=0.85, bot_reg="trim", right_reg="trim")
    door_l.add_framed_window((41.0, yb_cowl * 0.96, zb), (4.0, yb_cab, zb), (4.0, yr, zr_edge), (xr1, yr, zr_edge),
                             w_bot=1.5, w_right=2.6, w_top=2.5, w_left=3.2, recess=0.80, bot_reg="trim", right_reg="trim", double_sided_frame=True)
    door_r.add_framed_window((4.0, -yb_cab, zb), (41.0, -yb_cowl * 0.96, zb), (xr1, -yr, zr_edge), (4.0, -yr, zr_edge),
                             w_bot=1.5, w_right=3.2, w_top=2.5, w_left=2.6, recess=0.80, bot_reg="trim", left_reg="trim", double_sided_frame=True)

    # West-Coast Chrome Tow Mirrors on doors
    for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
        d_pb.add_box(33.0, sy * (yb_cab - 0.5), zb + 2.0, 36.5, sy * (yb_cab + 9.5), zb + 4.0, "chrome")
        d_pb.add_box(33.0, sy * (yb_cab - 0.5), zb + 10.0, 36.5, sy * (yb_cab + 9.5), zb + 11.8, "chrome")
        d_pb.add_box(32.0, sy * (yb_cab + 8.5), zb + 0.5, 37.0, sy * (yb_cab + 11.8), zb + 14.0, "chrome", {"-x": "glass"})

    # Hollow Heavy-Duty Pickup Bed + Aux Diesel Tank + Rear Bumper
    xb0, xb1 = sp["x_bed_r"], sp["x_bed_f"]
    y_bed_in = hw * 0.78
    z_bed_flr = z0 + 20.0
    chassis.add_quad((xb0, -y_bed_in, z_bed_flr), (xb1, -y_bed_in, z_bed_flr), (xb1, y_bed_in, z_bed_flr), (xb0, y_bed_in, z_bed_flr), "top")
    chassis.add_quad((xb1, y_bed_in, z_bed_flr), (xb1, -y_bed_in, z_bed_flr), (xb1, -y_bed_in, zb), (xb1, y_bed_in, zb), "trim")
    for sgn_y in (-1.0, 1.0):
        yi = y_bed_in * sgn_y
        yo = yb_cab * sgn_y
        if sgn_y > 0:
            chassis.add_quad((xb0, yi, z_bed_flr), (xb0, yi, zb), (xb1, yi, zb), (xb1, yi, z_bed_flr), "trim")
            chassis.add_quad((xb0, yi, zb), (xb0, yo, zb), (xb1, yo, zb), (xb1, yi, zb), "trim")
        else:
            chassis.add_quad((xb1, yi, z_bed_flr), (xb1, yi, zb), (xb0, yi, zb), (xb0, yi, z_bed_flr), "trim")
            chassis.add_quad((xb1, yi, zb), (xb1, yo, zb), (xb0, yo, zb), (xb0, yi, zb), "trim")
    chassis.add_box(-48.0, -y_bed_in + 1.0, z_bed_flr + 0.5, -31.0, y_bed_in - 1.0, zb + 3.5, "chrome", {"+z": "top"})

    _, _, yb_r, _, _ = side_profile(x_tail)
    for sgn_y in (-1.0, 1.0):
        ya, yb_p = min(y_bed_in * sgn_y, yb_r * sgn_y), max(y_bed_in * sgn_y, yb_r * sgn_y)
        chassis.add_quad((x_tail, yb_p, z_bmp), (x_tail, ya, z_bmp), (x_tail, ya, zr_top), (x_tail, yb_p, zr_top), "rear")
    add_wraparound_bumper(bumper_r, x_tail + 0.5, x0 - 1.2, -1.8, hw * 0.98, z0, z_bmp, wing_len=7.0, is_front=False, top_reg="trim")
    # Under-bumper Class-V tow hitch receiver + chrome hitch ball (cleanly below rear license plate!)
    bumper_r.add_box(x0 - 4.2, -3.2, z0 - 3.6, x0 + 1.0, 3.2, z0 + 0.4, "trim")
    bumper_r.add_cylinder((x0 - 3.4, 0.0, z0 - 0.5), (x0 - 3.4, 0.0, z0 + 2.4), 1.6, 1.4, segs=8, region="chrome")

    # EXTRA PART: Headache Rack + Twin Vertical Chrome Diesel Exhaust Stacks + Tailgate!
    extra.add_box(x_tail - 0.8, -y_bed_in, z_bmp + 0.4, x_tail + 2.4, y_bed_in, zr_top, "trim", {"-x": "rear"})
    z_hr = z1 + 3.0
    for sy in (-1.0, 1.0):
        extra.add_box(-33.5, sy * (y_bed_in - 2.5) - 1.5, zb, -30.5, sy * (y_bed_in - 2.5) + 1.5, z_hr, "trim")
        st_y = sy * (y_bed_in - 7.5)
        extra.add_cylinder((-35.0, st_y, z_bed_flr + 2.0), (-35.0, st_y, z1 + 13.5), 3.4, 3.4, segs=12, region="chrome")
        extra.add_cylinder((-35.0, st_y, z1 + 13.5), (-39.5, st_y + sy * 2.5, z1 + 17.5), 3.4, 3.6, segs=12, region="chrome")
    extra.add_box(-33.5, -(y_bed_in - 1.0), z_hr - 2.5, -30.5, (y_bed_in - 1.0), z_hr + 0.5, "trim")

    # Undercarriage frame & heavy axles + CB antenna
    detail.add_cylinder((-31.0, yb_cab - 4.0, z_hr), (-34.0, yb_cab - 3.0, z_hr + 24.0), 0.65, 0.25, segs=6, region="chrome")
    for sy in (-1.0, 1.0):
        chassis.add_box(x_tail + 10.0, sy * 16.0 - 2.5, z0 - 1.8, x_nose - 10.0, sy * 16.0 + 2.5, z0 + 1.8, "trim")
    for wx in wxs:
        chassis.add_cylinder((wx, -sp["wheel_y"] + 2.0, sp["wheel_r"]), (wx, sp["wheel_y"] - 2.0, sp["wheel_r"]), 2.2, 2.2, segs=8, region="trim")
        chassis.add_cylinder((wx, -6.0, sp["wheel_r"]), (wx, 6.0, sp["wheel_r"]), 5.2, 5.2, segs=10, region="trim")

    chassis_dict = chassis.export_dict(custom_origin=(0.0, 0.0, 0.0))
    wreck_dict = _build_crumpled_wreck(chassis_dict, sp, seed=501)

    w_l = build_3d_wheel("wl", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], True, sp)
    w_r = build_3d_wheel("wr", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], False, sp)

    parts = {
        "chassis": chassis_dict,
        "wreck_chassis": wreck_dict,
        "hood": hood.export_dict(hinge_pivot=(xc, 0.0, zb_cowl)),
        "door_l": door_l.export_dict(),
        "door_r": door_r.export_dict(),
        "extra_part": extra.export_dict(),
        "bumper_f": bumper_f.export_dict(),
        "bumper_r": bumper_r.export_dict(),
        "detail_vib": detail.export_dict(),
        "wheel_fl": _place_wheel(w_l, "wheel_fl", sp["wheel_x_f"], sp["wheel_y"], sp["wheel_r"]),
        "wheel_fr": _place_wheel(w_r, "wheel_fr", sp["wheel_x_f"], -sp["wheel_y"], sp["wheel_r"]),
        "wheel_rl": _place_wheel(w_l, "wheel_rl", sp["wheel_x_r"], sp["wheel_y"] + 2.5, sp["wheel_r"]),
        "wheel_rr": _place_wheel(w_r, "wheel_rr", sp["wheel_x_r"], -(sp["wheel_y"] + 2.5), sp["wheel_r"]),
        "wheel_rl2": _place_wheel(w_l, "wheel_rl2", sp["wheel_x_r"], sp["wheel_y_inner"], sp["wheel_r"]),
        "wheel_rr2": _place_wheel(w_r, "wheel_rr2", sp["wheel_x_r"], -sp["wheel_y_inner"], sp["wheel_r"]),
    }
    for si, sd in enumerate(_build_shrapnel_set(sp, seed=502, count=12)):
        parts[f"shrap_{si}"] = sd
    return {"spec": sp, "parts": parts}


# ==============================================================================
# 2. FULL-SIZE TYPE-C CONVENTIONAL YELLOW SCHOOL BUS ("schoolbus")
# ==============================================================================
def build_schoolbus():
    sp = dict(wvs.get_wild_spec("schoolbus"))
    x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
    z0, z_bmp, zb, z1 = sp["z_bot"], sp["z_bmp"], sp["z_belt"], sp["z_roof"]
    zn_top, zr_top = sp["z_nose_top"], sp["z_rear_top"]
    xc = sp["x_cowl"]  # 100.0

    chassis = PartBuilder("chassis", sp)
    hood = PartBuilder("hood", sp)
    door_l = PartBuilder("door_l", sp)
    door_r = PartBuilder("door_r", sp)
    extra = PartBuilder("extra_part", sp)
    bumper_f = PartBuilder("bumper_f", sp)
    bumper_r = PartBuilder("bumper_r", sp)
    detail = PartBuilder("detail_vib", sp)

    x_body_r = -172.0
    x_nose = x1 - 3.0  # 151.0

    # --- A. Main Yellow Bus Passenger Body Sides (x: -172 .. +100)
    xs_bus = sorted(set(
        [round(x_body_r + (xc - x_body_r) * i / 30.0, 2) for i in range(31)]
        + [sp["x_door0"], sp["x_door1"]]
    ))
    for i in range(len(xs_bus) - 1):
        xa, xb = xs_bus[i], xs_bus[i + 1]
        xm = 0.5 * (xa + xb)
        dz_a, dy_a = arch_lift(xa, (sp["wheel_x_r"],), sp["arch_r"], sp["flare"])
        dz_b, dy_b = arch_lift(xb, (sp["wheel_x_r"],), sp["arch_r"], sp["flare"])
        zsa = z0 + dz_a
        zsb = z0 + dz_b
        ya_w = hw + dy_a * 0.5
        yb_w = hw + dy_b * 0.5

        in_dl = (xm > sp["x_door0"] + 0.05) and (xm < sp["x_door1"] - 0.05)
        in_dr = in_dl

        tl = door_l if in_dl else chassis

        # Left side (+Y): lower skirt..beltline
        tl.add_quad((xb, yb_w, zsb), (xa, ya_w, zsa), (xa, hw, zb), (xb, hw, zb), "side")
        if in_dl:
            door_l.add_quad((xa, hw - 2.0, zsa + 2.0), (xb, hw - 2.0, zsb + 2.0), (xb, hw - 2.0, zb), (xa, hw - 2.0, zb), "int_wall")

        # Right side (-Y): outside entry-door opening
        if not in_dr:
            chassis.add_quad((xa, -ya_w, zsa), (xb, -yb_w, zsb), (xb, -hw, zb), (xa, -hw, zb), "side")

        # Bus underfloor belly + wheelhouse clearance
        chassis.add_quad((xa, -22.0, z0), (xa, 22.0, z0), (xb, 22.0, z0), (xb, -22.0, z0), "bottom")
        chassis.add_quad((xa, 22.0, zsa), (xa, ya_w, zsa), (xb, yb_w, zsb), (xb, 22.0, zsb), "trim")
        chassis.add_quad((xa, -ya_w, zsa), (xa, -22.0, zsa), (xb, -22.0, zsb), (xb, -yb_w, zsb), "trim")

    def bus_side_y_at(x, z):
        dz_x, dy_x = arch_lift(x, (sp["wheel_x_r"],), sp["arch_r"], sp["flare"])
        zs_x = z0 + dz_x
        t = max(0.0, min(1.0, (z - zs_x) / max(1.0, zb - zs_x)))
        return (hw + dy_x * 0.5) * (1.0 - t) + hw * t

    # Right-reading "BAKERSFIELD UNIFIED • BUS 42" letterboard between upper rub rails on BOTH +Y and -Y sides!
    add_bilateral_side_decal(
        chassis, chassis,
        -150.0, 62.0, zb - 10.6, zb - 4.0,
        bus_side_y_at,
        wvs.RECT_DECAL_STRIP, n_segs=22, pad_px=4.0, y_ofs=0.42,
    )

    # Raised 3D Black Corrugated Rub-Rail Strips along Left & Right Bus Sides
    for sy in (-1.0, 1.0):
        x_end_rr = sp["x_door0"] - 0.5
        for rz in (zb - 1.5, zb - 13.5, zb - 26.5):
            chassis.add_box(x_body_r + 1.0, sy * hw, rz - 1.2, x_end_rr, sy * (hw + 0.9), rz + 1.2, "trim")

    # --- B. 7 Framed Split-Sash Passenger Windows per Side + Letterboard!
    yr = sp["y_roof"]  # 41.5
    z_win_top = 87.5
    z_roof_edge = 95.5
    win_x0 = -166.0
    win_x1 = 64.0
    n_wins = 7
    win_step = (win_x1 - win_x0) / n_wins

    for wi in range(n_wins):
        wxa = win_x0 + wi * win_step
        wxb = wxa + win_step
        chassis.add_framed_window(
            (wxb, hw, zb), (wxa, hw, zb), (wxa, yr + 1.5, z_win_top), (wxb, yr + 1.5, z_win_top),
            w_bot=1.8, w_right=2.4, w_top=2.2, w_left=2.4, recess=0.95,
            bot_reg="trim", right_reg="side", top_reg="side", left_reg="side",
        )
        z_sash = 0.5 * (zb + z_win_top)
        y_sash = 0.5 * (hw + yr + 1.5) - 0.4
        chassis.add_box(wxa + 2.2, y_sash - 0.5, z_sash - 0.6, wxb - 2.2, y_sash + 0.6, z_sash + 0.6, "chrome")

        chassis.add_framed_window(
            (wxa, -hw, zb), (wxb, -hw, zb), (wxb, -(yr + 1.5), z_win_top), (wxa, -(yr + 1.5), z_win_top),
            w_bot=1.8, w_right=2.4, w_top=2.2, w_left=2.4, recess=0.95,
            bot_reg="trim", right_reg="side", top_reg="side", left_reg="side",
        )
        chassis.add_box(wxa + 2.2, -(y_sash + 0.6), z_sash - 0.6, wxb - 2.2, -(y_sash - 0.5), z_sash + 0.6, "chrome")

    # Upper yellow letterboard band above windows (z_win_top .. z_roof_edge)
    chassis.add_quad((xc - 14.0, yr + 1.5, z_win_top), (x_body_r, yr + 1.5, z_win_top),
                     (x_body_r, yr, z_roof_edge), (xc - 14.0, yr, z_roof_edge), "side")
    chassis.add_quad((x_body_r, -(yr + 1.5), z_win_top), (xc - 14.0, -(yr + 1.5), z_win_top),
                     (xc - 14.0, -yr, z_roof_edge), (x_body_r, -yr, z_roof_edge), "side")

    # --- C. Driver Door (`door_l`) w/ EXACT POLAR-UV RED OCTAGONAL STOP SIGN + Curb Bi-Fold Entry Door (`door_r`)!
    door_l.add_framed_window(
        (sp["x_door1"], hw * 0.96, zb), (sp["x_door0"], hw, zb),
        (sp["x_door0"], yr + 1.5, z_win_top), (84.0, yr + 1.0, z_win_top),
        w_bot=1.6, w_right=2.4, w_top=2.2, w_left=3.0, recess=0.85,
        bot_reg="trim", right_reg="side", top_reg="side", left_reg="side", double_sided_frame=True,
    )

    # Swing-Out Red Octagonal STOP Sign on `door_l` with exact polar UVs (right-reading on BOTH front & back faces!)
    st_hinge_x, st_hinge_y, st_z = 75.5, hw + 1.2, zb - 2.5
    door_l.add_box(st_hinge_x - 1.5, hw - 0.5, st_z - 3.2, st_hinge_x + 1.5, st_hinge_y + 1.2, st_z + 3.2, "trim")
    r_oct = 9.4
    # Blade swings out from +Y driver side at 68 deg from body so it is prominently visible from front, side & rear!
    dir_x, dir_y = -0.38, 0.925
    nrm_x, nrm_y = 0.925, 0.38  # +X/+Y front-facing normal
    cx_oct = st_hinge_x + dir_x * (r_oct + 1.0)
    cy_oct = st_hinge_y + dir_y * (r_oct + 1.0)
    thk_oct = 0.35

    sx0, sy0, sx1, sy1 = wvs.RECT_STOP_SIGN
    scx_uv = 0.5 * (sx0 + sx1) / vs.W_ATLAS
    scy_uv = 0.5 * (sy0 + sy1) / vs.H_ATLAS
    sr_uv = 46.5 / vs.W_ATLAS

    oct_f, oct_b, uv_f, uv_b = [], [], [], []
    for k in range(8):
        ang = math.pi / 8.0 + k * math.pi / 4.0
        ca, sa = math.cos(ang), math.sin(ang)
        px = cx_oct + dir_x * (ca * r_oct)
        py = cy_oct + dir_y * (ca * r_oct)
        pz = st_z + sa * r_oct
        oct_f.append((px + nrm_x * thk_oct, py + nrm_y * thk_oct, pz))
        oct_b.append((px - nrm_x * thk_oct, py - nrm_y * thk_oct, pz))
        # Looking at front (+nrm) face: viewer's right is +dir (ca > 0), up is +Z (sa > 0)
        uv_f.append((scx_uv + ca * sr_uv, scy_uv - sa * sr_uv))
        # Looking at rear (-nrm) face: viewer's right is -dir (-ca > 0), up is +Z (sa > 0) -> ALSO reads "STOP"!
        uv_b.append((scx_uv - ca * sr_uv, scy_uv - sa * sr_uv))

    c_f = (cx_oct + nrm_x * thk_oct, cy_oct + nrm_y * thk_oct, st_z)
    c_b = (cx_oct - nrm_x * thk_oct, cy_oct - nrm_y * thk_oct, st_z)
    c_uv = (scx_uv, scy_uv)
    for k in range(8):
        kn = (k + 1) % 8
        add_uv_tri(door_l, c_f, oct_f[k], oct_f[kn], c_uv, uv_f[k], uv_f[kn], region="stop_sign")
        add_uv_tri(door_l, c_b, oct_b[kn], oct_b[k], c_uv, uv_b[kn], uv_b[k], region="stop_sign")
        door_l.add_quad(oct_f[k], oct_b[k], oct_b[kn], oct_f[kn], "trim")

    # Driver West-Coast Bus Mirror
    door_l.add_box(91.0, hw - 1.0, zb + 3.0, 94.0, hw + 9.0, zb + 4.8, "trim")
    door_l.add_box(90.0, hw + 7.5, zb + 1.0, 95.0, hw + 11.0, zb + 16.0, "trim", {"-x": "glass"})

    # Curb-side 2-Leaf Bi-Fold Glass Entry Door (`door_r`: x = 66..96, z = z0+2 .. z_win_top)
    for leaf_xa, leaf_xb in ((66.2, 80.8), (81.2, 95.8)):
        door_r.add_framed_window(
            (leaf_xa, -hw, z0 + 3.0), (leaf_xb, -hw, z0 + 3.0),
            (leaf_xb, -hw + 0.5, zb - 1.0), (leaf_xa, -hw + 0.5, zb - 1.0),
            w_bot=2.5, w_right=2.0, w_top=2.2, w_left=2.0, recess=0.70,
            bot_reg="trim", right_reg="trim", top_reg="trim", left_reg="trim", double_sided_frame=True,
        )
        door_r.add_framed_window(
            (leaf_xa, -hw + 0.5, zb - 1.0), (leaf_xb, -hw + 0.5, zb - 1.0),
            (leaf_xb, -(yr + 1.5), z_win_top), (leaf_xa, -(yr + 1.5), z_win_top),
            w_bot=2.0, w_right=2.0, w_top=2.4, w_left=2.0, recess=0.70,
            bot_reg="trim", right_reg="side", top_reg="side", left_reg="side", double_sided_frame=True,
        )

    # --- D. Crowned Bus Roof + RIGHT-READING Front & Rear "SCHOOL BUS" 8-Way Flasher Header Caps!
    xr0, xr1 = sp["x_roof0"], sp["x_roof1"]  # -170 .. 84
    for j in range(6):
        ya = -yr + 2.0 * yr * j / 6.0
        yb_s = -yr + 2.0 * yr * (j + 1) / 6.0
        za = z_roof_edge + (1.0 - (ya / yr) ** 2) * 6.5
        zbs = z_roof_edge + (1.0 - (yb_s / yr) ** 2) * 6.5
        chassis.add_quad((xr0, ya, za), (xr1, ya, za), (xr1, yb_s, zbs), (xr0, yb_s, zbs), "top")
        # Front roof header (+X normal): map with rear_uv(sp, -y, z) so "SCHOOL BUS" reads 100% left-to-right!
        add_uv_quad(
            chassis,
            (xr1, ya, z_win_top), (xr1, yb_s, z_win_top), (xr1, yb_s, zbs), (xr1, ya, za),
            vs.rear_uv(sp, -ya, z_win_top),
            vs.rear_uv(sp, -yb_s, z_win_top),
            vs.rear_uv(sp, -yb_s, zbs),
            vs.rear_uv(sp, -ya, za),
            region="front_header",
        )
        # Rear roof header (-X normal): standard rear_uv(sp, y, z) reads 100% left-to-right!
        chassis.add_quad((xr0, yb_s, z_win_top), (xr0, ya, z_win_top), (xr0, ya, za), (xr0, yb_s, zbs), "rear")

    # Black warning-flasher eyebrow visors ABOVE the flashers on front & rear roof headers
    for sy in (-1.0, 1.0):
        chassis.add_box(xr1 - 0.5, sy * 22.0, z_roof_edge + 3.2, xr1 + 3.0, sy * 39.5, z_roof_edge + 4.6, "trim")
        chassis.add_box(xr0 - 3.0, sy * 22.0, z_roof_edge + 3.2, xr0 + 0.5, sy * 39.5, z_roof_edge + 4.6, "trim")

    # Split 2-Pane Raked School Bus Windshield (`xc = 100 -> xr1 = 84`)
    for (wya, wyb) in ((-hw * 0.94, -1.2), (1.2, hw * 0.94)):
        tya, tyb = wya * (yr / (hw * 0.94)), wyb * (yr / (hw * 0.94))
        chassis.add_framed_window(
            (xc, wya, zb), (xc, wyb, zb), (xr1, tyb, z_win_top), (xr1, tya, z_win_top),
            w_bot=2.2, w_right=2.6, w_top=2.6, w_left=2.6, recess=0.95,
            bot_reg="trim", right_reg="trim", top_reg="side", left_reg="side",
        )
    chassis.add_box(xc - 2.0, -1.8, zb, xr1 + 1.0, 1.8, z_win_top, "trim")

    # --- E. Seamless Type-C Front Nose Fenders (Flush w/ Sloped Hood!), Engine Bay & Tilt-Hood (`hood`)!
    y_hood_f = hw * 0.62
    y_hood_c = hw * 0.78
    add_curved_fascia(chassis, x_nose, 2.2, hw * 0.94, z_bmp, zn_top + 1.8, is_front=True, n_strips=6)

    def nose_profile(x):
        tx = max(0.0, min(1.0, (x - xc) / max(1.0, x_nose - xc)))
        yh_in = y_hood_c + (y_hood_f - y_hood_c) * tx
        zh_top = zb + (zn_top - zb) * (tx ** 1.1)
        dz_a, dy_a = arch_lift(x, (sp["wheel_x_f"],), sp["arch_r"], sp["flare"])
        z_flr = max(z0 + dz_a, z_bmp if x > x_nose - 5.0 else z0 + dz_a)
        y_out = hw * (0.98 - 0.04 * tx) + dy_a * 0.65
        return yh_in, y_out, min(zh_top - 3.5, z_flr), zh_top

    xs_nose = [round(xc + (x_nose - xc) * k / 12.0, 2) for k in range(13)]
    for k in range(len(xs_nose) - 1):
        xa, xb = xs_nose[k], xs_nose[k + 1]
        yia, yoa, zsa, zta = nose_profile(xa)
        yib, yob, zsb, ztb = nose_profile(xb)
        # Left (+Y) & Right (-Y) sculpted front fenders meeting hood seam 100% flush!
        chassis.add_quad((xb, yob, zsb), (xa, yoa, zsa), (xa, yoa * 0.98, zta), (xb, yob * 0.98, ztb), "side")
        chassis.add_quad((xa, -yoa, zsa), (xb, -yob, zsb), (xb, -yob * 0.98, ztb), (xa, -yoa * 0.98, zta), "side")
        # Top fender crown from outer fender lip inward to hood seam
        chassis.add_quad((xa, yia, zta - 0.3), (xb, yib, ztb - 0.3), (xb, yob * 0.98, ztb), (xa, yoa * 0.98, zta), "top")
        chassis.add_quad((xa, -yoa * 0.98, zta), (xb, -yob * 0.98, ztb), (xb, -yib, ztb - 0.3), (xa, -yia, zta - 0.3), "top")
        # Under-fender wheelhouse splash shield
        chassis.add_quad((xa, 20.0, zsa), (xa, yoa, zsa), (xb, yob, zsb), (xb, 20.0, zsb), "trim")
        chassis.add_quad((xa, -yoa, zsa), (xa, -20.0, zsa), (xb, -20.0, zsb), (xb, -yob, zsb), "trim")
        chassis.add_quad((xa, -20.0, z0), (xa, 20.0, z0), (xb, 20.0, z0), (xb, -20.0, z0), "bottom")

    # Recessed turbo-diesel inline-6 engine block + engine bay tray under hood
    chassis.add_box(xc + 2.0, -y_hood_f * 0.92, z_bmp, x_nose - 2.5, y_hood_f * 0.92, z_bmp + 2.0, "trim")
    chassis.add_box(xc + 5.0, -14.0, z_bmp + 2.0, x_nose - 8.0, 14.0, zn_top - 1.5, "engine")

    hood_grid = []
    for i in range(5):
        tx = i / 4.0
        xh = (xc + 0.4) + (x_nose + 0.4 - (xc + 0.4)) * tx
        yh_w = y_hood_c + (y_hood_f - y_hood_c) * tx
        zh_b = zb + (zn_top - zb) * (tx ** 1.1)
        row = []
        for j in range(5):
            ty = -1.0 + 2.0 * j / 4.0
            row.append((xh, yh_w * ty, zh_b + (1.0 - ty * ty) * 2.6))
        hood_grid.append(row)
    add_painted_panel(hood, hood_grid, (0.0, 0.0, -1.5), outer_region="top", inner_region="trim", edge_region="top")

    # Front Heavy Steel Channel Bumper + Yellow Crossing Gate Arm + Fender Crossover Mirrors!
    add_wraparound_bumper(bumper_f, x_nose - 0.5, x1 + 1.2, 2.0, hw * 0.98, z0, z_bmp, wing_len=6.0, is_front=True, top_reg="trim")
    bumper_f.add_box(x1 + 1.5, -hw * 0.88, z0 + 2.0, x1 + 4.2, -16.0, z0 + 4.8, "side")
    for sy in (-1.0, 1.0):
        bumper_f.add_cylinder((x_nose - 4.0, sy * (hw * 0.86), zn_top - 1.0), (x_nose + 2.0, sy * (hw * 0.94), zn_top + 9.5), 0.8, 0.7, segs=6, region="trim")
        bumper_f.add_cylinder((x_nose + 1.5, sy * (hw * 0.94), zn_top + 9.5), (x_nose + 3.2, sy * (hw * 0.94), zn_top + 9.5), 4.2, 4.2, segs=10, region="chrome")

    # --- F. Rear Bus Bulkhead + EXTRA PART (Rear Emergency Exit Door + 2 Roof Escape Hatches!)
    for sy in (-1.0, 1.0):
        ya, yb_p = sorted([sy * 17.5, sy * hw])
        chassis.add_quad((x_body_r, yb_p, z_bmp), (x_body_r, ya, z_bmp), (x_body_r, ya, z_win_top), (x_body_r, yb_p, z_win_top), "rear")
    add_wraparound_bumper(bumper_r, x_body_r + 0.5, x0 - 1.2, -1.6, hw * 0.98, z0, z_bmp, wing_len=7.0, is_front=False, top_reg="trim")

    # Center Rear Emergency Exit Door + 2 White Roof Escape Hatches (blow clean off on explosion!)
    extra.add_box(x_body_r - 1.2, -17.5, z_bmp + 1.5, x_body_r + 1.2, 17.5, z_win_top - 1.5, "trim", {"-x": "rear", "+x": "int_wall"})
    for hx_w in (-105.0, -15.0):
        extra.add_box(hx_w - 13.0, -13.0, z1 - 0.8, hx_w + 13.0, 13.0, z1 + 2.2, "trim", {"+z": "top"})

    # --- G. Full Interior School Bus Bench Seats & Central Aisle!
    z_bus_flr = z0 + 6.0
    chassis.add_quad((x_body_r + 2.0, -hw * 0.88, z_bus_flr), (xc - 4.0, -hw * 0.88, z_bus_flr),
                     (xc - 4.0, hw * 0.88, z_bus_flr), (x_body_r + 2.0, hw * 0.88, z_bus_flr), "int_floor")
    chassis.add_quad((x_body_r + 3.0, yr - 2.0, z_roof_edge - 1.0), (xr1 - 3.0, yr - 2.0, z_roof_edge - 1.0),
                     (xr1 - 3.0, -(yr - 2.0), z_roof_edge - 1.0), (x_body_r + 3.0, -(yr - 2.0), z_roof_edge - 1.0), "int_wall")
    for ri in range(7):
        bx = -152.0 + ri * 31.0
        for sy in (-1.0, 1.0):
            ya, yb_s = sorted([sy * 11.5, sy * (hw - 4.5)])
            chassis.add_box(bx, ya, z_bus_flr + 4.0, bx + 13.5, yb_s, z_bus_flr + 9.0, "int_seat")
            chassis.add_box(bx - 2.5, ya, z_bus_flr + 9.0, bx + 2.0, yb_s, zb + 6.5, "int_seat")
    chassis.add_box(84.0, -hw * 0.82, z_bus_flr, xc - 1.5, hw * 0.82, zb - 1.5, "int_dash")
    chassis.add_box(68.0, 14.0, z_bus_flr + 3.0, 82.0, 32.0, zb + 8.0, "int_seat")
    chassis.add_cylinder((84.0, 23.0, zb + 1.5), (77.0, 23.0, zb + 6.5), 6.8, 6.8, segs=10, region="trim")

    # Long commercial C-channel frame rails, midship 100-gal diesel tank, axles & tailpipe
    for sy in (-1.0, 1.0):
        chassis.add_box(x_body_r + 12.0, sy * 17.5 - 2.5, z0 - 2.2, x_nose - 10.0, sy * 17.5 + 2.5, z0 + 1.5, "trim")
    chassis.add_box(-38.0, -hw * 0.82, z0 - 3.5, 16.0, -21.0, z0 + 6.0, "trim")
    for wx in (sp["wheel_x_f"], sp["wheel_x_r"]):
        chassis.add_cylinder((wx, -sp["wheel_y"] + 2.0, sp["wheel_r"]), (wx, sp["wheel_y"] - 2.0, sp["wheel_r"]), 2.4, 2.4, segs=8, region="trim")
    detail.add_cylinder((-145.0, 22.0, z0 - 1.0), (x0 - 4.0, 26.0, z0 - 1.8), 2.5, 2.7, segs=10, region="chrome")

    chassis_dict = chassis.export_dict(custom_origin=(0.0, 0.0, 0.0))
    wreck_dict = _build_crumpled_wreck(chassis_dict, sp, seed=601)

    w_l = build_3d_wheel("wl", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], True, sp)
    w_r = build_3d_wheel("wr", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], False, sp)

    parts = {
        "chassis": chassis_dict,
        "wreck_chassis": wreck_dict,
        "hood": hood.export_dict(hinge_pivot=(xc, 0.0, zb)),
        "door_l": door_l.export_dict(),
        "door_r": door_r.export_dict(),
        "extra_part": extra.export_dict(),
        "bumper_f": bumper_f.export_dict(),
        "bumper_r": bumper_r.export_dict(),
        "detail_vib": detail.export_dict(),
        "wheel_fl": _place_wheel(w_l, "wheel_fl", sp["wheel_x_f"], sp["wheel_y"], sp["wheel_r"]),
        "wheel_fr": _place_wheel(w_r, "wheel_fr", sp["wheel_x_f"], -sp["wheel_y"], sp["wheel_r"]),
        "wheel_rl": _place_wheel(w_l, "wheel_rl", sp["wheel_x_r"], sp["wheel_y"] + 1.5, sp["wheel_r"]),
        "wheel_rr": _place_wheel(w_r, "wheel_rr", sp["wheel_x_r"], -(sp["wheel_y"] + 1.5), sp["wheel_r"]),
        "wheel_rl2": _place_wheel(w_l, "wheel_rl2", sp["wheel_x_r"], sp["wheel_y_inner"], sp["wheel_r"]),
        "wheel_rr2": _place_wheel(w_r, "wheel_rr2", sp["wheel_x_r"], -sp["wheel_y_inner"], sp["wheel_r"]),
    }
    for si, sd in enumerate(_build_shrapnel_set(sp, seed=602, count=12)):
        parts[f"shrap_{si}"] = sd
    return {"spec": sp, "parts": parts}


# ==============================================================================
# 3. REALISTIC V8 STREET MUSCLE FASTBACK CAR ("gtcar")
# ==============================================================================
def build_gtcar():
    sp = dict(wvs.get_wild_spec("gtcar"))
    x0, x1, hw = sp["x0"], sp["x1"], sp["hw"]
    z0, z_bmp, zb, z1 = sp["z_bot"], sp["z_bmp"], sp["z_belt"], sp["z_roof"]
    zn_top, zr_top = sp["z_nose_top"], sp["z_rear_top"]
    wxs = (sp["wheel_x_f"], sp["wheel_x_r"])

    chassis = PartBuilder("chassis", sp)
    hood = PartBuilder("hood", sp)
    door_l = PartBuilder("door_l", sp)
    door_r = PartBuilder("door_r", sp)
    extra = PartBuilder("extra_part", sp)
    bumper_f = PartBuilder("bumper_f", sp)
    bumper_r = PartBuilder("bumper_r", sp)
    detail = PartBuilder("detail_vib", sp)

    x_nose = x1 - 3.0
    x_tail = x0 + 2.5

    xs = sorted(set(
        [round(x_tail + (x_nose - x_tail) * i / 36.0, 2) for i in range(37)]
        + [sp["x_door0"], sp["x_door1"], sp["x_cowl"], sp["x_cab_rear"]]
    ))

    def side_profile(x):
        t_f = max(0.0, (x - (x_nose - 22.0)) / 22.0)
        t_r = max(0.0, ((x_tail + 15.0) - x) / 15.0)
        taper = 1.0 - 0.10 * (t_f ** 1.6) - 0.05 * (t_r ** 1.6)
        dz_a, dy_f = arch_lift(x, wxs, sp["arch_r"], sp["flare"])
        haunch = 2.2 * math.exp(-(((x - (-52.0)) / 24.0) ** 2))
        if x > sp["x_cowl"]:
            ft = min(1.0, (x - sp["x_cowl"]) / max(1.0, x_nose - sp["x_cowl"]))
            zb_x = zb + (zn_top - zb) * (ft ** 1.18)
        elif x < sp["x_cab_rear"]:
            rt = min(1.0, (sp["x_cab_rear"] - x) / max(1.0, sp["x_cab_rear"] - x_tail))
            zb_x = zb + (zr_top - zb) * rt
        else:
            zb_x = zb
        y_sh = hw * taper + dy_f + haunch
        y_sill = hw * 0.92 * taper + dy_f * 0.4 + haunch * 0.35
        y_blt = hw * 0.94 * taper + haunch * 0.55
        z_flr = z0 + dz_a
        if x > x_nose - 5.5 or x < x_tail + 5.5:
            z_flr = max(z_flr, z_bmp - 0.5)
        return y_sill, y_sh, y_blt, min(zb_x - 4.0, z_flr), zb_x

    def side_y_at(x, z):
        ys, ysh, yblt, zs, zbx = side_profile(x)
        zm = 0.5 * (zs + zbx)
        if z <= zm:
            t = max(0.0, min(1.0, (z - zs) / max(0.5, zm - zs)))
            return ys + (ysh - ys) * t
        t = max(0.0, min(1.0, (z - zm) / max(0.5, zbx - zm)))
        return ysh + (yblt - ysh) * t

    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        xm = 0.5 * (xa + xb)
        ys_a, ysh_a, yb_a, zs_a, zba = side_profile(xa)
        ys_b, ysh_b, yb_b, zs_b, zbb = side_profile(xb)
        zmid_a = 0.5 * (zs_a + zba)
        zmid_b = 0.5 * (zs_b + zbb)

        in_door = (xm > sp["x_door0"] + 0.05) and (xm < sp["x_door1"] - 0.05)
        tl = door_l if in_door else chassis
        tr = door_r if in_door else chassis

        tl.add_quad((xb, ys_b, zs_b), (xa, ys_a, zs_a), (xa, ysh_a, zmid_a), (xb, ysh_b, zmid_b), "auto")
        tl.add_quad((xb, ysh_b, zmid_b), (xa, ysh_a, zmid_a), (xa, yb_a, zba), (xb, yb_b, zbb), "auto")
        tr.add_quad((xa, -ys_a, zs_a), (xb, -ys_b, zs_b), (xb, -ysh_b, zmid_b), (xa, -ysh_a, zmid_a), "auto")
        tr.add_quad((xa, -ysh_a, zmid_a), (xb, -ysh_b, zmid_b), (xb, -yb_b, zbb), (xa, -yb_a, zba), "auto")

        if in_door:
            yi = 2.4
            door_l.add_quad((xa, ys_a - yi, zs_a + 1.2), (xb, ys_b - yi, zs_b + 1.2), (xb, yb_b - yi, zbb - 0.4), (xa, yb_a - yi, zba - 0.4), "interior")
            door_l.add_quad((xa, yb_a, zba), (xa, yb_a - yi, zba - 0.4), (xb, yb_b - yi, zbb - 0.4), (xb, yb_b, zbb), "trim")
            door_r.add_quad((xb, -ys_b + yi, zs_b + 1.2), (xa, -ys_a + yi, zs_a + 1.2), (xa, -yb_a + yi, zba - 0.4), (xb, -yb_b + yi, zbb - 0.4), "interior")
            door_r.add_quad((xb, -yb_b, zbb), (xb, -yb_b + yi, zbb - 0.4), (xa, -yb_a + yi, zba - 0.4), (xa, -yb_a, zba), "trim")

        yw = 18.0
        chassis.add_quad((xa, -yw, z0), (xa, yw, z0), (xb, yw, z0), (xb, -yw, z0), "bottom")
        chassis.add_quad((xa, yw, zs_a), (xa, ys_a, zs_a), (xb, ys_b, zs_b), (xb, yw, zs_b), "trim")
        chassis.add_quad((xa, -ys_a, zs_a), (xa, -yw, zs_a), (xb, -yw, zs_b), (xb, -ys_b, zs_b), "trim")

    # Right-reading "5.0 SUPERCHARGED" front fender badge & "GT • V8 PERFORMANCE" door rocker decal on BOTH sides!
    add_bilateral_side_decal(chassis, chassis, 31.0, 38.6, zb - 6.8, zb - 2.6, side_y_at, wvs.RECT_BADGE_A, n_segs=3, pad_px=4.0, y_ofs=0.40)
    add_bilateral_side_decal(door_l, door_r, -11.5, 24.5, z0 + 5.2, z0 + 9.2, side_y_at, wvs.RECT_DECAL_STRIP, n_segs=6, pad_px=4.0, y_ofs=0.40)

    # Carbon side-skirt blades
    for sy in (-1.0, 1.0):
        chassis.add_box(-38.0, sy * (hw - 1.5), z0 - 0.8, 38.0, sy * (hw + 1.4), z0 + 1.0, "trim")

    # Front Fascia, Aggressive Chin-Splitter Bumper & V8 Engine Bay
    _, _, yb_f, _, _ = side_profile(x_nose)
    add_curved_fascia(chassis, x_nose, 2.6, yb_f, z_bmp, zn_top + 1.8, is_front=True, n_strips=6)
    add_wraparound_bumper(bumper_f, x_nose - 0.5, x1 + 1.0, 2.8, hw * 0.96, z0, z_bmp, wing_len=7.0, is_front=True, top_reg="top")
    bumper_f.add_box(x1 - 3.5, -hw * 0.95, z0 - 1.4, x1 + 4.8, hw * 0.95, z0 + 0.5, "trim")

    xc = sp["x_cowl"]
    ye = yb_f * 0.82
    ze_flr = zn_top - 10.0
    chassis.add_box(xc + 2.0, -ye, ze_flr, x_nose - 2.5, ye, ze_flr + 2.0, "trim")
    chassis.add_box(xc + 6.0, -13.5, ze_flr + 2.0, x_nose - 10.0, 13.5, zn_top - 1.0, "engine")
    _, _, yb_cowl, _, zb_cowl = side_profile(xc)
    for sgn_y in (-1.0, 1.0):
        if sgn_y > 0:
            chassis.add_quad((xc, ye, zb_cowl - 0.4), (x_nose, ye, zn_top - 0.4), (x_nose, yb_f, zn_top), (xc, yb_cowl, zb_cowl), "top")
        else:
            chassis.add_quad((xc, -yb_cowl, zb_cowl), (x_nose, -yb_f, zn_top), (x_nose, -ye, zn_top - 0.4), (xc, -ye, zb_cowl - 0.4), "top")

    # Twin-Scoop Cowl-Induction V8 Muscle Hood (painted rolled edges so racing stripes never break!)
    hood_grid = []
    for i in range(6):
        tx = i / 5.0
        xh = (xc + 0.6) + (x_nose + 0.6 - (xc + 0.6)) * tx
        _, _, yb_h, _, zbh = side_profile(xh)
        yh_max = yb_h * 0.85
        row = []
        for j in range(7):
            ty = -1.0 + 2.0 * j / 6.0
            crown = (1.0 - ty * ty) * 2.2
            if abs(ty) < 0.46 and 0.12 < tx < 0.84:
                crown += 2.1 * math.sin(math.pi * (tx - 0.12) / 0.72)
            row.append((xh, yh_max * ty, zbh + crown))
        hood_grid.append(row)
    add_painted_panel(hood, hood_grid, (0.0, 0.0, -1.4), outer_region="top", inner_region="trim", edge_region="top")

    # Fastback Cabin, Cockpit Interior, Doors & Rear Deck
    z_cab_flr = z0 + 3.5
    chassis.add_box(sp["x_cab_rear"] + 8.0, -hw * 0.70, z_cab_flr, xc - 2.0, hw * 0.70, z_cab_flr + 2.0, "int_floor")
    chassis.add_box(xc - 13.0, -hw * 0.68, z_cab_flr + 2.0, xc - 2.0, hw * 0.68, zb + 1.0, "int_dash")
    chassis.add_cylinder((xc - 13.5, 13.5, zb - 1.0), (xc - 17.0, 13.5, zb + 1.2), 4.8, 4.8, segs=10, region="trim")
    for sy in (-13.5, 13.5):
        chassis.add_box(-8.0, sy - 8.0, z_cab_flr + 2.0, 10.0, sy + 8.0, zb - 3.0, "int_seat")
        chassis.add_box(-11.0, sy - 7.5, zb - 3.0, -4.5, sy + 7.5, zb + 10.5, "int_seat")

    yr = sp["y_roof"]
    xr0, xr1 = sp["x_roof0"], sp["x_roof1"]
    zr_edge = z1 - 1.5
    for j in range(6):
        ya = -yr + 2.0 * yr * j / 6.0
        yb_s = -yr + 2.0 * yr * (j + 1) / 6.0
        za = zr_edge + (1.0 - (ya / yr) ** 2) * 1.6
        zbs = zr_edge + (1.0 - (yb_s / yr) ** 2) * 1.6
        chassis.add_quad((xr0, ya, za), (xr1, ya, za), (xr1, yb_s, zbs), (xr0, yb_s, zbs), "top")
        chassis.add_quad((xr1, ya, zr_edge), (xr1, yb_s, zr_edge), (xr1, yb_s, zbs), (xr1, ya, za), "top")
        chassis.add_quad((xr0, yb_s, zr_edge), (xr0, ya, zr_edge), (xr0, ya, za), (xr0, yb_s, zbs), "top")

    yb_cab = side_profile(6.0)[2]
    _, _, yb_cr, _, zb_cr = side_profile(sp["x_cab_rear"])
    chassis.add_framed_window((xc, -yb_cowl, zb), (xc, yb_cowl, zb), (xr1, yr, zr_edge), (xr1, -yr, zr_edge),
                              w_bot=2.0, w_right=4.0, w_top=2.5, w_left=4.0, recess=0.90, bot_reg="trim", top_reg="top")
    chassis.add_framed_window((sp["x_cab_rear"], yb_cr, zb_cr), (sp["x_cab_rear"], -yb_cr, zb_cr), (xr0, -yr, zr_edge), (xr0, yr, zr_edge),
                              w_bot=2.4, w_right=6.0, w_top=2.6, w_left=6.0, recess=0.85, bot_reg="top", top_reg="top")
    chassis.add_framed_window((-14.0, yb_cab, zb), (sp["x_cab_rear"], yb_cr, zb_cr), (xr0, yr, zr_edge), (-14.0, yr, zr_edge),
                              w_bot=1.4, w_right=7.0, w_top=2.4, w_left=2.2, recess=0.75, bot_reg="trim", left_reg="trim")
    chassis.add_framed_window((sp["x_cab_rear"], -yb_cr, zb_cr), (-14.0, -yb_cab, zb), (-14.0, -yr, zr_edge), (xr0, -yr, zr_edge),
                              w_bot=1.4, w_right=2.2, w_top=2.4, w_left=7.0, recess=0.75, bot_reg="trim", right_reg="trim")

    door_l.add_framed_window((27.0, yb_cowl, zb), (-14.0, yb_cab, zb), (-14.0, yr, zr_edge), (xr1, yr, zr_edge),
                             w_bot=1.2, w_right=2.2, w_top=2.0, w_left=2.8, recess=0.70, bot_reg="trim", right_reg="trim", double_sided_frame=True)
    door_r.add_framed_window((-14.0, -yb_cab, zb), (27.0, -yb_cowl, zb), (xr1, -yr, zr_edge), (-14.0, -yr, zr_edge),
                             w_bot=1.2, w_right=2.8, w_top=2.0, w_left=2.2, recess=0.70, bot_reg="trim", left_reg="trim", double_sided_frame=True)
    for d_pb, sy in ((door_l, 1.0), (door_r, -1.0)):
        d_pb.add_box(19.0, sy * (yb_cab - 0.5), zb + 0.8, 24.5, sy * (yb_cab + 6.0), zb + 4.8, "auto", {"-x": "glass"})

    _, _, yb_r, _, _ = side_profile(x_tail)
    add_curved_fascia(chassis, x_tail, -2.2, yb_r, z_bmp, zr_top, is_front=False, n_strips=6)
    add_wraparound_bumper(bumper_r, x_tail + 0.5, x0 - 0.8, -2.2, hw * 0.96, z0, z_bmp, wing_len=6.5, is_front=False, top_reg="top")
    chassis.add_box(-93.0, -yb_r * 0.80, zr_top - 7.5, sp["x_cab_rear"] - 1.0, yb_r * 0.80, zr_top - 5.5, "interior")

    # EXTRA PART: Sculpted Trunk Decklid + Raised Pedestal Muscle Wing Spoiler (painted rolled edges!)
    tr_grid = []
    for i in range(4):
        tx = i / 3.0
        xt = (x_tail + 0.6) + (sp["x_cab_rear"] - (x_tail + 0.6)) * tx
        _, _, ybt, _, zbt = side_profile(xt)
        yt_m = ybt * 0.90
        tr_grid.append([(xt, yt_m * (-1.0 + 2.0 * j / 6.0), zbt + 1.2 * (1.0 - (-1.0 + 2.0 * j / 6.0) ** 2)) for j in range(7)])
    add_painted_panel(extra, tr_grid, (0.0, 0.0, -1.3), outer_region="top", inner_region="trim", edge_region="top")

    zw = zr_top + 7.5
    yw = yb_r * 0.94
    for sy in (-1.0, 1.0):
        extra.add_box(-93.0, sy * (yw * 0.62) - 1.2, zr_top, -83.0, sy * (yw * 0.62) + 1.2, zw, "trim")
    wing_grid = [
        [(-95.5, -yw + 2.0 * yw * j / 6.0, zw + 0.9 + 0.5 * (1.0 - (-1.0 + 2.0 * j / 6.0) ** 2)) for j in range(7)],
        [(-83.5, -yw + 2.0 * yw * j / 6.0, zw - 0.6 + 0.4 * (1.0 - (-1.0 + 2.0 * j / 6.0) ** 2)) for j in range(7)],
    ]
    add_painted_panel(extra, wing_grid, (0.0, 0.0, -1.1), outer_region="top", inner_region="trim", edge_region="top")

    # Quad Chrome Exhaust Tips + Frame Rails & Axles
    for sy in (-1.0, 1.0):
        for dy in (-3.2, 3.2):
            detail.add_cylinder((-78.0, sy * 20.0 + dy, z0 + 0.5), (x0 - 3.2, sy * 20.0 + dy, z0 - 0.3), 1.9, 2.1, segs=10, region="chrome")
        chassis.add_box(x_tail + 10.0, sy * 14.5 - 2.0, z0 - 1.0, x_nose - 10.0, sy * 14.5 + 2.0, z0 + 1.5, "trim")
    for wx in wxs:
        chassis.add_cylinder((wx, -sp["wheel_y"] + 2.5, sp["wheel_r"]), (wx, sp["wheel_y"] - 2.5, sp["wheel_r"]), 1.7, 1.7, segs=8, region="trim")

    chassis_dict = chassis.export_dict(custom_origin=(0.0, 0.0, 0.0))
    wreck_dict = _build_crumpled_wreck(chassis_dict, sp, seed=701)

    w_l = build_3d_wheel("wl", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], True, sp)
    w_r = build_3d_wheel("wr", sp["wheel_r"], sp["wheel_w"], sp["dish"], sp["rim_ratio"], False, sp)

    parts = {
        "chassis": chassis_dict,
        "wreck_chassis": wreck_dict,
        "hood": hood.export_dict(hinge_pivot=(xc, 0.0, zb_cowl)),
        "door_l": door_l.export_dict(),
        "door_r": door_r.export_dict(),
        "extra_part": extra.export_dict(),
        "bumper_f": bumper_f.export_dict(),
        "bumper_r": bumper_r.export_dict(),
        "detail_vib": detail.export_dict(),
        "wheel_fl": _place_wheel(w_l, "wheel_fl", sp["wheel_x_f"], sp["wheel_y"], sp["wheel_r"]),
        "wheel_fr": _place_wheel(w_r, "wheel_fr", sp["wheel_x_f"], -sp["wheel_y"], sp["wheel_r"]),
        "wheel_rl": _place_wheel(w_l, "wheel_rl", sp["wheel_x_r"], sp["wheel_y"], sp["wheel_r"]),
        "wheel_rr": _place_wheel(w_r, "wheel_rr", sp["wheel_x_r"], -sp["wheel_y"], sp["wheel_r"]),
    }
    for si, sd in enumerate(_build_shrapnel_set(sp, seed=702, count=12)):
        parts[f"shrap_{si}"] = sd
    return {"spec": sp, "parts": parts}


def main():
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    builders = {
        "hdtruck": build_hdtruck,
        "schoolbus": build_schoolbus,
        "gtcar": build_gtcar,
    }
    out = {}
    for k, fn in builders.items():
        vdata = fn()
        parts = vdata["parts"]
        intact_v = sum(len(p["verts"]) for nm, p in parts.items() if nm != "wreck_chassis" and not nm.startswith("shrap_"))
        intact_t = sum(len(p["tris"]) for nm, p in parts.items() if nm != "wreck_chassis" and not nm.startswith("shrap_"))
        n_wheels = sum(1 for nm in parts if nm.startswith("wheel_"))
        print(f"  [{k:9s}] intact={intact_v:4d} verts / {intact_t:4d} tris | wheels={n_wheels} | wreck={len(parts['wreck_chassis']['verts']):4d} verts")
        out[k] = vdata
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(f"Wrote {OUT_JSON} ({os.path.getsize(OUT_JSON) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
