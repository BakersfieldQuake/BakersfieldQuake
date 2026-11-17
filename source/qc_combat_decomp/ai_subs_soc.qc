//Decompiled code. Please respect the original copyright.

float(entity targ, vector s_offset, vector t_offset, float nomonsters) visxray =
{
	local vector spot1;
	local vector spot2;

	if (self.bsporigin)
	{
		spot1 = bmodel_origin(self) + s_offset;
	}
	else
	{
		spot1 = self.origin + s_offset;
	}
	spot2 = targ.origin + t_offset;
	traceline(spot1, spot2, nomonsters, self);
	if ((liquid_alpha == 1))
	{
		if ((trace_inopen && trace_inwater))
		{
			return (0);
		}
	}
	if (nomonsters)
	{
		if ((trace_fraction == 1))
		{
			return (TRUE);
		}
		return (0);
	}
	else
	{
		if ((trace_ent == targ))
		{
			return (TRUE);
		}
		return (0);
	}
};

float(vector source, vector targ, float offset, float reverse, float dst_ang) viewangle =
{
	local float targ_dir;
	local float targ_ang;

	if (reverse)
	{
		targ_dir = vectoyaw((source - targ));
	}
	else
	{
		targ_dir = vectoyaw((targ - source));
	}
	targ_ang = anglemod(((dst_ang - targ_dir) + offset));
	return (targ_ang);
};

void() ai_resetangles =
{
	self.angles_z = 0;
	self.angles_x = 0;
};
