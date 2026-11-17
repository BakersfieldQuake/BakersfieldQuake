#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SHOOTABLE / TIRE-FLYING 3D BICYCLES - definitions (Combat+)

Three distinct Bakersfield 3D bicycles with progressive shoot reactions & flying tires:
  1 = misc_bike_cruiser : "Kern River Cruiser" 26x2.125" Fat Whitewall Cruiser (95 HP)
  2 = misc_bike_bmx     : "#661 Oildale Street BMX" 20x2.4" Freestyle Stunt BMX (85 HP)
  3 = misc_bike_road    : "Kern Canyon Aero 700c" Carbon Drop-Bar Road Racer (80 HP)

Progressive Shoot Lifecycle:
  BIKE_STATE_INTACT   (0) : Parked on kickstand (frames 0..11). Light shots trigger HitSpin
                            (frames 12..27): both tires spin 360 deg & shimmy, handlebars whip,
                            pedals kick backward, spoke ping + brass bell ring + metallic sparks!
  BIKE_STATE_NO_FRONT (1) : Below 58% HP (front hit) -> front tire blasts off & rolls away on
                            banked gyroscopic curves; bare front fork drops onto pavement while
                            rear tire spins continuously in the air (skin 1, frames 28..39 / 40..45).
  BIKE_STATE_NO_REAR  (2) : Below 58% HP (rear hit) -> rear tire blasts off & rolls away; bare
                            rear dropouts slam down while front tire spins & fork wobbles
                            (skin 2, frames 46..57 / 58..63).
  BIKE_STATE_WRECK    (3) : 0 HP -> remaining tire(s), handlebars, saddle, and basket/#661 plate/
                            water bottles fly off; mangled frame flips airborne, slams sideways
                            with sparks, bounces once, and settles flat on the pavement (frames 0..23).

Cheat test impulses (sv_cheats 1):
  - impulse 121 : Spawn Kern River Cruiser ahead of player
  - impulse 122 : Spawn #661 Oildale Street BMX ahead of player
  - impulse 123 : Spawn Kern Canyon Aero 700c Road Racer ahead of player
  - impulse 124 : Spawn all 3 bicycles side-by-side ahead of player
================
*/

float	BIKE_CRUISER		= 1;
float	BIKE_BMX			= 2;
float	BIKE_ROAD			= 3;

float	BIKE_STATE_INTACT	= 0;
float	BIKE_STATE_NO_FRONT	= 1;
float	BIKE_STATE_NO_REAR	= 2;
float	BIKE_STATE_WRECK	= 3;

var float	autocvar_bike_respawn	= 0;	// > 0: seconds after wreck settles before map bicycle respawns (0 = stay wrecked)

float	bikes_precached;
float	bike_fx_sparks;
float	bike_debris_count;

.float	bike_kind;			// 1..3 on shootable bicycles, 0 on everything else
.float	bike_state;			// BIKE_STATE_*
.float	bike_anim;			// animation frame accumulator
.float	bike_flinch_end;	// timestamp until HitSpin or 1-wheel flinch finishes
.float	bike_pain_snd_t;	// rate-limit metallic spoke ping under rapid fire
.float	bike_temp;			// TRUE when spawned dynamically via impulse 121..124
.float	bike_hit_t;			// timestamp of last recorded hit position
.vector	bike_hit_pos;		// world-space impact point (distinguishes front vs rear tire shots)
.vector	bike_spawn_org;		// initial map origin (for optional respawn)
.vector	bike_spawn_ang;		// initial map angles

void() Bikes_Precache;
void() Bicycles_Impulse;
void() misc_bicycle;
void() misc_bike_cruiser;
void() misc_bike_bmx;
void() misc_bike_road;
