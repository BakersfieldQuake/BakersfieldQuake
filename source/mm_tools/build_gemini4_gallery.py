r"""Builds G:\Quake\Combat\BakersfieldQuake\gemini4_models.html:
A 100% self-contained, offline WebGL2 3D Showcase & Interactive Studio featuring
every 3D model and physics simulation created by Gemini 4 for BakersfieldQuake.

Covers all 14 Gemini 4 creations across 4 suites:
  1. Mega Man 480 Hz Explosion & Debris Suite (31-body TRS physics scene + 4 DarkPlaces MD3 packs)
  2. Mega Man Player Weapon Suite (Mega-Slinger Rail Gun, Ranger Gauntlet Throw, Clean Payload)
  3. Pocket Rocket Throwable Suite (Giant Hand Weapon, Flying Torpedo Projectile, 3D Character)
  4. Custom Weapons, Gear & Reconstructions (AOL Hacker Laptop Gun, Twin-Thruster Jetpack JP-02, Big Ears 3D Head)

Usage:
    python3.13 source/mm_tools/build_gemini4_gallery.py
"""
import base64
import gzip
import io
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
TEMPLATE = os.path.join(HERE, "gemini4_gallery.template.html")
OUT_HTML = os.path.join(MOD, "gemini4_models.html")
SRC_GLB = r"g:\Downloads\Telegram Desktop\megaman1.glb"

sys.path.insert(0, HERE)
import md3lib
from mm_explode_sim import build_fracture_atlas, build_blast_starburst_mesh, part_world_aligned_mesh


class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_image(self, key, im, label="", max_dim=1024, force_png=False, jpeg_q=89, nearest=False):
        if key in self.tex_map:
            return self.tex_map[key]
        w0, h0 = im.size
        has_alpha = im.mode == "RGBA" and np.array(im.getchannel("A")).min() < 250
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        if has_alpha or force_png or max(im.size) <= 128:
            im_out = im.convert("RGBA" if has_alpha else "RGB")
            im_out.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            im_out = im.convert("RGB")
            im_out.save(bio, "JPEG", quality=jpeg_q, optimize=True)
            mime = "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[key] = idx
        self.tex_list.append(dict(
            key=os.path.basename(key),
            label=label or os.path.basename(key),
            w=w0,
            h=h0,
            alpha=bool(has_alpha),
            nearest=bool(nearest),
            uri=uri,
        ))
        return idx

    def add_tex_file(self, path, label="", max_dim=1024, force_png=False, jpeg_q=89, nearest=False):
        abs_p = os.path.abspath(path)
        if abs_p in self.tex_map:
            return self.tex_map[abs_p]
        im = Image.open(abs_p)
        im.load()
        return self.add_image(abs_p, im, label=label or os.path.basename(abs_p),
                              max_dim=max_dim, force_png=force_png, jpeg_q=jpeg_q, nearest=nearest)


