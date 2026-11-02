"""NetSend PC: the CRT screen as its own model (owner's review 2026-10-31: "the skin is messed up ... wheres the correct screen?").
In DarkPlaces the screen surface inside progs/netsend_pc.md3 samples its texture wrongly (a four-colour test card came out
as one solid colour, the Win98 dialog as stairs), while the same surface in a model of its own draws right. So the screen is
a second entity (NS_Think in netsend.qc keeps its frame, skin, origin and angles equal to the PC's).
Reads the screen surface (all 50 frames) out of progs/netsend_pc.md3 and writes progs/netsend_scr.md3 (the glass pushed
0.25 units toward the viewer so it covers the PC's own surface) and progs/netsend_scr.md3_0..6.skin (the same screen
shaders as the PC's skins, scripts/netsend.shader).
usage: python build_netsend_screen.py   (run after build_netsend_assets.py; the PC model is not changed)"""
import os
import struct

import md3lib

HERE = os.path.dirname(os.path.abspath(__file__))
PROGS = os.path.join(HERE, "..", "..", "progs")
PUSH = 0.25
SHADERS = ["loop", "off", "noise", "init", "lol", "first", "dot"]		# skin 0..6, as in build_netsend_assets.py


def main():
    d = open(os.path.join(PROGS, "netsend_pc.md3"), "rb").read()
    _, _, _, _, nf, _, ns, _, _, _, ofss, _ = struct.unpack("<4si64s9i", d[:108])
    o = ofss
    for _ in range(ns):
        h = struct.unpack("<4s64s10i", d[o:o + 108])
        name = h[1].split(b"\0")[0].decode()
        _, _, _, nv, nt, ofs_t, _, ofs_st, ofs_xyz, ofs_end = h[2:]
        if name == "netsend_screen":
            st = [struct.unpack("<2f", d[o + ofs_st + j * 8:o + ofs_st + j * 8 + 8]) for j in range(nv)]
            tris = [struct.unpack("<3i", d[o + ofs_t + j * 12:o + ofs_t + j * 12 + 12]) for j in range(nt)]
            frames = []
            for f in range(nf):
                vs, ns_ = [], []
                for j in range(nv):
                    x, y, z, n = struct.unpack("<3hH", d[o + ofs_xyz + (f * nv + j) * 8:o + ofs_xyz + (f * nv + j) * 8 + 8])
                    vs.append((x / 64.0 + PUSH, y / 64.0, z / 64.0))
                    ns_.append(md3lib.dec_normal(n))
                frames.append((vs, ns_))
            surf = dict(name="netsend_screen", shader="progs/netsend_scr_loop", tris=tris, st=st, frames=frames)
            md3lib.write(os.path.join(PROGS, "netsend_scr.md3"), dict(name="netsend_scr", surfaces=[surf], nframes=nf))
            print("wrote progs/netsend_scr.md3: %d frames, %d verts, %d tris" % (nf, nv, nt))
        o += ofs_end
    for i, sh in enumerate(SHADERS):
        with open(os.path.join(PROGS, "netsend_scr.md3_%d.skin" % i), "w", newline="\n") as f:
            f.write("netsend_screen,progs/netsend_scr_%s\n" % sh)
    print("wrote progs/netsend_scr.md3_0..6.skin")


if __name__ == "__main__":
    main()
