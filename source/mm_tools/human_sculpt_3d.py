"""Anatomical 3D Signed-Distance-Field (SDF) Human Sculptor & Part Classifier for:
  1. Suit Rider  ('vid1_suit')  - Screaming Tan-Blazer Suit Rider on Reclined Bucket-Seat Rig
  2. Squat Rider ('vid2_squat') - Squatting Plaid-Shirt Rider on Sparking Handlebar Chariot

Produces smooth, watertight, anatomically rounded 3D human geometry fitted directly to the
studio cardinal blueprints (Front 0 deg, Profile +-90 deg, Rear 180 deg) with exact per-vertex
semantic Body-Part IDs so multi-view photographic projection is 100% free of ghost double-faces,
swiss-cheese limb holes, collar-on-chin bleed, or wheel-on-pants bleed.
"""
import math
import numpy as np

import mm_riders_rig as rig

# Semantic Body-Part IDs
PART_HEAD = 1
PART_TORSO = 2
PART_ARM_R = 3   # -Y side (rider's anatomical right)
PART_ARM_L = 4   # +Y side (rider's anatomical left)
PART_LEG_R = 5   # -Y side
PART_LEG_L = 6   # +Y side
PART_SHOE_R = 7  # -Y side
PART_SHOE_L = 8  # +Y side


# --------------------------------------------------------------------------- Vectorized Smooth SDF Primitives
def smin(a, b, k=0.55):
    if k <= 1e-5:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)


def smax(a, b, k=0.35):
    return -smin(-a, -b, k)


def sdf_ellipsoid(X, Y, Z, cx, cy, cz, rx, ry, rz, pitch_deg=0.0, yaw_deg=0.0, roll_deg=0.0):
    dx = X - cx
    dy = Y - cy
    dz = Z - cz
    if yaw_deg != 0.0:
        r = math.radians(-yaw_deg)
        c, s = math.cos(r), math.sin(r)
        dx, dy = dx * c - dy * s, dx * s + dy * c
    if pitch_deg != 0.0:
        r = math.radians(-pitch_deg)
        c, s = math.cos(r), math.sin(r)
        dx, dz = dx * c - dz * s, dx * s + dz * c
    if roll_deg != 0.0:
        r = math.radians(-roll_deg)
        c, s = math.cos(r), math.sin(r)
        dy, dz = dy * c - dz * s, dy * s + dz * c

    qx, qy, qz = dx / rx, dy / ry, dz / rz
    k0 = np.sqrt(qx * qx + qy * qy + qz * qz + 1e-8)
    k1 = np.sqrt((qx / rx) ** 2 + (qy / ry) ** 2 + (qz / rz) ** 2 + 1e-8)
    return k0 * (k0 - 1.0) / k1


def sdf_tapered_capsule(X, Y, Z, p0, p1, r0, r1):
    ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    ab2 = max(ax * ax + ay * ay + az * az, 1e-6)
    px, py, pz = X - p0[0], Y - p0[1], Z - p0[2]
    t = np.clip((px * ax + py * ay + pz * az) / ab2, 0.0, 1.0)
    dx = px - t * ax
    dy = py - t * ay
    dz = pz - t * az
    r = r0 + (r1 - r0) * t
    return np.sqrt(dx * dx + dy * dy + dz * dz + 1e-8) - r


