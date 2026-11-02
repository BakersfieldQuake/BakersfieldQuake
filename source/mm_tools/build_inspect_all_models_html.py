r"""Builds G:\Quake\Combat\BakersfieldQuake\inspect_all_models.html:
A fast, 100% self-contained Master 3D Model Inspector (WebGL2) packing ALL 24 flagship 3D models:
  - Category 1 (jw_air)  : All 3 Ridiculous John Wave x Mega Man 3D Aircraft (72 frames each)
  - Category 2 (sky_veh) : All 4 Combined 4-Video 3D Sky-Vehicles (56 frames each)
  - Category 3 (comp)    : All 8 Source 3D Heads, Mega Man Contraptions & Component Props
  - Category 4 (arsenal) : All 9 Driveable Mod Ground Vehicles, 3D Weapons & Props
  - Plus a live drag-and-drop / file-picker .MD3 (+ .PNG/.JPG) loader for inspecting any other .MD3 on disk!

Usage:
    python3.13 source/mm_tools/build_inspect_all_models_html.py
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
SOUND = os.path.join(MOD, "sound")
TEMPLATE = os.path.join(HERE, "inspect_all_models.template.html")
OUT_HTML = os.path.join(MOD, "inspect_all_models.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_head_grenade as bhg
import build_sky_vehicles as bsv
import md3lib
import mmw_geometry as mmg


def pack_voice_soundboard():
    specs = [
        (os.path.join(SOUND, "john", "jwthrow.wav"),      '🌊 "JOHN WAVE!"'),
        (os.path.join(SOUND, "funny", "waveofhair.wav"),  '💇 "Wave of Hair!"'),
        (os.path.join(SOUND, "john", "jv00.wav"),         '🎙 Quip #1'),
        (os.path.join(SOUND, "john", "jv01.wav"),         '🎙 Quip #2'),
        (os.path.join(SOUND, "john", "jv02.wav"),         '🎙 Quip #3'),
        (os.path.join(SOUND, "john", "jv04.wav"),         '🎙 Quip #4'),
    ]
    out = []
    for wav_p, label in specs:
        if os.path.isfile(wav_p):
            b64 = base64.b64encode(open(wav_p, "rb").read()).decode("ascii")
            out.append(dict(label=label, uri=f"data:audio/wav;base64,{b64}"))
    return out


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

    def add_tex_file(self, path, max_dim=1024, jpeg_q=89, force_png=False, lift=1.0):
        abs_p = os.path.abspath(path)
        key = (abs_p, max_dim, bool(force_png), round(float(lift), 2))
        if key in self.tex_map:
            return self.tex_map[key]
        im = Image.open(abs_p).convert("RGB")
        if abs(lift - 1.0) > 1e-3:
            arr = np.asarray(im, dtype=np.float32) / 255.0
            arr = np.clip((arr ** 0.86) * float(lift), 0.0, 1.0)
            im = Image.fromarray(np.rint(arr * 255.0).astype(np.uint8), "RGB")
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        if force_png or max(im.size) <= 64:
            im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            im.save(bio, "JPEG", quality=jpeg_q, optimize=True)
            mime = "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[key] = idx
        self.tex_list.append(dict(uri=uri, w=im.size[0], h=im.size[1]))
        return idx


def build_wire_edges(tri_arr):
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def encode_surface(packer, sname, shader, uv_arr, tri_arr, all_v, all_n, mat):
    nf, nv, _ = all_v.shape
    assert nv < 65535, f"Surface {sname} nv={nv} exceeds Uint16 limit!"
    uv_f32 = np.asarray(uv_arr, dtype="<f4")
    tri_u16 = np.asarray(tri_arr, dtype="<u2")
    edges_u16 = build_wire_edges(tri_u16)
    nt = len(tri_u16)

    max_abs = float(np.max(np.abs(all_v))) if all_v.size else 1.0
    inv_scale = 64.0 if max_abs < 500.0 else (32000.0 / max(max_abs, 1.0))
    pos_scale = 1.0 / inv_scale

    pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
    pos_i16[:, :, :3] = np.clip(np.round(all_v * inv_scale), -32767, 32767).astype("<i2")
    dpos = pos_i16.copy()
    if nf > 1:
        dpos[1:] = ((pos_i16[1:].astype(np.int32) - pos_i16[:-1].astype(np.int32)) & 0xFFFF).astype("<u2").view("<i2")

    n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
    nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
    nrm_i8[:, :, :3] = np.clip(np.round((all_n / n_len) * 127.0), -127, 127).astype("<i1")
    dnrm = nrm_i8.copy()
    if nf > 1:
        dnrm[1:] = ((nrm_i8[1:].astype(np.int32) - nrm_i8[:-1].astype(np.int32)) & 0xFF).astype("<u1").view("<i1")

    return dict(
        name=sname,
        shader=shader,
        nv=nv,
        nt=nt,
        ne=len(edges_u16),
        posScale=pos_scale,
        tris=packer.add_bytes(tri_u16.tobytes()),
        edges=packer.add_bytes(edges_u16.tobytes()),
        uv=packer.add_bytes(uv_f32.tobytes()),
        pos=packer.add_bytes(dpos.tobytes()),
        nrm=packer.add_bytes(dnrm.tobytes()),
        tex=mat["tex"],
        glowTex=mat.get("glowTex", -1),
        metallic=mat.get("metallic", 0.15),
        roughness=mat.get("roughness", 0.50),
        spec=mat.get("spec", 0.40),
        unlit=1 if mat.get("unlit") else 0,
        additive=1 if mat.get("additive") else 0,
    )


def pack_md3_model(packer, md3_path, surf_mats, meta, bbox_frames=(0,)):
    m = md3lib.read(md3_path)
    nf = m["nframes"]
    surfs_out = []
    tot_v, tot_t = 0, 0
    solid_pts = []

    for s in m["surfaces"]:
        sname = s["name"]
        shader = s["shader"]
        nv = len(s["st"])
        nt = len(s["tris"])
        tot_v += nv
        tot_t += nt

        all_v = np.stack([np.asarray(fr[0], dtype=np.float32) for fr in s["frames"]], axis=0)
        all_n = np.stack([np.asarray(fr[1], dtype=np.float32) for fr in s["frames"]], axis=0)

        mat = surf_mats[shader]
        if not mat.get("additive", False):
            for fi in bbox_frames:
                if 0 <= fi < nf:
                    solid_pts.append(all_v[fi])

        surfs_out.append(encode_surface(packer, sname, shader, s["st"], s["tris"], all_v, all_n, mat))

    if not solid_pts:
        solid_pts = [np.asarray(m["surfaces"][0]["frames"][0][0], dtype=np.float32)]
    pts_cat = np.vstack(solid_pts)
    bmin = pts_cat.min(axis=0).round(2).tolist()
    bmax = pts_cat.max(axis=0).round(2).tolist()

    out = dict(nf=nf, nv=tot_v, nt=tot_t, bbox=[bmin, bmax], surfaces=surfs_out)
    out.update(meta)
    return out


def build_calm_john_component(packer, t_calm):
    calm_m = bhg.build()
    MH, NH = bhg.MH, bhg.NH
    V_raw = calm_m["V"]
    ring_V = V_raw[:MH * NH].reshape(MH, NH, 3)
    bot_pole = V_raw[MH * NH]
    top_pole = V_raw[MH * NH + 1]

    verts_c, uvs_c, tris_c = [], [], []
    cols = NH + 1
    for j in range(MH):
        vv_uv = (MH - 1 - j) / float(MH - 1)
        for k in range(cols):
            verts_c.append(ring_V[j, k % NH])
            uvs_c.append((k / float(NH), vv_uv))
    i_bot = len(verts_c)
    verts_c.append(bot_pole)
    uvs_c.append((0.5, 1.0))
    i_top = len(verts_c)
    verts_c.append(top_pole)
    uvs_c.append((0.5, 0.0))

    verts_c = np.asarray(verts_c, dtype=np.float32) * 2.2  # Crisp hero bust scale (~62 units tall)
    verts_c[:, 2] -= float(verts_c[:, 2].min())
    uvs_c = np.asarray(uvs_c, dtype=np.float32)

    def add_outward_tri(a, b, c, out_dir):
        fn = np.cross(verts_c[b] - verts_c[a], verts_c[c] - verts_c[a])
        if float(np.dot(fn, out_dir)) < 0.0:
            b, c = c, b
        tris_c.append((a, b, c))

    for j in range(MH - 1):
        rc = 0.5 * (ring_V[j].mean(axis=0) + ring_V[j + 1].mean(axis=0)) * 2.2
        rc[2] = 0.5 * (verts_c[j * cols : (j + 1) * cols, 2].mean() + verts_c[(j + 1) * cols : (j + 2) * cols, 2].mean())
        for k in range(NH):
            a = j * cols + k
            b, d = a + 1, (j + 1) * cols + k
            c = d + 1
            cen = 0.25 * (verts_c[a] + verts_c[b] + verts_c[c] + verts_c[d])
            add_outward_tri(a, b, c, cen - rc)
            add_outward_tri(a, c, d, cen - rc)
    for k in range(NH):
        add_outward_tri(k, k + 1, i_bot, np.array([0.0, 0.0, -1.0], dtype=np.float32))
        top_row = (MH - 1) * cols
        add_outward_tri(top_row + k, top_row + k + 1, i_top, np.array([0.0, 0.0, +1.0], dtype=np.float32))

    tris_c = np.asarray(tris_c, dtype=np.int32)
    norms_c = np.zeros_like(verts_c)
    fn_all = np.cross(verts_c[tris_c[:, 1]] - verts_c[tris_c[:, 0]], verts_c[tris_c[:, 2]] - verts_c[tris_c[:, 0]])
    for c_i in range(3):
        np.add.at(norms_c, tris_c[:, c_i], fn_all)
    for j in range(MH):
        i0, i1 = j * cols, j * cols + NH
        sn = norms_c[i0] + norms_c[i1]
        norms_c[i0], norms_c[i1] = sn, sn
    norms_c /= np.maximum(np.linalg.norm(norms_c, axis=1, keepdims=True), 1e-8)

    mat = dict(tex=t_calm, metallic=0.05, roughness=0.58, spec=0.28)
    s_enc = encode_surface(packer, "calm_john_head", "progs/jw_air_calm", uvs_c, tris_c, verts_c[None, ...], norms_c[None, ...], mat)
    bmin = verts_c.min(axis=0).round(2).tolist()
    bmax = verts_c.max(axis=0).round(2).tolist()
    return dict(
        id="calm_john",
        cat="comp",
        badge="3D HEAD · DEADPAN JOHN",
        title="Deadpan Calm Lush-Hair 3D John Wave Head",
        file="jw_air_calm (3D Cylindrical Bust)",
        desc="3D sculpted calm, lush-bearded John Wave portrait head reconstructed from front & back studio photos—serves as the unbothered aviator co-pilot, tail-gunner & backward Chinook face!",
        nf=1,
        nv=len(verts_c),
        nt=len(tris_c),
        bbox=[bmin, bmax],
        surfaces=[s_enc],
        clips=[dict(id="static", label="🗿 3D Bust Mesh (Frame 0)", start=0, count=1, fps=10.0, lie=True)],
    )


def build_megaman_bar_component(packer, t_chr, t_whl):
    parts = mmg.build_megaman_payload_parts()
    nf = 16
    sc = 6.5
    z_lift = mmg.MM_WHEEL_R * sc

    # Surface 1: Chrome Bullet Shaft + TIG Cross-Axle + Cotter-Pin Hub Hardware
    chr_v_frames, chr_n_frames = [], []
    whl_v_frames, whl_n_frames = [], []
    chr_uv, chr_tri = None, None
    whl_uv, whl_tri = None, None

    for fi in range(nf):
        ang = math.radians(-360.0 * (fi / float(nf)))
        cy, sy = math.cos(ang), math.sin(ang)
        R_spin = np.array([[cy, 0.0, -sy], [0.0, 1.0, 0.0], [sy, 0.0, cy]], dtype=np.float32)

        # Chrome parts
        sb_c = bsv.SurfBuilder("chrome_bar", "progs/mmw_chrome_axle")
        sb_c.add_mesh_part(parts["bar_axle"], scale=sc, offset=(0.0, 0.0, z_lift))
        sb_c.add_mesh_part(parts["wheel_hw_l"], scale=sc, R=R_spin, offset=(0.0, +mmg.MM_WHEEL_Y * sc, z_lift))
        sb_c.add_mesh_part(parts["wheel_hw_r"], scale=sc, R=R_spin, offset=(0.0, -mmg.MM_WHEEL_Y * sc, z_lift))
        vc, nc, uc, tc = sb_c.finalize_static()
        chr_v_frames.append(vc)
        chr_n_frames.append(nc)
        if chr_uv is None:
            chr_uv, chr_tri = uc, tc

        # Wheel parts
        sb_w = bsv.SurfBuilder("dish_tires", "progs/mmw_wheel")
        sb_w.add_mesh_part(parts["wheel_l"], scale=sc, R=R_spin, offset=(0.0, +mmg.MM_WHEEL_Y * sc, z_lift))
        sb_w.add_mesh_part(parts["wheel_r"], scale=sc, R=R_spin, offset=(0.0, -mmg.MM_WHEEL_Y * sc, z_lift))
        vw, nw, uw, tw = sb_w.finalize_static()
        whl_v_frames.append(vw)
        whl_n_frames.append(nw)
        if whl_uv is None:
            whl_uv, whl_tri = uw, tw

    all_vc = np.stack(chr_v_frames, axis=0)
    all_nc = np.stack(chr_n_frames, axis=0)
    all_vw = np.stack(whl_v_frames, axis=0)
    all_nw = np.stack(whl_n_frames, axis=0)

    s1 = encode_surface(packer, "chrome_bullet_bar", "progs/mmw_chrome_axle", chr_uv, chr_tri, all_vc, all_nc,
                        dict(tex=t_chr, metallic=0.88, roughness=0.16, spec=0.96))
    s2 = encode_surface(packer, "white_dish_tires", "progs/mmw_wheel", whl_uv, whl_tri, all_vw, all_nw,
                        dict(tex=t_whl, metallic=0.15, roughness=0.52, spec=0.42))

    pts0 = np.vstack([all_vc[0], all_vw[0]])
    bmin = pts0.min(axis=0).round(2).tolist()
    bmax = pts0.max(axis=0).round(2).tolist()
    return dict(
        id="megaman_bar",
        cat="comp",
        badge="HERO PAYLOAD · MEGA MAN BAR",
        title="The Mega Man Chrome Bar & Pneumatic Dish Tires",
        file="mmw_geometry (High-Detail 3D Rig)",
        desc="Precision-lathed gleaming chrome bullet shaft, TIG-welded cross-axle, zinc hex nuts, yellow cotter pins, and 5-ribbed pneumatic rubber tires on concave white stamped-steel dish rims!",
        nf=nf,
        nv=s1["nv"] + s2["nv"],
        nt=s1["nt"] + s2["nt"],
        bbox=[bmin, bmax],
        surfaces=[s1, s2],
        clips=[
            dict(id="spin", label="⚙ Spinning Dish Tires (16f)", start=0, count=16, fps=15.0, lie=True),
            dict(id="static", label="🗿 Parked Frame 0", start=0, count=1, fps=10.0, lie=True),
        ],
    )


def build_pinklady_component(packer, t_pink):
    npz = np.load(os.path.join(HERE, "out", "skyveh", "pinklady3d.npz"))
    v_base = npz["verts"].astype(np.float32)
    n_base = npz["norms"].astype(np.float32)
    uv_arr = npz["uvs"].astype(np.float32)
    tri_arr = npz["tris"].astype(np.int32)

    nf = 16
    sc = 1.65
    z_off = -float(v_base[:, 2].min()) * sc

    v_frames, n_frames = [], []
    for fi in range(nf):
        ph = 2.0 * math.pi * (fi / float(nf))
        vp, np_ = bsv.deform_pinklady(
            v_base, n_base,
            arm_wave_deg=14.0 * math.sin(ph),
            arm_fore_deg=6.0 * math.cos(ph),
            pod_breath=0.05 * math.sin(ph * 2.0),
            pod_bob=0.9 * math.sin(ph),
            ribbon_back=5.5 + 3.0 * math.sin(ph * 2.0),
            ribbon_sway=4.2 * math.cos(ph),
        )
        vp = vp * sc
        vp[:, 2] += z_off
        v_frames.append(vp)
        n_frames.append(np_)

    all_v = np.stack(v_frames, axis=0)
    all_n = np.stack(n_frames, axis=0)
    s_enc = encode_surface(packer, "pinklady_3d", "progs/skyveh_pinklady", uv_arr, tri_arr, all_v, all_n,
                           dict(tex=t_pink, metallic=0.06, roughness=0.50, spec=0.36))
    bmin = all_v[0].min(axis=0).round(2).tolist()
    bmax = all_v[0].max(axis=0).round(2).tolist()
    return dict(
        id="pinklady3d",
        cat="comp",
        badge="VIDEO 3 · 3D RECONSTRUCTION",
        title="3D Hot-Pink Buoyant Twin-Sphere V-Arm Lady",
        file="pinklady3d.npz (3,702v / 3,800t)",
        desc="Full watertight 3D figure reconstructed from Video 3 with articulated V-arms, breathing twin buoyant spheres, gold choker, and fluttering hot-pink tie-ribbons!",
        nf=nf,
        nv=s_enc["nv"],
        nt=s_enc["nt"],
        bbox=[bmin, bmax],
        surfaces=[s_enc],
        clips=[
            dict(id="cruise", label="💖 V-Arm Wave & Flutter (16f)", start=0, count=16, fps=12.0, lie=False),
            dict(id="lie", label="🗿 Neutral Pose (Frame 0)", start=0, count=1, fps=10.0, lie=True),
        ],
    )


def main():
    print("1. Packing voice horn clips & shared sRGB textures...", flush=True)
    sounds = pack_voice_soundboard()
    packer = ArenaPacker()

    # Core Aircraft & Sky-Vehicle sRGB Textures
    t_jw_scream = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_scream_srgb.png"), max_dim=1024, jpeg_q=90)
    t_jw_calm   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_calm_srgb.png"), max_dim=768, jpeg_q=90)
    t_jw_fed    = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fedora_srgb.png"), max_dim=512, jpeg_q=92)
    t_jw_wave   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_wave_srgb.png"), max_dim=256, jpeg_q=90)
    t_jw_fx     = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fx_srgb.png"), max_dim=256, force_png=True)

    t_bigears   = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "bigears_srgb.png"), max_dim=1024, jpeg_q=89)
    t_pinklady  = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "pinklady3d_srgb.png"), max_dim=1024, jpeg_q=90)
    t_sky_fx    = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "skyveh_fx_srgb.png"), max_dim=256, force_png=True)

    t_mm_chr    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png"), max_dim=512, jpeg_q=91)
    t_mm_whl    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"), max_dim=512, jpeg_q=91)
    t_mm_gun    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_gun_metal.png"), max_dim=768, jpeg_q=88)
    t_mm_gauge  = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_gauge_glow.png"), max_dim=256, jpeg_q=90)
    t_mm_hand   = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_hand.png"), max_dim=512, jpeg_q=88)
    t_mm_fx     = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_fx.png"), max_dim=256, force_png=True)
    t_mm_scan   = packer.add_tex_file(os.path.join(PROGS, "megaman.png"), max_dim=768, jpeg_q=88, lift=1.65)

    # Driveable Vehicle Atlases + Glow Maps
    t_van       = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_van_atlas.png"), max_dim=1024, jpeg_q=88)
    t_van_gl    = packer.add_tex_file(os.path.join(PROGS, "veh_van_tex_glow.png"), max_dim=512, jpeg_q=85)
    t_van_glass = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_van_glass.png"), max_dim=256, jpeg_q=88)

    t_truck     = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_truck_atlas.png"), max_dim=768, jpeg_q=87)
    t_truck_gl  = packer.add_tex_file(os.path.join(PROGS, "veh_truck_tex_glow.png"), max_dim=512, jpeg_q=85)
    t_sedan     = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_sedan_atlas.png"), max_dim=768, jpeg_q=87)
    t_sedan_gl  = packer.add_tex_file(os.path.join(PROGS, "veh_sedan_tex_glow.png"), max_dim=512, jpeg_q=85)
    t_coupe     = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_coupe_atlas.png"), max_dim=768, jpeg_q=87)
    t_coupe_gl  = packer.add_tex_file(os.path.join(PROGS, "veh_coupe_tex_glow.png"), max_dim=512, jpeg_q=85)

    # Arsenal / Mod Props Textures
    t_jp_dark   = packer.add_tex_file(os.path.join(PROGS, "jetpack_dark.png"), max_dim=256)
    t_jp_dial   = packer.add_tex_file(os.path.join(PROGS, "jetpack_dial.png"), max_dim=256)
    t_jp_glow   = packer.add_tex_file(os.path.join(PROGS, "jetpack_glow.png"), max_dim=256)
    t_jp_hose   = packer.add_tex_file(os.path.join(PROGS, "jetpack_hose.png"), max_dim=256)
    t_jp_metal  = packer.add_tex_file(os.path.join(PROGS, "jetpack_metal.png"), max_dim=256)
    t_jp_plume  = packer.add_tex_file(os.path.join(PROGS, "jetpack_plume.png"), max_dim=256, force_png=True)
    t_jp_strap  = packer.add_tex_file(os.path.join(PROGS, "jetpack_strap.png"), max_dim=256)
    t_jp_tank   = packer.add_tex_file(os.path.join(PROGS, "jetpack_tank.png"), max_dim=256)
    t_jp_wing   = packer.add_tex_file(os.path.join(PROGS, "jetpack_wing.png"), max_dim=256)

    t_lp_body   = packer.add_tex_file(os.path.join(PROGS, "v_laptop_body.png"), max_dim=512, lift=1.55)
    t_lp_keys   = packer.add_tex_file(os.path.join(PROGS, "v_laptop_keys.png"), max_dim=512, lift=1.45)
    t_lp_scr    = packer.add_tex_file(os.path.join(PROGS, "v_laptop_scr.png"), max_dim=512, lift=1.25)
    t_lp_hand   = packer.add_tex_file(os.path.join(PROGS, "v_laptop_hand.png"), max_dim=512, lift=1.35)
    t_lp_zap    = packer.add_tex_file(os.path.join(PROGS, "v_laptop_zap.png"), max_dim=256, force_png=True)

    t_ns_body   = packer.add_tex_file(os.path.join(PROGS, "netsend_pc_body.png"), max_dim=512, lift=1.45)
    t_ns_disk   = packer.add_tex_file(os.path.join(PROGS, "netsend_disk.png"), max_dim=256, lift=1.40)
    t_ns_scr    = packer.add_tex_file(os.path.join(PROGS, "netsend_s_lol0.png"), max_dim=256, lift=1.20)
    t_ns_leds   = packer.add_tex_file(os.path.join(PROGS, "netsend_leds.png"), max_dim=128)

    t_gg_black  = packer.add_tex_file(os.path.join(PROGS, "googun_black.png"), max_dim=128, lift=1.45)
    t_gg_dark   = packer.add_tex_file(os.path.join(PROGS, "googun_dark.png"), max_dim=128, lift=1.45)
    t_gg_decal  = packer.add_tex_file(os.path.join(PROGS, "googun_decal.png"), max_dim=128, lift=1.35)
    t_gg_foam   = packer.add_tex_file(os.path.join(PROGS, "googun_foam.png"), max_dim=128, lift=1.30)
    t_gg_hole   = packer.add_tex_file(os.path.join(PROGS, "googun_hole.png"), max_dim=128, lift=1.35)
    t_gg_metal  = packer.add_tex_file(os.path.join(PROGS, "googun_metal.png"), max_dim=128, lift=1.55)
    t_gg_rubber = packer.add_tex_file(os.path.join(PROGS, "googun_rubber.png"), max_dim=128, lift=1.45)
    t_gg_tank   = packer.add_tex_file(os.path.join(PROGS, "googun_tank.png"), max_dim=128, lift=1.30)

    t_horse     = packer.add_tex_file(os.path.join(PROGS, "gw_horse.png"), max_dim=256, lift=1.40)
    t_rock      = packer.add_tex_file(os.path.join(PROGS, "gw_rock.png"), max_dim=256, lift=1.35)

    models_out = []

    # ==================== CATEGORY 1: 3 JOHN WAVE x MEGA MAN AIRCRAFT (72f) ====================
    print("2. Packing 3 John Wave x Mega Man 72-frame Aircraft...", flush=True)
    jw_mats = {
        "progs/jw_air_scream": dict(tex=t_jw_scream, metallic=0.05, roughness=0.62, spec=0.28),
        "progs/jw_air_calm":   dict(tex=t_jw_calm,   metallic=0.05, roughness=0.60, spec=0.28),
        "progs/jw_air_fedora": dict(tex=t_jw_fed,    metallic=0.04, roughness=0.76, spec=0.24),
        "progs/jw_air_chrome": dict(tex=t_mm_chr,    metallic=0.88, roughness=0.17, spec=0.96),
        "progs/jw_air_wheel":  dict(tex=t_mm_whl,    metallic=0.16, roughness=0.52, spec=0.42),
        "progs/jw_air_wave":   dict(tex=t_jw_wave,   unlit=True),
        "progs/jw_air_fx":     dict(tex=t_jw_fx,     unlit=True, additive=True),
    }
    jw_clips = [
        dict(id="fly_cruise",      label="✈ Cruise (Jaw & Hair)",   start=0,  count=16, fps=12.0, lie=False),
        dict(id="fly_boost",       label="🔥 MAX Scream Boost",      start=16, count=16, fps=18.0, lie=False),
        dict(id="fly_barrel_roll", label="🌀 360° Barrel Roll!",     start=56, count=16, fps=16.0, lie=False, roll=True),
        dict(id="fly_hover",       label="🚁 VTOL Hover",            start=32, count=12, fps=10.0, lie=False),
        dict(id="lie_rest",        label="🛬 Landed / Snoring",      start=44, count=12, fps=8.0,  lie=True),
        dict(id="all",             label="🎬 All 72f",               start=0,  count=72, fps=13.0, lie=False),
    ]
    for vid, badge, title, fn_disp, desc in [
        ("jw_air_v1", "JW AIRCRAFT V1", 'F-69 "The Mouth-Breather" Biplane', "progs/jw_aircraft.md3 (jw_air_v1.md3)",
         "100% Screaming-Head-Free Red-Fedora Edition! Giant Gold-Spring Bobblehead John wearing a jauntily cocked Crimson-Red Felt Fedora, spinning Gold Tire-Monocle, pumping 'Rock' eyebrow, bullfrog cheeks, lit Mega-Man Cigar puffing 3D 'John Wave' smoke rings, Dalí mustache tire-props, flapping bird-wings with Mini-Red-Fedora Henchmen Johns & Cuckoo-Clock Man-Bun John!"),
        ("jw_air_v2", "JW AIRCRAFT V2", 'SR-99 "In-One-Ear" Rocket Jet', "progs/jw_air_v2.md3",
         "Mach-5 Mega-Man Rocket spearing out of Giant John's mouth and skewering him ear-to-ear with monster Beats-by-Mega-Man tilt-rotor headphone tires + twin screaming ramjets!"),
        ("jw_air_v3", "JW AIRCRAFT V3", 'CH-99 "The Hair-icopter" Chinook', "progs/jw_air_v3.md3",
         "100% Screaming-Head-Free Push-Me-Pull-You flying broomstick: Front, Rear & Midship Tire-Shades Biker are ALL stoic Deadpan Lush-Hair Johns with twin Mega-Man Propeller-Beanie hair rotors!"),
    ]:
        models_out.append(pack_md3_model(
            packer, os.path.join(PROGS, f"{vid}.md3"), jw_mats,
            dict(id=vid, cat="jw_air", badge=badge, title=title, file=fn_disp, desc=desc, clips=jw_clips),
            bbox_frames=(0, 44),
        ))

    # ==================== CATEGORY 2: 4 COMBINED 4-VIDEO SKY-VEHICLES (56f) ====================
    print("3. Packing 4 Combined 4-Video 56-frame Sky-Vehicles...", flush=True)
    sky_mats = {
        "progs/skyveh_van":      dict(tex=t_van, glowTex=t_van_gl, metallic=0.14, roughness=0.42, spec=0.45),
        "progs/skyveh_bigears":  dict(tex=t_bigears,  metallic=0.05, roughness=0.62, spec=0.25),
        "progs/skyveh_pinklady": dict(tex=t_pinklady, metallic=0.06, roughness=0.52, spec=0.34),
        "progs/skyveh_chrome":   dict(tex=t_mm_chr,   metallic=0.78, roughness=0.18, spec=0.92),
        "progs/skyveh_wheel":    dict(tex=t_mm_whl,   metallic=0.12, roughness=0.64, spec=0.30),
        "progs/skyveh_fx":       dict(tex=t_sky_fx,   unlit=True, additive=True),
    }
    sky_clips = [
        dict(id="fly_cruise", label="✈ Sky Cruise",       start=0,  count=16, fps=12.0, lie=False),
        dict(id="fly_boost",  label="🔥 Sky Boost",       start=16, count=16, fps=18.0, lie=False),
        dict(id="fly_hover",  label="🚁 VTOL Hover",      start=32, count=12, fps=10.0, lie=False),
        dict(id="lie_rest",   label="🛬 Lying / Landed",  start=44, count=12, fps=8.0,  lie=True),
        dict(id="all",        label="🎬 All 56f",         start=0,  count=56, fps=12.0, lie=False),
    ]
    for vid, badge, title, desc in [
        ("skyveh_v1", "SKY-VEHICLE V1", "The Ear-nithopter Sky-Galleon",
         "Dirigible airship gondola with dorsal flapping giant ear-wings, 3D Pink Lady prow figurehead & forward chin chrome pitot-lance with tilting VTOL wheels."),
        ("skyveh_v2", "SKY-VEHICLE V2", "The Valkyrie V-22 Tilt-Rotor",
         "Heavy assault dropship with wingtip Osprey chrome nacelles spinning giant white-dish pneumatic-tire rotors, dorsal Atlas Pink Lady & Big-Ears dive-canards."),
        ("skyveh_v3", "SKY-VEHICLE V3", "The Podracer Sky-Chariot & Autogyro",
         "Screaming Big-Ears tractor pod towing the ProMaster chariot on twin chrome booms while Pink Lady holds an overhead twin-tire autogyro helicopter mast."),
        ("skyveh_v4", "SKY-VEHICLE V4", "The Biomech Mecha-Wyvern",
         "Apex sky-dragon with barn-doors flaring as white Beetle Elytra wing-shells, arched chrome dragon neck with Big-Ears head & scorpion tail-rotor stinger."),
    ]:
        models_out.append(pack_md3_model(
            packer, os.path.join(PROGS, f"{vid}.md3"), sky_mats,
            dict(id=vid, cat="sky_veh", badge=badge, title=title, file=f"progs/{vid}.md3", desc=desc, clips=sky_clips),
            bbox_frames=(0, 44),
        ))

    # ==================== CATEGORY 3: 8 SOURCE 3D HEADS & MEGA MAN COMPONENTS ====================
    print("4. Packing 8 Source 3D Heads, Mega Man Contraptions & Component Models...", flush=True)
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "johnhead3d.md3"),
        {"progs/johnhead3d": dict(tex=t_jw_scream, metallic=0.05, roughness=0.62, spec=0.28)},
        dict(
            id="johnhead3d", cat="comp", badge="3D HEAD · SCREAMING JOHN",
            title="Screaming John Wave 3D Head", file="progs/johnhead3d.md3",
            desc="Full 4,837-vertex 3D screaming John Wave head with wind-whipped mane curls and wide-open mouth—the flagship hull of the John Wave Aircraft!",
            clips=[dict(id="static", label="🗿 3D Head Mesh (Frame 0)", start=0, count=1, fps=10.0, lie=True)],
        ),
    ))
    models_out.append(build_calm_john_component(packer, t_jw_calm))
    models_out.append(build_megaman_bar_component(packer, t_mm_chr, t_mm_whl))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "megaman.md3"),
        {"progs/megaman": dict(tex=t_mm_scan, metallic=0.25, roughness=0.48, spec=0.45)},
        dict(
            id="megaman_scan", cat="comp", badge="VIDEO 1 · SCANNED MD3",
            title="Original Mega Man Projectile MD3", file="progs/megaman.md3",
            desc="The 16-frame spinning 3D projectile MD3 in progs/megaman.md3 with separated left/right wheel surfaces and central bar body.",
            clips=[
                dict(id="cruise", label="⚙ Spin Loop (16f)", start=0, count=16, fps=15.0, lie=True),
                dict(id="lie", label="🗿 Frame 0", start=0, count=1, fps=10.0, lie=True),
            ],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "v_megaman.md3"),
        {
            "progs/mmw_gun_metal":   dict(tex=t_mm_gun,   metallic=0.65, roughness=0.28, spec=0.78),
            "progs/mmw_chrome_axle": dict(tex=t_mm_chr,   metallic=0.88, roughness=0.17, spec=0.95),
            "progs/mmw_wheel":       dict(tex=t_mm_whl,   metallic=0.16, roughness=0.52, spec=0.42),
            "progs/mmw_gauge_glow":  dict(tex=t_mm_gauge, unlit=True),
            "progs/mmw_hand":        dict(tex=t_mm_hand,  metallic=0.05, roughness=0.65, spec=0.22),
            "progs/mmw_fx":          dict(tex=t_mm_fx,    unlit=True, additive=True),
        },
        dict(
            id="v_megaman", cat="comp", badge="3D WEAPON · 37 FRAMES",
            title="Mega-Slinger Launcher Viewmodel", file="progs/v_megaman.md3",
            desc="First-person 37-frame launcher cradle cradling the Mega-Man chrome bar & spinning white-dish tires with glowing pressure gauge and Ranger hands!",
            clips=[
                dict(id="all",   label="🎬 Full 37f Sequence", start=0,  count=37, fps=14.0, lie=False),
                dict(id="cruise",label="🔫 Idle Spin",         start=0,  count=8,  fps=10.0, lie=False),
                dict(id="boost", label="💥 Launch / Reload",   start=8,  count=24, fps=16.0, lie=False, roll=True),
            ],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "bigears.md3"),
        {"progs/bigears": dict(tex=t_bigears, metallic=0.05, roughness=0.62, spec=0.25)},
        dict(
            id="bigears", cat="comp", badge="VIDEO 4 · 3D HEAD",
            title="Giant-Eared Screaming 3D Head", file="progs/bigears.md3",
            desc="Watertight 4,562-vertex 3D head reconstructed from Video 4 featuring colossal outstretched ears that articulate as ornithopter wings on the Sky-Vehicles!",
            clips=[dict(id="static", label="🗿 3D Head Mesh (Frame 0)", start=0, count=1, fps=10.0, lie=True)],
        ),
    ))
    models_out.append(build_pinklady_component(packer, t_pinklady))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "jw_wave.md3"),
        {"progs/jw_wave": dict(tex=t_jw_wave, unlit=True)},
        dict(
            id="jw_wave", cat="comp", badge="3D FX · OCEAN SURF",
            title='Foamy "John Wave" Ocean Surf Ring', file="progs/jw_wave.md3",
            desc="960-triangle 3D curling Pacific tidal-wave crown ring used for John Wave's surf attacks, jet exhaust plumes, and helicopter rotor hurricanes!",
            clips=[dict(id="static", label="🌊 Surf Ring Mesh", start=0, count=1, fps=10.0, lie=True)],
        ),
    ))

    # ==================== CATEGORY 4: 9 MOD GROUND VEHICLES, WEAPONS & PROPS ====================
    print("5. Packing 9 Driveable Mod Ground Vehicles, 3D Weapons & Props...", flush=True)
    veh_clips = [
        dict(id="all",    label="🎬 All 36 Frames",      start=0,  count=36, fps=14.0, lie=True),
        dict(id="cruise", label="🚗 Straight Roll",      start=0,  count=12, fps=14.0, lie=True),
        dict(id="boost",  label="↩ Steer Left",          start=12, count=12, fps=14.0, lie=True),
        dict(id="roll",   label="↪ Steer Right",         start=24, count=12, fps=14.0, lie=True, roll=True),
    ]
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "veh_van.md3"),
        {
            "progs/veh_van_tex":   dict(tex=t_van, glowTex=t_van_gl, metallic=0.16, roughness=0.40, spec=0.48),
            "progs/veh_van_glass": dict(tex=t_van_glass, metallic=0.65, roughness=0.14, spec=0.90),
        },
        dict(
            id="veh_van", cat="arsenal", badge="VIDEO 2 · WALK-IN VAN",
            title="Walk-In Ram ProMaster Cargo Van", file="progs/veh_van.md3",
            desc="36-frame driveable white high-roof cargo van with walk-in rear barn doors, full cab/cargo interior, steering front wheels & emissive headlamps!",
            clips=veh_clips,
        ),
    ))
    for vid, badge, title, t_main, t_gl, desc in [
        ("veh_truck", "GROUND VEHICLE", "Driveable Pickup Truck", t_truck, t_truck_gl,
         "36-frame driveable Quake pickup truck with rolling & steering wheels, bed detail, and glowing headlights/taillights."),
        ("veh_sedan", "GROUND VEHICLE", "Driveable 4-Door Sedan", t_sedan, t_sedan_gl,
         "36-frame driveable street sedan with rolling & steering wheels and emissive lightmap."),
        ("veh_coupe", "GROUND VEHICLE", "Driveable Sports Coupe", t_coupe, t_coupe_gl,
         "36-frame fast two-door sports coupe with rolling & steering animations and emissive headlamps."),
    ]:
        models_out.append(pack_md3_model(
            packer, os.path.join(PROGS, f"{vid}.md3"),
            {f"progs/{vid}_tex": dict(tex=t_main, glowTex=t_gl, metallic=0.22, roughness=0.38, spec=0.55)},
            dict(id=vid, cat="arsenal", badge=badge, title=title, file=f"progs/{vid}.md3", desc=desc, clips=veh_clips),
        ))

    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "jetpack.md3"),
        {
            "progs/jetpack_dark":  dict(tex=t_jp_dark,  metallic=0.35, roughness=0.55, spec=0.35),
            "progs/jetpack_dial":  dict(tex=t_jp_dial,  unlit=True),
            "progs/jetpack_glow":  dict(tex=t_jp_glow,  unlit=True),
            "progs/jetpack_hose":  dict(tex=t_jp_hose,  metallic=0.15, roughness=0.65, spec=0.25),
            "progs/jetpack_metal": dict(tex=t_jp_metal, metallic=0.78, roughness=0.24, spec=0.88),
            "progs/jetpack_plume": dict(tex=t_jp_plume, unlit=True, additive=True),
            "progs/jetpack_strap": dict(tex=t_jp_strap, metallic=0.08, roughness=0.72, spec=0.20),
            "progs/jetpack_tank":  dict(tex=t_jp_tank,  metallic=0.55, roughness=0.32, spec=0.65),
            "progs/jetpack_wing":  dict(tex=t_jp_wing,  metallic=0.50, roughness=0.36, spec=0.60),
        },
        dict(
            id="jetpack", cat="arsenal", badge="FLIGHT GEAR · 16f",
            title="Twin-Turbine Rocket Jetpack", file="progs/jetpack.md3",
            desc="9-surface 16-frame wearable twin-tank rocket jetpack with pressure dial, braided hoses, harness straps, winglets & pulsing exhaust plumes!",
            clips=[dict(id="cruise", label="🔥 Thruster Burn (16f)", start=0, count=16, fps=15.0, lie=False)],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "v_laptop.md3"),
        {
            "progs/v_laptop_body": dict(tex=t_lp_body, metallic=0.35, roughness=0.45, spec=0.48),
            "progs/v_laptop_keys": dict(tex=t_lp_keys, metallic=0.15, roughness=0.55, spec=0.35),
            "progs/v_laptop_scr":  dict(tex=t_lp_scr,  unlit=True),
            "progs/v_laptop_hand": dict(tex=t_lp_hand, metallic=0.05, roughness=0.68, spec=0.22),
            "progs/v_laptop_zap":  dict(tex=t_lp_zap,  unlit=True, additive=True),
        },
        dict(
            id="v_laptop", cat="arsenal", badge="3D WEAPON · 34f",
            title="LTG Arc-Lightning Laptop Weapon", file="progs/v_laptop.md3",
            desc="34-frame weaponized laptop with individual keycaps, glowing display, typing hands & additive electric arc-lightning discharges!",
            clips=[dict(id="all", label="⚡ Type & Zap (34f)", start=0, count=34, fps=14.0, lie=False)],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "netsend_pc.md3"),
        {
            "progs/netsend_pc_body":  dict(tex=t_ns_body, metallic=0.15, roughness=0.58, spec=0.32),
            "progs/netsend_disk":     dict(tex=t_ns_disk, metallic=0.20, roughness=0.48, spec=0.38),
            "progs/netsend_scr_loop": dict(tex=t_ns_scr,  unlit=True),
            "progs/netsend_leds":     dict(tex=t_ns_leds, unlit=True),
        },
        dict(
            id="netsend_pc", cat="arsenal", badge="3D DEPLOYABLE · 50f",
            title="NetSend Retro CRT Desktop PC", file="progs/netsend_pc.md3",
            desc="50-frame animated beige retro CRT computer tower/monitor launching spinning floppy disks with blinking status LEDs!",
            clips=[dict(id="all", label="💾 Disk Shoot Loop (50f)", start=0, count=50, fps=15.0, lie=True)],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "v_googun.md3"),
        {
            "progs/googun_black":  dict(tex=t_gg_black,  metallic=0.25, roughness=0.50, spec=0.38),
            "progs/googun_dark":   dict(tex=t_gg_dark,   metallic=0.35, roughness=0.45, spec=0.45),
            "progs/googun_decal":  dict(tex=t_gg_decal,  metallic=0.15, roughness=0.50, spec=0.35),
            "progs/googun_foam":   dict(tex=t_gg_foam,   unlit=True),
            "progs/googun_hole":   dict(tex=t_gg_hole,   metallic=0.10, roughness=0.80, spec=0.10),
            "progs/googun_metal":  dict(tex=t_gg_metal,  metallic=0.72, roughness=0.28, spec=0.80),
            "progs/googun_rubber": dict(tex=t_gg_rubber, metallic=0.08, roughness=0.72, spec=0.22),
            "progs/googun_tank":   dict(tex=t_gg_tank,   unlit=True),
        },
        dict(
            id="v_googun", cat="arsenal", badge="3D WEAPON · 7f",
            title="Bio-Foam Goo Gun Viewmodel", file="progs/v_googun.md3",
            desc="8-surface pressurized bio-foam sprayer viewmodel with glowing tank, machined barrel & recoil animation.",
            clips=[dict(id="all", label="🧪 Fire Recoil (7f)", start=0, count=7, fps=12.0, lie=False)],
        ),
    ))
    models_out.append(pack_md3_model(
        packer, os.path.join(PROGS, "gw_horse.md3"),
        {
            "progs/gw_horse": dict(tex=t_horse, metallic=0.72, roughness=0.32, spec=0.78),
            "progs/gw_rock":  dict(tex=t_rock,  metallic=0.05, roughness=0.82, spec=0.18),
        },
        dict(
            id="gw_horse", cat="arsenal", badge="3D PROP · STATUE",
            title="Rearing Bronze Horse Statue", file="progs/gw_horse.md3",
            desc="3,692-triangle sculpted bronze horse monument rearing atop a rocky plinth.",
            clips=[dict(id="static", label="🗿 Statue Mesh", start=0, count=1, fps=10.0, lie=True)],
        ),
    ))

    print(f"   Total models packed: {len(models_out)}", flush=True)
    assert len(models_out) == 24, f"Expected 24 models, got {len(models_out)}"

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    print(f"   Binary arena: {len(raw_bytes)/1e6:.2f} MB raw -> {len(gz_bytes)/1e6:.2f} MB gzipped ({len(b64_gz)/1e6:.2f} MB b64)", flush=True)

    meta_obj = dict(
        sounds=sounds,
        textures=packer.tex_list,
        models=models_out,
    )
    meta_json = json.dumps(meta_obj, separators=(",", ":"))

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    assert "/*__META_JSON__*/" in tpl, "Missing /*__META_JSON__*/ in template!"
    assert "/*__BIN_GZ__*/" in tpl, "Missing /*__BIN_GZ__*/ in template!"
    html = tpl.replace("/*__META_JSON__*/", meta_json, 1).replace("/*__BIN_GZ__*/", b64_gz, 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"6. Wrote Master 3D Model Inspector HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
