"""Complete Pickle Surprise Grenade Asset Overhaul Builder (`source/mm_tools/build_pickle_overhaul.py`).

Generates and installs all upgraded Pickle Surprise models, skins, textures, shaders, and particle effects:
  1. `progs/v_pickle.md3` + `progs/v_pickle.md3_0..134.skin` + `progs/pvm_*.png` + `scripts/picklevm.shader`:
     - Skins `0..94`  (`95` frames): 20fps optical-flow smoothed, rim-decontaminated idle with complete rounded
       turquoise crown dome and extended bronze vambrace cuff (ping-ponged cleanly in QuakeC — zero 64-frame cut!).
     - Skins `95..112` (`18` frames): Snap choke-squeeze windup -> blistering diagonal forward whip -> wide-open
       armored gauntlet release (`Pk_Launch` at frame 14 of wind_whip = skin `109`!).
     - Skins `113..122` (`10` frames): Empty open-claw follow-through slashing down-left off screen.
     - Skins `123..134` (`12` frames): Aggressive belt-snatch reload with elastic cheek-squish settle into idle.
  2. `progs/pickle_throw.md3` + `progs/pickle_throw.md3_0..7.skin` + `progs/pthr_00..07.png`:
     - Seamless camera-billboarded spinning/tumbling Pickle Surprise throw sprite used while in flight (`pk_state == 1`),
       matching the held Pickle Surprise at the exact release ray before sticking as 3D `pickle_bomb.md3` on impact!
  3. `progs/pickle_bomb.md3` & `progs/pickle_gib.md3` + `progs/pickle_skin.png` & `progs/pickle_face_00,01,02,15.png`:
     - Upgraded 3D Pickle Surprise totem mesh wrapped in a true 360-degree photographic turquoise gold-studded unwrap
       built directly from `progs/pickle_00..15.png` (eliminating the mismatched dull olive-green cylinder!).
  4. `progs/pickle.md3` + `progs/pickle.md3_0..19.skin`:
     - 1-card, 1-frame, 20-skin standing Pickle Surprise balloon (eliminating DarkPlaces MD3 vertex-lerp pulsing!).
  5. `effectinfo.txt` (`pk_throw_trail`, `pk_stick`, `pk_boom`, `pk_flame`, `pk_puff`).
"""
from __future__ import annotations

import glob
import math
import os
import shutil
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib
import pickle_throw_rig as ptr

MOD = r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")

# Skin index layout for `progs/v_pickle.md3` (must match `pickle.qc` constants!)
PVM_IDLE_SKIN = 0       # 0..94   (95 frames: 48 studio + 47 optical-flow mid-frames)
PVM_IDLE_COUNT = 95
PVM_WIND_SKIN = 95      # 95..112 (18 frames: windup 0..6, whip 7..13, open-palm release 14..17)
PVM_WIND_COUNT = 18
PVM_RELEASE_STEP = 14   # skin 95 + 14 = 109 is first open-palm empty frame (`Pk_Launch()` fires here!)
PVM_FOLLOW_SKIN = 113   # 113..122 (10 frames: empty-gauntlet follow-through off bottom-left)
PVM_FOLLOW_COUNT = 10
PVM_RELOAD_SKIN = 123   # 123..134 (12 frames: belt-snatch fresh Pickle raise & squish settle)
PVM_RELOAD_COUNT = 12
PVM_TOTAL_SKINS = PVM_IDLE_COUNT + PVM_WIND_COUNT + PVM_FOLLOW_COUNT + PVM_RELOAD_COUNT  # 135


def write_single_card_md3(
    path: str,
    model_name: str,
    surf_name: str,
    default_shader: str,
    dx: float,
    y_left: float,
    y_right: float,
    z_bot: float,
    z_top: float,
) -> None:
    """Writes a 1-surface, 1-frame double-sided MD3 card in the Y/Z plane at `x = dx` facing `-X`."""
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
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
    """Writes `progs/<md3_basename>_<k>.skin` files mapping `surf_name` to `shaders[k]`."""
    for old in glob.glob(os.path.join(PROGS, f"{md3_basename}_*.skin")):
        os.remove(old)
    for k, sh in enumerate(shaders):
        skin_path = os.path.join(PROGS, f"{md3_basename}_{k}.skin")
        with open(skin_path, "wb") as f:
            f.write(f"{surf_name},{sh}\n".encode("ascii"))


