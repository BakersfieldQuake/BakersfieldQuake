//Decompiled code. Please respect the original copyright.

void() hydra_stand1 = [ 45, hydra_stand2 ]
{
	ai_stand();
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, "hydra/hydra_idle2.wav", 1, ATTN_NORM);
	}
};

void() hydra_stand2 = [ 46, hydra_stand3 ]
{
	ai_stand();
};

void() hydra_stand3 = [ 47, hydra_stand4 ]
{
	ai_stand();
};

void() hydra_stand4 = [ 48, hydra_stand5 ]
{
	ai_stand();
};

void() hydra_stand5 = [ 49, hydra_stand6 ]
{
	ai_stand();
};

void() hydra_stand6 = [ 50, hydra_stand7 ]
{
	ai_stand();
};

void() hydra_stand7 = [ 51, hydra_stand8 ]
{
	ai_stand();
};

void() hydra_stand8 = [ 52, hydra_stand9 ]
{
	ai_stand();
};

void() hydra_stand9 = [ 53, hydra_stand10 ]
{
	ai_stand();
};

void() hydra_stand10 = [ 54, hydra_stand11 ]
{
	ai_stand();
};

void() hydra_stand11 = [ 55, hydra_stand12 ]
{
	ai_stand();
};

void() hydra_stand12 = [ 56, hydra_stand13 ]
{
	ai_stand();
};

void() hydra_stand13 = [ 57, hydra_stand14 ]
{
	ai_stand();
};

void() hydra_stand14 = [ 58, hydra_stand15 ]
{
	ai_stand();
};

void() hydra_stand15 = [ 59, hydra_stand16 ]
{
	ai_stand();
};

void() hydra_stand16 = [ 60, hydra_stand17 ]
{
	ai_stand();
};

void() hydra_stand17 = [ 61, hydra_stand18 ]
{
	ai_stand();
};

void() hydra_stand18 = [ 62, hydra_stand1 ]
{
	ai_stand();
};

void() hydra_walk1 = [ 45, hydra_walk2 ]
{
	ai_walk(8);
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, "hydra/hydra_idle2.wav", 1, ATTN_NORM);
	}
};

void() hydra_walk2 = [ 46, hydra_walk3 ]
{
	ai_walk(8);
};

void() hydra_walk3 = [ 47, hydra_walk4 ]
{
	ai_walk(8);
};

void() hydra_walk4 = [ 48, hydra_walk5 ]
{
	ai_walk(8);
};

void() hydra_walk5 = [ 49, hydra_walk6 ]
{
	ai_walk(8);
};

void() hydra_walk6 = [ 50, hydra_walk7 ]
{
	ai_walk(8);
};

void() hydra_walk7 = [ 51, hydra_walk8 ]
{
	ai_walk(8);
};

void() hydra_walk8 = [ 52, hydra_walk9 ]
{
	ai_walk(8);
};

void() hydra_walk9 = [ 53, hydra_walk10 ]
{
	ai_walk(8);
};

void() hydra_walk10 = [ 54, hydra_walk11 ]
{
	ai_walk(8);
};

void() hydra_walk11 = [ 55, hydra_walk12 ]
{
	ai_walk(8);
};

void() hydra_walk12 = [ 56, hydra_walk13 ]
{
	ai_walk(8);
};

void() hydra_walk13 = [ 57, hydra_walk14 ]
{
	ai_walk(8);
};

void() hydra_walk14 = [ 58, hydra_walk15 ]
{
	ai_walk(8);
};

void() hydra_walk15 = [ 59, hydra_walk16 ]
{
	ai_walk(8);
};

void() hydra_walk16 = [ 60, hydra_walk17 ]
{
	ai_walk(8);
};

void() hydra_walk17 = [ 61, hydra_walk18 ]
{
	ai_walk(8);
};

void() hydra_walk18 = [ 62, hydra_walk1 ]
{
	ai_walk(8);
};

void() hydra_run1 = [ 45, hydra_run2 ]
{
	ai_run(13);
	if ((random() < 0.5))
	{
		sound(self, CHAN_VOICE, "hydra/hydra_idle.wav", 1, ATTN_NORM);
	}
};

void() hydra_run2 = [ 47, hydra_run3 ]
{
	ai_run((13 + skill));
};

