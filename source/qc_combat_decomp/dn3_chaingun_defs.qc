#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DN3DOOM CHAINGUN CANNON (slot 4: IT_NAILGUN)
Triple-barrel rotary ripper (W_Chaingun.txt, Gloves / CGGN* style):
  - 18-frame 2D CSQC drawpic (CGGNA0..CGGNR0) with Doom grAb offsets & walk bob
  - Sounds: sound/dn3cg/{fire,select,dryfire}.wav + DN3FX bullet impacts/ricochets
  - 35 Hz rotary cadence (~17.5 rds/s, 0.0571s), 12 dmg hitscan bullets, 3.5x3 deg spread
  - 100-round belt magazine (bm_reload), brass casings, tracers, muzzle smoke, vertical kick
================
*/

float DN3CG_TIC			= 0.0285714;	// 1 / 35 s (Doom 35 Hz tic rate)
float DN3CG_REFIRE		= 0.0571428;	// 2 tics per rotary shot (~17.5 rds/s)
float DN3CG_DRAW_TIME	= 0.22;			// raise slide time
float DN3CG_BULLET_DMG	= 12;			// 12 dmg * 17.5/s = 210 DPS (alongside M4A1)

// CSQC clientstat slot 122 (+ shared slot 113 dn3_st_speed)
.float	dn3_cg_st_frame;	// packed: bits 0..4=frame (1..18), bit 5=bright, bits 6..8=offset idx, bits 9..14=raise_px

// Server per-player state
.float	dn3_cg_active;		// 1 while holding IT_NAILGUN
.float	dn3_cg_draw_t;		// time weapon was drawn
.float	dn3_cg_draw_snd;	// 1 once equip click played
.float	dn3_cg_fire_t;		// time last bullet fired
.float	dn3_cg_step;		// 0=tap first shot, 1..6=rotary barrel loop step
.float	dn3_cg_spindown_t;	// start time of H->I->J glowing spindown on trigger release

void() DN3CG_Precache;
void() DN3CG_Reset;
float() DN3CG_CanFire;
void() DN3CG_Fire;
void() DN3CG_Frame;
