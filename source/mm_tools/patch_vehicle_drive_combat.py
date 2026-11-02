"""Hook DRIVING the van (mm_tools\\vehicle_drive.qc) into the Combat+ source in qc_combat_decomp:
  - weapons.qc  W_WeaponFrame: Veh_DriveFrame() right after FD_Frame(); a driver does nothing but drive
  - custom_effects.qc  the gun-drawing helper hides the gun while he drives
  - client.qc   ClientObituary: "X was run over by Y's van"; ClientDisconnect: a driver who drops leaves the van parked
  - progs.src   vehicle_drive.qc after vehicles.qc
  - build_combat.py  copies vehicle_drive.qc alongside the other shared sources
Run after patch_vehicles_combat.py. Marker-guarded (safe to re-run), keeps *.pre_vehicle_drive backups.
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
    if not os.path.exists(path + ".pre_vehicle_drive"):
        shutil.copy(path, path + ".pre_vehicle_drive")
    open(path, "w", encoding="utf-8", errors="surrogateescape", newline="").write(
        s.replace("\n", "\r\n") if crlf else s
    )
    print(path, "patched")


patch(D + "progs.src", "vehicle_drive.qc", [
    ("\nvehicles.qc\n", "\nvehicles.qc\nvehicle_drive.qc\n"),
])

patch(D + "weapons.qc", "Veh_DriveFrame", [
    (
        "\tif (FD_Frame())\n\t{\n\t\treturn;\t// flying a Rob Dob head: nothing else happens (floathead.qc)\n\t}\n",
        "\tif (FD_Frame())\n\t{\n\t\treturn;\t// flying a Rob Dob head: nothing else happens (floathead.qc)\n\t}\n"
        "\tif (Veh_DriveFrame())\n\t{\n\t\treturn;\t// driving the van: nothing else happens (vehicle_drive.qc)\n\t}\n",
    ),
])

patch(D + "client.qc", "veh_runover", [
    (
        "\t\t\tif ((targ == attacker))\n\t\t\t{\n\t\t\t\tbprint(targ.netname);\n",
        "\t\t\tif (veh_runover)\n\t\t\t{\n"
        "\t\t\t\tbprint(targ.netname);\n"
        "\t\t\t\tbprint(\" was run over by \");\n"
        "\t\t\t\tbprint(attacker.netname);\n"
        "\t\t\t\tbprint(\"'s van\\n\");\n"
        "\t\t\t\treturn;\n\t\t\t}\n"
        "\t\t\tif ((targ == attacker))\n\t\t\t{\n\t\t\t\tbprint(targ.netname);\n",
    ),
])

# --- client.qc ClientDisconnect: a driver who drops leaves the van parked
patch(D + "client.qc", "Veh_ClientGone", [
    (
        "void() ClientDisconnect =\n{\n\tClientDisconnected();\n",
        "void() ClientDisconnect =\n{\n\tClientDisconnected();\n\tVeh_ClientGone();\t// a driver who drops leaves the van parked (vehicle_drive.qc)\n",
    ),
])

# --- custom_effects.qc: the helper entity that draws the gun hides it while he drives (as it does while flying a Rob Dob head)
patch(D + "custom_effects.qc", "Veh_Driving", [
    (
        "|| FD_Flying(self.owner))",
        "|| FD_Flying(self.owner) || Veh_Driving(self.owner))",
    ),
])

patch(T + "build_combat.py", "vehicle_drive.qc", [
    ("\"vehicles_defs.qc\", \"vehicles.qc\")", "\"vehicles_defs.qc\", \"vehicles.qc\", \"vehicle_drive.qc\")"),
])
