/*
================
THE SNIPER RIFLE - definitions (Combat+ only; it replaces the nailgun)

Key 4 / IT_NAILGUN is Team Fortress's sniper rifle (TF 2.9 SNIPER.QC / WEAPONS.QC), minus head shots:
	- hold fire to aim: only from (nearly) standing still, SN_START_SPEED. The shot starts at SN_HEAT_START damage and
	  charges SN_HEAT_RATE a second up to SN_HEAT_MAX (TF: +3 a frame); you walk at SN_AIM_SPEED while aiming
	- the view zooms in while you aim (TF autozoom: 90 -> 30 fov) and back out after (cvar sn_autozoom 0 = off);
	  zoomed in, the held rifle is hidden so it doesn't fill the screen
	- a red laser dot (progs/sight.spr) sits where you aim, and everyone can see it
	- let go to fire one hitscan shot of the charge; only with your feet on the ground (let go in the air and the
	  charge is lost); then SN_REFIRE seconds before the next
	- leg shots (below the victim's middle) do x0.5 and slow them 10% a hit, up to 6 hits; a health pickup of
	  health over 95 heals the legs (TF's T_Heal rule; regeneration counts once it passes 95)
	- one nail a shot from the nailgun's LAN magazine (bm_reload.qc), so ammo never really runs out, like TF's 75 shells
Models: progs/v_srifle.mdl (TF's own view model), g_srifle.mdl (pickup), p_srifle.md3 (in the hands); build_srifle.py.
================
*/

float	SN_HEAT_START	= 50;
float	SN_HEAT_MAX		= 400;
float	SN_HEAT_RATE	= 216;		// a second: TF's +3 a frame at 72 frames a second, so ~1.6 s to full
float	SN_FOV_RATE_IN	= 360;		// fov a second: TF's -5 a frame
float	SN_FOV_RATE_OUT	= 576;		// TF's +8 a frame
float	SN_FOV_MIN		= 30;
float	SN_FOV_SCOPE	= 60;		// zoomed in further than this, the held rifle is hidden (it would fill the screen)
float	SN_START_SPEED	= 50;		// TF WEAP_SNIPER_RIFLE_MAX_MOVE
float	SN_AIM_SPEED	= 80;
float	SN_REFIRE		= 1.5;		// TF SNIPER_RIFLE_RELOAD_TIME
float	SN_RANGE		= 8192;
float	SN_LEG_MAX		= 6;

var float	autocvar_sn_autozoom	= 1;

float	sn_inflicting;		// 1 body shot, 2 leg shot: the rifle is dealing damage (obituary)

.float	sn_aiming;			// player: fire is held and the rifle is charging
.float	sn_heat;			// player: the charge (damage of the shot)
.float	sn_fov;				// player: autozoom fov (90 = none)
.float	sn_leg;				// player: leg shots taken (each one is -10% speed)
.float	sn_hp;				// player: health last frame (spots health pickups)
.entity	sn_sight;			// player: their laser dot

void() Sniper_Precache;
void() Sniper_Spawn;
void() Sniper_PlayerFrame;
float(entity p) Sniper_Scoped;
float() Sniper_Frame;
string() Sniper_Death;
