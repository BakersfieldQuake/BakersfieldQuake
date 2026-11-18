#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
WINGED BREEZY-HAIR JOHN - FLYABLE VEHICLE & COMBAT DOGFIGHTER (john_bird_defs.qc)

Model: progs/john_bird_head.md3 (7,832 verts, 14,560 tris, 100 frames across 7 clips)
  0..15  : fly_breezy    (cruising wingbeat + breezy hair)
  16..31 : windy_soar    (outstretched thermal glide)
  32..47 : hover_flutter (energetic hover scull + wild hair)
  48..59 : swoop_dive    (high-speed falcon swoop / boost)
  60..71 : perch_breeze  (folded wings perched idle)
  72..87 : combat_fly    (giant waving bangs combat flight)
  88..99 : combat_whip   (mega-bangs pompadour whip-slap)

Props:
  progs/jb_hairspray_can.md3 ("JOHN'S MEGA HOLD" aerosol can)
  progs/jb_match.md3         (giant lit wooden match, frames 0..7)

Controls:
  H (impulse 86) : Mount perched Winged John / Dismount while flying
  P (impulse 98) : Summon & immediately fly Winged John anywhere (or dismount)
  K (impulse 87) : Toggle 3rd-person chase camera / 1st-person breezy-crown view
  WASD + Mouse   : Fast 3D flight (940 u/s cruise)
  SPACE          : Vigorous upward wing-climb (+540 u/s)
  SHIFT (+button4): Peregrine Swoop Boost (1,460 u/s) + aerial dive-ram
  CLICK (Fire)   : Shoot big actively-spraying hairspray can at anything!
  V (impulse 20) : Speak random "John" voice line on demand
  impulse 97     : (sv_cheats) Spawn perched Winged John ahead of player
  impulse 99     : (sv_cheats) Spawn AI dogfighting Winged John overhead!

Durability:
  500 HP — exact 100 damage per direct rocket = 5 rockets to shoot him down!
================
*/

float	JB_MAX_HP			= 250;		// balanced aerial vehicle: ~2-3 rockets or crisp AA gunfire to shoot down
float	JB_ROCKET_DMG		= 100;		// 100 per direct rocket (~3 rockets to shoot down)
float	JB_SPEED_CRUISE		= 780;		// fast cruising speed (~2.4x player run speed)
float	JB_SPEED_SWOOP		= 1220;		// SHIFT (+button4) high-speed falcon swoop boost
float	JB_SPEED_STRAFE		= 500;
float	JB_SPEED_CLIMB		= 460;
float	JB_SLOW_SPEED		= 190;		// on-foot sticky slow horizontal cap (~60% of 320 u/s)
float	JB_BIRD_SLOW_MULT	= 0.58;		// ~42% slower flight when sticky-slowed
float	JB_VOICE_COUNT		= 14;
float	JB_MAX_AMMO			= 6;		// finite hairspray can rack capacity (anti-spam balance)
float	JB_AMMO_RECHARGE_DELAY	= 1.50;	// pause after firing before cans restock
float	JB_AMMO_RECHARGE_TIME	= 3.00;	// seconds per restocked hairspray can

float	jb_precached;
float	jb_has_birds;
float	jb_inflicting;					// 1 = 5-rocket shootdown blast, 2 = swoop dive-ram, 3..7 = combat variants
float	jb_cvar_variant_last;

// Cached particle effect indices
float	jb_fx_hairspray;
float	jb_fx_hairfire;
float	jb_fx_bottle_trail;
float	jb_fx_sticky_foam;
float	jb_fx_feather_boom;
float	jb_fx_mist_burst;
float	jb_fx_mist_cloud;

