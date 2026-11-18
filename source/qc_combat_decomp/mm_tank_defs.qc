#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
MEGA MAN TANK - shared declarations (Combat+)

Map entity:
  - misc_mm_tank : Drivable, oversized 2-wheel + silver-bar Mega Man Tank!
                   Press H (impulse 86) to climb aboard / exit.
                   W/S drive forward/reverse (~190 u/s max), A/D rotate heavy hull,
                   Mouse smoothly aims 3rd-person chase cam & turret yaw+pitch,
                   MOUSE1 fires rocket-boosted silver bar (fire trail + 150 splash boom + wheel debris),
                   SPACE honks horn & brakes, K (impulse 87) toggles chase camera distance.
                   Perched Wheelman mechanic visibly rebuilds & re-installs the silver bar over ~6s!

Cvars:
  - mm_tank_variant   (1..4, default 1)    : Live-selectable 3D tank prototype (V1..V4)
  - mm_tank_soundpack (0..11, default 0)   : 0 = Official Voted Mix; 1..11 = pack1..pack11
  - mm_tank_boom_mask (default 1793)       : Random boom pool bitmask (1793 = pack1,9,10,11; 0 = active pack)
  - mm_tank_hp        (default 600)        : Tank health (~6 rockets to destroy)
  - mm_tank_respawn   (default 45)         : Seconds after wreck settles before map tank respawns

Impulses:
  - impulse 132 : (sv_cheats 1) Spawn a Mega Man Tank ahead of player
  - impulse 133 : (sv_cheats 1) Spawn & immediately drive a Mega Man Tank right here
  - impulse 134 : Cycle tank prototype 1..4 live
  - impulse 135 : Cycle tank sound pack 0..11 live
================
*/

float	MMT_STATE_IDLE		= 0;
float	MMT_STATE_FIRE		= 1;
float	MMT_STATE_WRECK		= 2;

float	MMT_TOP_FWD			= 190;
float	MMT_TOP_REV			= 130;
float	MMT_ACCEL			= 240;
float	MMT_BRAKE			= 460;
float	MMT_COAST			= 170;
float	MMT_TURN_RATE		= 68;
float	MMT_TURN_ACCEL		= 220;
float	MMT_RELOAD_TIME		= 6.0;
float	MMT_BAR_SPEED		= 1350;
float	MMT_BAR_DMG			= 210;
float	MMT_BAR_DIRECT		= 280;
float	MMT_HALF_RAD		= 104;
float	MMT_BODY_H			= 132;

var float	autocvar_mm_tank_variant	= 1;
var float	autocvar_mm_tank_soundpack	= 0;
var float	autocvar_mm_tank_boom_mask	= 1793;	// 1793 = pack1+pack9+pack10+pack11; 0 = active pack boom.wav; 2047 = all 11
var float	autocvar_mm_tank_hp			= 600;
var float	autocvar_mm_tank_respawn	= 45;

float	mmt_precached;
float	mmt_has_tanks;
float	mmt_inflicting;			// 1 = silver bar blast, 2 = catastrophic tank explosion, 3 = tank ram/crush
float	mmt_debris_count;
float	mmt_last_variant;

float	mmt_fx_bar_trail;
float	mmt_fx_bar_boom;
float	mmt_fx_reload_sparks;
float	mmt_fx_catastrophic;
float	mmt_fx_fire;
float	mmt_fx_smoke;
float	mmt_fx_wreck;
float	mmt_fx_sparks;

