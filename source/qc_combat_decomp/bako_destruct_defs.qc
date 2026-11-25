#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD-ISH DESTRUCTIBLE LANDMARKS - Definitions (bako_destruct_defs.qc)

Shared entity contract with maps/bakersfieldish.bsp:
  - Fox Theater:      bako_fox_clock, bako_fox_piece, bako_fox_rubble
  - Padre Hotel:      bako_padre_piece, bako_padre_rubble
  - Bakersfield Sign: bako_sign_piece, bako_sign_rubble
  - Glass Windows:    func_breakable (style 3 / BTYPE_GLASS)
================
*/

// Tunable cvars
var float	autocvar_bako_padre_hp			= 2600;
var float	autocvar_bako_fox_clock_hp		= 450;
var float	autocvar_bako_sign_hp			= 540;
var float	autocvar_bako_fox_rubble_t		= 115;
var float	autocvar_bako_padre_rubble_t	= 115;
var float	autocvar_bako_sign_rubble_t		= 115;
var float	autocvar_bako_fox_rebuild_t		= 25;
var float	autocvar_bako_auto_rebuild		= 1;
var float	autocvar_bako_boulder_dmg		= 15;

// Landmark group IDs
float	BAKO_GRP_NONE		= 0;
float	BAKO_GRP_FOX		= 1;
float	BAKO_GRP_PADRE		= 2;
float	BAKO_GRP_SIGN		= 3;
float	BAKO_GRP_GLASS		= 4;

// Material IDs (also used to suppress blood & gunshot soot in dn3_fx.qc & weapons.qc)
float	BAKO_MAT_MASONRY	= 1;
float	BAKO_MAT_METAL		= 2;
float	BAKO_MAT_GLASS		= 3;

// Landmark state machine
float	BAKO_ST_INTACT		= 0;
float	BAKO_ST_COLLAPSE	= 1;
float	BAKO_ST_RUBBLE		= 2;
float	BAKO_ST_REBUILD		= 3;

// Map-authored keys on bako_*_piece / bako_fox_clock
.string	bako_role;
.vector	bako_fall_angles;
.float	bako_fall_drop;
.vector	bako_fall_shift;
.float	bako_delay;
.float	bako_dur;
.float	bako_rebuild_order;

// Internal fields on destructibles, rubble, boulders, shards, roof props & players
.float	bako_group;
.float	bako_material;
.entity	bako_dest_next;
.entity	bako_piece_next;
.entity	bako_rubble_next;
.entity	bako_glass_next;
.entity	bako_last_infl;
.float	bako_last_infl_t;
.vector	bako_home_org;
.vector	bako_home_ang;
.vector	bako_home_min;
.vector	bako_home_max;
.float	bako_piece_hit;
.float	bako_piece_pop;
.float	bako_piece_fx_t;
.float	bako_piece_rb_done;
.float	bako_piece_rb_vis;
.float	bako_piece_bury_t;
.float	bako_piece_hidden;
.float	bako_broken;			// 0=intact, 1=actively breaking off in Stage 1/2, 2=broken & hidden
.float	bako_break_t0;
.float	bako_break_dur;
.float	bako_break_bursts;
.vector	bako_piece_hit_pos;
.vector	bako_piece_hit_ang;
.float	bako_glass_respawn_t;
.float	bako_glass_wait;
.float	bako_glass_hp;

// Per-player smooth 60 Hz damped-sine shake state (zero single-frame snaps!)
.vector	bako_shake_cur;

// Rooftop entity hide/restore fields (eliminates ALL midair floating pickups/skypads/karts)
.float	bako_roof_grp;
.vector	bako_roof_org;
.vector	bako_roof_mins;
.vector	bako_roof_maxs;
.vector	bako_roof_avel;
.string	bako_roof_mdl;
.float	bako_roof_solid;
.float	bako_roof_mt;
.float	bako_roof_fx;
.float	bako_roof_llev;
.float	bako_roof_pflags;
.float	bako_roof_trail;
.void()	bako_roof_think;
.float	bako_roof_nthink;
.float	bako_roof_hidden;
.entity	bako_roof_next;

// Rolling boulder, masonry chunk & glass shard fields
.float	bako_boulder_born;
.float	bako_boulder_life;
.float	bako_boulder_rest_t;
.float	bako_boulder_snd_t;
.float	bako_boulder_dust_t;
.float	bako_boulder_settled;
.float	bako_boulder_hit_t;
.float	bako_worker_slot;
.float	bako_worker_snd_t;
.float	bako_worker_panic_t;
.float	bako_worker_anim;

// CSQC HUD clientstats (slots 120..121)
.float	bako_st_padre_pct;		// 101=hidden/untouched, 1..99=damaged %, 0=collapsed
.float	bako_st_event;			// 0=none, 1..13=status/milestone toasts, 100..200=fox rebuild %

