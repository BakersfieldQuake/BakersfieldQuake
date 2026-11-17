//Decompiled code. Please respect the original copyright.

void() DropHook =
{
	local entity linkptr;
	local entity nextptr;

	self.owner.hook = 0;
	linkptr = self;
	while ((linkptr != world))
	{
		nextptr = linkptr.goalentity;
		remove(linkptr);
		linkptr = nextptr;
	}
	sound7(self.owner, CHAN_AUTO, "hook/retract.wav", 1, ATTN_NORM, SNDSPD);
	self.owner.swing = 0;
};

void() MaintainLinks =
{
	local vector chainvec;
	local vector chainunit;
	local float chainlen;
	local entity newlink;
	local entity currlink;
	local entity nextlink;
	local float currpos;
	local float linknum;
	local float linkstart;
	local vector p_self_origin;

	currpos = vlen(self.velocity) / 22;
	p_self_origin = self.origin + (normalize(self.velocity) * currpos);
	chainvec = (self.owner.origin + '0 0 16') - p_self_origin;
	chainunit = normalize(chainvec);
	chainvec = chainvec - (chainunit * 18);
	chainlen = vlen(chainvec);
	currlink = self;
	currpos = 0;
	linknum = ceil((chainlen / CHAIN_LINK_LEN));
	while ((currpos < linknum))
	{
		if ((currlink.goalentity == world))
		{
			newlink = spawn();
			newlink.movetype = MOVETYPE_NOCLIP;
			newlink.solid = 0;
			setmodel(newlink, "progs/chain.mdl");
			setsize(newlink, VEC_ORIGIN, VEC_ORIGIN);
			newlink.goalentity = world;
			currlink.goalentity = newlink;
		}
		currlink = currlink.goalentity;
		currpos = currpos + 1;
		currlink.angles = vectoangles(chainvec);
		if (((currlink.angles_y > 0) && (currlink.angles_y < 180)))
		{
			currlink.angles = (currlink.angles + '0 1 0');
		}
		currlink.angles_z = (currlink.angles_z + (crandom() * 8));
		linkstart = (currpos - 1) * CHAIN_LINK_LEN;
		if ((currpos < linknum))
		{
			setorigin(currlink, (p_self_origin + (chainunit * (linkstart + 27.5))));
			currlink.frame = 9;
		}
		else
		{
			setorigin(currlink, (p_self_origin + (chainunit * (linkstart + ((chainlen - linkstart) / 2)))));
			currlink.frame = floor((((chainlen - linkstart) / CHAIN_LINK_LEN) * 10));
		}
	}
	nextlink = currlink.goalentity;
	currlink.goalentity = world;
	currlink = nextlink;
	while ((currlink != world))
	{
		nextlink = currlink.goalentity;
		remove(currlink);
		currlink = nextlink;
	}
};

void() HookBehavior =
{
	local vector chainvec;
	local vector velpart;
	local float chainlen;
	local float framestep;
	local float f1;
	local float f2;

	if (((((!(self.owner.hook & HOOK_ON) || (self.owner.teleport_time > time)) || (self.owner.view_ofs == VEC_ORIGIN)) || self.owner.deadflag) || (self.enemy.solid == SOLID_NOT)))
	{
		DropHook();
		return;
	}
	self.velocity = self.enemy.velocity;
	if (((self.owner.hook & GROW_ON) && (self.armorvalue < MAX_CHAIN_LEN)))
	{
		if (((time - self.ltime) > 0.1))
		{
			self.ltime = (time - 0.1);
		}
		framestep = (10 * (time - self.ltime)) * GROW_SHRINK_RATE;
		self.armorvalue = (self.armorvalue + framestep);
		if ((self.armorvalue > MAX_CHAIN_LEN))
		{
			self.armorvalue = MAX_CHAIN_LEN;
		}
		self.ltime = time;
		if (((time - self.delay) >= 0.1))
		{
			sound7(self.owner, CHAN_AUTO, "hook/chain1.wav", 0.8, ATTN_NORM, SNDSPD);
			self.delay = time;
		}
	}
	if (((self.owner.hook & SHRINK_ON) && (self.armorvalue > MIN_CHAIN_LEN)))
	{
		if (((time - self.ltime) > 0.1))
		{
			self.ltime = (time - 0.1);
		}
		framestep = (10 * (time - self.ltime)) * GROW_SHRINK_RATE;
		self.armorvalue = (self.armorvalue - framestep);
		if ((self.armorvalue < MIN_CHAIN_LEN))
		{
			self.armorvalue = MIN_CHAIN_LEN;
		}
		self.ltime = time;
		if (((time - self.delay) >= 0.1))
		{
			sound7(self.owner, CHAN_AUTO, "hook/chain2.wav", 0.8, ATTN_NORM, SNDSPD);
			self.delay = time;
		}
	}
	chainvec = self.origin - (self.owner.origin + '0 0 16');
	chainlen = vlen(chainvec);
	if ((chainlen > self.armorvalue))
	{
		velpart = chainvec * ((self.owner.velocity * chainvec) / (chainvec * chainvec));
		f2 = (chainlen - self.armorvalue) * 5;
		if (((self.owner.velocity * chainvec) < 0))
		{
			if ((chainlen > (self.armorvalue + 25)))
			{
				self.owner.velocity = (self.owner.velocity - velpart);
			}
			f1 = f2;
		}
		else
		{
			if ((vlen(velpart) < f2))
			{
				f1 = f2 - vlen(velpart);
			}
			else
			{
				f1 = 0;
			}
		}
	}
	else
	{
		f1 = 0;
	}
	self.owner.velocity = (self.owner.velocity + (normalize(chainvec) * f1));
	if ((self.owner.velocity_z > (cvar("sv_gravity") / 20)))
	{
		self.owner.flags = (self.owner.flags - (self.owner.flags & FL_ONGROUND));
	}
	MaintainLinks();
	self.nextthink = (time + 0.01);
};

