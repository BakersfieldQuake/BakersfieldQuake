"""Builds source/gun_pose_vote/index.html: one page to place EVERY gun's first-person model and vote on it.

The models are the ones the game draws now (BakersfieldQuake, then quake15 + q15.pk3, then id1 paks, the same search order
the engine uses), embedded with their textures, so the page is one file.  python -I build_gun_pose_vote.py
The user's page output (gun_pose_votes.json) lists, per gun, a verdict, a note and the pose they set.  Pose maths are the
same as apply_viewmodel_edits.py (turn/scale about the centre of the frame-0 bounding box, then move; eye space x forward,
y left, z up), measured against the model file as shipped: it REPLACES the stock weapon_position_fully_adjustable_*_angle
tilt, which the page already includes in its starting pose."""
import base64
import gzip
import io
import json
import os
import re
import struct
import sys
import time
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
COMBAT = "G:/Quake/Combat/"
MOD = COMBAT + "BakersfieldQuake/"
OUT = MOD + "source/gun_pose_vote/index.html"

# ------------------------------------------------------------------ file lookup (mod dir, quake15 dir + pk3, id1 paks)
ZIPS = [zipfile.ZipFile(COMBAT + "quake15/q15.pk3")]


def pak_index(path):
    f = open(path, "rb")
    ident, ofs, ln = struct.unpack("<4sii", f.read(12))
    assert ident == b"PACK"
    f.seek(ofs)
    raw = f.read(ln)
    ent = {}
    for i in range(0, ln, 64):
        nm = raw[i:i + 56].split(b"\0")[0].decode("latin1").lower()
        ent[nm] = struct.unpack("<ii", raw[i + 56:i + 64])
    return f, ent


PAKS = [pak_index(COMBAT + "id1/pak1.pak"), pak_index(COMBAT + "id1/pak0.pak")]


def find(rel):
    """bytes of a game file by its relative path, or None."""
    for d in (MOD, COMBAT + "quake15/"):
        p = d + rel
        if os.path.isfile(p):
            return open(p, "rb").read()
        if d.endswith("quake15/"):
            for z in ZIPS:
                try:
                    return z.read(rel)
                except KeyError:
                    pass
    for f, ent in PAKS:
        if rel.lower() in ent:
            pos, sz = ent[rel.lower()]
            f.seek(pos)
            return f.read(sz)
    return None


def png_data(raw, maxdim=512):
    im = Image.open(io.BytesIO(raw))
    im = im.convert("RGBA")
    if max(im.size) > maxdim:
        k = maxdim / max(im.size)
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def tex_for(shader):
    for ext in (".png", ".tga", ".jpg"):
        raw = find(shader + ext)
        if raw:
            return png_data(raw)
    return None


# ------------------------------------------------------------------ the roster
def md3_info(raw):
    nframes = struct.unpack("<i", raw[76:80])[0]
    nsurf = struct.unpack("<i", raw[84:88])[0]
    o = struct.unpack("<i", raw[100:104])[0]
    surfs = []
    for _ in range(nsurf):
        name = raw[o + 4:o + 68].split(b"\0")[0].decode()
        oSh, oEnd = struct.unpack("<ii", raw[o + 92:o + 96] + raw[o + 104:o + 108])
        shader = raw[o + oSh:o + oSh + 64].split(b"\0")[0].decode()
        surfs.append((name, shader))
        o += oEnd
    return nframes, surfs


def mdl_frames(raw):
    nskin, sw, sh, nv, nt, nf = struct.unpack("<6i", raw[48:72])
    o = 84
    for _ in range(nskin):
        g = struct.unpack("<i", raw[o:o + 4])[0]
        o += 4
        if g == 0:
            o += sw * sh
        else:
            n = struct.unpack("<i", raw[o:o + 4])[0]
            o += 4 + 4 * n + n * sw * sh
    o += nv * 12 + nt * 16
    names = []
    for _ in range(nf):
        t = struct.unpack("<i", raw[o:o + 4])[0]
        o += 4
        if t == 0:
            names.append(raw[o + 8:o + 24].split(b"\0")[0].decode())
            o += 24 + nv * 4
        else:
            n = struct.unpack("<i", raw[o:o + 4])[0]
            o += 4 + 8 + 4 * n
            for _ in range(n):
                names.append(raw[o + 8:o + 24].split(b"\0")[0].decode())
                o += 24 + nv * 4
    return names


FUN_CLIPS = [("idle", 0, 15, 10, 1), ("fire kick", 16, 18, 12, 0), ("gone", 19, 19, 1, 1), ("coming back", 20, 21, 6, 0)]
CLIPS = {
    "progs/v_megaman.md3": [("idle", 0, 15, 10, 1), ("fire (whole shot)", 16, 35, 20, 0), ("launch (frame 19)", 19, 19, 1, 1),
                            ("recoil + steam", 19, 24, 12, 0), ("reload lifts next one", 25, 35, 15, 0), ("empty rails", 36, 36, 1, 1)],
    "progs/v_googun.md3": [("idle", 0, 0, 1, 1), ("fire kick", 0, 6, 12, 0)],
    "progs/ltg_v3d.md3": [("idle", 0, 11, 10, 1), ("typing + lightning", 12, 33, 22, 0)],
}

