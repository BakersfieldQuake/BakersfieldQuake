//Decompiled code. Please respect the original copyright.

void(float loudness, float side) shambler_footsteps =
{
	local float select;

	if ((autocvar_monsterfootsteps == 1))
	{
		select = random();
		if ((select <= 0.33))
		{
			sound7(self, CHAN_AUTO, "walk/shambler1.wav", loudness, ATTN_IDLE, SNDSPD);
		}
		else
		{
			if ((select <= 0.66))
			{
				sound7(self, CHAN_AUTO, "walk/shambler2.wav", loudness, ATTN_IDLE, SNDSPD);
			}
			else
			{
				sound7(self, CHAN_AUTO, "walk/shambler3.wav", loudness, ATTN_IDLE, SNDSPD);
			}
		}
		if ((side && (autocvar_shambler_walking_quake >= 2)))
		{
			makevectors(self.angles);
			if ((side == 1))
			{
				particleeffectnum(/*52589i*/"shambler_foot_dust");
				pointparticles(particleeffectnum(/*52589i*/"shambler_foot_dust"), ((((self.origin + self.view_ofs) + (v_up * -40)) + (v_forward * 7)) + (v_right * -22)), VEC_ORIGIN, 1);
			}
			else
			{
				particleeffectnum(/*52589i*/"shambler_foot_dust");
				pointparticles(particleeffectnum(/*52589i*/"shambler_foot_dust"), ((((self.origin + self.view_ofs) + (v_up * -40)) + (v_forward * 7)) + (v_right * 22)), VEC_ORIGIN, 1);
			}
		}
		if (((loudness > 0.8) && ((autocvar_shambler_walking_quake == 1) || (autocvar_shambler_walking_quake == 3))))
		{
			shambler_walking_quake();
		}
	}
};

void() sham_stand1 = [ 0, sham_stand2 ]
{
	ai_stand();
};

void() sham_stand2 = [ 1, sham_stand3 ]
{
	ai_stand();
};

void() sham_stand3 = [ 2, sham_stand4 ]
{
	ai_stand();
};

void() sham_stand4 = [ 3, sham_stand5 ]
{
	ai_stand();
};

void() sham_stand5 = [ 4, sham_stand6 ]
{
	ai_stand();
};

void() sham_stand6 = [ 5, sham_stand7 ]
{
	ai_stand();
};

void() sham_stand7 = [ 6, sham_stand8 ]
{
	ai_stand();
};

void() sham_stand8 = [ 7, sham_stand9 ]
{
	ai_stand();
};

void() sham_stand9 = [ 8, sham_stand10 ]
{
	ai_stand();
};

void() sham_stand10 = [ 9, sham_stand11 ]
{
	ai_stand();
};

void() sham_stand11 = [ 10, sham_stand12 ]
{
	ai_stand();
};

void() sham_stand12 = [ 11, sham_stand13 ]
{
	ai_stand();
};

void() sham_stand13 = [ 12, sham_stand14 ]
{
	ai_stand();
};

void() sham_stand14 = [ 13, sham_stand15 ]
{
	ai_stand();
};

void() sham_stand15 = [ 14, sham_stand16 ]
{
	ai_stand();
};

void() sham_stand16 = [ 15, sham_stand17 ]
{
	ai_stand();
};

void() sham_stand17 = [ 16, sham_stand1 ]
{
	ai_stand();
};

void() sham_walk1 = [ 17, sham_walk2 ]
{
	ai_walk(10);
	shambler_footsteps(0.9, 2);
};

void() sham_walk2 = [ 18, sham_walk3 ]
{
	ai_walk(9);
};

void() sham_walk3 = [ 19, sham_walk4 ]
{
	ai_walk(9);
};

void() sham_walk4 = [ 20, sham_walk5 ]
{
	ai_walk(5);
};

void() sham_walk5 = [ 21, sham_walk6 ]
{
	ai_walk(6);
};

void() sham_walk6 = [ 22, sham_walk7 ]
{
	ai_walk(12);
};

void() sham_walk7 = [ 23, sham_walk8 ]
{
	ai_walk(8);
	shambler_footsteps(0.9, 1);
};

void() sham_walk8 = [ 24, sham_walk9 ]
{
	ai_walk(3);
};

void() sham_walk9 = [ 25, sham_walk10 ]
{
	ai_walk(13);
};

void() sham_walk10 = [ 26, sham_walk11 ]
{
	ai_walk(9);
};

void() sham_walk11 = [ 27, sham_walk12 ]
{
	ai_walk(7);
};

void() sham_walk12 = [ 28, sham_walk1 ]
{
	ai_walk(7);
	if ((random() > 0.8))
	{
		sound7(self, CHAN_VOICE, "shambler/sidle.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() sham_run1 = [ 29, sham_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
};

void() sham_run2 = [ 30, sham_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(24);
	shambler_footsteps(1, 2);
};

void() sham_run3 = [ 31, sham_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
};

void() sham_run4 = [ 32, sham_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
};

void() sham_run5 = [ 33, sham_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(24);
	shambler_footsteps(1, 1);
};

void() sham_run6 = [ 34, sham_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(20);
	if ((random() > 0.8))
	{
		sound7(self, CHAN_VOICE, "shambler/sidle.wav", 1, ATTN_IDLE, SNDSPD);
	}
};

void() sham_smash1 = [ 35, sham_smash2 ]
{
	sound7(self, CHAN_VOICE, "shambler/melee1.wav", 1, ATTN_NORM, SNDSPD);
	ai_charge(2);
};

void() sham_smash2 = [ 36, sham_smash3 ]
{
	ai_charge(6);
};

void() sham_smash3 = [ 37, sham_smash4 ]
{
	ai_charge(6);
};

void() sham_smash4 = [ 38, sham_smash5 ]
{
	ai_charge(5);
};

void() sham_smash5 = [ 39, sham_smash6 ]
{
	ai_charge(4);
	shambler_footsteps(0.75, 0);
};

void() sham_smash6 = [ 40, sham_smash7 ]
{
	ai_charge(1);
};

void() sham_smash7 = [ 41, sham_smash8 ]
{
	ai_charge(0);
};

void() sham_smash8 = [ 42, sham_smash9 ]
{
	ai_charge(0);
};

void() sham_smash9 = [ 43, sham_smash10 ]
{
	ai_charge(0);
};

void() sham_smash10 = [ 44, sham_smash11 ]
{
	local vector delta;
	local float ldmg;

	if (((self.grimrock_helper == 1) && (self.alpha < 1)))
	{
		delta = self.enemy.origin - self.origin;
		if ((((vlen(delta) > 100) || !self.enemy) || !CanDamage(self.enemy, self)))
		{
			self.alpha = -1;
			te_customflash(self.origin, 500, 0.7, '1 0 0');
			self.nextthink = (time + 0.2);
			self.think = SUB_Remove;
		}
	}
	if (!self.enemy)
	{
		return;
	}
	ai_charge(0);
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	if (!CanDamage(self.enemy, self))
	{
		return;
	}
	if ((autocvar_shambler_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_shambler_doubleclaws) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_shambler_doubleclaws;
	}
	T_Damage(self.enemy, self, self, ldmg);
	sound7(self, CHAN_VOICE, "shambler/smack.wav", 1, ATTN_NORM, SNDSPD);
	SpawnMeatSpray((self.origin + (v_forward * 16)), ((crandom() * 100) * v_right));
	SpawnMeatSpray((self.origin + (v_forward * 16)), ((crandom() * 100) * v_right));
	if (((self.grimrock_helper == 1) && (self.alpha < 1)))
	{
		self.alpha = -1;
		te_customflash(self.origin, 500, 0.7, '1 0 0');
		self.nextthink = (time + 0.2);
		self.think = SUB_Remove;
	}
};

void() sham_smash11 = [ 45, sham_smash12 ]
{
	ai_charge(5);
};

void() sham_smash12 = [ 46, sham_run1 ]
{
	ai_charge(4);
};

void(float side) ShamClaw =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	ai_charge(10);
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 100))
	{
		return;
	}
	if ((autocvar_shambler_size_influenced_attack == 1))
	{
		ldmg = (((random() + random()) + random()) * autocvar_shambler_claws) * self.scale;
	}
	else
	{
		ldmg = ((random() + random()) + random()) * autocvar_shambler_claws;
	}
	T_Damage(self.enemy, self, self, ldmg);
	sound7(self, CHAN_VOICE, "shambler/smack.wav", 1, ATTN_NORM, SNDSPD);
	if (side)
	{
		makevectors(self.angles);
		SpawnMeatSpray((self.origin + (v_forward * 16)), (side * v_right));
	}
};

