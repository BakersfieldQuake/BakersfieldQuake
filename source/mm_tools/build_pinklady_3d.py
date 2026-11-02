r"""Reconstructs the True 3D Textured Pink Lady Mesh & 1024x1024 Texture
from the 145-frame 360-degree turntable clip.

Anatomical 3-part webbing-free & clip-free 3D reconstruction:
  1. Central Head + Long Blonde Hair + Twin Buoyant Pink Spheres carved from 50 calibrated turntable views
     (with chroma-clean segmentation that excludes 100% of the white pedestal, plus sculpted 3D front/rear pod valleys).
  2. Full-length Raised V-Arms & Open Hands sculpted directly from the exact front (f=144) & rear (f=73) silhouettes
     with anatomical cylindrical cross-sections into the shoulders so slender wrists/hands never erode under turntable zoom.
  3. Front Tie-Knot & Dangling Twin Pink Ribbons sculpted cleanly below the pod valley.
  4. Region-pure 1024x1024 texture bake (separating raised arms vs central hair/face/pods so pink sleeves never bleed onto blonde hair).
"""
import math
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
OUT_DIR = os.path.join(HERE, "out", "skyveh")
DEFAULT_VID = r"C:\Users\qxdc\.gemini\antigravity\brain\7eaea46a-2e55-469f-9e43-8368b8dfe4ff\.user_uploaded\media_1793417816011_5c97eac8.mp4"
VIDEO = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VID
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

LANDMARKS = [
    (4, 0.0),
    (45, 90.0),
    (73, 180.0),
    (101, 270.0),
    (144, 360.0),
]
SIGN = -1.0
F_DOWN = 2
TRI_BUDGET = 3800
TEX_SIZE = 1024
HEIGHT_UNITS = 58.0


def frame_angle_deg(f_idx):
    for (f0, a0), (f1, a1) in zip(LANDMARKS, LANDMARKS[1:]):
        if f0 <= f_idx <= f1:
            return a0 + (a1 - a0) * (f_idx - f0) / float(f1 - f0)
    return 360.0 if f_idx > LANDMARKS[-1][0] else 0.0


def segment_pinklady_mask(rgb):
    """Chroma-pure segmentation: keeps 100% of hands, hair, face, pink pods, and dangling ribbons,
    while rejecting 100% of the pale studio wall and bright/shaded floor pedestal."""
    H, W = rgb.shape[:2]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    bg_row = np.median(np.concatenate([lab[:, :45, :], lab[:, -45:, :]], axis=1), axis=1)
    dl = lab[..., 0] - bg_row[:, None, 0]
    dab = np.hypot(lab[..., 1] - bg_row[:, None, 1], lab[..., 2] - bg_row[:, None, 2])
    rows = np.arange(H)[:, None]

    # Note: only negative dl (dark brows/lashes/hair roots above r=480) is allowed without chroma,
    # so bright/shaded grey pedestal below r=720 (dab < 5) is 0% included!
    fg_raw = (
        ((dab > 12.5) & (rows < 875))
        | ((dab > 9.0) & (rows < 220))   # pale fingertips at top of frame
        | ((dl < -18.0) & (rows < 480))  # dark eyelashes/pupils/parting
    )
    m = ndimage.binary_opening(fg_raw, structure=np.ones((3, 3), bool))
    m = ndimage.binary_closing(m, structure=np.ones((5, 5), bool))
    lbl, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lbl, range(1, n + 1))
        m = lbl == (1 + int(np.argmax(sizes)))

    inv = np.logical_not(m)
    ilbl, inum = ndimage.label(inv)
    if inum > 1:
        isizes = ndimage.sum(inv, ilbl, range(1, inum + 1))
        for k_id, sz in enumerate(isizes, start=1):
            if k_id != ilbl[0, 0] and k_id != ilbl[0, W - 1] and sz < 1800:
                m[ilbl == k_id] = True
    return m


def split_coronal_arms_and_torso(mask):
    """Splits a coronal (front f=144 or rear f=73) full-res mask into:
      (torso_head_mask, left_screen_arm_mask, right_screen_arm_mask, cL_curve, cR_curve)
    across the raised-arm rows (from fingertips down to shoulder junction r ~ 405)."""
    H, W = mask.shape
    c_mid = 423.0
    cL = np.zeros(H, dtype=np.float32)
    cR = np.full(H, float(W - 1), dtype=np.float32)

    # Below r=415 there are no separate arm spans; above r=215 there is ONLY left arm & right arm (no head!)
    r_head_top = 215
    for r in range(0, r_head_top):
        cL[r] = c_mid - 2.0
        cR[r] = c_mid + 2.0

    last_L, last_R = c_mid - 35.0, c_mid + 35.0
    r_join = 400
    for r in range(r_head_top, 425):
        cs = np.nonzero(mask[r])[0]
        if not len(cs):
            cL[r], cR[r] = last_L, last_R
            continue
        splits = np.where(np.diff(cs) > 2)[0]
        spans = []
        s0 = int(cs[0])
        for sp in splits:
            spans.append((s0, int(cs[sp])))
            s0 = int(cs[sp + 1])
        spans.append((s0, int(cs[-1])))
        if len(spans) >= 3:
            # Left screen arm, center head/hair, right screen arm!
            mid_sp = min(spans, key=lambda ab: abs(0.5 * (ab[0] + ab[1]) - c_mid))
            left_sps = [ab for ab in spans if ab[1] < mid_sp[0]]
            right_sps = [ab for ab in spans if ab[0] > mid_sp[1]]
            if left_sps and right_sps:
                last_L = 0.5 * (left_sps[-1][1] + mid_sp[0])
                last_R = 0.5 * (mid_sp[1] + right_sps[0][0])
                cL[r], cR[r] = last_L, last_R
                r_join = r
                continue
        # Once arms merge into shoulders (around r=390..420), flare crease smoothly outward into armpits
        t = min(1.0, max(0.0, (r - r_join) / 28.0))
        cL[r] = last_L * (1.0 - t) + 0.0 * t
        cR[r] = last_R * (1.0 - t) + float(W - 1) * t

    cols = np.arange(W)[None, :]
    arm_scr_L = mask & (np.arange(H)[:, None] < r_join + 16) & (cols < np.floor(cL[:, None]))
    arm_scr_R = mask & (np.arange(H)[:, None] < r_join + 16) & (cols > np.ceil(cR[:, None]))
    torso_head = mask & np.logical_not(arm_scr_L | arm_scr_R)
    return torso_head, arm_scr_L, arm_scr_R, cL, cR


