#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
CYRAX NET LAUNCHER - definitions (Fun Gun Slot 10, FG_CYRAX = 10, BM_FG10 = 19, impulse 70, key L)

Mortal Kombat 3 Cyrax green energy net weapon:
  - Hold Mouse1 for 1.8s (CY_CHARGE_TIME) to charge; auto-fires immediately at 1.8s.
  - Releasing Mouse1 early (< 1.8s) aborts charge, plays cyrax/vent.wav, vents green dust, spends NO ammo.
  - Captures ONLY: Players/Bots (and Winged John pilot+bird), Winged John Birds, and Milky Grenades.
  - Pulls target (~240 u/s) to ~80u in front of shooter's aim, then suspends up to 30.0s.
  - Trapped players/bots are stunned (no move/jump/fire/weapon-switch) and visually locked to IT_AXE.
  - Clicking Mouse1 while holding/pulling a target equips IT_AXE, plays a snappy 0.30s Bonk Hammer
    wind-up & Tier-3 swing, plays cyrax/bonk_launch.wav + frying_pan.wav, deals 40 dmg (players/birds),
    and launches the target at 1800 u/s along aim (Milky transfers ownership to shooter!).
================
*/

float	CY_CHARGE_TIME		= 1.8;		// full hold time required to fire
float	CY_NET_SPEED		= 950;		// projectile velocity u/s
float	CY_NET_LIFE			= 4.0;		// max projectile flight time
float	CY_HOLD_MAX			= 30.0;		// max capture/pull/hold duration
float	CY_PULL_SPEED		= 240;		// pull speed u/s toward hold point
float	CY_HOLD_DIST		= 80;		// suspended distance in front of shooter's aim
float	CY_HOLD_ENTER_DIST	= 88;		// distance from hold point to switch pull -> hold
float	CY_BONK_WIND_TIME	= 0.30;		// snappy Bonk Hammer wind-up before launch strike
float	CY_BONK_FOLLOW_TIME	= 0.40;		// Tier-3 swing + follow-through duration
float	CY_BONK_DMG			= 40;		// impact damage for players / Winged John Birds
float	CY_BONK_SPEED		= 1800;		// launch speed along shooter's aim vector
float	CY_BONK_UP			= 140;		// slight upward lift on launch
float	CY_RECOIL_PUSH		= 140;		// shooter pushback on net fire

// progs/v_cyrax.md3 skin ranges (56 skins total: 0..55)
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

float	CY_FIRE_ANIM_TIME	= 0.52;
float	CY_DRAW_ANIM_TIME	= 0.25;
float	CY_VENT_ANIM_TIME	= 0.42;

var float	autocvar_cyrax_test	= 0;	// 1 = allow capturing yourself in solo testing

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
.float	cy_empty;			// TRUE while out of ammo after fire/vent anim
.entity	cy_vm;				// dedicated viewmodel entity for progs/v_cyrax.md3 skins 0..55
.float	cy_vm_was_on;		// viewmodel tracking flag

// Capture / hold state on shooter
.entity	cy_hold_targ;		// currently netted target (player, bird, or milky)
.entity	cy_hold_wrap;		// progs/cyrax_wrap.md3 entity following target
.float	cy_hold_kind;		// 0=player/bot, 1=Winged John Bird, 2=Milky Grenade
.float	cy_hold_end;		// 30s timeout timestamp
.float	cy_hold_phase;		// 0=none, 1=pulling, 2=holding ready to bonk
.float	cy_pull_snd_t;		// next periodic pull.wav timestamp
.float	cy_click_ready;		// TRUE once Mouse1 has been released after capture/fire

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
