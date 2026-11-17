"""Master Pickle Surprise Overhaul Builder (`source/mm_tools/build_pickle_diva_overhaul.py`).

Combines:
  1. `pickle_violent_rig.py` -> First-person `progs/v_pickle.md3` + `0..119` `.skin` files + `progs/pvm_000..119.png`
     + `scripts/picklevm.shader`:
       - Skins `0..71`  (72 frames): 24fps optical-flow smoothed idle, decontaminated rim, uncropped turquoise crown dome,
         and seamless extended bronze vambrace cuff.
       - Skins `72..87` (16 frames): Brutal choke-crush throat squeeze + terrified bug-eyed pink-tongue scream + high
         cock-back windup -> blistering cross-screen forward whip w/ 9-tap continuous Gaussian shutter motion blur &
         triple kinetic air-rip shockwave arcs (`Pk_Launch()` fires right as the claw snaps open at skin `88`!).
       - Skins `88..106` (19 frames): High-visibility splayed open-claw mid-screen recoil shudder + follow-through slash
         down off bottom-left.
       - Skins `107..119` (13 frames): Aggressive belt-snatch reload with elastic cheek-squish catch settle!
  2. `pickle_diva_rig.py` -> World `progs/pickle.md3` (36-frame base-planted 3D deforming `9x17` inflatable ribbon-grid
     mesh — frames `0..23` S-curve Wacky-Waving Diva Dance, frames `24..35` Pre-Blast Over-Inflation Balloon Swell &
     Violent Shudder, ZERO collapsed cards!) + `progs/pickle.md3_0..63.skin` + `progs/pkv_s{0..3}_v{00..15}.png` covering
     all 4 full-16-angle expressive pose sets (`Sing`, `Cheeky Pucker Wink`, `Bug-Eyes + Real Pink Tongue Out`, and
     `Full 360° Giant Pre-Blast Scream` across all 16 angles!).
  3. `progs/pickle_throw.md3` + `0..7` `.skin` files (`progs/pthr_00..07.png`): Clean decontaminated tumbling throw
     sprite with genuine bug-eyed pink-tongue scream frames.
  4. `progs/pickle_bomb.md3` & `progs/pickle_gib.md3` + seamless 360-degree cylindrical turquoise gold-studded unwrap
     with **8 live expressive animated faces** (`progs/pickle_face_00..07.png`: Sing, Cheeky Pucker, Bug-Eyes + Pink
     Tongue Out, Wide Gasp) + `progs/pickle_skin.png`.
  5. Studio-sRGB showcase assets in `source/mm_tools/out/pickle_overhaul/` (including the 61-frame 4-clip animated 3D
     watertight hull `pickle3d_anim.npz` + `pickle3d_srgb.png`) for `pickle_surprise_animations.html` and
     `custom_models_and_animations.html`!
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib
import pickle_violent_rig as ptr
import pickle_diva_rig as pwr

MOD = r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
OUT_DIR = os.path.join(HERE, "out", "pickle_overhaul")

VM_TEX_W = 416
VM_TEX_H = int(round(VM_TEX_W * ptr.STAGE_H / float(ptr.STAGE_W)))  # 416 x 455

PVM_IDLE_SKIN = 0
PVM_IDLE_COUNT = 72
PVM_WIND_SKIN = 72
PVM_PRE_COUNT = 16       # 72..87: choke-squeeze windup + cross-screen whip to release
PVM_POST_SKIN = 88
PVM_POST_COUNT = 19      # 88..106: open-claw mid-screen recoil shudder + downward slash off screen
PVM_RELOAD_SKIN = 107
PVM_RELOAD_COUNT = 13    # 107..119: aggressive belt-snatch reload + squish settle
PVM_TOTAL_SKINS = PVM_IDLE_COUNT + PVM_PRE_COUNT + PVM_POST_COUNT + PVM_RELOAD_COUNT  # 120


def downsample_premul_rgba(rgba: np.ndarray, out_wh: tuple[int, int]) -> np.ndarray:
    """Premultiplied Lanczos downsample so alpha edges stay razor-clean with zero dark/bright halos."""
    pm = ptr.premul_from_rgba(rgba)
    ds_pm = cv2.resize(pm, out_wh, interpolation=cv2.INTER_AREA)
    return ptr.rgba_from_premul(ds_pm)


def write_card_md3(
    path: str,
    model_name: str,
    surf_name: str,
    default_shader: str,
    dx: float,
    y_left: float,
    y_right: float,
    z_bot: float,
    z_top: float,
    double_sided: bool = False,
) -> None:
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    if double_sided:
        tris += [(0, 2, 1), (0, 3, 2)]
    card = [
        (dx, y_left, z_bot),
        (dx, y_left, z_top),
        (dx, y_right, z_top),
        (dx, y_right, z_bot),
    ]
    surf = dict(
        name=surf_name,
        shader=default_shader,
        tris=tris,
        st=st,
        frames=[(card, [(-1.0, 0.0, 0.0)] * 4)],
    )
    md3lib.write(path, dict(name=model_name, surfaces=[surf], nframes=1))


def write_skin_files(md3_basename: str, surf_name: str, shaders: list[str]) -> None:
    for old in glob.glob(os.path.join(PROGS, f"{md3_basename}_*.skin")):
        os.remove(old)
    for k, sh in enumerate(shaders):
        skin_path = os.path.join(PROGS, f"{md3_basename}_{k}.skin")
        with open(skin_path, "wb") as f:
            f.write(f"{surf_name},{sh}\n".encode("ascii"))


def build_viewmodel_overhaul(srgb_vpk: list[np.ndarray], srgb_pk0: np.ndarray) -> ptr.PickleViolentThrowRig:
    print("[1/5] Building VIOLENT OVERHAND WHIP-THROW viewmodel (`progs/v_pickle.md3` + 120 skins)...")
    rig = ptr.PickleViolentThrowRig(srgb_vpk, srgb_pk0)
    idle_72 = rig.render_smooth_idle_sequence(PVM_IDLE_COUNT)
    throw_48 = rig.render_violent_throw_sequence(48)
    all_120 = idle_72 + throw_48
    assert len(all_120) == PVM_TOTAL_SKINS

    for old in glob.glob(os.path.join(PROGS, "pvm_*.png")):
        os.remove(old)
    os.makedirs(os.path.join(OUT_DIR, "v_pickle"), exist_ok=True)

    shader_names: list[str] = []
    for idx, frame_srgb in enumerate(all_120):
        ds_srgb = downsample_premul_rgba(frame_srgb, (VM_TEX_W, VM_TEX_H))
        # Save studio-sRGB frame for standalone HTML violent-throw simulator!
        Image.fromarray(ds_srgb, "RGBA").save(
            os.path.join(OUT_DIR, "v_pickle", f"pvm_srgb_{idx:03d}.png"), optimize=True
        )
        # Tone for DarkPlaces rgbGen lightingDiffuse + HDR 1.25..1.45
        toned = ptr.tone_for_quake_hdr(ds_srgb, dim=0.87, contrast=1.04)
        tex_name = f"pvm_{idx:03d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tex_name}.png"), optimize=False)
        shader_names.append(f"progs/{tex_name}")

    u_per_px = 24.0 / 607.0
    y_right = -28.5
    y_left = y_right + ptr.STAGE_W * u_per_px
    z_bot = -19.5
    z_top = z_bot + ptr.STAGE_H * u_per_px

    # Single-sided card with `cull none` + `blendfunc blend` so semi-transparent motion blur NEVER double-blends!
    write_card_md3(
        os.path.join(PROGS, "v_pickle.md3"),
        "v_pickle",
        "card",
        shader_names[0],
        dx=14.0,
        y_left=y_left,
        y_right=y_right,
        z_bot=z_bot,
        z_top=z_top,
        double_sided=False,
    )
    write_skin_files("v_pickle.md3", "card", shader_names)

    sh_lines = ["// written by source/mm_tools/build_pickle_diva_overhaul.py\n"]
    for sh in shader_names:
        sh_lines.append(
            f"{sh}\n{{\n\tcull none\n\t{{\n\t\tclampmap {sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    with open(os.path.join(SCRIPTS, "picklevm.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(sh_lines))

    return rig


def build_world_diva_and_throw_sprite(
    srgb_views: list[np.ndarray], rig_t: ptr.PickleViolentThrowRig
) -> list[list[np.ndarray]]:
    print("[2/5] Building 4x16 (64-skin) 360-degree expressive Diva poses + 36-frame deforming `progs/pickle.md3`...")
    pose_sets = pwr.build_four_16view_pose_sets(srgb_views, rig_t)
    assert len(pose_sets) == 4 and all(len(s) == 16 for s in pose_sets)

    for old in glob.glob(os.path.join(PROGS, "pkv_s*_v*.png")):
        os.remove(old)
    os.makedirs(os.path.join(OUT_DIR, "diva_views"), exist_ok=True)

    balloon_shaders: list[str] = []
    for s_idx, pset in enumerate(pose_sets):
        for v_idx, frame_srgb in enumerate(pset):
            Image.fromarray(frame_srgb, "RGBA").save(
                os.path.join(OUT_DIR, "diva_views", f"diva_s{s_idx}_v{v_idx:02d}.png"), optimize=True
            )
            # Tone to match Quake world overbright (`DIM=0.36, Contrast=1.12`) with crisp alpha
            toned = ptr.tone_for_quake_hdr(frame_srgb, dim=0.36, contrast=1.12)
            tname = f"pkv_s{s_idx}_v{v_idx:02d}"
            Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
            balloon_shaders.append(f"progs/{tname}")

    # Write 36-frame base-planted 3D deforming `9x17` ribbon-grid MD3 (`progs/pickle.md3`) + 64 `.skin` files!
    md3_dict = pwr.build_deforming_balloon_md3_dict(half=10.0)
    md3_dict["surfaces"][0]["shader"] = balloon_shaders[0]
    md3lib.write(os.path.join(PROGS, "pickle.md3"), md3_dict)
    write_skin_files("pickle.md3", "card", balloon_shaders)

    # Also save deforming ribbon-grid MD3 to OUT_DIR for HTML showcase inspection
    md3lib.write(os.path.join(OUT_DIR, "pickle_deforming.md3"), md3_dict)

    print("[3/5] Building clean decontaminated tumbling throw sprite (`progs/pickle_throw.md3` + 8 skins)...")
    # Use genuine bug-eyed pink-tongue scream (`pose_sets[2]`) & giant scream (`pose_sets[3]`) across 360°!
    throw_srgb_sources = [
        pose_sets[2][0],   # 0: terrified bug-eyes + pink tongue front (matches hand release!)
        pose_sets[2][2],   # 1: 45-deg pink tongue
        pose_sets[2][4],   # 2: profile sideways pink tongue!
        pose_sets[0][6],   # 3: 3/4 back
        pose_sets[0][8],   # 4: back
        pose_sets[0][10],  # 5: 3/4 back right
        pose_sets[2][12],  # 6: profile right sideways pink tongue!
        pose_sets[3][15],  # 7: giant scream 3/4 front!
    ]
    for old in glob.glob(os.path.join(PROGS, "pthr_*.png")):
        os.remove(old)
    os.makedirs(os.path.join(OUT_DIR, "throw_sprite"), exist_ok=True)

    throw_shaders: list[str] = []
    for k, src_srgb in enumerate(throw_srgb_sources):
        ds_srgb = downsample_premul_rgba(src_srgb, (256, 256))
        Image.fromarray(ds_srgb, "RGBA").save(
            os.path.join(OUT_DIR, "throw_sprite", f"pthr_srgb_{k:02d}.png"), optimize=True
        )
        toned = ptr.tone_for_quake_hdr(ds_srgb, dim=0.44, contrast=1.10)
        tname = f"pthr_{k:02d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
        throw_shaders.append(f"progs/{tname}")

    write_card_md3(
        os.path.join(PROGS, "pickle_throw.md3"),
        "pickle_throw",
        "card",
        throw_shaders[0],
        dx=0.0,
        y_left=8.0,
        y_right=-8.0,
        z_bot=-8.0,
        z_top=8.0,
        double_sided=True,
    )
    write_skin_files("pickle_throw.md3", "card", throw_shaders)
    return pose_sets


def build_3d_totem_and_hull_assets(srgb_views: list[np.ndarray], pose_sets: list[list[np.ndarray]]) -> None:
    print("[4/5] Building 360-unwrapped 8-expression `pickle_bomb.md3` / `pickle_gib.md3` & 4-clip 3D `pickle3d`...")
    TEX_W, TEX_H = 512, 512

    def extract_normalized_rows(im_rgba: np.ndarray, y0: int = 22, y1: int = 488) -> np.ndarray:
        out = np.zeros((TEX_H, 128, 3), dtype=np.float32)
        rgb = im_rgba[..., :3].astype(np.float32)
        a = im_rgba[..., 3]
        valid = a > 160
        fallback = np.median(rgb[valid], axis=0) if np.any(valid) else np.array([36.0, 148.0, 168.0], dtype=np.float32)
        last_row = np.tile(fallback, (128, 1))
        for r in range(TEX_H):
            yy = int(round(y0 + (y1 - y0) * (r / float(TEX_H - 1))))
            yy = max(0, min(im_rgba.shape[0] - 1, yy))
            xs = np.where(a[yy] > 140)[0]
            if len(xs) >= 8:
                xl = min(xs[0] + 3, xs[-1])
                xr = max(xl + 1, xs[-1] - 3)
                sample_x = np.linspace(xl, xr, 128, dtype=np.float32)
                row_rgb = cv2.remap(
                    rgb[yy : yy + 1, :, :],
                    sample_x[None, :],
                    np.zeros((1, 128), dtype=np.float32),
                    cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REPLICATE,
                )[0]
                last_row = row_rgb
            out[r] = last_row
        return out

    # Seamless 360° turquoise gold-studded skin (`pickle_skin.png`)
    back_a = extract_normalized_rows(srgb_views[8], y0=28, y1=328)[:, 18:110, :]
    back_b = extract_normalized_rows(srgb_views[7], y0=28, y1=328)[:, 18:110, :]
    s_a = cv2.resize(back_a, (256, 256), interpolation=cv2.INTER_CUBIC)
    s_b = cv2.resize(np.roll(back_b, shift=128, axis=0), (256, 256), interpolation=cv2.INTER_CUBIC)
    w_wrap = (0.5 - 0.5 * np.cos(np.linspace(0.0, 2.0 * math.pi, 256, endpoint=False, dtype=np.float32)))[None, :, None]
    gib_srgb = np.clip(np.round(s_a * (1.0 - w_wrap) + s_b * w_wrap), 0, 255).astype(np.uint8)
    Image.fromarray(gib_srgb, "RGB").save(os.path.join(OUT_DIR, "pickle_skin_srgb.png"), optimize=True)
    gib_quake = ptr.tone_for_quake_hdr(
        np.dstack([gib_srgb, np.full((256, 256), 255, dtype=np.uint8)]), dim=0.45, contrast=1.10
    )[..., :3]
    Image.fromarray(gib_quake, "RGB").save(os.path.join(PROGS, "pickle_skin.png"), optimize=False)

    # 8-expression live face sequence on seamless 360° turquoise gold-studded wrap!
    back_full = cv2.resize(
        extract_normalized_rows(srgb_views[8], y0=22, y1=340)[:, 14:114, :], (TEX_W, TEX_H), interpolation=cv2.INTER_CUBIC
    )
    side_r = cv2.resize(extract_normalized_rows(srgb_views[4])[:, 16:112, :], (220, TEX_H), interpolation=cv2.INTER_CUBIC)
    side_l = cv2.resize(extract_normalized_rows(srgb_views[12])[:, 16:112, :], (220, TEX_H), interpolation=cv2.INTER_CUBIC)

    front_8_exprs = [
        pose_sets[0][0],   # 0: Sing front
        pose_sets[0][1],   # 1: Sing slight left
        pose_sets[1][0],   # 2: Cheeky Puffed-Cheek Pucker Wink!
        pose_sets[0][2],   # 3: Sing turn left
        pose_sets[2][0],   # 4: Wild Bug-Eyes + Pink Tongue Out!
        pose_sets[3][0],   # 5: Wide Surprised Gasp!
        pose_sets[1][15],  # 6: Cheeky Wink right!
        pose_sets[0][15],  # 7: Sing slight right
    ]
    os.makedirs(os.path.join(OUT_DIR, "bomb_faces"), exist_ok=True)
    for old in glob.glob(os.path.join(PROGS, "pickle_face_*.png")):
        os.remove(old)

    w512 = (0.5 - 0.5 * np.cos(np.linspace(0.0, 2.0 * math.pi, TEX_W, endpoint=False, dtype=np.float32)))[None, :, None]
    w_side = (0.5 * (1.0 + np.cos(np.linspace(-math.pi, math.pi, 220, dtype=np.float32))))[None, :, None] * 0.75
    w_front = (0.5 * (1.0 + np.cos(np.linspace(-math.pi, math.pi, 236, dtype=np.float32))))[None, :, None] ** 0.75

    for idx_f, front_rgba in enumerate(front_8_exprs):
        base_r = np.roll(back_full, shift=TEX_W // 2, axis=1)
        canvas_360 = back_full * (1.0 - w512) + base_r * w512
        canvas_360[:, 256 - 110 : 256 + 110, :] = (
            canvas_360[:, 256 - 110 : 256 + 110, :] * (1.0 - w_side) + side_r * w_side
        )
        rolled = np.roll(canvas_360, shift=110, axis=1)
        rolled[:, 0:220, :] = rolled[:, 0:220, :] * (1.0 - w_side) + side_l * w_side
        canvas_360 = np.roll(rolled, shift=-110, axis=1)

        front_strip = cv2.resize(extract_normalized_rows(front_rgba), (236, TEX_H), interpolation=cv2.INTER_CUBIC)
        xs0 = 128 - 118
        canvas_360[:, xs0 : xs0 + 236, :] = (
            canvas_360[:, xs0 : xs0 + 236, :] * (1.0 - w_front) + front_strip * w_front
        )

        face_srgb = np.clip(np.round(canvas_360), 0, 255).astype(np.uint8)
        Image.fromarray(face_srgb, "RGB").save(
            os.path.join(OUT_DIR, "bomb_faces", f"bomb_face_{idx_f:02d}.png"), optimize=True
        )
        face_quake = ptr.tone_for_quake_hdr(
            np.dstack([face_srgb, np.full((TEX_H, TEX_W), 255, dtype=np.uint8)]), dim=0.45, contrast=1.10
        )[..., :3]
        Image.fromarray(face_quake, "RGB").save(os.path.join(PROGS, f"pickle_face_{idx_f:02d}.png"), optimize=False)

    # Sculpt 3D totem mesh for `progs/pickle_bomb.md3` & `progs/pickle_gib.md3`
    def write_totem_pickle_md3(path: str, name: str, shader_name: str) -> None:
        L, R, RINGS, SEGS, BEND = 13.0, 2.75, 20, 20, 0.55
        verts, norms, st, tris = [], [], [], []
        for i in range(RINGS + 1):
            t = i / float(RINGS)
            u = 2.0 * t - 1.0
            dome_env = max(0.0, 1.0 - (abs(u) ** 3.6)) ** 0.48
            cheek_bulge = 1.0 + 0.14 * math.exp(-(((t - 0.68) / 0.16) ** 2)) - 0.08 * math.exp(-(((t - 0.92) / 0.10) ** 2))
            stud_bump = 1.0 + (0.045 * math.sin(t * 18.0) if t < 0.52 else 0.0)
            r = R * dome_env * cheek_bulge * stud_bump
            cy = BEND * (1.0 - u * u)
            for j in range(SEGS + 1):
                a = 2.0 * math.pi * j / SEGS
                ny, nz = math.cos(a), math.sin(a)
                rz = r * (0.92 if (nz > 0.2 and 0.48 < t < 0.90) else 1.0)
                ry = r * (1.06 if (0.55 < t < 0.82) else 1.0)
                verts.append(((t - 0.5) * L, cy + ry * ny, rz * nz))
                norms.append((0.0, ny, nz) if 0 < i < RINGS else ((-1.0 if i == 0 else 1.0), 0.0, 0.0))
                st.append((j / float(SEGS), t))
        for i in range(RINGS):
            for j in range(SEGS):
                a = i * (SEGS + 1) + j
                b = a + SEGS + 1
                tris += [(a, b, a + 1), (a + 1, b, b + 1)]
        surf = dict(name="pickle", shader=shader_name, tris=tris, st=st, frames=[(verts, norms)])
        md3lib.write(path, dict(name=name, surfaces=[surf], nframes=1))

    write_totem_pickle_md3(os.path.join(PROGS, "pickle_gib.md3"), "pickle_gib", "progs/pickle_skin")
    write_totem_pickle_md3(os.path.join(PROGS, "pickle_bomb.md3"), "pickle_bomb", "progs/pickle_bombskin")

    # Build 61-frame 4-clip animated watertight 3D `pickle3d` hull (`pickle3d_anim.npz` + `pickle3d_srgb.png`)!
    all_v, all_n, uv_arr, tri_arr, atlas_pil, clips_meta = pwr.build_animated_3d_pickle_hull(srgb_views)
    atlas_pil.save(os.path.join(OUT_DIR, "pickle3d_srgb.png"), optimize=True)
    np.savez_compressed(
        os.path.join(OUT_DIR, "pickle3d_anim.npz"),
        verts=all_v,
        norms=all_n,
        uvs=uv_arr,
        tris=tri_arr,
        clips_json=json.dumps(clips_meta),
    )


def write_world_shaders_and_effects() -> None:
    print("[5/5] Writing `scripts/pickle.shader` (64 diva skins + 8 throw skins + 8-face bombskin) & `effectinfo.txt`...")
    lines = ["// written by source/mm_tools/build_pickle_diva_overhaul.py\n"]

    # 64 standing Diva view/expression shaders (`progs/pkv_s{0..3}_v{00..15}`)
    for s_idx in range(4):
        for v_idx in range(16):
            sh = f"progs/pkv_s{s_idx}_v{v_idx:02d}"
            lines.append(
                f"{sh}\n{{\n\tcull none\n\t{{\n\t\tmap {sh}\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}}\n}}\n"
            )

    # 8 flying throw sprite shaders (`progs/pthr_00..07`)
    for k in range(8):
        lines.append(
            f"progs/pthr_{k:02d}\n{{\n\tcull none\n\t{{\n\t\tmap progs/pthr_{k:02d}\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}}\n}}\n"
        )

    # 8-expression live animated sticky bomb skin (`progs/pickle_bombskin`) + gib skin (`progs/pickle_skin`)
    face_anim = " ".join(f"progs/pickle_face_{i:02d}" for i in (0, 1, 2, 3, 4, 5, 6, 7))
    lines.append(
        f"progs/pickle_bombskin\n{{\n\t{{\n\t\tanimmap 7 {face_anim}\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
    )
    lines.append(
        "progs/pickle_skin\n{\n\t{\n\t\tmap progs/pickle_skin\n\t\trgbGen lightingDiffuse\n\t}\n}\n"
    )

    with open(os.path.join(SCRIPTS, "pickle.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(lines))

    # Update `effectinfo.txt` with `pk_throw_trail`, `pk_stick`, `pk_boom`, `pk_flame`, `pk_puff`
    base_fx = open(os.path.join(HERE, "pickle_effectinfo.txt"), "rb").read().replace(b"\r\n", b"\n")
    extra_fx = b"""
