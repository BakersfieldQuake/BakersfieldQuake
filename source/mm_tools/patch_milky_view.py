"""Hook the Milky Gun's held model (progs/v_milky.md3 from build_milky_view.py, driven by Milky_ViewFrame in milky.qc) into the
Combat+ source in qc_combat_decomp, and lengthen its fire to the windup (MILKY_WIND: press fire, the fist winds up, she is thrown).
Run after patch_milky_combat.py. Marker-guarded (safe to re-run), keeps *.pre_milkyview backups. Then: python -I build_combat.py
python -I patch_milky_view.py"""
import os
import shutil
import sys

ROOT = "G:\\Quake\\Combat\\BakersfieldQuake\\"
D = ROOT + "source\\qc_combat_decomp\\"


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
    if not os.path.exists(path + ".pre_milkyview"):
        shutil.copy(path, path + ".pre_milkyview")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


# --- custom_effects.qc: the viewmodel entity shows the Milky Gun's card model, and Milky_ViewFrame picks its animation
patch(D + "custom_effects.qc", "Milky_ViewFrame", [
    ("setmodel(self, \"progs/v_nail2.mdl\");", "setmodel(self, \"progs/v_milky.md3\");\t// the Milky Gun (milky.qc)", 2),
    ("setmodel(self, \"progs/centered/v_nail2.mdl\");", "setmodel(self, \"progs/v_milky.md3\");"),
    ("\t\tself.alpha = -1;\t// zoomed in with the sniper rifle (sniper.qc)\n\t}\n",
     "\t\tself.alpha = -1;\t// zoomed in with the sniper rifle (sniper.qc)\n\t}\n\tMilky_ViewFrame (self);\t// which Milky Gun clip, and when the hand is put away (milky.qc)\n"),
])

# --- weapons.qc: the old nailgun's glowing-barrel overlay draws nothing now
patch(D + "weapons.qc", "v_nail2_barrel_cleared", [
    ("setmodel(self, \"progs/centered/v_nail2_barrel.mdl\");", "setmodel(self, string_null);\t// v_nail2_barrel_cleared"),
    ("setmodel(self, \"progs/v_nail2_barrel.mdl\");", "setmodel(self, string_null);"),
    ("setmodel(sngb, \"progs/centered/v_nail2_barrel.mdl\");", "setmodel(sngb, string_null);"),
    ("setmodel(sngb, \"progs/v_nail2_barrel.mdl\");", "setmodel(sngb, string_null);"),
])
