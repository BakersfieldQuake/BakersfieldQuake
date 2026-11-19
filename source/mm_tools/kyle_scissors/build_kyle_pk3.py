"""Build the reproducible BakersfieldQuake overlay package: zz_kyle.pk3.

Never touches bakersfield.pk3 or quake15/q15.pk3!
Packages all Pocket Kyle Fun Gun (Slot 8 / impulse 68) assets cleanly into zz_kyle.pk3:
  - progs/v_kyle.md3                (1-frame flat viewmodel card)
  - progs/v_kyle.md3_0..111.skin    (112 skins @ 24 FPS: 48 idle, 24 lock, 28 fire, 12 draw)
  - progs/kvm_000..111.png          (320x426 RGBA, HDR-toned + edge RGB bled)
  - scripts/kylevm.shader           (per-frame clampmap + rgbGen lightingDiffuse shaders)
  - progs/kyle_proj.spr32           (IDSP v32 SPR_VP_PARALLEL, 416f: 4 custom states x 8 dirs)
      0..127   running_scissors  (8 dirs x 16f @ 24 FPS)
      128..223 overhead_scissors (8 dirs x 12f @ 24 FPS)
      224..319 front_scissors    (8 dirs x 12f @ 24 FPS)
      320..415 no_scissors       (8 dirs x 12f @ 16 FPS)
  - progs/kyle_cash.spr32           (IDSP v32 SPR_VP_PARALLEL, 24f centered US currency)
      0..7     Realistic US $100 bills (8 tumbling/fluttering frames)
      8..15    2024 Washington Silver Quarter (8 spinning 3D frames)
      16..23   2024 Sacagawea Gold Dollar (8 spinning 3D frames)
  - sound/kyle/*.wav                (17 clean 22050 Hz mono PCM WAVs — ZERO 'clients' clips)

Run:
    python source/mm_tools/kyle_scissors/build_kyle_pk3.py
"""

import hashlib
import io
import json
import math
import os
import struct
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE.parent
REPO_ROOT = TOOLS_DIR.parent.parent
sys.path.insert(0, str(TOOLS_DIR))
import md3lib

ARTIFACT_ROOT = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671")
VM_SRC_DIR = ARTIFACT_ROOT / "scratch" / "pocket_kyle_hd"
SPR_SRC_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "sprites"
SFX_SRC_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "sfx"
VOICE_SRC_DIR = ARTIFACT_ROOT / "scratch" / "kyle_clips"
OUT_PK3 = REPO_ROOT / "zz_kyle.pk3"

# Viewmodel card placement (user-tuned via Pocket Kyle POV Tuner on 16:9 FOV 90 viewplane @ VIEW_X = 14)
VIEW_X = 14.0
VIEW_H = 32.24
VIEW_RIGHT = -26.54
VIEW_TOP = 15.64
VIEW_ROLL = 20.0          # clockwise tilt (deg) about (50% W, 72% down from top), matching POV tuner
VM_SIZE = (320, 426)      # 3:4 aspect matching 420x560 source
VM_DIM = 0.64             # balanced for DarkPlaces rgbGen lightingDiffuse + HDR

PROJ_TARGET_H = 160       # 160px -> ~70u tall in world at scale 0.44 (crisp & light VRAM!)
PROJ_DIM = 0.78           # balanced for DarkPlaces SPR32 fullbright/HDR
CASH_DIM = 0.86

