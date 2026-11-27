#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD KILLCAM - server ring buffer, snapshot freezer, and chunked streamer (SSQC)

Maintains a 16 Hz rolling 2.25s history of all players (1P eye/viewmodel or 3P vehicle cam)
and active projectiles. On a Deathmatch/CTF kill by another player (human or bot), freezes
the relevant window into one of 4 snapshot slots and streams it in 9 small SendEntity chunks
during the 0.55s death linger so playback starts smoothly without packet spikes or PVS holes.
================
*/

// Sound codes sent per tick (matched by csqc/bm_killcam_hud.qc)
float	KC_SND_NONE		= 0;
float	KC_SND_SG		= 1;
float	KC_SND_SSG		= 2;
float	KC_SND_NAIL		= 3;
float	KC_SND_GL		= 4;
float	KC_SND_RL		= 5;
float	KC_SND_LG		= 6;
float	KC_SND_LASER	= 7;
float	KC_SND_HAMMER	= 8;
float	KC_SND_M4		= 9;
float	KC_SND_GARAND	= 10;
float	KC_SND_MEGAMAN	= 11;

// Live ring buffer: 36 ticks x 16 players = 576 entries
float	kc_head;			// next write tick index 0..35
float	kc_count;			// number of valid ticks recorded (0..36)
float	kc_next_t;			// next sample time
float	kc_tick_t[36];

vector	kc_p_eye[576];
vector	kc_p_ang[576];
vector	kc_p_org[576];
float	kc_p_yaw[576];
float	kc_p_mdl[576];
float	kc_p_frm[576];
float	kc_p_skin[576];
float	kc_p_col[576];
float	kc_p_vm[576];
float	kc_p_vfrm[576];
float	kc_p_fl[576];		// 1=fired, 2=hit, 4=3P/vehicle, 8=alive, 16=has_tracer
float	kc_p_snd[576];
float	kc_p_dn3[576];
vector	kc_p_tend[576];

// Live projectile ring: 36 ticks x 10 projectiles = 360 entries
float	kc_pr_cnt[36];
vector	kc_pr_org[360];
vector	kc_pr_ang[360];
float	kc_pr_mdl[360];
float	kc_pr_frm[360];
float	kc_pr_sc[360];

// Frozen snapshot pool: 4 slots x 36 frames = 144 frames
float	kc_snap_rr;
float	kc_s_nframes[4];
float	kc_s_kill_tick[4];
float	kc_s_seq[4];
string	kc_s_kname[4];
string	kc_s_wname[4];

// Frozen killer (144)
vector	kc_sk_eye[144];
vector	kc_sk_ang[144];
vector	kc_sk_org[144];
float	kc_sk_yaw[144];
float	kc_sk_mdl[144];
float	kc_sk_frm[144];
float	kc_sk_skin[144];
float	kc_sk_col[144];
float	kc_sk_vm[144];
float	kc_sk_vfrm[144];
float	kc_sk_fl[144];
float	kc_sk_snd[144];
float	kc_sk_dn3[144];
vector	kc_sk_tend[144];

// Frozen victim (144)
vector	kc_sv_org[144];
float	kc_sv_yaw[144];
float	kc_sv_mdl[144];
float	kc_sv_frm[144];
float	kc_sv_skin[144];
float	kc_sv_col[144];
float	kc_sv_alive[144];

// Frozen nearby others: 4 x 36 x 3 = 432
float	kc_so_cnt[144];
vector	kc_so_org[432];
float	kc_so_yaw[432];
float	kc_so_mdl[432];
float	kc_so_frm[432];
float	kc_so_skin[432];
float	kc_so_col[432];

// Frozen projectiles: 4 x 36 x 6 = 864
float	kc_sp_cnt[144];
vector	kc_sp_org[864];
vector	kc_sp_ang[864];
float	kc_sp_mdl[864];
float	kc_sp_frm[864];
float	kc_sp_sc[864];

// ---------------------------------------------------------------- helpers

float(entity p) KC_SlotOf =
{
	local float idx;

	if (!p || p == world)
		return -1;
	idx = num_for_edict (p);
	idx = idx - 1;
	if (idx < 0 || idx >= KC_MAX_P)
		return -1;
	return idx;
};

float(float a) KC_PackByteAng =
{
	local float w;

	w = a - 360 * floor (a / 360);
	return bound (0, floor (w * 255 / 360 + 0.5), 255);
};

float(float a) KC_PackShortAng =
{
	local float w;

	w = a - 360 * rint (a / 360);
	return rint (w * 64);
};

entity(entity p) KC_BodyEnt =
{
	if (p.veh_van != world && !bm_wasfreed (p.veh_van))
		return p.veh_van;
	if (p.mmt_tank != world && !bm_wasfreed (p.mmt_tank))
		return p.mmt_tank;
	if (p.jb_vehicle != world && !bm_wasfreed (p.jb_vehicle))
		return p.jb_vehicle;
	if (p.rr_vehicle != world && !bm_wasfreed (p.rr_vehicle))
		return p.rr_vehicle;
	if (p.fd_head != world && !bm_wasfreed (p.fd_head))
		return p.fd_head;
	return p;
};

