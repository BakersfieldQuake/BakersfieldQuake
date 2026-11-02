"""Hook the laptop gun (mm_tools\\ltgun_defs.qc, ltgun.qc) into the Combat+ source in qc_combat_decomp. It takes over from the
sniper rifle (which had taken over the nailgun): key 4 / IT_NAILGUN keeps its slot, item bit and nail magazine, but shows the
laptop, types while fire is pressed, and sends the guided head. The sniper sources stay in the build, just unhooked.
Marker-guarded (safe to re-run), keeps *.pre_ltgun backups. Then: python -I build_combat.py
Assets: python build_ltgun_assets.py   (needs PIL + numpy, so not -I and not the venv python)
python -I patch_ltgun_combat.py"""
import os
import shutil
import sys

ROOT = "G:\\Quake\\Combat\\BakersfieldQuake\\"
D = ROOT + "source\\qc_combat_decomp\\"
T = ROOT + "source\\mm_tools\\"


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
    if not os.path.exists(path + ".pre_ltgun"):
        shutil.copy(path, path + ".pre_ltgun")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


# --- weapons.qc: precache, the view model, the per-frame work, the fire button
patch(D + "weapons.qc", "LtGun_", [
    ("\tSniper_Precache();\t// the sniper rifle replaces the nailgun (sniper.qc)\n",
     "\tLtGun_Precache();\t// the laptop gun replaces the sniper rifle (ltgun.qc)\n"),
    ("\"progs/v_srifle.mdl\"", "\"progs/ltg_view.md3\"", 2),
    ("\tSniper_PlayerFrame();\t// the rifle's zoom, laser dot and leg shots (sniper.qc)\n",
     "\tLtGun_PlayerFrame();\t// the laptop's held model and the shock (ltgun.qc)\n"),
    ("\tif (Sniper_Frame())\n", "\tif (LtGun_Frame())\n"),
    ("// sniper rifle\n", "// laptop gun\n"),
])

# --- player.qc: the gun a dead player drops
patch(D + "player.qc", "ltg_p", [
    ("progs/p_srifle.md3", "progs/ltg_p.md3"),
])

# --- client.qc: third-person model, obituary, a fresh life
patch(D + "client.qc", "ltg_inflicting", [
    ("progs/p_srifle.md3", "progs/ltg_p.md3"),
    ("if (sn_inflicting)", "if (ltg_inflicting)"),
    ("Sniper_Death();\t// sniper rifle", "LtGun_Death();\t// laptop gun"),
    ("\tSniper_Spawn();\t// steady legs, no zoom (sniper.qc)\n", "\tLtGun_Spawn();\t// not shocked, not typing (ltgun.qc)\n"),
])

# --- items.qc: the pickup
patch(D + "items.qc", "ltg_g", [
    ("precache_model(\"progs/g_srifle.mdl\");\t// sniper rifle", "precache_model(\"progs/ltg_g.md3\");\t// laptop gun"),
    ("setmodel(self, \"progs/g_srifle.mdl\");", "setmodel(self, \"progs/ltg_g.md3\");"),
    ("self.netname = \"Sniper Rifle\";", "self.netname = \"Laptop\";"),
])

# --- custom_effects.qc: the adjustable weapon-position helper draws the laptop (typing or idle model)
patch(D + "custom_effects.qc", "LtGun_VModel", [
    ("setmodel(self, \"progs/v_srifle.mdl\");", "setmodel(self, LtGun_VModel(self.owner));", 3),
])

# --- progs.src: the defs early, the code with the other guns
patch(D + "progs.src", "ltgun.qc", [
    ("\nsniper_defs.qc\n", "\nsniper_defs.qc\nltgun_defs.qc\n"),
    ("\nsniper.qc\n", "\nsniper.qc\nltgun.qc\n"),
])

# --- build_combat.py: copy the laptop sources with the other shared ones
patch(T + "build_combat.py", "ltgun.qc", [
    ("\"sniper_defs.qc\", \"sniper.qc\"", "\"sniper_defs.qc\", \"sniper.qc\", \"ltgun_defs.qc\", \"ltgun.qc\""),
])
