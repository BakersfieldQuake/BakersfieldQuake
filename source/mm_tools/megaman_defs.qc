/*
================
THE MEGA MAN GUN

Its own weapon (IT_MEGAMAN, impulse MM_IMPULSE); every player carries it.
Shared by the vanilla (BakersfieldMemes) and Combat+ (BakersfieldQuake) builds;
Combat+ compiles it with COMBATPLUS defined.
Holds MM_MAX_AMMO Mega Men that recharge over time.

Throw one and it flies out, lands on its wheels and goes straight for the nearest
enemy anywhere on the map (round walls and corners, since it steers round them). In plain
sight it hops up with a blast of its horn, chases, and when close enough crouches
and leaps on them like a headcrab: only touching an enemy sets it off. Out of road
(walls head on cost one of its MM_MAX_BOUNCES, or the time is up) it just falls apart
harmlessly: a bang with nobody there is confusing.

mm_state: 0 = airborne (thrown, hopping or leaping), 1 = driving, 2 = crouched to leap
================
*/

float	IT_MEGAMAN		= 128;		// IT_EXTRA_WEAPON, unused by id
float	MM_IMPULSE		= 14;		// "impulse 14" selects it

#ifndef COMBATPLUS
// Darkplaces extensions the id code doesn't declare (Combat+ already has them)
void(entity e, float chan, string samp, float vol, float atten, float speed, float flags) sound7 = #8;
void(entity e, entity tagentity, string tagname) setattachment = #443;
float(float f) sin = #60;
float(float f) cos = #61;
void(vector v1, vector mins, vector maxs, vector v2, float nomonsters, entity forent) tracebox = #90;
.float	scale;
.entity	exteriormodeltoclient;
#endif

float	mm_inflicting;		// TRUE while a Mega Man is dealing damage (for the obituary)
float	mm_los;				// MegaMan_FindTarget: the enemy it returned is in plain sight (else it only knows where they are)
float	mm_precached_mask;	// bitmask of precached mm_variant viewmodels
float	mm_variant_cached;	// cached floor(cvar("mm_variant"))
float	mm_variant_t;		// next cvar("mm_variant") refresh time

void() BecomeExplosion;
void() W_SetCurrentAmmo;
void() player_mm1;
void() MegaMan_Precache;
string() MM_PickVModel;
void() MegaMan_Attack;
void() MegaMan_Select;
void(entity p) MegaMan_Give;
void() MegaMan_ViewFrame;

.float	mm_state;
.float	mm_dist;		// distance rolled so far; picks the wheel-spin frame (16 per revolution)
.float	mm_born;
.float	mm_stuck;		// consecutive ticks airborne without moving
.vector	mm_lastorg;
.float	mm_bounces;		// head-on wall hits used so far
.float	mm_bouncetime;	// when the last one was counted
.float	mm_heading;		// direction it drives when it has nobody to chase
.float	mm_side;		// which way it prefers to go round obstacles (1 = left, -1 = right)
.float	mm_motor;		// when to play the motor sound next
.entity	mm_target;		// who it is chasing
.float	mm_leap_t;		// earliest time it may leap again
.float	mm_crouch_t;	// when the crouch ends and the leap starts
.float	mm_life;		// wreckage: seconds before it is cleared away
.float	mm_lean;		// wheel/bar wreckage: camber lean angle (deg)
.float	mm_speed;		// wheel/bar wreckage: ground rolling speed (u/s)
.float	mm_roll_yaw;	// wheel/bar wreckage: ground rolling heading (deg)
.float	mm_hops;		// hops up steps since it last drove freely
.float	mm_freeticks;	// ticks driven without being blocked
.float	mm_fire_t;		// player: when the throw started
.float	mm_launch_t;	// player: when Mega Man leaves the hand
.float	mm_pending;		// player: throw in progress
.float	mm_ammo;		// player: Mega Men in hand
.float	mm_regen_t;		// player: when the next one recharges
.float	mm_larry_t;		// player: the Larry clip playing now ends then
.float	mm_detour_yaw;	// Mega Man: the way round the wall he last found (MM_OpenYaw), reused while it stays clear
.float	mm_detour_t;	// Mega Man: until when that detour may be reused before a fresh search
.float	mm_vm_var;		// player: mm_variant + 1 of the view model last set up (0 = not holding the gun); an inspect resets only when it changes
.float	mm_inspect_t;	// player: when the current CoD weapon inspect started (0 = none)
.float	mm_inspect_kind;// player: 1 = CoD Hold-Out (37..60), 2 = CoD Clean-Bar (61..88)
.float	mm_next_inspect;// player: next random idle CoD weapon inspect timestamp
.float	mm_glint_ding;	// player: TRUE once the frame-82 chrome star-glint ting played
.entity	mm_vwep;		// player: the little Mega Man other people see in your hand

float	MM_DRIVE_STEP	= 19.25;	// units per 0.05s tick (385 u/s — faster than 320 u/s players!)
float	MM_WHEEL_FRAME	= 4.7;		// units rolled per frame (wheel radius 12, 16 frames)
float	MM_LIFETIME		= 30;		// seconds before it gives up and falls apart
float	MM_MAX_BOUNCES	= 8;		// head-on wall hits before it falls apart
float	MM_LOOK			= 160;		// how far ahead it looks for walls
float	MM_TURN_CRUISE	= 4;		// degrees per tick when nothing is in the way
float	MM_TURN_AVOID	= 14;		// degrees per tick when steering round a wall
float	MM_TURN_CHASE	= 12;		// degrees per tick when running down an enemy
float	MM_SEEK_RANGE	= 4000;		// how far it can sense an enemy (the whole map): it heads for the nearest one
float	MM_LEAP_RANGE	= 300;		// leaps at enemies this close
float	MM_PROXIMITY	= 40;		// detonate this close to an enemy
float	MM_DRIVE_LEN	= 3.42;		// length of the driving sound; it restarts as it ends
float	MM_HEALTH		= 40;		// how much shooting it takes to stop him
float	MM_MAX_AMMO		= 2;
float	MM_REGEN_TIME	= 5;		// seconds per Mega Man recharged