float(entity p) KC_WeaponSoundCode =
{
	local float w, g;

	if (p.veh_van != world || p.mmt_tank != world || p.jb_vehicle != world || p.rr_vehicle != world)
		return KC_SND_RL;
	w = p.weapon;
	if (w == IT_AXE)				return KC_SND_HAMMER;
	if (w == IT_SHOTGUN)			return KC_SND_SG;
	if (w == IT_SUPER_SHOTGUN)		return KC_SND_SSG;
	if (w == IT_NAILGUN || w == IT_SUPER_NAILGUN) return KC_SND_NAIL;
	if (w == IT_GRENADE_LAUNCHER)	return KC_SND_GL;
	if (w == IT_ROCKET_LAUNCHER)	return KC_SND_RL;
	if (w == IT_LIGHTNING)			return KC_SND_LG;
	if (w == IT_LASER_CANNON)		return KC_SND_LASER;
	if (w == IT_MEGAMAN)			return KC_SND_MEGAMAN;
	if (w == IT_FUNGUN)
	{
		g = p.fg_sel;
		if (g == FG_M4)				return KC_SND_M4;
		if (g == FG_GARAND)			return KC_SND_GARAND;
		if (g == FG_WCANNON)		return KC_SND_RL;
		return KC_SND_GL;
	}
	return KC_SND_SG;
};

float(entity p) KC_IsHitscan =
{
	local float w, g;

	if (p.veh_van != world || p.mmt_tank != world || p.jb_vehicle != world || p.rr_vehicle != world || p.fd_head != world)
		return FALSE;
	w = p.weapon;
	if (w == IT_SHOTGUN || w == IT_SUPER_SHOTGUN || w == IT_LIGHTNING)
		return TRUE;
	if (w == IT_FUNGUN)
	{
		g = p.fg_sel;
		if (g == FG_M4 || g == FG_GARAND)
			return TRUE;
	}
	return FALSE;
};

string(entity killer, entity inflictor) KC_WeaponLabel =
{
	local string cn;
	local float w, g;

	if (inflictor != world && inflictor != killer)
	{
		cn = inflictor.classname;
		if (cn == "bako_van" || cn == "bako_gokart") return (inflictor.veh_kind >= VEH_GOKART_1 && inflictor.veh_kind <= VEH_GOKART_6) ? "Go-Kart" : "Bakersfield Van";
		if (cn == "mm_tank")			return "Mega Man Tank";
		if (cn == "misc_vehicle_johnbird") return "Winged John";
		if (cn == "rocket_rider")		return "Rocket Rider";
		if (cn == "robdob")				return "Rob Dob Drone";
		if (cn == "megaman")			return "Mega Man";
		if (cn == "milky")				return "Milky Gun";
		if (cn == "dookie_shot")		return "Dookie Bazooka";
		if (cn == "wc_shot")			return "Wheelman Cannon";
		if (cn == "kyle_proj")			return "The Pocket Kyle";
		if (cn == "pickle")				return "Pickle Surprise";
		if (cn == "greenjar_proj" || cn == "greenguy_mini") return "Jar o' Green Guys";
		if (cn == "netsend_disk" || cn == "netsend_sentry") return "NetSend";
		if (cn == "bigbanana")			return "Banana";
		if (cn == "grenade")			return "Grenade Launcher";
		if (cn == "missile")			return "Rocket Launcher";
	}
	if (killer.veh_van != world)
		return (killer.veh_van.veh_kind >= VEH_GOKART_1 && killer.veh_van.veh_kind <= VEH_GOKART_6) ? "Go-Kart" : "Bakersfield Van";
	if (killer.mmt_tank != world)		return "Mega Man Tank";
	if (killer.jb_vehicle != world)		return "Winged John";
	if (killer.rr_vehicle != world)		return "Rocket Rider";
	if (killer.fd_head != world)		return "Rob Dob Drone";

	w = killer.weapon;
	if (w == IT_AXE)				return "Bonk Hammer";
	if (w == IT_SHOTGUN)			return "Shotgun";
	if (w == IT_SUPER_SHOTGUN)		return "Pump Shotgun";
	if (w == IT_NAILGUN)			return "Nailgun";
	if (w == IT_SUPER_NAILGUN)		return "Super Nailgun";
	if (w == IT_GRENADE_LAUNCHER)	return "Grenade Launcher";
	if (w == IT_ROCKET_LAUNCHER)	return "Rocket Launcher";
	if (w == IT_LIGHTNING)			return "Lightning Gun";
	if (w == IT_LASER_CANNON)		return "CCC Laser Cannon";
	if (w == IT_MEGAMAN)			return "Mega Man";
	if (w == IT_FUNGUN)
	{
		g = killer.fg_sel;
		if (g == FG_M4)				return "M4A1";
		if (g == FG_GARAND)			return "M1 Garand";
		if (g == FG_DOB)			return "Rob Dob";
		if (g == FG_PONG)			return "Jar o' Green Guys";
		if (g == FG_PICKLE)			return "Pickle Surprise";
		if (g == FG_NETSEND)		return "NetSend";
		if (g == FG_DOOKIE)			return "Dookie Bazooka";
		if (g == FG_WCANNON)		return "Wheelman Cannon";
		if (g == FG_KYLE)			return "The Pocket Kyle";
		if (g == FG_CYRAX)			return "Cyrax Net";
	}
	return "Weapon";
};

// ---------------------------------------------------------------- init / stats / commands

void() KC_Precache =
{
	local float i;

	registercvar ("bm_killcam", "1");
	kc_head = 0;
	kc_count = 0;
	kc_next_t = 0;
	kc_snap_rr = 0;
	for (i = 0; i < KC_MAX_SNAPS; i = i + 1)
	{
		kc_s_kname[i] = "";
		kc_s_wname[i] = "";
	}
};

void() KC_Stats =
{
	clientstat (122, 2, kc_st_active);
	clientstat (123, 2, kc_st_seq);
};

