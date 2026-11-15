"""make_goldenwest.py — Top-level entry point for Golden West Casino & S Union Ave (.map).

Backward-Compatibility Hook:
- When GW_SEG is set in the environment (used by build_bklan4.sh / make_bakolansmall.py),
  delegates transparently to make_goldenwest_legacy.py so existing composite route builds
  remain 100% intact.
- Otherwise delegates directly to the modular goldenwest.make_gw orchestrator (`12 u/ft`,
  zero legacy bklan*/bk_* textures, full enterable interiors & Hull-1 navigation).

Usage: python make_goldenwest.py [out/maps/goldenwest.map] [--fast] [--no-check-textures] [--no-validate]
"""
from __future__ import annotations

import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

if os.environ.get("GW_SEG"):
    runpy.run_path(os.path.join(HERE, "make_goldenwest_legacy.py"), run_name="__main__")
    sys.exit(0)

if HERE not in sys.path:
    sys.path.insert(0, HERE)
_GW_DIR = os.path.join(HERE, "goldenwest")
if _GW_DIR not in sys.path:
    sys.path.insert(0, _GW_DIR)

from goldenwest.make_gw import (  # noqa: E402
    DEFAULT_OUT_MAP,
    assemble_into,
    build_all,
    build_goldenwest,
    build_map,
    main as _gw_main,
)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    # Preserve historical positional default (`out/maps/goldenwest.map`) if caller runs legacy path,
    # or pass explicit CLI args straight through to goldenwest.make_gw.main().
    if not args and "--out-legacy" in os.environ.get("GW_LEGACY_OUT", ""):
        args = [os.path.join(HERE, "out", "maps", "goldenwest.map")]
    if os.environ.get("GW_FAST") and "--fast" not in args:
        args.append("--fast")
    return _gw_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
