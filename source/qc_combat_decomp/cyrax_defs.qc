#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
CYRAX NET LAUNCHER - definitions (Fun Gun Slot 10, FG_CYRAX = 10, BM_FG10 = 19, impulse 70, key L)

Mortal Kombat 3 Cyrax green energy net weapon:
  - Hold Mouse1 to charge (CY_CHARGE_TIME 0.8s); it fires a full net by itself when charged.
    Letting go after CY_MIN_CHARGE fires a smaller, slower net; a tap shorter than that does nothing.
    After a shot the trigger must be released before the next charge (cy_need_release).
  - The net has a small world hull, so it always leaves the muzzle; it catches by proximity
    (CY_CATCH_RADIUS) and splats on walls, staying visible for a moment.
  - Captures ONLY: Players/Bots (and Winged John pilot+bird), Winged John Birds, and Milky Grenades.
  - Pulls the target to CY_HOLD_DIST in front of the shooter's aim along a route that never gets stuck:
    the net's flight line back to the shooter, then the shooter's breadcrumbs (cyrax_crumb), with
    line-of-sight shortcuts, wall sliding, and a short hop forward when no progress is made.
  - The hold lasts cyrax_hold_time seconds (default 8, pull + hold); then the net breaks and they drop free.
  - Trapped players/bots are stunned (no move/jump/fire/weapon-switch) and visually locked to IT_AXE.
  - Clicking Mouse1 while holding/pulling a target equips IT_AXE, plays a snappy 0.30s Bonk Hammer
    wind-up & Tier-3 swing, plays cyrax/bonk_launch.wav + frying_pan.wav, deals 40 dmg (players/birds),
    and launches the target at 1800 u/s along aim (Milky transfers ownership to shooter!).
================
*/

float	CY_CHARGE_TIME		= 0.8;		// hold time for a full net (fires by itself)
float	CY_MIN_CHARGE		= 0.25;		// releasing after this fires a weak net; before it, nothing
float	CY_NET_SPEED		= 1100;		// full net velocity u/s
float	CY_WEAK_SPEED		= 750;		// weak (early release) net velocity u/s
float	CY_NET_SCALE		= 1.7;		// flying net model size (a weak net is 0.7 of this)
float	CY_CATCH_RADIUS		= 96;		// full net proximity catch radius
float	CY_WEAK_RADIUS		= 68;		// weak net proximity catch radius
float	CY_NET_LIFE			= 4.0;		// max projectile flight time
float	CY_SPLAT_TIME		= 0.5;		// a missed net stays stuck to the wall this long
float	CY_HOLD_MAX			= 8.0;		// default capture/pull/hold duration (cvar cyrax_hold_time)
float	CY_PULL_SPEED_FAR	= 320;		// pull speed u/s when far away
float	CY_PULL_SPEED_NEAR	= 150;		// pull speed u/s when arriving
float	CY_HOLD_DIST		= 72;		// suspended distance in front of shooter's aim
float	CY_HOLD_ENTER_DIST	= 88;		// distance from hold point to switch pull -> hold
float	CY_CRUMB_STEP		= 40;		// shooter breadcrumb spacing
float	CY_CRUMB_MAX		= 24;		// max breadcrumbs kept per shooter
float	CY_STUCK_TIME		= 0.3;		// no progress for this long -> hop forward along the route
float	CY_STUCK_DIST		= 8;		// "progress" means moving at least this far
float	CY_BONK_WIND_TIME	= 0.30;		// snappy Bonk Hammer wind-up before launch strike
float	CY_BONK_FOLLOW_TIME	= 0.40;		// Tier-3 swing + follow-through duration
float	CY_BONK_DMG			= 40;		// impact damage for players / Winged John Birds
float	CY_BONK_SPEED		= 1800;		// launch speed along shooter's aim vector
float	CY_BONK_UP			= 140;		// slight upward lift on launch
float	CY_RECOIL_PUSH		= 140;		// shooter pushback on net fire

// progs/v_cyrax.md3 skin ranges (68 skins total: 0..67)
float	CY_VM_IDLE_SKIN		= 0;		// 0..7   (8f)
float	CY_VM_IDLE_COUNT	= 8;
float	CY_VM_CHARGE_SKIN	= 8;		// 8..31  (24f)
float	CY_VM_CHARGE_COUNT	= 24;
float	CY_VM_FIRE_SKIN		= 32;		// 32..43 (12f: 32..36 flash, 37..43 recoil)
float	CY_VM_FIRE_COUNT	= 12;
float	CY_VM_DRAW_SKIN		= 44;		// 44..49 (6f)
float	CY_VM_DRAW_COUNT	= 6;
float	CY_VM_VENT_SKIN		= 50;		// 50..55 (6f)
float	CY_VM_VENT_COUNT	= 6;
float	CY_VM_CATCH_SKIN	= 56;		// 56..67 (12f: dopamine capture celebration)
float	CY_VM_CATCH_COUNT	= 12;