void(entity p) KC_ClientConnect =
{
	p.kc_enabled = 1;
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
	p.kc_st_seq = 0;
	p.kc_relay = world;
	p.kc_cam = world;
	p.kc_fire_pending = 0;
	p.kc_has_shot_end = FALSE;
	p.kc_prev_att_fin = 0;
	p.kc_prev_wframe = 0;
	p.kc_prev_dn3 = 0;
};

void(entity p) KC_ClientDisconnect =
{
	if (p.kc_cam != world)
	{
		remove (p.kc_cam);
		p.kc_cam = world;
	}
	if (p.kc_relay != world)
	{
		remove (p.kc_relay);
		p.kc_relay = world;
	}
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
};

void(entity p, string val) KC_Command =
{
	local float v;

	v = (stof (val) != 0) ? 1 : 0;
	p.kc_enabled = v;
	if (!v && p.kc_state != KC_NONE)
		KC_Reset (p);
};

float() KC_PlayerCustomize =
{
	// Hide live player bodies from any client currently watching a rewound killcam
	if (other != world && other.kc_state == KC_PLAYING)
		return FALSE;
	return TRUE;
};

// ---------------------------------------------------------------- recording

void(entity attacker, entity targ, vector hitpos) KC_NoteHit =
{
	if (!deathmatch || !autocvar_bm_killcam)
		return;
	if (!attacker || attacker == world || attacker.classname != "player" || attacker == targ)
		return;
	if (targ.classname != "player")
		return;
	attacker.kc_fire_pending = attacker.kc_fire_pending | 3;
	attacker.kc_fire_snd = KC_WeaponSoundCode (attacker);
	attacker.kc_shot_end = hitpos;
	attacker.kc_has_shot_end = TRUE;
};

void() KC_RecordSample =
{
	local float t_idx, p_idx, slot, fl, fired, has_tr, vm_mdl, vm_frm, pr_cnt, base_pr;
	local entity p, body, e;
	local vector eye, ang, tend;

	t_idx = kc_head;
	kc_tick_t[t_idx] = time;

	// Clear all 16 player slots for this tick first
	for (slot = 0; slot < KC_MAX_P; slot = slot + 1)
	{
		p_idx = t_idx * KC_MAX_P + slot;
		kc_p_fl[p_idx] = 0;
		kc_p_mdl[p_idx] = 0;
		kc_p_vm[p_idx] = 0;
	}

	p = bm_player_head;
	while (p)
	{
		slot = KC_SlotOf (p);
		if (slot >= 0 && !p.bm_obs)
		{
			p_idx = t_idx * KC_MAX_P + slot;
			body = KC_BodyEnt (p);
			fl = 0;

			if (p.health > 0 && !p.deadflag)
				fl = fl | 8;

			if (p.clientcamera != world && p.clientcamera != p)
			{
				eye = p.clientcamera.origin;
				ang = p.clientcamera.angles;
				fl = fl | 4;
			}
			else
			{
				eye = p.origin + p.view_ofs;
				ang = p.v_angle;
				if (body != p)
					fl = fl | 4;
			}

			fired = (p.kc_fire_pending & 1);
			if (p.attack_finished > p.kc_prev_att_fin + 0.02)
				fired = TRUE;
			else if (p.weaponframe > 0 && p.kc_prev_wframe == 0)
				fired = TRUE;
			else if (p.dn3_st_frame > 0 && (p.dn3_st_frame & 63) > 1 && (p.kc_prev_dn3 & 63) <= 1)
				fired = TRUE;
			else if (p.button0 && p.weapon == IT_LIGHTNING && p.ammo_cells > 0 && p.health > 0)
				fired = TRUE;

			p.kc_prev_att_fin = p.attack_finished;
			p.kc_prev_wframe = p.weaponframe;
			p.kc_prev_dn3 = p.dn3_st_frame;

			if (fired)
				fl = fl | 1;
			if (p.kc_fire_pending & 2)
				fl = fl | 2;

			has_tr = FALSE;
			if (p.kc_has_shot_end)
			{
				tend = p.kc_shot_end;
				has_tr = TRUE;
			}
			else if (fired && KC_IsHitscan (p))
			{
				makevectors (p.v_angle);
				traceline (p.origin + p.view_ofs, p.origin + p.view_ofs + v_forward * 2048, FALSE, p);
				tend = trace_endpos;
				has_tr = TRUE;
			}
			if (has_tr)
				fl = fl | 16;

			kc_p_eye[p_idx] = eye;
			kc_p_ang[p_idx] = ang;
			kc_p_org[p_idx] = body.origin;
			kc_p_yaw[p_idx] = body.angles_y;
			kc_p_mdl[p_idx] = body.modelindex;
			kc_p_frm[p_idx] = body.frame;
			kc_p_skin[p_idx] = body.skin;
			kc_p_col[p_idx] = p.colormap;
			kc_p_dn3[p_idx] = (p.weapon == IT_SUPER_SHOTGUN && p.dn3_st_frame <= 0) ? (fired ? 2 : 1) : p.dn3_st_frame;
			kc_p_tend[p_idx] = tend;
			kc_p_fl[p_idx] = fl;
			kc_p_snd[p_idx] = (p.kc_fire_snd > 0) ? p.kc_fire_snd : KC_WeaponSoundCode (p);

			vm_mdl = 0;
			vm_frm = 0;
			if (!(fl & 4) && (fl & 8) && p.weaponmodel != "")
			{
				// Look up the modelindex of p.weaponmodel without mutating p.modelindex:
				// use p.kc_relay if present or match via temp field? We can cache on a helper or use setmodel on a scratch entity!
				vm_frm = p.weaponframe;
			}
			kc_p_vm[p_idx] = vm_mdl;
			kc_p_vfrm[p_idx] = vm_frm;
			// Store weapon slot in upper bits of dn3 if needed, or resolve weaponmodel index via scratch entity below
			if (!(fl & 4) && (fl & 8) && p.weaponmodel != "")
			{
				if (!p.kc_relay)
				{
					// Lazily create scratch/relay entity once so we can resolve p.weaponmodel -> modelindex cleanly
				}
			}

			p.kc_fire_pending = 0;
			p.kc_fire_snd = 0;
			p.kc_has_shot_end = FALSE;
		}
		p = p.bm_player_next;
	}

	// Sample active projectiles from proj_collide lists (fast, no full edict scan)
	pr_cnt = 0;
	base_pr = t_idx * KC_LIVE_PROJ;
	e = pc_head;
	while (e && pr_cnt < KC_LIVE_PROJ)
	{
		if (!bm_wasfreed (e) && e.modelindex > 0 && e.classname != "misc_vehicle_johnbird")
		{
			kc_pr_org[base_pr + pr_cnt] = e.origin;
			kc_pr_ang[base_pr + pr_cnt] = e.angles;
			kc_pr_mdl[base_pr + pr_cnt] = e.modelindex;
			kc_pr_frm[base_pr + pr_cnt] = e.frame;
			kc_pr_sc[base_pr + pr_cnt] = (e.scale > 0) ? e.scale : 1;
			pr_cnt = pr_cnt + 1;
		}
		e = e.pc_next;
	}
	e = pc_spike_head;
	while (e && pr_cnt < KC_LIVE_PROJ)
	{
		if (!bm_wasfreed (e) && e.modelindex > 0)
		{
			kc_pr_org[base_pr + pr_cnt] = e.origin;
			kc_pr_ang[base_pr + pr_cnt] = e.angles;
			kc_pr_mdl[base_pr + pr_cnt] = e.modelindex;
			kc_pr_frm[base_pr + pr_cnt] = e.frame;
			kc_pr_sc[base_pr + pr_cnt] = (e.scale > 0) ? e.scale : 1;
			pr_cnt = pr_cnt + 1;
		}
		e = e.pc_spike_next;
	}
	kc_pr_cnt[t_idx] = pr_cnt;

	kc_head = kc_head + 1;
	if (kc_head >= KC_HIST)
		kc_head = 0;
	if (kc_count < KC_HIST)
		kc_count = kc_count + 1;
};

