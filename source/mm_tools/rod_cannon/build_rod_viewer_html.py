"""Builds:
  1. `source/mm_tools/out/rod_cannon/previews/rod_cannon_contact_sheet.png` (2x4 labeled contact sheet w/ POV crosshairs)
  2. `G:\\Quake\\Combat\\BakersfieldQuake\\rod_cannon.html` — 100% self-contained WebGL2 3D Studio & Slapstick Simulator
     packing `v_rodcannon.md3` (48f), `p_rodcannon.md3` + Combat+ `player_vwep.mdl` Ranger (259f), and `g_rodcannon.md3`!
"""
import base64
import gzip
import io
import json
import os
import struct
import sys
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "rod_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")
PREV_DIR = os.path.join(OUT_ROOT, "previews")
HTML_OUT = os.path.join(MOD_ROOT, "rod_cannon.html")

Q15_PK3 = r"G:\Quake\Combat\quake15\q15.pk3"
PAK_PATHS = (r"G:\Quake\Combat\id1\pak0.pak", r"G:\Quake\QBJ3\id1\pak0.pak")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
import md3lib


def _font(size):
    for nm in ("segoeui.ttf", "arialbd.ttf", "tahomabd.ttf", "consolab.ttf"):
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def stitch_contact_sheet():
    panels = [
        ("01_pov_idle.png",      "1 · 1ST-PERSON IDLE (f0) — Chrome Axle, Both Cart Wheels & Bullet Breech", True),
        ("02_pov_swell_max.png", "2 · MAX SWELL (f25) — +56% Chrome Belly Bulge & 3000-RPM Tire Burnout!",   True),
        ("03_pov_surge.png",     "3 · PERISTALTIC SURGE (f26) — +62% Bulge Rockets Past Axle T-Collar!",     True),
        ("04_pov_blast.png",     "4 · PEAK BLAST (f27) — +68% Flared Black Mouth, Starburst & Smoke-Rings!", True),
        ("05_pov_wheelie.png",   "5 · WHEELIE KICKBACK (f28) — +24° Muzzle Climb & Barbell Axle Whip!",      True),
        ("06_3p_stand.png",      "6 · 3RD-PERSON VWEP (`p_rodcannon` Stand f12) — Giant Shoulder Bazooka!",  False),
        ("07_3p_blast.png",      "7 · 3RD-PERSON FIRING (`p_rodcannon` RockAtt f108) — Blast & Smoke Ring!", False),
        ("08_pickup_tilt.png",   "8 · WORLD PICKUP (`g_rodcannon`) — Video Contraption at 34° Cannon Tilt!", False),
    ]
    pw, ph = 880, 520
    hdr_h = 38
    pad = 12
    cols, rows = 2, 4
    cw = pad + cols * (pw + pad)
    ch = 58 + rows * (ph + hdr_h + pad) + pad
    sheet = Image.new("RGB", (cw, ch), (10, 14, 23))
    draw = ImageDraw.Draw(sheet)
    f_title = _font(24)
    f_lbl = _font(16)

    draw.text(
        (pad + 6, 15),
        "CHROME-ROD CONTRAPTION BAZOOKA (`v_rodcannon` / `p_rodcannon` / `g_rodcannon`) — 8-PANEL VERIFICATION SHEET",
        fill=(241, 245, 249),
        font=f_title,
    )

    for idx, (fn, title, is_pov) in enumerate(panels):
        p_path = os.path.join(PREV_DIR, fn)
        if not os.path.exists(p_path):
            continue
        im = Image.open(p_path).convert("RGB")
        if im.size != (pw, ph):
            im = im.resize((pw, ph), Image.LANCZOS)
        if is_pov:
            d_im = ImageDraw.Draw(im)
            cx, cy = pw // 2, ph // 2
            d_im.line((cx - 10, cy, cx + 10, cy), fill=(74, 222, 128), width=2)
            d_im.line((cx, cy - 10, cx, cy + 10), fill=(74, 222, 128), width=2)

        c = idx % cols
        r = idx // cols
        x0 = pad + c * (pw + pad)
        y0 = 58 + r * (ph + hdr_h + pad)
        draw.rectangle((x0, y0, x0 + pw, y0 + hdr_h + ph), fill=(18, 25, 40), outline=(44, 62, 94), width=1)
        draw.text((x0 + 12, y0 + 9), title, fill=(125, 211, 252), font=f_lbl)
        sheet.paste(im, (x0, y0 + hdr_h))

    out_p = os.path.join(PREV_DIR, "rod_cannon_contact_sheet.png")
    sheet.save(out_p, "PNG", optimize=True)
    print(f"[SHEET OK] Wrote {out_p} ({sheet.size[0]}x{sheet.size[1]})")
    return out_p


def build_edges(tris):
    s = set()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u != v:
                s.add((min(int(u), int(v)), max(int(u), int(v))))
    return np.array(sorted(s), dtype=np.uint16)


def encode_pil_rgba(im: Image.Image, name: str):
    bio = io.BytesIO()
    im.convert("RGBA").save(bio, "PNG", optimize=True)
    return dict(name=name, uri="data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii"))


def add_bytes(arena: bytearray, b: bytes):
    while len(arena) & 3:
        arena.append(0)
    off = len(arena)
    arena.extend(b)
    return [off, len(b)]


