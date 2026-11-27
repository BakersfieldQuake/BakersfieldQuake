#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD KILLCAM - definitions (SSQC, Combat+)

Records a lightweight 16 Hz rolling ring buffer of the last 2.25 seconds of combat
(killer/player camera, body/vehicle poses, 1P viewmodels, tracers, and projectiles)
and streams a frozen snapshot to the victim on death in Deathmatch / CTF.
================
*/

var float	autocvar_bm_killcam		= 1;	// 1 = record & allow Call of Duty style killcams in DM/CTF

float	ENT_BM_KILLCAM		= 10;			// CSQC SendEntity type (matches csqc/bm_killcam_hud.qc)

float	KC_NONE				= 0;
float	KC_LINGER			= 1;			// 0.55s death linger while snapshot streams
float	KC_PLAYING			= 2;			// ~2.75s killcam playback

float	KC_HIST				= 36;			// 36 ticks @ 16 Hz = 2.25s history
float	KC_DT				= 0.0625;		// 16 Hz sample interval
float	KC_MAX_P			= 16;			// max client slots 0..15
float	KC_MAX_OTH			= 3;			// max nearby other players per tick
float	KC_MAX_PROJ			= 6;			// max nearby projectiles per tick
float	KC_LIVE_PROJ		= 10;			// max projectiles stored in live ring per tick
float	KC_MAX_SNAPS		= 4;			// concurrent frozen killcam snapshots
float	KC_CHUNK_FRAMES		= 4;			// frames per SendEntity chunk (36 / 4 = 9 chunks)
float	KC_LINGER_SEC		= 0.55;			// death linger before camera snaps to killer
float	KC_PLAY_SEC			= 2.75;			// playback duration (1.90s @ 1x + 0.85s slow-mo beat)

// Per-player live & playback state
.float	kc_enabled;			// client preference synced via cmd bm_killcam <0|1> (default 1)
.float	kc_state;			// KC_NONE / KC_LINGER / KC_PLAYING
.float	kc_snap_id;			// frozen snapshot slot 0..3
.float	kc_seq;				// monotonic killcam sequence 1..255
.float	kc_linger_end;		// server time when linger transitions to playback
.float	kc_play_t0;			// server time when playback started
.float	kc_end;				// server time when killcam auto-respawns
.float	kc_skip_armed;		// TRUE once fire/jump released after dying
.float	kc_sent_chunks;		// bitmask of chunks queued so far (bits 0..8)
.float	kc_next_chunk_t;	// next chunk send timestamp
.entity	kc_relay;			// private SendEntity relay for this client
.entity	kc_cam;				// server PVS camera anchor during playback

// Clientstats (slots 122..123, read by CSQC)
.float	kc_st_active;		// 0=off, 1=linger, 2=playing
.float	kc_st_seq;			// active killcam seq

// Per-player shot/hit tracking between 16 Hz ticks
.float	kc_fire_pending;	// bit 1 = fired, bit 2 = hit player
.float	kc_fire_snd;		// mapped weapon fire sound code
.vector	kc_shot_end;		// hitscan tracer endpoint
.float	kc_has_shot_end;	// TRUE if kc_shot_end is valid this tick
.float	kc_prev_att_fin;	// previous attack_finished for automatic shot detection
.float	kc_prev_wframe;		// previous weaponframe for automatic shot detection
.float	kc_prev_dn3;		// previous dn3_st_frame

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
float() KC_PlayerCustomize;
