#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PROJECTILE COLLISION & SKEET-SHOOTING INTERACTIVITY (proj_collide_defs.qc)

Lets curated projectiles, Rob Dob drones, and Winged Breezy-Hair John birds
collide in mid-air with weight/comedy tiers, and lets players skeet-shoot
projectiles out of the air for escalating combo rewards.

CVAR: bm_proj_collide (default 1; 0 disables the system)
================
*/

var float	autocvar_bm_proj_collide = 1;

float	PC_KIND_NONE		= 0;
float	PC_KIND_LIGHT		= 1;	// missile, grenade, greenjar_proj, greenguy_mini, pickle, bigbanana, netsend_disk
float	PC_KIND_DOOKIE		= 2;	// dookie_shot (Super-Splat Pinata + Poop-Coating)
float	PC_KIND_ROB			= 3;	// robdob (drone)
float	PC_KIND_HEAVY		= 4;	// wc_shot, kyle_proj, megaman, milky
float	PC_KIND_BIRD		= 5;	// misc_vehicle_johnbird

float	PC_SKEET_WINDOW		= 5.0;	// seconds to chain Skeet Combo tiers
float	PC_SELF_GRACE		= 0.15;	// seconds after spawn before shooter can airburst own shot
float	PC_POOP_DUR			= 2.5;	// seconds of Poop-Coating slow + stink + fly buzz
float	PC_POOP_SLOW_MULT	= 0.70;	// 30% movement slow while poop-coated
float	PC_POOP_RADIUS		= 340;	// splash coating radius on mid-air Dookie Pinata

entity	pc_head;
entity	pc_spike_head;

.float	pc_reg;
.entity	pc_next;
.float	pc_kind;
.float	pc_rad;
.float	pc_born;
.float	pc_popped;
.float	pc_pinata;
.entity	pc_killer;
.entity	pc_blast_ignore;	// light projectile ignores splash on the Heavy that plowed through it
.vector	pc_prev_org;
.float	pc_clash_cd;		// throttle mid-air interception callouts on heavy plow-throughs

.float	pc_spike_reg;
.entity	pc_spike_next;

.float	pc_skeet_cnt;		// player: active skeet combo count
.float	pc_skeet_t;			// player: combo expiry timestamp
.float	pc_skeet_frame;		// player: prevents multi-pellet single-frame double-count
.float	pc_refund_cooldown;	// player: clears attack_finished cleanly on next frame

.float	pc_poop_t;			// player/bird: Poop-Coating expiry timestamp
.float	pc_poop_fx_t;		// player/bird: next stink-cloud + fly buzz timestamp
.float	pc_poop_cshift;		// player: TRUE while brown mud v_cshift is applied

void(entity e, float kind, float rad) PC_Register;
void(entity s) PC_RegisterSpike;
void(entity p) PC_ResetPlayer;
void() PC_PlayerFrame;
void() PC_Frame;
float(entity attacker, vector src, vector end, float dmg) PC_TraceIntercept;
float(entity a, entity b) PC_HandlePair;
void(entity dookie, vector org, entity attacker) PC_DookiePinata;
void(entity e, entity attacker) PC_NoteKilled;
