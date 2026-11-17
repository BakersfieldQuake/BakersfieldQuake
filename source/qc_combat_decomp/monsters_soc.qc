//Decompiled code. Please respect the original copyright.

void(entity attacker, float damage) monster_pain_check =
{
	self.pain_check = 0;
	if ((self.health < 1))
	{
		self.pain_check = 0;
	}
	else
	{
		if (((self.watertype == CONTENT_SLIME) || (self.watertype == CONTENT_LAVA)))
		{
			self.pain_check = 1;
		}
		else
		{
			if ((attacker == world))
			{
				self.pain_check = 1;
			}
			else
			{
				if (((random() * self.pain_flinch) > damage))
				{
					self.pain_check = 3;
				}
				else
				{
					self.pain_check = 1;
				}
			}
		}
	}
};

void() monster_idle_sound =
{
	if (!(self.flags & FL_MONSTER))
	{
		return;
	}
	if ((self.health < 1))
	{
		return;
	}
	if ((self.idletimer > time))
	{
		return;
	}
	if ((self.spawnflags & MON_SPAWN_NOIDLE))
	{
		return;
	}
	self.idletimer = ((time + 5) + (random() * 3));
	if ((!self.idlemoreoften && (random() > MON_IDLE_SOUND)))
	{
		return;
	}
	if ((self.enemy && (self.idle_soundcom != "")))
	{
		if ((self.idle_soundcom2 != ""))
		{
			if ((random() < 0.5))
			{
				sound(self, CHAN_VOICE, self.idle_soundcom, 1, ATTN_NORM);
			}
			else
			{
				sound(self, CHAN_VOICE, self.idle_soundcom2, 1, ATTN_NORM);
			}
		}
		else
		{
			sound(self, CHAN_VOICE, self.idle_soundcom, 1, ATTN_NORM);
		}
	}
	else
	{
		if ((self.idle_sound2 != ""))
		{
			if ((random() < 0.5))
			{
				sound(self, CHAN_VOICE, self.idle_sound, 1, ATTN_NORM);
			}
			else
			{
				sound(self, CHAN_VOICE, self.idle_sound2, 1, ATTN_NORM);
			}
		}
		else
		{
			sound(self, CHAN_VOICE, self.idle_sound, 1, ATTN_NORM);
		}
	}
};

void(float wakeupothers) FoundHuntTarget =
{
	if ((self.health < 1))
	{
		return;
	}
	if (!self.enemy)
	{
		return;
	}
	if (((self.enemy.flags & FL_CLIENT) && (wakeupothers == TRUE)))
	{
		sight_entity = self;
		sight_entity_time = time;
	}
	self.show_hostile = (time + 1);
	self.oldorigin = self.origin;
	self.goalentity = self.enemy;
	self.ideal_yaw = vectoyaw((self.enemy.origin - self.origin));
	SUB_AttackFinished(1);
};

entity() SUB_entEnemyTarget =
{
	if (!self.enemy)
	{
		return (world);
	}
	if ((self.enemy.classtype == CT_ENEMYTARGET))
	{
		return (self.enemy.enemy);
	}
	else
	{
		return (self.enemy);
	}
};

vector() SUB_orgEnemyTarget =
{
	if (!self.enemy)
	{
		return (VEC_ORIGIN);
	}
	if ((self.enemy.classtype == CT_ENEMYTARGET))
	{
		return (self.enemy.enemy.origin);
	}
	else
	{
		return (self.enemy.origin);
	}
};

float(float attackdist) ai_checkmelee =
{
	local vector spot1;
	local vector spot2;
	local float delta;
	local float zdiff;

	spot1 = SUB_orgEnemyTarget();
	spot2 = self.origin;
	zdiff = fabs((0 - 0));
	delta = vlen((spot1 - spot2));
	if (((delta < attackdist) && (zdiff < MONAI_MELEEZAXIS)))
	{
		return (TRUE);
	}
	else
	{
		return (0);
	}
};
