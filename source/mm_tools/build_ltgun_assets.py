"""The laptop gun's art and sound, written straight into BakersfieldQuake (see ltgun.qc, ltgun_defs.qc):
  progs/ltg_view.md3         the held laptop at rest: the "hold" video, ping-ponged (shader animmap)
  progs/ltg_type_0..7.md3    the held laptop while it types: the "typing" video (dial-up, typing, HACKING 100%, glowing hot) sped up 3x
                             into 2 s. The engine runs animmap on the clock, so there are 8 copies of the film each starting at a
                             different frame; ltgun.qc (LtGun_Variant) picks the one that is on frame 0 when fire is pressed
  progs/ltg_head.md3         the big-eared head: 24 cards in 24 frames (earhead_sprite/), the frame picks the view (as the pickle)
  progs/ltg_aura.md3         a card of network cables and wi-fi signals round the head (additive, animated)
  progs/ltg_p.md3, ltg_g.md3 the laptop in other players' hands, and as a pickup (boxes with a little drawn skin)
  scripts/ltgun.shader, effectinfo.txt (ltg_trail / ltg_zap / ltg_boom between markers)
  sound/ltgun/canis.wav (the "Canis Lupus" clip), type.wav, send.wav, zap.wav, hit.wav, null.wav
Run it with the WindowsApps Python 3.13 (needs PIL, numpy), not -I:  python build_ltgun_assets.py
The held model's cut-outs are keyed from magenta; the numbers at the top are the ones ltgun_defs.qc shares."""
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

MOD = r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
SOUND = os.path.join(MOD, "sound", "ltgun")
IDLE_VIDEO = r"G:\Downloads\grok-video-fa7aa7e3-1343-4960-8449-4a32543014d2.mp4"          # 10 s: the laptop held, "BAKERSFIELD LAN"
TYPE_VIDEO = r"G:\Downloads\grok-video-fa7aa7e3-1343-4960-8449-4a32543014d2 (1).mp4"      # 6 s: dial-up, typing, hacking, overheating
CANIS_VIDEO = r"D:\Local\Video\canisdur.wmv"
CANIS_START = 0.85      # the clip opens with about 0.9 s of hiss before the first sound: the game's flying sound starts here
HEAD_DIR = os.path.join(MOD, "earhead_sprite")
if not os.path.isdir(HEAD_DIR):
    HEAD_DIR = os.path.join(os.path.dirname(MOD), "_bakersfield_dev", "earhead_sprite")

# shared with ltgun_defs.qc
ANIM_FPS = 42        # the typing film plays at 42 frames a second ...
ANIM_N = 48          # ... for 48 frames (1.14 s: the video's 6 s at 5.25x; "HACKING 100%" is at 0.8 s)
VARIANTS = 16         # copies of the film, each starting ANIM_N / VARIANTS frames later

IDLE_FROM, IDLE_LEN, IDLE_FPS = 4.6, 5.4, 8        # the first 4.5 s of the hold video have motion-ghost frames; use 4.6 s..10 s
TEX_W = 512          # held-laptop texture width
HELD_DIM = 0.72      # tuned for Zircon r_hdr_scenebrightness 1.45 + r_minlight 3
HEAD_DIM = 0.78      # restored from 0.26 (which was crushed for old sb=2.5 and made Eric heads near-black)
HEAD_W = 384
HEAD_H = 34.0        # the head card is this many units tall in the world
VIEW_W = 28.0        # the held card is this wide; its left edge sits at VIEW_LEFT (screen is about +/-27.8 wide, +/-15.6 high)
VIEW_LEFT = 1.0
VIEW_TOP = -1.0
VIEW_X = 14.0


# ----------------------------------------------------------------------------- the held model

