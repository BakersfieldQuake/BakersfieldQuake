//Decompiled code. Please respect the original copyright.

float(float key) CL_KeyState =
{
	return (((self.keys & key) > 0));
};

void() CL_KeyMove =
{
	local float anglespeed;
	local vector view;

	if ((self.keys != self.oldkeys))
	{
		self.movevect = VEC_ORIGIN;
		self.movevect_y = (self.movevect_y + (350 * CL_KeyState(KEY_MOVERIGHT)));
		self.movevect_y = (self.movevect_y - (350 * CL_KeyState(KEY_MOVELEFT)));
		self.movevect_x = (self.movevect_x + (200 * CL_KeyState(KEY_MOVEFORWARD)));
		self.movevect_x = (self.movevect_x - (200 * CL_KeyState(KEY_MOVEBACK)));
		self.movevect_z = (self.movevect_z + (200 * CL_KeyState(KEY_MOVEUP)));
		self.movevect_z = (self.movevect_z - (200 * CL_KeyState(KEY_MOVEDOWN)));
		if (!(self.b_aiflags & AI_PRECISION))
		{
			self.movevect = (self.movevect * 2);
		}
	}
	self.oldkeys = self.keys;
	self.movement = self.movevect;
	if ((self.b_skill != 2))
	{
		anglespeed = 1.65 * real_frametime;
		self.v_angle_y = (self.v_angle_y + ((anglespeed * CL_KeyState(KEY_LOOKLEFT)) * 140));
		self.v_angle_y = (self.v_angle_y - ((anglespeed * CL_KeyState(KEY_LOOKRIGHT)) * 140));
		self.v_angle_x = (self.v_angle_x - ((anglespeed * CL_KeyState(KEY_LOOKUP)) * 150));
		self.v_angle_x = (self.v_angle_x + ((anglespeed * CL_KeyState(KEY_LOOKDOWN)) * 150));
	}
	else
	{
		view_x = angcomp(self.b_angle_x, self.v_angle_x);
		view_y = angcomp(self.b_angle_y, self.v_angle_y);
		if ((vlen(view) > 30))
		{
			self.mouse_emu = (self.mouse_emu + (view * 30));
			if ((vlen(self.mouse_emu) > 180))
			{
				self.mouse_emu = (normalize(self.mouse_emu) * 180);
			}
		}
		else
		{
			self.mouse_emu = (view * (1 / real_frametime));
		}
		self.v_angle = (self.v_angle + (self.mouse_emu * real_frametime));
	}
	if ((self.v_angle_x > 80))
	{
		self.v_angle_x = 80;
	}
	else
	{
		if ((self.v_angle_x < -70))
		{
			self.v_angle_x = -70;
		}
	}
	if ((self.v_angle_z > 50))
	{
		self.v_angle_z = 50;
	}
	else
	{
		if ((self.v_angle_z < -50))
		{
			self.v_angle_z = -50;
		}
	}
	self.v_angle_y = frik_anglemod(self.v_angle_y);
};

void() SV_UserFriction =
{
	local vector vel;
	local vector start;
	local vector stop;
	local float sped;
	local float friction;
	local float newspeed;

	vel = self.velocity;
	sped = vlen(vel);
	vel = self.velocity;
	if (!sped)
	{
		return;
	}
	stop_x = self.origin_x + (vel_x / (sped / 16));
	stop_y = self.origin_y + (vel_y / (sped / 16));
	stop_z = self.origin_z + self.mins_z;
	start = stop;
	stop_z = start_z - 34;
	traceline(start, stop, TRUE, self);
	if (((trace_fraction == 1) && cvar("bm_falldamage")))
	{
		friction = sv_friction * 2;
	}
	else
	{
		friction = sv_friction;
	}
	if ((sped < sv_stopspeed))
	{
		newspeed = sped - ((real_frametime * sv_stopspeed) * friction);
	}
	else
	{
		newspeed = sped - ((real_frametime * sped) * friction);
	}
	if ((newspeed < 0))
	{
		newspeed = 0;
	}
	newspeed = newspeed / sped;
	self.velocity_y = (vel_y * newspeed);
	self.velocity_x = (vel_x * newspeed);
};

