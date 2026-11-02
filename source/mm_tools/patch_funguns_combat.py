"""Combat+ (BakersfieldQuake): the five fun guns (IT_FUNGUN + .fg_sel, impulses 61-65) and the Bakersfield Memes loadout.

Run AFTER patch_megaman_combat.py and patch_banana_combat.py: it adds the fun-gun hooks next to the banana
ones, gives everyone every weapon and plenty of ammo on spawn (SetNewParms), starts deathmatch players
holding a random fun gun, and copies funguns_defs.qc / funguns.qc in. Safe to re-run (a file that
already mentions IT_FUNGUN is left alone).
python -I patch_megaman_combat.py && python -I patch_banana_combat.py && python -I patch_funguns_combat.py"""
import re

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"


def rd(p):
    return open(p, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(n, s):
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("wrote", n)


def rep(s, old, new, count=1):
    assert s.count(old) == count, "expected %d (%d): %r" % (count, s.count(old), old[:90])
    return s.replace(old, new)


def resub(s, pat, new):
    s2, n = re.subn(pat, new, s, count=1)
    assert n == 1, "pattern not found: " + pat[:90]
    return s2


# ---------------------------------------------------------------- weapons.qc
w = rd(D + "weapons.qc")
if "IT_FUNGUN" not in w:
    w = rep(w, "\tBanana_Precache();\n", "\tBanana_Precache();\n\tFunGun_Precache();\n")

    # W_SetCurrentAmmo: the fun gun shows its own ammo; the model depends on which one is out
    w = resub(w, r"(\t+)else if \(\(self\.weapon == IT_BANANA\)\)\n(\t+)\{\n\t+self\.currentammo = self\.bn_ammo;",
              lambda m: (m.group(1) + "else if ((self.weapon == IT_FUNGUN))\n" + m.group(2) + "{\n"
                         + m.group(2) + "\tself.currentammo = FunGun_Ammo(self, self.fg_sel);\n"
                         + m.group(2) + "\tself.weaponmodel = FunGun_VModel(self.fg_sel);\n"
                         + m.group(2) + "\tself.weaponframe = 0;\n"
                         + m.group(2) + "\taxeequipped = 0;\n" + m.group(2) + "}\n"
                         + m.group(0)))

    # W_CheckNoAmmo: they recharge by themselves
    w = rep(w, "\tif (((self.weapon == IT_MEGAMAN) || (self.weapon == IT_BANANA)))\n",
            "\tif ((((self.weapon == IT_MEGAMAN) || (self.weapon == IT_BANANA)) || (self.weapon == IT_FUNGUN)))\n")

    # W_Attack
    w = rep(w, "\tif ((self.weapon == IT_BANANA))\n\t{\n\t\tBanana_Attack();\n\t\treturn;\n\t}\n",
            "\tif ((self.weapon == IT_BANANA))\n\t{\n\t\tBanana_Attack();\n\t\treturn;\n\t}\n"
            "\tif ((self.weapon == IT_FUNGUN))\n\t{\n\t\tFunGun_Attack();\n\t\treturn;\n\t}\n")

    # impulse 9 hands them out too
    w = rep(w, "\tBanana_Give(self);\n", "\tBanana_Give(self);\n\tFunGun_Give(self);\n")

    # weapon cycling: ... Mega Man -> banana -> fun guns 1..6 -> axe (and back)
    w = rep(w, "it = (self.items | IT_BANANA);", "it = (self.items | IT_FUNGUN);", count=2)	# banana removed: it is never an owned weapon, so cycling skips it
    w = rep(w, "\t\tif ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n",
            "\t\tif ((self.weapon == IT_FUNGUN))\n\t\t{\n\t\t\tif (!FunGun_CycleNext())\n\t\t\t{\n\t\t\t\tself.weapon = IT_AXE;\n\t\t\t}\n\t\t}\n"
            "\t\telse if ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_FUNGUN;\n\t\t\tself.fg_sel = 1;\n\t\t}\n")
    w = rep(w, "\t\tif ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n",
            "\t\tif ((self.weapon == IT_FUNGUN))\n\t\t{\n\t\t\tif (!FunGun_CyclePrev())\n\t\t\t{\n\t\t\t\tself.weapon = IT_BANANA;\n\t\t\t}\n\t\t}\n"
            "\t\telse if ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n")
    w = resub(w, r"(if \(\(self\.weapon == IT_AXE\)\)\n\t+\{\n(\t+))self\.weapon = IT_BANANA;\n",
              lambda m: m.group(1) + "self.weapon = IT_FUNGUN;\n" + m.group(2) + "self.fg_sel = FG_COUNT;\n")

    w = rep(w, "\tif ((self.impulse == BN_IMPULSE))\n\t{\n\t\tBanana_Select();\n\t}\n",
            "\tif ((self.impulse == BN_IMPULSE))\n\t{\n\t\tBanana_Select();\n\t}\n"
            "\tif (((self.impulse >= FG_IMPULSE) && (self.impulse < (FG_IMPULSE + FG_COUNT))))\n\t{\n"
            "\t\tFunGun_Select(((self.impulse - FG_IMPULSE) + 1));\n\t}\n")
    w = rep(w, "\tBanana_ViewFrame();\n", "\tBanana_ViewFrame();\n\tFunGun_ViewFrame();\n")
    wr("weapons.qc", w)
else:
    print("weapons.qc already patched")

# ---------------------------------------------------------------- items.qc: backpacks never hand out a fun gun
it = rd(D + "items.qc")
if "IT_FUNGUN" not in it:
    it = rep(it, "((item.items == IT_MEGAMAN) || (item.items == IT_BANANA))",
             "(((item.items == IT_MEGAMAN) || (item.items == IT_BANANA)) || (item.items == IT_FUNGUN))")
    wr("items.qc", it)
else:
    print("items.qc already patched")

# ---------------------------------------------------------------- custom_effects.qc: the weapon-position helper draws the held weapon
ce = rd(D + "custom_effects.qc")
if "IT_FUNGUN" not in ce:
    block = ("\tif ((self.owner.weapon == IT_BANANA))\n\t{\n\t\tsetmodel(self, \"progs/v_banana.md3\");\n"
             "\t\tself.origin = '0 0 0';\n\t\tself.angles = '0 0 0';\n\t}\n")
    fg = ("\tif ((self.owner.weapon == IT_FUNGUN))\n\t{\n\t\tsetmodel(self, FunGun_VModel(self.owner.fg_sel));\n"
          "\t\tself.origin = '0 0 0';\n\t\tself.angles = '0 0 0';\n\t}\n")
    ce = rep(ce, block, block + fg, count=2)
    wr("custom_effects.qc", ce)
else:
    print("custom_effects.qc already patched")

# ---------------------------------------------------------------- client.qc
c = rd(D + "client.qc")
if "IT_FUNGUN" not in c:
    c = resub(c, r"(\telse if \(self\.owner\.weapon == IT_BANANA\)\n\t\tself\.vwep = \"\";[^\n]*\n)",
              lambda m: m.group(1) + "\telse if (self.owner.weapon == IT_FUNGUN)\n\t\tself.vwep = \"\";\n")

    # spawn: every fun gun, and in deathmatch you start holding a random one
    c = rep(c, "\tBanana_Give(self);\n\tW_SetCurrentAmmo();\n",
            "\tBanana_Give(self);\n\tFunGun_Give(self);\n\tif (deathmatch)\n\t{\n\t\tself.weapon = IT_FUNGUN;\n"
            "\t\tself.fg_sel = 1 + floor(random() * FG_COUNT);\n\t\tif ((self.fg_sel > FG_COUNT))\n\t\t{\n"
            "\t\t\tself.fg_sel = FG_COUNT;\n\t\t}\n\t}\n\tW_SetCurrentAmmo();\n")
    c = rep(c, "((self.weapon != IT_MEGAMAN) && (self.weapon != IT_BANANA))",
            "(((self.weapon != IT_MEGAMAN) && (self.weapon != IT_BANANA)) && (self.weapon != IT_FUNGUN))")
    c = resub(c, r"(\n(\t+)if \(bn_inflicting\)\n\t+\{\n\t+rnum = IT_BANANA;\n[^\n]*\n[^\n]*\n\t+\}\n)",
              lambda m: m.group(1) + m.group(2) + "if (fg_inflicting)\n" + m.group(2) + "{\n"
                        + m.group(2) + "\trnum = IT_FUNGUN;\n"
                        + m.group(2) + "\tdeathstring = FunGun_Death1(fg_inflicting);\n"
                        + m.group(2) + "\tdeathstring2 = FunGun_Death2(fg_inflicting);\n" + m.group(2) + "}\n")

    # Bakersfield Memes loadout: no hunting for guns. Axe, shotgun, super shotgun, both nailguns, grenade and
    # rocket launchers, lightning gun, laser cannon and chainsaw, with plenty of ammo
    c = rep(c, "void() SetNewParms =\n{\n\tparm1 = 4097;\n\tparm2 = 100;\n\tparm3 = 0;\n\tparm4 = 25;\n\tparm5 = 0;\n\tparm6 = 0;\n\tparm7 = 0;\n\tparm8 = 1;\n",
            "void() SetNewParms =\n{\n\tparm1 = 8458367;\n\tparm2 = 100;\n\tparm3 = 0;\n\tparm4 = 60;\n\tparm5 = 150;\n\tparm6 = 20;\n\tparm7 = 100;\n\tparm8 = IT_ROCKET_LAUNCHER;\n")
    wr("client.qc", c)
else:
    print("client.qc already patched")

# ---------------------------------------------------------------- frikbot: bots play with the fun guns too
bf = rd(D + "frikbot.bot_fight.qc")
if "FunGun_BotPick" not in bf:
    bf = rep(bf, "\tlocal vector v;\n\n\tit = self.items & 127;\n",
             "\tlocal vector v;\n\n\tif (FunGun_BotPick())\n\t{\n\t\treturn;\n\t}\n\tit = self.items & 127;\n")
    wr("frikbot.bot_fight.qc", bf)
else:
    print("frikbot.bot_fight.qc already patched")

# ---------------------------------------------------------------- progs.src + the shared sources
ps = rd(D + "progs.src")
if "funguns.qc" not in ps:
    ps = rep(ps, "\nbanana_defs.qc\n", "\nbanana_defs.qc\nfunguns_defs.qc\n")
    ps = rep(ps, "\nbanana.qc\n", "\nbanana.qc\nfunguns.qc\n")
    wr("progs.src", ps)
guard = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"
if "friends.qc" not in ps:
    ps = rep(ps, "\nfunguns.qc\n", "\nfunguns.qc\nfriends.qc\n")
    wr("progs.src", ps)
for n in ("funguns_defs.qc", "funguns.qc", "friends.qc"):
    wr(n, guard + rd(T + n))
