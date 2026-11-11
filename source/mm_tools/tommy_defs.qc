/*
================
THE THOMPSON (stand-alone Day of Defeat 1.3 M1A1 Thompson SMG: impulse 68, keys Z and -).
Full-auto .45 ACP hitscan submachine gun with DoD draw, idle, shoot1/shoot2, and reload animations,
additive muzzle flash, brass shell ejection, third-person held SMG (progs/p_tommy.md3), and CSQC HUD
silhouette (gfx/hud_tommy.tga).

Storage uses FG_TOMMY (fg_ammo8 / BM_FG8) so all 24 item bits stay untouched, while FunGun_Attack and
bm_reload.qc exempt it from fun-gun cooldown locks (bm_fg_lock), underdog reload scaling, and 2.5s
partial-mag auto-reload:
  - Reloads only when pressing R (impulse 41) or hitting 0/30 rounds, playing the full 2.80s DoD reload.
  - Balanced alongside the M4 (12 dmg pinpoint rifle): higher close-range punch (14 dmg @ 0.09s) and
    faster reload (2.80s vs 3.08s), with wider SMG cone + sustained-fire heat bloom.
  - Damage is dealt in the shooter's name with fg_inflicting = FG_TOMMY ("was gunned down by ...'s Thompson").

Frames of v_tommy.md3 (from progs/v_tommy.frames.json):
  0-60 idle (6 fps)   61-86 draw (22.5 fps)   87-150 reload (22.5 fps)
  151-181 shoot1 (25 fps)   182-212 shoot2 (30 fps)   213 empty (1 fps)
DoD sound events: reload clipout at 0.5333s, clipin at 2.2222s; draw slideback on deploy.
================
*/

float	TOM_REFIRE			= 0.09;		// seconds between bullets (~666 RPM)
float	TOM_DAMAGE			= 14;		// close-quarters .45 ACP punch (vs M4's 12)
float	TOM_SPREAD_STAND	= 0.018;	// SMG base cone standing still
float	TOM_SPREAD_MOVE		= 0.030;	// added at full run speed
float	TOM_SPREAD_AIR		= 0.025;	// added while airborne
float	TOM_HEAT_SHOT		= 0.0045;	// spray bloom added per bullet
float	TOM_HEAT_MAX		= 0.050;	// maximum extra spray bloom
float	TOM_HEAT_DECAY		= 0.15;		// spray recovery per second once firing stops
float	TOM_RANGE			= 4096;
float	TOM_RELOAD_TIME		= 2.80;		// 126 source frames at 45 fps
float	TOM_DRAW_LOCK		= 0.55;		// seconds after draw begins before firing is allowed
float	TOM_RECOIL			= 1.3;		// view kick (degrees) per bullet

float	TOM_IDLE_FIRST		= 0;	float	TOM_IDLE_COUNT		= 61;	float	TOM_IDLE_FPS	= 6.0;
float	TOM_DRAW_FIRST		= 61;	float	TOM_DRAW_COUNT		= 26;	float	TOM_DRAW_FPS	= 22.5;
float	TOM_RELOAD_FIRST	= 87;	float	TOM_RELOAD_COUNT	= 64;	float	TOM_RELOAD_FPS	= 22.5;
float	TOM_SHOOT1_FIRST	= 151;	float	TOM_SHOOT1_COUNT	= 31;	float	TOM_SHOOT1_FPS	= 25.0;
float	TOM_SHOOT2_FIRST	= 182;	float	TOM_SHOOT2_COUNT	= 31;	float	TOM_SHOOT2_FPS	= 30.0;
float	TOM_EMPTY_FIRST		= 213;

float	TOM_EVT_CLIPOUT		= 0.5333;
float	TOM_EVT_CLIPIN		= 2.2222;

float	tommy_ok;			// progs/v_tommy.md3 precached and ready

.float	tom_vf_t;			// player: last frame the Thompson was held (a gap = just drawn)
.float	tom_draw_t;			// player: when the current draw began
.float	tom_draw_snd;		// player: 1 once draw slideback sound played
.float	tom_rl_stage;		// player: which reload sounds have played (0..2)
.float	tom_heat;			// player: sustained-fire SMG heat bloom
.float	tom_heat_t;			// player: timestamp of last Thompson shot
.float	tom_alt;			// player: alternates shoot1 / shoot2
.float	tom_shootanim;		// player: 0 none, 1 shoot1, 2 shoot2
.float	tom_shoot_t;		// player: timestamp of last Thompson shot animation
.entity	tom_vwep;			// player: third-person held Thompson seen by other players

void() Tommy_Precache;
void() Tommy_Press;
float() Tommy_Anim;
float(entity p) Tommy_ShowsReload;
string() Tommy_VModel;
void() Tommy_UpdateVwep;
