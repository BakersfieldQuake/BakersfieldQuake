"""Export MK-IV Dookie Bazooka assets into BakersfieldQuake DarkPlaces runtime formats.

Writes (both loose in BakersfieldQuake/ and synced into _bakersfield_dev/staged_assets if active):
  - progs/v_dookie.md3 + v_dookie.md3_0..113.skin + progs/dvm_000..113.png + scripts/dookievm.shader
      60 idle (0..59) + 16 windup/charge (60..75) + 20 fire/recoil (76..95) + 18 reload (96..113)
  - progs/dookie_proj.spr32   (IDSP type 2 SPR_VP_PARALLEL, 384f: 0..127 horiz 16x8, 128..255 above45 16x8, 256..383 above90 16x8)
  - progs/dookie_splat.spr32  (IDSP type 2 SPR_VP_PARALLEL, 16 radial mud + toxic fume + fly scatter frames, centered)
  - sound/dookie/*.wav        (dk_charge = windup_v6, dk_fire = fire_v5, dk_music = proj_music,
                               dk_yell1..3, dk_scream, dk_splat, dk_flies)
  - source/mm_tools/poop_gun/work/dookie_mk4/audit_game_export.png
  - source/mm_tools/poop_gun/work/dookie_mk4/audit_overhead_sheet.png
"""
from __future__ import annotations

