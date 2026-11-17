BakersfieldQuake - Combat+ (quake15) with the Mega Man gun.
Engine: Zircon Engine (engine\zircon_beta_gcc.exe; we are no longer using DarkPlaces).
Layered on top of quake15: launch with  Play BakersfieldQuake.exe  or  engine\zircon_beta_gcc.exe -basedir . -userdir . -game quake15 -game BakersfieldQuake +mlook
(from G:\Quake\Combat; quake15 itself is untouched).

THE MEGA MAN GUN - its own weapon; every player has it. All the normal weapons are stock again.
  Select: key 9 (bind "9" "impulse 14", set in qxdc.cfg). Also in weapon cycling after the CCC gun (the old laser cannon).
  Ammo:   a magazine of 2 Mega Men that reloads (see LAN RULES below; with bm_reload 0 it is 1 back every 5 s).
  Fire:   wind up and throw. He lands on his wheels and drives straight, steering round walls
          and corners (follows the map), hops up steps and rolls off ledges. When he spots
          someone he hops and blasts his horn, chases them, then crouches and leaps on them
          like a headcrab. Head-on wall hits: 5, then he blows. Gives up after 12 seconds.
  Sounds: deep boat motor while driving (revs up near a target), foghorn when he spots/leaps.
  Others see a little Mega Man in your hand (you see it too in chase_active).
  Kill message: "X got run over by Y's Mega Man".

Files: progs/megaman.md3 (+.png) the projectile, progs/v_megaman.md3 (+mm_hand.png) the held view,
sound/weapons/megamotor.wav + megahorn.wav. progs.dat is Combat+'s own game code, decompiled and
rebuilt (BakersfieldQuake\source\qc_combat_decomp\). The decompiled Combat+ code belongs to its author (Totalitarian);
keep it for personal use.

Tools (mm_tools): megaman.qc / megaman_defs.qc are the gun's code (shared with the vanilla build),
patch_megaman_combat.py hooks it into qc_combat_decomp, build_viewmodel.py makes the held model,
make_sounds.py the sounds. Rebuild: python -I BakersfieldQuake\source\mm_tools\patch_megaman_combat.py, then compile
BakersfieldQuake\source\qc_combat_decomp\progs.src with fteqcc64 and copy progs.dat here.

