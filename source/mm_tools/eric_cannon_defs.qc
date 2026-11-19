/*
================
THE ERIC DEASON CANNON — shared declarations (Combat+)

Map entity:
  - misc_eric_cannon : Walk-around 94u monument cannon with radar-twitching giant ears.
                       Press H (impulse 86) to mount & aim 360 deg, MOUSE1 for hilarious
                       Wew-Cannon rubber wind-up/blast + modest-volume canislupusfantasy2.wav,
                       soar ~2600u high in 3rd-person guided sky flight, and kamikaze-land in a
                       rocket explosion showering 30+ bouncing CRT monitors, ATX PCs & PC parts!

Cheat / test impulses (sv_cheats 1):
  - impulse 128 : Spawn THE ERIC DEASON CANNON 150u ahead of player (walk around & press H)
  - impulse 129 : Spawn & immediately mount THE ERIC DEASON CANNON right here
================
*/

float	EC_STATE_IDLE		= 0;
float	EC_STATE_MOUNTED	= 1;
float	EC_STATE_WINDUP		= 2;
float	EC_STATE_FLYING		= 3;
float	EC_STATE_RELOAD		= 4;

float	EC_YOKE_Z			= 24.0;
float	EC_CANNON_Z			= 56.8;
float	EC_REST_PITCH		= 15.6;
float	EC_RELOAD_TIME		= 40.0;
float	EC_WATCH_TIME		= 3.5;

float	ec_precached;
float	ec_has_cannons;
float	ec_debris_count;
float	ec_inflicting;			// 1 = kamikaze rider blast, 2 = orbital enemy kill
float	ec_fx_smoke;
float	ec_fx_rocket;
float	ec_fx_rocket_classic;
float	ec_fx_nuke_trail;
float	ec_fx_nuke_flash;
float	ec_fx_nuke_shock;
float	ec_fx_nuke_mushroom;

// Fields on misc_eric_cannon (base), ec_tube, and player
.entity	ec_yoke;				// base -> yawing elevation yoke entity
.entity	ec_tube;				// base -> launching barrel + Eric head + giant ears entity
.entity	ec_base;				// tube -> parent street tripod base
.entity	ec_pilot;				// base -> mounted / flying player
.entity	ec_cannon_ent;			// player -> mounted / flying misc_eric_cannon base
.entity	ec_cam;					// player -> 3rd-person aim / flight / crater watch camera
.entity	ec_my_temp;				// player -> personal cheat-spawned cannon (recycled cleanly)
.entity	ec_summoner;			// base -> player who cheat-spawned this temp cannon
.entity	ec_prompt_ent;			// player -> last cannon that showed the H prompt
.entity	ec_return_base;			// player -> pedestal base to return next to after watch-cam

.float	ec_state;				// EC_STATE_*
.float	ec_temp;				// TRUE if spawned via impulse 128/129
.float	ec_yaw;					// current turret yaw (deg)
.float	ec_pitch;				// current turret elevation pitch (+ = skyward, deg)
.float	ec_fly_yaw;				// guided airborne heading yaw (deg)
.float	ec_prev_yaw;			// previous frame yaw for roll banking
.float	ec_phase_t;				// timestamp when current phase (windup / flight) began
.float	ec_boomed;				// TRUE once blastboom fired during windup
.float	ec_screamed;			// TRUE once apex Doppler scream played
.float	ec_dive_snd_t;			// next dive whistle sound timestamp
.float	ec_wind_snd_t;			// next sky wind loop timestamp
.float	ec_flap_snd_t;			// (legacy, unused)
.float	ec_smoke_t;				// next rocket exhaust trail puff timestamp
.float	ec_anim_clock;			// smooth animation frame accumulator
.float	ec_btn;					// latch for MOUSE1 edge detection
.float	ec_oldmove;				// saved player movetype
.float	ec_oldsolid;			// saved player solid
.float	ec_oldtakedmg;			// saved player takedamage
.float	ec_notarget;			// TRUE if we added FL_NOTARGET to player
.float	ec_watch_until;			// player watches impact crater until this timestamp
.float	ec_prompt_scan_t;		// throttle proximity scan
.float	ec_prompt_t;			// cooldown before repeating centerprint on same cannon
.float	ec_hint_shown;			// TRUE once full control hint shown this match
.float	ec_nuke_stage;			// multi-stage nuclear detonation step
.float	ec_nuke_t0;				// detonation start timestamp
.float	ec_nuke_ceil;			// ceiling clearance above ground zero for rising mushroom cloud
.float	ec_return_yaw;			// saved pedestal heading to restore after watch-cam
.vector	ec_boomat;				// impact crater origin for watch-cam
.vector	ec_hitnorm;				// surface normal from flight trace
.vector	ec_prev_nozzle;			// previous frame rear nozzle position for continuous contrail
.vector	ec_return_pos;			// saved safe pedestal exit position after watch-cam

void() EricCannon_Precache;
float(entity p) EricCannon_Active;
float() EricCannon_Frame;
void(entity p) EricCannon_Reset;
void() EricCannon_ClientGone;
entity(entity p) EricCannon_NearIdle;
void() EricCannon_NearPrompt;
float() EricCannon_TryEnterKey;
void() EricCannon_Impulse;
void() misc_eric_cannon;