// Scratch entity used only to resolve weaponmodel string -> precache modelindex
entity	kc_mdl_scratch;

float(string mdl) KC_ResolveModelIndex =
{
	if (mdl == "")
		return 0;
	if (!kc_mdl_scratch || bm_wasfreed (kc_mdl_scratch))
	{
		kc_mdl_scratch = spawn ();
		kc_mdl_scratch.classname = "kc_mdl_scratch";
		kc_mdl_scratch.solid = SOLID_NOT;
		kc_mdl_scratch.movetype = MOVETYPE_NONE;
		kc_mdl_scratch.effects = EF_NODRAW;
	}
	setmodel (kc_mdl_scratch, mdl);
	return kc_mdl_scratch.modelindex;
};

string(entity p) KC_FallbackVModel =
{
	local float w;

	w = p.weapon;
	if (w == IT_AXE)				return "progs/v_hammer.mdl";
	if (w == IT_SHOTGUN)			return "progs/v_shot.mdl";
	if (w == IT_NAILGUN)			return "progs/v_nail.mdl";
	if (w == IT_SUPER_NAILGUN)		return "progs/v_nail2.mdl";
	if (w == IT_GRENADE_LAUNCHER)	return "progs/v_rock.mdl";
	if (w == IT_ROCKET_LAUNCHER)	return "progs/v_rock2.mdl";
	if (w == IT_LIGHTNING)			return "progs/v_light.mdl";
	if (w == IT_LASER_CANNON)		return "progs/v_laserg.mdl";
	if (w == IT_MEGAMAN)			return "progs/v_mm_cannon.md3";
	if (w == IT_FUNGUN)				return FunGun_VModel (p.fg_sel);
	return "";
};

// Fill missing viewmodel modelindex on the newest tick (called inside KC_RecordSample wrapper)
void(float t_idx) KC_RecordViewmodels =
{
	local entity p;
	local float slot, p_idx;
	local string vmdl;

	p = bm_player_head;
	while (p)
	{
		slot = KC_SlotOf (p);
		if (slot >= 0 && !p.bm_obs)
		{
			p_idx = t_idx * KC_MAX_P + slot;
			if ((kc_p_fl[p_idx] & 8) && !(kc_p_fl[p_idx] & 4))
			{
				vmdl = p.weaponmodel;
				if (vmdl == "" && p.weapon != IT_SUPER_SHOTGUN)
					vmdl = KC_FallbackVModel (p);
				if (vmdl != "")
					kc_p_vm[p_idx] = KC_ResolveModelIndex (vmdl);
			}
		}
		p = p.bm_player_next;
	}
};

// ---------------------------------------------------------------- snapshot & streaming

