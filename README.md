# BakersfieldQuake

A Quake mod layered on Combat+ (quake15) and the **Zircon Engine** (we no longer use DarkPlaces): custom guns (Mega Man gun, NetSend, Mystery Box,
Wheelman Cannon, jetpack and more), Bakersfield maps (`bklan`, `orcom` and others) and a LAN-party deathmatch ruleset.

## Play it

1. Download `BAKOQUAKE.zip` from the **Releases** page of this repo and unzip it.
2. Put the Quake data files into the `id1` folder inside it: `pak0.pak` and `pak1.pak` from your own copy of Quake.
   They are not in the download because they belong to id Software.
3. Run `PLAY BAKERSFIELDQUAKE.exe`. It joins a LAN server if it finds one, otherwise it opens the intro.
   Windows only. In game, F2 joins the LAN game; `Start Server.cmd` hosts one.

## What is in this repo

Text and source only; the built game data is in the release download.

- `source/mm_tools/` - the QuakeC for the guns and game rules (`*.qc`), the Python that builds models, maps and sounds,
  and the per-feature notes.
- `website/` - the project web page.
- top-level `*.cfg`, `quake.rc`, `readme.txt` and the `*_NOTES.md` / `*_PROMPT.md` design documents.

## What is not in this repo

- Built data: `bakersfield.pk3`, `maps/`, `progs/`, `progs.dat`, `csprogs.dat` (about 1 GB; in the release zip).
- Quake's own data files (`id1/pak0.pak`, `pak1.pak`).
- The decompiled Combat+ game code (`source/qc_combat_decomp`). Combat+ belongs to its author, Totalitarian
  (https://www.moddb.com/mods/quake-combat), and is kept for personal use. The QuakeC here is meant to be patched into it
  by `source/mm_tools/patch_megaman_combat.py`.
- Personal settings (`config.cfg`, `personal.cfg`) and the large source art/video folders.

Keep this repository private: the release zip contains Combat+ and Quake 1.5 content that are not ours to redistribute.
