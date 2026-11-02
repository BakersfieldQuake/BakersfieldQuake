"""Hook the 4 shootable/explodable 3D vehicles (mm_tools\\vehicles_defs.qc, vehicles.qc) into
the Combat+ source in qc_combat_decomp:
  - precache models, sounds, and effectinfo particle IDs in W_Precache (weapons.qc)
  - emit metallic bullet sparks instead of flesh blood/sounds when shooting vehicles (weapons.qc)
  - spawn/test impulses 81..85 in ImpulseCommands (weapons.qc)
  - custom exploding-vehicle kill & self-kill obituaries in ClientObituary (client.qc)
  - add vehicles_defs.qc & vehicles.qc to progs.src and build_combat.py
Marker-guarded (safe to re-run), keeps *.pre_vehicles backups.
"""
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
            sys.exit("%s: anchor found %d times, expected %d: %r" % (path, n, want, old[:90]))
        s = s.replace(old, new)
    if not os.path.exists(path + ".pre_vehicles"):
        shutil.copy(path, path + ".pre_vehicles")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(
        s.replace("\n", "\r\n") if crlf else s
    )
    print(path, "patched")


# --- progs.src: defs early, implementation with the custom modules
patch(D + "progs.src", "vehicles.qc", [
    ("\nmilky_defs.qc\n", "\nmilky_defs.qc\nvehicles_defs.qc\n"),
    ("\nmilky.qc\n", "\nmilky.qc\nvehicles.qc\n"),
])

# --- weapons.qc: precache, metallic bullet impacts, impulses 81..85
patch(D + "weapons.qc", "Vehicles_Precache", [
    (
        "\tMilky_Precache();\t// the Milky Gun replaces the super nailgun (milky.qc)\n",
        "\tMilky_Precache();\t// the Milky Gun replaces the super nailgun (milky.qc)\n"
        "\tVehicles_Precache();\t// 4 shootable/explodable 3D vehicles (vehicles.qc)\n",
    ),
    (
        "void(vector org, vector vel, float damage) SpawnBlood =\n{\n",
        "void(vector org, vector vel, float damage) SpawnBlood =\n{\n"
        "\tif (trace_ent.veh_kind)\n\t{\n\t\tsendParticle(\"TE_GUNSHOT\", org, VEC_ORIGIN, 1);\n\t\treturn;\n\t}\n",
    ),
    (
        "\torg = trace_endpos - (dir * 4);\n\tif (trace_ent.takedamage)\n\t{\n",
        "\torg = trace_endpos - (dir * 4);\n\tif (trace_ent.takedamage)\n\t{\n"
        "\t\tif (trace_ent.veh_kind)\n\t\t{\n"
        "\t\t\tsendParticle(\"TE_GUNSHOT\", org, VEC_ORIGIN, 1);\n"
        "\t\t\tAddMultiDamage(trace_ent, damage);\n\t\t\treturn;\n\t\t}\n",
    ),
    (
        "void() ImpulseCommands =\n{\n",
        "void() ImpulseCommands =\n{\n\tVehicles_Impulse();\n",
    ),
])

# --- client.qc: exploding vehicle obituaries
patch(D + "client.qc", "veh_inflicting", [
    (
        "\t\t\t\tif (sg_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint(\" was mown down by their own sentry gun\\n\");\n\t\t\t\t\treturn;\n\t\t\t\t}\n",
        "\t\t\t\tif (sg_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint(\" was mown down by their own sentry gun\\n\");\n\t\t\t\t\treturn;\n\t\t\t\t}\n"
        "\t\t\t\tif (veh_inflicting)\n\t\t\t\t{\n\t\t\t\t\tbprint(\" stood too close to a burning vehicle\\n\");\n\t\t\t\t\treturn;\n\t\t\t\t}\n",
    ),
    (
        "\t\t\t\t\tif (sg_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SENTRY;\n\t\t\t\t\t\tdeathstring = \" is mown down by \";\n\t\t\t\t\t\tdeathstring2 = \"'s sentry gun\\n\";\n\t\t\t\t\t}\n",
        "\t\t\t\t\tif (sg_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = IT_SENTRY;\n\t\t\t\t\t\tdeathstring = \" is mown down by \";\n\t\t\t\t\t\tdeathstring2 = \"'s sentry gun\\n\";\n\t\t\t\t\t}\n"
        "\t\t\t\t\tif (veh_inflicting)\n\t\t\t\t\t{\n\t\t\t\t\t\trnum = 999999;\n\t\t\t\t\t\tdeathstring = \" was blown sky-high by \";\n\t\t\t\t\t\tdeathstring2 = \"'s exploding vehicle\\n\";\n\t\t\t\t\t}\n",
    ),
    (
        "\t\t\tbprint(targ.netname);\n\t\t\tif ((attacker.flags & FL_MONSTER))\n",
        "\t\t\tbprint(targ.netname);\n\t\t\tif (veh_inflicting)\n\t\t\t{\n\t\t\t\tbprint(\" was blown sky-high by an exploding vehicle\\n\");\n\t\t\t\treturn;\n\t\t\t}\n\t\t\tif ((attacker.flags & FL_MONSTER))\n",
    ),
])

# --- build_combat.py: copy vehicles_defs.qc and vehicles.qc alongside the other shared sources
patch(T + "build_combat.py", "vehicles.qc", [
    ("\"milky_defs.qc\", \"milky.qc\")", "\"milky_defs.qc\", \"milky.qc\", \"vehicles_defs.qc\", \"vehicles.qc\")"),
])