void(entity victim, entity attacker, entity inflictor) KC_FreezeSnapshot =
{
	local float sid, kslot, vslot, n, i, t_idx, oldest, dst, pid_k, pid_v, s;
	local float o_cnt, o_base, p_cnt, p_base, best_d, d, j, best_idx, used_mask, bit;
	local float live_base, live_n, best_p;
	local vector ref_org;
	local float kill_tick;

	sid = kc_snap_rr;
	kc_snap_rr = kc_snap_rr + 1;
	if (kc_snap_rr >= KC_MAX_SNAPS)
		kc_snap_rr = 0;

	victim.kc_snap_id = sid;
	kslot = KC_SlotOf (attacker);
	vslot = KC_SlotOf (victim);

	n = kc_count;
	if (n <= 0)
		n = 1;
	if (n > KC_HIST)
		n = KC_HIST;

	oldest = kc_head - n;
	if (oldest < 0)
		oldest = oldest + KC_HIST;

	if (kc_s_kname[sid] != "")
		strunzone (kc_s_kname[sid]);
	if (kc_s_wname[sid] != "")
		strunzone (kc_s_wname[sid]);
	kc_s_kname[sid] = strzone ((attacker.netname != "") ? attacker.netname : "Player");
	kc_s_wname[sid] = strzone (KC_WeaponLabel (attacker, inflictor));
	kc_s_nframes[sid] = n;
	kc_s_seq[sid] = victim.kc_seq;
	kill_tick = n - 1;

	for (i = 0; i < n; i = i + 1)
	{
		t_idx = oldest + i;
		if (t_idx >= KC_HIST)
			t_idx = t_idx - KC_HIST;
		dst = sid * KC_HIST + i;

		// Killer
		pid_k = t_idx * KC_MAX_P + kslot;
		if (kslot >= 0 && kc_p_mdl[pid_k] > 0)
		{
			kc_sk_eye[dst] = kc_p_eye[pid_k];
			kc_sk_ang[dst] = kc_p_ang[pid_k];
			kc_sk_org[dst] = kc_p_org[pid_k];
			kc_sk_yaw[dst] = kc_p_yaw[pid_k];
			kc_sk_mdl[dst] = kc_p_mdl[pid_k];
			kc_sk_frm[dst] = kc_p_frm[pid_k];
			kc_sk_skin[dst] = kc_p_skin[pid_k];
			kc_sk_col[dst] = kc_p_col[pid_k];
			kc_sk_vm[dst] = kc_p_vm[pid_k];
			kc_sk_vfrm[dst] = kc_p_vfrm[pid_k];
			kc_sk_fl[dst] = kc_p_fl[pid_k];
			kc_sk_snd[dst] = kc_p_snd[pid_k];
			kc_sk_dn3[dst] = kc_p_dn3[pid_k];
			kc_sk_tend[dst] = kc_p_tend[pid_k];
			if (kc_p_fl[pid_k] & 2)
				kill_tick = i;
		}
		else
		{
			kc_sk_eye[dst] = (attacker.clientcamera != world && attacker.clientcamera != attacker) ? attacker.clientcamera.origin : (attacker.origin + attacker.view_ofs);
			kc_sk_ang[dst] = attacker.v_angle;
			kc_sk_org[dst] = attacker.origin;
			kc_sk_yaw[dst] = attacker.angles_y;
			kc_sk_mdl[dst] = attacker.modelindex;
			kc_sk_frm[dst] = attacker.frame;
			kc_sk_skin[dst] = attacker.skin;
			kc_sk_col[dst] = attacker.colormap;
			kc_sk_vm[dst] = KC_ResolveModelIndex (attacker.weaponmodel);
			kc_sk_vfrm[dst] = attacker.weaponframe;
			kc_sk_fl[dst] = 8;
			kc_sk_snd[dst] = KC_WeaponSoundCode (attacker);
			kc_sk_dn3[dst] = attacker.dn3_st_frame;
			kc_sk_tend[dst] = victim.origin + '0 0 18';
		}

		// Force hitmarker & fatal-shot tracer on the final tick
		if (i == n - 1)
		{
			kc_sk_fl[dst] = kc_sk_fl[dst] | 2;
			if (!(kc_sk_fl[dst] & 16))
			{
				kc_sk_fl[dst] = kc_sk_fl[dst] | 16;
				kc_sk_tend[dst] = victim.origin + '0 0 18';
			}
		}

		// Victim
		pid_v = t_idx * KC_MAX_P + vslot;
		if (vslot >= 0 && kc_p_mdl[pid_v] > 0)
		{
			kc_sv_org[dst] = kc_p_org[pid_v];
			kc_sv_yaw[dst] = kc_p_yaw[pid_v];
			kc_sv_mdl[dst] = kc_p_mdl[pid_v];
			kc_sv_frm[dst] = kc_p_frm[pid_v];
			kc_sv_skin[dst] = kc_p_skin[pid_v];
			kc_sv_col[dst] = kc_p_col[pid_v];
			kc_sv_alive[dst] = (kc_p_fl[pid_v] & 8) ? 1 : 0;
		}
		else
		{
			kc_sv_org[dst] = victim.origin;
			kc_sv_yaw[dst] = victim.angles_y;
			kc_sv_mdl[dst] = victim.modelindex;
			kc_sv_frm[dst] = victim.frame;
			kc_sv_skin[dst] = victim.skin;
			kc_sv_col[dst] = victim.colormap;
			kc_sv_alive[dst] = (i < n - 1) ? 1 : 0;
		}

		ref_org = kc_sk_eye[dst];

		// Pick up to KC_MAX_OTH (3) closest other players within 2000u
		o_cnt = 0;
		o_base = dst * KC_MAX_OTH;
		used_mask = 0;
		for (j = 0; j < KC_MAX_OTH; j = j + 1)
		{
			best_idx = -1;
			best_d = 2000;
			bit = 1;
			for (s = 0; s < KC_MAX_P; s = s + 1)
			{
				if (s != kslot && s != vslot && !(used_mask & bit))
				{
					pid_v = t_idx * KC_MAX_P + s;
					if ((kc_p_fl[pid_v] & 8) && kc_p_mdl[pid_v] > 0)
					{
						d = vlen (kc_p_org[pid_v] - ref_org);
						if (d < best_d)
						{
							best_d = d;
							best_idx = s;
						}
					}
				}
				bit = bit * 2;
			}
			if (best_idx < 0)
				break;
			bit = pow (2, best_idx);
			used_mask = used_mask | bit;
			pid_v = t_idx * KC_MAX_P + best_idx;
			kc_so_org[o_base + o_cnt] = kc_p_org[pid_v];
			kc_so_yaw[o_base + o_cnt] = kc_p_yaw[pid_v];
			kc_so_mdl[o_base + o_cnt] = kc_p_mdl[pid_v];
			kc_so_frm[o_base + o_cnt] = kc_p_frm[pid_v];
			kc_so_skin[o_base + o_cnt] = kc_p_skin[pid_v];
			kc_so_col[o_base + o_cnt] = kc_p_col[pid_v];
			o_cnt = o_cnt + 1;
		}
		kc_so_cnt[dst] = o_cnt;

		// Pick up to KC_MAX_PROJ (6) closest projectiles within 2200u
		p_cnt = 0;
		p_base = dst * KC_MAX_PROJ;
		live_base = t_idx * KC_LIVE_PROJ;
		live_n = kc_pr_cnt[t_idx];
		used_mask = 0;
		for (j = 0; j < KC_MAX_PROJ; j = j + 1)
		{
			best_p = -1;
			best_d = 2200;
			bit = 1;
			for (s = 0; s < live_n; s = s + 1)
			{
				if (!(used_mask & bit))
				{
					d = vlen (kc_pr_org[live_base + s] - ref_org);
					if (d < best_d)
					{
						best_d = d;
						best_p = s;
					}
				}
				bit = bit * 2;
			}
			if (best_p < 0)
				break;
			used_mask = used_mask | pow (2, best_p);
			kc_sp_org[p_base + p_cnt] = kc_pr_org[live_base + best_p];
			kc_sp_ang[p_base + p_cnt] = kc_pr_ang[live_base + best_p];
			kc_sp_mdl[p_base + p_cnt] = kc_pr_mdl[live_base + best_p];
			kc_sp_frm[p_base + p_cnt] = kc_pr_frm[live_base + best_p];
			kc_sp_sc[p_base + p_cnt] = kc_pr_sc[live_base + best_p];
			p_cnt = p_cnt + 1;
		}
		kc_sp_cnt[dst] = p_cnt;
	}
	kc_s_kill_tick[sid] = kill_tick;
};

