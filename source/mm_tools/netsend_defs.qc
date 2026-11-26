/*
================
THE NETSEND GUN ("WHERE'S THE DISK?", the fourth fun gun, took the sentry's slot, impulse 64; netsend.qc has the code)

The joke: a high-school interrogation over a floppy labelled LOL.BAT that sent NET SEND pop-ups to the whole network.
Fire: the hand throws the disk at the floor. It bounces off walls and sticks to the first floor it lands on, and a beige
early-90s PC grows out of it. For good it works like the TF sentry: it does not spin, it turns to face the
nearest player it can see (never its owner), shoots green lasers at them while it faces them, and sweeps the room when
nobody is in sight. Every NS_SHOT_GAP it also sends NET SEND to that player: a popup on their screen, a beep, a bolt of
packets, NS_DAMAGE. A PC never times out (review 2026-11-05) but can be shot to bits (NS_HEALTH; bug report 2026-11-07: it
could not be killed in deathmatch); the only limit is NS_MAX_PCS standing
PCs per player, so you can drop them all over the map. The next disk comes back with the magazine (FG_NETSEND_REGEN).

Models, shaders, effects and the frame map: source/mm_tools/build_netsend_assets.py (frames in netsend_frames.txt).
Hooks: funguns.qc (the tables, FunGun_Attack, FunGun_ViewFrame), bm_reload.qc (BM_FG4 magazine), pickle.qc
(Pickle_ViewFrame calls NS_DiskViewFrame for the held model). The obituary is the
generic fun gun one (client.qc, through fg_inflicting).
================
*/

float	NS_RANGE		= 900;		// it only sends to someone this close, and in its view
float	NS_DAMAGE		= 8;		// per NET SEND
float	NS_SHOT_GAP		= 7;		// seconds between two NET SENDs (funny popup without HUD spam)
float	NS_MAX_PCS		= 2;		// PCs one player can have standing at once (oldest pops on #3)
float	NS_LIFE			= 30;		// battery lifetime (seconds) before a deployed PC powers down & pops
float	NS_HEALTH		= 40;		// shoot it to bits and it is gone (its owner can have another standing in its place)
float	NS_THROW		= 620;		// the disk's speed when thrown
// NS_THROW_DELAY (when the hand lets go, after the fire) comes with the held model's frame map: netsend_diskvm.qc
float	NS_LIFE_DISK	= 8;		// a disk that has not stuck by then is lost (and the magazine gets it back)
float	NS_TURN			= 240;		// degrees a second the PC turns to face its target (the TF sentry's head; no spinning)
float	NS_AIM			= 12;		// it fires once it faces its target within this many degrees
float	NS_SCAN_ARC		= 60;		// with nobody in sight it sweeps this many degrees each side of where it faced when it landed
float	NS_SCAN_RATE	= 1.2;		// radians a second of that sweep
float	NS_LASER_GAP	= 0.42;		// seconds between two green lasers (~12 DPS per PC without laser spam)
float	NS_LASER_DMG	= 5;		// per laser (harassment prop, not a laser killbox)
float	NS_LASER_SPEED	= 1100;

.float	ns_state;		// PC: 2 materializing, 3 booting, 4 sending, for good (the disk in the air has none)
.float	ns_t;			// PC: when the current state began
.float	ns_next;		// PC: when the next NET SEND may go
.entity	ns_arc;			// PC: its lightning model (netsend_arc.md3)
.float	ns_throw_at;	// player: when the disk leaves the hand (0 = not throwing)
.float	ns_fire_t;		// player: when the throw began (the fire; the disk leaves NS_THROW_DELAY later)
.float	ns_empty;		// player: the hand was empty last frame
.float	ns_rl_t;		// player: when the new disk came back into the hand
.float	ns_laser_t;		// PC: when the next green laser may go
.entity	ns_scr;			// PC: its screen, a model of its own (netsend_scr.md3)
.float	ns_scan_t;		// PC: when NS_Sentry next looks for a target (it keeps ns_target in between)
.entity	ns_target;	// PC: the player it is facing / shooting at
.float	ns_yaw0;		// PC: where it faced when it landed (the middle of its sweep)

// the held disk (v_netsend.md3 is THE DISK: one card, its skin picks the frame; build_netsend_disk_view.py, frame map in
// netsend_diskvm.qc). It rests, does a trick now and then, throws, drops away and a new disk comes up
float	NDVM_RAISE		= 0.42;		// seconds for a new disk to come up from below
float	NDVM_DROP		= 0.24;		// seconds for the empty hand to drop away after the throw
float	NDVM_GAP		= 0.40;		// seconds with nothing in the hand before the next disk comes up
var float	autocvar_ns_vm_tricks	= 1;	// 0: the hand just rests (no disk tricks)
.float	ndvm_on;		// viewmodel entity: showing THE DISK
.float	ndvm_rest_t;	// player: when the current rest began
.float	ndvm_wait;		// player: how long to rest before the next trick
.float	ndvm_trick;		// player: the trick playing, 1-based (0 = resting)
.float	ndvm_trick_t;	// player: when it began
.float	ndvm_count;		// player: tricks played so far (they take turns)

void() NS_Precache;
void(entity vm, float is_quad) NS_DiskViewFrame;
void() NS_Throw;
void() NS_DiskThink;
void() NS_DiskTouch;
void() NS_Think;
void() NS_LaserTouch;
float(entity who) NS_Count;
void(entity who) NS_MakeRoom;
void(entity p) NS_ClientGone;
