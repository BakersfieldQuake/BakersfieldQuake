"""The THE DISK vote page: one self-contained HTML file (no external files or scripts) with the three animation sets
from build_netsend_disk_view.py running side by side, a frame inspector, the projectile from
build_netsend_disk_proj.py on a WebGL turntable, what each source video was used for, notes, and the vote form
(POSTs to /api/netsend-disk-vote on bakersfield.larrywew.fun, see netsend_disk_vote_server.py).

python3 build_netsend_disk_vote_html.py [--work build/netsend_disk] [--videos DIR] [--out docs/netsend_disk_vote/index.html]
"""
import argparse
import base64
import io
import json
import os
import sys
import zipfile

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import build_netsend_disk_view as bv  # noqa: E402

LEVELSHOTS = os.path.join(REPO, "..", "..", "..", "..", "BAKOQUAKE", "BakersfieldQuake", "zz_levelshots.pk3")
BGS = [("bklan6", "Padre Hotel (bklan6)"), ("bakersfieldish", "Bakersfield-ish street"), ("start", "start"),
       ("dm3", "dm3")]
WEBP_Q = 80

LEFT_OUT = {
    "v0": [(85, 240, "the disk turns black here (an AI glitch), so it is left out")],
    "v1": [(153, 240, "a slow push in on the label; Flip & Aim settles back to rest instead")],
    "v3": [(47, 55, "runs off the top of the video"), (197, 205, "the label warps (AI)")],
    "v4": [(167, 240, "the disk flies off; empty frames")],
    "v5": [(87, 240, "the disk flies at the camera, then the hand leaves")],
    "v6": [(89, 240, "the arm leaves the top of the frame, then the disk shatters")],
}
DESCR = {
    "v0": "Tilts the disk edge-on and sights down it. After f85 the disk turns black (an AI glitch).",
    "v1": "Turns it edge-on, shows the back, holds it flat like a frisbee, turns it back, then a slow push in.",
    "v2": "Twirls it in the fingers, shows the back, rubs the label with a thumb, rolls the grip.",
    "v3": "Close-up inspection, the label pulled up close; the disk hopping and spinning on the fingertips; a flick up and away.",
    "v4": "A whoosh across the frame (motion-streak backdrop, keyed out), then flipped onto the open palm and popped up.",
    "v5": "A sidearm frisbee throw.",
    "v6": "Raised overhead and turned to the light, then the arm leaves the frame and the disk shatters.",
}


def data_uri(mime, raw):
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def webp(path):
    im = Image.open(path).convert("RGBA")
    b = io.BytesIO()
    im.save(b, "WEBP", quality=WEBP_Q, method=6, alpha_quality=90)
    return data_uri("image/webp", b.getvalue())


def jpeg(im, q=84):
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return data_uri("image/jpeg", b.getvalue())


def strip(video_path, n=13, h=90):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    idx = [round(i * (len(frames) - 1) / (n - 1)) for i in range(n)]
    w = round(h * 16 / 9)
    tiles = []
    for i in idx:
        t = cv2.resize(frames[i], (w, h), interpolation=cv2.INTER_AREA)
        cv2.putText(t, str(i), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (40, 40, 230), 1, cv2.LINE_AA)
        tiles.append(t)
    return jpeg(Image.fromarray(cv2.cvtColor(np.hstack(tiles), cv2.COLOR_BGR2RGB)), 80)


def uses():
    out = {v: [] for v in bv.VIDEO_NAMES}
    out["v5"].append(dict(set="R", a=0, b=27, label="Rest hold (all sets)"))
    for sid, spec in bv.SETS.items():
        clips = [(t["name"], t["segs"]) for t in spec["tricks"]] + [(spec["throw"]["name"] + " (throw)", spec["throw"]["segs"])]
        for name, segs in clips:
            span = {}
            for seg in segs:
                if seg[0] != "src" or (seg[1] == "v5" and seg[2] == [0.0]):
                    continue
                a, b = min(seg[2]), max(seg[2])
                lo, hi = span.get(seg[1], (a, b))
                span[seg[1]] = (min(lo, a), max(hi, b))
            for v, (a, b) in span.items():
                out[v].append(dict(set=sid, a=round(a), b=round(b), label=name))
    for v, lst in LEFT_OUT.items():
        for a, b, why in lst:
            out[v].append(dict(set="X", a=a, b=b, label="left out: " + why))
    for v in out:
        out[v].sort(key=lambda u: u["a"])
        for k, u in enumerate(out[v]):
            u["lane"] = k % 2
    return out


