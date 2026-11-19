//Decompiled code. Please respect the original copyright.

void(float eftype) sparkler =
{
	local entity new;

	new = spawn();
	new.origin = (self.origin + '0 0 10');
	new.origin_x = (new.origin_x + ((random() * 10) + -5));
	new.origin_y = (new.origin_y + ((random() * 10) + -5));
	new.origin = (new.origin + ((VEC_ORIGIN - v_forward) * 40));
	new.movetype = MOVETYPE_TOSS;
	new.solid = 0;
	new.velocity_x = ((random() * 600) + -300);
	new.velocity_y = ((random() * 600) + -300);
	new.velocity_z = ((random() * 400) + 300);
	if ((eftype == 2))
	{
		new.gravity = 1.1;
	}
	else
	{
		new.gravity = 0.7;
	}
	if ((coop || deathmatch))
	{
		new.effects = EF_LOWPRECISION | EF_NOSHADOW;
	}
	else
	{
		new.effects = EF_NOSHADOW;
	}
	setmodel(new, "progs/misc_spark.mdl");
	setsize(new, VEC_ORIGIN, VEC_ORIGIN);
	new.think = SUB_Remove;
	new.alpha = 0.01;
	if ((eftype == 2))
	{
		new.velocity_x = ((random() * 360) + -180);
		new.velocity_y = ((random() * 360) + -180);
		new.velocity_z = ((random() * 300) + 200);
		new.nextthink = (time + ((random() * 0.45) + 0.55));
	}
	else
	{
		if ((eftype == 1))
		{
			new.velocity_x = ((random() * 360) + -180);
			new.velocity_y = ((random() * 360) + -180);
			new.velocity_z = ((random() * 20) + 200);
			new.nextthink = (time + ((random() * 0.4) + 0.45));
		}
		else
		{
			new.nextthink = (time + ((random() * 0.4) + 0.4));
		}
	}
	if ((eftype == 1))
	{
		new.traileffectnum = particleeffectnum(/*24377i*/"smoke_trail");
	}
	else
	{
		if ((eftype == 2))
		{
			new.traileffectnum = particleeffectnum(/*24389i*/"fire_trail");
		}
		else
		{
			new.traileffectnum = particleeffectnum(/*24400i*/"sparkler");
		}
	}
	if ((pointcontents(new.origin) == CONTENT_SOLID))
	{
		remove(new);
	}
};

void(float eftype) sparklers =
{
	if ((autocvar_effects_sparkballs == 1))
	{
		if ((random() > 0.45))
		{
			sparkler(eftype);
		}
	}
};

void() muzzle_think =
{
	self.ltime = (self.ltime + 1);
	if ((self.ltime == 1))
	{
		self.delay = (time + 0.05);	// gone ~0.06 s after the spawn (+0.01 first think): by time, so the think rate can't stretch it
	}
	if (((self.model == "progs/shot_muzz.spr") || (self.model == "progs/shot_muzz_b.spr")))
	{
		self.scale = (self.scale + 0.05);
	}
	else
	{
		self.scale = (self.scale + 0.2);
	}
	self.think = muzzle_think;
	self.nextthink = (time + 0.015);
	if ((time >= self.delay))
	{
		remove(self);
	}
};

void() muzzle_small_think =
{
	self.ltime = (self.ltime + 1);
	self.think = muzzle_small_think;
	if ((self.model == "progs/s_explodmed.spr"))
	{
		if ((self.frame <= 13))
		{
			self.alpha = (self.alpha - 0.09);
			self.frame = (self.frame + 1);
		}
		if ((self.ltime > 14))
		{
			remove(self);
		}
		self.scale = (self.scale + 0.03);
		self.nextthink = (time + 0.07);
	}
	else
	{
		if ((self.ltime == 1))
		{
			self.delay = (time + 0.05);	// by time, not think count (see muzzle_think)
		}
		self.nextthink = (time + 0.015);
		if ((((self.model == "progs/sng_muzz.spr") || (self.model == "progs/sng_muzz_b.spr")) || (self.model == "progs/shot_muzz_b.spr")))
		{
			self.scale = (self.scale + 0.04);
			self.alpha = (self.alpha - 0.05);
		}
		else
		{
			self.scale = (self.scale + 0.1);
		}
		if ((time >= self.delay))
		{
			remove(self);
		}
	}
};