void(float sid, float fidx) KC_WriteFrame =
{
	local float dst, fl, n_oth, n_prj, i, o_base, p_base;
	local vector v;

	dst = sid * KC_HIST + fidx;
	fl = kc_sk_fl[dst];

	v = kc_sk_eye[dst];
	WriteCoord (MSG_ENTITY, v_x);
	WriteCoord (MSG_ENTITY, v_y);
	WriteCoord (MSG_ENTITY, v_z);
	v = kc_sk_ang[dst];
	WriteShort (MSG_ENTITY, KC_PackShortAng (v_x));
	WriteShort (MSG_ENTITY, KC_PackShortAng (v_y));
	WriteShort (MSG_ENTITY, kc_sk_vm[dst]);
	WriteByte (MSG_ENTITY, bound (0, kc_sk_vfrm[dst], 255));
	WriteByte (MSG_ENTITY, fl);
	WriteByte (MSG_ENTITY, kc_sk_snd[dst]);
	WriteShort (MSG_ENTITY, kc_sk_dn3[dst]);
	if (fl & 4)
	{
		v = kc_sk_org[dst];
		WriteCoord (MSG_ENTITY, v_x);
		WriteCoord (MSG_ENTITY, v_y);
		WriteCoord (MSG_ENTITY, v_z);
		WriteByte (MSG_ENTITY, KC_PackByteAng (kc_sk_yaw[dst]));
		WriteShort (MSG_ENTITY, kc_sk_mdl[dst]);
		WriteByte (MSG_ENTITY, bound (0, kc_sk_frm[dst], 255));
		WriteByte (MSG_ENTITY, bound (0, kc_sk_skin[dst], 255));
		WriteByte (MSG_ENTITY, bound (0, kc_sk_col[dst], 255));
	}
	if (fl & 16)
	{
		v = kc_sk_tend[dst];
		WriteCoord (MSG_ENTITY, v_x);
		WriteCoord (MSG_ENTITY, v_y);
		WriteCoord (MSG_ENTITY, v_z);
	}

	// Victim
	v = kc_sv_org[dst];
	WriteCoord (MSG_ENTITY, v_x);
	WriteCoord (MSG_ENTITY, v_y);
	WriteCoord (MSG_ENTITY, v_z);
	WriteByte (MSG_ENTITY, KC_PackByteAng (kc_sv_yaw[dst]));
	WriteShort (MSG_ENTITY, kc_sv_mdl[dst]);
	WriteByte (MSG_ENTITY, bound (0, kc_sv_frm[dst], 255));
	WriteByte (MSG_ENTITY, bound (0, kc_sv_skin[dst], 255));
	WriteByte (MSG_ENTITY, bound (0, kc_sv_col[dst], 255));
	WriteByte (MSG_ENTITY, kc_sv_alive[dst]);

	// Nearby others
	n_oth = kc_so_cnt[dst];
	WriteByte (MSG_ENTITY, n_oth);
	o_base = dst * KC_MAX_OTH;
	for (i = 0; i < n_oth; i = i + 1)
	{
		v = kc_so_org[o_base + i];
		WriteCoord (MSG_ENTITY, v_x);
		WriteCoord (MSG_ENTITY, v_y);
		WriteCoord (MSG_ENTITY, v_z);
		WriteByte (MSG_ENTITY, KC_PackByteAng (kc_so_yaw[o_base + i]));
		WriteShort (MSG_ENTITY, kc_so_mdl[o_base + i]);
		WriteByte (MSG_ENTITY, bound (0, kc_so_frm[o_base + i], 255));
		WriteByte (MSG_ENTITY, bound (0, kc_so_skin[o_base + i], 255));
		WriteByte (MSG_ENTITY, bound (0, kc_so_col[o_base + i], 255));
	}

	// Projectiles
	n_prj = kc_sp_cnt[dst];
	WriteByte (MSG_ENTITY, n_prj);
	p_base = dst * KC_MAX_PROJ;
	for (i = 0; i < n_prj; i = i + 1)
	{
		v = kc_sp_org[p_base + i];
		WriteCoord (MSG_ENTITY, v_x);
		WriteCoord (MSG_ENTITY, v_y);
		WriteCoord (MSG_ENTITY, v_z);
		v = kc_sp_ang[p_base + i];
		WriteByte (MSG_ENTITY, KC_PackByteAng (v_x));
		WriteByte (MSG_ENTITY, KC_PackByteAng (v_y));
		WriteShort (MSG_ENTITY, kc_sp_mdl[p_base + i]);
		WriteByte (MSG_ENTITY, bound (0, kc_sp_frm[p_base + i], 255));
		WriteByte (MSG_ENTITY, bound (1, rint (kc_sp_sc[p_base + i] * 32), 255));
	}
};

