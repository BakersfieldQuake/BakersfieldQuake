/*
================
THE FUN GUNS (Bakersfield Memes)

Three joke weapons and the NetSend gun. Every player spawns with all of them; each has its own ammo that
recharges by itself. Combat+ only (COMBATPLUS).

  1 Rob Dob        impulse 61  (or 17)  your head flies out of you, you steer it, then it screams into someone and blows up
                               like a rocket (floathead.qc). One head per FG_DOB_REGEN seconds. Replaced the Whack-a-Mole hammer.
  2 Jar o' Green Guys impulse 62 (key I) clear glass jar filled with swirling neon-green mist and a spazzing Green-Suit Guy;
                               shatters into green smoke and 12 wheel-driving green men that circle enemies 3x before attacking (greenjar.qc)
  3 Pickle Surprise impulse 63 a pickle you throw: it sticks to whatever it hits and sits there about the size of a
                               grenade. When someone comes close it goes erect, twice the height of a man, waves
                               about like a roadside inflatable, shouts "pickle surprise" and blows up green,
                               throwing a shower of pickles that each do a little damage (pickle.qc)
  5 Dookie Bazooka impulse 65  (key U) MK-IV Omega BFG-9000: hold fire to wind up tabla reactor, release to blast
                               a screaming hand-waving fat guy with orbiting flies & Bhangra music (dookie.qc)
  6 Wheelman Cannon impulse 66 (key G) hold fire to charge, let go (or full charge) and a screaming Wheelman blasts off
                               and crashes in a big explosion with flying wheels, bars and gibs (wcannon.qc)
  7 M4A1           impulse 67  (keys C / 0) stand-alone CS 1.6 automatic rifle (m4.qc)
  8 Thompson       impulse 68  (keys Z / -) stand-alone DoD 1.3 .45 ACP submachine gun (tommy.qc)
  9 M1 Garand      impulse 69  (keys M / =) stand-alone DoD 1.3 .30-06 semi-auto rifle (garand.qc)
  4 NetSend        impulse 64  (key B or N) fire throws LOL.BAT: it sticks to the floor and grows a beige PC that sends NET SEND
                               pop-ups at everyone else for good; up to 20 PCs per player (netsend.qc)

Ownership is not an item bit (all 24 are taken): .weapon == IT_FUNGUN means "a fun gun
is out" and .fg_sel says which one. IT_FUNGUN reuses the key-2 bit, which no weapon
in hand ever has (the banana gun uses key 1 the same way).
================
*/

float	IT_FUNGUN		= 262144;
float	FG_IMPULSE		= 61;		// impulse 61..69 select fun gun 1..9
float	FG_COUNT		= 9;

float	FG_DOB		= 1;
float	FG_PONG		= 2;
float	FG_PICKLE	= 3;
float	FG_NETSEND	= 4;
float	FG_DOOKIE	= 5;
float	FG_WCANNON	= 6;
float	FG_M4		= 7;		// CS 1.6 M4A1 (m4.qc)
float	FG_TOMMY	= 8;		// DoD 1.3 M1A1 Thompson SMG (tommy.qc)
float	FG_GARAND	= 9;		// DoD 1.3 M1 Garand rifle (garand.qc)

float	fg_inflicting;		// which fun gun is dealing damage right now (0 = none), for the obituary

void() FunGun_Precache;
void() FunGun_Attack;
void(float g) FunGun_Select;
void(entity p) FunGun_Give;
void() FunGun_ViewFrame;
void() Binoc_Frame;
float(entity p) Binoc_On;
string(float g) FunGun_VModel;
float(float g) FunGun_Available;
float(entity p, float g) FunGun_Ammo;
float() FunGun_First;
float() FunGun_CycleNext;
float() FunGun_Last;
float() FunGun_CyclePrev;
float() FunGun_BotPick;
void() Pickle_Precache;
void() Pk_Launch;
void(entity vm, float is_quad) Pickle_ViewFrame;
void() FD_Launch;
void(entity p) FD_Reset;

float	PK_THROW_DELAY	= 0.19;		// brutal choke-squeeze windup + violent cross-screen whip before claw snaps open & Pk_Launch() fires
float	PK_FOLLOW_TIME	= 0.24;		// mid-screen open-claw recoil shudder + slash down off bottom-left
float	PK_RAISE_TIME	= 0.22;		// aggressive belt-snatch fresh Pickle raise & cheek-squish catch settle