// Player fields
.entity	jb_vehicle;						// Winged John currently piloted by this player
.entity	jb_my_temp;						// Personal summoned Winged John (max 1 per player)
.entity	jb_summoner;					// on a summoned/projectile entity: owning player
.float	jb_dying;						// bird: JB_Die has run (until JB_Respawn)
.float	jb_feather_t;					// bird: hit feather / HP print throttle
.float	jb_oldmove;
.float	jb_oldsolid;
.float	jb_cam_mode;					// 0 = 3rd-person avian chase cam, 1 = 1st-person crown view
.float	jb_prev_yaw;
.float	jb_cooldown_t;					// brief cooldown after shootdown
.float	jb_prompt_scan_t;
.float	jb_prompt_t;
.entity	jb_prompt_ent;
.float	jb_hint_shown;
.float	jb_variant;						// active combat variant 1..3
.float	jb_slow_t;						// sticky-slow expiry on player/bird
.float	jb_slow_fx_t;					// next sticky foam particle puff
.float	jb_burn_t;						// hairspray fire DoT expiry on player/bird
.float	jb_burn_tick;					// next burn DoT tick
.entity	jb_burn_by;						// attacker who ignited this entity

// CSQC HUD clientstats (slots 93..102)
.float	jb_st_active;					// 93: 0=off, 1=3rd-person, 2=1st-person
.float	jb_st_variant;					// 94: 1..3
.float	jb_st_combat;					// 95: bitmask (1=combat, 2=M1, 4=M3/R, 16=Shift boost)
.float	jb_st_status;					// 96: bitmask (1=slowed, 2=burning, 4=low HP <=200)
.float	jb_st_boost;					// 97: 0..100 boost energy
.float	jb_st_hp;						// 98: 0..500 bird HP
.float	jb_st_hit;						// 99: hit-confirm counter
.float	jb_st_ammo;						// 100: remaining hairspray cans 0..JB_MAX_AMMO
.float	jb_st_ammoprog;					// 101: 0..100 restock progress for next can
.float	jb_st_speed;					// 102: flight airspeed u/s

// Bird vehicle fields
.entity	jb_pilot;						// Player currently flying this bird (world if perched / AI)
.entity	jb_cam;							// Speck camera entity (progs/spike.mdl)
.entity	jb_can_ent;						// Attached hairspray can prop
.entity	jb_match_ent;					// Attached lit match prop
.float	jb_temp;						// TRUE if spawned via impulse, FALSE if map-placed
.float	jb_ai;							// TRUE for impulse 99 dogfighting AI bird
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
.float	jb_boost_energy;				// 0..100 continuous Shift boost gauge
.float	jb_boosting;					// TRUE while Shift boost engaged
.float	jb_boost_snd_t;
.float	jb_ammo;						// remaining hairspray cans on this bird
.float	jb_ammo_regen_t;				// timestamp when next can restocks
.float	jb_dry_snd_t;					// dry-fire click sound throttle
.float	jb_match_on;					// Variant 1 R-key match toggle
.float	jb_match_was;
.float	jb_fire_t;
.float	jb_alt_t;
.float	jb_spray_snd_t;
.float	jb_whip_until;
.float	jb_whip_hit_t;
.float	jb_ai_fire_t;
.float	jb_ai_mode_t;
.float	jb_ai_combat_t;
.float	jb_ai_strafe;
.float	jb_ai_mode;
.float	jb_ai_scan_t;
.float	jb_foam_until;
.float	jb_first_shot_said;				// TRUE after playing "Do you have any hairspray?" on first shot
.entity	jb_last_inflictor;				// deduplicates rocket direct + splash damage in same frame
.float	jb_last_inflictor_t;

void() JohnBird_Precache;
float(entity p) JohnBird_Flying;
float() JohnBird_Frame;
void() JohnBird_DebuffFrame;
void(entity p) JohnBird_Reset;
void() JohnBird_ClientGone;
entity(entity p) JohnBird_NearPerched;
void() JohnBird_NearPrompt;
float() JohnBird_TryEnterKey;
void() JohnBird_Impulse;
void() misc_vehicle_johnbird;