def build_viewmodel_assets(raw_vpk_srgb: list[np.ndarray], pk0_srgb: np.ndarray, throw_only: bool = False) -> dict:
    """Builds `progs/pvm_*.png`, `progs/v_pickle.md3`, `progs/v_pickle.md3_0..134.skin`, and `scripts/picklevm.shader`."""
    if not throw_only:
        print("[1/5] Expanding & dome-completing 48 studio frames + computing 47 optical-flow in-betweens...")
        base_48 = [ptr.prepare_expanded_vpk_frame(f, pk0_srgb) for f in raw_vpk_srgb]
        idle_95: list[np.ndarray] = []
        for i in range(len(base_48)):
            idle_95.append(base_48[i])
            if i + 1 < len(base_48):
                idle_95.append(ptr.interpolate_flow_pair(base_48[i], base_48[i + 1], 0.5))
        assert len(idle_95) == PVM_IDLE_COUNT
    else:
        print("[1/5] Keeping existing 95 optical-flow idle frames (--throw-only)...")
        idle_95 = []

    print("[2/5] Rendering articulated violent throw, snap-open release, follow-through & belt-snatch reload...")
    rig = ptr.PickleThrowRig(raw_vpk_srgb, pk0_srgb)
    handoff = rig.measure_pre_release_pickle_bbox(PVM_WIND_COUNT, PVM_RELEASE_STEP - 1)
    wind_18 = rig.render_phase_frames("wind_whip", PVM_WIND_COUNT)
    follow_10 = rig.render_phase_frames("follow", PVM_FOLLOW_COUNT)
    reload_12 = rig.render_phase_frames("reload", PVM_RELOAD_COUNT)

    if not throw_only:
        all_frames = idle_95 + wind_18 + follow_10 + reload_12
        assert len(all_frames) == PVM_TOTAL_SKINS
        for old in glob.glob(os.path.join(PROGS, "pvm_*.png")):
            os.remove(old)
        start_idx = 0
    else:
        all_frames = wind_18 + follow_10 + reload_12
        start_idx = PVM_WIND_SKIN

    shader_names: list[str] = [f"progs/pvm_{k:03d}" for k in range(PVM_TOTAL_SKINS)]
    for rel_i, frame_srgb in enumerate(all_frames):
        idx = start_idx + rel_i
        ds = ptr.downsample_canvas(frame_srgb, (ptr.OUT_W, ptr.OUT_H))
        toned = ptr.tone_for_quake_hdr(ds, dim=0.58, contrast=1.08)
        tex_name = f"pvm_{idx:03d}"
        Image.fromarray(toned, "RGBA").save(os.path.join(PROGS, f"{tex_name}.png"), optimize=False)

    # Exact 3D card coordinates preserving 1:1 original resting pixel position & scale
    U_PER_PX = 24.0 / 607.0
    y_left0 = -28.5 + 24.0 * (512.0 / 607.0)
    y_left = y_left0 + ptr.X_OFF * U_PER_PX
    y_right = -28.5 - (ptr.CANVAS_W - ptr.X_OFF - ptr.ORIG_W) * U_PER_PX
    z_top = 4.5 + ptr.Y_OFF * U_PER_PX
    z_bot = -19.5 - (ptr.CANVAS_H - ptr.Y_OFF - ptr.ORIG_H) * U_PER_PX

    write_single_card_md3(
        os.path.join(PROGS, "v_pickle.md3"),
        "v_pickle",
        "card",
        shader_names[0],
        dx=14.0,
        y_left=y_left,
        y_right=y_right,
        z_bot=z_bot,
        z_top=z_top,
    )
    write_skin_files("v_pickle.md3", "card", shader_names)

    # Write `scripts/picklevm.shader` with smooth 8-bit straight-alpha `blendfunc blend` + `rgbGen lightingDiffuse`
    sh_lines = ["// written by source/mm_tools/build_pickle_overhaul.py\n"]
    for sh in shader_names:
        sh_lines.append(
            f"{sh}\n{{\n\tcull none\n\t{{\n\t\tmap {sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    with open(os.path.join(SCRIPTS, "picklevm.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(sh_lines))

    return handoff


