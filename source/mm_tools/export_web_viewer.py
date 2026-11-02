"""Exports maps/<name>.bsp (+ .lit, textures, skybox, SimReady & LAN party props) for the browser walk-around viewer
(web_viewer/index.html, three.js).
python export_web_viewer.py <out dir> [map name, default bklan]
Writes into <out dir>:  map.json   draw groups, texture names, spawn and teleport spots, the hull-1 collision tree
                        map.bin    world vertices (float32 pos xyz, uv, lightmap uv), then each prop model once
                                   (float32 pos xyz, uv + uint32 triangles); placements are instances in map.json
                        lightmap.png, tex/*.png (textures, <=512 px; CRT strips at 1536x144), sky/*.jpg
Coordinates stay in Quake units, z up; the viewer turns them."""
import io
import json
import math
import os
import re
import shutil
import struct
import sys
import tempfile
import zipfile

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
STAGED = os.path.normpath(os.path.join(MOD, "..", "_bakersfield_dev", "staged_assets"))
sys.path.insert(0, HERE)
import md3lib  # noqa: E402

_PK3_PATH = os.path.join(MOD, "bakersfield.pk3")
_PK3 = zipfile.ZipFile(_PK3_PATH, "r") if os.path.exists(_PK3_PATH) else None
_PK3_NAMES = set(_PK3.namelist()) if _PK3 else set()


def mod_bytes(rel):
    rel_u = rel.replace("\\", "/")
    for base in (MOD, STAGED):
        disk = os.path.join(base, rel_u.replace("/", os.sep))
        if os.path.exists(disk):
            return open(disk, "rb").read()
    if rel_u in _PK3_NAMES:
        return _PK3.read(rel_u)
    return None


OUT = sys.argv[1]
NAME = sys.argv[2] if len(sys.argv) > 2 else "bklan"                       # bklan, orcom, bklan5
BSP = os.path.join(MOD, "maps", NAME + ".bsp")
LIT = os.path.join(MOD, "maps", NAME + ".lit")
SKIP = ("sky", "clip", "skip", "trigger")
TEXMAX = 512

d = open(BSP, "rb").read()
BSP2 = d[:4] == b"BSP2"                     # qbsp switches to BSP2 when the map outgrows BSP29 (wider fields)
assert BSP2 or struct.unpack("<i", d[:4])[0] == 29, d[:4]
lumps = [struct.unpack("<2i", d[4 + 8 * i: 12 + 8 * i]) for i in range(15)]
FACE, FACE_SZ = ("<iiiii4Bi", 28) if BSP2 else ("<hhihh4Bi", 20)
CLIP, CLIP_SZ = ("<iii", 12) if BSP2 else ("<ihh", 8)
EDGE, EDGE_SZ = ("<2I", 8) if BSP2 else ("<2H", 4)


def lump(i):
    o, n = lumps[i]
    return d[o:o + n]


entities = lump(0).decode("latin1")
planes = [struct.unpack("<4fi", lump(1)[i:i + 20]) for i in range(0, len(lump(1)), 20)]
verts = [struct.unpack("<3f", lump(3)[i:i + 12]) for i in range(0, len(lump(3)), 12)]
texinfo = [struct.unpack("<8f2i", lump(6)[i:i + 40]) for i in range(0, len(lump(6)), 40)]
faces = [struct.unpack(FACE, lump(7)[i:i + FACE_SZ]) for i in range(0, len(lump(7)), FACE_SZ)]
lighting = lump(8)
clipnodes = [struct.unpack(CLIP, lump(9)[i:i + CLIP_SZ]) for i in range(0, len(lump(9)), CLIP_SZ)]
edges = [struct.unpack(EDGE, lump(12)[i:i + EDGE_SZ]) for i in range(0, len(lump(12)), EDGE_SZ)]
surfedges = struct.unpack("<%di" % (len(lump(13)) // 4), lump(13))
models = [struct.unpack("<9f7i", lump(14)[i:i + 64]) for i in range(0, len(lump(14)), 64)]

tl = lump(2)
nmip = struct.unpack("<i", tl[:4])[0]
miptex = []
for i in range(nmip):
    o = struct.unpack("<i", tl[4 + 4 * i: 8 + 4 * i])[0]
    if o < 0:
        miptex.append(("", 16, 16))
        continue
    name, w, h = struct.unpack("<16s2I", tl[o:o + 24])
    miptex.append((name.split(b"\0")[0].decode("latin1"), w, h))

lit = open(LIT, "rb").read()[8:] if os.path.exists(LIT) else None


def ents():
    for m in re.finditer(r"\{([^}]*)\}", entities):
        yield dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1)))


