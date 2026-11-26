"""THE DISK: the NetSend gun's held model rebuilt from the user's seven Grok videos (a black-gloved hand and a blue 3.5"
floppy labelled THE DISK), the same way the Milky Gun's hand is built (build_milky_view.py): keyed video frames on one
card MD3, the frame picked per tick through .skin files.

Three animation sets are built so they can be compared and voted on (docs/netsend_disk_vote/). Each set has:
  rest      a subtle hold, ping-ponged (all sets share it, so every set rests in exactly the same spot)
  tricks    2-3 fidgets played from the rest pose now and then; each starts on the rest pose and ends on it
            (played there and back, or glided back with an affine + optical-flow "settle")
  throw     windup -> release -> follow-through, time-remapped and flow-interpolated to 60 fps;
            after the release frame the disk is keyed out of the hand (the game spawns the real one)

Source clips (24 fps, 241 frames; every clip starts on the same still):
  v0  tilt the disk edge-on to sight down it (the disk turns black after ~85: unused)
  v1  turn it edge-on, show the back, hold it flat like a frisbee, turn it back, bring it close
  v2  twirls in the fingers, the back, the thumb rubbing the label, grip changes
  v3  close-up inspection; the disk hovering and spinning on the fingertips; a flick up and away
  v4  a whoosh across the frame (motion-streak backdrop, keyed out); the disk flipped onto the palm and popped up
  v5  a sidearm frisbee throw
  v6  raised overhead to show it off (then a shatter, unused)

python3 build_netsend_disk_view.py [--videos DIR] [--work DIR] [--sets A,B,C] [--game-set A --mod DIR]
  --work     cache + outputs (default build/netsend_disk); preview frames land in <work>/preview/<set>/
  --game-set writes that set's game files (progs/ndvm_*.png, progs/v_netsend.md3 + .skin files,
             scripts/netsend_diskvm.shader, and netsend_diskvm.qc constants) into --mod (a BakersfieldQuake folder)
"""
import argparse
import functools
import json
import os
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import disk_anim as da  # noqa: E402
import disk_keyer as dk  # noqa: E402

VIDEO_DIR = "/home/computer/Desktop/Media/images/quakeassets"
VIDEO_NAMES = {
    "v0": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2.mp4",
    "v1": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (1).mp4",
    "v2": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (2).mp4",
    "v3": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (3).mp4",
    "v4": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (4).mp4",
    "v5": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (5).mp4",
    "v6": "grok-video-1b4a1e8e-6f57-46eb-a259-398a6121b5d2 (6).mp4",
}

# ---------------------------------------------------------------- where the rest pose sits on screen
# Screen units: height = 1, width = 16/9; x from the left, y from the top. The rest disk's centre and height:
REST_CX, REST_CY = 0.705 * 16 / 9, 0.585
REST_DISK_H = 0.215
SCREEN_W = 16.0 / 9.0
# The game's view space at depth VIEW_X (same frame as the Milky Gun's card): +/-HALF_W across, +/-HALF_H up
VIEW_X, HALF_W, HALF_H = 14.0, 27.8, 15.6
TEX_W = 512
GAME_DIM = 0.60          # in-game textures are baked dim (rgbGen lightingDiffuse + the mod's HDR, like the Milky Gun)
OUT_FPS_THROW = 60.0


# ---------------------------------------------------------------- the clip specs
def rng(a, b, step=1.0):
    n = int(round(abs(b - a) / step)) + 1
    return list(np.linspace(a, b, n))


def S(v, positions, keep="all"):
    return ("src", v, [float(p) for p in positions], keep)


def M(n):
    """n in-between frames gliding from the previous segment's last frame onto the next segment's first
    (optical flow: for poses that are close)."""
    return ("morph", n)


def SM(n):
    """n smear frames between two poses that are too different for optical flow."""
    return ("smear", n)


def W(n, dx, dy, rot, pivot):
    """n synthetic follow-through frames flinging the previous segment's last frame."""
    return ("whip", n, dx, dy, rot, pivot)


REST = dict(name="Rest", kind="rest", fps=14.0, segs=[S("v5", rng(0, 27))],
            note="v5 f0-27, ping-ponged: the hand barely breathes")
REST_REF = ("v5", 0.0, "all")

