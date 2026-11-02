"""Hook the Goo Gun (mm_tools\\goo_defs.qc, goo.qc) into the Combat+ source in qc_combat_decomp. It takes over the
single-barrel shotgun: key 2 / IT_SHOTGUN keeps its slot, item bit and shells, but shows the goo gun and lobs goo.
Marker-guarded (safe to re-run), keeps *.pre_goo backups. Then: python -I build_combat.py
python -I patch_goo_combat.py"""
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
    shutil.copy(path, path + ".pre_goo")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


V = "progs/v_googun.md3"

# --- weapons.qc: precache, the view model, firing, the per-frame slow-down
patch(D + "weapons.qc", "Goo_", [
    ("\tFunGun_Precache();\n", "\tFunGun_Precache();\n\tGoo_Precache();\t// the Goo Gun replaces the shotgun (goo.qc)\n"),
    ("self.weaponmodel = \"progs/v_shot_right.mdl\";", "self.weaponmodel = \"%s\";\t// Goo Gun" % V),
    ("self.weaponmodel = \"progs/centered/v_shot.mdl\";", "self.weaponmodel = \"%s\";" % V),
    ("self.weaponmodel = \"progs/v_shot.mdl\";", "self.weaponmodel = \"%s\";" % V),
    ("\t\t\tW_FireShotgun();\n\t\t\tself.attack_timer = 1;\n\t\t\tif ((self.rapid_timer > 0))\n\t\t\t{\n\t\t\t\tself.attack_finished = (time + 0.24);\n"
     "\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\tself.attack_finished = (time + 0.54);\n\t\t\t}\n",
     "\t\t\tGoo_Fire();\t// the Goo Gun (goo.qc), full auto\n\t\t\tself.attack_timer = 1;\n\t\t\tif ((self.rapid_timer > 0))\n\t\t\t{\n"
     "\t\t\t\tself.attack_finished = (time + GOO_REFIRE_RAPID);\n\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\tself.attack_finished = (time + GOO_REFIRE);\n\t\t\t}\n"),
    ("\tFunGun_ViewFrame();\n", "\tFunGun_ViewFrame();\n\tGoo_PlayerFrame();\t// gummed-up players crawl\n"),
])

# --- player.qc: no shell casings out of the goo gun; the gun a dead player drops
patch(D + "player.qc", "goo gun", [
    ("\tif ((self.weapon == IT_SHOTGUN))\n\t{\n\t\tcasing(0);\n\t\tself.nextthink = (time + 0.07);\n\t}\n",
     "\tif ((self.weapon == IT_SHOTGUN))\n\t{\n\t\tself.nextthink = (time + 0.07);\t// the goo gun has no casings\n\t}\n", 2),
    ("(self.weapon == IT_SHOTGUN)\n\t\t\tgibname = \"progs/p_shot.md3\";", "(self.weapon == IT_SHOTGUN)\n\t\t\tgibname = \"progs/p_googun.md3\";"),
])

# --- custom_effects.qc: the adjustable weapon-position helper draws the goo gun
patch(D + "custom_effects.qc", "v_googun", [
    ("setmodel(self, \"progs/v_shot.mdl\");", "setmodel(self, \"%s\");" % V, 2),
    ("setmodel(self, \"progs/centered/v_shot.mdl\");", "setmodel(self, \"%s\");" % V),
])

# --- client.qc: third-person model, obituary
patch(D + "client.qc", "goo_inflicting", [
    ("\t\tself.vwep = \"progs/p_shot.md3\";", "\t\tself.vwep = \"progs/p_googun.md3\";\t// the Goo Gun rides p_shot's frames (build_googun.py)"),
    ("\t\t\t\t\tif (fg_inflicting)\n",
     "\t\t\t\t\tif (goo_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SHOTGUN;\n\t\t\t\t\t}\n\t\t\t\t\tif (fg_inflicting)\n"),
    ("\t\t\t\t\t\tdeathstring = \" chewed on \";\n\t\t\t\t\t\tdeathstring2 = \"'s boomstick\\n\";\n",
     "\t\t\t\t\t\tdeathstring = \" got gooed by \";\n\t\t\t\t\t\tdeathstring2 = \"'s Goo Gun\\n\";\n"),
])

# --- combat.qc: explosions tear goo apart
patch(D + "combat.qc", "Goo_Damage", [
    ("\tdamage = BM_Damage(targ, inflictor, attacker, damage);",
     "\tdamage = Goo_Damage(targ, inflictor, damage);\t// explosions x2.25 on goo (goo.qc)\n\tdamage = BM_Damage(targ, inflictor, attacker, damage);"),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "goo.qc", [
    ("\nbm_defs.qc\n", "\nbm_defs.qc\ngoo_defs.qc\n"),
    ("\nfriends.qc\n", "\nfriends.qc\ngoo.qc\n"),
])

# --- bm_reload.qc (shared source): the shotgun slot is the goo gun's 20-round magazine, 2.4 s reload
patch(T + "bm_reload.qc", "Goo Gun", [
    ("\tif (s == BM_SG)\t\t\tn = 8;\n", "\tif (s == BM_SG)\t\t\tn = 20;\t\t// the Goo Gun (it took the shotgun's slot)\n"),
    ("\tif (s == BM_SG)\t\t\tt = 1.5;\n", "\tif (s == BM_SG)\t\t\tt = 2.4;\t\t// Goo Gun\n"),
])

# --- build_combat.py: copy the goo sources with the other shared ones
patch(T + "build_combat.py", "goo.qc", [
    ("\"playerbody.qc\")", "\"playerbody.qc\", \"goo_defs.qc\", \"goo.qc\")"),
])

# --- effectinfo.txt: goo_splat, goo_chip, goo_burst, goo_snow, goo_puff (the block is swapped for the current one each run)
fx = ROOT + "effectinfo.txt"
raw = open(fx, "rb").read().decode("latin-1").replace("\r\n", "\n")
add = open(T + "goo_effectinfo.txt", "rb").read().decode("latin-1").replace("\r\n", "\n")
B, E = "// ---- Goo Gun begin", "// ---- Goo Gun end\n"
OLD = "// Goo Gun (goo.qc): a glob splatting onto something\n"    # the first version had no end marker
if B in raw:
    i = raw.index(B)
    j = raw.index(E, i) + len(E)
elif OLD in raw:
    i = raw.index(OLD)
    j = raw.index("effect goo_puff", i)
    j = raw.find("\n\n", j)
    j = len(raw) if j < 0 else j + 1
else:
    i = j = len(raw.rstrip("\n")) + 1
    add = "\n" + add
if raw[i:j] == add:
    print(fx, "goo effects up to date")
else:
    shutil.copy(fx, fx + ".pre_goo2")
    raw = raw[:i] + add + raw[j:]
    open(fx, "wb").write(raw.replace("\n", "\r\n").encode("latin-1"))
    print(fx, "goo effects written")