# ------------------------------------------------------------------ lightmap atlas (shelf packing, 1 px border)
blocks = []
face_lm = {}
for fi, f in enumerate(faces):
    planenum, side, firstedge, numedges, ti, s0, s1, s2, s3, lightofs = f
    tex = miptex[texinfo[ti][8]][0]
    if tex.startswith(SKIP) or s0 == 255 or lightofs < 0:
        continue
    vec = texinfo[ti]
    pts = []
    for k in range(numedges):
        e = surfedges[firstedge + k]
        pts.append(verts[edges[e][0]] if e >= 0 else verts[edges[-e][1]])
    st = [(p[0] * vec[0] + p[1] * vec[1] + p[2] * vec[2] + vec[3], p[0] * vec[4] + p[1] * vec[5] + p[2] * vec[6] + vec[7]) for p in pts]
    mins = [math.floor(min(s[a] for s in st) / 16) for a in (0, 1)]
    maxs = [math.ceil(max(s[a] for s in st) / 16) for a in (0, 1)]
    w, h = maxs[0] - mins[0] + 1, maxs[1] - mins[1] + 1
    blocks.append((h, w, fi, mins))
blocks.sort(reverse=True)
AW = 4096 if sum(b[0] * b[1] for b in blocks) > 2048 * 1024 else 2048
x = y = shelf = 0
place = {}
for h, w, fi, mins in blocks:
    if x + w + 2 > AW:
        x, y, shelf = 0, y + shelf + 2, 0
    place[fi] = (x + 1, y + 1, w, h, mins)
    x += w + 2
    shelf = max(shelf, h)
AH = 1 << max(1, (y + shelf + 2 - 1).bit_length())
atlas = Image.new("RGB", (AW, AH), (255, 255, 255))
px = atlas.load()
for fi, (ax, ay, w, h, mins) in place.items():
    ofs = faces[fi][9]
    for v in range(h):
        for u in range(w):
            i = ofs + v * w + u
            c = (lit[3 * i], lit[3 * i + 1], lit[3 * i + 2]) if lit else (lighting[i],) * 3
            px[ax + u, ay + v] = c
    # copy the edge texels into the border so bilinear filtering doesn't bleed
    for v in range(-1, h + 1):
        for u in (-1, w):
            px[ax + u, ay + v] = px[ax + min(max(u, 0), w - 1), ay + min(max(v, 0), h - 1)]
    for u in range(0, w):
        for v in (-1, h):
            px[ax + u, ay + v] = px[ax + u, ay + min(max(v, 0), h - 1)]


def lm_sample(fi, s, t):
    """Lightmap colour (0..1) of face fi at texture coords s, t."""
    ax, ay, w, h, mins = place[fi]
    u = min(max(int(round(s / 16 - mins[0])), 0), w - 1)
    v = min(max(int(round(t / 16 - mins[1])), 0), h - 1)
    return [c / 255 for c in px[ax + u, ay + v]]


# ------------------------------------------------------------------ world + bmodel faces, grouped by texture
groups = {}
world_faces = []
bmodels = [0] + [int(e["model"][1:]) for e in ents()
                 if e.get("model", "").startswith("*") and not e.get("classname", "").startswith("trigger")]   # triggers are invisible, not solid
for mi in bmodels:
    m = models[mi]
    firstface, numfaces = m[14], m[15]
    world_faces += range(firstface, firstface + numfaces)