void() sham_swingl1 = [ 56, sham_swingl2 ]
{
	sound7(self, CHAN_VOICE, "shambler/melee2.wav", 1, ATTN_NORM, SNDSPD);
	ai_charge(5);
};

void() sham_swingl2 = [ 57, sham_swingl3 ]
{
	ai_charge(3);
};

void() sham_swingl3 = [ 58, sham_swingl4 ]
{
	ai_charge(7);
};

void() sham_swingl4 = [ 59, sham_swingl5 ]
{
	ai_charge(3);
};

void() sham_swingl5 = [ 60, sham_swingl6 ]
{
	ai_charge(7);
};

void() sham_swingl6 = [ 61, sham_swingl7 ]
{
	ai_charge(9);
};

void() sham_swingl7 = [ 62, sham_swingl8 ]
{
	ai_charge(5);
	ShamClaw(250);
};

void() sham_swingl8 = [ 63, sham_swingl9 ]
{
	ai_charge(4);
	shambler_footsteps(0.7, 0);
};

void() sham_swingl9 = [ 64, sham_run1 ]
{
	ai_charge(8);
	if ((random() < 0.5))
	{
		self.think = sham_swingr1;
	}
};

void() sham_swingr1 = [ 47, sham_swingr2 ]
{
	sound7(self, CHAN_VOICE, "shambler/melee1.wav", 1, ATTN_NORM, SNDSPD);
	ai_charge(1);
};

void() sham_swingr2 = [ 48, sham_swingr3 ]
{
	ai_charge(8);
};

void() sham_swingr3 = [ 49, sham_swingr4 ]
{
	ai_charge(14);
};

void() sham_swingr4 = [ 50, sham_swingr5 ]
{
	ai_charge(7);
};

void() sham_swingr5 = [ 51, sham_swingr6 ]
{
	ai_charge(3);
};

void() sham_swingr6 = [ 52, sham_swingr7 ]
{
	ai_charge(6);
};

void() sham_swingr7 = [ 53, sham_swingr8 ]
{
	ai_charge(6);
	ShamClaw(-250);
};

void() sham_swingr8 = [ 54, sham_swingr9 ]
{
	ai_charge(3);
};

void() sham_swingr9 = [ 55, sham_run1 ]
{
	ai_charge(1);
	shambler_footsteps(0.7, 0);
	ai_charge(10);
	if ((random() < 0.5))
	{
		self.think = sham_swingl1;
	}
};

void() sham_melee =
{
	local float chance;

	chance = random();
	if (((chance > 0.6) || (self.health == 600)))
	{
		sham_smash1();
	}
	else
	{
		if ((chance > 0.3))
		{
			sham_swingr1();
		}
		else
		{
			sham_swingl1();
		}
	}
};

void() ShamblerLightning_Touch =
{
	if (other.health)
	{
		pointparticles(particleeffectnum(/*53679i*/"shambler_beam_impact"), self.origin, VEC_ORIGIN, 1);
	}
	else
	{
		pointparticles(particleeffectnum(/*53700i*/"shambler_beam_impact1"), self.origin, VEC_ORIGIN, 1);
	}
	self.touch = SUB_Null;
	self.solid = 0;
	self.nextthink = (time + 0.05);
	self.think = SUB_Remove;
};

void() FireShamblerLightning =
{
	local entity missile;
	local vector org;

	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_FLYMISSILE;
	missile.solid = SOLID_BBOX;
	missile.classname = "shamblerbeam";
	org = ((self.origin + (v_right * 1)) + (v_up * 24)) + (v_forward * 15);
	makevectors(self.angles);
	missile.velocity = normalize(((self.enemy.origin + '0 0 10') - org));
	missile.velocity = (missile.velocity * 9999999);
	missile.scale = 0.1;
	missile.alpha = -1;
	missile.touch = ShamblerLightning_Touch;
	missile.nextthink = (time + 1);
	missile.think = SUB_Remove;
	setmodel(missile, "progs/k_spike.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile, org);
};

void() FireShamblerLightning_right1 =
{
	local entity missile1;
	local vector org1;

	missile1 = spawn();
	missile1.owner = self;
	missile1.movetype = MOVETYPE_FLYMISSILE;
	missile1.solid = SOLID_BBOX;
	missile1.classname = "shamblerbeam1";
	org1 = ((self.origin + (v_right * 60)) + (v_up * 21)) + (v_forward * 15);
	makevectors(self.angles);
	missile1.velocity = normalize(((self.enemy.origin + '0 0 10') - org1));
	missile1.velocity = (missile1.velocity * 9999999);
	missile1.scale = 0.1;
	missile1.alpha = -1;
	missile1.touch = ShamblerLightning_Touch;
	missile1.nextthink = (time + 1);
	missile1.think = SUB_Remove;
	setmodel(missile1, "progs/k_spike.mdl");
	setsize(missile1, VEC_ORIGIN, VEC_ORIGIN);
	missile1.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile1, org1);
	self.nextthink = (time + 0.1);
	self.think = sham_magic6;
};