SOUND_MAP = {
    # Draw, Sky Throw & Superman Torpedo ("Whoa man!" / "WHOAAA WHOAAAA!!") voices
    "sound/kyle/whoa_man.wav":      VOICE_SRC_DIR / "cut_01_wheres_my_cut.wav",
    "sound/kyle/whoa_1.wav":        VOICE_SRC_DIR / "whoa_01_short.wav",
    "sound/kyle/whoa_2.wav":        VOICE_SRC_DIR / "whoa_02_wobble.wav",
    "sound/kyle/whoa_3.wav":        VOICE_SRC_DIR / "whoa_03_rise.wav",
    "sound/kyle/whoa_4.wav":        VOICE_SRC_DIR / "whoa_04_punch.wav",
    "sound/kyle/whoa_5.wav":        VOICE_SRC_DIR / "whoa_05_long.wav",
    "sound/kyle/whoa_6.wav":        VOICE_SRC_DIR / "whoa_06_double_warble.wav",
    "sound/kyle/whoa_7.wav":        VOICE_SRC_DIR / "whoa_07_triple_rapid.wav",
    "sound/kyle/whoa_8.wav":        VOICE_SRC_DIR / "whoa_08_superman_doppler.wav",
    "sound/kyle/whoa_9.wav":        VOICE_SRC_DIR / "whoa_09_canyon_yell.wav",
    "sound/kyle/whoa_10.wav":       VOICE_SRC_DIR / "whoa_10_whoa_whoaaa_long.wav",
    "sound/kyle/whoa_12.wav":       VOICE_SRC_DIR / "whoa_12_torpedo_cut_cry.wav",
    # Action / Latch / Wander voices (ZERO "Will stole my clients" clips!)
    "sound/kyle/kyle_hey.wav":      VOICE_SRC_DIR / "kyle_02_hey_bright.wav",
    "sound/kyle/kyle_hey2.wav":     VOICE_SRC_DIR / "kyle_03_its_kyle.wav",
    "sound/kyle/kyle_cut.wav":      VOICE_SRC_DIR / "cut_02_give_me_a_cut.wav",
    "sound/kyle/kyle_cut2.wav":     VOICE_SRC_DIR / "edit_02_whoa_give_cut.wav",
    "sound/kyle/kyle_hey_man.wav":  VOICE_SRC_DIR / "edit_01_hey_man_tight.wav",
    # Synthesized Scissor, Lock & Cash SFX
    "sound/kyle/snip_fast.wav":     SFX_SRC_DIR / "snip_fast.wav",
    "sound/kyle/snip_heavy.wav":    SFX_SRC_DIR / "snip_heavy.wav",
    "sound/kyle/lock_tick.wav":     SFX_SRC_DIR / "lock_tick.wav",
    "sound/kyle/lock_ready.wav":    SFX_SRC_DIR / "lock_ready.wav",
    "sound/kyle/cash_register.wav": SFX_SRC_DIR / "cash_register.wav",
    "sound/kyle/cash_flutter.wav":  SFX_SRC_DIR / "cash_flutter.wav",
    "sound/kyle/plane_whoosh.wav":  SFX_SRC_DIR / "plane_whoosh.wav",
    "sound/kyle/scissor_clang1.wav": SFX_SRC_DIR / "scissor_clang1.wav",
    "sound/kyle/scissor_clang2.wav": SFX_SRC_DIR / "scissor_clang2.wav",
    "sound/kyle/scissor_clang3.wav": SFX_SRC_DIR / "scissor_clang3.wav",
}

MODEL_SRC_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "models"


def resize_premul(rgba: np.ndarray, wh: Tuple[int, int]) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    pm = np.empty(rgba.shape, dtype=np.float32)
    pm[..., :3] = rgba[..., :3].astype(np.float32) * a
    pm[..., 3:4] = a
    pm_s = cv2.resize(pm, wh, interpolation=cv2.INTER_AREA)
    a_s = np.clip(pm_s[..., 3:4], 0.0, 1.0)
    rgb = np.where(a_s > 1e-4, pm_s[..., :3] / np.maximum(a_s, 1e-4), 0.0)
    out = np.empty((wh[1], wh[0], 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a_s[..., 0] * 255.0), 0, 255).astype(np.uint8)
    return out


