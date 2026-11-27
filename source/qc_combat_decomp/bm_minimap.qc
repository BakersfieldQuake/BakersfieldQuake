/*
================
bm_minimap.qc — Server-side CoD floorplan tactical radar feed (ENT_BM_RADAR)

Streams:
  - Live enemy coordinates + facing yaw at ~10 Hz (up to 16 closest enemies).
  - Big power-up locations (excluding suit pickups) for in-range display.
  - Nearby unoccupied vehicles when the player is walking near them (~600-720u).
================
*/

float	mm_sv_pu_cnt;
vector	mm_sv_pu_pos[36];
float	mm_sv_pu_kind[36];

vector	mm_sv_veh_pos[8];
float	mm_sv_veh_yaw[8];
float	mm_sv_veh_kind[8];
float	mm_sv_veh_dist[8];

float(entity a, entity b) BM_Radar_IsAlly =
{
	if (!a || !b || a == world || b == world)
		return FALSE;
	if (a == b)
		return TRUE;
	if (a.classname == "player" && b.classname == "player")
	{
		if (coop)
			return TRUE;
		if ((teamplay || CTF_ENABLED) && a.team > 0 && a.team == b.team)
			return TRUE;
	}
	return FALSE;
};

float(float y) BM_Radar_PackYaw =
{
	local float a;

	a = y - 360 * floor (y / 360);
	return bound (0, floor (a * 255 / 360 + 0.5), 255);
};

vector(entity e) BM_Radar_EntityPos =
{
	if (e.veh_van != world && !bm_wasfreed (e.veh_van))
		return e.veh_van.origin;
	if (e.mmt_tank != world && !bm_wasfreed (e.mmt_tank))
		return e.mmt_tank.origin;
	if (e.jb_vehicle != world && !bm_wasfreed (e.jb_vehicle))
		return e.jb_vehicle.origin;
	if (e.rr_vehicle != world && !bm_wasfreed (e.rr_vehicle))
		return e.rr_vehicle.origin;
	return e.origin;
};

float(entity e) BM_Radar_EntityYaw =
{
	if (e.veh_van != world && !bm_wasfreed (e.veh_van))
		return e.veh_van.angles_y;
	if (e.mmt_tank != world && !bm_wasfreed (e.mmt_tank))
		return e.mmt_tank.angles_y;
	if (e.jb_vehicle != world && !bm_wasfreed (e.jb_vehicle))
		return e.jb_vehicle.angles_y;
	if (e.rr_vehicle != world && !bm_wasfreed (e.rr_vehicle))
		return e.rr_vehicle.angles_y;
	return e.angles_y;
};

void(entity feed, float idx, vector pos, float yaw, float flg) BM_Radar_WriteEnemySlot =
{
	if (idx == 0)       { feed.bm_re0_pos = pos;  feed.bm_re0_yaw = yaw;  feed.bm_re0_flg = flg; }
	else if (idx == 1)  { feed.bm_re1_pos = pos;  feed.bm_re1_yaw = yaw;  feed.bm_re1_flg = flg; }
	else if (idx == 2)  { feed.bm_re2_pos = pos;  feed.bm_re2_yaw = yaw;  feed.bm_re2_flg = flg; }
	else if (idx == 3)  { feed.bm_re3_pos = pos;  feed.bm_re3_yaw = yaw;  feed.bm_re3_flg = flg; }
	else if (idx == 4)  { feed.bm_re4_pos = pos;  feed.bm_re4_yaw = yaw;  feed.bm_re4_flg = flg; }
	else if (idx == 5)  { feed.bm_re5_pos = pos;  feed.bm_re5_yaw = yaw;  feed.bm_re5_flg = flg; }
	else if (idx == 6)  { feed.bm_re6_pos = pos;  feed.bm_re6_yaw = yaw;  feed.bm_re6_flg = flg; }
	else if (idx == 7)  { feed.bm_re7_pos = pos;  feed.bm_re7_yaw = yaw;  feed.bm_re7_flg = flg; }
	else if (idx == 8)  { feed.bm_re8_pos = pos;  feed.bm_re8_yaw = yaw;  feed.bm_re8_flg = flg; }
	else if (idx == 9)  { feed.bm_re9_pos = pos;  feed.bm_re9_yaw = yaw;  feed.bm_re9_flg = flg; }
	else if (idx == 10) { feed.bm_re10_pos = pos; feed.bm_re10_yaw = yaw; feed.bm_re10_flg = flg; }
	else if (idx == 11) { feed.bm_re11_pos = pos; feed.bm_re11_yaw = yaw; feed.bm_re11_flg = flg; }
	else if (idx == 12) { feed.bm_re12_pos = pos; feed.bm_re12_yaw = yaw; feed.bm_re12_flg = flg; }
	else if (idx == 13) { feed.bm_re13_pos = pos; feed.bm_re13_yaw = yaw; feed.bm_re13_flg = flg; }
	else if (idx == 14) { feed.bm_re14_pos = pos; feed.bm_re14_yaw = yaw; feed.bm_re14_flg = flg; }
	else if (idx == 15) { feed.bm_re15_pos = pos; feed.bm_re15_yaw = yaw; feed.bm_re15_flg = flg; }
};

