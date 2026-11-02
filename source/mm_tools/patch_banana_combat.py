"""Combat+ (BakersfieldQuake): the banana gun as a second custom weapon (IT_BANANA, impulse 15).

Run AFTER patch_megaman_combat.py (which rebuilds weapons.qc / items.qc / custom_effects.qc from the
pristine copies and patches client.qc / progs.src): this script adds the banana hooks on top of
those files, next to the Mega Man ones, and copies banana_defs.qc / banana.qc in. Safe to re-run
(a file that already mentions IT_BANANA is left alone).
python -I patch_megaman_combat.py && python -I patch_banana_combat.py"""
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
if "IT_BANANA" not in w:
    w = rep(w, "\tMegaMan_Precache();\n", "\tMegaMan_Precache();\n\tBanana_Precache();\n")

    # W_SetCurrentAmmo: the banana gun shows its own bananas as the ammo count
    w = resub(w, r"(\t+)else if \(\(self\.weapon == IT_MEGAMAN\)\)\n(\t+)\{\n\t+self\.currentammo = self\.mm_ammo;",
              lambda m: (m.group(1) + "else if ((self.weapon == IT_BANANA))\n" + m.group(2) + "{\n"
                         + m.group(2) + "\tself.currentammo = self.bn_ammo;\n"
                         + m.group(2) + "\tself.weaponmodel = \"progs/v_banana.md3\";\n"
                         + m.group(2) + "\tself.weaponframe = 0;\n"
                         + m.group(2) + "\taxeequipped = 0;\n" + m.group(2) + "}\n"
                         + m.group(1) + "else if ((self.weapon == IT_MEGAMAN))\n" + m.group(2) + "{\n"
                         + m.group(2) + "\tself.currentammo = self.mm_ammo;"))

    # W_CheckNoAmmo: it recharges by itself
    w = rep(w, "\tif ((self.weapon == IT_MEGAMAN))\n\t{\n\t\treturn (TRUE);\n\t}\n",
            "\tif (((self.weapon == IT_MEGAMAN) || (self.weapon == IT_BANANA)))\n\t{\n\t\treturn (TRUE);\n\t}\n")

    # W_Attack
    w = rep(w, "\tif ((self.weapon == IT_MEGAMAN))\n\t{\n\t\tMegaMan_Attack();\n\t\treturn;\n\t}\n",
            "\tif ((self.weapon == IT_MEGAMAN))\n\t{\n\t\tMegaMan_Attack();\n\t\treturn;\n\t}\n"
            "\tif ((self.weapon == IT_BANANA))\n\t{\n\t\tBanana_Attack();\n\t\treturn;\n\t}\n")

    # impulse 9 hands it out too
    w = rep(w, "\tMegaMan_Give(self);\n", "\tMegaMan_Give(self);\n\tBanana_Give(self);\n")

    # weapon cycling: ... laser cannon -> Mega Man -> banana -> axe (and back). Nobody owns it as an item bit,
    # so the (items & weapon) test in both loops gets IT_BANANA ORed in.
    w = rep(w, "\tit = self.items;\n\tself.impulse = 0;\n\tself.idletimer = 1;\n\tself.switchtimer = -8;\n",
            "\tit = (self.items | IT_BANANA);\n\tself.impulse = 0;\n\tself.idletimer = 1;\n\tself.switchtimer = -8;\n", count=2)
    w = rep(w, "\t\tif ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n",
            "\t\tif ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n"
            "\t\telse if ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_BANANA;\n\t\t}\n")
    w = rep(w, "\t\tif ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_LASER_CANNON;\n",
            "\t\tif ((self.weapon == IT_BANANA))\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n"
            "\t\telse if ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_LASER_CANNON;\n")
    w = resub(w, r"(if \(\(self\.weapon == IT_AXE\)\)\n\t+\{\n\t+)self\.weapon = IT_MEGAMAN;\n",
              lambda m: m.group(1) + "self.weapon = IT_BANANA;\n")

    w = rep(w, "\tif ((self.impulse == MM_IMPULSE))\n\t{\n\t\tMegaMan_Select();\n\t}\n",
            "\tif ((self.impulse == MM_IMPULSE))\n\t{\n\t\tMegaMan_Select();\n\t}\n"
            "\tif ((self.impulse == BN_IMPULSE))\n\t{\n\t\tBanana_Select();\n\t}\n")
    w = rep(w, "\tMegaMan_ViewFrame();\n", "\tMegaMan_ViewFrame();\n\tBanana_ViewFrame();\n")
    wr("weapons.qc", w)
