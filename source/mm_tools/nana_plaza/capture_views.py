"""capture_views.py — Safe, single-session in-game DarkPlaces screenshot capturer and side-by-side
photo comparison builder for Nana Plaza (`specs/cameras.json` -> `out/renders/*.png` & `out/comparisons/*.jpg`).

Uses DarkPlaces `prvm_edictset server 1` (`movetype 8`, `origin`, `angles`, `fixangle 1`) inside a deferred
batch script (`zz_np_shots.cfg`) so ALL 18 reference cameras capture in ONE single ~28s engine launch with:
- Exact sub-inch floating eye height (no gravity drop!)
- Exact 0.1-degree pitch and yaw matching every Street View / photo horizon!
- Full shared-workspace safety (`CLAUDE.md`): checks no other `darkplaces.exe` is active, backs up and restores
  `BakersfieldQuake/config.cfg` in `try...finally`, cleans up `zz_np_shots.cfg`, and tracks only its own PID.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from PIL import Image, ImageDraw, ImageFont

from nana_lib import HERE, PLAZA_YAW_DEG, U_M, plaza_to_world

SPEC_CAM = os.path.join(HERE, "specs", "cameras.json")
REF_DIR = os.path.join(HERE, "ref_images")
OUT_DIR = os.path.join(HERE, "out")
RENDER_DIR = os.path.join(OUT_DIR, "renders")
COMP_DIR = os.path.join(OUT_DIR, "comparisons")

MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
COMBAT_DIR = os.path.abspath(os.path.join(MOD_DIR, ".."))
DARKPLACES = os.path.join(COMBAT_DIR, "darkplaces.exe")

CFG_PATH = os.path.join(MOD_DIR, "config.cfg")
CFG_BAK = os.path.join(OUT_DIR, ".nanaplaza_cfg_bak")
SHOT_CFG = os.path.join(MOD_DIR, "zz_np_shots.cfg")

# Quake player view_ofs_z = +22 units above origin.z
VIEW_OFS_U = 22.0


def other_darkplaces_running():
    res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq darkplaces.exe", "/NH"], capture_output=True, text=True)
    return "darkplaces.exe" in res.stdout.lower()


def wait_for_darkplaces_slot(timeout_s=180):
    t0 = time.time()
    while other_darkplaces_running():
        if time.time() - t0 > timeout_s:
            raise RuntimeError("Timed out waiting for another darkplaces.exe session to finish.")
        time.sleep(2.5)


def make_comparison_card(cam, ref_path, shot_path, out_card_path, fnt_hdr, fnt_sub):
    ref_im = Image.open(ref_path).convert("RGB")
    shot_im = Image.open(shot_path).convert("RGB")

    target_h = 540
    rw = int(round(ref_im.width * (target_h / ref_im.height)))
    sw = int(round(shot_im.width * (target_h / shot_im.height)))
    ref_r = ref_im.resize((rw, target_h), Image.Resampling.LANCZOS)
    shot_r = shot_im.resize((sw, target_h), Image.Resampling.LANCZOS)

    hdr_h = 58
    pad = 12
    total_w = rw + sw + pad * 3
    total_h = target_h + hdr_h + pad
    card = Image.new("RGB", (total_w, total_h), (20, 22, 26))
    d = ImageDraw.Draw(card)
    d.text((pad, 8), f"{cam['id']} — {cam['title']}", fill=(255, 232, 140), font=fnt_hdr)
    d.text((pad, 33), f"LEFT: Ground-Truth Photo ({cam['ref']})   |   RIGHT: Quake In-Game Render (1:1 Scale, FOV {cam.get('fov', 90)})", fill=(185, 215, 245), font=fnt_sub)
    card.paste(ref_r, (pad, hdr_h))
    card.paste(shot_r, (pad * 2 + rw, hdr_h))
    d.rectangle([pad - 1, hdr_h - 1, pad + rw, hdr_h + target_h], outline=(90, 95, 105), width=1)
    d.rectangle([pad * 2 + rw - 1, hdr_h - 1, pad * 2 + rw + sw, hdr_h + target_h], outline=(90, 95, 105), width=1)
    card.save(out_card_path, quality=92)
    return card


def main():
    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(COMP_DIR, exist_ok=True)

    with open(SPEC_CAM, "r", encoding="utf-8") as f:
        cams = json.load(f)["cameras"]

    only_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only_filter = set(arg.split("=", 1)[1].split(","))
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only_filter = set(sys.argv[idx + 1].split(","))

    selected = [c for c in cams if (not only_filter or c["id"] in only_filter)]
    if not selected:
        print("No matching cameras selected.")
        return

    mod_bsp = os.path.join(MOD_DIR, "maps", "nanaplaza.bsp")
    if not os.path.exists(mod_bsp):
        raise FileNotFoundError(f"Missing {mod_bsp}; run build_nanaplaza.py first.")

    try:
        fnt_hdr = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
        fnt_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    except OSError:
        fnt_hdr = ImageFont.load_default()
        fnt_sub = fnt_hdr

    # Build deferred camera schedule in zz_np_shots.cfg
    cfg_lines = [
        "sv_gravity 0",
        "r_sky 1",
        "r_useinfinitefarclip 1",
        "loadsky nanaplaza_",
        "r_drawviewmodel 0",
        "viewsize 120",
        "crosshair 0",
        "cl_bob 0",
        "v_idlescale 0",
        "r_hdr_scenebrightness 1.35",
        "v_gamma 1.12",
        "v_contrast 1.14",
        "gl_picmip 0",
        "gl_texture_anisotropy 16",
        "prvm_edictset server 1 movetype 8",
        'prvm_edictset server 1 velocity "0 0 0"',
    ]

    temp_cfgs = [SHOT_CFG]
    t_sec = 1.0
    for idx_c, cam in enumerate(selected):
        cid = cam["id"]
        shot_rel = f"znp_{cid}.png"
        mod_shot = os.path.join(MOD_DIR, shot_rel)
        if os.path.exists(mod_shot):
            os.remove(mod_shot)

        if cam["frame"] == "plaza":
            wx, wy = plaza_to_world(cam["s"], cam["w"])
            yaw = (PLAZA_YAW_DEG + cam["yaw_rel"]) % 360.0
        else:
            wx, wy = cam["x"], cam["y"]
            yaw = cam["yaw"] % 360.0

        xu = wx * U_M
        yu = wy * U_M
        zu = cam["z"] * U_M - VIEW_OFS_U
        pitch = cam.get("pitch", 0.0)
        fov = cam.get("fov", 90)

        sub_name = f"zz_np_c{idx_c:02d}.cfg"
        sub_path = os.path.join(MOD_DIR, sub_name)
        temp_cfgs.append(sub_path)
        exp = cam.get("exposure", 1.35)
        with open(sub_path, "w", encoding="utf-8") as sf:
            sf.write(
                f"r_sky 1\n"
                f"loadsky nanaplaza_\n"
                f"fov {fov}\n"
                f"r_hdr_scenebrightness {exp:.2f}\n"
                f"prvm_edictset server 1 movetype 8\n"
                f'prvm_edictset server 1 velocity "0 0 0"\n'
                f'prvm_edictset server 1 origin "{xu:.1f} {yu:.1f} {zu:.1f}"\n'
                f'prvm_edictset server 1 angles "{pitch:.1f} {yaw:.1f} 0"\n'
                f'prvm_edictset server 1 v_angle "{pitch:.1f} {yaw:.1f} 0"\n'
                f"prvm_edictset server 1 fixangle 1\n"
            )
        cfg_lines.append(f'defer {t_sec:.1f} "exec {sub_name}"')
        cfg_lines.append(f'defer {t_sec + 0.6:.1f} "screenshot {shot_rel}"')
        t_sec += 1.3

    cfg_lines.append(f'defer {t_sec + 0.8:.1f} "quit"')

    wait_for_darkplaces_slot()
    had_cfg = os.path.exists(CFG_PATH)
    if had_cfg:
        shutil.copy2(CFG_PATH, CFG_BAK)

    proc = None
    try:
        with open(SHOT_CFG, "w", encoding="utf-8") as cf:
            cf.write("\n".join(cfg_lines) + "\n")

        cmd = [
            DARKPLACES,
            "-window", "-width", "1280", "-height", "720",
            "-game", "quake15", "-game", "BakersfieldQuake",
            "+vid_mouse", "0", "+joystick", "0", "+m_pitch", "0", "+m_yaw", "0",
            "+r_drawviewmodel", "0", "+viewsize", "120", "+crosshair", "0", "+cl_bob", "0",
            "+deathmatch", "0", "+coop", "0", "+sv_gravity", "0",
            "+map", "nanaplaza",
            "+defer", "5", "exec zz_np_shots.cfg",
        ]
        timeout_total = int(t_sec + 25)
        proc = subprocess.Popen(cmd, cwd=COMBAT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait(timeout=timeout_total)
    except subprocess.TimeoutExpired:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        for tp in temp_cfgs:
            if os.path.exists(tp):
                try:
                    os.remove(tp)
                except OSError:
                    pass
        if had_cfg and os.path.exists(CFG_BAK):
            shutil.copy2(CFG_BAK, CFG_PATH)
            os.remove(CFG_BAK)

    for cam in selected:
        cid = cam["id"]
        mod_shot = os.path.join(MOD_DIR, f"znp_{cid}.png")
        dst_shot = os.path.join(RENDER_DIR, f"{cid}.png")
        if os.path.exists(mod_shot):
            shutil.move(mod_shot, dst_shot)
            card_p = os.path.join(COMP_DIR, f"{cid}_compare.jpg")
            make_comparison_card(cam, os.path.join(REF_DIR, cam["ref"]), dst_shot, card_p, fnt_hdr, fnt_sub)
            print(f"[OK] {cid} -> {dst_shot}")
        else:
            print(f"[WARN] Screenshot missing for {cid}!")

    # Build overview sheets of all existing comparison cards
    cards = []
    for cam in cams:
        cp = os.path.join(COMP_DIR, f"{cam['id']}_compare.jpg")
        if os.path.exists(cp):
            cards.append(Image.open(cp).convert("RGB"))
    for page_i in range(0, len(cards), 6):
        batch = cards[page_i : page_i + 6]
        max_w = max(im.width for im in batch)
        sum_h = sum(im.height + 10 for im in batch) + 10
        sheet = Image.new("RGB", (max_w + 20, sum_h), (12, 14, 18))
        y_cur = 10
        for im in batch:
            sheet.paste(im, (10, y_cur))
            y_cur += im.height + 10
        sp = os.path.join(COMP_DIR, f"overview_page_{(page_i // 6) + 1:02d}.jpg")
        sheet.save(sp, quality=88)
        print(f"Wrote {sp}")


if __name__ == "__main__":
    main()