def pack_md3_surfaces(md3_path, arena, surf_tex_map, surf_style):
    m = md3lib.read(md3_path)
    nf = m["nframes"]
    surfs_out = []
    tot_v, tot_t = 0, 0
    for s in m["surfaces"]:
        sname = s["name"]
        nt = len(s["tris"])
        # Compact away DarkPlaces VBO alignment prefix padding so WebGL buffers hold only active vertices!
        used = sorted({int(idx) for tri in s["tris"] for idx in tri})
        remap = {old_i: new_i for new_i, old_i in enumerate(used)}
        used_arr = np.array(used, dtype=np.int32)
        nv = len(used)
        tot_v += nv
        tot_t += nt
        tris_ccw = np.array([(remap[a], remap[c], remap[b]) for a, b, c in s["tris"]], dtype=np.uint16)
        edges = build_edges(tris_ccw)
        uv = np.array(s["st"], dtype=np.float32)[used_arr]

        pos_q = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_q = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            vv_u = np.array(vv, dtype=np.float32)[used_arr]
            nn_u = np.array(nn, dtype=np.float32)[used_arr]
            pos_q[fi] = np.clip(np.round(vv_u * 64.0), -32768, 32767).astype(np.int16)
            nrm_q[fi] = np.clip(np.round(nn_u * 127.0), -127, 127).astype(np.int8)

        st = surf_style[sname]
        surfs_out.append(dict(
            name=sname,
            nv=nv, nt=nt, ne=len(edges),
            tex=surf_tex_map[sname],
            metallic=st["metallic"],
            rough=st["rough"],
            unlit=st["unlit"],
            additive=st["additive"],
            tris=add_bytes(arena, tris_ccw.tobytes()),
            edges=add_bytes(arena, edges.tobytes()),
            uv=add_bytes(arena, uv.tobytes()),
            pos=add_bytes(arena, pos_q.tobytes()),
            nrm=add_bytes(arena, nrm_q.tobytes()),
        ))
    return dict(nf=nf, nv=tot_v, nt=tot_t, surfaces=surfs_out)


