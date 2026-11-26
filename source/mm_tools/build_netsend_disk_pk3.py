"""Pack zz_netsend_disk.pk3 from the game files that build_netsend_disk_view.py (--game-set X) and
build_netsend_disk_proj.py write into build/netsend_disk/game: THE DISK held model (card MD3, its .skin files and
frames, scripts/netsend_diskvm.shader) and the new projectile (progs/netsend_disk.md3 + .png).
Reproducible (AGENTS.md): fixed timestamps and attributes, sorted entries, png stored, the rest deflated at level 9.

python3 build_netsend_disk_pk3.py [--game build/netsend_disk/game] [--out build/netsend_disk/zz_netsend_disk.pk3]
"""
import argparse
import hashlib
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=os.path.join(REPO, "build", "netsend_disk", "game"))
    ap.add_argument("--out", default=os.path.join(REPO, "build", "netsend_disk", "zz_netsend_disk.pk3"))
    args = ap.parse_args()
    names = []
    for root, _, files in os.walk(args.game):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), args.game).replace(os.sep, "/")
            if rel.startswith(("progs/", "scripts/")):
                names.append(rel)
    names.sort()
    tmp = args.out + ".tmp"
    with zipfile.ZipFile(tmp, "w") as z:
        for n in names:
            zi = zipfile.ZipInfo(n, date_time=(1980, 1, 1, 0, 0, 0))
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            data = open(os.path.join(args.game, n), "rb").read()
            if n.endswith(".png"):
                zi.compress_type = zipfile.ZIP_STORED
                z.writestr(zi, data)
            else:
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, data, compresslevel=9)
    os.replace(tmp, args.out)
    h = hashlib.sha256(open(args.out, "rb").read()).hexdigest()
    print("%s: %d files, %.1f MB, sha256 %s" % (args.out, len(names), os.path.getsize(args.out) / 1e6, h))


if __name__ == "__main__":
    main()