void() SV_WaterJump =
{
	if (((time > self.teleport_time) || !self.waterlevel))
	{
		self.flags = (self.flags - (self.flags & FL_WATERJUMP));
		self.teleport_time = 0;
	}
	self.velocity_x = self.movedir_x;
	self.velocity_y = self.movedir_y;
};

void() DropPunchAngle =
{
	local float len;

	len = vlen(self.punchangle);
	self.punchangle = normalize(self.punchangle);
	len = len - (10 * real_frametime);
	if ((len < 0))
	{
		len = 0;
	}
	self.punchangle = (self.punchangle * len);
};

void(vector wishvel) SV_AirAccelerate =
{
	local float addspeed;
	local float wishspd;
	local float accelspeed;
	local float currentspeed;

	wishspd = vlen(wishvel);
	wishvel = normalize(wishvel);
	if ((wishspd > 30))
	{
		wishspd = 30;
	}
	currentspeed = self.velocity * wishvel;
	addspeed = wishspd - currentspeed;
	if ((addspeed <= 0))
	{
		return;
	}
	accelspeed = ((10 * sv_accelerate) * wishspd) * real_frametime;
	if ((accelspeed > addspeed))
	{
		accelspeed = addspeed;
	}
	self.velocity = (self.velocity + (accelspeed * wishvel));
};

void(vector wishvel) SV_Accelerate =
{
	local float addspeed;
	local float wishspd;
	local float accelspeed;
	local float currentspeed;

	wishspd = vlen(wishvel);
	wishvel = normalize(wishvel);
	currentspeed = self.velocity * wishvel;
	addspeed = wishspd - currentspeed;
	if ((addspeed <= 0))
	{
		return;
	}
	accelspeed = (sv_accelerate * wishspd) * real_frametime;
	if ((accelspeed > addspeed))
	{
		accelspeed = addspeed;
	}
	self.velocity = (self.velocity + (accelspeed * wishvel));
};

void() SV_WaterMove =
{
	local vector wishvel;
	local float wishspeed;
	local float addspeed;
	local float cspeed;
	local float newspeed;

	makevectors(self.v_angle);
	wishvel = (v_right * self.movevect_y) + (v_forward * self.movevect_x);
	if ((self.movevect == VEC_ORIGIN))
	{
	}
	else
	{
	}
	wishspeed = vlen(wishvel);
	if ((wishspeed > sv_maxspeed))
	{
		wishvel = (sv_maxspeed / wishspeed) * wishvel;
		wishspeed = sv_maxspeed;
	}
	wishspeed = wishspeed * 0.7;
	cspeed = vlen(self.velocity);
	if (cspeed)
	{
		newspeed = cspeed - ((real_frametime * cspeed) * sv_friction);
		if ((newspeed < 0))
		{
			newspeed = 0;
		}
		self.velocity = (self.velocity * (newspeed / cspeed));
	}
	else
	{
		newspeed = 0;
	}
	if (!wishspeed)
	{
		return;
	}
	addspeed = wishspeed - newspeed;
	if ((addspeed <= 0))
	{
		return;
	}
	wishvel = normalize(wishvel);
	cspeed = (sv_accelerate * wishspeed) * real_frametime;
	if ((cspeed > addspeed))
	{
		cspeed = addspeed;
	}
	self.velocity = (self.velocity + (cspeed * wishvel));
};

