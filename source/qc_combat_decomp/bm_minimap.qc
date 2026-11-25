/*
================
bm_minimap.qc — Server-side anti-wallhack radar feed (ENT_BM_RADAR)

Never streams live enemy coordinates to clients:
  1. Gunfire / explosions / kills / monster attacks push a static, frozen ping at the event origin.
  2. Every 5.0 seconds, a coarse 256u-quantized + jittered heat snapshot clusters active combatants
     into ~320u fuzzy neighborhood zones (never exact positions).
  3. Only teammates (teamplay / CTF) and coop allies stream live positions (~5 Hz when moving).
================
*/

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

float(entity to, float sendflags) BM_RadarSend =
{
	if (to != self.owner || to.bm_obs)
		return FALSE;

	WriteByte (MSG_ENTITY, ENT_BM_RADAR);
	WriteByte (MSG_ENTITY, sendflags);

	if (sendflags & 1)
	{
		WriteByte (MSG_ENTITY, self.bm_rp0_seq);
		WriteByte (MSG_ENTITY, self.bm_rp0_kind);
		WriteCoord (MSG_ENTITY, self.bm_rp0_pos_x);
		WriteCoord (MSG_ENTITY, self.bm_rp0_pos_y);
		WriteCoord (MSG_ENTITY, self.bm_rp0_pos_z);

		WriteByte (MSG_ENTITY, self.bm_rp1_seq);
		WriteByte (MSG_ENTITY, self.bm_rp1_kind);
		WriteCoord (MSG_ENTITY, self.bm_rp1_pos_x);
		WriteCoord (MSG_ENTITY, self.bm_rp1_pos_y);
		WriteCoord (MSG_ENTITY, self.bm_rp1_pos_z);

		WriteByte (MSG_ENTITY, self.bm_rp2_seq);
		WriteByte (MSG_ENTITY, self.bm_rp2_kind);
		WriteCoord (MSG_ENTITY, self.bm_rp2_pos_x);
		WriteCoord (MSG_ENTITY, self.bm_rp2_pos_y);
		WriteCoord (MSG_ENTITY, self.bm_rp2_pos_z);

		WriteByte (MSG_ENTITY, self.bm_rp3_seq);
		WriteByte (MSG_ENTITY, self.bm_rp3_kind);
		WriteCoord (MSG_ENTITY, self.bm_rp3_pos_x);
		WriteCoord (MSG_ENTITY, self.bm_rp3_pos_y);
		WriteCoord (MSG_ENTITY, self.bm_rp3_pos_z);
	}

	if (sendflags & 2)
	{
		WriteByte (MSG_ENTITY, self.bm_rh_seq);
		WriteByte (MSG_ENTITY, self.bm_rh_cnt);
		if (self.bm_rh_cnt >= 1)
		{
			WriteCoord (MSG_ENTITY, self.bm_rh0_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_rh0_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_rh0_pos_z);
			WriteByte (MSG_ENTITY, self.bm_rh0_int);
		}
		if (self.bm_rh_cnt >= 2)
		{
			WriteCoord (MSG_ENTITY, self.bm_rh1_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_rh1_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_rh1_pos_z);
			WriteByte (MSG_ENTITY, self.bm_rh1_int);
		}
		if (self.bm_rh_cnt >= 3)
		{
			WriteCoord (MSG_ENTITY, self.bm_rh2_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_rh2_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_rh2_pos_z);
			WriteByte (MSG_ENTITY, self.bm_rh2_int);
		}
		if (self.bm_rh_cnt >= 4)
		{
			WriteCoord (MSG_ENTITY, self.bm_rh3_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_rh3_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_rh3_pos_z);
			WriteByte (MSG_ENTITY, self.bm_rh3_int);
		}
	}

	if (sendflags & 4)
	{
		WriteByte (MSG_ENTITY, self.bm_ra_cnt);
		if (self.bm_ra_cnt >= 1)
		{
			WriteCoord (MSG_ENTITY, self.bm_ra0_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_ra0_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_ra0_pos_z);
			WriteByte (MSG_ENTITY, self.bm_ra0_yaw);
		}
		if (self.bm_ra_cnt >= 2)
		{
			WriteCoord (MSG_ENTITY, self.bm_ra1_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_ra1_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_ra1_pos_z);
			WriteByte (MSG_ENTITY, self.bm_ra1_yaw);
		}
		if (self.bm_ra_cnt >= 3)
		{
			WriteCoord (MSG_ENTITY, self.bm_ra2_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_ra2_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_ra2_pos_z);
			WriteByte (MSG_ENTITY, self.bm_ra2_yaw);
		}
		if (self.bm_ra_cnt >= 4)
		{
			WriteCoord (MSG_ENTITY, self.bm_ra3_pos_x);
			WriteCoord (MSG_ENTITY, self.bm_ra3_pos_y);
			WriteCoord (MSG_ENTITY, self.bm_ra3_pos_z);
			WriteByte (MSG_ENTITY, self.bm_ra3_yaw);
		}
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

// Public hook: emit a frozen static radar ping at `org` for all non-allied human players.
void(entity actor, vector org, float kind) BM_Radar_Ping =
{
	local entity p, feed;
	local float cd;

	if (bm_menubg_active || intermission_running)
		return;
	if (actor && actor != world)
	{
		if (kind == BM_RPK_BLAST)
			cd = 0.16;
		else if (kind == BM_RPK_KILL)
			cd = 0;
		else
			cd = 0.35;
		if (cd > 0 && time < actor.bm_radar_cd)
			return;
		if (cd > 0)
			actor.bm_radar_cd = time + cd;
	}

	p = bm_player_head;
	while (p)
	{
		if (p.ishuman == 1 && !p.bm_obs && p != actor && !BM_Radar_IsAlly (p, actor))
		{
			feed = BM_Radar_EnsureFeed (p);
			if (feed)
				BM_Radar_PushPing (feed, kind, org);
		}
		p = p.bm_player_next;
	}
};

void(entity feed, float idx, vector pos, float intensity) BM_Radar_SetHeatSlot =
{
	if (idx == 0)
	{
		feed.bm_rh0_pos = pos;
		feed.bm_rh0_int = intensity;
	}
	else if (idx == 1)
	{
		feed.bm_rh1_pos = pos;
		feed.bm_rh1_int = intensity;
	}
	else if (idx == 2)
	{
		feed.bm_rh2_pos = pos;
		feed.bm_rh2_int = intensity;
	}
	else if (idx == 3)
	{
		feed.bm_rh3_pos = pos;
		feed.bm_rh3_int = intensity;
	}
};

float(vector a, vector b) BM_Radar_Dist2D =
{
	local vector d;

	d_x = a_x - b_x;
	d_y = a_y - b_y;
	d_z = 0;
	return vlen (d);
};

void(entity c) BM_Radar_BuildClientHeat =
{
	local entity feed, e;
	local vector q, z0, z1, z2, z3;
	local float n0, n1, n2, n3, cnt, rseq;
	local float d0, d1, d2, d3, dq, pass;

	feed = BM_Radar_EnsureFeed (c);
	if (!feed)
		return;

	n0 = 0; n1 = 0; n2 = 0; n3 = 0;
	z0 = '0 0 0'; z1 = '0 0 0'; z2 = '0 0 0'; z3 = '0 0 0';
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
					|| (e.flags & FL_NOTARGET) || (e.items & IT_INVISIBILITY)
					|| BM_Radar_IsAlly (c, e))
				{
					e = e.bm_player_next;
					continue;
				}
			}
			else
			{
				if (!(e.flags & FL_MONSTER) || e.health <= 0 || !e.takedamage || (e.flags & FL_NOTARGET)
					|| (e.enemy == world && vlen (e.origin - c.origin) > 1800))
				{
					e = nextent (e);
					continue;
				}
			}

			// Quantize to a coarse 256u cell + jitter so corners/positions stay non-wallhack
			q_x = floor (e.origin_x / 256) * 256 + 128 + crandom () * 88;
			q_y = floor (e.origin_y / 256) * 256 + 128 + crandom () * 88;
			q_z = e.origin_z;

			if (n0 > 0 && BM_Radar_Dist2D (q, z0) < 440)
			{
				z0 = (z0 * n0 + q) / (n0 + 1);
				n0 = n0 + 1;
			}
			else if (n1 > 0 && BM_Radar_Dist2D (q, z1) < 440)
			{
				z1 = (z1 * n1 + q) / (n1 + 1);
				n1 = n1 + 1;
			}
			else if (n2 > 0 && BM_Radar_Dist2D (q, z2) < 440)
			{
				z2 = (z2 * n2 + q) / (n2 + 1);
				n2 = n2 + 1;
			}
			else if (n3 > 0 && BM_Radar_Dist2D (q, z3) < 440)
			{
				z3 = (z3 * n3 + q) / (n3 + 1);
				n3 = n3 + 1;
			}
			else if (cnt < 4)
			{
				if (cnt == 0) { z0 = q; n0 = 1; }
				else if (cnt == 1) { z1 = q; n1 = 1; }
				else if (cnt == 2) { z2 = q; n2 = 1; }
				else { z3 = q; n3 = 1; }
				cnt = cnt + 1;
			}
			else
			{
				// Replace whichever existing zone is farthest from the viewer
				d0 = vlen (z0 - c.origin);
				d1 = vlen (z1 - c.origin);
				d2 = vlen (z2 - c.origin);
				d3 = vlen (z3 - c.origin);
				dq = vlen (q - c.origin);
				if (dq < d0 && d0 >= d1 && d0 >= d2 && d0 >= d3) { z0 = q; n0 = 1; }
				else if (dq < d1 && d1 >= d0 && d1 >= d2 && d1 >= d3) { z1 = q; n1 = 1; }
				else if (dq < d2 && d2 >= d0 && d2 >= d1 && d2 >= d3) { z2 = q; n2 = 1; }
				else if (dq < d3) { z3 = q; n3 = 1; }
			}

			if (pass == 0)
				e = e.bm_player_next;
			else
				e = nextent (e);
		}
		pass = pass + 1;
	}

	rseq = feed.bm_rh_seq + 1;
	if (rseq > 255)
		rseq = 1;
	feed.bm_rh_seq = rseq;
	feed.bm_rh_cnt = cnt;
	if (cnt >= 1) BM_Radar_SetHeatSlot (feed, 0, z0, bound (1, n0 * 48, 255));
	if (cnt >= 2) BM_Radar_SetHeatSlot (feed, 1, z1, bound (1, n1 * 48, 255));
	if (cnt >= 3) BM_Radar_SetHeatSlot (feed, 2, z2, bound (1, n2 * 48, 255));
	if (cnt >= 4) BM_Radar_SetHeatSlot (feed, 3, z3, bound (1, n3 * 48, 255));
	feed.SendFlags = feed.SendFlags | 2;
};