def extract(video, vf, tmp, tag):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + vf[0] + ["-i", video, "-vf", vf[1], "-fps_mode", "vfr",
                    os.path.join(tmp, tag + "%03d.png")], check=True)
    return [Image.open(os.path.join(tmp, n)).convert("RGB") for n in sorted(os.listdir(tmp)) if n.startswith(tag)]


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def keyout(im):
    """magenta backdrop -> alpha. 'Magentaness' is min(R, B) - G: high on the backdrop, negative on skin, steel and the blue screen"""
    from scipy import ndimage as ndi
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(r, b) - g
    alpha = 1 - smooth(30, 80, m)
    # the pink rim: edge pixels take the colour of the nearest solid pixel inside the shape
    core = ndi.minimum_filter(alpha > 0.98, size=5)
    _, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
    edge = ~core
    rgb = a.copy()
    rgb[edge] = a[iy[edge], ix[edge]]
    # the video lights the laptop's rim magenta: near the edge, pull red and blue that stand above green back down
    dist = ndi.distance_transform_edt(alpha > 0.5)
    band = (dist < 16)[..., None]
    spill = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None)
    cap = rgb[..., 1] * 1.15 + 8                         # pink pixels near the edge go to a grey as bright as their green
    pink = band[..., 0] & (spill > 6)
    rgb = np.where(pink[..., None], np.stack([np.minimum(rgb[..., 0], cap), rgb[..., 1], np.minimum(rgb[..., 2], cap)], axis=-1), rgb)
    alpha = ndi.minimum_filter(alpha, size=2)         # one pixel tighter
    out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def held_textures():
    with tempfile.TemporaryDirectory() as tmp:
        idle = extract(IDLE_VIDEO, (["-ss", str(IDLE_FROM), "-t", str(IDLE_LEN)], "fps=%d" % IDLE_FPS), tmp, "i")
        film = extract(TYPE_VIDEO, ([], "fps=8"), tmp, "t")[:ANIM_N]
    assert len(film) == ANIM_N, "typing video gave %d frames, need %d" % (len(film), ANIM_N)
    cut_i = [keyout(f) for f in idle]
    cut_t = [keyout(f) for f in film]
    boxes = [c.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox() for c in cut_i + cut_t]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    aspect = (box[2] - box[0]) / float(box[3] - box[1])
    h = round(TEX_W / aspect)
    for old in os.listdir(PROGS):
        if old.startswith(("ltg_i_", "ltg_t_")):
            os.remove(os.path.join(PROGS, old))

    def save(c, name):
        c = c.crop(box).resize((TEX_W, h), Image.LANCZOS)
        px = np.asarray(c).astype(np.float32)
        px[..., :3] *= HELD_DIM
        Image.fromarray(px.astype(np.uint8), "RGBA").save(os.path.join(PROGS, name))
    for i, c in enumerate(cut_i):
        save(c, "ltg_i_%02d.png" % i)
    for i, c in enumerate(cut_t):
        save(c, "ltg_t_%02d.png" % i)
    print("held model: %d idle frames, %d typing frames, crop %s, aspect %.2f" % (len(cut_i), len(cut_t), box, aspect))
    return len(cut_i), aspect


def card(path, name, shader, hw, hh, dx, dy, dz):
    """one card in the Y/Z plane at x = dx, centred on (dy, dz), facing -X (the viewer, in the viewmodel); picture-left is +Y"""
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
    verts = [(dx, dy + hw, dz - hh), (dx, dy + hw, dz + hh), (dx, dy - hw, dz + hh), (dx, dy - hw, dz - hh)]
    surf = dict(name="card", shader=shader, tris=tris, st=st, frames=[(verts, [(-1.0, 0.0, 0.0)] * 4)])
    md3lib.write(path, dict(name=name, surfaces=[surf], nframes=1))


def held_models(idle_count, aspect):
    vw = VIEW_W
    vh = vw / aspect
    dy = VIEW_LEFT - vw / 2
    dz = VIEW_TOP - vh / 2
    card(os.path.join(PROGS, "ltg_view.md3"), "ltg_view", "progs/ltg_idle", vw / 2, vh / 2, VIEW_X, dy, dz)
    for k in range(VARIANTS):
        card(os.path.join(PROGS, "ltg_type_%d.md3" % k), "ltg_type_%d" % k, "progs/ltg_type_%d" % k, vw / 2, vh / 2, VIEW_X, dy, dz)
    print("held cards: %.1f x %.1f units, left edge %.1f, top %.1f" % (vw, vh, VIEW_LEFT, VIEW_TOP))


# ----------------------------------------------------------------------------- the head and its cables

