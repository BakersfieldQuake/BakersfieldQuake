/*
================
DOOKIE BAZOOKA MK-IV ("OMEGA BFG-9000", Fun Gun Slot 5, FG_DOOKIE = 5, impulse 65, key U)

Caged toxic reactor packed with 5 calm bobbing heads, Chakra turbine wheel, tricolor flags,
orbiting slow flies, and one wildly-waving flying-guy projectile!
  - Hold Fire (`+attack`) to wind up with escalating reactor glow + fast tabla wobble (windup_v6).
  - Release (or hit full charge) to blast with Dhol Slam & Sad Fart Trombone (fire_v5).
  - Launches ONE readable waving fat guy (`progs/dookie_proj.spr32`, 16 angles x 8 frames)
    with small orbiting flies, emitting yelling + Bhangra track in 3D flight!
  - Can be shot down mid-air after 0.18s grace, or splatters on impact (`progs/dookie_splat.spr32`)
    with radius mud blast (`mud_splat.wav` + `fly_buzz.wav`) and `fg_inflicting = FG_DOOKIE`.

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

float	DK_CHARGE_TIME		= 1.45;		// seconds to full overpressure blast (matches windup_v6.wav 1.5s)
float	DK_SPEED_MIN		= 430;		// readable comedy flight speed even at quick release
float	DK_SPEED_MAX		= 720;		// full-charge flight speed
float	DK_LIFE				= 6.5;		// max flight time before mid-air mud detonation
float	DK_HEALTH			= 50;		// shootable out of the air after 0.18s muzzle grace
float	DK_DAMAGE_BASE		= 85;		// base splash damage
float	DK_DAMAGE_CHARGE	= 35;		// extra splash damage at 100% windup
float	DK_DIRECT_BONUS		= 25;		// extra direct-hit damage
float	DK_SCALE			= 0.72;		// 112x126 projectile sprite -> ~80u tall in world
float	DK_SPLAT_SCALE		= 1.25;		// 128x128 impact burst scale
float	DK_FOLLOW_TIME		= 0.50;		// 20f blast recoil animation before reload may hide/swap
float	DK_RAISE_TIME		= 0.55;		// raise animation duration
float	DK_COOLDOWN			= 0.65;		// post-blast lockout before next windup

float	DK_SPLAT_LIFE		= 16;		// seconds wall/floor poop splats stay before fading
float	DK_SPLAT_FADE		= 3;		// fade-out duration
float	DK_SPLAT_MAX		= 80;		// max active poop wall/floor splats in map (FIFO cap)
float	DK_SPLAT_TRACES		= 48;		// radial rays splattering walls/floors/ceilings on blast
float	DK_SPLAT_RANGE		= 950;		// spray reach in units
float	DK_SPLAT_GLOBS		= 28;		// physical flying poop globs arcing out to distant walls

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
