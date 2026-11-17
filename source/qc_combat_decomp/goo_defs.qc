#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE GOO GUN - definitions (Combat+ only; it replaces the single-barrel shotgun)

Key 2 / IT_SHOTGUN is the Goo Gun: same item bit, same shells, but it lobs blobs of goo (goo.qc).
	- full auto, a shot every GOO_REFIRE seconds; one shell a shot (the LAN magazine is 20, bm_reload.qc)
	- the blob arcs (it has gravity) and sticks to the first thing it hits: a wall, the floor, the ceiling,
	  another blob (so they pile up into walls and towers)
	- a stuck blob swells into a solid puff: it blocks players, bullets and rockets, and you can stand on it. A floor blob is
	  33 high and each blob stacked on another adds 25, so you can jump up a ladder of them; a blob that swells under a
	  player lifts them onto its top (shoot at your own feet to climb)
	- GOO_HEALTH health; explosions do GOO_EXPLOSIVE x damage to it; it goes away by itself after GOO_LIFE seconds
	- every hit chips grey debris and a drift of "snow" off it; popping throws GOO_CHUNKS lumps and a long snowfall
	- a blob that finishes swelling on a player lifts them onto its top; if there is no room it stays soft and pops after GOO_OVERLAP seconds
	- a direct hit on a player does GOO_HIT_DAMAGE and gums them up: GOO_SLOW_TIME seconds at GOO_SLOW_SPEED, no jumping
Model: progs/v_googun.md3 (view), p_googun.md3 (in the hands), goo.md3 (the blob); build_googun.py makes them.
================
*/

float	GOO_SPEED		= 1150;
float	GOO_GRAVITY		= 0.55;
float	GOO_REFIRE		= 0.26;		// 230 rounds a minute
float	GOO_REFIRE_RAPID	= 0.16;		// with the rapid-fire power-up
float	GOO_HEALTH		= 60;
float	GOO_EXPLOSIVE	= 2.25;
float	GOO_LIFE		= 30;
float	GOO_OVERLAP		= 0.35;
float	GOO_SCALE		= 0.65;	// a grown blob is goo.md3 at this scale (~29 each way): small enough that you can JUMP onto one
float	GOO_HALF		= 25;		// a grown blob's box is GOO_HALF each way
float	GOO_SINK		= 0.3;		// a blob's centre sits this fraction of GOO_HALF off the surface it hit: a floor blob is only 33 high (a jump is 45)
float	GOO_STACK		= 1.0;		// a blob stuck on another one sits GOO_STACK x GOO_HALF past its centre: each step of a ladder is 25 high
float	GOO_HIT_DAMAGE	= 8;
float	GOO_SLOW_TIME	= 1.6;
float	GOO_SLOW_SPEED	= 110;
float	GOO_MAX			= 96;		// blobs in the world at once; the oldest pops to make room
float	GOO_CHUNKS		= 3;		// bouncing lumps a blob breaks into when it pops

float	goo_inflicting;		// TRUE while goo is dealing damage (obituary)
float	goo_count;			// blobs in the world
float	goo_chunk_n;		// bouncing lumps in the world (edict budget: pops are capped, see Goo_Chunks)

.float	goo_born;			// blob: when it was made
.float	goo_state;			// blob: 0 flying, 1 growing, 2 solid, 3 soft (a player is inside it), 4 shrinking away
.float	goo_t;				// blob: when the current state started
.float	goo_fx;				// blob: no more hit debris until (shotgun pellets would flood the particles)
.float	goo_slow;			// player: gummed up until
.entity	goo_stuck;			// player: the blob stuck on them

void() Goo_Precache;
void() Goo_Fire;
void() Goo_PlayerFrame;
float(entity targ, entity inflictor, float damage) Goo_Damage;
.float	goo_snd_t;		// player: next time one of his blobs may make an impact sound
