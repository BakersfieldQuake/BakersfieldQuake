#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
THE JETPACK - definitions (Combat+ only)

Duke Nukem 3D's jetpack. One sits next to every yellow armor in every map (item_armor2, see Jetpack_ForArmor).
	- touch it: you get JP fuel (autocvar_jp_fuel seconds, refilled if you already have some). It respawns
	  autocvar_jp_respawn seconds later. You can't pick one up while your tank is full
	- in the air, press jump again (or press J, impulse 71, any time) and the jetpack lights: "they seem to be
	  floating" plays, gravity is off, and you hover. Hold jump to climb. J (or landing, or running dry) turns it off
	- the fuel drains while it is lit: 1 a second climbing, half that hovering
	- a swoosh loops while it burns (jetpack/swoosh.wav), with flames under your feet
	- it is gone when you die
Model/sound: progs/jetpack.md3 and sound/jetpack/swoosh.wav (build_jetpack_assets.py). The "floating" voice is funny/imfloating.wav ("I'm floating"), boosted.
================
*/

var float	autocvar_jp_fuel	= 40;		// seconds of fuel a pickup gives
var float	autocvar_jp_hover	= 0.8;		// fuel used per second while hovering (climbing uses 1 a second)
var float	autocvar_jp_respawn	= 30;		// seconds before a taken jetpack comes back

float	JP_CLIMB	= 260;		// climb speed while jump is held
float	JP_DOWN		= 220;		// descent speed while crouch is held
float	JP_SINK		= 110;		// with no keys held you sink this fast (review 2026-10-31: "let go and do nothing, I should float down faster")
float	JP_DTAP		= 0.32;		// two jump presses this close together ignite in mid-air or switch off
float	JP_SPEED	= 320;		// sideways speed: as fast as a player runs (Quake's own air control is about 30 and can't steer)
float	JP_STEER	= 4;		// how quickly you reach it (1/s: about a quarter of a second)
float	JP_BRAKE	= 2.5;		// how quickly you slow to a hover when you let go of the move keys
float	JP_ACCEL	= 1400;		// how fast it gets there (and brakes to a hover)
float	JP_MAXSPEED	= 1150;		// top sideways speed after holding forward a while
float	JP_RAMP		= 7;		// seconds of holding forward to get from JP_SPEED to the top (it eases in: slow at first, then faster and faster)
float	JP_COAST	= 2.5;		// seconds to lose it all again when you let go of forward
float	JP_LOWGRAV	= 0.000001;	// DarkPlaces reads gravity 0 as "normal", so hover with almost none

.float	jp_fuel;		// player: seconds of fuel left (0 = no jetpack)
.float	jp_on;			// player: TRUE while it is lit
.float	jp_t0;			// player: when it was lit
.float	jp_jump;		// player: jump was held last frame
.float	jp_tap;			// player: when jump was last pressed while it burned (for the double tap)
.float	jp_air_tap;		// player: when jump was last pressed in mid-air while off (double-tap ignition!)
.float	jp_snd;			// player: when to restart the swoosh
.float	jp_flame;		// player: when to puff the next flames
.float	jp_voice;		// player: when the "floating" voice may play again
.float	jp_low;			// player: the low-fuel warning has been shown
.float	jp_hint_shown;	// player: shown the pickup hint once on this map
.entity	jp_armor;		// pickup: the yellow armor it stands next to
.entity	jp_worn;		// player: the pack on their back
.float	jp_boost;		// player: 0-1, how long forward has been held (the ramp timer)
.float	jp_fast;		// player: 0-1, jp_boost eased: how far from JP_SPEED to JP_MAXSPEED you are (drives the flames)
.float	jp_puff;		// player: when to puff the next smoke
.float	jp_sndup;		// player: whether the engine loop was started while climbing
.float	jp_st_fuel;		// player: fuel left in tenths of a second (stat 66, the HUD's glass tank)
.float	jp_st_max;		// player: a full tank in tenths of a second (stat 67)

// the pack on your back (the model's +X is forward: the harness side faces your chest, the tanks face aft; 1 unit of the model = JP_WORN_SCALE)
float	JP_WORN_SCALE	= 0.7;
vector	JP_WORN_OFS		= '-15 0 6';
// where the fire comes out, relative to the player's origin (the nozzle exits at model x -3, y +-6.5, z -9)
float	JP_NOZZLE_X		= -17;
float	JP_NOZZLE_Y		= 4.5;
float	JP_NOZZLE_Z		= 0;

float	jp_fx_fire, jp_fx_light, jp_fx_smoke, jp_fx_dust, jp_fx_burst, jp_fx_blaze, jp_fx_glow;		// particleeffectnum of the effectinfo.txt effects

float	jp_side;		// sv_cheats test: which side of the pickup impulse 73 looks from
entity	jp_test;		// sv_cheats test: the stand-in armor (impulse 75)

void() Jetpack_Precache;
void(entity armor) Jetpack_ForArmor;
void() item_jetpack;
void() Jetpack_Spawn;
void() Jetpack_Frame;
void() Jetpack_Fly;
void() Jetpack_WornFrame;
void(float climbing) Jetpack_Exhaust;