vector(entity feed, float idx) BM_Radar_ReadEnemyPos =
{
	if (idx == 0) return feed.bm_re0_pos;
	if (idx == 1) return feed.bm_re1_pos;
	if (idx == 2) return feed.bm_re2_pos;
	if (idx == 3) return feed.bm_re3_pos;
	if (idx == 4) return feed.bm_re4_pos;
	if (idx == 5) return feed.bm_re5_pos;
	if (idx == 6) return feed.bm_re6_pos;
	if (idx == 7) return feed.bm_re7_pos;
	if (idx == 8) return feed.bm_re8_pos;
	if (idx == 9) return feed.bm_re9_pos;
	if (idx == 10) return feed.bm_re10_pos;
	if (idx == 11) return feed.bm_re11_pos;
	if (idx == 12) return feed.bm_re12_pos;
	if (idx == 13) return feed.bm_re13_pos;
	if (idx == 14) return feed.bm_re14_pos;
	return feed.bm_re15_pos;
};

float(entity feed, float idx) BM_Radar_ReadEnemyYaw =
{
	if (idx == 0) return feed.bm_re0_yaw;
	if (idx == 1) return feed.bm_re1_yaw;
	if (idx == 2) return feed.bm_re2_yaw;
	if (idx == 3) return feed.bm_re3_yaw;
	if (idx == 4) return feed.bm_re4_yaw;
	if (idx == 5) return feed.bm_re5_yaw;
	if (idx == 6) return feed.bm_re6_yaw;
	if (idx == 7) return feed.bm_re7_yaw;
	if (idx == 8) return feed.bm_re8_yaw;
	if (idx == 9) return feed.bm_re9_yaw;
	if (idx == 10) return feed.bm_re10_yaw;
	if (idx == 11) return feed.bm_re11_yaw;
	if (idx == 12) return feed.bm_re12_yaw;
	if (idx == 13) return feed.bm_re13_yaw;
	if (idx == 14) return feed.bm_re14_yaw;
	return feed.bm_re15_yaw;
};

float(entity feed, float idx) BM_Radar_ReadEnemyFlg =
{
	if (idx == 0) return feed.bm_re0_flg;
	if (idx == 1) return feed.bm_re1_flg;
	if (idx == 2) return feed.bm_re2_flg;
	if (idx == 3) return feed.bm_re3_flg;
	if (idx == 4) return feed.bm_re4_flg;
	if (idx == 5) return feed.bm_re5_flg;
	if (idx == 6) return feed.bm_re6_flg;
	if (idx == 7) return feed.bm_re7_flg;
	if (idx == 8) return feed.bm_re8_flg;
	if (idx == 9) return feed.bm_re9_flg;
	if (idx == 10) return feed.bm_re10_flg;
	if (idx == 11) return feed.bm_re11_flg;
	if (idx == 12) return feed.bm_re12_flg;
	if (idx == 13) return feed.bm_re13_flg;
	if (idx == 14) return feed.bm_re14_flg;
	return feed.bm_re15_flg;
};

