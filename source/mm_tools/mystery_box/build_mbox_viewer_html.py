"""Builds G:\\Quake\\Combat\\BakersfieldQuake\\mystery_box.html:
A 100% self-contained, zero-dependency WebGL2 3D Weapon, Crystal-Ball 16-Vision Jukebox,
and Live Interactive Throw Range for the Mystery Box Quake Weapon (`v_mysterybox.md3`).
"""
import base64
import gzip
import io
import json
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
import md3lib

OUT_ROOT = os.path.join(MM_TOOLS, "out", "mystery_box")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
MD3_DIR = os.path.join(OUT_ROOT, "md3")
GLB_DIR = os.path.join(OUT_ROOT, "glb")
HTML_OUT = os.path.join(MOD_ROOT, "mystery_box.html")
REF_IMG = r"C:/Users/qxdc/.gemini/antigravity/brain/ad411f94-7510-45fc-a435-43ed7d928f93/.user_uploaded/media_1793446654453_888a2949.png"


def build_edges(tris):
    s = set()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u != v:
                s.add((min(int(u), int(v)), max(int(u), int(v))))
    return np.array(sorted(s), dtype=np.uint16)


def encode_tex(path):
    im = Image.open(path).convert("RGBA")
    bio = io.BytesIO()
    im.save(bio, "PNG", optimize=True)
    return dict(
        name=os.path.basename(path),
        uri="data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii"),
    )


def pack_md3(md3_path, arena, surf_tex_idx, surf_opts):
    m = md3lib.read(md3_path)
    nf = m["nframes"]

    def add_bytes(b):
        while len(arena) & 3:
            arena.append(0)
        off = len(arena)
        arena.extend(b)
        return [off, len(b)]

    surfs_out = []
    tot_v, tot_t = 0, 0
    pts_bounds = []

    for s in m["surfaces"]:
        sname = s["name"]
        nv = len(s["st"])
        nt = len(s["tris"])
        tot_v += nv
        tot_t += nt

        # Flip MD3 clockwise -> WebGL CCW!
        tris_ccw = np.array([(a, c, b) for a, b, c in s["tris"]], dtype=np.uint16)
        edges = build_edges(tris_ccw)
        uv = np.array(s["st"], dtype=np.float32)

        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            vp = np.array(vv, dtype=np.float32)
            if sname in ("man_hand", "box_glass") and fi == 0:
                pts_bounds.append(vp)
            pos_q[fi] = np.clip(np.round(vp * 64.0), -32768, 32767).astype(np.int16)
            na = np.array(nn, dtype=np.float32)
            nrm_q[fi] = np.clip(np.round(na * 127.0), -127, 127).astype(np.int8)

        opt = surf_opts[sname]
        surfs_out.append(dict(
            name=sname,
            nv=nv,
            nt=nt,
            ne=len(edges),
            tex=surf_tex_idx[sname],
            rough=opt.get("rough", 0.45),
            spec=opt.get("spec", 0.35),
            unlit=bool(opt.get("unlit", False)),
            blend=bool(opt.get("blend", False)),
            additive=bool(opt.get("additive", False)),
            twoSided=bool(opt.get("twoSided", True)),
            tint=opt.get("tint", [1.0, 1.0, 1.0]),
            tris=add_bytes(tris_ccw.tobytes()),
            edges=add_bytes(edges.tobytes()),
            uv=add_bytes(uv.tobytes()),
            pos=add_bytes(pos_q.tobytes()),
            nrm=add_bytes(nrm_q.tobytes()),
        ))

    pts_cat = np.vstack(pts_bounds)
    ctr = ((pts_cat.min(axis=0) + pts_cat.max(axis=0)) * 0.5).tolist()
    rad = float(np.linalg.norm(pts_cat - np.array(ctr), axis=1).max())
    return dict(
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        center=[round(x, 2) for x in ctr],
        radius=round(max(rad, 5.0), 2),
        surfaces=surfs_out,
    )


