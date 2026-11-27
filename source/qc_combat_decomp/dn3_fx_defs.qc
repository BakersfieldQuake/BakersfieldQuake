// dn3_fx_defs.qc — Shared server constants and forward declarations for DN3DooM FX.

float ENT_DN3FX = 9;

float DN3FX_FIRE_BURST  = 4;
float DN3FX_BULLET_PUFF = 5;
float DN3FX_GIB_BURST   = 6;

float autocvar_bm_dn3fx = 1;

.float dn3fx_fire_t;

float dn3fx_wall_puff_t;
float dn3fx_wall_snd_t;

void() DN3FX_Precache;
void(float kind, vector org, vector dir, float sc) DN3FX_Emit;
void(vector org, vector dir, float sc, float with_sound) DN3FX_OnFire;
void(vector org, vector norm) DN3FX_OnWallImpact;
void(vector org, float sc) DN3FX_OnGib;
