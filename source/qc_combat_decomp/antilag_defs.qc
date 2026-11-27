#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
HITSCAN LAG COMPENSATION / ANTILAG (antilag_defs.qc)

Per-tick ring buffer of living player/bot origins (48 ticks = 667 ms at 72 Hz,
480 ms at 100 Hz) keyed by client edict slot (0..15). Rewinds other players'
hitboxes by the shooter's engine-reported RTT (.float ping in ms, DP_SV_PING)
around hitscan tracelines and restores before ApplyMultiDamage / T_Damage.
================
*/

var float	autocvar_sv_antilag			= 1;		// 1 = rewind player/bot hitboxes for high-ping human hitscan shots
var float	autocvar_sv_antilag_maxping	= 450;		// max lag compensation rewind in milliseconds

float	AL_MAXCLIENTS	= 16;
float	AL_HIST			= 48;

vector	al_pos[768];		// AL_MAXCLIENTS * AL_HIST
float	al_valid[768];		// 1 if slot was alive + SOLID_SLIDEBOX at this tick
float	al_time[48];		// server time for each ring slot
float	al_head;			// index (0..AL_HIST-1) of most recently recorded frame
float	al_count;			// number of recorded frames (0..AL_HIST)
float	al_active;			// re-entrancy guard: 1 while hitboxes are rewound

.vector	al_save_org;		// saved current origin during rewind
.float	al_rewound;			// 1 if entity was moved by Antilag_Rewind

void() Antilag_Reset;
void() Antilag_RecordFrame;
void(entity attacker) Antilag_Rewind;
void() Antilag_Restore;
