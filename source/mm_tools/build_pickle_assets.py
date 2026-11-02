"""Pickle Surprise Bomb assets, written straight into BakersfieldQuake:
  progs/pickle_00..15.png    the pickle, one cut-out per frame of the turntable video (grey backdrop keyed out), toned down
  progs/vpk_00..NN.png       the hold video (an armoured fist gripping the pickle, pulling faces), white backdrop keyed out
  progs/pickle.md3           world model: a 20 unit two-sided card centred on the origin, front-facing faces
  progs/pickle_gib.md3       a real 3D pickle (a bumpy, slightly bent gherkin, 12 units long) with progs/pickle_skin.png: the pickles the blast throws
  progs/pickle_bomb.md3      the same pickle with the video's face on its top (pickle_face_NN.png, wandering eyes): the thrown, stuck grenade
  progs/v_pickle.md3         viewmodel: the hold video as a card low and to the right, the arm running off the bottom right
  scripts/pickle.shader      the animated faces (animmap)
  effectinfo.txt             pk_boom / pk_puff, the green explosion (from pickle_effectinfo.txt)
  sound/pickle/throw.wav, surprise.wav  the voted clips cut from the mp3 (22050 Hz mono)
python build_pickle_assets.py <turntable.mp4> <hold.mp4> <audio.mp3> [progs_dir] [sound_dir]
Needs ffmpeg on PATH and PIL (run it without -I so PIL is found)."""
import glob
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

TURNTABLE, HOLD, AUDIO = sys.argv[1], sys.argv[2], sys.argv[3]
PROGS = sys.argv[4] if len(sys.argv) > 4 else "G:/Quake/Combat/BakersfieldQuake/progs"
SOUND = sys.argv[5] if len(sys.argv) > 5 else "G:/Quake/Combat/BakersfieldQuake/sound"

N = 16              # turntable cut-outs
STEP = 9            # video frames between them (24 fps video)
CANVAS = 512        # turntable texture size
FRONT_SEQ = (15, 0, 1, 2, 1, 0)      # the frames that face you; the standing pickle only uses these
FACE_FPS = 5
HOLD_FPS = 8        # frames per second taken from the hold video
HOLD_W = 512        # hold texture width
DIM = 0.3           # the game runs r_hdr_scenebrightness 2.5, so a texture shows at two and a half times its value: the
                    # glossy render went to a white-out. These are tuned to look right under it.
HOLD_DIM = 0.6      # the held arm and pickle: brighter than the world ones (they sat too dark in the hand)
SPEED = {"surprise": 1.9}      # played faster (same pitch) so the trip-to-blast time is short: the clip comes out at 0.76 s
VOICES = [("throw", 78.05, 79.30),        # your vote: the "Pickle surprise" take at 78 s, as the throw
          ("surprise", 34.95, 36.40)]     # your vote: clip 017, the shout; cut to its first 1.45 s so the blast follows at once


def flooded(im, candidate):
    """alpha: everything except the candidate (backdrop) pixels connected to the frame's corners, specks dropped"""
    flood = candidate
    for corner in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
        if flood.getpixel(corner) == 255:
            ImageDraw.floodfill(flood, corner, 128)
    fg = flood.point(lambda x: 0 if x == 128 else 255)
    return fg.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))


def keyout_grey(im):
    """turntable: the backdrop and floor shadow are the pale, unsaturated pixels"""
    sat = im.convert("HSV").split()[1]
    out = im.convert("RGBA")
    out.putalpha(flooded(im, sat.point(lambda x: 255 if x < 40 else 0)))
    return out


def keyout_white(im):
    """hold video: the backdrop is white; the lightest channel of every backdrop pixel is high"""
    r, g, b = im.convert("RGB").split()
    lo = ImageChops.darker(ImageChops.darker(r, g), b)
    alpha = flooded(im, lo.point(lambda x: 255 if x > 226 else 0))
    alpha = alpha.filter(ImageFilter.MinFilter(3))                                   # eat the pale fringe
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out


def extract(video, tmp, vf, keyout, count=None):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf", vf, "-fps_mode", "vfr",
                    os.path.join(tmp, "f%03d.png")], check=True)
    names = sorted(n for n in os.listdir(tmp) if n.endswith(".png"))
    if count:
        assert len(names) >= count, "video gave %d frames, need %d" % (len(names), count)
        names = names[:count]
    return [keyout(Image.open(os.path.join(tmp, n))) for n in names]


def tone(crop, dim=None):
    """the render is glossy and pale: a little less light, a little more contrast"""
    rgb = crop.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.3)
    rgb = ImageEnhance.Brightness(rgb).enhance(DIM if dim is None else dim)
    rgb.putalpha(crop.getchannel("A"))
    return rgb


