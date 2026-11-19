#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE POCKET KYLE (Fun Gun Slot 8, FG_KYLE = 8, BM_FG8 = 17, impulse 68, key Z / -)

Kyle Tillet: greedy businessman with giant chrome scissors who always wants a 50% cut!
  - Pull Out (Draw): silent 12-frame surprised pop-up (NO draw voice SFX).
  - Idle: quiet chillin' 24-FPS loop with darting eyes, blinks & occasional casual snip (NO scissor SFX at idle).
  - Hold Mouse1 (Lock-On): frantic 24-FPS scissoring + yelling face + snip SFX; locks onto sky birds/vehicles
    in crosshair cone (0.48s inside 780u hairspray-counter range) or winds up throw power.
  - Release Mouse1 (Yeet Kyle): 42-frame physical throw:
      * Locked-on: Homing Superman-Torpedo Kyle flies nose-first straight at the target with 3D chrome
        scissors chopping out in front (no spin), countering Winged John Bird with 2x snip damage + wing slow!
      * Un-locked throw: flies forward chopping scissors in front (no spin), then sprints chasing nearby enemies!
  - Peripheral Latch: latches right into the victim's forward-side peripheral vision (~34u ahead,
    +/-22u side) for up to 5s (shootable, 35 HP), frantically chopping for 12 dmg / 0.45s while
    erupting realistic US $100 bills, 2024 Washington Silver Quarters & Sacagawea Gold Dollars
    visible to both the victim and everyone in third-person!

Assets (zz_kyle.pk3):
  progs/v_kyle.md3 + v_kyle.md3_0..149.skin + scripts/kylevm.shader
    0..47    Idle (48f @ 24 FPS)
    48..71   Ground Throw Power Wind-Up (24f @ 24 FPS)
    72..95   Horizontal Superman Bird Lock-On (24f @ 24 FPS)
    96..137  42-frame Real Physical Throw + pop-up
    138..149 Pull-out Draw pop-up (12f @ 24 FPS)
  progs/kyle_proj.spr32 (272f: 8 dirs x [8 run + 8 overhead + 8 front + 8 idle] + 8 below + 8 above)
  progs/kyle_torpedo.md3 (8f: horizontal Superman Kyle w/ 3D snapping chrome scissors straight out in front)
  progs/kyle_cash.spr32 (24f: 8 US $100 bills + 8 Silver Quarters + 8 Gold Dollars)
  sound/kyle/ wavs (ZERO "Will stole my clients" clips)
================
*/

float	KY_VM_IDLE_SKIN		= 0;
float	KY_VM_IDLE_COUNT	= 48;
float	KY_VM_LOCK_SKIN		= 48;		// ground throw power windup (skins 48..71)
float	KY_VM_LOCK_COUNT	= 24;
float	KY_VM_BIRDLOCK_SKIN	= 72;		// BRAND-NEW horizontal Superman anti-air bird lock-on (skins 72..95)
float	KY_VM_BIRDLOCK_COUNT= 24;
float	KY_VM_FIRE_SKIN		= 96;		// BRAND-NEW 42-frame 8-stage real physical throwing hand (skins 96..137)
float	KY_VM_FIRE_COUNT	= 42;
float	KY_VM_DRAW_SKIN		= 138;		// pull-out draw pop-up (skins 138..149)
float	KY_VM_DRAW_COUNT	= 12;

float	KY_LOCK_TIME		= 0.48;		// seconds to lock onto sky bird / vehicle inside hairspray range
float	KY_LOCK_BIRD_TIME	= 0.48;		// deliberate, dramatic lock-on animation onto diving Winged John Bird
float	KY_BIRD_LOCK_RANGE	= 780;		// hairspray-counter range (JB spray cone = 520u; far birds > 780u can't be locked!)
float	KY_LOCK_RANGE		= 780;		// max lock-on range (close-range anti-dive counter, not cross-map sniper)
float	KY_WINDUP_MAX_T		= 1.10;		// seconds of holding Mouse1 to reach 100% long-distance throw power
float	KY_THROW_DELAY		= 0.50;		// deep overhand cock-back + forward Superman drive before open-palm release!
float	KY_FOLLOW_TIME		= 1.10;		// splayed follow-through + goose-neck flick + "WHOA!" pop-up
float	KY_DRAW_TIME		= 0.50;		// 12f @ 24 FPS draw pop-up
float	KY_COOLDOWN			= 0.65;		// post-throw cooldown before next windup

