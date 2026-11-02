"""Hook the JohnWave grenade (BakersfieldQuake\source\mm_tools\\jg_splash.qc) into the Combat+ source in qc_combat_decomp.
Marker-guarded (safe to re-run), keeps *.pre_jg backups.  The grenade head is JohnWave's: see the top of jg_splash.qc.
python -I patch_jg_combat.py"""
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
    shutil.copy(path, path + ".pre_jg")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


# --- weapons.qc: precache, the explosion, the bounce, the fuse think, the launch
patch(D + "weapons.qc", "JG_", [
    ("\tBM_Precache();\n\tHitSound_Precache();\n",
     "\tBM_Precache();\n\tJG_SplashPrecache();\t// JohnWave grenade: splash sprites and sound (jg_splash.qc)\n\tHitSound_Precache();\n"),

    # damage and the 20% fire stay as they were; the explosion look and sound become the water splash
    ("\t\tspawn_fire();\n\t}\n\tif (((other.classname == \"monster_shambler\") || (other.classname == \"monster_hell_knight2\")))\n"
     "\t{\n\t\tsendParticle(\"rocket_resist\", self.origin, VEC_ORIGIN, 1);\n\t\tsparklers(1);\n\t\tsparklers(1);\n\t}\n\telse\n\t{\n\t\tsparklers();\n\t\tsparklers(2);\n\t\tif ((autocvar_explosiondebris == 0))\n"
     "\t\t{\n\t\t\tif ((pointcontents(self.origin) == CONTENT_SLIME))\n\t\t\t{\n\t\t\t\tsendParticle(\"slimesplash\", self.origin, VEC_ORIGIN, 1);\n\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\tif ((autocvar_effects_classic_explosion == 1))\n"
     "\t\t\t\t{\n\t\t\t\t\tsendParticle(\"rocket_explo_classic\", self.origin, VEC_ORIGIN, 1);\n\t\t\t\t}\n\t\t\t\telse\n\t\t\t\t{\n\t\t\t\t\tif (other.health)\n\t\t\t\t\t{\n\t\t\t\t\t\tsendParticle(\"grenade_explosion_nodebris\", self.origin, VEC_ORIGIN, 1);\n",
     "\t\tspawn_fire();\n\t}\n\tJG_Splash();\t// JohnWave's head goes off as a water splash (jg_splash.qc)\n\treturn;\n"
     "\tif (((other.classname == \"monster_shambler\") || (other.classname == \"monster_hell_knight2\")))\n"
     "\t{\n\t\tsendParticle(\"rocket_resist\", self.origin, VEC_ORIGIN, 1);\n\t\tsparklers(1);\n\t\tsparklers(1);\n\t}\n\telse\n\t{\n\t\tsparklers();\n\t\tsparklers(2);\n\t\tif ((autocvar_explosiondebris == 0))\n"
     "\t\t{\n\t\t\tif ((pointcontents(self.origin) == CONTENT_SLIME))\n\t\t\t{\n\t\t\t\tsendParticle(\"slimesplash\", self.origin, VEC_ORIGIN, 1);\n\t\t\t}\n\t\t\telse\n\t\t\t{\n\t\t\t\tif ((autocvar_effects_classic_explosion == 1))\n"
     "\t\t\t\t{\n\t\t\t\t\tsendParticle(\"rocket_explo_classic\", self.origin, VEC_ORIGIN, 1);\n\t\t\t\t}\n\t\t\t\telse\n\t\t\t\t{\n\t\t\t\t\tif (other.health)\n\t\t\t\t\t{\n\t\t\t\t\t\tsendParticle(\"grenade_explosion_nodebris\", self.origin, VEC_ORIGIN, 1);\n"),

    # a bounce sets the head tumbling; the fuse think (GLhitboxes, every 0.025 s) turns it to face the shooter / lie face up
    ("\tsound7(self, CHAN_WEAPON, \"weapons/bounce.wav\", 1, ATTN_NORM, SNDSPD);\n\tif ((self.velocity == VEC_ORIGIN))\n\t{\n\t\tself.avelocity = VEC_ORIGIN;\n\t}\n};\n\nvoid() GLhitboxes =\n{\n\tlocal entity glhb;\n\n",
     "\tsound7(self, CHAN_WEAPON, \"weapons/bounce.wav\", 1, ATTN_NORM, SNDSPD);\n\tJG_GrenadeBounce();\t// tumble\n\tif ((self.velocity == VEC_ORIGIN))\n\t{\n\t\tself.avelocity = VEC_ORIGIN;\n\t}\n};\n\nvoid() GLhitboxes =\n{\n\tlocal entity glhb;\n\n\tJG_GrenadeAnimate();\t// face the shooter / lie face up (jg_splash.qc)\n"),

    # the launch: face back at the shooter instead of spinning (the grenade box stays a point: a real box gets stuck on Combat+)
    ("\tmissile.avelocity = '300 300 300';\n\tmissile.angles = vectoangles(missile.velocity);\n\tmissile.touch = GrenadeTouch;\n\tsetmodel(missile, \"progs/grenade.mdl\");\n\tsetsize(missile, VEC_ORIGIN, VEC_ORIGIN);\n",
     "\tmissile.touch = GrenadeTouch;\n\tJG_GrenadeLaunch(missile, self.v_angle_y);\t// face looks back at you (jg_splash.qc)\n\tsetmodel(missile, \"progs/grenade.mdl\");\n\tsetsize(missile, VEC_ORIGIN, VEC_ORIGIN);\n"),
])

# --- ogre.qc: the ogre throws JohnWave's head too (not the skull a dead ogre throws)
patch(D + "ogre.qc", "JG_", [
    ("\t\tT_RadiusDamage(self, self.owner, autocvar_ogre_grenade, world);\n\t}\n\tif ((((pointcontents(self.origin) == CONTENT_WATER)",
     "\t\tT_RadiusDamage(self, self.owner, autocvar_ogre_grenade, world);\n\t}\n"
     "\tif ((self.model == \"progs/grenade.mdl\"))\n\t{\n\t\tJG_Splash();\t// JohnWave's head goes off as a water splash (jg_splash.qc)\n\t\treturn;\n\t}\n"
     "\tif ((((pointcontents(self.origin) == CONTENT_WATER)"),
])

# --- progs.src: compiled before weapons.qc
patch(D + "progs.src", "jg_splash", [
    ("env_effects.qc\nweapons.qc\n", "env_effects.qc\njg_splash.qc\nweapons.qc\n"),
])

# --- build_combat.py: copy it with the other shared sources
patch(T + "build_combat.py", "jg_splash.qc", [
    ("\"bm_defs.qc\", \"bm_reload.qc\", \"bm_match.qc\"):", "\"bm_defs.qc\", \"bm_reload.qc\", \"bm_match.qc\", \"jg_splash.qc\"):"),
])