void() SpawnMuzzleFlash =
{
	if ((self.ishuman != 1))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	if ((self.waterlevel >= 3))
	{
		setmodel(newmis, "progs/s_smoke_muzz.spr");
	}
	else
	{
		if (((random() * 100) < 50))
		{
			setmodel(newmis, "progs/shot_muzz.spr");
		}
		else
		{
			if (((random() * 100) < 50))
			{
				setmodel(newmis, "progs/muzzleflash3.spr");
			}
			else
			{
				setmodel(newmis, "progs/muzzleflash.spr");
			}
		}
	}
	newmis.scale = 0.8;
	newmis.alpha = 1;
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, '104 -16 -18');
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 16 0');
	}
	newmis.think = muzzle_think;
	newmis.nextthink = (time + 0.01);
};

void() SpawnSSGFlash =
{
	if ((self.ishuman != 1))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	newmis.alpha = 1;
	if (!self.cnt)
	{
		self.cnt = (self.cnt + 1);
	}
	else
	{
		self.cnt = 0;
	}
	if ((self.waterlevel >= 3))
	{
		setmodel(newmis, "progs/s_smoke_muzz.spr");
	}
	else
	{
		if (self.cnt)
		{
			setmodel(newmis, "progs/shot_muzz_b.spr");
		}
		else
		{
			setmodel(newmis, "progs/shot_muzz.spr");
		}
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.scale = 1;
	setorigin(newmis, '108 -26 -34');
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 26 0');
	}
	newmis.think = muzzle_think;
	newmis.nextthink = (time + 0.01);
};

void(vector offset) SpawnNailgunFlash =
{
	if (((self.ishuman != 1) || (self.waterlevel >= 3)))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	setmodel(newmis, "progs/muzzleflash2.spr");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, ('104 -24 -43' + offset));
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 24 0');
	}
	newmis.think = muzzle_think;
	newmis.nextthink = (time + 0.01);
};

void(vector offset, vector color) SpawnSNGFlash =
{
	if (((self.ishuman != 1) || (self.waterlevel >= 3)))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	if ((self.cnt < 2))
	{
		self.cnt = (self.cnt + 1);
	}
	else
	{
		self.cnt = 0;
	}
	newmis.colormod = color;
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	if (!self.cnt)
	{
		setmodel(newmis, "progs/sng_muzz_b.spr");
	}
	else
	{
		if ((self.cnt == 1))
		{
			setmodel(newmis, "progs/sng_muzz.spr");
		}
		else
		{
			setmodel(newmis, "progs/shot_muzz_b.spr");
		}
	}
	newmis.scale = 0.65;
	newmis.alpha = 0.9;
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, ('104 -26 -25' + offset));
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 26 0');
	}
	newmis.think = muzzle_small_think;
	newmis.nextthink = (time + 0.01);
};

void() SpawnHLFlash =
{
	if ((self.ishuman != 1))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	setmodel(newmis, "progs/muzzleflash1.spr");
	newmis.scale = 0.6;
	newmis.alpha = 0.3;
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, '104 -26 -24');
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 26 0');
	}
	newmis.think = muzzle_think;
	newmis.nextthink = (time + 0.01);
};

void(vector offset, vector color) SpawnRockFlash =
{
	if (((self.ishuman != 1) || (self.waterlevel >= 3)))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = 0;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = EF_NOSHADOW;
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.colormod = color;
	newmis.alpha = 1;
	newmis.velocity_z = 20;
	setmodel(newmis, "progs/s_explodmed.spr");
	newmis.scale = 0.45;
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, ('74 7 -69' + offset));
	newmis.think = muzzle_small_think;
	newmis.nextthink = (time + 0.01);
};

