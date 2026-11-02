"""Hook the jetpack (mm_tools\\jetpack_defs.qc, jetpack.qc) into the Combat+ source in qc_combat_decomp:
a pickup beside every yellow armor (item_armor2), the per-frame flying in W_WeaponFrame, a clean slate on respawn,
key J = impulse 71. Marker-guarded (safe to re-run), keeps *.pre_jetpack backups.
Then: python -I build_jetpack_assets.py, python -I build_combat.py.
python -I patch_jetpack_combat.py"""
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
    if not os.path.exists(path + ".pre_jetpack"):
        shutil.copy(path, path + ".pre_jetpack")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


# --- items.qc: the yellow armor spawns a jetpack beside it
patch(D + "items.qc", "Jetpack_", [
    ("\tself.skin = 1;\n\tsetsize(self, '-16 -16 0', '16 16 56');\n\tStartItem();\n",
     "\tself.skin = 1;\n\tsetsize(self, '-16 -16 0', '16 16 56');\n\tStartItem();\n\tJetpack_ForArmor(self);\t// a jetpack beside every yellow armor (jetpack.qc)\n"),
])

# --- weapons.qc: flying, every frame
patch(D + "weapons.qc", "Jetpack_", [
    ("\tHammer_PlayerFrame();", "\tJetpack_Frame();\t// switch on/off, hover, climb (jetpack.qc)\n\tHammer_PlayerFrame();"),
])

# --- client.qc: no fuel and normal gravity on every spawn
patch(D + "client.qc", "Jetpack_", [
    ("\tHammer_Spawn();", "\tJetpack_Spawn();\t// no fuel left over (jetpack.qc)\n\tHammer_Spawn();"),
])

# --- progs.src: defs early, code with the other guns
patch(D + "progs.src", "jetpack", [
    ("\nsentry_defs.qc\n", "\nsentry_defs.qc\njetpack_defs.qc\n"),
    ("\nsentry.qc\n", "\nsentry.qc\njetpack.qc\n"),
])

# --- build_combat.py: copy the jetpack sources with the other shared ones
patch(T + "build_combat.py", "jetpack", [
    ("\"sentry_defs.qc\", \"sentry.qc\")", "\"sentry_defs.qc\", \"sentry.qc\", \"jetpack_defs.qc\", \"jetpack.qc\")"),
])

# --- default.cfg: key J
patch(ROOT + "default.cfg", "impulse 71", [
    ("bind b \"impulse 64\"\t\t\t\t// Sentry Gun (fun gun 4)\n",
     "bind b \"impulse 64\"\t\t\t\t// Sentry Gun (fun gun 4)\nbind j \"impulse 71\"\t\t\t\t// jetpack on/off\n"),
])
