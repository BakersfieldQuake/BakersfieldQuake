# bakolansmall

Golden West Casino and the B-LAN warehouse block on one short stretch of S Union Ave. A deathmatch map for 4-5 players.
Install: `maps/bakolansmall.bsp` + `.lit`. Build: `sh source/mm_tools/build_bakolansmall.sh` (about 2 min; `BKS_REUSE=1` skips re-running the two source generators).
Play: `+deathmatch 1 +map bakolansmall`.

## Size
About 800 ft wide x 1550 ft long (x -140..655, y -250..1300 in the map's own feet), well inside +-32768 units (the origin is moved to the middle,
so the largest coordinate is about 9300 units). Running speed is about 27 ft/s, so the length is roughly a minute of running, not ten.
The **sky box is 2500 ft tall** (30000 units, the most the compiler allows): flying up with the jetpack or the sky pads never reaches a ceiling
(tested up to 900 ft; the clip lid sits at 2494 ft).

## Layout (north is up, 1 char = about 25 ft)
```
                    ORCOM lot            Union Ave                 B-LAN block (E 21st St)
 y 1300   .  .  .  .  .  .  .  .  | ||  |  ===========================================
                                   | ||  |  E 21st St   [J Appl.][118/120 + Larry's][LAN lot][130A LAN hall][Sacramento St]
 y 1000   [ORCOM hall] <--TP-->    | ||  |  <--------------------------------------------- (E 21st: x 268..655)
          (kitchen, tables)        | ||  |   [#105 red shop + 121 E 21st yard]
 y  800                            | ||  |
          PLAZA (west):            | ||  |   PLAZA (east): low walls, hedges, palms, cars
          cover walls, planters,   | ||  |
          palms, cars              | ||  |
 y  500                            | ||  |   [Bakersfield Sign (arch)]   <-- jump pad up to the sign
                                   | ||  |   [tall office]
 y  400   ---------------------+   | ||  |   [Buck Owens' Crystal Palace + lot]
          Golden West north lot|   | ||  |
          [high-limit room+bar]|   | ||  |
 y  100   [card room][turret]  |wall|| ||  |
          [lobby + cage]       |gate|| ||  |        (east side is a plain wall here: the street only)
 y    0   pylon sign           +----+| ||  |
          south parking lot (cars)    | ||  |
 y -250   ------------------------------------
          x -140 .......... 150 | 150..268 Union Ave | 268 ............ 655
                                  3 lanes + brick median with palms + 3 lanes
```
Union Ave (x 150..268, y -245..1295): three lanes each way, red-brick median with palms, hedges and cobra-head lamps, signals at the E 21st
crossing, abandoned cars for cover. It is the open area; the interiors (casino rooms, 118/120 units, the LAN hall, the ORCOM hall) are the close quarters.

## What came from where (nothing was redrawn)
`make_bakolansmall.py` runs `make_goldenwest.py` (`GW_FAST=1`, no OSM street) and `make_bklan.py` (`BKLAN_V3=1`) into `out/bks/`, reads their `.map`
back (`bks_mapio.py`), cuts four windows out, moves them (planes **and** texture offsets) and adds its own ground, sky, hull, street, plaza and gameplay.

| piece | source window (source feet) | moved by | what is in it |
|---|---|---|---|
| casino | goldenwest x -135..156, y -175..410 | none | parcel, stone wall + iron fence + gate pillars, pylon sign, turret, card room, lobby with cage, high-limit room and bar, portico + bronze horse, parked cars, palms |
| blan | bklan2 x -332..41, y -190..262 | +607, +983 | 118/120 E 21st (battery shop, seven roll-up units), Larry's Warehouse signs, the LAN lot, 130A LAN hall, Celebrity Bodyworks, J Appliances, #105 Performance Driveline + 121 E 21st yard, Sacramento St, BODY SHOP yard, v3 jump pads and roof items |
| sign | bklan2 x 745..1060, y -300..175 | -465, +450 | Bakersfield Sign arch, Buck Owens' Crystal Palace, the tall office |
| orcom | bklan2 x 336..462, y 282..352 | -308, +670 | ORCOM CONNECT LAN PARTY hall (kitchen, banquet tables, BAWLS banner) |

A brush counts as inside a window only if all of it is inside, so long road slabs, hull floors and sky walls of the source maps drop out and are replaced.
The source maps' own spawns, items and teleport hubs are dropped (placed again below); lights, models and the v3 jump-pad brushes inside the windows stay.