def head_model():
    for old in os.listdir(PROGS):
        if old.startswith("ltg_head_"):
            os.remove(os.path.join(PROGS, old))
    first = Image.open(os.path.join(HEAD_DIR, "earhead_00.png"))
    h = round(HEAD_W * first.height / first.width)
    for i in range(24):
        im = Image.open(os.path.join(HEAD_DIR, "earhead_%02d.png" % i)).convert("RGBA").resize((HEAD_W, h), Image.LANCZOS)
        px = np.asarray(im).astype(np.float32)
        px[..., :3] *= HEAD_DIM
        Image.fromarray(px.astype(np.uint8), "RGBA").save(os.path.join(PROGS, "ltg_head_%02d.png" % i))
    hh = HEAD_H / 2
    hw = hh * first.width / first.height
    nothing = [(0.0, 0.0, 0.0)] * 4
    cardv = [(0.0, hw, -hh), (0.0, hw, hh), (0.0, -hw, hh), (0.0, -hw, -hh)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
    surfaces = []
    for k in range(24):
        frames = [(cardv if f == k else nothing, [(-1.0, 0.0, 0.0)] * 4) for f in range(24)]
        surfaces.append(dict(name="view%02d" % k, shader="progs/ltg_head_v%02d" % k, tris=tris, st=st, frames=frames))
    md3lib.write(os.path.join(PROGS, "ltg_head.md3"), dict(name="ltg_head", surfaces=surfaces, nframes=24))
    print("head: 24 views, card %.1f x %.1f" % (2 * hw, 2 * hh))


AURA_N = 8
AURA_SIZE = 256


def aura_textures():
    """network cables (blue, orange, yellow, green, white ethernet colours) streaming out behind a head, and wi-fi arcs"""
    for old in os.listdir(PROGS):
        if old.startswith("ltg_aura_"):
            os.remove(os.path.join(PROGS, old))
    colors = [(40, 120, 255), (255, 140, 30), (255, 230, 60), (60, 230, 90), (235, 235, 235), (200, 80, 255)]
    S = AURA_SIZE * 2
    rnd = random.Random(7)
    cables = []
    for i in range(14):
        a0 = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.35, 0.62)
        bend = rnd.uniform(-1.4, 1.4)
        cables.append((a0, r, bend, colors[i % len(colors)], rnd.uniform(3, 6)))
    for f in range(AURA_N):
        ph = f / float(AURA_N)
        im = Image.new("RGB", (S, S), (0, 0, 0))
        d = ImageDraw.Draw(im)
        for a0, r, bend, col, w in cables:
            pts = []
            for s in range(41):
                t = s / 40.0
                ang = a0 + bend * t + 2 * math.pi * ph * (1 if bend > 0 else -1) * 0.25
                rad = (0.12 + r * t) * S / 2 + 4 * math.sin(t * 9 + ph * 2 * math.pi)
                pts.append((S / 2 + rad * math.cos(ang), S / 2 + rad * math.sin(ang)))
            d.line(pts, fill=col, width=int(w * 2))
            ex, ey = pts[-1]
            d.rectangle([ex - 7, ey - 5, ex + 7, ey + 5], fill=(190, 190, 190))       # the RJ45 plug
        for k in range(3):                                                           # wi-fi arcs, pulsing outwards
            rr = (0.62 + 0.14 * ((k + ph * 3) % 3)) * S / 2
            fade = 1 - ((k + ph * 3) % 3) / 3.0
            col = tuple(int(c * (0.35 + 0.65 * fade)) for c in (90, 230, 255))
            for ang0 in (-45, 135):
                d.arc([S / 2 - rr, S / 2 - rr, S / 2 + rr, S / 2 + rr], ang0 - 40, ang0 + 40, fill=col, width=9)
        im = im.resize((AURA_SIZE, AURA_SIZE), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
        im.save(os.path.join(PROGS, "ltg_aura_%02d.png" % f))
    hw = 30.0
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
    cardv = [(0.0, hw, -hw), (0.0, hw, hw), (0.0, -hw, hw), (0.0, -hw, -hw)]
    md3lib.write(os.path.join(PROGS, "ltg_aura.md3"), dict(name="ltg_aura", surfaces=[dict(
        name="aura", shader="progs/ltg_aura", tris=tris, st=st, frames=[(cardv, [(-1.0, 0.0, 0.0)] * 4)])], nframes=1))
    print("aura: %d frames" % AURA_N)


# ----------------------------------------------------------------------------- the laptop in other hands / on the floor

def laptop_skin():
    """256x256: screen (top left), keyboard (top right), dark metal (the bottom half)"""
    im = Image.new("RGB", (256, 256), (28, 28, 30))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 127], fill=(12, 30, 110))
    d.rectangle([6, 6, 121, 22], fill=(30, 70, 190))
    try:
        f = ImageFont.truetype("arialbd.ttf", 24)
        f2 = ImageFont.truetype("arial.ttf", 9)
    except OSError:
        f = f2 = ImageFont.load_default()
    d.text((8, 8), "America Online", font=f2, fill=(255, 255, 255))
    d.text((12, 46), "BAKERSFIELD", font=f, fill=(255, 210, 40))
    d.text((40, 76), "LAN", font=f, fill=(255, 210, 40))
    d.rectangle([128, 0, 255, 127], fill=(24, 24, 26))
    for r in range(6):
        for c in range(14):
            x, y = 132 + c * 8.6, 8 + r * 15
            d.rectangle([x, y, x + 7, y + 12], fill=(60, 60, 64))
    d.rectangle([160, 100, 224, 122], fill=(40, 40, 44))
    rnd = random.Random(3)
    for _ in range(900):
        x, y = rnd.randrange(256), rnd.randrange(128, 256)
        v = rnd.randrange(14, 40)
        d.point((x, y), fill=(v, v, v + 2))
    px = np.asarray(im).astype(np.float32) * 0.6
    Image.fromarray(px.astype(np.uint8), "RGB").save(os.path.join(PROGS, "ltg_p.png"))


