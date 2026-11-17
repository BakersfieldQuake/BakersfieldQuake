//Decompiled code. Please respect the original copyright.

void() ambient_sound_setup =
{
	if ((self.volume > 1))
	{
		self.volume = 1;
	}
	if ((self.speed == -1))
	{
		ambientsound(self.origin, self.noise, self.volume, ATTN_NONE);
	}
	else
	{
		ambientsound(self.origin, self.noise, self.volume, ATTN_STATIC);
	}
};

void() ambient_custom_loop =
{
	if ((self.noise == ""))
	{
		dprint("шамбъцустомълоопщ Missing sound file\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		remove(self);
		return;
	}
	precache_sound(self.noise);
	if ((self.volume <= 0))
	{
		self.volume = 1;
	}
	ambient_sound_setup();
};

void() ambient_custom_stop =
{
	if ((self.state == STATE_OFF))
	{
		return;
	}
	self.state = STATE_OFF;
	self.think = SUB_Null;
	self.nextthink = (time + 0.1);
	if ((self.estate & ESTATE_DISABLE))
	{
		return;
	}
	if ((self.noise1 != ""))
	{
		sound(self, self.impulse, self.noise1, self.volume, self.speed);
	}
	else
	{
		if (!self.waitmin2)
		{
			sound(self, self.impulse, SOUND_EMPTY, self.volume, self.speed);
		}
	}
};

void() ambient_custom_play =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.state = STATE_ON;
	if (((self.noise2 != "") && (random() < 0.5)))
	{
		sound(self, self.impulse, self.noise2, self.volume, self.speed);
	}
	else
	{
		sound(self, self.impulse, self.noise, self.volume, self.speed);
	}
	if ((self.target != ""))
	{
		trigger_strs(self.target, self);
	}
	if ((self.spawnflags & SOUND_PLAYONCE))
	{
		self.estate = ESTATE_DISABLE;
	}
	else
	{
		self.nextthink = ((time + self.delay) + (random() * self.wait));
		self.think = ambient_custom_play;
	}
};

void() ambient_custom_use =
{
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.spawnflags = (self.spawnflags - ENT_STARTOFF);
		self.estate_on();
	}
	else
	{
		if ((self.estate & ESTATE_BLOCK))
		{
			return;
		}
		if ((self.state == STATE_OFF))
		{
			self.estate_on();
		}
		else
		{
			self.estate_off();
		}
	}
};

void() ambient_custom_on =
{
	self.estate = ESTATE_ON;
	ambient_custom_play();
};

void() ambient_custom_off =
{
	self.estate = ESTATE_OFF;
	ambient_custom_stop();
};

void() ambient_custom_disable =
{
	self.state = STATE_OFF;
	sound(self, self.impulse, SOUND_EMPTY, self.volume, self.speed);
};

void() ambient_custom_sound =
{
	if ((self.noise == ""))
	{
		dprint("шамбиентъсоундщ Missing sound file at ");
		dprint(vtos(self.origin));
		dprint("\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		remove(self);
		return;
	}
	precache_sound(self.noise);
	if ((self.noise1 != ""))
	{
		precache_sound(self.noise1);
	}
	if ((self.noise2 != ""))
	{
		precache_sound(self.noise2);
	}
	self.classtype = CT_SOUNDEMITTER;
	if (((self.volume <= 0) || (self.volume > 1)))
	{
		self.volume = 1;
	}
	if ((self.wait == 0))
	{
		self.wait = 20;
	}
	if ((self.wait < 0))
	{
		self.wait = 0;
	}
	if ((self.delay <= 0))
	{
		self.delay = 2;
	}
	if ((self.waitmin == 0))
	{
		self.waitmin = 4;
	}
	if ((self.impulse <= 0))
	{
		self.impulse = 1;
	}
	if ((self.speed < 0))
	{
		self.speed = 0;
	}
	else
	{
		if ((self.speed == 2))
		{
			self.speed = ATTN_IDLE;
		}
		else
		{
			if ((self.speed == 3))
			{
				self.speed = ATTN_STATIC;
			}
			else
			{
				if ((self.speed == 4))
				{
					self.speed = ATTN_QUIET;
				}
				else
				{
					self.speed = ATTN_NORM;
				}
			}
		}
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_on = ambient_custom_on;
	self.estate_off = ambient_custom_off;
	self.estate_use = ambient_custom_use;
	self.estate_disable = ambient_custom_disable;
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.estate_off();
	}
	else
	{
		if ((self.waitmin > 0))
		{
			self.nextthink = ((time + self.waitmin) + (random() * self.waitmin));
			self.think = self.estate_on;
		}
		else
		{
			self.estate_on();
		}
	}
};