def build_throw_sprite_and_balloon(pk_turntable_raw: list[np.ndarray], pk_scream_raw: dict[int, np.ndarray]) -> float:
    """Builds:
      1. `progs/pickle_throw.md3` + `progs/pickle_throw.md3_0..7.skin` (spinning/tumbling flying Pickle Surprise sprite!)
      2. `progs/pickle.md3` + `progs/pickle.md3_0..19.skin` (1-card, 20-skin zero-pulse standing Pickle Surprise balloon!)
    Returns exact `THROW_CARD_HALF` so QuakeC initial scale matches the viewmodel release pixel height!"""
    print("[3/5] Building flying tumble sprite (`progs/pickle_throw.md3`) & zero-pulse balloon (`progs/pickle.md3`)...")

    # 8 tumbling views for `pickle_throw.md3`:
    # skin 0 = screaming front (`scream_00`), then turntable rotation (`scream_02, 04, 06, 08, 10, 12, scream_15`)
    throw_sources = [
        pk_scream_raw[0],
        pk_scream_raw[2],
        pk_turntable_raw[4],
        pk_turntable_raw[6],
        pk_turntable_raw[8],
        pk_turntable_raw[10],
        pk_turntable_raw[12],
        pk_scream_raw[15],
    ]
    for old in glob.glob(os.path.join(PROGS, "pthr_*.png")):
        os.remove(old)

    throw_shaders: list[str] = []
    # Measure active vertical fraction of pickle inside 512x512 canvas (`y=21..490` -> `469/512 = 0.916`)
    for k, src in enumerate(throw_sources):
        clean = ptr.decontaminate_rgba(src, rim_px=4.0, erode_px=0.5)
        # Lift slightly from world `DIM=0.3` (`1.28x`) so flying sprite matches the vibrant turquoise sheen of the hand!
        srgb_lifted = ptr.boost_vpk_to_studio_srgb(clean, mul=1.32)
        ds = ptr.downsample_canvas(srgb_lifted, (256, 256))
        tname = f"pthr_{k:02d}"
        Image.fromarray(ds, "RGBA").save(os.path.join(PROGS, f"{tname}.png"), optimize=False)
        throw_shaders.append(f"progs/{tname}")

    THROW_HALF = 8.0  # 16 x 16 unit centered card (`active pickle height = 16 * 0.916 = 14.66` units at scale 1.0)
    write_single_card_md3(
        os.path.join(PROGS, "pickle_throw.md3"),
        "pickle_throw",
        "card",
        throw_shaders[0],
        dx=0.0,
        y_left=THROW_HALF,
        y_right=-THROW_HALF,
        z_bot=-THROW_HALF,
        z_top=THROW_HALF,
    )
    write_skin_files("pickle_throw.md3", "card", throw_shaders)

    # Rebuild `progs/pickle.md3` as a 1-card, 1-frame model with 20 `.skin` files (`0..15` views + `16..19` scream views)!
    # Also clean rim halos on `pickle_00..15.png` & `pickle_scream_*.png` if needed while keeping exact dimensions/brightness
    balloon_shaders: list[str] = []
    for k in range(16):
        balloon_shaders.append("progs/pickle_front" if k == 0 else f"progs/pickle_v{k:02d}")
    for v in (0, 1, 2, 15):
        balloon_shaders.append("progs/pickle_scream_front" if v == 0 else f"progs/pickle_scream_v{v:02d}")

    HALF = 10.0
    write_single_card_md3(
        os.path.join(PROGS, "pickle.md3"),
        "pickle",
        "card",
        balloon_shaders[0],
        dx=0.0,
        y_left=HALF,
        y_right=-HALF,
        z_bot=-HALF,
        z_top=HALF,
    )
    write_skin_files("pickle.md3", "card", balloon_shaders)
    return THROW_HALF * (469.0 / 512.0) * 2.0  # active pickle height in units at scale 1.0 (~14.66)


