"""Hook the Milky Gun (mm_tools\\milky_defs.qc, milky.qc) into the Combat+ source in qc_combat_decomp. It takes over the
super nailgun: key 5 / IT_SUPER_NAILGUN keeps its slot, item bit, nails and (for now) its view model, but fires the Pink
Lady. Run after patch_sniper_combat.py. Marker-guarded (safe to re-run), keeps *.pre_milky backups. Then: python -I build_combat.py
Assets: python build_pinklady_assets.py <turntable.mp4>, python build_milky_assets.py <song.mp3>
python -I patch_milky_combat.py"""
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
    if not os.path.exists(path + ".pre_milky"):
        shutil.copy(path, path + ".pre_milky")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


SNG_FIRE = ("\t\t\t\t\tif ((self.weapon == IT_SUPER_NAILGUN))\n\t\t\t\t\t{\n\t\t\t\t\t\tif ((self.waterlevel >= 2))\n\t\t\t\t\t\t{\n"
            "\t\t\t\t\t\t\tplayer_swimnail1();\n\t\t\t\t\t\t}\n\t\t\t\t\t\telse\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\tplayer_nail1();\n\t\t\t\t\t\t}\n"
            "\t\t\t\t\t\tself.attack_timer = 1;\n\t\t\t\t\t}\n")
MILKY_FIRE = ("\t\t\t\t\tif ((self.weapon == IT_SUPER_NAILGUN))\n\t\t\t\t\t{\n"
              "\t\t\t\t\t\tif (Milky_CanFire())\n\t\t\t\t\t\t{\n"
              "\t\t\t\t\t\t\tMilky_Fire();\t// the Milky Gun winds up and throws the Pink Lady (milky.qc)\n"
              "\t\t\t\t\t\t}\n\t\t\t\t\t}\n")

# --- weapons.qc: precache, firing, the per-frame breadcrumbs and slide
patch(D + "weapons.qc", "Milky_", [
    ("\tFunGun_Precache();\n", "\tFunGun_Precache();\n\tMilky_Precache();\t// the Milky Gun replaces the super nailgun (milky.qc)\n"),
    (SNG_FIRE, MILKY_FIRE),
    ("\tGoo_PlayerFrame();\t// gummed-up players crawl\n",
     "\tGoo_PlayerFrame();\t// gummed-up players crawl\n\tMilky_PlayerFrame();\t// breadcrumbs for the ladies, sliding on milk (milky.qc)\n"),
])

# --- combat.qc: the lady keeps her own hit points
patch(D + "combat.qc", "Milky_Damage", [
    ("\tdamage = BM_Damage(targ, inflictor, attacker, damage);\t// spawn protection, less self-damage\n",
     "\tdamage = BM_Damage(targ, inflictor, attacker, damage);\t// spawn protection, less self-damage\n"
     "\tdamage = Milky_Damage(targ, inflictor, attacker, damage);\t// the Pink Lady keeps her own hit points (milky.qc)\n"),
])

# --- client.qc: obituary
patch(D + "client.qc", "milky_inflicting", [
    ("\t\t\t\t\tif (sn_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_NAILGUN;\n\t\t\t\t\t}\n",
     "\t\t\t\t\tif (sn_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_NAILGUN;\n\t\t\t\t\t}\n"
     "\t\t\t\t\tif (milky_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SUPER_NAILGUN;\n\t\t\t\t\t}\n"),
    ("\t\t\t\t\t\tdeathstring = \" was punctured by \";\n\t\t\t\t\t\tdeathstring2 = \"\\n\";\n",
     "\t\t\t\t\t\tdeathstring = \" got milked by \";\t// Milky Gun\n\t\t\t\t\t\tdeathstring2 = \"'s Pink Lady\\n\";\n"),
])

# --- items.qc: the pickup's name
patch(D + "items.qc", "Milky Gun", [
    ("\t\tself.netname = \"Super Nailgun\";\n", "\t\tself.netname = \"Milky Gun\";\n"),
    ("\t\t\t\t\t\titem.netname = \"Super Nailgun\";\n", "\t\t\t\t\t\titem.netname = \"Milky Gun\";\n"),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "milky.qc", [
    ("\njetpack_defs.qc\n", "\njetpack_defs.qc\nmilky_defs.qc\n"),
    ("\njetpack.qc\n", "\njetpack.qc\nmilky.qc\n"),
])

# --- bm_reload.qc (shared source): the super nailgun's magazine is two ladies, 5 s to reload, one nail a lady
patch(T + "bm_reload.qc", "Milky Gun", [
    ("\telse if (s == BM_SNG)\tn = 80;\t\t// 2 nails a shot: 40 shots\n", "\telse if (s == BM_SNG)\tn = 2;\t\t// the Milky Gun: two ladies\n"),
    ("\telse if (s == BM_SNG)\tt = 2.5;\n", "\telse if (s == BM_SNG)\tt = 5;\t\t// Milky Gun\n"),
    ("\tif (s == BM_SSG || s == BM_SNG)\n\t\treturn 2;\n", "\tif (s == BM_SSG)\n\t\treturn 2;\n"),
])

# --- build_combat.py: copy the milky sources with the other shared ones
patch(T + "build_combat.py", "milky.qc", [
    ("\"jetpack_defs.qc\", \"jetpack.qc\")", "\"jetpack_defs.qc\", \"jetpack.qc\", \"milky_defs.qc\", \"milky.qc\")"),
])