def turntable_textures(cutouts):
    boxes = [c.getchannel("A").getbbox() for c in cutouts]
    top = max(b[3] - b[1] for b in boxes)
    scale = (CANVAS - 16) / top     # one scale for the whole set, so the head does not grow and shrink
    for i, (c, b) in enumerate(zip(cutouts, boxes)):
        crop = tone(c.crop(b))
        crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        canvas.paste(crop, ((CANVAS - crop.width) // 2, (CANVAS - crop.height) // 2), crop)
        canvas.save(os.path.join(PROGS, "pickle_%02d.png" % i))


def hold_textures(frames):
    """every frame cropped to the same box (the union of them all), so the fist does not wander; returns (count, w/h)"""
    boxes = [f.getchannel("A").getbbox() for f in frames]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    h = round(HOLD_W * (box[3] - box[1]) / (box[2] - box[0]))
    for old in glob.glob(os.path.join(PROGS, "vpk_*.png")):
        os.remove(old)
    for i, f in enumerate(frames):
        tone(f.crop(box), HOLD_DIM).resize((HOLD_W, h), Image.LANCZOS).save(os.path.join(PROGS, "vpk_%02d.png" % i))
    return len(frames), (box[2] - box[0]) / float(box[3] - box[1])


def model(path, name, shader_name, hw, hh, dx, dy, dz):
    """one card, one frame: the faces are the shader's animmap, so the engine never blends between frames.
    The card stands in the Y/Z plane at x = dx, centred on (dy, dz), hw wide and hh high each side of that, and faces -X
    (the viewer, in the viewmodel). Left in the picture is +Y."""
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]          # both sides
    card = [(dx, dy + hw, dz - hh), (dx, dy + hw, dz + hh), (dx, dy - hw, dz + hh), (dx, dy - hw, dz - hh)]
    surf = dict(name="card", shader=shader_name, tris=tris, st=st, frames=[(card, [(-1.0, 0.0, 0.0)] * 4)])
    md3lib.write(path, dict(name=name, surfaces=[surf], nframes=1))


SKIN = 256


def base_skin():
    """a gherkin's skin: dull green, darker warts and paler bumps, tiling round the pickle (left to right)"""
    import random
    rnd = random.Random(11)
    w = h = SKIN
    im = Image.new("RGB", (w, h), (36, 62, 20))
    d = ImageDraw.Draw(im)
    for _ in range(190):                                      # long pale streaks
        x, y = rnd.randrange(w), rnd.randrange(h)
        for dx in (-w, 0, w):
            d.line((x + dx, y, x + dx + rnd.randint(-3, 3), y + rnd.randint(12, 40)), fill=(48, 80, 28))
    for _ in range(800):                                      # warts, wrapped so the seam does not show
        x, y, r = rnd.randrange(w), rnd.randrange(h), rnd.choice((1, 2, 2, 3))
        col = rnd.choice(((22, 40, 12), (66, 96, 40), (58, 84, 34)))
        for dx in (-w, 0, w):
            d.ellipse((x + dx - r, y - r, x + dx + r, y + r), fill=col)
    return im.filter(ImageFilter.GaussianBlur(0.8))


def pickle_skins(cutouts):
    """pickle_skin.png (plain: the flying pickles) and pickle_face_NN.png: the same skin with the video's face on the side that
    ends up facing up when the pickle lies on a floor (u = 0.25), one per front-facing frame, so its eyes wander"""
    base = base_skin()
    base.save(os.path.join(PROGS, "pickle_skin.png"))
    for i in FRONT_SEQ[:4]:
        c = cutouts[i]
        b = c.getchannel("A").getbbox()
        face = c.crop((b[0], b[1] + int((b[3] - b[1]) * 0.50), b[2], b[3]))              # the lower half of the pickle: the face
        face = tone(face)
        fw = 150
        face = face.resize((fw, round(face.height * fw / face.width)), Image.LANCZOS)
        skin = base.convert("RGBA")
        skin.paste(face, (SKIN // 4 - fw // 2, (SKIN - face.height) // 2), face)       # centred at u = 0.25
        skin.convert("RGB").save(os.path.join(PROGS, "pickle_face_%02d.png" % i))


def pickle_model(path, name, shader_name):
    """a surface of revolution along X: blunt ends, a little belly and a little bend, with smooth normals"""
    import math
    L, R, RINGS, SEGS, BEND = 12.0, 2.4, 14, 12, 0.9
    verts, norms, st, tris = [], [], [], []
    for i in range(RINGS + 1):
        t = i / float(RINGS)
        u = 2 * t - 1
        r = R * (1 - u ** 4) ** 0.5 * (1 + 0.08 * math.sin(t * 6.0))      # blunt ends and a slight lumpiness
        cy = BEND * (1 - u * u)                                           # the bend
        for j in range(SEGS + 1):
            a = 2 * math.pi * j / SEGS
            ny, nz = math.cos(a), math.sin(a)
            verts.append(((t - 0.5) * L, cy + r * ny, r * nz))
            norms.append((0.0, ny, nz) if 0 < i < RINGS else ((-1.0 if i == 0 else 1.0), 0.0, 0.0))
            st.append((j / float(SEGS), t))
    for i in range(RINGS):
        for j in range(SEGS):
            a = i * (SEGS + 1) + j
            b = a + SEGS + 1
            tris += [(a, b, a + 1), (a + 1, b, b + 1)]
    surf = dict(name="pickle", shader=shader_name, tris=tris, st=st, frames=[(verts, norms)])
    md3lib.write(path, dict(name=name, surfaces=[surf], nframes=1))


def shader(hold_count):
    scripts = os.path.join(os.path.dirname(PROGS), "scripts")
    os.makedirs(scripts, exist_ok=True)

    def block(name, fps, maps):
        return "%s\n{\n\tcull none\n\t{\n\t\tanimmap %d %s\n\t\talphafunc GE128\n\t}\n}\n" % (
            name, fps, " ".join(maps))

    with open(os.path.join(scripts, "pickle.shader"), "w") as f:
        f.write("// written by mm_tools/build_pickle_assets.py\n")
        f.write(block("progs/pickle_front", FACE_FPS, ["progs/pickle_%02d" % i for i in FRONT_SEQ]))
        ping = list(range(hold_count)) + list(range(hold_count - 2, 0, -1))      # first to last, then back to the first, and round again
        f.write(block("progs/pickle_hand", HOLD_FPS, ["progs/vpk_%02d" % i for i in ping]))
        f.write("progs/pickle_bombskin\n{\n\t{\n\t\tanimmap %d %s\n\t}\n}\n" % (
            FACE_FPS, " ".join("progs/pickle_face_%02d" % i for i in FRONT_SEQ)))


def effects():
    """pk_boom / pk_puff into the game's effectinfo.txt, between markers so a rerun replaces them"""
    fx = os.path.join(os.path.dirname(PROGS), "effectinfo.txt")
    begin, end = b"// ---- Pickle Surprise begin", b"// ---- Pickle Surprise end"
    raw = open(fx, "rb").read()
    if begin in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
    add = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pickle_effectinfo.txt"), "rb").read()
    add = add.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    open(fx, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + add + end + b"\r\n")


def sound():
    out_dir = os.path.join(SOUND, "pickle")
    os.makedirs(out_dir, exist_ok=True)
    for name, start, end in VOICES:
        dur = end - start
        speed = SPEED.get(name, 1.0)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.2f" % start,
                        "-t", "%.2f" % dur, "-i", AUDIO,
                        "-af", "atempo=%.2f,afade=t=in:st=0:d=0.03,afade=t=out:st=%.2f:d=0.15,loudnorm=I=-9:TP=-0.3" % (speed, dur / speed - 0.15),
                        "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", os.path.join(out_dir, name + ".wav")], check=True)


os.makedirs(PROGS, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    cutouts = extract(TURNTABLE, tmp, "select=not(mod(n\\,%d))" % STEP, keyout_grey, N)
    turntable_textures(cutouts)
with tempfile.TemporaryDirectory() as tmp:
    hold_count, hold_aspect = hold_textures(extract(HOLD, tmp, "fps=%d" % HOLD_FPS, keyout_white))

# progs/pickle.md3 (the standing balloon) now comes from make_pickle_views.py: 16 views in 16 frames. Run that after this script.
pickle_skins(cutouts)
pickle_model(os.path.join(PROGS, "pickle_gib.md3"), "pickle_gib", "progs/pickle_skin")
pickle_model(os.path.join(PROGS, "pickle_bomb.md3"), "pickle_bomb", "progs/pickle_bombskin")
# the hold card, at x = 14 in the viewmodel's space. Measured in game (1280x720): 23 pixels to the unit, so the screen is
# 55.6 units wide and 31.2 high around the view centre. The card's top is near the top of the picture, and its right edge and
# bottom edge are past the right and bottom of the screen, so the arm runs off the corner of the view like any held weapon
VH = 24.0
VW = VH * hold_aspect
model(os.path.join(PROGS, "v_pickle.md3"), "v_pickle", "progs/pickle_hand", VW / 2, VH / 2, 14.0, -28.5 + VW / 2, 4.5 - VH / 2)
shader(hold_count)
effects()
sound()
print("pickle assets written to", PROGS, "and", SOUND, "- hold video: %d frames, card %.1f x %.1f" % (hold_count, VW, VH))
