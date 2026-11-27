// Server-side definitions for the live transparent tactical minimap feed (bm_minimap.qc)

float	ENT_BM_RADAR		= 8;		// CSQC SendEntity type (matches ENT_BM_RADAR in csqc/bm_minimap_hud.qc)

float	BM_RPK_GUN			= 1;		// gunfire blip
float	BM_RPK_BLAST		= 2;		// heavy explosion / projectile blast
float	BM_RPK_KILL			= 3;		// frag / death burst
float	BM_RPK_MONSTER		= 4;		// monster attack ping (SP / Coop)

float	bm_radar_enemy_t;
float	bm_radar_ally_t;

.entity	bm_radar_ent;
.float	bm_radar_cd;
.float	bm_radar_prev_shot;
.float	bm_radar_prev_fg;

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

// Live tracked enemies (up to 16 closest enemies, exact coords + yaw + flags)
.float	bm_re_cnt;
.vector	bm_re0_pos;  .float bm_re0_yaw;  .float bm_re0_flg;
.vector	bm_re1_pos;  .float bm_re1_yaw;  .float bm_re1_flg;
.vector	bm_re2_pos;  .float bm_re2_yaw;  .float bm_re2_flg;
.vector	bm_re3_pos;  .float bm_re3_yaw;  .float bm_re3_flg;
.vector	bm_re4_pos;  .float bm_re4_yaw;  .float bm_re4_flg;
.vector	bm_re5_pos;  .float bm_re5_yaw;  .float bm_re5_flg;
.vector	bm_re6_pos;  .float bm_re6_yaw;  .float bm_re6_flg;
.vector	bm_re7_pos;  .float bm_re7_yaw;  .float bm_re7_flg;
.vector	bm_re8_pos;  .float bm_re8_yaw;  .float bm_re8_flg;
.vector	bm_re9_pos;  .float bm_re9_yaw;  .float bm_re9_flg;
.vector	bm_re10_pos; .float bm_re10_yaw; .float bm_re10_flg;
.vector	bm_re11_pos; .float bm_re11_yaw; .float bm_re11_flg;
.vector	bm_re12_pos; .float bm_re12_yaw; .float bm_re12_flg;
.vector	bm_re13_pos; .float bm_re13_yaw; .float bm_re13_flg;
.vector	bm_re14_pos; .float bm_re14_yaw; .float bm_re14_flg;
.vector	bm_re15_pos; .float bm_re15_yaw; .float bm_re15_flg;

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