for fi in world_faces:
    planenum, side, firstedge, numedges, ti, s0, s1, s2, s3, lightofs = faces[fi]
    vec = texinfo[ti]
    tex, tw, th = miptex[vec[8]]
    if tex.startswith(SKIP):
        continue
    pts = []
    for k in range(numedges):
        e = surfedges[firstedge + k]
        pts.append(verts[edges[e][0]] if e >= 0 else verts[edges[-e][1]])
    g = groups.setdefault(tex, [])
    rows = []
    for p in pts:
        s = p[0] * vec[0] + p[1] * vec[1] + p[2] * vec[2] + vec[3]
        t = p[0] * vec[4] + p[1] * vec[5] + p[2] * vec[6] + vec[7]
        if fi in place:
            ax, ay, w, h, mins = place[fi]
            lu, lv = (s / 16 - mins[0] + 0.5 + ax) / AW, (t / 16 - mins[1] + 0.5 + ay) / AH
        else:
            lu, lv = 0.5 / AW, 0.5 / AH               # white corner texel: unlit faces stay full bright
        rows.append((p[0], p[1], p[2], s / tw, t / th, lu, lv))
    for k in range(1, len(rows) - 1):
        g += [rows[0], rows[k + 1], rows[k]]           # Quake winds faces clockwise; three wants counter-clockwise


# ------------------------------------------------------------------ props (misc_model & LAN MD3s), lit from the floor under them
floor_faces = []
for fi in world_faces:
    pl = planes[faces[fi][0]]
    nz = -pl[2] if faces[fi][1] else pl[2]
    if nz > 0.7 and fi in place:
        planenum, side, firstedge, numedges = faces[fi][:4]
        pts = []
        for k in range(numedges):
            e = surfedges[firstedge + k]
            pts.append(verts[edges[e][0]] if e >= 0 else verts[edges[-e][1]])
        floor_faces.append((fi, pts))