void() muzzle_smoke_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.05);
	self.scale = (self.scale - 0.05);
	self.velocity_z = (self.velocity_z + 16);
	self.think = muzzle_smoke_think;
	self.nextthink = (time + 0.08);
	if ((self.ltime > 11))
	{
		remove(self);
	}
};

void() muzzle_smoke_nail_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.06);
	self.scale = (self.scale + 0.2);
	self.velocity_z = (self.velocity_z + 16);
	self.think = muzzle_smoke_think;
	self.nextthink = (time + 0.08);
	if ((self.ltime > 11))
	{
		remove(self);
	}
};

void() muzzle_spark_think =
{
	self.frame = (self.frame + 1);
	self.ltime = (self.ltime + 1);
	self.alpha = (self.alpha - 0.03);
	self.scale = (self.scale - 0.02);
	self.velocity_z = (self.velocity_z + -16);
	self.velocity_x = (self.velocity_x + -15);
	self.think = muzzle_spark_think;
	self.nextthink = (time + 0.03);
	if ((self.ltime > 9))
	{
		remove(self);
	}
};

void(float spscale, vector offset, float smokedir, vector color, float spritealpha) SpawnSmoke_Flash =
{
	if ((self.ishuman != 1))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = EF_NOSHADOW;
	setmodel(newmis, "progs/s_smoke_muzz.spr");
	newmis.scale = spscale;
	newmis.scale = (newmis.scale + ((random() * 0.2) + -0.1));
	newmis.alpha = spritealpha;
	newmis.colormod = color;
	if (smokedir)
	{
		newmis.velocity = '60 0 0';
	}
	else
	{
		newmis.velocity = '60 0 -40';
	}
	if (((self.weapon == IT_SUPER_NAILGUN) || (self.weapon == IT_GRENADE_LAUNCHER)))
	{
		newmis.velocity_y = (newmis.velocity_y + ((random() * 100) + -50));
		newmis.velocity_z = (newmis.velocity_z + ((random() * 40) + -20));
	}
	else
	{
		newmis.velocity_x = (newmis.velocity_x + ((random() * 10) + -25));
		newmis.velocity_y = (newmis.velocity_y + ((random() * 36) + -18));
		newmis.velocity_z = (newmis.velocity_z + ((random() * 20) + -10));
	}
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, '114 -37 -29');
	newmis.origin = (newmis.origin + offset);
	if (autocvar_centered_weapons)
	{
		newmis.origin = (newmis.origin + '0 33 -10');
	}
	if (!smokedir)
	{
		newmis.think = muzzle_smoke_think;
	}
	else
	{
		newmis.think = muzzle_smoke_nail_think;
	}
	newmis.nextthink = (time + 0.01);
};

void(float spscale, vector offset, vector color, float spritealpha) SpawnSpark_Flash =
{
	if ((self.ishuman != 1))
	{
		return;
	}
	newmis = spawn();
	newmis.movetype = MOVETYPE_NOCLIP;
	newmis.solid = 0;
	newmis.viewmodelforclient = self;
	newmis.owner = self;
	newmis.classname = "flash";
	newmis.effects = (newmis.effects + EF_ADDITIVE + EF_NOSHADOW);
	setmodel(newmis, "progs/s_spark_muzz.spr");
	if (!spritealpha)
	{
		newmis.alpha = 1;
	}
	else
	{
		newmis.alpha = spritealpha;
	}
	newmis.scale = spscale;
	newmis.velocity = '420 0 -5';
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, '74 7 -69');
	if (!color)
	{
		newmis.colormod = '1 1 1';
	}
	else
	{
		newmis.colormod = color;
	}
	newmis.origin = (newmis.origin + offset);
	if ((autocvar_centered_weapons && (self.weapon != IT_LASER_CANNON)))
	{
		newmis.origin = (newmis.origin + '0 15 0');
	}
	newmis.think = muzzle_spark_think;
	newmis.nextthink = (time + 0.01);
};
