"""Writes the sound changes picked in the gun sound editor page into the QC, rebuilds progs.dat and refreshes the page.

python -I apply_gun_sounds.py [gun_sound_changes.json] [--dry-run] [--no-build]

With no file it takes the newest gun_sound_changes*.json in the Downloads folder.  For each change it
  - swaps the sound name in the QC (gun_sounds_manifest.py says where), and adds a precache_sound line for it;
  - copies the sound into BakersfieldQuake/sound/ if it came from the joke or John-clip folders (stock and own sounds are already there);
  - for the two looping sounds (Rob Dob's hum, Mega Man's motor) rewrites the QC constant that holds the loop length;
  - keeps the old QC as <file>.pre_sounds and the old progs.dat as progs.dat.pre_gunsounds, then runs build_combat.py (an error puts the QC back).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_gun_sound_editor as B
import gun_sounds_manifest as M

DOWNLOADS = Path(os.path.expanduser("~")) / "Downloads"


def wav_seconds(data_path):
    with wave.open(str(data_path), "rb") as w:
        return w.getnframes() / w.getframerate()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry, nobuild = "--dry-run" in sys.argv, "--no-build" in sys.argv
    if args:
        src = Path(args[0])
    else:
        found = sorted(glob.glob(str(DOWNLOADS / "gun_sound_changes*.json")), key=os.path.getmtime)
        if not found:
            sys.exit("no gun_sound_changes*.json in " + str(DOWNLOADS))
        src = Path(found[-1])
    changes = json.load(open(src, encoding="utf-8"))["changes"]
    print("reading", src, "-", len(changes), "changes")

    texts, problems = B.scan_events()
    if problems:
        sys.exit("the QC no longer matches the manifest:\n  " + "\n  ".join(problems))
    events = {ev["key"]: ev for g in M.GUNS for ev in g["events"] if "pool" not in ev}
    lib = B.gather_library()

    todo = []
    for c in changes:
        ev = events.get(c["key"])
        if not ev:
            sys.exit("unknown sound slot " + c["key"])
        to = c["to"]
        if to == ev["current"]:
            continue
        if to not in lib:
            sys.exit(c["key"] + ": " + to + " is not a sound the editor knows")
        todo.append((ev, to))
    if not todo:
        print("nothing to change")
        return

    new_texts = dict(texts)
    for ev, to in todo:
        print("  %-20s %s -> %s" % (ev["key"], ev["current"], to))
    for f in {ev["file"] for ev, _ in todo}:
        text = texts[f]
        edits = []
        for ev, to in todo:
            if ev["file"] == f:
                edits += [(a, b, to) for a, b in ev["spans"]]
        for a, b, to in sorted(edits, reverse=True):
            text = text[:a] + to + text[b:]
        eol = "\r\n" if "\r\n" in text else "\n"
        for ev, to in todo:
            if ev["file"] == f and ('precache_sound ("%s")' % to) not in text:
                m = re.search(r"^([ \t]*)precache_sound \(", text, re.M)
                if not m:
                    sys.exit("no precache_sound line to put " + to + " next to in " + f)
                text = text[:m.start()] + m.group(1) + 'precache_sound ("%s");' % to + eol + text[m.start():]
        new_texts[f] = text

    # a looping sound restarts after the length the QC holds for it: set that to the new sound's length
    for ev, to in todo:
        if "lenvar" in ev:
            f, rx = ev["lenvar"]
            origin = lib[to][0]
            p = (B.LIB / origin / to)
            if not p.exists():
                B.write_library({to: lib[to]})
            secs = wav_seconds(p)
            body = new_texts[f] if f in new_texts else B.read_qc(f)
            m = re.search(rx, body)
            if not m:
                sys.exit("cannot find the loop length constant in " + f)
            body = body[:m.start(2)] + ("%.2f" % secs) + body[m.end(2):]
            new_texts[f] = body
            print("    loop length in %s -> %.2f s" % (f, secs))

    if dry:
        print("dry run: nothing written")
        return

    copies = [(to, lib[to]) for _, to in todo if lib[to][0] in ("jokes", "celeb")]
    for to, (origin, load, size) in copies:
        dst = B.MOD / "sound" / to
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(load())
        print("  copied", to, "->", dst)

    changed = [f for f in new_texts if new_texts[f] != texts.get(f, B.read_qc(f))]
    for f in changed:
        shutil.copyfile(B.QC / f, B.QC / (f + ".pre_sounds"))
        open(B.QC / f, "w", encoding="utf-8", errors="surrogateescape", newline="").write(new_texts[f])
    if not nobuild:
        progs = B.MOD / "progs.dat"
        shutil.copyfile(progs, B.MOD / "progs.dat.pre_gunsounds")
        r = subprocess.run([sys.executable, "-I", str(B.QC / "build_combat.py")])
        if r.returncode:
            for f in changed:
                shutil.copyfile(B.QC / (f + ".pre_sounds"), B.QC / f)
            sys.exit("the QC did not compile: the sources are back as they were")
    B.build()
    print("done:", len(todo), "sounds changed in", ", ".join(sorted(changed)))


if __name__ == "__main__":
    main()
