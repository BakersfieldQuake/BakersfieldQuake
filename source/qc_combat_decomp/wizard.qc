//Decompiled code. Please respect the original copyright.

void(entity missile, float mspeed, float accuracy) LaunchMissile =
{
	local vector vec;
	local vector move;
	local float fly;

	makevectors(self.angles);
	vec = ((self.enemy.origin + self.enemy.mins) + (self.enemy.size * 0.7)) - missile.origin;
	fly = vlen(vec) / mspeed;
	move = self.enemy.velocity;
	vec = vec + (move * fly);
	vec = normalize(vec);
	vec = (vec + ((accuracy * v_up) * (random() - 0.5))) + ((accuracy * v_right) * (random() - 0.5));
	missile.velocity = (vec * mspeed);
	missile.angles = VEC_ORIGIN;
	missile.angles_y = vectoyaw(missile.velocity);
	missile.nextthink = (time + 5);
	missile.think = SUB_Remove;
};

float() WizardCheckAttack =
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
		if ((self.attack_state != AS_STRAIGHT))
		{
			self.attack_state = AS_STRAIGHT;
			wiz_run1();
		}
		return (0);
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
			wiz_run1();
		}
		return (0);
	}
	if ((enemy_range == RANGE_MELEE))
	{
		if (autocvar_skill_adjusted_monster_rangedattack_frequence)
		{
			if ((skill == 0))
			{
				chance = 0.9;
			}
			else
			{
				if ((skill == 1))
				{
					chance = 0.92;
				}
				else
				{
					if ((skill == 2))
					{
						chance = 0.94;
					}
					else
					{
						chance = 0.96;
					}
				}
			}
		}
		else
		{
			chance = 0.9;
		}
	}
	else
	{
		if ((enemy_range == RANGE_NEAR))
		{
			if (autocvar_skill_adjusted_monster_rangedattack_frequence)
			{
				if ((skill == 0))
				{
					chance = 0.6;
				}
				else
				{
					if ((skill == 1))
					{
						chance = 0.7;
					}
					else
					{
						if ((skill == 2))
						{
							chance = 0.8;
						}
						else
						{
							chance = 0.9;
						}
					}
				}
			}
			else
			{
				chance = 0.6;
			}
		}
		else
		{
			if ((enemy_range == RANGE_MID))
			{
				if (autocvar_skill_adjusted_monster_rangedattack_frequence)
				{
					if ((skill == 0))
					{
						chance = 0.2;
					}
					else
					{
						if ((skill == 1))
						{
							chance = 0.35;
						}
						else
						{
							if ((skill == 2))
							{
								chance = 0.5;
							}
							else
							{
								chance = 0.666;
							}
						}
					}
				}
				else
				{
					chance = 0.2;
				}
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
			wiz_run1();
		}
	}
	else
	{
		if ((self.attack_state != AS_SLIDING))
		{
			self.attack_state = AS_SLIDING;
			wiz_side1();
		}
	}
	return (0);
};

void() WizardAttackFinished =
{
	if (((enemy_range >= RANGE_MID) || !enemy_vis))
	{
		self.attack_state = AS_STRAIGHT;
		self.think = wiz_run1;
	}
	else
	{
		self.attack_state = AS_SLIDING;
		self.think = wiz_side1;
	}
};

void() homing_spikes_think =
{
	local vector newdirection;
	local float t;
	local float homingpower;

	if ((self.enemy.health < 1))
	{
		remove(self);
	}
	if ((self.maxlifetime < time))
	{
		remove(self);
	}
	if ((time < self.skypad_steer_t))
	{
		self.ltime = time;
		self.angles = vectoangles(self.velocity);
		self.think = homing_spikes_think;
		self.nextthink = (time + 0.2);
		return;
	}
	self.velocity = normalize(self.velocity);
	newdirection = (self.enemy.origin + '0 0 12') - self.origin;
	newdirection = normalize(newdirection);
	t = time - self.ltime;
	self.ltime = time;
	if ((self.classname == "knightspike"))
	{
		if ((skill == 1))
		{
			homingpower = 0.2;
		}
		else
		{
			if ((skill == 2))
			{
				homingpower = 0.27;
			}
			else
			{
				homingpower = 0.33;
			}
		}
	}
	else
	{
		if ((skill == 1))
		{
			homingpower = 0.3;
		}
		else
		{
			if ((skill == 2))
			{
				homingpower = 0.4;
			}
			else
			{
				homingpower = 0.5;
			}
		}
	}
	self.velocity = (((self.velocity * (1 - homingpower)) * t) + ((newdirection * homingpower) * t));
	self.velocity = normalize(self.velocity);
	if ((self.classname == "knightspike"))
	{
		self.velocity = (self.velocity * 300);
	}
	else
	{
		self.velocity = (self.velocity * 600);
	}
	self.angles = vectoangles(self.velocity);
	self.think = homing_spikes_think;
	self.nextthink = (time + 0.2);
};

void(vector org, vector dir) launch_homing_spikes =
{
	newmis = spawn();
	newmis.owner = self;
	newmis.enemy = self.enemy;
	newmis.movetype = MOVETYPE_FLYMISSILE;
	newmis.solid = SOLID_BBOX;
	newmis.angles = vectoangles(dir);
	newmis.touch = spike_enemy_touch;
	setorigin(newmis, org);
	newmis.velocity = (dir * 1000);
	newmis.maxlifetime = (time + 5);
	newmis.think = homing_spikes_think;
	newmis.nextthink = (time + 0.1);
};