import glob
import math
import os
import random
import shutil
import struct
import sys
from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JAR_DIR = os.path.join(TOOLS_DIR, "green_guy_jar")
for _p in (TOOLS_DIR, JAR_DIR, os.path.dirname(__file__)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import md3lib
from bake_greenjar_all import (
    MOD_ROOT,
    PROGS_DIR,
    SCRIPTS_DIR,
    STAGED_PROGS_DIR,
    resize_rgba_premul,
    tone_for_quake_hdr_rgba,
    tone_for_spr32_rgba,
)
from poop_core import WORK_DIR, from_premul, to_premul
from poop_fx import alpha_over, render_fly_swarm, warp_rgba
from dookie_overhead import (
    _load_fx,
    load_keyed_overhead_masters,
    save_overhead_contact_sheet,
    synthesize_above45_frames,
    synthesize_above90_frames,
)

MK4_DIR = os.path.join(WORK_DIR, "dookie_mk4")
FX_DIR = os.path.join(WORK_DIR, "fx")
AUDIO_SRC_DIR = os.path.join(WORK_DIR, "audio")
SOUND_DOOKIE_DIR = os.path.join(MOD_ROOT, "sound", "dookie")
STAGED_ROOT = os.path.abspath(os.path.join(STAGED_PROGS_DIR, ".."))
STAGED_SCRIPTS_DIR = os.path.join(STAGED_ROOT, "scripts")
STAGED_SOUND_DOOKIE_DIR = os.path.join(STAGED_ROOT, "sound", "dookie")

# Approved MK-IV HTML weapon adjuster settings (16:9 viewport @ fov 111 matching user config.cfg)
VM_CFG: Dict[str, float] = {
    "xPct": 26.5,
    "yPct": 4.5,
    "scalePct": 78.0,
    "rotDeg": -2.0,
    "fovRef": 111.0,
    "muzzleX": 0.35,
    "muzzleY": 0.26,
    "aspect": 420.0 / 360.0,
}

# Sound map -> exact winning selections (#6 windup + #5 fire + flight music/yells + mud/flies)
AUDIO_EXPORTS: Dict[str, str] = {
    "windup_v6.wav": "dk_charge.wav",
    "fire_v5.wav": "dk_fire.wav",
    "proj_music.wav": "dk_music.wav",
    "yell_1.wav": "dk_yell1.wav",
    "yell_2.wav": "dk_yell2.wav",
    "yell_3.wav": "dk_yell3.wav",
    "wc_scream.wav": "dk_scream.wav",
    "mud_splat.wav": "dk_splat.wav",
    "fly_buzz.wav": "dk_flies.wav",
}


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def _sync_write(rel_targets: List[str], src_bytes: bytes) -> None:
    for dst in rel_targets:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(src_bytes)
        os.replace(tmp, dst)


def _tight_crop_and_bleed_dookie(
    rgba: np.ndarray, base_ox: int, base_oy: int, center_origin: bool = False
) -> Tuple[int, int, int, int, bytes]:
    from scipy import ndimage

    h, w, _ = rgba.shape
    ys, xs = np.nonzero(rgba[:, :, 3] > 2)
    if len(xs) == 0:
        empty = np.zeros((2, 2, 4), dtype=np.uint8)
        return -1, 1, 2, 2, empty.tobytes()
    x0 = max(0, int(xs.min()) - 1)
    y0 = max(0, int(ys.min()) - 1)
    x1 = min(w, int(xs.max()) + 2)
    y1 = min(h, int(ys.max()) + 2)
    cropped = rgba[y0:y1, x0:x1].copy()
    pad_l = 1 if x0 == int(xs.min()) else 0
    pad_t = 1 if y0 == int(ys.min()) else 0
    pad_r = 1 if x1 == int(xs.max()) + 1 else 0
    pad_b = 1 if y1 == int(ys.max()) + 1 else 0
    if pad_l or pad_t or pad_r or pad_b:
        cropped = np.pad(cropped, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="constant", constant_values=0)
        x0 -= pad_l
        y0 -= pad_t
    fg = cropped[:, :, 3] >= 32
    if not np.any(fg):
        fg = cropped[:, :, 3] > 0
    if np.any(fg):
        tr = cropped[:, :, 3] == 0
        if np.any(tr):
            _, (iy, ix) = ndimage.distance_transform_edt(~fg, return_indices=True)
            cropped[tr, :3] = cropped[iy[tr], ix[tr], :3]
    cw, ch = cropped.shape[1], cropped.shape[0]
    if center_origin:
        return -(cw // 2), ch // 2, cw, ch, cropped.tobytes()
    return int(base_ox + x0), int(base_oy - y0), cw, ch, cropped.tobytes()


def write_dookie_spr32(
    spr_path: str,
    toned_frames: Sequence[np.ndarray],
    ground_y: int,
    sprite_type: int = 2,
    center_from_frame: int | None = None,
) -> float:
    """Write a DarkPlaces IDSP v32 .spr32 sprite with configurable type and per-frame origin centering."""
    packed: List[Tuple[int, int, int, int, bytes]] = []
    for idx, fr in enumerate(toned_frames):
        fh, fw = fr.shape[:2]
        use_center = center_from_frame is not None and idx >= center_from_frame
        packed.append(
            _tight_crop_and_bleed_dookie(fr, -(fw // 2), ground_y, center_origin=use_center)
        )
    max_cw = max(f[2] for f in packed)
    max_ch = max(f[3] for f in packed)
    rad = 0.5 * math.hypot(max_cw, max_ch)
    buf = bytearray(
        b"IDSP" + struct.pack("<iifiiifi", 32, int(sprite_type), rad, max_cw, max_ch, len(packed), 0.0, 0)
    )
    for fox, foy, cw, ch, fb in packed:
        buf += struct.pack("<iiiii", 0, fox, foy, cw, ch)
        buf += fb
    targets = [spr_path]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        stg_p = os.path.join(STAGED_PROGS_DIR, os.path.basename(spr_path))
        if os.path.normcase(stg_p) != os.path.normcase(spr_path):
            targets.append(stg_p)
    _sync_write(targets, bytes(buf))
    return len(buf) / (1024.0 * 1024.0)


def _bleed_vm_edges(rgba: np.ndarray) -> np.ndarray:
    """Propagate RGB outward into alpha==0 texels so bilinear filtering never creates dark halos."""
    from scipy import ndimage

    out = rgba.copy()
    fg = out[..., 3] >= 24
    if not np.any(fg):
        fg = out[..., 3] > 0
    if np.any(fg):
        tr = out[..., 3] == 0
        if np.any(tr):
            _, (iy, ix) = ndimage.distance_transform_edt(~fg, return_indices=True)
            out[tr, :3] = out[iy[tr], ix[tr], :3]
    return out


def _build_windup_frames(idle_seq: List[np.ndarray], count: int = 16) -> List[np.ndarray]:
    """Synthesize escalating windup/overpressure shake frames from idle sequence."""
    out: List[np.ndarray] = []
    h, w = idle_seq[0].shape[:2]
    for i in range(count):
        u = i / float(max(1, count - 1))
        src = idle_seq[(i * 7) % len(idle_seq)]
        amp = 2.5 + 8.5 * (u ** 1.3)
        dx = amp * math.sin(i * 2.15)
        dy = amp * 0.75 * math.cos(i * 2.75)
        tilt = (1.8 * u) * math.sin(i * 1.9)
        warped = warp_rgba(
            src,
            angle_deg=tilt,
            sx=1.0 + 0.025 * u,
            sy=1.0 + 0.025 * u,
            dx=dx,
            dy=dy,
            pivot=(w * 0.55, h * 0.78),
            out_hw=(h, w),
        )
        # Toxic lime-gold overpressure glow over the glass reactor
        glow = np.zeros((h, w, 4), dtype=np.uint8)
        cx, cy = int(w * 0.54), int(h * 0.42)
        rad = int(52 + 28 * u)
        cv2.circle(glow, (cx, cy), rad, (120, 255, 65, int(45 + 95 * u)), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(glow, (31, 31), 12.0)
        # Mask glow roughly inside opaque silhouette so no aura leaks around transparent edges
        a_mask = (warped[..., 3:4].astype(np.float32) / 255.0)
        glow[..., 3] = np.clip(glow[..., 3].astype(np.float32) * a_mask[..., 0], 0, 255).astype(np.uint8)
        out.append(alpha_over(warped, glow, 0, 0))
    return out


def _compute_rotated_vm_quad(dx: float = 14.0) -> Tuple[List[Tuple[float, float, float]], Tuple[float, float]]:
    """Map HTML canvas (xPct, yPct, scalePct, rotDeg) at 16:9 reference FOV into DarkPlaces MD3 card corners.

    DarkPlaces `fov` is measured horizontally on a 4:3 screen (`tan_z = tan(fov/2) * 3/4`,
    `tan_y = tan_z * (16/9)`). Returns corners for st = [(0,1), (0,0), (1,0), (1,1)] and muzzle (y, z).
    """
    fov_deg = VM_CFG.get("fovRef", 111.0)
    half_z = dx * math.tan(math.radians(fov_deg * 0.5)) * 0.75
    half_y = half_z * (16.0 / 9.0)
    h_frac = VM_CFG["scalePct"] / 100.0
    w_frac = h_frac * VM_CFG["aspect"] / (16.0 / 9.0)

    cx = 0.50 + VM_CFG["xPct"] / 100.0
    vx0 = cx - w_frac * 0.5
    vy0 = (1.0 - h_frac) + VM_CFG["yPct"] / 100.0
    px = vx0 + 0.55 * w_frac
    py = vy0 + 0.78 * h_frac

    rot = math.radians(VM_CFG["rotDeg"])
    cr, sr = math.cos(rot), math.sin(rot)
    asp = 16.0 / 9.0

    def to_md3(u: float, v: float) -> Tuple[float, float, float]:
        # Scale x into isotropic pixel ratio before applying screen-space rotation
        lx = (vx0 + u * w_frac - px) * asp
        ly = vy0 + v * h_frac - py
        rx = px + (lx * cr - ly * sr) / asp
        ry = py + (lx * sr + ly * cr)
        return (dx, (0.5 - rx) * 2.0 * half_y, (0.5 - ry) * 2.0 * half_z)

    # Order matches bake_greenjar_all.py: BL (0,1), TL (0,0), TR (1,0), BR (1,1)
    quad = [to_md3(0.0, 1.0), to_md3(0.0, 0.0), to_md3(1.0, 0.0), to_md3(1.0, 1.0)]
    muzzle = to_md3(VM_CFG.get("muzzleX", 0.35), VM_CFG.get("muzzleY", 0.26))
    return quad, (muzzle[1], muzzle[2])


def _write_dookie_md3(path: str, card: List[Tuple[float, float, float]], default_shader: str) -> None:
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surf = dict(
        name="card",
        shader=default_shader,
        tris=tris,
        st=st,
        frames=[(card, [(-1.0, 0.0, 0.0)] * 4)],
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    md3lib.write(path, dict(name="v_dookie", surfaces=[surf], nframes=1))


def export_viewmodel() -> Tuple[List[np.ndarray], Tuple[float, float]]:
    print("[1/4] Exporting progs/v_dookie.md3 (114 skins) + scripts/dookievm.shader...")
    idle_all = [_load_rgba(os.path.join(MK4_DIR, f"vm_idle_{i:03d}.png")) for i in range(120)]
    idle_60 = idle_all[::2]
    windup_16 = _build_windup_frames(idle_all, 16)
    fire_20 = [_load_rgba(os.path.join(MK4_DIR, f"vm_fire_{i:03d}.png")) for i in range(20)]
    reload_18 = [_load_rgba(os.path.join(MK4_DIR, f"vm_reload_{i:03d}.png")) for i in range(18)]

    all_114 = idle_60 + windup_16 + fire_20 + reload_18
    assert len(all_114) == 114

    progs_targets = [PROGS_DIR]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        progs_targets.append(STAGED_PROGS_DIR)

    for pdir in progs_targets:
        for old in glob.glob(os.path.join(pdir, "dvm_*.png")) + glob.glob(os.path.join(pdir, "v_dookie.md3_*.skin")):
            os.remove(old)

    shader_names: List[str] = []
    for idx, fr in enumerate(all_114):
        toned = _bleed_vm_edges(tone_for_quake_hdr_rgba(fr, dim=0.87, contrast=1.04))
        tex_name = f"dvm_{idx:03d}"
        out_png = os.path.join(PROGS_DIR, f"{tex_name}.png")
        Image.fromarray(toned, "RGBA").save(out_png, optimize=False)
        if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
            shutil.copy2(out_png, os.path.join(STAGED_PROGS_DIR, f"{tex_name}.png"))
        sh = f"progs/{tex_name}"
        shader_names.append(sh)
        skin_bytes = f"card,{sh}\n".encode("ascii")
        _sync_write([os.path.join(pdir, f"v_dookie.md3_{idx}.skin") for pdir in progs_targets], skin_bytes)

    card, muzzle_yz = _compute_rotated_vm_quad(dx=14.0)
    md3_main = os.path.join(PROGS_DIR, "v_dookie.md3")
    _write_dookie_md3(md3_main, card, shader_names[0])
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        shutil.copy2(md3_main, os.path.join(STAGED_PROGS_DIR, "v_dookie.md3"))

    sh_lines = ["// written by source/mm_tools/poop_gun/export_dookie_game.py\n"]
    for sh in shader_names:
        sh_lines.append(
            f"{sh}\n{{\n\tcull none\n\t{{\n\t\tclampmap {sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    sh_bytes = "".join(sh_lines).encode("utf-8")
    sh_targets = [os.path.join(SCRIPTS_DIR, "dookievm.shader")]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        sh_targets.append(os.path.join(STAGED_SCRIPTS_DIR, "dookievm.shader"))
    _sync_write(sh_targets, sh_bytes)

    return all_114, muzzle_yz


def export_world_sprites() -> Tuple[List[np.ndarray], List[np.ndarray]]:
    print("[2/4] Exporting progs/dookie_proj.spr32 (384f: horiz + above45 + above90) and progs/dookie_splat.spr32 (16f)...")
    PROJ_W, PROJ_H = 112, 126
    OVERHEAD_SZ = 120
    proj_srgb: List[np.ndarray] = []
    proj_toned: List[np.ndarray] = []
    for a in range(16):
        for f in range(8):
            raw = _load_rgba(os.path.join(MK4_DIR, f"proj_a{a:02d}_f{f:02d}.png"))
            rs = resize_rgba_premul(raw, PROJ_W, PROJ_H)
            proj_srgb.append(rs)
            proj_toned.append(tone_for_spr32_rgba(rs))
    assert len(proj_toned) == 128

    master45, master90 = load_keyed_overhead_masters()
    fx_map = _load_fx()
    above45_srgb = synthesize_above45_frames(master45, master90, fx_map, out_sz=OVERHEAD_SZ)
    above90_srgb = synthesize_above90_frames(master90, fx_map, out_sz=OVERHEAD_SZ)
    assert len(above45_srgb) == 128 and len(above90_srgb) == 128

    overhead_sheet = save_overhead_contact_sheet(
        above45_srgb, above90_srgb, os.path.join(MK4_DIR, "audit_overhead_sheet.png")
    )
    print(f"      Overhead contact sheet -> {overhead_sheet}")

    for fr in above45_srgb + above90_srgb:
        proj_srgb.append(fr)
        proj_toned.append(tone_for_spr32_rgba(fr))
    assert len(proj_toned) == 384

    mb_proj = write_dookie_spr32(
        os.path.join(PROGS_DIR, "dookie_proj.spr32"),
        proj_toned,
        PROJ_H // 2,
        sprite_type=2,
        center_from_frame=128,
    )

    # 16-frame radial mud splatter + toxic fume + orbiting flies impact burst
    SPLAT_SZ = 128
    splat_imgs = [_load_rgba(os.path.join(FX_DIR, f"splat_0{i}.png")) for i in range(4)]
    globs = [_load_rgba(os.path.join(FX_DIR, f"mud_glob_0{i}.png")) for i in range(4)]
    mists = [_load_rgba(os.path.join(FX_DIR, f"mist_0{i}.png")) for i in range(6)]

    # Pre-seed 10 radial mud glob velocities
    glob_vecs = [
        (math.cos(2.0 * math.pi * k / 10.0 + 0.17 * k), math.sin(2.0 * math.pi * k / 10.0 + 0.17 * k))
        for k in range(10)
    ]

    splat_srgb: List[np.ndarray] = []
    splat_toned: List[np.ndarray] = []
    for i in range(16):
        u = i / 15.0
        canvas = np.zeros((SPLAT_SZ, SPLAT_SZ, 4), dtype=np.uint8)

        # Expanding toxic fume ring
        mist = resize_rgba_premul(mists[i % len(mists)], int(SPLAT_SZ * (0.45 + 0.52 * u)), int(SPLAT_SZ * (0.45 + 0.52 * u)))
        mist_fade = max(0.0, (1.0 - max(0.0, u - 0.35) / 0.65) * 0.85)
        mw, mh = mist.shape[1], mist.shape[0]
        canvas = alpha_over(canvas, mist, (SPLAT_SZ - mw) * 0.5, (SPLAT_SZ - mh) * 0.5, opacity=mist_fade)

        # Expanding wet brown mud splatter core
        sp = splat_imgs[min(3, int(u * 4))]
        sp_sz = max(24, int(SPLAT_SZ * (0.28 + 0.70 * (u ** 0.55))))
        sp_rs = resize_rgba_premul(sp, sp_sz, sp_sz)
        sp_fade = 1.0 if u < 0.55 else max(0.0, 1.0 - (u - 0.55) / 0.45)
        canvas = alpha_over(canvas, sp_rs, (SPLAT_SZ - sp_sz) * 0.5, (SPLAT_SZ - sp_sz) * 0.5, opacity=sp_fade)

        # Flying radial mud globs
        for k, (vx, vy) in enumerate(glob_vecs):
            g_im = resize_rgba_premul(globs[(k + i) % len(globs)], 18, 18)
            dist = (8.0 + 48.0 * (u ** 0.72)) * (0.85 + 0.30 * (k % 3))
            gx = SPLAT_SZ * 0.5 + vx * dist - 9.0
            gy = SPLAT_SZ * 0.5 + vy * dist - 9.0 + 10.0 * u * u
            canvas = alpha_over(canvas, g_im, gx, gy, opacity=sp_fade * 0.95)

        # Scattering flies
        canvas = render_fly_swarm(
            canvas,
            [(SPLAT_SZ * 0.5, SPLAT_SZ * 0.5)],
            t_norm=u,
            n_flies=6,
            scale=0.30,
            calm=False,
            orbit_rx=(22.0 + 26.0 * u, 38.0 + 22.0 * u),
            orbit_ry=(18.0 + 24.0 * u, 34.0 + 20.0 * u),
        )
        splat_srgb.append(canvas)
        splat_toned.append(tone_for_spr32_rgba(canvas))

    mb_splat = write_dookie_spr32(
        os.path.join(PROGS_DIR, "dookie_splat.spr32"),
        splat_toned,
        SPLAT_SZ // 2,
        sprite_type=2,
        center_from_frame=0,
    )
    print(f"      .spr32 sizes (MiB): dookie_proj={mb_proj:.2f}, dookie_splat={mb_splat:.2f}")
    return proj_srgb, splat_srgb


def _paint_poop_wall_splat(seed: int, runs: bool) -> Image.Image:
    """Render a 256x256 glossy chunky dark-brown poop splatter decal (0..2 round, 3..5 drippy wall runs)."""
    tex = 256
    big = tex * 2
    rnd = random.Random(seed)
    a = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(a)
    cx = big * 0.5
    cy = big * (0.31 if runs else 0.50)
    r0 = big * (0.19 if runs else 0.24)

    # Lumpy irregular poop core
    for _ in range(18):
        ang = rnd.uniform(0, 2 * math.pi)
        off = rnd.uniform(0, r0 * 0.62)
        rr = r0 * rnd.uniform(0.42, 0.85)
        x, y = cx + math.cos(ang) * off, cy + math.sin(ang) * off
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)

    # Radial splash fingers & thick blobs
    for _ in range(rnd.randint(12, 18)):
        ang = rnd.uniform(0, 2 * math.pi)
        ln = r0 * rnd.uniform(0.95, 1.98)
        w = big * rnd.uniform(0.013, 0.030)
        x0, y0 = cx + math.cos(ang) * r0 * 0.42, cy + math.sin(ang) * r0 * 0.42
        x1, y1 = cx + math.cos(ang) * ln, cy + math.sin(ang) * ln
        d.line((x0, y0, x1, y1), fill=255, width=max(2, int(w * 2)))
        if rnd.random() < 0.82:
            rr = w * rnd.uniform(1.3, 2.2)
            d.ellipse((x1 - rr, y1 - rr, x1 + rr, y1 + rr), fill=255)

    # Scattered chunks/droplets around the blast center
    for _ in range(rnd.randint(22, 34)):
        ang = rnd.uniform(0, 2 * math.pi)
        dist = r0 * rnd.uniform(1.10, 2.12)
        rr = big * rnd.uniform(0.008, 0.025)
        x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
        if 8 < x < big - 8 and 8 < y < big - 8:
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)

    # Thick dripping brown runs down vertical walls (frames 3..5)
    if runs:
        n_runs = rnd.randint(7, 10)
        for i in range(n_runs):
            u = (i + rnd.uniform(0.18, 0.82)) / float(n_runs)
            x = cx + (u * 2.0 - 1.0) * r0 * 1.16
            w = big * rnd.uniform(0.012, 0.028)
            y0 = cy + rnd.uniform(-0.15, 0.35) * r0
            y1 = y0 + rnd.uniform(0.30, 0.96) * (big * 0.90 - y0)
            d.rectangle((x - w, y0, x + w, y1), fill=255)
            if y1 - y0 > big * 0.22:
                ym = y0 + (y1 - y0) * rnd.uniform(0.40, 0.68)
                rb = w * rnd.uniform(1.35, 1.75)
                d.ellipse((x - rb, ym - rb * 1.1, x + rb, ym + rb * 1.2), fill=255)
            rr = w * rnd.uniform(1.65, 2.35)
            d.ellipse((x - rr, y1 - rr * 0.85, x + rr, y1 + rr * 1.35), fill=255)
            if rnd.random() < 0.62 and y1 + rr * 3.8 < big - 10:
                yd = y1 + rr * rnd.uniform(2.2, 3.5)
                rd = rr * rnd.uniform(0.60, 0.88)
                d.ellipse((x - rd, yd - rd * 1.15, x + rd, yd + rd * 1.15), fill=255)

    m = 6
    a = a.crop((m, m, big - m, big - m)).resize((big, big))
    a = a.filter(ImageFilter.GaussianBlur(2.2)).point(lambda v: 0 if v < 68 else min(255, int((v - 68) * 255 / 118)))
    a = a.resize((tex, tex), Image.LANCZOS)

    a_np = np.array(a, dtype=np.float32) / 255.0
    thick = cv2.GaussianBlur(a_np, (0, 0), 4.0)
    gx = cv2.Sobel(thick, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(thick, cv2.CV_32F, 0, 1, ksize=3)
    spec = np.clip(-0.48 * gx - 0.62 * gy + 0.25 * thick, 0.0, 1.0)
    glint = np.power(spec, 2.0)

    # Organic chunky variation (slight nutty/olive poop fleck mottling)
    rng_np = np.random.default_rng(seed + 77)
    mottle = cv2.GaussianBlur(rng_np.uniform(-1.0, 1.0, (tex, tex)).astype(np.float32), (0, 0), 3.0)
    speck = np.clip(rng_np.uniform(0.0, 1.0, (tex, tex)).astype(np.float32) - 0.96, 0.0, 1.0) * 18.0

    # Deep chocolate core -> warm muddy-brown edges -> glossy wet highlights
    r_c = (64.0 + 26.0 * (1.0 - thick) + 14.0 * mottle + 48.0 * glint + 38.0 * speck)
    g_c = (40.0 + 18.0 * (1.0 - thick) + 10.0 * mottle + 34.0 * glint + 26.0 * speck)
    b_c = (16.0 + 10.0 * (1.0 - thick) + 4.0 * mottle + 18.0 * glint + 10.0 * speck)

    rgb = np.stack([
        np.clip(np.round(r_c), 0, 255).astype(np.uint8),
        np.clip(np.round(g_c), 0, 255).astype(np.uint8),
        np.clip(np.round(b_c), 0, 255).astype(np.uint8),
    ], axis=-1)
    a_u8 = np.array(a, dtype=np.uint8)
    rgb[a_u8 == 0] = 0
    return Image.fromarray(np.dstack([rgb, a_u8]), "RGBA")


DOOKIE_EFFECTINFO_BLOCK = """// ---- Dookie Gun begin
// Thick brown/olive poop spray, flying globs, stink mist, and dripping wall splats
effect dookie_boom
count 75
type spark
blend alpha
tex 0 8
color 0x422810 0x7c4e20
size 4.0 7.2
alpha 256 256 240
originjitter 22 22 22
velocityjitter 1300 1300 980
velocityoffset 0 0 340
gravity 1
airfriction 0.45
bounce -1

effect dookie_boom
count 65
type alphastatic
tex 0 8
color 0x38200c 0x6b4218
size 4.2 8.4
alpha 256 256 125
originjitter 30 30 30
velocityjitter 980 980 720
velocityoffset 0 0 360
gravity 1
airfriction 0.3
bounce 0.16

effect dookie_boom
count 26
type alphastatic
tex 0 8
color 0x462b12 0x7e5222
size 4.0 7.6
alpha 256 256 155
originjitter 12 12 40
velocityjitter 200 200 340
velocityoffset 0 0 790
gravity 1
airfriction 0.2

effect dookie_boom
count 6
type alphastatic
tex 0 8
color 0x4d5822 0x70642c
size 54 88
sizeincrease 60
alpha 85 130 120
originjitter 58 58 48
velocityjitter 280 280 190
airfriction 2

effect dookie_boom
count 35
type alphastatic
tex 0 8
color 0x4a2e12 0x825424
size 2.0 3.8
alpha 256 256 250
originjitter 10 10 10
velocityjitter 1820 1820 1050
gravity 0.7
airfriction 1

effect dookie_glob
trailspacing 3.6
type alphastatic
tex 0 8
color 0x442910 0x7a4e1e
size 2.4 4.2
alpha 256 256 320
originjitter 2 2 2
velocityjitter 28 28 28
gravity 0.45

effect dookie_glob
trailspacing 7.5
type spark
blend alpha
tex 0 8
color 0x523216 0x885826
size 1.6 3.0
alpha 240 256 360
velocityjitter 22 22 22
gravity 0.7

effect dookie_drip
count 2
type alphastatic
tex 0 8
color 0x3c220e 0x6e441a
size 2.2 4.0
alpha 256 256 70
originjitter 3 3 2
velocityjitter 8 8 6
velocityoffset 0 0 -42
gravity 1
airfriction 0.14

effect dookie_drip
count 1
type spark
blend alpha
tex 0 8
color 0x482b12 0x784c20
size 1.5 2.8
alpha 256 256 105
originjitter 2 2 2
velocityjitter 5 5 4
velocityoffset 0 0 -75
gravity 1
// ---- Dookie Gun end
"""


def export_wall_splats_and_fx() -> None:
    print("[3/5] Exporting progs/dookie_wall.md3 + dookie_wall_0..5.png + scripts/dookiesplat.shader + effectinfo.txt...")
    variants = 6
    half = 12.0
    progs_targets = [PROGS_DIR]
    sh_targets = [os.path.join(SCRIPTS_DIR, "dookiesplat.shader")]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        os.makedirs(STAGED_PROGS_DIR, exist_ok=True)
        os.makedirs(STAGED_SCRIPTS_DIR, exist_ok=True)
        progs_targets.append(STAGED_PROGS_DIR)
        sh_targets.append(os.path.join(STAGED_SCRIPTS_DIR, "dookiesplat.shader"))

    for k in range(variants):
        im = _paint_poop_wall_splat(20261115 + k, runs=(k >= 3))
        out_png = os.path.join(PROGS_DIR, f"dookie_wall_{k}.png")
        im.save(out_png, optimize=False)
        for pd in progs_targets[1:]:
            shutil.copy2(out_png, os.path.join(pd, f"dookie_wall_{k}.png"))

    sh_lines = ["// written by source/mm_tools/poop_gun/export_dookie_game.py\n"]
    for k in range(variants):
        sh_lines.append(
            f"progs/dookie_wall_v{k}\n{{\n\tcull none\n\tnopicmip\n\tpolygonoffset\n\t{{\n\t\tmap progs/dookie_wall_{k}\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}}\n}}\n"
        )
    _sync_write(sh_targets, "".join(sh_lines).encode("utf-8"))

    # 6-frame single-sided +X wall card MD3 matching milksplat.md3 orientation
    card = [(0.0, half, -half), (0.0, half, half), (0.0, -half, half), (0.0, -half, -half)]
    nothing = [(0.0, 0.0, 0.0)] * 4
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surfaces = []
    for k in range(variants):
        frames = [(card if f == k else nothing, [(1.0, 0.0, 0.0)] * 4) for f in range(variants)]
        surfaces.append(dict(name=f"splat{k}", shader=f"progs/dookie_wall_v{k}", tris=tris, st=st, frames=frames))

    md3_out = os.path.join(PROGS_DIR, "dookie_wall.md3")
    md3lib.write(md3_out, dict(name="dookie_wall", surfaces=surfaces, nframes=variants))
    for pd in progs_targets[1:]:
        shutil.copy2(md3_out, os.path.join(pd, "dookie_wall.md3"))

    # Update effectinfo.txt between markers
    fx_path = os.path.join(MOD_ROOT, "effectinfo.txt")
    begin, end = b"// ---- Dookie Gun begin", b"// ---- Dookie Gun end"
    raw = open(fx_path, "rb").read()
    if begin in raw and end in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
    add = DOOKIE_EFFECTINFO_BLOCK.encode("ascii").replace(b"\r\n", b"\n").replace(b"\n", b"\r\n").rstrip(b"\r\n") + b"\r\n"
    open(fx_path, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + add)


def export_sounds() -> None:
    print("[4/5] Exporting sound/dookie/*.wav...")
    sound_targets = [SOUND_DOOKIE_DIR]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        sound_targets.append(STAGED_SOUND_DOOKIE_DIR)
    for d in sound_targets:
        os.makedirs(d, exist_ok=True)
    for src_name, dst_name in AUDIO_EXPORTS.items():
        src_p = os.path.join(AUDIO_SRC_DIR, src_name)
        if not os.path.isfile(src_p):
            raise FileNotFoundError(src_p)
        for d in sound_targets:
            shutil.copy2(src_p, os.path.join(d, dst_name))


def save_audit_sheet(all_vm: List[np.ndarray], proj_srgb: List[np.ndarray], splat_srgb: List[np.ndarray], muzzle_yz: Tuple[float, float]) -> str:
    print("[4/4] Writing audit_game_export.png...")
    W, H = 1600, 900
    sheet = Image.new("RGB", (W, H), (22, 26, 30))
    dr = ImageDraw.Draw(sheet)
    dr.text((16, 10), f"DOOKIE BAZOOKA MK-IV DARKPLACES EXPORT AUDIT | v_dookie.md3 (114 skins) | muzzle y={muzzle_yz[0]:.2f} z={muzzle_yz[1]:.2f}", fill=(255, 225, 110))

    def paste_cell(arr: np.ndarray, x: int, y: int, cw: int, ch: int, label: str) -> None:
        pil = Image.fromarray(resize_rgba_premul(arr, cw, ch), "RGBA")
        bg = Image.new("RGBA", (cw, ch), (36, 42, 48, 255))
        sheet.paste(Image.alpha_composite(bg, pil).convert("RGB"), (x, y))
        dr.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(76, 110, 84))
        dr.text((x + 4, y + 4), label, fill=(210, 255, 180))

    vm_picks = [
        (all_vm[0], "VM Idle 0"),
        (all_vm[30], "VM Idle 30"),
        (all_vm[62], "Windup 62"),
        (all_vm[74], "Windup Max 74"),
        (all_vm[80], "Fire 80"),
        (all_vm[88], "Fire 88"),
        (all_vm[100], "Reload 100"),
        (all_vm[112], "Reload 112"),
    ]
    for i, (arr, lb) in enumerate(vm_picks):
        paste_cell(arr, 16 + i * 196, 38, 190, 164, lb)

    proj_picks = [
        (proj_srgb[0 * 8 + 0], "Proj 0deg Front"),
        (proj_srgb[2 * 8 + 2], "Proj 45deg"),
        (proj_srgb[4 * 8 + 2], "Proj 90deg Left"),
        (proj_srgb[8 * 8 + 0], "Proj 180deg Back"),
        (proj_srgb[12 * 8 + 4], "Proj 270deg Right"),
        (proj_srgb[14 * 8 + 6], "Proj 315deg"),
    ]
    for i, (arr, lb) in enumerate(proj_picks):
        paste_cell(arr, 16 + i * 260, 224, 248, 278, lb)

    splat_picks = [
        (splat_srgb[0], "Splat 0"),
        (splat_srgb[2], "Splat 2"),
        (splat_srgb[5], "Splat 5"),
        (splat_srgb[8], "Splat 8"),
        (splat_srgb[11], "Splat 11"),
        (splat_srgb[15], "Splat 15"),
    ]
    for i, (arr, lb) in enumerate(splat_picks):
        paste_cell(arr, 16 + i * 260, 528, 248, 248, lb)

    out_p = os.path.join(MK4_DIR, "audit_game_export.png")
    sheet.save(out_p)
    return out_p


def main() -> None:
    if "--sprites-only" in sys.argv[1:]:
        export_world_sprites()
        print("DONE! World sprites updated.")
        return
    all_vm, muzzle_yz = export_viewmodel()
    proj_srgb, splat_srgb = export_world_sprites()
    export_wall_splats_and_fx()
    export_sounds()
    audit_p = save_audit_sheet(all_vm, proj_srgb, splat_srgb, muzzle_yz)
    print(f"DONE! Audit -> {audit_p}")


if __name__ == "__main__":
    main()
