//Decompiled code. Please respect the original copyright.

float() AfritCheckAttack =
{
	local vector spot1;
	local vector spot2;
	local entity targ;
	local float chance;

	if ((time < self.attack_finished))
	{
		return (0);
	}
	if (!enemy_vis)
	{
		return (0);
	}
	if ((enemy_range == RANGE_FAR))
	{
		if ((self.th_run == afrit_side1))
		{
			if ((self.attack_state != AS_SLIDING))
			{
				self.attack_state = AS_SLIDING;
				afrit_side1();
			}
			if ((random() < 0.05))
			{
				self.th_run = afrit_run1;
			}
		}
		else
		{
			if ((self.attack_state != AS_STRAIGHT))
			{
				self.attack_state = AS_STRAIGHT;
				afrit_run1();
			}
		}
		return (0);
	}
	if ((skill == 3))
	{
		if (((random() < 0.925) && (enemy_range == RANGE_MID)))
		{
			return (0);
		}
		else
		{
			if (((random() < 0.85) && (enemy_range == RANGE_NEAR)))
			{
				return (0);
			}
		}
	}
	targ = self.enemy;
	spot1 = self.origin + self.view_ofs;
	spot2 = targ.origin + targ.view_ofs;
	traceline(spot1, spot2, FALSE, self);
	if ((trace_ent != targ))
	{
		if ((self.attack_state != AS_STRAIGHT))
		{
			self.attack_state = AS_STRAIGHT;
			afrit_run1();
		}
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		chance = 0.9;
	}
	else
	{
		if ((enemy_range == RANGE_NEAR))
		{
			chance = 0.6;
		}
		else
		{
			if ((enemy_range == RANGE_MID))
			{
				chance = 0.2;
			}
			else
			{
				chance = 0;
			}
		}
	}
	if ((random() < chance))
	{
		self.attack_state = AS_MISSILE;
		return (TRUE);
	}
	if ((enemy_range == RANGE_MID))
	{
		if ((self.attack_state != AS_STRAIGHT))
		{
			self.attack_state = AS_STRAIGHT;
			afrit_run1();
		}
	}
	else
	{
		if ((self.attack_state != AS_SLIDING))
		{
			self.attack_state = AS_SLIDING;
			afrit_side1();
		}
	}
	return (0);
};

