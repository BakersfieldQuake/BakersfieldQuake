"""Builds progs/v_megaman.md3 (first-person Mega Man weapon) + progs/mm_hand.png.

A gloved fist (no arm) holds Mega Man by the metal pipe, wheels towards you. The pipe + axle + wheels come from
mm_parts.json (megaman1.glb, see prep_model.py). The MD3 is a vertex-animated model:

  frames  0-15   idle loop (gentle bob, wheels turn)          -> 10 fps from QC
  frames 16-19   wind up, thrust, release (Mega Man flies off)
  frames 20-21   empty open hand
  frames 22-25   a fresh Mega Man pops up into the hand

python -I build_viewmodel.py <mm_parts.json> <outdir> [previewdir]
"""
import json, math, os, struct, sys, zlib

parts_json, outdir = sys.argv[1:3]
previewdir = sys.argv[3] if len(sys.argv) > 3 else None

# ---------------------------------------------------------------- tuning
def _env(name, default):
    v = os.environ.get(name)
    return tuple(float(x) for x in v.split(",")) if v and "," in v else (float(v) if v else default)

SCALE = _env("MM_SCALE", 0.5)                 # model units -> view units
BASE = _env("MM_BASE", (10.5, -14.0, -10.0))  # where the grip sits in front of the eye (x fwd, y left, z up)
YAW = _env("MM_YAW", 21.0)                    # turns the whole thing towards the crosshair
POSE_PITCH = _env("MM_PITCH", 60.0)           # lifts the pipe so it points up towards the crosshair
ARM = os.environ.get("MM_ARM", "0") == "1"    # 1 = sleeve and cuff too; default is just the fist
ROLL = _env("MM_ROLL", 0.0)                   # extra roll about the forward axis (pov_tuner.html)
TILT = _env("MM_TILT", 0.0)                   # extra pitch applied after the pose (pov_tuner.html)
HAND_SCALE = _env("MM_HAND_SCALE", 0.7)       # fist size, about the grip point
HAND_SLIDE = _env("MM_HAND_SLIDE", -20.0)       # fist position along the pipe, pose units
FINGER_LEN = 9.0
NFRAMES = 26

# ---------------------------------------------------------------- vector helpers
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    l = length(a) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)

def rot_y(p, deg):
    """+deg lifts +X towards +Z (nose up)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)

def rot_x(p, deg):
    """+deg lifts +Y (left) towards +Z."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)

def rot_z(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])

# ---------------------------------------------------------------- the Mega Man parts
parts = json.load(open(parts_json))
info = parts.pop("_info")
CX, CZ = info["axis_center_x"], info["axis_center_z"]

body_v = parts["body"]["verts"]
# pipe axis: cap end (top/back) to nose end (low/front), measured from the mesh
CAP = (-11.7, 0.3, 20.3)
NOSE = (14.6, 0.0, 3.2)
PIPE_A = norm(sub(NOSE, CAP))
pipe_len = length(sub(NOSE, CAP))

def dist_to_axis(p):
    d = sub(p, CAP)
    t = dot(d, PIPE_A)
    return length(sub(d, mul(PIPE_A, t))), t / pipe_len

radii = [r for r, t in (dist_to_axis(p) for p in body_v) if True]
near = [dist_to_axis(p)[0] for p in body_v if 0.05 < dist_to_axis(p)[1] < 0.3]
PIPE_R = (sum(near) / len(near)) * SCALE if near else 1.5 * SCALE
print("pipe radius (view units)", round(PIPE_R, 3), "samples", len(near))

GRIP_M = add(CAP, mul(PIPE_A, 5.0))          # grip point on the pipe, model space

def spin(p, theta):
    x, y, z = p
    dx, dz = x - CX, z - CZ
    c, s = math.cos(theta), math.sin(theta)
    return (CX + dx * c + dz * s, y, CZ - dx * s + dz * c)

def spin_n(n, theta):
    x, y, z = n
    c, s = math.cos(theta), math.sin(theta)
    return (x * c + z * s, y, -x * s + z * c)

# ---------------------------------------------------------------- frame table
# obj = Mega Man (pitch deg, dx, dz, wheel spin deg); hand = (pitch, dx, dz); curl 0..1; tcurl 0..1
FR = []
for i in range(16):
    ph = 2 * math.pi * i / 16
    FR.append(dict(op=5.0 * math.sin(ph), ox=0.0, oz=1.3 * math.sin(ph + 0.6), spin=i * 22.5,
                   hp=1.8 * math.sin(ph), hx=0.0, hz=0.4 * math.sin(ph + 0.6), curl=1.0, tcurl=1.0))
