#!/usr/bin/env python3
"""Builds the folder bakoweb.py serves to browser players (the "site").

  site-out/
    index.html, darkplaces-wasm.js      the play page and the engine
    manifest.json                       every game file with its size, for the page's loader and cache
    files/<gamedir>/...                 the game files, laid out like a normal install

The game files come from a normal install / the BAKOQUAKE package (--game-dir with id1, quake15 and
BakersfieldQuake in it). progs.dat and csprogs.dat must be the same ones the server runs.

Quake's own first-person lightning gun replaces the one in the mod's pk3s: BakersfieldQuake/progs/v_light.mdl goes in
the pack, taken from the install (the launchers put it there) or else from its id1/pak0.pak.

Maps: only the ones named in the server's config (map, bm_maplist, bm_votemaps), plus any --maps.
Usage:
  python3 make_web_pack.py --game-dir ../../dist/BAKOQUAKE --engine wasm-out/darkplaces-wasm.js --out site-out
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAMEDIRS = ("id1", "quake15", "BakersfieldQuake")
# never sent to browsers: server-only or Windows-only files
SKIP_NAMES = {"server.cfg", "warmup.cfg", "server_vps.cfg", "personal.cfg", "personal_post.cfg"}
SKIP_EXT = {".exe", ".dll", ".log", ".bak", ".tmp", ".sav"}
LG_NAME = "progs/v_light.mdl"                       # first-person lightning gun
LG_REL = "BakersfieldQuake/" + LG_NAME


def is_mdl(data):
    """A whole-looking Quake model (the same test as tools/find-quake-paks.sh): "IDPO", version 6, 20000+ bytes."""
    return len(data) >= 20000 and data[:8] == b"IDPO\x06\x00\x00\x00"


def pak_entry(pak_path, name):
    """The bytes of file `name` in a Quake .pak, or None (not a pak, damaged, or no such file)."""
    try:
        with open(pak_path, "rb") as f:
            magic, off, size = struct.unpack("<4sII", f.read(12))
            if magic != b"PACK" or size % 64 or size > 4 << 20:
                return None
            f.seek(off)
            table = f.read(size)
            for i in range(0, len(table) - 63, 64):
                entry, pos, length = struct.unpack_from("<56sII", table, i)
                if entry.split(b"\0")[0].lower() == name.encode():
                    if length > 1 << 20:
                        return None
                    f.seek(pos)
                    data = f.read(length)
                    return data if len(data) == length else None
    except (OSError, struct.error):
        pass
    return None


def stock_lightning_gun(game):
    """(model bytes, pak mtime) from the install's id1/pak0.pak (any case), or (None, 0)."""
    id1 = os.path.join(game, "id1")
    for fn in sorted(os.listdir(id1)):
        if fn.lower() == "pak0.pak":
            data = pak_entry(os.path.join(id1, fn), LG_NAME)
            if data and is_mdl(data):
                return data, int(os.stat(os.path.join(id1, fn)).st_mtime)
    return None, 0