def sdf_elliptical_segment(X, Y, Z, p0, p1, rx0, ry0, rx1, ry1):
    """Capped tapered capsule with elliptical cross-section: rx sagittal/normal, ry lateral."""
    ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    L = math.sqrt(max(ax * ax + ay * ay + az * az, 1e-6))
    tx, ty, tz = ax / L, ay / L, az / L

    # Build orthonormal frame (U_lat roughly along Y, V_sag in XZ plane)
    if abs(ty) < 0.92:
        ux, uy, uz = -ty * tx, 1.0 - ty * ty, -ty * tz
    else:
        ux, uy, uz = 1.0 - tx * tx, -tx * ty, -tx * tz
    ul = math.sqrt(max(ux * ux + uy * uy + uz * uz, 1e-8))
    ux, uy, uz = ux / ul, uy / ul, uz / ul
    vx = ty * uz - tz * uy
    vy = tz * ux - tx * uz
    vz = tx * uy - ty * ux

    px, py, pz = X - p0[0], Y - p0[1], Z - p0[2]
    s_raw = px * tx + py * ty + pz * tz
    s = np.clip(s_raw, 0.0, L)
    dt = s_raw - s  # nonzero axial overhang past segment ends!
    frac = s / L
    dx = px - s * tx
    dy = py - s * ty
    dz = pz - s * tz

    du = dx * ux + dy * uy + dz * uz  # lateral (ry)
    dv = dx * vx + dy * vy + dz * vz  # sagittal/fore-aft (rx)
    ru = ry0 + (ry1 - ry0) * frac
    rv = rx0 + (rx1 - rx0) * frac
    rm = 0.5 * (ru + rv)
    rt = 0.65 * rm  # smooth rounded endcap length
    q = np.sqrt((du / ru) ** 2 + (dv / rv) ** 2 + (dt / rt) ** 2 + 1e-8)
    return (q - 1.0) * np.minimum(ru, rv)


def sdf_round_box(X, Y, Z, cx, cy, cz, hx, hy, hz, r_round=0.45, pitch_deg=0.0, yaw_deg=0.0, roll_deg=0.0):
    dx, dy, dz = X - cx, Y - cy, Z - cz
    if yaw_deg != 0.0:
        r = math.radians(-yaw_deg)
        c, s = math.cos(r), math.sin(r)
        dx, dy = dx * c - dy * s, dx * s + dy * c
    if pitch_deg != 0.0:
        r = math.radians(-pitch_deg)
        c, s = math.cos(r), math.sin(r)
        dx, dz = dx * c - dz * s, dx * s + dz * c
    if roll_deg != 0.0:
        r = math.radians(-roll_deg)
        c, s = math.cos(r), math.sin(r)
        dy, dz = dy * c - dz * s, dy * s + dz * c

    qx = np.abs(dx) - hx
    qy = np.abs(dy) - hy
    qz = np.abs(dz) - hz
    out = np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qy, 0.0) ** 2 + np.maximum(qz, 0.0) ** 2 + 1e-8)
    ins = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0.0)
    return out + ins - r_round