void() FireShamblerLightning_right2 =
{
	local entity missile1;
	local vector org1;

	missile1 = spawn();
	missile1.owner = self;
	missile1.movetype = MOVETYPE_FLYMISSILE;
	missile1.solid = SOLID_BBOX;
	missile1.classname = "shamblerbeam1";
	org1 = ((self.origin + (v_right * 60)) + (v_up * 21)) + (v_forward * 15);
	makevectors(self.angles);
	missile1.velocity = normalize(((self.enemy.origin + '0 0 10') - org1));
	missile1.velocity = (missile1.velocity * 9999999);
	missile1.scale = 0.1;
	missile1.alpha = -1;
	missile1.touch = ShamblerLightning_Touch;
	missile1.nextthink = (time + 1);
	missile1.think = SUB_Remove;
	setmodel(missile1, "progs/k_spike.mdl");
	setsize(missile1, VEC_ORIGIN, VEC_ORIGIN);
	missile1.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile1, org1);
	self.nextthink = (time + 0.1);
	self.think = sham_magic9;
};

void() FireShamblerLightning_right3 =
{
	local entity missile1;
	local vector org1;

	missile1 = spawn();
	missile1.owner = self;
	missile1.movetype = MOVETYPE_FLYMISSILE;
	missile1.solid = SOLID_BBOX;
	missile1.classname = "shamblerbeam1";
	org1 = ((self.origin + (v_right * 60)) + (v_up * 21)) + (v_forward * 15);
	makevectors(self.angles);
	missile1.velocity = normalize(((self.enemy.origin + '0 0 10') - org1));
	missile1.velocity = (missile1.velocity * 9999999);
	missile1.scale = 0.1;
	missile1.alpha = -1;
	missile1.touch = ShamblerLightning_Touch;
	missile1.nextthink = (time + 1);
	missile1.think = SUB_Remove;
	setmodel(missile1, "progs/k_spike.mdl");
	setsize(missile1, VEC_ORIGIN, VEC_ORIGIN);
	missile1.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile1, org1);
	self.nextthink = (time + 0.1);
	self.think = sham_magic10;
};

void() FireShamblerLightning_right4 =
{
	local entity missile1;
	local vector org1;

	missile1 = spawn();
	missile1.owner = self;
	missile1.movetype = MOVETYPE_FLYMISSILE;
	missile1.solid = SOLID_BBOX;
	missile1.classname = "shamblerbeam1";
	org1 = ((self.origin + (v_right * 60)) + (v_up * 21)) + (v_forward * 15);
	makevectors(self.angles);
	missile1.velocity = normalize(((self.enemy.origin + '0 0 10') - org1));
	missile1.velocity = (missile1.velocity * 9999999);
	missile1.scale = 0.1;
	missile1.alpha = -1;
	missile1.touch = ShamblerLightning_Touch;
	missile1.nextthink = (time + 1);
	missile1.think = SUB_Remove;
	setmodel(missile1, "progs/k_spike.mdl");
	setsize(missile1, VEC_ORIGIN, VEC_ORIGIN);
	missile1.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile1, org1);
	self.nextthink = (time + 0.1);
	self.think = sham_magic11;
};

void() FireShamblerLightning_right5 =
{
	local entity missile1;
	local vector org1;

	missile1 = spawn();
	missile1.owner = self;
	missile1.movetype = MOVETYPE_FLYMISSILE;
	missile1.solid = SOLID_BBOX;
	missile1.classname = "shamblerbeam1";
	org1 = ((self.origin + (v_right * 60)) + (v_up * 21)) + (v_forward * 15);
	makevectors(self.angles);
	missile1.velocity = normalize(((self.enemy.origin + '0 0 10') - org1));
	missile1.velocity = (missile1.velocity * 9999999);
	missile1.scale = 0.1;
	missile1.alpha = -1;
	missile1.touch = ShamblerLightning_Touch;
	missile1.nextthink = (time + 1);
	missile1.think = SUB_Remove;
	setmodel(missile1, "progs/k_spike.mdl");
	setsize(missile1, VEC_ORIGIN, VEC_ORIGIN);
	missile1.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile1, org1);
	self.nextthink = (time + 0.1);
	self.think = sham_magic12;
};

void(float nummer) FireShamblerLightning_left =
{
	local entity missile;
	local vector org;

	missile = spawn();
	missile.owner = self;
	missile.movetype = MOVETYPE_FLYMISSILE;
	missile.solid = SOLID_BBOX;
	missile.classname = "shamblerbeam";
	org = ((self.origin + (v_right * -47)) + (v_up * 17)) + (v_forward * 15);
	makevectors(self.angles);
	missile.velocity = normalize(((self.enemy.origin + '0 0 10') - org));
	missile.velocity = (missile.velocity * 9999999);
	missile.scale = 0.1;
	missile.alpha = -1;
	missile.touch = ShamblerLightning_Touch;
	missile.nextthink = (time + 1);
	missile.think = SUB_Remove;
	setmodel(missile, "progs/k_spike.mdl");
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	missile.traileffectnum = particleeffectnum(/*53735i*/"shambler_beam");
	setorigin(missile, org);
	self.nextthink = (time + 0.001);
	if ((nummer == 1))
	{
		self.think = FireShamblerLightning_right1;
	}
	else
	{
		if ((nummer == 2))
		{
			self.think = FireShamblerLightning_right2;
		}
		else
		{
			if ((nummer == 3))
			{
				self.think = FireShamblerLightning_right3;
			}
			else
			{
				if ((nummer == 4))
				{
					self.think = FireShamblerLightning_right4;
				}
				else
				{
					if ((nummer == 5))
					{
						self.think = FireShamblerLightning_right5;
					}
				}
			}
		}
	}
};

