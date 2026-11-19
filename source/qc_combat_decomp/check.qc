//Decompiled code. Please respect the original copyright.

float(entity head, vector spot) PM_TraceCheck =
{
	local vector p1;
	local vector p2;
	local vector mn;
	local vector mx;

	if ((head != world))
	{
		mn = head.mins;
		mx = head.maxs;
	}
	else
	{
		mn = self.mins;
		mx = self.maxs;
	}
	p1 = spot + mn;
	p2 = spot + mx;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1_x = spot_x + mx_x;
	p2_x = spot_x + mn_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1_y = spot_y + mx_y;
	p2_y = spot_y + mn_y;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1_x = spot_x + mn_x;
	p2_x = spot_x + mx_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + mx;
	p1 = p2;
	p1_z = spot_z + mn_z;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2_x = spot_x + mn_x;
	p1_x = p2_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2_y = spot_y + mn_y;
	p1_y = p2_y;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2_x = spot_x + mx_x;
	p1_x = p2_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + mn;
	p1 = p2;
	p2_x = spot_x + mx_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_y = spot_y + mx_y;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_x = spot_x + mn_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_y = spot_y + mn_y;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + mx;
	p1 = p2;
	p2_x = spot_x + mn_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_y = spot_y + mn_y;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_x = spot_x + mx_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_y = spot_y + mx_y;
	traceline(p1, p2, FALSE, head);
	return ((trace_fraction == 1));
};

float(entity head, vector spot) PM_InWall =
{
	local vector p;
	local float pc;

	p = spot;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p = spot;
	p_y = spot_y + head.mins_y;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_y = spot_y + head.maxs_y;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p = spot;
	p_z = spot_z + head.mins_z;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_z = spot_z + head.maxs_z;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_z = spot_z + head.mins_z;
	p_y = spot_y + head.mins_y;
	p_x = spot_x + head.mins_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_y = spot_y + head.maxs_y;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_z = spot_z + head.maxs_z;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_y = spot_y + head.mins_y;
	pc = pointcontents(p);
	if (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	pc = pointcontents(p);
	return (((pc == CONTENT_SOLID) || (pc == CONTENT_SKY)));
};

float(entity head, vector spot) PM_InEmpty =
{
	local vector p;

	p = spot;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p = spot;
	p_y = spot_y + head.mins_y;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_y = spot_y + head.maxs_y;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p = spot;
	p_z = spot_z + head.mins_z;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_z = spot_z + head.maxs_z;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_z = spot_z + head.mins_z;
	p_y = spot_y + head.mins_y;
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_y = spot_y + head.maxs_y;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_z = spot_z + head.maxs_z;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_y = spot_y + head.mins_y;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.mins_x;
	return ((pointcontents(p) == CONTENT_EMPTY));
};

float(entity head) PM_InLiquid =
{
	if ((pointcontents(head.origin) == CONTENT_WATER))
	{
		return (TRUE);
	}
	if ((pointcontents(head.origin) == CONTENT_SLIME))
	{
		return (TRUE);
	}
	if ((pointcontents(head.origin) == CONTENT_LAVA))
	{
		return (TRUE);
	}
	return (0);
};
