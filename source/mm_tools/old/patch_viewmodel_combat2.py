"""Combat+'s "fully adjustable weapon position" helper entity draws the held weapon itself:
point it at v_megaman.md3 for the rocket launcher slot and drop the user's per-weapon offsets/idle wobble.
python -I patch_viewmodel_combat2.py   (idempotent; run against qc_combat_decomp)"""
import re

fn = r"G:\Quake\Combat\BakersfieldQuake\source\qc_combat_decomp\custom_effects.qc"
c = open(fn, encoding="utf-8", errors="surrogateescape", newline="").read()
if "v_megaman" in c:
    print("custom_effects.qc already patched")
    raise SystemExit

# 1) the main helper: centred or normal rocket launcher model -> Mega Man
pat0 = re.compile(r'([ \t]+)if \(autocvar_centered_weapons\)\n[ \t]+\{\n[ \t]+setmodel\(self, "progs/centered/v_rock2\.mdl"\);\n'
                  r'[ \t]+\}\n[ \t]+else\n[ \t]+\{\n[ \t]+setmodel\(self, "progs/v_rock2\.mdl"\);\n[ \t]+\}\n')
m0 = pat0.search(c)
assert m0, "rock model block not found"
c = c[:m0.start()] + m0.group(1) + 'setmodel(self, "progs/v_megaman.md3");\n' + c[m0.end():]

# 2) after the rocket launcher's position / idle-wobble code, force the model to sit at the view origin
pat = re.compile(r"(idle_weapon_animation\(autocvar_weapon_position_fully_adjustable_rock_x_offset[^\n]*\n[ \t]+\}\n[ \t]+\}\n)([ \t]+)\}\n")
m = pat.search(c)
assert m, "rock idle block not found"
ind = m.group(2)
c = c[:m.end()] + ind + "self.origin = '0 0 0';\n" + ind + "self.angles = '0 0 0';\n" + c[m.end():]

# 3) the quad damage overlay copy of the weapon
pat3 = re.compile(r'(setmodel\(self, )"progs/v_rock2\.mdl"(\);\n[ \t]+self\.origin_x = autocvar_weapon_position_fully_adjustable_rock_x_offset;)')
m3 = pat3.search(c)
assert m3, "quad block not found"
c = c[:m3.start()] + m3.group(1) + '"progs/v_megaman.md3"' + m3.group(2) + c[m3.end():]

open(fn, "w", encoding="utf-8", errors="surrogateescape", newline="").write(c)
print("custom_effects.qc patched")
