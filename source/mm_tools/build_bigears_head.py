"""Reconstructs the Giant-Eared 3D Floating Head (progs/bigears.md3 + progs/bigears.png)
from the 145-frame 360-degree turntable clip (source/mm_tools/ref/bigears_turntable.mp4).

Pipeline:
  1. Per-frame Lab chroma + luma studio background segmentation across frames 4..144 (excludes pedestal & contact shadow).
  2. Multi-pass matchTemplate silhouette-to-hull alignment of 48 turntable views (~7.5 deg apart).
  3. Anatomical 2-part 3D reconstruction (prevents horizontal visual-hull cheek-to-ear webbing):
     - Central Head + Hair + Nose + Open Mouth + Neck carved from the 48 aligned views + coronal skull masks (f=144, f=82)
       with cranial ovoid rounding behind the ears while keeping nose/brow/lips/chin 100% silhouette-accurate.
     - Giant Left & Right 3D Curved Ears sculpted to the exact pixel silhouettes of f=144, cupped/flared to match profile
       frames (f=50..64, f=100..112), and embossed with real 3D helix/antihelix/concha cartilage relief.
  4. Seamless union via headless Blender 5.2: Voxel Remesh -> Smooth -> Quadric Decimate (5,600 tris) -> Smart UV Project.
  5. Region-pure 1024x1024 texture bake (separating skull vs giant-ear texels via 3D signed distance + cKDTree 3D surface
     crease inpainting so hair never bleeds onto pink ear backs and oblique views never band across cheeks/ears).
  6. Exports progs/bigears.md3 (face -> +X, ~30 Quake units ear-to-ear) + progs/bigears.png.

Usage:
    python3.13 source/mm_tools/build_bigears_head.py
"""
import math
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
VIDEO = os.path.join(HERE, "ref", "bigears_turntable.mp4")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

sys.path.insert(0, HERE)
import md3lib

# Calibrated turntable landmarks (0-based frame index -> turn angle in degrees)
# At 90 deg (frame 50) the face points to SCREEN LEFT and left ear faces camera -> SIGN = -1
LANDMARKS = [
    (4, 0.0),
    (50, 90.0),
    (83, 180.0),
    (112, 270.0),
    (144, 360.0),
]
SIGN = -1.0
F_DOWN = 2          # 1 voxel = 2 source pixels (584x384 working grid -> ~404-voxel ear-to-ear span)
TRI_BUDGET = 5600
TEX_SIZE = 1024
WIDTH_UNITS = 30.0  # Quake units ear-tip to ear-tip


def frame_angle_deg(f_idx):
    for (f0, a0), (f1, a1) in zip(LANDMARKS, LANDMARKS[1:]):
        if f0 <= f_idx <= f1:
            return a0 + (a1 - a0) * (f_idx - f0) / float(f1 - f0)
    return 360.0 if f_idx > LANDMARKS[-1][0] else 0.0


def segment_head_mask(rgb):
    """Segments head + hair + giant ears cleanly from the neutral studio wall & oval turntable."""
    H, W = rgb.shape[:2]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    bg_row = np.median(np.concatenate([lab[:, :70, :], lab[:, -70:, :]], axis=1), axis=1)
    dl = lab[..., 0] - bg_row[:, None, 0]
    dab = np.hypot(lab[..., 1] - bg_row[:, None, 1], lab[..., 2] - bg_row[:, None, 2])
    rows = np.arange(H)[:, None]

    # Above row 515 (strictly above turntable oval horizon at ~544): keep dark hair & specular highlights.
    # Below row 515: require warm flesh/lip chroma (dab > 7.5) so grey turntable & contact shadow are 0% included.
    fg_raw = (
        (dab > 7.5)
        | ((dab > 6.0) & (rows < 525))
        | ((dl < -21.0) & (rows < 515))
        | ((np.abs(dl) > 34.0) & (rows < 500))
    )
    m = ndimage.binary_opening(fg_raw, structure=np.ones((3, 3), bool))
    m = ndimage.binary_closing(m, structure=np.ones((5, 5), bool))
    lbl, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lbl, range(1, n + 1))
        m = lbl == (1 + int(np.argmax(sizes)))

    # Fill enclosed facial holes (eye sclera, teeth, nostrils) without closing open jaw-to-earlobe notches
    inv = ~m
    ilbl, inum = ndimage.label(inv)
    if inum > 1:
        isizes = ndimage.sum(inv, ilbl, range(1, inum + 1))
        for k_id, sz in enumerate(isizes, start=1):
            if k_id != ilbl[0, 0] and sz < 3500:
                m[ilbl == k_id] = True
    return m


