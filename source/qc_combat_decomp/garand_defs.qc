#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE M1 GARAND (stand-alone Day of Defeat 1.3 M1 Garand rifle: impulse 69, keys M and =).
Semi-automatic .30-06 battle rifle with an 8-round en-bloc clip that visibly ejects and PINGS out on
the 8th shot, DoD draw/draw_empty, idle/empty_idle, shoot1/shoot2/shoot_empty, and reload animations,
transparent rear aperture sight, muzzle flash, brass ejection, third-person held rifle (progs/p_garand.md3),
and CSQC HUD silhouette (gfx/hud_garand.tga).

Storage uses FG_GARAND (fg_ammo9 / BM_FG9):
  - True semi-auto: trigger must be released between shots (.gar_ready).
  - Firing the 8th round plays shoot_empty (0.66s clip-ejection) + garand_reload_clipding.wav ("PING!"),
    then automatically transitions into the 1.92s DoD en-bloc reload (or press R early).
  - Balanced alongside the M4: 48 dmg per round (clean 3-shot kill through 100HP + 100 green armor),
    pinpoint standing accuracy (0.003), and crisp battle-rifle recoil.
  - Damage is dealt in the shooter's name with fg_inflicting = FG_GARAND ("was picked off by ...'s M1 Garand").

Frames of v_garand.md3 (from progs/v_garand.frames.json):
  0-60 idle (5 fps)   61-86 draw (20 fps)   87-112 drawe (20 fps)
  113-138 shoot1 (25 fps)   139-164 shoot2 (25 fps)   165-187 shoote (33.3333 fps)
  188-236 reload (25 fps)   237 empty (1 fps)
DoD sound events: reload clipin at 0.9600s; last-round clipding on 8th shot; rifleselect on deploy.
================
*/

float	GAR_REFIRE				= 0.28;		// seconds between semi-auto shots (~196 DPS)
float	GAR_DAMAGE				= 55;		// .30-06 punch (3-shots 100HP+100GA DM spawn cleanly)
float	GAR_SPREAD_STAND		= 0.003;	// pinpoint standing rifle accuracy
float	GAR_SPREAD_MOVE			= 0.025;	// added at full run speed
float	GAR_SPREAD_AIR			= 0.020;	// added while airborne
float	GAR_RANGE				= 4096;
float	GAR_SHOOT_EMPTY_TIME	= 0.32;		// snappy clip-eject PING beat before auto-reload begins
float	GAR_RELOAD_TIME			= 1.92;		// 96 source frames at 50 fps
float	GAR_DRAW_LOCK			= 0.22;		// snappy draw lock before firing is allowed
float	GAR_RECOIL				= 3.8;		// crisp semi-auto battle-rifle view kick

float	GAR_IDLE_FIRST		= 0;	float	GAR_IDLE_COUNT		= 61;	float	GAR_IDLE_FPS	= 5.0;
float	GAR_DRAW_FIRST		= 61;	float	GAR_DRAW_COUNT		= 26;	float	GAR_DRAW_FPS	= 20.0;
float	GAR_DRAWE_FIRST		= 87;	float	GAR_DRAWE_COUNT		= 26;	float	GAR_DRAWE_FPS	= 20.0;
float	GAR_SHOOT1_FIRST	= 113;	float	GAR_SHOOT1_COUNT	= 26;	float	GAR_SHOOT1_FPS	= 25.0;
float	GAR_SHOOT2_FIRST	= 139;	float	GAR_SHOOT2_COUNT	= 26;	float	GAR_SHOOT2_FPS	= 25.0;
float	GAR_SHOOTE_FIRST	= 165;	float	GAR_SHOOTE_COUNT	= 23;	float	GAR_SHOOTE_FPS	= 33.3333;
float	GAR_RELOAD_FIRST	= 188;	float	GAR_RELOAD_COUNT	= 49;	float	GAR_RELOAD_FPS	= 25.0;
float	GAR_EMPTY_FIRST		= 237;

float	GAR_EVT_CLIPIN		= 0.9600;

float	garand_ok;			// progs/v_garand.md3 precached and ready

.float	gar_vf_t;			// player: last frame the Garand was held (a gap = just drawn)
.float	gar_draw_t;			// player: when the current draw began
.float	gar_draw_empty;		// player: 1 if drawn with an empty clip
.float	gar_draw_snd;		// player: 1 once rifleselect played
.float	gar_rl_stage;		// player: 1 once garand_reload_clipin played
.float	gar_ready;			// player: 1 once +attack released since last Garand shot (semi-auto gate)
.float	gar_alt;			// player: alternates shoot1 / shoot2
.float	gar_shootanim;		// player: 0 none, 1 shoot1, 2 shoot2, 3 shoote (8th-round clip eject)
.float	gar_shoot_t;		// player: timestamp of last Garand shot
.float	gar_empty_t;		// player: timestamp when 8th shot emptied clip (delays auto-reload for 0.66s shoote)
.entity	gar_vwep;			// player: third-person held M1 Garand seen by other players

void() Garand_Precache;
void() Garand_Press;
float() Garand_Anim;
float(entity p) Garand_ShowsReload;
string() Garand_VModel;
void() Garand_UpdateVwep;