def dilate_rgb_from_mask(rgb, valid_mask):
    _, (iy, ix) = ndimage.distance_transform_edt(np.logical_not(valid_mask), return_indices=True)
    return rgb[iy, ix].astype(np.float32)


def bilinear_sample(img_f32, fu, fv):
    H, W = img_f32.shape[:2]
    fu_c = np.clip(fu, 0.0, W - 1.001)
    fv_c = np.clip(fv, 0.0, H - 1.001)
    x0 = np.floor(fu_c).astype(np.int32)
    y0 = np.floor(fv_c).astype(np.int32)
    x1 = np.minimum(x0 + 1, W - 1)
    y1 = np.minimum(y0 + 1, H - 1)
    wx = (fu_c - x0)[:, None]
    wy = (fv_c - y0)[:, None]
    return (
        img_f32[y0, x0] * (1.0 - wx) * (1.0 - wy)
        + img_f32[y0, x1] * wx * (1.0 - wy)
        + img_f32[y1, x0] * (1.0 - wx) * wy
        + img_f32[y1, x1] * wx * wy
    )


def run_blender_remesh_and_uv(verts, faces, work_dir):
    in_npz = os.path.join(work_dir, "hull_in.npz")
    out_npz = os.path.join(work_dir, "mesh_out.npz")
    np.savez(in_npz, verts=verts.astype(np.float32), faces=faces.astype(np.int32))

    bl_script = os.path.join(work_dir, "bl_job.py")
    with open(bl_script, "w", encoding="utf-8") as f:
        f.write(f"""import math, bpy, numpy as np
d = np.load({in_npz!r})
verts, faces = d["verts"], d["faces"]

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("hull")
me.vertices.add(len(verts))
me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(faces) * 3)
me.loops.foreach_set("vertex_index", faces.ravel())
me.polygons.add(len(faces))
me.polygons.foreach_set("loop_start", np.arange(len(faces), dtype=np.int32) * 3)
me.polygons.foreach_set("loop_total", np.full(len(faces), 3, dtype=np.int32))
me.update(calc_edges=True)

obj = bpy.data.objects.new("pinklady", me)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

rm = obj.modifiers.new("rm", "REMESH")
rm.mode = "VOXEL"
rm.voxel_size = 1.25
bpy.ops.object.modifier_apply(modifier="rm")

sm = obj.modifiers.new("sm", "SMOOTH")
sm.factor = 0.48
sm.iterations = 6
bpy.ops.object.modifier_apply(modifier="sm")

dm = obj.modifiers.new("dec", "DECIMATE")
dm.ratio = min(1.0, {TRI_BUDGET} / max(1, len(obj.data.polygons) * 2.0))
bpy.ops.object.modifier_apply(modifier="dec")

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.008)
bpy.ops.object.mode_set(mode="OBJECT")

lme = obj.data
lme.calc_loop_triangles()
uvl = lme.uv_layers.active
nv = len(lme.vertices)
vp = np.zeros(nv * 3, dtype=np.float32)
vn = np.zeros(nv * 3, dtype=np.float32)
lme.vertices.foreach_get("co", vp)
lme.vertices.foreach_get("normal", vn)
vp = vp.reshape(nv, 3)
vn = vn.reshape(nv, 3)

sm_pick = obj.modifiers.new("pick", "SMOOTH")
sm_pick.factor = 1.0
sm_pick.iterations = 30
dg = bpy.context.evaluated_depsgraph_get()
sme = obj.evaluated_get(dg).to_mesh()
vn_smooth = np.zeros(nv * 3, dtype=np.float32)
sme.vertices.foreach_get("normal", vn_smooth)
vn_smooth = vn_smooth.reshape(nv, 3)
obj.evaluated_get(dg).to_mesh_clear()
obj.modifiers.remove(sm_pick)

tv = np.array([lt.vertices[:] for lt in lme.loop_triangles], dtype=np.int32)
tuv = np.array([[uvl.data[li].uv[:] for li in lt.loops] for lt in lme.loop_triangles], dtype=np.float32)

np.savez({out_npz!r}, vp=vp, vn=vn, vn_smooth=vn_smooth, tv=tv, tuv=tuv)
print("BLENDER_OK tris=", len(tv), "verts=", nv)
""")

    res = subprocess.run([BLENDER, "-b", "-P", bl_script], capture_output=True, text=True, check=True)
    for line in res.stdout.splitlines():
        if "BLENDER_OK" in line:
            print(" ", line, flush=True)
    with np.load(out_npz) as d:
        return {k: d[k].copy() for k in d.files}