# --------------------------------------------------------------------------- 1. SUIT RIDER ANATOMICAL 3D SCULPT
def eval_suit_parts_sdf(X, Y, Z):
    """Evaluates per-part SDFs for Suit Rider ('vid1_suit') on 3D arrays (X, Y, Z).
    Returns dict {part_id: sdf_array}."""
    # 1. HEAD, PARTED WAVY DARK-BROWN HAIR, EARS, NOSE, & SCREAMING BEARDED JAW
    d_neck = sdf_elliptical_segment(X, Y, Z, (-8.45, -0.20, 35.5), (-8.30, -0.20, 39.2), 2.25, 2.15, 2.05, 1.95)
    d_skull = sdf_ellipsoid(X, Y, Z, -8.35, -0.20, 42.9, 3.55, 3.02, 4.10, pitch_deg=-5.0)
    d_hair = sdf_ellipsoid(X, Y, Z, -8.70, -0.20, 44.35, 3.85, 3.46, 3.55, pitch_deg=-4.0)
    d_hair_part = sdf_ellipsoid(X, Y, Z, -7.85, -1.05, 46.15, 2.35, 1.85, 1.65)
    d_jaw = sdf_elliptical_segment(X, Y, Z, (-7.10, -0.20, 40.8), (-5.85, -0.20, 38.3), 2.40, 2.62, 1.85, 2.05)
    d_cheeks = smin(
        sdf_ellipsoid(X, Y, Z, -6.35, -1.85, 41.9, 1.65, 1.35, 1.65),
        sdf_ellipsoid(X, Y, Z, -6.35, +1.45, 41.9, 1.65, 1.35, 1.65),
        k=0.6,
    )
    d_nose = sdf_tapered_capsule(X, Y, Z, (-5.55, -0.20, 43.3), (-4.55, -0.20, 41.65), 0.50, 0.62)
    d_ears = np.minimum(
        sdf_ellipsoid(X, Y, Z, -8.45, -3.35, 42.1, 0.58, 0.48, 1.05),
        sdf_ellipsoid(X, Y, Z, -8.45, +2.95, 42.1, 0.58, 0.48, 1.05),
    )
    d_head = smin(d_neck, d_skull, k=0.65)
    d_head = smin(d_head, d_hair, k=0.55)
    d_head = smin(d_head, d_hair_part, k=0.65)
    d_head = smin(d_head, d_jaw, k=0.65)
    d_head = smin(d_head, d_cheeks, k=0.55)
    d_head = smin(d_head, d_nose, k=0.35)
    d_head = smin(d_head, d_ears, k=0.25)
    # Subtle open-mouth concavity for realistic 3D screaming mouth depth
    d_mouth_cavity = sdf_ellipsoid(X, Y, Z, -4.95, -0.20, 39.95, 0.85, 1.05, 0.95)
    d_head = smax(d_head, -d_mouth_cavity, k=0.25)

    # 2. RECLINED TORSO: WHITE SHIRT, STRIPED TIE, TAN BLAZER LAPELS & TWIN DRAPED SIDE SKIRTS
    d_pelvis = sdf_elliptical_segment(X, Y, Z, (-5.0, 0.0, 16.4), (-6.3, -0.1, 22.8), 4.10, 6.25, 3.95, 6.50)
    d_rib = sdf_elliptical_segment(X, Y, Z, (-6.3, -0.1, 22.8), (-7.6, -0.15, 30.2), 3.95, 6.50, 3.85, 7.25)
    d_chest = sdf_elliptical_segment(X, Y, Z, (-7.6, -0.15, 30.2), (-8.35, -0.20, 35.3), 3.85, 7.25, 3.45, 8.85)
    d_sh_r = sdf_tapered_capsule(X, Y, Z, (-8.35, -0.20, 36.4), (-8.25, -9.15, 35.0), 2.55, 2.35)
    d_sh_l = sdf_tapered_capsule(X, Y, Z, (-8.35, -0.20, 36.4), (-8.15, +8.80, 34.9), 2.55, 2.35)
    d_collar = sdf_ellipsoid(X, Y, Z, -7.85, -0.20, 36.7, 2.65, 2.58, 1.15)
    d_tie = sdf_elliptical_segment(X, Y, Z, (-5.65, -0.20, 35.2), (-1.95, -0.10, 22.5), 0.75, 1.45, 0.65, 1.55)

    # Twin tailored tan blazer side-skirts hanging cleanly outside the silver stainless bucket seat (|Y| > 7.4)!
    d_skirt_r = sdf_round_box(X, Y, Z, -8.10, -8.05, 20.8, 3.55, 1.25, 6.45, r_round=0.50, pitch_deg=-8.0, roll_deg=-4.0)
    d_skirt_l = sdf_round_box(X, Y, Z, -8.10, +8.05, 20.8, 3.55, 1.25, 6.45, r_round=0.50, pitch_deg=-8.0, roll_deg=+4.0)

    d_torso = smin(d_pelvis, d_rib, k=0.75)
    d_torso = smin(d_torso, d_chest, k=0.75)
    d_torso = smin(d_torso, d_sh_r, k=0.65)
    d_torso = smin(d_torso, d_sh_l, k=0.65)
    d_torso = smin(d_torso, d_collar, k=0.35)
    d_torso = smin(d_torso, d_tie, k=0.55)
    d_torso = smin(d_torso, d_skirt_r, k=0.80)
    d_torso = smin(d_torso, d_skirt_l, k=0.80)

    # Carve stainless bucket-seat inner shell boundary so blazer back NEVER pokes through silver backrest!
    seat_back_x = -9.15 - 0.255 * np.clip(Z - 14.8, 0.0, 12.0)
    seat_pan_z = 14.25
    in_seat_zone = (np.abs(Y) <= 7.45) & (Z <= 26.2)
    seat_keepout = np.where(in_seat_zone, np.maximum(seat_back_x - X, seat_pan_z - Z), -10.0)
    d_torso = smax(d_torso, seat_keepout, k=0.25)

    # 3 & 4. TRIUMPHANT RAISED ARMS, WHITE DRESS CUFFS & SCULPTED CLENCHED FISTS
    # Right Arm (-Y, viewer-left in Front f=120, foreground in Right Profile f=41)
    d_ua_r = sdf_tapered_capsule(X, Y, Z, (-8.25, -8.85, 35.1), (-6.85, -12.35, 33.1), 2.22, 1.92)
    d_fa_r = sdf_tapered_capsule(X, Y, Z, (-6.85, -12.35, 33.1), (-5.55, -13.85, 37.6), 1.90, 1.56)
    d_cf_r = sdf_tapered_capsule(X, Y, Z, (-5.55, -13.85, 37.6), (-5.25, -13.85, 38.75), 1.28, 1.20)
    d_fi_r = smin(
        sdf_round_box(X, Y, Z, -5.00, -13.70, 40.35, 1.10, 1.02, 1.26, r_round=0.46, roll_deg=12.0),
        sdf_ellipsoid(X, Y, Z, -4.35, -12.75, 39.85, 0.80, 0.76, 0.88),
        k=0.35,
    )
    d_arm_r = smin(smin(d_ua_r, d_fa_r, k=0.55), smin(d_cf_r, d_fi_r, k=0.25), k=0.22)

    # Left Arm (+Y, viewer-right in Front f=120, forward fist visible in f=41!)
    d_ua_l = sdf_tapered_capsule(X, Y, Z, (-8.15, +8.55, 35.0), (-5.55, +11.85, 32.9), 2.22, 1.92)
    d_fa_l = sdf_tapered_capsule(X, Y, Z, (-5.55, +11.85, 32.9), (-2.15, +13.25, 37.2), 1.90, 1.56)
    d_cf_l = sdf_tapered_capsule(X, Y, Z, (-2.15, +13.25, 37.2), (-1.75, +13.20, 38.35), 1.28, 1.20)
    d_fi_l = smin(
        sdf_round_box(X, Y, Z, -1.45, +12.90, 39.95, 1.10, 1.02, 1.26, r_round=0.46, roll_deg=-12.0),
        sdf_ellipsoid(X, Y, Z, -0.90, +11.95, 39.45, 0.80, 0.76, 0.88),
        k=0.35,
    )
    d_arm_l = smin(smin(d_ua_l, d_fa_l, k=0.55), smin(d_cf_l, d_fi_l, k=0.25), k=0.22)

    # 5 & 6. OUTSTRETCHED V-SPLAYED BLACK DRESS TROUSERS + GREY RIBBED SOCKS
    # Right Leg (-Y, splayed to Y ~ -12.2 at ankle, matching f=120 & f=76!)
    d_th_r = sdf_elliptical_segment(X, Y, Z, (-3.6, -3.5, 18.0), (+8.8, -7.2, 23.8), 3.30, 3.15, 2.70, 2.55)
    d_shn_r = sdf_elliptical_segment(X, Y, Z, (+8.8, -7.2, 23.8), (+19.4, -10.8, 26.8), 2.68, 2.52, 2.25, 2.10)
    d_sck_r = sdf_tapered_capsule(X, Y, Z, (+19.2, -10.7, 26.75), (+23.1, -12.05, 27.75), 1.48, 1.40)
    d_leg_r = smin(smin(d_th_r, d_shn_r, k=0.55), d_sck_r, k=0.18)

    # Left Leg (+Y, angled to Y ~ +4.7 at ankle, matching f=120 & f=76!)
    d_th_l = sdf_elliptical_segment(X, Y, Z, (-3.6, +3.1, 17.8), (+9.0, +4.0, 23.2), 3.30, 3.15, 2.70, 2.55)
    d_shn_l = sdf_elliptical_segment(X, Y, Z, (+9.0, +4.0, 23.2), (+19.7, +4.55, 25.9), 2.68, 2.52, 2.25, 2.10)
    d_sck_l = sdf_tapered_capsule(X, Y, Z, (+19.5, +4.55, 25.85), (+23.4, +4.75, 26.85), 1.48, 1.40)
    d_leg_l = smin(smin(d_th_l, d_shn_l, k=0.55), d_sck_l, k=0.18)

    # 7 & 8. LACED DARK-BROWN LEATHER OXFORD DRESS SHOES (Crisp heel, arch, vamp, & upturned rounded toe!)
    def make_oxford_shoe(x0, y0, z0, yaw_d, roll_d=0.0):
        sole = sdf_round_box(X, Y, Z, x0 + 1.35, y0, z0 + 1.95, 0.54, 1.32, 3.95, r_round=0.38, pitch_deg=-10.0, yaw_deg=yaw_d, roll_deg=roll_d)
        heel = sdf_round_box(X, Y, Z, x0 + 1.25, y0, z0 - 1.15, 0.85, 1.28, 0.92, r_round=0.28, pitch_deg=-10.0, yaw_deg=yaw_d, roll_deg=roll_d)
        dy_toe = -1.15 * math.sin(math.radians(roll_d))
        vamp = sdf_elliptical_segment(
            X, Y, Z,
            (x0 - 0.15, y0, z0 - 0.35),
            (x0 + 0.72, y0 + dy_toe * 0.8, z0 + 4.25),
            1.62, 1.45, 1.15, 1.28,
        )
        toe = sdf_ellipsoid(X, Y, Z, x0 + 0.92, y0 + dy_toe, z0 + 5.15, 1.18, 1.25, 1.32, pitch_deg=-10.0, yaw_deg=yaw_d, roll_deg=roll_d)
        return smin(smin(sole, heel, k=0.22), smin(vamp, toe, k=0.45), k=0.32)

    d_shoe_r = make_oxford_shoe(+23.65, -12.35, 27.35, yaw_d=-16.0, roll_d=+18.0)
    d_shoe_l = make_oxford_shoe(+23.95, +4.85, 26.45, yaw_d=+3.0, roll_d=-5.0)

    return {
        PART_HEAD: d_head,
        PART_TORSO: d_torso,
        PART_ARM_R: d_arm_r,
        PART_ARM_L: d_arm_l,
        PART_LEG_R: d_leg_r,
        PART_LEG_L: d_leg_l,
        PART_SHOE_R: d_shoe_r,
        PART_SHOE_L: d_shoe_l,
    }


