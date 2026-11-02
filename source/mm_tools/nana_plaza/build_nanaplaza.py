"""build_nanaplaza.py — End-to-end reproducible build pipeline for Nana Plaza (`maps/nanaplaza.bsp` + `.lit`).
1. Optionally rebuilds WAD2 + DarkPlaces PNG textures (`--textures` or if `out/nanaplaza.wad` is missing).
2. Generates `out/nanaplaza.map` purely from `specs/*.json` via `make_nanaplaza.py`.
3. Compiles BSP2 (`qbsp.exe -bsp2`), PVS (`vis.exe`), and colored radiosity/sunlight (`light.exe -extra`).
4. Verifies 0 leaks and inspects compiler logs, then installs `maps/nanaplaza.bsp` and `maps/nanaplaza.lit`.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "out")
MOD_MAPS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "maps"))
PY = sys.executable
ERICW = r"D:\vibe\quake1opensource\tools\ericw"


def run_step(cmd, cwd, log_path=None):
    if log_path:
        with open(log_path, "w", encoding="utf-8") as lf:
            res = subprocess.run(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, text=True)
        if res.returncode != 0:
            with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                tail = "".join(lf.readlines()[-30:])
            raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{tail}")
    else:
        res = subprocess.run(cmd, cwd=cwd, check=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(MOD_MAPS, exist_ok=True)

    fast = os.environ.get("NANA_FAST", "") == "1" or "--fast" in sys.argv
    rebuild_tex = "--textures" in sys.argv or not os.path.exists(os.path.join(OUT_DIR, "nanaplaza.wad"))

    if rebuild_tex:
        print("[1/5] Building photo-derived textures & WAD2...")
        run_step([PY, os.path.join(HERE, "build_textures.py")], cwd=HERE)
        run_step([PY, os.path.join(HERE, "build_sky.py")], cwd=HERE)
    else:
        print("[1/5] Using existing out/nanaplaza.wad & skybox...")

    print("[2/5] Generating out/nanaplaza.map from specs/*.json...")
    env = dict(os.environ)
    env.pop("NANA_START", None)
    subprocess.run([PY, os.path.join(HERE, "make_nanaplaza.py")], cwd=HERE, env=env, check=True)

    qbsp_log = os.path.join(OUT_DIR, "qbsp.log")
    vis_log = os.path.join(OUT_DIR, "vis.log")
    light_log = os.path.join(OUT_DIR, "light.log")

    print("[3/5] Running qbsp.exe -bsp2...")
    run_step([os.path.join(ERICW, "qbsp.exe"), "-bsp2", "-threads", "4", "nanaplaza.map"], cwd=OUT_DIR, log_path=qbsp_log)
    with open(qbsp_log, "r", encoding="utf-8", errors="replace") as f:
        qtxt = f.read()
    if "leak" in qtxt.lower():
        raise RuntimeError(f"LEAK DETECTED in qbsp.log!\n{qtxt}")
    warns = [ln.strip() for ln in qtxt.splitlines() if "warning" in ln.lower()]
    print(f"      qbsp OK — 0 leaks, {len(warns)} warnings.")
    for w in warns[:15]:
        print(f"      WARN: {w}")

    print(f"[4/5] Running vis.exe ({'-fast' if fast else 'full'})...")
    vis_cmd = [os.path.join(ERICW, "vis.exe"), "-threads", "4"] + (["-fast"] if fast else []) + ["nanaplaza.bsp"]
    run_step(vis_cmd, cwd=OUT_DIR, log_path=vis_log)
    print("      vis OK.")

    print(f"[5/5] Running light.exe ({'fast' if fast else '-extra'})...")
    light_cmd = [os.path.join(ERICW, "light.exe"), "-threads", "4"] + ([] if fast else ["-extra"]) + ["nanaplaza.bsp"]
    run_step(light_cmd, cwd=OUT_DIR, log_path=light_log)
    with open(light_log, "r", encoding="utf-8", errors="replace") as f:
        ltxt = f.read()
    lwarns = [ln.strip() for ln in ltxt.splitlines() if "warning" in ln.lower()]
    print(f"      light OK — {len(lwarns)} warnings.")

    dst_bsp = os.path.join(MOD_MAPS, "nanaplaza.bsp")
    dst_lit = os.path.join(MOD_MAPS, "nanaplaza.lit")
    shutil.copy2(os.path.join(OUT_DIR, "nanaplaza.bsp"), dst_bsp)
    if os.path.exists(os.path.join(OUT_DIR, "nanaplaza.lit")):
        shutil.copy2(os.path.join(OUT_DIR, "nanaplaza.lit"), dst_lit)
    print(f"Installed:\n  {dst_bsp}\n  {dst_lit}")


if __name__ == "__main__":
    main()