void(entity c) BM_Radar_UpdateClientAllies =
{
	local entity feed, p;
	local float cnt, chg, y;

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
			y = BM_Radar_PackYaw (p.angles_y);
			if (cnt == 0)
			{
				if (vlen (p.origin - feed.bm_ra0_pos) > 14 || fabs (y - feed.bm_ra0_yaw) > 4) chg = TRUE;
				feed.bm_ra0_pos = p.origin; feed.bm_ra0_yaw = y;
			}
			else if (cnt == 1)
			{
				if (vlen (p.origin - feed.bm_ra1_pos) > 14 || fabs (y - feed.bm_ra1_yaw) > 4) chg = TRUE;
				feed.bm_ra1_pos = p.origin; feed.bm_ra1_yaw = y;
			}
			else if (cnt == 2)
			{
				if (vlen (p.origin - feed.bm_ra2_pos) > 14 || fabs (y - feed.bm_ra2_yaw) > 4) chg = TRUE;
				feed.bm_ra2_pos = p.origin; feed.bm_ra2_yaw = y;
			}
			else
			{
				if (vlen (p.origin - feed.bm_ra3_pos) > 14 || fabs (y - feed.bm_ra3_yaw) > 4) chg = TRUE;
				feed.bm_ra3_pos = p.origin; feed.bm_ra3_yaw = y;
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

void() BM_Radar_Tick =
{
	local entity p;
	local float do_heat, do_allies;

	if (bm_menubg_active || intermission_running)
		return;

	do_heat = (time >= bm_radar_heat_t);
	if (do_heat)
		bm_radar_heat_t = time + 5.0;

	do_allies = ((teamplay || coop || CTF_ENABLED) && time >= bm_radar_ally_t);
	if (do_allies)
		bm_radar_ally_t = time + 0.2;

	p = bm_player_head;
	while (p)
	{
		// Detect custom firearm / fun-gun shots via bm_lastshot or fg_fire_t bumps
		if (p.health > 0 && !p.bm_obs)
		{
			if (p.bm_lastshot > p.bm_radar_prev_shot || p.fg_fire_t > p.bm_radar_prev_fg)
			{
				p.bm_radar_prev_shot = p.bm_lastshot;
				p.bm_radar_prev_fg = p.fg_fire_t;
				BM_Radar_Ping (p, p.origin, BM_RPK_GUN);
			}
		}

		if (p.ishuman == 1 && !p.bm_obs)
		{
			BM_Radar_EnsureFeed (p);
			if (do_heat)
				BM_Radar_BuildClientHeat (p);
			if (do_allies)
				BM_Radar_UpdateClientAllies (p);
		}
		p = p.bm_player_next;
	}
};