def split_coronal_skull_and_ears(mask):
    """Separates a coronal (front f=144 or back f=82) foreground mask into:
    (skull_mask, left_screen_ear_mask, right_screen_ear_mask, cL_curve, cR_curve).
    Uses exact multi-span gaps above/below the ear root and interpolates a smooth temple-to-jaw curve across the root."""
    H, W = mask.shape
    fg_rows = np.nonzero(mask.any(axis=1))[0]
    r0, r1 = int(fg_rows[0]), int(fg_rows[-1])
    fg_cols = np.nonzero(mask.any(axis=0))[0]
    total_w = float(fg_cols[-1] - fg_cols[0])

    # Crown hair (top 6%..20% of head height) has no ears -> gives exact horizontal head center
    crown_r0 = r0 + int(0.06 * (r1 - r0))
    crown_r1 = r0 + int(0.20 * (r1 - r0))
    mids = []
    for r in range(crown_r0, crown_r1 + 1):
        cs = np.nonzero(mask[r])[0]
        if len(cs):
            mids.append(0.5 * (cs[0] + cs[-1]))
    c_mid = float(np.median(mids))

    cL = np.zeros(H, dtype=np.float32)
    cR = np.full(H, float(W - 1), dtype=np.float32)
    pure_skull_row = np.zeros(H, dtype=bool)

    for r in range(r0, r1 + 1):
        cs = np.nonzero(mask[r])[0]
        if not len(cs):
            continue
        splits = np.where(np.diff(cs) > 1)[0]
        spans = []
        s_start = int(cs[0])
        for sp in splits:
            spans.append((s_start, int(cs[sp])))
            s_start = int(cs[sp + 1])
        spans.append((s_start, int(cs[-1])))

        # Choose span containing c_mid (or closest to c_mid); check BOTH left & right half-widths independently!
        best_sp = min(spans, key=lambda ab: 0.0 if (ab[0] <= c_mid <= ab[1]) else min(abs(c_mid - ab[0]), abs(c_mid - ab[1])))
        hw_L = c_mid - float(best_sp[0])
        hw_R = float(best_sp[1]) - c_mid
        if (0.0 < hw_L < 0.255 * total_w) and (0.0 < hw_R < 0.255 * total_w):
            hw = min(hw_L, hw_R)
            cL[r], cR[r] = c_mid - hw, c_mid + hw
            pure_skull_row[r] = True

    # Find merged ear-attachment band [r_top .. r_bot]
    mid_r = int(round(0.52 * (r0 + r1)))
    top_candidates = [r for r in range(r0 + 5, mid_r) if pure_skull_row[r]]
    bot_candidates = [r for r in range(mid_r, r1 - 3) if pure_skull_row[r]]
    r_top = max(top_candidates)
    r_bot = min(bot_candidates)

    for r in range(r_top, r_bot + 1):
        t = (r - r_top) / max(1.0, float(r_bot - r_top))
        s = t * t * (3.0 - 2.0 * t)
        cheek_bulge = 0.011 * total_w * (math.sin(math.pi * t) ** 1.35)
        cL[r] = (1.0 - s) * cL[r_top] + s * cL[r_bot] - cheek_bulge
        cR[r] = (1.0 - s) * cR[r_top] + s * cR[r_bot] + cheek_bulge

    # Extrapolate cleanly outside [r0..r1]
    cL[:r0], cR[:r0] = cL[r0], cR[r0]
    cL[r1 + 1:], cR[r1 + 1:] = cL[r1], cR[r1]

    cols = np.arange(W)[None, :]
    skull = mask & (cols >= np.floor(cL[:, None])) & (cols <= np.ceil(cR[:, None]))
    ear_screen_left = mask & (cols < np.floor(cL[:, None]))
    ear_screen_right = mask & (cols > np.ceil(cR[:, None]))
    return skull, ear_screen_left, ear_screen_right, cL, cR


def dilate_rgb_from_mask(rgb, valid_mask):
    """Replaces all pixels outside valid_mask with the color of the nearest pixel inside valid_mask."""
    _, (iy, ix) = ndimage.distance_transform_edt(~valid_mask, return_indices=True)
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


def load_video_and_masks():
    print(f"Loading {VIDEO} ...", flush=True)
    cap = cv2.VideoCapture(VIDEO)
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    assert len(frames) >= 145, f"Expected 145 frames, got {len(frames)}"
    masks = [None] * len(frames)
    for i in range(4, len(frames)):
        masks[i] = segment_head_mask(frames[i])
    return frames, masks


def run_blender_remesh_and_uv(verts, faces, work_dir):
    """Runs Blender 5.2 headlessly to Voxel-Remesh, Smooth, Decimate, and Smart-UV-Project the hull."""
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

obj = bpy.data.objects.new("head", me)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

rm = obj.modifiers.new("rm", "REMESH")
rm.mode = "VOXEL"
rm.voxel_size = 1.25
bpy.ops.object.modifier_apply(modifier="rm")

sm = obj.modifiers.new("sm", "SMOOTH")
sm.factor = 0.50
sm.iterations = 7
bpy.ops.object.modifier_apply(modifier="sm")

dm = obj.modifiers.new("dec", "DECIMATE")
dm.ratio = min(1.0, {TRI_BUDGET} / max(1, len(obj.data.polygons) * 2.0))
bpy.ops.object.modifier_apply(modifier="dec")

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(68.0), island_margin=0.008)
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

# Smoothed normals for view-angle weighting so facets never chatter across adjacent keyframes
sm_pick = obj.modifiers.new("pick", "SMOOTH")
sm_pick.factor = 1.0
sm_pick.iterations = 35
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