SETS = {
    "A": dict(
        title="Frisbee Pro",
        blurb="Slow, smooth, confident. Turns the disk over to read the back, sights down it like a frisbee, "
              "then throws it with a real sidearm frisbee fling.",
        tricks=[
            dict(name="Flip & Aim", fps=24.0, play="once",
                 segs=[S("v1", rng(0, 152, 1.45)), M(9), S("v5", [0])],
                 note="v1 f0-152 at 1.65x: edge-on, the back, held flat to aim, turned back; settles to rest"),
            dict(name="Edge Sight", fps=24.0, play="pingpong", back=1.35,
                 segs=[S("v0", rng(0, 82, 1.3))],
                 note="v0 f0-82: tilts the disk edge-on and sights down it, then back"),
        ],
        throw=dict(name="Sidearm Frisbee", segs=[
            S("v5", da.ease_positions(46, 79.5, 22, power_in=2.2)),  # coil left, sweep, snap
            S("v5", [80], keep="nodisk"),                            # the disk is gone from here on
            W(9, 300, 150, -24, (900.0, 700.0)),                     # the arm whips on across and down
        ], release=22, note="v5 f46-80 time-remapped (slow coil, fast snap), released at f80 (the disk keyed out of "
                            "the hand), then the empty arm whips on across and down (synthetic, motion-blurred)"),
    ),
    "B": dict(
        title="Trickster",
        blurb="Busy fingers. Twirls it, rubs the label with a thumb, rolls the grip, balances it spinning on the "
              "fingertips, and flicks it away off the fingers.",
        tricks=[
            dict(name="Twirl & Rub", fps=24.0, play="once",
                 segs=[S("v2", rng(0, 150, 1.5)), SM(8), S("v5", [0])],
                 note="v2 f0-150 at 1.5x: spins, flips, the back, the thumb across the label; settles to rest"),
            dict(name="Grip Roll", fps=24.0, play="once",
                 segs=[S("v5", [0]), SM(6), S("v2", rng(156, 228, 1.5)), SM(7), S("v5", [0])],
                 note="v2 f156-228 at 1.5x: rolls the disk through the fingers; glides in and out of rest"),
            dict(name="Fingertip Spin", fps=24.0, play="once",
                 segs=[S("v3", rng(84, 196, 1.6)), SM(8), S("v5", [0])],
                 note="v3 f84-196 at 1.6x: the disk hops onto the fingertips and spins there; settles to rest"),
        ],
        throw=dict(name="Finger Flick", segs=[
            S("v5", [0]), SM(4),
            S("v3", da.ease_positions(206, 212, 14, power_in=1.8)),   # pinch, draw back, flick up and away
            S("v3", da.ease_positions(213, 220, 9, power_out=1.5), keep="arm"),
        ], release=19, note="smears into v3 f206 (the pinch), draws back and flicks it up and away (f206-212), "
                            "released at f212, open hand f213-220"),
    ),
    "C": dict(
        title="Showboat",
        blurb="Big and theatrical. Whooshes the disk across, brings it right up to the camera, raises it overhead, "
              "and throws by flipping it onto an open palm and popping it up.",
        tricks=[
            dict(name="Whoosh", fps=24.0, play="once",
                 segs=[S("v4", rng(0, 126, 1.5)), SM(8), S("v5", [0])],
                 note="v4 f0-126 at 1.5x (motion-streak backdrop keyed out): swept across and back; settles to rest"),
            dict(name="Close Look", fps=24.0, play="pingpong", back=1.4,
                 segs=[S("v3", rng(0, 45, 1.25))],
                 note="v3 f0-45: turned edge-on and over, the back brought right up to the camera, then back "
                      "(f47-55 run off the top of the video, so they are left out)"),
            dict(name="Read the Label", fps=24.0, play="pingpong", back=1.3,
                 segs=[S("v5", [0]), M(5), S("v3", rng(82, 57, 1.15))],
                 note="glides into v3 f82 and plays f82 back to f57: the label pulled up close to read it, then lowered"),
            dict(name="Show Off", fps=24.0, play="pingpong", back=1.5,
                 segs=[S("v6", rng(0, 88, 1.4))],
                 note="v6 f0-88: raised overhead and tilted to the light, then back down"),
        ],
        throw=dict(name="Palm Pop", segs=[
            S("v5", [0]), SM(4),
            S("v4", da.ease_positions(139, 157, 20, power_in=1.6)),   # flip onto the open palm, pop it up
            S("v4", da.ease_positions(158, 166, 9, power_out=1.5), keep="arm"),
        ], release=25, note="smears into v4 f139, flips it onto the open palm and pops it up (f139-157), empty palm f158-166"),
    ),
}