void() SV_AirMove =
{
	local vector wishvel;
	local vector vangle;

	vangle = self.v_angle;
	vangle_x = 0;
	makevectors(vangle);
	if (((time < self.teleport_time) && (self.movevect_x < 0)))
	{
		self.movevect_x = 0;
	}
	wishvel = (v_right * self.movevect_y) + (v_forward * self.movevect_x);
	if ((self.movetype != MOVETYPE_WALK))
	{
	}
	else
	{
	}
	if ((vlen(wishvel) > sv_maxspeed))
	{
		wishvel = normalize(wishvel) * sv_maxspeed;
	}
	if ((self.movetype == MOVETYPE_NOCLIP))
	{
		self.velocity = wishvel;
	}
	else
	{
		if ((self.flags & FL_ONGROUND))
		{
			SV_UserFriction();
			SV_Accelerate(wishvel);
		}
		else
		{
			SV_AirAccelerate(wishvel);
		}
	}
};

void() SV_ClientThink =
{
	local vector vangle;

	if ((self.movetype == MOVETYPE_NONE))
	{
		return;
	}
	DropPunchAngle();
	if ((self.health <= 0))
	{
		return;
	}
	self.v_angle_z = 0;
	self.angles_z = (self.v_angle_z * 4);
	vangle = self.v_angle + self.punchangle;
	if (!self.fixangle)
	{
		self.angles_x = (vangle_x / -3);
		self.angles_y = vangle_y;
	}
	else
	{
		self.v_angle = self.angles;
		self.fixangle = 0;
	}
	if ((self.flags & FL_WATERJUMP))
	{
		SV_WaterJump();
		return;
	}
	if (((self.waterlevel >= 2) && (self.movetype != MOVETYPE_NOCLIP)))
	{
		SV_WaterMove();
		return;
	}
	SV_AirMove();
};

float() SV_RunThink =
{
	local float thinktime;
	local float bkuptime;

	thinktime = self.nextthink;
	bkuptime = time;
	if (((thinktime <= 0) || (thinktime > (time + real_frametime))))
	{
		return (TRUE);
	}
	if ((thinktime < time))
	{
		thinktime = time;
	}
	self.nextthink = 0;
	time = thinktime;
	other = world;
	makevectors(self.v_angle);
	self.think();
	time = bkuptime;
	return (TRUE);
};

void(float scale) SV_AddGravity =
{
	if ((self.gravity > 0))
	{
		scale = scale * self.gravity;
	}
	self.velocity_z = (self.velocity_z - ((scale * sv_gravity) * real_frametime));
};

float() SV_CheckWater =
{
	local vector point;
	local float cont;

	point_x = self.origin_x;
	point_y = self.origin_y;
	point_z = (self.origin_z + self.mins_z) + 1;
	self.waterlevel = 0;
	self.watertype = CONTENT_EMPTY;
	cont = pointcontents(point);
	if ((cont <= CONTENT_WATER))
	{
		self.watertype = cont;
		self.waterlevel = 1;
		point_z = self.origin_z + ((self.mins_z + self.maxs_z) * 0.5);
		cont = pointcontents(point);
		if ((cont <= CONTENT_WATER))
		{
			self.waterlevel = 2;
			point_z = self.origin_z + self.view_ofs_z;
			cont = pointcontents(point);
			if ((cont <= CONTENT_WATER))
			{
				self.waterlevel = 3;
			}
		}
	}
	return ((self.waterlevel > 1));
};

void() RemoveThud =
{
	local entity oself;

	if ((other == world))
	{
		if ((self.flags & FL_ONGROUND))
		{
			self.flags = (self.flags - FL_ONGROUND);
		}
	}
	else
	{
		if (((other.solid == SOLID_BSP) && (self.flags & FL_ONGROUND)))
		{
			self.flags = (self.flags - FL_ONGROUND);
		}
		if ((other == self.owner))
		{
			return;
		}
		if ((self.owner.solid == SOLID_NOT))
		{
			return;
		}
		oself = other;
		other = self.owner;
		self = oself;
		if ((self.solid == SOLID_BSP))
		{
			if (self.touch)
			{
				self.touch();
			}
		}
	}
};