def box_mesh(x0, x1, y0, y1, z0, z1, faces, rot=None):
    """faces: name -> (u0, v0, u1, v1) in the skin; rot = function applied to each corner (the lid's hinge)"""
    p = lambda x, y, z: rot((x, y, z)) if rot else (x, y, z)
    q = {
        "top":    [p(x0, y1, z1), p(x1, y1, z1), p(x1, y0, z1), p(x0, y0, z1)],
        "bottom": [p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0)],
        "front":  [p(x1, y1, z0), p(x1, y0, z0), p(x1, y0, z1), p(x1, y1, z1)],
        "back":   [p(x0, y0, z0), p(x0, y1, z0), p(x0, y1, z1), p(x0, y0, z1)],
        "left":   [p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1)],
        "right":  [p(x1, y0, z0), p(x0, y0, z0), p(x0, y0, z1), p(x1, y0, z1)],
    }
    verts, st, tris = [], [], []
    for name, quad in q.items():
        u0, v0, u1, v1 = faces[name]
        b = len(verts)
        verts += quad
        st += [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    return verts, st, tris


def laptop_geometry():
    """gun space for build_srifle.held_frames: x forward, y left, z up. The laptop lies open, held by the base, screen towards the player"""
    screen, keys, metal = (0, 0, .5, .5), (.5, 0, 1, .5), (0, .5, 1, 1)
    base_faces = dict(top=keys, bottom=metal, front=metal, back=metal, left=metal, right=metal)
    lid_faces = dict(top=metal, bottom=metal, front=metal, back=screen, left=metal, right=metal)
    bv, bs, bt = box_mesh(0, 9, -6, 6, -0.7, 0.7, base_faces)
    a = math.radians(100)

    def hinge(pt):
        x, y, z = pt
        return (x * math.cos(a) - z * math.sin(a), y, x * math.sin(a) + z * math.cos(a))
    lv, ls, lt = box_mesh(0, 8, -6, 6, -0.4, 0.4, lid_faces, rot=lambda pt: hinge((pt[0], pt[1], pt[2])))
    lv = [(x + 0.2, y, z + 0.6) for x, y, z in lv]
    verts = bv + lv
    st = bs + ls
    tris = bt + [(a_ + len(bv), b_ + len(bv), c_ + len(bv)) for a_, b_, c_ in lt]
    return verts, st, tris


def laptop_models():
    from build_srifle import held_frames, smooth_normals
    laptop_skin()
    verts, st, tris = laptop_geometry()
    # the held one: the base is the "gun", gripped in the middle
    ctr = (4.5, 0.0, 0.0)
    gverts = [(x - 0, y, z) for x, y, z in verts]
    gnorms = smooth_normals(gverts, tris)
    frames = held_frames(gverts, gnorms, 4.5, 30.0)     # (the last number sets the scale: about 11 units, a laptop in a hand)
    md3lib.write(os.path.join(PROGS, "ltg_p.md3"), dict(name="ltg_p", surfaces=[dict(
        name="laptop", shader="progs/ltg_p", tris=tris, st=st, frames=frames)], nframes=len(frames)))
    # the pickup: bigger, lying a little above the floor, screen up and open
    k = 2.4
    pv = [((x - 4.5) * k, y * k, z * k + 14) for x, y, z in verts]
    pn = smooth_normals(pv, tris)
    md3lib.write(os.path.join(PROGS, "ltg_g.md3"), dict(name="ltg_g", surfaces=[dict(
        name="laptop", shader="progs/ltg_p", tris=tris, st=st, frames=[(pv, pn)])], nframes=1))
    print("wrote ltg_p.md3 (%d frames) and ltg_g.md3" % len(frames))



# ----------------------------------------------------------------------------- the laser beam

LASER_LEN = 300.0     # the beam model is this long; ltgun.qc stretches it with .scale (distance / LASER_LEN)
LASER_HALF = 0.9      # half its width: the stretch scales the width too, so it stays the same thickness on screen at any distance


def laser_model():
    from PIL import Image as _I
    im = _I.new("RGB", (16, 16))
    px = im.load()
    for y in range(16):                       # across the beam: white-hot in the middle, red at the edges
        t = abs(y - 7.5) / 7.5
        r, g, bl = 255, int(255 * max(0.0, 1 - t * 1.6) ** 1.5), int(255 * max(0.0, 1 - t * 2.2) ** 2)
        for x in range(16):
            px[x, y] = (r, g, bl)
    im.save(os.path.join(PROGS, "ltg_laser.png"))
    L, w = LASER_LEN, LASER_HALF
    verts = [(0, -w, 0), (L, -w, 0), (L, w, 0), (0, w, 0),          # a ribbon in the horizontal plane ...
             (0, 0, -w), (L, 0, -w), (L, 0, w), (0, 0, w)]          # ... and one in the vertical plane: seen from any side
    st = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 0), (1, 1), (0, 1)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (4, 6, 5), (4, 7, 6)]
    norms = [(0, 0, 1)] * 4 + [(0, 1, 0)] * 4
    md3lib.write(os.path.join(PROGS, "ltg_laser.md3"), dict(name="ltg_laser", surfaces=[dict(
        name="beam", shader="progs/ltg_laser", tris=tris, st=st, frames=[(verts, norms)])], nframes=1))

