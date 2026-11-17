#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
greenjar_defs.qc — "Jar o' Green Guys" (Fun Gun Slot 2, FG_PONG = 2, impulse 62)
A clear specimen glass jar filled with swirling neon-green mist and a spazzing live-action Green-Suit Guy.
Hold Fire to cocktail-shake; release to whip-throw. Shatters into igniting neon-green smoke and 12 bigger
wheel-driving, helium-giggling Green-Suit Men that motor across the map on spinning pneumatic tires, swarm and
drive 3 full circles around enemies BEFORE lunging in to attack (non-lethal 1%-2% chip hits, clamped >= 1 HP),
and spin like punctured balloons into rainbow confetti when shot!
*/

float	GJ_VM_IDLE_SKIN			= 0;
float	GJ_VM_IDLE_COUNT		= 60;		// 0..59:  4 manic in-jar antics @ 20 FPS (3.0s loop)
float	GJ_VM_SHAKE_SKIN		= 60;
float	GJ_VM_SHAKE_COUNT		= 16;		// 60..75: cocktail-shaker windup @ 40 FPS
float	GJ_VM_WIND_SKIN			= 76;
float	GJ_VM_PRE_COUNT			= 8;		// 76..83: high cock-back & cross-screen forward whip
float	GJ_VM_POST_SKIN			= 84;
float	GJ_VM_POST_COUNT		= 10;		// 84..93: splayed open-claw release & recoil slash
float	GJ_VM_RELOAD_SKIN		= 94;
float	GJ_VM_RELOAD_COUNT		= 18;		// 94..111: belt-snatch fresh rattling jar raise

float	GJ_THROW_DELAY			= 0.14;		// cock-back + whip before GJ_Launch() fires at skin 84
float	GJ_FOLLOW_TIME			= 0.22;		// splayed open-claw follow-through
float	GJ_RAISE_TIME			= 0.25;		// belt-snatch fresh jar raise
float	GJ_MAX_SHAKE			= 1.35;		// max hold-to-shake windup before auto-hurling

float	GJ_MINI_COUNT			= 12;		// 12 unleashed wheel-driving Green Men per shattered jar
float	GJ_MAX_MINIS			= 24;		// safety cap per player
float	GJ_ORBITS_BEFORE_ATK	= 270;		// ~0.75s chaotic swirl around victim BEFORE swarming in to attack!

.float	gj_shaking;			// player: timestamp when cocktail-shaker hold started (0 = not shaking)
.float	gj_next_rattle;		// player: next cocktail-shake sound timestamp
.float	gj_next_muffle;		// player: next muffled inside-the-jar giggle while held idle
.float	gj_fire_t;			// player: timestamp when whip-throw started
.float	gj_throw_at;		// player: timestamp when hand snaps open & GJ_Launch() spawns jar
.float	gj_threw_t;			// player: timestamp when GJ_Launch() fired
.float	gj_reload_t;		// player: timestamp when fresh jar belt-snatch started
.float	gj_empty;			// player: TRUE while out of jars after follow-through
.float	gj_charge_bonus;	// player: 0..1 bonus speed/pop from shaking the jar
.float	gjvm_on;			// viewmodel entity: TRUE while displaying progs/v_greenjar.md3

.float	gj_state;			// 1=wheel_drive, 2=wall_drive, 3=drive_3_laps (no attack!), 4=shot_spin, 5=balloon_pop, 6=attack_frenzy!
.float	gj_role;			// 0=cruiser, 1=sprinter, 2=wall-driver
.float	gj_anim_t0;			// animation phase start
.float	gj_step;			// discrete frame step for spin / balloon-pop
.float	gj_orbit_ang;		// current target angle (degrees) around victim
.float	gj_prev_yaw;		// previous measured angle around victim for true 3-lap counting
.float	gj_orbit_deg;		// accumulated degrees driven around victim (attacks at 1080 = 3 laps!)
.float	gj_orbit_dir;		// +1 or -1 driving orbit direction
.float	gj_orbit_rad;		// 72..108u multi-lane driving circle radius
.float	gj_attack_end;		// timestamp when post-3-lap attack frenzy ends -> confetti pop
.float	gj_next_voice;		// next high-pitched giggle/scream timestamp
.float	gj_next_poke;		// next non-lethal 1%-2% attack hit timestamp
.float	gj_next_boing;		// next curb-hop / attack-leap timestamp
.float	gj_wall_cool;		// cooldown before latching onto another wall after ceiling kick-off
.float	gj_climb_end;		// max duration of a single wall climb
.float	gj_die_at;			// max lifetime safety pop timestamp
.vector	gj_wall_n;			// surface normal of vertical building wall being climbed

void() GreenJar_Precache;
void() GJ_Press;
void() GJ_Frame;
void() GJ_Launch;
void(entity p) GJ_ResetPlayer;
void(entity vm, float is_quad) GreenJar_ViewFrame;
