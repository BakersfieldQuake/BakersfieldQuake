"""The Pickle Surprise's face at the moment it blows up: big big eyes and a wide open mouth. Makes six strengths of it from the
front turntable cut-outs (progs/pickle_15, 00, 01, 02: the four that the standing pickle's face animation cycles through) by bulging
the eyes and stretching the mouth open (a smooth lens warp, the cut-out's outline is left alone), and a vote page to pick one:
  out/faces/<option>_<frame>.png        the full 512 px textures, in the game's dimmed look (what would go in the game)
  source/pickle_face_vote/index.html    the vote page (the faces brightened to what the game shows, animated like the game does)
python make_pickle_faces.py      (needs numpy, opencv, PIL; run it without -I)"""
import base64
import io
import json
import os

import cv2
import numpy as np
from PIL import Image

MOD = r"G:\Quake\Combat\BakersfieldQuake"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "faces")
PAGE = os.path.join(HERE, "..", "pickle_face_vote", "index.html")

# where the eyes and the mouth are in each front cut-out (512 x 512), measured on a grid: (left eye, right eye, mouth)
FACE = {
    0: ((231, 368), (281, 368), (256, 441)),
    1: ((232, 369), (279, 369), (249, 440)),
    2: ((207, 365), (263, 366), (233, 440)),
    15: ((240, 365), (292, 368), (270, 441)),
}
SEQ = [15, 0, 1, 2, 1, 0]            # the order the game's animation shows them (progs/pickle_front), 5 per second
EYE_R = (46.0, 36.0)                 # radius of the lens round each eye (x, y)
MOUTH_R = (50.0, 38.0)
# name, title, what it is, eye magnification, mouth stretch (x, y)
OPTIONS = [
    ("surprised", "Surprised", "Eyes up half as big, mouth a bit wider. The gentle one.", 1.5, (1.25, 1.3)),
    ("bugeyes", "Bug eyes", "Huge eyes, the mouth as it is.", 2.3, (1.1, 1.1)),
    ("widemouth", "Wide mouth", "Eyes a little bigger, mouth stretched wide open.", 1.25, (1.9, 1.8)),
    ("scream", "Scream", "Big eyes and a big mouth together.", 2.0, (1.7, 1.8)),
    ("cartoon", "Cartoon", "Giant eyes, giant mouth.", 2.7, (2.1, 2.0)),
    ("googly", "Googly", "As far as it goes: the eyes take over the face, the mouth is a cave.", 3.4, (2.5, 2.4)),
]


def lens(img, c, r, sx, sy):
    """magnify the image round c (an ellipse of radii r) by sx, sy at the centre, fading to nothing at the rim"""
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs - c[0]) / r[0]
    ny = (ys - c[1]) / r[1]
    q = np.clip(1.0 - (nx * nx + ny * ny), 0.0, 1.0) ** 2         # 1 at the centre, 0 at the rim
    gx = 1.0 - (1.0 - 1.0 / sx) * q
    gy = 1.0 - (1.0 - 1.0 / sy) * q
    mx = (c[0] + (xs - c[0]) * gx).astype(np.float32)
    my = (c[1] + (ys - c[1]) * gy).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def warp(rgba, frame, eye, mouth):
    le, re_, m = FACE[frame]
    rgb = np.ascontiguousarray(rgba[..., :3])
    a = rgba[..., 3]
    km = max(1.0, 0.55 + 0.3 * (mouth[0] + mouth[1]) / 2)           # a bigger stretch needs a bigger lens or it just clips
    ke = max(1.0, 0.6 + 0.35 * eye)
    rgb = lens(rgb, m, (MOUTH_R[0] * km, MOUTH_R[1] * km), mouth[0], mouth[1])
    rgb = lens(rgb, le, (EYE_R[0] * ke, EYE_R[1] * ke), eye, eye)
    rgb = lens(rgb, re_, (EYE_R[0] * ke, EYE_R[1] * ke), eye, eye)
    return np.dstack([rgb, a])                                       # the outline (alpha) stays the cut-out's own


