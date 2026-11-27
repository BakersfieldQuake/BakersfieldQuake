#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD KILLER CAM - definitions (SSQC, Combat+)

When killed by another player (human or bot) in Deathmatch / CTF, lingers
briefly on your death (~0.5s) then smoothly follows your killer in live
3rd-person for ~3.0s. Optional via bm_killcam (default 1) and skippable
anytime with FIRE or JUMP.
================
*/

var float	autocvar_bm_killcam		= 1;	// 1 = follow killer in 3rd-person after death in DM/CTF

float	ENT_BM_KILLCAM		= 10;			// CSQC SendEntity type (matches csqc/bm_killcam_hud.qc)

float	KC_NONE				= 0;
float	KC_LINGER			= 1;			// ~0.5s death linger
float	KC_PLAYING			= 2;			// ~3.0s live 3rd-person follow

float	KC_LINGER_SEC		= 0.50;
float	KC_PLAY_SEC			= 3.00;

// Per-player state
.float	kc_enabled;			// client preference synced via cmd bm_killcam <0|1> (default 1)
.float	kc_state;			// KC_NONE / KC_LINGER / KC_PLAYING
.float	kc_seq;				// monotonic killcam sequence 1..255
.float	kc_linger_end;		// server time when camera switches to killer
.float	kc_end;				// server time when killcam auto-respawns
.float	kc_skip_armed;		// TRUE once fire/jump released after dying
.entity	kc_killer;			// killer being followed
.string	kc_kname;			// strzoned killer netname
.string	kc_wname;			// strzoned weapon/vehicle label
.vector	kc_cam_org;			// smoothed 3rd-person camera origin
.vector	kc_cam_ang;			// smoothed 3rd-person camera angles
.float	kc_cam_init;		// TRUE once camera initialized for this death
.float	kc_header_sent;		// TRUE once killer/weapon strings sent for this seq
.float	kc_frame_t;			// previous frame time for smoothing
.entity	kc_relay;			// private SendEntity relay for this client
.entity	kc_cam;				// server PVS camera anchor during playback

// Clientstats (slots 122..123, read by CSQC)
.float	kc_st_active;		// 0=off, 1=linger, 2=playing
.float	kc_st_seq;			// active killcam seq

// Prototypes
void() KC_Precache;
void() KC_Stats;
void() KC_Tick;
void(entity attacker, entity targ, vector hitpos) KC_NoteHit;
void(entity targ, entity attacker, entity inflictor) KC_OnPlayerKilled;
float(entity p) KC_DeathThink;
void(entity p) KC_Reset;
void(entity p) KC_ClientConnect;
void(entity p) KC_ClientDisconnect;
void(entity p, string val) KC_Command;
