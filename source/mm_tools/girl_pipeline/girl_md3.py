"""baked_{hi,lo}.npz + atlas_{hi,lo}.png -> progs/girl.md3 (8-frame run bob) + progs/girl.png, progs/v_banana.md3 (16 frames) + progs/v_banana.png.
python -I girl_md3.py <progs dir>"""
import sys, math
import numpy as np, cv2
sys.path.insert(0, "G:/Quake/Combat/BakersfieldQuake/source/mm_tools")
import md3lib

OUT = sys.argv[1]
H_WORLD = 54.0           # standing height in Quake units (the player is 56)


def load(tag):
    d = np.load(f"baked_{tag}.npz")
    return d["V"], d["F"], d["fu"], d["fv"]


def to_quake(V, height):
    s = height / (V[:, 1].max() - V[:, 1].min())
    return np.stack([V[:, 2], V[:, 0], V[:, 1] - V[:, 1].min()], 1) * s     # x forward, y left, z up (same handedness)


def vnormals(P, F):
    t = P[F]
    fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    N = np.zeros_like(P)
    for q in range(3):
        np.add.at(N, F[:, q], fn)
    return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)


def surfaces(P, N, F, fu, fv, rows, shader, frames_fn, nframes):
    """split into <=4000-vertex surfaces; frames_fn(points)->list of nframes arrays (normals rotated alike)"""
    order = np.argsort(P[F].mean(1)[:, 2])
    surfs = []
    cur = {}
    cf = []

    def flush():
        if not cf:
            return
        keys = list(cur.keys())
        vi = np.array([k[0] for k in keys])
        st = [(k[1] / 4096.0, k[2] / float(rows)) for k in keys]
        fr = frames_fn(P[vi], N[vi])
        surfs.append(dict(name="girl%d" % len(surfs), shader=shader, tris=list(cf), st=st,
                          frames=[([tuple(p) for p in pp], [tuple(n) for n in nn]) for pp, nn in fr]))
    for f in order:
        ids = []
        for q in range(3):
            k = (int(F[f, q]), round(float(fu[f, q]), 1), round(float(fv[f, q]), 1))
            ids.append(k)
        new = sum(1 for k in ids if k not in cur)
        if len(cur) + new > 4000:
            flush()
            cur.clear()
            cf.clear()
        tri = []
        for k in ids:
            if k not in cur:
                cur[k] = len(cur)
            tri.append(cur[k])
        cf.append((tri[0], tri[2], tri[1]))   # DarkPlaces wants the other winding
    flush()
    return surfs


def rot(pitch=0.0, roll=0.0, yaw=0.0):
    """pitch + = lean forward (head toward +x), roll + = lean to her left, about the origin (the feet)"""
    p, r, y = math.radians(pitch), math.radians(roll), math.radians(yaw)
    Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def make_atlas(tag, name):
    a = cv2.imread(f"atlas_{tag}.png")
    rows = int(np.nonzero(a.reshape(a.shape[0], -1).max(1) > 0)[0].max()) + 2
    rows = min(a.shape[0], int(math.ceil(rows / 8.0) * 8))
    a = a[:rows]
    cv2.imwrite(OUT + "/" + name, cv2.resize(a, (2048, rows // 2), interpolation=cv2.INTER_AREA))
    return rows


# ------------------------------------------------------------ projectile / third-person model: 8-frame run bob
V, F, fu, fv = load("hi")
P = to_quake(V, H_WORLD)
N = vnormals(P, F)
rows = make_atlas("hi", "girl.png")


def run_frames(pts, nrm):
    out = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        R = rot(pitch=7, roll=4 * math.sin(ph), yaw=3 * math.sin(ph))
        bob = np.array([0, 0, 1.3 * abs(math.sin(ph))])
        out.append((pts @ R.T + bob, nrm @ R.T))
    return out


S = surfaces(P, N, F, fu, fv, rows, "progs/girl", run_frames, 8)
md3lib.write(OUT + "/girl.md3", dict(name="girl", surfaces=S))
print("girl.md3 surfaces", [(len(s['st']), len(s['tris'])) for s in S])

# ------------------------------------------------------------ held view model (the girl in your hand): 0-7 idle sway, 8-15 throw
V, F, fu, fv = load("lo")
P = to_quake(V, 8.0)
N = vnormals(P, F)
rows = make_atlas("lo", "v_banana.png")
HOLD = np.array([11.0, -8.0, -12.5])


def held_frames(pts, nrm):
    out = []
    for i in range(16):
        if i < 8:
            ph = 2 * math.pi * i / 8
            R = rot(pitch=-5 + 3 * math.sin(ph), roll=5 * math.sin(ph + 1.0), yaw=160 + 4 * math.sin(ph))
            off = HOLD + np.array([0, 0, 0.5 * math.sin(ph)])
            sc = 1.0
        else:
            j = i - 8     # 0..7 over the 0.5 s after the button goes down; she leaves at ~0.1 s (j 1-2)
            seq = [(-30, 0, -15, [-3, 0, 1], 1.0), (-70, 0, 0, [-6, 0, 3], 1.0), (25, 0, 0, [14, 0, 3], 1.0),
                   (40, 0, 0, [30, 0, 2], 0.0), (0, 0, 0, [0, 0, -40], 0.0), (0, 0, 0, [0, 0, -40], 0.0),
                   (0, 0, 0, [0, 0, -40], 0.0), (-10, 0, -15, [0, 0, -5], 0.7)]
            pi_, ro, ya, of, sc = seq[j]; ya = ya + 160
            R = rot(pitch=pi_, roll=ro, yaw=ya)
            off = HOLD + np.array(of, float)
        sc = max(sc, 0.001)
        out.append(((pts * sc) @ R.T + off, nrm @ R.T))
    return out


S = surfaces(P, N, F, fu, fv, rows, "progs/v_banana", held_frames, 16)
md3lib.write(OUT + "/v_banana.md3", dict(name="v_banana", surfaces=S))
print("v_banana.md3 surfaces", [(len(s['st']), len(s['tris'])) for s in S])