# --------------------------------------------------------------------------- 2. SQUAT RIDER ANATOMICAL 3D SCULPT
def eval_squat_parts_sdf(X, Y, Z):
    """Evaluates per-part SDFs for Squat Rider ('vid2_squat') on 3D arrays (X, Y, Z)."""
    # 1. HEAD, SHORT CURLY BLACK HAIR, FULL CHEEKS, NOSE, & GOATEE CHIN (Exact X lock in f=48 & f=98!)
    d_neck = sdf_elliptical_segment(X, Y, Z, (-2.35, -0.15, 35.8), (-1.15, -0.15, 39.2), 2.55, 2.32, 2.35, 2.15)
    d_skull = sdf_ellipsoid(X, Y, Z, -1.05, -0.15, 42.65, 3.72, 3.25, 4.12, pitch_deg=4.0)
    d_hair = sdf_ellipsoid(X, Y, Z, -1.50, -0.15, 44.35, 3.95, 3.58, 3.55)
    d_jaw = sdf_elliptical_segment(X, Y, Z, (+0.35, -0.15, 40.2), (+1.70, -0.15, 37.45), 2.18, 2.28, 1.42, 1.54)
    d_cheeks = smin(
        sdf_ellipsoid(X, Y, Z, +0.45, -1.85, 40.75, 1.72, 1.34, 1.72),
        sdf_ellipsoid(X, Y, Z, +0.45, +1.55, 40.75, 1.72, 1.34, 1.72),
        k=0.55,
    )
    d_nose = sdf_tapered_capsule(X, Y, Z, (+1.85, -0.15, 42.55), (+2.92, -0.15, 40.85), 0.56, 0.72)
    d_ears = np.minimum(
        sdf_ellipsoid(X, Y, Z, -1.45, -3.42, 41.8, 0.56, 0.46, 1.02),
        sdf_ellipsoid(X, Y, Z, -1.45, +3.12, 41.8, 0.56, 0.46, 1.02),
    )
    d_head = smin(d_neck, d_skull, k=0.60)
    d_head = smin(d_head, d_hair, k=0.48)
    d_head = smin(d_head, d_jaw, k=0.60)
    d_head = smin(d_head, d_cheeks, k=0.55)
    d_head = smin(d_head, d_nose, k=0.38)
    d_head = smin(d_head, d_ears, k=0.25)

    # 2. BROAD HUNCHED TORSO & CREAM WINDOWPANE-PLAID SHORT-SLEEVE SHIRT
    d_seat = sdf_elliptical_segment(X, Y, Z, (-9.8, -0.1, 21.3), (-7.6, -0.1, 25.6), 4.95, 7.65, 7.35, 8.45)
    d_mid = sdf_elliptical_segment(X, Y, Z, (-7.6, -0.1, 25.6), (-6.0, -0.1, 30.6), 7.35, 8.45, 7.15, 8.65)
    d_up = sdf_elliptical_segment(X, Y, Z, (-6.0, -0.1, 30.6), (-4.0, -0.15, 34.8), 7.15, 8.65, 5.15, 8.35)
    d_yoke = sdf_elliptical_segment(X, Y, Z, (-4.0, -0.15, 34.8), (-2.45, -0.15, 36.1), 4.45, 7.45, 2.95, 3.45)

    # Flared loose short sleeves overhanging bare forearms at Z ~ 28.9!
    d_slv_r = sdf_tapered_capsule(X, Y, Z, (-3.4, -8.1, 34.4), (-2.05, -11.45, 28.9), 2.68, 2.38)
    d_slv_l = sdf_tapered_capsule(X, Y, Z, (-3.4, +8.0, 34.4), (-2.05, +11.55, 28.9), 2.68, 2.38)

    d_torso = smin(d_seat, d_mid, k=0.75)
    d_torso = smin(d_torso, d_up, k=0.75)
    d_torso = smin(d_torso, d_yoke, k=0.65)
    d_torso = smin(d_torso, d_slv_r, k=0.62)
    d_torso = smin(d_torso, d_slv_l, k=0.62)

    # Keep shirt collar cleanly below/behind jaw & chin (Z < 36.8 in front!) so collar never touches face!
    chin_keepout = -sdf_ellipsoid(X, Y, Z, +1.15, -0.15, 39.2, 3.10, 2.85, 3.15)
    d_torso = smax(d_torso, chin_keepout, k=0.25)

    # 3 & 4. BARE MUSCULAR FOREARMS & HANDS GRIPPING THE Y = +-13.0, Z = 18.75 HANDLEBARS
    d_fa_r = sdf_tapered_capsule(X, Y, Z, (-2.05, -11.55, 29.5), (-0.75, -12.85, 20.8), 1.98, 1.38)
    d_hd_r = sdf_round_box(X, Y, Z, -0.45, -12.95, 18.85, 1.35, 1.15, 1.20, r_round=0.52)
    d_arm_r = smin(d_fa_r, d_hd_r, k=0.35)

    d_fa_l = sdf_tapered_capsule(X, Y, Z, (-2.05, +11.65, 29.5), (-0.75, +12.95, 20.8), 1.98, 1.38)
    d_hd_l = sdf_round_box(X, Y, Z, -0.45, +13.05, 18.85, 1.35, 1.15, 1.20, r_round=0.52)
    d_arm_l = smin(d_fa_l, d_hd_l, k=0.35)

    # 5 & 6. DEEPLY SQUATTING OLIVE-BROWN CARGO-PANT LEGS
    d_th_r = sdf_elliptical_segment(X, Y, Z, (-8.8, -4.9, 20.4), (+4.2, -7.35, 22.6), 4.25, 3.95, 3.50, 3.45)
    d_cf_r = sdf_elliptical_segment(X, Y, Z, (+4.2, -7.35, 22.1), (-2.9, -5.05, 8.6), 3.35, 3.20, 2.45, 2.40)
    d_leg_r = smin(d_th_r, d_cf_r, k=0.65)

    d_th_l = sdf_elliptical_segment(X, Y, Z, (-8.8, +4.8, 20.4), (+4.2, +7.35, 22.6), 4.25, 3.95, 3.50, 3.45)
    d_cf_l = sdf_elliptical_segment(X, Y, Z, (+4.2, +7.35, 22.1), (-2.9, +5.45, 8.6), 3.35, 3.20, 2.45, 2.40)
    d_leg_l = smin(d_th_l, d_cf_l, k=0.65)

    # 7 & 8. TUCKED DARK-BROWN SUEDE SHOES
    def make_suede_shoe(y_c, yaw_d):
        heel = sdf_round_box(X, Y, Z, -3.55, y_c, 6.25, 1.45, 1.52, 1.65, r_round=0.45, yaw_deg=yaw_d)
        vamp = sdf_elliptical_segment(X, Y, Z, (-3.45, y_c, 6.15), (+1.45, y_c * 1.08, 5.75), 1.62, 1.72, 1.32, 1.62)
        toe = sdf_ellipsoid(X, Y, Z, +1.85, y_c * 1.10, 5.65, 1.50, 1.62, 1.32, yaw_deg=yaw_d)
        shoe = smin(smin(heel, vamp, k=0.45), toe, k=0.45)
        return smax(shoe, 4.15 - Z, k=0.18)

    d_shoe_r = make_suede_shoe(-4.95, yaw_d=-8.0)
    d_shoe_l = make_suede_shoe(+5.55, yaw_d=+14.0)

    return {
        PART_HEAD: d_head,
        PART_TORSO: d_torso,
        PART_ARM_R: d_arm_r,
        PART_ARM_L: d_arm_l,
        PART_LEG_R: d_leg_r,
        PART_LEG_L: d_leg_l,
        PART_SHOE_R: d_shoe_r,
        PART_SHOE_L: d_shoe_l,
    }


