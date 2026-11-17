//Decompiled code. Please respect the original copyright.

void() bot_jump =
{
	self.button2 = TRUE;
};

float(entity e) bot_can_rj =
{
	if ((e.b_skill == 0))
	{
		return (0);
	}
	if ((e.items & 4194304))
	{
		return (0);
	}
	if (!((e.items & 32) && (e.ammo_rockets > 0)))
	{
		return (0);
	}
	if ((e.items & 1048576))
	{
		return (TRUE);
	}
	if ((e.health > 50))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float(float flag) frik_recognize_plat =
{
	if (((self.classname != "waypoint") && !(self.flags & FL_ONGROUND)))
	{
		return (0);
	}
	traceline(self.origin, (self.origin - '0 0 64'), TRUE, self);
	if ((trace_ent != world))
	{
		if (flag)
		{
			if ((self.keys & KEY_MOVEUP))
			{
				if ((trace_ent.velocity_z > 0))
				{
					self.keys = (self.keys & 960);
				}
			}
			else
			{
				if ((self.keys & KEY_MOVEDOWN))
				{
					if ((trace_ent.velocity_z < 0))
					{
						self.keys = (self.keys & 960);
					}
				}
			}
		}
		return (TRUE);
	}
	else
	{
		return (0);
	}
};

float(vector sdir) frik_KeysForDir =
{
	local vector keydir;
	local float outkeys;
	local float tang;

	outkeys = 0;
	if ((sdir_x || sdir_y))
	{
		keydir = vectoangles(sdir);
		tang = angcomp(keydir_y, self.v_angle_y);
		if (((tang <= 150) && (tang >= 30)))
		{
			outkeys = outkeys + KEY_MOVELEFT;
		}
		else
		{
			if (((tang >= -150) && (tang <= -30)))
			{
				outkeys = outkeys + KEY_MOVERIGHT;
			}
		}
		if ((fabs(tang) <= 60))
		{
			outkeys = outkeys + KEY_MOVEFORWARD;
		}
		else
		{
			if ((fabs(tang) >= 120))
			{
				outkeys = outkeys + KEY_MOVEBACK;
			}
		}
	}
	if ((sdir_z > 0))
	{
		outkeys = outkeys + KEY_MOVEUP;
	}
	else
	{
		if ((sdir_z < 0))
		{
			outkeys = outkeys + KEY_MOVEDOWN;
		}
	}
	return (outkeys);
};

void(vector whichway, float danger) frik_obstructed =
{
	local float dist;
	local vector disway;
	local vector org;

	if ((self.b_aiflags & AI_BLIND))
	{
		return;
	}
	org = realorigin(self.target1);
	if (danger)
	{
		self.b_aiflags = (self.b_aiflags | AI_DANGER);
		self.keys = frik_KeysForDir((VEC_ORIGIN - whichway));
	}
	if ((self.b_aiflags & AI_PRECISION))
	{
		return;
	}
	if (self.target1)
	{
		if ((self.b_aiflags & AI_OBSTRUCTED))
		{
			if (!(self.b_aiflags & AI_DANGER))
			{
				self.b_aiflags = (self.b_aiflags - AI_OBSTRUCTED);
				return;
			}
			else
			{
				if (!danger)
				{
					return;
				}
			}
		}
		self.obs_dir = whichway;
		disway_x = whichway_y * -1;
		disway_y = whichway_x;
		dist = vlen((org - (self.origin + disway)));
		disway_x = whichway_y;
		disway_y = whichway_x * -1;
		self.wallhug = (vlen((org - (self.origin + disway))) > dist);
		self.b_aiflags = (self.b_aiflags | AI_OBSTRUCTED);
	}
	else
	{
		disway_x = whichway_y * -1;
		disway_y = whichway_x;
		dist = vlen((disway - self.obs_dir));
		disway_x = whichway_y;
		disway_y = whichway_x * -1;
		self.wallhug = (vlen((disway - self.obs_dir)) < dist);
		self.obs_dir = whichway;
		self.b_aiflags = (self.b_aiflags | AI_OBSTRUCTED);
	}
};

void() frik_obstacles =
{
	local vector start;
	local vector stop;
	local vector ang;
	local float test;
	local float conts;
	local float dist;
	local float hgt;

	if (!(self.flags & FL_ONGROUND))
	{
		return;
	}
	if ((self.b_aiflags & AI_BLIND))
	{
		return;
	}
	ang = normalize(self.velocity);
	ang_z = 0;
	start = self.origin + (ang * 32);
	start_z = self.origin_z + self.maxs_z;
	stop = start;
	stop_z = self.origin_z + self.mins_z;
	traceline(start, (stop - '0 0 256'), TRUE, self);
	if ((trace_allsolid || trace_startsolid))
	{
		return;
	}
	hgt = trace_endpos_z - stop_z;
	if ((hgt > 18))
	{
		bot_jump();
		return;
	}
	if ((hgt >= 0))
	{
		return;
	}
	conts = pointcontents((trace_endpos + '0 0 4'));
	if (((trace_fraction == 1) && !autocvar_bm_falldamage))
	{
		traceline(start, (stop - '0 0 2400'), TRUE, self);
		conts = pointcontents((trace_endpos + '0 0 4'));
		if ((conts > -4))
		{
			if (self.enemy)
			{
				if (((self.enemy.origin_z + 48) < self.origin_z))
				{
					bot_jump();
					return;
				}
			}
			if (self.target1)
			{
				stop = realorigin(self.target1);
				if ((((self.origin_z + self.mins_z) - stop_z) > 32))
				{
					bot_jump();
					return;
				}
			}
		}
	}
	start = stop - '0 0 8';
	stop = start + (ang * 256);
	traceline(start, stop, TRUE, self);
	test = vlen((trace_endpos - start));
	if ((test <= 20))
	{
		return;
	}
	ang_x = self.velocity_y * -1;
	ang_y = self.velocity_x;
	ang = normalize(ang);
	traceline((start - (ang * 10)), (start + (ang * 10)), TRUE, self);
	if (((trace_fraction != 1) || trace_startsolid))
	{
		return;
	}
	ang = self.velocity;
	ang_z = 0;
	dist = (540 / sv_gravity) * vlen(ang);
	if ((test > dist))
	{
		if ((conts < -3))
		{
			frik_obstructed(ang, TRUE);
			return;
		}
		else
		{
			if (!autocvar_bm_falldamage)
			{
				if (self.enemy)
				{
					if (((self.enemy.origin_z + 48) < self.origin_z))
					{
						bot_jump();
						return;
					}
				}
			}
			if (self.target1)
			{
				stop = realorigin(self.target1);
				if ((((self.origin_z + self.mins_z) - stop_z) > 32))
				{
					if (!autocvar_bm_falldamage)
					{
						bot_jump();
					}
					return;
				}
			}
			frik_obstructed(ang, FALSE);
			return;
		}
	}
	else
	{
		ang = normalize(ang);
		traceline(self.origin, (self.origin + (ang * (test + 20))), TRUE, self);
		if ((trace_fraction != 1))
		{
			if ((conts < -3))
			{
				frik_obstructed(ang, TRUE);
				return;
			}
			else
			{
				if (self.target1)
				{
					stop = realorigin(self.target1);
					if ((((self.origin_z + self.mins_z) - stop_z) > 32))
					{
						return;
					}
				}
				frik_obstructed(ang, FALSE);
				return;
			}
		}
		if (self.target1)
		{
			test = vlen((self.target1.origin - (ang + self.origin)));
			if ((test > vlen((self.target1.origin - self.origin))))
			{
				if ((conts < -3))
				{
					frik_obstructed(ang, TRUE);
					return;
				}
				else
				{
					frik_obstructed(ang, FALSE);
					return;
				}
			}
		}
	}
	if ((hgt < -18))
	{
		if ((conts < -3))
		{
			frik_obstructed(ang, TRUE);
			return;
		}
		if (self.target1)
		{
			stop = realorigin(self.target1);
			if ((((self.origin_z + self.mins_z) - stop_z) > 32))
			{
				return;
			}
		}
		bot_jump();
	}
};

void() frik_dodge_obstruction =
{
	local vector way;
	local vector org;
	local float oflags;
	local float yaw;

	if (!(self.b_aiflags & AI_OBSTRUCTED))
	{
		return;
	}
	if (((self.b_aiflags & 160) || !(self.flags & FL_ONGROUND)))
	{
		self.b_aiflags = (self.b_aiflags - AI_OBSTRUCTED);
		return;
	}
	oflags = self.flags;
	org = self.origin;
	yaw = vectoyaw(self.obs_dir);
	if (walkmove(yaw, 32))
	{
		self.b_aiflags = (self.b_aiflags - AI_OBSTRUCTED);
	}
	else
	{
		if ((self.b_aiflags & AI_DANGER))
		{
			way = VEC_ORIGIN - self.obs_dir;
		}
		else
		{
			if (self.wallhug)
			{
				way_x = self.obs_dir_y * -1;
				way_y = self.obs_dir_x;
			}
			else
			{
				way_x = self.obs_dir_y;
				way_y = self.obs_dir_x * -1;
			}
		}
		self.keys = ((self.keys & 960) + frik_KeysForDir(way));
	}
	self.origin = org;
	self.flags = oflags;
};

void() frik_movetogoal =
{
	local vector way;
	local float g;

	if ((self.target1 == world))
	{
		makevectors(self.v_angle);
		frik_walkmove(v_forward);
		return;
	}
	way = realorigin(self.target1) - self.origin;
	if ((vlen(way) < 25))
	{
		self.keys = (self.keys & 960);
		return;
	}
	way = normalize(way);
	self.keys = ((self.keys & 960) + frik_KeysForDir(way));
	frik_dodge_obstruction();
	frik_recognize_plat(TRUE);
	if ((self.b_aiflags & AI_PRECISION))
	{
		g = angcomp(self.v_angle_x, self.b_angle_x);
		if ((fabs(g) > 10))
		{
			self.keys = (self.keys & 960);
		}
		g = angcomp(self.v_angle_y, self.b_angle_y);
		if ((fabs(g) > 10))
		{
			self.keys = (self.keys & 960);
		}
	}
};

float(vector weird) frik_walkmove =
{

	self.keys = ((self.keys & 960) + frik_KeysForDir(weird));
	frik_dodge_obstruction();
	frik_recognize_plat(TRUE);
	if ((self.b_aiflags & AI_OBSTRUCTED))
	{
		return (0);
	}
	else
	{
		return (TRUE);
	}
};

void() frik_bot_roam =
{
	local vector org;
	local vector ang;
	local vector org1;
	local float loopcount;
	local float flag;
	local float dist;

	loopcount = 26;
	flag = 0;
	while (((loopcount > 0) && !flag))
	{
		loopcount = loopcount - 1;
		org = self.origin + self.view_ofs;
		ang = self.angles;
		ang_y = frik_anglemod(((ang_y - 90) + (random() * 180)));
		ang_x = 0;
		makevectors(ang);
		traceline(org, (org + (v_forward * 2300)), TRUE, self);
		if ((trace_fraction != 1))
		{
			org1 = trace_endpos;
			ang = normalize(trace_plane_normal);
			traceline(org1, (org1 + (ang * 2300)), TRUE, self);
			if (((trace_fraction != 1) && (vlen((trace_endpos - org1)) >= 64)))
			{
				org = trace_endpos;
				traceline(org, (self.origin + self.view_ofs), TRUE, self);
				if ((trace_fraction != 1))
				{
					dist = vlen((org1 - org)) / 2;
					org = org1 + (ang * dist);
					traceline(org, (org - '0 0 48'), TRUE, self);
					if ((trace_fraction != 1))
					{
						SpawnTempWaypoint(org);
						flag = TRUE;
					}
				}
			}
		}
	}
	self.b_angle_y = (self.v_angle_y + 10);
	frik_walkmove(v_forward);
};
