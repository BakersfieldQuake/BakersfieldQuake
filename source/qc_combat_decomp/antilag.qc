#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
HITSCAN LAG COMPENSATION / ANTILAG (antilag.qc)

Uses DP/Zircon's DP_SV_PING (.float ping in ms) to rewind living player & bot
hitboxes during human hitscan traces. VM_SV_setorigin -> SV_LinkEdict only
updates absmin/absmax and area-grid links (never fires SV_TouchLinks), so
rewind/restore has zero trigger or item side effects.
================
*/

void() Antilag_Reset =
{
	local float i;

	al_head = 0;
	al_count = 0;
	al_active = 0;
	for (i = 0; i < AL_HIST; i = i + 1)
		al_time[i] = 0;
	for (i = 0; i < AL_MAXCLIENTS * AL_HIST; i = i + 1)
		al_valid[i] = 0;
};

void() Antilag_RecordFrame =
{
	local entity p;
	local float s, idx;

	if (al_active)
		return;

	al_head = al_head + 1;
	if (al_head >= AL_HIST)
		al_head = 0;
	al_time[al_head] = time;

	for (s = 0; s < AL_MAXCLIENTS; s = s + 1)
		al_valid[s * AL_HIST + al_head] = 0;

	p = bm_player_head;
	while (p)
	{
		if (!bm_wasfreed (p) && p.health > 0 && p.deadflag == 0 && !p.bm_obs && p.solid == SOLID_SLIDEBOX && !(p.flags & FL_NOTARGET))
		{
			s = num_for_edict (p);
			s = s - 1;
			if (s >= 0 && s < AL_MAXCLIENTS)
			{
				idx = s * AL_HIST + al_head;
				al_pos[idx] = p.origin;
				al_valid[idx] = 1;
			}
		}
		p = p.bm_player_next;
	}

	if (al_count < AL_HIST)
		al_count = al_count + 1;
};

void(entity attacker) Antilag_Rewind =
{
	local entity p;
	local float back, target_t, max_back, steps, i0, i1, prev, dt, frac, s, idx0, idx1, v0, v1;
	local vector p0, p1, org;

	if (!autocvar_sv_antilag || al_active)
		return;
	if (!attacker || attacker == world || attacker.ishuman != 1)
		return;
	if (attacker.ping <= 0 || al_count < 2)
		return;

	max_back = autocvar_sv_antilag_maxping * 0.001;
	if (max_back <= 0)
		return;
	back = bound (0, attacker.ping * 0.001, max_back);
	if (back < 0.005)
		return;

	target_t = time - back;

	// Find bracketing ring indices (i0 <= target_t <= i1)
	i1 = al_head;
	i0 = i1;
	steps = 1;
	while (steps < al_count)
	{
		prev = i1 - 1;
		if (prev < 0)
			prev = AL_HIST - 1;
		if (al_time[prev] <= target_t)
		{
			i0 = prev;
			break;
		}
		i1 = prev;
		i0 = prev;
		steps = steps + 1;
	}

	dt = al_time[i1] - al_time[i0];
	if (dt > 0.0001)
		frac = bound (0, (target_t - al_time[i0]) / dt, 1);
	else
		frac = 1;

	p = bm_player_head;
	while (p)
	{
		if (p != attacker && !bm_wasfreed (p) && p.health > 0 && p.deadflag == 0 && !p.bm_obs && p.solid == SOLID_SLIDEBOX)
		{
			s = num_for_edict (p);
			s = s - 1;
			if (s >= 0 && s < AL_MAXCLIENTS)
			{
				idx0 = s * AL_HIST + i0;
				idx1 = s * AL_HIST + i1;
				v0 = al_valid[idx0];
				v1 = al_valid[idx1];
				if (v0 && v1)
				{
					p0 = al_pos[idx0];
					p1 = al_pos[idx1];
					if (vlen (p1 - p0) > 256)
						org = p1;		// teleport or respawn discontinuity: snap instead of lerping across map
					else
						org = p0 + (p1 - p0) * frac;
					if (vlen (org - p.origin) <= 512)
					{
						p.al_save_org = p.origin;
						p.al_rewound = 1;
						setorigin (p, org);
					}
				}
				else if (v1)
				{
					org = al_pos[idx1];
					if (vlen (org - p.origin) <= 512)
					{
						p.al_save_org = p.origin;
						p.al_rewound = 1;
						setorigin (p, org);
					}
				}
			}
		}
		p = p.bm_player_next;
	}

	al_active = 1;
};

void() Antilag_Restore =
{
	local entity p;

	if (!al_active)
		return;
	al_active = 0;

	p = bm_player_head;
	while (p)
	{
		if (!bm_wasfreed (p) && p.al_rewound)
		{
			p.al_rewound = 0;
			setorigin (p, p.al_save_org);
		}
		p = p.bm_player_next;
	}
};