FR += [
    dict(op=20.0, ox=-3.0, oz=2.5, spin=40.0, hp=10.0, hx=-3.0, hz=1.0, curl=1.0, tcurl=1.0),     # 16 wind up
    dict(op=32.0, ox=-6.5, oz=3.5, spin=100.0, hp=18.0, hx=-5.5, hz=1.5, curl=1.0, tcurl=1.0),    # 17 wind up more
    dict(op=-14.0, ox=11.0, oz=-1.0, spin=200.0, hp=-9.0, hx=9.0, hz=-0.5, curl=0.55, tcurl=0.6),  # 18 thrust
    dict(op=-18.0, ox=95.0, oz=6.0, spin=330.0, hp=-11.0, hx=10.0, hz=-0.5, curl=0.0, tcurl=0.0),  # 19 released
    dict(op=0.0, ox=60.0, oz=-70.0, spin=0.0, hp=-5.0, hx=4.0, hz=-1.0, curl=0.0, tcurl=0.0),     # 20 hand only
    dict(op=0.0, ox=0.0, oz=-60.0, spin=0.0, hp=-1.5, hx=0.5, hz=-1.0, curl=0.1, tcurl=0.1),      # 21 hand only
    dict(op=-6.0, ox=0.0, oz=-26.0, spin=60.0, hp=0.0, hx=0.0, hz=-0.5, curl=0.35, tcurl=0.3),     # 22 pops up
    dict(op=4.0, ox=0.0, oz=-8.0, spin=150.0, hp=1.0, hx=0.0, hz=0.0, curl=0.75, tcurl=0.7),      # 23
    dict(op=-3.0, ox=0.0, oz=2.2, spin=250.0, hp=-0.5, hx=0.0, hz=0.3, curl=1.0, tcurl=1.0),      # 24 overshoot
    dict(op=2.0, ox=0.0, oz=-0.5, spin=330.0, hp=0.5, hx=0.0, hz=-0.2, curl=1.0, tcurl=1.0),      # 25 settle
]
assert len(FR) == NFRAMES

def to_view(p, pitch, dx, dz):
    """pose-space point (grip at origin) -> eye space"""
    q = rot_y(p, pitch)
    q = (q[0] + dx, q[1], q[2] + dz)
    q = rot_y(rot_x(q, ROLL), TILT)
    q = mul(q, SCALE)
    q = rot_z(q, YAW)
    return add(q, BASE)

def to_view_n(n, pitch):
    return norm(rot_z(rot_y(rot_x(rot_y(n, pitch), ROLL), TILT), YAW))

# ---------------------------------------------------------------- mesh primitives
SWATCH = {"sleeve": 0, "cuff": 1, "glove": 2, "knuckle": 3, "dark": 4}

def uv_of(name):
    return ((SWATCH[name] * 8 + 4) / 64.0, 0.5)

def frame_basis(t):
    t = norm(t)
    ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = norm(cross(t, ref))
    v = cross(t, u)
    return t, u, v

def tube(points, radii, swatch, sides=8):
    """sweep a circle along the polyline, with pointed end caps"""
    verts, norms, tris = [], [], []
    n = len(points)
    tans = []
    for i in range(n):
        a = points[max(i - 1, 0)]
        b = points[min(i + 1, n - 1)]
        tans.append(norm(sub(b, a)))
    rings = []
    # start cap
    c0 = sub(points[0], mul(tans[0], radii[0] * 0.8))
    verts.append(c0); norms.append(mul(tans[0], -1.0))
    ring0 = 1
    for i in range(n):
        t, u, v = frame_basis(tans[i])
        rings.append(len(verts))
        for k in range(sides):
            ang = 2 * math.pi * k / sides
            d = add(mul(u, math.cos(ang)), mul(v, math.sin(ang)))
            verts.append(add(points[i], mul(d, radii[i])))
            norms.append(d)
    c1 = add(points[-1], mul(tans[-1], radii[-1] * 0.8))
    cap1 = len(verts)
    verts.append(c1); norms.append(tans[-1])
    for k in range(sides):
        k2 = (k + 1) % sides
        tris.append([0, rings[0] + k2, rings[0] + k])
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            a, b, c, d = rings[i] + k, rings[i] + k2, rings[i + 1] + k2, rings[i + 1] + k
            tris.append([a, b, c]); tris.append([a, c, d])
    for k in range(sides):
        k2 = (k + 1) % sides
        tris.append([cap1, rings[-1] + k, rings[-1] + k2])
    return verts, norms, tris, [uv_of(swatch)] * len(verts)

