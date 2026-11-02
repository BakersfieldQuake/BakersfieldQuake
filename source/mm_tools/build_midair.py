"""build_midair.py — Full end-to-end build pipeline for `maps/midair.bsp` + `maps/midair.lit`.

Steps:
1. Generates 6-face 1024px nighttime starry/moonlit cubemap (`gfx/env/midair_*.png` + `.tga`).
2. Generates high-res nocturnal textures + `_glow.png` maps (`textures/ma_*.png`) & `out/maps/midair.wad`.
3. Generates `out/maps/midair.map` via `make_midair.py`.
4. Compiles BSP2 (`qbsp.exe -bsp2`), PVS (`vis.exe`), and colored radiosity/moonlight (`light.exe -extra4`).
5. Verifies 0 leaks and installs `maps/midair.bsp` and `maps/midair.lit`.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "out", "maps")
MOD_MAPS = os.path.abspath(os.path.join(HERE, "..", "..", "maps"))
PY = sys.executable
ERICW = r"D:\vibe\quake1opensource\tools\ericw"


def run_logged(cmd, cwd, log_path):
    with open(log_path, "w", encoding="utf-8") as lf:
        res = subprocess.run(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, text=True)
    with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
        txt = lf.read()
    if res.returncode != 0:
        tail = "\n".join(txt.splitlines()[-35:])
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{tail}")
    return txt


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(MOD_MAPS, exist_ok=True)

    skip_assets = "--fast-map" in sys.argv
    fast_light = "--fast" in sys.argv

    if not skip_assets:
        print("[1/5] Building nighttime skybox (gfx/env/midair_*)...")
        subprocess.run([PY, os.path.join(HERE, "build_midair_sky.py")], cwd=HERE, check=True)

        print("[2/5] Building HD textures, _glow maps, and midair.wad...")
        subprocess.run([PY, os.path.join(HERE, "build_midair_textures.py")], cwd=HERE, check=True)

    print("[3/5] Generating out/maps/midair.map...")
    env = dict(os.environ)
    env.pop("MIDAIR_START", None)
    subprocess.run([PY, os.path.join(HERE, "make_midair.py"), os.path.join(OUT_DIR, "midair.map")], cwd=HERE, env=env, check=True)

    print("[4/5] Compiling BSP2 & VIS...")
    qbsp_txt = run_logged(
        [os.path.join(ERICW, "qbsp.exe"), "-bsp2", "-threads", "4", "midair.map"],
        cwd=OUT_DIR,
        log_path=os.path.join(OUT_DIR, "midair-qbsp.log"),
    )
    if "leak" in qbsp_txt.lower():
        raise RuntimeError(f"LEAK DETECTED in midair-qbsp.log!\n{qbsp_txt}")
    qwarns = [ln.strip() for ln in qbsp_txt.splitlines() if "warning" in ln.lower()]
    print(f"      qbsp OK — 0 leaks, {len(qwarns)} warnings.")
    for w in qwarns[:15]:
        print(f"      WARN: {w}")

    vis_cmd = [os.path.join(ERICW, "vis.exe"), "-threads", "4"] + (["-fast"] if fast_light else []) + ["midair.bsp"]
    run_logged(vis_cmd, cwd=OUT_DIR, log_path=os.path.join(OUT_DIR, "midair-vis.log"))
    print("      vis OK.")

    print(f"[5/5] Running light.exe ({'fast' if fast_light else '-extra4'})...")
    light_cmd = [os.path.join(ERICW, "light.exe"), "-threads", "4"] + ([] if fast_light else ["-extra4"]) + ["midair.bsp"]
    ltxt = run_logged(light_cmd, cwd=OUT_DIR, log_path=os.path.join(OUT_DIR, "midair-light.log"))
    lwarns = [ln.strip() for ln in ltxt.splitlines() if "warning" in ln.lower()]
    print(f"      light OK — {len(lwarns)} warnings.")
    for w in lwarns[:10]:
        print(f"      WARN: {w}")

    dst_bsp = os.path.join(MOD_MAPS, "midair.bsp")
    dst_lit = os.path.join(MOD_MAPS, "midair.lit")
    shutil.copy2(os.path.join(OUT_DIR, "midair.bsp"), dst_bsp)
    if os.path.exists(os.path.join(OUT_DIR, "midair.lit")):
        shutil.copy2(os.path.join(OUT_DIR, "midair.lit"), dst_lit)
    print(f"Installed:\n  {dst_bsp}\n  {dst_lit}")


if __name__ == "__main__":
    main()