void() AfritAttackFinished =
{
	if ((((enemy_range >= RANGE_MID) || !enemy_vis) && (random() < 0.8)))
	{
		self.attack_state = AS_STRAIGHT;
		self.think = afrit_run1;
	}
	else
	{
		traceline(self.origin, (self.origin - '50 50 0'), FALSE, self);
		if ((trace_fraction == 1))
		{
			traceline(self.origin, (self.origin + '50 50 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				self.attack_state = AS_SLIDING;
				self.think = afrit_side1;
			}
			else
			{
				self.attack_state = AS_STRAIGHT;
				self.think = afrit_run1;
			}
		}
		else
		{
			self.attack_state = AS_STRAIGHT;
			self.think = afrit_run1;
		}
	}
};

void() spike_afrit_touch =
{
	local float zufal;

	if ((other == self.owner))
	{
		return;
	}
	if ((other.solid == SOLID_TRIGGER))
	{
		return;
	}
	if ((pointcontents(self.origin) == CONTENT_SKY))
	{
		remove(self);
		return;
	}
	if (other.takedamage)
	{
		spawn_touchblood(autocvar_afrit_fireball_damage);
		T_Damage(other, self, self.owner, autocvar_afrit_fireball_damage);
		if (autocvar_afrit_projectiles_inflame_chance)
		{
			zufal = random() * 100;
			if ((zufal <= autocvar_afrit_projectiles_inflame_chance))
			{
				other.inflamed = 1;
				other.inflametime = (time + 10);
				other.inflamepause = (time + autocvar_fire_projectiles_and_lava_inflame_frequence);
				stuffcmd(self, "bf\n");
				if (autocvar_fire_projectiles_and_lava_inflame_particles)
				{
					sound7(other, CHAN_AUTO, "player/inflame.wav", 1, ATTN_NORM, SNDSPD);
					sound7(other, 120, "zombie/corpse_fire.wav", 1, ATTN_NORM, SNDSPD);
				}
			}
		}
	}
	else
	{
		if (self.owner.skin)
		{
			pointparticles(particleeffectnum(/*51990i*/"TE_AFRITSPIKE_GREY"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52009i*/"TE_AFRITSPIKE_RED"), self.origin, VEC_ORIGIN, 1);
			DN3FX_OnFire(self.origin, '0 0 22', 0.80, FALSE);
		}
		sound7(self, CHAN_WEAPON, "afrit/fireballtouch.wav", 0.6, ATTN_NORM, SNDSPD);
	}
	remove(self);
};

void(vector org, vector dir) launch_afrit_spike =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = spike_afrit_touch;
	newmis.think = SUB_Remove;
	newmis.nextthink = (time + 6);
	setmodel(newmis, "progs/k_spike.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(newmis, org);
	newmis.velocity = (dir * 1000);
};

void() Afrit_RapidFire =
{
	local vector vec;
	local vector dst;
	local vector follow;

	if ((self.owner.health > 0))
	{
		self.owner.effects = (self.owner.effects | EF_MUZZLEFLASH);
		makevectors(self.enemy.angles);
		follow = self.enemy.velocity * 0.35;
		dst = (self.enemy.origin + follow) - (13 * self.movedir);
		vec = normalize((dst - self.origin));
		sound7(self, CHAN_WEAPON, "afrit/attack.wav", 1, ATTN_NORM, SNDSPD);
		launch_afrit_spike(self.origin, vec);
		newmis.velocity = (vec * (450 + (skill * 25)));
		newmis.owner = self.owner;
		newmis.classname = "afritspike";
		setmodel(newmis, "progs/k_spike.mdl");
		if (self.owner.skin)
		{
			newmis.traileffectnum = particleeffectnum(/*52038i*/"TR_AFRITSPIKE_GREY");
		}
		else
		{
			newmis.traileffectnum = particleeffectnum(/*52057i*/"TR_AFRITSPIKE_RED");
		}
		setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	}
	remove(self);
};

void() Afrit_StartRapidFire =
{
	local entity missile;

	self.v_angle = self.angles;
	makevectors(self.angles);
	missile = spawn();
	missile.owner = self;
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, ((self.origin + '0 0 13') + (v_forward * 10)));
	missile.enemy = self.enemy;
	missile.nextthink = (time + 0.2);
	missile.think = Afrit_RapidFire;
	missile.movedir = VEC_ORIGIN;
	missile = spawn();
	missile.owner = self;
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, ((self.origin + '0 0 13') + (v_forward * 10)));
	missile.enemy = self.enemy;
	missile.nextthink = (time + 0.1);
	missile.think = Afrit_RapidFire;
	missile.movedir = VEC_ORIGIN;
	if (((self.flags == 0) && (random() < 0.4)))
	{
	}
	else
	{
		missile = spawn();
		missile.owner = self;
		setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
		setorigin(missile, ((self.origin + '0 0 13') + (v_forward * 10)));
		missile.enemy = self.enemy;
		missile.nextthink = (time + 0.001);
		missile.think = Afrit_RapidFire;
		missile.movedir = VEC_ORIGIN;
	}
};