# ---------------------------------------------------------------- keying (cached, one worker per video)
def key_path(work, v, i, keep):
    return os.path.join(work, "key", "%s_%03d_%s.png" % (v, i, keep))


def _key_video(args):
    work, video_dir, v, wanted = args
    todo = sorted(x for x in wanted if not os.path.exists(key_path(work, v, x[0], x[1])))
    if not todo:
        return v, 0
    need = {}
    for i, keep in todo:
        need.setdefault(i, []).append(keep)
    cap = cv2.VideoCapture(os.path.join(video_dir, VIDEO_NAMES[v]))
    i = 0
    last = max(need)
    while i <= last:
        ok, bgr = cap.read()
        if not ok:
            break
        if i in need:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            for keep in need[i]:
                rgba = dk.key_frame(rgb, keep)
                cv2.imwrite(key_path(work, v, i, keep), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        i += 1
    cap.release()
    return v, len(todo)


def all_segments(set_ids):
    segs = list(REST["segs"])
    for s in set_ids:
        for t in SETS[s]["tricks"]:
            segs += t["segs"]
        segs += SETS[s]["throw"]["segs"]
    return segs


def key_everything(work, video_dir, set_ids):
    os.makedirs(os.path.join(work, "key"), exist_ok=True)
    wanted = {}
    for seg in all_segments(set_ids):
        if seg[0] != "src":
            continue
        _, v, pos, keep = seg
        for p in pos:
            for i in {int(np.floor(p)), int(np.ceil(p))}:
                wanted.setdefault(v, set()).add((i, keep))
    jobs = [(work, video_dir, v, w) for v, w in sorted(wanted.items())]
    with Pool(min(len(jobs), 7)) as pool:
        for v, n in pool.imap_unordered(_key_video, jobs):
            print("  keyed %s: %d new frames" % (v, n))


@functools.lru_cache(maxsize=48)
def keyed(work, v, i, keep):
    bgra = cv2.imread(key_path(work, v, i, keep), cv2.IMREAD_UNCHANGED)
    return cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA)


def src_frames(work, v, positions, keep):
    out = []
    for p in positions:
        i0 = int(np.floor(p))
        f = p - i0
        a = keyed(work, v, i0, keep)
        out.append(a.copy() if f < 1e-3 else da.flow_interp(a, keyed(work, v, i0 + 1, keep), f))
    return out


def render_clip(work, segs):
    """Full-resolution RGBA frames for a list of segments (morphs resolved against their neighbours)."""
    parts = []
    for seg in segs:
        if seg[0] == "src":
            parts.append(src_frames(work, seg[1], seg[2], seg[3]))
        else:
            parts.append(seg)
    out = []
    for k, part in enumerate(parts):
        if isinstance(part, tuple):
            if part[0] == "whip":
                out += da.whip(out[-1], part[1], part[2], part[3], part[4], part[5])
            elif part[0] == "smear":
                out += da.smear(out[-1], parts[k + 1][0], part[1])
            else:
                out += da.morph(out[-1], parts[k + 1][0], part[1])
        else:
            out += part
    return out


def drop_dupes(frames, segs):
    """A trailing S('v5', [0]) only anchors the settle morph; the rest clip already has that frame."""
    if segs and segs[-1][0] == "src" and segs[-1][1:3] == ("v5", [0.0]):
        frames = frames[:-1]
    if segs and segs[0][0] == "src" and segs[0][1:3] == ("v5", [0.0]):
        frames = frames[1:]
    return frames