def render_verification_sheet(verts_q, norms_q, uvs, tris, tex_u8, out_path):
    H_r, W_r = 380, 280
    angles = [0, 45, 90, 180, 270, 315]
    sheet = np.full((H_r, W_r * len(angles), 3), 28, dtype=np.uint8)
    th, tw = tex_u8.shape[:2]

    vmin, vmax = verts_q.min(axis=0), verts_q.max(axis=0)
    ctr = 0.5 * (vmin + vmax)
    span = max(vmax - vmin)
    sc = (H_r * 0.88) / span

    light_dir = np.array([0.48, -0.32, 0.82], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)

    for idx, deg in enumerate(angles):
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        p = verts_q - ctr
        rx = p[:, 0] * ca - p[:, 1] * sa
        ry = p[:, 0] * sa + p[:, 1] * ca
        rz = p[:, 2]
        nx = norms_q[:, 0] * ca - norms_q[:, 1] * sa
        ny = norms_q[:, 0] * sa + norms_q[:, 1] * ca
        nz = norms_q[:, 2]

        sx = (W_r * 0.5) - ry * sc
        sy = (H_r * 0.5) - rz * sc
        sz = rx

        zb = np.full((H_r, W_r), -1e9, dtype=np.float32)
        cb = np.full((H_r, W_r, 3), 30, dtype=np.uint8)

        for a, b, c in tris:
            x0, x1 = max(0, int(min(sx[a], sx[b], sx[c]))), min(W_r - 1, int(max(sx[a], sx[b], sx[c])) + 1)
            y0, y1 = max(0, int(min(sy[a], sy[b], sy[c]))), min(H_r - 1, int(max(sy[a], sy[b], sy[c])) + 1)
            if x1 < x0 or y1 < y0:
                continue
            den = (sy[b] - sy[c]) * (sx[a] - sx[c]) + (sx[c] - sx[b]) * (sy[a] - sy[c])
            if abs(den) < 1e-5:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((sy[b] - sy[c]) * (gx - sx[c]) + (sx[c] - sx[b]) * (gy - sy[c])) / den
            w1 = ((sy[c] - sy[a]) * (gx - sx[c]) + (sx[a] - sx[c]) * (gy - sy[c])) / den
            w2 = 1.0 - w0 - w1
            ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not ins.any():
                continue
            zz = w0[ins] * sz[a] + w1[ins] * sz[b] + w2[ins] * sz[c]
            yi, xi = gy[ins].astype(np.int32), gx[ins].astype(np.int32)
            vis = zz > zb[yi, xi]
            if not vis.any():
                continue
            yi, xi, zz = yi[vis], xi[vis], zz[vis]
            w0v, w1v, w2v = w0[ins][vis], w1[ins][vis], w2[ins][vis]
            zb[yi, xi] = zz

            uu = np.clip(((w0v * uvs[a, 0] + w1v * uvs[b, 0] + w2v * uvs[c, 0]) * (tw - 1)).astype(np.int32), 0, tw - 1)
            vv = np.clip(((w0v * uvs[a, 1] + w1v * uvs[b, 1] + w2v * uvs[c, 1]) * (th - 1)).astype(np.int32), 0, th - 1)
            nnx = w0v * nx[a] + w1v * nx[b] + w2v * nx[c]
            nny = w0v * ny[a] + w1v * ny[b] + w2v * ny[c]
            nnz = w0v * nz[a] + w1v * nz[b] + w2v * nz[c]
            nl = np.maximum(np.sqrt(nnx * nnx + nny * nny + nnz * nnz), 1e-6)
            lit = 0.44 + 0.62 * np.clip((nnx * light_dir[0] + nny * light_dir[1] + nnz * light_dir[2]) / nl, 0.0, 1.0)
            col = np.clip(tex_u8[vv, uu].astype(np.float32) * lit[:, None], 0, 255).astype(np.uint8)
            cb[yi, xi] = col

        sheet[:, idx * W_r:(idx + 1) * W_r] = cb
    Image.fromarray(sheet, "RGB").save(out_path, "PNG")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS, exist_ok=True)

    print(f"Loading Pink Lady turntable video: {VIDEO} ...", flush=True)
    cap = cv2.VideoCapture(VIDEO)
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()

    H, W = frames[0].shape[:2]
    h2, w2 = H // F_DOWN, W // F_DOWN

    masks = [None] * len(frames)
    for i in range(4, len(frames)):
        masks[i] = segment_pinklady_mask(frames[i])

    torso_144_full, armR_144_full, armL_144_full, cL_144_full, cR_144_full = split_coronal_arms_and_torso(masks[144])
    torso_73_full, armL_73_full, armR_73_full, cL_73_full, cR_73_full = split_coronal_arms_and_torso(masks[73])

    base_fids = set(np.round(np.linspace(6, 144, 46)).astype(int).tolist())
    base_fids.update([24, 36, 45, 58, 73, 88, 101, 118, 132, 144])
    carve_fids = sorted(base_fids)
    idx_of_fid = {fi: k for k, fi in enumerate(carve_fids)}

    small_masks = {}
    for fi in carve_fids:
        m = masks[fi][:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.40
        small_masks[fi] = m

    ang = np.array([math.radians(frame_angle_deg(fi)) for fi in carve_fids], dtype=np.float64)

    k144 = idx_of_fid[144]
    k73 = idx_of_fid[73]
    rr144, cc144 = np.nonzero(small_masks[144])
    cx0_init = 0.5 * (cc144.min() + cc144.max())
    cz0_init = 0.5 * (rr144.min() + rr144.max())
    cx = np.full(len(carve_fids), cx0_init, dtype=np.float64)
    cz = np.full(len(carve_fids), cz0_init, dtype=np.float64)

    R_XY = 148
    Z_TOP = 232
    Z_BOT = 232
    X = np.arange(-R_XY, R_XY + 1, dtype=np.float32)
    Y = np.arange(-R_XY, R_XY + 1, dtype=np.float32)
    Zr = np.arange(-Z_TOP, Z_BOT + 1, dtype=np.float32)
    XX, YY = np.meshgrid(X, Y, indexing="ij")

    Xc, Yc, Zrc = X[::2], Y[::2], Zr[::2]
    XXc, YYc = np.meshgrid(Xc, Yc, indexing="ij")

    def carve_grid(Xv, Yv, Zrv, XXv, YYv, cx_v, cz_v, keep_ratio=0.90, dilate_px=1):
        cnt = np.zeros((len(Xv), len(Yv), len(Zrv)), dtype=np.uint8)
        zero_row = np.zeros((1, len(Zrv)), dtype=np.uint8)
        for k, fi in enumerate(carve_fids):
            a = SIGN * ang[k]
            ca, sa = math.cos(a), math.sin(a)
            U = np.rint(cx_v[k] + XXv * ca - YYv * sa).astype(np.int32)
            V = np.rint(cz_v[k] + Zrv).astype(np.int32)
            okU = (U >= 0) & (U < w2)
            okV = (V >= 0) & (V < h2)
            m = small_masks[fi]
            if dilate_px > 0:
                m = ndimage.binary_dilation(m, iterations=dilate_px)
            m_sub = np.ascontiguousarray(m[np.clip(V, 0, h2 - 1), :].T, dtype=np.uint8)
            m_sub[:, ~okV] = 0
            lut = np.vstack([m_sub, zero_row])
            cnt += lut[np.where(okU, U, w2)]
        return cnt >= int(round(keep_ratio * len(carve_fids)))

    def project_coarse(occ_c, k, cx_v, cz_v):
        a = SIGN * ang[k]
        xi, yi, zi = np.nonzero(occ_c)
        U = np.rint(cx_v[k] + Xc[xi] * math.cos(a) - Yc[yi] * math.sin(a)).astype(np.int32)
        V = np.rint(cz_v[k] + Zrc[zi]).astype(np.int32)
        ok = (U >= 0) & (U < w2) & (V >= 0) & (V < h2)
        img = np.zeros((h2, w2), dtype=bool)
        img[V[ok], U[ok]] = True
        return ndimage.binary_closing(img, structure=np.ones((3, 3), bool))

    print(f"Aligning {len(carve_fids)} turntable views ...", flush=True)
    occ_align = carve_grid(Xc, Yc, Zrc, XXc, YYc, cx, cz, keep_ratio=0.86, dilate_px=2)
    for it in range(4):
        moved = 0
        new_dx = np.zeros(len(carve_fids), dtype=np.float64)
        new_dz = np.zeros(len(carve_fids), dtype=np.float64)
        for k, fi in enumerate(carve_fids):
            pj = project_coarse(occ_align, k, cx, cz).astype(np.float32)
            m = small_masks[fi].astype(np.float32)
            m_pad = np.pad(m, ((6, 6), (9, 9)), mode="constant")
            inter = cv2.matchTemplate(m_pad, pj, cv2.TM_CCORR)
            uni = np.maximum(m.sum() + pj.sum() - inter, 1.0)
            iou = inter / uni
            iz_best, ix_best = np.unravel_index(int(np.argmax(iou)), iou.shape)
            bd_x, bd_z = int(ix_best) - 9, int(iz_best) - 6
            new_dx[k] = bd_x
            new_dz[k] = bd_z
            moved += abs(bd_x) + abs(bd_z)
        cx += new_dx - new_dx[k144]
        cz += new_dz - new_dz[k144]
        occ_align = carve_grid(Xc, Yc, Zrc, XXc, YYc, cx, cz, keep_ratio=0.90, dilate_px=1)
        print(f"  align pass {it + 1}: shift={moved}", flush=True)

    # 1. Central Torso + Twin Spheres + Head + Hair (strictly inside torso_head coronal masks!)
    print("Sculpting 3D Torso/Spheres/Head + Full-Length Raised V-Arms + Tie-Ribbons ...", flush=True)
    occ_torso = carve_grid(X, Y, Zr, XX, YY, cx, cz, keep_ratio=0.90, dilate_px=1)

    torso_144_hr = torso_144_full[:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.40
    torso_73_hr = torso_73_full[:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.40

    U_0 = np.clip(np.rint(cx[k144] + X).astype(np.int32), 0, w2 - 1)
    V_0 = np.clip(np.rint(cz[k144] + Zr).astype(np.int32), 0, h2 - 1)
    cor_t0 = ndimage.binary_dilation(torso_144_hr, iterations=1)[V_0, :][:, U_0].T

    U_180 = np.clip(np.rint(cx[k73] - X).astype(np.int32), 0, w2 - 1)
    V_180 = np.clip(np.rint(cz[k73] + Zr).astype(np.int32), 0, h2 - 1)
    cor_t180 = ndimage.binary_dilation(torso_73_hr, iterations=2)[V_180, :][:, U_180].T

    occ_torso &= cor_t0[:, None, :] & cor_t180[:, None, :]

    # Sculpt twin-sphere cleavage valley (-Y) and rear inter-pod crease (+Y)
    for iz, zv in enumerate(Zr):
        v_hr = cz[k144] + zv
        if 225.0 <= v_hr <= 372.0:
            sl = occ_torso[:, :, iz]
            if not sl.any():
                continue
            t_pod = (v_hr - 225.0) / (372.0 - 225.0)
            bell = math.sin(math.pi * min(1.0, max(0.0, t_pod)))
            ys_f = np.nonzero(sl.any(axis=0))[0]
            if len(ys_f) < 4:
                continue
            y_front = float(Y[ys_f[0]])
            y_back = float(Y[ys_f[-1]])
            cleft_depth = 23.0 * (bell ** 0.85) * (1.0 - 0.35 * max(0.0, (t_pod - 0.72) / 0.28))
            cleft_hw = 16.5 * (0.45 + 0.55 * bell)
            y_cut_front = y_front + cleft_depth * np.exp(-((X / cleft_hw) ** 2))
            keep_mask = np.logical_not(YY < y_cut_front[:, None])

            if v_hr > 325.0:
                b_bell = math.sin(math.pi * min(1.0, (v_hr - 325.0) / 50.0))
                y_cut_back = y_back - 8.5 * b_bell * np.exp(-((X / 15.0) ** 2))
                keep_mask &= np.logical_not(YY > y_cut_back[:, None])

            occ_torso[:, :, iz] = sl & keep_mask
        elif v_hr > 372.0:
            # Below the pods (v_hr > 372), keep ONLY the thin front dangling tie-ribbons (near front knot Y ~ -52..-34)
            sl = occ_torso[:, :, iz]
            if sl.any():
                occ_torso[:, :, iz] = sl & (YY >= -64.0) & (YY <= -28.0)

    # 2. Full-Length Raised V-Arms & Hands sculpted from exact f=144 arm silhouettes (fingertip-to-shoulder!)
    # Find shoulder Y-center in occ_torso around v_hr = 195..215 so arms weld seamlessly into the shoulders!
    iz_sh = int(np.argmin(np.abs((cz[k144] + Zr) - 205.0)))
    ys_sh = np.nonzero(occ_torso[:, :, iz_sh].any(axis=0))[0]
    y_shoulder = float(np.median(Y[ys_sh])) if len(ys_sh) else 20.0

    arms_144_full = armL_144_full | armR_144_full
    # Dilate by 1 full-res px so finger gaps merge cleanly at remesh scale while preserving full hand height!
    arms_144_hr = ndimage.binary_closing(arms_144_full, structure=np.ones((3, 3), bool))[
        :h2 * F_DOWN, :w2 * F_DOWN
    ].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.35
    # Extend shoulder root 8 half-res rows downward into torso so union is 100% manifold
    arms_ext_hr = ndimage.binary_dilation(arms_144_hr, structure=np.ones((9, 5), bool)) & small_masks[144]
    dt_arm = cv2.distanceTransform(arms_ext_hr.astype(np.uint8), cv2.DIST_L2, 5)

    arm_xz = arms_ext_hr[V_0, :][:, U_0].T
    dt_arm_xz = dt_arm[V_0, :][:, U_0].T
    v_hr_row = cz[k144] + Zr  # shape (len(Zr),)

    # Arm centerline Y_arm tilts slightly forward from shoulder (y_shoulder) toward raised hands (y_shoulder - 5)
    t_up = np.clip((205.0 - v_hr_row) / 195.0, 0.0, 1.0)
    Y_arm_mid = y_shoulder - 5.0 * t_up
    # Cylindrical cross-section: thickness scales with distance transform dt_arm_xz (thinner flat palms above v_hr < 55)
    hand_flat = np.where(v_hr_row < 52.0, 0.52, 0.92)[None, :]
    half_T_arm = np.clip(dt_arm_xz * hand_flat, 0.0, 11.5)
    occ_arms = (
        arm_xz[:, None, :]
        & (half_T_arm[:, None, :] > 0.6)
        & (np.abs(Y[None, :, None] - Y_arm_mid[None, None, :]) <= half_T_arm[:, None, :])
    )

    # 3. Ensure crisp dangling hot-pink tie ribbons below tie-knot (v_hr in 355..432) from f=144
    rib_144_hr = small_masks[144].copy()
    rib_144_hr[:355, :] = False
    rib_xz = rib_144_hr[V_0, :][:, U_0].T
    dt_rib = cv2.distanceTransform(rib_144_hr.astype(np.uint8), cv2.DIST_L2, 5)[V_0, :][:, U_0].T
    # Locate front tie-knot Y at v_hr ~ 358
    iz_kn = int(np.argmin(np.abs((cz[k144] + Zr) - 358.0)))
    ys_kn = np.nonzero(occ_torso[:, :, iz_kn].any(axis=0))[0]
    y_knot = float(Y[ys_kn[0]] + 7.0) if len(ys_kn) else -46.0
    half_T_rib = np.clip(dt_rib * 0.65, 1.4, 4.2)
    occ_rib = (
        rib_xz[:, None, :]
        & (np.abs(Y[None, :, None] - y_knot) <= half_T_rib[:, None, :])
    )

    occ = occ_torso | occ_arms | occ_rib
    occ = ndimage.binary_closing(occ, iterations=1)
    lbl, n_lbl = ndimage.label(occ)
    if n_lbl > 1:
        sz = ndimage.sum(occ, lbl, range(1, n_lbl + 1))
        occ = lbl == (1 + int(np.argmax(sz)))

    print(f"  Voxels -> torso: {int(occ_torso.sum()):,}, arms: {int(occ_arms.sum()):,}, union: {int(occ.sum()):,}", flush=True)
    field = ndimage.gaussian_filter(occ.astype(np.float32), sigma=0.72)
    verts_mc, faces_mc, _, _ = measure.marching_cubes(field, level=0.5)
    verts_hull = np.stack([
        X[0] + verts_mc[:, 0],
        Y[0] + verts_mc[:, 1],
        -(Zr[0] + verts_mc[:, 2]),
    ], axis=1).astype(np.float32)

    a0, b0, c0 = verts_hull[faces_mc[:, 0]], verts_hull[faces_mc[:, 1]], verts_hull[faces_mc[:, 2]]
    fn0 = np.cross(b0 - a0, c0 - a0)
    cen0 = (a0 + b0 + c0) / 3.0 - verts_hull.mean(axis=0)
    if float(np.sum(fn0 * cen0)) < 0:
        faces_mc = faces_mc[:, [0, 2, 1]]
    print(f"Marching-cubes hull: {len(verts_hull):,} verts, {len(faces_mc):,} tris", flush=True)

    with tempfile.TemporaryDirectory() as work_dir:
        bl = run_blender_remesh_and_uv(verts_hull, faces_mc, work_dir)
        VP = bl["vp"]
        VN = bl["vn"]
        VN_SM = bl["vn_smooth"]
        TV = bl["tv"]
        TUV = bl["tuv"]

    # Rasterize 1024x1024 UV texels
    print(f"Baking region-pure {TEX_SIZE}x{TEX_SIZE} texture ...", flush=True)
    TUV_px = TUV * TEX_SIZE
    PP, NN, PX, PY = [], [], [], []
    for t in range(len(TV)):
        a, b, c = TUV_px[t]
        x0, y0 = max(0, int(math.floor(min(a[0], b[0], c[0]))) - 1), max(0, int(math.floor(min(a[1], b[1], c[1]))) - 1)
        x1, y1 = min(TEX_SIZE, int(math.ceil(max(a[0], b[0], c[0]))) + 1), min(TEX_SIZE, int(math.ceil(max(a[1], b[1], c[1]))) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        v0, v1 = b - a, c - a
        d00 = float(v0[0] * v0[0] + v0[1] * v0[1])
        d01 = float(v0[0] * v1[0] + v0[1] * v1[1])
        d11 = float(v1[0] * v1[0] + v1[1] * v1[1])
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-11:
            continue
        px_, py_ = gx - a[0], gy - a[1]
        d20 = px_ * v0[0] + py_ * v0[1]
        d21 = px_ * v1[0] + py_ * v1[1]
        l1 = (d11 * d20 - d01 * d21) / den
        l2 = (d00 * d21 - d01 * d20) / den
        l0 = 1.0 - l1 - l2
        ins = (l0 >= -0.06) & (l1 >= -0.06) & (l2 >= -0.06)
        if not ins.any():
            continue
        l0c, l1c, l2c = np.clip(l0[ins], 0.0, 1.0), np.clip(l1[ins], 0.0, 1.0), np.clip(l2[ins], 0.0, 1.0)
        lsum = np.maximum(l0c + l1c + l2c, 1e-8)
        l0c, l1c, l2c = l0c / lsum, l1c / lsum, l2c / lsum
        ia, ib, ic = TV[t]
        PP.append(l0c[:, None] * VP[ia] + l1c[:, None] * VP[ib] + l2c[:, None] * VP[ic])
        NN.append(l0c[:, None] * VN_SM[ia] + l1c[:, None] * VN_SM[ib] + l2c[:, None] * VN_SM[ic])
        PX.append(gx[ins].astype(np.int32))
        PY.append(gy[ins].astype(np.int32))

    P = np.concatenate(PP, axis=0)
    N_nrm = np.concatenate(NN, axis=0)
    N_nrm /= np.maximum(np.linalg.norm(N_nrm, axis=1, keepdims=True), 1e-6)
    PX = np.concatenate(PX, axis=0)
    PY = np.concatenate(PY, axis=0)

    # Smooth arm weight arm_t in [0, 1] from coronal arm-crease curves cL_144_full, cR_144_full
    fu_front = (cx[k144] + P[:, 0]) * F_DOWN
    fv_front = (cz[k144] - P[:, 2]) * F_DOWN
    r_idx = np.clip(np.rint(fv_front).astype(np.int32), 0, H - 1)
    lat_arm = np.maximum(fu_front - cR_144_full[r_idx], cL_144_full[r_idx] - fu_front)
    arm_t = np.where(fv_front < 408.0, np.clip((lat_arm + 4.0) / 10.0, 0.0, 1.0), 0.0)

    # A. Bake Raised Arm & Hand Texels cleanly from f=144 (front) & f=73 (back)
    dt_144 = cv2.distanceTransform(masks[144].astype(np.uint8), cv2.DIST_L2, 5)
    img_arm_front = dilate_rgb_from_mask(frames[144], (armL_144_full | armR_144_full) & (dt_144 >= 2.0))
    dt_73 = cv2.distanceTransform(masks[73].astype(np.uint8), cv2.DIST_L2, 5)
    img_arm_back = dilate_rgb_from_mask(frames[73], (armL_73_full | armR_73_full) & (dt_73 >= 2.0))

    fu_back = (cx[k73] - P[:, 0]) * F_DOWN
    fv_back = (cz[k73] - P[:, 2]) * F_DOWN
    rgb_af = bilinear_sample(img_arm_front, fu_front, fv_front)
    rgb_ab = bilinear_sample(img_arm_back, fu_back, fv_back)
    wf_a = np.clip(-N_nrm[:, 1] + 0.45, 0.0, 1.45) ** 2.4 + 1e-4
    wb_a = np.clip(+N_nrm[:, 1] + 0.45, 0.0, 1.45) ** 2.4 + 1e-4
    col_arm = ((rgb_af * wf_a[:, None] + rgb_ab * wb_a[:, None]) / (wf_a + wb_a)[:, None]) / 255.0

    # B. Bake Central Torso / Twin Spheres / Face / Blonde Hair (excluding arm occlusion on oblique views!)
    tri_pts = VP[TV]
    surf_cloud = np.vstack([
        VP,
        tri_pts.mean(axis=1),
        0.5 * (tri_pts[:, 0] + tri_pts[:, 1]),
        0.5 * (tri_pts[:, 1] + tri_pts[:, 2]),
        0.5 * (tri_pts[:, 2] + tri_pts[:, 0]),
    ])
    occ_arms_pure = occ_arms & np.logical_not(occ_torso)
    axi, ayi, azi = np.nonzero(occ_arms_pure[::2, ::2, ::2])
    arm_cloud = np.stack([X[0] + axi * 2.0, Y[0] + ayi * 2.0, -(Zr[0] + azi * 2.0)], axis=1).astype(np.float32)

    bake_fids = [144, 24, 36, 45, 58, 73, 88, 101, 118, 132]
    acc_col = np.zeros((len(P), 3), dtype=np.float64)
    wsum_col = np.zeros(len(P), dtype=np.float64)

    for fi in bake_fids:
        k = idx_of_fid[fi]
        a = SIGN * ang[k]
        ca, sa = math.cos(a), math.sin(a)

        Us = np.rint(cx[k] + surf_cloud[:, 0] * ca - surf_cloud[:, 1] * sa).astype(np.int32)
        Vs = np.rint(cz[k] - surf_cloud[:, 2]).astype(np.int32)
        Ds = surf_cloud[:, 0] * sa + surf_cloud[:, 1] * ca
        ok_s = (Us >= 0) & (Us < w2) & (Vs >= 0) & (Vs < h2)
        zb = np.full((h2, w2), 1e9, dtype=np.float32)
        np.minimum.at(zb, (Vs[ok_s], Us[ok_s]), Ds[ok_s])
        zb_closed = ndimage.minimum_filter(zb, size=3)

        Ua = np.rint(cx[k] + arm_cloud[:, 0] * ca - arm_cloud[:, 1] * sa).astype(np.int32)
        Va = np.rint(cz[k] - arm_cloud[:, 2]).astype(np.int32)
        Da = arm_cloud[:, 0] * sa + arm_cloud[:, 1] * ca
        ok_a = (Ua >= 0) & (Ua < w2) & (Va >= 0) & (Va < h2)
        zb_arm = np.full((h2, w2), 1e9, dtype=np.float32)
        np.minimum.at(zb_arm, (Va[ok_a], Ua[ok_a]), Da[ok_a])
        zb_arm_dil = ndimage.minimum_filter(zb_arm, size=7)

        dt_m = cv2.distanceTransform(masks[fi].astype(np.uint8), cv2.DIST_L2, 5)
        if fi == 144:
            valid_fg = torso_144_full & (dt_m >= 2.0)
        elif fi == 73:
            valid_fg = torso_73_full & (dt_m >= 2.0)
        else:
            arm_front_hr = zb_arm_dil < (zb_closed + 6.0)
            arm_front_full = cv2.resize(arm_front_hr.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
            valid_fg = masks[fi] & (dt_m >= 2.5) & np.logical_not(arm_front_full)

        img_clean = dilate_rgb_from_mask(frames[fi], valid_fg)

        u_hr = cx[k] + P[:, 0] * ca - P[:, 1] * sa
        v_hr = cz[k] - P[:, 2]
        depth = P[:, 0] * sa + P[:, 1] * ca
        cos_inc = np.clip(-(N_nrm[:, 0] * sa + N_nrm[:, 1] * ca), 0.0, 1.0)

        ui = np.clip(np.rint(u_hr).astype(np.int32), 0, w2 - 1)
        vi = np.clip(np.rint(v_hr).astype(np.int32), 0, h2 - 1)
        vis = (depth <= (zb_closed[vi, ui] + 4.5)) & (depth <= (zb_arm_dil[vi, ui] - 1.5))

        fu = u_hr * F_DOWN
        fv = v_hr * F_DOWN
        fui = np.clip(np.rint(fu).astype(np.int32), 0, W - 1)
        fvi = np.clip(np.rint(fv).astype(np.int32), 0, H - 1)
        edge_w = np.clip((dt_m[fvi, fui] - 1.5) / 5.5, 0.0, 1.0)

        rgb_s = bilinear_sample(img_clean, fu, fv)
        if fi == 144:
            w = (cos_inc ** 2.6) * 12.0 * vis * np.clip(edge_w + 0.25, 0.0, 1.0)
        elif fi == 73:
            w = (cos_inc ** 3.6) * 7.5 * vis * np.clip(edge_w + 0.20, 0.0, 1.0)
        else:
            w = (cos_inc ** 6.5) * vis * edge_w

        acc_col += rgb_s * w[:, None]
        wsum_col += w

    col_torso = np.zeros((len(P), 3), dtype=np.float32)
    seen = wsum_col > 1e-6
    col_torso[seen] = (acc_col[seen] / wsum_col[seen][:, None]) / 255.0

    need = np.logical_not(seen) & (arm_t < 0.999)
    if need.any() and seen.any():
        src = seen & (arm_t < 0.35)
        if not src.any():
            src = seen
        tree = cKDTree(P[src])
        dists, idxs = tree.query(P[need], k=min(6, int(src.sum())))
        if idxs.ndim == 1:
            idxs = idxs[:, None]
            dists = dists[:, None]
        w_knn = 1.0 / np.maximum(dists, 0.25)
        w_knn /= w_knn.sum(axis=1, keepdims=True)
        src_cols = col_torso[src]
        col_torso[need] = (src_cols[idxs] * w_knn[:, :, None]).sum(axis=1)

    col = (1.0 - arm_t[:, None]) * col_torso + arm_t[:, None] * col_arm

    tex = np.zeros((TEX_SIZE, TEX_SIZE, 3), dtype=np.float32)
    cov = np.zeros((TEX_SIZE, TEX_SIZE), dtype=bool)
    tex[PY, PX] = col
    cov[PY, PX] = True

    for _ in range(12):
        acc2 = np.zeros_like(tex)
        n2 = np.zeros((TEX_SIZE, TEX_SIZE), dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            acc2 += np.roll(np.roll(tex * cov[..., None], dy, axis=0), dx, axis=1)
            n2 += np.roll(np.roll(cov.astype(np.float32), dy, axis=0), dx, axis=1)
        grow = np.logical_not(cov) & (n2 > 0)
        if not grow.any():
            break
        tex[grow] = acc2[grow] / n2[grow][:, None]
        cov |= grow

    tex_u8 = np.clip(np.rint(tex * 255.0), 0, 255).astype(np.uint8)
    srgb_png = os.path.join(OUT_DIR, "pinklady3d_srgb.png")
    im_srgb = Image.fromarray(tex_u8, "RGB")
    im_srgb.save(srgb_png, "PNG", optimize=True)

    dp_im = ImageEnhance.Contrast(im_srgb).enhance(1.12)
    dp_im = ImageEnhance.Brightness(dp_im).enhance(0.58)
    dp_png = os.path.join(PROGS, "skyveh_pinklady.png")
    dp_im.save(dp_png, "PNG", optimize=True)

    ctr = 0.5 * (VP.min(axis=0) + VP.max(axis=0))
    span_h = float(VP[:, 2].max() - VP[:, 2].min())
    scale = HEIGHT_UNITS / span_h

    mv, mst, mn, mt, mp = [], [], [], [], {}
    for ti in range(len(TV)):
        tri = []
        for c_i in range(3):
            vi = int(TV[ti, c_i])
            u_c, v_c = float(TUV[ti, c_i, 0]), float(TUV[ti, c_i, 1])
            key = (vi, round(u_c, 5), round(v_c, 5))
            if key not in mp:
                mp[key] = len(mv)
                x, y, z = (VP[vi] - ctr) * scale
                mv.append((float(-y), float(x), float(z)))
                nx, ny, nz = VN[vi]
                mn.append((float(-ny), float(nx), float(nz)))
                mst.append((u_c, v_c))
            tri.append(mp[key])
        mt.append((tri[0], tri[1], tri[2]))

    verts_q = np.array(mv, dtype=np.float32)
    norms_q = np.array(mn, dtype=np.float32)
    uvs_q = np.array(mst, dtype=np.float32)
    tris_q = np.array(mt, dtype=np.int32)

    out_npz = os.path.join(OUT_DIR, "pinklady3d.npz")
    np.savez_compressed(out_npz, verts=verts_q, norms=norms_q, uvs=uvs_q, tris=tris_q)

    check_png = os.path.join(OUT_DIR, "pinklady3d_check.png")
    render_verification_sheet(verts_q, norms_q, uvs_q, tris_q, tex_u8, check_png)
    print(f"Wrote {out_npz}: {len(verts_q)} UV-verts, {len(tris_q)} tris, bbox={verts_q.min(0).round(1)}..{verts_q.max(0).round(1)}", flush=True)


if __name__ == "__main__":
    main()
