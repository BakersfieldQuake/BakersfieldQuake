#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
DOOKIE BAZOOKA MK-IV ("OMEGA BFG-9000", Fun Gun Slot 5, FG_DOOKIE = 5, impulse 65, key U)

Caged toxic reactor packed with 5 calm bobbing heads, Chakra turbine wheel, tricolor flags,
orbiting slow flies, and one wildly-waving flying-guy projectile!
  - Hold Fire (`+attack`) to wind up with escalating reactor glow + fast tabla wobble (windup_v6).
  - Release (or hit full charge) to blast with Dhol Slam & Sad Fart Trombone (fire_v5).
  - Launches ONE readable waving fat guy (`progs/dookie_proj.spr32`, 3x16x8 = 384f: horiz + above45 + above90)
    with small orbiting flies, emitting yelling + Bhangra track in 3D flight!
  - Can be shot down mid-air after 0.18s grace, or splatters on impact (`progs/dookie_splat.spr32`)
    with radius mud blast (`mud_splat.wav` + `fly_buzz.wav`) and `fg_inflicting = FG_DOOKIE`.
  - Shooting the ground near your feet bolts you straight up into the air (~3x a rocket jump).

Skins of progs/v_dookie.md3 (114 skins):
  0..59   idle 30 fps loop (2.0s cycle of 5 heads + turbine + flags + tank flies)
  60..75  windup / reactor overpressure charge (16f)
  76..95  blast fire + mud recoil (20f)
  96..113 reload / fresh canister raise (18f)
================
*/

float	DK_VM_IDLE_SKIN		= 0;
float	DK_VM_IDLE_COUNT	= 60;
float	DK_VM_CHARGE_SKIN	= 60;
float	DK_VM_CHARGE_COUNT	= 16;
float	DK_VM_FIRE_SKIN		= 76;
float	DK_VM_FIRE_COUNT	= 20;
float	DK_VM_RELOAD_SKIN	= 96;
float	DK_VM_RELOAD_COUNT	= 18;

float	DK_CHARGE_TIME		= 0.85;		// seconds to full overpressure blast (snappy windup)
float	DK_SPEED_MIN		= 500;		// readable comedy flight speed even at quick release
float	DK_SPEED_MAX		= 780;		// full-charge flight speed
float	DK_LIFE				= 6.5;		// max flight time before mid-air mud detonation
float	DK_HEALTH			= 50;		// shootable out of the air after 0.18s muzzle grace
float	DK_DAMAGE_BASE		= 105;		// base splash damage
float	DK_DAMAGE_CHARGE	= 45;		// extra splash damage at 100% windup (150 max)
float	DK_DIRECT_BONUS		= 25;		// extra direct-hit damage
float	DK_SCALE			= 0.72;		// 112x126 projectile sprite -> ~80u tall in world
float	DK_SPLAT_SCALE		= 1.65;		// 128x128 impact burst scale
float	DK_FOLLOW_TIME		= 0.40;		// 20f blast recoil animation before reload may hide/swap
float	DK_RAISE_TIME		= 0.45;		// raise animation duration (only on draw / actual reload)
float	DK_COOLDOWN			= 0.45;		// post-blast lockout before next windup

float	DK_BOLT_RADIUS		= 185;		// max distance from ground blast for sky-bolt launch
float	DK_BOLT_FULL_DIST	= 115;		// full bolt within this distance (tapers to 0 at DK_BOLT_RADIUS)
float	DK_BOLT_VZ_BASE		= 1350;		// ~3x rocket-jump vertical launch straight into the air
float	DK_BOLT_VZ_CHARGE	= 210;		// bonus vertical boost at 100% windup (1560 max, < sv_maxvelocity 2000)
float	DK_BOLT_SELF_DMG	= 18;		// light RJ-sized self-damage (bm_selfdamage 0.6 -> ~11 HP)

float	DK_SPLAT_LIFE		= 20;		// seconds wall/floor poop splats stay before fading
float	DK_SPLAT_FADE		= 3;		// fade-out duration
float	DK_SPLAT_MAX		= 160;		// max active poop wall/floor splats in map (FIFO cap)
float	DK_SPLAT_TRACES		= 76;		// radial rays splattering walls/floors/ceilings on blast
float	DK_SPLAT_RANGE		= 1150;		// spray reach in units
float	DK_SPLAT_GLOBS		= 44;		// physical flying poop globs arcing out to distant walls

float	dk_splat_count;
entity	dk_splat_qhead;
entity	dk_splat_qtail;
.entity	dk_splat_qprev;
.entity	dk_splat_qnext;
.float	dk_splat_born;
.float	dk_splat_size;
.float	dk_splat_drip;
.vector	dk_splat_n;

.float	dk_charging;		// player: timestamp when windup began (0 = idle)
.float	dk_cool;			// player: earliest next windup timestamp
.float	dk_fire_t;			// player: timestamp of last blast
.float	dk_reload_t;		// player: timestamp when raise/reload animation began
.float	dk_empty;			// player: TRUE while out of ammo
.float	dkvm_on;			// viewmodel entity: TRUE while holding v_dookie.md3

.float	dk_charge;			// projectile: 0..1 charge level
.float	dk_done;			// projectile: TRUE once splatted (prevents double trigger)
.float	dk_yell_t;			// projectile: next mid-air yell timestamp

void() Dookie_Precache;
void() DK_Press;
void() DK_Frame;
void(float c) DK_Launch;
void(entity p) DK_ResetPlayer;
void(entity vm, float is_quad) Dookie_ViewFrame;