float(entity to, float sendflags) BM_RadarSend =
{
	local float i;
	local vector pos;

	if (to != self.owner || to.bm_obs)
		return FALSE;

	sendflags = sendflags & 26;
	if (!sendflags)
		sendflags = 26;

	WriteByte (MSG_ENTITY, ENT_BM_RADAR);
	WriteByte (MSG_ENTITY, sendflags);

	if (sendflags & 2)
	{
		WriteByte (MSG_ENTITY, self.bm_re_cnt);
		i = 0;
		while (i < self.bm_re_cnt)
		{
			pos = BM_Radar_ReadEnemyPos (self, i);
			WriteCoord (MSG_ENTITY, pos_x);
			WriteCoord (MSG_ENTITY, pos_y);
			WriteCoord (MSG_ENTITY, pos_z);
			WriteByte (MSG_ENTITY, BM_Radar_ReadEnemyYaw (self, i));
			WriteByte (MSG_ENTITY, BM_Radar_ReadEnemyFlg (self, i));
			i = i + 1;
		}
	}

	if (sendflags & 8)
	{
		WriteByte (MSG_ENTITY, mm_sv_pu_cnt);
		i = 0;
		while (i < mm_sv_pu_cnt)
		{
			pos = mm_sv_pu_pos[i];
			WriteByte (MSG_ENTITY, mm_sv_pu_kind[i]);
			WriteCoord (MSG_ENTITY, pos_x);
			WriteCoord (MSG_ENTITY, pos_y);
			WriteCoord (MSG_ENTITY, pos_z);
			i = i + 1;
		}
	}

	if (sendflags & 16)
	{
		WriteByte (MSG_ENTITY, self.bm_rv_cnt);
		if (self.bm_rv_cnt >= 1) { WriteByte (MSG_ENTITY, self.bm_rv0_kind); WriteCoord (MSG_ENTITY, self.bm_rv0_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv0_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv0_pos_z); WriteByte (MSG_ENTITY, self.bm_rv0_yaw); }
		if (self.bm_rv_cnt >= 2) { WriteByte (MSG_ENTITY, self.bm_rv1_kind); WriteCoord (MSG_ENTITY, self.bm_rv1_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv1_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv1_pos_z); WriteByte (MSG_ENTITY, self.bm_rv1_yaw); }
		if (self.bm_rv_cnt >= 3) { WriteByte (MSG_ENTITY, self.bm_rv2_kind); WriteCoord (MSG_ENTITY, self.bm_rv2_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv2_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv2_pos_z); WriteByte (MSG_ENTITY, self.bm_rv2_yaw); }
		if (self.bm_rv_cnt >= 4) { WriteByte (MSG_ENTITY, self.bm_rv3_kind); WriteCoord (MSG_ENTITY, self.bm_rv3_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv3_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv3_pos_z); WriteByte (MSG_ENTITY, self.bm_rv3_yaw); }
		if (self.bm_rv_cnt >= 5) { WriteByte (MSG_ENTITY, self.bm_rv4_kind); WriteCoord (MSG_ENTITY, self.bm_rv4_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv4_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv4_pos_z); WriteByte (MSG_ENTITY, self.bm_rv4_yaw); }
		if (self.bm_rv_cnt >= 6) { WriteByte (MSG_ENTITY, self.bm_rv5_kind); WriteCoord (MSG_ENTITY, self.bm_rv5_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv5_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv5_pos_z); WriteByte (MSG_ENTITY, self.bm_rv5_yaw); }
		if (self.bm_rv_cnt >= 7) { WriteByte (MSG_ENTITY, self.bm_rv6_kind); WriteCoord (MSG_ENTITY, self.bm_rv6_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv6_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv6_pos_z); WriteByte (MSG_ENTITY, self.bm_rv6_yaw); }
		if (self.bm_rv_cnt >= 8) { WriteByte (MSG_ENTITY, self.bm_rv7_kind); WriteCoord (MSG_ENTITY, self.bm_rv7_pos_x); WriteCoord (MSG_ENTITY, self.bm_rv7_pos_y); WriteCoord (MSG_ENTITY, self.bm_rv7_pos_z); WriteByte (MSG_ENTITY, self.bm_rv7_yaw); }
	}

	return TRUE;
};