# (id, name, where, file, tilt) - tilt = the stock weapon_position_fully_adjustable_<slot>_x_angle the game adds today
# (entity pitch is nose-down positive, so -4 means nose UP 4 degrees).  Slots that are re-centred by the game get 0.
GUNS = [
    ("googun", "Goo Gun", "shotgun slot", "progs/v_googun.md3", 4),
    ("shot2", "Super Shotgun", "super shotgun slot (stock Quake model)", "progs/v_shot2.mdl", 4),
    ("laptop", "Laptop Gun", "nailgun slot", "progs/ltg_v3d.md3", 0),
    ("milky", "Milky Gun", "super nailgun slot", "progs/v_milky.md3", 3),
    ("gl", "Grenade Launcher", "stock Quake model", "progs/v_rock.mdl", 0),
    ("rl", "Rocket Launcher", "stock Quake model", "progs/v_rock2.mdl", 0),
    ("lg", "Lightning Gun", "stock Quake model (the game keeps it dead centre)", "progs/v_light.mdl", 0),
    ("hammer", "Bonk Hammer", "the axe slot", "progs/v_hammer.mdl", 0),
    ("megaman", "Mega Man (Mega-Slinger)", "own weapon", "progs/v_megaman.md3", 0),
    ("robdob", "Rob Dob", "fun gun", "progs/v_robdob.mdl", 0),
    ("netsend", "NetSend", "fun gun (the PC screen is a separate model, not shown)", "progs/v_netsend.md3", 0),
    ("mbox", "Mystery Box", "fun gun", "progs/v_mysterybox.md3", 0),
    ("wheelman", "Wheelman Cannon", "fun gun", "progs/v_wewcannon.md3", 0),
    ("pickle", "Pickle Surprise", "fun gun (flat card, 120 skins; skin 0 shown)", "progs/v_pickle.md3", 0),
]

guns = []
for gid, label, where, rel, tilt in GUNS:
    raw = find(rel)
    if raw is None:
        print("MISSING", rel)
        continue
    g = dict(id=gid, label=label, where=where, file=rel, kind="mdl" if rel.endswith(".mdl") else "md3",
             tilt=tilt, b64=base64.b64encode(gzip.compress(raw, 9, mtime=0)).decode(), size=len(raw), tex={}, ext=None, skin={})
    if g["kind"] == "md3":
        n, surfs = md3_info(raw)
        skin = {}
        sk = find(rel + "_0.skin")
        if sk:
            for line in sk.decode("latin1").splitlines():
                if "," in line:
                    a, b = line.split(",", 1)
                    skin[a.strip()] = b.strip()
        g["skin"] = skin
        for name, shader in surfs:
            shader = skin.get(name, shader)
            if shader and shader not in g["tex"]:
                t = tex_for(shader)
                if t:
                    g["tex"][shader] = t
                else:
                    print("  no texture for", rel, name, shader)
        g["clips"] = CLIPS.get(rel) or (FUN_CLIPS if n == 22 else [("all frames", 0, n - 1, 10, 1)])
        g["frames"] = n
    else:
        names = mdl_frames(raw)
        n = len(names)
        ext = find(rel + "_0.png") or find(rel + "_0.tga") or find(rel + "_0.jpg")
        if ext:
            g["ext"] = png_data(ext)
        if rel == "progs/v_robdob.mdl":
            g["clips"] = [("bobbing in hand", 0, 7, 10, 1), ("gone (flying)", 8, 8, 1, 1)]
        else:
            g["clips"] = [("idle", 0, 0, 1, 1)] + ([("fire (frames 1-%d)" % (n - 1), 1, n - 1, 12, 0)] if n > 1 else []) + \
                         ([("all frames", 0, n - 1, 10, 1)] if n > 2 else [])
        g["frames"] = n
    g["clips"] = [[l, a, min(b, g["frames"] - 1), fps, lp] for l, a, b, fps, lp in g["clips"] if a < g["frames"]]
    g["sig"] = "%d:%d" % (g["size"], sum(raw[::97]) & 0xFFFFFF)
    print("%-10s %-3s %4d frames %6d KB  %d textures%s" % (gid, g["kind"], g["frames"], g["size"] // 1024, len(g["tex"]),
                                                             " +ext skin" if g["ext"] else ""))
    guns.append(g)

fov = 111.0
for line in open(MOD + "config.cfg", encoding="utf-8", errors="replace"):
    if line.startswith('"fov"') or line.startswith("fov "):
        fov = float(line.replace('"', " ").split()[1])
print("game fov", fov)

data = dict(
    guns=guns, fov=fov, build=str(int(time.time())),
    palette=base64.b64encode(find("gfx/palette.lmp")).decode(),
    anorm=json.load(open(COMBAT + "monster_page/anorm.json")),
)
t = open(HERE + "/gun_pose_vote.template.html", encoding="utf-8").read()
js = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(t.replace("__DATA__", js))
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
