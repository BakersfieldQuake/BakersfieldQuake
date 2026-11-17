#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
SHOOTABLE / EXPLODABLE 3D VEHICLES - definitions (Combat+)

Four unique early-2000s Bakersfield LAN era vehicles for maps (and spawnable via impulses 81..85; the van can also be
DRIVEN, see vehicle_drive.qc: H = impulse 86 gets in / out, K = impulse 87 camera, 88 = a running van right here, and the
sv_cheats test aids 89 = into the nearest van's cab, 90 = a sedan to ram), plus 3 intense wild-explosion vehicles
spawnable via impulses 91..94:
  1 = misc_vehicle_truck     : Cobalt Blue & Silver 4x4 Extended-Cab Pickup Truck (300 HP)
  2 = misc_vehicle_sedan     : Metallic Emerald Green Late-90s 4-Door Sedan (230 HP)
  3 = misc_vehicle_van       : Fleet Oxford White Ford Econoline Cargo Van (280 HP)
  4 = misc_vehicle_coupe     : Milano Red Early-2000s 2-Door Tuner Sport Coupe (210 HP)
  5 = misc_vehicle_hdtruck   : Flame-Crimson & Gunmetal Heavy-Duty Diesel Dually Rig (380 HP, 6 wheels)
  6 = misc_vehicle_schoolbus : Chrome Yellow Type-C Conventional School Bus (520 HP, 6 wheels)
  7 = misc_vehicle_gtcar     : Liquid Gunmetal V8 Street Muscle Fastback Car (250 HP, 4 wide wheels)

Lifecycle:
  VEH_STATE_IDLE  (0) : Unique mechanical engine idle animation (frames 0..15) + soft engine rumble;
                        metallic bullet sparks + clang & suspension flinch (frames 16..21) when shot.
  VEH_STATE_FIRE  (1) : Below 48% HP -> blistered/scorched skin (skin 1), hood pops ajar & rattles
                        violently (frames 22..35), roaring flames & dark smoke pour from engine bay,
                        cooks off until HP hits 0 (or explodes immediately under heavy fire).
  VEH_STATE_WRECK (2) : Catastrophic fuel-tank explosion -> fireball, 3D shock starburst, radius blast,
                        all 4/6 unique tires bounce & roll away on banked gyroscopic curves, hood/doors/
                        bumpers/signature parts/shrapnel fly & clang everywhere, and the vehicle
                        transforms into a leaping/flipping/rolling crumpled charred hulk!
================
*/

float	VEH_TRUCK		= 1;
float	VEH_SEDAN		= 2;
float	VEH_VAN			= 3;
float	VEH_COUPE		= 4;
float	VEH_HDTRUCK		= 5;
float	VEH_SCHOOLBUS	= 6;
float	VEH_GTCAR		= 7;
float	VEH_GOLFCART	= 8;
float	VEH_TUKTUK		= 9;

float	VEH_STATE_IDLE	= 0;
float	VEH_STATE_FIRE	= 1;
float	VEH_STATE_WRECK	= 2;

var float	autocvar_veh_respawn	= 30;	// > 0: seconds after wreck settles before map vehicle respawns fresh (0 = permanent charred wreck)
var float	autocvar_veh_debug		= 0;	// 1: log the driven van's speed / heading / steering / revs 4x a second (needs developer 1)

float	veh_inflicting;						// TRUE while an exploding vehicle deals T_RadiusDamage (for ClientObituary & chain stagger)
float	veh_fx_fire, veh_fx_smoke, veh_fx_explode, veh_fx_wreck, veh_fx_sparks, veh_fx_boost, veh_fx_drift;

.float	veh_kind;			// 1..7 on shootable vehicles, 0 on everything else
.float	veh_state;			// VEH_STATE_IDLE, VEH_STATE_FIRE, VEH_STATE_WRECK
.float	veh_anim;			// animation frame accumulator
.float	veh_flinch_end;		// timestamp until hit-flinch frames 16..21 finish
.float	veh_snd_t;			// next engine idle / fire loop timestamp
.entity	veh_prompt_van;	// the van whose "press H" prompt he has been shown
.float	veh_prompt_t;
.float	veh_pain_snd_t;		// rate-limit metallic hit sound under high-ROF fire
.float	veh_fx_t;			// next flame / ember particle emission
.float	veh_smoke_t;		// next smoke puff emission
.float	veh_cook_t;			// next cook-off self-damage tick
.float	veh_chain_t;		// > 0: domino chain-reaction detonation timestamp
.float	veh_wreck_t;		// timestamp when lingering wreck embers finish
.float	veh_temp;			// TRUE when spawned dynamically via test impulse 81..85 / 91..94
.entity	veh_igniter;		// player/attacker credited with igniting or blowing up this vehicle
.vector	veh_spawn_org;		// initial map origin (for optional respawn)
.vector	veh_spawn_ang;		// initial map angles
.vector	veh_orig_colormod;	// preserved custom map tint before burn/wreck clears it
.float	veh_has_cm;

// Per-wheel rolling geometry on blown-off tires
.float	veh_wheel_r;		// tire outer radius (16.5 / 13.0 / 14.8 / 12.6 / 18.0 / 17.5 / 13.8)
.float	veh_wheel_hw;		// tire half-width (6.2 / 4.6 / 5.4 / 5.0 / 6.1 / 5.5 / 5.1)
.float	veh_wheel_step;		// circumference / 16 spin frames

// Walk-in interior & driving foundation
.entity	veh_clip_head;		// linked list of child collision clip boxes for walk-in van interior
.entity	veh_driver;			// player currently in the driver's seat
.float	veh_drive_mode;		// TRUE if driver mode is active

// Driving (vehicle_drive.qc). On the van:
.entity	veh_cament;			// the camera entity the driver sees through
.float	veh_steer;			// steering wheel position -1 (full left) .. +1 (full right), eased toward the keys
.float	veh_yawrate;		// degrees/second the body is turning (+ = left, counter-clockwise)
.float	veh_rpm;			// engine speed 0..1, drives the engine note's pitch
.float	veh_boost;			// 0..1: how long he has held the throttle open; the van builds up to a higher top speed
.float	veh_gear;			// 1..5, for the shift dip in the engine note
.float	veh_shift_t;		// end of the post-upshift rev dip
.float	veh_vz;				// vertical speed while airborne (or the ground's rise rate while rolling)
.float	veh_air;			// TRUE while all four wheels are off the ground
.float	veh_eng_t;			// next engine-note grain
.float	veh_eng_ch;			// which of the two grain channels plays next
.float	veh_skid_t;			// next tyre-squeal grain
.float	veh_horn_t;			// horn may sound again at this time
.float	veh_music_t;		// the 6 man LAN van chant is over at this time (restart it then)
.float	veh_smoke_t2;		// next tyre-smoke puff
.float	veh_start_t;		// engine finishes cranking at this time (no drive before)
.float	veh_crash_t;		// rate limit for crash damage/sounds
.float	veh_coast_until;	// > 0 while empty vehicle is ghost-riding / coasting after a high-speed dive-bail
.float	veh_fx_boost_t;		// next turbo exhaust flame/spark emission
.float	veh_land_dip;		// temporary suspension pitch dip on landing
.float	veh_drift_t;		// continuous handbrake drift duration (fuels drift-exit mini-turbo)
// ... on the player:
.entity	veh_van;			// the vehicle he is driving (world = on foot)
.entity	veh_ride;			// the vehicle he is riding in as a drive-by passenger (world = not riding)
.float	veh_seat;			// passenger seat index 1..5 on veh_ride
.entity	veh_last_van;		// vehicle most recently exited via dive-bail / passenger hop
.float	veh_bail_safe_t;	// brief ram & self-blast immunity after diving clear of veh_last_van
.float	veh_oldmove;		// movetype / solid to give back when he gets out
.float	veh_oldsolid;
.float	veh_camera;			// 0 = cockpit view, 1 = chase view (default)
.float	veh_cam_yaw;		// smoothed yaw of the chase camera
.float	veh_cam_pitch;		// smoothed pitch of the chase camera
.float	veh_cam_dist;		// smoothed distance of the chase camera
.float	veh_cam_look;		// smoothed steering lead of the cockpit camera
.float	veh_prompt_scan_t;	// throttle Veh_NearPrompt spatial scan to 10 Hz
.float	veh_hint_shown;		// controls hint shown once per player
// ... on anything a van can hit:
float	veh_boom_t, veh_boom_n;	// recent vehicle explosions (Veh_ExplodeNow): a chain reaction scatters less shrapnel per car
.entity	veh_blast_infl;		// vehicle: the explosion (inflictor) that last hit it, and when: one blast hits it once,
.float	veh_blast_t;		// not once for each of the van's 12 clip boxes in the radius (combat.qc T_Damage)
void(entity v) Veh_FreeClips;
float(entity v, entity p) Veh_ExitSpot;
.float	veh_hit_t;			// a van ran into this at this time (so a body is hit once per pass, not once per frame)

float	veh_runover;		// TRUE while a van deals ram damage (for ClientObituary)

void() Vehicles_Precache;
void() Vehicles_Impulse;
string(float kind) Veh_DisplayName;
float(float kind) Veh_HalfLen;
float(float kind) Veh_HalfWid;
float(float kind) Veh_BodyHeight;
float(entity p) Veh_Driving;				// TRUE while p is at the wheel (custom_effects.qc hides the gun on it)
float(entity p) Veh_Riding;					// TRUE while p is riding shotgun / turret passenger
float() Veh_DriveFrame;						// W_WeaponFrame hook: TRUE while this player is driving (he does nothing else)
void() Veh_PassengerFrame;					// W_WeaponFrame hook: syncs passenger seat & handles H bail while keeping full weapons
void() Veh_SpawnReset;						// PutClientInServer: clear driver/passenger fields cleanly
void(entity v) Veh_SyncPassengers;			// lockstep passenger sync after vehicle moves
void(entity v, float exploding) Veh_AllPassengersBail;
void(entity v, float dt) Veh_CoastStep;		// ghost-riding empty vehicle coast & crash step
void(entity v) Veh_DriveWatch;				// van think: let the driver go if he died or dropped
void(entity v) Veh_DriverBail;				// the van is blowing up: throw the driver out at the seat
void() Veh_ClientGone;					// ClientDisconnect: a driver who drops leaves the van parked
void() Veh_NearPrompt;						// every frame on foot: the "Press H to drive" prompt beside a free van
void() Veh_EnterKey;						// impulse 86 on foot: get in if he is in the driver's seat
float() Veh_VanCustomize;					// customizeentityforclient on the van: the driver's skin (vehicle_drive.qc)
void() Veh_SpawnAndEnter;
void() Veh_TestSeat;						// impulse 89 (sv_cheats): into the nearest van's cab					// impulse 88: a running van right here
void() Veh_TestTarget;					// impulse 90 (sv_cheats): a sedan to ram, 700 units ahead
void() misc_vehicle;
void() misc_vehicle_truck;
void() misc_vehicle_sedan;
void() misc_vehicle_van;
void() misc_vehicle_coupe;
void() misc_vehicle_hdtruck;
void() misc_vehicle_schoolbus;
void() misc_vehicle_gtcar;
void() misc_vehicle_golfcart;
void() misc_vehicle_tuktuk;