float	KY_PLANE_SPEED		= 360;		// base torpedo speed vs slow/hovering targets
float	KY_BIRD_SPEED		= 460;		// minimum torpedo speed vs Winged John Bird (dynamically = bird_speed + 85 u/s!)
float	KY_RUN_SPEED		= 275;		// brisk readable ground chase speed
float	KY_HEALTH			= 35;		// shootable HP (blast him -> explodes into money + bouncing 3D scissors!)
float	KY_LATCH_TIME		= 5.0;		// max latch duration before popping
float	KY_CHOP_INTERVAL	= 0.45;		// seconds between scissor chops while latched
float	KY_CHOP_DMG			= 12;		// damage per chop (24 vs Winged John Bird!)
float	KY_SCALE			= 0.50;		// bold, crystal-clear ~80u tall in world
float	KY_LIFE				= 12.0;		// max lifetime for ground-runner / wander Kyle
float	KY_MAX_ACTIVE		= 4;		// max simultaneous Kyles per owner
float	KY_CASH_MAX			= 42;		// global FIFO cap on fluttering US bills & coins

// Sound attenuation: tighter than ATTN_NORM (1.0 = 1000u) so distant/off-screen Kyles never spam the map
float	KY_ATTN_DEATH		= 1.5;		// ~665u: latch & death pop
float	KY_ATTN_VOICE		= 1.8;		// ~555u: flight/lock voice
float	KY_ATTN_SNIP		= 2.0;		// ~500u: scissor snips, lock ticks, scissor clangs
float	KY_ATTN_ROAM		= 2.2;		// ~455u: ground runner / wander voice lines

// Projectile animation states in progs/kyle_proj.spr32 (272 frames)
float	KY_ANIM_RUN			= 0;		// frames   0..63  (8 dirs x 8f @ 13 FPS)
float	KY_ANIM_OVERHEAD	= 1;		// frames  64..127 (8 dirs x 8f @ 13 FPS)
float	KY_ANIM_FRONT		= 2;		// frames 128..191 (8 dirs x 8f @ 14 FPS)
float	KY_ANIM_IDLE		= 3;		// frames 192..255 (8 dirs x 8f @  8 FPS)
float	KY_ANIM_BELOW		= 4;		// frames 256..263 (from-below sky overhead chop x 8f @ 13 FPS)
float	KY_ANIM_ABOVE		= 5;		// frames 264..271 (from-above top-down chop x 8f @ 12 FPS)

// Projectile AI modes
float	KY_MODE_HOMING		= 1;		// Paper-plane homing in air
float	KY_MODE_RUNNER		= 2;		// Ground sprinting / chasing
float	KY_MODE_LATCHED		= 3;		// Clinging in victim's peripheral vision (or on John Bird)
float	KY_MODE_REGISTER	= 4;		// (unused legacy)
float	KY_MODE_WANDER		= 5;		// Active ground roaming & brief funny shrugs
float	KY_MODE_DYING		= 6;		// Death pop -> explodes into US money + bouncing 3D chrome scissors!

var float	autocvar_kyle_test	= 0;	// 1 = allows locking/latching onto yourself in solo testing
var float	autocvar_kyle_cam	= 0;	// 1 = cinematic 3rd-person follow cam on flying Superman-Torpedo Kyle

.entity	ky_cam;				// active 3rd-person Kyle follow camera (player)
.entity	ky_cam_kyle;		// followed Kyle entity (camera)
.entity	ky_cam_targ;		// hunted bird/target entity (camera)
.float	ky_cam_end;			// timestamp to detach camera after target kill/pop
.vector	ky_cam_last;		// smoothed focus origin after projectile/bird explodes

float	ky_cash_count;
entity	ky_cash_qhead;
entity	ky_cash_qtail;
.entity	ky_cash_qprev;
.entity	ky_cash_qnext;
.float	ky_cash_kind;		// 0 = US $100 bill, 1 = Silver Quarter, 2 = Sacagawea Gold Dollar
.float	ky_cash_phase;