def strip_reversed_dups_and_orient(tris, vv0, nn0):
    """Removes exact duplicate reversed triangles to prevent coplanar z-fighting,
    and ensures remaining triangles wind counter-clockwise relative to vertex normals."""
    seen = set()
    kept = []
    had_dup = False
    for a, b, c in tris:
        a, b, c = int(a), int(b), int(c)
        if a == b or b == c or a == c:
            continue
        rev_keys = ((a, c, b), (c, b, a), (b, a, c))
        if any(rk in seen for rk in rev_keys):
            had_dup = True
            continue
        seen.add((a, b, c))
        kept.append([a, b, c])

    if not kept:
        return np.zeros((0, 3), dtype=np.uint16), had_dup

    tri_arr = np.array(kept, dtype=np.int64)
    p0 = vv0[tri_arr[:, 0]]
    p1 = vv0[tri_arr[:, 1]]
    p2 = vv0[tri_arr[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    navg = nn0[tri_arr[:, 0]] + nn0[tri_arr[:, 1]] + nn0[tri_arr[:, 2]]
    dots = np.sum(fn * navg, axis=1)
    flip = dots < -1e-9
    if np.any(flip):
        tmp = tri_arr[flip, 1].copy()
        tri_arr[flip, 1] = tri_arr[flip, 2]
        tri_arr[flip, 2] = tmp
    return tri_arr.astype(np.uint16), had_dup


def build_wire_edges(tri_arr):
    if len(tri_arr) == 0:
        return np.zeros((0, 2), dtype=np.uint16)
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype(np.uint16)


def pack_md3_asset(packer, path, surf_resolver, idle_frames=None, meta=None):
    m = md3lib.read(path)
    nf = m["nframes"]
    if idle_frames is None:
        idle_frames = list(range(min(nf, 12)))

    surfs_out = []
    tot_v, tot_t = 0, 0
    idle_pts = []

    for s in m["surfaces"]:
        sname = s["name"]
        nv = len(s["st"])
        uv_arr = np.asarray(s["st"], dtype=np.float32)
        wrap = bool(uv_arr.min() < -0.01 or uv_arr.max() > 1.01)

        vv0 = np.asarray(s["frames"][0][0], dtype=np.float64)
        nn0 = np.asarray(s["frames"][0][1], dtype=np.float64)
        tri_arr, had_dup = strip_reversed_dups_and_orient(s["tris"], vv0, nn0)
        edges_arr = build_wire_edges(tri_arr)
        nt = len(tri_arr)
        tot_v += nv
        tot_t += nt

        sh = surf_resolver(sname, s["shader"])
        if not sh.get("additive", False):
            for fi in idle_frames:
                if fi < nf:
                    pts_f = np.asarray(s["frames"][fi][0], dtype=np.float32)
                    if len(pts_f):
                        idle_pts.append(pts_f)

        # Compute high-precision int16 quantization scale (8-byte 4-short aligned per vertex for D3D11/ANGLE!)
        all_v = np.stack([np.asarray(fr[0], dtype=np.float32) for fr in s["frames"]], axis=0)
        all_n = np.stack([np.asarray(fr[1], dtype=np.float32) for fr in s["frames"]], axis=0)
        max_abs = float(np.max(np.abs(all_v))) if all_v.size else 1.0
        pos_scale = max(max_abs / 32000.0, 1.0 / 512.0)

        pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
        pos_i16[:, :, :3] = np.clip(np.round(all_v / pos_scale), -32767, 32767).astype("<i2")

        n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
        all_n_unit = all_n / n_len
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        nrm_i8[:, :, :3] = np.clip(np.round(all_n_unit * 127.0), -127, 127).astype("<i1")

        surfs_out.append(dict(
            name=sname,
            nv=nv,
            nt=nt,
            ne=len(edges_arr),
            posScale=round(pos_scale, 8),
            wrap=bool(wrap or sh.get("scrollV", 0.0) != 0.0),
            tris=packer.add_bytes(tri_arr.tobytes()),
            edges=packer.add_bytes(edges_arr.tobytes()),
            uv=packer.add_bytes(uv_arr.tobytes()),
            pos=packer.add_bytes(pos_i16.tobytes()),
            nrm=packer.add_bytes(nrm_i8.tobytes()),
            tex=sh["tex"],
            texFps=sh.get("fps", 0.0),
            metallic=sh.get("metallic", 0.18),
            roughness=sh.get("roughness", 0.48),
            spec=sh.get("spec", 0.45),
            unlit=1 if sh.get("unlit") else 0,
            additive=1 if sh.get("additive") else 0,
            alphaTest=1 if sh.get("alphaTest") else 0,
            twoSided=1 if (had_dup or sh.get("twoSided")) else 0,
        ))

    pts_cat = np.vstack(idle_pts) if idle_pts else np.zeros((1, 3), dtype=np.float32)
    bmin = pts_cat.min(axis=0).round(2).tolist()
    bmax = pts_cat.max(axis=0).round(2).tolist()

    out = dict(
        kind="md3",
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        bbox=[bmin, bmax],
        surfaces=surfs_out,
    )
    if meta:
        out.update(meta)
    return out


def build_shrapnel_constellation(packer, debris_tex_id):
    """Packs all 8 fractured hardware & Voronoi steel shrapnel MD3s (mm_cap, mm_axle, mm_frag1..6)
    into a curated 16-frame 3D zero-G constellation so every fractured solid & interior cut face is inspectable."""
    part_specs = [
        ("mm_cap.md3",   "rear_cap",   0.0,  0.0,  4.2, (0.3, 1.0, 0.2)),
        ("mm_axle.md3",  "cross_axle", 0.0,  0.0, -3.8, (0.2, 0.4, 1.0)),
    ]
    frag_files = [f"mm_frag{i}.md3" for i in range(1, 7)]
    for idx, fn in enumerate(frag_files):
        ang = idx * (2.0 * math.pi / len(frag_files))
        r = 9.2
        z = 1.6 * math.sin(idx * 2.1)
        axis = (math.cos(ang * 1.3), math.sin(ang * 0.7), 0.85)
        part_specs.append((fn, f"voronoi_frag_{idx + 1}", r * math.cos(ang), r * math.sin(ang), z, axis))

    nf = 24
    surfs_out = []
    tot_v, tot_t = 0, 0
    idle_pts = []

    for p_idx, (fn, label, ox, oy, oz, ax) in enumerate(part_specs):
        m = md3lib.read(os.path.join(PROGS, fn))
        s = m["surfaces"][0]
        nv = len(s["st"])
        uv_arr = np.asarray(s["st"], dtype=np.float32)
        vv0 = np.asarray(s["frames"][0][0], dtype=np.float64)
        nn0 = np.asarray(s["frames"][0][1], dtype=np.float64)
        tri_arr, had_dup = strip_reversed_dups_and_orient(s["tris"], vv0, nn0)
        edges_arr = build_wire_edges(tri_arr)
        nt = len(tri_arr)
        tot_v += nv
        tot_t += nt

        ax_v = np.array(ax, dtype=np.float64)
        ax_v /= np.linalg.norm(ax_v)
        center0 = vv0.mean(axis=0)
        v_local = vv0 - center0

        all_v = np.zeros((nf, nv, 3), dtype=np.float32)
        all_n = np.zeros((nf, nv, 3), dtype=np.float32)
        for fi in range(nf):
            th = (2.0 * math.pi * fi) / nf
            # Smooth Rodrigues rotation (1 full gentle revolution over 24 frames so loop is seamless!)
            K = np.array([
                [0, -ax_v[2], ax_v[1]],
                [ax_v[2], 0, -ax_v[0]],
                [-ax_v[1], ax_v[0], 0],
            ])
            R = np.eye(3) + math.sin(th) * K + (1.0 - math.cos(th)) * (K @ K)
            bob = 0.55 * math.sin(th + p_idx * 0.9)
            vf = (v_local @ R.T) + np.array([ox, oy, oz + bob])
            nf_n = nn0 @ R.T
            all_v[fi] = vf.astype(np.float32)
            all_n[fi] = nf_n.astype(np.float32)

        idle_pts.append(all_v[0])
        max_abs = float(np.max(np.abs(all_v)))
        pos_scale = max(max_abs / 32000.0, 1.0 / 512.0)

        pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
        pos_i16[:, :, :3] = np.clip(np.round(all_v / pos_scale), -32767, 32767).astype("<i2")
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        nrm_i8[:, :, :3] = np.clip(np.round(all_n * 127.0), -127, 127).astype("<i1")

        is_cap = (fn == "mm_cap.md3")
        surfs_out.append(dict(
            name=label,
            nv=nv,
            nt=nt,
            ne=len(edges_arr),
            posScale=round(pos_scale, 8),
            wrap=False,
            tris=packer.add_bytes(tri_arr.tobytes()),
            edges=packer.add_bytes(edges_arr.tobytes()),
            uv=packer.add_bytes(uv_arr.tobytes()),
            pos=packer.add_bytes(pos_i16.tobytes()),
            nrm=packer.add_bytes(nrm_i8.tobytes()),
            tex=[debris_tex_id],
            texFps=0.0,
            metallic=0.15 if is_cap else 0.85,
            roughness=0.52 if is_cap else 0.22,
            spec=0.35 if is_cap else 1.25,
            unlit=0,
            additive=0,
            alphaTest=0,
            twoSided=1 if had_dup else 0,
        ))

    pts_cat = np.vstack(idle_pts)
    return dict(
        id="mm_shrapnel_pack",
        kind="md3",
        suite="explosion",
        badge="8 VORONOI MD3 SOLIDS",
        name="Mega Man — Voronoi Shrapnel & Hardware Pack",
        file="progs/mm_cap.md3, progs/mm_axle.md3, progs/mm_frag1..6.md3",
        script="source/mm_tools/blender_fracture_mm.py + build_mm_debris.py",
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        animFps=10,
        az=0.65,
        el=0.26,
        distMul=1.02,
        bbox=[pts_cat.min(0).round(2).tolist(), pts_cat.max(0).round(2).tolist()],
        surfaces=surfs_out,
        clips=[
            dict(name="Zero-G Fracture Inspection (Loop)", frames=list(range(nf))),
            dict(name="Freeze Pose", frames=[0]),
        ],
        presets=[
            ["Constellation 3/4", 0.65, 0.26, 1.02],
            ["Top Ring Overview", 0.40, 1.18, 1.12],
            ["Close-Up Cut Faces", 1.45, 0.12, 0.68],
        ],
        summary="All 8 in-game DarkPlaces hardware & 3D Voronoi steel shrapnel MD3 models arranged in an inspectable constellation.",
        how=[
            "Carved in headless Blender 5.2 via 3D Voronoi plane bisection (`bmesh.ops.bisect_plane`) with persistent `is_orig` face tagging so outer brushed-steel UVs remain 100% intact.",
            "Every newly exposed interior cut cap is planar-mapped onto a procedural brushed-steel fracture grain strip (`u in [0.90, 0.98]`).",
            "Spawned in clusters of 12 bouncing, spinning shrapnel entities (`MM_SpawnDebris`) whenever Mega Man detonates in DarkPlaces.",
        ],
    )


def pack_trs_explosion_scene(packer):
    """Packs the full 31-rigid-body 480 Hz -> 60 FPS Mega Man explosion & rolling wreckage simulation!"""
    parts_json = os.path.join(HERE, "out", "mm_fractured_parts.json")
    sim_npz = os.path.join(HERE, "out", "mm_explode_sim_cache.npz")
    with open(parts_json, "r", encoding="utf-8") as f:
        parts = json.load(f)
    sim = np.load(sim_npz, allow_pickle=True)
    fps = int(np.asarray(sim["fps"]).reshape(-1)[0])
    n_frames = int(np.asarray(sim["n_frames"]).reshape(-1)[0])
    boom_frame = int(np.asarray(sim["boom_frame"]).reshape(-1)[0])
    sparks = json.loads(str(np.asarray(sim["sparks_json"]).reshape(-1)[0]))

    atlas_im = build_fracture_atlas(SRC_GLB)
    tex_id = packer.add_image("mm_explode_atlas", atlas_im,
                              label="Mega Man Fracture + Brushed Steel Atlas (1024×1024)",
                              max_dim=1024, jpeg_q=91)

    blast_mesh = build_blast_starburst_mesh()
    ordered_names = (
        ["wheel_left", "wheel_right", "main_bar", "rear_cap", "axle_left", "axle_right"]
        + [k for k in sorted(parts.keys()) if k.startswith("frag_")]
        + ["blast_flash"]
    )

    surfs_out = []
    tot_v, tot_t = 0, 0

    for name in ordered_names:
        if name == "blast_flash":
            vw = np.asarray(blast_mesh["verts"], dtype=np.float64)
            nw = np.asarray(blast_mesh["norms"], dtype=np.float64)
            uv_arr = np.asarray(blast_mesh["uvs"], dtype=np.float32)
            raw_tris = blast_mesh["tris"]
            cat = "flash"
            metallic, roughness, spec, unlit, additive = 0.0, 0.5, 0.0, 1, 1
        else:
            p = parts[name]
            vw, nw = part_world_aligned_mesh(p)
            uv_arr = np.asarray(p["uvs"], dtype=np.float32)
            raw_tris = p["tris"]
            pmat = p.get("phys_mat", "metal")
            if name in ("wheel_left", "wheel_right"):
                cat = "wheel"
                metallic, roughness, spec = 0.12, 0.54, 0.42
            elif name == "main_bar":
                cat = "bar"
                metallic, roughness, spec = 0.88, 0.16, 1.45
            elif name in ("rear_cap", "axle_left", "axle_right"):
                cat = "hardware"
                metallic = 0.18 if name == "rear_cap" else 0.82
                roughness = 0.50 if name == "rear_cap" else 0.22
                spec = 0.35 if name == "rear_cap" else 1.15
            else:
                cat = "frag"
                metallic, roughness, spec = 0.82, 0.24, 1.15
            unlit, additive = 0, 0

        tri_arr, had_dup = strip_reversed_dups_and_orient(raw_tris, vw, nw)
        edges_arr = build_wire_edges(tri_arr)
        nv = len(vw)
        nt = len(tri_arr)
        tot_v += nv
        tot_t += nt

        max_abs = max(float(np.max(np.abs(vw))), 1e-3)
        pos_scale = max(max_abs / 32000.0, 1.0 / 512.0)
        pos_i16 = np.zeros((1, nv, 4), dtype="<i2")
        pos_i16[0, :, :3] = np.clip(np.round(vw / pos_scale), -32767, 32767).astype("<i2")

        n_len = np.maximum(np.linalg.norm(nw, axis=1, keepdims=True), 1e-8)
        nw_unit = nw / n_len
        nrm_i8 = np.zeros((1, nv, 4), dtype="<i1")
        nrm_i8[0, :, :3] = np.clip(np.round(nw_unit * 127.0), -127, 127).astype("<i1")

        # TRS track in Quake units: pos(3) + quat_xyzw(4) + scl(3) = 10 float32s per frame
        tr_p = np.asarray(sim[f"pos_{name}"], dtype=np.float32)
        tr_r = np.asarray(sim[f"rot_{name}"], dtype=np.float32)
        tr_r /= np.maximum(np.linalg.norm(tr_r, axis=1, keepdims=True), 1e-8)
        tr_s = np.asarray(sim[f"scl_{name}"], dtype=np.float32)
        trs = np.hstack([tr_p, tr_r, tr_s]).astype("<f4")

        surfs_out.append(dict(
            name=name,
            cat=cat,
            nv=nv,
            nt=nt,
            ne=len(edges_arr),
            posScale=round(pos_scale, 8),
            wrap=False,
            tris=packer.add_bytes(tri_arr.tobytes()),
            edges=packer.add_bytes(edges_arr.tobytes()),
            uv=packer.add_bytes(uv_arr.tobytes()),
            pos=packer.add_bytes(pos_i16.tobytes()),
            nrm=packer.add_bytes(nrm_i8.tobytes()),
            trs=packer.add_bytes(trs.tobytes()),
            tex=[tex_id],
            texFps=0.0,
            metallic=metallic,
            roughness=roughness,
            spec=spec,
            unlit=unlit,
            additive=additive,
            alphaTest=0,
            twoSided=1 if (had_dup or cat == "flash") else 0,
        ))

    js_sparks = [
        dict(
            t=round(float(sp["t"]), 4),
            p=[round(float(sp["pos"][0]), 2), round(float(sp["pos"][1]), 2), round(float(sp["pos"][2]), 2)],
            i=round(float(sp["intensity"]), 2),
        )
        for sp in sparks
    ]

    return dict(
        id="mm_explode_scene",
        kind="trs",
        hero=True,
        suite="explosion",
        badge="HERO · 31 RIGID BODIES · 480 HZ",
        name="Mega Man Contraption — 31-Piece Detonation & Rolling Wreckage",
        file="megaman_explode.glb (3.13 MB animated glTF 2.0)",
        script="source/mm_tools/blender_fracture_mm.py + mm_explode_sim.py",
        standaloneHref="megaman_explode.html",
        downloadHref="megaman_explode.glb",
        nf=n_frames,
        boomFrame=boom_frame,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        animFps=fps,
        az=-1.05,
        el=0.38,
        distMul=1.08,
        actionLabel="💥 Re-Detonate!",
        # Arena bounds centered near detonation so card & overview frame both rolling wheels + bar!
        bbox=[[-48.0, -52.0, 0.0], [52.0, 52.0, 26.0]],
        surfaces=surfs_out,
        sparks=js_sparks,
        clips=[
            dict(name="Full 4.5s Detonation & Roll", frames=list(range(0, n_frames))),
            dict(name="Pre-Blast Wheel Rev (0.0–0.42s)", frames=list(range(0, boom_frame))),
            dict(name="Core Shatter Burst (0.38–1.10s)", frames=list(range(max(0, boom_frame - 3), min(n_frames, boom_frame + 42)))),
            dict(name="Wheels Banking & Bar Rolling (0.8–4.5s)", frames=list(range(48, n_frames))),
        ],
        presets=[
            ["Arena Overview", -1.05, 0.38, 1.08],
            ["Detonation Close-Up", -0.65, 0.24, 0.44],
            ["Low Action Angle", -1.28, 0.16, 0.85],
            ["Top-Down Trajectories", -1.57, 1.32, 1.25],
        ],
        trackTargets=[
            ["Overview", "none"],
            ["Track Left Wheel", "wheel_left"],
            ["Track Right Wheel", "wheel_right"],
            ["Track Steel Bar", "main_bar"],
        ],
        summary="31 watertight fractured rigid bodies simulated at 480 Hz: wheel spin-up, 3D starburst core flash, 24 Voronoi fragments, banked wheel curves into Euler-disk coin wobble, and tumbling/rolling stainless bar.",
        how=[
            "Headless Blender 5.2 separates both wheels, high-detail brushed stainless bar (`3,655` verts, UV-seam preserved), Delrin rear cap, and cross-axles, then carves 24 watertight 3D Voronoi shrapnel solids.",
            "Custom 480 Hz physics solver simulates wheel gyroscopic banking (`260°–320°` curved arcs), elastic tire bounce, Euler-disk coin wobble onto flat sidewalls, and end-over-end bar clanging into 4+ floor revolutions.",
            "Includes live colored ground-contact rolling trails (cyan left wheel, amber right wheel, green steel bar) and floor impact sparks.",
        ],
    )


def main():
    packer = ArenaPacker()
    models = []

    print("1/5 Packing Hero 31-Piece Mega Man 480 Hz Explosion & Rolling Wreckage scene...")
    models.append(pack_trs_explosion_scene(packer))

    print("2/5 Packing Mega Man Player Weapon Suite (3 models)...")
    mmw_dir = os.path.join(HERE, "out", "megaman_weapon")
    mmw_tex = {
        "progs/mmw_chrome_axle": (packer.add_tex_file(os.path.join(mmw_dir, "mmw_chrome_axle.png"), "Chrome Bar, Weld & Axle"),
                                  dict(metallic=0.88, roughness=0.15, spec=1.45)),
        "progs/mmw_wheel":       (packer.add_tex_file(os.path.join(mmw_dir, "mmw_wheel.png"), "5-Rib Tire & Stamped White Rim"),
                                  dict(metallic=0.10, roughness=0.52, spec=0.42)),
        "progs/mmw_gun_metal":   (packer.add_tex_file(os.path.join(mmw_dir, "mmw_gun_metal.png"), "Quake Iron, Launch Rails & Tanks"),
                                  dict(metallic=0.64, roughness=0.30, spec=0.92)),
        "progs/mmw_hand":        (packer.add_tex_file(os.path.join(mmw_dir, "mmw_hand.png"), "Ranger Leather Glove & Bracer"),
                                  dict(metallic=0.20, roughness=0.46, spec=0.45)),
        "progs/mmw_gauge_glow":  (packer.add_tex_file(os.path.join(mmw_dir, "mmw_gauge_glow.png"), "0–250 PSI Dial & Mega-Core Glow", force_png=True),
                                  dict(metallic=0.0, roughness=0.5, spec=0.0, unlit=True)),
        "progs/mmw_fx":          (packer.add_tex_file(os.path.join(mmw_dir, "mmw_fx.png"), "Pneumatic Shock-Ring & Slipstream FX", force_png=True),
                                  dict(metallic=0.0, roughness=0.5, spec=0.0, unlit=True, additive=True, twoSided=True)),
    }

    def resolve_mmw(sname, shader):
        tid, opts = mmw_tex[shader]
        d = dict(tex=[tid])
        d.update(opts)
        return d

    slinger_md3_path = os.path.join(mmw_dir, "v_megaman_gun.md3")
    slinger_nf = md3lib.read(slinger_md3_path)["nframes"]
    models.append(pack_md3_asset(
        packer, slinger_md3_path, resolve_mmw, idle_frames=list(range(0, 16)),
        meta=dict(
            id="v_megaman_gun",
            suite="mm_weapon",
            badge="VIEWMODEL · 37 FRAMES",
            name="The Mega-Slinger · Pneumatic Rail-Catapult Gun",
            file="progs/v_megaman.md3 (out/megaman_weapon/v_megaman_gun.md3)",
            script="source/mm_tools/build_megaman_weapon.py",
            standaloneHref="megaman_weapon.html",
            animFps=13,
            pov=True,
            az=2.45,
            el=0.24,
            distMul=0.95,
            actionLabel="⚡ Fire Catapult!",
            fireClipIdx=1,
            clips=[
                dict(name="Idle: Wheel Spin & PSI Needle", frames=list(range(0, 16))),
                dict(name="Fire, Shock-Ring & Spring Reload", frames=list(range(16, slinger_nf))),
                dict(name="Full Showcase Cycle", frames=list(range(0, slinger_nf))),
            ],
            presets=[
                ["3/4 Hero Orbit", 2.45, 0.24, 0.95],
                ["Muzzle & Spinning Wheels", 0.22, 0.14, 0.92],
                ["Breech, Hands & PSI Dial", 3.02, 0.30, 0.82],
                ["Left Profile (Rails & Tank)", 1.62, 0.14, 1.02],
            ],
            summary="Open-top twin I-beam pneumatic rail catapult cradling Mega Man's spinning chrome bar & 5-ribbed wheels, with 0–250 PSI dial and piston slam reload.",
            how=[
                "Twin launch rails cradle the bullet-nose chrome bar with wide side clearance for the steel cross-axle and spinning pneumatic wheels.",
                "Idle (`0–15`): weapon breathing sway, friction rollers actively spinning the tires, quivering 190 PSI analog needle, and glowing cyan Mega-Core.",
                "Fire (`16–36`): retention jaws snap open, twin chrome pistons slam the bronze sled downrange with a 3D shock-ring, followed by spring-elevator reload.",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(mmw_dir, "v_megaman_hand.md3"), resolve_mmw, idle_frames=list(range(0, 16)),
        meta=dict(
            id="v_megaman_hand",
            suite="mm_weapon",
            badge="VIEWMODEL · 32 FRAMES",
            name="Quake Ranger Gauntlet · Hand-Thrown Mega Man",
            file="source/mm_tools/out/megaman_weapon/v_megaman_hand.md3",
            script="source/mm_tools/build_megaman_weapon.py",
            standaloneHref="megaman_weapon.html",
            animFps=13,
            pov=True,
            az=2.42,
            el=0.22,
            distMul=0.95,
            actionLabel="⚡ Hurl Mega Man!",
            fireClipIdx=1,
            clips=[
                dict(name="Idle: Revving Wheels & Grip", frames=list(range(0, 16))),
                dict(name="Wind-Up, Open-Hand Throw & Catch", frames=list(range(16, 32))),
                dict(name="Full Showcase Cycle", frames=list(range(0, 32))),
            ],
            presets=[
                ["3/4 Gauntlet & Wheels", 2.42, 0.22, 0.95],
                ["Front Tires & Nosecone", 0.30, 0.15, 0.92],
                ["Leather Glove & Knuckle Studs", 1.45, -0.05, 0.80],
            ],
            summary="Articulated Quake Ranger leather glove & riveted bronze bracer gripping, revving, and hurling the wheeled contraption.",
            how=[
                "Sculpted distressed leather combat glove with 4-stud bronze knuckle plate, buckled forearm bracer, and 5 articulated 3-phalanx fingers.",
                "Cocks wrist upward while revving the tires, whips forward uncurling all 5 fingers with a cyan slipstream wake, and catches a fresh unit.",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(mmw_dir, "megaman_clean.md3"), resolve_mmw, idle_frames=list(range(0, 16)),
        meta=dict(
            id="megaman_clean",
            suite="mm_weapon",
            badge="CLEAN RECREATION · 16 FRAMES",
            name="Clean Reconstructed Mega Man Contraption",
            file="source/mm_tools/out/megaman_weapon/megaman_clean.md3",
            script="source/mm_tools/mmw_geometry.py",
            standaloneHref="megaman_weapon.html",
            animFps=12,
            az=0.68,
            el=0.26,
            distMul=0.96,
            clips=[
                dict(name="Wheel-Spin Drive Cycle", frames=list(range(0, 16))),
            ],
            presets=[
                ["3/4 Contraption View", 0.68, 0.26, 0.96],
                ["Front Chrome Bullet Nose", 0.0, 0.18, 0.92],
                ["Concave Rim, Nut & Valve", 1.57, 0.14, 0.78],
                ["Rear Delrin Cap & TIG Weld", 3.14, 0.22, 0.94],
            ],
            summary="Artifact-free procedural 3D recreation of megaman1.glb with concave white steel rims, 5-ribbed tires, Schrader valves, cotter pins & mirror-chrome bar.",
            how=[
                "Rebuilds the 167,500-tri noisy scan into crisp Quake geometry with true 3D concave stamped-steel dish rims, hex axle nuts, and yellow cotter pins.",
                "Anisotropic polished chrome bar tilted at -34.7° with stepped matte-black rear cap, TIG-welded cross-sleeve, and ogive nose.",
            ],
        )
    ))

    print("3/5 Packing Pocket Rocket Throwable Suite (3 models)...")
    pr_dir = os.path.join(HERE, "out", "pocket_rocket")
    pr_tex_dir = os.path.join(pr_dir, "textures")
    pr_md3_dir = os.path.join(pr_dir, "md3")
    pr_tex = {
        "giant_hand":    (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_giant_hand.png"), "Giant 1st-Person Hand, Palm & Nails"),
                          dict(metallic=0.06, roughness=0.52, spec=0.34)),
        "char_skin":     (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_skin.png"), "Character Face & Skin"),
                          dict(metallic=0.05, roughness=0.46, spec=0.38)),
        "char_hair":     (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_hair.png"), "Champagne Blonde Layered Hair"),
                          dict(metallic=0.12, roughness=0.34, spec=0.58, twoSided=True)),
        "char_pink_top": (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_pink_top.png"), "Hot-Pink Tie-Front Top"),
                          dict(metallic=0.05, roughness=0.60, spec=0.28, twoSided=True)),
        "char_jeans":    (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_jeans.png"), "Indigo Skinny Jeans & Stitching"),
                          dict(metallic=0.04, roughness=0.72, spec=0.20)),
        "char_sneakers": (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_sneakers.png"), "Hot-Pink Laced Sneakers"),
                          dict(metallic=0.08, roughness=0.48, spec=0.36)),
        "speedlines":    (packer.add_tex_file(os.path.join(pr_tex_dir, "tex_speedlines.png"), "Aerodynamic Slipstream Speed-Lines", force_png=True),
                          dict(metallic=0.0, roughness=0.5, spec=0.0, unlit=True, additive=True, twoSided=True)),
    }

    def resolve_pr(sname, _shader):
        tid, opts = pr_tex[sname]
        d = dict(tex=[tid])
        d.update(opts)
        return d

    models.append(pack_md3_asset(
        packer, os.path.join(pr_md3_dir, "v_pocket_rocket.md3"), resolve_pr, idle_frames=list(range(0, 12)),
        meta=dict(
            id="v_pocket_rocket",
            suite="pocket_rocket",
            badge="VIEWMODEL · 36 FRAMES · 55K TRIS",
            name="Pocket Rocket · Held Giant Hand Weapon",
            file="out/pocket_rocket/md3/v_pocket_rocket.md3 (+ .glb)",
            script="source/mm_tools/pocket_rocket/sculpt_hand_and_export.py",
            downloadHref="source/mm_tools/out/pocket_rocket/glb/pocket_rocket_weapon.glb",
            animFps=11,
            pov=True,
            az=2.85,
            el=0.16,
            distMul=0.95,
            actionLabel="⚡ Throw Torpedo!",
            fireClipIdx=2,
            clips=[
                dict(name="Idle: Hands on Hips", frames=list(range(0, 12))),
                dict(name="Excited Dual-Arm Wave", frames=list(range(12, 24))),
                dict(name="Wind-Up & Open-Hand Throw", frames=list(range(24, 36))),
                dict(name="Full 36-Frame Showcase", frames=list(range(0, 36))),
            ],
            presets=[
                ["3/4 Hand & Grip", 2.65, 0.18, 0.95],
                ["Front Grip & Manicured Nails", 3.08, 0.08, 0.88],
                ["Back of Mini Character", 0.35, 0.18, 0.95],
            ],
            summary="18-bone sculpted giant right hand with 3D knuckles & fingernails gripping the 25-bone rigged miniature woman around the waist and hurling her forward.",
            how=[
                "Built completely from scratch in Blender 5.2 + Python FK skinning: 18-bone anatomical right hand with palm creases and 5 inset 3D fingernails.",
                "Includes 3 distinct animation acts: breathing idle (`0–11`), excited dual-arm wave (`12–23`), and full 5-finger splay release (`24–35`).",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(pr_md3_dir, "pocket_rocket_proj.md3"), resolve_pr, idle_frames=list(range(0, 16)),
        meta=dict(
            id="pocket_rocket_proj",
            suite="pocket_rocket",
            badge="PROJECTILE · 16 FRAMES + VFX",
            name="Pocket Rocket · Flying Skydiver Torpedo Projectile",
            file="out/pocket_rocket/md3/pocket_rocket_proj.md3 (+ .glb)",
            script="source/mm_tools/pocket_rocket/sculpt_hand_and_export.py",
            downloadHref="source/mm_tools/out/pocket_rocket/glb/pocket_rocket_projectile.glb",
            animFps=12,
            az=0.68,
            el=0.18,
            distMul=0.96,
            clips=[
                dict(name="Skydiver Torpedo Flight (Loop)", frames=list(range(0, 16))),
            ],
            presets=[
                ["Front-3/4 Glide", 0.68, 0.18, 0.96],
                ["Side Torpedo Profile", -1.57, 0.06, 0.92],
                ["Rear-3/4 Hair & Jeans", -2.42, 0.26, 0.96],
                ["Top-Down Wingspan", -1.57, 1.25, 1.05],
            ],
            summary="In-flight projectile hurled horizontally (+X) with swept-wing arms, billowing blonde hair, fluttering bow ribbons, and additive slipstream speed-lines.",
            how=[
                "25-bone skeletal flight pose with sinusoidal hair, ribbon, and limb flutter across 16 seamless loop frames plus additive RGBA slipstream streaks.",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(pr_md3_dir, "pocket_rocket_char.md3"), resolve_pr, idle_frames=list(range(0, 8)),
        meta=dict(
            id="pocket_rocket_char",
            suite="pocket_rocket",
            badge="CHARACTER · 32 FRAMES",
            name="Pocket Rocket · Sculpted 25-Bone 3D Character",
            file="out/pocket_rocket/md3/pocket_rocket_char.md3 (+ .glb)",
            script="source/mm_tools/pocket_rocket/sculpt_character.py",
            downloadHref="source/mm_tools/out/pocket_rocket/glb/pocket_rocket_character.glb",
            animFps=10,
            az=0.38,
            el=0.14,
            distMul=1.02,
            clips=[
                dict(name="Hands-on-Hips Idle", frames=list(range(0, 8))),
                dict(name="Joyful Dual-Arm Wave", frames=list(range(8, 16))),
                dict(name="Ready-to-Fly Spread", frames=list(range(16, 24))),
                dict(name="Skydiver Flight Pose", frames=list(range(24, 32))),
            ],
            presets=[
                ["Front 3/4 Hero", 0.38, 0.14, 1.02],
                ["Face & Hair Close-Up", 0.18, 0.16, 0.62],
                ["Side Silhouette", -1.57, 0.08, 1.02],
                ["Back Hair & Jeans Pockets", 3.05, 0.12, 1.02],
            ],
            summary="Unobstructed 360° turnaround of the custom-sculpted 25-bone character mesh across 4 animated pose clips and 5 high-res material surfaces.",
            how=[
                "Custom parametric anatomical sculpting + linear-blend skinning with layered champagne-blonde hair, tie-front cardigan, stitched indigo jeans & laced sneakers.",
            ],
        )
    ))

    print("4/5 Packing Custom Gear, Laptop Gun & Big Ears 3D Head (3 models)...")

    # 4a. AOL Dial-Up Hacker Laptop Gun
    def resolve_laptop(sname, shader):
        base = os.path.basename(shader)
        p = os.path.join(PROGS, base + ".png")
        if base == "v_laptop_scr":
            tid = packer.add_tex_file(p, "AOL 5.0 Dial-Up & Hacking LCD (1024×1024)", max_dim=1024, force_png=True)
            return dict(tex=[tid], metallic=0.0, roughness=0.4, spec=0.0, unlit=True)
        if base == "v_laptop_zap":
            tid = packer.add_tex_file(p, "3D Electric Lightning Arc", max_dim=256, force_png=True)
            return dict(tex=[tid], metallic=0.0, roughness=0.5, spec=0.0, unlit=True, additive=True, twoSided=True)
        if base == "v_laptop_keys":
            tid = packer.add_tex_file(p, "Sculpted QWERTY Keyboard & TrackPoint", max_dim=512, force_png=True)
            return dict(tex=[tid], metallic=0.22, roughness=0.42, spec=0.55)
        if base == "v_laptop_body":
            tid = packer.add_tex_file(p, "Matte-Black Chassis & RJ-11 Cord", max_dim=512, force_png=True)
            return dict(tex=[tid], metallic=0.35, roughness=0.38, spec=0.65)
        tid = packer.add_tex_file(p, "Articulated Typing Hands", max_dim=512)
        return dict(tex=[tid], metallic=0.08, roughness=0.52, spec=0.32)

    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_laptop.md3"), resolve_laptop, idle_frames=list(range(0, 12)),
        meta=dict(
            id="v_laptop",
            suite="gear_heads",
            badge="VIEWMODEL · 34 FRAMES",
            name="AOL Dial-Up Hacker Laptop Gun",
            file="progs/v_laptop.md3",
            script="source/mm_tools/build_laptop_gun.py",
            standaloneHref="laptop_gun.html",
            animFps=12,
            pov=True,
            az=2.76,
            el=0.24,
            distMul=0.94,
            actionLabel="⚡ Hack & Zap!",
            fireClipIdx=1,
            clips=[
                dict(name="Full Idle + Rapid Typing & Zap", frames=list(range(0, 34))),
                dict(name="Shoot: Fast Typing & Lightning", frames=list(range(12, 34))),
                dict(name="Right-Hand Hold Idle", frames=list(range(0, 12))),
            ],
            presets=[
                ["3/4 Hands & Screen", 2.76, 0.24, 0.94],
                ["AOL Screen & QWERTY Keys", 3.12, 0.14, 0.72],
                ["Side & Electric Bolts", 1.85, 0.16, 1.08],
                ["Outer Lid Emblem", 0.15, 0.16, 0.92],
            ],
            summary="Black laptop held in the right hand displaying Windows 98 AOL 5.0 Dial-Up & 'Hacking internet lag'; firing whips up the left hand to hammer the 3D keys and discharge cyan lightning.",
            how=[
                "Sculpted 3D QWERTY keycaps, red TrackPoint nub, coiled 56k RJ-11 phone cord, and lossless 1024×1024 unlit LCD screen.",
                "Shoot frames (`12–33`) animate ultra-fast two-handed typing while firing 3D additive cyan-white electric bolts.",
            ],
        )
    ))

    # 4b. Twin-Thruster Rocket Jetpack (JP-02)
    jp_plume_tids = [
        packer.add_tex_file(os.path.join(PROGS, f"jetpack_plume_{k}.png"), f"Mach Shock-Diamond Plume {k + 1}", max_dim=256, force_png=True)
        for k in range(4)
    ]

    def resolve_jetpack(sname, shader):
        base = os.path.basename(shader)
        if base == "jetpack_plume":
            return dict(tex=jp_plume_tids, fps=18.0, unlit=True, additive=True, twoSided=True)
        p = os.path.join(PROGS, base + ".png")
        tid = packer.add_tex_file(p, base.replace("_", " ").title(), max_dim=512, force_png=(base == "jetpack_dial"))
        if base == "jetpack_glow":
            return dict(tex=[tid], unlit=True)
        if base in ("jetpack_metal", "jetpack_tank"):
            return dict(tex=[tid], metallic=0.78, roughness=0.22, spec=1.18)
        if base == "jetpack_dark":
            return dict(tex=[tid], metallic=0.52, roughness=0.34, spec=0.75)
        if base == "jetpack_hose":
            return dict(tex=[tid], metallic=0.65, roughness=0.28, spec=0.95)
        return dict(tex=[tid], metallic=0.18, roughness=0.52, spec=0.38, twoSided=(base == "jetpack_wing"))

    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "jetpack.md3"), resolve_jetpack, idle_frames=list(range(0, 8)),
        meta=dict(
            id="jetpack",
            suite="gear_heads",
            badge="9 SURFACES · AFTERBURNER VFX",
            name="Twin-Thruster Rocket Jetpack (JP-02)",
            file="progs/jetpack.md3",
            script="source/mm_tools/build_jetpack.py",
            standaloneHref="jetpack.html",
            animFps=12,
            az=2.62,
            el=0.16,
            distMul=0.96,
            clips=[
                dict(name="Full Afterburner Thrust", frames=list(range(0, 8))),
                dict(name="Standby Pilot-Flame Idle", frames=list(range(8, 16))),
            ],
            presets=[
                ["Rear Thrusters & Core", 2.68, 0.16, 0.96],
                ["Front Harness & Sticks", 0.45, 0.16, 0.96],
                ["Underneath De Laval Nozzles", 2.95, -0.55, 0.84],
                ["Side Hazard Winglet", 1.57, 0.10, 0.95],
            ],
            summary="9-surface twin-cylinder titanium rocket pack with cyan plasma core, PSI gauge dial, braided Catmull-Rom fuel hoses, EVA harness, pilot sticks & 18 FPS shock-diamond exhaust plumes.",
            how=[
                "Twin brushed-titanium propellant canisters with `JP-02` stencil bands, bleed valves, roll-bar hoops, and hazard winglets.",
                "Gimballed de Laval nozzles drive 4-frame 18 FPS additive Mach shock-diamond thruster plumes.",
            ],
        )
    ))

    # 4c. Giant-Eared 3D Floating Head
    bigears_tid = packer.add_tex_file(os.path.join(PROGS, "bigears.png"), "Region-Pure 360° Head & Ears Bake (1024×1024)", max_dim=1024, jpeg_q=92)
    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "bigears.md3"),
        lambda _sn, _sh: dict(tex=[bigears_tid], metallic=0.04, roughness=0.58, spec=0.26),
        meta=dict(
            id="bigears",
            suite="gear_heads",
            badge="3D TURNTABLE RECONSTRUCTION",
            name="Giant-Eared 3D Floating Portrait Head",
            file="progs/bigears.md3",
            script="source/mm_tools/build_bigears_head.py",
            standaloneHref="bigears_head.html",
            animFps=10,
            az=-0.34,
            el=0.08,
            distMul=0.92,
            clips=[dict(name="Static 3D Sculpture", frames=[0])],
            presets=[
                ["3/4 Portrait", -0.52, 0.08, 0.92],
                ["Front Face", 0.0, 0.05, 0.90],
                ["Left Giant Ear", 1.38, 0.08, 0.92],
                ["Right Profile", -1.48, 0.08, 0.92],
                ["Back of Head", 3.14, 0.10, 0.94],
            ],
            summary="True 3D head-only sculpture reconstructed from 48 turntable views with separated giant cupped ears, Blender 5.2 voxel remesh, and 1024×1024 region-pure texture bake.",
            how=[
                "Separates cranium/face from the two giant cupped ears to prevent visual-hull cheek webbing while carving real 3D nose, lips, chin & ear cartilage.",
                "Voxel-remeshed, smoothed, and decimated to 5,600 triangles in Blender 5.2 with 3D k-NN crease inpainting.",
            ],
        )
    ))

    print("5/5 Packing DarkPlaces In-Game Mega Man Explosion & Debris MD3s (4 packs)...")
    debris_tex_id = packer.add_tex_file(os.path.join(PROGS, "mm_debris_tex.png"), "Mega Man Debris & Fracture Grain Atlas", max_dim=1024, jpeg_q=90)
    blast_flash_id = packer.add_tex_file(os.path.join(PROGS, "mm_blast_flash.png"), "Core Starburst Flash", max_dim=256, force_png=True)

    def resolve_mm_explode(sname, shader):
        if "flash" in sname or "flash" in shader:
            return dict(tex=[blast_flash_id], unlit=True, additive=True, twoSided=True)
        return dict(tex=[debris_tex_id], metallic=0.82, roughness=0.22, spec=1.22, twoSided=True)

    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_explode.md3"), resolve_mm_explode, idle_frames=[2, 3, 4, 5],
        meta=dict(
            id="mm_explode_md3",
            suite="explosion",
            badge="IN-GAME MD3 · 20 FRAMES",
            name="Mega Man — Core Shatter Burst (In-Game MD3)",
            file="progs/mm_explode.md3",
            script="source/mm_tools/build_mm_debris.py",
            animFps=15,
            az=0.62,
            el=0.24,
            distMul=1.08,
            actionLabel="💥 Replay Burst!",
            fireClipIdx=0,
            clips=[
                dict(name="20-Frame Shatter Burst", frames=list(range(0, 20))),
                dict(name="Peak Starburst Flash (f0–6)", frames=list(range(0, 7))),
            ],
            presets=[
                ["3/4 Burst View", 0.62, 0.24, 1.08],
                ["Top Scatter Pattern", 0.3, 1.22, 1.15],
            ],
            summary="20-frame vertex-animated in-game explosion centerpiece (`MM_BurstThink`) combining 24 outward-tumbling Voronoi chunks with an expanding/fading 3D core starburst.",
            how=[
                "Bakes the first 0.67s of the 480 Hz shatter burst directly into 3 MD3 surfaces (`shatter0`, `shatter1`, and additive `flash`) for zero-overhead playback in DarkPlaces.",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_wheel.md3"),
        lambda _sn, _sh: dict(tex=[debris_tex_id], metallic=0.14, roughness=0.52, spec=0.45),
        idle_frames=list(range(0, 16)),
        meta=dict(
            id="mm_wheel",
            suite="explosion",
            badge="IN-GAME MD3 · 16 SPIN FRAMES",
            name="Mega Man — Detached Spinning Tire Debris",
            file="progs/mm_wheel.md3",
            script="source/mm_tools/build_mm_debris.py + megaman.qc",
            animFps=16,
            az=0.58,
            el=0.20,
            distMul=0.95,
            clips=[
                dict(name="16-Frame Rolling Spin", frames=list(range(0, 16))),
            ],
            presets=[
                ["3/4 Rim, Zerk & Valve", 0.58, 0.20, 0.95],
                ["Outer White Dish Face", 1.57, 0.08, 0.92],
                ["5-Rib Tire Tread Profile", 0.0, 0.08, 0.95],
            ],
            summary="Watertight 3,637-vertex pneumatic wheel & white stamped-steel dish rim that bounces, carves banked curves across the Quake floor, reflects off walls, and Euler-disk wobbles flat.",
            how=[
                "Driven in QuakeC by `MM_WheelThink` at 20 Hz: elastic rubber bounces (`megaman/tire1..3.wav`), speed-coupled frame advancing, gyroscopic lean banking, and coin-wobble settle.",
            ],
        )
    ))

    models.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_bar.md3"),
        lambda _sn, _sh: dict(tex=[debris_tex_id], metallic=0.90, roughness=0.15, spec=1.50),
        meta=dict(
            id="mm_bar",
            suite="explosion",
            badge="IN-GAME MD3 · 3,655 VERTS",
            name="Mega Man — Brushed Stainless Steel Central Bar",
            file="progs/mm_bar.md3",
            script="source/mm_tools/blender_fracture_mm.py + megaman.qc",
            animFps=10,
            az=0.62,
            el=0.22,
            distMul=0.92,
            clips=[dict(name="Polished Stainless Inspection", frames=[0])],
            presets=[
                ["3/4 Bar & Bullet Nose", 0.62, 0.22, 0.92],
                ["Ogive Bullet Tip", 0.12, 0.12, 0.78],
                ["Fractured Rear Collar", 2.95, 0.18, 0.84],
            ],
            summary="High-poly (`3,655`-vert / `4,544`-tri) UV-seam-preserved brushed stainless steel central bar & ogive bullet nosecone that clangs with sparks and rolls across the floor.",
            how=[
                "Decimated in Blender 5.2 with `delimit={'UV'}` at `0.20` ratio so cylindrical shading and brushed steel UVs stay mirror-smooth right up to MD3's 4,096-vertex ceiling.",
                "Driven in QuakeC by `MM_BarThink`: tumbles end-over-end with metallic spark showers, then rolls perpendicular to its long axis across the map floor.",
            ],
        )
    ))

    models.append(build_shrapnel_constellation(packer, debris_tex_id))

    gz_bin = gzip.compress(bytes(packer.buf), compresslevel=9)
    b64_gz = base64.b64encode(gz_bin).decode("ascii")
    print(f"Binary arena: raw={len(packer.buf)/1e6:.2f} MB -> gzip={len(gz_bin)/1e6:.2f} MB, textures={len(packer.tex_list)}, models={len(models)}")

    payload = dict(
        binGz=b64_gz,
        binLen=len(packer.buf),
        textures=packer.tex_list,
        models=models,
    )

    with open(TEMPLATE, "r", encoding="utf-8") as f:
        tpl = f.read()
    assert "/*__GEMINI4_DATA__*/null" in tpl, "Missing /*__GEMINI4_DATA__*/null placeholder in template"
    html = tpl.replace("/*__GEMINI4_DATA__*/null", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote standalone Gemini 4 3D Showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
