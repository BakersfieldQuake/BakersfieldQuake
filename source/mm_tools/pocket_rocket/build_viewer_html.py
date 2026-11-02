"""Builds G:\\Quake\\Combat\\BakersfieldQuake\\pocket_rocket.html:
A 100% self-contained, zero-dependency WebGL2 3D Model Inspector & Interactive
Throw Range for the Pocket Rocket / Pink Torpedo throwable weapon & projectile.

Embeds:
  - Gzip-compressed binary geometry & vertex-normal animation arena for all 3 models:
      1. Thrown Projectile (In-Flight 3D + toggleable aerodynamic speed-lines)
      2. Held Throwable Weapon (Giant 3D Right Hand + Miniature Woman, 36 frames)
      3. Unobstructed 3D Character Turnaround (4 pose clips, 32 frames)
  - All 7 brand-new high-res PNG textures as data: URIs
  - Embedded .GLB binaries for 1-click export right from the browser
"""
import base64
import gzip
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
sys.path.insert(0, MM_TOOLS)
import md3lib

OUT_ROOT = os.path.join(MM_TOOLS, "out", "pocket_rocket")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
MD3_DIR = os.path.join(OUT_ROOT, "md3")
GLB_DIR = os.path.join(OUT_ROOT, "glb")
HTML_OUT = os.path.join(MOD_ROOT, "pocket_rocket.html")


def build_edges(tris):
    s = set()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u != v:
                s.add((min(u, v), max(u, v)))
    arr = np.array(sorted(s), dtype=np.uint16)
    return arr


def encode_texture(path, label, max_dim=1024):
    im = Image.open(path)
    im.load()
    w0, h0 = im.size
    has_alpha = im.mode == "RGBA" and np.array(im.getchannel("A")).min() < 250
    if max(w0, h0) > max_dim:
        sc = max_dim / float(max(w0, h0))
        im = im.resize((round(w0 * sc), round(h0 * sc)), Image.LANCZOS)
    buf = io.BytesIO()
    if has_alpha:
        im.convert("RGBA").save(buf, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=92, optimize=True)
        mime = "image/jpeg"
    uri = f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return dict(name=os.path.basename(path), label=label, w=w0, h=h0, alpha=bool(has_alpha), uri=uri)


def pack_md3(md3_path, bin_arena, tex_idx_by_surf, surf_opts):
    m = md3lib.read(md3_path)
    nf = m["nframes"]

    def add_bytes(b):
        while len(bin_arena) & 3:
            bin_arena.append(0)
        off = len(bin_arena)
        bin_arena.extend(b)
        return [off, len(b)]

    surfs_out = []
    tot_v, tot_t = 0, 0
    all_pts = []

    for s in m["surfaces"]:
        sname = s["name"]
        nv = len(s["st"])
        nt = len(s["tris"])
        tot_v += nv
        tot_t += nt

        # Convert MD3 clockwise back to standard WebGL CCW!
        tris_ccw = np.array([(a, c, b) for a, b, c in s["tris"]], dtype=np.uint16)
        edges = build_edges(tris_ccw)
        uv = np.array(s["st"], dtype=np.float32)

        # Quantize positions to int16 (1/64 unit) & normals to int8 ([-127..127]) for ultra-fast compact WebGL2 upload!
        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            vp = np.array(vv, dtype=np.float32)
            if not surf_opts.get(sname, {}).get("additive"):
                all_pts.append(vp)
            pos_q[fi] = np.clip(np.round(vp * 64.0), -32768, 32767).astype(np.int16)
            np_arr = np.array(nn, dtype=np.float32)
            nrm_q[fi] = np.clip(np.round(np_arr * 127.0), -127, 127).astype(np.int8)

        opt = surf_opts.get(sname, {})
        surfs_out.append(dict(
            name=sname,
            nv=nv,
            nt=nt,
            ne=len(edges),
            tex=tex_idx_by_surf[sname],
            rough=opt.get("rough", 0.55),
            spec=opt.get("spec", 0.35),
            additive=bool(opt.get("additive", False)),
            unlit=bool(opt.get("unlit", False)),
            twoSided=bool(opt.get("twoSided", False)),
            isVfx=bool(opt.get("isVfx", False)),
            tris=add_bytes(tris_ccw.tobytes()),
            edges=add_bytes(edges.tobytes()),
            uv=add_bytes(uv.tobytes()),
            pos=add_bytes(pos_q.tobytes()),
            nrm=add_bytes(nrm_q.tobytes()),
        ))

    pts_cat = np.vstack(all_pts)
    mn = pts_cat.min(axis=0).tolist()
    mx = pts_cat.max(axis=0).tolist()
    center = ((pts_cat.min(axis=0) + pts_cat.max(axis=0)) * 0.5).tolist()
    radius = float(np.linalg.norm(pts_cat - np.array(center), axis=1).max())

    return dict(
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        mins=[round(x, 2) for x in mn],
        maxs=[round(x, 2) for x in mx],
        center=[round(x, 2) for x in center],
        radius=round(radius, 2),
        surfaces=surfs_out,
    )