def main():
    tex_files = [
        "mbox_hand_web.png",
        "mbox_qmark.png",
        "mbox_ghost_3d.png",
        "mbox_ghost_spr.png",
        "mbox_glass.png",
        "mbox_fx.png",
    ]
    tex_list = [encode_tex(os.path.join(TEX_DIR, fn)) for fn in tex_files]
    tmap = {fn: i for i, fn in enumerate(tex_files)}

    surf_tex = {
        "man_hand":     tmap["mbox_hand_web.png"],
        "crystal_core": tmap["mbox_qmark.png"],
        "ghost_3d":     tmap["mbox_ghost_3d.png"],
        "ghost_spr":    tmap["mbox_ghost_spr.png"],
        "box_glass":    tmap["mbox_glass.png"],
        "box_qmark":    tmap["mbox_qmark.png"],
        "box_fx":       tmap["mbox_fx.png"],
    }
    surf_opts = {
        "man_hand":     dict(rough=0.52, spec=0.36, unlit=False, blend=False, additive=False, twoSided=False),
        "crystal_core": dict(rough=0.20, spec=0.00, unlit=True,  blend=True,  additive=False, twoSided=True),
        "ghost_3d":     dict(rough=0.20, spec=0.00, unlit=True,  blend=False, additive=True,  twoSided=True),
        "ghost_spr":    dict(rough=0.20, spec=0.00, unlit=True,  blend=False, additive=True,  twoSided=True),
        "box_glass":    dict(rough=0.08, spec=0.92, unlit=True,  blend=True,  additive=False, twoSided=True),
        "box_qmark":    dict(rough=0.12, spec=0.55, unlit=True,  blend=True,  additive=False, twoSided=False),
        "box_fx":       dict(rough=0.20, spec=0.00, unlit=True,  blend=False, additive=True,  twoSided=True),
    }

    arena = bytearray()

    m_vm = pack_md3(os.path.join(MD3_DIR, "v_mysterybox.md3"), arena, surf_tex, surf_opts)
    m_vm.update(dict(
        tab="🖐️ Held Weapon + Live Throw",
        file="progs/v_mysterybox.md3",
        fps=11.0,
        defaultPov=True,
        orbitCenter=[15.8, -4.6, -3.6],
        az=2.65,
        el=0.14,
        dist=1.55,
        floorZ=-18.0,
        clips=[
            dict(name="Crystal-Ball Idle (0-191)", start=0, end=191),
            dict(name="Fire: Grab·Glow·Throw (192-219)", start=192, end=219),
            dict(name="Full 220f Cycle (0-219)", start=0, end=219),
        ],
        presets=[
            ["1st-Person Quake POV", "pov", 0, 1],
            ["Side Levitation Gap", 2.15, 0.08, 1.48],
            ["3/4 Realistic Hand", 2.45, 0.22, 1.38],
            ["Front Crystal Window", 3.05, 0.14, 1.05],
        ],
    ))

    m_hero = pack_md3(os.path.join(MD3_DIR, "mysterybox_closeup.md3"), arena, surf_tex, surf_opts)
    m_hero.update(dict(
        tab="🔮 Crystal Ball Close-Up (16 Visions)",
        file="mysterybox_closeup.md3",
        fps=11.0,
        defaultPov=False,
        orbitCenter=[0.0, 0.0, 0.0],
        az=0.0,
        el=0.14,
        dist=2.45,
        floorZ=-18.0,
        clips=[
            dict(name="All 16 Visions Loop (0-191)", start=0, end=191),
        ],
        presets=[
            ["Direct Crystal Portal", 0.0, 0.10, 2.30],
            ["3/4 Rainbow Cube", 0.65, 0.28, 2.55],
            ["Deep Magnifying Zoom", 0.05, 0.06, 1.65],
            ["Top-Down Prism", 0.0, 1.25, 2.75],
        ],
    ))

    m_proj = pack_md3(os.path.join(MD3_DIR, "proj_mysterybox.md3"), arena, surf_tex, surf_opts)
    m_proj.update(dict(
        tab="☄️ Thrown Projectile",
        file="progs/proj_mysterybox.md3",
        fps=16.0,
        defaultPov=False,
        orbitCenter=[-3.0, 0.0, 0.0],
        az=0.68,
        el=0.22,
        dist=3.20,
        floorZ=-14.0,
        clips=[
            dict(name="Ballistic Flight & Comet (0-31)", start=0, end=31),
        ],
        presets=[
            ["3/4 Flight & Comet", 0.68, 0.22, 3.20],
            ["Side Comet Profile", -1.57, 0.10, 3.40],
            ["Head-On Incoming", 0.05, 0.12, 2.60],
        ],
    ))

    # Encode Reference Image thumbnail
    ref_im = Image.open(REF_IMG).convert("RGBA")
    rw = round(ref_im.width * (80.0 / ref_im.height))
    ref_im = ref_im.resize((rw, 80), Image.Resampling.LANCZOS)
    rbio = io.BytesIO()
    ref_im.save(rbio, "PNG", optimize=True)
    ref_uri = "data:image/png;base64," + base64.b64encode(rbio.getvalue()).decode("ascii")

    # Embed gzipped .GLB files for 1-click download
    glbs = {}
    for key, fn in (
        ("weapon",     "mystery_box_weapon.glb"),
        ("projectile", "mystery_box_projectile.glb"),
        ("closeup",    "mystery_box_closeup.glb"),
    ):
        p = os.path.join(GLB_DIR, fn)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            glbs[key] = dict(
                filename=fn,
                sizeKB=round(len(raw) / 1024.0, 1),
                gzB64=base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii"),
            )

    meta = json.load(open(os.path.join(OUT_ROOT, "mbox_meta.json"), encoding="utf-8"))
    gz_arena = gzip.compress(bytes(arena), compresslevel=9)

    payload = dict(
        refUri=ref_uri,
        binGz=base64.b64encode(gz_arena).decode("ascii"),
        textures=tex_list,
        models=[m_vm, m_hero, m_proj],
        meta=meta,
        glbs=glbs,
    )

    tpl = open(os.path.join(HERE, "mbox_viewer_template.html"), encoding="utf-8").read()
    assert "/*__MBOX_DATA__*/null" in tpl
    html = tpl.replace("/*__MBOX_DATA__*/null", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained {HTML_OUT} ({os.path.getsize(HTML_OUT) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
