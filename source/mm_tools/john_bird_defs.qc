/*
================
WINGED BREEZY-HAIR JOHN - FLYABLE VEHICLE (john_bird_defs.qc)

Model: progs/john_bird_head.md3 (7,832 verts, 14,560 tris, 72 frames across 5 clips)
  0..15  : fly_breezy    (cruising wingbeat + breezy hair)
  16..31 : windy_soar    (outstretched thermal glide)
  32..47 : hover_flutter (energetic hover scull + wild hair)
  48..59 : swoop_dive    (high-speed falcon swoop / boost)
  60..71 : perch_breeze  (folded wings perched idle)

Controls:
  H (impulse 86) : Mount perched Winged John / Dismount while flying
  P (impulse 98) : Summon & immediately fly Winged John anywhere (or dismount)
  K (impulse 87) : Toggle 3rd-person chase camera / 1st-person breezy-crown view
  WASD + Mouse   : Fast 3D flight (940 u/s cruise)
  SPACE          : Vigorous upward wing-climb (+540 u/s)
  MOUSE1 (Fire)  : Peregrine Swoop Boost (1,460 u/s) + aerial dive-ram
  V (impulse 20) : Speak random "John" voice line on demand
  impulse 97     : (sv_cheats) Spawn perched Winged John ahead of player
  impulse 99     : (sv_cheats) Spawn fast-circling AI Winged John overhead (5-rocket target practice!)

Durability:
  500 HP — exact 100 damage per direct rocket = 5 rockets to shoot him down!
================
*/

float	JB_MAX_HP			= 500;
float	JB_ROCKET_DMG		= 100;		// 5 rockets * 100 = 500 HP exact shootdown
float	JB_SPEED_CRUISE		= 940;		// fast cruising speed (nearly 3x player run speed)
float	JB_SPEED_SWOOP		= 1460;		// MOUSE1 high-speed falcon swoop boost
float	JB_SPEED_STRAFE		= 580;
float	JB_SPEED_CLIMB		= 540;
float	JB_VOICE_COUNT		= 14;

float	jb_precached;
float	jb_has_birds;
float	jb_inflicting;					// 1 = 5-rocket shootdown blast, 2 = swoop dive-ram

// Player fields
.entity	jb_vehicle;						// Winged John currently piloted by this player
.entity	jb_my_temp;						// Personal summoned Winged John (max 1 per player)
.float	jb_oldmove;
.float	jb_oldsolid;
.float	jb_cam_mode;					// 0 = 3rd-person avian chase cam, 1 = 1st-person crown view
.float	jb_prev_yaw;
.float	jb_cooldown_t;					// brief cooldown after shootdown
.float	jb_prompt_scan_t;
.float	jb_prompt_t;
.entity	jb_prompt_ent;

// Bird vehicle fields
.entity	jb_pilot;						// Player currently flying this bird (world if perched / AI)
.entity	jb_cam;							// Speck camera entity (progs/spike.mdl)
.float	jb_temp;						// TRUE if spawned via impulse, FALSE if map-placed
.float	jb_ai;							// TRUE for impulse 99 fast-circling autopilot bird
.vector	jb_spawn_org;
.float	jb_spawn_yaw;
.float	jb_flap_t;						// next wing-flap SFX timestamp
.float	jb_flap_idx;					// cycles flap1..flap4
.float	jb_voice_t;						// next random "John" voice line timestamp
.float	jb_voice_last1;
.float	jb_voice_last2;
.float	jb_swoop_until;
.float	jb_swoop_cd;
.float	jb_ram_cd;
.float	jb_smoke_t;
.float	jb_anim_clock;
.float	jb_ai_phase;
.entity	jb_last_inflictor;				// deduplicates rocket direct + splash damage in same frame
.float	jb_last_inflictor_t;

void() JohnBird_Precache;
float(entity p) JohnBird_Flying;
float() JohnBird_Frame;
void() JohnBird_ClientGone;
entity(entity p) JohnBird_NearPerched;
void() JohnBird_NearPrompt;
float() JohnBird_TryEnterKey;
void() JohnBird_Impulse;
void() misc_vehicle_johnbird;