void(entity p) BM_Radar_ClientGone =
{
	if (!p)
		return;
	if (p.bm_radar_ent)
	{
		if (!bm_wasfreed (p.bm_radar_ent) && p.bm_radar_ent.classname == "bm_radar_feed" && p.bm_radar_ent.owner == p)
			remove (p.bm_radar_ent);
		p.bm_radar_ent = world;
	}
};

entity(entity p) BM_Radar_EnsureFeed =
{
	local entity f;

	if (!p || p.ishuman != 1 || p.bm_obs)
		return world;
	f = p.bm_radar_ent;
	if (!f || bm_wasfreed (f) || f.classname != "bm_radar_feed" || f.owner != p)
	{
		f = spawn ();
		f.classname = "bm_radar_feed";
		f.owner = p;
		setmodel (f, "progs/s_bubble.spr");
		setsize (f, '0 0 0', '0 0 0');
		f.alpha = 0.0001;
		f.SendEntity = BM_RadarSend;
		f.bm_rpu_ver_sent = -1;
		p.bm_radar_ent = f;
	}
	if (vlen (f.origin - p.origin) > 64 || f.SendFlags != 0)
		setorigin (f, p.origin);
	return f;
};

void(entity feed, float kind, vector org) BM_Radar_PushPing =
{
	local float idx, seq;

	if (!feed)
		return;
	seq = feed.bm_rp_seq_gen + 1;
	if (seq > 255)
		seq = 1;
	feed.bm_rp_seq_gen = seq;

	idx = feed.bm_rp_idx;
	if (idx == 0)
	{
		feed.bm_rp0_seq = seq;
		feed.bm_rp0_kind = kind;
		feed.bm_rp0_pos = org;
	}
	else if (idx == 1)
	{
		feed.bm_rp1_seq = seq;
		feed.bm_rp1_kind = kind;
		feed.bm_rp1_pos = org;
	}
	else if (idx == 2)
	{
		feed.bm_rp2_seq = seq;
		feed.bm_rp2_kind = kind;
		feed.bm_rp2_pos = org;
	}
	else
	{
		feed.bm_rp3_seq = seq;
		feed.bm_rp3_kind = kind;
		feed.bm_rp3_pos = org;
	}

	idx = idx + 1;
	if (idx >= 4)
		idx = 0;
	feed.bm_rp_idx = idx;
	feed.SendFlags = feed.SendFlags | 1;
};

// Pings disabled to keep the minimap focused on enemies, big power-ups, and nearby vehicles.
void(entity actor, vector org, float kind) BM_Radar_Ping =
{
	return;
};

vector mm_sv_pos[16];
float  mm_sv_yaw[16];
float  mm_sv_flg[16];
float  mm_sv_dist[16];

