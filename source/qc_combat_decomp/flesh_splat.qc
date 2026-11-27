//Decompiled code. Please respect the original copyright.

void() flesh_remove1 = [ 0, flesh_remove2 ]
{
	self.scale = 0.7;
};

void() flesh_remove2 = [ 0, flesh_remove3 ]
{
	self.scale = 0.6;
};

void() flesh_remove3 = [ 0, flesh_remove4 ]
{
	self.scale = 0.5;
};

void() flesh_remove4 = [ 0, flesh_remove5 ]
{
	self.scale = 0.4;
};

void() flesh_remove5 = [ 0, flesh_remove6 ]
{
	self.scale = 0.2;
};

void() flesh_remove6 = [ 0, flesh_remove7 ]
{
	self.scale = 0.1;
};

void() flesh_remove7 = [ 0, flesh_remove7 ]
{
	remove(self);
};

void() SplatThink =
{
	if (((self.attack_finished <= time) || (self.flags & FL_ONGROUND)))
	{
		flesh_remove1();
		return;
	}
	if ((self.model == "progs/gib_splat.mdl"))
	{
		self.traileffectnum = particleeffectnum(/*24244i*/"gibtr");
	}
	self.velocity_z = (random() * -10);
	if ((self.model != "progs/gib_splat.mdl"))
	{
		self.angles = vectoangles(self.velocity);
	}
	else
	{
		self.angles_z = 0;
	}
	self.solid = SOLID_TRIGGER;
	self.nextthink = (time + 10.2);
};

void() DripThink =
{
	if (((self.attack_finished <= time) || (self.flags & FL_ONGROUND)))
	{
		remove(self);
		return;
	}
	self.angles = vectoangles(self.velocity);
	self.solid = SOLID_TRIGGER;
	self.nextthink = (time + 10.2);
	self.ONCEIL = 0;
};

void() SplatTouch =
{

	if (((((other != world) || (pointcontents(self.origin) <= -3)) || (self.flags & FL_ONGROUND)) || (pointcontents(self.origin) == CONTENT_SKY)))
	{
		remove(self);
		return;
	}
	self.avelocity = VEC_ORIGIN;
	self.velocity = VEC_ORIGIN;
	self.movetype = MOVETYPE_FLY;
	self.touch = SUB_Null;
	self.attack_finished = ((time + 4) + (2 * random()));
	pointparticles(particleeffectnum(/*15292i*/"hldecal"), self.origin, VEC_ORIGIN, 2);
	if ((self.ONCEIL == 0))
	{
		self.traileffectnum = particleeffectnum(/*24250i*/"gibd");
		self.think = SplatThink;
	}
	else
	{
		self.traileffectnum = particleeffectnum(/*24255i*/"gibceil");
		self.think = DripThink;
	}
	self.nextthink = (time + 0.2);
};

void(vector dir, vector org, entity own) ThrowBloodSplat =
{
	local entity splat;

	if (((trace_ent.classname == "ShalrathMissile") || (trace_ent.classname == "monster_jim")))
	{
		return;
	}
	if (!((own.flags & FL_MONSTER) || (own.classname == "player")))
	{
		return;
	}
	splat = spawn();
	splat.owner = own;
	splat.movetype = MOVETYPE_TOSS;
	splat.solid = SOLID_BBOX;
	splat.effects = EF_LOWPRECISION;
	if (self.ONCEIL)
	{
		splat.velocity = dir;
	}
	else
	{
		dir = normalize(dir);
		splat.velocity = (dir * (1050 + (50 * random())));
		splat.velocity_x = (splat.velocity_x + (crandom() * 40));
		splat.velocity_y = (splat.velocity_y + (crandom() * 40));
		splat.velocity_z = ((splat.velocity_z + 120) + (50 * random()));
		splat.avelocity = '3000 1000 2000';
	}
	splat.touch = SplatTouch;
	splat.nextthink = (time + 2);
	splat.think = SUB_Remove;
	if (((self.ONCEIL == 0) && (random() < 0.25)))
	{
		setmodel(splat, "progs/gib_splat.mdl");
		if ((random() < 0.35))
		{
			splat.scale = 0.8;
		}
	}
	else
	{
		setmodel(splat, "progs/wallsplat.mdl");
		splat.alpha = 0.1;
	}
	splat.traileffectnum = particleeffectnum("TR_BLOOD");
	splat.alpha = 1;
	setsize(splat, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(splat, org);
};

void() cs_touch =
{
	local float surfacenum;
	local string tex;

	if ((other != world))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if (world_has_q1_surfs)
	{
		surfacenum = getsurfacenearpoint(world, self.origin);
		if ((surfacenum >= 0))
		{
			tex = getsurfacetexture(world, surfacenum);
			if (((((tex == "sky1") || (tex == "sky4")) || (tex == "sky_base")) || (tex == "sky_curse1")))
			{
				remove(self);
				return;
			}
		}
	}
	sendParticle("hldecal", self.origin, '0 0 100', 2);
	self.netname = "gibsplat";
	self.movetype = 0;
	self.spawnflags = MISC_DRIPBLOOD;
	BLD = BLD + 1;
	self.think = misc_drip;
	self.nextthink = time;
};

void() CeilSplat =
{
	local entity dripper;
	local vector throwdir;

	throwdir_x = crandom() * 240;
	throwdir_y = crandom() * 240;
	throwdir_z = 480 + (random() * 340);
	dripper = spawn();
	setorigin(dripper, self.origin + '0 0 12');
	setsize(dripper, VEC_ORIGIN, VEC_ORIGIN);
	if (((random() * 100) < 50))
	{
		dripper.wait = 0.1;
	}
	else
	{
		dripper.wait = 0.4;
	}
	dripper.gravity = 0.3;
	dripper.velocity = throwdir;
	dripper.movetype = MOVETYPE_FLY;
	dripper.solid = SOLID_TRIGGER;
	dripper.touch = cs_touch;
	dripper.traileffectnum = particleeffectnum("TR_BLOOD");
	dripper.think = SUB_Remove;
	dripper.nextthink = (time + 2.5);
};
