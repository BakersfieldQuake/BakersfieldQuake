"""No smoke behind the thrown proximity grenade (key C). progs/proxbomb.mdl carries Quake's grenade-trail flag, so the
grenade gets Combat+'s empty "monsternull" trail effect instead. (The grenade launcher's JohnWave grenade lost its
trail in jg_splash.qc, JG_GrenadeLaunch.) Marker-guarded, keeps *.pre_nosmoke. Then: python -I build_combat.py
python -I patch_nosmoke_combat.py"""
import os
import shutil
import sys

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"


def patch(path, marker, edits):
    raw = open(path, encoding="utf-8", errors="surrogateescape", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    if marker in s:
        print(path, "already patched")
        return
    for old, new in edits:
        if s.count(old) != 1:
            sys.exit("%s: anchor found %d times: %r" % (path, s.count(old), old[:80]))
        s = s.replace(old, new)
    if not os.path.exists(path + ".pre_nosmoke"):
        shutil.copy(path, path + ".pre_nosmoke")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    print(path, "patched")


patch(D + "weapons.qc", "no barrel smoke", [
    ("\tsetmodel(missile, \"progs/grenade.mdl\");\n\tsetsize(missile, VEC_ORIGIN, VEC_ORIGIN);\n\tSpawnSmoke_Flash(1.3, VEC_ORIGIN, 1, VEC_ORIGIN, 0.7);\n",
     "\tsetmodel(missile, \"progs/grenade.mdl\");\n\tsetsize(missile, VEC_ORIGIN, VEC_ORIGIN);\n\t// no barrel smoke on the grenade launcher (was SpawnSmoke_Flash(1.3, VEC_ORIGIN, 1, VEC_ORIGIN, 0.7))\n"),
])

patch(D + "enforcer.qc", "no smoke trail", [
    ("\tsetmodel(missile, \"progs/proxbomb.mdl\");\n",
     "\tsetmodel(missile, \"progs/proxbomb.mdl\");\n\tmissile.traileffectnum = particleeffectnum(\"monsternull\");\t// no smoke trail\n"),
])
