// Server-side definitions for the live transparent tactical minimap feed (bm_minimap.qc)

float	ENT_BM_RADAR		= 8;		// CSQC SendEntity type (matches ENT_BM_RADAR in csqc/bm_minimap_hud.qc)

float	BM_RPK_GUN			= 1;		// gunfire blip
float	BM_RPK_BLAST		= 2;		// heavy explosion / projectile blast
float	BM_RPK_KILL			= 3;		// frag / death burst
float	BM_RPK_MONSTER		= 4;		// monster attack ping (SP / Coop)

float	BM_RPU_TRIPLE		= 1;		// Dual Wield
float	BM_RPU_QUAD			= 3;		// Quad Damage
float	BM_RPU_PENT			= 4;		// Pentagram / Berserk Pentagram
float	BM_RPU_TIME			= 5;		// Time Dilation Rune
float	BM_RPU_SUIT			= 6;		// Biosuit / Wetsuit
float	BM_RPU_RING			= 7;		// Ring of Shadows

float	BM_MM_PU_MAX		= 36;		// max active power-ups streamed to radar

float	BM_RVEH_MMTANK		= 1;		// Mega Man Tank
float	BM_RVEH_HEAVY		= 2;		// Truck, HD Truck, School Bus, John Bird, Rocket Rider, Eric Cannon
float	BM_RVEH_CAR			= 3;		// Sedan, Van, Coupe, GT Car, Golf Cart, Tuk-Tuk, Go-Karts

float	BM_MM_VEH_MAX		= 8;		// max nearby unoccupied vehicles streamed to radar
float	BM_MM_VEH_RANGE		= 600;		// walking proximity radius (Quake units)
float	BM_MM_VEH_RANGE_BIG	= 720;		// slightly wider radius for big vehicles like Mega Man Tank

float	bm_radar_enemy_t;
float	bm_radar_ally_t;
float	bm_radar_pu_t;
float	bm_radar_veh_t;
float	bm_pu_ver;
entity	bm_pu_head;
entity	bm_veh_head;

.entity	bm_radar_ent;
.float	bm_radar_cd;
.float	bm_radar_prev_shot;
.float	bm_radar_prev_fg;
.entity	bm_pu_next;
.float	bm_pu_kind;
.float	bm_rpu_ver_sent;
.entity	bm_veh_next;
.float	bm_veh_kind;

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

// Nearby unoccupied vehicles (up to 8 within walking range)
.float	bm_rv_cnt;
.vector	bm_rv0_pos;  .float bm_rv0_yaw;  .float bm_rv0_kind;
.vector	bm_rv1_pos;  .float bm_rv1_yaw;  .float bm_rv1_kind;
.vector	bm_rv2_pos;  .float bm_rv2_yaw;  .float bm_rv2_kind;
.vector	bm_rv3_pos;  .float bm_rv3_yaw;  .float bm_rv3_kind;
.vector	bm_rv4_pos;  .float bm_rv4_yaw;  .float bm_rv4_kind;
.vector	bm_rv5_pos;  .float bm_rv5_yaw;  .float bm_rv5_kind;
.vector	bm_rv6_pos;  .float bm_rv6_yaw;  .float bm_rv6_kind;
.vector	bm_rv7_pos;  .float bm_rv7_yaw;  .float bm_rv7_kind;

void(entity actor, vector org, float kind) BM_Radar_Ping;
void() BM_Radar_Tick;
void(entity p) BM_Radar_ClientGone;
void(entity e, float kind) BM_Radar_RegisterPowerup;
void(entity v, float kind) BM_Radar_RegisterVehicle;