void() SV_CheckOnGround =
{
	local vector org;
	local vector v;
	local float currentflags;

	org = self.origin;
	currentflags = self.flags;
	self.flags = ((self.flags | FL_ONGROUND) | FL_PARTIALGROUND);
	walkmove(0, 0);
	if (((self.velocity_z > 180) || (time < self.skypad_cool_t) || self.jp_on))
	{
		self.flags = (currentflags - (currentflags & FL_ONGROUND));
		return;
	}
	self.flags = (currentflags | FL_ONGROUND);
	if (((org_x != self.origin_x) || (org_y != self.origin_y)))
	{
		org = self.origin;
	}
	else
	{
		self.origin = org;
	}
	v = org;
	v_z = ((self.mins_z + org_z) - 1);
	traceline(org, v, TRUE, self);
	if (((self.waterlevel == 3) && (self.movetype == MOVETYPE_WALK)))
	{
		self.flags = (self.flags - FL_ONGROUND);
	}
	else
	{
		if (((trace_plane_normal_z <= 0.7) && (trace_fraction != 1)))
		{
			self.flags = (self.flags - FL_ONGROUND);
		}
		else
		{
			tracebox((org + '0 0 1'), self.mins, self.maxs, (org - '0 0 2'), FALSE, self);
			if (((trace_fraction == 1) || (trace_plane_normal_z <= 0.7)))
			{
				self.flags = (self.flags - FL_ONGROUND);
			}
			else
			{
				self.flags = (self.flags | FL_ONGROUND);
			}
		}
	}
	setorigin(self, org);
};

float(vector dir) botCheckForStep =
{
	local vector currentorigin;
	local vector v;
	local float currentflags;
	local float yaw;
	local float stepdistance;
	local float movedistance;

	currentorigin = self.origin;
	currentflags = self.flags;
	self.flags = 1536;
	dir = normalize(dir);
	dir_z = 0;
	yaw = vectoyaw(dir);
	if (walkmove(yaw, 3))
	{
		if (droptofloor(0, 0))
		{
			stepdistance = self.origin_z - currentorigin_z;
			v = self.origin - currentorigin;
			movedistance = vlen(v);
			if ((((stepdistance > 0) && (stepdistance <= 16)) && (movedistance != 0)))
			{
				self.flags = (currentflags | FL_PARTIALGROUND);
				return (1);
			}
		}
	}
	self.flags = currentflags;
	v = currentorigin;
	v_z = self.origin_z;
	if ((vlen((v - self.origin)) <= 4))
	{
		setorigin(self, currentorigin);
	}
	return (0);
};

void(vector dir) BruteForceStep =
{
	local vector currentorigin;
	local float currentflags;
	local float i;
	local float len;

	currentorigin = self.origin;
	currentflags = self.flags;
	len = vlen(dir);
	if ((len > 16))
	{
		dir = normalize(dir) * 16;
	}
	setorigin(self, (currentorigin + dir));
	while (((i < 18) && !walkmove(0, 0)))
	{
		self.origin_z = (currentorigin_z + i);
		i = i + 2;
	}
	self.flags = currentflags;
	if ((i >= 18))
	{
		setorigin(self, currentorigin);
	}
};

void() PostPhysics =
{
	local vector obstr;
	local vector org;
	local float back;
	local float dst;
	local float cflags;

	self = self.owner;
	self.velocity = ((self.velocity - self.phys_obj.dest1) + self.phys_obj.velocity);
	if ((self.phys_obj.dest2 == self.origin))
	{
		setorigin(self, self.phys_obj.origin);
		if ((self.movetype == MOVETYPE_WALK))
		{
			if ((self.phys_obj.dest1_x || self.phys_obj.dest1_y))
			{
				if (((self.flags & FL_ONGROUND) || (self.waterlevel <= 2)))
				{
					obstr = self.phys_obj.movedir - self.origin;
					obstr_z = 0;
					if ((vlen(obstr) > 0.1))
					{
						dst = vlen(obstr);
						back = vectoyaw(obstr);
						cflags = self.flags;
						self.flags = (self.flags | FL_PARTIALGROUND);
						if (walkmove(back, dst))
						{
							self.flags = cflags;
							self.phys_obj.dest1_z = 0;
							self.velocity = ((self.velocity + self.phys_obj.dest1) - self.phys_obj.velocity);
						}
						else
						{
							if ((dst > 1))
							{
								frik_obstructed(obstr, FALSE);
							}
							org = self.origin;
							self.flags = cflags;
							obstr = self.phys_obj.dest1;
							obstr_x = 0;
							if (!botCheckForStep(obstr))
							{
								obstr = self.phys_obj.dest1;
								obstr_y = 0;
								if (!botCheckForStep(obstr))
								{
									if (!botCheckForStep(self.phys_obj.dest1))
									{
										BruteForceStep(self.phys_obj.dest1);
									}
								}
							}
						}
					}
				}
			}
		}
	}
	SV_CheckOnGround();
	PlayerPostThink();
	BotAI();
	self.dmg_save = 0;
	self.dmg_take = 0;
};

