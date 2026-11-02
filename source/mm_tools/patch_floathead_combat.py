"""Hook the floating head monster (BakersfieldQuake\source\mm_tools\\floathead.qc) into the Combat+ source in qc_combat_decomp.
Marker-guarded (safe to re-run), keeps *.pre_fh backups.   python -I patch_floathead_combat.py"""
import shutil
import sys

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"


def patch(path, marker, edits):
    raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    if marker in s:
        print(path, "already patched")
        return
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit("%s: anchor found %d times, expected 1: %r" % (path, n, old[:80]))
        s = s.replace(old, new)
    shutil.copy(path, path + ".pre_fh")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


patch(D + "weapons.qc", "FloatHead_", [
    # precache the model and sounds
    ("\tJG_SplashPrecache();\t// JohnWave grenade: splash sprites and sound (jg_splash.qc)\n",
     "\tJG_SplashPrecache();\t// JohnWave grenade: splash sprites and sound (jg_splash.qc)\n\tFloatHead_Precache();\t// the floating head monster (floathead.qc)\n"),
    # impulse 17: summon one in front of you
    ("\tif ((self.impulse == 255))\n\t{\n\t\tQuadCheat();\n\t}\n\tself.impulse = 0;\n};",
     "\tif ((self.impulse == 255))\n\t{\n\t\tQuadCheat();\n\t}\n\tif ((self.impulse == 17))\n\t{\n\t\tFloatHead_Summon();\t// a floating head right in front of you (floathead.qc)\n\t}\n\tself.impulse = 0;\n};"),
])

patch(D + "client.qc", "FloatHead_", [
    # the first real player into a deathmatch map starts the head spawner
    ("\tBM_PlayerSpawned();\t// spawn protection\n};",
     "\tBM_PlayerSpawned();\t// spawn protection\n\tFloatHead_StartSpawner();\t// floating heads in deathmatch (floathead.qc)\n};"),
    # the obituary
    ("\t\t\tif ((attacker.flags & FL_MONSTER))\n\t\t\t{\n\t\t\t\tif ((attacker.classname == \"monster_army\"))\n",
     "\t\t\tif ((attacker.flags & FL_MONSTER))\n\t\t\t{\n\t\t\t\tif (((attacker.classname == \"monster_floathead\") || (attacker.classname == \"fh_dead\")))\n\t\t\t\t{\n\t\t\t\t\tbprint(\" got a big wet kiss from a floating head\\n\");\n\t\t\t\t}\n\t\t\t\tif ((attacker.classname == \"monster_army\"))\n"),
])

patch(D + "progs.src", "floathead", [
    ("jg_splash.qc\nweapons.qc\n", "jg_splash.qc\nfloathead.qc\nweapons.qc\n"),
])

patch(T + "build_combat.py", "floathead.qc", [
    ("\"bm_match.qc\", \"jg_splash.qc\"):", "\"bm_match.qc\", \"jg_splash.qc\", \"floathead.qc\"):"),
])