def ellipsoid(center, ax, ay, az, rx, ry, rz, swatch, segs=10, rings=7):
    """axes ax/ay/az are orthonormal; rx/ry/rz the half extents"""
    verts, norms, tris = [], [], []
    for r in range(rings + 1):
        th = math.pi * r / rings
        for s in range(segs):
            ph = 2 * math.pi * s / segs
            x, y, z = math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)
            p = add(center, add(add(mul(ax, x * rx), mul(ay, y * ry)), mul(az, z * rz)))
            nn = add(add(mul(ax, x / rx), mul(ay, y / ry)), mul(az, z / rz))
            verts.append(p); norms.append(norm(nn))
    for r in range(rings):
        for s in range(segs):
            s2 = (s + 1) % segs
            a, b = r * segs + s, r * segs + s2
            c, d = (r + 1) * segs + s2, (r + 1) * segs + s
            tris.append([a, c, b]); tris.append([a, d, c])
    return verts, norms, tris, [uv_of(swatch)] * len(verts)

# ---------------------------------------------------------------- the hand, in pose space (grip at origin)
A = norm(rot_y(PIPE_A, POSE_PITCH))              # pipe axis after the pose pitch
U = norm(cross((0.0, 1.0, 0.0), A))              # perpendicular, pointing "up"
U = U if U[2] > 0 else mul(U, -1.0)
E1 = (0.0, -1.0, 0.0)                            # towards the palm side (right of the pipe)
E2 = mul(U, -1.0)                                # towards the bottom of the pipe
RP = PIPE_R / SCALE                              # pipe radius in pose units
RF = RP + 1.0                                    # finger centre-line radius
FORE = norm((-0.80, -0.38, -0.46))               # wrist -> elbow, back, right and down

def radial(psi):
    return add(mul(E1, math.cos(psi)), mul(E2, math.sin(psi)))

def tangent(psi):
    return add(mul(E1, -math.sin(psi)), mul(E2, math.cos(psi)))

def finger_points(s_along, psi0, direction, curl, length_, steps=4):
    """turtle walk in the pipe cross-section: wraps the pipe when curl=1, straight when 0"""
    pos2 = (RF * math.cos(psi0), RF * math.sin(psi0))
    head = (-math.sin(psi0) * direction, math.cos(psi0) * direction)
    pts = []
    ds = length_ / steps
    kappa = direction * curl / RF
    ang = math.atan2(head[1], head[0])
    for i in range(steps + 1):
        pts.append(add(add(mul(A, s_along), mul(E1, pos2[0])), mul(E2, pos2[1])))
        ang += kappa * ds
        pos2 = (pos2[0] + math.cos(ang) * ds, pos2[1] + math.sin(ang) * ds)
    return pts

def hand_surfaces(curl, tcurl):
    out = []
    palm_c = mul(E1, RP + 1.4)
    out.append(("palm",) + ellipsoid(palm_c, A, E2, E1, 4.6, 3.1, 1.7, "glove", 12, 8))
    out.append(("knuckles",) + ellipsoid(add(palm_c, add(mul(E1, 0.6), mul(E2, 2.6))), A, E2, E1, 4.9, 1.5, 1.45, "knuckle", 10, 6))
    # forearm (sleeve) + cuff
    wrist = add(palm_c, mul(E1, 1.2))
    fore_pts = [add(wrist, mul(FORE, 1.5)), add(wrist, mul(FORE, 9)), add(wrist, mul(FORE, 20)), add(wrist, mul(FORE, 40))]
    if ARM:
        out.append(("sleeve",) + tube(fore_pts, [2.5, 2.9, 3.8, 5.6], "sleeve", 10))
        cuff_pts = [add(wrist, mul(FORE, 3.6)), add(wrist, mul(FORE, 5.4))]
        out.append(("cuff",) + tube(cuff_pts, [3.0, 3.0], "cuff", 10))
    else:
        # just a short glove cuff closing off the wrist
        out.append(("cuff",) + tube([add(wrist, mul(FORE, 1.0)), add(wrist, mul(FORE, 3.2))], [2.6, 2.9], "cuff", 10))
    # four fingers, side by side along the pipe
    for i, s in enumerate((-3.1, -1.05, 1.0, 3.05)):
        L = FINGER_LEN * (0.92 if i in (0, 3) else 1.0)
        pts = finger_points(s, math.radians(38), +1, curl, L)
        rads = [1.0, 0.95, 0.9, 0.85, 0.75]
        out.append(("finger%d" % i,) + tube(pts, rads, "glove", 7))
    # thumb comes over the top from the other side
    tpts = finger_points(4.2, math.radians(-40), -1, tcurl, 7.0)
    out.append(("thumb",) + tube(tpts, [1.15, 1.05, 0.95, 0.85, 0.75], "knuckle", 7))
    return out

