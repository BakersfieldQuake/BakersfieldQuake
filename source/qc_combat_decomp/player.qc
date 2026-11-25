//Decompiled code. Please respect the original copyright.

void(entity e, float waterwalk) walksound =
{
	local float surfnum;
	local float r;
	local float mat;
	local string s;

	if ((vlen(self.velocity) < 100))
	{
		return;
	}
	makevectors(e.v_angle);
	if ((waterwalk != 0))
	{
		if ((random() < 0.65))
		{
			sound7(e, CHAN_AUTO, "walk/waterwade1.wav", 0.7, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(e, CHAN_AUTO, "walk/waterwade2.wav", 0.7, ATTN_NORM, SNDSPD);
		}
		return;
	}
	mat = 0;
	if (world_has_q1_surfs)
	{
		surfnum = getsurfacenearpoint(world, (e.origin - '0 0 24'));
		if ((surfnum < 0))
		{
			return;
		}
		s = getsurfacetexture(world, surfnum);
		mat = returnsurface(s);
	}
	if (((mat == GROUND) || (mat == ROCK)))
	{
		r = rint((random() * 3));
		if ((r == 0))
		{
			sound7(e, CHAN_AUTO, "walk/pl_dirt1.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 1))
		{
			sound7(e, CHAN_AUTO, "walk/pl_dirt2.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 2))
		{
			sound7(e, CHAN_AUTO, "walk/pl_dirt3.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(e, CHAN_AUTO, "walk/pl_dirt4.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
	}
	else if ((mat == METAL))
	{
		r = rint((random() * 3));
		if ((r == 0))
		{
			sound7(e, CHAN_AUTO, "walk/metal1.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 1))
		{
			sound7(e, CHAN_AUTO, "walk/metal2.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 2))
		{
			sound7(e, CHAN_AUTO, "walk/metal3.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(e, CHAN_AUTO, "walk/metal4.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
	}
	else if ((mat == MEAT))
	{
		r = rint((random() * 3));
		if ((r == 0))
		{
			sound7(e, CHAN_AUTO, "custom/flesh1.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 1))
		{
			sound7(e, CHAN_AUTO, "custom/flesh5.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 2))
		{
			sound7(e, CHAN_AUTO, "custom/flesh3.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(e, CHAN_AUTO, "custom/flesh4.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
	}
	else
	{
		r = rint((random() * 4));
		if ((r == 0))
		{
			sound7(e, CHAN_AUTO, "walk/generic1.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 1))
		{
			sound7(e, CHAN_AUTO, "walk/generic2.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 2))
		{
			sound7(e, CHAN_AUTO, "walk/generic3.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else if ((r == 3))
		{
			sound7(e, CHAN_AUTO, "walk/generic4.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(e, CHAN_AUTO, "walk/generic5.wav", autocvar_playerfootsteps, ATTN_NORM, SNDSPD);
		}
	}
};

void() player_stand1 = [ 17, player_stand1 ]
{
	if ((self.velocity_x || self.velocity_y))
	{
		self.walkframe = 0;
		player_run();
		return;
	}
	if ((self.weapon == IT_CHAINSAW))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe >= 5))
		{
			self.weaponframe = 0;
			if ((self.view_ofs != VEC_ORIGIN))
			{
				sound7(self, CHAN_WEAPON, "weapons/sawridle.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			}
		}
		if ((((self.weaponframe == 0) || (self.weaponframe == 2)) || (self.weaponframe == 4)))
		{
			if ((autocvar_effects_explosion_shake != 0))
			{
				self.punchangle_x = -0.5;
			}
		}
		if ((self.walkframe >= 5))
		{
			self.walkframe = 0;
		}
		if ((self.waterlevel >= 2))
		{
			self.frame = (207 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
		}
		else
		{
			if (!(self.flags & FL_ONGROUND))
			{
				self.frame = (247 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
				if ((self.walkframe >= 5))
				{
					self.walkframe = 4;
				}
			}
			else
			{
				self.frame = (12 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
			}
		}
		return;
	}
	if ((((self.weapon == IT_SUPER_NAILGUN) && (self.spindown == 1)) && (autocvar_nospinup == 0)))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe < 10))
		{
			self.weaponframe = 10;
		}
		self.spintimer = (self.spintimer + 1.2);
		if ((self.weaponframe >= 19))
		{
			self.weaponframe = 1;
		}
		if ((self.spintimer >= 9))
		{
			sound7(self, CHAN_WEAPON, "weapons/spikespn.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			self.weapontimer = 0;
			self.spindown = 0;
		}
		if ((self.walkframe == 5))
		{
			self.walkframe = 0;
		}
		if ((self.waterlevel >= 2))
		{
			self.frame = (207 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
		}
		else
		{
			if (!(self.flags & FL_ONGROUND))
			{
				if ((self.walkframe >= 5))
				{
					self.walkframe = 4;
				}
				self.frame = (247 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
			}
			else
			{
				self.frame = (12 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
			}
		}
		return;
	}
	if (((self.weapon == IT_ROCKET_LAUNCHER) && (self.weaponframe >= 6)))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 8))
		{
			sound7(self, CHAN_AUTO, "weapons/rockload.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.weaponframe >= 9))
		{
			self.weaponframe = 0;
		}
	}
	if (autocvar_mage_weapon)
	{
		if ((self.weapon != IT_LIGHTNING))
		{
			self.weaponframe = 0;
		}
	}
	else
	{
		if ((self.weapon != IT_ROCKET_LAUNCHER))
		{
			self.weaponframe = 0;
		}
	}
	if ((self.waterlevel >= 2))
	{
		player_swim();
		return;
	}
	if ((self.weapon == IT_LIGHTNING))
	{
		self.weapontimer = (self.weapontimer + 1);
		if ((self.weapontimer == 7))
		{
			sound7(self, CHAN_AUTO, "weapons/lg_hum.wav", 0.7, ATTN_NORM, SNDSPD);
			self.weapontimer = 0;
		}
	}
	if ((!(self.flags & FL_ONGROUND) && (self.weapon != IT_AXE)))
	{
		self.frame = (247 + self.walkframe);
		self.walkframe = (self.walkframe + 1);
		if ((self.walkframe >= 6))
		{
			self.walkframe = 5;
		}
		self.weaponframe = 0;
		return;
	}
	if ((self.weapon == IT_AXE))
	{
		if (!(self.flags & FL_ONGROUND))
		{
			self.frame = (243 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
			if ((self.walkframe >= 5))
			{
				self.walkframe = 4;
				self.frame = 246;
			}
			return;
		}
		if ((self.walkframe >= 12))
		{
			self.walkframe = 0;
		}
		self.frame = (17 + self.walkframe);
	}
	else
	{
		if ((self.walkframe >= 5))
		{
			self.walkframe = 0;
		}
		self.frame = (12 + self.walkframe);
	}
	self.walkframe = (self.walkframe + 1);
};

void() player_swim = [ 207, player_swim ]
{
	if (((self.weapon == IT_ROCKET_LAUNCHER) && (self.weaponframe >= 6)))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 8))
		{
			sound7(self, CHAN_AUTO, "weapons/rockload.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.weaponframe >= 9))
		{
			self.weaponframe = 0;
		}
	}
	else
	{
		self.weaponframe = 0;
	}
	if ((self.waterlevel >= 2))
	{
		if (((self.model == "progs/player_id1.mdl") && (self.walkframe >= 6)) || (self.walkframe == 7))
		{
			self.walkframe = 0;
		}
		if ((self.weapon == IT_AXE))
		{
			self.frame = (214 + self.walkframe);
		}
		else
		{
			self.frame = (207 + self.walkframe);
		}
		self.walkframe = (self.walkframe + 1);
	}
	else
	{
		self.walkframe = 0;
		player_stand1();
		return;
	}
};

void() player_run = [ 6, player_run ]
{
	self.meleeing = 0;
	self.viewzoom = 0;
	if ((self.throwing == 1))
	{
		self.weaponframe = 0;
		self.throwing = 0;
		W_SetCurrentAmmo();
	}
	if ((!self.velocity_x && !self.velocity_y))
	{
		self.walkframe = 0;
		player_stand1();
		return;
	}
	if ((self.weapon == IT_CHAINSAW))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe >= 5))
		{
			self.weaponframe = 0;
			if ((self.view_ofs != VEC_ORIGIN))
			{
				sound7(self, CHAN_WEAPON, "weapons/sawridle.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			}
		}
		if ((((self.weaponframe == 0) || (self.weaponframe == 2)) || (self.weaponframe == 4)))
		{
			if ((autocvar_effects_explosion_shake != 0))
			{
				self.punchangle_x = -0.4;
			}
		}
		if ((self.walkframe == 6))
		{
			self.walkframe = 0;
		}
		if ((self.waterlevel >= 2))
		{
			self.frame = (207 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
		}
		else
		{
			if (!(self.flags & FL_ONGROUND))
			{
				self.frame = (247 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
				if ((self.walkframe >= 5))
				{
					self.walkframe = 4;
				}
			}
			else
			{
				self.frame = (6 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
			}
		}
		return;
	}
	if ((((self.weapon == IT_SUPER_NAILGUN) && (self.spindown == 1)) && (autocvar_nospinup == 0)))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe < 10))
		{
			self.weaponframe = 10;
		}
		self.spintimer = (self.spintimer + 1);
		if ((self.weaponframe >= 19))
		{
			self.weaponframe = 1;
		}
		if ((self.spintimer >= 9))
		{
			sound7(self, CHAN_WEAPON, "weapons/spikespn.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
			self.weapontimer = 0;
			self.spindown = 0;
		}
		if ((self.walkframe == 6))
		{
			self.walkframe = 0;
		}
		if ((self.waterlevel >= 2))
		{
			self.frame = (207 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
		}
		else
		{
			if (!(self.flags & FL_ONGROUND))
			{
				self.frame = (247 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
				if ((self.walkframe >= 5))
				{
					self.walkframe = 4;
				}
			}
			else
			{
				self.frame = (6 + self.walkframe);
				self.walkframe = (self.walkframe + 1);
			}
		}
		return;
	}
	if (((self.weapon == IT_ROCKET_LAUNCHER) && (self.weaponframe >= 6)))
	{
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 8))
		{
			sound7(self, CHAN_AUTO, "weapons/rockload.wav", 1, ATTN_NORM, SNDSPD);
		}
		if ((self.weaponframe >= 9))
		{
			self.weaponframe = 0;
		}
	}
	if ((self.waterlevel >= 2))
	{
		player_swim();
		return;
	}
	if (((self.waterlevel == 0) && autocvar_playerfootsteps))
	{
		if ((checkbottom(self) == TRUE))
		{
			if (((self.walkframe == 1) || (self.walkframe == 4)))
			{
				walksound(self, 0);
			}
		}
	}
	else
	{
		if ((((self.waterlevel == 1) || (self.waterlevel == 2)) && autocvar_waterwalk_and_swim_sound))
		{
			if ((self.walkframe == 1))
			{
				if ((autocvar_waterwalk_and_swim_sound >= 2))
				{
					walksound(self, 1);
				}
				else
				{
					if ((checkbottom(self) == TRUE))
					{
						walksound(self, 1);
					}
				}
			}
		}
	}
	if ((self.weapon == IT_LIGHTNING))
	{
		self.weapontimer = (self.weapontimer + 1);
		if ((self.weapontimer == 7))
		{
			sound7(self, CHAN_AUTO, "weapons/lg_hum.wav", 0.7, ATTN_NORM, SNDSPD);
			self.weapontimer = 0;
		}
	}
	if ((!(self.flags & FL_ONGROUND) && (self.weapon != IT_AXE)))
	{
		if ((self.walkframe >= 6))
		{
			self.walkframe = 5;
		}
		self.frame = (247 + self.walkframe);
		self.walkframe = (self.walkframe + 1);
		if (((self.weapon == IT_ROCKET_LAUNCHER) && (self.weaponframe >= 6)))
		{
			self.weaponframe = (self.weaponframe + 1);
			if ((self.weaponframe == 8))
			{
				sound7(self, CHAN_AUTO, "weapons/rockload.wav", 1, ATTN_NORM, SNDSPD);
			}
			if ((self.weaponframe >= 9))
			{
				self.weaponframe = 0;
			}
		}
		else
		{
			self.weaponframe = 0;
		}
		return;
	}
	if (autocvar_mage_weapon)
	{
		if ((self.weapon != IT_LIGHTNING))
		{
			self.weaponframe = 0;
		}
	}
	else
	{
		if ((self.weapon != IT_ROCKET_LAUNCHER))
		{
			self.weaponframe = 0;
		}
	}
	if ((self.weapon == IT_AXE))
	{
		if (!(self.flags & FL_ONGROUND))
		{
			self.frame = (243 + self.walkframe);
			self.walkframe = (self.walkframe + 1);
			if ((self.walkframe >= 5))
			{
				self.walkframe = 4;
				self.frame = 246;
			}
			return;
		}
		if ((self.walkframe == 6))
		{
			self.walkframe = 0;
		}
		self.frame = self.walkframe;
	}
	else
	{
		if ((self.walkframe == 6))
		{
			self.walkframe = 0;
		}
		self.frame = (self.frame + self.walkframe);
	}
	self.walkframe = (self.walkframe + 1);
};

void() player_shot1 = [ 113, player_shot2 ]
{
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
	self.weaponframe = 1;
	self.effects = (self.effects | EF_MUZZLEFLASH);
};

void() player_shot2 = [ 114, player_shot3 ]
{
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
	self.viewzoom = 0;
	self.weaponframe = 2;
};

void() player_shot3 = [ 115, player_shot4 ]
{
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
	self.weaponframe = 3;
};

void() player_shot4 = [ 116, player_shot5 ]
{
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
	self.weaponframe = 4;
};

void() player_shot5 = [ 117, player_shot6 ]
{
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.07);
	}
	self.weaponframe = 5;
};

void() player_shot6 = [ 118, player_run ]
{
	self.weaponframe = 6;
	if ((self.weapon == IT_SHOTGUN))
	{
		casing(0);
		self.nextthink = (time + 0.07);
	}
};

void() player_shotswim1 = [ 221, player_shotswim2 ]
{
	self.weaponframe = 1;
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
};

void() player_shotswim2 = [ 222, player_shotswim3 ]
{
	self.weaponframe = 2;
	self.viewzoom = 0;
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
};

void() player_shotswim3 = [ 223, player_shotswim4 ]
{
	self.weaponframe = 3;
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
};

void() player_shotswim4 = [ 224, player_shotswim5 ]
{
	self.weaponframe = 4;
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.08);
	}
};

void() player_shotswim5 = [ 225, player_shotswim6 ]
{
	self.weaponframe = 5;
	if ((self.weapon == IT_SHOTGUN))
	{
		self.nextthink = (time + 0.07);
	}
};

void() player_shotswim6 = [ 226, player_swim ]
{
	self.weaponframe = 6;
	if ((self.weapon == IT_SHOTGUN))
	{
		casing(0);
		self.nextthink = (time + 0.07);
	}
};

void() player_axe1 = [ 119, player_axe2 ]
{
	self.weaponframe = 1;
};

void() player_axe2 = [ 120, player_axe3 ]
{
	self.weaponframe = 2;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 3;
		self.punchangle_y = -1;
	}
};

void() player_axe3 = [ 121, player_axe4 ]
{
	self.weaponframe = 3;
	W_FireAxe();
};

void() player_axe4 = [ 122, player_run ]
{
	self.weaponframe = 4;
};

void() player_axeb1 = [ 125, player_axeb2 ]
{
	self.weaponframe = 5;
};

void() player_axeb2 = [ 126, player_axeb3 ]
{
	self.weaponframe = 6;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 0.2;
		self.punchangle_y = 3;
	}
};

void() player_axeb3 = [ 127, player_axeb4 ]
{
	self.weaponframe = 7;
	W_FireAxe();
};

void() player_axeb4 = [ 128, player_run ]
{
	self.weaponframe = 8;
};

void() player_axec1 = [ 131, player_axec2 ]
{
	self.weaponframe = 1;
};

void() player_axec2 = [ 132, player_axec3 ]
{
	self.weaponframe = 2;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 3;
		self.punchangle_y = -1;
	}
};

void() player_axec3 = [ 133, player_axec4 ]
{
	self.weaponframe = 3;
	W_FireAxe();
};

void() player_axec4 = [ 134, player_run ]
{
	self.weaponframe = 4;
};

void() player_axed1 = [ 137, player_axed2 ]
{
	self.weaponframe = 5;
};

void() player_axed2 = [ 138, player_axed3 ]
{
	self.weaponframe = 6;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 0.2;
		self.punchangle_y = 5;
	}
};

void() player_axed3 = [ 139, player_axed4 ]
{
	self.weaponframe = 7;
	W_FireAxe();
};

void() player_axed4 = [ 140, player_run ]
{
	self.weaponframe = 8;
};

void() player_axes1 = [ 227, player_axes2 ]
{
	self.weaponframe = 1;
};

void() player_axes2 = [ 229, player_axes3 ]
{
	self.weaponframe = 2;
};

void() player_axes3 = [ 230, player_axes4 ]
{
	self.weaponframe = 3;
	W_FireAxe();
};

void() player_axes4 = [ 232, player_swim ]
{
	self.weaponframe = 4;
};

void() player_chainsaw1 = [ 103, player_chainsaw2 ]
{
	self.weaponframe = 5;
	W_FireSaw();
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1;
	}
};

void() player_chainsaw2 = [ 104, player_chainsaw3 ]
{
	self.weaponframe = 6;
	if (!self.button0)
	{
		player_run();
		return;
		if ((autocvar_effects_explosion_shake != 0))
		{
			self.punchangle_x = -0.5;
		}
	}
};

void() player_chainsaw3 = [ 103, player_chainsaw4 ]
{
	self.weaponframe = 7;
	W_FireSaw();
	self.punchangle_x = -1;
};

void() player_chainsaw4 = [ 104, player_chainsaw5 ]
{
	self.weaponframe = 8;
	if (!self.button0)
	{
		player_run();
		return;
		if ((autocvar_effects_explosion_shake != 0))
		{
			self.punchangle_x = -0.5;
		}
	}
};

void() player_chainsaw5 = [ 103, player_chainsaw6 ]
{
	self.weaponframe = 9;
	W_FireSaw();
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1;
	}
};

void() player_chainsaw6 = [ 104, player_run ]
{
	self.weaponframe = 10;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -0.5;
	}
};

void() player_swimsaw1 = [ 221, player_swimsaw2 ]
{
	self.weaponframe = 5;
	W_FireSaw();
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1;
	}
};

void() player_swimsaw2 = [ 222, player_swimsaw3 ]
{
	self.weaponframe = 6;
	if (!self.button0)
	{
		player_run();
		return;
		if ((autocvar_effects_explosion_shake != 0))
		{
			self.punchangle_x = -0.5;
		}
	}
};

void() player_swimsaw3 = [ 221, player_swimsaw4 ]
{
	self.weaponframe = 7;
	W_FireSaw();
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1;
	}
};

void() player_swimsaw4 = [ 222, player_swimsaw5 ]
{
	self.weaponframe = 8;
	if (!self.button0)
	{
		player_run();
		return;
		if ((autocvar_effects_explosion_shake != 0))
		{
			self.punchangle_x = -0.5;
		}
	}
};

void() player_swimsaw5 = [ 221, player_swimsaw6 ]
{
	self.weaponframe = 9;
	W_FireSaw();
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -1;
	}
};

void() player_swimsaw6 = [ 222, player_run ]
{
	self.weaponframe = 10;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -0.5;
	}
};

void() melee_kick1 = [ 233, melee_kick2 ]
{
	self.weaponframe = 1;
	self.meleeing = 1;
};

void() melee_kick2 = [ 234, melee_kick3 ]
{
	self.weaponframe = 2;
	self.meleeing = 1;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3;
	}
};

void() melee_kick3 = [ 235, melee_kick5 ]
{
	self.weaponframe = 3;
	self.meleeing = 1;
	W_FireAxe();
};

void() melee_kick5 = [ 236, player_run ]
{
	self.weaponframe = 4;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() melee_kick6 = [ 233, melee_kick7 ]
{
	self.weaponframe = 5;
	self.meleeing = 1;
};

void() melee_kick7 = [ 234, melee_kick8 ]
{
	self.weaponframe = 6;
	self.meleeing = 1;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 2;
		self.punchangle_y = -3;
	}
};

void() melee_kick8 = [ 235, melee_kick10 ]
{
	self.weaponframe = 7;
	self.meleeing = 1;
	W_FireAxe();
};

void() melee_kick10 = [ 236, player_run ]
{
	self.weaponframe = 7;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() melee_kickax1 = [ 238, melee_kickax2 ]
{
	self.weaponframe = 1;
	self.meleeing = 1;
};

void() melee_kickax2 = [ 239, melee_kickax3 ]
{
	self.weaponframe = 2;
	self.meleeing = 1;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3;
	}
};

void() melee_kickax3 = [ 240, melee_kickax5 ]
{
	self.weaponframe = 3;
	self.meleeing = 1;
	W_FireAxe();
};

void() melee_kickax5 = [ 241, player_run ]
{
	self.weaponframe = 4;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() melee_kickax6 = [ 238, melee_kickax7 ]
{
	self.weaponframe = 5;
	self.meleeing = 1;
};

void() melee_kickax7 = [ 239, melee_kickax8 ]
{
	self.weaponframe = 6;
	self.meleeing = 1;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = 2;
		self.punchangle_y = -3;
	}
};

void() melee_kickax8 = [ 240, melee_kickax10 ]
{
	self.weaponframe = 7;
	self.meleeing = 1;
	W_FireAxe();
};

void() melee_kickax10 = [ 241, player_run ]
{
	self.weaponframe = 7;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() player_nail1 = [ 103, player_nail2 ]
{
	if (((self.weapon == IT_SUPER_NAILGUN) && (self.ammo_nails < 2)))
	{
		BM_OutOfAmmo();
		return;
	}
	if ((((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)) && (self.weapon != IT_NAILGUN)))
	{
		nailcasing(0);
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	if ((self.weapon == IT_SUPER_NAILGUN))
	{
		if ((self.weaponframe >= 10))
		{
			self.weaponframe = 1;
		}
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 9))
		{
			self.weaponframe = 1;
		}
	}
	SuperDamageSound();
	if (cvar("chase_active"))
	{
		W_FireSpikes(2);
	}
	else
	{
		if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
		{
			W_FireSpikes(10);
		}
		else
		{
			if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
			{
				W_FireSpikes(autocvar_weapon_position_adjustable_projectile_nail1a_offset);
			}
			else
			{
				W_FireSpikes(3);
			}
		}
	}
	self.attack_finished = (time + 0.2);
};

void() player_nail2 = [ 104, player_nail1 ]
{
	if (((self.weapon == IT_SUPER_NAILGUN) && (self.ammo_nails < 2)))
	{
		BM_OutOfAmmo();
		return;
	}
	if ((((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)) && (self.weapon != IT_NAILGUN)))
	{
		nailcasing(0);
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	if ((self.weapon == IT_SUPER_NAILGUN))
	{
		if ((self.weaponframe >= 10))
		{
			self.weaponframe = 1;
		}
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 9))
		{
			self.weaponframe = 1;
		}
	}
	SuperDamageSound();
	if (cvar("chase_active"))
	{
		W_FireSpikes(-4);
	}
	else
	{
		if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
		{
			W_FireSpikes(6);
		}
		else
		{
			if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
			{
				W_FireSpikes(autocvar_weapon_position_adjustable_projectile_nail1b_offset);
			}
			else
			{
				W_FireSpikes(-3);
			}
		}
	}
	self.attack_finished = (time + 0.2);
};

void() player_swimnail1 = [ 223, player_swimnail2 ]
{
	if (((self.weapon == IT_SUPER_NAILGUN) && (self.ammo_nails < 2)))
	{
		BM_OutOfAmmo();
		return;
	}
	if ((((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)) && (self.weapon != IT_NAILGUN)))
	{
		nailcasing(0);
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	if ((self.weapon == IT_SUPER_NAILGUN))
	{
		if ((self.weaponframe >= 10))
		{
			self.weaponframe = 1;
		}
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 9))
		{
			self.weaponframe = 1;
		}
	}
	SuperDamageSound();
	if (cvar("chase_active"))
	{
		W_FireSpikes(2);
	}
	else
	{
		if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
		{
			W_FireSpikes(10);
		}
		else
		{
			if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
			{
				W_FireSpikes(autocvar_weapon_position_adjustable_projectile_nail1a_offset);
			}
			else
			{
				W_FireSpikes(3);
			}
		}
	}
	self.attack_finished = (time + 0.2);
};

void() player_swimnail2 = [ 225, player_swimnail1 ]
{
	if (((self.weapon == IT_SUPER_NAILGUN) && (self.ammo_nails < 2)))
	{
		BM_OutOfAmmo();
		return;
	}
	if ((((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)) && (self.weapon != IT_NAILGUN)))
	{
		nailcasing(0);
	}
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	if ((self.weapon == IT_SUPER_NAILGUN))
	{
		if ((self.weaponframe >= 10))
		{
			self.weaponframe = 1;
		}
		self.weaponframe = (self.weaponframe + 1);
		if ((self.weaponframe == 9))
		{
			self.weaponframe = 1;
		}
	}
	SuperDamageSound();
	if (cvar("chase_active"))
	{
		W_FireSpikes(-4);
	}
	else
	{
		if ((autocvar_weapon_position_right && !autocvar_weapon_position_fully_adjustable))
		{
			W_FireSpikes(6);
		}
		else
		{
			if ((!autocvar_weapon_position_right && autocvar_weapon_position_fully_adjustable))
			{
				W_FireSpikes(autocvar_weapon_position_adjustable_projectile_nail1b_offset);
			}
			else
			{
				W_FireSpikes(-3);
			}
		}
	}
	self.attack_finished = (time + 0.2);
};

void() player_light1 = [ 105, player_light2 ]
{
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	self.weaponframe = (self.weaponframe + 1);
	if ((self.weaponframe == 5))
	{
		self.weaponframe = 1;
	}
	SuperDamageSound();
	W_FireLightning();
	self.attack_finished = (time + 0.2);
};

void() player_light2 = [ 106, player_light1 ]
{
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	self.weaponframe = (self.weaponframe + 1);
	if ((self.weaponframe == 5))
	{
		self.weaponframe = 1;
	}
	SuperDamageSound();
	W_FireLightning();
	self.attack_finished = (time + 0.2);
};

void() player_mage1 = [ 105, player_mage2 ]
{
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	self.weaponframe = 18;
	self.animate_mage_weapon_helper = 1;
	SuperDamageSound();
	W_FireLightning();
	self.attack_finished = (time + 0.2);
};

void() player_mage2 = [ 106, player_mage1 ]
{
	self.effects = (self.effects | EF_MUZZLEFLASH);
	if (!self.button0)
	{
		player_run();
		return;
	}
	self.weaponframe = 19;
	self.animate_mage_weapon_helper = 1;
	SuperDamageSound();
	W_FireLightning();
	self.attack_finished = (time + 0.2);
};

void() player_nade1 = [ 119, player_nade2 ]
{
	self.weaponframe = 0;
	self.throwing = 1;
	sound7(self, CHAN_WEAPON, "weapons/grenarm.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	self.impulse = 0;
};

void() player_nade2 = [ 120, player_nade3 ]
{
	self.weaponframe = 1;
	if ((autocvar_effects_explosion_shake != 0))
	{
		self.punchangle_x = -3;
	}
};

void() player_nade3 = [ 121, player_nade4 ]
{
	self.weaponframe = 2;
	W_FireProximityGrenade();
};

void() player_nade4 = [ 122, player_nade5 ]
{
	sound7(self, CHAN_WEAPON, "weapons/grenthrow.wav", 1, ATTN_NORM, self.PLR_SNDSPD);
	self.weaponframe = 3;
};

void() player_nade5 = [ 123, player_run ]
{
	self.weaponframe = 4;
	self.impulse = 0;
	W_SetCurrentAmmo();
};

void() player_laser1 = [ 103, player_laser3 ]
{
	self.attack_finished = (time + 0.07);
	HIP_FireLaser(0);
};

void() player_laser2 = [ 104, player_laser3 ]
{
	self.attack_finished = (time + 0.07);
};

void() player_laser3 = [ 104, player_laser1 ]
{
	self.attack_finished = (time + 0.07);
	HIP_FireLaser(1);
};

void() player_laser4 = [ 103, player_laser1 ]
{
	self.attack_finished = (time + 0.07);
};

void() ThrowNade =
{
	if (((self.health < 1) || (self.throwing == 1)))
	{
		return;
	}
	if ((self.grenade_ammo <= 0))
	{
		sprint(self, "No Proximity Grenades.\n");
		return;
	}
	else
	{
		self.throwing = 1;
		self.impulse = 0;
		if ((autocvar_cheat_crazyexplosives == 1))
		{
			self.attack_finished = (time + 0.07);
		}
		else
		{
			self.attack_finished = (time + 0.55);
		}
		self.weaponmodel = "progs/v_nade.mdl";
		self.weaponframe = 0;
		player_nade1();
	}
};

void() player_rocket1 = [ 107, player_rocket2 ]
{
	self.weaponframe = 1;
	self.effects = (self.effects | EF_MUZZLEFLASH);
};

void() player_rocket2 = [ 108, player_rocket3 ]
{
	self.weaponframe = 2;
	if ((((autocvar_shellcasing == 1) && (autocvar_casingejectframe >= 1)) && (self.weapon == IT_ROCKET_LAUNCHER)))
	{
		missilecase(0);
	}
};

void() player_rocket3 = [ 109, player_rocket4 ]
{
	self.weaponframe = 3;
};

void() player_rocket4 = [ 110, player_rocket5 ]
{
	self.weaponframe = 4;
};

void() player_rocket5 = [ 111, player_rocket6 ]
{
	self.weaponframe = 5;
};

void() player_rocket6 = [ 112, player_run ]
{
	self.weaponframe = 6;
};

// Mega Man gun throw: the rocket firing pose; the view model is driven by MegaMan_ViewFrame
void() player_mm1 = [ 107, player_mm2 ] {};
void() player_mm2 = [ 108, player_mm3 ] {};
void() player_mm3 = [ 109, player_mm4 ] {};
void() player_mm4 = [ 110, player_mm5 ] {};
void() player_mm5 = [ 111, player_mm6 ] {};
void() player_mm6 = [ 112, player_run ] {};

void() PainSound =
{
	local float rs;

	if ((self.health < 0))
	{
		return;
	}
	if ((damage_attacker.classname == "teledeath"))
	{
		sound7(self, CHAN_VOICE, "player/teledth1.wav", 1, ATTN_NONE, SNDSPD);
		return;
	}
	if (((self.watertype == CONTENT_WATER) && (self.waterlevel == 3)))
	{
		DeathBubbles(1);
		if ((random() > 0.5))
		{
			sound(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_NORM);
		}
		else
		{
			sound(self, CHAN_VOICE, "player/drown2.wav", 1, ATTN_NORM);
		}
		return;
	}
	if ((self.watertype == CONTENT_SLIME))
	{
		if ((random() > 0.5))
		{
			sound7(self, CHAN_VOICE, "player/lburn1.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "player/lburn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		return;
	}
	if ((self.watertype == CONTENT_LAVA))
	{
		if ((random() > 0.5))
		{
			sound7(self, CHAN_VOICE, "player/lburn1.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_VOICE, "player/lburn2.wav", 1, ATTN_NORM, SNDSPD);
		}
		return;
	}
	if ((self.pain_finished > time))
	{
		self.axhitme = 0;
		return;
	}
	self.pain_finished = (time + 0.5);
	if ((self.axhitme == 1))
	{
		self.axhitme = 0;
		sound7(self, CHAN_VOICE, "player/axhit1.wav", 1, ATTN_NORM, SNDSPD);
		return;
	}
	rs = rint(((random() * 5) + 1));
	self.noise = "";
	if ((rs == 1))
	{
		self.noise = "player/pain1.wav";
	}
	else
	{
		if ((rs == 2))
		{
			self.noise = "player/pain2.wav";
		}
		else
		{
			if ((rs == 3))
			{
				self.noise = "player/pain3.wav";
			}
			else
			{
				if ((rs == 4))
				{
					self.noise = "player/pain4.wav";
				}
				else
				{
					if ((rs == 5))
					{
						self.noise = "player/pain5.wav";
					}
					else
					{
						self.noise = "player/pain6.wav";
					}
				}
			}
		}
	}
	sound7(self, CHAN_VOICE, self.noise, 1, ATTN_NORM, SNDSPD);
	return;
};

void() player_pain1 = [ 35, player_pain2 ]
{
	PainSound();
	if (!self.throwing)
	{
		self.weaponframe = 0;
	}
};

void() player_pain2 = [ 36, player_pain3 ]
{
};

void() player_pain3 = [ 37, player_pain4 ]
{
};

void() player_pain4 = [ 38, player_pain5 ]
{
};

void() player_pain5 = [ 39, player_pain6 ]
{
};

void() player_pain6 = [ 40, player_run ]
{
};

void() player_jump =
{
	if ((self.weapon == IT_AXE))
	{
		self.frame = 243;
	}
	else
	{
		self.frame = 247;
	}
	self.frame = (self.frame + 1);
};

void() player_axpain1 = [ 29, player_axpain2 ]
{
	PainSound();
	self.weaponframe = 0;
};

void() player_axpain2 = [ 30, player_axpain3 ]
{
};

void() player_axpain3 = [ 31, player_axpain4 ]
{
};

void() player_axpain4 = [ 32, player_axpain5 ]
{
};

void() player_axpain5 = [ 33, player_axpain6 ]
{
};

void() player_axpain6 = [ 34, player_run ]
{
};

void() player_pain =
{
	if ((self.weaponframe || self.throwing))
	{
		return;
	}
	if ((self.invisible_finished > time))
	{
		return;
	}
	if ((self.weapon == IT_AXE))
	{
		player_axpain1();
	}
	else
	{
		player_pain1();
	}
};

void() DeathBubblesSpawn =
{
	local entity bubble;

	if (((self.owner.waterlevel != 3) || (self.owner.classname != "player")))
	{
		remove(self);
		return;
	}
	bubble = spawn();
	setmodel(bubble, "progs/s_bubble.spr");
	setorigin(bubble, (self.owner.origin + '0 0 24'));
	bubble.movetype = MOVETYPE_NOCLIP;
	bubble.solid = 0;
	bubble.velocity = '0 0 15';
	bubble.nextthink = (time + 0.5);
	bubble.think = bubble_bob;
	bubble.classname = "bubble";
	bubble.frame = 0;
	bubble.cnt = 0;
	setsize(bubble, '-8 -8 -8', '8 8 8');
	self.nextthink = (time + 0.1);
	self.think = DeathBubblesSpawn;
	self.air_finished = (self.air_finished + 1);
	if ((self.air_finished >= self.bubble_count))
	{
		remove(self);
	}
};

void(float num_bubbles) DeathBubbles =
{
	local entity bubble_spawner;

	bubble_spawner = spawn();
	setorigin(bubble_spawner, self.origin);
	bubble_spawner.movetype = 0;
	bubble_spawner.solid = 0;
	bubble_spawner.nextthink = (time + 0.1);
	bubble_spawner.think = DeathBubblesSpawn;
	bubble_spawner.air_finished = 0;
	bubble_spawner.owner = self;
	bubble_spawner.bubble_count = num_bubbles;
	return;
};

void() DeathSound =
{
	local float rs;

	if (((self.waterlevel == 3) && (self.watertype == CONTENT_WATER)))
	{
		DeathBubbles(20);
		sound7(self, CHAN_VOICE, "player/h2odeath.wav", 1, ATTN_NORM, SNDSPD);
		return;
	}
	if ((self.watertype == CONTENT_SLIME))
	{
		DeathBubbles(20);
		sound7(self, CHAN_VOICE, "player/slimedeath.wav", 1, ATTN_NORM, SNDSPD);
		return;
	}
	if ((self.watertype == CONTENT_LAVA))
	{
		DeathBubbles(20);
		sound7(self, CHAN_VOICE, "player/lavadeath.wav", 1, ATTN_NORM, SNDSPD);
		return;
	}
	rs = rint(((random() * 4) + 1));
	if ((rs == 1))
	{
		self.noise = "player/death1.wav";
	}
	if ((rs == 2))
	{
		self.noise = "player/death2.wav";
	}
	if ((rs == 3))
	{
		self.noise = "player/death3.wav";
	}
	if ((rs == 4))
	{
		self.noise = "player/death4.wav";
	}
	if ((rs == 5))
	{
		self.noise = "player/death5.wav";
	}
	sound7(self, CHAN_VOICE, self.noise, 1, ATTN_NORM, SNDSPD);
	return;
};

void() PlayerDead =
{
	self.nextthink = -1;
	self.deadflag = DEAD_DEAD;
	self.avelocity = VEC_ORIGIN;
};

vector(float dm) VelocityForDamage =
{
	local vector v;

	v_x = 100 * crandom();
	if ((dm > -50))
	{
		v = v * 0.7;
	}
	else
	{
		if ((dm > -200))
		{
			v = v * 2;
		}
		else
		{
			v = v * 10;
		}
	}
	return (v);
};

void() gibsfade_noblood =
{
	if ((self.alpha && (self.scale <= 0.01)))
	{
		remove(self);
		return;
	}
	else
	{
		self.alpha = (self.alpha - 0.06);
	}
	self.scale = (self.scale - 0.04);
	self.nextthink = (time + 0.06);
	self.think = gibsfade_noblood;
};

void() gibsfade_blood =
{
	local vector v;

	v_x = self.origin_x;
	if ((self.alpha && (self.scale <= 0.5)))
	{
		sound7(self, CHAN_VOICE, "player/gibexplode.wav", 1, ATTN_NORM, SNDSPD);
		te_blood(v, '0 80 1000', 7);
		te_blood(v, '80 0 1000', 7);
		te_blood(v, '-80 0 1000', 7);
		te_blood(v, '0 -80 1000', 7);
		remove(self);
		return;
	}
	else
	{
		self.alpha = (self.alpha - 0.06);
	}
	self.scale = (self.scale - 0.04);
	self.nextthink = (time + 0.06);
	self.think = gibsfade_blood;
};

void() wepTouch =
{
	if (((time - self.delay) < 0.2))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_LAVA))
	{
		self.velocity = (self.velocity * 0.5);
		self.colormod = '0.4 0.1 0.1';
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SLIME))
	{
		self.velocity = (self.velocity * 0.5);
		self.colormod = '0.3 1.6 0.3';
		return;
	}
	if ((deathmatch && (self.nextthink <= 0)))
	{
		self.think = SUB_Remove;
		self.nextthink = (time + 60);
	}
	if (((other.classname == "player") || (other == self.owner)))
	{
		return;
	}
	if (((other.classname != "player") || !(other.flags & FL_MONSTER)))
	{
		if ((other == world))
		{
			if ((((((self.model == "progs/p_axe.md3") || (self.model == "progs/w_chainsaw.mdl")) || (self.model == "progs/w_knightsword.mdl")) || (self.model == "progs/w_wsword.mdl")) || (self.model == "progs/w_dknightsword.mdl")))
			{
				sound7(self, CHAN_BODY, "kickgib/gib_metal.wav", 1, ATTN_NORM, SNDSPD);
			}
			else
			{
				if ((self.model == "progs/gib_freddie_leg.mdl"))
				{
					if ((random() < 0.5))
					{
						sound7(self, CHAN_BODY, "debris/metal2.wav", 1, ATTN_NORM, SNDSPD);
					}
					else
					{
						sound7(self, CHAN_BODY, "debris/metal1.wav", 1, ATTN_NORM, SNDSPD);
					}
				}
				else
				{
					sound7(self, CHAN_BODY, "kickgib/gib_plastic.wav", 1, ATTN_NORM, SNDSPD);
				}
			}
			self.delay = time;
		}
	}
	else
	{
		return;
	}
};

void(string gibname, float dm) ThrowWeapon =
{
	local entity new;
	local vector org;

	new = spawn();
	org = self.origin + randompos((self.mins + '16 16 0'), (self.maxs - '16 16 0'));
	new.origin = org;
	new.origin_z = (new.origin_z + 5);
	if ((gibname == "progs/gib_freddie_leg.mdl"))
	{
		new.origin_z = (new.origin_z + 15);
		new.avelocity = (crandom() * '600 600 0');
	}
	else
	{
		new.avelocity = (crandom() * '0 600 0');
	}
	if ((gibname == "progs/w_playergun.mdl"))
	{
		// hand-repaired: the decompiler scrambled this weapon-to-model lookup
		if (self.weapon == IT_SHOTGUN)
			gibname = "progs/p_shot.md3";
		else if (self.weapon == IT_SUPER_SHOTGUN)
		{
			if (autocvar_qc_ssg == 1)
				gibname = "progs/QC/p_ssg.md3";
			else
				gibname = "progs/p_ssg.md3";
		}
		else if (self.weapon == IT_NAILGUN)
			gibname = "progs/ltg_p.md3";	// sniper rifle
		else if (self.weapon == IT_SUPER_NAILGUN)
			gibname = "progs/p_nail2.md3";
		else if (self.weapon == IT_GRENADE_LAUNCHER)
			gibname = "progs/p_rock.md3";
		else if (self.weapon == IT_ROCKET_LAUNCHER)
			gibname = "progs/p_rock2.md3";
		else if (self.weapon == IT_LIGHTNING)
			gibname = "progs/p_light.md3";
		else if (self.weapon == IT_LASER_CANNON)
			gibname = "progs/p_laser.md3";
		else if (self.weapon == IT_CHAINSAW)
			gibname = "progs/p_saw.md3";
		else
			gibname = "progs/p_shot.md3";
		new.frame = 256;
	}
	if ((gibname == "progs/p_axe.md3"))
	{
		new.frame = 256;
	}
	setmodel(new, gibname);
	setsize(new, VEC_ORIGIN, VEC_ORIGIN);
	new.velocity = VelocityForDamage((dm / 2));
	new.gravity = 1.1;
	new.owner = self;
	new.solid = SOLID_CORPSE;
	new.movetype = MOVETYPE_BOUNCE;
	new.cansplash = TRUE;
	new.touch = wepTouch;
	GibPhysics(new);
	new.think = SUB_Remove;
	new.nextthink = (time + 20);
};

void(string gibname, float dm) ThrowBody =
{
	local entity new;
	local vector org;
	local vector dir;

	new = spawn();
	org = self.origin;
	new.origin = org;
	new.origin_z = (new.origin_z - 8);
	setmodel(new, gibname);
	new.colormap = self.colormap;
	if ((new.model == "progs/coal.mdl"))
	{
		new.gravity = 0.6;
		new.origin_z = (new.origin_z - ((random() * 4) + 0));
		new.scale = ((random() * 0.2) + 0.9);
		new.think = SUB_Remove;
		new.nextthink = (time + 45);
	}
	else
	{
		new.think = SUB_Remove;
		new.nextthink = (time + 20);
	}
	setsize(new, VEC_ORIGIN, VEC_ORIGIN);
	new.velocity = VelocityForDamage((dm / 2));
	new.solid = 0;
	new.movetype = MOVETYPE_BOUNCE;
	new.cansplash = TRUE;
	new.owner = new;
	dir = vectoangles(new.velocity);
	new.angles_y = (0 - 0);
	GibPhysics(new);
	if ((new.model == "progs/coal.mdl"))
	{
		new.avelocity = (crandom() * '300 100 200');
	}
	else
	{
		new.avelocity = (crandom() * '0 100 0');
	}
};

void(string gibname, float dm) ThrowGib =
{
	local entity new;
	local float gibsfadetime;
	local vector org;

	new = spawn();
	org = self.origin + randompos((self.mins + '16 16 0'), (self.maxs - '16 16 0'));
	new.origin = org;
	if ((gibname != "progs/gib_soldhead.mdl"))
	{
		new.origin_z = (new.origin_z + 15);
	}
	else
	{
		new.origin_z = (new.origin_z + 9);
		new.angles = self.angles;
	}
	if ((self.classname == "player"))
	{
		new.colormod = self.colormod;
		new.colormap = self.colormap;
	}
	new.effects = EF_LOWPRECISION;
	setmodel(new, gibname);
	if ((gibname == "progs/gib_soldhead.mdl"))
	{
		setsize(new, '0 0 -1', VEC_ORIGIN);
	}
	else
	{
		if ((gibname == "progs/gib_skull.mdl"))
		{
			setsize(new, '0 0 -2', VEC_ORIGIN);
		}
		else
		{
			setsize(new, VEC_ORIGIN, VEC_ORIGIN);
		}
	}
	new.classname = "gib";
	new.velocity = VelocityForDamage(dm);
	new.movetype = MOVETYPE_BOUNCE;
	new.cansplash = TRUE;
	if ((((((self.enemy.weapon == IT_ROCKET_LAUNCHER) || (self.enemy.weapon == IT_GRENADE_LAUNCHER)) || (self.sticky == 1)) && (random() < 0.125)) && (self.enemy.meleeing == 0)))
	{
		new.traileffectnum = particleeffectnum(/*45835i*/"burning_gib");
		new.colormod = '0.85 0.9 0.9';
		setsize(new, '0 0 -2', VEC_ORIGIN);
	}
	else
	{
		if (((((self.shocked == 100) || (self.enemy.weapon == IT_LASER_CANNON)) || (self.enemy.classname == "monster_enforcer")) || (self.enemy.classname == "monster_jim")))
		{
			if (((random() < 0.15) && (self.enemy.meleeing == 0)))
			{
				new.traileffectnum = particleeffectnum(/*45835i*/"burning_gib");
				new.colormod = '0.35 0.4 0.4';
				new.velocity = (new.velocity * 0.333333);
				setsize(new, '0 0 -2', VEC_ORIGIN);
			}
		}
	}
	new.owner = new;
	if ((autocvar_kickgibs == 1))
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch;
	}
	else
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch3;
	}
	if ((gibname != "progs/gibheart.mdl"))
	{
		if ((autocvar_gibspinstyle == 1))
		{
			new.avelocity = (crandom() * '0 600 0');
		}
		else
		{
			new.avelocity_x = (crandom() * 600);
			new.avelocity_y = (crandom() * 600);
			new.avelocity_z = (crandom() * 600);
		}
	}
	else
	{
		new.avelocity = (crandom() * '0 600 0');
	}
	if ((autocvar_gibsduration == 0))
	{
		new.nextthink = -1;
	}
	else
	{
		new.alpha = 1;
		new.scale = 1;
		gibsfadetime = autocvar_gibsduration;
		if ((autocvar_gibsexplode == 0))
		{
			new.think = gibsfade_noblood;
			new.ltime = time;
			new.nextthink = ((time + gibsfadetime) + (random() * 10));
		}
		else
		{
			new.think = gibsfade_blood;
			new.ltime = time;
			new.nextthink = ((time + gibsfadetime) + (random() * 10));
		}
	}
	BM_DMBurnGib(new);	// deathmatch: flames burn out after 6 s (gib_extra.qc)
	new.frame = 0;
	new.flags = 0;
	GibPhysics(new);
	if (((self.shocked > 0) && (self.shocked < 100)))
	{
		if ((!deathmatch && !coop))
		{
			new.traileffectnum = particleeffectnum(/*45847i*/"gib_lg");
		}
		new.colormod = '0.1 0.1 0.1';
		new.think = chargib_think;
		new.nextthink = (time + 0.1);
		return;
	}
	if ((self.weapon == IT_SUPER_SHOTGUN))
	{
		new.velocity = (new.velocity + (v_forward * 60));
	}
};

void(string gibname, float dm, float skincolor) ThrowGibSpider =
{
	local entity new;
	local float gibsfadetime;
	local vector org;

	new = spawn();
	org = self.origin + randompos((self.mins + '16 16 0'), (self.maxs - '16 16 0'));
	new.origin = org;
	setmodel(new, gibname);
	setsize(new, '-16 -16 0', '16 16 48');
	new.velocity = VelocityForDamage(dm);
	new.movetype = MOVETYPE_BOUNCE;
	new.skin = skincolor;
	new.cansplash = TRUE;
	if ((autocvar_kickgibs == 1))
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch;
	}
	else
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch3;
	}
	new.avelocity = (crandom() * '0 600 0');
	if ((autocvar_gibsduration == 0))
	{
		new.nextthink = -1;
	}
	else
	{
		new.alpha = 1;
		new.scale = 1;
		gibsfadetime = autocvar_gibsduration;
		if ((autocvar_gibsexplode == 0))
		{
			new.think = gibsfade_noblood;
			new.ltime = time;
			new.nextthink = ((time + gibsfadetime) + (random() * 10));
		}
		else
		{
			new.think = gibsfade_blood;
			new.ltime = time;
			new.nextthink = ((time + gibsfadetime) + (random() * 10));
		}
	}
	new.frame = 0;
	new.flags = 0;
	GibPhysics(new);
};

void() gib_heart_stop_beating =
{
	local float gibsfadetime;

	if ((autocvar_kickgibs == 1))
	{
		self.solid = SOLID_TRIGGER;
		self.touch = kick_touch_heart1_nobeating;
	}
	else
	{
		self.solid = SOLID_TRIGGER;
		self.touch = kick_touch_heart2_nobeating;
	}
	if ((autocvar_gibsduration == 0))
	{
		self.nextthink = -1;
	}
	else
	{
		gibsfadetime = autocvar_gibsduration;
		if ((autocvar_gibsexplode == 0))
		{
			self.think = gibsfade_noblood;
			self.ltime = time;
			self.nextthink = (time + gibsfadetime);
		}
		else
		{
			self.think = gibsfade_blood;
			self.ltime = time;
			self.nextthink = (time + gibsfadetime);
		}
	}
};

void() gib_heart_movement2 =
{
	local float deadheart;

	deadheart = autocvar_heartgiblifetime * 3;
	if ((self.heartcounter >= deadheart))
	{
		self.scale = 1;
		self.traileffectnum = particleeffectnum(/*45883i*/"gib_heart_nobeating");
		self.think = gib_heart_stop_beating;
		self.nextthink = time;
		return;
	}
	if ((self.scale > 0.92))
	{
		self.nextthink = (time + 0.014);
		self.scale = (self.scale - 0.007);
		self.think = gib_heart_movement2;
	}
	else
	{
		sound7(self, CHAN_VOICE, "ambience/gibheartbeat.wav", 0.8, ATTN_NORM);
		self.nextthink = time;
		self.think = gib_heart_movement;
		self.heartcounter = (self.heartcounter + 1);
	}
};

void() gib_heart_movement =
{
	if ((self.scale < 1.08))
	{
		self.nextthink = (time + 0.014);
		self.scale = (self.scale + 0.007);
		self.think = gib_heart_movement;
	}
	else
	{
		self.nextthink = time;
		self.think = gib_heart_movement2;
		self.heartcounter = (self.heartcounter + 1);
	}
};

void(string gibname, float dm) ThrowHeart =
{
	local entity new;
	local vector org;

	new = spawn();
	org = self.origin + randompos((self.mins + '16 16 0'), (self.maxs - '16 16 0'));
	new.origin = org;
	setmodel(new, gibname);
	setsize(new, '-16 -16 0', '16 16 48');
	new.velocity = VelocityForDamage(dm);
	new.movetype = MOVETYPE_BOUNCE;
	if ((autocvar_kickgibs == 1))
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch_heart1;
	}
	else
	{
		new.solid = SOLID_TRIGGER;
		new.touch = kick_touch_heart2;
	}
	new.avelocity = (crandom() * '80 600 20');
	new.traileffectnum = particleeffectnum(/*45903i*/"gib_heart");
	new.scale = 1;
	new.alpha = 1;
	new.heartcounter = 0;
	new.nextthink = (time + 0.1);
	new.think = gib_heart_movement;
	new.frame = 0;
	new.flags = 0;
	if ((self.shocked > 0))
	{
		new.velocity = (new.velocity * 0.2);
	}
	GibPhysics(new);
};

void(string gibname, float dm) ThrowHead =
{
	setmodel(self, gibname);
	self.cansplash = TRUE;
	self.frame = 0;
	self.scale = 1;
	if (autocvar_head_gibs_always_face_player)
	{
		self.nextthink = (time + 2);
		self.think = head_gib_faceplayer;
	}
	else
	{
		self.nextthink = -1;
	}
	self.movetype = MOVETYPE_BOUNCE;
	self.takedamage = 0;
	if ((self.shocked > 0))
	{
		self.colormod = '0.2 0.2 0.2';
		self.traileffectnum = particleeffectnum(/*15169i*/"charred_gib");
	}
	if ((autocvar_kickgibs == 1))
	{
		self.solid = SOLID_TRIGGER;
		self.touch = kick_touch2;
	}
	else
	{
		self.solid = SOLID_TRIGGER;
		self.touch = kick_touch3;
	}
	if ((self.flags & FL_ONGROUND))
	{
		if (((self.angles_z >= 80) || (self.angles_z <= -80)))
		{
			self.angles_z = 0;
		}
		if (((self.angles_x >= 80) || (self.angles_x <= -80)))
		{
			self.angles_x = 0;
		}
	}
	if ((self.shocked > 0))
	{
		self.velocity = (self.velocity * 0.2);
	}
	self.view_ofs = '0 0 8';
	setsize(self, '-16 -16 0', '16 16 56');
	self.velocity = VelocityForDamage(dm);
	self.origin_z = (self.origin_z - 24);
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	if ((self.enemy.weapon == IT_SUPER_SHOTGUN))
	{
		self.velocity = (self.velocity + (v_forward * 60));
	}
	if ((self.enemy.weapon == IT_LASER_CANNON))
	{
		self.colormod = '0.25 0.3 0.3';
		self.velocity = (self.velocity * 0.333333);
	}
	if ((self.shocked > 0))
	{
		self.velocity = (self.velocity * 0.25);
	}
	if ((self.model != "progs/player_swim.mdl"))
	{
		self.avelocity = (crandom() * '600 600 0');
	}
	else
	{
		self.avelocity = (crandom() * '0 600 0');
	}
	Gyro_Object_ClearPhysics(self);
	GibPhysics(self);
};

void() debTouch =
{
	if ((((other.classname == "player") || (other.classname == "debris")) || (other.flags & FL_MONSTER)))
	{
		return;
	}
	if ((random() > 0.34))
	{
		sound7(self, CHAN_ITEM, "debris/metal1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((random() < 0.64))
		{
			sound7(self, CHAN_ITEM, "debris/metal2.wav", 1, ATTN_NORM, SNDSPD);
		}
		else
		{
			sound7(self, CHAN_ITEM, "debris/metal3.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() debris_remove =
{
	Gyro_Object_ClearPhysics(self);
	remove(self);
};

void(vector org, vector vel, string debrisname) Throwdebris =
{
	local entity debris;

	debris = spawn();
	debris.cansplash = TRUE;
	setorigin(debris, org);
	setmodel(debris, debrisname);
	setsize(debris, VEC_ORIGIN, VEC_ORIGIN);
	debris.traileffectnum = particleeffectnum(/*26564i*/"debris");
	debris.velocity = (vel + (randomvec() * 2));
	debris.movetype = MOVETYPE_BOUNCE;
	debris.classname = "debris";
	debris.effects = EF_LOWPRECISION;
	if ((autocvar_kickdebris == 1))
	{
		debris.solid = SOLID_TRIGGER;
		debris.touch = kick_touch4;
	}
	else
	{
		debris.solid = SOLID_TRIGGER;
		debris.touch = debTouch;
	}
	debris.avelocity = (crandom() * '0 600 0');
	debris.alpha = 1;
	debris.scale = 1;
	debris.think = debris_remove;
	debris.nextthink = ((time + 10) + (random() * 5));
	debris.frame = 0;
	debris.flags = 0;
	debris.gravity = 0.8;
	Gyro_Object_Activate(debris, 3977);
};

void(vector org, vector vel, string gibname, float skintype) ThrowAfritGibs =
{
	local entity afritgib;
	local float gibsfadetime;
	local float zufall;

	afritgib = spawn();
	afritgib.cansplash = TRUE;
	setorigin(afritgib, org);
	setmodel(afritgib, gibname);
	setsize(afritgib, VEC_ORIGIN, VEC_ORIGIN);
	if (skintype)
	{
		afritgib.traileffectnum = particleeffectnum(/*45854i*/"Afrit_gib_grey");
		afritgib.skin_type = 1;
	}
	else
	{
		afritgib.traileffectnum = particleeffectnum(/*45869i*/"Afrit_gib_red");
		afritgib.skin_type = 0;
	}
	afritgib.velocity = (vel + (randomvec() * 25));
	afritgib.velocity_z = (afritgib.velocity_z + 100);
	afritgib.movetype = MOVETYPE_BOUNCE;
	zufall = random();
	if ((zufall > 0.8))
	{
		afritgib.scale = 0.8;
	}
	else
	{
		if ((zufall > 0.6))
		{
			afritgib.scale = 0.65;
		}
		else
		{
			if ((zufall > 0.4))
			{
				afritgib.scale = 0.5;
			}
			else
			{
				if ((zufall > 0.2))
				{
					afritgib.scale = 0.35;
				}
				else
				{
					afritgib.scale = 0.2;
				}
			}
		}
	}
	afritgib.alpha = 1;
	if (autocvar_kick_afrit_gibs)
	{
		afritgib.solid = SOLID_TRIGGER;
		afritgib.touch = kick_touch5temp;
	}
	else
	{
		afritgib.solid = SOLID_TRIGGER;
		afritgib.touch = kick_touch6temp;
	}
	afritgib.avelocity_x = (crandom() * 600);
	afritgib.avelocity_y = (crandom() * 600);
	afritgib.avelocity_z = (crandom() * 600);
	if ((autocvar_gibsduration == 0))
	{
		afritgib.nextthink = -1;
	}
	else
	{
		gibsfadetime = autocvar_gibsduration;
		afritgib.think = gibsfade_noblood;
		afritgib.ltime = time;
		afritgib.nextthink = ((time + gibsfadetime) + (random() * 10));
	}
	afritgib.frame = 0;
	afritgib.flags = (afritgib.flags - (afritgib.flags & FL_ONGROUND));
	GibPhysics(afritgib);
};

void() GibPlayer =
{
	if ((autocvar_player_model == 1))
	{
		ThrowHead("progs/h_player1.mdl", self.health);
	}
	else
	{
		if ((autocvar_player_model == 2))
		{
			ThrowHead("progs/h_player2.mdl", self.health);
		}
		else
		{
			if ((autocvar_player_model == 3))
			{
				ThrowHead("progs/h_player3.mdl", self.health);
			}
			else
			{
				if ((autocvar_player_model == 4))
				{
					ThrowHead("progs/h_player4.mdl", self.health);
				}
				else
				{
					ThrowHead("progs/h_player.mdl", self.health);
				}
			}
		}
	}
	self.delete_painskin = 1;
	ThrowGib("progs/gib_5.mdl", self.health);
	ThrowGib("progs/gib_soldfoot1.mdl", self.health);
	ThrowGib("progs/gib_soldfoot2.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowWeapon("progs/w_playergun.mdl", self.health);
	CeilSplat();
	CeilSplat();
	CeilSplat();
	CeilSplat();
	CeilSplat();
	if ((autocvar_heartgib >= 1))
	{
		ThrowHeart("progs/gibheart.mdl", self.health);
	}
	self.deadflag = DEAD_DEAD;
	if ((damage_attacker.classname == "teledeath"))
	{
		sound7(self, CHAN_VOICE, "player/teledth1.wav", 1, ATTN_NONE, SNDSPD);
		return;
	}
	if ((damage_attacker.classname == "teledeath2"))
	{
		sound7(self, CHAN_VOICE, "player/teledth1.wav", 1, ATTN_NONE, SNDSPD);
		return;
	}
	play_gibsound();
	gibdeath_effects();
};

void() setDamageSkin =
{
	if ((self.watertype == CONTENT_LAVA))
	{
		self.skin = 0;
	}
	if ((self.watertype == CONTENT_SLIME))
	{
		self.skin = 1;
	}
};

void() PlayerDie =
{
	local float i;
	local entity bed;

	FunGun_PlayerDie();
	// killed riding Eric's hospital bed: get out of it (and remove it) before the death sets up the body
	bed = self.veh_van;
	if (((bed != world) && (bed.veh_driver == self) && (bed.veh_kind == VEH_FORELOCO)))
		Veh_Leave(bed, bed.origin + '0 0 24', bed.velocity * 0.4 + '0 0 200', FALSE);
	if ((autocvar_chasecam_death_view && !cvar("chase_active")))
	{
		stuffcmd(self, "chase_active 1\n");
		stuffcmd(self, "chase_back 65\n");
		stuffcmd(self, "chase_up 70\n");
		stuffcmd(self, "chase_overhead 1\n");
	}
	self.items = (self.items - (self.items & IT_INVISIBILITY));
	self.invisible_finished = 0;
	self.invincible_finished = 0;
	self.super_damage_finished = 0;
	self.radsuit_finished = 0;
	self.modelindex = modelindex_player;
	if ((deathmatch || coop))
	{
		DropBackpack();
	}
	self.weaponmodel = "";
	self.view_ofs = '0 0 -8';
	self.deadflag = DEAD_DYING;
	self.solid = 0;
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	self.movetype = MOVETYPE_TOSS;
	if ((self.velocity_z < 10))
	{
		self.velocity_z = (self.velocity_z + (random() * 300));
	}
	player_die_ax1();
	if ((cvar("bm_death_anim") <= 0) || (damage_attacker.classname == "teledeath") || (damage_attacker.classname == "teledeath2"))
	{
		if (((self.model == "progs/player_id1.mdl") && (self.health < -40) && (self.health >= -95) && (self.enemy.weapon != IT_CHAINSAW)))
		{
			if ((random() < 0.45))
			{
				GibPlayer();
				return;
			}
		}
		else if (((self.health < -40) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.5))))
		{
			GibPlayer();
			return;
		}
	}
	if (!self.ishuman)
	{
		self.angles_y = 0;
	}
	DeathSound();
	self.angles_x = 0;
	self.angles_z = 0;
	spawn_bloodpool(0.5);
	if ((self.model == "progs/player_torso.mdl"))
	{
		setmodel(self, "progs/player.mdl");
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
	if (((self.model == "progs/player_id1.mdl") && (self.watertype != CONTENT_LAVA) && (self.watertype != CONTENT_SLIME) && !((self.watertype == CONTENT_WATER) && (self.waterlevel >= 2))))
	{
		if (PD_TryCustomPlayerDeath())
			return;
	}
	if ((self.enemy.meleeing == 0))
	{
		if ((self.enemy.weapon == IT_SHOTGUN))
		{
			if ((random() < 0.3))
			{
				ThrowGib("progs/chop.mdl", self.health);
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_ssg.mdl";
				setmodel(self, "progs/player_ssg.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_diessg1();
				sound7(self, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
				return;
			}
			else
			{
				ThrowWeapon("progs/w_playergun.mdl", self.health);
			}
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
		}
		if ((self.enemy.weapon == IT_NAILGUN))
		{
			if ((random() < 0.5))
			{
				self.delete_painskin = 1;
				self.model = "progs/player_ng.mdl";
				setmodel(self, "progs/player_ng.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_dienail1();
				return;
			}
			else
			{
				self.delete_painskin = 1;
				self.model = "progs/player_holes.mdl";
				setmodel(self, "progs/player_holes.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_diea1();
				pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
				sound7(self, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
				return;
			}
		}
		if ((self.enemy.weapon == IT_SUPER_SHOTGUN))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			if ((random() < 0.3))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/chop.mdl", self.health);
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_ssg.mdl";
				setmodel(self, "progs/player_ssg.mdl");
				player_diessg1();
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				return;
			}
			else
			{
				if (((random() >= 0.5) && (random() <= 0.7)))
				{
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowGib("progs/chop.mdl", self.health);
					ThrowWeapon("progs/p_axe.md3", self.health);
					ThrowWeapon("progs/w_playergun.mdl", self.health);
					self.delete_painskin = 1;
					self.model = "progs/player_ssg.mdl";
					setmodel(self, "progs/player_ssg.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					player_diessg1();
					sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
					ThrowHead("progs/gib_player_torso_head.mdl", self.health);
					ThrowGib("progs/gib_player_larm.mdl", self.health);
					ThrowGib("progs/gib_player_legs.mdl", self.health);
					self.deadflag = DEAD_DEAD;
					return;
				}
				else
				{
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
					}
					ThrowGib("progs/chop.mdl", self.health);
					ThrowWeapon("progs/p_axe.md3", self.health);
					ThrowWeapon("progs/w_playergun.mdl", self.health);
					self.delete_painskin = 1;
					player_diea1();
					sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
					ThrowHead("progs/gib_player_torso.mdl", self.health);
					ThrowGib("progs/gib_player_larm.mdl", self.health);
					ThrowGib("progs/gib_player_larm.mdl", self.health);
					ThrowGib("progs/gib_player_head.mdl", self.health);
					ThrowGib("progs/gib_player_legs.mdl", self.health);
					self.deadflag = DEAD_DEAD;
					return;
				}
			}
		}
		if (((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((random() < 0.2))
			{
				ThrowWeapon("progs/p_axe.md3", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_axe.mdl";
				setmodel(self, "progs/player_axe.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_dieaxe1();
				return;
			}
			else
			{
				if (((random() >= 0.2) && (random() < 0.5)))
				{
					ThrowWeapon("progs/p_axe.md3", self.health);
					ThrowWeapon("progs/w_playergun.mdl", self.health);
					self.delete_painskin = 1;
					self.model = "progs/player_disarm.mdl";
					setmodel(self, "progs/player_disarm.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					player_dieaxc1();
					return;
				}
				else
				{
					ThrowWeapon("progs/p_axe.md3", self.health);
					ThrowWeapon("progs/w_playergun.mdl", self.health);
					self.delete_painskin = 1;
					self.model = "progs/player_decap.mdl";
					setmodel(self, "progs/player_decap.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					player_dieaxb1();
					return;
				}
			}
		}
		if ((self.enemy.weapon == IT_SUPER_NAILGUN))
		{
			if ((random() < 0.5))
			{
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_deleg.mdl";
				setmodel(self, "progs/player_deleg.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_diesng1();
				StickGib("progs/gib_player_torso_sng.mdl");
				return;
			}
			else
			{
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_deleg.mdl";
				setmodel(self, "progs/player_deleg.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_diesng1();
				ThrowGib("progs/gib_player_arm_sng.mdl", self.health);
				StickGib("progs/gib_player_head_sng.mdl");
				StickGib("progs/gib_player_torso_sng_b.mdl");
				return;
			}
		}
		if ((self.enemy.weapon == IT_ROCKET_LAUNCHER))
		{
			CeilSplat();
			CeilSplat();
			CeilSplat();
			CeilSplat();
			setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
			if ((random() < 0.6))
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/player_deleg.mdl";
				setmodel(self, "progs/player_deleg.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				player_diea1();
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib_player_head.mdl", self.health);
				sound7(self, CHAN_VOICE, "misc/z_gib.wav", 1, ATTN_IDLE, SNDSPD);
				return;
			}
			else
			{
				pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				ThrowWeapon("progs/p_axe.md3", self.health);
				ThrowWeapon("progs/w_playergun.mdl", self.health);
				self.delete_painskin = 1;
				player_diea1();
				ThrowGib("progs/gib_player_larm.mdl", self.health);
				ThrowHead("progs/gib_player_legs.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/gib_player_head.mdl", self.health);
				sound7(self, CHAN_VOICE, "misc/z_gib.wav", 1, ATTN_IDLE, SNDSPD);
				self.deadflag = DEAD_DEAD;
				return;
			}
		}
		if ((self.enemy.weapon == IT_LIGHTNING))
		{
			if ((random() < 0.3))
			{
			}
			else
			{
				self.delete_painskin = 1;
				self.model = "progs/player_melt.mdl";
				setmodel(self, "progs/player_melt.mdl");
				setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
				self.skin = 1;
				player_dielg1();
				return;
			}
		}
		if ((self.enemy.weapon == IT_LASER_CANNON))
		{
			gibdeath_effects();
		}
		if ((self.enemy.classname == "monster_army"))
		{
			if (((self.enemy.model == "progs/soldier1.mdl") || (self.enemy.model == "progs/soldier1_pain.mdl")))
			{
				if ((random() < 0.5))
				{
					self.delete_painskin = 1;
					self.model = "progs/player_ng.mdl";
					setmodel(self, "progs/player_ng.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					player_dienail1();
					return;
				}
				else
				{
					self.delete_painskin = 1;
					self.model = "progs/player_holes.mdl";
					setmodel(self, "progs/player_holes.mdl");
					setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
					player_diea1();
					pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
					sound7(self, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
					return;
				}
			}
			else
			{
				if (((self.enemy.model == "progs/soldier.mdl") || (self.enemy.model == "progs/soldier_pain.mdl")))
				{
					if ((random() < 0.4))
					{
						if ((autocvar_bloodextension == 1))
						{
							pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
						}
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowWeapon("progs/p_axe.md3", self.health);
						ThrowWeapon("progs/w_playergun.mdl", self.health);
						self.delete_painskin = 1;
						self.model = "progs/player_ssg.mdl";
						setmodel(self, "progs/player_ssg.mdl");
						setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
						player_diessg1();
						return;
					}
					else
					{
						ThrowWeapon("progs/w_playergun.mdl", self.health);
						self.delete_painskin = 1;
						self.model = "progs/player_ssg.mdl";
						setmodel(self, "progs/player_ssg.mdl");
						setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
						if ((random() < 0.5))
						{
							player_dieb1();
						}
						else
						{
							if (((random() >= 0.5) && (random() <= 0.8)))
							{
								player_died1();
							}
							else
							{
								player_diec1();
							}
						}
						sound7(self, CHAN_AUTO, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
						return;
					}
				}
			}
		}
		else
		{
			if (((self.enemy.classname == "monster_enforcer") && (self.enemy.skin != 1)))
			{
			}
			else
			{
				if ((self.enemy.classname == "monster_wizard"))
				{
					if ((random() < 0.4))
					{
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowGib("progs/chop.mdl", self.health);
						ThrowWeapon("progs/p_axe.md3", self.health);
						self.delete_painskin = 1;
						self.model = "progs/player_melt.mdl";
						setmodel(self, "progs/player_melt.mdl");
						self.skin = 0;
						player_die_melt1();
						self.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
						sound7(self, CHAN_VOICE, "player/slimedeath.wav", 1, ATTN_NONE);
						return;
					}
				}
				else
				{
					if (((self.enemy.classname == "monster_knight") || (self.enemy.classname == "monster_zombiek")))
					{
						if ((random() < 0.4))
						{
							ThrowGib("progs/chop.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							ThrowWeapon("progs/p_axe.md3", self.health);
							self.delete_painskin = 1;
							self.model = "progs/player_axe.mdl";
							setmodel(self, "progs/player_axe.mdl");
							setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
							player_dieaxe1();
							return;
						}
						else
						{
							ThrowGib("progs/chop.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							ThrowGib("progs/chop.mdl", self.health);
							ThrowWeapon("progs/p_axe.md3", self.health);
							ThrowWeapon("progs/w_playergun.mdl", self.health);
							self.delete_painskin = 1;
							self.model = "progs/player_decap.mdl";
							setmodel(self, "progs/player_decap.mdl");
							setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
							player_dieaxb1();
							return;
						}
					}
					else
					{
						if ((self.enemy.classname == "monster_hell_knight"))
						{
							if ((random() < 0.4))
							{
								ThrowGib("progs/chop.mdl", self.health);
								ThrowGib("progs/chop.mdl", self.health);
								ThrowGib("progs/chop.mdl", self.health);
								ThrowWeapon("progs/p_axe.md3", self.health);
								self.delete_painskin = 1;
								self.model = "progs/player_axe.mdl";
								setmodel(self, "progs/player_axe.mdl");
								setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
								player_dieaxe1();
								return;
							}
							else
							{
								if (((random() >= 0.4) && (random() < 0.8)))
								{
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowWeapon("progs/p_axe.md3", self.health);
									ThrowWeapon("progs/w_playergun.mdl", self.health);
									self.delete_painskin = 1;
									self.model = "progs/player_decap.mdl";
									setmodel(self, "progs/player_decap.mdl");
									setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
									player_dieaxb1();
									return;
								}
							}
						}
						else
						{
							if ((self.enemy.classname == "monster_ogre"))
							{
								if ((random() < 0.4))
								{
									if ((autocvar_bloodextension == 1))
									{
										pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
									}
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowWeapon("progs/p_axe.md3", self.health);
									ThrowWeapon("progs/w_playergun.mdl", self.health);
									self.delete_painskin = 1;
									player_diea1();
									sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
									ThrowHead("progs/gib_player_torso.mdl", self.health);
									ThrowGib("progs/gib_player_larm.mdl", self.health);
									ThrowGib("progs/gib_player_larm.mdl", self.health);
									ThrowGib("progs/gib_player_head.mdl", self.health);
									ThrowGib("progs/gib_player_legs.mdl", self.health);
									self.deadflag = DEAD_DEAD;
									return;
								}
							}
							else
							{
								if ((self.enemy.classname == "buzzsaw"))
								{
									if ((autocvar_bloodextension == 1))
									{
										pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
									}
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowGib("progs/chop.mdl", self.health);
									ThrowWeapon("progs/p_axe.md3", self.health);
									ThrowWeapon("progs/w_playergun.mdl", self.health);
									self.delete_painskin = 1;
									self.model = "progs/player_buzz.mdl";
									setmodel(self, "progs/player_buzz.mdl");
									sound7(self, CHAN_VOICE, "player/buzzdeath.wav", 1, ATTN_IDLE, SNDSPD);
									if ((random() < 0.4))
									{
										ThrowHead("progs/gib_player_torso.mdl", self.health);
										ThrowGib("progs/gib_player_head.mdl", self.health);
									}
									else
									{
										ThrowHead("progs/gib_player_torso_head.mdl", self.health);
									}
									ThrowGib("progs/gib_player_larm.mdl", self.health);
									ThrowGib("progs/gib_player_larm.mdl", self.health);
									ThrowGib("progs/gib_player_legs.mdl", self.health);
									setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
									self.deadflag = DEAD_DEAD;
									return;
								}
								else
								{
									if ((self.enemy.classname == "pendulum"))
									{
										if ((random() < 0.6))
										{
											ThrowGib("progs/chop.mdl", self.health);
											ThrowGib("progs/chop.mdl", self.health);
											ThrowGib("progs/chop.mdl", self.health);
											ThrowWeapon("progs/p_axe.md3", self.health);
											ThrowWeapon("progs/w_playergun.mdl", self.health);
											ThrowGib("progs/gib_player_torso_head.mdl", self.health);
											self.delete_painskin = 1;
											self.model = "progs/player_deleg.mdl";
											setmodel(self, "progs/player_deleg.mdl");
											player_dieb1();
											sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
											sound7(self, CHAN_AUTO, "player/axeflesh3.wav", 1, ATTN_IDLE, SNDSPD);
											if ((autocvar_bloodextension == 1))
											{
												pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
											}
											setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
											return;
										}
										else
										{
											ThrowGib("progs/chop.mdl", self.health);
											ThrowGib("progs/chop.mdl", self.health);
											ThrowGib("progs/chop.mdl", self.health);
											ThrowWeapon("progs/p_axe.md3", self.health);
											ThrowWeapon("progs/w_playergun.mdl", self.health);
											self.delete_painskin = 1;
											self.model = "progs/player_decap.mdl";
											setmodel(self, "progs/player_decap.mdl");
											player_dieaxb1();
											setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
											return;
										}
									}
									else
									{
										if ((self.enemy.classname != "player"))
										{
											ThrowWeapon("progs/w_playergun.mdl", self.health);
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	if ((self.watertype == CONTENT_LAVA))
	{
		if ((self.waterlevel == 1))
		{
			self.model = "progs/player_scorchlegs.mdl";
			setmodel(self, "progs/player_scorchlegs.mdl");
		}
		else
		{
			self.model = "progs/player_scorch.mdl";
			setmodel(self, "progs/player_scorch.mdl");
		}
		player_die_scorch1();
		return;
	}
	if ((self.watertype == CONTENT_SLIME))
	{
		self.model = "progs/player_melt.mdl";
		setmodel(self, "progs/player_melt.mdl");
		player_die_melt1();
		self.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
		return;
	}
	if (((self.watertype == CONTENT_WATER) && (self.waterlevel >= 2)))
	{
		player_dieb1();
		PlayerDead();
		if ((deathmatch || coop))
		{
			ThrowBody("progs/player_swim.mdl", self.health);
			ThrowHead("progs/chop.mdl", self.health);
		}
		else
		{
			ThrowHead("progs/player_swim.mdl", self.health);
		}
		return;
	}
	if ((self.weapon == IT_AXE))
	{
		player_die_ax1();
		return;
	}
	i = cvar("temp1");
	if (!i)
	{
		i = 1 + floor((random() * 6));
	}
	if ((i == 1))
	{
		player_diea1();
	}
	else
	{
		if ((i == 2))
		{
			player_dieb1();
		}
		else
		{
			if ((i == 3))
			{
				player_diec1();
			}
			else
			{
				if ((i == 4))
				{
					player_died1();
				}
				else
				{
					player_diee1();
				}
			}
		}
	}
};

void() set_suicide_frame =
{
	if (((((((((((((((self.model != "progs/player_id1.mdl") && (self.model != "progs/player_torso.mdl")) && (self.model != "progs/player.mdl")) && (self.model != "progs/player1.mdl")) && (self.model != "progs/player2.mdl")) && (self.model != "progs/player3.mdl")) && (self.model != "progs/player4.mdl")) && (self.model != "progs/player_shot.mdl")) && (self.model != "progs/player_shot2.mdl")) && (self.model != "progs/player_nail.mdl")) && (self.model != "progs/player_nail2.mdl")) && (self.model != "progs/player_rock.mdl")) && (self.model != "progs/player_rock2.mdl")) && (self.model != "progs/player_light.mdl")))
	{
		return;
	}
	self.solid = 0;
	self.movetype = MOVETYPE_TOSS;
	self.deadflag = DEAD_DEAD;
	self.nextthink = -1;
};

void() player_diea1 = [ 50, player_diea2 ]
{
};

void() player_diea2 = [ 51, player_diea3 ]
{
};

void() player_diea3 = [ 52, player_diea4 ]
{
};

void() player_diea4 = [ 53, player_diea5 ]
{
};

void() player_diea5 = [ 54, player_diea6 ]
{
};

void() player_diea6 = [ 55, player_diea7 ]
{
};

void() player_diea7 = [ 56, player_diea8 ]
{
};

void() player_diea8 = [ 57, player_diea9 ]
{
};

void() player_diea9 = [ 58, player_diea10 ]
{
};

void() player_diea10 = [ 59, player_diea11 ]
{
};

void() player_diea11 = [ 60, player_diea11 ]
{
	PlayerDead();
};

void() player_dieb1 = [ 61, player_dieb2 ]
{
};

void() player_dieb2 = [ 62, player_dieb3 ]
{
};

void() player_dieb3 = [ 63, player_dieb4 ]
{
};

void() player_dieb4 = [ 64, player_dieb5 ]
{
};

void() player_dieb5 = [ 65, player_dieb6 ]
{
};

void() player_dieb6 = [ 66, player_dieb7 ]
{
};

void() player_dieb7 = [ 67, player_dieb8 ]
{
};

void() player_dieb8 = [ 68, player_dieb9 ]
{
};

void() player_dieb9 = [ 69, player_dieb9 ]
{
	PlayerDead();
};

void() player_diec1 = [ 70, player_diec2 ]
{
};

void() player_diec2 = [ 71, player_diec3 ]
{
};

void() player_diec3 = [ 72, player_diec4 ]
{
};

void() player_diec4 = [ 73, player_diec5 ]
{
};

void() player_diec5 = [ 74, player_diec6 ]
{
};

void() player_diec6 = [ 75, player_diec7 ]
{
};

void() player_diec7 = [ 76, player_diec8 ]
{
};

void() player_diec8 = [ 77, player_diec9 ]
{
};

void() player_diec9 = [ 78, player_diec10 ]
{
};

void() player_diec10 = [ 79, player_diec11 ]
{
};

void() player_diec11 = [ 80, player_diec12 ]
{
};

void() player_diec12 = [ 81, player_diec13 ]
{
};

void() player_diec13 = [ 82, player_diec14 ]
{
};

void() player_diec14 = [ 83, player_diec15 ]
{
};

void() player_diec15 = [ 84, player_diec15 ]
{
	PlayerDead();
};

void() player_died1 = [ 85, player_died2 ]
{
};

void() player_died2 = [ 86, player_died3 ]
{
};

void() player_died3 = [ 87, player_died4 ]
{
};

void() player_died4 = [ 88, player_died5 ]
{
};

void() player_died5 = [ 89, player_died6 ]
{
};

void() player_died6 = [ 90, player_died7 ]
{
};

void() player_died7 = [ 91, player_died8 ]
{
};

void() player_died8 = [ 92, player_died9 ]
{
};

void() player_died9 = [ 93, player_died9 ]
{
	PlayerDead();
};

void() player_diee1 = [ 94, player_diee2 ]
{
};

void() player_diee2 = [ 95, player_diee3 ]
{
};

void() player_diee3 = [ 96, player_diee4 ]
{
};

void() player_diee4 = [ 97, player_diee5 ]
{
};

void() player_diee5 = [ 98, player_diee6 ]
{
};

void() player_diee6 = [ 99, player_diee7 ]
{
};

void() player_diee7 = [ 100, player_diee8 ]
{
};

void() player_diee8 = [ 101, player_diee9 ]
{
};

void() player_diee9 = [ 102, player_diee9 ]
{
	PlayerDead();
};

void() player_die_ax1 = [ 41, player_die_ax2 ]
{
};

void() player_die_ax2 = [ 42, player_die_ax3 ]
{
};

void() player_die_ax3 = [ 43, player_die_ax4 ]
{
};

void() player_die_ax4 = [ 44, player_die_ax5 ]
{
};

void() player_die_ax5 = [ 45, player_die_ax6 ]
{
};

void() player_die_ax6 = [ 46, player_die_ax7 ]
{
};

void() player_die_ax7 = [ 47, player_die_ax8 ]
{
};

void() player_die_ax8 = [ 48, player_die_ax9 ]
{
};

void() player_die_ax9 = [ 49, player_die_ax9 ]
{
	PlayerDead();
};

void() player_die_melt1 = [ 143, player_die_melt2 ]
{
	pointparticles(particleeffectnum(/*19565i*/"monsteracid"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt2 = [ 144, player_die_melt3 ]
{
};

void() player_die_melt3 = [ 145, player_die_melt4 ]
{
	pointparticles(particleeffectnum(/*12483i*/"corpse_charred"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt4 = [ 146, player_die_melt5 ]
{
};

void() player_die_melt5 = [ 147, player_die_melt6 ]
{
	pointparticles(particleeffectnum(/*19565i*/"monsteracid"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt6 = [ 148, player_die_melt7 ]
{
};

void() player_die_melt7 = [ 149, player_die_melt8 ]
{
	pointparticles(particleeffectnum(/*12483i*/"corpse_charred"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt8 = [ 150, player_die_melt9 ]
{
};

void() player_die_melt9 = [ 151, player_die_melt10 ]
{
	pointparticles(particleeffectnum(/*19565i*/"monsteracid"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt10 = [ 152, player_die_melt11 ]
{
};

void() player_die_melt11 = [ 153, player_die_melt12 ]
{
	pointparticles(particleeffectnum(/*12483i*/"corpse_charred"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt12 = [ 154, player_die_melt13 ]
{
};

void() player_die_melt13 = [ 155, player_die_melt14 ]
{
	pointparticles(particleeffectnum(/*19565i*/"monsteracid"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt14 = [ 156, player_die_melt15 ]
{
};

void() player_die_melt15 = [ 157, player_die_melt16 ]
{
	pointparticles(particleeffectnum(/*12483i*/"corpse_charred"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt16 = [ 158, player_die_melt17 ]
{
	pointparticles(particleeffectnum(/*19565i*/"monsteracid"), self.origin, VEC_ORIGIN, 1);
};

void() player_die_melt17 = [ 159, player_die_melt18 ]
{
	PlayerDead();
};

void() player_die_melt18 = [ 160, player_die_melt18 ]
{
};

void() player_die_scorch1 = [ 143, player_die_scorch2 ]
{
};

void() player_die_scorch2 = [ 144, player_die_scorch3 ]
{
};

void() player_die_scorch3 = [ 145, player_die_scorch4 ]
{
};

void() player_die_scorch4 = [ 146, player_die_scorch5 ]
{
};

void() player_die_scorch5 = [ 147, player_die_scorch6 ]
{
};

void() player_die_scorch6 = [ 148, player_die_scorch7 ]
{
};

void() player_die_scorch7 = [ 149, player_die_scorch8 ]
{
};

void() player_die_scorch8 = [ 150, player_die_scorch9 ]
{
};

void() player_die_scorch9 = [ 151, player_die_scorch10 ]
{
};

void() player_die_scorch10 = [ 152, player_die_scorch11 ]
{
};

void() player_die_scorch11 = [ 153, player_die_scorch12 ]
{
};

void() player_die_scorch12 = [ 154, player_die_scorch13 ]
{
};

void() player_die_scorch13 = [ 155, player_die_scorch14 ]
{
};

void() player_die_scorch14 = [ 156, player_die_scorch15 ]
{
};

void() player_die_scorch15 = [ 157, player_die_scorch16 ]
{
};

void() player_die_scorch16 = [ 158, player_die_scorch17 ]
{
};

void() player_die_scorch17 = [ 159, player_die_scorch18 ]
{
	PlayerDead();
	if ((deathmatch || coop))
	{
		ThrowGib("progs/gib_player_helmet.mdl", self.health);
		ThrowHead("progs/p_axe.md3", self.health);
	}
	else
	{
		ThrowHead("progs/gib_player_helmet.mdl");
	}
};

void() player_die_scorch18 = [ 160, player_die_scorch18 ]
{
};

void() player_diessg1 = [ 161, player_diessg2 ]
{
};

void() player_diessg2 = [ 162, player_diessg3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diessg3 = [ 163, player_diessg4 ]
{
};

void() player_diessg4 = [ 164, player_diessg5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diessg5 = [ 165, player_diessg6 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diessg6 = [ 166, player_diessg7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diessg7 = [ 167, player_diessg8 ]
{
};

void() player_diessg8 = [ 168, player_diessg9 ]
{
};

void() player_diessg9 = [ 169, player_diessg10 ]
{
};

void() player_diessg10 = [ 170, player_diessg11 ]
{
};

void() player_diessg11 = [ 171, player_diessg12 ]
{
};

void() player_diessg12 = [ 172, player_diessg13 ]
{
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diessg13 = [ 173, player_diessg14 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diessg14 = [ 174, player_diessg15 ]
{
};

void() player_diessg15 = [ 175, player_diessg15 ]
{
	PlayerDead();
};

void() player_dieaxe1 = [ 176, player_dieaxe2 ]
{
};

void() player_dieaxe2 = [ 177, player_dieaxe3 ]
{
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxe3 = [ 178, player_dieaxe4 ]
{
};

void() player_dieaxe4 = [ 179, player_dieaxe5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxe5 = [ 180, player_dieaxe6 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxe6 = [ 181, player_dieaxe7 ]
{
};

void() player_dieaxe7 = [ 182, player_dieaxe8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxe8 = [ 183, player_dieaxe9 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxe9 = [ 184, player_dieaxe10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxe10 = [ 185, player_dieaxe11 ]
{
};

void() player_dieaxe11 = [ 186, player_dieaxe12 ]
{
};

void() player_dieaxe12 = [ 187, player_dieaxe13 ]
{
};

void() player_dieaxe13 = [ 188, player_dieaxe14 ]
{
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxe14 = [ 189, player_dieaxe14 ]
{
	PlayerDead();
};

void() player_dieaxb1 = [ 50, player_dieaxb2 ]
{
};

void() player_dieaxb2 = [ 51, player_dieaxb3 ]
{
	ThrowGib("progs/gib_player_head.mdl", self.health);
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxb3 = [ 52, player_dieaxb4 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxb4 = [ 53, player_dieaxb5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxb5 = [ 54, player_dieaxb6 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxb6 = [ 55, player_dieaxb7 ]
{
};

void() player_dieaxb7 = [ 56, player_dieaxb8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxb8 = [ 57, player_dieaxb9 ]
{
};

void() player_dieaxb9 = [ 58, player_dieaxb10 ]
{
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxb10 = [ 59, player_dieaxb11 ]
{
};

void() player_dieaxb11 = [ 60, player_dieaxb11 ]
{
	PlayerDead();
};

void() player_dieaxc1 = [ 35, player_dieaxc2 ]
{
};

void() player_dieaxc2 = [ 36, player_dieaxc3 ]
{
	ThrowGib("progs/gib_player_larm.mdl", self.health);
};

void() player_dieaxc3 = [ 37, player_dieaxc4 ]
{
	sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxc4 = [ 38, player_dieaxc5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxc5 = [ 39, player_dieaxc6 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxc6 = [ 53, player_dieaxc7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxc7 = [ 54, player_dieaxc8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxc8 = [ 55, player_dieaxc9 ]
{
};

void() player_dieaxc9 = [ 56, player_dieaxc10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dieaxc10 = [ 57, player_dieaxc11 ]
{
};

void() player_dieaxc11 = [ 58, player_dieaxc12 ]
{
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dieaxc12 = [ 59, player_dieaxc13 ]
{
};

void() player_dieaxc13 = [ 60, player_dieaxc13 ]
{
	PlayerDead();
};

void() player_diesng1 = [ 35, player_diesng2 ]
{
};

void() player_diesng2 = [ 36, player_diesng3 ]
{
};

void() player_diesng3 = [ 37, player_diesng4 ]
{
	sound7(self, CHAN_VOICE, "player/gibexplode.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diesng4 = [ 38, player_diesng5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diesng5 = [ 39, player_diesng6 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diesng6 = [ 53, player_diesng7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diesng7 = [ 54, player_diesng8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diesng8 = [ 55, player_diesng9 ]
{
};

void() player_diesng9 = [ 56, player_diesng10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_diesng10 = [ 57, player_diesng11 ]
{
};

void() player_diesng11 = [ 58, player_diesng12 ]
{
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_diesng12 = [ 59, player_diesng13 ]
{
};

void() player_diesng13 = [ 60, player_diesng13 ]
{
	PlayerDead();
};

void() player_dielg1 = [ 35, player_dielg2 ]
{
	self.shocked = 1;
	self.colormod = '0.1 0.1 0.1';
};

void() player_dielg2 = [ 37, player_dielg3 ]
{
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg3 = [ 39, player_dielg4 ]
{
	ThrowGib("progs/chop.mdl", self.health);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg4 = [ 36, player_dielg5 ]
{
	lg_shock_player();
	ThrowGib("progs/chop.mdl", self.health);
	sound7(self, CHAN_AUTO, "weapons/lstart.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg5 = [ 39, player_dielg6 ]
{
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg6 = [ 35, player_dielg7 ]
{
	lg_shock_player();
	sound7(self, CHAN_AUTO, "weapons/lstart.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg7 = [ 39, player_dielg8 ]
{
	ThrowGib("progs/chop.mdl", self.health);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg8 = [ 35, player_dielg9 ]
{
	lg_shock_player();
	ThrowGib("progs/chop.mdl", self.health);
	sound7(self, CHAN_AUTO, "weapons/lstart.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg9 = [ 39, player_dielg10 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_VOICE, "player/drown1.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dielg10 = [ 35, player_dielg11 ]
{
	PlayerDead();
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	ThrowGib("progs/gib_player_head.mdl", self.health);
	ThrowGib("progs/gib_player_larm.mdl", self.health);
	ThrowHead("progs/gib_player_torso.mdl", self.health);
	ThrowWeapon("progs/p_axe.md3", self.health);
	ThrowGib("progs/gib_soldfoot2.mdl", self.health);
	sound7(self, CHAN_VOICE, "player/gib.wav", 1, ATTN_IDLE, SNDSPD);
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
	ThrowGib("progs/gib_player_larm.mdl", self.health);
	ThrowGib("progs/gib_soldfoot1.mdl", self.health);
	ThrowWeapon("progs/w_playergun.mdl", self.health);
};

void() player_dielg11 = [ 40, player_dielg11 ]
{
};

void() player_dienail1 = [ 190, player_dienail2 ]
{
};

void() player_dienail2 = [ 191, player_dienail3 ]
{
	sound7(self, CHAN_VOICE, "player/gibexplode.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dienail3 = [ 192, player_dienail4 ]
{
};

void() player_dienail4 = [ 193, player_dienail5 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dienail5 = [ 194, player_dienail6 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dienail6 = [ 195, player_dienail7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() player_dienail7 = [ 196, player_dienail8 ]
{
};

void() player_dienail8 = [ 197, player_dienail9 ]
{
};

void() player_dienail9 = [ 198, player_dienail10 ]
{
};

void() player_dienail10 = [ 199, player_dienail11 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dienail11 = [ 200, player_dienail12 ]
{
};

void() player_dienail12 = [ 201, player_dienail13 ]
{
};

void() player_dienail13 = [ 202, player_dienail14 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() player_dienail14 = [ 203, player_dienail15 ]
{
};

void() player_dienail15 = [ 204, player_dienail16 ]
{
};

void() player_dienail16 = [ 205, player_dienail17 ]
{
	ThrowWeapon("progs/w_playergun.mdl", self.health);
};

void() player_dienail17 = [ 206, player_dienail17 ]
{
	sound7(self, CHAN_AUTO, "soldier/fall_forwards.wav", 1, ATTN_IDLE, SNDSPD);
	pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
	PlayerDead();
};
