"""NOTE: the IT_SENTRY weapon hooks this script adds (and key B = impulse 70) were later removed by hand: the sentry is now the
fourth fun gun (funguns.qc, FG_SENTRY, impulse 64). Do not re-run it on a fresh source tree without removing them again.

Hook the sentry gun (mm_tools\\sentry_defs.qc, sentry.qc) into the Combat+ source in qc_combat_decomp: a gun of its own
(.weapon IT_SENTRY, key B = impulse 70) whose fire builds a TF level 2 sentry. Run after patch_hammer_combat.py
(it hooks in next to the hammer). Marker-guarded (safe to re-run), keeps *.pre_sentry backups.
Then: python -I build_combat.py. Assets: python -I build_sentry.py. The B bind is in BakersfieldQuake\\default.cfg.
python -I patch_sentry_combat.py"""
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
    if not os.path.exists(path + ".pre_sentry"):
        shutil.copy(path, path + ".pre_sentry")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


TABS = "\t" * 10

# --- weapons.qc: precache, the spanner as a weapon, the per-frame work, the fire button
patch(D + "weapons.qc", "Sentry_", [
    ("\tHammer_Precache();", "\tSentry_Precache();\t// the sentry gun (sentry.qc)\n\tHammer_Precache();"),
    (TABS + "else if ((self.weapon == IT_MEGAMAN))\n",
     TABS + "else if ((self.weapon == IT_SENTRY))\n" + TABS + "{\n"
     + TABS + "\tself.currentammo = (time >= self.sg_ready);\t// the sentry gun's spanner (sentry.qc)\n"
     + TABS + "\tself.weaponmodel = \"progs/v_span.mdl\";\n" + TABS + "\tself.weaponframe = 0;\n"
     + TABS + "\taxeequipped = 0;\n" + TABS + "}\n"
     + TABS + "else if ((self.weapon == IT_MEGAMAN))\n"),
    ("\tHammer_PlayerFrame();", "\tSentry_PlayerFrame();\t// key B, the spanner, its reload bar (sentry.qc)\n\tHammer_PlayerFrame();"),
    ("\tif (self.weapon == IT_AXE)\n\t{\n",
     "\tif (Sentry_Frame())\n\t{\n\t\treturn;\t// the spanner builds a sentry gun (sentry.qc)\n\t}\n\tif (self.weapon == IT_AXE)\n\t{\n"),
])

# --- custom_effects.qc: the weapon-sway helper draws the spanner
patch(D + "custom_effects.qc", "v_span", [
    ("\tif ((self.owner.weapon == IT_MEGAMAN))\n",
     "\tif ((self.owner.weapon == IT_SENTRY))\n\t{\n\t\tsetmodel(self, \"progs/v_span.mdl\");\n\t\tself.origin = '0 0 0';\n"
     "\t\tself.angles = '0 0 0';\n\t}\n\tif ((self.owner.weapon == IT_MEGAMAN))\n", 2),
])

# --- client.qc: no gun in the hands for the spanner, the obituary
patch(D + "client.qc", "sg_inflicting", [
    ("\telse if (self.owner.weapon == IT_MEGAMAN)\n",
     "\telse if (self.owner.weapon == IT_SENTRY)\n\t\tself.vwep = \"\";\t// the sentry gun's spanner\n\telse if (self.owner.weapon == IT_MEGAMAN)\n"),
    ("\t\t\t\t\tif (sn_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_NAILGUN;\n\t\t\t\t\t}\n",
     "\t\t\t\t\tif (sn_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_NAILGUN;\n\t\t\t\t\t}\n"
     "\t\t\t\t\tif (sg_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SENTRY;\n"
     "\t\t\t\t\t\tdeathstring = \" is mown down by \";\n\t\t\t\t\t\tdeathstring2 = \"'s sentry gun\\n\";\n\t\t\t\t\t}\n"),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "sentry.qc", [
    ("\nhammer_defs.qc\n", "\nhammer_defs.qc\nsentry_defs.qc\n"),
    ("\nhammer.qc\n", "\nhammer.qc\nsentry.qc\n"),
])

# --- build_combat.py: copy the sentry sources with the other shared ones
patch(T + "build_combat.py", "sentry.qc", [
    ("\"hammer_defs.qc\", \"hammer.qc\")", "\"hammer_defs.qc\", \"hammer.qc\", \"sentry_defs.qc\", \"sentry.qc\")"),
])

# --- default.cfg: key B
patch(ROOT + "default.cfg", "impulse 70", [
    ("bind v \"impulse 20\"\t\t\t\t// melee\n", "bind v \"impulse 20\"\t\t\t\t// melee\nbind b \"impulse 70\"\t\t\t\t// sentry gun\n"),
])
