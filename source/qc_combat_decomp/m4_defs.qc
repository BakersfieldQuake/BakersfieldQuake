#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE M4 (stand-alone CS 1.6 style M4A1 rifle: impulse 67, keys C and 0).
Automatic hitscan rifle with the CS 1.6 draw, idle, fire and reload animations, muzzle flash, brass shell ejection,
third-person held rifle (progs/p_m4.md3), and CSQC HUD silhouette (gfx/hud_m4.tga).

Storage uses FG_M4 (fg_ammo7 / BM_FG7) so all 24 item bits stay untouched, while FunGun_Attack and bm_reload.qc exempt
it from fun-gun cooldown locks (bm_fg_lock), underdog reload scaling, and 2.5s partial-mag auto-reload:
  - Reloads only when pressing R (impulse 41) or hitting 0/30 rounds, playing the full 3.08s CS reload animation.
  - Tap/short bursts are pinpoint accurate; sustained full-auto builds CS-style spray bloom that settles when you pause.
  - Damage is dealt in the shooter's name with fg_inflicting = FG_M4 ("was lit up by ...'s M4").

Frames of v_m4.md3 (from progs/v_m4.frames.json):
  0-8 idle (16 fps)   9-39 fire (20 fps)   40-153 reload (37 fps)   154-194 draw (40 fps)
CS sound events: reload clip out at frame 25, clip in at 53, bolt at 88 (of 114); draw deploy at 1, bolt at 17 (of 41).
================
*/

float	M4_REFIRE		= 0.09;		// seconds between bullets (CS 1.6 M4A1 is ~666 RPM)
float	M4_DAMAGE		= 19;		// damage per bullet (clean 8-shot kill on 100HP+100GA DM spawn)
float	M4_SPREAD		= 0.004;	// pinpoint first-shot / tap accuracy standing still
float	M4_SPREAD_BLOOM	= 0.034;	// additional CS-style full-auto spray cone at max sustained fire
float	M4_SPREAD_MOVE	= 0.021;	// extra spread at full run speed (Quake-friendly, -40%)
float	M4_SPREAD_AIR	= 0.015;	// extra spread while airborne / jetpacking (-40%)
float	M4_CLIMB_MAX	= 0.078;	// ~4.5 deg upward recoil climb at max sustained spray (pull down to compensate)
float	M4_RANGE		= 4096;
float	M4_RELOAD_TIME	= 2.10;		// snappy full CS reload animation
float	M4_DRAW_TIME	= 0.25;		// snappy deploy lock
float	M4_RECOIL		= 1.4;		// view kick (degrees) per bullet

float	M4_IDLE_FIRST	= 0;	float	M4_IDLE_COUNT	= 9;	float	M4_IDLE_FPS		= 16;
float	M4_FIRE_FIRST	= 9;	float	M4_FIRE_COUNT	= 31;	float	M4_FIRE_FPS		= 20;
float	M4_RELOAD_FIRST	= 40;	float	M4_RELOAD_COUNT	= 114;
float	M4_DRAW_FIRST	= 154;	float	M4_DRAW_COUNT	= 41;	float	M4_DRAW_FPS		= 74.5;

float	m4_ok;				// progs/v_m4.md3 precached and ready

.float	m4_vf_t;			// player: last frame the M4 was the gun in hand (a gap = it was just drawn)
.float	m4_draw_t;			// player: when the current draw began
.float	m4_draw_stage;		// player: which draw sounds have played (0..2)
.float	m4_rl_stage;		// player: which reload sounds have played (0..3)
.float	m4_bloom;			// player: sustained full-auto spray bloom (0..1)
.float	m4_bloom_t;			// player: timestamp of last M4 shot (drives bloom recovery)
.float	m4_shot_n;			// player: consecutive shots in current burst (drives CS T-pattern horizontal sway)
.entity	m4_vwep;			// player: third-person held M4 rifle seen by other players

void() M4_Precache;
void() M4_Press;
float() M4_Anim;
float(entity p) M4_ShowsReload;
string() M4_VModel;
void() M4_UpdateVwep;
