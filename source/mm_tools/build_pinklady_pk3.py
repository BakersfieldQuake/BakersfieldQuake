"""Builds zz_pinklady.pk3: tones down the over-bright Pink Lady projectile textures.

    python -I source/mm_tools/build_pinklady_pk3.py <path to bakersfield.pk3> [output pk3]

Why: in bakersfield.pk3, scripts/pinklady.shader renders progs/pinklady_*.png with
"rgbGen identity" (unlit 1.0x), while Zircon runs r_hdr_scenebrightness 1.45,
v_gamma 1.3125, v_contrast 1.125 and r_bloom 1. build_pinklady_assets.py originally
lifted those textures with pow(x, 0.82) * 1.12, pushing skin/hair to ~221/255 and
half the pink top to 255, so the projectile blows out washed-out white in game.
Other "rgbGen identity" sprites (such as progs/jesskart_f00.png and progs/pthr_00.png)
keep diffuse values around 0.45x (p95 ~ 105-120).

What it does: reads the 138 Pink Lady frame PNGs referenced by scripts/pinklady.shader
out of bakersfield.pk3, undoes the washout gamma lift, restores saturation and scales
into the calibrated ~0.45x unlit sprite range, and writes BakersfieldQuake/zz_pinklady.pk3.

Reproducible: depends only on pinned numpy and pillow; entries are sorted, dated
1980-01-01, with fixed attributes, and stored (PNGs are already compressed).
"""
import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

SHADER_PATH = "scripts/pinklady.shader"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
FILE_ATTR = 0o100644 << 16

GAMMA = 1.22
DIM = 0.45
SAT_BOOST = 1.06


def regrade_pinklady_rgba(
    rgba: np.ndarray,
    gamma: float = GAMMA,
    dim: float = DIM,
    sat_boost: float = SAT_BOOST,
) -> np.ndarray:
    """Tone a bright Pink Lady RGBA frame down for rgbGen identity + Zircon HDR/gamma."""
    f = rgba.astype(np.float32)
    rgb = np.power(np.clip(f[..., :3] / 255.0, 0.0, 1.0), gamma)
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[..., None]
    rgb = lum + (rgb - lum) * sat_boost
    rgb = np.clip(rgb * dim, 0.0, 1.0)

    alpha = rgba[..., 3]
    rgb_u8 = np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)
    rgb_u8[alpha < 4] = 0
    return np.dstack([rgb_u8, alpha])


def shader_frame_paths(shader_text: str) -> list[str]:
    """Return sorted unique progs/pinklady_*.png paths referenced by animmap in pinklady.shader."""
    refs: set[str] = set()
    for line in shader_text.splitlines():
        m = re.match(r"^\s*animmap\s+\S+\s+(.+)$", line)
        if m:
            for tok in m.group(1).split():
                if not tok.startswith("progs/pinklady_"):
                    raise ValueError(f"Unexpected texture token in {SHADER_PATH}: {tok}")
                refs.add(f"{tok}.png")
    if len(refs) != 138:
        raise ValueError(f"Expected 138 frames in {SHADER_PATH}, found {len(refs)}")
    return sorted(refs)


def write_pk3(out_path: Path, entries: dict[str, bytes]) -> None:
    """Write a deterministic pk3 with sorted ZIP_STORED PNG entries."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pk3.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w") as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.create_system = 3
            info.external_attr = FILE_ATTR
            zf.writestr(info, entries[name], compress_type=zipfile.ZIP_STORED)
    tmp.replace(out_path)


def build_zz_pinklady(base_pk3: Path, out_pk3: Path) -> Path:
    """Build zz_pinklady.pk3 from bakersfield.pk3."""
    if not base_pk3.is_file():
        raise FileNotFoundError(f"bakersfield.pk3 not found: {base_pk3}")

    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(base_pk3) as zf:
        shader_text = zf.read(SHADER_PATH).decode("latin-1")
        frame_paths = shader_frame_paths(shader_text)
        for path in frame_paths:
            with Image.open(io.BytesIO(zf.read(path))) as im:
                arr = np.asarray(im.convert("RGBA"))
            toned = regrade_pinklady_rgba(arr)
            buf = io.BytesIO()
            Image.fromarray(toned, "RGBA").save(buf, format="PNG", optimize=True)
            entries[path] = buf.getvalue()

    write_pk3(out_pk3, entries)
    return out_pk3


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base_pk3", type=Path)
    ap.add_argument("out_pk3", type=Path, nargs="?")
    args = ap.parse_args(argv)
    out_pk3 = args.out_pk3 or args.base_pk3.with_name("zz_pinklady.pk3")
    if not args.base_pk3.is_file():
        sys.exit(f"missing base pk3: {args.base_pk3}")
    build_zz_pinklady(args.base_pk3, out_pk3)
    print(f"wrote {out_pk3} ({out_pk3.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