def main():
    tex_specs = [
        ("tex_skin.png",       "Character Face, Cleavage & Hands (1024×1024)"),
        ("tex_hair.png",       "Center-Parted Champagne Blonde Hair (1024×1024)"),
        ("tex_pink_top.png",   "Hot-Pink Plunging Tie-Front Cardigan (1024×1024)"),
        ("tex_jeans.png",      "Indigo Skinny Jeans & Stitched Pockets (1024×1024)"),
        ("tex_sneakers.png",   "Hot-Pink Laced Sneakers & Treads (512×512)"),
        ("tex_giant_hand.png", "Giant 1st-Person Hand, Palm Lines & Nails (1024×1024)"),
        ("tex_speedlines.png", "Aerodynamic Slipstream Speed-Lines (512×256 RGBA)"),
    ]
    tex_list = []
    tex_map = {}
    for fn, lbl in tex_specs:
        tex_map[fn] = len(tex_list)
        tex_list.append(encode_texture(os.path.join(TEX_DIR, fn), lbl))

    surf_tex = {
        "char_skin": tex_map["tex_skin.png"],
        "char_hair": tex_map["tex_hair.png"],
        "char_pink_top": tex_map["tex_pink_top.png"],
        "char_jeans": tex_map["tex_jeans.png"],
        "char_sneakers": tex_map["tex_sneakers.png"],
        "giant_hand": tex_map["tex_giant_hand.png"],
        "speedlines": tex_map["tex_speedlines.png"],
    }
    surf_opts = {
        "char_skin":     dict(rough=0.46, spec=0.38),
        "char_hair":     dict(rough=0.34, spec=0.58, twoSided=True),
        "char_pink_top": dict(rough=0.62, spec=0.26, twoSided=True),
        "char_jeans":    dict(rough=0.74, spec=0.18),
        "char_sneakers": dict(rough=0.48, spec=0.36),
        "giant_hand":    dict(rough=0.52, spec=0.32),
        "speedlines":    dict(additive=True, unlit=True, twoSided=True, isVfx=True),
    }

    arena = bytearray()
    m_proj = pack_md3(os.path.join(MD3_DIR, "pocket_rocket_proj.md3"), arena, surf_tex, surf_opts)
    m_proj.update(dict(
        id="projectile",
        tab="🚀 Thrown Projectile",
        title="Pocket Rocket — Thrown Flying Projectile",
        badge="PROJECTILE · 16 FRAMES",
        file="pocket_rocket_proj.md3 / pocket_rocket_projectile.glb",
        fps=12,
        az=0.68,
        el=0.18,
        dist=1.85,
        floorZ=-16.0,
        role="In-flight projectile hurled from the player's hand: flies horizontally (+X) chest-first with arched laughing head, billowing blonde hair, fluttering pink bow ribbons, swept-wing arms, blue skinny jeans, hot-pink sneakers & slipstream speed-lines.",
        clips=[
            dict(name="Skydiver Torpedo Flight (Loop)", frames=list(range(0, 16))),
        ],
        presets=[
            ["Front-3/4 Glide", 0.68, 0.18, 1.85],
            ["Side Torpedo Profile", -1.57, 0.06, 1.75],
            ["Rear-3/4 Hair & Jeans", -2.42, 0.28, 1.85],
            ["Head-On Nosecone", 0.0, 0.08, 1.65],
            ["Top-Down Wingspan", -1.57, 1.28, 2.05],
        ],
    ))

    m_weap = pack_md3(os.path.join(MD3_DIR, "v_pocket_rocket.md3"), arena, surf_tex, surf_opts)
    m_weap.update(dict(
        id="weapon",
        tab="🖐️ Held Weapon + Throw Test",
        title="Pocket Rocket — Held Hand Weapon & Live Throw Simulator",
        badge="VIEWMODEL · 36 FRAMES",
        file="v_pocket_rocket.md3 / pocket_rocket_weapon.glb",
        fps=11,
        pov=True,
        defaultPov=True,
        az=2.92,
        el=0.14,
        dist=1.75,
        floorZ=-17.0,
        role="First-person articulated giant right hand gripping the miniature character around her jeans waist (showing 3D knuckles & manicured fingernails). Press THROW (or Spacebar) to uncurl all 5 digits wide open and launch the live 3D projectile downrange!",
        clips=[
            dict(name="Idle: Hands on Hips (Video 1)", frames=list(range(0, 12))),
            dict(name="Excited Wave: 'Weee!' (Video 2)", frames=list(range(12, 24))),
            dict(name="Wind-Up & Open-Hand Throw (Video 3)", frames=list(range(24, 36))),
            dict(name="Full Showcase Cycle", frames=list(range(0, 36))),
        ],
        presets=[
            ["1st-Person POV", "pov", 0, 1],
            ["Front Grip & Nails", 3.08, 0.08, 1.55],
            ["3/4 Hand & Palm", 2.35, 0.20, 1.75],
            ["Back of Character", 0.35, 0.18, 1.75],
        ],
    ))

    m_char = pack_md3(os.path.join(MD3_DIR, "pocket_rocket_char.md3"), arena, surf_tex, surf_opts)
    m_char.update(dict(
        id="character",
        tab="💃 3D Character Turnaround",
        title="Pocket Rocket — Unobstructed 3D Character Mesh",
        badge="TURNAROUND · 32 FRAMES",
        file="pocket_rocket_char.md3 / pocket_rocket_character.glb",
        fps=10,
        az=0.38,
        el=0.12,
        dist=2.05,
        floorZ=-26.0,
        role="Full 360° unobstructed inspection of the newly sculpted 25-bone rigged 3D character mesh without the giant hand—inspect facial expression, layered blonde hair, plunging tie-front cardigan, seamless bifurcated skinny jeans & laced sneakers.",
        clips=[
            dict(name="Hands-on-Hips Idle", frames=list(range(0, 8))),
            dict(name="Joyful Dual-Arm Wave", frames=list(range(8, 16))),
            dict(name="Ready-to-Fly Spread", frames=list(range(16, 24))),
            dict(name="Skydiver Flight Pose", frames=list(range(24, 32))),
        ],
        presets=[
            ["Front 3/4 Hero", 0.38, 0.12, 2.05],
            ["Face & Bust Close-Up", 0.18, 0.16, 1.05],
            ["Side Silhouette", -1.57, 0.08, 2.05],
            ["Back Hair & Jeans Pockets", 3.05, 0.12, 2.05],
        ],
    ))

    # Also embed gzipped .GLB files for 1-click download from the HTML inspector!
    glb_b64 = {}
    for key, fn in (
        ("projectile", "pocket_rocket_projectile.glb"),
        ("weapon",     "pocket_rocket_weapon.glb"),
        ("character",  "pocket_rocket_character.glb"),
    ):
        p = os.path.join(GLB_DIR, fn)
        if os.path.exists(p):
            raw_glb = open(p, "rb").read()
            glb_b64[key] = dict(
                filename=fn,
                sizeKB=round(len(raw_glb) / 1024.0, 1),
                gzB64=base64.b64encode(gzip.compress(raw_glb, compresslevel=9)).decode("ascii"),
            )

    gz_arena = gzip.compress(bytes(arena), compresslevel=9)
    payload = dict(
        binGz=base64.b64encode(gz_arena).decode("ascii"),
        binLen=len(arena),
        textures=tex_list,
        models=[m_proj, m_weap, m_char],
        glbs=glb_b64,
    )

    tpl_path = os.path.join(HERE, "viewer_template.html")
    tpl = open(tpl_path, encoding="utf-8").read()
    assert "/*__PR_DATA__*/null" in tpl
    html = tpl.replace("/*__PR_DATA__*/null", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained {HTML_OUT} ({os.path.getsize(HTML_OUT) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