// Stream exact live coordinates of up to 16 closest living enemies to client `c`.
void(entity c) BM_Radar_UpdateClientEnemies =
{
	local entity feed, e;
	local vector eorg, porg, oldp;
	local float cnt, pass, d, eyaw, eflg, ins, k, worst_i, worst_d, chg;

	feed = BM_Radar_EnsureFeed (c);
	if (!feed)
		return;

	porg = BM_Radar_EntityPos (c);
	cnt = 0;

	// Pass 0: players & bots in DM / CTF. Pass 1: active monsters in SP / Coop.
	pass = 0;
	while (pass < 2)
	{
		if (pass == 0)
			e = bm_player_head;
		else if (!deathmatch)
			e = nextent (world);
		else
			e = world;

		while (e)
		{
			if (pass == 0)
			{
				if (e == c || e.bm_obs || e.health <= 0 || e.modelindex == 0
					|| (e.flags & FL_NOTARGET) || BM_Radar_IsAlly (c, e))
				{
					e = e.bm_player_next;
					continue;
				}
				eflg = 1;	// player / bot
				if (e.ishuman != 1)
					eflg = eflg | 2;
				if ((time - e.bm_lastshot) < 0.8 || (time - e.fg_fire_t) < 0.8)
					eflg = eflg | 4;
			}
			else
			{
				if (!(e.flags & FL_MONSTER) || e.health <= 0 || !e.takedamage || (e.flags & FL_NOTARGET))
				{
					e = nextent (e);
					continue;
				}
				eflg = 0;	// monster
				if (e.enemy != world)
					eflg = eflg | 4;
			}

			eorg = BM_Radar_EntityPos (e);
			eyaw = BM_Radar_PackYaw (BM_Radar_EntityYaw (e));
			d = vlen (eorg - porg);

			if (cnt < 16)
			{
				ins = cnt;
				cnt = cnt + 1;
			}
			else
			{
				worst_i = 0;
				worst_d = mm_sv_dist[0];
				k = 1;
				while (k < 16)
				{
					if (mm_sv_dist[k] > worst_d)
					{
						worst_d = mm_sv_dist[k];
						worst_i = k;
					}
					k = k + 1;
				}
				ins = (d < worst_d) ? worst_i : -1;
			}

			if (ins >= 0)
			{
				mm_sv_pos[ins] = eorg;
				mm_sv_yaw[ins] = eyaw;
				mm_sv_flg[ins] = eflg;
				mm_sv_dist[ins] = d;
			}

			if (pass == 0)
				e = e.bm_player_next;
			else
				e = nextent (e);
		}
		pass = pass + 1;
	}

	// Keep slot 0 as the closest enemy so CSQC always gets nearest-first even on truncated packets
	if (cnt > 1)
	{
		local float best_i, best_d;
		local vector tmp_v;
		local float tmp_f;

		best_i = 0;
		best_d = mm_sv_dist[0];
		k = 1;
		while (k < cnt)
		{
			if (mm_sv_dist[k] < best_d)
			{
				best_d = mm_sv_dist[k];
				best_i = k;
			}
			k = k + 1;
		}
		if (best_i != 0)
		{
			tmp_v = mm_sv_pos[0]; mm_sv_pos[0] = mm_sv_pos[best_i]; mm_sv_pos[best_i] = tmp_v;
			tmp_f = mm_sv_yaw[0]; mm_sv_yaw[0] = mm_sv_yaw[best_i]; mm_sv_yaw[best_i] = tmp_f;
			tmp_f = mm_sv_flg[0]; mm_sv_flg[0] = mm_sv_flg[best_i]; mm_sv_flg[best_i] = tmp_f;
			tmp_f = mm_sv_dist[0]; mm_sv_dist[0] = mm_sv_dist[best_i]; mm_sv_dist[best_i] = tmp_f;
		}
	}

	chg = (cnt != feed.bm_re_cnt);
	k = 0;
	while (k < cnt)
	{
		if (!chg)
		{
			oldp = BM_Radar_ReadEnemyPos (feed, k);
			if (vlen (mm_sv_pos[k] - oldp) > 8
				|| fabs (mm_sv_yaw[k] - BM_Radar_ReadEnemyYaw (feed, k)) > 4
				|| mm_sv_flg[k] != BM_Radar_ReadEnemyFlg (feed, k))
				chg = TRUE;
		}
		BM_Radar_WriteEnemySlot (feed, k, mm_sv_pos[k], mm_sv_yaw[k], mm_sv_flg[k]);
		k = k + 1;
	}
	feed.bm_re_cnt = cnt;
	if (chg)
		feed.SendFlags = feed.SendFlags | 2;
};

