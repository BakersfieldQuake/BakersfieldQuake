"""make_midair.py — Generates `out/maps/midair.map` (Valve 220 format for ericw-tools `-bsp2`):
A sleek nighttime circular midair arena (`maps/midair.bsp` + `.lit`) with a glowing central pit
and a super-high sky jump pad at the bottom of the hole.

Usage:
    python make_midair.py [out/maps/midair.map]
Optional env:
    MIDAIR_START="x y z yaw [pitch]"   -> overrides info_player_start for automated camera screenshots
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "maps", "midair.map")
WAD_PATH = os.path.join(HERE, "out", "maps", "midair.wad")

# Read exact WAD2 miptex sizes so planar & cylindrical UVs match both ericw light and DarkPlaces HD PNGs
TEXSIZE = {}
with open(WAD_PATH, "rb") as _f:
    _magic, _num, _dir_ofs = struct.unpack("<4sii", _f.read(12))
    assert _magic == b"WAD2", f"Bad WAD header in {WAD_PATH}"
    _f.seek(_dir_ofs)
    _entries = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_num)]
    for _pos, _, _, _, _, _, _raw in _entries:
        _f.seek(_pos)
        _, _w, _h = struct.unpack("<16s2I", _f.read(24))
        TEXSIZE[_raw.split(b"\0")[0].decode()] = (_w, _h)

# ==============================================================================
# Arena Dimensions (Quake units; player = 32x32x56, rocket = 1000 u/s)
# ==============================================================================
N_SEG = 48                  # 48-sided smooth circle (7.5 deg per facet)

R_HOLE = 192                # Central hole radius (384 units = 32 ft across)
R_COLLAR = 272              # Hazard/launch glow collar around central hole
R_FLOOR_1 = 560             # Inner dark slate floor ring
R_RING_C = 584              # Flush glowing cyan range ring (R = 560..584)
R_FLOOR_2 = 944             # Mid dark slate floor ring
R_RING_M = 968              # Flush glowing violet/magenta range ring (R = 944..968)
R_FLOOR_3 = 1280            # Outer main circular floor edge
R_STEP_1 = 1408             # Outer amphitheater terrace step 1 (z = +16)
R_STEP_2 = 1536             # Outer amphitheater terrace step 2 (z = +32)
R_WALL_OUT = 1600           # Curved perimeter parapet outer radius

Z_BASE = -288               # Bottom structural underside of floating colosseum disc
Z_PAD = -224                # Top surface of the jump pad at the bottom of the central hole
Z_FLOOR = 0                 # Main circular arena floor height
Z_STEP_1 = 16               # Terrace step 1
Z_STEP_2 = 32               # Terrace step 2
Z_WALL_TOP = 176            # Curved perimeter parapet coping height (keeps 360-deg night sky wide open!)

HULL_HALF = 1856            # Sealed outer skybox X/Y half-extent
HULL_Z_MIN = -384           # Sealed outer skybox floor
HULL_Z_MAX = 6144           # Tall sky ceiling (6,144 units above floor; jump pad apex ~2,370u!)
HULL_THICK = 64

GROUPS = {"world": [], "phong": [], "detail": []}
ENTS = []


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def uv_planar_top(tex, tile_units=256.0, centered_span=None):
    """Valve 220 horizontal UV: u along +X, v along -Y, centered at world (0, 0)."""
    tw, th = TEXSIZE[tex]
    if centered_span is not None:
        sx = centered_span / tw
        sy = centered_span / th
    else:
        sx = tile_units / tw
        sy = tile_units / th
    uoff = tw / 2.0
    voff = th / 2.0
    return f"{tex} [ 1 0 0 {uoff:.4f} ] [ 0 -1 0 {voff:.4f} ] 0 {sx:.6f} {sy:.6f}"


def uv_wall_chord(tex, p0, p1, arc_u0=0.0, u_units=256.0, v_units=256.0, z_ref=0.0):
    """Valve 220 vertical wall UV aligned cleanly along chord p0 -> p1 and world -Z."""
    tw, th = TEXSIZE[tex]
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        tx, ty = 1.0, 0.0
    else:
        tx, ty = dx / L, dy / L
    sx = u_units / tw
    sy = v_units / th
    # At p0: (tx*x0 + ty*y0)/sx + uoff = arc_u0 / sx
    uoff = (arc_u0 - (tx * p0[0] + ty * p0[1])) / sx
    # At z = z_ref: (-z_ref)/sy + voff = 0 -> voff = z_ref / sy
    voff = z_ref / sy
    return f"{tex} [ {tx:.6f} {ty:.6f} 0 {uoff:.4f} ] [ 0 0 -1 {voff:.4f} ] 0 {sx:.6f} {sy:.6f}"


def uv_box_axis(tex, axis, scale=1.0):
    if axis in ("t", "b"):
        return f"{tex} [ 1 0 0 0 ] [ 0 -1 0 0 ] 0 {scale:.4f} {scale:.4f}"
    if axis in ("e", "w"):
        return f"{tex} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 {scale:.4f} {scale:.4f}"
    return f"{tex} [ 1 0 0 0 ] [ 0 0 -1 0 ] 0 {scale:.4f} {scale:.4f}"


def plane_line(p0, p1, p2, outward, uv_str):
    """Quake plane half-space check: in Quake .map, (p0 - p1) x (p2 - p1) points OUTWARD."""
    n = cross(sub(p0, p1), sub(p2, p1))
    if n[0] * outward[0] + n[1] * outward[1] + n[2] * outward[2] < 0:
        p0, p2 = p2, p0
    return f"( {p0[0]} {p0[1]} {p0[2]} ) ( {p1[0]} {p1[1]} {p1[2]} ) ( {p2[0]} {p2[1]} {p2[2]} ) {uv_str}\n"


def box_brush(x1, y1, z1, x2, y2, z2, tex, scale=1.0):
    X1, X2 = sorted((int(round(x1)), int(round(x2))))
    Y1, Y2 = sorted((int(round(y1)), int(round(y2))))
    Z1, Z2 = sorted((int(round(z1)), int(round(z2))))
    s = "{\n"
    s += plane_line((X1, Y1, Z1), (X1, Y2, Z1), (X1, Y1, Z2), (-1, 0, 0), uv_box_axis(tex, "w", scale))
    s += plane_line((X2, Y1, Z1), (X2, Y1, Z2), (X2, Y2, Z1), (1, 0, 0), uv_box_axis(tex, "e", scale))
    s += plane_line((X1, Y1, Z1), (X1, Y1, Z2), (X2, Y1, Z1), (0, -1, 0), uv_box_axis(tex, "s", scale))
    s += plane_line((X1, Y2, Z1), (X2, Y2, Z1), (X1, Y2, Z2), (0, 1, 0), uv_box_axis(tex, "n", scale))
    s += plane_line((X1, Y1, Z1), (X2, Y1, Z1), (X1, Y2, Z1), (0, 0, -1), uv_box_axis(tex, "b", scale))
    s += plane_line((X1, Y1, Z2), (X1, Y2, Z2), (X2, Y1, Z2), (0, 0, 1), uv_box_axis(tex, "t", scale))
    return s + "}\n"


def ring_pts(radius, n=N_SEG):
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        pts.append((int(round(radius * math.cos(a))), int(round(radius * math.sin(a))))
                   )
    return pts


def poly_prism(pts_ccw, z1, z2, top_uv, bot_uv, side_uvs):
    """Convex vertical prism from CCW 2D integer vertices pts_ccw."""
    Z1, Z2 = int(round(z1)), int(round(z2))
    m = len(pts_ccw)
    s = "{\n"
    for k in range(m):
        a = pts_ccw[k]
        b = pts_ccw[(k + 1) % m]
        outward = (b[1] - a[1], -(b[0] - a[0]), 0)
        s += plane_line((a[0], a[1], Z1), (b[0], b[1], Z1), (a[0], a[1], Z2), outward, side_uvs[k])
    i1 = max(1, m // 3)
    i2 = max(i1 + 1, (2 * m) // 3)
    p0, p1, p2 = pts_ccw[0], pts_ccw[i1], pts_ccw[i2]
    s += plane_line((p0[0], p0[1], Z2), (p1[0], p1[1], Z2), (p2[0], p2[1], Z2), (0, 0, 1), top_uv)
    s += plane_line((p0[0], p0[1], Z1), (p1[0], p1[1], Z1), (p2[0], p2[1], Z1), (0, 0, -1), bot_uv)
    return s + "}\n"


def add_annulus(r_in, r_out, z1, z2, top_uv, bot_uv, inner_tex, outer_tex,
                inner_u_Period=None, outer_u_period=None, inner_v=224.0, outer_v=144.0,
                z_ref_in=0.0, z_ref_out=176.0, group="world"):
    """Builds 48 watertight annular quad brushes sharing exact integer chord & radial vertices."""
    P_in = ring_pts(r_in)
    P_out = ring_pts(r_out)
    in_circ = sum(math.hypot(P_in[(i + 1) % N_SEG][0] - P_in[i][0], P_in[(i + 1) % N_SEG][1] - P_in[i][1]) for i in range(N_SEG))
    out_circ = sum(math.hypot(P_out[(i + 1) % N_SEG][0] - P_out[i][0], P_out[(i + 1) % N_SEG][1] - P_out[i][1]) for i in range(N_SEG))
    in_u_unit = inner_u_Period or (in_circ / 16.0)
    out_u_unit = outer_u_period or (out_circ / 24.0)

    arc_in = 0.0
    arc_out = 0.0
    for i in range(N_SEG):
        j = (i + 1) % N_SEG
        ri0, ri1 = P_in[i], P_in[j]
        ro0, ro1 = P_out[i], P_out[j]
        # CCW quad: ri0 -> ro0 -> ro1 -> ri1
        # Edges:
        #   0: ri0 -> ro0 (radial -a0)
        #   1: ro0 -> ro1 (outer chord, faces outward +R)
        #   2: ro1 -> ri1 (radial +a1)
        #   3: ri1 -> ri0 (inner chord, faces inward toward origin -R!)
        len_in = math.hypot(ri1[0] - ri0[0], ri1[1] - ri0[1])
        len_out = math.hypot(ro1[0] - ro0[0], ro1[1] - ro0[1])

        uv_rad0 = uv_wall_chord(outer_tex, ri0, ro0, 0.0, 256.0, outer_v, z_ref_out)
        uv_out = uv_wall_chord(outer_tex, ro0, ro1, arc_out, out_u_unit, outer_v, z_ref_out)
        uv_rad1 = uv_wall_chord(outer_tex, ro1, ri1, 0.0, 256.0, outer_v, z_ref_out)
        # Note on inner face ri1 -> ri0: pass ri0 -> ri1 so horizontal texture axis runs CCW consistently
        uv_in = uv_wall_chord(inner_tex, ri0, ri1, arc_in, in_u_unit, inner_v, z_ref_in)

        b = poly_prism(
            [ri0, ro0, ro1, ri1],
            z1,
            z2,
            top_uv=top_uv,
            bot_uv=bot_uv,
            side_uvs=[uv_rad0, uv_out, uv_rad1, uv_in],
        )
        GROUPS[group].append(b)
        arc_in += len_in
        arc_out += len_out


def ent(classname, origin=None, **kv):
    lines = ['{\n', f'"classname" "{classname}"\n']
    if origin is not None:
        lines.append(f'"origin" "{int(round(origin[0]))} {int(round(origin[1]))} {int(round(origin[2]))}"\n')
    for k, v in kv.items():
        lines.append(f'"{k}" "{v}"\n')
    lines.append("}\n")
    ENTS.append("".join(lines))


# ==============================================================================
# 1. Watertight Outer Skybox Hull (worldspawn, sky1 -> CONTENT_SKY)
# ==============================================================================
H = HULL_HALF
T = HULL_THICK
GROUPS["world"].extend([
    box_brush(-H - T, -H - T, HULL_Z_MIN - T, H + T, H + T, HULL_Z_MIN, "sky1"),      # bottom sky seal
    box_brush(-H - T, -H - T, HULL_Z_MAX, H + T, H + T, HULL_Z_MAX + T, "sky1"),      # top sky ceiling
    box_brush(-H - T, -H - T, HULL_Z_MIN, -H, H + T, HULL_Z_MAX, "sky1"),             # west sky wall
    box_brush(H, -H - T, HULL_Z_MIN, H + T, H + T, HULL_Z_MAX, "sky1"),               # east sky wall
    box_brush(-H, -H - T, HULL_Z_MIN, H, -H, HULL_Z_MAX, "sky1"),                     # south sky wall
    box_brush(-H, H, HULL_Z_MIN, H, H + T, HULL_Z_MAX, "sky1"),                       # north sky wall
    # Ceiling player clip lid so sky-high rocket juggles never touch raw sky ceiling
    box_brush(-H, -H, HULL_Z_MAX - 64, H, H, HULL_Z_MAX, "clip"),
])

# ==============================================================================
# 2. Central Hole Bottom Jump-Pad Disc (R = 0 .. R_HOLE, z = Z_BASE .. Z_PAD)
#    Split into 4 clean 12-sided convex quadrants meeting at (0, 0) so no brush
#    ever has > 16 faces and the circular ma_pad graphic maps seamlessly!
# ==============================================================================
P_hole = ring_pts(R_HOLE)
pad_top_uv = uv_planar_top("ma_pad", centered_span=R_HOLE * 2.0)
bot_dark_uv = uv_planar_top("ma_outer", tile_units=256.0)

STEP_Q = N_SEG // 4  # 12 facets per quadrant
for q in range(4):
    i0 = q * STEP_Q
    quad_pts = [(0, 0)] + [P_hole[(i0 + k) % N_SEG] for k in range(STEP_Q + 1)]
    side_uvs = [uv_wall_chord("ma_outer", quad_pts[k], quad_pts[(k + 1) % len(quad_pts)]) for k in range(len(quad_pts))]
    GROUPS["world"].append(poly_prism(quad_pts, Z_BASE, Z_PAD, pad_top_uv, bot_dark_uv, side_uvs))

# ==============================================================================
# 3. Concentric Circular Arena Rings (N_SEG = 48 smooth circle)
# ==============================================================================
collar_uv = uv_planar_top("ma_collar", centered_span=R_COLLAR * 2.0)
floor_uv = uv_planar_top("ma_floor", tile_units=256.0)
ring_c_uv = uv_planar_top("ma_ring_c", tile_units=128.0)
ring_m_uv = uv_planar_top("ma_ring_m", tile_units=128.0)
step_uv = uv_planar_top("ma_step", tile_units=256.0)

# Launch collar around central hole: inner face at R_HOLE = 192 IS the glowing cylindrical launch shaft!
# Put in phong-smoothed func_detail? Keep structural base in world, or put shaft ring in phong group:
# Since the entire arena sits inside a sealed skybox, phong func_detail gives genuine smooth Gouraud shading
# around the cylindrical central shaft AND curved perimeter parapet!
add_annulus(
    R_HOLE, R_COLLAR, Z_BASE, Z_FLOOR,
    top_uv=collar_uv, bot_uv=bot_dark_uv,
    inner_tex="ma_shaft", outer_tex="ma_floor",
    inner_v=224.0, z_ref_in=0.0,
    group="phong",
)

# Main circular floor + 2 flush luminous distance rings
add_annulus(R_COLLAR, R_FLOOR_1, Z_BASE, Z_FLOOR, floor_uv, bot_dark_uv, "ma_floor", "ma_floor", group="world")
add_annulus(R_FLOOR_1, R_RING_C, Z_BASE, Z_FLOOR, ring_c_uv, bot_dark_uv, "ma_ring_c", "ma_ring_c", group="world")
add_annulus(R_RING_C, R_FLOOR_2, Z_BASE, Z_FLOOR, floor_uv, bot_dark_uv, "ma_floor", "ma_floor", group="world")
add_annulus(R_FLOOR_2, R_RING_M, Z_BASE, Z_FLOOR, ring_m_uv, bot_dark_uv, "ma_ring_m", "ma_ring_m", group="world")
add_annulus(R_RING_M, R_FLOOR_3, Z_BASE, Z_FLOOR, floor_uv, bot_dark_uv, "ma_floor", "ma_floor", group="world")

# Outer amphitheater terrace steps (16-unit walk-up risers with glowing trim)
add_annulus(
    R_FLOOR_3, R_STEP_1, Z_BASE, Z_STEP_1,
    top_uv=step_uv, bot_uv=bot_dark_uv,
    inner_tex="ma_riser", outer_tex="ma_step",
    inner_v=64.0, z_ref_in=Z_STEP_1,
    group="phong",
)
add_annulus(
    R_STEP_1, R_STEP_2, Z_BASE, Z_STEP_2,
    top_uv=step_uv, bot_uv=bot_dark_uv,
    inner_tex="ma_riser", outer_tex="ma_step",
    inner_v=64.0, z_ref_in=Z_STEP_2,
    group="phong",
)

# Curved perimeter parapet wall (R = 1536..1600, z = -288..+176) — smooth phong-shaded circle!
add_annulus(
    R_STEP_2, R_WALL_OUT, Z_BASE, Z_WALL_TOP,
    top_uv=step_uv, bot_uv=bot_dark_uv,
    inner_tex="ma_wall", outer_tex="ma_outer",
    inner_v=144.0, outer_v=232.0,
    z_ref_in=Z_WALL_TOP, z_ref_out=Z_WALL_TOP,
    group="phong",
)

# Invisible cylindrical player clip wall above parapet (R = 1536..1600, z = +176..+6080)
# Keeps rocket-juggled airborne players inside the big circle while rockets fly cleanly into sky1!
clip_uv = uv_planar_top("clip", tile_units=256.0)
add_annulus(
    R_STEP_2, R_WALL_OUT, Z_WALL_TOP, HULL_Z_MAX - 64,
    top_uv=clip_uv, bot_uv=clip_uv,
    inner_tex="clip", outer_tex="clip",
    group="world",
)

# 16 sleek beveled floodlight beacon sconces integrated flush along the perimeter wall (every 3rd facet = 22.5 deg)
P_sconce_in = ring_pts(R_STEP_2 - 10)
P_sconce_wall = ring_pts(R_STEP_2)
for k in range(0, N_SEG, 3):
    j = (k + 1) % N_SEG
    # Slight bevel inward on inner face
    a0 = 2.0 * math.pi * (k + 0.15) / N_SEG
    a1 = 2.0 * math.pi * (k + 0.85) / N_SEG
    pi0 = (int(round((R_STEP_2 - 10) * math.cos(a0))), int(round((R_STEP_2 - 10) * math.sin(a0))))
    pi1 = (int(round((R_STEP_2 - 10) * math.cos(a1))), int(round((R_STEP_2 - 10) * math.sin(a1))))
    pw0, pw1 = P_sconce_wall[k], P_sconce_wall[j]
    pts = [pi0, pw0, pw1, pi1]
    suvs = [
        uv_wall_chord("ma_wall", pi0, pw0, 0.0, 128.0, 160.0, Z_WALL_TOP + 20),
        uv_wall_chord("ma_wall", pw0, pw1, 0.0, 128.0, 160.0, Z_WALL_TOP + 20),
        uv_wall_chord("ma_wall", pw1, pi1, 0.0, 128.0, 160.0, Z_WALL_TOP + 20),
        uv_wall_chord("ma_pylon", pi0, pi1, 0.0, math.hypot(pi1[0] - pi0[0], pi1[1] - pi0[1]), 160.0, Z_WALL_TOP + 20),
    ]
    GROUPS["detail"].append(poly_prism(pts, Z_STEP_2, Z_WALL_TOP + 20, step_uv, step_uv, suvs))

# ==============================================================================
# 4. THE CENTRAL HOLE HYPER-JUMP PAD (trigger_push)
#    Placed at the bottom of the central hole (z = -220 .. -136):
#    Players genuinely drop INTO the hole, grab the Megahealth on the pad, and
#    get launched straight up at 2000 u/s (~2,370u above the floor, ~5.0s hang time!).
# ==============================================================================
P_trig = ring_pts(R_HOLE + 8, n=16)  # 16-sided trigger overlapping 8u into solid shaft wall -> 0 gap!
trig_uvs = [uv_box_axis("clip", "n") for _ in range(16)]
trig_brush = poly_prism(P_trig, Z_PAD + 4, Z_PAD + 88, uv_box_axis("clip", "t"), uv_box_axis("clip", "b"), trig_uvs)
ENTS.append(
    '{\n'
    '"classname" "trigger_push"\n'
    '"angles" "0 -1 0"\n'
    '"speed" "200"\n'
    + trig_brush
    + '}\n'
)

# ==============================================================================
# 5. Nighttime Lighting (Moonlight + Blazing Central Pit + 16 Stadium Beacons)
# ==============================================================================
# Central launch silo uplights (cyan reactor core + plasma violet shaft wash)
ent("light", (0, 0, Z_PAD + 28), light=440, _color="80 235 255", wait="0.82")
for k in range(4):
    ang = math.pi * 0.5 * k + math.pi * 0.25
    ent("light", (116 * math.cos(ang), 116 * math.sin(ang), Z_PAD + 112), light=260, _color="175 105 255", wait="0.9")
ent("light", (0, 0, 96), light=390, _color="75 225 255", wait="0.75")
ent("light", (0, 0, 220), light=270, _color="125 170 255", wait="0.70")

# Subtle mid-floor neon ring fill lights
for k in range(8):
    ang = 2.0 * math.pi * k / 8
    ent("light", (572 * math.cos(ang), 572 * math.sin(ang), 76), light=170, _color="65 205 255", wait="0.95")
    ang2 = ang + math.pi / 8.0
    ent("light", (956 * math.cos(ang2), 956 * math.sin(ang2), 84), light=180, _color="190 105 255", wait="0.95")

# 16 Perimeter floodlight beacons matching the 16 wall sconces (alternating electric cyan & warm stadium amber)
for idx, k in enumerate(range(0, N_SEG, 3)):
    ang = 2.0 * math.pi * (k + 0.5) / N_SEG
    lx = (R_STEP_2 - 48) * math.cos(ang)
    ly = (R_STEP_2 - 48) * math.sin(ang)
    col = "85 215 255" if (idx % 2 == 0) else "255 170 95"
    ent("light", (lx, ly, 148), light=300, _color=col, wait="0.82")

# ==============================================================================
# 6. Spawns & Midair Combat Pickups
# ==============================================================================
# 12 deathmatch spawns around R = 1180, all facing inward toward the central hole (0, 0)
for i in range(12):
    ang = 2.0 * math.pi * i / 12.0 + (math.pi / 12.0)
    sx = 1180.0 * math.cos(ang)
    sy = 1180.0 * math.sin(ang)
    yaw_inward = int(round(math.degrees(math.atan2(-sy, -sx)))) % 360
    ent("info_player_deathmatch", (sx, sy, Z_FLOOR + 28), angle=yaw_inward)

if os.environ.get("MIDAIR_START"):
    vals = [float(v) for v in os.environ["MIDAIR_START"].split()]
    sx, sy, sz = vals[0], vals[1], vals[2]
    syaw = int(round(vals[3])) if len(vals) > 3 else 0
    spitch = int(round(vals[4])) if len(vals) > 4 else 0
    ent("info_player_start", (sx, sy, sz), angles=f"{spitch} {syaw} 0")
else:
    ent("info_player_start", (-1180, 0, Z_FLOOR + 28), angle=0)

# Dramatic intermission camera overlooking the glowing hole and starry night sky
ent("info_intermission", (1340, -320, 380), mangle="14 166 0")

# Megahealth right at the bottom of the central hole on the jump pad!
# (b_bh100.bsp mins='0 0 0' maxs='32 32 56' -> offset (-16, -16) centers it at exact (0, 0))
ent("item_health", (-16, -16, Z_PAD + 12), spawnflags=2)

# 4 Rocket Launchers at cardinal points + 4 large Cell packs on diagonals (R = 1040)
for i in range(4):
    ang = 0.5 * math.pi * i
    ent("weapon_rocketlauncher", (1040 * math.cos(ang), 1040 * math.sin(ang), Z_FLOOR + 28))
    ang_d = ang + 0.25 * math.pi
    ent("item_cells", (1040 * math.cos(ang_d) - 16, 1040 * math.sin(ang_d) - 16, Z_FLOOR + 20), spawnflags=1)

# 8 large Rocket ammo boxes around mid-ring (R = 690, every 45 deg) so rockets never run dry
for i in range(8):
    ang = 2.0 * math.pi * i / 8.0
    ent("item_rockets", (690 * math.cos(ang) - 16, 690 * math.sin(ang) - 16, Z_FLOOR + 20), spawnflags=1)

# 8 Health kits around Terrace Step 1 (R = 1344, z = +16)
for i in range(8):
    ang = 2.0 * math.pi * i / 8.0 + math.pi / 8.0
    ent("item_health", (1344 * math.cos(ang) - 16, 1344 * math.sin(ang) - 16, Z_STEP_1 + 20))

# 4 Green Armors on Terrace Step 2 (R = 1468, z = +32; NO item_armor2 so jetpacks don't spawn!)
for i in range(4):
    ang = 0.5 * math.pi * i + 0.25 * math.pi
    ent("item_armor1", (1468 * math.cos(ang), 1468 * math.sin(ang), Z_STEP_2 + 28))

# ==============================================================================
# Write .map
# ==============================================================================
os.makedirs(os.path.dirname(os.path.abspath(OUT_MAP)), exist_ok=True)
with open(OUT_MAP, "w", encoding="utf-8") as f:
    f.write(
        '{\n'
        '"classname" "worldspawn"\n'
        '"mapversion" "220"\n'
        '"wad" "midair.wad"\n'
        '"worldtype" "2"\n'
        '"message" "Midnight Orbit - Midair Arena"\n'
        '"skyname" "midair_"\n'
        '"_sunlight" "54"\n'
        '"_sunlight_mangle" "309 -31 0"\n'
        '"_sunlight_color" "0.62 0.76 1.0"\n'
        '"_sunlight_penumbra" "2.5"\n'
        '"_sunlight2" "38"\n'
        '"_sunlight2_color" "0.38 0.52 0.88"\n'
        '"_minlight" "22"\n'
        '"_minlight_color" "105 130 185"\n'
        '"_dirt" "1"\n'
        '"_dirtscale" "0.45"\n'
    )
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    if GROUPS["phong"]:
        f.write(
            '{\n'
            '"classname" "func_detail"\n'
            '"_phong" "1"\n'
            '"_phong_angle" "45"\n'
            + "".join(GROUPS["phong"])
            + "}\n"
        )
    if GROUPS["detail"]:
        f.write(
            '{\n'
            '"classname" "func_detail"\n'
            + "".join(GROUPS["detail"])
            + "}\n"
        )
    f.write("".join(ENTS))

print(
    f"wrote {OUT_MAP}: {len(GROUPS['world'])} world + {len(GROUPS['phong'])} phong + "
    f"{len(GROUPS['detail'])} detail brushes, {len(ENTS)} entities"
)
