//Decompiled code. Please respect the original copyright.

float(entity e) bot_size_player =
{
	local float sz;

	sz = e.health + (e.armorvalue * e.armortype);
	if ((e.weapon == 32))
	{
		sz = sz + 60;
	}
	else
	{
		if ((e.weapon == 64))
		{
			sz = sz + 60;
		}
		else
		{
			if ((e.weapon == 16))
			{
				sz = sz + 50;
			}
			else
			{
				if ((e.weapon == 8))
				{
					sz = sz + 50;
				}
				else
				{
					if ((e.weapon == 4))
					{
						sz = sz + 40;
					}
					else
					{
						if ((e.weapon == 2))
						{
							sz = sz + 40;
						}
						else
						{
							if ((e.weapon == 1))
							{
								sz = sz + 10;
							}
							else
							{
								if ((e.weapon == 4096))
								{
									sz = sz - 50;
								}
							}
						}
					}
				}
			}
		}
	}
	if ((e.items & 4194304))
	{
		sz = sz + 200;
	}
	if ((e.items & 1048576))
	{
		sz = sz + 300;
	}
	if ((e.items & 524288))
	{
		sz = sz + 250;
	}
	return (sz);
};

void() bot_dodge_stuff =
{
	local entity foe, best_m, best_s;
	local float avdist, dist_m, dist_s;
	local float foesz;
	local float flen;
	local float tsz;
	local vector v;

	if ((waypoint_mode > WM_LOADED))
	{
		return;
	}
	if (self.avoid)
	{
		local float wf;
		wf = wasfreed(self.avoid);
		if (wf)
			self.avoid = world;
	}
	if ((time < self.dodge_time))
		return;
	self.dodge_time = (time + 0.05);
	self.avoid = world;
	if (self.enemy)
	{
		if (bm_wasfreed(self.enemy))
		{
			self.enemy = world;
		}
	}
	if (self.enemy)
	{
		v = self.origin - realorigin(self.enemy);
		foesz = bot_size_player(self.enemy);
		foesz = foesz + (vlen(v) * 0.5);
	}
	else
	{
		foesz = 9999999;
	}
	avdist = 256;
	dist_m = 256;
	dist_s = 256;
	best_m = world;
	best_s = world;
	foe = findradius(self.origin, 256);
	while (foe)
	{
		if ((foe.classname == "grenade"))
		{
			flen = vlen((foe.origin - self.origin));
			if ((flen < avdist))
			{
				avdist = flen;
				self.avoid = foe;
			}
		}
		else if (!self.avoid)
		{
			if (((foe.classname == "missile") && (foe.owner != self)))
			{
				flen = vlen((foe.origin - self.origin));
				if ((flen < dist_m))
				{
					dist_m = flen;
					best_m = foe;
				}
			}
			else if ((!best_m && (foe.classname == "spike") && (foe.owner != self)))
			{
				flen = vlen((foe.origin - self.origin));
				if ((flen < dist_s))
				{
					dist_s = flen;
					best_s = foe;
				}
			}
		}
		foe = foe.chain;
	}
	if (!self.avoid)
	{
		if (best_m)
			self.avoid = best_m;
		else
			self.avoid = best_s;
	}
	if (coop)
	{
		if (!self.enemy)
		{
			foe = findradius(self.origin, 9999);
			while (foe)
			{
				if ((foe.flags & FL_MONSTER))
				{
					if ((foe.health > 0))
					{
						bot_size_player(foe);
						tsz = bot_size_player(foe) + (vlen((foe.origin - self.origin)) * 0.5);
						if ((tsz < foesz))
						{
							if (fisible(foe))
							{
								self.enemy = foe;
								foesz = tsz;
							}
						}
					}
				}
				foe = foe.chain;
			}
		}
	}
	else
	{
		foe = player_head;
		while (foe)
		{
			if ((foe != self))
			{
				if (((foe.modelindex != 0) && !(foe.flags & FL_NOTARGET)))
				{
					if ((foe.health > 0))
					{
						if (!((teamplay || CTF_ENABLED) && (self.team > 0) && (self.team == foe.team)))
						{
							tsz = bot_size_player(foe) + (vlen((foe.origin - self.origin)) * 0.35);
							if ((tsz < foesz))
							{
								if ((((vlen((foe.origin - self.origin)) < 950) || fov(foe) || (foe.b_sound > time) || (foe.show_hostile > time)) || (self.b_skill == 3)))
								{
									if (fisible(foe))
									{
										self.enemy = foe;
										foesz = tsz;
									}
								}
							}
						}
					}
				}
			}
			foe = foe._next;
		}
	}
};