# ---------------------------------------------------------------- assemble the surfaces
surfaces = []          # (name, shader, uvs, tris, [frame] -> (verts, norms))

# Mega Man parts (progs/megaman texture)
for gname, g in parts.items():
    frames = []
    for f in FR:
        th = math.radians(f["spin"]) if gname != "body" else 0.0
        vv, nn = [], []
        for v, n in zip(g["verts"], g["norms"]):
            p = tuple(v); nrm = tuple(n)
            if gname != "body":
                p = spin(p, th); nrm = spin_n(nrm, th)
            p = rot_y(sub(p, GRIP_M), POSE_PITCH)
            nrm = rot_y(nrm, POSE_PITCH)
            vv.append(to_view(p, f["op"], f["ox"], f["oz"]))
            nn.append(to_view_n(nrm, f["op"]))
        frames.append((vv, nn))
    surfaces.append((gname, "progs/megaman", [tuple(u) for u in g["uvs"]], [list(t) for t in g["tris"]], frames))

# hand parts (progs/mm_hand texture), topology identical in every frame
hand_frames = [hand_surfaces(f["curl"], f["tcurl"]) for f in FR]
for si in range(len(hand_frames[0])):
    name = hand_frames[0][si][0]
    uvs = hand_frames[0][si][4]
    tris = hand_frames[0][si][3]
    frames = []
    for fi, f in enumerate(FR):
        _, vv, nn, _, _ = hand_frames[fi][si]
        assert len(vv) == len(uvs), name
        frames.append(([to_view(add(mul(p, HAND_SCALE), mul(A, HAND_SLIDE)), f["hp"], f["hx"], f["hz"]) for p in vv], [to_view_n(n, f["hp"]) for n in nn]))
    surfaces.append((name, "progs/mm_hand", uvs, tris, frames))

# ---------------------------------------------------------------- pose-space export for pov_tuner.html
if os.environ.get("MM_EXPORT"):
    SW_RGB = [(30, 94, 208), (84, 212, 240), (62, 146, 236), (138, 214, 248), (18, 46, 118)]
    def r3(v): return round(v, 3)
    out = {"parts": []}
    ctr = rot_y(sub((CX, 0.0, CZ), GRIP_M), POSE_PITCH)
    out["axis_center"] = [r3(c) for c in ctr]
    out["pipe_axis"] = [r3(c) for c in A]
    for gname, g in parts.items():
        vv = [rot_y(sub(tuple(v), GRIP_M), POSE_PITCH) for v in g["verts"]]
        nn = [rot_y(tuple(n), POSE_PITCH) for n in g["norms"]]
        out["parts"].append({"name": gname, "kind": "mm", "wheel": gname != "body",
                             "v": [r3(c) for p in vv for c in p], "n": [r3(c) for p in nn for c in norm(p)],
                             "uv": [r3(c) for u in g["uvs"] for c in u], "i": [i for t in g["tris"] for i in t]})
    for name, vv, nn, tris, uvs in hand_surfaces(1.0, 1.0):
        sw = int(uvs[0][0] * 8)
        out["parts"].append({"name": name, "kind": "hand", "wheel": False, "color": SW_RGB[sw],
                             "v": [r3(c) for p in vv for c in p], "n": [r3(c) for p in nn for c in norm(p)],
                             "i": [i for t in tris for i in t]})
    out["defaults"] = {"scale": SCALE, "pos": list(BASE), "yaw": YAW, "tilt": TILT, "roll": ROLL,
                       "hand_scale": HAND_SCALE, "hand_slide": HAND_SLIDE, "arm": ARM}
    json.dump(out, open(os.environ["MM_EXPORT"], "w"), separators=(",", ":"))
    print("exported", os.environ["MM_EXPORT"], os.path.getsize(os.environ["MM_EXPORT"]), "bytes")

# ---------------------------------------------------------------- MD3 writer
def name64(s):
    return s.encode("ascii")[:63].ljust(64, b"\0")

def i16(v):
    return max(-32768, min(32767, int(round(v * 64))))

def enc_normal(n):
    x, y, z = norm(n)
    lng = int(round(math.acos(max(-1.0, min(1.0, z))) * 255 / (2 * math.pi))) & 255
    lat = int(round(math.atan2(y, x) * 255 / (2 * math.pi))) & 255
    return (lng << 8) | lat

