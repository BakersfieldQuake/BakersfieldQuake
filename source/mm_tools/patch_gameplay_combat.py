"""Combat+ (BakersfieldQuake) gameplay tweaks, applied to the decompiled QuakeC in qc_combat_decomp:
  1. holding jump keeps jumping (auto-bunnyhop, like Quake Champions)
  2. the grappling hook is gone (CheckGrapHook is never called, so impulse 98 and the swing physics never run)
  3. regenerating health: RG_DELAY seconds after the last damage, health climbs RG_RATE per second up to max_health
Run AFTER patch_megaman_combat.py, patch_banana_combat.py and patch_funguns_combat.py (it only touches client.qc,
combat.qc and defs_custom.qc, which those leave alone). Safe to re-run (markers).
python -I patch_gameplay_combat.py"""
import os
import shutil

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"


def rd(n):
    return open(D + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(n, s):
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("wrote", n)


def rep(s, old, new, count=1):
    assert s.count(old) == count, "expected %d (%d): %r" % (count, s.count(old), old[:90])
    return s.replace(old, new)


def backup(n):
    b = D + n + ".pre_gameplay"
    if not os.path.exists(b):
        shutil.copy(D + n, b)


# ---------------------------------------------------------------- defs_custom.qc: regen fields and tuning
d = rd("defs_custom.qc")
if "rg_hurt_t" not in d:
    backup("defs_custom.qc")
    d += '''
// ---- regenerating health (patch_gameplay_combat.py)
float	RG_DELAY	= 4;		// seconds after the last damage before health starts to come back
float	RG_RATE		= 10;		// health per second once it does
.float	rg_hurt_t;			// player: when they last took damage
.float	rg_frac;			// player: fractional health not yet added
.float	rg_last_t;			// player: when the regen code last ran
'''
    wr("defs_custom.qc", d)
else:
    print("defs_custom.qc already patched")

# ---------------------------------------------------------------- combat.qc: remember when a player was hurt
c = rd("combat.qc")
if "rg_hurt_t" not in c:
    backup("combat.qc")
    c = rep(c, "\ttake = ceil((damage - save));\n\tif ((targ.flags & FL_CLIENT))\n\t{\n",
            "\ttake = ceil((damage - save));\n\tif ((take > 0) && (targ.classname == \"player\"))\n\t{\n\t\ttarg.rg_hurt_t = time;\t// regenerating health waits for this\n\t}\n\tif ((targ.flags & FL_CLIENT))\n\t{\n")
    wr("combat.qc", c)
else:
    print("combat.qc already patched")

# ---------------------------------------------------------------- client.qc
q = rd("client.qc")
if "rg_hurt_t" not in q:
    backup("client.qc")
    # auto jump: holding the button re-arms the jump every time you are on the ground
    q = rep(q, "\tif (self.button2)\n\t{\n\t\tPlayerJump();\n\t}\n\telse\n\t{\n\t\tself.flags = (self.flags | FL_JUMPRELEASED);\n\t}\n\tif ((time < self.pausetime))",
            "\tif (self.button2)\n\t{\n\t\tif ((self.flags & FL_ONGROUND))\n\t\t{\n\t\t\tself.flags = (self.flags | FL_JUMPRELEASED);\t// hold jump = keep jumping\n\t\t}\n\t\tPlayerJump();\n\t}\n\telse\n\t{\n\t\tself.flags = (self.flags | FL_JUMPRELEASED);\n\t}\n\tif ((time < self.pausetime))")
    # no grappling hook
    q = rep(q, "\tif (((autocvar_mp_grapple && deathmatch) || autocvar_cheat_hook_sp))\n\t{\n\t\tCheckGrapHook();\n\t}\n", "")
    # regenerating health, ahead of the bot early-out so bots heal too
    q = rep(q, "void() PlayerPostThink =\n{\n\tif (BotPostFrame())",
            "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;\n\n"
            "\trg_dt = time - self.rg_last_t;\n\tself.rg_last_t = time;\n\tif (rg_dt > 0.2)\n\t\trg_dt = 0.2;\n"
            "\tif (((self.health > 0) && (self.health < self.max_health) && !self.deadflag && (time > (self.rg_hurt_t + RG_DELAY))))\n\t{\n"
            "\t\tself.rg_frac = (self.rg_frac + (RG_RATE * rg_dt));\n\t\tif ((self.rg_frac >= 1))\n\t\t{\n"
            "\t\t\trg_n = floor(self.rg_frac);\n\t\t\tself.rg_frac = (self.rg_frac - rg_n);\n"
            "\t\t\tself.health = self.health + rg_n;\n\t\t\tif ((self.health > self.max_health))\n\t\t\t{\n\t\t\t\tself.health = self.max_health;\n\t\t\t}\n\t\t}\n\t}\n"
            "\telse\n\t{\n\t\tself.rg_frac = 0;\n\t}\n"
            "\tif (BotPostFrame())")
    wr("client.qc", q)
else:
    print("client.qc already patched")

# ---------------------------------------------------------------- underdog: catch-up boosts and the leader's bounty (underdog.qc)
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"
d = rd("defs_custom.qc")
if "ud_level" not in d:
    d += """
// ---- underdog (underdog.qc, patch_gameplay_combat.py)
.float	ud_level;			// player: underdog level 0-5, set at spawn, drops one per kill
.float	ud_streak;			// player: deaths at other players' hands since their last kill
.float	ud_bounty;			// player: TRUE while they are the runaway leader
.float	ud_blueshell;		// player: their next Rob / Mega Man hunts the leader
.entity	ud_hunt;			// Rob / Mega Man: the leader it is hunting
float	ud_next_t;			// next bounty check
"""
    wr("defs_custom.qc", d)
else:
    print("defs_custom.qc underdog already patched")

ps = rd("progs.src")
if "underdog.qc" not in ps:
    ps = rep(ps, "\ncombat.qc\n", "\nunderdog.qc\ncombat.qc\n")
    wr("progs.src", ps)
open(D + "underdog.qc", "w", encoding="utf-8").write(open(T + "underdog.qc", encoding="utf-8").read())
print("wrote underdog.qc")

c = rd("combat.qc")
if "Underdog_" not in c:
    c = rep(c, "\tif ((attacker.super_damage_finished > time))\n\t{\n\t\tdamage = damage * 4;\n\t}\n",
            "\tif ((attacker.super_damage_finished > time))\n\t{\n\t\tdamage = damage * 4;\n\t}\n\tdamage = Underdog_Damage(targ, attacker, damage);\n")
    c = rep(c, "\tself.enemy = attacker;\n\tif ((self.flags & FL_MONSTER))\n",
            "\tUnderdog_Killed(targ, attacker);\n\tself.enemy = attacker;\n\tif ((self.flags & FL_MONSTER))\n")
    wr("combat.qc", c)
else:
    print("combat.qc underdog already patched")

q = rd("client.qc")
if "Underdog_" not in q:
    q = rep(q, "\tif (!autocvar_ent_fog)\n\t{\n\t\tlocalcmd(\"fog 0\\n\");\n\t}\n};",
            "\tif (!autocvar_ent_fog)\n\t{\n\t\tlocalcmd(\"fog 0\\n\");\n\t}\n\tUnderdog_Spawn();\n};")
    q = rep(q, "(time > (self.rg_hurt_t + RG_DELAY))", "(time > (self.rg_hurt_t + Underdog_RegenDelay()))")
    q = rep(q, "(RG_RATE * rg_dt)", "(Underdog_RegenRate() * rg_dt)")
    q = rep(q, "\telse\n\t{\n\t\tself.rg_frac = 0;\n\t}\n\tif (BotPostFrame())",
            "\telse\n\t{\n\t\tself.rg_frac = 0;\n\t}\n\tUnderdog_UpdateBounty();\n\tif (BotPostFrame())")
    wr("client.qc", q)
else:
    print("client.qc underdog already patched")


# ---------------------------------------------------------------- hit sounds (hitsound.qc): a tick for the attacker when a shot lands
ps = rd("progs.src")
if "hitsound.qc" not in ps:
    ps = rep(ps, "\nunderdog.qc\ncombat.qc\n", "\nunderdog.qc\nhitsound.qc\ncombat.qc\n")
    wr("progs.src", ps)
open(D + "hitsound.qc", "w", encoding="utf-8").write(open(T + "hitsound.qc", encoding="utf-8").read())
print("wrote hitsound.qc")

c = rd("combat.qc")
if "HitSound_" not in c:
    c = rep(c, "\t\tif ((targ.classname == \"monster_zombie\"))\n\t\t{\n\t\t\ttarg.painskin_helper = 1;\n\t\t}\n\t}\n\tif ((targ.health <= 0))\n",
            "\t\tif ((targ.classname == \"monster_zombie\"))\n\t\t{\n\t\t\ttarg.painskin_helper = 1;\n\t\t}\n\t\tHitSound_Play(targ, attacker, take);\n\t}\n\tif ((targ.health <= 0))\n")
    wr("combat.qc", c)
else:
    print("combat.qc hit sound already patched")

w = rd("weapons.qc")
if "HitSound_" not in w:
    w = rep(w, "\tMegaMan_Precache();\n", "\tMegaMan_Precache();\n\tHitSound_Precache();\n")
    wr("weapons.qc", w)
else:
    print("weapons.qc hit sound already patched")


# ---------------------------------------------------------------- FrikBot: the decompiler lost the range check, so bots never fired
# weapon_range() returns (best, min, max); the decompiled bot_fight_style compared against 0 and 0 instead of v_y and v_z,
# which is never true, so bot_shoot() was unreachable. Restored to the original FrikBot test.
bf = rd("frikbot.bot_fight.qc")
broken = "\tif (((foedist > 0) && (foedist < 0)))\n\t{\n\t\ttraceline((self.origin + self.view_ofs), ((self.origin + self.view_ofs) + (v_forward * 0)), FALSE, self);\n\t\tif ((vlen((trace_endpos - (self.origin + self.view_ofs))) >= 0))"
if broken in bf:
    backup("frikbot.bot_fight.qc")
    bf = rep(bf, broken, "\tif (((foedist > v_y) && (foedist < v_z)))\n\t{\n\t\ttraceline((self.origin + self.view_ofs), ((self.origin + self.view_ofs) + (v_forward * v_z)), FALSE, self);\n\t\tif ((vlen((trace_endpos - (self.origin + self.view_ofs))) >= v_y))")
    wr("frikbot.bot_fight.qc", bf)
else:
    print("frikbot.bot_fight.qc range check already fixed")

# bots: shooting ranges (best, min, max) for our weapons, which weapon_range() did not know (it returned nothing)
bf = rd("frikbot.bot_fight.qc")
if "IT_FUNGUN" not in bf.split("vector(float wep) weapon_range =")[1][:400]:
    bf = rep(bf, "vector(float wep) weapon_range =\n{\n",
             "vector(float wep) weapon_range =\n{\n\tif ((wep == IT_FUNGUN))\n\t{\n\t\treturn ('400 0 2500');\n\t}\n\tif ((wep == IT_MEGAMAN))\n\t{\n\t\treturn ('300 0 1500');\n\t}\n")
    wr("frikbot.bot_fight.qc", bf)
else:
    print("weapon_range already knows the fun guns")