// Player fields
.float	ky_locking;			// timestamp when Mouse1 hold started (0 = idle)
.float	ky_lock_prog;		// 0..1 bird lock-on progress
.float	ky_windup;			// 0..1 throw-distance wind-up charge when not locking onto a bird
.float	ky_bird_locking;	// TRUE while actively locking onto a sky bird/vehicle <= 780u
.float	ky_lock_ready;		// TRUE once bird lock chime played
.float	ky_lock_snip_t;		// next hold-clipping viewmodel snip SFX timestamp
.float	ky_lock_tick_t;		// next lock-on reticle tick SFX timestamp
.float	ky_lock_snd_t;		// cooldown for Bird Lock voice callout
.float	ky_lock_msg_t;		// throttled centerprint timestamp
.entity	ky_lock_ent;		// currently tracked/locked sky bird/vehicle entity
.float	ky_throw_at;		// timestamp when Kyle leaves the hand
.float	ky_fire_t;			// timestamp when throw animation started
.float	ky_threw_t;			// timestamp when Kyle actually launched
.float	ky_draw_t;			// timestamp when Pull-Out Gun draw started
.float	ky_cool;			// earliest next fire timestamp
.float	ky_empty;			// TRUE while out of charges
.float	ky_pending_homing;	// TRUE if release was locked onto ky_pending_targ (launches Superman Torpedo!)
.float	ky_pending_power;	// 0..1 throw power carried across KY_THROW_DELAY
.entity	ky_pending_targ;	// locked bird/vehicle carried across KY_THROW_DELAY
.float	kyvm_on;			// viewmodel entity: TRUE while showing v_kyle.md3

// CSQC HUD clientstats (slots 103..108, bm_match.qc -> csqc/bm_hud.qc)
.float	ky_st_mode;			// 0=off, 1=windup power, 2=locking bird, 3=locked, 4=bird too far (>780u)
.float	ky_st_prog;			// 0..100
.float	ky_st_dist;			// distance in units to aimed bird/vehicle
.float	ky_st_tx;
.float	ky_st_ty;
.float	ky_st_tz;

entity	ky_far_bird;		// scratch global: distant bird (>780u) spotted in aim
float	ky_far_dist;

// Projectile fields
.float	ky_mode;			// KY_MODE_*
.float	ky_anim;			// KY_ANIM_*
.float	ky_anim_t;			// animation phase origin
.float	ky_chop_t;			// next scissor chop damage timestamp
.float	ky_voice_t;			// next Kyle voice line timestamp
.float	ky_latch_end;		// when latch expires
.float	ky_latch_side;		// -1 (left peripheral) or +1 (right peripheral)
.float	ky_trail_t;			// next flight cash trail puff timestamp
.float	ky_wand_yaw;		// wander heading
.float	ky_wand_t;			// next wander direction change
.float	ky_done;			// TRUE once popped
.float	ky_sky_throw;		// TRUE when lobbed up into the sky (overhead sky-chopping arc!)
.float	ky_air_snip_t;		// next mid-air scissor snip SFX timestamp
.float	ky_die_t;			// death pop explosion timestamp
.float	ky_clang_t;			// throttle metallic scissor bounce clang SFX
.float	ky_range_given;		// kyle_range: auto-equipped Pocket Kyle on spawn
.entity	ky_targ;			// latched or pursued target
.vector	ky_reg_pos;			// unused legacy field

entity	ky_range_ctrl;		// practice range controller (only active on map kyle_range)
entity	ky_range_bird;		// circling Winged John Bird on kyle_range
entity	ky_range_enemy;		// patrolling practice enemy on kyle_range
float	ky_range_bird_t;
float	ky_range_enemy_t;

void() Kyle_Precache;
void() KY_Press;
void() KY_Frame;
void(entity p) KY_ResetPlayer;
void(entity p) KY_CleanupOwner;
void(entity vm, float is_quad) Kyle_ViewFrame;
void(vector org, float count, float speed_mult) KY_SpawnCashBurst;
