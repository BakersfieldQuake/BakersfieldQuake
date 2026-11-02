"""Hook the sniper rifle (mm_tools\\sniper_defs.qc, sniper.qc) into the Combat+ source in qc_combat_decomp. It takes over the
nailgun: key 4 / IT_NAILGUN keeps its slot, item bit and nail magazine, but shows TF's rifle, charges while fire is held
and shoots on release. Marker-guarded (safe to re-run), keeps *.pre_sniper backups. Then: python -I build_combat.py
Assets: python -I build_srifle.py
python -I patch_sniper_combat.py"""
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
    if not os.path.exists(path + ".pre_sniper"):
        shutil.copy(path, path + ".pre_sniper")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


V = "progs/v_srifle.mdl"
P = "progs/p_srifle.md3"

# --- weapons.qc: precache, the view model, the per-frame work, the fire button
patch(D + "weapons.qc", "Sniper_", [
    ("\tFunGun_Precache();\n", "\tFunGun_Precache();\n\tSniper_Precache();\t// the sniper rifle replaces the nailgun (sniper.qc)\n"),
    ("self.weaponmodel = \"progs/v_nail_right.mdl\";", "self.weaponmodel = \"%s\";\t// sniper rifle" % V),
    ("self.weaponmodel = \"progs/v_nail.mdl\";", "self.weaponmodel = \"%s\";" % V),
    ("\tGoo_PlayerFrame();\t// gummed-up players crawl\n",
     "\tGoo_PlayerFrame();\t// gummed-up players crawl\n\tSniper_PlayerFrame();\t// the rifle's zoom, laser dot and leg shots (sniper.qc)\n"),
    ("\tself.attack_timer = 0;\n\tImpulseCommands();\n\tif (self.button0)\n",
     "\tself.attack_timer = 0;\n\tImpulseCommands();\n\tif (Sniper_Frame())\n\t{\n"
     "\t\treturn;\t// the sniper rifle charges while fire is held and shoots on release (sniper.qc)\n\t}\n\tif (self.button0)\n"),
])

# --- player.qc: the gun a dead player drops
patch(D + "player.qc", "p_srifle", [
    ("else if (self.weapon == IT_NAILGUN)\n\t\t\tgibname = \"progs/p_nail.md3\";",
     "else if (self.weapon == IT_NAILGUN)\n\t\t\tgibname = \"%s\";\t// sniper rifle" % P),
])

# --- client.qc: third-person model, obituary, a fresh life
patch(D + "client.qc", "sn_inflicting", [
    ("\telse if (self.owner.weapon == IT_NAILGUN)\n\t\tself.vwep = \"progs/p_nail.md3\";",
     "\telse if (self.owner.weapon == IT_NAILGUN)\n\t\tself.vwep = \"%s\";\t// the sniper rifle rides p_shot's frames (build_srifle.py)" % P),
    ("\t\t\t\t\tif (goo_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SHOTGUN;\n\t\t\t\t\t}\n",
     "\t\t\t\t\tif (goo_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SHOTGUN;\n\t\t\t\t\t}\n"
     "\t\t\t\t\tif (sn_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_NAILGUN;\n\t\t\t\t\t}\n"),
    ("\t\t\t\t\t\tdeathstring = \" was nailed by \";\n\t\t\t\t\t\tdeathstring2 = \"\\n\";\n",
     "\t\t\t\t\t\tdeathstring = Sniper_Death();\t// sniper rifle\n\t\t\t\t\t\tdeathstring2 = \"\\n\";\n"),
    ("\tBM_Spawn();\t// full magazines\n", "\tBM_Spawn();\t// full magazines\n\tSniper_Spawn();\t// steady legs, no zoom (sniper.qc)\n"),
])

# --- items.qc: the pickup
patch(D + "items.qc", "g_srifle", [
    ("\t\tprecache_model(\"progs/g_nail.mdl\");\n\t\tsetmodel(self, \"progs/g_nail.mdl\");\n",
     "\t\tprecache_model(\"progs/g_srifle.mdl\");\t// sniper rifle\n\t\tsetmodel(self, \"progs/g_srifle.mdl\");\n"),
    ("\t\tself.netname = \"nailgun\";\n", "\t\tself.netname = \"Sniper Rifle\";\n"),
])

# --- custom_effects.qc: the adjustable weapon-position helper draws the rifle
patch(D + "custom_effects.qc", "v_srifle", [
    ("setmodel(self, \"progs/v_nail.mdl\");", "setmodel(self, \"%s\");" % V, 2),
    ("setmodel(self, \"progs/centered/v_nail.mdl\");", "setmodel(self, \"%s\");" % V),
])
# ... and the weapon-sway helper hides it while zoomed in (it sets alpha every frame, so this goes right after)
patch(D + "custom_effects.qc", "Sniper_Scoped", [
    ("\tself.nextthink = time;\n\tself.owner.gunof = self.origin;\n",
     "\tif (Sniper_Scoped(self.owner))\n\t{\n\t\tself.alpha = -1;\t// zoomed in with the sniper rifle (sniper.qc)\n\t}\n"
     "\tself.nextthink = time;\n\tself.owner.gunof = self.origin;\n"),
])

# --- FrikBots: they never stand still long enough to aim it, so they leave it alone
patch(D + "frikbot.bot_fight.qc", "sniper rifle", [
    ("\tit = self.items & 127;\n", "\tit = self.items & 123;\t// not the sniper rifle (IT_NAILGUN 4)\n"),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "sniper.qc", [
    ("\ngoo_defs.qc\n", "\ngoo_defs.qc\nsniper_defs.qc\n"),
    ("\ngoo.qc\n", "\ngoo.qc\nsniper.qc\n"),
])

# --- build_combat.py: copy the sniper sources with the other shared ones
patch(T + "build_combat.py", "sniper.qc", [
    ("\"goo_defs.qc\", \"goo.qc\")", "\"goo_defs.qc\", \"goo.qc\", \"sniper_defs.qc\", \"sniper.qc\")"),
])
