"""Instantly switches maps/bklan5.bsp + maps/bklan5.lit between any of the pre-baked lighting presets
in source/mm_tools/out/lighting_presets/<preset>/ without waiting for qbsp, vis, or light!

Available presets:
  soft_daylight    — Soft Diffused California Daylight (low contrast, zero blowout — Default)
  sunny_balanced   — Balanced Sunny Bakersfield (mild shadow relief, zero blowout)
  warm_amber       — Warm Late-Afternoon Amber (golden wash + cool sky shadows)
  twilight_neon    — Cool Early-Dusk / Neon & Marquee Pop

Usage:
  python source/mm_tools/apply_bklan5_preset.py <preset>
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
PRESET_DIR = os.path.join(HERE, "out", "lighting_presets")

if len(sys.argv) < 2:
    avail = sorted(d for d in os.listdir(PRESET_DIR) if os.path.isdir(os.path.join(PRESET_DIR, d)))
    print("Usage: python apply_bklan5_preset.py <" + "|".join(avail) + ">")
    sys.exit(1)

preset = sys.argv[1]
src = os.path.join(PRESET_DIR, preset)
assert os.path.isfile(os.path.join(src, "bklan5.lit")), f"Unknown preset '{preset}'"
shutil.copy2(os.path.join(src, "bklan5.bsp"), os.path.join(MOD, "maps", "bklan5.bsp"))
shutil.copy2(os.path.join(src, "bklan5.lit"), os.path.join(MOD, "maps", "bklan5.lit"))
print(f"Installed lighting preset '{preset}' -> maps/bklan5.bsp & maps/bklan5.lit (run `map bklan5` in Quake console!)")
