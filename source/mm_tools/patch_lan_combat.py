"""Bakersfield LAN rules for Combat+ (BakersfieldQuake): magazines + reload, spawn protection, less self-damage,
no fall damage, suicides never cost frags, map playlist, intermission auto-advance, HUD stats, bot fill,
and the frag-gap catch-up rewrite in underdog.qc. The code lives in bm_defs.qc / bm_reload.qc / bm_match.qc /
underdog.qc; this script only adds the hooks to the decompiled game code in qc_combat_decomp.

Run AFTER patch_megaman_combat.py, patch_banana_combat.py, patch_funguns_combat.py and patch_gameplay_combat.py.
Safe to re-run (markers). Then python -I build_combat.py compiles and installs progs.dat.
python -I patch_lan_combat.py"""
import os
import re
import shutil

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"
GUARD = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"


def rd(n):
    return open(D + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(n, s):
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("wrote", n)


def rep(s, old, new, count=1):
    assert s.count(old) == count, "expected %d (%d): %r" % (count, s.count(old), old[:90])
    return s.replace(old, new)


def backup(n):
    b = D + n + ".pre_lan"
    if not os.path.exists(b):
        shutil.copy(D + n, b)


# ---------------------------------------------------------------- the shared sources
for n in ("bm_defs.qc", "bm_reload.qc", "bm_match.qc", "bm_fun.qc"):
    s = open(T + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(GUARD + s)
    print("copied", n)
open(D + "underdog.qc", "w", encoding="utf-8").write(open(T + "underdog.qc", encoding="utf-8").read())
print("copied underdog.qc")

# ---------------------------------------------------------------- progs.src
ps = rd("progs.src")
if "bm_defs.qc" not in ps:
    backup("progs.src")
    ps = rep(ps, "\nfunguns_defs.qc\n", "\nfunguns_defs.qc\nbm_defs.qc\n")
    ps = rep(ps, "\nweapons.qc\n", "\nweapons.qc\nbm_reload.qc\nbm_match.qc\nbm_fun.qc\n")
    wr("progs.src", ps)
else:
    print("progs.src already patched")

# ---------------------------------------------------------------- weapons.qc
w = rd("weapons.qc")
if "BM_Frame" not in w:
    backup("weapons.qc")
    w = rep(w, "\tMegaMan_Precache();\n", "\tMegaMan_Precache();\n\tBM_Precache();\n")
    w = rep(w, "void() W_SetCurrentAmmo =\n{\n\tplayer_run();\n",
            "void() W_SetCurrentAmmo =\n{\n\tBM_SwapIn();\t// LAN magazines: bank the old gun's, load the new one's\n\tplayer_run();\n")
    w = rep(w, "float() W_CheckNoAmmo =\n{\n",
            "float() W_CheckNoAmmo =\n{\n\tif (BM_CurSlot())\n\t{\n\t\treturn (BM_CheckNoAmmo());\t// empty magazine: reload, don't switch\n\t}\n")
    w = rep(w, "void() W_WeaponFrame =\n{\n\tMegaMan_ViewFrame();\n",
            "void() W_WeaponFrame =\n{\n\tBM_Frame();\n\tBM_LifeFrame();\n\tBM_TestImpulses();\n\tMegaMan_ViewFrame();\n")
    # running dry mid-burst (shotgun, LG, nailguns): reload instead of switching away
    w, n = re.subn(r"self\.weapon = W_BestWeapon\(\);\n(\t+)W_SetCurrentAmmo\(\);\n", r"BM_OutOfAmmo();\n", w)
    assert n == 4, n		# 3 fire functions + W_CheckNoAmmo (non-magazine guns still switch, see BM_OutOfAmmo)
    # weapon change: the ammo_* fields show other guns' magazines, so never refuse a switch for "no ammo"
    w = rep(w, "\tif (am)\n", "\tif (autocvar_bm_reload)\n\t{\n\t\tam = 0;\n\t}\n\tif (am)\n")
    # QC super shotgun burst: per player instead of one global for everyone
    w = rep(w, "\t\t\t\t\tif ((autocvar_pushbacklight == 15))\n\t\t\t\t\t{\n\t\t\t\t\t\tself.attack_finished = (time + 0.95);\n\t\t\t\t\t\tautocvar_pushbacklight = 16;\n\t\t\t\t\t}\n\t\t\t\t\telse\n\t\t\t\t\t{\n\t\t\t\t\t\tself.attack_finished = (time + 0.15);\n\t\t\t\t\t\tautocvar_pushbacklight = 15;\n\t\t\t\t\t}\n",
            "\t\t\t\t\tBM_FiredSSG();\n")
    w = rep(w, "\t\t\t\tif (((autocvar_vanilla_ssg == 0) && (autocvar_pushbacklight == 15)))\n\t\t\t\t{\n\t\t\t\t\tautocvar_pushbacklight = 16;\n\t\t\t\t}\n",
            "\t\t\t\tif (((autocvar_vanilla_ssg == 0) && (self.bm_ssgburst == 15)))\n\t\t\t\t{\n\t\t\t\t\tself.bm_ssgburst = 16;\n\t\t\t\t}\n")
    w = rep(w, "(autocvar_vanilla_ssg == 0)) && (autocvar_pushbacklight == 15)) && ((time - 0.45) < self.attack_finished)",
            "(autocvar_vanilla_ssg == 0)) && (self.bm_ssgburst == 15)) && ((time - 0.45) < self.attack_finished)")
    wr("weapons.qc", w)
else:
    print("weapons.qc already patched")

p = rd("player.qc")
if "BM_OutOfAmmo" not in p:
    backup("player.qc")
    p, n = re.subn(r"self\.weapon = W_BestWeapon\(\);\n(\t+)W_SetCurrentAmmo\(\);\n", r"BM_OutOfAmmo();\n", p)
    assert n == 4, n
    p = rep(p, "if (((autocvar_vanilla_ssg == 0) && (autocvar_pushbacklight != 15)))",
            "if (((autocvar_vanilla_ssg == 0) && (self.bm_ssgburst != 15)))", 2)
    wr("player.qc", p)
else:
    print("player.qc already patched")

# ---------------------------------------------------------------- combat.qc
c = rd("combat.qc")
if "BM_Damage" not in c:
    backup("combat.qc")
    c = rep(c, "\tdamage = Underdog_Damage(targ, attacker, damage);\n",
            "\tdamage = Underdog_Damage(targ, attacker, damage);\n\tdamage = BM_Damage(targ, inflictor, attacker, damage);\t// spawn protection, less self-damage\n")
    c = rep(c, "\t\ttarg.velocity = (targ.velocity + ((dir * damage) * 8));\n",
            "\t\ttarg.velocity = (targ.velocity + ((dir * bm_kb) * 8));\t// full push, even when the damage was scaled down\n")
    c = rep(c, "\tif ((targ.flags & FL_GODMODE))\n\t{\n\t\treturn;\n\t}\n",
            "\tif (bm_blocked)\n\t{\n\t\treturn;\t// spawn protection soaked it up\n\t}\n\tif ((targ.flags & FL_GODMODE))\n\t{\n\t\treturn;\n\t}\n")
    wr("combat.qc", c)
else:
    print("combat.qc already patched")

# ---------------------------------------------------------------- client.qc
q = rd("client.qc")
if "BM_Spawn" not in q:
    backup("client.qc")
    # kill command: just die (world deaths cost nothing now), no stale 'other' handing out frags
    q = rep(q, "void() ClientKill =\n{\n\tbprint(self.netname);\n\tbprint(\" suicides\\n\");\n\tT_Damage(self, other, other, 300);\n\tself.frags = (self.frags - 2);\n};",
            "void() ClientKill =\n{\n\tif ((self.health <= 0) || intermission_running)\n\t{\n\t\treturn;\n\t}\n\tself.bm_prot_t = 0;\n\tself.invincible_finished = 0;\n\tself.deathtype = \"suicide\";\n\tT_Damage(self, world, world, 50000);\n};")
    q = rep(q, "\tW_SetCurrentAmmo();\n\tself.attack_finished = time;\n\tself.th_pain = player_pain;\n",
            "\tBM_Spawn();\t// full magazines\n\tW_SetCurrentAmmo();\n\tself.attack_finished = time;\n\tself.th_pain = player_pain;\n")
    q = rep(q, "\tUnderdog_Spawn();\n};", "\tUnderdog_Spawn();\n\tBM_PlayerSpawned();\t// spawn protection\n};")
    # empty gun: the magazine reloads, no switching to the "best" weapon
    q = rep(q, "\tif ((((((time > self.attack_finished) && (self.currentammo == 0))",
            "\tif (!autocvar_bm_reload && (((((time > self.attack_finished) && (self.currentammo == 0))")
    q = rep(q, "\t\t\t\tT_Damage(self, world, world, 5);\n",
            "\t\t\t\tif (autocvar_bm_falldamage)\n\t\t\t\t{\n\t\t\t\t\tT_Damage(self, world, world, 5);\n\t\t\t\t}\n")
    # suicides, telefrag bounces, lava, falls, monsters: no frag lost
    q = rep(q, "\t\t\tbprint(\"'s telefrag\\n\");\n\t\t\ttarg.frags = (targ.frags - 1);\n", "\t\t\tbprint(\"'s telefrag\\n\");\n")
    q = rep(q, "\t\t\t\tattacker.frags = (attacker.frags - 1);\n\t\t\t\tbprint(targ.netname);\n\t\t\t\tif (((targ.weapon == 64)",
            "\t\t\t\tbprint(targ.netname);\n\t\t\t\tif (((targ.weapon == 64)")
    q = rep(q, "\t\t\ttarg.frags = (targ.frags - 1);\n\t\t\tbprint(targ.netname);\n\t\t\tif ((attacker.flags & FL_MONSTER))",
            "\t\t\tbprint(targ.netname);\n\t\t\tif ((attacker.flags & FL_MONSTER))")
    q = rep(q, "\t\t\tif ((deathmatch && (attacker.ishuman == 1)))\n\t\t\t{\n\t\t\t\tif (((attacker.weapon == IT_CHAINSAW)",
            "\t\t\tif ((deathmatch && (attacker.ishuman == 1) && (targ != attacker)))\n\t\t\t{\n\t\t\t\tif (((attacker.weapon == IT_CHAINSAW)")
    # map playlist and intermission auto-advance
    q = rep(q, "void() NextLevel =\n{\n\tlocal entity o;\n\n", "void() NextLevel =\n{\n\tlocal entity o;\n\n\tif (BM_NextLevel())\n\t{\n\t\treturn;\t// bm_maplist\n\t}\n")
    q = rep(q, "void() IntermissionThink =\n{\n", "void() IntermissionThink =\n{\n\tif (BM_IntermissionThink())\n\t{\n\t\treturn;\n\t}\n")
    wr("client.qc", q)
else:
    print("client.qc already patched")

# ---------------------------------------------------------------- items.qc: picking up a gun never switches to it
it = rd("items.qc")
if "BM_NoPickupSwitch" not in it:
    backup("items.qc")
    it = rep(it, "void(float old, float new) Deathmatch_Weapon =\n{\n\tlocal float or;\n\tlocal float nr;\n\n",
             "void(float old, float new) Deathmatch_Weapon =\n{\n\tlocal float or;\n\tlocal float nr;\n\n\tif (autocvar_bm_reload)\n\t{\n\t\treturn;\t// BM_NoPickupSwitch: everyone already has every gun\n\t}\n")
    wr("items.qc", it)
else:
    print("items.qc already patched")

# ---------------------------------------------------------------- world.qc
wo = rd("world.qc")
if "BM_Stats" not in wo:
    backup("world.qc")
    wo = rep(wo, "\tclientstat(51, 2, gametype);\n", "\tclientstat(51, 2, gametype);\n\tBM_Stats();\n")
    wo = rep(wo, "void() StartFrame =\n{\n\tBotFrame();\n", "void() StartFrame =\n{\n\tBotFrame();\n\tBM_StartFrame();\n")
    wr("world.qc", wo)
else:
    print("world.qc already patched")

# ---------------------------------------------------------------- client.qc: obituary polish, one-line kill command, the empty trail effect
q = rd("client.qc")
if "was lasered by" not in q:
    q = rep(q, '\t\tself.traileffectnum = particleeffectnum(/*1i*/"");\n', '\t\tself.traileffectnum = 0;\t// BM: was particleeffectnum(""), which is -1 and spams "Unknown effect number 65535"\n', 2)
    q = rep(q, '\tbprint(self.netname, " suicides\\n");\n\tself.bm_prot_t = 0;\n', '\tself.bm_prot_t = 0;\n', 1)
    q = rep(q, '\t\t\tbprint(targ.netname);\n\t\t\tif ((attacker.flags & FL_MONSTER))\n', '\t\t\tif ((targ.deathtype == "suicide"))\n\t\t\t{\n\t\t\t\ttarg.deathtype = "";\n\t\t\t\tbprint(targ.netname, " suicides\\n");\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tbprint(targ.netname);\n\t\t\tif ((attacker.flags & FL_MONSTER))\n', 1)
    q = rep(q, '\t\t\t\tif ((targ.weapon == IT_GRENADE_LAUNCHER))\n\t\t\t\t{\n\t\t\t\t\tbprint(" tries to put the pin back in\\n");\n\t\t\t\t}\n', '\t\t\t\tif (mm_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint(" got run over by their own Mega Man\\n");\n\t\t\t\t\treturn;\n\t\t\t\t}\n\t\t\t\tif (bn_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint("\'s girlfriend had enough\\n");\n\t\t\t\t\treturn;\n\t\t\t\t}\n\t\t\t\tif (sg_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint(" was mown down by their own sentry gun\\n");\n\t\t\t\t\treturn;\n\t\t\t\t}\n\t\t\t\tif ((fg_inflicting == FG_PICKLE))\n\t\t\t\t{\n\t\t\t\t\tbprint(" surprised themself\\n");\n\t\t\t\t\treturn;\n\t\t\t\t}\n\t\t\t\tif ((fg_inflicting == FG_DOB))\n\t\t\t\t{\n\t\t\t\t\tbprint(" blew their own head off\\n");\n\t\t\t\t\treturn;\n\t\t\t\t}\n\t\t\t\tif ((targ.weapon == IT_GRENADE_LAUNCHER))\n\t\t\t\t{\n\t\t\t\t\tbprint(" drowned in their own JohnWave\\n");\n\t\t\t\t}\n', 1)
    q = rep(q, '\t\t\t\t\trnum = attacker.weapon;\n\t\t\t\t\tif (mm_inflicting)\n', '\t\t\t\t\trnum = attacker.weapon;\n\t\t\t\t\tdeathstring = " was killed by ";\n\t\t\t\t\tdeathstring2 = "\\n";\n\t\t\t\t\tif (mm_inflicting)\n', 1)
    q = rep(q, '\t\t\t\t\t\tdeathstring = " got bonked by ";\t// Bonk Hammer\n\t\t\t\t\t\tdeathstring2 = "\'s hammer\\n";\n', '\t\t\t\t\t\tdeathstring = " got bonked by ";\t// Bonk Hammer\n\t\t\t\t\t\tdeathstring2 = "\'s hammer\\n";\n\t\t\t\t\t\tif ((attacker.hm_tier == 3))\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\tdeathstring = " got sent flying by ";\n\t\t\t\t\t\t}\n', 1)
    q = rep(q, '\t\t\t\t\t\tdeathstring = " eats ";\n\t\t\t\t\t\tdeathstring2 = "\'s pineapple\\n";\n\t\t\t\t\t\tif ((targ.health < -40))\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\tdeathstring = " was gibbed by ";\n\t\t\t\t\t\t\tdeathstring2 = "\'s grenade\\n";\n', '\t\t\t\t\t\tdeathstring = " got a face full of ";\t// the grenade is JohnWave\'s head\n\t\t\t\t\t\tdeathstring2 = "\'s JohnWave\\n";\n\t\t\t\t\t\tif ((targ.health < -40))\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\tdeathstring = " was washed away by ";\n\t\t\t\t\t\t\tdeathstring2 = "\'s JohnWave\\n";\n', 1)
    q = rep(q, '\t\t\t\t\t\t\tdeathstring2 = "\'s shaft\\n";\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t\tbprint(targ.netname);\n', '\t\t\t\t\t\t\tdeathstring2 = "\'s shaft\\n";\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t\tif ((rnum == IT_LASER_CANNON))\n\t\t\t\t\t{\n\t\t\t\t\t\tdeathstring = " was lasered by ";\n\t\t\t\t\t\tdeathstring2 = "\\n";\n\t\t\t\t\t}\n\t\t\t\t\tbprint(targ.netname);\n', 1)
    wr("client.qc", q)
else:
    print("client.qc obituary already patched")