void() HookTouch =
{
	local vector spray;

	self.armorvalue = vlen((self.origin - (self.owner.origin + '0 0 16')));
	if ((!(self.owner.hook & HOOK_ON) || (pointcontents(self.origin) == CONTENT_SKY)))
	{
		DropHook();
		return;
	}
	self.owner.hook = (self.owner.hook | HOOK_IN);
	if (other.takedamage)
	{
		T_Damage(other, self, self.owner, 10);
	}
	if ((other.solid == SOLID_SLIDEBOX))
	{
		sound7(self, CHAN_AUTO, "shambler/smack.wav", 1, ATTN_NORM, SNDSPD);
		spray_x = 40 * crandom();
		SpawnBlood(self.origin, spray, 10);
		spray_x = 80 * crandom();
		SpawnBlood(self.origin, spray, 10);
		spray_x = 120 * crandom();
		SpawnBlood(self.origin, spray, 10);
		other.velocity = (other.velocity + (normalize(self.velocity) * 300));
		DropHook();
	}
	else
	{
		sound7(self, CHAN_AUTO, "player/axhit2.wav", 1, ATTN_NORM, SNDSPD);
		self.avelocity = VEC_ORIGIN;
	}
	self.velocity = other.velocity;
	self.enemy = other;
	self.think = HookBehavior;
	self.nextthink = (time + 0.01);
	self.touch = SUB_Null;
};

void() LaunchHook =
{
	local float chainlen;

	chainlen = vlen((self.origin - (self.owner.origin + '0 0 16')));
	if ((!(self.owner.hook & HOOK_ON) || (chainlen > MAX_CHAIN_LEN)))
	{
		DropHook();
		return;
	}
	if (((time - self.delay) >= 0.25))
	{
		sound7(self.owner, CHAN_AUTO, "hook/chain1.wav", 0.8, ATTN_NORM, SNDSPD);
		self.delay = time;
	}
	MaintainLinks();
	self.nextthink = (time + 0.02);
};

void(entity myself) InitiateHook =
{
	local entity newhook;

	newhook = spawn();
	newhook.owner = myself;
	newhook.movetype = MOVETYPE_FLY;
	newhook.solid = SOLID_BBOX;
	setmodel(newhook, "progs/hook.mdl");
	setsize(newhook, VEC_ORIGIN, VEC_ORIGIN);
	makevectors(myself.v_angle);
	setorigin(newhook, ((myself.origin + (v_forward * 16)) + '0 0 16'));
	newhook.velocity = (v_forward * 1000);
	newhook.angles = vectoangles(v_forward);
	newhook.avelocity = '0 0 600';
	sound7(myself, CHAN_AUTO, "hook/launch.wav", 1, ATTN_NORM, SNDSPD);
	sound7(myself, CHAN_AUTO, "hook/chain1.wav", 0.8, ATTN_NORM, SNDSPD);
	newhook.goalentity = world;
	newhook.ltime = time;
	newhook.delay = time;
	newhook.touch = HookTouch;
	newhook.nextthink = (time + 0.01);
	newhook.think = LaunchHook;
};

void() CheckGrapHook =
{
	if ((!(self.hook & HOOK_ON) && (self.impulse == I_HOOK)))
	{
		self.hook = HOOK_ON;
		self.swing = 1;
		InitiateHook(self);
		return;
	}
	if ((self.hook & HOOK_ON))
	{
		if ((self.impulse == I_HOOK))
		{
			self.hook = (self.hook - (self.hook & HOOK_ON));
			self.swing = 0;
			return;
		}
		if (((((self.button2 && (self.flags & FL_JUMPRELEASED)) && (self.hook & HOOK_IN)) && !(self.flags & FL_ONGROUND)) && !(self.flags & FL_INWATER)))
		{
			self.hook = (self.hook - (self.hook & HOOK_ON));
			self.velocity_z = (self.velocity_z + 200);
			sound7(self, CHAN_BODY, "player/plyrjmp8.wav", 1, ATTN_NORM, SNDSPD);
			self.swing = 0;
			return;
		}
		if ((self.impulse == I_STOP))
		{
			self.hook = (self.hook - (self.hook & 12));
			return;
		}
		if ((autocvar_mp_grapple == 2))
		{
			if ((self.impulse == I_GROW))
			{
				self.hook = (self.hook | GROW_ON);
				self.hook = (self.hook - (self.hook & SHRINK_ON));
				return;
			}
			if ((self.impulse == I_SHRINK))
			{
				self.hook = (self.hook | SHRINK_ON);
				self.hook = (self.hook - (self.hook & GROW_ON));
			}
		}
	}
};
