#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
FORELOCO POWERUP - shared declarations (Combat+)

Watermelon Four Loko floating pickup -> 1st-person pickup/open/drink -> "VEGAS BABY!"
party music + blackout -> 30-second runaway Eric in the Hospital Bed rampage!
================
*/

float	FL_DRINK_DUR	= 2.85;
float	FL_VM_FRAMES	= 36;
float	FL_BLACK_HOLD	= 0.45;
float	FL_BLACK_FADE	= 0.35;
float	FL_INTRO_DUR	= 2.50;
float	FL_INVULN_DUR	= 3.20;
float	FL_BED_DUR		= 32.5;
float	FL_PARTY_LEN	= 6.80;		// sound/foreloco/party_loop.wav is 6.857s

.float	fl_phase;					// 0=off, 1=drinking, 2=blackout pre-bed, 3=driving Eric bed
.float	fl_t0;						// current phase start timestamp
.float	fl_end_t;					// hospital bed expiration timestamp
.float	fl_invuln_t;				// spawn invulnerability expiration timestamp
.float	fl_hits;					// enemies/players launched during this ForeLoco rampage
.float	fl_vm_frame;				// 1..36 sprite frame
.float	fl_snd_flags;				// 1=can_open, 2=drink_gulp, 4=vegas_baby, 8=intro_launch
.float	fl_saved_wep;				// weapon restored after ForeLoco ends
.float	fl_proj_alt;				// toggles 0/1 between thrown Four Loko can and flying bedpan
.float	fl_fx_t;					// party sparkle particle throttle

// CSQC stats (114..119 in bm_match.qc)
.float	fl_st_black;				// 0..100 screen blackout alpha
.float	fl_st_mode;					// 0=off, 1=drinking, 2=blackout, 3=hospital bed rampage
.float	fl_st_rem;					// tenths of seconds left (0..325)
.float	fl_st_speed;				// current speed in u/s
.float	fl_st_flags;				// bit1=invuln, bit2=360 reveal, bit4=boost, high bits=hits*16
.float	fl_st_anim;					// 1..36 2D viewmodel sprite frame

void() FL_Precache;
void() FL_Impulse;
float() FL_Frame;
void(entity p) FL_Reset;
float() FL_BedCustomize;
void(entity p, entity v) FL_BedFire;
void(entity p, entity v, float dt) FL_BedDriveTick;
void() item_powerup_foreloco;