THE GIRLFRIEND GUN - a thrown photo-model projectile (it lives in the old banana gun's slot: IT_BANANA, impulse 15).
  Select: key 0 (bind "0" "impulse 15"). Also in weapon cycling after the Mega Man gun.
  Ammo:   2 girlfriends, one recharges every 6 seconds (no magazine/reload).
  Fire:   you throw her (nose first); she lands on her feet and runs at the nearest enemy she can see (280 u/s, steers round
          walls, hops steps) and blows up next to them: 90 radius damage, rocket-style explosion. Nobody in sight: she runs
          about and blows up after 12 s or 5 wall bumps. You can shoot her down (40 health): she just pops.
  Kill message: "X was blown up by Y's girlfriend".
  Model: progs/girl.md3 + girl.png (about 26k triangles, 8-frame run bob) and progs/v_banana.md3 + v_banana.png (held, 16 frames).
          Rebuilt from the turnaround video (visual hull + projected photo texture): source\mm_tools\out\girl (OBJ) and
          source\mm_tools\girl_pipeline (the python), girl_md3.py writes the md3s. Code: banana_defs.qc, banana.qc (Banana_* names kept).
  Sounds are existing ones (funny/giggles.wav, giggle2.wav, r_exp3). Backups: progs.dat.pre_girl, banana.qc.pre_girl.
  Rebuild: python source\mm_toolsuild_combat.py (copies the sources, compiles, installs progs.dat).

THE BANANA GUN - REMOVED (Banana_Select/Banana_Give do nothing now; the text below is history).
  Select: key 0 (bind "0" "impulse 15", set in quake15\qxdc.cfg). Also in weapon cycling after the Mega Man gun.
  Ammo:   5 bananas, one recharges every 2 seconds (shown as the ammo count).
  Fire:   the big yellow tube shoots a huge banana that bursts on impact (big explosion, 90 direct + 100 splash)
          into 20 little bananas. They bounce around and go off on touch (25 damage) or after 1-3 seconds.
  Kill message: "X was peeled by Y's banana".
  Sounds: bananafire/bananasplat/bananapop are synthesised; bananavoice, bananalaugh and megause are cut from
          the Johny clips pack (also: "use Megaman" now plays when the Mega Man gun throws).

Files: progs/banana.md3 + banana.png (the banana; NVIDIA SimReady asset food_produce_banana_j01, CC-BY, credit NVIDIA),
progs/v_banana.md3 + v_banana.png (the held tube). Code: BakersfieldQuake\source\mm_tools\banana_defs.qc, banana.qc.
All 24 item bits are taken, so IT_BANANA is only a .weapon value (see banana_defs.qc); nobody "owns" it as an item.
Rebuild: python -I BakersfieldQuake\source\mm_tools\patch_megaman_combat.py, python -I BakersfieldQuake\source\mm_tools\patch_banana_combat.py, then compile
BakersfieldQuake\source\qc_combat_decomp\progs.src with fteqcc64 and copy progs.dat here (BakersfieldQuake\source\qc_combat_decomp\build.bat does the compile + copy).
Assets: python -I BakersfieldQuake\source\mm_tools\build_banana_assets.py. A backup of the pre-banana progs.dat is progs.dat.pre_banana.

THE JETPACK (Duke Nukem 3D's) - a pickup next to every yellow armor, in every map (a map with no yellow armor has none).
  Pick up: walk into it; you get 60 s of fuel (cvar jp_fuel; 1 a second climbing, 0.4 a second hovering: cvar jp_hover). It comes back 30 s later (jp_respawn). A full tank can't take another.
  Fly:     in the air press jump again (or press J, impulse 71, any time): "they seem to be floating" plays, gravity is off, you hover.
           Hold jump to climb, crouch to sink, and the move keys fly you sideways at run speed (it brakes to a hover when you let go). J, landing or running dry switches it off. Fuel: 1 a second climbing, 0.4 a second hovering (about 2.5 minutes of hover on a full tank). Death loses it.
  Sounds:  sound/jetpack/floating.wav ("I'm floating", funny/imfloating.wav boosted) when you take off, sound/jetpack/swoosh.wav looping while it burns; flames under your feet.
  Files:   jetpack_defs.qc, jetpack.qc (mm_tools), progs/jetpack.md3 + jetpack_*.png (build_jetpack.py), sound/jetpack/swoosh.wav.
  Rebuild: python -I build_jetpack_assets.py, python -I patch_jetpack_combat.py (once), python -I build_combat.py.
  Test (sv_cheats): impulse 75 = a stand-in armor + jetpack 200 units ahead (start has no armor), 73 = stand by it, 74 = step on it.
  Backup of the pre-jetpack progs.dat: progs.dat.pre_jetpack.

BAKERSFIELD LAN RULES (BakersfieldQuake\source\mm_tools\bm_defs.qc, bm_reload.qc, bm_match.qc, underdog.qc, bm_fun.qc; HUD overlay in
BakersfieldQuake\source\qc_combat_decomp\csqc\bm_hud.qc). A chill LAN deathmatch where scores stay close.
  Magazines: ammo never runs out, but every gun has a magazine (GL 6 like KTX Clan Arena, RL 5, Goo Gun 20, SSG 6 shots,
          NG 50, SNG 40 shots, LG ~6 s, laser ~4 s, Mega Man 2, Whack-a-Mole 3, Rob Trap 2).
          Empty = it reloads by itself; R reloads early; stop firing 2.5 s and it quietly tops up.
          Only the gun in your hand reloads at full speed (holstered ones at 1/4), so swapping can't keep
          the rockets coming. Any ammo or weapon pickup refills every magazine; pickups never switch your gun.
  Spawn protection 3 s (firing ends it). Self-damage x0.6 on top of the stock halving (rocket jumps keep
          their push). No fall damage. Health regenerates 5 s after the last hit, 10 a second.
  Score: suicides, the kill command, lava, falls, exits and monsters never change your frags.
  Catch-up (heat = your frags minus everyone else's average; gaps of 0-1 do nothing):
          leader heat 2+ gold glow, 4+ a +1 bounty on them, 6+ beacon and HUD marker
          through walls + "DOMINATING", 10+ whole body through walls. Nothing makes the leader weaker.
          Everyone spawns with 100 health and 100 green armor (bm_spawnarmor). The comeback boost (0-100%) comes from
          your deaths in a row, your K/D and how far behind you are, and it scales with player count: a kill halves
          the streak; suicides, lava and falls don't count; first place and anyone 2+ frags above the pack get none.
          Up to +150 spawn health, yellow armor (150) at 30% (bm_ud_yellow), red (200) at 60% (bm_ud_red), 250 at 90%,
          faster regen (1.5 s / 50 a second), up to +100% damage to and -35% damage from higher scorers, a free
          power-up after a real death from 50% (8 s Quad or pentagram from 75%), the Blue Shell from 70%.
          LAST STAND: 7 deaths in a row (bm_ud_streak; 8 in a 1v1, 6 at 6+ players, 5 at 10+) spawns you with Quad and
          a pentagram for 10 s, every spawn until you get a kill. Bots stop at 60% (bm_ud_botcap) with no Last Stand.
  Announcer (bm_fun.qc): FIRST BLOOD, KILLING SPREE 3 / RAMPAGE 5 / GODLIKE 8, "ended X's spree", DOUBLE / TRIPLE /
          MULTI KILL (within 3 s), REVENGE, each with a clip from sound/funny played to the whole room; a cheer when
          last place scores, a clip on gibs, HIGH bonks and 300+ sniper shots, "durr" on suicides. One clip every
          bm_fun_gap seconds; bm_fun 0 turns it off. The clip table is at the top of bm_fun.qc. Most clips can be a Larry McCart prank-call line instead (sound/larry, bm_fun_larry chance, default 0.7).
          Kill lines: the CCC gun (the old laser cannon), JohnWave grenade and every self-kill with a mod weapon have their own now.
  Match: bm_maplist playlist (server.cfg: e2m1 dm6 aerowalk dm3 dm4), timelimit 8, the scoreboard moves on
          by itself after 10 s. bm_botfill N keeps FrikBots in until there are N players.
  HUD: magazine pips and reload bar under the crosshair, protection countdown, red edges at low health,
          leader banner, comeback boost, "press F1" in warmup.
  Tuning: every number is a bm_* cvar, defaults in autoexec.cfg (set bm_debug 1 prints everyone's state).
  Configs: quake.rc (no intro demos) -> default.cfg (clean WASD binds, 1080p) -> q15_config_coop.cfg ->
          config.cfg (your saved settings win) -> autoexec.cfg (bm_* rules) -> personal.cfg (not shipped).
          server.cfg = the LAN dedicated server, warmup.cfg = the local game Play.cmd starts.
  Rebuild: python -I BakersfieldQuake\source\mm_tools\patch_lan_combat.py (after the other patch_*_combat.py), then
          python -I BakersfieldQuake\source\mm_tools\build_combat.py; the HUD: python -I BakersfieldQuake\source\mm_tools\build_csqc.py.
          progs.dat.pre_lan is the progs.dat from before.

---- MERGED FROM BakersfieldMemes (Oct 29) ----------------------------------------------------------------------

JOHNWAVE GRENADE - the grenade (grenade launcher and ogre) is JohnWave's head and goes off as a blue water splash instead of an
  explosion (same damage, same 20% fire): wavy splash sprite, rings on the floor, droplets, blue flash, splash sound. In flight the
  face looks back at the shooter; a bounce sets it tumbling; lying still it rolls face-up towards the nearest player.
  Files: progs/grenade.mdl (+_0.tga), progs/jw_splash.spr32, progs/jw_ripple.spr32, effect "johnwave_splash" in effectinfo.txt
  (copy in BakersfieldQuake\source\mm_tools\jg_effectinfo.txt). Code: BakersfieldQuake\source\mm_tools\jg_splash.qc (JG_ prefix; BakersfieldQuake\source\mm_tools\johnwave.qc, the tidal-wave gun, is separate),
  hooked in by BakersfieldQuake\source\mm_tools\patch_jg_combat.py. Delete grenade.mdl* to get the stock grenade back.

FLOATING HEAD - a monster: a big floating photo head that drifts round, says hello when it sees you, opens its mouth, then yells
  "HUG TIME" and rushes you and blows up (90 radius damage), spraying little screaming heads. 40 health; shooting it blows it up too.
  Deathmatch: cvar fh_heads N keeps N heads floating round the map (default 2, 0 = none). impulse 17 summons one in front of you.
  Killing one gives no frag (Combat+ gives none for monsters). Obituary: "got a big wet kiss from a floating head".
  Files: progs/floathead.mdl (+_0/_1.tga), sound/floathead/*.wav. Code: BakersfieldQuake\source\mm_tools\floathead.qc, patch_floathead_combat.py.

PLAYER BODIES - REMOVED 2026-10-30 (suit guy / robe guy / wife). Everyone is Combat+'s own Ranger again. The models, playerbody.qc
  and the old personal.cfg lines are saved in G:\Quake\Combat\_backups\player_bodies_removed_2026-10-30.

GOO GUN - replaces the single-barrel shotgun (key 2, same slot, same shells). Full auto, a glob every 0.26 s, magazine 20,
  2.4 s reload. The glob arcs and sticks to whatever it hits (walls, floor, ceiling, other goo, so it piles up into walls and
  towers) and swells into a solid grey foam puff: it blocks players, bullets and rockets, and you can stand on it. 60 health,
  every hit chips grey debris and snow off it, explosions do x2.25 to it, popping throws lumps and a snowfall that
  lingers on the floor, it shrinks away after 20 s (96 in the world at most, the oldest pops). A blob that swells into a
  player stays soft and pops after 0.35 s. A direct hit does 8 and gums them up: 1.6 s crawling, no jumping ("GOOED!").
  Kill message: "X got gooed by Y's Goo Gun".
  Files: progs/v_googun.md3 (view), p_googun.md3 (in the hands; it rides p_shot.md3's frames), goo.md3 + googun_*.png, goo.png,
  sound/weapons/goofire/goosplat/goopop/goostick.wav, effects goo_splat/goo_chip/goo_burst/goo_snow/goo_puff in effectinfo.txt
  (copy in BakersfieldQuake\source\mm_tools\goo_effectinfo.txt). Code: BakersfieldQuake\source\mm_tools\goo_defs.qc, goo.qc,
  hooked in by patch_goo_combat.py. Assets: build_googun.py (the model is built from primitives in Python), make_goo_sounds.py.

SNIPER RIFLE - Team Fortress's sniper rifle replaces the nailgun (key 4, same slot, nail magazine of 50, 1 a shot).
  Hold fire to aim (only from standing nearly still): the shot charges from 50 to 400 damage in ~1.6 s, you walk at 80 while
  aiming, and the view zooms in (fov 90 -> 30; sn_autozoom 0 turns it off). Everyone sees your red laser dot where you aim.
  Let go to fire one hitscan shot of the charge, feet on the ground only (in the air the charge is lost), then 1.5 s before the next.
  No head shots. Leg shots (below the middle) do half and slow the victim 10% a hit, up to 6; a health pickup or healing past 95 mends them.
  Bots leave it alone (they never stand still to aim). Kill messages are TF's: "takes a bullet in the chest from", "is made legless by" ...
  Files: progs/v_srifle.mdl + sight.spr + sound/weapons/sniper.wav (Team Fortress 2.8's own; Valve owns TF now, so LAN only),
  progs/g_srifle.mdl (pickup) and p_srifle.md3 + .png (in the hands), both made from v_srifle by build_srifle.py.
  Code: BakersfieldQuake\source\mm_tools\sniper_defs.qc, sniper.qc, hooked in by patch_sniper_combat.py. progs.dat.pre_sniper is the one before.

BONK HAMMER - Bonk Jam's big bonker replaces the axe (key 1), with Bonk Jam's own numbers.
  Hold fire to charge (LOW under 0.7 s, MED to 1.35 s, HIGH after; a stinger plays at MED and HIGH), let go to swing.
  Hit someone: 30 / 80 / 200 and they get swatted along your view (on top of the normal damage push, so a HIGH hit sends
  players flying); a monster on its last legs takes double and gibs. Swing at the floor: the bonk hop, a launch that always
  tops out 64 / 128 / 192 units over the floor. Swing at a wall: a little push back. Swing at nothing in the air: an air dash
  (+25 / 250 / 500 forward). One swing can hit two things. 0.4 s before the next charge. Impulse 1 with it out: the spinny twirl.
  Kill message: "X got bonked by Y's hammer". Third person still shows Combat+'s axe (Bonk Jam only made the view model).
  Files: progs/v_hammer.mdl (Bonk Jam's v_hammer_default.mdl), spark_blue/spark_yellow.mdl, sound/hammer/*.wav, copied by build_hammer.py.
  Bonk Jam is by Kebby, fairweather and spootnik1 (ModDB); no licence for its models and sounds, so LAN only, ask them before sharing.
  Code: BakersfieldQuake\source\mm_tools\hammer_defs.qc, hammer.qc, hooked in by patch_hammer_combat.py (after patch_sniper_combat.py).
  progs.dat.pre_hammer is the one before.

SENTRY GUN - Team Fortress's sentry gun, always level 2, carried as a gun of its own: key B (impulse 70) takes out the spanner.
  Fire builds a sentry 64 units in front of you (feet on the ground, with room for it); it is see-through for 2 s while it sets
  up, then sweeps 50 degrees each way and shoots anyone it can see within 480 units except you: 16 damage every 0.1 s (160 a
  second), after it has turned to face them. 180 health, 120 shells (then it only sweeps). One each: building a new one blows up
  the old one. The spanner then reloads for 60 s (cvar sg_reload; the HUD reload bar shows it). Destroyed, it blows up (75 radius
  damage); knocked more than 15 units off its tripod (a Bonk Hammer swat will do it) it "malfunctions" and blows up.
  Its kills are your frags: "X is mown down by Y's sentry gun". Bots don't build them, but they get shot like anyone else.
  Files: progs/turrbase.mdl, turrgun.mdl, tgib1-3.mdl, v_span.mdl, sound/weapons/turrset/turrspot/turridle.wav (Team Fortress
  2.8's own, LAN only), copied by build_sentry.py. Code: BakersfieldQuake\source\mm_tools\sentry_defs.qc, sentry.qc, hooked in
  by patch_sentry_combat.py (after patch_hammer_combat.py; it also adds the B bind to default.cfg). progs.dat.pre_sentry is the one before.

Rebuild everything:  python -I BakersfieldQuake\source\mm_tools\build_combat.py   (the patch_*_combat.py scripts only need re-running on a fresh decompile)
TEST BOX MAP (testbox) - a wide open empty box (3072 x 3072, 768 high) for trying guns. Deathmatch only, 8 spawns on a ring in the
  middle, a row of health / armor / ammo boxes along the south wall. Every bot on this map is a target dummy: it walks in a small
  circle (half one way, half the other) and never shoots, never looks at you. The match is kept at 4 players (you + 3 bots).
  Play it:  engine\zircon_beta_gcc.exe -basedir . -userdir . -game quake15 -game BakersfieldQuake +deathmatch 1 +maxplayers 4 +map testbox
  Code: BM_DummyMap / BM_DummyBot in source\mm_tools\bm_match.qc (BotAI in frikbot.bot_ai.qc asks first). Map: source\mm_tools\make_testbox.py.
B-LAN WAREHOUSE MAP (bklan) - "Larry's warehouse": the 2001 B-LAN party in unit 130A of the multi-unit warehouse at 118 E 21st St,
  Bakersfield, and its block: the LAN hall (from the 2001 tape bklan.wmv), the back rooms, shop units 120A / 130C / the auto shop
  (insides guessed), both side lots, LMC Paint Supply, E 21st St and what is across it (from a Feb 2026 Street View gallery).
  Play it:  engine\zircon_beta_gcc.exe -basedir . -userdir . -game quake15 -game BakersfieldQuake +deathmatch 1 +maxplayers 4 +map bklan
  Files: maps/bklan.bsp + .lit, textures/bk_*.png and {*.png, gfx/env/bklan_*.png (skybox), progs/bklan/*.md3 + t_*.png (props).
  Build: source\mm_tools\build_bklan.sh (textures, map, ericw qbsp/vis/light); view_bklan.sh takes screenshots from given spots;
  props: simready_export.py (Blender) + simready_props.py. The making-of page: making_of_larrys_warehouse.html (build_making_of.py).
  Credits: props are NVIDIA SimReady Assets (huggingface.co/datasets/nvidia/simready-assets), CC-BY 4.0, credit NVIDIA;
  decimated, re-textured and converted to MD3 here. Street View / aerial imagery (c) Google, used as reference and for some
  street textures and the road-end backdrops: LAN only, do not redistribute the map with those images.
  In a browser: https://bakersfield.larrywew.fun/warehouse/ (walk / jump / fly, Quake movement and collision, three.js) and
  /warehouse/making-of.html. Rebuild + upload after map changes: sh source\mm_tools\deploy_web_viewer.sh
  Added 2026-10-31 (east of Sonora St, box B): E 21st St runs on into a replica of Sillect Ave with the Bakersfield Sign
  arching over it (measured: towers 97 ft apart, 31 ft high; source\mm_tools\bklan_sign.py), Buck Owens' Crystal Palace
  and its pylon, Buck Owens Blvd, the office block; south of it 1608 Manning St (the house with the white van), Manning St,
  School House Rd, Placer Ct and Amberton Park. Real footprints (OSM / Bakersfield GIS): osm_site.py -> bklan_site_*.json,
  built by make_bklan_v2.py. The map is BSP2 now (77k faces); vis takes about an hour.
ORCOM CONNECT LAN PARTY (orcom) - the Dec 2002 OrCom Connect LAN hall from "Orcom 2.mpg": a church / lodge banquet hall,
  76 x 52 ft, kitchen pass-through, OrCom / BAWLS banner, "Computer Renaissance" banner, rows of CRTs, burgundy chairs.
  Play it:  engine\zircon_beta_gcc.exe -basedir . -userdir . -game quake15 -game BakersfieldQuake +deathmatch 1 +maxplayers 4 +map orcom
  Build: python -I source\mm_tools\make_orcom.py out\maps\orcom.map, then qbsp/vis/light. Browser: /orcom/ on the VPS
  (sh source\mm_tools\deploy_orcom_viewer.sh). Screenshots: view_orcom.sh.