def main():
    os.makedirs(PROGS, exist_ok=True)
    frames, masks = load_video_and_masks()
    H, W = frames[0].shape[:2]
    h2, w2 = H // F_DOWN, W // F_DOWN

    # Ensure key coronal/profile frames (36, 50, 64, 82, 100, 112, 128, 144) are directly in the 48-view set
    base_fids = set(np.round(np.linspace(6, 144, 46)).astype(int).tolist())
    base_fids.update([36, 50, 64, 82, 100, 112, 128, 144])
    carve_fids = sorted(base_fids)
    idx_of_fid = {fi: k for k, fi in enumerate(carve_fids)}

    small_masks = {}
    for fi in carve_fids:
        m = masks[fi][:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.45
        small_masks[fi] = m

    ang = np.array([math.radians(frame_angle_deg(fi)) for fi in carve_fids], dtype=np.float64)

    cx = np.zeros(len(carve_fids), dtype=np.float64)
    cz = np.zeros(len(carve_fids), dtype=np.float64)
    for k, fi in enumerate(carve_fids):
        rr, cc = np.nonzero(small_masks[fi])
        cx[k] = cc.mean()
        cz[k] = rr.min() + 132.0

    R_XY = 220
    Z_HI = 160
    X = np.arange(-R_XY, R_XY + 1, dtype=np.float32)
    Y = np.arange(-R_XY, R_XY + 1, dtype=np.float32)
    Zr = np.arange(-Z_HI, Z_HI + 1, dtype=np.float32)   # +Zr = screen down
    XX, YY = np.meshgrid(X, Y, indexing="ij")

    def carve(cx_v, cz_v, mask_dict, keep_ratio=0.90, dilate_px=1):
        cnt = np.zeros((len(X), len(Y), len(Zr)), dtype=np.uint8)
        zero_row = np.zeros((1, len(Zr)), dtype=np.uint8)
        for k, fi in enumerate(carve_fids):
            a = SIGN * ang[k]
            ca, sa = math.cos(a), math.sin(a)
            U = np.rint(cx_v[k] + XX * ca - YY * sa).astype(np.int32)
            V = np.rint(cz_v[k] + Zr).astype(np.int32)
            okU = (U >= 0) & (U < w2)
            okV = (V >= 0) & (V < h2)
            m = mask_dict[fi]
            if dilate_px > 0:
                m = ndimage.binary_dilation(m, iterations=dilate_px)
            m_sub = np.ascontiguousarray(m[np.clip(V, 0, h2 - 1), :].T, dtype=np.uint8)
            m_sub[:, ~okV] = 0
            lut = np.vstack([m_sub, zero_row])
            u_idx = np.where(okU, U, w2)
            cnt += lut[u_idx]
        return cnt >= int(round(keep_ratio * len(carve_fids)))

    def project_hull(occ, k, cx_v, cz_v):
        a = SIGN * ang[k]
        xi, yi, zi = np.nonzero(occ)
        U = np.rint(cx_v[k] + X[xi] * math.cos(a) - Y[yi] * math.sin(a)).astype(np.int32)
        V = np.rint(cz_v[k] + Zr[zi]).astype(np.int32)
        ok = (U >= 0) & (U < w2) & (V >= 0) & (V < h2)
        img = np.zeros((h2, w2), dtype=bool)
        img[V[ok], U[ok]] = True
        return img

    print(f"Aligning {len(carve_fids)} turntable views ...", flush=True)
    # Fast coarse 3D hull (step=2 -> 8x fewer voxels) for integer (cx, cz) registration, then full-res carve for final mesh!
    Xc, Yc, Zrc = X[::2], Y[::2], Zr[::2]
    XXc, YYc = np.meshgrid(Xc, Yc, indexing="ij")

    def carve_coarse(cx_v, cz_v, keep_ratio=0.90, dilate_px=1):
        cnt = np.zeros((len(Xc), len(Yc), len(Zrc)), dtype=np.uint8)
        zero_row = np.zeros((1, len(Zrc)), dtype=np.uint8)
        for k, fi in enumerate(carve_fids):
            a = SIGN * ang[k]
            ca, sa = math.cos(a), math.sin(a)
            U = np.rint(cx_v[k] + XXc * ca - YYc * sa).astype(np.int32)
            V = np.rint(cz_v[k] + Zrc).astype(np.int32)
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

    occ_align = carve_coarse(cx, cz, keep_ratio=0.86, dilate_px=2)
    for it in range(4):
        moved = 0
        new_dx = np.zeros(len(carve_fids), dtype=np.float64)
        new_dz = np.zeros(len(carve_fids), dtype=np.float64)
        for k, fi in enumerate(carve_fids):
            pj = project_coarse(occ_align, k, cx, cz).astype(np.float32)
            m = small_masks[fi].astype(np.float32)
            m_pad = np.pad(m, ((5, 5), (9, 9)), mode="constant")
            inter = cv2.matchTemplate(m_pad, pj, cv2.TM_CCORR)
            uni = np.maximum(m.sum() + pj.sum() - inter, 1.0)
            iou = inter / uni
            iz_best, ix_best = np.unravel_index(int(np.argmax(iou)), iou.shape)
            bd_x, bd_z = int(ix_best) - 9, int(iz_best) - 5
            new_dx[k] = bd_x
            new_dz[k] = bd_z
            moved += abs(bd_x) + abs(bd_z)
        cx += new_dx
        cz += new_dz - np.round(np.mean(new_dz))
        occ_align = carve_coarse(cx, cz, keep_ratio=0.90, dilate_px=1)
        print(f"  align pass {it + 1}: shift={moved}", flush=True)

    # Re-center cx[k_144] so X=0 sits strictly on the coronal skull symmetry axis of f=144!
    k144 = idx_of_fid[144]
    k82 = idx_of_fid[82]
    skull_144_full, earR_144_full, earL_144_full, cL_144_full, cR_144_full = split_coronal_skull_and_ears(masks[144])
    skull_82_full, earL_82_full, earR_82_full, cL_82_full, cR_82_full = split_coronal_skull_and_ears(masks[82])

    skull_144_hr = skull_144_full[:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.45
    skull_82_hr = skull_82_full[:h2 * F_DOWN, :w2 * F_DOWN].reshape(h2, F_DOWN, w2, F_DOWN).mean(axis=(1, 3)) > 0.45
    cL_144_hr = 0.5 * cL_144_full[:h2 * F_DOWN:F_DOWN]
    cR_144_hr = 0.5 * cR_144_full[:h2 * F_DOWN:F_DOWN]

    # Part 1: Carve clean, webbing-free 3D central head (skull + face + hair + neck)
    print("Sculpting webbing-free 3D skull + giant curved 3D ears ...", flush=True)
    occ_skull = carve(cx, cz, small_masks, keep_ratio=0.92, dilate_px=1)

    # Intersect strictly with coronal skull-only silhouettes from f=144 (0 deg) and f=82 (180 deg)
    U_0 = np.clip(np.rint(cx[k144] + X).astype(np.int32), 0, w2 - 1)
    V_0 = np.clip(np.rint(cz[k144] + Zr).astype(np.int32), 0, h2 - 1)
    coronal_0 = ndimage.binary_dilation(skull_144_hr, iterations=1)[V_0, :][:, U_0].T   # shape (len(X), len(Zr))

    U_180 = np.clip(np.rint(cx[k82] - X).astype(np.int32), 0, w2 - 1)
    V_180 = np.clip(np.rint(cz[k82] + Zr).astype(np.int32), 0, h2 - 1)
    coronal_180 = ndimage.binary_dilation(skull_82_hr, iterations=4)[V_180, :][:, U_180].T

    occ_skull &= coronal_0[:, None, :] & coronal_180[:, None, :]

    # Round off the 45-deg visual-hull corners behind the giant ears into a natural cranial ovoid per Z slice,
    # while leaving the central nose/brow/lips/chin corridor (|x - x_mid| <= 0.40 * rx) 100% untouched!
    for iz in range(len(Zr)):
        sl = occ_skull[:, :, iz]
        if not sl.any():
            continue
        xs = np.nonzero(sl.any(axis=1))[0]
        x0, x1 = float(X[xs[0]]), float(X[xs[-1]])
        x_mid = 0.5 * (x0 + x1)
        rx = max(6.0, 0.5 * (x1 - x0))
        # Sample front/back skull depth just lateral to nose (0.34..0.44 * rx)
        lat_band = (np.abs(X - x_mid) >= 0.28 * rx) & (np.abs(X - x_mid) <= 0.46 * rx)
        if not sl[lat_band, :].any():
            lat_band = np.abs(X - x_mid) <= 0.46 * rx
        ys = np.nonzero(sl[lat_band, :].any(axis=0))[0]
        if len(ys) < 2:
            continue
        y0, y1 = float(Y[ys[0]]), float(Y[ys[-1]])
        y_mid = 0.5 * (y0 + y1)
        ry = max(6.0, 0.5 * (y1 - y0))
        ovoid = ((np.abs(XX - x_mid) / (rx * 1.03)) ** 2.15 + (np.abs(YY - y_mid) / (ry * 1.03)) ** 2.15) <= 1.0
        keep_nose = np.abs(XX - x_mid) <= (0.40 * rx)
        occ_skull[:, :, iz] &= (ovoid | keep_nose)

    occ_skull = ndimage.binary_opening(occ_skull, structure=np.ones((5, 5, 5), bool))
    occ_skull = ndimage.binary_closing(occ_skull, iterations=1)
    lbl_s, n_s = ndimage.label(occ_skull)
    if n_s > 1:
        sz_s = ndimage.sum(occ_skull, lbl_s, range(1, n_s + 1))
        occ_skull = lbl_s == (1 + int(np.argmax(sz_s)))

    # Part 2: True 3D Sculpted Giant Left & Right Ears matched pixel-for-pixel to f=144 + profile sweep + cartilage relief
    dt_full_hr = cv2.distanceTransform(small_masks[144].astype(np.uint8), cv2.DIST_L2, 5)
    # High-pass luminance relief from f=144 (bright helix/antihelix/tragus ridges vs recessed concha bowl)
    gray_144_hr = cv2.resize(cv2.cvtColor(frames[144], cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0, (w2, h2), interpolation=cv2.INTER_AREA)
    lum_band = ndimage.gaussian_filter(gray_144_hr, sigma=1.6) - ndimage.gaussian_filter(gray_144_hr, sigma=14.0)
    lum_relief_hr = np.clip(lum_band / 0.10, -1.0, 1.0)

    occ_ears = np.zeros_like(occ_skull)
    U0_grid = np.rint(cx[k144] + X).astype(np.int32)
    V0_grid = np.rint(cz[k144] + Zr).astype(np.int32)
    ok_u0 = (U0_grid >= 0) & (U0_grid < w2)
    ok_v0 = (V0_grid >= 0) & (V0_grid < h2)
    u0_c = np.clip(U0_grid, 0, w2 - 1)
    v0_c = np.clip(V0_grid, 0, h2 - 1)

    m144_xz = (small_masks[144][v0_c, :][:, u0_c].T) & ok_u0[:, None] & ok_v0[None, :]
    dt_xz = dt_full_hr[v0_c, :][:, u0_c].T
    rel_xz = lum_relief_hr[v0_c, :][:, u0_c].T

    cL_at_z = cL_144_hr[v0_c]   # shape (len(Zr),)
    cR_at_z = cR_144_hr[v0_c]

    for side in (+1, -1):
        # First find exact vertical span of the protruding outer ear (outside skull wall) so root overlap never climbs into crown hair!
        if side == +1:
            outer_only = m144_xz & (U0_grid[:, None] > (cR_at_z[None, :] + 1.0))
        else:
            outer_only = m144_xz & (U0_grid[:, None] < (cL_at_z[None, :] - 1.0))
        if not outer_only.any():
            continue
        iz_outer = np.nonzero(outer_only.any(axis=0))[0]
        z_top_idx, z_bot_idx = int(iz_outer[0]), int(iz_outer[-1])
        z_in_ear_band = (np.arange(len(Zr)) >= z_top_idx) & (np.arange(len(Zr)) <= z_bot_idx)

        # Embed root 14 half-res voxels deep inside the skull wall ONLY across the ear-root attachment rows!
        if side == +1:
            # Left giant ear (screen right at 0 deg: U > cR)
            ear_2d = m144_xz & (U0_grid[:, None] >= (cR_at_z[None, :] - 14.0)) & z_in_ear_band[None, :]
            lat_dist = U0_grid[:, None].astype(np.float32) - cR_at_z[None, :]
        else:
            # Right giant ear (screen left at 0 deg: U < cL)
            ear_2d = m144_xz & (U0_grid[:, None] <= (cL_at_z[None, :] + 14.0)) & z_in_ear_band[None, :]
            lat_dist = cL_at_z[None, :] - U0_grid[:, None].astype(np.float32)

        max_lat = max(25.0, float(lat_dist[ear_2d].max()))

        u_span = lat_dist / max_lat   # <0 inside skull root, 0 at cheek/temple crease, 1 at outer helix tip
        # v_span: +1 at top of helix, -1 at bottom of earlobe
        v_span = 1.0 - 2.0 * (np.arange(len(Zr), dtype=np.float32)[None, :] - z_top_idx) / max(1.0, float(z_bot_idx - z_top_idx))

        u_pos = np.clip(u_span, 0.0, 1.0)
        # Center surface Y_mid (recall -Y = nose/front, +Y = occiput/back):
        # Root sits right behind cheek/sideburn (Y ~ +5), top tilts gently back (+4.5*v_span), flares +24 voxels backward
        # with concave concha dish (+6.5) and forward-curled outer helix rim (-6.0) matching profile frames f=50..64!
        concha_cup = 6.5 * np.sin(np.pi * np.clip((u_pos - 0.08) / 0.72, 0.0, 1.0)) * np.clip(1.0 - (v_span / 0.78) ** 2, 0.0, 1.0)
        helix_curl = -6.0 * np.exp(-((dt_xz - 5.5) / 7.5) ** 2) * np.clip(u_pos / 0.25, 0.0, 1.0)
        Y_mid = 5.0 + 4.5 * v_span + 23.5 * (u_pos ** 0.88) + concha_cup + helix_curl

        rim_prof = np.clip(dt_xz / 5.5, 0.0, 1.0) ** 0.52
        helix_tube = 2.6 * np.exp(-((dt_xz - 8.0) / 5.5) ** 2)
        lobe_plump = 2.2 * np.clip(-v_span - 0.35, 0.0, 1.0)
        half_T = rim_prof * (6.8 + helix_tube + lobe_plump)

        Y_front = Y_mid - half_T - 2.2 * rel_xz * rim_prof
        Y_back = Y_mid + half_T - 0.5 * rel_xz * rim_prof

        in_shell = (
            ear_2d[:, None, :]
            & (Y[None, :, None] >= Y_front[:, None, :])
            & (Y[None, :, None] <= Y_back[:, None, :])
        )
        occ_ears |= in_shell

    occ = occ_skull | occ_ears
    occ = ndimage.binary_closing(occ, iterations=1)
    lbl3, n3 = ndimage.label(occ)
    if n3 > 1:
        s3 = ndimage.sum(occ, lbl3, range(1, n3 + 1))
        occ = lbl3 == (1 + int(np.argmax(s3)))

    print(f"  skull voxels: {int(occ_skull.sum()):,}, ear voxels: {int(occ_ears.sum()):,}, union: {int(occ.sum()):,}", flush=True)

    field = ndimage.gaussian_filter(occ.astype(np.float32), sigma=0.80)
    verts_mc, faces_mc, _, _ = measure.marching_cubes(field, level=0.5)
    verts_head = np.stack([
        X[0] + verts_mc[:, 0],
        Y[0] + verts_mc[:, 1],
        -(Zr[0] + verts_mc[:, 2]),
    ], axis=1).astype(np.float32)

    a0, b0, c0 = verts_head[faces_mc[:, 0]], verts_head[faces_mc[:, 1]], verts_head[faces_mc[:, 2]]
    fn0 = np.cross(b0 - a0, c0 - a0)
    cen0 = (a0 + b0 + c0) / 3.0 - verts_head.mean(axis=0)
    if float(np.sum(fn0 * cen0)) < 0:
        faces_mc = faces_mc[:, [0, 2, 1]]
    print(f"Marching-cubes hull: {len(verts_head):,} verts, {len(faces_mc):,} tris", flush=True)

    with tempfile.TemporaryDirectory() as work_dir:
        bl = run_blender_remesh_and_uv(verts_head, faces_mc, work_dir)
        VP = bl["vp"]
        VN = bl["vn"]
        VN_SM = bl["vn_smooth"]
        TV = bl["tv"]
        TUV = bl["tuv"]

    # Rasterize UV triangles to 3D surface positions & smoothed normals at TEX_SIZE x TEX_SIZE
    print(f"Rasterizing {TEX_SIZE}x{TEX_SIZE} UV texels ...", flush=True)
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

    # Compute smooth anatomical region weight ear_t in [0, 1] directly from lateral distance outside the coronal skull crease!
    fu_ear_front = (cx[k144] + P[:, 0]) * F_DOWN
    fv_ear_front = (cz[k144] - P[:, 2]) * F_DOWN
    r_idx_p = np.clip(np.rint(fv_ear_front).astype(np.int32), 0, H - 1)
    lat_out_px = np.maximum(fu_ear_front - cR_144_full[r_idx_p], cL_144_full[r_idx_p] - fu_ear_front)
    ear_t = np.clip((lat_out_px + 4.0) / 12.0, 0.0, 1.0)
    occ_ears_pure = occ_ears & (~occ_skull)

    # ------------------------------------------------------------------ A. Bake Giant Ear Texels (col_ear)
    # Front ear RGB: f=144 with central skull, dark stray hair, & exterior replaced by pure warm interior ear skin
    dt_144 = cv2.distanceTransform(masks[144].astype(np.uint8), cv2.DIST_L2, 5)
    luma_144 = frames[144].mean(axis=2)
    ear_valid_144 = (earL_144_full | earR_144_full) & (dt_144 >= 3.0) & (luma_144 > 72.0)
    img_ear_front = dilate_rgb_from_mask(frames[144], ear_valid_144)

    # Back ear RGB: f=82 with dark brown skull hair & exterior replaced by pure pink rear-ear skin!
    dt_82 = cv2.distanceTransform(masks[82].astype(np.uint8), cv2.DIST_L2, 5)
    luma_82 = frames[82].mean(axis=2)
    ear_valid_82 = (earL_82_full | earR_82_full) & (dt_82 >= 3.0) & (luma_82 > 72.0)
    img_ear_back = dilate_rgb_from_mask(frames[82], ear_valid_82)

    # In f=82 (180 deg), left ear (+X, earL_144 on screen right of f=144) is on SCREEN LEFT (earL_82_full)!
    r144_L, c144_L = np.nonzero(earL_144_full)
    r144_R, c144_R = np.nonzero(earR_144_full)
    r82_L, c82_L = np.nonzero(earL_82_full)     # screen-left in f=82 = character's LEFT ear (+X)
    r82_R, c82_R = np.nonzero(earR_82_full)     # screen-right in f=82 = character's RIGHT ear (-X)

    fu_ear_back = np.zeros_like(fu_ear_front)
    fv_ear_back = np.zeros_like(fv_ear_front)
    is_left_side = P[:, 0] >= 0.0

    # Left ear (+X): map mirror-x from [c144_L.min..c144_L.max] -> [c82_L.max..c82_L.min]
    t_uL = (fu_ear_front[is_left_side] - c144_L.min()) / max(1.0, float(c144_L.max() - c144_L.min()))
    t_vL = (fv_ear_front[is_left_side] - r144_L.min()) / max(1.0, float(r144_L.max() - r144_L.min()))
    fu_ear_back[is_left_side] = c82_L.max() - t_uL * float(c82_L.max() - c82_L.min())
    fv_ear_back[is_left_side] = r82_L.min() + t_vL * float(r82_L.max() - r82_L.min())

    # Right ear (-X): map mirror-x from [c144_R.min..c144_R.max] -> [c82_R.max..c82_R.min]
    t_uR = (fu_ear_front[~is_left_side] - c144_R.min()) / max(1.0, float(c144_R.max() - c144_R.min()))
    t_vR = (fv_ear_front[~is_left_side] - r144_R.min()) / max(1.0, float(r144_R.max() - r144_R.min()))
    fu_ear_back[~is_left_side] = c82_R.max() - t_uR * float(c82_R.max() - c82_R.min())
    fv_ear_back[~is_left_side] = r82_R.min() + t_vR * float(r82_R.max() - r82_R.min())

    rgb_ef = bilinear_sample(img_ear_front, fu_ear_front, fv_ear_front)
    rgb_eb = bilinear_sample(img_ear_back, fu_ear_back, fv_ear_back)
    wf_e = np.clip(-N_nrm[:, 1] + 0.45, 0.0, 1.45) ** 2.6 + 1e-4
    wb_e = np.clip(+N_nrm[:, 1] + 0.45, 0.0, 1.45) ** 2.6 + 1e-4
    col_ear = ((rgb_ef * wf_e[:, None] + rgb_eb * wb_e[:, None]) / (wf_e + wb_e)[:, None]) / 255.0

    # ------------------------------------------------------------------ B. Bake Central Skull / Face / Hair Texels (col_skull)
    skull_fids = [144, 36, 50, 64, 82, 100, 112, 128]
    print("Baking skull & giant-ear textures from calibrated keyframes:", skull_fids, flush=True)

    # Surface cloud + separate ear voxel cloud so oblique/profile views never stamp ear skin onto skull hair/cheek!
    tri_pts = VP[TV]
    surf_cloud = np.vstack([
        VP,
        tri_pts.mean(axis=1),
        0.5 * (tri_pts[:, 0] + tri_pts[:, 1]),
        0.5 * (tri_pts[:, 1] + tri_pts[:, 2]),
        0.5 * (tri_pts[:, 2] + tri_pts[:, 0]),
    ])
    exi, eyi, ezi = np.nonzero(occ_ears_pure[::2, ::2, ::2])
    ear_cloud = np.stack([X[0] + exi * 2.0, Y[0] + eyi * 2.0, -(Zr[0] + ezi * 2.0)], axis=1).astype(np.float32)

    # Reference vertical span of f=144 (crown -> chin) to lock jaw opening height on oblique front views (36, 128)
    rr144 = np.nonzero(masks[144].any(axis=1))[0]
    r_top_144, r_bot_144 = float(rr144[0]), float(rr144[-1])

    acc_sk = np.zeros((len(P), 3), dtype=np.float64)
    wsum_sk = np.zeros(len(P), dtype=np.float64)

    for fi in skull_fids:
        k = idx_of_fid[fi]
        a = SIGN * ang[k]
        ca, sa = math.cos(a), math.sin(a)

        # Full-mesh Z-buffer
        Us = np.rint(cx[k] + surf_cloud[:, 0] * ca - surf_cloud[:, 1] * sa).astype(np.int32)
        Vs = np.rint(cz[k] - surf_cloud[:, 2]).astype(np.int32)
        Ds = surf_cloud[:, 0] * sa + surf_cloud[:, 1] * ca
        ok_s = (Us >= 0) & (Us < w2) & (Vs >= 0) & (Vs < h2)
        zb = np.full((h2, w2), 1e9, dtype=np.float32)
        np.minimum.at(zb, (Vs[ok_s], Us[ok_s]), Ds[ok_s])
        zb_closed = ndimage.minimum_filter(zb, size=3)

        # Ear-only Z-buffer (dilated by 3 half-res px) so side/back views never project pink ear onto skull behind ear!
        Ue = np.rint(cx[k] + ear_cloud[:, 0] * ca - ear_cloud[:, 1] * sa).astype(np.int32)
        Ve = np.rint(cz[k] - ear_cloud[:, 2]).astype(np.int32)
        De = ear_cloud[:, 0] * sa + ear_cloud[:, 1] * ca
        ok_e = (Ue >= 0) & (Ue < w2) & (Ve >= 0) & (Ve < h2)
        zb_ear = np.full((h2, w2), 1e9, dtype=np.float32)
        np.minimum.at(zb_ear, (Ve[ok_e], Ue[ok_e]), De[ok_e])
        zb_ear_dil = ndimage.minimum_filter(zb_ear, size=7)

        dt_m = cv2.distanceTransform(masks[fi].astype(np.uint8), cv2.DIST_L2, 5)
        if fi == 144:
            valid_fg = skull_144_full & (dt_m >= 2.0)
        elif fi == 82:
            valid_fg = skull_82_full & (dt_m >= 2.0)
        else:
            # Exclude pixels where the giant ear sits in front of the skull
            ear_in_front_hr = zb_ear_dil < (zb_closed + 6.0)
            ear_in_front_full = cv2.resize(ear_in_front_hr.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
            valid_fg = masks[fi] & (dt_m >= 2.5) & (~ear_in_front_full)

        img_clean = dilate_rgb_from_mask(frames[fi], valid_fg)

        u_hr = cx[k] + P[:, 0] * ca - P[:, 1] * sa
        v_hr = cz[k] - P[:, 2]
        depth = P[:, 0] * sa + P[:, 1] * ca
        cos_inc = np.clip(-(N_nrm[:, 0] * sa + N_nrm[:, 1] * ca), 0.0, 1.0)

        ui = np.clip(np.rint(u_hr).astype(np.int32), 0, w2 - 1)
        vi = np.clip(np.rint(v_hr).astype(np.int32), 0, h2 - 1)
        vis = (depth <= (zb_closed[vi, ui] + 3.5)) & (depth <= (zb_ear_dil[vi, ui] - 1.5))

        fu = u_hr * F_DOWN
        fv = v_hr * F_DOWN
        # Register vertical jaw span on oblique front views (36, 128) to match f=144's open mouth height!
        if fi in (36, 128):
            rr_i = np.nonzero(masks[fi].any(axis=1))[0]
            r_top_i, r_bot_i = float(rr_i[0]), float(rr_i[-1])
            fv = r_top_i + (fv - r_top_144) * ((r_bot_i - r_top_i) / (r_bot_144 - r_top_144))

        fui = np.clip(np.rint(fu).astype(np.int32), 0, W - 1)
        fvi = np.clip(np.rint(fv).astype(np.int32), 0, H - 1)
        edge_w = np.clip((dt_m[fvi, fui] - 1.0) / 5.0, 0.0, 1.0)

        rgb_s = bilinear_sample(img_clean, fu, fv)
        if fi == 144:
            # Smooth front-face hero dominance (no hard step box -> zero vertical cheek seam!)
            w = (cos_inc ** 3.2) * 9.0 * vis * np.clip(edge_w + 0.25, 0.0, 1.0)
        elif fi == 82:
            w = (cos_inc ** 5.0) * 4.0 * vis * np.clip(edge_w + 0.20, 0.0, 1.0)
        else:
            w = (cos_inc ** 7.0) * vis * edge_w

        acc_sk += rgb_s * w[:, None]
        wsum_sk += w

    col_skull = np.zeros((len(P), 3), dtype=np.float32)
    seen_sk = wsum_sk > 1e-6
    col_skull[seen_sk] = (acc_sk[seen_sk] / wsum_sk[seen_sk][:, None]) / 255.0

    # 3D surface k-NN inpainting for any hidden skull pocket directly behind the giant ear root!
    need_sk = (~seen_sk) & (ear_t < 0.999)
    if need_sk.any() and seen_sk.any():
        sk_src = seen_sk & (ear_t < 0.35)
        if not sk_src.any():
            sk_src = seen_sk
        tree = cKDTree(P[sk_src])
        dists, idxs = tree.query(P[need_sk], k=min(6, int(sk_src.sum())))
        if idxs.ndim == 1:
            idxs = idxs[:, None]
            dists = dists[:, None]
        w_knn = 1.0 / np.maximum(dists, 0.25)
        w_knn /= w_knn.sum(axis=1, keepdims=True)
        src_cols = col_skull[sk_src]
        col_skull[need_sk] = (src_cols[idxs] * w_knn[:, :, None]).sum(axis=1)
    print(f"Skull texels inpained via 3D k-NN behind ear roots: {int(need_sk.sum()):,} / {len(P):,}", flush=True)

    # Blend skull & giant-ear textures smoothly across the 4.5-voxel anatomical ear-attachment crease
    col = (1.0 - ear_t[:, None]) * col_skull + ear_t[:, None] * col_ear

    tex = np.zeros((TEX_SIZE, TEX_SIZE, 3), dtype=np.float32)
    cov = np.zeros((TEX_SIZE, TEX_SIZE), dtype=bool)
    tex[PY, PX] = col
    cov[PY, PX] = True

    # Bleed UV island borders outward by 12px so trilinear mipmaps never show dark seams
    for _ in range(12):
        acc2 = np.zeros_like(tex)
        n2 = np.zeros((TEX_SIZE, TEX_SIZE), dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            acc2 += np.roll(np.roll(tex * cov[..., None], dy, axis=0), dx, axis=1)
            n2 += np.roll(np.roll(cov.astype(np.float32), dy, axis=0), dx, axis=1)
        grow = (~cov) & (n2 > 0)
        if not grow.any():
            break
        tex[grow] = acc2[grow] / n2[grow][:, None]
        cov |= grow

    out_png = os.path.join(PROGS, "bigears.png")
    tex_u8 = np.clip(np.rint(tex * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(tex_u8, "RGB").save(out_png, "PNG", optimize=True)
    print(f"Wrote {out_png} ({TEX_SIZE}x{TEX_SIZE})", flush=True)

    # Export Quake MD3: face (-y) -> Quake +X, left ear (+x) -> Quake +Y, crown (+z) -> Quake +Z
    ctr = 0.5 * (VP.min(axis=0) + VP.max(axis=0))
    span_w = float(VP[:, 0].max() - VP[:, 0].min())
    scale = WIDTH_UNITS / span_w

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

    out_md3 = os.path.join(PROGS, "bigears.md3")
    surf = dict(name="head", shader="progs/bigears", tris=mt, st=mst, frames=[(mv, mn)])
    md3lib.write(out_md3, dict(name="bigears", surfaces=[surf], nframes=1))
    print(f"Wrote {out_md3}: {len(mv)} verts, {len(mt)} tris", flush=True)


if __name__ == "__main__":
    main()
