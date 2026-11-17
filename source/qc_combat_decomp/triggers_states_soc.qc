//Decompiled code. Please respect the original copyright.

void() trigger_bmodel_sounds =
{
	if ((self.sounds == 1))
	{
		self.noise = "misc/secret.wav";
	}
	else
	{
		if ((self.sounds == 2))
		{
			self.noise = SOUND_TALK;
		}
		else
		{
			if ((self.sounds == 3))
			{
				self.noise = "misc/trigger1.wav";
			}
			else
			{
				if ((self.sounds == 4))
				{
					self.noise = SOUND_EMPTY;
				}
				else
				{
					if ((self.sounds == 6))
					{
						self.noise = "misc/secret3.wav";
					}
				}
			}
		}
	}
	if ((self.noise != ""))
	{
		precache_sound(self.noise);
	}
};

void() trigger_bmodel_inview =
{
	local entity client;
	local entity tself;
	local float play_dist;
	local float play_range;
	local float play_angle;

	if ((self.attack_finished > time))
	{
		return;
	}
	if (!self.attachment)
	{
		self.attachment = spawn();
		self.attachment.owner = self;
		self.oldorigin = bmodel_origin(self);
		setorigin(self.attachment, self.oldorigin);
	}
	tself = self;
	self = self.attachment;
	client = checkclient();
	self = tself;
	if ((client.flags & FL_CLIENT))
	{
		if (visxray(client, VEC_ORIGIN, VEC_ORIGIN, FALSE))
		{
			play_dist = vlen((self.oldorigin - client.origin));
			if (!self.t_length)
			{
				play_range = play_dist + 1;
			}
			else
			{
				play_range = self.t_length;
			}
			play_angle = viewangle(self.oldorigin, client.origin, 45, TRUE, client.v_angle_y);
			if ((((play_dist < play_range) && (play_angle > 30)) && (play_angle < 60)))
			{
				self.wait = -1;
				self.bmodel_act = activator;
				self.estate_fire();
				return;
			}
		}
	}
	self.nextthink = (time + 0.1);
	self.think = trigger_bmodel_inview;
};

void() trigger_bmodel_fire =
{
	if ((self.attack_finished > time))
	{
		return;
	}
	if ((self.classtype == CT_TRIGSECRET))
	{
		if (!(self.bmodel_act.flags & FL_CLIENT))
		{
			return;
		}
		if ((self.count > 0))
		{
			found_secrets = found_secrets + self.count;
			WriteByte(MSG_ALL, SVC_FOUNDSECRET);
			self.count = 0;
		}
	}
	if ((self.noise != ""))
	{
		sound(self, CHAN_VOICE, self.noise, 1, ATTN_NORM);
	}
	activator = self.bmodel_act;
	SUB_UseTargets();
	if ((self.wait > 0))
	{
		self.attack_finished = (time + self.wait);
		self.nextthink = self.attack_finished;
		self.think = self.estate_on;
	}
	else
	{
		self.attack_finished = LARGE_TIMER;
		self.estate_off();
	}
};

void() trigger_bmodel_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.bmodel_act = activator;
	self.estate_fire();
};

void() trigger_bmodel_touch =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((!(self.spawnflags & TRIG_MONSTERS) && !(other.flags & FL_CLIENT)))
	{
		return;
	}
	if ((CheckZeroVector(self.movedir) == FALSE))
	{
		makevectors(other.angles);
		if (((v_forward * self.movedir) < 0))
		{
			return;
		}
	}
	self.bmodel_act = other;
	self.estate_fire();
};

void() trigger_bmodel_anytouch =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.bmodel_act = other;
	self.estate_fire();
};

void() trigger_bmodel_killed =
{
	self.health = self.max_health;
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	self.takedamage = 0;
	self.bmodel_act = damage_attacker;
	self.estate_fire();
};

void() trigger_bmodel_restore =
{
	if (((self.max_health > 0) && !(self.spawnflags & TRIG_NODAMAGE)))
	{
		self.health = self.max_health;
		self.takedamage = DAMAGE_YES;
		self.solid = SOLID_BBOX;
	}
	else
	{
		if ((!(self.spawnflags & TRIG_NOTOUCH) || (self.spawnflags & TRIG_ALWAYTOUCH)))
		{
			self.solid = SOLID_TRIGGER;
		}
		else
		{
			self.solid = 0;
		}
	}
	setsize(self, self.bbmins, self.bbmaxs);
	if ((skill == 3))
	{
		return;
	}
	if (coop)
	{
		return;
	}
};

void() trigger_bmodel_delay =
{
	if ((self.estate == ESTATE_DISABLE))
	{
		return;
	}
	self.spawnflags = (self.spawnflags - (self.spawnflags & ENT_STARTOFF));
	self.estate_use = trigger_bmodel_use;
	self.attack_finished = 0;
	self.estate = ESTATE_ON;
	if (((self.classtype == CT_TRIGONCE) && (self.spawnflags & TRIG_INVIEW)))
	{
		setsize(self, self.bbmins, self.bbmaxs);
		self.spawnflags = ((self.spawnflags | TRIG_NOTOUCH) | TRIG_NODAMAGE);
		self.estate_use = trigger_bmodel_inview;
		self.estate_use();
		return;
	}
	if ((self.health && !(self.spawnflags & TRIG_NODAMAGE)))
	{
		self.max_health = self.health;
		self.th_die = trigger_bmodel_killed;
	}
	else
	{
		if ((!(self.spawnflags & TRIG_NOTOUCH) || (self.spawnflags & TRIG_ALWAYTOUCH)))
		{
			if (!self.touch)
			{
				self.touch = trigger_bmodel_touch;
			}
		}
	}
	trigger_bmodel_restore();
};

void() trigger_bmodel_on =
{
	self.estate = ESTATE_ON;
	self.movetype = 0;
	if (((self.spawnflags & ENT_STARTOFF) || (self.attack_finished > time)))
	{
		self.solid = 0;
	}
	else
	{
		trigger_bmodel_restore();
	}
};

void() trigger_bmodel_off =
{
	self.estate = ESTATE_OFF;
	self.movetype = 0;
	self.solid = 0;
	setsize(self, VEC_ORIGIN, VEC_ORIGIN);
	self.estate_disable();
};

void() trigger_bmodel_reset =
{
	self.attack_finished = 0;
	self.estate_on();
};

void() trigger_bmodel_disable =
{
	self.takedamage = 0;
	self.think = SUB_Null;
};

void() trigger_bmodel_default =
{
	self.estate_on = trigger_bmodel_on;
	self.estate_off = trigger_bmodel_off;
	if (!self.estate_fire)
	{
		self.estate_fire = trigger_bmodel_fire;
	}
	self.estate_disable = trigger_bmodel_disable;
	self.estate_reset = trigger_bmodel_reset;
	self.estate = ESTATE_ON;
};

void() trigger_bmodel_setup =
{
	trigger_bmodel_default();
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = trigger_bmodel_delay;
	if ((self.spawnflags & ENT_STARTOFF))
	{
		self.estate_use = trigger_bmodel_delay;
		self.estate_on = trigger_bmodel_delay;
		self.estate_off();
	}
	else
	{
		self.estate_use();
	}
};