def build_human_sdf_occupancy(kind, vox_step=0.24):
    """Evaluates the complete smooth-unioned anatomical 3D human occupancy grid (occ, X, Y, Z)."""
    if kind == "suit":
        x_rng, y_rng, z_rng = (-14.2, 28.5), (-18.0, 17.5), (13.2, 49.5)
        eval_fn = eval_suit_parts_sdf
    else:
        x_rng, y_rng, z_rng = (-17.2, 9.8), (-16.8, 16.8), (3.8, 49.5)
        eval_fn = eval_squat_parts_sdf

    X = np.arange(x_rng[0], x_rng[1] + 0.01, vox_step, dtype=np.float32)
    Y = np.arange(y_rng[0], y_rng[1] + 0.01, vox_step, dtype=np.float32)
    Z = np.arange(z_rng[0], z_rng[1] + 0.01, vox_step, dtype=np.float32)
    XX, YY, ZZ = np.meshgrid(X, Y, Z, indexing="ij")

    parts = eval_fn(XX, YY, ZZ)
    # Smoothly union torso + neck/head + limbs where joints meet, keeping crisp seams at cuffs/shoes!
    d_body = smin(parts[PART_TORSO], parts[PART_HEAD], k=0.35)
    d_body = smin(d_body, parts[PART_ARM_R], k=0.30)
    d_body = smin(d_body, parts[PART_ARM_L], k=0.30)
    d_body = smin(d_body, parts[PART_LEG_R], k=0.40)
    d_body = smin(d_body, parts[PART_LEG_L], k=0.40)
    d_body = smin(d_body, parts[PART_SHOE_R], k=0.15)
    d_body = smin(d_body, parts[PART_SHOE_L], k=0.15)

    occ = (d_body <= 0.0) & (~rig.rig_exclusive_mask_3d(kind, XX, YY, ZZ))
    return occ, X, Y, Z


def classify_points_part_id(kind, P):
    """Assigns exact semantic PART_* ID to an (N, 3) array of 3D surface points P."""
    X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
    parts = eval_suit_parts_sdf(X, Y, Z) if kind == "suit" else eval_squat_parts_sdf(X, Y, Z)
    part_ids = sorted(parts.keys())
    stack = np.column_stack([parts[pid] for pid in part_ids])
    best_idx = np.argmin(stack, axis=1)
    return np.array([part_ids[i] for i in best_idx], dtype=np.int32)