else:
    print("weapons.qc already patched")

# ---------------------------------------------------------------- items.qc: backpacks never hand out the banana gun
it = rd(D + "items.qc")
if "IT_BANANA" not in it:
    it = rep(it, "\tif ((item.items == IT_MEGAMAN))\n", "\tif (((item.items == IT_MEGAMAN) || (item.items == IT_BANANA)))\n")
    wr("items.qc", it)
else:
    print("items.qc already patched")

# ---------------------------------------------------------------- custom_effects.qc: the weapon-position helper draws the held weapon
ce = rd(D + "custom_effects.qc")
if "IT_BANANA" not in ce:
    block = ("\tif ((self.owner.weapon == IT_MEGAMAN))\n\t{\n\t\tsetmodel(self, \"progs/v_megaman.md3\");\n"
             "\t\tself.origin = '0 0 0';\n\t\tself.angles = '0 0 0';\n\t}\n")
    ce = rep(ce, block, block + block.replace("IT_MEGAMAN", "IT_BANANA").replace("v_megaman", "v_banana"), count=2)
    wr("custom_effects.qc", ce)
else:
    print("custom_effects.qc already patched")

# ---------------------------------------------------------------- client.qc
c = rd(D + "client.qc")
if "IT_BANANA" not in c:
    c = resub(c, r"(\telse if \(self\.owner\.weapon == IT_MEGAMAN\)\n\t\tself\.vwep = \"\";[^\n]*\n)",
              lambda m: m.group(1) + "\telse if (self.owner.weapon == IT_BANANA)\n\t\tself.vwep = \"\";\t// the banana gun has its own little banana (Banana_UpdateVwep)\n")
    c = rep(c, "\tMegaMan_Give(self);\n", "\tMegaMan_Give(self);\n\tBanana_Give(self);\n")
    c = rep(c, "(self.weapon != IT_MEGAMAN)", "((self.weapon != IT_MEGAMAN) && (self.weapon != IT_BANANA))")
    c = resub(c, r"(\n(\t+)if \(mm_inflicting\)\n\t+\{\n\t+rnum = IT_MEGAMAN;\n[^\n]*\n[^\n]*\n\t+\}\n)",
              lambda m: m.group(1) + m.group(2) + "if (bn_inflicting)\n" + m.group(2) + "{\n"
                        + m.group(2) + "\trnum = IT_BANANA;\n"
                        + m.group(2) + "\tdeathstring = \" was blown up by \";\n"
                        + m.group(2) + "\tdeathstring2 = \"'s girlfriend\\n\";\n" + m.group(2) + "}\n")
    wr("client.qc", c)
else:
    print("client.qc already patched")

# ---------------------------------------------------------------- progs.src + the shared sources
ps = rd(D + "progs.src")
if "banana.qc" not in ps:
    ps = rep(ps, "\nmegaman_defs.qc\n", "\nmegaman_defs.qc\nbanana_defs.qc\n")
    ps = rep(ps, "\nmegaman.qc\n", "\nmegaman.qc\nbanana.qc\n")
    wr("progs.src", ps)
guard = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"
for n in ("banana_defs.qc", "banana.qc"):
    wr(n, guard + rd(T + n))