float	CY_FIRE_ANIM_TIME	= 0.36;
float	CY_DRAW_ANIM_TIME	= 0.25;
float	CY_VENT_ANIM_TIME	= 0.42;
float	CY_CATCH_ANIM_TIME	= 0.72;

var float	autocvar_cyrax_test	= 0;	// 1 = allow capturing yourself in solo testing
var float	autocvar_cyrax_hold_time	= 8;	// seconds a net holds its target (pull + hold)
var float	autocvar_cyrax_debug	= 0;	// 1 = print pull distance / hops to the console

// Cached particle effect indices
float	cy_fx_charge_glow;
float	cy_fx_muzzle_flash;
float	cy_fx_muzzle_dust;
float	cy_fx_net_trail;
float	cy_fx_net_capture;
float	cy_fx_bonk_launch;

// Shooter / player fields
.float	cy_charging;		// timestamp when Mouse1 charge began (0 = not charging)
.float	cy_charge_snd_t;	// next allowed charge sound start
.float	cy_charge_fx_t;		// next charge muzzle particle timestamp
.float	cy_fire_t;			// timestamp when net fired
.float	cy_vent_t;			// timestamp when early abort vented
.float	cy_draw_t;			// timestamp when viewmodel raised
.float	cy_catch_t;			// timestamp when dopamine capture animation started
.float	cy_tether_t;		// next green tether particle stream timestamp
.float	cy_empty;			// unused (Cyrax has no reload/empty state)
.entity	cy_vm;				// dedicated viewmodel entity for progs/v_cyrax.md3 skins 0..55
.float	cy_vm_was_on;		// viewmodel tracking flag

// Capture / hold state on shooter
.entity	cy_hold_targ;		// currently netted target (player, bird, or milky)
.entity	cy_hold_wrap;		// progs/cyrax_wrap.md3 entity following target
.float	cy_hold_kind;		// 0=player/bot, 1=Winged John Bird, 2=Milky Grenade
.float	cy_hold_end;		// hold timeout timestamp (cyrax_hold_time)
.float	cy_hold_phase;		// 0=none, 1=pulling, 2=holding ready to bonk
.float	cy_pull_snd_t;		// next periodic pull.wav timestamp
.float	cy_click_ready;		// TRUE once Mouse1 has been released after capture/fire
.float	cy_need_release;	// TRUE after a full-charge shot until Mouse1 is released
.entity	cy_crumbs;			// shooter: oldest breadcrumb (cyrax_crumb chain via .cy_next)
.float	cy_crumb_n;			// shooter: number of breadcrumbs in the chain
.vector	cy_fire_org;		// shooter: where the shooter stood when the net was fired
.float	cy_route_i;			// shooter: route index the victim is heading for (0 = fire origin, 1.. = crumbs)
.entity	cy_next;			// breadcrumb: next (newer) crumb
.vector	cy_last_prog_org;	// victim: position at the last progress check
.float	cy_prog_t;			// victim: time of the last progress check
.float	cy_hops;			// victim: unstick hops used (debug)
.float	cy_route_t;			// shooter: next route shortcut check
.float	cy_dbg_t;			// shooter: next cyrax_debug print
.entity	cy_net;				// shooter: the net in flight (crumbs are dropped while it flies)
.float	cy_radius;			// net projectile: proximity catch radius
.float	cy_splat_t;			// splatted net: time it hit the wall
.float	cy_scale_full;		// net projectile: size it unfurls to (starts small so it doesn't cover your view)

// Bonk-Launch strike state on shooter
.float	cy_bonk_phase;		// 0=off, 1=windup (0.30s), 2=swing follow-through
.float	cy_bonk_t0;			// timestamp when bonk phase started
.float	cy_bonk_hit_at;		// timestamp when bonk impact & launch executes
.float	cy_bonk_end;		// timestamp when swing follow-through ends
.float	cy_bonk_snd;		// TRUE once charge_full.wav played in windup

// Trapped state on target (player, Winged John Bird, or Milky Grenade)
.entity	cy_trapped_by;		// shooter holding this entity in a net
.float	cy_trapped_end;		// expiry timestamp
.float	cy_old_movetype;	// saved movetype before net capture
.float	cy_old_weapon;		// saved player weapon before visual IT_AXE lock
.float	cy_launch_until;	// brief post-launch ballistic immunity from speed clamping / client prediction

// Projectile / wrap entity fields
.entity	cy_targ;			// wrap entity: target being wrapped
.vector	cy_vel;				// net projectile: stored velocity to ignore non-target projectiles

// Forward declarations
void() Cyrax_Precache;
void() Cyrax_Press;
void() Cyrax_Frame;
void() Cyrax_BonkFrame;
void(entity p) Cyrax_ResetPlayer;
void(entity p) Cyrax_ClientGone;
void(entity targ) Cyrax_ReleaseTargetEntity;
float() Cyrax_VictimWeaponFrame;
void() Cyrax_VictimPreThink;
void() Hammer_Body1;