void() SV_FlyMove =
{
	if ((self.phys_obj == world))
	{
		self.phys_obj = find(world, classname, "phys_obj");
		while ((self.phys_obj.owner != self))
		{
			self.phys_obj = find(self.phys_obj, classname, "phys_obj");
			if ((self.phys_obj == world))
			{
				error("No physics entity spawned!\nMake sure BotInit was called\n");
			}
		}
	}
	setmodel(self.phys_obj, string_null);
	self.phys_obj.movetype = MOVETYPE_STEP;
	self.phys_obj.solid = SOLID_TRIGGER;
	self.phys_obj.touch = RemoveThud;
	setsize(self.phys_obj, self.mins, self.maxs);
	self.phys_obj.origin = self.origin;
	self.phys_obj.dest2 = self.origin;
	self.phys_obj.watertype = 0;
	self.phys_obj.movedir = (self.origin + (real_frametime * self.velocity));
	self.phys_obj.velocity = self.velocity;
	self.phys_obj.dest1 = self.velocity;
	self.phys_obj.velocity_z = (self.phys_obj.velocity_z + (sv_gravity * real_frametime));
	self.phys_obj.flags = 0;
	self.phys_obj.think = PostPhysics;
	self.phys_obj.nextthink = time;
};

void() SV_Physics_Toss =
{
	if (!SV_RunThink())
	{
		return;
	}
	if ((self.flags & FL_ONGROUND))
	{
		self.velocity = VEC_ORIGIN;
		BotAI();
		return;
	}
	if ((self.movetype != MOVETYPE_FLY))
	{
		SV_AddGravity(1);
	}
	self.angles = (self.angles + (real_frametime * self.avelocity));
	SV_FlyMove();
};

void() SV_Physics_Client =
{
	PlayerPreThink();
	if ((self.movetype == MOVETYPE_NONE))
	{
		if (!SV_RunThink())
		{
			return;
		}
		PlayerPostThink();
		BotAI();
	}
	else
	{
		if (((self.movetype == MOVETYPE_WALK) || (self.movetype == MOVETYPE_STEP)))
		{
			if (!SV_RunThink())
			{
				return;
			}
			if ((!SV_CheckWater() && !(self.flags & FL_WATERJUMP)))
			{
				SV_AddGravity(1);
			}
			SV_FlyMove();
		}
		else
		{
			if (((self.movetype == MOVETYPE_TOSS) || (self.movetype == MOVETYPE_BOUNCE)))
			{
				SV_Physics_Toss();
			}
			else
			{
				if ((self.movetype == MOVETYPE_FLY))
				{
					if (!SV_RunThink())
					{
						return;
					}
					SV_FlyMove();
				}
				else
				{
					if ((self.movetype == MOVETYPE_NOCLIP))
					{
						if (!SV_RunThink())
						{
							return;
						}
						self.origin = (self.origin + (real_frametime * self.velocity));
						PlayerPostThink();
						BotAI();
					}
					else
					{
						error("SV_Physics_Client: Bad Movetype (BOT)");
					}
				}
			}
		}
	}
};
