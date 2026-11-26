"""Reproducible builder for zz_netsend_sentry.pk3 (Classic Retro Style Disc Sentry Gun).

Generates all assets directly from source (zero committed binary blobs):
  - progs/netsend_sentry_base.md3    (16-frame folding tripod base)
  - progs/netsend_sentry_turret.md3  (24-frame Classic Retro workstation turret + speaker cannons + CRT)
  - progs/netsend_sentry_turret.md3_0..4.skin (CRT states: active, off, static, fire, fatal)
  - progs/netsend_sentry_floppy.md3  (8-frame custom 3D BOOT_95.DSK 3.5" floppy projectile & throw disk)
  - progs/netsend_sentry_gib0..2.md3 (CRT housing, 486 tower, and speaker-cannon barrel gibs)
  - progs/ds_classic_body.png, progs/ds_classic_floppy.png, progs/ds_leds.png
  - progs/ds_classic_scr_{off,static,active,fire,fatal}.png
  - scripts/netsend_sentry.shader    (LF newlines)
  - sound/netsend/sentry_deploy.wav, sentry_spot.wav, sentry_fire.wav, sentry_explode.wav, floppy_bounce.wav

Usage:
  python -I source/mm_tools/disc_sentry/build_netsend_sentry_pk3.py [--out PATH] [--verify-repro]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import struct
import sys
import tempfile
import wave
import zipfile
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
REPO_ROOT = MM_TOOLS.parent.parent

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import md3lib  # noqa: E402
from disc_sentry import build_models, build_sounds, textures  # noqa: E402

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16
STORE_EXTS = {".png", ".jpg", ".jpeg", ".ogg"}

CONCEPT_ID = "classic"
MODEL_PREFIX = "netsend_sentry"

SKIN_SCREENS = (
    (0, "active"),
    (1, "off"),
    (2, "static"),
    (3, "fire"),
    (4, "fatal"),
)

SHADER_TEXT = """\
progs/ds_classic_body
{
\tcull none
\t{
\t\tmap progs/ds_classic_body.png
\t\trgbGen lightingDiffuse
\t}
}

progs/ds_classic_floppy
{
\tcull none
\t{
\t\tmap progs/ds_classic_floppy.png
\t\trgbGen lightingDiffuse
\t}
}

progs/ds_leds
{
\tcull none
\t{
\t\tmap progs/ds_leds.png
\t\trgbGen identity
\t}
}

progs/ds_classic_scr_off
{
\tcull none
\t{
\t\tmap progs/ds_classic_scr_off.png
\t\trgbGen identity
\t}
}

progs/ds_classic_scr_static
{
\tcull none
\t{
\t\tmap progs/ds_classic_scr_static.png
\t\trgbGen identity
\t}
}

progs/ds_classic_scr_active
{
\tcull none
\t{
\t\tmap progs/ds_classic_scr_active.png
\t\trgbGen identity
\t}
}

progs/ds_classic_scr_fire
{
\tcull none
\t{
\t\tmap progs/ds_classic_scr_fire.png
\t\trgbGen identity
\t}
}

