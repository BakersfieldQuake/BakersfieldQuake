"""Hook the selectable player bodies (BakersfieldQuake\source\mm_tools\\playerbody.qc) into the Combat+ source in qc_combat_decomp.
Marker-guarded (safe to re-run), keeps *.pre_pb backups.   python -I patch_playerbody_combat.py"""
import shutil
import sys

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"


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
    shutil.copy(path, path + ".pre_pb")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


patch(D + "weapons.qc", "PB_Precache", [
    ("\tFloatHead_Precache();\t// the floating head monster (floathead.qc)\n",
     "\tFloatHead_Precache();\t// the floating head monster (floathead.qc)\n\tPB_Precache();\t// the suit / robe / wife player bodies (playerbody.qc)\n"),
])

patch(D + "client.qc", "PB_", [
    # the model indexes of the bodies, got the same way Combat+ gets modelindex_eyes
    ("\tsetmodel(self, \"progs/eyes.mdl\");\n\tmodelindex_eyes = self.modelindex;\n",
     "\tsetmodel(self, \"progs/eyes.mdl\");\n\tmodelindex_eyes = self.modelindex;\n\tPB_CacheIndexes();\t// suit / robe / wife bodies (playerbody.qc)\n"),
    # after Combat+ has set this frame's model
    ("\t\t\tself.modelindex = modelindex_player;\n\t\t}\n\t\tself.alpha = 1;\n",
     "\t\t\tself.modelindex = modelindex_player;\n\t\t}\n\t\tself.alpha = 1;\n\t\tPB_SetBody();\t// the body the player picked (playerbody.qc)\n"),
])

patch(D + "progs.src", "playerbody", [
    ("floathead.qc\nweapons.qc\n", "floathead.qc\nplayerbody.qc\nweapons.qc\n"),
])

patch(T + "build_combat.py", "playerbody.qc", [
    ("\"jg_splash.qc\", \"floathead.qc\"):", "\"jg_splash.qc\", \"floathead.qc\", \"playerbody.qc\"):"),
])