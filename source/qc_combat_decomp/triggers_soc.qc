//Decompiled code. Please respect the original copyright.

void() trigger_ladder_fire =
{
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.touch = trigger_ladder_fire;
	}
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if (!(other.flags & FL_CLIENT))
	{
		return;
	}
	if ((other.health < 1))
	{
		return;
	}
	if ((other.waterlevel > 1))
	{
		return;
	}
	if ((other.flags & FL_WATERJUMP))
	{
		return;
	}
	other.onladder = 1;
	other.entladder = self;
	if ((other.flags & FL_ONGROUND))
	{
		other.flags = (other.flags - FL_ONGROUND);
	}
};

void() trigger_ladder =
{
	if (!self.sounds)
	{
		self.sounds = 2;
	}
	if ((self.sounds == 1))
	{
		if (!self.waitmin)
		{
			self.waitmin = 0.45;
		}
		self.noise1 = "player/ladmetal1.wav";
		self.noise2 = "player/ladmetal2.wav";
		self.noise3 = "player/ladmetal3.wav";
		self.noise4 = "player/ladmetal4.wav";
	}
	else
	{
		if ((self.sounds == 2))
		{
			if (!self.waitmin)
			{
				self.waitmin = 0.4;
			}
			self.noise1 = "player/ladwood1.wav";
			self.noise2 = "player/ladwood2.wav";
			self.noise3 = "player/ladwood3.wav";
			self.noise4 = "player/ladwood4.wav";
		}
		else
		{
			if ((self.sounds == 3))
			{
				if (!self.waitmin)
				{
					self.waitmin = 0.7;
				}
				self.noise1 = "player/ladrope1.wav";
				self.noise2 = "player/ladrope2.wav";
				self.noise3 = "player/ladrope3.wav";
				self.noise4 = "player/ladrope4.wav";
			}
			else
			{
				if (!self.waitmin)
				{
					self.waitmin = 0.5;
				}
				if ((self.noise1 == ""))
				{
					self.noise1 = SOUND_EMPTY;
				}
				if ((self.noise2 == ""))
				{
					self.noise2 = SOUND_EMPTY;
				}
				if ((self.noise3 == ""))
				{
					self.noise3 = SOUND_EMPTY;
				}
				if ((self.noise4 == ""))
				{
					self.noise4 = SOUND_EMPTY;
				}
			}
		}
	}
	precache_sound(self.noise1);
	precache_sound(self.noise2);
	precache_sound(self.noise3);
	precache_sound(self.noise4);
	self.classtype = CT_TRIGLADDER;
	InitTrigger();
	if (!self.speed)
	{
		self.speed = 160;
	}
	self.spawnflags = ((self.spawnflags | TRIG_ALWAYTOUCH) | TRIG_NODAMAGE);
	self.spawnflags = (self.spawnflags - (self.spawnflags & TRIG_MONSTERS));
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.touch = SUB_Null;
		self.use = trigger_ladder_fire;
	}
	else
	{
		self.touch = trigger_ladder_fire;
	}
};

void() gravity_touch =
{
	local float grav;

	grav = self.gravity;
	if ((other.classname == "player"))
	{
		cvar_set("sv_gravity", ftos(grav));
	}
};

void() trigger_setgravity =
{
	InitTrigger();
	if (!self.gravity)
	{
		self.gravity = 800;
	}
	self.touch = gravity_touch;
};

void() removeItems =
{
	if ((other.classname == "player"))
	{
		other.weapon = IT_AXE;
	}
};

void() trigger_weaponstrip =
{
	InitTrigger();
	self.touch = removeItems;
};

void() removeEnts =
{
	if ((other == world))
	{
		return;
	}
	if ((other.flags & FL_CLIENT))
	{
		return;
	}
	if ((other.flags & FL_MONSTER))
	{
		return;
	}
	remove(other);
};

void() trigger_removeEnts =
{
	InitTrigger();
	self.touch = removeEnts;
};