// Global state
float	bako_precached;
float	bako_present;
entity	bako_ctrl;
entity	bako_snd_ent;
entity	bako_dest_head;
entity	bako_glass_head;
entity	bako_fox_roof_list;
entity	bako_padre_roof_list;
float	bako_roof_scan_t;

// Corner HUD toast & continuous 60 Hz smooth damped-sine seismic oscillator state
float	bako_toast_code;
float	bako_toast_end;
float	bako_eq_amp;
float	bako_eq_phase;
float	bako_eq_last_t;
vector	bako_eq_org;
float	bako_eq_rad;

// Fox Theater globals
float	bako_fox_state;
float	bako_fox_stage;
float	bako_fox_phase_t0;
float	bako_fox_hp;
float	bako_fox_max_hp;
float	bako_fox_collapse_dur;
float	bako_fox_rubble_up;
float	bako_fox_fx_t;
float	bako_fox_rb_snd_t;
float	bako_fox_rb_clank_t;
float	bako_fox_clock_rb_vis;
float	bako_fox_clock_rb_done;
float	bako_fox_last_t;
entity	bako_fox_last_infl;
entity	bako_fox_clock_ent;
entity	bako_fox_twr_low;
entity	bako_fox_twr_hi;
entity	bako_fox_pieces;
entity	bako_fox_rubble_list;
vector	bako_fox_ctr;
vector	bako_fox_bmin;
vector	bako_fox_bmax;
float	bako_fox_piece_cnt;

// Padre Hotel globals
float	bako_padre_state;
float	bako_padre_stage;
float	bako_padre_phase_t0;
float	bako_padre_hp;
float	bako_padre_max_hp;
float	bako_padre_ms;			// milestone bits: 1=75%, 2=50%, 4=25%
float	bako_padre_collapse_dur;
float	bako_padre_rubble_up;
float	bako_padre_pop_idx;
float	bako_padre_wave_bits;
float	bako_padre_fx_t;
float	bako_padre_smoke_t;
float	bako_padre_rumble_t;
float	bako_padre_boom_t;
float	bako_padre_rb_snd_t;
float	bako_padre_last_t;
entity	bako_padre_last_infl;
entity	bako_padre_t4;
entity	bako_padre_crown;
entity	bako_padre_pieces;
entity	bako_padre_rubble_list;
vector	bako_padre_ctr;
vector	bako_padre_bmin;
vector	bako_padre_bmax;
float	bako_padre_piece_cnt;

// Bakersfield Sign globals
float	bako_sign_state;
float	bako_sign_stage;
float	bako_sign_phase_t0;
float	bako_sign_hp;
float	bako_sign_max_hp;
float	bako_sign_collapse_dur;
float	bako_sign_impacted;
float	bako_sign_rebound_clank;
float	bako_sign_fx_t;
float	bako_sign_last_t;
entity	bako_sign_last_infl;
entity	bako_sign_pieces;
entity	bako_sign_rubble_list;
vector	bako_sign_ctr;
float	bako_sign_piece_cnt;

// Active debris pools
float	bako_boulder_count;
float	bako_chunk_count;
float	bako_shard_count;
float	bako_kart_glass_t;

// Cached effectinfo indices
float	bako_fx_dust_surge;
float	bako_fx_collapse_plume;
float	bako_fx_window_smoke;
float	bako_fx_masonry_burst;
float	bako_fx_charge_pop;
float	bako_fx_big_boom;
float	bako_fx_sign_sparks;
float	bako_fx_rebuild_weld;
float	bako_fx_rock_dust;
float	bako_fx_glass_break;
float	bako_fx_glass_sparkle;
float	bako_fx_rocket_burn;

// Forward declarations
void() BakoDestruct_Precache;
void() BakoDestruct_Frame;
void(entity targ, vector hit_org, entity inflictor, entity attacker, float damage) BakoDestruct_OnDamage;
void(vector org, float radius, float peak_dmg, entity inflictor, entity attacker, float is_nuke) BakoDestruct_RadiusSplash;
float(entity p, float n) BakoDestruct_ClientCmd;
void() BakoDestruct_Impulse;
void(entity g) BakoDestruct_RegisterGlass;
void(entity g) BakoDestruct_OnGlassBreak;
float(entity g, entity other_ent) BakoDestruct_GlassTouchCheck;
void(entity p) BakoDestruct_UpdatePlayerStats;
void(vector bmin, vector bmax) Bako_RestoreGlassInBox;
void(entity e, vector ctr_ref) Bako_VeilPieceLanding;
void(entity hi, vector ctr_ref) Bako_VeilFoxTowerUpper;
void(float heavy) Bako_EmitPadreCenterVeil;
