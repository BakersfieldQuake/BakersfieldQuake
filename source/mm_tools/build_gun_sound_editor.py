"""Builds the gun sound editor page: source/gun_sound_editor/index.html (open it in a browser).

It reads what every custom gun plays right now straight out of the QC (gun_sounds_manifest.py says where), copies the
sound library next to the page (lib/<where from>/<path>) and writes index.html from gun_sound_editor.template.html.

  mod     BakersfieldQuake/sound/**                 (the guns' own sounds, John, funny, ...; the song slices are left out)
  stock   id1 pak0/pak1 + quake15/q15.pk3 sounds     (wav only, under 600 KB, no music / ambience / custom folders)
  jokes   grenade_sound_vote/audio/new               (generated joke sounds; copied to sound/grenade/ when picked)
  celeb   grenade_sound_vote/audio/celeb             (John clips; copied to sound/celeb/ when picked)

python -I build_gun_sound_editor.py          then pick sounds in the page and run apply_gun_sounds.py on what it downloads
"""
import json
import os
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gun_sounds_manifest as M

COMBAT = Path(r"G:\Quake\Combat")
MOD = COMBAT / "BakersfieldQuake"
QC = HERE
OUT = MOD / "source" / "gun_sound_editor"
LIB = OUT / "lib"
JOKES = MOD / "source" / "grenade_sound_vote" / "audio" / "new"
CELEB = MOD / "source" / "grenade_sound_vote" / "audio" / "celeb"
STOCK_MAX = 600_000
STOCK_SKIP = {"custom", "cdtracks", "ambience"}
MOD_SKIP = ("calc/", "floathead/calc/")
ORIGIN_ORDER = ["mod", "stock", "jokes", "celeb"]       # when two origins have the same path the first one is what the game plays


def read_qc(name):
    return open(QC / name, encoding="utf-8", errors="surrogateescape", newline="").read()


def ctx_regexes(ev):
    """the event's patterns (one string or a list), with line breaks that may be CRLF"""
    ctx = ev["ctx"] if isinstance(ev["ctx"], (list, tuple)) else [ev["ctx"]]
    return [re.compile(c.replace("\\n", "\\r?\\n")) for c in ctx]


def scan_events():
    """every event with the sound the QC plays now (current) and the spans of the sound name in its file (spans)"""
    texts = {}
    problems = []
    for g in M.GUNS:
        for ev in g["events"]:
            ev["key"] = g["id"] + "." + ev["id"]
            if "pool" in ev:
                continue
            f = ev["file"]
            if f not in texts:
                texts[f] = read_qc(f)
            spans, names = [], []
            for rx in ctx_regexes(ev):
                for m in rx.finditer(texts[f]):
                    for gi in range(1, (rx.groups or 0) + 1):
                        spans.append(m.span(gi))
                        names.append(m.group(gi))
            if not spans:
                problems.append(ev["key"] + ": no match in " + f)
                continue
            if len(set(names)) > 1:
                problems.append(ev["key"] + ": its places play different sounds " + str(sorted(set(names))))
            ev["current"] = names[0]
            ev["spans"] = spans
    claimed = {}
    for g in M.GUNS:           # two events must not claim the same text
        for ev in g["events"]:
            for sp in ev.get("spans", []):
                k = (ev["file"], sp)
                if k in claimed:
                    problems.append(ev["key"] + " and " + claimed[k] + " both match the same text in " + ev["file"])
                claimed[k] = ev["key"]
    return texts, problems


