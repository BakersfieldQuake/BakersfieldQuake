"""High-Precision Perspective Z-Buffer Audit Renderer for THE ERIC DEASON CANNON.

Renders the actual compiled `.md3` + PNG textures (`eric_tripod.md3`, `eric_yoke.md3`,
`eric_cannon.md3`) across:
  1. `pass{N}_turntable_8.png` : 8-angle 360-deg side-by-side comparison vs `turntable.mp4`
  2. `pass{N}_closeups.png`    : High-res close-ups of Eric's face, giant ears, buckles & decals
                                 vs `f240`, `f001`, `f087`, and `f137`
  3. `pass{N}_animations.png`  : 16-panel strip of idle radar-ear motion, hilarious Wew-Cannon
                                 bend/bulge/explosion, and sky-glide ear flapping!
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))

for p in (MM_TOOLS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib
import build_eric_cannon as bec

OUT_ROOT = os.path.join(MM_TOOLS, "out", "eric_cannon")
REF_FRAMES = os.path.join(OUT_ROOT, "ref", "video_frames")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
MODEL_DIR = os.path.join(OUT_ROOT, "models")
AUDIT_DIR = os.path.join(OUT_ROOT, "audits")


def _font(sz):
    for nm in ("consolab.ttf", "arialbd.ttf", "segoeui.ttf"):
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def load_tex_rgba(path):
    im = Image.open(path).convert("RGBA")
    return np.asarray(im, dtype=np.float32)


def load_assembled_md3_scene():
    """Reads the actual `.md3` files from `models/` so audits test real exported MD3 geometry & UVs!"""
    tripod = md3lib.read(os.path.join(MODEL_DIR, "eric_tripod.md3"))
    yoke   = md3lib.read(os.path.join(MODEL_DIR, "eric_yoke.md3"))
    cannon = md3lib.read(os.path.join(MODEL_DIR, "eric_cannon.md3"))
    tex_map = {
        "progs/eric_cannon_metal": load_tex_rgba(os.path.join(TEX_DIR, "eric_cannon_metal.png")),
        "progs/eric_cannon_head":  load_tex_rgba(os.path.join(TEX_DIR, "eric_cannon_head.png")),
        "progs/eric_cannon_ears":  load_tex_rgba(os.path.join(TEX_DIR, "eric_cannon_ears.png")),
        "progs/eric_cannon_fx":    load_tex_rgba(os.path.join(TEX_DIR, "eric_cannon_fx.png")),
    }
    return tripod, yoke, cannon, tex_map


def decode_latlng_normals(latlng_arr):
    """Decodes MD3 16-bit spherical normals `(lat, lng)` if needed, or returns float normals directly."""
    arr = np.asarray(latlng_arr, dtype=np.float32)
    return arr


def render_mesh_list(meshes, W, H, cam_pos, look_at, fov_y_deg=34.0, bg_style="studio"):
    """Vectorized scanline / bounding-box perspective Z-buffer renderer with studio 3-point lighting,
    ground turntable disc & soft contact shadow, and additive FX pass."""
    # Studio background + grey turntable pedestal ellipse matching `turntable.mp4`!
    yy_bg = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    if bg_style == "studio":
        bg = np.empty((H, W, 3), dtype=np.float32)
        bg[..., 0] = 204.0 - 8.0 * yy_bg
        bg[..., 1] = 201.0 - 8.0 * yy_bg
        bg[..., 2] = 199.0 - 8.0 * yy_bg
    elif bg_style == "white":
        bg = np.full((H, W, 3), 252.0, dtype=np.float32)
    else:
        bg = np.empty((H, W, 3), dtype=np.float32)
        bg[..., 0] = 24.0 + 18.0 * (1.0 - yy_bg)
        bg[..., 1] = 30.0 + 26.0 * (1.0 - yy_bg)
        bg[..., 2] = 42.0 + 38.0 * (1.0 - yy_bg)

    cam = np.array(cam_pos, dtype=np.float64)
    tgt = np.array(look_at, dtype=np.float64)
    fwd = tgt - cam
    fwd /= np.linalg.norm(fwd)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    right = np.cross(fwd, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    fy = 0.5 * H / math.tan(math.radians(fov_y_deg * 0.5))
    cx_scr, cy_scr = 0.5 * W, 0.5 * H

    # Render studio turntable platter at z = 0 (`R = 112u`) when bg_style == "studio"
    if bg_style == "studio":
        px = (np.arange(W, dtype=np.float32) + 0.5 - cx_scr) / fy
        py = (cy_scr - (np.arange(H, dtype=np.float32) + 0.5)) / fy
        PX, PY = np.meshgrid(px, py)
        # Ray direction in world space: fwd + PX*right + PY*up
        dz = fwd[2] + PX * right[2] + PY * up[2]
        hit = dz < -1e-4
        t_hit = np.where(hit, -cam[2] / np.where(hit, dz, -1.0), -1.0)
        hx = cam[0] + t_hit * (fwd[0] + PX * right[0] + PY * up[0])
        hy = cam[1] + t_hit * (fwd[1] + PX * right[1] + PY * up[1])
        rr = np.hypot(hx, hy)
        on_disc = hit & (t_hit > 0.0) & (rr <= 118.0)
        on_rim = hit & (t_hit > 0.0) & (rr > 118.0) & (rr <= 122.5) & (hy * right[0] - hx * right[1] < 140.0)
        ao = 1.0 - 0.30 * np.exp(-((rr / 34.0) ** 2))
        for c, base_c in enumerate((181.0, 177.0, 173.0)):
            bg[..., c] = np.where(on_disc, base_c * ao, bg[..., c])
            bg[..., c] = np.where(on_rim, base_c * 0.72, bg[..., c])

    zbuf = np.full((H, W), 1e12, dtype=np.float32)
    img = bg.copy()

    # Studio 3-point lighting directions (in camera-relative + world hybrid so turntable stays evenly lit like studio!)
    l_key = fwd * -0.55 + right * -0.32 + up * 0.72
    l_key = (l_key / np.linalg.norm(l_key)).astype(np.float32)
    l_fill = (-fwd * 0.45 + right * 0.65 + up * 0.35)
    l_fill = (l_fill / np.linalg.norm(l_fill)).astype(np.float32)

    opaque_Queue = [m for m in meshes if not m["additive"]]
    add_Queue    = [m for m in meshes if m["additive"]]

    def rasterize(m, is_additive):
        V = m["verts"]       # (nv, 3) float64
        N = m["norms"]       # (nv, 3) float32
        ST = m["st"]         # (nv, 2) float32
        TR = m["tris"]       # (nt, 3) int32 (CCW-outward or double-sided!)
        TEX = m["tex"]       # (th, tw, 4) float32
        th, tw, _ = TEX.shape

        rel = V - cam[None, :]
        zc = (rel @ fwd).astype(np.float32)
        xc = (rel @ right).astype(np.float32)
        yc = (rel @ up).astype(np.float32)

        inv_z = 1.0 / np.maximum(zc, 0.5)
        sx = cx_scr + xc * inv_z * fy
        sy = cy_scr - yc * inv_z * fy

        # Per-vertex shading
        if is_additive:
            shade = np.ones(len(V), dtype=np.float32)
        else:
            # Flip normal toward camera if backfacing (`cull none` shader)
            view_dir = -rel / np.maximum(np.linalg.norm(rel, axis=1, keepdims=True), 1e-6)
            ndv = np.sum(N * view_dir, axis=1)
            N_eff = np.where((ndv < 0.0)[:, None], -N, N)
            dk = np.maximum(0.0, N_eff @ l_key)
            df = np.maximum(0.0, N_eff @ l_fill)
            # Subtle studio rim/specular for metal vs softer skin for head/ears
            if m["is_skin"]:
                shade = 0.58 + 0.42 * dk + 0.14 * df
            else:
                h_vec = l_key - fwd.astype(np.float32)
                h_vec /= np.linalg.norm(h_vec)
                spec = np.maximum(0.0, N_eff @ h_vec) ** 18.0
                shade = 0.48 + 0.50 * dk + 0.18 * df + 0.16 * spec

        for a, b, c in TR:
            za, zb, zc_t = zc[a], zc[b], zc[c]
            if za < 2.0 or zb < 2.0 or zc_t < 2.0:
                continue
            ax, ay = sx[a], sy[a]
            bx, by = sx[b], sy[b]
            cx_t, cy_t = sx[c], sy[c]

            x0 = max(0, int(math.floor(min(ax, bx, cx_t))))
            x1 = min(W - 1, int(math.ceil(max(ax, bx, cx_t))))
            y0 = max(0, int(math.floor(min(ay, by, cy_t))))
            y1 = min(H - 1, int(math.ceil(max(ay, by, cy_t))))
            if x0 > x1 or y0 > y1:
                continue

            denom = (by - cy_t) * (ax - cx_t) + (cx_t - bx) * (ay - cy_t)
            if abs(denom) < 1e-5:
                continue
            inv_d = 1.0 / denom

            xs = np.arange(x0, x1 + 1, dtype=np.float32) + 0.5
            ys = np.arange(y0, y1 + 1, dtype=np.float32) + 0.5
            XX, YY = np.meshgrid(xs, ys)

            w0 = ((by - cy_t) * (XX - cx_t) + (cx_t - bx) * (YY - cy_t)) * inv_d
            w1 = ((cy_t - ay) * (XX - cx_t) + (ax - cx_t) * (YY - cy_t)) * inv_d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not inside.any():
                continue

            # Perspective-correct interpolation
            iz0, iz1, iz2 = inv_z[a], inv_z[b], inv_z[c]
            iz_interp = w0 * iz0 + w1 * iz1 + w2 * iz2
            z_pix = 1.0 / np.maximum(iz_interp, 1e-7)

            z_slice = zbuf[y0:y1 + 1, x0:x1 + 1]
            vis = inside & (z_pix < z_slice)
            if not vis.any():
                continue

            pw0 = (w0[vis] * iz0) * z_pix[vis]
            pw1 = (w1[vis] * iz1) * z_pix[vis]
            pw2 = (w2[vis] * iz2) * z_pix[vis]

            u_p = pw0 * ST[a, 0] + pw1 * ST[b, 0] + pw2 * ST[c, 0]
            v_p = pw0 * ST[a, 1] + pw1 * ST[b, 1] + pw2 * ST[c, 1]
            ui = np.clip((u_p % 1.0) * tw, 0, tw - 1).astype(np.int32)
            vi = np.clip((v_p % 1.0) * th, 0, th - 1).astype(np.int32)
            samp = TEX[vi, ui]  # (npix, 4)

            if is_additive:
                alpha = samp[:, 3:4] / 255.0
                patch = img[y0:y1 + 1, x0:x1 + 1]
                patch[vis] = np.clip(patch[vis] + samp[:, :3] * alpha * 1.15, 0.0, 255.0)
            else:
                z_slice[vis] = z_pix[vis]
                sh_p = (pw0 * shade[a] + pw1 * shade[b] + pw2 * shade[c])[:, None]
                patch = img[y0:y1 + 1, x0:x1 + 1]
                patch[vis] = np.clip(samp[:, :3] * sh_p, 0.0, 255.0)

    for m in opaque_Queue:
        rasterize(m, False)
    for m in add_Queue:
        rasterize(m, True)

    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="RGB")


def assemble_meshes_for_frame(tripod_md3, yoke_md3, cannon_md3, tex_map, frame_idx=0, include_base=True, cannon_pitch=None):
    if cannon_pitch is None:
        cannon_pitch = bec.REST_PITCH_DEG if include_base else 0.0

    meshes = []

    def add_md3(md3_obj, fi, pos_fn, nrm_fn):
        for s in md3_obj["surfaces"]:
            sh = s["shaders"][0] if "shaders" in s and s["shaders"] else s.get("shader", "progs/eric_cannon_metal")
            if isinstance(sh, dict):
                sh = sh.get("name", "progs/eric_cannon_metal")
            is_fx = sh.endswith("_fx")
            if is_fx and fi == 0:
                continue
            vp_raw, vn_raw = s["frames"][fi]
            V = np.array([pos_fn(p) for p in vp_raw], dtype=np.float64)
            N = np.array([nrm_fn(nm) for nm in vn_raw], dtype=np.float32)
            ST = np.array(s["st"], dtype=np.float32)
            TR = np.array(s["tris"], dtype=np.int32)
            meshes.append(dict(
                verts=V, norms=N, st=ST, tris=TR,
                tex=tex_map[sh],
                additive=is_fx,
                is_skin=("_head" in sh or "_ears" in sh),
            ))

    if include_base:
        add_md3(tripod_md3, 0, lambda p: p, lambda nm: nm)
        add_md3(yoke_md3, 0, lambda p: (p[0], p[1], p[2] + bec.YOKE_BASE_Z), lambda nm: nm)

    def xf_p(p):
        pr = bec.rot_y_up_pt(p, cannon_pitch)
        if include_base:
            return (pr[0] + bec.CANNON_REST_X, pr[1], pr[2] + bec.CANNON_REST_Z)
        return pr

    def xf_n(nm):
        return bec.rot_y_up_pt(nm, cannon_pitch)

    add_md3(cannon_md3, frame_idx, xf_p, xf_n)
    return meshes


def run_audit_renders(pass_num=1):
    os.makedirs(AUDIT_DIR, exist_ok=True)
    tripod, yoke, cannon, tex_map = load_assembled_md3_scene()
    fnt = _font(15)
    fnt_big = _font(19)

    # ==========================================================================
    # BOARD 1: 8-ANGLE 360-DEG TURNTABLE COMPARISON (`pass{N}_turntable_8.png`)
    # ==========================================================================
    # Match turntable.mp4 camera:
    #   f240 = 0 deg (+X), f062 = 45 deg, f087 = 90 deg (+Y left side), f112 = 135 deg,
    #   f137 = 180 deg (-X rear), f162 = 225 deg, f185 = 270 deg (-Y right side), f213 = 315 deg
    # Note: let's verify direction of turntable rotation in video!
    #   In f087 (closeup_anatomy_board top-right), Eric faces LEFT (-X_screen)!
    #   If camera is at +Y looking toward (0,0,z) (-Y), then right = (-Y) x (+Z) = -X_world? Wait:
    #     cam = (0, +D, z) -> fwd = (0, -1, 0), world_up = (0, 0, 1) -> right = fwd x up = (-1, 0, 0)!
    #     Then +X_world projects onto -right = LEFT of screen! YES!! Camera at +90 deg (`+Y`) sees Eric facing LEFT (`f087`),
    #     and camera at 270 deg (`-Y`) has `fwd = (0, +1, 0)`, `right = (+1, 0, 0)`, so +X_world projects RIGHT (`f185`)!
    turntable_views = [
        (0.0,   240, "0 deg Front (f240)"),
        (45.0,   62, "45 deg Front-Left (f062)"),
        (90.0,   87, "90 deg Left Profile (f087)"),
        (135.0, 112, "135 deg Rear-Left (f112)"),
        (180.0, 137, "180 deg Rear Bore (f137)"),
        (225.0, 162, "225 deg Rear-Right (f162)"),
        (270.0, 185, "270 deg Right Profile (f185)"),
        (315.0, 213, "315 deg Front-Right (f213)"),
    ]

    meshes_ref = assemble_meshes_for_frame(tripod, yoke, cannon, tex_map, frame_idx=0, include_base=True)
    pw, ph = 468, 308  # Same aspect ratio as 1168x768!
    board1 = Image.new("RGB", (pw * 4, (ph + 28) * 4), (18, 20, 24))
    d1 = ImageDraw.Draw(board1)

    cam_dist = 258.0
    cam_elev_z = 92.0
    look_z = 51.5

    for idx, (ang_deg, ref_f, label) in enumerate(turntable_views):
        row = idx // 2
        col_pair = (idx % 2) * 2
        rad = math.radians(ang_deg)
        look_pt = (0.0, 0.0, look_z)
        cam_p = (look_pt[0] + cam_dist * math.cos(rad), look_pt[1] + cam_dist * math.sin(rad), cam_elev_z)

        rnd = render_mesh_list(meshes_ref, pw, ph, cam_p, look_pt, fov_y_deg=28.5, bg_style="studio")
        ref_im = Image.open(os.path.join(REF_FRAMES, f"frame_{ref_f:03d}.png")).convert("RGB").resize((pw, ph), Image.LANCZOS)

        y_top = row * (ph + 28)
        x_ref = col_pair * pw
        x_rnd = (col_pair + 1) * pw
        board1.paste(ref_im, (x_ref, y_top + 28))
        board1.paste(rnd, (x_rnd, y_top + 28))
        d1.rectangle([x_ref, y_top, x_ref + pw - 1, y_top + 27], fill=(32, 38, 48))
        d1.rectangle([x_rnd, y_top, x_rnd + pw - 1, y_top + 27], fill=(24, 52, 38))
        d1.text((x_ref + 8, y_top + 5), f"REF: {label}", fill=(235, 240, 250), font=fnt)
        d1.text((x_rnd + 8, y_top + 5), f"PASS {pass_num} 3D MD3: {ang_deg:.0f} deg", fill=(165, 255, 195), font=fnt)

    p1_path = os.path.join(AUDIT_DIR, f"pass{pass_num}_turntable_8.png")
    board1.save(p1_path, "PNG")

    # ==========================================================================
    # BOARD 2: FACE, GIANT EARS, BUCKLES & DECALS CLOSEUPS (`pass{N}_closeups.png`)
    # ==========================================================================
    cw, ch = 520, 390
    board2 = Image.new("RGB", (cw * 4, (ch + 32) * 2), (18, 20, 24))
    d2 = ImageDraw.Draw(board2)

    closeups = [
        # (title, ref_frame, crop_box_1168x768, cam_pos, look_at, fov, bg)
        ("Front Face & Giant Ears", 240, (340, 74, 832, 443), (186.0, 0.0, 99.0), (50.0, 0.0, 69.5), 24.5, "studio"),
        ("Hero 3/4 Face, Bell & Decals", 1, (0, 0, 1168, 768), (150.0, -148.0, 82.0), (8.0, 0.0, 60.0), 28.0, "white"),
        ("Profile Nose, Snarl, Buckle & Ear", 87, (38, 52, 558, 442), (48.0, 138.0, 78.0), (48.0, 0.0, 74.5), 25.5, "studio"),
        ("Rear Venturi Bore & Back of Ears", 137, (334, 110, 834, 485), (-195.0, 0.0, 84.0), (-20.0, 0.0, 61.0), 24.5, "studio"),
    ]

    for idx, (title, rf, cbox, cp, lp, fv, bg_s) in enumerate(closeups):
        row = idx // 2
        col_pair = (idx % 2) * 2
        ref_full = Image.open(os.path.join(REF_FRAMES, f"frame_{rf:03d}.png")).convert("RGB")
        ref_crop = ref_full.crop(cbox).resize((cw, ch), Image.LANCZOS)
        rnd_c = render_mesh_list(meshes_ref, cw, ch, cp, lp, fov_y_deg=fv, bg_style=bg_s)

        y_top = row * (ch + 32)
        x_ref = col_pair * cw
        x_rnd = (col_pair + 1) * cw
        board2.paste(ref_crop, (x_ref, y_top + 32))
        board2.paste(rnd_c, (x_rnd, y_top + 32))
        d2.rectangle([x_ref, y_top, x_ref + cw - 1, y_top + 31], fill=(32, 38, 48))
        d2.rectangle([x_rnd, y_top, x_rnd + cw - 1, y_top + 31], fill=(24, 52, 38))
        d2.text((x_ref + 10, y_top + 7), f"REF PHOTO: {title}", fill=(240, 244, 255), font=fnt)
        d2.text((x_rnd + 10, y_top + 7), f"PASS {pass_num} 3D CLOSEUP: {title}", fill=(165, 255, 195), font=fnt)

    p2_path = os.path.join(AUDIT_DIR, f"pass{pass_num}_closeups.png")
    board2.save(p2_path, "PNG")

    # ==========================================================================
    # BOARD 3: ANIMATION STRIP — IDLE EARS, WEW WIND-UP/BLAST & SKY FLIGHT
    # ==========================================================================
    aw, ah = 400, 280
    board3 = Image.new("RGB", (aw * 4, (ah + 28) * 4), (14, 16, 22))
    d3 = ImageDraw.Draw(board3)

    anim_panels = [
        # Row 0: Idle radar-ear twitching (front 3/4 closeup)
        (2,  True,  (165.0, -55.0, 82.0), (62.0, 0.0, 75.0), 29.0, "studio", "Idle f02: Left Ear Radar Perk"),
        (6,  True,  (165.0, -55.0, 82.0), (62.0, 0.0, 75.0), 29.0, "studio", "Idle f06: Asymmetric Ear Flick"),
        (10, True,  (165.0, -55.0, 82.0), (62.0, 0.0, 75.0), 29.0, "studio", "Idle f10: Right Ear Cup Forward"),
        (14, True,  (165.0, -55.0, 82.0), (62.0, 0.0, 75.0), 29.0, "studio", "Idle f14: Double-Listen Twitch"),
        # Row 1: Hilarious Wew-Cannon Wind-Up (side-3/4 view showing skyward bend + belly bulge + pinned ears!)
        (19, True,  (105.0, -215.0, 86.0), (6.0, 0.0, 62.0), 34.0, "dark",   "Windup f19: +23 deg Bend & Belly Swell"),
        (22, True,  (105.0, -215.0, 86.0), (6.0, 0.0, 62.0), 34.0, "dark",   "Windup f22: +38.5 deg Peak Bend & Ears Pinned!"),
        (24, True,  (105.0, -215.0, 86.0), (6.0, 0.0, 62.0), 34.0, "dark",   "Windup f24: +54% Bulge Surging Down Bore!"),
        (25, True,  (105.0, -215.0, 86.0), (6.0, 0.0, 62.0), 34.0, "dark",   "Windup f25: Muzzle Pre-Ignition Swell"),
        # Row 2: Wew-Cannon Explosion & Liftoff (starburst + Mach shockwave rings + snapped ears!)
        (26, True,  (120.0, -235.0, 88.0), (10.0, 0.0, 64.0), 36.0, "dark",  "BLAST f26: Bell Flares +42% & Starburst!"),
        (27, True,  (120.0, -235.0, 88.0), (10.0, 0.0, 64.0), 36.0, "dark",  "BLAST f27: Twin Mach Shockrings & Ear Snap!"),
        (28, False, (105.0, -225.0, 45.0), (0.0, 0.0, 0.0),   36.0, "dark",  "BLAST f28: Tube & Head Blast Off Tripod!"),
        (30, False, (105.0, -225.0, 45.0), (0.0, 0.0, 0.0),   35.0, "dark",  "Liftoff f30: S-Bend Whiplash & Jet Roar"),
        # Row 3: Sky-High Flight Modes (tube + head + giant wing-ears flying free in sky!)
        (36, False, (-165.0, -135.0, 55.0), (0.0, 0.0, 0.0),  33.0, "dark",  "Sky Boost f36: Shock-Diamond Climb"),
        (49, False, (135.0, -145.0, 48.0),  (12.0, 0.0, 0.0), 33.0, "dark",  "Sky Glide f49: Giant Ears Wingbeat UP"),
        (57, False, (135.0, -145.0, 48.0),  (12.0, 0.0, 0.0), 33.0, "dark",  "Sky Glide f57: Giant Ears Wingbeat DOWN"),
        (72, False, (145.0, -125.0, 42.0),  (16.0, 0.0, 0.0), 33.0, "dark",  "Sky Flare f72: Cupped Ear Airbrake!"),
    ]

    for idx, (fi, inc_base, cp, lp, fv, bg_s, title) in enumerate(anim_panels):
        r, c = idx // 4, idx % 4
        ms = assemble_meshes_for_frame(tripod, yoke, cannon, tex_map, frame_idx=fi, include_base=inc_base)
        im_a = render_mesh_list(ms, aw, ah, cp, lp, fov_y_deg=fv, bg_style=bg_s)
        x0, y0 = c * aw, r * (ah + 28)
        board3.paste(im_a, (x0, y0 + 28))
        d3.rectangle([x0, y0, x0 + aw - 1, y0 + 27], fill=(28, 34, 48))
        d3.text((x0 + 8, y0 + 5), title, fill=(255, 226, 145), font=fnt)

    p3_path = os.path.join(AUDIT_DIR, f"pass{pass_num}_animations.png")
    board3.save(p3_path, "PNG")
    print(f"Rendered Audit Pass {pass_num} boards:\n  {p1_path}\n  {p2_path}\n  {p3_path}")
    return p1_path, p2_path, p3_path


if __name__ == "__main__":
    p_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_audit_renders(p_num)