void(float hurt, float nummer) CastLightning =
{
	local vector org;
	local vector dir;

	self.effects = (self.effects | EF_MUZZLEFLASH);
	ai_face();
	org = self.origin + '0 0 40';
	dir = (self.enemy.origin + '0 0 16') - org;
	dir = normalize(dir);
	traceline(org, (self.origin + (dir * 600)), TRUE, self);
	if ((autocvar_shambler_lightning_beam == 1))
	{
		FireShamblerLightning();
	}
	else
	{
		if ((autocvar_shambler_lightning_beam == 2))
		{
			FireShamblerLightning_left(nummer);
		}
		else
		{
			WriteByte(MSG_BROADCAST, SVC_TEMPENTITY);
			WriteByte(MSG_BROADCAST, TE_LIGHTNING1);
			WriteEntity(MSG_BROADCAST, self);
			WriteCoord(MSG_BROADCAST, org_x);
			WriteCoord(MSG_BROADCAST, 0);
			WriteCoord(MSG_BROADCAST, 0);
			WriteCoord(MSG_BROADCAST, trace_endpos_x);
			WriteCoord(MSG_BROADCAST, 0);
			WriteCoord(MSG_BROADCAST, 0);
		}
	}
	if (hurt)
	{
		if ((autocvar_shambler_size_influenced_attack == 1))
		{
			LightningDamage(org, trace_endpos, self, (autocvar_shambler_lightning * self.scale));
		}
		else
		{
			LightningDamage(org, trace_endpos, self, autocvar_shambler_lightning);
		}
	}
};

void() sham_magic1 = [ 65, sham_magic2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	sound7(self, CHAN_WEAPON, "shambler/sattck1.wav", 1, ATTN_NORM, SNDSPD);
	if ((random() < 0.5))
	{
		self.has_fired = 1;
	}
};

void() sham_magic2 = [ 66, sham_magic3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
};

void() sham_magic3 = [ 67, sham_magic4 ]
{
	local entity ball;
	local vector org;

	ai_face();
	self.nextthink = (self.nextthink + 0.2);
	self.effects = (self.effects | EF_MUZZLEFLASH);
	ai_face();
	ball = spawn();
	setmodel(ball, "progs/plasma.mdl");
	ball.solid = SOLID_BBOX;
	ball.movetype = MOVETYPE_FLY;
	setsize(ball, VEC_ORIGIN, VEC_ORIGIN);
	makevectors(self.angles);
	if ((autocvar_shamblertype == 1))
	{
		org = ((self.origin + (v_up * 78)) + (v_right * 15)) + (v_forward * 22);
		setorigin(ball, org);
		ball.scale = 1.6;
	}
	else
	{
		if ((autocvar_shamblertype == 2))
		{
			org = ((self.origin + (v_up * 71)) + (v_right * 5)) + (v_forward * 15);
			setorigin(ball, org);
			ball.scale = 1.6;
		}
		else
		{
			if ((autocvar_shamblertype == 3))
			{
				if ((self.model == "progs/shambler.mdl"))
				{
					org = ((self.origin + (v_up * 78)) + (v_right * 22)) + (v_forward * 15);
					setorigin(ball, org);
					ball.scale = 1.9;
				}
				else
				{
					if ((self.model == "progs/shambler1.mdl"))
					{
						org = ((self.origin + (v_up * 78)) + (v_right * 15)) + (v_forward * 22);
						setorigin(ball, org);
						ball.scale = 1.6;
					}
				}
			}
			else
			{
				org = ((self.origin + (v_up * 78)) + (v_right * 22)) + (v_forward * 15);
				setorigin(ball, org);
				ball.scale = 1.9;
			}
		}
	}
	ball.alpha = 0.5;
	ball.avelocity = '700 600 900';
	pointparticles(particleeffectnum(/*46127i*/"shambler_ball"), org, VEC_ORIGIN, 1);
	ball.nextthink = (time + 0.45);
	ball.think = SUB_Remove;
};

void() sham_magic4 = [ 68, sham_magic5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	shambler_footsteps(0.8, 0);
};

void() sham_magic5 = [ 69, sham_magic6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	if (autocvar_shambler_lightning_beam)
	{
		CastLightning(0, 1);
	}
};

void() sham_magic6 = [ 70, sham_magic9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	CastLightning(1, 2);
	particleeffectnum(/*53801i*/"shambler_body");
	pointparticles(particleeffectnum(/*53801i*/"shambler_body"), (self.origin + (v_up * 30)), VEC_ORIGIN, 1);
	sound7(self, CHAN_WEAPON, "shambler/sboom.wav", 1, ATTN_NORM, SNDSPD);
};

void() sham_magic9 = [ 73, sham_magic10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	CastLightning(1, 3);
};

void() sham_magic10 = [ 74, sham_magic11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	CastLightning(1, 4);
};

void() sham_magic11 = [ 75, sham_magic12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	if ((skill == 3))
	{
		CastLightning(1, 5);
	}
	self.has_fired = 0;
};

void() sham_magic12 = [ 76, sham_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	if (((self.grimrock_helper == 1) && (self.alpha < 1)))
	{
		self.alpha = -1;
		te_customflash(self.origin, 500, 0.7, '1 0 0');
		self.nextthink = (time + 0.2);
		self.think = SUB_Remove;
	}
};

void() sham_pain1 = [ 77, sham_pain2 ]
{
};

void() sham_pain2 = [ 78, sham_pain3 ]
{
};

void() sham_pain3 = [ 79, sham_pain4 ]
{
};

void() sham_pain4 = [ 80, sham_pain5 ]
{
};

void() sham_pain5 = [ 81, sham_pain6 ]
{
};

void() sham_pain6 = [ 82, sham_run1 ]
{
};

void(entity attacker, float damage) sham_pain =
{
	sound7(self, CHAN_VOICE, "shambler/shurt2.wav", 1, ATTN_NORM, SNDSPD);
	if ((self.health <= 0))
	{
		return;
	}
	if (((random() * 400) > damage))
	{
		return;
	}
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 2);
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_shambler * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sham_pain1();
};

void() sham_dieburn1 = [ 83, sham_dieburn2 ]
{
	self.burnz_origin = 14;
	burn_toggle_shambler();
};

void() sham_dieburn2 = [ 84, sham_dieburn3 ]
{
	self.burnz_origin = 12;
};

void() sham_dieburn3 = [ 85, sham_dieburn4 ]
{
	self.burnz_origin = 8;
	self.solid = 0;
};

void() sham_dieburn4 = [ 86, sham_dieburn5 ]
{
	self.burnz_origin = 5;
};

void() sham_dieburn5 = [ 87, sham_dieburn6 ]
{
	self.burnz_origin = 1;
};