void() afrit_stand1 = [ 23, afrit_stand2 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "afrit/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand2 = [ 24, afrit_stand3 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand3 = [ 25, afrit_stand4 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand4 = [ 26, afrit_stand5 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand5 = [ 27, afrit_stand6 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand6 = [ 28, afrit_stand7 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	sound7(self, CHAN_VOICE, "afrit/wingsflap.wav", 0.9, ATTN_IDLE, SNDSPD);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand7 = [ 29, afrit_stand8 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand8 = [ 30, afrit_stand9 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand9 = [ 31, afrit_stand10 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand10 = [ 32, afrit_stand11 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand11 = [ 33, afrit_stand12 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand12 = [ 34, afrit_stand13 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand13 = [ 35, afrit_stand14 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand14 = [ 36, afrit_stand15 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand15 = [ 37, afrit_stand16 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_stand16 = [ 38, afrit_stand1 ]
{
	ai_stand();
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52075i*/"Afrit_idle_grey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52091i*/"Afrit_idle_red"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_change_shape1 = [ 3, afrit_change_shape2 ]
{
	self.nextthink = (time + 0.1);
	sound7(self, CHAN_AUTO, "afrit/awake.wav", 1, ATTN_NORM, SNDSPD);
	self.takedamage = 0;
	self.th_pain = afrit_Pain;
};

void() afrit_change_shape2 = [ 4, afrit_change_shape3 ]
{
	self.nextthink = (time + 0.1);
};

void() afrit_change_shape3 = [ 5, afrit_change_shape4 ]
{
	self.nextthink = (time + 0.1);
};

void() afrit_change_shape4 = [ 6, afrit_change_shape5 ]
{
	self.nextthink = (time + 0.1);
};

void() afrit_change_shape5 = [ 7, afrit_change_shape6 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape6 = [ 8, afrit_change_shape7 ]
{
	self.nextthink = (time + 0.07);
	self.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
};

void() afrit_change_shape7 = [ 9, afrit_change_shape8 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape8 = [ 10, afrit_change_shape9 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape9 = [ 11, afrit_change_shape10 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape10 = [ 12, afrit_change_shape11 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape11 = [ 13, afrit_change_shape12 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape12 = [ 14, afrit_change_shape13 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape13 = [ 15, afrit_change_shape14 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape14 = [ 16, afrit_change_shape15 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape15 = [ 17, afrit_change_shape16 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape16 = [ 18, afrit_change_shape17 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape17 = [ 19, afrit_change_shape18 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape18 = [ 20, afrit_change_shape19 ]
{
	self.nextthink = (time + 0.07);
	self.takedamage = DAMAGE_AIM;
};

void() afrit_change_shape19 = [ 21, afrit_change_shape20 ]
{
	self.nextthink = (time + 0.07);
};

void() afrit_change_shape20 = [ 22, afrit_run1 ]
{
	self.nextthink = (time + 0.07);
	self.attack_finished = (time + 1);
	self.th_run = afrit_run1;
	self.th_stand = afrit_stand1;
	self.origin_z = (self.origin_z + 7);
};

void() afrit_use_cocoon1 = [ 0, afrit_use_cocoon2 ]
{
	ai_stand();
	self.nextthink = ((time + 0.1) + (random() * 0.35));
};

void() afrit_use_cocoon2 = [ 1, afrit_use_cocoon3 ]
{
	ai_stand();
	self.nextthink = ((time + 0.1) + (random() * 0.35));
};

void() afrit_use_cocoon3 = [ 2, afrit_use_cocoon1 ]
{
	ai_stand();
	self.nextthink = ((time + 0.1) + (random() * 0.4));
	self.th_run = afrit_change_shape1;
	self.th_pain = afrit_Pain_dummy;
	self.in_cocoon_shape = 1;
	if (self.skin)
	{
		self.traileffectnum = particleeffectnum(/*52106i*/"Afrit_cocoon_grey");
	}
	else
	{
		self.traileffectnum = particleeffectnum(/*52124i*/"Afrit_cocoon_red");
	}
};

void() afrit_stand_random =
{
	local float cocoonchance;

	cocoonchance = autocvar_afrit_waits_in_cocoon * 0.01;
	if ((random() < cocoonchance))
	{
		self.think = afrit_use_cocoon1;
	}
	else
	{
		self.think = afrit_stand1;
	}
	self.nextthink = (time + 0.4);
};

void() afrit_walk1 = [ 23, afrit_walk2 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "afrit/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk2 = [ 24, afrit_walk3 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk3 = [ 25, afrit_walk4 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk4 = [ 26, afrit_walk5 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk5 = [ 27, afrit_walk6 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk6 = [ 28, afrit_walk7 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	sound7(self, CHAN_VOICE, "afrit/wingsflap.wav", 0.9, ATTN_IDLE, SNDSPD);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk7 = [ 29, afrit_walk8 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk8 = [ 30, afrit_walk9 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk9 = [ 31, afrit_walk10 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk10 = [ 32, afrit_walk11 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk11 = [ 33, afrit_walk12 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk12 = [ 34, afrit_walk13 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk13 = [ 35, afrit_walk14 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk14 = [ 36, afrit_walk15 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk15 = [ 37, afrit_walk16 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_walk16 = [ 38, afrit_walk1 ]
{
	ai_walk(6);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side1 = [ 23, afrit_side2 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "afrit/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side2 = [ 24, afrit_side3 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side3 = [ 25, afrit_side4 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side4 = [ 26, afrit_side5 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side5 = [ 27, afrit_side6 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side6 = [ 28, afrit_side7 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	sound7(self, CHAN_VOICE, "afrit/wingsflap.wav", 0.9, ATTN_IDLE, SNDSPD);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side7 = [ 29, afrit_side8 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side8 = [ 30, afrit_side9 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side9 = [ 31, afrit_side10 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side10 = [ 32, afrit_side11 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side11 = [ 33, afrit_side12 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side12 = [ 34, afrit_side13 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side13 = [ 35, afrit_side14 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side14 = [ 36, afrit_side15 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side15 = [ 37, afrit_side16 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_side16 = [ 38, afrit_side1 ]
{
	ai_run(8);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run1 = [ 23, afrit_run2 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((random() < 0.2))
	{
		sound7(self, CHAN_VOICE, "afrit/idle.wav", 1, ATTN_IDLE, SNDSPD);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run2 = [ 24, afrit_run3 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run3 = [ 25, afrit_run4 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run4 = [ 26, afrit_run5 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run5 = [ 27, afrit_run6 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run6 = [ 28, afrit_run7 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	sound7(self, CHAN_VOICE, "afrit/wingsflap.wav", 0.9, ATTN_IDLE, SNDSPD);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run7 = [ 29, afrit_run8 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run8 = [ 30, afrit_run9 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run9 = [ 31, afrit_run10 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run10 = [ 32, afrit_run11 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run11 = [ 33, afrit_run12 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run12 = [ 34, afrit_run13 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run13 = [ 35, afrit_run14 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run14 = [ 36, afrit_run15 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run15 = [ 37, afrit_run16 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_run16 = [ 38, afrit_run1 ]
{
	ai_run(16);
	self.nextthink = (time + 0.07);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast1 = [ 48, afrit_fast2 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
	if (((random() < 0.4) || (self.health <= 0)))
	{
		if ((self.health <= 0))
		{
			self.flags = 0;
		}
		traceline(self.origin, (self.origin + '0 0 128'), FALSE, self);
		if ((trace_endpos == (self.origin + '0 0 128')))
		{
			self.flags = 0;
		}
	}
	self.velocity_z = 2;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast2 = [ 49, afrit_fast3 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
	self.velocity_z = 2;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast3 = [ 50, afrit_fast4 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
	self.velocity_z = 2;
	if ((self.health <= 0))
	{
		self.alpha = (self.alpha - 0.035);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast4 = [ 51, afrit_fast5 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
	self.velocity_z = 64;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast5 = [ 52, afrit_fast6 ]
{
	ai_face();
	self.nextthink = (time + 0.08);
	self.velocity_z = 128;
	if ((self.health <= 0))
	{
		self.alpha = (self.alpha - 0.035);
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast6 = [ 53, afrit_fast7 ]
{
	ai_face();
	self.nextthink = (time + 0.17);
	if ((self.health > 0))
	{
		Afrit_StartRapidFire();
	}
	self.velocity_z = 190;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast7 = [ 54, afrit_fast8 ]
{
	ai_face();
	self.nextthink = (time + 0.16);
	self.velocity_z = 260;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast8 = [ 55, afrit_fast9 ]
{

	ai_face();
	self.nextthink = (time + 0.13);
	self.velocity_z = 290;
	if (((self.health <= 0) && (self.attack_chance < 3)))
	{
		self.attack_chance = (self.attack_chance + 1);
		self.alpha = (self.alpha - 0.035);
		traceline(self.origin, (self.origin + '0 0 112'), FALSE, self);
		if ((pointcontents(trace_endpos) != CONTENT_SKY))
		{
			afrit_fast6();
		}
		else
		{
			self.alpha = -1;
			te_customflash(self.origin, 500, 0.7, '1 0 0');
			self.nextthink = (time + 0.2);
			self.think = SUB_Remove;
		}
	}
	else
	{
		if ((self.attack_chance >= 3))
		{
			self.alpha = -1;
			te_customflash(self.origin, 500, 0.7, '1 0 0');
			self.nextthink = (time + 0.2);
			self.think = SUB_Remove;
		}
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
	traceline(self.origin, (self.origin + '0 0 112'), FALSE, self);
	if (((trace_endpos == (self.origin + '0 0 112')) && (pointcontents(trace_endpos) != CONTENT_SKY)))
	{
		if (((random() < 0.5) && (self.flags == 0)))
		{
			afrit_fast6();
		}
	}
};

void() afrit_fast9 = [ 56, afrit_fast10 ]
{
	ai_face();
	self.velocity_z = 160;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast10 = [ 57, afrit_fast11 ]
{
	ai_face();
	self.velocity_z = 130;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast11 = [ 58, afrit_fast12 ]
{
	ai_face();
	self.velocity_z = 120;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast12 = [ 59, afrit_fast13 ]
{
	ai_face();
	self.velocity_z = 80;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_fast13 = [ 60, afrit_run1 ]
{
	ai_face();
	SUB_AttackFinished((1 + random()));
	AfritAttackFinished();
	self.velocity_z = 60;
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
	self.flags = (self.flags | FL_FLY);
	self.flags = (self.flags | FL_MONSTER);
};

void() afrit_paina1 = [ 39, afrit_paina2 ]
{
	ai_back(38);
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_paina2 = [ 40, afrit_paina3 ]
{
	ai_back(35);
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_paina3 = [ 41, afrit_paina4 ]
{
	ai_back(32);
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_paina4 = [ 42, afrit_paina5 ]
{
	ai_back(29);
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_paina5 = [ 43, afrit_paina6 ]
{
	ai_back(28);
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_paina6 = [ 44, afrit_run1 ]
{
	self.nextthink = (time + 0.12);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_painb1 = [ 45, afrit_painb2 ]
{
	ai_back(38);
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_painb2 = [ 46, afrit_painb3 ]
{
	ai_back(32);
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_painb3 = [ 47, afrit_run1 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void(entity attacker, float damage) afrit_Pain =
{
	self.in_cocoon_shape = 0;
	if ((self.pain_finished > time))
	{
		return;
	}
	if ((((random() * 60) > damage) && !self.enemy.meleeing))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_afrit * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	self.flags = (self.flags | FL_FLY);
	self.flags = (self.flags | FL_MONSTER);
	if ((random() > 0.27))
	{
		sound7(self, CHAN_AUTO, "afrit/pain1.wav", 1, ATTN_NORM, SNDSPD);
		afrit_paina1();
	}
	else
	{
		sound7(self, CHAN_AUTO, "afrit/pain2.wav", 1, ATTN_NORM, SNDSPD);
		afrit_painb1();
	}
};

void(entity attacker, float damage) afrit_Pain_dummy =
{
	self.in_cocoon_shape = 0;
	return;
};

void() afrit_deatha1 = [ 61, afrit_deatha2 ]
{
	self.nextthink = (time + 0.15);
	self.velocity_x = (-170 + (340 * random()));
	self.velocity_y = (-170 + (340 * random()));
	self.velocity_z = (75 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha2 = [ 62, afrit_deatha3 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha3 = [ 63, afrit_deatha4 ]
{
	self.solid = 0;
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha4 = [ 64, afrit_deatha5 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha5 = [ 64, afrit_deatha6 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha6 = [ 64, afrit_deatha7 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha7 = [ 64, afrit_deatha8 ]
{
	self.nextthink = (time + 0.15);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deatha8 = [ 64, afrit_deatha8 ]
{
	local float zufall;

	self.nextthink = (time + 0.15);
	if ((autocvar_afritcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_afritcorpsehealth, "progs/h_afrit.mdl");
	if ((self.grimrock_helper == 1))
	{
		if ((self.velocity != VEC_ORIGIN))
		{
			return;
		}
		zufall = random();
		if ((zufall > 0.825))
		{
			ghost_die();
		}
		else
		{
			if ((zufall < 0.15))
			{
				if ((zufall < 0.004))
				{
					soul("progs/afrit.mdl", 64, 27.451);
				}
				else
				{
					soul("progs/afrit.mdl", 64, 20);
				}
			}
			else
			{
				self.health = -40;
				vengeance_afrit("progs/h_afrit.mdl", 64);
			}
		}
	}
	else
	{
		if (((random() < 0.075) && (self.velocity == VEC_ORIGIN)))
		{
			self.health = -40;
			vengeance_afrit("progs/h_afrit.mdl", 64);
		}
	}
};

void() afrit_deathb1 = [ 61, afrit_deathb2 ]
{
	self.nextthink = (time + 0.1);
	self.velocity_x = (-170 + (340 * random()));
	self.velocity_y = (-170 + (340 * random()));
	self.velocity_z = (75 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deathb2 = [ 62, afrit_deathb3 ]
{
	self.nextthink = (time + 0.1);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deathb3 = [ 63, afrit_deathb4 ]
{
	self.solid = 0;
	self.nextthink = (time + 0.1);
	if ((self.afrit_on_fire == 1))
	{
		if (self.skin)
		{
			pointparticles(particleeffectnum(/*52141i*/"Afrit_flygrey"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			pointparticles(particleeffectnum(/*52155i*/"Afrit_flyred"), self.origin, VEC_ORIGIN, 1);
		}
	}
};

void() afrit_deathb4 = [ 64, afrit_deathb4 ]
{
	local vector v;
	local vector v2;

	self.nextthink = (time + 0.1);
	sound7(self, CHAN_AUTO, "afrit/body_explode.wav", 0.8, ATTN_NORM, SNDSPD);
	self.delete_painskin = 1;
	if (!self.skin)
	{
		pointparticles(particleeffectnum(/*13606i*/"Afrit_death_explode"), self.origin, VEC_ORIGIN, 1);
	}
	if (self.skin)
	{
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_gargwing2.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 1);
	}
	else
	{
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_gargwing2.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
		v = randompos(self.mins, self.maxs) + self.origin;
		v2 = randomvec() * 275;
		ThrowAfritGibs(v, v2, "progs/gib_afrit.mdl", 0);
	}
	v = randompos(self.mins, self.maxs) + self.origin;
	v2 = randomvec() * 275;
	ThrowHead("progs/h_afrit.mdl", self.health);
	return;
};

void() afrit_coal_touch =
{
	if ((self.flags & FL_ONGROUND))
	{
		self.solid = 0;
		baked_explode();
		return;
	}
	else
	{
		if ((self.velocity == VEC_ORIGIN))
		{
			self.solid = 0;
			baked_explode();
			return;
		}
	}
	self.think = afrit_coal_touch;
	self.nextthink = (time + 0.001);
};

void() afrit_lightning_death = [ 41, afrit_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		self.movetype = 0;
		self.velocity = VEC_ORIGIN;
		lightninggun_death_fade();
		return;
	}
	self.velocity_x = (-170 + (340 * random()));
	self.velocity_y = (-170 + (340 * random()));
	self.velocity_z = (100 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
};

void() afrit_lightning_death1 = [ 41, afrit_lightning_death1 ]
{
	self.touch = afrit_coal_touch;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
};

void() gib_afrit =
{
	sound7(self, CHAN_VOICE, "afrit/body_explode.wav", 1, ATTN_NORM, SNDSPD);
	self.delete_painskin = 1;
	ThrowGib("progs/gib_gargwing2.mdl", self.health);
	ThrowGib("progs/gib_gargwing2.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/chop.mdl", self.health);
	ThrowGib("progs/gib_afrit.mdl", self.health);
	ThrowGib("progs/gib_afrit.mdl", self.health);
	ThrowGib("progs/gib3.mdl", self.health);
	sendParticle("blood_monster_gib", self.origin, VEC_ORIGIN, 1, 0);
	ThrowHead("progs/h_afrit.mdl", self.health);
	return;
};

void() afrit_die =
{
	sound7(self, CHAN_WEAPON, SOUND_EMPTY, 1, ATTN_NORM);
	sound7(self, CHAN_VOICE, SOUND_EMPTY, 1, ATTN_NORM);
	sound7(self, CHAN_ITEM, SOUND_EMPTY, 1, ATTN_NORM);
	sound7(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	sound7(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	sound7(self, CHAN_AUTO, SOUND_EMPTY, 1, ATTN_NORM);
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			afrit_lightning_death();
			return;
		}
	}
	else
	{
		if (((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.sticky != 1)))
		{
			self.flags = (self.flags + FL_FLY);
			lg_death1();
			return;
		}
		else
		{
			if ((self.shocked > 0))
			{
				if ((self.flags & FL_FLY))
				{
					self.flags = (self.flags - FL_FLY);
				}
			}
		}
	}
	if ((random() < 0.8))
	{
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
	}
	if (((self.health < -40) || (random() < 0.1)))
	{
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		if ((self.enemy.weapon == IT_LASER_CANNON))
		{
			gibdeath_effects();
		}
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_afrit * 0.01)))
			{
				the_matrix = 1;
				SNDSPD = 70;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		gib_afrit();
		return;
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_afrit * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "afrit/death.wav", 1, ATTN_NORM, SNDSPD);
	afrit_deatha1();
};

void() monster_afrit =
{
	local float zufal;
	local float zufall;

	self.classname = "monster_afrit";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	setmodel(self, "progs/afrit.mdl");
	zufal = autocvar_afrit_multiskin * 0.01;
	if ((random() <= zufal))
	{
		self.skin = 1;
	}
	else
	{
		self.skin = 0;
	}
	self.monstermodel = 0;
	setsize(self, '-18 -18 -18', '18 18 20');
	if (!self.health)
	{
		self.health = autocvar_afrit_health;
	}
	if ((cvar("skill") == 3))
	{
		self.health = 130;
	}
	else
	{
		self.health = 110;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.scale = 1;
	self.th_stand = afrit_stand1;
	self.th_walk = afrit_walk1;
	if ((random() < 0.8))
	{
		self.th_run = afrit_side1;
	}
	else
	{
		self.th_run = afrit_run1;
	}
	self.th_missile = afrit_fast1;
	self.th_melee = SUB_Null;
	self.th_pain = afrit_Pain;
	self.th_die = afrit_die;
	zufall = autocvar_afrit_burning * 0.01;
	if ((random() <= zufall))
	{
		self.afrit_on_fire = 1;
	}
	self.alpha = (autocvar_monstertransparency * 0.01);
	flymonster_start();
	MonsterPhysics(self, autocvar_afritmass);
};

void() monster_minotaurminion =
{
	self.classname = "monster_afrit";
	monster_afrit();
};

void() monster_gargoyle =
{
	self.classname = "monster_afrit";
	monster_afrit();
};

void() monster_afrit_liftorigin =
{
	local float zufal;
	local float zufall;
	local entity pain_skin_entity;

	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((self.classname != "monster_wizard"))
	{
		self.origin_z = (self.origin_z + 16);
	}
	self.classname = "monster_afrit";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	setmodel(self, "progs/afrit.mdl");
	zufal = autocvar_afrit_multiskin * 0.01;
	if ((random() <= zufal))
	{
		self.skin = 1;
	}
	else
	{
		self.skin = 0;
	}
	self.monstermodel = 0;
	setsize(self, '-18 -18 -18', '18 18 20');
	if (!self.health)
	{
		self.health = autocvar_afrit_health;
	}
	if ((cvar("skill") == 3))
	{
		self.health = 130;
	}
	else
	{
		self.health = 110;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.scale = 1;
	self.th_stand = afrit_stand_random;
	self.th_walk = afrit_walk1;
	self.th_run = afrit_run1;
	self.th_missile = afrit_fast1;
	self.th_melee = SUB_Null;
	self.th_pain = afrit_Pain;
	self.th_die = afrit_die;
	zufall = autocvar_afrit_burning * 0.01;
	if ((random() <= zufall))
	{
		self.afrit_on_fire = 1;
	}
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, VEC_HULL2_MIN, VEC_HULL2_MAX);
		setorigin(pain_skin_entity, VEC_ORIGIN);
		pain_skin_entity.skin = self.skin;
		pain_skin_entity.colormod_x = self.colormod_x;
		pain_skin_entity.colormod_y = self.colormod_y;
		pain_skin_entity.colormod_z = self.colormod_z;
		pain_skin_entity.monstermodel = self.monstermodel;
		pain_skin_entity.frame = self.frame;
		pain_skin_entity.alpha = autocvar_painskin_transparency;
		pain_skin_entity.think = pain_skin_entity_think;
		pain_skin_entity.nextthink = time;
		setattachment(pain_skin_entity, self, /*37325i*/"test");
	}
	flymonster_start();
	MonsterPhysics(self, autocvar_afritmass);
};

void() monster_afrit_start =
{
	local entity clone;

	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_afrit;
	clone.nextthink = (time + 0.000100);
};

void() monster_afrit_liftorigin_start =
{
	local entity clone;

	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_afrit_liftorigin;
	clone.nextthink = (time + 0.000100);
};

void() add_afrit_support_fly =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		pos = ((self.origin + (((random() + 0.4) * 80) * v_forward)) + ((crandom() * 128) * v_right)) + (((random() + 0.3) * 128) * v_up);
		pos = pos + '0 0 40';
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					traceline(self.origin, (pos + '0 0 40'), FALSE, self);
					if ((trace_fraction == 1))
					{
						done = 1;
					}
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 10))
			{
				return;
			}
		}
	}
	if ((((((pointcontents(pos) == CONTENT_SOLID) || (pointcontents(pos) == CONTENT_SKY)) || (pointcontents(pos) == CONTENT_LAVA)) || (pointcontents(pos) == CONTENT_SLIME)) || (pointcontents(pos) == CONTENT_WATER)))
	{
		return;
	}
	if (PM_InWall(self, pos))
	{
		return;
	}
	clone = spawn();
	copyentity(self, clone);
	setorigin(clone, pos);
	clone.think = monster_afrit;
	clone.nextthink = (time + 0.000100);
};

void() add_afrit_support_walk =
{
	local entity clone;
	local entity head;
	local float done;
	local float c;
	local float proceed;
	local vector ang;
	local vector pos;

	done = 0;
	c = 0;
	ang = self.angles;
	while ((done == 0))
	{
		makevectors(ang);
		pos = ((self.origin + (48 * v_forward)) + ((crandom() * 48) * v_right)) + (((random() + 0.3) * 256) * v_up);
		head = findradius(pos, 35);
		proceed = 1;
		while (head)
		{
			if (((head.health > 0) && (head.flags & 40)))
			{
				proceed = 0;
			}
			head = head.chain;
		}
		traceline(self.origin, pos, FALSE, self);
		if (((trace_fraction == 1) && (proceed == 1)))
		{
			traceline(self.origin, (pos - '40 40 0'), FALSE, self);
			if ((trace_fraction == 1))
			{
				traceline(self.origin, (pos + '40 40 0'), FALSE, self);
				if ((trace_fraction == 1))
				{
					traceline(self.origin, (pos + '0 0 50'), FALSE, self);
					if ((trace_fraction == 1))
					{
						traceline(self.origin, (pos - '0 0 60'), FALSE, self);
						if ((trace_fraction == 1))
						{
							done = 1;
						}
					}
				}
			}
		}
		if ((done == 0))
		{
			c = c + 1;
			if ((c == 12))
			{
				return;
			}
		}
	}
	if (PM_InWall(self, pos))
	{
		return;
	}
	if ((((((pointcontents(pos) == CONTENT_SOLID) || (pointcontents(pos) == CONTENT_SKY)) || (pointcontents(pos) == CONTENT_LAVA)) || (pointcontents(pos) == CONTENT_SLIME)) || (pointcontents(pos) == CONTENT_WATER)))
	{
		return;
	}
	clone = spawn();
	copyentity(self, clone);
	setorigin(clone, pos);
	clone.think = monster_afrit;
	clone.nextthink = (time + 0.000100);
};

void() trap_flame_touch3 =
{
	ApplyFireDmg(other, 0.000100, 0.000100);
	self.touch = SUB_Null;
};

void() boss_trap_fin3 =
{
	local entity flame;

	flame = spawn();
	flame.owner = self;
	if ((self.has_fired == 0))
	{
		if ((((pointcontents(self.origin) == CONTENT_WATER) || (pointcontents(self.origin) == CONTENT_SOLID)) || (pointcontents(self.origin) == CONTENT_SLIME)))
		{
			remove(self);
		}
		self.alpha = 1;
		self.has_fired = 1;
		self.angles_y = ((random() * 720) + -360);
		pointparticles(particleeffectnum(/*12736i*/"lava_eruption_large"), self.origin, VEC_ORIGIN, 1);
	}
	setmodel(flame, "progs/s_flame.spr");
	setorigin(flame, (self.origin + '0 0 1'));
	setsize(flame, VEC_ORIGIN, '14 14 1');
	flame.velocity = '0 0 180';
	flame.alpha = -1;
	if ((random() < 0.01))
	{
		if ((random() < 0.7))
		{
			pointparticles(particleeffectnum(/*12681i*/"lava_eruption_medium"), self.origin, VEC_ORIGIN, 1);
			if ((random() < 0.8))
			{
				sound(self, CHAN_BODY, "ambience/rumblefade.wav", 1, ATTN_NORM);
			}
		}
		else
		{
			pointparticles(particleeffectnum(/*12628i*/"lava_eruption_small"), self.origin, VEC_ORIGIN, 1);
		}
	}
	flame.velocity_x = ((random() * 40) + -20);
	flame.velocity_y = ((random() * 40) + -20);
	flame.movetype = MOVETYPE_FLY;
	flame.solid = SOLID_TRIGGER;
	if ((random() < 0.85))
	{
		flame.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
	}
	flame.nextthink = ((time + 0.05) + (random() * 0.05));
	flame.think = trap_gasshooter_think;
	flame.touch = trap_flame_touch3;
	sound(self, CHAN_WEAPON, "traps/steam_loop.wav", 0.9, ATTN_STATIC);
	self.think = boss_trap_fin3;
	self.nextthink = (time + (0.3 - (random() * 0.1)));
};

void() afrit_deathc1 = [ 64, afrit_deathc2 ]
{
	self.nextthink = (time + 0.15);
};

void() afrit_deathc2 = [ 64, afrit_deathc3 ]
{
	self.nextthink = (time + 0.2);
};

void() afrit_deathc3 = [ 64, afrit_deathc4 ]
{
	self.nextthink = (time + 0.2);
};

void() afrit_deathc4 = [ 64, afrit_fast1 ]
{
	local entity missile;

	self.nextthink = (time + 0.000100);
	sound(self, CHAN_AUTO, "boss1/quake.wav", 1, ATTN_NONE);
	missile = spawn();
	missile.owner = self;
	missile.solid = SOLID_BBOX;
	missile.movetype = MOVETYPE_TOSS;
	setmodel(missile, "progs/lavacrack.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.origin = (self.origin + '0 0 8');
	missile.nextthink = (time + 0.1);
	missile.scale = (missile.scale * (3 + random()));
	missile.angles_y = ((random() * 720) + -360);
	missile.think = boss_trap_fin3;
	missile.frame = 4;
	missile.alpha = -1;
	pointparticles(particleeffectnum(/*26433i*/"cthon_fireball"), self.origin, VEC_ORIGIN, 1);
	T_RadiusDamage(self, self, 80, self);
};

void() vengeance_afrit_bright05 =
{
	sound(self, CHAN_WEAPON, "ambience/rumblefade.wav", 1, ATTN_NORM);
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = afrit_deathc1;
};

void() vengeance_afrit_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_afrit_bright05;
};

void() vengeance_afrit_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_afrit_bright04;
};

void() vengeance_afrit_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_afrit_bright03;
};

void() vengeance_afrit_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_afrit_bright02;
};

void() vengeance_afrit_bright00 =
{
	sound(self, CHAN_BODY, "ambience/rumblefade.wav", 0.8, ATTN_NORM);
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.1);
	self.think = vengeance_afrit_bright01;
};

void(string modelname, float modelframe) vengeance_afrit =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.origin_z = (self.origin_z + 1);
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_NOCLIP;
	self.inflamed = 0;
	setmodel(self, "progs/afrit.mdl");
	setsize(self, '-16 -16 -4', '16 16 4');
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_afritmass);
	vengeance_afrit_bright00();
};
