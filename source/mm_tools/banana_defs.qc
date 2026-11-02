/*
================
THE BANANA GUN

A big yellow tube (impulse BN_IMPULSE; every player carries it). It shoots a huge
banana that bursts on impact into BN_MINIS little bananas; those bounce around and
go off when they touch someone or run out of fuse. Holds BN_MAX_AMMO bananas that
recharge over time. Combat+ only (compiled with COMBATPLUS defined).

All 24 item bits are taken, so ownership is not an item bit: IT_BANANA is only ever
the value of .weapon (it reuses the key-1 bit, which no weapon in hand ever has).
The weapon-cycling code tests (items & weapon), so it ORs IT_BANANA into its copy.
================
*/

float	IT_BANANA		= 131072;
float	BN_IMPULSE		= 15;		// "impulse 15" selects it

float	bn_inflicting;		// TRUE while a banana is dealing damage (for the obituary)

void() Banana_Precache;
void() Banana_Attack;
void() Banana_Select;
void(entity p) Banana_Give;
void() Banana_ViewFrame;

.float	bn_ammo;		// player: bananas in the tube
.float	bn_regen_t;		// player: when the next one recharges
.float	bn_fire_t;		// player: when the shot started
.float	bn_launch_t;		// player: when the banana leaves the tube
.float	bn_pending;		// player: shot in progress
.entity	bn_vwep;		// player: the banana other people see in your hand

float	BN_MAX_AMMO		= 3;
float	BN_REGEN_TIME		= 3.5;		// seconds per banana recharged
float	BN_SPEED		= 780;		// big banana speed
float	BN_SCALE		= 3;		// big banana size (model is 16 units long)
float	BN_MINIS		= 20;		// small bananas per burst
float	BN_BIG_DAMAGE		= 45;		// direct hit
float	BN_BIG_SPLASH		= 60;		// burst radius damage
float	BN_MINI_DAMAGE		= 10;		// small banana direct hit
float	BN_MINI_SPLASH		= 16;		// small banana radius damage