def pack_ranger_vwep_surface(arena, ranger_tex_idx):
    """Loads Combat+'s 259-frame `progs/player_vwep.mdl` + palette skin so Tab 2 renders Ranger holding `p_rodcannon`!"""
    pak_p = next(p for p in PAK_PATHS if os.path.exists(p))
    d_pak = open(pak_p, "rb").read()
    _, ofs, ln = struct.unpack_from("<4sii", d_pak, 0)
    pal = None
    for i in range(ln // 64):
        n, o, s = struct.unpack_from("<56sii", d_pak, ofs + 64 * i)
        if n.split(b"\0")[0].decode("ascii").lower() == "gfx/palette.lmp":
            pal = np.frombuffer(d_pak[o:o + s], dtype=np.uint8).reshape(256, 3)
            break

    with zipfile.ZipFile(Q15_PK3, "r") as z:
        b = z.read("progs/player_vwep.mdl")

    scale = struct.unpack_from("<3f", b, 8)
    origin = struct.unpack_from("<3f", b, 20)
    nsk, sw, sh, nv, nt, nf = struct.unpack_from("<6i", b, 48)
    p = 84
    skin_raw = None
    for k in range(nsk):
        gt = struct.unpack_from("<i", b, p)[0]
        p += 4
        if gt == 0:
            if k == 0:
                skin_raw = b[p:p + sw * sh]
            p += sw * sh
        else:
            nb = struct.unpack_from("<i", b, p)[0]
            p += 4 + 4 * nb
            if k == 0:
                skin_raw = b[p:p + sw * sh]
            p += nb * sw * sh

    skin_idx = np.frombuffer(skin_raw, dtype=np.uint8).reshape(sh, sw)
    skin_im = Image.fromarray(pal[skin_idx], mode="RGB")

    st_raw = [struct.unpack_from("<3i", b, p + 12 * i) for i in range(nv)]
    p += 12 * nv
    tris_raw = [struct.unpack_from("<4i", b, p + 16 * i) for i in range(nt)]
    p += 16 * nt

    frames_verts, frame_names = [], []
    for _ in range(nf):
        ft = struct.unpack_from("<i", b, p)[0]
        p += 4
        if ft == 0:
            fnm = b[p + 8:p + 24].split(b"\0")[0].decode("ascii", errors="ignore")
            p += 24
            fv = np.array([
                (b[p + 4 * i] * scale[0] + origin[0],
                 b[p + 4 * i + 1] * scale[1] + origin[1],
                 b[p + 4 * i + 2] * scale[2] + origin[2])
                for i in range(nv)
            ], dtype=np.float32)
            p += 4 * nv
            frames_verts.append(fv)
            frame_names.append(fnm)
        else:
            nb = struct.unpack_from("<i", b, p)[0]
            p += 4 + 8 + 4 * nb
            fv, fnm = None, "grp"
            for sub in range(nb):
                if sub == 0:
                    fnm = b[p + 8:p + 24].split(b"\0")[0].decode("ascii", errors="ignore")
                p += 24
                if sub == 0:
                    fv = np.array([
                        (b[p + 4 * i] * scale[0] + origin[0],
                         b[p + 4 * i + 1] * scale[1] + origin[1],
                         b[p + 4 * i + 2] * scale[2] + origin[2])
                        for i in range(nv)
                    ], dtype=np.float32)
                p += 4 * nv
            frames_verts.append(fv)
            frame_names.append(fnm)

    vmap, orig_idx, uv_list, tris_ccw = {}, [], [], []
    for front, i0, i1, i2 in tris_raw:
        tri = []
        for idx in (i0, i1, i2):
            onseam, s_px, t_px = st_raw[idx]
            back = bool(onseam) and (front == 0)
            key = (idx, back)
            if key not in vmap:
                vmap[key] = len(orig_idx)
                orig_idx.append(idx)
                su = (s_px + (sw * 0.5 if back else 0.0) + 0.5) / sw
                tv = (t_px + 0.5) / sh
                uv_list.append((su, tv))
            tri.append(vmap[key])
        if tri[0] != tri[1] and tri[1] != tri[2] and tri[0] != tri[2]:
            tris_ccw.append((tri[0], tri[2], tri[1]))

    orig_arr = np.array(orig_idx, dtype=np.int32)
    tris_np = np.array(tris_ccw, dtype=np.uint16)
    edges = build_edges(tris_np)
    uv_np = np.array(uv_list, dtype=np.float32)
    nv_u = len(orig_idx)

    pos_q = np.zeros((nf, nv_u, 3), dtype=np.int16)
    nrm_q = np.zeros((nf, nv_u, 3), dtype=np.int8)
    F_i = tris_np.astype(np.int32)
    for fi, fv in enumerate(frames_verts):
        V_u = fv[orig_arr]
        N_u = np.zeros_like(V_u)
        fn = np.cross(V_u[F_i[:, 1]] - V_u[F_i[:, 0]], V_u[F_i[:, 2]] - V_u[F_i[:, 0]])
        np.add.at(N_u, F_i[:, 0], fn)
        np.add.at(N_u, F_i[:, 1], fn)
        np.add.at(N_u, F_i[:, 2], fn)
        nl = np.maximum(1e-6, np.linalg.norm(N_u, axis=1, keepdims=True))
        N_u /= nl
        pos_q[fi] = np.clip(np.round(V_u * 64.0), -32768, 32767).astype(np.int16)
        nrm_q[fi] = np.clip(np.round(N_u * 127.0), -127, 127).astype(np.int8)

    surf = dict(
        name="ranger_body",
        nv=nv_u, nt=len(tris_np), ne=len(edges),
        tex=ranger_tex_idx,
        metallic=0.12, rough=0.68, unlit=False, additive=False,
        tris=add_bytes(arena, tris_np.tobytes()),
        edges=add_bytes(arena, edges.tobytes()),
        uv=add_bytes(arena, uv_np.tobytes()),
        pos=add_bytes(arena, pos_q.tobytes()),
        nrm=add_bytes(arena, nrm_q.tobytes()),
    )
    return surf, skin_im, frame_names


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CHROME-ROD CONTRAPTION BAZOOKA · Quake 3D Weapon Studio</title>
<style>
  :root { --bg:#080c15; --panel:#101726; --border:#24334f; --acc:#38bdf8; --silver:#e2e8f0; --hot:#fb923c; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--silver); font-family:'Segoe UI',system-ui,sans-serif; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
  header { padding:10px 18px; background:#0c1220; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .brand { display:flex; align-items:center; gap:12px; }
  .badge { background:linear-gradient(135deg,#f8fafc,#94a3b8); color:#080c15; font-weight:900; font-size:11px; padding:3px 8px; border-radius:4px; letter-spacing:0.08em; }
  h1 { font-size:17px; font-weight:900; letter-spacing:0.05em; color:#f8fafc; }
  .tabs { display:flex; gap:6px; flex-wrap:wrap; }
  button { background:#172136; color:#dbeafe; border:1px solid var(--border); border-radius:6px; padding:7px 12px; font-size:12px; font-weight:700; cursor:pointer; transition:0.15s; }
  button:hover { border-color:var(--acc); background:#1f2e4a; }
  button.active { background:var(--acc); color:#06101e; border-color:var(--acc); }
  button.fire-btn { background:linear-gradient(135deg,#f97316,#ef4444); color:#fff; border-color:#fdba74; font-size:13px; padding:8px 16px; box-shadow:0 0 18px rgba(249,115,22,0.42); }
  button.fire-btn:active, button.fire-btn.charging { background:linear-gradient(135deg,#38bdf8,#ffffff); color:#06101e; box-shadow:0 0 26px rgba(56,189,248,0.88); }
  main { flex:1; display:grid; grid-template-columns:1fr 340px; min-height:0; }
  #vp-wrap { position:relative; background:radial-gradient(circle at 50% 42%,#16213a 0%,#060911 78%); overflow:hidden; }
  canvas { width:100%; height:100%; display:block; }
  #crosshair { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); pointer-events:none; color:#4ade80; font-weight:900; font-size:20px; text-shadow:0 0 6px #000; }
  #charge-hud { position:absolute; left:50%; bottom:68px; transform:translateX(-50%); background:rgba(8,12,21,0.84); border:1px solid var(--border); border-radius:8px; padding:8px 16px; text-align:center; pointer-events:none; min-width:290px; }
  #charge-bar { height:9px; background:#1e293b; border-radius:5px; overflow:hidden; margin-top:5px; }
  #charge-fill { height:100%; width:0%; background:linear-gradient(90deg,#38bdf8,#facc15,#ef4444); transition:width 0.04s linear; }
  #scrubber-bar { position:absolute; left:14px; right:14px; bottom:12px; background:rgba(12,18,32,0.90); border:1px solid var(--border); border-radius:8px; padding:8px 14px; display:flex; align-items:center; gap:10px; }
  input[type=range] { flex:1; accent-color:var(--acc); }
  aside { background:var(--panel); border-left:1px solid var(--border); padding:14px; overflow-y:auto; display:flex; flex-direction:column; gap:11px; font-size:12.5px; line-height:1.45; }
  .card { background:#0b111e; border:1px solid var(--border); border-radius:8px; padding:11px; }
  .card h3 { font-size:11.5px; text-transform:uppercase; letter-spacing:0.08em; color:var(--acc); margin-bottom:7px; }
  .kv { display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #162036; gap:8px; }
  .kv:last-child { border-bottom:none; }
  .row { display:flex; flex-wrap:wrap; gap:6px; }
  code { color:#93c5fd; font-family:Consolas,monospace; font-size:11.5px; }
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">MD3 + STRICT Q1 MDL + VWEP</span>
    <h1>CHROME-ROD CONTRAPTION BAZOOKA</h1>
  </div>
  <div class="tabs">
    <button id="tab-0" class="active" onclick="setModel(0)">1 · 1st-Person Bazooka (48f)</button>
    <button id="tab-1" onclick="setModel(1)">2 · 3rd-Person Ranger vwep (259f)</button>
    <button id="tab-2" onclick="setModel(2)">3 · World Pickup (`g_rodcannon`)</button>
  </div>
  <div class="row">
    <button id="btn-charge" class="fire-btn">HOLD TO SWELL &amp; BLAST! (or Space)</button>
  </div>
</header>
<main>
  <div id="vp-wrap">
    <canvas id="gl"></canvas>
    <div id="crosshair">+</div>
    <div id="charge-hud">
      <div id="hud-label" style="font-weight:800;font-size:12px;letter-spacing:0.05em;">READY · HOLD SPACE TO SWELL BREECH &amp; REV WHEELS!</div>
      <div id="charge-bar"><div id="charge-fill"></div></div>
    </div>
    <div id="scrubber-bar">
      <button id="btn-play" onclick="togglePlay()">Pause</button>
      <button onclick="triggerFullCycle()">Play Full Slapstick Shot</button>
      <input id="scrub" type="range" min="0" max="47" step="0.05" value="0">
      <span id="frame-lbl" style="min-width:138px;font-family:Consolas,monospace;font-size:12px;">f00 · idle1</span>
    </div>
  </div>
  <aside>
    <div class="card">
      <h3>Camera &amp; Viewport</h3>
      <div class="row" style="margin-bottom:8px;">
        <button id="btn-pov90" class="active" onclick="setPov(90)">Quake POV 90°</button>
        <button id="btn-pov111" onclick="setPov(111)">Bakersfield POV 111°</button>
        <button id="btn-orbit" onclick="setOrbit()">Free 3D Orbit</button>
      </div>
      <div class="row">
        <button id="btn-wire" onclick="toggleWire()">Wireframe: OFF</button>
        <button id="btn-ranger" class="active" onclick="toggleRanger()">Ranger Body: ON</button>
      </div>
      <div style="margin-top:7px;color:#94a3b8;font-size:11.5px;">Drag mouse in Orbit / 3rd-Person / Pickup mode to rotate; scroll wheel to zoom.</div>
    </div>
    <div class="card">
      <h3>3rd-Person Ranger vwep Clips (Tab 2)</h3>
      <div class="row">
        <button id="p3-stand" class="active" onclick="set3PClip('stand',12,16,8)">Stand (f12–16)</button>
        <button id="p3-run" onclick="set3PClip('run',6,11,10)">Run + Rolling Wheels! (f6–11)</button>
        <button id="p3-blast" onclick="set3PClip('blast',107,112,9)">Bazooka Blast! (f107–112)</button>
        <button id="p3-nail" onclick="set3PClip('nail',103,106,12)">Rapid Jitter (f103–106)</button>
      </div>
    </div>
    <div class="card">
      <h3>48-Frame Slapstick Schedule (`v_rodcannon`)</h3>
      <div class="kv"><span>Frames 0–15</span><code>idle1..16 (Heft &amp; Free-Roll)</code></div>
      <div class="kv"><span>Frames 16–25</span><code>swell1..10 (+56% Bulge &amp; Burnout)</code></div>
      <div class="kv"><span>Frames 26–29</span><code>blast1..4 (+68% Bell &amp; Wheelie)</code></div>
      <div class="kv"><span>Frames 30–39</span><code>recoil1..10 (Barbell Axle Boing)</code></div>
      <div class="kv"><span>Frames 40–47</span><code>reload1..8 (Breech Gulp)</code></div>
    </div>
    <div class="card">
      <h3>Standalone Quake Deliverables</h3>
      <div class="kv"><span>1st-Person HD</span><code>progs/v_rodcannon.md3</code></div>
      <div class="kv"><span>1st-Person Q1</span><code>progs/v_rodcannon.mdl</code></div>
      <div class="kv"><span>3rd-Person vwep</span><code>progs/p_rodcannon.md3</code></div>
      <div class="kv"><span>World Pickup</span><code>progs/g_rodcannon.md3/.mdl</code></div>
      <div class="kv"><span>DP Chrome Shader</span><code>scripts/rodcannon.shader</code></div>
    </div>
  </aside>
</main>
<script>
const PAYLOAD = /*__ROD_DATA__*/null;

async function DecompressB64Gz(b64) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const ds = new DecompressionStream('gzip');
  const w = ds.writable.getWriter();
  w.write(bin); w.close();
  return await new Response(ds.readable).arrayBuffer();
}

let gl, prog, arenaBuf;
let gpuModels = [], gpuTextures = [];
let curModelIdx = 0, povMode = true, fovDeg = 90, showWire = false, showRanger = true;
let playing = true, animMode = 'idle', animFrame = 0.0;
let charging = false, chargeVal = 0.0, spinTurntable = 0.0;
let p3Clip = { id: 'stand', start: 12, end: 16, fps: 8 };
let orbitAz = -0.68, orbitEl = 0.30, orbitDist = 66.0, dragging = false, lx = 0, ly = 0;

const VS = `#version 300 es
layout(location=0) in vec3 aPos0;
layout(location=1) in vec3 aNrm0;
layout(location=2) in vec3 aPos1;
layout(location=3) in vec3 aNrm1;
layout(location=4) in vec2 aUV;
uniform mat4 uMVP, uModel;
uniform float uLerp;
out vec3 vNrm, vPos;
out vec2 vUV;
void main() {
  vec3 p = mix(aPos0, aPos1, uLerp) / 64.0;
  vec3 n = normalize(mix(aNrm0, aNrm1, uLerp) / 127.0);
  vec4 wp = uModel * vec4(p, 1.0);
  vPos = wp.xyz;
  vNrm = normalize(mat3(uModel) * n);
  vUV = aUV;
  gl_Position = uMVP * wp;
}`;

const FS = `#version 300 es
precision highp float;
in vec3 vNrm, vPos;
in vec2 vUV;
uniform sampler2D uTex;
uniform vec3 uCamPos;
uniform float uMetallic, uRough, uUnlit, uWirePass;
out vec4 fragColor;
void main() {
  if (uWirePass > 0.5) { fragColor = vec4(0.22, 0.80, 1.0, 0.55); return; }
  vec4 tx = texture(uTex, vUV);
  if (uUnlit > 0.5) { fragColor = tx; return; }
  vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
  vec3 V = normalize(uCamPos - vPos);
  vec3 L1 = normalize(vec3(-0.32, 0.52, 0.79));
  vec3 L2 = normalize(vec3(0.72, -0.44, 0.52));
  float d1 = max(dot(N, L1), 0.0);
  float d2 = max(dot(N, L2), 0.0);
  vec3 H1 = normalize(L1 + V);
  float spec = pow(max(dot(N, H1), 0.0), mix(16.0, 84.0, 1.0 - uRough)) * (0.30 + 1.05 * uMetallic);
  vec3 R = reflect(-V, N);
  float softbox = smoothstep(0.15, 0.85, R.z) * 0.65 + 0.35 * exp(-pow((R.z - 0.55) / 0.22, 2.0));
  vec3 lit = tx.rgb * (0.34 + 0.72 * d1 + 0.28 * d2) + tx.rgb * uMetallic * 0.36 * softbox + vec3(0.95, 0.98, 1.0) * spec;
  fragColor = vec4(lit, tx.a);
}`;

function compile(vs, fs) {
  const s = (t, src) => { const sh = gl.createShader(t); gl.shaderSource(sh, src); gl.compileShader(sh); return sh; };
  const p = gl.createProgram();
  gl.attachShader(p, s(gl.VERTEX_SHADER, vs));
  gl.attachShader(p, s(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p);
  return p;
}

function mat4Mul(a, b) {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++)
    o[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1] + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
  return o;
}
function mat4Persp(fovYRad, asp, zn, zf) {
  const f = 1.0 / Math.tan(fovYRad * 0.5), nf = 1.0 / (zn - zf);
  return new Float32Array([f/asp,0,0,0, 0,f,0,0, 0,0,(zf+zn)*nf,-1, 0,0,2*zf*zn*nf,0]);
}
function mat4LookAt(eye, tgt, up) {
  const z0=eye[0]-tgt[0], z1=eye[1]-tgt[1], z2=eye[2]-tgt[2];
  let zl = Math.hypot(z0,z1,z2)||1; const zx=z0/zl, zy=z1/zl, zz=z2/zl;
  let xx = up[1]*zz - up[2]*zy, xy = up[2]*zx - up[0]*zz, xz = up[0]*zy - up[1]*zx;
  let xl = Math.hypot(xx,xy,xz)||1; xx/=xl; xy/=xl; xz/=xl;
  const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
  return new Float32Array([
    xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
    -(xx*eye[0]+xy*eye[1]+xz*eye[2]),
    -(yx*eye[0]+yy*eye[1]+yz*eye[2]),
    -(zx*eye[0]+zy*eye[1]+zz*eye[2]), 1
  ]);
}
function mat4RotZ(rad) {
  const c = Math.cos(rad), s = Math.sin(rad);
  return new Float32Array([c,s,0,0, -s,c,0,0, 0,0,1,0, 0,0,0,1]);
}

async function init() {
  const canvas = document.getElementById('gl');
  gl = canvas.getContext('webgl2', { antialias: true });
  prog = compile(VS, FS);
  arenaBuf = await DecompressB64Gz(PAYLOAD.binGz);

  for (const t of PAYLOAD.textures) {
    const img = new Image();
    img.src = t.uri;
    await img.decode();
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    if (t.nearest) {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    gpuTextures.push(tex);
  }

  for (const m of PAYLOAD.models) {
    const surfs = m.surfaces.map(s => {
      const mkBuf = (slice, target) => {
        const b = gl.createBuffer();
        gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(arenaBuf, slice[0], slice[1]), gl.STATIC_DRAW);
        return b;
      };
      return {
        ...s,
        bPos: mkBuf(s.pos, gl.ARRAY_BUFFER),
        bNrm: mkBuf(s.nrm, gl.ARRAY_BUFFER),
        bUV:  mkBuf(s.uv,  gl.ARRAY_BUFFER),
        bTri: mkBuf(s.tris, gl.ELEMENT_ARRAY_BUFFER),
        bEdg: mkBuf(s.edges, gl.ELEMENT_ARRAY_BUFFER),
      };
    });
    gpuModels.push({ ...m, surfs });
  }

  setupControls(canvas);
  requestAnimationFrame(loop);
}

function setupControls(canvas) {
  const btnC = document.getElementById('btn-charge');
  const startCharge = () => {
    if (curModelIdx !== 0) setModel(0);
    if (!charging && animMode !== 'blast') {
      charging = true; chargeVal = 0.0; playing = true;
      btnC.classList.add('charging');
    }
  };
  const endCharge = () => {
    if (charging) {
      charging = false;
      btnC.classList.remove('charging');
      animMode = 'blast';
      animFrame = 26.0;
    }
  };
  btnC.addEventListener('mousedown', startCharge);
  window.addEventListener('mouseup', endCharge);
  window.addEventListener('keydown', e => { if (e.code === 'Space' && !e.repeat) { e.preventDefault(); startCharge(); } });
  window.addEventListener('keyup', e => { if (e.code === 'Space') { e.preventDefault(); endCharge(); } });

  document.getElementById('scrub').addEventListener('input', e => {
    playing = false;
    document.getElementById('btn-play').textContent = 'Play';
    animFrame = parseFloat(e.target.value);
  });

  canvas.addEventListener('mousedown', e => { if (!povMode || curModelIdx !== 0) { dragging = true; lx = e.clientX; ly = e.clientY; } });
  window.addEventListener('mousemove', e => {
    if (!dragging) return;
    orbitAz -= (e.clientX - lx) * 0.008;
    orbitEl = Math.max(-1.25, Math.min(1.25, orbitEl + (e.clientY - ly) * 0.008));
    lx = e.clientX; ly = e.clientY;
  });
  window.addEventListener('mouseup', () => dragging = false);
  canvas.addEventListener('wheel', e => { orbitDist = Math.max(16, Math.min(140, orbitDist + e.deltaY * 0.04)); });
}

function setModel(idx) {
  curModelIdx = idx;
  playing = true; charging = false;
  document.getElementById('btn-charge').classList.remove('charging');
  if (idx === 0) { animFrame = 0; animMode = 'idle'; orbitDist = 48.0; orbitAz = 2.45; orbitEl = 0.26; }
  else if (idx === 1) { animFrame = p3Clip.start; orbitDist = 74.0; orbitAz = -0.68; orbitEl = 0.28; }
  else { animFrame = 0; orbitDist = 54.0; orbitAz = -0.95; orbitEl = 0.30; }
  [0,1,2].forEach(i => document.getElementById('tab-' + i).classList.toggle('active', i === idx));
  document.getElementById('scrub').max = Math.max(0, gpuModels[idx].nf - 1);
  document.getElementById('crosshair').style.display = (idx === 0 && povMode) ? 'block' : 'none';
  document.getElementById('charge-hud').style.display = (idx === 0) ? 'block' : 'none';
  document.getElementById('btn-play').textContent = 'Pause';
}

function set3PClip(id, s, e, fps) {
  p3Clip = { id, start: s, end: e, fps };
  ['stand','run','blast','nail'].forEach(k => document.getElementById('p3-' + k).classList.toggle('active', k === id));
  if (curModelIdx !== 1) setModel(1);
  animFrame = s;
  playing = true;
}

function setPov(deg) {
  if (curModelIdx !== 0) setModel(0);
  povMode = true; fovDeg = deg;
  document.getElementById('btn-pov90').classList.toggle('active', deg === 90);
  document.getElementById('btn-pov111').classList.toggle('active', deg === 111);
  document.getElementById('btn-orbit').classList.remove('active');
  document.getElementById('crosshair').style.display = 'block';
}
function setOrbit() {
  povMode = false;
  document.getElementById('btn-pov90').classList.remove('active');
  document.getElementById('btn-pov111').classList.remove('active');
  document.getElementById('btn-orbit').classList.add('active');
  document.getElementById('crosshair').style.display = 'none';
}
function toggleWire() {
  showWire = !showWire;
  document.getElementById('btn-wire').textContent = 'Wireframe: ' + (showWire ? 'ON' : 'OFF');
}
function toggleRanger() {
  showRanger = !showRanger;
  document.getElementById('btn-ranger').textContent = 'Ranger Body: ' + (showRanger ? 'ON' : 'OFF');
  document.getElementById('btn-ranger').classList.toggle('active', showRanger);
}
function togglePlay() {
  playing = !playing;
  document.getElementById('btn-play').textContent = playing ? 'Pause' : 'Play';
}
function triggerFullCycle() {
  if (curModelIdx !== 0) setModel(0);
  playing = true; charging = false; animMode = 'full'; animFrame = 16.0;
  document.getElementById('btn-play').textContent = 'Pause';
}

function drawModel(m, f0, f1, lerp, modelMat, vpMat, camPos) {
  const mvp = mat4Mul(vpMat, modelMat);
  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uMVP'), false, mvp);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uModel'), false, modelMat);
  gl.uniform3fv(gl.getUniformLocation(prog, 'uCamPos'), camPos);
  gl.uniform1f(gl.getUniformLocation(prog, 'uLerp'), lerp);

  for (const s of m.surfs) {
    if (s.name === 'ranger_body' && !showRanger) continue;
    if (s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE); gl.depthMask(false);
    } else {
      gl.disable(gl.BLEND); gl.depthMask(true);
    }
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, gpuTextures[s.tex]);
    gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uMetallic'), s.metallic);
    gl.uniform1f(gl.getUniformLocation(prog, 'uRough'), s.rough);
    gl.uniform1f(gl.getUniformLocation(prog, 'uUnlit'), s.unlit ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 0.0);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bPos);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.SHORT, false, 0, f0 * s.nv * 6);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 3, gl.SHORT, false, 0, f1 * s.nv * 6);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bNrm);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.BYTE, false, 0, f0 * s.nv * 3);
    gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.BYTE, false, 0, f1 * s.nv * 3);

    gl.bindBuffer(gl.ARRAY_BUFFER, s.bUV);
    gl.enableVertexAttribArray(4); gl.vertexAttribPointer(4, 2, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bTri);
    gl.drawElements(gl.TRIANGLES, s.nt * 3, gl.UNSIGNED_SHORT, 0);

    if (showWire && !s.additive) {
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.uniform1f(gl.getUniformLocation(prog, 'uWirePass'), 1.0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, s.bEdg);
      gl.drawElements(gl.LINES, s.ne * 2, gl.UNSIGNED_SHORT, 0);
      gl.disable(gl.BLEND);
    }
  }
  gl.depthMask(true); gl.disable(gl.BLEND);
}

let lastT = performance.now(), jitterPh = 0.0;
function loop(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000.0);
  lastT = now;
  jitterPh += dt * 28.0;

  const canvas = document.getElementById('gl');
  const dpr = window.devicePixelRatio || 1;
  const w = Math.floor(canvas.clientWidth * dpr), h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.clearColor(0.036, 0.048, 0.078, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const m = gpuModels[curModelIdx];
  let f0 = 0, f1 = 0, lerp = 0.0;

  if (curModelIdx === 0) {
    if (charging) {
      chargeVal = Math.min(1.0, chargeVal + dt / 1.15);
      animFrame = (chargeVal >= 0.999) ? (24.4 + 0.55 * (0.5 + 0.5 * Math.sin(jitterPh))) : (16.0 + chargeVal * 9.0);
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      document.getElementById('hud-label').textContent = chargeVal >= 0.99 ? 'BREECH AT +56% MAX SWELL & 3000 RPM! RELEASE!!' : `SWELLING CHROME BREECH & REVVING TIRES... ${(chargeVal*100)|0}%`;
    } else if (playing) {
      if (animMode === 'blast') {
        animFrame += dt * 18.0;
        if (animFrame >= 48.0) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else if (animMode === 'full') {
        animFrame += dt * (animFrame < 26.0 ? 9.5 : 18.0);
        chargeVal = animFrame < 26.0 ? (animFrame - 16.0) / 10.0 : Math.max(0, 1.0 - (animFrame - 26.0) * 0.16);
        if (animFrame >= 48.0) { animMode = 'idle'; animFrame = 0.0; chargeVal = 0.0; }
      } else {
        animFrame = (animFrame + dt * 9.0) % 16.0;
        chargeVal = Math.max(0.0, chargeVal - dt * 2.5);
      }
      document.getElementById('charge-fill').style.width = (chargeVal * 100).toFixed(1) + '%';
      if (animMode === 'idle') document.getElementById('hud-label').textContent = 'READY · HOLD SPACE TO SWELL BREECH & REV WHEELS!';
      else document.getElementById('hud-label').textContent = animFrame < 30 ? 'TRUMPET-BELL BLAST & +25° WHEELIE!!' : (animFrame < 40 ? 'BARBELL-AXLE BOING WHIPLASH!' : 'CHROME BREECH GULP RELOAD');
    }
    f0 = Math.max(0, Math.min(47, Math.floor(animFrame)));
    if (animMode === 'idle' && !charging && f0 === 15) f1 = 0;
    else f1 = (f0 + 1 < 48) ? f0 + 1 : 0;
    lerp = animFrame - Math.floor(animFrame);
  } else if (curModelIdx === 1) {
    const span = (p3Clip.end - p3Clip.start + 1);
    if (playing) {
      animFrame = p3Clip.start + ((animFrame - p3Clip.start + dt * p3Clip.fps) % span);
    }
    f0 = Math.max(0, Math.min(m.nf - 1, Math.floor(animFrame)));
    f1 = (f0 >= p3Clip.start && f0 <= p3Clip.end) ? (p3Clip.start + ((f0 - p3Clip.start + 1) % span)) : ((f0 + 1) % m.nf);
    lerp = animFrame - Math.floor(animFrame);
  } else {
    if (playing && !dragging) spinTurntable += dt * 1.15;
    f0 = 0; f1 = 0; lerp = 0.0;
  }

  document.getElementById('scrub').value = f0;
  const fname = PAYLOAD.frameNames[curModelIdx][f0] || ('f' + f0);
  document.getElementById('frame-lbl').textContent = `f${String(f0).padStart(3,'0')} · ${fname}`;

  const asp = w / Math.max(1, h);
  let camPos, viewMat, projMat, modelMat = mat4RotZ(0.0);
  if (curModelIdx === 0 && povMode) {
    const fovX = fovDeg * Math.PI / 180.0;
    const fovY = 2.0 * Math.atan(Math.tan(fovX * 0.5) / asp);
    projMat = mat4Persp(fovY, asp, 0.5, 900.0);
    camPos = [0, 0, 0];
    viewMat = mat4LookAt(camPos, [24, 0, 0], [0, 0, 1]);
  } else {
    projMat = mat4Persp(46.0 * Math.PI / 180.0, asp, 0.5, 900.0);
    const ctr = curModelIdx === 0 ? [26, -3, -5] : (curModelIdx === 1 ? [2, 0, 8] : [0, 0, 15]);
    camPos = [
      ctr[0] + orbitDist * Math.cos(orbitEl) * Math.cos(orbitAz),
      ctr[1] + orbitDist * Math.cos(orbitEl) * Math.sin(orbitAz),
      ctr[2] + orbitDist * Math.sin(orbitEl)
    ];
    viewMat = mat4LookAt(camPos, ctr, [0, 0, 1]);
    if (curModelIdx === 2) modelMat = mat4RotZ(spinTurntable);
  }
  const vpMat = mat4Mul(projMat, viewMat);
  drawModel(m, f0, f1, lerp, modelMat, vpMat, camPos);

  requestAnimationFrame(loop);
}
init();
</script>
</body>
</html>
"""


def main():
    stitch_contact_sheet()

    tex_files = ["rod_chrome.png", "rod_wheel.png", "rod_hand.png", "rod_fx.png"]
    tex_list = [encode_pil_rgba(Image.open(os.path.join(TEX_DIR, fn)), fn) for fn in tex_files]
    tmap = {fn: i for i, fn in enumerate(tex_files)}

    surf_tex = {
        "rod_chrome":   tmap["rod_chrome.png"],
        "rod_wheel":    tmap["rod_wheel.png"],
        "ranger_hands": tmap["rod_hand.png"],
        "rod_fx":       tmap["rod_fx.png"],
    }
    surf_style = {
        "rod_chrome":   dict(metallic=0.95, rough=0.11, unlit=False, additive=False),
        "rod_wheel":    dict(metallic=0.14, rough=0.45, unlit=False, additive=False),
        "ranger_hands": dict(metallic=0.22, rough=0.52, unlit=False, additive=False),
        "rod_fx":       dict(metallic=0.00, rough=0.45, unlit=True,  additive=True),
    }

    meta = json.loads(open(os.path.join(OUT_ROOT, "rod_meta.json"), encoding="utf-8").read())
    arena = bytearray()
    m_vm = pack_md3_surfaces(os.path.join(STAGE_DIR, "v_rodcannon.md3"), arena, surf_tex, surf_style)
    m_3p = pack_md3_surfaces(os.path.join(STAGE_DIR, "p_rodcannon.md3"), arena, surf_tex, surf_style)
    m_pk = pack_md3_surfaces(os.path.join(STAGE_DIR, "g_rodcannon.md3"), arena, surf_tex, surf_style)

    ranger_tex_idx = len(tex_list)
    ranger_surf, ranger_skin_im, fn_player = pack_ranger_vwep_surface(arena, ranger_tex_idx)
    r_tex_entry = encode_pil_rgba(ranger_skin_im, "ranger_skin.png")
    r_tex_entry["nearest"] = True
    tex_list.append(r_tex_entry)
    m_3p["surfaces"].insert(0, ranger_surf)

    gz = gzip.compress(bytes(arena), compresslevel=9)
    payload = dict(
        binGz=base64.b64encode(gz).decode("ascii"),
        textures=tex_list,
        models=[m_vm, m_3p, m_pk],
        frameNames=[meta["frameNames"], fn_player, ["pickup1"]],
    )
    html = HTML_TEMPLATE.replace("/*__ROD_DATA__*/null", json.dumps(payload, separators=(",", ":")))
    open(HTML_OUT, "w", encoding="utf-8").write(html)
    print(f"[HTML OK] Wrote {HTML_OUT} ({os.path.getsize(HTML_OUT) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