void() Wiz_FastFire =
{
	local vector vec;
	local vector dst;

	if ((self.owner.has_fired > 0))
	{
		remove(self);
		return;
	}
	else
	{
		if ((self.owner.health > 0))
		{
			self.owner.effects = (self.owner.effects | EF_MUZZLEFLASH);
			makevectors(self.enemy.angles);
			dst = self.enemy.origin - (13 * self.movedir);
			vec = normalize((dst - self.origin));
			sound7(self, CHAN_WEAPON, "wizard/wattack.wav", 1, ATTN_NORM, SNDSPD);
			if ((autocvar_skill_adjusted_wizard_projectile_homing && (skill != 0)))
			{
				launch_homing_spikes(self.origin, vec);
			}
			else
			{
				launch_enemy_spike(self.origin, vec);
			}
			newmis.velocity = (vec * 600);
			newmis.owner = self.owner;
			newmis.classname = "wizspike";
			setmodel(newmis, "progs/w_spike.mdl");
			newmis.scale = autocvar_wizard_projectile_size;
			if ((autocvar_wizard_projectile_traileffect != 1))
			{
				newmis.traileffectnum = particleeffectnum(/*55508i*/"TR_WIZSPIKE_2");
			}
			setsize(newmis, VEC_ORIGIN, VEC_ORIGIN);
		}
	}
	remove(self);
};

void() Wiz_StartFast =
{
	local entity missile;

	if ((self.has_fired > 0))
	{
		return;
	}
	sound7(self, CHAN_WEAPON, "wizard/wattack.wav", 1, ATTN_NORM, SNDSPD);
	self.v_angle = self.angles;
	makevectors(self.angles);
	missile = spawn();
	missile.owner = self;
	missile.nextthink = (time + 0.6);
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, (((self.origin + '0 0 30') + (v_forward * 14)) + (v_right * 14)));
	missile.enemy = self.enemy;
	missile.classname = "wizspike";
	missile.nextthink = (time + 0.8);
	missile.think = Wiz_FastFire;
	missile.movedir = v_right;
	missile = spawn();
	missile.owner = self;
	missile.classname = "wizspike";
	missile.nextthink = (time + 1);
	setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
	setorigin(missile, (((self.origin + '0 0 30') + (v_forward * 14)) + (v_right * -14)));
	missile.enemy = self.enemy;
	missile.nextthink = (time + 0.3);
	missile.think = Wiz_FastFire;
	missile.movedir = (VEC_ORIGIN - v_right);
};

void() Wiz_idlesound =
{
	local float wr;

	wr = random() * 5;
	if ((self.waitmin < time))
	{
		self.waitmin = (time + 2);
		if ((wr > 4.5))
		{
			sound7(self, CHAN_VOICE, "wizard/widle1.wav", 1, ATTN_IDLE, SNDSPD);
		}
		if ((wr < 1.5))
		{
			sound(self, CHAN_VOICE, "wizard/widle2.wav", 1, ATTN_IDLE, SNDSPD);
		}
	}
	return;
};

void(vector org) spawn_wizard_fog =
{
	s = spawn();
	s.origin = org;
	s.nextthink = (time + 0.2);
	s.think = play_teleport;
	pointparticles(particleeffectnum(/*55558i*/"wizard_fog"), org, VEC_ORIGIN, 1);
};

float(entity beacon, float attack) PM_WizTeleport =
{
	local vector spot;
	local vector vec;

	if ((self.health <= 0))
	{
		return (0);
	}
	spot_x = beacon.origin_x + ((random() * 2500) - 1250);
	vec = normalize((spot - beacon.origin));
	traceline(beacon.origin, spot, TRUE, beacon);
	spot = trace_endpos - (vec * 50);
	if ((vlen((spot - self.origin)) < 128))
	{
		return (0);
	}
	if (PM_InWall(self, spot))
	{
		return (0);
	}
	if (!PM_TraceCheck(self, spot))
	{
		return (0);
	}
	if (attack)
	{
		traceline(spot, self.enemy.origin, FALSE, self);
		if ((trace_fraction < 1))
		{
			if ((trace_ent != self.enemy))
			{
				return (0);
			}
		}
	}
	if ((vlen((spot - self.enemy.origin)) < 256))
	{
		return (0);
	}
	setorigin(self, spot);
	self.angles_y = vectoyaw((self.enemy.origin - spot));
	self.fixangle = TRUE;
	return (TRUE);
};

void(entity beacon, float attack) PM_WizBlink =
{
	local vector org;

	org = self.origin;
	if (PM_WizTeleport(beacon, attack))
	{
		spawn_wizard_fog(org);
		spawn_wizard_fog(self.origin);
		self.has_fired = 1;
	}
};

void() PM_WizMultiBlink =
{
	local vector org;
	local float success;

	org = self.origin;
	success = 0;
	success = success + PM_WizTeleport(self, FALSE);
	if (success)
	{
		spawn_wizard_fog(org);
		spawn_wizard_fog(self.origin);
		self.has_fired = 1;
	}
};

void() wiz_stand1 = [ 0, wiz_stand2 ]
{
	ai_stand();
};

void() wiz_stand2 = [ 1, wiz_stand3 ]
{
	ai_stand();
};

void() wiz_stand3 = [ 2, wiz_stand4 ]
{
	ai_stand();
};

void() wiz_stand4 = [ 3, wiz_stand5 ]
{
	ai_stand();
};

void() wiz_stand5 = [ 4, wiz_stand6 ]
{
	ai_stand();
};

void() wiz_stand6 = [ 5, wiz_stand7 ]
{
	ai_stand();
};

void() wiz_stand7 = [ 6, wiz_stand8 ]
{
	ai_stand();
};

void() wiz_stand8 = [ 7, wiz_stand9 ]
{
	ai_stand();
};

void() wiz_stand9 = [ 8, wiz_stand10 ]
{
	ai_stand();
};

void() wiz_stand10 = [ 9, wiz_stand11 ]
{
	ai_stand();
};

void() wiz_stand11 = [ 10, wiz_stand12 ]
{
	ai_stand();
};

void() wiz_stand12 = [ 11, wiz_stand13 ]
{
	ai_stand();
};

