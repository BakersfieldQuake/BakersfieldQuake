"""Procedural anatomical & costume 3D mesh sculptor + skeletal pose evaluator
for the Miniature Blonde Woman ("Pocket Rocket / Pink Torpedo").

Coordinate convention (Character Rest Space, height H = 1.00):
  Origin (0, 0, 0) between soles of sneakers on the floor
  +X  forward (face, nose, bust, toes point +X)
  +Y  character's LEFT,  -Y  character's RIGHT
  +Z  up (0.00 = sneaker sole, 1.00 = crown of head)

UV convention returned by all builders:
  (u, v) with v = 0 at TOP of PNG texture, v = 1 at BOTTOM (MD3 / WebGL direct).
"""
import math
import numpy as np


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0 + 1e-12)))
    return t * t * (3.0 - 2.0 * t)


def rot_x(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def rot_y(deg):
    # Positive deg pitches +Z forward toward +X (or +X down toward -Z)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def rot_z(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)


def compute_normals(V, F):
    t = V[F]
    fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    N = np.where(ln > 1e-12, N / (ln + 1e-12), np.array([1.0, 0.0, 0.0]))
    return N


def grid_tris(nu, nv, wrap_u=False, flip=False):
    tris = []
    cols = nu if wrap_u else (nu - 1)
    for j in range(nv - 1):
        for i in range(cols):
            i1 = (i + 1) % nu if wrap_u else (i + 1)
            a = j * nu + i
            b = j * nu + i1
            c = (j + 1) * nu + i1
            d = (j + 1) * nu + i
            if not flip:
                tris.append((a, b, c))
                tris.append((a, c, d))
            else:
                tris.append((a, c, b))
                tris.append((a, d, c))
    return np.array(tris, dtype=np.int32)


def taubin_smooth(V, F, iters=6, lam=0.45, mu=-0.47, pin_mask=None):
    V = V.copy()
    n = len(V)
    nbrs = [[] for _ in range(n)]
    for a, b, c in F:
        nbrs[a].extend((b, c))
        nbrs[b].extend((a, c))
        nbrs[c].extend((a, b))
    nbrs = [np.unique(nb) for nb in nbrs]
    for _ in range(iters):
        for step in (lam, mu):
            V_new = V.copy()
            for idx in range(n):
                if pin_mask is not None and pin_mask[idx]:
                    continue
                nb = nbrs[idx]
                if len(nb) > 0:
                    V_new[idx] = V[idx] + step * (V[nb].mean(axis=0) - V[idx])
            V = V_new
    return V


# ===========================================================================
# SKELETON DEFINITION (Rest Joints & Hierarchical Forward Kinematics)
# ===========================================================================
REST_JOINTS = {
    "pelvis":   np.array([0.000,  0.000, 0.455]),
    "waist":    np.array([0.000,  0.000, 0.535]),
    "chest":    np.array([0.005,  0.000, 0.655]),
    "bust_L":   np.array([0.045,  0.068, 0.675]),
    "bust_R":   np.array([0.045, -0.068, 0.675]),
    "knot":     np.array([0.155,  0.000, 0.528]),
    "ribbon_L": np.array([0.155,  0.015, 0.518]),
    "ribbon_R": np.array([0.155, -0.015, 0.518]),
    "neck":     np.array([0.000,  0.000, 0.805]),
    "head":     np.array([0.005,  0.000, 0.845]),
    "hair_1":   np.array([-0.035, 0.000, 0.895]),
    "hair_2":   np.array([-0.055, 0.000, 0.770]),
    "hair_3":   np.array([-0.062, 0.000, 0.640]),
    "sh_L":     np.array([0.000,  0.112, 0.758]),
    "el_L":     np.array([-0.008, 0.210, 0.660]),
    "wr_L":     np.array([0.005,  0.290, 0.572]),
    "sh_R":     np.array([0.000, -0.112, 0.758]),
    "el_R":     np.array([-0.008, -0.210, 0.660]),
    "wr_R":     np.array([0.005, -0.290, 0.572]),
    "hip_L":    np.array([0.000,  0.062, 0.440]),
    "kn_L":     np.array([0.004,  0.065, 0.268]),
    "an_L":     np.array([-0.004, 0.066, 0.088]),
    "hip_R":    np.array([0.000, -0.062, 0.440]),
    "kn_R":     np.array([0.004, -0.065, 0.268]),
    "an_R":     np.array([-0.004, -0.066, 0.088]),
}

PARENTS = {
    "pelvis": None,
    "waist": "pelvis",
    "chest": "waist",
    "bust_L": "chest",
    "bust_R": "chest",
    "knot": "chest",
    "ribbon_L": "knot",
    "ribbon_R": "knot",
    "neck": "chest",
    "head": "neck",
    "hair_1": "head",
    "hair_2": "hair_1",
    "hair_3": "hair_2",
    "sh_L": "chest",
    "el_L": "sh_L",
    "wr_L": "el_L",
    "sh_R": "chest",
    "el_R": "sh_R",
    "wr_R": "el_R",
    "hip_L": "pelvis",
    "kn_L": "hip_L",
    "an_L": "kn_L",
    "hip_R": "pelvis",
    "kn_R": "hip_R",
    "an_R": "kn_R",
}

BONE_ORDER = [
    "pelvis", "waist", "chest", "bust_L", "bust_R", "knot", "ribbon_L", "ribbon_R",
    "neck", "head", "hair_1", "hair_2", "hair_3",
    "sh_L", "el_L", "wr_L", "sh_R", "el_R", "wr_R",
    "hip_L", "kn_L", "an_L", "hip_R", "kn_R", "an_R",
]
BONE_IDX = {b: i for i, b in enumerate(BONE_ORDER)}


def solve_fk(pose_rots, root_offset=(0.0, 0.0, 0.0), local_offsets=None):
    """Computes world 3x3 rotation R_w and world pivot P_w for each bone,
    so skinning x' = sum_i w_i * (R_w[i] @ (x - J_rest[i]) + P_w[i]) is exact."""
    R_w = {}
    P_w = {}
    for b in BONE_ORDER:
        rx, ry, rz = pose_rots.get(b, (0.0, 0.0, 0.0))
        R_loc = rot_z(rz) @ rot_y(ry) @ rot_x(rx)
        lo = np.array(local_offsets.get(b, (0.0, 0.0, 0.0)) if local_offsets else (0.0, 0.0, 0.0), dtype=np.float64)
        p = PARENTS[b]
        if p is None:
            R_w[b] = R_loc
            P_w[b] = REST_JOINTS[b] + np.array(root_offset, dtype=np.float64) + lo
        else:
            R_w[b] = R_w[p] @ R_loc
            P_w[b] = P_w[p] + R_w[p] @ (REST_JOINTS[b] - REST_JOINTS[p] + lo)
    return R_w, P_w


def apply_skin(V_rest, W, R_w, P_w):
    """Linear blend skinning with post-renormalized normals."""
    out = np.zeros_like(V_rest)
    for bi, b in enumerate(BONE_ORDER):
        w = W[:, bi:bi + 1]
        if np.max(w) < 1e-6:
            continue
        R = R_w[b]
        P = P_w[b]
        J = REST_JOINTS[b]
        out += w * ((V_rest - J) @ R.T + P)
    return out


# ===========================================================================
# PART 1: HEAD + SMILING FACE + NECK (`surf_skin` part A)
# ===========================================================================
def build_head_and_neck():
    nu, nv = 56, 44
    # Smooth spherical crown dome + fuller feminine oval jaw/chin + graceful continuous neck
    verts = []
    uvs = []
    weights = np.zeros((nu * nv, len(BONE_ORDER)), dtype=np.float64)

    for j in range(nv):
        tv = j / (nv - 1)
        if tv <= 0.34:
            # True smooth hemispherical/ellipsoidal cranium dome from crown pole (z=0.998) down to brow/temple equator (z=0.918)
            phi = (tv / 0.34) * (math.pi * 0.5)
            sp, cp = math.sin(phi), math.cos(phi)
            z_base = 0.918 + 0.080 * cp
            rx = 0.066 * sp
            ry = 0.056 * sp
            cx = 0.004 * sp
            chin_dip = 0.0
        elif tv <= 0.72:
            # Mid & lower feminine oval face from brow/temples (z=0.918) down to rounded jaw/chin (z=0.834)
            lt = (tv - 0.34) / 0.38
            z_base = 0.918 - lt * (0.918 - 0.834)
            # Keep cheekbones & smiling mouth region full & appealing, tapering smoothly into a rounded oval chin -> neck!
            jaw_t = sstep(0.18, 0.92, lt)
            submental_t = sstep(0.76, 1.0, lt)
            rx_face = 0.066 * (1.0 - 0.24 * jaw_t)
            ry_face = 0.056 * (1.0 - 0.22 * jaw_t)
            cx_face = 0.004 + 0.008 * math.sin(lt * math.pi * 0.85)
            # Blend smoothly at submental crease into neck cylinder (rx=0.033, ry=0.032, cx=0.002)
            rx = rx_face * (1.0 - submental_t) + 0.033 * submental_t
            ry = ry_face * (1.0 - submental_t) + 0.032 * submental_t
            cx = cx_face * (1.0 - submental_t) + 0.002 * submental_t
            chin_dip = -0.005 * math.sin(lt * math.pi)
        else:
            # Graceful slender neck from z=0.834 down to collarbone z=0.770
            nt = (tv - 0.72) / 0.28
            z_base = 0.834 - nt * (0.834 - 0.770)
            flare = sstep(0.50, 1.0, nt)
            rx = 0.033 + 0.018 * flare
            ry = 0.032 + 0.038 * flare
            cx = 0.002 - 0.004 * nt
            chin_dip = 0.0

        # Height-locked UV v so 3D eyes/nose/mouth/chin align sub-pixel with tex_skin.png!
        uv_v = 0.02 + 0.48 * np.clip((0.998 - z_base) / (0.998 - 0.770), 0.0, 1.0)

        for i in range(nu):
            # theta = 0 at +X (nose center!), +pi/2 at +Y (char left), +-pi at -X (back of head)
            u_frac = i / nu
            theta = (u_frac - 0.50) * 2.0 * math.pi
            ct, st = math.cos(theta), math.sin(theta)

            x = cx + rx * ct
            y = ry * st
            zz = z_base + chin_dip * max(0.0, ct)

            # Sculpt 3D facial relief on front hemisphere (|theta| < 1.45 and z_base > 0.828)
            if abs(theta) < 1.45 and z_base > 0.828:
                fu = (u_frac - 0.50) / 0.195
                fv = (uv_v - 0.25) / 0.21

                # 1. Forehead smooth dome
                fh = math.exp(-((fu / 0.68) ** 2 + ((fv + 0.45) / 0.36) ** 2))
                x += 0.0045 * fh

                # 2. Brow ridge + eye socket concave recess + eyeball dome
                for sgn in (-1.0, 1.0):
                    brow = math.exp(-(((fu - sgn * 0.33) / 0.24) ** 2 + ((fv + 0.30) / 0.08) ** 2))
                    sock = math.exp(-(((fu - sgn * 0.32) / 0.20) ** 2 + ((fv + 0.11) / 0.10) ** 2))
                    ball = math.exp(-(((fu - sgn * 0.32) / 0.12) ** 2 + ((fv + 0.11) / 0.068) ** 2))
                    x += 0.0030 * brow - 0.0042 * sock + 0.0038 * ball

                # 3. Cute upturned 3D nose bridge + nasal tip + alar wings
                bridge = math.exp(-((fu / 0.095) ** 2 + ((fv + 0.02) / 0.18) ** 2))
                ntip = math.exp(-((fu / 0.105) ** 2 + ((fv - 0.11) / 0.085) ** 2))
                x += 0.0072 * bridge + 0.0118 * ntip
                zz += 0.0020 * ntip
                for sgn in (-1.0, 1.0):
                    wing = math.exp(-(((fu - sgn * 0.115) / 0.065) ** 2 + ((fv - 0.135) / 0.055) ** 2))
                    x += 0.0040 * wing
                    y += sgn * 0.0016 * wing

                # 4. Full, warm laughing cheeks & cheekbones
                for sgn in (-1.0, 1.0):
                    cheek = math.exp(-(((fu - sgn * 0.44) / 0.28) ** 2 + ((fv - 0.06) / 0.22) ** 2))
                    x += 0.0068 * cheek
                    y += sgn * 0.0052 * cheek
                    zz += 0.0018 * cheek

                # 5. Sculpted smiling lips + open laughing mouth recess + rounded feminine chin!
                upper_lip = math.exp(-((fu / 0.28) ** 2 + ((fv - 0.26) / 0.060) ** 2))
                lower_lip = math.exp(-((fu / 0.26) ** 2 + ((fv - 0.45) / 0.065) ** 2))
                mouth_cav = math.exp(-((fu / 0.23) ** 2 + ((fv - 0.35) / 0.062) ** 2))
                chin = math.exp(-((fu / 0.26) ** 2 + ((fv - 0.58) / 0.14) ** 2))
                x += 0.0055 * upper_lip + 0.0058 * lower_lip - 0.0045 * mouth_cav + 0.0075 * chin

            verts.append((x, y, zz))
            uvs.append((float(u_frac), float(uv_v)))

            idx = j * nu + i
            w_head = 1.0 - sstep(0.68, 0.86, tv)
            w_neck = sstep(0.68, 0.86, tv) * (1.0 - sstep(0.88, 1.0, tv))
            w_chest = sstep(0.88, 1.0, tv)
            weights[idx, BONE_IDX["head"]] = w_head
            weights[idx, BONE_IDX["neck"]] = w_neck
            weights[idx, BONE_IDX["chest"]] = w_chest

    F = grid_tris(nu, nv, wrap_u=True, flip=False)
    V = np.array(verts, dtype=np.float64)
    UV = np.array(uvs, dtype=np.float64)
    return V, F, UV, weights


# ===========================================================================
# PART 2: EXAGGERATED BUST + PLUNGING TIE-FRONT PINK TOP (`surf_skin` B + `surf_pink_top` + `surf_pink_bow`)
# ===========================================================================
def eval_bust_torso_field(z, theta):
    """Shared analytical torso + rounded shoulders + twin exaggerated teardrop breasts surface!
    Guarantees 0.0 mm gap and 100% continuous curvature between exposed cleavage skin
    and the snug hot-pink plunging tie-front cardigan."""
    # Base feminine ribcage / narrow waist / rounded shoulder-to-collar dome (z in 0.505 .. 0.790)
    t_h = float(np.clip((z - 0.505) / (0.790 - 0.505), 0.0, 1.0))
    waist_pinch = math.sin(t_h * math.pi * 0.65)
    rx_rib = 0.066 + 0.018 * sstep(0.12, 0.75, t_h)
    ry_rib = 0.088 + 0.032 * sstep(0.15, 0.75, t_h)
    # Smoothly dome the upper shoulders inward toward the neck collar above z=0.735 so zero sharp shoulder horns!
    sh_cap = sstep(0.732, 0.790, z) ** 1.25
    rx_rib = rx_rib * (1.0 - sh_cap) + 0.048 * sh_cap
    ry_rib = ry_rib * (1.0 - sh_cap) + 0.062 * sh_cap
    cx_rib = 0.004 * waist_pinch * (1.0 - sh_cap) - 0.002 * sh_cap

    ct, st = math.cos(theta), math.sin(theta)
    x = cx_rib + rx_rib * ct
    y = ry_rib * st
    # Slight spinal hollow along back midline (theta ~ +-pi)
    back_groove = math.exp(-(((abs(theta) - math.pi) / 0.28) ** 2)) * sstep(0.1, 0.75, t_h) * (1.0 - sh_cap)
    x += 0.006 * back_groove

    # Now add the TWIN EXAGGERATED TEARDROP BREASTS on the front hemisphere (|theta| < 1.92)!
    if 0.506 <= z <= 0.778 and abs(theta) < 1.92:
        bz = max(0.0, min(1.0, (z - 0.506) / (0.778 - 0.506)))
        vert_prof = (max(0.0, math.sin(bz * math.pi)) ** 0.68) * (1.0 + 0.32 * (1.0 - bz))
        vert_prof *= sstep(0.0, 0.09, bz) * (1.0 - sstep(0.88, 1.0, bz))

        a_abs = abs(theta)
        lobe_outer = math.exp(-(((a_abs - 0.48) / 0.68) ** 2))
        cleav_pinch = 1.0 - 0.76 * math.exp(-((theta / 0.115) ** 2))
        lobe = lobe_outer * cleav_pinch

        proj_x = 0.175 * vert_prof * lobe
        proj_y = 0.092 * vert_prof * math.sin(a_abs * 1.05) * math.exp(-(((a_abs - 0.72) / 0.78) ** 2))
        sag_z = -0.022 * vert_prof * lobe

        x += proj_x
        y += math.copysign(proj_y, theta) if abs(theta) > 1e-6 else 0.0
        z_out = z + sag_z
    else:
        z_out = z
    return x, y, z_out


def neckline_theta_bound(z):
    """Returns half-angle theta_neck(z) >= 0 of the open plunging U/V neckline!"""
    if z <= 0.530:
        return 0.0
    t = min(1.0, (z - 0.530) / (0.788 - 0.530))
    return 0.62 * (t ** 0.46)


def build_chest_skin_and_pink_top():
    # A. Exposed Chest & Deep Plunging Cleavage Skin Patch (`surf_skin` part B)
    nu_s, nv_s = 43, 36
    s_verts, s_uvs = [], []
    s_w = np.zeros((nu_s * nv_s, len(BONE_ORDER)), dtype=np.float64)

    for j in range(nv_s):
        tv = j / (nv_s - 1)   # 0 = top collar (z=0.788) -> 1 = tucked behind knot/waist (z=0.508)
        z = 0.788 - tv * (0.788 - 0.508)
        th_n = neckline_theta_bound(z)
        th_max = max(0.14, th_n + 0.12)  # generous tuck margin underneath pink cardigan!
        for i in range(nu_s):
            s = (i / (nu_s - 1)) * 2.0 - 1.0   # -1 (right) .. +1 (left)
            theta = s * th_max
            x, y, zz = eval_bust_torso_field(z, theta)
            # Tuck outer margin (|theta| > th_n) slightly inward (-1.8 mm) so skin never pokes out through pink cloth!
            over = max(0.0, abs(theta) - th_n)
            tuck = 0.0022 * sstep(0.0, 0.08, over) + 0.0020 * sstep(0.534, 0.516, z)
            rn = math.hypot(x, y) + 1e-9
            x -= (x / rn) * tuck
            y -= (y / rn) * tuck

            s_verts.append((x, y, zz))
            u_tex = 0.325 + s * 0.27 * (th_max / 0.74)
            v_tex = 0.53 + tv * 0.45
            s_uvs.append((u_tex, v_tex))

            idx = j * nu_s + i
            w_waist = sstep(0.68, 1.0, tv) * 0.75
            w_neck = (1.0 - sstep(0.0, 0.18, tv)) * 0.35
            w_bust = (1.0 - w_waist) * sstep(0.12, 0.48, tv) * (1.0 - sstep(0.82, 0.98, tv)) * 0.58
            w_chest = max(0.0, 1.0 - w_waist - w_neck - w_bust)
            s_w[idx, BONE_IDX["waist"]] = w_waist
            s_w[idx, BONE_IDX["neck"]] = w_neck
            s_w[idx, BONE_IDX["chest"]] = w_chest
            if s >= 0:
                s_w[idx, BONE_IDX["bust_L"]] = w_bust * abs(s)
                s_w[idx, BONE_IDX["chest"]] += w_bust * (1.0 - abs(s))
            else:
                s_w[idx, BONE_IDX["bust_R"]] = w_bust * abs(s)
                s_w[idx, BONE_IDX["chest"]] += w_bust * (1.0 - abs(s))

    F_skin = grid_tris(nu_s, nv_s, wrap_u=False, flip=True)
    V_skin = np.array(s_verts, dtype=np.float64)
    UV_skin = np.array(s_uvs, dtype=np.float64)

    # B. Hot-Pink Plunging Tie-Front Cardigan Torso (`surf_pink_top` body)
    nu_p, nv_p = 72, 40
    p_verts, p_uvs = [], []
    p_w = np.zeros((nu_p * nv_p, len(BONE_ORDER)), dtype=np.float64)

    for j in range(nv_p):
        tv = j / (nv_p - 1)   # 0 = rounded collar rim (z=0.790) -> 1 = high-waist hem (z=0.505)
        z = 0.790 - tv * (0.790 - 0.505)
        th_n = neckline_theta_bound(z)
        arc_span = 2.0 * (math.pi - th_n)
        for i in range(nu_p):
            q = i / (nu_p - 1)
            theta = th_n + q * arc_span
            if theta > math.pi:
                theta -= 2.0 * math.pi

            x, y, zz = eval_bust_torso_field(z, theta)

            edge_dist = min(q, 1.0 - q)
            collar_roll = math.exp(-((edge_dist / 0.028) ** 2)) * sstep(0.532, 0.57, z)
            d_knot = math.hypot(theta * 0.55, (z - 0.532) * 2.2)
            pleat_3d = 0.0018 * math.sin(theta * 28.0) * math.exp(-((d_knot / 0.35) ** 2)) * sstep(0.03, 0.12, d_knot)

            thick = 0.0024 + 0.0018 * collar_roll + pleat_3d
            rn = math.hypot(x, y) + 1e-9
            x += (x / rn) * thick
            y += (y / rn) * thick

            if z < 0.520:
                zz = max(zz, 0.506 - 0.008 * math.exp(-((theta / 0.35) ** 2)))

            p_verts.append((x, y, zz))
            u_tex = 0.50 + (theta / math.pi) * 0.48
            v_tex = 0.14 + tv * 0.72
            p_uvs.append((u_tex, v_tex))

            idx = j * nu_p + i
            w_waist = sstep(0.68, 1.0, tv) * 0.75
            w_bust = (1.0 - w_waist) * sstep(0.15, 0.50, tv) * (1.0 - sstep(0.80, 0.98, tv)) * max(0.0, math.cos(theta)) * 0.65
            w_chest = max(0.0, 1.0 - w_waist - w_bust)
            p_w[idx, BONE_IDX["waist"]] = w_waist
            p_w[idx, BONE_IDX["chest"]] = w_chest
            if theta >= 0:
                p_w[idx, BONE_IDX["bust_L"]] = w_bust
            else:
                p_w[idx, BONE_IDX["bust_R"]] = w_bust

    F_pink = grid_tris(nu_p, nv_p, wrap_u=False, flip=False)
    V_pink = np.array(p_verts, dtype=np.float64)
    UV_pink = np.array(p_uvs, dtype=np.float64)

    return (V_skin, F_skin, UV_skin, s_w), (V_pink, F_pink, UV_pink, p_w)


# ===========================================================================
# PART 3: 3D TIE-FRONT KNOT & TWIN HANGING RIBBON TAILS (`surf_pink_bow`)
# ===========================================================================
def build_tie_knot_and_ribbons():
    verts, tris, uvs, w_list = [], [], [], []

    # 1. Plump sculpted center fabric knot at REST_JOINTS["knot"] = (0.155, 0.0, 0.528)
    kx, ky, kz = REST_JOINTS["knot"]
    nu_k, nv_k = 20, 14
    base_i = len(verts)
    for j in range(nv_k):
        ph = (j / (nv_k - 1) - 0.5) * math.pi
        for i in range(nu_k):
            th = (i / nu_k) * 2.0 * math.pi
            # Slightly pinched pillow-knot shape with Diagonal wrap twist
            r_mod = 1.0 + 0.14 * math.sin(2.0 * th + 2.0 * ph)
            x = kx + 0.017 * math.cos(ph) * math.cos(th) * r_mod
            y = ky + 0.021 * math.cos(ph) * math.sin(th) * r_mod
            z = kz + 0.023 * math.sin(ph) * r_mod
            verts.append((x, y, z))
            uvs.append((0.46 + 0.08 * (i / nu_k), 0.70 + 0.08 * (j / (nv_k - 1))))
            w = np.zeros(len(BONE_ORDER), dtype=np.float64)
            w[BONE_IDX["knot"]] = 1.0
            w_list.append(w)
    kt = grid_tris(nu_k, nv_k, wrap_u=True, flip=False) + base_i
    tris.extend(kt.tolist())

    # 2. Twin hanging hot-pink ribbon tails (solid 3D flat-oval cross-section so both sides light cleanly!)
    # Look at v1_f180 & v3_f120: two long magenta tie straps (~0.17 H long) with angled notched tips!
    for side, sgn, bname, length, x_bias in (
        ("L",  1.0, "ribbon_L", 0.175, 0.006),
        ("R", -1.0, "ribbon_R", 0.165, 0.002),
    ):
        nu_r, nv_r = 16, 22
        b0 = len(verts)
        jx, jy, jz = REST_JOINTS[bname]
        for j in range(nv_r):
            t = j / (nv_r - 1)   # 0 at knot -> 1 at pointed ribbon tip
            # Taper from narrow gathered neck -> wide ribbon blade -> angled V-point tip!
            width = 0.019 * (0.45 + 0.75 * sstep(0.0, 0.25, t)) * (1.0 - 0.88 * sstep(0.84, 1.0, t))
            thick = 0.0042 * (1.0 - 0.55 * t)
            cx = jx + x_bias + 0.008 * math.sin(t * 2.4)
            cy = jy + sgn * (0.004 + 0.016 * t)
            cz = jz - t * length
            twist = sgn * (0.18 + 0.35 * t)
            ctw, stw = math.cos(twist), math.sin(twist)

            for i in range(nu_r):
                ang = (i / nu_r) * 2.0 * math.pi
                ly = width * math.sin(ang)
                lx = thick * math.cos(ang)
                # Rotate ribbon blade slightly around Z
                rx_p = lx * ctw - ly * stw
                ry_p = lx * stw + ly * ctw
                verts.append((cx + rx_p, cy + ry_p, cz))
                uvs.append((0.20 + 0.12 * (i / nu_r), 0.20 + 0.65 * t))

                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w_rib = sstep(0.04, 0.22, t)
                w[BONE_IDX[bname]] = w_rib
                w[BONE_IDX["knot"]] = 1.0 - w_rib
                w_list.append(w)

        rt = grid_tris(nu_r, nv_r, wrap_u=True, flip=True) + b0
        tris.extend(rt.tolist())

    return (
        np.array(verts, dtype=np.float64),
        np.array(tris, dtype=np.int32),
        np.array(uvs, dtype=np.float64),
        np.array(w_list, dtype=np.float64),
    )


# ===========================================================================
# PART 4: FITTED HOT-PINK LONG SLEEVES & DELICATE 3D HANDS
# ===========================================================================
def build_sleeves_and_hands():
    sl_v, sl_t, sl_uv, sl_w = [], [], [], []
    hd_v, hd_t, hd_uv, hd_w = [], [], [], []

    for sgn, sh_b, el_b, wr_b in (
        (1.0,  "sh_L", "el_L", "wr_L"),
        (-1.0, "sh_R", "el_R", "wr_R"),
    ):
        P_sh = REST_JOINTS[sh_b]
        P_el = REST_JOINTS[el_b]
        P_wr = REST_JOINTS[wr_b]

        # Build smooth shoulder-cap-to-wrist sleeve tube (tucked cleanly into rounded shoulder torso!)
        P_root = P_sh + np.array([0.0, -sgn * 0.032, -0.006])
        nu, nv = 24, 30
        b0 = len(sl_v)
        for j in range(nv):
            t = j / (nv - 1)   # 0 = shoulder tuck -> 0.52 = elbow -> 1.0 = wrist cuff
            if t <= 0.52:
                u_seg = t / 0.52
                center = P_root * (1.0 - u_seg) + P_el * u_seg
                # Smooth deltoid cap tapering gently toward elbow
                rad = 0.039 * (1.0 - 0.25 * u_seg) + 0.006 * math.exp(-(((u_seg - 0.18) / 0.22) ** 2))
            else:
                u_seg = (t - 0.52) / 0.48
                center = P_el * (1.0 - u_seg) + P_wr * u_seg
                # Forearm tapering to snug wrist cuff + subtle cuff rib gathers!
                rad = 0.030 * (1.0 - 0.28 * u_seg) + 0.0016 * math.sin(u_seg * 26.0) * sstep(0.55, 0.95, u_seg)

            # Orthonormal frame along arm tangent
            axis = (P_el - P_root) if t <= 0.52 else (P_wr - P_el)
            T = axis / (np.linalg.norm(axis) + 1e-12)
            B1 = np.cross(np.array([0.0, 0.0, 1.0]), T)
            B1 /= (np.linalg.norm(B1) + 1e-12)
            B2 = np.cross(T, B1)

            for i in range(nu):
                ang = (i / nu) * 2.0 * math.pi
                off = B1 * (rad * 1.04 * math.cos(ang)) + B2 * (rad * 0.94 * math.sin(ang))
                p = center + off
                sl_v.append(tuple(p))
                sl_uv.append((0.10 + 0.30 * (i / nu), 0.08 + 0.80 * t))

                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w_chest = 1.0 - sstep(0.0, 0.20, t)
                w_uarm = sstep(0.0, 0.20, t) * (1.0 - sstep(0.42, 0.62, t))
                w_farm = sstep(0.42, 0.62, t)
                w[BONE_IDX["chest"]] = w_chest
                w[BONE_IDX[sh_b]] = w_uarm
                w[BONE_IDX[el_b]] = w_farm
                sl_w.append(w)

        tris_arm = grid_tris(nu, nv, wrap_u=True, flip=(sgn < 0)) + b0
        sl_t.extend(tris_arm.tolist())

        # Delicate 3D Female Hand + 5 Sculpted Fingers emerging from wrist cuff (`surf_skin`)!
        arm_dir = (P_wr - P_el)
        arm_dir = arm_dir / (np.linalg.norm(arm_dir) + 1e-12)
        # Palm faces slightly down/inward in rest A-pose
        up_n = np.array([0.25, 0.0, 0.96])
        side_v = np.cross(up_n, arm_dir)
        side_v /= (np.linalg.norm(side_v) + 1e-12)
        dors_v = np.cross(arm_dir, side_v)

        # Palm loft (wrist to knuckles)
        nu_h, nv_h = 18, 10
        hb0 = len(hd_v)
        for j in range(nv_h):
            th = j / (nv_h - 1)
            c_palm = P_wr + arm_dir * (th * 0.036)
            w_palm = 0.016 + 0.008 * sstep(0.0, 0.75, th) * (1.0 - 0.15 * sstep(0.8, 1.0, th))
            t_palm = 0.011 * (1.0 - 0.28 * th)
            for i in range(nu_h):
                ang = (i / nu_h) * 2.0 * math.pi
                p = c_palm + side_v * (w_palm * math.cos(ang)) + dors_v * (t_palm * math.sin(ang))
                hd_v.append(tuple(p))
                hd_uv.append((0.70 + 0.12 * (i / nu_h), 0.58 + 0.18 * th))
                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w[BONE_IDX[wr_b]] = 0.85 + 0.15 * th
                w[BONE_IDX[el_b]] = 0.15 * (1.0 - th)
                hd_w.append(w)
        hd_t.extend((grid_tris(nu_h, nv_h, wrap_u=True, flip=False) + hb0).tolist())

        # 4 slender fingers + thumb with pale-pink manicured tips!
        finger_specs = [
            (-0.78, 0.030, 0.0044, -6.0),   # index / radial
            (-0.25, 0.034, 0.0045,  0.0),   # middle
            ( 0.28, 0.031, 0.0043,  4.0),   # ring
            ( 0.78, 0.025, 0.0038,  9.0),   # pinky
        ]
        for lat_f, f_len, f_rad, splay_deg in finger_specs:
            fb0 = len(hd_v)
            nu_f, nv_f = 10, 9
            f_base = P_wr + arm_dir * 0.034 + side_v * (lat_f * 0.020 * sgn)
            f_dir = arm_dir * math.cos(math.radians(splay_deg)) + side_v * (sgn * math.sin(math.radians(splay_deg)))
            for j in range(nv_f):
                tf = j / (nv_f - 1)
                r_cur = f_rad * (1.0 - 0.35 * tf) * (math.sqrt(max(0.0, 1.0 - max(0.0, (tf - 0.82) / 0.18) ** 2)))
                c_f = f_base + f_dir * (tf * f_len) - dors_v * (0.002 * tf * tf)
                for i in range(nu_f):
                    ang = (i / nu_f) * 2.0 * math.pi
                    p = c_f + side_v * (r_cur * math.cos(ang)) + dors_v * (r_cur * 0.88 * math.sin(ang))
                    hd_v.append(tuple(p))
                    # Dorsal tip maps to manicured pale-pink nail patch!
                    if tf > 0.72 and math.sin(ang) > 0.15:
                        hd_uv.append((0.88 + 0.06 * math.cos(ang), 0.96 - (tf - 0.72) / 0.28 * 0.10))
                    else:
                        hd_uv.append((0.72 + 0.08 * (i / nu_f), 0.62 + 0.16 * tf))
                    w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                    w[BONE_IDX[wr_b]] = 1.0
                    hd_w.append(w)
            hd_t.extend((grid_tris(nu_f, nv_f, wrap_u=True, flip=False) + fb0).tolist())

        # Thumb
        tb0 = len(hd_v)
        nu_f, nv_f = 10, 8
        t_base = P_wr + arm_dir * 0.014 + side_v * (-0.95 * 0.018 * sgn) - dors_v * 0.002
        t_dir = (arm_dir * 0.76 + side_v * (-0.62 * sgn))
        t_dir /= np.linalg.norm(t_dir)
        for j in range(nv_f):
            tf = j / (nv_f - 1)
            r_cur = 0.0050 * (1.0 - 0.32 * tf) * math.sqrt(max(0.0, 1.0 - max(0.0, (tf - 0.80) / 0.20) ** 2))
            c_f = t_base + t_dir * (tf * 0.026)
            for i in range(nu_f):
                ang = (i / nu_f) * 2.0 * math.pi
                p = c_f + side_v * (r_cur * math.cos(ang)) + dors_v * (r_cur * math.sin(ang))
                hd_v.append(tuple(p))
                hd_uv.append((0.72 + 0.08 * (i / nu_f), 0.62 + 0.15 * tf))
                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w[BONE_IDX[wr_b]] = 1.0
                hd_w.append(w)
        hd_t.extend((grid_tris(nu_f, nv_f, wrap_u=True, flip=False) + tb0).tolist())

    return (
        (np.array(sl_v, dtype=np.float64), np.array(sl_t, dtype=np.int32), np.array(sl_uv, dtype=np.float64), np.array(sl_w, dtype=np.float64)),
        (np.array(hd_v, dtype=np.float64), np.array(hd_t, dtype=np.int32), np.array(hd_uv, dtype=np.float64), np.array(hd_w, dtype=np.float64)),
    )


# ===========================================================================
# PART 5: VOLUMETRIC CENTER-PARTED LONG SILKY BLONDE HAIR (`surf_hair`)
# ===========================================================================
def build_blonde_hair():
    verts, tris, uvs, w_list = [], [], [], []

    # A. Main lush volumetric hair mantle + spherical scalp cap (parted cleanly at top midline y = 0!)
    nu, nv = 54, 38
    b0 = len(verts)

    def push_outside_skull(px, py, pz, min_clear=0.0055):
        """Guarantees inner/base hair surface never dips inside the spherical cranium dome!"""
        if pz < 0.885:
            return px, py, pz
        rx_s = 0.066 + min_clear
        ry_s = 0.056 + min_clear
        rz_s = 0.080 + min_clear
        dx = (px - 0.004) / rx_s
        dy = py / ry_s
        dz = (pz - 0.918) / rz_s
        r_e = math.sqrt(dx * dx + dy * dy + dz * dz)
        if r_e < 1.0 and r_e > 1e-6:
            k_push = 1.0 / r_e
            px = 0.004 + dx * k_push * rx_s
            py = dy * k_push * ry_s
            pz = 0.918 + dz * k_push * rz_s
        return px, py, pz

    for j in range(nv):
        tv = j / (nv - 1)   # 0 = center part root at crown -> 1 = feathered tips at mid-back / upper bust
        for i in range(nu):
            q = (i / (nu - 1)) * 2.0 - 1.0
            az = math.pi - q * (math.pi - 0.68)

            if tv < 0.22:
                # Spherical scalp wrap from center part line (y ~ 0) out over crown & temples down to z ~ 0.922!
                rt = tv / 0.22
                # Center part arc along top of skull from forehead hairline (x=+0.056, z=0.968) over crown (z=1.003) to back (x=-0.054)
                part_x = 0.056 * abs(q) - 0.052 * (1.0 - abs(q))
                part_y = math.copysign(0.0012, q) if abs(q) > 1e-4 else 0.0
                part_z = 0.918 + 0.085 * math.sqrt(max(0.05, 1.0 - ((part_x - 0.004) / 0.072) ** 2))

                skull_x = 0.004 + 0.072 * math.cos(az)
                skull_y = 0.062 * math.sin(az)
                skull_z = 0.926 - 0.012 * (1.0 - abs(q))

                # Spherical-style arch lift across chord so crown stays round & full!
                arch_lift = 0.014 * math.sin(rt * math.pi)
                x = part_x * (1.0 - rt) + skull_x * rt
                y = part_y * (1.0 - rt) + skull_y * rt
                z = part_z * (1.0 - rt) + skull_z * rt + arch_lift
                x, y, z = push_outside_skull(x, y, z, min_clear=0.0045 + 0.0025 * rt)
                thick_dir = np.array([math.cos(az) * rt, math.sin(az) * rt, 0.85 - 0.55 * rt])
            else:
                # Flowing long silky curtain with smooth U-shaped back hemline & face-framing front locks!
                ft = (tv - 0.22) / 0.78
                fl_blend = sstep(0.56, 0.88, abs(q))
                end_z = (0.555 + 0.032 * (q * q)) * (1.0 - fl_blend) + 0.672 * fl_blend
                start_z = 0.926 - 0.012 * (1.0 - abs(q))
                z = start_z * (1.0 - ft) + end_z * ft

                sh_drape = sstep(0.14, 0.56, ft)
                base_rx = 0.072 + 0.018 * sh_drape
                base_ry = 0.062 + 0.066 * sh_drape * (0.45 + 0.55 * (q * q))

                x = 0.004 + base_rx * math.cos(az)
                y = base_ry * math.sin(az)

                # Front locks curve gracefully forward over clavicles onto upper outer slope of bust
                if abs(q) > 0.58:
                    fl_k = sstep(0.58, 0.95, abs(q)) * sstep(0.12, 0.75, ft)
                    x += 0.070 * fl_k
                    y += math.copysign(0.022 * fl_k, q)

                wave = 0.0045 * math.sin(q * 18.0) * sstep(0.1, 0.8, ft)
                x += wave * math.cos(az)
                y += wave * math.sin(az)
                x, y, z = push_outside_skull(x, y, z, min_clear=0.0065)
                thick_dir = np.array([math.cos(az), math.sin(az), 0.08])

            thick_dir = thick_dir / (np.linalg.norm(thick_dir) + 1e-12)
            part_dip = 1.0 - 0.45 * math.exp(-((tv / 0.035) ** 2))
            thick = (0.0105 * math.sin(min(1.0, tv * 1.12) * math.pi * 0.88) + 0.0040) * part_dip
            p_out = np.array([x, y, z]) + thick_dir * thick
            verts.append(tuple(p_out))
            uvs.append(((q + 1.0) * 0.5, tv))

            w = np.zeros(len(BONE_ORDER), dtype=np.float64)
            if tv < 0.28:
                w[BONE_IDX["head"]] = 1.0 - sstep(0.18, 0.28, tv)
                w[BONE_IDX["hair_1"]] = sstep(0.18, 0.28, tv)
            elif tv < 0.56:
                k = sstep(0.28, 0.56, tv)
                w[BONE_IDX["hair_1"]] = 1.0 - k
                w[BONE_IDX["hair_2"]] = k
            else:
                k = sstep(0.56, 0.88, tv)
                w[BONE_IDX["hair_2"]] = 1.0 - k
                w[BONE_IDX["hair_3"]] = k
            w_list.append(w)

    # Inner underside of hair sheet (pushed safely outside skull dome!)
    n_outer = len(verts) - b0
    for idx_o in range(n_outer):
        j = idx_o // nu
        i = idx_o % nu
        tv = j / (nv - 1)
        q = (i / (nu - 1)) * 2.0 - 1.0
        az = math.pi - q * (math.pi - 0.68)
        inward = np.array([math.cos(az) * sstep(0.0, 0.20, tv), math.sin(az) * sstep(0.0, 0.20, tv), 0.35 * (1.0 - sstep(0.0, 0.25, tv)) + 0.10])
        inward /= (np.linalg.norm(inward) + 1e-12)
        thick_in = 0.0085 * sstep(0.03, 0.26, tv) * (1.0 - 0.78 * sstep(0.82, 1.0, tv))
        p_in = np.array(verts[b0 + idx_o]) - inward * thick_in
        px, py, pz = push_outside_skull(float(p_in[0]), float(p_in[1]), float(p_in[2]), min_clear=0.0025)
        verts.append((px, py, pz))
        uvs.append(uvs[b0 + idx_o])
        w_list.append(w_list[b0 + idx_o].copy())

    t_out = grid_tris(nu, nv, wrap_u=False, flip=True) + b0
    t_in = grid_tris(nu, nv, wrap_u=False, flip=False) + (b0 + n_outer)
    tris.extend(t_out.tolist())
    tris.extend(t_in.tolist())

    # Stitch left edge (i=0), right edge (i=nu-1), and bottom tip edge (j=nv-1)
    for j in range(nv - 1):
        # Left edge i=0
        o0, o1 = b0 + j * nu, b0 + (j + 1) * nu
        i0, i1 = o0 + n_outer, o1 + n_outer
        tris.extend([(o0, i0, i1), (o0, i1, o1)])
        # Right edge i=nu-1
        o0, o1 = b0 + j * nu + (nu - 1), b0 + (j + 1) * nu + (nu - 1)
        i0, i1 = o0 + n_outer, o1 + n_outer
        tris.extend([(o0, o1, i1), (o0, i1, i0)])
    for i in range(nu - 1):
        o0, o1 = b0 + (nv - 1) * nu + i, b0 + (nv - 1) * nu + (i + 1)
        i0, i1 = o0 + n_outer, o1 + n_outer
        tris.extend([(o0, i0, i1), (o0, i1, o1)])

    return (
        np.array(verts, dtype=np.float64),
        np.array(tris, dtype=np.int32),
        np.array(uvs, dtype=np.float64),
        np.array(w_list, dtype=np.float64),
    )


# ===========================================================================
# PART 6: ANKLES & CHUNKY HOT-PINK ATHLETIC SNEAKERS (`surf_skin` C + `surf_sneakers`)
# ===========================================================================
def build_ankles_and_sneakers():
    ak_v, ak_t, ak_uv, ak_w = [], [], [], []
    sn_v, sn_t, sn_uv, sn_w = [], [], [], []

    for sgn, kn_b, an_b in ((1.0, "kn_L", "an_L"), (-1.0, "kn_R", "an_R")):
        cy = sgn * 0.066

        # 1. Exposed Ankle Skin Collar (z = 0.076 .. 0.122)
        nu_a, nv_a = 18, 7
        ab0 = len(ak_v)
        for j in range(nv_a):
            ta = j / (nv_a - 1)
            z = 0.122 - ta * (0.122 - 0.076)
            r = 0.025 - 0.002 * math.sin(ta * math.pi)
            for i in range(nu_a):
                ang = (i / nu_a) * 2.0 * math.pi
                ak_v.append((-0.004 + r * 1.08 * math.cos(ang), cy + r * 0.95 * math.sin(ang), z))
                ak_uv.append((0.70 + 0.10 * (i / nu_a), 0.78 + 0.10 * ta))
                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w[BONE_IDX[kn_b]] = 1.0 - sstep(0.2, 0.85, ta)
                w[BONE_IDX[an_b]] = sstep(0.2, 0.85, ta)
                ak_w.append(w)
        ak_t.extend((grid_tris(nu_a, nv_a, wrap_u=True, flip=False) + ab0).tolist())

        # 2. Sculpted 3D Hot-Pink Athletic Sneaker (z = 0.000 .. 0.088, heel x=-0.048 to rounded toe x=+0.102)
        nu_s, nv_s = 32, 20
        sb0 = len(sn_v)
        for j in range(nv_s):
            ts = j / (nv_s - 1)
            # ts: 0.0 = ankle collar opening -> 0.68 = midsole wall -> 0.86 = outsole bottom perimeter -> 1.0 = sole center!
            for i in range(nu_s):
                ang = (i / nu_s) * 2.0 * math.pi   # ang = 0 is +X (toe!), +-pi is -X (heel!)
                ca, sa = math.cos(ang), math.sin(ang)

                # Foot last horizontal contour (asymmetric athletic shoe silhouette!)
                len_f = 0.102 if ca >= 0 else 0.046
                wid_f = 0.036 + 0.006 * max(0.0, ca)   # slightly wider forefoot than heel

                if ts <= 0.65:
                    # Upper shoe vamp, tongue arch, & padded ankle collar!
                    u_up = ts / 0.65
                    # Collar ring at u_up=0 expanding out to full shoe last at u_up=1
                    collar_r_x = 0.032
                    collar_r_y = 0.027
                    collar_cx = -0.006

                    shoe_x = 0.026 + (0.076 * ca if ca >= 0 else 0.072 * ca)
                    shoe_y = wid_f * sa

                    # Smooth instep slope & rounded puffy toe box!
                    blend = u_up ** 0.78
                    x = collar_cx * (1.0 - blend) + shoe_x * blend
                    y = cy + (collar_r_y * sa) * (1.0 - blend) + shoe_y * blend

                    # Height profile: raised padded tongue at front (ca > 0.4, u_up < 0.35), low-cut ankle notch at sides, heel tab at back!
                    tongue_lift = 0.015 * math.exp(-(((1.0 - ca) / 0.25) ** 2)) * (1.0 - sstep(0.0, 0.42, u_up))
                    heel_tab = 0.010 * math.exp(-(((1.0 + ca) / 0.25) ** 2)) * (1.0 - sstep(0.0, 0.35, u_up))
                    toe_puff = 0.016 * math.sin(u_up * math.pi) * max(0.0, ca)
                    z = 0.080 * (1.0 - u_up) + 0.022 * u_up + tongue_lift + heel_tab + toe_puff

                    # Map front vamp/instep (ca > -0.10) to laces/toe-box, and sides/heel cleanly to breathable hot-pink mesh!
                    front_k = sstep(-0.10, 0.35, ca)
                    u_front = 0.50 + 0.36 * (shoe_y / 0.042) * (0.35 + 0.65 * u_up)
                    v_front = 0.22 + 0.54 * np.clip((x - (-0.010)) / (0.102 - (-0.010)), 0.0, 1.0)
                    u_heel = 0.12 + 0.16 * abs(sa)
                    v_heel = 0.05 + 0.10 * u_up
                    u_tex = u_heel * (1.0 - front_k) + u_front * front_k
                    v_tex = v_heel * (1.0 - front_k) + v_front * front_k
                elif ts <= 0.86:
                    # Sculpted chunky rubber midsole wall (z = 0.022 down to 0.002) with slight flare!
                    ms = (ts - 0.65) / 0.21
                    flare = 1.0 + 0.07 * ms
                    x = 0.026 + (0.076 * ca if ca >= 0 else 0.072 * ca) * flare
                    y = cy + wid_f * sa * flare
                    z = 0.022 * (1.0 - ms) + 0.002 * ms
                    u_tex = (i / nu_s)
                    v_tex = 0.82 + 0.16 * ms
                else:
                    # Flat treaded outsole bottom closing cleanly to center point!
                    bt = (ts - 0.86) / 0.14
                    flare = 1.07 * (1.0 - bt)
                    x = 0.026 + (0.076 * ca if ca >= 0 else 0.072 * ca) * flare
                    y = cy + wid_f * sa * flare
                    z = 0.002 * (1.0 - bt)
                    u_tex = 0.50 + 0.20 * sa * (1.0 - bt)
                    v_tex = 0.90 + 0.08 * ca * (1.0 - bt)

                sn_v.append((x, y, z))
                sn_uv.append((u_tex, v_tex))
                w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                w[BONE_IDX[an_b]] = 1.0
                sn_w.append(w)

        sn_t.extend((grid_tris(nu_s, nv_s, wrap_u=True, flip=False) + sb0).tolist())

        # Add tied 3D hot-pink shoelace bow loops on top of tongue (z ~ 0.072, x ~ 0.026)!
        for loop_sgn in (-1.0, 1.0):
            lb0 = len(sn_v)
            nu_l, nv_l = 8, 12
            for j in range(nv_l):
                tl = (j / (nv_l - 1)) * math.pi
                lc_x = 0.024 + 0.006 * math.sin(tl)
                lc_y = cy + loop_sgn * (0.004 + 0.019 * math.sin(tl))
                lc_z = 0.071 + 0.006 * math.sin(tl * 2.0)
                for i in range(nu_l):
                    a2 = (i / nu_l) * 2.0 * math.pi
                    sn_v.append((lc_x + 0.0024 * math.cos(a2), lc_y, lc_z + 0.0024 * math.sin(a2)))
                    sn_uv.append((0.50, 0.36))
                    w = np.zeros(len(BONE_ORDER), dtype=np.float64)
                    w[BONE_IDX[an_b]] = 1.0
                    sn_w.append(w)
            sn_t.extend((grid_tris(nu_l, nv_l, wrap_u=True, flip=False) + lb0).tolist())

    return (
        (np.array(ak_v, dtype=np.float64), np.array(ak_t, dtype=np.int32), np.array(ak_uv, dtype=np.float64), np.array(ak_w, dtype=np.float64)),
        (np.array(sn_v, dtype=np.float64), np.array(sn_t, dtype=np.int32), np.array(sn_uv, dtype=np.float64), np.array(sn_w, dtype=np.float64)),
    )


# ===========================================================================
# PART 7: SEAMLESS BIFURCATED BLUE SKINNY JEANS WITH SCULPTED GLUTES (Blender Voxel Union!)
# ===========================================================================
def build_seamless_jeans_bpy(bpy):
    """Uses Blender 5.2's Voxel Remesh + Corrective Smooth + Quadric Decimate to fuse
    a curvy high-waisted pelvis + twin rounded glutes + left/right skinny jean legs into a
    100% seamless bifurcated garment, then assigns crisp seam-split Front/Back denim UVs!"""
    import bmesh

    # 1. Pelvis + High Waist + Sculpted Twin Glutes Mesh (z in 0.405 .. 0.538)
    nu_p, nv_p = 56, 28
    pv, pf = [], []
    for j in range(nv_p):
        t = j / (nv_p - 1)   # 0 = top high waist (z=0.538) -> 1 = lower pelvis saddle (z=0.405)
        z = 0.538 - t * (0.538 - 0.405)
        # Curvy hourglass flare from waist (ry=0.089) to full hips (ry=0.132 at z ~ 0.455) then tapering to saddle
        hip_curve = math.sin(min(1.0, t * 1.12) * math.pi * 0.82)
        ry = 0.089 + 0.044 * hip_curve
        rx = 0.068 + 0.024 * hip_curve
        # Pinch bottom saddle cleanly between thighs
        saddle_pinch = sstep(0.75, 1.0, t)
        for i in range(nu_p):
            th = (i / nu_p) * 2.0 * math.pi   # 0 = +X front, +-pi = -X back
            ct, st = math.cos(th), math.sin(th)
            x = rx * ct * (1.0 - 0.35 * saddle_pinch * (ct * ct))
            y = ry * st

            # Sculpted twin rounded glutes on posterior side (|th| > 1.75) with realistic intergluteal cleft at th = +-pi!
            a_back = abs(abs(th) - math.pi)   # 0 at dead center back, increases outward
            glute_h = math.exp(-(((z - 0.448) / 0.052) ** 2))
            glute_lobe = math.exp(-(((a_back - 0.52) / 0.50) ** 2))
            cleft = 1.0 - 0.62 * math.exp(-((a_back / 0.14) ** 2))
            glute_push = 0.036 * glute_h * glute_lobe * cleft
            x -= glute_push
            z_adj = z - 0.008 * saddle_pinch * (1.0 - st * st)
            pv.append((x, y, z_adj))

    # Close top waist cap & bottom saddle cap so voxel remesher sees a watertight solid!
    top_c = len(pv)
    pv.append((0.0, 0.0, 0.538))
    bot_c = len(pv)
    pv.append((0.0, 0.0, 0.405))
    pf_grid = grid_tris(nu_p, nv_p, wrap_u=True, flip=True)
    pf.extend(pf_grid.tolist())
    for i in range(nu_p):
        i1 = (i + 1) % nu_p
        pf.append((top_c, i1, i))
        b_i = (nv_p - 1) * nu_p + i
        b_i1 = (nv_p - 1) * nu_p + i1
        pf.append((bot_c, b_i, b_i1))

    def make_bobj(name, verts_l, faces_l):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts_l, [], [tuple(f) for f in faces_l])
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        return ob

    objs = [make_bobj("jeans_pelvis", pv, pf)]

    # 2. Left & Right Fitted Skinny Jean Legs (z = 0.465 down to rolled ankle cuff z = 0.114)
    for sgn, tag in ((1.0, "L"), (-1.0, "R")):
        nu_l, nv_l = 36, 36
        lv, lf = [], []
        for j in range(nv_l):
            t = j / (nv_l - 1)   # 0 = upper thigh/glute blend (z=0.465) -> 0.55 = knee (z=0.268) -> 1.0 = cuff (z=0.114)
            z = 0.465 - t * (0.465 - 0.114)
            cy = sgn * (0.062 + 0.004 * t)
            cx = 0.004 * math.sin(t * math.pi) - 0.003 * sstep(0.5, 1.0, t)

            # Thigh -> knee -> calf -> rolled ankle cuff taper!
            thigh_full = (1.0 - sstep(0.0, 0.54, t))
            calf_muscle = math.exp(-(((t - 0.70) / 0.14) ** 2))
            cuff_roll = math.exp(-(((t - 0.975) / 0.025) ** 2))
            rx = 0.064 * thigh_full + 0.041 * (1.0 - thigh_full) * (1.0 - 0.30 * sstep(0.55, 1.0, t)) + 0.006 * calf_muscle + 0.0025 * cuff_roll
            ry = 0.062 * thigh_full + 0.039 * (1.0 - thigh_full) * (1.0 - 0.30 * sstep(0.55, 1.0, t)) + 0.005 * calf_muscle + 0.0025 * cuff_roll

            for i in range(nu_l):
                th = (i / nu_l) * 2.0 * math.pi
                ct, st = math.cos(th), math.sin(th)
                # Slightly flatten medial inner-thigh near crotch (t < 0.25) so left & right thighs have a crisp clean gap!
                medial = (sgn * st < -0.2) and (t > 0.14)
                ry_eff = ry * (0.86 if (medial and t < 0.32) else 1.0)
                x = cx + rx * ct - (0.005 * calf_muscle * max(0.0, -ct))
                y = cy + ry_eff * st
                lv.append((x, y, z))

        tc = len(lv)
        lv.append((0.0, sgn * 0.062, 0.465))
        bc = len(lv)
        lv.append((-0.003, sgn * 0.066, 0.114))
        lf.extend(grid_tris(nu_l, nv_l, wrap_u=True, flip=True).tolist())
        for i in range(nu_l):
            i1 = (i + 1) % nu_l
            lf.append((tc, i1, i))
            bi = (nv_l - 1) * nu_l + i
            bi1 = (nv_l - 1) * nu_l + i1
            lf.append((bc, bi, bi1))
        objs.append(make_bobj(f"jeans_leg_{tag}", lv, lf))

    # Join & Voxel Remesh + Smooth + Decimate in Blender 5.2!
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j_ob = bpy.context.active_object

    rem = j_ob.modifiers.new("Remesh", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = 0.0036
    rem.adaptivity = 0.0

    sm = j_ob.modifiers.new("Smooth", "SMOOTH")
    sm.factor = 0.55
    sm.iterations = 6

    dec = j_ob.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = 0.20

    deps = bpy.context.evaluated_depsgraph_get()
    eval_ob = j_ob.evaluated_get(deps)
    eval_me = eval_ob.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(eval_me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    V_raw = np.array([(v.co.x, v.co.y, v.co.z) for v in bm.verts], dtype=np.float64)
    F_raw = np.array([[v.index for v in f.verts] for f in bm.faces], dtype=np.int32)
    bm.free()
    eval_ob.to_mesh_clear()
    bpy.data.objects.remove(j_ob, do_unlink=True)

    # Split Front (nx >= 0) vs Back (nx < 0) triangles onto their own clean UV vertices along the physical denim outseam/inseam!
    N_raw = compute_normals(V_raw, F_raw)
    t_pts = V_raw[F_raw]
    fn = np.cross(t_pts[:, 1] - t_pts[:, 0], t_pts[:, 2] - t_pts[:, 0])
    is_front = fn[:, 0] >= 0.0

    # Compute smooth analytical skinning weights on V_raw first so shared seam vertices deform identically!
    W_raw = np.zeros((len(V_raw), len(BONE_ORDER)), dtype=np.float64)
    for idx, (x, y, z) in enumerate(V_raw):
        w_waist = sstep(0.495, 0.538, z) * 0.65
        w_pelv = (1.0 - w_waist) * (1.0 - sstep(0.405, 0.455, 0.538 - (z - 0.405)))  # wait: simpler explicit height!
        w_pelv = (1.0 - w_waist) * sstep(0.395, 0.468, z)
        rem_leg = max(0.0, 1.0 - w_waist - w_pelv)
        w_shin = rem_leg * (1.0 - sstep(0.235, 0.300, z))
        w_thigh = rem_leg - w_shin

        W_raw[idx, BONE_IDX["waist"]] = w_waist
        W_raw[idx, BONE_IDX["pelvis"]] = w_pelv
        if y >= 0.0:
            W_raw[idx, BONE_IDX["hip_L"]] = w_thigh
            W_raw[idx, BONE_IDX["kn_L"]] = w_shin
        else:
            W_raw[idx, BONE_IDX["hip_R"]] = w_thigh
            W_raw[idx, BONE_IDX["kn_R"]] = w_shin

    # Build split vertex list (front UV island vs back UV island) while preserving smoothed 3D normals!
    v_map = {}
    V_out, N_out, UV_out, W_out, F_out = [], [], [], [], []

    for fi, tri in enumerate(F_raw):
        fr = bool(is_front[fi])
        new_tri = []
        for vi in tri:
            key = (int(vi), fr)
            if key not in v_map:
                x, y, z = V_raw[vi]
                # Normalized vertical v_tex: 0.008 at waist (z=0.538) -> 0.955 at ankle cuff (z=0.114)
                v_tex = np.clip(0.008 + (0.538 - z) / (0.538 - 0.114) * 0.947, 0.005, 0.985)
                # Normalized horizontal span at height z so legs stay aligned with hip panels!
                half_span = 0.135 if z > 0.42 else 0.118
                y_norm = np.clip(y / half_span, -0.98, 0.98)
                if fr:
                    # Front UV: u = 0.25 is y=0, +Y (left hip) -> u = 0.02, -Y (right hip) -> u = 0.48
                    u_tex = 0.25 - y_norm * 0.23
                else:
                    # Back UV: u = 0.75 is y=0, -Y (right glute) -> u = 0.52, +Y (left glute) -> u = 0.98
                    u_tex = 0.75 + y_norm * 0.23

                v_map[key] = len(V_out)
                V_out.append((x, y, z))
                N_out.append(tuple(N_raw[vi]))
                UV_out.append((float(u_tex), float(v_tex)))
                W_out.append(W_raw[vi])
            new_tri.append(v_map[key])
        F_out.append(tuple(new_tri))

    return (
        np.array(V_out, dtype=np.float64),
        np.array(F_out, dtype=np.int32),
        np.array(UV_out, dtype=np.float64),
        np.array(W_out, dtype=np.float64),
    )


# ===========================================================================
# CHARACTER ANIMATION POSES (Inspired directly by Videos 1, 2, & 3!)
# ===========================================================================
def pose_standing_hips(phase):
    """Video 1 inspiration: Standing with hands resting confidently on hips,
    warm smile, gentle hip sway, breathing, and soft hair drift."""
    s = math.sin(phase)
    c = math.cos(phase)
    rots = {
        "pelvis":   (2.5 * s, 0.0, 3.0 * s),
        "waist":    (-2.0 * s, -2.0 + 1.2 * c, -2.0 * s),
        "chest":    (-1.5 * s, -3.5 + 1.8 * s, 0.0),
        "bust_L":   (0.0, 1.8 * c, 0.8 * s),
        "bust_R":   (0.0, 1.8 * c, -0.8 * s),
        "ribbon_L": (2.5 * s, 2.0 + 2.0 * c, 0.0),
        "ribbon_R": (-2.0 * s, 2.0 - 2.0 * c, 0.0),
        "neck":     (1.5 * s, 2.5, 0.0),
        "head":     (3.5 * c, 3.0 + 2.0 * s, -4.0 * s),
        "hair_1":   (2.0 * s, 2.0, 0.0),
        "hair_2":   (4.5 * c, 3.5 + 2.5 * s, 0.0),
        "hair_3":   (6.5 * s, 4.0 + 3.5 * c, 0.0),
        # Akimbo hands-on-hips pose (elbows flared out +-Y, hands turned inward onto jeans waist!)
        "sh_L":     (14.0, -8.0, -24.0),
        "el_L":     (-68.0, 28.0, 62.0),
        "wr_L":     (18.0, -20.0, 12.0),
        "sh_R":     (-14.0, -8.0, 24.0),
        "el_R":     (68.0, 28.0, -62.0),
        "wr_R":     (-18.0, -20.0, -12.0),
        "hip_L":    (-1.5 * s, -2.0, 0.0),
        "kn_L":     (0.0, 4.0, 0.0),
        "an_L":     (0.0, -2.0, 0.0),
        "hip_R":    (-1.5 * s, 2.0, 0.0),
        "kn_R":     (0.0, 3.0, 0.0),
        "an_R":     (0.0, -2.0, 0.0),
    }
    off = (0.0, 0.006 * s, 0.004 * abs(s))
    return rots, off


def pose_joyful_wave(phase):
    """Video 2 inspiration ('Hi there, let's have some fun! Weee!'):
    Both arms raised high waving enthusiastically side-to-side, joyful bounce!"""
    s = math.sin(phase)
    s2 = math.sin(phase * 2.0)
    c = math.cos(phase)
    rots = {
        "pelvis":   (4.5 * s, 0.0, 5.0 * s),
        "waist":    (2.5 * s, -4.0 + 2.0 * s2, -3.0 * s),
        "chest":    (4.0 * s, -6.0 + 3.0 * s2, 4.0 * c),
        "bust_L":   (1.5 * s, 4.5 * math.sin(phase * 2.0 - 0.5), 1.5 * c),
        "bust_R":   (-1.5 * s, 4.5 * math.sin(phase * 2.0 - 0.5), -1.5 * c),
        "ribbon_L": (6.0 * s, 5.0 + 6.0 * s2, 4.0 * c),
        "ribbon_R": (-6.0 * s, 5.0 - 6.0 * s2, -4.0 * c),
        "neck":     (-3.0 * s, 2.0, 0.0),
        "head":     (-8.0 * s, -4.0 + 3.0 * c, 6.0 * s),
        "hair_1":   (5.0 * s, 4.0 + 2.0 * s2, 0.0),
        "hair_2":   (10.0 * c, 6.0 + 4.0 * s, 0.0),
        "hair_3":   (14.0 * s, 8.0 + 5.0 * c, 0.0),
        # Arms raised high waving! (v2_f060.png)
        "sh_L":     (-62.0 + 10.0 * s, -18.0, 12.0 + 14.0 * s),
        "el_L":     (-52.0 + 18.0 * c, -24.0, 22.0 + 16.0 * s),
        "wr_L":     (14.0 * s2, -12.0, 18.0 * c),
        "sh_R":     (62.0 + 10.0 * s, -18.0, -12.0 + 14.0 * s),
        "el_R":     (52.0 + 18.0 * c, -24.0, -22.0 + 16.0 * s),
        "wr_R":     (14.0 * s2, -12.0, 18.0 * c),
        "hip_L":    (-2.0 * s, -3.0 + 3.0 * s2, 2.0),
        "kn_L":     (0.0, 6.0 - 3.0 * s2, 0.0),
        "an_L":     (0.0, -3.0, 0.0),
        "hip_R":    (-2.0 * s, -3.0 - 3.0 * s2, -2.0),
        "kn_R":     (0.0, 6.0 + 3.0 * s2, 0.0),
        "an_R":     (0.0, -3.0, 0.0),
    }
    off = (0.0, 0.012 * s, 0.014 * abs(s))
    return rots, off


def pose_spread_ready(t01):
    """Video 3 pre-launch ('Whoa, ready for this?'): Spreading arms wide & arching chest!"""
    k = sstep(0.0, 1.0, t01)
    rots = {
        "pelvis":   (0.0, 4.0 * k, 0.0),
        "waist":    (0.0, -8.0 * k, 0.0),
        "chest":    (0.0, -12.0 * k, 0.0),
        "bust_L":   (0.0, -3.0 * k, 0.0),
        "bust_R":   (0.0, -3.0 * k, 0.0),
        "ribbon_L": (4.0 * k, 12.0 * k, 0.0),
        "ribbon_R": (-4.0 * k, 12.0 * k, 0.0),
        "neck":     (0.0, -6.0 * k, 0.0),
        "head":     (0.0, -10.0 * k, 0.0),
        "hair_1":   (0.0, 12.0 * k, 0.0),
        "hair_2":   (0.0, 18.0 * k, 0.0),
        "hair_3":   (0.0, 24.0 * k, 0.0),
        "sh_L":     (-12.0 * k, 8.0 * k, -26.0 * k),
        "el_L":     (0.0, 6.0 * k, -10.0 * k),
        "wr_L":     (0.0, -18.0 * k, 0.0),
        "sh_R":     (12.0 * k, 8.0 * k, 26.0 * k),
        "el_R":     (0.0, 6.0 * k, 10.0 * k),
        "wr_R":     (0.0, -18.0 * k, 0.0),
        "hip_L":    (0.0, 4.0 * k, 3.0 * k),
        "kn_L":     (0.0, 8.0 * k, 0.0),
        "hip_R":    (0.0, 4.0 * k, -3.0 * k),
        "kn_R":     (0.0, 8.0 * k, 0.0),
    }
    return rots, (0.0, 0.0, 0.010 * k)


def pose_projectile_flight(phase):
    """Video 3 HERO PROJECTILE FLIGHT POSE (v3_f120.png & v3_f168.png)!
    She flies horizontally toward +X:
      - Pelvis pitched +82 deg forward so torso/legs stream horizontally along X!
      - Spine & neck arched gracefully UPWARD (negative Y pitch) so her joyful face looks forward (+X)!
      - Twin hot-pink bust leads forward/downward as aerodynamic nosecones!
      - Tie-front ribbons stream backward (-X) underneath her waist fluttering in the slipstream!
      - Long blonde hair billows & ripples backward (-X) in a travelling wind wave!
      - Pink-sleeved arms sweep out & back (~38 deg swept wings) with upturned hands!
      - Blue-jeaned legs trail behind with skydiver knee bend & pink sneakers fluttering!"""
    s = math.sin(phase)
    c = math.cos(phase)
    s2 = math.sin(phase * 2.0)
    c2 = math.cos(phase * 2.0)

    rots = {
        # Pitch whole body forward +82 deg around Y so +Z becomes +X, with gentle banking roll!
        "pelvis":   (4.5 * s, 82.0 + 1.8 * c, 2.5 * c),
        "waist":    (-1.5 * s, -14.0 + 1.5 * s2, 0.0),
        "chest":    (-2.0 * s, -22.0 + 2.0 * c2, 0.0),
        # Aerodynamic nosecone settle + slight flutter
        "bust_L":   (0.0, 5.0 + 1.8 * s2, 1.2 * s),
        "bust_R":   (0.0, 5.0 + 1.8 * s2, -1.2 * s),
        # Bow ribbons stream backward underneath waist (pitch toward legs!) & flutter rapidly!
        "knot":     (0.0, 12.0, 0.0),
        "ribbon_L": (8.0 * s2, -26.0 + 9.0 * math.sin(phase * 2.0 + 0.4), 6.0 * c2),
        "ribbon_R": (-8.0 * s2, -28.0 + 9.0 * math.cos(phase * 2.0 - 0.3), -6.0 * c2),
        # Arched neck & lifted joyful laughing head looking straight ahead (+X) & slightly up!
        "neck":     (0.0, -24.0 + 1.5 * s, 0.0),
        "head":     (-3.5 * s, -26.0 + 2.0 * c, 2.5 * s),
        # Travelling wind-wave billowing hair backward & upward (like v3_f120 & v3_f168)!
        "hair_1":   (3.0 * s, 44.0 + 5.0 * math.sin(phase), 2.0 * c),
        "hair_2":   (5.0 * c, 22.0 + 9.0 * math.sin(phase - 1.1), 4.0 * s),
        "hair_3":   (7.0 * s, 12.0 + 13.0 * math.sin(phase - 2.2), 6.0 * c),
        # Swept-back pink sleeves & upturned wingtip hands!
        "sh_L":     (18.0 + 3.0 * s, 26.0 + 2.5 * c, -34.0 + 3.0 * s),
        "el_L":     (8.0, 10.0 + 2.0 * s2, -12.0),
        "wr_L":     (-12.0, -28.0 + 5.0 * c2, 8.0),
        "sh_R":     (-18.0 + 3.0 * s, 26.0 - 2.5 * c, 34.0 + 3.0 * s),
        "el_R":     (-8.0, 10.0 - 2.0 * s2, 12.0),
        "wr_R":     (12.0, -28.0 - 5.0 * c2, -8.0),
        # Skydiver trailing denim legs & gently kicking/fluttering hot-pink sneakers!
        "hip_L":    (-3.0, -10.0 + 5.5 * s, 5.5 + 1.5 * c),
        "kn_L":     (0.0, 24.0 + 7.0 * c, 0.0),
        "an_L":     (0.0, 18.0 + 6.0 * s, 0.0),
        "hip_R":    (3.0, -10.0 - 5.5 * s, -5.5 - 1.5 * c),
        "kn_R":     (0.0, 24.0 - 7.0 * c, 0.0),
        "an_R":     (0.0, 18.0 - 6.0 * s, 0.0),
    }
    # Center projectile around (0, 0, 0) in flight!
    off = (-0.06, 0.008 * s, -0.44 + 0.014 * c)
    return rots, off