void() sham_dieburn6 = [ 88, sham_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() sham_dieburn7 = [ 89, sham_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() sham_dieburn8 = [ 90, sham_dieburn9 ]
{
	self.burnz_origin = -6;
};

void() sham_dieburn9 = [ 91, sham_dieburn10 ]
{
	self.burnz_origin = -6;
};

void() sham_dieburn10 = [ 92, sham_dieburn10 ]
{
	self.burnz_origin = -10;
};

void() sham_axdeth1 = [ 94, sham_axdeth2 ]
{
};

void() sham_axdeth2 = [ 95, sham_axdeth3 ]
{
	sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_IDLE, SNDSPD);
};

void() sham_axdeth3 = [ 96, sham_axdeth4 ]
{
	self.solid = 0;
	pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth4 = [ 97, sham_axdeth5 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth5 = [ 98, sham_axdeth6 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() sham_axdeth6 = [ 99, sham_axdeth7 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth7 = [ 100, sham_axdeth8 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth8 = [ 101, sham_axdeth9 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth9 = [ 102, sham_axdeth10 ]
{
	sound7(self, CHAN_AUTO, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth10 = [ 103, sham_axdeth11 ]
{
};

void() sham_axdeth11 = [ 104, sham_axdeth12 ]
{
};

void() sham_axdeth12 = [ 105, sham_axdeth13 ]
{
};

void() sham_axdeth13 = [ 106, sham_axdeth14 ]
{
};

void() sham_axdeth14 = [ 107, sham_axdeth15 ]
{
};

void() sham_axdeth15 = [ 108, sham_axdeth16 ]
{
	sound7(self, CHAN_VOICE, "misc/paste.wav", 1, ATTN_IDLE, SNDSPD);
};

void() sham_axdeth16 = [ 109, sham_axdeth17 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth17 = [ 110, sham_axdeth18 ]
{
};

void() sham_axdeth18 = [ 111, sham_axdeth19 ]
{
};

void() sham_axdeth19 = [ 112, sham_axdeth20 ]
{
};

void() sham_axdeth20 = [ 113, sham_axdeth21 ]
{
};

void() sham_axdeth21 = [ 114, sham_axdeth22 ]
{
};

void() sham_axdeth22 = [ 115, sham_axdeth23 ]
{
};

void() sham_axdeth23 = [ 116, sham_axdeth24 ]
{
};

void() sham_axdeth24 = [ 117, sham_axdeth25 ]
{
};

void() sham_axdeth25 = [ 118, sham_axdeth26 ]
{
};

void() sham_axdeth26 = [ 119, sham_axdeth27 ]
{
	pointparticles(particleeffectnum(/*15139i*/"blood_spurt"), self.origin, VEC_ORIGIN, 1);
};

void() sham_axdeth27 = [ 120, sham_axdeth28 ]
{
	pointparticles(particleeffectnum(/*52626i*/"shambler_falling_dust"), self.origin, VEC_ORIGIN, 1);
	sound7(self, CHAN_AUTO, "demon/fall_backwards.wav", 1, ATTN_NORM, SNDSPD);
};

void() sham_axdeth28 = [ 121, sham_axdeth29 ]
{
};

void() sham_axdeth29 = [ 122, sham_axdeth30 ]
{
};

void() sham_axdeth30 = [ 123, sham_axdeth31 ]
{
};

void() sham_axdeth31 = [ 124, sham_axdeth32 ]
{
};

void() sham_axdeth32 = [ 125, sham_axdeth33 ]
{
};

void() sham_axdeth33 = [ 126, sham_axdeth34 ]
{
};

void() sham_axdeth34 = [ 127, sham_axdeth35 ]
{
};

void() sham_axdeth35 = [ 128, sham_axdeth36 ]
{
};

void() sham_axdeth36 = [ 129, sham_axdeth37 ]
{
};

void() sham_axdeth37 = [ 130, sham_axdeth38 ]
{
	pointparticles(particleeffectnum(/*52626i*/"shambler_falling_dust"), self.origin, VEC_ORIGIN, 1);
	Monster_Animation_EarthQuake(20, 377);
	sound7(self, CHAN_AUTO, "shambler/fall.wav", 1, ATTN_NORM, SNDSPD);
};

void() sham_axdeth38 = [ 131, sham_axdeth38 ]
{
	self.burnable_corpse = 1;
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_shamblercorpsehealth, "progs/h_shams.mdl");
};

void() sham_death1 = [ 83, sham_death2 ]
{
};

void() sham_death2 = [ 84, sham_death3 ]
{
};

void() sham_death3 = [ 85, sham_death4 ]
{
	self.solid = 0;
};

void() sham_death4 = [ 86, sham_death5 ]
{
};

void() sham_death5 = [ 87, sham_death6 ]
{
};

void() sham_death6 = [ 88, sham_death7 ]
{
};

void() sham_death7 = [ 89, sham_death8 ]
{
};

void() sham_death8 = [ 90, sham_death9 ]
{
};

void() sham_death9 = [ 91, sham_death10 ]
{
};

void() sham_death10 = [ 92, sham_death11 ]
{
	pointparticles(particleeffectnum(/*52626i*/"shambler_falling_dust"), self.origin, VEC_ORIGIN, 1);
	Monster_Animation_EarthQuake(20, 377);
	sound7(self, CHAN_AUTO, "shambler/fall.wav", 1, ATTN_NORM, SNDSPD);
};

void() sham_death11 = [ 93, sham_death11 ]
{
	local float zufall;
	local float zet;
	local float randomness;

	if ((self.inflamed == 1))
	{
		self.colormod = '0.25 0.17 0.17';
		self.alpha = 1;
		if ((self.monstermodel == 0))
		{
			CopyMonsterToBodyQue(autocvar_shamblercorpsehealth, "progs/h_shams.mdl");
		}
		if ((self.monstermodel == 1))
		{
			CopyMonsterToBodyQue(autocvar_shamblercorpsehealth, "progs/h_shams1.mdl");
		}
		return;
	}
	zet = 33;
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_shamblercorpsehealth, "progs/h_shams.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_shamblercorpsehealth, "progs/h_shams1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
	if ((self.grimrock_helper == 0))
	{
		autocvar_shamblerrandomness = autocvar_shamblerrandomness * 0.01;
		if ((autocvar_shambler == 1))
		{
			randomness = random();
			if ((randomness <= autocvar_shamblerrandomness))
			{
				ghost_die();
			}
		}
		else
		{
			if ((autocvar_shambler == 2))
			{
				randomness = random();
				if ((randomness <= autocvar_shamblerrandomness))
				{
					if ((self.monstermodel == 0))
					{
						soul("progs/shambler.mdl", 93, zet);
					}
					else
					{
						if ((self.monstermodel == 1))
						{
							soul("progs/shambler1.mdl", 93, zet);
						}
					}
				}
			}
			else
			{
				if ((autocvar_shambler == 3))
				{
					randomness = random();
					if ((randomness <= autocvar_shamblerrandomness))
					{
						vengeance_shambler("progs/shambler.mdl", 93);
					}
				}
				else
				{
					if ((autocvar_shambler == 5))
					{
						randomness = random();
						if ((randomness <= autocvar_shamblerrandomness))
						{
							zufall = random();
							if ((zufall > 0.64))
							{
								ghost_die();
							}
							else
							{
								if ((zufall < 0.26))
								{
									if ((self.monstermodel == 0))
									{
										soul("progs/shambler.mdl", 93, zet);
									}
									else
									{
										if ((self.monstermodel == 1))
										{
											soul("progs/shambler1.mdl", 93, zet);
										}
									}
								}
								else
								{
								}
							}
						}
					}
					else
					{
					}
				}
			}
		}
	}
	else
	{
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.9))
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
						if ((self.monstermodel == 0))
						{
							soul("progs/shambler.mdl", 93, zet);
						}
						else
						{
							if ((self.monstermodel == 1))
							{
								soul("progs/shambler1.mdl", 93, zet);
							}
						}
					}
				}
				else
				{
					vengeance_shambler("progs/shambler.mdl", 93);
				}
			}
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_shambler =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		ThrowGib("progs/gib_shfoot2.mdl", self.health);
		ThrowGib("progs/gib_shclaw1.mdl", self.health);
		ThrowGib("progs/gib_shclaw2.mdl", self.health);
		ThrowGib("progs/gib_shfoot1.mdl", self.health);
	}
	gibscounter = gibscounter + 1;
	producegibs_shambler(maxgibs, gibscounter);
};

void() shambler_lightning_death = [ 80, shambler_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		lightninggun_death_fade();
	}
};

void() shambler_lightning_death1 = [ 80, shambler_lightning_death1 ]
{
	self.solid = 0;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(1, "progs/h_shams.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(1, "progs/h_shams1.mdl");
	}
};

void() sham_inflamed1 = [ 29, sham_inflamed2 ]
{
	local float r;

	ai_run_inflamed(20);
	r = random();
	if ((r < 0.4))
	{
		sound7(self, CHAN_VOICE, "shambler/melee1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.82))
		{
			sound7(self, CHAN_VOICE, "shambler/shurt2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() sham_inflamed2 = [ 30, sham_inflamed3 ]
{
	ai_run_inflamed(24);
	shambler_footsteps(1, 2);
};

void() sham_inflamed3 = [ 31, sham_inflamed4 ]
{
	ai_run_inflamed(20);
};

void() sham_inflamed4 = [ 32, sham_inflamed5 ]
{
	ai_run_inflamed(20);
};

void() sham_inflamed5 = [ 33, sham_inflamed6 ]
{
	ai_run_inflamed(24);
	shambler_footsteps(1, 1);
};

void() sham_inflamed6 = [ 34, sham_inflamed1 ]
{
	ai_run_inflamed(20);
	if ((self.inflametime < time))
	{
		sham_die();
		return;
	}
	if ((random() < 0.4))
	{
		sham_inflamed7();
	}
};

void() sham_inflamed7 = [ 77, sham_inflamed8 ]
{
	local float r;

	self.nextthink = (time + 0.09);
	r = random();
	if ((r < 0.4))
	{
		sound7(self, CHAN_VOICE, "shambler/melee1.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		if ((r < 0.85))
		{
			sound7(self, CHAN_VOICE, "shambler/shurt2.wav", 1, ATTN_NORM, SNDSPD);
		}
	}
};

void() sham_inflamed8 = [ 78, sham_inflamed9 ]
{
	self.nextthink = (time + 0.09);
};

void() sham_inflamed9 = [ 79, sham_inflamed10 ]
{
	self.nextthink = (time + 0.09);
};

void() sham_inflamed10 = [ 80, sham_inflamed11 ]
{
	self.nextthink = (time + 0.09);
};

void() sham_inflamed11 = [ 81, sham_inflamed12 ]
{
	self.nextthink = (time + 0.09);
};

void() sham_inflamed12 = [ 82, sham_inflamed1 ]
{
	self.nextthink = (time + 0.09);
	if ((self.inflametime < time))
	{
		sham_die();
		return;
	}
};

void() sham_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float zufall;
	local float randomness;

	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			shambler_lightning_death();
			return;
		}
	}
	else
	{
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.enemy.meleeing == 0)) && (self.sticky != 1)))
		{
			lg_death1();
			return;
		}
	}
	if ((self.health < -60))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_shambler * 0.01)))
			{
				the_matrix = 1;
				SNDSPD = 70;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		play_gibsound();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		CeilSplat();
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_shams.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_shams1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_shambler(maxgibs, gibscounter);
		return;
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 100;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				sham_inflamed1();
				return;
			}
		}
		else
		{
			sound7(self, CHAN_VOICE, "shambler/sdeath.wav", 1, ATTN_NORM, SNDSPD);
			sham_death1();
			return;
		}
	}
	autocvar_shamblerrandomness = autocvar_shamblerrandomness * 0.01;
	if ((autocvar_shambler == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_shamblerrandomness))
		{
			self.delete_painskin = 1;
			sham_dieburn1();
			return;
		}
	}
	if ((autocvar_shambler == 6))
	{
		randomness = random();
		if ((randomness <= autocvar_shamblerrandomness))
		{
			zufall = random();
			if ((zufall <= 0.26))
			{
				self.delete_painskin = 1;
				sham_dieburn1();
				return;
			}
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_shambler * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	sound7(self, CHAN_VOICE, "shambler/sdeath.wav", 1, ATTN_NORM, SNDSPD);
	sham_death1();
	if ((self.enemy.meleeing == 0))
	{
		if ((((self.enemy.weapon == IT_AXE) || (self.enemy.weapon == IT_CHAINSAW)) || (random() < 0.075)))
		{
			if ((autocvar_bloodextension == 1))
			{
				pointparticles(particleeffectnum(/*53066i*/"blood_blast"), self.origin, VEC_ORIGIN, 1);
			}
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			self.delete_painskin = 1;
			if ((self.skin == 0))
			{
				self.model = "progs/shambleraxe.mdl";
				setmodel(self, "progs/shambleraxe.mdl");
				self.skin = 0;
			}
			else
			{
				self.model = "progs/shambleraxe.mdl";
				setmodel(self, "progs/shambleraxe.mdl");
				self.skin = 1;
			}
			sham_axdeth1();
			ThrowGib("progs/chop.mdl", self.health);
		}
	}
};

void() monster_shambler =
{
	local float zufall;
	local float zuffa;
	local float replacerr;
	local float replacerrr;
	local float replacer;
	local vector check;
	local float replacez;
	local float replac;
	local entity pain_skin_entity;
	local float replacce;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	precache_model("progs/shambler.mdl");
	precache_model("progs/s_light.mdl");
	precache_model("progs/h_shams.mdl");
	precache_model("progs/bolt.mdl");
	precache_model("progs/plasma.mdl");
	precachegibs_shamb();
	precache_sound("shambler/sattck1.wav");
	precache_sound("shambler/sboom.wav");
	precache_sound("shambler/sdeath.wav");
	precache_sound("shambler/shurt2.wav");
	precache_sound("shambler/sidle.wav");
	precache_sound("shambler/ssight.wav");
	precache_sound("shambler/melee1.wav");
	precache_sound("shambler/melee2.wav");
	precache_sound("shambler/smack.wav");
	precache_sound("shambler/fall.wav");
	precache_sound("walk/shambler1.wav");
	precache_sound("walk/shambler2.wav");
	precache_sound("walk/shambler3.wav");
	precache_sound("demon/fall_backwards.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_shamblermultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/shambler.mdl");
		zufall = random();
		if ((zufall >= 0.5))
		{
			self.skin = 0;
			self.monsterskin = 0;
			self.monstermodel = 0;
		}
		else
		{
			self.skin = 1;
			self.monsterskin = 1;
			self.monstermodel = 0;
		}
	}
	else
	{
		if ((autocvar_shamblermultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/shambler1.mdl");
			precache_model("progs/h_shams1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/shambler.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/shambler1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_shamblermultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/shambler1.mdl");
				precache_model("progs/h_shams1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/shambler.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/shambler.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/shambler1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_shamblermultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/shambler1.mdl");
					precache_model("progs/h_shams1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/shambler.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/shambler.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/shambler1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/shambler1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/shambler.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_shambler_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
			self.sizediff = '0 0 3';
			setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
				self.sizediff = '0 0 1';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				self.scale = 1;
				setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			}
		}
	}
	else
	{
		if ((autocvar_shambler_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
				self.sizediff = '0 0 5';
				setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
					self.sizediff = '0 0 3';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
						self.sizediff = '0 0 1';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						self.scale = 1;
						setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
					}
				}
			}
		}
		else
		{
			if ((autocvar_shambler_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
					self.sizediff = '0 0 7';
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
						self.sizediff = '0 0 5';
						setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
							setsize(self, '-32 -32 -27', '32 32 61');
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
								self.sizediff = '0 0 1';
								setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
							}
							else
							{
								self.scale = 1;
								setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_shambler_size > 3))
				{
					if ((autocvar_shambler_size > 40))
					{
						self.origin = (self.origin + '0 0 10');
					}
					self.scale = (1 + (autocvar_shambler_size * 0.01));
					self.sizefactor_x = 0;
					self.sizefactor_y = 0;
					self.sizefactor_z = (autocvar_shambler_size * 0.25);
					self.sizediff = self.sizefactor;
					setsize(self, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
				}
				else
				{
					self.scale = 1;
					setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
				}
			}
		}
	}
	if ((autocvar_shambler_size_influenced_health == 1))
	{
		self.health = (autocvar_shambler_health * self.scale);
	}
	else
	{
		self.health = autocvar_shambler_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_shambler_random_skin_colors))
	{
		self.colormod_x = random();
		if ((self.colormod_x < 0.5))
		{
			self.colormod_x = (self.colormod_x + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_x < 0.75))
			{
				self.colormod_x = (self.colormod_x + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_x < 0.65))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
			else
			{
				if ((self.colormod_x < 0.55))
				{
					self.colormod_x = (self.colormod_x + 0.25);
				}
			}
		}
		self.colormod_y = random();
		if ((self.colormod_y < 0.5))
		{
			self.colormod_y = (self.colormod_y + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_y < 0.75))
			{
				self.colormod_y = (self.colormod_y + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_y < 0.65))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
			else
			{
				if ((self.colormod_y < 0.55))
				{
					self.colormod_y = (self.colormod_y + 0.25);
				}
			}
		}
		self.colormod_z = random();
		if ((self.colormod_z < 0.5))
		{
			self.colormod_z = (self.colormod_z + 0.5);
		}
		if ((autocvar_monster_random_skin_color_alteration == 1))
		{
			if ((self.colormod_z < 0.75))
			{
				self.colormod_z = (self.colormod_z + 0.25);
			}
		}
		else
		{
			if ((autocvar_monster_random_skin_color_alteration == 2))
			{
				if ((self.colormod_z < 0.65))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
			else
			{
				if ((self.colormod_z < 0.55))
				{
					self.colormod_z = (self.colormod_z + 0.25);
				}
			}
		}
	}
	self.th_stand = sham_stand1;
	self.th_walk = sham_walk1;
	self.th_run = sham_run1;
	self.th_die = sham_die;
	self.th_melee = sham_melee;
	self.th_missile = sham_magic1;
	self.th_pain = sham_pain;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_yakman_replace_shambler)
	{
		replacerr = autocvar_yakman_replace_shambler * 0.01;
		if ((random() <= replacerr))
		{
			self.health = autocvar_shambler_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_yakman_start();
			return;
		}
	}
	if (autocvar_carnivean_replace_shambler)
	{
		replacerrr = autocvar_carnivean_replace_shambler * 0.01;
		if ((random() <= replacerrr))
		{
			self.health = autocvar_shambler_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_carnivean_start();
			return;
		}
	}
	if (autocvar_spider_replace_shambler)
	{
		replacer = autocvar_spider_replace_shambler * 0.01;
		if ((random() <= replacer))
		{
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((pointcontents(check) == CONTENT_WATER) && autocvar_spider_can_spawn_in_water) || (pointcontents(check) != CONTENT_WATER)))
			{
				if (autocvar_spider_replace_shambler_large)
				{
					self.scale = 1;
					setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
					self.nextthink = (time + 0.3);
					self.think = SUB_Remove;
					monster_spider_shambler_start();
				}
				else
				{
					self.skin = 1;
					self.health = autocvar_shambler_health;
					self.scale = 1;
					setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
					self.nextthink = (time + 0.3);
					self.think = SUB_Remove;
					monster_spider_start();
				}
				return;
			}
		}
	}
	if (autocvar_reiver_replace_shambler)
	{
		replacez = autocvar_reiver_replace_shambler * 0.01;
		if ((random() <= replacez))
		{
			self.health = autocvar_shambler_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_liftorigin_start();
			return;
		}
	}
	if (autocvar_afrit_replace_shambler)
	{
		replac = autocvar_afrit_replace_shambler * 0.01;
		if ((random() <= replac))
		{
			self.health = autocvar_shambler_health;
			self.scale = 1;
			setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_liftorigin_start();
			return;
		}
	}
	if (autocvar_painskin_transparency)
	{
		pain_skin_entity = spawn();
		pain_skin_entity.solid = 0;
		pain_skin_entity.movetype = MOVETYPE_NOCLIP;
		pain_skin_entity.owner = self;
		setmodel(pain_skin_entity, self.model);
		setsize(pain_skin_entity, (VEC_HULL2_MIN - self.sizediff), (VEC_HULL2_MAX - self.sizediff));
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
	walkmonster_start();
	do_the_cloning();
	if (autocvar_reiver_supports_shambler)
	{
		replacce = autocvar_reiver_supports_shambler * 0.01;
		if ((random() <= replacce))
		{
			add_reiver_support_walk();
		}
	}
	if (autocvar_afrit_supports_shambler)
	{
		if ((cvar("skill") == 3))
		{
			replace = (autocvar_afrit_supports_shambler + 1) * 0.01;
		}
		else
		{
			replace = autocvar_afrit_supports_shambler * 0.01;
		}
		if ((random() <= replace))
		{
			add_afrit_support_walk();
		}
	}
	MonsterPhysics(self, autocvar_shamblermass);
};

