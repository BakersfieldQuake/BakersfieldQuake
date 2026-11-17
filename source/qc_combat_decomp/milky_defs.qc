#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE MILKY GUN - definitions (Combat+ only; it replaces the super nailgun)

Key 5 / IT_SUPER_NAILGUN is the Milky Gun: same item bit and nails, but it fires the Pink Lady (milky.qc).
	- one lady a shot, MILKY_REFIRE between shots; the LAN magazine holds 2 (bm_reload.qc), reload 5 s
	- she floats (no gravity) at MILKY_SPEED, always facing the way she goes, and the song plays quietly from her
	  (sound/milky/song.ogg, the track from 0:20.1, at MILKY_SONG_VOL / MILKY_SONG_ATTN: only audible when kinda close)
	- she drifts along the shooter's aim until she sees an enemy, then turns toward him slowly (MILKY_TURN)
	- while ladies are out every player drops breadcrumbs (milk_crumb) as he moves; when she loses sight of her
	  target she follows his newest crumb she can reach, so she finds her way round corners after him.
	  No crumb in reach for MILKY_LOST seconds: she gives him up and looks for someone else
	- MILKY_HEALTH: five or six rockets. Hits spurt milk instead of blood
	- she bursts when she reaches an enemy, is shot down, or after MILKY_LIFE: MILKY_BLAST radius damage, a huge
	  spray of milk, and the milk splats onto the walls, floor and ceiling round her (and where the flung globs land)
	- wall and ceiling splats drip; floor splats are puddles you slide on (MILK_GRIP: little grip, momentum kept)
	- splats last MILK_LIFE seconds and fade; at most MILK_MAX in the world
	- ONE lady at a time per player: while his is alive the gun refuses to throw another (Milky_CanFire); he can throw the next
	  after she explodes (reached someone, shot down, timed out), or, with the 2-lady magazine empty, after the reload
Models: progs/pinklady.md3 (16-view sprite, build_pinklady_assets.py), progs/milksplat.md3 (build_milky_assets.py).
Test aid: cvar milky_test 1 makes the shooter a target too (zz_milky.cfg).
================
*/

float	MILKY_REFIRE		= 0.75;		// cool-down after she is thrown
float	MILKY_WIND			= 0.50;		// fire pressed to her leaving the open palm (mvm_f_00..35, build_milky_view.py)
float	MILKY_FLYOUT		= 0.30;		// empty open hand follows through and drops away (mvm_f_36..55)
float	MILKY_HIDE			= 0.45;		// minimum pause out of sight before a fresh lady rises into the fist
float	MILKY_RAISE			= 0.28;		// seconds the fist takes to rise smoothly from below onto the screen
float	MILKY_EMERGE		= 0.56;		// seconds the 3D Pink Lady glides & twirls from palm size to MILKY_SCALE
float	MILKY_IDLE_FRAMES	= 96;		// skins 0..95 (idle A) and 96..191 (idle B), native 24 fps, ping-ponged in QuakeC
float	MILKY_IDLE_FPS		= 24;		// 190 ping-pong steps at 24 fps = 7.92 s per idle cycle
float	MILKY_SKIN_B		= 96;		// first skin of idle B
float	MILKY_SKIN_F		= 192;		// first skin of the shot (192..247)
float	MILKY_WIND_FRAMES	= 36;		// mvm_f_00..35 (skins 192..227): windup & fingers opening
float	MILKY_FOLLOW_FRAMES	= 20;		// mvm_f_36..55 (skins 228..247): empty open hand dropping away
float	MILKY_SPEED			= 130;		// players run 320: you can get away, for a while (review 2026-10-31: "slowly creep up to people")
float	MILKY_SPEED_LOST	= 80;		// hovering about when she has lost her target
float	MILKY_TURN			= 70;		// degrees a second she turns toward what she wants: a slow lock-on
float	MILKY_HEALTH		= 600;		// a direct rocket does 100-120
float	MILKY_LIFE			= 60;		// tone-down 2026-11-02, was 214 (the 105 s song twice): she no longer sings across a whole match
float	MILKY_SONG_LEN		= 105.2;	// sound/milky/song.ogg: replayed once when it ends
float	MILKY_HOVER			= 100;		// her middle stays this high over the floor: the 190-unit picture never sinks into it
float	MILKY_FLASH			= 900;		// players this close who can see the burst get the white flash and the milk dripping down the screen
float	MILKY_FREEZE		= 0.6;		// seconds the blast freezes you in place (then you slide on the milk)
float	MILKY_SEEK			= 2500;		// how far she can spot someone
float	MILKY_LOST			= 6;
float	MILKY_REACH			= 170;		// this close to an enemy and she bursts (was 110)
float	MILKY_BLAST			= 200;		// tone-down 2026-11-02 (was 320)
float	MILKY_PER_PLAYER	= 1;
float	MILKY_SCALE			= 13;		// the 20 unit card is 260 units; she fills 0.72 of it (build_pinklady_assets.py ROOM): about 190 tall, three players
vector	MILKY_MIN			= '-28 -28 -90';		// her box: down to the bottom of her picture, so she floats above the floor instead of sinking in
vector	MILKY_MAX			= '28 28 40';
float	MILKY_SONG_VOL		= 0.3;		// quieter single-channel volume (review 2026-11-01: turn the volume down on her)
float	MILKY_SONG_ATTN		= 1.6;		// 1 is gone at 1000 units; 1.6 is gone past ~625 units ("only hear her if you're kinda close")