def data_uri(arr, bright):
    rgb = np.clip(arr[..., :3].astype(np.float32) * bright, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, arr[..., 3]]), "RGBA").crop((130, 285, 380, 490))
    im = im.resize((int(im.width * 1.4), int(im.height * 1.4)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def main():
    os.makedirs(OUT, exist_ok=True)
    src = {f: np.array(Image.open(os.path.join(MOD, "progs", "pickle_%02d.png" % f)).convert("RGBA")) for f in FACE}
    opts = [("now", "As it is now", "Today's face, for comparison.", None)]
    for name, title, what, eye, mouth in OPTIONS:
        opts.append((name, title, what, (eye, mouth)))
    data = []
    for name, title, what, par in opts:
        frames = {}
        for f in FACE:
            out = src[f] if par is None else warp(src[f], f, par[0], par[1])
            if par is not None:
                Image.fromarray(out.astype(np.uint8), "RGBA").save(os.path.join(OUT, "%s_%02d.png" % (name, f)))
            frames[f] = data_uri(out, 2.6)               # the game shows textures 2.5x brighter: show them that way
        data.append(dict(id=name, title=title, what=what, frames=[frames[f] for f in SEQ]))
        print("made", name)
    os.makedirs(os.path.dirname(os.path.abspath(PAGE)), exist_ok=True)
    open(PAGE, "w", encoding="utf-8").write(HTML.replace("/*DATA*/", "const OPTS = %s;" % json.dumps(data)))
    print("wrote", os.path.abspath(PAGE))


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pickle Face Vote</title>
<style>
:root{--bg:#f1f3ea;--card:#fbfcf6;--ink:#1c2a1c;--mute:#637060;--line:#d4d9c4;--accent:#2f8a3d;--accent-ink:#fff;--pick:#e3f3dd;--stage:#1d251d}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141a14;--card:#1d261d;--ink:#e7efe2;--mute:#94a28f;--line:#33403a;--accent:#58c46a;--accent-ink:#0d170f;--pick:#25402a;--stage:#0f150f}}
:root[data-theme="dark"]{--bg:#141a14;--card:#1d261d;--ink:#e7efe2;--mute:#94a28f;--line:#33403a;--accent:#58c46a;--accent-ink:#0d170f;--pick:#25402a;--stage:#0f150f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,Segoe UI,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 120px}
header{padding:20px 0 8px}
h1{margin:0 0 4px;font-size:26px}
header p{margin:0;color:var(--mute);max-width:80ch}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-top:14px}
.card{position:relative;border:2px solid var(--line);background:var(--card);border-radius:14px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column}
.card input{position:absolute;left:12px;top:12px;width:20px;height:20px;accent-color:var(--accent);z-index:2}
.card.on{border-color:var(--accent);background:var(--pick)}
.stage{background:var(--stage);display:flex;align-items:center;justify-content:center;aspect-ratio:350/287}
.stage img{width:100%;height:100%;object-fit:contain;display:block}
.info{padding:10px 12px 12px}
.info h2{margin:0;font-size:17px}
.info p{margin:2px 0 0;color:var(--mute);font-size:13.5px}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px;z-index:5}
.bar-in{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center}
.bar b{font-size:16px}
button{font:inherit;color:var(--accent-ink);background:var(--accent);border:0;border-radius:10px;padding:8px 16px;font-weight:650;cursor:pointer}
button.ghost{background:transparent;color:var(--ink);border:1px solid var(--line);font-weight:500}
textarea{font:inherit;width:100%;max-width:520px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);padding:6px 8px;height:34px;resize:none}
.hint{color:var(--mute);font-size:13px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Pickle face: the moment it blows up</h1>
  <p>Big big eyes and a wide open mouth. Each card is the pickle's face animated the way the game wobbles it, in the brightness the
  game shows. Pick the one you want (you can add a note, like "eyes from Cartoon, mouth from Scream"), then press
  <b>Copy my vote</b> and paste it to me in the chat.</p>
</header>
<div class="grid" id="grid"></div>
</div>
<div class="bar"><div class="bar-in">
  <span>Your pick: <b id="pick">nothing yet</b></span>
  <textarea id="note" placeholder="Optional note (e.g. eyes from Cartoon, mouth from Scream)"></textarea>
  <button id="copy">Copy my vote</button>
  <span class="hint" id="msg"></span>
</div></div>
<script>
/*DATA*/
const $ = id => document.getElementById(id);
let chosen = null;
try { chosen = localStorage.getItem("pickleFaceVote"); } catch (e) {}
const cards = [];
OPTS.forEach(o => {
  const el = document.createElement("label");
  el.className = "card";
  el.innerHTML = '<input type="radio" name="face" value="' + o.id + '"><div class="stage"><img alt=""></div><div class="info"><h2>' + o.title + '</h2><p>' + o.what + '</p></div>';
  $("grid").appendChild(el);
  const img = el.querySelector("img"), radio = el.querySelector("input");
  radio.addEventListener("change", () => select(o.id));
  cards.push({o, el, img, radio});
});
function select(id) {
  chosen = id;
  try { localStorage.setItem("pickleFaceVote", id); } catch (e) {}
  cards.forEach(c => { c.el.classList.toggle("on", c.o.id === id); c.radio.checked = c.o.id === id; });
  const o = OPTS.find(x => x.id === id);
  $("pick").textContent = o ? o.title : "nothing yet";
}
if (chosen) select(chosen);
let t0 = performance.now();
setInterval(() => {
  const i = Math.floor((performance.now() - t0) / 200);
  cards.forEach(c => { c.img.src = c.o.frames[i % c.o.frames.length]; });
}, 100);
$("copy").addEventListener("click", async () => {
  const o = OPTS.find(x => x.id === chosen);
  if (!o) { $("msg").textContent = "Pick a face first."; return; }
  const text = "Face vote: " + o.title + " (" + o.id + ")" + ($("note").value.trim() ? " - " + $("note").value.trim() : "");
  try { await navigator.clipboard.writeText(text); $("msg").textContent = "Copied: " + text; }
  catch (e) { $("note").value = text; $("note").select(); $("msg").textContent = "Copy it from the box: " + text; }
});
</script>
</body>
</html>
"""

main()
