//Decompiled code. Please respect the original copyright.

float(entity head, vector spot) PM_TraceCheck =
{
	local vector p1;
	local vector p2;

	p1 = spot + self.mins;
	p2 = spot + self.maxs;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1_x = spot_x + self.maxs_x;
	p2_x = spot_x + self.mins_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1_x = spot_x + self.mins_x;
	p2_x = spot_x + self.maxs_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + self.maxs;
	p1 = p2;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2_x = spot_x + self.mins_x;
	p1_x = p2_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2_x = spot_x + self.maxs_x;
	p1_x = p2_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + self.mins;
	p1 = p2;
	p2_x = spot_x + self.maxs_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_x = spot_x + self.mins_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p2 = spot + self.maxs;
	p1 = p2;
	p2_x = spot_x + self.mins_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	p2_x = spot_x + self.maxs_x;
	traceline(p1, p2, FALSE, head);
	if ((trace_fraction < 1))
	{
		return (0);
	}
	p1 = p2;
	traceline(p1, p2, FALSE, head);
	return ((trace_fraction == 1));
};

float(entity head, vector spot) PM_InWall =
{
	local vector p;

	p = spot;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p = spot;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p = spot;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.maxs_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	if ((pointcontents(p) == CONTENT_SKY))
	{
		return (TRUE);
	}
	p_x = spot_x + head.mins_x;
	if ((pointcontents(p) == CONTENT_SOLID))
	{
		return (TRUE);
	}
	return ((pointcontents(p) == CONTENT_SKY));
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
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p = spot;
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	if ((pointcontents(p) != CONTENT_EMPTY))
	{
		return (0);
	}
	p_x = spot_x + head.maxs_x;
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