fmin = [[1e9] * 3 for _ in range(NFRAMES)]
fmax = [[-1e9] * 3 for _ in range(NFRAMES)]
blobs = []
for name, shader, uvs, tris, frames in surfaces:
    nv, nt = len(uvs), len(tris)
    tri_blob = b"".join(struct.pack("<3i", *t) for t in tris)
    shader_blob = name64(shader) + struct.pack("<i", 0)
    st_blob = b"".join(struct.pack("<2f", u, v) for u, v in uvs)
    xyz = []
    for fi, (vv, nn) in enumerate(frames):
        assert len(vv) == nv
        for p, n in zip(vv, nn):
            for k in range(3):
                fmin[fi][k] = min(fmin[fi][k], p[k]); fmax[fi][k] = max(fmax[fi][k], p[k])
            xyz.append(struct.pack("<3hH", i16(p[0]), i16(p[1]), i16(p[2]), enc_normal(n)))
    xyz_blob = b"".join(xyz)
    hdr_size = 4 + 64 + 4 * 10
    ofs_tri = hdr_size
    ofs_shader = ofs_tri + len(tri_blob)
    ofs_st = ofs_shader + len(shader_blob)
    ofs_xyz = ofs_st + len(st_blob)
    ofs_end = ofs_xyz + len(xyz_blob)
    hdr = b"IDP3" + name64(name) + struct.pack("<10i", 0, NFRAMES, 1, nv, nt, ofs_tri, ofs_shader, ofs_st, ofs_xyz, ofs_end)
    blobs.append(hdr + tri_blob + shader_blob + st_blob + xyz_blob)

frames_blob = b""
for fi in range(NFRAMES):
    mn, mx = fmin[fi], fmax[fi]
    rad = max(math.sqrt(a * a + b * b + c * c) for a in (mn[0], mx[0]) for b in (mn[1], mx[1]) for c in (mn[2], mx[2]))
    frames_blob += struct.pack("<3f3f3ff", *mn, *mx, 0.0, 0.0, 0.0, rad) + name64("f%d" % fi)[:16]

HDR = 4 + 4 + 64 + 4 * 9
ofs_frames = HDR
ofs_tags = ofs_frames + len(frames_blob)
total = ofs_tags + sum(len(b) for b in blobs)
header = b"IDP3" + struct.pack("<i", 15) + name64("v_megaman") + struct.pack("<9i", 0, NFRAMES, 0, len(blobs), 0, ofs_frames, ofs_tags, ofs_tags, total)
assert len(header) == HDR
os.makedirs(os.path.join(outdir, "progs"), exist_ok=True)
outp = os.path.join(outdir, "progs", "v_megaman.md3")
open(outp, "wb").write(header + frames_blob + b"".join(blobs))
print("wrote", outp, os.path.getsize(outp), "bytes;", sum(len(s[3]) for s in surfaces), "tris;", NFRAMES, "frames")

# ---------------------------------------------------------------- hand texture (8 swatches of 8x8)
SW = [(30, 94, 208), (84, 212, 240), (62, 146, 236), (138, 214, 248), (18, 46, 118), (255, 255, 255), (255, 255, 255), (255, 255, 255)]
SW = [tuple(int(c * 0.42) for c in col) for col in SW]   # the engine lights models ~2.4x too bright for these colours
W, H = 64, 8
raw = b""
for y in range(H):
    raw += b"\0"
    for x in range(W):
        raw += bytes(SW[x // 8])

def png_chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")
open(os.path.join(outdir, "progs", "mm_hand.png"), "wb").write(png)

# ---------------------------------------------------------------- preview dumps (OBJ, blender axes: X=-y, Y=x, Z=z)
if previewdir:
    os.makedirs(previewdir, exist_ok=True)
    for fi in range(NFRAMES):
        lines = []
        base = 1
        for name, shader, uvs, tris, frames in surfaces:
            vv, nn = frames[fi]
            lines.append("o %s__%s" % (name, "mm" if shader.endswith("megaman") else "hand"))
            for p in vv:
                lines.append("v %.4f %.4f %.4f" % (-p[1], p[0], p[2]))
            for t in tris:
                lines.append("f %d %d %d" % (t[0] + base, t[1] + base, t[2] + base))
            base += len(vv)
        open(os.path.join(previewdir, "f%02d.obj" % fi), "w").write("\n".join(lines) + "\n")
    print("preview OBJs in", previewdir)
