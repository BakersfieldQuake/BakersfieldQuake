#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PRACTICE RANGE - definitions (maps/practice.bsp)

Provides passive respawning shooting-range targets for active in-game custom
characters, circling aerial targets (Winged John & Rob Dob) above the Central
Jump Pad, auto-provisioned & fast-refilling guns/ammo, and an optional
Live-Fire Pen toggle.
================
*/

float	practice_active;
float	practice_live_fire;
entity	practice_ctrl;

entity	practice_air_bird;
entity	practice_air_float;
float	practice_air_bird_t;
float	practice_air_float_t;

float	practice_live_t;

// info_practice_target fields
.float	pr_kind;		// archetype ID
.float	pr_patrol_dist;		// half-width of patrol sweep (0 = stationary)
.vector	pr_home;		// initial lane spawn origin
.vector	pr_patrol_dir;		// unit patrol axis
.float	pr_patrol_sign;		// +1 or -1
.float	pr_home_yaw;		// initial facing yaw
.float	pr_respawn_t;		// >0 when waiting to respawn
.float	pr_f0;			// base animation frame
.float	pr_fcount;		// animation frame count
.float	pr_fps;			// animation speed
.float	pr_dir_mode;		// 0=model, 2=8-dir major (d*stride + f0 + k), 3=16-dir robhead
.float	pr_dir_stride;		// stride per direction for mode 2
.float	pr_live_pen;		// TRUE on live-fire pen fighters
.float	pr_items_given;		// player: initial arsenal granted on this life

void() Practice_Precache;
void(entity p) Practice_OnPlayerSpawn;
void() Practice_PlayerFrame;
void() Practice_ToggleLiveFire;
void() info_practice_target;
void() trigger_practice_livefire;
