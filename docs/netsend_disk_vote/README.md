# THE DISK: the NetSend gun's new held model (vote, 2026-11-26)

The NetSend gun's 3D hand with the black `LOL.BAT` floppy is replaced by a sprite built from seven Grok videos
(a black-gloved hand and a blue floppy labelled **THE DISK**), the same way the Milky Gun's hand is made: one card MD3
whose skin picks the frame every tick. Three animation sets were built for a vote.

- Vote page: https://bakersfield.larrywew.fun/netsend_disk_vote.html (self-contained; also sent to the BAKOQUAKE
  Telegram group as a file).
- Votes: `GET/POST https://bakersfield.larrywew.fun/api/netsend-disk-vote` (`netsend-disk-vote.service` on the VPS,
  `/opt/netsend-disk-vote/votes.json`; every vote is also posted to the Telegram group).
- In-game check: `ingame_test.jpg` (set A, map `start`): rest hold, coil, whip release, the disk in flight, the PC.

## Sets

| Set | Tricks | Throw (release after fire) |
|---|---|---|
| A Frisbee Pro | Flip & Aim (v1), Edge Sight (v0) | Sidearm Frisbee (v5), 0.37 s |
| B Trickster | Twirl & Rub, Grip Roll (v2), Fingertip Spin (v3) | Finger Flick (v3), 0.30 s |
| C Showboat | Whoosh (v4), Close Look, Read the Label (v3), Show Off (v6) | Palm Pop (v4), 0.40 s |

All sets share the rest hold (v5 f0-27) and one crop, so any set ships with the same card and screen position.

**Winner: A Frisbee Pro** (picked 2026-11-26). `source/mm_tools/netsend_diskvm.qc` is generated for set A, and
`zz_netsend_disk.pk3` for set A is sha256 `e557aa2b2488481fb753296f8ca13124d873d0a0ceb65ccf2b1d7f77b745712d`
(482 files, 12.6 MB).

## Rebuild / switch to the winning set

Videos default to `/home/computer/Desktop/Media/images/quakeassets/` (`--videos` to change). Outputs go to
`build/netsend_disk/` (gitignored).

```sh
python3 source/mm_tools/build_netsend_disk_view.py            # key + build all three sets (about 5 min)
python3 source/mm_tools/build_netsend_disk_view.py --skip-build --game-set B   # game files + netsend_diskvm.qc for set B
python3 source/mm_tools/build_netsend_disk_proj.py            # the projectile (netsend_disk.md3/.png)
python3 source/mm_tools/build_netsend_disk_pk3.py             # build/netsend_disk/zz_netsend_disk.pk3 (reproducible)
python3 source/mm_tools/build_netsend_disk_vote_html.py       # the vote page
```

`--game-set` rewrites `source/mm_tools/netsend_diskvm.qc` (frame map + `NS_THROW_DELAY`); copy it into
`qc_combat_decomp` (build_combat.py does) and recompile.

## Code

- `netsend.qc`: `NS_DiskViewFrame` (throw, drop-away, empty, raise, tricks, rest; `ns_vm_tricks 0` turns tricks off),
  the disk leaves from the hand's side (`NS_Throw`).
- `pickle.qc`: `Pickle_ViewFrame` calls it (viewmodel and quad overlay). `funguns.qc`: NetSend is frame 0 of the card.
- `bm_reload.qc`: the LAN magazine reload waits for the throw and drop-away (it hid the throw before).
- Tools: `disk_keyer.py` (keying), `disk_anim.py` (flow in-betweens, settle morphs, smears, whips).

## Shipping

The videos are not in the repo, so CI does not build this pk3. It is built here and pinned: the release workflow
(`Fetch zz_netsend_disk.pk3` in `build-zip.yml`) downloads
`https://bakersfield.larrywew.fun/pk3/zz_netsend_disk-<first 8 of sha256>.pk3` (VPS: `/var/www/megaman/pk3/`) and
checks its sha256. To ship a new build:

1. Rebuild (commands above), then upload `build/netsend_disk/zz_netsend_disk.pk3` under its new hashed name.
   Never overwrite an old one: older commits still pin it.
2. Update the URL and sha256 in that step, and the frame names in the "Check the package" list if the frame count
   changed.
3. Commit the regenerated `netsend_diskvm.qc` (both copies) in the same change, so the QC frame map matches the pk3.