// Turquoise-lime & gold sequin spin trail on the violently hurled Pickle Surprise in flight
effect pk_throw_trail
trailspacing 8
type alphastatic
tex 0 8
color 0x18e0d8 0x80ff90
size 4.8 8.0
sizeincrease -9
alpha 185 240 480
originjitter 2.5 2.5 2.5
velocityjitter 22 22 22
airfriction 2.0

effect pk_throw_trail
trailspacing 18
type spark
tex 0 8
color 0xffd860 0xfff4a0
size 1.6 2.8
alpha 225 256 520
originjitter 3 3 3
velocityjitter 50 50 50
airfriction 1.2

// Crisp turquoise-green sticky splat puff when the thrown Pickle Surprise slaps onto a wall/floor
effect pk_stick
count 18
type alphastatic
tex 0 8
color 0x18d8c8 0x80ff70
size 4 8.5
sizeincrease 15
alpha 215 256 420
originjitter 3 3 3
velocityjitter 105 105 105
airfriction 2.5
"""
    combined = (base_fx.rstrip(b"\n") + b"\n" + extra_fx.lstrip(b"\n")).replace(b"\n", b"\r\n")
    fx_path = os.path.join(MOD, "effectinfo.txt")
    begin, end = b"// ---- Pickle Surprise begin", b"// ---- Pickle Surprise end"
    raw = open(fx_path, "rb").read()
    if begin in raw:
        raw = raw[: raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end) :].lstrip(b"\r\n")
    open(fx_path, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + combined + end + b"\r\n")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Load & repair 16 turntable views (`progs/pickle_00..15.png`)
    raw_pk16 = [
        np.asarray(Image.open(os.path.join(PROGS, f"pickle_{k:02d}.png")).convert("RGBA"))
        for k in range(16)
    ]
    srgb_pk16 = [pwr.decontaminate_and_boost_turntable(im) for im in raw_pk16]
    srgb_pk16 = pwr.repair_profile_eye_notches(srgb_pk16)

    # 2. Load & rim-decontaminate 48 studio viewmodel frames (`progs/vpk_00..47.png`)
    vpk_paths = sorted(glob.glob(os.path.join(PROGS, "vpk_*.png")))
    assert len(vpk_paths) == 48, f"Expected 48 vpk_*.png frames, found {len(vpk_paths)}"
    srgb_vpk = [
        ptr.boost_vpk_to_studio_srgb(ptr.decontaminate_rgba(np.asarray(Image.open(p).convert("RGBA"))))
        for p in vpk_paths
    ]

    rig_t = build_viewmodel_overhaul(srgb_vpk, srgb_pk16[0])
    pose_sets = build_world_diva_and_throw_sprite(srgb_pk16, rig_t)
    build_3d_totem_and_hull_assets(srgb_pk16, pose_sets)
    write_world_shaders_and_effects()
    print("\n=== MASTER PICKLE SURPRISE DIVA & VIOLENT THROW OVERHAUL COMPLETE ===")


def fast_install_from_out() -> None:
    """Installs all `progs/*` models, `.skin` files, toned textures, and `scripts/*` shaders in ~2s from `OUT_DIR`."""
    print("[Fast Install] Installing v_pickle.md3 (120 skins), pickle.md3 (36f, 64 skins), pickle_throw, pickle_bomb & shaders...")
    for old in glob.glob(os.path.join(PROGS, "pvm_*.png")):
        os.remove(old)
    vm_shaders: list[str] = []
    for idx in range(PVM_TOTAL_SKINS):
        ds_srgb = np.asarray(Image.open(os.path.join(OUT_DIR, "v_pickle", f"pvm_srgb_{idx:03d}.png")).convert("RGBA"))
        toned = ptr.tone_for_quake_hdr(ds_srgb, dim=0.56, contrast=1.08)
        tname = f"pvm_{idx:03d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
        vm_shaders.append(f"progs/{tname}")

    u_per_px = 24.0 / 607.0
    y_right = -28.5
    y_left = y_right + ptr.STAGE_W * u_per_px
    z_bot = -19.5
    z_top = z_bot + ptr.STAGE_H * u_per_px
    write_card_md3(
        os.path.join(PROGS, "v_pickle.md3"), "v_pickle", "card", vm_shaders[0],
        dx=14.0, y_left=y_left, y_right=y_right, z_bot=z_bot, z_top=z_top, double_sided=False,
    )
    write_skin_files("v_pickle.md3", "card", vm_shaders)
    sh_lines = ["// written by source/mm_tools/build_pickle_diva_overhaul.py\n"]
    for sh in vm_shaders:
        sh_lines.append(f"{sh}\n{{\n\tcull none\n\t{{\n\t\tmap {sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n")
    with open(os.path.join(SCRIPTS, "picklevm.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(sh_lines))

    # 36-frame deforming `progs/pickle.md3` + 64 skins
    balloon_shaders: list[str] = []
    for s_idx in range(4):
        for v_idx in range(16):
            im_srgb = np.asarray(Image.open(os.path.join(OUT_DIR, "diva_views", f"diva_s{s_idx}_v{v_idx:02d}.png")).convert("RGBA"))
            toned = ptr.tone_for_quake_hdr(im_srgb, dim=0.36, contrast=1.12)
            tname = f"pkv_s{s_idx}_v{v_idx:02d}"
            Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
            balloon_shaders.append(f"progs/{tname}")
    md3_def = md3lib.read(os.path.join(OUT_DIR, "pickle_deforming.md3"))
    md3_def["surfaces"][0]["shader"] = balloon_shaders[0]
    md3lib.write(os.path.join(PROGS, "pickle.md3"), md3_def)
    write_skin_files("pickle.md3", "card", balloon_shaders)

    # 8 throw skins
    throw_shaders: list[str] = []
    for k in range(8):
        im_srgb = np.asarray(Image.open(os.path.join(OUT_DIR, "throw_sprite", f"pthr_srgb_{k:02d}.png")).convert("RGBA"))
        toned = ptr.tone_for_quake_hdr(im_srgb, dim=0.44, contrast=1.10)
        tname = f"pthr_{k:02d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
        throw_shaders.append(f"progs/{tname}")
    write_card_md3(
        os.path.join(PROGS, "pickle_throw.md3"), "pickle_throw", "card", throw_shaders[0],
        dx=0.0, y_left=8.0, y_right=-8.0, z_bot=-8.0, z_top=8.0, double_sided=True,
    )
    write_skin_files("pickle_throw.md3", "card", throw_shaders)

    # 8-expression bomb faces + gib skin
    gib_srgb = np.asarray(Image.open(os.path.join(OUT_DIR, "pickle_skin_srgb.png")).convert("RGB"))
    gib_q = ptr.tone_for_quake_hdr(np.dstack([gib_srgb, np.full((256, 256), 255, dtype=np.uint8)]), dim=0.45, contrast=1.10)[..., :3]
    Image.fromarray(gib_q, "RGB").save(os.path.join(PROGS, "pickle_skin.png"), optimize=False)
    for old in glob.glob(os.path.join(PROGS, "pickle_face_*.png")):
        os.remove(old)
    for idx_f in range(8):
        f_srgb = np.asarray(Image.open(os.path.join(OUT_DIR, "bomb_faces", f"bomb_face_{idx_f:02d}.png")).convert("RGB"))
        f_q = ptr.tone_for_quake_hdr(np.dstack([f_srgb, np.full((512, 512), 255, dtype=np.uint8)]), dim=0.45, contrast=1.10)[..., :3]
        Image.fromarray(f_q, "RGB").save(os.path.join(PROGS, f"pickle_face_{idx_f:02d}.png"), optimize=False)

    write_world_shaders_and_effects()
    print("[Fast Install] COMPLETE!")


if __name__ == "__main__":
    if "--fast-install" in sys.argv:
        fast_install_from_out()
    else:
        main()