void(entity c) BM_Radar_UpdateClientAllies =
{
	local entity feed, p;
	local float cnt, chg, y;
	local vector apos;

	feed = BM_Radar_EnsureFeed (c);
	if (!feed)
		return;

	cnt = 0;
	chg = FALSE;
	p = bm_player_head;
	while (p && cnt < 4)
	{
		if (p != c && !p.bm_obs && p.health > 0 && BM_Radar_IsAlly (c, p))
		{
			apos = BM_Radar_EntityPos (p);
			y = BM_Radar_PackYaw (BM_Radar_EntityYaw (p));
			if (cnt == 0)
			{
				if (vlen (apos - feed.bm_ra0_pos) > 12 || fabs (y - feed.bm_ra0_yaw) > 4) chg = TRUE;
				feed.bm_ra0_pos = apos; feed.bm_ra0_yaw = y;
			}
			else if (cnt == 1)
			{
				if (vlen (apos - feed.bm_ra1_pos) > 12 || fabs (y - feed.bm_ra1_yaw) > 4) chg = TRUE;
				feed.bm_ra1_pos = apos; feed.bm_ra1_yaw = y;
			}
			else if (cnt == 2)
			{
				if (vlen (apos - feed.bm_ra2_pos) > 12 || fabs (y - feed.bm_ra2_yaw) > 4) chg = TRUE;
				feed.bm_ra2_pos = apos; feed.bm_ra2_yaw = y;
			}
			else
			{
				if (vlen (apos - feed.bm_ra3_pos) > 12 || fabs (y - feed.bm_ra3_yaw) > 4) chg = TRUE;
				feed.bm_ra3_pos = apos; feed.bm_ra3_yaw = y;
			}
			cnt = cnt + 1;
		}
		p = p.bm_player_next;
	}
	if (cnt != feed.bm_ra_cnt)
	{
		feed.bm_ra_cnt = cnt;
		chg = TRUE;
	}
	if (chg)
		feed.SendFlags = feed.SendFlags | 4;
};

void(entity e, float kind) BM_Radar_RegisterPowerup =
{
	if (!e || e == world || kind <= 0)
		return;
	if (e.bm_pu_kind > 0)
	{
		e.bm_pu_kind = kind;
		return;
	}
	e.bm_pu_kind = kind;
	e.bm_pu_next = bm_pu_head;
	bm_pu_head = e;
};

void() BM_Radar_RefreshPowerups =
{
	local entity e, prev, nxt;
	local float cnt, chg;
	local vector pos, oldp;

	cnt = 0;
	chg = FALSE;
	if (bm_pu_ver <= 0)
		bm_pu_ver = 1;

	prev = world;
	e = bm_pu_head;
	while (e)
	{
		nxt = e.bm_pu_next;
		if (bm_wasfreed (e) || e.bm_pu_kind <= 0)
		{
			if (prev == world)
				bm_pu_head = nxt;
			else
				prev.bm_pu_next = nxt;
			e = nxt;
			continue;
		}

		if (e.solid == SOLID_TRIGGER && e.model != "" && e.modelindex > 0
			&& e.bm_pu_kind != BM_RPU_SUIT && cnt < BM_MM_PU_MAX)
		{
			if (e.classname == "item_powerup_triple_wheeled" && e.tw_spawn_org != '0 0 0')
				pos = e.tw_spawn_org;
			else if (e.classname == "item_powerup_foreloco" && e.veh_spawn_org != '0 0 0')
				pos = e.veh_spawn_org;
			else
				pos = e.origin;

			if (cnt >= mm_sv_pu_cnt)
				chg = TRUE;
			else
			{
				oldp = mm_sv_pu_pos[cnt];
				if (mm_sv_pu_kind[cnt] != e.bm_pu_kind
					|| fabs (pos_x - oldp_x) > 16
					|| fabs (pos_y - oldp_y) > 16
					|| fabs (pos_z - oldp_z) > 16)
					chg = TRUE;
			}
			mm_sv_pu_pos[cnt] = pos;
			mm_sv_pu_kind[cnt] = e.bm_pu_kind;
			cnt = cnt + 1;
		}
		prev = e;
		e = nxt;
	}

	if (cnt != mm_sv_pu_cnt)
		chg = TRUE;
	mm_sv_pu_cnt = cnt;
	if (chg)
	{
		bm_pu_ver = bm_pu_ver + 1;
		if (bm_pu_ver > 1000000)
			bm_pu_ver = 1;
	}
};

void(entity v, float kind) BM_Radar_RegisterVehicle =
{
	if (!v || v == world || kind <= 0)
		return;
	if (v.bm_veh_kind > 0)
	{
		v.bm_veh_kind = kind;
		return;
	}
	v.bm_veh_kind = kind;
	v.bm_veh_next = bm_veh_head;
	bm_veh_head = v;
};

