//Decompiled code. Please respect the original copyright.

void() trap_tracking =
{
	if ((self.target == ""))
	{
		return;
	}
	if (!self.movetarget)
	{
		self.movetarget = find(world, targetname, self.target);
	}
	if (self.movetarget)
	{
		if (self.movetarget.bsporigin)
		{
			self.dest1 = bmodel_origin(self.movetarget);
		}
		else
		{
			self.dest1 = self.movetarget.origin;
		}
		self.movedir = normalize((self.dest1 - self.origin));
	}
};

void() trap_gasshooter_touch =
{
	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((other.health < 1))
	{
		return;
	}
	if ((other.takedamage == DAMAGE_NO))
	{
		return;
	}
	if ((self.attack_finished > time))
	{
		return;
	}
	if ((other.classtype == self.owner.classtype))
	{
		return;
	}
	self.attack_finished = (time + 1);
	if ((other.flags & FL_CLIENT))
	{
		if ((self.owner.spawnflags & TRAP_GASFIRE))
		{
			ApplyFireDmg(other, self.owner.dmg, self.owner.dmg);
		}
		else
		{
			if ((self.owner.spawnflags & TRAP_GASPOISON))
			{
				ApplyFireDmg(other, self.owner.dmg, self.owner.dmg);
			}
			else
			{
				T_Damage(other, self, self, self.owner.dmg, NOARMOR);
			}
		}
	}
	else
	{
		if ((other.flags & FL_MONSTER))
		{
			T_Damage(other, self, self, DAMAGE_MONFLAME, NOARMOR);
		}
		else
		{
			T_Damage(other, self, self, self.owner.dmg, NOARMOR);
		}
	}
	self.velocity = VEC_ORIGIN;
};

void() trap_gasshooter_think =
{
	self.cnt = (self.cnt + 1);
	if ((self.cnt > 6))
	{
		remove(self);
	}
	else
	{
		self.frame = self.cnt;
		self.nextthink = ((time + 0.1) + (random() * 0.05));
	}
};

void() trap_gasshooter_spawn =
{
	local entity partemit;

	if ((self.estate & ESTATE_BLOCK))
	{
		self.state = STATE_OFF;
	}
	if ((self.state == STATE_OFF))
	{
		return;
	}
	if ((self.spawnflags & TRAP_TRACKING))
	{
		trap_tracking();
	}
	partemit = spawn();
	partemit.classtype = CT_TEMPSTREAM;
	partemit.owner = self;
	partemit.cnt = 0;
	partemit.frame = 0;
	partemit.movetype = MOVETYPE_FLY;
	partemit.solid = SOLID_TRIGGER;
	setmodel(partemit, self.mdl);
	setorigin(partemit, self.origin);
	setsize(partemit, VEC_ORIGIN, VEC_ORIGIN);
	partemit.oldorigin = vecrand(0, 20, TRUE);
	partemit.velocity = ((self.movedir * self.speed) + partemit.oldorigin);
	partemit.angles_z = (random() * 360);
	if ((engine == ENG_DPEXT))
	{
		partemit.effects = (partemit.effects + EF_NOSHADOW);
	}
	partemit.nextthink = ((time + 0.1) + (random() * 0.05));
	partemit.think = trap_gasshooter_think;
	partemit.touch = trap_gasshooter_touch;
	if (((self.spawnflags & TRAP_TOGGLE) || (self.waitmin2 > time)))
	{
		self.think = trap_gasshooter_spawn;
		self.nextthink = (time + self.wait);
	}
	else
	{
		self.state = STATE_OFF;
		sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
	}
};

void() trap_gasshooter_off =
{
	self.estate = ESTATE_OFF;
	if ((self.state == STATE_ON))
	{
		sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
	}
	else
	{
		sound(self, CHAN_VOICE, SOUND_EMPTY, 1, ATTN_NORM);
	}
	self.state = STATE_OFF;
};

void() trap_gasshooter_reset =
{
	self.estate = ESTATE_ON;
	sound(self, CHAN_VOICE, SOUND_EMPTY, 1, ATTN_NORM);
	self.state = STATE_OFF;
};

void() trap_gasshooter_on =
{
	self.estate = ESTATE_ON;
	self.state = STATE_ON;
	sound(self, CHAN_VOICE, self.noise1, 1, ATTN_NORM);
	self.waitmin2 = (time + self.waitmin);
	trap_gasshooter_spawn();
};

void() trap_gasshooter_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.state == STATE_ON))
	{
		self.state = STATE_OFF;
		sound(self, CHAN_VOICE, self.noise2, 1, ATTN_NORM);
	}
	else
	{
		trap_gasshooter_on();
	}
};