vector(float wep) weapon_range =
{
	return (BM_BotWeaponRange(wep));
};

void(float brange) bot_weapon_switch =
{
	if (BM_BotWeaponSwitch(brange))
	{
		return;
	}
};

void() bot_shoot =
{
	BM_BotShoot();
};

void() bot_fight_style =
{
	local vector v;
	local vector v1;
	local vector v2;
	local vector org;
	local float foedist;

	if ((!self.enemy || bm_wasfreed(self.enemy)))
	{
		self.enemy = world;
		return;
	}
	if ((self.enemy.health <= 0))
	{
		self.enemy = world;
		return;
	}
	if ((!self.enemy.takedamage || (self.enemy.flags & FL_NOTARGET)))
	{
		self.enemy = world;
		return;
	}
	if (!fisible(self.enemy))
	{
		self.enemy = world;
		return;
	}
	org = realorigin(self.enemy);
	makevectors(self.v_angle);
	foedist = vlen((org - self.origin));
	v = weapon_range(self.weapon);
	if (((foedist >= v_y) && (foedist <= v_z)))
	{
		traceline((self.origin + self.view_ofs), ((self.origin + self.view_ofs) + (v_forward * v_z)), FALSE, self);
		if (((vlen((trace_endpos - (self.origin + self.view_ofs))) >= v_y) || (trace_ent == self.enemy)))
		{
			if ((trace_ent.classname == "player"))
			{
				if (((((trace_ent.team == self.team) && (self.team > 0)) && (teamplay || CTF_ENABLED)) || coop))
				{
					return;
				}
			}
			bot_shoot();
		}
	}
	else
	{
		bot_weapon_switch(foedist);
		v = weapon_range(self.weapon);
		if (((foedist >= v_y) && (foedist <= v_z)))
		{
			bot_shoot();
		}
	}
	if (!(self.b_aiflags & 161))
	{
		if ((self.avoid && bm_wasfreed(self.avoid)))
		{
			self.avoid = world;
		}
		if (self.avoid)
		{
			if (!!self.avoid.velocity)
			{
				v = self.avoid.velocity;
			}
			else
			{
				v = normalize((self.avoid.origin - self.origin));
			}
			v1_x = v_y * -1;
			v1_y = v_x;
			v2_x = v_y;
			v2_y = v_x * -1;
			foedist = vlen((self.avoid.origin - (self.origin + v1)));
			if ((foedist < vlen((self.avoid.origin - (self.origin + v2)))))
			{
				frik_walkmove(v2);
			}
			else
			{
				frik_walkmove(v1);
			}
		}
		else if (!(self.enemy.flags & FL_MONSTER))
		{
			if ((random() < 0.04))
			{
				self.wallhug = !self.wallhug;
			}
			if (((foedist + 48) < v_x))
			{
				frik_walkmove(((self.origin - org) + (v_right * ((self.wallhug * 160) - 80))));
			}
			else if (((foedist - 64) > v_x))
			{
				frik_walkmove(((org - self.origin) + (v_right * ((self.wallhug * 180) - 90))));
			}
			else if (self.wallhug)
			{
				frik_walkmove((v_right + (v_forward * 0.35)));
			}
			else
			{
				frik_walkmove(((v_right * -1) + (v_forward * 0.35)));
			}
			if (((self.flags & FL_ONGROUND) && (random() < 0.06)))
			{
				bot_jump();
			}
		}
	}
};