.float	fg_sel;			// player: which fun gun is out (1..FG_COUNT)
.float	fg_ammo1, fg_ammo2, fg_ammo3, fg_ammo4, fg_ammo5, fg_ammo6, fg_ammo7, fg_ammo8, fg_ammo9;
.float	fg_regen1, fg_regen2, fg_regen3, fg_regen4, fg_regen5, fg_regen6, fg_regen7, fg_regen8, fg_regen9;
.float	fg_fire_t;		// player: when the last shot went
.float	fg_lock_t;		// player: until this time only fg_lock_gun can fire (bm_fg_lock)
.float	fg_lock_gun;	// player: the fun gun that fired last
.float	bm_fx_sent;		// player: the lighter particle file has been asked for on this map
.float	fg_lock_msg;	// player: next time the "locked" click and message may play
.float	fd_hint_shown;	// player: Rob Dob flight hint shown once
.float	fg_seen_mask;	// player: bitmask of fun guns whose intro hint was shown
void(float g) FunGun_Lock;
void() FunGun_PlayerDie;
void() BM_PredictFrame;
void() Jetpack_Off;
.float	fg_bot_until;	// bot: keeps its current weapon choice until then
.float	fg_bot_fun;		// bot: TRUE while it is playing with a fun gun

.float	pk_fire_t;		// player: when Mouse1 started a Pickle Surprise throw
// the binoculars (review 2026-11-01: "a binocular that you can zoom in"): hold the key (MOUSE3 or O, +button3), the mouse wheel changes the zoom
float	BN_ZOOM_MIN	= 2;		// times
float	BN_ZOOM_MAX	= 16;
float	BN_ZOOM_START	= 5;
.float	bn_on;			// player: the binoculars are up
.float	bn_zoom;		// player: how many times they magnify
.float	bn_msg;			// player: when the range read-out was last printed

.float	pk_throw_at;	// player: timestamp when the hand snaps open and Pk_Launch() spawns the pickle
.float	pk_threw_t;		// player: timestamp when Pk_Launch() fired (drives follow-through & reload snatch)
.float	pk_reload_t;	// player: timestamp when an empty/selected hand snatches up a fresh pickle
.float	pk_empty;		// player: TRUE while out of pickles after follow-through finished
.float	pvm_on;			// viewmodel entity: TRUE while showing v_pickle.md3

.float	fg_born;		// projectile / pickle / gib: spawn time
.float	fg_bounces;		// projectile: bounces so far

.float	pk_front;		// pickle (balloon): the way its own face looks, in degrees (Pk_Customize picks the view from it)
.float	pk_state;		// pickle: 1 in the air, 2 stuck and arming, 3 armed, 4 tripped (inflating, talking)
.float	pk_t;			// pickle: when the current state ends
.float	pk_t0;			// pickle: when it was tripped (the inflate starts here)
.vector	pk_n;			// pickle: normal of the surface it stuck to
.vector	pk_p0;			// pickle: where it stuck / where it stands once it has inflated
.vector	pk_p1;
.vector	pk_a0;			// pickle: its angles when it stuck
.entity	pk_who;			// pickle: whoever set it off

// ammo: max, seconds per round recharged
float	FG_DOB_MAX		= 1;	float	FG_DOB_REGEN	= 20;
float	FG_PONG_MAX		= 2;	float	FG_PONG_REGEN	= 10;	// two Jars o' Green Guys; 10 s per jar recharge (greenjar.qc)
float	FG_PICKLE_MAX	= 2;	float	FG_PICKLE_REGEN	= 5;
float	FG_DOOKIE_MAX	= 2;	float	FG_DOOKIE_REGEN	= 10;	// two canisters; 10 s to refill the next (dookie.qc)
float	FG_WCANNON_MAX	= 1;	float	FG_WCANNON_REGEN	= 18;	// like a BFG: one Wheelman, 18 s to reload the next (wcannon_defs.qc)
float	FG_M4_MAX	= 30;	float	FG_M4_REGEN	= 0.2;	// the M4's magazine; REGEN is only used with bm_reload 0 (m4_defs.qc)
float	FG_TOMMY_MAX	= 30;	float	FG_TOMMY_REGEN	= 0.2;	// Thompson 30-round stick mag (tommy_defs.qc)
float	FG_GARAND_MAX	= 8;	float	FG_GARAND_REGEN	= 0.35;	// M1 Garand 8-round en-bloc clip (garand_defs.qc)
float	FG_NETSEND_MAX	= 1;	float	FG_NETSEND_REGEN	= 2;	// one disk; 2 s to write the next LOL.BAT: the only limit is 20 PCs up (netsend_defs.qc)