float(entity c) BM_Radar_PlayerOnFoot =
{
	if (c.veh_van != world || c.veh_ride != world || c.mmt_tank != world
		|| c.jb_vehicle != world || c.rr_vehicle != world
		|| c.ec_cannon_ent != world || c.fd_head != world)
		return FALSE;
	return TRUE;
};

float(entity v) BM_Radar_VehicleAvailable =
{
	if (v.classname == "misc_mm_tank")
		return (v.mmt_driver == world && v.mmt_state != MMT_STATE_WRECK && v.health > 0);
	if (v.classname == "misc_vehicle_johnbird")
		return (v.jb_pilot == world && !v.jb_dying && !v.jb_ai && v.health > 0 && !(v.effects & EF_NODRAW));
	if (v.classname == "misc_vehicle_rocketrider")
		return (v.rr_pilot == world && !v.rr_dying && v.health > 0 && !(v.effects & EF_NODRAW));
	if (v.classname == "misc_eric_cannon")
		return (v.ec_pilot == world && v.ec_state == 0);
	if (v.veh_kind > 0)
		return (v.veh_driver == world && v.veh_state != VEH_STATE_WRECK && v.health > 0 && !(v.effects & EF_NODRAW));
	return FALSE;
};

void(entity feed, float idx, vector pos, float yaw, float kind) BM_Radar_WriteVehSlot =
{
	if (idx == 0)      { feed.bm_rv0_pos = pos; feed.bm_rv0_yaw = yaw; feed.bm_rv0_kind = kind; }
	else if (idx == 1) { feed.bm_rv1_pos = pos; feed.bm_rv1_yaw = yaw; feed.bm_rv1_kind = kind; }
	else if (idx == 2) { feed.bm_rv2_pos = pos; feed.bm_rv2_yaw = yaw; feed.bm_rv2_kind = kind; }
	else if (idx == 3) { feed.bm_rv3_pos = pos; feed.bm_rv3_yaw = yaw; feed.bm_rv3_kind = kind; }
	else if (idx == 4) { feed.bm_rv4_pos = pos; feed.bm_rv4_yaw = yaw; feed.bm_rv4_kind = kind; }
	else if (idx == 5) { feed.bm_rv5_pos = pos; feed.bm_rv5_yaw = yaw; feed.bm_rv5_kind = kind; }
	else if (idx == 6) { feed.bm_rv6_pos = pos; feed.bm_rv6_yaw = yaw; feed.bm_rv6_kind = kind; }
	else if (idx == 7) { feed.bm_rv7_pos = pos; feed.bm_rv7_yaw = yaw; feed.bm_rv7_kind = kind; }
};

vector(entity feed, float idx) BM_Radar_ReadVehPos =
{
	if (idx == 0) return feed.bm_rv0_pos;
	if (idx == 1) return feed.bm_rv1_pos;
	if (idx == 2) return feed.bm_rv2_pos;
	if (idx == 3) return feed.bm_rv3_pos;
	if (idx == 4) return feed.bm_rv4_pos;
	if (idx == 5) return feed.bm_rv5_pos;
	if (idx == 6) return feed.bm_rv6_pos;
	return feed.bm_rv7_pos;
};

float(entity feed, float idx) BM_Radar_ReadVehYaw =
{
	if (idx == 0) return feed.bm_rv0_yaw;
	if (idx == 1) return feed.bm_rv1_yaw;
	if (idx == 2) return feed.bm_rv2_yaw;
	if (idx == 3) return feed.bm_rv3_yaw;
	if (idx == 4) return feed.bm_rv4_yaw;
	if (idx == 5) return feed.bm_rv5_yaw;
	if (idx == 6) return feed.bm_rv6_yaw;
	return feed.bm_rv7_yaw;
};

float(entity feed, float idx) BM_Radar_ReadVehKind =
{
	if (idx == 0) return feed.bm_rv0_kind;
	if (idx == 1) return feed.bm_rv1_kind;
	if (idx == 2) return feed.bm_rv2_kind;
	if (idx == 3) return feed.bm_rv3_kind;
	if (idx == 4) return feed.bm_rv4_kind;
	if (idx == 5) return feed.bm_rv5_kind;
	if (idx == 6) return feed.bm_rv6_kind;
	return feed.bm_rv7_kind;
};