def build_turquoise_3d_pickle_models(pk_turntable_raw: list[np.ndarray]) -> None:
    """Rebuilds `progs/pickle_skin.png`, `progs/pickle_face_00,01,02,15.png`, `progs/pickle_bomb.md3`,
    and `progs/pickle_gib.md3` using a genuine 360-degree cylindrical unwrap of the turquoise gold-studded
    Pickle Surprise turntable views (`progs/pickle_00..15.png`)!"""
    print("[4/5] Unwrapping 360-degree turquoise gold-studded textures & sculpting 3D `pickle_bomb.md3` / `pickle_gib.md3`...")
    TEX_W, TEX_H = 512, 512

    def extract_normalized_rows(im_rgba: np.ndarray, y0: int = 22, y1: int = 488) -> np.ndarray:
        """Maps each row `r in 0..TEX_H-1` between `y0` (crown top) and `y1` (chin bottom) across horizontal span `[-1..+1]`."""
        out = np.zeros((TEX_H, 128, 3), dtype=np.float32)
        rgb = im_rgba[..., :3].astype(np.float32)
        a = im_rgba[..., 3]
        # Fallback rich dark-turquoise base color if any row is empty near pole
        valid = a > 160
        fallback = np.median(rgb[valid], axis=0) if np.any(valid) else np.array([12.0, 52.0, 62.0], dtype=np.float32)
        last_row = np.tile(fallback, (128, 1))
        for r in range(TEX_H):
            yy = int(round(y0 + (y1 - y0) * (r / float(TEX_H - 1))))
            yy = max(0, min(im_rgba.shape[0] - 1, yy))
            xs = np.where(a[yy] > 140)[0]
            if len(xs) >= 8:
                # Inset 3px from silhouette edge so zero background rim enters the 3D wrap!
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

    strips_16 = [extract_normalized_rows(im) for im in pk_turntable_raw]

    # 1. Build `progs/pickle_skin.png`: seamless 360-degree glossy turquoise gold-studded pickle skin!
    #    Sample the rich studded turquoise body (`y0=28..330` of `pickle_08` & `pickle_07`) with cosine wrap-blending so
    #    there are ZERO vertical seams!
    back_a = extract_normalized_rows(pk_turntable_raw[8], y0=28, y1=328)[:, 18:110, :]
    back_b = extract_normalized_rows(pk_turntable_raw[7], y0=28, y1=328)[:, 18:110, :]
    s_a = cv2.resize(back_a, (256, 256), interpolation=cv2.INTER_CUBIC)
    s_b = cv2.resize(np.roll(back_b, shift=128, axis=0), (256, 256), interpolation=cv2.INTER_CUBIC)
    w_wrap = (0.5 - 0.5 * np.cos(np.linspace(0.0, 2.0 * math.pi, 256, endpoint=False, dtype=np.float32)))[None, :, None]
    gib_tex = s_a * (1.0 - w_wrap) + s_b * w_wrap
    gib_u8 = np.clip(np.round(gib_tex * 1.25), 0, 255).astype(np.uint8)
    Image.fromarray(gib_u8, "RGB").save(os.path.join(PROGS, "pickle_skin.png"), optimize=False)

    # 2. Build `progs/pickle_face_{15,00,01,02}.png` (`512 x 512`):
    #    Smoothly cross-blend the 4 cardinal views (`view 12` at u=0.0, `front` at u=0.25, `view 4` at u=0.50, `view 8` at u=0.75)
    #    with raised-cosine weights so there are ZERO vertical strip seams anywhere around the 360-degree mesh!
    back_full = cv2.resize(extract_normalized_rows(pk_turntable_raw[8], y0=22, y1=340)[:, 14:114, :], (TEX_W, TEX_H), interpolation=cv2.INTER_CUBIC)
    side_r = cv2.resize(strips_16[4][:, 16:112, :], (220, TEX_H), interpolation=cv2.INTER_CUBIC)
    side_l = cv2.resize(strips_16[12][:, 16:112, :], (220, TEX_H), interpolation=cv2.INTER_CUBIC)

    for front_idx in (15, 0, 1, 2):
        # Start from seamless turquoise gold-studded wrap (`back_full` tiled horizontally with smooth seam blend)
        base_r = np.roll(back_full, shift=TEX_W // 2, axis=1)
        w512 = (0.5 - 0.5 * np.cos(np.linspace(0.0, 2.0 * math.pi, TEX_W, endpoint=False, dtype=np.float32)))[None, :, None]
        canvas_360 = back_full * (1.0 - w512) + base_r * w512

        # Blend right side (`u = 0.50 -> x = 256`) and left side (`u = 0.00 -> x = 0/512`)
        w_side = (0.5 * (1.0 + np.cos(np.linspace(-math.pi, math.pi, 220, dtype=np.float32))))[None, :, None] * 0.75
        canvas_360[:, 256 - 110 : 256 + 110, :] = (
            canvas_360[:, 256 - 110 : 256 + 110, :] * (1.0 - w_side) + side_r * w_side
        )
        rolled = np.roll(canvas_360, shift=110, axis=1)
        rolled[:, 0:220, :] = rolled[:, 0:220, :] * (1.0 - w_side) + side_l * w_side
        canvas_360 = np.roll(rolled, shift=-110, axis=1)

        # Blend crisp full front face & third eye centered at `u = 0.25` (`x = 128`)
        front_wide = cv2.resize(strips_16[front_idx], (236, TEX_H), interpolation=cv2.INTER_CUBIC)
        w_front = (0.5 * (1.0 + np.cos(np.linspace(-math.pi, math.pi, 236, dtype=np.float32))))[None, :, None] ** 0.75
        xs0 = 128 - 118  # 10..246
        canvas_360[:, xs0 : xs0 + 236, :] = (
            canvas_360[:, xs0 : xs0 + 236, :] * (1.0 - w_front) + front_wide * w_front
        )

        face_u8 = np.clip(np.round(canvas_360 * 1.25), 0, 255).astype(np.uint8)
        Image.fromarray(face_u8, "RGB").save(os.path.join(PROGS, f"pickle_face_{front_idx:02d}.png"), optimize=False)

    # 3. Sculpt authentic Pickle Surprise 3D mesh (`progs/pickle_bomb.md3` & `progs/pickle_gib.md3`)
    def write_totem_pickle_md3(path: str, name: str, shader_name: str) -> None:
        L, R, RINGS, SEGS, BEND = 13.0, 2.75, 20, 20, 0.55
        verts, norms, st, tris = [], [], [], []
        for i in range(RINGS + 1):
            t = i / float(RINGS)  # 0 = crown dome (-X), 1 = chin (+X)
            u = 2.0 * t - 1.0
            # Authentic Pickle Surprise profile: rounded crown dome (t=0..0.5), slightly broader cheekbone/ear zone (t=0.68), tapered chin (t=1.0)
            dome_env = max(0.0, 1.0 - (abs(u) ** 3.6)) ** 0.48
            cheek_bulge = 1.0 + 0.14 * math.exp(-(((t - 0.68) / 0.16) ** 2)) - 0.08 * math.exp(-(((t - 0.92) / 0.10) ** 2))
            stud_bump = 1.0 + (0.045 * math.sin(t * 18.0) if t < 0.52 else 0.0)
            r = R * dome_env * cheek_bulge * stud_bump
            cy = BEND * (1.0 - u * u)
            for j in range(SEGS + 1):
                a = 2.0 * math.pi * j / SEGS
                ny, nz = math.cos(a), math.sin(a)
                # Subtle horizontal face flattening on +Z (`nz > 0.3, t in 0.5..0.9`) so the face reads crisply!
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


def write_world_pickle_shader_and_effects() -> None:
    """Writes clean `scripts/pickle.shader` (including `pthr_00..07` throw sprite shaders, `pickle_bombskin`,
    `pickle_skin`, and all 20 standing balloon view shaders) and updates `effectinfo.txt` with `pk_throw_trail` & `pk_stick`."""
    print("[5/5] Writing `scripts/pickle.shader` and updating `effectinfo.txt`...")
    lines = ["// written by source/mm_tools/build_pickle_overhaul.py\n"]

    # Standing balloon front animated shader + v01..v15 + scream shaders
    lines.append(
        "progs/pickle_front\n{\n\tcull none\n\t{\n\t\tanimmap 5 progs/pickle_15 progs/pickle_00 progs/pickle_01 progs/pickle_02 progs/pickle_01 progs/pickle_00\n\t\talphafunc GE128\n\t}\n}\n"
    )
    for k in range(1, 16):
        lines.append(f"progs/pickle_v{k:02d}\n{{\n\tcull none\n\t{{\n\t\tmap progs/pickle_{k:02d}\n\t\talphafunc GE128\n\t}}\n}}\n")

    lines.append(
        "progs/pickle_scream_front\n{\n\tcull none\n\t{\n\t\tanimmap 5 progs/pickle_scream_15 progs/pickle_scream_00 progs/pickle_scream_01 progs/pickle_scream_02 progs/pickle_scream_01 progs/pickle_scream_00\n\t\talphafunc GE128\n\t}\n}\n"
    )
    for v in (1, 2, 15):
        lines.append(
            f"progs/pickle_scream_v{v:02d}\n{{\n\tcull none\n\t{{\n\t\tmap progs/pickle_scream_{v:02d}\n\t\talphafunc GE128\n\t}}\n}}\n"
        )

    # Flying throw sprite shaders (`progs/pthr_00..07`) — crisp alpha test + smooth blend & diffuse lighting
    for k in range(8):
        lines.append(
            f"progs/pthr_{k:02d}\n{{\n\tcull none\n\t{{\n\t\tmap progs/pthr_{k:02d}\n\t\talphafunc GE128\n\t}}\n}}\n"
        )

    # 3D stuck bomb & gib shaders (lit by world light so 3D form & turquoise/gold studs shade naturally!)
    lines.append(
        "progs/pickle_bombskin\n{\n\t{\n\t\tanimmap 5 progs/pickle_face_15 progs/pickle_face_00 progs/pickle_face_01 progs/pickle_face_02 progs/pickle_face_01 progs/pickle_face_00\n\t\trgbGen lightingDiffuse\n\t}\n}\n"
    )
    lines.append(
        "progs/pickle_skin\n{\n\t{\n\t\tmap progs/pickle_skin\n\t\trgbGen lightingDiffuse\n\t}\n}\n"
    )

    with open(os.path.join(SCRIPTS, "pickle.shader"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(lines))

    # Update `pickle_effectinfo.txt` -> `effectinfo.txt` (preserving all existing `pk_boom`, `pk_flame`, `pk_puff` + adding `pk_throw_trail` & `pk_stick`)
    base_fx = open(os.path.join(HERE, "pickle_effectinfo.txt"), "rb").read().replace(b"\r\n", b"\n")
    extra_fx = b"""
// Turquoise-lime & gold sequin spin trail on the thrown Pickle Surprise grenade in flight
effect pk_throw_trail
trailspacing 9
type alphastatic
tex 0 8
color 0x18d8d0 0x80ff90
size 4.5 7.5
sizeincrease -9
alpha 175 230 480
originjitter 2.5 2.5 2.5
velocityjitter 18 18 18
airfriction 2.0

effect pk_throw_trail
trailspacing 22
type spark
tex 0 8
color 0xffd860 0xfff4a0
size 1.5 2.6
alpha 220 256 520
originjitter 3 3 3
velocityjitter 45 45 45
airfriction 1.2

// Crisp turquoise-green sticky splat puff when the thrown Pickle Surprise slaps onto a wall/floor
effect pk_stick
count 16
type alphastatic
tex 0 8
color 0x18d8c8 0x80ff70
size 4 8
sizeincrease 14
alpha 210 256 420
originjitter 3 3 3
velocityjitter 95 95 95
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
    vpk_paths = sorted(glob.glob(os.path.join(PROGS, "vpk_*.png")))
    assert len(vpk_paths) == 48, f"Expected 48 vpk_*.png frames, found {len(vpk_paths)}"
    raw_vpk_srgb = [
        ptr.boost_vpk_to_studio_srgb(ptr.decontaminate_rgba(np.asarray(Image.open(p).convert("RGBA"))), mul=1.72)
        for p in vpk_paths
    ]
    pk_turntable = [
        np.asarray(Image.open(os.path.join(PROGS, f"pickle_{k:02d}.png")).convert("RGBA"))
        for k in range(16)
    ]
    pk_scream = {
        v: np.asarray(Image.open(os.path.join(PROGS, f"pickle_scream_{v:02d}.png")).convert("RGBA"))
        for v in (0, 1, 2, 15)
    }
    pk0_srgb = ptr.boost_vpk_to_studio_srgb(ptr.decontaminate_rgba(pk_turntable[0], rim_px=4.0, erode_px=0.5), mul=3.15)

    throw_only = "--throw-only" in sys.argv
    handoff = build_viewmodel_assets(raw_vpk_srgb, pk0_srgb, throw_only=throw_only)
    active_h_scale1 = build_throw_sprite_and_balloon(pk_turntable, pk_scream)
    if not throw_only:
        build_turquoise_3d_pickle_models(pk_turntable)
    write_world_pickle_shader_and_effects()

    exact_scale0 = handoff["world_height_at_24"] / active_h_scale1
    print("\n=== PICKLE SURPRISE ASSET OVERHAUL COMPLETE ===")
    print(f"Viewmodel skins: 0..{PVM_TOTAL_SKINS - 1} ({PVM_TOTAL_SKINS} total)")
    print(f"Release handoff at D={handoff['forward']:.1f}: right={handoff['right']:.2f}, up={handoff['up']:.2f}, rot={handoff['rot_deg']:.1f} deg")
    print(f"Exact initial throw sprite scale at D=24: {exact_scale0:.3f} (world_h={handoff['world_height_at_24']:.2f} / card_h={active_h_scale1:.2f})")


if __name__ == "__main__":
    main()
