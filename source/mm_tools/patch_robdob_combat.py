"""Game-code changes for the Rob Dob / feedback round, applied to the Combat+ source in qc_combat_decomp.
Marker-guarded (safe to re-run), keeps *.pre_rd backups.   python -I patch_robdob_combat.py
  client.qc      CheckWaterJump: the decompiled version traced the same line twice, so the water jump (climbing out of water
                 onto a ledge) could never trigger. Back to Quake's: waist-high solid, open at eye level, yaw only.
  defs_custom.qc the axe hits harder (player_axe 20 -> 50)
  weapons.qc     W_WeaponFrame: while a Rob Dob head is out the player does nothing else (floathead.qc FD_Frame)"""
import shutil
import sys

D = "G:/Quake/Combat/BakersfieldQuake/source/qc_combat_decomp/"


def patch(path, marker, edits):
    raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    if marker in s:
        print(path, "already patched")
        return
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit("%s: anchor found %d times, expected 1: %r" % (path, n, old[:80]))
        s = s.replace(old, new)
    shutil.copy(path, path + ".pre_rd")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


patch(D + "client.qc", "// water jump (rd)", [
    ("\tmakevectors(self.angles);\n\tstart = self.origin;\n\tnormalize(v_forward);\n\tend = start + (v_forward * 24);\n\ttraceline(start, end, TRUE, self);\n\tif ((trace_fraction < 1))\n\t{\n\t\tend = start + (v_forward * 24);\n\t\tself.movedir = (trace_plane_normal * -50);\n\t\ttraceline(start, end, TRUE, self);\n",
     "\t// water jump (rd): Quake's own test, which the decompile had flattened (both traces were the same line, so it never fired)\n"
     "\tmakevectors('0 1 0' * self.angles_y);\n\tstart = self.origin;\n\tstart_z = (start_z + 8);\n\tend = start + (v_forward * 24);\n\ttraceline(start, end, TRUE, self);\n\tif ((trace_fraction < 1))\n\t{\n"
     "\t\tstart_z = ((start_z + self.maxs_z) - 8);\n\t\tend = start + (v_forward * 24);\n\t\tself.movedir = (trace_plane_normal * -50);\n\t\ttraceline(start, end, TRUE, self);\n"),
])

patch(D + "defs_custom.qc", "autocvar_player_axe    = 50", [
    ("float autocvar_player_axe    = 20;", "float autocvar_player_axe    = 50;"),
])

patch(D + "weapons.qc", "FD_Frame", [
    ("\tFunGun_ViewFrame();\n\tif (((deathmatch || coop) && (mapstart == 0)))\n",
     "\tFunGun_ViewFrame();\n\tif (FD_Frame())\n\t{\n\t\treturn;\t// flying a Rob Dob head: nothing else happens (floathead.qc)\n\t}\n\tif (((deathmatch || coop) && (mapstart == 0)))\n"),
])