void() vengeance_shambler_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_shambler_touch =
{
	self.touch = SUB_Null;
	self.think = vengeance_shambler_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull =
{
	local vector offang;
	local vector org;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = ((self.origin + self.mins) + (self.size * 0.5)) + (v_forward * 20);
	launch_vengeance_skull(org);
	newmis.classname = "skull";
	setmodel(newmis, "progs/skull.mdl");
	setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
	newmis.scale = 0.9;
	precache_sound("vengeance/skull.wav");
	precache_sound("vengeance/skulltouch.wav");
};

void() vengeance_shambler_run1 = [ 29, vengeance_shambler_run2 ]
{
	ai_face();
	movetogoal(21);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_run2 = [ 30, vengeance_shambler_run3 ]
{
	ai_face();
	movetogoal(25);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.35;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_run3 = [ 31, vengeance_shambler_run4 ]
{
	ai_face();
	movetogoal(21);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_run4 = [ 32, vengeance_shambler_run5 ]
{
	ai_face();
	movetogoal(21);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.25;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_run5 = [ 33, vengeance_shambler_random ]
{
	ai_face();
	movetogoal(25);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash1 = [ 35, vengeance_shambler_smash2 ]
{
	ai_face();
	movetogoal(4);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash2 = [ 36, vengeance_shambler_smash3 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.18;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash3 = [ 37, vengeance_shambler_smash4 ]
{
	ai_face();
	movetogoal(8);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.16;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash4 = [ 38, vengeance_shambler_smash5 ]
{
	ai_face();
	movetogoal(7);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.14;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash5 = [ 39, vengeance_shambler_smash6 ]
{
	ai_face();
	movetogoal(6);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.12;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash6 = [ 40, vengeance_shambler_smash7 ]
{
	ai_face();
	movetogoal(3);
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.1;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash7 = [ 42, vengeance_shambler_smash8 ]
{
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.08;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_smash8 = [ 43, vengeance_shambler_end1 ]
{
	ai_face();
	self.touch = vengeance_shambler_touch;
	sound7(self, CHAN_VOICE, "shambler/melee2.wav", 1, 4);
	makevectors(self.angles);
	self.origin_z = (self.origin_z + 1);
	self.velocity = ((v_forward * 200) + '0 0 10');
	self.alpha = 0.06;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull1 = [ 65, vengeance_shambler_skull2 ]
{
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull2 = [ 66, vengeance_shambler_skull3 ]
{
	sound7(self, CHAN_VOICE, "vengeance/shamattck1.wav", 1, 4);
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull3 = [ 67, vengeance_shambler_skull4 ]
{
	local entity o;

	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (self.nextthink + 0.2);
	self.effects = (self.effects | EF_MUZZLEFLASH);
	self.owner = spawn();
	o = self.owner;
	setmodel(o, "progs/s_light.mdl");
	setorigin(o, self.origin);
	o.angles = self.angles;
	o.colormod = '8 0 0';
	o.alpha = 0.4;
	o.nextthink = (time + 0.5);
	o.think = SUB_Remove;
};

void() vengeance_shambler_skull4 = [ 68, vengeance_shambler_skull5 ]
{
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.effects = (self.effects | EF_MUZZLEFLASH);
	self.owner.frame = 1;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull5 = [ 69, vengeance_shambler_skull6 ]
{
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.effects = (self.effects | EF_MUZZLEFLASH);
	self.owner.frame = 2;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_skull6 = [ 70, vengeance_shambler_end1 ]
{
	remove(self.owner);
	ai_face();
	self.touch = vengeance_shambler_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	vengeance_shambler_skull();
};

void() vengeance_shambler_random =
{
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	if ((random() > 0.65))
	{
		self.think = sham_smash1;
	}
	else
	{
		self.think = sham_magic1;
	}
};

void() vengeance_shambler1 = [ 92, vengeance_shambler2 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler2 = [ 91, vengeance_shambler3 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler3 = [ 90, vengeance_shambler4 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler4 = [ 89, vengeance_shambler5 ]
{
	sound7(self, CHAN_WEAPON, "vengeance/shamawake.wav", 1, ATTN_NORM, SNDSPD);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler5 = [ 88, vengeance_shambler6 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler6 = [ 87, vengeance_shambler7 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler7 = [ 86, vengeance_shambler8 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler8 = [ 85, vengeance_shambler9 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler9 = [ 84, vengeance_shambler10 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler10 = [ 83, vengeance_shambler_run1 ]
{
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_shambler_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shambler1;
};

void() vengeance_shambler_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shambler_bright05;
};

void() vengeance_shambler_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shambler_bright04;
};

void() vengeance_shambler_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shambler_bright03;
};

void() vengeance_shambler_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_shambler_bright02;
};

void() vengeance_shambler_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.3);
	self.think = vengeance_shambler_bright01;
};

void(string modelname, float modelframe) vengeance_shambler =
{
	local vector v;

	v_x = self.origin_x;
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_STEP;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/shambler.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/shambler1.mdl");
		}
	}
	setsize(self, VEC_HULL2_MIN, VEC_HULL2_MAX);
	self.frame = modelframe;
	self.solid = 0;
	MonsterPhysics(self, autocvar_shamblermass);
	vengeance_shambler_bright00();
};