def bleed_rgb_edges(rgba: np.ndarray, passes: int = 4) -> np.ndarray:
    """Propagate foreground RGB into alpha==0 neighbors (pure numpy/cv2, zero scipy)
    so DarkPlaces bilinear filtering never produces dark or white halos."""
    out = rgba.copy()
    mask = out[..., 3] >= 24
    if not np.any(mask):
        return out
    rgb = out[..., :3].astype(np.float32)
    valid = mask.astype(np.float32)
    k = np.ones((3, 3), np.float32)
    for _ in range(passes):
        w_sum = cv2.filter2D(valid, -1, k, borderType=cv2.BORDER_REPLICATE)
        need = (valid < 0.5) & (w_sum > 0.5)
        if not np.any(need):
            break
        for c in range(3):
            c_sum = cv2.filter2D(rgb[..., c] * valid, -1, k, borderType=cv2.BORDER_REPLICATE)
            rgb[..., c][need] = c_sum[need] / w_sum[need]
        valid[need] = 1.0
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    return out


def tone_rgba(rgba: np.ndarray, dim: float) -> np.ndarray:
    out = rgba.copy()
    out[..., :3] = np.clip(np.round(out[..., :3].astype(np.float32) * dim), 0, 255).astype(np.uint8)
    return out


def encode_png(rgba: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG", compress_level=6, optimize=False)
    return buf.getvalue()


def build_md3_card_bytes(aspect: float) -> bytes:
    vh = VIEW_H
    vw = vh * aspect
    dy = VIEW_RIGHT + vw / 2.0
    dz = VIEW_TOP - vh / 2.0
    hw, hh = vw / 2.0, vh / 2.0
    # Pivot at (50% W, 72% down from top) matching the HTML POV tuner canvas transform
    py = VIEW_RIGHT + vw * 0.5
    pz = VIEW_TOP - vh * 0.72
    rad = math.radians(VIEW_ROLL)
    cr, sr = math.cos(rad), math.sin(rad)

    raw_card = [
        (dy + hw, dz - hh),
        (dy + hw, dz + hh),
        (dy - hw, dz + hh),
        (dy - hw, dz - hh),
    ]
    card = []
    for y, z in raw_card:
        sx = -(y - py)   # +right on screen
        sy = -(z - pz)   # +down on screen
        sx_r = sx * cr - sy * sr
        sy_r = sx * sr + sy * cr
        card.append((VIEW_X, py - sx_r, pz - sy_r))
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surf = dict(
        name="card",
        shader="progs/kvm_000",
        tris=tris,
        st=st,
        frames=[(card, [(-1.0, 0.0, 0.0)] * 4)],
    )
    tmp_path = ARTIFACT_ROOT / "scratch" / "_tmp_v_kyle.md3"
    md3lib.write(str(tmp_path), dict(name="v_kyle", surfaces=[surf], nframes=1))
    data = tmp_path.read_bytes()
    tmp_path.unlink(missing_ok=True)
    return data


def pack_spr32_bytes(frames_rgba: List[np.ndarray], center_origin: bool = False,
                     ground_pad_bottom: int = 4) -> bytes:
    """Write a DarkPlaces IDSP v32 SPR_VP_PARALLEL (.spr32) binary in memory."""
    packed = []
    for arr in frames_rgba:
        h, w = arr.shape[:2]
        ys, xs = np.nonzero(arr[..., 3] >= 12)
        if len(xs) == 0:
            crop = np.zeros((4, 4, 4), dtype=np.uint8)
            packed.append((-2, 2, 4, 4, crop.tobytes()))
            continue
        x0 = max(0, int(xs.min()) - 2)
        x1 = min(w, int(xs.max()) + 3)
        y0 = max(0, int(ys.min()) - 2)
        y1 = min(h, int(ys.max()) + 3)
        crop = bleed_rgb_edges(arr[y0:y1, x0:x1], passes=3)
        cw, ch = crop.shape[1], crop.shape[0]
        if center_origin:
            ox, oy = -(cw // 2), ch // 2
        else:
            # Anchor horizontally around original image center, vertically so feet sit at Z = 0!
            ox = x0 - (w // 2)
            oy = (h - ground_pad_bottom) - y0
        packed.append((ox, oy, cw, ch, crop.tobytes()))

    max_cw = max(f[2] for f in packed)
    max_ch = max(f[3] for f in packed)
    rad = 0.5 * math.hypot(max_cw, max_ch)
    buf = bytearray(
        b"IDSP" + struct.pack("<iifiiifi", 32, 2, rad, max_cw, max_ch, len(packed), 0.0, 0)
    )
    for ox, oy, cw, ch, fb in packed:
        buf += struct.pack("<iiiii", 0, ox, oy, cw, ch)
        buf += fb
    return bytes(buf)


def build_pk3(out_path: Path) -> str:
    files: Dict[str, bytes] = {}

    # 1. Viewmodel (150 frames @ 24 FPS = every 2nd frame of 300 @ 48 FPS)
    with open(VM_SRC_DIR / "manifest.json", "r", encoding="utf-8") as fh:
        vm_m = json.load(fh)

    vm_list = (
        vm_m["idle"][::2]      # 48 frames (skins   0..47)
        + vm_m["lock"][::2]    # 24 frames (skins  48..71 — ground windup)
        + vm_m["birdlock"][::2]# 24 frames (skins  72..95 — BRAND-NEW Superman anti-air bird lock-on!)
        + vm_m["fire"][::2]    # 42 frames (skins  96..137 — BRAND-NEW 8-stage physical throwing hand!)
        + vm_m["draw"][::2]    # 12 frames (skins 138..149)
    )
    assert len(vm_list) == 150, f"Expected 150 viewmodel frames, got {len(vm_list)}"

    shader_lines = ["// generated by source/mm_tools/kyle_scissors/build_kyle_pk3.py\n"]
    for idx, fname in enumerate(vm_list):
        raw = np.asarray(Image.open(VM_SRC_DIR / fname).convert("RGBA"))
        rsz = resize_premul(raw, VM_SIZE)
        toned = bleed_rgb_edges(tone_rgba(rsz, VM_DIM), passes=4)
        sh_name = f"progs/kvm_{idx:03d}"
        files[f"{sh_name}.png"] = encode_png(toned)
        files[f"progs/v_kyle.md3_{idx}.skin"] = f"card,{sh_name}\n".encode("ascii")
        shader_lines.append(
            f"{sh_name}\n{{\n\tcull none\n\tnomipmaps\n\t{{\n"
            f"\t\tclampmap {sh_name}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    # Add 3D bouncing chrome scissors + 3D spinning Superman-Torpedo Kyle shaders & models
    shader_lines.append(
        "progs/kyle_scissors\n{\n\tcull none\n\t{\n\t\tmap progs/kyle_scissors.png\n\t\trgbGen lightingDiffuse\n\t}\n}\n"
    )
    for tname, cull_line in (
        ("kyle_torp_belly", ""),
        ("kyle_torp_back", ""),
        ("kyle_torp_side", "\tcull none\n"),
    ):
        shader_lines.append(
            f"progs/{tname}\n{{\n{cull_line}\tnomipmaps\n\t{{\n"
            f"\t\tclampmap progs/{tname}.png\n\t\talphaFunc GE128\n\t\tdepthWrite\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    files["scripts/kylevm.shader"] = "".join(shader_lines).encode("ascii")
    files["progs/v_kyle.md3"] = build_md3_card_bytes(VM_SIZE[0] / float(VM_SIZE[1]))
    files["progs/kyle_scissors.md3"] = (MODEL_SRC_DIR / "kyle_scissors.md3").read_bytes()
    files["progs/kyle_scissors.png"] = (MODEL_SRC_DIR / "kyle_scissors.png").read_bytes()
    files["progs/kyle_torpedo.md3"] = (MODEL_SRC_DIR / "kyle_torpedo.md3").read_bytes()
    for tname in ("kyle_torp_belly", "kyle_torp_back", "kyle_torp_side"):
        files[f"progs/{tname}.png"] = (MODEL_SRC_DIR / f"{tname}.png").read_bytes()

    # 2. Projectile 4-State x 8-Dir + From-Below (8f) + From-Above (8f) SPR32 (272 frames)
    with open(SPR_SRC_DIR / "manifest.json", "r", encoding="utf-8") as fh:
        sp_m = json.load(fh)

    proj_frames: List[np.ndarray] = []
    for st_key in ("running_scissors", "overhead_scissors", "front_scissors", "no_scissors"):
        st = sp_m["states"][st_key]
        for d in range(8):
            for rel in st["directions"][str(d)]:
                raw = np.asarray(Image.open(SPR_SRC_DIR / rel).convert("RGBA"))
                h, w = raw.shape[:2]
                new_w = max(8, int(round(w * (PROJ_TARGET_H / float(h)))))
                rsz = resize_premul(raw, (new_w, PROJ_TARGET_H))
                proj_frames.append(tone_rgba(rsz, PROJ_DIM))
    for st_key in ("from_below", "from_above"):
        st = sp_m["states"][st_key]
        for rel in st["directions"]["0"]:
            raw = np.asarray(Image.open(SPR_SRC_DIR / rel).convert("RGBA"))
            h, w = raw.shape[:2]
            new_w = max(8, int(round(w * (PROJ_TARGET_H / float(h)))))
            rsz = resize_premul(raw, (new_w, PROJ_TARGET_H))
            proj_frames.append(tone_rgba(rsz, PROJ_DIM))
    assert len(proj_frames) == 272, f"Expected 272 proj frames (256 + 8 below + 8 above), got {len(proj_frames)}"
    files["progs/kyle_proj.spr32"] = pack_spr32_bytes(proj_frames, center_origin=False, ground_pad_bottom=4)

    # 3. Realistic US Currency SPR32 (24 frames: 8 bills + 8 quarters + 8 gold dollars)
    cash_frames: List[np.ndarray] = []
    for rel in sp_m["cash_fx"]["bills"]:
        raw = np.asarray(Image.open(SPR_SRC_DIR / rel).convert("RGBA"))
        cash_frames.append(tone_rgba(resize_premul(raw, (96, 54)), CASH_DIM))
    for rel in sp_m["cash_fx"]["quarters"]:
        raw = np.asarray(Image.open(SPR_SRC_DIR / rel).convert("RGBA"))
        cash_frames.append(tone_rgba(resize_premul(raw, (64, 64)), CASH_DIM))
    for rel in sp_m["cash_fx"]["gold_dollars"]:
        raw = np.asarray(Image.open(SPR_SRC_DIR / rel).convert("RGBA"))
        cash_frames.append(tone_rgba(resize_premul(raw, (64, 64)), CASH_DIM))
    assert len(cash_frames) == 24
    files["progs/kyle_cash.spr32"] = pack_spr32_bytes(cash_frames, center_origin=True)

    # 4. Sounds (ZERO 'clients' clips!)
    for arc, src_p in SOUND_MAP.items():
        assert src_p.exists(), f"Missing sound: {src_p}"
        assert "clients" not in arc.lower() and "clients" not in src_p.name.lower()
        files[arc] = src_p.read_bytes()

    # 5. Write deterministic reproducible PK3 (sorted entries, fixed 1980-01-01 timestamp & attrs)
    with zipfile.ZipFile(out_path, "w") as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            ext = os.path.splitext(name)[1].lower()
            if ext in (".png", ".jpg", ".ogg"):
                info.compress_type = zipfile.ZIP_STORED
                zf.writestr(info, files[name])
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, files[name], compresslevel=6)

    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    mb = out_path.stat().st_size / (1024 * 1024)
    print(f"Built {out_path} ({len(files)} entries, {mb:.2f} MB, sha256={sha[:16]}...)")
    return sha


def main():
    sha1 = build_pk3(OUT_PK3)
    # Verify byte-identical reproducibility per AGENTS.md!
    tmp_check = ARTIFACT_ROOT / "scratch" / "_zz_kyle_repro_check.pk3"
    sha2 = build_pk3(tmp_check)
    tmp_check.unlink(missing_ok=True)
    assert sha1 == sha2, f"Reproducibility check FAILED: {sha1} != {sha2}"
    print(f"Reproducibility PASSED: byte-identical sha256 = {sha1}")


if __name__ == "__main__":
    main()
