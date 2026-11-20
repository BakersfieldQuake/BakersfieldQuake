#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
CLASSIC QUAKE ROCKET RIDER - FLYABLE SKY-MOUNT (rocket_rider_defs.qc)

2-MD3 V1 Classic Quake Munition assets (packaged in zz_rocketrider.pk3):
  progs/rocket_rider.md3       (rocket_body + flame_fx, 100 frames across 7 clips)
  progs/rocket_rider_rider.md3 (Quake 1 Ranger straddling U-hoop, synced lockstep while mounted)

Animation Schedule (100 frames):
   0..15 : fly_cruise   (14..20 fps, level cruising flight)
  16..31 : fly_boost    (22 fps, Shift / carve afterburner boost)
  32..43 : fly_hover    (12 fps, hover / climb)
  44..55 : swoop_dive   (16 fps, steep downward dive)
  56..67 : idle_ground  (8 fps, parked flush on Z = 0.00 X-fin skids)
  68..83 : hit_flail    (26 fps, 0.65s bucking damage reaction while flying)
  84..99 : skypad_hyper (30 fps, supersonic SkyPad / trigger_push arc)

Controls (bm_veh_binds.cfg compatible):
  H (impulse 86)  : Mount parked Classic Quake Rocket / Dismount in flight
  K (impulse 87)  : Toggle 3rd-person chase camera / 1st-person nose view
  WASD + Mouse    : 3D flight (780 u/s cruise + mouse-carve speed bonus + smooth +-42 deg bank)
  SPACE / Crouch  : Climb (+460 u/s) / Dive (-460 u/s)
  SHIFT (+button4): Rechargeable Afterburner Boost (1,280 u/s)
  M1 (Fire)       : Exhaust flare whistle burst
  impulse 139     : (sv_cheats) Spawn parked Classic Quake Rocket ahead
  impulse 140     : (sv_cheats) Spawn & mount Classic Quake Rocket immediately
================
*/

float	RR_MAX_HP			= 150;
float	RR_LOW_HP			= 60;
float	RR_SPEED_CRUISE		= 780;
float	RR_SPEED_BOOST		= 1280;
float	RR_SPEED_CARVE_MAX	= 440;
float	RR_SPEED_STRAFE		= 500;
float	RR_SPEED_CLIMB		= 460;
float	RR_ABANDON_TIME		= 45;
float	RR_RESPAWN_TIME		= 20;

float	rr_precached;
float	rr_has_rockets;
float	rr_map_spawned;
float	rr_inflicting;				// 1 = shootdown/destruction blast, 2 = high-speed aerial ram

// Cached particle effect indices
float	rr_fx_boost;
float	rr_fx_hairfire;
float	rr_fx_smoke;
float	rr_fx_explode;
float	rr_fx_sparks;
float	rr_fx_teleport;

// Player fields
.entity	rr_vehicle;					// Rocket Rider currently piloted by this player
.entity	rr_my_temp;					// Personal cheat-spawned Rocket Rider
.float	rr_oldmove;
.float	rr_oldsolid;
.float	rr_cam_mode;				// 0 = 3rd-person chase cam, 1 = 1st-person nose view
.float	rr_prev_yaw;
.float	rr_prev_pitch;
.float	rr_prompt_scan_t;
.float	rr_prompt_t;
.entity	rr_prompt_ent;

// Rocket Rider vehicle entity fields
.entity	rr_pilot;					// Player currently flying this rocket (world if parked)
.entity	rr_cam;						// Speck camera entity (progs/spike.mdl)
.entity	rr_riderent;				// Synced Quake 1 Ranger entity (progs/rocket_rider_rider.md3) while mounted
.entity	rr_summoner;				// Owning player for sv_cheats temp spawns
.entity	rr_blast_pilot;				// Pilot ejected during RR_Die -> RR_DieBlast
.entity	rr_last_inflictor;			// Deduplicates direct + splash damage in same frame
.float	rr_last_inflictor_t;
.float	rr_temp;					// TRUE if spawned via cheat impulse, FALSE if map-placed
.float	rr_dying;					// TRUE once RR_Die runs until RR_Respawn
.vector	rr_spawn_org;				// Initial map origin for respawn / abandoned return
.float	rr_spawn_yaw;				// Initial map yaw
.float	rr_anim_clock;
.float	rr_flail_until;				// hit_flail animation expiry (0.65s on RR_Pain while flying)
.float	rr_skypad_until;			// Supersonic SkyPad ballistic arc expiry
.float	rr_pad_scan_t;				// 20 Hz SkyPad / trigger_push scan throttle
.float	rr_carve_spd;				// 0..100 mouse-carve speed gauge
.float	rr_carve_snd_t;
.float	rr_boost_energy;			// 0..100 continuous Shift afterburner gauge
.float	rr_boosting;				// TRUE while Shift afterburner engaged
.float	rr_boost_snd_t;
.float	rr_cam_pull;				// Smoothed 3P camera boost pullback offset
.float	rr_fx_t;					// Nozzle particle emission throttle (~18 Hz)
.float	rr_smoke_t;					// Low-HP / water smoke particle throttle
.float	rr_pain_t;					// Metal hit SFX / HP sprint throttle
.float	rr_ram_cd;					// High-speed aerial ram cooldown
.float	rr_flare_cd;				// M1 exhaust whistle burst cooldown
.float	rr_abandoned_t;				// Timestamp when unmanned map rocket returns to spawn
.float	rr_enter_lock_t;			// Brief post-mount view-angle alignment lock
.float	rr_hud_t;					// Centerprint status bar refresh throttle
.float	rr_hud_key;					// Last centerprint state key (send only on change)
.float	rr_hud_keep;				// Keep-alive resend timestamp so centerprint stays visible

// Forward declaration for SkyPad helper (skypad.qc compiles after rocket_rider.qc)
void(entity pad, entity rr) SkyPad_LaunchRocketRider;

void() RocketRider_Precache;
float(entity p) RocketRider_Flying;
float() RocketRider_Frame;
void(entity p) RocketRider_Reset;
void() RocketRider_ClientGone;
entity(entity p) RocketRider_NearParked;
void() RocketRider_NearPrompt;
float() RocketRider_TryEnterKey;
void() RocketRider_Impulse;
void() RocketRider_MapTick;
void() misc_vehicle_rocketrider;
