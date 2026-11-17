//Decompiled code. Please respect the original copyright.

void() entity_state_on =
{
	if (self.estate_on)
	{
		self.estate_on();
	}
	else
	{
		self.estate = ESTATE_ON;
	}
};

void() entity_state_off =
{
	if (self.estate_off)
	{
		self.estate_off();
	}
	else
	{
		self.estate = ESTATE_OFF;
	}
};

void() entity_state_disable =
{
	if (self.estate_disable)
	{
		self.estate_disable();
	}
	self.estate = ESTATE_DISABLE;
};

void() entity_state_reset =
{
	if (self.estate_reset)
	{
		self.estate_reset();
	}
};

void() entity_state_use =
{
	if (other.estate_trigger)
	{
		if ((other.estate_trigger & ESTATE_ON))
		{
			entity_state_on();
		}
		else
		{
			if ((other.estate_trigger & ESTATE_OFF))
			{
				entity_state_off();
			}
			else
			{
				if ((other.estate_trigger & ESTATE_DISABLE))
				{
					entity_state_disable();
				}
				else
				{
					if ((other.estate_trigger & ESTATE_RESET))
					{
						entity_state_reset();
					}
				}
			}
		}
	}
	else
	{
		if ((self.estate == ESTATE_DISABLE))
		{
			return;
		}
		if (self.estate_use)
		{
			self.estate_use();
		}
		else
		{
			if ((self.estate == ESTATE_OFF))
			{
				entity_state_on();
			}
			else
			{
				entity_state_off();
			}
		}
	}
};

void(string targstr) trigger_entitystate_target =
{
	local entity t;
	local entity stemp;
	local entity otemp;

	t = find(world, targetname, targstr);
	stemp = self;
	otemp = other;
	while (t)
	{
		if ((!(t.flags & FL_CLIENT) && !(t.flags & FL_MONSTER)))
		{
			if ((t.use != SUB_Null))
			{
				if (t.use)
				{
					self = t;
					other = stemp;
					entity_state_use();
					self = stemp;
					other = otemp;
				}
			}
		}
		t = find(t, targetname, targstr);
	}
};

void() trigger_entitystate_use =
{
	if ((self.target != ""))
	{
		trigger_entitystate_target(self.target);
	}
};

void() trigger_entitystate_off =
{
	self.classtype = CT_ESTATE;
	if (!self.target)
	{
		dprint("шентстатещ Missing target!\n");
	}
	if ((self.targetname != ""))
	{
		self.use = trigger_entitystate_use;
	}
	self.estate_trigger = ESTATE_OFF;
};

void() trigger_entitystate_on =
{
	self.classtype = CT_ESTATE;
	if (!self.target)
	{
		dprint("шентстатещ Missing target!\n");
	}
	if ((self.targetname != ""))
	{
		self.use = trigger_entitystate_use;
	}
	self.estate_trigger = ESTATE_ON;
};

void() trigger_entitystate_disable =
{
	self.classtype = CT_ESTATE;
	if (!self.target)
	{
		dprint("шентстатещ Missing target!\n");
	}
	if ((self.targetname != ""))
	{
		self.use = trigger_entitystate_use;
	}
	self.estate_trigger = ESTATE_DISABLE;
};

void() trigger_entitystate_reset =
{
	self.classtype = CT_ESTATE;
	if (!self.target)
	{
		dprint("шентстатещ Missing target!\n");
	}
	if ((self.targetname != ""))
	{
		self.use = trigger_entitystate_use;
	}
	self.estate_trigger = ESTATE_RESET;
};
