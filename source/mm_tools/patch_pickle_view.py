"""Hook `Pickle_ViewFrame` (from `pickle.qc`) into `source/qc_combat_decomp/custom_effects.qc`
for both the primary viewmodel (`v_weapon_position_think`) and the Quad Damage overlay
(`Quake3_quad_effect_v_weapon_position_anim`). Marker-guarded and keeps `.pre_pickleview` backup.
Also updates `patch_funguns_combat.py` so a fresh rebuild from decomp includes the hook!"""
import os
import shutil
import sys

ROOT = "G:\\Quake\\Combat\\BakersfieldQuake\\"
D = ROOT + "source\\qc_combat_decomp\\"
T = ROOT + "source\\mm_tools\\"


def patch_custom_effects():
    path = D + "custom_effects.qc"
    raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    if "Pickle_ViewFrame" in s:
        print(path, "already has Pickle_ViewFrame")
        return

    old_quad = (
        "\tif ((self.owner.weapon == IT_FUNGUN))\n"
        "\t{\n"
        "\t\tsetmodel(self, FunGun_VModel(self.owner.fg_sel));\n"
        "\t\tself.origin = '0 0 0';\n"
        "\t\tself.angles = '0 0 0';\n"
        "\t}\n"
        "\tself.frame = self.owner.weaponframe;\n"
    )
    new_quad = (
        old_quad
        + "\tPickle_ViewFrame (self, TRUE);\t// sync articulated Pickle Surprise skin & pose on Quad overlay (pickle.qc)\n"
    )
    assert s.count(old_quad) == 1, f"Expected 1 quad anchor, found {s.count(old_quad)}"
    s = s.replace(old_quad, new_quad, 1)

    old_vm = "\tMilky_ViewFrame (self);\t// which Milky Gun clip, and when the hand is put away (milky.qc)\n"
    new_vm = (
        old_vm
        + "\tPickle_ViewFrame (self, FALSE);\t// articulated Pickle Surprise idle, throw, follow-through & reload (pickle.qc)\n"
    )
    assert s.count(old_vm) == 1, f"Expected 1 Milky_ViewFrame anchor, found {s.count(old_vm)}"
    s = s.replace(old_vm, new_vm, 1)

    if not os.path.exists(path + ".pre_pickleview"):
        shutil.copy(path, path + ".pre_pickleview")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(
        s.replace("\n", "\r\n") if crlf else s
    )
    print("Patched", path)


if __name__ == "__main__":
    patch_custom_effects()