float	MILK_LIFE			= 20;
float	MILK_FADE			= 3;
float	MILK_MAX			= 120;
float	MILK_TRACES			= 70;		// splats thrown straight out of the burst ("cover everything with milk")
float	MILK_RANGE			= 1150;
float	MILK_GLOBS			= 45;		// globs flung out that splat where they land
float	MILK_GRIP			= 0.03;		// how much of your own pushing counts on milk ("you should be sliding all over the place")
float	MILK_DRAG			= 0.1;		// fraction of your slide lost a second
float	MILK_PASS			= 260;		// a kick bigger than this in one frame (a blast, a jump pad) is left alone
float	MILK_TOPSPEED		= 650;
float	MILK_CRUMB_LIFE		= 14;

float	milky_inflicting;		// TRUE while a lady's burst is dealing damage (obituary)
float	milky_count;			// ladies in the world
float	milk_count;				// splats in the world
entity	milk_qhead;				// O(1) FIFO queue head (oldest milk splat/puddle)
entity	milk_qtail;				// O(1) FIFO queue tail (newest milk splat/puddle)
.entity	milk_qprev;
.entity	milk_qnext;
.entity	milky_active;			// player: currently active Pink Lady entity
.float	milk_under_t;			// player: throttle Milk_Under check
.float	milk_under_cached;

.entity	milky_owner;		// lady: who fired her (she is solid to everyone, him too, so .owner stays world)
.entity	milky_target;		// lady: who she is after
.vector	milky_dir;			// lady: the way she faces and flies
.vector	milky_goal;			// lady: where she is heading now
.float	milky_goal_t;		// lady: the crumb time of milky_goal (0: the target himself)
.float	milky_seen;			// lady: when she last had her target or one of his crumbs in reach
.float	milky_born;
.float	milky_hp;			// lady: what is left of her (her .health is never touched, so T_Damage never kills her)
.float	milky_scan;			// lady: next look round for someone to go after
.vector	milky_last;			// lady: where she was a second ago (stuck check)
.float	milky_lastt;
.float	milky_dodge;		// lady: shoving off sideways until (she was stuck)
.float	milky_drip;			// lady / splat: next drip
.float	milky_phase;		// lady: her bob and sway
.float	milk_born;			// splat
.float	milk_size;			// splat: final scale
.float	milk_r;				// puddle: slippery radius
.vector	milk_n;				// splat: surface normal
.float	milk_t;				// crumb: when dropped
.vector	milk_crumbat;		// player: where the last crumb went
.float	milk_crumbt;
.vector	milk_v;				// player: velocity at the end of last frame (the slide)
float	MILK_COAST			= 0.3;		// you keep sliding this long after the last puddle edge (review 2026-11-01: slide, not in control)
.float	milk_last;			// player: when a puddle was last under him
.float	milk_slip;			// player: on milk last frame
.float	milk_fx;			// player: next skid splash
.float	milky_wind;			// player: when the lady in his fist leaves it (0: none)
.float	milky_msg;			// player: no more 'she is still out there' message until
.float	milky_hide;			// player: the hand is out of sight until
.float	milky_threw;		// player: when the last one was thrown
.float	milky_fire_t;		// player: when the current windup began
.float	milky_ptrail;		// lady: next puddle on the floor under her
.vector	milky_from;			// lady: palm-side start position during launch emergence
.vector	milky_to;			// lady: bbox-verified full-scale flight handoff position
.float	milky_emerged;		// lady: TRUE once initial emergence into full bbox has completed
.float	mv_on;				// view model: drawn last frame
.float	mv_clip;			// view model: idle clip 0 (A) or 1 (B)
.float	mv_state;			// view model: 0 idle, 2 the shot
.float	mv_t;				// view model: when the current clip started
.float	mv_raise;			// view model: rising smoothly into view until
.float	milky_song2;		// lady: the second play of the song has started
.float	milk_freeze;		// player: frozen by a burst until
.float	milk_scr;			// player: when milk last hit his screen (the flash and the drips, csqc/bm_hud.qc)
.float	milk_st;			// player: stat 68, milk on the screen in tenths of a second (60 = just hit, 0 = clean)

void() Milky_Precache;
void() Milky_Fire;
float() Milky_CanFire;
void() Milky_PlayerFrame;
void(entity vm) Milky_ViewFrame;
float(entity targ, entity inflictor, entity attacker, float damage) Milky_Damage;
