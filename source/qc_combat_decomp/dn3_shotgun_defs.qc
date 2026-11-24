#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DN3DOOM PUMP SHOTGUN (replaces IT_SUPER_SHOTGUN slot 3)
Sprites: Sprites/Weapons/ShotGun/Gloves/DSGG* (20 frames, 2D CSQC drawpic)
Sounds:  sound/dn3sg/{fire,pump,shell,dryfire}.wav
================
*/

float DN3SG_TIC			= 0.0285714;	// 1 / 35 s (Doom 35 Hz tic rate)
float DN3SG_REFIRE		= 0.8571428;	// 30 tics fire + pump cycle
float DN3SG_PUMP_AT		= 0.5142857;	// 18 tics: pump sound + shell casing eject
float DN3SG_FLASH_END	= 0.0571428;	// 2 tics: zoom snap reset
float DN3SG_DRAW_TIME	= 0.22;			// raise slide time
float DN3SG_MAG_SIZE	= 8;			// 8-shell tube magazine
float DN3SG_PELLETS		= 7;			// 7 pellets per shot
float DN3SG_PELLET_DMG	= 12;			// 7 * 12 = 84 dmg (matches DN3DooM avg)
float DN3SG_PUSHBACK	= 120;			// 120 u/s pushback opposite aim

float DN3SG_SND_NONE	= 0;

// CSQC clientstats (slots 112..113)
.float	dn3_st_frame;		// packed frame (bits 0..5 = 1..20, bit 6 = offset(-4,31), bit 7 = bright, bits 8..15 = raise_px)
.float	dn3_st_speed;		// horizontal ground speed for Doom figure-8 walk bob

// Server per-player state
.float	dn3_sg_active;		// 1 while holding IT_SUPER_SHOTGUN
.float	dn3_sg_draw_t;		// time weapon was drawn
.float	dn3_sg_draw_snd;	// 1 once equip pump sound played
.float	dn3_sg_fire_t;		// time last shot started
.float	dn3_sg_pump_done;	// 1 once pump sound + casing happened for current shot
.float	dn3_sg_kick_step;	// pitch-kick curve step (0..5)
.float	dn3_sg_rl_phase;	// 0=none, 1=tilt-in, 2=insert-loop, 3=tilt-out
.float	dn3_sg_rl_t;		// start time of current reload phase/cycle
.float	dn3_sg_rl_snd;		// 1 once shell insert sound + mag increment happened in current cycle

void() DN3SG_Precache;
void() DN3SG_Reset;
float() DN3SG_CanFire;
void() DN3SG_Fire;
void() DN3SG_StartReload;
void() DN3SG_Frame;
