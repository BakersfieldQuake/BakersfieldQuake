#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
PRACTICE RANGE - definitions (maps/practice.bsp)

Wide-open empty practice arena with a central jump-pad hole, 1 walking
non-shooting enemy player model, 1 Mega Man Tank, 1 Go-Kart, and each powerup.
================
*/

float	practice_active;
float	practice_live_fire;
entity	practice_ctrl;

entity	practice_enemy;
float	practice_enemy_t;
float	practice_live_t;

// info_practice_target / practice enemy fields
.float	pr_kind;		// archetype ID
.float	pr_patrol_dist;		// half-width of patrol sweep (0 = stationary)
.vector	pr_home;		// initial spawn origin
.vector	pr_patrol_dir;		// unit patrol axis
.float	pr_patrol_sign;		// current waypoint index / patrol sign
.float	pr_home_yaw;		// initial facing yaw
.float	pr_respawn_t;		// >0 when waiting to respawn
.float	pr_f0;			// base animation frame
.float	pr_fcount;		// animation frame count
.float	pr_fps;			// animation speed
.float	pr_dir_mode;		// 0=model, 2=8-dir major, 3=16-dir robhead
.float	pr_dir_stride;		// stride per direction for mode 2
.float	pr_live_pen;		// legacy live-fire pen flag
.float	pr_items_given;		// player: initial arsenal granted on this life
.float	pr_stuck_t;		// enemy patrol stall timer

void() Practice_Precache;
void(entity p) Practice_OnPlayerSpawn;
void() Practice_PlayerFrame;
void() Practice_ToggleLiveFire;
void() info_practice_target;
void() trigger_practice_livefire;
