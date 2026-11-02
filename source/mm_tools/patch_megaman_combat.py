"""Combat+ (BakersfieldQuake): Mega Man gun as its own weapon (IT_MEGAMAN = 128, impulse 14).

Rebuilds weapons.qc / player.qc / items.qc / custom_effects.qc from the pristine copies
(weapons.qc.orig_decomp, *.pre_viewmodel), so the rocket launcher is the stock one again,
then hooks in the shared BakersfieldQuake/source/mm_tools/megaman_defs.qc + megaman.qc (compiled with COMBATPLUS).
client.qc and progs.src are patched in place. Safe to re-run.
python -I patch_megaman_combat.py"""
import re

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"


def rd(p):
    return open(p, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(n, s):
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("wrote", n)


def rep(s, old, new):
    assert s.count(old) == 1, "expected once (%d): %r" % (s.count(old), old[:90])
    return s.replace(old, new, 1)


def resub(s, pat, new):
    s2, n = re.subn(pat, new, s, count=1)
    assert n == 1, "pattern not found: " + pat[:90]
    return s2


# ---------------------------------------------------------------- weapons.qc
w = rd(D + "weapons.qc.orig_decomp")
w = rep(w, "void() W_Precache =\n{\n", "void() W_Precache =\n{\n\tMegaMan_Precache();\n")

# W_SetCurrentAmmo: the Mega Man gun shows its own Mega Men as the ammo count
w = resub(w, r'(\t+)else\n\t+\{\n\t+self\.currentammo = 0;\n\t+self\.weaponmodel = "";\n\t+self\.weaponframe = 0;\n\t+axeequipped = 0;\n\t+\}\n',
          lambda m: (m.group(1) + "else if ((self.weapon == IT_MEGAMAN))\n" + m.group(1) + "{\n"
                     + m.group(1) + "\tself.currentammo = self.mm_ammo;\n"
                     + m.group(1) + "\tself.weaponmodel = \"progs/v_megaman.md3\";\n"
                     + m.group(1) + "\tself.weaponframe = 0;\n"
                     + m.group(1) + "\taxeequipped = 0;\n" + m.group(1) + "}\n" + m.group(0)))

# W_CheckNoAmmo: it recharges by itself, never switch away because it's empty
w = rep(w, "float() W_CheckNoAmmo =\n{\n\tif ((self.currentammo > 0))\n\t{\n\t\treturn (TRUE);\n\t}\n",
        "float() W_CheckNoAmmo =\n{\n\tif ((self.currentammo > 0))\n\t{\n\t\treturn (TRUE);\n\t}\n"
        "\tif ((self.weapon == IT_MEGAMAN))\n\t{\n\t\treturn (TRUE);\n\t}\n")

# W_Attack
w = rep(w, "\tif (((self.meleeing == 1) || (self.throwing == 1)))\n\t{\n\t\treturn;\n\t}\n\tmakevectors(self.v_angle);\n\tself.show_hostile = (time + 1);\n",
        "\tif (((self.meleeing == 1) || (self.throwing == 1)))\n\t{\n\t\treturn;\n\t}\n\tmakevectors(self.v_angle);\n\tself.show_hostile = (time + 1);\n"
        "\tif ((self.weapon == IT_MEGAMAN))\n\t{\n\t\tMegaMan_Attack();\n\t\treturn;\n\t}\n")

# impulse 9 hands it out too
w = rep(w, "\tself.grenade_ammo = 6;\n\tself.weapon = IT_ROCKET_LAUNCHER;\n",
        "\tself.grenade_ammo = 6;\n\tMegaMan_Give(self);\n\tself.weapon = IT_ROCKET_LAUNCHER;\n")

# weapon cycling: ... laser cannon -> Mega Man -> axe (and back)
w = rep(w, "\t\tam = 0;\n\t\tif ((self.weapon == IT_LASER_CANNON))\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n",
        "\t\tam = 0;\n\t\tif ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n"
        "\t\telse if ((self.weapon == IT_LASER_CANNON))\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n")
w = rep(w, "\t\tam = 0;\n\t\tif ((self.weapon == IT_LASER_CANNON))\n\t\t{\n\t\t\tself.weapon = IT_LIGHTNING;\n",
        "\t\tam = 0;\n\t\tif ((self.weapon == IT_MEGAMAN))\n\t\t{\n\t\t\tself.weapon = IT_LASER_CANNON;\n"
        "\t\t\tif ((self.ammo_cells < 1))\n\t\t\t{\n\t\t\t\tam = 1;\n\t\t\t}\n\t\t}\n"
        "\t\telse if ((self.weapon == IT_LASER_CANNON))\n\t\t{\n\t\t\tself.weapon = IT_LIGHTNING;\n")
w = resub(w, r"(if \(\(self\.weapon == IT_AXE\)\)\n\t+\{\n(\t+))self\.weapon = IT_LASER_CANNON;\n\t+if \(\(self\.ammo_cells < 1\)\)\n\t+\{\n\t+am = 1;\n\t+\}\n",
          lambda m: m.group(1) + "self.weapon = IT_MEGAMAN;\n")

w = rep(w, "void() ImpulseCommands =\n{\n", "void() ImpulseCommands =\n{\n\tif ((self.impulse == MM_IMPULSE))\n\t{\n\t\tMegaMan_Select();\n\t}\n")
w = rep(w, "void() W_WeaponFrame =\n{\n", "void() W_WeaponFrame =\n{\n\tMegaMan_ViewFrame();\n")
assert "MegaMan_BeginThrow" not in w and "\"progs/megaman.md3\"" not in w
wr("weapons.qc", w)

# ---------------------------------------------------------------- player.qc: throw animation that leaves the view model alone
p = rd(D + "player.qc.pre_viewmodel")
anchor = "void() player_rocket6 = [ 112, player_run ]\n{\n\tself.weaponframe = 6;\n};\n"
p = rep(p, anchor, anchor + "\n// Mega Man gun throw: the rocket firing pose; the view model is driven by MegaMan_ViewFrame\n"
        + "".join("void() player_mm%d = [ %d, %s ] {};\n" % (i, 106 + i, "player_mm%d" % (i + 1) if i < 6 else "player_run") for i in range(1, 7)))
wr("player.qc", p)

# ---------------------------------------------------------------- items.qc: stock rocket launcher pickup; backpacks don't hand out the Mega Man gun
it = rd(D + "items.qc.pre_viewmodel")
it = rep(it, "\titem.items = self.weapon;\n", "\titem.items = self.weapon;\n\tif ((item.items == IT_MEGAMAN))\n\t{\n\t\titem.items = 0;\n\t}\n")
wr("items.qc", it)

# ---------------------------------------------------------------- custom_effects.qc: the "weapon position" helper entity draws the held weapon
ce = rd(D + "custom_effects.qc.pre_viewmodel")
block = ("\tif ((self.owner.weapon == IT_MEGAMAN))\n\t{\n\t\tsetmodel(self, \"progs/v_megaman.md3\");\n"
         "\t\tself.origin = '0 0 0';\n\t\tself.angles = '0 0 0';\n\t}\n")
ce = rep(ce, "\tself.owner.weaponmodel = \"\";\n\tself.frame = self.owner.weaponframe;\n",
         block + "\tself.owner.weaponmodel = \"\";\n\tself.frame = self.owner.weaponframe;\n")
a = ce.index("void() Quake3_quad_effect_v_weapon_position_anim =")
tail = "\tself.frame = self.owner.weaponframe;\n\tself.nextthink = time;\n};\n"
b = ce.index(tail, a)
ce = ce[:b] + block + ce[b:]
wr("custom_effects.qc", ce)

# ---------------------------------------------------------------- client.qc (patched in place)
c = rd(D + "client.qc")
if "IT_MEGAMAN" not in c:
    c = rep(c, "\telse if (self.owner.weapon == IT_LASER_CANNON)\n\t\tself.vwep = \"progs/p_laser.md3\";\n",
            "\telse if (self.owner.weapon == IT_LASER_CANNON)\n\t\tself.vwep = \"progs/p_laser.md3\";\n"
            "\telse if (self.owner.weapon == IT_MEGAMAN)\n\t\tself.vwep = \"\";\t// the Mega Man gun has its own little Mega Man (MegaMan_UpdateVwep)\n")
    c = rep(c, "\tDecodeLevelParms();\n", "\tDecodeLevelParms();\n\tMegaMan_Give(self);\n")
    c = rep(c, "if (((((time > self.attack_finished) && (self.currentammo == 0)) && (self.weapon != IT_AXE)) && (self.weapon != IT_CHAINSAW)))",
            "if ((((((time > self.attack_finished) && (self.currentammo == 0)) && (self.weapon != IT_AXE)) && (self.weapon != IT_CHAINSAW)) && (self.weapon != IT_MEGAMAN)))")
    c = resub(c, r"(\n(\t+)rnum = attacker\.weapon;\n)",
              lambda m: m.group(1) + m.group(2) + "if (mm_inflicting)\n" + m.group(2) + "{\n"
                        + m.group(2) + "\trnum = IT_MEGAMAN;\n"
                        + m.group(2) + "\tdeathstring = \" got run over by \";\n"
                        + m.group(2) + "\tdeathstring2 = \"'s Mega Man\\n\";\n" + m.group(2) + "}\n")
    wr("client.qc", c)
else:
    print("client.qc already patched")

# ---------------------------------------------------------------- progs.src + the shared Mega Man sources
ps = rd(D + "progs.src")
if "megaman.qc" not in ps:
    ps = rep(ps, "\ndefs_custom.qc\n", "\ndefs_custom.qc\nmegaman_defs.qc\n")
    ps = rep(ps, "\nweapons.qc\n", "\nweapons.qc\nmegaman.qc\n")
    wr("progs.src", ps)
guard = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"
for n in ("megaman_defs.qc", "megaman.qc"):
    wr(n, guard + rd(T + n))