void(entity c) BM_Radar_UpdateClientVehicles =
{
	local entity feed, v, prev, nxt;
	local float cnt, chg, k, d, max_d, vyaw, ins, worst_i, worst_d;
	local vector porg, oldp;

	feed = BM_Radar_EnsureFeed (c);
	if (!feed)
		return;

	cnt = 0;
	if (BM_Radar_PlayerOnFoot (c))
	{
		porg = BM_Radar_EntityPos (c);
		prev = world;
		v = bm_veh_head;
		while (v)
		{
			nxt = v.bm_veh_next;
			if (bm_wasfreed (v) || v.bm_veh_kind <= 0)
			{
				if (prev == world)
					bm_veh_head = nxt;
				else
					prev.bm_veh_next = nxt;
				v = nxt;
				continue;
			}
			prev = v;

			if (BM_Radar_VehicleAvailable (v))
			{
				max_d = (v.bm_veh_kind == BM_RVEH_MMTANK) ? BM_MM_VEH_RANGE_BIG : BM_MM_VEH_RANGE;
				d = vlen (v.origin - porg);
				if (d <= max_d)
				{
					vyaw = BM_Radar_PackYaw (v.angles_y);
					if (cnt < BM_MM_VEH_MAX)
					{
						ins = cnt;
						cnt = cnt + 1;
					}
					else
					{
						worst_i = 0;
						worst_d = mm_sv_veh_dist[0];
						k = 1;
						while (k < BM_MM_VEH_MAX)
						{
							if (mm_sv_veh_dist[k] > worst_d)
							{
								worst_d = mm_sv_veh_dist[k];
								worst_i = k;
							}
							k = k + 1;
						}
						ins = (d < worst_d) ? worst_i : -1;
					}
					if (ins >= 0)
					{
						mm_sv_veh_pos[ins] = v.origin;
						mm_sv_veh_yaw[ins] = vyaw;
						mm_sv_veh_kind[ins] = v.bm_veh_kind;
						mm_sv_veh_dist[ins] = d;
					}
				}
			}
			v = nxt;
		}
	}

	chg = (cnt != feed.bm_rv_cnt);
	k = 0;
	while (k < cnt)
	{
		if (!chg)
		{
			oldp = BM_Radar_ReadVehPos (feed, k);
			if (mm_sv_veh_kind[k] != BM_Radar_ReadVehKind (feed, k)
				|| vlen (mm_sv_veh_pos[k] - oldp) > 8
				|| fabs (mm_sv_veh_yaw[k] - BM_Radar_ReadVehYaw (feed, k)) > 4)
				chg = TRUE;
		}
		BM_Radar_WriteVehSlot (feed, k, mm_sv_veh_pos[k], mm_sv_veh_yaw[k], mm_sv_veh_kind[k]);
		k = k + 1;
	}
	feed.bm_rv_cnt = cnt;
	if (chg)
		feed.SendFlags = feed.SendFlags | 16;
};

void() BM_Radar_Tick =
{
	local entity p, feed;
	local float do_enemies, do_vehicles;

	if (bm_menubg_active || intermission_running)
		return;

	do_enemies = (time >= bm_radar_enemy_t);
	if (do_enemies)
		bm_radar_enemy_t = time + 0.1;

	do_vehicles = (time >= bm_radar_veh_t);
	if (do_vehicles)
		bm_radar_veh_t = time + 0.15;

	if (time >= bm_radar_pu_t)
	{
		bm_radar_pu_t = time + 0.35;
		BM_Radar_RefreshPowerups ();
	}

	p = bm_player_head;
	while (p)
	{
		if (p.ishuman == 1 && !p.bm_obs)
		{
			feed = BM_Radar_EnsureFeed (p);
			if (do_enemies)
				BM_Radar_UpdateClientEnemies (p);
			if (do_vehicles)
				BM_Radar_UpdateClientVehicles (p);
			if (feed && feed.bm_rpu_ver_sent != bm_pu_ver)
			{
				feed.bm_rpu_ver_sent = bm_pu_ver;
				feed.SendFlags = feed.SendFlags | 8;
			}
		}
		p = p.bm_player_next;
	}
};
