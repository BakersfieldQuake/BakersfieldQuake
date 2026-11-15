#!/usr/bin/env python3
"""Builds the folder bakoweb.py serves to browser players (the "site").

  site-out/
    index.html, darkplaces-wasm.js      the play page and the engine
    manifest.json                       every game file with its size, for the page's loader and cache
    files/<gamedir>/...                 the game files, laid out like a normal install

The game files come from a normal install / the BAKOQUAKE package (--game-dir with id1, quake15 and
BakersfieldQuake in it). progs.dat and csprogs.dat must be the same ones the server runs.

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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAMEDIRS = ("id1", "quake15", "BakersfieldQuake")
# never sent to browsers: server-only or Windows-only files
SKIP_NAMES = {"server.cfg", "warmup.cfg", "server_vps.cfg", "personal.cfg", "personal_post.cfg"}
SKIP_EXT = {".exe", ".dll", ".log", ".bak", ".tmp", ".sav"}


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