def inside(pts, x, y):
    c = False
    for i in range(len(pts)):
        x1, y1 = pts[i][:2]
        x2, y2 = pts[i - 1][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def light_at(x, y, z):
    best, bz = None, -1e9
    for fi, pts in floor_faces:
        fz = sum(p[2] for p in pts) / len(pts)
        if bz < fz <= z + 2 and inside(pts, x, y):
            best, bz = fi, fz
    if best is None:
        return [0.6, 0.6, 0.6]
    vec = texinfo[faces[best][4]]
    return lm_sample(best, x * vec[0] + y * vec[1] + bz * vec[2] + vec[3], x * vec[4] + y * vec[5] + bz * vec[6] + vec[7])


models_used = {}                                          # mdl_key -> list of surfaces (shader, verts, st, tris)
GAME_MODELS = {"misc_vehicle_truck": ("progs/veh_truck.md3", 1), "misc_vehicle_sedan": ("progs/veh_sedan.md3", 1),
               "misc_vehicle_van": ("progs/veh_van.md3", 1), "misc_vehicle_coupe": ("progs/veh_coupe.md3", 1),
               "misc_vehicle_hdtruck": ("progs/veh_hdtruck.md3", 1), "misc_vehicle_schoolbus": ("progs/veh_schoolbus.md3", 1),
               "misc_vehicle_gtcar": ("progs/veh_gtcar.md3", 1), "misc_vehicle_johnbird": ("progs/john_bird_head.md3", 1.0),
               "bk_trashcan": ("progs/bklan/trashcan.md3", 1.0),
               "prop_daniel_table": ("progs/daniel_table.md3", 1.0), "prop_daniel_webcam": ("progs/daniel_webcam.md3", 1.0)}
LAN_MON_SKINS = {0: "scr_q3a1", 1: "scr_cs1", 2: "scr_win98a", 3: "scr_q3a2", 4: "scr_cs2", 5: "scr_win98b", 6: "scr_dead"}
LAN_ANIM_SCREENS = {"scr_q3a1": (8, 7.0), "scr_q3a2": (8, 7.0), "scr_cs1": (8, 8.0), "scr_cs2": (8, 6.0),
                    "scr_win98a": (8, 4.0), "scr_win98b": (8, 3.0)}
LAN_UNLIT_TEX = set(LAN_ANIM_SCREENS) | {"scr_pc2uv"}


def model_index(path, skin_tex=None):
    key = f"{path}@{skin_tex}" if skin_tex else path
    if key not in models_used:
        disk = os.path.join(MOD, path.replace("/", os.sep))
        if os.path.exists(disk):
            mdl = md3lib.read(disk)
        else:
            raw = mod_bytes(path)
            assert raw is not None, f"Missing model: {path}"
            with tempfile.NamedTemporaryFile(suffix=".md3", delete=False) as tf:
                tf.write(raw)
                tmp_p = tf.name
            try:
                mdl = md3lib.read(tmp_p)
            finally:
                os.unlink(tmp_p)
        surfs = []
        for s in mdl["surfaces"]:
            stex = s["shader"].split("/")[-1]
            if skin_tex and (s.get("name") == "screen" or stex.startswith("scr_")):
                stex = skin_tex
            surfs.append((stex, s["frames"][0][0], s["st"], s["tris"]))
        models_used[key] = surfs
    return list(models_used).index(key)


instances = []
for e in ents():
    cls = e.get("classname")
    skin_tex = None
    if cls == "misc_model":
        path, sc = e["mdl"], float(e.get("scale", 1))
        yaw = float(e.get("angles", "0 0 0").split()[1])
    elif cls in GAME_MODELS:
        path, sc = GAME_MODELS[cls]
        yaw = float(e["angles"].split()[1]) if "angles" in e else float(e.get("angle", 0))
    elif cls == "misc_lan_monitor":
        v = max(1, min(4, int(float(e.get("cnt", 1)))))
        sk = max(0, min(6, int(float(e.get("skin", 0)))))
        path, sc, skin_tex = f"progs/bklan/lan_mon{v}.md3", 1.0, LAN_MON_SKINS.get(sk, "scr_q3a1")
        yaw = float(e["angles"].split()[1]) if "angles" in e else float(e.get("angle", 0))
    elif cls == "misc_lan_pc":
        v = max(1, min(4, int(float(e.get("cnt", 1)))))
        path, sc = f"progs/bklan/lan_pc{v}.md3", 1.0
        yaw = float(e["angles"].split()[1]) if "angles" in e else float(e.get("angle", 0))
    elif cls == "misc_lan_chair":
        v = max(1, min(4, int(float(e.get("cnt", 1)))))
        path, sc = f"progs/bklan/lan_chair{v}.md3", 1.0
        yaw = float(e["angles"].split()[1]) if "angles" in e else float(e.get("angle", 0))
    elif cls == "misc_lan_table":
        v = max(1, min(5, int(float(e.get("cnt", 1)))))
        path, sc = ("progs/bklan/lan_table4s.md3" if v == 5 else f"progs/bklan/lan_table{v}.md3"), 1.0
        yaw = float(e["angles"].split()[1]) if "angles" in e else float(e.get("angle", 0))
    else:
        continue
    ox, oy, oz = (float(v) for v in e["origin"].split())
    instances.append({"m": model_index(path, skin_tex), "o": [ox, oy, oz], "yaw": yaw,
                      "s": sc, "light": [round(c, 3) for c in light_at(ox, oy, oz + 8)]})

# bklan3's movers (bklan_movers.qc), for the viewer to animate: cruisers follow their bk_route chain
movers = []
_by_name = {e.get("targetname"): e for e in ents() if e.get("classname") == "bk_route"}
for e in ents():
    cls = e.get("classname")
    if cls == "bk_cruiser":
        pink = e.get("cnt", "1") != "2"
        pts, nm = [], e.get("target")
        while nm in _by_name and len(pts) < 200:
            r = _by_name[nm]
            pts.append([float(v) for v in r["origin"].split()] + [float(r.get("speed", 1))])
            nm = r.get("target")
            if nm == e.get("target"):
                break
        o = [float(v) for v in e["origin"].split()]
        movers.append({"m": model_index("progs/pink_supercar.md3" if pink else "progs/skyveh_v3.md3"), "kind": "route",
                       "start": o, "pts": pts, "speed": 560 if pink else 300, "light": [round(c, 3) for c in light_at(o[0], o[1], o[2] + 8)]})
props = {tex for surfs in models_used.values() for tex, _, _, _ in surfs}
# shader names that are not image files (model skins point at scripts/*.shader entries): the shader's first image
SHADER_MAP = {}
for _fn in os.listdir(os.path.join(MOD, "scripts")):
    if _fn.endswith(".shader"):
        for _m in re.finditer(r"^(progs/\S+)\s*\{(.*?)^\}", open(os.path.join(MOD, "scripts", _fn), encoding="latin1").read(), re.S | re.M):
            _img = re.search(r"\b(?:map|animmap\s+[\d.]+)\s+(progs/\S+)", _m.group(2))
            if _img:
                SHADER_MAP.setdefault(_m.group(1).split("/")[-1], _img.group(1))


# ------------------------------------------------------------------ hull 1 (player) collision tree
used_hulls = {mi: models[mi][10] for mi in bmodels}       # headnode[1]

# ------------------------------------------------------------------ jump pads and teleporters (trigger_push / trigger_teleport)
triggers = []
_all = list(ents())
for e in _all:
    cls = e.get("classname", "")
    if cls not in ("trigger_push", "trigger_teleport") or not e.get("model", "").startswith("*"):
        continue
    m = models[int(e["model"][1:])]
    t = {"min": list(m[0:3]), "max": list(m[3:6])}
    if cls == "trigger_push":
        if "angles" in e:
            p, yw, _r = (math.radians(float(v)) for v in e["angles"].split())
            fw = [math.cos(p) * math.cos(yw), math.cos(p) * math.sin(yw), -math.sin(p)]
        else:
            fw = [0, 0, 1 if float(e.get("angle", -1)) == -1 else -1]
        t["push"] = [c * float(e.get("speed", 1000)) * 10 for c in fw]
    else:
        d = next((x for x in _all if x.get("targetname") == e.get("target") and x.get("classname") == "info_teleport_destination"), None)
        if d is None:
            continue
        o = [float(v) for v in d["origin"].split()]
        t["tp"] = [o[0], o[1], o[2] + 27, float(d.get("angle", 0))]
    triggers.append(t)

# ------------------------------------------------------------------ spawn + teleport spots
spots = json.load(open(os.path.join(HERE, "out", "maps", NAME + ".spots.json")))   # written by make_<name>.py

# ------------------------------------------------------------------ write
os.makedirs(os.path.join(OUT, "tex"), exist_ok=True)
os.makedirs(os.path.join(OUT, "sky"), exist_ok=True)
atlas.save(os.path.join(OUT, "lightmap.png"))


def safe(name):
    return name.replace("{", "fence_").replace("*", "star_")


def find_prop_tex(tex, suffix=""):
    stem = tex[:-4] if tex.lower().endswith((".png", ".jpg", ".tga")) else tex
    for ext in (".png", ".jpg", ".tga"):
        for rel in (
            "progs/bklan/" + stem + suffix + ext,
            "progs/fox/" + stem + suffix + ext,
            "progs/" + stem + suffix + ext,
            "textures/" + stem + suffix + ext,
            SHADER_MAP[stem] + suffix + ext if stem in SHADER_MAP else "",
        ):
            if rel:
                b = mod_bytes(rel)
                if b is not None:
                    return b
    return None


meta = {"world": [], "spots": spots, "lightmap": [AW, AH],
        "frame": {"bklan": [-110, 225], "bklan2": [-110, 225], "bklan3": [-110, 225], "bklan4": [-110, 225], "bklan5": [-110, 225], "fox": [220, -118], "orcom": [38, 26]}.get(NAME, [0, 0]),      # generator origin (ft): dev overlay shows map feet
        "triggers": triggers,
        "built": __import__("time").strftime("%Y-%m-%d %H:%M", __import__("time").localtime(os.path.getmtime(os.path.join(MOD, "maps", NAME + ".bsp"))))}
blob = bytearray()
for tex, rows in sorted(groups.items()):
    meta["world"].append({"tex": safe(tex), "alpha": tex.startswith("{"), "offset": len(blob) // 4, "count": len(rows),
                          "glow": mod_bytes("textures/" + tex + "_glow.png") is not None})
    blob += struct.pack("<%df" % (7 * len(rows)), *[v for r in rows for v in r])
meta["models"] = []
for path, surfs in models_used.items():
    mm = []
    for tex, vv, st, tris in surfs:
        off = len(blob) // 4
        blob += struct.pack("<%df" % (5 * len(vv)), *[c for v, t in zip(vv, st) for c in (v[0], v[1], v[2], t[0], t[1])])
        ioff = len(blob) // 4
        blob += struct.pack("<%dI" % (3 * len(tris)), *[i for t in tris for i in t])
        sd = {"tex": tex, "glow": find_prop_tex(tex, "_glow") is not None,
              "offset": off, "verts": len(vv), "ioffset": ioff, "icount": 3 * len(tris)}
        if tex in LAN_UNLIT_TEX:
            sd["unlit"] = True
        if tex in LAN_ANIM_SCREENS:
            sd["anim"] = list(LAN_ANIM_SCREENS[tex])
        mm.append(sd)
    meta["models"].append({"name": path.split("@")[0].split("/")[-1], "surfaces": mm})
meta["instances"] = instances
meta["movers"] = movers
meta["planes"] = [[round(p[0], 6), round(p[1], 6), round(p[2], 6), round(p[3], 3), p[4]] for p in planes]
meta["clipnodes"] = clipnodes
meta["hulls"] = list(used_hulls.values())
open(os.path.join(OUT, "map.bin"), "wb").write(blob)
json.dump(meta, open(os.path.join(OUT, "map.json"), "w"), separators=(",", ":"))


def copy_tex(src, dst):
    im = Image.open(io.BytesIO(src) if isinstance(src, (bytes, bytearray)) else src)
    im.thumbnail((TEXMAX, TEXMAX), Image.LANCZOS)
    im.save(dst)


for tex in groups:
    for suffix in ("", "_glow"):
        raw = mod_bytes("textures/" + tex + suffix + ".png")
        if raw is None:
            alt = os.path.join(HERE, "out", "tex_orig", tex + suffix + ".png")
            if os.path.exists(alt):
                raw = open(alt, "rb").read()
        if tex == "*teleport" and not suffix:                                # id's teleporter field lives in the wad only
            raw = open(os.path.join(HERE, "star_teleport.png"), "rb").read()
        if raw is not None:
            copy_tex(raw, os.path.join(OUT, "tex", safe(tex) + suffix + ".png"))
for tex in props:
    if tex in LAN_ANIM_SCREENS:
        nf, _ = LAN_ANIM_SCREENS[tex]
        frames = []
        for fi in range(nf):
            fb = mod_bytes(f"progs/bklan/{tex}_{fi}.png")
            assert fb is not None, f"Missing CRT frame progs/bklan/{tex}_{fi}.png"
            fim = Image.open(io.BytesIO(fb)).convert("RGB").resize((192, 144), Image.LANCZOS)
            fim = ImageEnhance.Brightness(fim).enhance(1.0 / 0.56)
            frames.append(fim)
        strip = Image.new("RGB", (192 * nf, 144))
        for fi, fim in enumerate(frames):
            strip.paste(fim, (192 * fi, 0))
        strip.save(os.path.join(OUT, "tex", tex + ".png"), optimize=True)
        continue
    for suffix in ("", "_glow"):
        _raw = find_prop_tex(tex, suffix)
        if _raw is not None:
            dst_p = os.path.join(OUT, "tex", tex + suffix + ".png")
            if not suffix and tex == "scr_pc2uv":
                im = Image.open(io.BytesIO(_raw)).convert("RGB")
                ImageEnhance.Brightness(im).enhance(1.0 / 0.56).save(dst_p, optimize=True)
            elif not suffix and tex.startswith(("t_mon", "t_pc", "t_chair", "t_table", "scr_dead")):
                im = Image.open(io.BytesIO(_raw)).convert("RGB")
                ImageEnhance.Brightness(im).enhance(1.0 / 0.52).save(dst_p, optimize=True)
            else:
                copy_tex(_raw, dst_p)
if NAME in ("bklan3", "bklan4", "bklan5", "fox"):                          # the 2026-11-01 sunny sky: drawn for three's cube layout
    import build_bklan_sky  # noqa: E402
    build_bklan_sky.web_faces(os.path.join(OUT, "sky"))
else:
    for side in ("rt", "lf", "up", "dn", "ft", "bk"):
        sb = mod_bytes("gfx/env/bklan_%s.png" % side)
        if sb is not None:
            sky = Image.open(io.BytesIO(sb)).convert("RGB")
            ImageEnhance.Brightness(sky).enhance(2.06).save(os.path.join(OUT, "sky", "%s.jpg" % side), quality=85)
        else:
            import build_bklan_sky  # noqa: E402
            build_bklan_sky.web_faces(os.path.join(OUT, "sky"))
            break
print("world %d tris in %d groups, %d prop models, %d placed, lightmap %dx%d, %.1f MB geometry" % (
    sum(len(r) for r in groups.values()) // 3, len(groups), len(models_used), len(instances), AW, AH, len(blob) / 1e6))