def notes_html(manifest, proj_facts):
    rows = []
    for sid, s in manifest["sets"].items():
        th = [c for c in s["clips"] if c["kind"] == "throw"][0]
        mb = s["frames"] * manifest["tex"][0] * manifest["tex"][1] * 4 / 1e6
        rows.append("<tr><td><span class='tag t%s'>%s</span> %s</td><td class='n'>%d</td><td class='n'>%d</td>"
                    "<td class='n'>%.0f MB</td><td class='n'>%.2f s</td></tr>"
                    % (sid, sid, s["title"], s["frames"], len([c for c in s["clips"] if c["kind"] == "trick"]), mb,
                       th["release"] / th["fps"]))
    return """
<h3>What this is</h3>
<ul>
<li>The NetSend gun ("WHERE'S THE DISK?", the 4th fun gun) gets a new held model. The old 3D hand with the black
  <code>LOL.BAT</code> floppy is replaced by a sprite of a black-gloved hand and the blue <b>THE DISK</b> floppy from your videos.
  It is built exactly like the Milky Gun's hand: one card MD3 (<code>progs/v_netsend.md3</code>) whose skin picks the frame each tick.</li>
<li>The thrown disk (<code>progs/netsend_disk.md3</code>) is a new model textured from the same videos, so the disk you throw is the one in the hand.
  The disk sticking out of the PC uses the same texture and turns blue too.</li>
<li>Three animation sets to vote on. Clips can be mixed after the vote, for example set A's throw with set B's tricks.</li>
</ul>
<h3>The sets</h3>
<table><thead><tr><th>Set</th><th>Frames</th><th>Tricks</th><th>Texture memory</th><th>Fire → release</th></tr></thead><tbody>%s</tbody></table>
<p class="sub" style="margin-top:6px">Frames are %dx%d RGBA, the same texel density on screen as the Milky Gun (248 frames, 384x510, about 194 MB).
Only the winning set ships, so players load one set. The old model released the disk 0.29 s after fire.</p>
<h3>How the frames were made</h3>
<ul>
<li><b>Frame extraction:</b> all 7 videos (1280x720, 24 fps, 241 frames) were split into frames and reviewed on contact sheets. The clip ranges used are below in <a href="#sources">Source videos</a>.</li>
<li><b>Keying</b> (<code>disk_keyer.py</code>): the backdrop is estimated per frame (it follows the studio vignette and the grey cyclorama),
  and edges get a real matte with the colour un-mixed from the backdrop, so there is no white rim.
  The disk is convex, so its plastic hull is filled in. That keeps the near-white metal shutter from being keyed out.
  Light-grey fringe outside the disk is removed, which also cleans up the motion streaks in v4.</li>
<li><b>Smoothness</b> (<code>disk_anim.py</code>): the clips are retimed (tricks about 1.5x faster than the slow AI footage) and in-between frames come from optical flow.
  Each throw is retimed to 60 fps with a slow coil and a fast snap.
  Where a clip has to get back to the rest pose: if the poses are close, the hand glides back along a fitted affine plus flow.
  If they are far apart, a short motion-blurred smear is used instead, because flow would double-expose.</li>
<li><b>Release:</b> from the release frame on, the disk is keyed out of the hand, and the game spawns the real disk on that exact frame
  (<code>NS_THROW_DELAY</code> now comes from the frame map). Set A's follow-through is a synthetic motion-blurred arm whip,
  because in v5 the disk flies back at the camera across the arm.</li>
<li><b>Placement:</b> every set shares one crop, so they all rest in exactly the same spot (lower right, clear of the crosshair).</li>
</ul>
<h3>In the game</h3>
<ul>
<li><code>netsend.qc</code>: new <code>NS_DiskViewFrame</code>. In order: the throw, the empty hand dropping away, nothing in the hand until the magazine
  gives a disk back, a new disk rising from below with a little overshoot, a trick, or the rest hold. A trick starts on the rest hold's neutral frame every 3 to 6 s, and the tricks take turns.
  This is the same logic the preview runs. <code>ns_vm_tricks 0</code> turns the tricks off.</li>
<li>The disk now leaves from the hand's side of the screen (6 units right, traced so it never starts inside a wall) instead of dead centre.</li>
<li>Hooked in like the other card guns: <code>Pickle_ViewFrame</code> calls it for the viewmodel and its quad overlay. In <code>funguns.qc</code> the NetSend gun is just frame 0 of the card.</li>
<li>Builders: <code>build_netsend_disk_view.py</code> (frames, skins, shader, card MD3, the QC frame map <code>netsend_diskvm.qc</code>),
  <code>build_netsend_disk_proj.py</code> (projectile), and this page's <code>build_netsend_disk_vote_html.py</code>.</li>
</ul>
<h3>Projectile</h3><p class="sub">%s</p>
""" % ("".join(rows), manifest["tex"][0], manifest["tex"][1], proj_facts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=os.path.join(REPO, "build", "netsend_disk"))
    ap.add_argument("--videos", default=bv.VIDEO_DIR)
    ap.add_argument("--levelshots", default=os.path.abspath(LEVELSHOTS))
    ap.add_argument("--out", default=os.path.join(REPO, "build", "netsend_disk", "netsend_disk_vote.html"))
    ap.add_argument("--extra-notes", default="", help="an HTML file appended to the notes (test results)")
    ap.add_argument("--reuse-data", action="store_true", help="only re-apply the template to <work>/vote_data.json")
    args = ap.parse_args()
    tpl = open(os.path.join(HERE, "netsend_disk_vote.template.html"), encoding="utf-8").read()
    cache = os.path.join(args.work, "vote_data.json")
    if args.reuse_data:
        with open(cache, encoding="utf-8") as f:
            payload = f.read()
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(tpl.replace("/*__DATA__*/null", payload))
        print("wrote %s (%.1f MB) from cached data" % (args.out, os.path.getsize(args.out) / 1e6))
        return

    with open(os.path.join(args.work, "manifest.json")) as f:
        m = json.load(f)
    sets = {}
    for sid, s in m["sets"].items():
        frames = [webp(os.path.join(args.work, "preview", sid, "f%03d.png" % i)) for i in range(s["frames"])]
        sets[sid] = dict(title=s["title"], blurb=s["blurb"], clips=s["clips"], frames=frames)
        print("set %s: %d frames, %.1f MB as webp" % (sid, len(frames), sum(len(x) for x in frames) / 1e6))

    bgs = {}
    with zipfile.ZipFile(args.levelshots) as z:
        for key, name in BGS:
            im = Image.open(io.BytesIO(z.read("levelshots/%s.png" % key)))
            bgs[key] = dict(name=name, src=jpeg(im.resize((1024, 640), Image.LANCZOS), 82))
    g = np.linspace(70, 38, 320)[:, None].repeat(512, 1)
    bgs["grey"] = dict(name="plain grey", src=jpeg(Image.fromarray(np.dstack([g, g * 1.04, g * 1.12]).clip(0, 255).astype(np.uint8))))

    with open(os.path.join(args.work, "disk_proj.json")) as f:
        proj = json.load(f)
    atlas = Image.open(os.path.join(args.work, "netsend_disk_full.png"))
    proj["tex"] = jpeg(atlas, 90)
    proj["atlas"] = proj["tex"]
    ntri = len(proj["tris"])
    proj["facts"] = ("%d triangles, %d vertices, 8 frames (0 flying flat with the label up, 1 stuck in the floor, 2-7 trembling there), "
                     "one 512x512 texture: front, back, shutter, rim. Same frame map and texture name as before, so "
                     "NS_Throw and the PC model need no changes." % (ntri, len(proj["st"])))

    u = uses()
    sources = []
    for v, fn in bv.VIDEO_NAMES.items():
        sources.append(dict(id=v, file=fn, desc=DESCR[v], strip=strip(os.path.join(args.videos, fn)), uses=u[v]))

    notes = notes_html(m, proj["facts"])
    if args.extra_notes and os.path.exists(args.extra_notes):
        notes += open(args.extra_notes).read()

    data = dict(sets=sets, screen=m["screen"], tex=m["tex"], bgs=bgs, proj=proj, sources=sources, notes=notes)
    payload = json.dumps(data, separators=(",", ":"))
    with open(cache, "w", encoding="utf-8") as f:
        f.write(payload)
    html = tpl.replace("/*__DATA__*/null", payload)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s (%.1f MB)" % (args.out, os.path.getsize(args.out) / 1e6))


if __name__ == "__main__":
    main()