float(entity to, float sendflags) KC_RelaySend =
{
	local float sid, nframes, chunk, bit, f0, f1, f;

	if (to != self.owner || to.bm_obs || to.kc_state == KC_NONE)
		return FALSE;

	// DarkPlaces passes 0xFFFFFF when an entity first enters PVS; never dump all 9 chunks in one packet
	if (sendflags > 511)
		sendflags = 1;

	sid = to.kc_snap_id;
	nframes = kc_s_nframes[sid];

	WriteByte (MSG_ENTITY, ENT_BM_KILLCAM);
	WriteShort (MSG_ENTITY, sendflags);
	WriteByte (MSG_ENTITY, kc_s_seq[sid]);

	if (sendflags & 1)
	{
		WriteByte (MSG_ENTITY, nframes);
		WriteByte (MSG_ENTITY, kc_s_kill_tick[sid]);
		WriteString (MSG_ENTITY, kc_s_kname[sid]);
		WriteString (MSG_ENTITY, kc_s_wname[sid]);
	}

	bit = 1;
	for (chunk = 0; chunk < 9; chunk = chunk + 1)
	{
		if (sendflags & bit)
		{
			f0 = chunk * KC_CHUNK_FRAMES;
			f1 = min (nframes, f0 + KC_CHUNK_FRAMES);
			WriteByte (MSG_ENTITY, f0);
			WriteByte (MSG_ENTITY, max (0, f1 - f0));
			for (f = f0; f < f1; f = f + 1)
				KC_WriteFrame (sid, f);
		}
		bit = bit * 2;
	}
	return TRUE;
};

void(entity p) KC_EnsureRelay =
{
	local entity r;

	if (p.kc_relay != world && !bm_wasfreed (p.kc_relay))
		return;
	r = spawn ();
	r.classname = "kc_relay";
	r.owner = p;
	setmodel (r, "progs/spike.mdl");
	setsize (r, '0 0 0', '0 0 0');
	r.alpha = 0.0001;
	r.scale = 0.01;
	r.SendEntity = KC_RelaySend;
	p.kc_relay = r;
};

// ---------------------------------------------------------------- lifecycle

void(entity p) KC_Reset =
{
	if (!p || p == world)
		return;
	if (p.kc_cam != world)
	{
		if (!bm_wasfreed (p.kc_cam))
			remove (p.kc_cam);
		p.kc_cam = world;
	}
	if (p.clientcamera != p && p.ishuman == 1 && !p.bm_obs)
	{
		p.clientcamera = p;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, p);
	}
	p.kc_state = KC_NONE;
	p.kc_st_active = 0;
	p.kc_sent_chunks = 0;
};

void(entity targ, entity attacker, entity inflictor) KC_OnPlayerKilled =
{
	if (!deathmatch || !autocvar_bm_killcam || intermission_running)
		return;
	if (!targ || targ.classname != "player" || targ.ishuman != 1 || targ.bm_obs)
		return;
	if (!attacker || attacker.classname != "player" || attacker == targ || attacker.bm_obs)
		return;
	if (!targ.kc_enabled)
		return;

	KC_EnsureRelay (targ);

	targ.kc_seq = targ.kc_seq + 1;
	if (targ.kc_seq > 255 || targ.kc_seq < 1)
		targ.kc_seq = 1;

	KC_FreezeSnapshot (targ, attacker, inflictor);

	targ.kc_state = KC_LINGER;
	targ.kc_linger_end = time + KC_LINGER_SEC;
	targ.kc_play_t0 = targ.kc_linger_end;
	targ.kc_end = targ.kc_linger_end + KC_PLAY_SEC;
	targ.kc_skip_armed = FALSE;
	targ.kc_sent_chunks = 0;
	targ.kc_next_chunk_t = time;
	targ.kc_st_active = KC_LINGER;
	targ.kc_st_seq = targ.kc_seq;

	setorigin (targ.kc_relay, targ.origin);
};