void() trap_gasshooter =
{
	if ((self.spawnflags & TRAP_GASFIRE))
	{
		self.mdl = "progs/s_flame.spr";
		self.noise1 = "traps/flame_loop.wav";
		self.noise2 = "traps/flame_off.wav";
	}
	else
	{
		if ((self.spawnflags & TRAP_GASPOISON))
		{
			self.mdl = "progs/s_poison.spr";
			self.noise1 = "traps/steam_loop.wav";
			self.noise2 = "traps/steam_off.wav";
			self.alpha = 1;
		}
		else
		{
			self.spawnflags = (self.spawnflags | TRAP_GASSTEAM);
			self.mdl = "progs/s_steam.spr";
			self.noise1 = "traps/steam_loop.wav";
			self.noise2 = "traps/steam_off.wav";
		}
	}
	if ((self.spawnflags & TRAP_GASSILENT))
	{
		self.noise1 = SOUND_EMPTY;
		self.noise2 = SOUND_EMPTY;
	}
	precache_model(self.mdl);
	precache_sound(self.noise1);
	precache_sound(self.noise2);
	self.classtype = CT_GASSHOOTER;
	self.solid = 0;
	self.movetype = 0;
	if (!self.dmg)
	{
		self.dmg = 1;
	}
	if ((self.speed < 1))
	{
		self.speed = 200;
	}
	if ((self.wait < 0.05))
	{
		self.wait = 0.05;
	}
	if ((self.waitmin <= 0))
	{
		self.waitmin = 0.5;
	}
	if ((self.spawnflags & TRAP_TOGGLE))
	{
		self.waitmin = LARGE_TIMER;
	}
	if ((self.angles_y == 0))
	{
		self.angles_y = 360;
	}
	self.mangle = self.angles;
	SetMovedir();
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = trap_gasshooter_use;
	self.estate_reset = trap_gasshooter_reset;
	self.estate_off = trap_gasshooter_off;
	self.estate_on = trap_gasshooter_on;
	self.estate = ESTATE_ON;
	self.state = STATE_OFF;
	if ((self.target != ""))
	{
		self.nextthink = ((time + 1) + random());
		self.think = trap_tracking;
	}
};

void() trap_shooter_fire =
{
	local vector lightn_start;
	local vector lightn_finish;

	if ((self.estate & ESTATE_BLOCK))
	{
		self.state = STATE_OFF;
	}
	if ((self.state == STATE_OFF))
	{
		return;
	}
	if ((self.spawnflags & TRAP_TRACKING))
	{
		trap_tracking();
	}
	if ((self.classname == "trap_lightningshooter"))
	{
		if ((self.t_width < time))
		{
			sound(self, CHAN_VOICE, self.noise, self.volume, ATTN_NORM);
			self.t_width = (time + 0.6);
		}
	}
	else
	{
		if ((self.noise != ""))
		{
			sound(self, CHAN_VOICE, self.noise, self.volume, ATTN_NORM);
		}
	}
	if ((self.classname == "trap_lightningshooter"))
	{
		if (CheckZeroVector(self.dest1))
		{
			return;
		}
		self.effects = (self.effects | EF_MUZZLEFLASH);
		lightn_finish = VEC_ORIGIN;
		lightn_start = VEC_ORIGIN;
		if ((CheckZeroVector(self.pos1) == FALSE))
		{
			lightn_start_x = self.pos1_x * crandom();
		}
		lightn_start = lightn_start + self.origin;
		if ((CheckZeroVector(self.pos2) == FALSE))
		{
			lightn_finish_x = self.pos2_x * crandom();
		}
		lightn_finish = lightn_finish + self.dest1;
		traceline(lightn_start, lightn_finish, TRUE, self);
		if (((self.spawnflags & TRAP_LIGHTDUST) && (random() < 0.7)))
		{
			newmis = spawn();
			newmis.classgroup = CG_TEMPENT;
			newmis.movetype = MOVETYPE_TOSS;
			newmis.solid = 0;
			setmodel(newmis, "progs/proj_smoke.mdl");
			setorigin(newmis, trace_endpos);
			setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
			self.pos3 = normalize((lightn_finish - lightn_start));
			self.pos3 = vectoangles(self.pos3);
			makevectors(self.pos3);
			newmis.velocity = (((crandom() * v_right) * 150) + (v_forward * (150 + (random() * 300))));
			newmis.nextthink = ((time + 1) + (random() * 3));
			newmis.think = SUB_Remove;
		}
		if ((self.spawnflags & TRAP_LIGHTPART))
		{
			particle_explode(trace_endpos, (5 + (random() * 5)), 1, PARTICLE_BURST_BLUE, PARTICLE_BURST_LOSTUP);
		}
		WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
		WriteByte(MSG_BROADCAST, self.lip);
		WriteEntity(MSG_BROADCAST, self);
		WriteCoord(MSG_BROADCAST, lightn_start_x);
		WriteCoord(MSG_BROADCAST, (self.pos1_y * crandom()));
		WriteCoord(MSG_BROADCAST, (self.pos1_z * crandom()));
		WriteCoord(MSG_BROADCAST, trace_endpos_x);
		WriteCoord(MSG_BROADCAST, 0);
		WriteCoord(MSG_BROADCAST, 0);
		LightningDamage(lightn_start, trace_endpos, self, self.dmg);
	}
	if (((self.waitmin > 0) && (time < self.pausetime)))
	{
		self.think = trap_shooter_fire;
		self.nextthink = (time + self.waitmin2);
	}
	else
	{
		if ((self.spawnflags & TRAP_TOGGLE))
		{
			self.think = trap_shooter_fire;
			self.nextthink = ((time + self.wait) + (random() * self.delay));
		}
		else
		{
			self.state = STATE_OFF;
		}
	}
};