# ---------------------------------------------------------------- the library
def pak_entries(path):
    f = open(path, "rb")
    _, off, ln = struct.unpack("<4sii", f.read(12))
    f.seek(off)
    out = {}
    for _ in range(ln // 64):
        n, o, l = struct.unpack("<56sii", f.read(64))
        out[n.split(b"\0")[0].decode("latin-1")] = (path, o, l)
    return out


def gather_library():
    """{game path: (origin, loader)}; the first origin in ORIGIN_ORDER to have a path wins"""
    lib = {}

    def add(path, origin, load, size):
        if path not in lib:
            lib[path] = (origin, load, size)

    for p in sorted((MOD / "sound").rglob("*.wav")):
        rel = p.relative_to(MOD / "sound").as_posix()
        if rel.startswith(MOD_SKIP):
            continue
        add(rel, "mod", (lambda p=p: p.read_bytes()), p.stat().st_size)

    stock = {}
    for pk in ("pak0.pak", "pak1.pak"):
        for n, (path, o, l) in pak_entries(COMBAT / "id1" / pk).items():
            stock[n] = ("pak", path, o, l)
    z = zipfile.ZipFile(COMBAT / "quake15" / "q15.pk3")          # the game loads it after the paks: it wins
    for i in z.infolist():
        if not i.is_dir():
            stock[i.filename] = ("zip", z, i, i.file_size)
    for n, v in sorted(stock.items()):
        parts = n.split("/")
        if parts[0] != "sound" or len(parts) < 3 or not n.lower().endswith(".wav") or parts[1] in STOCK_SKIP:
            continue
        if v[3] > STOCK_MAX or " - copy" in n:
            continue
        if v[0] == "pak":
            def load(v=v):
                with open(v[1], "rb") as f:
                    f.seek(v[2])
                    return f.read(v[3])
        else:
            def load(v=v):
                return v[1].read(v[2])
        add("/".join(parts[1:]), "stock", load, v[3])

    for p in sorted(JOKES.glob("*.wav")):
        add("grenade/" + p.name, "jokes", (lambda p=p: p.read_bytes()), p.stat().st_size)
    for p in sorted(CELEB.glob("*.wav")):
        add("celeb/" + p.name, "celeb", (lambda p=p: p.read_bytes()), p.stat().st_size)
    return lib


def write_library(lib):
    n = 0
    for path, (origin, load, size) in lib.items():
        dst = LIB / origin / path
        if dst.exists() and dst.stat().st_size == size:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(load())
        n += 1
    return n


# ---------------------------------------------------------------- the page
def build(quiet=False):
    texts, problems = scan_events()
    lib = gather_library()
    for g in M.GUNS:
        for ev in g["events"]:
            if "pool" in ev:
                pat, count = ev["pool"][0], ev["pool"][1]
                start = ev["pool"][2] if len(ev["pool"]) > 2 else 0
                ev["pool_paths"] = [pat.format(n=i) for i in range(start, start + count)]
            elif "current" in ev and ev["current"] not in lib:
                problems.append(ev["key"] + ": the QC plays " + ev["current"] + " but the library has no such file")
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        sys.exit(1)

    wrote = write_library(lib)
    # the calc song slices and similar pools are not in the library: copy the one sample the page plays
    for g in M.GUNS:
        for ev in g["events"]:
            if "pool_paths" in ev:
                sample = ev["pool_paths"][0]
                if sample in lib:
                    ev["sample"] = sample
                else:
                    src = MOD / "sound" / sample
                    dst = LIB / "mod" / sample
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
                    lib[sample] = ("mod", None, dst.stat().st_size)
                    ev["sample"] = sample
                    ev["sample_hidden"] = True

    guns = []
    for g in M.GUNS:
        evs = []
        for ev in g["events"]:
            e = dict(id=ev["id"], key=ev["key"], label=ev["label"], hint=ev.get("hint", ""), vol=ev.get("vol", 1), rate=ev.get("rate", 1),
                     loop=bool(ev.get("loop")))
            if "pool_paths" in ev:
                e["pool"] = len(ev["pool_paths"])
                e["sample"] = ev["sample"]
                e["current"] = ev["pool_paths"][0] + " ... " + ev["pool_paths"][-1].rsplit("/", 1)[-1]
                e["poolpaths"] = ev["pool_paths"]
            else:
                e["current"] = ev["current"]
                e["places"] = len(ev["spans"])
            evs.append(e)
        steps = [dict(name=n, steps=[[s[0], s[1], s[2] if len(s) > 2 else {}] for s in sc]) for n, sc in g["scenarios"]]
        guns.append(dict(id=g["id"], name=g["name"], sub=g["sub"], scenarios=steps, events=evs))

    libs = []
    for path, (origin, load, size) in sorted(lib.items(), key=lambda kv: (ORIGIN_ORDER.index(kv[1][0]), kv[0])):
        if path.startswith(("floathead/calc/",)):
            continue
        libs.append([path, origin, size])
    data = dict(guns=guns, lib=libs, origins=dict(mod="This game's own", stock="Quake stock", jokes="Joke sounds (new)", celeb="John clips (new)"))

    page = open(HERE / "gun_sound_editor.template.html", encoding="utf-8").read()
    assert "/*DATA*/null" in page
    page = page.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    OUT.mkdir(parents=True, exist_ok=True)
    open(OUT / "index.html", "w", encoding="utf-8").write(page)
    if not quiet:
        print("%d guns, %d events, %d library sounds (%d files copied) -> %s" % (len(guns), sum(len(g["events"]) for g in guns), len(libs), wrote, OUT / "index.html"))
    return lib


if __name__ == "__main__":
    build()
