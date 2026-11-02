"""Hook the Bonk Hammer (mm_tools\\hammer_defs.qc, hammer.qc) into the Combat+ source in qc_combat_decomp. It takes over the
axe: key 1 / IT_AXE keeps its slot and item bit, but shows Bonk Jam's hammer, charges while fire is held and swings on
release. Run after patch_sniper_combat.py (it hooks in next to the rifle). Marker-guarded (safe to re-run), keeps
*.pre_hammer backups. Then: python -I build_combat.py
Assets: python -I build_hammer.py
python -I patch_hammer_combat.py"""
import os
import shutil
import sys

ROOT = "G:\\Quake\\Combat\\BakersfieldQuake\\"
D = ROOT + "source\\qc_combat_decomp\\"
T = ROOT + "source\\mm_tools\\"


def patch(path, marker, edits):
    raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    if marker in s:
        print(path, "already patched")
        return
    for old, new, *cnt in edits:
        want = cnt[0] if cnt else 1
        n = s.count(old)
        if n != want:
            sys.exit("%s: anchor found %d times, expected %d: %r" % (path, n, want, old[:80]))
        s = s.replace(old, new)
    if not os.path.exists(path + ".pre_hammer"):
        shutil.copy(path, path + ".pre_hammer")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


V = "progs/v_hammer.mdl"

# --- weapons.qc: precache, the view model (the zombie-axe variants too), the per-frame work, no stock axe swing
patch(D + "weapons.qc", "Hammer_", [
    ("\tSniper_Precache();", "\tHammer_Precache();\t// the Bonk Hammer replaces the axe (hammer.qc)\n\tSniper_Precache();"),
    ("\"progs/v_axe_zombie00.mdl\"", "\"%s\"" % V, 2),
    ("\"progs/v_axe_zombie01.mdl\"", "\"%s\"" % V),
    ("\"progs/v_axe.mdl\"", "\"%s\"" % V),
    ("\tSniper_PlayerFrame();", "\tHammer_PlayerFrame();\t// charge, swing, spin (hammer.qc)\n\tSniper_PlayerFrame();"),
    ("\tif (Sniper_Frame())\n\t{\n",
     "\tif (self.weapon == IT_AXE)\n\t{\n\t\treturn;\t// the Bonk Hammer charges and swings by itself (hammer.qc)\n\t}\n\tif (Sniper_Frame())\n\t{\n"),
])

# --- custom_effects.qc: the weapon-sway helper draws the hammer
patch(D + "custom_effects.qc", "v_hammer", [
    ("\"progs/v_axe_zombie00.mdl\"", "\"%s\"" % V, 2),
    ("\"progs/v_axe.mdl\"", "\"%s\"" % V, 2),
])

# --- client.qc: obituary, a fresh life
patch(D + "client.qc", "Hammer_Spawn", [
    ("\t\t\t\t\t\tdeathstring = \" was ax-murdered by \";\n\t\t\t\t\t\tdeathstring2 = \"\\n\";\n",
     "\t\t\t\t\t\tdeathstring = \" got bonked by \";\t// Bonk Hammer\n\t\t\t\t\t\tdeathstring2 = \"'s hammer\\n\";\n"),
    ("\tSniper_Spawn();", "\tHammer_Spawn();\t// no charge left over (hammer.qc)\n\tSniper_Spawn();"),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "hammer.qc", [
    ("\nsniper_defs.qc\n", "\nsniper_defs.qc\nhammer_defs.qc\n"),
    ("\nsniper.qc\n", "\nsniper.qc\nhammer.qc\n"),
])

# --- build_combat.py: copy the hammer sources with the other shared ones
patch(T + "build_combat.py", "hammer.qc", [
    ("\"sniper_defs.qc\", \"sniper.qc\")", "\"sniper_defs.qc\", \"sniper.qc\", \"hammer_defs.qc\", \"hammer.qc\")"),
])
