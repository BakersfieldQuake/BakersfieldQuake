/*
================
THE NETSEND GUN ("WHERE'S THE DISK?", the fourth fun gun, took the sentry's slot, impulse 64; netsend.qc has the code)

The joke: a high-school interrogation over a floppy labelled LOL.BAT that sent NET SEND pop-ups to the whole network.
Fire: the hand throws the disk at the floor. It bounces off walls and sticks to the first floor it lands on, and a beige
early-90s PC grows out of it. For NS_ACTIVE seconds it works like the TF sentry: it does not spin, it turns to face the
nearest player it can see (never its owner), shoots green lasers at them while it faces them, and sweeps the room when
nobody is in sight. Every NS_SHOT_GAP it also sends NET SEND to that player: a popup on their screen, a beep, a bolt of
packets, NS_DAMAGE. Shoot it (NS_HEALTH) to switch it off.
One at a time: a new throw switches the old PC off. The disk comes back with the magazine (FG_NETSEND_REGEN).

Models, shaders, effects and the frame map: source/mm_tools/build_netsend_assets.py (frames in netsend_frames.txt).
Hooks: funguns.qc (the tables, FunGun_Attack, FunGun_ViewFrame), bm_reload.qc (BM_FG4 magazine). The obituary is the
generic fun gun one (client.qc, through fg_inflicting).
================
*/

float	NS_RANGE		= 900;		// it only sends to someone this close, and in its view
float	NS_DAMAGE		= 5;		// per NET SEND
float	NS_SHOT_GAP		= 1.5;		// seconds between two NET SENDs
float	NS_ACTIVE		= 20;		// seconds it sends once it has booted
float	NS_HEALTH		= 40;		// shoot it to switch it off
float	NS_THROW		= 620;		// the disk's speed when thrown
float	NS_THROW_DELAY	= 0.29;		// the hand lets go at frame 44 of v_netsend.md3, 0.29 s into the throw
float	NS_LIFE_DISK	= 8;		// a disk that has not stuck by then is lost (and the magazine gets it back)
float	NS_TURN			= 240;		// degrees a second the PC turns to face its target (the TF sentry's head; no spinning)
float	NS_AIM			= 12;		// it fires once it faces its target within this many degrees
float	NS_SCAN_ARC		= 60;		// with nobody in sight it sweeps this many degrees each side of where it faced when it landed
float	NS_SCAN_RATE	= 1.2;		// radians a second of that sweep
float	NS_LASER_GAP	= 0.15;		// seconds between two green lasers (review 2026-10-31: "act just like the sentry gun from TF")
float	NS_LASER_DMG	= 3;		// per laser
float	NS_LASER_SPEED	= 1100;

.float	ns_state;		// PC: 2 materializing, 3 booting, 4 sending, 5 shutting down (the disk in the air has none)
.float	ns_t;			// PC: when the current state began
.float	ns_next;		// PC: when the next NET SEND may go
.entity	ns_arc;			// PC: its lightning model (netsend_arc.md3)
.entity	ns_pc;			// player: their PC, while it is up
.float	ns_throw_at;	// player: when the disk leaves the hand (0 = not throwing)
.float	ns_fire_t;		// player: when the throw began (the fire; the disk leaves NS_THROW_DELAY later)
.float	ns_empty;		// player: the hand was empty last frame
.float	ns_rl_t;		// player: when the new disk came back into the hand
.float	ns_laser_t;		// PC: when the next green laser may go
.entity	ns_scr;			// PC: its screen, a model of its own (netsend_scr.md3)
.float	ns_yaw0;		// PC: where it faced when it landed (the middle of its sweep)

void() NS_Precache;
void() NS_Throw;
void() NS_DiskThink;
void() NS_DiskTouch;
void() NS_Think;
void() NS_Die;
void() NS_LaserTouch;
void(entity pc) NS_Off;