// Map playback elapsed seconds -> interpolated frame index [0..nframes-1] for server PVS tracking
vector(float sid, float elapsed) KC_EvalPVSPos =
{
	local float n, split_f, t_fast, u, f, f0, f1, frac;

	n = kc_s_nframes[sid];
	if (n <= 1)
		return kc_sk_eye[sid * KC_HIST];

	split_f = max (0, n - 6);
	t_fast = 1.90;
	if (elapsed <= t_fast)
		f = (elapsed / t_fast) * split_f;
	else
	{
		u = bound (0, (elapsed - t_fast) / max (0.05, KC_PLAY_SEC - t_fast), 1);
		f = split_f + u * (n - 1 - split_f);
	}
	f0 = bound (0, floor (f), n - 1);
	f1 = min (n - 1, f0 + 1);
	frac = f - f0;
	return kc_sk_eye[sid * KC_HIST + f0] * (1 - frac) + kc_sk_eye[sid * KC_HIST + f1] * frac;
};

void(entity p) KC_StreamForPlayer =
{
	local float chunk, bit, nframes, need_chunks;
	local entity cam;
	local vector pos;

	if (p.kc_state == KC_NONE)
		return;
	if (intermission_running || !p.kc_enabled || !autocvar_bm_killcam)
	{
		KC_Reset (p);
		return;
	}

	if (p.kc_relay != world && !bm_wasfreed (p.kc_relay))
		setorigin (p.kc_relay, (p.clientcamera != world && p.clientcamera != p) ? p.clientcamera.origin : p.origin);

	// Queue 9 reliable chunks at ~25 Hz (finishes by ~0.36s during the 0.55s linger)
	nframes = kc_s_nframes[p.kc_snap_id];
	need_chunks = ceil (nframes / KC_CHUNK_FRAMES);
	if (p.kc_sent_chunks < pow (2, need_chunks) - 1 && time >= p.kc_next_chunk_t)
	{
		bit = 1;
		for (chunk = 0; chunk < need_chunks; chunk = chunk + 1)
		{
			if (!(p.kc_sent_chunks & bit))
			{
				p.kc_sent_chunks = p.kc_sent_chunks | bit;
				p.kc_relay.SendFlags = p.kc_relay.SendFlags | bit;
				p.kc_next_chunk_t = time + 0.035;
				break;
			}
			bit = bit * 2;
		}
	}

	if (p.kc_state == KC_LINGER && time >= p.kc_linger_end)
	{
		p.kc_state = KC_PLAYING;
		p.kc_play_t0 = time;
		p.kc_end = time + KC_PLAY_SEC;
		p.kc_st_active = KC_PLAYING;

		cam = p.kc_cam;
		if (!cam || bm_wasfreed (cam))
		{
			cam = spawn ();
			cam.classname = "kc_cam";
			cam.movetype = MOVETYPE_NONE;
			cam.solid = SOLID_NOT;
			cam.alpha = 0.01;
			cam.scale = 0.01;
			setmodel (cam, "progs/spike.mdl");
			setsize (cam, '0 0 0', '0 0 0');
			p.kc_cam = cam;
		}
		pos = KC_EvalPVSPos (p.kc_snap_id, 0);
		setorigin (cam, pos);
		p.clientcamera = cam;
		msg_entity = p;
		WriteByte (MSG_ONE, 5);		// svc_setview
		WriteEntity (MSG_ONE, cam);
	}
	else if (p.kc_state == KC_PLAYING && p.kc_cam != world && !bm_wasfreed (p.kc_cam))
	{
		pos = KC_EvalPVSPos (p.kc_snap_id, time - p.kc_play_t0);
		setorigin (p.kc_cam, pos);
	}
};

void() KC_Tick =
{
	local entity p;
	local float recorded_idx;

	if (!deathmatch || !autocvar_bm_killcam || intermission_running)
	{
		p = bm_player_head;
		while (p)
		{
			if (p.ishuman == 1 && p.kc_state != KC_NONE)
				KC_Reset (p);
			p = p.bm_player_next;
		}
		return;
	}

	if (time >= kc_next_t)
	{
		recorded_idx = kc_head;
		KC_RecordSample ();
		KC_RecordViewmodels (recorded_idx);
		kc_next_t = time + KC_DT;
	}

	p = bm_player_head;
	while (p)
	{
		if (p.ishuman == 1 && p.kc_state != KC_NONE)
			KC_StreamForPlayer (p);
		p = p.bm_player_next;
	}
};

// Called from PlayerDeathThink in client.qc; returns TRUE if killcam owns death input/respawn right now
float(entity p) KC_DeathThink =
{
	if (p.kc_state == KC_NONE)
		return FALSE;

	if (!(p.button0 || p.button1 || p.button2))
		p.kc_skip_armed = TRUE;

	// Skip anytime (after releasing held button from moment of death) or auto-respawn when done
	if ((p.kc_skip_armed && (p.button0 || p.button2)) || time >= p.kc_end)
	{
		p.button0 = 0;
		p.button1 = 0;
		p.button2 = 0;
		KC_Reset (p);
		respawn ();
		return TRUE;
	}
	return TRUE;
};