## Gameplay
- **10 `info_player_deathmatch`** (+1 `info_player_start` on Union Ave): casino card room, casino lobby, casino south lot, Union Ave south, Union Ave middle,
  LAN lot (in front of 130A), LAN lot (centre), E 21st St, ORCOM hall, under the Bakersfield Sign.
- **Weapons (6, one each):** super shotgun (casino wing), nailgun (LAN lot), grenade launcher (ORCOM hall), rocket launcher (Sign plaza), lightning gun (LAN lot), super nailgun (Union Ave).
- **Armour:** 4 yellow armour (= jetpack, as in bklan2): casino lobby, on top of the Bakersfield Sign (31 ft), LAN lot, ORCOM hall; 1 green armour (Union Ave).
- **Health:** 9 + a mega health on the Sign. **Ammo:** 3 shells, 2 nails, 4 rockets, 2 cells (two rocket / cell packs sit on the 130A roof, reached by the v3 pads).
- **Teleports (4 pads, 2 pairs):** casino north lot <-> Larry's lot; Bakersfield Sign <-> ORCOM porch. Boards say where they go. Tested: every pad lands on its destination.
- **Jump pads:** Union median -> up onto the Bakersfield Sign; Union median -> straight up 300 ft (jetpack / sky); casino south lot -> straight up 200 ft;
  plus the v3 pads kept from bklan2 inside the B-LAN and Sign windows (corner pads, pads up to roofs).
- Sealed: `qbsp` reports no leak (BSP2). `vis -fast`, `light -extra`.

## Testing done
- Screenshots (contact sheets, `source/mm_tools/out/bks/img/`): `sheet1.jpg`, `sheet2.jpg` (random spawns, two looks each), `sheet_tp.jpg` (the four teleports), `sheet_ov.jpg` (sky at 900 ft); `zs_final.png`, `zs_tp1..4.png`, `zs_ov*.png` in the project root.
- `source/mm_tools/bks_reach.py`: ground flood fill from the first spawn: 99.6 % of the floor is connected; all spawns, items and teleports are reachable (items on roofs / the Sign are reached by pads and skipped).
- Bots: they join (`bm_botfill`) and spawn on my spawns without being stuck, **but they do not walk on this map, nor on bklan2** (FrikBot needs `maps/*.way` waypoints and none ship), so item reach by bots could not be tested; the flood fill stands in for it.
- Scripts: `zz_bks.cfg` (respawn look-around), `zz_bksbots.cfg`, `source/mm_tools/view_bks.sh "name x y z yaw [pitch]"` (fixed-position views on a no-vis test map).

## What was cut
- bklan2: Manning St house + van, Amberton Park, the railroad, Sumner St, Union Ave overpass / loop ramp, the Capri Motel, all GIS filler blocks, the v3 sound wall, the v3 teleport hubs (to Manning St) and the real Sacramento St length.
- goldenwest: the OpenStreetMap street (cross streets, motels, RV parks, houses, Delaware St, Trinity Ave), the used-car lot south of the parcel and the original Union Ave strip (replaced by the new street).
- Real distance: the two places are about 800 ft apart here (the real ones about 2 miles).

## What is missing / next
- Manning St house + van and Amberton Park (box B of bklan2) are not in; they would be another window plus a pad or teleport.
- No bot waypoints: bots stand still. A `maps/bakolansmall.way` would need the FrikBot waypoint tooling.
- The east side of Union Ave south of the Sign (y < 150) is a plain wall; the plaza fill is generic (low walls, hedge planters, palms, cars), not traced.
- The 130A LAN hall is crowded with furniture; the flood fill cannot judge its inside, so the three pickups that used to be inside it were moved onto the lot in front.
- The source maps carry a few degenerate hip-roof brushes (qbsp warns "invalid winding point" once, harmless, same as goldenwest).
- Wads are used as they are in `out/maps` (goldenwest, gwcasino, bklan, bklan3); `build_bakolansmall.sh` does not rebuild them, so rebuild a wad first if another agent changes its textures.
- Files: `make_bakolansmall.py`, `build_bakolansmall.sh`, `bks_mapio.py`, `bks_topdown.py`, `bks_reach.py`, `bks_sheet.py`, `view_bks.sh` (all new, in `source/mm_tools`).