void() hydra_run3 = [ 49, hydra_run4 ]
{
	ai_run((13 + skill));
};

void() hydra_run4 = [ 51, hydra_run5 ]
{
	ai_run((13 + skill));
};

void() hydra_run5 = [ 53, hydra_run6 ]
{
	ai_run((13 + skill));
};

void() hydra_run6 = [ 55, hydra_run7 ]
{
	ai_run((13 + skill));
};

void() hydra_run7 = [ 57, hydra_run8 ]
{
	ai_run((13 + skill));
};

void() hydra_run8 = [ 59, hydra_run9 ]
{
	ai_run((13 + skill));
};

void() hydra_run9 = [ 61, hydra_run1 ]
{
	ai_run((13 + skill));
};

void() hydra_melee =
{
	local vector delta;
	local float ldmg;

	if (!self.enemy)
	{
		return;
	}
	delta = self.enemy.origin - self.origin;
	if ((vlen(delta) > 75))
	{
		return;
	}
	sound(self, CHAN_VOICE, "hydra/hydra_tent.wav", 1, ATTN_NORM);
	ldmg = (random() + random()) * autocvar_hydra_tentacle;
	T_Damage(self.enemy, self, self, ldmg);
};

void() hydra_attack1 = [ 0, hydra_attack2 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack2 = [ 1, hydra_attack3 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack3 = [ 2, hydra_attack4 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack4 = [ 3, hydra_attack5 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack5 = [ 4, hydra_attack6 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack6 = [ 5, hydra_attack7 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
	hydra_melee();
};

void() hydra_attack7 = [ 6, hydra_attack8 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack8 = [ 7, hydra_attack9 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack9 = [ 8, hydra_attack10 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack10 = [ 9, hydra_attack11 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
	hydra_melee();
};

void() hydra_attack11 = [ 10, hydra_attack12 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack12 = [ 11, hydra_attack13 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack13 = [ 12, hydra_attack14 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack14 = [ 13, hydra_attack15 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
	hydra_melee();
};

void() hydra_attack15 = [ 14, hydra_attack16 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack16 = [ 15, hydra_attack17 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack17 = [ 16, hydra_attack18 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack18 = [ 17, hydra_attack19 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack19 = [ 18, hydra_attack20 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack20 = [ 19, hydra_attack21 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack21 = [ 20, hydra_attack22 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack22 = [ 21, hydra_attack23 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
	hydra_melee();
};

void() hydra_attack23 = [ 22, hydra_attack24 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_attack24 = [ 23, hydra_run1 ]
{
	self.nextthink = (time + 0.07);
	ai_charge((10 + skill));
};

void() hydra_spit_touch =
{
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
		if ((other.classname == "player"))
		{
			spawn_touchblood(7);
			T_Damage(other, self, self.owner, autocvar_hydra_spit);
			sound(self, CHAN_WEAPON, "hydra/spit_impact_player.wav", 1, ATTN_NORM);
			if ((autocvar_hydra_can_spit == 2))
			{
				pointparticles(particleeffectnum(/*52177i*/"hydra_toxic_player"), other.origin, VEC_ORIGIN, 1);
			}
		}
	}
	else
	{
		pointparticles(particleeffectnum(/*52196i*/"hydra_toxic_touch"), self.origin, VEC_ORIGIN, 1);
	}
	remove(self);
};

void() hydra_spit_start =
{
	local vector offang;
	local vector org;
	local vector vec;
	local vector follow;
	local entity spit;

	offang = vectoangles((self.enemy.origin - self.origin));
	makevectors(offang);
	org = (self.origin + (v_up * 1)) + (v_forward * 5);
	spit = spawn();
	spit.classname = "spit";
	setorigin(spit, org);
	setmodel(spit, "progs/w_spike.mdl");
	spit.scale = 1.1;
	spit.alpha = 0.05;
	setsize(spit, VEC_ORIGIN, VEC_ORIGIN);
	spit.movetype = MOVETYPE_FLYMISSILE;
	spit.solid = SOLID_BBOX;
	follow = self.enemy.velocity * 0.2;
	vec = normalize((((self.enemy.origin + '0 0 10') + follow) - org));
	spit.velocity = (vec * 444);
	spit.angles = vectoangles(vec);
	spit.traileffectnum = particleeffectnum(/*52219i*/"spit_trail");
	spit.owner = self;
	spit.enemy = self.enemy;
	spit.touch = hydra_spit_touch;
	spit.think = SUB_Remove;
	spit.nextthink = (time + 5);
	sound(self, CHAN_WEAPON, "hydra/hydra_spit.wav", 1, ATTN_NORM);
};

void() Hydra_Spit1 = [ 72, Hydra_Spit2 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit2 = [ 73, Hydra_Spit3 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit3 = [ 74, Hydra_Spit4 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit4 = [ 75, Hydra_Spit5 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit5 = [ 76, Hydra_Spit6 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit6 = [ 77, Hydra_Spit7 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit7 = [ 78, Hydra_Spit8 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit8 = [ 79, Hydra_Spit9 ]
{
	ai_face();
	hydra_spit_start();
};

void() Hydra_Spit9 = [ 80, Hydra_Spit10 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit10 = [ 81, Hydra_Spit11 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit11 = [ 82, Hydra_Spit12 ]
{
	ai_face();
	self.nextthink = (time + 0.07);
};

void() Hydra_Spit12 = [ 83, hydra_run1 ]
{
	ai_face();
	SUB_AttackFinished((1 + random()));
};

void() hydra_spit =
{
	Hydra_Spit1();
};

void() hydra_death1 = [ 24, hydra_death2 ]
{
	if (((self.health < -24) || ((self.enemy.weapon == IT_CHAINSAW) || (self.enemy.weapon == IT_SUPER_SHOTGUN))))
	{
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib_hydra.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib_hydra.mdl", self.health);
		ThrowGib("progs/gib3.mdl", self.health);
		ThrowGib("progs/gib_hydra.mdl", self.health);
		ThrowGib("progs/gib_hydra.mdl", self.health);
		sendParticle("blood_corpse_gib", self.origin, VEC_ORIGIN, 1, 0);
		ThrowHead("progs/gib_hydra.mdl", self.health);
		CeilSplat();
		CeilSplat();
		CeilSplat();
		sound(self, CHAN_VOICE, "misc/gib2.wav", 1, ATTN_NORM);
		return;
	}
	sound(self, CHAN_VOICE, "hydra/hydra_death.wav", 1, ATTN_NORM);
};

void() hydra_death2 = [ 25, hydra_death3 ]
{
};

void() hydra_death3 = [ 26, hydra_death4 ]
{
};

void() hydra_death4 = [ 27, hydra_death5 ]
{
};

void() hydra_death5 = [ 28, hydra_death6 ]
{
};

void() hydra_death6 = [ 29, hydra_death7 ]
{
};

void() hydra_death7 = [ 30, hydra_death8 ]
{
};

void() hydra_death8 = [ 31, hydra_death9 ]
{
};

void() hydra_death9 = [ 32, hydra_death10 ]
{
};

void() hydra_death10 = [ 33, hydra_death11 ]
{
};

void() hydra_death11 = [ 34, hydra_death12 ]
{
};

void() hydra_death12 = [ 35, hydra_death13 ]
{
};

void() hydra_death13 = [ 36, hydra_death14 ]
{
};

void() hydra_death14 = [ 37, hydra_death15 ]
{
};

void() hydra_death15 = [ 38, hydra_death16 ]
{
};

void() hydra_death16 = [ 39, hydra_death17 ]
{
};

void() hydra_death17 = [ 40, hydra_death18 ]
{
};

void() hydra_death18 = [ 41, hydra_death19 ]
{
};

void() hydra_death19 = [ 42, hydra_death20 ]
{
};

void() hydra_death20 = [ 43, hydra_death21 ]
{
};

void() hydra_death21 = [ 44, hydra_death21 ]
{
	self.solid = 0;
};

void() hydra_pain1 = [ 63, hydra_pain2 ]
{
	sound(self, CHAN_AUTO, "hydra/hydra_pain.wav", 1, ATTN_NORM);
};

void() hydra_pain2 = [ 64, hydra_pain3 ]
{
	ai_pain(6);
};

void() hydra_pain3 = [ 65, hydra_pain4 ]
{
	ai_pain(6);
};

void() hydra_pain4 = [ 66, hydra_pain5 ]
{
	ai_pain(6);
};

void() hydra_pain5 = [ 67, hydra_pain6 ]
{
	ai_pain(6);
};

void() hydra_pain6 = [ 68, hydra_pain7 ]
{
	ai_pain(6);
};

void() hydra_pain7 = [ 69, hydra_pain8 ]
{
	ai_pain(6);
};

void() hydra_pain8 = [ 70, hydra_pain9 ]
{
	ai_pain(6);
};

void() hydra_pain9 = [ 71, hydra_run1 ]
{
	ai_pain(6);
};

void(entity attacker, float damage) hydra_pain =
{
	if ((self.pain_finished > time))
	{
		return;
	}
	self.pain_finished = (time + 1);
	hydra_pain1();
};

void() monster_hydra =
{
	local float zufall;
	local entity pain_skin_entity;

	self.classname = "monster_hydra";
	if (deathmatch)
	{
		remove(self);
		return;
	}
	self.solid = SOLID_SLIDEBOX;
	self.movetype = MOVETYPE_STEP;
	if ((autocvar_hydramultiskin == 1))
	{
		self.multiskin = 1;
		setmodel(self, "progs/hydra.mdl");
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
		if ((autocvar_hydramultiskin == 2))
		{
			self.multiskin = 2;
			precache_model("progs/hydra1.mdl");
			zufall = random();
			if ((zufall >= 0.5))
			{
				setmodel(self, "progs/hydra.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 0;
			}
			else
			{
				setmodel(self, "progs/hydra1.mdl");
				self.skin = 0;
				self.monsterskin = 0;
				self.monstermodel = 1;
			}
		}
		else
		{
			if ((autocvar_hydramultiskin == 3))
			{
				self.multiskin = 3;
				precache_model("progs/hydra1.mdl");
				zufall = random();
				if ((zufall > 0.66))
				{
					setmodel(self, "progs/hydra.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
				else
				{
					if ((zufall < 0.34))
					{
						setmodel(self, "progs/hydra.mdl");
						self.skin = 1;
						self.monsterskin = 1;
						self.monstermodel = 0;
					}
					else
					{
						setmodel(self, "progs/hydra1.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 1;
					}
				}
			}
			else
			{
				if ((autocvar_hydramultiskin == 4))
				{
					self.multiskin = 4;
					precache_model("progs/hydra1.mdl");
					zufall = random();
					if ((zufall > 0.75))
					{
						setmodel(self, "progs/hydra.mdl");
						self.skin = 0;
						self.monsterskin = 0;
						self.monstermodel = 0;
					}
					else
					{
						if (((zufall > 0.5) && (zufall <= 0.75)))
						{
							setmodel(self, "progs/hydra.mdl");
							self.skin = 1;
							self.monsterskin = 1;
							self.monstermodel = 0;
						}
						else
						{
							if (((zufall > 0.25) && (zufall <= 0.5)))
							{
								setmodel(self, "progs/hydra1.mdl");
								self.skin = 0;
								self.monsterskin = 0;
								self.monstermodel = 1;
							}
							else
							{
								setmodel(self, "progs/hydra1.mdl");
								self.skin = 1;
								self.monsterskin = 1;
								self.monstermodel = 1;
							}
						}
					}
				}
				else
				{
					setmodel(self, "progs/hydra.mdl");
					self.skin = 0;
					self.monsterskin = 0;
					self.monstermodel = 0;
				}
			}
		}
	}
	setsize(self, '-13 -13 -20', '13 13 20');
	self.scale = 0.8;
	if (!self.health)
	{
		self.health = autocvar_hydra_health;
	}
	self.health_initial = self.health;
	self.colormod = '1 1 1';
	self.th_stand = hydra_stand1;
	self.th_walk = hydra_walk1;
	self.th_run = hydra_run1;
	self.th_die = hydra_death1;
	self.th_pain = hydra_pain;
	self.th_melee = hydra_attack1;
	if (autocvar_hydra_can_spit)
	{
		self.th_missile = hydra_spit;
	}
	self.alpha = (autocvar_monstertransparency * 0.01);
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
	swimmonster_start();
	do_the_cloning__fly_swim();
	HydraPhysics(self);
};

void() monster_hydra_start =
{
	local entity clone;

	self.scale = 1;
	clone = spawn();
	copyentity(self, clone);
	clone.think = monster_hydra;
	clone.nextthink = (time + 0.000100);
};