# ----------------------------------------------------------------------------- shaders

def block(name, lines):
    return "%s\n{\n\tcull none\n%s}\n" % (name, "".join("\t%s\n" % l for l in lines))


def shaders(idle_count):
    os.makedirs(SCRIPTS, exist_ok=True)
    out = ["// written by mm_tools/build_ltgun_assets.py\n"]
    ping = list(range(idle_count)) + list(range(idle_count - 2, 0, -1))
    out.append(block("progs/ltg_idle", ["{", "\tanimmap 8 " + " ".join("progs/ltg_i_%02d" % i for i in ping), "\talphafunc GE128", "}"]))
    step = ANIM_N // VARIANTS
    for k in range(VARIANTS):
        seq = [(i - step * k) % ANIM_N for i in range(ANIM_N)]       # the film starts (frame 0) when the clock is on frame step * k
        out.append(block("progs/ltg_type_%d" % k, ["{", "\tanimmap %d " % ANIM_FPS + " ".join("progs/ltg_t_%02d" % i for i in seq), "\talphafunc GE128", "}"]))
    for v in range(24):
        out.append(block("progs/ltg_head_v%02d" % v, ["{", "\tmap progs/ltg_head_%02d" % v, "\talphafunc GE128", "}"]))
    out.append(block("progs/ltg_laser", ["{", "	map progs/ltg_laser", "	blendfunc add", "}"]))
    out.append(block("progs/ltg_aura", ["{", "\tanimmap 10 " + " ".join("progs/ltg_aura_%02d" % i for i in range(AURA_N)), "\tblendfunc add", "}"]))
    open(os.path.join(SCRIPTS, "ltgun.shader"), "w").write("\n".join(out))


