"""Vanilla (BakersfieldMemes): Mega Man gun as its own weapon (IT_MEGAMAN, impulse 14).
Rebuilds weapons.qc / items.qc / player.qc / progs.src from the pristine git copies (so the
rocket launcher is the stock one again), then hooks megaman.qc in. client.qc keeps its bot
and mm_start code. Safe to re-run.
python -I patch_megaman_vanilla.py"""
import subprocess

REPO = r"G:\Quake\Combat\qc_src"
ROOT = REPO + r"\quakec"


def pristine(n):
    s = subprocess.run(["git", "-C", REPO, "show", "HEAD:quakec/" + n], capture_output=True, check=True).stdout
    return s.decode("utf-8", "surrogateescape").replace("\r\n", "\n")


def rd(n):
    return open(ROOT + "\\" + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")


def wr(n, s):
    open(ROOT + "\\" + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n"))
    print("wrote", n)


def rep(s, old, new):
    assert s.count(old) == 1, "expected once (%d): %r" % (s.count(old), old[:80])
    return s.replace(old, new, 1)


# ---- weapons.qc ----
w = pristine("weapons.qc")
w = rep(w, "void() W_Precache =\n{\n", "void() W_Precache =\n{\n\tMegaMan_Precache ();\t// the Mega Man gun\n")
w = rep(w, "\telse\n\t{\n\t\tself.currentammo = 0;\n\t\tself.weaponmodel = string_null;\n\t}\n};",
        "\telse if (self.weapon == IT_MEGAMAN)\n\t{\n\t\tself.currentammo = self.mm_ammo;\n\t\tself.weaponmodel = \"progs/v_megaman.md3\";\n\t}\n"
        "\telse\n\t{\n\t\tself.currentammo = 0;\n\t\tself.weaponmodel = string_null;\n\t}\n};")
w = rep(w, "\tif (self.currentammo)\n\t\treturn FALSE;\n",
        "\tif (self.currentammo)\n\t\treturn FALSE;\n\n\tif (self.weapon == IT_MEGAMAN)\n\t\treturn FALSE;\t// recharges by itself\n")
w = rep(w, "\tif ( W_HasNoAmmo() ) {\n",
        "\tif (self.weapon == IT_MEGAMAN)\n\t{\n\t\tmakevectors (self.v_angle);\n\t\tself.show_hostile = time + 1;\n"
        "\t\tself.fired_weapon = 1;\n\t\tMegaMan_Attack ();\n\t\treturn;\n\t}\n\n\tif ( W_HasNoAmmo() ) {\n")
w = rep(w, "\t\tfl = IT_LIGHTNING;\n\t\tif (self.ammo_cells < 1)\n\t\t\tam = 1;\n\t}\n",
        "\t\tfl = IT_LIGHTNING;\n\t\tif (self.ammo_cells < 1)\n\t\t\tam = 1;\n\t}\n\telse if (self.impulse == MM_IMPULSE)\n\t{\n\t\tfl = IT_MEGAMAN;\n\t}\n")
w = rep(w, "\tself.weapon = IT_ROCKET_LAUNCHER;\n\tself.impulse = 0;\n\tW_SetCurrentAmmo ();\n};",
        "\tMegaMan_Give (self);\n\tself.weapon = IT_ROCKET_LAUNCHER;\n\tself.impulse = 0;\n\tW_SetCurrentAmmo ();\n};")
# cycling: ... lightning -> Mega Man -> axe (and back)
w = rep(w, "\t\tif (self.weapon == IT_LIGHTNING)\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n",
        "\t\tif (self.weapon == IT_LIGHTNING)\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n\t\telse if (self.weapon == IT_MEGAMAN)\n\t\t{\n\t\t\tself.weapon = IT_AXE;\n\t\t}\n")
w = rep(w, "\t\telse if (self.weapon == IT_AXE)\n\t\t{\n\t\t\tself.weapon = IT_LIGHTNING;\n",
        "\t\telse if (self.weapon == IT_AXE)\n\t\t{\n\t\t\tself.weapon = IT_MEGAMAN;\n\t\t}\n\n\t\telse if (self.weapon == IT_MEGAMAN)\n\t\t{\n\t\t\tself.weapon = IT_LIGHTNING;\n")
w = rep(w, "\tif (self.impulse == 255)\n\t\tQuadCheat ();\n",
        "\tif (self.impulse == 255)\n\t\tQuadCheat ();\n\tif (self.impulse == MM_IMPULSE)\n\t\tW_ChangeWeapon ();\n")
w = rep(w, "void() W_WeaponFrame =\n{\n", "void() W_WeaponFrame =\n{\n\tMegaMan_ViewFrame ();\n\n")
wr("weapons.qc", w)

# ---- items.qc: stock rocket launcher pickup; a dead player's backpack doesn't hand out the Mega Man gun ----
it = pristine("items.qc")
it = rep(it, "\titem.items = self.weapon;\n",
         "\titem.items = self.weapon;\n\tif (item.items == IT_EXTRA_WEAPON)\n\t\titem.items = 0;\t// everyone already has the Mega Man gun\n")
wr("items.qc", it)

# ---- player.qc: throw animation that leaves the view model alone ----
p = pristine("player.qc")
anchor = "void() player_rocket6   =[$rockatt6, player_run  ] {self.weaponframe=6;};\n"
p = rep(p, anchor, anchor + "\n// Mega Man gun throw: the rocket firing pose, the view model is driven by MegaMan_ViewFrame\n"
        + "".join("void() player_mm%d =[$rockatt%d, %s] {};\n" % (i, i, "player_mm%d" % (i + 1) if i < 6 else "player_run") for i in range(1, 7)))
wr("player.qc", p)

# ---- progs.src ----
ps = pristine("progs.src")
ps = rep(ps, "items.qc\n", "items.qc\nmegaman_defs.qc\t\t// the Mega Man gun (shared with Combat+, see mm_tools)\nmegaman.qc\n")
ps = ps.rstrip("\n") + "\n\nmegaman_bots.qc\n"
wr("progs.src", ps)

# ---- the Mega Man gun itself: shared sources from mm_tools ----
for n in ("megaman_defs.qc", "megaman.qc"):
    wr(n, open(r"G:\Quake\Combat\BakersfieldQuake\source\mm_tools" + "\\" + n, encoding="utf-8").read())

# ---- client.qc: everyone gets the gun; mm_start hands you 99 and selects it ----
c = rd("client.qc")
if "MegaMan_Give (self);" not in c:
    old = ("\t// +set mm_start 1 : spawn holding the Mega Man gun with 99 shots\n\tif (cvar (\"mm_start\") && clienttype (self) == CLIENTTYPE_REAL)\n\t{\n"
           "\t\tself.items = self.items | IT_ROCKET_LAUNCHER;\n\t\tif (self.ammo_rockets < 99)\n\t\t\tself.ammo_rockets = 99;\n\t\tself.weapon = IT_ROCKET_LAUNCHER;\n\t}\n")
    new = ("\tMegaMan_Give (self);\n\n\t// +set mm_start 1 : spawn holding the Mega Man gun with 99 Mega Men\n\tif (cvar (\"mm_start\") && clienttype (self) == CLIENTTYPE_REAL)\n\t{\n"
           "\t\tself.mm_ammo = 99;\n\t\tself.weapon = IT_MEGAMAN;\n\t}\n")
    c = rep(c, old, new)
    wr("client.qc", c)
else:
    print("client.qc already patched")
c = rd("client.qc")
if "mm_inflicting" not in c:
    c = rep(c, "\t\t\t\trnum = attacker.weapon;\n",
            "\t\t\t\trnum = attacker.weapon;\n\n\t\t\t\tif (mm_inflicting)\n\t\t\t\t{\n"
            "\t\t\t\t\tbprint (targ.netname, \" got run over by \", attacker.netname, \"'s Mega Man\\n\");\n"
            "\t\t\t\t\treturn;\n\t\t\t\t}\n")
    wr("client.qc", c)