void() trap_shooter_use =
{
	if ((self.estate & ESTATE_BLOCK))
	{
		return;
	}
	if ((self.state == STATE_OFF))
	{
		self.state = STATE_ON;
		if ((self.waitmin > 0))
		{
			self.pausetime = (time + self.waitmin);
		}
		if (!self.waitmin2)
		{
			self.waitmin2 = 0.1;
		}
	}
	else
	{
		self.state = STATE_OFF;
	}
	trap_shooter_fire();
};

void() trap_shooter_reset =
{
	self.estate = ESTATE_ON;
	self.state = STATE_OFF;
};

void() trap_lightningshooter =
{
	self.noise = "weapons/lhit.wav";
	precache_sound(self.noise);
	if ((self.wait <= 0))
	{
		self.wait = 1;
	}
	if ((self.delay < 0))
	{
		self.delay = 0;
	}
	if (!self.volume)
	{
		self.volume = 0.75;
	}
	self.t_width = 0;
	if ((self.dmg < 1))
	{
		self.dmg = 15;
		if ((self.spawnflags & TRAP_LIGHTLARGE))
		{
			self.dmg = 30;
		}
	}
	if ((self.spawnflags & TRAP_LIGHTLARGE))
	{
		self.lip = TE_LIGHTNING3;
	}
	else
	{
		self.lip = TE_LIGHTNING2;
	}
	if ((self.target == ""))
	{
		dprint("ÛÔÒÁÐÝ Lightning trap missing target!\n");
		spawn_marker(self.origin, SPNMARK_YELLOW);
		remove(self);
		return;
	}
	if ((self.targetname != ""))
	{
		self.use = entity_state_use;
	}
	self.estate_use = trap_shooter_use;
	self.estate_reset = trap_shooter_reset;
	self.estate = ESTATE_ON;
	self.state = STATE_OFF;
	self.nextthink = ((time + 1) + random());
	self.think = trap_tracking;
};

void() trap_tesla_scan =
{
	local entity head;
	local entity prev;

	tesla_numtargets = 0;
	head = findradius(self.origin, self.distance);
	while (head)
	{
		if ((!(head.flags & FL_NOTARGET) && (head.flags & self.cnt)))
		{
			visible(head);
			if ((visible(head) && (head.health > 0)))
			{
				if ((tesla_numtargets == 0))
				{
					tesla_target = head;
				}
				else
				{
					prev.next_ent = head;
				}
				tesla_numtargets = tesla_numtargets + 1;
				prev = head;
				if ((tesla_numtargets == self.count))
				{
					return;
				}
			}
		}
		head = head.chain;
	}
};

void() trap_gravity_touch =
{
	if ((self.attack_finished > time))
	{
		return;
	}
	if (other.takedamage)
	{
		T_Damage(other, self, self, self.dmg);
		self.attack_finished = (time + 0.2);
	}
};

void() trap_gravity_think =
{
	local vector vel;
	local vector dir;
	local vector delta;

	self.ltime = time;
	trap_tesla_scan();
	while ((tesla_numtargets > 0))
	{
		delta = self.origin - tesla_target.origin;
		dir = normalize(delta);
		vel = dir * self.speed;
		if (((tesla_target.wetsuit_finished > time) && (self.waterlevel >= 2)))
		{
			vel = vel * 0.6;
		}
		tesla_target.velocity = (tesla_target.velocity + vel);
		tesla_target = tesla_target.next_ent;
		tesla_numtargets = tesla_numtargets - 1;
	}
	self.nextthink = (time + 0.1);
};

void() trap_gravity_well =
{
	self.solid = SOLID_TRIGGER;
	self.movetype = 0;
	setsize(self, '-16 -16 -16', '16 16 16');
	if ((self.dmg == 0))
	{
		self.dmg = 10000;
	}
	if ((self.speed == 0))
	{
		self.speed = 210;
	}
	if ((self.distance == 0))
	{
		self.distance = 600;
	}
	if ((self.spawnflags & 1))
	{
		self.cnt = 40;
	}
	else
	{
		self.cnt = FL_CLIENT;
	}
	self.attack_finished = 0;
	self.think = trap_gravity_think;
	self.touch = trap_gravity_touch;
	self.lastvictim = world;
	tesla_numtargets = 0;
	self.nextthink = (time + 0.1);
	self.ltime = time;
};