progs/ds_classic_scr_fatal
{
\tcull none
\t{
\t\tmap progs/ds_classic_scr_fatal.png
\t\trgbGen identity
\t}
}
"""


def _png_bytes(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=False, compress_level=6)
    return buf.getvalue()


def _wav_bytes(samples: np.ndarray, sr: int = build_sounds.SR) -> bytes:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _md3_bytes(spec: dict, md3_name: str) -> bytes:
    clean = dict(spec)
    clean["name"] = md3_name
    clean.pop("muzzle_pts", None)
    with tempfile.NamedTemporaryFile(suffix=".md3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        md3lib.write(tmp_path, clean)
        return Path(tmp_path).read_bytes()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _check_md3(raw: bytes, label: str, expected_surfs: list[str] | None = None) -> None:
    ident, ver = struct.unpack_from("<4si", raw, 0)
    if ident != b"IDP3" or ver != 15:
        raise ValueError(f"{label}: bad MD3 header {ident!r} v{ver}")
    nframes, _, nsurfs, _, _, _, ofs_surfs, ofs_eof = struct.unpack_from("<8i", raw, 76)
    if nframes < 1 or nsurfs < 1 or ofs_eof != len(raw):
        raise ValueError(f"{label}: invalid MD3 layout nframes={nframes} nsurfs={nsurfs} ofs_eof={ofs_eof}")
    names: list[str] = []
    cur = ofs_surfs
    for _ in range(nsurfs):
        if raw[cur : cur + 4] != b"IDP3":
            raise ValueError(f"{label}: corrupt surface header")
        s_name = raw[cur + 4 : cur + 68].split(b"\x00", 1)[0].decode("ascii")
        ofs_end = struct.unpack_from("<i", raw, cur + 104)[0]
        names.append(s_name)
        cur += ofs_end
    if expected_surfs is not None and names != expected_surfs:
        raise ValueError(f"{label}: surfaces={names!r}, expected {expected_surfs!r}")


def collect_entries() -> Dict[str, bytes]:
    """Build every MD3, texture, skin, shader, and WAV deterministically in memory."""
    prev_font_mode = textures._USE_BUILTIN_FONT
    textures._USE_BUILTIN_FONT = True
    try:
        entries: Dict[str, bytes] = {}

        # 1. MD3 models for Concept #2 (Classic Retro Style)
        base_spec = build_models.build_base_md3(CONCEPT_ID)
        turret_spec = build_models._build_turret_geometry(CONCEPT_ID)
        floppy_spec = build_models.build_floppy_md3(CONCEPT_ID)
        gib_specs = build_models.build_gib_md3s(CONCEPT_ID)

        entries[f"progs/{MODEL_PREFIX}_base.md3"] = _md3_bytes(base_spec, f"{MODEL_PREFIX}_base")
        entries[f"progs/{MODEL_PREFIX}_turret.md3"] = _md3_bytes(turret_spec, f"{MODEL_PREFIX}_turret")
        entries[f"progs/{MODEL_PREFIX}_floppy.md3"] = _md3_bytes(floppy_spec, f"{MODEL_PREFIX}_floppy")
        for gi, gspec in enumerate(gib_specs):
            entries[f"progs/{MODEL_PREFIX}_gib{gi}.md3"] = _md3_bytes(gspec, f"{MODEL_PREFIX}_gib{gi}")

        _check_md3(entries[f"progs/{MODEL_PREFIX}_base.md3"], "base", ["base_body"])
        _check_md3(
            entries[f"progs/{MODEL_PREFIX}_turret.md3"],
            "turret",
            ["turret_body", "turret_leds", "crt_screen"],
        )
        _check_md3(entries[f"progs/{MODEL_PREFIX}_floppy.md3"], "floppy", ["floppy_disk"])
        for gi in range(3):
            _check_md3(entries[f"progs/{MODEL_PREFIX}_gib{gi}.md3"], f"gib{gi}", [f"gib_{gi}"])

        # 2. Turret .skin files switching CRT states cleanly
        for skin_idx, state in SKIN_SCREENS:
            skin_text = (
                f"turret_body,progs/ds_{CONCEPT_ID}_body\n"
                f"turret_leds,progs/ds_leds\n"
                f"crt_screen,progs/ds_{CONCEPT_ID}_scr_{state}\n"
            )
            entries[f"progs/{MODEL_PREFIX}_turret.md3_{skin_idx}.skin"] = skin_text.encode("ascii")

        # 3. Deterministic PNG textures (built-in FreeType font via Pillow 13.0.0)
        with tempfile.TemporaryDirectory() as td:
            p_body = textures.build_concept_body_texture(CONCEPT_ID, td)
            p_flop = textures.build_floppy_texture(CONCEPT_ID, td)
            p_leds = textures.build_leds_texture(td)
            scr_paths = textures.build_crt_screens_for_concept(CONCEPT_ID, td)

            entries[f"progs/ds_{CONCEPT_ID}_body.png"] = Path(p_body).read_bytes()
            entries[f"progs/ds_{CONCEPT_ID}_floppy.png"] = Path(p_flop).read_bytes()
            entries["progs/ds_leds.png"] = Path(p_leds).read_bytes()
            for _, state in SKIN_SCREENS:
                entries[f"progs/ds_{CONCEPT_ID}_scr_{state}.png"] = Path(scr_paths[state]).read_bytes()

        # 4. Shader script (LF newlines)
        if "\r" in SHADER_TEXT:
            raise ValueError("Shader script must use LF newlines")
        entries["scripts/netsend_sentry.shader"] = SHADER_TEXT.encode("ascii")

        # 5. Scary 22050Hz mono PCM SFX
        entries["sound/netsend/sentry_deploy.wav"] = _wav_bytes(build_sounds.synth_activate_deploy())
        entries["sound/netsend/sentry_spot.wav"] = _wav_bytes(build_sounds.synth_spot_klaxon())
        entries["sound/netsend/sentry_fire.wav"] = _wav_bytes(build_sounds.synth_fire_heavy())
        entries["sound/netsend/sentry_explode.wav"] = _wav_bytes(build_sounds.synth_explode_mega())
        entries["sound/netsend/floppy_bounce.wav"] = _wav_bytes(build_sounds.synth_floppy_clatter(seed=91))

        return entries
    finally:
        textures._USE_BUILTIN_FONT = prev_font_mode


def build_pk3_bytes(entries: Dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for arcname in sorted(entries):
            ext = Path(arcname).suffix.lower()
            comp = zipfile.ZIP_STORED if ext in STORE_EXTS else zipfile.ZIP_DEFLATED
            zi = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            zi.external_attr = FILE_ATTR
            zi.create_system = 3
            if comp == zipfile.ZIP_DEFLATED:
                zf.writestr(zi, entries[arcname], compress_type=comp, compresslevel=6)
            else:
                zf.writestr(zi, entries[arcname], compress_type=comp)
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build reproducible zz_netsend_sentry.pk3")
    parser.add_argument(
        "--out",
        default=str(MM_TOOLS / "out" / "disc_sentry" / "zz_netsend_sentry.pk3"),
        help="Destination .pk3 path",
    )
    parser.add_argument(
        "--verify-repro",
        action="store_true",
        help="Build twice and assert identical SHA-256",
    )
    args = parser.parse_args()

    entries1 = collect_entries()
    blob1 = build_pk3_bytes(entries1)
    h1 = hashlib.sha256(blob1).hexdigest()

    if args.verify_repro:
        entries2 = collect_entries()
        blob2 = build_pk3_bytes(entries2)
        h2 = hashlib.sha256(blob2).hexdigest()
        if h1 != h2 or blob1 != blob2:
            raise RuntimeError(f"Reproducibility check failed: {h1} != {h2}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(blob1)
    print(f"[zz_netsend_sentry] wrote {out_path} ({len(blob1):,} bytes, {len(entries1)} files, sha256={h1[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
