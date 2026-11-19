// Server-side definitions for the CoD-style anti-wallhack minimap feed (bm_minimap.qc)

float	ENT_BM_RADAR		= 8;		// CSQC SendEntity type (matches ENT_BM_RADAR in csqc/bm_minimap_hud.qc)

float	BM_RPK_GUN			= 1;		// loud gunfire static blip
float	BM_RPK_BLAST		= 2;		// heavy explosion / projectile blast
float	BM_RPK_KILL			= 3;		// frag / death burst
float	BM_RPK_MONSTER		= 4;		// monster attack ping (SP / Coop)

float	bm_radar_heat_t;
float	bm_radar_ally_t;

.entity	bm_radar_ent;
.float	bm_radar_cd;
.float	bm_radar_prev_shot;
.float	bm_radar_prev_fg;
.float	bm_radar_prev_org_t;

// Fields on the per-client bm_radar_feed entity
.float	bm_rp_idx;
.float	bm_rp_seq_gen;

.float	bm_rp0_seq;
.float	bm_rp0_kind;
.vector	bm_rp0_pos;
.float	bm_rp1_seq;
.float	bm_rp1_kind;
.vector	bm_rp1_pos;
.float	bm_rp2_seq;
.float	bm_rp2_kind;
.vector	bm_rp2_pos;
.float	bm_rp3_seq;
.float	bm_rp3_kind;
.vector	bm_rp3_pos;

.float	bm_rh_seq;
.float	bm_rh_cnt;
.vector	bm_rh0_pos;
.float	bm_rh0_int;
.vector	bm_rh1_pos;
.float	bm_rh1_int;
.vector	bm_rh2_pos;
.float	bm_rh2_int;
.vector	bm_rh3_pos;
.float	bm_rh3_int;

.float	bm_ra_cnt;
.vector	bm_ra0_pos;
.float	bm_ra0_yaw;
.vector	bm_ra1_pos;
.float	bm_ra1_yaw;
.vector	bm_ra2_pos;
.float	bm_ra2_yaw;
.vector	bm_ra3_pos;
.float	bm_ra3_yaw;

void(entity actor, vector org, float kind) BM_Radar_Ping;
void() BM_Radar_Tick;
void(entity p) BM_Radar_ClientGone;