// Tank & child entity fields
.float	mmt_state;				// MMT_STATE_*
.float	mmt_variant;			// active prototype 1..4 on this tank
.float	mmt_temp;				// TRUE if spawned via cheat impulse
.float	mmt_fwd_spd;			// current forward/reverse speed along hull heading
.float	mmt_vz;					// vertical velocity when airborne
.float	mmt_air;				// TRUE if airborne off a ledge
.float	mmt_yawrate;			// current hull turn rate (deg/s)
.float	mmt_turret_yaw;			// independent world turret yaw (deg)
.float	mmt_turret_pitch;		// independent turret elevation (+ = up, deg)
.float	mmt_wheel_dist;			// accumulated wheel roll distance for 16f spin
.float	mmt_anim_t;				// hull idle/recoil/flinch accumulator
.float	mmt_flinch_end;			// hull hit-flinch until
.float	mmt_recoil_end;			// hull/turret recoil end
.float	mmt_reload_start;		// timestamp when current 6s reload began
.float	mmt_reload_end;			// timestamp when silver bar is ready again
.float	mmt_reload_snd1;		// played first reload audio
.float	mmt_reload_snd2;		// played second reload audio
.float	mmt_reload_spk_t;		// next reload welding spark timestamp
.float	mmt_reload_lock_snd;	// played lock-in clank
.float	mmt_eng_t;				// next engine loop sound
.float	mmt_move_t;				// next movement loop sound
.float	mmt_horn_t;				// next horn allowed
.float	mmt_fx_t;				// next fire/ember particle tick
.float	mmt_smoke_t;			// next smoke particle tick
.float	mmt_cook_t;				// next burning self-damage tick
.float	mmt_fire_snd_t;			// next fire burn loop sound
.float	mmt_pain_snd_t;			// rate-limit metallic pain clangs
.float	mmt_wreck_t;			// timestamp when wreck embers stop
.float	mmt_respawn_t;			// timestamp when destroyed map tank respawns
.float	mmt_born;				// projectile/debris spawn time
.float	mmt_life;				// debris max lifetime
.float	mmt_bounces;			// debris bounce count
.float	mmt_bouncetime;			// debris bounce sound cooldown
.float	mmt_roll_state;			// wheel debris: 0 = airborne bounce, 1 = ground roll
.float	mmt_roll_yaw;			// wheel debris rolling heading
.float	mmt_roll_spd;			// wheel debris ground speed
.float	mmt_lean;				// wheel debris bank lean angle
.float	mmt_side;				// wheel debris lean side (+1 / -1)
.float	mmt_hit_t;				// per-target ram damage cooldown
.vector	mmt_air_vel;			// carried horizontal air velocity from jump/launch pads
.float	mmt_has_air_vel;		// TRUE while jump/launch pad air velocity is active
.float	mmt_pad_cool;			// next timestamp a jump/launch pad can boost this tank

.vector	mmt_spawn_org;			// original map origin
.vector	mmt_spawn_ang;			// original map angles

.entity	mmt_turret;				// tank -> independent turret entity
.entity	mmt_wheelman;			// tank -> front perched Wheelman mechanic sprite
.entity	mmt_bar_prop;			// tank -> 3D rising/spinning reload bar prop
.entity	mmt_base;				// child -> parent tank
.entity	mmt_driver;				// tank -> player driving
.entity	mmt_igniter;			// tank -> last player who damaged it
.entity	mmt_cam;				// tank -> 3rd-person chase camera entity
.entity	mmt_tank;				// player/projectile -> active tank
.entity	mmt_my_temp;			// player -> personal cheat-spawned tank
.entity	mmt_summoner;			// temp tank -> player who summoned it
.entity	mmt_prompt_ent;			// player -> last tank that showed H prompt
.entity	mmt_blast_infl;			// deduplicate splash hits in same frame
.float	mmt_blast_t;

// Player driving fields
.float	mmt_oldmove;
.float	mmt_oldsolid;
.float	mmt_notarget;
.float	mmt_btn;				// MOUSE1 edge/cooldown helper
.float	mmt_cam_mode;			// 0 = standard chase, 1 = wide chase
.float	mmt_prompt_scan_t;
.float	mmt_prompt_t;
.float	mmt_hint_shown;
.float	mmt_alias_sent;

// Driver clientstats (86..92) for live CSQC aiming trajectory line
.float	mmt_st_active;			// 0 = off, 1 = ready to fire, 2 = reloading
.float	mmt_st_sx;
.float	mmt_st_sy;
.float	mmt_st_sz;
.float	mmt_st_ex;
.float	mmt_st_ey;
.float	mmt_st_ez;

// Shared exact shot-line results from MMT_CalcAim
vector	mmt_aim_muz;
vector	mmt_aim_dir;
vector	mmt_aim_end;
float	mmt_aim_instant;
entity	mmt_aim_hit;

void() MMTank_Precache;
void() MMTank_StartFrame;
float(entity p) MMTank_Driving;
float() MMTank_DriveFrame;
void(entity p) MMTank_Reset;
void() MMTank_ClientGone;
entity(entity p) MMTank_NearFree;
void() MMTank_NearPrompt;
float() MMTank_TryEnterKey;
void() MMTank_Impulse;
void(float v) MMTank_SetVariant;
void(float p) MMTank_SetSoundPack;
void(float mask) MMTank_SetBoomMask;
string(float mask) MMT_BoomMaskSummary;
string(float cur_pack) MMT_PickBoomSound;
void() misc_mm_tank;

// Forward declarations for SkyPad helpers (skypad.qc compiles after mm_tank.qc)
void() SkyPad_RaiseMaxVel;
vector(vector org, vector dst, float apex_z) SkyPad_CalcVel;