void() wiz_stand13 = [ 12, wiz_stand14 ]
{
	ai_stand();
};

void() wiz_stand14 = [ 13, wiz_stand15 ]
{
	ai_stand();
};

void() wiz_stand15 = [ 14, wiz_stand1 ]
{
	ai_stand();
};

void() wiz_walk1 = [ 0, wiz_walk2 ]
{
	ai_walk(8);
	Wiz_idlesound();
};

void() wiz_walk2 = [ 1, wiz_walk3 ]
{
	ai_walk(8);
};

void() wiz_walk3 = [ 2, wiz_walk4 ]
{
	ai_walk(8);
};

void() wiz_walk4 = [ 3, wiz_walk5 ]
{
	ai_walk(8);
};

void() wiz_walk5 = [ 4, wiz_walk6 ]
{
	ai_walk(8);
};

void() wiz_walk6 = [ 5, wiz_walk7 ]
{
	ai_walk(8);
};

void() wiz_walk7 = [ 6, wiz_walk8 ]
{
	ai_walk(8);
};

void() wiz_walk8 = [ 7, wiz_walk9 ]
{
	ai_walk(8);
};

void() wiz_walk9 = [ 8, wiz_walk10 ]
{
	ai_stand();
};

void() wiz_walk10 = [ 9, wiz_walk11 ]
{
	ai_stand();
};

void() wiz_walk11 = [ 10, wiz_walk12 ]
{
	ai_stand();
};

void() wiz_walk12 = [ 11, wiz_walk13 ]
{
	ai_stand();
};

void() wiz_walk13 = [ 12, wiz_walk14 ]
{
	ai_stand();
};

void() wiz_walk14 = [ 13, wiz_walk15 ]
{
	ai_stand();
};

void() wiz_walk15 = [ 14, wiz_walk1 ]
{
	ai_stand();
};

void() wiz_side1 = [ 0, wiz_side2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
	Wiz_idlesound();
	self.has_fired = 0;
};