def effects():
    fx = os.path.join(MOD, "effectinfo.txt")
    begin, end = b"// ---- Laptop gun begin", b"// ---- Laptop gun end"
    raw = open(fx, "rb").read()
    if begin in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
    add = open(os.path.join(HERE, "ltgun_effectinfo.txt"), "rb").read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    open(fx, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + add + end + b"\r\n")


# ----------------------------------------------------------------------------- sounds

RATE = 22050


def write_wav(name, samples):
    s = np.clip(samples, -1, 1)
    with wave.open(os.path.join(SOUND, name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((s * 32000).astype("<i2").tobytes())


def env(n, attack, decay):
    t = np.arange(n) / RATE
    return np.minimum(t / max(attack, 1e-4), 1) * np.exp(-t / decay)


def sounds():
    os.makedirs(SOUND, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(CANIS_START), "-i", CANIS_VIDEO, "-vn",
                    "-af", "loudnorm=I=-14:TP=-1.0", "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16",
                    os.path.join(SOUND, "canis.wav")], check=True)
    rnd = np.random.RandomState(5)
    # keyboard: clicks every 50-110 ms for the 0.8 s of typing
    n = int(RATE * 0.8)
    out = np.zeros(n)
    t = 0.0
    while t < 0.75:
        i = int(t * RATE)
        m = int(RATE * 0.03)
        click = rnd.randn(m) * env(m, 0.0005, 0.004) + 0.6 * np.sin(2 * math.pi * rnd.uniform(700, 1500) * np.arange(m) / RATE) * env(m, 0.0005, 0.006)
        out[i:i + m] += click[:n - i] * rnd.uniform(0.5, 1.0)
        t += rnd.uniform(0.04, 0.08)
    write_wav("type.wav", out * 0.6)
    # send: a dial-up modem screech that ends in a whoosh
    n = int(RATE * 0.55)
    tt = np.arange(n) / RATE
    f = 1200 + 1100 * np.sin(2 * math.pi * 6 * tt) + 900 * tt
    ph = 2 * math.pi * np.cumsum(f) / RATE
    sig = np.sin(ph) * 0.5 + np.sign(np.sin(ph * 0.5)) * 0.15
    whoosh = rnd.randn(n) * np.clip((tt - 0.3) / 0.25, 0, 1) * np.exp(-(tt - 0.3).clip(0) * 4) * 0.5
    write_wav("send.wav", (sig * np.minimum(tt / 0.02, 1) * np.exp(-tt * 1.5) + whoosh) * 0.8)

    def crackle(dur, power):
        n = int(RATE * dur)
        tt = np.arange(n) / RATE
        sig = np.zeros(n)
        for _ in range(int(40 * dur * power)):
            i = rnd.randint(0, n - 200)
            m = rnd.randint(40, 200)
            sig[i:i + m] += rnd.randn(m) * np.exp(-np.arange(m) / (m / 4.0)) * rnd.uniform(0.3, 1.0)
        sig += np.sin(2 * math.pi * 120 * tt) * 0.25 * np.exp(-tt * 6) + np.sin(2 * math.pi * 3200 * tt) * 0.1 * np.exp(-tt * 12)
        return sig * np.minimum(tt / 0.003, 1) * np.exp(-tt * (3.0 / dur))
    write_wav("zap.wav", crackle(0.4, 1.0) * 0.9)
    big = crackle(0.6, 1.6)
    tt = np.arange(len(big)) / RATE
    write_wav("hit.wav", (big + np.sin(2 * math.pi * (90 - 50 * tt) * tt) * 0.8 * np.exp(-tt * 7)) * 0.8)
    write_wav("null.wav", np.zeros(int(RATE * 0.05)))
    print("sounds written to", SOUND)


if __name__ == "__main__":
    os.makedirs(PROGS, exist_ok=True)
    idle_count, aspect = held_textures()
    held_models(idle_count, aspect)
    head_model()
    aura_textures()
    laser_model()
    laptop_models()
    shaders(idle_count)
    effects()
    sounds()
    print("laptop gun assets done")
