#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
B. TRIPLE WHEELED POWERUP - definitions (Combat+)

Pick up the spinning, glowing 4-Rocket-Launcher cluster -> hold FOUR guns at once for a short burst:
  - Slot 0 (Bottom-Right): whatever weapon you are currently holding
  - Slot 1 (Bottom-Left):  randomly selected weapon
  - Slot 2 (Top-Right):    randomly selected weapon, positioned UPSIDE DOWN
  - Slot 3 (Top-Left):     randomly selected weapon, positioned UPSIDE DOWN
Firing unleashes all 4 weapons in rapid succession (bm_triple_delay between shots, 0.25s..1.0s).
================
*/

var float	autocvar_bm_triple_dur		= 15;		// short duration in seconds
var float	autocvar_bm_triple_delay	= 0.25;		// seconds between each of the 4 sequential shots (0.25..1.0)
var float	autocvar_bm_triple_spawn	= 1;		// 1 = auto-place powerup in DM maps that lack one

float	TW_RL			= 1;
float	TW_GL			= 2;
float	TW_SSG			= 3;
float	TW_LASER		= 4;
float	TW_LG			= 5;
float	TW_MEGAMAN		= 6;
float	TW_MILKY		= 7;
float	TW_M4			= 8;
float	TW_GARAND		= 9;
float	TW_WCANNON		= 10;
float	TW_DOOKIE		= 11;
float	TW_PICKLE		= 12;
float	TW_GREENJAR		= 13;
float	TW_NETSEND		= 14;
float	TW_KYLE			= 15;
float	TW_CYRAX		= 16;
float	TW_POOL_COUNT	= 16;

// Extra main-gun display codes for CSQC HUD
float	TW_AXE			= 17;
float	TW_DOB			= 18;
float	TW_BANANA		= 19;

// Per-player state
.float	tw_end_t;			// expiration timestamp (0 = inactive)
.float	tw_wep1;			// Bottom-Left random weapon (1..TW_POOL_COUNT)
.float	tw_wep2;			// Top-Right upside-down random weapon
.float	tw_wep3;			// Top-Left upside-down random weapon
.float	tw_seq_step;		// 0 = idle, 1..3 = next slot to fire in rapid sequence
.float	tw_seq_next;		// server time for next sequential shot
.float	tw_fire_t0;			// last fire timestamp for slot 0 (HUD flash)
.float	tw_fire_t1;			// last fire timestamp for slot 1 (kickback + HUD flash)
.float	tw_fire_t2;			// last fire timestamp for slot 2
.float	tw_fire_t3;			// last fire timestamp for slot 3
.float	tw_warn_stage;		// 0..3 expiration countdown warning stage
.entity	tw_vm1;				// 1st-person Bottom-Left viewmodel
.entity	tw_vm2;				// 1st-person Top-Right upside-down viewmodel
.entity	tw_vm3;				// 1st-person Top-Left upside-down viewmodel
.entity	tw_halo;			// 3rd-person spinning 4-RL halo visible to others & chasecam

// Pickup entity fields
.vector	tw_spawn_org;
.float	tw_fx_t;

// CSQC clientstats (slots 152..157)
.float	tw_st_rem;
.float	tw_st_wep0;
.float	tw_st_wep1;
.float	tw_st_wep2;
.float	tw_st_wep3;
.float	tw_st_step;

float	tw_precached;
float	tw_map_spawned;

void() TW_Precache;
void() TW_MapSpawn;
void() TW_Frame;
void() TW_TriggerSequence;
void(entity p) TW_Reset;
void(entity p, float force_all_rl) TW_Activate;
void() TW_Impulse;
void() item_powerup_triple_wheeled;