void() wiz_side2 = [ 1, wiz_side3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side3 = [ 2, wiz_side4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side4 = [ 3, wiz_side5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side5 = [ 4, wiz_side6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side6 = [ 5, wiz_side7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side7 = [ 6, wiz_side8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_side8 = [ 7, wiz_side1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(8);
};

void() wiz_run1 = [ 15, wiz_run2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
	Wiz_idlesound();
	self.has_fired = 0;
	if (autocvar_wizardteleport)
	{
		if ((random() < (skill * 0.01)))
		{
			PM_WizBlink(self.enemy, FALSE);
		}
	}
};

void() wiz_run2 = [ 16, wiz_run3 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run3 = [ 17, wiz_run4 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run4 = [ 18, wiz_run5 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run5 = [ 19, wiz_run6 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run6 = [ 20, wiz_run7 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run7 = [ 21, wiz_run8 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run8 = [ 22, wiz_run9 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run9 = [ 23, wiz_run10 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run10 = [ 24, wiz_run11 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run11 = [ 25, wiz_run12 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run12 = [ 26, wiz_run13 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run13 = [ 27, wiz_run14 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_run14 = [ 28, wiz_run1 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_run_animation_speed_factor * 0.001));
	ai_run(16);
};

void() wiz_fast1 = [ 29, wiz_fast2 ]
{
	self.nextthink = ((time + 0.1) - (autocvar_monster_rangedattack_animation_speed_factor * 0.001));
	ai_face();
	Wiz_StartFast();
};

void() wiz_fast2 = [ 30, wiz_fast3 ]
{
	ai_face();
};

void() wiz_fast3 = [ 31, wiz_fast4 ]
{
	ai_face();
};

void() wiz_fast4 = [ 32, wiz_fast5 ]
{
	ai_face();
	if ((autocvar_wizardteleport && (skill > 1)))
	{
		if ((random() <= 0.05))
		{
			PM_WizBlink(self, TRUE);
		}
	}
};

void() wiz_fast5 = [ 33, wiz_fast6 ]
{
	ai_face();
};

void() wiz_fast6 = [ 34, wiz_fast7 ]
{
	ai_face();
};

void() wiz_fast7 = [ 33, wiz_fast8 ]
{
	ai_face();
};

void() wiz_fast8 = [ 32, wiz_fast9 ]
{
	ai_face();
};

void() wiz_fast9 = [ 31, wiz_fast10 ]
{
	ai_face();
};

void() wiz_fast10 = [ 30, wiz_run1 ]
{
	ai_face();
	if (autocvar_skill_adjusted_monster_rangedattack_frequence)
	{
		if ((skill == 0))
		{
			SUB_AttackFinished(2);
		}
		else
		{
			if ((skill == 1))
			{
				SUB_AttackFinished(1.5);
			}
			else
			{
				if ((skill == 2))
				{
					SUB_AttackFinished(1);
				}
				else
				{
					SUB_AttackFinished(2);
				}
			}
		}
	}
	else
	{
		SUB_AttackFinished(2);
	}
	WizardAttackFinished();
};

void() wiz_pain1 = [ 42, wiz_pain2 ]
{
	self.has_fired = 1;
	self.nextthink = (time + 0.14);
};

void() wiz_pain2 = [ 43, wiz_pain3 ]
{
	self.nextthink = (time + 0.14);
};

void() wiz_pain3 = [ 44, wiz_pain4 ]
{
	self.nextthink = (time + 0.14);
};

void() wiz_pain4 = [ 45, wiz_run1 ]
{
	self.nextthink = (time + 0.14);
};

void() soulcall_wizard =
{
	local float zet;

	zet = 25;
	if ((random() < 0.002))
	{
		soul("progs/afrit.mdl", 64, 27.451);
	}
	else
	{
		if ((self.monstermodel == 0))
		{
			soul("progs/wizard.mdl", 53, zet);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				soul("progs/wizard1.mdl", 53, zet);
			}
		}
	}
};

void() vengeancecall_wizard =
{
	vengeance_wizard("progs/wizard.mdl", 53);
};

void() wizard_death_touch =
{
	local float zufall;

	if ((self.flags & FL_ONGROUND))
	{
		self.solid = 0;
		if ((self.model != "progs/wizardblast.mdl"))
		{
		}
		pointparticles(particleeffectnum(/*55569i*/"wizard_falling_dust"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_AUTO, "zombie/z_hit.wav", 0.8, ATTN_NORM, SNDSPD);
		wiz_death8();
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.78))
			{
				self.think = ghost_die;
				self.nextthink = (time + 1);
			}
			else
			{
				if ((zufall < 0.26))
				{
					self.think = soulcall_wizard;
					self.nextthink = (time + 1);
				}
				else
				{
					self.think = vengeancecall_wizard;
					self.nextthink = (time + 1);
				}
			}
		}
		return;
	}
	else
	{
		if ((self.velocity == VEC_ORIGIN))
		{
			self.solid = 0;
			if ((self.model != "progs/wizardblast.mdl"))
			{
			}
			pointparticles(particleeffectnum(/*55569i*/"wizard_falling_dust"), self.origin, VEC_ORIGIN, 1);
			sound(self, CHAN_AUTO, "zombie/z_hit.wav", 0.8, ATTN_NORM, SNDSPD);
			wiz_death8();
			if ((self.grimrock_helper == 1))
			{
				zufall = random();
				if ((zufall > 0.78))
				{
					self.think = ghost_die;
					self.nextthink = (time + 1);
				}
				else
				{
					if ((zufall < 0.26))
					{
						self.think = soulcall_wizard;
						self.nextthink = (time + 1);
					}
					else
					{
						self.think = vengeancecall_wizard;
						self.nextthink = (time + 1);
					}
				}
			}
			return;
		}
	}
	if ((self.origin == self.old_origin))
	{
		self.solid = 0;
		if ((self.model != "progs/wizardblast.mdl"))
		{
		}
		pointparticles(particleeffectnum(/*55569i*/"wizard_falling_dust"), self.origin, VEC_ORIGIN, 1);
		sound(self, CHAN_AUTO, "zombie/z_hit.wav", 0.8, ATTN_NORM, SNDSPD);
		wiz_death8();
		if ((self.grimrock_helper == 1))
		{
			zufall = random();
			if ((zufall > 0.78))
			{
				self.think = ghost_die;
				self.nextthink = (time + 1);
			}
			else
			{
				if ((zufall < 0.26))
				{
					self.think = soulcall_wizard;
					self.nextthink = (time + 1);
				}
				else
				{
					self.think = vengeancecall_wizard;
					self.nextthink = (time + 1);
				}
			}
		}
		return;
	}
	self.old_origin = self.origin;
	self.think = wizard_death_touch;
	self.nextthink = (time + 0.001);
};

void() wiz_dieburn1 = [ 46, wiz_dieburn2 ]
{
	self.burnz_origin = 12;
	burn_toggle_allround();
	sound7(self, CHAN_VOICE, "wizard/wdeath.wav", 1, ATTN_NORM, SNDSPD);
};

void() wiz_dieburn2 = [ 47, wiz_dieburn3 ]
{
	self.burnz_origin = 11;
};

void() wiz_dieburn3 = [ 48, wiz_dieburn4 ]
{
	self.burnz_origin = 6;
	self.solid = 0;
};

void() wiz_dieburn4 = [ 49, wiz_dieburn5 ]
{
	self.burnz_origin = 3;
};

void() wiz_dieburn5 = [ 50, wiz_dieburn6 ]
{
	self.burnz_origin = 0;
};

void() wiz_dieburn6 = [ 51, wiz_dieburn7 ]
{
	self.burnz_origin = -2;
};

void() wiz_dieburn7 = [ 52, wiz_dieburn8 ]
{
	self.burnz_origin = -4;
};

void() wiz_dieburn8 = [ 53, wiz_dieburn8 ]
{
	self.burnz_origin = -6;
};

void() wiz_death1 = [ 46, wiz_death2 ]
{
	if ((self.scale != 1))
	{
		self.sizefactor_x = 0;
		self.sizefactor_y = 0;
		self.sizefactor_z = ((self.scale - 1) * 25);
		setsize(self, (VEC_HULL_MIN - self.sizefactor), ('16 16 40' - self.sizefactor));
	}
	self.velocity_x = (-200 + (400 * random()));
	self.velocity_y = (-200 + (400 * random()));
	self.velocity_z = (100 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	sound7(self, CHAN_VOICE, "wizard/wdeath.wav", 1, ATTN_NORM, SNDSPD);
};

void() wiz_death2 = [ 47, wiz_death3 ]
{
};

void() wiz_death3 = [ 48, wiz_death4 ]
{
};

void() wiz_death4 = [ 49, wiz_death5 ]
{
};

void() wiz_death5 = [ 50, wiz_death6 ]
{
};

void() wiz_death6 = [ 51, wiz_death7 ]
{
	wizard_death_touch();
};

void() wiz_death7 = [ 52, wiz_death8 ]
{
};

void() wiz_death8 = [ 53, wiz_death8 ]
{
	if ((self.inflamed == 1))
	{
		inflamed_die();
		return;
	}
	if ((autocvar_wizardcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	if ((self.monstermodel == 0))
	{
		CopyMonsterToBodyQue(autocvar_wizardcorpsehealth, "progs/h_wizard.mdl");
	}
	if ((self.monstermodel == 1))
	{
		CopyMonsterToBodyQue(autocvar_wizardcorpsehealth, "progs/h_wizard1.mdl");
	}
	if ((self.nodeathanim == 1))
	{
		return;
	}
};

void() wiz_diessg1 = [ 54, wiz_diessg2 ]
{
	if ((self.scale != 1))
	{
		self.sizefactor_x = 0;
		self.sizefactor_y = 0;
		self.sizefactor_z = ((self.scale - 1) * 25);
		setsize(self, (VEC_HULL_MIN - self.sizefactor), ('16 16 40' - self.sizefactor));
	}
	self.velocity_x = (-200 + (400 * random()));
	self.velocity_y = (-200 + (400 * random()));
	self.velocity_z = (100 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
	sound7(self, CHAN_VOICE, "player/gibsplit.wav", 1, ATTN_NORM, SNDSPD);
};

void() wiz_diessg2 = [ 55, wiz_diessg3 ]
{
	self.solid = 0;
};

void() wiz_diessg3 = [ 56, wiz_diessg4 ]
{
};

void() wiz_diessg4 = [ 57, wiz_diessg5 ]
{
};

void() wiz_diessg5 = [ 58, wiz_diessg6 ]
{
};

void() wiz_diessg6 = [ 59, wiz_diessg7 ]
{
};

void() wiz_diessg7 = [ 60, wiz_diessg8 ]
{
};

void() wiz_diessg8 = [ 61, wiz_diessg9 ]
{
};

void() wiz_diessg9 = [ 62, wiz_diessg10 ]
{
};

void() wiz_diessg10 = [ 63, wiz_diessg11 ]
{
};

void() wiz_diessg11 = [ 64, wiz_diessg12 ]
{
};

void() wiz_diessg12 = [ 65, wiz_diessg13 ]
{
};

void() wiz_diessg13 = [ 66, wiz_diessg14 ]
{
};

void() wiz_diessg14 = [ 67, wiz_diessg15 ]
{
};

void() wiz_diessg15 = [ 68, wiz_diessg16 ]
{
};

void() wiz_diessg16 = [ 69, wiz_diessg17 ]
{
};

void() wiz_diessg17 = [ 70, wiz_diessg18 ]
{
};

void() wiz_diessg18 = [ 71, wiz_diessg19 ]
{
};

void() wiz_diessg19 = [ 72, wiz_diessg20 ]
{
};

void() wiz_diessg20 = [ 73, wiz_diessg21 ]
{
};

void() wiz_diessg21 = [ 74, wiz_diessg22 ]
{
};

void() wiz_diessg22 = [ 75, wiz_diessg23 ]
{
};

void() wiz_diessg23 = [ 76, wiz_diessg24 ]
{
};

void() wiz_diessg24 = [ 77, wiz_diessg25 ]
{
};

void() wiz_diessg25 = [ 78, wiz_diessg26 ]
{
};

void() wiz_diessg26 = [ 79, wiz_diessg27 ]
{
};

void() wiz_diessg27 = [ 80, wiz_diessg28 ]
{
};

void() wiz_diessg28 = [ 81, wiz_diessg29 ]
{
};

void() wiz_diessg29 = [ 82, wiz_diessg29 ]
{
	if ((autocvar_wizardcorpseburnable == 1))
	{
		self.burnable_corpse = 1;
	}
	self.delete_painskin = 1;
	CopyMonsterToBodyQue(autocvar_wizardcorpsehealth, "progs/gib_wztail.mdl");
};

void(float maxgibs, float gibscounter) producegibs_wizard =
{
	if ((gibscounter >= maxgibs))
	{
		ThrowGib("progs/gib_wzarm1.mdl", self.health);
		ThrowGib("progs/gib_wzarm2.mdl", self.health);
		ThrowGib("progs/gib_wztail.mdl", self.health);
		ThrowGib("progs/gib_4.mdl", self.health);
		return;
	}
	gibscounter = gibscounter + 1;
	producegibs_wizard(maxgibs, gibscounter);
};

void() wizard_coal_touch =
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
	if ((self.origin == self.old_origin))
	{
		self.solid = 0;
		baked_explode();
		return;
	}
	self.old_origin = self.origin;
	self.think = wizard_coal_touch;
	self.nextthink = (time + 0.001);
};

void() wizard_lightning_death = [ 44, wizard_lightning_death1 ]
{
	self.delete_painskin = 1;
	if ((autocvar_lightninggun_death_animation == 2))
	{
		self.movetype = 0;
		self.velocity = VEC_ORIGIN;
		lightninggun_death_fade();
		return;
	}
	self.velocity_x = (-200 + (400 * random()));
	self.velocity_y = (-200 + (400 * random()));
	self.velocity_z = (100 + (100 * random()));
	self.flags = (self.flags - (self.flags & FL_ONGROUND));
};

void() wizard_lightning_death1 = [ 44, wizard_lightning_death1 ]
{
	self.touch = wizard_coal_touch;
	self.baked = 1;
	self.colormod = '0.25 0.22 0.22';
};

void() wiz_inflamed1 = [ 0, wiz_inflamed2 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
	if ((random() < 0.75))
	{
		sound7(self, CHAN_VOICE, "wizard/wpain.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() wiz_inflamed2 = [ 1, wiz_inflamed3 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed3 = [ 2, wiz_inflamed4 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed4 = [ 3, wiz_inflamed5 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed5 = [ 4, wiz_inflamed6 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed6 = [ 5, wiz_inflamed7 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed7 = [ 6, wiz_inflamed8 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
};

void() wiz_inflamed8 = [ 7, wiz_inflamed1 ]
{
	ai_run_inflamed(16);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		wiz_die();
		return;
	}
	if ((random() < 0.5))
	{
		wiz_inflamed9();
	}
};

void() wiz_inflamed9 = [ 42, wiz_inflamed10 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.08);
	if ((random() < 0.8))
	{
		sound7(self, CHAN_VOICE, "wizard/wpain.wav", 1, ATTN_NORM, SNDSPD);
	}
};

void() wiz_inflamed10 = [ 43, wiz_inflamed11 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.08);
};

void() wiz_inflamed11 = [ 44, wiz_inflamed12 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.08);
};

void() wiz_inflamed12 = [ 45, wiz_inflamed13 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.08);
};

void() wiz_inflamed13 = [ 43, wiz_inflamed1 ]
{
	ai_run_inflamed(10);
	self.nextthink = (time + 0.07);
	if ((self.inflametime < time))
	{
		wiz_die();
		return;
	}
};

void() wiz_die =
{
	local float maxgibs;
	local float gibscounter;
	local float zufa;
	local float randomness;

	self.has_fired = 1;
	if (autocvar_lightninggun_death_animation)
	{
		if (((self.enemy.weapon == IT_LIGHTNING) && (self.enemy.meleeing == 0)))
		{
			wizard_lightning_death();
			return;
		}
	}
	else
	{
		if ((((!self.shocked && (self.enemy.weapon == IT_LIGHTNING)) && (self.enemy.meleeing == 0)) && (self.sticky != 1)))
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
	if ((random() < 0.85))
	{
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1);
	}
	if ((((self.health < -35) || (random() < 0.1)) || ((self.enemy.weapon == IT_CHAINSAW) && (random() < 0.7))))
	{
		self.delete_painskin = 1;
		gibbed_monsters = gibbed_monsters + 1;
		if ((autocvar_slowmotion >= 1))
		{
			if ((random() <= (autocvar_slowmotion_randomness_wizard * 0.01)))
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
		if ((self.monstermodel == 0))
		{
			ThrowHead("progs/h_wizard.mdl", self.health);
		}
		else
		{
			if ((self.monstermodel == 1))
			{
				ThrowHead("progs/h_wizard1.mdl", self.health);
			}
		}
		if ((autocvar_heartgib >= 1))
		{
			ThrowHeart("progs/gibheart.mdl", self.health);
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		gibdeath_effects();
		producegibs_wizard(maxgibs, gibscounter);
		return;
	}
	if (autocvar_burning_monsters_death_animation)
	{
		if ((self.inflamed == 0))
		{
			zufa = random() * 110;
			if ((((((self.enemy.weapon == IT_GRENADE_LAUNCHER) || (self.enemy.weapon == IT_ROCKET_LAUNCHER)) && (zufa <= autocvar_burning_monsters_death_animation)) && (self.watertype != CONTENT_WATER)) && (self.enemy.meleeing == 0)))
			{
				self.delete_painskin = 1;
				self.flags = (self.flags | FL_FLY);
				self.inflamed = 1;
				self.traileffectnum = particleeffectnum(/*23479i*/"burning_monster");
				self.inflametime = ((time + autocvar_burning_monsters_death_animation_time) + random());
				wiz_inflamed1();
				return;
			}
		}
		else
		{
			self.flags = (self.flags - (self.flags & FL_FLY));
			wiz_death1();
			return;
		}
	}
	autocvar_wizardrandomness = autocvar_wizardrandomness * 0.01;
	if ((autocvar_wizard == 4))
	{
		randomness = random();
		if ((randomness <= autocvar_wizardrandomness))
		{
			self.delete_painskin = 1;
			wiz_dieburn1();
			return;
		}
	}
	if ((autocvar_slowmotion >= 3))
	{
		if ((random() <= (autocvar_slowmotion_randomness_wizard * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	wiz_death1();
	if ((self.enemy.meleeing == 0))
	{
		if ((((self.enemy.weapon == IT_SUPER_SHOTGUN) || (self.enemy.weapon == IT_SUPER_NAILGUN)) || (self.enemy.weapon == IT_CHAINSAW)))
		{
			if ((random() <= 0.5))
			{
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*15151i*/"blood_monster_gib"), self.origin, VEC_ORIGIN, 1);
				}
				ThrowGib("progs/gib_wzarm1.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				ThrowGib("progs/chop.mdl", self.health);
				self.delete_painskin = 1;
				self.model = "progs/wizardblast.mdl";
				setmodel(self, "progs/wizardblast.mdl");
				wiz_diessg1();
				return;
			}
		}
		if (((self.enemy.weapon == IT_NAILGUN) || (self.enemy.weapon == IT_SUPER_NAILGUN)))
		{
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			ThrowGib("progs/chop.mdl", self.health);
			self.delete_painskin = 1;
			self.model = "progs/wizard_nail.mdl";
			setmodel(self, "progs/wizard_nail.mdl");
			wiz_death1();
			sound7(self, CHAN_AUTO, "player/axeflesh3.wav", 1, ATTN_IDLE, SNDSPD);
			sound7(self, CHAN_VOICE, "soldier/decap.wav", 1, ATTN_IDLE, SNDSPD);
		}
		setsize(self, VEC_HULL_MIN, VEC_HULL_MAX);
	}
};

void(entity attacker, float damage) Wiz_Pain =
{
	sound7(self, CHAN_VOICE, "wizard/wpain.wav", 1, ATTN_NORM, SNDSPD);
	if ((autocvar_wizardteleport && (skill > 1)))
	{
		random();
		if ((random() < (0.05 + (skill * 0.01))))
		{
			PM_WizMultiBlink();
		}
	}
	if ((((random() * 60) > damage) && (damage != autocvar_player_axe)))
	{
		return;
	}
	if ((autocvar_slowmotion >= 4))
	{
		if ((random() <= (autocvar_slowmotion_randomness_wizard * 0.01)))
		{
			the_matrix = 1;
			matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
		}
	}
	wiz_pain1();
};

void() Wiz_Missile =
{
	if ((self.has_fired == 0))
	{
		wiz_fast1();
	}
};

void() monster_wizard =
{
	local float zufall;
	local float zuffa;
	local float replaceer;
	local float replacer;
	local entity pain_skin_entity;
	local float replacee;
	local float replace;

	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.has_fired = 0;
	precache_model("progs/wizard.mdl");
	precache_model("progs/h_wizard.mdl");
	precache_model("progs/w_spike.mdl");
	precachegibs_wiz();
	precache_sound("wizard/hit.wav");
	precache_sound("wizard/wattack.wav");
	precache_sound("wizard/wdeath.wav");
	precache_sound("wizard/widle1.wav");
	precache_sound("wizard/widle2.wav");
	precache_sound("wizard/wpain.wav");
	precache_sound("wizard/wsight.wav");
	precache_sound("zombie/z_hit.wav");
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	self.netname = "monster_wizard";
	if ((autocvar_wizardmultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/wizard.mdl");
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
		if ((autocvar_wizardmultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/wizard1.mdl");
			precache_model("progs/h_wizard1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/wizard.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/wizard1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_wizardmultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/wizard1.mdl");
				precache_model("progs/h_wizard1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/wizard.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/wizard.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/wizard1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_wizardmultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/wizard1.mdl");
					precache_model("progs/h_wizard1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/wizard.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/wizard.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/wizard1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/wizard1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/wizard.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	if ((autocvar_wizard_size == 1))
	{
		zuffa = random();
		if ((zuffa <= 0.33))
		{
			self.scale = 1.14;
		}
		else
		{
			if ((zuffa <= 0.66))
			{
				self.scale = 1.07;
			}
			else
			{
				self.scale = 1;
			}
		}
	}
	else
	{
		if ((autocvar_wizard_size == 2))
		{
			zuffa = random();
			if ((zuffa <= 0.25))
			{
				self.scale = 1.21;
			}
			else
			{
				if ((zuffa <= 0.5))
				{
					self.scale = 1.14;
				}
				else
				{
					if ((zuffa <= 0.75))
					{
						self.scale = 1.07;
					}
					else
					{
						self.scale = 1;
					}
				}
			}
		}
		else
		{
			if ((autocvar_wizard_size == 3))
			{
				zuffa = random();
				if ((zuffa <= 0.2))
				{
					self.scale = 1.28;
				}
				else
				{
					if ((zuffa <= 0.4))
					{
						self.scale = 1.21;
					}
					else
					{
						if ((zuffa <= 0.6))
						{
							self.scale = 1.14;
						}
						else
						{
							if ((zuffa <= 0.8))
							{
								self.scale = 1.07;
							}
							else
							{
								self.scale = 1;
							}
						}
					}
				}
			}
			else
			{
				if ((autocvar_wizard_size == 4))
				{
					zuffa = random();
					if ((zuffa <= 0.17))
					{
						self.scale = 1.35;
					}
					else
					{
						if ((zuffa <= 0.34))
						{
							self.scale = 1.28;
						}
						else
						{
							if ((zuffa <= 0.5))
							{
								self.scale = 1.21;
							}
							else
							{
								if ((zuffa <= 0.67))
								{
									self.scale = 1.14;
								}
								else
								{
									if ((zuffa <= 0.84))
									{
										self.scale = 1.07;
									}
									else
									{
										self.scale = 1;
									}
								}
							}
						}
					}
				}
				else
				{
					if ((autocvar_wizard_size > 4))
					{
						if ((autocvar_wizard_size > 40))
						{
							self.origin = (self.origin + '0 0 10');
						}
						self.scale = (1 + (autocvar_wizard_size * 0.01));
						self.sizefactor_x = 0;
						self.sizefactor_y = 0;
						self.sizefactor_z = (autocvar_wizard_size * 0.25);
					}
					else
					{
						self.scale = 1;
					}
				}
			}
		}
	}
	setsize(self, VEC_HULL_MIN, '16 16 40');
	if ((autocvar_wizard_size_influenced_health == 1))
	{
		self.health = (autocvar_wizard_health + ((self.scale - 1) * 100));
	}
	else
	{
		self.health = autocvar_wizard_health;
	}
	self.health_initial = self.health;
	if ((autocvar_monster_random_skin_color_alteration && autocvar_wizard_random_skin_colors))
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
	self.cansplash = TRUE;
	self.th_stand = wiz_stand1;
	self.th_walk = wiz_walk1;
	self.th_run = wiz_run1;
	self.th_missile = Wiz_Missile;
	self.th_pain = Wiz_Pain;
	self.th_die = wiz_die;
	self.alpha = (autocvar_monstertransparency * 0.01);
	if (autocvar_reiver_replace_wizard)
	{
		replaceer = autocvar_reiver_replace_wizard * 0.01;
		if ((random() <= replaceer))
		{
			self.health = (autocvar_wizard_health + 40);
			self.scale = 1;
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_reiver_start();
			return;
		}
	}
	if (autocvar_afrit_replace_wizard)
	{
		replacer = autocvar_afrit_replace_wizard * 0.01;
		if ((random() <= replacer))
		{
			self.health = (autocvar_wizard_health + 25);
			self.scale = 1;
			self.nextthink = (time + 0.3);
			self.think = SUB_Remove;
			monster_afrit_start();
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
	do_the_cloning__fly_swim();
	if (autocvar_reiver_supports_wizard)
	{
		replacee = autocvar_reiver_supports_wizard * 0.01;
		if ((random() <= replacee))
		{
			add_reiver_support_fly();
		}
	}
	if (autocvar_afrit_supports_wizard)
	{
		replace = autocvar_afrit_supports_wizard * 0.01;
		if ((cvar("quadreplacer") > 0))
		{
			replace = replace + 0.01;
		}
		if ((random() <= replace))
		{
			add_afrit_support_fly();
		}
	}
	MonsterPhysics(self, autocvar_wizardmass);
};

void() vengeance_wizard_end1 =
{
	self.alpha = -1;
	te_customflash(self.origin, 500, 0.7, '1 0 0');
	self.nextthink = (time + 0.2);
	self.think = SUB_Remove;
};

void() vengeance_wizard_touch =
{
	local float ldmg;

	ldmg = rint((0.5 + (3 * random())));
	T_Damage(self.enemy, self, self, ldmg);
	self.touch = SUB_Null;
	self.think = vengeance_wizard_end1;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull =
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

void() vengeance_wizard_fly1 = [ 15, vengeance_wizard_fly2 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_fly2 = [ 16, vengeance_wizard_fly3 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.36;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_fly3 = [ 17, vengeance_wizard_fly4 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.32;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_fly4 = [ 18, vengeance_wizard_fly5 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.28;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_fly5 = [ 19, vengeance_wizard_fly6 ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.24;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_fly6 = [ 20, vengeance_wizard_random ]
{
	ai_face();
	movetogoal(23);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_kamikaze1 = [ 21, vengeance_wizard_kamikaze2 ]
{
	ai_face();
	movetogoal(25);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.17;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_kamikaze2 = [ 22, vengeance_wizard_kamikaze3 ]
{
	ai_face();
	movetogoal(25);
	if ((autocvar_quadreplacer != 0))
	{
		ai_melee();
	}
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_kamikaze3 = [ 23, vengeance_wizard_kamikaze4 ]
{
	sound7(self, CHAN_VOICE, "vengeance/wizattack.wav", 1, 4);
	ai_face();
	movetogoal(25);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.13;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_kamikaze4 = [ 24, vengeance_wizard_kamikaze5 ]
{
	ai_face();
	movetogoal(25);
	if ((autocvar_quadreplacer != 0))
	{
		ai_melee();
	}
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.11;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_kamikaze5 = [ 25, vengeance_wizard_end1 ]
{
	ai_face();
	movetogoal(25);
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.07;
	self.glow_color = 75;
	self.glow_size = 600;
	if ((((random() < 0.65) || (self.has_fired == 20)) && (self.has_fired < 27)))
	{
		self.has_fired = (self.has_fired + 1);
		vengeance_wizard_kamikaze1();
	}
	if ((autocvar_quadreplacer != 0))
	{
		ai_melee();
	}
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull1 = [ 32, vengeance_wizard_skull2 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull2 = [ 33, vengeance_wizard_skull3 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull3 = [ 34, vengeance_wizard_skull4 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull4 = [ 35, vengeance_wizard_skull5 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull5 = [ 36, vengeance_wizard_skull6 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull6 = [ 37, vengeance_wizard_skull7 ]
{
	sound7(self, CHAN_VOICE, "wizard/wpain.wav", 1, 4);
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_skull7 = [ 37, vengeance_wizard_end1 ]
{
	ai_face();
	self.touch = vengeance_wizard_touch;
	self.alpha = 0.15;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
	vengeance_wizard_skull();
};

void() vengeance_wizard_random =
{
	self.alpha = 0.2;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.01);
	self.has_fired = 20;
	self.think = vengeance_wizard_kamikaze1;
};

void() vengeance_wizard1 = [ 52, vengeance_wizard2 ]
{
	self.origin_z = (self.origin_z + 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard2 = [ 51, vengeance_wizard3 ]
{
	self.origin_z = (self.origin_z + 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard3 = [ 50, vengeance_wizard4 ]
{
	self.origin_z = (self.origin_z + 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard4 = [ 49, vengeance_wizard5 ]
{
	self.origin_z = (self.origin_z + 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard5 = [ 48, vengeance_wizard6 ]
{
	sound7(self, CHAN_WEAPON, "wizard/wsight.wav", 1, 4);
	self.origin_z = (self.origin_z + 2);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard6 = [ 47, vengeance_wizard7 ]
{
	self.origin_z = (self.origin_z + 3);
	self.flags = (self.flags - FL_ONGROUND);
	self.flags = (self.flags | FL_FLY);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard7 = [ 46, vengeance_wizard_fly1 ]
{
	self.origin_z = (self.origin_z + 3);
	self.alpha = 0.4;
	self.glow_color = 75;
	self.glow_size = 600;
	self.nextthink = (time + 0.1);
};

void() vengeance_wizard_bright05 =
{
	self.alpha = 0.3;
	self.colormod = '6 1 1';
	self.glow_color = 75;
	self.glow_size = 450;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard1;
};

void() vengeance_wizard_bright04 =
{
	self.alpha = 0.3;
	self.colormod = '5 1 1';
	self.glow_color = 75;
	self.glow_size = 350;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard_bright05;
};

void() vengeance_wizard_bright03 =
{
	self.alpha = 0.3;
	self.colormod = '4 1 1';
	self.glow_color = 75;
	self.glow_size = 270;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard_bright04;
};

void() vengeance_wizard_bright02 =
{
	self.alpha = 0.3;
	self.colormod = '3 1 1';
	self.glow_color = 75;
	self.glow_size = 185;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard_bright03;
};

void() vengeance_wizard_bright01 =
{
	self.alpha = 0.3;
	self.colormod = '2 1 1';
	self.glow_color = 75;
	self.glow_size = 100;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard_bright02;
};

void() vengeance_wizard_bright00 =
{
	self.alpha = 0.3;
	self.glow_color = 75;
	self.glow_size = 10;
	self.nextthink = (time + 0.1);
	self.think = vengeance_wizard_bright01;
};

void(string modelname, float modelframe) vengeance_wizard =
{
	local vector v;

	v_x = self.origin_x;
	precache_sound("vengeance/wizattack.wav");
	precache_model("progs/skull.mdl");
	self.origin = v;
	self.touch = SUB_Null;
	self.movetype = MOVETYPE_NOCLIP;
	self.inflamed = 0;
	if ((self.monstermodel == 0))
	{
		setmodel(self, "progs/wizard.mdl");
	}
	else
	{
		if ((self.monstermodel == 1))
		{
			setmodel(self, "progs/wizard1.mdl");
		}
	}
	setsize(self, '-16 -16 -4', '16 16 4');
	self.frame = modelframe;
	self.solid = 0;
	vengeance_wizard_bright00();
};