def maps_from_cfg(path):
    names = []
    if not os.path.exists(path):
        return names
    text = open(path, encoding="latin-1").read()
    text = re.sub(r"//[^\n]*", "", text)
    for m in re.finditer(r'^\s*map\s+"?([\w\-]+)"?', text, re.M):
        names.append(m.group(1))
    for m in re.finditer(r'^\s*set[a]?\s+bm_(?:maplist|votemaps)\s+"([^"]*)"', text, re.M):
        names += m.group(1).split()
    return list(dict.fromkeys(names))


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) \
            and int(os.path.getmtime(dst)) == int(os.path.getmtime(src)):
        return
    shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", required=True, help="folder holding id1, quake15 and BakersfieldQuake")
    ap.add_argument("--engine", required=True, help="darkplaces-wasm.js from engine/build_wasm.sh")
    ap.add_argument("--out", default=os.path.join(HERE, "site-out"))
    ap.add_argument("--server-cfg", help="server config to read the map list from (default BakersfieldQuake/server.cfg)")
    ap.add_argument("--maps", default="", help="extra maps, space separated")
    ap.add_argument("--all-maps", action="store_true", help="ship every map in BakersfieldQuake/maps")
    a = ap.parse_args()

    game = os.path.abspath(a.game_dir)
    out = os.path.abspath(a.out)
    cfg = a.server_cfg or os.path.join(game, "BakersfieldQuake", "server.cfg")
    wanted_maps = set(maps_from_cfg(cfg) + a.maps.split())

    entries = []
    for gd in GAMEDIRS:
        root = os.path.join(game, gd)
        if not os.path.isdir(root):
            sys.exit("missing %s" % root)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d.lower() not in ("source", "website", "dev")]
            rel_dir = os.path.relpath(dirpath, game).replace(os.sep, "/")
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if fn in SKIP_NAMES or ext in SKIP_EXT:
                    continue
                rel = rel_dir + "/" + fn
                if rel.lower().startswith("bakersfieldquake/maps/") and not a.all_maps:
                    base = os.path.splitext(fn)[0]
                    if base not in wanted_maps:
                        continue
                entries.append(rel)

    # An install no launcher has run yet has no loose lightning gun (or a broken one): take it from the pak. It is only
    # written into the pack, never into the install, which may still be zipped and passed on.
    lg_data, lg_mtime = None, 0
    have_lg = False
    if LG_REL in entries:
        with open(os.path.join(game, LG_REL), "rb") as f:
            have_lg = is_mdl(f.read())
    if not have_lg:
        lg_data, lg_mtime = stock_lightning_gun(game)
        if lg_data:
            entries = [e for e in entries if e != LG_REL]
        else:
            print("WARNING: no %s in id1/pak0.pak: browser players get the mod's lightning gun" % LG_NAME)

    shipped_maps = {os.path.splitext(e.split("/")[-1])[0] for e in entries if e.lower().endswith(".bsp")}
    missing = sorted(m for m in wanted_maps if m not in shipped_maps)

    files = []
    total = 0
    for rel in sorted(entries):
        src = os.path.join(game, rel)
        copy(src, os.path.join(out, "files", rel))
        st = os.stat(src)
        files.append({"path": rel, "url": "files/" + rel, "size": st.st_size, "mtime": int(st.st_mtime)})
        total += st.st_size

    if lg_data:
        dst = os.path.join(out, "files", LG_REL)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst + ".tmp", "wb") as f:
            f.write(lg_data)
        os.utime(dst + ".tmp", (lg_mtime, lg_mtime))      # stable between builds, so browsers keep their copy
        os.replace(dst + ".tmp", dst)
        files.append({"path": LG_REL, "url": "files/" + LG_REL, "size": len(lg_data), "mtime": lg_mtime})
        total += len(lg_data)

    # the browser settings file goes in with the game files
    webcfg = os.path.join(HERE, "site", "web.cfg")
    copy(webcfg, os.path.join(out, "files", "BakersfieldQuake", "web.cfg"))
    st = os.stat(webcfg)
    files.append({"path": "BakersfieldQuake/web.cfg", "url": "files/BakersfieldQuake/web.cfg",
                  "size": st.st_size, "mtime": int(st.st_mtime)})
    total += st.st_size

    copy(a.engine, os.path.join(out, "darkplaces-wasm.js"))
    for fn in os.listdir(os.path.join(HERE, "site")):
        if fn != "web.cfg":
            copy(os.path.join(HERE, "site", fn), os.path.join(out, fn))

    est = os.stat(a.engine)
    version = hashlib.sha1(json.dumps([[f["path"], f["size"], f["mtime"]] for f in files]
                                      + [est.st_size, int(est.st_mtime)]).encode()).hexdigest()[:12]
    manifest = {"version": version, "engine": "darkplaces-wasm.js?v=%x" % int(est.st_mtime),
                "total": total, "files": files}
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)

    print("web pack %s: %d files, %.0f MB -> %s" % (version, len(files), total / 1e6, out))
    print("maps: %s" % " ".join(sorted(shipped_maps)))
    if missing:
        print("WARNING: maps named in %s but not found as BakersfieldQuake/maps/*.bsp (may live in a pk3): %s"
              % (os.path.basename(cfg), " ".join(missing)))
    big = sorted(files, key=lambda f: -f["size"])[:6]
    print("largest: " + ", ".join("%s %.0f MB" % (f["path"], f["size"] / 1e6) for f in big))


if __name__ == "__main__":
    main()