# ---------------------------------------------------------------- placement, crop, grading
def placement(work):
    """Source->screen mapping from the rest still: scale (screen heights per source px) and the source point that
    lands on the rest centre."""
    rest = keyed(work, *REST_REF[:1], int(REST_REF[1]), REST_REF[2])
    rgb = np.ascontiguousarray(rest[..., :3])
    hull = dk.disk_hull(rgb)
    ys, xs = np.nonzero(hull > 0.5)
    cx, cy = (xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0
    dh = float(ys.max() - ys.min())
    return REST_DISK_H / dh, cx, cy


def to_screen(px, py, place):
    s, cx, cy = place
    return REST_CX + (px - cx) * s, REST_CY + (py - cy) * s


def from_screen(sx, sy, place):
    s, cx, cy = place
    return cx + (sx - REST_CX) / s, cy + (sy - REST_CY) / s


def union_crop(boxes, place, src_w=1280, src_h=720):
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    # never wider than what can be on screen: the right and bottom run off the screen edge
    vx0, vy0 = from_screen(0.0, 0.0, place)
    vx1, vy1 = from_screen(SCREEN_W, 1.0, place)
    x0, y0 = max(x0 - 2, int(np.floor(vx0)), 0), max(y0 - 2, int(np.floor(vy0)), 0)
    x1, y1 = min(x1 + 2, int(np.ceil(vx1)), src_w), min(y1 + 2, int(np.ceil(vy1)), src_h)
    return int(x0), int(y0), int(x1), int(y1)


def crop_resize(rgba, box, tw, th):
    c = rgba[box[1]:box[3], box[0]:box[2]].astype(np.float32)
    a = c[..., 3:4] / 255.0
    pm = np.dstack([c[..., :3] * a, c[..., 3:4]])
    r = cv2.resize(pm, (tw, th), interpolation=cv2.INTER_AREA)
    al = np.clip(r[..., 3], 0, 255)
    rgb = np.clip(r[..., :3] / np.maximum(al[..., None] / 255.0, 1e-4), 0, 255)
    # a touch of unsharp mask after the downscale keeps the label legible
    blur = cv2.GaussianBlur(rgb, (0, 0), 0.8)
    rgb = np.clip(rgb + 0.35 * (rgb - blur), 0, 255)
    a8 = np.where(al < 6, 0, np.round(al)).astype(np.uint8)
    c8 = np.round(rgb).astype(np.uint8)
    c8[a8 == 0] = 0
    return np.dstack([c8, a8])


def grade(rgba, dim):
    """Gentle contrast and a richer blue; dim < 1 bakes the in-game darkening."""
    x = rgba[..., :3].astype(np.float32) / 255.0
    x = np.clip((x - 0.015) / 0.985, 0, 1)
    x = np.power(x, 0.95)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    blue = np.clip((b - r - 0.12) / 0.3, 0, 1)
    b = np.clip(b * (1 + 0.06 * blue), 0, 1)
    r = np.clip(r * (1 - 0.04 * blue), 0, 1)
    x = np.dstack([r, g, b]) * dim
    out = rgba.copy()
    out[..., :3] = np.clip(np.round(x * 255), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0, :3] = 0
    return out


# ---------------------------------------------------------------- building
def build_set(args):
    """Renders one set's frames at full resolution into <work>/full/<sid>/NNN.png; returns the clip list and the
    union bbox of everything drawn."""
    work, sid = args
    spec = SETS[sid]
    fdir = os.path.join(work, "full", sid)
    os.makedirs(fdir, exist_ok=True)
    for old in os.listdir(fdir):
        os.remove(os.path.join(fdir, old))
    state = dict(n=0, box=[1 << 20, 1 << 20, 0, 0])

    def save(frames):
        first = state["n"]
        for f in frames:
            ys, xs = np.nonzero(f[..., 3] > 8)
            if len(xs):
                b = state["box"]
                b[0], b[1] = min(b[0], int(xs.min())), min(b[1], int(ys.min()))
                b[2], b[3] = max(b[2], int(xs.max()) + 1), max(b[3], int(ys.max()) + 1)
            cv2.imwrite(os.path.join(fdir, "%03d.png" % state["n"]), cv2.cvtColor(f, cv2.COLOR_RGBA2BGRA),
                        [cv2.IMWRITE_PNG_COMPRESSION, 1])
            state["n"] += 1
        return first, len(frames)

    clips = []
    first, cnt = save(render_clip(work, REST["segs"]))
    clips.append(dict(name=REST["name"], kind="rest", fps=REST["fps"], play="pingpong", back=1.0, first=first,
                      count=cnt, note=REST["note"]))
    for t in spec["tricks"]:
        first, cnt = save(drop_dupes(render_clip(work, t["segs"]), t["segs"]))
        clips.append(dict(name=t["name"], kind="trick", fps=t["fps"], play=t["play"], back=t.get("back", 1.0),
                          first=first, count=cnt, note=t["note"]))
        print("   set %s: %-16s %3d frames" % (sid, t["name"], cnt), flush=True)
    th = spec["throw"]
    first, cnt = save(drop_dupes(render_clip(work, th["segs"]), th["segs"]))
    rel = th["release"] - (1 if th["segs"][0][0] == "src" and th["segs"][0][1:3] == ("v5", [0.0]) else 0)
    clips.append(dict(name=th["name"], kind="throw", fps=OUT_FPS_THROW, play="once", back=1.0, first=first,
                      count=cnt, release=rel, note=th["note"]))
    print("   set %s: %-16s %3d frames (release at %d)" % (sid, th["name"], cnt, rel), flush=True)
    return sid, clips, state["box"], state["n"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", default=VIDEO_DIR)
    ap.add_argument("--work", default=os.path.join(REPO, "build", "netsend_disk"))
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--game-set", default="")
    ap.add_argument("--mod", default="")
    ap.add_argument("--qc-out", default=os.path.join(HERE, "netsend_diskvm.qc"))
    ap.add_argument("--skip-build", action="store_true", help="reuse <work>/manifest.json and preview frames")
    args = ap.parse_args()
    set_ids = [s.strip() for s in args.sets.split(",") if s.strip()]
    if args.game_set and args.game_set not in set_ids:
        set_ids.append(args.game_set)
    work = args.work
    if args.skip_build:
        with open(os.path.join(work, "manifest.json")) as f:
            manifest = json.load(f)
        write_game_files(work, manifest, args.game_set, args.mod or os.path.join(REPO, "build", "netsend_disk", "game"),
                         args.qc_out)
        return

    print("keying...")
    key_everything(work, args.videos, set_ids)
    place = placement(work)
    print("placement: %.6f screen-H per px, rest centre at source (%.1f, %.1f)" % place)

    built, boxes, counts = {}, [], {}
    print("building sets %s..." % ",".join(set_ids))
    with Pool(len(set_ids)) as pool:
        for sid, clips, bb, n in pool.imap_unordered(build_set, [(work, s) for s in set_ids]):
            built[sid], counts[sid] = clips, n
            boxes.append(bb)

    # one crop for every set, so they all sit in the same place (and any one can ship with the same card)
    box = union_crop(boxes, place)
    aspect = (box[2] - box[0]) / float(box[3] - box[1])
    tex_h = int(round(TEX_W / aspect))
    sx0, sy0 = to_screen(box[0], box[1], place)
    sx1, sy1 = to_screen(box[2], box[3], place)
    print("crop %s -> %dx%d, screen x %.3f..%.3f (of %.3f), y %.3f..%.3f" % (box, TEX_W, tex_h, sx0, sx1, SCREEN_W, sy0, sy1))

    manifest = dict(crop=box, tex=[TEX_W, tex_h], screen=dict(x0=sx0, y0=sy0, x1=sx1, y1=sy1, w=SCREEN_W),
                    sets={})
    for sid in set_ids:
        clips = built[sid]
        pdir = os.path.join(work, "preview", sid)
        os.makedirs(pdir, exist_ok=True)
        for old in os.listdir(pdir):
            os.remove(os.path.join(pdir, old))
        fdir = os.path.join(work, "full", sid)
        for skin in range(counts[sid]):
            fr = cv2.cvtColor(cv2.imread(os.path.join(fdir, "%03d.png" % skin), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
            small = crop_resize(fr, box, TEX_W, tex_h)
            Image.fromarray(grade(small, 1.0), "RGBA").save(os.path.join(pdir, "f%03d.png" % skin), compress_level=4)
        manifest["sets"][sid] = dict(title=SETS[sid]["title"], blurb=SETS[sid]["blurb"], clips=clips,
                                     frames=counts[sid])
        print("set %s: %d frames" % (sid, counts[sid]))
    with open(os.path.join(work, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)

    if args.game_set:
        write_game_files(work, manifest, args.game_set, args.mod or os.path.join(REPO, "build", "netsend_disk", "game"),
                         args.qc_out)


# ---------------------------------------------------------------- game files
def write_game_files(work, manifest, sid, mod, qc_out):
    import md3lib
    m = manifest["sets"][sid]
    tw, th = manifest["tex"]
    progs = os.path.join(mod, "progs")
    scripts = os.path.join(mod, "scripts")
    os.makedirs(progs, exist_ok=True)
    os.makedirs(scripts, exist_ok=True)
    for old in os.listdir(progs):
        if old.startswith("ndvm_") or old.startswith("v_netsend.md3_"):
            os.remove(os.path.join(progs, old))
    pdir = os.path.join(work, "preview", sid)
    with open(os.path.join(scripts, "netsend_diskvm.shader"), "w", newline="\n") as sh:
        sh.write("// written by mm_tools/build_netsend_disk_view.py (THE DISK, set %s: %s)\n" % (sid, m["title"]))
        for i in range(m["frames"]):
            name = "progs/ndvm_%03d" % i
            im = Image.open(os.path.join(pdir, "f%03d.png" % i)).convert("RGBA")
            arr = np.asarray(im).copy()
            Image.fromarray(grade_dim(arr), "RGBA").save(os.path.join(progs, "ndvm_%03d.png" % i), optimize=False, compress_level=9)
            sh.write("%s\n{\n\tcull none\n\tnomipmaps\n\t{\n\t\tclampmap %s\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}\n}\n" % (name, name))
            with open(os.path.join(progs, "v_netsend.md3_%d.skin" % i), "w", newline="\n") as sk:
                sk.write("card,%s\n" % name)

    # the card: the crop's screen rectangle mapped into view space at depth VIEW_X
    sc = manifest["screen"]

    def vy(sx):
        return HALF_W - sx / sc["w"] * 2 * HALF_W

    def vz(sy):
        return HALF_H - sy * 2 * HALF_H
    yl, yr, zt, zb = vy(sc["x0"]), vy(sc["x1"]), vz(sc["y0"]), vz(sc["y1"])
    card = [(VIEW_X, yl, zb), (VIEW_X, yl, zt), (VIEW_X, yr, zt), (VIEW_X, yr, zb)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    surf = dict(name="card", shader="progs/ndvm_000", tris=[(0, 1, 2), (0, 2, 3)], st=st,
                frames=[(card, [(-1.0, 0.0, 0.0)] * 4)])
    md3lib.write(os.path.join(progs, "v_netsend.md3"), dict(name="v_netsend", surfaces=[surf], nframes=1))

    # the frame map, as QuakeC constants (netsend_diskvm.qc is included by progs.src)
    lines = ["// written by mm_tools/build_netsend_disk_view.py: THE DISK set %s (%s), %d skins of progs/v_netsend.md3"
             % (sid, m["title"], m["frames"])]
    tricks = [c for c in m["clips"] if c["kind"] == "trick"]
    for c in m["clips"]:
        if c["kind"] == "rest":
            lines.append("float\tNDVM_REST_SKIN\t= %d;\nfloat\tNDVM_REST_COUNT\t= %d;\nfloat\tNDVM_REST_FPS\t= %g;"
                         % (c["first"], c["count"], c["fps"]))
        if c["kind"] == "throw":
            lines.append("float\tNDVM_THROW_SKIN\t= %d;\nfloat\tNDVM_THROW_COUNT\t= %d;\nfloat\tNDVM_THROW_FPS\t= %g;\n"
                         "float\tNDVM_THROW_RELEASE\t= %d;\t// skin offset where the disk leaves the hand\n"
                         "float\tNS_THROW_DELAY\t= %.4f;\t// seconds from the fire to the release frame (funguns.qc)"
                         % (c["first"], c["count"], c["fps"], c["release"], c["release"] / c["fps"]))
    lines.append("float\tNDVM_TRICKS\t= %d;" % len(tricks))
    for k in range(4):
        c = tricks[k] if k < len(tricks) else tricks[-1]
        lines.append("float\tNDVM_T%d_SKIN\t= %d;\nfloat\tNDVM_T%d_COUNT\t= %d;\nfloat\tNDVM_T%d_FPS\t= %g;\n"
                     "float\tNDVM_T%d_PINGPONG\t= %d;\nfloat\tNDVM_T%d_BACK\t= %g;\t// %s"
                     % (k, c["first"], k, c["count"], k, c["fps"], k, 1 if c["play"] == "pingpong" else 0, k,
                        c.get("back", 1.0), c["name"]))
    with open(qc_out, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("game files for set %s -> %s" % (sid, mod))


def grade_dim(arr):
    out = arr.copy()
    out[..., :3] = np.clip(np.round(arr[..., :3].astype(np.float32) * GAME_DIM), 0, 255).astype(np.uint8)
    return out


if __name__ == "__main__":
    main()
